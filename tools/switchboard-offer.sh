#!/bin/bash
# SessionStart, through tools/hook_wiring.json: offer once to set up the
# switchboard in a cloud environment that lacks it. The logic is
# precedent_switchboard_offer.py; this only finds Python and fails open.
set -uo pipefail

# THE DECLARED PYTHON (2026-10-16, practice one-python). Claude Code starts
# a hook with its own PATH, so a bare `python3` here is the image's default,
# not the Python precedent.json declares, and lacks the packages setup put
# there. Setup links the declared one at .precedent/python-bin; it goes
# first on PATH here. The same block sits in every hook that starts python3;
# verify_harness keeps the copies identical. No link: python3 as before,
# never a refusal.
_precedent_pybin="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/.precedent/python-bin" || true
if [ -x "$_precedent_pybin/python3" ]; then PATH="$_precedent_pybin:$PATH"; fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$here/precedent_switchboard_offer.py" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$here/precedent_switchboard_offer.py" --hook
