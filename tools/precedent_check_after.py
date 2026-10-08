#!/usr/bin/env python3
"""The full check of a commit that already landed, run in the background; a failure is filed under todo/ and pushed

    python3 tools/precedent_check_after.py [--commit SHA] [--branch BRANCH]
    python3 tools/precedent_check_after.py --self-check

For a repository whose precedent.json says `update_full_check: after`,
Update Vendors runs the basic check only and names this command to start
once the update is pushed (Alex, 2026-10-08, decided: "Yes let's do that",
on running the update's full check after it lands). Any job that pushed
first and checks after may use it the same way.

It checks COMMIT (default HEAD) in a worktree of its own, so the checkout it
was started from is free while it runs, with the push check's full tier
(--gate: a tree that already passed is not checked again). Passed: exit 0.
Failed: the finding is written as an open blocker item under todo/
(tools/open_failures.py; practice: automation-issues), committed on a fresh
copy of origin/BRANCH (default: the landing branch, else the current one),
and pushed there, where the next session is told of it at start; exit 1.
The fix, or a revert of the commit, then lands like any other change.
"""
import contextlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import open_failures  # noqa: E402

PUSH_TRIES = 3
FULL = ["--gate", "--tier", "full"]


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, check=check)


def tail(text, n=40):
    return "\n".join(text.strip().splitlines()[-n:])


@contextlib.contextmanager
def worktree(root, ref):
    path = pathlib.Path(tempfile.mkdtemp(prefix="precedent-check-after-"))
    path.rmdir()
    git(root, "worktree", "add", "-q", "--detach", str(path), ref)
    try:
        yield path
    finally:
        git(root, "worktree", "remove", "--force", str(path), check=False)
        shutil.rmtree(path, ignore_errors=True)
        git(root, "worktree", "prune", check=False)


def default_branch(root):
    """The branch the work landed on: the landing branch when origin has
    it, else precedent.json's base_branch, else the current branch. Found
    2026-10-08: a consumer whose trunk is `master` resolves its landing
    branch to the word "main", which its origin does not have -- and a
    failure pushed there would have opened a stray branch."""
    import json
    def on_origin(name):
        return bool(name) and git(root, "ls-remote", "--exit-code", "--heads", "origin",
                                  name, check=False).returncode == 0
    try:
        import precedent_branches as pb
        landing = pb.landing_branch(root)[0]
    except Exception:                                          # noqa: BLE001
        landing = None
    if on_origin(landing):
        return landing
    try:
        base = json.loads((root / "precedent.json").read_text(encoding="utf-8")).get("base_branch")
    except (OSError, ValueError, AttributeError):
        base = None
    if on_origin(base):
        return base
    return git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def run_check(tree, args=FULL):
    r = subprocess.run([sys.executable, str(tree / "tools" / "precedent_push_check.py"), *args],
                       cwd=str(tree), capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def file_failure(root, branch, title, finding, closes):
    """Commit the failure item on a fresh origin/BRANCH and push it.
    -> the item's path, or "" when it could not be pushed."""
    for _ in range(PUSH_TRIES):
        git(root, "fetch", "-q", "origin", branch, check=False)
        with worktree(root, f"origin/{branch}") as wt:
            item = open_failures.write_item(wt, title, finding, closes)
            git(wt, "add", "todo")
            if git(wt, "commit", "-q", "-m", f"Open failure: {title}", check=False).returncode:
                return ""
            if git(wt, "push", "-q", "origin", f"HEAD:{branch}", check=False).returncode == 0:
                return str(item.relative_to(wt))
    return ""


def check_after(root, commit, branch, args=FULL):
    sha = git(root, "rev-parse", commit).stdout.strip()
    with worktree(root, sha) as wt:
        ok, out = run_check(wt, args)
    if ok:
        print(f"CHECKED AFTER {sha[:12]}: the full check passed.")
        return 0
    item = file_failure(
        root, branch, f"Commit {sha[:12]} failed its full check after it landed", tail(out),
        f"`{branch}` passes the full check again: the failure is fixed and landed, "
        f"or `{sha[:12]}` is reverted.")
    print(f"CHECK AFTER FAILED {sha[:12]}: it failed the full check after landing on "
          f"{branch}. Tell the person; fix it, or revert {sha[:12]}. "
          + (f"Filed as {item} on {branch}." if item else
             "It could NOT be filed under todo/ either: say so.")
          + f"\n{tail(out)}")
    return 1


def self_check():
    """A scratch origin and clone: a passing check files nothing; a failing
    one pushes exactly one open failure item to origin's branch."""
    import os
    os.environ.update({"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
                       "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com"})
    global run_check
    real = run_check
    ok = True
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        origin, work = td / "origin.git", td / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(origin), str(work)], capture_output=True)
        git(work, "checkout", "-q", "-b", "main")
        (work / "a.txt").write_text("a\n")
        git(work, "add", "-A"); git(work, "commit", "-qm", "base")
        git(work, "push", "-q", "origin", "main")
        try:
            run_check = lambda tree, args=FULL: (True, "fine")    # noqa: E731
            ok &= check_after(work, "HEAD", "main") == 0
            run_check = lambda tree, args=FULL: (False, "planted")  # noqa: E731
            ok &= check_after(work, "HEAD", "main") == 1
        finally:
            run_check = real
        listed = git(work, "ls-tree", "-r", "--name-only", "origin/main").stdout
        git(work, "fetch", "-q", "origin", "main")
        listed = git(work, "ls-tree", "-r", "--name-only", "origin/main").stdout
        ok &= sum(1 for l in listed.splitlines() if l.startswith("todo/todo-")) == 1
        ok &= git(work, "worktree", "list").stdout.count("\n") == 1
    print(f"precedent_check_after self-check: {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


def main(argv):
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if "--self-check" in argv:
        return self_check()
    root = pathlib.Path(git(pathlib.Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    commit = argv[argv.index("--commit") + 1] if "--commit" in argv else "HEAD"
    branch = argv[argv.index("--branch") + 1] if "--branch" in argv else default_branch(root)
    return check_after(root, commit, branch)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
