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

# Every session, local ones included (Morgan, 2026-09-28, strength:
# decided). Until then this exited unless CLAUDE_CODE_REMOTE=true, on the
# reasoning that a local machine manages its own packages -- which is true
# of the pip install and of nothing else bootstrap.sh does. So a local
# Claude Code session never had its declared shared sets cloned, its
# checkout fast-forwarded, its loader block checked, or any of the
# session-start notices printed.
#
# A local session is marked rather than skipped: PRECEDENT_LOCAL_SESSION=1
# tells bootstrap.sh to leave out the steps that belong to a hosted
# container and not to a person's own machine -- the package install, and
# the machine-wide settings commit-identity.sh writes. bootstrap.sh says
# which, at its top.
#
# A bootstrap.sh that never heard of the variable would do all of them
# anyway, so locally it runs only when it names PRECEDENT_LOCAL_SESSION. That
# is a real case, not a hypothetical one: this hook is refreshed by Update
# Vendors, while a bootstrap.sh the repo has edited is only reported and
# never rewritten, so the two can arrive a release apart.
bootstrap="${CLAUDE_PROJECT_DIR:-.}/tools/bootstrap.sh"
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  export PRECEDENT_LOCAL_SESSION=1
  if ! grep -q 'PRECEDENT_LOCAL_SESSION' "$bootstrap" 2>/dev/null; then
    if [ -f "$bootstrap" ]; then
      echo "NOTE: local session -- tools/bootstrap.sh was NOT run: this copy predates local sessions (it never reads PRECEDENT_LOCAL_SESSION), so it would pip install into this machine's own environment. Take the local-session block from Precedent's templates/bootstrap.sh into it; Update Vendors names what it lacks." >&2
    fi
    exit 0
  fi
fi

exec bash "$bootstrap"
