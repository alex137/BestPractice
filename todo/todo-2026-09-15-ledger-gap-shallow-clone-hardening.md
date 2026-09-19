---
slug:              todo-2026-09-15-ledger-gap-shallow-clone-hardening
kind:              verify
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
noted:             2026-09-15
closed:            2026-09-15
---
## What

- <a id="ledger-gap-shallow-clone-hardening"></a>**`parallel-artifact-ledger`
    is red on `precedent-beta-v01` itself, pre-existing.**
    `python3 tools/precedent_check.py --only parallel-artifact-ledger` fails:
    `templates/harness/LEDGER.md` has no row for `4b19b04` ("Harden the
    shallow-clone self-heal", 2026-09-15), which touched
    `templates/harness/claude-code`. Found while running the deep check for
    an unrelated change; not this session's commit and not fixed here —
    writing the row needs the per-member transfer verdict for that specific
    commit, which this session did not investigate.
    **CLOSED 2026-09-15 — backfilled by a concurrent commit.**
    [`7c674fa`](https://github.com/alex137/BestPractice/commit/7c674fa)
    landed a `templates/harness/LEDGER.md` row for `4b19b04` while this
    session's own PR was in flight; `precedent_check.py --only
    parallel-artifact-ledger` passes clean on `precedent-beta-v01`'s current
    tip.

## How It Closes

Already closed 2026-09-15 -- see the item's own text above for what
finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../`.
