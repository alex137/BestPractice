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
  precedent_branches.py --ensure-tiers [--apply]
                                            report (or make) pre-staging and a real
                                            staging branch on origin -- the migration step
"""
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

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
# The repository's own staging tier -- the conventional route, a pull
# request into the branch work normally lands on -- for anyone who has not
# chosen otherwise. The tiered route (pre-staging, then Promote) is a
# person's opt-in, set as landing_branch "pre-staging" in their own
# identity.json. Morgan, 2026-09-26 (strength: decided): "This forced
# pre-staging -> staging -> main should be mandatory for me, but not
# necessarily anyone else. (We may change that in the future.)" It was
# PRE_STAGING for everyone from 2026-09-25 until then.
DEFAULT_LANDING = STAGING

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


# A repository's own staging branch, when it has one apart from base_branch.
# Written by --ensure-tiers into a repository whose base_branch is main, so it
# gains a real staging branch WITHOUT base_branch moving: base_branch also
# pins where a practice source's session clone sits, and that pin stays on
# main (spec/BRANCH_TIERS_PLAN.md, "Installs take their updates from main").
STAGING_KEY = 'staging_branch'


def staging_branch(root):
    """The staging tier's branch name in this repository, today."""
    explicit = precedent_json(root).get(STAGING_KEY)
    if isinstance(explicit, str) and explicit.strip() \
            and explicit.strip() != PRE_STAGING:
        return explicit.strip()
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
        # one's needs the person to name main in the request -- still
        # decides whether a session may push there.
        return MAIN, why
    return staging_branch(root), why


# PROMOTE ONLY -- a per-person setting, off unless that person turns it on
# (Morgan, 2026-09-25: "please make this an INDIVIDUAL rule for me, because I
# believe that Alex and others won't necessarily use this system"). With it
# on, staging and main take work only by promotion: the push gate refuses a
# `git push` that writes to either, and the merge gate refuses a pull request
# into either unless its head is the tier directly below. Promote itself
# pushes from inside this module, where no push gate sees it, so the one
# sanctioned route stays open.
#
# Why (2026-09-25, measured in a practice source that has no staging branch
# of its own): five changes reached its main in one day without passing
# through pre-staging -- sessions committing on the main checkout the
# session-start clone gives them, and a pull request opened against the
# default branch. Nothing refused any of it: the push check chose how hard
# to test by branch, and a push to main passed the full check.
PROMOTE_ONLY_SETTING = 'promote_only'


def promote_only(root, user_config=None):
    """-> (on, where). Only a literal `true` turns it on."""
    value, where = personal_setting(root, PROMOTE_ONLY_SETTING, user_config)
    return value is True, where


def _promotion_heads(root, base):
    """The branches allowed to be merged into `base` when promote_only is on:
    the tier directly below it."""
    if base == MAIN:
        return {staging_branch(root), STAGING, LEGACY_STAGING} - {MAIN}
    return {PRE_STAGING}


def direct_push_refusal(root, args, user_config=None):
    """-> None, or why a `git push <args>` is refused: promote_only is on
    and the push writes straight to staging or main. A push whose
    destination cannot be read is left to the full check, not refused."""
    on, where = promote_only(root, user_config)
    if not on:
        return None
    targets = push_targets(root, args)
    hit = sorted(set(targets or ()) & full_branches(root))
    if not hit:
        return None
    return (f'{" and ".join(hit)} take{"s" if len(hit) == 1 else ""} work only '
            f'by promotion here -- {PROMOTE_ONLY_SETTING} is on in {where}. '
            f'Push to {PRE_STAGING} instead (`git push origin HEAD:{PRE_STAGING}`), '
            f'then say Promote. A commit made on a local {hit[0]} checkout goes '
            f'the same way; move the checkout back with '
            f'`git reset --keep origin/{hit[0]}` once origin/{PRE_STAGING} has it.')


def merge_refusal(root, bases, heads, user_config=None):
    """-> None, or why merging a pull request is refused: promote_only is
    on, its base is staging or main, and its head is not the tier directly
    below. `bases` and `heads` are every branch at the base and head tips;
    when the base is ambiguous (two branches at one commit, one of them not
    protected) nothing is refused -- a wrong refusal of an ordinary pull
    request into pre-staging would be the common case right after Promote."""
    on, where = promote_only(root, user_config)
    if not on or not bases:
        return None
    protected = full_branches(root)
    if not all(b in protected for b in bases):
        return None
    allowed = set()
    for b in bases:
        allowed |= _promotion_heads(root, b)
    if set(heads or ()) & allowed:
        return None
    return (f'a pull request into {" or ".join(sorted(bases))} is merged only '
            f'from {" or ".join(sorted(allowed))} here -- {PROMOTE_ONLY_SETTING} '
            f'is on in {where}. Retarget it at {PRE_STAGING}, merge it there, '
            f'and say Promote.')


def tier_branches(root):
    """Every branch that is a tier here: main, staging (and its old name)
    and pre-staging. None of them may ever be the SOURCE of a pull request:
    A merged pull request's page offers to delete its source branch, and
    staging was deleted right after a merge of it into main on 2026-09-26,
    cause not established (see
    gotchas/gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging.md)."""
    return sorted({MAIN, PRE_STAGING, LEGACY_STAGING, STAGING,
                   staging_branch(root)})


def ensure_tiers(root, apply=False, say=print):
    """Make origin carry pre-staging and a real staging branch. -> 0 when
    both exist (or were just made), 1 when something is missing and
    `apply` is off, or could not be made.

    A repository whose staging tier is main (base_branch "main", no
    staging_branch) gains a `staging` branch at main's tip, and its
    precedent.json gains `"staging_branch": "staging"` -- written here,
    committed by the session running the migration. base_branch itself is
    left alone (see STAGING_KEY). Then pre-staging is made from staging by
    sync_pre_staging, the same way first use makes it everywhere else."""
    root = pathlib.Path(root)
    staging = staging_branch(root)
    missing = []
    wants_staging_branch = staging == MAIN
    if wants_staging_branch:
        missing.append(f'a separate {STAGING} branch (the staging tier is '
                       f'{MAIN} here)')
    elif not _remote_tip(root, staging):
        missing.append(f'{staging} on origin')
    if not _remote_tip(root, PRE_STAGING):
        missing.append(f'{PRE_STAGING} on origin')
    if not missing:
        say(f'tiers: {PRE_STAGING} -> {staging} -> {MAIN}, all present.')
        return 0
    if not apply:
        say('tiers: missing ' + '; '.join(missing) +
            ' -- run `python3 tools/precedent_branches.py --ensure-tiers --apply`.')
        return 1
    if wants_staging_branch or not _remote_tip(root, staging):
        # A staging branch that has gone missing is rebuilt from the old
        # name kept in step with it, else from main. 2026-09-26:
        # staging was deleted right after a pull request FROM staging into
        # main was merged (cause not established), and this looked for staging
        # itself to rebuild it from, found nothing and gave up. Right after
        # such a merge, main contains staging exactly.
        if wants_staging_branch:
            src = MAIN
        elif staging != LEGACY_STAGING and _remote_tip(root, LEGACY_STAGING):
            src = LEGACY_STAGING
        else:
            src = MAIN
        tip = _remote_tip(root, STAGING) or _remote_tip(root, src)
        if not tip:
            say(f'origin has no {src} branch, so there is nothing to base '
                f'{STAGING} on; nothing was changed.')
            return 1
        if not _remote_tip(root, STAGING):
            p = _run(root, 'push', '-q', 'origin', f'{tip}:refs/heads/{STAGING}')
            if p.returncode != 0:
                say(f'could not create {STAGING} on origin: {p.stderr.strip()[:300]}')
                return 1
            say(f'created {STAGING} on origin at {src} ({tip[:12]}).')
        if wants_staging_branch:
            path = root / 'precedent.json'
            data = _read_json(path) or {}
            data[STAGING_KEY] = STAGING
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
            say(f'wrote "{STAGING_KEY}": "{STAGING}" into precedent.json -- commit '
                f'it; {MAIN} now takes work from {STAGING} by pull request.')
    if not sync_pre_staging(root, say):
        return 1
    say(f'tiers: {PRE_STAGING} -> {staging_branch(root)} -> {MAIN}.')
    return 0


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


def _merge_env(root=None):
    """A merge commit this module makes must never carry `[skip ci]`
    (plan, hole 3): PRECEDENT_CI_NOW is the cadence hook's own override.

    It is also dated in the committing person's zone -- the repository's
    fallback only when no person's zone is declared -- never the
    container's (practice: timestamps-carry-offset). On 2026-09-25 a Promote in an
    individual source was refused by its own full check: the merge commit
    this module had just made carried the container's -0400, and that
    repository enforces its owner's declared zone on every commit. The zone
    comes from precedent_time.py's ladder, the one every other stamp uses;
    when that module is not beside this one, the environment is left as it
    is, as before."""
    env = dict(os.environ, PRECEDENT_CI_NOW='1')
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_time
        env['TZ'] = precedent_time.resolved(root)[1]
    except Exception:
        pass
    finally:
        sys.path.pop(0)
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
                     f'Merge {branch} into {PRE_STAGING}', tip, env=_merge_env(root))
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


# THE PROMOTE LOCK. Two windows promoting at once race: both run the full
# check, one push wins, and the other run was minutes thrown away (seen twice
# in a row on 2026-09-25). So a Promote first claims a lock on origin, and a
# second one that finds it held stops before doing anything.
#
# The lock is a BRANCH, because a web session's git proxy refuses a push to
# any ref outside refs/heads/ (gotchas/gotcha-2026-09-25-a-session-cannot-
# push-a-ref-outside-refs-heads.md), and it can never be deleted, for the
# same reason (practice: never-delete-a-remote-branch). So it is never
# created and removed: it only ever moves FORWARD, one empty commit per
# claim or release, and its newest commit's subject says its state --
# "held by ..." or "free". A plain (never forced) push is the compare-and-
# swap: if another window moved it first, the push is not a fast-forward
# and is refused, so two windows cannot both hold it. Each commit carries
# [skip ci], so a workflow that runs on every branch push spends nothing.
#
# A holder that dies leaves it held; after LOCK_STALE_SECONDS anyone may
# claim it on top. Morgan, 2026-09-25: "yes to the lock branch, very much
# approved and supported" (strength: decided).
LOCK_BRANCH = 'precedent-promote-lock'
LOCK_STALE_SECONDS = 45 * 60
_EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


def _lock_holder_name():
    """Who a claim names: whatever the environment says this session is
    called, else host and process -- enough to tell two windows apart."""
    import socket
    return (os.environ.get('PRECEDENT_SESSION_NAME')
            or f'{socket.gethostname()} pid {os.getpid()}')


def _lock_state(root):
    """-> (tip, subject, committed_at) of the lock branch on origin, or
    (None, None, None) when it does not exist yet."""
    tip = _remote_tip(root, LOCK_BRANCH)
    if not tip:
        return None, None, None
    _run(root, 'fetch', '-q', 'origin', LOCK_BRANCH)
    subject = _git(root, 'log', '-1', '--format=%s', tip) or ''
    stamp = _git(root, 'log', '-1', '--format=%ct', tip) or '0'
    return tip, subject, int(stamp) if stamp.isdigit() else 0


def _lock_push(root, parent, subject, body):
    """Commit `subject` on top of `parent` and push it to the lock branch.
    -> (ok, commit, stderr). Never forced."""
    args = ['commit-tree', _EMPTY_TREE, '-m', f'{subject} [skip ci]', '-m', body]
    if parent:
        args += ['-p', parent]
    made = _run(root, *args, env=_merge_env(root))
    commit = made.stdout.strip()
    if made.returncode != 0 or not commit:
        return False, None, made.stderr.strip()
    p = _run(root, 'push', '-q', 'origin', f'{commit}:refs/heads/{LOCK_BRANCH}')
    return p.returncode == 0, commit, p.stderr.strip()


def _lock_claim(root, say):
    """-> ('held', commit) when this window now holds the lock; ('busy',
    reason) when another does; ('none', reason) when the lock could not be
    used at all, and the Promote goes ahead without it, as before."""
    tip, subject, at = _lock_state(root)
    age = time.time() - at if at else None
    if tip and subject.startswith('held by') and age is not None \
            and age < LOCK_STALE_SECONDS:
        return 'busy', f'{subject.replace(" [skip ci]", "")}, {int(age // 60)} min ago'
    stale = ' (taking over a claim older than %d min)' % (LOCK_STALE_SECONDS // 60) \
        if tip and subject.startswith('held by') else ''
    ok, commit, err = _lock_push(
        root, tip, f'held by {_lock_holder_name()}',
        'A Promote is running. tools/precedent_branches.py releases this when '
        f'it ends; a claim older than {LOCK_STALE_SECONDS // 60} minutes may be '
        f'taken over.{stale}')
    if ok:
        return 'held', commit
    if any(w in err for w in ('non-fast-forward', 'fetch first', 'rejected')):
        tip, subject, at = _lock_state(root)
        who = subject.replace(' [skip ci]', '') if subject else 'another window'
        return 'busy', f'{who}, just now'
    return 'none', err[:200] or 'the lock commit could not be made'


def _lock_release(root, held, say):
    ok, _commit, err = _lock_push(root, held, 'free', 'No Promote is running.')
    if not ok:
        say(f'NOTE: could not release {LOCK_BRANCH} ({err[:160]}); it frees '
            f'itself after {LOCK_STALE_SECONDS // 60} minutes.')


def promote(root, say=print):
    """Pre-staging into staging, fully checked, one window at a time. -> 0
    promoted, nothing to promote, or another window already promoting; 1
    refused (a failing check, a conflict, a race)."""
    state, info = _lock_claim(root, say)
    if state == 'busy':
        say(f'another window is promoting right now ({info}), so this one did '
            f'nothing. It carries what was on {PRE_STAGING} when it started; '
            f'anything pushed there since goes in the next Promote. Do not '
            f'Promote again while it runs.')
        return 0
    if state == 'none':
        say(f'NOTE: could not take the Promote lock ({info}); going ahead '
            f'without it.')
        return _promote_unlocked(root, say)
    try:
        return _promote_unlocked(root, say)
    finally:
        _lock_release(root, info, say)


def _promote_unlocked(root, say=print):
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
                 ptip, env=_merge_env(root))
        if m.returncode != 0:
            _run(wt, 'merge', '--abort')
            say(f'{PRE_STAGING} does not merge cleanly into {staging}; nothing was pushed.')
            return 1
        say(f'checking {len(batch)} commit(s) from {PRE_STAGING} with the full push check...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, FULL)
        took = time.monotonic() - t0
        if not ok:
            say(f'PROMOTE REFUSED: the full check failed, so {staging} did not move. '
                f'The batch was:\n  ' + '\n  '.join(batch) + f'\n\n{out}\n\n'
                f'Fix it on {PRE_STAGING} and Promote again.')
            return 1
        p = _run(wt, 'push', '-q', 'origin', f'HEAD:refs/heads/{staging}')
        if p.returncode != 0:
            # Most often another window promoted the same batch while this
            # one was checking it. Then there is nothing left to do, and
            # "Promote again" would only send the person round a second
            # time for work already on staging (2026-09-25: two sessions
            # raced this way twice in a row, each told to try again).
            now = _remote_tip(root, staging)
            if now:
                _run(root, 'fetch', '-q', 'origin', staging)
            if now and _run(root, 'merge-base', '--is-ancestor', ptip,
                            now).returncode == 0:
                say(f'another window promoted this batch while the check ran: '
                    f'{staging} ({now[:12]}) already has everything that was on '
                    f'{PRE_STAGING}. Nothing was pushed, and there is nothing '
                    f'left to promote.')
                return 0
            say(f'{staging} moved while the check ran, so nothing was pushed; '
                f'Promote again. ({p.stderr.strip()[:200]})')
            return 1
        new = _git(wt, 'rev-parse', 'HEAD')
    # Say which it was. A reused pass and a fresh run end the same way, and a
    # person who cannot tell them apart assumes the suite ran twice.
    reused = next((l for l in out.splitlines() if 'already passed' in l), None)
    if reused:
        say('the full check was NOT re-run: ' + reused.split(': ', 1)[-1]
            + ' Same files, so the earlier run stands.')
    else:
        say(f'the full check ran on the batch and passed, in {took:.0f}s.')
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
    if argv[:1] == ['--ensure-tiers'] and set(argv[1:]) <= {'--apply'}:
        return ensure_tiers(root, apply='--apply' in argv)
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
