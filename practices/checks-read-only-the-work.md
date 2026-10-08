---
slug:        checks-read-only-the-work
title:       A routine check reads only the work in front of it, never the whole history or other branches
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus. Any check, test, gate or hook a routine moment runs, wherever its code lives; the practice is a property of what a check reads, not of a path. Decided: 2026-10-08, with the practice."
occasion:    "writing, running or reviewing a gate, audit, cache or heavy solve"
gates:       []
index_clause: "read this change and its branch; never the whole history or other branches"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-08"
approved_by: "Morgan, 2026-10-08 -- \"WE SHOULD NOT RUN ANY TESTS THAT CHECK THE FULL HISTORY (NOR ANY BRANCHES OTHER THAN THE DIRECTLY RELEVANT ONES TO THE WORK / ISSUE OR THAT CHANGED) -- THIS NEEDS TO BE A STRONG PRINCIPLE.\""
strength:    decided
source_practice_number: null
---
## Rule
**A check that runs at a routine moment reads only the work in front of
it**: the files this change brings, the commits this branch adds over its
base, and the current version of the tree. Routine moments are a commit,
a push, a merge, a promotion from one branch tier to the next, the GitHub
check and Update Vendors. Such a check **never walks the whole history and never reads a
branch other than the ones the work is on or that changed**.

A check whose question seems to need the past is rescoped to the change:
the run's range, or this branch against its published base. **A
whole-history audit happens only when a person asks for it**: the very
deep check, or a check run by hand over a range that starts at the first
commit.

## Detail
**What counts as reading the work.** The diff of this branch against its
base (`base...HEAD`), the commits not yet on any remote (`HEAD --not
--remotes`), the range a gate was handed, and the files on disk now. A
local branch that holds unpublished commits has changed, so a check that
looks for unpublished work on every local branch reads only branches that
changed, and stays allowed.

**What does not.** `git log HEAD` over every commit, a walk of a
directory's whole history, a loop over every remote branch, or a read of
another branch's content. A count or a date taken from history to seed a
rotation reads no one's work and judges nothing; it is not a check.

**An explicit audit is the exception, and only by name.** A flag or
environment switch that restores the whole walk (`--all-history`,
`PRECEDENT_CHECK_FULL_HISTORY=1`), or a `--range` that starts at the first
commit, is fine when a person or the very deep check sets it on purpose.
No routine moment sets it.

**What the narrower scope gives up.** A problem is judged once, on the
change that caused it. One that slipped past then is not raised again on
every later push; finding it takes an audit someone asks for.

## Why
A check that reads the whole history re-judges every past change on every
run. Its cost grows with the repository's age, not with the change, and
an old problem nobody is working on comes back on every push as if it
were new. On 2026-09-22 the commit checks were rescoped to unpushed
commits for exactly this reason (Morgan: *"Whole history reviews are good
for things like very deep check but not for daily practice"*), but no
practice carried the rule, so it reached only those checks.

## Story
On 2026-10-08 a session timed the two slowest tests in the harness suite.
One of them ran an Update Vendors on a fake consuming repo, and its full
check spent 295 of 313 seconds in one check, `rename-updates-links`.
Morgan read the session's first account of it, which said the check
"scans the repo's full history", and set this rule in capitals. That
account was wrong: the check reads only the branch against its base, and
it was slow because of a loop that re-read every file once per deleted
path. That was fixed the same day, from 298 seconds to 1.

The audit his rule asked for found two checks that did walk the whole
history. `change-updates-its-docs` ran `git log HEAD` over every
deletion the repository ever made. `parallel-artifact-ledger`, when run
without a range, walked every commit ever made to the harness-adapter
directories. Both now read this branch against its base, and the harness
asserts each one's quiet half: a change already on the base is not judged
again on a later branch.

## Install
Nothing to wire. Review a new or changed check against the Rule. A check
that reads git history or branches names its scope in a comment, citing
this practice, the way `_paths_this_repo_removed()` and
`_parallel_artifact_ledger()` in
[tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) do.

**Why `checked_by` is null** (practice: checkable-gets-checked). A static
scan was tried on 2026-10-08, looking for a `git log` or `rev-list` call
inside a check with no range argument. What a call reads is decided by
arguments built at run time: a range variable, `--not --remotes`, a base
looked up from `origin`. Those arguments arrive through several wrappers
(`_git`, `subprocess.run`, and a check script's own helper). The scan
cannot tell `git log <range>` from `git log HEAD` without running the
code, so it would either pass the very calls this rule forbids or flag
the scoped ones it allows. The harness asserts the quiet half of each
check that was rescoped, which is the part a static scan could not prove
anyway.
