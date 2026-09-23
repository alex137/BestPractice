#!/bin/bash
# Claude Code adapter: Stop hook. Install to .claude/hooks/stop-git-check.sh
# (wired by the adapter's settings.json, as its own `Stop` entry). Blocks the
# agent from ending a turn with uncommitted, untracked, or unpushed work
# still sitting in the working tree — a repo-tracked backstop for whatever a
# given session's own environment doesn't already provide (some managed
# Claude Code environments ship an equivalent check outside the repo; this
# makes the same guarantee travel with the practice layer for the ones that
# don't). Harness-specific, unlike tools/bootstrap.sh: only Claude Code's
# hook mechanism can block a stop this way (see templates/harness/README.md's
# enforcement caveat).
#
# 2026-09-23: this file WAS also where the reply gate's advisory print, the
# blocking reply check, and close detection ran — all four wired as one
# `Stop` entry, so a repo objecting to THIS check (git cleanliness; see
# INSTALL.md's decision table) had no way to keep the other three, which
# nobody had objected to. They now live in the sibling hook
# stop-reply-check.sh, wired as its own `Stop` entry, so a settings.json can
# carry either independently. Nothing here changed behavior; it only stopped
# doing the other three things.
#
# Every reason to stop is COLLECTED and reported in one exit-2 message rather
# than the first one ending the script. Claude Code re-invokes a blocked Stop
# hook with stop_hook_active=true and this script exits clean on that, so
# whichever check came first used to be the only one that ever got enforced
# on a turn.
set -euo pipefail

# Claude Code re-invokes a Stop hook once after it already blocked a stop
# this turn, with stop_hook_active=true on stdin — exit clean rather than
# loop if this hook (or another one) already fired.
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  stop_hook_active="$(echo "$input" | jq -r '.stop_hook_active // empty' 2>/dev/null || true)"
  [[ "$stop_hook_active" == "true" ]] && exit 0
fi

# Not a git repo — nothing here to check.
in_git=1
git rev-parse --git-dir >/dev/null 2>&1 || in_git=0

reasons=()

if [[ "$in_git" == "1" ]] && [[ -n "$(git remote 2>/dev/null)" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    reasons+=("Uncommitted changes in the working tree. Commit (or intentionally discard) them before stopping.")
  fi

  if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    reasons+=("Untracked files in the working tree. Add and commit them, or add them to .gitignore, before stopping.")
  fi

  current_branch="$(git branch --show-current)"
  if [[ -n "$current_branch" ]] && git rev-parse -q --verify "origin/$current_branch" >/dev/null 2>&1; then
    unpushed="$(git rev-list "origin/$current_branch..HEAD" --count 2>/dev/null || echo 0)"
    if [[ "$unpushed" -gt 0 ]]; then
      reasons+=("$unpushed unpushed commit(s) on branch '$current_branch'. Push them to the remote before stopping.")
    fi
  fi
fi

if [[ ${#reasons[@]} -gt 0 ]]; then
  printf '%s\n' "${reasons[@]}" >&2
  exit 2
fi

exit 0
