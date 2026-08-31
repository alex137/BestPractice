---
slug:        acronyms-glossary
title:       Acronyms are expanded, and a central glossary holds them
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
index_clause: "expand acronyms on first use; keep one central glossary"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 17
---
## Rule
A domain-dense repo accumulates far more acronyms and coined terms
than any reader — human or agent — keeps in their head. So: (a) **expand an
acronym on first use** in a document — *long form (ACRONYM)* — and/or carry a
short **"Acronyms" note at the bottom** of a document that uses several; and
(b) keep **one central glossary file** as the living master list, so an
expansion is never re-derived from scratch. When a session uses a term that
isn't in the glossary, it adds it there in the same pass. Identifiers that
already have their own registry (a code table, a component index) are pointed
to, not duplicated.

## Detail

## Why
In a repo-is-the-memory system the reader arriving at a document is
usually *not* the person who wrote it and often has none of the surrounding
context — the exact case an acronym silently assumes. One undefined initialism
can make a paragraph unreadable, and the cost compounds: a suite with dozens
of coined two- and three-letter terms becomes navigable only to its authors,
which defeats the point of writing it down. The central list is the same
single-source-of-truth instinct as practice 7 — derive the expansion in one
place, reference it everywhere — and the bottom-of-document note is the local,
low-friction form for the reader who won't leave the page.

## Story

## Install
A writing convention plus one living file (a `GLOSSARY.md` grouped
by theme, alphabetical within a group), and the natural audit extension
(practice 6) is built: [tools/doc_lint.py](tools/doc_lint.py) check 3 scans each
changed document for ALL-CAPS tokens absent from `GLOSSARY.md` — skipping ones
defined inline on the line (`long form (TOKEN)`) and a stoplist of common
words/units — and warns, the same "convention → loud check" shape as its
link/strikethrough checks. Warning-only and auto-disabled when the repo has no
`GLOSSARY.md`, so it never blocks a repo that hasn't adopted the practice.
