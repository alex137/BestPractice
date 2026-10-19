#!/usr/bin/env python3
"""Offers, once, to set up the switchboard in a person's cloud environment when it is missing

precedent_switchboard_offer.py -- at session start in Claude Code on the
web, when the person's environment does not run the switchboard
(precedent_run_repo_hooks.py), tell the session to offer setting it up: one
plain sentence in its first reply, and on a yes one environment edit the
person approves with a click. Silent outside the cloud, silent once the
switchboard is wired, and silent for good once the person has said no.

WHY (Morgan, 2026-10-19: "ALEX AND EVERYONE ELSE WILL FIND THIS VERY
FRUSTRATING", then "Yes, build it"). The switchboard needs a setup-script
step in each person's own cloud environment, once. Without it, every
session of theirs that works across several repositories skips every
repository's own checks, and nothing tells them: they would have to find
documentation/CLOUD_SETUP.md and paste a script. A session can make the
edit itself, behind the one approval prompt Claude Code always shows for
an environment change; this is what tells it to offer.

THE SCRIPT LIVES HERE (SETUP_SCRIPT), and documentation/CLOUD_SETUP.md
carries a copy that verify_harness holds byte-identical to it, because a
consuming repository carries this file and not that document.

A NO IS KEPT in the person's individual set: `"switchboard_offer":
"declined"` in its identity.json. Without an individual set there is
nowhere durable to keep it, and the offer comes back in the next session;
the instruction says so, so the session can tell the person.

    python3 tools/precedent_switchboard_offer.py --hook     # SessionStart
    python3 tools/precedent_switchboard_offer.py --script   # print the step
"""
import json
import os
import pathlib
import sys

DECLINED_KEY = 'switchboard_offer'
DECLINED = 'declined'
MARKER = 'precedent_run_repo_hooks.py'

SETUP_SCRIPT = r'''mkdir -p ~/.claude
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
def find(name):
    return f'f=$(ls -d /home/user/*/tools/{name} 2>/dev/null | head -1);'
wanted = [('SessionStart', find('precedent_run_session_hooks.py')
           + ' [ -n "$f" ] && python3 "$f" || true')]
for event in ('UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop'):
    wanted.append((event, find('precedent_run_repo_hooks.py')
                   + f' [ -z "$f" ] || python3 "$f" {event}'))
hooks = d.setdefault('hooks', {})
for event in list(hooks):
    hooks[event] = [e for e in hooks[event] if not any(
        'precedent_global_gate.sh' in h.get('command', '')
        for h in e.get('hooks', []))]
for event, cmd in wanted:
    entries = hooks.setdefault(event, [])
    if any(h.get('command') == cmd for e in entries for h in e.get('hooks', [])):
        continue
    entries.append({'hooks': [{'type': 'command', 'command': cmd, 'timeout': 900}]})
p.write_text(json.dumps(d, indent=2))
PY'''


def wired(home=None):
    """-> True when the user-level settings already call the switchboard."""
    p = pathlib.Path(home or pathlib.Path.home()) / '.claude' / 'settings.json'
    try:
        hooks = json.loads(p.read_text(encoding='utf-8')).get('hooks') or {}
    except (OSError, ValueError, AttributeError):
        return False
    return any(MARKER in (h.get('command') or '')
               for entries in hooks.values() for e in entries or []
               for h in (e or {}).get('hooks') or [])


def individual_identity():
    """-> (identity.json path, its data) of the person's individual set, or
    (None, None) when none resolves."""
    cfg = pathlib.Path(os.environ.get('PRECEDENT_USER_CONFIG',
                                      '~/.config/precedent/config.json')).expanduser()
    try:
        ind = (json.loads(cfg.read_text(encoding='utf-8')).get('individual') or {})
        path = pathlib.Path(ind['path']).expanduser() / 'identity.json'
        return path, json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None, None


def offer_text(identity_path):
    keep = (f'set `"{DECLINED_KEY}": "{DECLINED}"` in {identity_path} and commit '
            f'it there, so it is never offered again'
            if identity_path else
            'tell them it will be offered again in their next session, since '
            'they have no individual set to keep the answer in')
    return (
        "SWITCHBOARD NOT SET UP in this person's cloud environment. Their "
        "sessions that work across several repositories skip every "
        "repository's own checks, and nothing tells them. In your first "
        "reply, offer to set it up in one plain sentence, with no file or "
        "tool names: it is a one-time change to their environment that they "
        "approve with one click, and it runs on its own in every new session "
        "after that. On a yes: call get_environment, then update_environment "
        "with the step that `python3 tools/precedent_switchboard_offer.py "
        "--script` prints -- appended to their existing setup script, "
        "replacing an older copy of the same step (one starting "
        "`mkdir -p ~/.claude` that writes ~/.claude/settings.json hooks), "
        "and keeping every other line of theirs. On a no: " + keep + ". "
        "Ask once in this session, and not again in it either way.")


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__)
        return 0
    if '--script' in argv:
        print(SETUP_SCRIPT)
        return 0
    if os.environ.get('CLAUDE_CODE_REMOTE') != 'true' or wired():
        return 0
    path, ident = individual_identity()
    if isinstance(ident, dict) and ident.get(DECLINED_KEY) == DECLINED:
        return 0
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart',
                                             'additionalContext': offer_text(path)}}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:                                   # noqa: BLE001
        print(f'NOTE: precedent_switchboard_offer: {e}; no offer made.', file=sys.stderr)
        sys.exit(0)
