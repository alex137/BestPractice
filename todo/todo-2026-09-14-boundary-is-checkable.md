---
slug:              todo-2026-09-14-boundary-is-checkable
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the throwaway repository, a token with administration read, and the assumptions."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="boundary-is-checkable"></a>**Nothing checks that a document
    project's boundary is actually on.** A forgotten instantiation step 6
    (branch protection) leaves Write as unrestricted write, silently, while
    every document goes on describing a boundary. Finding 5 of the
    2026-09-14 review. The check is the shape of
    [tools/precedent_source_names.py](../tools/precedent_source_names.py): ask
    the GitHub API whether the base branch requires a pull request and a
    code-owner review, and print `UNVERIFIED` rather than a pass when it
    cannot.
    **BUILT 2026-09-14, the same day**:
    [tools/precedent_boundary_check.py](../tools/precedent_boundary_check.py),
    PASS / FAIL / UNVERIFIED, the API stubbed in
    [tools/verify_harness.py](../tools/verify_harness.py) so every verdict
    asserts its own words, and a 403 naming a plan upgrade read as FAIL
    rather than UNVERIFIED — it is an answer to assumption 2. Run live here it
    says UNVERIFIED: the session's token cannot read protection settings.
    **What is not done**: nobody has run it against a repository where
    protection is on, so the 200 branch is tested only against the response
    shape the session remembers GitHub sending. **Blocked on:** the throwaway
    repository, a token with administration read, and the assumptions.
    **Disposition:** wait (2026-09-14, the review)

## How It Closes

Not open until: the throwaway repository, a token with administration read, and the assumptions.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
