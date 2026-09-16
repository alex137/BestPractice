---
slug:              todo-2026-09-14-github-budget-into-the-source-sets
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing, deliberately — refreshing four private repositories from here would open four pull requests for a file none of them can use yet, which is the opposite of what [cross-source-rollout](../practices/cross-source-rollout.md) is for. Close it when a refresh has landed in each set, or when one of the"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="github-budget-into-the-source-sets"></a>**The four practice sets do not have
    `github_budget.py` yet, and will not until their next engine refresh.**
    Added 2026-09-14 with
    [github-api-budget](../practices/github-api-budget.md):
    [tools/github_budget.py](../tools/github_budget.py) is now in
    `ENGINE_FILES`, so every set picks it up the next time
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
    runs there — the `Update Vendors` runbook, or each set's own
    on-demand engine-refresh workflow. Until then the vendored
    `precedent_check.py` in those sets carries the `github-api-budget`
    check and reports NOT APPLICABLE, correctly: a set declares no
    `tools/github_api_budgets.json` and nothing in one calls the API, so
    there is no spend to judge. Nothing is broken there; this item exists
    so nobody re-derives that from a NOT APPLICABLE row.

    **Blocked on:** nothing, deliberately — refreshing four private
    repositories from here would open four pull requests for a file none
    of them can use yet, which is the opposite of what
    [cross-source-rollout](../practices/cross-source-rollout.md) is for.
    Close it when a refresh has landed in each set, or when one of them
    grows its own API-calling tool and needs the module sooner.

    **Disposition:** wait (2026-09-14, the session that added the practice)

## How It Closes

Not open until: nothing, deliberately — refreshing four private repositories from here would open four pull requests for a file none of them can use yet, which is the opposite of what [cross-source-rollout](../practices/cross-source-rollout.md) is for. Close it when a refresh has landed in each set, or when one of the

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
