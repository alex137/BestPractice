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

# Set the commit author to whoever is actually running this session, not
# a container's own bot identity -- practice `session-bootstrap`. Claude
# Code gets this from its own SessionStart hook
# (.claude/hooks/commit-identity.sh, wired in .claude/settings.json) before
# this script would ever run, so this call is a harmless no-op there (the
# script is idempotent -- "already right: no churn, no message"). Every
# other harness has no such hook, so this is the only place it runs.
# Depends on nothing Claude-Code-specific beyond how it's invoked: it reads
# $CLAUDE_PROJECT_DIR, falling back to $PWD, and otherwise just needs git.
if [ -f .claude/hooks/commit-identity.sh ]; then
  bash .claude/hooks/commit-identity.sh || \
    echo "WARN: commit-identity.sh failed - commits may be authored as whatever git is already configured with" >&2
fi

# Clone every shared practice set precedent.json declares, beside this repo,
# where the environment carries a credential (PRECEDENT_GIT_TOKEN and
# PRECEDENT_SOURCE_BASE_URL -- documentation/PER_MACHINE_SETUP.md); pull the
# ones already there. No credential: the tool names each set that is missing
# and why, and startup carries on. It runs BEFORE the loader-block check below,
# which otherwise compares AGENTS.md against sources that are not on disk.
#
# Until 2026-09-26 this step was not in the template. The only session-start
# code that ran it was precedent-universal-catalogue.sh, a hook for practice
# sets that every consumer is told to decline, so a consumer declaring a
# shared set never got it cloned in a fresh container. Seen in a real consumer
# that day: the set missing from every fresh container, and
# precedent_sync_views.py --check reporting 36 differences that disappeared
# once it was cloned by hand (gotchas/, "a declared shared set is never
# cloned"). precedent_check.py's declared-sources-are-cloned fails a repo that
# declares a shared set and wires nothing that clones it.
if [ -f precedent.json ] && [ -f tools/precedent_source_bootstrap.py ]; then
  python3 tools/precedent_source_bootstrap.py --sources-from . --remote-only false || true
elif [ -f precedent.json ] && [ -f process/upstream/tools/precedent_source_bootstrap.py ]; then
  python3 process/upstream/tools/precedent_source_bootstrap.py --sources-from . --remote-only false || true
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
# Only where an origin exists at all: a repo that has not been pushed yet has
# nothing to widen, and the NOTE below would be false there (measured on two
# fresh installs, 2026-09-14).
if git rev-parse --git-dir >/dev/null 2>&1 && git remote get-url origin >/dev/null 2>&1; then
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
  # A branch origin has never seen fails `git fetch origin <branch>` with
  # "couldn't find remote ref", exactly like an unreachable origin does --
  # and that is every fresh Claude Code web session, whose branch is not
  # pushed until its first push. Reported 2026-09-25: those sessions opened
  # on "could not fetch -- freshness NOT verified" when there was nothing to
  # be stale against. `ls-remote --exit-code` tells the two apart: 2 means
  # origin answered and has no such branch; anything else non-zero means the
  # question could not be asked, and that keeps the warning. Same test as
  # freshness-guard.sh's _branch_absent_from_origin.
  branch_absent=0
  _branch_absent_from_origin() {
    git ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1
    [ "$?" = "2" ]
  }
  if [ -n "$git_dir" ] && [ -f "$git_dir/shallow" ]; then
    # TODO.md's shallow-clone-self-heal-hardening item (BestPractice
    # record/GOTCHAS.md#g37, third occurrence): one bounded attempt used to
    # be the whole mechanism, and a failure here surfaced as nothing more
    # than a WARN line. A second, independently-bounded attempt costs
    # nothing when the first succeeds; a marker file left behind on total
    # failure means a later run of this same script (or this adapter's
    # freshness-guard.sh, where that hook is also installed) has a second,
    # independent chance to notice and say so loudly instead of silently
    # inheriting a still-truncated history.
    if timeout 90 git fetch --quiet --depth=1000 origin "$branch" 2>/dev/null \
       || timeout 60 git fetch --quiet --depth=1000 origin "$branch" 2>/dev/null; then
      [ -n "$git_dir" ] && rm -f "$git_dir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
    elif _branch_absent_from_origin "$branch"; then
      # Nothing to deepen along; the base-branch check below deepens along
      # the base instead, and owns the shallow warning if that fails too.
      branch_absent=1
    else
      fetch_ok=0
      echo "WARN: could not deepen this shallow clone after two attempts -- history-reading checks may see far less than the real history. Remedy by hand: git fetch --unshallow" >&2
      [ -n "$git_dir" ] && : > "$git_dir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
    fi
  elif ! git fetch --quiet origin "$branch" 2>/dev/null; then
    if _branch_absent_from_origin "$branch"; then branch_absent=1; else fetch_ok=0; fi
  fi
  # A FAILED fetch must never read as "in sync". Without this the compare
  # below runs against an unrefreshed remote-tracking ref: local HEAD equals
  # origin/$branch because BOTH are old, nothing looks behind, and silence
  # means "not checked", not "current". Same shape as the check suite's own
  # "a skip is not a pass" rule, in the guard meant to enforce it.
  if [ "$fetch_ok" = "0" ]; then
    echo "WARN: could not fetch origin/$branch -- freshness NOT verified, and any comparison below is against a possibly stale remote-tracking ref. Re-run 'git fetch origin $branch' before trusting what you read here." >&2
  fi
  # Not on origin yet: nothing there to be behind, but the branch can still
  # be cut from a stale base, which is the staleness that matters for a
  # brand-new branch. The base is precedent.json's `base_branch` when
  # declared (origin/HEAD is the wrong answer in any repo that pins work to
  # a non-default branch), else origin/HEAD. Repairs only the unambiguous
  # case, as above: clean tree, no commits of its own, strictly behind.
  if [ "$branch_absent" = "1" ]; then
    base_branch=""
    if [ -f precedent.json ]; then
      base_branch="$(python3 -c 'import json,sys; print(json.load(open("precedent.json")).get("base_branch") or "")' 2>/dev/null || true)"
    fi
    if [ -z "$base_branch" ]; then
      base_branch="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
      base_branch="${base_branch#origin/}"
    fi
    if [ -z "$base_branch" ] || [ "$base_branch" = "$branch" ]; then
      echo "NOTE: '$branch' is not on origin yet -- nothing to be behind there. No base branch resolved (set base_branch in precedent.json), so the base check is SKIPPED, not passed." >&2
    else
      echo "NOTE: '$branch' is not on origin yet -- nothing to be behind there. Checking it against origin/$base_branch instead." >&2
      if [ -n "$git_dir" ] && [ -f "$git_dir/shallow" ]; then
        if timeout 90 git fetch --quiet --depth=1000 origin "$base_branch" 2>/dev/null \
           || timeout 60 git fetch --quiet --depth=1000 origin "$base_branch" 2>/dev/null; then
          rm -f "$git_dir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
        else
          fetch_ok=0
          echo "WARN: could not deepen this shallow clone along origin/$base_branch after two attempts -- history-reading checks may see far less than the real history. Remedy by hand: git fetch --unshallow" >&2
          : > "$git_dir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
        fi
      else
        git fetch --quiet origin "$base_branch" 2>/dev/null || fetch_ok=0
      fi
      if [ "$fetch_ok" = "0" ]; then
        echo "WARN: could not fetch origin/$base_branch -- freshness NOT verified. Re-run 'git fetch origin $base_branch' before trusting what you read here." >&2
      elif git rev-parse --verify -q "origin/$base_branch" >/dev/null 2>&1 \
           && ! git merge-base --is-ancestor "origin/$base_branch" HEAD 2>/dev/null; then
        behind="$(git rev-list --count "HEAD..origin/$base_branch" 2>/dev/null || echo '?')"
        ahead="$(git rev-list --count "origin/$base_branch..HEAD" 2>/dev/null || echo '?')"
        if [ "$ahead" = "0" ] && [ -z "$(git status --porcelain --untracked-files=no 2>/dev/null || true)" ] \
           && git merge --ff-only --quiet "origin/$base_branch" 2>/dev/null; then
          echo "NOTE: '$branch' was cut $behind commit(s) behind origin/$base_branch and has no commits of its own; fast-forwarded to $(git rev-parse --short HEAD). Your checkout NOW matches origin/$base_branch -- anything read before this line was stale." >&2
        else
          echo "WARN: '$branch' is missing $behind commit(s) from origin/$base_branch -- it was cut from a stale base. NOT repaired automatically (it has commits of its own, or a dirty tree). Bring it up to date deliberately: git merge origin/$base_branch" >&2
        fi
      fi
    fi
  fi
  if [ "$branch_absent" = "0" ] && git rev-parse --verify -q "origin/$branch" >/dev/null 2>&1; then
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

# WHICH REPOS IN FORCE THIS SESSION CAN ACTUALLY LAND WORK IN.
#
# practice: spawn-session, which has said "settle who merges before the work
# starts" since 2026-09-12 -- and the sentence alone did not carry. On
# 2026-09-10 a session rooted in a private practice set migrated twelve
# repositories and built a seven-commit patch for the upstream repo that it
# could not push, because a session holding one owner's repositories is
# refused another's. It sat blocked four days, having spent about a hundred
# dollars to reach a branch nobody could land. The rule was right; the MOMENT
# was missing, and the session least likely to stop and read a practice file
# is the one already deep enough in the work for this to cost the most.
#
# Guarded like every other step here, and the guard matters: this tool is
# vendored (ENGINE_FILES), so a tree older than 2026-09-14 does not have it
# and must start anyway. Reports and never gates; bounded internally so an
# unreachable remote cannot hold a session at the door. A repo it could not
# reach is printed as unanswered, never as refused.
if [ -f tools/precedent_access_check.py ]; then
  python3 tools/precedent_access_check.py . || \
    echo "WARN: access check did not run -- whether this session can land work in each repo in force is unknown" >&2
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

# IS THE VENDORED CATALOGUE IN FORCE AT ALL? (2026-09-23.) A classic
# install -- process/upstream/ copied in, no loader over it -- vendors every
# practice and runs none of them, and until this line nothing said so: a
# consumer installed that way, took an update, and its sessions described
# the rules as "a vendored copy, not something this repo adopted". Printed
# to stdout on purpose, so the SessionStart hook puts it in front of the
# session rather than only the terminal. Guarded on the flag, because an
# older vendored audit without it would run the whole audit here instead.
if [ -f process/upstream/tools/practice_audit.py ] && \
   grep -q -- '--loader-notice' process/upstream/tools/practice_audit.py; then
  python3 process/upstream/tools/practice_audit.py --loader-notice || true
fi

# EVERY SOURCE THIS REPO DECLARES, checked outward (2026-09-23). The line
# above reads one manifest; this reads precedent.json and covers each
# declared source every way it is reached here -- the vendored engine
# (tools/ENGINE_MANIFEST.json), a vendored tree (process/manifest*.json)
# and a live sibling clone whose practices load as it stands. A source is
# covered from the moment it is declared, or it is not covered: a second
# shared set had no freshness check on either half until this ran, and
# nothing said so. --quiet speaks only when something is behind; a
# session start that a network hiccup can block is worse than the
# staleness, so the tool exits 0 in every failure mode and this line
# never gates. Taking an update stays "Update Vendors".
if [ -f tools/precedent_engine_freshness.py ]; then
  python3 tools/precedent_engine_freshness.py --quiet || \
    echo "WARN: source freshness did not run -- whether anything this repo vendors or resolves live is current is unknown this session" >&2
fi

# A WORKFLOW NOBODY APPROVED, said at session start (2026-09-26, practice:
# ci-workflow-approved). The same check refuses a session's push, but a
# workflow edited on GitHub's website or written through the API never
# passes a push, and it bills from the moment it lands. This clone was just
# taken from GitHub, so it holds such an edit already: say so before any
# work starts, not at the first push. Loud when something is wrong, silent
# otherwise, and it never gates.
if [ -f tools/precedent_check.py ] && [ -f tools/ENGINE_MANIFEST.json ] && \
   [ -d .github/workflows ]; then
  # `|| _wf_rc=$?`: under this file's `set -e` a failing check inside $()
  # would otherwise end the whole bootstrap.
  _wf_rc=0
  _wf_out=$(python3 tools/precedent_check.py --only ci-workflow-approved 2>&1) || _wf_rc=$?
  if [ "$_wf_rc" -ne 0 ] && grep -q '^VIOLATION' <<<"$_wf_out"; then
    echo "WARNING: a GitHub Actions workflow here has no approval, or changed since it was approved -- it may be spending Actions minutes now:" >&2
    { grep -E '^    \.github/workflows/' <<<"$_wf_out" | cut -c1-400 >&2; } || true
    echo "  Show the person each one and ask before doing anything else (practice: ci-workflow-approved)." >&2
  fi
fi

# A bootstrap that blocks startup is worse than anything it protects against,
# and `set -e` at the top would otherwise let a non-zero last command take the
# session down. Every check here reports; none of them gates.
exit 0
