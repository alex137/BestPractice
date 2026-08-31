---
slug:        doc-references-are-links
title:       Document references are links; approximation is ≈
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a document"
checked_by:  "tools/doc_lint.py"
defines:     ["document reference"]
status:      active
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

## Why
All born from real bugs: readers hunting for referenced files, an
outward-facing document that rendered with unintended strikethrough, and a
thread that spent two commits converting a link to a `target="_blank"`
anchor and reverting it once the rendered page proved the attribute was
stripped.

## Story

## Install
[tools/doc_lint.py](tools/doc_lint.py) checks all three — it
gates on files changed vs the default branch (the "fix what you touch"
scope, which also protects frozen documents), `--all` reports the backlog,
`--fix` rewrites `~`→`≈` on struck lines; `target=` anchors are reported as
warnings. Requires `cmarkgfm` for exact detection with GitHub's own
renderer.
