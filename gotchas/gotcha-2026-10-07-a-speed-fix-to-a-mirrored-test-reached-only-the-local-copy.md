---
slug:            gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy
status:          live
noted:           2026-10-07
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

GitHub's test on a pull request into `main` takes about 30 minutes, while
the same suite run here with `python3 tools/verify_harness.py --as-ci`
takes about 11. One GitHub job, "verify_harness (everything else)", holds
nearly all of it.

## Story

**2026-09-30.** A session sped up the suite's local run: `--as-ci` started
its shards side by side and cut the big "everything else" shard into parts,
one per core. It was measured here, and closed on the numbers here.

**2026-10-06.** A bare `--all` got the same treatment, again measured here:
about 31 minutes down to about 11.

**2026-10-07.** Morgan asked why a Produce waited 30 minutes. GitHub's
"everything else" job had run 569 checks one after another on one core:
1,805 seconds of checks. The split had been written in two places, the
workflow's own jobs and the harness's `CI_SHARDS` table, and only the
harness side ever learned to cut the rest into parts. The check that was
meant to keep the two in step compared the workflow's two jobs with the
table's two rows. They still matched, because the new split lived below
the table, so it stayed green for a week. Every Promote into main paid the
difference, and the session that reported the 30 minutes that evening
quoted it as a fact instead of asking why it was three times the local
run.

## Fix

The workflow no longer describes the split. Its one job runs
`python3 tools/verify_harness.py --as-ci`, the same command a session
runs, so `CI_SHARDS` and `_as_ci_runs()` are the only description there
is. `check_as_ci_shards_match_the_workflow` now refuses any other way of
running the suite in the workflow, and any split variable set there
(`PRECEDENT_CHECK_ONLY`, `PRECEDENT_CHECK_SKIP`, `PRECEDENT_HARNESS_ALL`,
`PRECEDENT_AS_CI_JOBS`), with a planted copy of the old two-job workflow
among its cases. The parts are dealt by the committed
`tools/harness_check_times.json`, not by the machine's cores, so both
sides deal the suite identically. Refresh it with
`--as-ci --record-times`.

**The general lesson:** when a fix speeds up, or otherwise changes, a check
that runs in two places, measure it in both before calling it done. A
local number says nothing about the copy GitHub runs. Better still, leave
one copy: have the second place run the first one's command.
