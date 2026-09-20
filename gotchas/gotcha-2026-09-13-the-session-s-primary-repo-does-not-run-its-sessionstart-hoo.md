---
slug:            gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The session's PRIMARY repo does not run its SessionStart hooks either, when the harness rooted the session one directory ABOVE it — and this project's own required layout is what causes that.

## Story

**The session's PRIMARY repo does not run its SessionStart hooks either, when
the harness rooted the session one directory ABOVE it — and this project's own
required layout is what causes that.** Four Precedent repos side by side under
`/home/user` is what a team source needs, since it resolves as a sibling
clone; the harness then sets the session root to that parent, every hook path
written as `$CLAUDE_PROJECT_DIR/.claude/hooks/…` resolves to nothing, and **a
hook whose path does not exist is not an error anybody sees.** On 2026-09-08
that silently cost the commit identity, the global backstop, the freshness
guard, the `pip install`, the path-trigger channel — and
`.precedent/SESSION_PRACTICES.md`, the only route by which private team and
individual practices reach a session at all. **Do not diagnose this from
`env`** — `CLAUDE_PROJECT_DIR` is usually not set in a tool shell, so reading
it proves nothing either way. Test the effects:
[tools/precedent_session_check.py](../tools/precedent_session_check.py) checks
each guarantee by what it left behind, and `--apply` runs the three hooks by
hand. It cannot itself be a hook, for the obvious reason.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
