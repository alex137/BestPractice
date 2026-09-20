---
slug:              todo-2026-09-06-source-repo-consumes-no-catalogue
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- <a id="source-repo-consumes-no-catalogue"></a>**A source repo consumes no catalogue, so it cannot check itself.**
    None of the three private sets has a `precedent.json`, so each set's
    `build_views.py` renders its own catalogue alone — and a universal
    practice cannot reach the set that dropped its own copy in favour of it.
    `very-deep-check` is in force in every consuming project and invisible
    inside `precedent-team-repo-maintenance` itself; so is
    `headline-capitalization`, whose team-level copy that set deduplicated.
    This is the structural half of why `status:` went unhonored in three
    loading channels for so long. **A design decision, not a bug fix** — a
    source repo eating its own cooking changes what binds a contributor to
    that set, so it needs Morgan's call before any work starts.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
