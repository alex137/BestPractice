#!/bin/bash
# precedent_global_gate.sh GATE -- run one of the engine's gates (GATE is
# merge-check-gate.sh or push-check-gate.sh) for a session opened ABOVE its
# repositories, from the user-level settings the cloud environment's setup
# script writes (documentation/CLOUD_SETUP.md).
#
# WHY (Morgan, 2026-10-19: "Go"). A repository's gates are hooks in its own
# .claude/settings.json, and Claude Code runs only the hooks of the folder a
# session is opened in. A session opened in /home/user, the folder holding
# every repository, ran none of them: its merges into main were never
# checked, and #1206 and #1217 reached main broken. The setup script writes
# this into ~/.claude/settings.json before the session starts, so Claude
# Code reads it at startup; no session edits its own settings, which auto
# mode would hold for a yes.
#
# Each gate already finds the repository a call is for -- `git -C`, a
# leading `cd`, the pull request's owner and repo, the call's working
# folder -- and runs THAT repository's own check. This file only stays out
# of the way where the repository's own hooks already run: a session opened
# in a folder whose .claude/settings.json wires the same gate. The hook's
# input arrives on stdin and passes straight through.
gate="${1:-}"
case "$gate" in
    merge-check-gate.sh|push-check-gate.sh) ;;
    *) echo "NOTE: precedent_global_gate.sh: no gate named '$gate'; nothing checked." >&2
       exit 0 ;;
esac
project="${CLAUDE_PROJECT_DIR:-$PWD}"
if [[ -f "$project/.claude/settings.json" ]] \
        && grep -q "$gate" "$project/.claude/settings.json" 2>/dev/null; then
    exit 0      # the project's own hook runs this gate; never twice
fi
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if [[ ! -f "$here/$gate" ]]; then
    echo "NOTE: precedent_global_gate.sh: tools/$gate is not beside this file, so nothing was checked." >&2
    exit 0
fi
# The gate reads its own tool from the project folder, which here is the
# folder above every repository and holds none: name the engine's
# repository instead. The gate still judges the repository the call is for,
# found among that one's neighbours.
CLAUDE_PROJECT_DIR="$(cd "$here/.." && pwd)" exec bash "$here/$gate"
