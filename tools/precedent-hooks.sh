#!/bin/bash
# The script behind .claude/hooks/precedent-hooks.sh, the one settings.json
# entry per hook event that a hook added after 2026-10-07 is run through
# (tools/precedent_hooks.py says why). Called with the event's name.
#
# Most tool calls match no hook in either list, and this runs on every one,
# so it looks first, in bash, and starts Python only when a list names this
# event at all.

# THE DECLARED PYTHON (2026-10-16, practice one-python). Claude Code starts
# a hook with its own PATH, so a bare `python3` here is the image's default,
# not the Python precedent.json declares, and lacks the packages setup put
# there. Setup links the declared one at .precedent/python-bin; it goes
# first on PATH here. The same block sits in every hook that starts python3;
# verify_harness keeps the copies identical. No link: python3 as before,
# never a refusal.
_precedent_pybin="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/.precedent/python-bin" || true
if [ -x "$_precedent_pybin/python3" ]; then PATH="$_precedent_pybin:$PATH"; fi

event="${1:-}"
[[ -n "$event" ]] || exit 0
tools="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$tools")"
grep -qs "\"$event\"" "$tools/hook_wiring.json" "$root/process/practice_hooks.json" || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$tools/precedent_hooks.py" "$event"
