---
title:         "Plan: detection at the end of a turn"
kind:          proposal
status:        drafted
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Make the system notice candidate practices on its own — a closing line in every reply that names a candidate or says there was none, plus a phrase detector on the person's own messages.
---
# Plan: detection at the end of a turn

**The system was designed so that practices arrive on their own, and that
half was never wired up.** [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)
states the shape plainly — *"the automation sits at the two ends: the system
notices, and the system enforces. A human approves in the middle."*
Enforcement got built out heavily: gates, checks, harnesses, audits.
Approval got built. **Noticing got a tool and no trigger.**

This proposes two changes that close that gap, both riding on machinery that
already exists and already fires.

## What is actually wrong

**Stage 1 of the creation pipeline is built and unreachable.**
[tools/precedent_detect.py](../tools/precedent_detect.py) implements three of
the plan's seven detection signals and works — but **nothing invokes it.**
Outside its own test in [tools/verify_harness.py](../tools/verify_harness.py)
and two generated index tables, it is referenced nowhere: no hook calls it,
no gate cites it, the occasion index has no entry pointing at it.

**The evidence that this matters is the candidate record itself.** Across all
four private sources there are **two candidate files, both dated
2026-09-02** — the day the pipeline was built — both raised by the same
deep-check session deliberately exercising the tooling rather than by anyone
noticing anything. Nothing since. Every practice that has landed in the weeks
after arrived by the person saying something and a session writing it up.

**The mechanical cause is that the detection practices sit on gates that
cannot fire.** `mistakes-become-rules` is registered to the `review` gate,
which has no invocation point anywhere. Its own Rule text argues against that
placement in so many words — *"The trigger is the fix, not the review: most
defects here are never reviewed, they are just mentioned and repaired, and a
rule that waits for a review never fires on them."* **The text learned the
lesson and the wiring did not follow.**

## Background: what a gate is, and why only two of the four work

A **gate** is a named moment in a session's life. A practice declares which
moments it belongs to in its frontmatter (`gates: ["reply"]`), and
[tools/precedent_gate.py](../tools/precedent_gate.py) prints exactly the rules
registered to a given moment. Gates exist because **no file-path pattern
reaches a moment** — "when you merge" is a point in time, not a file.

| Gate | The moment | Fires by itself? |
|---|---|---|
| `merge` | Merging a branch. | **No.** Cited only. |
| `review` | Reviewing work, or finding a defect. | **No.** Cited only. |
| `push` | Before pushing. | **Yes** — a git pre-push hook. |
| `reply` | Ending a turn and writing the reply. | **Yes** — twice: a prompt-submit hook at turn start and the Stop hook at turn end. |

**The split is not an oversight and it is not closeable.** No harness adapter
has a merge-time or review-time interrupt, so there is nothing to wire;
[precedent_gate.py](../tools/precedent_gate.py)'s own header calls this
*"this channel's honest, permanent shape"*. A rule on `merge` or `review` loads only when a session
reads the standing instruction and chooses to run the command.

**This is the whole reason the proposal targets `reply`.** It is the one
moment that arrives unconditionally, at the end of every turn, with the
session's own work still in front of it.

## The design

### Part 1 — a closing line that names a candidate, or says there was none

**The judgment is soft; the disclosure is hard.** A new practice on the
`reply` gate asks the session, as it writes its closing section, whether
anything in this turn's work was a rule rather than a one-off. That judgment
is advisory — the session may honestly conclude nothing was. **What is
enforced is that the reply says which.**

The enforcement rides on [tools/precedent_reply_check.py](../tools/precedent_reply_check.py),
which reads a `reply_check.json` from each resolved source and **refuses the
turn** when a declared requirement is unmet. That mechanism already carries
the `## Next Steps` heading and the archive sentence. A third requirement —
one of two phrases, one naming a candidate and one saying there was none —
is the same shape and needs no new machinery.

**The argument for hard disclosure rather than hard detection is one this
reply-check mechanism already rests on.** The requirement it carries today is
a closing sentence that must say one of two things, precisely because a reply
that omits the sentence and a reply that says "nothing is outstanding" look
identical on the page and mean opposite things. Identical reasoning here.
Forcing a session to *find* something trains it to invent; forcing it to
*say which of two things happened* costs one sentence and cannot be complied
with accidentally.

**At most one candidate reaches the reply. Any others are written, not
raised.** Candidates are designed to cost nothing —
[spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md): *"creating one costs
nothing; ignoring one costs nothing"*, and no loader ever reads
`candidates/`. So the cap protects the reader's attention, not the
repository, and it belongs on what is surfaced rather than on what is
recorded. Write down everything worth acting on; raise only what the reader
must decide now.

### Part 2 — a phrase detector on the person's own messages

**The plan calls an explicit standing instruction *"the highest-signal moment
the system will ever get"*, and today it is handled ad hoc.**
`precedent_detect.py explicit-instruction` already detects it, over supplied
text, with patterns deliberately narrowed to the standing-rule shape rather
than the bare words. It has never been connected to anything.

A `UserPromptSubmit` hook pipes the incoming message through it and surfaces
any hit to the session before the turn begins. That hook type is already in
use here — the freshness guard runs in it — so this is wiring, not
invention.

**The two parts catch different things and do not overlap.** Part 2 catches
rules the person states; it lowers the cost of writing up a decision they
have already made, but they remain the originator. **Part 1 catches rules
nobody stated** — a fix that took three attempts, a correction absorbed
without comment, a trap hit and worked around. That is the half currently
missing entirely, and it is the reason Part 1 leads.

## What this does not do

- **It does not let a session mint a practice.** Detection produces a
  candidate; approval stays where
  [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s Stage 4 puts it.
  `disclose-landing` already forces any landing to be stated out loud.
- **It does not touch the `merge` or `review` gates' reach.** Those stay
  cited-only for the reason above.
- **It does not add a check-failure-history signal.**
  `repeated-check-failure` needs a persistent log of runs over time, which
  nothing here keeps; [precedent_detect.py](../tools/precedent_detect.py) names that gap in its own
  header
  and this proposal leaves it open.

## The open question, stated rather than buried

**A session judging its own finished work is the exact task shape
[ATTENTION_CEILING.md](ATTENTION_CEILING.md) measured at 50–54% recall,
three separate ways.** That document also already reasoned about this
specific case, in its *"Does the ceiling reach Stage 1 and Stage 3?"*
section, and argued the shapes differ: one item with its own fresh evidence
and a cheap closed question is structurally the framing that did **not** hit
the ceiling, unlike a whole-catalogue sweep over a finished diff. It marked
that reasoning as reasoning, not measurement, and deferred the test.

**This proposal is a cheap way to finally run it.** A candidate file is a
dated record, so after some weeks of real use the questions are countable:
how many were raised, how many promoted, and how many rules the person still
had to catch themselves. If the ceiling does reach this task, the closing
line will show it — as a long run of honest "nothing this session" against
practices that arrived by the old route anyway.

## Origin

Morgan raised it, 2026-09-14, asking whether the system looks for practices
on its own or only acts when told. The investigation that produced the
evidence above was the answer. **The closing-line shape is his** — he
proposed hanging detection off the `## Next Steps` section already enforced
at the end of every reply, capped at one per session so it cannot become
noise. He chose to include Part 2 alongside it; `strength: decided`.
