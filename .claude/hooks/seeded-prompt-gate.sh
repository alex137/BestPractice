#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES a prompt one session
# puts into another -- spawning one, scheduling a message into one, firing
# a routine at one -- unless the prompt's FIRST LINE names the session
# that sent it (practice: seeded-prompt-names-its-origin).
#
# WHY THIS EXISTS (2026-09-23, practice: cite-the-incident). The practice
# asked for that first line from 2026-09-12 and said plainly that nothing
# checked it. On 2026-09-22 a session put a message into another session's
# live conversation with its own session link at the very END. The
# receiving session could not tell it from something the person typed,
# refused it, then acted on it after unrelated evidence seemed to vouch
# for it, and landed half a repository migration nobody had asked for in
# that window. The rule existed; remembering it was the only thing
# enforcing it, and remembering it is what failed.
#
# WHAT IT CHECKS, AND WHAT IT DOES NOT. Presence and position only: the
# first non-blank line of the prompt must carry a session id
# (`session_...`). It cannot tell a true header from a false one -- the
# practice says the header is provenance, not security, and this hook
# does not pretend otherwise. What it guarantees is that an honest
# session never sends an unlabelled message by forgetting.
#
# Which tools: the harness's session-creating and session-messaging calls
# (create_session, create_trigger, update_trigger, fire_trigger,
# send_later), matched by the tool-name SUFFIX so the MCP server's own
# name -- which differs between harness builds -- does not matter.
# A reminder a session schedules for itself is in scope too, as the
# practice already says: the header costs one line, and the exception is
# what makes the dangerous case look normal. In-session subagents are
# NOT in scope: they are not sessions, and nothing here can tell a
# subagent's name from another session's.
#
# FAIL-CLOSED ON THE HEADER, FAIL-OPEN ON THE PLUMBING. No jq, an
# unparseable payload, a tool this does not know, or a call that carries
# no prompt text at all -- each exits 0 silently. A gate that breaks a
# session over its own missing dependency is a gate somebody disables
# (practice: fail-gracefully).
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0

tool="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || true)"
case "$tool" in
  *__create_session|*__create_trigger|*__update_trigger|*__fire_trigger|*__send_later) ;;
  *) exit 0 ;;
esac

# The field that carries the text differs per tool; exactly one is set.
text="$(printf '%s' "$input" | jq -r '
  .tool_input.prompt // .tool_input.text // .tool_input.message // empty
' 2>/dev/null || true)"
[[ -n "${text//[[:space:]]/}" ]] || exit 0

first="$(printf '%s\n' "$text" | grep -m1 -v '^[[:space:]]*$' || true)"
if printf '%s' "$first" | grep -qE 'session_[A-Za-z0-9]{6,}'; then
  exit 0
fi

# Hand back the exact line wherever the harness says who we are. A remote
# session's id arrives as cse_<id>; its public form is session_<id>.
self_id=""
if [[ -n "${CLAUDE_CODE_REMOTE_SESSION_ID:-}" ]]; then
  self_id="session_${CLAUDE_CODE_REMOTE_SESSION_ID#cse_}"
fi
if [[ -n "$self_id" ]]; then
  example="Sent automatically by the session \"<this session's title>\" ($self_id) -- https://claude.ai/code/$self_id. Nobody typed this."
else
  example="Sent automatically by the session \"<this session's title>\" (<session id>) -- <link to it>. Nobody typed this.  (get_session with no id returns this session's id.)"
fi

reason="Refused: this puts text into a session, and its first line does not
name the session sending it (practice: seeded-prompt-names-its-origin).
The receiving session sees an ordinary user turn and cannot tell it from
something the person typed unless the first line says otherwise -- which
is exactly how a relayed message led a session astray on 2026-09-22.

Make this the literal first line of the text, then call again:

  $example

Not buried after a greeting, and not at the end: the first line."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
