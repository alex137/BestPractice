---
slug:              todo-2026-09-06-roll-out-four-pass-restructure
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "an explicit instruction, not availability — the source was attached in the session that made this change, whose ask was scoped to BestPractice's `precedent-beta-v01` alone. Any session with `precedent-team-repo-maintenance` attached and a mandate to touch it can close this. **Narrowed 2026-09-06:** "
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- <a id="roll-out-four-pass-restructure"></a>**Roll the very deep check's four-pass restructure out to
    `precedent-team-repo-maintenance`' own `deep-check`.**
    [practices/very-deep-check.md](../practices/very-deep-check.md) was
    restructured 2026-09-06 from one drift checklist into four ordered
    passes — adopter installs, whether the mechanisms tell the truth, the
    coherence read, then catalogue and housekeeping — with the run made
    resumable via [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md). The
    team set's `deep-check` is the same inherited list one generation back,
    so it now states an older, narrower version of the same rule: it should
    either adopt the passes, or point at this practice via `overrides:` and
    stop restating it. That call was already open (item 17 above records it
    as the team's own to make); this restructure is what makes leaving it
    open cost something. **Blocked on:** an explicit instruction, not
    availability — the source was attached in the session that made this
    change, whose ask was scoped to BestPractice's `precedent-beta-v01`
    alone. Any session with `precedent-team-repo-maintenance` attached and a
    mandate to touch it can close this.
    **Narrowed 2026-09-06:** the `overrides:` half is already ruled out —
    [practices/very-deep-check.md](../practices/very-deep-check.md)'s Story
    records Morgan's ruling that the team's `deep-check` and this practice
    are unrelated rules, so there is nothing to override, and the team's
    routine per-commit check keeps happening. The same date,
    [practices/two-check-levels.md](../practices/two-check-levels.md) drew the
    general line this rests on: what gates a commit, push or merge is one of
    the two named levels, while a rare audit a person asks for by name is a
    separate mechanism. So the open call is only whether the team's
    `deep-check` should adopt anything from the four passes — not whether it
    should be replaced by them.

## How It Closes

Not open until: an explicit instruction, not availability — the source was attached in the session that made this change, whose ask was scoped to BestPractice's `precedent-beta-v01` alone. Any session with `precedent-team-repo-maintenance` attached and a mandate to touch it can close this. **Narrowed 2026-09-06:** 

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
