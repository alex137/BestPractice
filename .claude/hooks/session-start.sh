#!/bin/bash
# SessionStart hook for the BestPractice repo itself (practice 13).
# cmarkgfm gives doc_lint its exact GitHub-renderer strikethrough check and
# the deck engine its markdown renderer.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
pip install --quiet cmarkgfm 2>/dev/null || \
  echo "WARN: pip install failed - doc_lint strikethrough check and .md deck slides degrade" >&2

# Verify the local checkout actually matches origin before any work starts.
# See AGENTS.md's gotchas section for the incident: a session's local branch
# had ZERO commits in common with origin -- 51 real commits invisible, no
# error, `git status` reporting "up to date" because that check runs before
# any fetch. This block fetches the current branch and compares; it never
# fails the session (a git failure here must not block startup), it only
# warns loudly so the warning is impossible to miss at session start rather
# than discovered by accident deep into unrelated work.
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
  git fetch --quiet origin "$branch" 2>/dev/null || true
  if git rev-parse --verify -q "origin/$branch" >/dev/null 2>&1; then
    local_head="$(git rev-parse HEAD 2>/dev/null || true)"
    remote_head="$(git rev-parse "origin/$branch" 2>/dev/null || true)"
    if [ -n "$local_head" ] && [ "$local_head" != "$remote_head" ]; then
      base="$(git merge-base HEAD "origin/$branch" 2>/dev/null || true)"
      if [ -z "$base" ]; then
        echo "WARN: local '$branch' shares NO commit history with origin/$branch -- this checkout is stale or was rewritten upstream. Everything you read locally may be missing real, merged work. Fix (working tree must be clean): git checkout -B $branch origin/$branch" >&2
      else
        behind="$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo '')"
        if [ -n "$behind" ] && [ "$behind" != "0" ]; then
          echo "WARN: local '$branch' is $behind commit(s) behind origin/$branch. Fix (working tree must be clean): git checkout -B $branch origin/$branch" >&2
        fi
      fi
    fi
  fi
fi
