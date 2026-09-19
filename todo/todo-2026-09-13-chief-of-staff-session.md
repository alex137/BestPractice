---
slug:              todo-2026-09-13-chief-of-staff-session
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Build the Chief of Staff session -- decided after the first real fleet sweep reported sessions as blocked on Morgan that he had already archived."
decision_strength: decided
waiting_on:        null
noted:             2026-09-13
closed:            2026-09-14
---
## What

- <a id="chief-of-staff-session"></a>~~**Decide whether to build the Chief of
    Staff session.**~~ **Decided 2026-09-14, by him: build it.** The universal
    practice and the sweeper Routine are live; the tag namespaces and the
    standing desk are not, and each is still his call —
    [spec/CHIEF_OF_STAFF.md](../spec/CHIEF_OF_STAFF.md)'s "What got built" says
    which is which. What decided it was the first real sweep reporting two
    sessions as blocked on him that he had already archived, which is now the
    practice's own filter: state, never the session's own prose. Proposal drafted 2026-09-13 at
    [spec/CHIEF_OF_STAFF.md](../spec/CHIEF_OF_STAFF.md): one standing session that
    reads the whole fleet through `list_sessions`, reports what is blocked and
    what collides, spawns work rather than doing it, and links every session it
    names so the next action is one click away. The platform capability is
    measured, not assumed — the status buckets, the `needs_action` field and the
    one-way messaging limit are all recorded there with the date.

    **What a decision unblocks, in order:** a universal practice defining the
    command; the `subject:`/`repo:`/`role:`/`wants:` tag namespaces written
    where a spawning session reads them; and the session itself. The tag
    convention is the half that decays if it waits — a `subject:` tag is only
    useful applied at creation, so every session opened before the decision is
    invisible to the collision check unless somebody retags it by hand.

    **A reminder was recorded here as scheduled for 2026-09-16** — a one-shot
    Routine that would put the four questions to him. **It is not on the
    account.** Checked 2026-09-14 with `list_triggers`, which returned four
    Routines, all one-shot dispatchers from the 2026-09-13 rollout, all
    already fired. Why it is missing is not established. The decision arrived
    without it, so nothing is owed — but it is the second thing this item
    demonstrates: **a Routine is invisible from inside the repository, so a
    session reporting that it scheduled one is not evidence that it exists.**
    Verify with `list_triggers`
    ([verify-postcondition](../practices/verify-postcondition.md)).
    **Disposition:** parked (2026-09-14, closed by his decision)

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
