#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES merging a pull request
# through GitHub until the push check passes on what that merge would land.
#
# WHY THIS EXISTS (spec/BRANCH_TIERS_PLAN.md, hole 1, 2026-09-25). The push
# gate (push-check-gate.sh) checks a `git push`. A merge made with GitHub's
# merge tool is a push no local hook ever sees, so under the branch tiers --
# where a working branch gets only the basic check -- a merge into staging
# or main would land work nobody fully checked. This closes that: before
# the merge tool runs, tools/precedent_merge_check.py runs the repository's
# own push check on the merge GitHub would make, at the tier the base branch
# needs.
#
# TWO SHAPES OF MERGE. The GitHub MCP server's merge_pull_request tool
# (owner, repo and pull number in its input), and `gh pr merge` in Bash
# where a harness has the gh CLI -- by number, or with none, which merges
# the current branch's pull request and is checked fully because its base
# is not named.
#
# AFTER THE MERGE TOO (PostToolUse, 2026-09-30). The check before a merge
# judges GitHub's test merge, then frees the base, and GitHub merges seconds
# later: a base that moved in that gap lands a merge nobody checked. Wired a
# second time on PostToolUse, this runs precedent_merge_check.py --landed on
# the merge commit itself -- instant when nothing moved (the pass is reused),
# a full check when the base did, and a revert of the merge when that fails.
#
# FAIL-CLOSED ON A FINDING, FAIL-OPEN ON THE PLUMBING, as every gate here
# (practice: fail-gracefully): no jq, python3 or git, no checkout of the
# repository beside this project, no push check in it, a fetch that fails --
# all let the merge through, loudly on stderr.
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

tool_name="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || true)"
event="$(printf '%s' "$input" | jq -r '.hook_event_name // empty' 2>/dev/null || true)"
project_dir="${CLAUDE_PROJECT_DIR:-.}"
cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
here="${cwd:-$project_dir}"

args=()
case "$tool_name" in
    mcp__*__merge_pull_request)
        owner="$(printf '%s' "$input" | jq -r '.tool_input.owner // empty')"
        repo="$(printf '%s' "$input" | jq -r '.tool_input.repo // empty')"
        number="$(printf '%s' "$input" | jq -r '.tool_input.pullNumber // empty')"
        [[ -n "$owner" && -n "$repo" && -n "$number" ]] || exit 0
        args=(--owner "$owner" --repo "$repo" --number "${number%.*}"
              --search "$here" --search "$project_dir")
        ;;
    Bash)
        cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
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
        printf '%s' "$bare" \
          | grep -qE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*gh[[:space:]]+pr[[:space:]]+merge\b' \
          || exit 0
        # Only a real `gh pr merge`, in command position.
        merge="$(printf '%s' "$cmd" \
          | grep -oE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*gh[[:space:]]+pr[[:space:]]+merge\b[^;&|]*' \
          | head -n1 || true)"
        [[ -n "$merge" ]] || exit 0
        number="$(printf '%s' "$merge" | sed -E 's/^.*pr[[:space:]]+merge//' \
          | grep -oE '(^|[[:space:]])#?[0-9]+([[:space:]]|$)' | head -n1 | tr -dc '0-9' || true)"
        slug="$(printf '%s' "$merge" \
          | grep -oE '(-R|--repo)[[:space:]=]+[^[:space:]]+' | head -n1 \
          | sed -E 's/^(-R|--repo)[[:space:]=]+//' || true)"
        if [[ -n "$number" && -z "$slug" ]]; then
            url="$(git -C "$here" remote get-url origin 2>/dev/null || true)"
            slug="$(printf '%s' "${url%.git}" | grep -oE '[^/:]+/[^/:]+$' || true)"
        fi
        if [[ -n "$number" && -n "$slug" ]]; then
            args=(--owner "${slug%%/*}" --repo "${slug#*/}" --number "$number"
                  --search "$here" --search "$project_dir")
        else
            args=(--head --search "$here")
        fi
        ;;
    *)
        exit 0
        ;;
esac

engine=""
for candidate in "$project_dir/tools/precedent_merge_check.py"; do
    if [[ -f "$candidate" ]]; then
        engine="$candidate"
        break
    fi
done
if [[ -z "$engine" ]]; then
    echo "NOTE: merge-check-gate: this project carries no precedent_merge_check.py, so this merge was NOT checked." >&2
    exit 0
fi

if [[ "$event" == "PostToolUse" ]]; then
    [[ " ${args[*]} " == *" --number "* ]] || exit 0
    # The merge commit, from the merge tool's own answer when it gives one;
    # else the engine asks GitHub. No answer at all: nothing was merged.
    sha="$(printf '%s' "$input" | jq -r '.tool_response | tostring' 2>/dev/null \
      | grep -oE 'sha[^0-9a-f]{1,8}[0-9a-f]{40}' | head -n1 | grep -oE '[0-9a-f]{40}$' || true)"
    if [[ "$tool_name" == mcp__* && -z "$sha" ]]; then
        exit 0
    fi
    post_limit=()
    command -v timeout >/dev/null 2>&1 && post_limit=(timeout 840)
    set +e
    out="$(${post_limit[@]+"${post_limit[@]}"} python3 "$engine" "${args[@]}" --landed "${sha:-unknown}" 2>&1)"
    rc=$?
    set -e
    if printf '%s' "$out" | grep -q '^Traceback (most recent call last):'; then
        rc=2
        out="precedent_merge_check.py CRASHED after the merge, so what landed was NOT checked:
$(printf '%s\n' "$out" | tail -n 30)"
    fi
    if [[ "$rc" == 0 ]] && ! printf '%s' "$out" | grep -q 'MOVED'; then
        printf '%s\n' "$out" | tail -n 1 >&2
        exit 0
    fi
    if [[ "$rc" == 1 ]]; then
        # The words are the tool's: see the note above the refusal below.
        reason="$(printf '%s' "$out" | python3 "$engine" --hook-reason landed-1 2>/dev/null)" || reason=""
        [[ -n "$reason" ]] || reason="precedent_merge_check.py --landed failed:

$out"
        printf '%s' "$reason" | jq -Rs '{decision: "block", reason: .}'
    else
        printf '%s' "$out" | jq -Rs '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: .}}'
    fi
    exit 0
fi

# 840s inside the 900s this hook is given, for the reason push-check-gate.sh
# gives: an expiry the harness enforces is a non-blocking error, which would
# let the merge through unchecked.
limit=()
if command -v timeout >/dev/null 2>&1; then
    limit=(timeout 840)
fi
set +e
out="$(${limit[@]+"${limit[@]}"} python3 "$engine" "${args[@]}" 2>&1)"
rc=$?
set -e

if printf '%s' "$out" | grep -q '^Traceback (most recent call last):'; then
    echo "WARN: merge-check-gate: precedent_merge_check.py CRASHED, so this merge was NOT checked. Failing open:" >&2
    printf '%s\n' "$out" | tail -n 30 >&2
    exit 0
fi

case "$rc" in
    0) printf '%s\n' "$out" | tail -n 3 >&2; exit 0 ;;
    1|124) ;;
    *) echo "NOTE: merge-check-gate: $out" >&2; exit 0 ;;
esac

# THE WORDS ARE THE TOOL'S (2026-10-07). This hook decides WHETHER to
# refuse; precedent_merge_check.py decides what the refusal says, through
# --hook-reason, and this file passes it on. A hook is a file Claude Code's
# auto mode holds for a person's yes, so wording kept here made every
# rewording a question in every repository at its next Update Vendors. The
# short line below is only for an engine too old to answer --hook-reason.
reason="$(printf '%s' "$out" | python3 "$engine" --hook-reason "$rc" 2>/dev/null)" || reason=""
[[ -n "$reason" ]] || reason="precedent_merge_check.py refused this merge (exit $rc):

$(printf '%s\n' "$out" | tail -n 120)"

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
