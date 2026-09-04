#!/bin/bash
# Stop hook for the BestPractice repo itself (practice 13), instantiated
# from templates/harness/claude-code/hooks/stop-git-check.sh — logic
# unchanged; that file already resolves tools/precedent_gate.py correctly
# for this repo's own root-tools/ layout (it also checks
# process/upstream/tools/, which a dependent repo needs and this repo does
# not have). This repo went without a Stop hook at all until the same
# 2026-09-04 gate audit that fixed the template found the reply gate unwired
# — dogfooding it here closes the same gap in the repo that teaches it.
set -euo pipefail

# Claude Code re-invokes a Stop hook once after it already blocked a stop
# this turn, with stop_hook_active=true on stdin — exit clean rather than
# loop if this hook (or another one) already fired.
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  stop_hook_active="$(echo "$input" | jq -r '.stop_hook_active // empty' 2>/dev/null || true)"
  [[ "$stop_hook_active" == "true" ]] && exit 0
fi

# Not a git repo — nothing to check at all.
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# The REPLY gate (`disclose-landing`, `reply-links-files`, `repo-is-memory`,
# `verify-postcondition`) — the gate-triggered channel's other real
# invocation point, alongside templates/hooks/pre-push's `push` gate. It
# never blocks; printing costs nothing when the Rules are already being
# followed.
root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$root" ]]; then
  for gate_script in "$root/tools/precedent_gate.py" "$root/process/upstream/tools/precedent_gate.py"; do
    if [[ -f "$gate_script" ]]; then
      python3 "$gate_script" reply >&2 || true
      break
    fi
  done
fi

# No remote at all (e.g. a scratch clone) — nothing to push, nothing else to
# check below.
[[ -n "$(git remote 2>/dev/null)" ]] || exit 0

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Uncommitted changes in the working tree. Commit (or intentionally discard) them before stopping." >&2
  exit 2
fi

if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  echo "Untracked files in the working tree. Add and commit them, or add them to .gitignore, before stopping." >&2
  exit 2
fi

current_branch="$(git branch --show-current)"
if [[ -n "$current_branch" ]] && git rev-parse -q --verify "origin/$current_branch" >/dev/null 2>&1; then
  unpushed="$(git rev-list "origin/$current_branch..HEAD" --count 2>/dev/null || echo 0)"
  if [[ "$unpushed" -gt 0 ]]; then
    echo "$unpushed unpushed commit(s) on branch '$current_branch'. Push them to the remote before stopping." >&2
    exit 2
  fi
fi

exit 0
