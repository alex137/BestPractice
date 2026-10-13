---
slug:        inner-workings-for-code-owners
title:       "How Precedent works inside is for code owners; everyone else gets plain words"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment, not a file: what any reply says to the person it is for. Routed by the `reply` gate. Decided: 2026-10-12, when the practice landed at universal."
occasion:    "writing a reply, or anything a tool prints for a reply, to a person who may not be one of the repository's code owners"
gates:       ["reply"]
gates_why:   "It governs what every reply says, so the reply gate is the moment it fires; no file path reaches it."
index_clause: "inner workings for code owners only; to anyone else, plain words"
index_required: false
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-12"
approved_by: "Morgan, 2026-10-12 (BP is BestPractice (BP)): \"Any TECHNICAL suggestions on how BP works must only be shown to users who are CODEOWNERS\", then \"Anything on the inner works of how BP works including things like file management, dealing with temporary files, dealing with temporary repos etc -- should only be for codeowners. We must assume that non-codeowners are very low tech people.\""
strength:    decided
---
## Rule
**How Precedent works inside is for the repository's code owners only.**
That covers its file management, temporary files and scratch folders,
temporary or attached clones, branches, checks and gates, hooks, vendoring,
and every suggestion about changing any of it. A session says none of it
to a person who is not a code owner, and **assumes that person is not
technical at all**.

To them, a reply says what happened to *their* work, in everyday words: it
is saved, it is shared, it is waiting for someone, or something needs their
answer. Whatever the engine needed done along the way, the session does it
or leaves it unsaid. When a check would have the session explain a
mechanism, it settles the matter itself instead, or says the outcome in one
plain sentence.

## Detail
**Who is a code owner** is what
[tools/precedent_audience.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_audience.py) answers. **In
doubt, the person is treated as not one**, as that tool already does.

**Code owners get the full picture**, as before. Hiding changes what a person
is told, never what is enforced: every check still runs.

**What this replaces.** Since 2026-10-05 a practice about running the
repository could be marked `visible_to: code-owners`
([spec/PRACTICE_FORMAT.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_FORMAT.md)), which hides the
practice's text from everyone else. That hid the rules, not what the
session then said: a check that applies to everyone could still have the
session name a scratch folder or a clone to a person who has never heard of
either. This rule is about what is said.

**The first place it was applied**, the same day: closing a session. The
reply gate tells a session that holds files found nowhere else to tidy
them itself for a person who is not a code owner, and never to show them the
technical line a code owner gets for it
([tools/precedent_gate.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_gate.py)).

**Then everything else that spoke through a session**, the next day
(Morgan: "Nothing technical should ever be said to a non technical person.
The list you gave is great and should only be for code owners"):

- the reply gate opens every turn, for a person who is not a code owner,
  with the plain-words instruction, naming each kind of message below;
- the "Files touched" list
  ([reply-links-files](reply-links-files.md)) is for code owners only;
- the session-setup warning printed at the start of a turn says it is for
  the session to repair, never to relay;
- the stop hook's refusal says to correct the reply without naming the
  check, a file, a branch, a clone or a folder;
- Update Vendors' report opens, for a person who is not a code owner, by
  saying none of it reaches them, and what to tell them instead.
- a wait ([answer-first-ask-before-long-work](answer-first-ask-before-long-work.md)
  part 3) is said as its outcome -- "I'm double-checking the change; I'll
  tell you when it's done, or say stop" -- never as a background run, a
  test or CI schedule, a branch, or a job to kill. Added 2026-10-13, after
  a code owner, told about a full suite running on `main` until GitHub's
  weekly test was due, asked whether a person who is not one would be told
  the same; nothing in the gate's list said otherwise.

The ladder's own lines (stage words, branch names in The Boildown) reach only
a person on the ladder.

## Why
A person who is not a code owner came to get their own work done. Hearing
about scratch folders, clones or checks costs them attention, asks them to
judge something they cannot judge, and makes a simple tool feel like a
machine they have to operate. The session can settle almost all of it
itself, and a code owner is there for the rest.

## Story
2026-10-12: a closing reply in a consuming repository gave its person a line
about a scratch folder, a commit message file, a printout of a practice and
the update's own log. The person was a code owner, so it was right for them,
and they asked whether a person who is not one would see the same. They
would have.

## Install
Nothing to install: the reply gate carries the rule to every session, and
the archive check's instruction already follows it. A check or tool that
speaks to the person asks `precedent_audience.is_code_owner` before it
explains a mechanism.
