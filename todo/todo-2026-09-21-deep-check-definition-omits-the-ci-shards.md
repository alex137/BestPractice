---
slug:              todo-2026-09-21-deep-check-definition-omits-the-ci-shards
kind:              manual
domain:            engine
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Option 1, delivered as one command rather than an instruction -- Morgan, 2026-09-22: \"Build both, CI shard fix first\""
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-22
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

## Closed 2026-09-22 — option 1, delivered as a command

The definition is widened, and the thing it names is
`python3 tools/verify_harness.py --as-ci`: one command that runs both CI
shapes in sequence, each in its own process with both filter variables
cleared first so an exported one cannot skew a shard.

**Option 1 as written said "two more runs before every push", and that
overstated the cost.** The shards PARTITION the suite. Measured in this
tree, 2026-09-22: **4m01s for `--as-ci` against roughly 4m20s for one plain
run.** It is one run's work, split the way CI splits it.

**Delivered as a command, not a sentence**, which is the part the option
list did not say. An instruction to run two extra commands is skipped
exactly when time is short — the drift `two-check-levels`' own **Why**
already names — so the repo's tool grew the mode and the definition names
one thing.

**Its limit is stated wherever it is named**, because over-promising here
would repeat the failure it fixes: `--as-ci` reproduces CI's command
**shape**, never CI's **environment**. A local session resolves private
practice sources CI has no credential for, so a check keyed to one can fail
here and pass there. Green under `--as-ci` means the sharding is not what
breaks. It does not mean CI is green. Its first real run demonstrated
exactly that — the `rest` shard green at 253 passed, the `heavy` shard
carrying the known local-only vocabulary failure.

**The table cannot drift from the workflow**:
`check_as_ci_shards_match_the_workflow` asserts every variable and value in
`CI_SHARDS` against `.github/workflows/deep-check.yml`, in both directions,
and was proven to fail when the table is altered. A local command claiming
to run "what CI runs" that has quietly drifted is worse than no command at
all — it returns green with authority.

**The general rule went upstream, not just the fix**:
[two-check-levels](../practices/two-check-levels.md) now carries it as a
Detail — a deep check must run each gate in the shape CI runs it, deliver
that as one command, and say what the mode does not prove — so every repo
that vendors this practice gets the rule rather than this repo keeping the
lesson to itself.

