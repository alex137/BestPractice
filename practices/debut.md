---
slug:        debut
title:       "\"Debut\" is stage 4: move pre-staging into staging, with the full checks"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Debut\", \"Test Readiness\" or \"Promote 4\""
gates:       ["merge"]
index_clause: "stage 4: Promote pre-staging into staging, full checks"
checked_by:  null
defines:     ["Debut", "Test Readiness"]
command:     {"Debut": "Stage 4 (Promote 4): move pre-staging into staging, with the full local checks, saying so first -- saving this session's own work to pre-staging first if it is not there yet.", "Test Readiness": "The same as **Debut**."}
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

**Where a repository has no pre-staging** -- a person who lands on staging
-- Debut has nothing to do, and says so.

## Why
"Debut" names the step for what it means: the work's first appearance where
it is fully checked, ready to be judged for production.

## Story
Named 2026-09-27 with the rest of the ladder.

## Install
Nothing new: the promotion tool and its checks are
[promote](promote.md)'s.
