---
slug:              todo-2026-10-29-landing-runs-the-tests-it-reaches
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Morgan, 2026-10-29: scoped harness run after each landing on staging and on main; the planted-case sweep only nightly and in the very deep check"
decision_strength: decided
waiting_on:        null
noted:             2026-10-29
closed:            2026-10-29
---
## What

The 2026-10-29 Produce turned `main` red on five harness cases, each a
test left stale by a commit landed on staging that day, not a broken
engine: three per-part budget tests after the session-load total was
recorded in this repository's registry, a reply-check fixture after "a
reply is never compared with its own turn", and a stage list after
`--land-confirm`. No full run was on record for staging, by design: the
fast Produce merges first and GitHub's test reports after (Alex,
2026-10-08). The fix was
[alex137/BestPractice#1393](https://github.com/alex137/BestPractice/pull/1393),
about 20 minutes later.

Morgan asked the same day whether the Debut or Produce full test should
review the tests a change touches for ones it made stale.

**Measured the same day:**
[`tools/harness_reach.py`](../tools/harness_reach.py)` select`, run on each
culprit commit against its parent, names every failing case:

| commit | checks reached | failing cases it names |
|---|---|---|
| `3b6ce672c` (record the 10,000 total) | 398 of 840 | all four |
| `1441a2b51` (own-turn reply check) | 231 of 841 | the delete-link control |
| `1b63e318b` (`--land-confirm`) | 216 of 849 | the stage list |

`check_precedent_check_fires` is reached by every one of them (it reads
[MAP.md](../MAP.md)), and took 519 s in that day's GitHub run.

## Proposed

Answered with three options; the session's pick is the third, paired with
steps 2 and 3 of
[todo-2026-10-11-planted-cases-in-minutes](todo-2026-10-11-planted-cases-in-minutes.md),
which keep it cheap:

1. Keep it: `main` goes red now and then and is fixed in the same sitting.
2. Make the Debut required before every Produce: each Produce waits on the
   full suite, and the author of a break is long gone.
3. After a landing on staging, the landing session runs, in the
   background, the harness checks
   [`tools/harness_reach.py`](../tools/harness_reach.py) says that landing
   reaches, and fixes what fails before it ends. Nothing new runs before a
   push, so the quick tier stays closed.

A session reading the tests for staleness was set aside: none of the five
looked wrong on reading; each failed only when run.

## Decided and Built

Morgan, 2026-10-29 (strength: decided), choosing a fourth shape over the
three above: "Let's have the test of only what's relevant (what you built
for alex) run upon each staging; and also, upon each produce, let's have
it run *afterwards* after the push to main, in what runs now; AND let's NO
LONGER RUN the full 519 second test of everything on main. *BUT* let's add
back that full 519 second test two places: it should run when I do a 'very
deep test'; and also ... in the nightly tests".

Built the same day:

- **After each landing**, [`tools/precedent_branches.py`](../tools/precedent_branches.py)
  prints the command for the checks that landing reaches, measured from
  the tip it landed on (`PRECEDENT_HARNESS_SINCE`, read by
  [`tools/harness_reach.py`](../tools/harness_reach.py)), to run in the
  background; `--land-confirm` prints it too.
- **`check_precedent_check_fires` runs only in a whole-suite run asked for
  by name** (`--all`, which the very deep check runs, and
  `PRECEDENT_HARNESS_FULL=1`, which GitHub's nightly and by-hand runs set),
  in [`tools/verify_harness.py`](../tools/verify_harness.py)'s
  `_planted_sweep_runs`. The pull request into main, the push after a
  Produce and a Debut leave it out, even when the change reaches most of
  the suite.

Estimated from the recorded check times (2026-10-09 basis, 4 cores), a
landing's run is about ten minutes, in the background; most of it is the
Update Vendors checks, which are picked every time because their reach is
not fully seen. Not measured as a run.

## How It Closes

Morgan picks an option. If it is the third, a landing session runs the
reached checks after landing and reports their result, and a Produce
that follows a day of such landings does not turn `main` red on a stale
test.
