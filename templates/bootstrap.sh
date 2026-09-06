#!/bin/bash
# Bootstrap template (practice 13) — environment setup as code, harness-neutral.
#
# Install to tools/bootstrap.sh in the dependent repo. Every entry here should
# exist because its absence cost a real session (practice 4): record the story
# in the instructions file's gotchas section, and encode the fix here so it
# applies itself. Keep it idempotent, fast when cached, and loud (a WARN,
# never a silent failure) when something can't install.
#
# Wiring (see templates/harness/): harnesses with a session hook run this
# automatically; for the rest, the instructions file tells the agent to run
# `bash tools/bootstrap.sh` at session start.
set -euo pipefail

# apt packages this repo's tooling needs (idempotent). A stale package
# index makes the fetch 404 (seen 2026-08-06): on failure, refresh the
# index (apt-get update) and retry once before WARNing:
# if ! dpkg -s <package> >/dev/null 2>&1; then
#   apt-get install -y --no-install-recommends <package> >/dev/null 2>&1 || \
#     echo "WARN: <package> install failed - <what degrades without it>" >&2
# fi

# Python deps the repo's scripts import (cmarkgfm is doc_lint's exact
# GitHub-renderer check; keep it even if you add nothing else):
pip install --quiet cmarkgfm 2>/dev/null || \
  echo "WARN: pip install failed - doc_lint strikethrough check will be skipped" >&2

# Is THIS checkout current with its own origin? Distinct from the upstream
# freshness notice below, which asks whether BestPractice has moved -- this
# asks whether the session is even looking at its own repo's real content.
# Both have failed for real. Origin incident: a session's local branch shared
# ZERO commits with origin, 51 merged commits invisible, `git status` cheerily
# reporting "up to date" because it compares against a remote-tracking ref
# that no fetch had refreshed. A second, 2026-09-06: a container came up on a
# 5-day-old shallow clone, 207 commits behind, and the session's first
# conclusion was that files landed a week earlier did not exist.
#
# A FAILED fetch is reported, never treated as "in sync" -- that is the whole
# trap. When the fetch cannot run, local HEAD matches the stale
# remote-tracking ref, nothing looks behind, and silence means "not checked",
# not "current". Never fails the session; a bootstrap that blocks startup is
# worse than a stale checkout.
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
  if ! git fetch --quiet origin "$branch" 2>/dev/null; then
    echo "WARN: could not fetch origin/$branch - freshness NOT verified. Anything you read locally may be out of date; re-run 'git fetch origin $branch' before trusting it." >&2
  fi
  if git rev-parse --verify -q "origin/$branch" >/dev/null 2>&1; then
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse "origin/$branch")" ]; then
      if [ -z "$(git merge-base HEAD "origin/$branch" 2>/dev/null || true)" ]; then
        echo "WARN: local '$branch' shares NO commit history with origin/$branch - this checkout is stale or was rewritten upstream. Fix (working tree must be clean): git checkout -B $branch origin/$branch" >&2
      else
        behind="$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo '')"
        if [ -n "$behind" ] && [ "$behind" != "0" ]; then
          echo "WARN: local '$branch' is $behind commit(s) behind origin/$branch. Fix (working tree must be clean): git checkout -B $branch origin/$branch" >&2
        fi
      fi
    fi
  fi
fi

# BestPractice upstream freshness notice (see PRACTICES.md practice 13):
# detection is automated -- one ls-remote against the public upstream,
# silent when current or offline; TAKING the update stays deliberate
# (INSTALL.md sec.2) because installs are adaptive and unattended mirrors
# are the mechanism class that loses content.
python3 process/upstream/tools/checkin.py fresh 2>/dev/null || true
