---
slug:        produce
title:       "\"Produce\" is stage 5: move staging into main -- production"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Produce\", \"Make live\" or \"Promote 5\""
gates:       ["merge"]
index_clause: "stage 5: Promote staging into main (production); read strictly"
checked_by:  null
defines:     ["Produce", "Make live", "production"]
command:     {"Produce": "Stage 5 (Promote 5): move staging into main -- production -- with the full local checks plus the GitHub test, saying so first.", "Make live": "The same as **Produce**."}
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

## Why
The last step needs a word that is a verb like the others and has the "go
live" feel without "launch", which is common in tech and usually means
something much bigger. A theater production fits the ladder's metaphor.

## Story
Named 2026-09-28. The first word was "Picked up", which is ordinary coding
talk ("CI picked up the change"); "Production" followed, and became the
verb "Produce" so every stage reads as something to do.

## Install
Nothing new: the promotion tool and its checks are
[promote](promote.md)'s.
