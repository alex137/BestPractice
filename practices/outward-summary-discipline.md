---
slug:        outward-summary-discipline
title:       Outward-facing summaries: a claims-to-source table, honest aggregation, and a recorded adversarial pass
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing an outward-facing summary of claims"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 25
---
## Rule
A document that summarizes a body of work for an external audience
carries three things. **(a) A claims-to-source table**: every quantitative
claim mapped to the living source that backs it — this is what makes
verification cheap enough to actually run. **(b) Honest aggregation**: any
sum over rows drawn from different sources names its rows and states its
dedupe rule beside the sum, after reading each row's defining prose for
inclusion statements (rows with different names are not additive until
proven additive); and in any companion computation, a revenue or benefit
line names its enabling condition and the computation either carries that
enabler's cost or excludes the line. **(c) A recorded adversarial pass
before external use**: claim-vs-source verification plus a cross-document
consistency sweep, run adversarially (a subtly different range counts as a
finding), with findings, resolutions, and the open tail written to a dated
diligence record. The record is part of the deliverable.

**(d) Run the pass automatically, in the same working session, before
reporting the work done** — do not queue it, offer it as an option, or defer
it to "before external use". Deferred verification is verification that does
not happen: the session that wrote the analysis is the one that still holds
the reasoning, and a later session inherits the conclusions without the
context that would let it attack them. Only genuinely external blockers (an
unreachable source, a number needing a field measurement) stay open, listed
as the open tail rather than used to postpone the pass. **(e) A correction
that moves numbers in the author's own favour carries its justification in
writing** — that direction needs the most scrutiny, not the least. **(f) When
a model composes two agents with different characteristic times, check the
slower one's cycle time against the faster one's before costing the
composition** — a cost model can be dimensionally perfect and still describe
an operation that cannot be performed. **(g) When comparing alternatives,
check that each side's standing/availability cost is charged, or that
neither is** — marginal-only costing of a human alternative against a
capital alternative that already carries its overhead is the commonest
one-sided comparison, and it flatters whichever side the author owns.
**(h) State which technology generation the incumbent is allowed to use.**
Costing your automated proposal against a manual incumbent compares your
future to their present. Give the incumbent the same generation of technology
your own case assumes, and where you claim an asymmetry — that a rule or a
physical constraint permits your automation but not theirs — justify it from
the environment rather than from convenience, and say which regime each
finding belongs to. **(i) When a term's sign or direction is the claim being made,
compute it — do not reason about which way it goes.** Directional assertions
about a model's own terms are the easiest thing to get backwards and the
hardest to notice, because they sound like understanding.

## Why
The same audit that produced practice 24 found twenty-two defects
in a summary whose every number had been written in good faith from real
sources: three differently-named rows summing one underlying market, a
benefit line booked without its gating cost, claims citing documents that
did not contain them, and stale values the sources had since revised. The
claims-to-source table let two independent reviewers verify thirty claims
in minutes — without it the pass would have been unaffordable and would not
have happened. The diligence record then made every fix auditable and left
an honest open-items tail the next revision inherits, converting a one-off
cleanup into a repeatable gate. Clauses (d)–(f) came later, from the
principal's standing direction after a second analysis shipped with its pass
queued rather than run ("I don't care about unchecked work"): the pass that
was then run immediately found that the model had silently assumed a
composite operation neither participant had time to perform — a defect no
amount of source-checking would have surfaced, because every input was
correct and only their *composition in time* was impossible. Clause (g) came
from the principal's next question — whether the human alternative's
availability cost had been modelled. It had not, while the authored side's
equivalent overhead was already charged; the omission was invisible because
each side's own numbers were internally consistent. Clause (h) followed
immediately: the same reviewer asked whether the manual incumbent should have
been allowed to automate too. It should — and modelling it removed most of the
proposal's advantage, leaving a narrower but defensible claim. The three
questions form a family: whether the composed parts fit in *time*, whether
both sides carry their *standing* costs, and whether both are costed at the
same *technology generation*. A fourth round added clause (i) after the
author's own answer to a reviewer's challenge asserted, confidently and
backwards, which way one of the model's terms inverted — inside the very pass
meant to be checking the work. The lesson generalises past cost models: a pass
that only re-reads reasoning reproduces its errors, while one that re-computes
the disputed quantity does not.

## Story

## Install
