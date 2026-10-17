#!/usr/bin/env python3
"""Would anything be lost if this container went away? Scans every git checkout in it for uncommitted, untracked and unpushed work

Is anything in THIS CONTAINER unsaved -- anywhere, not just the repo the
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
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

try:
    import precedent_refresh_sources as _refresh
except Exception:                     # a source-config problem is that
    _refresh = None                   # tool's to report; never fatal here


def fetch_missing_tracking_ref(repo, branch):
    """Fetch origin's `branch` into refs/remotes/origin/<branch> when this
    clone has no such ref and origin has the branch. -> True when it fetched.

    A SHALLOW, SINGLE-BRANCH CLONE NEVER LEARNS ITS OWN PUSHES (2026-10-17).
    `git clone --depth 1` (what attaching a repository mid-session runs)
    sets a fetch refspec for the default branch only, so `git push -u` of a
    feature branch creates no refs/remotes/origin/<branch>. Every check
    asking "is HEAD on a remote?" through --remotes then reported a pushed
    commit as "on no remote", and held the archive line over work that was
    safe. Making the ref exist is the repair: the question is then answered
    the ordinary way, here and by every later check."""
    if not branch or _git(repo, 'rev-parse', '--verify', '-q',
                          f'refs/remotes/origin/{branch}')[0]:
        return False
    ok, out = _git(repo, 'ls-remote', '--heads', 'origin', branch)
    if not ok or not out.strip():
        return False
    return _git(repo, 'fetch', '-q', 'origin',
                f'+refs/heads/{branch}:refs/remotes/origin/{branch}')[0]


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


# WORK LEFT IN A SCRATCH FOLDER (2026-10-11). A session's scratch folder is
# outside every repository, so the checkout scan above never sees it. On
# 2026-10-11 a session in a consuming repo built 189 summaries there, had the
# filing step refused, and moved on; had it closed then, the archive line
# would have passed and the summaries gone with the container. Morgan:
# "EVERYTHING MUST GO INTO A REPO." repo-is-memory says finished work never
# waits there; this makes the closing line unable to pass over it. Measured
# the same day: six scratch folders in one container, one file between
# them, and that one a page already published -- so in practice it costs a
# session nothing.
#
# Where: the harness's scratch folders (one per session, under
# /tmp/claude-<uid>/<project>/<session>/scratchpad), plus any folder a
# repository names in its precedent.json `scratch_dirs`.
SCRATCH_GLOB = '/tmp/claude-*/*/*/scratchpad'
try:
    from precedent_stale_branches import PAGE_FILENAME as _BRANCH_PAGE
except Exception:                                           # noqa: BLE001
    _BRANCH_PAGE = 'branch-cleanup.html'
# Files a tool writes into the scratch folder only to publish them at once.
PUBLISHED_ON_PURPOSE = frozenset({_BRANCH_PAGE})
# Folders that only ever hold copies of something already published: the
# Artifact tool's read saves a page, or a file of one, under
# <scratchpad>/artifact-files/<artifact id>/ by default. Found the night the
# scratch scan shipped (2026-10-12): the first session to read a live page
# before republishing it was told its container was unsafe over that copy.
PUBLISHED_COPY_DIRS = frozenset({'artifact-files'})


def scratch_dirs():
    """-> every scratch folder in this container, resolved and de-duplicated."""
    import glob
    cands = [pathlib.Path(p) for p in glob.glob(SCRATCH_GLOB)]
    try:
        cfg = json.loads((ROOT / 'precedent.json').read_text(encoding='utf-8'))
        for raw in cfg.get('scratch_dirs') or []:
            p = pathlib.Path(str(raw)).expanduser()
            cands.append(p if p.is_absolute() else ROOT / p)
    except (OSError, ValueError, AttributeError):
        pass
    out = []
    for p in cands:
        try:
            p = p.resolve()
        except (OSError, RuntimeError):
            continue
        if p.is_dir() and p not in out:
            out.append(p)
    return sorted(out)


def scratch_name(d):
    """-> the name a reply gives a scratch folder up by: `scratch:` and the
    first eight characters of the folder it sits in (the session's ID for
    the harness's own), because every harness folder is called scratchpad."""
    d = pathlib.Path(d)
    owner = d.parent.name if d.name == 'scratchpad' else d.name
    return f'scratch:{owner[:8]}'


# A file whose text is already a commit's message: a session writes its
# message to a scratch file and runs `git commit -F` on it. Found
# 2026-10-13, in an Update Vendors run whose commit had landed, been pushed
# and merged, and whose archive line was still refused over msg.txt.
# Matched against the newest commits on HEAD and every remote-tracking ref
# of the checkouts scanned -- a commit only on HEAD is the checkout scan's
# to report -- and only for a file small enough to be a message.
COMMIT_MSG_WINDOW = 400
COMMIT_MSG_MAX_BYTES = 64 * 1024
# The markers precedent-ci-cadence's commit-msg hook adds, as
# tools/commit-identity.sh writes them; stripped from both sides.
_SKIP_MARK = re.compile(r'\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]',
                        re.I)


def _msg_lines(text):
    """-> a message's non-blank lines, trailing space and CI skip markers
    stripped: what git's own cleanup and the cadence hook leave alone."""
    out = []
    for line in text.splitlines():
        line = _SKIP_MARK.sub('', line).rstrip()
        if line.strip():
            out.append(line)
    return out


def commit_messages(repos):
    """-> the message lines of the newest commits on HEAD and every
    remote-tracking ref of `repos`, as a list of line lists."""
    msgs = []
    for repo in repos:
        ok, out = _git(repo, 'log', f'-n{COMMIT_MSG_WINDOW}', '--format=%B%x00',
                       'HEAD', '--remotes')
        if ok:
            msgs.extend(m for m in (_msg_lines(b) for b in out.split('\0')) if m)
    return msgs


def is_commit_message(path, msgs):
    """True when every line of the file at `path` is in one commit's message,
    in order, starting with its subject. Lines the commit has and the file
    lacks are what a hook added; nothing in the file is lost."""
    try:
        if path.stat().st_size > COMMIT_MSG_MAX_BYTES:
            return False
        want = _msg_lines(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError):
        return False
    if not want:
        return False
    for have in msgs:
        if have[0] != want[0]:
            continue
        it = iter(have)
        if all(line in it for line in want):
            return True
    return False


def scan_scratch(d, repos=()):
    """-> an entry shaped like scan_one's, or None when the folder holds
    nothing but files published on purpose, or commit messages already in
    one of `repos`."""
    d = pathlib.Path(d)
    files, msgs = [], None
    for f in sorted(d.rglob('*')):
        rel = f.relative_to(d)
        if (f.is_file() and f.name not in PUBLISHED_ON_PURPOSE
                and rel.parts[0] not in PUBLISHED_COPY_DIRS):
            if msgs is None:
                msgs = commit_messages(repos)
            if is_commit_message(f, msgs):
                continue
            files.append(str(rel))
    if not files:
        return None
    return {'repo': str(d), 'name': scratch_name(d), 'branch': 'scratch folder',
            'unsafe': [f'{len(files)} file(s) in a scratch folder, in no '
                       f'repository'],
            'detail': {'untracked': files[:20]}}


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
    if ok and out.isdigit() and int(out) > 0 and fetch_missing_tracking_ref(repo, branch):
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


# A HOOK IS NOT THE SESSION'S WORK (2026-09-30). The harness runs a hook
# for the same event as a child of the agent too, so a hook firing beside
# this check -- freshness-guard.sh on the same prompt as the reply gate --
# read as a command the session left running and forbade the archive line;
# it had exited seconds later. Every adapter in templates/harness/ runs its
# hooks from a `.claude/hooks/` directory (Gemini CLI and Codex through
# `bash .claude/hooks/...`), and none wraps a hook the way an agent wraps
# its own tool command (`eval '...'`). A shell counts as a hook only when
# both hold, so a hook script the session started by hand, in its own tool
# shell, is still listed.
_HOOK_SCRIPT = re.compile(r'(?:^|[\s/"\'}])\.claude/hooks/[\w.-]+\.sh\b')


def _is_hook(args):
    return "eval '" not in args and bool(_HOOK_SCRIPT.search(args))


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
            if ppid == agent and pid not in ancestors and _base(a) in SHELLS
            and not _is_hook(a)]


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
    ap.add_argument('--scratch', nargs='+', metavar='DIR', default=None,
                    help='check exactly these scratch folders instead of '
                         'discovering them (with --only and no --scratch, '
                         'none is checked)')
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
    if args.scratch:
        scratch = [pathlib.Path(x).expanduser().resolve() for x in args.scratch]
    else:
        scratch = [] if args.only else scratch_dirs()
    leftovers = [e for e in (scan_scratch(d, targets) for d in scratch
                                  if d.is_dir()) if e]
    bad = [f for f in found if f['unsafe']] + leftovers
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
                  + (f', {len(scratch)} scratch folder(s) empty'
                     if scratch else '')
                  + ('' if not running else ' (but see STILL RUNNING above)'))
        else:
            print(f'CONTAINER NOT SAFE TO LOSE -- {len(bad)} of '
                  f'{len(found) + len(scratch)} checkout(s) and scratch '
                  f'folder(s) hold work that is only here:')
            for f in bad:
                where = (f"{f['name']} -- {f['repo']}" if f.get('name')
                         else label(f['repo']))
                print(f"  {where} ({f['branch']}): "
                      f"{', '.join(f['unsafe'])}")
                for k in ('uncommitted', 'untracked'):
                    if f['detail'].get(k):
                        print(f"      {k}: {', '.join(f['detail'][k][:6])}"
                              + (' ...' if len(f['detail'][k]) > 6 else ''))
                for line in f['detail'].get('unpushed_head', [])[:3]:
                    print(f'      {line}')
            print('\nPush or merge it, or say plainly that it is meant to be '
                  'lost, before telling anyone the session can be archived.'
                  + (' A scratch folder\'s files go into a repository, or the '
                     'folder is given up by the name shown.' if leftovers else ''))
    return 1 if (bad or running) else 0


if __name__ == '__main__':
    sys.exit(main())
