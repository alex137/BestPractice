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
  pip_err="$(pip install --quiet cmarkgfm markdown 2>&1 1>/dev/null)" || \
    echo "WARN: pip install failed - doc_lint strikethrough check, .md deck slides, and tools/doc_html.py all degrade - pip stderr: ${pip_err}" >&2
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

# Make this checkout's HISTORY complete, not just its files.
#
# practice: durable-fix. The container clones this repo `--depth 1`, so every
# file of the branch is present and current and almost none of the past is.
# The files are what a person notices; the past is what the TOOLS read, and
# three of them degrade on a truncated one without ever failing:
# behavioral_replay.py has nothing to replay, doc_lint.py silently narrows
# from "the files changed against the base branch" to "the files not
# committed yet", and precedent_check.py's `scope: tree` checks read an empty
# `git log` as `0 violated` rather than as "could not check"
# (record/GOTCHAS.md#g6, #g8). Git itself is not immune: a branch that is
# merely BEHIND reads as diverged when the two truncated stretches do not
# overlap, which cost a whole session on 2026-09-14 (#g37) before the
# freshness guard learned to deepen before believing its own counts.
#
# Measured 2026-09-14 against this remote through this container's proxy, in
# exactly the order below (refspec widened first, so the deepen reaches every
# branch rather than one): 2.7 MB of history before, 9.5 MB after, 4 seconds.
# That is the whole cost, once per session, which is why this is
# unconditional rather than clever about which sessions need it.
#
# Bounded and never fatal. `timeout` caps a slow or hanging network so a
# session cannot be held at the door, and `--deepen` is the fallback because
# some git policy hooks refuse `--unshallow` outright. A failure reports and
# continues: a session with a short history is worse off than one without,
# and far better off than a session that does not start.
# TODO.md's shallow-clone-self-heal-hardening item, g37's third recurrence.
# ONE bounded attempt used to be the whole mechanism: on failure this printed
# a WARN nothing re-surfaced, and the next chance to fix it was whatever this
# checkout's freshness-guard.sh happened to do on its own (previously: only
# when it looked diverged, never for a checkout that was merely shallow and
# behind). A second, independently-bounded attempt costs nothing when the
# first succeeds, and turns a single transient network hiccup through this
# container's proxy into a recoverable one instead of a silent WARN.
if git rev-parse --git-dir >/dev/null 2>&1 \
   && [ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
  _shallow_fixed=0
  if timeout 90 git fetch --quiet --unshallow 2>/dev/null \
     || timeout 90 git fetch --quiet --deepen=1000 2>/dev/null; then
    _shallow_fixed=1
  elif timeout 60 git fetch --quiet --deepen=1000 2>/dev/null; then
    _shallow_fixed=1
  fi
  _shallow_gitdir="$(git rev-parse --absolute-git-dir 2>/dev/null || true)"
  if [ "$_shallow_fixed" = "1" ]; then
    echo "NOTE: this clone carried only the most recent commits; fetched the rest of the history so history-reading tools do not silently degrade. (See AGENTS.md gotchas g6, g8, g37.)" >&2
    [ -n "$_shallow_gitdir" ] && rm -f "$_shallow_gitdir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
  else
    # A marker, not just a log line: freshness-guard.sh checks for this on
    # every session-start, throttled prompt, and first tool call, and says so
    # out loud if it is STILL shallow after its own retry too -- instead of
    # this WARN sitting in stdout nobody reads back.
    echo "WARN: could not deepen this shallow clone after two attempts -- behavioral_replay.py, doc_lint.py's changed-files scope and precedent_check.py's tree checks may report success while checking little or nothing. freshness-guard.sh will keep retrying. Remedy by hand: git fetch --unshallow" >&2
    [ -n "$_shallow_gitdir" ] && : > "$_shallow_gitdir/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null || true
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

# The PRIVATE practice sources, when this environment carries a credential.
#
# THIS IS THE ONE STEP THAT CAN RUN BEFORE THE AGENT'S FIRST TURN, and that
# is the whole point of it. A private source normally reaches a hosted
# session because the agent calls `add_repo` in its own turn -- which
# `add_repo` refuses across owners, reproduced 2026-09-09 as a session's
# very first tool call ("cross-tier adds are not supported in v1"). A
# credential the ENVIRONMENT carries is under no such ordering: git can use
# it here, before anything else runs, which is why setting
# PRECEDENT_GIT_TOKEN is the durable fix and `add_repo` is the per-session
# one (practice: durable-fix).
#
# The shared sets are cloned as SIBLINGS, from $PRECEDENT_SOURCE_BASE_URL/<name>
# (or /<repo>, when the declaration says the repository is called something
# else), because that is how tools/precedent_resolve.py resolves one. The
# individual set needs nothing here: precedent_resolve.py's own self-heal
# already re-runs its bootstrap hook, and with a token set that attempt now
# succeeds where it used to fail for want of access.
#
# No token, no network call: the tool says which sources are missing and
# why, and startup continues. INSTALL.md section 8 is where the two
# variables are documented.
if [ -f tools/precedent_source_bootstrap.py ]; then
  python3 tools/precedent_source_bootstrap.py --teams-from . --remote-only false || true
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
# APPLIED, NOT JUST REPORTED (2026-09-15). Morgan: "my objection was to the
# WEEKLY updates that were automatic; I never objected to START OF SESSION
# checks that are automatic, I LOVE THAT." (strength: decided). This does
# not reopen precedent_refresh_sources.py's own 2026-09-14 "no unattended
# path" paragraph -- that decision killed a scheduled workflow running on
# its own cadence, unattended, with nobody watching. This is the opposite
# shape: it runs once, inside a session someone is sitting in, against
# that session's own working tree, and it still never commits or pushes --
# publishing stays "Update Vendors" or a person reading the diff by hand.
# See that file's docstring for the fuller record.
#
# A source with its own uncommitted changes is left alone rather than
# refreshed -- precedent_refresh_sources.py checks for that before writing
# anything, so a person's in-progress edit in precedent-individual or a
# team set is never interleaved with a regenerated diff it did not ask
# for. Reports and never gates on failure, like everything else here.
if [ -f tools/precedent_refresh_sources.py ]; then
  python3 tools/precedent_refresh_sources.py --apply 2>/dev/null || true
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
  # `$_indiv` IS IN THIS LIST, and leaving it out was a real bug (2026-09-14,
  # record/GOTCHAS.md#g40). An individual set does not have to be a sibling of
  # the primary repo -- `~/.config/precedent/config.json` puts it wherever it
  # was cloned, which on this container is `$HOME/precedent-individual` while
  # the primary repo and every team clone sit under a different parent. The
  # glob below then covers all of those and misses the individual set, so the
  # one repo this block reads the identity FROM was the one repo it never
  # applied it TO. The script is idempotent, so naming a path twice (when the
  # set IS a sibling) costs nothing.
  for _repo in "$_here" "$_indiv" "$_here"/../*/; do
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

# WHICH REPOS IN FORCE THIS SESSION CAN ACTUALLY LAND WORK IN.
#
# practice: spawn-session, which has said "settle who merges before the work
# starts" since 2026-09-12 -- and the sentence alone did not carry. On
# 2026-09-10 a session rooted in a private practice set migrated twelve
# repositories and built a seven-commit patch for THIS repo that it could not
# push, because a session holding one owner's repositories is refused
# another's. It sat blocked four days on "root session at alex137/BestPractice
# to land the team-set declaration in precedent.json", having spent about a
# hundred dollars to reach a branch nobody could land. The rule was right; the
# MOMENT was missing, and the session least likely to stop and read a practice
# file is the one already deep enough in the work for this to cost the most.
#
# So the question is asked here, where nobody has to remember it and the
# answer lands before the first turn. The probe is
# tools/very_deep_check.py's `can_land_here` -- imported, never copied, since
# two copies is how one silently stops matching the other (the freshness block
# above was deleted for exactly that reason).
#
# Reports and never gates, like everything else here, and bounded: the tool
# caps its own probing so an unreachable remote cannot hold a session at the
# door. A repo it could not reach is printed as unanswered, never as refused.
if [ -f tools/precedent_access_check.py ]; then
  python3 tools/precedent_access_check.py . || \
    echo "WARN: access check did not run -- whether this session can land work in each repo in force is unknown" >&2
fi

# Say whether Alex has moved `main` since the last time somebody carried it
# onto this branch. It PRINTS and stops there: Morgan asked for the reminder
# in a session he is sitting in rather than a job that merges behind his back
# ("I don't want it to merge invisibly, I'd like to do it in a session when
# I'm there", 2026-09-08). The comparison is against
# tools/upstream_watermark.json, not against git ancestry -- this branch
# carries `main` rather than merging it, so an ancestry test reports a
# permanent, meaningless gap. See that file's own comment for the incident.
# Resolved from this script's own path, not from the working directory or
# CLAUDE_PROJECT_DIR: when the harness roots a session one directory above
# the repo, both of those point somewhere else (and that layout is this
# project's own, since a team source resolves as a sibling clone).
_hook_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
python3 "$_hook_repo/tools/precedent_upstream_check.py" || \
  echo "WARN: upstream check did not run -- whether main has moved since the last carry is unknown this session" >&2

# AND, IN A REPO THAT VENDORS THE ENGINE, whether that engine has fallen
# behind upstream (2026-09-21). The check above is this repo's own question
# -- has `main` moved since the last carry -- and is meaningless in a
# dependent repo. This one is the dependent repo's question: is the engine
# it is enforcing with still the engine upstream ships?
#
# Nothing could answer that before. Every other check in this system runs
# inside one repository and compares it against itself, which is why a fix
# merged upstream reached an installed repo only when somebody remembered
# to run "Update Vendors" there, and why running a deep check could never
# find a stale vendored tree. Measured 2026-09-20: 18 of 22 repositories
# had never taken an update.
#
# Here in BestPractice it prints "not checked -- no ENGINE_MANIFEST.json",
# which is correct: this is the engine's own origin and has nothing
# vendored. It earns its place in the repos this hook is copied into.
#
# --quiet, so it speaks only when the repo is actually behind: a line that
# says "current" every single session is a line nobody reads by the third
# day. It exits 0 on no network, no manifest and a malformed one, so a
# hiccup cannot block a session start (practice: fail-gracefully).
python3 "$_hook_repo/tools/precedent_engine_freshness.py" --quiet || \
  echo "WARN: engine freshness did not run -- whether this repo's vendored engine is current is unknown this session" >&2

# Say whether anyone other than Morgan has pushed to `precedent-beta-v01`
# since he was last told -- Alex also commits here, and unlike the upstream
# check above, this one auto-advances the moment it reports (see
# tools/precedent_beta_watermark_check.py's own header for why the two
# watermarks are not the same shape). Session start always gets a line, the
# same way the upstream check above always does; the reply gate's own copy
# of this check (tools/precedent_gate.py) stays silent except on a real
# alert, which is where the "never repeat it every message" half lives.
python3 "$_hook_repo/tools/precedent_beta_watermark_check.py" || \
  echo "WARN: beta-branch watermark check did not run -- whether anyone else pushed to precedent-beta-v01 is unknown this session" >&2

# A bootstrap that blocks startup is worse than anything it protects against,
# and `set -e` above would otherwise let a non-zero last command take the
# session down. Every check here reports; none of them gates.
exit 0
