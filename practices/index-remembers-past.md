---
slug:        index-remembers-past
title:       A document does not remember its past; the index does
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a document replaces or is replaced by an earlier one"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 48
source_rule_unlabeled: true
---
## Rule
Current-state documents (the no-revision-history rule) still need
*provenance* — a reader landing on a fresh document that replaced an older
one deserves to know the lineage, and the older document's readers deserve a
pointer forward. Neither note belongs in the documents themselves: the fresh
document opens clean (no "successor to…", no inherited framing debt), and
the superseded one is not edited into a museum label. **Provenance lives in
the repository index**: the index row for the new document names what it
succeeded, the row for the old one names what superseded it, and where the
evolution itself carries lessons worth keeping, they go in a dedicated
evolution-notes document the index points to. Commit messages carry the
rest.

## Why
**Why the index and not the document.** A document is read for its content;
an index is read for orientation — lineage is orientation. Provenance notes
inside documents also invert the current-state rule's economics: they start
accurate and decay (the successor gets its own successor; the note never
updates), whereas index rows are touched every time the map is maintained.

**Related.** The current-state rule (git is the history) this completes;
practice 41 (index what you write) supplies the index rows this rides on.

## Story

## Install
