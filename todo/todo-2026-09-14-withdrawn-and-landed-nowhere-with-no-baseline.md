---
slug:              todo-2026-09-14-withdrawn-and-landed-nowhere-with-no-baseline
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a design for what a set itself could refuse — a `git diff` guard in the set's own check that treats a deleted `practices/*.md` as a finding unless a deduplicated or retired record replaced it is the obvious shape, and it would sit in the set's `precedent-check.yml`."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="withdrawn-and-landed-nowhere-with-no-baseline"></a>**A rule
    withdrawn at its source and landed nowhere is still caught only where a
    consumer had already recorded it.** The move rehearsal of 2026-09-14
    ([spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md), "the fifth
    question") produced three reports that day — the resolver's `IN FORCE
    NOWHERE` for a forwarding address that resolves in no source, the
    sync's copy-and-delete warning, and
    [tools/precedent_move.py](../tools/precedent_move.py) refusing the unsafe
    states — and all three take a baseline: a deduplicated file with a
    target, or a committed `MANIFEST.json` naming the slug. A practice
    deleted outright from a set, in a consumer that never synced it, is
    reported by nothing; only the set's own `git log` shows the delete.
    **Blocked on:** a design for what a set itself could refuse — a
    `git diff` guard in the set's own check that treats a deleted
    `practices/*.md` as a finding unless a deduplicated or retired record
    replaced it is the obvious shape, and it would sit in the set's
    `precedent-check.yml`. **Disposition:** wait (2026-09-14, the move
    rehearsal)

## How It Closes

Not open until: a design for what a set itself could refuse — a `git diff` guard in the set's own check that treats a deleted `practices/*.md` as a finding unless a deduplicated or retired record replaced it is the obvious shape, and it would sit in the set's `precedent-check.yml`.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
