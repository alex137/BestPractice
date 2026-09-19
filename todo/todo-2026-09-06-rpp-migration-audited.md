---
slug:              todo-2026-09-06-rpp-migration-audited
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
closed:            2026-09-06
---
## What

- <a id="rpp-migration-audited"></a>**Done 2026-09-06 — nothing was lost in the migration, and the audit
    is recorded here because no ledger holds it.** RepoPersonalPreferences'
    46 rule identifiers (from its own `process/personal/README.md` headings,
    cross-checked against its `MAP.md`) were diffed against 41 practices in
    `precedent-team-repo-maintenance`, 10 in `precedent-individual` and the
    placeholder in `precedent-team-tms`. **43 have a live descendant** — 39
    team, 4 individual, plus `bestpractice-sync`, retired in team and active
    in individual after the 2026-09-03 move. **3 have no active descendant,
    none of them lost:** `deep-check` moved to universal (retired in team
    2026-09-05 in favour of `very-deep-check`); `bestpractice-wins` was
    deliberately retired, its effect now carried structurally by the
    resolver's precedence; `morgan-scope` was deliberately retired, and its
    substantive half — the attributing account, and he/him — survives inside
    `precedent-individual`'s `commit-author.md` `## Detail`. That last one
    survived *by absorption rather than by design*: nothing recorded that it
    moved there, which is the whole argument for a ledger.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what
finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../`.
