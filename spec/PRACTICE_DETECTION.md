---
title:         "Plan: detection at the end of a turn"
kind:          proposal
status:        executed
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Makes the system notice candidate practices on its own — at the close of a session that merged something and is ready to archive, one candidate at most, and only when a detector found something in that session's own material. Built 2026-09-14.
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

## What was built

**Morgan narrowed the design before it was built, and every limit he set is
a measured condition rather than a line of guidance.** The first draft had a
closing sentence on every reply — one phrase naming a candidate, one saying
there was none. He replaced that with something much quieter: *"this should
just be a bullet point within that section, targeting a maximum of 1 per
session, without forcing it."*

**One bullet, in the closing list, and only when all four of these hold:**

| Condition | Why | How it is measured |
|---|---|---|
| This session **merged** something | *"if there wasn't, we were just talking!"* | the transcript's own tool calls — `git merge`, `gh pr merge`, the GitHub merge tool |
| The reply says the session is **ready to archive** | *"if it's not ready to be archived, it's not yet ready for the suggestion"* | the declared archive sentence appears in the reply being written |
| **One per session**, not one per reply | so it cannot become a drip | no earlier reply this session carried the candidate marker |
| A detector found something **in this session's own material** | *"shouldn't be random stuff from other conversations"* | the person's own messages, and commits made since the session started |

**The fourth condition is what replaced hard disclosure**, and it is a
better answer than the one it replaced. Because the hook fires only on
positive evidence, a session with nothing to offer is never interrupted —
and is never made to say it found nothing either. The reply of an ordinary
session is exactly what it would have been.

### The pieces

- **[tools/precedent_close_detect.py](../tools/precedent_close_detect.py)** —
  the trigger Stage 1 never had. It reads the Stop hook's payload, measures
  all four conditions against the session transcript, and blocks the close
  only when every one of them holds, naming what it found and saying plainly
  that a one-off is a valid answer.
- **[practices/merged-session-offers-a-practice.md](../practices/merged-session-offers-a-practice.md)** —
  the universal practice, on the `reply` gate.
- **[tools/precedent_detect.py](../tools/precedent_detect.py)** — refactored
  so its signals are callable functions rather than CLI printers. Half of
  why Stage 1 was never invoked is that there was nothing to call.
- **The Stop hook** — in
  [.claude/hooks/stop-git-check.sh](../.claude/hooks/stop-git-check.sh) and
  in the template it is instantiated from
  ([templates/harness/claude-code/hooks/stop-git-check.sh](../templates/harness/claude-code/hooks/stop-git-check.sh)),
  alongside the reply check it already ran.
- **A `close_detect.json` per source** — the phrases are declared, never
  compiled in, exactly as `reply_check.json` already works. A repo whose
  sources declare none is never blocked by any of this.

**Blocking rather than printing is forced by the moment, not chosen.** A
Stop hook's stdout does not reach the model on a clean exit — the same
finding that put the reply gate's brief in a `UserPromptSubmit` hook — so an
advisory print at the close reaches nobody. Exit 2 is the only channel that
arrives, and firing it on evidence only is what keeps that from being a tax.

### Where Part 2 went

The original Part 2 was a `UserPromptSubmit` hook running the
explicit-instruction detector on each incoming message. **That surface
contradicts the rule Morgan set** — *"I don't want to DISTRACT people
working on something to propose practices"* — so the detector runs over the
person's messages at the **close** instead, where it is subject to all four
conditions above. Nothing about the signal was dropped; only the moment it
is raised at moved to the end.

## What this does not do

- **It does not let a session mint a practice.** Detection produces a
  candidate; approval stays where
  [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s Stage 4 puts it.
  `disclose-landing` already forces any landing to be stated out loud.
- **It does not touch the `merge` or `review` gates' reach.** Those stay
  cited-only for the reason above.
- **It does not add a check-failure-history signal.**
  `repeated-check-failure` needs a persistent log of runs over time, which
  nothing here keeps; [precedent_detect.py](../tools/precedent_detect.py)
  names that gap in its own header and this leaves it open.
- **It cannot see a rule nobody said and no commit undid.** The session's own
  judgment about its finished work is the practice's Rule text, loaded at the
  `reply` gate and advisory — the mechanical half fires on evidence, and
  evidence is narrower than noticing. That gap is the open question below.

## The open question, stated rather than buried

**A session judging its own finished work is the exact task shape
[ATTENTION_CEILING.md](ATTENTION_CEILING.md) measured at 50–54% recall,
three separate ways.** That document also already reasoned about this
specific case, in its *"Does the ceiling reach Stage 1 and Stage 3?"*
section, and argued the shapes differ: one item with its own fresh evidence
and a cheap closed question is structurally the framing that did **not** hit
the ceiling, unlike a whole-catalogue sweep over a finished diff. It marked
that reasoning as reasoning, not measurement, and deferred the test.

**This is a cheap way to finally run it.** A candidate file is a
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

**He then narrowed it, same day, and said to build it.** Not one per reply
but one per session; only in the final message after a merge; only from that
conversation's own material; and only alongside the sentence that says the
session is ready to archive. That last condition is the one that turned the
design from a closing line into something that mostly says nothing, and it
is his: *"I don't want to DISTRACT people working on something to propose
practices."* Built the same day; `strength: decided`.
