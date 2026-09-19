---
slug:              todo-2026-09-08-park-it-to-individual-set
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""we should have our own commands we use for people who live in our universe." -- Morgan chose universal over the individual set the item proposed."
decision_strength: decided
waiting_on:        null
noted:             2026-09-08
closed:            2026-09-08
---
## What

- <a id="park-it-to-individual-set"></a>**Move `park-it` from this repo's local source to Morgan's individual
  set.** [local/practices/park-it.md](../local/practices/park-it.md) records his standing phrase "Park
  it" — one person's preference, which by
  [layered-practice-packs](../practices/layered-practice-packs.md) belongs at the individual level beside
  `go-merge`, not in a repo-local source that binds everyone working here.
  It is a level too low on purpose and says so in its own text.

  **Closed 2026-09-08 — resolved UPWARD instead, and the item's premise was
  wrong.** It assumed the only two homes were repo-local (too low) and the
  individual set (correct). Morgan chose a third: universal, on the grounds
  that these are the project's own commands rather than one person's habits
  — *"we should have our own commands we use for people who live in our
  universe."* `park-it` now lives at
  [practices/park-it.md](../practices/park-it.md), the repo-local copy is
  `deduplicated` pointing at it, and the cross-owner `add_repo` blocker this
  item was waiting on turned out not to matter, because universal is
  reachable from here.

  **Disposition:** parked (2026-09-08, Morgan)

  **What was actually done**, following
  [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md): landed at universal,
  deduplicated at the source rather than deleted, and
  [AGENTS.md](../AGENTS.md)'s "Park it" paragraph repointed.
  `local/tools/checks/check_park_it.py` stays repo-local by design — it
  asserts that this repository's own `AGENTS.md` still spells the phrase
  out, which is a property of this repo, not of the rule.

## How It Closes

Already closed 2026-09-08 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
