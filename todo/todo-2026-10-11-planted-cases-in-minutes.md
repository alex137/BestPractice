---
slug:              todo-2026-10-11-planted-cases-in-minutes
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a go-ahead: the 2026-10-11 ask was to measure and propose, not to build"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-11
closed:            null
---
## What

`check_precedent_check_fires` in
[tools/verify_harness.py](../tools/verify_harness.py) took 487 seconds
alone on a 4-core container, measured 2026-10-11, and was recorded at 777.5
under `--as-ci`. While it runs as one block, nobody can run one check's
planted case on its own in a few seconds. The measurements are in
[spec/VERIFY_HARNESS_PERFORMANCE.md](../spec/VERIFY_HARNESS_PERFORMANCE.md#2026-10-11-where-check_precedent_check_firess-eight-minutes-go).

## Proposed

All of it is in [`tools/verify_harness.py`](../tools/verify_harness.py), which is not vendored.
[`tools/precedent_check.py`](../tools/precedent_check.py) and every other vendored file stay as they are.

**Step 1, prototyped and measured: 487 s down to 216 s, all 331 stated
cases passing. Built 2026-10-11 (go-ahead in chat: "Build step 1 and
book it"); steps 2 and 3 stay open.**

1. Fixture `git` runs with `-c core.hooksPath=/dev/null`, in the function's
   `git()` helper and its direct `git` calls. No case depends on a global
   hook firing, and the [`precedent_check.py`](../tools/precedent_check.py) runs are untouched.
2. The baseline repository is repacked once, after its commit.
3. Each case's worker deletes its own fixture when its run is done, instead
   of one bulk delete at the end (108 s of the old run).
4. `case()` returns at once, with as many processes in flight as the
   machine has cores, plus two. `planted` resolves a pending case when
   something reads it (`[]`, `in`, `.get`, `.items()`), and the baseline
   bare run goes in the background. All of it is settled before the closing
   assertions.

**Step 2, estimated and not measured: about 2 to 2.5 minutes for the
whole run.** Put the error-isolation `--full-sweep` (31 s) in the
background like the baseline. Make each of the roughly 44 bespoke
fixtures outside `case()` a unit tagged with the slug it tests, so the
units run side by side.

**Step 3, one slug alone: `PRECEDENT_PLANTED_ONLY=<slug>[,<slug>]`.** It
runs only that slug's `case()`, its bespoke units and its later assertions
(the step 2 tag), and it skips the baseline and the error-isolation sweep.
The registry assertion still runs, because it only reads source. As with
the rotation today, the result line names the narrowing. Measured as a
standalone pipeline it takes 2.4 to 3.7 s for a typical slug, and 7 s for
`hooks-on-disk-are-reachable` before its bespoke fixtures. Like the
rotation, it is a path only some runs take
([gotcha](../gotchas/gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-green-ci.md)),
so it needs its own stated cases, next to
`check_planted_case_rotation_never_narrows_silently`.

**Coverage.** The full run keeps every case. The one-slug mode runs one
slug by design and says so in its result line. The width of 6 processes is
bounded on purpose:
[gotcha-2026-09-18](../gotchas/gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools.md)
is a fan-out of this kind that ran out of memory.

**A lead, not measured:** the slow update-vendors and changed-files checks
also build fixture repositories, and probably pay the same global-hook toll
locally.

Step 2's units are also the first move toward
[todo-2026-09-29-planted-case-lives-beside-its-check](todo-2026-09-29-planted-case-lives-beside-its-check.md):
a case that is one unit per slug can later move beside its check.

**Asked again, 2026-10-29.** After the Produce that day, Morgan asked why
the test does not reuse one repository instead of building a fresh one per
case. That was tried on 2026-09-19 and reverted
([spec/VERIFY_HARNESS_PERFORMANCE.md](../spec/VERIFY_HARNESS_PERFORMANCE.md#reverted-reusing-one-fixture-directory-instead-of-copying-fresh-per-case)):
a 10-20% gain, because the cases that make commits, remotes or branches
need a full rebuild anyway, bought with three safety mechanisms in the one
test that exists to catch a check that never fires. Since step 1 a copy
costs about a third of a second, so reuse would save less today. The same
day, GitHub's `--as-ci` run timed this test at 519 s, against 188-218 s
locally after step 1; that gap is not measured. This is the third time the
test's length has come up (2026-10-06, 2026-10-11, 2026-10-29). Steps 2
and 3 still wait on a go-ahead.

**Moved out of the everyday runs, 2026-10-29.** By Morgan's decision that
day ([todo-2026-10-29-landing-runs-the-tests-it-reaches](todo-2026-10-29-landing-runs-the-tests-it-reaches.md)),
this test now runs only in the nightly run, a by-hand GitHub run and the
very deep check. Steps 2 and 3 still matter there, and step 3 would let a
landing run just the planted cases of the checks it touched.

## How It Closes

The whole function runs in under a third of its 2026-10-11 time (487 s) on
a 4-core container, with the same stated cases. One slug's planted case
also runs alone, by name, in under 15 seconds.
