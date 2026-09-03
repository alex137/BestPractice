---
slug:        merge-target-is-beta-branch
title:       Every merge targets precedent-beta-v01, never main, unless Alex says otherwise
tier:        on-demand
severity:    blocking
applies_to:  ["**"]
occasion:    "opening or merging a pull request in this repository"
gates:       ["merge"]
index_clause: "every PR targets precedent-beta-v01; main only on Alex's explicit say-so"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "Alex, 2026-09-03"
---
## Rule
Until Alex reviews and approves `precedent-beta-v01` and merges it into
`main` — a deliberate, phase-7 act Alex performs or explicitly authorizes —
every pull request (PR) opened in this repository targets
`precedent-beta-v01`, never `main`. Before opening or merging a PR, confirm
the base branch is `precedent-beta-v01` — do not assume `main` is the
default just because it is the repository's configured default branch.
Merging into `main` requires Alex saying so explicitly, in that specific
request, naming `main` by name — a general "PR and merge it" authorization
means `precedent-beta-v01`.

## Detail
This holds even when `main` and `precedent-beta-v01` happen to be at the
same commit, which is exactly the condition under which the incident this
practice exists to prevent occurred — the two branches looked
interchangeable at that moment, and they were not.

## Why
`main` is this repository's public, shared default branch; `precedent-beta-v01`
is the working branch for the Precedent restructuring
(`PRACTICE_ENGINE_PLAN.md`: "Precedent is a branch of BestPractice, not a
fork" — merging back to `main` is `CHANGES_TO_TELL_ALEX.md`'s explicit,
deferred phase-7 step, not something any single PR does incidentally). A
branch based off `precedent-beta-v01`'s tip, opened with `base: main`,
merges cleanly with no conflict and no warning — git has no concept of
"the wrong branch," only of mergeable or not — so nothing in the mechanics
of opening or merging the PR signals the mistake. The only thing that
catches it is checking the base explicitly, every time, before acting.

## Story
2026-09-03: a session built two new practices on a branch created from
`precedent-beta-v01`'s tip, then opened and merged the PR with `base: main`
— main and precedent-beta-v01 happened to be at the identical commit at
that moment, so the merge produced no conflict and reported success
cleanly. Because the working branch's own history included all of
`precedent-beta-v01`'s unmerged restructuring work (phases 1 through 6,
roughly 600 files), the merge silently carried that entire body of work
onto `main` — work `CHANGES_TO_TELL_ALEX.md` already named as deliberately
staying off `main` until a real phase-7 review. Caught only because Alex
happened to ask "did that merge to main?" afterward. Fixed with a
`git revert -m 1` PR against `main` (verified byte-identical to `main`'s
real pre-incident tree) and a second PR re-targeting `precedent-beta-v01`
correctly. This practice is the fix that stops a session from needing to
be asked.

## Install
`tools/precedent_check.py`'s `merge-target-is-beta-branch` check compares
`origin/main` against `origin/precedent-beta-v01`: if `precedent-beta-v01`
is an ancestor of `main` — meaning its work has landed there via a merge —
the check fails, unless this practice has already been retired (see
below). It reports `NotApplicable` when either ref is not fetched locally,
since it cannot compare branches it cannot see; run
`git fetch origin main precedent-beta-v01` first if it skips. It cannot
catch a PR opened with the wrong base *before* that PR is merged — only
that a merge already happened. `gates: ["merge"]` surfaces this practice's
Rule via `python3 tools/precedent_gate.py merge`, which is the check-before
step.

**A second, load-bearing gap, disclosed rather than assumed away**:
because this is a repo-local practice (declared in `precedent.json`,
`path: "local"`, per `PRACTICE_ENGINE_PLAN.md`'s "Source" section) and this
repository's own generated `AGENTS.md` loader block stays deliberately
single-source (`precedent.json`'s own `_comment`: "this repo's own
session-loading is the universal catalogue alone"), this Rule does **not**
reach a session through the normal resident/occasion-index channel the way
a universal practice would. `AGENTS.md`'s hand-authored "Working in this
repo" section carries the same rule directly, in prose, for exactly that
reason — belt and suspenders, not redundancy.

**Retirement.** The moment Alex actually reviews and merges
`precedent-beta-v01` into `main` for real, delete this file,
remove the `merge-target-is-beta-branch` check from
`tools/precedent_check.py`, and remove the pointer from `AGENTS.md` — in
that same PR, not left as later cleanup.
