#!/usr/bin/env python3
"""Update Vendors' bootstrap: run the update with code at least as new as what it applies

WHY (2026-10-11, todo/todo-2026-10-11-update-vendors-runs-stale-driver-code.md).
precedent_update.py runs from the BestPractice clone's WORKING TREE, and its
fetch moves only the clone's origin refs. A consumer's update stopped on
what read as a BestPractice bug whose fix was already on main: the clone
was behind, and its old code applied the new commit. The session nearly
asked the person to override for nothing.

The rule this restores: the code that runs is never older than the code it
applies. The engine keeps it by reading blobs (_source_tools_at); this does
it for the update itself, without moving the clone -- a checkout in the
caller's clone is the PR #110 failure, and a second run of the update in
parallel must never have its code changed under it.

WHAT IT DOES, before precedent_update.py writes anything into the consumer:
fetch the followed branch, pick the driver commit, and either run in place
or run that commit's precedent_update.py from a detached worktree under
<common git dir>/precedent-update-drivers/, removed when the run ends. The
two tables are the open item's, in order: driver choice (G, data, ancestry)
and where to run (opt-out, dirty, same tools/, ahead, else a worktree).

KEEP IT SMALL AND RARELY TOUCHED. This is the one piece that still runs
from whatever the clone holds: a change here reaches a clone only when that
clone is pulled. It reads and decides; it never writes into the consumer.
Standard library and three engine modules only.
"""
import os
import pathlib
import secrets
import subprocess
import sys

try:
    import fcntl
except ImportError:                                         # pragma: no cover
    fcntl = None

# Set by the person or a harness: run this clone's own code, whatever its
# age -- for someone testing their own unmerged changes to the update.
OPT_OUT_ENV = 'PRECEDENT_UPDATE_RUN_IN_PLACE'
# Set on the run started from a worktree: the driver commit it runs. It is
# the only thing passed across; the run reads it and drops it at once, so
# nothing it spawns inherits it.
GUARD_ENV = 'PRECEDENT_UPDATE_DRIVER'
# Print the verdict and exit 0 without running anything: the seam the
# harness tests both tables through.
ONLY_ENV = 'PRECEDENT_UPDATE_BOOTSTRAP_ONLY'
DRIVERS_DIR = 'precedent-update-drivers'
NO_HOOKS_DIR = 'no-hooks'


def _git(cwd, *args):
    r = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True,
                       text=True)
    # rstrip, never strip: a porcelain line's leading space is its status.
    return r.returncode, r.stdout.rstrip(), r.stderr.strip()


def common_dir(path):
    """-> the absolute git common directory of the repository at `path`
    (a worktree's resolves to its main clone's), or None."""
    rc, out, _err = _git(path, 'rev-parse', '--path-format=absolute',
                         '--git-common-dir')
    return pathlib.Path(out) if rc == 0 and out else None


def display_root(source):
    """-> the path to NAME for `source` in anything a person reads.

    A run started from a driver worktree sits in a directory deleted when it
    ends; a message or a remedy naming it is dead by the time anyone reads
    it. Inside one, the real clone the worktree belongs to; anywhere else,
    `source` itself (no git call)."""
    source = pathlib.Path(source)
    if source.parent.name != DRIVERS_DIR:
        return source
    common = common_dir(source)
    return common.parent if common else source


def _commit(cwd, rev):
    rc, out, _err = _git(cwd, 'rev-parse', '--verify', '-q', f'{rev}^{{commit}}')
    return out if rc == 0 and out else None


def _is_ancestor(cwd, a, b):
    """-> True when commit `a` is `b` or an ancestor of it."""
    return _git(cwd, 'merge-base', '--is-ancestor', a, b)[0] == 0


def newest_green(source, follow, markers, window):
    """-> (G, why-not): rule a/b. On main, the newest first-parent commit
    within `window` whose tree carries a passed marker; on staging, its tip
    (staging carries no markers, as source_commit already takes it). G is
    None with the reason when it cannot be named -- never a guessed tip."""
    if follow != 'main':
        tip = _commit(source, f'origin/{follow}')
        return (tip, None) if tip else (None, f'origin/{follow} is not in the clone')
    if markers is None:
        return None, "the passed markers on origin could not be read"
    rc, listed, _err = _git(source, 'rev-list', '--first-parent',
                            f'--max-count={window}', 'origin/main')
    for sha in (listed.split() if rc == 0 else []):
        if _git(source, 'rev-parse', f'{sha}^{{tree}}')[1] in markers:
            return sha, None
    return None, (f"none of main's newest {window} commits carries a passed "
                  f"marker")


def data_commit(source, follow, g, ref=None, take=None, move=False, pin=None):
    """-> rule c: the commit this run will apply -- --from-ref, else
    --take-anyway, else an unfinished update's pin (when it is on `follow`,
    still in the clone, and --move did not drop it), else G."""
    if ref:
        return _commit(source, ref)
    if take:
        return _commit(source, take)
    if (pin and not move and pin.get('branch') == follow
            and _commit(source, pin.get('commit', ''))):
        return _commit(source, pin['commit'])
    return g


def driver_commit(source, g, data):
    """-> rule d: data is G or newer -> data; data is older -> G;
    diverged (a test commit) -> data. Never older than the data."""
    if data is None or data == g or _is_ancestor(source, g, data):
        return data or g
    if _is_ancestor(source, data, g):
        return g
    return data


def dirty_tools(source):
    """-> the tools/ paths that make the clone's code match no commit:
    tracked changes, and untracked *.py."""
    rc, out, _err = _git(source, 'status', '--porcelain', '--', 'tools')
    found = []
    for line in (out.splitlines() if rc == 0 else []):
        path = line[3:]
        if not line.startswith('??') or path.endswith('.py'):
            found.append(path)
    return found


def where_to_run(source, driver):
    """-> (row, in_place): the second table, first match wins."""
    if os.environ.get(OPT_OUT_ENV):
        return 'opt-out', True
    if dirty_tools(source):
        return 'dirty', True
    head_tools = _git(source, 'rev-parse', 'HEAD:tools')[1]
    if head_tools and head_tools == _git(source, 'rev-parse', f'{driver}:tools')[1]:
        return 'same', True
    head = _commit(source, 'HEAD')
    if head and _is_ancestor(source, driver, head):
        return 'ahead', True
    return 'worktree', False


def decide(source, repo, follow, *, markers, window, ref=None, take=None,
           move=False, pin=None):
    """-> the verdict: {'row', 'in_place', 'g', 'data', 'driver', 'head',
    'line', 'warning'}. Reads only; the fetch is the caller's."""
    head = _commit(source, 'HEAD')
    v = {'row': None, 'in_place': True, 'g': None, 'data': None,
         'driver': None, 'head': head, 'line': None, 'warning': None}
    here = str(display_root(source))
    short = (head or 'an unknown commit')[:12]
    g, why_not = newest_green(source, follow, markers, window)
    v['g'] = g
    if g is None:
        v['row'] = 'no-green'
        v['line'] = f"ran this clone's own code, {here} @ {short}"
        v['warning'] = (f"could not tell which {follow} commit passed GitHub's "
                        f"test ({why_not}), so this ran the clone's own code at "
                        f"{short}, which may be older than what it applies. If "
                        f"it stops on what looks like a BestPractice bug, pull "
                        f"the clone first: git -C {here} pull --ff-only")
        return v
    v['data'] = data_commit(source, follow, g, ref, take, move, pin)
    v['driver'] = driver_commit(source, g, v['data'])
    row, in_place = where_to_run(source, v['driver'])
    v['row'], v['in_place'] = row, in_place
    drv = v['driver'][:12]
    if row == 'opt-out':
        v['line'] = (f"ran this clone's own code, {here} @ {short}, as "
                     f"{OPT_OUT_ENV} asks; the newest it would otherwise run "
                     f"is {drv}")
    elif row == 'dirty':
        v['line'] = f"ran this clone's own code, {here} @ {short} plus local changes"
        v['warning'] = (f"the clone's tools/ has changes no commit holds "
                        f"({', '.join(dirty_tools(source)[:5])}), so this ran "
                        f"them as they are rather than {drv}'s code. Commit or "
                        f"discard them if they are not a test of your own")
    elif row == 'same':
        v['line'] = f"ran this clone's own code, {here} @ {short}: its tools/ is {drv}'s"
    elif row == 'ahead':
        v['line'] = f"ran this clone's own code, {here} @ {short}, which already contains {drv}"
    else:
        v['line'] = (f"ran {drv}'s code from a temporary checkout: the clone, "
                     f"{here}, is at {short}, which lacks it. The clone was "
                     f"not touched")
    return v


def _try_lock(path):
    """-> an open file holding an exclusive flock on `path`, or None when
    another live process holds it."""
    f = open(path, 'a+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def clean_leftovers(source, drivers):
    """Remove each worktree under `drivers` whose run has ended: its lock
    can be taken, and the kernel drops a flock when its holder exits, crash
    and reboot included. A busy one is a live run's, and is left alone.
    Without fcntl (Windows) nothing is judged, and nothing is removed."""
    if fcntl is None or not drivers.is_dir():
        return
    # Only a dead run's checkout is removed (practice: repair-cannot-discard-work).
    for lock in sorted(drivers.glob('*.lock')):
        held = _try_lock(lock)
        if held is None:
            continue
        try:
            tree = drivers / lock.stem
            if tree.exists():
                _git(source, 'worktree', 'remove', '--force', str(tree))
            lock.unlink()
        finally:
            held.close()
    _git(source, 'worktree', 'prune')


def run_from_worktree(source, driver, argv, held):
    """Run `driver`'s precedent_update.py from a detached worktree of
    `source` and -> its exit code, or (None, why) when the worktree could
    not be made. The clone's own branch, HEAD, index and files never move."""
    common = common_dir(source)
    if common is None:
        return None, 'the clone has no git directory to put a worktree in'
    drivers = common / DRIVERS_DIR
    name = f'{os.getpid()}-{driver[:12]}-{secrets.token_hex(3)}'
    tree, lock_file = drivers / name, drivers / f'{name}.lock'
    mine = None
    try:
        with held(source):
            drivers.mkdir(exist_ok=True)
            clean_leftovers(source, drivers)
            if fcntl is not None:
                mine = _try_lock(lock_file)
            no_hooks = drivers / NO_HOOKS_DIR
            no_hooks.mkdir(exist_ok=True)
            # An empty hooks directory, not /dev/null: "no hooks" on every
            # platform. The global post-checkout pass-through would otherwise
            # run the clone's own post-checkout on `worktree add`.
            rc, _out, err = _git(source, '-c', f'core.hooksPath={no_hooks}',
                                 'worktree', 'add', '--detach', str(tree), driver)
        if rc != 0:
            return None, err.splitlines()[-1] if err else 'git worktree add failed'
        env = {**os.environ, GUARD_ENV: driver}
        script = tree / 'tools' / 'precedent_update.py'
        return subprocess.run([sys.executable, str(script), *argv],
                              env=env).returncode, None
    except OSError as e:
        return None, str(e)
    finally:
        if tree.exists():
            with held(source):
                _git(source, 'worktree', 'remove', '--force', str(tree))
        if mine is not None:
            try:
                lock_file.unlink()
            except OSError:
                pass
            mine.close()


def child_line(source):
    """-> the 'code' line for a run started from a driver worktree, and
    drops the guard so nothing this run spawns inherits it."""
    driver = os.environ.pop(GUARD_ENV, '')
    clone = display_root(source)
    head = (_commit(clone, 'HEAD') or 'an unknown commit')[:12]
    return (f"ran {driver[:12]}'s code from a temporary checkout: the clone, "
            f"{clone}, is at {head}, which lacks it. The clone was not touched")
