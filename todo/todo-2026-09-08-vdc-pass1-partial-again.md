---
slug:              todo-2026-09-08-vdc-pass1-partial-again
kind:              manual
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
noted:             2026-09-08
closed:            null
---
## What

- <a id="vdc-pass1-partial-again"></a>**Pass 1 of the very deep check has been PARTIAL two runs
  running, on the same item.** [practices/very-deep-check.md](../practices/very-deep-check.md) puts "a REAL
  consumer repository, brought up to date" at the top of pass 1 and says
  the asking goes first, because the answer may not come back. It has not
  come back twice. The 2026-09-08 run also left three cheaper halves
  unbuilt — the migration fixture, the empty neighbourhood, and the
  cross-repo permissions walk (open since 2026-09-07 as well) — because
  the update fixture it did build produced every defect it had time to fix.

  **Disposition:** wait

  The consumer-repo half genuinely needs Morgan to attach one. The other
  three need nothing but a session's time and should simply be done first
  next run, before the fresh-install fixture that has now come back clean
  twice — those do not wait on anyone and should not be recorded as if
  they did.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
