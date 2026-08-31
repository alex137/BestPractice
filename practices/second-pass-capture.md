---
slug:        second-pass-capture
title:       The second-pass capture sweep: production work gets a separate capture review
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "finishing a substantial work-product, before the merge-time capture gate"
index_clause: "a separate capture pass after the work, not inside it"
checked_by:  null
defines:     ["capture sweep"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 21
---
## Rule
After producing any substantial work-product — a document, a design,
an analysis, a decision — the same session does a deliberate second pass **as
a separate step, not part of the production flow**, re-reading its own
reasoning against a short checklist: (a) did every idea discussed reach its
**durable artifact**, or does it live only in prose or conversation? (b) do
**parallel artifacts** that must track this change have their transfer
verdicts (practice 22)? (c) did technical value get its **cross-ledger
capture** — the business, operational, or planning implication recorded where
those live? (d) are open decisions **queued in the typed TODO** (practice 2)
rather than only in the conversation? (e) are the **indexes, registries, and
glossaries** synced? Run the sweep before the merge-time capture gate
(practice 10), so what it finds lands in the same change-set as the work.

## Detail

## Why
The production mindset cannot audit itself: while drafting, every
idea feels captured because it was *thought*. In the origin repo, an
owner-prompted "did we miss capturing anything?" sweep found two real gaps in
the same day's work — a cross-artifact transfer that had been waved off and a
competitor-inspired idea noted in passing but never landed — each of which
the drafting passes had individually missed. The separation is the point: the
sweep is a different cognitive act (reading for omissions) from drafting
(writing for completeness), and it is cheap — minutes against the cost of a
lost idea.

## Story

## Install
Add the checklist to the session-end or pre-merge ritual, before
the capture gate. Adapt the checklist items to the repo's ledgers (what
counts as a durable artifact, which registries exist). The trigger for
adopting it retroactively: the first time an owner's "did we miss anything?"
finds something — that incident is the origin story (practice 20).
