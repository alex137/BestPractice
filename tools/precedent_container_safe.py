#!/usr/bin/env python3
"""Is anything in THIS CONTAINER unsaved -- anywhere, not just the repo the
session happens to be rooted in?

WHY THIS EXISTS. Archiving a session releases its container, and everything
in that container that is not pushed somewhere goes with it. `the-boildown`
already gated its archive line on "the work is safe somewhere that is not
this session's container", and a session reading that reliably checked the
one clone it had been working in -- because that is the clone `git status`
answers for, and because "the work" reads as "the thing I was asked to do".
Neither reading is wrong; both are too narrow. A container here routinely
holds five or six checkouts: this repo, a second copy of it under a
different HOME, and one per practice source. On 2026-09-22 a session said
"You can archive this session" with six unpushed commits sitting in
~/precedent-individual, correctly reporting that its OWN eight commits were
pushed. Morgan, same day: *"if changes are done locally but not pushed to
main or precedent-beta-v01 then never never recommend 'You can archive this
session' (unless the work is intended to be lost!)"*.

So the question this answers is not "did I push my work" but "would
anything we want to keep be lost if this container went away right now",
and it answers it by looking, in every checkout it can find, rather than by
asking the session to remember.

WHAT COUNTS AS UNSAFE, three things, per checkout:
  * tracked changes, staged or not
  * untracked files git is not already ignoring
  * commits on HEAD that no remote-tracking ref can reach

WHAT DELIBERATELY DOES NOT. Engine output written into a source clone by
`precedent_refresh_sources.py`, which that tool writes on every run and
deliberately never commits (`classify_dirt` is the one definition of which
paths those are, imported rather than restated). Counting it would make
every clone permanently unsafe and teach a session to ignore the answer --
the exact failure mode `classify_dirt`'s own docstring records from the
other direction.

AND ONE MORE THING, OUTSIDE ANY CHECKOUT: commands still running. A
background command this session started and never stopped is not saved
work, but it is not nothing either: archiving the container kills it, and
one that waits forever keeps running until then. On 2026-09-28 two wait
loops ran for five hours after the script they waited on had finished,
because `pgrep -f <name>` matched the loop's own command line
(gotchas/gotcha-2026-09-28-a-wait-loop-on-pgrep-f-finds-itself-and-never-ends.md),
while this tool said the container was clean. So a scan that discovers its
checkouts also lists every shell the agent running this session started
that is still running and is not part of this check. It finds that agent
by name among this process's ancestors (AGENT_NAMES, or
PRECEDENT_AGENT_PROCESS); run from a person's own terminal, where there is
no agent above it, it lists nothing rather than guess.

EXIT CODES. 0 when nothing would be lost and nothing is still running, 1
otherwise. `--json`
prints the finding machine-readably; the default prints one line per
unsafe checkout, naming the path, the branch, and which of the three it is.
Provider-neutral by construction: it shells out to git and to nothing else.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

try:
    import precedent_refresh_sources as _refresh
except Exception:                     # a source-config problem is that
    _refresh = None                   # tool's to report; never fatal here


def _git(repo, *args):
    """(ok, stdout). Never raises: a checkout that cannot answer is reported
    as unknown, which is not the same as safe and is not the same as a crash
    that takes the whole scan down."""
    try:
        p = subprocess.run(['git', *args], cwd=str(repo),
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f'{type(exc).__name__}: {exc}'
    return p.returncode == 0, (p.stdout or '').strip()


def _is_checkout(path):
    ok, out = _git(path, 'rev-parse', '--show-toplevel')
    return ok and out and pathlib.Path(out).resolve() == pathlib.Path(path).resolve()


def checkouts():
    """Every git checkout this container is likely to be holding work in,
    resolved and de-duplicated.

    Four places, and each earned its line. THIS repo, which is the one a
    session already checks. Its SIBLINGS, because an attached repo lands
    beside it. The HOME directory's children, because the source clones a
    SessionStart hook writes go there -- and because a second copy of this
    very repo can sit there too, under a different HOME than the session's
    working directory, which is how `/root/BestPractice` and
    `/home/user/BestPractice` coexist. And whatever the source config
    DECLARES, since an individual set is cloned wherever its owner's
    user-level config says, which need not be either of the above."""
    seen, out = [], []
    cands = [ROOT, *sorted(ROOT.parent.iterdir()),
             *sorted(pathlib.Path.home().iterdir())]
    if _refresh is not None:
        try:
            cands += _refresh.declared_paths()
        except Exception:
            pass
    for p in cands:
        try:
            p = pathlib.Path(p).expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        if p in seen or not p.is_dir():
            continue
        seen.append(p)
        if _is_checkout(p):
            out.append(p)
    return out


def _engine_dirt(repo):
    """Paths in this checkout that are the refresh tool's own output. Empty
    for anything that is not a vendored source clone."""
    if _refresh is None:
        return set()
    try:
        engine, _other = _refresh.classify_dirt(repo)
    except Exception:
        return set()
    return set(engine)


def scan_one(repo):
    """-> {'repo', 'branch', 'unsafe': [reason, ...], 'detail': {...}}."""
    ok, branch = _git(repo, 'rev-parse', '--abbrev-ref', 'HEAD')
    branch = branch if ok else '?'
    unsafe, detail = [], {}

    ignore = _engine_dirt(repo)
    ok, porcelain = _git(repo, 'status', '--porcelain', '--untracked-files=normal')
    if ok:
        tracked, untracked = [], []
        for line in porcelain.splitlines():
            code, _, path = line.partition(' ')
            path = (line[2:] if len(line) > 2 else line).strip()
            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1]
            if not path or path in ignore:
                continue
            (untracked if line.lstrip().startswith('??') else tracked).append(path)
        if tracked:
            unsafe.append('uncommitted changes')
            detail['uncommitted'] = sorted(tracked)[:20]
        if untracked:
            unsafe.append('untracked files')
            detail['untracked'] = sorted(untracked)[:20]

    # Commits no remote can reach. `--remotes` rather than
    # origin/<branch>: work parked on a local branch whose upstream does
    # not exist yet is exactly the work most likely to be lost, and
    # comparing against one named remote branch cannot see it.
    ok, out = _git(repo, 'rev-list', '--count', 'HEAD', '--not', '--remotes')
    # Commits that change no file -- a merge, an empty commit -- lose nothing
    # when the container goes, so they are never reported as work at risk
    # (Morgan, 2026-09-27, strength: decided). Proven by content: HEAD's
    # files are identical to its branch on origin.
    if ok and out.isdigit() and int(out) > 0 and branch and _git(
            repo, 'diff', '--quiet', f'origin/{branch}', 'HEAD')[0]:
        out = '0'
    if ok and out.isdigit() and int(out) > 0:
        ok_real, real = _git(repo, 'rev-list', '--count', '--no-merges', 'HEAD',
                             '--not', '--remotes', '--', '.')
        if ok_real and real.isdigit() and int(real) > 0:
            out = real
        unsafe.append(f'{out} commit(s) on no remote')
        detail['unpushed'] = int(out)
        ok2, subjects = _git(repo, 'log', '--oneline', '-5', 'HEAD', '--not', '--remotes')
        if ok2 and subjects:
            detail['unpushed_head'] = subjects.splitlines()

    return {'repo': str(repo), 'branch': branch, 'unsafe': unsafe, 'detail': detail}


# The processes a coding agent runs as. A shell one of them started is a
# command the session ran; anything else under it (a language server, an MCP
# server) is the agent's own machinery and is never listed.
AGENT_NAMES = ('claude', 'codex', 'gemini', 'grok')
SHELLS = ('bash', 'sh', 'zsh', 'dash', 'fish')


def _ps_rows():
    """-> [(pid, ppid, elapsed, args)] for every process, or [] if `ps`
    cannot answer. `ps -eo` works on Linux and macOS alike."""
    try:
        p = subprocess.run(['ps', '-eo', 'pid=,ppid=,etime=,args='],
                           capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for line in p.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[0].isdigit() and parts[1].isdigit():
            rows.append((int(parts[0]), int(parts[1]), parts[2], parts[3]))
    return rows


def _base(args):
    first = args.split(None, 1)[0] if args.strip() else ''
    return first.rsplit('/', 1)[-1].lstrip('-')


def _shown(args):
    """The command a person would recognise: the text a tool shell `eval`s,
    without the wrapper every such shell carries around it."""
    if "eval '" in args:
        args = args.rsplit("eval '", 1)[1].split("' < /dev/null", 1)[0]
    return ' '.join(args.split())[:200]


def still_running(rows=None, me=None, agent_names=None):
    """-> [{'pid', 'elapsed', 'command'}] for every shell the agent above
    `me` started that is still running and is not one of `me`'s own
    ancestors. [] when no agent is found above `me`."""
    rows = _ps_rows() if rows is None else rows
    me = os.getpid() if me is None else me
    names = agent_names or tuple(
        n for n in (os.environ.get('PRECEDENT_AGENT_PROCESS', '').split(',')
                    + list(AGENT_NAMES)) if n)
    parent = {pid: ppid for pid, ppid, _e, _a in rows}
    args_of = {pid: a for pid, _pp, _e, a in rows}
    ancestors, cur = [], me
    while cur in parent and cur not in ancestors and cur > 1:
        ancestors.append(cur)
        cur = parent[cur]
    agent = next((a for a in ancestors[1:]
                  if any(n in _base(args_of.get(a, '')) for n in names)), None)
    if agent is None:
        return []
    return [{'pid': pid, 'elapsed': e, 'command': _shown(a)}
            for pid, ppid, e, a in rows
            if ppid == agent and pid not in ancestors and _base(a) in SHELLS]


def label(repo):
    try:
        return '~/' + str(pathlib.Path(repo).relative_to(pathlib.Path.home()))
    except ValueError:
        return str(repo)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--only', nargs='+', metavar='DIR', default=None,
                    help='scan exactly these checkouts instead of discovering '
                         'them -- what a test plants a known container with, '
                         'and what a person uses to ask about one directory')
    ap.add_argument('--json', action='store_true',
                    help='machine-readable finding on stdout')
    ap.add_argument('--no-processes', action='store_true',
                    help='check the checkouts only, not commands still running')
    ap.add_argument('--quiet', action='store_true',
                    help='print nothing; say it in the exit code alone')
    args = ap.parse_args(argv)

    if args.only:
        targets = []
        for raw in args.only:
            d = pathlib.Path(raw).expanduser().resolve()
            if _is_checkout(d):
                targets.append(d)
            else:
                print(f'not a git checkout, skipped: {d}', file=sys.stderr)
    else:
        targets = checkouts()
    found = [scan_one(r) for r in targets]
    bad = [f for f in found if f['unsafe']]
    # Only when discovering: --only is a question about named checkouts,
    # and a planted test container must not depend on what else is running.
    running = [] if (args.only or args.no_processes) else still_running()

    if args.json:
        print(json.dumps({'safe': not bad and not running,
                          'scanned': len(found), 'unsafe': bad,
                          'still_running': running}, indent=1))
    elif not args.quiet:
        if running:
            print(f'STILL RUNNING -- {len(running)} command(s) this session '
                  f'started have not finished; archiving the container kills '
                  f'them. Stop each one that has nothing left to do, or wait:')
            for r in running:
                print(f"  pid {r['pid']}, running {r['elapsed']}: {r['command']}")
            print()
        if not bad:
            print(f'container safe: {len(found)} checkout(s), '
                  f'nothing uncommitted and nothing off a remote'
                  + ('' if not running else ' (but see STILL RUNNING above)'))
        else:
            print(f'CONTAINER NOT SAFE TO LOSE -- {len(bad)} of {len(found)} '
                  f'checkout(s) hold work that is only here:')
            for f in bad:
                print(f"  {label(f['repo'])} ({f['branch']}): "
                      f"{', '.join(f['unsafe'])}")
                for k in ('uncommitted', 'untracked'):
                    if f['detail'].get(k):
                        print(f"      {k}: {', '.join(f['detail'][k][:6])}"
                              + (' ...' if len(f['detail'][k]) > 6 else ''))
                for line in f['detail'].get('unpushed_head', [])[:3]:
                    print(f'      {line}')
            print('\nPush or merge it, or say plainly that it is meant to be '
                  'lost, before telling anyone the session can be archived.')
    return 1 if (bad or running) else 0


if __name__ == '__main__':
    sys.exit(main())
