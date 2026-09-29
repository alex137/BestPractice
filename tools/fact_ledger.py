"""fact_ledger -- verified facts that let a gate skip work that cannot have
changed (practice: slow-steps-report-and-cache).

A gate that re-runs a script to prove its output still matches spends most
of its time proving that nothing changed. A fact records, for one unit of
work (a generated block, a model's self-check), everything the result can
depend on:

  * the fingerprint of the code the work can reach (reach_key.py, the
    engine that keys memos), and the repository modules that fingerprint
    accounts for -- its whole static import closure;
  * the files the work actually read and the repository modules it loaded
    outside that closure (loaded by file path, or by a computed name), each
    with a content hash -- recorded by an audit hook in the process that did
    the work, so nothing is declared by hand;
  * the hash of the result;
  * for a unit that runs local git queries against a repository, that
    repository's state (kind "g": HEAD, refs, and the working tree by
    content).

A unit whose fact holds on all three is not run. Facts verify themselves --
every line says what it depends on and the gate re-hashes it -- so the
ledger merges by union (mark it `merge=union`) and a stale or foreign line
costs one re-run, never a skipped unit. A run whose reads could not be
recorded (the hook did not load, or the process died before exit) gets no
fact and always runs.

    led = Ledger(root, "facts.jsonl", reach_dirs=["models"], ignore=["models/cache.py"])
    code = led.code_key("models/cost.py", ["emit_table"], b"table")
    env = led.hook_env(reads_file)            # run the work under this env
    reads = led.parse_reads(reads_file)
    led.put(led.make("doc.md", "table", "models/cost.py", code, output, reads))
    led.save()

Host knobs belong to the caller: `ignore` names modules whose only effect is
to fetch or store results (a memo loader, a shared-cache client), whose
loading a fact does not count.
"""
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

READS_HOOK = r"""
import os as _os, sys as _sys
def _fact_ledger_reads():
    out = _os.environ.get("FACT_LEDGER_READS")
    root = _os.environ.get("FACT_LEDGER_ROOT")
    if not out or not root:
        return
    root = _os.path.realpath(root) + _os.sep
    busy = [False]
    seen = set()
    skip = (".git" + _os.sep, ".cache" + _os.sep, "__pycache__")
    def note(kind, path):
        try:
            if isinstance(path, int):
                return
            if isinstance(path, bytes):
                path = path.decode(errors="replace")
            full = _os.path.realpath(_os.fspath(path))
        except Exception:
            return
        if not full.startswith(root):
            return
        rel = full[len(root):]
        if rel.endswith(".pyc") or any(x in rel for x in skip) or (kind, rel) in seen:
            return
        if rel.endswith(".py"):
            # the import system reading code is the fingerprint's business;
            # anything else reading a .py file reads it as data
            f = _sys._getframe(2)
            while f is not None:
                if "importlib" in f.f_code.co_filename:
                    return
                f = f.f_back
        seen.add((kind, rel))
        with open(out, "a") as f:
            f.write(kind + "\t" + rel + "\n")
    def hook(event, args):
        if busy[0]:
            return
        busy[0] = True
        try:
            if event == "open" and args and args[0] is not None:
                mode, flags = args[1], args[2] if len(args) > 2 else 0
                if isinstance(mode, str):
                    if any(c in mode for c in "wax") and "+" not in mode:
                        return
                elif flags & 3:
                    return
                if _os.path.isfile(args[0]) if not isinstance(args[0], int) else False:
                    note("f", args[0])
            elif event in ("os.listdir", "os.scandir") and args:
                # the import system lists every directory it searches; that
                # is where code is found, which the fingerprint covers, not
                # data the work reads
                f = _sys._getframe(1)
                while f is not None:
                    if "importlib" in f.f_code.co_filename:
                        return
                    f = f.f_back
                p = args[0] if args[0] is not None else "."
                note("d", p)
        finally:
            busy[0] = False
    def modules():
        # every repository module the process loaded: the fingerprint covers
        # the ones it can follow, and the rest are hashed whole from this list
        busy[0] = True
        try:
            with open(out, "a") as f:
                for m in list(_sys.modules.values()):
                    fn = getattr(m, "__file__", None)
                    if fn and fn.endswith(".py"):
                        full = _os.path.realpath(fn)
                        if full.startswith(root) and ".cache" + _os.sep not in full:
                            f.write("m\t" + full[len(root):] + "\n")
                f.write("#done\n")
        except Exception:
            pass
    import atexit as _atexit
    _atexit.register(modules)
    with open(out, "a") as f:
        f.write("#active\n")
    _sys.addaudithook(hook)
_fact_ledger_reads()
del _fact_ledger_reads
"""


def sha(data):
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()[:16]


class Ledger:
    def __init__(self, root, path=None, reach_dirs=(), ignore=()):
        self.root = Path(root)
        self.path = path
        self.reach_dirs = tuple(reach_dirs)
        self.ignore = set(ignore)
        self.facts = {}
        self._hook_dir = None
        self._rk = None
        self._keys = {}
        self._covered = {}
        self._repo = {}
        if path:
            self.load()

    # -- the hook -----------------------------------------------------------
    def hook_env(self, reads_file, env=None):
        """The environment of a run that records its reads: the hook rides in
        a usercustomize on PYTHONPATH, so the script itself runs exactly as
        it would from the shell."""
        if self._hook_dir is None:
            self._hook_dir = tempfile.mkdtemp(prefix="fact_ledger_hook_")
            Path(self._hook_dir, "usercustomize.py").write_text(READS_HOOK)
        env = dict(os.environ if env is None else env)
        env["PYTHONPATH"] = self._hook_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["FACT_LEDGER_READS"] = str(reads_file)
        env["FACT_LEDGER_ROOT"] = str(self.root)
        return env

    @staticmethod
    def parse_reads(reads_file):
        """The reads a run recorded, or None when the hook never ran or the
        process died before exit (a fact then cannot be recorded)."""
        try:
            lines = Path(reads_file).read_text().splitlines()
        except OSError:
            return None
        if "#active" not in lines or "#done" not in lines:
            return None
        return sorted({tuple(ln.split("\t", 1)) for ln in lines if "\t" in ln})

    def repo_state(self, path):
        """The state a local git query can see in the repository at `path`:
        HEAD, every ref, the working tree against HEAD (tracked changes and
        untracked files, by content). Computed once per ledger -- a run does
        not change it -- so a unit that runs git against a checkout it did
        not make can still hold a fact, re-run when any of that moves."""
        key = str(path)
        if key not in self._repo:
            import subprocess

            def git(*a):
                r = subprocess.run(["git", "-C", key, *a], capture_output=True)
                return r.stdout if r.returncode == 0 else b"?"
            h = hashlib.sha256()
            for part in (git("rev-parse", "HEAD"), git("for-each-ref", "--format=%(refname) %(objectname)"),
                         git("diff", "HEAD", "--binary"), git("status", "--porcelain=v1", "-uall", "-z")):
                h.update(part + b"\0")
            for name in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
                f = Path(key) / name.decode(errors="replace")
                if name and f.is_file():
                    h.update(name + b"\0" + f.read_bytes())
            self._repo[key] = h.hexdigest()[:16]
        return self._repo[key]

    def read_sig(self, kind, rel):
        p = self.root / rel
        if kind == "g":
            return self.repo_state(p)
        try:
            if kind == "d":
                return sha("\n".join(sorted(x.name for x in p.iterdir())))
            return sha(p.read_bytes())
        except OSError:
            return "missing"

    # -- the code fingerprint -----------------------------------------------
    def reach_engine(self):
        if self._rk is None:
            spec = importlib.util.spec_from_file_location("_fact_ledger_reach_key",
                                                          Path(__file__).resolve().parent / "reach_key.py")
            self._rk = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._rk)
        return self._rk

    def begin(self):
        """Open a fingerprint session: no file changes until end()."""
        rk = self.reach_engine()
        if hasattr(rk, "begin_session"):
            rk.begin_session()

    def end(self):
        rk = self.reach_engine()
        if hasattr(rk, "end_session"):
            rk.end_session()

    def code_key(self, script, entries, extra=b""):
        """The fingerprint of the code `entries` in `script` can reach."""
        extra = extra if isinstance(extra, bytes) else str(extra).encode()
        k = (script, tuple(entries), extra)
        if k not in self._keys:
            path = self.root / script
            dirs = [str(path.parent)] + [str(self.root / d) for d in self.reach_dirs]
            files = set()
            self._keys[k] = self.reach_engine().reach_key(path, list(entries), dirs, extra=extra,
                                                          root=self.root, files=files)
            # the fingerprint accounts for its whole static import closure:
            # what of it can run is hashed, and the rest cannot change a result
            self._covered[self._keys[k]] = files | {script}
        return self._keys[k]

    # -- the facts ----------------------------------------------------------
    def load(self):
        """(scope, name) -> [facts]; a line that does not parse is ignored,
        as a union merge can leave one."""
        self.facts = {}
        if not self.path or not (self.root / self.path).is_file():
            return self.facts
        for ln in (self.root / self.path).read_text().splitlines():
            try:
                f = json.loads(ln)
                self.facts.setdefault((f["doc"], f["block"]), []).append(f)
            except (ValueError, KeyError, TypeError):
                continue
        return self.facts

    def save(self):
        lines = [json.dumps(self.facts[k][-1], sort_keys=True, separators=(",", ":"))
                 for k in sorted(self.facts)]
        (self.root / self.path).write_text("".join(ln + "\n" for ln in lines))

    def holds(self, f, code, out=None):
        """A fact holds when its code, every read, and (when given) the
        output it recorded are all what they are now."""
        return (f.get("code") == code and (out is None or f.get("out") == sha(out))
                and f.get("reads") is not None
                and all(rel in self.ignore or self.read_sig(kind, rel) == s
                        for kind, rel, s in f["reads"]))

    def find(self, scope, name, code, out=None):
        """The holding fact for (scope, name), or None."""
        return next((f for f in self.facts.get((scope, name), []) if self.holds(f, code, out)), None)

    def make(self, scope, name, script, code, out, reads, **extra):
        """The fact for one verified unit. A loaded module the fingerprint
        does not cover is kept as a read and hashed whole; a covered one is
        left to the fingerprint."""
        covered = self._covered.get(code, set()) | self.ignore
        keep = sorted({("f" if kind == "m" else kind, rel) for kind, rel in reads
                       if not (kind == "m" and rel in covered)})
        f = {"doc": scope, "block": name, "script": script, "code": code, "out": sha(out),
             "reads": [[kind, rel, self.read_sig(kind, rel)] for kind, rel in keep]}
        f.update(extra)
        return f

    def put(self, f):
        self.facts[(f["doc"], f["block"])] = [f]
