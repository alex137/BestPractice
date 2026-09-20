---
slug:              todo-2026-09-14-session-start-deepen-is-tentative
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
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

- <a id="session-start-deepen-is-tentative"></a>**The session-start deepen is
    TENTATIVE — revisit whether every session should pay it.** Since
    2026-09-14 [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh)
    fetches the rest of a shallow clone's history before the first turn, so no
    session here reads a truncated one. What it buys: three tools that report
    success while checking almost nothing on a short history
    ([behavioral_replay.py](../tools/behavioral_replay.py) with nothing to replay,
    [doc_lint.py](../tools/doc_lint.py) silently narrowing to uncommitted files,
    [precedent_check.py](../tools/precedent_check.py)'s `scope: tree` checks
    reading an empty `git log` as `0 violated`). What it costs: **4 seconds and
    about 7 MB on every session**, measured against this remote through this
    container's proxy — 2.7 MB of history before, 9.5 MB after — paid whether
    or not that session ever reads history, which most do not.

    **Morgan approved it weakly and asked for this item in the same breath**
    (`strength: assented`, 2026-09-14): *"Okay let's do it, go merge. BUT note
    this in the Todo as an issue to revisit in the future, it's tentative,
    'weak'."* So the thing to revisit is the trade, not the implementation.

    Three things would change the answer, and none of them is knowable yet
    from one measurement: whether **4 seconds is noticeable** in practice at
    the start of a session; whether the repo's history **grows** enough that
    the figure stops being 4 seconds (it is ≈1,300 commits of mostly text
    today); and whether the three tools above get fixed to **say "could not
    check"** instead of degrading, which would remove most of the reason for
    the deepen. The narrower alternative, if it stops paying: deepen a bounded
    slice rather than everything, or deepen only when a tool that needs history
    is about to run.

    **Close it** by re-measuring the cost on a fresh container, deciding
    keep / narrow / drop with that number in hand, and recording which — not
    by the deepen having worked, which says nothing about whether it was worth
    it.

    **Disposition:** ask (2026-09-14, Morgan — he asked for it to be revisited)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
