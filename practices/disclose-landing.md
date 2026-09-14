---
slug:        disclose-landing
title:       Landing or proposing a practice is disclosed plainly, every time
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a practice lands or a candidate is raised, at any level"
gates:       ["reply"]
index_clause: "state plainly what happened and where — individual, named team, or universal"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
Whenever a session lands a practice or raises a candidate — at any of the
three levels — its reply states plainly, in its own words, that this
happened and exactly where: the individual's own set, a **named** team set,
or the universal library. It also states plainly whether the practice is
already in force or is still waiting on someone else's yes, and if the
latter, who that is. This is never left to be inferred from a file path in a
diff, a tool's stdout, or a generic "I've added a practice" with no level or
location named.

## Detail
`precedent_land.py` and `precedent_candidate.py` both print an explicit
`DISCLOSE TO THE HUMAN:` line for exactly this reason — it names the level,
the location, the approver where one is needed, and whether the practice is
already in force. A session that runs either tool has this sentence handed
to it already assembled; the failure mode this practice exists to prevent is
reading that line and then summarizing the *outcome* ("added a practice
about X") while dropping the *level and status*, which is exactly the
information a person cannot recover without reading the diff themselves.

The three shapes this actually takes:
- **Individual** — always already in force the moment it's agreed; say so,
  and name whose set it's in (it's never ambiguous — it's the person you're
  talking to).
- **Team** — in force immediately if the person is a listed approver (say
  which team, and that their own agreement was the approval); otherwise it
  is a proposal sitting where an approver will see it, and the reply names
  both the team and, if known, who has to say yes.
- **Universal** — never in force yet on landing; it is a draft that needs a
  pull request (PR) and a human review from someone other than whoever
  wrote it. Say so explicitly rather than letting "landed" read as "done."

## Why
Asked directly whether this was happening — "do you clearly tell the human,
and clearly say where?" — the honest answer was no: the tools' own output
technically carried enough information to work it out, but nothing required
a session to actually relay it, and nothing stopped a summary that named the
practice without naming its level or status. That gap is exactly the kind
this catalogue exists to close: the design plan already said "the proposer
is told immediately what happens next... never leave the person who raised
it guessing" (PRACTICE_ENGINE_PLAN.md, Stage 4), but that was narrative
intent, not an enforceable rule a session could be checked against. This
practice is that intent, made explicit and citable.

## Story
A session had built the individual/team/universal creation pipeline and
used it repeatedly across a working session, landing and proposing several
practices along the way. Asked afterward to confirm, plainly, that every one
of those had been disclosed to the human with its level and location named,
the honest answer was that this had never been made an explicit requirement
— it happened to come across clearly in that particular conversation, but
nothing in the tooling or the instructions actually guaranteed it would
happen again, on a different practice, in a different session. The fix
went into the tools themselves (`DISCLOSE TO THE HUMAN:` lines,
unconditionally printed) rather than trusting a session's own judgment to
remember, since a rule about what a *reply* contains cannot be verified by
scanning a repo's tree — only by the tool that generates the sentence in
the first place, every time it runs.

## Install
`tools/precedent_land.py` and `tools/precedent_candidate.py` print the
`DISCLOSE TO THE HUMAN:` line unconditionally in every code path that lands
a practice or raises a candidate — no separate install step; it ships with
the creation pipeline itself. `tools/verify_harness.py`'s
`check_creation_pipeline_fires` asserts the marker appears for every level.
