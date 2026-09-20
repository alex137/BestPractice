---
slug:            gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools
status:          retired
noted:           2026-09-18
severity:        null
retired:         2026-09-18
retires_when:    "tools/precedent_resolve.py's _self_heal_stale_render() carries the PRECEDENT_SELF_HEAL_IN_PROGRESS reentrancy guard -- condition met the same day, below"
---
## Symptom

`python3` [`tools/verify_harness.py`](../tools/verify_harness.py) gets
silently killed partway through (exit 137, no FAIL printed, no Python
traceback) at a different check each time, somewhere between roughly a
quarter and two thirds of the way through its 172 checks.

## Story

Landing a single new practice file, `verify_harness.py` was run five times
in one session chasing what looked like a flaky test. Four of the five runs
died at exit 137 with no error message — once at 23/172 checks done, once
at 117/172, twice more at almost exactly the same spot (45 `PASS` lines in).
The one run that *did* complete printed a single genuine `FAIL` (a missing
`routing_scope.json` entry for the new practice, unrelated to the crashes)
and every other check passed.

`dmesg` named the actual cause, which nothing in the tool's own output
hints at:

```
oom-kill:constraint=CONSTRAINT_MEMCG, ... task_memcg=.../claude-code-bash
Memory cgroup out of memory: Killed process ... (python3)
```

The Bash tool runs inside its own memory cgroup, separate from the
container's overall RAM. `ps aux` during a live run showed the cause:
one of the harness's "N stated cases" checks (the neighborhood of
`check_precedent_check_fires`, `check_session_check_reports_a_dead_also_list_entry`
and the session-bootstrap fixtures around it) fans out into hundreds, and at
its peak over a **thousand**, concurrent
[`precedent_session_practices.py`](../tools/precedent_session_practices.py)
subprocesses — each individually tiny (a few MB), but enough of them at once
to blow a cgroup ceiling sized in the low tens of GB, well before the host's
own free memory ran out. `free -h` on the host looked fine throughout; only
the cgroup's own `memory.usage_in_bytes` told the real story.

Leftover children from a killed run do not always get reaped: a `pkill -9 -f
precedent_session_practices.py` was needed between attempts to bring the
cgroup back down before the next run had any headroom at all — otherwise a
"clean" retry inherited the previous run's half-cleaned-up processes and hit
the ceiling even sooner.

This is a genuinely intermittent trap, not a fixed threshold: the same
unchanged tree completed cleanly once and died differently three more times,
depending on exactly how much of the cgroup's ceiling prior activity in the
same session had already consumed. It is not caused by the change being
verified — the one real `FAIL` any run surfaced was a legitimate,
change-specific finding (a missing routing-scope entry), completely
independent of whether that same run then survived to the end.

## Fix

No fix for the fan-out itself from inside this repo — the subprocess
fan-out is how [`verify_harness.py`](../tools/verify_harness.py)'s
stress-style checks are written, and narrowing it is harness work, not a
per-change fix. What worked, practically:

- **`PRECEDENT_CHECK_SKIP=name1,name2 python3` [`tools/verify_harness.py`](../tools/verify_harness.py)**
  (added 2026-09-18, alongside `PRECEDENT_CHECK_ONLY` for the inverse)
  replaces named `check_*` functions with a no-op before they run, so their
  fan-out never happens. Reproduced directly: two full runs died at exit
  137 in almost the same spot (117-118/172, right after
  `check_creation_pipeline_fires`); skipping the two checks already
  confirmed heaviest (`check_leak_gate_refuses_a_fresh_container`,
  `check_precedent_check_fires`) let the same tree sail past that exact
  point in under a minute. This does not fix the fan-out — it lets you
  avoid re-triggering an already-identified heavy check's fan-out while
  isolating or re-measuring the rest, which the `pkill`-and-retry approach
  below cannot do (a retry re-runs everything, fan-out included).
- Before a retry, kill any survivors: `pkill -9 -f
  precedent_session_practices.py` (and `-f verify_harness.py` if the prior
  attempt is still hanging around), then confirm with `free -h` and
  `pgrep -fc precedent_session_practices.py` before starting the next run.
- Treat one **complete** run (exit 0, or a `FAIL` list you've read and
  fixed) as sufficient evidence — do not keep re-running for reassurance
  once you have one clean pass plus the repo's faster checks
  ([`doc_lint.py`](../tools/doc_lint.py), [`leak_gate.py`](../tools/leak_gate.py),
  [`precedent_check.py`](../tools/precedent_check.py),
  [`doc_sync.py`](../tools/doc_sync.py)), all of which are far less
  memory-hungry and did not exhibit this at all.
- If every retry keeps dying before completion, `dmesg | tail` is the
  fastest way to confirm it is this trap and not a real regression: an
  `oom-kill` line naming the Bash tool's own memcg means keep going, not
  stop and debug the diff.

## Resolution (2026-09-18, Same Day, a Different Session)

**The Story above's diagnosis was wrong about the mechanism, even though
the symptom and the process count were both real.** It called the fan-out
"the neighborhood of `check_precedent_check_fires`... and the
session-bootstrap fixtures around it," read as many legitimate parallel
test cases piling up. Watching a live run's process tree
(`ps --forest`) instead of only counting processes after the fact showed
something different: a single **linear recursive chain**, each link an
identical
[`precedent_session_practices.py --repo <same path>`](../tools/precedent_session_practices.py)
invocation, 26+ levels deep and still growing when caught.

The actual bug: [`tools/precedent_resolve.py`](../tools/precedent_resolve.py)'s
`_self_heal_stale_render()` spawns
[`precedent_session_practices.py`](../tools/precedent_session_practices.py)
as a subprocess whenever the untracked `.precedent/SESSION_PRACTICES.md` is
missing or stale.
That subprocess itself calls `load_config()`, which reaches the same
function for the same `repo_root` — and the target file this function is
spawning the process TO WRITE does not exist yet at that moment, since the
write only happens once the child's own render completes. With no
reentrancy guard, the child decided it also needed to self-heal, spawned a
third copy of itself, and so on with no base case, until the cgroup ceiling
this Story describes was hit. `check_bootstrap_source_produces_resolvable_set`
and `check_leak_gate_refuses_a_fresh_container` both bootstrap a fresh
source with no rendered file yet, which is exactly the condition that
triggers it — matching this Story's "45 `PASS` lines in" and "117/172"
crash points, both immediately after a check that bootstraps a fresh
individual source.

**Fixed**: an environment-variable sentinel
(`PRECEDENT_SELF_HEAL_IN_PROGRESS`) set on the spawned subprocess's
environment, checked at the top of `_self_heal_stale_render()`, so a child
already inside a self-heal attempt never triggers another one for itself.
Verified directly: `check_leak_gate_refuses_a_fresh_container` dropped from
241.8s to 1.72s, `check_bootstrap_source_produces_resolvable_set` from an
OOM crash to 4.50s, and a full unmodified
[`verify_harness.py`](../tools/verify_harness.py) run completed in 149.9s
(215 passed, 0 failed) — the first clean completion this investigation
saw, after two runs died at exit 137 in the same spot.

**What stays true from the Story above, for whoever hits a resemblance
that isn't this exact bug**: the Bash tool's own memory cgroup can be
exhausted well before the host's own `free -h` shows any pressure, and
`dmesg`'s `oom-kill` line naming the Bash tool's memcg is still the fastest
way to confirm that shape of failure. What's retired is the specific
cause and the specific two checks — not the general "a cgroup can OOM
before the host does" lesson.
