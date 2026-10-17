---
slug:              todo-2026-09-06-background-freshness-fetch
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
remind_on:         null
blocked_on:        "nothing external, but it was not worth the complexity at the measured numbers — with the throttle the ≈500ms lands so rarely that backgrounding buys little. It also rests on an unverified assumption that a process detached from a hook survives the hook returning rather than being reaped with it, whi"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- <a id="background-freshness-fetch"></a>**Consider making the freshness check's fetch asynchronous.**
    [.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh)'s
    `user-prompt` mode is throttled rather than backgrounded: it skips
    entirely inside its interval (measured ≈17ms, no network, no output) and
    pays one fetch when the interval has passed. Measured 2026-09-06 in a
    cloud container: any remote check costs ≈500ms and `git ls-remote` is
    **not** cheaper than a no-op `git fetch` (≈600ms vs ≈500ms — both are one
    network round trip; neither transfers objects when current), so the only
    lever is asking less often, which is what the throttle does. The
    alternative considered and deliberately deferred: fire the fetch
    detached, return immediately, and act on the *previous* fetch via the
    ≈5ms local comparison — ≈0ms added latency at the cost of freshness
    lagging by one message. **Blocked on:** nothing external, but it was not
    worth the complexity at the measured numbers — with the throttle the
    ≈500ms lands so rarely that backgrounding buys little. It also rests on
    an unverified assumption that a process detached from a hook survives the
    hook returning rather than being reaped with it, which needs a real test
    (this repo has already been burned once by a mechanism verified only
    against synthetic fixtures — see
    [practices/session-bootstrap.md](../practices/session-bootstrap.md)'s
    Detail). Revisit if the throttle's interval ever has to drop low enough
    that the fetch becomes noticeable. Full reasoning, including the
    measurements and the two rejected alternatives:
    [this thread](https://claude.ai/code/session_01NQCKsA4otmeujdrbCGrqR3).

**Disposition:** parked (2026-10-17, the session, under Morgan's delegation of 2026-10-17 ("Fix the other issues you found including the checks that never run. Tell me what you decide. I will be offline so don't wait for me. Approved, act, and Booked."); "drop it" is Morgan's word, not his here)

## How It Closes

Not open until: nothing external, but it was not worth the complexity at the measured numbers — with the throttle the ≈500ms lands so rarely that backgrounding buys little. It also rests on an unverified assumption that a process detached from a hook survives the hook returning rather than being reaped with it, whi

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

2026-10-17, very deep check pass 4 (ambiguous, asked of the person): a deliberate deferral with a revisit trigger (throttle interval dropping) that has not fired; it is a declined idea, not blocked work. Would drop it (status: dropped) as decided-not-to-build; Morgan's call.

2026-10-17, parked by the session under Morgan's delegation of 2026-10-17 ("Fix the other issues you found including the checks that never run. Tell me what you decide. I will be offline so don't wait for me. Approved, act, and Booked."), the way the very deep check said it would settle it: a deliberate deferral whose revisit condition never came. It is not raised again unprompted.
