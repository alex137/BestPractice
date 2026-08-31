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
| Resident budget, hard-capped | `RESIDENT_BUDGET_TOKENS = 2000` in tools/build_views.py; the build exits nonzero over budget | Built. Current resident block: ~621 tokens, 6 of 52 practices. |
| Premise measured, not assumed | [tools/behavioral_replay.py](../tools/behavioral_replay.py) | Built. See "What the replay measures" below — it is honest about what it can and cannot prove. |

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

## The premise, measured — v2

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
