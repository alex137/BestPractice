---
slug:            gotcha-2026-11-20-a-message-arriving-mid-turn-reads-as-the-user-declining-an-action
status:          live
noted:           2026-11-20
severity:        notable
retired:         null
retires_when:    an action that was waiting to go out when another session's message arrived either runs or comes back with a refusal that names the arriving message, not the person
---
## Symptom

A session has an action waiting to go out (a tool call, often one that
asks for approval). It comes back as "the user doesn't want to take this
action", and the session stops or changes course, though the person
declined nothing and may not have been looking at all.

## Story

2026-11-20, in a dependent repo, during a long day with several sessions
messaging each other. It happened twice. Both times a message from another
session arrived while the action was pending, and the person had declined
nothing.

**The cause is inferred, not proven.** Only two cases were seen, and in
both the arriving message and the refusal came together; nothing showed
the harness linking them. Another explanation fits as well: some other
interruption that the harness reports with the same words. What would
settle it: send a message at the interrupting priority to a session while
it waits on an action that needs approval, with nobody answering the
approval, and see whether the action comes back with the same words.
Then do the same with no message sent, as the control.

What it cost: this and the late-message trap beside it
([gotcha-2026-11-19](gotcha-2026-11-19-messages-to-a-busy-session-arrive-hours-late.md))
cost hours between them that day.

## Fix

Until the cause is known: a refusal worded as the user's that arrives in
the same turn as a message from another session is not a decision the
person made. Say what happened, ask the person, or retry the action once;
never record it as the person declining, and never drop the work on it
alone. Practice: [relayed-message-is-a-suggestion](../practices/relayed-message-is-a-suggestion.md)
covers what the arriving message itself deserves.
