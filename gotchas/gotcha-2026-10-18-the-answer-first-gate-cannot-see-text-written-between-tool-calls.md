---
slug:            gotcha-2026-10-18-the-answer-first-gate-cannot-see-text-written-between-tool-calls
status:          retired
noted:           2026-10-18
severity:        notable
retired:         2026-10-19
retires_when:    "tools/answer_first_gate.py counts the answer from something the harness reliably records, or the harness writes every text block to the transcript before the next tool call runs"
---
## Symptom

Every `git commit` is refused with "ANSWER FIRST: the person's latest
message asks something, and it has not been answered yet", even after the
session has written the person a long answer in the same turn. Rewording the
answer, or making it longer, changes nothing.

## Story

**2026-10-18.** Morgan's message asked for a rule change and ended with
"Just tell me", which the gate reads as a question. The session wrote him
two answers, well over the gate's 50 words, between tool calls, and the
commit was refused three times. Reading the transcript the gate reads showed
why: of the session's text blocks that turn, only a three-word one ("Now the
edits.") had been written to it. The longer ones were shown to the person
but never reached the file, so
[`answer_first_gate.py`](https://github.com/alex137/BestPractice/blob/staging/tools/answer_first_gate.py) counted 3 words and
held the commit. It went through on the next turn, once the turn-ending reply
had been recorded.

**2026-10-19, measured again.** The lag fix that landed the same night
(waiting up to three seconds for the guarded call to be recorded) does not
reach this: the text is not late, it is never written. In one session,
every mid-turn text of 25 to 32 words was in the transcript and every one
of about 45 words or more was not, minutes later or ever, whether or not
its tool call was refused; the turn-ending reply was. The session's
200-word answer was refused four times running. Morgan: "if you write a
longer answer for me, IS THERE A REASON TO NOT GIVE IT TO ME IMMEDIATELY?
WHY WAIT OR WHY REFUSE?", then "okay, go fix" (strength: decided). The gate
now refuses once per question and lets the next change through once its
own refusal is in the transcript, so the trap below can cost one refused
call, never a loop. Retired the same day.

## Fix

By hand: end the turn with the answer as the final message, which the
transcript does record, and commit on the next turn. To check, count what
the gate sees: run `unanswered()` from the gate over the session's
`.jsonl`. Never skip the hook. The root fix belongs in the gate, which
should count from a source that is actually recorded. That is open, and
this file retires when it lands.
