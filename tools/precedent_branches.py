#!/usr/bin/env python3
"""Where a person's work lands here (spec/LADDER_OPT_IN_PLAN.md D3) and whether a push to a branch gets the basic or the full push check; the branch tiers and their moves for a person whose set provides them (spec/BRANCH_TIERS_PLAN.md)

precedent_branches.py -- the three branch tiers, and what a push to each
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

WHERE `Go update` LANDS is `landing_branch`: `pre-staging`, `staging` or
`main`. Read in the OTHER order from `branch_push_checks`: the person's own
identity.json first, then the repository's precedent.json, then the built-in
default, `staging` (Morgan, 2026-09-27, strength: decided: "have the
individual repo take precedence over the others (if it set, use that)").
Where a person works is theirs to choose; a repository's value is its
default for everyone who has not. New repositories are written with
`pre-staging` (precedent_install.py, the document-project template, a new
practice set), and Update Vendors adds it to one that has none. An
unreadable value lands on staging, where work landed before the tiers
existed, never somewhere new.

PROMOTE moves pre-staging into staging (plan step 6; Morgan named the
command, strength: assented). Since 2026-10-03 it COMPOSES one tree in a
throwaway worktree -- staging, then any fix branch it is handed (--work
claude/DATE-promote-fix-ID), then work made directly on main, then pre-staging -- each
by a merge commit, never a fast-forward, so a `[skip ci]` line on a
pre-staging commit can never become staging's head and silence the GitHub
test on the pull request into main (plan, hole 3). It rebuilds the
generated files main's work left stale, runs the FULL push check on that
tree once, and only if it passes moves staging AND pre-staging to that same
commit in one atomic push. A failure or a conflict in hand-written text
moves neither: the tree goes to a local claude/DATE-promote-fix-ID branch
(named like every temporary branch since 2026-10-06; promote-fix-DATE
before, still recognized), to be fixed
there and promoted with --work (spec/LADDER_OPT_IN_PLAN.md D10; see the
comment above _promote_unlocked). It pushes by itself, so it runs the check
by itself: no push gate sees a push made from inside a script.

PROMOTE ALSO MOVES STAGING INTO MAIN, since 2026-09-26, and picks which of
the two steps to run (promotion_step): the one the session names with --to,
else pre-staging first whenever it has work waiting -- including when the
work the session was just on (--work) waits on staging for main, since both
steps waiting makes the Promote ambiguous -- else the one --work needs. It prints "Now promoting from X to Y" before
anything else. Into main it runs the same full check on staging merged into
main, then pushes a throwaway copy of staging for the pull request into
main; that pull request's GitHub test is main's last gate, so main itself
is never pushed from here. That state exits 3 (PROMOTE_MAIN_NOT_MOVED), not
0, and says first that main has not moved: exit 0 means the branch moved.

IN A PRIVATE REPOSITORY THAT GITHUB TEST RUNS AT MOST ONCE EVERY
github_ci_every_hours (2026-10-01, spec/CI_CADENCE_PLAN.md, "Promote
decides"; see main_test_due). When it is not due, the copy is named
claude/DATE-promote-to-main-not-due-ID (to-main-not-due-DATE before
2026-10-06, and still where a GitHub test knows only that), the light check's job skips that pull request before
a runner starts, and --wait-main-test says NOT DUE and exits 0.

CLI:
  precedent_branches.py                     the tiers, as this repo resolves them
  precedent_branches.py --tier BRANCH       prints `basic` or `full`
  precedent_branches.py --push ARGS...      the tier a `git push ARGS...` gets
  precedent_branches.py --landing           where `Go update` lands for this person
  precedent_branches.py --sync-pre-staging [--check]
                                            create pre-staging, or copy into it what
                                            reached staging another way -- what has
                                            had its tier's checks, or with --check,
                                            whatever passes them once run (main's
                                            comes down only in a Promote)
  precedent_branches.py --wait-main-test COPY
                                            wait for main's GitHub test on the to-main
                                            copy's pull request; 0 only when it passed,
                                            or when the copy is a not-due one
  precedent_branches.py --drift             what staging and main carry that pre-staging
                                            lacks, checked or not (the session-start note)
  precedent_branches.py --promote [--to staging|main] [--work BRANCH]
                                            pre-staging into staging, or staging into
                                            main, fully checked; says which first.
                                            0 moved or nothing to move, 1 refused,
                                            3 main not moved yet (its pull request
                                            is still to open, test and merge)
  precedent_branches.py --ensure-tiers [--apply]
                                            report (or make) pre-staging and a real
                                            staging branch on origin -- the migration step
"""
import calendar
import json
import os
import pathlib
import re
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
# PRE_STAGING for everyone from 2026-09-25 until then. Since 2026-09-27 a
# repository carries its own default (pre-staging, written at install and
# by Update Vendors), below the person and above this one: Morgan, "have
# the Precedent one default to staging".
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


# What a repository says when it has not been told otherwise: pre-staging,
# the tiered route. Written into precedent.json at install, into a new
# practice set, and by Update Vendors into a repository that has no value of
# its own (Morgan, 2026-09-27, strength: decided). It sits BELOW the person
# (landing_branch() reads identity.json first), so it is a default, never an
# override of somebody's own choice.
REPO_LANDING_DEFAULT = PRE_STAGING
REPO_LANDING_COMMENT = [
    'Where Go update lands for anyone whose own identity.json names no',
    'landing_branch -- a person\'s own setting always wins. pre-staging is',
    'the tiered route: work reaches staging and main only by a Promote.',
    'Change it here for this repository.',
]


def ensure_repo_landing(root, new_install=False):
    """Give precedent.json a `landing_branch` when it has none. -> True when
    it wrote one. Never changes a value that is there, and never creates the
    file: a repository without a precedent.json is not an install.

    Only for a person on the ladder, and only where the repository asks for
    tiers -- a fresh install by that person, or a repository that already
    has them (spec/LADDER_OPT_IN_PLAN.md D3: nothing creates tiers in a
    repository that did not ask for them)."""
    path = pathlib.Path(root) / 'precedent.json'
    data = _read_json(path)
    if not isinstance(data, dict) or LANDING_SETTING in data:
        return False
    # Tiers are written only by a person on the ladder (D3): anyone else
    # installing or updating leaves the repository on its main branch alone.
    ladder = ladder_in_force(root)
    if ladder is False or (ladder and not new_install
                           and not repo_has_tiers(root)):
        return False
    # Appended as text before the closing brace, so the rest of a
    # hand-kept file -- its order, its escapes, its comments' wrapping --
    # comes back byte for byte. A file that does not end in `}` is
    # rewritten whole instead, which is still valid, only noisier.
    text = path.read_text(encoding='utf-8')
    body = text.rstrip()
    added = (f',\n  "{LANDING_SETTING}": {json.dumps(REPO_LANDING_DEFAULT)},\n'
             f'  "_{LANDING_SETTING}_comment": [\n'
             + ',\n'.join('    ' + json.dumps(line) for line in REPO_LANDING_COMMENT)
             + '\n  ]\n}\n')
    candidate = body[:-1].rstrip() + added if body.endswith('}') else None
    try:
        if candidate is None or json.loads(candidate).get(LANDING_SETTING) \
                != REPO_LANDING_DEFAULT:
            raise ValueError
    except ValueError:
        data[LANDING_SETTING] = REPO_LANDING_DEFAULT
        data['_' + LANDING_SETTING + '_comment'] = REPO_LANDING_COMMENT
        candidate = json.dumps(data, indent=2) + '\n'
    path.write_text(candidate, encoding='utf-8')
    return True


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


def person_first_setting(root, key, user_config=None):
    """-> (value, where), the person's identity.json first and the
    repository's precedent.json second -- the reverse of personal_setting,
    for a choice that is the person's to make wherever they work."""
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email') and key in ident:
            return ident[key], str(path)
    repo = precedent_json(root)
    if key in repo:
        return repo[key], "this repo's precedent.json"
    return None, None


def ladder_in_force(root, user_config=None):
    """-> True or False from tools/precedent_ladder.py, or None when that
    helper is not beside this file (an engine older than it): the caller
    then keeps the behaviour from before the ladder became opt-in. Imported
    here, not at the top, because this module must import cleanly with
    nothing else vendored beside it."""
    try:
        here = str(pathlib.Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import precedent_ladder
    except Exception:                                       # noqa: BLE001
        return None
    try:
        return bool(precedent_ladder.ladder_in_force(root, user_config))
    except Exception:                                       # noqa: BLE001
        return None


def repo_has_tiers(root):
    """True when this repository has tiers: precedent.json names a tier as
    its landing_branch or base_branch, or a staging_branch of its own, or
    origin already carries pre-staging. A repository with none of these has
    only its main branch, and nothing here gives it more."""
    data = precedent_json(root)
    if data.get(LANDING_SETTING) in (PRE_STAGING, STAGING):
        return True
    if base_branch(root) in (PRE_STAGING, STAGING, LEGACY_STAGING):
        return True
    explicit = data.get(STAGING_KEY)
    if isinstance(explicit, str) and explicit.strip():
        return True
    try:
        r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify',
                            '-q', f'refs/remotes/origin/{PRE_STAGING}'],
                           capture_output=True, text=True)
        return r.returncode == 0
    except OSError:
        return False


def landing_branch(root, user_config=None):
    """-> (branch, why): where this person's work lands
    (spec/LADDER_OPT_IN_PLAN.md D3, Morgan 2026-10-02, strength: decided).

    1. The person's own landing_branch, else the repository's main branch.
    2. A tier value -- pre-staging or staging, the person's or the
       repository's -- counts only while the ladder is in force for this
       person AND the repository declares tiers. Otherwise it is ignored and
       never edited: a person off the ladder has no tiers, and a ladder user
       never creates them in a repository that did not ask for them.
    3. On the ladder, in a repository with tiers: the person, then the
       repository, then pre-staging.

    With no tools/precedent_ladder.py beside this file, the order from before
    the ladder became opt-in: the person, the repository, DEFAULT_LANDING."""
    ladder = ladder_in_force(root, user_config)
    if ladder is not None:
        return _landing_by_ladder(root, ladder, user_config)
    value, where = person_first_setting(root, LANDING_SETTING, user_config)
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


def _landing_by_ladder(root, ladder, user_config=None):
    """landing_branch's rule once the ladder can be asked about."""
    person, where = None, None
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email') and LANDING_SETTING in ident:
            person, where = ident[LANDING_SETTING], str(path)
            break
    repo = precedent_json(root).get(LANDING_SETTING)
    tiers = bool(ladder) and repo_has_tiers(root)
    if person is not None and person not in (PRE_STAGING, STAGING, MAIN):
        person = None                     # a typo: as if it were not set
    if person == MAIN:
        return MAIN, f'{LANDING_SETTING} is "main" in {where}'
    if person in (PRE_STAGING, STAGING):
        if tiers:
            return (PRE_STAGING if person == PRE_STAGING else staging_branch(root),
                    f'{LANDING_SETTING} is "{person}" in {where}')
        return MAIN, (f'{LANDING_SETTING} is "{person}" in {where}, a branch '
                      f'this repository does not use for you, so work lands '
                      f'on {MAIN}')
    if tiers:
        if repo == STAGING:
            return staging_branch(root), (f'{LANDING_SETTING} is "staging" in '
                                          f"this repo's precedent.json")
        return PRE_STAGING, (f'{LANDING_SETTING} is "pre-staging" in this '
                             f"repo's precedent.json")
    return MAIN, f'work lands on {MAIN} here'


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
    """-> (on, where). Only a literal `true` turns it on, and only while the
    ladder is in force for this person (spec/LADDER_OPT_IN_PLAN.md D3.4):
    off the ladder, and in a session started with PRECEDENT_NO_LADDERS, the
    setting is ignored, never edited."""
    value, where = personal_setting(root, PROMOTE_ONLY_SETTING, user_config)
    if value is True:
        ladder = ladder_in_force(root, user_config)
        # Off the ladder, or in a repository with no tiers to promote
        # through, main is where work lands -- refusing pushes there would
        # leave the person nowhere to put it.
        if ladder is False or (ladder and not repo_has_tiers(root)):
            return False, where
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
    stale = sorted(h for h in heads or () if is_main_copy(h))
    if MAIN in bases and stale:
        return (f'{stale[0]} is a copy of {staging_branch(root)} that is out of '
                f'date: {staging_branch(root)} has moved since it was made. '
                f'Close this pull request, promote {staging_branch(root)} into '
                f'{MAIN} again for a fresh copy, and open the pull request '
                f'from that. Never retarget it.')
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


def ensure_tiers(root, apply=False, say=print, new_install=False):
    """Make origin carry pre-staging and a real staging branch. -> 0 when
    both exist (or were just made), 1 when something is missing and
    `apply` is off, or could not be made.

    A missing staging is made from the old name kept in step with it, else
    from pre-staging, else from main; a missing pre-staging is made from
    staging. A repository whose staging tier is main (base_branch "main", no
    staging_branch) gains a `staging` branch the same way, and its
    precedent.json gains `"staging_branch": "staging"` -- written here,
    committed by the session running the migration. base_branch itself is
    left alone (see STAGING_KEY). Then pre-staging is made from staging by
    sync_pre_staging, the same way first use makes it everywhere else."""
    root = pathlib.Path(root)
    # Only a person on the ladder makes tiers (spec/LADDER_OPT_IN_PLAN.md D3):
    # for anyone else a repository has its main branch and nothing to make,
    # and saying so would be the ladder's words in their session.
    ladder = ladder_in_force(root)
    if ladder is False or (ladder and not new_install
                           and not repo_has_tiers(root)):
        return 0
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
        #
        # Then from pre-staging, and only then from main (Morgan,
        # 2026-09-27, strength: decided: "copying the latest from
        # pre-staging to staging or vice versa and if neither exist then
        # copying to both the latest from main"). What lands on staging this
        # way has not had staging's full check, and it gets it on the way to
        # main: a Promote into main runs the full check on anything it has
        # not seen pass.
        if (not wants_staging_branch and staging != LEGACY_STAGING
                and _remote_tip(root, LEGACY_STAGING)):
            src = LEGACY_STAGING
        elif _remote_tip(root, PRE_STAGING):
            src = PRE_STAGING
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


class CommitRefused(Exception):
    """A commit this module was about to make has nobody to author it, in a
    repository that enforces who does (precedent_identity.IdentityRequired).
    Nothing is committed or pushed; _main says so and exits 1."""


def _merge_env(root=None):
    """The environment every commit this module makes runs under.

    A merge commit this module makes must never carry `[skip ci]` (plan,
    hole 3): PRECEDENT_CI_NOW is the cadence hook's own override.

    It is also AUTHORED by the declared person and dated in their zone,
    stated on the command itself through precedent_identity.commit_env()
    -- never left to whatever `git config` and TZ this session happens to
    hold. Two incidents, one cause. On 2026-09-25 a Promote's merge carried
    the container's -0400 and was refused by the individual source's own
    full check, which is when TZ got set here. On 2026-09-26 a session
    rooted above four attached practice sets, so that no SessionStart hook
    had configured any of them, ran Promote in all four: every merge and
    lock commit came out authored by the container's bot, because TZ was
    set here and the author was not. `git merge` and `git commit-tree` run
    no `pre-commit` hook, so the global backstop never saw them (practice:
    upstream-fix).

    Where the repository is somebody's individual source and no author
    resolves, CommitRefused is raised instead of committing as the bot.
    When precedent_identity is not beside this module (an engine older than
    the helper), the zone alone is set, as before."""
    env = dict(os.environ, PRECEDENT_CI_NOW='1')
    repo = pathlib.Path(root or os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())
    here = str(pathlib.Path(__file__).resolve().parent)
    sys.path.insert(0, here)
    try:
        try:
            import precedent_identity
        except ImportError:
            precedent_identity = None
        if precedent_identity is not None:
            try:
                return precedent_identity.commit_env(repo, env)
            except precedent_identity.IdentityRequired as exc:
                raise CommitRefused(str(exc)) from exc
        try:
            import precedent_time
            env['TZ'] = precedent_time.resolved(repo)[1]
        except Exception:
            pass
        return env
    finally:
        if sys.path and sys.path[0] == here:
            sys.path.pop(0)


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


def _check(root, wt, tier, dest=None):
    """-> (ok, output): the repo's own push check at `tier` in worktree
    `wt`, reusing a pass the checkout already recorded for the same tree.
    `dest` is the branch the result is pushed to: the views check holds a
    set's commits to that same rung."""
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
    p = subprocess.run([sys.executable, tool, '--gate', '--tier', tier]
                       + (['--destination', dest] if dest else []),
                       cwd=wt, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).rstrip()


# DRIFT FROM ABOVE (spec/BRANCH_TIERS_PLAN.md, holes 2, 4 and 5). Work is
# meant to climb the tiers: pre-staging, then staging by Promote, then main
# by the pull request from staging. Some of it arrives from above instead --
# a direct push to staging, a workflow's bot commit on main, an edit made
# on GitHub's website -- and none of that passed through pre-staging, so
# the windows syncing from there never see it, and the next pull request
# into main meets it as a conflict. The sync copies it DOWN into
# pre-staging, and only once the tier it sits on has had its own checks:
# staging's full local check, and on main that plus the GitHub test.
#
# Morgan, 2026-09-26 (strength: decided): "a good point to check to make
# sure anything that got onto main not through our system [...] had those
# checks and if not we should do it, including the GitHub CI/CD for main,
# and also for staging, if it got there through a different route, to make
# sure it has our staging ones". And on the copy itself, to "whenever the
# robot adds something to main, copy it back down to the lower branches":
# "I love it."
#
# ONLY A FILE CHANGE COUNTS. Right after an ordinary staging-to-main pull
# request, main is ahead of pre-staging by two merge commits -- the Promote
# merge and the pull request's -- whose files pre-staging already has
# (measured 2026-09-26 in two repositories). The test is whether merging the
# upper branch in would change a file, not whether the two trees are equal:
# a plain diff of the tips calls main "different" whenever staging has moved
# on past it, which on that day was true in this repository too. Morgan, on
# leaving those merges alone: "yes add that".

# The GitHub test is awaited this long before the sync gives up and says
# so. A run that is still queued after it is not failed, only not answered.
GITHUB_TEST_WAIT_SECONDS = 30 * 60
GITHUB_POLL_SECONDS = 45
# A pull request's run shows up on GitHub within a minute or two of the
# pull request opening. One that has not appeared by this long is never
# going to, and waiting the full half hour for it would only hide that.
GITHUB_START_WAIT_SECONDS = 5 * 60


def _tree(root, rev):
    return _git(root, 'rev-parse', f'{rev}^{{tree}}')


def _brings_nothing(root, lower, upper):
    """True when merging `upper` into `lower` would change no file: `upper`
    is already in it, or is ahead only by merges of files it already has."""
    if _run(root, 'merge-base', '--is-ancestor', upper, lower).returncode == 0:
        return True
    p = _run(root, 'merge-tree', '--write-tree', lower, upper)
    if p.returncode == 0 and p.stdout.split():
        return p.stdout.split()[0] == _tree(root, lower)
    if p.returncode == 1:
        return False            # it conflicts, so it plainly brings something
    # git before 2.38 has no --write-tree: upper's own changes since the two
    # parted, which misses only a change both sides made identically.
    return _run(root, 'diff', '--quiet', f'{lower}...{upper}').returncode == 0


def drift(root, lower, upper):
    """-> the commits on `upper` that bring `lower` a file change, one line
    each; [] when a merge would change nothing. Merge commits are left out
    of the list unless nothing else explains the change."""
    if _brings_nothing(root, lower, upper):
        return []
    return _new_commits(root, lower, upper) or (
        _git(root, 'log', '--oneline', f'{lower}..{upper}') or '').splitlines()


def _sibling(name):
    """Import an engine module that sits beside this one, or None."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        return __import__(name)
    except Exception:
        return None
    finally:
        sys.path.pop(0)


def _receipt(root, sha):
    """-> the full-check receipt published for `sha`'s exact tree, or None.
    precedent_push_check.py publishes one on the receipt branch for every
    tree that passes; none means the commit went round the checks, or its
    receipt aged out (the newest RECEIPTS_KEPT are kept). Both are
    unchecked."""
    ppc = _sibling('precedent_push_check')
    if ppc is None:
        return None
    try:
        home = pathlib.Path(root).resolve()
        _kind, checks = ppc.plan(home, tier=FULL)
        if not checks:
            return None
        return ppc.shared_pass(home, _tree(root, sha), [ppc.signature(checks)])
    except Exception:
        return None


def _slug(root):
    url = _git(root, 'config', '--get', 'remote.origin.url') or ''
    m = re.search(r'github\.com[:/]+([^/]+)/(.+?)(?:\.git)?/?$', url)
    return f'{m.group(1)}/{m.group(2)}' if m else None


def _trigger_list(block, key):
    """-> the list under `key:` in a trigger's block, inline (`[a, b]`) or
    one `- item` per line, quotes stripped; None when the key is absent."""
    m = re.search(rf'^([ \t]*){re.escape(key)}:[ \t]*(.*)\n((?:\1[ \t]+.*\n|[ \t]*#.*\n|\n)*)',
                  block if block.endswith('\n') else block + '\n', re.M)
    if not m:
        return None
    inline = m.group(2).split('#', 1)[0].strip()
    if inline.startswith('['):
        items = inline.strip('[]').split(',')
    elif inline:
        items = [inline]
    else:
        items = [l.strip()[1:] for l in m.group(3).splitlines()
                 if l.strip().startswith('-')]
    return [i.split(' #', 1)[0].strip().strip('"\'') for i in items
            if i.strip().strip('"\'')]


def _glob_re(pattern):
    """GitHub's path filter pattern as a regex: `*` stays inside one
    directory, `**` crosses them, `?` is one character."""
    out, i = '', 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith('**/', i):     # any directories, or none
            out, i = out + '(?:.*/)?', i + 3
            continue
        if pattern.startswith('**', i):
            out, i = out + '.*', i + 2
            continue
        out += {'*': '[^/]*', '?': '[^/]'}.get(c, re.escape(c))
        i += 1
    return re.compile(out + r'\Z')


def _path_filter_runs(paths, ignore, changed):
    """-> does a pull_request trigger with these `paths:` / `paths-ignore:`
    lists run for a diff touching `changed`? GitHub's rules: with `paths`,
    a file counts when the LAST pattern it matches is not a `!` one, and
    one counting file runs it; with `paths-ignore`, it runs unless every
    file is ignored."""
    if paths is not None:
        def counts(f):
            hit = False
            for pat in paths:
                neg = pat.startswith('!')
                if _glob_re(pat[1:] if neg else pat).match(f):
                    hit = not neg
            return hit
        return any(counts(f) for f in changed)
    if ignore is not None:
        return not all(any(_glob_re(p).match(f) for p in ignore) for f in changed)
    return True


def _changed_into_main(root, sha):
    """-> the paths a pull request of `sha` into main changes (from where
    they parted), or None when that cannot be read."""
    base = _remote_tip(root, MAIN) or _git(root, 'rev-parse', '--verify', '-q', MAIN)
    if not base:
        return None
    r = _run(root, 'diff', '--name-only', f'{base}...{sha}')
    if r.returncode != 0:
        return None
    return [l for l in r.stdout.splitlines() if l.strip()]


def github_tests(root, sha):
    """-> [(path, dispatchable)] for each workflow in `sha`'s tree that runs
    on a pull request of `sha` into main: main's GitHub test. [] when the
    repository has none installed (github_ci_workflows disabled, or no
    workflows).

    Read off the tree rather than a list, as precedent_ci_verified.py reads
    them, and blind the same way to glob branch patterns. A commented-out
    trigger never counts: the keys are anchored to the start of a line.

    A `paths:` or `paths-ignore:` filter is honoured: a workflow the pull
    request's own diff does not reach is not one GitHub runs, so it is not
    required. 2026-10-04: a consumer's Produce touched neither path of its
    docs check, GitHub rightly never ran it, and the wait said "never ran
    on it. Do not merge" for good. When the diff cannot be read, the
    workflow is required, as before."""
    out = []
    changed = False   # read once, and only for a workflow with a path filter
    names = _git(root, 'ls-tree', '--name-only', f'{sha}:.github/workflows') or ''
    for name in names.splitlines():
        if not name.endswith(('.yml', '.yaml')):
            continue
        path = f'.github/workflows/{name}'
        text = _git(root, 'show', f'{sha}:{path}') or ''
        on = re.search(r'^on:[ \t]*(.*)\n((?:[ \t]+.*\n|[ \t]*#.*\n|\n)*)', text + '\n', re.M)
        if not on:
            continue
        inline, body = on.group(1), on.group(2)
        pr = re.search(r'^([ \t]+)pull_request:[ \t]*\n((?:\1[ \t]+.*\n|[ \t]*#.*\n|\n)*)',
                       body, re.M)
        if pr:
            branches = _trigger_list(pr.group(2), 'branches')
            wanted = branches is None or MAIN in branches
            paths = _trigger_list(pr.group(2), 'paths')
            ignore = _trigger_list(pr.group(2), 'paths-ignore')
            if wanted and (paths is not None or ignore is not None):
                if changed is False:
                    changed = _changed_into_main(root, sha)
                if changed is not None:
                    wanted = _path_filter_runs(paths, ignore, changed)
        else:
            wanted = 'pull_request' in inline
        if wanted:
            out.append((path, bool(re.search(r'^[ \t]+workflow_dispatch:', body, re.M))
                        or 'workflow_dispatch' in inline))
    return out


def _runs_on(gh, slug, sha):
    data, err = gh.call(f'repos/{slug}/actions/runs?head_sha={sha}&per_page=100',
                        cache=False)
    if err or not isinstance(data, dict):
        return None, err or 'GitHub gave an answer this could not read'
    return data.get('workflow_runs') or [], None


_CURRENT_SLUG = {}


def _current_slug(gh, slug):
    """-> (the repository's current owner/name per GitHub, None) or (None,
    why). One call per slug per process: a wait asks this on every poll."""
    if slug not in _CURRENT_SLUG:
        data, err = gh.call(f'repos/{slug}', cache=False)
        name = data.get('full_name') if isinstance(data, dict) else None
        _CURRENT_SLUG[slug] = (name, None) if name else (
            None, err or 'its answer named no repository')
    return _CURRENT_SLUG[slug]


def github_test_state(root, sha, tests, gh=None, via_pulls=True,
                      _slug_override=None, _renamed_from=None):
    """-> (state, detail): did main's GitHub test run on `sha` and pass?

    A run counts from either of two places: on the commit itself (a workflow
    with a push trigger, or a button press, tests a bot commit on its own),
    or on the head of the pull request that brought the commit in (a
    pull-request run tests the pull request -- the head merged into main --
    which is what the ordinary route checks, and not always the final
    commit's exact tree). The newest run per workflow decides.

    state is one of 'passed', 'failed', 'running', 'none' (never ran) and
    'unknown' (GitHub could not be asked). Two or three API calls, counted
    by github_budget.py (practice: github-api-budget); one with
    `via_pulls` off, which is how a run started on the commit is awaited."""
    gh = gh or _sibling('github_budget')
    slug = _slug_override or _slug(root)
    if gh is None or not slug:
        return 'unknown', ('no github.com origin could be read here'
                           if not slug else 'github_budget.py is not beside this file')
    runs, err = _runs_on(gh, slug, sha)
    if runs is None:
        return 'unknown', err
    pulls = gh.call(f'repos/{slug}/commits/{sha}/pulls', cache=False)[0] \
        if via_pulls else []
    heads = {sha: None}
    for pr in pulls if isinstance(pulls, list) else []:
        head = (pr.get('head') or {}).get('sha')
        if (pr.get('base') or {}).get('ref') == MAIN and head and head != sha:
            heads[head] = f'pull request #{pr.get("number")}'
            more, _err = _runs_on(gh, slug, head)
            runs = runs + [dict(r, _via=heads[head]) for r in more or []]
    wanted = {p for p, _ in tests}

    def _newest(runs):
        # A SKIPPED run did not happen. GitHub records one, free, for every
        # push to main in a private repository and for a Promote that was not
        # due a test; counted as a failure, it read main's test as failed
        # in every private repository from 2026-09-25, and would hold every
        # copy-down of main behind a test that was never meant to run.
        newest = {}
        for r in runs:
            path = r.get('path')
            if r.get('conclusion') == 'skipped':
                continue
            if path in wanted and (path not in newest or (r.get('created_at') or '')
                                   > (newest[path].get('created_at') or '')):
                newest[path] = r
        return newest
    newest = _newest(runs)
    if wanted - set(newest):
        # GitHub's run list FILTERED by head_sha can leave out a run that is
        # already going: on 2026-09-30 a Produce's test started seconds
        # after its pull request opened, and the filtered list stayed empty
        # for the whole seven-minute wait, so this said "never ran" and
        # "Do not merge" while it ran; a second wait found it done. The
        # unfiltered list of recent runs has it at once, so one more call,
        # only when something is missing, reads that and matches the
        # commit (or its pull request's head) itself.
        recent, _err = gh.call(f'repos/{slug}/actions/runs?per_page=50', cache=False)
        extra = [dict(r, _via=heads[r.get('head_sha')]) if heads.get(r.get('head_sha'))
                 else r
                 for r in ((recent or {}).get('workflow_runs') or []
                           if isinstance(recent, dict) else [])
                 if r.get('head_sha') in heads]
        newest = _newest(runs + extra)
    missing = sorted(wanted - set(newest))
    bad = sorted(p for p, r in newest.items() if r.get('status') == 'completed'
                 and r.get('conclusion') != 'success')
    busy = sorted(p for p, r in newest.items() if r.get('status') != 'completed')
    if bad:
        return 'failed', ', '.join(f'{p} ({newest[p].get("conclusion")}, '
                                   f'{newest[p].get("html_url", "")})' for p in bad)
    if missing:
        # "Never ran" is only true of the repository GitHub knows by this
        # name. After a rename the old name's run list answered with no runs
        # and no error, and this said "never ran" on a test that had passed
        # (2026-10-04). Ask once what the repository is called now: under a
        # new name, ask again there; when GitHub cannot say, it is unknown.
        if not _renamed_from:
            current, why = _current_slug(gh, slug)
            if current is None:
                return 'unknown', (', '.join(missing) + f' shows no run under {slug}, '
                                   f'and GitHub could not confirm that is still the '
                                   f'repository\'s name: {why}')
            if current.lower() != slug.lower():
                state, detail = github_test_state(root, sha, tests, gh, via_pulls,
                                                  _slug_override=current,
                                                  _renamed_from=slug)
                return state, (f'{detail} (asked as {current}: origin still names '
                               f'{slug}, the repository\'s old name -- '
                               f'git remote set-url origin to the new one)')
        return 'none', ', '.join(missing) + ' never ran on it'
    if busy:
        return 'running', ', '.join(busy) + ' has not finished'
    return 'passed', ', '.join(f'{p} passed' + (f' on {r["_via"]}' if r.get('_via') else '')
                               for p, r in sorted(newest.items()))


def _run_github_test(root, sha, tests, say, gh=None):
    """Start main's GitHub test on `sha` with its workflow_dispatch trigger
    -- a direct commit has no pull request for it to run on -- and wait for
    the answer. -> (state, detail), as github_test_state.

    A button press runs on the branch's tip, not on a commit, so it is
    pressed only while main's tip IS `sha`; if main moves meanwhile, the run
    tested something else, and that is said rather than counted."""
    gh = gh or _sibling('github_budget')
    slug = _slug(root)
    if gh is None or not slug:
        return 'unknown', 'GitHub cannot be asked from here'
    stuck = [p for p, dispatchable in tests if not dispatchable]
    if stuck:
        return 'none', (', '.join(stuck) + ' has no workflow_dispatch trigger, so '
                        'it cannot be started on a commit with no pull request')
    if _remote_tip(root, MAIN) != sha:
        return 'unknown', f'{MAIN} moved on from {sha[:12]} before its test could start'
    for path, _ in tests:
        ok, err = gh.post(f'repos/{slug}/actions/workflows/{path.rsplit("/", 1)[-1]}'
                          f'/dispatches', {'ref': MAIN})
        if not ok:
            return 'unknown', f'could not start {path}: {err}'
    say(f'started the GitHub test on {MAIN} ({sha[:12]}): '
        + ', '.join(p for p, _ in tests) + '. Waiting for it '
        f'(up to {GITHUB_TEST_WAIT_SECONDS // 60} minutes)...')
    deadline = time.monotonic() + GITHUB_TEST_WAIT_SECONDS
    while True:
        time.sleep(GITHUB_POLL_SECONDS)
        state, detail = github_test_state(root, sha, tests, gh, via_pulls=False)
        if state in ('passed', 'failed'):
            return state, detail
        if time.monotonic() >= deadline:
            if _remote_tip(root, MAIN) != sha:
                return 'unknown', (f'{MAIN} moved on from {sha[:12]} while its '
                                   f'test was starting, so the run tested '
                                   f'something else')
            return 'running', (f'{detail}; still no answer after '
                               f'{GITHUB_TEST_WAIT_SECONDS // 60} minutes')


# MAIN'S GITHUB TEST, AT MOST ONCE EVERY X HOURS IN A PRIVATE REPOSITORY
# (2026-10-01, spec/CI_CADENCE_PLAN.md, "Promote decides"). Morgan: "if
# those number of hours or more has passed ... these tests will happen
# BEFORE the github workflow yaml is triggered so that, if it's not being
# run, it doesn't even get to the github point", then "Act ... 168 hours"
# (strength: decided).
#
# THE DECISION IS MADE HERE, IN THE SESSION, WHERE IT COSTS NOTHING. The
# retired ci_debounce_minutes made it inside a GitHub job, which billed a
# minute to decide not to spend one (spec/BILLING_FLOOR.md). Promote names
# the pull request's branch NOT_DUE_PREFIX... when no test is due, and the
# light-check template's job `if:` skips on that name before a runner
# starts.
#
# THE PERSON'S VALUE WINS HERE, the reverse of the commit hook. Morgan: "if
# it conflicts, and I run promote, it still skips it but the repo owner's
# wins on the 2A method" -- the commit hook's [skip ci] (precedent-ci-cadence)
# keeps the repository's own value first.
#
# EVERY DOUBT RUNS THE TEST: a public or undeclared repository, a value of 0
# or one that is not a number, PRECEDENT_CI_NOW=1, no passing run found, a
# newest run that failed, or GitHub not answering. A batch that changes a
# workflow or the vendored engine is NOT forced: Morgan, 2026-10-01, "I'm
# hesitant about forcing that, because I might update the vendored engines a
# lot or I can quickly see this getting out of control" (strength: decided).
#
# ONLY A DUE PROMOTE COPY RUNS IN A PRIVATE REPOSITORY. The light check's
# job `if:` runs a private pull request into main only when its branch is
# a to-main- copy that is not NOT_DUE_PREFIX: GitHub cannot read anyone's
# settings, so a pull request nobody judged is never tested there. Morgan:
# "if and only if the setting is turned on ... AND the number of hours is
# more than the number defined since the last successful test".
NOT_DUE_PREFIX = 'to-main-not-due-'
CADENCE_KEYS = ('github_ci_every_hours', 'ci_every_hours')
FORCE_ENV = 'PRECEDENT_CI_NOW'


def main_test_cadence(root, user_config=None):
    """-> (hours, where): at most how often main's GitHub test runs on a
    Promote. 0 means every Promote. The person's identity.json first, then
    the repository's precedent.json; the new key before the old in each."""
    if precedent_json(root).get('visibility') != 'private':
        return 0.0, 'this repository is not declared private'
    found = None
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email'):
            found = next(((ident[k], str(path)) for k in CADENCE_KEYS if k in ident), None)
            if found:
                break
    if not found:
        repo = precedent_json(root)
        found = next(((repo[k], "this repo's precedent.json") for k in CADENCE_KEYS
                      if k in repo), None)
    if not found:
        return 0.0, 'github_ci_every_hours is not set anywhere'
    value, where = found
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return 0.0, f'github_ci_every_hours is {value!r} in {where}, which is not a number of hours'
    return float(value), where


SWITCH_KEYS = ('github_ci_workflows', 'ci_workflows')


def main_test_switch(root, user_config=None):
    """-> (on, where): are GitHub tests switched on? The person's own
    identity.json first, then the repository's precedent.json, the new key
    before the old in each; on only for "enabled" or nothing declared, so a
    typo switches it off rather than spending minutes. Morgan, 2026-10-01: "it should check the user's
    precedent-individual (if it exists) and see if it has the variable for
    github tests turned on (assume yes)"."""
    found = None
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email'):
            found = next(((ident[k], str(path)) for k in SWITCH_KEYS if k in ident), None)
            break
    if not found:
        repo = precedent_json(root)
        found = next(((repo[k], "this repo's precedent.json") for k in SWITCH_KEYS
                      if k in repo), None)
    if not found:
        return True, 'github_ci_workflows is not declared anywhere, so GitHub tests count as on'
    value, where = found
    if value == 'enabled':
        return True, f'github_ci_workflows is "enabled" in {where}'
    return False, f'github_ci_workflows is {value!r} in {where}'


def _when(root, unix_ts):
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_time
        return precedent_time.from_unix(unix_ts, root).strftime('%Y-%m-%d %H:%M %z')
    except Exception:
        return time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(unix_ts))
    finally:
        sys.path.pop(0)


def _parse_iso(text):
    try:
        return float(calendar.timegm(time.strptime(text, '%Y-%m-%dT%H:%M:%SZ')))
    except (TypeError, ValueError):
        return None


def last_main_test_pass(root, tests, gh=None):
    """-> (unix time or None, problem or None): when main's GitHub test last
    passed -- on main itself, or on a pull request into it from a to-main
    copy. With several test workflows, the OLDEST of their newest passes,
    so each must be within the window. A problem is anything that makes the
    test due whatever the clock says: GitHub not answering, or the newest
    run that finished having FAILED, so a failure stays due until a run
    passes. Skipped runs did not happen and are left out. One API call per
    workflow."""
    gh = gh or _sibling('github_budget')
    slug = _slug(root)
    if gh is None or not slug:
        return None, ('no github.com origin could be read here' if not slug
                      else 'github_budget.py is not beside this file')
    newest = []
    for path, _ in tests:
        data, err = gh.call(f'repos/{slug}/actions/workflows/{path.rsplit("/", 1)[-1]}'
                            f'/runs?per_page=50', cache=False)
        if err or not isinstance(data, dict):
            return None, err or 'GitHub gave an answer this could not read'
        done = sorted(
            ((_parse_iso(r.get('created_at')), r) for r in data.get('workflow_runs') or []
             if r.get('status') == 'completed' and r.get('conclusion') != 'skipped'
             and (r.get('head_branch') == MAIN
                  or is_main_copy(r.get('head_branch')))),
            key=lambda tr: tr[0] or 0, reverse=True)
        if done and done[0][1].get('conclusion') != 'success':
            r = done[0][1]
            return None, (f'its newest run, on {r.get("head_branch")}, ended '
                          f'{r.get("conclusion")} ({r.get("html_url", "")})')
        times = [t for t, r in done if t is not None and r.get('conclusion') == 'success']
        if not times:
            return None, None
        newest.append(max(times))
    return (min(newest) if newest else None), None


MAIN_TEST_KEY = 'github_ci_main_test'
# The same marker precedent_vendor_engine.render_ci_workflow writes; text,
# because this module must import with nothing vendored beside it.
MAIN_TEST_ALWAYS_TEXT = "'main-test:always' == 'main-test:always'"


def main_test_mode(root):
    """-> (mode, hours, why): the repository's own say over main's GitHub
    test, from precedent.json's `github_ci_main_test` (2026-10-01,
    spec/CI_CADENCE_PLAN.md, "The repository decides"). mode is
    'individual' (the default: the person's switch and hours decide),
    'never', 'always' or 'hours' (this many, whatever the person says).
    Anything else is 'never', and says so: a typo costs a missed test,
    never minutes."""
    cfg = precedent_json(root)
    if MAIN_TEST_KEY not in cfg:
        return 'individual', None, f'{MAIN_TEST_KEY} is not set in this repo'
    value = cfg[MAIN_TEST_KEY]
    if value in ('individual', 'never', 'always'):
        return value, None, f'{MAIN_TEST_KEY} is "{value}" in this repo\'s precedent.json'
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return 'hours', float(value), (f'{MAIN_TEST_KEY} is {value:g} in this repo\'s '
                                       f'precedent.json')
    return 'never', None, (f'{MAIN_TEST_KEY} is {value!r} in this repo\'s precedent.json, '
                           f'which is not "individual", "never", "always" or a number of '
                           f'hours -- read as "never" until it is fixed')


def _always_installed(root, tip, tests):
    """True when every installed test workflow carries the marker set to
    always -- what Update Vendors writes for "always". Until it does, an
    "always" repo is decided as "individual", so it is never left with no
    test at all."""
    return bool(tests) and all(
        MAIN_TEST_ALWAYS_TEXT in (_git(root, 'show', f'{tip}:{p}') or '') for p, _ in tests)


def main_test_due(root, tip, gh=None, user_config=None):
    """-> (due, why): does a Promote of `tip` into main get its GitHub test
    on its pull request? In a private repository the repository's own
    github_ci_main_test has the final say; "individual" hands it to the
    person's switch and hours."""
    private = precedent_json(root).get('visibility') == 'private'
    note = ''
    mode = 'individual'
    if private:
        mode, mode_hours, mode_why = main_test_mode(root)
        if mode == 'never':
            return False, f'{mode_why}, so this repository gets no GitHub test'
        if mode == 'always':
            if _always_installed(root, tip, github_tests(root, tip)):
                return False, (f'{mode_why}: GitHub tests the push to {MAIN} once this '
                               f'merges, and never the pull request, so it runs once')
            mode = 'individual'
            note = (f'{mode_why}, but this repo\'s light-check.yml does not say so yet '
                    f'-- run Update Vendors; until then it is decided as "individual": ')
    if os.environ.get(FORCE_ENV) == '1':
        return True, f'{note}{FORCE_ENV}=1 asks for it'
    if private and mode == 'hours':
        hours, where = mode_hours, "this repo's precedent.json"
        key = MAIN_TEST_KEY
    else:
        if private:
            on, where = main_test_switch(root, user_config)
            if not on:
                return False, (f'{note}{where}, so a private repository gets no GitHub '
                               f'test. To run it anyway: {FORCE_ENV}=1 before the Promote')
        hours, where = main_test_cadence(root, user_config)
        key = 'github_ci_every_hours'
    if not hours:
        return True, f'{note}every Promote gets it ({where})'
    tests = github_tests(root, tip)
    if not tests:
        return True, f'{note}no GitHub test is installed here'
    # A workflow installed before 2026-10-01 has no skip on the not-due name,
    # so it would run anyway and a "not due" wait would merge under it.
    old = [p for p, _ in tests
           if NOT_DUE_PREFIX not in (_git(root, 'show', f'{tip}:{p}') or '')]
    if old:
        return True, (f'{note}{old[0]} predates the not-due skip, so it runs on every '
                      f'pull request into {MAIN} until Update Vendors brings the '
                      f'current one')
    when, problem = last_main_test_pass(root, tests, gh)
    if problem:
        return True, note + problem
    if when is None:
        return True, f'{note}no passing run of it was found'
    age = time.time() - when
    if age >= hours * 3600:
        return True, (f'{note}it last passed {_when(root, when)}, {age / 3600:.0f}h ago, '
                      f'and {where} sets {key} {hours:g}')
    return False, (f'{note}it last passed {_when(root, when)}, {age / 3600:.0f}h ago; '
                   f'{where} sets {key} {hours:g}, so the next one '
                   f'is due {_when(root, when + hours * 3600)}. To run it anyway: '
                   f'{FORCE_ENV}=1 before the Promote')


def _gets_github_test(root, branch):
    """Main's GitHub test belongs to main as a tier of its own. Where main
    IS the staging tier, Promote pushes into it with no pull request, so the
    staging tier's local check is its whole bar here too."""
    return branch == MAIN and staging_branch(root) != MAIN


def tier_check_state(root, branch, tip, gh=None):
    """-> (checked, detail) without running anything: has `tip`, on tier
    `branch`, had the checks that tier requires? A published full-check
    receipt for its tree, and on main the GitHub test too where one is
    installed. Cheap: a fetch of the receipt branch, and on main a few API
    calls."""
    rec = _receipt(root, tip)
    parts = [f'full local check passed at {rec.get("at", "an unrecorded time")}'
             if rec else 'no full local check on record']
    ok = bool(rec)
    if _gets_github_test(root, branch):
        tests = github_tests(root, tip)
        if not tests:
            parts.append('no GitHub test is installed here')
        else:
            state, detail = github_test_state(root, tip, tests, gh)
            if state != 'passed':
                due, why = main_test_due(root, tip, gh=gh)
                if not due:
                    state, detail = 'not due', why
            parts.append(f'GitHub test {state}: {detail}')
            ok = ok and state in ('passed', 'not due')
    return ok, '; '.join(parts)


def _check_tier(root, branch, tip, say, gh=None):
    """Give `tip`, on tier `branch`, whatever of its tier's checks it lacks,
    and -> (ok, detail). The full local check (a published receipt makes it
    instant), then on main the GitHub test: found on the commit or its pull
    request, else started and awaited."""
    with _Worktree(root, tip) as wt:
        t0 = time.monotonic()
        ok, out = _check(root, wt, FULL, dest=branch)
        took = time.monotonic() - t0
    if not ok:
        return False, f'the full local check failed on {tip[:12]}:\n{out}'
    reused = any('already passed' in l for l in out.splitlines())
    local = ('its full local check had already passed' if reused else
             f'the full local check ran on it and passed, in {took:.0f}s')
    if not _gets_github_test(root, branch):
        return True, local
    tests = github_tests(root, tip)
    if not tests:
        return True, (f'{local}; no GitHub test is installed in this repository, '
                      f'so the local check is the whole check')
    state, detail = github_test_state(root, tip, tests, gh)
    if state != 'passed':
        due, why = main_test_due(root, tip, gh=gh)
        if not due:
            return True, f'{local}; GitHub test not due: {why}'
    if state == 'none':
        state, detail = _run_github_test(root, tip, tests, say, gh)
    elif state == 'running':
        say(f'the GitHub test on {MAIN} ({tip[:12]}) is still running; waiting for it...')
        deadline = time.monotonic() + GITHUB_TEST_WAIT_SECONDS
        while state == 'running' and time.monotonic() < deadline:
            time.sleep(GITHUB_POLL_SECONDS)
            state, detail = github_test_state(root, tip, tests, gh)
    if state == 'passed':
        return True, f'{local}; GitHub test: {detail}'
    return False, f'{local}, but the GitHub test is {state}: {detail}'


def _at_head(sha):
    """', at head commit <all 40 characters>' -- the merge instruction's
    expected head. A merge through GitHub's API takes the head it expects in
    full (expectedHeadSha), and the twelve-character form printed everywhere
    else here is refused there; a session in nomen-omen read the short one
    back and had to look the rest up (2026-10-06). Pinning the head also
    means a copy that moved after its check is not merged by mistake."""
    return f', at head commit {sha}' if sha else ''


def wait_for_main_test(root, sha, say=print, gh=None, copy=None):
    """Wait for main's GitHub test on `sha` -- the to-main copy's tip, once
    its pull request into main is open -- and -> 0 passed, 1 anything else.

    The last step of a Promote into main is "wait for its GitHub test, then
    merge", and until 2026-09-27 nothing here did the waiting, so each
    session wrote its own poller; one crashed mid-wait that day on a Python
    version quirk and was read by eye instead. This is that wait, once:
    `--wait-main-test COPY` after opening the pull request. A run that has
    not appeared within GITHUB_START_WAIT_SECONDS is reported as never
    started rather than waited on for the full half hour."""
    tests = github_tests(root, sha)
    if not tests:
        say(f'no GitHub test is installed here, so there is nothing to wait for '
            f'on {sha[:12]}: the full local check at the Promote was the whole check.')
        return 0
    if copy and is_not_due_copy(copy):
        say(f'GitHub test NOT DUE on {sha[:12]}: Promote named this copy {copy} '
            f'because main\'s GitHub test is not due on its pull request (the '
            f'Promote printed why), so the pull request shows the test as skipped '
            f'and no runner started. The full local check at the Promote stands; '
            f'in a repo set to github_ci_main_test "always", GitHub tests the push '
            f'to {MAIN} once this merges. Merge the pull request into {MAIN} with '
            f'a merge commit{_at_head(sha)}.')
        return 0
    say(f'waiting for the GitHub test on {sha[:12]} (up to '
        f'{GITHUB_TEST_WAIT_SECONDS // 60} minutes): ' + ', '.join(p for p, _ in tests))
    t0 = time.monotonic()
    state, detail = github_test_state(root, sha, tests, gh)
    while state in ('running', 'none'):
        waited = time.monotonic() - t0
        if waited >= GITHUB_TEST_WAIT_SECONDS or (
                state == 'none' and waited >= GITHUB_START_WAIT_SECONDS):
            break
        time.sleep(GITHUB_POLL_SECONDS)
        state, detail = github_test_state(root, sha, tests, gh)
    if state == 'passed':
        say(f'GitHub test PASSED on {sha[:12]}: {detail}. Merge the pull request '
            f'into {MAIN} with a merge commit{_at_head(sha)}.')
        return 0
    say(f'GitHub test {state.upper()} on {sha[:12]}: {detail}. Do not merge.')
    return 1


# A FILE A TOOL WRITES is never a merge conflict worth a person's time:
# neither side's copy is right, a fresh one from the merged sources is. Two
# marks say a file is generated -- the `generated_by: tools/X.py` header
# every whole generated view carries (build_views, build_gotcha_index,
# build_todo_index), and doc_html's own registry of the pages it renders.
# A conflict in anything else is hand-written text and still stops.
_GENERATED_BY_RE = re.compile(r'^generated_by:\s*["\']?(tools/[\w./-]+\.py)', re.M)

# ...and only a generator that rebuilds its files when run with no
# arguments, cheaply and offline, is ever run here. A header can name a tool
# that is something else besides: record/stale_branches.md is written by
# very_deep_check.py, which run bare is the very deep check itself, network
# and all. A file whose generator is not listed here counts as hand-written.
REBUILT_BARE = ('tools/build_views.py', 'tools/build_gotcha_index.py',
                'tools/build_todo_index.py', 'tools/doc_html.py')


def _generator_of(wt, rel):
    """-> the repo-relative tool that writes `rel` in worktree `wt`, or None
    when `rel` is hand-written. Read from our side of a conflicted file
    (index stage 2), so a conflict hunk cannot hide the header. Read as
    bytes: a conflicted file can be binary (a Word file), which carries no
    header and so counts as hand-written -- the Promote stops and names it,
    where decoding it as text crashed (2026-10-05)."""
    ours = subprocess.run(['git', '-C', str(wt), 'show', f':2:{rel}'],
                          capture_output=True)
    head = (ours.stdout[:2000].decode('utf-8', errors='replace')
            if ours.returncode == 0 else '')
    m = _GENERATED_BY_RE.search(head)
    if m and m.group(1) in REBUILT_BARE and (pathlib.Path(wt) / m.group(1)).is_file():
        return m.group(1)
    if rel.endswith('.html') and (pathlib.Path(wt) / 'tools' / 'doc_html.py').is_file():
        src = rel[:-len('.html')] + '.md'
        reg = (pathlib.Path(wt) / 'tools' / 'doc_html.py').read_text(encoding='utf-8')
        if re.search(r"\(\s*['\"]" + re.escape(src) + r"['\"]", reg):
            return 'tools/doc_html.py'
    return None


def _resolve_by_regenerating(wt, say):
    """After a merge stopped on conflicts in `wt`: when every conflicted file
    is generated, take our side, run each one's generator over the merged
    sources, and stage the result. -> (True, [regenerated]) or (False, [the
    hand-written files that conflict])."""
    conflicted = [l for l in _run(wt, 'diff', '--name-only', '--diff-filter=U')
                  .stdout.splitlines() if l.strip()]
    gens = {rel: _generator_of(wt, rel) for rel in conflicted}
    hand = sorted(rel for rel, g in gens.items() if not g)
    if hand or not conflicted:
        return False, hand
    for rel in conflicted:
        _run(wt, 'checkout', '--ours', '--', rel)
    for tool in sorted(set(gens.values())):
        r = subprocess.run([sys.executable, tool], cwd=str(wt),
                           capture_output=True, text=True)
        if r.returncode != 0:
            say(f'{tool} could not rebuild {", ".join(sorted(k for k, v in gens.items() if v == tool))}: '
                f'{(r.stdout + r.stderr).strip()[-300:]}')
            return False, []
    for rel in conflicted:
        text = (pathlib.Path(wt) / rel).read_text(encoding='utf-8', errors='replace')
        if '<<<<<<<' in text or '>>>>>>>' in text:
            return False, [rel]
    _drop_stamp_only_changes(wt)
    _run(wt, 'add', '-A', '--', *conflicted)
    _run(wt, 'add', '-u')
    return True, sorted(conflicted)


def _stamp_only(wt, rel):
    """True when the only lines `rel` changed in worktree `wt` are a
    render's build stamp: doc_html writes the time it ran into every page it
    renders, so a rebuild of an unchanged page differs by that line alone."""
    diff = _run(wt, 'diff', '-U0', '--', rel).stdout.splitlines()
    changed = [l for l in diff if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    return bool(changed) and all('class="renderstamp"' in l for l in changed)


def _drop_stamp_only_changes(wt):
    """Put back every tracked file in `wt` whose only change is a build stamp."""
    for rel in (_git(wt, 'diff', '--name-only') or '').splitlines():
        if rel and _stamp_only(wt, rel):
            _run(wt, 'checkout', '--', rel)


def _rebuild_generated(wt, say):
    """Run, over the composed sources in worktree `wt`, every generator it
    uses that rebuilds bare (REBUILT_BARE): the ones named in a
    `generated_by:` header, and doc_html where it is present. -> the tracked
    files that came out different, apart from build stamps; [] when every
    generated file was already current.

    This is the mechanical repair most pushes made off the ladder need: a
    source edited on main whose render, map or index nobody rebuilt. On a
    tree that is already consistent it changes nothing."""
    tools = set()
    for line in (_git(wt, 'grep', '-h', '-I', '-E', '^generated_by:') or '').splitlines():
        m = _GENERATED_BY_RE.match(line)
        if m and m.group(1) in REBUILT_BARE and (pathlib.Path(wt) / m.group(1)).is_file():
            tools.add(m.group(1))
    if (pathlib.Path(wt) / 'tools' / 'doc_html.py').is_file():
        tools.add('tools/doc_html.py')
    # doc_html last: it renders documents the others may have just rewritten.
    for tool in sorted(tools, key=lambda t: (t == 'tools/doc_html.py', t)):
        r = subprocess.run([sys.executable, tool], cwd=str(wt),
                           capture_output=True, text=True)
        if r.returncode != 0:
            say(f'NOTE: {tool} could not run over the composed tree, so what it '
                f'generates was left as merged and the full check judges it: '
                f'{(r.stdout + r.stderr).strip()[-300:]}')
    _drop_stamp_only_changes(wt)
    return [l for l in (_git(wt, 'diff', '--name-only') or '').splitlines() if l]


def sync_pre_staging(root, say=print, check=False):
    """Make origin's pre-staging exist and hold what reached staging without
    climbing through it. -> True on success, False when pre-staging could
    not be brought current (a conflict, a race, a failing basic check on the
    merge).

    MAIN'S WORK IS NOT COPIED HERE (spec/LADDER_OPT_IN_PLAN.md D10, Morgan
    2026-10-03, strength: decided). People off the ladder push to main
    directly, with none of the ladder's checks, so their work comes down
    only inside a Promote into staging (_promote_unlocked), composed with
    staging and pre-staging and fully checked as one tree: pre-staging only
    ever receives a composition that passed. Where main has such work, this
    says so and names that Promote.

    Creates pre-staging at staging's tip when origin has none. Otherwise,
    for staging with a file change pre-staging lacks: its tip must first
    have had its own tier's checks -- tier_check_state. With `check`, anything missing is run (_check_tier);
    without it, unchecked work is reported and left where it is, because a
    GitHub test can take many minutes and `Go update` is meant to be quick.
    Promote runs with `check`. What passes is merged into pre-staging, a
    basic-tier push; what fails is reported with the commit and the reason,
    and never copied. A conflict stops the sync and pushes nothing. Nothing
    here ever pushes to staging or main."""
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
    if staging != MAIN:
        mtip = _remote_tip(root, MAIN)
        if mtip:
            _run(root, 'fetch', '-q', 'origin', MAIN)
            sources.append((MAIN, mtip))
    pending = [(b, t, c) for b, t in sources for c in [drift(root, ptip, t)] if c]
    if not pending:
        return True
    ready = []
    for branch, tip, commits in pending:
        what = (f'{branch} has {len(commits)} commit(s) with changes '
                f'{PRE_STAGING} lacks, up to {tip[:12]}')
        if branch == MAIN and staging != MAIN:
            say(f'LEFT FOR THE NEXT PROMOTE INTO {staging.upper()}: {what}. They '
                f'come down there, composed with {staging} and {PRE_STAGING} and '
                f'fully checked as one tree, never copied here on their own: '
                f'python3 tools/precedent_branches.py --promote --to staging')
            continue
        if check:
            ok, detail = _check_tier(root, branch, tip, say)
        else:
            ok, detail = tier_check_state(root, branch, tip)
        if ok:
            ready.append((branch, tip))
            continue
        if not check:
            say(f'NOT COPIED YET: {what}, and it has not had all of the '
                f'{branch} checks ({detail}). Run them and copy it down: '
                f'python3 tools/precedent_branches.py --sync-pre-staging --check '
                f'(Promote does the same).')
        else:
            say(f'NOT COPIED: {what}, and it did not pass the {branch} checks, so it '
                f'was not copied into {PRE_STAGING}. It is live on {branch} '
                f'already; fix it the normal way -- on {PRE_STAGING}, then '
                f'Promote.\n  '
                + '\n  '.join(commits) + f'\n{detail}')
    if not ready:
        return True
    with _Worktree(root, ptip) as wt:
        for branch, tip in ready:
            m = _run(wt, 'merge', '--no-ff', '-q', '-m',
                     f'Merge {branch} into {PRE_STAGING}', tip, env=_merge_env(root))
            if m.returncode != 0:
                done, files = _resolve_by_regenerating(wt, say)
                if done:
                    c = _run(wt, 'commit', '-q', '--no-edit', env=_merge_env(root))
                    done = c.returncode == 0
                if not done:
                    _run(wt, 'merge', '--abort')
                    say(f'{branch} does not merge cleanly into {PRE_STAGING} -- the '
                        f'same lines changed on both'
                        + (f' ({", ".join(files)})' if files else '')
                        + f'. Nothing was pushed. Merge {branch} into {PRE_STAGING} '
                        f'by hand, resolve it, and push to {PRE_STAGING}.')
                    return False
                say(f'{branch} and {PRE_STAGING} both changed '
                    f'{", ".join(files)}; generated, so rebuilt from the merged '
                    f'sources rather than either side taken.')
        ok, out = _check(root, wt, BASIC, dest=PRE_STAGING)
        if not ok:
            say(f'the merge of {" and ".join(b for b, _ in ready)} into '
                f'{PRE_STAGING} fails the basic check; nothing was pushed.\n{out}')
            return False
        p = _run(wt, 'push', '-q', 'origin', f'HEAD:refs/heads/{PRE_STAGING}')
        if p.returncode != 0:
            say(f'{PRE_STAGING} moved while this ran; run it again. ({p.stderr.strip()[:200]})')
            return False
    say(f'merged {" and ".join(b for b, _ in ready)} into {PRE_STAGING}.')
    return True


def drift_report(root, gh=None):
    """-> [line] for the session-start freshness report: each tier above
    pre-staging with a file change pre-staging lacks, how many commits, and
    whether they have had their tier's checks. Silent about merge commits
    that change no file. Reads origin as last fetched plus the receipt
    branch; on main with a GitHub test installed, a few API calls."""
    staging = staging_branch(root)
    ptip = _git(root, 'rev-parse', '-q', '--verify', f'refs/remotes/origin/{PRE_STAGING}')
    if not ptip:
        return []
    out = []
    for branch in [staging] + ([MAIN] if staging != MAIN else []):
        tip = _git(root, 'rev-parse', '-q', '--verify', f'refs/remotes/origin/{branch}')
        commits = drift(root, ptip, tip) if tip else []
        if not commits:
            continue
        ok, _detail = tier_check_state(root, branch, tip, gh)
        if branch == MAIN:
            # Made off the ladder: they come down composed and fully checked
            # with the ladder's own work, never copied on their own.
            out.append(f'origin/{MAIN} is {len(commits)} commit(s) ahead of '
                       f'origin/{PRE_STAGING} with changes it lacks '
                       f'({"checked" if ok else "unchecked"}). The next Promote '
                       f'into {staging} brings them in, checked with the rest: '
                       f'python3 tools/precedent_branches.py --promote --to staging')
            continue
        cmd = ('python3 tools/precedent_branches.py --sync-pre-staging'
               + ('' if ok else ' --check'))
        out.append(f'origin/{branch} is {len(commits)} commit(s) ahead of '
                   f'origin/{PRE_STAGING} with changes it lacks '
                   f'({"checked" if ok else "unchecked"}). Bring them in: {cmd}')
    return out


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
#
# 20 minutes, down from 45, on 2026-09-26. That day a window died holding
# the lock and every Promote said in other windows did nothing for the full
# 45 minutes, while staging sat still. A live Promote holds it for its one
# full check plus a merge and a push: the slowest full check measured that
# day took 379 seconds, so 20 minutes is still about three times what a
# live holder needs. Morgan: "Please update the lock to be 20 minutes
# unless you disagree" (strength: decided).
#
# 15 minutes, down from 20, later on 2026-09-26. 900 seconds is still about
# two and a half times that slowest 379-second check. An overrun costs one
# wasted check run, never a commit: the later window's plain push to staging
# is refused. Morgan: "Let's update that again to 15 minutes ... this should
# be more than enough" (strength: decided).
LOCK_BRANCH = 'precedent-promote-lock'
LOCK_STALE_SECONDS = 15 * 60
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


def promote_in_progress(root):
    """-> 'held by X, N min ago' while another window holds a fresh Promote
    lock on this repo, else None. Never raises.

    For anything that would otherwise tell the person a Promote is waiting:
    while one is already running, suggesting another is wrong. Morgan,
    2026-09-27 (strength: decided), after the reply gate's per-turn line
    told him "a Promote can move them" twice while another window was
    promoting and his own Promote had just done nothing: "NEVER recommend a
    promote when another session is already doing it!!!" A claim older than
    LOCK_STALE_SECONDS is not a Promote running -- the next one takes it
    over -- so it does not count."""
    try:
        tip, subject, at = _lock_state(root)
    except Exception:                                         # noqa: BLE001
        return None
    if not tip or not (subject or '').startswith('held by') or not at:
        return None
    age = time.time() - at
    if age >= LOCK_STALE_SECONDS:
        return None
    return f'{subject.replace(" [skip ci]", "")}, {int(age // 60)} min ago'


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


def _lock_claim(root, say, what=None):
    """-> ('held', commit) when this window now holds the lock; ('busy',
    reason) when another does; ('none', reason) when the lock could not be
    used at all, and the Promote goes ahead without it, as before. `what`
    names a holder other than a Promote -- the merge gate's landing check
    (hold_for_landing) -- in the claim's subject."""
    tip, subject, at = _lock_state(root)
    age = time.time() - at if at else None
    if tip and subject.startswith('held by') and age is not None \
            and age < LOCK_STALE_SECONDS:
        return 'busy', f'{subject.replace(" [skip ci]", "")}, {int(age // 60)} min ago'
    stale = ' (taking over a claim older than %d min)' % (LOCK_STALE_SECONDS // 60) \
        if tip and subject.startswith('held by') else ''
    ok, commit, err = _lock_push(
        root, tip, f'held by {_lock_holder_name()}' + (f' ({what})' if what else ''),
        f'{"A Promote" if not what else what[0].upper() + what[1:]} is running. '
        'tools/precedent_branches.py releases this when it ends; a claim older '
        f'than {LOCK_STALE_SECONDS // 60} minutes may be taken over.{stale}')
    if ok:
        return 'held', commit
    if any(w in err for w in ('non-fast-forward', 'fetch first', 'rejected')):
        tip, subject, at = _lock_state(root)
        who = subject.replace(' [skip ci]', '') if subject else 'another window'
        return 'busy', f'{who}, just now'
    return 'none', err[:200] or 'the lock commit could not be made'


def _lock_release(root, held, say):
    try:
        ok, _commit, err = _lock_push(root, held, 'free', 'No Promote is running.')
    except CommitRefused as exc:
        ok, err = False, str(exc)
    if not ok:
        say(f'NOTE: could not release {LOCK_BRANCH} ({err[:160]}); it frees '
            f'itself after {LOCK_STALE_SECONDS // 60} minutes.')



def hold_for_landing(root, what):
    """-> (state, info) as _lock_claim: the Promote lock, taken by the merge
    gate while it checks a pull request into a fully checked branch.

    WHY (2026-09-30). The merge gate judges the exact merge GitHub would
    make, so any move of the base while its check runs makes the pass stale
    and the check runs again. One landing into staging ran its full check
    five times in an afternoon, twice only because other windows promoted
    into staging while it ran. Taking the lock Promote already takes holds
    both kinds of move still: a Promote finds it held and does nothing, and
    another landing's merge gate refuses at once instead of starting a check
    that would be out of date before it finished. The gate frees it as soon
    as the check ends; the merge follows within seconds, so a move in that
    gap is the one window left open."""
    return _lock_claim(root, print, what=what)


def release_hold(root, held):
    """Free a hold_for_landing claim; a failure only says so (the claim
    frees itself after LOCK_STALE_SECONDS)."""
    _lock_release(root, held, print)

def _new_commits(root, since, tip):
    """The commits on `tip` that `since` lacks and that change a file, one
    line each. A merge made only to keep two tiers in step, or an empty
    commit, is not work waiting to move, and is never counted where a person
    reads the number (Morgan, 2026-09-27, strength: decided: tell me "the
    number of commits ahead/behind that made changes to the repo")."""
    return (_git(root, 'log', '--oneline', '--no-merges', f'{since}..{tip}',
                 '--', '.') or '').splitlines()


# A batch shows which commits are not this session's own. Found 2026-10-06,
# a Produce in a shared set: it carried one session's one-line change and
# another session's Update Vendors, listed the same way, and auto mode held
# the move until the person approved a commit nobody had named to them.
OTHER_WORK_MARK = "<- not this session's work"


def _this_session_id():
    """-> this session's ID without its `cse_`/`session_` prefix, or ''."""
    here = str(pathlib.Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        from precedent_detect import this_session_id
        sid = this_session_id() or ''
    except Exception:                                       # noqa: BLE001
        sid = ''
    for prefix in ('cse_', 'session_'):
        if sid.startswith(prefix):
            sid = sid[len(prefix):]
    return sid


def mark_other_work(root, batch, work=None, sid=None):
    """-> (lines, others): `batch` (_new_commits lines) with each commit that
    is not this session's work marked OTHER_WORK_MARK, and those commits'
    lines. A commit is this session's when it is on the `work` branch, or
    when its message carries a Claude-Session line naming this session --
    the second catches a session that Booked two branches and promotes with
    one of them. A fix branch counts for nothing here, since it carries the
    whole batch; only the session line is read. With neither a work branch nor a session ID nothing can be
    told apart, so nothing is marked."""
    sid = _this_session_id() if sid is None else sid
    wtip = None
    name = (work[len('origin/'):] if work and work.startswith('origin/')
            else work)
    # A fix branch is the last unfinished Promote's composition: every
    # commit in the batch is on it, so being on it says nothing about whose
    # work a commit is, and only the Claude-Session line can (found
    # 2026-10-06, a Debut rerun from its fix branch marked no commit,
    # another session's among them).
    if work and not is_fix_branch(name):
        wtip = (_git(root, 'rev-parse', '--verify', '--quiet', f'origin/{name}^{{commit}}')
                or _git(root, 'rev-parse', '--verify', '--quiet', f'{work}^{{commit}}'))
    if not wtip and not sid:
        return list(batch), []
    lines, others = [], []
    for line in batch:
        sha = line.split(' ', 1)[0]
        mine = bool(wtip) and _run(root, 'merge-base', '--is-ancestor', sha,
                                   wtip).returncode == 0
        if not mine and sid:
            body = _git(root, 'log', '-1', '--format=%B', sha) or ''
            mine = any(l.startswith('Claude-Session:') and l.rstrip().endswith(sid)
                       for l in body.splitlines())
        if mine:
            lines.append(line)
        else:
            lines.append(f'{line}   {OTHER_WORK_MARK}')
            others.append(line)
    return lines, others


def _other_work_note(others, work):
    if not others:
        return ''
    on = f'not on {work} and ' if work else ''
    return (f'\n{len(others)} of these commit(s) are {on}not marked with this '
            f'session\'s Claude-Session line: someone else Booked them. Name '
            f'them to the person when asking to approve this move.')


def promotion_step(root, to=None, work=None):
    """-> (step, why): which Promote to run. `step` is STAGING (pre-staging
    into staging), MAIN (staging into main) or None (nothing waiting).

    Morgan, 2026-09-26 (strength: decided): Promote "should decide based on
    the context and ... what branch we were just working on" whether it moves
    pre-staging to staging or staging to main, and say which it chose. The
    context is the session's, so the session hands it in:
      to    the step itself, when the person named one
      work  the branch or commit the session was just working on. Not on
            staging yet -> pre-staging into staging; on staging but not on
            main -> staging into main.
    With neither, the tiers decide: work waiting on pre-staging goes first,
    and only when there is none does staging move into main. A repository
    whose staging tier IS main has one step only.

    When BOTH steps have work waiting -- pre-staging ahead of staging and
    staging ahead of main -- an unnamed Promote is ambiguous, and it moves
    pre-staging into staging even when `work` sits on staging already
    (Morgan, 2026-09-26, strength: decided: "if my 'promote' is ambiguous
    and you don't know which of the two types of promotion it should refer
    to - then choose to do pre-staging to staging"). Only --to main
    overrides that."""
    staging = staging_branch(root)
    if staging == MAIN:
        return STAGING, f'{MAIN} is the staging tier here, so there is one step'
    if to in (STAGING, MAIN):
        return to, f'asked for by name (--to {to})'
    _run(root, 'fetch', '-q', 'origin', PRE_STAGING, staging, MAIN)
    stip, mtip = _remote_tip(root, staging), _remote_tip(root, MAIN)
    ptip = _remote_tip(root, PRE_STAGING)
    if work:
        _run(root, 'fetch', '-q', 'origin', work)
        sha = _git(root, 'rev-parse', '--verify', '--quiet', f'{work}^{{commit}}') \
            or _git(root, 'rev-parse', '--verify', '--quiet', f'origin/{work}^{{commit}}')
        if not sha:
            return None, (f'{work!r} is not a branch or commit this checkout can '
                          f'see, so nothing was chosen from it')
        on = lambda tip: bool(tip) and _run(
            root, 'merge-base', '--is-ancestor', sha, tip).returncode == 0
        if not on(stip):
            return STAGING, (f'the work just done ({work}) is not on {staging} '
                             f'yet, so it moves there first')
        if mtip and not on(mtip):
            if ptip and stip and _new_commits(root, stip, ptip):
                return STAGING, (f'the work just done ({work}) waits for '
                                 f'{MAIN}, but {PRE_STAGING} also has work '
                                 f'{staging} lacks, so the step is ambiguous '
                                 f'and {PRE_STAGING} goes first')
            return MAIN, (f'the work just done ({work}) is on {staging} '
                          f'already and not yet on {MAIN}')
    if ptip and stip and _new_commits(root, stip, ptip):
        return STAGING, (f'{PRE_STAGING} has work {staging} lacks, and it goes '
                         f'first')
    if stip and mtip and _new_commits(root, mtip, stip):
        return MAIN, (f'nothing is waiting on {PRE_STAGING}, and {staging} has '
                      f'work {MAIN} lacks')
    if not mtip:
        return None, f'{PRE_STAGING} has nothing {staging} lacks, and origin has no {MAIN}'
    return None, f'{PRE_STAGING}, {staging} and {MAIN} carry the same work'


def produce_waiting_hold(root, gh=None):
    """-> why a move from pre-staging into staging waits, or None: a pull
    request into main from a `to-main-` copy of staging is still open, and
    moving staging now leaves that copy behind, so the merge check refuses
    it and the Produce starts over. Seen 2026-10-06: a second Debut ran
    while a Produce pull request waited on its GitHub test, and the pull
    request had to be closed and made again. None when GitHub cannot be
    asked -- the merge check still refuses a stale copy."""
    gh = gh or _sibling('github_budget')
    slug = _slug(root)
    if gh is None or not slug:
        return None
    got, _err = gh.call(f'repos/{slug}/pulls?state=open&base={MAIN}', cache=False)
    if not isinstance(got, list):
        return None
    waiting = [f'#{p.get("number")}' for p in got
               if is_main_copy((p.get('head') or {}).get('ref'))]
    if not waiting:
        return None
    return (f'NOT PROMOTED: {" and ".join(waiting)} into {MAIN} is still open, '
            f'made from a copy of {staging_branch(root)}. Moving '
            f'{staging_branch(root)} now would leave that copy out of date and '
            f'the merge check would refuse it. Finish it first -- wait for its '
            f'GitHub test (--wait-main-test) and merge it -- or close it, then '
            f'promote again.')


def retired_set_hold(root, env=None):
    """-> why a Promote in a practice set that says it is retired does
    nothing, or None. Morgan, 2026-10-06 (strength: decided), the same day
    a session promoted toward main in every set at once: "I just told you a
    few minutes ago to not edit nor promote nor touch repo maintenance or
    working style, unless it is essential to their graceful deprecation."
    Practice: retired-set-takes-only-its-retirement (temporary). The
    person's own words in PRECEDENT_RETIRED_SET_EDIT let one Promote run."""
    env = os.environ if env is None else env
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_vendor_engine as ve
    except ImportError:
        return None
    finally:
        sys.path.pop(0)
    judge = (getattr(ve, 'retirement_on_any_tier', None)
             or getattr(ve, 'source_retirement', None))
    retirement = judge(root) if judge else None
    if retirement is None:
        return None
    asked = (env.get('PRECEDENT_RETIRED_SET_EDIT') or '').strip()
    if asked:
        print(f'promoting a retired set, because the person asked: {asked!r}',
              flush=True)
        return None
    return ('NOT PROMOTED: this set says it is retired, and a retired set is '
            'not promoted unless the person asks for that exact move as '
            'essential to retiring it gracefully (practice: '
            'retired-set-takes-only-its-retirement). If they have, run again '
            'with PRECEDENT_RETIRED_SET_EDIT="<their words>".')


def promote(root, say=print, to=None, work=None):
    """Pick the step (promotion_step), SAY it, then run it, one window at a
    time. -> 0 promoted, nothing to promote, or another window already
    promoting; 1 refused (a failing check, a conflict, a race);
    PROMOTE_MAIN_NOT_MOVED when staging into main is ready for its pull
    request and main has not moved yet."""
    held = retired_set_hold(root)
    if held:
        say(held)
        return 1
    if not repo_has_tiers(root) and not _git(
            root, 'rev-parse', '--verify', '--quiet',
            f'refs/remotes/origin/{staging_branch(root)}'):
        # Nothing ever creates tiers in a repository that did not ask for
        # them (spec/LADDER_OPT_IN_PLAN.md, Morgan 2026-10-02: "Yes"). Before
        # this, a Promote here announced a move, failed on the missing
        # staging branch, and left its lock branch behind on origin.
        say(f'this repository has only {MAIN}, and work lands there '
            f'directly, so there is nothing to promote.')
        return 0
    step, why = promotion_step(root, to, work)
    staging = staging_branch(root)
    above = _drifted_from_above(root) if step is None else []
    if step is None and not above:
        say(f'nothing to promote: {why}.')
        return 0
    if step is None:
        # Nothing climbs, but something arrived from above -- a bot commit
        # on main, a direct push to staging. Promote is where that gets its
        # checks and is copied down, so it is not left for a day when
        # pre-staging happens to have work waiting.
        say(f'Nothing waits to be promoted ({why}), but {" and ".join(above)} '
            f'carr{"ies" if len(above) == 1 else "y"} changes {PRE_STAGING} '
            f'lacks: composing them with {staging} and {PRE_STAGING}, checking '
            f'that, and moving both.')
        run = _promote_unlocked
    else:
        source, dest = (PRE_STAGING, staging) if step == STAGING else (staging, MAIN)
        if step == STAGING:
            waits = produce_waiting_hold(root)
            if waits:
                say(waits)
                return 1
        # The one line a person reads first: which move this is, in these words.
        say(f'Now promoting from {source} to {dest} ({why}).')
        run = _promote_unlocked if step == STAGING else _promote_to_main
    if work and run in (_promote_unlocked, _promote_to_main):
        run = (lambda r, s, f=run: f(r, s, work=work))
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
        return run(root, say)
    old_handlers = _exit_cleanly_on_signal()
    try:
        return run(root, say)
    finally:
        _ignore_signals(old_handlers)
        try:
            _lock_release(root, info, say)
        finally:
            _restore_signals(old_handlers)


# A KILLED PROMOTE RELEASES ITS LOCK (2026-09-28). The try/finally above
# frees the lock on an error or a Ctrl-C, but SIGTERM -- what a command
# timeout, a closed session or `kill` sends -- ends Python without running
# any finally block. A session ran a Promote under a 590-second limit, the
# limit killed it mid-check, and its claim sat on origin for the full
# LOCK_STALE_SECONDS: the same session's retry was told another window was
# promoting, and so would every other window have been. Turning SIGTERM and
# SIGHUP into SystemExit makes the finally run; the child check is killed
# by subprocess.run on the way out. SIGKILL cannot be caught, which is what
# the staleness timeout is still for. Morgan: "Yes approved! Please add
# this!!" (strength: decided).
_CLEAN_EXIT_SIGNALS = ('SIGTERM', 'SIGHUP')


def _exit_cleanly_on_signal():
    """Make SIGTERM and SIGHUP raise SystemExit, so finally blocks run.
    -> the previous handlers, for _restore_signals. Never raises: off the
    main thread signal.signal refuses, and the Promote goes on as before."""
    import signal

    def _raise(signum, _frame):
        raise SystemExit(128 + signum)
    old = {}
    for name in _CLEAN_EXIT_SIGNALS:
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            old[sig] = signal.signal(sig, _raise)
        except (ValueError, OSError):
            pass
    return old


def _ignore_signals(old):
    """While the release itself runs -- one small push -- a second SIGTERM
    must not cut it short, or the kill that started it wins after all."""
    import signal
    for sig in old:
        try:
            signal.signal(sig, signal.SIG_IGN)
        except (ValueError, OSError):
            pass


def _restore_signals(old):
    import signal
    for sig, handler in old.items():
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError, TypeError):
            pass


def _drifted_from_above(root):
    """-> the tiers above pre-staging whose tips carry a file change
    pre-staging lacks, as origin last showed them (promotion_step has just
    fetched all three)."""
    staging = staging_branch(root)
    ptip = _remote_tip(root, PRE_STAGING)
    if not ptip or staging == MAIN:
        return []
    out = []
    for branch in (staging, MAIN):
        tip = _remote_tip(root, branch)
        if tip and drift(root, ptip, tip):
            out.append(branch)
    return out


# PROMOTE'S OWN BRANCHES ARE NAMED LIKE A SESSION'S (Morgan, 2026-10-06,
# strength: decided: "isn't our URL format for temporary GitHub repo URLs to
# start with the timestamps then the slug then a few random characters? ...
# let's do that"). The fix branch and the copy a pull request into main
# comes from were named promote-fix-DATE and to-main-DATE, outside the
# claude/<date>-<slug>-<id> format every other temporary branch takes from
# tools/precedent_branch_name.py, so they led back to no session. They are
# named by that tool now. The old names are still RECOGNIZED -- a branch
# already on origin, an engine copy elsewhere -- by the is_* functions below,
# the one place that answers "is this a Promote's branch".
FIX_SLUG = 'promote-fix'
COPY_SLUG = 'promote-to-main'
NOT_DUE_SLUG = 'promote-to-main-not-due'
_PROMOTE_MADE_RE = re.compile(
    r'(?:^|/)\d{4}-\d\d-\d\d-(promote-fix|promote-to-main(?:-not-due)?)'
    r'-[a-z0-9]{5}(?:-[a-z0-9]{5})?$')
# What a GitHub workflow that skips a not-due copy by its NEW name contains;
# a workflow without it knows only the old names, so the copy keeps one.
COPY_NAME_MARKER = f'-{COPY_SLUG}-'


def _promote_made(name):
    m = _PROMOTE_MADE_RE.search(str(name or ''))
    return m.group(1) if m else None


def is_fix_branch(name):
    """True for a Promote's fix branch, new name or old."""
    return str(name or '').startswith(FIX_PREFIX) or _promote_made(name) == FIX_SLUG


def is_main_copy(name):
    """True for a Promote's copy of staging, due or not, new name or old."""
    return str(name or '').startswith('to-main-') or \
        _promote_made(name) in (COPY_SLUG, NOT_DUE_SLUG)


def is_not_due_copy(name):
    """True for a copy whose pull request main's GitHub test skips."""
    return str(name or '').startswith(NOT_DUE_PREFIX) or \
        _promote_made(name) == NOT_DUE_SLUG


def _day_and_moment(root):
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_time
        return precedent_time.today(root), precedent_time.compact(root)
    except Exception:
        return 'copy', str(int(time.time()))
    finally:
        sys.path.pop(0)


def promote_branch_name(root, slug, taken):
    """-> claude/<date>-<slug>-<session ID's end> from precedent_branch_name.py
    (random characters where there is no session ID, more where the name is
    taken), or None when that tool cannot be loaded."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_branch_name as pbn
    except Exception:                                           # noqa: BLE001
        return None
    finally:
        sys.path.pop(0)
    day, _moment = _day_and_moment(root)
    name, _notes = pbn.build(slug.split('-'), date=day, exists=taken)
    return name


def _workflows_know_new_copy_names(root):
    """True when every GitHub test at staging's tip recognizes the new copy
    names (or none is installed). A repository that has not taken the
    workflow carrying them would run its test on a not-due copy, so its
    copies keep the old names until Update Vendors brings it."""
    tip = _remote_tip(root, staging_branch(root))
    if not tip:
        return False
    return all(COPY_NAME_MARKER in (_git(root, 'show', f'{tip}:{p}') or '')
               for p, _d in github_tests(root, tip))


def _to_main_copy(root, due=True):
    """The throwaway branch a pull request into main comes FROM: never
    staging itself, whose pull request page offers to delete it (gotchas/
    gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging.md). Named
    as precedent_merge_check.py's refusal names it, with a suffix when that
    name is taken -- and the not-due name instead when main's GitHub test is
    not due, which is the name the light check's job skips on. In the
    session-branch format (promote_branch_name), unless a GitHub test here
    still knows only the old names."""
    if _workflows_know_new_copy_names(root):
        name = promote_branch_name(root, COPY_SLUG if due else NOT_DUE_SLUG,
                                   lambda n: bool(_remote_tip(root, n)))
        if name:
            return name
    day, moment = _day_and_moment(root)
    prefix = 'to-main-' if due else NOT_DUE_PREFIX
    base = f'{prefix}{day}'
    return base if not _remote_tip(root, base) else f'{prefix}{moment}'


# Exit 0 from a Promote means the branch it names has moved. Into main it
# stops short -- the pull request, its GitHub test and the merge are the
# session's -- and until 2026-09-28 it still exited 0 there: a session read
# the 0 as done while main had not moved. That state has its own code now,
# distinct from a refusal (1) and a usage error (2).
PROMOTE_MAIN_NOT_MOVED = 3


def _carries_changes_of(root, tip, other):
    """True when `tip` already has every file change `other` brings: merging
    `other` into `tip` would leave `tip`'s tree as it is. A Produce's own
    merge commit on main is the common case -- it changes no file, so a
    Debut has nothing to take down and never makes staging its descendant.
    Until 2026-10-05 main_test_holds_produce asked for ancestry alone, so a
    main whose GitHub test went red without running (no runner) held every
    Produce while telling the session to Debut, and the Debut had nothing to
    do. Needs `git merge-tree --write-tree` (git 2.38); where that is
    missing, or the merge conflicts, this answers False, the old reading."""
    r = _run(root, 'merge-tree', '--write-tree', tip, other)
    if r.returncode != 0:
        return False
    merged = r.stdout.split('\n', 1)[0].strip()
    return bool(merged) and merged == _git(root, 'rev-parse', f'{tip}^{{tree}}')


def main_test_holds_produce(root, say=print, gh=None):
    """-> None when a move into main may go ahead, else why not. Main's
    GitHub test on its own tip: failing holds it, still running is waited
    for (spec/LADDER_OPT_IN_PLAN.md D10, Morgan 2026-10-02, strength:
    decided: "Produce waits until main's test passes"). No test installed,
    none on this tip, or one GitHub cannot be asked about holds nothing:
    the pull request's own test is still the last gate."""
    if not _gets_github_test(root, MAIN):
        return None
    mtip = _remote_tip(root, MAIN)
    tests = github_tests(root, mtip) if mtip else []
    if not tests:
        return None
    state, detail = github_test_state(root, mtip, tests, gh)
    if state == 'running':
        say(f'the GitHub test on {MAIN} ({mtip[:12]}) is still running; a move '
            f'into {MAIN} waits for it...')
        deadline = time.monotonic() + GITHUB_TEST_WAIT_SECONDS
        while state == 'running' and time.monotonic() < deadline:
            time.sleep(GITHUB_POLL_SECONDS)
            state, detail = github_test_state(root, mtip, tests, gh)
    if state == 'failed':
        # Staging already carries main's tip: this Produce is what repairs
        # main, and its own pull request's GitHub test is the last gate.
        # Holding it waited for a fix from someone off the ladder, who does
        # not make one (Morgan, 2026-10-03, strength: decided; narrows D10).
        staging = staging_branch(root)
        _run(root, 'fetch', '-q', 'origin', staging)
        stip = _remote_tip(root, staging)
        carried = bool(stip) and (
            _run(root, 'merge-base', '--is-ancestor', mtip, stip).returncode == 0
            or _carries_changes_of(root, stip, mtip))
        # ...checked first, never taken on trust: carrying main's commit says
        # nothing about whether the tree it makes with the ladder's work
        # passes, so the hold lifts only for a staging tip whose exact tree
        # has passed the full local check (Morgan, 2026-10-03: "Should it
        # check this first?"). The pull request's GitHub test is still the
        # last gate before the merge.
        if carried and _receipt(root, stip):
            say(f'{MAIN}\'s own GitHub test is failing on its tip ({mtip[:12]}: '
                f'{detail}). {staging} already carries that commit, and its tip '
                f'({stip[:12]}) has passed the full local check, so this Produce '
                f'goes ahead: it is what brings {MAIN} back to green, and its pull '
                f'request\'s own GitHub test is the last gate.')
            return None
        if carried:
            return (f'{MAIN}\'s own GitHub test is failing on its tip ({mtip[:12]}: '
                    f'{detail}). {staging} carries that commit, but its tip '
                    f'({stip[:12]}) has no full local check on record, so it is '
                    f'not known to repair {MAIN}. Debut first: its full check '
                    f'judges that tree, then Produce again.')
        return (f'{MAIN}\'s own GitHub test is failing on its tip ({mtip[:12]}: '
                f'{detail}), and {staging} does not carry that commit yet. Debut '
                f'first: the Promote takes {MAIN}\'s work down and checks it with '
                f'yours, then Produce again.')
    if state == 'running':
        return (f'{MAIN}\'s GitHub test on {mtip[:12]} was still running after '
                f'{GITHUB_TEST_WAIT_SECONDS // 60} minutes ({detail}); Promote '
                f'again once it finishes.')
    return None


def _promote_to_main(root, say=print, work=None):
    """Staging into main: the full check on exactly what main would hold,
    then a throwaway copy of staging for the pull request into main, whose
    GitHub test is the last gate (spec/BRANCH_TIERS_PLAN.md: main gets "all
    those local tests AND the most important GitHub test"). Main is moved by
    that pull request, never by this script. -> PROMOTE_MAIN_NOT_MOVED when
    the copy is ready and main has not moved yet; 0 nothing to promote; 1
    refused."""
    staging = staging_branch(root)
    held = main_test_holds_produce(root, say)
    if held:
        say(f'PROMOTE REFUSED: {held}')
        return 1
    # What reached main or staging by another route is checked and copied
    # down first, the same as before the step into staging.
    if not sync_pre_staging(root, say, check=True):
        return 1
    _run(root, 'fetch', '-q', 'origin', staging, MAIN)
    stip, mtip = _remote_tip(root, staging), _remote_tip(root, MAIN)
    if not stip or not mtip:
        say(f'origin lacks {staging if not stip else MAIN}, so there is nothing '
            f'to promote into {MAIN}.')
        return 1
    batch = _new_commits(root, mtip, stip)
    if not batch:
        say(f'nothing to promote: {MAIN} already has everything on {staging}.')
        return 0
    with _Worktree(root, mtip) as wt:
        m = _run(wt, 'merge', '--no-ff', '-q', '-m',
                 f'Promote {staging} into {MAIN} ({len(batch)} commit(s))',
                 stip, env=_merge_env(root))
        if m.returncode != 0:
            _run(wt, 'merge', '--abort')
            say(f'{staging} does not merge cleanly into {MAIN}; nothing was pushed. '
                f'{MAIN} has changes of its own on the same lines -- merge {MAIN} '
                f'into {PRE_STAGING}, resolve it there, and Promote again.')
            return 1
        say(f'checking {len(batch)} commit(s) from {staging} with the full push check...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, FULL, dest=MAIN)
        took = time.monotonic() - t0
    if not ok:
        say(f'PROMOTE REFUSED: the full check failed on {staging} merged into '
            f'{MAIN}, so nothing was pushed. The batch was:\n  '
            + '\n  '.join(batch) + f'\n\n{out}\n\nFix it on {PRE_STAGING} and '
            f'Promote again.')
        return 1
    reused = next((l for l in out.splitlines() if 'already passed' in l), None)
    if reused:
        say('the full check was NOT re-run: ' + reused.split(': ', 1)[-1]
            + ' Same files, so the earlier run stands.')
    else:
        say(f'the full check ran on the batch and passed, in {took:.0f}s.')
    due, why = main_test_due(root, stip)
    # No GitHub test runs on this pull request at all -- none is installed,
    # or every one is path-filtered off this change. "DUE", then "wait for
    # it", read as a test to wait on where none would ever start (2026-10-04,
    # all four shared sets and a consumer); --wait-main-test said the same.
    none_runs = not github_tests(root, stip)
    copy = _to_main_copy(root, due)
    p = _run(root, 'push', '-q', 'origin', f'{stip}:refs/heads/{copy}')
    if p.returncode != 0:
        say(f'could not push the copy {copy}: {p.stderr.strip()[:200]}')
        return 1
    shown, others = mark_other_work(root, batch, work)
    say(f'{MAIN.upper()} HAS NOT MOVED YET: this Promote exits '
        f'{PROMOTE_MAIN_NOT_MOVED}, not 0, until the pull request below is merged.\n'
        f'READY FOR {MAIN.upper()}: {len(batch)} commit(s) from {staging} '
        f'({stip[:12]}), copied to {copy}:\n  ' + '\n  '.join(shown)
        + _other_work_note(others, work) + '\n\n'
        + (f'GitHub test: NONE -- no GitHub test runs on this pull request '
           f'(none is installed here, or its path filter does not reach this '
           f'change), so the full local check above is the whole check.\n\n'
           if none_runs else
           f'GitHub test: DUE -- {why}.\n\n' if due else
           f'GitHub test: ON THE PUSH TO {MAIN.upper()} -- {why}. Its pull request '
           f'shows the test as skipped, which starts no runner and costs nothing.\n\n'
           if 'never the pull request' in why else
           f'GitHub test: NOT DUE -- {why}. Its pull request shows the test as '
           f'skipped, which starts no runner and costs nothing.\n\n') +
        f'Next, and not by this script: open a pull request from {copy} into '
        f'{MAIN}, titled "Promote {staging} into {MAIN} ({len(batch)} '
        f'commit(s))", '
        + (f'and merge it with a merge commit{_at_head(stip)}' if none_runs else
           f'wait for its GitHub test with\n'
           f'  python3 tools/precedent_branches.py --wait-main-test {copy}\n'
           f'and merge it with a merge commit once that says PASSED'
           + ('' if due else ' (or, for this not-due copy, NOT DUE)')
           + _at_head(stip)) +
        f'. Never open it from {staging} itself.')
    return PROMOTE_MAIN_NOT_MOVED


# THE PROMOTE INTO STAGING COMPOSES, CHECKS ONCE, THEN MOVES BOTH TIERS
# (spec/LADDER_OPT_IN_PLAN.md D10, Morgan 2026-10-03, strength: decided).
# The ladder is opt-in, so people off it push straight to main, and that is
# expected to go on. Their work is live for everyone already; what the
# ladder must not do is take it into pre-staging unchecked, or leave it out
# until the next Produce meets it as a conflict. So this step builds one
# tree in a scratch worktree -- staging, then main's new work, then
# pre-staging's -- rebuilds what main left stale, runs the full check on it
# once, and only then moves staging AND pre-staging to that same commit.
#
# A failure moves neither. The tree is put on a LOCAL fix branch (pushed
# only with a fix, 2026-10-06; see _not_finished), and the
# session fixes it there in the same turn, whoever's commit broke it ("if
# it fails because of a problem on main (caused by someone not using this
# process) -- then you have to fix it as part of this process"), and runs
# this again with --work FIX-BRANCH, which takes the fix in first.
FIX_PREFIX = 'promote-fix-'


def _fix_branch(root):
    """A fresh fix-branch name, in the session-branch format: e.g.
    claude/2026-10-06-promote-fix-y1ktn (promote_branch_name says why).
    The old promote-fix-DATE only where the naming tool cannot be loaded."""
    def taken(name):
        return bool(_remote_tip(root, name)) or _run(
            root, 'rev-parse', '--verify', '-q', f'refs/heads/{name}').returncode == 0
    name = promote_branch_name(root, FIX_SLUG, taken)
    if name:
        return name
    day, moment = _day_and_moment(root)
    base = f'{FIX_PREFIX}{day}'
    return base if not taken(base) else f'{FIX_PREFIX}{moment}'


def _branches_page(root, name):
    """-> the GitHub branches page filtered to `name`, or '' off GitHub."""
    slug = _slug(root)
    return f' (https://github.com/{slug}/branches/all?query={name})' if slug else ''


def _compose(root, wt, parts, staging, say):
    """Merge each (label, sha, message) in `parts` into worktree `wt`'s HEAD,
    in order, by merge commits. One already in HEAD is skipped; a conflict
    only in generated files is rebuilt (_resolve_by_regenerating).
    -> (None, merged labels) or ((label, sha, files), merged) on a conflict
    in hand-written text, the merge aborted and HEAD left as it was before
    it."""
    env = _merge_env(root)
    merged = []
    for label, sha, message in parts:
        if _run(wt, 'merge-base', '--is-ancestor', sha, 'HEAD').returncode == 0:
            continue
        m = _run(wt, 'merge', '--no-ff', '-q', '-m', message, sha, env=env)
        if m.returncode != 0:
            done, files = _resolve_by_regenerating(wt, say)
            if done:
                done = _run(wt, 'commit', '-q', '--no-edit', env=env).returncode == 0
            if not done:
                _run(wt, 'merge', '--abort')
                return (label, sha, files), merged
            say(f'{label} and the rest both changed {", ".join(files)}; generated, '
                f'so rebuilt from the merged sources rather than either side taken.')
        merged.append(label)
    return None, merged


def _commit_rebuilt(root, wt, say, why):
    """Rebuild the generated files in `wt` and commit any that changed.
    -> the files rebuilt."""
    rebuilt = _rebuild_generated(wt, say)
    if rebuilt:
        _run(wt, 'add', '-u')
        _run(wt, 'commit', '-q', '-m', f'Rebuild generated files {why}\n\n'
             + '\n'.join(rebuilt), env=_merge_env(root))
    return rebuilt


def _promote_unlocked(root, say=print, work=None):
    """Pre-staging into staging, composed with whatever reached main or
    staging by another route, fully checked once, both tiers moved level.
    `work` is the branch the session was on; a FIX_PREFIX branch is the fix
    for an earlier unfinished run and is taken in first. -> 0 promoted or
    nothing to promote; 1 refused or not finished (a failing check, a
    conflict, a race)."""
    staging = staging_branch(root)
    if not _remote_tip(root, PRE_STAGING) and not sync_pre_staging(root, say):
        return 1
    _run(root, 'fetch', '-q', 'origin', staging, PRE_STAGING)
    stip, ptip = _remote_tip(root, staging), _remote_tip(root, PRE_STAGING)
    if not stip or not ptip:
        say(f'origin lacks {staging if not stip else PRE_STAGING}, so there is '
            f'nothing to promote.')
        return 1
    above = []
    for branch in ((MAIN,) if staging != MAIN else ()) + (
            (LEGACY_STAGING,) if staging != LEGACY_STAGING else ()):
        tip = _remote_tip(root, branch)
        if tip:
            _run(root, 'fetch', '-q', 'origin', branch)
            commits = drift(root, stip, tip)
            if commits:
                above.append((branch, tip, commits))
    fix = None
    if work:
        name = work[len('origin/'):] if work.startswith('origin/') else work
        _run(root, 'fetch', '-q', 'origin', name)
        sha = (_git(root, 'rev-parse', '--verify', '--quiet', f'origin/{name}^{{commit}}')
               or _git(root, 'rev-parse', '--verify', '--quiet', f'{work}^{{commit}}'))
        if sha and is_fix_branch(name):
            fix = (name, sha)
        elif sha and not any(_run(root, 'merge-base', '--is-ancestor', sha,
                                  t).returncode == 0 for t in (ptip, stip)):
            say(f'NOTE: {work} is not on {PRE_STAGING}, so this Promote does not '
                f'carry it. Book it onto {PRE_STAGING} first, then Promote again.')
    batch = _new_commits(root, stip, ptip)
    parts = []
    if fix:
        parts.append((fix[0], fix[1], f'Merge {fix[0]} into {staging}: the fix '
                      f'for an unfinished Promote'))
    for branch, tip, commits in above:
        parts.append((branch, tip, f'Bring {branch} into {staging}: {len(commits)} '
                      f'commit(s) made there directly'))
    parts.append((PRE_STAGING, ptip, f'Promote {PRE_STAGING} into {staging} '
                   f'({len(batch)} commit(s))'))
    staging_brings = not _brings_nothing(root, ptip, stip)
    if not fix and not above and _run(root, 'merge-base', '--is-ancestor', ptip,
                                      stip).returncode == 0 and not staging_brings:
        say(f'nothing to promote: {staging} already has everything on {PRE_STAGING}.')
        return 0
    from_above = '; '.join(f'{b}\'s {len(c)} commit(s)' for b, _, c in above)
    with _Worktree(root, stip) as wt:
        conflict, merged = _compose(root, wt, parts, staging, say)
        rebuilt = []
        if not conflict and above:
            rebuilt = _commit_rebuilt(root, wt, say, f'after {from_above} '
                                      f'made directly')
        new = _git(wt, 'rev-parse', 'HEAD')
        if conflict:
            label, sha, files = conflict
            return _not_finished(root, say, new, staging, (
                f'{label} ({sha[:12]}) does not merge cleanly into '
                f'{" + ".join([staging] + merged)}: the same lines of hand-written '
                f'text changed on both sides'
                + (f' ({", ".join(files)})' if files else '') + '.'),
                f'merge {label} into it -- git merge {sha} -- and resolve it')
        say(f'checking the composition -- {staging}'
            + (f', then {fix[0]}' if fix else '')
            + (f', then {from_above} made directly' if above else '')
            + f', then {len(batch)} commit(s) from {PRE_STAGING} -- with the full '
            f'push check...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, FULL, dest=staging)
        took = time.monotonic() - t0
        if not ok:
            where = _where_it_fails(root, stip, above, staging)
            return _not_finished(root, say, new, staging, (
                f'the full check failed on the composition, after {took:.0f}s.'
                + (f'\n{where}' if where else '') + f'\n\n{out}'),
                'fix what failed there, whoever\'s commit it came from')
        refs = ([f'{new}:refs/heads/{staging}'] if new != stip else []) + (
            [f'{new}:refs/heads/{PRE_STAGING}'] if new != ptip else [])
        if not refs:
            say(f'nothing to promote: {staging} and {PRE_STAGING} are level.')
            return 0
        p = _run(wt, 'push', '--atomic', '-q', 'origin', *refs)
        if p.returncode != 0 and 'does not support --atomic' in p.stderr:
            # A remote that cannot take both in one push: staging first, so
            # a refused second push leaves pre-staging behind, never ahead.
            p = _run(wt, 'push', '-q', 'origin', refs[0])
            if p.returncode == 0 and len(refs) > 1:
                p = _run(wt, 'push', '-q', 'origin', refs[1])
    if p.returncode != 0:
        return _raced(root, say, staging, stip, ptip, new, p)
    reused = next((l for l in out.splitlines() if 'already passed' in l), None)
    if reused:
        say('the full check was NOT re-run: ' + reused.split(': ', 1)[-1]
            + ' Same files, so the earlier run stands.')
    else:
        say(f'the full check ran on the batch and passed, in {took:.0f}s.')
    if batch:
        shown, others = mark_other_work(root, batch, work)
        say(f'PROMOTED {len(batch)} commit(s) from {PRE_STAGING} into {staging} '
            f'({new[:12]}):\n  ' + '\n  '.join(shown)
            + _other_work_note(others, work))
    for branch, _tip, commits in above:
        say(f'BROUGHT IN {len(commits)} commit(s) made directly on {branch}, '
            f'checked with the rest:\n  ' + '\n  '.join(commits))
    if rebuilt:
        say(f'REBUILT what those left stale: {", ".join(rebuilt)}.')
    if fix:
        say(f'TOOK IN {fix[0]}, the fix for the last unfinished Promote. It has '
            f'done its job{_branches_page(root, fix[0])}.')
    if not batch and not above and not fix:
        say(f'PROMOTED nothing new: {staging} had changes {PRE_STAGING} lacked, '
            f'and they passed the full check.')
    say(f'{staging} and {PRE_STAGING} are both at {new[:12]} now.')
    _mirror_legacy(root, staging, new, say)
    return 0


def _where_it_fails(root, stip, above, staging):
    """After the composition failed the full check: -> where to look first,
    from what is on record, or '' when nothing came from above. Never a
    verdict. Checking staging with main's work alone used to settle it, at
    the cost of a second full check -- on 2026-10-03 the two took about 24
    minutes, past the Promote lock's 15, and still blamed main for a test
    that failed on staging's own tip in that container. The session
    measures it on the fix branch instead (practice: diagnosis-is-measured),
    where running only what failed on each tip takes seconds."""
    if not above:
        return ''
    names = ' and '.join(b for b, _, _ in above)
    listed = '\n  '.join(c for _b, _t, cs in above for c in cs)
    rec = _receipt(root, stip)
    if rec:
        return (f'{staging}\'s own tip passed the full check '
                f'({rec.get("at", "time not recorded")}), and {names} brought these '
                f'commits, made without the ladder\'s checks:\n  {listed}\nLook '
                f'there first, then at how they meet {PRE_STAGING}\'s work; run '
                f'what failed on each tip before saying which it was.')
    return (f'{names} brought these commits, made without the ladder\'s '
            f'checks:\n  {listed}\n{staging}\'s own tip has no full check on record '
            f'either, so the failure may be on {staging} already; run what failed '
            f'on {staging} alone first.')


def _not_finished(root, say, sha, staging, what, todo):
    """Put the composition `sha` on a fresh LOCAL fix branch, say what stopped
    it and how the session finishes it, and -> 1. Neither tier has moved.

    LOCAL, NOT PUSHED (2026-10-06). It used to be pushed at once, so every
    refused Promote left a branch on origin -- one consumer had four by the
    next day, all already contained in staging, each for a person to delete
    by hand -- including the many refusals that are fixed on pre-staging and
    never touch the fix branch at all. The composition can always be made
    again, so nothing is lost if the container goes; it reaches origin only
    when the session pushes a fix to it."""
    fix = _fix_branch(root)
    b = _run(root, 'branch', fix, sha)
    if b.returncode != 0:
        say(f'PROMOTE NOT FINISHED, and neither {staging} nor {PRE_STAGING} '
            f'moved: {what}\n\nThe composition could not be put on a fix '
            f'branch either ({b.stderr.strip()[:200]}); run the Promote again.')
        return 1
    say(f'PROMOTE NOT FINISHED, and neither {staging} nor {PRE_STAGING} moved: '
        f'{what}\n\nThe composition is on the local branch {fix} ({sha[:12]}), '
        f'not pushed: a fix made on {PRE_STAGING} instead leaves nothing behind '
        f'on origin. Finish it in this same turn: on {fix}, {todo}; push it '
        f'with `git push -u origin {fix}`; then\n'
        f'  python3 tools/precedent_branches.py --promote --to staging --work {fix}\n'
        f'which takes the fix in first and moves both tiers together.')
    return 1


def _raced(root, say, staging, stip, ptip, new, p):
    """The push of a checked composition was refused: say why, -> 0 when the
    work is on staging anyway, else 1. Nothing was pushed (the push is
    atomic) -- or, on a remote without atomic pushes, staging alone."""
    _run(root, 'fetch', '-q', 'origin', staging, PRE_STAGING)
    now_s, now_p = _remote_tip(root, staging), _remote_tip(root, PRE_STAGING)
    if now_s == new:
        say(f'{staging} moved to the checked composition ({new[:12]}), but '
            f'{PRE_STAGING} gained work while the check ran, so it was not '
            f'moved; the next Promote levels it.')
        return 0
    if now_s != stip:
        # Most often another window promoted the same batch while this one
        # was checking it. Then there is nothing left to do, and "Promote
        # again" would only send the person round a second time for work
        # already on staging (2026-09-25: two sessions raced this way twice
        # in a row, each told to try again).
        if now_s and _run(root, 'merge-base', '--is-ancestor', ptip,
                          now_s).returncode == 0:
            say(f'another window promoted this batch while the check ran: '
                f'{staging} ({now_s[:12]}) already has everything that was on '
                f'{PRE_STAGING}. Nothing was pushed, and there is nothing '
                f'left to promote.')
            return 0
        say(f'{staging} moved while the check ran, so nothing was pushed; '
            f'Promote again. ({p.stderr.strip()[:200]})')
        return 1
    if now_p != ptip:
        say(f'{PRE_STAGING} gained work while the check ran, so nothing was '
            f'pushed; Promote again to take it in too. ({p.stderr.strip()[:200]})')
        return 1
    say(f'the push was refused, so nothing moved: {p.stderr.strip()[:300]}')
    return 1


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
    if argv[:1] == ['--sync-pre-staging'] and set(argv[1:]) <= {'--check'}:
        return 0 if sync_pre_staging(root, check='--check' in argv) else 1
    if argv == ['--drift']:
        _run(root, 'fetch', '-q', 'origin', PRE_STAGING, staging_branch(root), MAIN)
        for line in drift_report(root):
            print(line)
        return 0
    if argv[:1] == ['--promote']:
        rest, opts = argv[1:], {}
        while len(rest) >= 2 and rest[0] in ('--to', '--work'):
            opts[rest[0][2:]] = rest[1]
            rest = rest[2:]
        if rest or opts.get('to', STAGING) not in (STAGING, MAIN):
            print('usage: precedent_branches.py --promote [--to staging|main] '
                  '[--work BRANCH-OR-COMMIT]', file=sys.stderr)
            return 2
        return promote(root, to=opts.get('to'), work=opts.get('work'))
    if argv[:1] == ['--wait-main-test'] and len(argv) == 2:
        _run(root, 'fetch', '-q', 'origin', argv[1])
        sha = (_git(root, 'rev-parse', '--verify', '--quiet', f'origin/{argv[1]}^{{commit}}')
               or _git(root, 'rev-parse', '--verify', '--quiet', f'{argv[1]}^{{commit}}'))
        if not sha:
            print(f'precedent_branches: {argv[1]} names no branch or commit here.',
                  file=sys.stderr)
            return 2
        return wait_for_main_test(root, sha, copy=argv[1])
    if argv[:1] == ['--ensure-tiers'] and set(argv[1:]) <= {'--apply'}:
        return ensure_tiers(root, apply='--apply' in argv)
    tier, why = branch_push_checks(root)
    landing, lwhy = landing_branch(root)
    if ladder_in_force(root) is False or not repo_has_tiers(root):
        # Off the ladder there are no tiers to list (spec/LADDER_OPT_IN_PLAN.md
        # D3), and a repository without them has none to list for anyone:
        # the main branch, how pushes are checked, where work lands.
        print(f'main         {MAIN}')
        print(f'checked fully: {MAIN}')
        print(f'every other branch: {tier} ({why})')
        print(f'your work lands on: {landing} ({lwhy})')
        return 0
    print(f'pre-staging  {PRE_STAGING}')
    print(f'staging      {staging_branch(root)}')
    print(f'main         {MAIN}')
    print(f'always checked fully: {", ".join(sorted(full_branches(root)))}')
    print(f'every other branch: {tier} ({why})')
    print(f'Booked (Go update) lands on: {landing} ({lwhy})')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    try:
        sys.exit(_main(sys.argv[1:]))
    except CommitRefused as exc:
        print(f'REFUSED: no commit was made and nothing was pushed -- {exc}',
              file=sys.stderr)
        sys.exit(1)
