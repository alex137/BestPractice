---
slug:        registry-source-of-truth
title:       State lives in one machine-readable registry; documents derive
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "tracking state that multiple documents need to agree on"
gates:       []
index_clause: "state lives in one machine-readable registry; documents derive"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 7
---
## Rule
Any status that scripts or sessions make decisions on (what's
released, what's pending, what version is installed) lives in exactly one
machine-readable registry. Human-readable documents restate it; they never
own it. When registry and document disagree, the registry wins — and an audit
([convention-to-audit](convention-to-audit.md)) detects the disagreement.

## Detail

## Why
Duplicated state always diverges.

## Story
The worst version: a document header said one thing, the registry said
another, and a builder trusted the registry while humans trusted the header.
The fix was not "be careful" — it was declaring the registry the single
source of truth and auditing drift. Corollary: **baseline snapshots** —
record a content hash when state is declared (released, synced, approved),
and the audit flags any later change to content whose status claims it is
frozen.

## Install
`process/manifest.json` (see [INSTALL.md](INSTALL.md)) is itself
a registry of this kind, with baseline hashes checked by
[tools/practice_audit.py](tools/practice_audit.py). Build your own registries
the same shape: entries + status + hash, one owner, one audit.
