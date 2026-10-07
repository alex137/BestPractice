#!/bin/bash
# Claude Code adapter: PreToolUse wrapper that runs commit-identity.sh at
# most ONCE per session, not on every Edit/Write/Bash call.
#
# WHY THIS EXISTS, 2026-09-22 (Morgan: "it seems excessive to run it on
# EVERY write/bash call. Maybe we just run it on the FIRST write/bash call
# in the session, and just use that result for the rest of the session?").
# commit-identity.sh is wired at PreToolUse (matcher
# Edit|Write|NotebookEdit|Bash) alongside its original SessionStart entry,
# added the same day this file was, because a session rooted one directory
# above this repo (this project's own required multi-source sibling layout
# causes that -- gotcha-2026-09-13) runs NONE of its SessionStart hooks,
# silently, and the container's bot identity plus commit.gpgsign=true then
# sit unfixed until something notices. Running the full script -- git
# config reads, an identity resolution ladder, rewriting the pre-commit and
# prepare-commit-msg backstops, a settings.local.json write -- on every
# single tool call is real, repeated work for a fact that essentially never
# changes mid-session. The first run either finds everything already
# correct or fixes it; nothing later in the same session changes that
# answer, so nothing is gained by re-running it.
#
# Same seen-file idiom precedent-paths.sh already uses for the identical
# shaped problem (its own header explains the token-cost version of it):
# keyed on the PreToolUse payload's session_id, in $TMPDIR because it is
# scratch and losing it only costs one extra run, not correctness.
#
# FAILS TOWARD RUNNING, not toward skipping: no jq, no session_id in the
# payload, or a filesystem that refuses the marker all fall through to
# running commit-identity.sh anyway. A hook whose job is to fix identity
# must never silently decide not to over a missing dependency -- that is
# the exact failure this whole mechanism exists to prevent.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="$here/commit-identity.sh"

input="$(cat)"

session=""
if command -v jq >/dev/null 2>&1; then
  session="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null || true)"
fi

if [[ -n "$session" ]]; then
  marker="${TMPDIR:-/tmp}/precedent-commit-identity-ran-${session}"
  if [[ -e "$marker" ]]; then
    exit 0
  fi
  touch "$marker" 2>/dev/null || true
fi

exec "$target"
