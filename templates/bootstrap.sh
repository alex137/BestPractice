#!/bin/bash
# Bootstrap template (practice 13) — environment setup as code, harness-neutral.
#
# Install to tools/bootstrap.sh in the dependent repo. Every entry here should
# exist because its absence cost a real session (practice 4): record the story
# in the instructions file's gotchas section, and encode the fix here so it
# applies itself. Keep it idempotent, fast when cached, and loud (a WARN,
# never a silent failure) when something can't install.
#
# Wiring (see templates/harness/): harnesses with a session hook run this
# automatically; for the rest, the instructions file tells the agent to run
# `bash tools/bootstrap.sh` at session start.
set -euo pipefail

# apt packages this repo's tooling needs (idempotent):
# if ! dpkg -s <package> >/dev/null 2>&1; then
#   apt-get install -y --no-install-recommends <package> >/dev/null 2>&1 || \
#     echo "WARN: <package> install failed - <what degrades without it>" >&2
# fi

# Python deps the repo's scripts import (cmarkgfm is doc_lint's exact
# GitHub-renderer check; keep it even if you add nothing else):
pip install --quiet cmarkgfm 2>/dev/null || \
  echo "WARN: pip install failed - doc_lint strikethrough check will be skipped" >&2
