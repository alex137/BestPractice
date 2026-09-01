---
slug:        readers-vocabulary
title:       Outward-facing documents use the reader's vocabulary, not the sources'
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing an outward-facing document"
gates:       []
index_clause: "use the reader's words; gloss inline or replace"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 34
---
## Rule
A document written for an audience outside the work — a README, a
product page, a pitch, an onboarding guide — uses words the intended reader
already owns. Every term that names a category gets one of three verdicts:
it is **already the reader's word**, so keep it; it has a **plain
equivalent**, so use that instead; or it is **genuinely the right term**, so
gloss it inline on first use — a short parenthetical, in the sentence, not a
pointer to a glossary. The test that catches most cases: *if the term can be
replaced by a plain description of five words or fewer, it is jargon.*

## Detail

## Why
Jargon in an outward-facing document usually arrives from the
**sources**, not from the author — and that is what makes it systematic
rather than careless.

Two properties generalise from that:

- **The risk scales with how much research went into the document.** The
  more sources you read, the more of their register you carry, and their
  words feel natural precisely because you have just spent hours inside
  them. The documents most likely to fail this are the well-researched ones.
- **Recently acquired words are indistinguishable from long-held ones.** You
  cannot feel which words you learned this week. An agent is maximally
  exposed: it acquires a source's vocabulary within a single session, has no
  sense of when a word entered its usage, and writes fluently in whatever
  register it just read.

Note that a glossary is the **wrong remedy here**, which is what separates
this from [acronyms-glossary](acronyms-glossary.md). You can ask a colleague to consult the repo's
glossary. You cannot ask a prospective user to consult anything — they will
simply stop reading.

## Story
The origin incident: a product description aimed at people who work in
Google Docs and Notion used *forge* throughout — the self-hosted-git
community's word for a repository hosting platform — alongside *substrate*,
*lens*, and *stateless*. The owner's reaction was the diagnosis: "I have no
idea what it means or where it came from." It came from the research done
for the document days earlier. It had never been the author's word, and it
was certainly not the reader's.

## Install
A vocabulary pass, run as a **separate step after drafting**,
in the shape of [second-pass-capture](second-pass-capture.md)'s capture sweep: write the intended reader down
as a plain sentence, then walk every category-naming noun against *"would
this reader define this unprompted?"* Where the answer is no, apply one of
the three verdicts. Do it after the framing check of [frame-from-audience-question](frame-from-audience-question.md), since
reframing changes who the reader is.

The natural audit extension ([convention-to-audit](convention-to-audit.md)) is a per-repo list of known insider
terms, checked by [tools/doc_lint.py](tools/doc_lint.py) against documents
marked outward-facing — the same machinery as the scrub blocklist of
[scrub-gate](scrub-gate.md), aimed at comprehension instead of confidentiality. Keep it
**warning-level**: a glossed term is a legitimate pass, and only a human can
judge that.

**Related.** [acronyms-glossary](acronyms-glossary.md) (acronyms and a central glossary) is the
inward-facing counterpart — expansion for readers who will consult a list.
[label-describes-content](label-describes-content.md) (a label describes what follows) and [frame-from-audience-question](frame-from-audience-question.md) (frame from the
audience's question) are the other two audience-facing failures, and all
three survive each other: a document can be correctly framed, honestly
labelled, and still unreadable because of its vocabulary. Three separate
passes, not one.
