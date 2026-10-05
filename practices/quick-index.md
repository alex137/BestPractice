---
slug:        quick-index
title:       A quick index before searching
tier:        on-demand
severity:    default
applies_to:  ["AGENTS.md", "CLAUDE.md", "WHERE_THINGS_ARE.md"]
applies_to_why: "The table lives in the instructions file (or the full index it links), so editing one of those is the moment it fires. The table itself is what a searching session reads, and the install template carries it; the quick-index check refuses an instructions file without one. Decided: on-demand, Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)."
occasion:    "looking for where something lives, before searching"
gates:       []
index_clause: "the instructions file carries a \"looking for X -> go to Y\" table"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork); tier on-demand: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)"
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

**On-demand from 2026-10-01.** The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) found this rule resident in every session while the table it asks for sits in every instructions file the install template writes, and the quick-index check refuses one without it. Morgan approved making it on-demand, reached by editing the instructions file or `WHERE_THINGS_ARE.md` (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
Part of
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/staging/templates/AGENTS.md.template).
