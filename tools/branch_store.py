#!/usr/bin/env python3
"""Small records on a dedicated branch of a shared remote, with the push as the lock: the git plumbing shared by the lease board and the result cache

Branch store: small records kept on a dedicated branch of a shared remote.

Practice `judgment-check-or-tool` (spec/SHARED_ENGINES_PLAN.md, section 1).
Two tools kept their own copy of the same git plumbing: the lease board
(`lease_board.py`, practice `lease-in-flight-work`) and the shared result
cache (`result_cache.py`, practice `shared-result-cache`). This module is
that plumbing, once. Each caller keeps its own policy -- what a lease is,
who holds it, which cache entries survive -- and asks the store for
everything that touches git.

What it guarantees:
  * The working tree, the index and the current branch are never touched.
    Reads go through a private ref (`ref`) fetched from the remote; writes
    build a tree in a private index file and a commit with `commit-tree`.
  * `git push` is the lock. `transact(mutate, message)` fetches the tip,
    calls `mutate(tip)` for the change, commits, pushes; when the push is
    refused it fetches again and calls `mutate` again, so any check inside
    `mutate` always runs against the tip it is about to replace.
  * Two history modes, chosen by the caller:
      history=True   each commit's parent is the tip it read: the branch's
                     log is the record of every change (the lease board).
      history=False  each commit is a new root holding the whole state,
                     pushed with --force-with-lease on the tip it read: the
                     branch never grows past what it holds now (the cache).
                     `mutate` must then return the full tree it wants kept;
                     `keep(tip, path)` carries an existing blob over.

Writes are {path: value}; a value is str (text), bytes, Blob(sha) for a
blob already in the object store, or File(path) for a local file hashed in
without being read into memory.

  python3 branch_store.py --self-check     # scratch remote, both modes
"""
import os
import subprocess
import sys
import tempfile
import time


class Unreachable(RuntimeError):
    """The remote could not be listed, fetched or (after every retry)
    pushed. `stage` is "list", "fetch" or "push"; `stderr` is git's."""

    def __init__(self, message, stage="", stderr=""):
        super().__init__(message)
        self.stage = stage
        self.stderr = stderr


class Blob(str):
    """A blob already in the object store, by sha."""


class File(str):
    """A local file, hashed into the object store by path."""


class BranchStore:
    def __init__(self, remote="origin", branch="coord", repo=None, *,
                 ref=None, retries=5, history=True, seed=None, backoff=1.0):
        self.remote = remote
        self.branch = branch
        self.repo = repo
        self.ref = ref or f"refs/branch-store/{branch}"
        self.retries = retries
        self.history = history
        self.seed = seed or {}      # written into the first commit only
        self.backoff = backoff

    # ------------------------------------------------------------- git --
    def git(self, *args, env=None, input=None, text=True):
        e = dict(os.environ)
        if env:
            e.update(env)
        return subprocess.run(["git", *args], cwd=self.repo, env=e,
                              input=input, capture_output=True, text=text)

    def _ok(self, *args, **kw):
        r = self.git(*args, **kw)
        if r.returncode != 0:
            raise subprocess.CalledProcessError(r.returncode, ["git", *args],
                                                r.stdout, r.stderr)
        return r

    # ------------------------------------------------------------ read --
    def fetch(self):
        """Fetch the branch into the private ref. Returns its commit, or
        None when the branch does not exist yet. Raises Unreachable."""
        r = self.git("ls-remote", "--heads", self.remote, self.branch)
        if r.returncode != 0:
            raise Unreachable(f"cannot reach {self.remote}: {r.stderr.strip()}",
                              "list", r.stderr.strip())
        if not r.stdout.strip():
            return None
        r = self.git("fetch", "--quiet", "--no-tags", self.remote,
                     f"+refs/heads/{self.branch}:{self.ref}")
        if r.returncode != 0:
            raise Unreachable(f"cannot fetch {self.remote}/{self.branch}: "
                              f"{r.stderr.strip()}", "fetch", r.stderr.strip())
        return self._ok("rev-parse", self.ref).stdout.strip()

    def list(self, commit, directory=""):
        """Names directly under `directory` at `commit` ([] if absent)."""
        if commit is None:
            return []
        spec = f"{commit}:{directory}" if directory else f"{commit}:"
        r = self.git("ls-tree", "--name-only", spec)
        return r.stdout.split() if r.returncode == 0 else []

    def read(self, commit, path, binary=False):
        """The file at `path` in `commit`, or None."""
        if commit is None:
            return None
        r = self.git("cat-file", "blob", f"{commit}:{path}", text=not binary)
        return r.stdout if r.returncode == 0 else None

    def blob(self, commit, path):
        """The blob sha of `path` at `commit`, or None -- for keeping an
        entry across a history=False commit without reading it."""
        if commit is None:
            return None
        r = self.git("rev-parse", "--verify", "--quiet", f"{commit}:{path}")
        return Blob(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None

    # ----------------------------------------------------------- write --
    def _hash(self, value):
        if isinstance(value, Blob):
            return str(value)
        if isinstance(value, File):
            return self._ok("hash-object", "-w", str(value)).stdout.strip()
        if isinstance(value, bytes):
            return self._ok("hash-object", "-w", "--stdin", input=value,
                            text=False).stdout.decode().strip()
        return self._ok("hash-object", "-w", "--stdin", input=value).stdout.strip()

    def commit(self, parent, writes, deletes=(), message="update"):
        """A commit writing `writes` and deleting `deletes`. With history,
        it starts from `parent`'s tree and names it as parent; without, it
        starts empty and has no parent."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
            if parent and self.history:
                self._ok("read-tree", parent, env=env)
            else:
                self._ok("read-tree", "--empty", env=env)
                if parent is None:
                    for path, value in self.seed.items():
                        self._ok("update-index", "--add", "--cacheinfo",
                                 f"100644,{self._hash(value)},{path}", env=env)
            for path, value in writes.items():
                self._ok("update-index", "--add", "--cacheinfo",
                         f"100644,{self._hash(value)},{path}", env=env)
            for path in deletes:
                self._ok("update-index", "--force-remove", path, env=env)
            tree = self._ok("write-tree", env=env).stdout.strip()
        args = ["commit-tree", tree, "-m", message]
        if parent and self.history:
            args += ["-p", parent]
        return self._ok(*args).stdout.strip()

    def push(self, commit, tip):
        """Push `commit` as the branch. With history, a plain push (refused
        unless it fast-forwards `tip`); without, a lease on `tip`."""
        args = ["push", "--quiet"]
        if not self.history:
            args.append(f"--force-with-lease=refs/heads/{self.branch}:{tip or ''}")
        r = self.git(*args, self.remote, f"{commit}:refs/heads/{self.branch}")
        return r.returncode == 0, r.stderr.strip()

    def transact(self, mutate, message):
        """Fetch the tip, apply `mutate(tip) -> (writes, deletes)` (None or
        two empty collections: nothing to do), commit, push; on a refused
        push fetch again and re-apply. Returns the new commit, or None when
        there was nothing to write. Raises Unreachable after `retries`."""
        err = ""
        for attempt in range(self.retries):
            tip = self.fetch()
            change = mutate(tip)
            if not change or (not change[0] and not change[1]):
                return None
            writes, deletes = change
            new = self.commit(tip, writes, deletes, message)
            ok, err = self.push(new, tip)
            if ok:
                self.git("update-ref", self.ref, new)
                return new
            time.sleep(self.backoff * (1 + attempt))
        raise Unreachable(f"push to {self.remote}/{self.branch} kept failing: {err}",
                          "push", err)


# ------------------------------------------------------------ self-check --
def self_check():
    """Both modes on a scratch remote: a record written by one clone is read
    by another; a stale writer re-applies on the fresh tip; history=True
    keeps every commit, history=False keeps one; a File and a Blob round-trip
    byte for byte; an unreachable remote raises Unreachable."""
    bad = []

    def run(*a, cwd=None):
        return subprocess.run(["git", *a], cwd=cwd, capture_output=True,
                              text=True, check=True).stdout.strip()

    with tempfile.TemporaryDirectory() as t:
        remote = os.path.join(t, "remote.git")
        run("init", "-q", "--bare", remote)
        clones = []
        for c in ("a", "b"):
            d = os.path.join(t, c)
            run("init", "-q", d)
            run("-C", d, "remote", "add", "origin", remote)
            clones.append(d)
        a, b = clones

        # history=True: records accumulate as commits
        sa = BranchStore("origin", "log", a, seed={"README.md": "# log\n"}, backoff=0)
        sb = BranchStore("origin", "log", b, backoff=0)
        sa.transact(lambda tip: ({"r/one.json": "1\n"}, []), "one")
        stale = sb.fetch()
        sa.transact(lambda tip: ({"r/two.json": "2\n"}, []), "two")
        seen = []

        def add_three(tip):
            seen.append(tip)
            return {"r/three.json": "3\n"}, []
        sb.transact(add_three, "three")
        if len(seen) != 1 or seen[0] == stale:
            bad.append("a transaction did not read the fresh tip")
        tip = sb.fetch()
        if sorted(sb.list(tip, "r")) != ["one.json", "three.json", "two.json"]:
            bad.append(f"history mode lost a record: {sb.list(tip, 'r')}")
        if run("rev-list", "--count", "log", cwd=remote) != "3":
            bad.append("history mode did not keep one commit per change")
        if sb.read(tip, "README.md") != "# log\n":
            bad.append("the seed was not written into the first commit")
        sb.transact(lambda tip: ({}, ["r/one.json"]), "drop one")
        if "one.json" in sb.list(sb.fetch(), "r"):
            bad.append("a delete did not take")
        if sb.transact(lambda tip: None, "nothing") is not None:
            bad.append("an empty change made a commit")

        # history=False: one root commit holding the whole state
        ca = BranchStore("origin", "snap", a, history=False, backoff=0)
        cb = BranchStore("origin", "snap", b, history=False, backoff=0)
        payload = os.path.join(t, "payload.bin")
        with open(payload, "wb") as f:
            f.write(bytes(range(256)) * 4)
        ca.transact(lambda tip: ({"p.bin": File(payload), "i.txt": "a\n"}, []), "p")
        stale = cb.fetch()
        ca.transact(lambda tip: ({"p.bin": ca.blob(tip, "p.bin"), "i.txt": "a2\n"}, []), "i")

        def keep_and_add(tip):
            return {"p.bin": cb.blob(tip, "p.bin"), "i.txt": cb.read(tip, "i.txt"),
                    "q.txt": b"q\n"}, []
        cb.transact(keep_and_add, "q")
        tip = cb.fetch()
        if cb.read(tip, "p.bin", binary=True) != bytes(range(256)) * 4:
            bad.append("a File did not round-trip byte for byte")
        if cb.read(tip, "i.txt") != "a2\n" or cb.read(tip, "q.txt") != "q\n":
            bad.append("the snapshot writer lost a concurrent change")
        if run("rev-list", "--count", "snap", cwd=remote) != "1":
            bad.append("snapshot mode kept history")
        if stale == tip:
            bad.append("the stale tip was not replaced")

        # unreachable
        u = BranchStore(os.path.join(t, "missing.git"), "x", a, backoff=0)
        try:
            u.fetch()
            bad.append("an unreachable remote did not raise")
        except Unreachable as e:
            if e.stage != "list":
                bad.append(f"unreachable raised at stage {e.stage!r}")
    return bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--self-check"]:
        bad = self_check()
        for b in bad:
            print(f"branch_store self-check FAIL: {b}")
        if not bad:
            print("branch_store self-check OK: both modes on a scratch remote")
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
