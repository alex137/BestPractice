---
slug:              todo-2026-09-08-small-calls-vs-brainstorm
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
noted:             2026-09-08
closed:            null
---
## What

- <a id="small-calls-vs-brainstorm"></a>**`small-calls` tells a session to commit during a brainstorm, and
    nothing mechanical stops it.** Opened 2026-09-08 alongside
    `brainstorm-holds-commits`, and
    **corrected the same day** — the first version of this item said the team
    rule "wins on precedence," which is wrong. `PRECEDENCE` is
    `team > repo-local > individual > universal` **by slug**, and these are
    different slugs, so neither overrides the other. Both are simply in
    force, nothing reports a conflict, and `severity: blocking` would not
    change that either — it is a same-slug mechanism too.

    So the conflict is semantic, not mechanical: a session holding both reads
    *"Default to continuing, not asking… make the call and note it"* beside
    *"write nothing to the repository until they say to."* Committing a
    captured open item is exactly the shape `small-calls` calls small —
    cheap, reversible, keeps the work moving — and that reading is what
    produced the incident, twice in one thread.

    **Resolved for now in the universal practice's own text**, which names
    `small-calls` and says the brainstorm state narrows it. Both rules are in
    front of the session, so the one that addresses the other by name is the
    one that wins in the moment, and that needed no access to the private
    team source. **Still worth a clause in `small-calls` as belt-and-braces**
    — an exception naming the brainstorm state, the same way its Rule already
    carves out credentials and production. **Blocked-on:** read-only access
    to `precedent-shared-repo-maintenance` from this session (`cross-source-rollout`).
    Whoever takes it should check the individual set for the same shape.

## How It Closes

`small-calls` carries an exception naming the brainstorm state, the way its Rule already carves out credentials and production, and the individual set has been read for the same shape -- or the clause is declined and the reason recorded here.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-10-06: the retired set names in this item's current-state text (`precedent-team-*`) now read `precedent-shared-*`; dated history keeps the names it had (very deep check of 2026-10-05, pass 4).

2026-10-06: re-triaged; no longer blocked. The only blocker was read access to a private set, which a session now normally has (the private sources arrive at session start, or by `add_repo`). And `small-calls` itself has been universal since 2026-10-05 ([practices/small-calls.md](../practices/small-calls.md)), so the clause is an edit in this repository. It does not mention the brainstorm state yet. The disposition stays `wait`: changing it is the owner's call.
