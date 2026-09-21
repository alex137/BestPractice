#!/bin/bash
# Claude Code adapter: SessionStart hook wrapper. Install to
# .claude/hooks/session-start.sh (wired by the adapter's settings.json).
# All real setup lives in the harness-neutral tools/bootstrap.sh — keep this
# wrapper free of content so other harnesses share the same bootstrap.
#
# ITS PARALLEL ON EVERY OTHER HARNESS IS tools/bootstrap.sh. Codex,
# gemini-cli and grok-build have no SessionStart hook; templates/harness/
# README.md tells each of them to wire that script instead, so a step added
# HERE and not THERE reaches one harness out of four. That is not
# hypothetical: until 2026-09-21 this hook ran seven things and the script
# ran three, and the difference included .precedent/SESSION_PRACTICES.md --
# every team and individual practice in force, which AGENTS.md's Standing
# instruction tells every session to read and which no non-Claude session
# had ever been given. Adding a step here? Add it there, or write the
# reason it cannot travel into templates/harness/PARALLELS.md, which is
# checked (claude-only-surface-has-a-parallel) and re-judged on every very
# deep check.
set -euo pipefail

# Web/remote sessions only — local machines manage their own packages.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

exec bash "${CLAUDE_PROJECT_DIR:-.}/tools/bootstrap.sh"
