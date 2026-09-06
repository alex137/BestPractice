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

# Per-session memory of which practices have already been surfaced in full.
# Measured on the upstream repo (2026-09-06): an edit to any markdown file
# matches ten on-demand practices and prints ~1,000 words of Rule text, so a
# session editing thirty markdown files was handed the same ~1,000 words
# thirty times -- roughly forty thousand tokens of exact duplication, by a
# mechanism whose whole purpose is to spend context carefully. With this
# file, the first match prints the Rule and every later one prints the slug
# and its one-line clause. Keyed by session id so a new session starts
# fresh; in $TMPDIR because it is scratch, and losing it only means a Rule
# is shown twice.
session="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null || true)"
seen_args=()
if [[ -n "$session" ]]; then
  seen_args=(--seen-file "${TMPDIR:-/tmp}/precedent-paths-seen-${session}.txt")
fi

rules="$(python3 "$script" "${seen_args[@]}" "$path" 2>/dev/null || true)"
no_match="(no on-demand practice's applies_to matches the given path(s))"
[[ -n "$rules" && "$rules" != "$no_match" ]] || exit 0

# NO `permissionDecision` FIELD, deliberately (2026-09-06). This hook's
# whole job is to put the matching practice Rules in front of the model
# before it edits a file; deciding whether the edit is allowed is not its
# business and never was. It used to emit
# `"permissionDecision": "allow"` alongside the context, which in Claude
# Code's PreToolUse contract is a permission verdict, not a formality --
# on the reading where it settles the decision, every install of this
# adapter silently auto-approved every Edit, Write and NotebookEdit whose
# path matched any practice, which is most of them. Omitting the field
# injects exactly the same context and leaves the permission flow alone,
# so it is correct under either reading of the contract and costs nothing.
# It matters most for the case this repo already designs for: a
# non-technical contributor on a deliberately narrow permission set (see
# templates/nontechnical-document-project/AGENTS.md), where a practice
# loader quietly widening what may be written is the opposite of what was
# asked for.
python3 - "$rules" <<'PYEOF'
import json, sys

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": sys.argv[1],
    }
}))
PYEOF
