#!/usr/bin/env python3
"""The master maintainer's heartbeat: pushed on a schedule to a side branch, read at every session start, and a stale one named to the person once

precedent_heartbeat.py -- practice `master-maintainer`.

A repository that declares a `maintainer` block in precedent.json has one
standing session watching its trunk: after each landing it runs the full
check, refreshes generated tables, publishes renders and watches the
repositories vendored into it. That session proves it is alive by pushing a
heartbeat: one small JSON file on the `coord` branch, never on the trunk, so
the trunk's history stays clean. The file is the landing queue's own
heartbeat record (tools/land_queue.py `beat maintainer`); this tool adds
only what to do about its age.

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
      "stale_after_hours": 24                       # optional
    }

Run:
  python3 tools/precedent_heartbeat.py beat     the maintainer, on its schedule
  python3 tools/precedent_heartbeat.py age      exit 0 fresh, 1 stale or none, 2 not declared
  python3 tools/precedent_heartbeat.py prompt   print the prompt that starts a maintainer
  python3 tools/precedent_heartbeat.py --hook   SessionStart
"""
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

JOB = 'maintainer'
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


def _limit(cfg):
    v = cfg.get('stale_after_hours')
    return float(STALE_AFTER_HOURS if v is None else v)


def _origin_slug(repo):
    url = _git(repo, 'remote', 'get-url', 'origin') or ''
    tail = url.rstrip('/').removesuffix('.git').split('github.com')[-1]
    return tail.lstrip(':/') or pathlib.Path(repo).resolve().name


def read(repo, cfg=None):
    """-> (state, age_hours): state is 'fresh', 'stale', 'none' or
    'unreachable'; age_hours is None unless a beat was found."""
    import branch_store
    import land_queue
    cfg = cfg or config(repo) or {}
    try:
        age = land_queue.beats(land_queue._store(repo=pathlib.Path(repo))).get(JOB)
    except (branch_store.Unreachable, OSError, subprocess.SubprocessError):
        return 'unreachable', None
    if age is None:
        return 'none', None
    return ('fresh' if age <= _limit(cfg) else 'stale'), round(age, 1)


def beat(repo):
    """Record a heartbeat for the maintainer on the coord branch."""
    import land_queue
    land_queue.beat(land_queue._store(repo=pathlib.Path(repo)), JOB)


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
    state, age = read(repo, cfg)
    if state in ('fresh', 'unreachable'):
        return ''
    why = (f"its last heartbeat on the `coord` branch is {age} hours old, past "
           f"the {_limit(cfg):g}-hour limit"
           if state == 'stale' else
           "no heartbeat has ever been recorded on the `coord` branch")
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
        beat(repo)
        state, age = read(repo, cfg)
        if state != 'fresh':
            print(f'precedent_heartbeat: a beat was pushed, but reading it back '
                  f'says {state}.', file=sys.stderr)
            return 1
        print(f'heartbeat recorded on the coord branch ({age} hours old)')
        return 0
    if cmd == 'prompt':
        print(start_prompt(repo, cfg))
        return 0
    state, age = read(repo, cfg)
    print(f"maintainer heartbeat: {state}" + (f", {age} hours old" if age is not None else ''))
    return 0 if state == 'fresh' else 1


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:                                   # noqa: BLE001
        if '--hook' in sys.argv:
            print(f'NOTE: precedent_heartbeat: {e}; nothing checked.', file=sys.stderr)
            sys.exit(0)
        raise
