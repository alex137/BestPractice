---
slug:        frame-from-audience-question
title:       Frame the deliverable from the audience's question, not from the material in hand
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "starting an outward-facing deliverable"
gates:       []
index_clause: "build it around the audience's question, not your material"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 28
---
## Rule
When you finish producing a body of work and then write the thing
that explains it — a pitch, a summary, a README, a recommendation — build it
around **the question the audience actually has**, and check explicitly that
you have not instead built it around **the material you just produced**. The
tell is that the deliverable's headline matches the shape of your recent work
rather than the shape of the reader's problem. If a one-sentence statement of
the audience's question does not appear near the top, you probably skipped
this.

## Detail

## Why
This is a specific failure of *sequence*, not of care: the more thoroughly you
have just worked something out, the more available it is when you sit down to
explain, and availability reads as importance. Effort spent on a component is
not evidence that the component is the headline.

## Story
A thread had just produced a detailed body of work on one property of
a system, and wrote the outward-facing explanation around that property. It
was true, well-evidenced, and nearly useless to the reader, whose question was
a different one that the same machinery answered better. The correction came
from outside and reframed the whole document — including which limitation was
binding, which market to lead with, and which mechanism was the strongest thing
on offer. Nothing was wrong with the underlying work; the framing was wrong
because it inherited the author's recent path instead of the reader's need.

## Install
Before writing an outward-facing artifact, write the audience's
question down as a plain sentence — literally, in the draft — and confirm the
artifact answers *that*. Keep it in the finished document if it helps the
reader; delete it if not. In review, ask of the opening: *whose question is
this?* When a reframe does arrive, record what it changed — but record it in the
**dated review artifact, not in the deliverable**. A reader who saw the earlier
version deserves the diff and the failure mode should stay legible ([mistakes-become-rules](mistakes-become-rules.md)
applied to framing rather than to defects), yet a "what this used to say" block
inside a living document is precisely the changelog that [docs-are-current-state](docs-are-current-state.md) forbids.
Put it where dated history belongs; leave the deliverable reading as current
state.

**Related.** [docs-are-current-state](docs-are-current-state.md) (documents are current state) constrains *where* the
reframe record goes — the two practices collide if this one is read as
licensing a changelog inside the artifact, and the review record is the
resolution. [outward-summary-discipline](outward-summary-discipline.md) (an adversarial pass on outward-facing work) will not
catch this on its own: a well-framed-for-the-wrong-question document survives
claim-to-source verification intact, because every claim in it is true. The
framing check has to be separate, and it has to happen before the verification
pass rather than after.

**The internal case: a specification organised by answers hides its own
requirements.** The same failure has a quieter form aimed inward. A
specification that opens with identity, then dimensions, then a catalogue of
capabilities is organised by *what we decided*, and a reader who wants to know
*what the thing must do* has to reverse-engineer the requirements out of the
answers. That is tiring, and it is why the owner of a system can find its own
specification unreadable without being able to say why.

What makes this worth a separate note is the failure it causes rather than the
discomfort it causes. **A catalogue is indexed by subsystem or by feature, and a
requirement that crosses every subsystem has nowhere to live** — so it either
appears nowhere, or appears as an implementation detail inside whichever
subsystem happened to mention it first. Those cross-cutting requirements are
usually the load-bearing ones: the shared interface every other choice depends
on, the worst-case condition that sizes the structure. They are also the
expensive ones to discover late.

**Install.** Give a specification a requirements section *first* — a numbered
list of what must be true, each entry pointing at the section that specifies
how. Write it by asking "what must be true?" rather than by summarising the
sections below it, because summarising reproduces the same index and therefore
the same blind spot. Two prompts flush out most of what a catalogue loses:
*which requirement belongs to no single subsystem?* and *which case actually
sizes this — is it the one we describe most, or the one we describe least?*
