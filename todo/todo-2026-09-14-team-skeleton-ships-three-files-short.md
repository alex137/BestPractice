---
slug:              todo-2026-09-14-team-skeleton-ships-three-files-short
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the edit — the three files' current shape is in any of the three sets, and [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) already installs the individual hook for a new set, so the question is only whether the skeleton should carry a `precedent.json` with plac"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="team-skeleton-ships-three-files-short"></a>**All three team sets
    carry `precedent.json`, `precedent-individual-bootstrap.sh` and
    `precedent-universal-catalogue.sh`, and
    [templates/practice-set-team/](../templates/practice-set-team/) ships none
    of them.** Reported by the very deep check's `TEMPLATE FRESHNESS`
    section on 2026-09-14 — three of three sources of the level, which is
    the threshold that separates a habit from a template gap. The
    `precedent.json` carries each set's `fallback_timezone` and
    `visibility`; the two hooks are what the `wire-individual-hook-in-existing-sets`
    item (81) and the adapters declaration added after the skeleton was
    written. **Blocked on:** nothing but the edit — the three files' current
    shape is in any of the three sets, and
    [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
    already installs the individual hook for a new set, so the question is
    only whether the skeleton should carry a `precedent.json` with
    placeholders. **Disposition:** wait (2026-09-14, the very deep check)

## How It Closes

Not open until: nothing but the edit — the three files' current shape is in any of the three sets, and [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) already installs the individual hook for a new set, so the question is only whether the skeleton should carry a `precedent.json` with plac

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
