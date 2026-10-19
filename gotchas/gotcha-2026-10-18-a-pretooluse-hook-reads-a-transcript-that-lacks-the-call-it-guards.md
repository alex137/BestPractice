---
slug:            gotcha-2026-10-18-a-pretooluse-hook-reads-a-transcript-that-lacks-the-call-it-guards
status:          live
noted:           2026-10-18
severity:        null
retired:         null
retires_when:    "Claude Code writes an assistant message to the transcript before it runs PreToolUse hooks for the tool calls in it"
---
## Symptom

A PreToolUse hook that reads `transcript_path` does not find the tool call it was started for, or the text the session wrote just before that call. A hook that judges "what has the session said so far" undercounts by exactly the message being guarded.

## Story

On 2026-10-18 a session in a consuming repo answered a question in about a hundred words and then tried to merge. [tools/answer_first_gate.py](../tools/answer_first_gate.py) counted 11 words and refused three times. A probe in the hook, logging the payload's `tool_use_id` against the transcript, showed the cause: at PreToolUse time the call being checked was never in the transcript, and neither was the sentence written right before it, which landed one line past where the hook had read. Waiting in the hook, the call usually showed up within a second; once it had not after four.

## Fix

Use the payload's `tool_use_id` as the marker: poll the transcript, briefly, until it carries that id (the message's text lands before its tool call), then read. If it never arrives inside the bound, treat the transcript as provably behind and fail open. The answer-first gate's `recorded()` does this with a 3-second bound, and only on the path that would otherwise refuse, so an allowed call never waits.
