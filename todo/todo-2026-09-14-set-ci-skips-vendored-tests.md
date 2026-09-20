---
slug:              todo-2026-09-14-set-ci-skips-vendored-tests
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "two calls: whether the suite belongs in the `precedent-check` workflow or its own, and what it should do in a set whose checks want a BestPractice clone CI does not have — the same gap that turns real answers into `SKIPPED` unless `PRECEDENT_BESTPRACTICE_CLONE` is set."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="set-ci-skips-vendored-tests"></a>**No practice set's CI runs the
    vendored checks' own test suite, so a red suite sits under a green pull
    request.** Verified 2026-09-14: none of the three workflow templates a set
    is bootstrapped with —
    [doc-lint](../templates/github-actions/doc-lint.yml.template),
    [precedent-check](../templates/github-actions/precedent-check.yml.template),
    [views-drift](../templates/github-actions/views-drift.yml.template) —
    references `tools/checks/tests/run_all.sh`, and the same day a sweep of
    all four private sets' workflows found no reference either.
    The cost is already real: `precedent-team-writing`'s engine-refresh PR
    showed every check green while `run_all.sh` exited 1 with two failures
    (*"fixture bug: this case requires NO engine"*). They reproduce on that
    set's pre-refresh `main`, so they predate the refresh — and the only
    reason anyone knows is that the session ran the suite by hand and wrote it
    into the PR body.
    **Blocked-on** two calls: whether the suite belongs in the
    `precedent-check` workflow or its own, and what it should do in a set
    whose checks want a BestPractice clone CI does not have — the same gap
    that turns real answers into `SKIPPED` unless
    `PRECEDENT_BESTPRACTICE_CLONE` is set.

## How It Closes

Not open until: two calls: whether the suite belongs in the `precedent-check` workflow or its own, and what it should do in a set whose checks want a BestPractice clone CI does not have — the same gap that turns real answers into `SKIPPED` unless `PRECEDENT_BESTPRACTICE_CLONE` is set.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
