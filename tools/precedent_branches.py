#!/usr/bin/env python3
"""precedent_branches.py -- the three branch tiers, and what a push to each
one is checked with. spec/BRANCH_TIERS_PLAN.md is the plan this implements.

THE RULE (Morgan, 2026-09-25, strength: decided): "to prestaging only the
most minimal test; to staging/precedent-beta-v01 all local tests; and then
to main, you get all those local tests AND the most important GitHub test",
and "the default for everyone should be all branches other than the above
never get tested beyond the basic markdown test when pushed to".

  pre-staging, and any other branch   basic  (markdown lint, leak gate,
                                               the commit-author checks)
  staging                             full   (everything
                                               precedent_push_check.py runs)
  main                                full, plus one GitHub test on the
                                               pull request into it

WHY ONE MODULE. The literal `precedent-beta-v01` sat in 249 files of this
repository when the plan was written, 37 of them under tools/. The same
three names are meant to hold in every repository, and the staging branch
is being renamed; every tool that needs a tier name asks here, so the
rename is a change in one place (practice: registry-source-of-truth).

STAGING BEFORE THE RENAME. Until a repository has a branch called
`staging`, its staging tier is whatever it declares as `base_branch` in
precedent.json -- `precedent-beta-v01` in the Precedent repositories. A
repository whose base_branch is `main` -- most repositories that install
Precedent -- has no separate staging branch yet, so its staging tier IS
main: pre-staging is created from main and promoted into main, and `Go
update` for a person who has not chosen pre-staging lands on main, as it
always did. (Until 2026-09-25 this answered `staging` there, a branch those
repositories do not have -- found before any of them had taken the engine.)

A PUSH NOBODY CAN READ IS CHECKED FULLY. push_targets() returns None for a
push whose destination it cannot establish (--all, --mirror, --tags, a tag
refspec, a detached HEAD), and tier_for_push() answers `full` for None.
Getting it wrong in that direction costs minutes; the other direction
lands unchecked work.

The person's setting, `branch_push_checks`, is read the way
spec/CI_CADENCE_PLAN.md reads its own: a repository's precedent.json wins,
then the person's identity.json (this repository's own when it is an
individual source, else the one ~/.config/precedent/config.json names),
then the default, `basic`. Nothing it says can lower staging or main.

WHERE `Go update` LANDS is the person's `landing_branch` setting, read
the same way: `pre-staging` (the default, for everyone, since 2026-09-25),
`staging`, or `main`. An unreadable value lands on staging, where work landed
before the tiers existed, never somewhere new.

PROMOTE moves pre-staging into staging (plan step 6; Morgan named the
command, strength: assented). It merges staging into pre-staging first when
staging has moved on its own, then makes a merge commit of pre-staging onto
staging -- always a merge commit, never a fast-forward, so a `[skip ci]`
line on a pre-staging commit can never become staging's head and silence
the GitHub test on the pull request into main (plan, hole 3) -- runs the
FULL push check on exactly that commit in a throwaway worktree, and pushes
it to staging only if it passes. It pushes by itself, so it runs the check
by itself: no push gate sees a push made from inside a script.

CLI:
  precedent_branches.py                     the tiers, as this repo resolves them
  precedent_branches.py --tier BRANCH       prints `basic` or `full`
  precedent_branches.py --push ARGS...      the tier a `git push ARGS...` gets
  precedent_branches.py --landing           where `Go update` lands for this person
  precedent_branches.py --sync-pre-staging  create pre-staging, or merge staging into it
  precedent_branches.py --promote           pre-staging into staging, fully checked
"""
import json
import os
import pathlib
import shlex
import subprocess
import sys

PRE_STAGING = 'pre-staging'
STAGING = 'staging'
# The staging branch's name until 2026-09-25, in the Precedent repositories.
# Kept on origin, and fast-forwarded to staging by every Promote, so an
# install still pinned to it takes one more update from it -- onto an
# engine that names staging -- and then follows staging. Work pushed there
# by a session that has not moved yet is merged into pre-staging by the
# sync, never lost (spec/BRANCH_TIERS_PLAN.md, step 10).
LEGACY_STAGING = 'precedent-beta-v01'
MAIN = 'main'
BASIC = 'basic'
FULL = 'full'
TIERS = (BASIC, FULL)

SETTING = 'branch_push_checks'
DEFAULT_TIER = BASIC
LANDING_SETTING = 'landing_branch'
# PRE_STAGING for everyone since 2026-09-25, once Alex had heard and
# approved (relayed by Morgan: "Alex is on top of this and approves").
# A person who wants to land on staging sets landing_branch there.
DEFAULT_LANDING = PRE_STAGING

# Same names and values as precedent_identity.py, duplicated rather than
# imported for the reason that file gives for duplicating them itself: this
# module must import cleanly in every kind of repository, with nothing else
# vendored beside it.
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'
DEFAULT_USER_CONFIG = pathlib.Path.home() / '.config' / 'precedent' / 'config.json'


def _read_json(path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def precedent_json(root):
    return _read_json(pathlib.Path(root) / 'precedent.json') or {}


def base_branch(root):
    """The branch precedent.json declares, or None."""
    value = precedent_json(root).get('base_branch')
    return value.strip() if isinstance(value, str) and value.strip() else None


def staging_branch(root):
    """The staging tier's branch name in this repository, today."""
    declared = base_branch(root)
    if declared and declared != PRE_STAGING:
        return declared
    return STAGING


def full_branches(root):
    """Every branch a push to is always fully checked."""
    # The pre-rename name stays fully checked while it exists: a push there
    # is a push to staging under its old name.
    names = {MAIN, STAGING, LEGACY_STAGING, staging_branch(root)}
    declared = base_branch(root)
    if declared and declared != PRE_STAGING:
        names.add(declared)
    return names


def _identity_files(root, user_config=None):
    """identity.json candidates, in the order they win."""
    root = pathlib.Path(root)
    yield root / 'identity.json'
    cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    cfg = _read_json(cfg_path) or {}
    indiv = cfg.get('individual')
    path = indiv.get('path') if isinstance(indiv, dict) else None
    if isinstance(path, str) and path:
        yield pathlib.Path(path).expanduser() / 'identity.json'


def personal_setting(root, key, user_config=None):
    """-> (value, where) for a per-person setting, or (None, None). A
    repository's own precedent.json wins over the person."""
    repo = precedent_json(root)
    if key in repo:
        return repo[key], "this repo's precedent.json"
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email') and key in ident:
            return ident[key], str(path)
    return None, None


def branch_push_checks(root, user_config=None):
    """-> (tier, why) for a push to any branch but staging and main."""
    value, where = personal_setting(root, SETTING, user_config)
    if value is None:
        return DEFAULT_TIER, f'{SETTING} is not set anywhere; the default is {DEFAULT_TIER}'
    if value in TIERS:
        return value, f'{SETTING} is "{value}" in {where}'
    # A typo can only make a push slower, never less checked.
    return FULL, (f'{SETTING} is {value!r} in {where}, which is neither '
                  f'"basic" nor "full" -- checked fully until it is fixed')


def tier_for_branch(root, branch, user_config=None):
    """-> (tier, why) for a push to `branch`."""
    if branch in full_branches(root):
        return FULL, f'{branch} is a fully checked branch'
    tier, why = branch_push_checks(root, user_config)
    return tier, f'{branch}: {why}'


def landing_branch(root, user_config=None):
    """-> (branch, why): where this person's `Go update` lands."""
    value, where = personal_setting(root, LANDING_SETTING, user_config)
    if value is None:
        tier, why = DEFAULT_LANDING, f'{LANDING_SETTING} is not set; the default is {DEFAULT_LANDING}'
    elif value in (PRE_STAGING, STAGING, MAIN):
        tier, why = value, f'{LANDING_SETTING} is "{value}" in {where}'
    else:
        tier, why = STAGING, (f'{LANDING_SETTING} is {value!r} in {where}, which '
                              f'is none of "pre-staging", "staging" or "main" -- '
                              f'landing on staging, as before the tiers')
    if tier == PRE_STAGING:
        return PRE_STAGING, why
    if tier == MAIN:
        # Straight to main is a person's choice to make (Morgan, 2026-09-25:
        # "they have to be able to set it to \"main\" if they want"). It
        # skips staging, never the checks: a push to main is fully checked
        # like one to staging. A repository's own rule about main -- this
        # one's needs Alex's named go-ahead for a major change -- still
        # decides whether a session may push there.
        return MAIN, why
    return staging_branch(root), why


def _git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def _run(root, *args, env=None):
    return subprocess.run(['git', '-C', str(root), *args],
                          capture_output=True, text=True, env=env)


def _remote_tip(root, branch):
    out = _git(root, 'ls-remote', '--heads', 'origin', branch) or ''
    for line in out.splitlines():
        sha, _, ref = line.partition('\t')
        if ref == f'refs/heads/{branch}':
            return sha
    return None


def _merge_env():
    """A merge commit this module makes must never carry `[skip ci]`
    (plan, hole 3): PRECEDENT_CI_NOW is the cadence hook's own override."""
    env = dict(os.environ, PRECEDENT_CI_NOW='1')
    return env


def _push_check_tool(root):
    for rel in ('tools/precedent_push_check.py',
                'process/upstream/tools/precedent_push_check.py'):
        if (pathlib.Path(root) / rel).is_file():
            return rel
    return None


class _Worktree:
    """A throwaway detached worktree, removed on exit whatever happens."""
    def __init__(self, root, commit):
        import tempfile
        self.root, self.commit = root, commit
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-branches-'))
        self.path = self.tmp / 'tree'

    def __enter__(self):
        p = _run(self.root, 'worktree', 'add', '-q', '--detach', str(self.path), self.commit)
        if p.returncode != 0:
            raise RuntimeError(f'could not make a worktree of {self.commit}: {p.stderr.strip()[:300]}')
        return self.path

    def __exit__(self, *exc):
        import shutil
        _run(self.root, 'worktree', 'remove', '--force', str(self.path))
        shutil.rmtree(self.tmp, ignore_errors=True)
        _run(self.root, 'worktree', 'prune')
        return False


def _check(root, wt, tier):
    """-> (ok, output): the repo's own push check at `tier` in worktree
    `wt`, reusing a pass the checkout already recorded for the same tree."""
    tool = _push_check_tool(wt)
    if tool is None:
        return False, 'this repository carries no precedent_push_check.py, so nothing could be checked'
    src = _git(root, 'rev-parse', '--git-path', 'precedent-push-check.json')
    dst = _git(wt, 'rev-parse', '--git-path', 'precedent-push-check.json')
    if src and dst:
        import shutil
        src_p = pathlib.Path(src) if pathlib.Path(src).is_absolute() else pathlib.Path(root) / src
        dst_p = pathlib.Path(dst) if pathlib.Path(dst).is_absolute() else wt / dst
        if src_p.is_file():
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst_p)
    p = subprocess.run([sys.executable, tool, '--gate', '--tier', tier],
                       cwd=wt, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).rstrip()


def sync_pre_staging(root, say=print):
    """Make origin's pre-staging exist and contain staging. -> True on
    success. Creates it at staging's tip when origin has none; merges
    staging in when staging has moved on its own (plan, hole 2); stops and
    says so on a conflict, touching nothing."""
    staging = staging_branch(root)
    _run(root, 'fetch', '-q', 'origin', staging)
    stip = _remote_tip(root, staging)
    if not stip:
        say(f'origin has no {staging} branch, so there is nothing to base pre-staging on.')
        return False
    ptip = _remote_tip(root, PRE_STAGING)
    if not ptip:
        p = _run(root, 'push', '-q', 'origin', f'{stip}:refs/heads/{PRE_STAGING}')
        if p.returncode != 0:
            say(f'could not create {PRE_STAGING} on origin: {p.stderr.strip()[:300]}')
            return False
        say(f'created {PRE_STAGING} on origin at {staging} ({stip[:12]}).')
        return True
    _run(root, 'fetch', '-q', 'origin', PRE_STAGING)
    sources = [(staging, stip)]
    if staging != LEGACY_STAGING:
        ltip = _remote_tip(root, LEGACY_STAGING)
        if ltip:
            _run(root, 'fetch', '-q', 'origin', LEGACY_STAGING)
            sources.append((LEGACY_STAGING, ltip))
    pending = [(b, t) for b, t in sources
               if _run(root, 'merge-base', '--is-ancestor', t, ptip).returncode != 0]
    if not pending:
        return True
    with _Worktree(root, ptip) as wt:
        for branch, tip in pending:
            m = _run(wt, 'merge', '--no-ff', '-q', '-m',
                     f'Merge {branch} into {PRE_STAGING}', tip, env=_merge_env())
            if m.returncode != 0:
                _run(wt, 'merge', '--abort')
                say(f'{branch} does not merge cleanly into {PRE_STAGING} -- the same '
                    f'lines changed on both. Nothing was pushed. Merge {branch} into '
                    f'{PRE_STAGING} by hand, resolve it, and push to {PRE_STAGING}.')
                return False
        ok, out = _check(root, wt, BASIC)
        if not ok:
            say(f'the merge of {staging} into {PRE_STAGING} fails the basic check; nothing was pushed.\n{out}')
            return False
        p = _run(wt, 'push', '-q', 'origin', f'HEAD:refs/heads/{PRE_STAGING}')
        if p.returncode != 0:
            say(f'{PRE_STAGING} moved while this ran; run it again. ({p.stderr.strip()[:200]})')
            return False
    say(f'merged {" and ".join(b for b, _ in pending)} into {PRE_STAGING}.')
    return True


def promote(root, say=print):
    """Pre-staging into staging, fully checked. -> 0 promoted or nothing to
    promote; 1 refused (a failing check, a conflict, a race)."""
    staging = staging_branch(root)
    if not sync_pre_staging(root, say):
        return 1
    stip, ptip = _remote_tip(root, staging), _remote_tip(root, PRE_STAGING)
    _run(root, 'fetch', '-q', 'origin', staging, PRE_STAGING)
    if _run(root, 'merge-base', '--is-ancestor', ptip, stip).returncode == 0:
        say(f'nothing to promote: {staging} already has everything on {PRE_STAGING}.')
        return 0
    batch = (_git(root, 'log', '--oneline', '--no-merges', f'{stip}..{ptip}') or '').splitlines()
    with _Worktree(root, stip) as wt:
        m = _run(wt, 'merge', '--no-ff', '-q', '-m',
                 f'Promote {PRE_STAGING} into {staging} ({len(batch)} commit(s))',
                 ptip, env=_merge_env())
        if m.returncode != 0:
            _run(wt, 'merge', '--abort')
            say(f'{PRE_STAGING} does not merge cleanly into {staging}; nothing was pushed.')
            return 1
        say(f'checking {len(batch)} commit(s) from {PRE_STAGING} with the full push check...')
        ok, out = _check(root, wt, FULL)
        if not ok:
            say(f'PROMOTE REFUSED: the full check failed, so {staging} did not move. '
                f'The batch was:\n  ' + '\n  '.join(batch) + f'\n\n{out}\n\n'
                f'Fix it on {PRE_STAGING} and Promote again.')
            return 1
        p = _run(wt, 'push', '-q', 'origin', f'HEAD:refs/heads/{staging}')
        if p.returncode != 0:
            say(f'{staging} moved while the check ran, so nothing was pushed; '
                f'Promote again. ({p.stderr.strip()[:200]})')
            return 1
        new = _git(wt, 'rev-parse', 'HEAD')
    say(f'PROMOTED {len(batch)} commit(s) from {PRE_STAGING} into {staging} '
        f'({new[:12]}):\n  ' + '\n  '.join(batch))
    _mirror_legacy(root, staging, new, say)
    return 0


def _mirror_legacy(root, staging, new, say):
    """Fast-forward the pre-rename name to what staging now holds, while it
    exists. Never forced: the sync has already merged anything pushed there
    into pre-staging, so a legacy tip that is not an ancestor means someone
    pushed to it during this Promote, and it is said rather than overwritten."""
    if staging == LEGACY_STAGING:
        return
    ltip = _remote_tip(root, LEGACY_STAGING)
    if not ltip or ltip == new:
        return
    _run(root, 'fetch', '-q', 'origin', LEGACY_STAGING)
    if _run(root, 'merge-base', '--is-ancestor', ltip, new).returncode != 0:
        say(f'NOTE: {LEGACY_STAGING} has commits {staging} lacks, so it was not '
            f'moved; the next Promote brings them in through {PRE_STAGING}.')
        return
    p = _run(root, 'push', '-q', 'origin', f'{new}:refs/heads/{LEGACY_STAGING}')
    if p.returncode == 0:
        say(f'also moved {LEGACY_STAGING} to it, for installs still pinned to the old name.')
    else:
        say(f'NOTE: could not move {LEGACY_STAGING}: {p.stderr.strip()[:200]}')


# `git push` options that take the NEXT word as their value.
_VALUED = {'-o', '--push-option', '--repo', '--receive-pack', '--exec'}
# Options that push something no refspec names.
_UNREADABLE = {'--all', '--mirror', '--tags', '--follow-tags', '--branches'}


def _current_push_branch(root):
    """Where a bare `git push` (or a refspec of HEAD) sends the current
    branch: its push destination when one is configured, else its own
    name. None on a detached HEAD."""
    dest = _git(root, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{push}')
    if dest and '/' in dest:
        return dest.split('/', 1)[1]
    head = _git(root, 'symbolic-ref', '--short', '-q', 'HEAD')
    return head or None


def _dest_of(root, refspec):
    spec = refspec.lstrip('+')
    if ':' in spec:
        src, dst = spec.split(':', 1)
        if not dst:
            return None
    else:
        src = dst = spec
    if dst == 'HEAD' or (src == 'HEAD' and ':' not in spec):
        return _current_push_branch(root)
    if dst.startswith('refs/heads/'):
        return dst[len('refs/heads/'):]
    if dst.startswith('refs/'):
        return None
    return dst


def push_targets(root, args):
    """-> the branch names a `git push <args>` writes to, or None when that
    cannot be established. `args` is everything after `push`, as a list or
    as one shell-quoted string."""
    if isinstance(args, str):
        try:
            args = shlex.split(args)
        except ValueError:
            return None
    positional, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a in _UNREADABLE:
            return None
        if a in _VALUED:
            skip = True
            continue
        if a.startswith('-'):
            continue
        positional.append(a)
    refspecs = positional[1:]
    if not refspecs:
        branch = _current_push_branch(root)
        return [branch] if branch else None
    out = []
    for spec in refspecs:
        dest = _dest_of(root, spec)
        if dest is None:
            return None
        out.append(dest)
    return out


def tier_for_push(root, args, user_config=None):
    """-> (tier, why) for a `git push <args>`: the highest tier any branch
    it writes to needs."""
    targets = push_targets(root, args)
    if not targets:
        return FULL, ('where this push goes could not be read from its '
                      'arguments, so it is checked fully')
    tiers = [tier_for_branch(root, t, user_config) for t in targets]
    for tier, why in tiers:
        if tier == FULL:
            return FULL, why
    return BASIC, tiers[0][1]


def _main(argv):
    root = _git(pathlib.Path.cwd(), 'rev-parse', '--show-toplevel')
    if not root:
        print('precedent_branches: not inside a git checkout.', file=sys.stderr)
        return 2
    if argv[:1] == ['--tier'] and len(argv) == 2:
        tier, why = tier_for_branch(root, argv[1])
        print(tier)
        print(why, file=sys.stderr)
        return 0
    if argv[:1] == ['--push']:
        tier, why = tier_for_push(root, argv[1:])
        print(tier)
        print(why, file=sys.stderr)
        return 0
    if argv == ['--landing']:
        branch, why = landing_branch(root)
        print(branch)
        print(why, file=sys.stderr)
        return 0
    if argv == ['--sync-pre-staging']:
        return 0 if sync_pre_staging(root) else 1
    if argv == ['--promote']:
        return promote(root)
    tier, why = branch_push_checks(root)
    print(f'pre-staging  {PRE_STAGING}')
    print(f'staging      {staging_branch(root)}')
    print(f'main         {MAIN}')
    print(f'always checked fully: {", ".join(sorted(full_branches(root)))}')
    print(f'every other branch: {tier} ({why})')
    landing, lwhy = landing_branch(root)
    print(f'Go update lands on: {landing} ({lwhy})')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(_main(sys.argv[1:]))
