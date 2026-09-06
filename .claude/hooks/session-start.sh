#!/bin/bash
# SessionStart hook for the BestPractice repo itself (practice
# `session-bootstrap`).
#
# Two jobs, deliberately in this order and with different gating:
#   1. Install the packages this repo's tooling imports (remote only -- a
#      local shell manages its own environment).
#   2. Make sure this checkout is actually current with origin, and repair
#      it when it is not (EVERY environment -- see below).
#
# cmarkgfm gives doc_lint its exact GitHub-renderer strikethrough check and
# the deck engine its markdown renderer. markdown is tools/doc_html.py's
# renderer (tabular-shared-renderer) -- absent until 2026-09-04, when running
# it for the first real registered document (spec/PREFORK_AUDIT.md) found
# ModuleNotFoundError: nobody had run this tool successfully in a fresh
# session before either.
set -euo pipefail

# Package install is the only remote-gated step. Everything below it used to
# sit behind this same gate, which meant the freshness check -- the guard
# against reading a stale checkout -- never ran on a local machine at all.
# Ungated 2026-09-06: a stale checkout is not a cloud-only failure, and the
# reason to gate the pip install (do not touch a developer's own environment)
# does not apply to reading and repairing git state.
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  pip install --quiet cmarkgfm markdown 2>/dev/null || \
    echo "WARN: pip install failed - doc_lint strikethrough check, .md deck slides, and tools/doc_html.py all degrade" >&2
fi

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

# Is THIS checkout current with its own origin -- and if not, MAKE it current.
# See the instructions file's gotchas section for the incidents. Three now,
# each worse than a warning would suggest:
#   2026-09-01  local branch shared ZERO commits with origin; 51 merged
#               commits invisible, `git status` reporting "up to date"
#               because it compares against a ref no fetch had refreshed.
#   2026-09-06  a container came up 207 commits behind on a 5-day-old
#               shallow clone; the session concluded that files landed a
#               week earlier "did not exist".
#   2026-09-06  a container came up 366 commits behind. The freshness block
#               that exists to catch exactly this DID run and could not
#               help: the container's copy of this hook predated the block
#               by six days. A guard shipped inside the checkout it guards
#               is missing from precisely the containers stale enough to
#               need it, so warning is not enough -- by the time a session
#               could act on a warning it has already been handed a stale
#               instructions file. This block therefore REPAIRS.
#
# Repair is confined to the unambiguous case: a clean tree, strictly behind,
# pure fast-forward. Every other shape (diverged, no shared history, dirty
# tree) still only warns -- those need a human decision, and a hook that
# discards work is worse than any stale checkout. Never fails the session.
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
  # Deepen a shallow clone rather than only fetching the tip. Staleness is
  # not the only thing an under-fetched clone causes: the gotchas section
  # records three checks that silently PASS on one rather than failing --
  # a `scope: 'tree'` check whose `git log` cannot reach the commit it
  # should flag, `%P` reporting a merge commit as parentless at the shallow
  # boundary, and `merge-base` exiting 1 between two branches that do share
  # history. A tip-only fetch fixes the staleness and leaves those lying.
  # Bounded, not --unshallow: some git policy hooks block --unshallow, and
  # a bounded fetch works either way.
  git_dir="$(git rev-parse --git-dir 2>/dev/null || true)"
  fetch_ok=1
  if [ -n "$git_dir" ] && [ -f "$git_dir/shallow" ]; then
    git fetch --quiet --depth=1000 origin "$branch" 2>/dev/null || fetch_ok=0
  else
    git fetch --quiet origin "$branch" 2>/dev/null || fetch_ok=0
  fi
  # A FAILED fetch must never read as "in sync". Without this the compare
  # below runs against an unrefreshed remote-tracking ref: local HEAD equals
  # origin/$branch because BOTH are old, nothing looks behind, and silence
  # means "not checked", not "current". Same shape as the check suite's own
  # "a skip is not a pass" rule, in the guard meant to enforce it.
  if [ "$fetch_ok" = "0" ]; then
    echo "WARN: could not fetch origin/$branch -- freshness NOT verified, and any comparison below is against a possibly stale remote-tracking ref. Re-run 'git fetch origin $branch' before trusting what you read here." >&2
  fi
  if git rev-parse --verify -q "origin/$branch" >/dev/null 2>&1; then
    local_head="$(git rev-parse HEAD 2>/dev/null || true)"
    remote_head="$(git rev-parse --verify -q "origin/$branch" 2>/dev/null || true)"
    if [ -n "$local_head" ] && [ -n "$remote_head" ] && [ "$local_head" != "$remote_head" ]; then
      base="$(git merge-base HEAD "origin/$branch" 2>/dev/null || true)"
      if [ -z "$base" ]; then
        echo "WARN: local '$branch' shares NO commit history with origin/$branch -- this checkout is stale or was rewritten upstream. Everything you read locally may be missing real, merged work. NOT repaired automatically: check what is here first, then (clean tree) git checkout -B $branch origin/$branch" >&2
      else
        behind="$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo '')"
        ahead="$(git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo '')"
        if [ -n "$behind" ] && [ "$behind" != "0" ]; then
          if [ -n "$ahead" ] && [ "$ahead" != "0" ]; then
            echo "WARN: local '$branch' has diverged from origin/$branch -- $behind behind, $ahead ahead. NOT repaired automatically: a merge or rebase here is your call, not a hook's." >&2
          elif [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null || true)" ]; then
            echo "WARN: local '$branch' is $behind commit(s) behind origin/$branch, and the working tree has uncommitted changes -- NOT repaired automatically. Commit or stash, then: git merge --ff-only origin/$branch" >&2
          elif git merge --ff-only --quiet "origin/$branch" 2>/dev/null; then
            echo "NOTE: local '$branch' was $behind commit(s) behind origin/$branch; fast-forwarded to $(git rev-parse --short HEAD). Your checkout NOW matches origin -- anything read before this line was stale." >&2
          else
            echo "WARN: local '$branch' is $behind commit(s) behind origin/$branch and the fast-forward FAILED (an untracked file in the way, most likely). Resolve, then: git merge --ff-only origin/$branch" >&2
          fi
        fi
      fi
    fi
  fi
fi

# A bootstrap that blocks startup is worse than anything it protects against,
# and `set -e` above would otherwise let a non-zero last command take the
# session down. Every check here reports; none of them gates.
exit 0
