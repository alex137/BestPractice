---
slug:            gotcha-2026-11-19-messages-to-a-busy-session-arrive-hours-late
status:          live
noted:           2026-11-19
severity:        notable
retired:         null
retires_when:    a message sent to a session that is mid-turn reaches it at its next tool call, whatever its priority
---
## Symptom

A session that tasks other sessions sends one a change of plan. The send
reports "delivered". The other session carries on with the old plan, and
hours later says the message "never arrived", or that several arrived at
once.

## Story

2026-11-18 and 2026-11-19, in a dependent repo. A main session ran up to
seven worker sessions on jobs that take hours. Each worker held one turn
open for its whole run, waking every ten minutes to look at a log,
because [an earlier trap](gotcha-2026-11-18-attaching-a-repository-restarts-a-cloud-session-and-kills-its-jobs.md)
had taught that a machine can restart between turns and kill a background
job. The main session had told them to work that way.

A message sent at the default priority waits for the receiving turn to
end. With a turn that lasts all night, that is all night. One worker
received eleven messages together, twelve hours after the first was sent.
Messages sent at the priority meant to join a running turn fared no
better in at least three cases: four hours late, or not before the turn
ended. Why that priority did not work was not established.

What it cost: workers ran work that had been cancelled, ran on settings
that had been replaced, and reported themselves finished and idle while
three other sessions waited on work they had never been asked for. About
a night of machine time across the sessions went to runs that were redone
or not wanted. The main session lost hours more before it saw the
pattern, because each late message looked like one worker's oversight.

A message sent at the interrupting priority arrived within a minute every
time it was used. It ends the receiving session's current wait, not the
job that session started in the background, so nothing was lost by it.

Seen again on 2026-11-20, in a different dependent repo installing a
practice set over a long multi-session day: default-priority messages
between sessions arrived hours late, and messages sent at the
interrupting priority arrived at once. Same shape, same remedy.

## Fix

Practice [tasked-session-stays-reachable](../practices/tasked-session-stays-reachable.md):
a message that changes another session's plan interrupts and asks for an
acknowledgment; a session doing long work for another checks for messages
on every wake and lists what it has seen.
