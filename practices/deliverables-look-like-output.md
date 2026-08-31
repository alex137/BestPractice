---
slug:        deliverables-look-like-output
title:       Deliverables look like their output; the record doc holds everything else
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing a reader-facing deliverable with supporting apparatus"
index_clause: "the deliverable holds only what its audience needs"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 49
source_rule_unlabeled: true
---
## Rule
A reader-facing document is the finished product: it contains what its
audience needs and nothing about how it was made. Everything else — the
claims-to-source table, the verification log, decision provenance ("who
chose this and when"), retired-alternative lore, open verify-later items,
notes about the document itself — is real and worth keeping, and lives in a
**paired record document** (`*_record.md`, or the diligence record where one
exists), linked once from the deliverable's footer and from the index.

## Detail
Three rules:

1. **If it is not intended to travel with the text, it goes in another
   document.** The test is the reader: would the audience the document is
   written for act on this line? Apparatus that exists for future verifiers
   and future maintainers is record-doc content by definition.
2. **A verify-later flag is a prompt, not a label: go verify now.** The
   inclination to write "[verify]" marks the exact moment verification is
   cheapest — the claim and its context are in hand. Only an externally
   blocked item (an unreachable primary source, a needed field measurement)
   may remain open, listed in the record's open tail — never flagged in the
   deliverable.
3. **A decision cited anywhere names its decider and date** — in the record
   doc. "Per a user decision" in a deliverable is doubly wrong: it is
   process residue, and it is unattributed.

## Why
**Why a lint check and not a rule.** This practice failed as prose four
times in one repo — the leak recurs because the author writes apparatus at
the moment of doing the work, in the file that is open, and nothing objects.
The portable `doc_lint` therefore carries a residue check (check 6): a
changed deliverable containing verify-later flags, verification/claims
apparatus, unattributed decision references, or retirement lore fails the
gate; record-class files (by name pattern) are exempt. The written rule says
why; the check is what holds.

## Story

## Install
**Related.** The current-state rule (git is the history) and practice 48
(provenance lives in the index) bound what a deliverable may remember;
practices 24–25 (quote discipline, adversarial pass) generate exactly the
apparatus this practice routes into the record doc.
