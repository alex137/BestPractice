---
slug:        reply-links-files
title:       Every reply links the files it touched
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "ending a reply that created or modified files"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 12
---
## Rule
A session's reply that created or modified files ends with a
"Files touched" list: each entry links the file on the working branch *and*
its post-merge location, with a one-line description. The reader must be able
to open the work from the chat, not merely learn it exists.

**Rendered files get a rendered-view link, not just a repo link.** A
repository link to an HTML file or an image shows source or a raw blob — the
one form of the file the reader did *not* want. When the session's surface
offers hosted private previews (an artifact/paste service the harness
provides), a touched HTML render or picture's entry also carries that
rendered-view link, published from the same file path each time so the link
stays stable across revisions — one preview per file, re-published on
meaningful change, never a new one per reply. Files that are per-recipient
send records are excluded: a hosted preview is a distribution channel, and
those files' distribution is governed by their own send policy.

## Why

## Story

## Install
Convention in
[templates/AGENTS.md.template](templates/AGENTS.md.template).
