---
slug:              todo-2026-10-06-merge-refusal-misreads-a-stale-to-main-copy
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-06
closed:            null
---
## What

When staging moves while a pull request into main waits on its GitHub
test, the merge check refuses that pull request with *"a pull request into
main is merged only from staging here ... Retarget it at pre-staging, merge
it there, and say Promote."* The refusal is right and the remedy is wrong.
The head is the promote tool's own `to-main-...` copy of staging, and it no
longer matches staging's tip. Retargeting it at pre-staging would be a
mistake.

Seen 2026-10-06: a second Debut ran while the Produce pull request waited
on its test. A session first read the refusal as the two tools
contradicting each other. They don't: when main has not moved past
staging, the copy is staging's exact tip, and that passes.

## Proposed

In `merge_refusal` in [tools/precedent_branches.py](../tools/precedent_branches.py),
when the base is main and a head starts with `to-main-`, say what
happened: *this copy of staging is out of date, because staging has moved
since it was made. Close it, run the Produce again for a fresh copy, and
open the pull request from that.* Plant the case beside the existing
`merge_refusal` cases in [tools/verify_harness.py](../tools/verify_harness.py).

## How It Closes

A stale `to-main-...` head is refused with the remedy above, and a planted
case shows it.
