---
slug:            gotcha-2026-09-13-the-absence-of-claude-hooks-is-not-evidence-that-a-repo-s-ho
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are missing — resolve the paths its settings.json actually declares.

## Story

**The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
missing — resolve the paths its settings.json actually declares.** A set can
wire its hooks to a tracked `bootstrap/` directory on purpose, and from a
directory listing that looks identical to a set whose hooks were never
installed. 2026-09-09: a session called four working hooks silently dead on
exactly that reading. **Both halves are mechanical now** — `python3
tools/precedent_check.py --only declared-hooks-exist` resolves every declared
`$CLAUDE_PROJECT_DIR` hook path and fails on one that is missing or not
executable, and
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py) does
the same per attached source. Full story:
[record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) entry 37.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
