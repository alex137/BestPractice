#!/usr/bin/env python3
"""Runs the hooks of the repo an action is about, for a session opened in the folder above the repos

precedent_run_repo_hooks.py EVENT -- for a session opened ABOVE the repos it
works in, run the EVENT hooks of the one repository the action is about,
exactly as that repository's own settings would have, and hand back their
answer: a refusal stays a refusal, added context stays context.

WHY (Morgan, 2026-10-19: "Okay, let's do it, Act and Booked", option B).
Claude Code runs the hooks of the folder a session is opened in, and a
session that works across several repositories is opened in /home/user,
which has none. precedent_run_session_hooks.py already covered SessionStart,
and tools/precedent_global_gate.sh added the merge and push gates one at a
time; everything else a repository wires -- the turn-start reply gate, the
end-of-reply check, the rules loaded before a file is edited, the commit
identity, the doc lint -- never ran in such a session. This is the one
switchboard instead: the cloud setup script writes one user-level line per
event pointing here (documentation/CLOUD_SETUP.md), and a hook a repository
adds later reaches these sessions with no change to that script.

WHICH REPOSITORY. For a tool call: the file it writes (`file_path`,
`notebook_path`); else, for Bash, a leading `cd DIR` or a `git -C DIR`; else
the GitHub repository an MCP call names (`owner`/`repo`) when a clone of it
is here; else the folder the call runs in (the hook input's `cwd`). For a
prompt or the end of a reply: the `cwd`. When none of that is in a
repository, the tool-call events run only the two gates that find their own
repository (push-check-gate.sh, merge-check-gate.sh, from the repository
this file sits in), as tools/precedent_global_gate.sh did; a prompt or the
end of a reply runs this repository's hooks, whose reply rules are the
universal ones.

Inside a repository with its own settings, its hooks already run natively,
so this does nothing. Its own failures never block: an unreadable input or
settings file runs nothing and exits 0.

    python3 tools/precedent_run_repo_hooks.py UserPromptSubmit|PreToolUse|PostToolUse|Stop
"""
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

EVENTS = ('UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop')
TOOL_EVENTS = ('PreToolUse', 'PostToolUse')
DEFAULT_TIMEOUT = 60
# The gates that find the repository a call is for by themselves, so they
# may run from this file's own repository when the call names none.
SELF_LOCATING = ('push-check-gate.sh', 'merge-check-gate.sh')
HERE = pathlib.Path(__file__).resolve().parent
ENGINE_REPO = HERE.parent


def _toplevel(path):
    """-> the git repository holding `path` that declares hooks, or None."""
    try:
        p = pathlib.Path(path).expanduser()
        d = p if p.is_dir() else p.parent
        while not d.exists() and d != d.parent:
            d = d.parent
        out = subprocess.run(['git', '-C', str(d), 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, timeout=20)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    top = out.stdout.strip()
    if out.returncode or not top:
        return None
    top = pathlib.Path(top)
    return top if (top / '.claude' / 'settings.json').is_file() else None


def _bash_dir(command, cwd):
    """-> the folder a Bash command works in, from a leading `cd DIR` or a
    `git -C DIR`, or None."""
    m = re.match(r'\s*cd\s+(\S+)\s*(?:&&|;|$)', command or '')
    if not m:
        m = re.search(r'\bgit\s+-C\s+(\S+)', command or '')
    if not m:
        return None
    try:
        word = shlex.split(m.group(1))[0]
    except (ValueError, IndexError):
        word = m.group(1)
    p = pathlib.Path(os.path.expanduser(word))
    return p if p.is_absolute() else pathlib.Path(cwd or '.') / p


def _clone_named(root, owner, repo):
    """-> the clone under `root` of github.com/<owner>/<repo>, or None."""
    want = f'{owner}/{repo}'.lower()
    try:
        children = sorted(root.iterdir())
    except OSError:
        return None
    for child in children:
        try:
            url = subprocess.run(['git', '-C', str(child), 'remote', 'get-url', 'origin'],
                                 capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        url = url.strip().lower().removesuffix('.git')
        if url.endswith('/' + want) and (child / '.claude' / 'settings.json').is_file():
            return child
    return None


def target_repo(event, payload, root):
    """-> the repository the action is about, or None."""
    cwd = payload.get('cwd') or ''
    if event in TOOL_EVENTS:
        ti = payload.get('tool_input') or {}
        for key in ('file_path', 'notebook_path'):
            if ti.get(key):
                return _toplevel(ti[key])
        if payload.get('tool_name') == 'Bash':
            d = _bash_dir(ti.get('command'), cwd)
            if d is not None:
                return _toplevel(d)
        if ti.get('owner') and ti.get('repo'):
            hit = _clone_named(root, ti['owner'], ti['repo'])
            if hit:
                return hit
    return _toplevel(cwd) if cwd else None


def _matches(matcher, tool_name):
    if not matcher or matcher == '*':
        return True
    try:
        return re.fullmatch(matcher, tool_name or '') is not None
    except re.error:
        return matcher == tool_name


def hooks_for(repo, event, tool_name):
    """-> [(command, timeout)] of `repo`'s own `event` hooks, in order,
    those whose matcher takes `tool_name` for a tool-call event."""
    try:
        data = json.loads((repo / '.claude' / 'settings.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    out = []
    for group in (data.get('hooks') or {}).get(event) or []:
        if event in TOOL_EVENTS and not _matches((group or {}).get('matcher'), tool_name):
            continue
        for hook in (group or {}).get('hooks') or []:
            if hook.get('type') == 'command' and hook.get('command'):
                out.append((hook['command'], hook.get('timeout') or DEFAULT_TIMEOUT))
    return out


def _blocks(obj):
    """-> True for a hook's JSON answer that stops the action."""
    hso = obj.get('hookSpecificOutput') or {}
    return (obj.get('decision') == 'block' or obj.get('continue') is False
            or hso.get('permissionDecision') in ('deny', 'ask'))


def run(event, raw, project):
    """-> (exit code, stdout, stderr) for the switchboard's answer."""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0, '', ''
    if not isinstance(payload, dict):
        return 0, '', ''
    project = pathlib.Path(project)
    if (project / '.git').exists() and (project / '.claude' / 'settings.json').is_file():
        return 0, '', ''        # the repository's own hooks run natively
    tool_name = payload.get('tool_name') or ''
    repo = target_repo(event, payload, project)
    only = None
    if repo is None:
        repo = ENGINE_REPO
        if event in TOOL_EVENTS:
            only = SELF_LOCATING
    plain, contexts, errs = [], [], []
    for command, timeout in hooks_for(repo, event, tool_name):
        if only and not any(name in command for name in only):
            continue
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
        try:
            r = subprocess.run(['bash', '-c', command], input=raw, cwd=str(repo), env=env,
                               capture_output=True, text=True, timeout=float(timeout))
        except subprocess.TimeoutExpired:
            errs.append(f'NOTE: precedent_run_repo_hooks: {command} ran past {timeout}s; skipped.')
            continue
        except OSError as e:
            errs.append(f'NOTE: precedent_run_repo_hooks: {command} could not run ({e}).')
            continue
        if r.returncode == 2:
            return 2, '', '\n'.join(errs + [r.stderr.rstrip()]).strip() + '\n'
        if r.stderr.strip():
            errs.append(r.stderr.rstrip())
        out = r.stdout.strip()
        if not out:
            continue
        if out.startswith('{'):
            try:
                obj = json.loads(out)
            except ValueError:
                obj = None
            if isinstance(obj, dict):
                if _blocks(obj):
                    return 0, out + '\n', '\n'.join(errs)
                ctx = (obj.get('hookSpecificOutput') or {}).get('additionalContext')
                if isinstance(ctx, str) and ctx.strip():
                    contexts.append(ctx.strip())
                continue
        plain.append(out)
    err = '\n'.join(e for e in errs if e)
    if contexts:
        return 0, json.dumps({'hookSpecificOutput': {
            'hookEventName': event,
            'additionalContext': '\n\n'.join(plain + contexts)}}) + '\n', err
    return 0, ('\n'.join(plain) + '\n') if plain else '', err


def main(argv):
    if not argv or argv[0] in ('-h', '--help') or argv[0] not in EVENTS:
        print(__doc__.split('\n\n')[0])
        print('usage: precedent_run_repo_hooks.py ' + '|'.join(EVENTS))
        return 0
    raw = sys.stdin.read()
    project = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    try:
        code, out, err = run(argv[0], raw, project)
    except Exception as e:                                   # noqa: BLE001
        print(f'NOTE: precedent_run_repo_hooks: {e}; nothing was run.', file=sys.stderr)
        return 0
    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err if err.endswith('\n') else err + '\n')
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
