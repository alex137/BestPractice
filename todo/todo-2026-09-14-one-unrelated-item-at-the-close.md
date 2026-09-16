---
slug:              todo-2026-09-14-one-unrelated-item-at-the-close
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
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

- <a id="one-unrelated-item-at-the-close"></a>**`closing-items-are-this-thread`
    forbade every unrelated item; Morgan asked for exactly one, and only at
    the close. CLOSED 2026-09-14 — the amendment is in the practice file.**
    Asked for 2026-09-14, in his own words: *"please only give me ONE to-do
    that is unrelated to the issue, and ONLY do that when the issue is done
    (when you are about to say it's ready to be archived), and make it the
    issue most important in your opinion AND (importantly) label clearly that
    this is UNRELATED to the thread."* **Strength:** decided (2026-09-14,
    Morgan).
    **Why the old rule was not quite right.** It read *"close on this thread's
    own work and nothing else — an unrelated suggestion sends me to a window
    already doing it"*, and the reasoning holds: an unrelated item dropped
    mid-thread competes with the thread. But a blanket ban also lost the one
    case where a session is the only thing that has seen a problem, and the
    person asking "anything else?" gets told no.
    **What landed.** The amendment is now the practice's own Rule, transcribed
    unchanged from the blockquote this item used to carry, with the exchange
    above in its Story: one unrelated item, only in the `## Next Steps`
    section of the reply that says the session can be archived, labelled
    **"Unrelated Todo item to consider:"**, chosen rather than collected. It
    is a `gates: ["reply"]` practice with no mechanical check, for the reason
    its Install section gives — the subject is the conversation transcript,
    and the correct outcome is the *absence* of a paragraph.
    **The item was already stale when it was read.** Its blocked-on paragraph
    said a session rooted in that set lands it and this one cannot; a
    different window holding that repository had landed it the same day, at
    12:05 −03:00, hours before this item was next opened. That is the
    mechanism working as intended — the wording was preserved here precisely
    so another window could land it, and one did — but it is also why
    [item-closes-on-its-condition](../practices/item-closes-on-its-condition.md)
    says to check the condition rather than re-read the item's own
    description of the world.
    **Disposition:** parked (2026-09-14, closed as done)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
