---
slug:              todo-2026-09-06-migrated-practices-lost-their-stories
kind:              verify
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-07
---
## What

- <a id="migrated-practices-lost-their-stories"></a>~~**The RepoPersonalPreferences (RPP) migration dropped every `## Story`, and that is the
    provenance the catalogue exists to keep.**~~ **Done — confirmed by
    re-measurement, 2026-09-07.** The backfill happened; this item outlived
    it and went on asserting figures that were no longer true. Every one of
    the **57** practice files across all three private sets — 42 in
    `precedent-team-repo-maintenance` (40 active, 2 deduplicated), 14 in
    `precedent-individual`, 1 in `precedent-team-tms` — now has a non-empty
    `## Story`, at any status. So do all 57 `## Why` sections. Nine files
    have an empty `## Detail`, which is not a violation:
    [catalogue-carries-stories](../practices/catalogue-carries-stories.md)
    requires a Story, and Detail is optional.

    The three specific claims this item carried are all now false, and each
    was checked rather than assumed: it is not "34 of 41 and 3 of 10" (it is
    0 of 57); `header-caps` has a `## Why`; and `fail-gracefully` has
    substantial Detail, Why *and* Story — 1,123, 751 and 1,204 characters.
    The counts had also drifted with the catalogue: 41 and 10 were the sizes
    when this was written, against 42 and 14 today.

    The measurement itself is worth recording, because the first attempt at
    it was wrong in the direction this project keeps warning about. Reading
    the sections with the key `'Story'` instead of `'story'` returned `None`
    for every file and reported **100% empty across all three sets** — a
    confident, precise, entirely false finding, and one that happened to
    agree with what this stale item already claimed. It was caught only
    because 100% is not a believable number, not because anything failed.
    The corrected sweep therefore asserts a control first: a practice known
    to have all three sections must come back non-empty, or the sweep
    refuses to report. "Could not read" and "read, found nothing" must never
    render identically — the rule is `fail-gracefully`'s second clause, and
    the finding above is what it looks like when nothing enforces it.

## How It Closes

Already closed 2026-09-07 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
