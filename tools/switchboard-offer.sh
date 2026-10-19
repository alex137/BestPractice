#!/bin/bash
# SessionStart, through tools/hook_wiring.json: offer once to set up the
# switchboard in a cloud environment that lacks it. The logic is
# precedent_switchboard_offer.py; this only finds Python and fails open.
set -uo pipefail

_precedent_pybin="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/.precedent/python-bin" || true
if [ -x "$_precedent_pybin/python3" ]; then PATH="$_precedent_pybin:$PATH"; fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$here/precedent_switchboard_offer.py" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$here/precedent_switchboard_offer.py" --hook
