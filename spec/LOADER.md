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
| Path-triggered | [tools/precedent_paths.py](../tools/precedent_paths.py) | Built as a command; not yet wired into a `PreToolUse` hook in [templates/harness/](../templates/harness/) — that is consumer-repo integration, phase 6 territory, not phase 2's done-when. |
| Gate-triggered | — | Not built. Depends on the runbook/gate-receipt machinery the plan describes under "Gate Receipts" and "Decisions" (phase 4). |
| Enforced (`checked_by`) | Already exists from phase 1 (a dozen practices carry it) | Unchanged by phase 2; phase 5 is "convert checkable practices to scripts." |
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
tools/precedent_paths.py — the real path-triggered channel, not a
re-implementation of it — and cross-checks its output against an independent
`fnmatch` pass over the same data.

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

What a full replay establishes: the mechanical channel has zero misses
against its own matching rule, across every replayed commit, and the
resident-plus-triggered loader costs roughly 85% fewer practices in context
per commit than the old always-everything arrangement, measured on this
repo's own history rather than asserted (84 non-merge, file-touching commits
replayed as of this writing; re-run tools/behavioral_replay.py for the
current figure, since it moves as this repo's own history grows — this is
exactly the kind of restated-computed-number practice 19/`docs-track-models`
warns against elsewhere, so treat the number here as illustrative, not a
citation).

What it does not establish, and says so in its own output rather than
implying otherwise: 34 of 46 on-demand practices are reachable only through
the `occasion` index's prose, not a path glob, and whether a session actually
reads and acts on an occasion-index line for a given piece of work is not a
fact recoverable from a git diff. That gap is the plan's own named weak
point (see "The Deep Check Audits Routing, Not Content"), and remains one
after phase 2 — the periodic deep check, not this replay, is what the plan
assigns to catch it, and that check is not built yet (phase 4 territory).

**Read plainly:** phase 2 proves the plumbing is correct and cheaper than
residency, on this repo's own history. It does not prove — and the plan
never claimed phase 2 alone would prove — that occasion-based prose routing
achieves the compliance residency failed to. That is a live, open question
the deep check exists to keep answering, not one phase 2 closes.
