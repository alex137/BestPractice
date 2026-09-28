---
slug:              todo-2026-09-28-very-deep-check-pass-1-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 1 found and the same day did not
fix. Everything else it found (update, deletion, migration, practice-move,
adapter and install findings, about fifty) was fixed that day on
`claude/very-deep-check-2amsjs`, each with a planted harness case where a
mechanism changed.

- **A consumer's install-once files still drift from a fresh install**
  beyond `.gitignore` (which the update now completes): the PR template and
  `TODO.md` an old install instantiated keep old wording, and nothing
  reports it. A diff against the current templates, reported, never
  written, would do.
- **In local Claude Code a consumer's SessionStart hook does nothing**: the
  shipped `session-start.sh` exits unless `CLAUDE_CODE_REMOTE=true`
  ("local machines manage their own packages"). The installed AGENTS.md now
  says so; whether local sessions should run `bootstrap.sh` automatically is
  a decision for Morgan, since it changes every local session's start.
