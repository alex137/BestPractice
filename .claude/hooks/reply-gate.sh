#!/bin/bash
# UserPromptSubmit hook: the reply gate's practices, one line each, at the
# START of the turn.
#
# WHY THIS EXISTS ALONGSIDE THE STOP HOOK. The reply gate's moment is
# "ending a turn and writing the reply", and the only adapter mechanism at
# that moment is Stop — which fires AFTER the reply is composed. Its
# advisory print has therefore never reached the reply it was about: on a
# clean exit Claude Code does not feed a Stop hook's output back to the
# model, so at best it landed on the next turn. UserPromptSubmit is the
# closest moment that is still BEFORE the reply, and its stdout does reach
# the session.
#
# BRIEF, not the full Rules, and that is a budget decision rather than a
# taste one: the reply gate's full text is thousands of tokens and this
# fires on every single prompt (practice: session-load-budget). One line per
# practice, resident ones skipped because they are in the loader block
# already, and a pointer to the full text for the session that needs it.
#
# Exits 0 unconditionally — a UserPromptSubmit hook that exits non-zero eats
# the person's message.
set -uo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null || echo "${CLAUDE_PROJECT_DIR:-.}")"
for d in "$root/tools" "$root/process/upstream/tools"; do
  if [[ -f "$d/precedent_gate.py" ]]; then
    python3 "$d/precedent_gate.py" reply --brief 2>/dev/null || true
    break
  fi
done
exit 0
