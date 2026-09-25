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
repository whose base_branch is `main` has no separate staging branch yet,
so its staging tier is simply called `staging`, and its main is checked
fully either way.

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

CLI:
  precedent_branches.py                     the tiers, as this repo resolves them
  precedent_branches.py --tier BRANCH       prints `basic` or `full`
  precedent_branches.py --push ARGS...      the tier a `git push ARGS...` gets
"""
import json
import os
import pathlib
import shlex
import subprocess
import sys

PRE_STAGING = 'pre-staging'
STAGING = 'staging'
MAIN = 'main'
BASIC = 'basic'
FULL = 'full'
TIERS = (BASIC, FULL)

SETTING = 'branch_push_checks'
DEFAULT_TIER = BASIC

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
    if declared and declared not in (MAIN, PRE_STAGING):
        return declared
    return STAGING


def full_branches(root):
    """Every branch a push to is always fully checked."""
    names = {MAIN, STAGING, staging_branch(root)}
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


def _git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


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
    tier, why = branch_push_checks(root)
    print(f'pre-staging  {PRE_STAGING}')
    print(f'staging      {staging_branch(root)}')
    print(f'main         {MAIN}')
    print(f'always checked fully: {", ".join(sorted(full_branches(root)))}')
    print(f'every other branch: {tier} ({why})')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(_main(sys.argv[1:]))
