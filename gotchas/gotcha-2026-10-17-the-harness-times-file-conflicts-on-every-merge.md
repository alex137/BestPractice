---
slug:            gotcha-2026-10-17-the-harness-times-file-conflicts-on-every-merge
status:          live
noted:           2026-10-17
severity:        notable
retired:         null
retires_when:    "every BestPractice clone has the merge driver configured, so a session never sees this file conflict"
---
## Symptom

A merge of staging into a branch stops on a conflict in
`tools/harness_check_times.json`, often the only conflicted file. Or the
merge goes through and, later, `check_as_ci_parts_partition_the_suite`
fails with "the committed record names only checks that exist: stale: ...".

## Story

**2026-10-17.** The file conflicted on nearly every merge that day, in
three places at once: each `--record-new-times` appended to one shared
`measured` line, rewrote `default_seconds`, and inserted its test into a
sorted list beside another branch's. Sessions resolved it by hand, or by
taking both sides. Taking both sides brings back a test the other side
deleted: one merge into staging restored five timings an earlier pull
request had removed, and the partition case went red there.

## Fix

The file now merges itself. `.gitattributes` names a merge driver,
[tools/harness_times_merge.py](https://github.com/alex137/BestPractice/blob/staging/tools/harness_times_merge.py), which
keeps a test one side deleted deleted and a test either side added kept,
and `tools/bootstrap.sh` configures it in the clone at session start.
`--record-new-times` no longer touches the shared fields, and drops a
removed test's time on its own, in seconds.

**A session whose start-up hooks did not run** (one rooted above the repos
it works in) configures the driver by hand, once per clone:

    git config merge.precedent-harness-times.driver 'python3 tools/harness_times_merge.py %O %A %B'

A stale-name failure that is already on a branch goes away with
`python3 tools/verify_harness.py --record-new-times`.

**Prevention: the driver, and a planted case that proves it merges.**
`check_harness_times_merge_without_a_conflict` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py)
merges two branches that each record a test, one deleting another, and
fails on the old code. Session start configures the driver in each clone
(`precedent_session_check.py --merge-drivers`); a session rooted above its
repositories gets it from `python3 tools/precedent_run_session_hooks.py`,
or the one `git config` line above. Still live on 2026-10-31 (very deep
check of 2026-10-30, pass 4): this file's condition is about every clone,
and a clone whose start-up hooks never ran still lacks the driver.
