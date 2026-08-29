#!/bin/bash
# Claude Code adapter: Stop hook. Install to .claude/hooks/stop-git-check.sh
# (wired by the adapter's settings.json). Blocks the agent from ending a
# turn with uncommitted, untracked, or unpushed work still sitting in the
# working tree — a repo-tracked backstop for whatever a given session's own
# environment doesn't already provide (some managed Claude Code environments
# ship an equivalent check outside the repo; this makes the same guarantee
# travel with the practice layer for the ones that don't). Harness-specific,
# unlike tools/bootstrap.sh: only Claude Code's hook mechanism can block a
# stop this way (see templates/harness/README.md's enforcement caveat).
set -euo pipefail

# Claude Code re-invokes a Stop hook once after it already blocked a stop
# this turn, with stop_hook_active=true on stdin — exit clean rather than
# loop if this hook (or another one) already fired.
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  stop_hook_active="$(echo "$input" | jq -r '.stop_hook_active // empty' 2>/dev/null || true)"
  [[ "$stop_hook_active" == "true" ]] && exit 0
fi

# Not a git repo, or a git repo with no remote at all (e.g. a scratch clone)
# — nothing to push, nothing to check.
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[[ -n "$(git remote 2>/dev/null)" ]] || exit 0

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Uncommitted changes in the working tree. Commit (or intentionally discard) them before stopping." >&2
  exit 2
fi

if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  echo "Untracked files in the working tree. Add and commit them, or add them to .gitignore, before stopping." >&2
  exit 2
fi

current_branch="$(git branch --show-current)"
if [[ -n "$current_branch" ]] && git rev-parse -q --verify "origin/$current_branch" >/dev/null 2>&1; then
  unpushed="$(git rev-list "origin/$current_branch..HEAD" --count 2>/dev/null || echo 0)"
  if [[ "$unpushed" -gt 0 ]]; then
    echo "$unpushed unpushed commit(s) on branch '$current_branch'. Push them to the remote before stopping." >&2
    exit 2
  fi
fi

exit 0
