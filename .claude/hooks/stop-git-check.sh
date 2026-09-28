#!/bin/bash
# Stop hook for the BestPractice repo itself (practice 13), instantiated
# from templates/harness/claude-code/hooks/stop-git-check.sh — logic
# unchanged; that file already resolves tools/precedent_gate.py correctly
# for this repo's own root-tools/ layout (it also checks
# process/upstream/tools/, which a dependent repo needs and this repo does
# not have). This repo went without a Stop hook at all until the same
# 2026-09-04 gate audit that fixed the template found the reply gate unwired
# — dogfooding it here closes the same gap in the repo that teaches it.
#
# 2026-09-23: this file WAS also where the reply gate's advisory print, the
# blocking reply check, and close detection ran — all four wired as one
# `Stop` entry, so a repo objecting to THIS check (git cleanliness; see
# INSTALL.md's decision table) had no way to keep the other three, which
# nobody had objected to. They now live in the sibling hook
# .claude/hooks/stop-reply-check.sh, wired as its own `Stop` entry, so a
# settings.json can carry either independently. Nothing here changed
# behavior; it only stopped doing the other three things.
#
# Every reason to stop is now COLLECTED and reported in one exit-2 message
# instead of the first one ending the script. Claude Code re-invokes a
# blocked Stop hook with stop_hook_active=true and this script exits clean
# on that, so whichever check came first was the only one that ever got
# enforced on a turn.
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
    # Unpushed means on NO remote ref, not "ahead of origin/<this branch>"
    # (2026-09-28, reported from a consumer repo). That one ref goes stale:
    # its remote copy deleted after the pull request merged, or the branch
    # reset onto origin/pre-staging whose tip merges it. Both times the hook
    # counted commits origin/main or origin/pre-staging already held. A
    # stale ref still counts as a remote here -- its commits were pushed
    # once -- but it is never the only thing the count is measured against.
    unpushed="$(git rev-list --count HEAD --not --remotes 2>/dev/null || echo 0)"
    # Commits that change no file -- a merge, an empty commit -- lose nothing,
    # so they never block a stop (Morgan, 2026-09-27, strength: decided):
    # identical files on origin means nothing is at risk. Otherwise the count
    # a person reads is the commits that change a file, never the merges.
    if [[ "$unpushed" -gt 0 ]] && git diff --quiet "origin/$current_branch" HEAD 2>/dev/null; then
      unpushed=0
    fi
    if [[ "$unpushed" -gt 0 ]]; then
      real="$(git rev-list --count --no-merges HEAD --not --remotes -- . 2>/dev/null || echo 0)"
      [[ "$real" -gt 0 ]] && unpushed="$real"
      reasons+=("$unpushed unpushed commit(s) on branch '$current_branch'. Push them to the remote before stopping.")
    fi
  fi
fi

if [[ ${#reasons[@]} -gt 0 ]]; then
  printf '%s\n' "${reasons[@]}" >&2
  exit 2
fi

exit 0
