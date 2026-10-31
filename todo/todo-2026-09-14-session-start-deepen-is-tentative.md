---
slug:              todo-2026-09-14-session-start-deepen-is-tentative
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan: the approved --deepen=1000 measured no cheaper than the full fetch (2026-10-31 note); which bound, if any"
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
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
2026-10-31, very deep check of 2026-10-30, pass 4 (re-measured, asked of Morgan): a
`--depth=50` clone of `staging` through this container's proxy took 19.6
seconds to `git fetch --unshallow`, and its `.git` grew from 7.7 MB to 33 MB,
against 4 seconds and about 7 MB at roughly 1,300 commits on 2026-09-14;
history is now about 5,560 commits. One measurement, and of `staging` alone:
the hook widens the refspec first, so a real session pays at least this.
The trade the item asked to watch has moved about fivefold. The session's
pick: narrow it to a bounded deepen (`--deepen=1000`, already the hook's
fallback) and leave the full history to the tools that ask for it.

2026-10-31, Morgan approved the pick above ("do your recommendations for
all", **strength: assented**), and the change was **not made**, because
measured it changes nothing. Each a single run through this container's
proxy, starting from a fresh `--depth 1` clone of `staging` (7.0 MB `.git`)
with the refspec widened first, as the hook does:

| What the hook would run | Time | `.git` after | Still shallow? |
|---|---|---|---|
| `git fetch --unshallow` (today) | 26.9 s | 31.4 MB | no |
| `git fetch --deepen=1000` (the approved pick) | 27.0 s | 31.9 MB | no |
| `git fetch --depth=1000` | 25.4 s | 31.6 MB | yes |
| `git fetch --depth=100` | 24.2 s | 25.8 MB | yes |
| `git fetch --deepen=100` | 26.7 s | 31.2 MB | yes |
| `git fetch --deepen=100 origin staging` (one branch) | 10.0 s | 14.9 MB | yes |
| `git fetch --deepen=300 origin staging` (one branch) | 19.6 s | 21.1 MB | yes |

Why the bound does not bound: this history is merge-heavy (about 5,600
commits on `staging`, its first-parent line about 1,700), so 1,000
generations from the tip reach every commit, and the widened refspec
brings all of origin's 95 branches with it -- most of the cost is those
branches, whatever the depth. Only a deepen of the current branch alone
came in well under the full fetch.

**Pick, for Morgan:** deepen the current branch alone by about 100
(about 10 s and 15 MB here, against about 27 s and 31 MB), and leave the
rest of the history to the tools that already deepen when they need it.
Two costs to weigh: whether the three tools this item names still see
enough history at that depth is unmeasured; and `freshness-guard.sh`
deepens a still-shallow clone by 500 more on every check
(`_deepen_if_shallow`), so it would need to deepen only when its counts
cannot be trusted, or the narrowing undoes itself within a session. The
alternative is to keep the full fetch and close this item on the new
figure. Either way the item stays open until he says which.
