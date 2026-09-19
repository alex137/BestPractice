---
slug:              todo-2026-09-14-agents-md-over-its-ceiling
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""Let's do a reduction pass as you recommend" -- Morgan picked the reduction pass over raising the ceiling."
decision_strength: decided
waiting_on:        null
noted:             2026-09-14
closed:            2026-09-14
---
## What

- <a id="agents-md-over-its-ceiling"></a>**AGENTS.md is over its declared ceiling, and it is a decision, not a
   bug.** Measured 2026-09-14 on an untouched checkout of
   `precedent-beta-v01`: 12,019 tokens against the 12,000 in
   [tools/session_load_budgets.json](../tools/session_load_budgets.json), so
   `python3 tools/precedent_check.py --only session-load-budget` is red on
   the branch itself and will be red for every session's deep check until
   somebody acts. Nothing did this wrong — the catalogue grew (an occasion
   index line, which is generated and cannot be hand-trimmed, plus gotchas
   g37–g39), which is exactly the drift the ceiling exists to surface.
   [session-load-budget](../practices/session-load-budget.md) forbids raising
   the number to clear the red and names the alternative: delete what is
   duplicated, retire what cannot happen any more, split what is still live
   and still long. The registry's own `why` already says the next raise
   should come with a reduction pass rather than another re-measurement.
   **CLOSED 2026-09-14 — Morgan picked the reduction pass** (`strength:
   decided`, from *"Let's do a reduction pass as you recommend"*), and the
   ceiling was never raised. Two passes ran, deliberately separate: the
   session that broke it cut the gotchas preamble, which spent three
   paragraphs restating [environment-gotchas](../practices/environment-gotchas.md)
   that every session already loads in full in the resident block
   (12,026 → 11,917, PR #357); then this one cut the quick index, where 14
   rows had grown into abstracts of the documents they only need to point at
   (11,917 → 11,538). Both cuts were duplication, not content — every fact
   dropped was verified present in the file the row links to, or in this
   file. **462 tokens of headroom now**, which is the real close condition:
   a ceiling met exactly is one the next honest addition breaks, and that is
   precisely how this happened.

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
