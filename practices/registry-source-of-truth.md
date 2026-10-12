---
slug:        registry-source-of-truth
title:       State lives in one machine-readable registry; documents derive
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Genuinely unroutable — see spec/LOADER.md. A registry is recognised by what it is for, and this repo's are .json, .py and .md alike. Decided: phase 4 routing pass."
occasion:    "tracking state several documents must agree on"
gates:       []
index_clause: "state lives in one machine-readable registry; documents derive"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork); extended 2026-10-12, Alex
  (strength: decided): a fix that needs a second list of what a tool
  already lists is the warning sign -- \"yes, add it to this PR\""
source_practice_number: 7
---
## Rule
Any status that scripts or sessions make decisions on (what's
released, what's pending, what version is installed) lives in exactly one
machine-readable registry. Human-readable documents restate it; they never
own it. When registry and document disagree, the registry wins — and an audit
([convention-to-audit](convention-to-audit.md)) detects the disagreement.

**A fix that needs a second list of things some tool already lists is the
warning sign.** Stop, and find where that tool's own list is already read;
read it there too, and register nothing twice.

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

**2026-10-12: the second list nearly built.** A rendered page kept going
stale because the commit-time rebuild never touched it. The first fix
proposed listing every render in the generated-files registry and labelling
each one, which would have spread into every consuming repository. The
renderer already listed its pages, and the same rebuild step already read
another tool's own list for the generated blocks inside documents; the
registry's own notes said so. The fix that landed reads the renderer's list.
Asked why the better way was missed: the design started from the registry
the rebuild reads and asked how to fit the page into it, never whether
that step already handled a kind with a list of its own.

## Install
`process/manifest.json` (see [INSTALL.md](https://github.com/alex137/BestPractice/blob/staging/INSTALL.md)) is itself
a registry of this kind, with baseline hashes checked by
[tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/staging/tools/practice_audit.py). Build your own registries
the same shape: entries + status + hash, one owner, one audit.
