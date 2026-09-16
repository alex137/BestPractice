---
slug:              todo-2026-09-11-source-sets-vendor-the-broken-clause-matcher
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="source-sets-vendor-the-broken-clause-matcher"></a>**All four
    practice-set sources vendor the pre-fix `Source:` clause matcher.**
    `precedent_check.py` is in `ENGINE_FILES`, so `precedent-individual`,
    `precedent-team-repo-maintenance`, `precedent-team-writing` and
    `precedent-team-working-style` each carry their own copy, and each will
    keep rejecting a hyphenated or extension-carrying `Source:` path until it
    is refreshed. **No impact today, which is the only reason this is an item
    rather than the work:** every one of their generated headers names
    `practices/`, which both the old and the new matcher read identically. It
    bites the first time any of those sets writes a clause naming a real file.
    The fix in each is the same one command item 61 already established:
    `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`,
    then regenerate views and open a pull request there.
    **blocked-on: no push access to the source repositories from a session
    rooted here** — they are under a different owner, and
    [cross-source-rollout](../practices/cross-source-rollout.md)'s "roll it out
    now, it is attached" does not reach them because attachment here is read
    only. Re-measured 2026-09-11 rather than taken from item 61's record:
    `git push --dry-run` into one of the clones returns
    `access denied by the git proxy ... not in this session's authorized
    repository set` and HTTP 403. The clones are also behind their own
    `origin`, so a commit made on top of one here would be built on a stale
    tree.
    **Disposition:** wait (2026-09-11 — no session has set this to `ask`)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
