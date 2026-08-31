---
slug:        parallel-artifact-ledger
title:       Parallel-artifact families: transfer verdicts are per-mechanism, per-change, and ledgered
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a change must propagate across several parallel artifacts"
index_clause: "ledger the transfer verdict per member, per change"
checked_by:  null
defines:     ["parallel-artifact family"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 22
---
## Rule
When a family of artifacts embodies **one design in several
parallel forms** — the same architecture on different platforms, media,
languages, or markets — a change to any member presumptively transfers to the
others, and the transfer check obeys three constraints. **Decompose by
mechanism, not headline:** the verdict is formed per mechanism inside the
change, never once for a whole cluster — a cluster's headline can be
member-specific while a mechanism inside it transfers. **Verdicts are
per-change, not per-session:** a verdict recorded for one batch of changes
says nothing about the next batch added later, even minutes later; re-run the
check every time. **Every verdict is ledgered:** a dated row per change —
originating matter, and per member either *applied as `<what>`* or *no
transfer because `<reason>`* — with a small **audit that fails any change
date lacking a complete row**.

## Detail

## Why

## Story
The origin incident: a session recorded a headline-level verdict
("this cluster is member-specific — no transfer") that was true as a headline
and wrong for one mechanism inside it, which transferred to all three sibling
artifacts. Nothing forced the verdict to be decomposed, re-run, or recorded
per member, so the miss was invisible until a prompted second pass (practice
21) caught it. Free-text one-time verdicts have three failure modes the
ledger kills: wrong granularity (headline vs mechanism), staleness (new
changes inherit old verdicts), and unauditability (nothing can check what was
never recorded).

## Install
A ledger table (date | originating change | one verdict column
per family member) plus a small audit keyed on dated change markers in
whatever registry tracks the family — any marked date without a complete
ledger row fails. The family definition itself lives at the top of the
ledger, with the origin incident (practice 20).
