#!/usr/bin/env python3
"""Everything GitHub CI used to run on a push, per kind of repository, run locally before it -- `push-check-gate.sh` refuses a push until it passes; a push to a working branch runs its basic tier only, and a push to main the full one

precedent_push_check.py -- run, before a push, what CI used to run after it.

WHY THIS EXISTS (Morgan, 2026-09-25, strength: decided). Three switches now
keep GitHub Actions from running on most of his pushes: `ci_workflows`
(no workflow installed), `ci_every_hours` and `ci_on_branches` (a `[skip
ci]` line on the commit, spec/CI_CADENCE_PLAN.md). And since 2026-09-21 a
practice source runs no CI at all (practice: source-sets-run-no-ci). Every
one of those decisions was argued on the same premise -- "the local check
runs before the push, so CI is a second opinion" -- and nothing ran the
local check. It was a sentence in AGENTS.md and in go-update's Rule. His
ask, on being shown that: "it should be the same list of everything we
used to run (just locally we do it, not via the github ci/cd)."

So this is that list, per kind of repository, and one command that runs
all of it. `push-check-gate.sh` (templates/harness/claude-code/hooks/) calls
it with `--gate` before a session's `git push`, and refuses the push on a
failure. Nothing here depends on any one agent harness; the hook is the
thin Claude Code adapter, and any other harness runs this file directly.

WHAT "EVERYTHING WE USED TO RUN" MEANS, kind by kind. Each entry names the
workflow it replaces, so the next person to retire or add a workflow can
see where its local twin lives:

  upstream   BestPractice itself: .github/workflows/deep-check.yml
             (verify_harness, precedent_check, doc_sync), leak-gate.yml,
             and the retired docs.yml (doc_lint). This is also AGENTS.md's
             own "deep check" list, word for word.
  source     a practice set: the retired precedent-check.yml
             (precedent_check, plus its views-drift job, build_views
             --check), leak-gate.yml and doc-lint.yml. Its commit-identity
             steps already moved to commit-identity-push-gate.sh on
             2026-09-21 and are not repeated here.
  consumer   a repo that installs Precedent: leak-gate.yml, light-check.yml
             (precedent_check) and the retired bestpractice-docs.yml
             (doc_lint).

Two deliberate departures from what CI ran, both stronger rather than
weaker. precedent_check runs `--full-sweep`: bare, it runs only this diff's
checks plus a one-in-ten rotation, which is the trap every source set's
AGENTS.md warns about, and a sweep costs seconds. And leak_gate runs whole,
not `--structural-only`: CI could only run the structural half because it
never had the private blocklist, and a local run does.

THE DEEP CHECK'S OWN SUITE RUNS TOO, wherever a repo has one. A set that
maintains check scripts under tools/checks/ keeps a two-direction test for
each and a driver, tools/checks/tests/run_all.sh, that runs them all --
the mechanical half of its `deep-check` practice, in that practice's own
words. No workflow ever ran it; it was run by hand, or not. Morgan,
2026-09-25: "We had a deep_check too." The first run found five of one
set's cases red, fixed the same day. A repo with no driver skips the entry
and says so.

AND IN A PRACTICE SOURCE, RUNS IT A SECOND TIME SHAPED LIKE A CONSUMER.
Those tests ship: every repository that resolves the source runs them
against its own tree. precedent_consumer_shape.py runs the suite again with
git ignoring what a typical consuming repository ignores, so a test that
passes only in its home layout goes red here instead of there. 2026-09-25:
one test staged a fixture under vendor/ with a plain `git add`, passed on
every run in its source, and failed for days in a consumer that ignores
vendor/, where nobody could fix it.

A SHALLOW CLONE IS DEEPENED FIRST, or the push is refused. Every clone in
a cloud session starts shallow, and a check that walks `git log` over a
shallow clone reports SKIPPED -- which this list would then call a pass.
Measured 2026-09-25: all five of that day's clones were shallow, and a
history check in one set had been skipping on every run. `git fetch
--unshallow` took one to five seconds each.

A PASS IS RECORDED AGAINST THE TREE, so the gate does not run the suite
twice. After a clean run with nothing uncommitted, the HEAD tree's hash
goes into .git/precedent-push-check.json. `--gate` finds that record and
exits at once, which is what makes "run the deep check, then push" cost one
run rather than two (practice: slow-steps-report-and-cache). The record
is keyed on the tree and the check list together, so any change to either
invalidates it, and it lives in the git directory, never in the tracked
tree. "Nothing uncommitted" leaves out the fact ledgers the checks
themselves write (practice: gate-ledger): fact_ledger.py reports each one it
saves, the pass is recorded for the commit, and the refreshed ledgers are
left in place for the person to commit. A ledger only caches facts that
verify themselves, so its working copy changes no verdict; any other
uncommitted edit, before or after the run, still blocks the record.

AND THE PASS IS SHARED WITH EVERY CHECKOUT (Morgan, 2026-09-25, strength:
decided). The record above lives in one checkout, and a person working in
many windows has one checkout per window: a full run in one window was
invisible to the Promote said in another, which ran the whole suite again
on files it had already passed. So a recorded pass is also published to
origin as a small receipt on the receipt branch (data-check-receipts in a
repository on the ladder, precedent-check-receipts elsewhere; see
precedent_data_branches.py) --
receipts/<check list>/<tree>.json, naming the files by hash and carrying
none of them, so it publishes no unpushed work. `--gate` fetches that
branch when this checkout has no record of its own. The trade, said
plainly: anyone who can push to origin can write one, and every checkout
then believes it. Only this file writes them, and only after every check
passed -- the trust the local record already asked for, now reaching every
window instead of one. PRECEDENT_NO_SHARED_PASS=1 turns
both halves off.

TWO TIERS, BY BRANCH (spec/BRANCH_TIERS_PLAN.md, Morgan, 2026-09-25,
strength: decided). Since 2026-10-17 a push to main, and to staging for a
person who lands there, runs only the BASIC tier, and the FULL tier runs at
the Debut and after the push into main (Morgan: "the full tests should
happen after that"). A push to any other branch runs only the BASIC
tier: the markdown lint, the leak gate (pushing any branch of a public
repository publishes it) and the commit-author checks, seconds rather than
minutes. The person's `branch_push_checks` setting can raise the other
branches to full; nothing lowers staging or main. Which branch gets which
lives in precedent_branches.py, not here. A full pass satisfies a basic
gate; a basic pass never satisfies a full one.

Run:
  python3 tools/precedent_push_check.py                  # your landing branch's tier, record a pass
  python3 tools/precedent_push_check.py --tier basic     # the basic tier only
  python3 tools/precedent_push_check.py --tier full --because 'why'
                                  # the full suite; refused without a reason
                                  # where the landing branch is the quick tier
  python3 tools/precedent_push_check.py --gate           # skip if this tree passed
  python3 tools/precedent_push_check.py --gate --push-command 'origin staging'
                                  # the tier that push needs (what the hook runs)
  python3 tools/precedent_push_check.py --list           # what would run, and why

Exit status: 0 everything passed; 1 a check failed; 2 nothing could be run
(not a git checkout, or a repository of no kind this file knows).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = 'precedent-push-check.json'
# The variable fact_ledger.py reads to report each ledger it saves
# (fact_ledger.WRITTEN_ENV; practice: gate-ledger).
LEDGER_WRITES_ENV = 'FACT_LEDGER_WRITTEN'
# Set for every check a push check runs: the branch the push goes to, and
# the commit its change is measured from (the quick tier only).
PUSH_DESTINATION_ENV = 'PRECEDENT_PUSH_DESTINATION'
CHANGED_SINCE_ENV = 'PRECEDENT_CHANGED_SINCE'
# The shared receipts live on one branch -- a cloud session's git proxy
# lets it push branches and nothing else, so a hidden ref namespace was
# refused with a 403 (measured 2026-09-25). One small file per pass,
# receipts/<check list>/<tree>.json, the newest RECEIPTS_KEPT of them.
# Its name comes from precedent_data_branches.py since 2026-10-11:
# data-check-receipts on the ladder, this old name everywhere else, and
# this old name where that file is missing (a partial engine copy).
RECEIPT_BRANCH = 'precedent-check-receipts'
RECEIPT_REF = 'refs/precedent/receipts'


def _receipt_branch(root, write=False):
    """-> the branch the receipts live on here. `write` lets a ladder
    repository's first write copy the old branch to its data- name."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import precedent_data_branches as pdb
    except Exception:                                         # noqa: BLE001
        return RECEIPT_BRANCH
    finally:
        sys.path.pop(0)
    try:
        if write:
            return pdb.name_for_write(root, pdb.RECEIPTS, say=lambda m: print(
                f'precedent_push_check: {m}'))
        return pdb.name(root, pdb.RECEIPTS)[0]
    except Exception:                                         # noqa: BLE001
        return RECEIPT_BRANCH
RECEIPTS_KEPT = 300
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
SHARED_ENV = {'GIT_AUTHOR_NAME': 'precedent_push_check',
              'GIT_AUTHOR_EMAIL': 'precedent-push-check@localhost',
              'GIT_COMMITTER_NAME': 'precedent_push_check',
              'GIT_COMMITTER_EMAIL': 'precedent-push-check@localhost'}
TAIL_LINES = 40
# The lines that say WHY a check failed, printed before the tail. A check can
# end on pages of lines that are not the finding -- precedent_check prints its
# VIOLATION block and then every SKIPPED and unverified check after it -- so a
# tail alone can hold nothing but noise. On 2026-09-25 a merge gate refused a
# consumer's pull request over one unbumped version header, and the session it
# refused could not see why: all forty lines it was shown said SKIPPED.
# A tool name or SHARD may come first: the harness's isolated run prints
# "SHARD FAILED" and "verify_harness FAIL: ..." for a shard that broke, and
# until 2026-09-30 neither was picked, so a full check failed naming nothing.
FINDING = re.compile(r'^\s*(?:[\w.-]+ )?(VIOLATION|ERROR|FAIL(ED|URE)?)\b')
FINDING_LINES = 30
# A shard that died before any verdict -- a traceback, a killed process --
# has no FAIL: line to pick, only the stderr tail the harness prints under
# its SHARD FAILED header, at that header's own indent. On 2026-10-17 a
# Debut failed reading "SHARD FAILED (exit 1)" and nothing else, and the
# same commit passed when rerun, so what broke it was never known.
SHARD_FAILED = re.compile(r'^\s*SHARD FAILED\b')
SHARD_NOISE = re.compile(r'^\s*(?:SKIP|N/A)\b')



def _ladder_off():
    """True only when tools/precedent_ladder.py is here and says the ladder
    is not in force for this person; without it, the old wording stands."""
    try:
        import precedent_ladder
        return precedent_ladder.ladder_in_force(Path(__file__).resolve().parent.parent) is False
    except Exception:                                       # noqa: BLE001
        return False

def _finding_lines(out):
    """The finding headers in `out`, each with the indented lines under it
    (its findings, not the rule text after them), capped at FINDING_LINES."""
    picked, i = [], 0
    while i < len(out) and len(picked) < FINDING_LINES:
        if FINDING.match(out[i]):
            picked.append(out[i])
            i += 1
            if SHARD_FAILED.match(picked[-1]):
                end = i
                while (end < len(out) and out[end].startswith('  ')
                       and not SHARD_FAILED.match(out[end])):
                    end += 1
                block = out[i:end]
                if not any(FINDING.match(l) for l in block):
                    room = FINDING_LINES - len(picked)
                    picked += [l for l in block
                               if not SHARD_NOISE.match(l)][:room]
                    i = end
                continue
            while (i < len(out) and out[i].startswith('    ')
                   and len(picked) < FINDING_LINES):
                picked.append(out[i])
                i += 1
            continue
        i += 1
    return picked

# name, argv, and the workflow it stands in for. A python3 script is named
# by its path alone ({engine} is the engine directory); anything else gives
# its interpreter first. ONE list per kind -- this is the registry; nothing
# else restates it (practice: registry-source-of-truth).
DEEP_CHECK_SUITE = ('deep_check', ['bash', 'tools/checks/tests/run_all.sh'],
                    "no workflow -- the deep-check practice's own suite")
# The same suite as a consumer will run it -- a practice source only, since
# only a source ships its tests (practice: two-check-levels).
CONSUMER_SHAPE_SUITE = ('consumer_shape',
                        ['{engine}/precedent_consumer_shape.py'],
                        "no workflow -- the deep-check suite, consumer-shaped")
# The author and timezone checks, where a repo carries them. They ran in
# precedent-individual's commit-identity.yml and precedent-check.yml until
# 2026-09-21; commit-identity-push-gate.sh runs them too, but only where it
# is wired, and a person running this list by hand should get everything.
# Exit 2 ("could not run here") fails in a repo that carries its own
# identity.json, as it did there; anywhere else it is the expected answer --
# a shared repo's HISTORY is never audited against one person's timezone,
# since other people's commits live there (Morgan, 2026-09-25). His own new
# commits still carry his zone everywhere; the commit-time backstop in
# commit-identity.sh is what holds them to it.
SKIP_IS_FINE_WITHOUT_IDENTITY = {'commit_author', 'commit_dates'}
# THE CHECKS THAT JUDGE COMMITS, NOT THE TREE. A recorded or shared pass is
# keyed on the tree, and two commits can carry one tree with different
# authors: the merge a Promote makes has exactly the tree its checked parents
# had. So these two run on every gate, reused pass or not -- they take about
# a second. On 2026-09-26 a Promote reused another checkout's pass for the
# same tree in four repositories, and the bot-authored merge commits it had
# just made went out unjudged; one of those repositories' own full sweep
# failed on its staging afterwards (practice: upstream-fix).
HISTORY_CHECKS = {'commit_author', 'commit_dates', 'session_trailer',
                  'leak_gate_commits'}
# session_trailer (2026-09-29): a repository that declares the shared set
# carrying check_session_trailer.py gets it materialized beside the other
# two, and it judges only the commits origin does not have yet -- what this
# push carries. Before, it ran only inside a full sweep, walked the whole
# history, and refused a consumer's Promote over one old commit on main;
# at the basic tier, --changed-files-only dropped its findings (they name no
# file), so nothing judged a commit at Booked at all.
# A check a practice SET ships reaches a repository on the set's own
# schedule, which is not the engine's (practice: vendor-rollout-disclosed,
# question 3). An engine that runs one at every push must not run a copy
# older than the push-time behaviour: {name: text only the new copy has}.
PUSH_TIME_SINCE = {'session_trailer': '--all-history'}
# precedent_update.py judges an update "as committed" by making a stand-in
# commit, running this, and undoing it. That commit's message, author and
# date are the tool's, not the ones the session's real commit will carry, so
# the checks that judge commits rather than files have nothing true to judge
# there: a set's session-trailer check refused every update over the
# stand-in's missing `Session:` line (2026-09-29). With this variable set,
# they stand aside and the push gate judges the real commit. An engine too
# old to know the variable ignores it and behaves as before.
STANDIN_COMMIT_ENV = 'PRECEDENT_STANDIN_COMMIT'
IDENTITY_NAMES = ('commit_author', 'commit_dates')
IDENTITY_CHECKS = (
    ('commit_author', ['{engine}/check_commit_author.py'],
     "precedent-individual's commit-identity.yml, retired 2026-09-21"),
    ('commit_dates', ['{engine}/check_commit_dates.py'],
     "precedent-individual's commit-identity.yml, retired 2026-09-21"),
    ('session_trailer', ['{engine}/checks/check_session_trailer.py'],
     'nothing -- the trailer was judged only inside a full sweep'),
)


def identity_slug(name, root):
    """-> the practice the identity check `name` enforces here, for
    not_binding: the practice in force whose checked_by names the engine's
    tools/check_<name>.py. The engine's two copies cite no practice -- theirs
    live in a person's own set, whose practice names the engine never
    carries (Morgan, 2026-10-16, strength: decided: "sets practice names
    should NOT be in BestPractice") -- and check_session_trailer.py,
    materialized, carries its own `# practice:` line."""
    try:
        sys.path.insert(0, str(HERE))
        import precedent_identity
        return precedent_identity.practice_checked_by(f'check_{name}.py', root)[0]
    except Exception:                                        # noqa: BLE001
        return None
    finally:
        sys.path.pop(0)
# Every workflow file is the engine's own untouched copy or carries the
# person's approval pinned to its content (practice: ci-workflow-approved).
# Every file a tool writes is current with its tool: basic tier
# (BASIC_CHECKS says why). The full sweep runs it too.
GENERATED_FILES_CHECK = (
    'generated_files', ['{engine}/precedent_check.py', '--only',
                        'generated-files-registered'],
    'nothing -- it ran only inside the full sweep')
# A reference left pointing at a path this branch renamed away: basic tier
# (BASIC_CHECKS says why). The full sweep runs it too.
RENAME_LINKS_CHECK = (
    'rename_links', ['{engine}/precedent_check.py', '--only',
                     'rename-updates-links'],
    'nothing -- it ran only inside the full sweep, at the landing')
CI_WORKFLOWS_CHECK = (
    'ci_workflows', ['{engine}/precedent_check.py', '--only',
                     'ci-workflow-approved'],
    'no workflow -- the check that keeps workflows from being added unasked')
# Entries a repo may simply not have: skipped with a note, never a failure.
OPTIONAL = {'deep_check', 'commit_author', 'commit_dates', 'session_trailer',
            'light_check', 'views_sync'}
# The BASIC tier: what a push to a working branch runs. Everything else
# in a kind's list is FULL-only. The leak gate is
# here because a push IS publication in a public repository, and cannot
# wait for promotion (Morgan, 2026-09-25: "Good on nothing private going
# out", strength: assented). Each costs seconds.
# ci_workflows is here because a workflow file starts billing the moment it
# reaches ANY branch GitHub runs it on; light_check is the repo's own fast
# check, and its secret scan wants every push (practice: ci-workflow-approved;
# Morgan, 2026-09-25, "we need to absolutely put a hard stop to this").
# build_views joins it for a practice set (2026-10-03, spec/
# GENERATED_FILES_PLAN.md step 4): a stale or hand-edited view used to pass
# every push and fail only at the Debut. It takes under a second.
# The practice audit's two checks join it for a consumer (2026-10-02): a
# classic install migrated onto the loader carried stale manifest baselines
# and no scrub blocklist, both full-tier findings, so its pushes
# passed and the first Debut failed on both. They run in seconds.
# generated_files joins a consumer's and a practice set's basic tier
# (2026-10-04): an Update Vendors that refreshed build_todo_index.py left
# todo/TODO.md stale, the push passed, and only the full
# check said so. Two seconds. Not upstream's: there precedent_check.py is
# full-only by design, and BestPractice's commit backstop rebuilds these.
# rename_links joins a consumer's and a practice set's basic tier
# (2026-10-08): a branch renamed a page and repointed the references a
# search for *.py and *.md found, but not a key in a tool's table or lines
# in two ledgers. Every push of the branch passed, and the landing's full
# check failed on them. It judges only what this branch renamed or deleted
# against its base -- a finding no push but this branch's could bring --
# and takes seconds.
#
# THE BASIC TIER IS CLOSED (Morgan, 2026-10-16, strength: decided: "LET'S
# BAN ALL NEW TESTS BEFOREHAND EXCEPT WHEN EXPLICITLY DIRECTLY VERBALLY
# AUTHORIZED"; spec/TESTS_RUN_AT_THE_DEBUT_PLAN.md; practice:
# quick-tier-is-closed). Everything that runs before a push is listed here
# as (the words that let it in, its time in seconds), and
# check_quick_tier_is_closed fails the moment BASIC_CHECKS and its list
# differ, an entry carries no quoted words and date, or a new entry carries
# no time. A new entry needs the person's own words asking for THIS check
# before a push, given after they were told its time and urged to put it
# at the Debut instead -- never a session's judgment that it is cheap.
# The fourteen below were in force when the tier was closed. A time is the
# one measured on 2026-10-16 here, or its own note above; the six this repo
# does not run (ci_workflows, light_check, views_sync, scrub_gate,
# practice_export_loop, rename_links) were measured on 2026-10-17 in two
# consuming repositories, three runs each, from the slower repo's median.
_IN_FORCE_AT_CLOSING = ('in force when Morgan closed the tier, 2026-10-16: '
                        '"all the testing EXCEPT THE BARE ESSENTIAL AND LEAK '
                        'GATES SHOULD GO INTO DEBUT"')
_LEAKS = 'Morgan, 2026-09-25: "Good on nothing private going out"'
_WORKFLOWS = 'Morgan, 2026-09-25: "we need to absolutely put a hard stop to this"'
BASIC_CHECKS_APPROVED = {
    'leak_gate': (_LEAKS, 16),
    'leak_gate_commits': (_LEAKS, 4),
    'ci_workflows': (_WORKFLOWS, 0),
    'light_check': (_WORKFLOWS, 0),
    'doc_lint': (_IN_FORCE_AT_CLOSING, 1),
    'commit_author': (_IN_FORCE_AT_CLOSING, 0),
    'commit_dates': (_IN_FORCE_AT_CLOSING, 0),
    'session_trailer': (_IN_FORCE_AT_CLOSING, 0),
    'build_views': (_IN_FORCE_AT_CLOSING, 1),
    'generated_files': (_IN_FORCE_AT_CLOSING, 2),
    'views_sync': (_IN_FORCE_AT_CLOSING, 2),
    'scrub_gate': (_IN_FORCE_AT_CLOSING, 1),
    'practice_export_loop': (_IN_FORCE_AT_CLOSING, 1),
    'rename_links': (_IN_FORCE_AT_CLOSING, 0),
}
BASIC_CHECKS = set(BASIC_CHECKS_APPROVED)
BASIC, FULL = 'basic', 'full'
# The commits a push would publish: everything HEAD has that no remote
# ref does (leak_gate.py's own documented form for a new branch).
LEAK_COMMITS_RANGE = 'HEAD --not --remotes'
# A PUSH TO A WORKING BRANCH IS JUDGED ON WHAT IT BRINGS (2026-09-28). A
# consumer session could not push its claude/* branch: commit_author refused
# over two old commits already on main, ci_workflows over a workflow file
# already on main, and the Stop hook refused to end the turn with the commit
# unpushed -- neither step could move until the person answered. Nothing
# about that push could fix either finding; main's history is published and
# is not rewritten. So on a push whose every destination is a working
# branch (no tier), a finding in these checks that is already on a tier
# branch on origin -- a commit that branch contains, or a finding the same
# check prints at the commit this push forked from -- is printed and does
# not refuse. A finding the push brings still refuses, and a push to a tier
# branch is judged exactly as before.
# views_sync joined 2026-10-06: a practice source this repository declares
# moved, every generated view went stale, and a one-line content push to a
# feature branch was refused for it. A stale view the fork point shows too
# is the source's doing, refreshed as a commit of its own at Booked
# (precedent_merge_vendors.py); a view this push edits by hand still refuses,
# and a push to a tier branch is judged exactly as before.
RANGE_JUDGED = {'commit_author', 'commit_dates', 'ci_workflows',
                'scrub_gate', 'practice_export_loop', 'views_sync'}
COMMIT_IN_FINDING = re.compile(r'\bcommit ([0-9a-f]{7,40})\b')
PUSH_CHECKS = {
    'upstream': (
        # --isolated (2026-09-29): the shards run in a clone with no
        # siblings, an empty $HOME and no source credentials -- what the
        # runner has -- and a check that could not run there runs here. It
        # cost 12.8 min against 18.3 for the plain run, in one container.
        # --because: the harness refuses a full run nobody asked for
        # (2026-10-07); this tier was asked for, by the push or the Promote.
        ('verify_harness', ['{engine}/verify_harness.py', '--as-ci',
                            '--isolated', '--because',
                            'precedent_push_check.py, full tier'],
         'deep-check.yml, its verify_harness --as-ci step'),
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'deep-check.yml, its precedent_check and doc_sync steps'),
        ('doc_sync', ['{engine}/doc_sync.py'],
         'deep-check.yml, its precedent_check and doc_sync steps'),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml (structural half only in CI)'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'docs.yml, retired 2026-09-21'),
        DEEP_CHECK_SUITE,
        *IDENTITY_CHECKS,
    ),
    'source': (
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'precedent-check.yml, retired 2026-09-21'),
        ('build_views', ['{engine}/build_views.py', '--repo', '.', '--check'],
         "precedent-check.yml's views-drift job, retired 2026-09-21"),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml, retired 2026-09-21'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'doc-lint.yml, retired 2026-09-21'),
        GENERATED_FILES_CHECK,
        RENAME_LINKS_CHECK,
        CI_WORKFLOWS_CHECK,
        DEEP_CHECK_SUITE,
        CONSUMER_SHAPE_SUITE,
        *IDENTITY_CHECKS,
    ),
    'consumer': (
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'light-check.yml'),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml (structural half only in CI)'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'bestpractice-docs.yml, retired 2026-09-21'),
        GENERATED_FILES_CHECK,
        RENAME_LINKS_CHECK,
        CI_WORKFLOWS_CHECK,
        # Whether the generated views still match the practice sources
        # (2026-10-03): a reduction pass retired practices in the shared sets,
        # a consumer's views were never re-synced, and nothing said so until a
        # Debut's full check -- whose message sent the session after missing
        # sources. Basic tier, so every push says it; sources
        # that cannot be resolved here are said and skipped, never failed.
        ('views_sync', ['{engine}/precedent_sync_views.py', '--repo', '.',
                        '--check', '--skip-unresolved'],
         'nothing -- a stale view surfaced only at the full check'),
        # Whether MAP.md and GLOSSARY.md still match their own sources
        # (2026-10-12): a session typed a row into a consumer's MAP.md
        # instead of MAP.source.md, every push of the branch passed, and the
        # next Update Vendors regenerated the map and erased the row without
        # a word. BASIC_CHECKS already named build_views for a practice set;
        # a consumer's views have their own sources too. Two seconds.
        ('build_views', ['{engine}/build_views.py', '--repo', '.', '--views-only', '--check'],
         'nothing -- a hand-edited view surfaced only when a rebuild erased it'),
        # The repo's OWN light check, where it has one: what its
        # light-check.yml ran on GitHub, run here instead of there.
        ('light_check', ['tools/light_check.py'],
         "the repo's own light-check.yml"),
        # The practice audit, at every tier (BASIC_CHECKS says why); also
        # inside the full sweep, where it always ran.
        ('scrub_gate', ['{engine}/precedent_check.py', '--only', 'scrub-gate'],
         'nothing -- it ran only inside the full sweep, at the Debut'),
        ('practice_export_loop', ['{engine}/precedent_check.py', '--only',
                                  'practice-export-loop'],
         'nothing -- it ran only inside the full sweep, at the Debut'),
        DEEP_CHECK_SUITE,
        *IDENTITY_CHECKS,
    ),
}


# WHAT A PASS HAS TO SHOW, beyond exit 0. The retired precedent-check.yml
# refused three shapes of "green" that verified nothing, each after it had
# happened for real; they are carried over here rather than lost with it.
def _guard_precedent_check(out, engine):
    m = re.search(r'^precedent_check: (\d+) passed', out, re.M)
    if not m:
        return ('no precedent_check summary line, so nothing says what it '
                'checked')
    if int(m.group(1)) == 0:
        return ('ZERO checks passed -- every one skipped or did not run, and '
                'a skip is not a pass')
    if repo_kind(engine) == 'source':
        # An engine from before binds_publishers skips, in a practice set,
        # the checks whose practice lives upstream, and still exits 0.
        p = subprocess.run(
            [sys.executable, '-c',
             'import sys; sys.path.insert(0, sys.argv[1]); '
             'import precedent_check as pc; '
             'sys.exit(0 if any(c.get("binds_publishers") for c in '
             'pc.CHECKS.values()) else 1)', str(engine)],
            capture_output=True, text=True)
        if p.returncode != 0:
            return ('the vendored engine predates binds_publishers, so in a '
                    'practice set it skips the checks that bind what this '
                    'repo publishes -- refresh it (precedent_vendor_engine.py '
                    'refresh)')
    return None


def _guard_build_views(out, engine):
    if 'NOT VERIFIABLE' in out:
        return ('the loader block is built from sources this machine cannot '
                'reach, so "no drift" was not established')
    return None


GUARDS = {'precedent_check': _guard_precedent_check,
          'build_views': _guard_build_views}


# A STAND-DOWN IS NOT A PASS, and says so. These tools exit 0 when they had
# nothing to inspect -- correctly, since failing would punish a state the
# repo chose -- but the line printed here used to read "passed" regardless,
# and the receipt recorded the same (very deep check, 2026-09-28). The
# marker is the tool's own wording; the note replaces "passed".
STAND_DOWNS = {'leak_gate': ('NOT APPLICABLE', 'stood down -- it inspected '
                             'nothing (a private repository)'),
               'leak_gate_commits': ('NOT APPLICABLE', 'stood down -- it '
                                     'inspected nothing (a private repository)'),
               'doc_lint': ('NOTHING IS BEING GATED', 'stood down -- no '
                            'Markdown file was in scope'),
               # The views were generated with a person's individual set,
               # and none resolves here (build_views.individual_not_verifiable).
               'views_sync': ('NOT VERIFIABLE', 'not verified -- the views '
                              'carry practices from an individual set this '
                              'machine cannot reach'),
               # practice_audit.EMPTY_BLOCKLIST (2026-10-13).
               'scrub_gate': ('BLOCKLIST IS EMPTY', 'not verified -- the '
                              'blocklist has no patterns, so nothing was '
                              'checked')}


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def repo_kind(engine=HERE):
    """-> 'upstream' | 'source' | 'consumer' | None. A vendored engine says
    its own kind in ENGINE_MANIFEST.json; BestPractice has no manifest,
    because it is where the engine comes from, and is the only repo
    carrying verify_harness.py (never vendored)."""
    manifest = engine / 'ENGINE_MANIFEST.json'
    if manifest.is_file():
        try:
            kind = json.loads(manifest.read_text(encoding='utf-8')).get('kind')
        except (OSError, ValueError):
            return None
        return kind if kind in PUSH_CHECKS else None
    if (engine / 'verify_harness.py').is_file():
        return 'upstream'
    return None


# A REPOSITORY'S OWN APPROVED WORKFLOWS RUN HERE TOO (2026-10-10). A consumer
# keeps workflows of its own through Update Vendors, recorded in
# precedent.json's github_ci_approved, and this list ran none of what they
# run: every local tier passed a change that platform-docs-check.yml then
# failed as GitHub's test on the pull request into main, a fix and a second
# Produce later. The workflow file stays the one record of its commands: each
# step that is a plain `python3 tools/<x>.py [args]` call runs here, in the
# full tier (the Debut and around Produce; never before a push, since
# 2026-10-17); a workflow the engine installs
# (ENGINE_MANIFEST's ci_workflow_files) is skipped, since this list already
# carries what it runs, and so is a step calling an engine file. Any other
# step is named by Update Vendors, once per update (the second answer of
# approved_workflow_checks), so nobody reads a pass as covering it.
#
# ONLY TESTS, NEVER THE PRODUCT (2026-10-10, a consumer whose workflows ARE
# its deliverable -- a live calendar sync run on GitHub with secrets). Its
# Update Vendors called every step of them a missed check and said to run it
# on every push, which would have run the live sync on every push. So a
# workflow counts only when GitHub runs it on a change (push, pull_request,
# merge_group), never one an entry marks `"role": "deliverable"`; a step
# counts only when it looks like a check (its name or command says check,
# test, lint, audit, verify or validate); and a step reading GitHub's own
# environment (`$VAR`) is never run here, only named.
APPROVED_WORKFLOWS_KEY = 'github_ci_approved'
DELIVERABLE_ROLE = 'deliverable'
_LOCAL_STEP_RE = re.compile(r'^(python3?)\s+(tools/[\w./-]+\.py)(\s.*)?$')
_CHECK_LIKE_RE = re.compile(
    r'(?<![a-z])(check|checks|checker|test|tests|lint|linter|audit|verify|'
    r'validate|validation|phpunit|pytest|unittest|doc_lint)(?![a-z])', re.I)
_CHANGE_EVENTS = {'push', 'pull_request', 'pull_request_target', 'merge_group'}
_SETUP_STEP_RE = re.compile(r'^(?:python3?\s+-m\s+pip|pip3?|echo|set|cd|export|git\s+config|true)\b')


def _workflow_steps(text):
    """-> [(step name, command, condition)] for every `run:` line in a
    workflow, a block's lines one by one; `condition` is the step's own
    `if:`, '' when it has none. Read line by line, not as YAML: nothing here
    may need PyYAML, and a run step's shape is regular enough."""
    out, name, cond, block, indent = [], '', '', False, 0
    for line in text.splitlines():
        stripped = line.strip()
        lead = len(line) - len(line.lstrip())
        if block:
            if stripped and lead <= indent:
                block = False
            elif stripped and not stripped.startswith('#'):
                out.append((name, stripped, cond))
                continue
            else:
                continue
        if re.match(r'^\s*-\s+[\w-]+:', line):        # a new step begins
            name, cond = '', ''
        m = re.match(r'^\s*-?\s*name:\s*(.+?)\s*$', line)
        if m:
            name = m.group(1).strip('"\'')
        m = re.match(r'^\s*-?\s*if:\s*(.+?)\s*$', line)
        if m:
            cond = m.group(1)
        m = re.match(r'^(\s*)-?\s*run:\s*(.*?)\s*$', line)
        if m:
            if m.group(2) in ('|', '>', '|-', '>-'):
                block, indent = True, len(m.group(1))
            elif m.group(2):
                out.append((name, m.group(2), cond))
    return out


def _workflow_commands(text):
    """-> [(step name, command)] for every `run:` line (_workflow_steps)."""
    return [(n, c) for n, c, _ in _workflow_steps(text)]


# A STEP NO CHANGE CAN RUN IS NO TEST OF ONE (2026-10-10, a consumer's
# product workflow). Its alarm drill files a todo item and opens an issue
# only when the job has already failed, and only when started by hand with
# an input set; the detector counted both as GitHub-only checks because
# their names said "alerting test". A step whose `if:` runs it only after a
# failure (failure() or cancelled(), and not always()), or only on a manual
# input (inputs.X required, never negated or or-ed), is skipped.
def _never_tests_a_change(cond):
    c = (cond or '').replace(' ', '')
    if not c:
        return False
    if re.search(r'\b(?:failure|cancelled)\(\)', c) and 'always()' not in c \
            and not re.search(r'\bsuccess\(\)', c):
        return True
    return bool(re.search(r'(?<![!\w.])inputs\.\w+', c)) and '||' not in c


def _unquoted(cmd):
    """-> `cmd` with its quoted strings blanked: words a script prints or
    stores are not what it runs (2026-10-10: "Commit state" matched on
    'file the alerting test as a todo item', a string it appends)."""
    return re.sub(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'', ' ', cmd)


def _workflow_events(text):
    """-> the set of events a workflow's `on:` names, or None when there is
    no `on:` to read (then it is treated as running on a change)."""
    events, seen, inside = set(), False, False
    for line in text.splitlines():
        body = line.split(' #', 1)[0].rstrip()
        if not body.strip() or body.lstrip().startswith('#'):
            continue
        ind = len(body) - len(body.lstrip(' '))
        if ind == 0:
            m = re.match(r'["\']?on["\']?:\s*(.*)$', body)
            inside = bool(m) and not m.group(1).strip()
            if m:
                seen = True
                events |= set(re.findall(r'[\w-]+', m.group(1)))
            continue
        if inside and ind == 2:
            m = re.match(r'\s*-?\s*["\']?([\w-]+)["\']?', body)
            if m:
                events.add(m.group(1))
    return events if seen else None


def _local_argv(cmd):
    """-> the argv of a `python3 tools/<x>.py ARGS` line, quoted arguments
    unquoted, or None when it is not one, cannot be split, or reads
    GitHub's environment ($VAR), which only GitHub has."""
    m = _LOCAL_STEP_RE.match(cmd)
    if not m or '$' in cmd or '`' in cmd:
        return None
    try:
        import shlex
        rest = shlex.split(m.group(3) or '')
    except ValueError:
        return None
    if any(t in ('|', '||', '&&', ';', '>', '>>', '<') or t.startswith(('>', '<', '|'))
           for t in rest):
        return None
    return [m.group(2), *rest]


def approved_workflow_checks(root):
    """-> (checks, unrun): `checks` [(name, argv, replaces)] for each local
    step of each workflow precedent.json's github_ci_approved keeps; `unrun`
    [(workflow, step, command)] for the steps this cannot run here."""
    root = Path(root)
    try:
        approved = json.loads((root / 'precedent.json').read_text(
            encoding='utf-8')).get(APPROVED_WORKFLOWS_KEY) or {}
    except (OSError, ValueError, AttributeError):
        return [], []
    try:
        man = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json').read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        man = {}
    engine_wf = set(man.get('ci_workflow_files') or [])
    try:                    # the engine's own workflows, by name, whatever an
        import precedent_vendor_engine as _pve      # older manifest recorded
        engine_wf |= {d for rows in _pve.CI_WORKFLOW_TEMPLATES.values()
                      for _t, d in rows}
    except Exception:                                          # noqa: BLE001
        pass
    engine_tools = {f'tools/{f}' for f in man.get('files') or []}
    checks, unrun = [], []
    for rel in sorted(approved if isinstance(approved, dict) else []):
        wf = root / rel
        entry = approved.get(rel)
        if rel in engine_wf or not wf.is_file() or (
                isinstance(entry, dict) and entry.get('role') == DELIVERABLE_ROLE):
            continue
        text = wf.read_text(encoding='utf-8', errors='replace')
        events = _workflow_events(text)
        if events is not None and not events & _CHANGE_EVENTS:
            continue            # a button or a schedule: never a change's test
        for step, cmd, cond in _workflow_steps(text):
            if _never_tests_a_change(cond):
                continue
            if not (_CHECK_LIKE_RE.search(step) or _CHECK_LIKE_RE.search(_unquoted(cmd))):
                continue
            argv = _local_argv(cmd)
            if argv:
                if argv[0] in engine_tools:
                    continue
                checks.append((f'workflow {Path(rel).name}: {argv[0]}',
                               [sys.executable, *argv],
                               f'its step "{step}" on GitHub'))
            elif not _SETUP_STEP_RE.match(cmd) and \
                    not any(u[:2] == (rel, step) for u in unrun):
                unrun.append((rel, step, cmd))       # one line per step
    return checks, unrun


def plan(root, engine=HERE, tier=FULL):
    """-> (kind, [(name, argv, replaces)]) with {engine} resolved relative
    to `root`, so the commands print the way a person would type them.
    `tier` BASIC keeps only BASIC_CHECKS."""
    kind = repo_kind(engine)
    if kind is None:
        return None, []
    rel = engine.relative_to(root) if engine.is_relative_to(root) else engine
    out = []
    for name, argv, replaces in PUSH_CHECKS[kind]:
        if tier == BASIC and name not in BASIC_CHECKS:
            continue
        argv = [a.replace('{engine}', str(rel)) for a in argv]
        if argv[0].endswith('.py'):
            argv = [sys.executable, *argv]
        out.append((name, argv, replaces))
        # A push publishes every commit it carries, not only the tree they
        # end at. 2026-10-10: one commit named a private repository in a
        # test, the next scrubbed it, the tree passed, and the first commit
        # went out to a public branch with the name in it. So the leak gate
        # also walks the commits no remote has yet, messages included.
        if name == 'leak_gate':
            out.append(('leak_gate_commits',
                        [*argv, '--range', LEAK_COMMITS_RANGE],
                        'nothing: the tree check alone let a commit that a '
                        'later one scrubbed go out (2026-10-10)'))
    # A workflow step calling a tool this list already runs is left to this
    # list, which owns its tier: BestPractice's own deep-check.yml runs the
    # full suite, which a basic push must not.
    # A repository's own workflow checks are tests, so they run in the full
    # tier: at the Debut, never before an ordinary push. A push to the
    # staging tier gets them in the basic tier too, inside a budget
    # (own_checks_before_staging, 2026-10-19). Until
    # 2026-10-17 they ran at every tier, outside BASIC_CHECKS, where the
    # closed quick tier could not see them (Morgan, 2026-10-16: "all the
    # testing EXCEPT THE BARE ESSENTIAL AND LEAK GATES SHOULD GO INTO DEBUT";
    # found by the very deep check's CHECKS BY STAGE).
    if tier == BASIC:
        return kind, out
    planned = {Path(a[0].replace('{engine}', str(rel))).as_posix()
               for _n, a, _r in PUSH_CHECKS[kind] if a}
    out.extend(c for c in approved_workflow_checks(root)[0]
               if Path(c[1][1]).as_posix() not in planned)
    return kind, out


# A REPOSITORY'S OWN CHECKS RUN BEFORE STAGING, INSIDE A BUDGET (2026-10-19).
# Since 2026-10-17 a push or merge into main takes the basic tier, so a
# repository's own approved workflow steps ran only at the Debut, and two
# consuming repositories' Produce merged a change their own pull-request
# check (platform-docs-check.yml) was certain to fail. Those steps are what
# GitHub runs on that pull request, and each measured under 0.2s that day,
# so the quick checks for a push to the staging tier run them too: a change
# meets them before it is shared at all, and GitHub's test still runs after
# it is live on main. Morgan, the same day (strength: decided): "let's run
# them ... before it's even pushed to staging", not during the push to main.
# And earlier:
# "I want to prevent the problem that happened before. We had one little
# check, then another little check ... So it goes back to being from seconds
# to minutes." Hence the budget: together they get OWN_CHECKS_BUDGET_SECONDS,
# split evenly; one that runs past its share is stopped, said, and left to
# GitHub, never counted as a failure, so no slow step added later can turn
# Produce back into minutes.
OWN_CHECKS_BUDGET_SECONDS = 10
_BUDGET_RUNNER = (
    'import subprocess, sys\n'
    't = float(sys.argv[1])\n'
    'try:\n'
    '    sys.exit(subprocess.run(sys.argv[2:], timeout=t).returncode)\n'
    'except subprocess.TimeoutExpired:\n'
    '    print(f"ran past its {t:g}s share of the budget for a push to staging; '
    'stopped and left to GitHub")\n')


def _staging_name(root):
    """-> the staging tier's branch name in `root`, or 'staging'."""
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
        return precedent_branches.staging_branch(root)
    except Exception:                                        # noqa: BLE001
        return 'staging'
    finally:
        sys.path.pop(0)


def script_arg(argv):
    """-> the script `argv` runs: argv[1], or, for a step own_checks_before_
    staging wrapped in its budget runner, the script inside the wrapper.
    Reading argv[1] of a wrapped step looked for a file named "-c" and
    reported every repository's own checks as "could not run here"
    (2026-10-20, Update All Vendors; seen in this repository too)."""
    if len(argv) > 5 and argv[1] == '-c' and argv[2] == _BUDGET_RUNNER:
        return argv[5]
    return argv[1]


def own_checks_before_staging(root, engine=HERE, planned=()):
    """-> approved_workflow_checks(root), minus a tool `planned` already
    runs, each wrapped to stop at its share of OWN_CHECKS_BUDGET_SECONDS."""
    planned = {Path(a).as_posix() for a in planned}
    own = [c for c in approved_workflow_checks(root)[0]
           if Path(c[1][1]).as_posix() not in planned]
    if not own:
        return []
    share = round(max(OWN_CHECKS_BUDGET_SECONDS / len(own), 1.0), 1)
    return [(name, [sys.executable, '-c', _BUDGET_RUNNER, str(share), *argv],
             f'{replaces}, before staging (at most {share:g}s)')
            for name, argv, replaces in own]


def shown_interpreter(argv):
    return 'python3' if argv[0] == sys.executable else argv[0]


def signature(checks):
    return hashlib.sha256(json.dumps(
        [[n, a[1:]] for n, a, _ in checks]).encode()).hexdigest()[:16]


def record_path(root):
    p = git(root, 'rev-parse', '--git-path', RECORD)
    return (root / p) if p else None


# A FAILED TREE IS NOT PUSHED (2026-10-10). A session working in a
# repository it was not started in loads none of that repository's harness
# hooks, push-check-gate.sh among them, and pushed a branch right after this
# tool had printed "FAILED ... do not push past it". Nothing stopped it. A
# failure is now written down against the tree it judged, in the git
# directory every worktree shares, and the global pre-push hook
# (commit-identity.sh, _write_pre_push) refuses a push of that tree, from
# any repository, under any harness. A pass of the same tree clears it. The
# hook runs no check itself: on a ladder push it would re-run the full
# suite a session's own gate has already run.
FAILED_TREES = 'precedent-push-check-failed.json'
FAILED_TREES_KEPT = 50


def failed_trees_path(root):
    p = git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    return Path(p) / FAILED_TREES if p else None


def _failed_trees(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def note_failed_tree(root, tree, failed):
    """Record that `tree` failed `failed` (check names). Never raises."""
    path = failed_trees_path(root)
    if not (tree and path):
        return
    try:
        data = _failed_trees(path)
        data.pop(tree, None)
        data[tree] = {'failed': list(failed),
                      'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        keep = dict(list(data.items())[-FAILED_TREES_KEPT:])
        path.write_text(json.dumps(keep, indent=2) + '\n', encoding='utf-8')
    except OSError:
        pass


def clear_failed_tree(root, tree):
    """A pass of `tree` clears any failure recorded for it. Never raises."""
    path = failed_trees_path(root)
    if not (tree and path and path.is_file()):
        return
    data = _failed_trees(path)
    if data.pop(tree, None) is not None:
        try:
            path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        except OSError:
            pass


def dirty_paths(root):
    """-> the repo-relative tracked paths with uncommitted changes (both
    sides of a rename), or None when git cannot say."""
    p = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '-z',
                        '--untracked-files=no'], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    out, parts = set(), p.stdout.split('\0')
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.add(entry[3:])
        if entry[0] in 'RC' or entry[1] in 'RC':
            if i < len(parts) and parts[i]:
                out.add(parts[i])
            i += 1
    return out


def clean_tree(root, ledgers=()):
    """-> the HEAD tree hash when nothing tracked is uncommitted, else None.
    A run over uncommitted edits checked something the push will not send,
    so it is never recorded as a pass for the commit.

    `ledgers`: fact-ledger files (practice: gate-ledger) whose uncommitted
    state does not count. A ledger only caches facts that verify themselves
    -- a stale or foreign line costs one re-run, never a skipped unit -- so
    no verdict depends on its working copy, and the push sends the
    committed one. Without this the check dirtied the very tree it judged:
    the model audit refreshed its ledger as it ran, and a 799 s pass was
    never recorded, so the push gate ran the suite again and timed out
    (consumer repo, 2026-10-02)."""
    dirty = dirty_paths(root)
    if dirty is None or not dirty <= set(ledgers):
        return None
    return git(root, 'rev-parse', 'HEAD^{tree}')


def known_ledgers(root):
    """The fact-ledger paths an earlier run here saw the ledger engine
    write, kept in the local record; empty when there is none."""
    path = record_path(root)
    try:
        rec = json.loads(path.read_text(encoding='utf-8')) if path else {}
    except (OSError, ValueError):
        return []
    got = rec.get('ledgers') if isinstance(rec, dict) else None
    return [x for x in got if isinstance(x, str)] if isinstance(got, list) else []


def ledgers_written(root, listing):
    """The repo-relative ledger paths fact_ledger.py reported saving into
    `listing` (its WRITTEN_ENV file) during the run."""
    try:
        lines = Path(listing).read_text(encoding='utf-8').splitlines()
    except OSError:
        return set()
    base, out = Path(root).resolve(), set()
    for ln in lines:
        try:
            out.add(Path(ln.strip()).resolve().relative_to(base).as_posix())
        except ValueError:
            continue                  # a ledger in some other repository
    return out


def already_passed(root, checks, also=()):
    """The record, when this tree's recorded pass covers `checks` -- or any
    of the check lists in `also`, which is how a FULL pass satisfies a BASIC
    gate -- else None. The record names the list it passed by signature, so
    a BASIC pass can never satisfy a FULL gate."""
    tree = clean_tree(root, known_ledgers(root))
    path = record_path(root)
    if not tree or not path or not path.is_file():
        return None
    try:
        rec = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    accepted = {signature(checks), *(signature(c) for c in also)}
    if rec.get('tree') == tree and rec.get('checks') in accepted:
        return rec
    return None


def _shared_off(root):
    if (os.environ.get('PRECEDENT_NO_SHARED_PASS') == '1'
            or not git(root, 'remote', 'get-url', 'origin')):
        return True
    # AN EMPTY ORIGIN GETS NO RECEIPT BRANCH (2026-09-28). The first branch
    # pushed to an empty GitHub repository becomes its default branch, and
    # on a fresh install the push gate runs before the first `git push` --
    # so the receipt branch would be the repository's first, and default,
    # branch. Unreachable is not empty: only a clean, empty answer counts.
    r = _git_env(root, ['ls-remote', '--heads', 'origin'], 15)
    return r is not None and r.returncode == 0 and not r.stdout.strip()


def _git_env(root, args, timeout, env=None):
    try:
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                              text=True, timeout=timeout,
                              env=dict(os.environ, **(env or {})))
    except (OSError, subprocess.TimeoutExpired):
        return None


def _fetch_receipts(root, branch=None):
    """-> the receipt branch's tip, fetched into a private ref, or None."""
    branch = branch or _receipt_branch(root)
    f = _git_env(root, ['fetch', '-q', '--no-tags', 'origin',
                        f'+refs/heads/{branch}:{RECEIPT_REF}'], 30)
    if f is None or f.returncode != 0:
        return None
    return git(root, 'rev-parse', '-q', '--verify', RECEIPT_REF) or None


def shared_pass(root, tree, sigs):
    """The record another checkout published to origin for `tree` under any
    of the check-list signatures `sigs`, else None. Never raises: a remote
    that cannot be reached is a pass not found, and the suite runs."""
    if not tree or _shared_off(root) or not _fetch_receipts(root):
        return None
    for sig in sigs:
        body = git(root, 'cat-file', '-p', f'{RECEIPT_REF}:receipts/{sig}/{tree}.json')
        if body:
            try:
                rec = json.loads(body)
            except ValueError:
                continue
            if rec.get('tree') == tree and rec.get('checks') == sig:
                return rec
    return None


def publish_pass(root, rec):
    """Add a recorded pass to the receipt branch on origin, for every other
    checkout. Best effort: a failure is said and never fails the run that
    passed. Two windows writing at once is a rejected push, retried on the
    newer tip."""
    if _shared_off(root):
        return
    path = f'receipts/{rec["checks"]}/{rec["tree"]}.json'
    index = git(root, 'rev-parse', '--git-path', 'precedent-receipts.index')
    if not index:
        return
    env = dict(SHARED_ENV, GIT_INDEX_FILE=str(
        Path(index) if Path(index).is_absolute() else root / index))
    why = 'no attempt made'
    branch = _receipt_branch(root, write=True)
    for _ in range(3):
        tip = _fetch_receipts(root, branch)
        _git_env(root, ['read-tree', tip or '--empty'], 10, env)
        order = (git(root, 'cat-file', '-p', f'{tip}:ORDER') if tip else '') or ''
        order = [l for l in order.splitlines() if l and l != path] + [path]
        blob = subprocess.run(['git', '-C', str(root), 'hash-object', '-w', '--stdin'],
                              input=json.dumps(rec, indent=2, sort_keys=True) + '\n',
                              capture_output=True, text=True).stdout.strip()
        olist = subprocess.run(['git', '-C', str(root), 'hash-object', '-w', '--stdin'],
                               input='\n'.join(order[-RECEIPTS_KEPT:]) + '\n',
                               capture_output=True, text=True).stdout.strip()
        for old in order[:-RECEIPTS_KEPT]:
            _git_env(root, ['update-index', '--force-remove', old], 10, env)
        _git_env(root, ['update-index', '--add', '--cacheinfo',
                        f'100644,{blob},{path}'], 10, env)
        _git_env(root, ['update-index', '--add', '--cacheinfo',
                        f'100644,{olist},ORDER'], 10, env)
        tree = _git_env(root, ['write-tree'], 10, env)
        if tree is None or tree.returncode != 0:
            why = 'could not build the receipt'
            break
        # [skip ci]: a workflow that runs on every branch push must not
        # bill a run for a receipt.
        c = _git_env(root, ['commit-tree', tree.stdout.strip(),
                            *(['-p', tip] if tip else []), '-m',
                            f'[skip ci] receipt: {rec["tier"]} check passed on '
                            f'tree {rec["tree"][:12]}'], 10, SHARED_ENV)
        if c is None or c.returncode != 0:
            why = 'could not build the receipt'
            break
        # --no-verify: a pre-push hook here is this very check.
        p = _git_env(root, ['push', '-q', '--no-verify', 'origin',
                            f'{c.stdout.strip()}:refs/heads/{branch}'], 60)
        if p is not None and p.returncode == 0:
            _git_env(root, ['update-ref', RECEIPT_REF, c.stdout.strip()], 10)
            # SAY THE PUSH (2026-10-17). A check that writes to origin is
            # rare enough that a reader of the run must see it in plain
            # words: what was pushed, where, and how to stop it.
            print(f'precedent_push_check: pushed a pass receipt to {branch} '
                  f'on origin, so no other checkout re-runs these files '
                  f'(PRECEDENT_NO_SHARED_PASS=1 turns this off).')
            return
        why = p.stderr.strip()[:200] if p is not None else 'timed out'
    print(f'precedent_push_check: NOTE -- could not push the pass receipt to '
          f'{branch} on origin ({why}); other checkouts will run the suite '
          f'themselves.')


def _promote_only_refusal(root, argv):
    """-> why the named push is refused before any check runs, or None.
    Only a person who turned promote_only on is ever refused here
    (precedent_branches.direct_push_refusal); an engine too old to know the
    setting refuses nothing."""
    if '--push-command' not in argv:
        return None
    i = argv.index('--push-command')
    cmd = argv[i + 1] if i + 1 < len(argv) else ''
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
    except ImportError:
        return None
    finally:
        sys.path.pop(0)
    refusal = getattr(precedent_branches, 'direct_push_refusal', None)
    return refusal(root, cmd) if refusal else None


# The practice checks, on the files a push CHANGES, and
# nothing else (Morgan, 2026-09-27, strength: decided: "ONLY for files that
# changed (or were added) in that session ... NOT for every file in the
# repo"). A push to the landing branch takes the quick tier, so a document
# whose title and first heading disagreed went straight onto it and was
# caught only by the next Promote's full check. The practice checks take
# seconds; the test suite, which is what makes the full check slow, still
# waits for the full tier.
# What a step prints when a session-load size cap is exceeded but not
# refused: precedent_check.py's quick-check WARNING, build_views.py's.
SIZE_CAP_WARNINGS = ('over a size cap. The quick check',
                     'build_views WARNING:')
CAP_WARNED = []           # the steps that printed one, this run
CAP_DETAILS = []          # what each said: file, measure and limit
_CAP_BLOCK = re.compile(r'^WARNING\s+(\S+)\s+\S+\s+over a size cap')


def _cap_details(text):
    """-> one short line per cap a step's output says is over: the file, its
    measured size and its limit, in the check's own words, cut at the first
    sentence. The findings under precedent_check.py's WARNING block, and
    build_views.py's own WARNING line.

    WHY (2026-10-08, from a consumer's Update Vendors). The closing line
    said only "over a session-load size cap (changed_practice, above)": a
    passing step's output is never printed, so "above" pointed at nothing,
    and the person was told a cap was over without which file, how far, or
    which limit."""
    got, block = [], False
    for line in text.splitlines():
        if _CAP_BLOCK.match(line):
            block = True
            continue
        if block and line.startswith('    ') and line.strip():
            got.append(re.split(r'\. | -- ', line.strip(), maxsplit=1)[0])
            continue
        block = False
        if line.startswith('build_views WARNING:') and 'Written anyway' in line:
            msg = line[len('build_views WARNING:'):].split(' Written anyway')[0]
            got.append('the AGENTS.md loader block: '
                       + re.split(r'\. | -- ', msg.strip(), maxsplit=1)[0])
    return list(dict.fromkeys(got))


def _cap_warning_last(tier=None):
    """Say it last, where the push gate's short tail of a pass shows it:
    a size cap is over, allowed at the quick check, refused at the Debut
    (Morgan, 2026-09-30: warn at the quick check, no change for staging).
    One line that carries the file, its size, the limit and the check that
    measured it, since Update Vendors repeats this line and nothing else."""
    if not CAP_WARNED:
        return
    what = '; '.join(CAP_DETAILS) or 'the step did not say which file'
    by = (f'measured by the {tier} check\'s {", ".join(CAP_WARNED)} step'
          if tier else f'measured by the {", ".join(CAP_WARNED)} step')
    head = f'WARNING: over a session-load size cap -- {what} ({by}).'
    if _ladder_off():
        print(f'{head} Allowed onto this branch; the full check refuses it, '
              f'so bring it under first (a Reduction pass). Tell the person.')
    else:
        print(f'{head} Allowed onto your landing branch; the full check '
              f'(Debut, or Produce into main) refuses it, so bring it under '
              f'first (a Reduction pass). Tell the person.')




# The file-level checks on the same changed files (Morgan, 2026-09-27,
# strength: decided: "these ones only check the individual files and ...
# the files that need to be generated. Nothing more than that"). Each looks
# only at a file the push created or changed, or at the generated files a
# changed practice feeds -- never at the rest of the repository:
#   - a changed Python file compiles;
#   - a changed shell script parses (bash -n);
#   - a changed JSON file parses;
#   - a changed check's tests are named, and run at the Debut (TESTS RUN
#     AT THE DEBUT, below), never here;
#   - a new check has that test, and defines SOURCE_ROOT;
#   - in BestPractice, a change to the check registry or the harness leaves
#     every registered check with a planted case (a text read, no harness
#     run -- see _unplanted_checks);
#   - a changed practice file's generated views (AGENTS.md, MAP.md,
#     GLOSSARY.md) were regenerated with it -- in a repository whose own
#     views build_views.py renders, which is BestPractice and a practice set.
# A push sends commits that already exist, so this can only refuse, never
# regenerate: it names the command that does.
CHANGED_FILES_CHECK = ('changed_files',
                       'the changed files compile or parse, and a changed '
                       'practice regenerated its views')


def _changed_paths(root, since, kinds='AMR'):
    out = git(root, 'diff', '--name-only', f'--diff-filter={kinds}', f'{since}...HEAD')
    return [l for l in (out or '').splitlines() if l.strip()]


def _is_engine_check(root, rel):
    """True for a check script the engine itself ships: BestPractice's own
    tools/checks/, or one a vendored engine's ENGINE_MANIFEST.json lists."""
    engine = HERE.relative_to(root) if HERE.is_relative_to(root) else None
    if engine is None or not rel.startswith(f'{engine}/checks/'):
        return False
    if repo_kind(HERE) == 'upstream':
        return True
    try:
        files = json.loads((HERE / 'ENGINE_MANIFEST.json').read_text(
            encoding='utf-8')).get('files') or []
    except (OSError, ValueError):
        return False
    return rel[len(f'{engine}/'):] in files


# Every check precedent_check.py registers needs a planted case in
# verify_harness.py's check_precedent_check_fires -- the harness asserts it
# ("every registered check has a planted case here"), but only on a full
# run, which a basic-tier push never does. On 2026-09-29 a new check
# landed without one, the session ran only the harness cases its
# change touched, and the Debut to staging failed 20 minutes in. This reads
# the same two sets as text, in well under a second, whenever a change
# touches either side. The cause itself -- a check's case living in a
# second, much larger file -- is a todo item
# (todo/todo-2026-09-29-planted-case-lives-beside-its-check.md).
_CHECK_REG_RE = re.compile(r"""^@check\(\s*['"]([\w-]+)['"]""", re.M)
_CASE_RE = re.compile(r"""\bcase\(\s*['"]([\w-]+)['"]""")
_CHECKED_BY_RE = re.compile(r"""^checked_by:\s*['"]?([^'"\s#]+)""", re.M)
_CHECK_SCRIPT_DIRS = ('tools/checks', 'local/tools/checks')


def _unplanted_checks(root):
    """-> sorted slugs registered here with no `case('<slug>', ...)` in
    tools/verify_harness.py: every @check in tools/precedent_check.py, and
    every check_*.py script precedent_check.register_materialized_checks()
    would add (named by the practice whose checked_by claims it, else by its
    stem -- the same naming). [] where either file is missing."""
    pc, vh = root / 'tools' / 'precedent_check.py', root / 'tools' / 'verify_harness.py'
    if not (pc.is_file() and vh.is_file()):
        return []
    registered = set(_CHECK_REG_RE.findall(pc.read_text(encoding='utf-8',
                                                        errors='replace')))
    claimed = {}
    for d in ('practices', 'local/practices'):
        for f in sorted((root / d).glob('*.md')):
            m = _CHECKED_BY_RE.search(f.read_text(encoding='utf-8',
                                                  errors='replace')[:4000])
            if m and m.group(1).endswith('.py') and '/checks/' in m.group(1):
                claimed.setdefault(Path(m.group(1)).name, f.stem)
    for d in _CHECK_SCRIPT_DIRS:
        for script in sorted((root / d).glob('check_*.py')):
            slug = claimed.get(script.name, script.stem)
            registered.add(slug)
    declared = set(_CASE_RE.findall(vh.read_text(encoding='utf-8',
                                                 errors='replace')))
    return sorted(registered - declared)


def _front_matter_changed(root, since, rel):
    """True when practice file `rel`'s front matter differs from `since`'s
    copy (or it had none there)."""
    def head(text):
        parts = (text or '').split('\n---', 1)
        return parts[0] if text.startswith('---') else ''
    before = git(root, 'show', f'{since}:{rel}') or ''
    try:
        now = (root / rel).read_text(encoding='utf-8')
    except OSError:
        return False
    return head(before) != head(now)


_CHECK_PAIR_RE = re.compile(
    r'(?:(.*)/)?tools/checks/(?:check_(\w+)\.py|tests/test_(\w+)\.sh)$')


def _check_script_tests(root, files):
    """-> the tests/test_*.sh a change to `files` runs: each changed check's
    or test's own, and every test that names a changed check."""
    tests = []
    for rel in files:
        m = _CHECK_PAIR_RE.match(rel)
        if not m:
            continue
        base = f'{m.group(1)}/' if m.group(1) else ''
        name = m.group(2) or m.group(3)
        test = f'{base}tools/checks/tests/test_{name}.sh'
        materialized = f'tools/checks/tests/test_{name}.sh'
        if base and (root / materialized).is_file():
            test = materialized
        if test not in tests and (root / test).is_file():
            tests.append(test)
        # A TEST THAT NAMES THE CHECK RUNS TOO (2026-10-11). Two scripts can
        # share one test -- the philosophy pair shares
        # test_philosophy_scoping.sh -- and pairing by file name alone ran
        # no test for either. A check's test must name it (check_deep_check.py),
        # so reading the tests for that name finds every one, with no map
        # to keep.
        if m.group(2):
            for other in sorted((root / f'{base}tools/checks/tests').glob('test_*.sh')):
                if f'check_{name}.py' not in other.read_text(encoding='utf-8',
                                                             errors='replace'):
                    continue
                found = f'{base}tools/checks/tests/{other.name}'
                if base and (root / f'tools/checks/tests/{other.name}').is_file():
                    found = f'tools/checks/tests/{other.name}'
                if found not in tests:
                    tests.append(found)
    return tests


def _new_tests_have_times(root, since, files, problems):
    """A harness test this change adds carries its recorded time (Morgan,
    2026-10-16: "The new heavy tests should be in the batch of tests as they
    land on the branch"). A text read of the diff and the timing list --
    no test runs here; the command it names times only the new ones."""
    if 'tools/verify_harness.py' not in files:
        return
    diff = git(root, 'diff', '-U0', f'{since}...HEAD', '--',
               'tools/verify_harness.py') or ''
    added = re.findall(r'^\+def (check_\w+)\(', diff, re.M)
    try:
        known = json.loads((root / 'tools' / 'harness_check_times.json')
                           .read_text(encoding='utf-8')).get('seconds') or {}
    except (OSError, ValueError):
        known = {}
    missing = [n for n in added if n not in known]
    if missing:
        problems.append(
            f'tools/verify_harness.py adds {len(missing)} test(s) with no '
            f'recorded time ({", ".join(missing)}) -- run `python3 '
            f'tools/verify_harness.py --record-new-times` and commit '
            f'tools/harness_check_times.json with them')


def changed_files_check(root, since):
    """-> 0 when every file the change touches is sound, 1 with each
    problem named. Reads nothing but the changed files, and the views a
    changed practice feeds."""
    files = _changed_paths(root, since)
    problems = []
    for rel in files:
        path = root / rel
        if not path.is_file():
            continue
        if rel.endswith('.py'):
            try:
                compile(path.read_text(encoding='utf-8'), rel, 'exec')
            except (SyntaxError, ValueError, UnicodeDecodeError) as e:
                problems.append(f'{rel}: does not compile -- {e}')
        elif rel.endswith('.sh'):
            r = subprocess.run(['bash', '-n', str(path)], capture_output=True,
                               text=True)
            if r.returncode != 0:
                problems.append(f'{rel}: does not parse -- '
                                f'{(r.stderr or r.stdout).strip()[:300]}')
        elif rel.endswith('.json'):
            try:
                json.loads(path.read_text(encoding='utf-8'))
            except (ValueError, UnicodeDecodeError) as e:
                problems.append(f'{rel}: is not valid JSON -- {e}')
    # A changed check, or a changed test, runs that check's own test: the
    # pair is tools/checks/check_x.py and tools/checks/tests/test_x.sh.
    #
    # ONE COPY OF EACH TEST. In a consuming repo a repo-local check lives in
    # local/tools/checks/ and is materialized, byte for byte, into
    # tools/checks/; both copies change together, and this used to run both.
    # A test's `cd "$(dirname "$0")/../../.."` lands in local/ from the first
    # and the repo root from the second, so a test written for one location
    # failed from the other -- only here, never in run_all.sh, which runs the
    # materialized copy alone (a consumer report, 2026-09-28). The
    # materialized copy is what the deep check runs, so it is what runs here.
    tests = _check_script_tests(root, files)
    added = set(_changed_paths(root, since, 'A'))
    judged = set()
    for rel in files:
        m = _CHECK_PAIR_RE.match(rel)
        if not m:
            continue
        base = f'{m.group(1)}/' if m.group(1) else ''
        name = m.group(2) or m.group(3)
        test = f'{base}tools/checks/tests/test_{name}.sh'
        materialized = f'tools/checks/tests/test_{name}.sh'
        if base and (root / materialized).is_file():
            test = materialized
        # A NEW CHECK SHIPS WITH ITS TEST. check_deep_check.py (the deep-check
        # practice) refuses a check with no tests/test_x.sh, or one that does
        # not define SOURCE_ROOT -- but it judges the whole tree, so the
        # changed-files scope dropped its finding and a check added without
        # either was first refused at the Promote. Asked here, on the commit
        # that adds the check, with the exact file and lines to write. The
        # engine's own checks are tested by its harness, not a test_x.sh.
        path = root / rel
        if not m.group(2) or rel not in added or not path.is_file() \
                or name in judged or _is_engine_check(root, rel):
            continue
        judged.add(name)
        if not (root / test).is_file():
            problems.append(
                f'{rel}: a new check with no test -- add {base}tools/checks/'
                f'tests/test_{name}.sh, invoking check_{name}.py by name; '
                f'run_all.sh runs only test_*.sh, so without it the deep '
                f'check never runs this check and check_deep_check.py '
                f'refuses the next full check')
        elif f'check_{name}.py' not in (root / test).read_text(
                encoding='utf-8', errors='replace'):
            problems.append(
                f'{test}: never names check_{name}.py -- a check\'s test must '
                f'invoke it by name, or check_deep_check.py refuses the next '
                f'full check')
        text = path.read_text(encoding='utf-8', errors='replace')
        if not re.search(r'^SOURCE_ROOT\s*=', text, re.M) \
                or not re.search(r'PRECEDENT_CHECK_ROOT["\']', text):
            problems.append(
                f'{rel}: does not separate the set it ships in from the repo '
                f'it audits -- define both at column 0, '
                f'`SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent'
                f'.parent` and `ROOT = pathlib.Path(os.environ.get('
                f'"PRECEDENT_CHECK_ROOT") or SOURCE_ROOT)`, and resolve '
                f'PRACTICE_FILE against SOURCE_ROOT, or check_deep_check.py '
                f'refuses the next full check')
    if repo_kind(HERE) == 'upstream' and any(
            rel in ('tools/precedent_check.py', 'tools/verify_harness.py')
            or re.match(r'(?:local/)?tools/checks/check_\w+\.py$', rel)
            for rel in files):
        for slug in _unplanted_checks(root):
            problems.append(
                f'{slug}: a registered check with no planted case -- add '
                f"case('{slug}', <plant>) to check_precedent_check_fires in "
                f'tools/verify_harness.py, planting the violation it exists '
                f'to catch; the harness refuses a check without one, and '
                f'the next full check runs it')
    practice = [f for f in files if f.endswith('.md')
                and (f.startswith('practices/') or '/practices/' in f)]
    build = root / 'tools' / 'build_views.py'
    if practice and build.is_file() and repo_kind(HERE) in ('upstream', 'source'):
        r = subprocess.run([sys.executable, str(build), '--repo', '.', '--check'],
                           cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(
                f'{practice[0]}{" and others" if len(practice) > 1 else ""} '
                f'changed, and the generated views were not regenerated with '
                f'it -- run `python3 tools/build_views.py` and commit what it '
                f'rewrites. ' + (r.stdout + r.stderr).strip().splitlines()[0][:300])
    # THE GENERATED COUNTS FOLLOW A NEW PRACTICE (2026-09-29). doc_sync's
    # blocks (the catalogue count in spec/LOADER.md, the enforced count,
    # the routing table) move when a practice is added or its front matter
    # changes, and only the full tier ran doc_sync -- so
    # stage-word-carries-its-step landed with three stale blocks and the
    # Debut was the first to notice. The drift gate,
    # never --write; about half a second.
    sync = root / 'tools' / 'doc_sync.py'
    moved = [f for f in practice
             if f in added or _front_matter_changed(root, since, f)]
    if moved and sync.is_file():
        r = subprocess.run([sys.executable, str(sync)], cwd=root,
                           capture_output=True, text=True)
        if r.returncode != 0:
            stale = [l.strip() for l in (r.stdout + r.stderr).splitlines()
                     if 'DRIFT' in l or 'STALE' in l or 'FAIL' in l][:4]
            problems.append(
                f'{moved[0]}{" and others" if len(moved) > 1 else ""} added or '
                f'changed its front matter, and the generated blocks that '
                f'count practices were not regenerated -- run `python3 '
                f'tools/doc_sync.py --write` and commit what it rewrites. '
                + ' | '.join(stale)[:400])
    # THE COUNTS PROSE QUOTES FOLLOW A CHANGED PRACTICE (2026-10-11). A
    # sentence in spec/PRACTICE_FORMAT.md or spec/PRACTICE_ENGINE_PLAN.md
    # restates a figure tools/catalogue_stats.py computes from the practice
    # files (its ANCHORS), and only the full tier ran that comparison. So
    # repo-is-memory gaining a Detail moved "practices with a Detail" from
    # 24 to 25, every quick check passed, and the fast Produce turned main
    # red (issue #1088). The figure has moved about ten times since
    # 2026-09-01, each time an original practice gained a Detail. Under
    # half a second.
    stats = root / 'tools' / 'catalogue_stats.py'
    anchored = practice or [f for f in files if f in (
        'tools/catalogue_stats.py', 'spec/PRACTICE_FORMAT.md',
        'spec/PRACTICE_ENGINE_PLAN.md')]
    if anchored and stats.is_file():
        r = subprocess.run([sys.executable, str(stats)], cwd=root,
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails = [l.strip()[len('FAIL'):].strip()
                     for l in (r.stdout + r.stderr).splitlines()
                     if l.strip().startswith('FAIL')][:3]
            problems.append(
                f'{anchored[0]}{" and others" if len(anchored) > 1 else ""} '
                f'changed, and a figure the prose quotes no longer matches '
                f'what tools/catalogue_stats.py computes -- update the '
                f'sentence and the anchor in catalogue_stats.py together. '
                + ' | '.join(fails)[:500])
    _new_tests_have_times(root, since, files, problems)
    for line in problems:
        print(f'  {line}')
    if tests:
        print(f'changed_files: {len(tests)} test(s) of changed checks run '
              f'at the Debut, not here: ' + ', '.join(tests))
    print(f'changed_files: {len(files)} changed file(s) checked, '
          f'{len(problems)} problem(s).')
    return 1 if problems else 0


# TESTS RUN AT THE DEBUT, NEVER BEFORE A PUSH (Morgan, 2026-10-16,
# strength: decided: "all the testing EXCEPT THE BARE ESSENTIAL AND LEAK
# GATES SHOULD GO INTO DEBUT, AND THE GITHUB TEST AFTER THE NEXT PRODUCE,
# AND THE MAIN TEST AFTER THE NEXT PRODUCE IN THE CASES WHERE THE GITHUB ONE
# IS NOT RUN"). A landing's quick check had grown to minutes: the practice
# checks on the changed files (precedent_check.py --changed-files-only,
# about 40 s, many of them reading the whole repository) and, from
# 2026-10-11, the harness tests a change reaches plus each changed check
# script's test_x.sh (a minute by a timing list a hundred tests out of
# date, two in fact). None of it is about publication -- the leak gate and
# the commit checks are, and stay -- and the full tier runs all of it: the
# Debut (--run-tests) on staging, then GitHub's test after Produce, or the
# full local suite on main where that test is not due. `verify_harness.py
# --for-change REF` still says, and runs, what a change reaches, by hand.
def _changed_since(root, argv):
    """-> the ref a push's change is measured from, or None. `--changed-since
    REF` names it (the merge gate passes the pull request's base); otherwise
    a push whose --push-command writes to staging, by a person who lands
    there, is measured from origin/staging (changed_since_for)."""
    if '--changed-since' in argv:
        i = argv.index('--changed-since')
        return argv[i + 1] if i + 1 < len(argv) else None
    if '--push-command' not in argv:
        return None
    i = argv.index('--push-command')
    cmd = argv[i + 1] if i + 1 < len(argv) else ''
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
    except ImportError:
        return None
    finally:
        sys.path.pop(0)
    targets = precedent_branches.push_targets(root, cmd) or []
    since_for = getattr(precedent_branches, 'changed_since_for', None)
    if since_for:
        # staging, for a person who lands straight on it.
        return since_for(root, targets)
    return None


def _default_destination(root, argv):
    """A run that names no destination checks what a push to the person's
    landing branch would get. -> argv, with --push-command added when it
    was missing.

    Morgan, 2026-10-01, strength: assented. A session ran this bare before
    every landing, as AGENTS.md's "before push or merge"
    line read, and bare meant the full ~11-minute suite -- the check that
    belongs to the Debut into staging -- several times in one day, for work
    the push gate itself would have checked in seconds. Now the bare run
    and the push agree: a bare run gets the tier a push to the landing
    branch gets. `--tier full` asks for the
    full check outright; the push gate, the merge gate and a Promote name
    their own destination or tier, so none of them is changed by this."""
    if any(a in argv for a in ('--tier', '--push-command', '--changed-files-check')):
        return argv
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
        landing = precedent_branches.landing_branch(root)[0]
    except Exception:                                        # noqa: BLE001
        return argv
    finally:
        sys.path.pop(0)
    if not landing:
        return argv
    if _ladder_off():
        # Off the ladder a person lands on main, which IS the full check
        # (spec/LADDER_OPT_IN_PLAN.md D3) -- there is no later step to name.
        print(f'precedent_push_check: no destination named, so this checks what '
              f'a push to {landing}, your landing branch, gets.', flush=True)
    else:
        print(f'precedent_push_check: no destination named, so this checks what '
              f'a push to {landing}, your landing branch, gets. The full check is the Debut\'s: '
              f'--tier full --because "<reason>".', flush=True)
    return list(argv) + ['--push-command', f'origin HEAD:{landing}']


def _full_tier_refusal(root, argv):
    """-> why `--tier full` is refused before anything runs, or None.

    Morgan, 2026-10-01, strength: decided ("Go, do both, then Booked"). The
    bare run already checks at the landing branch's tier (_default_destination),
    and on the same day a session still paid the ~12-minute suite three times
    for work going to the landing branch -- by typing `--tier full` itself,
    and by writing it into every helper's brief, because "deep check before
    push" read as "the thorough one". A landing push is the quick tier on
    purpose; the
    full check belongs to the Debut into staging, which runs it for you. So
    asking for full where the landing branch is the quick tier now needs a
    stated reason: `--because "<why>"`. A machine caller (`--gate`), a named
    push (`--push-command`) and a landing branch that is fully checked are
    untouched."""
    if '--tier' not in argv:
        return None
    i = argv.index('--tier')
    if (argv[i + 1] if i + 1 < len(argv) else '') != FULL:
        return None
    if any(a in argv for a in ('--gate', '--push-command', '--because')):
        return None
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
        landing = precedent_branches.landing_branch(root)[0]
        tier = precedent_branches.tier_for_branch(root, landing)[0]
    except Exception:                                        # noqa: BLE001
        return None
    finally:
        sys.path.pop(0)
    if tier != BASIC:
        return None
    # A person who lands straight on staging asks for the full suite with
    # --run-tests, which records it for the move into main.
    return (f'--tier full asks for the ~12-minute suite, and your landing '
            f'branch, {landing}, takes the quick check: run this bare. The '
            f'full suite is `python3 tools/precedent_branches.py --run-tests`, '
            f'which records its result for the move into main. If you really '
            f'mean this, say why: --tier full --because "<reason>".')


# Highest first: a push writing to several branches is judged by the one
# that needs the most.
_RUNG_ORDER = ('main', 'staging', 'precedent-beta-v01')


def _destination(root, argv):
    """-> the branch this push goes to, as far as it can be read: --destination
    (Promote names it), else the highest-rung branch --push-command writes
    to; None when neither says."""
    if '--destination' in argv:
        i = argv.index('--destination')
        return argv[i + 1] if i + 1 < len(argv) else None
    if '--push-command' not in argv:
        return None
    i = argv.index('--push-command')
    try:
        sys.path.insert(0, str(HERE))
        import precedent_branches
        targets = precedent_branches.push_targets(
            root, argv[i + 1] if i + 1 < len(argv) else '') or []
    except Exception:                                        # noqa: BLE001
        return None
    finally:
        sys.path.pop(0)
    for rung in _RUNG_ORDER:
        if rung in targets:
            return rung
    return targets[0] if targets else None


def _rung_refusal(root, kind, dest):
    """-> the refusal text when this push would put `dest` (staging
    or main) ahead of a shared set it takes from, else None.

    Its own step, outside the recorded passes, on purpose: whether a set
    has landed a commit on a rung changes with no change to this tree, and
    putting the destination into the views step's argv (the first version,
    2026-10-05) changed every pass's signature, so a Promote stopped reusing
    the full check the same tree had already passed. It is git ancestry
    only, and takes seconds. A source that cannot be resolved here is
    skipped, as the views step skips it."""
    if kind != 'consumer' or not dest:
        return None
    tool = HERE / 'precedent_sync_views.py'
    if not tool.is_file():
        return None
    p = subprocess.run([sys.executable, str(tool), '--repo', str(root),
                        '--rung-only', '--for-branch', dest],
                       cwd=root, capture_output=True, text=True)
    if p.returncode == 0:
        return None
    return (p.stdout + p.stderr).strip()


def _tier_from_args(root, argv):
    """-> (tier, why). --tier wins; else --push-command names the push and
    precedent_branches.py decides; else FULL, today's behaviour."""
    if '--tier' in argv:
        i = argv.index('--tier')
        value = argv[i + 1] if i + 1 < len(argv) else ''
        if value in (BASIC, FULL):
            return value, f'--tier {value}'
        return FULL, f'--tier {value!r} is not basic or full; running full'
    if '--push-command' in argv:
        i = argv.index('--push-command')
        cmd = argv[i + 1] if i + 1 < len(argv) else ''
        try:
            sys.path.insert(0, str(HERE))
            import precedent_branches
        except ImportError:
            return FULL, ('precedent_branches.py is not beside this file, so '
                          'the branch cannot be read -- running full')
        finally:
            sys.path.pop(0)
        return precedent_branches.tier_for_push(root, cmd)
    return FULL, 'no tier named'



def _practice_of(script):
    """-> the slug a check script names in its `# practice: SLUG` line, or
    None. Every script under tools/checks/ carries one."""
    try:
        with open(script, encoding='utf-8') as fh:
            for _n, line in zip(range(40), fh):
                m = re.match(r'#\s*practice:\s*([\w-]+)\s*$', line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


_NOT_BINDING = None


def not_binding():
    """-> {slug: reason} this repository declares does not bind it, as
    precedent_check.load_exemptions() answers it -- the same function, so
    the two tools cannot disagree about what is exempt. A `severity:
    blocking` practice is never in it. {} when it cannot be read, which
    exempts nothing.

    2026-09-28: a consumer declared commit-author not binding, and
    precedent_check reported it EXEMPT, while this file ran the check script
    directly and refused a push over two old commits already on main."""
    global _NOT_BINDING
    if _NOT_BINDING is None:
        sys.path.insert(0, str(HERE))
        try:
            import precedent_check
            _NOT_BINDING = precedent_check.load_exemptions()[0]
        except (Exception, SystemExit) as e:      # practice: fail-gracefully
            print(f'precedent_push_check: NOTE -- could not read this repo\'s '
                  f'`not_binding` ({e}), so no check is exempted.', flush=True)
            _NOT_BINDING = {}
        finally:
            sys.path.pop(0)
    return _NOT_BINDING


def working_branch_push(root, argv):
    """-> True when --push-command names a push whose every destination is
    a working branch, none of them a tier branch."""
    if '--push-command' not in argv:
        return False
    i = argv.index('--push-command')
    cmd = argv[i + 1] if i + 1 < len(argv) else ''
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches as pb
        targets = pb.push_targets(root, cmd)
        return bool(targets) and not set(targets) & set(pb.tier_branches(root))
    except Exception:                             # practice: fail-gracefully
        return False
    finally:
        sys.path.pop(0)


def landed_refs(root):
    """-> the tier branches of origin as local refs, fetched first where
    origin answers: what "already landed" means for a working-branch push.
    Offline, whatever this checkout last fetched."""
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches as pb
        tiers = pb.tier_branches(root)
    except Exception:                             # practice: fail-gracefully
        return []
    finally:
        sys.path.pop(0)
    ls = _git_env(root, ['ls-remote', '--heads', 'origin'], 30)
    if ls is not None and ls.returncode == 0:
        present = [b for b in tiers if f'\trefs/heads/{b}' in ls.stdout]
        if present:
            _git_env(root, ['fetch', '-q', '--no-tags', 'origin',
                            *(f'+refs/heads/{b}:refs/remotes/origin/{b}'
                              for b in present)], 60)
    return [f'refs/remotes/origin/{b}' for b in tiers
            if git(root, 'rev-parse', '-q', '--verify', f'refs/remotes/origin/{b}')]


def violation_lines(out):
    """The finding lines under each VIOLATION header of a check's output, up
    to its rule text -- the shape both a check script and precedent_check
    print. [] when there is no such header."""
    picked, inside = [], False
    for line in out:
        s = line.strip()
        if re.match(r'VIOLATION\b', s):
            inside = True
        elif inside and (not s or s.startswith('the rule:')
                         or s.startswith('precedent_check:')
                         or re.match(r'(ADVISORY|ERROR|SKIPPED|EXEMPT|NOTE|'
                                     r'COULD NOT VERIFY)\b', s)):
            inside = False
        elif inside:
            picked.append(s)
    return picked


def _output_at(root, rev, argv):
    """The output lines of `argv`, run in a throwaway worktree of `rev`."""
    tmp = Path(tempfile.mkdtemp(prefix='precedent-push-base-'))
    wt = tmp / 'tree'
    try:
        add = _git_env(root, ['worktree', 'add', '-q', '--detach', str(wt), rev], 60)
        if add is None or add.returncode != 0 or not (wt / script_arg(argv)).is_file():
            return []
        p = subprocess.run(argv, cwd=wt, capture_output=True, text=True)
        return (p.stdout + p.stderr).splitlines()
    finally:
        _git_env(root, ['worktree', 'remove', '--force', str(wt)], 60)
        shutil.rmtree(tmp, ignore_errors=True)
        _git_env(root, ['worktree', 'prune'], 30)


def already_landed(root, argv, out, landed):
    """-> the findings of a failed check when EVERY one of them is already on
    a landed branch, else None. A finding naming a commit is landed when a
    landed branch contains that commit; any other is landed when the same
    check prints the same line at the commit this push forked from. A check
    that printed no finding lines is never excused."""
    found = violation_lines(out)
    if not found or not landed:
        return None
    left = []
    for line in found:
        m = COMMIT_IN_FINDING.search(line)
        sha = m and git(root, 'rev-parse', '-q', '--verify', f'{m.group(1)}^{{commit}}')
        if sha and any(_git_env(root, ['merge-base', '--is-ancestor', sha, ref], 30)
                       .returncode == 0 for ref in landed):
            continue
        left.append(line)
    if left:
        bases = [b for b in (git(root, 'merge-base', 'HEAD', ref) for ref in landed) if b]
        fork = (git(root, 'merge-base', '--independent', *bases) or '').split()
        at_fork = set(violation_lines(_output_at(root, fork[0], argv))) if fork else set()
        left = [line for line in left if line not in at_fork]
    return None if left else found


# CHEAP CHECKS FIRST, AND A SLOW ONE ONLY WHEN THEY PASSED (2026-09-28). The
# harness suite takes minutes and every other check takes seconds, and it
# ran first: a merge gate refused a pull request for stale generated views
# -- a one-second finding -- after ten minutes, then took ten more on the
# fixed push. So the slow checks run last, and not at all once a fast one
# has failed, because the push is refused either way and the fix will be
# checked again. PRECEDENT_PUSH_CHECK_ALL=1 runs every check regardless,
# for a session that wants every failure in one pass.
SLOW_CHECKS = ('verify_harness', 'deep_check', 'consumer_shape')


def cheap_first(checks):
    """The checks with the slow ones moved to the end, order otherwise kept."""
    return [c for c in checks if c[0] not in SLOW_CHECKS] + \
        [c for c in checks if c[0] in SLOW_CHECKS]


def _run_streaming_stderr(argv, cwd):
    """subprocess.run(argv, capture_output=True, text=True), except that
    each line the child writes to stderr is ALSO passed through to this
    process's stderr as it arrives. Returns the same CompletedProcess, so
    every guard, stand-down and finding below reads exactly what it read
    before.

    WHY (practice: slow-steps-report-and-cache; very deep check,
    2026-09-28). verify_harness prints its progress and time-remaining
    lines to stderr for about four minutes, and a captured run swallowed
    every one of them: the person watching saw `[1/5] harness: ...` and
    then nothing until it finished or failed. Only stderr is streamed --
    a gate's stdout is its verdict, printed below in the shape this file
    has always used."""
    import threading
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    out_chunks = []
    reader = threading.Thread(target=lambda: out_chunks.append(
        proc.stdout.read()), daemon=True)
    reader.start()
    err_lines = []
    for line in iter(proc.stderr.readline, ''):
        err_lines.append(line)
        try:
            sys.stderr.write(f'      {line}' if line.endswith('\n')
                             else f'      {line}\n')
            sys.stderr.flush()
        except (OSError, ValueError):
            pass                  # a closed stderr never costs the verdict
    proc.stderr.close()
    reader.join()
    proc.stdout.close()
    rc = proc.wait()
    return subprocess.CompletedProcess(argv, rc, ''.join(out_chunks),
                                       ''.join(err_lines))


def run(root, checks, landed=None, reported=None):
    """`landed`: the refs whose findings a working-branch push is not
    refused over (RANGE_JUDGED), or a callable returning them, called only
    when one of those checks fails; `reported` collects the checks that
    failed only on such findings."""
    failed, missing, findings = [], [], {}
    started = time.monotonic()
    checks = cheap_first(checks)
    run_all = os.environ.get('PRECEDENT_PUSH_CHECK_ALL') == '1'
    for i, (name, argv, replaces) in enumerate(checks, 1):
        if name in SLOW_CHECKS and failed and not run_all:
            print(f'[{i}/{len(checks)}] {name}: NOT RUN -- {", ".join(failed)} '
                  f'already failed, so this push is refused either way; fix '
                  f'that and run again (PRECEDENT_PUSH_CHECK_ALL=1 runs it '
                  f'anyway)', flush=True)
            continue
        script_rel = script_arg(argv)
        script = root / script_rel
        shown = ' '.join([shown_interpreter(argv), *argv[1:]])
        if not script.is_file() and name in OPTIONAL:
            print(f'[{i}/{len(checks)}] {name}: not here -- this repo has no '
                  f'{script_rel}', flush=True)
            continue
        slug = (identity_slug(name, root) if name in IDENTITY_NAMES else None) or (
            _practice_of(script) if script.is_file() and
            'checks' in Path(script_rel).parts else None)
        if slug and slug in not_binding():
            print(f'[{i}/{len(checks)}] {name}: EXEMPT -- this repo declares '
                  f'{slug} not binding in precedent.json: '
                  f'{not_binding()[slug]}', flush=True)
            continue
        if os.environ.get(STANDIN_COMMIT_ENV) and \
                name in {c[0] for c in IDENTITY_CHECKS}:
            print(f'[{i}/{len(checks)}] {name}: not judged here -- the newest '
                  f'commit is a stand-in the update made to judge its tree; the '
                  f'push gate judges the real commit\'s author, date and '
                  f'trailer', flush=True)
            continue
        if (name in PUSH_TIME_SINCE and script.is_file() and
                PUSH_TIME_SINCE[name] not in script.read_text(encoding='utf-8',
                                                              errors='ignore')):
            print(f'[{i}/{len(checks)}] {name}: not run at push time -- this '
                  f'repo\'s copy of {script_rel} predates judging only what a push '
                  f'carries, and would read the whole history; it still runs in '
                  f'the full sweep, as it did before, until the set that ships '
                  f'it is updated here', flush=True)
            continue
        if not script.is_file():
            # A check whose tool this repo does not carry cannot be run, and
            # saying so beats a crash. Reported, never silently dropped.
            missing.append(name)
            print(f'[{i}/{len(checks)}] {name}: NOT RUN -- {script_rel} is not '
                  f'in this repo (stands in for {replaces})', flush=True)
            continue
        print(f'[{i}/{len(checks)}] {name}: {shown}', flush=True)
        t0 = time.monotonic()
        p = _run_streaming_stderr(argv, root)
        took = time.monotonic() - t0
        guard = GUARDS.get(name)
        why = guard(p.stdout + p.stderr, HERE) if guard and p.returncode == 0 \
            else None
        if why:
            failed.append(name)
            print(f'      FAILED in {took:.0f}s although it exited 0: {why}',
                  flush=True)
            continue
        if p.returncode == 0 and any(m in p.stdout + p.stderr
                                     for m in SIZE_CAP_WARNINGS):
            CAP_WARNED.append(name)
            CAP_DETAILS.extend(d for d in _cap_details(p.stdout + p.stderr)
                               if d not in CAP_DETAILS)
        if p.returncode == 0:
            marker, note = STAND_DOWNS.get(name, (None, None))
            if marker and marker in p.stdout + p.stderr:
                print(f'      {note} ({took:.0f}s)', flush=True)
                continue
            # An identity check passes with a WARNING for a bot-authored
            # commit -- an emergency fallback, never refused (Morgan,
            # 2026-10-06) -- and the warning is shown, not swallowed.
            warned = [ln for ln in p.stdout.splitlines()
                      if ln.startswith('WARNING:')] \
                if name in {c[0] for c in IDENTITY_CHECKS} else []
            if warned:
                print(f'      passed in {took:.0f}s, WITH A WARNING -- tell '
                      f'the person, and record an open item:', flush=True)
                for line in warned:
                    print(f'      | {line}')
                continue
            print(f'      passed in {took:.0f}s', flush=True)
            continue
        if (p.returncode == 2 and name in SKIP_IS_FINE_WITHOUT_IDENTITY
                and not (root / 'identity.json').is_file()):
            print(f'      stood aside in {took:.0f}s -- not an individual '
                  f'source, so there is no person to hold it to', flush=True)
            continue
        out = (p.stdout + p.stderr).rstrip().splitlines()
        refs = (landed() if callable(landed) else landed) \
            if landed and name in RANGE_JUDGED else None
        prior = already_landed(root, argv, out, refs) if refs else None
        if prior:
            if reported is not None:
                reported.append(name)
            print(f'      found {len(prior)} thing(s) in {took:.0f}s, every one '
                  f'already on {", ".join(r.rsplit("/", 1)[-1] for r in refs)} '
                  f'on origin -- this push to a working branch brings none of '
                  f'them, so they are reported, not blocking:', flush=True)
            for line in prior:
                print(f'      | {line}')
            continue
        failed.append(name)
        found = _finding_lines(out)
        findings[name] = found
        if found:
            print(f'      FAILED (exit {p.returncode}) in {took:.0f}s; what '
                  f'it found:', flush=True)
            for line in found:
                print(f'      | {line}')
        print(f'      last {TAIL_LINES} lines of its output:', flush=True)
        for line in out[-TAIL_LINES:]:
            print(f'      | {line}')
    total = time.monotonic() - started
    return failed, missing, total, findings


# THE PACKAGES THE GATES IMPORT, installed here rather than trusted to a hook
# (2026-09-26). Only BestPractice's SessionStart hook installs them, and a
# hook fires only in a session rooted in that repo -- a session rooted above
# every repo runs none. Without them doc_lint and doc_html degrade quietly,
# and verify_harness fails its checks after seven minutes naming what each
# was testing, never what is absent: that cost two full re-runs on
# 2026-09-14 and one more on 2026-09-26. Same list as
# precedent_session_check.py's "the packages the gates import" row.
GATE_PACKAGES = ('cmarkgfm', 'markdown')

# The one gate package that is not every repository's: `markdown` is
# tools/doc_html.py's alone (tabular-shared-renderer's renderer), and a
# practice set gets no doc_html.py at all, while a consumer receives one it
# may never run. Until 2026-10-08 both checks asked for it everywhere, so a
# repository with no use for the renderer was told a package was missing,
# and a push check without network to install it stopped on it.
DOC_HTML_PACKAGE = 'markdown'


def doc_html_in_use(root):
    """True where tools/doc_html.py is present and something here runs it.

    In BestPractice, or wherever doc_html.py is the repository's own (no
    tools/ENGINE_MANIFEST.json lists it), presence is use. Where the engine
    vendored it, it is in use when a file the repository wrote itself -- a
    tracked .py or .sh outside the vendored engine and the mirrored
    catalogue -- names it, which is how a host shim loads it. Unreadable
    state answers True: asking for a package that is not needed costs a
    line, and missing one that is costs a check that degrades unseen."""
    root = Path(root)
    if not (root / 'tools' / 'doc_html.py').is_file():
        return False
    try:
        m = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json')
                       .read_text(encoding='utf-8'))
    except (OSError, ValueError):       # no manifest: doc_html.py is ours
        return True
    names = m.get('files') if isinstance(m, dict) else None
    vendored = {f'tools/{n}' for n in (names or []) if isinstance(n, str)}
    if 'tools/doc_html.py' not in vendored:
        return True
    try:
        sys.path.insert(0, str(HERE))
        import precedent_resolve
        mirrored = tuple(precedent_resolve.mirrored_prefixes(root))
    except Exception:                                        # noqa: BLE001
        mirrored = ('process/upstream/',)
    r = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--',
                        '*.py', '*.sh'], capture_output=True, text=True)
    if r.returncode != 0:
        return True
    for rel in filter(None, r.stdout.split('\0')):
        if rel in vendored or rel.startswith(mirrored):
            continue
        try:
            if 'doc_html' in (root / rel).read_text(encoding='utf-8',
                                                    errors='ignore'):
                return True
        except OSError:
            continue
    return False


def gate_packages(root):
    """GATE_PACKAGES this repository's gates actually import."""
    return tuple(p for p in GATE_PACKAGES
                 if p != DOC_HTML_PACKAGE or doc_html_in_use(root))


def _importable(mod):
    return subprocess.run([sys.executable, '-c', f'import {mod}'],
                          capture_output=True).returncode == 0


def _pip_install(mods):
    # precedent_python.pip_install is the engine's one install call: it
    # retries a PEP 668 refusal, which a cloud container's system Python
    # gives a plain `pip install` (2026-10-15). Both files are engine files;
    # the plain call stays only for a tree that lacks it.
    try:
        sys.path.insert(0, str(HERE))
        import precedent_python
        r = precedent_python.pip_install(sys.executable, mods)
    except ImportError:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet',
                            *mods], capture_output=True, text=True)
    tail = (r.stderr or r.stdout or '').strip().splitlines()
    return tail[-1] if tail else ''


def ensure_gate_packages(packages=GATE_PACKAGES, importable=_importable,
                         install=_pip_install):
    """-> (ok, note). Installs whichever of `packages` this interpreter cannot
    import. ok is False only when one is still missing afterwards, so the run
    stops in seconds naming it instead of failing minutes later without."""
    missing = [m for m in packages if not importable(m)]
    if not missing:
        return True, ''
    said = install(missing)
    still = [m for m in missing if not importable(m)]
    if still:
        return False, (f'{", ".join(still)} missing and pip could not install '
                       f'{"it" if len(still) == 1 else "them"}'
                       f'{f" ({said})" if said else ""} -- run `pip install '
                       f'{" ".join(still)}`, then this again')
    return True, f'installed {", ".join(missing)}, which the gates import'


def _test_session_refusal():
    """The No ladders test session pushes nothing (precedent_ladder.py).
    A repository without the helper has no such session: None."""
    try:
        sys.path.insert(0, str(HERE))
        import precedent_ladder
    except Exception:                                        # noqa: BLE001
        return None
    return precedent_ladder.test_session_refusal()


def main(argv):
    root_s = git(HERE, 'rev-parse', '--show-toplevel')
    if not root_s:
        print('precedent_push_check: not inside a git checkout; nothing to '
              'check.', file=sys.stderr)
        return 2
    root = Path(root_s)
    if '--gate' in argv:
        refusal = _test_session_refusal()
        if refusal:
            print(f'precedent_push_check: {refusal}')
            return 1
    # A run from inside a different repo reads THIS repo, silently -- say so
    # (precedent_which_repo.py; gotcha-2026-09-29). Warn only; never fatal.
    try:
        sys.path.insert(0, str(HERE))
        import precedent_which_repo
        precedent_which_repo.warn_if_elsewhere(root, 'precedent_push_check.py')
    except Exception:                                        # noqa: BLE001
        pass
    argv = _default_destination(root, argv)
    # --list runs nothing and pushes nothing, so no refusal about what a
    # push may carry applies to it. It used to be refused whenever main had
    # commits staging lacked, which turned the harness test that reads it
    # red for a reason unrelated to any change (2026-10-17).
    listing = '--list' in argv
    refused = None if listing else _full_tier_refusal(root, argv)
    if refused:
        print(f'precedent_push_check: REFUSED -- {refused}', file=sys.stderr)
        return 1
    if '--because' in argv:
        i = argv.index('--because')
        print(f'precedent_push_check: running as asked, because: '
              f'{argv[i + 1] if i + 1 < len(argv) else "(no reason given)"}',
              flush=True)
    refused = None if listing else _promote_only_refusal(root, argv)
    if refused:
        print(f'precedent_push_check: REFUSED -- {refused}', file=sys.stderr)
        return 1
    if '--tier' in argv:
        i = argv.index('--tier')
        value = argv[i + 1] if i + 1 < len(argv) else ''
        if value not in (BASIC, FULL):
            # Refused, not run full: a misspelt tier used to run the full
            # suite silently and so skipped the --because refusal --tier
            # full has (found by a consumer rehearsal, 2026-10-03, which ran
            # "--tier main" believing it named a tier).
            print(f'precedent_push_check: REFUSED -- --tier {value!r} is not '
                  f'a tier. The tiers are {BASIC} and {FULL}; a branch name '
                  f'such as main is not one. Run this bare to get the tier '
                  f'your landing branch takes.', file=sys.stderr)
            return 1
    tier, why = _tier_from_args(root, argv)
    kind, checks = plan(root, tier=tier)
    if '--changed-files-check' in argv:
        i = argv.index('--changed-files-check')
        return changed_files_check(root, argv[i + 1] if i + 1 < len(argv)
                                   else 'origin/staging')
    since = _changed_since(root, argv) if tier == BASIC else None
    # Where the push goes and what it changes, for the checks this runs: a
    # practice set's own check may judge a push by its destination -- the
    # ladder's go-update refuses a high-risk change landing with no pull
    # request -- and the engine says only where, never what any set's rule
    # is (practice: enforcement-lives-with-its-practice, 2026-10-16).
    _dest = _destination(root, argv)
    for _name, _value in ((PUSH_DESTINATION_ENV, _dest), (CHANGED_SINCE_ENV, since)):
        if _value:
            os.environ[_name] = _value
        else:
            os.environ.pop(_name, None)
    if tier == BASIC and _dest and _dest == _staging_name(root) and kind is not None:
        checks.extend(own_checks_before_staging(
            root, planned=[a[1] if a and a[0] == sys.executable else a[0]
                           for _n, a, _r in checks if a]))
    if since and kind is not None:
        rel = HERE.relative_to(root) if HERE.is_relative_to(root) else HERE
        # Only the per-file checks: the practice checks and every test run
        # at the Debut and around Produce (TESTS RUN AT THE DEBUT, below).
        checks.append((CHANGED_FILES_CHECK[0],
                       [sys.executable, str(rel / 'precedent_push_check.py'),
                        '--changed-files-check', since],
                       CHANGED_FILES_CHECK[1]))
    if kind is None:
        print(f'precedent_push_check: cannot tell what kind of repository '
              f'{root} is (no ENGINE_MANIFEST.json kind beside this file, and '
              f'it is not BestPractice), so there is no list to run.',
              file=sys.stderr)
        return 2

    if '--list' in argv:
        # Which branches take the full list is precedent_branches' answer,
        # not this sentence's: staging is a lander's quick tier (2026-10-09).
        full_to, others = 'main', 'any other branch'
        if not _ladder_off():
            full_to = 'staging or main'
            try:
                sys.path.insert(0, str(HERE))
                import precedent_branches
                st = precedent_branches.staging_branch(root)
                if precedent_branches.tier_for_branch(root, st)[0] != FULL:
                    full_to = 'main'
                    others = (f'any other branch, {st} included (your '
                              f'landing branch),')
            except Exception:                               # noqa: BLE001
                pass                       # an older engine: the old wording
            finally:
                sys.path.pop(0)
        print(f'{root.name} is {"an" if kind[0] in "aeiou" else "a"} {kind} '
              f'repository. Before a push to {full_to} (full); a push '
              f'to {others} runs only the checks marked basic:')
        for name, a, replaces in plan(root, tier=FULL)[1]:
            mark = 'basic' if name in BASIC_CHECKS else 'full '
            print(f'  {name:16} [{mark}] {shown_interpreter(a)} {" ".join(a[1:])}')
            print(f'  {"":16}         replaces {replaces}')
        wf_text = ''.join(w.read_text(encoding='utf-8', errors='replace')
                          for w in sorted((root / '.github' / 'workflows').glob('*.y*ml')))
        here = {c: w for c, w in GITHUB_ONLY_STEPS.items() if c in wf_text}
        if here:
            print('Run only on GitHub, never before a push (they change something; '
                  'they check nothing):')
            for cmd, why in here.items():
                print(f'  {cmd} -- {why}')
        return 0

    refused = _rung_refusal(root, kind, _destination(root, argv))
    if refused:
        print(f'precedent_push_check: REFUSED -- {refused}', file=sys.stderr)
        return 1
    also = [plan(root, tier=FULL)[1]] if tier == BASIC else []
    landed, reported = None, []
    if tier == BASIC and working_branch_push(root, argv):
        memo = []

        def landed():
            if not memo:
                memo.append(landed_refs(root))
            return memo[0]
    rec = already_passed(root, checks, also) if '--gate' in argv else None
    where = ''
    if '--gate' in argv and not rec:
        sigs = [signature(checks), *(signature(c) for c in also)]
        known = known_ledgers(root)
        rec = shared_pass(root, clean_tree(root, known), sigs)
        if rec:
            where = ', in another checkout'
            path = record_path(root)
            if path:
                kept = {k: v for k, v in rec.items() if k != 'shared'}
                if known:
                    kept['ledgers'] = known
                path.write_text(json.dumps(kept, indent=2) + '\n',
                                encoding='utf-8')
    if rec:
        when = f' at {rec["at"]}' if rec.get('at') else ''
        history = [c for c in checks if c[0] in HISTORY_CHECKS]
        print(f'precedent_push_check: this exact tree already passed the '
              f'{rec.get("tier", tier)} check{when}{where} ({len(checks)} '
              f'check(s)); nothing to re-run'
              + (' but the checks that judge commits rather than files.'
                 if history else '.'), flush=True)
        if not history:
            clear_failed_tree(root, rec.get('tree'))
            return 0
        failed, _missing, total, findings = run(root, history, landed)
        if failed:
            for name in failed:
                for line in findings.get(name, []):
                    print(f'  {name} | {line}')
            print(f'\nprecedent_push_check: FAILED -- {", ".join(failed)} '
                  f'({total:.0f}s). The files passed before, but a commit '
                  f'here since then did not. Fix the commit and run this '
                  f'again; do not push past it.')
            note_failed_tree(root, rec.get('tree'), failed)
            return 1
        clear_failed_tree(root, rec.get('tree'))
        return 0

    if git(root, 'rev-parse', '--is-shallow-repository') == 'true':
        print('precedent_push_check: this clone is shallow, so every check '
              'that reads history would skip -- deepening it first '
              '(git fetch --unshallow).', flush=True)
        subprocess.run(['git', '-C', str(root), 'fetch', '-q', '--unshallow'],
                       capture_output=True, text=True)
        if git(root, 'rev-parse', '--is-shallow-repository') == 'true':
            # A second --unshallow cannot help when the clone stays shallow
            # only because .git/shallow still names commits of branches
            # deleted upstream; the gotcha carries the safe recovery.
            print('precedent_push_check: FAILED -- the clone is still shallow, '
                  'so the history checks cannot run. If `git fetch '
                  '--unshallow` has not finished, run it again; if it '
                  'completes and the clone still says shallow, .git/shallow '
                  'names commits of deleted branches -- follow gotchas/'
                  'gotcha-2026-09-28-stale-shallow-entries-for-deleted-'
                  'branches-survive-unshallow.md.')
            return 1

    ok_pkgs, note = ensure_gate_packages(gate_packages(root))
    if note:
        print(f'precedent_push_check: {"" if ok_pkgs else "FAILED -- "}{note}.',
              flush=True)
    if not ok_pkgs:
        return 1

    if tier == FULL:
        print(f'precedent_push_check: {kind} repository {root.name}, '
              f'{len(checks)} check(s) -- everything CI used to run, run here '
              f'({why}).', flush=True)
    else:
        print(f'precedent_push_check: {kind} repository {root.name}, the '
              f'basic check, {len(checks)} check(s) ({why}). The full suite '
              f'runs at the Debut, and after a push or Produce into main.',
              flush=True)
    # The tree is read BEFORE the run as well as after, and a pass is
    # recorded only when the two agree. Read only afterwards, a commit made
    # while the suite ran was credited with a pass the suite never gave it:
    # the isolated harness had copied the commit before it, so a new check
    # with no planted case (whats-new, 2026-10-01) went green in the full
    # check and was refused minutes later by the merge gate's quick one.
    #
    # Fact ledgers the checks write (practice: gate-ledger) are the one kind
    # of edit a run makes to the tree it judges. fact_ledger.py reports each
    # ledger it saves into the file FACT_LEDGER_WRITTEN names; those paths,
    # and the ones an earlier run here saw, are left out of "uncommitted".
    # Anything else dirty, before or after, still refuses the record.
    dirty_before = dirty_paths(root)
    head_before = git(root, 'rev-parse', 'HEAD^{tree}')
    fd, listing = tempfile.mkstemp(prefix='precedent-ledgers-')
    os.close(fd)
    prior_env = os.environ.get(LEDGER_WRITES_ENV)
    os.environ[LEDGER_WRITES_ENV] = listing
    try:
        failed, missing, total, findings = run(root, checks, landed, reported)
    finally:
        if prior_env is None:
            os.environ.pop(LEDGER_WRITES_ENV, None)
        else:
            os.environ[LEDGER_WRITES_ENV] = prior_env
        written = ledgers_written(root, listing)
        try:
            os.unlink(listing)
        except OSError:
            pass
    ledgers = sorted(set(known_ledgers(root)) | written)
    tree_before = head_before if (dirty_before is not None and
                                  dirty_before <= set(ledgers)) else None
    tree = clean_tree(root, ledgers)
    refreshed = sorted((dirty_paths(root) or set()) & set(ledgers))
    moved = tree is not None and tree != tree_before
    if moved:
        tree = None
    if failed:
        # Said again at the very end, because the end is what every caller
        # that truncates -- the push gate, the merge gate -- keeps.
        for name in failed:
            for line in findings.get(name, []):
                print(f'  {name} | {line}')
        print(f'\nprecedent_push_check: FAILED -- {", ".join(failed)} '
              f'({total:.0f}s). Fix the finding and run this again; do not '
              f'push past it.')
        # Only a tree the run judged exactly: over uncommitted edits it
        # judged something no push sends.
        note_failed_tree(root, tree or (tree_before if not moved else None), failed)
        return 1
    if missing:
        print(f'\nprecedent_push_check: passed, but {", ".join(missing)} '
              f'could not run here -- this repo does not carry the tool. '
              f'Refresh the vendored engine to get it.')
    clear_failed_tree(root, tree)
    path = record_path(root)
    if reported:
        # Not recorded: the pass stood only because this push goes to a
        # working branch, and a record is reused by pushes that go elsewhere.
        print(f'\nprecedent_push_check: passed in {total:.0f}s for this push '
              f'to a working branch; {", ".join(reported)} found only what is '
              f'already on origin\'s tier branches (above). NOT recorded as a '
              f'pass, since a push to a tier branch judges those findings.')
        _cap_warning_last(tier)
        return 0
    if tree and path:
        rec = {'tree': tree, 'checks': signature(checks), 'kind': kind,
               'tier': tier, 'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        local = dict(rec, ledgers=ledgers) if ledgers else rec
        path.write_text(json.dumps(local, indent=2) + '\n', encoding='utf-8')
        if refreshed:
            print(f'\nprecedent_push_check: the run refreshed '
                  f'{len(refreshed)} fact ledger(s), left in place and '
                  f'uncommitted: {", ".join(refreshed)}. They only cache '
                  f'facts that verify themselves, so the pass below holds for '
                  f'the commit; commit them when convenient so the next run '
                  f'starts warm.')
        print(f'\nprecedent_push_check: all passed in {total:.0f}s; recorded '
              f'for tree {tree[:12]} ({tier}), so a push of this commit will '
              f'not re-run them.')
        publish_pass(root, rec)
    elif moved:
        print(f'\nprecedent_push_check: all passed in {total:.0f}s, but the '
              f'commit changed while it ran -- NOT recorded. Part of the run '
              f'copied the commit it started on, so this pass says nothing '
              f'about the one checked out now. Run it again, without '
              f'committing until it ends.')
    else:
        print(f'\nprecedent_push_check: all passed in {total:.0f}s, over a '
              f'working tree with uncommitted changes -- NOT recorded, since '
              f'the push sends the commit, not these edits. Commit, then run '
              f'it again or let the push gate do it.')
    _cap_warning_last(tier)
    return 0


# THE PUSH GATE'S REFUSAL IS WRITTEN HERE, NOT IN THE HOOK (2026-10-07), for
# the reason doc_lint.py's hook_reason gives: a reworded hook is a question
# for a person in every repository at its next Update Vendors, and a
# reworded tool is not. .claude/hooks/push-check-gate.sh pipes the run's
# output back in with --hook-reason and passes on what comes out.
# A hook refuses the WHOLE Bash command before any of it starts, so in
# `git add ... && git commit ... && git push` the commit never happened
# either. Twice (2026-10-03 and 2026-10-05) a session in a consumer
# repository read a bare "REFUSED this push" as "committed, push refused"
# and told its person the work was committed when it was not.
NOTHING_RAN = ('Nothing in the refused command ran -- not the push, and not any step\n'
               'before it in the same command (a commit or an add included). Make those\n'
               'steps in a call of their own, check `git status`, then push separately.')


def hook_reason(outcome, out, top='', tool='tools/precedent_push_check.py'):
    """-> the whole text the push gate refuses with: `outcome` the run's exit
    status ('1' a check failed, '124' the hook's deadline killed it), `out`
    what it printed, `top` the repository pushed. 'identity' is the
    commit-identity push gate's refusal, `out` its findings. None for any
    other outcome, which the gate does not refuse on."""
    if outcome == 'identity':
        return identity_hook_reason(out)
    if outcome == '1':
        why = ('A check failed. Fix it before pushing -- this list is what GitHub\n'
               'CI used to run on this push, and CI is not going to run it now.')
    elif outcome == '124':
        why = ('The checks did not finish within 14 minutes, so nothing was\n'
               'verified. Run them directly with a long Bash timeout, then push again --\n'
               'a pass is recorded against the tree, so the push will not re-run them:\n\n'
               f'    cd {top or "."} && python3 {tool}')
    else:
        return None
    tail = '\n'.join(out.rstrip().splitlines()[-120:])
    return (f'The push check REFUSED this push of {top or "this repository"}.\n\n'
            f'{NOTHING_RAN}\n\n{why}\n\n{tail}\n\n'
            'Nothing lets a push past this, and nothing should: fix what it found and\n'
            'push again. If the check itself is wrong, fix the check where it lives.')


def identity_hook_reason(findings):
    """-> the whole text commit-identity-push-gate.sh refuses with,
    `findings` being what tools/check_commit_author.py and
    tools/check_commit_dates.py reported. Written here, not in the hook,
    for the reason hook_reason() gives (moved 2026-10-07)."""
    return ('The commit-identity push gate REFUSED this push.\n\n'
            f'{NOTHING_RAN}\n\n'
            'These two checks are scope `tree`: they audit every commit reachable from\n'
            'HEAD, not just the ones this push adds. They ran in GitHub Actions until\n'
            '2026-09-21, when a practice source stopped running CI at all; this hook is\n'
            'what replaced them, which makes it the only thing standing between a\n'
            'mis-authored commit and a published branch.\n'
            f'{findings.rstrip()}\n\n'
            'Fix it before the commit is published. On an UNPUSHED commit this is one\n'
            '`git commit --amend --reset-author` (re-run under\n'
            'TZ=America/Argentina/Buenos_Aires for the offset); once it is on a shared\n'
            'branch, no-rewrite-for-warnings applies and the only honest route left is a\n'
            'grandfathered_commit_shas entry in identity.json with a reason. That\n'
            'asymmetry is the whole reason this gate sits before the push rather than\n'
            'after it.\n\n'
            'Nothing lets a push past this: fix the commit as above, then push again.')


def _hook_reason_main(argv):
    """`--hook-reason OUTCOME [--top DIR]`, the run's output on stdin: print
    the refusal, exit 0; exit 2 for an outcome this tool does not word."""
    val = lambda f: argv[argv.index(f) + 1] if f in argv and argv.index(f) + 1 < len(argv) else ''
    text = hook_reason(val('--hook-reason'), sys.stdin.read(), top=val('--top'))
    if text is None:
        return 2
    print(text)
    return 0


# Every option main() reads. An option it does not know is refused rather
# than ignored: a PR template naming a flag this file never had
# (--changed-files-only) ran the full ~14-minute suite twice, silently
# (2026-09-30).
VALUE_OPTIONS = ('--tier', '--changed-since', '--push-command', '--because',
                 '--destination')
OPTIONAL_VALUE_OPTIONS = ('--changed-files-check',)
FLAG_OPTIONS = ('--gate', '--list', '--help', '-h')

# Workflow steps here that run a tool but test nothing, so a push never
# runs them: named in --list, so every tool a workflow runs is accounted
# for (check_push_check_runs_what_ci_ran).
GITHUB_ONLY_STEPS = {
    'python3 tools/harness_reach.py publish':
        'stores the ledger of what each check reaches that a green whole-suite '
        'run on GitHub recorded (2026-10-12)',
    'python3 tools/precedent_stale_branches.py --delete-merged':
        'deletes the branches already in main, from the branch cleanup '
        "page's button, started only by a person (2026-10-16, "
        'spec/BRANCH_CLEANUP_BUTTON_PLAN.md)',
}


def unknown_arguments(argv):
    """-> the arguments in `argv` main() would not read, in order."""
    out, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in VALUE_OPTIONS:
            i += 2
            continue
        if a in OPTIONAL_VALUE_OPTIONS:
            i += 2 if i + 1 < len(argv) and not argv[i + 1].startswith('-') else 1
            continue
        if a not in FLAG_OPTIONS:
            out.append(a)
        i += 1
    return out


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    if '--hook-reason' in sys.argv[1:]:
        sys.exit(_hook_reason_main(sys.argv[1:]))
    unknown = unknown_arguments(sys.argv[1:])
    if unknown:
        print(f'precedent_push_check: unknown argument(s): {" ".join(unknown)}. '
              f'It takes {", ".join(o + " VALUE" for o in VALUE_OPTIONS)}, '
              f'--changed-files-check [REF], --gate and --list; --help says '
              f'what each does. Nothing was run.', file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
