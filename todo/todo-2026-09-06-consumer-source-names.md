---
slug:              todo-2026-09-06-consumer-source-names
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

- <a id="consumer-source-names"></a>~~**Check the consumer repos' own source names against the convention.**~~
    **Done (2026-09-06.)** A private consumer repo — the one consumer
    that declares sources and was not attached when
    [practices/source-naming.md](../practices/source-naming.md) landed — was
    refreshed from its own session and merged. Its repo-local source was
    named after the repository itself; it is now `local`. What the pilot actually
    proved, beyond the rename: the refusal fired at the right moment
    (`precedent_sync_views`, before anything was written), its message was
    actionable enough that the session fixed the name without having
    [spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md) in its tree, and
    `precedent_check.py` reported `source-naming` as SKIPPED with its
    reason rather than passing falsely — the enforcement arrives with the
    engine, the explanation with the catalogue, and the gap between them
    is visible instead of silent. Two findings it surfaced are the
    `team-check-cites-retired-practice` item and the `code-cites-practice`
    fix that landed with this entry.

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
