---
slug:        doc-references-are-links
title:       Document references are links; approximation is ≈
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
gates:       []
index_clause: "reference repo files as relative links; use \u2248, never ~"
checked_by:  "tools/precedent_check.py"
defines:     ["document reference"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 11
---
## Rule
(a) In-repo documents reference other repo files as relative
markdown links, never bare backticked filenames — docs are read on a web UI
where a bare name is a dead end. New text always links; any thread touching a
document fixes the references in the parts it touches. (b) Use `≈` for
"approximately", never `~` — two stray tildes on a line render as
strikethrough on GitHub, silently garbling text. (c) Links stay plain
markdown — don't reach for a raw HTML anchor to control link behavior:
GitHub's sanitizer strips `target=` (and most other attributes) from
anchors in rendered markdown, so an "open in new tab" link silently does
nothing there (*as of 2026-08*).

## Detail
**A practice file is the one document here that does not follow clause (a)
to the letter, and [practice-links-travel](practice-links-travel.md) is why.**
The catalogue is copied into every repository that adopts it, so a relative
link out of `practices/` is live where it was written and dead everywhere it
is read. Inside `practices/`, a reference to something that does not travel
with the file is an absolute URL into the publishing repository instead. The
clause is unchanged for every other document in the tree, which is nearly all
of them.

## Why
All born from real bugs: readers hunting for referenced files, an
outward-facing document that rendered with unintended strikethrough, and a
thread that spent two commits converting a link to a `target="_blank"`
anchor and reverting it once the rendered page proved the attribute was
stripped.

## Story
**All three clauses were born from real bugs, one each.**

(a) Readers hunting for referenced files. A bare backticked filename is a
dead end on a web interface, where these documents are actually read, and
the reader is left to search for something the writer already knew the path
to.

(b) An outward-facing document that rendered with unintended strikethrough.
Two stray tildes on one line are a markdown footgun: they are invisible in
the source and silently garble the rendered text, which is the worst
combination for a document going to someone outside the project.

(c) A thread that spent two commits converting a link to a `target="_blank"`
anchor and then reverting it, once the rendered page proved the attribute
was stripped. That is the clause's real value -- not the styling preference,
but the fact that somebody already paid to find out, so nobody has to pay
again.

## Install
[tools/doc_lint.py](../tools/doc_lint.py) checks all three — it
gates on files changed vs the default branch (the "fix what you touch"
scope, which also protects frozen documents), `--all` reports the backlog,
`--fix` rewrites `~`→`≈` on struck lines; `target=` anchors are reported as
warnings. Requires `cmarkgfm` for exact detection with GitHub's own
renderer.
