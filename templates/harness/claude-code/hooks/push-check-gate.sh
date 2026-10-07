#!/bin/bash
# PRECEDENT HOOK STUB. Every engine hook in .claude/hooks/ is this same file,
# byte for byte, and it is never edited: it runs the real script of the same
# name from the engine, tools/<this file's name>, which Update Vendors keeps
# current like any other engine file.
#
# WHY (Morgan, 2026-10-07, strength: decided: "It should no longer ask").
# Claude Code's auto mode holds any commit that changes a file under .claude/
# until the person says yes, and the hook scripts changed upstream on 27 days
# in one month, so nearly every Update Vendors stopped to ask about a change
# nobody needed to judge. The logic lives in tools/ now; this file, and so
# .claude/, stays the same. What a gate does arrives with the engine, under
# the person's "Update Vendors", after BestPractice's own full check.
#
# Where the script is: beside this stub's repository (.claude/hooks/ ->
# tools/, or bootstrap/ -> tools/ where a set ships the stub from there), else
# the project Claude Code names, else -- for the template copy inside
# BestPractice -- four levels up. No script anywhere (an engine older
# than its stub): say so and let the call through, as every gate fails open
# on its own plumbing (practice: fail-gracefully).
name="$(basename "$0")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for real in "$here/../../tools/$name" "$here/../tools/$name" \
            "${CLAUDE_PROJECT_DIR:-/nonexistent}/tools/$name" \
            "$here/../../../../tools/$name"; do
  if [[ -f "$real" ]]; then
    exec bash "$real" "$@"
  fi
done
echo "NOTE: $name: tools/$name is not here, so this hook did nothing. Update Vendors brings it." >&2
exit 0
