"""Verified facts (code fingerprint, recorded reads, result) that let a drift gate or an audit skip a unit whose fact still holds

fact_ledger -- verified facts that let a gate skip work that cannot have
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
import os as _os, sys as _sys, hashlib as _hl
def _fact_ledger_reads():
    out = _os.environ.get("FACT_LEDGER_READS")
    root = _os.environ.get("FACT_LEDGER_ROOT")
    if not out or not root:
        return
    root = _os.path.realpath(root) + _os.sep
    me = _os.path.realpath(__file__)
    loaders = {_os.path.realpath(x) for x in _os.environ.get("FACT_LEDGER_LOADERS", "").split(_os.pathsep) if x}
    plumbing = {_os.path.realpath(x) for x in _os.environ.get("FACT_LEDGER_PLUMBING", "").split(_os.pathsep) if x}
    def from_plumbing():
        # a memo loader or shared-cache client (the host's ignore list): what
        # it runs fetches or stores results keyed by code, and changes none
        f = _sys._getframe(1)
        while f is not None:
            if _os.path.realpath(f.f_code.co_filename) in plumbing:
                return True
            f = f.f_back
        return False
    own_env = ("FACT_LEDGER_READS", "FACT_LEDGER_ROOT", "FACT_LEDGER_LOADERS", "FACT_LEDGER_PLUMBING", "PYTHONPATH")
    busy = [False]
    seen = {}
    skip = (_os.sep + ".git" + _os.sep, _os.sep + ".cache" + _os.sep + "models" + _os.sep, "__pycache__")
    def sha(b):
        return _hl.sha256(b).hexdigest()[:16]
    def write(line):
        with open(out, "a") as f:
            f.write(line + "\n")
    def loading_code():
        # the first frame that is not this hook: the import system, a loader
        # the gate named, or no Python frame at all (the interpreter opening
        # the main script) are loading code, which the fingerprint covers
        f = _sys._getframe(1)
        while f is not None and _os.path.realpath(f.f_code.co_filename) == me:
            f = f.f_back
        if f is None:
            return True
        fn = f.f_code.co_filename
        # frozen import machinery (<frozen importlib._bootstrap>, <frozen
        # zipimport>, which opens the main script to test it for a zip)
        return "importlib" in fn or fn.startswith("<frozen ") or _os.path.realpath(fn) in loaders
    def record(kind, rel, sig):
        k = (kind, rel)
        if k in seen:
            if seen[k] != sig:            # changed while the run was reading it
                write("#opaque\t" + kind + " " + rel + " changed during the run")
            return
        seen[k] = sig
        write(kind + "\t" + rel + "\t" + sig)
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
        if rel.endswith(".pyc") or any(x in _os.sep + rel for x in skip):
            return
        if rel.endswith(".py") and loading_code():
            return
        try:
            if kind == "d":
                sig = sha("\n".join(sorted(_os.listdir(full))).encode())
            elif _os.path.isdir(full):
                return
            else:
                with open(full, "rb") as fh:
                    sig = sha(fh.read())
        except OSError:
            sig = "missing"
        record(kind, rel, sig)
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
                elif (flags & 3) == 1:          # O_WRONLY; O_RDWR reads too
                    return
                note("f", args[0])
            elif event in ("os.listdir", "os.scandir") and args:
                if loading_code():
                    return
                note("d", args[0] if args[0] is not None else ".")
            elif event == "subprocess.Popen":
                exe, argv = args[0], args[1]
                prog = _os.path.basename(_os.fsdecode(exe or (argv[0] if isinstance(argv, (list, tuple)) and argv else argv or "")))
                if not prog.startswith("python") and not from_plumbing():
                    # a non-Python child's reads are invisible here
                    write("#opaque\tstarted " + prog)
            elif event in ("os.system", "os.exec", "os.posix_spawn", "os.spawn") and not from_plumbing():
                write("#opaque\t" + event)
        finally:
            busy[0] = False
    E = type(_os.environ)
    class _RecEnv(E):
        # a variable the work reads is a read: its value at the time
        def __getitem__(self, k):
            try:
                v = E.__getitem__(self, k)
            except KeyError:
                v = None
            if not busy[0] and k not in own_env:
                busy[0] = True
                try:
                    record("e", k, sha(("\0unset" if v is None else v).encode()))
                finally:
                    busy[0] = False
            if v is None:
                raise KeyError(k)
            return v
    try:
        _os.environ.__class__ = _RecEnv
    except TypeError:
        write("#opaque\tthe environment could not be watched")
    # existence and type tests raise no audit event: os.stat and os.lstat
    # (which Path.exists, os.path.exists and isfile go through; the import
    # system uses the posix module directly) record what they found
    def kind_of(full):
        if _os.path.isdir(full):
            return "dir"
        return "file" if _os.path.lexists(full) else "missing"
    def watch(fn):
        def wrapped(path, *a, **k):
            if not busy[0] and not isinstance(path, int):
                busy[0] = True
                try:
                    full = _os.path.realpath(_os.fsdecode(_os.fspath(path)))
                    if full.startswith(root) and not any(x in _os.sep + full[len(root):] for x in skip):
                        record("x", full[len(root):], kind_of(full))
                except Exception:
                    pass
                finally:
                    busy[0] = False
            return fn(path, *a, **k)
        return wrapped
    _os.stat = watch(_os.stat)
    _os.lstat = watch(_os.lstat)
    def modules():
        # every repository module the process loaded: the fingerprint covers
        # the ones it can follow, and the rest are hashed whole from this list
        busy[0] = True
        try:
            for m in list(_sys.modules.values()):
                fn = getattr(m, "__file__", None)
                if fn and fn.endswith(".py"):
                    full = _os.path.realpath(fn)
                    if full.startswith(root) and _os.sep + ".cache" + _os.sep not in full:
                        try:
                            with open(full, "rb") as fh:
                                write("m\t" + full[len(root):] + "\t" + sha(fh.read()))
                        except OSError:
                            pass
            write("#done")
        except Exception:
            pass
    import atexit as _atexit
    _atexit.register(modules)
    write("#active")
    _sys.addaudithook(hook)
_fact_ledger_reads()
del _fact_ledger_reads
"""

# A fact records the hook that saw its reads: a change to what the hook
# watches invalidates every fact recorded under the old one.
HOOK_VERSION = hashlib.sha256(READS_HOOK.encode()).hexdigest()[:12]


def _load_record():
    # the hashing is content_record's (beside this file), loaded by path
    # because this module is itself often loaded by path
    spec = importlib.util.spec_from_file_location("_fact_ledger_content_record",
                                                  Path(__file__).resolve().parent / "content_record.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


content_record = _load_record()


def sha(data):
    return content_record.digest(data, 16)


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
        self.reader = content_record.Reader(self.root, length=16)
        if path:
            self.load()

    # -- the hook -----------------------------------------------------------
    def hook_env(self, reads_file, env=None, loaders=()):
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
        env["FACT_LEDGER_LOADERS"] = os.pathsep.join(str(Path(x).resolve()) for x in loaders)
        env["FACT_LEDGER_PLUMBING"] = os.pathsep.join(str((self.root / x).resolve()) for x in sorted(self.ignore))
        return env

    @staticmethod
    def parse_reads(reads_file):
        """The reads a run recorded, or None when the hook never ran or the
        process died before exit (a fact then cannot be recorded)."""
        try:
            lines = Path(reads_file).read_text().splitlines()
        except OSError:
            return None
        if "#active" not in lines or lines.count("#active") != lines.count("#done"):
            return None                  # a process that never loaded the hook, or died
        if any(ln.startswith("#opaque") for ln in lines):
            return None                  # something the hook cannot see
        out = {}
        for ln in lines:
            parts = ln.split("\t")
            if len(parts) == 3 and not ln.startswith("#"):
                k = (parts[0], parts[1])
                if k in out and out[k] != parts[2] and parts[0] != "m":
                    return None          # two processes saw different contents
                out.setdefault(k, parts[2])
        return sorted((k[0], k[1], v) for k, v in out.items())

    def repo_state(self, path):
        """The state a local git query can see in the repository at `path`
        (content_record kind "g"), computed once per ledger."""
        return self.reader.repo_state(path)

    def read_sig(self, kind, rel):
        return self.reader.sig(kind, rel)

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
        return (f.get("code") == code and self.reads_hold(f)
                and (out is None or f.get("out") == sha(out)))

    def reads_hold(self, f):
        """The fact was taken under this hook and every read it recorded
        still has the content the work saw."""
        return (f.get("hook") == HOOK_VERSION and f.get("reads") is not None
                and content_record.Record(f["reads"]).holds(self.reader, self.ignore)[0])

    def find(self, scope, name, code, out=None):
        """The holding fact for (scope, name), or None."""
        return next((f for f in self.facts.get((scope, name), []) if self.holds(f, code, out)), None)

    def make(self, scope, name, script, code, out, reads, **extra):
        """The fact for one verified unit. A loaded module the fingerprint
        does not cover is kept as a read and hashed whole; a covered one is
        left to the fingerprint."""
        covered = self._covered.get(code, set()) | self.ignore
        # each read carries the content the work saw (hashed by the hook at
        # the time), never the content at recording time
        keep = {}
        for r in reads:
            kind, rel, sig = r if len(r) == 3 else (r[0], r[1], None)
            if kind == "m" and rel in covered:
                continue
            kind = "f" if kind == "m" else kind
            keep.setdefault((kind, rel), sig if sig is not None else self.read_sig(kind, rel))
        f = {"doc": scope, "block": name, "script": script, "code": code, "out": sha(out),
             "hook": HOOK_VERSION, "reads": [[k, r, s] for (k, r), s in sorted(keep.items())]}
        f.update(extra)
        return f

    def put(self, f):
        self.facts[(f["doc"], f["block"])] = [f]
