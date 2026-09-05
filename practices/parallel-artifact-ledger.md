---
slug:        parallel-artifact-ledger
title:       Parallel-artifact families: transfer verdicts are per-mechanism, per-change, and ledgered
tier:        on-demand
severity:    default
applies_to:  ["templates/harness/**"]
occasion:    "a change must propagate across several parallel artifacts"
gates:       []
index_clause: "ledger the transfer verdict per member, per change"
checked_by:  "tools/precedent_check.py"
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
per member, so the miss was invisible until a prompted second pass
([second-pass-capture](second-pass-capture.md)) caught it. Free-text one-time verdicts have three failure modes the
ledger kills: wrong granularity (headline vs mechanism), staleness (new
changes inherit old verdicts), and unauditability (nothing can check what was
never recorded).

## Install
A ledger table (date | originating change | one verdict column
per family member) plus a small audit keyed on dated change markers in
whatever registry tracks the family — any marked date without a complete
ledger row fails. The family definition itself lives at the top of the
ledger, with the origin incident ([mistakes-become-rules](mistakes-become-rules.md)).

This repo's own instance: [templates/harness/LEDGER.md](templates/harness/LEDGER.md)
for the [claude-code/codex/gemini-cli harness adapter family](templates/harness/README.md);
`tools/precedent_check.py`'s `parallel-artifact-ledger` check (found by
`checked_by` above) walks `git log --no-merges` for each member directory
(excluding the repository's own root commit, which is inception rather
than a change) and fails if any commit's hash isn't referenced somewhere
in the ledger. Checks only that a row exists for every commit that touched
a member, not that the recorded verdict is correct — see
[spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s "audit-judgment
result" for the run whose blind judge named this gap in the first place.
