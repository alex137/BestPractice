#!/usr/bin/env python3
"""model_audit -- run each computing script's self-assertions, and check the
figures its authoritative source documents recite (practice: scripts-assert-properties).

The failure mode this kills is NOT a stale copy, and that is the whole point.
In the incident that produced this tool, a script published results out by a
third at one input and by more than 3x at another. The constant it started from
was correct, correctly labelled, and identical in the two sibling scripts that
also used it -- one of which stated the governing property in its own docstring.
A shared constants module would have handed it the right number and the defect
would have survived, because the defect was in the TRANSFORMATION applied after
import: a scaling law applied to a quantity whose defining property is that it
does not scale.

So the check that matters is not "do the numbers match" but "does the output
satisfy the properties it must satisfy". And the edge that mattered was not
document-vs-script (computed-numbers-in-scripts' sync gate covers that, and it faithfully
published the wrong number) but SCRIPT-VS-SOURCE-DOCUMENT: the authoritative
document recited the correct figure for exactly the case the script got wrong,
and nothing compared them. The most carefully reasoned documents in a repo are
often checked by nothing.

A script may declare either or both of:

    def self_check() -> list[str]
        Property assertions on its own outputs. Returns failure descriptions;
        empty list means pass. Assert INVARIANTS, not values -- an invariance,
        a monotonicity, a conservation, a ratio held by construction. A value
        comparison cannot catch a correct input transformed by a wrong law.

    ANCHORS = [(label, recited_lo, recited_hi, callable -> (lo, hi)), ...]
    def check_anchors() -> (passes, failures)
        Figures RECITED IN AN AUTHORITATIVE SOURCE DOCUMENT that this script
        must reproduce. Label each with the document and section reciting it.
        Compare by band OVERLAP, not equality, when either side is an estimate.

An anchor failure means a script and a document of record disagree. That is
always worth a human's attention, and it resolves in both directions: the script
may be wrong (the origin incident), the document may need amending, or -- the
case that is pure profit -- the recited figure may carry an assumption the
document never stated, in which case the unconditional figure is the one
anything must actually be sized to. NEVER silently refit an anchor to make it
pass; record which way it resolved. An anchor quietly widened to pass is worse
than no anchor, because it now certifies the thing it stopped checking.

    python3 tools/model_audit.py            # gate: fail on any failure
    python3 tools/model_audit.py --list     # what is instrumented
    python3 tools/model_audit.py --verbose  # show passing anchors too

Run it with the repo's other pre-commit gates.

Scope note: instrumentation is deliberately not required of every script. It is
warranted where a script CONSUMES OR RE-DERIVES a quantity another script or an
authoritative document owns -- that is where this failure class lives. Scripts
that own their numbers end to end need nothing. INSTRUMENTED below is the
explicit list; the audit warns when a listed script carries no assertions, and
ignores everything else.
"""


import argparse
import io
import json
import os
import tempfile
import pathlib
import importlib.util
import sys
import traceback
from pathlib import Path

def find_root(start):
    """Repo root by .git discovery, so the tool works at any install depth."""
    p = Path(start).resolve()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent
    return p.parents[1]


ROOT = find_root(__file__)
# Where this file physically sits -- <repo>/tools/ in a loader install,
# <repo>/process/upstream/tools/ in the classic vendoring one. See the
# INSTRUMENTED loop for why the difference matters.
HERE = Path(__file__).resolve()

# Scripts expected to carry self_check() and/or ANCHORS: those that consume or
# re-derive a quantity owned by another script or recited in an authoritative
# source document. Add a script here when it starts depending on a derived
# quantity it does not itself own.
INSTRUMENTED = [
    # Re-derives the catalogue figures that spec/ and the plan recite.
    "tools/catalogue_stats.py",
    # "scripts/some_model.py",
    # Add a script here when it starts consuming or re-deriving a quantity
    # another script or an authoritative document owns.
]

# A CONSUMER'S AUDIT IS ITS OWN FILE (2026-10-01). The list above is
# BestPractice's, and this file is vendored: a consumer that copied it into
# its tools/ had precedent_check.py's scripts-assert-properties audit
# BestPractice's list there ("tools/catalogue_stats.py ... absent"), and a
# hand edit of the list is refused by the engine refresh. So where this repo
# holds a vendored engine (tools/ENGINE_MANIFEST.json), its configuration is
# read from tools/model_audit_host.json, the same shape as doc_sync's
# tools/doc_sync_pairs.json:
#   {"scripts": [...]}  -- the repo's INSTRUMENTED list, or
#   {"shim": "path/to/shim.py"} -- a host shim that loads this engine and
#                          sets everything itself; running this file runs it.
# A repo with no such file has nothing instrumented. BestPractice, which
# vendors nothing into itself, keeps the list above.
HOST_FILE = "tools/model_audit_host.json"


def _host_config():
    """-> the consumer's configuration dict, or None where the list above is
    this repo's own (BestPractice itself)."""
    if not (ROOT / "tools" / "ENGINE_MANIFEST.json").is_file():
        return None
    f = ROOT / HOST_FILE
    if not f.is_file():
        return {}
    try:
        cfg = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"model_audit FAIL: {HOST_FILE} is not valid JSON ({e})")
    if not isinstance(cfg, dict) or not (
            isinstance(cfg.get("scripts", []), list)
            and all(isinstance(x, str) and x for x in cfg.get("scripts", []))
            and isinstance(cfg.get("shim", ""), str)):
        sys.exit(f"model_audit FAIL: {HOST_FILE} must be an object with a "
                 f"\"scripts\" list of paths or a \"shim\" path")
    return cfg


_HOST = _host_config()
if _HOST is not None:
    INSTRUMENTED = list(_HOST.get("scripts") or [])


def load(path: Path):
    """Import a model. Some print at module level; swallow that so the audit's
    own output stays readable."""
    # One copy of a model per process: when another audited model has
    # already imported this file under its own name, audit that module;
    # otherwise load it under its own name, so a model imported later by
    # name gets this copy. Two copies of one model share every module they
    # both import, and a cache in a shared module then carries state from
    # one copy's rows into the other's (found when a model began importing
    # a second model that imports the first: its self-check passed alone
    # and failed under the audit).
    prior = sys.modules.get(path.stem)
    if prior is not None and pathlib.Path(getattr(prior, "__file__", "") or "").resolve() == path.resolve():
        return prior, None
    name = path.stem if prior is None else f"_ma_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Register before executing (the importlib recipe): a model that
    # fans its solve out over a multiprocessing pool pickles its worker
    # by module name, and an unregistered module cannot be resolved in
    # the workers.
    sys.modules[spec.name] = mod
    sys.path.insert(0, str(path.parent))
    real_stdout, sys.stdout = sys.stdout, io.StringIO()
    try:
        spec.loader.exec_module(mod)
        return mod, None
    except Exception:
        sys.modules.pop(spec.name, None)
        return None, traceback.format_exc(limit=3)
    finally:
        sys.stdout = real_stdout
        sys.path.pop(0)


# ---------------------------------------------------------------------------
# Undecided-constants guard (practice: constants-are-risk-inputs). A
# module-level constant in an instrumented script whose attached comments
# claim a settled status must be named in the host's constants register (as
# a risk input, a banded setting, or an explicit exclusion) or carry
# '# doctrine-ok: <reason>'.
# Hosts set CONSTANTS_REGISTER to the register's repo-relative path; left
# None, the check is skipped.
CONSTANTS_REGISTER = None
SETTLED_WORDS = ("doctrine", "as built", "settled")


# ---------------------------------------------------------------------------
# The changed-only gate (--changed). A model's self-check and anchors can only
# move when its own code or code it imports moves, so a turn that touched a
# few models audits those, and the full run stays the pre-merge gate. The
# closure is static: import statements resolved to files in the repo, the
# model's own directory first, then SEARCH_DIRS. A change under
# ALWAYS_FULL_PREFIXES (vendored engines loaded by path, which no import
# statement names) falls back to the full list. Hosts set BASE_REF (the ref
# the branch is compared with) and SEARCH_DIRS.
BASE_REF = "origin/HEAD"
SEARCH_DIRS = []
ALWAYS_FULL_PREFIXES = ("process/", "tools/")


def _git(*args):
    import subprocess
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def changed_files(base=None):
    """Repo-relative paths changed on this branch against the merge base with
    `base`, plus uncommitted and untracked changes. None when git cannot say
    (no such ref): the caller then audits everything."""
    base = base or BASE_REF
    mb = _git("merge-base", "HEAD", base)
    if not mb:
        return None
    out = set()
    for args in (("diff", "--name-only", mb), ("diff", "--name-only"),
                 ("ls-files", "--others", "--exclude-standard")):
        txt = _git(*args)
        if txt is None:
            return None
        out.update(x for x in txt.splitlines() if x)
    return out


def import_closure(path):
    """The repo files a script imports, transitively (static: import
    statements resolved against its own directory, then SEARCH_DIRS)."""
    import re
    imp = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)
    dirs = [ROOT / d for d in SEARCH_DIRS]
    seen, todo = set(), [Path(path).resolve()]
    while todo:
        q = todo.pop()
        if q in seen or not q.exists():
            continue
        seen.add(q)
        for name in imp.findall(q.read_text(errors="replace")):
            for d in [q.parent, *dirs]:
                c = d / f"{name}.py"
                if c.exists():
                    if c.resolve() not in seen:
                        todo.append(c.resolve())
                    break
    return seen


def select_changed(scripts, base=None):
    """(the scripts whose closure holds a changed file, a note). Every
    script when git cannot say or a changed file is under
    ALWAYS_FULL_PREFIXES."""
    ch = changed_files(base)
    if ch is None:
        return list(scripts), f"--changed: no merge base with {base or BASE_REF}; auditing all"
    full = sorted(c for c in ch if c.startswith(ALWAYS_FULL_PREFIXES) and c.endswith(".py"))
    if full:
        return list(scripts), f"--changed: {full[0]} changed (an engine no import names); auditing all"
    chp = {(ROOT / c).resolve() for c in ch if c.endswith(".py")}
    keep = []
    for rel in scripts:
        p = ROOT / rel
        if p.exists() and import_closure(p) & chp:
            keep.append(rel)
    return keep, (f"--changed: {len(keep)} of {len(scripts)} instrumented script(s) import "
                  f"code changed against {base or BASE_REF}; the full run is the merge gate")


def check_constants_register():
    import re
    if not CONSTANTS_REGISTER:
        return []
    reg_path = ROOT / CONSTANTS_REGISTER
    if not reg_path.exists():
        return [f"constants register missing: {CONSTANTS_REGISTER}"]
    register = reg_path.read_text()
    cdef = re.compile(r"^([A-Z][A-Z0-9_]{2,}) = ")
    fails = []
    for rel in INSTRUMENTED:
        path = ROOT / rel
        if not path.exists() or not rel.endswith(".py"):
            continue
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            m = cdef.match(line)
            if not m:
                continue
            name = m.group(1)
            texts = []
            # Preceding block: column-0 comments only -- an indented comment
            # above a def is the previous constant's trailing continuation.
            j = i - 1
            while j >= 0 and lines[j].startswith("#"):
                texts.append(lines[j]); j -= 1
            texts.append(line)
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("#"):
                texts.append(lines[j]); j += 1
            blob = "\n".join(texts).lower()
            if not any(w in blob for w in SETTLED_WORDS):
                continue
            if "doctrine-ok" in blob or name in register:
                continue
            fails.append(
                f"[constants] {rel}: {name} wears a settled label but is not "
                f"named in {CONSTANTS_REGISTER} -- register it as a risk "
                "input (or an exclusion with its reason), or mark the line "
                "'# doctrine-ok: <reason>'")
    return fails


# ---------------------------------------------------------------------------
# The ledger (fact_ledger.py, beside this file). With LEDGER set, each model
# is audited in a process of its own under the reads hook, and a clean
# audit records a fact: the fingerprint of the code its self_check() and
# check_anchors() reach, the files they read, and the result. A model whose
# fact holds is not run again -- the audit of an unchanged tree takes the
# time to fingerprint it, not the time to re-solve every model. Models run
# in parallel (MODEL_AUDIT_JOBS, default the CPU count); a failing audit is
# never recorded, so it runs every time until it passes. Hosts set LEDGER
# (repo-relative, `merge=union`), REACH_DIRS and LEDGER_IGNORE as for
# doc_sync.
LEDGER = None
REACH_DIRS = ()
LEDGER_IGNORE = ()


def _run_one(path, out):
    """The child of a ledger run: one model's self-check and anchors."""
    import json
    res = {"failures": [], "passes": [], "has_sc": False, "has_an": False, "error": None}
    mod, err = load(path)
    if err:
        res["error"] = err
    else:
        res["has_sc"] = callable(getattr(mod, "self_check", None))
        res["has_an"] = callable(getattr(mod, "check_anchors", None))
        if res["has_sc"]:
            try:
                res["failures"] += [f"[self_check] {{rel}}: {f}" for f in (mod.self_check() or [])]
            except Exception:
                res["failures"].append(f"[self_check] {{rel}} raised:\n{traceback.format_exc(limit=2)}")
        if res["has_an"]:
            try:
                passes, fails = mod.check_anchors()
                res["passes"] = [str(p) for p in passes]
                res["failures"] += [f"[anchor] {{rel}}: {f}" for f in fails]
            except Exception:
                res["failures"].append(f"[anchors] {{rel}} raised:\n{traceback.format_exc(limit=2)}")
    json.dump(res, open(out, "w"))


def _ledger():
    spec = importlib.util.spec_from_file_location("_model_audit_fact_ledger", Path(__file__).resolve().parent / "fact_ledger.py")
    fl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fl)
    return fl.Ledger(ROOT, LEDGER, REACH_DIRS, LEDGER_IGNORE)


def _audit_entries(path):
    import ast
    top = ast.parse(path.read_text()).body
    names = set()
    for st in top:
        # defined here, assigned, or imported from another module: the key
        # follows the name wherever it is bound
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(st.name)
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            names.update(a.asname or a.name for a in st.names)
        elif isinstance(st, ast.Assign):
            names.update(t.id for t in st.targets if isinstance(t, ast.Name))
    ents = [n for n in ("self_check", "check_anchors") if n in names]
    # no self-check the key can name: every name the script binds stands
    # in, so the key is never empty
    return ents or sorted(names)


def audit_with_ledger(scripts, full=False, verbose=False):
    """(failures, warnings, checked, anchors_ok) for `scripts`, each audited
    in its own process unless its fact holds."""
    import concurrent.futures
    import json
    import subprocess
    import time
    led = _ledger()
    failures, warnings, checked, anchors_ok = [], [], 0, 0
    todo, held = [], 0
    t0 = time.time()
    led.begin()
    try:
        for rel in scripts:
            path = ROOT / rel
            if not path.exists():
                path = HERE.parent / pathlib.PurePath(rel).name
            if not path.exists():
                failures.append(f"MISSING: {rel} listed in INSTRUMENTED but absent from both {ROOT} and {HERE.parent}")
                continue
            prel = str(path.resolve().relative_to(ROOT.resolve())) if ROOT.resolve() in path.resolve().parents else rel
            code = led.code_key(prel, _audit_entries(path), b"model-audit")
            f = None if full else led.find("#audit", prel, code)
            if f is not None:
                held += 1
                res = f["result"]
                if res["has_sc"] or res["has_an"]:
                    checked += 1
                    anchors_ok += len(res["passes"])
                else:
                    warnings.append(f"{rel}: no self_check() or ANCHORS — it consumes a quantity it "
                                    "does not own; assert the property or the recited figure")
                continue
            todo.append((rel, prel, path, code))
    finally:
        led.end()
    print(f"model_audit: ledger: {held} of {held + len(todo)} script(s) unchanged since their last clean "
          f"audit ({time.time() - t0:.1f} s); auditing {len(todo)}", flush=True)

    def one(item):
        rel, prel, path, code = item
        fd, out = tempfile.mkstemp(suffix=".json"); os.close(fd)
        fd, reads = tempfile.mkstemp(suffix=".reads"); os.close(fd)
        try:
            t = time.time()
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--_one", str(path), out],
                               capture_output=True, text=True, env=led.hook_env(reads), cwd=str(ROOT))
            try:
                res = json.load(open(out))
            except (OSError, ValueError):
                res = {"failures": [], "passes": [], "has_sc": False, "has_an": False,
                       "error": f"the audit process exited {r.returncode}:\n{r.stderr[-2000:]}"}
            return rel, prel, code, res, led.parse_reads(reads), time.time() - t
        finally:
            os.unlink(out)
            os.unlink(reads)
    jobs = int(os.environ.get("MODEL_AUDIT_JOBS", "0") or 0) or os.cpu_count() or 1
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        for rel, prel, code, res, reads, took in ex.map(one, todo):
            done += 1
            print(f"model_audit: [{done}/{len(todo)}] {rel} ({took:.0f} s)", flush=True)
            if res["error"]:
                failures.append(f"IMPORT FAILED: {rel}\n{res['error']}")
                continue
            res["failures"] = [x.replace("{rel}", rel) for x in res["failures"]]
            if not (res["has_sc"] or res["has_an"]):
                warnings.append(f"{rel}: no self_check() or ANCHORS — it consumes a quantity it "
                                "does not own; assert the property or the recited figure")
            else:
                checked += 1
                anchors_ok += len(res["passes"])
            if verbose:
                for p in res["passes"]:
                    print(f"  ok  {rel}: {p}")
            failures.extend(res["failures"])
            if not res["failures"] and reads is not None:
                led.put(led.make("#audit", prel, prel, code, json.dumps(res, sort_keys=True), reads, result=res))
    led.save()
    return failures, warnings, checked, anchors_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--changed", nargs="?", const="", default=None, metavar="BASE",
                    help="audit only the scripts whose import closure changed against "
                         "BASE (default BASE_REF); the full run stays the merge gate")
    ap.add_argument("--full", action="store_true", help="ignore the ledger and audit every script")
    args = ap.parse_args()

    failures, warnings, checked, anchors_ok = [], [], 0, 0
    failures.extend(check_constants_register())

    scripts = list(INSTRUMENTED)
    if args.changed is not None:
        scripts, note = select_changed(scripts, args.changed or None)
        print(f"model_audit {note}")
        if not scripts:
            print("model_audit OK: no instrumented script imports changed code.")
            return 0

    if LEDGER and not args.list:
        f2, w2, checked, anchors_ok = audit_with_ledger(scripts, full=args.full, verbose=args.verbose)
        failures.extend(f2)
        warnings.extend(w2)
        scripts = []

    for rel in scripts:
        # Two layouts. In the classic vendoring install this file sits at
        # <repo>/process/upstream/tools/, ROOT is the CONSUMING repo's
        # root, and the upstream scripts this list names live beside this
        # file rather than at <repo>/tools/ -- so a vendored copy reported
        # every entry of its own inherited list as MISSING, in every
        # dependent repo, forever. Fall back to the tree this file was
        # vendored with before calling an entry absent.
        path = ROOT / rel
        if not path.exists():
            path = HERE.parent / pathlib.PurePath(rel).name
        if not path.exists():
            failures.append(f"MISSING: {rel} listed in INSTRUMENTED but absent "
                            f"from both {ROOT} and {HERE.parent}")
            continue
        mod, err = load(path)
        if err:
            failures.append(f"IMPORT FAILED: {rel}\n{err}")
            continue

        has_sc = callable(getattr(mod, "self_check", None))
        has_an = callable(getattr(mod, "check_anchors", None))
        if args.list:
            marks = ("self_check " if has_sc else "") + ("anchors" if has_an else "")
            print(f"  {rel:<58} {marks or '(none)'}")
            continue
        if not (has_sc or has_an):
            warnings.append(
                f"{rel}: no self_check() or ANCHORS — it consumes a quantity it "
                "does not own; assert the property or the recited figure")
            continue

        checked += 1
        if has_sc:
            try:
                for f in mod.self_check() or []:
                    failures.append(f"[self_check] {rel}: {f}")
            except Exception:
                failures.append(f"[self_check] {rel} raised:\n"
                                f"{traceback.format_exc(limit=2)}")
        if has_an:
            try:
                passes, fails = mod.check_anchors()
                anchors_ok += len(passes)
                for f in fails:
                    failures.append(f"[anchor] {rel}: {f}")
                if args.verbose:
                    for p in passes:
                        print(f"  ok  {rel}: {p}")
            except Exception:
                failures.append(f"[anchors] {rel} raised:\n"
                                f"{traceback.format_exc(limit=2)}")

    if args.list:
        return 0

    for w in warnings:
        print(f"WARN: {w}")
    for f in failures:
        print(f"FAIL: {f}")

    if failures:
        print(f"\nmodel_audit FAIL — {len(failures)} failure(s), "
              f"{len(warnings)} warning(s).")
        print("An anchor failure means a script and a source document disagree. "
              "Resolve it — do not refit the anchor to silence it.")
        return 1
    if not INSTRUMENTED:
        # "OK: 0 instrumented script(s)" is the confident all-clear from a
        # check that never ran -- the failure mode this repo has now been
        # bitten by four times. Nothing was inspected, so nothing passed.
        print("model_audit NOT APPLICABLE: INSTRUMENTED is empty, so no script "
              "was inspected. This is not a pass — instrument the scripts that "
              "re-derive a quantity another script or document owns.")
        return 0
    print(f"model_audit OK: {checked} instrumented script(s), "
          f"{anchors_ok} figure(s) recited in source documents verified, "
          f"{len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--_one":
        _run_one(Path(sys.argv[2]), sys.argv[3])
        sys.exit(0)
    if _HOST and _HOST.get("shim"):
        # The shim loads this file under its own module name, so this branch
        # never runs twice.
        import runpy
        _shim = ROOT / _HOST["shim"]
        if not _shim.is_file():
            sys.exit(f"model_audit FAIL: {HOST_FILE} names shim {_HOST['shim']}, "
                     f"which does not exist")
        sys.argv[0] = str(_shim)
        runpy.run_path(str(_shim), run_name="__main__")
        sys.exit(0)
    sys.exit(main())
