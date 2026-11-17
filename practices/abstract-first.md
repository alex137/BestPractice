---
slug:        abstract-first
title:       A brief opens with an abstract, then its contents, then where its numbers come from
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A brief, report or write-up can live at any path, so no narrower glob names them; the occasion is what selects it."
occasion:    "writing or revising a brief, report or write-up for people to read"
gates:       []
index_clause: "abstract, contents, note on numbers; tight; no history in the document"
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
**A brief opens in this order: the title; one paragraph labeled *Abstract.*
in italics; the contents; then one paragraph saying where the document's
numbers come from** ([numbers-are-sourced](numbers-are-sourced.md)). The
abstract says what is being examined, how it is built and what it is judged
against, in the reader's own terms. It is never labeled "In short",
"Summary" or "TL;DR".

**The body is tight.** A section earns its place by carrying something the
reader needs in order to decide or to build. Background, a caveat said
twice and a survey of options nobody is choosing between come out.

**The document carries no history.** No comparison with an earlier version
the reader has not seen, no "what changed" section, no note about its own
revision ([docs-are-current-state](docs-are-current-state.md)). Changes go
in a record kept beside the document, never in it.

## Why
A reader handed a brief wants to know in one paragraph what it claims, then
to find the part they care about. A document that argues with its own past
versions makes them read a history they were never shown.

## Story
2026-11-17, a consuming project's hardware design brief. The session's
rewrite opened with a status note and a paragraph labeled "In short",
compared itself with "version 0.6" throughout, and closed on a "What
changed" section. Alex, reading it: "I see this document referring to prior
versions that haven't been shared", "you keep doing these write-ups in a
form that is such a waste of space and time. The top should have a tight
abstract. Then the ToC", and "Using **in short** is ridiculous style
nonsense. It should be *Abstract*". The rules against history in a document
were already in force, and no residue pattern matched a version reference;
`tools/doc_lint.py` gained three that day.

## Install
The order of the opening has no mechanical check: the session writing the
brief reads this rule at the occasion. The ban on history is checked, by
the residue patterns in `tools/doc_lint.py`, on any document in a declared
output path.
