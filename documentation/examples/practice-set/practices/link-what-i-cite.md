---
slug:        link-what-i-cite
title:       Link what I cite, including the line
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "citing a file or a document"
index_clause: "cite with a link, and point at the line"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   doc-references-are-links
added:       2026-08-31
approved_by: "me, in the session that raised it"
---
## Rule
Every file or document named in something I write is a link, and a link to a
specific claim points at the line, not just the file.

## Detail

## Why
The universal practice already requires the link. This one is stricter about
where the link lands, because a reader sent to a two-thousand-line file to
find one sentence has been sent nowhere.

## Story
Written after a review comment that said, in full, "which line?".

## Install
`overrides: doc-references-are-links` is what makes this replace the
universal practice of that name rather than sit beside it. Without it, both
would be in force and a reader would have to work out which one won. The
resolver reports the replacement, so the practice being replaced is never
silently gone.

A personal practice can only override a lower source's practice this way if
that practice is not marked blocking. This one is not, so the override
stands.
