---
slug:        capture-gate
title:       Capture in the thread that created the need — before the merge
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "merging a branch"
gates:       ["merge"]
index_clause: "capture the follow-on work in the thread that created the need"
checked_by:  null
defines:     ["capture gate"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 10
---
## Rule
The thread that develops a capability, a number, a decision, or a
limit is the thread that understands what follow-on artifact it implies (a
document update, a registry entry, an exported practice, a decision record).
Capture it **in that thread, before merging** — as step 0 of the merge
runbook. Never park it in a "for later review" staging document.

## Detail

## Why
Deferred capture repeatedly lost both the rationale (the merging
thread didn't know why the matter existed) and the timestamp (priority went
to whoever wrote it down first). A "waiting for review" parking lot caused a
real miss: staged content sat unrecorded for a full cycle because its thread
ended without folding it in. The gate that fixed it: before any merge, ask
"did this thread's work imply anything that must be captured?" — and a grep
for known parking-lot markers, run at thread end.

## Story
**A real miss, and the parking lot that caused it.** Deferred capture
repeatedly lost two things at once: the rationale, because the thread doing
the merging did not know why the matter existed, and the timestamp, because
priority went to whoever wrote it down first rather than to whoever found
it first.

The specific failure that produced the gate was a "waiting for review"
staging document. Content staged there sat unrecorded for a full cycle,
because the thread that put it there ended without folding it in -- and
nothing about a parking lot forces anyone to come back. The parking lot
looked like the responsible thing to do, which is why it survived long
enough to lose something.

The fix is the gate, not a better parking lot: before any merge, ask
whether this thread's work implied anything that must be captured, and grep
for the known parking-lot markers at thread end. The prohibition on
"for later review" staging documents is part of the rule rather than a
stylistic aside, since re-introducing one re-opens the same hole.

## Install
Step 0 of the runbook in
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.template). The
practice-export gate ([practice-export-loop](practice-export-loop.md)) is this same rule applied to process
improvements.
