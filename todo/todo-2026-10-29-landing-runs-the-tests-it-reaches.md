---
slug:              todo-2026-10-29-landing-runs-the-tests-it-reaches
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a go-ahead: the 2026-10-29 ask was a question, answered with options"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-29
closed:            null
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

## How It Closes

Morgan picks an option. If it is the third, a landing session runs the
reached checks after landing and reports their result, and a Produce
that follows a day of such landings does not turn `main` red on a stale
test.
