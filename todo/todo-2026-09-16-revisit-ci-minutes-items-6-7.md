---
slug:              todo-2026-09-16-revisit-ci-minutes-items-6-7
kind:              manual
domain:            content
severity:          notable
status:            open
disposition:       ask
remind_on:         "2026-09-19"
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-16
closed:            null
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
