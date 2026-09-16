---
slug:            gotcha-2026-09-11-the-absence-of-claude-hooks-is-not-evidence-that-a-repo-s-ho
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are missing

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
  missing. Resolve the paths its settings.json actually declares — a
  directory listing cannot answer the question.** 2026-09-09: a session
  measured that an individual practice source had a `.claude/settings.json`
  and no `.claude/hooks/` directory at all, and concluded from that pair
  alone that the set's freshness guard and commit-identity backstop had been
  declared and silently off for its whole life. **They had not been.** That
  set wires four hooks to its own tracked `bootstrap/` directory, on purpose,
  so that one copy exists and nothing can drift from it; all four resolve,
  exist, and are executable. A path-resolving check across all five private
  sets then found every declared hook present and executable in every one.
  The wrong reading was easy because it names a real failure — a hook whose
  path does not exist really is silent, per the two entries above — and the
  two states look identical from a listing.
  **Both halves are mechanical now.**
  `python3 tools/precedent_check.py --only declared-hooks-exist` resolves
  every `$CLAUDE_PROJECT_DIR` hook path a settings.json declares and fails on
  one that is missing or not executable, in any repository the engine is
  vendored into.
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  does the same per attached source and **refuses to "repair" a hook declared
  outside `.claude/hooks/`**: its own first version assumed the standard
  layout, and against that individual set would have installed exactly the
  second copy its comment exists to prevent.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
