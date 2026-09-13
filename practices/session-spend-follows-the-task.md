---
slug:        session-spend-follows-the-task
title:       "Model and compaction follow the task's shape, not a default or a threshold"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "creating a session, or deciding when to compact one"
gates:       []
index_clause: "pick the model from the task; compact at a task boundary, never at a size"
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
  session's)."
strength:    assented
source_practice_number: null
---
## Rule
Two choices a session makes about its own running are decided by **the shape
of the task**, never by a default and never by a threshold.

**Pick the model for the job.** Session creation takes a model parameter, and
it is usually left alone. Reading, diffing, inventory, and *"check whether X
is true"* do not need the largest model available; judgment and writing do.
The work that is mostly retrieval and comparison is the work that runs fine
smaller, and it is also the bulk of what gets spawned.

**Say when a compact is cheap; do not decide it.** The moment worth naming is
when a deliverable has landed and the next thing is independent of how it was
reached — there, the summary carries the conclusion and nothing is lost.
Compacting in the middle of an investigation costs a re-read of everything the
investigation had established.

**Whose call it is: the person's, always.** A session that reaches a boundary
says so in one line — *"this is a cheap point to compact if you want to"* — and
then carries on without it. The context is the person's working memory of the
thread as much as the session's, they may want the detail kept for reasons the
session cannot see, and a session that compacts on its own initiative has
discarded something it was not asked to discard. **Offer the moment, never take
it.**

**How full the context is decides WHICH boundary you say it at, never whether
the offer is yours to act on.** Boundaries are not evenly spaced — a long
session passes several, and everything above makes each of them worth naming.
Far from the limit, name whichever comes naturally. Close to it, say so at the
next boundary rather than letting it go by for a tidier one, and say that it is
close: the person is deciding against a number they cannot see, and the
alternative to their choosing is the harness compacting at the limit,
mid-investigation, keeping whatever it guesses matters. Where the work in front
of you is long enough that no boundary is coming, make the offer anyway and say
what would have to be written down first for the compact to be cheap.

**The one principle under both: what is expensive is re-deriving, not
length.** A long context that already holds the answer is cheap to continue;
a short one that has to rebuild the answer is not. Both defaults — the
biggest model every time, and compacting only when something forces it —
optimize the wrong quantity.

## Detail
**The threshold is the tempting rule and it is the wrong one**, because size
is visible and task structure is not. Watching the context fill up gives a
number to react to; asking *"is the thing I am about to do independent of how
I got here?"* gives no number at all. The number is the one that does not
correlate with cost.

**The clause above is not that threshold coming back in**, because the trigger
has not moved: a boundary is still the only thing that produces the offer, and
size never produces one by itself. What size decides is which boundary is worth
interrupting for, and how plainly to say that room is running out. The case
that separates the two is a session most of the way full and mid-investigation
— under a threshold it compacts there, or nags to; under this rule it says
nothing and keeps working, which is the right answer and the one a threshold
gets wrong.

**A fresh session is the largest re-read there is**, which puts this beside
[spawn-session](spawn-session.md) rather than under it: that rule governs
*whether* the work goes somewhere else, this one governs what it costs once
it does. A new session re-reads its repository from scratch, so the same
reasoning that says "wake a live session before creating one" says "do not
compact mid-investigation" — both are paying twice to learn the same thing.

**[session-load-budget](session-load-budget.md) is the third member**, one
step earlier again: it caps what *every* session pays before its first turn.
The three are the same economy at three moments — what loading costs, what
starting a session costs, and what re-deriving inside one costs.

**The two halves differ in who decides.** Model choice is settled when a
session is created, by whoever creates it, and a session creating another one
makes that call itself. Compacting happens inside a running conversation the
person is reading, so it is theirs. Same economy, different owner.

**Model choice is a floor, not a ceiling.** The rule is against reaching for
the largest model by reflex; it is not a case for running judgment work
small. A task whose output is prose somebody will act on, a design call, or a
review is the work the capability is for. When it is genuinely unclear which
kind a task is, it is the judgment kind.

## Why
These are both choices nobody is forced to make, which is exactly why they
default. Nothing fails when a reading task runs on the largest model, and
nothing fails when a session runs long without compacting — the cost is real
and completely silent, paid per session, spread across every session anybody
spawns.

Naming them as a rule turns two non-decisions into two decisions. That is the
whole mechanism: neither half is hard once somebody asks the question, and
neither gets asked by itself.

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

**What makes the three-session case the useful example** is that none of the
three did anything wrong. Each was created for a reasonable-looking piece of
work. The cost was in the pattern, which no individual session was in a
position to see — the same blind spot [spawn-session](spawn-session.md)
records from the other side, where the session that should have been reused
is invisible to the session about to be created.

## Install
Nothing to configure, and nothing to install: both halves are decisions made
at the moment a session is created or continued, and the parameters belong to
whatever harness is running it.

No mechanical check. The artifacts are a session-creation call and a
compaction, neither of which is in the repository, and a repository cannot
see what model another session ran on or when it compacted. A check that
inferred either from commit timing would be a guess wearing a mechanism's
clothes — the shape [checkable-gets-checked](checkable-gets-checked.md) warns
against, since a gate that fires on correct work teaches the next session to
ignore every gate.
