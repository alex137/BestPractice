#!/usr/bin/env python3
"""Where a person's work lands here (spec/LADDER_OPT_IN_PLAN.md D3) and whether a push to a branch gets the basic or the full push check; the branch tiers and their moves for a person whose set provides them (spec/BRANCH_TIERS_PLAN.md)

precedent_branches.py -- the branch tiers, staging and main, and what a
push to each one is checked with. spec/BRANCH_TIERS_PLAN.md is the plan
this implements.

WHAT A PUSH GETS (Morgan, 2026-10-17, strength: decided: main and staging
both take the quick checks before a push; the full suite runs at the Debut,
`--run-tests`, and after a push into main):

  staging, and any other branch   the person's branch_push_checks, basic
                                  by default (markdown lint, leak gate,
                                  the commit-author checks)
  main                            the quick checks; the full suite after

WHY ONE MODULE. The literal `precedent-beta-v01` sat in 249 files of this
repository when the plan was written, 37 of them under tools/. The same
names are meant to hold in every repository, and the staging branch was
renamed; every tool that needs a tier name asks here, so a rename is a
change in one place (practice: registry-source-of-truth).

STAGING BEFORE A STAGING BRANCH. Until a repository has a branch called
`staging`, its staging tier is whatever it declares as `base_branch` in
precedent.json. A repository whose base_branch is `main` -- most
repositories that install Precedent -- has no separate staging branch, so
its staging tier IS main, and `Go update` lands on main, as it always did.

A PUSH NOBODY CAN READ IS CHECKED FULLY. push_targets() returns None for a
push whose destination it cannot establish (--all, --mirror, --tags, a tag
refspec, a detached HEAD), and tier_for_push() answers `full` for None.
Getting it wrong in that direction costs minutes; the other direction
lands unchecked work.

The person's setting, `branch_push_checks`, is read the way
spec/CI_CADENCE_PLAN.md reads its own: a repository's precedent.json wins,
then the person's identity.json (this repository's own when it is an
individual source, else the one ~/.config/precedent/config.json names),
then the default, `basic`.

WHERE `Go update` LANDS is `landing_branch`: `staging` or `main`. Read in
the OTHER order from `branch_push_checks`: the person's own identity.json
first, then the repository's precedent.json, then the built-in default,
`staging` (Morgan, 2026-09-27, strength: decided: "have the individual repo
take precedence over the others (if it set, use that)"). Where a person
works is theirs to choose; a repository's value is its default for everyone
who has not. New repositories are written with `staging`, and Update
Vendors adds it to one that has none. A value that is neither is not used,
and --land refuses on it by name (unknown_landing), never sending work
somewhere new.

--land PUTS WORK ON STAGING: it composes staging, then what reached main
directly, then the work, each by a merge commit in a throwaway worktree,
runs the quick checks, and pushes staging, never forced (see LAND_RESULT).

PROMOTE MOVES STAGING INTO MAIN (promotion_step). It prints "Now promoting
from X to Y" before anything else, runs the check on staging merged into
main, then pushes a throwaway copy of staging for the pull request into
main; that pull request's GitHub test is main's last gate, so main itself
is never pushed from here. That state exits 3 (PROMOTE_MAIN_NOT_MOVED), not
0, and says first that main has not moved: exit 0 means the branch moved.
A failure or a conflict nothing here rebuilds moves nothing: the tree goes
to a local DATE-promote-fix-ID branch (promote-fix-DATE before 2026-10-06,
still recognized), to be fixed there and promoted with --work
(spec/LADDER_OPT_IN_PLAN.md D10; see the comment above _promote_unlocked).
It pushes by itself, so it runs the check by itself: no push gate sees a
push made from inside a script.

EVERY PROMOTE ENDS WITH ONE RESULT LINE (2026-10-08). Whatever path a run
takes -- moved, nothing to move, refused, not finished, ready for main's
pull request, or stopped by an error -- the last line it prints is

  PROMOTE RESULT: <to> <- <from>: <verdict>

with any commit in it written in full. A session reads that one line from
the command's own output: a consuming repository's session that wrote a
Debut's log to a file was refused the `tail` that would have read it back,
and could not say whether the Debut had worked.

IN A PRIVATE REPOSITORY THAT GITHUB TEST RUNS AT MOST ONCE EVERY
github_ci_every_hours (2026-10-01, spec/CI_CADENCE_PLAN.md, "Promote
decides"; see main_test_due). When it is not due, the copy is named
DATE-promote-to-main-not-due-ID (to-main-not-due-DATE before
2026-10-06, and still where a GitHub test knows only that), the light check's job skips that pull request before
a runner starts, and --wait-main-test says NOT DUE and exits 0.

CLI:
  precedent_branches.py                     the tiers, as this repo resolves them
  precedent_branches.py --tier BRANCH       prints `basic` or `full`
  precedent_branches.py --push ARGS...      the tier a `git push ARGS...` gets
  precedent_branches.py --landing           where `Go update` lands for this person
  precedent_branches.py --wait-main-test COPY
                                            wait for main's GitHub test on the to-main
                                            copy's pull request; 0 only when it passed,
                                            or when the copy is a not-due one
  precedent_branches.py --promote [--to main] [--work BRANCH]
                                            staging into main, the fast way (below);
                                            says so first. 0 moved or nothing to
                                            move, 1 refused, 3 main not moved yet
                                            (its pull request is still to open and
                                            merge)
  precedent_branches.py --promote --to main [--despite-failed-tests] [--no-full-after]
                                            staging into main with the quick checks
                                            only, the default (Morgan, 2026-10-11);
                                            GitHub's test runs after the merge,
                                            or, when it is not due, the full local
                                            suite on main here (full_check_after);
                                            --no-full-after when the person asked
                                            for a fast one. --fast is still taken.
  precedent_branches.py --promote --to main --full --because '<their words>'
                                            the long route, only when the person asks
                                            for it or agrees to it, in their own
                                            words (refused without --because): the
                                            full local suite, then GitHub's test
                                            before the merge
                                            4 (PROMOTE_ASKS) when --run-tests failed on
                                            staging's current commit: ask the person,
                                            and on a yes add --despite-failed-tests
  precedent_branches.py --land [BRANCH]     for a person who lands on staging: BRANCH
                                            (default HEAD) onto staging, composed
                                            with main's direct work, quick checks
  precedent_branches.py --run-tests [BRANCH]
                                            the full local suite on BRANCH (default:
                                            the landing branch) with main's direct
                                            work, moving nothing; recorded for the
                                            fast move into main. 0 passed, 1 failed
  precedent_branches.py --ensure-tiers [--apply]
                                            report (or make) a real staging branch
                                            on origin
"""
import calendar
import fnmatch
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import time

STAGING = 'staging'
# The staging branch's name until 2026-09-25, in the Precedent repositories.
# Promote stopped keeping it in step on 2026-10-11, when Morgan retired it
# (todo-2026-09-26-retire-precedent-beta-v01). The name is still recognized
# as a tier and never offered for deletion, because an install may still
# declare it as its base branch until its next Update Vendors renames it.
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
# chosen otherwise. A repository carries its own default too
# (REPO_LANDING_DEFAULT), below the person and above this one: Morgan,
# 2026-09-27, "have the Precedent one default to staging".
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


# What a repository says when it has not been told otherwise: staging.
# Written into precedent.json at install, into a new practice set, and by
# Update Vendors into a repository that has no value of its own (Morgan,
# 2026-09-27, strength: decided). It sits BELOW the person (landing_branch()
# reads identity.json first), so it is a default, never an override of
# somebody's own choice.
REPO_LANDING_DEFAULT = STAGING
REPO_LANDING_COMMENT = [
    'Where Go update lands for anyone whose own identity.json names no',
    'landing_branch -- a person\'s own setting always wins. staging: work',
    'lands there with the quick checks and reaches main by a Produce.',
    'Change it here for this repository.',
]

def repo_landing_default(root, user_config=None):
    """-> (branch, comment) a new install, or a repository given its first
    landing_branch, writes into precedent.json: REPO_LANDING_DEFAULT,
    staging."""
    return REPO_LANDING_DEFAULT, REPO_LANDING_COMMENT


def ensure_repo_landing(root, new_install=False, user_config=None):
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
    landing, comment = repo_landing_default(root, user_config)
    text = path.read_text(encoding='utf-8')
    body = text.rstrip()
    added = (f',\n  "{LANDING_SETTING}": {json.dumps(landing)},\n'
             f'  "_{LANDING_SETTING}_comment": [\n'
             + ',\n'.join('    ' + json.dumps(line) for line in comment)
             + '\n  ]\n}\n')
    candidate = body[:-1].rstrip() + added if body.endswith('}') else None
    try:
        if candidate is None or json.loads(candidate).get(LANDING_SETTING) \
                != landing:
            raise ValueError
    except ValueError:
        data[LANDING_SETTING] = landing
        data['_' + LANDING_SETTING + '_comment'] = comment
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
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    declared = base_branch(root)
    if declared == MAIN and precedent_json(root).get(LANDING_SETTING) == STAGING \
            and _origin_has(root, STAGING):
        # Main is never the staging tier of a repository that lands on a
        # staging branch origin has (2026-10-14): precedent-shared-ladder
        # declared base_branch main and landing_branch staging, and
        # --landing printed "main" above its own reason line naming
        # staging, and --land then refused.
        return STAGING
    if declared:
        return declared
    return STAGING


def _origin_has(root, branch):
    """True when this clone has origin's `branch` as a remote-tracking ref."""
    try:
        return subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', '-q',
                               f'refs/remotes/origin/{branch}'],
                              capture_output=True, text=True).returncode == 0
    except OSError:
        return False


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
    """-> (tier, why) for a push to `branch`. Staging takes the quick checks:
    work lands there, and the full suite is asked for with --run-tests.

    MAIN TAKES THE QUICK CHECKS TOO, and the full suite runs after the push
    (Morgan, 2026-10-17, strength: decided: "remove, the full tests should
    happen after that"; 2026-10-16: "all the testing EXCEPT THE BARE
    ESSENTIAL AND LEAK GATES SHOULD GO INTO DEBUT, AND THE GITHUB TEST AFTER
    THE NEXT PRODUCE"). This reaches the pre-push gate and the merge gate for
    a pull request into main; Produce's --full route still runs the full
    suite first, on the person's own words."""
    if branch == MAIN:
        return BASIC, (f'a push to {MAIN} gets the quick checks; the full suite '
                       f'runs after it -- GitHub\'s test, or `python3 '
                       f'tools/precedent_branches.py --run-tests {MAIN}` where '
                       f'that is not due')
    if branch in tier_branches(root):
        # Staging, under whichever name the repository gives it, takes what
        # every other branch takes (Morgan, 2026-10-17, strength: decided).
        # Work lands here; the full suite runs when asked for, with
        # --run-tests (the Debut), or before the push for a person whose
        # branch_push_checks says full.
        tier, why = branch_push_checks(root, user_config)
        return tier, (f'{branch} is where work lands, so a push there gets '
                      f'what any branch gets ({why}); the full suite runs '
                      f'when asked for, with --run-tests')
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
    """True when this repository has tiers: precedent.json names a
    landing_branch other than main, a staging base_branch, or a
    staging_branch of its own. A repository with none of these has only its
    main branch, and nothing here gives it more. A landing_branch this
    engine does not know still counts: the repository asked for tiers, and
    --land refuses it by name (unknown_landing) rather than sending work to
    main."""
    data = precedent_json(root)
    value = data.get(LANDING_SETTING)
    if isinstance(value, str) and value.strip() and value != MAIN:
        return True
    if base_branch(root) in (STAGING, LEGACY_STAGING):
        return True
    explicit = data.get(STAGING_KEY)
    return isinstance(explicit, str) and bool(explicit.strip())


def landing_branch(root, user_config=None):
    """-> (branch, why): where this person's work lands
    (spec/LADDER_OPT_IN_PLAN.md D3, Morgan 2026-10-02, strength: decided).

    1. The person's own landing_branch, else the repository's main branch.
    2. A tier value -- staging, the person's or the repository's -- counts
       only while the ladder is in force for this
       person AND the repository declares tiers. Otherwise it is ignored and
       never edited: a person off the ladder has no tiers, and a ladder user
       never creates them in a repository that did not ask for them.
    3. On the ladder, in a repository with tiers: the person, then the
       repository, then staging. A value that is neither staging nor main
       is not used, and --land refuses until it is fixed (unknown_landing).

    With no tools/precedent_ladder.py beside this file, the order from before
    the ladder became opt-in: the person, the repository, DEFAULT_LANDING."""
    ladder = ladder_in_force(root, user_config)
    if ladder is not None:
        return _landing_by_ladder(root, ladder, user_config)
    value, where = person_first_setting(root, LANDING_SETTING, user_config)
    if value is None:
        tier, why = DEFAULT_LANDING, f'{LANDING_SETTING} is not set; the default is {DEFAULT_LANDING}'
    elif value in (STAGING, MAIN):
        tier, why = value, f'{LANDING_SETTING} is "{value}" in {where}'
    else:
        tier, why = STAGING, (f'{LANDING_SETTING} is {value!r} in {where}, which '
                              f'is neither "staging" nor "main" -- '
                              f'landing on staging, as before the tiers')
    if tier == MAIN:
        # Straight to main is a person's choice to make (Morgan, 2026-09-25:
        # "they have to be able to set it to \"main\" if they want"). It
        # skips staging, never the checks: a push to main takes the quick
        # checks and its full suite runs after (tier_for_branch, 2026-10-17). A repository's own rule about main -- this
        # one's needs the person to name main in the request -- still
        # decides whether a session may push there.
        return MAIN, why
    return staging_branch(root), why


def unknown_landing(root, user_config=None):
    """-> a sentence when the person's identity.json or this repository's
    precedent.json sets a landing_branch that is neither staging nor main,
    else None. landing_branch() passes over such a value; --land refuses on
    it, so work never goes somewhere the setting did not mean. Update
    Vendors' migrations rewrite a value the engine has dropped."""
    found = []
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email') and LANDING_SETTING in ident:
            found.append((ident[LANDING_SETTING], str(path)))
            break
    if LANDING_SETTING in precedent_json(root):
        found.append((precedent_json(root)[LANDING_SETTING],
                      "this repo's precedent.json"))
    for value, where in found:
        if value not in (STAGING, MAIN):
            return (f'{LANDING_SETTING} is {value!r} in {where}, a branch this '
                    f'engine does not know. Run Update Vendors, which moves it, '
                    f'or set it to "{STAGING}" or "{MAIN}"')
    return None


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
    if person is not None and person not in (STAGING, MAIN):
        person = None                     # unknown: as if it were not set
    if person == MAIN:
        return MAIN, f'{LANDING_SETTING} is "main" in {where}'
    if person == STAGING:
        if tiers:
            return staging_branch(root), (f'{LANDING_SETTING} is "{person}" in '
                                          f'{where}')
        return MAIN, (f'{LANDING_SETTING} is "{person}" in {where}, a branch '
                      f'this repository does not use for you, so work lands '
                      f'on {MAIN}')
    if tiers:
        if repo == STAGING:
            return staging_branch(root), (f'{LANDING_SETTING} is "{repo}" in '
                                          f"this repo's precedent.json")
        if repo is not None:
            return staging_branch(root), (f'{LANDING_SETTING} is {repo!r} in '
                                          f"this repo's precedent.json, which "
                                          f'this engine does not know, so it '
                                          f'reads as {STAGING}; --land refuses '
                                          f'until it is fixed')
        return staging_branch(root), (f'{LANDING_SETTING} is not set in this '
                                      f"repo's precedent.json; the default "
                                      f'is {STAGING}')
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
# through a tier below it -- sessions committing on the main checkout the
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


# LANDING STRAIGHT ON STAGING (2026-10-09, Morgan, strength: decided). A
# person whose landing_branch is the staging tier AND who has promote_only
# on means "my work lands on staging, and main still takes it only by
# promotion". promote_only off, or a landing branch of main, reads as
# before.
#
# Staging is reconciled with main on every landing (Morgan, 2026-10-09:
# "make sure that staging doesn't change what it does now, in reconciling
# the versions sent directly to main with our staging"). --land composes
# (_compose_onto): staging, then what reached main directly, then the
# work. A plain push or a pull request
# into staging is let through only when what it lands already carries
# everything main has (main_work_missing), so nothing that reached main
# directly is ever left out of staging.
def lands_on_staging(root, user_config=None):
    """-> (on, why): this person lands work straight on the staging tier --
    promote_only is on and their landing branch is staging, in a repository
    whose staging tier is a branch of its own. (False, None) otherwise."""
    on, _where = promote_only(root, user_config)
    if not on:
        return False, None
    staging = staging_branch(root)
    if staging == MAIN:
        return False, None
    landing, why = landing_branch(root, user_config)
    if landing != staging:
        return False, None
    return True, why


def changed_since_for(root, targets, user_config=None):
    """-> the ref a quick-checked landing on a tier is measured from, or
    None: origin/<staging> for a push into staging by a person who lands
    there (lands_on_staging)."""
    targets = set(targets or ())
    staging = staging_branch(root)
    if staging in targets and lands_on_staging(root, user_config)[0]:
        return f'origin/{staging}'
    return None


def main_work_missing(root, sha):
    """-> one line per commit on origin's main that brings `sha` a file
    change it lacks; [] when `sha` already carries all of main's work, or
    when main cannot be read. Fetches main first."""
    if not sha:
        return []
    _run(root, 'fetch', '-q', 'origin', MAIN)
    mtip = _remote_tip(root, MAIN)
    if not mtip or _git(root, 'cat-file', '-t', mtip) != 'commit':
        return []
    return drift(root, sha, mtip)


def _pushed_commit(root, args, dest):
    """-> the commit a `git push <args>` sends to branch `dest`, or None
    when it cannot be read."""
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
        if a in _VALUED:
            skip = True
            continue
        if not a.startswith('-'):
            positional.append(a)
    specs = positional[1:] or ['HEAD']
    for spec in specs:
        if _dest_of(root, spec) != dest:
            continue
        src = spec.lstrip('+').split(':', 1)[0] or None
        if src is None:
            return None
        return _git(root, 'rev-parse', '--verify', '--quiet', f'{src}^{{commit}}')
    return None


LAND_COMMAND = 'python3 tools/precedent_branches.py --land'


def _promotion_heads(root, base):
    """The branches allowed to be merged into `base` when promote_only is on:
    the tier directly below it."""
    if base == MAIN:
        return {staging_branch(root), STAGING, LEGACY_STAGING} - {MAIN}
    # Staging takes work by --land, never by merging a tier below it: there
    # is none.
    return set()


def _push_remote(root, args):
    """-> the remote a `git push <args>` writes to: its first positional
    argument, else the current branch's configured remote, else origin."""
    if isinstance(args, str):
        try:
            args = shlex.split(args)
        except ValueError:
            return 'origin'
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in _VALUED:
            skip = True
            continue
        if not a.startswith('-'):
            return a
    branch = _run(root, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    configured = _run(root, 'config', f'branch.{branch}.remote').stdout.strip()
    return configured or 'origin'


def _remote_is_empty(root, remote):
    """True only when the remote answers and holds no branch at all: a
    brand-new repository, whose first landing creates main.

    Practice promote-only's first-install exception (Morgan, 2026-10-08:
    "Why not install it straight to main?") lets that one push through, and
    until 2026-10-08 this gate refused it like any other. Kept to an empty
    remote on purpose: once anything is there, an existing main (even a
    README-only one) or a missing staging beside it, the push is refused as
    before. A remote that cannot be asked (no network, no such remote)
    answers False, so the push stays refused."""
    try:
        r = subprocess.run(['git', '-C', str(root), 'ls-remote', '--heads',
                            remote],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):  # practice: fail-gracefully
        return False
    return r.returncode == 0 and not r.stdout.strip()


def content_only(root, sha):
    """promote-only's content exception: True when every file `sha` changes,
    from where it parted from main's tip, is under precedent.json's
    `content_paths` -- the person's own material, such as a personal to-do
    list. Such a change goes straight into main, and staging takes it from
    there the usual way (main_work_missing; --land brings main's direct
    work in first). Anything else in the change, precedent.json included,
    and it is refused as before.

    Why (Morgan, 2026-10-13, strength: decided, relayed by a personal to-do
    repository's session): "since the "Add" is just PURE CONTENT, it
    shouldn't need to go through staging ... I just want to update lists
    quickly and easily." Nothing declared, nothing read, or nothing changed:
    False, so the gate stays as strict as before."""
    try:
        here = str(pathlib.Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import precedent_resolve as _pr
        declared = _pr.declared_content_paths(root)
        inside = _pr.in_declared_paths
    except Exception:                                       # noqa: BLE001
        return False
    if not declared or not sha:
        return False
    base = _remote_tip(root, MAIN) or _git(root, 'rev-parse', '--verify', '-q', MAIN)
    if not base:
        return False
    if _run(root, 'cat-file', '-e', f'{base}^{{commit}}').returncode != 0:
        _run(root, 'fetch', '-q', 'origin', MAIN)
    r = _run(root, 'diff', '--name-only', f'{base}...{sha}')
    changed = [l for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []
    return bool(changed) and all(inside(f, declared) for f in changed)


def direct_push_refusal(root, args, user_config=None):
    """-> None, or why a `git push <args>` is refused: promote_only is on
    and the push writes straight to staging or main. A push whose
    destination cannot be read is left to the full check, not refused."""
    on, where = promote_only(root, user_config)
    if not on:
        return None
    targets = push_targets(root, args)
    hit = sorted(set(targets or ()) & set(tier_branches(root)))
    if hit and _remote_is_empty(root, _push_remote(root, args)):
        return None
    landable, _lwhy = lands_on_staging(root, user_config)
    staging = staging_branch(root)
    if landable and staging in hit:
        # The person's own landing branch is always landable; what lands
        # must carry main's direct work, or it goes through --land, which
        # brings that in first.
        sha = _pushed_commit(root, args, staging)
        missing = main_work_missing(root, sha) if sha else None
        if missing is None or missing:
            why = ('what this push sends could not be read' if missing is None
                   else f'{MAIN} has {len(missing)} commit(s) made directly that it '
                        f'lacks:\n  ' + '\n  '.join(missing[:10]))
            return (f'{staging} is your landing branch, and work lands there '
                    f'carrying everything {MAIN} has -- {why}. Land it with '
                    f'`{LAND_COMMAND}` (add the branch name, or it lands HEAD): '
                    f'it brings {MAIN}\'s work in first, the same way a Promote '
                    f'into {staging} always has, runs the quick checks and pushes.')
        hit = [b for b in hit if b != staging]
    if MAIN in hit and content_only(root, _pushed_commit(root, args, MAIN)):
        hit = [b for b in hit if b != MAIN]
    if not hit:
        return None
    if staging == MAIN:
        # No staging branch yet: there is nothing to land on below main.
        return (f'{" and ".join(hit)} take{"s" if len(hit) == 1 else ""} '
                f'work only by promotion here -- '
                f'{PROMOTE_ONLY_SETTING} is on in {where} -- and this '
                f'repository has no staging branch to land on first. Make one '
                f'with `python3 tools/precedent_branches.py --ensure-tiers '
                f'--apply`, then land the work there (`{LAND_COMMAND}`) and say '
                f'Promote.')
    if landable:
        return (f'{" and ".join(hit)} take{"s" if len(hit) == 1 else ""} work '
                f'only by promotion here -- {PROMOTE_ONLY_SETTING} is on in '
                f'{where}. Your work lands on {staging} (`{LAND_COMMAND}`); '
                f'then promote it into {MAIN}: '
                f'`python3 tools/precedent_branches.py --promote --to {MAIN}`.')
    return (f'{" and ".join(hit)} take{"s" if len(hit) == 1 else ""} work only '
            f'by promotion here -- {PROMOTE_ONLY_SETTING} is on in {where}. '
            f'Land it on {staging} instead (`{LAND_COMMAND}`), then say Promote. '
            f'A commit made on a local {hit[0]} checkout goes the same way; move '
            f'the checkout back with `git reset --keep origin/{hit[0]}` once '
            f'origin/{staging} has it.')


# ONE DEFINITION OF A CURRENT COPY FOR MAIN (2026-10-08). Since 2026-10-07
# Produce's copy is staging merged with main, so main's push test can skip
# what the pull request already passed. The merge check went on allowing a
# head into main only at staging's own tip, so it refused every such copy
# as "out of date: staging has moved" while staging had not moved -- every
# Produce, in every repository on that engine, found by a consumer on
# 2026-10-08. Promote now makes its copy with this function's rule and the
# merge check judges it by the same function, so the two cannot drift
# apart again.
def main_copy_tip(root, mtip, stip, message):
    """-> the commit Produce's copy should be, given main's tip `mtip` and
    staging's `stip`, made and checked out in `root` (a worktree at mtip),
    or None when staging does not merge cleanly into main. Staging's own tip
    when main is already in staging: GitHub's merge of it then has no
    parent the tested head lacks. Otherwise staging merged into main, which
    contains both."""
    if _run(root, 'merge-base', '--is-ancestor', mtip, stip).returncode == 0:
        _run(root, 'checkout', '-q', '--detach', stip)
        return stip
    m = _run(root, 'merge', '--no-ff', '-q', '-m', message, stip,
             env=_merge_env(root))
    if m.returncode != 0:
        _run(root, 'merge', '--abort')
        return None
    return _run(root, 'rev-parse', 'HEAD').stdout.strip()


def main_copy_current(root, head, stip, mtip):
    """True when `head` is a copy main_copy_tip would make from staging's
    current tip `stip`: staging's tip itself, or a merge of exactly
    (a commit on main, stip) whose files are what that merge makes on its
    own -- nothing added by hand. A copy made before staging moved has an
    older staging parent and is not current."""
    if not head or not stip:
        return False
    if head == stip:
        return True
    line = _run(root, 'rev-list', '--parents', '-n', '1', head).stdout.split()
    if len(line) != 3 or line[2] != stip:
        return False
    first = line[1]
    if not mtip or _run(root, 'merge-base', '--is-ancestor', first, mtip).returncode != 0:
        return False
    made = _run(root, 'merge-tree', '--write-tree', first, stip)
    tree = _run(root, 'rev-parse', f'{head}^{{tree}}').stdout.strip()
    return made.returncode == 0 and made.stdout.split()[:1] == [tree]


def merge_refusal(root, bases, heads, user_config=None, head_sha=None):
    """-> None, or why merging a pull request is refused: promote_only is
    on, its base is staging or main, and its head is not the tier directly
    below. `bases` and `heads` are every branch at the base and head tips;
    when the base is ambiguous (two branches at one commit, one of them not
    protected) nothing is refused -- a wrong refusal of an ordinary pull
    request into a branch sitting at staging's commit would be the common
    case right after Promote.
    `head_sha`, the head's commit, lets a Produce copy that is a merge of
    staging and main through when main_copy_current says it is current."""
    on, where = promote_only(root, user_config)
    if not on or not bases:
        return None
    protected = set(tier_branches(root))
    if not all(b in protected for b in bases):
        return None
    staging = staging_branch(root)
    if MAIN not in bases and staging in bases \
            and lands_on_staging(root, user_config)[0]:
        # The person's own landing branch takes any pull request that
        # carries main's direct work; one that does not goes through --land.
        missing = main_work_missing(root, head_sha) if head_sha else []
        if not missing:
            return None
        return (f'{MAIN} has {len(missing)} commit(s) made directly that this '
                f'pull request into {staging} lacks, and work lands on '
                f'{staging} carrying everything {MAIN} has. Run '
                f'`{LAND_COMMAND} BRANCH`: it brings {MAIN}\'s work in first, '
                f'and lands it -- or, for a change that takes a pull request, '
                f'pushes that checked composition to the branch, and this '
                f'pull request merges. Or merge origin/{MAIN} into the branch, '
                f'push it, and merge again.')
    allowed = set()
    for b in bases:
        allowed |= _promotion_heads(root, b)
    if set(heads or ()) & allowed:
        return None
    stale = sorted(h for h in heads or () if is_main_copy(h))
    if MAIN in bases and stale and head_sha:
        staging = staging_branch(root)
        _run(root, 'fetch', '-q', 'origin', staging, MAIN)
        if main_copy_current(root, head_sha, _remote_tip(root, staging),
                             _remote_tip(root, MAIN)):
            return None
    if MAIN in bases and head_sha and red_main_fix(root, head_sha):
        return None
    if MAIN in bases and head_sha and content_only(root, head_sha):
        return None
    if MAIN in bases and stale:
        return (f'{stale[0]} is a copy of {staging_branch(root)} that is out of '
                f'date: {staging_branch(root)} has moved since it was made. '
                f'Close this pull request, promote {staging_branch(root)} into '
                f'{MAIN} again for a fresh copy, and open the pull request '
                f'from that. Never retarget it.')
    if staging == MAIN:
        return (f'a pull request into {MAIN} is merged only by promotion here '
                f'-- {PROMOTE_ONLY_SETTING} is on in {where} -- and this '
                f'repository has no staging branch to land on first. Make one '
                f'with `python3 tools/precedent_branches.py --ensure-tiers '
                f'--apply`, then land the branch there (`{LAND_COMMAND} '
                f'BRANCH`) and say Promote.')
    return (f'a pull request into {" or ".join(sorted(bases))} is merged only '
            f'from {" or ".join(sorted(allowed)) or "nowhere"} here -- '
            f'{PROMOTE_ONLY_SETTING} is on in {where}. Land the branch on '
            f'{staging} (`{LAND_COMMAND} BRANCH`) and say Promote.')


def main_test_failed(root):
    """True only when main's own GitHub test has run on main's tip and
    failed. No test installed, none on this tip, still running, or GitHub
    cannot be asked: False, so the gate stays as strict as before."""
    try:
        mtip = _remote_tip(root, MAIN)
        tests = (github_tests(root, mtip)
                 if mtip and _gets_github_test(root, MAIN) else [])
        if not tests:
            return False
        return github_test_state(root, mtip, tests)[0] == 'failed'
    except Exception:                                       # noqa: BLE001
        return False


def red_main_fix(root, head_sha):
    """promote-only's red-main exception: a pull request straight into main
    is let through when main's own GitHub test has failed on its tip and the
    pull request is built on that tip, so it repairs main as it stands. The
    session brings the same fix into staging afterwards; until it does, a
    landing into staging that lacks it is refused (main_work_missing).

    Why (Morgan, 2026-10-11, strength: assented): main failed its test after
    a Produce, the fix was refused straight into main, and went through
    staging and a second Produce instead. Asked about the rule, he approved
    letting a fix for a red main go straight there; every other move into
    main still comes from staging."""
    mtip = _remote_tip(root, MAIN)
    if not mtip or _run(root, 'merge-base', '--is-ancestor', mtip,
                        head_sha).returncode != 0:
        return False
    return main_test_failed(root)


def tier_branches(root):
    """Every branch that is a tier here: main and staging (and its old
    name). None of them may ever be the SOURCE of a pull request:
    A merged pull request's page offers to delete its source branch, and
    staging was deleted right after a merge of it into main on 2026-09-26,
    cause not established (see
    gotchas/gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging.md)."""
    names = {MAIN, LEGACY_STAGING, STAGING, staging_branch(root)}
    declared = base_branch(root)
    if declared:
        names.add(declared)
    return sorted(names)


def never_offered(root, user_config=None):
    """-> the branches never offered for deletion here: the tiers -- staging
    (and its old name) and main -- whoever asks. Every other branch is an
    ordinary branch, offered like any other."""
    return tier_branches(root)


def ensure_tiers(root, apply=False, say=print, new_install=False):
    """Make origin carry a real staging branch.
    -> 0 when it exists (or was just made), 1 when something is missing and
    `apply` is off, or could not be made.

    A missing staging is made from main.
    A repository whose staging tier is main (base_branch "main", no
    staging_branch) gains a `staging` branch the same way, and its
    precedent.json gains `"staging_branch": "staging"` -- written here,
    committed by the session running the migration. base_branch itself is
    left alone (see STAGING_KEY)."""
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
    if not missing:
        say(f'tiers: {staging} -> {MAIN}, both present.')
        return 0
    if not apply:
        say('tiers: missing ' + '; '.join(missing) +
            ' -- run `python3 tools/precedent_branches.py --ensure-tiers --apply`.')
        return 1
    if wants_staging_branch or not _remote_tip(root, staging):
        # A staging branch that has gone missing is rebuilt from main.
        # 2026-09-26:
        # staging was deleted right after a pull request FROM staging into
        # main was merged (cause not established), and this looked for staging
        # itself to rebuild it from, found nothing and gave up. Right after
        # such a merge, main contains staging exactly.
        #
        # What lands on staging this way has not had staging's full check,
        # and it gets it on the way to main: a Promote into main runs the
        # full check on anything it has not seen pass.
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
    say(f'tiers: {staging_branch(root)} -> {MAIN}.')
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


# MAIN'S TEST LEAVES A GIT MARKER WHEN IT PASSES (Morgan, 2026-10-10: "yes,
# build it and take it to main"). A session in another repository usually
# cannot ask GitHub's API about BestPractice, so Update Vendors took main on
# trust there, even on a day its test had failed. deep-check.yml now pushes
# PASSED_PREFIX + <tree> when the test passes on main or on a pull request
# into main, naming the tree it tested; plain git reads it anywhere a fetch
# works. Keyed by tree, not commit: a pull request's run tests the merge of
# its head into main, and the commit main gets from that merge has the same
# files under another name.
PASSED_PREFIX = 'refs/precedent/passed/'


def passed_markers(root):
    """-> the set of trees main's GitHub test marked as passed on origin, or
    None when origin could not be read. One ls-remote, no API call."""
    p = subprocess.run(['git', '-C', str(root), 'ls-remote', 'origin',
                        PASSED_PREFIX + '*'], capture_output=True, text=True,
                       timeout=60)
    if p.returncode != 0:
        return None
    return {ref[len(PASSED_PREFIX):] for ref in
            (line.partition('\t')[2] for line in p.stdout.splitlines())
            if ref.startswith(PASSED_PREFIX)}


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


def _yaml_scalar_list(value):
    """`[a, 'b']`, `a` or `` -> a list of plain strings."""
    v = value.split(' #', 1)[0].strip()
    if v.startswith('[') and v.endswith(']'):
        v = v[1:-1]
        return [x.strip().strip('\'"') for x in v.split(',') if x.strip()]
    return [v.strip('\'"')] if v else []


_ON_KEY = re.compile(r'''^(?:on|"on"|'on')\s*:\s*(.*)$''')
_YAML_KEY = re.compile(r'^([\w-]+)\s*:\s*(.*)$')


def workflow_triggers(text):
    """-> {event: {key: [values]}} read from a workflow's top-level `on:`,
    or None when the file has no `on:` this reader understands. Only what
    pull_request_checks needs: the events, and each event's list-valued
    keys (`branches`, `branches-ignore`), inline or as a dash list.

    WHY NOT PyYAML (2026-10-19). GitHub's runner has none, so this code
    never ran where the deep check runs, and its test reported itself not
    applicable there (#1218) -- a band-aid over a path CI could not
    exercise. A workflow's `on:` block is a small, regular shape; reading
    it here keeps one path everywhere, as frontmatter_yaml.py does for
    frontmatter."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _ON_KEY.match(line)
        if not m:
            continue
        inline = m.group(1).split(' #', 1)[0].strip()
        if inline:
            return {e: {} for e in _yaml_scalar_list(inline)}
        out, event, key, ev_indent = {}, None, None, None
        for raw in lines[i + 1:]:
            if raw.lstrip().startswith('#'):
                continue
            body = raw.split(' #', 1)[0].rstrip()
            if not body.strip():
                continue
            indent = len(body) - len(body.lstrip())
            if indent == 0:
                break
            item = body.strip()
            if ev_indent is None:
                ev_indent = indent
            if indent == ev_indent:
                em = _YAML_KEY.match(item)
                if not em:
                    return None
                event, key = em.group(1), None
                out[event] = {}
                continue
            if event is None:
                return None
            km = _YAML_KEY.match(item)
            if km:
                key = km.group(1)
                out[event][key] = _yaml_scalar_list(km.group(2))
            elif item.startswith('-') and key is not None:
                out[event][key].extend(_yaml_scalar_list(item[1:]))
        return out
    return None


def pull_request_checks(root, base):
    """-> [workflow file] whose `on: pull_request` fires for a pull request
    into `base`, or None when it cannot be told (a file whose `on:` this
    reader does not understand). Read from the checkout's
    .github/workflows/ with workflow_triggers, never PyYAML."""
    import fnmatch
    found = []
    for wf in sorted((pathlib.Path(root) / '.github' / 'workflows').glob('*.y*ml')):
        try:
            on = workflow_triggers(wf.read_text(encoding='utf-8'))
        except OSError:
            return None
        if on is None:
            return None
        if 'pull_request' not in on:
            continue
        cfg = on['pull_request']
        want = cfg.get('branches')
        skip = cfg.get('branches-ignore')
        if want is not None and not any(fnmatch.fnmatch(base, w) for w in want):
            continue
        if skip and any(fnmatch.fnmatch(base, w) for w in skip):
            continue
        found.append(wf.name)
    return found


def _carry_composition_to_branch(root, label, new):
    """After a landing refused for the pull-request route: push the
    composition the quick checks just passed -- staging, main's direct work
    and the branch -- to the branch itself, so the pull request carries
    everything main has. -> what to tell the person.

    WHY (2026-10-19). The refusal sent the work to a pull request from the
    branch as it stood, which lacked main's direct commits; the push check
    and the merge guard then refused THAT, telling the session to use
    --land, which had just sent it to the pull request. The way out was a
    hand merge of origin/main into the branch. The composition is already
    built and checked, and it descends from the branch, so this push is a
    fast-forward; a branch that moved, or a label that is no branch, is
    left alone and said."""
    branch = label[len('origin/'):] if label.startswith('origin/') else label
    if branch in ('HEAD', '') or branch in tier_branches(root):
        return (f'{label} is not a branch the pull request can come from, so '
                f'the checked composition was not pushed anywhere: merge '
                f'origin/{MAIN} into the branch you open it from first.')
    # A branch that already carries main's work -- one cut from main, a
    # red-main fix above all -- needs nothing, and is left alone: moving it
    # after its pull request into main merged sent the main-test wait to a
    # head no test ever ran on (2026-10-19).
    tip = _remote_tip(root, branch)
    if tip and not main_work_missing(root, tip):
        return (f'{branch} already carries everything {MAIN} has, so the pull '
                f'request from it as it stands lacks nothing.')
    p = _run(root, 'push', '-q', 'origin', f'{new}:refs/heads/{branch}')
    if p.returncode != 0:
        return (f'Could not bring {branch} up to the checked composition '
                f'({(p.stderr or p.stdout).strip()[:200]}): merge '
                f'origin/{MAIN} into {branch} and push it before opening the '
                f'pull request, or the merge is refused for lacking '
                f'{MAIN}\'s work.')
    return (f'{branch} now carries the composition the quick checks passed '
            f'({new[:12]}: {staging_branch(root)}, {MAIN}\'s direct work and '
            f'{branch}), so the pull request from it lacks nothing {MAIN} has.')


def pull_request_route_note(root, base, checks_ran=None):
    """What to do after a refusal that sends a landing through a pull
    request into `base`, said from what the workflows actually run.
    `checks_ran` is True when the caller ran the quick checks on this work
    just before (the land tool does); anything else, the two-argument call
    included, means nobody knows, and the note says to run them first.

    WHY (2026-10-18). A refusal said "open a pull request into staging, and
    merge it once its checks pass". Here no workflow runs on a pull request
    into staging, so no check ever reported, no event ever came, and the
    session sat waiting on one until Morgan asked whether anything was
    happening. The quick checks this landing ran are the checks; where
    GitHub adds none, the merge follows the pull request at once.

    WHY checks_ran (2026-10-18). The shared ladder's pre-push guard calls
    this from a plain `git push`, where no quick checks ran; the note said
    they had passed and invited a merge with nothing checked."""
    if checks_ran is True:
        ran = 'the quick checks above having passed'
        none_ran = ('The quick checks above passed on this composition: open '
                    'the pull request and merge it straight away.')
    else:
        tool = _push_check_tool(root) or 'tools/precedent_push_check.py'
        ran = (f'once the quick checks pass (`python3 {tool}`); nothing has '
               f'run them on this push')
        none_ran = (f'Nothing has run the quick checks on this push: run '
                    f'`python3 {tool}`, and once it passes, open the pull '
                    f'request and merge it straight away.')
    runs = pull_request_checks(root, base)
    if runs is None:
        return (f'Could not read which GitHub checks run on a pull request '
                f'into {base}. Open the pull request and look at its checks '
                f'right away: if none is listed, none is coming -- merge it, '
                f'{ran}. Never wait on a check nothing has started.')
    if not runs:
        return (f'No workflow here runs on a pull request into {base}, so no '
                f'GitHub check will ever report on one. {none_ran} Do not '
                f'wait for checks.')
    return (f'A pull request into {base} is checked by {", ".join(runs)}: open '
            f'it, and merge once those report green. If none has started a '
            f'few minutes after opening, look again rather than wait.')


def refused_push(root, branch, built, proc):
    """A push to origin's `branch` of commit `built` that git refused. ->
    (moved, said): `moved` True only when origin's `branch` now has work
    `built` does not contain -- a race, worth doing again -- and `said`, what
    the push itself printed.

    ONE PLACE FOR THIS, used by --land and land_next.py (2026-10-11). Each used to explain any refusal as "the
    branch moved": the lander was fixed on 2026-10-10 and --land was not,
    so a leak-gate refusal on a branch that sat still was reported as a race
    and the push's own words were cut to two hundred characters."""
    _run(root, 'fetch', '-q', 'origin', branch)
    tip = _remote_tip(root, branch)
    moved = bool(tip) and _run(root, 'merge-base', '--is-ancestor', tip,
                               built).returncode != 0
    said = ((getattr(proc, 'stderr', '') or '') + (getattr(proc, 'stdout', '') or '')).strip()
    return moved, said


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


def _check(root, wt, tier, dest=None, since=None):
    """-> (ok, output): the repo's own push check at `tier` in worktree
    `wt`, reusing a pass the checkout already recorded for the same tree.
    `dest` is the branch the result is pushed to: the views check holds a
    set's commits to that same rung. `since`, for the quick checks, is the
    commit the change is measured from (the practice checks run on the
    files changed since it)."""
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
                       + (['--destination', dest] if dest else [])
                       + (['--changed-since', since] if since else []),
                       cwd=wt, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).rstrip()


# DRIFT FROM ABOVE (spec/BRANCH_TIERS_PLAN.md, holes 2, 4 and 5). Work is
# meant to climb the tiers: staging by --land, then main by the pull
# request from staging. Some of it arrives from above instead -- a
# workflow's bot commit on main, an edit made on GitHub's website -- and
# the next pull request into main would meet it as a conflict. --land and
# Promote compose it into staging, and only once the tier it sits on has
# had its own checks: on main, the GitHub test.
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
# request, main is ahead of staging by merge commits whose files staging
# already has (measured 2026-09-26 in two repositories). The test is whether merging the
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


def _upstream_review(root, wt, stage, out, batch_range):
    """-> (lines, recorded): the upstream review for this stage (the ladder
    set's upstream-review practice) -- what the check printed, less what
    the batch's own commits already record as reviewed -- and whether its
    Upstream-seen lines were written into the commit at `wt`'s HEAD. Only on
    the ladder and only for a code owner: anyone else gets ([], False) and
    sees nothing. `wt` is None where nothing is recorded (Produce: main
    moves by a pull request). Never refuses a stage: on any error the review
    is simply not shown."""
    # The review is a set's (step_review in its precedent-source.json); the
    # engine only writes its lines into the commit (2026-10-17).
    pr = _sibling('precedent_resolve')
    ur = pr.load_set_tool(root, 'step_review') if pr is not None else None
    if ur is None:
        return [], False
    try:
        new, old = ur.prepare(root, stage, out, rev_range=batch_range)
        if new is None:
            return [], False
        recording = None
        if new and wt is not None:
            msg = (_git(wt, 'log', '-1', '--format=%B') or '').rstrip()
            msg += ('\n\n' if not ur.TRAILER in msg else '\n') \
                + '\n'.join(ur.trailer_lines(new)) + '\n'
            a = _run(wt, 'commit', '--amend', '--allow-empty', '-q', '--no-verify', '-m', msg,
                     env=_merge_env(root))
            recording = 'written' if a.returncode == 0 else None
        return ur.report(stage, new, old, recording), recording == 'written'
    except Exception:                                            # noqa: BLE001
        return [], False


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
    they parted), or None when that cannot be read.

    A Produce merges first and waits after (2026-10-13), and both broke the
    old reading, which compared `sha` with main as it is now. Right after
    the merge main's new tip is not in this clone yet, so the diff failed,
    and every path-filtered workflow was required: a consumer's wait said
    "never ran on it ... fix main now" of a prompt check its change never
    touched. Once fetched, main carries `sha`, the diff from where they
    parted is empty, and a workflow that did run dropped out. So: fetch
    main's tip when it is missing, and when main already carries `sha`, read
    the pull request's diff against the main it was merged onto -- `sha`'s
    first parent, which the Produce's copy (staging merged with main) has.
    A commit main carries that is no merge says nothing about where the
    pull request began: None, and the workflow is required, as before."""
    base = _remote_tip(root, MAIN) or _git(root, 'rev-parse', '--verify', '-q', MAIN)
    if not base:
        return None
    if _run(root, 'cat-file', '-e', f'{base}^{{commit}}').returncode != 0:
        _run(root, 'fetch', '-q', 'origin', MAIN)
        if _run(root, 'cat-file', '-e', f'{base}^{{commit}}').returncode != 0:
            return None
    if _run(root, 'merge-base', '--is-ancestor', sha, base).returncode == 0:
        parents = (_git(root, 'rev-list', '--parents', '-n', '1', sha) or '').split()[1:]
        if len(parents) < 2:
            return None
        base = parents[0]
    r = _run(root, 'diff', '--name-only', f'{base}...{sha}')
    if r.returncode != 0:
        return None
    return [l for l in r.stdout.splitlines() if l.strip()]


# A WORKFLOW GITHUB SKIPS HERE BY DESIGN IS NOT ONE OF MAIN'S GITHUB TESTS
# (2026-10-09). The leak-gate template gates its only job on
# `github.event.repository.private != true`: in a private repository it never
# runs, and GitHub records a skipped run for it on every pull request. A
# skipped run never counts as a pass (github_test_state), so a private
# consumer's wait read "leak-gate.yml never ran on it. Do not merge" on every
# pull request into main, for good, and the due check blamed an Update
# Vendors that would bring the same file. One definition, read by every
# reader of main's GitHub test: a workflow whose jobs are ALL gated off in a
# private repository, in a repository whose precedent.json declares
# visibility private. Anything else skipped still never reads as passed.
_PRIVATE_GATE = re.compile(
    r'\A(?:github\.event\.repository\.private\s*!=\s*true'
    r'|!\s*github\.event\.repository\.private'
    r'|github\.event\.repository\.private\s*==\s*false)\Z')


def _conjuncts(expr):
    """-> the top-level `&&` parts of a workflow expression, each stripped of
    `${{ }}` and of parentheses that wrap the whole part."""
    expr = expr.strip()
    if expr.startswith('${{') and expr.endswith('}}'):
        expr = expr[3:-2].strip()
    parts, depth, start, quote = [], 0, 0, False
    i = 0
    while i < len(expr):
        c = expr[i]
        if c == "'":
            quote = not quote
        elif not quote and c == '(':
            depth += 1
        elif not quote and c == ')':
            depth -= 1
        elif not quote and depth == 0 and expr.startswith('&&', i):
            parts.append(expr[start:i])
            start = i + 2
            i += 1
        i += 1
    parts.append(expr[start:])
    out = []
    for p in parts:
        p = ' '.join(p.split())
        while p.startswith('(') and p.endswith(')') and _balanced(p[1:-1]):
            p = p[1:-1].strip()
        out.append(p)
    return out


def _balanced(text):
    """True when `text`'s parentheses pair up on their own."""
    depth = 0
    for c in text:
        depth += {'(': 1, ')': -1}.get(c, 0)
        if depth < 0:
            return False
    return depth == 0


def _job_conditions(text):
    """-> [the job-level `if:` expression, or None] for each job in a
    workflow's text; [] when it declares none."""
    lines = text.splitlines()
    at = next((i for i, l in enumerate(lines) if re.match(r'jobs:[ \t]*(#.*)?$', l)), None)
    if at is None:
        return []
    body = []
    for l in lines[at + 1:]:
        if l.strip() and not l[0].isspace() and not l.startswith('#'):
            break
        body.append(l)

    def indent(l):
        return len(l) - len(l.lstrip(' '))
    real = [l for l in body if l.strip() and not l.lstrip().startswith('#')]
    if not real:
        return []
    job_at = indent(real[0])
    prop_at = next((indent(l) for l in real if indent(l) > job_at), None)
    conds = []
    i = 0
    while i < len(body):
        l = body[i]
        i += 1
        if not l.strip() or l.lstrip().startswith('#'):
            continue
        if indent(l) == job_at:
            conds.append(None)
            continue
        m = re.match(r' *if:[ \t]*(.*)$', l)
        if not (conds and m and indent(l) == prop_at and conds[-1] is None):
            continue
        value = m.group(1).strip()
        if value[:1] in ('>', '|'):          # a folded or literal block
            more = []
            while i < len(body) and (not body[i].strip() or indent(body[i]) > prop_at):
                more.append(body[i].strip())
                i += 1
            value = ' '.join(x for x in more if x)
        elif len(value) > 1 and value[0] == value[-1] == '"':
            value = value[1:-1]
        conds[-1] = value
    return conds


def skipped_by_design(root, text):
    """True when GitHub never runs this workflow's jobs in this repository:
    every job is gated on `github.event.repository.private != true` (or
    `!github.event.repository.private`) as a whole condition or a top-level
    `&&` part of one, and precedent.json declares visibility private. Main's
    GitHub test leaves such a workflow out, and nothing else does: in a
    public repository, or for a workflow skipped for any other reason, a
    skipped run is still a run that did not happen."""
    if precedent_json(root).get('visibility') != 'private':
        return False
    conds = _job_conditions(text or '')
    return bool(conds) and all(
        c is not None and any(_PRIVATE_GATE.match(p) for p in _conjuncts(c))
        for c in conds)


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
    workflow is required, as before.

    A workflow GitHub never runs in this repository (skipped_by_design: a
    private repository, and every job gated off there) is not required
    either; its skipped run is not a pass, and waiting for one waited
    forever (2026-10-09)."""
    out = []
    changed = False   # read once, and only for a workflow with a path filter
    names = _git(root, 'ls-tree', '--name-only', f'{sha}:.github/workflows') or ''
    for name in names.splitlines():
        if not name.endswith(('.yml', '.yaml')):
            continue
        path = f'.github/workflows/{name}'
        text = _git(root, 'show', f'{sha}:{path}') or ''
        if skipped_by_design(root, text):
            continue
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


def _refusal(data, key):
    """-> GitHub's own message when `data` is a refusal rather than the
    answer asked for: a JSON object carrying `message` and not `key`. The
    API answers a refusal (403, 404, or a session proxy that has no access
    to the repository) with such an object and a normal-looking body, so it
    read as "no runs" -- on 2026-10-09 a session without access to
    BestPractice said main's test "shows no run" when the real answer was
    "GitHub access to this repository is not enabled for this session"."""
    if isinstance(data, dict) and key not in data and data.get('message'):
        return str(data['message'])
    return None


def _runs_on(gh, slug, sha):
    data, err = gh.call(f'repos/{slug}/actions/runs?head_sha={sha}&per_page=100',
                        cache=False)
    if err or not isinstance(data, dict):
        return None, err or 'GitHub gave an answer this could not read'
    refused = _refusal(data, 'workflow_runs')
    if refused:
        return None, f'GitHub refused: {refused}'
    return data.get('workflow_runs') or [], None


_CURRENT_SLUG = {}


def _current_slug(gh, slug):
    """-> (the repository's current owner/name per GitHub, None) or (None,
    why). One call per slug per process: a wait asks this on every poll."""
    if slug not in _CURRENT_SLUG:
        data, err = gh.call(f'repos/{slug}', cache=False)
        name = data.get('full_name') if isinstance(data, dict) else None
        refused = _refusal(data, 'full_name')
        _CURRENT_SLUG[slug] = (name, None) if name else (
            None, err or (f'GitHub refused: {refused}' if refused
                          else 'its answer named no repository'))
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
# The installed workflows whose CURRENT template (templates/github-actions/
# <name>.template) carries the not-due skip: the only ones Update Vendors
# can bring it to. A consumer has no templates beside its engine, so this
# names them; verify_harness.py checks it against the templates themselves.
NOT_DUE_SKIP_TEMPLATES = ('light-check.yml',)
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


# THE CLEANUP BUTTON'S OWN NUMBER (2026-10-16, spec/BRANCH_CLEANUP_BUTTON_PLAN.md).
# At most how often the branch cleanup page offers a PRIVATE repository's
# "Delete all merged branches" button, in hours, counted from that
# repository's last cleanup run. Apart from github_ci_every_hours on purpose.
# Morgan: "instead of using the same variable ... let's define a second
# variable next to me and let's make that variable 336 for now" (strength:
# decided). Nothing ever runs the cleanup automatically; this only decides
# whether the button is shown.
CLEANUP_CADENCE_KEYS = ('github_branch_cleanup_every_hours',)


def branch_cleanup_cadence(root, user_config=None):
    """-> (hours, where): at most how often a private repository's cleanup
    button is shown. 0 means always. The person's identity.json first, then
    the repository's precedent.json, the way main_test_cadence reads its
    number. Unlike it, this says nothing about visibility: the page decides
    that per repository. A doubt -- unset, not a number, negative -- is 0,
    the button shown: showing it costs nothing, only a click does."""
    found = None
    for path in _identity_files(root, user_config):
        ident = _read_json(path)
        if ident and ident.get('email'):
            found = next(((ident[k], str(path)) for k in CLEANUP_CADENCE_KEYS
                          if k in ident), None)
            if found:
                break
    if not found:
        repo = precedent_json(root)
        found = next(((repo[k], "this repo's precedent.json")
                      for k in CLEANUP_CADENCE_KEYS if k in repo), None)
    if not found:
        return 0.0, 'github_branch_cleanup_every_hours is not set anywhere'
    value, where = found
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return 0.0, (f'github_branch_cleanup_every_hours is {value!r} in {where}, '
                     f'which is not a number of hours')
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
        # Update Vendors cures this only where the current template carries
        # the skip. Until 2026-10-09 every such workflow was told to wait for
        # one, leak-gate.yml included, whose template has never had it.
        if old[0].rsplit('/', 1)[-1] in NOT_DUE_SKIP_TEMPLATES:
            return True, (f'{note}{old[0]} predates the not-due skip, so it runs on '
                          f'every pull request into {MAIN} until Update Vendors '
                          f'brings the current one')
        return True, (f'{note}{old[0]} has no not-due skip, and no template this '
                      f'engine ships gives it one, so GitHub runs it on every pull '
                      f'request into {MAIN} whatever this decides')
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


def _at_head(sha):
    """', at head commit <all 40 characters>' -- the merge instruction's
    expected head. A merge through GitHub's API takes the head it expects in
    full (expectedHeadSha), and the twelve-character form printed everywhere
    else here is refused there; a session in a consuming repository read the short one
    back and had to look the rest up (2026-10-06); a session elsewhere passed
    seven characters, the merge failed, and auto mode then refused even its
    reads (2026-10-08), so the line says so outright. Pinning the head also
    means a copy that moved after its check is not merged by mistake."""
    return (f', at head commit {sha} -- the merge tool takes all 40 '
            f'characters, as here, or no expected head at all' if sha else '')


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
    # A fast move merges first and waits after, so by now main may already
    # carry the commit (2026-10-10: a passed test still said "Merge the pull
    # request" twice, over a pull request merged half an hour before).
    merged = _on_main_already(root, sha)
    if state == 'passed':
        if merged:
            say(f'GitHub test PASSED on {sha[:12]}: {detail}. {MAIN} already '
                f'carries it -- the pull request is merged; nothing is left to do.')
        else:
            say(f'GitHub test PASSED on {sha[:12]}: {detail}. Merge the pull request '
                f'into {MAIN} with a merge commit{_at_head(sha)}.')
        return 0
    if merged:
        say(f'GitHub test {state.upper()} on {sha[:12]}: {detail}. {MAIN} already '
            f'carries it, so fix {MAIN} now, straight into it: cut a branch '
            f'from {MAIN}\'s tip named by `python3 tools/precedent_branch_name.py '
            f'fix main WORDS`, open its pull request into {MAIN} (red_main_fix '
            f'lets that one through), then land the same branch on '
            f'{staging_branch(root)} (`{LAND_COMMAND} BRANCH`).')
    else:
        say(f'GitHub test {state.upper()} on {sha[:12]}: {detail}. Do not merge.')
    return 1


def _on_main_already(root, sha):
    """-> True when origin's main already holds `sha` (after a fresh fetch).
    False when it does not, or git cannot say."""
    _run(root, 'fetch', '-q', 'origin', MAIN)
    return _run(root, 'merge-base', '--is-ancestor', sha,
                f'origin/{MAIN}').returncode == 0


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

# Two more kinds of generated content carry no header (2026-10-16: a land
# in a repository writing a book stopped on both, and called them
# hand-written):
#
# * a doc_sync block -- <!--gen:NAME--> ... <!--/gen:NAME--> -- inside a
#   document that is otherwise hand-written. A conflict that sits entirely
#   inside such blocks is generated: either side is taken and
#   `tools/doc_sync.py --write` writes the block afresh.
# * an output the repository declares itself, in its precedent.json:
#
#   "generated": [{"paths": ["book/output/*.docx"],
#                  "rebuild": ["tools/build_book.py", "--all"]}]
#
#   `paths` are globs (fnmatch, repo-relative); `rebuild` is a tools/ script
#   and its arguments, run with this Python from the worktree's root.
GENERATED_KEY = 'generated'
_GEN_OPEN_RE = re.compile(r'<!--gen:[\w-]+-->')
_GEN_CLOSE_RE = re.compile(r'<!--/gen:[\w-]+-->')
DOC_SYNC = 'tools/doc_sync.py'


def _declared_generated(wt):
    """-> [(globs, argv)] from worktree `wt`'s precedent.json `generated`
    list; malformed entries are skipped, so a conflict in their files is
    still named rather than rebuilt by something nobody could read."""
    rows = precedent_json(wt).get(GENERATED_KEY)
    out = []
    for row in rows if isinstance(rows, list) else ():
        if not isinstance(row, dict):
            continue
        globs, argv = row.get('paths'), row.get('rebuild')
        if (isinstance(globs, list) and globs
                and all(isinstance(g, str) and g for g in globs)
                and isinstance(argv, list) and argv
                and all(isinstance(a, str) for a in argv)
                and argv[0].startswith('tools/') and argv[0].endswith('.py')
                and '..' not in pathlib.PurePosixPath(argv[0]).parts):
            out.append((tuple(globs), tuple(argv)))
    return out


def _conflict_only_in_gen_blocks(wt, rel):
    """True when every conflict hunk in worktree `wt`'s `rel` sits inside a
    doc_sync gen block, with no block boundary inside any hunk."""
    try:
        text = (pathlib.Path(wt) / rel).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    inside, in_hunk, hunks = False, False, 0
    for line in text.splitlines():
        if line.startswith('<<<<<<<'):
            if not inside or in_hunk:
                return False
            in_hunk, hunks = True, hunks + 1
        elif line.startswith('>>>>>>>'):
            in_hunk = False
        elif in_hunk:
            if _GEN_OPEN_RE.search(line) or _GEN_CLOSE_RE.search(line):
                return False
        elif _GEN_OPEN_RE.search(line):
            inside = True
        elif _GEN_CLOSE_RE.search(line):
            inside = False
    return hunks > 0 and not in_hunk


def _take_ours_in_hunks(wt, rel):
    """Resolve each conflict hunk in worktree `wt`'s `rel` to our side, in
    place, keeping everything git merged cleanly around them. A document
    with gen blocks is hand-written outside them, so `git checkout --ours`
    on the whole file would drop the other side's edits to its prose."""
    path = pathlib.Path(wt) / rel
    out, side = [], None
    for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
        if line.startswith('<<<<<<<'):
            side = 'ours'
        elif side and line.startswith('|||||||'):
            side = 'base'
        elif side and line.startswith('======='):
            side = 'theirs'
        elif side and line.startswith('>>>>>>>'):
            side = None
        elif side in (None, 'ours'):
            out.append(line)
    path.write_text(''.join(out), encoding='utf-8')


def _doc_html_in_use(wt):
    """True where tools/doc_html.py is in force in worktree `wt` -- the one
    rule precedent_push_check.doc_html_in_use() keeps for whether its
    package is asked for. Present is not enough: a consumer that declined
    sortable-table-renderer still receives the vendored file, and a Promote
    there ran it over the composed tree and failed on a document only
    BestPractice has (2026-10-08). Unanswerable (the module missing):
    present counts, as before."""
    ppc = _sibling('precedent_push_check')
    if ppc is None or not hasattr(ppc, 'doc_html_in_use'):
        return (pathlib.Path(wt) / 'tools' / 'doc_html.py').is_file()
    return ppc.doc_html_in_use(wt)


def _generator_of(wt, rel):
    """-> the command (a tools/ script and its arguments, as a tuple) that
    writes `rel` in worktree `wt`, or None when nothing here rebuilds it. Read from our side of a conflicted file
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
        return (m.group(1),)
    if rel.endswith('.html') and _doc_html_in_use(wt):
        src = rel[:-len('.html')] + '.md'
        reg = (pathlib.Path(wt) / 'tools' / 'doc_html.py').read_text(encoding='utf-8')
        if re.search(r"\(\s*['\"]" + re.escape(src) + r"['\"]", reg):
            return ('tools/doc_html.py',)
    for globs, argv in _declared_generated(wt):
        if (any(fnmatch.fnmatchcase(rel, g) for g in globs)
                and (pathlib.Path(wt) / argv[0]).is_file()):
            return argv
    if ((pathlib.Path(wt) / DOC_SYNC).is_file()
            and _conflict_only_in_gen_blocks(wt, rel)):
        return (DOC_SYNC, '--write', '--full', '--only', rel)
    return None


TIMES_FILE = 'tools/harness_check_times.json'


def _merge_times_file(wt):
    """Write the three-way merge of a conflicted harness timing list into
    worktree `wt`, by tools/harness_times_merge.py, the merge driver's own
    code. -> True when written, False when either side does not read as
    one (then it stops like any other conflict).

    WHY THREE-WAY (2026-10-19). This fallback used to write the union of
    both sides, which brings back a test the other side deleted -- the
    exact #1180/#1181 bug the merge driver was written to stop. Index stage
    1 is the base; a file both sides added has none, and reads as empty."""
    def side(n):
        r = subprocess.run(['git', '-C', str(wt), 'show', f':{n}:{TIMES_FILE}'],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout) if r.returncode == 0 else None
        except ValueError:
            return None
        return d if isinstance(d, dict) and isinstance(d.get('seconds'), dict) else None
    ours, theirs = side(2), side(3)
    if ours is None or theirs is None:
        return False
    here = str(pathlib.Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import harness_times_merge
    merged = harness_times_merge.merge(side(1) or {}, ours, theirs)
    # Both sides add to the one "measured" line: keep both notes.
    notes = [str(theirs.get('measured') or '')]
    notes += [n for n in str(ours.get('measured') or '').split('; ')
              if n and n not in notes[0]]
    merged['measured'] = '; '.join(x for x in notes if x)
    (pathlib.Path(wt) / TIMES_FILE).write_text(
        json.dumps(merged, indent=1) + '\n', encoding='utf-8')
    return True


HAND_WRITTEN = 'the same lines of hand-written text changed on both sides'


def _resolve_by_regenerating(wt, say):
    """After a merge stopped on conflicts in `wt`: when every conflicted file
    is generated, take our side, run each one's generator over the merged
    sources, and stage the result. -> (True, [regenerated], '') or (False,
    [the files that stop it], why) -- `why` says what kind of stop it is, so
    a refusal never calls a generated file hand-written."""
    conflicted = [l for l in _run(wt, 'diff', '--name-only', '--diff-filter=U')
                  .stdout.splitlines() if l.strip()]
    # The harness timing list is a record every session adds to: two that
    # each add tests conflict on its one "measured" line, every time (twice
    # on 2026-10-17). Both sides' times are kept, and the notes joined.
    if TIMES_FILE in conflicted and _merge_times_file(wt):
        _run(wt, 'add', '--', TIMES_FILE)
        conflicted.remove(TIMES_FILE)
        if not conflicted:
            return True, [TIMES_FILE], ''
    gens = {rel: _generator_of(wt, rel) for rel in conflicted}
    hand = sorted(rel for rel, g in gens.items() if not g)
    if hand or not conflicted:
        return False, hand, (
            HAND_WRITTEN + ' -- no generator here rebuilds '
            + ('it' if len(hand) == 1 else 'them') + ' (a generated file '
            f'carries a `generated_by:` header, sits inside a doc_sync '
            f'<!--gen:--> block, or is declared under "{GENERATED_KEY}" in '
            f'precedent.json)')
    for rel in conflicted:
        if gens[rel][0] == DOC_SYNC:
            _take_ours_in_hunks(wt, rel)
        else:
            _run(wt, 'checkout', '--ours', '--', rel)
    for cmd in sorted(set(gens.values())):
        made = sorted(k for k, v in gens.items() if v == cmd)
        r = subprocess.run([sys.executable, *cmd], cwd=str(wt),
                           capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).strip()[-300:]
            say(f'{" ".join(cmd)} could not rebuild {", ".join(made)}: {tail}')
            return False, made, (f'generated files changed on both sides, and '
                                 f'`{" ".join(cmd)}` could not rebuild them')
    for rel in conflicted:
        # A builder that writes dated names (a dated download name, which a
        # set's practice can ask for)
        # deletes the conflicted file and writes today's: a path gone is a
        # rebuild, not markers left in one.
        path = pathlib.Path(wt) / rel
        text = (path.read_text(encoding='utf-8', errors='replace')
                if path.is_file() else '')
        if '<<<<<<<' in text or '>>>>>>>' in text:
            return False, [rel], ('generated, but its rebuild left conflict '
                                  'markers in it')
    _drop_stamp_only_changes(wt)
    _run(wt, 'add', '-A', '--', *conflicted)
    _run(wt, 'add', '-u')
    # ...and that new file is untracked: staged by the globs that declared
    # the conflicted output, or the land committed the deletion and lost the
    # rebuilt document (2026-10-17, read off this code by the session that
    # declared a consumer's dated Word output).
    globs = [g for g_, argv in _declared_generated(wt)
             if argv in gens.values() for g in g_]
    if globs:
        new = [l for l in _run(wt, 'ls-files', '--others', '--exclude-standard')
               .stdout.splitlines()
               if l and any(fnmatch.fnmatchcase(l, g) for g in globs)]
        if new:
            _run(wt, 'add', '--', *new)
    return True, sorted(conflicted), ''


def _stamp_only(wt, rel):
    """True when the only lines `rel` changed in worktree `wt` are a
    render's build stamp: doc_html writes the time it ran into every page it
    renders, so a rebuild of an unchanged page differs by that line alone."""
    # Bytes, decoded leniently: a generated binary file git does not
    # recognise as binary would otherwise crash the decode (2026-10-16).
    diff = subprocess.run(['git', '-C', str(wt), 'diff', '-U0', '--', rel],
                          capture_output=True).stdout.decode(
                              'utf-8', errors='replace').splitlines()
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
    `generated_by:` header, and doc_html where it is in use. -> the tracked
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
    if _doc_html_in_use(wt):
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
# The lock's name comes from precedent_data_branches.py since 2026-10-11
# (Morgan: "'data-' for permanent branches is great and approved ... only
# for ones done by people using the ladder", strength: decided):
# data-promote-lock in a repository on the ladder, this old name elsewhere
# and wherever that file is missing.
LOCK_BRANCH = 'precedent-promote-lock'
LOCK_STALE_SECONDS = 15 * 60
_EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


def _lock_holder_name():
    """Who a claim names: whatever the environment says this session is
    called, else host and process -- enough to tell two windows apart."""
    import socket
    return (os.environ.get('PRECEDENT_SESSION_NAME')
            or f'{socket.gethostname()} pid {os.getpid()}')


def _lock_branch(root, write=False, say=None):
    """-> the lock's branch here (precedent_data_branches). `write` lets a
    ladder repository's first claim copy the old branch to its data- name."""
    try:
        here = str(pathlib.Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import precedent_data_branches as pdb
    except Exception:                                       # noqa: BLE001
        return LOCK_BRANCH
    try:
        if write:
            return pdb.name_for_write(root, pdb.LOCK, say=say)
        return pdb.name(root, pdb.LOCK)[0]
    except Exception:                                       # noqa: BLE001
        return LOCK_BRANCH


def _lock_state(root, branch=None):
    """-> (tip, subject, committed_at) of the lock branch on origin, or
    (None, None, None) when it does not exist yet."""
    branch = branch or _lock_branch(root)
    tip = _remote_tip(root, branch)
    if not tip:
        return None, None, None
    _run(root, 'fetch', '-q', 'origin', branch)
    subject = _git(root, 'log', '-1', '--format=%s', tip) or ''
    stamp = _git(root, 'log', '-1', '--format=%ct', tip) or '0'
    return tip, subject, int(stamp) if stamp.isdigit() else 0


def _fresh_hold(state):
    """-> 'held by X, N min ago' for a lock state holding a claim younger
    than LOCK_STALE_SECONDS, else None."""
    tip, subject, at = state
    if not tip or not (subject or '').startswith('held by') or not at:
        return None
    age = time.time() - at
    if age >= LOCK_STALE_SECONDS:
        return None
    return f'{subject.replace(" [skip ci]", "")}, {int(age // 60)} min ago'


def _old_name_hold(root, branch):
    """-> a fresh hold on the lock's old name, while this repository's lock
    is its data- name: a window on an older engine still claims the old
    branch, and the two must not run side by side. None otherwise."""
    if branch == LOCK_BRANCH:
        return None
    try:
        return _fresh_hold(_lock_state(root, LOCK_BRANCH))
    except Exception:                                         # noqa: BLE001
        return None


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
        branch = _lock_branch(root)
        return _fresh_hold(_lock_state(root, branch)) or _old_name_hold(root, branch)
    except Exception:                                         # noqa: BLE001
        return None


def _lock_push(root, parent, subject, body, branch=None):
    """Commit `subject` on top of `parent` and push it to the lock branch.
    -> (ok, commit, stderr). Never forced."""
    args = ['commit-tree', _EMPTY_TREE, '-m', f'{subject} [skip ci]', '-m', body]
    if parent:
        args += ['-p', parent]
    made = _run(root, *args, env=_merge_env(root))
    commit = made.stdout.strip()
    if made.returncode != 0 or not commit:
        return False, None, made.stderr.strip()
    branch = branch or _lock_branch(root)
    p = _run(root, 'push', '-q', 'origin', f'{commit}:refs/heads/{branch}')
    return p.returncode == 0, commit, p.stderr.strip()


def _lock_claim(root, say, what=None):
    """-> ('held', commit) when this window now holds the lock; ('busy',
    reason) when another does; ('none', reason) when the lock could not be
    used at all, and the Promote goes ahead without it, as before. `what`
    names a holder other than a Promote -- the merge gate's landing check
    (hold_for_landing) -- in the claim's subject."""
    branch = _lock_branch(root, write=True, say=say)
    tip, subject, at = _lock_state(root, branch)
    busy = _fresh_hold((tip, subject, at)) or _old_name_hold(root, branch)
    if busy:
        return 'busy', busy
    stale = ' (taking over a claim older than %d min)' % (LOCK_STALE_SECONDS // 60) \
        if tip and subject.startswith('held by') else ''
    ok, commit, err = _lock_push(
        root, tip, f'held by {_lock_holder_name()}' + (f' ({what})' if what else ''),
        f'{"A Promote" if not what else what[0].upper() + what[1:]} is running. '
        'tools/precedent_branches.py releases this when it ends; a claim older '
        f'than {LOCK_STALE_SECONDS // 60} minutes may be taken over.{stale}',
        branch)
    if ok:
        return 'held', commit
    if any(w in err for w in ('non-fast-forward', 'fetch first', 'rejected')):
        tip, subject, at = _lock_state(root, branch)
        who = subject.replace(' [skip ci]', '') if subject else 'another window'
        return 'busy', f'{who}, just now'
    return 'none', err[:200] or 'the lock commit could not be made'


def _lock_release(root, held, say):
    try:
        branch = _lock_branch(root)
        ok, _commit, err = _lock_push(root, held, 'free', 'No Promote is running.',
                                      branch)
    except CommitRefused as exc:
        branch, ok, err = _lock_branch(root), False, str(exc)
    if not ok:
        say(f'NOTE: could not release {branch} ({err[:160]}); it frees '
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


# A LANDING WAITS FOR THE LOCK (2026-10-10). Promote and the merge gate took
# this lock; the two landers -- --land here and tools/land_next.py -- did
# not. In a consumer where one session landed small edits on its landing
# branch every thirty to sixty seconds, the queue lander's six attempts
# across two runs all ended "push rejected": each attempt re-merged,
# resynced and re-checked for about 25 seconds, so the branch had always
# moved before the push. Starting over at once could never win that race,
# and backing off alone only makes losing it slower. Holding the lock
# from the merge to the push makes landings take turns; a busy lock is
# waited out, never a failure, up to LOCK_WAIT_SECONDS.
LOCK_WAIT_SECONDS = 10 * 60


def wait_for_landing_lock(root, what, say=print, limit=LOCK_WAIT_SECONDS,
                          sleep=None, clock=None, jitter=None):
    """Claim the lock for a landing, waiting while another window holds it.
    -> (state, info) as _lock_claim: ('held', commit) once claimed, to be
    freed with release_hold; ('none', reason) when the lock cannot be used
    at all, and the landing goes ahead without it, as before; ('busy',
    holder) when it is still held after `limit` seconds. Each wait doubles,
    from 5 seconds up to 30, times a random 0.5-1.5, so two waiting windows
    do not retry in step."""
    import random
    sleep, clock = sleep or time.sleep, clock or time.monotonic
    jitter = jitter or random.random
    start, pause = clock(), 5.0
    while True:
        state, info = _lock_claim(root, say, what=what)
        waited = clock() - start
        if state != 'busy' or waited >= limit:
            return state, info
        nap = min(pause * (0.5 + jitter()), max(limit - waited, 0.0))
        say(f'the landing lock is held ({info}); waiting {nap:.0f}s '
            f'({waited:.0f}s so far, at most {limit // 60} min).')
        sleep(nap)
        pause = min(pause * 2, 30.0)


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
    lines; others is None when this session's ID is unknown, and nothing is
    marked then. A commit is this session's only when its message carries a
    Claude-Session line naming this session.

    `work` decides nothing (kept for the callers' note). Being on the
    session's own branch said nothing: a feature branch is cut from
    staging and carries everything Booked there before it, and a fix
    branch carries the whole batch. Found 2026-10-06, a Produce of fourteen
    commits, five of them other sessions', marked none."""
    sid = _this_session_id() if sid is None else sid
    if not sid:
        return list(batch), None
    lines, others = [], []
    for line in batch:
        sha = line.split(' ', 1)[0]
        body = _git(root, 'log', '-1', '--format=%B', sha) or ''
        if any(l.startswith('Claude-Session:') and l.rstrip().endswith(sid)
               for l in body.splitlines()):
            lines.append(line)
        else:
            lines.append(f'{line}   {OTHER_WORK_MARK}')
            others.append(line)
    return lines, others


def _other_work_note(others, work=None):
    if others is None:
        return ('\nThis session\'s ID is unknown here, so no commit is marked '
                'as another session\'s: read the list before approving it.')
    if not others:
        return ''
    return (f'\n{len(others)} of these commit(s) do not carry this session\'s '
            f'Claude-Session line: someone else made them. Name them to the '
            f'person when asking to approve this move.')


def promotion_step(root, to=None, work=None):
    """-> (step, why): which Promote to run -- MAIN (staging into main) or
    None (nothing waiting, or nothing a Promote may do here).

    Work reaches staging by Booked (--land); a Promote only moves staging
    into main (Morgan, 2026-10-17, strength: decided). Asked for a step
    into staging, it says so and moves nothing. `work`, the branch the session was just on, still decides:
    not on staging yet means it must be Booked first."""
    staging = staging_branch(root)
    if staging == MAIN:
        return None, f'{MAIN} is the staging tier here, so work lands there directly'
    if to == STAGING:
        return None, (f'there is no step into {staging} any more: work reaches '
                      f'{staging} by Booked (--land), and a Promote moves '
                      f'{staging} into {MAIN}')
    _run(root, 'fetch', '-q', 'origin', staging, MAIN)
    stip, mtip = _remote_tip(root, staging), _remote_tip(root, MAIN)
    if work:
        _run(root, 'fetch', '-q', 'origin', work)
        sha = _git(root, 'rev-parse', '--verify', '--quiet', f'{work}^{{commit}}') \
            or _git(root, 'rev-parse', '--verify', '--quiet', f'origin/{work}^{{commit}}')
        if not sha:
            return None, (f'{work!r} is not a branch or commit this checkout can '
                          f'see, so nothing was chosen from it')
        if not (stip and _run(root, 'merge-base', '--is-ancestor', sha,
                              stip).returncode == 0):
            return None, (f'the work just done ({work}) is not on {staging} yet: '
                          f'Book it there first (--land), then Promote')
    if to == MAIN or (stip and mtip and _new_commits(root, mtip, stip)):
        return MAIN, ('asked for by name (--to main)' if to == MAIN else
                      f'{staging} has work {MAIN} lacks')
    if not mtip:
        return None, f'origin has no {MAIN}'
    return None, f'{staging} and {MAIN} carry the same work'


# What the run that is under way decided, for promote_result_line: set by
# _verdict at the point each path knows it, read once the run is over.
_RESULT = {}


def _verdict(text, move=None):
    """Record this Promote's verdict, one line, for its closing result line."""
    _RESULT['verdict'] = ' '.join(str(text).split())
    if move:
        _RESULT['move'] = move


# A failure never carries its success word (2026-10-11: a script searching
# "LANDED" read "NOT LANDED" as a landing): LAND REFUSED and PROMOTE REFUSED,
# never NOT LANDED or NOT PROMOTED. The old prefix stays readable here.
_REASON_PREFIXES = ('PROMOTE REFUSED: ', 'NOT PROMOTED: ', 'PROMOTE NOT FINISHED, ')


def promote_result_line(root, rc, to=None, last=''):
    """-> the single line a Promote ends on: which move, and what became of
    it. `rc` is the run's exit status (None when an error stopped it) and
    `last` the last thing it said, the reason when no path recorded one."""
    try:
        staging = staging_branch(root)
    except Exception:
        staging = STAGING
    move = _RESULT.get('move') or (
        f'{MAIN} <- {staging}')
    verdict = _RESULT.get('verdict')
    if not verdict:
        reason = ' '.join((str(last or '').strip().splitlines() or [''])[0].split())
        for prefix in _REASON_PREFIXES:
            if reason.startswith(prefix):
                reason = reason[len(prefix):]
        reason = reason[:240] or 'see the lines above'
        if rc is None:
            verdict = f'PROMOTE REFUSED: the run stopped on an error ({reason})'
        elif rc == 0:
            verdict = f'NOTHING TO PROMOTE: {reason}'
        else:
            verdict = f'PROMOTE REFUSED: {reason}'
    return f'PROMOTE RESULT: {move}: {verdict}'


def promote(root, say=print, to=None, work=None, fast=False,
            despite_failed_tests=False, no_full_after=False):
    """Run a Promote (_promote_run) and end it, on every path -- an error and
    a refusal included -- with promote_result_line as the last thing said.
    `fast` and `despite_failed_tests` are the fast move into main's
    (_promote_to_main). -> _promote_run's exit status."""
    _RESULT.clear()
    last = ['']

    def heard(msg=''):
        last[0] = msg
        say(msg)
    rc = None
    try:
        rc = _promote_run(root, heard, to, work, fast, despite_failed_tests,
                          no_full_after)
        return rc
    finally:
        say(promote_result_line(root, rc, to, last[0]))
        _RESULT.clear()


def _promote_run(root, say=print, to=None, work=None, fast=False,
                 despite_failed_tests=False, no_full_after=False):
    """Pick the step (promotion_step), SAY it, then run it, one window at a
    time. -> 0 promoted, nothing to promote, or another window already
    promoting; 1 refused (a failing check, a conflict, a race);
    PROMOTE_MAIN_NOT_MOVED when staging into main is ready for its pull
    request and main has not moved yet."""
    if not repo_has_tiers(root) and not _git(
            root, 'rev-parse', '--verify', '--quiet',
            f'refs/remotes/origin/{staging_branch(root)}'):
        # Nothing ever creates tiers in a repository that did not ask for
        # them (spec/LADDER_OPT_IN_PLAN.md, Morgan 2026-10-02: "Yes"). Before
        # this, a Promote here announced a move, failed on the missing
        # staging branch, and left its lock branch behind on origin.
        say(f'this repository has only {MAIN}, and work lands there '
            f'directly, so there is nothing to promote.')
        _verdict(f'NOTHING TO PROMOTE: this repository has only {MAIN}')
        return 0
    step, why = promotion_step(root, to, work)
    staging = staging_branch(root)
    if step is None:
        say(f'nothing to promote: {why}.')
        _verdict(f'NOTHING TO PROMOTE: {why}')
        return 0
    # The one line a person reads first: which move this is, in these words.
    say(f'Now promoting from {staging} to {MAIN} ({why}).')
    run = _promote_to_main
    kw = {'work': work} if work else {}
    if fast and run is _promote_to_main:
        kw.update(fast=True, despite_failed_tests=despite_failed_tests,
                  no_full_after=no_full_after)
    if kw:
        run = (lambda r, s, f=run, kw=kw: f(r, s, **kw))
    state, info = _lock_claim(root, say)
    if state == 'busy':
        say(f'another window is promoting or landing right now ({info}), so this one did '
            f'nothing. Do not Promote again while it runs.')
        _verdict(f'PROMOTE REFUSED: another window is promoting or landing right now ({info}); '
                 f'do not Promote again while it runs')
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


# PROMOTE'S OWN BRANCHES ARE NAMED LIKE A SESSION'S (Morgan, 2026-10-06,
# strength: decided: "isn't our URL format for temporary GitHub repo URLs to
# start with the timestamps then the slug then a few random characters? ...
# let's do that"). The fix branch and the copy a pull request into main
# comes from were named promote-fix-DATE and to-main-DATE, outside the
# <date>-<slug>-<session>-<random> format every other temporary branch takes from
# tools/precedent_branch_name.py, so they led back to no session. They are
# named by that tool now. The old names are still RECOGNIZED -- a branch
# already on origin, an engine copy elsewhere -- by the is_* functions below,
# the one place that answers "is this a Promote's branch".
FIX_SLUG = 'promote-fix'
COPY_SLUG = 'promote-to-main'
NOT_DUE_SLUG = 'promote-to-main-not-due'
# The person's GitHub username may sit between the date and the slug
# (Morgan, 2026-10-11: <date>-<username>-<slug>-<session>-<random>).
_PROMOTE_MADE_RE = re.compile(
    r'(?:^|/)\d{4}-\d\d-\d\d-(?:[a-z0-9][a-z0-9-]*?-)?'
    r'(promote-fix|promote-to-main(?:-not-due)?)'
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
    """-> <date>-<slug>-<session ID's end>-<random> from
    precedent_branch_name.py (random characters in the session part too
    where there is no session ID), or None when that tool cannot be loaded.
    Every copy carries the random part since 2026-10-11, so a session's
    second Promote of the day no longer gets a longer name than its first."""
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
    names, or does not look at copy names at all (or none is installed). A
    repository that has not taken the workflow carrying them would run its
    test on a not-due copy, so its copies keep the old names until Update
    Vendors brings it. A workflow that never names a copy (BestPractice's
    own deep check runs on every pull request into main) is indifferent, so
    it no longer holds the copies to the old names (Morgan, 2026-10-09:
    "those should be aligned with the format I like: 2026-12-31-slug-abcdef")."""
    tip = _remote_tip(root, staging_branch(root))
    if not tip:
        return False

    def knows(p):
        body = _git(root, 'show', f'{tip}:{p}') or ''
        return COPY_NAME_MARKER in body or 'to-main-' not in body
    return all(knows(p) for p, _d in github_tests(root, tip))


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
    if not _remote_tip(root, base):
        return base
    # The moment is a second: two Promotes in one second named the same
    # copy and the second push was refused as non-fast-forward (2026-10-19:
    # "the work just done, on staging, goes into main" failed only on
    # GitHub's faster runner, run 39259090526). Count up until one is free.
    name, n = f'{prefix}{moment}', 1
    while _remote_tip(root, name):
        n += 1
        name = f'{prefix}{moment}-{n}'
    return name


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


def _promote_to_main(root, say=print, work=None, fast=False,
                     despite_failed_tests=False, no_full_after=False):
    """Staging into main: the full check on exactly what main would hold,
    then a throwaway copy of staging for the pull request into main, whose
    GitHub test is the last gate (spec/BRANCH_TIERS_PLAN.md: main gets "all
    those local tests AND the most important GitHub test"). Main is moved by
    that pull request, never by this script. -> PROMOTE_MAIN_NOT_MOVED when
    the copy is ready and main has not moved yet; 0 nothing to promote; 1
    refused. `fast` is _promote_to_main_fast instead."""
    if fast:
        return _promote_to_main_fast(root, say, work, despite_failed_tests,
                                     no_full_after)
    staging = staging_branch(root)
    held = main_test_holds_produce(root, say)
    if held:
        say(f'PROMOTE REFUSED: {held}')
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
        _verdict(f'NOTHING TO PROMOTE: {MAIN} already has everything on '
                 f'{staging} ({stip})', move=f'{MAIN} <- {staging}')
        return 0
    with _Worktree(root, mtip) as wt:
        copy_tip = main_copy_tip(
            wt, mtip, stip,
            f'Promote {staging} into {MAIN} ({len(batch)} commit(s))')
        if not copy_tip:
            say(f'{staging} does not merge cleanly into {MAIN}; nothing was pushed. '
                f'{MAIN} has changes of its own on the same lines -- merge {MAIN} '
                f'into a branch, resolve it there, land it on {staging} '
                f'(`{LAND_COMMAND} BRANCH`), and Promote again.')
            return 1
        # THE COPY IS THIS MERGE, NOT STAGING'S TIP (2026-10-07). Pushed as
        # staging's tip, the pull request's merge into main had main's last
        # commit as a parent the tested head did not contain -- after any
        # earlier Produce, GitHub's own merge commit -- so the push test on
        # main could not tell it had just passed, re-ran the whole suite
        # (30 minutes that night) and the next Produce waited on it
        # (todo-2026-10-07-main-push-test-reruns-a-tree-its-pull-request-passed).
        # This commit contains main, is exactly what the full check below
        # judges, and is what the pull request's GitHub test then runs.
        # Where main is already in staging it is staging's tip itself, and
        # main_copy_current is what the merge check accepts (2026-10-08).
        say(f'checking {len(batch)} commit(s) from {staging} with the full push check...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, FULL, dest=MAIN)
        if ok:
            # What GitHub's test of the pull request into main will judge
            # against main, judged here first (a few seconds; 2026-10-17).
            against = _against_main(root, wt, staging, mtip, say)
            if against:
                ok = False
                out += '\n' + '\n'.join(f'  {f["check"]}: {f["line"]}'
                                         for f in against)
        took = time.monotonic() - t0
    review = _upstream_review(root, None, 'produce', out, f'{mtip}..{stip}')[0] \
        if ok else []
    if not ok:
        say(f'PROMOTE REFUSED: the full check failed on {staging} merged into '
            f'{MAIN}, so nothing was pushed. The batch was:\n  '
            + '\n  '.join(batch) + f'\n\n{out}\n\nFix it on a branch, land it on '
            f'{staging} (`{LAND_COMMAND} BRANCH`), and Promote again.')
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
    p = _run(root, 'push', '-q', 'origin', f'{copy_tip}:refs/heads/{copy}')
    if p.returncode != 0:
        say(f'could not push the copy {copy}: {p.stderr.strip()[:200]}')
        return 1
    shown, others = mark_other_work(root, batch, work)
    say(f'{MAIN.upper()} HAS NOT MOVED YET: this Promote exits '
        f'{PROMOTE_MAIN_NOT_MOVED}, not 0, until the pull request below is merged.\n'
        f'READY FOR {MAIN.upper()}: {len(batch)} commit(s) from {staging} '
        f'({stip[:12]}), '
        + ('which already contains ' + MAIN if copy_tip == stip else
           f'merged with {MAIN} as {copy_tip[:12]}')
        + f' and pushed as {copy}:\n  ' + '\n  '.join(shown)
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
        + (f'and merge it with a merge commit{_at_head(copy_tip)}' if none_runs else
           f'wait for its GitHub test with\n'
           f'  python3 tools/precedent_branches.py --wait-main-test {copy}\n'
           f'and merge it with a merge commit once that says PASSED'
           + ('' if due else ' (or, for this not-due copy, NOT DUE)')
           + _at_head(copy_tip)) +
        f'. Never open it from {staging} itself.')
    _verdict(f'READY FOR {MAIN.upper()}: open a pull request from {copy} into '
             f'{MAIN}, then merge with expectedHeadSha {copy_tip}'
             + ('' if none_runs else ' once its GitHub test says PASSED'
                + ('' if due else ' (or NOT DUE)'))
             + f'; {MAIN} has not moved yet', move=f'{MAIN} <- {staging}')
    for line in review:
        say(line)
    return PROMOTE_MAIN_NOT_MOVED


# THE FAST MOVE INTO MAIN (2026-10-09, the approved plan that makes the
# move into main fast for whoever asks for it; the default since
# 2026-10-11, promote_args). The full local suite is not run: it is --run-tests, asked
# for when wanted. This runs the quick checks on the change, builds the copy
# for the pull request exactly as the full move does (main_copy_tip: staging
# merged into main, so nothing that reached main directly is dropped), and
# says to merge it at once. GitHub's test still runs -- after the merge --
# and --wait-main-test waits on it.
#
# A FAILED --run-tests ON THIS VERY COMMIT ASKS, NEVER REFUSES (Morgan,
# 2026-10-09: "often these tests fail for trivial reasons, and sometimes I
# really just need to push something to live quickly"). It prints each
# failing check on a line and exits PROMOTE_ASKS; --despite-failed-tests is
# the person's yes. A failure recorded on an older commit says so, as stale,
# and does not ask.
#
# The merge gate reads FAST_MAIN_RECORD to know this copy took the quick
# checks on purpose: it checks the merge at the quick tier, before and after,
# instead of running the full suite the move skipped.
PROMOTE_ASKS = 4
DESPITE_FLAG = '--despite-failed-tests'
FAST_MAIN_RECORD = 'precedent-fast-main.json'
FAST_MAIN_KEPT = 20


def _fast_main_path(root):
    common = _git(root, 'rev-parse', '--git-common-dir')
    if not common:
        return None
    path = pathlib.Path(common)
    return (path if path.is_absolute() else pathlib.Path(root) / path) / FAST_MAIN_RECORD


def fast_main_copy(root, sha):
    """-> the record of a fast move into main whose copy is `sha`, or None."""
    path = _fast_main_path(root) if sha else None
    data = _read_json(path) if path else None
    entry = (data or {}).get(sha)
    return entry if isinstance(entry, dict) else None


def _record_fast_main(root, sha, entry):
    path = _fast_main_path(root)
    if not path:
        return
    data = _read_json(path) or {}
    data[sha] = entry
    for old in sorted(data, key=lambda k: str(data[k].get('at', '')))[:-FAST_MAIN_KEPT]:
        data.pop(old, None)
    try:
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    except OSError:
        pass


def full_check_owed(root, fetch=True):
    """-> [(copy_sha, state, line)] for each fast move into main recorded
    here that needs the full local suite after it (full_check_after), is on
    main now, and has no full run on main covering it: state 'none' (never
    started) or 'failed'. A run still going counts as started. [] when none
    is owed, or nothing can be read. The end-of-turn check reads this."""
    try:
        path = _fast_main_path(root)
        data = (_read_json(path) if path else None) or {}
        pending = [(sha, e) for sha, e in data.items()
                   if isinstance(e, dict) and e.get('full_after')
                   and not e.get('full_after_done')]
        if not pending:
            return []
        if fetch:
            _run(root, 'fetch', '-q', 'origin', MAIN)
        rec = run_tests_record(root, MAIN) or {}
        out, done = [], []
        for sha, e in pending:
            if _run(root, 'merge-base', '--is-ancestor', sha,
                    f'origin/{MAIN}').returncode != 0:
                continue                            # not merged: nothing owed yet
            ran = rec.get('commit')
            covers = bool(ran) and _run(root, 'merge-base', '--is-ancestor',
                                        sha, ran).returncode == 0
            if covers and rec.get('result') == 'passed':
                done.append(sha)
                continue
            if covers and rec.get('result') == 'running':
                continue
            if covers and rec.get('result') == 'failed':
                out.append((sha, 'failed', ', '.join(
                    f.get('check', '?') for f in rec.get('failed') or [])
                    or 'see its output'))
            else:
                out.append((sha, 'none', e.get('full_after_why') or ''))
        if done:
            for sha in done:
                data[sha]['full_after_done'] = True
            try:
                path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
            except OSError:
                pass
        return out
    except Exception:                                       # noqa: BLE001
        return []


def failed_tests_ask(root, branch, tip):
    """-> (asks, lines): what the last --run-tests on `branch` says about its
    tip `tip`. `asks` is True only when it FAILED on exactly that commit;
    `lines` is what to print -- the failures, or a stale or passing note."""
    rec = run_tests_record(root, branch)
    if not rec:
        return False, [f'no --run-tests result is on record here for {branch}.']
    when = rec.get('at', 'time not recorded')
    if rec.get('commit') != tip:
        state = 'failed' if rec.get('result') == 'failed' else 'passed'
        return False, [f'the last --run-tests on {branch} {state} on an older '
                       f'commit ({str(rec.get("commit"))[:12]}, {when}); it is '
                       f'STALE -- {branch} is at {tip[:12]} now -- so it decides '
                       f'nothing here.']
    if rec.get('result') == 'running':
        return False, [f'--run-tests is still running on this commit, or was '
                       f'stopped before it finished ({tip[:12]}, started {when}); '
                       f'it has passed nothing yet.']
    if rec.get('result') != 'failed':
        return False, [f'--run-tests PASSED on this commit ({tip[:12]}, {when}).']
    failed = rec.get('failed') or []
    return True, ([f'--run-tests FAILED on this commit ({tip[:12]}, {when}), '
                   f'{len(failed)} failing check(s):']
                  + [f'  {f.get("check")}: {f.get("line") or "(no detail)"}'
                     for f in failed])


NO_FULL_AFTER_FLAG = '--no-full-after'
UNCHECKED_REF = 'refs/precedent/main-unchecked'
# Prose a reader reads, which the quick checks already lint and link-check:
# a move of nothing else needs no full suite (Morgan, 2026-10-09: "I don't
# think we should force the big test for small content updates"). Rules,
# tools, hooks, workflows, settings and instruction files are never prose.
_PROSE_SUFFIXES = ('.md', '.txt')
_NEVER_PROSE = ('practices/', 'local/practices/', 'tools/', '.claude/',
                '.github/', 'templates/', 'doc-recipes/')
_INSTRUCTION_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md')


def only_prose_changed(root, base, tip):
    """-> True when every path that differs between `base` and `tip` is
    prose: a .md or .txt file outside the rule, tool, hook, workflow and
    template trees, and not an instructions file."""
    changed = [p for p in (_git(root, 'diff', '--name-only', base, tip) or '').splitlines()
               if p.strip()]
    if not changed:
        return False
    return all(p.endswith(_PROSE_SUFFIXES)
               and not p.startswith(_NEVER_PROSE)
               and p.rsplit('/', 1)[-1] not in _INSTRUCTION_FILES
               for p in changed)


def full_check_after(root, test_runs, stip, mtip, asked_fast=False):
    """-> (needed, why): does a fast move of staging `stip` into main `mtip`
    need the full local suite run on main after the merge? Only when all
    four of Morgan's conditions hold (2026-10-09): GitHub's test does not run
    on it (`test_runs` false: not due, or none installed); no Debut (Run
    tests) passed on exactly this staging and main; more than prose
    changed; and the person did not ask for a fast one (`asked_fast`)."""
    if test_runs:
        return False, 'GitHub\'s test runs on it after the merge'
    rec = run_tests_record(root, staging_branch(root)) or {}
    if (rec.get('result') == 'passed' and rec.get('commit') == stip
            and rec.get('main') == mtip):
        return False, (f'Debut (Run tests) already passed on exactly this '
                       f'({stip[:12]}, with {MAIN} at {mtip[:12]})')
    if only_prose_changed(root, mtip, stip):
        return False, 'only prose changed, which the quick checks cover'
    if asked_fast:
        return False, ('you asked for a fast one, so no full check runs on it '
                       f'now; {MAIN} is marked as moved without one until the '
                       f'next full run')
    return True, (f'GitHub\'s test does not run on it, so the full local suite '
                  f'runs on {MAIN} here after the merge')


def mark_main_unchecked(root, sha):
    """Record on origin that main moved without a full check, at `sha`, the
    first such move: one ref, kept until a full run clears it, so a run of
    fast moves is seen from any session, not only this container's."""
    if _git(root, 'ls-remote', 'origin', UNCHECKED_REF):
        return
    _run(root, 'push', '-q', 'origin', f'{sha}:{UNCHECKED_REF}')


def main_unchecked(root, fetch=True):
    """-> (since_sha, moves) when main has moved without a full check since
    since_sha (moves: how many merges into main since then, at least 1), or
    None."""
    line = _git(root, 'ls-remote', 'origin', UNCHECKED_REF) if fetch else ''
    since = (line or '').split()[0] if line else ''
    if not since:
        return None
    if fetch:
        _run(root, 'fetch', '-q', 'origin', MAIN, since)
    merges = _git(root, 'rev-list', '--count', '--first-parent', '--merges',
                  f'{since}..origin/{MAIN}') or '0'
    try:
        n = int(merges) + 1
    except ValueError:
        n = 1
    return since, n


def clear_main_unchecked(root, checked):
    """A full check passed on `checked`, a commit of main: drop the mark when
    it covers the first unchecked move. Never raises."""
    try:
        line = _git(root, 'ls-remote', 'origin', UNCHECKED_REF) or ''
        since = line.split()[0] if line else ''
        if not since:
            return False
        _run(root, 'fetch', '-q', 'origin', since)
        if _run(root, 'merge-base', '--is-ancestor', since, checked).returncode == 0:
            _run(root, 'push', '-q', 'origin', f':{UNCHECKED_REF}')
            return True
    except Exception:                                       # noqa: BLE001
        pass
    return False


def _main_test_note(root):
    """One look, never a wait, at main's own GitHub test: a line to say when
    it is failing or still running, else ''."""
    try:
        mtip = _remote_tip(root, MAIN)
        tests = github_tests(root, mtip) if mtip and _gets_github_test(root, MAIN) else []
        if not tests:
            return ''
        state, detail = github_test_state(root, mtip, tests)
    except Exception:                                       # noqa: BLE001
        return ''
    if state in ('failed', 'running'):
        return (f'NOTE: {MAIN}\'s own GitHub test is {state} on its tip '
                f'({mtip[:12]}: {detail}). This move does not wait on it.')
    return ''


def _promote_to_main_fast(root, say=print, work=None, despite_failed_tests=False,
                          no_full_after=False):
    """The fast move into main: quick checks, the copy, the merge
    instruction, and GitHub's test after the merge. -> PROMOTE_MAIN_NOT_MOVED
    when the copy is ready; PROMOTE_ASKS when --run-tests failed on this
    commit and the person has not said to go on; 0 nothing to promote; 1
    refused."""
    staging = staging_branch(root)
    move = f'{MAIN} <- {staging}'
    _run(root, 'fetch', '-q', 'origin', staging, MAIN)
    stip, mtip = _remote_tip(root, staging), _remote_tip(root, MAIN)
    if not stip or not mtip:
        say(f'origin lacks {staging if not stip else MAIN}, so there is nothing '
            f'to promote into {MAIN}.')
        return 1
    batch = _new_commits(root, mtip, stip)
    if not batch:
        say(f'nothing to promote: {MAIN} already has everything on {staging}.')
        _verdict(f'NOTHING TO PROMOTE: {MAIN} already has everything on '
                 f'{staging} ({stip})', move=move)
        return 0
    asks, lines = failed_tests_ask(root, staging, stip)
    if asks and not despite_failed_tests:
        say('\n'.join(lines))
        say(f'ASK THE PERSON, in these words: "Run tests found {len(lines) - 1} '
            f'failure(s) on {staging} (above). GitHub runs the same tests after '
            f'the merge, so a real one turns {MAIN} red until it is fixed. Run the '
            f'move anyway? Say yes to continue." On a yes, run this again with '
            f'{DESPITE_FLAG}. Nothing was pushed.')
        _verdict(f'ASKING: --run-tests failed on {staging} at {stip}; ask the '
                 f'person "Run the move anyway? Say yes to continue", and on a '
                 f'yes run again with {DESPITE_FLAG}; nothing was pushed',
                 move=move)
        return PROMOTE_ASKS
    for line in lines:
        say(line)
    if asks:
        say(f'going ahead anyway, as the person said ({DESPITE_FLAG}).')
    note = _main_test_note(root)
    if note:
        say(note)
    with _Worktree(root, mtip) as wt:
        copy_tip = main_copy_tip(
            wt, mtip, stip,
            f'Promote {staging} into {MAIN} ({len(batch)} commit(s))')
        if not copy_tip:
            say(f'{staging} does not merge cleanly into {MAIN}; nothing was pushed. '
                f'{MAIN} has changes of its own on the same lines -- merge '
                f'origin/{MAIN} into your branch, resolve it there, land it on '
                f'{staging}, and promote again.')
            return 1
        say(f'checking {len(batch)} commit(s) from {staging} with the quick '
            f'checks -- the full local suite is not run on a fast move...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, BASIC, dest=MAIN, since=mtip)
        if ok:
            # What GitHub's test of the pull request into main will judge
            # against main, judged here first (a few seconds; 2026-10-17).
            against = _against_main(root, wt, staging, mtip, say)
            if against:
                ok = False
                out += '\n' + '\n'.join(f'  {f["check"]}: {f["line"]}'
                                         for f in against)
        took = time.monotonic() - t0
    review = _upstream_review(root, None, 'produce', out, f'{mtip}..{stip}')[0] \
        if ok else []
    if not ok:
        say(f'PROMOTE REFUSED: the quick checks failed on {staging} merged into '
            f'{MAIN}, so nothing was pushed.\n\n{out}\n\nFix it, land the fix on '
            f'{staging}, and promote again.')
        return 1
    say(f'the quick checks passed, in {took:.0f}s.')
    due, _why = main_test_due(root, stip)
    none_runs = not github_tests(root, stip)
    copy = _to_main_copy(root, due)
    p = _run(root, 'push', '-q', 'origin', f'{copy_tip}:refs/heads/{copy}')
    if p.returncode != 0:
        say(f'could not push the copy {copy}: {p.stderr.strip()[:200]}')
        return 1
    shown, others = mark_other_work(root, batch, work)
    wait = (f'python3 tools/precedent_branches.py --wait-main-test {copy}')
    # A private repository tests main at most every N hours, and some have
    # no GitHub test at all: then the full suite runs here after the merge,
    # unless one of Morgan's other conditions says it is not needed
    # (full_check_after; 2026-10-09: "I want to make sure there's a full
    # check *somewhere* on the push to main, afterwards").
    test_runs = not none_runs and bool(due)
    skipped = not test_runs
    full_after, full_why = full_check_after(root, test_runs, stip, mtip,
                                            asked_fast=no_full_after)
    if skipped and no_full_after and not full_after and 'asked for a fast' in full_why:
        mark_main_unchecked(root, copy_tip)
    gh_line = ('no GitHub test runs here' if none_runs else
               f'GitHub\'s test is not due on this one ({_why})')
    after = (f'{gh_line}, so the full suite runs here instead, after the '
             f'merge: python3 tools/precedent_branches.py --run-tests {MAIN}, in '
             f'the background, and fix {MAIN} at once if it fails'
             if full_after else
             f'{gh_line}, and no full check is needed after it: {full_why}'
             if skipped else
             f'GitHub\'s test runs after the merge; wait on it with {wait} and '
             f'fix {MAIN} at once if it fails')
    _record_fast_main(root, copy_tip, {
        'copy': copy, 'staging': stip, 'main': mtip,
        'despite_failed_tests': bool(asks),
        'full_after': bool(full_after), 'full_after_why': full_why,
        'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')})
    say(f'{MAIN.upper()} HAS NOT MOVED YET: this Promote exits '
        f'{PROMOTE_MAIN_NOT_MOVED}, not 0, until the pull request below is merged.\n'
        f'READY FOR {MAIN.upper()} (FAST): {len(batch)} commit(s) from {staging} '
        f'({stip[:12]}), '
        + ('which already contains ' + MAIN if copy_tip == stip else
           f'merged with {MAIN} as {copy_tip[:12]}')
        + f' and pushed as {copy}:\n  ' + '\n  '.join(shown)
        + _other_work_note(others, work) + '\n\n'
        f'Next, and not by this script: open a pull request from {copy} into '
        f'{MAIN}, titled "Promote {staging} into {MAIN} ({len(batch)} '
        f'commit(s))", and merge it now with a merge commit{_at_head(copy_tip)}; '
        f'do not wait for GitHub\'s test first. Then: {after}. Never open it '
        f'from {staging} itself.')
    _verdict(f'READY FOR {MAIN.upper()} (FAST): open a pull request from {copy} '
             f'into {MAIN} and merge it now with expectedHeadSha {copy_tip}; '
             + (f'no GitHub test runs on this one, so do not wait for one; after '
                f'the merge run the full suite here with --run-tests {MAIN}'
                if full_after else
                f'no GitHub test runs on this one and no full check is needed '
                f'after it ({full_why})' if skipped else
                f'the GitHub test runs after the merge -- wait on it with '
                f'--wait-main-test {copy}')
             + f'; {MAIN} has not moved yet', move=move)
    for line in review:
        say(line)
    return PROMOTE_MAIN_NOT_MOVED


# WORK ONTO STAGING IS COMPOSED, CHECKED ONCE, THEN MOVED
# (spec/LADDER_OPT_IN_PLAN.md D10, Morgan 2026-10-03, strength: decided).
# The ladder is opt-in, so people off it push straight to main, and that is
# expected to go on. Their work is live for everyone already; what the
# ladder must not do is leave it out of staging until the next Produce
# meets it as a conflict. So one tree is built in a scratch worktree --
# staging, then main's new work, then the work being landed -- what main
# left stale is rebuilt, the check runs on it once, and only then does
# staging move to that commit.
#
# A failure moves nothing. The tree is put on a LOCAL fix branch (pushed
# only with a fix, 2026-10-06; see _not_finished), and the
# session fixes it there in the same turn, whoever's commit broke it ("if
# it fails because of a problem on main (caused by someone not using this
# process) -- then you have to fix it as part of this process"), and runs
# this again with --work FIX-BRANCH, which takes the fix in first.
FIX_PREFIX = 'promote-fix-'


def _compose(root, wt, parts, staging, say):
    """Merge each (label, sha, message) in `parts` into worktree `wt`'s HEAD,
    in order, by merge commits. One already in HEAD is skipped; a conflict
    only in generated files is rebuilt (_resolve_by_regenerating).
    -> (None, merged labels) or ((label, sha, files, why), merged) on a
    conflict nothing here rebuilds, the merge aborted and HEAD left as it
    was before it; `why` is _resolve_by_regenerating's."""
    env = _merge_env(root)
    merged = []
    for label, sha, message in parts:
        if _run(wt, 'merge-base', '--is-ancestor', sha, 'HEAD').returncode == 0:
            continue
        m = _run(wt, 'merge', '--no-ff', '-q', '-m', message, sha, env=env)
        if m.returncode != 0:
            done, files, why = _resolve_by_regenerating(wt, say)
            if done:
                done = _run(wt, 'commit', '-q', '--no-edit', env=env).returncode == 0
                why = why or 'the merge of the rebuilt files could not be committed'
            if not done:
                _run(wt, 'merge', '--abort')
                return (label, sha, files, why), merged
            say(f'{label} and the rest both changed {", ".join(files)}; generated, '
                f'so rebuilt from the merged sources rather than either side taken.')
        merged.append(label)
    return None, merged


def _from_above(root, staging, stip):
    """-> [(branch, tip, commits)] for main, wherever its tip brings `stip`
    (staging's tip) a file change: the work that reached it directly,
    without climbing. Fetches it."""
    above = []
    for branch in ((MAIN,) if staging != MAIN else ()):
        tip = _remote_tip(root, branch)
        if tip:
            _run(root, 'fetch', '-q', 'origin', branch)
            commits = drift(root, stip, tip)
            if commits:
                above.append((branch, tip, commits))
    return above


def _compose_onto(root, wt, staging, first, above, last, say):
    """THE composition every move into staging makes, in worktree `wt`
    checked out at staging's tip: the (label, sha, message) parts in `first`
    (a fix branch), then each branch in `above` (_from_above: what reached
    main directly), then the parts in `last` (the work landing); then the
    generated files that main's work left stale, rebuilt and committed.
    The Promote into staging, --land and --run-tests all compose here, so
    the reconciliation with main is one piece of code.
    -> (conflict, merged, rebuilt), conflict and merged as _compose's."""
    parts = list(first)
    for branch, tip, commits in above:
        parts.append((branch, tip, f'Bring {branch} into {staging}: {len(commits)} '
                      f'commit(s) made there directly'))
    parts += list(last)
    start = _git(wt, 'rev-parse', 'HEAD')
    conflict, merged = _compose(root, wt, parts, staging, say)
    rebuilt = []
    if not conflict and start:
        rebuilt += _commit_declared_rebuilt(root, wt, start, say)
    if not conflict and above:
        from_above = '; '.join(f'{b}\'s {len(c)} commit(s)' for b, _, c in above)
        rebuilt = _commit_rebuilt(root, wt, say, f'after {from_above} '
                                  f'made directly')
    return conflict, merged, rebuilt


def _commit_declared_rebuilt(root, wt, start, say):
    """Run every output a repository declares under "generated" whose files
    the composition since `start` touched, stage what it wrote -- dated
    names, deletions and all -- and commit it. -> the files rebuilt.

    TWO DAYS, TWO COPIES (2026-10-17). A builder that writes dated names
    (a dated download name, which a set's practice can ask for) gives two branches that rebuilt on
    different days two different files, so their merge never conflicts and
    keeps both. Rebuilding after the composition leaves one, from the merged
    sources. Only when the land touched a declared output: a land that
    changes nothing generated rebuilds nothing."""
    declared = _declared_generated(wt)
    if not declared:
        return []
    touched = [l for l in (_git(wt, 'diff', '--name-only', f'{start}..HEAD') or '')
               .splitlines() if l]
    globs = []
    for pats, argv in declared:
        if not any(fnmatch.fnmatchcase(t, g) for t in touched for g in pats):
            continue
        if not (pathlib.Path(wt) / argv[0]).is_file():
            continue
        r = subprocess.run([sys.executable, *argv], cwd=str(wt),
                           capture_output=True, text=True)
        if r.returncode != 0:
            say(f'NOTE: {" ".join(argv)} could not rebuild its declared output '
                f'over the composed tree, so it was left as merged and the full '
                f'check judges it: {(r.stdout + r.stderr).strip()[-300:]}')
            continue
        globs += pats
    if not globs:
        return []
    paths = set((_git(wt, 'ls-files') or '').splitlines()) | set(
        (_git(wt, 'ls-files', '--others', '--exclude-standard') or '').splitlines())
    mine = sorted(p for p in paths if p and any(fnmatch.fnmatchcase(p, g)
                                                 for g in globs))
    if mine:
        _run(wt, 'add', '-A', '--', *mine)
    changed = [l for l in (_git(wt, 'diff', '--cached', '--name-only') or '')
               .splitlines() if l]
    if changed:
        _run(wt, 'commit', '-q', '-m', 'Rebuild declared generated files over '
             'the composed tree\n\n' + '\n'.join(changed) + '\n\n'
             + _session_trailer(), env=_merge_env(root))
    return changed


def _commit_rebuilt(root, wt, say, why):
    """Rebuild the generated files in `wt` and commit any that changed.
    -> the files rebuilt."""
    rebuilt = _rebuild_generated(wt, say)
    if rebuilt:
        _run(wt, 'add', '-u')
        _run(wt, 'commit', '-q', '-m', f'Rebuild generated files {why}\n\n'
             + '\n'.join(rebuilt) + '\n\n' + _session_trailer(),
             env=_merge_env(root))
    return rebuilt


def _session_trailer():
    """The session-trailer line for a commit this module writes itself (a
    merge needs none: the trailer check passes merges). The session's own
    link when there is one, else the explicit form the check accepts. Found
    2026-10-07: a Debut's rebuild commit carried none, and the full check
    refused the Promote's own composition."""
    sid = _this_session_id()
    return (f'Claude-Session: https://claude.ai/code/session_{sid}' if sid
            else 'Session: none available (precedent_branches.py)')


# --land: WORK LANDS ON STAGING, RECONCILED WITH MAIN (2026-10-09). For a
# person who lands straight on staging (lands_on_staging). It composes in a
# throwaway worktree exactly as the Promote into staging does -- staging,
# then what reached main directly, then the work, each by a merge commit
# (_compose_onto) -- runs the quick checks on the change, and pushes staging
# to that commit, never forced, so a staging that moved meanwhile refuses
# the push and nothing is lost. Main is never touched; nothing is dropped
# from it or overwritten.
LAND_RESULT = 'LAND RESULT'
# WHAT IS BEING LANDED, TOLD TO THE PUSH'S OWN HOOKS (2026-10-17). git's
# pre-push sees only `<sha> -> refs/heads/staging` for a landing: the branch
# the work came from is gone by then, so a pre-push hook a practice declares
# could judge where work goes but never what was landed -- a harness-named
# branch reached staging by --land with every hook passing. So the landing's
# push carries the name it was asked to land (a branch, or HEAD's branch) in
# this variable, and it is pushed from the person's own checkout, not the
# throwaway worktree: hooks listed in untracked files there (a set the person
# brings, written at session start) are not in a fresh worktree, and did not
# run at all. Morgan, 2026-10-17: "Fix the other issues you found including
# the checks that never run" (very deep check of that day).
LANDING_SOURCE_ENV = 'PRECEDENT_LANDING_SOURCE'


def land(root, work=None, say=print):
    """Land `work` (a branch or commit; HEAD when None) on staging for a
    person who lands there, and end with one LAND RESULT line.
    -> 0 landed or nothing to land; 1 refused (a conflict, a failing quick
    check, staging moved); 2 not this person's route, or no such work."""
    staging = staging_branch(root)
    label = work or (_git(root, 'symbolic-ref', '--short', '-q', 'HEAD') or 'HEAD')
    verdict = ['LAND REFUSED: see the lines above']
    try:
        rc, verdict[0] = _land(root, work, label, staging, say)
        return rc
    finally:
        say(f'{LAND_RESULT}: {staging} <- {label}: {verdict[0]}')


def _land(root, work, label, staging, say):
    unknown = unknown_landing(root)
    if unknown:
        say(f'{unknown}. Nothing was landed.')
        return 2, f'LAND REFUSED: {unknown}'
    on, why = lands_on_staging(root)
    if not on:
        landing, lwhy = landing_branch(root)
        say(f'--land is the route for a person who lands work straight on '
            f'{staging} with {PROMOTE_ONLY_SETTING} on. Yours is {landing} '
            f'({lwhy}): land there as usual.')
        return 2, f'LAND REFUSED: your landing branch is {landing}'
    if work:
        name = work[len('origin/'):] if work.startswith('origin/') else work
        _run(root, 'fetch', '-q', 'origin', name)
    ref = work or 'HEAD'
    sha = (_git(root, 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}')
           or _git(root, 'rev-parse', '--verify', '--quiet', f'origin/{ref}^{{commit}}'))
    if not sha:
        say(f'{ref!r} is not a branch or commit this checkout can see.')
        return 2, f'LAND REFUSED: {ref} names no branch or commit here'
    state, info = wait_for_landing_lock(root, f'landing {label} on {staging}', say)
    if state == 'busy':
        say(f'LAND REFUSED, and {staging} did not move: the landing lock was still '
            f'held after {LOCK_WAIT_SECONDS // 60} minutes ({info}). Land again '
            f'once it is free.')
        return 1, f'LAND REFUSED: the landing lock stayed held ({info})'
    if state == 'none':
        say(f'NOTE: could not take the landing lock ({info}); going ahead '
            f'without it.')
        return _land_composed(root, sha, label, staging, why, say)
    old_handlers = _exit_cleanly_on_signal()
    try:
        return _land_composed(root, sha, label, staging, why, say)
    finally:
        _ignore_signals(old_handlers)
        try:
            _lock_release(root, info, say)
        finally:
            _restore_signals(old_handlers)


def _land_composed(root, sha, label, staging, why, say):
    """--land's composition, check and push, run while the lock is held."""
    _run(root, 'fetch', '-q', 'origin', staging)
    stip = _remote_tip(root, staging)
    if not stip:
        say(f'origin has no {staging} branch, so there is nowhere to land.')
        return 1, f'LAND REFUSED: origin has no {staging}'
    above = _from_above(root, staging, stip)
    carried = _run(root, 'merge-base', '--is-ancestor', sha, stip).returncode == 0
    if carried and not above:
        say(f'nothing to land: {staging} already has {label} ({sha[:12]}), and '
            f'everything {MAIN} has.')
        return 0, f'NOTHING TO LAND: {staging} already has {label} ({sha})'
    batch = [] if carried else _new_commits(root, stip, sha)
    last = [] if carried else [(label, sha, f'Land {label} on {staging} '
                                            f'({len(batch)} commit(s))')]
    from_above = '; '.join(f'{b}\'s {len(c)} commit(s)' for b, _, c in above)
    say(f'Now landing {label} on {staging} ({why})'
        + (f', bringing in {from_above} made directly first' if above else '')
        + '.')
    with _Worktree(root, stip) as wt:
        conflict, merged, rebuilt = _compose_onto(root, wt, staging, (), above,
                                                  last, say)
        if conflict:
            clabel, csha, files, why = conflict
            say(f'LAND REFUSED, and {staging} did not move: {clabel} ({csha[:12]}) '
                f'does not merge cleanly into {" + ".join([staging] + merged)} -- '
                f'{why}'
                + (f' ({", ".join(files)})' if files else '') + '. Merge '
                f'origin/{staging} and origin/{MAIN} into {label}, resolve it '
                f'there, push it, and land again.')
            return 1, (f'LAND REFUSED: {clabel} conflicts with '
                       f'{" + ".join([staging] + merged)}')
        new = _git(wt, 'rev-parse', 'HEAD')
        say(f'checking the composition -- {staging}'
            + (f', then {from_above} made directly' if above else '')
            + (f', then {len(batch)} commit(s) from {label}' if batch else '')
            + ' -- with the quick checks...')
        t0 = time.monotonic()
        ok, out = _check(root, wt, BASIC, dest=staging, since=stip)
        took = time.monotonic() - t0
        if not ok:
            say(f'LAND REFUSED, and {staging} did not move: the quick checks '
                f'failed on the composition, after {took:.0f}s.\n\n{out}\n\n'
                f'Fix it on {label} and land again.')
            return 1, 'LAND REFUSED: the quick checks failed on the composition'
        # The landing commit carries the review's Upstream-seen lines, so
        # Produce lists only what is new since (message only; the tree the
        # checks passed is unchanged).
        review, written = _upstream_review(root, wt if last else None, 'booked',
                                           out, f'{stip}..{sha}')
        if written:
            new = _git(wt, 'rev-parse', 'HEAD')
        # From the checkout, naming what is landed (LANDING_SOURCE_ENV).
        p = _run(root, 'push', '-q', 'origin', f'{new}:refs/heads/{staging}',
                 env=dict(os.environ, **{LANDING_SOURCE_ENV: label}))
    if p.returncode != 0:
        moved, said = refused_push(root, staging, new, p)
        if moved:
            say(f'{staging} moved while this ran, so nothing was pushed; land again. '
                f'({said[:200]})')
            return 1, f'LAND REFUSED: {staging} moved while this ran; land again'
        say(f'LAND REFUSED, and {staging} did not move: the push was refused, so '
            f'landing again would be refused the same way. What the push '
            f'said:\n{said[-1500:]}')
        if 'pull request' in said:
            say(_carry_composition_to_branch(root, label, new))
            say(pull_request_route_note(root, staging, checks_ran=True))
        first = next((ln for ln in said.splitlines() if ln.strip()), 'no reason given')
        return 1, f'LAND REFUSED: the push to {staging} was refused: {first[:200]}'
    say(f'the quick checks passed, in {took:.0f}s.')
    if batch:
        shown, others = mark_other_work(root, batch, label)
        say(f'LANDED {len(batch)} commit(s) from {label} on {staging} '
            f'({new[:12]}):\n  ' + '\n  '.join(shown) + _other_work_note(others, label))
    for branch, _tip, commits in above:
        say(f'BROUGHT IN {len(commits)} commit(s) made directly on {branch}, '
            f'checked with the rest:\n  ' + '\n  '.join(commits))
    if rebuilt:
        say(f'REBUILT what those left stale: {", ".join(rebuilt)}.')
    say(f'{staging} is at {new[:12]} now. The full suite has not run on it: '
        f'`python3 tools/precedent_branches.py --run-tests` runs it, moving '
        f'nothing.')
    for line in review:
        say(line)
    return 0, f'LANDED at {new}'


# --run-tests: THE FULL SUITE, ASKED FOR, MOVING NOTHING (2026-10-09). The
# same full push check a Promote into staging runs, on the same composition
# -- the branch, then main's direct work (_compose_onto) -- in a throwaway
# worktree. Nothing is pushed. The result is written to the checkout's git
# directory (RUN_TESTS_RECORD, one entry per branch), where a fast move into
# main reads it: the push check's receipts record only passes, by tree, and
# this needs the failures too, by the branch's commit.
RUN_TESTS_RECORD = 'precedent-run-tests.json'
RUN_TESTS_RESULT = 'RUN TESTS RESULT'


def _run_tests_path(root):
    common = _git(root, 'rev-parse', '--git-common-dir')
    if not common:
        return None
    path = pathlib.Path(common)
    return (path if path.is_absolute() else pathlib.Path(root) / path) / RUN_TESTS_RECORD


def run_tests_record(root, branch):
    """-> the last --run-tests result recorded for `branch` here, or None:
    {branch, commit, tested, main, result ('passed'|'failed'), failed
    [{check, line}], at}."""
    path = _run_tests_path(root)
    data = _read_json(path) if path else None
    entry = (data or {}).get(branch)
    return entry if isinstance(entry, dict) else None


def _record_run_tests(root, entry):
    path = _run_tests_path(root)
    if not path:
        return None
    data = _read_json(path) or {}
    data[entry['branch']] = entry
    try:
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    except OSError:
        return None
    return path


_FAILED_LINE = re.compile(r'precedent_push_check: FAILED -- (.+?) \(\d+s\)')


def _failed_checks(out):
    """-> [{check, line}]: each check the push check's output names as
    failed, with the first finding it printed for it."""
    names = []
    for m in _FAILED_LINE.finditer(out or ''):
        names = [n.strip() for n in m.group(1).split(',') if n.strip()]
    found = []
    for name in names:
        line = next((l.split(' | ', 1)[1].strip() for l in (out or '').splitlines()
                     if l.startswith(f'  {name} | ')), '')
        found.append({'check': name, 'line': line[:200]})
    if not found:
        last = next((l.strip() for l in reversed((out or '').splitlines())
                     if l.strip()), 'no output')
        found.append({'check': 'push check', 'line': last[:200]})
    return found


_VIOLATION_LINE = re.compile(r'^VIOLATION  (\S+)')


def _against_main(root, wt, branch, mtip, say):
    """-> [{check, line}]: what the checks that depend on the base find in
    `wt` when its change is measured from main's tip `mtip`, the way
    GitHub's test of the pull request into main measures it. [] when it is
    clean, when `branch` is main, or when main is unknown here.

    WHY (2026-10-17). The full suite measured staging against staging, so a
    Debut passed a tree that removed a file another page still named, and
    main went red after the Produce. Only these checks can answer
    differently against main, so only they run again
    (precedent_check.py's base_dependent_slugs): a few seconds, never a
    second suite (Morgan: "It should NOT")."""
    if branch == MAIN or not mtip:
        return []
    tool = pathlib.Path(wt) / 'tools' / 'precedent_check.py'
    if not tool.is_file():
        return []
    _run(root, 'fetch', '-q', 'origin', MAIN)
    if not _git(wt, 'rev-parse', '--verify', '--quiet', f'{mtip}^{{commit}}'):
        # The checks would quietly measure from staging instead.
        return [{'check': f'checks against {MAIN}', 'line':
                 f'{MAIN}\'s tip {mtip[:12]} could not be read here, so the '
                 f'change could not be judged against it'}]
    say(f'judging the change against {MAIN} too, the way the pull request '
        f'into {MAIN} will be judged (only the checks a base can change)...')
    env = dict(os.environ, PRECEDENT_CHANGED_SINCE=mtip)
    p = subprocess.run([sys.executable, str(tool), '--base-dependent'],
                       cwd=wt, capture_output=True, text=True, env=env)
    if p.returncode == 0:
        return []
    out = (p.stdout + p.stderr).splitlines()
    found = []
    for i, line in enumerate(out):
        m = _VIOLATION_LINE.match(line)
        if m:
            first = next((l.strip() for l in out[i + 1:i + 2]
                          if l.startswith('    ')), '')
            found.append({'check': f'{m.group(1)} (against {MAIN})',
                          'line': first[:200]})
    if not found:
        last = next((l.strip() for l in reversed(out) if l.strip()), 'no output')
        found.append({'check': f'checks against {MAIN}', 'line': last[:200]})
    return found


def run_tests(root, branch=None, say=print):
    """Run the full local suite on `branch` (default: the landing branch)
    composed with main's direct work, judge the checks a base can change
    against main too (_against_main), record the result, move nothing, and
    end with one RUN TESTS RESULT line. -> 0 passed, 1 failed, 2 no such
    branch."""
    branch = branch or landing_branch(root)[0]
    verdict = ['FAILED: see the lines above']
    try:
        rc, verdict[0] = _run_tests(root, branch, say)
        return rc
    finally:
        say(f'{RUN_TESTS_RESULT}: {branch}: {verdict[0]}')


def _run_tests(root, branch, say):
    _run(root, 'fetch', '-q', 'origin', branch)
    tip = _remote_tip(root, branch) or _git(
        root, 'rev-parse', '--verify', '--quiet', f'{branch}^{{commit}}')
    if not tip:
        say(f'{branch!r} is not a branch on origin or in this checkout.')
        return 2, f'NOT RUN: {branch} names no branch here'
    staging = staging_branch(root)
    above = ([a for a in _from_above(root, branch, tip) if a[0] == MAIN]
             if branch != MAIN else [])
    from_above = '; '.join(f'{b}\'s {len(c)} commit(s)' for b, _, c in above)
    mtip = _remote_tip(root, MAIN)
    say(f'running the full local suite on {branch} ({tip[:12]})'
        + (f' with {from_above} made directly, composed as a move into '
           f'{staging} would' if above else '')
        + ' -- nothing moves...')
    t0 = time.monotonic()
    # Said before the run, so the end-of-turn check can tell a full run on
    # main that is under way, in the background, from one never started.
    _record_run_tests(root, {'branch': branch, 'commit': tip, 'tested': None,
                             'main': mtip, 'result': 'running', 'failed': [],
                             'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')})
    with _Worktree(root, tip) as wt:
        conflict, merged, _rebuilt = _compose_onto(root, wt, branch, (), above,
                                                   (), say)
        tested = _git(wt, 'rev-parse', 'HEAD')
        if conflict:
            ok, out = False, ''
            failed = [{'check': 'merge with main', 'line':
                       f'{conflict[0]} ({conflict[1][:12]}) does not merge cleanly '
                       f'into {branch}: {conflict[3]}'
                       + (f' ({", ".join(conflict[2])})' if conflict[2] else '')}]
        else:
            ok, out = _check(root, wt, FULL, dest=staging)
            failed = [] if ok else _failed_checks(out)
            against = _against_main(root, wt, branch, mtip, say)
            if against:
                ok = False
                failed += against
    took = time.monotonic() - t0
    entry = {'branch': branch, 'commit': tip, 'tested': tested, 'main': mtip,
             'result': 'passed' if ok else 'failed', 'failed': failed,
             'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    where = _record_run_tests(root, entry)
    noted = f' Recorded in {where}.' if where else ' (could not be recorded)'
    if ok:
        if branch == MAIN and clear_main_unchecked(root, tip):
            noted += (f' {MAIN} had moved without a full check; this clears '
                      f'that mark.')
        say(f'the full local suite PASSED on {branch} ({tip}), in {took:.0f}s.'
            + noted)
        return 0, f'PASSED on {tip}; nothing moved'
    if out:
        say(out)
    say(f'the full local suite FAILED on {branch} ({tip}), after {took:.0f}s:\n  '
        + '\n  '.join(f'{f["check"]}: {f["line"]}' for f in failed) + noted
        + ' Nothing moved.')
    return 1, (f'FAILED on {tip}: ' + ', '.join(f['check'] for f in failed)
               + '; nothing moved')


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


FULL_FLAG = '--full'
BECAUSE_FLAG = '--because'


def full_route_refusal(kw):
    """-> why `kw` (from promote_args) is refused, or None. The full route
    into main is refused unless it carries the person's own words asking
    for it or agreeing to it, in --because."""
    if kw.get('fast', True):
        return None
    if (kw.get('because') or '').strip():
        return None
    return ('PROMOTE REFUSED: --full, the long way into main (the full local '
            'suite before the merge, and GitHub\'s test waited on first), is '
            'taken only when the person explicitly asks for it or agrees to it '
            '(Morgan, 2026-10-11). Without that, run the move with no flag: '
            'the quick checks, merge at once, and the tests after. If they '
            'did ask, run again with --because \'<their own words>\'.')


def promote_args(args):
    """-> the keyword arguments --promote's `args` ask promote() for, or None
    for a usage error.

    THE MOVE INTO MAIN IS THE FAST ONE UNLESS THE PERSON ASKS FOR THE FULL
    ONE (Morgan, 2026-10-11, strength: decided: "I think we should default
    to the fast route unless I explicitly agree to or request the slow
    route"). The slow route had stayed the default after the fast one was
    built, so a Produce run as the practice wrote it, with no flag, ran the
    full suite before the merge and waited on GitHub's test as well; that
    day it took most of an hour for a two-file change. --full asks for the
    old route; --fast is still taken, and changes nothing. The flag only
    matters when the step is the move into main: a Promote into staging
    is always fully checked.

    --full takes `--because '<the person's own words>'`, and without it is
    refused by full_route_refusal: the long way is taken only when the
    person agreed to it or asked for it, never on a session's own reading
    (Morgan, 2026-10-11: "only do the long way when explicitly authorized
    otherwise the short way with the tests after pushing it")."""
    rest, opts = list(args), {}
    while rest:
        if len(rest) >= 2 and rest[0] in ('--to', '--work', BECAUSE_FLAG):
            opts[rest[0][2:]] = rest[1]
            rest = rest[2:]
        elif rest[0] in ('--fast', FULL_FLAG, DESPITE_FLAG, NO_FULL_AFTER_FLAG):
            opts[rest[0]] = True
            rest = rest[1:]
        else:
            return None
    full = bool(opts.get(FULL_FLAG))
    if opts.get('--fast') and 'to' not in opts:
        opts['to'] = MAIN
    if opts.get('to', STAGING) not in (STAGING, MAIN):
        return None
    if full and (opts.get('--fast') or opts.get(DESPITE_FLAG)
                 or opts.get(NO_FULL_AFTER_FLAG)):
        return None
    if opts.get('because') is not None and not full:
        return None
    if opts.get('to') == STAGING and (opts.get('--fast') or full
                                      or opts.get(DESPITE_FLAG)
                                      or opts.get(NO_FULL_AFTER_FLAG)):
        return None
    return {'to': opts.get('to'), 'work': opts.get('work'), 'fast': not full,
            'because': opts.get('because'),
            'despite_failed_tests': bool(opts.get(DESPITE_FLAG)),
            'no_full_after': bool(opts.get(NO_FULL_AFTER_FLAG))}


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
    if argv[:1] == ['--promote']:
        kw = promote_args(argv[1:])
        if kw is None:
            print('usage: precedent_branches.py --promote [--to main] '
                  '[--work BRANCH-OR-COMMIT] [--full --because \'<their words>\' '
                  '| [--despite-failed-tests] [--no-full-after]]  (the move into '
                  'main is the fast one unless the person asks for --full)',
                  file=sys.stderr)
            return 2
        refused = full_route_refusal(kw)
        if refused:
            print(refused, file=sys.stderr)
            return 2
        because = kw.pop('because')
        if because:
            print(f'the full route into {MAIN}, because the person asked: '
                  f'{because.strip()!r}', flush=True)
        return promote(root, **kw)
    if argv[:1] == ['--land'] and len(argv) <= 2:
        return land(root, argv[1] if len(argv) == 2 else None)
    if argv[:1] == ['--run-tests'] and len(argv) <= 2:
        return run_tests(root, argv[1] if len(argv) == 2 else None)
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
        print(f'{MAIN}: the quick checks before a push, the full suite after')
        print(f'every other branch: {tier} ({why})')
        print(f'your work lands on: {landing} ({lwhy})')
        return 0
    print(f'staging      {staging_branch(root)}')
    print(f'main         {MAIN}')
    print(f'tier branches: {", ".join(sorted(set(tier_branches(root))))}')
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
