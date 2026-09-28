"""gitops.py -- the bridge's own checkout of a repository, and the only code that
commits, pushes or lands anything.

The model never runs git: it has no shell. After each turn the bridge looks
at what changed on disk, and commits it only if EVERY changed path is
content. Anything else is set aside with `git stash` -- kept, never deleted
(practice: repair-cannot-discard-work) -- and the person is told.

One checkout per person per repository, under the bridge's state directory,
on a work branch `chat/<handle>`. The person's own clones are never touched.
"""
from __future__ import annotations

import os
import pathlib
import subprocess


class GitError(RuntimeError):
    pass


def _env():
    e = dict(os.environ)
    e["GIT_TERMINAL_PROMPT"] = "0"   # never hang waiting for a password
    return e


class Checkout:
    def __init__(self, path, clone_url, landing, work_branch,
                 author_name=None, author_email=None, web_url=None):
        self.path = pathlib.Path(path)
        self.clone_url, self.landing, self.work = clone_url, landing, work_branch
        self.author_name, self.author_email = author_name, author_email
        self.web_url = (web_url or "").rstrip("/")

    # -- plumbing ------------------------------------------------------------
    def git(self, *args, check=True, timeout=300):
        r = subprocess.run(["git", *args], cwd=self.path, capture_output=True,
                           text=True, env=_env(), timeout=timeout)
        if check and r.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:400]}")
        return r

    def _has_ref(self, ref):
        return self.git("rev-parse", "--verify", "--quiet", ref, check=False).returncode == 0

    # -- lifecycle -------------------------------------------------------------
    def ensure(self):
        """Clone on first use; configure the commit identity."""
        if not (self.path / ".git").is_dir():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            r = subprocess.run(["git", "clone", "--quiet", self.clone_url, str(self.path)],
                               capture_output=True, text=True, env=_env(), timeout=600)
            if r.returncode != 0:
                raise GitError(f"could not clone {self.clone_url}: {r.stderr.strip()[:400]}")
            start = (f"origin/{self.work}" if self._has_ref(f"origin/{self.work}")
                     else f"origin/{self.landing}")
            if not self._has_ref(start):
                raise GitError(f"the landing branch '{self.landing}' does not exist on origin")
            self.git("checkout", "--quiet", "-B", self.work, start)
        if self.author_name:
            self.git("config", "user.name", self.author_name)
        if self.author_email:
            self.git("config", "user.email", self.author_email)

    def refresh(self):
        """Before a turn: set aside leftovers, then bring the work branch up to
        date with the landing branch. -> list of notes for the person."""
        notes = []
        self.git("fetch", "--quiet", "origin", self.landing)
        if self.changed_paths():
            ref = self.quarantine("left over from an earlier turn")
            notes.append(f"Set aside unfinished changes from before ({ref}).")
        if self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != self.work:
            self.git("checkout", "--quiet", self.work)
        upstream = f"origin/{self.landing}"
        if self.unlanded_count() == 0:
            self.git("merge", "--quiet", "--ff-only", upstream, check=False)
        else:
            r = self.git("merge", "--quiet", "--no-edit", upstream, check=False)
            if r.returncode != 0:
                self.git("merge", "--abort", check=False)
                notes.append(f"Couldn't bring in the latest {self.landing}: it conflicts "
                             f"with changes not landed yet.")
        return notes

    # -- what changed ------------------------------------------------------------
    def changed_paths(self):
        """Every path the working tree differs in, untracked files included.
        Both sides of a rename are listed: both must be content."""
        out = self.git("status", "--porcelain=v1", "-z", "-uall").stdout
        paths, items, i = [], out.split("\0"), 0
        while i < len(items):
            it = items[i]
            if not it:
                i += 1
                continue
            status, path = it[:2], it[3:]
            paths.append(path)
            if status[0] in "RC":
                i += 1
                paths.append(items[i])
            i += 1
        return sorted(set(paths))

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def unlanded_count(self):
        r = self.git("rev-list", "--count", f"origin/{self.landing}..HEAD", check=False)
        return int(r.stdout.strip() or 0) if r.returncode == 0 else 0

    def unlanded_paths(self):
        r = self.git("diff", "--name-only", f"origin/{self.landing}...HEAD", check=False)
        return [p for p in r.stdout.splitlines() if p]

    # -- writing -----------------------------------------------------------------
    def commit(self, subject, handle):
        self.git("add", "-A")
        msg = (f"{subject}\n\nMade through the chat bridge on behalf of {handle}; "
               f"content paths only.\n\nChat-Bridge: {handle}\n"
               f"Session: none available (chatbridge)\n")
        self.git("commit", "--quiet", "-m", msg)
        return self.head()

    def quarantine(self, why):
        """Set changes aside without losing them. -> a name the owner can find."""
        label = f"chatbridge: {why}"
        self.git("stash", "push", "--include-untracked", "--quiet", "-m", label)
        return "git stash list in " + str(self.path)

    def push_work(self):
        r = self.git("push", "--quiet", "origin", f"HEAD:refs/heads/{self.work}", check=False)
        return r.returncode == 0, (r.stderr or "").strip()[:300]

    def land(self, scope):
        """Put the work branch onto the landing branch, content only.
        -> (ok, message). Never forces; verifies origin afterwards."""
        self.git("fetch", "--quiet", "origin", self.landing)
        paths = self.unlanded_paths()
        if not paths:
            return False, "Nothing to land."
        bad = [(p, scope.verdict(p)[1]) for p in paths if not scope.is_content(p)]
        if bad:
            p, why = bad[0]
            return False, f"Not landing: {p} isn't content ({why})."
        r = self.git("merge", "--quiet", "--no-edit", f"origin/{self.landing}", check=False)
        if r.returncode != 0:
            self.git("merge", "--abort", check=False)
            return False, f"Not landing: it conflicts with the latest {self.landing}."
        r = self.git("push", "--quiet", "origin", f"HEAD:refs/heads/{self.landing}", check=False)
        if r.returncode != 0:
            return False, f"{self.landing} refused the push: {(r.stderr or '').strip()[:200]}"
        self.git("fetch", "--quiet", "origin", self.landing)
        if self.git("rev-parse", f"origin/{self.landing}").stdout.strip() != self.head():
            return False, f"Pushed, but {self.landing} on GitHub doesn't show it yet."
        return True, f"Landed {len(paths)} file(s) on {self.landing}."

    # -- links -------------------------------------------------------------------
    def file_url(self, path, branch=None):
        return f"{self.web_url}/blob/{branch or self.work}/{path}" if self.web_url else ""

    def commit_url(self, sha):
        return f"{self.web_url}/commit/{sha}" if self.web_url else ""

    def compare_url(self):
        return (f"{self.web_url}/compare/{self.landing}...{self.work}"
                if self.web_url else "")
