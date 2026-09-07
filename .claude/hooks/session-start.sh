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

# FRESHNESS LIVES IN .claude/hooks/freshness-guard.sh, NOT HERE.
# This file briefly carried its own fetch-and-fast-forward block (added
# 2026-09-06). A parallel session had meanwhile built freshness-guard.sh,
# wired in this repo's own .claude/settings.json at SessionStart,
# UserPromptSubmit and PreToolUse -- so the two ran back to back at every
# startup, fetching twice and racing to fast-forward the same branch. The
# guard's version is also strictly better: it additionally answers "does
# this branch contain everything on its BASE", which is the question that
# catches a branch perfectly in sync with its own remote and still built on
# a stale base. Two copies of a rule is how one of them silently stops
# matching the other, so this one is gone rather than kept in sync by hand.
# The refspec repair above deliberately stays: it is local config only, it
# is idempotent, and it runs before the guard so the guard's comparisons
# can resolve at all on a single-branch clone.

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

# Attached practice-set sources whose vendored engine has gone stale.
#
# WHY THIS BELONGS HERE AND NOWHERE ELSE. A source set (someone's own
# precedent-individual, a team's precedent-team-*) vendors this repo's
# engine as tracked files, and refreshing it needs a clone of THIS repo to
# compare against -- which an ordinary session in that set has no reason to
# have. A session working HERE always does, by definition. So this is the
# one place the question can be answered for free, and until 2026-09-06
# nothing asked it: two real sets sat more than two hundred commits behind,
# generating a loader block with a defect fixed upstream days earlier, and
# it surfaced only because a session happened to run a check by hand.
#
# Report only -- it never refreshes anything on its own. `--apply` is a
# person's decision (or a session acting on one), because the result has to
# be reviewed and published under each set's own merge rules, which this
# hook cannot know. Exit 0 regardless: a session that fails to START over
# an advisory notice about a DIFFERENT repository is a far worse outcome
# than one that misses the notice.
if [ -f tools/precedent_refresh_sources.py ]; then
  python3 tools/precedent_refresh_sources.py 2>/dev/null || true
fi

# ---- commit identity, for EVERY Precedent repo in the session
#
# practice: session-bootstrap, and the incident is this repo's own.
#
# A SessionStart hook fires for the session's PRIMARY repo only. A sibling
# attached with `add_repo` is just a directory on disk -- AGENTS.md's
# gotchas already say every guarantee that hook provides is absent there.
# The consequence nobody had joined up: the mechanism that sets a commit's
# AUTHOR and TIMEZONE lives in the individual practice set's own
# `bootstrap/commit-identity.sh`, so in a session whose primary repo is
# THIS one, no attached set gets an identity at all. Each one silently
# keeps the container's bot account and its UTC clock.
#
# 2026-09-07 it produced both halves in one turn: a commit authored as the
# container's agent (caught before it was pushed) and, an hour later, a
# merge commit stamped +0000 that reached main and had to be grandfathered
# by SHA. Setting it by hand had been the workaround all session, which is
# exactly the "instruction competing with a default, on every commit,
# forever" that commit-identity.sh's own header says not to rely on.
#
# THE INFORMATION STAYS IN ONE PLACE. This does not copy a name, an address
# or a zone anywhere: it runs the individual set's own script, which reads
# that set's `identity.json` -- still the single declaration
# (registry-source-of-truth). All this adds is REACH: the same script, once
# per repo, with CLAUDE_PROJECT_DIR pointing at each. The script is built
# for exactly this (it is meant to be installed in shared repositories that
# name no person) and is idempotent, so re-running costs nothing.
#
# Reports and never gates, like everything else here.
_ident_script=""
_indiv="$(python3 - <<'PYIND' 2>/dev/null || true
import json, os, pathlib
cfg = pathlib.Path(os.environ.get("PRECEDENT_USER_CONFIG",
                                  "~/.config/precedent/config.json")).expanduser()
try:
    d = json.loads(cfg.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit
for key in ("individual", "sources"):
    v = d.get(key)
    if isinstance(v, dict) and v.get("path"):
        print(v["path"]); raise SystemExit
    if isinstance(v, list):
        for e in v:
            if isinstance(e, dict) and e.get("level") == "individual" and e.get("path"):
                print(e["path"]); raise SystemExit
PYIND
)"
if [ -n "$_indiv" ] && [ -f "$_indiv/bootstrap/commit-identity.sh" ]; then
  _ident_script="$_indiv/bootstrap/commit-identity.sh"
fi

if [ -n "$_ident_script" ]; then
  _here="$(pwd -P)"
  for _repo in "$_here" "$_here"/../*/; do
    [ -d "$_repo/.git" ] || continue
    _abs="$(cd "$_repo" 2>/dev/null && pwd -P)" || continue
    # Only repos this system actually owns the identity rule for. Never a
    # stranger's checkout that happens to sit alongside.
    #
    # THREE MARKERS, NOT ONE, and the first version had only the first two:
    # a CONSUMER declares `precedent.json`, an INDIVIDUAL set declares
    # `identity.json` -- and a TEAM set has NEITHER. It is a practice
    # repository, so what it has is `practices/`. Tested by breaking all
    # four checkouts' git config and re-running: the two team sets were
    # silently skipped, which is the exact failure this block exists to
    # stop, reproduced by the block itself.
    if [ -f "$_abs/precedent.json" ] || [ -f "$_abs/identity.json" ] \
       || [ -d "$_abs/practices" ]; then
      CLAUDE_PROJECT_DIR="$_abs" bash "$_ident_script" 2>/dev/null || \
        echo "WARN: commit-identity could not be applied to $_abs -- commits there may carry the container's identity" >&2
    fi
  done
fi

# A bootstrap that blocks startup is worse than anything it protects against,
# and `set -e` above would otherwise let a non-zero last command take the
# session down. Every check here reports; none of them gates.
exit 0
