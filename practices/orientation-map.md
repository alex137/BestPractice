---
slug:        orientation-map
title:       An orientation map, read first
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "orienting in a repo for the first time this session"
gates:       []
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
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

## Install
[templates/MAP.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/MAP.md.template). Keep the
deliverable→backing-docs index current: any thread that adds a document adds
its row.
