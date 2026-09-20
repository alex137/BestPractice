---
slug:              todo-2026-09-08-upstream-notice-silent-when-rooted-above
kind:              manual
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
noted:             2026-09-08
closed:            null
---
## What

- <a id="upstream-notice-silent-when-rooted-above"></a>**The upstream-carry
    notice is silent in exactly the layout this project requires, and nothing
    reports its absence.**
    [tools/precedent_upstream_check.py](../tools/precedent_upstream_check.py)
    (landed 2026-09-08) says at session start whether Alex has moved `main`
    since the last carry. It rides
    [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh), so it
    does not run when the harness roots the session one directory ABOVE this
    repo — which is what happens whenever the sibling clones a team source
    needs are laid out alongside it, and is the gotcha that already cost a
    whole session's replies on 2026-09-08.

    **The failure is silent in the way that matters: no notice and "nothing
    changed" render identically.** A session in that layout reads no line,
    concludes `main` has not moved, and is wrong exactly when it counts.
    `python3 tools/precedent_upstream_check.py` by hand is the fallback, and
    a fallback nobody knows to reach for is not one.

    **Queued rather than done because it changes a different tool's
    contract.** [tools/precedent_session_check.py](../tools/precedent_session_check.py)
    reports *guarantees a SessionStart hook established*, tested by their
    effect; "you were told whether upstream moved" is not a state a later
    process can observe, so it does not fit that shape without deciding what
    that tool is for. Its `--apply` path already re-runs `session-start.sh`
    and therefore already prints the notice — what is missing is the
    REPORTING line that tells a session the notice never arrived.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
