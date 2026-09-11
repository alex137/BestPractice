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

# Is the loader block current with every practice source this repo
# declares? A consuming repo's AGENTS.md generated block is built from
# precedent.json's sources; any of them can move between sessions (a team
# set is a live sibling clone, not a vendored copy), and a session that
# reads a stale block follows rules nobody has any more -- or misses ones
# everybody does. --check never writes: it reports, and this never fails
# the session.
if [ -f tools/precedent_sync_views.py ] && [ -f precedent.json ]; then
  if ! python3 tools/precedent_sync_views.py --repo . --check >/dev/null 2>&1; then
    echo "WARN: AGENTS.md's generated loader block is out of date with precedent.json's sources. Fix: python3 tools/precedent_sync_views.py --repo ., review the diff, commit." >&2
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

# A bootstrap that blocks startup is worse than anything it protects against,
# and `set -e` at the top would otherwise let a non-zero last command take the
# session down. Every check here reports; none of them gates.
exit 0
