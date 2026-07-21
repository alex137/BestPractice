#!/bin/bash
# SessionStart hook for the BestPractice repo itself (practice 13).
# cmarkgfm gives doc_lint its exact GitHub-renderer strikethrough check and
# the deck engine its markdown renderer.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
pip install --quiet cmarkgfm 2>/dev/null || \
  echo "WARN: pip install failed - doc_lint strikethrough check and .md deck slides degrade" >&2
