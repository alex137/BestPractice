---
slug:        session-spend-follows-the-task
title:       "Model choice follows the task's shape, not a default"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "creating a session"
gates:       []
index_clause: "pick the model for the job -- reading runs small, judgment doesn't"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-13 -- \"it's good if it's universal BUT the practice
  should recommend to the user to recommend at those points, not compact by itself\".
  Universal is confirmed by him directly; the compact clause is rewritten to that
  correction. Its ORIGINAL landing, 2026-09-12, rested on a scheduled instruction
  asserting his authorization which he does not recall giving (\"I don't remember if I
  did\"), so the rule stands on the 2026-09-13 answer and not on that instruction.
  Pairing model choice with the compaction point in one practice was a session's
  judgment either way. AMENDED 2026-09-13, later the same day: Morgan asked
  whether the rule should also recommend compacting at a token size, and
  approved the narrower clause this session proposed in answer -- which boundary
  to speak at when room is running out, no threshold -- \"sure, these are good
  changes\" (strength: assented; the question is his, the clause is the
  session's). The INDEX CLAUSE was corrected 2026-09-13 in his own words --
  \"it should suggest it, never compact on its own\" (strength: decided) -- having
  still read \"compact at a task boundary, never at a size\", which predated the
  same day's rewrite of the Rule and was the one line every session sees in the
  occasion index. AMENDED AGAIN 2026-09-13, after hours of long sessions in which
  the offer was never once made: Morgan -- \"you have to make it a more prominent
  recommendation ... maybe we can have another trigger\" (strength: decided, for
  the requirement). Registering the practice on the `reply` gate, and requiring
  the offer to be its own line rather than a clause inside a paragraph, are the
  session's choice of mechanism. AMENDED 2026-09-14, after the reply-gate
  registration went eleven hours without producing one offer: Morgan --
  \"yes, build the size-aware check\" -- agreeing to the mechanism this session
  proposed in answer to his own question (\"should we update our rule again?\").
  Recorded `assented` and not `decided` because the proposal was the session's:
  the threshold, counting growth from the session's own starting context, and
  the two fixed sentences are all this session's choices, and none of them was
  put to him as a choice between alternatives."
strength:    assented
source_practice_number: null
---
## Rule
**Pick the model for the job.** Session creation takes a model parameter, and
it is usually left alone. Reading, diffing, inventory, and *"check whether X
is true"* do not need the largest model available; judgment and writing do.
The work that is mostly retrieval and comparison is the work that runs fine
smaller, and it is also the bulk of what gets spawned.

**Model choice is a floor, not a ceiling.** The rule is against reaching for
the largest model by reflex; it is not a case for running judgment work
small. A task whose output is prose somebody will act on, a design call, or a
review is the work the capability is for. When it is genuinely unclear which
kind a task is, it is the judgment kind.

## Detail
**A fresh session is the largest re-read there is**, which puts this beside
[session-text](session-text.md): that rule governs *whether* the work goes
somewhere else, this one governs what it costs once it does. Reasoning about
which model a spawned session needs is the same economy as reasoning about
whether to spawn it at all — neither is a decision nobody is forced to make,
which is exactly why both default.

**[session-load-budget](session-load-budget.md) is the other member of the
same family**, one step earlier again: it caps what *every* session pays
before its first turn. The two are the same economy at two moments — what
loading costs, and what starting a session on the right model costs.

## Why
Picking a model is a choice nobody is forced to make, which is exactly why it
defaults to the largest one available. Nothing fails when a reading task runs
on the largest model — the cost is real and completely silent, paid per
session, spread across every session anybody spawns. Naming it as a rule
turns a non-decision into a decision, and it is not hard once somebody asks
the question; it just does not get asked by itself.

## Story
**Reported 2026-09-12 and not verified in this repository**, which has no
access to the sessions in question: three separate sessions were created
against one repository to do work that one session could have done in
sequence, each paying in full for reading that repository from scratch. The
per-session cost was reported in single-digit US dollars; that figure is
relayed here rather than measured, and nothing in this repository can check
it ([no-invented-specifics](no-invented-specifics.md) — the range is
attributed rather than asserted).

**The clause about which boundary to name came from the question the rule
invites**, 2026-09-13: if a threshold is wrong, what happens to a session that
runs out of room before its next boundary? Nothing answered that, and the
answer that survives the objection above is not a threshold — it is which
boundary you speak at, once several are available. No incident behind it; a
gap found by reading the rule rather than by paying for it.

**The rule did not fire for hours, and could not have**, 2026-09-13.
Morgan worked a long stretch of long conversations after this practice landed
and was never once told a compact was cheap: *"you never suggested NOT ONCE to
do that (or if you did, it was hidden in your novel-length comments so I missed
it)."* The root cause is not that sessions forgot. The practice was routed
through the occasion index alone, and its occasion reads *"deciding when to
compact one"* — so the one line that would have prompted a session reached only
a session that had already decided to think about compacting. A trigger
conditioned on the thing it triggers is not a trigger. The reply gate fires at
the end of every turn regardless of what the session was thinking about, which
is the part the occasion index cannot do.

**The reply gate was not enough either, and the eleven hours after it prove
it**, 2026-09-14. The fix for the failure above landed 2026-09-13 at 19:38
UTC; Morgan worked through the night and into the morning and got the offer
exactly as often as before, which is never: *"you never once recommended I
compact a session - despite our updated rules."* The root cause is that the
reply gate **prints** — the stop hook writes the practice to stderr after the
reply has been composed and shown, so for a rule about what a reply must
CONTAIN it arrives after the only moment it could have been applied, and that
is written in the hook's own source. Only
[precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_reply_check.py)
refuses a turn, and until this change it enforced one source's closing
convention and nothing else.

**The thing that made it hard to enforce is worth keeping**: the offer is owed
at a boundary, and no check can see a boundary. A requirement that fired on
every reply would be a nag, and one that waited for a session to notice its
own boundary is what had already failed twice. Size is the third answer, and
it is not the threshold this practice rejects — it never decides whether to
compact, only whether the question has gone unasked for too long.

**What makes the three-session case the useful example** is that none of the
three did anything wrong. Each was created for a reasonable-looking piece of
work. The cost was in the pattern, which no individual session was in a
position to see — the same blind spot [session-text](session-text.md)
records from the other side, where the session that should have been reused
is invisible to the session about to be created.

## Install
**Deduplicated 2026-09-15, on the compact half only, into [the-boildown](the-boildown.md).** Morgan asked for the whole closing-section family of practices consolidated into one place; this practice's compaction clause, its reply-gate registration, and the enforced sentence pair moved there along with it. What follows below in this section is that mechanism's own history, kept for the record -- see the-boildown for how it works now. Model choice is a different occasion (session creation, not a reply's closing content) and was kept here, on the session's own judgment, rather than folded in: *"Let's go - go merge, do it, go update"* authorized the consolidation without either of them being told apart first, so the split -- and the reasoning for it -- is recorded here rather than silently assumed.

**The compaction offer was enforced from 2026-09-14 until the move above.** The universal source declared it in its own `reply_check.json`, and the stop hook refused a reply that carried neither *"This is a cheap point to compact"* nor *"Not a cheap point to compact"* once the conversation had grown 100,000 tokens since one of them was last said. Both answers satisfied it: mid-investigation the rule's own answer is to keep working, and a check that took only the offer would push a session into making one it does not mean.

**The number was a choice, and here is what it was chosen against.** A session
in this repository opens at ≈97,000 tokens of context before anyone types
anything, and this one reached ≈205,000 across a morning's work — both
measured on 2026-09-14, not estimated. So the threshold counted growth from
where the session STARTED, and 100,000 put the first offer about one long
working stretch in, and each repeat about the same again. Nobody measured
that it was the right interval; that constant now lives at the-boildown
([constants-are-risk-inputs](constants-are-risk-inputs.md)).

**What still has no mechanical check is the model half.** A session-creation
call is not in the repository, and a check that inferred the model from commit
timing would be a guess wearing a mechanism's clothes — the shape
[checkable-gets-checked](checkable-gets-checked.md) warns against, since a
gate that fires on correct work teaches the next session to ignore every
gate.
