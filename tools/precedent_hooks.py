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


def entries_for(event, tool_name, root=ROOT, engine=None, practice=None):
    """-> [(label, argv, timeout)] the hooks to run for this event and tool."""
    engine = _load(root / 'tools' / 'hook_wiring.json') if engine is None else engine
    practice = _load(root / 'process' / 'practice_hooks.json') if practice is None else practice
    kind = repo_kind(root)
    skip = declined(root)
    out = []
    rows = []
    if isinstance(engine, dict) and kind:
        rows += [dict(r, _engine=True) for r in (engine.get(kind) or [])
                 if isinstance(r, dict)]
    if isinstance(practice, dict):
        rows += [r for r in (practice.get('hooks') or []) if isinstance(r, dict)]
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
            if not command:
                continue
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


def main(argv):
    if not argv:
        print('usage: precedent_hooks.py <hook event>', file=sys.stderr)
        return 0
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
