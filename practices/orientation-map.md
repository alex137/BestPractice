---
slug:        orientation-map
title:       An orientation map, read first
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "orienting in a repo for the first time this session"
checked_by:  null
defines:     []
status:      active
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

## Install
[templates/MAP.md.template](templates/MAP.md.template). Keep the
deliverable→backing-docs index current: any thread that adds a document adds
its row.
