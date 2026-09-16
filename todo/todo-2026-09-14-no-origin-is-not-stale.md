---
slug:              todo-2026-09-14-no-origin-is-not-stale
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
noted:             2026-09-14
closed:            null
---
## What

- <a id="no-origin-is-not-stale"></a>**A repository with no `origin` at
    all reads as a stale checkout and as a repo with nothing changed, and
    both readings are wrong.** Measured 2026-09-14 on a freshly `git init`ed
    §0 install: the freshness guard's `pre-write` refused the session's
    first write (*could not fetch origin/…*), and `doc_lint.py`'s default
    scope reported `0 file(s) checked` on a tree with three dead links,
    because both hard-code `origin/<branch>` as the thing to compare
    against. An unreachable origin should block, deliberately (gotcha
    g21); an origin that was never configured cannot be stale relative to
    anything, and `git remote get-url origin` tells the two apart in one
    call. The install documents now say to lint the instantiated files by
    name and to give the repo an origin first (INSTALL.md §0 step 8, §1
    step 7), which is a workaround written as an instruction. **Blocked
    on:** a change to both copies of the guard plus the harness-adapter
    ledger, and to `doc_lint.py`'s `default_branch()` fallback — small, but
    it touches the hook every session runs, so it wants its own change with
    its own fixtures rather than a line in a documentation sweep.
    **Disposition:** wait (2026-09-14, the very deep check)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
