---
slug:        findings-return-through-repo
title:       A finding goes into the repo, not into a message the person relays
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "discovering something a session in another window will need"
index_clause: "commit it; never leave it for the person to carry to the next window"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-10"
approved_by: "Morgan"
source_practice_number: null
---
## Rule
Commit the finding; never leave it for the person to relay.

When a session discovers something another session will need — an
environment trap, a measurement, a corrected diagnosis — it **commits that
finding** rather than reporting it in chat for someone to carry to the next
window.

Sessions cannot see or message each other. The only thing connecting two
open windows is a person copying text between them, and **every hop through
a person is a hop where the finding can be dropped, paraphrased, or arrive
after the other session already paid to rediscover it.**

Say it in the reply too. The reply is how the person learns; the commit is
how the next session does.

## Detail
This is [repo-is-memory](repo-is-memory.md) at a shorter timescale. That
rule is about the session that starts tomorrow; this one is about the
session already running in the next window, which is the case where the
temptation to just say it is strongest and the loss is fastest.

**The test is not whether the finding is finished.** A measurement nobody has
explained yet is still worth committing — the next session needs the number,
not the conclusion.

## Why
Parallel windows are good for measuring and bad for relaying. Two sessions
measuring the same environment independently produce genuinely stronger
evidence; two sessions relaying findings through one person produce
duplicated work and half-transferred context.

## Story
2026-09-10, across a working day spent in several windows on one repository:
a session measured that a fresh container received no user-defined
environment variables, a second confirmed it independently, a third
discovered that a spawned session can lose its own tools mid-run, and a
fourth found that two practice-source repositories had their default branch
pointed at a feature branch — a silent revert waiting to happen.

**Every one of those reached the other windows by the person pasting it**,
and one of them arrived only after a session had already re-derived it. The
person said so directly: *"sometimes I don't want you to merge... I ask
other sessions, or sometimes I do something different during the waiting
time but it returns a bug - same one in the other session etc etc."*

The findings that were committed the same day — the gotchas, the open items
— cost nothing to transfer. The ones that stayed in chat cost a paste each
time, and the count of pastes is the whole argument.

## Install
Nothing to configure. When a session finds something durable, the finding
goes in the same commit as the work, or in the project's
environment-gotchas section, or as an open item — then into the reply.
