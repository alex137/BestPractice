---
slug:              todo-2026-09-06-github-issues-for-open-items
kind:              analysis
domain:            null
severity:          null
status:            dropped
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Overtaken: open items stay committed files, one per item under todo/ (repo-is-memory), and GitHub Issues are used only where an unattended job needs one (automation-issues)."
decision_strength: assented
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-28
---
## What

- <a id="github-issues-for-open-items"></a>**Evaluate GitHub Issues for open items.** Mirroring or replacing
   TODO-file items with Issues would let shell-less assistants and phone
   users browse, discuss, and close work items natively. Needs a
   convention for keeping Issues and the repo-is-the-memory principle
   consistent (an Issue is not on `main`).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

**Closed 2026-09-28 (dropped).** Overtaken: open items stay committed files, one per item under todo/ (repo-is-memory), and GitHub Issues are used only where an unattended job needs one (automation-issues). Morgan approved the very deep check's pass-4 recommendation to close it, 2026-09-28 ("Make the changes you recommend"); strength: assented.
