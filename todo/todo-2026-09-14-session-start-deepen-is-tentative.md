---
slug:              todo-2026-09-14-session-start-deepen-is-tentative
kind:              analysis
domain:            null
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Narrow: session start deepens the branch checked out and the landing branch by 100 generations instead of fetching the whole history; freshness-guard.sh deepens only when its counts cannot be trusted or that deepen failed (2026-10-31)."
decision_strength: assented
waiting_on:        null
noted:             2026-09-14
closed:            2026-10-31
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

The cost re-measured on a fresh clone, and keep / narrow / drop decided with
that number in hand and recorded here (stated in `## What`). Met
2026-10-31: narrowed, below.

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

2026-10-31, closed: **narrowed**, on Morgan's go-ahead to decide it ("use
your judgment, and act", **strength: assented**). Every figure is from this
container through its proxy, starting from a fresh `--depth 1` clone of
origin (its default branch, `main`; 7.1 MB `.git`) with the refspec widened
first, as the hook does.

What session start now runs, against what it ran:

| | Time | `.git` after | Commits held |
|---|---|---|---|
| `git fetch --unshallow` (until today) | 22.9 s, 69.8 s, 23.4 s (three runs) | 33 MB | all, about 5,600, and about 100 branches |
| `git fetch --deepen=100 origin main staging` (now) | 13.0 s, 10.7 s, 11.2 s | 15 MB | about 1,130 |
| `git fetch --deepen=300 origin main staging` | 20.4 s | 23 MB | about 3,270 |

Whether each history-reading tool still gives the right answer on the
100-generation stretch, compared with the full clone at the same HEAD, for
`main` as cloned and for a working branch cut from `staging` with one
commit:

| Tool | Full clone | Stretch of 100 |
|---|---|---|
| [doc_lint.py](../tools/doc_lint.py) changed-files scope (merge base, file list) | same base, same files | same |
| [precedent_check.py](../tools/precedent_check.py) base and change scope | `origin/staging`, same merge base, same count ahead | same |
| [precedent_check.py](../tools/precedent_check.py) `--full-sweep` | 105 passed, 2 violated (both the probe commit's) | byte-identical output |
| [behavioral_replay.py](../tools/behavioral_replay.py) | 142 commits replayed, 0 disagreements | same |
| the reply gate's unlanded-work lines | one line | same |
| freshness guard's verdicts (stale base, behind count) | `main` missing 2 from `staging` | same; a 12-day-old branch: missing 579, the true count |
| [precedent_branches.py](../tools/precedent_branches.py) ancestry | not run (its paths push); `_reach_merge_base` deepens by 300 then 3,000 itself, and `main`/`staging` share a merge base inside the stretch | |

The bare [precedent_check.py](../tools/precedent_check.py) picks a different rotation slice on the
stretch, because the slice is keyed on `git rev-list --count HEAD`; that
moves which checks run, not their answers.

Two things the narrowing needed, and one cost it moves:

- **`freshness-guard.sh` undid it at once.** Its deepen of 500 on every
  shallow clone took the narrowed clone from 16 to 36 MB in 24.9 s at the
  first check (11.5 s for a branch origin has not seen). It now deepens only
  when the two tips do not contain one another (the only case a truncated
  graph can get wrong, g37's), or when session start's failure marker is
  there, in which case it retries session start's deepen. Measured end to
  end with the new hook and guard: `main` 10.7 s + 2.6 s, a new branch
  11.7 s + 3.3 s, a 12-day-old pushed branch 12.7 s + 2.5 s, and nothing
  grows at the next prompt (the guard alone took 3.1 s on a full clone).
- **The guard's base fetch could shorten history.** It ran `--depth=200` on
  any shallow clone, and `--depth` on a shallow clone that already holds
  more cuts it back: `--depth=100` on a clone holding 3,263 commits of
  `staging` left 1,059 reachable. It now fetches a base it already has
  plainly (0.7 s, 2 new commits, nothing shortened) and deepens a base it
  never fetched by 100. Latent until now, because the clone was rarely
  shallow.
- **The push check still unshallows before it checks**, so a session that
  pushes pays the rest of the history at its first push: 18.9 s after the
  narrow deepen (15.3 s for `main` and `staging` alone). Such a session pays
  about the same in total as before, a few seconds more, later; a session
  that never pushes saves about 11 s, and every session's first reply comes
  that much sooner. Teaching the push check to accept a deep-enough clone is
  a separate decision (it was made "never on a shallow clone" on
  2026-09-25), not taken here.

Planted test: `check_session_deepen_stays_narrow` in
[tools/verify_harness.py](../tools/verify_harness.py) (a stretch at start,
left narrow when provable, still deepened when diverged, never shortened,
retried on the marker); against the old guard it fails on the first two,
and against the old base fetch on the fourth. Not changed:
[tools/bootstrap.sh](../tools/bootstrap.sh) and its template, which already
deepen only the current branch (`--depth=1000`) in consuming repositories.
