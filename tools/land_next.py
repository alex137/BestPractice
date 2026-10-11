#!/usr/bin/env python3
"""The lander as one command: land every queued branch on the trunk, oldest first, or say exactly why not

    python3 tools/land_next.py              # land the whole queue, then
                                            # Update Vendors on the trunk if behind
    python3 tools/land_next.py --once       # land at most one branch
    python3 tools/land_next.py --no-vendor  # land the queue and skip the update
    python3 tools/land_next.py --in-place   # land in this checkout, not a worktree
    python3 tools/land_next.py --self-check # a scratch repository, stubbed gates

A session that is ready to land a branch pushes it, queues it with
tools/land_queue.py, and runs this; any session lands the whole queue, its
own branches and anyone else's. What differs between repositories (the
trunk's name, the repository's own audits, its caches, its ledgers, the
generated lists it may rebuild) is precedent.json's "lander" block; see
lander_config. A repository may keep a two-line shim at a path its
permissions already allow; it changes nothing but the path.

For each branch `land_queue.py next` names, it:

1. waits its turn for the lock Promote and --land take (the branch
   precedent-promote-lock; a busy lock is waited out, up to ten minutes),
   then marks it `landing`, fetches it, and merges the commit that was queued
   (never a later one) into the trunk with `--no-ff`; a conflict confined
   to the generated lists it may rebuild is rebuilt, any other fails;
2. runs the repository's own gates;
3. resyncs the practice views, as a commit of its own if they moved;
4. runs the push check until it leaves no check-ledger files changed;
5. pushes the trunk, and on a rejected push (someone pushed without the
   lock) waits a few jittered seconds and starts that branch over on the
   new trunk, at most three times;
6. confirms by a fresh fetch that the merge commit is on the trunk, and
   only then marks the branch `landed`.

EVERY LANDING TAKES UPDATE VENDORS. Once the queue is landed, the vendor
update is taken as a commit of its own, pushed after the basic check only,
and the last line names the full check to run next,
`tools/precedent_check_after.py --commit SHA`, which a session runs as a
background task. A red result is filed under todo/ and pushed (it is listed
at every session start). A branch's own changes keep their full check
before the push. `--no-vendor` skips the update.

It does all of this in a worktree of its own, detached at the trunk on
origin and removed when it finishes, never in the checkout it is run from:
run in place, it switched the session's own checkout and built the landing
merge there, and for the whole push check the session reported that
half-done merge as unpushed work.

A merge conflict, a red gate or a third rejected push resets the trunk to
origin's, marks the branch `failed` with the finding, files the failure as
an open item under todo/ (and opens a GitHub issue where it can); the run
goes on to the next branch. It never force-pushes and never rewrites
history. It refuses to start unless the checkout is clean and the local
trunk holds nothing origin lacks, so the reset can only ever discard the
script's own merge.

Exit status: 0 when every branch it took landed (or the queue was empty),
1 when any failed, 2 when it refused to start.
"""
import contextlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import land_queue  # noqa: E402
import open_failures  # noqa: E402

BESTPRACTICE = ROOT.parent / "BestPractice"
BESTPRACTICE_URL = "https://github.com/alex137/BestPractice"


def _landing_branch(root, pj):
    """-> the branch a Booked lands on here: precedent_branches.landing_branch,
    the one definition --land and --landing read.

    WHY (2026-10-10). This read only precedent.json's base_branch, else
    main. A consumer whose precedent.json says "landing_branch": "staging",
    with no lander block, had a docs branch queued and landed straight onto
    main, past staging -- promote-only broken by the tool meant to keep it.
    Every consumer but one carrying this lander was in that shape. An engine
    too old to carry the function falls back to the setting itself."""
    main = pj.get("base_branch") or "main"
    try:
        import precedent_branches as pb
        branch = pb.landing_branch(pathlib.Path(root))[0]
    except Exception:  # noqa: BLE001
        branch = pj.get("landing_branch") or "main"
    # The resolver's "main" is the role, the trunk; a repository whose trunk
    # is called something else names it in base_branch.
    return main if branch == "main" else branch


def lander_config(root):
    """The repository's own part of the lander: precedent.json's "lander"
    block. Everything else here is the same in every repository.

      trunk          the branch it lands on (default: the landing branch
                     tools/precedent_branches.py --landing names -- the
                     person's, then precedent.json's -- read by its own
                     function, landing_branch, so the two can never differ)
      gates          [[name, command...], ...] run on each merge before the
                     push check -- the repository's own audits
      shared_caches  gitignored cache directories a landing worktree links
                     to the checkout's copy, so a gate reuses its solves
      ledgers        files the push check may leave changed (its fact
                     ledgers), committed as a commit of their own
      rebuilt        {path: command} generated lists a merge may conflict
                     on; a conflict confined to them is rebuilt, not failed
    """
    import json
    try:
        pj = json.loads((root / "precedent.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pj = {}
    cfg = pj.get("lander") or {}
    return {
        "trunk": cfg.get("trunk") or _landing_branch(root, pj),
        "gates": tuple((g[0], list(g[1:])) for g in cfg.get("gates", [])),
        "shared_caches": tuple(cfg.get("shared_caches", [".cache"])),
        "ledgers": tuple(cfg.get("ledgers", [])),
        "rebuilt": {k: list(v) for k, v in cfg.get("rebuilt", {}).items()},
    }


CFG = lander_config(ROOT)
TRUNK = CFG["trunk"]
# Gitignored on-disk caches the gates read (content-keyed model solves and
# the like). A worktree starts without them, so landing_worktree links each
# to the checkout's own copy: a gate then reuses the solves this machine
# already has instead of re-solving them cold. .gitignore must name each
# without a trailing slash, so the link is ignored as the directory is.
SHARED_CACHES = CFG["shared_caches"]
LEDGERS = CFG["ledgers"]
GATES = CFG["gates"]
# --gate: a tree that already passed the full check (the branch's own run,
# or the Update Vendors run just before; recorded in .git and shared through
# the receipt branch) is not checked again -- a --no-ff merge onto an
# unmoved master has exactly the branch's tree. Anything else runs in full.
# Found 2026-10-08: a landing right after Update Vendors re-ran the whole
# check on files the update had just passed.
PUSH_CHECK = ["python3", "tools/precedent_push_check.py", "--gate"]
# The vendor update lands after this one only; its full check runs after
# (tools/precedent_check_after.py), so a landing never waits on it.
BASIC_CHECK = ["python3", "tools/precedent_push_check.py", "--tier", "basic"]
# The practice views (AGENTS.md, practices/, tools/checks/, MANIFEST.json)
# are generated from the practice sets precedent.json declares, and a shared
# set changes on its own schedule: on 2026-10-05 a set was edited three times
# in an afternoon, and each time the push check refused every landing until
# someone resynced by hand. The lander resyncs them itself, as a commit of
# its own, before the push check judges the merge.
SYNC_VIEWS = ["python3", "tools/precedent_sync_views.py", "--repo", "."]
# Generated lists the merge may conflict on, each with the command that
# rebuilds it from the files it lists. A conflict confined to these is no
# judgment call: the lander rebuilds them and finishes the merge. Found
# 2026-10-08: two branches that each added an open item failed to land on
# todo/TODO.md, and the fix by hand was exactly this rebuild.
REBUILT = CFG["rebuilt"]
PUSH_TRIES = 3
TRAILER = ("\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n"
           "Landed-By: tools/land_next.py")


class Refused(Exception):
    """The run cannot start, or cannot go on, without a person."""


def log(msg, t0=[time.time()]):
    print(f"[land {int(time.time() - t0[0]):>4}s] {msg}", flush=True)


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed: {(r.stderr or r.stdout).strip()[-400:]}")
    return r


def run(repo, cmd):
    """-> (ok, full output)."""
    r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def dirty(repo):
    """`git status --porcelain` lines, less the cache links landing_worktree
    made: a master whose .gitignore still names a cache with a trailing
    slash (as before 2026-10-05) lists the link as untracked."""
    links = {f"?? {rel}" for rel in SHARED_CACHES}
    return [ln for ln in git(repo, "status", "--porcelain").stdout.splitlines()
            if ln.strip() and ln not in links]


def tail(text, n=6):
    return "\n".join(text.splitlines()[-n:])


@contextlib.contextmanager
def landing_worktree(root):
    """A worktree of `root`, detached at a fresh origin/master, removed on
    the way out whatever happened inside. Detached because master may be
    checked out in `root` itself, and git checks a branch out in one
    worktree only; the push names its target (HEAD:master) instead."""
    git(root, "fetch", "-q", "origin", TRUNK)
    path = pathlib.Path(tempfile.mkdtemp(prefix=f"{ROOT.name}-land-"))
    path.rmdir()
    git(root, "worktree", "add", "-q", "--detach", str(path), f"origin/{TRUNK}")
    for rel in SHARED_CACHES:
        if (root / rel).is_dir() and not (path / rel).exists():
            (path / rel).parent.mkdir(parents=True, exist_ok=True)
            os.symlink(root / rel, path / rel)
    try:
        yield path
    finally:
        git(root, "worktree", "remove", "--force", str(path), check=False)
        shutil.rmtree(path, ignore_errors=True)
        git(root, "worktree", "prune", check=False)


def followed_branch(repo):
    """The BestPractice branch this repo takes its updates from: the
    `upstream_branch` its precedent.json names (main or staging), else main.
    Read by this checkout's vendored engine (tools/precedent_vendor_engine.py
    followed_branch), so the lander and Update Vendors can never disagree
    about it; main where that engine predates upstream_branch."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        try:
            import precedent_vendor_engine as pve
        finally:
            sys.path.pop(0)
        return pve.followed_branch(pathlib.Path(repo))
    except Exception:  # noqa: BLE001
        return "main"


def prepare(repo, bestpractice, detached=False):
    """Master up to date and clean, or Refused. -> True when the BestPractice
    clone is on an up-to-date copy of the branch this repo follows
    (followed_branch: main, or staging since 2026-10-05), so the vendor step
    may run from it.
    `detached`: `repo` is the lander's own worktree, already at origin/master."""
    if dirty(repo):
        raise Refused("the checkout has uncommitted changes; the lander will not reset over them")
    git(repo, "fetch", "-q", "origin", TRUNK)
    if detached:
        git(repo, "checkout", "-q", "--detach", f"origin/{TRUNK}")
    else:
        git(repo, "checkout", "-q", TRUNK)
        ahead = git(repo, "rev-list", "--count", f"origin/{TRUNK}..{TRUNK}").stdout.strip()
        if ahead != "0":
            raise Refused(f"local {TRUNK} has {ahead} commit(s) origin lacks; push or move them first")
        git(repo, "merge", "-q", "--ff-only", f"origin/{TRUNK}")
    if git(repo, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        git(repo, "fetch", "-q", "--unshallow", "origin")
    if bestpractice is None:
        return False
    if not (bestpractice / ".git").exists():
        r = subprocess.run(["git", "clone", "-q", BESTPRACTICE_URL, str(bestpractice)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log(f"could not clone BestPractice; vendor step skipped: {r.stderr.strip()[-200:]}")
            return False
    if git(bestpractice, "status", "--porcelain").stdout.strip():
        log("BestPractice clone has local changes; left as it is, vendor step skipped")
        return False
    on = git(bestpractice, "branch", "--show-current", check=False).stdout.strip()
    follow = followed_branch(repo)
    if on != follow:
        # Someone is working on a branch there; moving it would pull their
        # checkout out from under them mid-task (found 2026-10-04). And
        # Update Vendors runs the clone's own tools, so on their branch it
        # would run unreviewed code: the vendor step is skipped instead.
        log(f"BestPractice clone is on {on or 'a detached HEAD'}; left there, vendor step skipped")
        return False
    return git(bestpractice, "pull", "-q", "--ff-only", "origin", follow,
               check=False).returncode == 0


@contextlib.contextmanager
def landing_lock(repo, what):
    """Hold the lock Promote and --land take (precedent_branches.py,
    wait_for_landing_lock) for one landing, waiting while another window
    holds it. Yields None once held, or when the lock cannot be used at all
    (the landing goes ahead as before); yields the holder when it stayed
    held past the wait, and the caller lands nothing. Master is reset to
    origin's after the claim, so the landing starts from the trunk as it is
    once the turn is ours."""
    try:
        import precedent_branches as pb
    except Exception as e:  # noqa: BLE001
        log(f"landing lock not used: precedent_branches did not import ({e})")
        yield None
        return
    state, info = pb.wait_for_landing_lock(repo, what, log)
    if state == "busy":
        yield info
        return
    if state == "none":
        log(f"landing lock not used: {info}")
    reset_to_origin(repo)
    try:
        yield None
    finally:
        if state == "held":
            pb.release_hold(repo, info)


def retry_pause(attempt, sleep=time.sleep):
    """A short, jittered wait before starting over on a moved trunk, so a
    push that keeps losing to one that does not take the lock is not retried
    in step with it."""
    import random
    sleep(min(5 * 2 ** (attempt - 1), 30) * (0.5 + random.random()))


def reset_to_origin(repo):
    git(repo, "merge", "--abort", check=False)
    git(repo, "fetch", "-q", "origin", TRUNK)
    git(repo, "reset", "-q", "--hard", f"origin/{TRUNK}")


def file_failure(repo, title, finding, closes):
    """Write a failure as an open item under todo/ and push it to master,
    where a later session finds it (open_failures.py). An issue needs gh
    signed in; this needs only the push the lander already makes.
    -> the item's path, or "" when it could not be pushed."""
    for _ in range(PUSH_TRIES):
        try:
            reset_to_origin(repo)
            path = open_failures.write_item(repo, title, finding, closes)
            run(repo, ["python3", "tools/build_todo_index.py"])
            # -A, not todo/: the index builder may also list its files in
            # tools/generated_files.json, and the tree was reset just above.
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", f"Open failure: {title}{TRAILER}")
        except Exception as e:  # noqa: BLE001
            log(f"could not file the failure under todo/: {e}")
            reset_to_origin(repo)
            return ""
        ok, detail = check_and_push(repo, BASIC_CHECK)
        if ok:
            return str(path.relative_to(repo))
        if detail != "rejected":
            log(f"could not push the failure item: {detail}")
            return ""
    return ""


def origin_slug(repo):
    """owner/name of origin on GitHub, or "" for any other host."""
    url = git(repo, "remote", "get-url", "origin", check=False).stdout.strip()
    if "github.com" not in url:
        return ""
    return url.split("github.com", 1)[1].lstrip(":/").removesuffix(".git").strip("/")


def report_failure(repo, branch, finding):
    """File the failure under todo/ on the trunk; also open a GitHub issue
    where gh is signed in and origin is on GitHub."""
    issue = ""
    slug = origin_slug(repo)
    if slug and shutil.which("gh"):
        body = (f"The lander (tools/land_next.py) could not land `{branch}`.\n\n"
                f"```\n{finding}\n```\n\nThe branch is marked `failed` in the landing queue "
                "(`land_queue.py list`). Fix it on the branch, push, and queue it again.")
        r = subprocess.run(["gh", "issue", "create", "--repo", slug,
                            "--title", f"Landing failed: {branch}", "--body", body],
                           cwd=str(repo), capture_output=True, text=True)
        issue = r.stdout.strip() if r.returncode == 0 else ""
    item = file_failure(repo, f"Landing failed: {branch}", finding,
                        f"`{branch}` lands, fixed on the branch and queued again "
                        "(`land_queue.py request --branch ...`), "
                        "or the person drops it.")
    return ", ".join(x for x in (issue, item) if x)


def vendor_line(out):
    """The vendor step's outcome: its last VENDORS line (the first is only
    the "behind upstream" heading)."""
    return next((ln for ln in reversed(out.splitlines()) if ln.startswith("VENDORS:")),
                "VENDORS: no VENDORS line printed")


def update_vendors(repo, push_check, vendor_cmd):
    """Take the vendor step on master itself, and land what it committed.
    -> (ok, line, landed commit or "")."""
    with landing_lock(repo, f"Update Vendors on {TRUNK}") as held_by:
        if held_by:
            return False, f"vendor update: the landing lock stayed held ({held_by})", ""
        return _update_vendors(repo, push_check, vendor_cmd)


def _update_vendors(repo, push_check, vendor_cmd):
    for attempt in range(1, PUSH_TRIES + 1):
        before = git(repo, "rev-parse", "HEAD").stdout.strip()
        line = vendor_line(run(repo, vendor_cmd)[1])
        log(line)
        if git(repo, "rev-parse", "HEAD").stdout.strip() == before:
            reset_to_origin(repo)
            return True, line, ""
        ok, detail = check_and_push(repo, push_check)
        if ok:
            return True, f"{line} landed in {detail}", detail
        if detail != "rejected":
            return False, f"{line} -- not landed: {detail}", ""
        log(f"push rejected, {TRUNK} moved; taking the vendor step again")
        if attempt < PUSH_TRIES:
            retry_pause(attempt)
    return False, f"vendor update: push rejected {PUSH_TRIES} times", ""


def check_and_push(repo, push_check):
    """Run the push check until it leaves nothing but committed ledgers, push
    master, and prove the result by a fresh fetch. -> (True, merge commit),
    (False, "rejected") when master moved, or (False, finding). On anything
    but success master is reset to origin/master."""
    for _ in range(3):
        ok, out = run(repo, push_check)
        if not ok:
            reset_to_origin(repo)
            return False, f"push check failed:\n{tail(out)}"
        changed = dirty(repo)
        if not changed:
            break
        paths = {ln[3:] for ln in changed}
        if not paths <= set(LEDGERS):
            reset_to_origin(repo)
            return False, "push check left files other than the check ledgers changed: " + \
                ", ".join(sorted(paths))
        git(repo, "add", *sorted(paths))
        git(repo, "commit", "-q", "-m", "Check ledgers: facts recorded by the push check" + TRAILER)
    else:
        reset_to_origin(repo)
        return False, "push check kept changing the ledgers after three runs"
    log("push check passed")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    pushed = git(repo, "push", "-q", "origin", f"HEAD:refs/heads/{TRUNK}", check=False)
    if pushed.returncode != 0:
        # Only a trunk that MOVED is a race worth starting over for
        # (2026-10-10: three attempts each said "master moved" while the
        # trunk sat still and a pre-push hook refused every push, its reason
        # thrown away). The trunk moved when origin's tip is no longer in
        # what this attempt built on.
        git(repo, "fetch", "-q", "origin", TRUNK, check=False)
        moved = git(repo, "merge-base", "--is-ancestor", f"origin/{TRUNK}", head,
                    check=False).returncode != 0
        reset_to_origin(repo)
        if moved:
            return False, "rejected"
        said = (pushed.stderr or pushed.stdout).strip()
        return False, (f"push refused, and {TRUNK} did not move, so trying again would "
                       f"be refused the same way. What the push said:\n{said[-1500:]}")
    git(repo, "fetch", "-q", "origin", TRUNK)
    if git(repo, "merge-base", "--is-ancestor", head, f"origin/{TRUNK}", check=False).returncode != 0:
        reset_to_origin(repo)
        return False, f"push reported success but {head[:12]} is not on origin/{TRUNK}"
    return True, head[:12]


def resync_views(repo, sync_cmd):
    """Regenerate the practice views and commit what changed, as its own
    commit. -> (ok, detail). Nothing changed is ok; a failed sync is not."""
    if not sync_cmd:
        return True, "not run"
    ok, out = run(repo, sync_cmd)
    if not ok:
        return False, f"practice views did not resync:\n{tail(out)}"
    if not dirty(repo):
        return True, "current"
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m",
        "Practice views: resync to the sets precedent.json declares" + TRAILER)
    return True, "resynced"


def rebuild_generated(repo, branch):
    """A merge that conflicts only on REBUILT lists: rebuild them, commit the
    merge, -> True. Anything else, or a rebuild that fails: -> False, with
    the merge left as it was for the caller to reset."""
    files = git(repo, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
    if not files or any(f not in REBUILT for f in files):
        return False
    for cmd in dict.fromkeys(tuple(REBUILT[f]) for f in files):
        ok, out = run(repo, list(cmd))
        if not ok:
            log(f"{branch}: rebuilding {' '.join(cmd)} failed:\n{tail(out)}")
            return False
    git(repo, "add", *files)
    if git(repo, "diff", "--name-only", "--diff-filter=U", check=False).stdout.strip():
        return False
    log(f"{branch}: conflict only in generated {', '.join(files)}; rebuilt them")
    return git(repo, "commit", "-q", "--no-edit", check=False).returncode == 0


def land_one(repo, store, rec, gates, push_check, vendor_cmd, sync_cmd=SYNC_VIEWS):
    """-> (landed, detail). Leaves master equal to origin/master either way."""
    branch, commit = rec["branch"], rec["commit"]
    land_queue.mark(store, branch, "landing")
    git(repo, "fetch", "-q", "origin", branch, check=False)
    if git(repo, "cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode != 0:
        return False, f"commit {commit[:12]} is not on origin any more (the branch was rewritten?)"
    with landing_lock(repo, f"landing {branch} on {TRUNK}") as held_by:
        if held_by:
            return False, f"the landing lock stayed held ({held_by}); {TRUNK} did not move"
        return _land_attempts(repo, branch, commit, gates, push_check, vendor_cmd, sync_cmd)


def _land_attempts(repo, branch, commit, gates, push_check, vendor_cmd, sync_cmd):
    for attempt in range(1, PUSH_TRIES + 1):
        log(f"{branch}: merging {commit[:12]} (attempt {attempt})")
        m = git(repo, "merge", "--no-ff", "--no-edit", "-m",
                f"Land {branch}{TRAILER}", commit, check=False)
        if m.returncode != 0 and rebuild_generated(repo, branch):
            m = git(repo, "rev-parse", "HEAD", check=False)
        if m.returncode != 0:
            files = git(repo, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
            reset_to_origin(repo)
            return False, ("merge conflict needing judgment in: " + ", ".join(files)) if files \
                else f"merge failed: {(m.stderr or m.stdout).strip()[-300:]}"
        for name, cmd in gates:
            ok, out = run(repo, cmd)
            if not ok:
                reset_to_origin(repo)
                return False, f"{name} failed:\n{tail(out)}"
            log(f"{branch}: {name} passed")
        ok, views = resync_views(repo, sync_cmd)
        if not ok:
            reset_to_origin(repo)
            return False, views
        if views == "resynced":
            log(f"{branch}: practice views resynced to the declared sets")
        vendors = "VENDORS: not run"
        if vendor_cmd:
            vendors = vendor_line(run(repo, vendor_cmd)[1])
            log(f"{branch}: {vendors}")
        ok, detail = check_and_push(repo, push_check)
        if ok:
            return True, f"{detail} {vendors}"
        if detail != "rejected":
            return False, detail
        log(f"{branch}: push rejected, {TRUNK} moved; starting over on the new {TRUNK}")
        if attempt < PUSH_TRIES:
            retry_pause(attempt)
    return False, f"push rejected {PUSH_TRIES} times; {TRUNK} kept moving"


def land_queue_run(repo=ROOT, once=False, vendor=False, gates=GATES, push_check=PUSH_CHECK,
                   bestpractice=BESTPRACTICE, store=None, vendor_cmd=None, in_place=True,
                   sync_cmd=SYNC_VIEWS):
    """`in_place=False` lands from a worktree of `repo` (see landing_worktree)."""
    if not in_place:
        try:
            with landing_worktree(repo) as wt:
                log(f"landing from a worktree of its own: {wt}")
                return _land_queue_run(wt, once, vendor, gates, push_check, bestpractice,
                                       store or land_queue._store(repo), vendor_cmd,
                                       detached=True, sync_cmd=sync_cmd)
        except Refused as e:
            print(f"REFUSED: {e}")
            return 2
    return _land_queue_run(repo, once, vendor, gates, push_check, bestpractice, store,
                           vendor_cmd, detached=False, sync_cmd=sync_cmd)


def _land_queue_run(repo, once, vendor, gates, push_check, bestpractice, store, vendor_cmd,
                    detached, sync_cmd=SYNC_VIEWS):
    store = store or land_queue._store(repo)
    try:
        bp_ready = prepare(repo, bestpractice, detached=detached)
    except Refused as e:
        print(f"REFUSED: {e}")
        return 2
    land_queue.beat(store, "lander")
    if vendor_cmd is None and bp_ready:
        vendor_cmd = ["python3", "tools/precedent_merge_vendors.py", "--source", str(bestpractice),
                      "--skip-check"]
    results = []
    while True:
        rec = land_queue.next_queued(store)
        if rec is None:
            break
        branch = rec["branch"]
        try:
            landed, detail = land_one(repo, store, rec, gates, push_check, None, sync_cmd)
        except Refused as e:
            reset_to_origin(repo)
            landed, detail = False, str(e)
        if landed:
            land_queue.mark(store, branch, "landed", detail)
        else:
            issue = report_failure(repo, branch, detail)
            land_queue.mark(store, branch, "failed", detail + (f" (issue: {issue})" if issue else ""))
        results.append((branch, landed, detail))
        log(f"{'LANDED' if landed else 'FAILED'} {branch}")
        if once:
            break
    vendor_ok = True
    # --no-vendor means no vendor step at all (2026-10-10: it was taken
    # anyway once a branch landed, and printed "VENDORS: updated").
    take = vendor
    if take and not vendor_cmd:
        print(f"VENDORS: NOT TAKEN -- the BestPractice clone is not on a clean, current "
              f"{followed_branch(repo)} (see the log above)")
    after = ""
    if take and vendor_cmd:
        land_queue.beat(store, "vendor_update")
        # a caller that stubs the push check (the self-check) stubs this one too
        basic = BASIC_CHECK if push_check == PUSH_CHECK else push_check
        vendor_ok, line, after = update_vendors(repo, basic, vendor_cmd)
        print(line)
        if not vendor_ok:
            report_failure(repo, "vendor update", line)
    if not results:
        print("queue empty")
        return 0 if vendor_ok else 1
    for branch, landed, detail in results:
        print(f"LANDED {branch} {detail}" if landed else f"FAILED {branch}: {detail}")
    if after:
        print(f"CHECK AFTER: the vendor update landed after the basic check only; run its "
              f"full check now, in the background: python3 tools/precedent_check_after.py "
              f"--commit {after}")
    return 0 if vendor_ok and all(landed for _, landed, _ in results) else 1


def self_check():
    """A scratch origin with master and three queued branches: one clean, one
    that a stub gate rejects, one that conflicts. Checks that the clean one
    lands with a fresh fetch to prove it, the other two are marked failed,
    origin's master holds only the clean merge, and a dirty checkout is
    refused before anything moves."""
    import tempfile
    env = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com"}
    os.environ.update(env)
    global report_failure, TRUNK, SHARED_CACHES, LEDGERS
    report_failure = lambda *a: ""  # noqa: E731 -- no issues from a scratch repo
    TRUNK, SHARED_CACHES, LEDGERS = "master", (".cache",), ()
    ok = True
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        origin, work = td / "origin.git", td / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(origin)])
        subprocess.run(["git", "clone", "-q", str(origin), str(work)], capture_output=True)
        g = lambda *a: git(work, *a)  # noqa: E731
        g("checkout", "-q", "-b", "master")
        (work / "shared.txt").write_text("base\n")
        (work / "gate.py").write_text("import sys,pathlib\n"
                                      "sys.exit(1 if pathlib.Path('bad.txt').exists() else 0)\n")
        g("add", "-A"); g("commit", "-qm", "base"); g("push", "-q", "origin", "master")
        for b, fname, text in (("feat/good", "good.txt", "ok\n"),
                               ("feat/red", "bad.txt", "x\n"),
                               ("feat/conflict", "shared.txt", "theirs\n")):
            g("checkout", "-q", "-B", b, "master")
            (work / fname).write_text(text)
            g("add", "-A"); g("commit", "-qm", b); g("push", "-q", "origin", b)
        g("checkout", "-q", "master")
        (work / "shared.txt").write_text("ours\n")
        g("commit", "-qam", "master moves"); g("push", "-q", "origin", "master")
        store = land_queue._store(work)
        for b in ("feat/good", "feat/red", "feat/conflict"):
            land_queue.request(store, b, repo=work)
        stub = [("stub gate", ["python3", "gate.py"])]
        (work / "stray.txt").write_text("uncommitted\n")
        rc = land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None, store=store, sync_cmd=None)
        ok &= rc == 2 and [e["status"] for e in land_queue.entries(store)] == ["queued"] * 3
        (work / "stray.txt").unlink()
        rc = land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None, store=store, sync_cmd=None)
        status = {e["branch"]: e["status"] for e in land_queue.entries(store)}
        ok &= rc == 1 and status == {"feat/good": "landed", "feat/red": "failed",
                                     "feat/conflict": "failed"}
        g("fetch", "-q", "origin", "master")
        files = set(g("ls-tree", "--name-only", "origin/master").stdout.split())
        ok &= files == {"shared.txt", "gate.py", "good.txt"}
        ok &= not g("status", "--porcelain").stdout.strip()
        ok &= "lander" in land_queue.beats(store)
        ok &= land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None,
                             store=store, sync_cmd=None) == 0
        (td / "vendor.py").write_text(
            "import pathlib,subprocess\n"
            "pathlib.Path('vendored.txt').write_text('v\\n')\n"
            "subprocess.run(['git','add','vendored.txt']);"
            "subprocess.run(['git','commit','-qm','vendor'])\n"
            "print('VENDORS: updated')\n")
        rc = land_queue_run(work, vendor=True, gates=stub, push_check=["true"],
                            bestpractice=None, store=store, sync_cmd=None,
                            vendor_cmd=["python3", str(td / "vendor.py")])
        g("fetch", "-q", "origin", "master")
        ok &= rc == 0 and "vendored.txt" in g("ls-tree", "--name-only", "origin/master").stdout
        ok &= "vendor_update" in land_queue.beats(store)
        # Landing from a worktree: the checkout it is run from sits on a
        # working branch with an uncommitted file, and neither moves; the
        # branch lands, and the worktree is gone afterwards.
        g("checkout", "-q", "-B", "feat/wt", "origin/master")
        (work / "wt.txt").write_text("from a worktree\n")
        g("add", "-A"); g("commit", "-qm", "feat/wt"); g("push", "-q", "origin", "feat/wt")
        land_queue.request(store, "feat/wt", repo=work)
        g("checkout", "-q", "-B", "someone-working", "origin/master")
        (work / "half-done.txt").write_text("not committed\n")
        rc = land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None,
                            store=store, in_place=False, sync_cmd=None)
        g("fetch", "-q", "origin", "master")
        ok &= rc == 0 and "wt.txt" in g("ls-tree", "--name-only", "origin/master").stdout
        ok &= g("branch", "--show-current").stdout.strip() == "someone-working"
        ok &= (work / "half-done.txt").exists()
        ok &= len(g("worktree", "list").stdout.splitlines()) == 1
        # A practice set moved since the branch last synced: the lander
        # resyncs the views as a commit of its own, and the branch lands.
        g("checkout", "-q", "-B", "feat/stale-views", "origin/master")
        (work / "views.txt").write_text("old view\n")
        g("add", "-A"); g("commit", "-qm", "feat/stale-views")
        g("push", "-q", "origin", "feat/stale-views")
        land_queue.request(store, "feat/stale-views", repo=work)
        (td / "sync.py").write_text("import pathlib\n"
                                    "pathlib.Path('views.txt').write_text('fresh view\\n')\n")
        rc = land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None,
                            store=store, in_place=False,
                            sync_cmd=["python3", str(td / "sync.py")])
        g("fetch", "-q", "origin", "master")
        ok &= rc == 0
        ok &= g("show", "origin/master:views.txt").stdout == "fresh view\n"
        ok &= "Practice views: resync" in g("log", "-3", "--format=%s", "origin/master").stdout
        # A conflict only in a generated list is rebuilt, and the branch lands.
        global REBUILT
        saved = REBUILT
        (td / "regen.py").write_text("import pathlib\n"
                                     "pathlib.Path('list.txt').write_text('rebuilt\\n')\n")
        REBUILT = {"list.txt": ["python3", str(td / "regen.py")]}
        try:
            g("checkout", "-q", "-B", "master", "origin/master")
            (work / "list.txt").write_text("base\n")
            g("add", "-A"); g("commit", "-qm", "list"); g("push", "-q", "origin", "master")
            g("checkout", "-q", "-B", "feat/list", "origin/master")
            (work / "list.txt").write_text("branch\n")
            g("commit", "-qam", "feat/list"); g("push", "-q", "origin", "feat/list")
            land_queue.request(store, "feat/list", repo=work)
            g("checkout", "-q", "master")
            (work / "list.txt").write_text("master\n")
            g("commit", "-qam", "master list"); g("push", "-q", "origin", "master")
            rc = land_queue_run(work, gates=stub, push_check=["true"], bestpractice=None,
                                store=store, in_place=False, sync_cmd=None)
            g("fetch", "-q", "origin", "master")
            ok &= rc == 0 and g("show", "origin/master:list.txt").stdout == "rebuilt\n"
        finally:
            REBUILT = saved
        # The branch the vendor step needs the BestPractice clone on is the
        # one precedent.json follows: main by default, staging when declared.
        ok &= followed_branch(work) == "main"
        (work / "precedent.json").write_text('{"upstream_branch": "staging"}\n')
        ok &= followed_branch(work) == "staging"
        (work / "precedent.json").write_text('{"upstream_branch": "pre-staging"}\n')
        ok &= followed_branch(work) == "main"
        # The repository's own part comes from precedent.json's "lander" block.
        (td / "precedent.json").write_text(
            '{"base_branch": "master", "lander": {"gates": [["audit", "python3", "a.py"]],'
            ' "ledgers": ["l.jsonl"], "rebuilt": {"todo/TODO.md": ["python3", "b.py"]}}}\n')
        cfg = lander_config(td)
        ok &= cfg["trunk"] == "master" and cfg["gates"] == (("audit", ["python3", "a.py"]),)
        ok &= cfg["ledgers"] == ("l.jsonl",) and cfg["shared_caches"] == (".cache",)
        ok &= cfg["rebuilt"] == {"todo/TODO.md": ["python3", "b.py"]}
        (td / "precedent.json").write_text('{"lander": {"trunk": "trunk"}}\n')
        ok &= lander_config(td)["trunk"] == "trunk"
        # The landing branch decides, as --land reads it (2026-10-10: a
        # repo landing on staging, with no lander block, landed on main).
        (td / "precedent.json").write_text('{"landing_branch": "staging"}\n')
        ok &= lander_config(td)["trunk"] == "staging"
        (td / "precedent.json").write_text('{"landing_branch": "staging", "base_branch": "main",'
                                           ' "lander": {"trunk": "elsewhere"}}\n')
        ok &= lander_config(td)["trunk"] == "elsewhere"
        (td / "precedent.json").unlink()
        ok &= lander_config(td) == {"trunk": "main", "gates": (), "shared_caches": (".cache",),
                                    "ledgers": (), "rebuilt": {}}
    print("land_next self-check:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if "--self-check" in argv:
        return self_check()
    if set(argv) - {"--once", "--vendor", "--no-vendor", "--in-place"}:
        print(__doc__.split("\n\n")[1])
        return 2
    # Every landing takes Update Vendors (S. Alexander Jacobson, 2026-10-02:
    # "Can we set up a system so merge also does vendor updates?"). Until
    # 2026-10-08 it needed --vendor, which the runbook's plain command never
    # passed, so a day of landings left the vendored copies behind. --vendor
    # is still accepted and changes nothing.
    return land_queue_run(once="--once" in argv, vendor="--no-vendor" not in argv,
                          in_place="--in-place" in argv)


if __name__ == "__main__":
    sys.exit(main())
