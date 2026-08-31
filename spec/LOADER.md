<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-2 build session -->

# The Loader (Phase 2)

What [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "How an Agent
Knows Which Practices to Load" actually builds to, in this repo, and what
phase 2 did and did not build. Read the plan section first; this is the
implementation note, not a restatement.

## What exists

| Channel (plan's term) | Built as | Status |
|---|---|---|
| Resident block | The generated block in [AGENTS.md](../AGENTS.md), between `<!-- BEGIN GENERATED: precedent-loader -->` / `<!-- END GENERATED -->` | Built. Regenerate with `tools/build_views.py`; hand-editing fails `tools/verify_harness.py`. |
| Occasion index | Same generated block, grouped by `occasion` | Built, same mechanism. |
| Standing instruction | Same generated block, one sentence | Built. |
| Path-triggered | [tools/precedent_paths.py](../tools/precedent_paths.py) | Built as a command; not yet wired into a `PreToolUse` hook in [templates/harness/](../templates/harness/) — that is consumer-repo integration, phase 6 territory, not phase 2's done-when. |
| Gate-triggered | — | Not built. Depends on the runbook/gate-receipt machinery the plan describes under "Gate Receipts" and "Decisions" (phase 4). |
| Enforced (`checked_by`) | Already exists from phase 1 (a dozen practices carry it) | Unchanged by phase 2; phase 5 is "convert checkable practices to scripts." |
| "One code path" (`precedent show`) | [tools/precedent_show.py](../tools/precedent_show.py) (phase 1) | Unchanged; `precedent_paths.py` calls the same file reader (`split_practices._read_practice_file`), not a second extractor. |
| Generated views | [tools/build_views.py](../tools/build_views.py) → AGENTS.md's loader block, [MAP.md](../MAP.md), [GLOSSARY.md](../GLOSSARY.md) | Built. All three fail `tools/verify_harness.py` if hand-edited or stale. |
| Resident budget, hard-capped | `RESIDENT_BUDGET_TOKENS = 2000` in `tools/build_views.py`; the build exits nonzero over budget | Built. Current resident block: ~845 tokens, 7 of 52 practices. |
| Premise measured, not assumed | [tools/behavioral_replay.py](../tools/behavioral_replay.py) | Built. See "What the replay measures" below — it is honest about what it can and cannot prove. |

## The resident set, and why these seven

Phase 1 deliberately left every practice `tier: on-demand` — curating the
resident set is explicitly phase 2's job, once the budget mechanism exists to
enforce it (see [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md)). Seven
practices are resident now:

`repo-is-memory`, `orientation-map`, `quick-index`, `reply-links-files`,
`verify-postcondition`, `mistakes-become-rules`, `environment-gotchas`.

The test applied: **does this apply to every task in this repo, regardless
of what's touched or what kind of work it is** — not "is this important."
Practices scoped to a kind of work (formatting a document, merging a branch,
naming a file) are on-demand by design, reached through the occasion index
or `applies_to`, even when they matter a great deal — that scoping is the
whole point of the split. These seven are the ones nothing else stands in
for: orientation at session start, the two mechanical habits that apply to
literally any state-changing action or any reply that touches files, and the
meta-practice that turns a caught mistake into a stronger routing decision
rather than a one-off fix. `defines:` was also populated on seven practices
that already named a term to give GLOSSARY.md real, non-empty content to
generate from — a start, not a completed pass over all 52.

Adding an eighth resident practice means demoting one of these seven, or
retiring it — mechanically enforced by the token cap, not by discipline.

## What the replay measures, and what it deliberately does not

`tools/behavioral_replay.py` replays this repo's own commit history (142
commits after a bounded `git fetch --depth=500`, well past the phase-1
shallow clone) against `tools/precedent_paths.py` — the real path-triggered
channel, not a re-implementation of it — and cross-checks its output against
an independent `fnmatch` pass over the same data.

What it establishes: the mechanical channel has zero misses against its own
matching rule, across every replayed commit, and the resident-plus-triggered
loader costs roughly 83% fewer practices in context per commit than the old
always-everything arrangement, measured on this repo's own history rather
than asserted.

What it does not establish, and says so in its own output rather than
implying otherwise: 33 of 45 on-demand practices are reachable only through
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
