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
repository. Each repository's hooks do their own work, exactly as they would
natively; this writes only that log and the allow rules below.

THE READ-ONLY ALLOW RULES (2026-10-14). Claude Code's settings docs: a
cloud session with several repositories "reads only the `enabledPlugins`
and `extraKnownMarketplaces` keys from each repository's
`.claude/settings.json`, not permission rules, hooks, `env`, or other
keys". So the allow rules a repository carries for Precedent's read-only
tools never reach exactly the session this runner serves, and a
`precedent_show.py` read went to auto mode's classifier: refused beside an
unrelated denied call, it put a "3 consecutive actions were blocked" dialog
on the person's phone. User-level settings are read in every session and
reloaded while it runs, so the runner adds those rules there, add-only:
the read-only ones the repositories' own settings allow and the settings
template has (precedent_vendor_engine.is_read_only_allow_rule), nothing
else. Morgan, 2026-10-14 (strength: decided): "let session start add the
read-only Precedent tools to the allow list".

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
# How precedent_session_practices.py's spoken-commands block begins (its
# SPOKEN_HEAD); the block is that line and the `- ` lines right after it.
# Not "up to a blank line": added_context() drops a hook's blank lines, so
# a consumer's whole output once read as one block. Every repo's block is
# lifted to the FRONT of what reaches the session, merged, before any cut:
# with five sets attached the cut fell before the ladder's stage words, and a
# session did not know "Debut" (2026-10-04). verify_harness checks that the
# two files agree on this text.
SPOKEN_PREFIX = 'Spoken commands in force here'


def lift_spoken(ctx):
    """-> (spoken lines, the rest of `ctx`): each spoken-commands block in
    `ctx` taken out, its head line included, and what remains."""
    spoken, rest, inside = [], [], False
    for line in ctx.split('\n'):
        if line.startswith(SPOKEN_PREFIX):
            inside = True
            spoken.append(line)
            continue
        if inside and not line.startswith('- '):
            inside = False
        (spoken if inside else rest).append(line)
    return spoken, '\n'.join(rest).strip()


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


def read_only_rules(root, repos):
    """-> the read-only Precedent tool allow rules the repositories under
    `root` declare or the settings template beside this file has, each
    once, in the order found. [] when the engine module is not here."""
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    try:
        import precedent_vendor_engine as pve
    except Exception:                                          # noqa: BLE001
        return []
    finally:
        sys.path.pop(0)
    found = []
    texts = []
    for base in [here.parent] + list(repos):
        for rel in (pve.SETTINGS_TEMPLATE, '.claude/settings.json'):
            try:
                texts.append((base / rel).read_text(encoding='utf-8'))
            except OSError:
                continue
    for text in texts:
        for rule in pve.read_only_allow_rules(text):
            if rule not in found:
                found.append(rule)
    return found


def ask_rules(root, repos):
    """-> the rules that always ask the person first, from the same files as
    read_only_rules (precedent_vendor_engine.engine_ask_rules), each once.
    They go beside the broad engine allow rule, never without it."""
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    try:
        import precedent_vendor_engine as pve
    except Exception:                                          # noqa: BLE001
        return []
    finally:
        sys.path.pop(0)
    found = []
    for base in [here.parent] + list(repos):
        for rel in (pve.SETTINGS_TEMPLATE, '.claude/settings.json'):
            try:
                text = (base / rel).read_text(encoding='utf-8')
            except OSError:
                continue
            for rule in pve.engine_ask_rules(text):
                if rule not in found:
                    found.append(rule)
    return found


def allow_at_user_level(rules, settings, ask=()):
    """ADD `rules` to the user-level settings' permissions.allow and `ask` to
    its permissions.ask, never editing, moving or removing what is there,
    and never one the file denies; the broad engine allow rule only with
    every ask rule beside it (precedent_vendor_engine.
    permission_rules_to_add, 2026-10-17). -> [added]; [] when there is
    nothing to add or the file does not parse (left exactly as it was)."""
    path = pathlib.Path(settings)
    try:
        data = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    except (OSError, ValueError):
        return []
    perms = data.get('permissions') if isinstance(data, dict) else None
    if not isinstance(data, dict) or (perms is not None and not isinstance(perms, dict)):
        return []
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    try:
        import precedent_vendor_engine as pve
        add, add_ask = pve.permission_rules_to_add(perms, list(rules), list(ask))
    except Exception:                                          # noqa: BLE001
        # No engine to say when the broad rule is safe: never write it.
        have = set((perms or {}).get('allow') or []) | set((perms or {}).get('deny') or [])
        add = [r for r in rules if r not in have
               and r != 'Bash(python3 tools/precedent_*)']
        add_ask = []
    finally:
        sys.path.pop(0)
    if not add and not add_ask:
        return []
    if add_ask:
        data.setdefault('permissions', {}).setdefault('ask', []).extend(add_ask)
    if add:
        data.setdefault('permissions', {}).setdefault('allow', []).extend(add)
    add = add + add_ask
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    except OSError:
        return []
    return add


def run(root, log=None, say=None, user_settings=None):
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
    # `user_settings` is passed by main() alone, so a test or another
    # caller of run() never writes the real user-level file.
    added = (allow_at_user_level(read_only_rules(root, repos_under(root)),
                                 settings=user_settings,
                                 ask=ask_rules(root, repos_under(root)))
             if user_settings is not None else [])
    if added:
        say(f'precedent session hooks: added {len(added)} Precedent tool '
            f'rule(s) to user-level settings (the tools that land, produce or '
            f'merge always ask), since a session above several repositories '
            f'reads none of theirs')
    if contexts:
        # The spoken commands first, whole and once, ahead of every repo's
        # output: what a person says must be understood before anything is
        # cut (SPOKEN_PREFIX).
        heads, items, lifted = [], [], []
        for name, ctx in contexts:
            spoken, rest = lift_spoken(ctx)
            for line in spoken:
                if line.startswith(SPOKEN_PREFIX):
                    if not heads:
                        heads.append(line)
                elif line not in items:
                    items.append(line)
            if rest:
                lifted.append((name, rest))
        contexts = lifted
        body, used = [], 0
        if items:
            first = '\n'.join(heads + items)
            body.append(first)
            used += len(first)
        for name, ctx in contexts:
            piece = f'[{name}]\n{ctx}'
            # The first always goes in whole: a session opened in that one
            # repository would have received it in full.
            if (body and (used + len(piece) > CONTEXT_CAP)
                    and (len(body) > 1 or not items)):
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
        run(root, user_settings=pathlib.Path.home() / '.claude' / 'settings.json')
    except Exception as e:                                       # noqa: BLE001
        print(f'precedent session hooks: skipped ({type(e).__name__}: {e})',
              file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
