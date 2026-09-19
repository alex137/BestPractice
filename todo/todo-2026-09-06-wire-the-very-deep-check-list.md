---
slug:              todo-2026-09-06-wire-the-very-deep-check-list
kind:              analysis
domain:            mechanism
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
closed:            2026-09-05
---
## What

- <a id="wire-the-very-deep-check-list"></a>~~**Enumerate and wire the inherited RepoPersonalPreferences (RPP) "very deep check" audit list as    an on-demand tool.**~~ **Done (2026-09-05)** — a session holding
    [RepoPersonalPreferences](https://github.com/themorgan/RepoPersonalPreferences)
    answered the redundancy question first: `full-practice-audit` asks,
    practice by practice, "is this Rule satisfied" — a closed question
    against one document's own text — while RPP's list asks whether the
    repo's *own writing*, taken as a set, still holds together
    (contradictions, stale cross-references, repeated rules, formatting
    drift, and the like), which no per-practice sweep can see. **Not
    redundant**, so it was built:
    [practices/very-deep-check.md](../practices/very-deep-check.md) plus
    [tools/very_deep_check.py](../tools/very_deep_check.py), same pattern as
    `routing-audit`/`full-practice-audit` (an on-demand practice file, an
    enumeration-only engine, never wired into a gate). The enumeration also
    found something nobody had connected: the same day's earlier phase-3
    migration (v27) had already carried RPP's list into
    `precedent-team-repo-maintenance` as its own `deep-check` practice, hours
    before v28's "not yet inventoried" was written — so the list was never
    actually missing, only unrecognized as fulfilling this commitment, and
    left with no companion engine and no reach outside that one private
    team set. Full record, including what this means for
    `precedent-team-repo-maintenance`'s own `deep-check` (a team-level call, not
    decided here): [spec/UNBUILT_PLAN_ITEMS.md](../spec/UNBUILT_PLAN_ITEMS.md)'s
    "Part 1, answered" section.

## How It Closes

Already closed 2026-09-05 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
