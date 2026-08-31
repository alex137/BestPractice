---
slug:        check-source-architecture
title:       An option you invented is not a baseline — check the source architecture first
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "comparing an option against a baseline"
index_clause: "check both options exist in the source before costing them"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 40
---
## Rule
**The practice.** Before costing or optimising a trade between two configurations,
verify that **both configurations actually exist in the source architecture**. It is
easy to invent a decomposition, forget that you invented it, and then spend real
effort optimising within your own fiction — producing a defensible-looking analysis
whose baseline never existed.

The tell is a trade study where one side is described in the source material and the
other is described only in your own notes. If you cannot cite the alternative to a
document you did not write, you are not comparing options; you are comparing the
system to your model of it.

**When the check fires, correct the framing before the numbers.** Restating the
conclusion while keeping the invented structure leaves the same error with better
arithmetic. Re-derive from the source architecture, then re-cost — the corrected
answer often inverts the original one rather than adjusting it.

## Detail
**Three questions that catch it cheaply:**

1. **Can I cite the alternative?** Not "is it plausible" — *which document specifies
   it*. An option with no citation is a hypothesis wearing a baseline's clothes.
2. **Does the established practice already integrate what I am proposing to combine?**
   Integration is common in mature designs precisely because someone already did this
   trade. If the answer is yes, the separated form is the thing needing justification,
   not the combined one.
3. **Am I optimising a step that should not exist?** A cost or delay attached to
   moving between two things you separated is a strong signal you separated something
   that was whole.

## Why
**Why it evades the usual checks.** Every downstream number can be internally correct.
The arithmetic reconciles, the units balance, the assertions pass — because the error
is upstream of all of them, in the framing. An adversarial pass that verifies claims
against sources will not catch it either, since the invented option has no source to
contradict. Only going back to the primary architecture catches it.

## Story

## Install
**Related:** practice 29 (a variant re-derives what it inherits) is the sibling
failure — carrying forward a base's *choices* unexamined. This one is the inverse:
introducing a distinction the base never made.
