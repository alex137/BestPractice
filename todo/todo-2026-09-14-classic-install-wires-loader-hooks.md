---
slug:              todo-2026-09-14-classic-install-wires-loader-hooks
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the previous item — if §0 becomes the default the §1 adapter shrinks to what §1 uses; if not, ship a §1 variant of `settings.json` or make the gate stay quiet under the `process/upstream` layout."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="classic-install-wires-loader-hooks"></a>**A §1 install ends
    every turn with `precedent gate FAIL`, because the Claude Code adapter
    wires two hooks the hook table says are loader-only.** Measured
    2026-09-14 on a by-the-book §1 rehearsal:
    [templates/harness/claude-code/settings.json](../templates/harness/claude-code/settings.json)
    wires `reply-gate.sh` and `precedent-paths.sh` unconditionally, and
    INSTALL.md's table marks both "only with the Precedent loader" without
    saying to delete the entries. `precedent-paths.sh` exits silently; the
    `Stop` hook's gate call finds `process/upstream/tools/precedent_gate.py`
    and prints *gate 'reply' has no practices registered to it* on every
    turn, permanently. **Blocked on:** the previous item — if §0 becomes the
    default the §1 adapter shrinks to what §1 uses; if not, ship a §1
    variant of `settings.json` or make the gate stay quiet under the
    `process/upstream` layout. **Disposition:** wait (2026-09-14, the very
    deep check). *Narrowed the same day*: §0 is the default now, so this
    reaches only a project that chooses §1 by name; the fix is the §1
    variant of `settings.json`, when somebody next installs §1.

## How It Closes

Not open until: the previous item — if §0 becomes the default the §1 adapter shrinks to what §1 uses; if not, ship a §1 variant of `settings.json` or make the gate stay quiet under the `process/upstream` layout.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
