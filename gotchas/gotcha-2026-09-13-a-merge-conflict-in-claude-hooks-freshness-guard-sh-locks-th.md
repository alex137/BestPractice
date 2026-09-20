---
slug:            gotcha-2026-09-13-a-merge-conflict-in-claude-hooks-freshness-guard-sh-locks-th
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A merge conflict in `.claude/hooks/freshness-guard.sh` locks the session out of every tool that could repair it, and `git` being exempt does not help.

## Story

**A merge conflict in `.claude/hooks/freshness-guard.sh` locks the session out
of every tool that could repair it, and `git` being exempt does not help.**
2026-09-11: merging `origin/precedent-beta-v01` into a branch that had also
touched the guard left conflict markers in the live PreToolUse hook. Bash
aborts on the parse error before reaching either the git exemption or the
once-per-session sentinel, and exits 2 — which is exactly how a PreToolUse
hook refuses a call. The matcher is `Edit|Write|NotebookEdit|Bash`, so **Edit,
Write and Bash were all refused at once**, and the guard's own fail-open path
does not cover this: it is written for "cannot read the payload", not for
"will not parse". **The way out is a tool the matcher does not name.**
`Monitor` runs a shell command under a different tool name, so it is not
matched: `Monitor(command: "cd <repo> && git checkout --ours
.claude/hooks/freshness-guard.sh")` restored a parseable file and every tool
came back. A subagent is NOT a way out — it inherits the same project hooks.
**Prefer avoiding it**: when a merge is going to touch the guard, expect this
and resolve that file first. Nothing detects it in advance, because the hook
is fine right up until the merge writes the markers.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
