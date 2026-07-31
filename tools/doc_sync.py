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
"""

import argparse
import difflib
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
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
