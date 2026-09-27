#!/usr/bin/env python3
"""Shared result cache: a heavy solve done once serves every session.

Practice `shared-result-cache`. Practice `slow-steps-report-and-cache` memoizes
a heavy pure solve to a gitignored directory under a key that is the content
hash of the code that produced it. That memo dies with the container, so every
fresh session pays the cold solve again. Because the key is a hash of the code,
a result stored under it is correct for ANY session running that code — so the
memo can be shared, safely, through the one channel every session already has:
git.

How it is stored, and why this way:
  * One branch (BRANCH, default "result-cache") holding ONE commit: a flat tree
    of memo files plus `index.json`. Every publish replaces that commit with a
    new root commit, pushed with --force-with-lease against the tip it read —
    a compare-and-swap, so two sessions publishing at once never lose each
    other's entries: the second is refused, re-reads, and retries. Old blobs
    fall out of reach instead of piling up in history, so a clone that fetches
    every branch pays for the current snapshot only.
  * A web session's git proxy refuses pushes outside refs/heads/ and cannot
    delete a branch, which rules out a ref (or a branch) per entry.
  * Each family (the file name with its key stripped) keeps its KEEP newest
    entries, so two sessions on different code versions do not evict each
    other; an entry over MAX_BYTES is not shared at all.
  * A cold solve takes a lease (practice `lease-in-flight-work`) on its file
    name. A second session that misses the cache while that lease is held
    waits for the result — polling, with progress on stderr — instead of
    running the same solve beside it. It stops waiting after WAIT_S, or at
    once for a lease older than STALE_S, and solves itself.

It is an accelerator, never a dependency: an unreachable remote, a refused
push, or RESULT_CACHE_OFF=1 degrades to the local memo alone, with one line on
stderr.

HOST CONFIGURATION (set by the host shim):
  REMOTE  — remote name or URL holding the cache branch (default "origin").
            Each repository caches its own models' results; the key is a hash
            of the code, so moving files between repositories never serves a
            wrong entry — at worst a miss.
  BRANCH  — the cache branch ("result-cache")
  REPO    — path to the host repository
  KEEP, MAX_BYTES, WAIT_S, STALE_S — limits above; TOTAL_BYTES caps the
            whole snapshot (oldest entries go first), which bounds what a
            clone that fetches every branch ever pulls

API (call sites wrap an existing memo file; the file name must carry the key):
  ready(path)   -> True when `path` is on disk: already there, pulled from the
                   cache, or pulled after waiting on a peer's solve
  claim(path)   take the solve lease (best effort; released at exit if the
                solve dies before publish)
  publish(path) share `path` and release the claim
  release(path) drop the claim without publishing

  result_cache.py list | get NAME | stats
"""
import atexit
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precedent_time  # noqa: E402
import lease_board     # noqa: E402

REMOTE = "origin"
BRANCH = "result-cache"
REPO = None
KEEP = 3
MAX_BYTES = 40 * 1024 * 1024
TOTAL_BYTES = 150 * 1024 * 1024
WAIT_S = 20 * 60
STALE_S = 6 * 3600
POLL_S = 30
RETRIES = 5
KIND = "solve"

_tip = None          # the cache commit this process read, or None
_fetched = False
_claims = {}         # file name -> lease id
_said = set()


def _off():
    return bool(os.environ.get("RESULT_CACHE_OFF"))


def _note(msg):
    if msg not in _said:
        _said.add(msg)
        print(f"[result-cache] {msg}", file=sys.stderr)


def _git(*args, input=None, env=None, text=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=REPO, input=input, env=e,
                          capture_output=True, text=text)


def _ref():
    return f"refs/result-cache/{BRANCH}"


def _fetch(force=False):
    """Fetch the cache branch once per process (or again when `force`).
    Returns the tip commit or None (empty, unreachable, or off)."""
    global _tip, _fetched
    if _off():
        return None
    if _fetched and not force:
        return _tip
    _fetched = True
    r = _git("ls-remote", "--heads", REMOTE, BRANCH)
    if r.returncode != 0:
        _note(f"cache unreachable ({r.stderr.strip()[:120]}); local memos only")
        _tip = None
        return None
    if not r.stdout.strip():
        _tip = None
        return None
    r = _git("fetch", "--quiet", "--no-tags", REMOTE,
             f"+refs/heads/{BRANCH}:{_ref()}")
    if r.returncode != 0:
        _note(f"cache fetch failed ({r.stderr.strip()[:120]}); local memos only")
        _tip = None
        return None
    _tip = _git("rev-parse", _ref()).stdout.strip()
    return _tip


def _index(tip):
    if not tip:
        return {}
    r = _git("show", f"{tip}:index.json")
    try:
        return json.loads(r.stdout) if r.returncode == 0 else {}
    except ValueError:
        return {}


def _pull(tip, name, dest):
    r = _git("cat-file", "blob", f"{tip}:{name}", text=False)
    if r.returncode != 0:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(r.stdout)
    os.replace(tmp, dest)        # atomic: a concurrent reader never sees half
    return True


def family(name):
    """The file name with its content key stripped: entries of one family
    are successive answers to the same question under different code."""
    return re.sub(r"_[0-9a-f]{8,}(?=\.[A-Za-z0-9]+$)", "", name)


def ready(path):
    """True when `path` exists locally, pulling it from the cache or waiting
    on a peer's in-flight solve if needed."""
    path = pathlib.Path(path)
    if path.exists():
        return True
    if _off():
        return False
    tip = _fetch()
    if tip and path.name in _index(tip) and _pull(tip, path.name, path):
        print(f"[result-cache] {path.name}: pulled from {REMOTE}/{BRANCH}",
              file=sys.stderr)
        return True
    return _await_peer(path)


def _peer_lease(name):
    try:
        held = lease_board.conflicts([name])
    except lease_board.BoardUnreachable:
        return None
    now = precedent_time.now(REPO)
    for l in held:
        try:
            age = (now - __import__("datetime").datetime.fromisoformat(
                l["taken_at"])).total_seconds()
        except (KeyError, TypeError, ValueError):
            continue
        if age < STALE_S:
            return l
    return None


def _await_peer(path):
    lease = _peer_lease(path.name)
    if not lease:
        return False
    t0 = time.time()
    print(f"[result-cache] {path.name}: {lease['holder']} has been solving it "
          f"since {lease['taken_at']}; waiting up to {WAIT_S // 60} min for "
          "the result (RESULT_CACHE_OFF=1 solves here instead)",
          file=sys.stderr)
    while time.time() - t0 < WAIT_S:
        time.sleep(POLL_S)
        tip = _fetch(force=True)
        if tip and path.name in _index(tip) and _pull(tip, path.name, path):
            print(f"[result-cache] {path.name}: pulled after "
                  f"{(time.time() - t0) / 60:.1f} min", file=sys.stderr)
            return True
        if not _peer_lease(path.name):
            print(f"[result-cache] {path.name}: the peer's lease is gone with "
                  "no result; solving here", file=sys.stderr)
            return False
        el = time.time() - t0
        print(f"[result-cache] {path.name}: waited {el / 60:.1f} min, "
              f"≈{(WAIT_S - el) / 60:.0f} min left before solving here",
              file=sys.stderr)
    print(f"[result-cache] {path.name}: gave up waiting; solving here",
          file=sys.stderr)
    return False


def claim(path):
    if _off():
        return
    name = pathlib.Path(path).name
    try:
        l = lease_board.take([name], KIND, note="cold solve in progress",
                             force=True)
        _claims[name] = l["id"]
    except (lease_board.BoardUnreachable, lease_board.LeaseConflict):
        pass


def release(path):
    lid = _claims.pop(pathlib.Path(path).name, None)
    if lid:
        try:
            lease_board.release([lid], "solve finished")
        except lease_board.BoardUnreachable:
            pass


@atexit.register
def _release_all():
    for name in list(_claims):
        release(name)


def publish(path):
    """Share `path` under its name; keep KEEP entries per family."""
    path = pathlib.Path(path)
    try:
        if _off() or not path.exists():
            return
        size = path.stat().st_size
        if size > MAX_BYTES:
            _note(f"{path.name}: {size / 2**20:.0f} MiB is over the "
                  f"{MAX_BYTES / 2**20:.0f} MiB share limit; kept local only")
            return
        blob = _git("hash-object", "-w", str(path)).stdout.strip()
        for attempt in range(RETRIES):
            tip = _fetch(force=True)
            idx = _index(tip)
            seq = 1 + max((e.get("seq", 0) for e in idx.values()), default=0)
            idx[path.name] = dict(family=family(path.name), bytes=size, seq=seq,
                                  published_at=precedent_time.stamp_iso(REPO),
                                  by=lease_board.holder_id())
            newest = lambda n: -idx[n].get("seq", 0)
            fam = family(path.name)
            for n in sorted((n for n, e in idx.items()
                             if e.get("family") == fam), key=newest)[KEEP:]:
                idx.pop(n)
            total = 0
            for n in sorted(idx, key=newest):
                total += idx[n].get("bytes", 0)
                if total > TOTAL_BYTES and n != path.name:
                    idx.pop(n)
            with tempfile.TemporaryDirectory() as tmp:
                env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
                _git("read-tree", "--empty", env=env)
                for n in idx:
                    if n == path.name:
                        sha = blob
                    else:
                        sha = _git("rev-parse", f"{tip}:{n}").stdout.strip()
                        if not sha:
                            continue
                    _git("update-index", "--add", "--cacheinfo",
                         f"100644,{sha},{n}", env=env)
                isha = _git("hash-object", "-w", "--stdin",
                            input=json.dumps(idx, indent=1, sort_keys=True)
                            + "\n").stdout.strip()
                _git("update-index", "--add", "--cacheinfo",
                     f"100644,{isha},index.json", env=env)
                tree = _git("write-tree", env=env).stdout.strip()
            commit = _git("commit-tree", tree, "-m",
                          f"publish {path.name}").stdout.strip()
            lease = f"--force-with-lease=refs/heads/{BRANCH}:{tip or ''}"
            r = _git("push", "--quiet", lease, REMOTE,
                     f"{commit}:refs/heads/{BRANCH}")
            if r.returncode == 0:
                print(f"[result-cache] {path.name}: shared on {REMOTE}/{BRANCH}",
                      file=sys.stderr)
                return
            time.sleep(1 + attempt)
        _note(f"{path.name}: could not publish ({r.stderr.strip()[:120]})")
    finally:
        release(path)


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("stats")
    g = sub.add_parser("get"); g.add_argument("name"); g.add_argument("--to", default=".")
    a = p.parse_args(argv)
    tip = _fetch()
    idx = _index(tip)
    if a.cmd == "list":
        for n, e in sorted(idx.items()):
            print(f"{n}  {e.get('bytes', 0) / 2**20:.2f} MiB  "
                  f"{e.get('published_at', '?')}  {e.get('by', '?')}")
        if not idx:
            print(f"cache {REMOTE}/{BRANCH}: empty")
    elif a.cmd == "stats":
        tot = sum(e.get("bytes", 0) for e in idx.values())
        fams = {e.get("family") for e in idx.values()}
        print(f"{len(idx)} entries, {len(fams)} families, {tot / 2**20:.1f} MiB")
    elif a.cmd == "get":
        dest = pathlib.Path(a.to) / a.name
        if not (tip and a.name in idx and _pull(tip, a.name, dest)):
            print(f"not in the cache: {a.name}", file=sys.stderr)
            return 1
        print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
