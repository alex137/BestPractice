---
slug:              todo-2026-10-28-one-session-load-total
kind:              decision
domain:            mechanism
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "Morgan's go on the plan (needs: decision -- Morgan)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-28
closed:            null
---
## What

Token-budget blocks came back on 2026-10-27 and 2026-10-28 because tokens
moved between budgets (rules moved into the ladder set, sets copied into
repositories, a fix to how a share is counted), not because sessions got
heavier. Every budget is a separate tight number only Morgan can raise, so
any change to which budget pays for a rule asks him again.

The analysis and the proposal are in
[spec/SESSION_LOAD_ONE_TOTAL_PLAN.md](../spec/SESSION_LOAD_ONE_TOTAL_PLAN.md):
one refusing number per session, the total it loads, declared once by the
person; every part's cap becomes a notice.

## Closes when

Morgan says go or no to the plan. On go, the engine change lands and his
total is recorded in the individual set; on no, the reason goes here.
