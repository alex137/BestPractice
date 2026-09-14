---
slug:        section-order-by-frequency
title:       Section order follows the reader's frequency, not the writer's derivation order
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "ordering sections in a document"
gates:       []
index_clause: "order sections by how often the reader needs them"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 36
---
## Rule
In any document that walks through instructions, guidance, or rules
in multiple sections, order the sections by how often and how urgently the
reader will actually need them — common, everyday content first; rare edge
cases, migration scenarios, and "if the world changes" contingencies last —
unless the subject matter itself dictates a different order (steps that must
be followed in sequence, a narrative that only makes sense in one direction).
The test: would most readers have to scroll past this section to reach the
one they actually opened the document for?

## Detail

## Why
A document is drafted in the order its author thought it through,
which is rarely the order its reader needs it in. An edge case sits next to
the common case that motivated it, in the author's head, and that adjacency
survives into the draft even though almost no reader will ever hit the edge
case — they just have to read past it every time.

## Story
No dated incident was recorded. The rule names a specific mechanism by
which good documents drift, and the mechanism is what makes it checkable.

**A document is drafted in the order its author thought it through, which is
rarely the order its reader needs it in.** In the author's head an edge case
sits next to the common case that motivated it, because that is when they
thought of it -- and that adjacency survives into the draft.

The cost lands entirely on the reader, and lands repeatedly. Almost nobody
will ever hit the edge case, but everybody has to read past it, every time,
to reach the section they opened the document for.

The escape hatch is deliberate and narrow: where the subject matter itself
dictates an order -- steps that must be followed in sequence, a narrative
that only makes sense forward -- that order wins. The rule is about
frequency governing order where nothing else already does, not about
frequency overriding logic.

## Install
A writing convention, checked in review with the question
above; part of [templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.template)'s
Conventions section. No mechanical audit — "which order serves most readers"
is a judgment call, not a pattern a lint can reliably detect.
