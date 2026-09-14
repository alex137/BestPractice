---
slug:        quick-index
title:       A quick index before searching
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "looking for where something lives, before searching"
gates:       []
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 3
---
## Rule
The project instructions file carries a "check here BEFORE searching
the repo" table: *looking for X → go to Y*, one row per thing sessions
actually hunt for.

## Detail

## Why
The map orients top-down; the quick index answers the specific
lookups that recur ("where are the canonical names?", "which script builds the
deliverable?"). Rows are added exactly when a session is observed searching
for something — the index is built from real misses, not speculation.

## Story
No dated incident was recorded, but the rule carries an unusual
construction constraint that is worth keeping, because it is what
distinguishes this from the map beside it.

**Rows are added exactly when a session is observed searching for
something.** The index is built from real misses, not from speculation about
what someone might want. An index written by imagining likely lookups fills
up with plausible rows nobody uses, and the real recurring lookups -- which
are often oddly specific -- never get added.

The division of labour with `orientation-map` is the other half. The map
orients top-down, answering what this repo is and how it is arranged. The
quick index answers the specific lookups that recur: where the canonical
names live, which script builds the deliverable. Those are different
questions, and collapsing them produces a document that serves neither.

## Install
Part of
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.template).
