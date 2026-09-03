# Decisions

One file per decision, `decisions/<date>-<slug>.md`, append-only, never
pruned. This is [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
["Where Decisions and History Live"](../PRACTICE_ENGINE_PLAN.md#where-decisions-and-history-live)
table's second row, made real: **a decision that is not about a practice**
("the sync merges unattended", "we chose X over Y") — as opposed to a
practice's own originating incident, which lives in that practice's
`## Story`, or work that is still open, which lives in
[TODO.md](../TODO.md).

**Never loaded into context.** A decision record is read when someone asks
"why did we do it this way," not carried by every session the way a
resident practice is. That is the whole point of separating it from
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md), which every session
*is* told to read in full — a document that keeps every decision's full
reasoning inline grows exactly the way this project's own founding case
study did (RPP's `AGENTS.md`: 29,443 → 71,059 bytes in three days) and
exactly the way this plan itself did before this mechanism existed
(56,675 → 108,557+ bytes across phases 0–4, entirely as accumulating
"Amendments Since Approval" entries — found by a 2026-09-01 deep-check
audit, which built this directory in response but did not retroactively
migrate the plan's existing amendment history into it: that is a larger,
judgment-heavy move on irreplaceable text, left for a session working
with the plan's author rather than done unilaterally).

## Format

Frontmatter, so decisions are queryable rather than prose to be grepped:

```
---
date:        2026-09-01
question:    What was actually being decided
decision:    What was decided
alternatives: ["Option considered and rejected", "Another one"]
decided_by:  Who decided
---

Prose explaining the reasoning, as long as it needs to be. Nothing here is
ever loaded automatically -- length costs nothing.
```

## Going forward

A new [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) amendment that
is actually recording a decision (not a change to what the plan itself
says the architecture does) belongs here, with only a one- or two-sentence
pointer left in the plan's "Amendments Since Approval" section — the same
split this project draws everywhere else between what is resident (short,
always paid for) and what is on-demand (long, read when someone actually
asks). `tools/verify_harness.py`'s `check_decision_records_not_inline`
enforces this going forward for newly-added amendment text.
