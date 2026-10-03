---
slug:        orientation-map
title:       An orientation map, read first
tier:        on-demand
severity:    default
applies_to:  ["MAP.md", "AGENTS.md", "CLAUDE.md"]
applies_to_why: "The map and the instructions file that sends a session to it are the files this rule is about, so editing either is the moment it fires. Reading MAP.md first does not need this rule resident: the install template's first line tells every session to, and the orientation-map check refuses an instructions file that never names MAP.md. Decided: on-demand, Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)."
occasion:    "orienting in a repo for the first time this session"
gates:       []
index_clause: "a top-level MAP.md indexes the repo; every session reads it first"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork); tier on-demand: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)"
source_practice_number: 2
---
## Rule
A top-level `MAP.md` indexes the repo: what the key deliverables
are, where everything lives, and — crucially — which supporting documents back
each part of each deliverable. Every session reads it before doing anything.

## Detail

## Why
Without a map, every session greps. With one, orientation is one
file read, and "which documents back this section of the deliverable?" has a
committed answer instead of a fresh investigation.

## Story
No dated incident was recorded. The rule is a straight cost comparison, and
it is short because the comparison is not close.

**Without a map, every session greps.** That cost is paid once per session,
forever, by every person and every agent, and it is invisible because it
looks like ordinary work rather than like waste.

With a map, orientation is a single file read, and the harder question --
which supporting documents actually back this part of the deliverable -- has
a committed answer instead of a fresh investigation each time. That second
half is the part a bare directory listing cannot supply, which is why the
rule names it as the crucial one rather than settling for "where things
are".

**On-demand from 2026-10-01.** The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) found this rule resident in every session while the install template already opens each instructions file with "read `MAP.md` first" and the orientation-map check refuses one that never names it. Morgan approved making it on-demand, reached by editing `MAP.md` or the instructions file (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
[templates/MAP.md.template](https://github.com/alex137/BestPractice/blob/staging/templates/MAP.md.template), instantiated as
`MAP.source.md`. `MAP.md` is generated from it, plus the practice catalogue
and the engine, and is never edited by hand (Morgan, 2026-10-03, strength:
decided). Keep the deliverable→backing-docs index current in `MAP.source.md`:
any thread that adds a document adds its row there.
