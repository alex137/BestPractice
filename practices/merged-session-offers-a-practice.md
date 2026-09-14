---
slug:        merged-session-offers-a-practice
title:       "A merged session offers one practice on its way out, or none"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a merged session closes as ready to archive"
gates:       ["reply"]
index_clause: "one candidate at most, in the closing list, from this session's work"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       2026-09-14
approved_by: "Morgan F, 2026-09-14 -- he set every condition on it (a merge
  happened, the session is ready to archive, one per session, never forced) and
  said to implement it; `strength: decided`."
---
## Rule
**A session that merged something, and is closing as ready to archive, adds
at most ONE bullet to its closing list naming a practice its own work turned
up.** The bullet says what the rule would be, in one sentence, and at which
level it would sit; the candidate is raised properly in the same turn with
[precedent_candidate.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_candidate.py),
so the offer in the reply is a pointer to a real record rather than a remark.

**All four conditions hold, or nothing is said at all.**

1. **Something was merged.** A conversation that merged nothing was a
   conversation; there is no finished work to draw a rule from.
2. **The reply closes as ready to archive.** A session still in flight is a
   session someone is working in, and a practice suggestion at that moment
   is an interruption.
3. **At most one per session** — not one per reply.
4. **The rule came from THIS session's own work.** Not a good idea in
   general, not something noticed in another thread, not a gap in the
   catalogue somebody could have named on any day.

**Nothing is offered when nothing was found, and that is the normal case.**
Most sessions are repetitive work that produces no rule. A reply with no
bullet is this practice being followed, not skipped — and a session that
manufactures a candidate to look thorough has failed it outright. The
proportionality test is [mistakes-become-rules](mistakes-become-rules.md)'s:
a systemic cause, or real cost.

**Already landed the practice this session?** Then it is already stated out
loud ([disclose-landing](disclose-landing.md)) and there is nothing to
offer. Say that in one line rather than offering it twice.

## Detail
**The mechanical half is
[precedent_close_detect.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_close_detect.py),
and it fires on evidence rather than on the occasion.** It measures all four
conditions from the session's own transcript — the merge from the tool calls
that performed it, the close from the reply being written, the cap from
whether a candidate was already offered — and then runs
[precedent_detect.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_detect.py)'s
Stage-1 signals over material scoped to this session: the person's own
messages, and commits made since it started. **Only a positive finding
blocks.** It is not registered in [precedent_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_check.py)'s registry and `checked_by` is null, for the same reason every other reply-gate practice's is: what it checks is a conversation, and no tree-scoped check has ever been able to read one. A session with nothing to offer is never interrupted and is never
asked to say so, which is the difference between this and a closing line
that has to be written either way.

**What a signal is worth is the session's call, and the hook says so in its
own message.** A detector hit is evidence that something was said in a
standing-rule shape, or that work was undone — neither is a verdict. The
honest answer to most hits is one line saying it was a one-off.

**The phrases are declared, never compiled in.** "You can archive this
session" is one person's closing convention. The engine reads a
`close_detect.json` from each resolved source, exactly as
[precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_reply_check.py)
reads `reply_check.json`, and a repo whose sources declare none is never
blocked by this ([rule-level-by-reach](rule-level-by-reach.md)).

**This is the `reply` gate because it is the only closing moment that
arrives by itself.** The `merge` gate would be the obvious home and no
harness has a merge-time interrupt, so a rule registered there loads only
when a session chooses to run the command.

## Why
The engine was designed with automation at both ends — the system notices, a
human approves, the system enforces. Enforcement was built out heavily and
**noticing was built and never wired up**: Stage 1's detector existed for
weeks with nothing calling it, and across every attached source exactly two
candidate files were ever raised, both on the day the pipeline was built.
Every practice that landed in the weeks after arrived because one person
said something. That is the gap this closes, and it closes it at the one
moment where the session's own finished work is still in front of it.

The four conditions are all restraint, and the restraint is what makes the
mechanism survivable. A suggestion engine that fires mid-session trains
people to ignore it; one that fires on every reply produces filler; one that
demands an answer either way turns a judgment into a form field. Firing once,
at the end, only on real evidence, costs a reader one bullet they can ignore.

## Story
Morgan, 2026-09-14, on the practice engine he had been feeding by hand for
weeks: *"I love the methodology of turning what we decide into Practices to
be followed or enforced, but it seems like I'm always the one making the
suggestions. Does the system, as it is now, look for them?"*

**It did not.** The investigation that answered him is written up in
[spec/PRACTICE_DETECTION.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRACTICE_DETECTION.md).
Stage 1's detector was referenced nowhere outside its own test and two
generated index tables: no hook called it, no gate cited it, the occasion
index had no entry pointing at it. The detection practice that should have
covered it, [mistakes-become-rules](mistakes-become-rules.md), sat on the
`review` gate, which has no invocation point anywhere — while its own Rule
text argued against that placement in so many words.

**The shape of the fix is his, and so is every limit on it.** He proposed
hanging it off the closing list already enforced at the end of every reply,
capped at one per session, *"in a way that's not forced -- often a lot of
work will be repetitive and won't have any."* Then, on the write-up, he
narrowed it further: not one per reply but one per session; only in the
final message after a merge, *"if there wasn't, we were just talking!"*;
only when it can really find something *"based on just that conversation
(shouldn't be random stuff from other conversations)"*; and only alongside
the sentence that says the session is ready to archive — *"if it's not ready
to be archived, it's not yet ready for the suggestion - I don't want to
DISTRACT people working on something to propose practices."*

The first draft of the mechanism reported a merge on every session that
started cleanly: its pattern was `\bgit\s+merge\b`, and `\b` matches inside
`merge-base`, which the freshness guard runs at session start. Caught by
reading the regex against the session's own opening commands rather than by
a test.

## Install
Nothing to install where the engine is already wired: the Stop hook that
runs [precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_reply_check.py)
runs this alongside it. To turn it on for yourself, declare the phrases in a
`close_detect.json` at the root of whichever source carries your closing
convention:

```json
{
  "practice": "merged-session-offers-a-practice",
  "archive_ready_one_of": ["You can archive this session"],
  "closing_heading_matching": "next step",
  "candidate_marker": "Practice candidate",
  "why": "so a finished session offers what it learned, once"
}
```

`python3 tools/precedent_close_detect.py --explain` prints what is declared
and, where nothing is, says so plainly.
