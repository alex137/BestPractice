#!/bin/bash
# SessionStart hook for the BestPractice repo itself (practice 13).
# cmarkgfm gives doc_lint its exact GitHub-renderer strikethrough check and
# the deck engine its markdown renderer. markdown is tools/doc_html.py's
# renderer (tabular-shared-renderer) -- absent until 2026-09-04, when running
# it for the first real registered document (spec/PREFORK_AUDIT.md) found
# ModuleNotFoundError: nobody had run this tool successfully in a fresh
# session before either.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
pip install --quiet cmarkgfm markdown 2>/dev/null || \
  echo "WARN: pip install failed - doc_lint strikethrough check, .md deck slides, and tools/doc_html.py all degrade" >&2

# Repair a single-branch clone's refspec before anything tries to fetch.
# A repository attached mid-session (Claude Code's `add_repo`, and any
# `git clone --single-branch`) is handed exactly one refspec --
# `+refs/heads/main:refs/remotes/origin/main`. Push a feature branch from
# such a clone and the push genuinely succeeds, but no `origin/<branch>`
# ref is ever written, so every later `git rev-list origin/<branch>..HEAD`
# fails to resolve and the branch reads as "unpushed, no remote
# counterpart" forever -- including to a Stop hook that then blocks the
# turn. Seen 2026-09-06 on two consumer repos whose work was already
# safely on GitHub; the honest-looking remedy (push again) changes
# nothing, because the push was never the problem.
#
# Widening the refspec is local config only: it adds no commits, moves no
# refs, and re-running it is a no-op. Doing it here means the freshness
# block below can actually resolve origin/<branch> on a feature branch,
# which on a single-branch clone it silently could not.
if git rev-parse --git-dir >/dev/null 2>&1; then
  if ! git config --get-all remote.origin.fetch 2>/dev/null | grep -q 'refs/heads/\*'; then
    git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*' 2>/dev/null && \
      echo "NOTE: this clone fetched only one branch; widened remote.origin.fetch so other branches resolve. (See AGENTS.md gotchas: a single-branch clone makes every other branch read as 'unpushed' forever.)" >&2
  fi
fi

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
  # A FAILED fetch must never read as "in sync". Without this, the compare
  # below runs against a stale remote-tracking ref: local HEAD equals
  # origin/$branch because BOTH are old, no branch is reported behind, and the
  # session proceeds silently on a checkout that is arbitrarily far out of
  # date. Seen 2026-09-06: a container came up on a 5-day-old shallow clone,
  # 207 commits behind, and this hook said nothing -- the session's first
  # conclusion was that files landed a week earlier did not exist. Same shape
  # as the check suite's own "a skip is not a pass" rule, in the guard meant
  # to enforce it.
  if ! git fetch --quiet origin "$branch" 2>/dev/null; then
    echo "WARN: could not fetch origin/$branch -- freshness NOT verified, and the comparison below (if any) is against a possibly stale remote-tracking ref. Re-run 'git fetch origin $branch' before trusting what you read here." >&2
  fi
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

# The practices in force from the TEAM, INDIVIDUAL and REPO-LOCAL sources.
#
# WHY THIS RUNS HERE AND WRITES AN UNTRACKED FILE. precedent.json declares
# more sources than the committed AGENTS.md carries: that block is
# single-source on purpose, because this repository is PUBLIC and private
# practice text may not be committed to it. Measured 2026-09-06
# (spec/PRELAUNCH_AUDIT.md): 43 of the 114 practices in force here reached
# no loading channel at all, so a session was never shown the team's or the
# person's own rules while precedent.json said they bind the work. The
# constraint is on committing that text, not on loading it -- so it is
# generated at session start into .precedent/ (gitignored) instead.
#
# `|| true` and the tool's own always-exit-0 are belt and braces on purpose:
# this file runs under `set -e`, and a session that fails to START because
# an OPTIONAL practice file could not be written is a far worse outcome than
# a session missing it. The tool names any source it could not resolve on
# stderr rather than omitting it silently -- "unreachable" and "has no
# rules" must not look the same.
if [ -f tools/precedent_session_practices.py ]; then
  python3 tools/precedent_session_practices.py || \
    echo "WARN: could not write .precedent/SESSION_PRACTICES.md - this session is not being shown the team/individual practices in force here" >&2
fi
