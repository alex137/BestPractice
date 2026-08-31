#!/usr/bin/env python3
"""model_audit -- run each computing script's self-assertions, and check the
figures its authoritative source documents recite (practice 30).

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
document-vs-script (practice 19's sync gate covers that, and it faithfully
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


def load(path: Path):
    """Import a model. Some print at module level; swallow that so the audit's
    own output stays readable."""
    spec = importlib.util.spec_from_file_location(f"_ma_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    real_stdout, sys.stdout = sys.stdout, io.StringIO()
    try:
        spec.loader.exec_module(mod)
        return mod, None
    except Exception:
        return None, traceback.format_exc(limit=3)
    finally:
        sys.stdout = real_stdout
        sys.path.pop(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    failures, warnings, checked, anchors_ok = [], [], 0, 0

    for rel in INSTRUMENTED:
        path = ROOT / rel
        if not path.exists():
            failures.append(f"MISSING: {rel} listed in INSTRUMENTED but absent")
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
    sys.exit(main())
