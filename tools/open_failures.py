#!/usr/bin/env python3
"""Failures an unattended job could not report anywhere else, kept as open blocker items in todo/ and listed at session start

    python3 tools/open_failures.py                       # list the open ones
    python3 tools/open_failures.py --file TITLE --closes TEXT [--what FILE] [--alerting-test]
                                                         # write one (the finding on
                                                         # stdin, or from FILE)
    python3 tools/open_failures.py --close PATH --because TEXT
                                                         # close one, saying what closed it
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

MAIN'S TEST FAILED COMES FIRST (2026-10-09, the main landing plan, piece
B, layer 2). Where this repository's own workflow opens a GitHub issue
labelled main-test-failed when the test on main fails (BestPractice's
deep-check.yml), an open one is listed before anything else here: a red main
is what every other repository's Update Vendors is held behind. One API call
through github_budget.py, and none in a repository whose workflows never
open such an issue; when GitHub cannot be read, one line says so.
The same workflow closes the issue once the test passes on main's current
head (tools/close_main_test_issue.sh, 2026-10-10), so an open one means main
is red now; before that, one stayed open eleven hours past a green main.

AN ALERTING TEST IS NOT A FAILURE (Morgan, 2026-10-09; practice:
automation-issues). A job's alerting test fails on purpose, to prove the
alert reaches the person, so it still files -- that is part of what it tests -- but with --alerting-test: no
`severity: blocker`, `kind: manual`, and listed at session start as a test
to confirm, never with the failures. It closes on the person's answer
(--close), not on a later run: a passed test once read "the sync failed"
first in every session until someone spent another run to clear it.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = "failures"
# The label .github/workflows/deep-check.yml puts on the issue it opens when
# main's test fails.
MAIN_TEST_LABEL = "main-test-failed"
# What marks an alerting test's item, on its checkbox line.
TEST_MARK = "an alerting test an unattended job filed here"


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "failure"


def _today(root):
    sys.path.insert(0, str(HERE))
    try:
        import precedent_time
        return precedent_time.today(root)
    finally:
        sys.path.pop(0)


def write_item(repo, title, what, closes, today=None, alerting_test=False):
    """Write one open failure item under todo/ in `repo`. -> its path.
    With alerting_test, the failure was deliberate: the item is the person's
    to confirm (kind manual, no severity), and never one of open_items()."""
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
        f"kind:              {'manual' if alerting_test else 'analysis'}\n"
        "domain:            null\n"
        f"severity:          {'null' if alerting_test else 'blocker'}\n"
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
        + (f"- [ ] **{title}** ({TEST_MARK}: the failure was deliberate; "
           "ask the person whether the alert reached them)\n\n" if alerting_test else
           f"- [ ] **{title}** (a failure an unattended job filed here; fix it before other work)\n\n")
        + 
        f"```\n{what.strip()}\n```\n\n"
        "## How It Closes\n\n"
        f"{closes}\n\n"
        "## Notes\n", encoding="utf-8")
    return path


def _status_open(text):
    head = text.split("\n---", 1)[0]
    return bool(re.search(r"^status:\s*open\s*$", head, re.M)), head


def alerting_tests(repo=ROOT):
    """-> [(path, title)] for every open alerting-test item."""
    out = []
    for f in sorted((pathlib.Path(repo) / "todo").glob("todo-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        is_open, _ = _status_open(text)
        m = re.search(r"^- \[ \] \*\*(.+?)\*\* \(" + re.escape(TEST_MARK), text, re.M)
        if is_open and m:
            out.append((f, m.group(1)))
    return out


def close_item(path, because, today=None):
    """Close one item this file wrote: `status: done`, dated, ticked, with
    what closed it as its last note. -> True, or False if it was not open."""
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    if not _status_open(text)[0]:
        return False
    today = today or _today(path.parent.parent)
    text = re.sub(r"^status:(\s*)open\s*$", r"status:\1done", text, count=1, flags=re.M)
    text = re.sub(r"^closed:(\s*)null\s*$", rf'closed:\1"{today}"', text, count=1, flags=re.M)
    text = text.replace("- [ ] **", "- [x] **", 1)
    path.write_text(text.rstrip("\n") + f"\n- {today}: closed: {because}\n", encoding="utf-8")
    return True


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


def main_test_issues(repo=ROOT, gh=None):
    """-> ([(number, title, url)] of open main-test-failed issues, None), or
    (None, why GitHub could not be read). ([], None) with no call at all
    where none of the repository's workflows names the label."""
    repo = pathlib.Path(repo)
    wf = repo / ".github" / "workflows"
    texts = [f.read_text(encoding="utf-8", errors="replace")
             for f in sorted(wf.glob("*.y*ml"))] if wf.is_dir() else []
    if not any(MAIN_TEST_LABEL in t for t in texts):
        return [], None
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches as pb
        gh = gh or pb._sibling("github_budget")
        slug = pb._slug(repo)
    except Exception as e:                        # noqa: BLE001 -- reported
        return None, f"could not load the GitHub helpers: {e}"
    finally:
        sys.path.pop(0)
    if gh is None or not slug:
        return None, ("no github.com origin could be read here" if not slug
                      else "github_budget.py is not beside this file")
    data, err = gh.call(f"repos/{slug}/issues?labels={MAIN_TEST_LABEL}"
                        f"&state=open&per_page=20", cache=False)
    if err or not isinstance(data, list):
        return None, err or "GitHub gave an answer this could not read"
    return [(i.get("number"), i.get("title") or "", i.get("html_url") or "")
            for i in data if isinstance(i, dict) and "pull_request" not in i], None


def report_lines(repo=ROOT, gh=None):
    """-> the session-start lines: an open main-test-failed issue first,
    then the open failure items under todo/."""
    repo = pathlib.Path(repo)
    lines = []
    issues, problem = main_test_issues(repo, gh)
    if problem:
        lines.append(f"MAIN'S TEST: could not read GitHub's issues to see whether "
                     f"main's test failed ({problem}).")
    for number, title, url in issues or []:
        lines.append(f"MAIN'S TEST FAILED: issue #{number} is open, \"{title}\" "
                     f"({url}). Tell the person first, and fix it before other "
                     f"work; close the issue once main's test passes.")
    items = open_items(repo)
    if items:
        lines.append(f"OPEN FAILURES ({len(items)}): an unattended job filed these "
                     "under todo/ because it could not report them anywhere else. "
                     "Tell the person, and fix them before other work:")
        for f, title in items:
            lines.append(f"  - {f.relative_to(repo)}: {title}")
    tests = alerting_tests(repo)
    if tests:
        lines.append(f"ALERTING TESTS ({len(tests)}): a job failed on purpose to prove "
                     "its alert reaches the person. These are not failures. Ask the "
                     "person whether the alert arrived, check the run failed the way "
                     "the test intends, and close each on the answer "
                     "(open_failures.py --close PATH --because TEXT):")
        for f, title in tests:
            lines.append(f"  - {f.relative_to(repo)}: {title}")
    return lines


def self_check():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = write_item(td, "Landing failed: feat/x", "boom", "It lands.", "2026-10-08")
        q = write_item(td, "Landing failed: feat/x", "again", "It lands.", "2026-10-08")
        found = open_items(td)
        ok = len(found) == 2 and p != q and found[0][1] == "Landing failed: feat/x"
        q.write_text(q.read_text().replace("status:            open", "status:            done"))
        ok &= len(open_items(td)) == 1
        t = write_item(td, "Alerting test ran", "boom", "The person confirms.",
                       "2026-10-09", alerting_test=True)
        ok &= len(open_items(td)) == 1 and alerting_tests(td) == [(t, "Alerting test ran")]
        ok &= close_item(t, "the alert arrived", "2026-10-09") and not alerting_tests(td)
        ok &= not close_item(t, "again", "2026-10-09")
    print(f"open_failures self-check: {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


def main(argv):
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if "--self-check" in argv:
        return self_check()
    if argv[:1] == ["--file"]:
        try:
            title = argv[1]
            closes = argv[argv.index("--closes") + 1]
        except (IndexError, ValueError):
            print("usage: open_failures.py --file TITLE --closes TEXT [--what FILE] "
                  "[--alerting-test]", file=sys.stderr)
            return 2
        what = (pathlib.Path(argv[argv.index("--what") + 1]).read_text(encoding="utf-8")
                if "--what" in argv else sys.stdin.read())
        print(write_item(ROOT, title, what, closes,
                         alerting_test="--alerting-test" in argv).relative_to(ROOT))
        return 0
    if argv[:1] == ["--close"]:
        try:
            path = pathlib.Path(argv[1])
            because = argv[argv.index("--because") + 1]
        except (IndexError, ValueError):
            print("usage: open_failures.py --close PATH --because TEXT", file=sys.stderr)
            return 2
        if not close_item(path if path.is_absolute() else ROOT / path, because):
            print(f"{path} is not open", file=sys.stderr)
            return 1
        print(f"closed {path}")
        return 0
    for line in report_lines():
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
