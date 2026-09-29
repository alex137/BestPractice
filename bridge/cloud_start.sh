#!/usr/bin/env bash
# cloud_start.sh -- start the chat bridge inside a Claude Code cloud session.
#
# Reads everything from environment variables set in the cloud environment's
# settings (bridge/SETUP.md, step 3), builds the config, installs local
# Whisper if voice notes use it, checks the setup, prints an invite link, and
# runs the bridge in the foreground. The session runs this in the background.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
venv="${CHATBRIDGE_VENV:-$HOME/.cache/chatbridge-venv}"
cfg="$HOME/.config/chatbridge/config.json"

[ -x "$venv/bin/python" ] || python3 -m venv "$venv"
if [ "${CHATBRIDGE_VOICE:-whisper-local}" = whisper-local ] \
   && ! "$venv/bin/python" -c "import faster_whisper" 2>/dev/null; then
  echo "installing local Whisper (once per machine)..."
  "$venv/bin/pip" install --quiet faster-whisper
fi

"$venv/bin/python" "$here/run.py" cloud-config --out "$cfg"
if ! "$venv/bin/python" "$here/run.py" check --config "$cfg"; then
  echo "chatbridge: not started -- fix the FIX lines above, then run this again."
  exit 1
fi
if [ -z "${CHATBRIDGE_TELEGRAM_USER_ID:-}" ]; then
  echo "INVITE LINK (open it on your phone and tap Start):"
  "$venv/bin/python" "$here/run.py" invite --config "$cfg" --handle "${CHATBRIDGE_HANDLE:-me}"
fi
exec "$venv/bin/python" -u "$here/run.py" run --config "$cfg"
