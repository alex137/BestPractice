#!/bin/bash
# Claude Code adapter: PreToolUse hook on add_repo that REFUSES a sweep of
# repository attaches the person did not ask for (practice: reach-or-ask).
# tools/repo_attach_gate.py holds the logic and says why (Morgan,
# 2026-10-29: "I want to prevent that."). Wired through
# tools/hook_wiring.json, so nothing under .claude/ changed.
#
# FAIL-OPEN ON THE PLUMBING: no python3 or no script exits 0, the same as
# every gate here (practice: fail-gracefully).
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
[[ -f "$here/repo_attach_gate.py" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$here/repo_attach_gate.py"
