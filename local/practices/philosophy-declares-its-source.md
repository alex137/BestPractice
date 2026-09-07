---
slug:        philosophy-declares-its-source
title:       Every philosophy document records where its text originally came from
tier:        on-demand
severity:    default
applies_to:  ["philosophy/**"]
occasion:    "adding or re-syncing a document under philosophy/"
gates:       []
index_clause: "an essay carries its origin on line one -- a record, not a sync pointer"
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
provenance line naming **where its text originally came from**: the
document and version it was taken from, or, for a file written here, that
it was written here.

    <!-- Last updated: <date> (Buenos Aires) by <who>; source:
         <origin document>, version <N>. -->

**This is a historical record, not a sync pointer.** These essays have no
upstream: the notebook they were written in was retired on 2026-09-07 and
this directory is the only copy. Edit the files directly. Never delete the
line to make text look native to this repository when it was not.

## Detail
The check requires the first line of each `philosophy/**/*.md` file to be
an HTML comment containing either `source:` or `written here`. It cannot
verify a version number against anything, and never could — the origin
repository no longer exists. What it enforces is that the question *"where
did this paragraph come from?"* has an answer on the page, which is the
part that survives the upstream going away.

## Why
Text with no stated origin reads as though it was always here. That is a
small loss while someone still remembers, and a total one afterwards: an
essay carries more weight when a reader can see it was worked out
somewhere, over dozens of revisions, than when it appears to have been
typed in one sitting.

The version number is what stops the line from being decorative. "Version
41" says this document was rewritten forty times before it settled, which
is a fact about how much argument is behind it — and it is the only
remaining trace of that, now the repository holding those revisions is
gone.

## Story
2026-09-07, and the rule outlived the reason it was written for, which is
why it is worth recording both.

It was written that morning, when `themorgan/WorkingWithAI`'s `content/`
tree was copied into `philosophy/` as a **copy**: the originals stayed
where they were, nothing synced the two, and the version number existed so
a later session could see how far this tree had fallen behind. By that
afternoon Morgan had decided the opposite — one permanent home, here, and
the notebook retired. The drift the rule guarded against became impossible
by construction.

**The rule survived the retirement; only its purpose changed.** A
provenance line that can no longer be checked against anything is still
the only thing telling a reader that these essays were argued out over
dozens of revisions somewhere else first. Deleting the line because its
original job ended would have thrown away the record along with the
mechanism.

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
