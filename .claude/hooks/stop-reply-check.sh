#!/bin/bash
# Stop hook for the BestPractice repo itself, instantiated from
# templates/harness/claude-code/hooks/stop-reply-check.sh — logic unchanged;
# that file already resolves tools/precedent_gate.py correctly for this
# repo's own root-tools/ layout (it also checks process/upstream/tools/,
# which a dependent repo needs and this repo does not have).
#
# 2026-09-23: split out of .claude/hooks/stop-git-check.sh, which carried
# this reply-gate print, the blocking reply check, and close detection
# alongside its own git-cleanliness check, all as one `Stop` entry — see
# that file's header for the incident. This is now that repo's own copy of
# the other three, wired as its own `Stop` entry so a repo can decline
# git-cleanliness without losing these.
#
# It runs the REPLY gate (tools/precedent_gate.py reply): a practice source
# may declare a reply_check.json stating what a reply must close with, and
# this hook refuses the stop when the session's own transcript shows the
# reply did not. A repo where no source declares one is never blocked by it.
#
# And CLOSE DETECTION (tools/precedent_close_detect.py) -- the noticing end
# of the same engine. A session that merged something and is closing as
# ready to archive is asked, once, whether its own work turned up a rule
# worth keeping, and only when a Stage-1 detector actually found something.
# Silent otherwise, and silent in any repo whose sources declare no
# close_detect.json.
#
# Every reason to stop is COLLECTED and reported in one exit-2 message
# instead of the first one ending the script. Claude Code re-invokes a
# blocked Stop hook with stop_hook_active=true and this script exits clean
# on that, so whichever check came first was the only one that ever got
# enforced on a turn.
set -euo pipefail

# Claude Code re-invokes a Stop hook once after it already blocked a stop
# this turn, with stop_hook_active=true on stdin — exit clean rather than
# loop if this hook (or another one) already fired.
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  stop_hook_active="$(echo "$input" | jq -r '.stop_hook_active // empty' 2>/dev/null || true)"
  [[ "$stop_hook_active" == "true" ]] && exit 0
fi

root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
tools=""
if [[ -n "$root" ]]; then
  for d in "$root/tools" "$root/process/upstream/tools"; do
    [[ -f "$d/precedent_gate.py" ]] && { tools="$d"; break; }
  done
fi

reasons=()

if [[ -n "$tools" ]]; then
  # The advisory print — --brief, not the full Rules: this fires on every
  # single Stop, unconditionally, and the un-briefed form prints every
  # reply-gate practice's entire text, every time, whether or not anything
  # is wrong. reply-gate.sh (UserPromptSubmit) already prints the same list
  # in brief form at the START of the turn -- this call was reprinting it in
  # full at the END of every turn, on top of that, which is what "printing
  # is advisory and costs nothing" missed: it costs the person reading it.
  python3 "$tools/precedent_gate.py" reply --brief >&2 || true

  # …and the BLOCKING half. The advisory print above goes to stderr on a
  # clean exit, which Claude Code does not feed back to the model — so for a
  # rule about how the reply is WRITTEN it arrives after the only moment it
  # could have been applied. precedent_reply_check.py reads the session
  # transcript this hook is handed and refuses the stop when the reply broke
  # a requirement a practice source declared. It checks nothing at all in a
  # repo where no source declares one.
  if [[ -f "$tools/precedent_reply_check.py" ]]; then
    reply_out="$(echo "$input" | python3 "$tools/precedent_reply_check.py" --repo "$root" 2>&1)" || {
      reasons+=("$reply_out")
    }
  fi

  # …and CLOSE DETECTION, the other end of the same engine.
  # precedent_close_detect.py asks, at the one moment all of its conditions
  # can be known, whether this session turned up a rule worth keeping: it
  # merged something, it is closing as ready to archive, it has not already
  # offered one, and a Stage-1 detector found something in this session's own
  # material. All four, or it is silent. Like the reply check, it detects
  # nothing in a repo where no source declares a close_detect.json.
  if [[ -f "$tools/precedent_close_detect.py" ]]; then
    close_out="$(echo "$input" | python3 "$tools/precedent_close_detect.py" --repo "$root" 2>&1)" || {
      reasons+=("$close_out")
    }
  fi
fi

if [[ ${#reasons[@]} -gt 0 ]]; then
  printf '%s\n' "${reasons[@]}" >&2
  exit 2
fi

exit 0
