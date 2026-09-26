#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES writing a GitHub Actions
# workflow file straight onto GitHub through a file-write tool.
#
# WHY THIS EXISTS (practice: ci-workflow-approved, 2026-09-26). A session can
# change a repository two ways: edit a clone and `git push` it, or write a
# file straight onto GitHub with a tool such as the GitHub MCP server's
# create_or_update_file or push_files. The push gate checks every workflow
# file on the first route. The second never passes a push, so a session
# could add a workflow nobody approved and it would bill from the moment it
# landed. Morgan, 2026-09-26: "please implement your idea".
#
# WHAT IT DOES. Any path under .github/workflows/ ending .yml or .yaml in the
# tool's input is refused, and the session is told to make the change in a
# clone and push it, where ci-workflow-approved checks the file against the
# person's approval. It does not try to read approvals over the network: the
# push route already does that properly, so this door only has to point at
# it. Deleting a workflow is not a write and is let through.
#
# FAIL-OPEN ON THE PLUMBING (practice: fail-gracefully): no jq, or input it
# cannot read, lets the call through.
set -euo pipefail

input="$(cat)"
command -v jq >/dev/null 2>&1 || exit 0

paths="$(printf '%s' "$input" | jq -r '
  [.tool_input.path // empty,
   ((.tool_input.files // []) | .[]? | .path // empty)] | .[]' 2>/dev/null || true)"
hits="$(printf '%s\n' "$paths" | grep -E '^/?\.github/workflows/[^/]+\.ya?ml$' || true)"
[[ -n "$hits" ]] || exit 0

reason="Writing a GitHub Actions workflow straight onto GitHub is refused (practice: ci-workflow-approved):

$hits

A workflow file bills minutes on every run, and only the person decides it should exist. Make this change in a clone and git push it instead: the push check there compares the file with the approval recorded in precedent.json's github_ci_approved. If the person has not approved this exact content, show them the file and when it runs, and ask."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
