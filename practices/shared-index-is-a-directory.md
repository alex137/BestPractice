---
slug:        shared-index-is-a-directory
title:       A file many threads add entries to is kept as a directory, one file per entry
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus. Any index, digest, registry, glossary or log in any repository can be the file every thread appends to, wherever it lives; the practice is a property of how a file grows, not of a path. Decided: 2026-10-12, with the practice."
occasion:    "creating or adding to a file many threads append entries to (an index, digest, registry or log), or when such a file conflicts in a merge"
gates:       []
index_clause: "one file per entry in a directory; generate the view; a view conflict is rebuilt"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-12"
approved_by: "Alex, 2026-10-12 -- \"yes do the directory split\", answering his own \"should we modify where_things_are to be a diretory rather than a file to solve this problem? Can we make bestpractice of using directories rather than files when we have files that are really just indexes of some sort?\""
strength:    decided
source_practice_number: null
---
## Rule
**A file that many threads add entries to -- an index, a digest, a
registry, a glossary, a log -- is kept as a directory with one file per
entry, and the file people read is generated from it.** Two threads that
each add an entry add two files and never meet in a merge.

**Only the generated view may conflict, and a conflict there is resolved by
taking either side and rebuilding it**, because the directory is the truth.

## Detail
**What counts.** A file is an index when most of its growth is new rows or
new entries, each written by whichever thread produced the thing it lists.
A document people argue over paragraph by paragraph is not one; a table
every thread appends a row to is.

**The worked examples are already here.** `todo/` and `gotchas/` hold one
file per item, and `todo/TODO.md` and `gotchas/INDEX.md` are generated
lists. `MAP.source/` and `GLOSSARY.source/` hold a repository's own map and
glossary text the same way, and `MAP.md` and `GLOSSARY.md` are built from
them ([orientation-map](orientation-map.md)).

**Splitting a Markdown index that is headings plus pipe tables** is one
command:

    python3 tools/precedent_migrate_views.py --repo . --split-file docs/INDEX.md

It moves the text into `docs/INDEX/` -- one file per heading, one per row of
each section's main table, numbered with gaps -- leaves `docs/INDEX.md` in
place as the generated view, refuses unless the directory rebuilds the file
byte for byte, and lists the view in `tools/generated_files.json` where the
repository keeps one. Add an entry as a new file numbered between its
neighbours (`0015-` goes between `0010-` and `0020-`), then rebuild:

    python3 tools/precedent_migrate_views.py --repo . --join docs/INDEX --out docs/INDEX.md

`--check` on the join says whether the view is current and changes nothing;
the generated-files list runs it, and the commit backstop runs the rebuild
when an entry changes. A line typed into the view by hand is never
overwritten silently: the join refuses and names it. Links in an entry are
written as they were in the view, and the light check reads them against
the view's folder.

**An index generated from structured data already qualifies** -- a JSON
registry with one row per entry is still one file every thread edits, and
conflicts the same way once threads are busy enough. Splitting it is the
same idea in its own format; until then, a conflict there is resolved by
keeping both rows.

## Why
A table every thread appends to puts every thread's new row on the same
last line. Git cannot merge two different lines added at the same place, so
two branches that each did the obvious thing conflict, and the second one
to land stops. With one file per entry there is nothing to merge: each
branch adds a file the other never touched. The generated view can still
conflict, but resolving it takes no judgment -- either side, then a rebuild
-- so it never needs the person.

## Story
**2026-10-12, a downstream repository.** A branch failed to land twice on
merge conflicts in two hand-edited index files: its full "where things are"
index, a Markdown table with one row per document, and a plain-English
digest of its internal codes, a table with one row per code. Every
concurrent thread adds a row to each, so every pair of threads conflicted
on both.

The fix already existed for two other files. On 2026-10-04 Alex had asked
whether the map should be a directory "so we don't have so many collisions
when multiple threads are running", and `precedent_migrate_views.py
--split` was built for `MAP.source.md` and `GLOSSARY.source.md` -- but the
rule was written as a rule about the map, so nothing carried it to the
other indexes that collide the same way. Asked whether the practice should
be "using directories rather than files when we have files that are really
just indexes of some sort", Alex said "yes do the directory split", and
the split was generalized to any Markdown index the same day.

## Install
Nothing to install: the split and the join ship with the engine
(`tools/precedent_migrate_views.py`). The `shared-index-is-a-directory`
check in `tools/precedent_check.py` names, as an advisory, a hand-written
Markdown file whose tables hold many rows and that has not been split; it
never stops work, because whether a long table really grows by many hands
is a judgment only the repository's people can make.
