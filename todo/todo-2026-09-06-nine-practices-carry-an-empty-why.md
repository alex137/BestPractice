---
slug:              todo-2026-09-06-nine-practices-carry-an-empty-why
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the work."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- **Nine practices carry an empty `## Why`.** Found 2026-09-07 by the Story
  backfill, which was scoped to `## Story` and deliberately did not widen:
  `docs-are-current-state`, `environment-gotchas`,
  `generated-artifact-provenance`, `label-describes-content`,
  `layered-practice-packs`, `lead-with-what-it-is`, `merge-runbook`,
  `one-formatter-per-quantity`, `parallel-artifact-ledger`. A tenth,
  `reply-links-files`, had an empty Why *and* an empty Story and was fixed in
  that pass, which is how the rest were noticed.
  This is a different gap from the Story one and probably has a different
  cause: `## Why` is reasoning the converter *did* carry across, so an empty
  one suggests the source practice stated a rule with no separate rationale
  rather than that anything was lost. Worth confirming against
  `PRACTICES.md` before writing anything — and note that
  [catalogue-carries-stories](../practices/catalogue-carries-stories.md)
  deliberately checks Story only, so nothing currently reports these.
  **Blocked on:** nothing but the work.

## How It Closes

Not open until: nothing but the work.

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
