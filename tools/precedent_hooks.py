#!/usr/bin/env python3
"""Runs the hooks listed in tools/hook_wiring.json and process/practice_hooks.json for one Claude Code hook event, and hands Claude Code one combined answer

precedent_hooks.py -- one fixed entry in .claude/settings.json per hook
event, so a hook added later never changes that file.

    .claude/settings.json  ->  .claude/hooks/precedent-hooks.sh <Event>
                           ->  tools/precedent-hooks.sh <Event>   (the stub's script)
                           ->  tools/precedent_hooks.py <Event>   (this file)

WHY (Morgan, 2026-10-07, strength: decided: "It should no longer ask").
Claude Code's auto mode holds any commit that changes a file under .claude/
until the person says yes. The hook scripts became stubs that run their
engine copy in tools/ the same day, which ended the asks over what a hook
DOES. What was left was .claude/settings.json itself: every new hook was a
new entry there, and so a question at every repository's next Update
Vendors (it changed on 9 days in the month before). This file is the last
entry that ever needs adding: the hooks it runs are listed in two files
outside .claude/, which change with no question asked:

  tools/hook_wiring.json      the engine's own hooks added from 2026-10-07 on,
                              per kind of repository, vendored with the engine
  process/practice_hooks.json what declared practices' `hooks:` fields ask
                              for, written by precedent_sync_views.py
  .precedent/practice_hooks.json  the same, for a set this repository does
                              not track (one the person brings): untracked,
                              written at session start (2026-10-13)

The hooks wired straight into settings.json before that date stay there;
nothing here runs them twice.

ONE ANSWER FROM MANY. Claude Code reads one hook's exit status, stdout and
stderr; this runs several, at once, and combines them the way Claude Code
would have treated them as separate entries:
  - exit 2 from any: exit 2, every blocker's stderr joined.
  - a PreToolUse `deny` from any: deny, every reason joined (`ask` likewise,
    below deny); an `allow` is never passed on, since it would skip the
    person's own permission prompt for the others' sake.
  - `decision: block` from any: block, the reasons joined.
  - additionalContext, and plain stdout at SessionStart and UserPromptSubmit
    (where Claude Code adds it as context), joined into one.
  - stderr is passed on as it came.
A hook that outlives its timeout is killed and treated as Claude Code
treats one: a non-blocking error, said on stderr.

FAIL-OPEN ON THE PLUMBING (practice: fail-gracefully): an unreadable list,
an unparseable payload or a missing script lets the call through, with a
line on stderr.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE_WIRING = HERE / 'hook_wiring.json'
PRACTICE_WIRING = ROOT / 'process' / 'practice_hooks.json'
SESSION_WIRING = ('.precedent', 'practice_hooks.json')
DEFAULT_TIMEOUT = 60
CONTEXT_FROM_STDOUT = ('SessionStart', 'UserPromptSubmit')


def _load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        print(f'precedent_hooks: {path.name} did not read ({exc}); its hooks did '
              f'not run', file=sys.stderr)
        return None


def repo_kind(root=ROOT):
    """'consumer' or 'source' from the engine manifest; BestPractice itself,
    which has none, runs the consumer list; a manifest with no kind gets no
    engine list, as precedent_vendor_engine.HOOK_WIRING does not guess."""
    manifest = _load(root / 'tools' / 'ENGINE_MANIFEST.json')
    if manifest is None:
        return 'consumer'
    return manifest.get('kind') if isinstance(manifest, dict) else None


def declined(root=ROOT):
    cfg = _load(root / 'precedent.json')
    if not isinstance(cfg, dict):
        return set()
    return {Path(str(e['path'])).name for e in (cfg.get('declined_adapters') or [])
            if isinstance(e, dict) and e.get('path')}


def base_branch(root=ROOT):
    cfg = _load(root / 'precedent.json')
    b = cfg.get('base_branch') if isinstance(cfg, dict) else None
    return b.strip() if isinstance(b, str) and b.strip() else 'main'


def entries_for(event, tool_name, root=ROOT, engine=None, practice=None,
                session=None):
    """-> [(label, argv, timeout)] the hooks to run for this event and tool."""
    engine = _load(root / 'tools' / 'hook_wiring.json') if engine is None else engine
    practice = _load(root / 'process' / 'practice_hooks.json') if practice is None else practice
    # practice: practice-carries-its-files -- a set the person brings ships
    # its hook's script untracked, and lists the hook here, untracked too.
    session = _load(root.joinpath(*SESSION_WIRING)) if session is None else session
    kind = repo_kind(root)
    skip = declined(root)
    out = []
    rows = []
    if isinstance(engine, dict) and kind:
        rows += [dict(r, _engine=True) for r in (engine.get(kind) or [])
                 if isinstance(r, dict)]
    for listed in (practice, session):
        if isinstance(listed, dict):
            rows += [r for r in (listed.get('hooks') or []) if isinstance(r, dict)]
    seen = set()
    for r in rows:
        if r.get('event') != event:
            continue
        matcher = r.get('matcher')
        if matcher and not re.fullmatch(matcher, tool_name or ''):
            continue
        timeout = int(r.get('timeout') or DEFAULT_TIMEOUT)
        if r.get('_engine'):
            script = str(r.get('script') or '')
            if not script or script in skip:
                continue
            args = str(r.get('args') or '').replace('{base}', base_branch(root)).split()
            out.append((script, ['bash', str(root / 'tools' / script), *args], timeout))
        else:
            command = str(r.get('command') or '')
            if not command or command in seen:
                continue
            seen.add(command)
            out.append((command, ['bash', '-c', command], timeout))
    return out


def _run(label, argv, timeout, payload, env):
    try:
        r = subprocess.run(argv, input=payload, capture_output=True, text=True,
                           timeout=timeout, env=env)
        return label, r.returncode, r.stdout, r.stderr, False
    except subprocess.TimeoutExpired:
        return label, None, '', f'precedent_hooks: {label} ran past its {timeout}s and was stopped; nothing it would have said was used\n', True
    except OSError as exc:
        return label, None, '', f'precedent_hooks: {label} did not start ({exc})\n', False


def combine(event, results):
    """-> (exit status, stdout text, stderr text) for Claude Code, from each
    hook's (label, rc, stdout, stderr, timed_out). See the module docstring."""
    err, blockers, denies, asks, blocks, ctx, notes = [], [], [], [], [], [], []
    stop = None
    for label, rc, out, e, _t in results:
        if e:
            err.append(e)
        if rc == 2:
            blockers.append(e.strip() or f'{label} blocked this')
            continue
        text = (out or '').strip()
        if not text:
            continue
        data = None
        if text.startswith('{'):
            try:
                data = json.loads(text)
            except ValueError:
                data = None
        if not isinstance(data, dict):
            if event in CONTEXT_FROM_STDOUT:
                ctx.append(text)
            else:
                err.append(text + '\n')
            continue
        hso = data.get('hookSpecificOutput') or {}
        decision = hso.get('permissionDecision')
        reason = str(hso.get('permissionDecisionReason') or '')
        if decision == 'deny':
            denies.append(reason or f'{label} refused this')
        elif decision == 'ask':
            asks.append(reason or f'{label} asks before this')
        if hso.get('additionalContext'):
            ctx.append(str(hso['additionalContext']))
        if data.get('decision') == 'block':
            blocks.append(str(data.get('reason') or f'{label} blocked this'))
        if data.get('systemMessage'):
            notes.append(str(data['systemMessage']))
        if data.get('continue') is False:
            stop = str(data.get('stopReason') or stop or '')
    if blockers:
        return 2, '', '\n\n'.join(blockers) + '\n'
    obj, hso = {}, {}
    if denies:
        hso.update(permissionDecision='deny', permissionDecisionReason='\n\n'.join(denies))
    elif asks:
        hso.update(permissionDecision='ask', permissionDecisionReason='\n\n'.join(asks))
    if ctx:
        hso['additionalContext'] = '\n\n'.join(ctx)
    if hso:
        obj['hookSpecificOutput'] = dict(hookEventName=event, **hso)
    if blocks:
        obj.update(decision='block', reason='\n\n'.join(blocks))
    if notes:
        obj['systemMessage'] = '\n'.join(notes)
    if stop is not None:
        obj.update({'continue': False, 'stopReason': stop})
    return 0, (json.dumps(obj) if obj else ''), ''.join(err)


GIT_EVENTS = ('pre-push',)


def _attach_hints(root=ROOT):
    """-> {name: 'owner/repo'} for the sources whose repository is known:
    the individual set from the user config, the sets it brings from its
    `brings`, and a declared shared set from PRECEDENT_SOURCE_BASE_URL."""
    import precedent_resolve as pr
    hints = {}

    def owner_repo(url):
        m = re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$', url or '')
        return f'{m.group(1)}/{m.group(2)}' if m else None

    try:
        cfg = json.loads(Path(os.environ.get(pr.USER_CONFIG_ENV, str(
            pr.DEFAULT_USER_CONFIG))).expanduser().read_text(encoding='utf-8'))
        ind = cfg.get('individual') or {}
    except (OSError, ValueError, AttributeError):
        ind = {}
    if isinstance(ind, dict):
        if owner_repo(ind.get('repo_url')):
            hints[ind.get('name') or pr.DEFAULT_INDIVIDUAL_NAME] = owner_repo(ind['repo_url'])
        for b in pr.brought_sources(ind.get('path'), warn=False):
            if owner_repo(b.get('repo')):
                hints[b['name']] = owner_repo(b['repo'])
    base = os.environ.get('PRECEDENT_SOURCE_BASE_URL', '')
    m = re.search(r'github\.com[/:]([^/]+)', base)
    if m:
        hints.setdefault('*', m.group(1))
    return hints


def unloaded_sources(root=ROOT):
    """-> [(name, attach)] for every shared or individual practice source
    this repository declares, or its person brings, that is not on disk to
    read (no practices/ directory). `attach` is the add_repo call that fixes
    it, or '' where the owner is not known here.

    Why at pre-push (2026-10-16): a set that fails to clone at session start
    reads, to everything downstream, the same as a set nobody declared --
    its hooks are not listed, its tools are not there -- so a pre-push hook
    it ships would be skipped without a word, which is how harness-named
    branches reached origin while the rule against them was in force. A
    person with no user config declares no individual set, and nothing is
    said for one."""
    try:
        sys.path.insert(0, str(HERE))
        import precedent_resolve as pr
        rows = pr.declared_source_paths(root)
        hints = _attach_hints(root)
    except Exception as exc:                                 # noqa: BLE001
        print(f'precedent_hooks: the practice sources here could not be read '
              f'({exc}); whether each loaded is not known', file=sys.stderr)
        return []
    out = []
    for path, level, name, _note in rows:
        if pr.normalize_level(level) not in pr.PRIVATE_LEVELS or not path:
            continue
        if (Path(path) / 'practices').is_dir():
            continue
        where = hints.get(name) or (f"{hints['*']}/{name}" if '*' in hints else '')
        out.append((name, where))
    return out


def run_git_hook(event, git_args, payload, root=ROOT):
    """-> exit status for git: 0 lets it through, 1 refuses. Runs every
    practice hook listed for `event`, in turn, with git's arguments and
    stdin; refuses first, without running any, while a source that would
    list one did not load (unloaded_sources)."""
    missing = unloaded_sources(root)
    if missing:
        lines = [f'  {name}: ' + (f'add_repo {where} (read access)'
                                  if where else 'attach it with add_repo')
                 + ', clone it where python3 tools/precedent_session_check.py '
                 'says, then push again'
                 for name, where in missing]
        print('push refused: a practice source in force here did not load, so '
              'the pre-push checks it ships could not run:\n' + '\n'.join(lines),
              file=sys.stderr)
        return 1
    env = dict(os.environ)
    env['CLAUDE_PROJECT_DIR'] = str(root)
    for label, argv, timeout in entries_for(event, '', root=root):
        if argv[:2] == ['bash', '-c']:
            argv = ['bash', '-c', argv[2] + ' "$@"', event, *git_args]
        label, rc, out, err, timed_out = _run(label, argv, timeout, payload, env)
        for text in (out, err):
            if text and text.strip():
                sys.stderr.write(text if text.endswith('\n') else text + '\n')
        if rc != 0 or timed_out:
            return 1
    return 0


def main(argv):
    if not argv:
        print('usage: precedent_hooks.py <hook event> | --git <git hook> [args]',
              file=sys.stderr)
        return 0
    if argv[0] == '--git':
        if len(argv) < 2 or argv[1] not in GIT_EVENTS:
            return 0
        return run_git_hook(argv[1], argv[2:], sys.stdin.read())
    event = argv[0]
    payload = sys.stdin.read()
    try:
        tool_name = str((json.loads(payload or '{}') or {}).get('tool_name') or '')
    except ValueError:
        tool_name = ''
    todo = entries_for(event, tool_name)
    if not todo:
        return 0
    env = dict(os.environ)
    env.setdefault('CLAUDE_PROJECT_DIR', str(ROOT))
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(todo)) as pool:
        results = list(pool.map(lambda t: _run(*t, payload, env), todo))
    rc, out, err = combine(event, results)
    if err:
        sys.stderr.write(err)
    if out:
        print(out)
    return rc


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
