---
title:         A changed check runs its own tests at push time
kind:          proposal
status:        accepted
opened:        2026-10-11
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "When a push changes a check in precedent_check.py, code a check uses, a tools/ module a check imports, a check script, or a harness test, the quick push check now runs those checks' own harness tests -- what fits in about a minute, the rest named with the command that runs them. A check whose only test is its planted case gets a visible note until that case can run alone."
---

# A changed check runs its own tests at push time

**Approved by Morgan on 2026-10-11 ("Let's build"), after two review rounds
with a second session.**

## What happened

On 2026-10-11, `a243d9c0` made `practice-file-shape` in
[tools/precedent_check.py](../tools/precedent_check.py) require `## Why`,
`## Story` and `## Install`. The harness test that feeds that check a
well-formed sample (`check_practice_file_shape_judges_one_file_at_a_time` in
[tools/verify_harness.py](../tools/verify_harness.py)) still had only
`## Rule`, so the control read as malformed and staging went red. `192c735b`
fixed the sample 17 minutes later. Run alone at `a243d9c0`, that test fails
in about 2 seconds; at `192c735b` it passes.

A session proposed a process rule: a check that gains a requirement updates
its sample in the same commit. That rule depends on memory. The session that
tightened the check was careful -- it deleted the suite test the check
replaced -- and still missed the sample, which lived in a different test in
a 75,000-line file.

## The cause

A push to a working branch or to staging runs the changed-files step of
[tools/precedent_push_check.py](../tools/precedent_push_check.py). That
step already runs a check script's `tests/test_x.sh` when the script
changes, and two harness sync tests when the harness changes. It never ran
the harness tests of a check inside
[`precedent_check.py`](../tools/precedent_check.py), so the commit
that changed the check never met its own test before it landed.

## The fix (step 1)

1. **`verify_harness.py --for-change REF`** works out which harness tests a
   change since `REF` can affect, and runs them. A test is selected when the
   change touches:
   - a `@check` in [`precedent_check.py`](../tools/precedent_check.py) (its range starts at the decorator);
   - a helper, constant or import there that a check uses, directly or
     through other helpers -- the registry itself reaches every check;
   - a `tools/` module a check imports, directly or through other modules;
   - a check script ([`tools/checks/check_session_trailer.py`](../tools/checks/check_session_trailer.py),
     [`tools/check_commit_author.py`](../tools/check_commit_author.py) and the like),
     matched by its file name in a test's code;
   - a harness test itself, or a harness helper a test uses.

   For a check, its tests are the `check_*` functions that call its
   implementation function, or name its slug as a string in code --
   `check_precedent_check_fires` excluded, since it is the 13-minute planted
   suite. A hunk that falls on a comment between definitions maps to
   nothing; anything that cannot be parsed is said, with the full-tier
   command.
2. **A budget.** It runs what fits in about 60 seconds of the tests'
   recorded times ([tools/harness_check_times.json](../tools/harness_check_times.json)),
   directly changed checks first, and names the rest with the command that
   runs them and that the full tier will. A changed check whose only harness
   coverage is its planted case gets the same note. None of these notes
   refuses the push; a test that runs and fails does.
3. **The push check calls it** in one subprocess, only where
   [`tools/verify_harness.py`](../tools/verify_harness.py) exists, so a consuming repo carries the line
   unused.
4. **Shell tests are found by content.** A changed check script runs every
   `tests/test_*.sh` beside it that names it, so two scripts sharing one
   test (the philosophy pair) are covered without a hand-kept map.
5. **A harness test** plants each kind of change in a scratch repository and
   asserts the selection and the notes.
6. The good-sample lesson goes into
   [todo-2026-09-29-planted-case-lives-beside-its-check](../todo/todo-2026-09-29-planted-case-lives-beside-its-check.md).
   The proposed process rule is dropped: the push check now catches the
   mistake.

## Step 2, later

Run one check's planted case alone. Today one slug alone takes about 225
seconds, because 18 slugs are pinned together by later assertions that read
their results. That waits on a separate session measuring how to speed up or
replace `check_precedent_check_fires`; the per-slug filter will plug into
`--for-change`.

## What it buys, and what it does not

Today's mistake would have been refused at push, in seconds, and so would
the same mistake in any check with a direct harness test or in a module it
imports. A push that touches no Python under `tools/` pays nothing. A change
to something every check depends on runs about a minute of tests and names
the rest; the full tier still runs everything.
