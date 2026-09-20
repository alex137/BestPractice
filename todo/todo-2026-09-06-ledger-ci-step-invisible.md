---
slug:              todo-2026-09-06-ledger-ci-step-invisible
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

- <a id="ledger-ci-step-invisible"></a>~~**Root-cause why `parallel-artifact-ledger`'s own CI step never shows    its diagnostic output — a GitHub Actions log-capture anomaly, currently
    working around it by making the check advisory-only.**~~ **Done
    (2026-09-06)** — there was no log-capture anomaly and no false positive.
    [verify_harness.py](../tools/verify_harness.py) (CI step 5) invoked a
    vendored [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
    `refresh <ROOT> --force`, and `refresh()` then ran `git checkout
    precedent-beta-v01` plus `git pull` in the clone it was handed — which in
    CI is the job's own workspace. Step 5 therefore moved the workspace onto
    the base branch, and [precedent_check.py](../tools/precedent_check.py) (step
    6) ran the *base* branch's tree, where
    the [harness adapter ledger](../templates/harness/LEDGER.md) genuinely has
    no `f2078d6` row.
    Every other symptom follows from the same substitution: the summary line
    CI printed was the base branch's own pre-advisory format, and the
    diagnostic prints never appeared because by step 6 the file was no longer
    the file they had been added to. `git status` stays clean throughout — a
    branch checkout leaves no dirty file to notice — which is why four rounds
    of content verification all came back correct while the workspace stood
    on a different commit.

    Reproduced deterministically: run
    [verify_harness.py](../tools/verify_harness.py) and then
    [precedent_check.py](../tools/precedent_check.py) in one checkout and the
    second reports the violation; run
    [precedent_check.py](../tools/precedent_check.py) alone on the same commit
    and it is clean. Fixed upstream in
    [`25546bc`](https://github.com/alex137/BestPractice/commit/25546bc) —
    `refresh()` materializes blobs with `git show` and never checks the clone
    out, with a regression case that fails against the pre-fix engine — and
    here by vendoring from a throwaway clone instead of `str(ROOT)`.
    `advisory=True` is off; the check is enforcing again. Full account:
    [PR #110, comment](https://github.com/alex137/BestPractice/pull/110#issuecomment-5556343855).

    **The scope note from 2026-09-05 was right, and still applies.**
    `precedent-beta-v01`'s
    [deep-check.yml](../.github/workflows/deep-check.yml) has no `fetch-depth:
    0` (only this PR's branch does), so its checkout stays shallow (depth 1),
    `git log --no-merges -- <member-dir>` finds nothing to flag, and this
    check falsely, silently passes there — the "scope: 'tree' check... false
    pass on an under-fetched clone" gotcha in [AGENTS.md](../AGENTS.md),
    manifesting repo-wide via the workflow's default rather than a local
    clone's. When this PR merges, `fetch-depth: 0` lands on
    `precedent-beta-v01` and the check starts really running there — which is
    why [`dfe504d`](https://github.com/alex137/BestPractice/commit/dfe504d)'s
    ledger row has to land in the same merge, as it does.

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
