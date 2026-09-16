---
slug:              todo-2026-09-07-stem-reminder-at-the-refusal
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
noted:             2026-09-07
closed:            null
---
## What

- <a id="stem-reminder-at-the-refusal"></a>**Consider putting the stem reminder in the allowlist's REFUSAL message
  too.** When the gate refuses `owner/name`, whoever clears it is at the
  keyboard, knows a private repo is being named, and is about to write a
  reason — the cheapest moment to also add its stem. Offered alongside the
  two mechanisms that were built and not selected, so this is a deliberate
  deferral rather than an oversight.

  **Out of scope for now, with the reason:** the built pair already covers
  most of it — clones on this disk get a note every run, and repositories
  the tree names get the deep check's API-backed finding. What is left is
  the narrow case of a repo named in a document but not cloned locally,
  caught at push time rather than on request. Worth doing if that case ever
  actually bites.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
