---
slug:              todo-2026-10-19-deferred-main-run-reads-as-passed
kind:              analysis
domain:            mechanism
severity:          high
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          fix it in the engine
decision_strength: decided
waiting_on:        null
noted:             2026-10-19
closed:            2026-10-19
---
## What

`github_test_state` in [tools/precedent_branches.py](../tools/precedent_branches.py)
read `main` as passing while the only run that tested its files had failed.

On 2026-10-19 the Produce in #1240 merged at once, as the short way says.
The pull request's run of [deep-check.yml](../.github/workflows/deep-check.yml)
was still going, so the push run on `main`'s tip (`d94c11c5`, run
39268820697) took the "still going and decides" branch of its
already-tested job: it skipped the suite and finished `success` in 16
seconds. The pull request's run then failed (run 39268688641, issue #1242).
`github_test_state(d94c11c5)` measured `passed`, because the newest run per
workflow decides, and `_newest` drops only runs whose own conclusion is
`skipped`. A run whose test job was skipped but whose decision job passed
concludes `success`.

What read it wrong:

- `red_main_fix` (through `main_test_failed`) refused the fix pull request
  straight into `main` (#1243): it saw `main` green. The fix went through
  staging and a second Produce (#1244, #1246) instead.
- [tools/precedent_update.py](../tools/precedent_update.py) and [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) read the same
  state, so Update Vendors elsewhere would have taken the red `main` as its
  "newest main whose test passed" for the half hour it was red.
- `--wait-main-test` got it right only because it waits on the Promote
  copy's head, not on `main`'s tip.

## Proposed fix

In `github_test_state`, count a run that tested nothing -- its decision job
passed and every other job was skipped -- as not having happened, when
another run for the same workflow (the pull request head's) exists. Then
that run decides. One extra API call per such run, counted by
[tools/github_budget.py](../tools/github_budget.py). If ignoring it leaves no run, keep it, so a
tree-identical re-run that leaned on an earlier pass does not turn into
"never ran". A verify_harness case plants the 2026-10-19 runs (deferred
push success newer than a failed pull request run) and fails on today's
code.

The other place to fix it is the workflow: a deferred push run could wait
for the pull request's run and copy its conclusion. That bills Actions
minutes for waiting, which the minutes rule is against, so the engine
side is the pick.

## Done, 2026-10-19

Morgan, 2026-10-19 (strength: decided): "yes, fix the engine and the two
small ones". Fixed as proposed in
[tools/precedent_branches.py](../tools/precedent_branches.py)
(`_tested_nothing`, `DECISION_JOB`). Measured on the real runs:
`d94c11c5` read `passed` before and reads `failed` now; `cc1a9e18`, after
the fix reached main in #1246, still reads `passed`.
`check_main_test_cadence` carries the case, which fails on the old code.
