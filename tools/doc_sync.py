#!/usr/bin/env python3
"""doc_sync -- keep script-generated blocks inside documents in sync (practice 19).

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
PAIRS = []

# Where this repo keeps prose, for the orphan-sentinel scan; narrow it in
# the host shim if the whole tree is too broad.
DOC_GLOB = "**/*.md"


def owned_figures(script):
    """Figures a script declares it owns, as (label, [rendered forms]).

    A script opts in by defining owned_figures() returning that shape. Scripts
    that do not are simply not checked -- instrumentation is per-script and
    deliberate.
    """
    path = ROOT / script
    spec = importlib.util.spec_from_file_location(f"_of_{Path(script).stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    real, sys.stdout = sys.stdout, io.StringIO()
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return []
    finally:
        sys.stdout = real
        sys.path.pop(0)
    fn = getattr(mod, "owned_figures", None)
    return fn() if callable(fn) else []


def block_re(name):
    return re.compile(
        rf"(<!--gen:{re.escape(name)}-->\n)(.*?)(<!--/gen:{re.escape(name)}-->)",
        re.S)


def emit(script, name):
    r = subprocess.run([sys.executable, str(ROOT / script), "--emit", name],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[doc_sync] FAIL: {script} --emit {name} exited "
                 f"{r.returncode}:\n{r.stderr}")
    return r.stdout.rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="regenerate drifted blocks in place")
    ap.add_argument("--list", action="store_true",
                    help="list registered document/block/script pairs")
    args = ap.parse_args()

    if args.list:
        for doc, name, script in PAIRS:
            print(f"  {doc} [{name}] <- {script}")
        return

    fail = False
    for doc, name, script in PAIRS:
        path = ROOT / doc
        text = path.read_text()
        m = block_re(name).search(text)
        if not m:
            print(f"[doc_sync] FAIL  {doc}: no <!--gen:{name}--> block")
            fail = True
            continue
        want = emit(script, name)
        have = m.group(2)
        if have == want:
            print(f"[doc_sync] OK    {doc} [{name}]")
        elif args.write:
            path.write_text(text[:m.start(2)] + want + text[m.end(2):])
            print(f"[doc_sync] WROTE {doc} [{name}]")
        else:
            print(f"[doc_sync] DRIFT {doc} [{name}] -- document block != "
                  "script output. Fix the script (numbers live there), then "
                  "run doc_sync.py --write.")
            for line in difflib.unified_diff(
                    have.splitlines(), want.splitlines(),
                    f"{doc} (document)", f"{script} --emit {name}",
                    lineterm="", n=1):
                print("    " + line)
            fail = True

    # Footer check: every registered document must end with a "Numbers by:"
    # footer naming each script that feeds it, so a reader always knows
    # which code produced the numbers.
    docs = {}
    for doc, name, script in PAIRS:
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
    # Restatement check (practice 33): a figure a script OWNS must not be
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
        for script in sorted({s for d, n, s in PAIRS if d == doc}):
            for label, forms in owned_figures(script):
                for form in forms:
                    rx = re.compile(re.escape(form) + r"(?![/\w])")
                    for line in outside.splitlines():
                        if rx.search(line) and "<!--owned-ok-->" not in line:
                            print(f"[doc_sync] FAIL  {doc}: restates "
                                  f"{label} ({form!r}) outside its gen block — "
                                  "point at the table instead, or mark the "
                                  "line <!--owned-ok--> if the restatement is "
                                  "deliberate")
                            fail = True

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
    for path in sorted(ROOT.glob(DOC_GLOB)):
        rel = str(path.relative_to(ROOT))
        for mm in re.finditer(r"<!--gen:([\w-]+)-->", path.read_text(errors="ignore")):
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
    main()
