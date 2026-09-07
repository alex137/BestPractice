---
slug:        philosophy-declares-its-source
title:       Every philosophy document says where it came from and what version it was copied at
tier:        on-demand
severity:    default
applies_to:  ["philosophy/**"]
occasion:    "adding or re-syncing a document under philosophy/"
gates:       []
index_clause: "a copied essay carries its source document and version on line one"
checked_by:  "tools/checks/check_philosophy_declares_its_source.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "Morgan, 2026-09-07, with the copy that created the need"
---
## Rule
Every markdown file under `philosophy/` opens with an HTML-comment
provenance line naming **where the document came from**: either the
upstream document and the version it was copied at, or, for a file written
here, that it was written here.

    <!-- Last updated: <date> (Buenos Aires) by <who>; source:
         themorgan/WorkingWithAI content/<FILE>, version <N>. -->

Re-syncing a document from upstream means updating that version number in
the same commit. Never delete the line to make an edit look native.

## Detail
The check requires the first line of each `philosophy/**/*.md` file to be
an HTML comment containing either `source:` or `written here`. It does not
verify the version number against WorkingWithAI — this repository has no
guaranteed access to that clone at check time, and a check that silently
skips whenever a sibling is missing teaches nothing. What it enforces is
that the question is *answerable*: a reader who wants to diff this copy
against its original knows exactly which file and which version to diff
against.

## Why
A copy with no stated origin is indistinguishable from an original, and
diverges silently. Six months on, nobody can tell whether a paragraph here
is an improvement that should be carried back upstream, an edit made here
for local reasons, or upstream text that has since been rewritten and
never re-pulled.

Naming the version, not just the file, is what makes the drift *visible*
rather than merely *possible to investigate*. "Version 41" against
upstream's current version 47 is a six-revision gap a session can see at a
glance.

## Story
2026-09-07. WorkingWithAI's `content/` was copied into `philosophy/` as a
copy, not a move: the originals stay where they are, and that repository's
three-stage pipeline keeps running there. So from the first commit this
tree has an upstream it can fall behind, and no sync workflow — nothing
here polls WorkingWithAI, and nothing there knows this copy exists.

The documents arrived already carrying a first-line header, from the
private individual-level `file-header` practice that governs them
upstream. That header records a per-file revision counter maintained by
that repository's own tooling, which does not run here — so left as-is,
every file would have carried a version number that could never advance
and named no source, which is worse than no header: it looks like live
provenance and is not. Rewriting them to name the source document and the
version *taken* turned a stale local counter into a real upstream pointer.

The same reasoning is why [philosophy/README.md](../../philosophy/README.md) states outright that the
copy is a copy. That sentence and this practice are the same defence
written twice, in the two places a reader might arrive.

## Install
Enforced by
[../tools/checks/check_philosophy_declares_its_source.py](../tools/checks/check_philosophy_declares_its_source.py),
a `tree`-scope check run by [tools/precedent_check.py](../../tools/precedent_check.py) from this
repo-local source. It reports NOT APPLICABLE when `philosophy/` does not
exist, so removing the directory does not fail the build.

[philosophy/doc-recipes/README.recipe.md](../../philosophy/doc-recipes/README.recipe.md) carries the same requirement as
a per-document recipe, since that is where someone editing the README will
be looking.
