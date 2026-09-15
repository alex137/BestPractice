---
slug:        findings-return-through-repo
title:       A finding goes into the repo, not into a message the person relays
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "discovering something a session in another window will need, or the person adopts a recommendation you gave in chat"
index_clause: "commit it, an adopted plan included; never leave it for the person to carry"
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

**An adopted recommendation is a finding, and the easiest one to lose.** When
the person asks *"should we do A first or B first?"*, the session answers,
and the person proceeds on that answer, a plan has just been made — but no
file was open, nothing was being edited, and the answer arrived in the shape
of advice rather than work. That is exactly the moment this rule does not
feel like it applies, and exactly the moment the next session most needs the
record: the *reason* for the ordering lives only in the exchange that
produced it. So the turn in which work starts on the adopted path writes the
decision into the open item it governs — what was chosen, why, who adopted
it, when, and its [decision-strength](decision-strength.md) (proceeding on a
recommendation without choosing it from options is `assented`). A plan made
by proceeding is still a plan; the repository records it or nobody does.

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

**2026-09-15, the adopted-recommendation case.** A session in a dependent
repository was asked which of two migrations to take first — the upstream
practice-system upgrade, or a planned restructuring of the repository — and
recommended the upgrade first, with the deeper half of it folded into a later
restructuring phase so a root instruction file would be migrated once rather
than twice. The person proceeded on that answer; the upgrade landed, then a
restructuring phase landed on top of it, all recorded in detail. The
sequencing decision itself — the reason the deeper migration was waiting, and
what phase it was waiting for — appeared in no file. A day later the person
asked *"is this planned path documented?"* and the honest answer was no: the
open item that should have carried it still described the pre-upgrade
world. Both of this repository's rules about memory were in force and loaded
that whole time; neither fired, because the decision had arrived as an
answer to a question, not as a finding.

## Install
Nothing to configure. When a session finds something durable, the finding
goes in the same commit as the work, or in the project's
environment-gotchas section, or as an open item — then into the reply.
