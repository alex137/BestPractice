---
slug:              todo-2026-10-06-full-harness-runs-on-one-core
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

A full harness run (`python3 tools/verify_harness.py --all`) takes about 31
minutes, measured 2026-10-06: about 500 checks run one after another at a
couple of seconds each, plus three that take about 13 minutes between them
-- `check_precedent_check_fires` (about 5.5 minutes: it copies the whole
repository for each of 108 planted cases), `check_update_vendors_survives_an_upstream_deletion`
(about 4.5) and `check_changed_files_only_judges_the_change` (about 3.5).
The container has 4 cores and the harness uses one. Morgan, 2026-10-06:
"That feels very, very long."

## Proposed

Run independent checks across the available cores, and split the three
slow ones (the planted cases in `check_precedent_check_fires` already run in
worker processes two at a time; they could run as wide as the machine
allows). Measure before and after on the same tree. A target of about ten
minutes looks reachable from these numbers, not promised.

## How It Closes

A full run on a 4-core container takes well under half its 2026-10-06 time,
with the same checks and results.
