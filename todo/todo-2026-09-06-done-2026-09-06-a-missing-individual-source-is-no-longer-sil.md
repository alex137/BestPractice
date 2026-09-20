---
slug:              todo-2026-09-06-done-2026-09-06-a-missing-individual-source-is-no-longer-sil
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

- **Done 2026-09-06 — a missing individual source is no longer silent.**
    Kept as a stub rather than deleted, so a later item does not shift under
    anyone who cited it. `tools/precedent_resolve.py` now diagnoses the
    four states an unresolved individual source can be in and reports the
    two that are genuinely *unknown* rather than *none*, on stderr and as
    `individual_status` in `--json`;
    [spec/SOURCES.md](../spec/SOURCES.md) carries the row.

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
