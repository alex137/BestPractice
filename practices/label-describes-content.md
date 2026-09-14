---
slug:        label-describes-content
title:       A label must describe what follows
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
gates:       []
index_clause: "\"one line\" must be one line; else name it for its content"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 27
---
## Rule
A heading or lead-in that names a form or length must match what it
actually introduces. Do not title something "in one line" / "one-pager" / "in
one paragraph" / "TL;DR" unless it literally is that. If a section runs to a
page, name it for its content, not for a brevity it doesn't have.

## Detail

## Why
A label naming a form — *in one line*, *TL;DR*, *one-pager* — is a **promise about the shape of what follows**, and a reader acts on it: they decide whether to read now, skim, or come back. Breaking it wastes the decision they just made on your behalf.

The damage is disproportionate to the error because it is not local. A reader who finds one label over-promising has learned something about the document's other claims, and the discount they apply is not confined to headings. In a document whose whole job is to be trusted, that reads as spin — the same credibility leak as a number that does not match its source.

The fix is cheap and always available: name the section for its content instead of for a brevity it does not have.

## Story
"The thesis in one line" sat atop three paragraphs; "the business
model in one line each" atop multi-line bullets. The label over-promises,
and a reader who trusts it feels misled the moment they read on — the same
credibility leak as a numeric claim that doesn't match its source. It reads
as spin in a document whose whole job is to be trusted.

## Install
A writing convention in the project instructions; catch it in
document review. The fix is almost always to rename the label to its content
("The thesis"), not to compress the content to the label.
