---
title:         verify_harness.py Performance — What Was Actually Found
kind:          record
status:        closed
opened:        2026-09-16
closed:        2026-09-16
superseded_by: null
supersedes:    []
audience:      session
summary:       "Why the deep-check suite ran ~250s, what actually made it slow, an audited parallelization that measured out to no real gain and was reverted, and a change-scoping fix that measurably worked."
---
# verify_harness.py Performance — What Was Actually Found

**The question that started this**: why does `tools/verify_harness.py` — the
deep check that gates a push, per [practices/two-check-levels.md](../practices/two-check-levels.md)
— take "up to ~10 minutes" for a single push. Written the way
[spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md) is written: what was actually
measured, not what seemed plausible.

## Measure first, not guess

The suite printed nothing between its first and last line, so "~10 minutes"
was an estimate, not a measurement. Per-check timing instrumentation was
added first — every `check_*` function wrapped to log individually slow
checks (≥2s) and a periodic done/elapsed/estimated-remaining line, plus a
slowest-checks summary at the end — **because that instrumentation doubled as
the profiler**: it needed no separate `cProfile` pass, and it's the thing a
future session reads instead of re-measuring from scratch.

**The real number, measured**: a full run took **250.7s**, not ~10 minutes.
**The real shape surprised us**: cost was not spread evenly across the
~270 `check_*` functions. Four functions accounted for 160 of the 250
seconds:

| Check | Time | % of total |
|---|---|---|
| `check_precedent_check_fires` | 90.2s | 36% |
| `check_very_deep_check_convergent_drift` | 32.1s | 13% |
| `check_very_deep_check_bootstrap_drift` | 22.1s | 9% |
| `check_shallow_clone_never_fabricates_unlanded_work` | 15.8s | 6% |

The other ~160 checks totaled ~90s combined (average ~0.56s each). An
earlier guess, made before this measurement, was that the ~29 scattered
`git clone`-based checks and their fixture overhead were the lever worth
pulling. They were not: they're cheap. The lesson **this session's own
practice, [slow-steps-report-and-cache](../practices/slow-steps-report-and-cache.md), states
directly**: "profile before declaring the remainder the next lever."

## The full audit of `check_precedent_check_fires` (90s, the single largest cost)

This function is 2,091 lines. It builds ~60 `case()` invocations (~193
stated assertions total), and each `case()` copies the entire repository
tree (`shutil.copytree`) twice and launches `tools/precedent_check.py` as a
subprocess twice — once against a planted violation, once against a clean
copy. That's the real cost: ~120 full-repo copies plus ~120 fresh Python
interpreter starts, sequentially.

**Naive parallelization (running all 60 cases concurrently) is unsafe.** The
audit found a real cross-case data dependency before touching any code:
`planted[slug]` — the `(rc, out)` result of one `case()` call — is read
**by slug, not position**, by unrelated code elsewhere in the same function
for roughly 8 producer slugs (`generated-edit-goes-upstream`,
`practice-links-travel`, `github-api-budget`, `session-load-budget`,
`access-probe-is-wired`, `declared-hooks-exist`,
`hooks-on-disk-are-reachable`, plus their automatic `-clean` pairs). The
function's own closing block also unpacks **every** entry in `planted` as
`(rc, out)`. Running all 60 concurrently without accounting for this would
either race a producer against its reader or need every one of ~190
assertion sites converted to a deferred/lazy read — a large, error-prone
rewrite of the exact test suite whose job is catching silent regressions.

**The audited, safe version: parallelize only within each `case()` call.**
A `case()` call's own two sub-runs (the planted fixture and the clean
fixture) are provably independent of each other and of everything else —
different directories, no shared state, `case()` still blocks and still
returns only after both are real `(rc, out)` tuples. This was implemented
with a small `ThreadPoolExecutor(max_workers=2)` local to the function.
Correctness held: 0 failures, same 193 stated cases, across every test run.

**It did not produce a real speedup, and was reverted.** A synthetic
2-copy microbenchmark of the same `shutil.copytree` operation showed a
genuine ~40% improvement from threading (1.68s sequential → 1.01s
concurrent) — so threading demonstrably works in this container. But that
gain did not survive inside the real function: isolated timed runs came
back at 89.2s (concurrent) vs. the 90.15s baseline — no real difference.
A single stash-based A/B comparison later showed 91.3s vs. 120.3s, which
looked like a win, but a rigorous **controlled 3×3 alternating comparison**
(sequential: 108.4s, 117.7s, 113.9s, mean ≈113.4s; concurrent: 114.0s,
110.3s, 114.7s, mean ≈113.0s) proved that was noise: this container's
run-to-run variance for this specific workload spans roughly 83–120s even
for byte-identical code. **Open question for whoever picks this up next**:
why the isolated 2-copy benchmark's ~40% gain didn't materialize in situ.
The leading unconfirmed hypothesis is that each case's real cost is
dominated by the several small `git` subprocess calls inside its
`plant()`/`setup()` closures (add, commit, config, branch) rather than by
the one big copytree-plus-subprocess pair that was parallelized — each
paying fixed process-spawn overhead that doesn't overlap the way two large
operations do. Confirming that needs the same rigor applied one level
deeper (instrument, isolate, A/B with repeats), not another guess.

Given no measured benefit and real added complexity (an executor
lifecycle, `cancel_futures` handling on the exception path), the change
was reverted rather than kept as unproven complexity.

## The change that did work: change-scoping the three `very_deep_check` tests

`check_very_deep_check_bootstrap_drift`, `check_very_deep_check_convergent_drift`,
and `check_shallow_clone_never_fabricates_unlanded_work` together cost
~70s. All three exist to test **`tools/very_deep_check.py`'s own drift and
unlanded-work-scanning logic** — not this repo's practice content — and
that logic changes rarely relative to how often this deep-check suite runs
on every push.

This repo already had the right pattern for exactly this shape of problem:
`check_machine_readable_files_parse`'s own docstring states it outright —
*"Changed-scope on purpose. This gates a push and runs constantly, so its
question is 'did I just break something', not 'is the whole repo well'.
The whole-tree sweep is the very deep check's job
(`tools/very_deep_check.py`), which is on-demand."* That check already uses
a shared helper, `parse_check.changed(ROOT)`, which never silently
narrows: with no base branch to diff against it falls back to the whole
tracked tree and says so.

A new shared helper, `_changed_touches(*rel_paths)`, reuses that same
`parse_check.changed()` call. Each of the three checks now calls
`not_applicable(...)` and returns immediately unless the push actually
touched `tools/very_deep_check.py` (and, for the two drift checks,
`tools/precedent_bootstrap_source.py` too — the generator whose output
they diff against). Verified both directions directly: ~14ms to skip when
untouched, and the full original fixture (same result as before) when
`tools/very_deep_check.py` is deliberately touched.

**The accepted gap, documented in `_changed_touches()`'s own docstring**:
this is scoped to the DIRECT file(s) named at each call site, not those
files' full transitive import closure. A change to one of
`very_deep_check.py`'s helper modules (it imports `precedent_resolve`,
`parse_check`, `precedent_bootstrap_source`, `split_practices`,
`build_views`, `leak_gate`, `precedent_time`, `precedent_access_check`)
that altered its behavior without touching `very_deep_check.py` or the
named file itself would not be caught by this scoped check at push time —
only by a later on-demand very deep check run. Enumerating a full
transitive closure by hand was deliberately not attempted: it goes stale
the moment those imports change, and a check that silently narrows itself
is worse than one that says plainly what it does not cover.

This one **did** measure out: a full suite run afterward came back
**208 passed, 0 failed, 4 not yet applicable, 192.9s total** — down from
the 250.7s baseline, and the ~60s difference lines up with the ~70s these
three checks used to cost.

## A real environmental incident hit along the way: gotcha g22, a third instance

Mid-session, this checkout's active branch silently switched from the
session's actual working branch back to `precedent-beta-v01` between one
tool call and the next — confirmed via `git reflog show HEAD`, which
showed `checkout: moving from claude/elegant-pascal-8cb3n2 to
precedent-beta-v01` with no command in this session's own history that
asked for it. This matches [record/GOTCHAS.md#g22](../record/GOTCHAS.md#g22)
exactly, and is now recorded there as a third instance: unlike the two
prior recorded cases, this time **uncommitted working-tree edits rode
along across the switch** rather than a commit being stranded or the
branch already being safely pushed. Recovery: `git diff` saved to a patch
file before touching anything else, a clean switch back to the correct
branch, and the patch reapplied (`git apply --reject`; one hunk conflicted
with code the correct branch already had and needed a manual reinsertion).
Nothing was lost, but it cost real time to diagnose and would have cost
much more without noticing before committing.

## Where this landed

Both real changes (instrumentation, then change-scoping) shipped as two
commits on `claude/elegant-pascal-8cb3n2`, merged via
[PR #427](https://github.com/alex137/BestPractice/pull/427) into
`precedent-beta-v01` at `63ab59a5`. The parallelization attempt was
implemented, measured, and reverted entirely within the session — it never
left the working tree.

## Open follow-ups

- **Why threading didn't help `check_precedent_check_fires` in situ**,
  despite working in an isolated benchmark — the many-small-git-subprocess-calls
  hypothesis above, unconfirmed.
- The three change-scoped checks' transitive-closure gap (above) is an
  accepted, documented tradeoff, not a task — revisit only if a real
  regression in one of `very_deep_check.py`'s helper modules is ever missed
  by it.
