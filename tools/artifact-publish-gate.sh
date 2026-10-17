#!/bin/bash
# Claude Code adapter: PreToolUse hook on the Artifact tool that REFUSES to
# publish a page unless it is a copy of a fresh render of a registered
# document (practice: docs-track-models, "Published pages").
#
# WHY THIS EXISTS (2026-10-05, a consumer). A deck's review page was
# hand-built with its figures typed in and published straight to a link.
# Every check on script-derived figures reads files in the repository, so
# nothing compared the page with a model, and it went stale unseen.
#
# The check itself, its registry and its limits are in
# tools/artifact_publish_gate.py; this file only adapts it to the harness.
#
# FAIL-OPEN ON THE PLUMBING. No jq, no python3, or no engine script: exit 0
# silently. The engine fails open on a registry that will not load, too.
set -uo pipefail

# THE DECLARED PYTHON (2026-10-16, practice one-python). Claude Code starts
# a hook with its own PATH, so a bare `python3` here is the image's default,
# not the Python precedent.json declares, and lacks the packages setup put
# there. Setup links the declared one at .precedent/python-bin; it goes
# first on PATH here. The same block sits in every hook that starts python3;
# verify_harness keeps the copies identical. No link: python3 as before,
# never a refusal.
_precedent_pybin="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/.precedent/python-bin" || true
if [ -x "$_precedent_pybin/python3" ]; then PATH="$_precedent_pybin:$PATH"; fi

input="$(cat)"
project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
script="$project_dir/tools/artifact_publish_gate.py"
[[ -f "$script" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

reason="$(printf '%s' "$input" | CLAUDE_PROJECT_DIR="$project_dir" python3 "$script" 2>&1 >/dev/null)"
status=$?
if [[ $status -ne 2 ]]; then
  [[ -n "$reason" ]] && printf '%s\n' "$reason" >&2
  exit 0
fi

# The tool's reason already names the practice; the words are the tool's,
# so rewording them never touches this file (2026-10-07).
printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
