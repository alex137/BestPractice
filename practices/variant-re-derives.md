---
slug:        variant-re-derives
title:       A variant re-derives what it inherits: limits it must respect, choices it need not keep
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "building a variant of an existing thing"
gates:       []
index_clause: "re-derive what a variant inherits; limits bind, choices do not"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 29
---
## Rule
When you build a variant of an existing thing — a new configuration
of a component, a fork of a process, a second instance of a design aimed at a
different job — treat **every attribute you inherited from the base as
unexamined until you have re-derived it against the new job**. Inherited
attributes come in two kinds, and both fail silently:

- **Constraints the base states** — which the variant must respect, and which
  your new reasoning may not have noticed it was violating.
- **Choices the base made** — which the variant is free to change, and which
  you may be carrying only because they were already there.

## Detail

## Why
The asymmetry is what makes this hard to catch. A constraint you violate tends
to produce an obviously wrong answer eventually. A choice you fail to re-open
produces a *plausible* answer that is merely answering the base's question
instead of yours — and the more carefully you work downstream of it, the more
solid it looks.

## Story
One piece of work made both mistakes about the same base, in opposite
directions, a day apart. First it computed a favourable property of a variant
and announced a capability from it, without reading the base's own stated
limits — which excluded that capability in plain language. Then it carried
forward one of the base's design *choices* without asking whether the change of
job had invalidated it; it had, and the inherited choice made the whole variant
unworkable at its intended duty cycle. The second miss was worse than the first
because the arithmetic built on it was internally correct: the numbers
described, in convincing detail, an operation that could not be performed.

## Install
When starting a variant, list what changed about the job — duty
cycle, duration, environment, load, audience, tempo — and walk the base's
attributes against that list, marking each *re-derived*, *inherited
deliberately*, or *not yet checked*. Nothing stays in the third state at
delivery. Two prompts do most of the work: *"what does the base say it cannot
do, and does my variant's reasoning quietly assume otherwise?"* and *"which of
the base's choices exist only because of a job my variant is not doing?"*

**Related.** Practice 20 (mistakes become rules) is how this one was derived —
and note that the second instance was folded into the *same* rule as the first
rather than minted as a new one, per that practice's proportionality guard: two
failures with one root cause get one widened guard, not two narrow ones.
