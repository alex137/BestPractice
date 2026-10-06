---
slug:              todo-2026-10-06-deal-harness-checks-by-measured-time
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

`verify_harness.py --as-ci` (and now a bare `--all`) deals the rest shard's
checks to its parts alphabetically, so the slow ones bunch up. In a Debut on
2026-10-06 the three parts took 634, 316 and about 640 seconds, and the
heavy shard 422. One part held
`check_update_vendors_survives_an_upstream_deletion` (298 seconds) and four
more over 15 seconds. Morgan, 2026-10-06: "Speeding up the checks is very
important."

## Proposed

Record each check's duration at the end of a run (the harness already
collects them in `CHECK_DURATIONS`) in a file under the git directory, and
have `_as_ci_runs` deal the slowest first to whichever part has the least
time so far, falling back to the alphabetical deal when there is no record.
On these numbers the three parts would come out nearer 530 seconds each.
The isolated run's copy has its own git directory, so the parent would pass
the record's path in.

## How It Closes

A full run's parts finish within about a minute of each other, measured on
the same container.
