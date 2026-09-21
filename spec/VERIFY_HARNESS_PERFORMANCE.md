---
title:         verify_harness.py Performance — What Was Actually Found
kind:          record
status:        closed
opened:        2026-09-16
closed:        2026-09-19
superseded_by: null
supersedes:    []
audience:      session
summary:       "Why the deep-check suite ran ~250s, what actually made it slow, an audited thread-based parallelization that measured out to no real gain and was reverted, a change-scoping fix that measurably worked, and a 2026-09-19 follow-up: CI's own job-split confirmed working, a reverted fixture-reuse attempt, and a process-based (not thread-based) parallelization of check_precedent_check_fires that landed."
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

## 2026-09-19 follow-up: CI's own job-split, a reverted fixture-reuse attempt, and a process-based parallelization that landed

A later session picked this back up from a different angle: not "why is
this slow" again, but "does the fix already exist somewhere, and can the
2026-09-16 threading conclusion be improved on."

### CI's parallel job-split (PR #461) is confirmed working

Separately from this record, [PR #461](https://github.com/alex137/BestPractice/pull/461)
(2026-09-18) split `deep-check.yml` into three parallel GitHub Actions jobs:
`check_precedent_check_fires` alone, the rest of
[tools/verify_harness.py](../tools/verify_harness.py), and
[tools/precedent_check.py](../tools/precedent_check.py) +
[tools/doc_sync.py](../tools/doc_sync.py). That PR's own commit message said
timing on GitHub's runner was "not yet measured." It now is: the most recent
run at the time of writing (run `35439918795`) shows the three jobs
completing in 86s, 61s, and 5s **concurrently**, for a total workflow
wall-clock of ~99s — against the ~150s+ a sequential run of the same work
takes. This works cleanly because it uses separate GitHub-hosted VMs, each
with their own disk — the same class of contention this record's threading
attempt (above) and the fixture-reuse attempt (below) both ran into does
not apply between separate machines.

This does not speed up a session's own local
`python3 tools/verify_harness.py` run before a push (per
[two-check-levels](../practices/two-check-levels.md)) —
that still runs everything on one machine, sequentially. The two are
separate wins: CI gets its parallelism for free from the job-split; a local
run needed its own fix, below.

### Reverted: reusing one fixture directory instead of copying fresh per case

A different lever than threading: `check_precedent_check_fires` builds
~63 `case()` invocations, each copying the whole repository tree twice via
`shutil.copytree`. Copying is measurably the expense, not the subprocess —
a fresh copytree of this tree costs ~450ms; resetting an already-checked-out
copy with `git reset --hard && git clean -fdx` costs ~15-125ms when nothing
but files changed. Reusing one tree across all 63 slugs and resetting it
between them, instead of recopying, was implemented and tested.

**Two real correctness bugs surfaced by actually running it, not by
review:**

1. `git reset --hard`/`clean -fdx` only restores the working tree and
   index — it does not undo git-level state (new commits, `git remote add`,
   branches, rewritten history), which several `setup()` closures create.
   The second case to call `_setup_origin` failed outright: "remote origin
   already exists," left behind by the first. Fixed by snapshotting
   `for-each-ref`/`.git/config`/`.git/HEAD` right after the tree's one-time
   initial copy and comparing byte-for-byte before every reset; a mismatch
   triggers a full `.git` rebuild from the pristine copy instead of the
   cheap working-tree-only reset.
2. `_publish()` creates a bare repo at a path derived from the fixture
   directory's own name, to push to. Unique names (one fixture per slug)
   made this safe by accident; one shared name made the second publish
   collide with the first's leftover history — a non-fast-forward push
   rejection. Fixed with a general sweep, on every reset, of anything under
   the scratch directory that is not a fixture registered through `fresh()`
   (which records its own name as it runs) and is not the reused directory
   itself — rather than hand-naming this one pattern, since the same
   blind spot that missed it once could just as easily miss the next one.

Both fixes verified correct: the isolated check reported the same
**200 of 200 stated cases pass**, twice, after both fixes landed. But the
speed result was modest and noisy — 85.3s baseline vs. 68-77s after, roughly
10-20%, far short of what the per-cycle microbenchmark (450ms → 15-125ms)
implied, because a real fraction of the 63 cases do actual git surgery and
fall onto the expensive rebuild path rather than the cheap one. Given a
small, noisy win bought with three interacting safety mechanisms (pristine
detection, a full-`.git`-rebuild fallback, and a stray-artifact sweep) in
the one check whose entire job is catching silent false coverage, this was
reverted rather than kept. The revert was clean: `git diff` against `HEAD`
came back empty.

### What actually worked: real OS processes, not threads

This record's 2026-09-16 threading attempt (above) found "no real
difference... proved that was noise" from a rigorous controlled comparison.
Testing the same underlying question again on 2026-09-19 — with a plain
synthetic benchmark, before touching any code — found something sharper and,
this time, actively negative: 4 sequential `shutil.copytree` calls of this
tree took 0.53s total (0.13s each); the same 4 run concurrently via
`ThreadPoolExecutor` took 1.36s total, each individual copy slowing to
1.34s under contention. Threads made this container's filesystem work
*slower*, not merely no-faster. **Real OS processes are a different story
entirely, benchmarked directly**: 8 independent (copytree + subprocess)
pipelines run one after another took 2.36s; the same 8 launched as separate
`multiprocessing.Process` workers took 0.73s, with identical results — a
genuine ~3.2x. Neither `ProcessPoolExecutor` nor `multiprocessing.Pool` fit
here: their worker processes receive tasks by pickling them through a
queue, and `plant`/`setup` are local closures, which pickling can't cross.
Plain `multiprocessing.Process` sidesteps this — it forks directly from the
point in the code where the closure already exists in memory, so only the
(trivially picklable) `(rc, out)` result has to cross the process boundary,
never the closure itself.

**This resolves, without fully explaining, the open question this record
closed with in 2026-09-16** ("why threading didn't help in situ despite
working in an isolated benchmark"): the two sessions' synthetic
copytree-only benchmarks disagree (no measurable difference vs. actively
worse), which itself says this container's behavior for concurrent file
copies is not a fixed, stable property — it varies enough between
measurement sessions that a conclusion drawn from one running instance does
not reliably predict another. What holds across both sessions is the
conclusion that matters operationally: **whatever mechanism python threads
use for this specific workload in this container, it does not reliably
help, and real processes are the safer bet going forward.**

**Implemented: parallelizing only within each `case()` call.** Scoped
identically to the 2026-09-16 threading attempt — a case's own two
sub-runs (the planted fixture and the clean fixture) are independent of
each other and of everything else, and `case()` still blocks and returns
only once both are real `(rc, out)` tuples, so nothing about call sites,
ordering, or the ~8 slugs whose results are read again later by unrelated
code needed to change. The only added complexity beyond the executor swap
itself: a plant()/setup() that raises inside a child process would
otherwise kill that process silently and hang the parent waiting on a
result that never arrives, instead of failing the whole check loudly the
way an exception in the original sequential code does — so each worker
catches and forwards the exception through the queue, and the parent
re-raises it.

Verified correct: **200 of 200 stated cases pass**, checked across three
separate runs. Timing, honestly reported rather than cherry-picked: two
isolated runs came back at 59.6s and 78.7s (both below this record's own
documented 83-120s noise floor for this exact check); one run under the
full 171-check suite came back at 102.56s (above the 85.26s single-sample
baseline this session started from, though within the documented noise
band). Three samples against noise this wide is not the rigorous 3×3
alternating comparison this record's 2026-09-16 section used to establish
that floor — but two of three landing below it, on a change with the same
safety profile as the code it replaces (each process still does its own
fully independent copy; no shared state, no reuse, no new leak surface),
reads as a real if noisy improvement rather than as noise dressed up as one.

## Where this landed (2026-09-19)

The process-based `case()` parallelization shipped on
`claude/verify-harness-rotation-70zvhm`, merged into `precedent-beta-v01`
(PR link added once opened). The fixture-reuse attempt was implemented,
measured, and reverted entirely within the session — like the 2026-09-16
threading attempt, it never left the working tree as a commit.

## 2026-09-21: the rotation, which is the change that actually moved it

Morgan, 2026-09-21 (strength: decided), having read the 211.5s breakdown
above: *"If it is 3.5 minutes to check every enforced rule every time, maybe
we also add in a '10% each time' there as well?"*

He had already invented the mechanism. `precedent_check.py`'s
`_scoped_tree_slugs()`, from his own 2026-09-18 direction, runs three tiers
— directly touched, indirectly touched, and a deterministic rotating slice
keyed by commit count. This applies the same shape to the planted cases.

**What always runs, and every one of these is load-bearing:**

- a check whose own `practices/<slug>.md` the change touched — editing a
  rule without re-proving its check still fires is the hole this function
  exists to close;
- any case whose recorded output a later assertion reads back out of
  `planted[...]`. **Derived from this file's own source at run time**, not
  kept as a hand-list: a hand-list drifts the first time somebody adds a
  deeper assertion, and the failure surfaces months later as a `KeyError`
  in an unrelated case. Nine slugs, as of this change;
- **everything**, when the change touches the check machinery itself
  (`tools/precedent_check.py`, `tools/verify_harness.py`, or a
  `tools/checks/` script). A change there can alter any check's behaviour,
  so no slice is a safe sample of it;
- **everything**, in CI. `deep-check.yml` sets `PRECEDENT_HARNESS_ALL=1`.
  Rotation is right for a push a person is standing at and wrong for the
  run nobody is watching.

**Measured selection**, by calling the selector directly with a fixed
`touched` set and bucket rather than timing a suite and inferring:

| change | cases selected |
|---|---|
| a documentation-only edit | 16 of 71 |
| one practice file | 17 of 71 |
| `tools/precedent_check.py` | 71 of 71 |

At the ~1.5s per case this record already measured, that takes the function
from 107.9s to roughly 25s on an ordinary change, and the whole suite from
~211s to ~128s.

**The selection is printed in the result line**, never silently narrowed —
`71 of 71 planted cases ran -- all (…)`, or `16 of 71 … 55 NOT exercised
this run`. This repo's own rule about its check suite is that a skip is not
a pass; a scheduler that hid what it declined to run would break that in the
one place hardest to notice.

**One measured trap, recorded because it cost the first run.**
`check_precedent_check_fires` contains a local `import importlib.util`
partway down, which makes `importlib` a local name for the whole enclosing
scope. The selector's registry read, placed above it, raised
`UnboundLocalError` — and because the selector is written to run everything
when it cannot decide, the failure surfaced as a full 81s run reporting
`all (the registry could not be read)` rather than as a crash. Fixed with
`import importlib.util as _ilu`, which binds no `importlib` name at all.
**The fail-open design is what made this survivable and also what made it
quiet**: worth knowing that any future "why is it still slow" starts by
reading the reason string in the result line.

**Does it inherit the 2026-09-20 zero-coverage failure?** Morgan asked
directly, and the answer is measured rather than argued. That day
`precedent_check.py`'s rotation landed on a bucket where every slug it
picked was inapplicable to the repo, reported `0 passed`, and CI's
"refuse a run that checked nothing" backstop correctly refused it — on two
real pull requests in two different sets (`_run_with_coverage_retry`'s
docstring has the account).

The shape here is different in two ways that matter. **A planted case has
no SKIP path**: it plants a violation and requires a non-zero exit, so an
inapplicable check fails loudly rather than passing vacuously. And nine
slugs are pinned in every bucket, so the selection never approaches zero —
measured per bucket, with a documentation-only diff:

```
selected per bucket: [16, 16, 15, 15, 15, 15, 15, 15, 15, 15]
minimum 15 of 71 -> 33 stated cases (15 x 2, plus the unplanted baseline
and the two registry assertions, which always run)
```

**That floor is a property of today's pinned set, not a guarantee**, and it
would weaken the day nobody reads `planted[...]` back any more. So it is
handled twice rather than left to arithmetic that happens to hold: the
selector returns the FULL set if a slice ever comes back empty, and the
check asserts both the per-bucket floor and that fail-safe. Ten stated
cases now, not eight.

Ten stated cases in `check_planted_case_rotation_never_narrows_silently`,
which assert the two states that must never narrow, that a touched practice
runs its own case in every bucket, that every pinned slug is pinned in every
bucket, that ten consecutive commits cover the whole set, that an ordinary
change really does run well under half, that no bucket selects zero, and
that an empty slice runs everything.

## Open follow-ups

- **The cross-session copytree-under-threads discrepancy** (no measurable
  difference in 2026-09-16's rigorous study vs. actively worse in
  2026-09-19's synthetic benchmark) is itself unexplained — is this
  container's underlying disk/filesystem behavior genuinely variable
  between sessions, or was one of the two benchmarks measuring something
  subtly different? Whoever hits this territory again should treat threads
  as unproven-to-actively-risky by default rather than re-litigate it from
  a single new sample.
- **A rigorous 3×3-style alternating comparison for the process-based
  change**, matching the standard this record's 2026-09-16 section set,
  would firm up the 59.6s/78.7s/102.56s picture above into something as
  solid as the noise floor it's being compared against.
- **Cross-case parallelization (running many of the 63 cases concurrently,
  not just the two halves of one case)** was analyzed but not attempted:
  the function isn't structured as a flat list of independent work (`case()`
  calls interleave with ~30 bespoke fixture blocks across ~2000 lines), ~8
  slugs have their result read again later by unrelated code, and the
  closure-pickling issue above rules out the standard pool tools. Three
  sketched approaches, none built: **(a)** a bounded lookahead pipeline
  paired with a lazy-resolving `planted` dict that blocks-and-resolves
  wherever a value is first read, so no case has to be hand-classified as
  "safe to defer" — the general fix, most build effort; **(b)** refactor
  the ~75 `plant`/`setup` closures to module-level functions (passing
  `tmp`/`pristine`/`git` explicitly instead of capturing them) so the
  standard `ProcessPoolExecutor` applies directly — less novel machinery,
  but a large mechanical rewrite across every case with real transcription
  risk; **(c)** a scoped-down version of (a) that only special-cases the
  known ~8 downstream-read slugs — least effort, but reintroduces exactly
  the "silently wrong if a future case is added and nobody updates the
  list" risk the general version avoids. Potential upside, from the 8-process
  synthetic benchmark above: something closer to 3-4x than the ~30%(ish, noisy)
  this session's narrower change achieved.
- The three change-scoped checks' transitive-closure gap (above, from
  2026-09-16) is an accepted, documented tradeoff, not a task — revisit
  only if a real regression in one of `very_deep_check.py`'s helper modules
  is ever missed by it.
