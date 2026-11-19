---
slug:        tasked-session-stays-reachable
title:       A session doing long work for another stays reachable, and a change of plan is not sent until it is acknowledged
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Tasking another session, or working for one, is a moment, not a file; the occasion index reaches it."
occasion:    "tasking a session with long work, changing its plan, or working for one"
gates:       []
index_clause: "a change of plan interrupts and is acknowledged; check messages each wake"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-19"
approved_by: "Alex, 2026-11-19: 'yes on bestpractice', to the proposal that the late-messages trap and its rule go upstream"
strength: decided
---
## Rule
**A message that changes what another session should do is not sent until that session says it has it.** Send it so that it interrupts, say in its first line that it interrupts only the wait and that background work keeps running, ask for a one-line acknowledgment, and send again if none comes. Put everything the other session needs in the one message.

**A session doing long work for another keeps itself reachable.** Its long job runs in the background, saves its progress and can resume ([slow-steps-report-and-cache](slow-steps-report-and-cache.md)); the session waits on it in short commands; on every wake it looks for messages from whoever tasked it before it looks at the job; and its first report after any gap lists the messages it has seen, by subject.

## Detail
A send that reports "delivered" says the message was accepted, not that it was read. A session in the middle of a turn does not see a message of ordinary priority until that turn ends, and a turn that babysits a job ends when the job does.

**Interrupting is cheap when the work is in the background.** It ends a wait. It does not end the job, so long as the job was started detached and writes its progress to disk. A session that runs its long job in the foreground has made itself unreachable for exactly as long as the job takes; that is the thing to avoid, not the interruption.

**One message, not three.** Messages sent over an hour can arrive in any grouping, or all at once, and a session that acts on the first before the second arrives acts on a plan already withdrawn. When a second message would change the first, send one that replaces both and says so.

**The acknowledgment is the delivery.** Whoever sent the message looks for it. Where a fleet is large, the sender keeps the list of what is unacknowledged in front of it and treats an unacknowledged change of plan as work not yet handed over.

**For the session that receives:** saying which messages it has seen costs one line and is the only way the sender can tell a message that was ignored from one that never came. A session that finds a message hours old says so plainly and says which of its work the message would have changed.

This sits beside [report-up-the-chain](report-up-the-chain.md), which says where a session's own report goes, and [relayed-message-is-a-suggestion](relayed-message-is-a-suggestion.md), which says how much weight a message from another session carries once it has arrived. This rule is about whether it arrives.

## Why
A fleet's orchestrator steers by message. If its messages land hours late it is steering from a picture that is hours old, and every worker is, at any moment, possibly executing a plan that was replaced. The waste compounds: the work is redone, the sessions that depended on it wait, and the orchestrator reads each late arrival as one worker's lapse and does not see the pattern.

## Story
[gotcha-2026-11-19](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-11-19-messages-to-a-busy-session-arrive-hours-late.md): about a night of machine time across seven sessions, and one worker that received eleven messages at once twelve hours after the first was sent. The orchestrating session had itself told the workers to hold their turns open.

## Install
Nothing to install. A session that tasks others loads this rule when it does; a brief written for a worker says, in its own words, to check for messages on each wake and to list what it has seen.
