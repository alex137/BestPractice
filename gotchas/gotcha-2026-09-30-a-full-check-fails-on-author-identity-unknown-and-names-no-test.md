---
slug:            gotcha-2026-09-30-a-full-check-fails-on-author-identity-unknown-and-names-no-test
status:          live
noted:           2026-09-30
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

`python3 tools/precedent_push_check.py` ends `FAILED -- verify_harness`, and
the report under it shows only a list of `SKIP (filtered out by
PRECEDENT_CHECK_ONLY/SKIP)` lines and timings. No test is named. Run again,
it may pass.

## Story

**2026-09-30, twice in one evening.** The push check runs the harness as
`--as-ci --isolated`: a fresh copy of the commit, with an empty `$HOME` and
no git identity, its shards running side by side in that one copy, and then
a short "not-applicable slice" run in place. The push check printed the
last 40 lines, which were the slice's skip list. The failure was further
up, in one shard: `verify_harness FAIL: could not create a scratch commit
... Author identity unknown`.

`_ref_including_worktree()` makes that commit only when the working tree
differs from HEAD. A fresh copy does not, unless another shard has just
written a file into the shared copy, and then it does for a moment. On a
person's own machine an identity exists, so the commit succeeded and the
stray file went into the snapshot unnoticed. In the isolated copy there is
none, so the run failed. Run on its own, the same shard passed and left
nothing behind, which is what pointed at the shards sharing the copy.

## Fix

The scratch commit carries its own identity (it is never pushed or
checked out), so the snapshot no longer depends on the machine having one
(`check_worktree_snapshot_needs_no_git_identity`).

The push check's report now picks `SHARD FAILED` and a line like
`verify_harness FAIL: ...` as findings; it used to recognize only a line
that began with `FAIL`, so it showed nothing. **If a full check still fails
naming no test, read the isolated run itself:**
`python3 tools/verify_harness.py --as-ci --isolated`, and look for
`SHARD FAILED`.

The writer was the leak-probe check, which wrote `ZZ_leakprobe_fixture.md`
into the shared copy while its gate ran. Another session found it the same
night and moved those fixtures into a throwaway worktree (`3e7da369`), so
the race and its cause are both closed.
