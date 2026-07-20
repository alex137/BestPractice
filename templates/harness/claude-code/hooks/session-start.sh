#!/bin/bash
# Claude Code adapter: SessionStart hook wrapper. Install to
# .claude/hooks/session-start.sh (wired by the adapter's settings.json).
# All real setup lives in the harness-neutral tools/bootstrap.sh — keep this
# wrapper free of content so other harnesses share the same bootstrap.
set -euo pipefail

# Web/remote sessions only — local machines manage their own packages.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

exec bash "${CLAUDE_PROJECT_DIR:-.}/tools/bootstrap.sh"
