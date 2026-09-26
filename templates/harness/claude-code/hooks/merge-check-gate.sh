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
for candidate in "$project_dir/tools/precedent_merge_check.py" \
                 "$project_dir/process/upstream/tools/precedent_merge_check.py"; do
    if [[ -f "$candidate" ]]; then
        engine="$candidate"
        break
    fi
done
if [[ -z "$engine" ]]; then
    echo "NOTE: merge-check-gate: this project carries no precedent_merge_check.py, so this merge was NOT checked." >&2
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
    1) why="A check failed on what this merge would land. Fix it on the
branch and push, then merge." ;;
    124) why="The checks did not finish within 14 minutes, so nothing was
verified. Run the push check on the branch first -- a recorded pass for the
same tree is reused -- then merge." ;;
    *) echo "NOTE: merge-check-gate: $out" >&2; exit 0 ;;
esac

reason="The merge check REFUSED this merge.

$why

$(printf '%s\n' "$out" | tail -n 120)

To merge anyway you must say so explicitly and say why."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
