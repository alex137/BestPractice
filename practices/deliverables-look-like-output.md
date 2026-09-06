---
slug:        deliverables-look-like-output
title:       Deliverables look like their output; the record doc holds everything else
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing a reader-facing deliverable with supporting apparatus"
gates:       []
index_clause: "the deliverable holds only what its audience needs"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
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
exists), linked once from the deliverable's footer and from the index. Where
a repo gives one of those kinds its own home, that home wins over the paired
record: under Precedent, a decision that is not about a practice goes to a
dated file in `decisions/`, and a practice's own originating incident goes to
its `## Story`
([PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md), "Where Decisions and
History Live").

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
   doc, or in the dated decision record where the repo keeps those. "Per a
   user decision" in a deliverable is doubly wrong: it is process residue,
   and it is unattributed.

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
The inherited incident this practice was minted from is not recorded here —
`## Story` was left empty for all 52 practices at phase-1 conversion, and
this one was not among the 19 the phase-1.5 editorial pass filled in. It
survives in the practice's own `## Why` (the leak recurred four times in one
repo before the written rule was replaced by a check) and, in more detail,
in the origin comment above check 6 in
[tools/doc_lint.py](../tools/doc_lint.py). Recorded as a gap rather than
reconstructed from those, which would be writing an incident this branch did
not witness.

**The amendment's own incident, 2026-09-06.** The Rule sent every kind of
apparatus to one paired record document. Precedent had since given one of
those kinds a different home — a decision that is not about a practice goes
to a dated file in `decisions/`, which this repo had been writing since the
record dated 2026-08-31 — and nothing updated the practice, so the rule and
the repo disagreed for a week about where a decision belongs.

The mechanical half had already turned into a live gate failure, reproduced
before it was fixed rather than argued from the code: a `decisions/` file was
not record-class, so check 6 linted a decision record as a deliverable and
flagged it for containing decision provenance — its entire purpose. And the
one reference the check allows a deliverable to carry had to match a
`_record.md`-style suffix, which a dated decision record's name does not, so
a deliverable that correctly *linked* its decision record instead of
restating the decision failed the gate for doing exactly what this practice
asks. The same class of miss as the 2026-08-31 fix that exempted
`practices/` and `spec/` after they failed check 6 for describing the
apparatus they document: each time, a new home for record-class content was
created and the check that protects deliverables was not told about it.

## Install
**Related.** The current-state rule (git is the history) and [index-remembers-past](index-remembers-past.md)
(provenance lives in the index) bound what a deliverable may remember;
[quote-discipline](quote-discipline.md) and [outward-summary-discipline](outward-summary-discipline.md) (quote discipline, adversarial pass) generate exactly the
apparatus this practice routes into the record doc.
