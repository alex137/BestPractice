#!/bin/bash
# Claude Code adapter: Stop hook. Install to .claude/hooks/stop-git-check.sh
# (wired by the adapter's settings.json). Blocks the agent from ending a
# turn with uncommitted, untracked, or unpushed work still sitting in the
# working tree — a repo-tracked backstop for whatever a given session's own
# environment doesn't already provide (some managed Claude Code environments
# ship an equivalent check outside the repo; this makes the same guarantee
# travel with the practice layer for the ones that don't). Harness-specific,
# unlike tools/bootstrap.sh: only Claude Code's hook mechanism can block a
# stop this way (see templates/harness/README.md's enforcement caveat).
#
# It also runs the REPLY gate (tools/precedent_gate.py reply), and since
# 2026-09-13 the blocking half of it (tools/precedent_reply_check.py): a
# practice source may declare a reply_check.json stating what a reply must
# close with, and this hook refuses the stop when the session's own
# transcript shows the reply did not. A repo where no source declares one is
# never blocked by it.
#
# 2026-09-14: and CLOSE DETECTION (tools/precedent_close_detect.py) -- the
# noticing end of the same engine. A session that merged something and is
# closing as ready to archive is asked, once, whether its own work turned up
# a rule worth keeping, and only when a Stage-1 detector actually found
# something. Silent otherwise, and silent in any repo whose sources declare
# no close_detect.json.
#
# 2026-09-13: every reason to stop is COLLECTED and reported in one exit-2
# message rather than the first one ending the script. Claude Code re-invokes
# a blocked Stop hook with stop_hook_active=true and this script exits clean
# on that, so whichever check came first used to be the only one that ever
# got enforced on a turn.
set -euo pipefail

# Claude Code re-invokes a Stop hook once after it already blocked a stop
# this turn, with stop_hook_active=true on stdin — exit clean rather than
# loop if this hook (or another one) already fired.
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  stop_hook_active="$(echo "$input" | jq -r '.stop_hook_active // empty' 2>/dev/null || true)"
  [[ "$stop_hook_active" == "true" ]] && exit 0
fi

# Not a git repo — the git half below has nothing to check, but the reply
# half still does: how a reply closes is not a property of a tree.
in_git=1
git rev-parse --git-dir >/dev/null 2>&1 || in_git=0

root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
tools=""
if [[ -n "$root" ]]; then
  for d in "$root/tools" "$root/process/upstream/tools"; do
    [[ -f "$d/precedent_gate.py" ]] && { tools="$d"; break; }
  done
fi

reasons=()

# The REPLY gate — the gate-triggered channel's other real invocation point,
# alongside templates/hooks/pre-push's `push` gate. Printing is advisory and
# costs nothing when the Rules are already being followed.
if [[ -n "$tools" ]]; then
  python3 "$tools/precedent_gate.py" reply >&2 || true

  # …and the BLOCKING half (2026-09-13). The advisory print above goes to
  # stderr on a clean exit, which Claude Code does not feed back to the
  # model — so for a rule about how the reply is WRITTEN it arrives after
  # the only moment it could have been applied. precedent_reply_check.py
  # reads the session transcript this hook is handed and refuses the stop
  # when the reply broke a requirement a practice source declared. It
  # checks nothing at all in a repo where no source declares one.
  if [[ -f "$tools/precedent_reply_check.py" ]]; then
    reply_out="$(echo "$input" | python3 "$tools/precedent_reply_check.py" --repo "$root" 2>&1)" || {
      reasons+=("$reply_out")
    }
  fi

  # …and CLOSE DETECTION (2026-09-14), the other end of the same engine.
  # precedent_close_detect.py asks, at the one moment all of its conditions
  # can be known, whether this session turned up a rule worth keeping: it
  # merged something, it is closing as ready to archive, it has not already
  # offered one, and a Stage-1 detector found something in this session's own
  # material. All four, or it is silent. Like the reply check, it detects
  # nothing in a repo where no source declares a close_detect.json.
  if [[ -f "$tools/precedent_close_detect.py" ]]; then
    close_out="$(echo "$input" | python3 "$tools/precedent_close_detect.py" --repo "$root" 2>&1)" || {
      reasons+=("$close_out")
    }
  fi
fi

if [[ "$in_git" == "1" ]] && [[ -n "$(git remote 2>/dev/null)" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    reasons+=("Uncommitted changes in the working tree. Commit (or intentionally discard) them before stopping.")
  fi

  if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    reasons+=("Untracked files in the working tree. Add and commit them, or add them to .gitignore, before stopping.")
  fi

  current_branch="$(git branch --show-current)"
  if [[ -n "$current_branch" ]] && git rev-parse -q --verify "origin/$current_branch" >/dev/null 2>&1; then
    unpushed="$(git rev-list "origin/$current_branch..HEAD" --count 2>/dev/null || echo 0)"
    if [[ "$unpushed" -gt 0 ]]; then
      reasons+=("$unpushed unpushed commit(s) on branch '$current_branch'. Push them to the remote before stopping.")
    fi
  fi
fi

if [[ ${#reasons[@]} -gt 0 ]]; then
  printf '%s\n' "${reasons[@]}" >&2
  exit 2
fi

exit 0
