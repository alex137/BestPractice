---
slug:        search-by-purpose
title:       Search by purpose as well as by mechanism, and index what you write
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "concluding that no prior work exists on a question"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 41
---
## Rule
**The practice.** Before concluding that no prior work exists on a question,
search the repository twice: once in the vocabulary of the **mechanism** (how the
thing works) and once in the vocabulary of the **purpose** (why it was done). Then
make your own output findable under both.

## Why
**Why one search is not enough.** Prior work is usually filed under the author's
reason for doing it, not under the machinery it used. A search keyed on the
mechanism misses a document that describes the *same mechanism* under a different
mission, and vice versa. The two vocabularies rarely overlap in a single
document's prose, so each search returns a clean, plausible, complete-looking
result set with the other half absent.

**Why it evades the usual checks.** Nothing in the missing document's absence is
visible. An adversarial pass that verifies every claim against its source passes,
because each claim really is supported; a consistency check across the documents
you *did* find passes, because they really are consistent. The failure is not a
wrong claim but an unexamined duplication — you re-derive a number someone
already owns, and if your value differs, the contradiction lands silently in the
repository for a later reader to trip over.

**The tell** is an "open item" that seems too basic to be open: a quantity so
central to the question that someone would surely have needed it already. When a
result says *"this wants a measurement we do not have"*, ask who else would have
needed the same measurement, and search for **their** reason for needing it.

**The other half is your own output.** Everything above applies to the next
reader looking for what you just wrote. So:

1. **Name the purpose in the document**, not only the mechanism — including the
   uses you are not writing about, so a search for those lands here.
2. **Link the document from an index** a reader actually consults. An analysis
   reachable only by knowing its filename is one nobody will find.
3. **Link the prior work you found**, in both directions. The path between two
   documents is the artifact with the shortest half-life; it is also the cheapest
   thing to add while both are open in front of you.

**Prefer a mechanical guard over a resolution to search harder.** "Search both
vocabularies" is advice a hurried reader will skip. "A document carrying
generated numbers must be linked from an index, checked by the linter" is a rule
that holds while nobody is paying attention — it does not force the *right*
search, but it guarantees the target of that search exists somewhere findable.
Measure the backlog when you introduce the check; a non-trivial count is the
evidence that the failure was systemic rather than one person's bad day.

**Related:** [outward-summary-discipline](outward-summary-discipline.md) (read the primary, not the summary) is the sibling
failure in the *depth* direction — this one is in the *breadth* direction.

## Story

## Install
