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
# IT ALSO CARRIES THE HARD REQUIREMENTS (2026-09-13). The blocking half of
# the reply gate reads each source's reply_check.json; the same file is
# printed here, verbatim, because a Stop hook fires after the reply has
# already been shown to the person -- so a refusal costs them the reply
# twice. The requirement has to arrive before the reply, not after it.
#
# BRIEF, not the full Rules, and that is a budget decision rather than a
# taste one: the reply gate's full text is thousands of tokens and this
# fires on every single prompt (practice: session-load-budget). One line per
# practice, resident ones skipped because they are in the loader block
# already, and a pointer to the full text for the session that needs it.
#
# IT PASSES THE TRANSCRIPT ON (2026-09-28), so the gate can say whether a
# size-conditioned requirement -- the Boildown's compact offer -- is owed in
# THIS reply, instead of telling the session to wait for a stop hook that
# never says. The hook's JSON payload names the transcript; stdin is read
# only when it is not a terminal, so a hand run does not hang.
#
# Exits 0 unconditionally — a UserPromptSubmit hook that exits non-zero eats
# the person's message.
set -uo pipefail
payload=""
[[ -t 0 ]] || payload="$(cat 2>/dev/null || true)"
transcript="$(printf '%s' "$payload" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("transcript_path") or "")
except Exception: pass' 2>/dev/null || true)"
export PRECEDENT_TRANSCRIPT_PATH="$transcript"
root="$(git rev-parse --show-toplevel 2>/dev/null || echo "${CLAUDE_PROJECT_DIR:-.}")"
for d in "$root/tools" "$root/process/upstream/tools"; do
  if [[ -f "$d/precedent_gate.py" ]]; then
    python3 "$d/precedent_gate.py" reply --brief 2>/dev/null || true
    break
  fi
done
exit 0
