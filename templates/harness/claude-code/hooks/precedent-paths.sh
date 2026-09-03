#!/bin/bash
# Claude Code adapter: PreToolUse hook wrapper for the path-triggered
# loading channel (PRACTICE_ENGINE_PLAN.md, "How an Agent Knows Which
# Practices to Load": "A PreToolUse hook matches the edited file against
# every practice's applies_to globs and prints the matching ## Rule
# sections."). Install to .claude/hooks/precedent-paths.sh (wired by the
# adapter's settings.json, matcher "Edit|Write|NotebookEdit").
#
# All real matching logic -- the glob semantics, the practice catalogue
# read -- lives in the vendored tools/precedent_paths.py, the same engine
# tools/behavioral_replay.py drives against commit history. This wrapper
# only reads the tool call's target path off stdin, shells out, and
# reshapes the result into a PreToolUse response. Keep it free of matching
# logic so other harnesses can share the same engine behind their own
# wrapper. practice: engine-plus-host-shims
#
# Never blocks the tool call: every failure path below (no jq, no python3,
# no engine present, an unparseable stdin payload, no matching practice)
# falls through to a silent `exit 0` with no stdout, which Claude Code
# treats as "no opinion" -- an advisory context feature earning a hard
# failure on a missing dependency would be worse than the feature not
# firing at all.
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# Edit and Write both key the target file as tool_input.file_path;
# NotebookEdit's own field name is not settled in the public hooks
# reference as of this writing (2026-09-03) -- try file_path first, fall
# back to notebook_path, so this keeps working whichever one a given
# Claude Code build actually sends.
path="$(printf '%s' "$input" \
  | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null \
  || true)"
[[ -n "$path" ]] || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-.}"
script="$project_dir/tools/precedent_paths.py"
[[ -f "$script" ]] || exit 0

rules="$(python3 "$script" "$path" 2>/dev/null || true)"
no_match="(no on-demand practice's applies_to matches the given path(s))"
[[ -n "$rules" && "$rules" != "$no_match" ]] || exit 0

python3 - "$rules" <<'PYEOF'
import json, sys

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "additionalContext": sys.argv[1],
    }
}))
PYEOF
