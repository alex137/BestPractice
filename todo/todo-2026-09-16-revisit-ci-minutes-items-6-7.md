---
slug:              todo-2026-09-16-revisit-ci-minutes-items-6-7
kind:              manual
domain:            content
severity:          notable
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Not doing items 6 and 7 for now: the CI minutes problem they were meant to address is solved."
decision_strength: decided
waiting_on:        null
noted:             2026-09-16
closed:            2026-10-11
---
## What

Get back to items 6 and 7 of
[spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md) — held out of the
2026-09-16 "go update" that implemented items 1 through 5. Item 6 is the
self-hosted-runner pilot (moving the highest-volume, lowest-sensitivity
lint jobs off metered GitHub-hosted minutes onto Morgan's own Linux
server or a RunCloud instance). Item 7 is checking Settings → Billing →
Actions directly for the account's actual included-minutes ceiling and
how much of it is already used, including the spike from 2026-09-16 that
the attached usage report didn't cover.

## How It Closes

`status` becomes `done` when Morgan has decided whether to run the
self-hosted-runner pilot (and on which repos) and has checked the actual
billing ceiling, or explicitly decides to defer either one further.

## Notes

**Closed 2026-10-11 (done).** Morgan deferred both items: "we not do those for now and remove the to-do; we solved the problem." That meets this item's own condition (he explicitly decided to defer either one further); strength: decided.
