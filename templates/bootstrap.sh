#!/bin/bash
# Bootstrap template (practice `session-bootstrap`) — environment setup as code, harness-neutral.
#
# Install to tools/bootstrap.sh in the dependent repo. Every entry here should
# exist because its absence cost a real session (practice `environment-gotchas`): record the story
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
# freshness notice below, which asks whether Precedent has moved -- this
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

# Is the loader block current with every practice source this repo
# declares? A consuming repo's AGENTS.md generated block is built from
# precedent.json's sources; any of them can move between sessions (a team
# set is a live sibling clone, not a vendored copy), and a session that
# reads a stale block follows rules nobody has any more -- or misses ones
# everybody does. --check never writes: it reports, and this never fails
# the session.
if [ -f tools/precedent_sync_views.py ] && [ -f precedent.json ]; then
  if ! python3 tools/precedent_sync_views.py --check >/dev/null 2>&1; then
    echo "WARN: AGENTS.md's generated loader block is out of date with precedent.json's sources. Fix: python3 tools/precedent_sync_views.py, review the diff, commit." >&2
  fi
fi

# Precedent upstream freshness notice, for a repo on the CLASSIC
# process/upstream/ vendoring layout (INSTALL.md section 1). Detection is
# automated -- one ls-remote against the public upstream, silent when
# current or offline; TAKING the update stays deliberate (INSTALL.md
# section 2) because installs are adaptive and unattended mirrors are the
# mechanism class that loses content.
#
# GUARDED, not silenced. This line used to be an unconditional
# `python3 process/upstream/tools/checkin.py fresh 2>/dev/null || true`,
# which in a Precedent-loader install (no process/upstream/ at all) failed
# on every session start and said nothing -- so a whole class of install
# got no freshness check and no notice that it had none. Silence has to
# mean "checked and current", never "there was nothing to run": that is
# the same trap the checkout-freshness block above exists for.
#
# The Precedent-loader layout has no equivalent to run here: its engine
# freshness check (`python3 tools/precedent_vendor_engine.py status
# <bestpractice-clone>`) needs a local clone of the upstream repo to
# compare against, which a fresh session has no reason to have. That one
# stays a deliberate step -- INSTALL.md section 2, "Keep the vendored
# engine current (consumer repos)".
if [ -f process/upstream/tools/checkin.py ]; then
  python3 process/upstream/tools/checkin.py fresh || \
    echo "WARN: upstream freshness check failed - not verified" >&2
fi
