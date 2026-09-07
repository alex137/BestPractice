---
slug:        docs-are-current-state
title:       Documents are current state; the VCS is the revision history
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
gates:       []
index_clause: "state what is true now; version control holds the history"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 26
---
## Rule
A document reads as a statement of what is true *now*, not a log of
how it got there. Do not annotate in-document when text was added or changed —
no "*(added DATE)*" / "*(rewritten DATE)*" section tags, no "Rev N" ladders in
headers, no superseded text kept inline "for history." Version control carries
all of that losslessly; `log`/`blame` answers "when did this change" better
than a prose annotation ever will, and never goes stale. Narrow exemptions,
where the date or prior state *is* the content: (a) records whose subject is a
dated decision or event ("decided DATE: X"); (b) volatile-fact freshness
stamps (practice for dated external claims); (c) legally or contractually
load-bearing markers; (d) as-shipped/as-filed artifacts whose purpose is
historical.

## Detail

## Why
An in-document annotation is a **second copy** of something version control already holds losslessly — and unlike the history, the copy does not update itself. So it does not merely fail to help; it decays into being wrong, and a "Rev 3" pointer outliving Rev 5 is worse than no pointer at all.

That makes the annotations a drift surface layered on top of the content they annotate, with the same maintenance cost as the content and none of its value. The reader pays as well: every one of them is text to read past on the way to what is currently true, forever, in exchange for an answer `log` and `blame` give better on demand.

The exemptions are narrow for the same reason the rule is broad — they cover the cases where the date or the prior state *is* the content, rather than a note about it.

## Story
A working document set accreted so many added/rewritten/Rev-N
annotations that documents read as changelogs instead of positions — and the
annotations themselves went stale (a "Rev 3" reference outliving Rev 5, an
"added 2026-…" tag on text three rewrites old), becoming a second drift
surface on top of the content. The revision history was already in the VCS,
losslessly; the in-document copy was pure liability.

## Install
State the convention in the project instructions with its
exemption list; when touching a document, strip stale revision annotations
from the parts you touch. A lint can flag `Rev \d`/`\*(added ` patterns
outside the exempted file classes.
