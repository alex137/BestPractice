#!/bin/bash
# The script behind .claude/hooks/precedent-hooks.sh, the one settings.json
# entry per hook event that a hook added after 2026-10-07 is run through
# (tools/precedent_hooks.py says why). Called with the event's name.
#
# Most tool calls match no hook in either list, and this runs on every one,
# so it looks first, in bash, and starts Python only when a list names this
# event at all.
event="${1:-}"
[[ -n "$event" ]] || exit 0
tools="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$tools")"
grep -qs "\"$event\"" "$tools/hook_wiring.json" "$root/process/practice_hooks.json" || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$tools/precedent_hooks.py" "$event"
