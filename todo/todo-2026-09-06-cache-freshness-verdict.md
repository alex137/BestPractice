---
slug:              todo-2026-09-06-cache-freshness-verdict
kind:              decision
domain:            mechanism
severity:          null
status:            dropped
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Considered and declined: caching the freshness guard verdict was not worth the added invalidation complexity, since a failing fetch in this environment is fast (8-382ms measured), not slow."
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-06
---
## What

- <a id="cache-freshness-verdict"></a>~~**Cache the freshness guard's verdict so a blocked state stops
    re-probing.**~~ **Considered and declined 2026-09-06 — the measurements
    are here so nobody re-derives them.** The behavior is real:
    [.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh)'s
    `pre-write` mode writes its once-per-session sentinel only on the
    *success* path, so in any of its five blocking states (fetch failed,
    behind-and-dirty, diverged, fast-forward failed, missing commits from
    base) every subsequent non-`git` tool call re-runs the whole check,
    network probe included, and refuses again with the same answer —
    reproduced with three consecutive blocked calls leaving zero sentinels.
    The proposed fix: replace "sentinel = verified OK" with a cached verdict
    in `$GIT_DIR`, keyed on HEAD sha + dirty flag + branch with a ≈60s max
    age, so a repeat call re-emits the cached refusal in ≈17ms instead of
    probing, while any remedy that moves HEAD or flips the dirty flag
    invalidates it instantly.
    **Why it was declined.** The case rested on an assumption that a failing
    fetch is slow. It is not, in this environment — measured 2026-09-06 in a
    Claude cloud container: a bad local path fails in 8ms, an unroutable IP
    (the genuine network-is-down case) in 53ms, an unresolvable host in
    254ms, and a real host with a nonexistent repo in 382ms. The proxy fails
    fast; there is no multi-second timeout to avoid. So the saving is
    ≈50–400ms per blocked non-`git` call, in states that are rare, and during
    which every `git` command — which is what every remedy the guard names
    actually is — is already exempt and free. A stuck episode of five
    non-`git` calls saves about one second in total, against a change that
    alters the sentinel's meaning, adds two invalidation paths, and could
    easily be misread by a later session as the guard going soft.
    Morgan works only in Claude's cloud sessions, not a local install (as of
    2026-09-06), so the offline case that motivates this most is the least
    likely one to occur.
    **If it is revisited**, two of the five blocking states are *not*
    invalidated by a HEAD + dirty key and would fall back to the timer alone:
    a failed fetch (the remedy is the network returning — nothing local
    changes) and a failed fast-forward caused by an untracked file (untracked
    files are outside the `--untracked-files=no` dirty check). A cached
    refusal must also say *when* it was formed, or it will quote a commit
    count that has since moved. **What would change the verdict:** a stuck
    state observed producing a genuinely slow probe on some network path
    other than this container's proxy, or the guard's blocking states turning
    out to be common rather than rare in practice. Full reasoning and the
    measurement runs:
    [this thread](https://claude.ai/code/session_01NQCKsA4otmeujdrbCGrqR3).

## How It Closes

Dropped -- see the item's own text above for why.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
