#!/usr/bin/env python3
"""Runs each repo's own SessionStart hooks for a session opened in the folder above them

precedent_run_session_hooks.py -- run each repo's own SessionStart hooks
for a session opened ABOVE the repos it works in.

WHY THIS EXISTS (very deep check, 2026-09-28). Claude Code runs the hooks in
the `.claude/settings.json` of the directory a session is opened in. A
multi-repo session in Claude Code on the web is opened in the parent
directory (`/home/user`) that holds every clone, and that directory has no
settings of its own -- so no repo's SessionStart hook runs, silently: no
commit identity, no `.precedent/SESSION_PRACTICES.md`, no individual source
in force, no engine refresh (gotcha-2026-09-25-a-session-rooted-above-every-
repo-it-touches-gets-hooks-and). Nothing inside a repo can fix that, because
nothing inside a repo runs. A USER-level hook does run, whatever directory
the session opens in, and this is what it calls: for each git repository
directly under the session's directory, run the SessionStart commands that
repository's own settings declare, as that repository's own hook would have.

When the session is opened IN a repository with its own settings, that
repository's hooks already ran natively, and this does nothing -- so a
user-level hook calling it is safe in every kind of session. A settings file
in a folder that is NOT a repository (`/home/user/.claude/settings.json`,
which is where the hook lands when the setup script writes `/home/user/`
for `~`) is not a repository's hooks, so the runner still runs there.

Never fails the session: every error is reported on stderr and the exit is
always 0. A hook's own output goes to a log (it would otherwise be injected
into the session's context once per repository); stderr gets one line per
repository. Nothing here writes anything but that log -- each repository's
hooks do their own work, exactly as they would natively.

    python3 tools/precedent_run_session_hooks.py [ROOT]

ROOT defaults to $CLAUDE_PROJECT_DIR, else the current directory. The wiring
(one environment setup-script step) is in documentation/CLOUD_SETUP.md.
"""
import json
import os
import pathlib
import subprocess
import sys

TIMEOUT = 600
LOG_NAME = 'precedent-session-hooks.log'
# What reaches the session's context, in characters. Each repo's catalogue
# hook injects its own practice list; five repos' worth unbounded would be a
# large first turn, so what does not fit is left in the log and said so.
CONTEXT_CAP = 24000


def added_context(output):
    """-> [str]: what Claude Code would have put in context had the hook
    run natively -- its plain stdout, and every
    `hookSpecificOutput.additionalContext` it printed as a JSON line."""
    found, plain = [], []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            # A SessionStart hook's plain stdout reaches context natively
            # too, not only its JSON.
            if line:
                plain.append(line)
            continue
        try:
            ctx = (json.loads(line).get('hookSpecificOutput') or {}) \
                .get('additionalContext')
        except (ValueError, AttributeError):
            continue
        if isinstance(ctx, str) and ctx.strip():
            found.append(ctx.strip())
    if plain:
        found.insert(0, '\n'.join(plain))
    return found


def session_start_commands(repo):
    """-> [command] from `repo`'s own .claude/settings.json SessionStart
    hooks, in order; [] when it declares none or cannot be read."""
    try:
        data = json.loads((repo / '.claude' / 'settings.json')
                          .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    out = []
    for group in (data.get('hooks') or {}).get('SessionStart') or []:
        for hook in (group or {}).get('hooks') or []:
            if hook.get('type') == 'command' and hook.get('command'):
                out.append(hook['command'])
    return out


def repos_under(root):
    """-> the git repositories directly under `root` that declare hooks."""
    found = []
    for child in sorted(root.iterdir()):
        try:
            if (child / '.git').exists() and \
                    (child / '.claude' / 'settings.json').is_file():
                found.append(child)
        except OSError:
            continue
    return found


def run(root, log=None, say=None):
    """-> [(repo, command, returncode)] for every hook run. Runs nothing
    when `root` is itself a repository with settings of its own (its hooks
    ran natively)."""
    root = pathlib.Path(root).resolve()
    say = say or (lambda m: print(m, file=sys.stderr))
    if (root / '.git').exists() and \
            (root / '.claude' / 'settings.json').is_file():
        return []
    log = log or (pathlib.Path.home() / '.cache' / LOG_NAME)
    ran, contexts = [], []
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        fh = open(log, 'a', encoding='utf-8')
    except OSError:
        fh = None
    for repo in repos_under(root):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo),
                   PRECEDENT_PROJECT_DIR=str(repo))
        for cmd in session_start_commands(repo):
            try:
                r = subprocess.run(['bash', '-c', cmd], cwd=str(repo), env=env,
                                   capture_output=True, text=True,
                                   timeout=TIMEOUT)
                rc, stdout, out = r.returncode, r.stdout, r.stdout + r.stderr
            except (OSError, subprocess.TimeoutExpired) as e:
                rc, stdout, out = 1, '', f'{type(e).__name__}: {e}'
            ran.append((repo, cmd, rc))
            for ctx in added_context(stdout):
                if ctx not in [c for _, c in contexts]:
                    contexts.append((repo.name, ctx))
            if fh:
                fh.write(f'=== {repo.name}: {cmd} (exit {rc})\n{out}\n')
        n = sum(1 for r in ran if r[0] == repo)
        bad = [c for r, c, rc in ran if r == repo and rc != 0]
        say(f'precedent session hooks: {repo.name}: ran {n} SessionStart '
            f'hook(s)' + (f', {len(bad)} failed -- see {log}' if bad else ''))
    if fh:
        fh.close()
    if contexts:
        body, used = [], 0
        for name, ctx in contexts:
            piece = f'[{name}]\n{ctx}'
            # The first always goes in whole: a session opened in that one
            # repository would have received it in full.
            if body and used + len(piece) > CONTEXT_CAP:
                body.append(f'(more hook context did not fit; it is in {log})')
                break
            body.append(piece)
            used += len(piece)
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': '\n\n'.join(body)}}))
    return ran


def main(argv):
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    root = argv[0] if argv else (os.environ.get('CLAUDE_PROJECT_DIR')
                                 or os.getcwd())
    try:
        run(root)
    except Exception as e:                                       # noqa: BLE001
        print(f'precedent session hooks: skipped ({type(e).__name__}: {e})',
              file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
