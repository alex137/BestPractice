#!/usr/bin/env python3
"""The master maintainer's heartbeat: pushed on a schedule to a side branch, read at every session start, and a stale one named to the person once

precedent_heartbeat.py -- practice `master-maintainer`.

A repository that declares a `maintainer` block in precedent.json has one
standing session watching its trunk: after each landing it runs the full
check, refreshes generated tables, publishes renders and watches the
repositories vendored into it. That session proves it is alive by pushing a
heartbeat: one small JSON file on a dedicated branch (`maintainer-heartbeat`
by default), never on the trunk, so the trunk's history stays clean. Each
beat replaces the last (branch_store.py with history=False), so the branch
never grows.

Every other session reads the heartbeat's age at session start. A stale or
missing one is told to the session once, with the paste-ready prompt that
starts a new maintainer, and the session tells the person in plain words.
One maintainer serves everyone who works in the repository, so nobody needs
anything set up in their own environment.

WHY (S. Alexander Jacobson, 2026-10-20, strength: decided): checks that
depend on every session running them miss the sessions that do not, and the
per-person switchboard built to close that gap asked everyone for a setup
step. One maintainer per repository replaces it; the heartbeat is what makes
a dead maintainer visible at the next session start rather than weeks later.

Opt-in: a repository without a `maintainer` block hears nothing.

    "maintainer": {
      "title":            "Master maintainer (<repo>)",
      "prompt_file":      "process/jobs/maintainer.md",
      "session":          "session_...",            # written once it runs
      "heartbeat_branch": "maintainer-heartbeat",   # optional
      "stale_after_hours": 24                       # optional
    }

Run:
  python3 tools/precedent_heartbeat.py beat     the maintainer, on its schedule
  python3 tools/precedent_heartbeat.py age      exit 0 fresh, 1 stale or none, 2 not declared
  python3 tools/precedent_heartbeat.py prompt   print the prompt that starts a maintainer
  python3 tools/precedent_heartbeat.py --hook   SessionStart
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

DEFAULT_BRANCH = 'maintainer-heartbeat'
FILE = 'heartbeat.json'
# How often the maintainer beats and when a beat counts as stale. Neither is
# a fact about the world: a guess at a schedule cheap enough to keep and a
# limit loose enough that one missed beat is not an alarm (practice:
# constants-are-risk-inputs). A repository changes the limit in its own
# precedent.json; the interval is what the job prompt asks the maintainer to
# schedule. Proposed by the building session, 2026-10-20.
BEAT_EVERY_HOURS = 6
STALE_AFTER_HOURS = 24


def config(repo):
    """-> the repository's `maintainer` block, or None when it declares none."""
    try:
        d = json.loads((pathlib.Path(repo) / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    m = d.get('maintainer')
    if not isinstance(m, dict):
        return None
    return dict(m, _base=d.get('base_branch') or 'main')


def _git(repo, *args, timeout=15):
    try:
        r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                           text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _origin_slug(repo):
    url = _git(repo, 'remote', 'get-url', 'origin') or ''
    tail = url.rstrip('/').removesuffix('.git').split('github.com')[-1]
    return tail.lstrip(':/') or pathlib.Path(repo).resolve().name


def read(repo, cfg=None):
    """-> (state, beat): state is 'fresh', 'stale', 'none' or 'unreachable';
    beat is the heartbeat's JSON plus `age_hours`, or None. Reads with time
    limits, so a session start never hangs on the network."""
    cfg = cfg or config(repo) or {}
    branch = cfg.get('heartbeat_branch') or DEFAULT_BRANCH
    ref = f'refs/branch-store/{branch}'
    heads = _git(repo, 'ls-remote', '--heads', 'origin', branch, timeout=8)
    if heads is None:
        return 'unreachable', None
    if not heads:
        return 'none', None
    if _git(repo, 'fetch', '--quiet', '--no-tags', '--depth', '1', 'origin',
            f'+refs/heads/{branch}:{ref}', timeout=15) is None:
        return 'unreachable', None
    try:
        beat = json.loads(_git(repo, 'cat-file', 'blob', f'{ref}:{FILE}') or '{}')
        at = datetime.datetime.fromisoformat(beat['at_utc'].replace('Z', '+00:00'))
    except (ValueError, KeyError, TypeError, AttributeError):
        return 'none', None
    age = (datetime.datetime.now(datetime.timezone.utc) - at).total_seconds() / 3600
    beat['age_hours'] = round(age, 1)
    limit = float(cfg.get('stale_after_hours') or STALE_AFTER_HOURS)
    return ('fresh' if age <= limit else 'stale'), beat


def beat(repo, note=''):
    """Push a new heartbeat, replacing the last. -> the new commit."""
    import branch_store
    import precedent_detect
    import precedent_time
    cfg = config(repo) or {}
    branch = cfg.get('heartbeat_branch') or DEFAULT_BRANCH
    store = branch_store.BranchStore(branch=branch, repo=str(repo), history=False)
    trunk = _git(repo, 'rev-parse', f"origin/{cfg.get('_base', 'main')}") or ''
    body = {'at_utc': precedent_time.utc_iso(),
            'session': precedent_detect.this_session_id(),
            'trunk_seen': trunk[:12],
            'note': note}
    return store.transact(lambda tip: ({FILE: json.dumps(body, indent=2) + '\n'}, ()),
                          f'heartbeat {body["at_utc"]}')


def start_prompt(repo, cfg):
    """-> the prompt a person pastes into a new session to start the
    maintainer. Its From and For lines are the pasting session's to add."""
    slug = _origin_slug(repo)
    title = cfg.get('title') or f'Master maintainer ({pathlib.Path(slug).name})'
    job = cfg.get('prompt_file') or 'the master-maintainer practice'
    return (
        f'You are the master maintainer for {slug}, a standing session. Title this '
        f'session "{title}" and tag it role:worker. Read {job} on '
        f"{cfg.get('_base', 'main')} and run it as your standing job: whenever a "
        f'landing, a scheduled heartbeat or a message from another session wakes '
        f'you, do what it says, without asking each time. Start by pushing a '
        f'heartbeat (python3 tools/precedent_heartbeat.py beat) and scheduling '
        f'one every {BEAT_EVERY_HOURS} hours into this session.')


def hook_text(repo):
    """-> what the SessionStart hook tells the session, or '' for nothing."""
    import precedent_detect
    cfg = config(repo)
    if cfg is None:
        return ''
    state, b = read(repo, cfg)
    if state in ('fresh', 'unreachable'):
        return ''
    branch = cfg.get('heartbeat_branch') or DEFAULT_BRANCH
    why = (f"its last heartbeat on the `{branch}` branch is {b['age_hours']} hours "
           f"old, past the {cfg.get('stale_after_hours') or STALE_AFTER_HOURS}-hour "
           f"limit (from {b.get('session') or 'an unnamed session'})"
           if state == 'stale' else
           f"no heartbeat has ever been pushed to the `{branch}` branch")
    if cfg.get('session') and cfg['session'] == precedent_detect.this_session_id():
        return (f'YOU ARE THIS REPOSITORY\'S MASTER MAINTAINER and {why}. Push one '
                f'now (python3 tools/precedent_heartbeat.py beat) and check that '
                f'your scheduled heartbeat still exists.')
    return (
        f'THIS REPOSITORY HAS NO LIVE MASTER MAINTAINER: {why}. Nothing is running '
        f'the checks after a landing, refreshing generated tables or publishing '
        f'pages for it. In your first reply, tell the person once, in plain words '
        f'and with no file or tool names, that the repository has no maintainer '
        f'running and that one new session started with the prompt below fixes '
        f'it for everyone. Give the prompt as a paste block (with its From, For '
        f'and Paste into lines), then carry on with what they asked. Do not say '
        f'it again in this session.\n\nThe prompt:\n\n' + start_prompt(repo, cfg))


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__)
        return 0
    repo = os.environ.get('CLAUDE_PROJECT_DIR') or '.'
    if '--repo' in argv:
        i = argv.index('--repo')
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if '--hook' in argv:
        text = hook_text(repo)
        if text:
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart',
                                                     'additionalContext': text}}))
        return 0
    cfg = config(repo)
    if cfg is None:
        print('precedent_heartbeat: this repository declares no maintainer '
              '(no "maintainer" block in precedent.json).')
        return 2
    cmd = argv[0] if argv else 'age'
    if cmd == 'beat':
        new = beat(repo, ' '.join(argv[1:]))
        state, b = read(repo, cfg)
        if state != 'fresh':
            print(f'precedent_heartbeat: pushed {new}, but reading it back says '
                  f'{state}.', file=sys.stderr)
            return 1
        print(f"heartbeat pushed: {b['at_utc']} ({new[:12] if new else 'unchanged'})")
        return 0
    if cmd == 'prompt':
        print(start_prompt(repo, cfg))
        return 0
    state, b = read(repo, cfg)
    print(f"maintainer heartbeat: {state}"
          + (f", {b['age_hours']} hours old, from {b.get('session') or '?'}" if b else ''))
    return 0 if state == 'fresh' else 1


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:                                   # noqa: BLE001
        if '--hook' in sys.argv:
            print(f'NOTE: precedent_heartbeat: {e}; nothing checked.', file=sys.stderr)
            sys.exit(0)
        raise
