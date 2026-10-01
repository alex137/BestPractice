---
slug:        debut
title:       "\"Debut\" is stage 4: move pre-staging into staging, with the full checks"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE (\"Debut\", \"Promote 4\") -- stage 4, a Promote with the step named, like promote's entry. Routed by the `merge` gate. Decided: 2026-09-29, when the practice landed."
occasion:    "a person says \"Promote\", \"Promote N\" or a stage word (\"Consider\", \"Act\", \"Debut\", \"Produce\", \"Make live\"), or asks to plan, build or move work up a tier"
gates:       ["merge"]
gates_why:   "Debut and Produce are merges between branch tiers -- the moment that gate exists for, as for promote."
index_clause: "stage 4: pre-staging into staging, full checks"
checked_by:  null
defines:     ["Debut", "Test Readiness"]
command:     {"Debut": "Stage 4 (Promote 4), also called Test Readiness: move pre-staging into staging, with the full local checks, saying so first -- saving this session's own work to pre-staging first if it is not there yet."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-27 -- stage 4 of the five stages, \"Debut (Test Readiness: To Staging)\""
strength:    decided
---
## Rule
**Debut is step 4 of the five-stage ladder ([promote](promote.md)): a
Promote from pre-staging into staging.** It runs exactly what
[Promote](promote.md) runs with the step named:

    python3 tools/precedent_branches.py --promote --to staging --work BRANCH

([tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)), and everything Promote says holds:
the lock, the full local check on the batch, nothing moving unless it
passes. Work still on this session's feature branch goes through
[Booked](go-update.md) first, and the read-back names both stages.

**When a Debut is refused, fix what it named, then run every step once in
the session before booking and trying again** -- `## Detail` has the
command (Morgan, 2026-10-01, strength: assented).

**Where a repository has no pre-staging** -- a person who lands on staging
-- Debut has nothing to do, and says so.

## Detail
A refusal shows only part of what is wrong: the push check stops at its
first failing step, and a test that crashes takes the rest of its batch
down with it. So after fixing what it named, run:

    PRECEDENT_PUSH_CHECK_ALL=1 python3 tools/precedent_push_check.py --tier full --because "a Debut was refused"

Fix all of what that finds, book it, and Debut again. The next Debut reuses
that pass for the same files rather than running it a second time.

## Why
"Debut" names the step for what it means: the work's first appearance where
it is fully checked, ready to be judged for production.

## Story
Named 2026-09-27 with the rest of the ladder.

**2026-10-01: five Debuts for one batch.** A change booked earlier that
day broke tests only the full suite runs, and the refused Debuts turned
them up a few at a time: every refusal stopped at its first failing step,
and in the third a crashing test fixture took the rest of its batch down
with it. Each fix cost a booking and a Debut of about eight minutes. After
the fourth, a single run of every step came back clean, and the fifth Debut
reused it and passed. Run after the first refusal, it would have saved most
of those rounds.

## Install
Nothing new: the promotion tool and its checks are
[promote](promote.md)'s.
