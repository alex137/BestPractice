#!/usr/bin/env python3
"""doc_sync -- keep script-generated blocks inside documents in sync (practice: computed-numbers-in-scripts).

The failure mode this kills: a script that computes numbers (a model, a cost
rollup) changes, and a document quoting those numbers silently keeps the old
ones -- someone has to notice and ask "did you update the table?". Instead,
any document region whose content a script computes is wrapped in invisible
sentinels:

    <!--gen:NAME-->
    ...generated markdown (typically a table)...
    <!--/gen:NAME-->

and the (document, NAME, script) triple is registered in PAIRS below. The
script must support `--emit NAME`, printing exactly the block's content.

    python3 tools/doc_sync.py           # gate: fail loudly on drift
    python3 tools/doc_sync.py --write   # regenerate blocks in place
    python3 tools/doc_sync.py --list    # show registered pairs

Run the bare command with the repo's other pre-commit gates. When a document
gains a script-generated table: wrap it in sentinels, give the script an
`--emit NAME` mode, register the pair. Never hand-edit inside a gen block --
the numbers live in the script; the document is a render target.

The sentinels are HTML comments, which render as nothing on hosted markdown.

THE LEDGER (host knob LEDGER). Re-running every emitter to see whether its
block still matches is the gate's whole cost, and most of it is spent
proving that nothing changed. With a ledger, each block carries a fact:
the fingerprint of the code its emitter can reach (reach_key.py, the same
engine that keys memos), the hashes of the files the emit actually read
(recorded by an audit hook in the emit process), and the hash of what it
printed. A block whose fact still holds on all three is skipped without
running anything; only the rest are emitted. Facts verify themselves, so
the ledger merges by union and a stale or foreign line costs one re-emit,
never a skipped block. An emit whose reads could not be recorded gets no
fact and always runs. `--full` ignores the ledger.

    python3 tools/doc_sync.py --full    # emit every block regardless

Beyond the drift gate, this tool enforces two things a generated block alone
cannot: a provenance footer naming the scripts that feed each document, and
the practice-33 RESTATEMENT check -- a figure a script declares it owns
(owned_figures()) must not be hand-typed into the prose around its block,
because that copy has no gate on it and silently survives a fix to the script.
"""

import argparse
import difflib
import importlib.util
import io
import re
import subprocess
import sys
from pathlib import Path


def find_root(start):
    p = Path(start).resolve()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent
    return p


ROOT = find_root(__file__)

# (document path, block name, script path) -- all repo-root-relative.
# Example:
#   ("docs/summary.md", "cost_table", "models/cost_model.py"),
PAIRS = [
    ("spec/LOADER.md", "catalogue", "tools/catalogue_stats.py"),
    ("spec/ENFORCEMENT.md", "enforcement", "tools/catalogue_stats.py"),
    ("documentation/DAILY_HABITS.md", "vocabulary",
     "tools/precedent_vocabulary.py"),
]

# spec/CHANGES_TO_TELL_ALEX.md's merge-back block left this list on
# 2026-09-22, when that record closed. A closed record is a measurement
# of its date; regenerating its figures afterwards would keep editing a
# document that says on its face it is no longer updated. The numbers
# are frozen inline there, labelled with the date they were taken.
#
# spec/VERY_DEEP_CHECK.md's merged-stale-checkout block is deliberately NOT
# here. Every PAIRS script above computes from this repo's own tracked
# files -- deterministic, reproducible from a bare copy of the tree.
# tools/very_deep_check.py --emit merged-stale-checkout instead makes a
# LIVE `git fetch`/`ls-remote` against the real GitHub origin, so its
# answer depends on the moment it runs and the clone's own depth, not on
# anything this repository's own commit fixes. Registering it here failed
# the very first CI run (practice: very-deep-check): the harness's own
# "enforced channel fires" self-test builds a scratch copy of the tree to
# plant one violation, and that copy's git history and remote are not the
# real repo's, so the live scan inside it produced a different answer than
# whatever was committed -- a false DRIFT with no connection to the
# planted violation being tested. `tools/very_deep_check.py` writes that
# block directly, with its own sentinel, when its checkout branch scan
# actually runs -- see `_update_spec_doc_block()` -- the same way it writes
# record/stale_branches.md, never gated on matching a moment that has
# already passed by the time anything checks it.

# Where this repo keeps prose, for the orphan-sentinel scan; narrow it in
# the host shim if the whole tree is too broad.
DOC_GLOB = "**/*.md"          # a pattern, or a list of patterns (e.g. slides generated as HTML)

# Directories the orphan-sentinel scan must not walk. A repo that VENDORS an
# upstream practice layer carries a whole copy of that upstream's documents,
# generated blocks and all -- and those blocks are registered in the
# UPSTREAM's PAIRS, not in this repo's. Scanning them reports every one as an
# unregistered orphan, in a tree the consuming repo is not allowed to edit.
# Seen 2026-09-06 in a real dependent repo: two orphans, both inside
# process/upstream/, neither actionable there.
SKIP_DIRS = ("process/upstream/",)


def strip_fenced_code(text):
    """Blank out fenced code blocks, keeping line numbering.

    A sentinel INSIDE a fence is documentation showing what a sentinel looks
    like, not a live generated block. The caller pairs this with a column-0
    anchor, which covers the other way a document shows the format: an
    indented code block. Origin: this repo documents the format as
    ``<!--gen:NAME-->`` in PRACTICES.md (indented) and in the practice file
    for computed-numbers-in-scripts (fenced), and the orphan scan reported
    both as unregistered blocks -- so the gate was red for a reason that had
    nothing to do with any number, on a repo with PAIRS = []. A permanently
    red gate is a gate nobody runs. A LIVE block's sentinel is always at
    column 0, because doc_sync writes it there.
    """
    out, fence = [], None
    for line in text.splitlines():
        m = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and m:
            fence = m.group(1)  # the real run, not normalized to length 3 --
            out.append("")      # per CommonMark a fence only closes on a run
            continue             # of the SAME character at least as long.
        if fence is not None:
            out.append("")
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        out.append(line)
    return "\n".join(out)


class OwnedFiguresUnavailable(Exception):
    """A script's owned_figures() could not be read -- never a silent pass."""


_OWNED_CHILD = r"""
import importlib.util, json, sys, io, contextlib
path, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, __import__("os").path.dirname(path))
spec = importlib.util.spec_from_file_location("_of_child", path)
mod = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(mod)
    figs = [[label, list(forms)] for label, forms in mod.owned_figures()]
json.dump(figs, open(out, "w"))
"""


def owned_figures_cached(script, ledger):
    """owned_figures() through the ledger: a script whose fingerprint and
    recorded reads still hold is not imported at all (declaring figures can
    cost a model's whole solve). Otherwise it runs in a child process that
    records its reads, and the answer is kept as a fact."""
    import json
    import os
    import tempfile
    if not LEDGER:
        return owned_figures(script)
    if not _binds_owned(script):
        return []
    code = _reach_engine().reach_key(ROOT / script, ["owned_figures"],
                                     [str((ROOT / script).parent)] + [str(ROOT / d) for d in REACH_DIRS],
                                     extra=b"owned", root=ROOT)
    for f in ledger.get(("#owned", script), []):
        if not FULL and f.get("code") == code and f.get("reads") is not None and f.get("figures") is not None \
                and all(_read_sig(k, r) == sig for k, r, sig in f["reads"]):
            return [(lab, forms) for lab, forms in f["figures"]]
    fd, out = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    fd, reads = tempfile.mkstemp(suffix=".reads")
    os.close(fd)
    try:
        r = subprocess.run([sys.executable, "-c", _OWNED_CHILD, str(ROOT / script), out],
                           capture_output=True, text=True, env=_hook_env(reads))
        if r.returncode != 0:
            raise OwnedFiguresUnavailable(f"{script}.owned_figures() could not be read: "
                                          f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
        figs = json.load(open(out))
        rd = _parse_reads(reads)
    finally:
        os.unlink(out)
        os.unlink(reads)
    if rd is not None:
        files = set()
        _reach_engine().reach_key(ROOT / script, ["owned_figures"],
                                  [str((ROOT / script).parent)] + [str(ROOT / d) for d in REACH_DIRS],
                                  extra=b"owned", root=ROOT, files=files)
        covered = files | {script} | set(LEDGER_IGNORE)
        keep = sorted({("f" if k == "m" else k, rel) for k, rel in rd if not (k == "m" and rel in covered)})
        ledger[("#owned", script)] = [{"doc": "#owned", "block": script, "script": script, "code": code,
                                       "figures": figs, "out": _sha(json.dumps(figs)),
                                       "reads": [[k, rel, _read_sig(k, rel)] for k, rel in keep]}]
    return [(lab, forms) for lab, forms in figs]


def _binds_owned(script):
    """Whether a script can define owned_figures at all (a script that never
    binds the name has nothing to declare, and is not imported)."""
    import ast
    try:
        top = ast.parse((ROOT / script).read_text()).body
    except SyntaxError:
        return True
    for st in top:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if st.name == "owned_figures":
                return True
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            if any((a.asname or a.name.split(".")[0]) in ("owned_figures", "*") for a in st.names):
                return True
        elif any(isinstance(x, ast.Name) and x.id == "owned_figures" and isinstance(x.ctx, ast.Store)
                 for x in ast.walk(st)) or any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                                                and x.func.id in ("globals", "exec", "setattr")
                                                for x in ast.walk(st)):
            return True
    return False


def owned_figures(script):
    """Figures a script declares it owns, as (label, [rendered forms]).

    A script opts in by defining owned_figures() returning that shape. Scripts
    that do not are simply not checked -- instrumentation is per-script and
    deliberate.

    A script that fails to IMPORT is a different thing entirely, and used to be
    indistinguishable from one that opted out: the bare `except Exception:
    return []` here made a crashing emitter look exactly like a deliberate
    opt-out, so the restatement scan silently examined nothing and the gate
    printed green. That is this repo's own recurring failure -- an empty result
    reading as "clean" rather than as "could not check" (see AGENTS.md's
    gotchas, where the same shape bit a scope:'tree' check and three inherited
    audits). An import failure now raises, and the caller fails the gate with
    the traceback.
    """
    path = ROOT / script
    spec = importlib.util.spec_from_file_location(f"_of_{Path(script).stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    real, sys.stdout = sys.stdout, io.StringIO()
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise OwnedFiguresUnavailable(
            f"{script} could not be imported to read owned_figures(): "
            f"{type(e).__name__}: {e}") from e
    finally:
        sys.stdout = real
        sys.path.pop(0)
    fn = getattr(mod, "owned_figures", None)
    if not callable(fn):
        return []
    try:
        return list(fn())
    except Exception as e:
        raise OwnedFiguresUnavailable(
            f"{script}.owned_figures() raised: {type(e).__name__}: {e}") from e


# ---------------------------------------------------------------------------
# The ledger (see the module docstring). Hosts set LEDGER to a repo-relative
# path (mark it `merge=union` in .gitattributes) and REACH_DIRS to the
# directories a bare `import name` in a script may resolve to after the
# script's own directory -- the same list the host's memo keys use. An import
# the fingerprint cannot resolve is not followed, so a missing directory
# here is a block skipped on stale code; list every directory models import
# from.
LEDGER = None
REACH_DIRS = ()
# Modules whose loading a fact does not count, because their only effect is
# to fetch or store a result (a memo loader, a shared-cache client, the key
# engine it calls): an edit to one never changes a number a block prints.
# Repo-relative paths; the host lists them.
LEDGER_IGNORE = ()
FULL = False                      # --full: ignore the ledger for this run
READS = {}                        # (script, name) -> recorded reads, or None when untracked
_HOOK_DIR = None

_READS_HOOK = r"""
import os as _os, sys as _sys
def _doc_sync_reads():
    out = _os.environ.get("DOC_SYNC_READS")
    root = _os.environ.get("DOC_SYNC_ROOT")
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
        if rel.endswith((".py", ".pyc")) or any(x in rel for x in skip) or (kind, rel) in seen:
            return
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
                # data a model reads
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
_doc_sync_reads()
del _doc_sync_reads
"""


def _hook_env(reads_file):
    """The environment of an emit that records its reads: the hook rides in
    a usercustomize on PYTHONPATH, so the script itself runs exactly as it
    would from the shell."""
    import os
    import tempfile
    global _HOOK_DIR
    if _HOOK_DIR is None:
        _HOOK_DIR = tempfile.mkdtemp(prefix="doc_sync_hook_")
        Path(_HOOK_DIR, "usercustomize.py").write_text(_READS_HOOK)
    env = dict(os.environ)
    env["PYTHONPATH"] = _HOOK_DIR + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["DOC_SYNC_READS"] = str(reads_file)
    env["DOC_SYNC_ROOT"] = str(ROOT)
    return env


def _parse_reads(reads_file):
    """The reads an emit recorded, or None when the hook never ran (a
    fact then cannot be recorded, and the block always emits)."""
    try:
        lines = Path(reads_file).read_text().splitlines()
    except OSError:
        return None
    if "#active" not in lines or "#done" not in lines:
        return None
    return sorted({tuple(ln.split("\t", 1)) for ln in lines if "\t" in ln})


def _sha(text):
    import hashlib
    return hashlib.sha256(text.encode() if isinstance(text, str) else text).hexdigest()[:16]


def _read_sig(kind, rel):
    p = ROOT / rel
    try:
        if kind == "d":
            return _sha("\n".join(sorted(x.name for x in p.iterdir())))
        return _sha(p.read_bytes())
    except OSError:
        return "missing"


_RK = None
_KEYS = {}
_COVERED = {}                     # (doc-free) block key -> repo files the fingerprint follows
_TREES = {}


def _reach_engine():
    global _RK
    if _RK is None:
        spec = importlib.util.spec_from_file_location("_doc_sync_reach_key",
                                                      Path(__file__).resolve().parent / "reach_key.py")
        _RK = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_RK)
    return _RK


def _block_entries(script, name):
    """What the emit of one block can run: the names the script's
    `__main__` block uses, with an EMITTERS table narrowed to the block's
    own entry (when the table is a plain dict literal nothing else edits),
    and the hashed text of the dispatch itself."""
    import ast
    tree = _TREES.get(script)
    if tree is None:
        tree = _TREES[script] = ast.parse((ROOT / script).read_text())
    guards = [st for st in tree.body if isinstance(st, ast.If) and isinstance(st.test, ast.Compare)
              and isinstance(st.test.left, ast.Name) and st.test.left.id == "__name__"]
    names = {n.id for g in guards for n in ast.walk(g) if isinstance(n, ast.Name)}
    extra = "".join(ast.dump(g) for g in guards)
    table = [st for st in tree.body if isinstance(st, ast.Assign) and len(st.targets) == 1
             and isinstance(st.targets[0], ast.Name) and st.targets[0].id == "EMITTERS"
             and isinstance(st.value, ast.Dict)]
    edited = any(
        (isinstance(n, (ast.Assign, ast.AugAssign)) and any(
            isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "EMITTERS"
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target])))
        or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "EMITTERS"
            and n.attr in ("update", "setdefault", "pop", "clear", "__setitem__"))
        or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EMITTERS" for t in n.targets)
            and n not in table)
        for n in ast.walk(tree))
    if "EMITTERS" in names and len(table) == 1 and not edited:
        d = table[0].value
        vals = [v for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value == name]
        if len(vals) == 1 and all(isinstance(k, ast.Constant) for k in d.keys):
            names.discard("EMITTERS")
            names |= {n.id for n in ast.walk(vals[0]) if isinstance(n, ast.Name)}
            extra += ast.dump(vals[0])
    return sorted(names), extra


def block_code_key(script, name):
    """The fingerprint of the code one block's emit can reach."""
    entries, extra = _block_entries(script, name)
    k = (script, tuple(entries), extra)
    if k not in _KEYS:
        path = ROOT / script
        dirs = [str(path.parent)] + [str(ROOT / d) for d in REACH_DIRS]
        files = set()
        _KEYS[k] = _reach_engine().reach_key(path, entries, dirs, extra=extra.encode(), root=ROOT, files=files)
        # the fingerprint accounts for its whole static import closure: what
        # of it can run is hashed, and the rest cannot change the output
        _COVERED[_KEYS[k]] = files | {script}
    return _KEYS[k]


def load_ledger():
    """(doc, block) -> [facts]; a line that does not parse is ignored, as a
    union merge can leave one."""
    import json
    out = {}
    if not LEDGER or not (ROOT / LEDGER).is_file():
        return out
    for ln in (ROOT / LEDGER).read_text().splitlines():
        try:
            f = json.loads(ln)
            out.setdefault((f["doc"], f["block"]), []).append(f)
        except (ValueError, KeyError, TypeError):
            continue
    return out


def save_ledger(ledger):
    import json
    lines = []
    for (doc, block) in sorted(ledger):
        f = ledger[(doc, block)][-1]
        lines.append(json.dumps(f, sort_keys=True, separators=(",", ":")))
    (ROOT / LEDGER).write_text("".join(ln + "\n" for ln in lines))


def fact_holds(f, code, have):
    return (f.get("code") == code and f.get("out") == _sha(have) and f.get("reads") is not None
            and all(_read_sig(kind, rel) == sig for kind, rel, sig in f["reads"]))


def make_fact(doc, name, script, code, want, reads):
    """The fact for one verified block. A loaded module the fingerprint
    does not cover (one loaded by file path, or by a computed name) is kept
    as a read and hashed whole; a covered one is left to the fingerprint."""
    covered = _COVERED.get(code, set()) | set(LEDGER_IGNORE)
    keep = sorted({("f" if kind == "m" else kind, rel) for kind, rel in reads
                   if not (kind == "m" and rel in covered)})
    return {"doc": doc, "block": name, "script": script, "code": code, "out": _sha(want),
            "reads": [[kind, rel, _read_sig(kind, rel)] for kind, rel in keep]}



def block_re(name):
    return re.compile(
        rf"(<!--gen:{re.escape(name)}-->\n)(.*?)(<!--/gen:{re.escape(name)}-->)",
        re.S)


# FAIL FAST. Emits run concurrently, and a pool waits for every running
# task before it lets an exception out, so a script that crashed in its
# first second was reported only when the slowest solve beside it finished
# -- fourteen minutes, twice in one session. Every emit is its own process
# group; the first failure stops the rest and the gate exits at once.
_PROCS = set()
_ABORTED = []


def _run(argv, env=None):
    import threading
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         env=env, start_new_session=True)
    _PROCS.add(p)
    try:
        out, err = p.communicate()
    finally:
        _PROCS.discard(p)
    return subprocess.CompletedProcess(argv, p.returncode, out, err)


def _abort_all():
    import os
    import signal
    _ABORTED.append(True)
    for p in list(_PROCS):
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def emit(script, name):
    import os
    import tempfile
    env = None
    if LEDGER:
        fd, reads = tempfile.mkstemp(suffix=".reads")
        os.close(fd)
        env = _hook_env(reads)
    try:
        r = _run([sys.executable, str(ROOT / script), "--emit", name], env=env)
        if LEDGER:
            READS[(script, name)] = _parse_reads(reads)
    finally:
        if LEDGER:
            os.unlink(reads)
    if r.returncode != 0:
        sys.exit(f"[doc_sync] FAIL: {script} --emit {name} exited "
                 f"{r.returncode}:\n{r.stderr}")
    return r.stdout.rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# One process per model (BATCH_MODELS). A model's blocks are otherwise each
# their own process, and a model that re-derives its state per process (a
# cold solve, a sizing loop, a sweep) repeats it once per block -- 29 times
# for one host model. A script listed in BATCH_MODELS is imported once in a
# child process and its own `__main__` block is re-run for each block name
# with sys.argv set to `SCRIPT --emit NAME`, so it keeps whatever dispatch
# it has and shares its in-process memos across its blocks. The output of
# each block is what the per-block run prints: the import-time output
# followed by the dispatch's. Blocks then share module state, so a script
# joins the list only after `--verify-batch SCRIPT` shows every one of its
# blocks identical both ways; hosts set BATCH_MODELS.
BATCH_MODELS = ()


def emit_batch(script, names):
    import json
    import os
    import tempfile
    fd, out = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    fd, reads = tempfile.mkstemp(suffix=".reads")
    os.close(fd)
    try:
        r = _run([sys.executable, str(Path(__file__).resolve()), "--_emit-batch",
                  str(ROOT / script), out, *names], env=_hook_env(reads) if LEDGER else None)
        if r.returncode != 0:
            sys.exit(f"[doc_sync] FAIL: {script} (one process, {len(names)} blocks) exited "
                     f"{r.returncode}:\n{r.stderr}")
        res = json.load(open(out))
        if LEDGER:                          # one process: its reads are every block's
            rd = _parse_reads(reads)
            READS.update({(script, n): rd for n in names})
    finally:
        os.unlink(out)
        os.unlink(reads)
    return {n: res[n].rstrip("\n") + "\n" for n in names}


def _emit_batch_child(script, out, names):
    """The child of emit_batch: the script's module body once, its
    `__main__` block once per name."""
    import ast
    import contextlib
    import io
    import json
    import types
    path = Path(script).resolve()
    tree = ast.parse(path.read_text(), str(path))
    guards = [st for st in tree.body if isinstance(st, ast.If) and isinstance(st.test, ast.Compare)
              and isinstance(st.test.left, ast.Name) and st.test.left.id == "__name__"]
    if len(guards) != 1:
        sys.exit(f"{script}: expected one `if __name__ == ...` block, found {len(guards)}")
    body = [st for st in tree.body if st is not guards[0]]
    sys.path.insert(0, str(path.parent))
    mod = types.ModuleType(path.stem)
    mod.__file__ = str(path)
    sys.modules[path.stem] = mod          # a fork pool pickles its workers by module name
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), mod.__dict__)
    head = buf.getvalue()
    main = compile(ast.Module(body=guards[0].body, type_ignores=[]), str(path), "exec")
    res = {}
    for n in names:
        sys.argv = [str(path), "--emit", n]
        b = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(b):
            try:
                exec(main, mod.__dict__)
            except SystemExit as e:
                if isinstance(e.code, str):
                    sys.stderr.write(e.code + "\n")
                    code = 1
                else:
                    code = e.code or 0
        if code:
            sys.stderr.write(f"{script} --emit {n} exited {code}\n")
            sys.exit(code)
        res[n] = head + b.getvalue()
    json.dump(res, open(out, "w"))


def verify_batch(script, names):
    """Every block of `script` emitted both ways; the names that differ."""
    one = {n: emit(script, n) for n in names}
    many = emit_batch(script, names)
    return [n for n in names if one[n] != many[n]]


def emit_all(pairs, jobs=None):
    """Every registered block's script output, run concurrently: each emit
    is its own process, and a model that re-derives its state per process
    spends most of a gate's wall clock doing so one block at a time. The
    number of concurrent emits is DOC_SYNC_JOBS, else the CPU count.
    Returns {(script, name): text}; the first failing emit exits the gate,
    as the serial loop did."""
    import concurrent.futures
    import os
    keys = list(dict.fromkeys((s, n) for _, n, s in pairs))
    batched = [s for s in dict.fromkeys(s for s, _ in keys) if s in BATCH_MODELS]
    tasks = [(emit_batch, (s, [n for s2, n in keys if s2 == s])) for s in batched]
    tasks += [(emit, k) for k in keys if k[0] not in batched]

    def collect(fn, args, res):
        if fn is emit_batch:
            return {(args[0], n): t for n, t in res.items()}
        return {args: res}
    jobs = jobs or int(os.environ.get("DOC_SYNC_JOBS", "0") or 0) or os.cpu_count() or 1
    out = {}
    if jobs <= 1 or len(tasks) <= 1:
        for fn, args in tasks:
            out.update(collect(fn, args, fn(*args)))
        return out
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=jobs)
    try:
        futs = {ex.submit(fn, *args): (fn, args) for fn, args in tasks}
        for f in concurrent.futures.as_completed(futs):
            fn, args = futs[f]
            try:
                res = f.result()
            except BaseException:
                if not _ABORTED:            # the first failure: stop every other emit now
                    running = len(_PROCS)
                    _abort_all()
                    print(f"[doc_sync] stopping {running} other emit(s): {args[0]} failed",
                          file=sys.stderr)
                raise
            out.update(collect(fn, args, res))
    finally:
        ex.shutdown(wait=True, cancel_futures=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="regenerate drifted blocks in place")
    ap.add_argument("--list", action="store_true",
                    help="list registered document/block/script pairs")
    ap.add_argument("--only", action="append", default=[], metavar="SUBSTR",
                    help="restrict to pairs whose document, block or script path "
                         "contains SUBSTR (repeatable) -- the fast gate for a "
                         "turn that touched a few documents (its restatement scan "
                         "reads only the selected scripts' owned figures); the "
                         "bare run stays the pre-merge gate")
    ap.add_argument("--verify-batch", metavar="SCRIPT",
                    help="emit every block of SCRIPT per block and in one process and "
                         "report any that differ: the check a script passes before it "
                         "joins BATCH_MODELS")
    ap.add_argument("--full", action="store_true",
                    help="ignore the ledger and emit every selected block (facts are still recorded)")
    args = ap.parse_args()
    global FULL
    FULL = args.full
    if args.verify_batch:
        names = [n for _, n, s in PAIRS if s == args.verify_batch]
        if not names:
            sys.exit(f"[doc_sync] {args.verify_batch}: no registered blocks")
        bad = verify_batch(args.verify_batch, list(dict.fromkeys(names)))
        if bad:
            print(f"[doc_sync] FAIL  {args.verify_batch}: {len(bad)} of {len(names)} block(s) differ "
                  f"in one process: {', '.join(bad)}")
            sys.exit(1)
        print(f"[doc_sync] OK    {args.verify_batch}: all {len(names)} block(s) identical in one process")
        return
    pairs = [p for p in PAIRS if not args.only
             or any(o in p[0] or o in p[1] or o in p[2] for o in args.only)]

    if args.list:
        for doc, name, script in pairs:
            print(f"  {doc} [{name}] <- {script}")
        return

    fail = False

    # A VENDORED copy arrives carrying UPSTREAM's registry, not this repo's.
    # Every entry then points at a document that does not exist here, and the
    # honest reading is "this copy is not configured yet", not "this repo's
    # registry is broken" -- the remedy is to replace PAIRS with this repo's
    # own pairs (or empty it), which is a host decision, not a defect to fix
    # by restoring files that were never here. Distinguished mechanically:
    # NONE of the registered documents existing is an unconfigured copy; SOME
    # of them missing is a genuinely stale registry, reported per entry below.
    live_pairs = [(d, n, s) for d, n, s in PAIRS if (ROOT / d).is_file()]
    if PAIRS and not live_pairs:
        print(f"[doc_sync] NOT APPLICABLE: all {len(PAIRS)} registered "
              f"document(s) are absent here ({', '.join(d for d, _, _ in PAIRS)})"
              f" -- this is an upstream copy of PAIRS, not this repo's. "
              f"Replace PAIRS in tools/doc_sync.py with this repo's own "
              f"(document, block, script) triples, or leave it empty if no "
              f"document here carries generated numbers yet.")
        PAIRS[:] = []
        pairs = []

    # the ledger: a block whose fact still holds is not emitted at all
    ledger = load_ledger() if LEDGER else {}
    codes, held = {}, set()
    if LEDGER:
        import time
        t0 = time.time()
        rk = _reach_engine()
        if hasattr(rk, "begin_session"):     # no file changes while the keys are taken
            rk.begin_session()
        for doc, name, script in pairs:
            path = ROOT / doc
            if not path.is_file() or not (ROOT / script).is_file():
                continue
            m = block_re(name).search(path.read_text())
            if not m:
                continue
            try:
                codes[(doc, name)] = block_code_key(script, name)
            except (SyntaxError, OSError) as e:
                print(f"[doc_sync] note  {script}: no fingerprint ({type(e).__name__}); its blocks emit")
                continue
            if not FULL and any(fact_holds(f, codes[(doc, name)], m.group(2))
                                for f in ledger.get((doc, name), [])):
                held.add((doc, name))
        if hasattr(rk, "end_session"):
            rk.end_session()
        print(f"[doc_sync] ledger: {len(held)} of {len(pairs)} block(s) unchanged since their "
              f"last check ({time.time() - t0:.1f} s); emitting {len(pairs) - len(held)}"
              + (" (--full)" if FULL else ""), file=sys.stderr)
    recorded = False
    wants = emit_all([(d, n, s) for d, n, s in pairs if (ROOT / d).is_file() and (d, n) not in held])
    for doc, name, script in pairs:
        if (doc, name) in held:
            print(f"[doc_sync] OK    {doc} [{name}] (ledger)")
            continue
        path = ROOT / doc
        # Graceful degradation, not a crash: PAIRS is hand-maintained, and a
        # document renamed or deleted without updating it leaves an entry
        # pointing at nothing. A bare FileNotFoundError here names a path
        # and no remedy; this names the registry that has to change.
        if not path.is_file():
            print(f"[doc_sync] FAIL  {doc}: registered in PAIRS but no such "
                  f"file -- the document was renamed or deleted; update "
                  f"PAIRS in tools/doc_sync.py (or restore the file)")
            fail = True
            continue
        text = path.read_text()
        m = block_re(name).search(text)
        if not m:
            print(f"[doc_sync] FAIL  {doc}: no <!--gen:{name}--> block")
            fail = True
            continue
        want = wants[(script, name)]
        have = m.group(2)
        verified = False
        if have == want:
            print(f"[doc_sync] OK    {doc} [{name}]")
            verified = True
        elif args.write:
            path.write_text(text[:m.start(2)] + want + text[m.end(2):])
            print(f"[doc_sync] WROTE {doc} [{name}]")
            verified = True
        if verified and LEDGER and (doc, name) in codes:
            reads = READS.get((script, name))
            if reads is not None:
                ledger[(doc, name)] = [make_fact(doc, name, script, codes[(doc, name)], want, reads)]
                recorded = True
            else:
                print(f"[doc_sync] note  {doc} [{name}]: its reads were not recorded, so it "
                      "gets no ledger fact and emits every run")
        if not verified:
            print(f"[doc_sync] DRIFT {doc} [{name}] -- document block != "
                  "script output. Fix the script (numbers live there), then "
                  "run doc_sync.py --write.")
            for line in difflib.unified_diff(
                    have.splitlines(), want.splitlines(),
                    f"{doc} (document)", f"{script} --emit {name}",
                    lineterm="", n=1):
                print("    " + line)
            fail = True

    if recorded:
        save_ledger(ledger)

    # Footer check: every registered document must end with a "Numbers by:"
    # footer naming each script that feeds it, so a reader always knows
    # which code produced the numbers.
    docs = {}
    for doc, name, script in pairs:
        # Graceful degradation, not a crash: a PAIRS entry pointing at a file that
        # no longer exists was already reported once, above; carrying it into
        # the footer and restatement passes only turns that one clear finding
        # into a bare FileNotFoundError two loops later.
        if not (ROOT / doc).is_file():
            continue
        docs.setdefault(doc, set()).add(Path(script).name)
    for doc, scripts in docs.items():
        text = (ROOT / doc).read_text()
        if "Numbers by:" not in text:
            print(f"[doc_sync] FAIL  {doc}: missing 'Numbers by:' footer")
            fail = True
            continue
        footer = text[text.rindex("Numbers by:"):]
        missing = [m for m in scripts if m not in footer]
        if missing:
            print(f"[doc_sync] FAIL  {doc}: footer does not name "
                  f"{', '.join(sorted(missing))}")
            fail = True
    # Restatement check (practice: docs-track-models): a figure a script OWNS must not be
    # hand-typed into the prose around its generated block. The gate can only
    # see what it is pointed at, so a corrected script self-corrects every
    # generated table and leaves every hand-typed restatement wrong.
    #
    # False positives are controlled by scope, not by cleverness:
    #   * only documents ALREADY WIRED to the script are scanned;
    #   * only figures the script DECLARES it owns, via owned_figures();
    #   * matched in the exact rendered form the script produces, units and
    #     all, with a unit boundary so "30 m" never matches "30 m/s".
    # A legitimate restatement is marked with <!--owned-ok--> on the line.
    for doc, scripts in docs.items():
        text = (ROOT / doc).read_text()
        outside = re.sub(r"<!--gen:.*?<!--/gen:[\w-]+-->", "", text, flags=re.S)
        # the scripts of the SELECTED pairs: a bare run selects every pair, so
        # the pre-merge gate scans exactly what it did; an --only run checks
        # the figures of the scripts it regenerated and does not import (and
        # solve) every other model wired to the same document
        for script in sorted({s for d, n, s in pairs if d == doc}):
            try:
                declared = owned_figures_cached(script, ledger)
            except OwnedFiguresUnavailable as e:
                print(f"[doc_sync] FAIL  {doc}: {e} — the restatement scan for "
                      "this document examined nothing, which is not a pass")
                fail = True
                continue
            for label, forms in declared:
                for form in forms:
                    rx = re.compile(r"(?<![\w.])" + re.escape(form) + r"(?![/\w])")
                    for line in outside.splitlines():
                        if rx.search(line) and "<!--owned-ok-->" not in line:
                            print(f"[doc_sync] FAIL  {doc}: restates "
                                  f"{label} ({form!r}) outside its gen block — "
                                  "point at the table instead, or mark the "
                                  "line <!--owned-ok--> if the restatement is "
                                  "deliberate")
                            fail = True

    if LEDGER and any(k[0] == "#owned" for k in ledger):
        save_ledger(ledger)

    # Registry-consistency check: PAIRS is a hand-maintained JOIN over two facts
    # that already declare themselves -- the sentinel in the document and the
    # emitter in the script. A hand-maintained restatement of something
    # derivable is exactly what the checks above forbid, so it must itself be
    # verified. The ORPHAN sentinel is the dangerous case: a generated block
    # registered nowhere, which nothing checks and whose numbers rot silently
    # while every gate reports green. (In the origin repo this found two orphan
    # blocks on its first run, one containing a literal placeholder that had sat
    # in a live document.) DOC_GLOB is the set of documents to scan for
    # sentinels; set it to wherever this repo keeps prose.
    registered = {(d, n) for d, n, _ in PAIRS}
    found = set()
    globs = [DOC_GLOB] if isinstance(DOC_GLOB, str) else list(DOC_GLOB)   # one pattern or several
    for path in sorted({p for g in globs for p in ROOT.glob(g)}):
        rel = str(path.relative_to(ROOT))
        if any(rel.startswith(d) for d in SKIP_DIRS):
            continue
        for mm in re.finditer(r"^<!--gen:([\w-]+)-->",
                              strip_fenced_code(path.read_text(errors="ignore")),
                              re.M):
            found.add((rel, mm.group(1)))
    for doc, name in sorted(found - registered):
        print(f"[doc_sync] FAIL  {doc}: <!--gen:{name}--> is not in PAIRS — "
              "an unregistered block is never checked and its numbers rot "
              "silently; register it (or delete the sentinel)")
        fail = True
    for doc, name in sorted(registered - found):
        print(f"[doc_sync] FAIL  {doc} [{name}]: registered in PAIRS but the "
              "document has no such sentinel — stale registry entry")
        fail = True
    for _, _, script in PAIRS:
        if not (ROOT / script).exists():
            print(f"[doc_sync] FAIL  PAIRS points at a missing script: {script}")
            fail = True

    if fail:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--_emit-batch":
        _emit_batch_child(sys.argv[2], sys.argv[3], sys.argv[4:])
        sys.exit(0)
    main()
