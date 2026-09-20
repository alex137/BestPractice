---
slug:              todo-2026-09-14-consumer-doc-sync-carries-upstream-pairs
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a decision per module: vendor it, or make the check say \"not part of the consumer engine\" rather than naming a missing file."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="consumer-doc-sync-carries-upstream-pairs"></a>**The vendored
    `doc_sync.py` ships this repository's own `PAIRS`, and two checks skip
    on modules the consumer seed omits.** Measured 2026-09-14 on a §0
    install: `computed-numbers-in-scripts` skips with *"this is an upstream
    copy of PAIRS"*, `doc_lint.py --all` reports four unfindable analyses
    for documents the consumer never had, and `document-status-header`,
    `speculation-is-marked` and `docs-track-models` skip on
    `doc_lifecycle.py` and `catalogue_stats.py`, which
    `CONSUMER_ENGINE_FILES` does not include — so an adopter reading "a skip
    is not a pass" cannot tell which of 21 skips are theirs. **Blocked on:**
    a decision per module: vendor it, or make the check say "not part of the
    consumer engine" rather than naming a missing file. **Disposition:** wait
    (2026-09-14, the very deep check)

## How It Closes

Not open until: a decision per module: vendor it, or make the check say "not part of the consumer engine" rather than naming a missing file.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
