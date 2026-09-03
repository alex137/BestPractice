<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-2 build session -->

# The Loader (Phase 2)

What [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "How an Agent
Knows Which Practices to Load" actually builds to, in this repo, and what
phase 2 did and did not build. Read the plan section first; this is the
implementation note, not a restatement.

## What exists

| Channel (plan's term) | Built as | Status |
|---|---|---|
| Resident block | The generated block in [AGENTS.md](../AGENTS.md), between `<!-- BEGIN GENERATED: precedent-loader -->` / `<!-- END GENERATED -->` | Built. Regenerate with [tools/build_views.py](../tools/build_views.py); hand-editing fails [tools/verify_harness.py](../tools/verify_harness.py). |
| Occasion index | Same generated block, grouped by `occasion` | Built, same mechanism. |
| Standing instruction | Same generated block, one sentence | Built. |
| Path-triggered | [tools/precedent_paths.py](../tools/precedent_paths.py) | Built as a command; not yet wired into a `PreToolUse` hook in [templates/harness/](../templates/harness/) — that is consumer-repo integration, phase 6 territory, not phase 2's done-when. Its glob matcher was rewritten after the first phase-2 pass shipped a broken one — see [Where this channel was silently broken](#where-this-channel-was-silently-broken-and-what-it-cost-the-numbers) below. |
| Gate-triggered | — | Not built. Depends on the runbook/gate-receipt machinery the plan describes under "Gate Receipts" and "Decisions" (phase 5). |
| Enforced (`checked_by`) | Already exists from phase 1 (8 of 52 practices carry one, naming 4 distinct scripts) | Unchanged by phase 2; phase 4 is "convert checkable practices to scripts." |
| "One code path" (`precedent show`) | [tools/precedent_show.py](../tools/precedent_show.py) (phase 1) | Unchanged; `precedent_paths.py` calls the same file reader (`split_practices._read_practice_file`), not a second extractor. |
| Generated views | [tools/build_views.py](../tools/build_views.py) → AGENTS.md's loader block, [MAP.md](../MAP.md), [GLOSSARY.md](../GLOSSARY.md) | Built. All three fail tools/verify_harness.py if hand-edited or stale. |
| Resident budget, hard-capped | `RESIDENT_BUDGET_TOKENS = 2000` in tools/build_views.py; the build exits nonzero over budget | Built. Current size is in [The catalogue as it stands](#the-catalogue-as-it-stands) below, generated. |
| Premise measured, not assumed | [tools/behavioral_replay.py](../tools/behavioral_replay.py) | Built. See "What the replay measures" below — it is honest about what it can and cannot prove. |

**Generated views are no longer this-repo-only (2026-09-03).** A team or
individual source repo (e.g. `precedent-team-maintainers`,
`precedent-individual`) vendors the same [tools/build_views.py](../tools/build_views.py)
and runs `python3 tools/build_views.py --agents-only` on its own
`practices/`, getting the identical resident-block/occasion-index/standing-
instruction treatment this repo's own `AGENTS.md` gets — `--agents-only`
skips `render_map_md()`/`render_glossary_md()`, which assume this repo's own
structure (`TOOLS_DESCRIPTIONS`, "this repo is BestPractice itself" prose)
and aren't meaningful for a practice-set repo with a different `tools/`
layout. **What this does NOT close**: each source repo still generates its
own view, single-source, exactly as this repo always has. The cross-source
case — one consuming repo (universal + team + individual + repo-local, all
resolved together into one generated `AGENTS.md`) — is still unbuilt; see
[spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s
"Known gap" section, which this change does not resolve.

## The catalogue as it stands

Generated — do not hand-edit, and do not restate these figures in the prose
around the block. This row used to be a sentence in the status table above,
and it said the resident block was "~621 tokens" for the whole of phase 3,
which had halved it. Every gate in the repository was green: no gate can see
a number in a sentence. That is `docs-track-models`, happening here.

<!--gen:catalogue-->
| | |
|---|---|
| Practices in the catalogue | 57 |
| Resident, loaded every session | 6 of 57 practices |
| Resident block size | ≈312 tokens of a 2000-token hard cap |
| `## Rule` share of the catalogue | 26% of the catalogue |
| Rules still over 150 words | 7 |
| Carrying a `## Detail` | 19 |
| Carrying a `## Story` | 24 |
| Enforced by a check | 26 of 57 practices carry a `checked_by` |
<!--/gen:catalogue-->

Numbers by: catalogue_stats.py

## The resident set, and why these six

Phase 1 deliberately left every practice `tier: on-demand` — curating the
resident set is explicitly phase 2's job, once the budget mechanism exists to
enforce it (see [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md)). Six
practices are resident now:

`repo-is-memory`, `orientation-map`, `quick-index`, `reply-links-files`,
`verify-postcondition`, `environment-gotchas`.

The test applied is narrower than "is this important": **does the moment
this practice fires arrive on essentially every task regardless of what's
touched, AND is that moment one a session can be expected to self-recognize
without being pointed at it.** Both halves matter. Practices scoped to a
kind of work (formatting a document, merging a branch, naming a file) fail
the first half and are on-demand by design, reached through the occasion
index or `applies_to`, even when they matter a great deal — that scoping is
the whole point of the split. `environment-gotchas` is the one entry that
looks, at a glance, like it should fail the first half too (`occasion:
"hitting an environment or tooling quirk"` is not literally every task) —
it earns residency on the second half instead: unlike "I am writing a
document" or "I am merging a branch," which a session recognizes as its own
current action, "this is an environment quirk, not a broken tool" is a
diagnosis a confused session is the *least* likely to reach for on its own —
that is the exact failure this practice's own `## Story` was written to
prevent, and the reason the occasion index (which requires recognizing the
occasion first) is the wrong channel for it.

**`mistakes-become-rules` was made resident in an earlier pass of this
curation and was demoted back to on-demand on review**, and it's worth
recording why, since the plan itself supplies the cautionary tale: it names
this exact practice (BestPractice's old practice 20, "the proportionality
guard") as evidence that **residency alone does not produce compliance** —
it was resident for all 46 rules during the weekend the review describes,
and did not fire. Keeping it resident here would have restaged that same
case study rather than acting on what it demonstrates. Its trigger ("a
review finds a defect") is also a moment a session self-recognizes cleanly,
unlike the environment-gotchas case above — a defect being caught is not
something a confused session might misdiagnose as something else — so it is
a good citizen of the occasion index instead, which it already has.

`defines:` was also populated on seven practices that already named a term
to give GLOSSARY.md real, non-empty content to generate from — a start, not
a completed pass over all 52.

Adding a seventh resident practice means demoting one of these six, or
retiring it — mechanically enforced by the token cap, not by discipline.

## What the replay measures, and what it deliberately does not

[tools/behavioral_replay.py](../tools/behavioral_replay.py) replays this
repo's own commit history (up to 142 commits after a bounded
`git fetch --depth=500`, well past the phase-1 shallow clone) against
[tools/precedent_paths.py](../tools/precedent_paths.py) — the real path-triggered channel, not a
re-implementation of it — and cross-checks its output against a separately
written segment-walk matcher.

**It degrades instead of crashing when there isn't enough history to
measure anything.** A fresh `git clone --depth 1` — this repo's own
documented default for a new session — has exactly one commit and no parent
to diff against; the first version of this script divided by that commit
count and crashed the whole harness with a traceback on exactly that
environment, found by actually cloning shallow and running it, not by
inspection. Below 20 replayable commits it now prints why, names the shallow
clone as the likely cause with the fetch command to fix it, and exits 0 with
a `REPLAY_STATUS: DEGRADED` marker line that tools/verify_harness.py
reports as not-yet-applicable rather than pass or fail — an environment
precondition, not a defect in the loader.

What a full replay establishes, stated carefully: the loader's own
implementation and a separately written one **agree on every replayed
commit**, and the resident-plus-triggered loader costs roughly 73% fewer
practices in context per commit than the old always-everything arrangement,
measured on this repo's own history rather than asserted (86 non-merge,
file-touching commits replayed as of this writing; re-run
[tools/behavioral_replay.py](../tools/behavioral_replay.py) for the current
figure, since it moves as this repo's own history grows — this is exactly
the kind of restated-computed-number practice 19/`docs-track-models` warns
against elsewhere, so treat the number here as illustrative, not a
citation).

**Agreement between two implementations is not a miss rate**, and this
document said otherwise until it was caught. What actually pins the
channel's semantics is the stated-case table in
[tools/verify_harness.py](../tools/verify_harness.py) (`check_glob_semantics`),
which asserts what `applies_to` is supposed to mean rather than that two
pieces of code do the same thing.

### Where this channel was silently broken, and what it cost — the numbers

Worth recording, because it is this design's named weak point happening in
its own repo rather than in the abstract.

The first phase-2 pass matched paths with a bare `fnmatch.fnmatch(path,
glob)`. `fnmatch` has no `**`: it expands every `*` to `.*`, so `**/*.md`
compiles to a pattern that **requires a literal `/`** and therefore never
matches a top-level file. Editing [AGENTS.md](../AGENTS.md),
[README.md](../README.md), [TODO.md](../TODO.md), [PRACTICES.md](../PRACTICES.md),
[MAP.md](../MAP.md) or [GLOSSARY.md](../GLOSSARY.md) surfaced **zero** of the
eight document practices scoped to `**/*.md`. The same file spelled
`./AGENTS.md` *did* match, so the answer depended on how the path was typed.

Nothing caught it, and that is the instructive part: the replay's
"independent" cross-check re-derived each commit's matches with **the same
`fnmatch` call the loader used**. It agreed with the bug on every commit and
reported "0 misses." A cross-check against a second copy of the same rule is
not a check.

Measured over this repo's history, the broken matcher silently dropped **520
(practice, commit) instances across 65 of 86 commits**. The corrected
figures, against the same history:

| | Before (broken) | After (fixed) |
|---|---|---|
| Commits with at least one path match | 39 of 86 (46%) | 81 of 86 (94%) |
| Total (practice, commit) matches | 148 | 676 |
| Practices in context per commit | 7.7 | 13.9 |
| Reduction vs. always-everything | 85% | **73%** |

So the headline saving is real but was **overstated by twelve points** — the
old number was cheaper precisely because the channel was failing to fire.

What it does not establish, and says so in its own output rather than
implying otherwise: 34 of 46 on-demand practices are reachable only through
the `occasion` index's prose, not a path glob, and whether a session actually
reads and acts on an occasion-index line for a given piece of work is not a
fact recoverable from a git diff. That gap is the plan's own named weak
point (see "The Deep Check Audits Routing, Not Content"), and remains one
after phase 2 — the periodic deep check, not this replay, is what the plan
assigns to catch it, and that check is not built yet (phase 5 territory).

## Re-run after the routing pass — v5, and it is a negative result

**The headline: more routing bought no recall.** A principled pass over all 46
on-demand practices, plus a fourth loading channel, moved the treatment arm's
miss count from 21 to 22 and cost 8% more context per case. That is not a
disappointing result to be explained away; it is the clearest thing this eval
has measured, and it settles where the remaining effort should go.

### What changed

- **A glob pass**, recorded with a reason per practice in
  [tools/routing_scope.json](../tools/routing_scope.json). Eight practices
  gained a narrower `applies_to`; 24 stay at `**` with the reason stated. Only
  three of the eight were in the v4 miss table — the rest were scoped on the
  merits, so the pass is not a fit to twenty commits.
- **The gate-triggered channel** ([tools/precedent_gate.py](../tools/precedent_gate.py)),
  and one line in the standing instruction naming it. **This eval cannot see
  gates at all** — they fire at moments a commit does not record — so no part
  of the result below is attributable to them, in either direction.

Oracle and control prompts are byte-identical to v4 and v3 for the third run
running, verified by regenerating them in a worktree and diffing all 60; those
40 answers are reused. All 20 treatment hop-1 prompts changed and 19 hop-2;
those 39 cells were re-run one isolated session each. v4's answers are in
`evals/routing/answers-v4-pre-routing-pass/`.

| | v4 | **v5** |
|---|---|---|
| Control — recall / miss | 84% / 16% | **84% / 16%** *(same answers)* |
| Treatment — recall / miss | 78% / 22% | **77% / 23%** |
| Treatment — precision | 79% | **77%** |
| Treatment — practice context | ≈4,296 tok/case | **≈4,642** |
| Recall per 1k tokens (control / treatment) | 9.5 / 18.1 | **9.5 / 16.6** |
| Head to head (control-only / treatment-only) | 10 / 4 | **13 / 6** |
| Total misses by the treatment arm | 21 | **22** |

### The prediction, and how it held

The run was made against a prediction written and committed before the globs
were applied ([evals/routing/PREDICTION.md](../evals/routing/PREDICTION.md)),
because this is the third change to the loader's inputs in one phase and
re-running a measurement until it moves is how a number stops meaning
anything.

| # | Predicted | Outcome |
|---|---|---|
| 1 | the named practices become surfaced | **Partly.** `session-bootstrap` and `engine-plus-host-shims` are surfaced; `scripts-assert-properties` was withdrawn before the run because a glob would have contradicted its own scope gate. |
| 2 | the aggregate moves 0–8 points and will not be claimed | **Held.** It moved −1. |
| 3 | precision falls, cost rises | **Held**, and inside the stated limits: 79% → 77%, +8% context (the failure line was 70% and +25%). |
| 4 | the in-context misses do not move | **Held.** `verify-postcondition` is 0 of 3 for the third run. |
| 5 | the gate channel is invisible here | **Held** by construction. |

Prediction 2 was the one worth writing down, and it is the one that came true.

### What did move, and it is the finding

Total misses did not change. **What the session had in front of it when it
missed did.**

| the miss was on a practice that was… | v4 | **v5** |
|---|---|---|
| resident, or surfaced by the path channel, or opened and declined | 8 | **11** |
| reachable only as a one-line index clause | 13 | **11** |

**The glob pass converted reach failures into judgment failures.** That is
exactly what a correct glob is supposed to do, and it is why the eight stay
even though recall did not move: a practice whose scope statement is right is
right, and twenty commits from one repository cannot settle otherwise. What
the pass demonstrates is that **reach was never the binding constraint.**
Practices the session had never been shown and practices it had been shown
were missed at about the same rate; moving practices from the first group to
the second changed which ones were missed, not how many.

`session-bootstrap` went 1 → 0 and `engine-plus-host-shims` 3 → 2. Against
that, `repo-is-memory`, `quick-index`, `volatile-rules-carry-dates`,
`convention-to-audit` and `docs-track-models` each picked up a miss they did
not have in v4 — ±1 per practice in both directions, which is what one run per
cell looks like. Nobody should read a story into any single row.

### What this settles for the design

Three runs have now asked whether better routing produces better compliance,
and the answer has been the same each time in a different form:

- **v3** — residency does not produce compliance. `verify-postcondition` was
  resident and found zero times out of three.
- **v4** — a corrected glob surfaced `practice-export-loop` on every case it
  applied to, and every remaining miss was a case where the session had been
  shown it and declined.
- **v5** — a pass over the whole catalogue reduced the practices a session was
  never shown, and the total did not move.

**The routing layer is close to done, and it is not where the remaining loss
is.** Eleven of the 22 misses are on practices already in front of the
session; fifteen of the 22 are on practices that now carry a check. What is
left after that is seven misses on five prose-only practices, and
[spec/ENFORCEMENT.md](ENFORCEMENT.md) says why each of them resisted a check.

### What no channel reaches, stated so nobody counts on it

`python3 tools/routing_eval.py --enforcement` attributes every remaining miss.
The residue after routing and enforcement is small and specific:

- **`mistakes-become-rules`** (×3) — the largest, reachable now through the
  `review` gate but not through any path, and deliberately unchecked: a check
  must carry the proportionality guard that decides whether the practice fires
  at all, and a check that mints a rule for every defect fix is the failure
  the plan opens by diagnosing.
- **`registry-source-of-truth`** (×1) — no path, no moment, no check. A
  registry is recognised by what it is *for*, and this repo's are `.json`,
  `.py` and `.md` alike. It is the one practice in the catalogue that every
  channel misses by construction, and it is recorded that way in
  [tools/routing_scope.json](../tools/routing_scope.json) rather than left
  looking like an oversight.
- **`convention-to-audit`, `volatile-rules-carry-dates`, `repo-is-memory`**
  (×1 each) — single misses in one run, on practices that were found in every
  other case. Not a pattern.

## Re-run after enforcement landed — v4 *(superseded by v5 above; kept as the pre-routing-pass baseline)*

**Read this before quoting any number below it.** Phase 4 changed one input
and one input only: the **path-triggered channel**. `practice-export-loop`'s
`applies_to` was corrected (it named where an export lands, not where the work
that triggers it happens), and a defect in the harness was fixed —
`changed_files` used `git diff-tree` without `--root`, so case c16, this
repo's initial commit, handed the treatment arm "(no files)" and zero
path-channel practices for a change touching 48 of them. That bias was present
in v1, v2 and v3.

**Every oracle and control prompt is byte-identical to v3**, verified by
regenerating v3's prompts from `ef4e9cc` in a worktree and diffing all 60.
Sixteen treatment hop-1 prompts changed, and therefore sixteen hop-2 prompts.
Those 32 cells were re-run, one isolated session each; the other 48 answers are
v3's, reused because their input did not change. v3's answers are preserved in
`evals/routing/answers-v3-pre-enforcement/`.

| | v3 | **v4** |
|---|---|---|
| Control — recall / miss | 84% / 16% | **84% / 16%** *(same answers)* |
| Treatment — recall / miss | 69% / 31% | **78% / 22%** |
| Treatment — precision | 81% | **79%** |
| Control — practice context | ≈8,905 tok/case | ≈8,898 |
| Treatment — practice context | ≈4,200 tok/case | **≈4,296** |
| Recall per 1k tokens (control / treatment) | 9.5 / 16.5 | **9.5 / 18.1** |
| Head to head (control-only / treatment-only) | 15 / 1 | **10 / 4** |
| Total misses by the treatment arm | 29 | **21** |

*(The control's context figure moved by 7 tokens against a byte-identical
prompt set: v3's committed `cost.json` was written from a slightly earlier
tree state than the prompts it finally used. Regenerating v3's prompts today
gives 8,898. Noted rather than smoothed, because a published figure that no
longer regenerates is the thing this repo's own `docs-track-models` is about.)*

### What is measured, and what is one run of variance

**The aggregate recall gain is not measured.** Treatment 69% → 78% is 9
points, and this eval's stated resolution is that a difference under roughly 15
points is not measured. One run per cell. Nobody should quote "the loader got
better" from this.

**One practice-level effect is measured, and has a mechanism.**

| practice | v3 treatment | v4 treatment |
|---|---|---|
| `practice-export-loop` | 2 caught / 8 missed | **6 caught / 4 missed** |

Its glob was corrected from `process/upstream/**` — where an export *lands* —
to the paths where this repo's generic practices are actually written. It went
from being surfaced by the path channel on **none** of the ten cases where it
applied to being surfaced on all of them. The misses halved.

**The rest of the movement is ±1 per practice and looks exactly like one-run
variance**: `cite-the-incident` 1 → 0, `docs-track-models` 2 → 0,
`environment-gotchas` 2 → 1, `parallel-artifact-ledger` 1 → 0,
`mistakes-become-rules` 5 → 4, against `registry-source-of-truth` 1 → 2 and
`merge-runbook` 0 → 1. Read it as churn, not as effect.

**The oracle-independent number moved more than the recall did.** Head to head
went from 15/1 to 10/4 — the treatment arm now finds four applicable practices
the control misses, against one before. That statistic does not use the oracle
at all, which is this eval's one soft spot, so it is worth more than its size
suggests. It is still one run.

**Precision fell slightly, as predicted.** Widening a glob surfaces a practice
on cases where it does not apply: `practice-export-loop` is now surfaced on 16
of 20 cases and applies in 10. 81% → 79%, and ≈96 more tokens per case. That is
the price of the reach fix and it is a small one.

### The finding that matters more than the numbers

**Reach and enforcement are two problems, and the four remaining
`practice-export-loop` misses prove it from the other side.** In v3 the loader
missed it eight times and had never been shown it. In v4 it is surfaced by the
path channel in **every one of the four cases where it is still missed** — the
session reads the Rule and declines it. Fixing the trigger fixed the trigger.
What is left is judgment, and no glob reaches it.

`verify-postcondition` (0 of 3) and `engine-plus-host-shims` (0 of 3) did not
move at all, and neither had its input changed. For `verify-postcondition` that
is now four consecutive runs in which residency has not produced routing at any
Rule length — which is the argument that carried it into
[spec/ENFORCEMENT.md](ENFORCEMENT.md) rather than into another curation pass.

### Where the misses that remain are covered

`python3 tools/routing_eval.py --enforcement` attributes the 21 remaining
misses to what now covers them: 14 are on practices that carry a check, 7 are
prose-only (`mistakes-become-rules` ×4, `registry-source-of-truth` ×2,
`merge-runbook` ×1). [spec/ENFORCEMENT.md](ENFORCEMENT.md) says why those three
were left unenforced, and states the limit on the coverage claim: a check being
in scope means a violation would be caught, not that these commits violated
anything or that a session complied.

## Re-baselined after the Rule/Detail split — v3 *(superseded by v4 above; kept as the pre-enforcement baseline)*

**Read this before quoting any number below it.** The v2 figures in the next
section were measured against a catalogue whose `## Rule` sections were 40% of
the corpus. Phase 3's Rule/Detail split changed that to 28%, which changed
**every arm's input**: the control loads all 52 Rules and the treatment's
resident block halved. The v2 table describes a catalogue that no longer
exists, and is kept below as the historical record, not as current state.

Same harness, same 20 cases, same method. Answers in
[evals/routing/answers/](../evals/routing/answers); v2's are preserved in
`evals/routing/answers-v2-pre-detail-split/`.

| | v2 (Rule at 40%) | **v3 (Rule at 28%)** |
|---|---|---|
| Control — recall / miss | 81% / 19% | **84% / 16%** |
| Treatment — recall / miss | 62% / 38% | **69% / 31%** |
| Control — practice context | ≈11,834 tok/case | **≈8,905** |
| Treatment — practice context | ≈4,509 tok/case | **≈4,200** |
| Control — recall per 1k tokens | 6.8 | **9.5** |
| Treatment — recall per 1k tokens | 13.7 | **16.5** |
| Treatment precision | 66% | **81%** |
| Head to head (control-only / treatment-only) | 15 / 3 | **15 / 1** |

### What moved, and what only appears to have moved

**The cost drop is real and is not a measurement.** It is computed from the
prompts, not from anything a model produced: the control now carries **25%
less** practice context per case because the Rules it loads are shorter. That
number would come out the same on any re-run.

**The recall changes are inside the noise.** Control 81% → 84% and treatment
62% → 69% are 3 and 7 points, on 20 cases, one run per cell. This eval's own
stated resolution is that a difference under roughly 15 points is *not
measured*. So the honest reading is: **shortening the Rules did not cost
either arm any recall, and may have gained a little.** It did not measurably
improve routing, and nobody should claim it did.

**The gap narrowed from 19 points to 15 — to exactly the resolution limit.**
The direction is unchanged and has now held across three runs: triggering
misses more than residency. The magnitude is no longer something this case
set can resolve.

**What actually improved is the loader's precision**, 66% → 81%, now *better*
than the control's 71%. Phase 2's diagnosis was that the index over-fires
because grouping by occasion invites a session to take a whole group; with
shorter Rules the second hop appears to discriminate better. Also inside the
noise, but it is the one movement with a mechanism behind it.

### The resident-practice finding inverted, and it is the flagged risk landing

Phase 2's sharpest result was that **both arms miss the same practices** —
`verify-postcondition` was applicable twice and found by neither arm. That is
no longer what the data says:

| practice | v2 control | v2 treatment | **v3 control** | **v3 treatment** |
|---|---|---|---|---|
| `verify-postcondition` (resident) | 0 of 2 | 0 of 2 | **3 of 3** | **0 of 3** |
| `environment-gotchas` (resident) | 1 of 2 | 0 of 2 | **2 of 2** | **0 of 2** |

Both are resident. Both now have short Rules. The control — which sees the
same shortened Rule — finds them every time; the loader finds them never.

**This is the risk phase 3 flagged when it made the split**, and it has landed
on the practice it was flagged for. `verify-postcondition`'s two concrete
traps moved to `## Detail`, and the arm that reads only the resident Rule
stopped surfacing it while the arm reading the whole catalogue started. Three
cases cannot resolve why — a shorter resident block may simply be less
salient beside a larger surfaced set, or it may be variance on n=3. What can
be said is that the earlier "both arms miss it equally" no longer holds, and
that the difference is now on the loader's side.

**It does not, on its own, argue for reverting the split.** The reverse
prediction — that a fuller resident Rule would have caught these — is exactly
what v2 measured and refuted: with the long Rule resident, the treatment arm
found `verify-postcondition` **zero times out of two**. Nothing in either run
shows residency working for this practice at any Rule length. What both runs
agree on is that it needs a check, which is what phase 4 is for.

### The queue phase 4 should actually work from

The plan's phase-4 queue was derived from v2's miss table. Re-derived from
v3, on the same cases:

| missed | caught | practice | reachable via |
|---|---|---|---|
| 8 | 2 | `practice-export-loop` | glob `process/upstream/**` **+ `checked_by`** |
| 5 | 7 | `mistakes-become-rules` | occasion prose only |
| 3 | 0 | `verify-postcondition` | **resident** |
| 3 | 0 | `engine-plus-host-shims` | occasion prose only |
| 2 | 0 | `environment-gotchas` | **resident** |
| 2 | 0 | `docs-track-models` | glob `**/*.md` **+ `checked_by`** |

Three changes from the v2 queue worth carrying into phase 4:

- **`practice-export-loop` is now the largest single miss** and was not on the
  old queue at all. It already has both a narrow glob and a `checked_by`, and
  the loader still missed 8 of 10 — its glob only fires on files under
  `process/upstream/`, and these cases touch other paths. **A practice can
  carry a check and still not be routed**, which is a distinction the phase-4
  framing ("every most-missed practice carries `checked_by: null`") no longer
  captures.
- **`cite-the-incident` and `convention-to-audit` have left the queue.**
  `cite-the-incident` went from 3 missed to 1 (of 15 applicable);
  `convention-to-audit` from 2 missed to 0 of 7. Both were on the plan's
  phase-4 starting list.
- **`capture-gate` did not come up at all** — the oracle judged it applicable
  in zero of the 20 cases this time, against two in v2. It stays a candidate
  on the strength of the earlier run, not this one.

### Why this run happened at all, given the plan says not to

[What Phase 2 Measured](../PRACTICE_ENGINE_PLAN.md#what-phase-2-measured) says
plainly: *"Do not re-run the eval before enforcement lands."* That instruction
was written when the loader's inputs were fixed, and its reason was that a
third run would only refine a direction already measured twice.

Phase 3 then changed both arms' inputs. Re-running **after** phase 4 against
the v2 table would have confounded enforcement with the Rule/Detail split, and
the pre-phase-4 baseline is recoverable only before phase 4 lands. So this run
is a **re-baselining, not a re-measurement of the direction** — and it did not
touch the occasion index, which is the tuning the same passage forbids. The
direction it reports is the same one, for the third time.

## The premise, measured — v2 *(superseded by v3 above; kept as the record of what was measured against the pre-split catalogue)*

[tools/routing_eval.py](../tools/routing_eval.py) is the test the replay
cannot do: whether a session shown the loader routes as well as one carrying
all 52 practices. Twenty real commits from this repo's history, an **oracle**
(all 52 Rules, asked only to classify, one case at a time: the answer key), a
**control** (all 52 Rules, asked to do the work: the pre-migration
arrangement), and a **treatment** (the real loader — resident block, occasion
index, *and* the path-triggered channel — in two hops: name what you want,
then decide having read exactly that).

| | recall | **miss rate** | practice context | recall per 1k tokens |
|---|---|---|---|---|
| Control — all 52 always loaded | 81% | **19%** | ≈11,834 tok/case | 6.8 |
| Treatment — the loader | 62% | **38%** | ≈4,509 tok/case | **13.7** |

Head to head, without the oracle: the control found **15** applicable
practices the treatment missed; the treatment found **3** the control missed.

**v1 was wrong about the size of the gap, and this document said so at the
time.** It gave the treatment arm two of the loader's three channels and
stopped it after one hop, scoring it at a 52% miss rate. Restoring the
path-triggered channel and the second hop moved it to 38%. The gap to
control narrowed only slightly (20 points to 19), because the wider case set
lifted the control too.

### What this actually says

**Triggering still misses more than residency does.** On the plan's own
terms — *"if triggering does not beat residency, the plan needs rethinking"* —
that has now been measured twice and come back the same way both times.

**And residency does not reach the goal either.** The control carries the
entire catalogue in every session and still misses 19% of what applies.
`verify-postcondition` was judged applicable twice and named by the control
**zero** times — while resident, in full, in its context. So the honest
summary is not "residency works, triggering does not." It is that **neither
arrangement gets close to few-or-no misses**, and one of them costs 2.6× the
context to be 19 points better.

That reframes the phase-2 question. The plan's premise was that trigger-based
loading would recover residency's compliance at a fraction of the cost. What
the measurement supports is weaker and more useful: **the loader buys 62%
less context for 19 points of recall — twice the recall per token — and
neither arrangement is good enough on its own.**

### Where the misses actually are

Counting which practices the treatment arm missed, across all 20 cases:

| missed | caught | practice | reachable via |
|---|---|---|---|
| 3 | 10 | `cite-the-incident` | occasion prose only |
| 2 | 0 | `capture-gate` | occasion prose only |
| 2 | 0 | `verify-postcondition` | **resident** |
| 2 | 0 | `environment-gotchas` | **resident** |
| 2 | 0 | `engine-plus-host-shims` | occasion prose only |
| 2 | 5 | `convention-to-audit` | occasion prose only |
| 2 | 9 | `mistakes-become-rules` | occasion prose only |

Two patterns, and they call for different fixes.

**The prose-only practices are a routing problem.** Everything missed twice
or more, apart from the two resident ones, is reachable only through the
occasion index — no glob, no check. These are practices about the *shape of
the work* ("a mistake was caught", "this is a check-in", "I am about to
merge"), which no file path can detect and which a session does not reliably
recognise about itself. This is the plan's own named weak point, now with a
number on it.

**The resident misses are not a routing problem at all**, and this is the
sharper finding. `verify-postcondition`, `environment-gotchas`,
`capture-gate` and `engine-plus-host-shims` were each judged applicable
twice; the control — holding all 52 — found them 0, 1, 1 and 1 times. **Both
arms miss the same practices.** Putting a practice in front of a session, in
full, at all times, does not make the session apply it. No change to the
loading channels can fix that; it is what `checked_by` and the phase-5 deep
check exist for.

**Read plainly:** phase 2 proves the plumbing is correct and cheaper than
residency, on this repo's own history. It does not prove — and the plan
never claimed phase 2 alone would prove — that occasion-based prose routing
achieves the compliance residency failed to. That is a live, open question
the deep check exists to keep answering, not one phase 2 closes.
