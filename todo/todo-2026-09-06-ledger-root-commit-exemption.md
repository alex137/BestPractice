---
slug:              todo-2026-09-06-ledger-root-commit-exemption
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
closed:            2026-09-06
---
## What

- <a id="ledger-root-commit-exemption"></a>~~**`parallel-artifact-ledger`'s root-commit exemption doesn't cover a    family's own inception commit.**~~ Found 2026-09-05: `_parallel_artifact_ledger`
    in [tools/precedent_check.py](../tools/precedent_check.py) excludes the
    *repository's* root commit (`git rev-list --max-parents=0`) from needing
    a ledger row, but not the commit that first created a given family's
    member directories — [`f2078d6`](https://github.com/alex137/BestPractice/commit/f2078d6ef32731e35d30e279c90d72a55e9b6268)
    (created `templates/harness/{claude-code,codex,gemini-cli}/` from
    scratch, 2026-07-20) went unflagged by every backfill pass until CI on
    an unrelated PR caught it, because scope is `tree` — the check runs
    against the whole repo regardless of what a given diff touches, so any
    unfixed gap fails every PR's CI, not just one. Backfilled as a row in
    [templates/harness/LEDGER.md](../templates/harness/LEDGER.md) rather than
    fixed then. **Done (2026-09-06)** — the exemption is per-member-directory
    now: each family member's own first commit is exempt, the same reasoning
    already applied repo-wide, so a future family's inception commit needs no
    manual backfill. `f2078d6`'s hand-written row stays (a real record of a
    real decision, and deleting it would only make the ledger less complete);
    the harness case that proves the check fires gained a fourth stated case
    for the exemption, and a planted removal of a genuine later change still
    fails, so the exemption did not widen into a hole.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
