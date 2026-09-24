---
slug:              todo-2026-09-11-source-load-ceilings
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="source-load-ceilings"></a>**Declare session-load ceilings in the attached practice-set sources, and
   measure the real total a session pays.**
   [session-load-budget](../practices/session-load-budget.md) landed 2026-09-11
   with a registry
   ([tools/session_load_budgets.json](../tools/session_load_budgets.json)) and a
   check that covers **this** repo's surfaces only. Each attached source
   carries its own `AGENTS.md` — measured the same day: 943, 956 and 963
   tokens for the three team sets — and none declares a ceiling, so nothing
   there ratchets. [tools/very_deep_check.py](../tools/very_deep_check.py)'s
   SESSION LOAD section now sums every repo in force, which is how the real
   figure gets read; what is missing is a per-source registry and the check
   running there.

   **blocked-on:** each source's vendored engine is behind
   `precedent-beta-v01` (all four were, at this session's start), so the check
   does not exist in those checkouts yet — and landing a file in any of them
   is a merge under that repository's own rules, not this one's. Do it in the
   session that refreshes their engines.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-09-22: **the second half — "the check running there" — is done, and the
first half is not.**
[tools/very_deep_check.py](../tools/very_deep_check.py)'s SESSION LOAD pass
now reads each measured repo's OWN `tools/session_load_budgets.json` and
reports any surface over the ceiling declared there, and
[tools/precedent_check.py](../tools/precedent_check.py)'s
`session-load-budget` check binds wherever that registry exists rather than
only where the practice file does (`check()`'s new `binds_when`). So a source
that declares a ceiling is now measured against it from a BestPractice
checkout, with nothing to refresh in that source first.

What is still open is the first half, unchanged: **a source that declares no
ceiling is still measured against nothing.** `precedent-individual` has a
registry; the three team sets did not when this item was written. Neither
mechanism can invent a number, and neither tries — a repo without a registry
is reported as untested, not as clean. The blocked-on above is now narrower
too: landing a registry in each source is still that repository's own merge,
but the CHECK no longer has to reach those checkouts for the ceiling to be
tested.
