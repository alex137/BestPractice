#!/usr/bin/env python3
"""The lease board -- work in flight across sessions, one JSON file per lease on a coordination branch, push as the lock

Lease board: work in flight, visible to every concurrent session.

Practice `lease-in-flight-work`. Trunk tells a session what has LANDED; it
cannot tell it what another session, in another container, has taken and
not yet landed. The lease board carries exactly that: short-lived claims
on named items ("these five records are in a package awaiting submission",
"this migration is being run"), one small JSON file per lease, on a
dedicated coordination branch of the shared remote.

Why a branch of JSON files and not a database:
  * `git push` is the lock. Two sessions racing for the same item both
    write; the second push is rejected as non-fast-forward, re-reads the
    board, sees the first lease, and refuses. No server, no credential
    beyond the one every session already has.
  * One file per lease means two sessions taking DIFFERENT leases touch
    different paths, so their retries always succeed; the only conflict
    left is the one that is wanted.
  * Every take, update and release is a commit: who held what, when, and
    why it was released is in `git log` of the branch.

Nothing here expires a lease on its own (practice
`repair-cannot-discard-work`): a stale lease is shown with its age and
released by a person or session that says why.

The board never touches the working tree, the index, or the current
branch: it reads with `git show`/`git ls-tree` on the fetched ref and
writes with plumbing (a private index file, `commit-tree`, and a push of
the new commit to the board branch).

HOST CONFIGURATION (set by the host shim before calling main()):
  REMOTE  — where the board lives: a remote name ("origin", the default) or
            a repository URL. A board guards the place where the costly work
            happens, not the repo a session is rooted in: when one project is
            split across several repositories, every one of them names the
            same URL here, and the board keeps working through the split
  BRANCH  — the coordination branch (default "coord")
  DIR     — directory on that branch holding the lease files ("leases")
  REPO    — path to the host repository (default: current directory)

LIBRARY API (for other tools to gate on):
  board()                        -> {lease_id: lease} active leases
  conflicts(items, holder=None)  -> leases held by someone else overlapping items
  take(items, kind, note, lease_id=None, holder=None, replace_kind=False)
  update(lease_id, **fields)
  release(lease_ids, reason)
  holder_id()                    -> this session's holder string (its branch)
Every call that reaches the remote raises BoardUnreachable if it cannot.

CLI
  lease_board.py list [--json]
  lease_board.py check ITEM [ITEM ...]           exit 1 on a conflict
  lease_board.py take ITEM [ITEM ...] --kind K --note "…" [--id ID]
  lease_board.py update ID --status S [--note "…"]
  lease_board.py release ID [ID ...] --reason "…"
  lease_board.py release --mine --reason "…"
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precedent_time  # noqa: E402  one module for every emitted moment
import branch_store    # noqa: E402  the branch plumbing, shared with result_cache

REMOTE = "origin"
BRANCH = "coord"
DIR = "leases"
REPO = None
RETRIES = 5

README = """# Lease board

Work in flight across concurrent sessions: one JSON file per lease under
`{dir}/`. Written only by the lease board tool, never by hand; every
take, update and release is a commit on this branch, so `git log` here is
the full history of who held what.
"""


BoardUnreachable = branch_store.Unreachable


class LeaseConflict(RuntimeError):
    def __init__(self, held):
        self.held = held
        super().__init__(describe_conflicts(held))


# ------------------------------------------------------------------ git ----
# The branch plumbing is branch_store's (history mode: every take, update and
# release is a commit on the board branch). Built per call, because the host
# shim sets REMOTE/BRANCH/DIR/REPO after import.
def _store():
    return branch_store.BranchStore(REMOTE, BRANCH, REPO, ref=_ref(),
                                    retries=RETRIES, history=True,
                                    seed={"README.md": README.format(dir=DIR)})


def _git(*args, check=True):
    r = _store().git(*args)
    if check and r.returncode != 0:
        raise subprocess.CalledProcessError(r.returncode, ["git", *args],
                                            r.stdout, r.stderr)
    return r


def _ref():
    return f"refs/lease-board/{BRANCH}"


def _fetch():
    return _store().fetch()


def _read(commit):
    st = _store()
    out = {}
    for name in st.list(commit, DIR):
        if not name.endswith(".json"):
            continue
        try:
            lease = json.loads(st.read(commit, f"{DIR}/{name}") or "")
        except ValueError:
            continue
        out[lease.get("id", name[:-5])] = lease
    return out


def _transact(mutate, message):
    """Read the board, apply `mutate(board) -> (writes, deletes)`, push; on a
    rejected push re-read and re-apply, so the check inside `mutate` always
    runs against the board it is about to replace."""
    def change(tip):
        writes, deletes = mutate(_read(tip))
        return ({f"{DIR}/{lid}.json": json.dumps(l, indent=2, sort_keys=True) + "\n"
                 for lid, l in writes.items()},
                [f"{DIR}/{lid}.json" for lid in deletes])
    _store().transact(change, message)


# ------------------------------------------------------------------ API ----
def _now():
    return precedent_time.stamp_iso(REPO)


def _repo_name():
    url = _git("remote", "get-url", "origin", check=False).stdout.strip()
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name[:-4] if name.endswith(".git") else (name or "local")


def holder_id():
    """The holder is `repo:branch` -- every session works on its own branch,
    and the repo name keeps two repositories sharing one board apart."""
    b = _git("branch", "--show-current", check=False).stdout.strip()
    b = b or _git("rev-parse", "--short", "HEAD").stdout.strip()
    return f"{_repo_name()}:{b}"


def board():
    return _read(_fetch())


def _overlap(board_, items, holder):
    items = set(items)
    return [l for l in board_.values()
            if l.get("holder") != holder and items & set(l.get("items", []))]


def conflicts(items, holder=None):
    return _overlap(board(), items, holder or holder_id())


def describe_conflicts(held):
    lines = []
    for l in held:
        lines.append(f"  lease {l['id']} ({l.get('kind', '?')}, "
                     f"{l.get('status', 'active')}) held by {l['holder']} "
                     f"since {l.get('taken_at', '?')}: "
                     f"{', '.join(sorted(l.get('items', [])))}"
                     + (f" — {l['note']}" if l.get("note") else ""))
    return "\n".join(lines)


def take(items, kind, note="", lease_id=None, holder=None,
         replace_kind=False, force=False):
    """Take a lease on `items`. Refuses (LeaseConflict) if another holder's
    lease overlaps, unless force. replace_kind releases this holder's other
    leases of the same kind in the same commit (a rebuilt package supersedes
    the previous one). Returns the lease."""
    holder = holder or holder_id()
    lease_id = lease_id or f"{kind}-{holder.replace('/', '-').replace(':', '-')}-{int(time.time())}"
    lease = dict(id=lease_id, kind=kind, holder=holder, items=sorted(set(items)),
                 note=note, status="active", taken_at=_now())

    def mutate(b):
        held = _overlap(b, items, holder)
        if held and not force:
            raise LeaseConflict(held)
        deletes = []
        if replace_kind:
            deletes = [l["id"] for l in b.values()
                       if l.get("holder") == holder and l.get("kind") == kind
                       and l["id"] != lease_id]
        return {lease_id: lease}, deletes

    _transact(mutate, f"take {lease_id}: {kind} by {holder}"
              + (f" — {note}" if note else ""))
    return lease


def update(lease_id, **fields):
    def mutate(b):
        if lease_id not in b:
            raise KeyError(f"no lease {lease_id} on the board")
        l = dict(b[lease_id])
        l.update({k: v for k, v in fields.items() if v is not None})
        l["updated_at"] = _now()
        return {lease_id: l}, []
    _transact(mutate, f"update {lease_id}: "
              + ", ".join(f"{k}={v}" for k, v in fields.items() if v))


def release(lease_ids, reason):
    if not reason:
        raise ValueError("a release names its reason")
    if not lease_ids:
        return
    ids = list(lease_ids)

    def mutate(b):
        missing = [i for i in ids if i not in b]
        if missing:
            print(f"lease_board: not on the board (already released?): "
                  f"{', '.join(missing)}", file=sys.stderr)
        return {}, [i for i in ids if i in b]
    _transact(mutate, f"release {', '.join(ids)}: {reason}")


# ------------------------------------------------------------------ CLI ----
def _age(ts):
    try:
        t = datetime.datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return "?"
    h = (precedent_time.now(REPO) - t).total_seconds() / 3600
    return f"{h:.0f} h" if h < 48 else f"{h / 24:.0f} d"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("check"); s.add_argument("items", nargs="+")
    s = sub.add_parser("take"); s.add_argument("items", nargs="+")
    s.add_argument("--kind", required=True); s.add_argument("--note", default="")
    s.add_argument("--id"); s.add_argument("--force", action="store_true")
    s = sub.add_parser("update"); s.add_argument("id")
    s.add_argument("--status"); s.add_argument("--note")
    s = sub.add_parser("release"); s.add_argument("ids", nargs="*")
    s.add_argument("--mine", action="store_true")
    s.add_argument("--reason", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "list":
            b = board()
            if a.json:
                print(json.dumps(b, indent=2, sort_keys=True))
            elif not b:
                print(f"lease board {REMOTE}/{BRANCH}: empty")
            else:
                for l in sorted(b.values(), key=lambda l: l.get("taken_at", "")):
                    print(f"{l['id']}  [{l.get('status', 'active')}, "
                          f"{_age(l.get('taken_at'))} old]  {l['holder']}\n"
                          f"    {', '.join(l.get('items', []))}"
                          + (f"\n    {l['note']}" if l.get("note") else ""))
        elif a.cmd == "check":
            held = conflicts(a.items)
            if held:
                print("HELD by another session:\n" + describe_conflicts(held))
                return 1
            print("clear: no other session holds any of these")
        elif a.cmd == "take":
            l = take(a.items, a.kind, a.note, a.id, force=a.force)
            print(f"took lease {l['id']} on {', '.join(l['items'])}")
        elif a.cmd == "update":
            update(a.id, status=a.status, note=a.note)
            print(f"updated lease {a.id}")
        elif a.cmd == "release":
            ids = list(a.ids)
            if a.mine:
                me = holder_id()
                ids += [i for i, l in board().items() if l.get("holder") == me]
            if not ids:
                print("nothing to release")
                return 0
            release(ids, a.reason)
            print(f"released {', '.join(ids)}")
    except LeaseConflict as e:
        print("REFUSED — held by another session:\n" + str(e), file=sys.stderr)
        return 1
    except BoardUnreachable as e:
        print(f"lease board unreachable: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
