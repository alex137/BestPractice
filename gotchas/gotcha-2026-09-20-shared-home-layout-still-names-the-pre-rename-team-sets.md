---
slug:            gotcha-2026-09-20-shared-home-layout-still-names-the-pre-rename-team-sets
status:          live
noted:           2026-09-20
severity:        minor
retired:         null
retires_when:    "PRECEDENT_FRESHNESS_ALSO is edited to name the precedent-shared-* paths, and the /home/user sibling clones are renamed or re-cloned to match"
---

## Symptom

In a multi-repo session rooted under `/home/user` (rather than a single
set), `themorgan/precedent-individual`'s own `precedent.json` names its
shared sources as `../precedent-shared-*`, but the sibling clones actually
on disk are named `precedent-team-*`, and `PRECEDENT_FRESHNESS_ALSO` names
the old paths too.

## Story

2026-09-20, in a session rooted at `alex137/BestPractice` with
`themorgan/precedent-individual` attached alongside it: `ls /home/user`
showed `precedent-team-repo-maintenance`, `precedent-team-working-style`
and `precedent-team-writing`, while
`/home/user/precedent-individual/precedent.json`'s `sources` list declares
`../precedent-shared-repo-maintenance`, `../precedent-shared-writing` and
`../precedent-shared-working-style` -- that file's own `_sources_comment`
documents the `precedent-team-*` → `precedent-shared-*` rename as already
done. `PRECEDENT_FRESHNESS_ALSO` in the environment still reads
`/root/precedent-individual=main;/home/user/precedent-team-repo-maintenance=main;/home/user/precedent-team-working-style=main;/home/user/precedent-team-writing=main`
-- the pre-rename names, in a variable a session cannot edit.

A set-rooted session (one whose primary repo IS a Precedent source set) is
unaffected: its own SessionStart hook clones sources fresh from whatever
`precedent.json` currently declares, so it gets the renamed paths
correctly. This only bites the shared, pre-existing `/home/user` layout,
where the sibling clones predate the rename and nothing re-clones them
under their new names automatically.

## Fix

**Not a session's to fix.** `PRECEDENT_FRESHNESS_ALSO` is Claude Code
environment configuration, not repository content -- editing it is
Morgan's own change to make in the environment's settings, not something a
session can patch around from inside a repo. A session that hits this can
rename or re-clone the `/home/user/precedent-team-*` directories to their
`precedent-shared-*` names by hand for its own run, but that fix does not
persist past the container and does not touch the environment variable
either way.
