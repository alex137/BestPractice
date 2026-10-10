"""One run at a time in a clone several runs share.

Update Vendors fetches into the source clone (../BestPractice) and pulls
each set a person's individual set brings, and every repo's run uses the
same clones. Two runs started together fetch the same ref at once, and one
of them fails: "cannot lock ref 'refs/remotes/origin/main': is at X but
expected Y" (2026-10-10, four voice repos updated in parallel). Running the
loser again alone worked, so nothing was wrong but the timing.

`held(path)` takes an exclusive lock on a file inside the clone's git
directory -- the clone itself when it exists, a lock beside where it will
go when it does not -- and waits for it instead of failing. The lock is the
operating system's (fcntl.flock), so a run that dies lets go of it at once;
there is no stale lock file to clean up. Where fcntl does not exist
(Windows), it does nothing, and the runs race as they did before.

It guards this engine's own git calls against each other, not against a
person running `git fetch` by hand in the same clone at the same moment.
"""
import contextlib
import os
import pathlib
import sys
import time

try:
    import fcntl
except ImportError:                                         # pragma: no cover
    fcntl = None

LOCK_NAME = 'precedent-clone.lock'
# Long enough for another run's fetch, clone or pull to finish, short enough
# that a wedged run does not hold the next one forever.
WAIT_SECONDS = 600
SAY_AFTER = 2


def lock_path(clone):
    """The lock file for `clone`: inside its git directory, or beside the
    path when there is no clone there yet."""
    clone = pathlib.Path(clone)
    git = clone / '.git'
    if git.is_dir():
        return git / LOCK_NAME
    if git.is_file():                       # a worktree: .git names the real one
        text = git.read_text(encoding='utf-8', errors='replace').strip()
        if text.startswith('gitdir:'):
            real = pathlib.Path(text[len('gitdir:'):].strip())
            if not real.is_absolute():
                real = clone / real
            common = real / 'commondir'
            if common.is_file():
                real = real / common.read_text(encoding='utf-8').strip()
            return real.resolve() / LOCK_NAME
    return clone.parent / f'.{clone.name}.{LOCK_NAME}'


@contextlib.contextmanager
def held(clone, wait=WAIT_SECONDS, say=None):
    """Hold the lock on `clone` for the body. Waits up to `wait` seconds,
    saying once (to `say`, stderr by default) that it is waiting and for
    what. Past `wait` it raises TimeoutError naming the clone, rather than
    going ahead and racing."""
    if fcntl is None:
        yield
        return
    path = lock_path(clone)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        start, told = time.monotonic(), False
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                waited = time.monotonic() - start
                if waited >= wait:
                    raise TimeoutError(
                        f'another run has held {clone} for {int(waited)}s; '
                        f'nothing was fetched there. Run this again once it '
                        f'finishes')
                if not told and waited >= SAY_AFTER:
                    print(f'waiting for another run to finish with {clone} '
                          f'(up to {wait // 60} minutes)',
                          file=say or sys.stderr, flush=True)
                    told = True
                time.sleep(0.2)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
