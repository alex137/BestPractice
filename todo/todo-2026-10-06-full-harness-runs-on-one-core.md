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

**Where the 31 minutes came from, measured 2026-10-06.** Only a bare
`--all` ran in one process -- the very deep check's step 2 is the one place
that runs it. The push check's full tier already ran `--as-ci`: four
processes side by side. In a Debut that day it took 646 seconds, against
about 1,900 seconds of checks. The heavy shard (`check_precedent_check_fires`
alone) took 422 seconds. The other three took 634, 316 and about 640
seconds, because checks are dealt to them alphabetically and the slow ones
bunch up: one part held
`check_update_vendors_survives_an_upstream_deletion` (298 seconds) and
four more over 15 seconds.

**Done 2026-10-06:** a bare `--all` now runs as `--as-ci` with every planted
case in every process (`check_bare_all_runs_across_the_cores`);
`PRECEDENT_HARNESS_SERIAL=1` keeps the one-process run for profiling.

**Still open:** deal the rest shard's checks by measured duration rather
than by name, which on these numbers would bring the three parts nearer
530 seconds each.

## How It Closes

A full run on a 4-core container takes well under half its 2026-10-06 time,
with the same checks and results.
