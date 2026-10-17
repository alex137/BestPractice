---
title:         Very Deep Check, 2026-10-17 — What It Found and What Was Done
kind:          record
status:        closed
opened:        2026-10-17
closed:        2026-10-17
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The full account of the most recent very deep check: what it read, what each pass found, what was fixed and where, and what is left for a person. The next run rewrites it; git history keeps this one."
---
# Very Deep Check, 2026-10-17 — What It Found and What Was Done

The full record of the latest run (the next run rewrites this file; git
history keeps each earlier one). The ledger of every run is
[VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md); this is the long form behind its
"Current run" row.

**Scope, as Morgan asked it:** "Very deep check for best practice then very
deep check for each of the three practice sets attached". BestPractice was
checked on `main` at 66e05b79, and each of the three sets it declares (the
individual set, the ladder set, the writing set) was checked whole as a
repository with an upstream, on its own `main`. All four passes, from 06:44 Buenos Aires time to about 08:45, with nine
helpers working in parallel in scratch worktrees and the session merging
their branches. Another session was running Update Vendors in the three sets
throughout; this run left their vendored engine files alone.

**Two things went wrong during the run, and they are part of the record.**
A helper ran the deep check bare in its worktree, and the check pushed its
pass receipt to the receipt branch on origin; nothing else reached origin
from a helper. And the session pushed one set's branch once with a
violation it had just introduced (the generated-files registry, below),
fixed and re-pushed within minutes.

## The Short Version

- **The full harness passed on `main` before any change** (`--all`, 119 of
  119 planted cases), and again on the finished branch (see the last
  section).
- **More than 150 findings across the four repositories, by the helpers'
  own counts; about 60 fixed in the run**, each code fix with stated cases
  that fail on the old code.
- **The check found real faults in itself**: it spent 27 minutes on the
  suite before refusing in seconds for a stale source, refused the detached
  checkout a cloud session starts from, skipped two scans in any worktree,
  and wrote a run record a set could not commit. All fixed.
- **39 open items closed and 15 gotchas retired**, each on its own
  condition.
- **What is left**, with Morgan's calls first, is in
  [todo-2026-10-17-very-deep-check-findings](../todo/todo-2026-10-17-very-deep-check-findings.md).

## Pass 1 — Can an Adopter Install, Update and Move Practices?

Six rehearsals in scratch, each with an isolated home directory so no real
set leaked in: the guided install (SETUP.md, as a non-technical
administrator), the developer install (INSTALL.md section 0), a
from-scratch install against `main` alone, an update from a 2026-10-01
install, a migration from the classic layout, and practice moves in every
direction the page offers. Every result's own checks came back clean in the
end; the findings are about what it took to get there.

Fixed:

- **The freshness guard wrote an origin with no URL into a repository that
  had none**, so the install's own "give it an origin" step failed. Fixed
  with a harness case.
- **A sync took a set's uncommitted new practice file and pinned a commit
  without it**, with `--check` green. Every practice move leaves exactly
  that state. Untracked files under what a sync reads now count.
- **Install documents brought in line with the installer**: three
  workflows ship, not two; the leak gate's real trigger; ladder words out of
  the guided install; the developer key described correctly; the migration
  guide's five stale steps; the move guide's seven.
- **The set skeletons' README and `.gitignore`** now describe what bootstrap
  writes; a fresh shared set no longer fails its own check on a dead link.

Found, not fixed (in the findings item): a person with no individual set
never sees 28 practices; "notices and offers a rule" does nothing on a fresh
install; the first local session rewrites global git identity; an update
needs seven hand calls on untouched template text; and the move tool's
mention fixer and approval line.

## Pass 2 — Do the Mechanisms Do What They Claim?

All 24 questions answered or explicitly marked partly attempted. Fixed:

- **The commit-identity check's prevention half had silently stopped
  running** wherever the hooks are stubs, since 2026-10-07: it looked for a
  marker the stubs no longer carry and passed without trying anything.
- **The contributor-boundary section called a set's boundary "on"** without
  reading the setting.
- **The very deep check, against itself**: `--with-harness` now waits for the
  source freshness gate; a detached checkout carrying origin's base is
  current; a local-only branch behind the base is told to bring the base
  in, not to push; "unpushed" counts what no origin ref has; a linked
  worktree is its own checkout; the warnings block links the exclusions
  registry only where it exists; and the tool lists the record files it
  writes in the checked repo's registry.
- **A shared ignore list could expose a private file.** The list that keeps
  a set's shipped tools out of git is shared by every worktree of a clone,
  and a run in one worktree rewrote it with only its own ships; three tools,
  one from a private repository, went back to untracked in the main
  checkout. Found when they reappeared mid-run; fixed with a stated case.
- **Four check descriptions, the shipped-class table and the push check's
  own `--list` and `--help`** said what the code no longer does.
- **Warnings judged for the first time**: dated records' unlinked references
  excluded for good, one advisory until its own revisit date. Open groups
  went from 2282 to about 2020; the rest are live documents to fix, not
  exclude.

Found, not fixed: running the materialize tool directly publishes private
practice text in a public consumer; a read-only check can empty the session
file; a set's own hooks never run in a set; the deep check pushes a receipt
and no document says so.

## Pass 3 — Does the Writing Hold Together?

The always-loaded files read against the rules they summarize, and
[spec/LOADER.md](LOADER.md) read whole (782 lines, never recorded as read).
Fixed: the deep check's tier described as before 2026-10-14; the resident
cap given as 2,000 tokens in four live places; LOADER.md telling a set to
run `--agents-only`; the TODO.md stub's two false sentences (the previous
run believed the stub could not be changed; it can); Update All Vendors
missing from the page on taking updates. AGENTS.md is at 5,554 of its 6,950
ceiling and has grown about 57 tokens a day.

## Pass 4 — Catalogue, Backlog, Branches

- **Every open item and live gotcha read**, in BestPractice and each set:
  39 items closed on their conditions, 15 gotchas retired, 10 items
  ambiguous and asked (listed in the run record).
- **One question settled by this run's own pushes**: one session holding
  every private source can push to both owners, so the cross-owner item is
  closed. The gotcha stays live: a clone that is not a session source still
  cannot be pushed.
- **Thirty practice pairs that read alike judged**: 29 kept, each with its
  reason; one merge candidate for Morgan.
- **Every branch judged.** Five unlanded branches recommended for deletion
  (landed another way, superseded, or already decided: the July spec branch
  Morgan said to close on 2026-10-11). Every other branch in the four
  repositories is merged; the ones from the still-running Update Vendors
  session wait until it ends.
- **Automated actions**: the daily `deep-check.yml` schedule is the only
  recurring job in force; one dead one-shot session reminder from September
  is disabled and can be deleted.
- The review page was published to Morgan privately, never committed.

## The Three Sets

Each set ran its own very deep check from its own clone, its own gates
(full sweep 0 violated, check tests, leak gate), and the four passes applied
to a set. Their run records, with each set's upstream findings and the
band-aid question, are in their own `spec/VERY_DEEP_CHECK.md`.

- **The individual set**: its install section told an adopter to copy a
  script carrying the set's private clone URL; fixed. Its shared clone, like
  the other two, carried stale shallow entries that refused the push check;
  cleared per the 2026-09-28 gotcha after a reachability check.
- **The ladder set**: the landing and branch checks above, the prompt-please
  contradiction, and stale lock and stage names fixed.
- **The writing set**: stale README, AGENTS.md and config text fixed; its
  `create-word-doc` never reaches a session building a Word file.

## Morgan's Calls

Asked in the run's reply; the list, each with the session's pick, opens
[todo-2026-10-17-very-deep-check-findings](../todo/todo-2026-10-17-very-deep-check-findings.md):
the ladder's two checks that never run, the ladder's prompt-please
contradiction, deleting a retired set's repository, code-owner reach for a
person with no individual set, vendoring `close_detect.json`, the global git
identity on a local machine, the skeleton's CI default, the update that drops
18 commands silently, the unlisted daily schedule, and whether this repo
and the sets carry band-aids until their upstream findings land.

## What Is Left

Everything not fixed, with where its fix lives, is in
[todo-2026-10-17-very-deep-check-findings](../todo/todo-2026-10-17-very-deep-check-findings.md).
Not run this time: a real consumer repository's update (none was attached;
asked at the start, unanswered), the reproduction of every live gotcha, and
a one-finding-at-a-time re-check of the earlier runs' composite items.

## The Harness, After the Fixes

The whole harness ran again on the finished branch with `--all`. Three
of its four parts passed (444, 194 and 185 cases). The fourth, every planted
case of the enforced checks, failed on one: the very deep check's own
"account owed" case read the real run ledger, whose last run had no passes
recorded yet, so it could not fire in the middle of a real run. The case now
plants its own ledger state, and all 119 planted cases pass.

## Warnings

<!--vdc-embed:warnings: never hand-edit -- written by tools/very_deep_check.py's WARNINGS section; refresh with --refresh-warnings -->
Measured 2026-10-17: **2267 warning(s), 2019 still open** (neither fixed nor excluded). For comparison, open at the previous run: 2282.

| Source | Kind | Warnings | Open | Excluded for good | Excluded until a date |
|---|---|---|---|---|---|
| doc_lint | unlinked file reference | 2192 | 1968 | 224 | 0 |
| doc_lint | open item naming no blocker | 48 | 48 | 0 | 0 |
| precedent_check | enforcement-lives-with-its-practice | 24 | 0 | 0 | 24 |
| doc_lint | process residue | 2 | 2 | 0 | 0 |
| precedent_session_check | undetermined | 1 | 1 | 0 | 0 |

**Exclusions decided this run: 4.**
- doc_lint / unlinked file reference / `decisions/*`: permanent, by the session -- A dated record: it says what was true when it was written, and the paths it names in backticks are named as they were. Relinking them is churn no reader gains from, and the history-aware checks (rename-updates-links, change-updates-its-docs, retired-words) already read this directory as history.
- doc_lint / unlinked file reference / `evals/*`: permanent, by the session -- A dated record: it says what was true when it was written, and the paths it names in backticks are named as they were. Relinking them is churn no reader gains from, and the history-aware checks (rename-updates-links, change-updates-its-docs, retired-words) already read this directory as history.
- doc_lint / unlinked file reference / `record/*`: permanent, by the session -- A dated record: it says what was true when it was written, and the paths it names in backticks are named as they were. Relinking them is churn no reader gains from, and the history-aware checks (rename-updates-links, change-updates-its-docs, retired-words) already read this directory as history.
- precedent_check / enforcement-lives-with-its-practice / `tools/*`: temporary, until 2026-11-16, by the session -- The check's own advisory term: temporary, waiting for the moves in spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md, revisit 2026-11-16. Each finding is one of those moves, already listed there.

Exclusions live in [tools/warning_exclusions.json](../tools/warning_exclusions.json); [tools/warning_review.py](../tools/warning_review.py) lists every open group.
<!--/vdc-embed:warnings-->

## Checks by stage

<!--vdc-embed:checks-by-stage: never hand-edit -- written by tools/very_deep_check.py's CHECKS BY STAGE section -->
Read from each repository's own push check and branch tool by this run (`tools/very_deep_check.py`, CHECKS BY STAGE). Before a push to staging or main only the quick tier may run: the bare essentials and the leak gate (Morgan, 2026-10-16 and 2026-10-17).

### this checkout

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | basic tier (`--full` on request: full; a plain push, or a pull request that is not a fast move's copy: basic) | GitHub: deep-check.yml (pull request into it), deep-check.yml (push), leak-gate.yml (push); else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (6): `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `verify_harness`, `precedent_check`, `doc_sync`, `deep_check`.

- **RETIRED**: Sync into pre-staging is pre-staging code still present (precedent_branches.py:2717, sync_pre_staging) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **RETIRED**: Promote from pre-staging into staging is pre-staging code still present (precedent_branches.py:4311, _promote_unlocked) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **RETIRED**: a push to staging still runs the full tier for a person who does not land on it, which only the retired pre-staging route left anyone doing (staging is a fully checked branch); delete it with the pre-staging code (todo/todo-2026-10-14-delete-pre-staging-code.md)

### precedent-individual

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | basic tier (`--full` on request: full; a plain push, or a pull request that is not a fast move's copy: full) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` untimed, `ci_workflows` untimed, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

- **RETIRED**: Sync into pre-staging is pre-staging code still present (precedent_branches.py:2650, sync_pre_staging) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **RETIRED**: Promote from pre-staging into staging is pre-staging code still present (precedent_branches.py:4194, _promote_unlocked) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **VIOLATION**: a push to main runs the full tier before it goes (main is a fully checked branch; the pre-push gate, and the merge gate for any pull request but a fast move's copy, read tier_for_branch) -- only the quick tier may run before a push to main
- **RETIRED**: a push to staging still runs the full tier for a person who does not land on it, which only the retired pre-staging route left anyone doing (staging is a fully checked branch); delete it with the pre-staging code (todo/todo-2026-10-14-delete-pre-staging-code.md)

### precedent-shared-writing

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | basic tier (`--full` on request: full; a plain push, or a pull request that is not a fast move's copy: full) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` untimed, `ci_workflows` untimed, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

- **RETIRED**: Sync into pre-staging is pre-staging code still present (precedent_branches.py:2650, sync_pre_staging) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **RETIRED**: Promote from pre-staging into staging is pre-staging code still present (precedent_branches.py:4194, _promote_unlocked) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **VIOLATION**: a push to main runs the full tier before it goes (main is a fully checked branch; the pre-push gate, and the merge gate for any pull request but a fast move's copy, read tier_for_branch) -- only the quick tier may run before a push to main
- **RETIRED**: a push to staging still runs the full tier for a person who does not land on it, which only the retired pre-staging route left anyone doing (staging is a fully checked branch); delete it with the pre-staging code (todo/todo-2026-10-14-delete-pre-staging-code.md)

### precedent-shared-ladder

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | basic tier (`--full` on request: full; a plain push, or a pull request that is not a fast move's copy: full) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` untimed, `ci_workflows` untimed, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

- **RETIRED**: Sync into pre-staging is pre-staging code still present (precedent_branches.py:2650, sync_pre_staging) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **RETIRED**: Promote from pre-staging into staging is pre-staging code still present (precedent_branches.py:4194, _promote_unlocked) -- pre-staging was retired 2026-10-14; delete it as todo/todo-2026-10-14-delete-pre-staging-code.md says
- **VIOLATION**: a push to main runs the full tier before it goes (main is a fully checked branch; the pre-push gate, and the merge gate for any pull request but a fast move's copy, read tier_for_branch) -- only the quick tier may run before a push to main
- **RETIRED**: a push to staging still runs the full tier for a person who does not land on it, which only the retired pre-staging route left anyone doing (staging is a fully checked branch); delete it with the pre-staging code (todo/todo-2026-10-14-delete-pre-staging-code.md)
<!--/vdc-embed:checks-by-stage-->
