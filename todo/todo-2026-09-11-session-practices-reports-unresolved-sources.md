---
slug:              todo-2026-09-11-session-practices-reports-unresolved-sources
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a fresh session to reproduce the ordering, since the failure only exists at session start."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            null
---
## What

- <a id="session-practices-reports-unresolved-sources"></a>**`.precedent/SESSION_PRACTICES.md` can report a source as unresolved that
    resolved fine minutes later — and a session reading it believes those
    practices are absent.** Measured 2026-09-11: the session-start hook
    reported all three team sources as *"has no practices/ directory"* and
    wrote that into the generated file's "Sources that did not resolve"
    section, while `precedent_resolve.py`, run by hand in the same session,
    resolved all three and put their practices in force. The clones were on
    disk with `practices/` present. So the file was written before the
    clones finished, not because anything was wrong with them.

    **This is the file's most dangerous possible failure**, because it is
    the one a session trusts to know what binds it: it says in as many
    words that a non-resolving source is *unknown, not "that source has no
    rules"* — and then a session reads the list and works as if the rules
    were absent. That is the same cost as
    [the "no individual source resolved" gotcha](../AGENTS.md), arriving
    through a file that looks authoritative.

    The fix is probably ordering (write the file after the clone step, or
    regenerate it once the clones land) but **nothing here is diagnosed** —
    the hook ran once, before the first turn, and cannot be re-run in the
    same container to watch it happen.
    **Blocked-on:** a fresh session to reproduce the ordering, since the
    failure only exists at session start.
    **Disposition:** wait
    ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

Not open until: a fresh session to reproduce the ordering, since the failure only exists at session start.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
