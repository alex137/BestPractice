---
slug:              todo-2026-09-16-file-retires-when-on-live-gotchas
kind:              analysis
domain:            content
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-16
closed:            null
---
## What

**Populate `retires_when` on the live gotchas.** Declared in the schema
from the start ([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](../spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 2, "`retires_when` Is Declared Now, Built Later") but deliberately
not populated by the migration itself — Part 4.1 step 9 names this as
the new system's own first `todo/` item, "a fitting first use, and a
small, well-scoped task rather than something this migration has to
carry." Every one of `gotchas/`'s 44 live entries (44 as migrated
2026-09-16, not the 42 the plan measured on 2026-09-14 — the gotchas
index grew by two in the two days between) currently carries
`retires_when: null`.

Three shapes should cover nearly every case, per the plan:

```
retires_when: "a mechanical check refuses this -- <name the check>"
retires_when: "the harness fixes <specific behavior>; re-test whenever
               the harness changes that behavior"
retires_when: "nothing has hit this since <date> and the mechanism
               that caused it no longer exists"
```

Read each entry's own `## Story` and `## Fix` before writing one — several
already state their own retirement condition in prose (a gotcha whose
Fix section says "verified against the fixed code, a regression check
confirms it" is close to shape 1 already; one whose Story opens "this
mechanism was fixed on <date>" is close to shape 3). Writing `retires_when`
is a rename of what the entry already says, not a new judgment about it,
the same discipline `decision_strength`'s migration used.

## How It Closes

Every `gotchas/gotcha-*.md` with `status: live` carries a non-null
`retires_when`. `tools/very_deep_check.py`'s `_gotcha_retirement_candidates`
(wired 2026-09-16, Part 4.1 step 8) already reads the field once it is set
— running it after this item closes is how the next session finds out
which ones now look met, not part of closing this item itself (Part 5
rules out an auto-closer, and populating the field is a separate act from
judging whether any entry's stated condition now holds).

## Notes

2026-09-16: filed by the session running spec/OPEN_ITEM_AND_GOTCHA_PLAN.md's
Part 4.1 steps 5-10, per step 9's own instruction to file this as the new
system's first item rather than populate it as part of the migration.
