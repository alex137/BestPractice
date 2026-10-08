#!/usr/bin/env python3
"""Failures an unattended job could not report anywhere else, kept as open blocker items in todo/ and listed at session start

    python3 tools/open_failures.py                       # list the open ones
    python3 tools/open_failures.py --file TITLE --closes TEXT [--what FILE]
                                                         # write one (the finding on
                                                         # stdin, or from FILE)
    python3 tools/open_failures.py --self-check

practice: automation-issues -- a blocked unattended job reports through a
tracked issue. An issue needs the host's issues API, and a cloud session's
`gh` is often not signed in, or the host is down, or is not GitHub at all;
then the issue never exists and nobody hears of the failure. So the job
also writes the failure into the repository: an open item under todo/,
`severity: blocker`, in the `failures` batch, with the finding and the
condition that closes it. The job commits and pushes it the way it pushes
anything else. tools/bootstrap.sh runs this script at session start, so the
next session, on any harness, is told first (Alex, 2026-10-08, decided:
"maybe we use an issues file or directory in the repo. Then if the session
is closed, another agent can check the directory and work on a fix").

An item is dated in the person's zone (practice: timestamps-carry-offset)
and closed the usual way: `status: done`, with what fixed it.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = "failures"


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "failure"


def _today(root):
    sys.path.insert(0, str(HERE))
    try:
        import precedent_time
        return precedent_time.today(root)
    finally:
        sys.path.pop(0)


def write_item(repo, title, what, closes, today=None):
    """Write one open failure item under todo/ in `repo`. -> its path."""
    repo = pathlib.Path(repo)
    today = today or _today(repo)
    todo = repo / "todo"
    todo.mkdir(exist_ok=True)
    base = f"todo-{today}-{_slug(title)}"
    path, n = todo / f"{base}.md", 2
    while path.exists():
        path, n = todo / f"{base}-{n}.md", n + 1
    path.write_text(
        "---\n"
        f"slug:              {path.stem}\n"
        "kind:              analysis\n"
        "domain:            null\n"
        "severity:          blocker\n"
        "status:            open\n"
        "disposition:       null\n"
        "remind_on:         null\n"
        "blocked_on:        null\n"
        f"batch:             {BATCH}\n"
        "decision:          null\n"
        "decision_strength: null\n"
        "waiting_on:        null\n"
        f"noted:             {today}\n"
        "closed:            null\n"
        "---\n"
        "## What\n\n"
        f"- [ ] **{title}** (a failure an unattended job filed here; fix it before other work)\n\n"
        f"```\n{what.strip()}\n```\n\n"
        "## How It Closes\n\n"
        f"{closes}\n\n"
        "## Notes\n", encoding="utf-8")
    return path


def open_items(repo=ROOT):
    """-> [(path, title)] for every open failure item."""
    out = []
    for f in sorted((pathlib.Path(repo) / "todo").glob("todo-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        head = text.split("\n---", 1)[0]
        if re.search(r"^severity:\s*blocker\s*$", head, re.M) and \
                re.search(r"^status:\s*open\s*$", head, re.M):
            m = re.search(r"^- \[ \] \*\*(.+?)\*\*", text, re.M)
            out.append((f, m.group(1) if m else f.stem))
    return out


def self_check():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = write_item(td, "Landing failed: feat/x", "boom", "It lands.", "2026-10-08")
        q = write_item(td, "Landing failed: feat/x", "again", "It lands.", "2026-10-08")
        found = open_items(td)
        ok = len(found) == 2 and p != q and found[0][1] == "Landing failed: feat/x"
        q.write_text(q.read_text().replace("status:            open", "status:            done"))
        ok &= len(open_items(td)) == 1
    print(f"open_failures self-check: {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


def main(argv):
    if argv[:1] in (["--help"], ["-h"]):
        print(__doc__.strip())
        return 0
    if "--self-check" in argv:
        return self_check()
    if argv[:1] == ["--file"]:
        try:
            title = argv[1]
            closes = argv[argv.index("--closes") + 1]
        except (IndexError, ValueError):
            print("usage: open_failures.py --file TITLE --closes TEXT [--what FILE]",
                  file=sys.stderr)
            return 2
        what = (pathlib.Path(argv[argv.index("--what") + 1]).read_text(encoding="utf-8")
                if "--what" in argv else sys.stdin.read())
        print(write_item(ROOT, title, what, closes).relative_to(ROOT))
        return 0
    items = open_items()
    if items:
        print(f"OPEN FAILURES ({len(items)}): an unattended job filed these under todo/ "
              "because it could not report them anywhere else. Tell the person, and fix "
              "them before other work:")
        for f, title in items:
            print(f"  - {f.relative_to(ROOT)}: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
