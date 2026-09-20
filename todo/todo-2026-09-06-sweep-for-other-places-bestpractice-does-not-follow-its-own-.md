---
slug:              todo-2026-09-06-sweep-for-other-places-bestpractice-does-not-follow-its-own-
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but its size and the per-step judgment call about which steps apply to the publisher — deliberately not folded into the thread that found the first instance, which would have meant deciding all of them in passing."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- **Sweep for other places BestPractice does not follow its own install
    instructions.** Item 27's root cause was not the missing hook, it was
    that every existing check builds a *fixture* consumer and asserts
    things about it — nothing asserted the publisher does what it
    publishes, so an install step this repo skipped stayed invisible until
    someone went looking for a rule that never loaded. One instance is now
    checked ([tools/verify_harness.py](../tools/verify_harness.py)'s
    self-consumer cases). The sweep is the rest: read
    [INSTALL.md](../INSTALL.md) and
    [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md) step by
    step against this repo's actual tree, decide per step whether it
    applies to the upstream at all (several genuinely do not — there is no
    `process/upstream/` here by design), and add a case for each one that
    does. **Blocked on:** nothing but its size and the per-step judgment
    call about which steps apply to the publisher — deliberately not
    folded into the thread that found the first instance, which would have
    meant deciding all of them in passing.

## How It Closes

Not open until: nothing but its size and the per-step judgment call about which steps apply to the publisher — deliberately not folded into the thread that found the first instance, which would have meant deciding all of them in passing.

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
