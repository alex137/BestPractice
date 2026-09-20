---
slug:              todo-2026-09-14-consumer-hears-about-files-it-does-not-have
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a consumer-aware remedy renderer (the engine knows its `kind` from `tools/ENGINE_MANIFEST.json`, so the upstream URL can replace a relative path there) and a `precedent.json` key that records \"no individual source, on purpose\"."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="consumer-hears-about-files-it-does-not-have"></a>**The engine's
    remedy strings and the loader template send a consumer to files only
    this repository has.** Measured 2026-09-14 on a §0 install: every
    prompt, stop and `vendor_engine status` prints *"Copy config.json.sample
    from templates/practice-set-individual/"* (no `templates/` in a
    consumer), session start prints *"see spec/BOOTSTRAP_NEW_SOURCES.md"*
    (no `spec/`), and
    [templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)
    says *"see INSTALL.md §0"* (no `INSTALL.md`). The same rehearsal found
    that an administrator who answered "no individual set" is told *"treat
    this as unknown, not as 'none'"* on every session start, every prompt
    and every stop, with no way to record the answer. **Blocked on:** a
    consumer-aware remedy renderer (the engine knows its `kind` from
    `tools/ENGINE_MANIFEST.json`, so the upstream URL can replace a relative
    path there) and a `precedent.json` key that records "no individual
    source, on purpose". **Disposition:** wait (2026-09-14, the very deep
    check)

## How It Closes

Not open until: a consumer-aware remedy renderer (the engine knows its `kind` from `tools/ENGINE_MANIFEST.json`, so the upstream URL can replace a relative path there) and a `precedent.json` key that records "no individual source, on purpose".

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
