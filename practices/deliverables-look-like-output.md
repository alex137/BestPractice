---
slug:        deliverables-look-like-output
title:       Deliverables look like their output; the record doc holds everything else
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
applies_to_why: "A reader-facing deliverable is a document. Its check already runs over changed markdown; the glob makes the Rule reachable at the same scope. Decided: phase 4 routing pass."
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
([PRACTICE_ENGINE_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_ENGINE_PLAN.md), "Where Decisions and
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
4. **The leak is the same in plain prose.** "Carried from memory until
   checked" is a verify-later flag; "which the next revision opens with" is
   a note about the document; "checked against search-engine snippets" is
   verification bookkeeping; "the record carries the tail" points the
   reader at apparatus. Each belongs in the record, however it is worded.
5. **A rendered page names things by title, never by repository path.**
   Linking a file by its filename is right on the forge, where the reader
   is in the repository; the reader of a render never is, and
   `fulton_configuration_model.py` tells them nothing. The renderer
   replaces a link whose text is the bare filename with the target's
   title, so the source keeps the repo convention and the page reads as
   output.

## Why
**Why a lint check and not a rule.** This practice failed as prose four
times in one repo — the leak recurs because the author writes apparatus at
the moment of doing the work, in the file that is open, and nothing objects.
The portable `doc_lint` therefore carries a residue check (check 6): a
changed deliverable containing verify-later flags, verification/claims
apparatus, unattributed decision references, or retirement lore fails the
gate; record-class files (by name pattern) are exempt. The written rule says
why; the check is what holds. The check matches the prose forms as well
as the bracketed ones (rule 4), and the shared renderer retitles filename
links (rule 5), so neither depends on the author remembering.

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

**The prose-form amendment's incident, 2026-10-01.** A consumer's three
most-read pages were republished after a model change and read in full on
the way out. Check 6 had passed every one of them, and they still carried
"public figures carried from memory … until checked against primary
sources", "the coast without a port, which the next revision opens with",
a comparator note ending "checked against search-engine snippets of the
maker's page, the page itself egress-blocked from the session (record, open
tail)", and "The record carries the tail." closing seven sections. Every
pattern check 6 knew was a bracketed flag or a fixed phrase, so the same
apparatus written as a sentence went straight through. The same read found
a dozen model filenames in each page's footer, shown to readers who have no
repository: the repo's link convention (filename as link text) was right in
the source and wrong in the render, and nothing turned one into the other.

## Install
**Related.** The current-state rule (git is the history) and [index-remembers-past](index-remembers-past.md)
(provenance lives in the index) bound what a deliverable may remember;
[quote-discipline](quote-discipline.md) and [outward-summary-discipline](outward-summary-discipline.md) (quote discipline, adversarial pass) generate exactly the
apparatus this practice routes into the record doc.
