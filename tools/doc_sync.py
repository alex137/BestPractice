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


def _committable_files():
    """-> the repo-relative paths git would commit here (tracked, plus
    untracked and not ignored), or None when git cannot say.

    The orphan-sentinel scan used to take ROOT.glob(DOC_GLOB) whole, so it
    walked ignored trees too -- and an ignored tree can hold a full copy of
    this repo. Found 2026-09-28: `.claude/worktrees/` (gitignored, where
    parallel agent sessions keep their own checkouts) put every worktree's
    spec/LOADER.md in front of the scan, and each registered block there
    read as an unregistered orphan in the main checkout. What is not going
    to be committed is not this repo's document."""
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z",
                            "--cached", "--others", "--exclude-standard"],
                           capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return {f for f in r.stdout.split("\0") if f}


def sentinel_blocks():
    """-> {(document, block name)} for every column-0 `<!--gen:NAME-->`
    sentinel in a DOC_GLOB document this repo would commit, minus SKIP_DIRS.
    Without git (a bare copy of the tree) the glob stands alone, as before."""
    committable = _committable_files()
    found = set()
    globs = [DOC_GLOB] if isinstance(DOC_GLOB, str) else list(DOC_GLOB)   # one pattern or several
    for path in sorted({p for g in globs for p in ROOT.glob(g)}):
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(d) for d in SKIP_DIRS):
            continue
        if committable is not None and rel not in committable:
            continue
        for mm in re.finditer(r"^<!--gen:([\w-]+)-->",
                              strip_fenced_code(path.read_text(errors="ignore")),
                              re.M):
            found.add((rel, mm.group(1)))
    return found


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
    code = _led().code_key(script, ["owned_figures"], b"owned")
    for f in ledger.get(("#owned", script), []):
        if not FULL and f.get("code") == code and f.get("reads") is not None and f.get("figures") is not None \
                and all(_led().read_sig(k, r) == sig for k, r, sig in f["reads"]):
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
        ledger[("#owned", script)] = [_led().make("#owned", script, script, code, json.dumps(figs), rd,
                                                  figures=figs)]
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
_LED = None


def _led():
    """The shared fact ledger (fact_ledger.py, beside this file), built from
    the host's knobs on first use."""
    global _LED
    if _LED is None:
        spec = importlib.util.spec_from_file_location("_doc_sync_fact_ledger",
                                                      Path(__file__).resolve().parent / "fact_ledger.py")
        fl = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fl)
        # the gate's own files: a batch emit runs inside this module, which
        # would otherwise count as a read of every block it emits
        here = Path(__file__).resolve().parent
        own = set()
        for f in (Path(__file__).resolve(), here / "fact_ledger.py", here / "reach_key.py"):
            try:
                own.add(str(f.relative_to(Path(ROOT).resolve())))
            except ValueError:
                pass
        _LED = fl.Ledger(ROOT, LEDGER, REACH_DIRS, set(LEDGER_IGNORE) | own)
        _LED.sha = fl.sha
    return _LED


def _hook_env(reads_file):
    return _led().hook_env(reads_file)


def _parse_reads(reads_file):
    return _led().parse_reads(reads_file)


def _sha(text):
    return _led().sha(text)


def _reach_engine():
    return _led().reach_engine()


def _argv_test(node, argv):
    """True/False when `node` is decidable from `argv` alone, else None.
    Understands len(sys.argv) compared with a constant or a tuple of them,
    sys.argv[i] compared with a string, "s" in sys.argv, and not/and/or."""
    import ast

    def is_argv(n):
        return (isinstance(n, ast.Attribute) and n.attr == "argv"
                and isinstance(n.value, ast.Name) and n.value.id == "sys")

    def value(n):
        if isinstance(n, ast.Constant):
            return True, n.value
        if isinstance(n, ast.Tuple) and all(isinstance(e, ast.Constant) for e in n.elts):
            return True, tuple(e.value for e in n.elts)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "len" \
                and len(n.args) == 1 and is_argv(n.args[0]):
            return True, len(argv)
        if isinstance(n, ast.Subscript) and is_argv(n.value) and isinstance(n.slice, ast.Constant) \
                and isinstance(n.slice.value, int):
            i = n.slice.value
            return (True, argv[i]) if -len(argv) <= i < len(argv) else (False, None)
        if is_argv(n):
            return True, tuple(argv)
        return False, None

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        v = _argv_test(node.operand, argv)
        return None if v is None else not v
    if isinstance(node, ast.BoolOp):
        vs = [_argv_test(v, argv) for v in node.values]
        if isinstance(node.op, ast.And):
            return False if False in vs else (None if None in vs else True)
        return True if True in vs else (None if None in vs else False)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        (ok1, a), (ok2, b) = value(node.left), value(node.comparators[0])
        if not (ok1 and ok2):
            return None
        op = node.ops[0]
        try:
            if isinstance(op, ast.Eq):
                return a == b
            if isinstance(op, ast.NotEq):
                return a != b
            if isinstance(op, ast.In):
                return a in b
            if isinstance(op, ast.NotIn):
                return a not in b
        except TypeError:
            return None
    return None


def _exits(stmts):
    """The statement list ends the run (sys.exit / raise SystemExit)."""
    import ast
    if not stmts:
        return False
    last = stmts[-1]
    if isinstance(last, ast.Raise):
        return True
    return (isinstance(last, ast.Expr) and isinstance(last.value, ast.Call)
            and isinstance(last.value.func, ast.Attribute) and last.value.func.attr == "exit"
            and isinstance(last.value.func.value, ast.Name) and last.value.func.value.id == "sys")


def _taken(stmts, argv):
    """The statements of a `__main__` body a run with `argv` can execute:
    an `if` decidable on argv takes one side, and a taken side that exits
    ends the list. Anything undecidable is kept whole."""
    import ast
    out = []
    for st in stmts:
        if isinstance(st, ast.If):
            v = _argv_test(st.test, argv)
            if v is None:
                out.append(st)
                continue
            side = st.body if v else st.orelse
            out.extend(_taken(side, argv))
            if _exits(side):
                return out
            continue
        out.append(st)
    return out


_TREES = {}


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
    # only the statements an `--emit NAME` run can take: a branch whose test
    # is decidable on that argv and false (the self-check, a smoke mode) is
    # left out, so editing what only it calls re-runs no block
    names, extra = set(), ""
    for g in guards:
        taken = _taken(g.body, ["SCRIPT", "--emit", name])
        whole = taken == g.body                 # nothing left out: keyed as it always was
        names |= {n.id for t in ([g] if whole else taken) for n in ast.walk(t) if isinstance(n, ast.Name)}
        extra += ast.dump(g) if whole else "".join(ast.dump(t) for t in taken)
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
    return _led().code_key(script, entries, extra.encode())


def load_ledger():
    """(doc, block) -> [facts]."""
    return _led().facts if LEDGER else {}


def save_ledger(ledger):
    _led().facts = ledger
    _led().save()


def fact_holds(f, code, have):
    return _led().holds(f, code, have)


def make_fact(doc, name, script, code, want, reads):
    return _led().make(doc, name, script, code, want, reads)


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
    found = sentinel_blocks()
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
