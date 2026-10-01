---
slug:        capture-gate
title:       Capture in the thread that created the need — before the merge
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment, not a place — routed by the `merge` gate, and by the occasion index for the second pass, which comes before any merge. Decided: phase 4 routing pass; the index line since 2026-10-01, when second-pass-capture merged in."
occasion:    "finishing substantial work, or merging a branch"
gates:       ["merge"]
gates_why:   "Its occasion is the merge, and the second pass runs just before it."
index_clause: "capture it in the turn that finds it; a separate second pass; merge is backstop"
index_required: true
checked_by:  null
defines:     ["capture gate", "capture sweep"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork); second-pass-capture (BestPractice, pre-fork) merged in on 2026-10-01, in the reduction pass Morgan approved that day: \"Question 3 - all are great, approved\" (strength: decided)"
source_practice_number: 10
---
## Rule
The thread that develops a capability, a number, a decision, or a
limit is the thread that understands what follow-on artifact it implies (a
document update, a registry entry, an exported practice, a decision record).
Capture it **in the turn that discovers it** — the merge-runbook gate is the
backstop that catches what a thread missed, never the plan. Never park it in
a "for later review" staging document.

**After any substantial work-product** — a document, a design, an analysis,
a decision — the same session does a deliberate second pass **as a separate
step, not part of the production flow**, re-reading its own reasoning
against a short checklist: (a) did every idea discussed reach its **durable
artifact**, or does it live only in prose or conversation? (b) do
**parallel artifacts** that must track this change have their transfer
verdicts ([parallel-artifact-ledger](https://github.com/alex137/BestPractice/blob/staging/practices/parallel-artifact-ledger.md))? (c) did technical value get its **cross-ledger
capture** — the business, operational, or planning implication recorded where
those live? (d) are open decisions **queued in the typed TODO**
([repo-is-memory](repo-is-memory.md))
rather than only in the conversation? (e) are the **indexes, registries, and
glossaries** synced? Run that sweep before the merge, so what it finds lands
in the same change-set as the work.

## Detail
**Why the unit is the turn, not the thread.** Long sessions are summarized
when their context fills, and a capture queued "for the merge" survives that
summary only as one line in a task list with its rationale gone. Fold the
matter before doing anything else in that turn. A mechanical check that
fails on "fold before merge" phrasing in task lists closes the loop.
(Origin: a thread surveyed a record, found four items its own decisions had
made necessary, queued them "to fold before merge" — correct under the
merge-gate form of this rule — and the person pointed out that a context
summary would have erased exactly that queue.)

## Why
Deferred capture repeatedly lost both the rationale (the merging
thread didn't know why the matter existed) and the timestamp (priority went
to whoever wrote it down first). A "waiting for review" parking lot caused a
real miss: staged content sat unrecorded for a full cycle because its thread
ended without folding it in. The gate that fixed it: before any merge, ask
"did this thread's work imply anything that must be captured?" — and a grep
for known parking-lot markers, run at thread end.

**Why the second pass is separate.** The production mindset cannot audit
itself: while drafting, every idea feels captured because it was *thought*.
In the origin repo, an owner-prompted "did we miss capturing anything?"
sweep found two real gaps in the same day's work — a cross-artifact transfer
that had been waved off and a competitor-inspired idea noted in passing but
never landed — each of which the drafting passes had individually missed.
The separation is the point: the sweep is a different cognitive act
(reading for omissions) from drafting (writing for completeness), and it is
cheap — minutes against the cost of a lost idea.

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

**The second pass came from the same kind of miss** (second-pass-capture's
own story). Somebody asked "did we miss capturing anything?" of work that
had already been drafted, reviewed and considered finished, and the answer
was yes twice: a cross-artifact transfer that had been waved off, and a
competitor-inspired idea noted in passing but never landed anywhere durable.
The drafting passes had individually missed both, which is the finding:
thinking an idea and landing it in a durable artifact are different acts
that feel identical from the inside, so no amount of care within the
drafting pass substitutes for a separate one.

**Merged, 2026-10-01.** second-pass-capture said to run its sweep "before
the merge-time capture gate", and both sat in the merge gate's list, so the
two were one rule in two files and two index lines. The reduction pass
Morgan approved that day folded the sweep in as the second paragraph of
this Rule. Its file stays as the record.

## Install
Step 0 of the runbook in
[templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/staging/templates/AGENTS.md.template). The
practice-export gate ([practice-export-loop](practice-export-loop.md)) is this same rule applied to process
improvements.

The second pass goes in the session-end or pre-merge ritual, before the
merge's capture question. Adapt its checklist to the repo's ledgers (what
counts as a durable artifact, which registries exist). The trigger for
adopting it retroactively: the first time an owner's "did we miss anything?"
finds something — that incident is the origin story
([mistakes-become-rules](mistakes-become-rules.md)).
