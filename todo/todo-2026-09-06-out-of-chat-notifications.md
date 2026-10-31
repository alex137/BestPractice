---
slug:              todo-2026-09-06-out-of-chat-notifications
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
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

- <a id="out-of-chat-notifications"></a>**Out-of-chat change notifications for members.** In-chat catch-up is
   now a convention (the instructions template's session-start
   catch-up), but a member who hasn't opened a session learns nothing.
   Evaluate a GitHub Actions job that emails a plain-language digest of
   merged changes (or leans on GitHub's built-in Watch notifications,
   documented in the members' page) — as of 2026-08, unexplored.

**Disposition:** parked (2026-10-31, Morgan, 2026-10-31 (strength: assented): "do your recommendations for all", on the very deep check's pick to park it)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
