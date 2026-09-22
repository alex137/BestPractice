---
slug:              todo-2026-09-21-deep-check-definition-omits-the-ci-shards
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**What this repository calls a "deep check" runs
[tools/verify_harness.py](../tools/verify_harness.py) the one way that
cannot catch the class of bug
[gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-green-ci](../gotchas/gotcha-2026-09-21-a-green-local-verify-harness-run-does-not-mean-green-ci.md)
was filed for.**

[AGENTS.md](../AGENTS.md)'s "Two check levels" paragraph and
[practices/two-check-levels.md](../practices/two-check-levels.md) both
define the deep check as five gates: [`verify_harness.py`](../tools/verify_harness.py), [`doc_lint.py`](../tools/doc_lint.py),
[`leak_gate.py`](../tools/leak_gate.py), [`precedent_check.py`](../tools/precedent_check.py), [`doc_sync.py`](../tools/doc_sync.py). A session that follows
that definition exactly runs the harness with neither `PRECEDENT_CHECK_ONLY`
nor `PRECEDENT_CHECK_SKIP` set.

CI does not. [.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml)
shards the harness across two jobs on those variables, because
`check_precedent_check_fires` is about half the total runtime
([spec/VERIFY_HARNESS_PERFORMANCE.md](../spec/VERIFY_HARNESS_PERFORMANCE.md)).
The filter path they select is therefore code **no local run ever
executes**, and on 2026-09-21 that gap hid a crash: the full local suite
reported `244 passed, 0 failed` while both sharded CI jobs died before
printing a single verdict. The session that hit it had run the complete
deep check, seen it green, and opened a pull request to `main` on that
basis.

## Why It Is Still Open After the Gotcha

The gotcha's own Fix says to run both shards before trusting a green deep
check ahead of a push, and names the two commands. **Nothing carries that
instruction into a place a session reads.** The very deep check's
`INCIDENT COVERAGE` section reports this gotcha as "cited by NOTHING in
tools/ or practices/", which is accurate: the one-off crash has a control
(`check_filtered_check_does_not_break_the_unpack_family`), and the general
trap — any behaviour that differs only under the filter — is named nowhere
a session will meet it.

A gotcha nobody is routed to is a gotcha nobody reads. That is the whole
premise of [environment-gotchas](../practices/environment-gotchas.md)'s
split: the catalogue is grepped on a confusing failure, not browsed. This
failure is not confusing — it is green.

## The Options

1. **Widen the deep check's definition** to name the two shard commands
   alongside the five gates, in [`two-check-levels.md`](../practices/two-check-levels.md) and in AGENTS.md's
   own paragraph. Cost: two more runs before every push, each well under
   the full suite's runtime. This is the durable fix
   ([durable-fix](../practices/durable-fix.md)) and the one this item
   recommends.
2. **Have [`verify_harness.py`](../tools/verify_harness.py) run the filter path itself** on a default
   invocation — a self-test that sets the variables in a subprocess for a
   trivial check set, so one local run covers both shapes. Cost: the
   harness grows a mode that exists to test the harness.
3. **Have the workflow stop sharding**, so local and CI run the same
   command. Cost: the runtime [`spec/VERIFY_HARNESS_PERFORMANCE.md`](../spec/VERIFY_HARNESS_PERFORMANCE.md) split
   it to avoid, paid on every push.

## How It Was Found

The 2026-09-21 very deep check, working its `INCIDENT COVERAGE` section's
standing question — what prevents a recurrence, and is there a planted case
proving it fires? That run then ran both shards itself; both were green
(`243 passed, 0 failed` and `3 passed, 0 failed`), which is evidence the
tree is currently fine and no evidence at all that the next session will
think to look.
