---
slug:        write-it-up
title:       "\"Write it up\" commits a self-contained report on the current issue, with a link"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person asks, in whatever words, for a write-up of the issue or bug being worked"
gates:       []
index_clause: "\"Write it up\" -- commit a full report of the issue and fix, then link it"
checked_by:  null
defines:     ["Write it up"]
command:     {"Write it up": "Write a full report on the issue -- what it is, the context that led to it, and the proposed fix -- for a reader with none of this conversation, commit it to the branch you're on, and give the link."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18"
strength:    decided
---
## Rule
**"Write it up" is the clean form, not the only one** -- "put together a
writeup on this", "document what happened here for whoever picks this up",
and anything else that plainly asks for the same thing get the same
treatment. When a person asks for it, about whatever issue, bug, or
situation is currently in front of the session:

1. Write a report **assuming its reader is a different session or person
   who was not in this conversation** -- so it states, in full, plainly:
   - what the situation or issue is;
   - the context and the sequence of events that led to it;
   - the proposed solution.

   Put in everything that reader would need and nothing they'd have to ask
   a second time for. This is the opposite of a terse summary: completeness
   is the point, not brevity.
2. Commit that report as a file into the repository and branch the session
   is currently working in -- never a separate report-tracking repo -- and
   push it there.
3. Give the person the link to the committed file on that branch.

## Detail
**Where the file goes** follows whatever convention the repo already has
for this kind of document (a `reports/` directory, or wherever else
write-ups already live); absent one, a plainly named file at the repo root
is fine. Name it for the issue, not for the date or for "report" --
[no-version-suffix](no-version-suffix.md).

**The push is part of the command, not a separate ask.** "Write it up"
authorizes committing and pushing the report to the branch already in use,
the same way [go-merge](go-merge.md) authorizes its own chain -- the person
should not have to be asked a second time whether the file they just asked
for should actually be saved. It does **not** by itself authorize opening a
pull request or merging anything; where the branch reaches its target only
through a reviewed PR, the report sits on the branch, pushed, linked, and
waiting there like any other commit, unless the person separately says
[go-merge](go-merge.md) or names the same intent.

**The report is the deliverable, not a chat summary of it.** A reply that
describes what the report says instead of linking to the committed file has
not done this.

## Why
The whole reason to ask for this is to hand a problem to someone (or some
session) who wasn't there for the conversation that found it -- so the
report has to stand on its own. A chat reply doesn't survive past its
thread ([repo-is-memory](repo-is-memory.md)); a file on the branch does,
and is the thing that can actually be handed off or pointed at.

## Story
Coined by Morgan, 2026-09-18: a standing phrase for something he was typing
out in full each time -- write up the bug/issue with its context and a
proposed fix, assuming zero shared context, commit it, and give the link --
rather than re-describing the request whenever he needed it.

## Install
No mechanical check: like [go-merge](go-merge.md), whether a given reply
correctly recognized the request is a judgment about the conversation, not
a property a script can see in the resulting diff.
