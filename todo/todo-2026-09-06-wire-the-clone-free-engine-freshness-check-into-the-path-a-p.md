---
slug:              todo-2026-09-06-wire-the-clone-free-engine-freshness-check-into-the-path-a-p
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "that hook lives in each private source repo (`precedent-individual/bootstrap/session-start.sh`), not here, and `templates/practice-set-*/` ships no equivalent for a new adopter to inherit. Doing it properly means generalizing that hook into the two templates first, so the fix reaches every set rathe"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- **Wire the clone-free engine-freshness check into the path a person's own
  session actually takes.** `python3 tools/precedent_vendor_engine.py fresh`
  already answers "is this vendored engine behind upstream?" with a single
  `git ls-remote` and no clone — it has since the vendoring mechanism
  landed, and it works: run in a stale set on 2026-09-06 it named the exact
  commit gap. **Nothing calls it.** The only mentions anywhere are in the
  tool's own docstring, which is why two sets could sit two hundred commits
  behind with nobody told. Three channels now exist that did not
  (2026-09-06): the scheduled workflow every source template ships, the
  bootstrap warning when the seeding checkout is itself behind, and
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  run from a session working here. All three are periodic or incidental.
  The channel that would catch it *every* time is the source set's own
  `bootstrap/session-start.sh` — the hook that already runs in every
  consuming project to clone or update the set — calling `fresh` right after
  it updates the clone, where a person is present to read the notice.
  **Blocked on:** that hook lives in each private source repo
  (`precedent-individual/bootstrap/session-start.sh`), not here, and
  `templates/practice-set-*/` ships no equivalent for a new adopter to
  inherit. Doing it properly means generalizing that hook into the two
  templates first, so the fix reaches every set rather than only the two
  that already exist.

## How It Closes

Not open until: that hook lives in each private source repo (`precedent-individual/bootstrap/session-start.sh`), not here, and `templates/practice-set-*/` ships no equivalent for a new adopter to inherit. Doing it properly means generalizing that hook into the two templates first, so the fix reaches every set rathe

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
