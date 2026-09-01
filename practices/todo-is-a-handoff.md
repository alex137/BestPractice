---
slug:        todo-is-a-handoff
title:       A TODO is a handoff, not a parking lot
tier:        on-demand
severity:    default
applies_to:  ["TODO.md"]
occasion:    "writing or triaging an open item"
gates:       ["merge"]
index_clause: "queue only for a stated blocked-on/out-of-scope reason — otherwise just do it"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 53
---
## Rule
Before writing an open item, ask: *could this session finish it
now?* If yes, do the work — the inclination to queue an agent-doable item is
the signal to do it, not to file it. An item may be queued only for a stated
reason.

## Detail
The reason is written into the item itself:

- **blocked-on** — a named external input: a decision (with its owner named),
  a resource, an event, an artifact that does not exist yet; or
- **out-of-scope** — genuinely too large or too tangential for the current
  session, in which case the item must carry the context a cold session
  needs: why it matters, the intended approach, and the pointers.

"Would enlarge this turn" is not a reason; it is the moment the context is
cheapest. A sweep that finds an open item with neither reason either does it
in the sweeping session or closes it as not worth doing.

## Why
A queued item sheds context every day it waits. The session that
noticed the need holds the reasoning, the file locations, and the half-formed
approach — and almost none of that survives into a one-line queue entry, so
deferral converts cheap work into expensive work, and often into work never
done. The catalog already outlaws deferral for two special cases — capture
happens in the thread that created the need (practice 10), and the
inclination to write a verify-later marker means go verify now (practice
49) — because both learned that the queue is where context goes to die. This
generalizes the same insight to ordinary work: the typed TODO exists to hand
work *across a genuine boundary* (to a human decision, to hardware, to a
session with the right scope), not to spare the current session effort.

## Story
Origin: a session queued two follow-up items from its own build — both
labeled agent-doable, one of them a half-hour mechanical change — and the
owner asked why work needing no input from them was parked at all. Both
items, done later, cost more to re-orient into than they would have cost to
finish on the spot.

## Install
The TODO template's header (practice 1) carries the compressed
rule, so every new item is written against it; the periodic sweep enforces
the stated-reason requirement on the backlog.

Not yet attempted mechanically: a check that scans `TODO.md` entries for a
stated `blocked-on`/`out-of-scope` reason is a plausible candidate
(`checkable-gets-checked` applies), left `checked_by: null` here rather than
wired in without testing, since this file is a straight conversion of
Alex's practice 53 (merged to `main` after this branch's fork point — see
[CHANGES_TO_TELL_ALEX.md](CHANGES_TO_TELL_ALEX.md)) and not new authorship
going through the creation pipeline's own review. Revisit when phase 5's
enforcement work reaches the backlog.
