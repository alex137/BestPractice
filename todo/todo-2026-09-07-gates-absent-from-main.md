---
slug:              todo-2026-09-07-gates-absent-from-main
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- <a id="gates-absent-from-main"></a>**Put the leak gate on `main`; the deep
    check cannot go there until the merge-back.** **Deferred by Morgan
    2026-09-07 — worth doing, not now.** `main` carries only
    [.github/workflows/docs.yml](../.github/workflows/docs.yml), so the official
    branch — the one a visitor lands on and every installer reads — is guarded
    by the markdown lint alone. Neither other gate has ever existed there:
    both were built on `precedent-beta-v01` (leak gate 2026-08-31, deep check
    2026-09-03), and the branches have diverged, with `main` 269 commits
    behind. Verified 2026-09-07 by listing `.github/workflows/` on
    `origin/main`.

    **The two halves are not the same job, which is what turned this from a
    question into a task.** The deep check *cannot* be ported: `main` has no
    [tools/verify_harness.py](../tools/verify_harness.py) and no
    [tools/precedent_check.py](../tools/precedent_check.py), so copying the
    workflow there would install a check that fails on its first run and every
    run after it. Porting those tools with it is not the fix either — they
    exercise the practice engine `main` does not have, against a `practices/`
    directory it does not have. That half waits for the merge-back as a matter
    of fact, not preference. The leak gate is the opposite:
    [tools/leak_gate.py](../tools/leak_gate.py) is self-contained, is not among
    the files [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
    copies downstream, and `main`'s tree **already passes it** — 59 units,
    exit 0, checked 2026-09-07 from inside a worktree of `origin/main`. (From
    *inside*: `ROOT` there resolves through `__file__`, so running the script
    by absolute path from another checkout silently scans the script's own
    repo and reports a confident, wrong pass — 799 units, this branch's
    figure. The next person auditing another branch will reach for exactly
    that command.) The private vocabulary half did not run, as always without
    the blocklist.

    **What it takes when it is done:** a small pull request to `main` carrying
    [tools/leak_gate.py](../tools/leak_gate.py),
    [tools/leak-blocklist.default.txt](../tools/leak-blocklist.default.txt) and
    [.github/workflows/leak-gate.yml](../.github/workflows/leak-gate.yml) as they
    stand on this branch, with `pull_request:` already dropped (d11394c) so it
    does not arrive carrying the double-run this branch just removed.

    **Why deferring is defensible, stated so the deferral can be re-judged
    rather than re-argued:** nothing has pushed to `main` since 2026-09-03 and
    its tree is clean today, so the exposure is a branch nobody writes to.
    **What would make it urgent:** any push to `main` before the merge-back —
    at which point the gate is missing exactly when it is needed, because the
    scanner's whole premise is that on a public repo a push is a publication
    with no grace period. **What closes it for free:** the merge-back landing
    first, which brings both gates to `main` in one move.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
