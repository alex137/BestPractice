#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES a Bash command running
# `pgrep -f` or `pkill -f`.
#
# WHY THIS EXISTS (2026-10-01, gotchas/gotcha-2026-10-01-a-wait-loop-on-pgrep-f-waits-on-itself.md).
# A session waited for an 11-minute check with
# `while pgrep -f "tools/precedent_push_check.py"; do sleep 10; done`. The
# harness runs every command through a shell whose own command line is the
# command, pattern included, so `pgrep -f` always found that shell and the
# loop never ended: 20 more minutes, until its time limit. The same session
# had already killed its own shell once with `pkill -f` on the same text.
# Morgan asked for a wall rather than a written lesson: "I think we need a
# harder enforcement" (2026-10-01).
#
# Inside this harness, `-f` matches the command running it, every time, so
# there is no case where it does what was meant. Run the long command in the
# background instead (the harness says when it finishes), or wait on its
# process ID: `cmd & pid=$!` then `wait "$pid"`.
#
# FAIL-OPEN ON THE PLUMBING: no jq or an unreadable payload exits 0, the
# same as every gate here (practice: fail-gracefully).
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0

cmd="$(printf '%s' "$input" \
  | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[[ -n "$cmd" ]] || exit 0

# THE COMMAND WITH ITS QUOTED TEXT BLANKED (2026-09-30), so the tests below
# read only what the shell will run. A `|` or `;` inside a quoted argument
# is not a pipe: `grep "a\|git push"` read as a push once, ran the full push
# check for 766 s and refused a read-only grep
# (todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command). Quoted
# strings and heredoc bodies become spaces, newlines kept; everything else
# is unchanged. The same block sits in every hook that asks "does this
# command run X"; verify_harness keeps the copies identical. No python3
# result: the raw command, as before.
bare="$(printf '%s' "$cmd" | python3 -c '
import re, sys
s = sys.stdin.read(); out = []; i = 0; n = len(s)
Q, D, B = chr(39), chr(34), chr(92)
blank = lambda t: re.sub(r"[^\n]", " ", t)
while i < n:
    c = s[i]
    if c == B and i + 1 < n:
        out.append(s[i:i + 2]); i += 2; continue
    if c in (Q, D):
        j = i + 1
        while j < n and s[j] != c:
            j += 2 if (c == D and s[j] == B) else 1
        out.append(c + blank(s[i + 1:min(j, n)]) + (c if j < n else "")); i = j + 1; continue
    m = re.match(r"<<-?[ \t]*([" + Q + D + r"]?)([A-Za-z_]\w*)\1", s[i:])
    if m:
        out.append(m.group(0)); i += m.end()
        nl = s.find("\n", i)
        if nl < 0:
            continue
        out.append(s[i:nl + 1]); i = nl + 1
        end = re.search(r"(?m)^[ \t]*" + re.escape(m.group(2)) + r"[ \t]*$", s[i:])
        stop = i + end.start() if end else n
        out.append(blank(s[i:stop])); i = stop; continue
    out.append(c); i += 1
sys.stdout.write("".join(out))
' 2>/dev/null)" || bare="$cmd"
[[ -n "$bare" ]] || bare="$cmd"

# pgrep or pkill in command position, with -f among its flags (-f, -fa,
# -af, --full). Quoted text is already blanked, so `grep "pgrep -f"` passes.
printf '%s' "$bare" | grep -Eq '(^|[;&|({`[:space:]])(sudo[[:space:]]+)?(pgrep|pkill)([[:space:]]+-[A-Za-z]*f[A-Za-z]*|[[:space:]]+--full)([[:space:]]|$)' || exit 0

reason="This command runs pgrep -f or pkill -f, which this hook refuses.
Here every command runs inside a shell whose own command line holds the
pattern, so -f always matches that shell: a wait loop never ends, and
pkill -f kills the shell it runs in. It cost a session 20 minutes on
2026-10-01 (gotchas/gotcha-2026-10-01-a-wait-loop-on-pgrep-f-waits-on-itself.md).

To wait for a long command, run it in the background and let the harness
say when it finishes. To wait on one you started: cmd & pid=\$!, then
wait \"\$pid\". To see what is running: ps -ef, read, not matched."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
