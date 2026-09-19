---
slug:              todo-2026-09-06-convert-team-set-retired-statuses
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-11
---
## What

- <a id="convert-team-set-retired-statuses"></a>*(was item 34 — two items carried that number until 2026-09-06.)* **Convert
    `precedent-team-repo-maintenance`' two `status: retired` practices to
    `status: deduplicated`.** `bestpractice-sync` (rule in force at
    individual) and `header-caps` (rule in force at universal) are both
    deduplications recorded under the old vocabulary, and neither can meet
    retirement's evidence bar (`in_force_at: none` plus a Story line saying
    nobody wants the rule anywhere) because both rules are fully in force.

    **Correction, same day:** an earlier draft of this item said the set
    would "go red on its next vendored-engine refresh." That was wrong, and
    wrong in the direction that matters — `verify_harness.py` is **not** in
    [`ENGINE_FILES`](../tools/precedent_vendor_engine.py), so
    `check_status_contract` never runs in a practice set at all. The set
    does not go red; it goes **silent**, which is worse. The new engine
    simply starts treating those two records as not in force — correct
    either way — with nothing to say the vocabulary underneath them changed.

    The migration is now mechanical:
    [`tools/precedent_migrate_status.py`](../tools/precedent_migrate_status.py)
    (vendored, so it runs inside the set) reports both, auto-proposes
    `bestpractice-sync` (same slug, active in `precedent-individual`), and
    leaves `header-caps` UNDETERMINED because its successor is renamed —
    `--set header-caps=headline-capitalization`. Run it report-only first.

    **Done — and neither half ended up needing the migration.** `header-caps`
    was converted to `status: deduplicated` with
    `in_force_at: headline-capitalization` at some point before 2026-09-11,
    which is what this item asked for. `bestpractice-sync` went the other
    way: it was still `active` in the team set (the 2026-09-09 subject split
    had reversed which copy was the live one, so this item's parenthetical
    "rule in force at individual" had gone stale), and on 2026-09-11 Morgan
    retired the rule outright. It is now `status: retired` with
    `in_force_at: none` and a Story saying why, in both sets — which is the
    one state the old record was never entitled to claim and is now simply
    true.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
