#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES a `git push` until the
# pushed repository's own tools/precedent_push_check.py passes -- the list of
# everything GitHub Actions used to run on a push, run here instead.
#
# WHY THIS EXISTS (Morgan, 2026-09-25, strength: decided). GitHub CI is off
# for most of his pushes now: a practice source runs none
# (source-sets-run-no-ci), `ci_workflows` installs none, and
# `ci_every_hours` / `ci_on_branches` tag commits `[skip ci]`. Each of those
# was decided on "the local check runs before the push" -- and nothing ran
# it; it was a sentence. His ask: "the same list of everything we used to
# run (just locally we do it, not via the github ci/cd)". The list lives in
# precedent_push_check.py, one place; this file only decides WHEN to run it.
#
# WHY A CLAUDE CODE HOOK AND NOT .git/hooks/pre-push -- the same answer
# commit-identity-push-gate.sh beside this gives: `core.hooksPath` is set
# globally on this machine, and putting one repo's checks into that global
# directory would run them on every push from every repository.
#
# WHICH REPOSITORY. Unlike commit-identity-push-gate.sh, which judges only
# the repo it is wired in, this follows the push: `git -C <dir> push` or a
# leading `cd <dir> &&` names the repository, and THAT repository's own
# push check runs. A session rooted in one repo routinely pushes its
# siblings, and a gate that stood aside for them would leave the practice
# sources -- the repos with no CI at all -- exactly as unguarded as before.
# A repository that carries no precedent_push_check.py is let through.
#
# IT CAN TAKE MINUTES, AND THAT IS HANDLED, NOT HOPED. BestPractice's list
# includes the verification harness (about four minutes). The tool records a
# pass against the tree, so a session that ran the deep check first pushes
# at once. When it did not, this runs the list itself under `timeout`,
# comfortably inside the hook's own configured timeout, and REFUSES on
# expiry -- a hook the harness kills is treated as a non-blocking error,
# which would let the push through unchecked.
#
# FAIL-CLOSED ON A FINDING, FAIL-OPEN ON THE PLUMBING, exactly as
# doc-lint-gate.sh and commit-identity-push-gate.sh do (practice:
# fail-gracefully): no jq, python3 or git, an unparseable payload, a tool
# that crashes or cannot tell what kind of repo it is in -- all exit 0,
# loudly on stderr. A gate that breaks a session over its own missing
# dependency is a gate somebody disables.
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

cmd="$(printf '%s' "$input" \
  | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[[ -n "$cmd" ]] || exit 0

# Only a real `git push`, in command position -- not one quoted in a commit
# message or a heredoc (gotcha-2026-09-21, the same discipline both sibling
# gates apply).
printf '%s' "$cmd" \
  | grep -qE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?push\b' \
  || exit 0

# A dry run sends nothing, and a branch deletion sends no content. Read off
# the push's OWN arguments: `git commit -n && git push` is a real push.
push_args="$(printf '%s' "$cmd" \
  | grep -oE 'git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?push[^;&|]*' \
  | head -n1 || true)"
if printf '%s' "$push_args" | grep -qE '[[:space:]](--dry-run|-n|--delete|-d)([[:space:]]|$)'; then
    exit 0
fi

project_dir="${CLAUDE_PROJECT_DIR:-.}"
cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"

# The repository being pushed: `git -C <dir>`, else a leading `cd <dir>`,
# else the tool call's working directory, else the project. `|| true` on
# each grep is load-bearing under pipefail: no match is the ordinary case.
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

tool=""
for candidate in tools/precedent_push_check.py process/upstream/tools/precedent_push_check.py; do
    if [[ -f "$top/$candidate" ]]; then
        tool="$top/$candidate"
        break
    fi
done
[[ -n "$tool" ]] || exit 0

# 840s: inside the 900s this hook is given in settings.json, so it is this
# script -- not the harness -- that decides what an expiry means.
# No `timeout` binary (stock macOS) means no deadline of our own; the
# harness's then governs, and an expiry there fails open. Said, not hidden.
limit=()
if command -v timeout >/dev/null 2>&1; then
    limit=(timeout 840)
else
    echo "NOTE: push-check-gate: no \`timeout\` command here, so a run that outlives the hook's own timeout would be let through unchecked." >&2
fi
set +e
out="$(cd "$top" && ${limit[@]+"${limit[@]}"} python3 "$tool" --gate 2>&1)"
rc=$?
set -e

if printf '%s' "$out" | grep -q '^Traceback (most recent call last):'; then
    echo "WARN: push-check-gate: precedent_push_check.py CRASHED rather than reporting, so this push was NOT checked. The gate is failing open:" >&2
    printf '%s\n' "$out" | tail -n 30 >&2
    exit 0
fi

case "$rc" in
    0) printf '%s\n' "$out" | tail -n 3 >&2; exit 0 ;;
    1) why="A check failed. Fix it before pushing -- this list is what GitHub
CI used to run on this push, and CI is not going to run it now." ;;
    124) why="The checks did not finish within 14 minutes, so nothing was
verified. Run them directly with a long Bash timeout, then push again --
a pass is recorded against the tree, so the push will not re-run them:

    cd $top && python3 ${tool#"$top"/}" ;;
    2) echo "NOTE: push-check-gate: $out" >&2; exit 0 ;;
    *) echo "WARN: push-check-gate: precedent_push_check.py exited $rc, which is not a result it defines; failing open:" >&2
       printf '%s\n' "$out" | tail -n 30 >&2
       exit 0 ;;
esac

reason="The push check REFUSED this push of $top.

$why

$(printf '%s\n' "$out" | tail -n 120)

To push anyway you must say so explicitly and say why."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
