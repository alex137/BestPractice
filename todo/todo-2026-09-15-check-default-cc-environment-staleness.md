---
slug:              todo-2026-09-15-check-default-cc-environment-staleness
kind:              verify
domain:            null
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Checked well past the few days asked for: sessions on the recreated environment kept cloning fresh through 2026-09-28, this one included; the freshness guard and the session-start report watch for a regression."
decision_strength: assented
waiting_on:        null
noted:             2026-09-15
closed:            2026-09-28
---
## What

- <a id="check-default-cc-environment-staleness"></a>**Check whether the
    "Default CC" environment is still cloning fresh in a few days.**
    the earlier environment (AA) — created 2026-04-17, "Default AA" —
    had every session start from a
    container frozen at a Sept-11 commit — 132 commits it had never pushed,
    ~500 behind live `origin/precedent-beta-v01` — which the freshness
    guard then blocked on and the Stop hook read as real unpushed work.
    Recreating the environment as "Default CC" cleared the symptom
    immediately (checked 2026-09-15: fresh clone, `HEAD` at that day's real
    tip). Whether "Default AA" was a one-time staleness or "Default CC" will
    drift the same way after enough days is unmeasured.
    **Remind:** check a session running in "Default CC" around 2026-09-18 —
    `git log -1 --format='%cI %s'`, or read its session-start output for a
    `STALE`/`UPSTREAM MOVED` notice — and confirm it's still tracking live
    `origin/precedent-beta-v01` rather than resuming a frozen container. If
    it's stale again, that's a platform caching bug, not something this repo
    can fix. (2026-09-15, Morgan)
    **Disposition:** ask (2026-09-15, Morgan)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

**Closed 2026-09-28 (done).** Checked well past the few days asked for: sessions on the recreated environment kept cloning fresh through 2026-09-28, this one included; the freshness guard and the session-start report watch for a regression. Morgan approved the very deep check's pass-4 recommendation to close it, 2026-09-28 ("Make the changes you recommend"); strength: assented.
