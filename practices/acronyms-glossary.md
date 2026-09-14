---
slug:        acronyms-glossary
title:       Acronyms are expanded, and a central glossary holds them
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
gates:       []
index_clause: "expand acronyms on first use; keep one central glossary"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
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
isn't in the glossary, it adds it in the same pass — **and where the glossary
is generated, it adds it at the glossary's source, never by editing the
generated file** (in this catalogue, the `defines:` field of the practice that
owns the term; see [generated-edit-goes-upstream](generated-edit-goes-upstream.md)).
Identifiers that already have their own registry (a code table, a component
index) are pointed to, not duplicated.

## Detail

## Why
In a repo-is-the-memory system the reader arriving at a document is
usually *not* the person who wrote it and often has none of the surrounding
context — the exact case an acronym silently assumes. One undefined initialism
can make a paragraph unreadable, and the cost compounds: a suite with dozens
of coined two- and three-letter terms becomes navigable only to its authors,
which defeats the point of writing it down. The central list is the same
single-source-of-truth instinct as [registry-source-of-truth](registry-source-of-truth.md) — derive the expansion in one
place, reference it everywhere — and the bottom-of-document note is the local,
low-friction form for the reader who won't leave the page.

## Story
No originating incident was recorded for this rule, and this Story does not
invent one. What it prevents is a cost that accrues rather than an event
that happened: in a system where the repo is the memory, the reader arriving
at a document is usually not its author and has none of the surrounding
context an acronym silently assumes. One undefined initialism can make a
paragraph unreadable, and a suite carrying dozens of coined two- and
three-letter terms ends up navigable only to the people who wrote it, which
is the exact failure the writing-it-down was meant to prevent.

The two halves answer two different readers. The central glossary is the
same single-source instinct as `registry-source-of-truth` -- derive an
expansion once, reference it everywhere -- and the bottom-of-document note
is the local, low-friction form for the reader who will not leave the
page.

**One incident IS recorded, and it is this rule pointing the wrong way.**
Until 2026-09-11 the Rule above said, without qualification, that a session
adds a missing term "there" -- to the glossary file. This practice's
`applies_to` is `**/*.md`, which matches `GLOSSARY.md` itself, so
`python3 tools/precedent_paths.py GLOSSARY.md` served that instruction to any
session about to touch the file. In Precedent `GLOSSARY.md` is generated from
every practice's `defines:` field and its own first line reads
`do not hand-edit`; a session following this Rule would have made an edit the
next `build_views.py` run destroys silently, and
`generated-artifact-provenance`'s check would have failed the commit for
doing what this practice told it to do. Raised by Morgan, who had been asking
for glossary additions in exactly those words for months.

The fix is the clause above rather than a narrower `applies_to`: the
acronym-expansion half of this rule is right for every markdown file
including a generated one -- what was wrong was telling a session where to
write.

## Install
A writing convention plus one living file (a `GLOSSARY.md` grouped
by theme, alphabetical within a group), and the natural audit extension
([convention-to-audit](convention-to-audit.md)) is built: [tools/doc_lint.py](../tools/doc_lint.py) check 3 scans each
changed document for ALL-CAPS tokens absent from `GLOSSARY.md` — skipping ones
defined inline on the line (`long form (TOKEN)`) and a stoplist of common
words/units — and warns, the same "convention → loud check" shape as its
link/strikethrough checks. Warning-only and auto-disabled when the repo has no
`GLOSSARY.md`, so it never blocks a repo that hasn't adopted the practice.
