#!/bin/bash
# Claude Code adapter: PreToolUse hook that SAYS, once per branch, when a
# session commits on the branch the harness named when it opened -- never
# refuses. The words and every decision are the tool's
# (tools/precedent_branch_name.py --commit-note); this only finds the
# commit and its repository, and hands the note to the session.
#
# WHY (2026-10-11). The ladder's act names a session's branch with the
# tool, and loads only when a person says "Act" or "Build". In a consumer a
# session took "Great" as its go-ahead, never loaded act, and built,
# pushed and landed a whole feature on claude/eager-volta-hfk5k3. The push
# note (precedent_push_check) comes after the work is built; the first
# commit is the moment every building session passes through, whatever
# word started it. Morgan: the conventions are for people on the ladder,
# not everyone, and the tool asks precedent_ladder before saying anything.
#
# Harness-neutral at the core: the pattern, the once-per-branch marker and
# the message live in the tool; a harness with no session ID gets nothing.
#
# FAIL-OPEN, ALWAYS: no jq, python3 or git, an unparseable payload, a
# repository without the tool, a tool too old for --commit-note -- all exit
# 0 silently. A note is never worth breaking a commit over.
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

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

# Only a real `git commit`, in command position (gotcha-2026-09-21), the
# same test doc-lint-gate.sh applies.
printf '%s' "$bare" \
  | grep -qE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit\b' \
  || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-.}"
cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"

# The repository committed in: `git -C <dir>`, else a leading `cd <dir>`,
# else the tool call's working directory, else the project -- the order
# push-check-gate.sh uses.
target="$(printf '%s' "$cmd" \
  | grep -oE 'git[[:space:]]+-C[[:space:]]+[^[:space:]]+' \
  | head -n1 | sed -E 's/^git[[:space:]]+-C[[:space:]]+//' || true)"
if [[ -z "$target" ]]; then
    target="$(printf '%s' "$cmd" \
      | grep -oE '^[[:space:]]*cd[[:space:]]+[^[:space:];&|]+' \
      | head -n1 | sed -E 's/^[[:space:]]*cd[[:space:]]+//' || true)"
fi
target="${target%\"}"; target="${target#\"}"
target="${target%\'}"; target="${target#\'}"
target="${target/#\~/$HOME}"
base="${cwd:-$project_dir}"
if [[ -z "$target" ]]; then
    target="$base"
elif [[ "$target" != /* ]]; then
    target="$base/$target"
fi

top="$(git -C "$target" rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$top" ]] || exit 0

# That repository's own copy of the tool, so its own ladder answer counts;
# else this engine's.
tool="$top/tools/precedent_branch_name.py"
[[ -f "$tool" ]] || tool="$(dirname "${BASH_SOURCE[0]}")/precedent_branch_name.py"
[[ -f "$tool" ]] || exit 0

note="$(cd "$top" && python3 "$tool" --commit-note --repo "$top" 2>/dev/null || true)"
[[ -n "$note" ]] || exit 0
printf '%s' "$note" | jq -Rs '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: .}}'
exit 0
