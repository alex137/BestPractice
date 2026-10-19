#!/bin/bash
# precedent_global_gate.sh GATE -- run one of the engine's gates (GATE is
# merge-check-gate.sh, push-check-gate.sh or stop-reply-check.sh) for a session opened ABOVE its
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
    merge-check-gate.sh|push-check-gate.sh|stop-reply-check.sh) ;;
    *) echo "NOTE: precedent_global_gate.sh: no gate named '$gate'; nothing checked." >&2
       exit 0 ;;
esac
# THE DECLARED PYTHON (2026-10-16, practice one-python). Claude Code starts
# a hook with its own PATH, so a bare `python3` here is the image's default,
# not the Python precedent.json declares, and lacks the packages setup put
# there. Setup links the declared one at .precedent/python-bin; it goes
# first on PATH here. The same block sits in every hook that starts python3;
# verify_harness keeps the copies identical. No link: python3 as before,
# never a refusal.
_precedent_pybin="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/.precedent/python-bin" || true
if [ -x "$_precedent_pybin/python3" ]; then PATH="$_precedent_pybin:$PATH"; fi
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
# The reply check judges the reply against the repository it runs in,
# found from the folder it starts in. A Stop hook names no repository, so it
# runs in the one the session was last working in (the hook input's `cwd`),
# or, when that folder is in none, in the engine's own: its reply rules are
# the universal ones, and the person's own and brought sets resolve from
# their user-level config wherever it runs. Added 2026-10-19 (Morgan: "Fix
# the link check"): until then no reply check ran for a session opened
# above its repositories, so nothing caught a Boildown that linked nothing.
if [[ "$gate" == stop-reply-check.sh ]]; then
    input="$(cat)"
    dir="$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd") or "")
except Exception: print("")' 2>/dev/null)"
    top="$( [[ -n "$dir" ]] && git -C "$dir" rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -z "$top" || ! -f "$top/tools/precedent_gate.py" && ! -f "$top/process/upstream/tools/precedent_gate.py" ]]; then
        top="$(cd "$here/.." && pwd)"
    fi
    cd "$top" || exit 0
    printf '%s' "$input" | CLAUDE_PROJECT_DIR="$top" bash "$here/$gate"
    exit $?
fi
# The gate reads its own tool from the project folder, which here is the
# folder above every repository and holds none: name the engine's
# repository instead. The gate still judges the repository the call is for,
# found among that one's neighbours.
CLAUDE_PROJECT_DIR="$(cd "$here/.." && pwd)" exec bash "$here/$gate"
