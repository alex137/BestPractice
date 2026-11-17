---
slug:        numbers-are-sourced
title:       Every number is a choice, a sourced figure or a model's output, never an estimate
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A number can be written into any document, table or model, so no narrower glob names them; the occasion is what selects it."
occasion:    "writing a number into a document, table or model"
gates:       []
index_clause: "a number is a choice, a stored-source figure or a model output; no estimates"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-17"
approved_by: "Alex, 2026-11-17"
strength:    decided
---
## Rule
**Every number in a document is one of three kinds, and the document says
which.**

1. **A choice**: a value the team picks. The text calls it a choice.
2. **A sourced figure**: it links to its source, and a copy of that source
   is stored in the repository, so the figure can still be checked after
   the link dies.
3. **A computed figure**: the output of a model in the repository whose
   only inputs are choices, sourced figures and defined constants
   ([computed-numbers-in-scripts](computed-numbers-in-scripts.md)).

**Nothing is just an estimate.** A figure recalled, guessed or rounded from
general knowledge does not go in, however clearly it is labeled
([no-invented-specifics](no-invented-specifics.md)). Where a figure is
needed and has no source yet, the document names the quantity, gives no
value, and lists it as an open item.

**The document says so under its contents**, in the paragraph on where its
numbers come from ([abstract-first](abstract-first.md)).

## Why
A labeled estimate still gets quoted without its label, and a decision
built on it cannot be checked. A missing figure named as missing tells the
reader exactly what work is left.

## Story
2026-11-17, a consuming project's hardware design brief. The session's
rewrite carried order-of-magnitude area and latency estimates, prices
copied from an earlier text with no stored source, and bandwidths assumed
per process, each labeled as an estimate or an illustration. Alex: "We
should also impose a rule that every number either is linked to a source
with a copy stored in the repo or the output of a computation from a model
that uses sourced numbers also into the repo. Nothing should be just an
estimate." All of them came out of the brief and were listed as figures
still to be sourced.

## Install
No mechanical check: whether a figure has a source cannot be read off the
text, since a sourced figure and a recalled one are the same shape. The
paragraph under a document's contents is where a reader can hold it to the
rule.
