---
slug:        quote-discipline
title:       Quote discipline: compression rounds against the writer, and qualifiers travel
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "quoting or compressing someone else's figures"
index_clause: "compression rounds against you; qualifiers travel with the figure"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 24
---
## Rule
Two obligations whenever a document quotes a figure from another source.
**(a)** When a sourced range or multi-case figure is compressed for prose —
rounded, summarized to one number, or reduced to its typical case — the
compression **rounds against the writer's interest**, or quotes both ends. A
summary that must pick one number picks the one that makes its own argument
weakest. **(b)** A source's **qualifiers are part of the figure**:
*best-case*, *worst-case*, a scenario label, a verify flag, or a fidelity
grade worse than the house default all travel with the number into every
document that quotes it. Dropping the label is misquoting, even when the
digits are copied faithfully. **(c)** When the source in hand is itself a
**summary of a primary artifact** — a briefing, a digest, a recording's
recap, a colleague's paraphrase — read the primary before drawing a
*structural* conclusion from it. A summary preserves the facts its author
found interesting and silently drops the ones that carry the structure, so
the omission is invisible from inside the summary: nothing in it looks
missing.

**Corrections that arrive as a pair are adopted as a pair.** When verifying a
figure against sources turns up two corrections to the same item that pull in
opposite directions — a price lower than assumed *and* a service life shorter
than assumed, say — adopting only the half that flatters the position is
selective sourcing, the quote-discipline failure in a subtler coat. Take both
in the same edit and let the record state that they were adopted together and
what the net came to; a verification pass whose every accepted correction
happens to move one way should be re-read for the halves it declined.

## Why
The bias is systematic, so the countermeasure must be a standing rule, not
vigilance.

## Story
Clause (c) has a separate origin. A working session was handed an accurate
summary of a technical disclosure and reached the right conclusions about it
— then, on pulling the primary documentation, found the single fact the
whole analysis turned on: the flaw the summary described as an oversight was
structurally *unavoidable* in the design it appeared in, which converted the
finding from "an instance of a known bug class" into "an antipattern with a
general remedy" and changed what the work recommended. The summary was not
wrong about anything it said. It simply had no reason to mention the fact
that mattered most, and no reading of it would have revealed the gap.

An adversarial audit of an outward-facing summary found the same failure
four independent times in one document: every compression had drifted in the
flattering direction (a range's ceiling shaved down, margin bands quoted
above their source, an unfavorable finding described as missing data, a
favorable-case figure paired with an unfavorable-case market). None was a
deliberate misstatement — each was an ordinary summarization choice made
under the incentive every summary carries. A separate pair of findings
showed the qualifier failure: a schedule date its source twice labeled
*best-case* became the central case downstream, and a source's own
worse-than-default fidelity grade was silently overridden by the quoting
document's blanket precision claim.

## Install
