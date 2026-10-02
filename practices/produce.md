---
slug:        produce
title:       "\"Produce\" is stage 5: move staging into main -- production"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE (\"Produce\", \"Promote 5\") -- stage 5, a Promote with the step named, like promote's entry. Routed by the `merge` gate. Decided: 2026-09-29, when the practice landed."
occasion:    "a person says \"Promote\", \"Promote N\" or a stage word (\"Consider\", \"Act\", \"Debut\", \"Produce\", \"Make live\"), or asks to plan, build or move work up a tier"
gates:       ["merge"]
gates_why:   "Debut and Produce are merges between branch tiers -- the moment that gate exists for, as for promote."
index_clause: "stage 5: staging into main (production); read strictly"
checked_by:  null
defines:     ["Produce", "Make live", "production"]
command:     {"Produce": "Stage 5 (Promote 5): move staging into main -- production -- with the full local checks plus the GitHub test, saying so first. Here we graduate you from the practice to real-life production!", "Make live": "The same as **Produce**."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-29"
approved_by: "Morgan, 2026-09-28 -- \"the stage 5 word should be \\\"Produce\\\" to make it a verb like the previous ones\", with \"production\" kept as the noun for main; the session must read it in context, \"should not just do a simple grep for that exact word\""
strength:    decided
---
## Rule
**Produce is step 5 of the five-stage ladder ([promote](promote.md)): a
Promote from staging into main.** `main` is **production** -- what everyone
gets. It runs Promote with the step named:

    python3 tools/precedent_branches.py --promote --to main --work BRANCH

([tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)), with the full local check plus the
GitHub test, and nothing moves unless they pass. A Produce is the named
go-ahead that merging into `main` needs.

**Read it strictly.** "Produce", "production" and "make live" all occur in
ordinary sentences, and this is the step that changes what everyone gets.
It fires only when the message is plainly asking for this step; where the
reading is a genuine judgment call, say it out loud and confirm before
anything moves.

**If Claude Code's own safety check refuses it anyway, stop.** Say in one
line that Claude Code's auto mode stopped the move, not this repository's
rules, and ask for it again in words that name the move ("Produce: staging
into main"). Never route around the check; the durable fix is the person's
([gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production.md)).

## Why
The last step needs a word that is a verb like the others and has the "go
live" feel without "launch", which is common in tech and usually means
something much bigger. A theater production fits the ladder's metaphor.

## Story
Named 2026-09-28. The first word was "Picked up", which is ordinary coding
talk ("CI picked up the change"); "Production" followed, and became the
verb "Produce" so every stage reads as something to do.

Also landed in the shared set `precedent-shared-ladder` on 2026-10-02, approved there by Morgan F. Kept ACTIVE here, not deduplicated: universal is the one level every Precedent consumer resolves, and a plain universal-only consumer never resolves a pointer into `precedent-shared-ladder` -- deduplicating this copy would leave the rule in force nowhere for them (the failure `verify_harness.py --as-ci`'s consumer-fixture check exists to catch, and did, 2026-09-23). Both copies are genuinely in force; review both when editing either. Withdraw this copy later, deliberately, with `--dedupe-only --accept-reach-loss` once the audience that matters has taken `precedent-shared-ladder`.

## Install
Nothing new: the promotion tool and its checks are
[promote](promote.md)'s.
