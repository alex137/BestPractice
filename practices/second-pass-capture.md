---
slug:        second-pass-capture
title:       "The second-pass capture sweep: production work gets a separate capture review"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "finishing a substantial work-product, before the merge-time capture gate"
gates:       ["merge"]
index_clause: "a separate capture pass after the work, not inside it"
checked_by:  null
defines:     ["capture sweep"]
status:      active
in_force_at: null
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
verdicts ([parallel-artifact-ledger](parallel-artifact-ledger.md))? (c) did technical value get its **cross-ledger
capture** — the business, operational, or planning implication recorded where
those live? (d) are open decisions **queued in the typed TODO**
([repo-is-memory](repo-is-memory.md))
rather than only in the conversation? (e) are the **indexes, registries, and
glossaries** synced? Run the sweep before the merge-time capture gate
([capture-gate](capture-gate.md)), so what it finds lands in the same change-set as the work.

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
**An owner-prompted sweep found two real gaps in a single day's work.**
Somebody asked "did we miss capturing anything?" of work that had already
been drafted, reviewed and considered finished, and the answer was yes
twice: a cross-artifact transfer that had been waved off, and a
competitor-inspired idea noted in passing but never landed anywhere durable.

The drafting passes had individually missed both. That is the finding, not
the two gaps themselves.

**The production mindset cannot audit itself: while drafting, every idea
feels captured because it was thought.** Thinking an idea and landing it in
a durable artifact are different acts that feel identical from the inside at
the moment of writing, which is why no amount of care within the drafting
pass substitutes for a separate one.

Hence the insistence that it is a separate step rather than a final section
of the production flow. Reading for omissions is a different cognitive act
from writing for completeness, and it only works when it is performed as
that different act. The cost argument closes it: minutes, against the cost
of an idea that is simply gone.

## Install
Add the checklist to the session-end or pre-merge ritual, before
the capture gate. Adapt the checklist items to the repo's ledgers (what
counts as a durable artifact, which registries exist). The trigger for
adopting it retroactively: the first time an owner's "did we miss anything?"
finds something — that incident is the origin story ([mistakes-become-rules](mistakes-become-rules.md)).
