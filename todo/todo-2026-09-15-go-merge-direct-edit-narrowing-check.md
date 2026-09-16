---
slug:              todo-2026-09-15-go-merge-direct-edit-narrowing-check
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
noted:             2026-09-15
closed:            null
---
## What

- <a id="go-merge-direct-edit-narrowing-check"></a>**A mechanical check
    could narrow the trivial/substantial judgment `Go merge` now makes, and
    it is not built.** [go-merge](../practices/go-merge.md) forks on a
    session's own read of whether a pending change is trivial
    (direct-push-eligible) or substantial (needs the full PR chain) — a
    judgment call, the same shape as the phrase-recognition it has always
    made. One slice of that judgment is mechanical and isn't wired up:
    whether a push straight to a repo's own working branch, with no open
    pull request, touches only content that repo's own convention already
    allows direct edits to. For BestPractice that is
    [this repo's own rule](../AGENTS.md#working-in-this-repo) — README,
    practice wording, engine code, never an incoming abstracted lesson — and
    a check could fail a direct push that lands outside that set. Not built
    here; out of scope for drafting the rule itself.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
