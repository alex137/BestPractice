---
slug:              todo-2026-09-07-the-branch-sweep-and-the-source-refresh-tool-disagree-about-
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the work."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- **The branch sweep and the source-refresh tool disagree about what is in
  scope, and the sweep is the narrower one.** Found 2026-09-07 by the
  [very deep check](../spec/VERY_DEEP_CHECK.md), which reported four unmerged
  branches and missed a fifth.
  [tools/very_deep_check.py](../tools/very_deep_check.py) scans this checkout
  plus the sources [precedent.json](../precedent.json) declares.
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  discovers every attached Precedent repo, declared or not. So
  `precedent-team-tms` — attached, a real Precedent repo, but nobody's
  declared source here — was refreshed by one tool and never swept by the
  other, and its own `claude/pre-launch-audit-fixes-7wumzx` (12 commits
  ahead) went unlisted.
  [practices/very-deep-check.md](../practices/very-deep-check.md) is explicit
  that "scope is every Precedent repo in the session, not this checkout
  alone", so the tool is narrower than the practice it implements. Give it
  the same discovery `precedent_refresh_sources.py` already uses rather than
  a second one.
  **Blocked on:** nothing but the work.

## How It Closes

Not open until: nothing but the work.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
