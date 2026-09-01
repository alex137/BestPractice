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

## Install
Step 0 of the runbook in
[templates/AGENTS.md.template](templates/AGENTS.md.template). The
practice-export gate ([practice-export-loop](practice-export-loop.md)) is this same rule applied to process
improvements.
