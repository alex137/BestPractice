#!/usr/bin/env python3
"""The landing queue: branches waiting for the lander to merge them into the trunk, one record per branch on the coord branch

A session that is ready to land a branch pushes it, queues it here, and runs
tools/land_next.py, which takes the whole queue one branch at a time
(Alex, 2026-10-04: "1, any session lands the queue"). Records live on the `coord` branch under
`land-queue/`, written with the same git plumbing as the lease board
(tools/branch_store.py): the working tree is never touched and `git push` is
the lock.

    python3 tools/land_queue.py request [--branch B] [--note TEXT]
    python3 tools/land_queue.py list
    python3 tools/land_queue.py next          # the lander: oldest queued, as JSON
    python3 tools/land_queue.py mark BRANCH STATUS [--detail TEXT]
                                                     # STATUS: landing | landed | failed | queued
    python3 tools/land_queue.py --self-check

A request records the branch's commit on origin at the time it was queued;
the lander lands that commit, never a later one, so pushing more work to the
branch means queueing it again.
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import branch_store  # noqa: E402

DIR = "land-queue"
STATUSES = ("queued", "landing", "landed", "failed")


def _store(repo=ROOT, remote="origin"):
    return branch_store.BranchStore(remote=remote, branch="coord", repo=str(repo))


def _key(branch):
    return branch.replace("/", "__") + ".json"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def entries(store):
    tip = store.fetch()
    if tip is None:
        return []
    out = []
    for name in store.list(tip, DIR):
        text = store.read(tip, f"{DIR}/{name}")
        try:
            out.append(json.loads(text))
        except (TypeError, ValueError):
            continue
    return sorted(out, key=lambda e: e.get("requested_at", ""))


def request(store, branch, note="", repo=ROOT, remote="origin"):
    r = _git(repo, "ls-remote", "--heads", remote, branch)
    line = r.stdout.split()
    if r.returncode != 0 or not line:
        raise SystemExit(f"land_queue: {branch} is not on {remote}; push it first.")
    commit = line[0]
    rec = {"branch": branch, "commit": commit, "status": "queued",
           "requested_at": _now(), "requested_by": os.environ.get("CLAUDE_SESSION_URL", ""),
           "note": note, "history": []}

    def mutate(tip):
        return {f"{DIR}/{_key(branch)}": json.dumps(rec, indent=2) + "\n"}, ()
    store.transact(mutate, f"land-queue: queue {branch} at {commit[:12]}")
    return rec


def mark(store, branch, status, detail=""):
    if status not in STATUSES:
        raise SystemExit(f"land_queue: status must be one of {', '.join(STATUSES)}")

    def mutate(tip):
        text = store.read(tip, f"{DIR}/{_key(branch)}") if tip else None
        if text is None:
            raise SystemExit(f"land_queue: {branch} is not in the queue")
        rec = json.loads(text)
        rec.setdefault("history", []).append(
            {"at": _now(), "from": rec.get("status"), "to": status, "detail": detail})
        rec["status"] = status
        rec["detail"] = detail
        return {f"{DIR}/{_key(branch)}": json.dumps(rec, indent=2) + "\n"}, ()
    store.transact(mutate, f"land-queue: {branch} -> {status}")


BEATS = "heartbeats"


def beat(store, job):
    """Record that `job` ran now (heartbeats/<job>.json on the coord branch)."""
    rec = {"job": job, "at": _now(), "by": os.environ.get("CLAUDE_SESSION_URL", "")}

    def mutate(tip):
        return {f"{BEATS}/{job}.json": json.dumps(rec, indent=2) + "\n"}, ()
    store.transact(mutate, f"heartbeat: {job}")


def beats(store):
    """-> {job: age in hours} for every recorded heartbeat."""
    tip = store.fetch()
    out = {}
    if tip is None:
        return out
    now = datetime.datetime.now(datetime.timezone.utc)
    for name in store.list(tip, BEATS):
        try:
            rec = json.loads(store.read(tip, f"{BEATS}/{name}"))
            at = datetime.datetime.strptime(rec["at"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc)
            out[rec["job"]] = (now - at).total_seconds() / 3600
        except (TypeError, ValueError, KeyError):
            continue
    return out


def next_queued(store):
    for e in entries(store):
        if e.get("status") == "queued":
            return e
    return None


def self_check():
    """A scratch remote: queue two branches, take them oldest first, mark
    them, and refuse a branch that was never pushed."""
    import tempfile
    env = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.com")
    ok = True
    with tempfile.TemporaryDirectory() as td:
        remote, work = pathlib.Path(td) / "remote.git", pathlib.Path(td) / "work"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], env=env)
        subprocess.run(["git", "init", "-q", "-b", "main", str(work)], env=env)
        subprocess.run(["git", "-C", str(work), "remote", "add", "origin", str(remote)], env=env)
        for b in ("feat/a", "feat/b"):
            subprocess.run(["git", "-C", str(work), "checkout", "-q", "-B", b], env=env)
            (work / f"{b.replace('/', '_')}.txt").write_text(b)
            subprocess.run(["git", "-C", str(work), "add", "-A"], env=env)
            subprocess.run(["git", "-C", str(work), "commit", "-qm", b], env=env)
            subprocess.run(["git", "-C", str(work), "push", "-q", "origin", b], env=env)
        os.environ.update({k: env[k] for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                                               "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")})
        st = _store(work)
        request(st, "feat/a", repo=work)
        request(st, "feat/b", repo=work)
        first = next_queued(st)
        ok &= first is not None and first["branch"] == "feat/a"
        mark(st, "feat/a", "landed", "merged as abc")
        ok &= next_queued(st)["branch"] == "feat/b"
        ok &= [e["status"] for e in entries(st)] == ["landed", "queued"]
        beat(st, "lander")
        ok &= 0 <= beats(st).get("lander", -1) < 0.1
        try:
            request(st, "feat/never-pushed", repo=work)
            ok = False
        except SystemExit:
            pass
    print("land_queue self-check:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-check" in argv:
        return self_check()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request")
    r.add_argument("--branch")
    r.add_argument("--note", default="")
    sub.add_parser("list")
    b = sub.add_parser("beat")
    b.add_argument("job")
    bs = sub.add_parser("beats")
    bs.add_argument("--stale-hours", type=float, default=None)
    sub.add_parser("next")
    m = sub.add_parser("mark")
    m.add_argument("branch")
    m.add_argument("status")
    m.add_argument("--detail", default="")
    a = ap.parse_args(argv)
    st = _store()
    if a.cmd == "request":
        branch = a.branch or _git(ROOT, "branch", "--show-current").stdout.strip()
        if branch in ("", "master", "main"):
            raise SystemExit("land_queue: name the branch to land (--branch)")
        rec = request(st, branch, a.note)
        lander = pathlib.Path(sys.argv[0]).with_name("land_next.py")
        try:
            lander = lander.resolve().relative_to(pathlib.Path.cwd().resolve())
        except ValueError:
            pass
        print(f"queued {branch} at {rec['commit'][:12]}; land the queue with "
              f"python3 {lander}")
    elif a.cmd == "list":
        es = entries(st)
        for e in es:
            print(f"{e.get('status'):8} {e.get('requested_at')}  {e.get('branch')}  "
                  f"{e.get('commit', '')[:12]}  {e.get('detail', '')}")
        if not es:
            print("the landing queue is empty")
    elif a.cmd == "beat":
        beat(st, a.job)
        print(f"heartbeat recorded for {a.job}")
    elif a.cmd == "beats":
        ages = beats(st)
        stale = []
        for job, h in sorted(ages.items()):
            flag = a.stale_hours is not None and h > a.stale_hours
            stale += [job] if flag else []
            print(f"{job:18} last ran {h:6.1f} h ago" + ("   STALE" if flag else ""))
        if not ages:
            print("no heartbeats recorded")
        return 1 if stale else 0
    elif a.cmd == "next":
        e = next_queued(st)
        print(json.dumps(e) if e else "")
    elif a.cmd == "mark":
        mark(st, a.branch, a.status, a.detail)
        print(f"{a.branch} -> {a.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
