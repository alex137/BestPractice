#!/usr/bin/env python3
"""The verification harness — run before trusting any change here

verify_harness.py — phase-1 verification harness for the practice-engine
conversion (PRACTICE_ENGINE_PLAN.md, "The Verification Harness" and Sequence
row 1: "Practices are files; the catalogue regenerates byte-identically;
harness passes.").

Only the checks that are meaningful with no loader and no resident-tier
curation yet (both phase 2) actually run. The two the plan lists that
depend on those — resident subset, behavioral replay — are reported as
NOT YET APPLICABLE rather than skipped silently, so their absence stays
visible instead of reading as a pass.

Run:  python3 tools/verify_harness.py
      python3 tools/verify_harness.py --as-ci             # CI's two shards
      python3 tools/verify_harness.py --as-ci --isolated  # and CI's machine:
            a copy with no siblings, no personal config or source token,
            then the tests that went not-applicable there, run here
      PRECEDENT_CHECK_ONLY=check_a,check_b python3 tools/verify_harness.py
                                                 # just the tests you name
      python3 tools/verify_harness.py --record-new-times
            time only the tests tools/harness_check_times.json does not
            name, and add them -- commit it with a new test
      python3 tools/verify_harness.py --for-change origin/staging [--dry-run]
            just the tests a change since that ref reaches, within a
            60-second budget (--budget N); the push check runs this
      A full run started by hand refuses until it is given the person's
      go-ahead: --because '<their words>'. It states what it costs first.
Exit: 0 if every applicable check passes, 1 otherwise.
"""
import collections, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time
import importlib.util
import frontmatter_yaml

# A FIXTURE COMMIT IS NOT A PERSON'S COMMIT. Since 2026-09-07 the commit
# identity hook installs a backstop at core.hooksPath -- global, because that
# is the only hook location reaching a repository attached mid-session, which
# is where three wrong-author incidents came from. It therefore also reaches
# the throwaway repos this harness builds by the dozen, and refused them for
# a +0000 offset, taking the whole run down with a RuntimeError on the first
# `git commit -qm base`.
#
# Set here, once, for every subprocess: the override the backstop itself
# documents. It is the right answer rather than a workaround -- nothing in a
# temporary directory is anybody's authorship. The two checks that exercise
# the backstop's own refusals pop this back out of their fixture env, so the
# coverage is not weakened by it.
os.environ.setdefault('PRECEDENT_ALLOW_ANY_AUTHOR', '1')

# EVERY UPDATE VENDORS RUN HERE TESTS THIS CHECKOUT'S CODE. Run from a clone
# behind origin/main, precedent_update.py would otherwise run origin's
# newest green commit from a worktree (precedent_update_driver.py) -- and a
# case would quietly test that instead of the change in front of it. Set
# once, for every subprocess; the one check of the driver itself clears it.
os.environ.setdefault('PRECEDENT_UPDATE_RUN_IN_PLACE', '1')

# THE SAME BUG, ON THE CLOCK INSTEAD OF THE AUTHOR, and it escaped the fix
# above by one field. commit-identity.sh repoints `/etc/localtime` so a
# session's commits carry the declared offset without a `TZ=` prefix. In a
# FIXTURE there is no declared identity to resolve, so the hook falls to the
# last rung -- precedent.json's `fallback_timezone`, America/New_York -- and
# repoints the REAL container's system clock to it. Two call sites already
# pass PRECEDENT_LOCALTIME to redirect that write; anything reaching the hook
# by another path did not, and silently reset the machine.
#
# Measured 2026-09-11, before/after on a controlled run: `/etc/localtime` went
# from America/Argentina/Buenos_Aires to America/New_York across one
# `verify_harness.py` invocation, with the session's own clock left wrong
# afterwards. The cost is not the harness's -- it is the NEXT commit in the
# session, refused by the backstop for `author-date offset is '-0400'` with
# the author already correct, which reads as a fresh identity problem and is
# really this. It cost a day of re-fixing git config that was never wrong.
#
# Set here for the same reason and in the same way: nothing in a temporary
# directory owns the machine's clock. The two checks that exercise the hook's
# own timezone behaviour set their own PRECEDENT_LOCALTIME and are unaffected.
# (practice: fixture-owns-its-state -- one level further out, since the state
# the fixture was mutating belonged to the container rather than to git.)
os.environ.setdefault(
    'PRECEDENT_LOCALTIME', '/tmp/precedent-harness-localtime')

# Same problem, opposite direction: the harness must OWN the identity its
# fixtures assert on, instead of inheriting whatever the session exports.
#
# check_identity_reaches_a_repo_that_did_not_exist_yet builds a fixture in a
# temporary HOME, sets a global identity inside it, and asserts that commits
# made there used it. But GIT_AUTHOR_* outrank `git config --global user.*`,
# so a session that exports them -- the individual practice set's
# .claude/settings.json does -- authored every fixture commit as the real
# person, and 4 of that check's 11 stated cases failed, none of them real.
# Three failed in the confusing direction: a bot identity the fixture plants
# in LOCAL config was never the author any more, so the refusal the case
# waits for correctly did not fire, and a working backstop read as broken.
#
# Measured 2026-09-07, same tree, no code change: `1 failed` with the two
# variables exported, `0 failed` under `env -u`. Dropped here, once, rather
# than in the single fixture that happened to notice -- a fixture written
# later would inherit the same invisible dependency and the same hour of
# misdiagnosis. GIT_AUTHOR_DATE goes with them because the same check
# asserts on the author-date offset, which that variable equally overrides.
#
# The GIT_COMMITTER_* trio is deliberately NOT dropped: nothing in this
# harness or in commit-identity.sh reads the committer (the hook resolves
# `git var GIT_AUTHOR_IDENT`), so removing them would be a guess at a
# problem nobody has had.
for _var in ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 'GIT_AUTHOR_DATE'):
    os.environ.pop(_var, None)

# THE SAME SHAPE AGAIN, on the private-source credential, and this one made
# the harness's own result depend on which container it ran in. Two fixtures
# build a scenario where NO credential is available -- "with no base url the
# shared source is named on stderr as NOT in force", and "--write-session-hook
# with NO --repo-url ... degrades quietly" -- and then spawn a subprocess
# carrying the container's own environment. Where PRECEDENT_GIT_TOKEN and
# PRECEDENT_SOURCE_BASE_URL are set (INSTALL.md section 8, and every session
# since the credential route was verified on 2026-09-10), the subprocess
# picks them up, finds a URL after all, and does the thing the case says it
# must not do. The fixture never established the state it asserted on.
#
# Measured 2026-09-11, same tree, no code change: `4 failed` with the two
# variables in the environment, `2 failed` under `env -u` -- so a harness
# whose credentials happened to be missing reported two checks green that a
# credentialed one reported red, and neither run was wrong about itself.
#
# The first fix popped both variables inside the two fixtures that noticed,
# and those pops are still there -- they document the hazard where a reader
# meets it, and they hold if anything ever re-adds a credential in a
# narrower scope. They are not the whole fix, because a fixture written next
# month inherits the same invisible dependency and will not have read them.
# So the scrub is dropped here as well, once, for the same reason as the
# block above. (practice: fixture-owns-its-state, whose Rule says exactly
# this: clear the ambient inputs at the top, not in the fixture that
# happened to notice.)
#
# A fixture that genuinely wants a credential sets it explicitly, and still
# gets it -- check_source_credentials plants its own token and its own
# file:// base URL, and is unaffected.
# check_fixtures_own_the_credential_environment asserts this block did its
# job, planted variables and all.
CREDENTIAL_ENV_VARS = ('PRECEDENT_GIT_TOKEN', 'PRECEDENT_SOURCE_BASE_URL')
for _var in CREDENTIAL_ENV_VARS:
    os.environ.pop(_var, None)

# A THIRD INSTANCE, three days later, and it turned the whole branch red on
# any machine that has the also-list set. PRECEDENT_FRESHNESS_ALSO names
# OTHER repositories the freshness guard should check
# (.claude/hooks/freshness-guard.sh), and a fixture that runs the guard
# against its own temporary clone inherits it -- so the guard walked out of
# the fixture into this container's real attached practice sets, could not
# fetch one of them (no credential for a private remote), and blocked. The
# check reported "pre-write does not block a branch absent from origin
# (exit 2)" in both copies: a correct guard, a correct absent-branch
# NOTE printed just above it, and a block belonging to a repository the
# fixture had never heard of.
#
# Measured 2026-09-11, same tree, no code change: `2 failed` with the
# variable set, and exit 0 from the same guard call under `env -u
# PRECEDENT_FRESHNESS_ALSO`. A fixture exercising the guard owns which
# repositories it checks exactly as much as it owns the clone it built
# (practice: fixture-owns-its-state) -- and the only thing that can own an
# ambient list for every fixture, including the ones written next month, is
# this block.
os.environ.pop('PRECEDENT_FRESHNESS_ALSO', None)

# GIT'S OWN REPOSITORY VARIABLES (2026-10-06, traced from
# gotchas/gotcha-2026-10-01-a-harness-check-run-in-a-linked-worktree-turns-the-main-clone-bare.md).
# `git bisect run` exports GIT_DIR to the command it runs, and a git hook
# gets GIT_DIR and GIT_INDEX_FILE. Every fixture here builds its env from
# os.environ, so under either one a fixture's `git init`, `git add` and
# `git commit` all went to the repository the harness was started in, not
# the temporary one in front of them. Run from a linked worktree, GIT_DIR is
# `.git/worktrees/<name>`, and `git init --bare` re-initialised it as bare,
# which writes `core.bare = true` into the config the main clone shares.
# That is the 2026-10-01 bisect: fixture commits on the worktree's HEAD, and
# a main clone git called bare. Reproduced the same way on 2026-10-06 in a
# throwaway repository. Nothing in the harness locates a repository through
# these: ROOT is this file's own location, and every git call names its
# directory or runs in one. So they are dropped here, once, for every fixture
# (check_harness_drops_inherited_git_repository_variables).
GIT_REPOSITORY_ENV_VARS = (
    'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
    'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
    'GIT_NAMESPACE', 'GIT_PREFIX')
for _var in GIT_REPOSITORY_ENV_VARS:
    os.environ.pop(_var, None)

# GIT'S BACKGROUND MAINTENANCE (2026-10-18, issue #1207). A commit ends by
# starting `git maintenance run --auto` detached, and that run holds
# .git/objects/maintenance.lock for a moment. check_precedent_check_fires
# copies its pristine fixture with shutil.copytree right after committing
# into it, listed the lock, found it gone by the time it went to copy it, and
# turned GitHub's test on pull request #1206 red with nothing wrong in the
# tree. No fixture wants git tidying its throwaway repository behind its
# back, so every git this harness or its subprocesses start is told not to,
# appended to any GIT_CONFIG_COUNT entries already in the environment
# (check_harness_fixtures_run_no_background_maintenance).
HARNESS_GIT_CONFIG = (('maintenance.auto', 'false'), ('gc.auto', '0'))
_n = int(os.environ.get('GIT_CONFIG_COUNT') or 0)
for _key, _value in HARNESS_GIT_CONFIG:
    os.environ[f'GIT_CONFIG_KEY_{_n}'] = _key
    os.environ[f'GIT_CONFIG_VALUE_{_n}'] = _value
    _n += 1
os.environ['GIT_CONFIG_COUNT'] = str(_n)

# THE SAME, FOR THE GITHUB ACCOUNT (2026-09-30). The account a session's
# token belongs to now fills in the private sets' location and the commit
# identity when nothing declares them, and a cloud container's proxy answers
# api.github.com/user for ANY caller -- so a fixture meaning "nobody is known
# here" was answered with the real person's account and walked off to clone
# their real individual set. Every fixture starts with GitHub knowing nobody;
# one that tests the account rung points PRECEDENT_GITHUB_USER_URL at its own
# answer, as the commit-identity and base-URL checks do.
import tempfile as _tempfile_for_env  # noqa: E402
os.environ['PRECEDENT_GITHUB_USER_URL'] = (
    pathlib.Path(_tempfile_for_env.gettempdir()) / 'harness-github-knows-nobody.json').as_uri()

# AND WHAT A FAILED CLONE LEAVES BEHIND (2026-10-09). The source bootstrap
# keeps git's output for a clone that failed beside the user config, so the
# credentials check can quote it later. Fixtures fail clones on purpose, and
# without this every one of them would write a note into the real
# ~/.config/precedent that a real session would then quote.
os.environ['PRECEDENT_CLONE_NOTES'] = str(
    pathlib.Path(_tempfile_for_env.mkdtemp(prefix='harness-clone-notes-'))
    / 'clone-failures.json')

# NEVER /dev/null AS GIT'S GLOBAL CONFIG (2026-10-31, the second time;
# gotcha-2026-10-10-git-config-global-with-dev-null-replaces-dev-null).
# `git config --global` writes by renaming a lock file over its target, so
# with GIT_CONFIG_GLOBAL=/dev/null it replaces the container's null device
# with an ordinary file, and every later `2>/dev/null` and every fixture
# reading it fails. On 2026-10-31 a helper of the very deep check ran one
# test with GIT_CONFIG_GLOBAL=/dev/null set from outside; the test set its
# own HOME but kept the inherited variable, and its `git config --global`
# took the device. So: an inherited GIT_CONFIG_GLOBAL that is not a regular
# file is swapped here for an empty one, and every fixture asks
# empty_gitconfig() for a fresh empty file of its own -- never os.devnull,
# which check_no_fixture_points_git_config_at_dev_null refuses.
_EMPTY_GITCONFIG_DIR = pathlib.Path(_tempfile_for_env.mkdtemp(prefix='harness-gitconfig-'))
_empty_gitconfig_n = [0]


def empty_gitconfig():
    """-> the path of a new, empty file for GIT_CONFIG_GLOBAL: reads as no
    global config, as /dev/null does, and a write lands in this file alone."""
    _empty_gitconfig_n[0] += 1
    path = _EMPTY_GITCONFIG_DIR / f'gitconfig-{_empty_gitconfig_n[0]}'
    path.write_text('', encoding='utf-8')
    return str(path)


_inherited = os.environ.get('GIT_CONFIG_GLOBAL')
if _inherited and not os.path.isfile(_inherited):
    os.environ['GIT_CONFIG_GLOBAL'] = empty_gitconfig()

# NO FIXTURE STARTS A REAL BACKGROUND RUN OR CALLS GITHUB (2026-10-31).
# --land now starts the harness checks a landing reaches in the background,
# and opens and merges its pull request itself where a token is set; a
# fixture that lands must do neither. The test of each turns it back on
# against a stub (check_land_holds_while_its_reached_tests_are_red).
os.environ['PRECEDENT_LAND_REACH_RUN'] = '0'
os.environ['PRECEDENT_LAND_AUTO_PR'] = '0'

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
AGENTS_MD = ROOT / 'AGENTS.md'
CATALOGUE = ROOT / 'PRACTICES.md'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import precedent_paths as pp
import precedent_candidate as pcand
import doc_lint as dl
# build_views is imported for its pure helpers only (_json_str,
# INDEX_CLAUSE_MAX). check_generated_views_regenerate still shells out to it
# as a SUBPROCESS on purpose: build_loader_block() calls sys.exit() when the
# resident block is over budget, and an in-process call would turn that into
# an uncaught SystemExit taking the whole harness down instead of a FAIL
# line. Keep it that way -- import helpers, run the build out-of-process.
import build_views as bv
import catalogue_stats as cs

FAILED = []

# THE HARNESS RUNS ON THE LADDER BY DEFAULT (2026-10-02). Most of its cases
# test the tier machinery -- Promote, promote_only, a staging landing --
# through fixture people who bring no set, and since the ladder became a set
# a person brings (spec/LADDER_OPT_IN_PLAN.md) such a person is off it. This
# keeps those cases testing what they always tested. Every case about the
# off-ladder world clears it explicitly (check_ladder_opt_in_loader,
# check_attached_sets_*, check_ladder_off_*).
os.environ.setdefault('PRECEDENT_ASSUME_LADDER', '1')

# THE HARNESS IS A CONTAINER, NOT A LAPTOP (2026-10-17). commit-identity.sh
# leaves the global git identity, the global core.hooksPath and the system
# clock alone in a local session -- CLAUDE_PROJECT_DIR set and
# CLAUDE_CODE_REMOTE not "true", as a fixture running the hook looks on a
# CI runner. The cases about those writes test the container; the one about
# the laptop (check_commit_identity_leaves_a_laptops_global_config_alone)
# says so itself.
os.environ.setdefault('PRECEDENT_LOCAL_SESSION', '0')

# THE HARNESS SEEDS FROM THE COMMIT UNDER TEST (2026-10-02), which main
# does not contain on any working branch or pull request. seed() and the
# bootstrap refuse that unless told it is on purpose (--off-main); every
# fixture here is on purpose. check_seed_refuses_an_engine_main_lacks clears
# it to test the refusal itself.
os.environ.setdefault('PRECEDENT_SEED_OFF_MAIN', '1')
PASSED = []
NA = []

# practice: slow-steps-report-and-cache -- populated by _install_check_timing(),
# read by main() to print the slowest checks once the run finishes, so the
# next session can cite real durations instead of estimating them.
CHECK_DURATIONS = []

# --------------------------------------------------------------------------
# Post-conversion provenance exceptions -- both narrow and self-checking.
# --------------------------------------------------------------------------

# Practices that existed on Alex's live `main` but not in this repo's own
# PRACTICES.md at the time they were converted here (spec/PRACTICE_FORMAT.md).
# Converted independently against `main`, not against PRACTICES.md, so the
# fidelity checks below had no ancestor to compare against and had to not
# read that absence as invention. Frontmatter values come back as strings
# (see split_practices.py's own int(num) casts before comparison), so these
# are strings too.
#
# EMPTIED 2026-09-02: practice 53 (`todo-is-a-handoff`) stopped qualifying
# the moment a phase-5 pre-flight `git merge origin/main` brought main's own
# "## 53." entry into this branch's PRACTICES.md -- an ancestor now exists,
# so the fidelity checks run for real instead of skipping via this set, and
# correctly found the same unregistered citation-link edit the 2026-09-01
# sweep already exempted for the other 52 (see AMENDED_POST_CONVERSION and
# CHANGES_TO_TELL_ALEX.md's "Slug-link citation sweep" entry, updated to
# match). Left as an empty set, not deleted, because the mechanism is
# real and will be needed again the next time `main` outruns this branch.
POST_SNAPSHOT_PRACTICE_NUMBERS = set()

# Practices deliberately rewritten after phase-1 conversion -- a real edit,
# not a conversion bug -- keyed by slug.
AMENDED_POST_CONVERSION = {
    'layered-practice-packs',
    # Pre-phase-5 citation sweep, 2026-09-01 (see CHANGES_TO_TELL_ALEX.md):
    # every in-body "practice N" cross-reference converted to a [slug](slug.md)
    # link, since numbers stop meaning one fixed thing once practices can be
    # reordered, split, and retired. Listed here because a slug link is new
    # text relative to BestPractice's frozen original, so it fails the
    # word-multiset and sentence-preservation checks below on the citation
    # words alone -- the exemption covers a real, disclosed edit, not a
    # conversion bug.
    'acronyms-glossary', 'affordance-is-shared', 'build-buy-decompose',
    'capture-gate', 'check-source-architecture', 'computed-numbers-in-scripts',
    'convention-to-audit', 'deliverables-look-like-output', 'docs-track-models',
    'engine-plus-host-shims', 'environment-gotchas', 'frame-from-audience-question',
    'generated-artifact-provenance', 'index-remembers-past',
    'merge-runbook', 'mistakes-become-rules',
    'no-rewrite-for-warnings', 'one-formatter-per-quantity',
    'outward-summary-discipline', 'parallel-artifact-ledger',
    'permutation-frontier-column', 'practice-export-loop', 'readers-vocabulary',
    'registry-source-of-truth', 'repo-is-memory', 'scripts-assert-properties',
    'scrub-gate', 'search-by-purpose', 'second-pass-capture', 'session-bootstrap',
    'tabular-shared-renderer', 'two-check-levels', 'variant-re-derives',
    'verify-decomposition', 'verify-postcondition', 'volatile-rules-carry-dates',
    # Added 2026-09-02, when a phase-5 pre-flight merge of `main` gave
    # practice 53 a real ancestor in PRACTICES.md for the first time on this
    # branch (see the POST_SNAPSHOT_PRACTICE_NUMBERS comment above) and the
    # fidelity checks found the same category of edit the rest of this set
    # already covers: three "practice N" citations converted to slug links.
    'todo-is-a-handoff',
    # Added 2026-09-06 by the broken-relative-link sweep (see
    # CHANGES_TO_TELL_ALEX.md, "Relative-link sweep in practices/"): a
    # practice file lives one directory down, so a link written
    # `](tools/doc_lint.py)` resolved to `practices/tools/doc_lint.py` and
    # 404'd on GitHub for every reader of the practice file itself. 67
    # such links across 28 files were repointed to `](../...)`. Only the
    # link TARGET changed -- no prose, and the word-multiset checks above
    # still pass untouched -- but the sentence-identity check compares the
    # rendered target too, so the eight practices whose changed links sit
    # inside a checked section are declared here rather than exempted
    # silently.
    'doc-references-are-links', 'github-setup-disclosed',
    'lead-with-what-it-is', 'orientation-map', 'pr-template-honest-gates',
    'quick-index', 'reply-links-files', 'section-order-by-frequency',
    # Added 2026-09-07 by the Story backfill (see CHANGES_TO_TELL_ALEX.md,
    # "Story backfill across the catalogue"): 30 practices carried an empty
    # `## Story`, and one -- reply-links-files -- an empty `## Why` as well.
    # A Story is by definition text BestPractice's frozen original does not
    # contain, so writing one fails the word-multiset and sentence checks on
    # every word of it. The exemption covers a real, disclosed edit rather
    # than a conversion bug, exactly as the citation sweeps above do. Most of
    # the 30 were already listed here for earlier sweeps; these three were
    # not.
    'cite-the-incident', 'no-version-suffix',
    # Scrubbed the same day: a private repo's name replaced with a general
    # description, after the leak gate's private vocabulary half was run
    # against this tree for the first time.
    'migration-scrubs-vocabulary',
    # Added 2026-09-07 by the Why backfill (see CHANGES_TO_TELL_ALEX.md,
    # "Why backfill"). Distinct from the Story backfill the same day: these
    # nine already HAD their incident recorded in a real ## Story. What they
    # lacked was the reasoning, because their source practice never had a
    # paragraph opening with a **Why.** label for the converter's
    # carry-forward walk to route there. The new text is derived from each
    # practice's own Rule and Story, so it is invented relative to
    # PRACTICES.md and needs this exemption. Seven of the nine were already
    # listed above for earlier sweeps.
    'docs-are-current-state', 'label-describes-content',
    # Added 2026-09-08 when Alex's `main` check-in was carried onto this
    # branch (see CHANGES_TO_TELL_ALEX.md, "Alex's 2026-09-08 main
    # check-in"). Upstream appended a ratings corollary to the ledger
    # practice's own section in PRACTICES.md; here PRACTICES.md is frozen,
    # so the corollary was split across this file's Rule/Why/Story instead
    # and is invented relative to the frozen original. verify-decomposition
    # took the same check-in's dual-direction clause and is already listed
    # above for an earlier sweep.
    'name-both-sides-of-ledger',
}

CHANGES_DOC = ROOT / 'spec' / 'CHANGES_TO_TELL_ALEX.md'


def _amended_and_logged(slug):
    """True only if `slug` is BOTH in AMENDED_POST_CONVERSION AND actually
    named in CHANGES_TO_TELL_ALEX.md. The registry alone is not enough --
    tying the exemption to a checked property rather than a trusted list is
    the same discipline check_corruption_drop_is_a_duplicate already uses,
    so an amendment that forgets to log itself fails here instead of
    silently exempting itself from the fidelity checks below."""
    if slug not in AMENDED_POST_CONVERSION:
        return False
    if not CHANGES_DOC.exists():
        return False
    return slug in CHANGES_DOC.read_text(encoding='utf-8')


class FixtureSetupError(Exception):
    """A git command a fixture ran during SETUP failed.

    Raised by fixture_git() below and caught at the check boundary, where it
    is reported as an ordinary FAILED check naming the command. It is never
    allowed to escape: an exception out of a check kills the whole run before
    any verdict prints, which is the failure mode the filter crash of
    2026-09-21 already demonstrated once.

    WHY THIS EXISTS. Fixtures build a situation and then assert on it. When a
    setup command fails silently the situation is never built, the assertions
    run against something else, and the check reports the TOOL as broken --
    a false accusation, and a far more expensive thing to read than a plain
    failure. On 2026-09-21 a `git commit` in a fixture clone failed in CI for
    want of a git identity; nothing looked at the exit code; the resulting
    message said a source-clone tool was rebasing people's unpushed work. It
    was not. See practice: fixture-owns-its-state.
    """


# check() records this without counting it, for a verdict the wrapper below
# has already reported. Without it a caught FixtureSetupError lands twice --
# once from the wrapper, once from `check('<name>', *check_foo())` unpacking
# the triple the wrapper returned in the check's place.
_CHECK_ALREADY_REPORTED = object()


def fixture_git(d, *a, allow_failure=False):
    """Run a git command in a FIXTURE and refuse to fail quietly.

    The default is strict: a non-zero exit raises FixtureSetupError naming the
    command and git's own stderr. Pass allow_failure=True for the handful of
    places that are deliberately asserting a git command DOES fail.

    Returns the CompletedProcess, so every existing `_git(d, ...).stdout`
    call site keeps working unchanged.
    """
    r = subprocess.run(['git', '-C', str(d), *a], capture_output=True, text=True)
    if r.returncode != 0 and not allow_failure:
        detail = (r.stderr or r.stdout or '').strip().splitlines()
        raise FixtureSetupError(
            f"git {' '.join(a)} (in {d}) exited {r.returncode}"
            + (f': {detail[-1]}' if detail else ''))
    return r


# A filtered-out check's stand-in returns this instead of None. The
# verdict-returning family is wired up as `check('<name>', *check_foo())`,
# so a stand-in returning None makes every one of those 10 call sites die
# on `*None` the moment PRECEDENT_CHECK_ONLY/SKIP is set -- which is how
# CI runs verify_harness, and only how CI runs it, so a full local run
# passes 244/0 and the sharded job crashes before its first verdict.
# Reported 2026-09-21 against the two sharded deep-check jobs.
_CHECK_FILTERED_OUT = object()


def check(name, ok, detail='', failure=''):
    """Record one verdict.

    The fourth argument exists for the verdict-returning family, which ends
    in `return (not bad, detail, failure)` and is wired up as
    `check('<name>', *check_foo())`. Those carry TWO strings: a detail worth
    printing when the check passes ("11 stated cases"), and the failure text
    naming what broke. Collapsing them at the call site would have meant
    every one of those sites choosing, and choosing differently; taking both
    here keeps the family's own return shape intact.

    A failing check prints its failure text when it has one, because that is
    the string that says what to go and look at."""
    if ok is _CHECK_ALREADY_REPORTED:
        return
    if ok is _CHECK_FILTERED_OUT:
        not_applicable(name, 'filtered out by PRECEDENT_CHECK_ONLY/SKIP')
        return
    shown = failure if (not ok and failure) else detail
    (PASSED if ok else FAILED).append((name, shown))
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" -- {shown}" if shown and not ok else ""))

# A LINE THAT NAMES A FAILURE. Upper-case words only: "0 failed" and
# "error" turn up in ordinary output, and a line picked for them would push
# the tail out for nothing.
_FAILURE_NAMING_RE = re.compile(
    r'\b(?:VIOLATION|VIOLATED|FAIL|FAILED|ERROR|ERRORED|REFUSED)\b'
    r'|^Traceback \(most recent call last\)|^\w+(?:Error|Exception):')
_FAILURE_DETAIL_GAP = '\n...\n'


def failure_detail(text, limit=600):
    """-> what a failing case reports from a tool's output `text`, in at
    most `limit` characters: the lines that name the failure (VIOLATION,
    FAIL, ERROR, REFUSED, a traceback), deduplicated and capped at half the
    limit, then as much of the tail as fits. A line the tail already shows
    is not repeated, and output with no such line comes back as exactly
    `text[-limit:]`, as does anything that is not a string.

    WHY (Morgan, 2026-10-31, strength: decided: "that should be a more
    general rule"). check_precedent_check_degrades_in_a_source_set reported
    a failure as `out[-600:]`, and the VIOLATION line naming the check that
    fired sat earlier, so the report never said which check it was. About
    500 tests here reported a failure the same way. The push check refuses
    a new raw tail in a check( or cases.append( detail (practice:
    control-asserts-which-failure)."""
    if not isinstance(text, str) or len(text) <= limit:
        return text[-limit:]
    tail = text[-limit:]
    named = []
    for line in text.splitlines():
        s = line.strip()
        if s and _FAILURE_NAMING_RE.search(s) and s not in named \
                and s not in tail:
            named.append(s)
    cap = limit // 2
    head = ''
    for s in named:
        grown = f'{head}\n{s}' if head else s
        if len(grown) > cap:
            head = head or s[:cap]
            break
        head = grown
    if not head:
        return tail
    room = limit - len(head) - len(_FAILURE_DETAIL_GAP)
    return head + _FAILURE_DETAIL_GAP + (text[-room:] if room > 0 else '')


# The check_* function running now, innermost last -- pushed and popped by
# _install_fixture_error_guard's wrapper. not_applicable() reads it, so a
# run can name the FUNCTIONS that went not-applicable and a second run can
# select exactly those (PRECEDENT_CHECK_ONLY takes function names, and a
# verdict's own name is prose). run_as_ci_isolated() is the caller.
_CURRENT_CHECK = []
NA_FUNCTIONS = set()


def not_applicable(name, reason):
    NA.append((name, reason))
    if _CURRENT_CHECK:
        NA_FUNCTIONS.add(_CURRENT_CHECK[-1])
    print(f"N/A:  {name} -- {reason}")


def _ref_including_worktree(repo):
    """A commit-ish naming `repo`'s state right now -- HEAD plus every
    uncommitted change, tracked or not -- built without touching `repo`'s
    real HEAD, index, or working tree. Every fixture below that vendors
    "from ROOT" through precedent_vendor_engine's `--from-ref` needs this
    in place of the literal string `'HEAD'`.

    WHY NOT JUST `'HEAD'`. `refresh()` reads source as git blobs rather
    than a checkout specifically so a vendoring read can never move the
    caller's own checkout (`_source_tools_at`'s own docstring in
    precedent_vendor_engine.py tells that incident). But blobs read at
    literal HEAD miss anything not yet committed -- most acutely a
    brand-new file not yet `git add`ed -- which is exactly the case
    `run_refresh`'s own comment below names as the reason `--from-ref`
    exists at all: "a mechanism landing in the SAME change as this test".
    Reproduced 2026-09-20: the deep check false-failed twice against an
    uncommitted tree before the cause was traced to this literal `'HEAD'`.

    WHY NOT `git stash create`. It was tried first and rejected for
    exactly the gap this closes: `stash create` has no untracked-file
    option at all (only `git stash push -u` does), so a new, not-yet-added
    file is invisible to it -- the same blind spot as literal `'HEAD'`,
    just for a narrower set of edits.

    THE MECHANISM: a scratch index. Read HEAD's tree into a throwaway
    index file (`GIT_INDEX_FILE`, never `repo`'s real `.git/index`),
    `add -A` the working tree onto it -- untracked files included,
    `.gitignore`d ones excluded, same as any other `add -A` -- write that
    as a tree object, and wrap it in a commit whose only parent is HEAD.
    Nothing here touches the real index, HEAD, or a single file on disk;
    the throwaway index file lives in its own temp directory and is
    discarded once this returns. Returns HEAD itself, untouched, when the
    tree is already clean -- no synthetic commit needed."""
    import tempfile

    def _git(*args, env=None):
        return subprocess.run(['git', '-C', str(repo), *args],
                              capture_output=True, text=True, env=env)

    head = _git('rev-parse', 'HEAD')
    if head.returncode != 0:
        sys.exit(f"verify_harness FAIL: {repo} has no HEAD to snapshot.")
    head_sha = head.stdout.strip()

    with tempfile.TemporaryDirectory(prefix='precedent-scratch-index-') as idx_dir:
        env = dict(os.environ, GIT_INDEX_FILE=str(pathlib.Path(idx_dir) / 'index'))
        r = _git('read-tree', head_sha, env=env)
        if r.returncode != 0:
            sys.exit(f"verify_harness FAIL: could not seed a scratch index "
                     f"for {repo} from {head_sha[:12]}: {r.stderr}")
        r = _git('add', '-A', env=env)
        if r.returncode != 0:
            sys.exit(f"verify_harness FAIL: could not stage {repo}'s working "
                     f"tree onto a scratch index: {r.stderr}")
        tree = _git('write-tree', env=env)
        if tree.returncode != 0:
            sys.exit(f"verify_harness FAIL: could not write a scratch tree "
                     f"for {repo}'s current state: {tree.stderr}")
        tree_sha = tree.stdout.strip()

        head_tree = _git('rev-parse', f'{head_sha}^{{tree}}').stdout.strip()
        if tree_sha == head_tree:
            return head_sha  # clean tree -- nothing uncommitted to capture

        # Its own identity: the commit is never pushed or checked out, and a
        # bare runner (the isolated --as-ci run, GitHub's) has none to give
        # it. Found 2026-09-30: shards share one checkout, a file one shard
        # wrote for a moment made another's tree read as dirty, and
        # commit-tree failed with "Author identity unknown" -- a full check
        # that failed without naming a test.
        env.update(GIT_AUTHOR_NAME='verify_harness', GIT_AUTHOR_EMAIL='harness@localhost',
                   GIT_COMMITTER_NAME='verify_harness',
                   GIT_COMMITTER_EMAIL='harness@localhost')
        commit = _git('commit-tree', tree_sha, '-p', head_sha, '-m',
                      'verify_harness: scratch snapshot of the working tree '
                      '(never pushed, never checked out)', env=env)
        if commit.returncode != 0:
            sys.exit(f"verify_harness FAIL: could not create a scratch "
                     f"commit for {repo}'s current state: {commit.stderr}")
        return commit.stdout.strip()


def _rmtree_retrying(path, attempts=5, delay=0.2):
    """Delete a directory tree, retrying a transient ENOTEMPTY instead of
    either crashing the whole run over it or silently swallowing it
    (practice: upstream-fix -- retrying is instrumentation, not suppression:
    a real, persistent leak still fails, now with evidence).

    THE INCIDENT, 2026-09-19: check_leak_gate_refuses_a_fresh_container's own
    `tempfile.TemporaryDirectory()` cleanup crashed this entire run on
    GitHub's hosted runner with `OSError: [Errno 39] Directory not empty`,
    tearing down a throwaway git repo the check builds and deletes.
    Everything the check does to that directory is a synchronous
    `subprocess.run` -- nothing in the check itself keeps a handle open --
    and the identical check passed clean on the identical commit both
    locally and on a same-runner re-run minutes later, so this reads as a
    transient filesystem race on the runner rather than a real leak (a
    plausible but UNMEASURED mechanism: modern git can auto-start a
    background filesystem-monitor daemon per repo that outlives the `git`
    command that spawned it). A short retry gives whatever is transiently
    holding the directory open a moment to let go; if it is still not empty
    after `attempts`, this raises anyway -- loudly, with what is actually
    left in the directory attached, rather than passing silently the way
    `ignore_cleanup_errors=True` would (practice: cite-the-incident).
    """
    last_err = None
    for _ in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError as e:
            last_err = e
            time.sleep(delay)
    remaining = []
    try:
        remaining = sorted(str(p) for p in pathlib.Path(path).rglob('*'))
    except OSError:
        pass
    shown = remaining[:20]
    more = f" (+{len(remaining) - 20} more)" if len(remaining) > 20 else ""
    raise OSError(f"{last_err} -- still not empty after {attempts} retries; "
                  f"contents: {shown}{more}")




# practice: slow-steps-report-and-cache -- this run has 270+ check_* calls
# and, before this, printed nothing between the first PASS/FAIL line and the
# last: a wait with no number on it, indistinguishable from a hang. Wrapping
# every check_* function (rather than hand-editing every call site in
# main()) is the low-risk way in: it needs no changes to main()'s ~270 call
# lines, so it cannot silently drop or reorder a check.
#
# PRECEDENT_NO_CHECK_TIMING=1 skips this -- set it when profiling under
# cProfile, so the wrapper's own frames don't show up in the profile.
_PROGRESS_INTERVAL_SECONDS = 5


def _install_check_filter():
    """PRECEDENT_CHECK_ONLY / PRECEDENT_CHECK_SKIP -- comma-separated
    check_* names -- let a run cover a named subset instead of all ~172.
    Built for splitting the handful of genuinely heavy checks into their
    own CI job (see spec/VERIFY_HARNESS_PERFORMANCE.md), and doubles as a
    way to re-measure the checks after a heavy one without re-paying for
    the heavy one itself. A filtered-out check is replaced with a no-op
    before it can run, so its subprocess fan-out never happens -- this is
    not a report filter, the check's own cost is what's being skipped.
    """
    only = os.environ.get('PRECEDENT_CHECK_ONLY')
    skip = os.environ.get('PRECEDENT_CHECK_SKIP')
    # PRECEDENT_CHECK_SELECT: the checks a change reaches
    # (tools/harness_reach.py), set by a scoped --as-ci run. Anything else
    # is not run, and says why.
    select = os.environ.get('PRECEDENT_CHECK_SELECT')
    if not only and not skip and select is None:
        return
    only_set = set(only.split(',')) if only else None
    skip_set = set(skip.split(',')) if skip else set()
    select_set = set(select.split(',')) - {''} if select is not None else None
    names = sorted(n for n, v in list(globals().items())
                    if n.startswith('check_') and callable(v))
    for name in names:
        if (only_set is not None and name not in only_set) or name in skip_set:
            def _skipped(*a, _name=name, **kw):
                print(f"  SKIP (filtered out by PRECEDENT_CHECK_ONLY/SKIP): {_name}",
                      file=sys.stderr)
                return (_CHECK_FILTERED_OUT, '', '')
            globals()[name] = _skipped
        elif select_set is not None and name not in select_set:
            def _unreached(*a, _name=name, **kw):
                print(f"  SKIP (not reached by this change): {_name}",
                      file=sys.stderr)
                return (_CHECK_FILTERED_OUT, '', '')
            globals()[name] = _unreached


def _install_reach_recording():
    """HARNESS_REACH_RECORD set (tools/harness_reach.py record): keep what
    each check that runs here reaches -- the ledger a change-scoped run
    selects from. A check the filter replaced records nothing."""
    out = os.environ.get('HARNESS_REACH_RECORD')
    if not out:
        return
    spec = importlib.util.spec_from_file_location(
        '_harness_reach_hook', ROOT / 'tools' / 'harness_reach_hook.py')
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    hook.start_parent(str(ROOT), out)
    names = sorted(n for n, v in list(globals().items())
                   if n.startswith('check_') and callable(v))

    def _wrap(name, fn):
        def wrapper(*args, **kwargs):
            hook.begin(name)
            ran = True
            try:
                out = fn(*args, **kwargs)
                ran = not (isinstance(out, tuple) and out and out[0] is _CHECK_FILTERED_OUT)
                return out
            finally:
                hook.end(name, ran)
        return wrapper

    for name in names:
        globals()[name] = _wrap(name, globals()[name])


def _install_retrying_tempdir_cleanup():
    """Every `tempfile.TemporaryDirectory()` in this harness deletes through
    _rmtree_retrying(), not one check at a time.

    gotcha-2026-09-19-verify-harnesss-fresh-container-check-can-fail-tempdir
    converted the one check that had crashed the run with `Directory not
    empty` on GitHub's runner, and said a recurrence on a different check
    would argue for sharing the retry. It recurred, 2026-10-05:
    check_session_check_adopts_a_detached_start's cleanup of its scratch
    repository's .git crashed the "everything else" job of a Produce's GitHub
    test, on a check that passed locally on the same tree. A directory
    still not empty after the retries still raises, with what is left in it
    -- loud, with evidence, never ignore_cleanup_errors' silence -- and a
    TemporaryDirectory asked to ignore errors keeps doing so."""
    import tempfile as _tempfile
    original = _tempfile.TemporaryDirectory._rmtree.__func__

    def _rmtree(cls, name, ignore_errors=False, repeated=False):
        if ignore_errors:
            return original(cls, name, ignore_errors=ignore_errors, repeated=repeated)
        _rmtree_retrying(name)
    _tempfile.TemporaryDirectory._rmtree = classmethod(_rmtree)


def _drop_foreign_engine_modules(path_before):
    """After a check: forget any engine module it left loaded from outside
    this repository's tools/, and any import path it added outside this
    repository, so the next check imports this tree's engine.

    WHY (2026-10-31). A landing's background run went red on
    check_repo_reference_allowlist: "module 'leak_gate' has no attribute
    '_ref_key'". The leak_gate that process held was a practice set's older
    vendored copy: an earlier check had run that set's ladder tools in this
    process, and they put the set's tools/ first on sys.path while
    importing. The set no longer does that (precedent-shared-ladder #167);
    this keeps any other copy, an adopter's older one included, from
    reaching the next check. -> the names dropped."""
    tools = (ROOT / 'tools').resolve()
    names = {f.stem for f in tools.glob('*.py')}
    dropped = []
    for n in list(sys.modules):
        if n not in names:
            continue
        f = getattr(sys.modules.get(n), '__file__', None)
        try:
            foreign = bool(f) and pathlib.Path(f).resolve().parent != tools
        except (OSError, ValueError):
            foreign = False
        if foreign:
            del sys.modules[n]
            dropped.append(n)
    before, root = set(path_before), ROOT.resolve()

    def _ours(entry):
        if entry in before or not entry:
            return True
        try:
            pathlib.Path(entry).resolve().relative_to(root)
            return True
        except (ValueError, OSError):
            return False
    sys.path[:] = [e for e in sys.path if _ours(e)]
    return dropped


def _install_fixture_error_guard():
    """Turn a FixtureSetupError into a FAILED check instead of a dead run.

    Installed unconditionally -- unlike the timing wrapper, which
    PRECEDENT_NO_CHECK_TIMING can switch off for profiling. A crash that only
    appears when profiling is off is exactly the kind of environment-shaped
    difference this whole guard exists to stop.
    """
    names = sorted(n for n, v in list(globals().items())
                   if n.startswith('check_') and callable(v))

    def _wrap(name, fn):
        def wrapper(*args, **kwargs):
            _CURRENT_CHECK.append(name)
            path_before = list(sys.path)
            try:
                return fn(*args, **kwargs)
            except FixtureSetupError as exc:
                check(name, False, '', f'fixture setup failed -- {exc}')
                # Reported already; the triple keeps the `check('<name>',
                # *check_foo())` call sites from recording it a second time.
                return (_CHECK_ALREADY_REPORTED, '', '')
            finally:
                _CURRENT_CHECK.pop()
                _drop_foreign_engine_modules(path_before)
        return wrapper

    for name in names:
        globals()[name] = _wrap(name, globals()[name])


def _install_check_timing():
    if os.environ.get('PRECEDENT_NO_CHECK_TIMING'):
        return
    names = sorted(n for n, v in list(globals().items())
                    if n.startswith('check_') and callable(v))
    total = len(names)
    state = {'done': 0, 'elapsed': 0.0, 'last_report': time.monotonic()}
    run_start = time.monotonic()

    def _wrap(name, fn):
        def wrapper(*args, **kwargs):
            t0 = time.monotonic()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = time.monotonic() - t0
                state['done'] += 1
                state['elapsed'] += dt
                CHECK_DURATIONS.append((name, dt))
                if dt >= 2.0:
                    print(f"  ...{name} took {dt:.1f}s", file=sys.stderr)
                now = time.monotonic()
                if now - state['last_report'] >= _PROGRESS_INTERVAL_SECONDS:
                    state['last_report'] = now
                    avg = state['elapsed'] / state['done']
                    remaining = avg * (total - state['done'])
                    print(f"  -- {state['done']}/{total} checks done, "
                          f"{now - run_start:.0f}s elapsed, "
                          f"~{remaining:.0f}s remaining", file=sys.stderr)
        return wrapper

    for name in names:
        globals()[name] = _wrap(name, globals()[name])


def _report_check_durations(top_n=15):
    if not CHECK_DURATIONS:
        return
    total = sum(dt for _, dt in CHECK_DURATIONS)
    slowest = sorted(CHECK_DURATIONS, key=lambda p: p[1], reverse=True)[:top_n]
    print(f"\n{len(CHECK_DURATIONS)} checks ran in {total:.1f}s total "
          f"(this run -- durations vary with what the tree currently holds). "
          f"Slowest {len(slowest)}:", file=sys.stderr)
    for name, dt in slowest:
        print(f"  {dt:6.2f}s  {name}", file=sys.stderr)


def load_practice_files():
    out = {}
    broken = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            broken.append(str(e))
            continue
        out[f.stem] = (fm, sections, f)
    if broken:
        # A malformed practice file used to abort the whole harness with a
        # bare AssertionError traceback that did not name the file. Report
        # it as a failed check, like everything else here, and keep going so
        # the rest of the run still tells you what else is wrong.
        for msg in broken:
            print(f"  {msg}")
        check('every practices/*.md file parses', False,
              f"{len(broken)} unparseable practice file(s)")
    else:
        check('every practices/*.md file parses', True)
    return out


def _without_session_id(fn):
    """Run a check with no CLAUDE_CODE_REMOTE_SESSION_ID in the environment.
    precedent_gate._unlanded_work reports only commits carrying this
    session's trailer when that id is set, so a fixture whose commits carry
    none must not inherit the id of the session running the harness
    (practice: fixture-owns-its-state)."""
    import functools

    @functools.wraps(fn)
    def run(*a, **k):
        saved = os.environ.pop('CLAUDE_CODE_REMOTE_SESSION_ID', None)
        try:
            return fn(*a, **k)
        finally:
            if saved is not None:
                os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = saved
    return run




# ---------------------------------------------------------------------------
# RETIRED: byte-identical regeneration.
#
# Phase 1's converter was mechanical -- it routed each paragraph by the bold
# label that opened it -- so the catalogue could be rebuilt from practices/
# and diffed against PRACTICES.md byte for byte. That was the right proof for
# a mechanical conversion, and it held: 52 practices, no unexplained
# difference, modulo three documented source quirks.
#
# It cannot survive the phase-1.5 editorial re-split, and not because the
# re-split is unfaithful. Re-homing a paragraph from Rule to Why moves where
# cmd_build re-emits the "**Why.**" label, so the rebuilt catalogue differs
# from the source however faithful the move was. A check that fails on
# correct work is worse than no check: it gets suppressed, and then it is not
# there when something is actually wrong.
#
# Its two claims are both still checked, by name, and one of them more
# strongly than before:
#
#   CONTENT  -> check_content_preserved_by_sentence. Byte-identical compared
#               a reassembly; this compares every sentence of every practice
#               against PRACTICES.md directly, in both directions. It is
#               strictly stronger: a single word reworded inside a Rule
#               passes both word-multiset checks (the reworded word can
#               lowercase to the same token) and fails this one.
#   ORDERING -> check_section_source_order. Text may be re-homed between
#               sections; within a section it must still appear in its
#               original source order.
#
# Plus check_no_lost_content, check_list_structure_preserved and
# check_corruption_drop_is_a_duplicate, none of which existed when
# byte-identical was the whole story.
#
# tools/split_practices.py build still renders a catalogue view and
# `build --diff` still runs -- but its diff is now expected output showing
# the editorial re-split, not a defect report.

# ---------------------------------------------------------------------------
# Content preservation across an EDITORIAL re-split.
#
# Phase 1's converter was mechanical, so "byte-identical regeneration" could
# prove it lost nothing: rebuild PRACTICES.md from practices/ and diff. That
# check cannot survive the phase-1.5 editorial pass, by construction -- the
# whole point of that pass is that text MOVES between sections, so the
# rebuilt catalogue's **Why.** label lands somewhere else and the diff is
# non-empty no matter how faithful the move was.
#
# It is replaced by something stronger on the dimension that actually
# matters, and weaker only on one that does not. The plan's own rule for the
# converter is a SENTENCE rule -- "no sentence may appear in the output that
# does not appear in the input" (Migration, The Converter) -- so that is what
# is checked, in both directions, against PRACTICES.md itself. PRACTICES.md
# is the immutable upstream source and stays in the repo, so this is a
# permanent, non-circular guarantee that survives any future re-split:
# whatever the sections end up being, their combined content is exactly
# BestPractice's content, sentence for sentence.
#
# What is lost is the ORDERING claim byte-identical regeneration also made,
# and check_section_source_order restores it: within each section, sentences
# must still appear in their original relative source order. Any pure
# re-homing preserves that; scrambling does not.
_PARA_SPLIT = re.compile(r'\n\s*\n')
_SENT_SPLIT = re.compile(r'(?<=[.!?])[ \t]+(?=[A-Z0-9*\[(“"`—-])')


def _sentences(text):
    """Sentence-ish chunks, whitespace-normalized. Deliberately the SAME
    tokenizer on both sides of every comparison, so an imperfect split (a
    trailing "e.g." swallowing the next sentence, say) is symmetric and
    harmless: it just makes the compared chunk bigger. The only way it
    misfires is if an edit splits text *inside* a chunk the tokenizer
    merged -- which fails the check rather than passing it, i.e. it fails
    closed, which is the direction to be wrong in."""
    out = []
    for para in _PARA_SPLIT.split(text or ''):
        para = ' '.join(para.split())
        if not para:
            continue
        out.extend(s for s in (x.strip() for x in _SENT_SPLIT.split(para)) if s)
    return out


def _source_sentences(orig):
    return _sentences(orig['rule']) + _sentences(orig['why']) + _sentences(orig['install'])


SECTION_ORDER = ('rule', 'detail', 'why', 'story', 'install')


def _output_sentences_by_section(sections):
    return [(name, _sentences(sections.get(name, ''))) for name in SECTION_ORDER]




_LIST_ITEM_RE = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.*)$')




SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")




CITATION_RE = re.compile(r'\bpractice\s+(\d+)\b', re.IGNORECASE)




# How many consecutive identical non-blank lines, shared between two
# different practices, count as duplication rather than coincidence. Three
# is comfortably clear of any real overlap in this catalogue: across all 52
# practices the ONLY pair that trips it is the one real corruption, and the
# runner-up shares nothing at all. Practices legitimately quote each other's
# names and cite each other by number; they do not share paragraphs.
DUPLICATE_RUN_LINES = 3


def _seed_consumer_engine(dest_tools, extra=(), only=None):
    """Copy the engine a CONSUMING repo actually receives into dest_tools.

    THE ONE PLACE THAT LIST LIVES, and why it had to become one.
    Fixtures here hand-listed the engine files they needed --
    `('precedent_resolve.py', 'split_practices.py', 'build_views.py', ...)`
    -- which is correct until an engine module is added, and then silently
    wrong: the fixture keeps copying a precedent_resolve.py that imports a
    companion the fixture has never heard of. On 2026-09-10 a new module
    (precedent_identity.py, carved out of the resolver) broke TWO fixtures
    that way in a single change, and one of them carried a comment warning
    about precisely this failure -- the warning did not help, because the
    list it guarded was still a hand-list.

    Reading precedent_vendor_engine's own CONSUMER_ENGINE_FILES is what
    makes a fixture a consumer rather than a curated subset of one
    (practice: fixture-owns-its-state -- the state a fixture owns includes
    which files a real consumer gets).

    `extra` adds non-engine companions a fixture needs (data files, the
    leak gate). `only` narrows to a subset by name for a fixture that is
    deliberately testing a partial engine -- pass it explicitly, so a
    narrow copy is a stated choice rather than an accident of drift."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    names = list(_pve.CONSUMER_ENGINE_FILES) + list(extra)
    if only is not None:
        names = [n for n in names if n in set(only) | set(extra)]
    dest_tools = pathlib.Path(dest_tools)
    dest_tools.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in names:
        src = ROOT / 'tools' / name
        if src.is_file():
            shutil.copy2(src, dest_tools / name)
            copied.append(name)
    return copied


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


EXAMPLE_SET = ROOT / 'documentation' / 'examples' / 'practice-set'




# Widened from the original `^\*\*(\d{4}-\d{2}-\d{2}) — ` (bold date, then
# exactly an em dash with a space each side, nothing else) after a
# 2026-09-01 audit constructed plausible near-future variants -- a colon
# instead of the em-dash, an en-dash, a double-hyphen, an unbolded date, a
# leading list marker or checkbox -- and found every one silently invisible
# to `entries()` below: a non-matching entry is not merely miscounted, it
# is DROPPED from the text entirely if it sits above the first recognized
# match, which is exactly where a new entry lands under this section's own
# newest-first convention. This still cannot recognize a violation with NO
# date-like structure at all (unfixable by any regex); it substantially
# narrows the gap for the plausible near-term reformattings a human or an
# agent might actually type.
AMENDMENT_ENTRY_RE = re.compile(
    r'^\s*(?:[-*]\s+)?(?:\[[ xX]\]\s+)?\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}'
    r'\s*(?:[:—–]|--)\s*', re.M)
# A bare substring test ('decisions/' anywhere in the entry) exempted any
# entry that merely MENTIONED the word, including "not yet migrated to
# decisions/, still keeping every word inline" -- prose about NOT having a
# record, exempted as if it were one. Requires an actual file reference.
DECISIONS_LINK_RE = re.compile(r'decisions/[\w.-]+\.md')
DECISION_LENGTH_WORDS = 120
PLAN_MD = ROOT / 'spec' / 'PRACTICE_ENGINE_PLAN.md'




# (path, glob, expected) -- the semantics `applies_to` is written against.
# This table exists because the path-triggered channel shipped with a bare
# fnmatch.fnmatch(path, glob), under which "**/*.md" silently never matched
# a top-level file, and NOTHING in the harness noticed: the behavioral
# replay's "independent" cross-check re-derived matches with the same
# fnmatch call, so it agreed with the bug on every commit and reported 0
# misses. A cross-check against a second copy of the same rule is not a
# check. Stating the intended semantics as literal cases is.
GLOB_CASES = [
    # a root-level file is at depth zero -- "**/" must match zero segments
    ('AGENTS.md',                          '**/*.md',                          True),
    ('README.md',                          '**/*.md',                          True),
    ('docs/guide.md',                      '**/*.md',                          True),
    ('a/b/c/deep.md',                      '**/*.md',                          True),
    ('notes.txt',                          '**/*.md',                          False),
    ('docs/notes.txt',                     '**/*.md',                          False),
    # the same file, spelled three ways, must give one answer
    ('./AGENTS.md',                        '**/*.md',                          True),
    (str(ROOT / 'AGENTS.md'),              '**/*.md',                          True),
    # a single * does not cross a directory separator
    ('docs/guide.md',                      '*.md',                             False),
    ('guide.md',                           '*.md',                             True),
    ('a/b.md',                             'a/*.md',                           True),
    ('a/b/c.md',                           'a/*.md',                           False),
    ('a/b/c.md',                           'a/**/*.md',                        True),
    ('a/c.md',                             'a/**/*.md',                        True),
    # "dir/**" is everything INSIDE dir, not dir itself
    ('process/upstream/tools/x.py',        'process/upstream/**',              True),
    ('process/upstream/x.py',              'process/upstream/**',              True),
    ('process/upstream',                   'process/upstream/**',              False),
    ('process/upstreamish/x.py',           'process/upstream/**',              False),
    # a literal path is a literal path
    ('.github/pull_request_template.md',   '.github/pull_request_template.md', True),
    ('docs/.github/pull_request_template.md',
                                           '.github/pull_request_template.md', False),
    ('README.md',                          'README.md',                        True),
    ('docs/README.md',                     'README.md',                        False),
    # "**" alone matches anything (filtered out of the path channel, but the
    # matcher still has to be right about it)
    ('anything/at/all.py',                 '**',                               True),
    ('top.py',                             '**',                               True),
]




# THE VERY DEEP CHECK'S GUARDS (Morgan, 2026-10-31, strength: decided: "why
# didnt this run do it? How do we make sure future runs do it?", then
# "Update the very deep instructions so to fix this in the future"). The
# 2026-10-30 run recorded every pass `partial` with nothing saying what was
# skipped or who agreed, never re-ran its suite green, left question 27
# "Not judged this run", lost 62 incident verdicts with a scratch file and
# copied the quiet-sections answer from the run before. Each test below
# plants one of those shapes in a run dated 2026-11-01 and asserts the
# tool's own refusal; its control is the same shape the guard lets through.
_VDC_G_START = '2026-11-01T09:00:00-03:00'


def _vdc_guard_repo(tmp, green=None, passes=(), date='2026-11-01',
                    harness=True, consumer=False, run_extra=None):
    """-> (repo, ledger): a repository with one completed run in its ledger,
    a harness of its own when `harness`, and `green` as its last green
    whole-suite run (practice: fixture-owns-its-state)."""
    repo = pathlib.Path(tmp) / 'repo'
    (repo / 'tools').mkdir(parents=True, exist_ok=True)
    (repo / 'record').mkdir(exist_ok=True)
    if harness:
        (repo / 'tools' / 'verify_harness.py').write_text('', encoding='utf-8')
        rec = {'measured': '2026-11-01, 4 cores, --as-ci', 'seconds': {}}
        if green:
            rec['green_full_run'] = green
        (repo / 'tools' / 'harness_check_times.json').write_text(
            json.dumps(rec), encoding='utf-8')
    if consumer:
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}', encoding='utf-8')
    run = {'run_id': _VDC_G_START, 'date': date, 'completed': True,
           'components': [], 'passes': list(passes)}
    run.update(run_extra or {})
    ledger = repo / 'record' / 'very-deep-check-ledger.json'
    ledger.write_text(json.dumps({'runs': [run]}), encoding='utf-8')
    return repo, ledger


def _vdc_record(vdc, arg, ledger, repo):
    """-> (exit, stderr, the run after it) for one --record-pass."""
    import contextlib, io
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        rc = vdc._record_pass(arg, ledger, repo)
    run = json.loads(ledger.read_text(encoding='utf-8'))['runs'][-1]
    return rc, err.getvalue(), run




_VDC_G_ACCOUNT = """---
opened: 2026-11-01
---
# Run

## Pass 2

| Question | Answer |
|---|---|
| 1 | answered |
| 2 | partly: half of it |
| 2a | not attempted |

## Incidents

- `gotcha-fx-one`: a check with a planted case, check_fx.
- `todo-fx-two`: nothing mechanical, deliberately, because it is judgment.

## Quiet sections, answered

2026-11-01: QUIET ONE kept, a cheap guard. CANNOT COUNT kept: it needs GitHub.

## Checks by stage

x

## Test review

<!--vdc-embed:test-review: never hand-edit -->
### this checkout

3 test(s), 3 timed, 4 s recorded in all. Judged: 3. Never judged: 0. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 0. Times measured 2026-11-01, 4 cores, --as-ci.

### a set

2 test(s), 0 timed, 0 s recorded in all. Judged: 2. Never judged: 0. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 0.
<!--/vdc-embed:test-review-->

## Long Rules

x
"""


def _vdc_account_fixture(tmp, date='2026-11-01'):
    """-> repo: a run whose account shows all the work, for the account
    check to be planted against (practice: fixture-owns-its-state)."""
    repo = pathlib.Path(tmp) / 'repo'
    for d in ('record', 'spec', 'tools', 'practices'):
        (repo / d).mkdir(parents=True, exist_ok=True)
    comp = lambda n, st='clean', f=0: {'name': n, 'kind': 'mechanical',
                                       'findings': f, 'status': st,
                                       'output_tokens': 10}
    earlier = [{'run_id': f'2026-10-{d}', 'date': f'2026-10-{d}',
                'components': [comp('QUIET ONE -- a guard')], 'passes': []}
               for d in ('10', '20')]
    run = {'run_id': '2026-11-01T09:00:00-03:00', 'date': date,
           'components': [comp('QUIET ONE -- a guard'),
                          comp('CANNOT COUNT', 'unknown', None),
                          dict(comp('INCIDENT COVERAGE'), kind='read',
                               listed=['gotcha-fx-one', 'todo-fx-two']),
                          dict(comp('TEST WORTH', 'findings', 3),
                               to_judge={'this checkout': 3})],
           'passes': [{'pass': str(n), 'status': 'done',
                       'recorded': '2026-11-01T13:00:00-03:00'}
                      for n in (1, 2, 3, 4)]}
    (repo / 'record' / 'very-deep-check-ledger.json').write_text(
        json.dumps({'runs': earlier + [run]}), encoding='utf-8')
    (repo / 'record' / 'automated_actions.md').write_text(
        '# Schedules\n\nConfirmed unchanged on 2026-11-01.\n', encoding='utf-8')
    (repo / 'tools' / 'test_verdicts.json').write_text(json.dumps(
        {'verdicts': {'check_a': {'verdict': 'keep', 'importance': 'low',
                                  'why': 'w', 'date': '2026-11-01'}}}),
        encoding='utf-8')
    (repo / 'practices' / 'very-deep-check.md').write_text(
        '## Detail\n\n### Pass 2 — mechanisms\n1. **One?** x\n\n'
        '2. **Two?** y\n2a. **Two, again?** z\n\n### Pass 3 — writing\n'
        '9. **Not pass 2.** w\n', encoding='utf-8')
    (repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md').write_text(
        _VDC_G_ACCOUNT, encoding='utf-8')
    return repo


def _vdc_account_findings(pc, repo):
    saved = pc.ROOT
    try:
        pc.ROOT = repo
        return ' | '.join(str(getattr(f, 'detail', f))
                          for f in pc._very_deep_check_write_up(None))
    finally:
        pc.ROOT = saved




# A raw comparison of a source's `level` against a level name: the field
# read straight (`x.get('level')`, `x['level']`, or a name bound to either in
# the same function) on one side, a level name or a *LEVELS tuple on the
# other. precedent_resolve.declared_level / normalize_level is the one
# reader; a comparison through it is a call, never matched here.
_LEVEL_NAMES = frozenset({'shared', 'team', 'individual', 'universal'})




# --------------------------------------------------------------------------
# ONE BUILD, COPIED BY PATH: a fixture tree a tool writes its own path into.
#
# A fresh precedent_install.py (about 9 seconds) and a pair of bootstrapped
# practice sets (a couple of seconds each) are the same bytes every time,
# but for the directory they were made in, which they write into a few
# files: the install report, a leak blocklist's comment, a session's
# practice list. _fixture_tree_cache builds one under a scratch directory,
# keeps it with that directory's path held as a marker, and copies it into
# each check's own directory with the marker written back as that path.
#
# CONTRACT (practice: review-against-a-contract): a copy is what a build in
# the check's own directory would leave, but for __pycache__, which is never
# kept (compiled files carry the path, and Python rebuilds them), and the
# time a build stamps (an install's MANIFEST.json generated_at_utc; checked
# 2026-10-31, file by file, against an install made in place). The key is
# _seed_cache_key's for an empty destination (ONE CONSUMER, COPIED above
# says what that covers) plus the recipe's name and today's UTC date, since
# a build may write the date. Every build runs under _isolated_env -- an
# empty HOME, no user config, no token, no PRECEDENT_*/GIT_* variable but
# PRECEDENT_SEED_OFF_MAIN, local git only -- which is what lets the key read
# HOME, and a build that writes anything into HOME, or fails, is never kept.
# PRECEDENT_NO_SEED_CACHE=1, or any error, builds in the check's directory.
_TREE_CACHE_MARKER = '@@PRECEDENT-HARNESS-FIXTURE-ROOT@@'
_TREE_CACHE_HOME_MARKER = '@@PRECEDENT-HARNESS-FIXTURE-HOME@@'


def _fixture_tree_env(home):
    """The environment every _fixture_tree_cache build runs under."""
    return dict(_isolated_env(os.environ, home), PRECEDENT_SEED_OFF_MAIN='1')


def _fixture_tree_cache(recipe, target, build, only=None):
    """build(root, env) -> (ok, outputs): writes a fixture tree into the
    existing empty directory `root` and returns a JSON-able dict of strings
    (its reports). This puts the same tree into `target` -- an existing,
    empty directory -- from the cache when it can, and returns the outputs
    with `target` and this call's HOME in place of the build's. `only`
    names the top-level entries of the tree to copy (all when None)."""
    import tempfile
    from datetime import datetime, timezone
    marker, home_marker = _TREE_CACHE_MARKER, _TREE_CACHE_HOME_MARKER
    target = pathlib.Path(target)
    with tempfile.TemporaryDirectory(prefix='fixture-home-') as home:
        env = _fixture_tree_env(home)

        def for_real():
            ok, outputs = build(target, env)
            if only is not None:
                for child in target.iterdir():
                    if child.name not in only:
                        shutil.rmtree(child) if child.is_dir() else child.unlink()
            return outputs

        def rewrite(top, old, new):
            for p in top.rglob('*') if top.is_dir() else [top]:
                if p.is_file() and not p.is_symlink():
                    data = p.read_bytes()
                    if old in data:
                        p.write_bytes(data.replace(old, new))

        if os.environ.get('PRECEDENT_NO_SEED_CACHE') == '1':
            return for_real()
        probe = pathlib.Path(tempfile.mkdtemp(prefix='fixture-key-'))
        try:
            day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            key = _seed_cache_key(probe, f'fixture-tree {recipe} {day}', env)
        except (OSError, ValueError, subprocess.SubprocessError):
            key = None                      # an accelerator, never a dependency
        finally:
            shutil.rmtree(probe, ignore_errors=True)
        if key is None:
            return for_real()
        cache = _seed_cache_dir()
        entry = cache / f'tree-{key}'
        if not (entry / 'complete').is_file():
            scratch = pathlib.Path(tempfile.mkdtemp(prefix='fixture-build-'))
            staging = None
            try:
                root = scratch / 'root'
                root.mkdir()
                ok, outputs = build(root, env)
                if ok and not any(pathlib.Path(home).iterdir()):
                    cache.mkdir(parents=True, exist_ok=True)
                    _seed_cache_prune(cache)
                    staging = pathlib.Path(tempfile.mkdtemp(
                        prefix=f'.build-tree-{key[:12]}-', dir=cache))
                    shutil.copytree(root, staging / 'root', symlinks=True,
                                    ignore=shutil.ignore_patterns('__pycache__'))
                    rewrite(staging / 'root', os.fsencode(str(root)), marker.encode())
                    (staging / 'outputs.json').write_text(json.dumps(
                        {k: v.replace(str(root), marker).replace(home, home_marker)
                         for k, v in outputs.items()}), encoding='utf-8')
                    (staging / 'complete').write_text(key + '\n', encoding='utf-8')
                    os.rename(staging, entry)   # atomic; loses to an entry already there
            except OSError:
                pass
            finally:
                shutil.rmtree(scratch, ignore_errors=True)
                if staging is not None and staging.exists():
                    shutil.rmtree(staging, ignore_errors=True)
            # The build above wrote into HOME (it is still this call's), so
            # a build for real starts from an emptied one.
            for child in pathlib.Path(home).iterdir():
                shutil.rmtree(child) if child.is_dir() else child.unlink()
        if not (entry / 'complete').is_file():
            return for_real()
        try:
            os.utime(entry)                 # in use: the prune leaves it
            outputs = json.loads((entry / 'outputs.json').read_text(encoding='utf-8'))
            for child in sorted((entry / 'root').iterdir()):
                if only is not None and child.name not in only:
                    continue
                dest = target / child.name
                if child.is_dir() and not child.is_symlink():
                    shutil.copytree(child, dest, symlinks=True)
                else:
                    shutil.copy2(child, dest, follow_symlinks=False)
                rewrite(dest, marker.encode(), os.fsencode(str(target)))
        except OSError:
            for child in list(target.iterdir()):    # undo, then build for real
                shutil.rmtree(child, ignore_errors=True) if child.is_dir() else child.unlink()
            return for_real()
        return {k: v.replace(marker, str(target)).replace(home_marker, home)
                for k, v in outputs.items()}


def _fresh_install_fixture(dest):
    """A fresh `precedent_install.py <dest> --project-name Fixture` into an
    empty repository at `dest` (made here when absent), the install every
    install check runs, through _fixture_tree_cache.
    -> (returncode, stdout, stderr) of the install."""
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    def build(root, env):
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(root)], env=env,
                       capture_output=True, check=True)
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                            str(root), '--project-name', 'Fixture'], cwd=str(ROOT),
                           env=env, capture_output=True, text=True)
        return r.returncode == 0, {'rc': str(r.returncode), 'stdout': r.stdout,
                                   'stderr': r.stderr}
    out = _fixture_tree_cache('fresh-install Fixture 1', dest, build)
    return int(out['rc']), out['stdout'], out['stderr']




HARNESS_ROTATION_BUCKETS = 10

def _deep_assertion_slugs():
    """-> slugs whose planted output a later assertion reads back.

    Read out of the harness's own text, every file of it (the planted
    cases live in tools/harness/vh_planted_cases.py since the 2026-10-31
    split; this file alone would answer "none"). A case that is skipped must
    not leave `planted['<slug>']` missing for code that indexes it
    directly, and the set of such slugs is exactly what a regex
    over the source can answer without anyone maintaining a list.
    """
    try:
        src = harness_parts.read_all(ROOT)
    except OSError:               # practice: fail-gracefully
        return None               # unknown -> caller runs everything
    found = set()
    for m in re.finditer(r"planted\['([A-Za-z0-9-]+)'\]", src):
        found.add(m.group(1)[:-len('-clean')]
                  if m.group(1).endswith('-clean') else m.group(1))
    return found

# THE SHARDS CI RUNS, and the one description of them there is. `--as-ci`
# starts these side by side, cutting the rest shard into parts
# (_as_ci_runs), and since 2026-10-07 GitHub's deep-check job runs exactly
# that command rather than keeping its own copy of the split
# (check_as_ci_shards_match_the_workflow refuses a second copy). The heavy
# check is its own shard because it is a large slice of the runtime
# (spec/VERIFY_HARNESS_PERFORMANCE.md). A plain local run sets neither
# variable, so the whole filter path -- every behaviour that depends on a
# check being replaced by a stand-in -- is code no plain run executes.
#
# That gap hid a crash on 2026-09-21: the full local suite reported
# 244 passed, 0 failed while BOTH sharded CI jobs died before their first
# verdict (gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-
# green-ci). The copy this table used to mirror went stale the other way on
# 2026-09-30, and GitHub ran on one core for a week
# (gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy).
CI_SHARDS = (
    ('heavy -- check_precedent_check_fires only, every planted case',
     {'PRECEDENT_CHECK_ONLY': 'check_precedent_check_fires',
      'PRECEDENT_HARNESS_ALL': '1'}),
    ('rest -- everything except that one',
     {'PRECEDENT_CHECK_SKIP': 'check_precedent_check_fires'}),
)


# The line prefixes that start a verdict (check() and not_applicable()); a
# FAIL's text runs until the next one.
_VERDICT_STARTS = ('PASS:', 'FAIL:', 'N/A:')


def _fail_blocks(stdout, cap=40):
    """-> [[line, ...]] each FAIL: verdict with the lines of its failure text
    that follow it, up to the next verdict, at most `cap` lines each.
    A failure text that runs over several lines kept only its first until
    2026-09-30: "an update that deletes a vendored file upstream dropped
    ends DONE" failed once in a full run, with its cause cut off, then
    passed four times in a row and the cause was never found."""
    blocks, cur = [], None
    for line in stdout.splitlines():
        if line.startswith(_VERDICT_STARTS):
            cur = [line] if line.startswith('FAIL:') else None
            if cur is not None:
                blocks.append(cur)
        elif cur is not None:
            if len(cur) < cap:
                cur.append(line)
            elif len(cur) == cap:
                cur.append('... (cut at 40 lines)')
    return blocks


def _shard_failure_detail(proc, tail_lines=20):
    """-> [str] what a failed shard says about WHY: every `FAIL:` verdict it
    printed, then the last `tail_lines` lines of its stderr. Until
    2026-09-28 a failed shard printed `SHARD FAILED (exit 1)` and nothing
    else, so the reason -- a named failing case, or a traceback that killed
    the shard before its first verdict -- meant rerunning four minutes of
    suite to find out."""
    out = []
    fails = _fail_blocks(proc.stdout or '')
    if fails:
        out.append(f'  {len(fails)} failing case(s):')
        for block in fails:
            out += [f'    {l}' for l in block]
    err = [l for l in (proc.stderr or '').splitlines() if l.strip()]
    if err:
        out.append(f'  last {min(tail_lines, len(err))} line(s) of its stderr:')
        out += [f'    {l}' for l in err[-tail_lines:]]
    if not out:
        out.append('  it printed no FAIL: line and nothing on stderr')
    return out


def _failing_case_lines(label, proc):
    """-> [str] one line per failing case a failed shard names: its FAIL:
    verdict, without the failure text below it. A shard that died before
    its first verdict gets one line saying so."""
    fails = _fail_blocks(proc.stdout or '')
    if not fails:
        return [f'shard {label}: exit {proc.returncode} with no FAIL: line '
                '(it died before a verdict; its stderr is in the run log)']
    return [b[0].removeprefix('FAIL:').strip() for b in fails]


def _write_failing_cases(lines):
    """Write `lines` to the file PRECEDENT_HARNESS_FAILURES names, if it
    names one; nothing otherwise. GitHub's "main's test failed" issue read
    the failing step's name from the jobs API and came back empty on
    2026-10-29 (issue #1402: "could not be read; open the run"), and a step
    name would only have said "the harness" anyway. The issue step reads
    this file and names the failing cases itself. Written on a green run
    too, empty, so a stale file never speaks for this one."""
    target = os.environ.get('PRECEDENT_HARNESS_FAILURES')
    if not target:
        return
    try:
        pathlib.Path(target).write_text(''.join(f'{l}\n' for l in lines),
                                        encoding='utf-8')
    except OSError as e:
        print(f'--as-ci: could not write the failing cases to {target}: {e}')


# WHAT EACH CHECK TOOK, committed, so the deal below is the same on every
# machine that runs `--as-ci` -- a session's and GitHub's runner alike. A
# record kept under .precedent/ would deal differently on each one, and the
# two sides would quietly stop running the same parts again
# (gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy).
# Refreshed only when asked: `--as-ci --record-times` (run_as_ci).
HARNESS_CHECK_TIMES = ROOT / 'tools' / 'harness_check_times.json'
# When the last green whole-suite `--all --record-times` run finished, in the
# person's zone with its offset (very_deep_check.py reads the same key).
GREEN_FULL_RUN_KEY = 'green_full_run'

# How many processes `--as-ci` starts, wherever it runs: the heavy shard
# plus three parts of the rest. A fixed number, not the machine's cores,
# so GitHub's four-core runner and a session's container deal the suite
# identically. PRECEDENT_AS_CI_JOBS still overrides it for one run.
AS_CI_JOBS = 4


def _check_times(path=None):
    """-> ({check name: seconds}, default seconds) from HARNESS_CHECK_TIMES;
    ({}, None) when it is missing or unreadable, and the deal then goes by
    names alone."""
    try:
        rec = json.loads(pathlib.Path(path or HARNESS_CHECK_TIMES)
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}, None
    if not isinstance(rec, dict):
        return {}, None
    times = {k: float(v) for k, v in (rec.get('seconds') or {}).items()
             if isinstance(v, (int, float)) and v >= 0}
    default = rec.get('default_seconds')
    return times, (float(default) if isinstance(default, (int, float)) else None)


def _write_check_times(seconds, measured, path=None, default=None, green=None):
    """Rewrite HARNESS_CHECK_TIMES from {check name: seconds}. Every check is
    named, so default_seconds covers only checks added since. `default`
    keeps the recorded one: only a whole re-record moves it (2026-10-17,
    harness_times_merge.py says why).

    `green`: when the last green whole-suite run (`--all --record-times`)
    finished, a timestamp with its offset. Only that run passes one; every
    other write keeps the one recorded. The very deep check's --record-pass
    reads it: a pass is recorded only after a green whole-suite run in the
    same run (Morgan, 2026-10-31, strength: decided: "Update the very deep
    instructions so to fix this in the future")."""
    if green is None:
        try:
            green = json.loads(pathlib.Path(path or HARNESS_CHECK_TIMES)
                               .read_text(encoding='utf-8')).get(GREEN_FULL_RUN_KEY)
        except (OSError, ValueError, AttributeError):
            green = None
    vals = sorted(seconds.values())
    rec = {
        'about': ('What each verify_harness check took, read by --as-ci to '
                  'deal the suite into parts the same way on every machine. '
                  "Regenerate with: python3 tools/verify_harness.py --as-ci "
                  "--record-times --because '<why>'. A check missing here "
                  'counts as default_seconds. green_full_run is when the last '
                  'green --all --record-times run finished.'),
        'measured': measured,
        'default_seconds': (default if default is not None else
                            round(vals[len(vals) // 2], 2) if vals else 1.0),
        'seconds': {k: round(v, 1) for k, v in sorted(seconds.items())},
    }
    if green:
        rec[GREEN_FULL_RUN_KEY] = green
    pathlib.Path(path or HARNESS_CHECK_TIMES).write_text(
        json.dumps(rec, indent=1) + '\n', encoding='utf-8')


def record_new_times():
    """--record-new-times: run only the tests HARNESS_CHECK_TIMES does not
    name, and add what each took. -> the run's exit code.

    A TEST'S TIME IS RECORDED WITH THE TEST (Morgan, 2026-10-16: "The new
    heavy tests should be in the batch of tests as they land on the
    branch"). The list was refreshed only by a whole --as-ci
    --record-times run, about 13 minutes nobody remembered after
    2026-10-09, so a hundred tests were dealt into CI's parts as
    default_seconds -- the slowest of them took 17.8 s. This times only
    the missing ones, in seconds to a few minutes, and the per-file step
    of the push check refuses a new test whose time is not recorded
    (precedent_push_check.changed_files_check), naming this command."""
    import tempfile
    times, default = _check_times()
    names = sorted(n for n, v in globals().items()
                   if n.startswith('check_') and callable(v))
    missing = [n for n in names if n not in times]
    # A TEST THAT IS GONE LEAVES THE LIST HERE (2026-10-17). Before, only a
    # whole --as-ci --record-times run, about fourteen minutes, cleared a
    # removed test's time, and the --as-ci partition case refused the list
    # until then. The run's other fields stay as recorded, so two branches
    # that each record a test touch only their own lines.
    stale = sorted(n for n in times if n not in set(names))
    if stale:
        times = {n: t for n, t in times.items() if n not in set(stale)}
        print(f'verify_harness: dropped {len(stale)} time(s) for test(s) that no '
              f'longer exist: ' + ', '.join(stale))
    try:
        before = json.loads(HARNESS_CHECK_TIMES.read_text(encoding='utf-8')).get(
            'measured', '')
    except (OSError, ValueError):
        before = ''
    if not missing:
        if stale:
            _write_check_times(times, before, default=default)
            print(f'verify_harness: wrote {HARNESS_CHECK_TIMES.relative_to(ROOT)}; '
                  f'commit it.')
        else:
            print('verify_harness: every test already has a recorded time.')
        return 0
    # ONE BASIS (2026-10-17). The list is recorded by `--as-ci
    # --record-times`, on CI's parts; this times tests in one process on
    # whatever machine it runs on. Three tests the list already names run
    # beside the new ones, and the new times are scaled by how the two
    # compare, so the deal into GitHub's parts stays even.
    calib = sorted(n for n, t in times.items() if 1.0 <= t <= 5.0
                   and n in names)[:3]
    print(f'verify_harness: timing {len(missing)} test(s) with no recorded '
          f'time: ' + ', '.join(missing), flush=True)
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / 'times.json'
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'verify_harness.py')],
                           cwd=ROOT, env=dict(os.environ,
                                              PRECEDENT_CHECK_ONLY=','.join(missing + calib),
                                              PRECEDENT_HARNESS_TIMES_OUT=str(out)))
        got = json.loads(out.read_text(encoding='utf-8')) if out.is_file() else {}
    here = sum(got.get(n, 0) for n in calib)
    there = sum(times[n] for n in calib if n in got)
    scale = min(max(there / here, 0.25), 4.0) if here > 0 and there > 0 else 1.0
    got = {n: dt * scale for n, dt in got.items() if n in missing}
    if not got:
        print('verify_harness: the run recorded no times; nothing written.')
        return r.returncode or 1
    _write_check_times({**times, **got}, before, default=default)
    print(f'verify_harness: {len(got)} added by --record-new-times, scaled by '
          f'{scale:.2f} to the recorded basis.')
    print(f'verify_harness: recorded {len(got)} time(s) in '
          f'{HARNESS_CHECK_TIMES.relative_to(ROOT)}; commit it with the tests.')
    return r.returncode


def _deal_by_time(names, parts, times, default=None):
    """-> [[name, ...]] * parts: every name in exactly one part, the slowest
    dealt first, each to whichever part has the least time so far. A check
    with no record counts as `default` (the record's default_seconds; else
    the median recorded time; one second with no record at all). Ties go
    by name, so the deal depends only on the names and the committed
    record -- never on the machine.

    Until 2026-10-07 the deal was round-robin by name, and the slow checks
    bunched up: one Debut's three parts took 634, 316 and about 640
    seconds (todo-2026-10-06-deal-harness-checks-by-measured-time)."""
    if default is None:
        known = sorted(times.values())
        default = known[len(known) // 2] if known else 1.0
    order = sorted(names, key=lambda n: (-times.get(n, default), n))
    load = [0.0] * parts
    dealt = [[] for _ in range(parts)]
    for n in order:
        i = min(range(parts), key=lambda k: (load[k], k))
        dealt[i].append(n)
        load[i] += times.get(n, default)
    return [sorted(d) for d in dealt]


def _as_ci_runs(jobs, names=None, times=None):
    """-> [(label, env_extra)]: the processes `--as-ci` starts side by side.

    CI_SHARDS as they are, except that the one shard run by SKIP (CI's
    "rest") is cut into enough parts to fill `jobs` processes. Each part
    still runs by PRECEDENT_CHECK_SKIP -- the shard's own filter path, the
    half a plain local run never executes -- skipping the heavy check and
    every name the other parts take. Names are dealt by their recorded
    time (_deal_by_time), so every check runs in exactly one process.

    Safe to split because no check calls another and none takes another's
    result (both verified over the whole file, 2026-09-30): a check sees the
    same arguments in a part as in the whole shard."""
    if names is None:
        names = sorted(n for n, v in globals().items()
                       if n.startswith('check_') and callable(v))
    skip_shards = [s for s in CI_SHARDS if 'PRECEDENT_CHECK_SKIP' in s[1]]
    parts = max(1, jobs - (len(CI_SHARDS) - len(skip_shards)))
    if len(skip_shards) != 1 or parts == 1:
        return list(CI_SHARDS)
    label, env_extra = skip_shards[0]
    base_skip = set(env_extra['PRECEDENT_CHECK_SKIP'].split(','))
    rest = [n for n in names if n not in base_skip]
    times, default = _check_times() if times is None else (times, None)
    dealt = _deal_by_time(rest, parts, times, default)
    out = []
    for s in CI_SHARDS:
        if s is not skip_shards[0]:
            out.append(s)
            continue
        for i, mine in enumerate(dealt):
            others = [n for n in rest if n not in set(mine)]
            out.append((f'{label} (part {i + 1} of {parts}, {len(mine)} checks)',
                        {**env_extra, 'PRECEDENT_CHECK_SKIP':
                         ','.join(sorted(base_skip) + others)}))
    return out


def _bare_all_runs_in_parallel(argv, environ):
    """-> True when this invocation is a bare `--all`, which run_as_ci runs
    across the cores: no filter of its own, and not asked to stay serial."""
    return ('--all' in argv
            and not environ.get('PRECEDENT_CHECK_ONLY')
            and not environ.get('PRECEDENT_CHECK_SKIP')
            and environ.get('PRECEDENT_HARNESS_SERIAL') != '1')


# A FULL RUN IS PROPOSED BEFORE IT STARTS (Morgan, 2026-10-07, strength:
# decided). A session started this suite whole, by hand, to double-check
# work bound only for the landing branch, quoted "15 to 25 minutes" from memory,
# and was still running at 25 minutes with a third done -- the one-process
# run takes about 40. answer-first-ask-before-long-work already said to
# propose a long run with the tool's own cost line; this suite had no such
# line, and nothing stopped it starting. Now a full run started by hand
# states what it costs and refuses without --because quoting the person's
# go-ahead. The callers that were asked for by name pass their own reason
# (precedent_push_check.py at the staging and main tiers, the very deep
# check's step 2), GitHub's runner is let through, and a run filtered to
# named checks (PRECEDENT_CHECK_ONLY / SKIP) is not a full run at all.
HARNESS_ASKED_ENV = 'PRECEDENT_HARNESS_ASKED'
HARNESS_TIMINGS = ROOT / '.precedent' / 'harness_timings.json'
# What each shape took when it was last measured, for a machine that has
# recorded none of its own. Measured, never guessed: the serial figure is
# 562 checks in 2369 s on a 4-core container (2026-10-07); the parallel
# --all figure is check_bare_all_runs_across_the_cores' (2026-10-06); the
# isolated one is precedent_push_check.py's note (2026-09-29).
HARNESS_MEASURED = {
    'one process': (40, '2026-10-07, 4 cores'),
    '--as-ci': (11, '2026-10-06, 4 cores'),
    '--all': (11, '2026-10-06, 4 cores'),
    '--as-ci --isolated': (13, '2026-09-29'),
}


def _because(argv):
    """-> the text after --because, or '' when there is none."""
    if '--because' in argv:
        i = argv.index('--because')
        if i + 1 < len(argv):
            return argv[i + 1].strip()
    return ''


def _full_run_shape(argv, environ):
    """-> which full run this invocation is ('one process', '--as-ci',
    '--all', '--as-ci --isolated'), or None for a run filtered to named
    checks -- a shard, or a session running the tests it changed."""
    if environ.get('PRECEDENT_CHECK_ONLY') or environ.get('PRECEDENT_CHECK_SKIP'):
        return None
    if '--as-ci' in argv:
        return '--as-ci --isolated' if '--isolated' in argv else '--as-ci'
    return '--all' if '--all' in argv else 'one process'


def _full_run_cost(shape, timings_file=None):
    """-> one line: what this shape took the last time it was measured,
    on this machine if it has recorded a run, else HARNESS_MEASURED's."""
    try:
        rec = json.loads(pathlib.Path(timings_file or HARNESS_TIMINGS)
                         .read_text(encoding='utf-8')).get(shape)
    except (OSError, ValueError, AttributeError):
        rec = None
    if isinstance(rec, dict) and rec.get('minutes'):
        return (f'a full run ({shape}) took {rec["minutes"]} minutes the last '
                f'time on this machine ({rec.get("when", "date unknown")})')
    mins, when = HARNESS_MEASURED.get(shape, (None, None))
    if mins is None:
        return f'a full run ({shape}) has no recorded time'
    return (f'a full run ({shape}) takes about {mins} minutes (measured '
            f'{when}; this machine has recorded none of its own)')


def _full_run_refusal(argv, environ):
    """-> the refusal text when this is a full run started by hand with no
    go-ahead, else None (see HARNESS_ASKED_ENV above)."""
    shape = _full_run_shape(argv, environ)
    if shape is None or environ.get('GITHUB_ACTIONS') == 'true':
        return None
    if environ.get(HARNESS_ASKED_ENV) or _because(argv):
        return None
    again = ' '.join(['python3 tools/verify_harness.py', *argv,
                      "--because '<their words>'"])
    faster = (f' The same tests side by side, --as-ci: '
              f'{_full_run_cost("--as-ci")}.' if shape == 'one process' else '')
    return (f'verify_harness: NOT STARTED -- {_full_run_cost(shape)}.{faster}\n'
            f'A run that long is proposed to the person first: what it is, '
            f'that time, what it blocks and what it does not '
            f'(answer-first-ask-before-long-work). Once they say go:\n'
            f'  {again}\n'
            f'Not needed for:\n'
            f'  - the tests your change touched: '
            f'PRECEDENT_CHECK_ONLY=check_a,check_b python3 tools/verify_harness.py\n'
            f'  - Booked (staging): its push check is the quick tier\n'
            f'  - Debut and Produce: precedent_push_check.py runs the whole '
            f'suite itself, in the faster --as-ci shape')


def _record_full_run(shape, seconds, rc, timings_file=None):
    """Keep what a finished full run took, for the next run's cost line.
    Local and untracked (.precedent/), so it never dirties the tree; a
    failed write costs only the estimate."""
    if shape is None or rc not in (0, 1):
        return
    path = pathlib.Path(timings_file or HARNESS_TIMINGS)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        data = data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        data = {}
    data[shape] = {'minutes': max(1, round(seconds / 60)),
                   'when': time.strftime('%Y-%m-%d') + f', {os.cpu_count() or 1} cores'}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    except OSError:
        pass


def _as_ci_scope(every_case):
    """-> (the checks to run, or None for every one; a line saying which;
    the harness_reach module, or None when it would not load).

    SCOPED TO THE CHANGE (Alex, 2026-10-12: "Can we have BestPractice
    checks limit themselves to checking changes that were actually
    made?"): only the checks the change reaches since the ledger a full
    run recorded (tools/harness_reach.py says how, and what it cannot
    see). The whole suite when asked (--all, PRECEDENT_HARNESS_FULL=1),
    when this run is the one recording the ledger, or when no ledger can
    be used -- harness_reach decides and says which."""
    try:
        spec = importlib.util.spec_from_file_location(
            '_harness_reach', ROOT / 'tools' / 'harness_reach.py')
        hr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hr)
    except Exception as e:                    # noqa: BLE001
        return None, f'the whole suite: harness_reach would not load ({e})', None
    if every_case:
        return None, 'the whole suite: --all', hr
    if os.environ.get('HARNESS_REACH_RECORD'):
        return None, 'the whole suite: this run records the ledger', hr
    names = sorted(n for n, v in globals().items()
                   if n.startswith('check_') and callable(v))
    try:
        selected, account = hr.plan(names)
    except Exception as e:                    # noqa: BLE001
        return None, f'the whole suite: the change scope could not be worked out ({e})', hr
    return selected, account, hr


def _planted_sweep_runs(every_case, environ=None):
    """-> True when this --as-ci run includes _PLANTED_SUITE.

    ONLY IN A WHOLE-SUITE RUN ASKED FOR BY NAME (Morgan, 2026-10-29,
    strength: decided: "let's NO LONGER RUN the full 519 second test of
    everything on main ... it should run when I do a 'very deep test'; and
    also ... in the nightly tests"): `--all` (the very deep check runs it
    that way), PRECEDENT_HARNESS_FULL=1 (deep-check.yml's nightly and
    by-hand runs) or a ledger recording. Every other run -- the pull
    request into main, the push after a Produce, a Debut, a landing's
    scoped run -- leaves it out, even when the change reaches most of the
    suite. It read files nearly every commit touches, so a scoped run
    always picked it, and it alone took 519 s of GitHub's run that day.
    What is given up: a check that stops firing is found by the nightly
    run, up to a day later, instead of at the merge."""
    environ = os.environ if environ is None else environ
    return bool(every_case or environ.get('PRECEDENT_HARNESS_FULL') == '1'
                or environ.get('HARNESS_REACH_RECORD'))


def run_as_ci(every_case=False, record_times=False):
    """-> exit status. Run this suite the way CI runs it, side by side.

    every_case: give every process PRECEDENT_HARNESS_ALL=1, which is what a
    bare `--all` asks for (see the bottom of this file).
    record_times (`--record-times`): after a green run, rewrite
    HARNESS_CHECK_TIMES from what each check took here, so the next deal
    is balanced on today's suite. It changes a committed file, so it runs
    only when asked.

    NOT the same work twice: the shards PARTITION the suite. Until
    2026-09-30 they ran one after the other, and the rest shard ran its
    three hundred-odd checks on one core, so a four-core session paid
    about sixteen minutes, mostly waiting (a landing check ran five times
    in one afternoon). Now every shard starts at once, and the rest shard
    is dealt into parts to fill PRECEDENT_AS_CI_JOBS processes (default:
    the machine's cores, at most four) -- _as_ci_runs() says how.
    PRECEDENT_AS_CI_JOBS=1 is the old serial run.

    SINCE 2026-10-07 IT IS CI'S COMMAND: GitHub's deep-check job runs
    `verify_harness.py --as-ci` itself, so there is one description of the
    split, here, and nothing to drift
    (check_as_ci_shards_match_the_workflow).

    IT REPRODUCES CI'S COMMAND, NOT CI'S ENVIRONMENT, and the
    difference is worth stating because over-promising here would repeat
    the exact failure this exists to fix. A local session resolves private
    practice sources that CI has no credential for, so a check keyed to one
    of them can fail here and pass there -- and the reverse, a check that
    needs something only CI has, would fail here for the same reason.
    Green under --as-ci means the shard SHAPE is not what breaks; it does
    not mean CI will be green."""
    import tempfile
    try:
        jobs = int(os.environ.get('PRECEDENT_AS_CI_JOBS') or 0)
    except ValueError:
        jobs = 0
    jobs = jobs or AS_CI_JOBS
    selected, account, hr = _as_ci_scope(every_case)
    print(f'--as-ci: {account}', flush=True)
    # A whole-suite run asked to record (PRECEDENT_HARNESS_RECORD_FULL=1:
    # GitHub on main, or harness_reach.py record) keeps what each check
    # reaches -- the ledger the next scoped run selects from. Recording
    # needs sys.monitoring (Python 3.12) to stay cheap.
    record_dir = None
    if (selected is None and hr is not None and not os.environ.get('HARNESS_REACH_RECORD')
            and os.environ.get('PRECEDENT_HARNESS_RECORD_FULL') == '1'):
        if sys.version_info >= (3, 12):
            record_dir = pathlib.Path(tempfile.mkdtemp(prefix='harness-reach-'))
            print('--as-ci: recording what each check reaches', flush=True)
        else:
            print('--as-ci: not recording what each check reaches -- that '
                  'needs Python 3.12', flush=True)
    runs = _as_ci_runs(jobs, names=sorted(selected) if selected is not None else None)
    if not _planted_sweep_runs(every_case):
        if selected is not None:
            selected = selected - {_PLANTED_SUITE}
        runs = [(label, e) for label, e in runs
                if e.get('PRECEDENT_CHECK_ONLY') != _PLANTED_SUITE]
        print(f'--as-ci: {_PLANTED_SUITE} is left out: it runs every planted '
              f'case only in a whole-suite run asked for by name -- the nightly '
              f'run, one started by hand, --all, the very deep check', flush=True)
    if selected is not None:
        # A shard that runs only named checks, none of them reached, has
        # nothing to do.
        runs = [(label, e) for label, e in runs
                if 'PRECEDENT_CHECK_ONLY' not in e
                or set(e['PRECEDENT_CHECK_ONLY'].split(',')) & selected] or runs[:1]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-as-ci-'))
    started = []
    t0 = time.monotonic()
    for i, (label, env_extra) in enumerate(runs):
        env = dict(os.environ) if record_dir is None else hr.record_env(record_dir)
        # Each shard gets a clean slate of BOTH variables, so a session that
        # already has one exported does not silently skew a shard.
        env.pop('PRECEDENT_CHECK_ONLY', None)
        env.pop('PRECEDENT_CHECK_SKIP', None)
        env.pop('PRECEDENT_HARNESS_ALL', None)
        env.pop('PRECEDENT_CHECK_SELECT', None)
        env.update(env_extra)
        if selected is not None:
            env['PRECEDENT_CHECK_SELECT'] = ','.join(sorted(selected))
        if every_case:
            env['PRECEDENT_HARNESS_ALL'] = '1'
        if record_times:
            env['PRECEDENT_HARNESS_TIMES_OUT'] = str(tmp / f'{i}.times.json')
        # Files, not pipes: a shard that fills a pipe nobody reads yet stalls.
        out, err = open(tmp / f'{i}.out', 'w+'), open(tmp / f'{i}.err', 'w+')
        proc = subprocess.Popen([sys.executable, str(pathlib.Path(__file__))],
                                env=env, stdout=out, stderr=err, text=True)
        started.append((label, proc, out, err))
    print(f'--as-ci: {len(started)} shard process(es) started side by side',
          flush=True)
    while True:
        running = [p for _l, p, _o, _e in started if p.poll() is None]
        if not running:
            break
        try:
            running[0].wait(timeout=30)
        except subprocess.TimeoutExpired:
            print(f'  -- {len(started) - len(running)} of {len(started)} shard '
                  f'process(es) done, {time.monotonic() - t0:.0f}s elapsed',
                  flush=True)
    failed, failing_cases = [], []
    for label, proc, out, err in started:
        out.seek(0)
        err.seek(0)
        done = subprocess.CompletedProcess(proc.args, proc.returncode,
                                           out.read(), err.read())
        out.close()
        err.close()
        print(f'\n=== shard: {label} ===', flush=True)
        # 'planted cases ran' is the heavy shard's statement of what it
        # selected; the very deep check quotes it as evidence that every
        # case ran.
        tail = [l for l in done.stdout.splitlines()
                if 'passed,' in l or l.startswith('  - ')
                or 'planted cases ran' in l]
        for line in tail[-12:]:
            print(line)
        if done.returncode != 0:
            failed.append(label)
            failing_cases += _failing_case_lines(label, done)
            print(f'  SHARD FAILED (exit {done.returncode})')
            for line in _shard_failure_detail(done):
                print(line)
    _write_failing_cases(failing_cases)
    recorded = {}
    if record_times and not failed:
        for f in sorted(tmp.glob('*.times.json')):
            # The largest wins: a shard's filtered-out checks are timed too,
            # as near-zero no-ops, and must not overwrite the real run.
            try:
                for n, dt in json.loads(f.read_text(encoding='utf-8')).items():
                    recorded[n] = max(dt, recorded.get(n, 0.0))
            except (OSError, ValueError, AttributeError, TypeError):
                pass
    shutil.rmtree(tmp, ignore_errors=True)
    if record_dir is not None:
        # The tree, not the commit: a pull request's run tests a merge
        # commit main never has, but main's commit after the merge holds
        # the same tree, so a later run can diff against it.
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD^{tree}'],
                              capture_output=True, text=True).stdout.strip()
        ledger = hr.merge(record_dir, head)
        # A failing check may have stopped before it reached everything it
        # would: such a ledger is kept for a look, and never published.
        ledger['green'] = not failed
        hr.LOCAL_LEDGER.parent.mkdir(exist_ok=True)
        hr.LOCAL_LEDGER.write_text(json.dumps(ledger, sort_keys=True), encoding='utf-8')
        unseen = sum(1 for v in ledger['checks'].values() if v.get('o'))
        print(f'--as-ci: what {len(ledger["checks"])} checks reach written to '
              f'{hr.LOCAL_LEDGER.relative_to(ROOT)} ({unseen} always run: '
              f'their reach is not fully seen)'
              + ('' if not failed else ' -- from a run that failed, so it is '
                 'never published'))
        shutil.rmtree(record_dir, ignore_errors=True)
    wall = time.monotonic() - t0
    if recorded:
        # A green run of EVERY case (--all) is the very deep check's step 2:
        # it stamps when it finished, and --record-pass reads the stamp.
        green = None
        if every_case:
            import precedent_time
            green = precedent_time.stamp_iso(ROOT)
        _write_check_times(recorded, f'{time.strftime("%Y-%m-%d")}, '
                           f'{os.cpu_count() or 1} cores, --as-ci', green=green)
        if green:
            print(f'--as-ci: green whole-suite run recorded at {green} '
                  f'({GREEN_FULL_RUN_KEY}) -- the very deep check\'s '
                  f'--record-pass reads it.')
        print(f'--as-ci: {len(recorded)} check times written to '
              f'{HARNESS_CHECK_TIMES.relative_to(ROOT)} -- commit it.')
    elif record_times:
        print('--as-ci: check times NOT written -- only a green run records them.')
    if failed:
        print(f'\n--as-ci: {len(failed)} of {len(started)} shard process(es) '
              f'failed in {wall:.0f}s: {"; ".join(failed)}')
        return 1
    print(f'\n--as-ci: all {len(started)} shard process(es) green in '
          f'{wall:.0f}s -- this is what CI will run.')
    return 0


# What GitHub's runner does not have, and a session's machine does. Unset in
# the isolated run; see run_as_ci_isolated().
ISOLATION_UNSET = ('PRECEDENT_GIT_TOKEN', 'PRECEDENT_SOURCE_BASE_URL',
                   'PRECEDENT_INDIVIDUAL_REPO', 'CLAUDE_PROJECT_DIR')


def _isolated_env(base, home):
    """-> the environment the isolated run gives the harness: `base` with
    every PRECEDENT_* and GIT_* variable and ISOLATION_UNSET removed, $HOME
    an empty directory, no user-level config, the runner's UTC clock, and
    git refusing every transport but a local file. The last one is not
    GitHub's -- its runner has a network -- but a self-heal that clones a
    source from the network would put the missing sibling right back, and
    the run would quietly stop matching the runner it stands in for."""
    env = {k: v for k, v in base.items()
           if not k.startswith(('PRECEDENT_', 'GIT_')) and k not in ISOLATION_UNSET}
    env.update(HOME=str(home), TZ='UTC',
               PRECEDENT_USER_CONFIG=str(pathlib.Path(home) / '.no-user-config.json'),
               GIT_ALLOW_PROTOCOL='file', GIT_TERMINAL_PROMPT='0',
               GIT_CONFIG_NOSYSTEM='1')
    return env


def _new_entries(parent, before):
    """-> sorted names in `parent` that were not in `before`."""
    return sorted(set(p.name for p in pathlib.Path(parent).iterdir()) - set(before))


def _carry_uncommitted(src, dst):
    """-> how many uncommitted paths of `src` were written into the clone
    `dst` (0 when there were none), or None when they could not be.

    The copy used to be committed work only, while every other step of the
    full check reads the working tree. Run before a commit, the harness
    then judged the commit BEFORE the change and the rest judged the
    change: on 2026-10-01 a new check with no planted case (whats-new) went
    green in the full check and was refused by the merge gate's quick one,
    which reads the files. Tracked edits travel as a binary diff against
    HEAD; untracked files that are not ignored are copied as they are."""
    import shutil
    diff = subprocess.run(['git', '-C', str(src), 'diff', 'HEAD', '--binary'],
                          capture_output=True)
    if diff.returncode != 0:
        return None
    n = 0
    if diff.stdout.strip():
        r = subprocess.run(['git', '-C', str(dst), 'apply', '--binary',
                            '--whitespace=nowarn', '-'], input=diff.stdout,
                           capture_output=True)
        if r.returncode != 0:
            return None
        names = subprocess.run(['git', '-C', str(src), 'diff', 'HEAD',
                                '--name-only'], capture_output=True, text=True)
        n += len(names.stdout.split())
    extra = subprocess.run(['git', '-C', str(src), 'ls-files', '--others',
                            '--exclude-standard', '-z'], capture_output=True)
    for rel in [x for x in extra.stdout.decode('utf-8', 'replace').split('\0') if x]:
        target = pathlib.Path(dst) / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(pathlib.Path(src) / rel, target)
        except OSError:
            return None
        n += 1
    return n


def run_as_ci_isolated():
    """-> exit status. --as-ci, from a copy of this commit laid out the way
    GitHub's runner lays it out, then the not-applicable slice again here.

    WHY. On 2026-09-29 the full local check passed and GitHub's deep-check
    failed: build_views sized a set's occasion cap from the universal source
    cloned BESIDE it, and the runner has no sibling clones, so universal
    measured 0. --as-ci reproduces CI's command shape and never its
    environment (run_as_ci's docstring); this is the environment half.

    THE COPY. A clone of HEAD in a temporary directory whose parent holds
    nothing else, with this checkout's remote-tracking refs and origin URL
    (actions/checkout's fetch-depth: 0 gives the runner every branch), run
    under _isolated_env(): an empty $HOME, no user config, no source token,
    UTC. The checkout's uncommitted changes are carried into it
    (_carry_uncommitted), so it judges what the rest of the check judges;
    a commit pushed later is what the runner checks out.

    THE SECOND RUN. A test that needs what only this machine has -- a
    private source, a sibling clone -- goes not-applicable in the copy.
    Those functions (not_applicable() records them) run once more here, in
    the ordinary environment, so the pair covers everything the plain
    --as-ci covered, plus what the runner would see.

    AFTERWARDS the copy's parent must still hold only the copy: anything
    new there is a sibling some step fetched, and the run is reported as
    no longer isolated rather than passed."""
    import shutil, tempfile
    work = pathlib.Path(tempfile.mkdtemp(prefix='precedent-isolated-'))
    t0 = time.monotonic()
    try:
        parent, home = work / 'work', work / 'home'
        parent.mkdir()
        home.mkdir()
        repo = parent / ROOT.name
        r = subprocess.run(['git', 'clone', '--quiet', '--no-checkout', str(ROOT),
                            str(repo)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f'--as-ci --isolated: could not copy this checkout: '
                  f'{r.stderr.strip()}')
            return 1
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        url = subprocess.run(['git', '-C', str(ROOT), 'remote', 'get-url',
                              'origin'], capture_output=True, text=True).stdout.strip()
        for args in (['fetch', '--quiet', str(ROOT),
                      '+refs/remotes/origin/*:refs/remotes/origin/*'],
                     ['checkout', '--quiet', '--detach', head]):
            subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
        if url:
            subprocess.run(['git', '-C', str(repo), 'remote', 'set-url',
                            'origin', url], capture_output=True)
        carried = _carry_uncommitted(ROOT, repo)
        if carried is None:
            print('--as-ci --isolated: could not carry this checkout\'s '
                  'uncommitted changes into the copy, so it would test the '
                  'last commit instead of them. Commit, then run it again.')
            return 1
        before = [p.name for p in parent.iterdir()]
        na_file = work / 'not-applicable.txt'
        env = _isolated_env(os.environ, home)
        env['PRECEDENT_NA_FUNCTIONS_FILE'] = str(na_file)
        print(f'=== isolated: {repo} at {head[:12]}'
              + (f' plus {carried} uncommitted path(s) from this checkout'
                 if carried else '')
              + ' (no siblings, empty $HOME, no source token, UTC) ===',
              flush=True)
        rc = subprocess.run([sys.executable, 'tools/verify_harness.py',
                             '--as-ci', '--because',
                             os.environ.get(HARNESS_ASKED_ENV)
                             or 'the isolated run this one was asked for'],
                            cwd=repo, env=env).returncode
        grown = _new_entries(parent, before)
        t1 = time.monotonic()
        slice_ = sorted(set(na_file.read_text(encoding='utf-8').split())
                        if na_file.is_file() else set())
        print(f'\n--as-ci --isolated: {"green" if rc == 0 else "FAILED"} in '
              f'{(t1 - t0) / 60:.1f} min; {len(slice_)} function(s) were not '
              f'applicable there' + (f': {", ".join(slice_)}' if slice_ else ''),
              flush=True)
        if grown:
            print(f'--as-ci --isolated: NOT ISOLATED -- the run added '
                  f'{", ".join(grown)} beside the copy, so it no longer '
                  f'matches a runner with no sibling clones. Find the step '
                  f'that fetched it and stop it fetching there.')
            return 1
        rc2 = 0
        if slice_:
            env2 = dict(os.environ)
            for k in ('PRECEDENT_CHECK_SKIP', 'PRECEDENT_NA_FUNCTIONS_FILE'):
                env2.pop(k, None)
            env2.update(PRECEDENT_CHECK_ONLY=','.join(slice_),
                        PRECEDENT_HARNESS_ALL='1')
            print('\n=== here, the not-applicable slice ===', flush=True)
            rc2 = subprocess.run([sys.executable, str(pathlib.Path(__file__))],
                                 env=env2).returncode
            print(f'--as-ci --isolated: the slice was '
                  f'{"green" if rc2 == 0 else "FAILED"} in '
                  f'{(time.monotonic() - t1) / 60:.1f} min', flush=True)
        return 1 if rc or rc2 else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)




_SPLIT_VARS = ('PRECEDENT_CHECK_ONLY', 'PRECEDENT_CHECK_SKIP',
               'PRECEDENT_HARNESS_ALL', 'PRECEDENT_AS_CI_JOBS',
               'PRECEDENT_HARNESS_PART', 'PRECEDENT_CHECK_SELECT')


def _selected_case_slugs(all_slugs, touched=None, count=None, forced=None,
                         named=None):
    """-> (set of slugs to run, one-line reason). Never raises: a
    selector that cannot decide runs everything, because the failure
    of a scheduler must not be silently less coverage.

    `touched` and `count` are normally read from git. They are parameters
    so this is testable without a fixture repository: a scheduler whose
    behaviour can only be observed by running the thing it schedules is a
    scheduler nobody can check, and this one decides how much of the push
    gate actually executes.

    `forced` is the same argument one level up, and it was added the day it
    bit. It normally reads the process's own `--all` / PRECEDENT_HARNESS_ALL,
    which is right for a real run and WRONG for the self-test below: that
    test asserts the selector NARROWS on an ordinary docs change, so on a
    run invoked with --all it was measuring the flag instead of the rule and
    failing 72/72. Found 2026-09-21, by the very deep check's own new step 2
    -- which prescribes --all, ran it, and turned the suite red on its first
    outing. A scheduler that cannot be exercised in the state it is not
    currently in is the same untestable scheduler this signature already
    exists to avoid.

    `named` picks cases by slug: normally PRECEDENT_HARNESS_CASES, a
    comma-separated list (2026-10-17). A session that changed one planted
    case could run the whole family or none of it; --all and
    PRECEDENT_HARNESS_ALL only force everything. The named cases run with
    the pinned ones, which later assertions read back, so nothing else
    breaks for lack of them. A name that is not a case is said, never
    silently dropped; when none is, every case runs."""
    if named is None:
        named = os.environ.get('PRECEDENT_HARNESS_CASES', '')
    wanted = {w.strip() for w in str(named or '').split(',') if w.strip()}
    if wanted:
        known = wanted & set(all_slugs)
        unknown = sorted(wanted - known)
        note = f'; not a planted case: {", ".join(unknown)}' if unknown else ''
        if not known:
            return set(all_slugs), ('all (PRECEDENT_HARNESS_CASES names no '
                                    f'planted case{note})')
        pinned = _deep_assertion_slugs() or set()
        return known | (pinned & set(all_slugs)), (
            f'{len(known)} named in PRECEDENT_HARNESS_CASES, with the '
            f'{len(pinned & set(all_slugs))} pinned{note}')
    if forced is None:
        forced = ('--all' in sys.argv
                  or os.environ.get('PRECEDENT_HARNESS_ALL') == '1')
    if forced:
        return set(all_slugs), 'all (--all / PRECEDENT_HARNESS_ALL)'
    pinned = _deep_assertion_slugs()
    if pinned is None:
        return set(all_slugs), 'all (could not read this file to find deep assertions)'
    if touched is not None and count is not None:
        touched, count = set(touched), int(count)
    else:
        try:
            base = subprocess.run(
                ['git', 'merge-base', 'HEAD', 'origin/HEAD'],
                capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
            if not base:
                base = 'HEAD~1'
            touched = set(subprocess.run(
                ['git', 'diff', '--name-only', base, '--'],
                capture_output=True, text=True,
                cwd=str(ROOT)).stdout.split())
            count = int(subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True, text=True,
                cwd=str(ROOT)).stdout.strip() or 0)
        except Exception:                                 # noqa: BLE001
            return set(all_slugs), 'all (the diff could not be read)'
    machinery = ('tools/precedent_check.py',
                 'tools/verify_harness.py')
    if any(f in touched for f in machinery) or any(
            f.startswith('tools/checks/') for f in touched):
        return set(all_slugs), 'all (this change touches the check machinery)'
    directly = {s for s in all_slugs
                if f'practices/{s}.md' in touched}
    rest = sorted(set(all_slugs) - directly - set(pinned))
    bucket = count % HARNESS_ROTATION_BUCKETS
    rot = {s for i, s in enumerate(rest)
           if i % HARNESS_ROTATION_BUCKETS == bucket}
    sel = directly | (set(pinned) & set(all_slugs)) | rot
    if not sel:
        # A BUCKET THAT SELECTED NOTHING RUNS EVERYTHING, and this is the
        # 2026-09-20 lesson ported rather than re-learned. That day
        # precedent_check.py's own rotation landed on a bucket where every
        # slug it picked was inapplicable to the repo, reported `0 passed`,
        # and CI's "refuse a run that checked nothing" backstop correctly
        # refused it -- on two real pull requests, in two different sets,
        # on commits with real passing coverage elsewhere in the catalogue
        # (_run_with_coverage_retry's own docstring has the full account).
        #
        # The shape here is different and safer: nine slugs are pinned in
        # every bucket, so the measured floor is 15 of 71 rather than
        # anything near zero, and a planted case has no SKIP path -- it
        # either asserts or fails loudly. But the floor is a PROPERTY of
        # today's pinned set, not a guarantee, and it would quietly weaken
        # the day nobody reads `planted[...]` back any more. So the empty
        # case is handled here instead of being left to arithmetic that
        # happens to hold.
        return set(all_slugs), ('all (the rotation slice came back empty -- '
                                'running everything rather than nothing)')
    return sel, (f'rotation bucket {bucket}/{HARNESS_ROTATION_BUCKETS}: '
                 f'{len(directly)} touched, {len(pinned & set(all_slugs))} pinned, '
                 f'{len(rot)} rotating')

def _registry_slugs():
    """-> sorted slugs precedent_check registers here. The selector
    needs the full set BEFORE the first case() runs, and the only
    authority on it is the registry itself -- the same module the
    untested-claim assertion at the end of this function loads, and
    for the same reason it calls register_materialized_checks()
    first: a source-supplied tools/checks/ script is not in CHECKS
    until it registers itself."""
    # `import importlib.util as _ilu`, NOT a bare
    # `importlib.util.…`: this function already contains a local
    # `import importlib.util` further down, which makes `importlib`
    # a local name for the WHOLE enclosing scope, so a reference up
    # here raises UnboundLocalError and the selector silently falls
    # back to running everything. Measured, not reasoned about --
    # the first run of this rotation reported "all (the registry
    # could not be read)" and took the full 81s.
    import importlib.util as _ilu
    try:
        _spec = _ilu.spec_from_file_location(
            '_pc_early', ROOT / 'tools' / 'precedent_check.py')
        _m = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_m)
        _m.register_materialized_checks()
        return sorted(_m.CHECKS)
    except Exception:                                 # noqa: BLE001
        return []      # -> selector runs everything, by _selected below




# --------------------------------------------------------------------------
# ONE SEED, COPIED: the vendored engine the update fixtures start from.
#
# Morgan, 2026-10-09: "share the fake project". The end-to-end Update Vendors
# checks each build small consumers from scratch, and each consumer used to
# run `precedent_vendor_engine.py seed`, a few seconds apiece, for bytes that
# are the same every time. Now the first fixture to seed with a given set of
# inputs keeps a copy of the files seed wrote, and every later one with the
# same inputs copies them in instead of running it. Each fixture still gets
# its own fresh files, its own git init and its own commit; nothing mutable
# is ever shared between checks.
#
# CONTRACT (practice: review-against-a-contract): a copy is used only when a
# fresh seed would write the same bytes -- the key moves whenever anything
# seed can read moves.
#
# The key hashes: this checkout's path, HEAD, the branch HEAD names and the
# SOURCE_BRANCH refs seed compares against; every uncommitted or untracked
# file in the checkout, by content (so an edited engine file, committed or
# not, is a new key); every file already in the destination, by path and
# content, and the destination's own refs; the kind; the Python running it;
# the contents of HOME and of the files _SEED_KEY_PATH_VARS name; and every
# other PRECEDENT_* and GIT_* variable in the environment it runs under. A
# seed that fails, removes a file, or writes the destination's own path into
# anything is never kept. Nothing is left out because seed "does not read
# it": an AGENTS.md that differs is a different key, a miss, never a guess.
#
# Concurrency: the harness runs as separate processes. An entry is built in
# a private directory and renamed into place; a process that loses the race
# drops its own copy and uses the winner's. A copy that fails part-way is
# undone and the seed simply runs. The cache is an accelerator, never a
# dependency (practice: shared-result-cache): PRECEDENT_NO_SEED_CACHE=1
# turns it off, and any error falls back to a real seed.
_SEED_CACHE_FORMAT = 1
_SEED_CACHE_KEEP_SECONDS = 6 * 3600
# Variables naming a file whose CONTENTS count, not its name: each harness
# process and fixture gives them a fresh temporary path.
_SEED_KEY_PATH_VARS = ('PRECEDENT_USER_CONFIG', 'PRECEDENT_CLONE_NOTES')


def _seed_cache_dir(env=None):
    """PRECEDENT_SEED_CACHE_DIR in `env` (or this process's environment)
    names another directory, for the check of the cache itself."""
    import tempfile
    named = (env or {}).get('PRECEDENT_SEED_CACHE_DIR') or os.environ.get(
        'PRECEDENT_SEED_CACHE_DIR')
    return (pathlib.Path(named) if named else
            pathlib.Path(tempfile.gettempdir()) / 'precedent-harness-seed-cache')


def _tree_digest(top, skip=('.git',), most=400):
    """sha256 over every file under `top` (path, mode, bytes), `skip`ped
    top-level names left out. Symlinks hash as their target string. More
    than `most` files raises ValueError: a key that would hash a whole home
    directory is not worth having, so the seed just runs."""
    h = hashlib.sha256()
    seen = 0
    top = pathlib.Path(top)
    if not top.exists():
        return 'absent'
    if top.is_file():
        return 'file ' + hashlib.sha256(top.read_bytes()).hexdigest()
    for dirpath, dirnames, filenames in os.walk(top):
        rel_dir = pathlib.Path(dirpath).relative_to(top)
        if rel_dir == pathlib.Path('.'):
            dirnames[:] = [d for d in dirnames if d not in skip]
        dirnames.sort()
        h.update(f'D {rel_dir.as_posix()}\n'.encode())
        for fn in sorted(filenames):
            seen += 1
            if seen > most:
                raise ValueError(f'more than {most} files under {top}')
            p = pathlib.Path(dirpath) / fn
            rel = (rel_dir / fn).as_posix()
            if p.is_symlink():
                h.update(f'L {rel} {os.readlink(p)}\n'.encode())
                continue
            st = p.stat()
            h.update(f'F {rel} {st.st_mode & 0o777} {st.st_size}\n'.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def _seed_cache_key(dest, kind, env, root=None):
    """-> the key described in the contract above, or None when it cannot
    be computed (then the seed simply runs)."""
    import precedent_vendor_engine as _pve
    dest = pathlib.Path(dest)
    root = ROOT if root is None else pathlib.Path(root)

    def git(where, *args):
        r = subprocess.run(['git', '--no-optional-locks', '-C', str(where), *args],
                           capture_output=True)
        return r.returncode, r.stdout

    h = hashlib.sha256()
    h.update(f'format {_SEED_CACHE_FORMAT}\nroot {root}\nkind {kind}\n'
             f'python {sys.executable} {sys.version}\n'.encode())
    branch = _pve.SOURCE_BRANCH
    for args in (('rev-parse', 'HEAD'), ('symbolic-ref', '-q', 'HEAD'),
                 ('rev-parse', '--verify', '-q', f'refs/remotes/origin/{branch}'),
                 ('rev-parse', '--verify', '-q', f'refs/heads/{branch}')):
        rc, out = git(root, *args)
        h.update(f'{" ".join(args)} -> {rc} '.encode() + out)
    rc, status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    if rc != 0:
        return None
    h.update(b'status ' + status)
    entries = status.split(b'\0')
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        if entry[:1] in (b'R', b'C'):
            i += 1                                  # the rename's source path
        p = root / os.fsdecode(entry[3:])
        h.update(b'dirty ' + entry[3:] + b' ' + _tree_digest(p).encode())
    h.update(b'dest ' + _tree_digest(dest).encode())
    for args in (('symbolic-ref', '-q', 'HEAD'), ('for-each-ref',)):
        rc, out = git(dest, *args)
        h.update(f'dest {" ".join(args)} -> {rc} '.encode() + out)
    for k in ('HOME',) + _SEED_KEY_PATH_VARS:
        where = env.get(k)
        h.update(f'{k} '.encode() + (_tree_digest(where).encode() if where else b'unset'))
    for k in sorted(env):
        if k.startswith(('PRECEDENT_', 'GIT_')) and k not in _SEED_KEY_PATH_VARS:
            h.update(f'env {k}={env[k]}\n'.encode())
    return h.hexdigest()


def _seed_cache_prune(cache):
    """Drop entries nobody has used for _SEED_CACHE_KEEP_SECONDS: a key
    names one checkout state, so an old one is never read again."""
    now = time.time()
    try:
        children = list(cache.iterdir())
    except OSError:
        return
    for child in children:
        try:
            if now - child.stat().st_mtime > _SEED_CACHE_KEEP_SECONDS:
                shutil.rmtree(child, ignore_errors=True)
        except OSError:
            pass


def _snapshot_files(top):
    """{relative path: (mode, sha256)} for every file under `top` but .git,
    and {relative path: ('dir',)} for every directory."""
    got = {}
    top = pathlib.Path(top)
    for dirpath, dirnames, filenames in os.walk(top):
        if pathlib.Path(dirpath) == top:
            dirnames[:] = [d for d in dirnames if d != '.git']
        for d in dirnames:
            got[(pathlib.Path(dirpath) / d).relative_to(top).as_posix()] = ('dir',)
        for fn in filenames:
            p = pathlib.Path(dirpath) / fn
            if p.is_symlink():
                got[p.relative_to(top).as_posix()] = ('link', os.readlink(p))
            else:
                got[p.relative_to(top).as_posix()] = (
                    p.stat().st_mode & 0o777,
                    hashlib.sha256(p.read_bytes()).hexdigest())
    return got


def _seed_fixture_engine(dest, kind, env, cwd):
    """`precedent_vendor_engine.py seed <dest> --kind <kind>`, run under
    `env` from `cwd` -- or the files an earlier seed with the same key wrote,
    copied into `dest`. Returns (returncode, output); a copy returns 0 and
    says so. Only for fixtures that use nothing of seed's but the files it
    writes (its output names the destination, so a copy cannot repeat it)."""
    dest = pathlib.Path(dest)

    def real_seed():
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
                            'seed', str(dest), '--kind', kind],
                           cwd=str(cwd), env=env, capture_output=True)
        return r.returncode, (r.stdout + r.stderr).decode(errors='replace')

    if env.get('PRECEDENT_NO_SEED_CACHE') == '1':     # every fixture env copies os.environ
        return real_seed()
    cache = _seed_cache_dir(env)
    try:
        key = _seed_cache_key(dest, kind, env)
    except (OSError, ValueError, subprocess.SubprocessError):
        key = None                          # an accelerator, never a dependency
    if key is None:
        return real_seed()
    entry = cache / key
    files = entry / 'files'
    if (entry / 'complete').is_file():
        made = []
        try:
            os.utime(entry)                 # in use: the prune leaves it
            for dirpath, dirnames, filenames in os.walk(files):
                dirnames.sort()
                rel_dir = pathlib.Path(dirpath).relative_to(files)
                for d in dirnames:
                    target = dest / rel_dir / d
                    if not target.is_dir():
                        target.mkdir()
                        made.append(target)
                for fn in sorted(filenames):
                    src, target = pathlib.Path(dirpath) / fn, dest / rel_dir / fn
                    if not target.exists():
                        made.append(target)
                    shutil.copy2(src, target)
            return 0, f'seed: copied from the harness seed cache ({key[:12]})'
        except OSError:
            for t in reversed(made):        # undo, then seed for real
                try:
                    t.rmdir() if t.is_dir() else t.unlink()
                except OSError:
                    pass
            return real_seed()
    before = _snapshot_files(dest)
    rc, out = real_seed()
    if rc != 0:
        return rc, out
    try:
        after = _snapshot_files(dest)
        if set(before) - set(after):
            return rc, out                  # it removed a file: a copy cannot say so
        wrote = sorted(rel for rel, v in after.items() if before.get(rel) != v)
        needle = os.fsencode(str(dest.resolve()))
        needle2 = os.fsencode(str(dest))
        if any(after[rel][0] == 'link' for rel in wrote):
            return rc, out                  # a symlink: copied files only
        for rel in wrote:
            p = dest / rel
            if after[rel] != ('dir',):
                data = p.read_bytes()
                if needle in data or needle2 in data:
                    return rc, out          # path-dependent: never kept
        cache.mkdir(parents=True, exist_ok=True)
        _seed_cache_prune(cache)
        import tempfile
        staging = pathlib.Path(tempfile.mkdtemp(prefix=f'.build-{key[:12]}-', dir=cache))
        try:
            (staging / 'files').mkdir()
            for rel in wrote:               # sorted: a directory before its files
                src, target = dest / rel, staging / 'files' / rel
                if after[rel] == ('dir',):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, target)
            (staging / 'complete').write_text(key + '\n', encoding='utf-8')
            os.rename(staging, entry)       # atomic; loses to an entry already there
        except OSError:
            pass
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
    except OSError:
        pass
    return rc, out


class _LocalEditsFixture:
    """Consumer-shaped fixtures for tools/precedent_local_edits.py, shared by
    the checks below (practice: fixture-owns-its-state): HOME, the user
    config and git identity are the fixture's own, so no private source of
    this container resolves into it.

    An "upstream change" is a commit object written into ROOT's object store
    on top of the commit a consumer was seeded from -- built with a scratch
    index, so no ref, index or file of ROOT moves -- and handed to
    precedent_update.py as --from-ref."""

    def __init__(self, prefix):
        import tempfile
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
        (self.tmp / 'home').mkdir()
        self.env = {**os.environ, 'HOME': str(self.tmp / 'home'),
                    'PRECEDENT_USER_CONFIG': str(self.tmp / 'no-user-config.json'),
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
        self.env.pop('CLAUDE_CODE_REMOTE_SESSION_ID', None)
        self.env.pop('PRECEDENT_LEAK_BLOCKLIST', None)

    def sh(self, *argv, cwd, data=None):
        r = subprocess.run(list(argv), cwd=str(cwd), env=self.env,
                           capture_output=True, input=data)
        return r.returncode, (r.stdout + r.stderr).decode(errors='replace')

    def git(self, cwd, *argv):
        return self.sh('git', '-C', str(cwd), *argv, cwd=cwd)[1].strip()

    def consumer(self, name, precedent_extra=None):
        repo = self.tmp / name
        repo.mkdir()
        self.sh('git', 'init', '-q', '-b', 'main', cwd=repo)
        cfg = {'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
               'sources': [{'level': 'universal', 'name': 'precedent',
                            'path': str(ROOT)}]}
        cfg.update(precedent_extra or {})
        (repo / 'precedent.json').write_text(json.dumps(cfg) + '\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')
        _seed_fixture_engine(repo, 'consumer', self.env, cwd=repo)
        self.sh('git', 'add', '-A', cwd=repo)
        self.sh('git', 'commit', '-qm', 'installed', cwd=repo)
        bare = self.tmp / f'{name}.git'
        self.sh('git', 'clone', '-q', '--bare', str(repo), str(bare), cwd=self.tmp)
        self.sh('git', 'remote', 'add', 'origin', str(bare), cwd=repo)
        self.sh('git', 'fetch', '-q', 'origin', cwd=repo)
        return repo

    def seeded_from(self, repo):
        return json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json')
                          .read_text(encoding='utf-8'))['source_commit']

    def upstream(self, base, changes):
        """-> a commit on top of `base` whose files `changes` replaces."""
        idx = self.tmp / 'scratch-index'
        e = {**self.env, 'GIT_INDEX_FILE': str(idx)}
        run = lambda *a, data=None: subprocess.run(
            ['git', '-C', str(ROOT), *a], env=e, capture_output=True, input=data)
        run('read-tree', base)
        for rel, data in changes.items():
            oid = run('hash-object', '-w', '--stdin', data=data).stdout.decode().strip()
            run('update-index', '--add', '--cacheinfo', f'100644,{oid},{rel}')
        tree = run('write-tree').stdout.decode().strip()
        idx.unlink()
        return run('commit-tree', tree, '-p', base, '-m',
                   'fixture upstream change').stdout.decode().strip()

    def update(self, repo, ref):
        return self.sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                       '--repo', str(repo), '--from-ref', ref, '--skip-check', cwd=repo)

    def commit(self, repo, message):
        self.sh('git', 'add', '-A', cwd=repo)
        self.sh('git', 'commit', '-qm', message, cwd=repo)
        return self.git(repo, 'log', '-1', '--format=%h')

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# ONE CONSUMER, COPIED: an Update Vendors fixture past its slow first steps.
#
# Several update checks start from the same consumer carried through the same
# warm-up (a vendored catalogue, a first update run, a commit), which costs
# 20-25 seconds of real update runs each time and gives the same repository
# every time. _uv_cached_consumer builds it once per key and copies it, the
# repository and its bare origin, into each case; every case still gets its
# own copy, and nothing one case does reaches another.
#
# CONTRACT (practice: review-against-a-contract): a copy is used only when a
# fresh build would leave the same repository. The key is _seed_cache_key's
# for an empty destination -- this checkout's path, HEAD, its SOURCE_BRANCH
# refs and every uncommitted or untracked file by content (this harness
# included, so an edited recipe is a new key), the contents of HOME and the
# user config, every PRECEDENT_*/GIT_* variable but the harness's own test
# filter -- plus the recipe's name. A build that leaves anything in HOME, or
# writes the fixture's temporary path anywhere but the remote URLs and
# FETCH_HEAD a copy rewrites, is never kept. PRECEDENT_NO_SEED_CACHE=1 turns
# it off with the seed cache; any error falls back to building, and within
# one fixture a recipe is still built only once.
_UV_CONSUMER_FILTER_VARS = ('PRECEDENT_CHECK_ONLY', 'PRECEDENT_CHECK_SKIP')
_UV_CONSUMER_PATH_OK = ('.git/config', '.git/FETCH_HEAD', 'config')


def _uv_consumer_source(fx, recipe, build):
    """-> (repo, bare) holding fx.consumer() carried through build(repo):
    a cache entry's, or one built in fx.tmp (and kept when it may be)."""
    env = {k: v for k, v in fx.env.items() if k not in _UV_CONSUMER_FILTER_VARS}
    key = None
    if fx.env.get('PRECEDENT_NO_SEED_CACHE') != '1':
        probe = fx.tmp / f'.uv-key-{recipe}'
        probe.mkdir()
        try:
            key = _seed_cache_key(probe, f'uv-consumer {recipe}', env)
        except (OSError, ValueError, subprocess.SubprocessError):
            key = None                      # an accelerator, never a dependency
        finally:
            shutil.rmtree(probe, ignore_errors=True)
    cache = _seed_cache_dir(fx.env)
    entry = cache / f'uv-{key}' if key else None
    if entry is not None and (entry / 'complete').is_file():
        try:
            os.utime(entry)                 # in use: the prune leaves it
            return entry / 'repo', entry / 'bare'
        except OSError:
            pass
    name = f'.uv-build-{recipe}'
    repo = fx.consumer(name)
    bare = fx.tmp / f'{name}.git'
    build(repo)
    if entry is None or any((fx.tmp / 'home').iterdir()):
        return repo, bare
    needle = os.fsencode(str(fx.tmp))
    for top, ok in ((repo, _UV_CONSUMER_PATH_OK[:2]), (bare, _UV_CONSUMER_PATH_OK[2:])):
        for dirpath, dirnames, filenames in os.walk(top):
            rel_dir = pathlib.Path(dirpath).relative_to(top)
            if rel_dir.as_posix() in ('.git/objects', 'objects'):
                dirnames[:] = []            # compressed; the worktree is scanned
                continue
            for fn in filenames:
                p = pathlib.Path(dirpath) / fn
                rel = (rel_dir / fn).as_posix()
                if rel not in ok and not p.is_symlink() and needle in p.read_bytes():
                    return repo, bare       # path-dependent: never kept
    import tempfile
    try:
        cache.mkdir(parents=True, exist_ok=True)
        _seed_cache_prune(cache)
        staging = pathlib.Path(tempfile.mkdtemp(prefix=f'.build-uv-{key[:12]}-', dir=cache))
    except OSError:
        return repo, bare
    try:
        shutil.copytree(repo, staging / 'repo', symlinks=True)
        shutil.copytree(bare, staging / 'bare', symlinks=True)
        (staging / 'complete').write_text(key + '\n', encoding='utf-8')
        os.rename(staging, entry)           # atomic; loses to an entry already there
    except OSError:
        pass
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return repo, bare


def _uv_cached_consumer(fx, name, recipe, build):
    """-> fx.tmp/<name>: a copy of fx.consumer() carried through
    build(repo), with its own copy of the bare origin at fx.tmp/<name>.git
    (see ONE CONSUMER, COPIED above). `recipe` names what build does, and
    must change when what it does changes in a way the key cannot see."""
    built = fx.__dict__.setdefault('_uv_built', {})
    if recipe not in built:
        built[recipe] = _uv_consumer_source(fx, recipe, build)
    src_repo, src_bare = built[recipe]
    repo, bare = fx.tmp / name, fx.tmp / f'{name}.git'
    shutil.copytree(src_repo, repo, symlinks=True)
    shutil.copytree(src_bare, bare, symlinks=True)
    fx.sh('git', 'remote', 'set-url', 'origin', str(bare), cwd=repo)
    fx.sh('git', 'remote', 'set-url', 'origin', str(repo), cwd=bare)
    fx.sh('git', 'fetch', '-q', 'origin', cwd=repo)
    return repo


def _insert(data, text, at=3):
    lines = data.decode().splitlines(True)
    return ''.join(lines[:at] + [text] + lines[at:]).encode()


def _replace_line(data, text, at=3):
    lines = data.decode().splitlines(True)
    return ''.join(lines[:at] + [text] + lines[at + 1:]).encode()


# The LOCAL EDITS group rule 2 lands in since 2026-10-08.
PREFERRED_GROUP = "Upstream's version taken over what was left"


def _section(out, title):
    """The lines of the LOCAL EDITS group titled `title`, joined."""
    block = out.split('LOCAL EDITS', 1)[-1] if 'LOCAL EDITS' in out else ''
    got, keep = [], False
    for line in block.splitlines():
        if line.startswith('  ') and not line.startswith('    '):
            keep = line.strip().startswith(title)
            continue
        if keep and line.startswith('    - '):
            got.append(line.strip())
        elif keep and line.startswith('      '):     # an item's own lines
            got.append(line.strip())
        elif not line.startswith('    '):
            keep = False
    return '\n'.join(got)


def _workflow_step_block(text, name):
    """-> the lines of the step named `name` in a workflow's text, or []."""
    lines = text.splitlines()
    at = next((i for i, l in enumerate(lines)
               if re.match(r'\s*- name:\s*' + re.escape(name) + r'\s*$', l)), None)
    if at is None:
        return []
    ind = len(lines[at]) - len(lines[at].lstrip())
    out = [lines[at]]
    for l in lines[at + 1:]:
        if l.strip() and len(l) - len(l.lstrip()) <= ind:
            break
        out.append(l)
    return out


def _actions_if(expr, event, ref, base_ref, failed):
    """Evaluate a GitHub Actions `if:` expression of the shape the issue
    step uses (failure(), ==, !=, &&, ||, parentheses, quoted strings),
    for one run. Anything else in it raises, so a new shape is seen."""
    s = expr.replace('${{', '').replace('}}', '')
    s = s.replace('failure()', 'True' if failed else 'False')
    s = s.replace('success()', 'False' if failed else 'True')
    s = (s.replace('github.event_name', repr(event)).replace('github.base_ref', repr(base_ref))
         .replace('github.ref', repr(ref)))
    s = s.replace('&&', ' and ').replace('||', ' or ').replace("'", '"')
    if re.search(r'\b(?!and\b|or\b|not\b)[A-Za-z_][\w.]*\s*\(', s) or 'github.' in s:
        raise ValueError(f'an expression this does not read: {expr}')
    return bool(eval(s, {'__builtins__': {}}, {'True': True, 'False': False}))


def _addition_fixture_practice(slug, *, tier='on-demand', status='active',
                               to='null', adds='', extra='', gates='[]',
                               rule='Do the thing.', occasion='doing the fixture'):
    """A minimal practice file for the adds_to cases: `adds` is the slug it
    adds to ('' for none), `extra` any further frontmatter lines."""
    return ('---\nslug:        ' + slug + '\ntitle:       A fixture practice\n'
            f'tier:        {tier}\nseverity:    default\n'
            'applies_to:  ["**"]\n'
            f'occasion:    "{occasion}"\ngates:       {gates}\n'
            'index_clause: "fixture"\n' + extra + 'checked_by:  null\n'
            f'defines:     []\nstatus:      {status}\nin_force_at: {to}\n'
            'supersedes:  []\noverrides:   null\n'
            + (f'adds_to:     {adds}\n' if adds else '')
            + 'added:       "2026-10-09"\napproved_by: "Fixture, 2026-10-09"\n'
            f'---\n\n## Rule\n{rule}\n\n## Why\nBecause.\n\n## Story\n'
            'A dated incident.\n')


def _update_tools():
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_vendor_engine as pve
        import precedent_resolve as pr
    finally:
        sys.path.pop(0)
    return pu, pve, pr




# Every engine-property check that has NOT yet declared its paths. The list
# exists so those checks are VISIBLE rather than silently rotation-only, and
# it may only ever shrink: adding a name back means a check went dark again.
# Declaring paths for one is evidence work -- read what the check actually
# inspects -- so they are done as they are verified, not guessed in bulk
# (2026-09-22, when three of eighteen were declared).
ENGINE_CHECKS_WITHOUT_DECLARED_PATHS = {
    'access-probe-is-wired',
    'claude-only-surface-has-a-parallel',
    'declared-base-branch',
    'expires-is-honoured',
    'index-required-is-declared',
    'no-hardcoded-git-identity',
    'shipped-hook-carries-its-script',
    'shipped-template-carries-its-script',
    'todo-gotcha-stale-reference',
    'tracked-practice-files',
    'vendored-engine-file-refs-resolve',
    'vendored-import-refs-resolve',
    'vocabulary-reaches-the-consumer',
    'wired-hooks-can-reach-a-consumer',
    'workflow-yaml-github-can-parse',
}




_CONFLICT_MARKER = re.compile(r'^(?:' + '<' * 7 + '|' + '>' * 7 + r')(?: |$)', re.M)


def _source_kind_engine_files():
    """-> (str, ...) the engine files precedent_vendor_engine.py vendors into
    a SOURCE set, plus routing_scope.json, which travels trimmed rather than
    by name in that list.

    READ FROM THE ENGINE, NOT RESTATED (practice: fixture-owns-its-state --
    the state a fixture owns includes which files a real source set gets;
    same reasoning as _consumer_engine_into above, which reads
    CONSUMER_ENGINE_FILES for exactly this reason). This was a hand-typed
    tuple until 2026-09-13, when precedent_source_bootstrap.py was promoted
    into ENGINE_FILES and the tuple went stale in the same commit -- the
    drift the comment ten lines above _consumer_engine_into warns about,
    repeated in the file that carries the warning."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    return tuple(_pve.ENGINE_FILES) + ('routing_scope.json',)


def _changed_files_fixture(tmp, base_files=None):
    """-> (repo, run) for precedent_push_check.changed_files_check against a
    consumer-shaped repo at `tmp`, run in-process: the script's own main()
    always judges the checkout it lives in, never the fixture.
    `base_files` ({path: text}) are in the base commit, so not part of the
    change."""
    import contextlib, io
    repo = tmp / 'repo'
    repo.mkdir(parents=True)
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def git(*a):
        return subprocess.run(['git', '-C', str(repo), '-c',
                               'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env)
    git('init', '-q', '-b', 'main')
    (repo / 'README.md').write_text('fixture\n', encoding='utf-8')
    for rel, text in (base_files or {}).items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding='utf-8')
    git('add', '-A'); git('commit', '-qm', 'base')
    since = git('rev-parse', 'HEAD').stdout.strip()
    spec = importlib.util.spec_from_file_location(
        'ppc_fixture', ROOT / 'tools' / 'precedent_push_check.py')
    ppc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppc)

    def commit(files):
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding='utf-8')
        git('add', '-A'); git('commit', '-qm', 'fixture change')

    def run():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ppc.changed_files_check(repo, since)
        return rc, buf.getvalue()
    return commit, run


_FIXTURE_CHECK_HEAD = (
    'import os, pathlib\n'
    'SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent\n'
    'ROOT = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT") or SOURCE_ROOT)\n')




# ---------------------------------------------------------------------------
# --for-change REF: THE HARNESS TESTS A CHANGE CAN REACH (2026-10-11,
# spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md). a243d9c0 made
# practice-file-shape require four sections; the harness test that feeds it
# a well-formed sample still had one, and staging went red. That test fails
# in about two seconds, but a push to a working branch or to staging never
# ran it: the changed-files step ran a check script's test_x.sh, never the
# harness tests of a check inside precedent_check.py. This works out which
# tests a change since REF reaches -- through precedent_check.py's checks
# and the helpers, constants and imports they use, the tools/ modules they
# import, the check scripts, and the harness's own tests and helpers -- and
# runs what fits a time budget, naming the rest. precedent_push_check.py's
# changed-files step calls it.
import ast  # noqa: E402
FOR_CHANGE_BUDGET_SECONDS = 60
# Set by a harness run that is not --for-change, so every fixture it starts
# plans without the live reach ledger (for_change_plan): a fixture is a
# worktree of this repository, shares its refs, and would otherwise run
# whatever the ledger fetched from origin picks -- main went red on
# check_changed_files_only_judges_the_change that way (2026-10-14, run
# 38607892096). A real push check never has it set.
FOR_CHANGE_LEDGER_OFF_ENV = 'PRECEDENT_FOR_CHANGE_LEDGER_OFF'
# The planted suite: one 13-minute test that cannot run one slug alone yet
# (the 18 slugs _deep_assertion_slugs pins run together). A check whose only
# harness coverage is its case there gets a note, not a run.
_PLANTED_SUITE = 'check_precedent_check_fires'
_PC_ALIASES_RE = re.compile(r'import precedent_check as (\w+)')
_IMPORT_RE = re.compile(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w., ]+?)(?:\s+as\s+\w+)?\s*$)',
                        re.M)


def _bound_names(stmt):
    """-> the top-level names `stmt` binds: a def or class, an assignment's
    targets, an import's names; an if/try/with block's own statements, never
    the inside of a function it defines."""
    names = set()
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(stmt.name)
    elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        for t in (stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]):
            names |= {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
    elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
        names |= {(a.asname or a.name).split('.')[0] for a in stmt.names}
    else:
        for field in ('body', 'orelse', 'finalbody', 'handlers'):
            for sub in getattr(stmt, field, None) or []:
                names |= _bound_names(sub)
    return names


def _source_units(text):
    """-> [unit] for each top-level statement of a Python source, or None
    when it does not parse. A unit is a dict: `first`/`last` lines (a
    decorated def starts at its first decorator), `names` it binds, `refs`
    (every name it reads, plus every module it imports, at any depth),
    `strings` (its string constants, its docstring left out), `attrs`
    ((base, attr) pairs), `slug` (a @check's), `node`."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    units = []
    for node in tree.body:
        decorators = getattr(node, 'decorator_list', [])
        first = min([node.lineno] + [d.lineno for d in decorators])
        refs, strings, attrs = set(), set(), set()
        doc = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and node.body and isinstance(node.body[0], ast.Expr) \
                and isinstance(node.body[0].value, ast.Constant):
            doc = node.body[0].value
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                refs.add(n.id)
            elif isinstance(n, ast.Import):
                refs |= {a.name.split('.')[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module:
                refs.add(n.module.split('.')[0])
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                attrs.add((n.value.id, n.attr))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and n is not doc:
                strings.add(n.value)
        slug = None
        for d in decorators:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) \
                    and d.func.id == 'check' and d.args \
                    and isinstance(d.args[0], ast.Constant):
                slug = d.args[0].value
        is_doc = isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        units.append({'first': first, 'last': node.end_lineno,
                      'names': _bound_names(node), 'refs': refs,
                      'strings': strings, 'attrs': attrs, 'slug': slug,
                      'node': node, 'is_doc': is_doc})
    return units


def _reach(units, seeds):
    """-> {unit index: depth} for every unit that reads a name in `seeds`
    ({name: depth}), at any remove: a unit is one deeper than the nearest
    name it reads, and the names it binds take its depth -- so a check that
    calls a changed helper is depth 1, and one that calls a helper of that
    helper is depth 2."""
    names, depth = dict(seeds), {}
    grew = True
    while grew:
        grew = False
        for i, u in enumerate(units):
            near = [names[n] for n in u['refs'] if n in names]
            if not near:
                continue
            d = min(near) + 1
            if d < depth.get(i, float('inf')):
                depth[i] = d
                grew = True
                for n in u['names']:
                    if d < names.get(n, float('inf')):
                        names[n] = d
    return depth


def _changed_new_lines(root, since, rel):
    """-> the lines of HEAD's `rel` the change since `since` touched; a pure
    deletion counts the lines either side of it. None when git cannot say."""
    r = subprocess.run(['git', '-C', str(root), 'diff', '-U0', '--no-color',
                        f'{since}...HEAD', '--', rel],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    lines = set()
    for m in re.finditer(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', r.stdout, re.M):
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        lines |= {start, start + 1} if count == 0 else set(range(start, start + count))
    return lines


def _units_at(units, lines):
    """-> (the units `lines` fall in, the lines that fall in none)."""
    hit, loose = [], set()
    for ln in sorted(lines):
        u = next((u for u in units if u['first'] <= ln <= u['last']), None)
        if u is None:
            loose.add(ln)
        elif u not in hit:
            hit.append(u)
    return hit, loose


def _importers(root, modules):
    """-> {module: depth} for `modules` (depth 0) and every tools/ module that
    imports one of them, at any remove (1 for a direct importer) -- read as
    text, every import line, a lazy one inside a function included."""
    graph = {}
    for f in sorted((root / 'tools').glob('*.py')):
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        imported = set()
        for m in _IMPORT_RE.finditer(text):
            if m.group(1):
                imported.add(m.group(1).split('.')[0])
            else:
                imported |= {p.strip().split()[0].split('.')[0]
                             for p in m.group(2).split(',') if p.strip()}
        graph[f.stem] = imported
    depth = {m: 0 for m in modules}
    frontier, d = set(modules), 0
    while frontier:
        d += 1
        frontier = {mod for mod, imported in graph.items()
                    if mod not in depth and imported & frontier}
        depth.update({mod: d for mod in frontier})
    return depth


def _span_text(lines):
    """-> '12-14, 30' for a set of line numbers."""
    out, run = [], []
    for ln in sorted(lines):
        if run and ln != run[-1] + 1:
            out.append(run)
            run = []
        run.append(ln)
    if run:
        out.append(run)
    return ', '.join(f'{r[0]}-{r[-1]}' if len(r) > 1 else str(r[0]) for r in out)


def for_change_plan(root, since, budget=FOR_CHANGE_BUDGET_SECONDS, ledger=None):
    """-> {'run': [test], 'deferred': [test], 'slugs': [slug],
    'planted_only': [slug], 'unmapped': [note], 'seconds': float} for the
    change since `since` in the repository at `root`: which harness tests it
    reaches, which of them fit `budget` seconds by their recorded times
    (nearest the change first -- what it touched, then what calls that --
    and the quickest first among equals), and what it could not reach.
    `ledger` is harness_reach's record of what each test ran; None reads
    this repository's own, and only when `root` is this repository.
    Reads; runs nothing."""
    root = pathlib.Path(root)
    plan = {'run': [], 'deferred': [], 'slugs': [], 'planted_only': [],
            'unmapped': [], 'seconds': 0.0}
    r = subprocess.run(['git', '-C', str(root), 'diff', '--name-only',
                        '--diff-filter=AMRD', f'{since}...HEAD'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        plan['unmapped'].append(f'git could not diff {since}...HEAD -- '
                                f'{(r.stderr or "").strip()[:200]}')
        return plan
    files = [l for l in r.stdout.splitlines() if l.strip()]
    py = [f for f in files if f.endswith('.py')
          and (f.startswith('tools/') or f.startswith('local/tools/'))]
    if not py:
        return plan
    pc_rel, vh_rel = 'tools/precedent_check.py', 'tools/verify_harness.py'
    vh_text = (root / vh_rel).read_text(encoding='utf-8', errors='replace') \
        if (root / vh_rel).is_file() else ''
    vh_units = _source_units(vh_text) if vh_text else []
    if vh_units is None:
        plan['unmapped'].append(f'{vh_rel} does not parse')
        return plan
    vh_defs = [u for u in vh_units if isinstance(u['node'], ast.FunctionDef)]
    tests = {u['node'].name: u for u in vh_defs
             if u['node'].name.startswith('check_')}
    aliases = set(_PC_ALIASES_RE.findall(vh_text)) | {'precedent_check'}

    # Each test's reach: its own body and every harness function it calls,
    # at any depth -- a test that runs a check through a helper still
    # tests it. Module-level tables are left out: a slug named only in a
    # data table is not a test of it.
    by_name = {u['node'].name: u for u in vh_defs}

    def closure(name):
        seen, todo = set(), [name]
        while todo:
            n = todo.pop()
            if n in seen or n not in by_name:
                continue
            seen.add(n)
            todo.extend(by_name[n]['refs'] & by_name.keys())
        return [by_name[n] for n in seen]
    reach = {t: closure(t) for t in tests}
    strings = {t: set().union(*(u['strings'] for u in us)) for t, us in reach.items()}
    attrs = {t: set().union(*(u['attrs'] for u in us)) for t, us in reach.items()}
    refs = {t: set().union(*(u['refs'] for u in us)) for t, us in reach.items()}

    rank = {}                       # test -> how far it sits from the change

    def want(r, names):
        for n in names:
            if n in tests and r < rank.get(n, float('inf')):
                rank[n] = r

    # 1. precedent_check.py, and the tools/ modules its checks import.
    pc_units = []
    if (root / pc_rel).is_file():
        pc_units = _source_units((root / pc_rel).read_text(
            encoding='utf-8', errors='replace'))
        if pc_units is None:
            plan['unmapped'].append(f'{pc_rel} does not parse')
            pc_units = []
    touched_pc, seeds = [], {}
    if pc_rel in py and pc_units:
        lines = _changed_new_lines(root, since, pc_rel)
        if lines is None:
            plan['unmapped'].append(f'git could not say which lines of {pc_rel} changed')
        else:
            # Lines that fall between definitions are comments and blank
            # lines: they reach nothing.
            touched_pc, _loose = _units_at(pc_units, lines)
            for u in touched_pc:
                seeds.update({n: 0 for n in u['names']})
                if not u['names'] and not u['slug'] and not u['is_doc']:
                    plan['unmapped'].append(
                        f'{pc_rel} lines {u["first"]}-{u["last"]} bind no '
                        f'name a check reads')
    modules = {pathlib.Path(f).stem for f in py if f.startswith('tools/')
               and f.count('/') == 1 and f not in (pc_rel, vh_rel)}
    if modules:
        for mod, d in _importers(root, modules).items():
            seeds[mod] = min(d, seeds.get(mod, d))
    depth = {i: 0 for i, u in enumerate(pc_units) if u in touched_pc}
    for i, d in _reach(pc_units, seeds).items():
        depth[i] = min(d, depth.get(i, d))
    order = sorted((d, i) for i, d in depth.items() if pc_units[i]['slug'])
    for d, i in order:
        u = pc_units[i]
        if u['slug'] in plan['slugs']:
            continue
        plan['slugs'].append(u['slug'])
        impl = u['node'].name
        hits = [t for t in tests if t != _PLANTED_SUITE and (
            u['slug'] in strings[t]
            or any((a, impl) in attrs[t] for a in aliases))]
        if hits:
            want(d, hits)
        else:
            plan['planted_only'].append(u['slug'])
    # A changed helper the harness calls directly (pc.main, pc._run, ...).
    for u in touched_pc:
        want(0, [t for t in tests if t != _PLANTED_SUITE and any(
            (a, n) in attrs[t] for a in aliases for n in u['names'])])

    # 2. A check script, by its file name in a test's code.
    for f in py:
        name = pathlib.Path(f).name
        if not re.match(r'check_\w+\.py$', name):
            continue
        want(0, [t for t in tests if t != _PLANTED_SUITE and (
            any(name in s for s in strings[t]) or name[:-3] in refs[t])])

    # 2b. A changed tools/ module a test imports or runs itself, at any
    # depth of the harness helpers it calls (2026-10-20). 1 reached a module
    # only through a check that imports it: a change to
    # precedent_sync_views.py picked no test at all, and one to
    # precedent_resolve.py missed six tests that import it -- 44 passed when
    # run by hand. The module itself only: a test that runs one of its
    # importers in a child process is the reach ledger's to find (4), and
    # following importers here picked some 600 tests for precedent_resolve.
    for mod in sorted(modules):
        ran = re.compile(r'(?<![\w.])' + re.escape(mod) + r'\.py\b')
        want(0, [t for t in tests if t != _PLANTED_SUITE and (
            mod in refs[t]
            or any(s == mod or ran.search(s) for s in strings[t]))])

    # 3. The harness itself: a changed test runs; a changed helper runs the
    # tests that reach it; a call added to main() runs what it calls.
    if vh_rel in py:
        lines = _changed_new_lines(root, since, vh_rel)
        if lines is None:
            plan['unmapped'].append(f'git could not say which lines of {vh_rel} changed')
        else:
            hit, _loose = _units_at(vh_units, lines)
            for u in hit:
                node = u['node']
                if isinstance(node, ast.FunctionDef) and node.name == 'main':
                    want(0, [c.func.id for c in ast.walk(node)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                             and c.func.id.startswith('check_')
                             and c.lineno in lines])
                elif isinstance(node, ast.FunctionDef) and node.name in tests:
                    want(0, [node.name])
                elif u['names']:
                    want(1, [t for t in tests if refs[t] & u['names']])

    # 4. What GitHub's scoped run picks: harness_reach's ledger of what each
    # test actually ran. A test that runs the change in a child process
    # names none of its functions, so 1-3 never see it: main went red on
    # check_vendor_engine_wires_a_new_hook_into_an_installed_repo
    # (2026-10-14, run 38570778970) after this plan, even at --budget 1500,
    # left it out. Reached through what it read or ran: one remove from the
    # change. Picked only because its reach was never fully seen, or because
    # it is newer than the ledger: two.
    if ledger is None and root.resolve() == ROOT.resolve() \
            and os.environ.get(FOR_CHANGE_LEDGER_OFF_ENV) != '1':
        import harness_reach
        ledger = harness_reach.load_ledger(fetch=True)
    if ledger and ledger.get('green') is not False:
        import harness_reach
        mb = subprocess.run(['git', '-C', str(root), 'merge-base', since, 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
        seen = dict(ledger, checks={n: {k: v for k, v in r.items() if k != 'o'}
                                    for n, r in ledger.get('checks', {}).items()})
        names = [t for t in tests if t != _PLANTED_SUITE]
        near, _r, full = harness_reach.select(seen, mb or since, 'HEAD', names, root)
        if full:
            plan['unmapped'].append(f'the reach ledger: {full} -- GitHub\'s '
                                    f'run on main runs the whole suite')
        else:
            rec = ledger.get('checks', {})
            want(1, sorted(near))
            want(2, [t for t in names if t not in rec or rec[t].get('o')])
    times, default = _check_times(root / 'tools' / 'harness_check_times.json')
    cost = lambda t: times.get(t, default if default is not None else 1.0)
    total = 0.0
    for t in sorted(rank, key=lambda t: (rank[t], cost(t), t)):
        if total + cost(t) <= budget:
            plan['run'].append(t)
            total += cost(t)
        else:
            plan['deferred'].append(t)
    plan['seconds'] = round(total, 1)
    return plan


def run_for_change(since, budget=FOR_CHANGE_BUDGET_SECONDS, dry_run=False,
                   root=None):
    """--for-change REF: say what the change reaches, run what fits the
    budget in one filtered harness run, and name the rest with the command
    that runs them. -> the run's exit code (0 when nothing ran). A note is
    never a failure: only a test that runs and fails is."""
    root = pathlib.Path(root or ROOT)
    plan = for_change_plan(root, since, budget)
    say = lambda s: print(f'for-change: {s}', flush=True)
    if plan['slugs']:
        say(f'the change reaches {len(plan["slugs"])} check(s): '
            + ', '.join(plan['slugs']))
    for note in plan['unmapped']:
        say(f'could not map: {note} -- the full tier covers it: '
            f"python3 tools/verify_harness.py --as-ci --because '<why>'")
    if plan['planted_only']:
        say(f'NOT RUN HERE: {len(plan["planted_only"])} check(s) are tested '
            f'only by their planted case in {_PLANTED_SUITE}, which runs at the '
            f'full tier (about 13 minutes, every case): '
            + ', '.join(plan['planted_only']))
    if plan['deferred']:
        say(f'NOT RUN HERE: {len(plan["deferred"])} test(s) over the '
            f'{budget:.0f}-second budget; the full tier runs them, or run them '
            f'now: PRECEDENT_CHECK_ONLY={",".join(plan["deferred"])} '
            f'python3 tools/verify_harness.py')
    if not plan['run']:
        say('no harness test to run for this change')
        return 0
    say(f'running {len(plan["run"])} test(s), about {plan["seconds"]:.0f} s by '
        f'their recorded times: ' + ', '.join(plan['run']))
    if dry_run:
        return 0
    r = subprocess.run([sys.executable, str(root / 'tools' / 'verify_harness.py')],
                       cwd=root, capture_output=True, text=True,
                       env=dict(os.environ, PRECEDENT_CHECK_ONLY=','.join(plan['run'])))
    said = [l for l in r.stdout.splitlines()
            if l.startswith(('PASS', 'FAIL', 'verify_harness'))]
    for line in said:
        print(line)
    if r.returncode != 0 and not any(l.startswith('FAIL') for l in said):
        # It stopped before a test could say FAIL: show why.
        tail = [l for l in (r.stdout + r.stderr).splitlines()
                if 'SKIP (filtered out' not in l and not re.match(r'\s+[\d.]+s\s', l)]
        for line in tail[-5:]:
            print(line)
    return r.returncode


def _gh_if(expr, event_name, private, head_ref=''):
    """Evaluate a GitHub Actions job `if:` the way GitHub does, for the few
    operators the light check uses (&&, ||, !, ==, !=, startsWith, contains,
    true),
    against one event. Strict on purpose: anything else in the expression
    raises, so a template edit this cannot read fails loudly, never reads as
    "skips"."""
    import types
    e = expr.replace('!=', ' __NE__ ').replace('==', ' __EQ__ ')
    e = e.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ')
    e = e.replace('__NE__', '!=').replace('__EQ__', '==')
    e = re.sub(r'\btrue\b', 'True', re.sub(r'\bfalse\b', 'False', e))
    left = re.sub(r"'[^']*'", '', e)
    names = set(re.findall(r'[A-Za-z_][\w.]*', left)) - {
        'and', 'or', 'not', 'True', 'False', 'startsWith', 'contains',
        'github.event_name',
        'github.head_ref', 'github.event.repository.private'}
    if names:
        raise ValueError(f'the job if: uses {sorted(names)}, which this evaluator does not model')
    ns = types.SimpleNamespace
    github = ns(event_name=event_name, head_ref=head_ref,
                event=ns(repository=ns(private=private)))
    return bool(eval(e, {'__builtins__': {}}, {
        'github': github,
        'startsWith': lambda a, b: str(a or '').lower().startswith(str(b).lower()),
        'contains': lambda a, b: str(b).lower() in str(a or '').lower()}))


def _write_generator_fixture(work):
    """A stand-in generator under a name the engine rebuilds bare
    (precedent_branches.REBUILT_BARE): OUT.md from src.txt, with a sum line
    so that two sides' rebuilds always conflict rather than merging."""
    (work / 'tools' / 'build_todo_index.py').write_text(
        'import pathlib, hashlib\nsrc = pathlib.Path("src.txt").read_text()\n'
        'pathlib.Path("OUT.md").write_text('
        '"---\\ngenerated_by: tools/build_todo_index.py\\n---\\nsum: "'
        ' + hashlib.md5(src.encode()).hexdigest() + "\\n" + src.upper())\n',
        encoding='utf-8')
    if not (work / 'src.txt').exists():
        (work / 'src.txt').write_text('a\nb\nc\n', encoding='utf-8')




_CODEX_HOOK_EVENTS = ('PreToolUse', 'PermissionRequest', 'PostToolUse',
                      'PreCompact', 'PostCompact', 'SessionStart', 'SessionEnd',
                      'UserPromptSubmit', 'SubagentStart', 'SubagentStop',
                      'Stop', 'Interrupt')


class _KeptDivergenceFixture:
    """Shared by the three kept-divergence checks below: a scratch consumer
    that precedent_update.py can take a whole update into, and synthetic
    upstream commits on top of this working tree that change one template
    file -- objects only, no ref, nothing checked out, as the bootstrap.sh
    fixture above builds them.

    Owns its state (practice: fixture-owns-its-state): HOME and the user
    config are isolated, as check_update_vendors_is_one_command's are, and
    precedent.json names its landing branch so no step asks. The consumer's
    AGENTS.md is the loader template exactly as install instantiates it and
    its bootstrap.sh is the template, so the only difference an update can
    find is the one a case plants -- which the CONTROL run asserts."""

    AGENTS_SRC = 'templates/AGENTS.md.loader.template'
    BOOT_SRC = 'templates/bootstrap.sh'

    def __init__(self, prefix):
        import tempfile
        import precedent_vendor_engine as pve
        self.pve = pve
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
        (self.tmp / 'home').mkdir()
        self.env = {**os.environ, 'HOME': str(self.tmp / 'home'),
                    'PRECEDENT_USER_CONFIG': str(self.tmp / 'no-user-config.json'),
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
        self.base = _ref_including_worktree(ROOT)

    def sh(self, *argv, cwd):
        r = subprocess.run(list(argv), cwd=str(cwd), env=self.env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def template(self, src):
        return subprocess.run(['git', '-C', str(ROOT), 'show', f'{self.base}:{src}'],
                              capture_output=True, check=True).stdout

    def upstream_with(self, src, data):
        """A commit on top of this tree whose only change is `src` := data."""
        import tempfile
        with tempfile.TemporaryDirectory(prefix='precedent-fixture-index-') as idx:
            env = dict(os.environ, GIT_INDEX_FILE=str(pathlib.Path(idx) / 'index'),
                       GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                       GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')

            def git(*args, data=None):
                return subprocess.run(['git', '-C', str(ROOT), *args], input=data,
                                      capture_output=True, env=env, check=True
                                      ).stdout.decode().strip()
            git('read-tree', self.base)
            mode = git('ls-tree', self.base, '--', src).split()[0]
            blob = git('hash-object', '-w', '--stdin', data=data)
            git('update-index', '--cacheinfo', f'{mode},{blob},{src}')
            return git('commit-tree', git('write-tree'), '-p', self.base, '-m',
                       'verify_harness: kept-divergence fixture (never pushed)')

    def consumer(self, name, agents=None, boot=None):
        repo = self.tmp / name
        repo.mkdir()
        self.sh('git', 'init', '-q', '-b', 'main', cwd=repo)
        self.write_config(repo, {
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'landing_branch': 'staging',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(ROOT)}]})
        if agents is None:
            agents = self.pve._instantiate(self.template(self.AGENTS_SRC).decode(),
                                           self.pve._agents_md_subs(repo))
        (repo / 'AGENTS.md').write_text(agents, encoding='utf-8')
        _seed_fixture_engine(repo, 'consumer', self.env, cwd=repo)
        (repo / 'tools' / 'bootstrap.sh').write_bytes(
            self.template(self.BOOT_SRC) if boot is None else boot)
        self.sh('git', 'add', '-A', cwd=repo)
        self.sh('git', 'commit', '-qm', 'installed', cwd=repo)
        self.sh('git', 'clone', '-q', '--bare', str(repo), str(self.tmp / f'{name}.git'),
                cwd=self.tmp)
        self.sh('git', 'remote', 'add', 'origin', str(self.tmp / f'{name}.git'), cwd=repo)
        self.sh('git', 'fetch', '-q', 'origin', cwd=repo)
        return repo

    @staticmethod
    def write_config(repo, cfg):
        (repo / 'precedent.json').write_text(json.dumps(cfg, indent=2) + '\n',
                                             encoding='utf-8')

    def keep(self, repo, item, reason, template_sha):
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        cfg.setdefault('kept_template_divergences', {})[item] = {
            'reason': reason, 'template_sha256': template_sha}
        self.write_config(repo, cfg)

    def judge(self, repo, item, titles, verdict='local-add-on'):
        """Record one block verdict per title (precedent_vendor_engine's ONE
        VERDICT PER BLOCK): since 2026-10-31 a reason and a pin alone no
        longer keep a section that lacks blocks. local-add-on points at an
        add-on practice the fixture writes, so the verdict holds."""
        addon = repo / 'local' / 'practices' / 'fixture-local-add-on.md'
        addon.parent.mkdir(parents=True, exist_ok=True)
        addon.write_text('---\nslug: fixture-local-add-on\n---\n## Rule\nLocal.\n',
                         encoding='utf-8')
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        blocks = cfg['kept_template_divergences'][item].setdefault('blocks', {})
        for t in titles:
            blocks[self.pve.block_id(t)] = {
                'verdict': verdict, 'practice': 'local/practices/fixture-local-add-on.md'}
        self.write_config(repo, cfg)

    def update(self, repo, ref=None):
        return self.sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                       '--repo', str(repo), '--from-ref', ref or self.base,
                       '--skip-check', cwd=repo)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def _renamed_universal_fixture(tmp):
    """A scratch consumer whose individual source cites a renamed universal
    practice -- the shape the go-merge -> go-update rename (2026-09-26)
    broke in every consumer. The universal source carries the live
    `go-update` and a deduplicated `go-merge` stub forwarding to it; the
    individual source carries its own `go-merge`, deduplicated against the
    universal one by the OLD name, and a practice citing `go-merge.md` both
    as a sibling and by a path into the universal clone. Returns the source
    list, lowest precedence first, and the consumer directory."""
    def write(path, slug, status='active', in_force_at=None, rule='x'):
        path.parent.mkdir(parents=True, exist_ok=True)
        ifa = f'in_force_at: {in_force_at}\n' if in_force_at else ''
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: []\noccasion: "x"\ngates: []\n'
            f'index_clause: "x"\nchecked_by: null\ndefines: []\n'
            f'status: {status}\n{ifa}supersedes: []\noverrides: null\n'
            f'added: 2026-09-26\napproved_by: "harness, 2026-09-26"\n---\n'
            f'## Rule\n{rule}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')
    uni, ind, consumer = tmp / 'uni', tmp / 'ind', tmp / 'consumer'
    write(uni / 'practices' / 'go-update.md', 'go-update')
    write(uni / 'practices' / 'go-merge.md', 'go-merge', 'deduplicated', 'go-update')
    write(ind / 'practices' / 'go-merge.md', 'go-merge', 'deduplicated', 'go-merge')
    write(ind / 'practices' / 'cites.md', 'cites',
          rule='Sibling: [go-merge](go-merge.md#rule). '
               'Path: [stub](../../uni/practices/go-merge.md).')
    consumer.mkdir()
    sources = [{'level': 'universal', 'name': 'precedent', 'path': str(uni)},
               {'level': 'individual', 'name': 'precedent-individual',
                'path': str(ind)}]
    return sources, consumer, write


def _fixture_git_env():
    return dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
                GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
                GIT_CONFIG_GLOBAL=empty_gitconfig(), PRECEDENT_ALLOW_ANY_AUTHOR='1')


def _drop_session_load_total(reg_path):
    """Remove `session_load_tokens` from a fixture's copied registry, so a
    test of the per-part budgets sees them in force: a declared total turns
    them into measurements (build_views.TOTAL_KEY)."""
    try:
        data = json.loads(pathlib.Path(reg_path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    if isinstance(data, dict) and data.pop('session_load_tokens', None) is not None:
        pathlib.Path(reg_path).write_text(json.dumps(data, indent=2) + '\n',
                                          encoding='utf-8')




# The (event, hook) pairs HOOK_WIRING carried on 2026-10-07, when the
# dispatcher's fixed entries were added and the list closed. A hook added
# later goes in tools/hook_wiring.json.
HOOK_WIRING_FROZEN = {
    ('PostToolUse', 'merge-check-gate.sh'), ('PostToolUse', 'precedent-hooks.sh'),
    ('PreToolUse', 'artifact-publish-gate.sh'), ('PreToolUse', 'commit-identity-once.sh'),
    ('PreToolUse', 'doc-lint-gate.sh'), ('PreToolUse', 'freshness-guard.sh'),
    ('PreToolUse', 'merge-check-gate.sh'), ('PreToolUse', 'precedent-hooks.sh'),
    ('PreToolUse', 'precedent-paths.sh'), ('PreToolUse', 'push-check-gate.sh'),
    ('PreToolUse', 'seeded-prompt-gate.sh'), ('PreToolUse', 'wait-loop-gate.sh'),
    ('PreToolUse', 'workflow-write-gate.sh'), ('SessionStart', 'commit-identity.sh'),
    ('SessionStart', 'freshness-guard.sh'), ('SessionStart', 'precedent-hooks.sh'),
    ('SessionStart', 'precedent-universal-catalogue.sh'), ('SessionStart', 'session-start.sh'),
    ('Stop', 'precedent-hooks.sh'), ('Stop', 'stop-git-check.sh'),
    ('Stop', 'stop-reply-check.sh'), ('UserPromptSubmit', 'freshness-guard.sh'),
    ('UserPromptSubmit', 'precedent-hooks.sh'), ('UserPromptSubmit', 'reply-gate.sh'),
}


def _stale_ref_fixture_env(tmp):
    """The environment every throwaway repo in the stale-ref checks below
    runs git under: a fixed author, no global or system config, and no
    personal Precedent config, so nothing on the machine leaks in."""
    return dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t' + chr(64) + 'example.com',
                GIT_COMMITTER_NAME='T',
                GIT_COMMITTER_EMAIL='t' + chr(64) + 'example.com',
                GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
                PRECEDENT_USER_CONFIG=str(tmp / 'config.json'))


def _promote_fixture(tmp, env, base_branch, tiers):
    """-> (work, git, branches, tip): a throwaway repo with a bare origin
    carrying `tiers`, stub checks that always pass, and the real
    precedent_branches.py and precedent_push_check.py. Same shape as
    the ladder set's Promote tests' fixture."""
    import json as _json, shutil as _shutil

    def git(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a],
                              capture_output=True, text=True, env=env)

    bare = tmp / 'origin.git'
    git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
    work = tmp / 'work'
    (work / 'tools').mkdir(parents=True)
    git(tmp, 'init', '-q', '-b', 'main', str(work))
    for f in ('precedent_push_check.py', 'precedent_branches.py', 'precedent_time.py'):
        _shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
    (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
        _json.dumps({'kind': 'consumer'}), encoding='utf-8')
    for t in ('precedent_check', 'leak_gate', 'doc_lint'):
        (work / 'tools' / f'{t}.py').write_text(
            'import sys\n'
            + ('print("precedent_check: 3 passed, 0 violated")\n'
               if t == 'precedent_check' else '')
            + 'sys.exit(0)\n', encoding='utf-8')
    (work / 'precedent.json').write_text(
        _json.dumps({'base_branch': base_branch}), encoding='utf-8')
    (work / 'list.txt').write_text('a\n', encoding='utf-8')
    git(work, 'add', '-A')
    git(work, 'commit', '-q', '-m', 'init')
    git(work, 'remote', 'add', 'origin', f'file://{bare}')
    for b in tiers:
        git(work, 'push', '-q', 'origin', f'HEAD:refs/heads/{b}')

    def branches(*a):
        p = subprocess.run([sys.executable, 'tools/precedent_branches.py', *a],
                           cwd=work, capture_output=True, text=True, env=env)
        return p.returncode, p.stdout + p.stderr

    def tip(b):
        return git(work, 'ls-remote', 'origin',
                   f'refs/heads/{b}').stdout.split('\t')[0]
    return work, git, branches, tip


def _move_fixture_env(tmp):
    """The environment every move fixture below runs its tools in: no
    individual source, no hosted-session self-heal, the commit backstop
    waved, and a mention fix that reads only the fixture's own repositories
    (practice: fixture-owns-its-state)."""
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'),
               PRECEDENT_MOVE_MENTION_REPOS='')
    env.pop('CLAUDE_CODE_REMOTE', None)
    return env


_MOVE_SETS = {'team': 'precedent-team-fixture', 'individual': 'precedent-individual'}


def _move_fixture_practice(slug, story='A dated incident.', install=None):
    """A minimal practice file, optionally with an ## Install section."""
    return ('---\nslug:        ' + slug + '\n'
            'title:       A fixture practice\n'
            'tier:        on-demand\nseverity:    default\n'
            'applies_to:  ["fixture/**"]\noccasion:    "fixture"\n'
            'gates:       []\nindex_clause: "fixture"\nchecked_by:  null\n'
            'defines:     []\nstatus:      active\nin_force_at: null\n'
            'supersedes:  []\noverrides:   null\nadded:       "2026-09-14"\n'
            'approved_by: "Fixture, 2026-09-14"\n---\n\n## Rule\nDo the thing.\n\n'
            '## Why\nBecause.\n\n## Story\n' + story + '\n'
            + ('' if install is None else '\n## Install\n' + install + '\n'))


# practice: environment-gotchas -- the trap this guards is gotchas/gotcha-2026-09-13-pip-install-cmarkgfm-or-tools-doclint-py-s-strikethrough-che.md.
#
# Several checks below need a package that is not in the standard library:
# doc_lint's strikethrough case suite and the `doc-references-are-links`
# planted violation both need cmarkgfm, and the --help sweep runs
# tools/doc_html.py, which imports markdown. Without them those checks FAIL,
# and they fail describing what they were testing rather than what is
# missing -- on 2026-09-14 that read as "3 failed" on a tree whose diff was
# two markdown files, and cost two full re-runs to attribute. The packages
# are installed by .claude/hooks/session-start.sh and by both CI workflows;
# a session whose hooks never ran (gotchas/gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo.md) has neither.
DOC_PACKAGES = ('cmarkgfm', 'markdown')


def missing_doc_packages():
    """-> [name] for each DOC_PACKAGES entry this interpreter cannot import."""
    return [n for n in DOC_PACKAGES if importlib.util.find_spec(n) is None]


def _report_missing_doc_packages(where):
    missing = missing_doc_packages()
    if not missing:
        return missing
    print(f'verify_harness {where}: {", ".join(missing)} not installed. '
          f'Checks that need them FAIL for that reason alone, not because of '
          f'anything in the tree -- install with: pip install '
          f'{" ".join(missing)}  (gotchas/gotcha-2026-09-13-pip-install-cmarkgfm-or-tools-doclint-py-s-strikethrough-che.md)')
    print('  and run: python3 tools/precedent_session_check.py -- these '
          'packages are installed by the SessionStart hook, so missing ones '
          'usually mean NO hook ran, and the hooks guarantee more than this')
    return missing


def _print_checkout_banner():
    """Print which branch and commit this run is actually checking, before
    a single check runs.

    A run against an unexpectedly-reset checkout looks identical to a run
    against the intended one -- same PASS/FAIL shape, no error -- and
    nothing else in this tool's output says which tree it ran against.
    Found 2026-09-17: a session's local checkout silently reset to this
    repo's started branch between turns (a container/session-lifecycle
    behavior, not something this repo controls), and a full run against
    the wrong branch read as a clean pass on a change that was not
    actually on disk -- caught only by a separate, manual
    `git branch --show-current`.
    (practice: upstream-fix -- the checkout resetting is outside this
    repo's control; making a run against the wrong tree impossible to
    mistake for one against the right tree is not.)
    """
    b = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--abbrev-ref', 'HEAD'],
                       capture_output=True, text=True)
    h = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD'],
                       capture_output=True, text=True)
    if b.returncode != 0 or h.returncode != 0:
        print(f"verify_harness: could not determine {ROOT}'s branch/commit -- "
              f"results below are not attributable to a known tree.\n")
        return
    print(f"verify_harness: checking {ROOT} @ {b.stdout.strip()} ({h.stdout.strip()})\n")


def main():
    _install_retrying_tempdir_cleanup()
    _install_check_filter()
    _install_reach_recording()
    _install_fixture_error_guard()
    _install_check_timing()
    _print_checkout_banner()
    _report_missing_doc_packages('PREFLIGHT')
    if not PRACTICES_DIR.exists():
        sys.exit("verify_harness FAIL: practices/ does not exist -- run "
                 "tools/split_practices.py split first")
    files = load_practice_files()
    original_text = CATALOGUE.read_text(encoding='utf-8')
    original_practices = {p['number']: p for p in sp.parse_catalogue(original_text)}
    check_source_coverage(files, original_practices)
    check_titles_match_source(files, original_practices)
    check_reachability(files)
    check_no_invented_content(files, original_practices)
    check_no_lost_content(files, original_practices)
    check_content_preserved_by_sentence(files, original_practices)
    check_section_source_order(files, original_practices)
    check_list_structure_preserved(files, original_practices)
    check_corruption_drop_is_a_duplicate(original_practices)
    check_no_cross_practice_duplication(files, original_practices)
    check_citation_integrity(files)
    check_leak_gate_fires()
    check_practice_audit_fires()
    check_practice_audit_loader()
    check_practice_audit_declined()
    check_freshness_gate_fires()
    check_very_deep_check_registers_its_own_records()
    check_very_deep_check_reads_a_worktree_and_runs_the_suite_last()
    check_doc_lint_exempts_links_in_a_mirrored_tree()
    check_local_engine_edit_saves_a_prompt_please()
    check_repo_may_declare_its_own_fallback_zone()
    check_session_check_reports_a_dead_also_list_entry()
    check_freshness_guard_checks_attached_repositories()
    check_freshness_guard_user_prompt_never_resets_mid_session()
    check_freshness_guard_waves_through_a_branch_origin_never_saw()
    check_freshness_guard_lets_a_read_through_on_a_stale_branch()
    check_freshness_guard_never_tells_a_tier_branch_to_merge()
    check_freshness_guard_leaves_a_source_on_its_tier_when_opened_above()
    check_session_deepen_stays_narrow()
    check_stale_branches_lists_one_repository_once()
    check_branch_cleanup_button()
    check_update_notes_workflow_changes_in_readme_platform_section()
    check_set_bootstrap_defers_to_a_newer_engine_copy()
    check_sync_removes_a_stale_ship_named_only_as_another_repos()
    check_update_keeps_the_harness_go_ahead_with_its_content()
    check_wait_main_test_finds_a_merged_pull_requests_head()
    check_push_to_staging_runs_own_checks_inside_a_budget()
    check_push_check_refuses_a_deleted_test_that_keeps_its_time()
    check_failure_detail_puts_the_naming_line_first()
    check_push_check_refuses_an_added_raw_tail_report()
    check_branch_policy_seam_asks_a_set_and_keeps_the_engine_answer()
    check_promote_is_handed_to_the_moves_a_set_names()
    check_update_holds_a_settings_change_and_offers_it_again()
    check_deduplicated_copy_stays_in_force_until_its_target_arrives()
    check_set_refuses_its_own_stranded_deduplication()
    check_bootstrap_separates_an_unpushed_branch_from_a_failed_fetch()
    check_bootstrap_runs_every_tool_session_start_runs()
    check_codex_hooks_template_runs_the_claude_gates()
    check_gemini_settings_template_keeps_stdout_clean()
    check_unmerged_branch_verdicts()
    check_no_tool_defines_a_function_twice()
    check_branch_scan_sees_every_branch()
    check_freshness_guard_writes_no_origin_into_a_repo_without_one()
    check_branch_name_follows_the_convention()
    check_base_branch_drift_ignores_carried_work()
    check_very_deep_check_never_offers_a_tier_branch_for_deletion()
    check_very_deep_check_skips_the_board_branches()
    check_very_deep_check_walks_every_tier_pair()
    check_upstream_review_only_for_a_code_owner_on_the_ladder()
    check_merged_branches_carry_a_date_and_a_staleness_verdict()
    check_branch_report_writes_delete_links_to_a_committable_file()
    check_branch_sweep_sees_work_landed_on_the_base_branch()
    check_session_sweep_reports_the_repo_half()
    check_very_deep_check_authenticates_its_own_fetches()
    check_very_deep_check_bootstrap_drift()
    check_very_deep_check_convergent_drift()
    check_public_tree_bakes_in_no_owner_account()
    check_public_consumer_does_not_materialize_private_text()
    check_materialize_run_directly_refuses_what_the_sync_withholds()
    check_assumed_visibility_never_deletes_practices()
    check_access_probe_separates_refusal_from_silence()
    check_sync_refuses_to_write_from_incomplete_sources()
    check_unlanded_work_is_reported_before_the_passes()
    check_very_deep_check_records_its_components()
    check_shallow_clone_never_fabricates_unlanded_work()
    check_reply_gate_reports_only_this_sessions_flow()
    check_a_renamed_engine_file_never_survives_a_reseed()
    check_leak_gate_refuses_a_fresh_container()
    check_structural_only_actually_drops_the_private_half()
    check_title_case_knows_the_files_it_ships()
    check_carry_check_never_invents_lost_content()
    check_doc_currency_finds_a_stale_document()
    check_template_freshness_reads_the_skeleton_correctly()
    check_withdrawn_table_never_links_a_successor_it_does_not_have()
    check_summary_fields_drop_links_before_the_cut()
    check_source_precedence()
    check_cross_source_resident_budget()
    check_doc_lint_fires()
    check_doc_lint_strict_refuses_the_gate_scope()
    check_practice_heading_parsing()
    check_decision_records_not_inline()
    check_decision_records_not_inline_fires()
    check_catalogue_anchors()
    check_all_workflows_disclosed()
    check_example_set()
    check_build_views_refuses_a_long_index_clause()
    check_glob_semantics()
    check_symlinked_root_path_matching()
    check_generated_views_regenerate()
    check_map_reads_each_tools_own_summary()
    check_where_things_are_from_one_source()
    check_commit_rebuilds_generated_files()
    check_commit_rebuild_runs_outside_the_hook_git_env()
    check_migrate_views_keeps_every_word()
    check_update_seeds_the_session_load_registry()
    check_session_start_charges_brought_sets_to_the_person()
    check_update_drops_the_dead_blank_blocklist_link()
    check_sync_does_not_call_a_held_back_check_an_orphan()
    check_sync_carries_a_test_helper_with_its_test()
    check_update_runs_a_set_s_own_tests_after_an_engine_refresh()
    check_update_clears_the_refresh_branch_session_start_left()
    check_sync_says_which_copy_of_a_claimed_check_runs()
    check_no_duplication_refuses_a_sets_copy_of_a_universal_rule()
    check_source_directory_splits_and_assembles()
    check_split_file_round_trips()
    check_split_and_join_take_edits_made_where_they_belong()
    check_split_directories_pass_the_repos_own_checks()
    check_stale_view_names_its_real_cause()
    check_tracked_views_read_the_same_whoever_regenerates()
    check_stale_views_say_why_and_stop_at_the_push()
    check_stale_freshness_also_says_delete_it()
    check_build_views_summary_matches_what_it_wrote()
    check_resident_rule_links_are_placed_for_the_block()
    check_source_names_detects_a_rename()
    check_source_survey_gives_every_repository_a_verdict()
    check_steps_8_and_9_tools_ship_to_every_kind_of_repo()
    check_owned_paths_previews_the_boundary()
    check_boundary_check_never_passes_unread()
    check_very_deep_check_boundary_audit_reads_the_setting()
    check_very_deep_check_warnings_are_judged_not_just_counted()
    check_very_deep_check_test_worth_judges_what_changed()
    check_test_review_times_script_tests()
    check_very_deep_check_token_budgets_are_shown_and_fire_tested()
    check_very_deep_check_lists_the_longest_rules()
    check_very_deep_check_record_pass_needs_a_green_suite()
    check_very_deep_check_record_pass_partial_needs_what_and_who()
    check_very_deep_check_pass_one_needs_a_consumer()
    check_very_deep_check_account_owes_tests_and_incidents()
    check_very_deep_check_account_reads_the_ledger_and_the_questions()
    check_very_deep_check_account_blocks_postdate_the_last_fix()
    check_default_blocklist_runs_the_vocabulary_layer()
    check_session_practices_load_without_publishing()
    check_fix_sweep_copy_keeps_its_neighbours()
    check_fix_sweep_judges_in_force_by_the_targets_resolver()
    check_engine_carries_no_branch_naming_enforcement()
    check_consumer_engine_carries_what_its_checks_import()
    check_install_names_the_other_assistants_adapters()
    check_install_report_lists_only_placeholders_an_adopter_fills()
    check_update_commit_note_leaves_out_the_vendored_catalogue()
    check_fresh_install_reaches_its_code_owner_practices()
    check_session_start_says_when_bootstrap_is_missing()
    check_individual_bootstrap_says_to_fill_in_identity()
    check_install_records_the_commit_its_catalogue_came_from()
    check_update_hands_the_engine_refresh_the_followed_tip()
    check_fresh_install_links_its_file_names()
    check_bare_all_runs_across_the_cores()
    check_full_run_asks_first()
    check_refresh_never_says_nothing_to_do_after_removing_a_file()
    check_refresh_from_ref_off_the_branch_is_recorded()
    check_upholds_is_a_listed_field()
    check_generated_files_candidates_are_repo_rooted_claims()
    check_incident_coverage_reads_what_the_gotcha_names()
    check_retired_sets_are_dropped_only_when_nothing_is_lost()
    check_source_level_reads_go_through_the_normalizer()
    check_update_vendors_retires_the_team_level_word()
    check_dropped_set_and_proxy_and_template_refs()
    check_dropped_set_prose_successors_and_families()
    check_removal_selects_its_checks()
    check_update_never_fetches_the_repo_it_updates()
    check_engine_capability_holds_a_practice_back()
    check_new_rule_shows_its_debt_and_booked_names_it()
    check_bot_authored_commits_are_warned_where_no_person_is_declared()
    check_harness_drops_inherited_git_repository_variables()
    check_a_check_leaves_no_foreign_engine_module_behind()
    check_harness_fixtures_run_no_background_maintenance()
    check_session_trailer_check_ships_with_the_engine()
    check_orphan_scan_reads_who_claims_a_script()
    check_move_dedupe_stub_names_the_slug_alone()
    check_session_practices_drop_what_agents_md_carries()
    check_not_binding_cannot_be_abused()
    check_codeowners_check_is_a_check()
    check_status_contract()
    check('the scope field is legal, and the spec list of what carries it '
          'matches the tree',
          *check_scope_field_is_legal_and_matches_this_spec())
    check_legacy_status_migration()
    check_retired_practices_leave_the_views()
    check_resident_subset(files)
    check_behavioral_replay()
    check('the reply gate names work committed but not landed',
          *check_reply_gate_names_work_not_yet_landed())
    check('a filtered-out check unpacks as N/A, never as a pass',
          *check_filtered_check_does_not_break_the_unpack_family())
    check('a practice source ships no CI workflow, and an existing set loses one',
          *check_a_source_set_ships_no_ci_workflow())
    check('the old install\'s leftovers leave by content, never by name',
          *check_legacy_leftovers_retired_by_content())
    check('a file a decommissioned engine tool wrote leaves by content',
          *check_engine_written_leftovers_leave_by_content())
    check('a local workflow declaration is one keep-or-delete question, asked once',
          *check_local_workflow_declaration_is_asked_once())
    check('retiring an engine tool asks what it left in other repositories',
          *check_retiring_an_engine_tool_asks_what_it_left())
    check('a change to Update Vendors is announced, with a one-repository trial offered',
          *check_update_vendors_change_is_announced())
    check('refresh repoints a retired catalogue pin to main, and no other pin',
          *check_refresh_repoints_a_retired_catalogue_pin())
    check('a repo\'s upstream_branch declaration is followed, and only main or staging',
          *check_upstream_branch_declaration_is_followed())
    check('the fixture seed cache copies exactly what a seed writes, under a key '
          'that moves with its inputs', *check_seed_cache_copies_what_a_seed_writes())
    check('Update Vendors runs as one command and stops only for the repo\'s own calls',
          *check_update_vendors_is_one_command())
    check('Update Vendors runs code no older than the commit it applies, and never '
          'moves the clone', *check_update_runs_code_at_least_as_new_as_it_applies())
    check('an update that deletes a vendored file upstream dropped ends DONE',
          *check_update_vendors_survives_an_upstream_deletion())
    check('Update Vendors resolves a committed local edit to an engine file by rule',
          *check_update_vendors_resolves_local_edits())
    check('a rerun after a FAILED Update Vendors takes the staged output as its own',
          *check_update_rerun_after_failed_takes_its_own_output())
    check('Update Vendors re-baselines a file it asked about, and its review reads no git output',
          *check_update_rebaselines_what_it_asked_about_and_reviews_no_git_output())
    check('a rerun of Update Vendors counts its own staged output apart from yours',
          *check_update_rerun_counts_its_own_staged_output_apart())
    check('Update Vendors reports every blocker before it starts the slow check',
          *check_update_reports_every_blocker_before_the_slow_check())
    check('change-updates-its-docs finds the same removed paths without a regex per path',
          *check_gone_path_matcher_matches_one_regex_per_path())
    check('model_audit --changed selects only the models a change reaches',
          *check_model_audit_changed_selects_only_what_a_change_reaches())
    check('a merge takes the vendor update as its own commit, or takes it back whole',
          *check_merge_takes_the_vendor_update())
    check('send carries a committed local edit upstream as a scrubbed branch',
          *check_send_carries_a_local_edit_upstream())
    check_local_edits_fetch_the_vendored_commit_from_upstream()
    check_a_sync_deletion_is_not_a_local_edit()
    check('a consumer\'s own check names a vendored copy that drifted from its '
          'record, with no upstream clone',
          *check_copy_fingerprint_is_checked_without_a_clone())
    check('Update Vendors resolves a committed edit to a vendored hook or declared path',
          *check_update_vendors_resolves_hook_and_engine_path_edits())
    check('a section 0 catalogue resolves a committed edit against its own sync record',
          *check_section0_catalogue_resolves_a_committed_edit())
    check('a merge is judged by the repo\'s landing-tier check, and taken back only if it is the cause',
          *check_merge_is_judged_by_the_landing_check())
    check_update_mirrors_from_a_depth_1_source_clone()
    check_update_vendors_resolves_a_catalogue_edit()
    check('a decline re-decided between two Update Vendors runs stays decided',
          *check_update_vendors_redecided_decline_sticks())
    check_decline_while_a_condition_holds()
    check('a declined catalogue file\'s copy is upstream\'s text, so one re-decision holds',
          *check_update_vendors_declined_catalogue_copy_is_upstreams())
    check('an update reruns against the source commit it started from until DONE',
          *check_update_vendors_reruns_pinned_to_its_first_commit())
    check('Update Vendors takes the newest main whose GitHub test passed, and says '
          'when that is not the newest',
          *check_update_vendors_takes_only_a_main_that_passed())
    check('a failed test on main opens a GitHub issue, from one step that runs only '
          'then', *check_main_test_failure_opens_an_issue())
    check('a passed test on main leaves a git marker any clone can read',
          *check_main_test_pass_leaves_a_git_marker())
    check('a passed test on main\'s head closes the "main\'s test failed" issue, '
          'from either job, or from a pull request once main holds its files',
          *check_main_test_pass_closes_the_issue())
    check('session start lists an open "main\'s test failed" issue first',
          *check_session_start_lists_a_red_main_first())
    check('a deliberate alerting test is listed as a test to confirm, never as a '
          'failure', *check_alerting_test_is_listed_as_a_test())
    check('Update Vendors ends with the catalogue copy its record names, a kept '
          'local edit reported',
          *check_update_vendors_leaves_the_copy_its_record_names())
    check_update_vendors_migrates_hand_written_views()
    check('every shipped CI template that runs the checks installs PyYAML first',
          *check_ci_templates_install_pyyaml_before_the_checks())
    check('the leak gate sees the main clone\'s private siblings from a worktree',
          *check_leak_gate_sees_main_clone_siblings_from_a_worktree())
    check('Update Vendors replaces a section 0 catalogue and never skips it silently',
          *check_update_vendors_updates_a_section_0_catalogue())
    check('the merge gate judges a pull request by its declared base',
          *check_merge_gate_judges_the_declared_base())
    check('Update Vendors lists what it says it lists, lets a renamed practice go, '
          'and keeps an unchanged timestamp',
          *check_update_vendors_reports_what_it_says_it_lists())
    check('every line of the withdrawal record reads back, so no consumer\'s sync '
          'refuses a deliberate withdrawal as a loss',
          *check_withdrawal_record_lines_all_read_back())
    check('the close detector does not read the assistant quoted back as the '
          'person\'s instruction', *check_close_detect_ignores_the_assistant_quoted_back())
    check('the close detector skips a seeded prompt whatever header shape it '
          'opens with', *check_close_detect_skips_every_seeded_header_shape())
    check('a view sync passes its own --check from another checkout of the same '
          'commit, as a Promote checks it',
          *check_sync_check_passes_from_another_checkout())
    check('the views check reads a shared set at the commit it was synced at, '
          'holds it to the push\'s rung, and a sync never rolls it back',
          *check_views_check_reads_a_set_at_the_commit_it_was_synced_at())
    check('the push check hands the views check where the push goes',
          *check_push_destination_reaches_the_views_check())
    check('the session check calls a commit unpushed only when no origin branch '
          'has it', *check_session_check_names_commits_on_origin_off_main())
    check('a change to a universal practice names each set copy that overrides it',
          *check_universal_change_names_the_set_copies_that_override_it())
    check('a generated index with no sources yet passes when its own check does',
          *check_generated_index_of_nothing_yet_passes())
    check('Update Vendors fetches the sets a person brings before it syncs the views',
          *check_update_fetches_brought_sets_before_the_views())
    check('the freshness notice reads a section 0 catalogue by its own sync record',
          *check_freshness_reads_a_section0_catalogues_own_sync())
    check('Update Vendors asks for headline case only on files the check judges',
          *check_update_asks_headings_only_of_published_files())
    check('Vocabulary reads a practice the sync wrote as one practice, not two',
          *check_vocabulary_reads_a_materialized_practice_as_one())
    check('a sync refuses a rule waiting on a brought set by that reason, never '
          'with --allow-removals', *check_sync_refuses_a_rule_waiting_on_a_brought_set_by_name())
    check('a re-run of Update Vendors stages an earlier run\'s catalogue mirror as its own',
          *check_update_adopts_an_earlier_runs_catalogue_mirror())
    check('precedent_show follows a deduplicated slug to the rule in force, across sources',
          *check_show_follows_a_deduplicated_slug_across_sources())
    check('every TemporaryDirectory cleanup retries a transient "not empty", '
          'and one that never empties still says what is left',
          *check_every_tempdir_cleanup_retries())
    check('a heading anchor keeps combining marks, as GitHub\'s does (doc_lint and doc_html)',
          *check_heading_anchor_keeps_combining_marks())
    check('spoken commands lead the session-start output, from every repo, before any cut',
          *check_spoken_commands_lead_the_session_start())
    check_vocabulary_scan_skips_code_owner_commands()
    check('Update Vendors: gotchas/ seeded, generated files rebuilt, filled placeholders '
          'carried, allow rules once, live citations quiet, pip errors kept',
          *check_update_vendors_onegplanning_findings())
    check('a set the person brings reaches the session at start: printed, not just '
          'written, and the block always points at the file',
          *check_a_brought_sets_spoken_trigger_reaches_the_session_at_start())
    check('the session file says each spoken command once: first, and not again '
          'in its occasion index',
          *check_session_file_says_each_command_once())
    check('an addition loads with the rule it adds to: no index line, shown by '
          'precedent_show and the gate with its base, marked on a spoken command',
          *check_additions_load_with_their_rule())
    check('Update Vendors builds the views again after stamping their source, and a '
          'consumer\'s view check skips a view it never had',
          *check_views_follow_the_header_stamp_and_consumer_check_skips_absent_views())
    check('declared exports: clones found in any case, exports-only copies resolve, '
          'stamps are no hand edits, copied-in tools run, history skipped, moved '
          'sections kept, output docs never link process/',
          *check_declared_exports_consumer_snags())
    check('a template a copied-in source ships is refreshed by Update Vendors when '
          'unedited, its workflow approval moving with it; an edited one is left',
          *check_installed_templates_follow_their_source())
    check('Update Vendors: left items survive a failure, headers stamp first, vendored '
          'baselines re-record, stale exemptions go, the old commit is right',
          *check_update_vendors_second_consumer_findings())
    check('run_all.sh says when a failure may be uncommitted checks, and only then',
          *check_run_all_warns_when_checks_are_uncommitted())
    check('run_all.sh runs only the check for an unchanged shipped test, the self-test otherwise',
          *check_run_all_trusts_only_unchanged_shipped_tests())
    check('precedent_source_names explains a hosted proxy\'s 403 and names the remedy',
          *check_source_names_explains_a_proxy_refusal())
    check('a push to main skips main\'s GitHub test only when those exact files already passed it',
          *check_push_to_main_skips_what_already_passed())
    check('Update Vendors converges a consumer\'s CI to upstream, and asks nobody',
          *check_update_vendors_converges_consumer_ci())
    check('the instruction files name only repositories that exist',
          *check_instruction_files_name_repos_that_exist())
    check('a consumer may declare a CI workflow its own and keep it',
          *check_a_consumer_may_declare_a_ci_workflow_its_own())
    check('the reply check names every predicate it cannot evaluate',
          *check_reply_check_names_what_it_cannot_evaluate())
    check_reply_examples_are_tested_with_what_they_inherit()
    check_reply_gate_prints_a_note_from_a_set_tool()
    check('the archive check sees work left in a scratch folder',
          *check_archive_check_sees_work_left_in_a_scratch_folder())
    check('the session check adopts a detached start the branch carries',
          *check_session_check_adopts_a_detached_start())
    check('the session check reports a source cloned twice on one disk',
          *check_session_check_reports_a_source_cloned_twice())
    check('one practice source is one tree: each harness\'s home folder, the '
          'listers on links running both ways, two runs leave one clone',
          *check_one_tree_per_source_whichever_way_links_run())
    check('a practice set carries the tools that rebuild its todo and gotcha indexes',
          *check_sets_carry_the_todo_and_gotcha_index_tools())
    check('session start says a source did not load only after cloning, '
          'and names each set once',
          *check_session_start_says_did_not_load_only_after_cloning())
    check('the session check never calls an unfetched source clone current',
          *check_session_check_never_calls_an_unfetched_clone_current())
    check_session_check_covers_the_universal_clone()
    check_doc_sync_reads_a_consumers_own_pairs()
    check_catalogue_copy_is_an_allowlist()
    check('the merge gate sees a workflow that never ran on this commit',
          *check_merge_gate_sees_a_workflow_that_never_ran())
    check('a declared loss releases the archive line, and only then',
          *check_declared_loss_unblocks_the_archive_line())
    check('every verdict-returning check is actually recorded',
          *check_every_verdict_returning_check_is_recorded())
    check('the quick tier refuses a harness check main() never calls',
          *check_changed_files_refuses_an_uncalled_harness_check())
    check('the reply check requires a destination for a fence block',
          *check_reply_check_requires_a_destination_for_a_fence_block())
    check_reply_check_refuses_a_paste_block_that_lands_unauthorized()
    check_reply_check_wants_a_prompt_block_to_name_both_ends()
    check_a_gap_names_its_reason()
    check_a_set_inherits_the_landing_triggers()
    check('the landing trigger reads per clause, from a list, and the old shape '
          'reads as it did', *check_reply_check_reads_a_landing_trigger_by_clause_and_by_list())
    check('the reply check requires the Boildown to open with where the work is',
          *check_reply_check_requires_the_boildown_first_line())
    check('the reply check wants an ask under Your next steps to state its question',
          *check_reply_check_wants_an_ask_to_state_its_question())
    check('the reply check wants a finished plan to ask to act, and a hold to '
          'say what runs', *check_reply_check_wants_a_finished_plan_to_ask_and_a_hold_to_say_why())
    check('a vendored container scan knows a session-start refresh branch',
          *check_vendored_container_scan_knows_a_refresh_branch())
    check('the reply check refuses a Boildown that only repeats the last one',
          *check_reply_check_refuses_a_repeated_boildown())
    check('the reply check keeps practice ideas to the closing reply',
          *check_reply_check_keeps_practice_ideas_at_the_close())
    check('the reply check keeps quiet while a batch of background jobs runs',
          *check_reply_check_keeps_quiet_while_a_batch_runs())
    check('a code-owners-only practice reaches only code owners',
          *check_code_owners_only_practices_reach_only_code_owners())
    check('a person with no individual set is known by --admin or their GitHub account',
          *check_a_person_with_no_individual_set_can_be_a_code_owner())
    check("the universal catalogue's close_detect.json travels with it on install and update",
          *check_installer_vendors_the_catalogue_companions())
    check("a fresh install declares universal's reply requirements",
          *check_install_ships_universal_reply_requirements())
    check('the installer asks origin for the base branch before taking the current one',
          *check_installer_base_branch_asks_origin_before_the_current_branch())
    check('the installer defaults visibility to public when it cannot be read, and says why',
          *check_installer_visibility_defaults_to_public_and_says_why())
    check('an install for an assistant with no terminal has GitHub test every push to main',
          *check_installer_no_terminal_tests_every_push_to_main())
    check("the individual-set skeleton's CI comment says what is true",
          *check_individual_skeleton_ci_comment_is_true())
    check('bootstrap.sh says a wrong-Python warning once, not twice',
          *check_bootstrap_says_the_python_warning_once())
    check('the leak gate says no private list is declared when none is',
          *check_leak_gate_note_says_when_no_private_list_is_declared())
    check("the 2026-10-17 install rehearsal's small findings stay fixed",
          *check_install_rehearsal_small_findings_2026_10_17())
    check("a local session's commit identity leaves the laptop's global git config alone",
          *check_commit_identity_leaves_a_laptops_global_config_alone())
    check_endgame_merge_finds_the_silent_drop()
    check('a moved-claim scan that cannot read the tree says so, rather than reporting it clean',
          *check_moved_claims_says_when_it_could_not_read_the_tree())
    check_philosophy_citations_run_both_ways()
    check_vendor_engine_names_a_dependent_of_a_deleted_file()
    check_a_hook_wired_from_elsewhere_is_reported_as_wired()
    check_vendor_engine_removes_a_hook_upstream_dropped()
    check_vendor_engine_keeps_a_declared_engine_path()
    check('a stale source clone is made current, and a skip is never a success',
          *check_a_stale_source_clone_is_made_current_not_reported_clean())
    check_as_ci_shards_match_the_workflow()
    check_main_test_issue_names_the_failing_cases()
    check_one_way_to_fetch_a_missing_commit()
    check_harness_reach_selects_what_a_change_reaches()
    check_isolated_run_matches_the_runner()
    check_isolated_copy_carries_uncommitted_changes()
    check("a suggested link keeps a dotfile path's leading dot",
          *check_suggested_links_keep_a_dotfiles_leading_dot())
    check('the planted-case rotation never narrows silently',
          *check_planted_case_rotation_never_narrows_silently())
    check('an unlabelled prompt into a session is refused before it is sent',
          *check_seeded_prompt_gate_refuses_an_unlabelled_prompt())
    check('an engine-property check is reachable by what you touched',
          *check_engine_checks_can_be_reached_by_what_you_touched())
    check_precedent_check_fires()
    check('checks read what their rules name', *check_checks_read_what_their_rules_name())
    check('checkin update --source stamps that source\'s manifest, not the universal one',
          *check_update_with_source_stamps_that_sources_manifest())
    check('the branch store and the lease board and result cache on it',
          *check_branch_store_and_its_callers())
    check('no file that runs ships with a merge conflict marker',
          *check_no_conflict_markers_in_shipped_tools())
    check_routing_reason_lives_in_the_practice()
    check_filename_separator_knows_names_it_did_not_choose()
    check_one_python()
    check_new_exemption_needs_a_root_fix()
    check_retired_words_are_found_and_history_is_left()
    check_practice_file_shape_judges_one_file_at_a_time()
    check_a_changed_glob_needs_its_reason_looked_at()
    check_very_deep_check_finds_a_second_list_of_practices()
    check_very_deep_check_finds_vendored_surplus()
    check_every_file_is_decided_by_a_vendoring_rule()
    check_show_loads_a_practice_from_a_declared_source()
    check_session_file_warning_does_not_count_against_its_ceiling()
    check_routing_audit_coverage()
    check_parallel_artifact_ledger_fires()
    check_publisher_bound_checks_run_in_a_source_set()
    check_a_set_runs_the_checks_its_declared_sources_put_in_force()
    check_deep_check_keeps_a_test_of_a_tool()
    check_deep_check_skips_a_repo_with_no_check_scripts()
    check_tree_checks_hold_on_every_kind_of_fresh_repo()
    check_stale_exemption_is_named()
    check_practice_links_travel_skips_a_consumers_repo_local_practices()
    check_practice_links_travel_holds_a_set_to_its_copy_in()
    check_gate_channel()
    check_reply_gate_sees_every_source()
    check_advisory_requirement_never_blocks()
    check_contradiction_requirement_blocks()
    check_compaction_offer_fires_on_context_growth()
    check_compaction_offer_owed_printed_at_turn_start()
    check_promote_names_a_binary_conflict()
    check_land_rebuilds_generated_content_without_a_header()
    check_gate_drops_a_practice_another_source_replaced()
    check_container_check_lists_commands_still_running()
    check('the archive line is refused when the container holds '
          'only-copy work',
          *check_archive_line_is_refused_when_the_container_holds_only_copy_work())
    check_vocabulary_prefers_the_file_you_are_standing_on()
    check_vocabulary_moves_a_word_to_our_language()
    check_archive_guard_refuses_work_left_on_a_feature_branch()
    check_archive_guard_waits_for_an_unfinished_plan()
    check_trivial_checkin_exempts_the_boildown_gate()
    check_close_detection_fires_only_when_all_conditions_hold()
    check_close_detect_counts_only_this_sessions_reverts()
    check_loader_block_advertises_only_live_channels()
    check_source_sets_can_learn_they_are_stale()
    check_loader_tools_are_repo_relocatable()
    check_materialize_bridges_loader()
    check_shipped_tests_name_their_owner_and_fail_at_home()
    check_materialize_carries_harness_adapters()
    check_sync_keeps_a_hook_whose_stub_has_no_script()
    check_practice_ships_its_files()
    check_brought_set_ships_reach_the_session_untracked()
    check_session_ships_exclude_survives_another_worktree()
    check_show_flags_unreachable_materialized_source()
    check_saved_individual_copy_loads_for_its_owner_only()
    check_sync_views_cross_source()
    check_sync_refuses_to_lose_a_recorded_practice()
    check_doc_lifecycle_fires_and_clears()
    check_commit_identity_derives_declared_timezone()
    check_superseded_source_says_so()
    check_refresh_removes_dropped_engine_files()
    check_decommission_skips_generated_files_and_prose()
    check_decommission_exempt_record_still_blocks_a_link()
    check_decommission_records_a_file_already_deleted()
    check_todo_migrate_needs_a_migrated_item()
    check_refresh_survives_an_upstream_rename()
    check_retirement_record_is_not_a_stranded_link()
    check_commit_identity_prevents_the_wrong_offset()
    check_commit_identity_ci_cadence()
    check_push_check_gate()
    check_hooks_share_one_quote_blanking_block()
    check_global_backstop_runs_person_fixer()
    check_update_judges_the_committed_tree()
    check_update_adopts_engine_written_ahead()
    check_acronym_scan_skips_wrapped_code_spans()
    check_lint_flags_a_table_with_no_render()
    check_lint_runs_the_hosts_shim()
    check_lint_refuses_an_open_item_waiting_on_an_upstream_fix()
    check_lint_refuses_an_open_item_that_names_no_blocker()
    check_content_paths_skip_session_work_checks()
    check_upstream_fix_sets_up_the_fix_in_the_source()
    check_code_owner_practice_stays_out_of_the_index()
    check_adds_to_names_a_rule_in_force()
    check_boildown_moments_named()
    check_thread_renders_never_touch_the_shared_ledger()
    check_changed_files_only_judges_the_change()
    check_branch_tiers()
    check_no_fixture_points_git_config_at_dev_null()
    check_merge_check_gate()
    check_refresh_sources_lists_a_linked_tree_once()
    check_history_checks_never_ride_a_reused_pass()
    check_identity_mechanism_check_reaches_a_stubbed_hook()
    check_shipped_copy_has_no_broken_links()
    check_commit_backstop_points_shipped_links_at_github()
    check_empty_commits_are_never_counted()
    check_promote_only_and_tier_branches()
    check_github_ci_setting_names()
    check_main_test_minutes_rule()
    check_private_repo_skipped_gate_is_not_main_test()
    check_main_test_cadence()
    check_main_test_repo_setting()
    check_main_test_without_individual_source()
    check_source_clone_is_pinned_to_a_branch()
    check_source_pin_counts_an_uncommitted_new_practice()
    check_consumer_bootstrap_clones_declared_sources()
    check_generator_wires_every_template_guard_mode()
    check_verify_reports_a_source_wired_for_fewer_moments()
    check_verify_flags_missing_session_practices_ceiling()
    check_commit_identity_copies_are_identical()
    check_identity_reaches_a_repo_that_did_not_exist_yet()
    check_person_zone_wins_in_a_shared_rooted_session()
    check_tier_branches_are_never_a_pull_requests_source()
    check_repo_reference_allowlist()
    check_leak_gate_scans_the_consuming_repo()
    check_leak_gate_email_rule_skips_an_ipv4_host()
    check_leak_gate_honors_a_declared_public_email_domain()
    check_update_refuses_while_a_branch_is_pinned()
    check_carry_check_never_counts_upstream_deletions()
    check_bare_sync_warning_ignores_prose_mentions()
    check_leftover_pack_is_flagged_after_migration()
    check_detect_restated_fires()
    check_creation_pipeline_fires()
    check_bootstrap_source_produces_resolvable_set()
    check_bootstrap_writes_what_real_sets_converged_on()
    check_bootstrap_does_what_a_first_update_vendors_adds()
    check_session_hooks_run_for_a_session_opened_above_the_repos()
    check_freshness_quiet_says_when_a_source_is_unverified()
    check_catalogue_hook_runs_the_freshness_notice()
    check_push_check_streams_a_gate_progress_live()
    check_very_deep_check_honours_not_binding_for_other_sources_checks()
    check_bootstrap_source_engine_is_functional()
    check_session_start_refreshes_an_attached_team_clone()
    check_views_drift_gate_reaches_a_source_set()
    check_precedent_check_degrades_in_a_source_set()
    check_rotation_gap_widens_to_find_coverage()
    check_vendor_engine_consumer_case()
    check_vendor_engine_hook_drift_respects_adapters()
    check_vendor_engine_refresh_converges_with_adapter_owned_hooks()
    check_hook_notes_are_said_when_they_change()
    check_archive_gate_keeps_inner_workings_from_non_owners()
    check_vendor_engine_wires_a_new_hook_into_an_installed_repo()
    check_vendor_engine_refreshes_ci_workflow_files()
    check_template_history_includes_a_version_made_in_a_merge()
    check_vendor_engine_refreshes_bootstrap_sh()
    check_vendor_engine_refreshes_agents_md_sections()
    check_retired_branch_name_does_not_ship()
    check_refresh_sources_leaves_an_attached_consumer_alone()
    check_refresh_sources_path_names_the_whole_target()
    check_refresh_sources_pulls_a_set_behind_its_own_origin()
    check_refresh_sources_never_fetches_the_branch_a_clone_sits_on()
    check_refresh_sources_branch_line_only_when_the_tree_is_older()
    check_refresh_sources_reads_a_fetched_main()
    check_removed_engine_path_is_found_in_the_sets_beside()
    check_land_refusal_says_whether_a_pull_request_gets_checks()
    check_leak_gate_reads_a_declared_visibility_before_the_owner_default()
    check_staging_tier_is_never_main_where_origin_has_staging()
    check_workflows_use_actions_that_run_on_node_24()
    check_refresh_sources_leaves_the_base_branch_clean()
    check_freshness_reads_a_private_source_through_its_clone()
    check_whats_new_log_mechanics()
    check_whats_new_skips_precedents_own_updates()
    check_received_hooks_and_moved_engine_files()
    check_loader_caps_unmeasured_without_a_declared_source()
    check_loader_block_with_an_absent_individual_set()
    check_rename_links_leaves_dated_records_alone()
    check_rename_links_spares_a_path_moved_into_gitignore()
    check_rename_links_spares_a_url_into_another_repository()
    check_clean_tree_judges_the_branch()
    check_views_refuse_to_drop_hand_edits()
    check_render_contents_can_be_switched_off()
    check_untracked_renders_use_source_fingerprints()
    check_bootstrap_local_steps_run_and_dead_lines_are_named()
    check_bootstrap_new_branch_compared_to_landing_branch()
    check_todo_migrate_refuses_a_subdirectory()
    check_todo_migrate_reads_a_consumers_list()
    check_docs_current_state_honours_load_bearing_paths()
    check_filename_separator_ignores_a_date_suffix()
    check_update_written_files_name_no_mirrored_engine()
    check_docs_name_no_path_this_repo_removed()
    check_workflow_growth_needs_the_persons_words()
    check_worktree_snapshot_needs_no_git_identity()
    check_practice_set_workflows_converge()
    check_update_deletes_a_shipped_voice_md()
    check_freshness_guard_checks_declared_sets()
    check_source_base_url_defaults_to_the_token_account()
    check_session_check_suggests_anchored_also_list()
    check_stale_source_paths_accepts_the_universal_pair()
    check_promote_runs_doc_html_only_where_it_is_in_use()
    check_push_check_installs_gate_packages()
    check_markdown_required_only_where_doc_html_runs()
    check_push_check_runs_cheap_checks_first()
    check_push_check_records_over_its_own_ledgers()
    check_push_check_refuses_an_unknown_option()
    check_bare_push_check_takes_the_landing_tier()
    check_full_tier_needs_a_reason_on_a_quick_landing()
    check_wait_loop_gate_refuses_pgrep_f()
    check_answer_first_gate_holds_a_change_until_the_question_is_answered()
    check_repo_attach_gate_refuses_a_sweep_nobody_asked_for()
    check_outbound_privacy_gate_refuses_and_scan_finds()
    check_reach_key_self_check()
    check_ledger_ignores_checkout_layout()
    check_content_record_self_check()
    check_doc_sync_ledger()
    check_doc_sync_fails_fast()
    check_doc_sync_keeps_finished_blocks()
    check_model_audit_ledger()
    check_vendor_engine_retires_ci_workflow_files()
    check_workflow_file_outside_vendoring_detects_candidates()
    check_ci_workflow_approved_pins_approval_to_content()
    check_ledger_accepts_a_row_added_with_its_change()
    check_ci_fleet_audit_reads_github_not_the_clone()
    check_ci_fleet_audit_skips_deleted_sets()
    check_ci_fleet_audit_names_when_a_workflow_left_main()
    check_session_start_warns_of_unapproved_workflow()
    check_workflow_write_gate_refuses_api_writes()
    check_very_deep_check_workflow_liveness_scan()
    check_rule_rewrite_detection()
    check_source_shape_is_verified()
    check_machine_readable_files_parse()
    check_null_frontmatter_is_absent()
    check_frontmatter_is_real_yaml()
    check_frontmatter_field_order_fixer()
    check_worktree_resolves_sources_beside_its_main_checkout()
    check_generated_blocks_both_styles()
    check_runner_drops_findings_on_received_files()
    check_refresh_wired_settings_is_not_lost_work()
    check_refreshed_agents_block_is_not_lost_work()
    check_link_anchors_resolve()
    check_materialized_links_are_placed()
    check_in_force_at_chain_is_followed()
    check_links_to_renamed_practice_forward()
    check_practice_refs_sorts_live_from_history()
    check_dedup_onto_same_slug_withdraws_nothing()
    check_update_skips_citations_of_a_rule_that_only_grew()
    check_practice_declared_hooks_are_wired()
    check_stale_views_judged_on_what_a_push_brings()
    check_merge_refreshes_stale_views_as_its_own_commit()
    check_update_asks_before_changing_hooks()
    check_update_asks_for_words_that_name_the_commit()
    check_update_keeps_hook_hashes_with_the_held_hooks()
    check_update_question_names_new_gates()
    check_data_branches_are_named_for_the_ladder()
    check_individual_set_is_charged_to_its_own_budget()
    check_session_share_keeps_a_moved_rule_with_its_brought_set()
    check_session_file_over_ceiling_names_the_individual_share()
    check_install_and_update_name_the_code_owners()
    check_update_judges_retired_sets_after_the_catalogue()
    check_date_check_skips_commits_github_made()
    check_update_rerun_after_left_for_you_still_drops_a_deleted_set()
    check_update_takes_a_removal_its_source_decommissioned()
    check_update_decommission_fits_the_vendored_sync()
    check_built_from_record_is_compared_and_orders_the_updates()
    check_update_all_vendors_skips_its_own_source()
    check_update_all_reads_what_the_update_prints()
    check_update_all_moves_a_reused_clone_off_its_pin()
    check_copy_in_clones_an_offered_set_it_said_yes_to()
    check_declared_set_found_beside_the_individual_set()
    check_engine_writes_the_persons_maintainer_name()
    check_private_scrub_names_a_copied_set_by_its_own_repo()
    check_copy_in_records_the_budget_it_brings()
    check_session_load_total_is_the_one_budget()
    check_legacy_workflow_sweep_honours_the_persons_approval()
    check_promote_commits_carry_a_session_trailer()
    check_promote_marks_other_sessions_commits()
    check_sync_names_files_still_naming_removed_checks()
    check_over_target_line_says_whose_load_and_how_to_break_it_down()
    check_session_check_names_a_declared_retired_set()
    check_deleted_set_is_not_an_unresolved_source()
    check_source_bootstrap_keeps_what_git_said()
    check_runbook_names_the_postcondition_after_a_merge()
    check_update_done_names_the_branch_to_commit_on()
    check_update_done_names_the_update_branches_it_replaces()
    check_session_check_stamps_at_session_start()
    check_vdc_is_a_known_acronym_everywhere()
    check_gates_promise_no_override()
    check_gate_refusals_are_worded_by_their_tools()
    check_publish_gate_passes_the_branch_cleanup_page()
    check_branch_cleanup_page_is_one_page_updated_in_place()
    check_branch_cleanup_page_script_parses()
    check_branch_cleanup_refresh_writes_only_what_it_checked()
    check_branch_cleanup_page_lists_staging_waiting_to_go_live()
    check_branch_cleanup_page_never_offers_main_and_marks_moved_engine_names()
    check_branch_cleanup_open_next_is_a_real_link()
    check_stale_branches_skip_a_reverted_merge()
    check_engine_unpacks_tars_in_one_place()
    check_update_seeds_an_upstream_budget_for_a_vendored_tool()
    check_kept_section_reports_upstreams_change_not_its_lacks()
    check_citations_skip_a_generated_block()
    check_citations_in_a_declared_record_are_history()
    check_second_pass_judgment_replaces_first_pass_left()
    check('a kept section re-pins by itself when upstream\'s change misses what it kept',
          *check_kept_section_repins_a_change_that_misses_the_kept_lines())
    check_repin_kept_records_the_persons_words()
    check_document_project_agents_md_is_compared_with_its_own_template()
    check_refresh_adds_read_only_allow_rules()
    check_attaching_a_source_needs_no_prompt()
    check_engine_tools_allowed_and_none_asks()
    check_leak_gate_reads_the_written_private_repo_list()
    check_session_hooks_allow_read_only_tools_at_user_level()
    check_global_gate_runs_a_repos_gate_only_from_above()
    check_reply_check_refuses_an_unlinked_branch_or_file()
    check_turn_start_names_what_the_last_reply_left_out()
    check_switchboard_runs_the_hooks_of_the_repo_an_action_is_about()
    check_maintainer_heartbeat_names_a_missing_maintainer_once()
    check_reply_gate_trims_for_standing_sessions_and_one_line_forms()
    check_cloud_setup_script_writes_each_hook_once()
    check('an empty blocklist is reported as nothing checked, never a pass',
          *check_empty_blocklist_is_not_a_pass())
    check_hook_changes_never_touch_dot_claude()
    check_sync_names_a_field_its_engine_does_not_know()
    check_practice_change_propagates_refuses()
    check_source_supplied_checks_run()
    check_individual_source_bootstrap_self_heals()
    check_stale_render_self_heals()
    check_stale_render_heal_never_overwrites_with_less()
    check_a_sets_own_hooks_are_registered_in_a_session_rooted_in_it()
    check_a_set_in_a_linked_worktree_does_not_load_itself_twice()
    check_attached_sets_sources_are_synced()
    check_attached_sets_sync_is_safe_for_everyone()
    check_ladder_opt_in_loader()
    check_landing_waits_for_a_missing_ladder_set()
    check_visibility_audit_skips_only_fixture_names()
    check_set_words_leave_out_the_set_itself_by_name()
    check_set_words_hold_a_practice_printed_part_to_output_patterns()
    check_moves_core_names_exist_in_the_engine()
    check_bound_set_tools_and_reply_examples_are_held_in_any_set()
    check_resolver_leaves_out_the_set_itself_by_name()
    check_a_missing_clone_says_not_cloned()
    check_off_base_sources_are_named()
    check_refresh_refuses_an_untested_main()
    check_ladder_off_engine_says_no_ladder_words()
    check_ladder_test_session_and_the_two_ladder_checks()
    check_consumer_sync_counts_what_a_brought_set_provides()
    check_brought_sets_have_their_own_session_budget()
    check_consumer_rehearsal_smaller_faults()
    check_sync_keeps_the_map_and_links_after_a_removal()
    check_refresh_never_rolls_a_newer_engine_back()
    check_seed_refuses_an_engine_main_lacks()
    check_self_heal_skips_a_scratch_copy()
    check_self_heal_universal_source_leaves_no_bytecode()
    check_source_credentials()
    check_hosted_sessions_resolve_without_attaching_a_repo()
    check_a_set_exports_only_its_own_rules()
    check_copied_in_shared_sets()
    check_copied_in_set_carries_its_reply_rules()
    check_copied_set_carries_another()
    check_copy_in_is_asked_once()
    check_declared_exports_are_copied()
    check_exports_only_copy_resolves()
    check('a failed update\'s rerun keeps an uncommitted copied-in set',
          *check_failed_rerun_keeps_an_uncommitted_copied_in_set())
    check_early_copy_in_yes_waits_for_the_set()
    check_public_copy_in_needs_the_leak_check()
    check_copy_in_question_names_what_would_leak()
    check_update_refuses_a_shortened_flag()
    check_vendored_engine_reads_the_consumer_root()
    check_source_clone_keeps_its_credential()
    check_source_credentials_reach_clones_nothing_syncs()
    check_fixtures_own_the_credential_environment()
    check_todo_progress_discriminates()
    check_split_projection_is_costed_and_ordered()
    check('duplicate detection ignores a run of lines with no word in it',
          *check_duplicate_runs_skip_wordless_lines())
    check_past_template_text_is_taken_over_a_stale_record()
    check_kept_agents_md_divergence_is_recorded()
    check_agents_templates_repeat_no_practice_text()
    check_agents_templates_conventions_point_to_practices()
    check_update_seeds_budgets_on_the_run_that_reports_done()
    check_absent_agents_md_section_is_asked_across_self_refresh()
    check_kept_bootstrap_divergence_is_recorded()
    check('the AGENTS.md template sections that became practices migrate out of '
          'an installed repository with every rule still reachable',
          *check_retired_template_sections_migrate_into_practices())
    check('a file a source exports and the consumer never received fails the '
          'copied-in check', *check_exported_file_not_received_fails_the_copied_in_check())
    check('a commit that edits template text in a consuming repository is refused '
          'until it is answered', *check_template_text_edit_trips_the_commit_check())
    check('a kept template divergence is judged block by block, and text moved '
          'out of AGENTS.md is still compared', *check_kept_divergence_is_judged_block_by_block())
    check_legacy_bootstrap_shim_is_replaced()
    check_duplicated_resident_text_detector()
    check_settled_marker_scan_is_scoped_and_follows_the_split()
    check_load_ceiling_blocks_only_the_change_that_grew_it()
    check_session_load_reports_a_file_over_its_own_declared_ceiling()
    check_repo_names_compare_without_case()
    check_engine_tools_say_which_repo_they_read()
    check_check_summary_names_the_repo_it_checked()
    check_engine_check_refuses_from_another_repo()
    check_todo_index_check_survives_midnight()
    check_todo_index_refuses_an_unknown_kind()
    check_clone_lock_makes_parallel_updates_wait()
    check_update_rerun_rerecords_a_template_file_the_first_run_wrote()
    check_audit_says_where_a_moved_bootstrap_section_went()
    check_push_check_walks_every_commit_it_publishes()
    check_rename_links_spares_a_longer_path_and_manifest_notes()
    check_reply_gate_counts_staging_as_a_landing_branch()
    check_global_pre_push_runs_the_leak_gate()
    check_push_check_rewrites_global_hooks_older_than_their_writer()
    check_archived_set_question_names_the_attach_fix()
    check_update_repoints_engine_paths_that_moved()
    check_update_derives_engine_moves_from_git()
    check_landed_check_names_the_tier_that_ran()
    check_branch_name_counts_local_branches()
    check_leak_gate_in_a_worktree_push_reads_its_own_repo()
    check_a_replacing_rule_inherits_what_it_does_not_restate()
    check_lander_lands_where_booked_does_and_says_why_a_push_failed()
    check_land_tells_the_push_hooks_what_it_lands()
    check_land_hands_over_the_landed_branchs_delete_link()
    check_land_sent_to_a_pull_request_carries_mains_work()
    check_land_skips_a_push_the_pull_request_guard_would_refuse()
    check_land_holds_while_its_reached_tests_are_red()
    check_one_fix_mends_two_red_landings_in_a_row()
    check_land_confirm_says_whether_what_landed_was_checked()
    check_leak_gate_reads_other_clones_as_themselves_inside_a_hook()
    check_one_list_declares_a_record()
    check_update_stages_what_a_late_step_writes()
    check_global_hooks_are_never_downgraded()
    check_landers_wait_their_turn_for_the_lock()
    check_a_failure_item_lists_the_index_it_creates()
    check_global_pre_push_refuses_a_tree_the_check_failed()
    check_global_pre_push_refuses_a_tree_the_full_sweep_failed()
    check_a_sessions_own_merge_rebuilds_generated_conflicts()
    check_writing_checks_leave_a_declared_record_as_filed()
    check_vocabulary_lets_a_local_practice_name_a_local_script()
    check_doc_lint_leaves_a_received_practice_to_its_source()
    check_one_upstream_move_is_said_once_at_session_start()
    check_session_load_target_is_reported_each_reply()
    check_budget_approvals_see_computed_raises()
    check_landed_reduction_quiets_the_reduction_ask()
    check_headroom_notice_watches_the_resident_block()
    check_universal_occasion_share_is_capped()
    check_refresh_judges_workflows_once_the_engine_is_whole()
    check_push_check_skips_a_set_check_older_than_push_time_judging()
    check_a_registry_file_can_be_a_checks_own_opt_in()
    check_environment_gotchas_follows_a_split_index()
    check_environment_gotchas_advises_migrating_an_inline_catalogue()
    check('Update Vendors judges a section 0 catalogue against its own sync commit',
          *check_update_vendors_trusts_the_catalogues_own_sync_commit())
    check('Update Vendors re-runs over the catalogue a failed run wrote',
          *check_update_vendors_reruns_over_its_own_output())
    check('the view sync lets an override and a retirement through',
          *check_update_vendors_lets_an_override_through_the_view_sync())
    check('IN FORCE NOWHERE reaches the Update Vendors report, uncontradicted',
          *check_update_vendors_asks_about_a_rule_in_force_nowhere())
    check_gotcha_currency_signals_fire()
    check_relayed_authorization_reader()
    check_pretooluse_hook_fires()
    check_not_binding_actually_exempts_a_check()
    check_mirrored_prefixes_answers_both_install_models()
    check_update_vendors_repoints_renamed_shared_sets()
    check_update_vendors_rebaselines_a_file_now_identical_to_upstream()
    check_default_branch_reads_each_repos_trunk()
    check_light_check_skips_declared_records()
    check_consumer_basic_tier_runs_the_practice_audit()
    check_individual_hook_run_by_hand_links_the_attached_set()
    check_shared_set_leaves_a_link_at_the_attach_path()
    check_update_vendors_defaults_headroom_floor()
    check_engine_fetch_reaches_main_in_a_single_branch_clone()
    check_update_vendors_leaves_mentions_of_a_deleted_file()
    check_no_engine_tool_hardcodes_a_mirror_path()
    check_templates_point_at_gotchas_rather_than_inline_them()
    check_installer_produces_a_clean_install()
    check_update_vendors_rehearsal_findings()
    check_update_vendors_reports_dropped_template_wording()
    check_update_vendors_maps_a_task_kind_to_manual()
    check_a_reasked_left_out_section_is_not_asked_every_rerun()
    check_update_vendors_refreshes_a_template_own_comment()
    check_update_vendors_dropped_wording_reads_a_views_source()
    check_kept_pin_moves_across_a_comment_only_template_change()
    check_update_vendors_names_what_others_changed_upstream()
    check_update_done_names_the_check_it_ran()
    check_update_merge_lines_carry_the_full_head()
    check_update_on_stubs_stages_nothing_under_claude()
    check_size_cap_warning_names_the_cap()
    check_update_finds_the_clone_by_its_origin()
    check_install_and_update_write_the_owners_zone()
    check_update_leaves_no_dead_manifest_entry()
    check_update_in_force_nowhere_asks_once()
    check_update_repoints_moved_engine_commands()
    check_update_vendors_dropped_wording_reads_placeholders_filled()
    check_update_takes_an_untouched_install_copy()
    check_refresh_replaces_a_past_individual_hook_rendering()
    check_refresh_names_an_in_place_hook_no_engine_path_keeps()
    check_retired_mentions_skip_what_the_repo_receives()
    check_dependents_warning_skips_a_wholly_generated_view()
    check_retired_mentions_match_the_full_path_only()
    check_second_pass_drops_a_first_pass_unshipped_workflow_call()
    check_update_says_once_that_commands_moved_to_an_undeclared_set()
    check_retired_words_reads_past_the_decommission_ledger()
    check_bootstrapping_a_set_reaches_no_network_unless_asked()
    check_parallels_table_holds_a_shipped_hook_this_repo_does_not_run()
    check_update_noise_template_lines_and_a_secret_never_had()
    check_session_start_hook_runs_bootstrap_locally()
    check_move_tool_lands_then_deduplicates()
    check_move_tool_covers_every_direction_and_team_removals()
    check_move_tool_names_sets_truly_and_keeps_approvals_current()
    check_move_withdrawal_from_universal_leaves_universal_green()
    check_move_mention_fix_reads_list_items_and_names_what_it_cannot_fix()
    check_bootstrapped_shared_set_carries_current_codeowners()
    check_codeowners_stamp_hashes_only_the_registry()
    check_as_ci_says_why_a_shard_failed()
    check_planted_sweep_runs_only_in_a_named_whole_suite_run()
    check_a_landing_names_the_checks_it_reaches()
    check_as_ci_parts_partition_the_suite()
    check_harness_times_merge_without_a_conflict()
    check_land_times_fallback_keeps_a_deleted_test_deleted()
    check_move_fixes_mentions_of_the_moved_practice()
    check_declared_identity_has_a_passing_state_in_a_shared_repo()
    check_instantiated_template_links_survive_the_copy()
    check_stop_hook_ignores_commits_another_remote_ref_has()
    check_stop_hook_says_each_state_once()
    check_debut_judges_the_change_against_main_too()
    check_update_vendors_retires_pre_staging()
    check_update_vendors_replaces_the_old_landing_comment()
    check_update_vendors_reports_live_pre_staging_mentions()
    check_reply_gate_refreshes_the_landing_branch()
    check_tools_answer_help_without_writing()
    check_loader_block_covers_every_declared_source()
    check_review_page_carries_every_source_and_is_never_committed()
    check_review_page_lists_practices_that_may_overlap()
    check_very_deep_check_fixes_a_renamed_repository()
    check_branch_report_keeps_private_names_out_of_a_public_tree()
    check_very_deep_check_reads_live_and_names_landing_work()
    check_very_deep_check_blocked_on_and_net_empty_branches()
    check_very_deep_check_refuses_unknown_flags_before_the_ledger()
    check_identity_reality_reads_grandfathering_the_bot_and_a_shallow_clone()
    check_config_keys_counts_a_key_a_practice_reads()
    check_very_deep_check_catalogue_loads_are_quiet()
    check_moved_claims_skips_narrated_deletions_and_templates()
    check_ci_fleet_audit_counts_each_workflow_past_the_sample()
    check_bestpractice_engine_hooks_are_stubs()
    check_shared_helpers_have_one_copy()
    check_retired_team_level_spares_ordinary_english()
    check_build_views_says_what_it_decides()
    check_vendored_surplus_counts_a_folder_a_consumer_is_told_to_search()
    check_very_deep_check_runs_other_sources_checks_here()
    check_title_case_leaves_code_and_first_word_alone()
    check_title_case_honours_repo_declared_internal_paths()
    check_push_gate_judges_only_what_a_working_branch_brings()
    check_push_check_runs_approved_workflow_steps()
    check_push_check_honours_not_binding()
    check_merge_gate_waits_for_a_current_merge_ref()
    check_title_case_never_corrupts_content()
    check_title_case_output_paths_inverts_the_default()
    check_checkin_update_never_mutates_the_clone()
    check_checkin_ignores_files_git_does_not_track_in_the_clone()
    check_leak_gate_notes_an_uncovered_private_repo()
    check_rename_links_spares_a_commit_pinned_permalink()
    check_shipped_hooks_pass_rename_links_without_the_mirror()
    check_changed_files_asks_a_new_check_for_its_test()
    check_changed_files_asks_a_new_check_for_its_planted_case()
    check_changed_files_fetches_a_base_a_single_branch_clone_lacks()
    check_changed_files_asks_a_changed_glob_for_its_reason()
    check_very_deep_check_record_trips_no_check_in_a_consumer()
    check_changed_files_compares_quoted_counts_when_a_practice_changes()
    check_changed_files_runs_one_copy_of_a_repo_local_test()
    check_for_change_runs_the_tests_a_change_reaches()
    check_for_change_adds_what_the_reach_ledger_picks()
    check_changed_files_runs_the_harness_tests_a_change_reaches()
    check_quick_tier_is_closed()
    check_a_land_rebuilds_dated_outputs_two_days_left()
    check_a_land_in_a_shallow_clone_is_not_a_conflict()
    check_container_check_sees_other_local_branches()
    check_caused_by_this_push_reads_advisory_findings()
    check_push_check_list_is_never_refused()
    check_a_pushed_branch_in_a_shallow_clone_is_safe()
    check_very_deep_check_lists_checks_by_stage()
    check_set_independence_reads_tests_and_rules()
    check_set_independence_holds_only_what_a_waiting_part_names()
    check_upstream_edits_need_an_answer()
    check_a_new_test_lands_with_its_time()
    check_boildown_contradiction_spares_work_waiting_upstream()
    check_leak_gate_discovers_the_individual_blocklist()
    check_leak_gate_reads_neighbour_blocklists()
    check_leak_gate_names_a_stale_blocklist_clone()
    check_leak_gate_refresh_declines_a_dirty_clone()
    check_freshness_covers_every_declared_source()
    check_visibility_audit_reads_the_blocklist_as_patterns()
    check_leak_gate_reads_a_sets_own_visibility()
    check_visibility_audit_reads_repo_names_out_of_prose()
    check_missing_brought_set_names_a_fetch_that_runs()
    check('the individual set has one tree on disk, whichever of the '
          'bootstrap and the attach tool cloned it first',
          *check_individual_set_has_one_tree_whichever_route_cloned_it())
    check('two diverged copies of the individual set are reported, never '
          'clobbered',
          *check_individual_set_diverged_copies_are_reported_not_clobbered())
    check_render_names_files_by_title()
    check_rendered_docs_are_current()
    check_install_names_every_not_vendored_dir()
    check_philosophy_readme_lists_every_file()
    check_todo_gotcha_stale_reference_fires()
    check_due_reminder_reaches_the_reply()
    check_todo_and_gotcha_sweeps()
    check('typography finishes outward text, and every engine page goes through it',
          *check_typography_finishes_outward_text_and_every_engine_page())
    check('an update leaves what a removed check strands, installs past PEP 668, '
          'stamps never reach a build code or a synced copy, and a materialized '
          'repository is a consumer',
          *check_update_leftovers_installs_and_stamps())

    # RECAP THE FAILURES BY NAME, immediately before the summary line.
    #
    # This run prints one line per check, and there are over a hundred, so in
    # practice everyone reads the tail: AGENTS.md's own deep-check section
    # says "what matters is 0 failed", which is a summary-line instruction.
    # A `tail -3` therefore captured "110 passed, 1 failed" and NOT the FAIL
    # line hundreds of lines above it -- which happened on 2026-09-07, to a
    # failure that then did not reproduce in five further runs on the same
    # tree. The count said something was wrong and the output no longer
    # existed to say what. An intermittent failure you cannot name is one you
    # cannot fix, and re-running is exactly what destroys the evidence.
    #
    # Cheap, and it makes the tail self-sufficient: the last thing printed
    # now names every failure, so the shortest reading of this tool's output
    # that anyone actually does is enough to act on.
    if FAILED:
        print("\nFAILED CHECKS:")
        for name, detail in FAILED:
            print(f"  - {name}" + (f" -- {detail}" if detail else ""))
        # The tail is what anyone actually reads, so the environment cause
        # is named again HERE rather than only in the preflight line, which
        # by now is hundreds of lines above.
        _report_missing_doc_packages('NOTE')
    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    na_file = os.environ.get('PRECEDENT_NA_FUNCTIONS_FILE')
    if na_file and NA_FUNCTIONS:
        # Appended, not written: --as-ci runs one process per shard.
        with open(na_file, 'a', encoding='utf-8') as fh:
            fh.write(''.join(f'{n}\n' for n in sorted(NA_FUNCTIONS)))
    times_out = os.environ.get('PRECEDENT_HARNESS_TIMES_OUT')
    if times_out and CHECK_DURATIONS:
        # One file per shard process: run_as_ci merges them for --record-times.
        with open(times_out, 'w', encoding='utf-8') as fh:
            json.dump({n: round(dt, 2) for n, dt in CHECK_DURATIONS}, fh)
    _report_check_durations()
    return 1 if FAILED else 0


# THE TESTS LIVE IN tools/harness/, ONE FILE PER AREA (2026-10-31). This file
# keeps the runner and the shared fixtures; every check moved into the area it
# exercises, so sessions stop colliding on one 98,000-line file. Each part is
# executed into THIS namespace, not imported: a check there sees every name
# defined above exactly as when it lived here, and the filter, the timing, the
# reach recording and main() find it in globals() as before. Compiled under its
# own path, so a traceback and the reach ledger name the real file.
# tools/split_verify_harness.py made the split; tools/harness_parts.py is the
# one answer to "which files are the harness" for every tool that reads it.
import harness_parts  # noqa: E402


def _load_harness_parts():
    # One namespace means a second `def` of a name already defined -- here or
    # in another part -- would replace the first without a word, and which
    # one wins would hang on file order. Refused instead, naming both.
    seen = {}
    for _part in harness_parts.part_paths(ROOT):
        _src = _part.read_text(encoding='utf-8')
        for _name in re.findall(r'^(?:def|class) (\w+)', _src, re.M):
            where = seen.get(_name) or ('tools/verify_harness.py'
                                        if _name in globals() else None)
            if where:
                raise SystemExit(f'verify_harness: {_name} is defined in '
                                 f'{where} and again in tools/harness/'
                                 f'{_part.name} -- one name, one definition')
            seen[_name] = f'tools/harness/{_part.name}'
        exec(compile(_src, str(_part), 'exec'), globals())


_load_harness_parts()



if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    # --for-change REF runs only the tests a change since REF reaches, under
    # a time budget (spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md) -- never a
    # full run, so it comes before the full-run refusal.
    if '--for-change' in sys.argv[1:]:
        _args = sys.argv[1:]
        _i = _args.index('--for-change')
        if _i + 1 >= len(_args):
            sys.exit('verify_harness: --for-change needs a ref, e.g. --for-change origin/staging')
        _ref = _args[_i + 1]
        # A file is not a ref (2026-10-19: `--for-change tools/x.py` said
        # "git could not diff tools/x.py...HEAD" and ran nothing).
        if subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', '-q',
                           f'{_ref}^{{commit}}'], capture_output=True).returncode != 0:
            hint = (f'{_ref} is a file, not a ref: --for-change takes the base '
                    f'the change is measured from' if (ROOT / _ref).exists()
                    else f'{_ref} names no commit here')
            sys.exit(f'verify_harness: {hint}, e.g. --for-change origin/staging')
        _budget = FOR_CHANGE_BUDGET_SECONDS
        if '--budget' in _args and _args.index('--budget') + 1 < len(_args):
            _budget = float(_args[_args.index('--budget') + 1])
        sys.exit(run_for_change(_args[_i + 1], _budget, dry_run='--dry-run' in _args))
    if '--record-new-times' in sys.argv[1:]:
        sys.exit(record_new_times())
    os.environ.setdefault(FOR_CHANGE_LEDGER_OFF_ENV, '1')
    # A full run by hand is proposed first (HARNESS_ASKED_ENV, above).
    refusal = _full_run_refusal(sys.argv[1:], os.environ)
    if refusal:
        print(refusal, file=sys.stderr)
        sys.exit(2)
    _shape = _full_run_shape(sys.argv[1:], os.environ)
    if _shape:
        os.environ.setdefault(HARNESS_ASKED_ENV, _because(sys.argv[1:]) or 'asked')
        print(f'verify_harness: {_full_run_cost(_shape)}', file=sys.stderr, flush=True)
    _t_start = time.monotonic()

    def _done(rc):
        _record_full_run(_shape, time.monotonic() - _t_start, rc)
        sys.exit(rc)
    # BEFORE main(), because this does not run the suite -- it runs the
    # suite twice, the two ways CI does, each in its own process.
    if '--as-ci' in sys.argv[1:] and '--isolated' in sys.argv[1:]:
        _done(run_as_ci_isolated())
    if '--as-ci' in sys.argv[1:]:
        _done(run_as_ci(record_times='--record-times' in sys.argv[1:]))
    # A BARE --all RUNS ACROSS THE CORES (2026-10-06). It is the same set as
    # --as-ci with every planted case, and run in one process it took about
    # 31 minutes on a 4-core container that --as-ci fills in about 11 (the
    # very deep check's step 2 runs it). A shard process never sees --all
    # (run_as_ci starts them with no arguments) and a filtered run keeps its
    # filter, so neither recurses. PRECEDENT_HARNESS_SERIAL=1 is the old
    # one-process run, for profiling.
    #
    # --all --record-times records every check's time from that run
    # (2026-10-17): the very deep check's whole-suite run is the one the
    # TEST WORTH section judges by, so its times must be that day's, not a
    # list measured before the suite last changed shape.
    if _bare_all_runs_in_parallel(sys.argv[1:], os.environ):
        _done(run_as_ci(every_case=True,
                        record_times='--record-times' in sys.argv[1:]))
    _done(main())
