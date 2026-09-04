---
slug:        vendored-engine-is-local-path
title:       This repo's vendored engine lives under vendor/precedent-engine/
tier:        on-demand
severity:    default
applies_to:  ["vendor/precedent-engine/**"]
occasion:    "exporting a tool across a repo boundary"
gates:       []
index_clause: "one vendored engine, thin host shims — here, under vendor/precedent-engine/"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   "engine-plus-host-shims"
added:       null
approved_by: "demo-consumer-repo fixture"
source_practice_number: null
---

## Rule
No file outside `vendor/precedent-engine/` duplicates a run of lines from
inside it — that is a fork, not a shim. Same rule as the universal
`engine-plus-host-shims`, narrowed to where *this* repo actually keeps its
vendored copy: `process/upstream/**` and `templates/harness/**` are
BestPractice's own paths for this, not this repo's.

## Why
The universal practice's glob names where BestPractice itself keeps
vendored/template text. In a host repo those paths are just unrelated files
(or don't exist at all) — the practice still applies, but only at the path
this repo actually vendors into.

## Story


## Install
This file lives at `local/practices/` per the repo-local convention
(`layered-practice-packs`: repo-local practices live in the declaring
repo's own instructions and never leave it). Materialize with
`python3 tools/practice_simulation.py build-fixture-repo`.
