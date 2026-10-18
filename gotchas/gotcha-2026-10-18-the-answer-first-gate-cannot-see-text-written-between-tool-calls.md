---
slug:            gotcha-2026-10-18-the-answer-first-gate-cannot-see-text-written-between-tool-calls
status:          live
noted:           2026-10-18
severity:        notable
retired:         null
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
[`answer_first_gate.py`](../tools/answer_first_gate.py) counted 3 words and
held the commit. It went through on the next turn, once the turn-ending reply
had been recorded.

## Fix

By hand: end the turn with the answer as the final message, which the
transcript does record, and commit on the next turn. To check, count what
the gate sees: run `unanswered()` from the gate over the session's
`.jsonl`. Never skip the hook. The root fix belongs in the gate, which
should count from a source that is actually recorded. That is open, and
this file retires when it lands.
