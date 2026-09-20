---
slug:              todo-2026-09-06-upstream-only-registries-ride-along-in-vendored-engine-files
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but a deliberate pass — this touches the vendoring contract (does `precedent_vendor_engine.py` blank a registry on the way out, or does each file read its registry from a host-owned file?), and picking wrong makes every consumer's copy diverge from upstream's, which is the one thing that tre"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- **Upstream-only registries ride along in vendored engine files.**
    [tools/doc_sync.py](../tools/doc_sync.py)'s `PAIRS` hardcodes
    `spec/LOADER.md` and `spec/ENFORCEMENT.md`;
    [tools/model_audit.py](../tools/model_audit.py)'s `INSTRUMENTED` names
    [tools/catalogue_stats.py](../tools/catalogue_stats.py). None of those
    exist in a consuming repo, and both files became consumer-vendored on
    2026-09-06 — so the first real consumer refresh (that private consumer repo, the
    same day) inherited BestPractice's own registry and reported
    `scripts-assert-properties` violated with `computed-numbers-in-scripts`
    and `docs-track-models` skipped. Nothing is broken; the consumer's
    check output is just wrong about whose registry it is reading.
    `doc_sync.py`'s own docstring already anticipates the host case
    (*"a repo with `PAIRS = []`"*), so the mechanism exists and the
    vendoring step simply does not use it. **Blocked on:** nothing but a
    deliberate pass — this touches the vendoring contract (does
    `precedent_vendor_engine.py` blank a registry on the way out, or does
    each file read its registry from a host-owned file?), and picking
    wrong makes every consumer's copy diverge from upstream's, which is
    the one thing that tree is designed never to do. Do not fix it
    piecemeal from a consumer repo.

## How It Closes

Not open until: nothing but a deliberate pass — this touches the vendoring contract (does `precedent_vendor_engine.py` blank a registry on the way out, or does each file read its registry from a host-owned file?), and picking wrong makes every consumer's copy diverge from upstream's, which is the one thing that tre

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
