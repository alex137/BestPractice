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

## Notes

**Built 2026-10-07, not yet measured.** The deal is now by recorded time
(`_deal_by_time`), slowest first, each check to the least-loaded part. The
record is committed, `tools/harness_check_times.json`, rather than kept
under the git directory as proposed above: GitHub's deep-check job now runs
`--as-ci` itself, and a record local to each machine would deal the two
sides differently
([gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy](../gotchas/gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy.md)).
It was seeded from GitHub's own log of the run on pull request #953: the 86
checks that took two seconds or more are named, and the other 483 share the
rest of the 1,805 seconds, 0.23 each. On those numbers the three parts come
to about 602 seconds each. `--as-ci --record-times` refreshes it from a
green run.

The slowest single check, `check_update_vendors_survives_an_upstream_deletion`,
took 560 seconds of that on GitHub's runner, so no deal can bring a part
much under it.

Closes on its own condition: the next GitHub test on a pull request into
`main` shows the parts finishing within about a minute of each other.
