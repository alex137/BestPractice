#!/usr/bin/env python3
"""Did this session's SessionStart hooks actually run? -- and repair it.

practice: session-bootstrap, fail-gracefully

THE INCIDENT, 2026-09-08. A session opened with four Precedent repositories
side by side under a parent directory -- this project's own required layout,
since a team source resolves as a SIBLING CLONE -- and the harness rooted the
session at that PARENT. `$CLAUDE_PROJECT_DIR` was therefore `/home/user`,
which has no `.claude/` of its own, so every hook in every one of the four
repositories' `settings.json` pointed at a path that does not exist. None of
them ran. Silently: a hook that cannot be found is not an error anybody sees.

What was missing, all at once, for a session doing a full review before the
work was shown to its reviewer: the commit identity (so commits would have
been authored by the container's bot and refused by this repo's own check),
the global commit backstop, the freshness guard, the package installs, the
path-trigger channel, the Stop-time git check, and
`.precedent/SESSION_PRACTICES.md` -- which is the ONLY route by which the
team and individual practices in force reach a session at all. AGENTS.md's
Standing Instruction tells every session to read that file; there was no file.

WHY THE EXISTING GOTCHA DID NOT COVER IT. AGENTS.md already records that a
repo ATTACHED mid-session never runs its own SessionStart hook. This is the
sibling failure and reads as its opposite: the repository is the one the
session is working in, its hooks are correctly wired, committed and
executable, and they still never fire -- because the session's root is one
directory ABOVE the repository. The multi-repo layout that causes it is not
exotic, it is what Precedent's own source resolution requires.

WHY THIS IS A TOOL AND NOT A HOOK. It cannot be a hook. The failure IS that
hooks do not run, so anything that waits to be triggered is the one thing
guaranteed not to fire (the same shape AGENTS.md records for a freshness
guard shipped inside the checkout it guards). It is reachable two ways
instead: AGENTS.md names it in the first-tool-call banner a session reads
before anything else, and `--apply` makes the repair one command rather than
three remembered ones.

Exit 0 when every guarantee holds, 1 otherwise, so it can gate a run.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOT_EMAILS = {'noreply@anthropic.com'}


def _run(*args, cwd=None):
    p = subprocess.run(args, capture_output=True, text=True,
                       cwd=str(cwd or ROOT))
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _git(*args):
    return _run('git', '-C', str(ROOT), *args)


def _declared_branch():
    try:
        cfg = json.loads((ROOT / 'precedent.json').read_text())
        return cfg.get('base_branch')
    except Exception:
        return None


def checks():
    """-> [(name, ok, detail)]. Each is a guarantee a SessionStart hook is
    supposed to have established, tested by its EFFECT rather than by
    whether some hook reported success -- a hook that never ran reports
    nothing at all, which is exactly the state being detected
    (practice: verify-postcondition)."""
    out = []

    # 1. The project dir the harness actually handed the hooks.
    proj = os.environ.get('CLAUDE_PROJECT_DIR')
    if proj is None:
        detail = ('CLAUDE_PROJECT_DIR is not set in this shell, so this '
                  'cannot be read directly -- the checks below test the '
                  'effects instead, which is the reliable signal either way')
        out.append(('the harness rooted the session at this repository',
                    None, detail))
    else:
        ok = pathlib.Path(proj).resolve() == ROOT
        detail = '' if ok else (
            f'CLAUDE_PROJECT_DIR={proj!r}, but this repository is {ROOT}. '
            f'Every hook in .claude/settings.json is written as '
            f'$CLAUDE_PROJECT_DIR/.claude/hooks/... so NONE of them resolve, '
            f'and none of them ran. This is the incident in the docstring')
        out.append(('the harness rooted the session at this repository',
                    ok, detail))

    # 2. The practices in force from private sources reached the session.
    sp = ROOT / '.precedent' / 'SESSION_PRACTICES.md'
    ok = sp.is_file()
    out.append(('the team and individual practices in force were written to '
                '.precedent/SESSION_PRACTICES.md', ok,
                '' if ok else
                'the file does not exist, so every team and individual '
                'practice binding work here is SILENTLY absent -- AGENTS.md '
                "tells this session to read it and there is nothing to read. "
                'Regenerate: python3 tools/precedent_session_practices.py'))

    # 2b. ...and if they did not, whether a credential could have helped.
    # The row above says the FILE is missing; this one says whether the
    # sources themselves resolved, which is the thing that actually binds
    # work here. Both matter: the file can exist and honestly report that
    # every private source was unreachable, which is the state a whole
    # working day was once lost to (AGENTS.md's "no individual source
    # resolved" gotcha).
    try:
        import precedent_source_credentials as psc
        verdict, message = psc.assess(ROOT)
        out.append(('the private practice sources resolved, or a credential '
                    'is set that could reach them', verdict != 'missing',
                    '' if verdict != 'missing' else message))
    except ImportError:
        out.append(('the private practice sources resolved, or a credential '
                    'is set that could reach them', None,
                    'tools/precedent_source_credentials.py is not importable '
                    'from here, so this could not be evaluated'))

    # 3. Commit identity is a person, not the container's bot.
    _, email, _ = _git('config', 'user.email')
    ok = bool(email) and email not in BOT_EMAILS
    out.append(('commits from this checkout are authored by a person', ok,
                '' if ok else
                f'user.email is {email!r}, the container\'s own agent '
                f'account. Commits made now are wrong-author commits, and '
                f'this repo\'s own check refuses them'))

    # 4. The global backstop reaches repositories attached later.
    _, hp, _ = _run('git', 'config', '--global', 'core.hooksPath')
    ok = bool(hp) and pathlib.Path(hp).is_dir()
    out.append(('the global commit backstop is installed', ok,
                '' if ok else
                'core.hooksPath is unset, so a repository attached LATER in '
                'this session inherits the container identity with nothing '
                'to refuse it'))

    # 5. The packages this repo's own gates import.
    missing = []
    for mod in ('cmarkgfm', 'markdown'):
        if subprocess.run([sys.executable, '-c', f'import {mod}'],
                          capture_output=True).returncode != 0:
            missing.append(mod)
    out.append(('the packages the gates import are installed', not missing,
                '' if not missing else
                f'missing {", ".join(missing)} -- doc_lint\'s strikethrough '
                f'check and tools/doc_html.py degrade rather than fail, so '
                f'they pass while checking less than they claim'))

    # 6. A single-branch clone's refspec, without which every branch reads
    #    as unpushed forever (AGENTS.md's add_repo entry).
    _, spec, _ = _git('config', '--get-all', 'remote.origin.fetch')
    ok = 'refs/heads/*' in spec
    out.append(('this clone can see every branch on origin', ok,
                '' if ok else
                f'remote.origin.fetch is {spec!r} -- a single-branch clone, '
                f'so branch scans see two or three refs on a repo that has '
                f'forty and report the rest as absent'))

    # 7. The branch this session started on is still the one checked out.
    #
    #    THE INCIDENT, 2026-09-08. Mid-session, this checkout was moved off
    #    its working branch onto `precedent-beta-v01` and fast-forwarded --
    #    `checkout: moving from claude/... to precedent-beta-v01` followed by
    #    `pull origin precedent-beta-v01: Fast-forward`, three minutes after a
    #    commit. The commit survived on the abandoned branch; the next twenty
    #    minutes of edits were made on the wrong one, and the loss showed up
    #    only as a check that had silently stopped existing.
    #
    #    THE CAUSE IS NOT KNOWN, and this says so rather than implying it is
    #    fixed. `precedent_vendor_engine.py seed`, `precedent_refresh_sources
    #    --apply` and `checkin.py fresh` were each replayed against a
    #    throwaway clone on a feature branch and NONE of them moved HEAD, so
    #    the three obvious suspects are ruled out. Whatever did it is outside
    #    this repo's own tools. Detection is therefore the whole remedy
    #    available: a stamp written on the first run of a session, compared on
    #    every later one.
    stamp = ROOT / '.git' / 'precedent-session-branch'
    rc, cur, _ = _git('rev-parse', '--abbrev-ref', 'HEAD')
    if rc == 0 and cur:
        if stamp.is_file():
            started = stamp.read_text().strip()
            ok = (started == cur)
            out.append(('this session is still on the branch it started on',
                        ok,
                        '' if ok else
                        f'started on {started!r}, now on {cur!r}. Work '
                        f'committed before the move is on {started!r} and is '
                        f'NOT lost -- `git checkout {started}` and check '
                        f'`git reflog` for anything after it. Work done SINCE '
                        f'the move is on the wrong branch'))
        else:
            try:
                stamp.write_text(cur + '\n')
            except OSError:
                pass
            out.append(('this session is still on the branch it started on',
                        None, f'first run this session -- recorded {cur!r} as '
                              f'the baseline to compare against later'))

    # 8. Freshness. Reported, never repaired here: discarding work is worse
    #    than a stale tree, so this only ever tells (practice: fail-gracefully).
    branch = _declared_branch()
    rc, cur, _ = _git('rev-parse', '--abbrev-ref', 'HEAD')
    if branch and rc == 0:
        _git('fetch', '--quiet', 'origin', branch)
        rc2, behind, _ = _git('rev-list', '--count', f'HEAD..origin/{branch}')
        if rc2 == 0 and behind.isdigit():
            ok = int(behind) == 0
            out.append((f'this checkout is not behind origin/{branch}', ok,
                        '' if ok else
                        f'{behind} commit(s) behind on branch {cur!r}. Work '
                        f'that landed reads as missing and fixed bugs read '
                        f'as open'))
        else:
            out.append((f'this checkout is not behind origin/{branch}', None,
                        'could not compare -- origin/'
                        f'{branch} did not resolve'))
    return out


def apply_repair():
    """Run the three SessionStart hooks by hand, in settings.json's order."""
    branch = _declared_branch() or 'main'
    hooks = [
        ('session-start.sh', []),
        ('freshness-guard.sh', ['session-start', branch]),
        ('commit-identity.sh', []),
    ]
    failed = []
    for name, args in hooks:
        path = ROOT / '.claude' / 'hooks' / name
        if not path.is_file():
            print(f'  SKIP {name} -- not present in this checkout')
            continue
        print(f'  running {name} {" ".join(args)}')
        p = subprocess.run(['bash', str(path), *args], cwd=str(ROOT))
        if p.returncode != 0:
            failed.append(name)
    # Never silent: a repair that half-worked is the state this whole tool
    # exists to make visible.
    for name in failed:
        print(f'  WARN: {name} exited non-zero -- re-run it directly to see why')
    return not failed


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true',
                    help='run this repo\'s SessionStart hooks by hand, then '
                         're-check')
    args = ap.parse_args()

    if args.apply:
        print('applying the SessionStart hooks by hand:\n')
        apply_repair()
        print()

    rows = checks()
    bad = [r for r in rows if r[1] is False]
    unknown = [r for r in rows if r[1] is None]
    for name, ok, detail in rows:
        mark = 'OK  ' if ok else ('FAIL' if ok is False else '??  ')
        print(f'  {mark} {name}')
        if detail:
            print(f'       {detail}')
    print()
    if bad:
        print(f'session check: {len(bad)} guarantee(s) NOT in effect'
              + (f', {len(unknown)} undetermined' if unknown else '') + '.')
        if not args.apply:
            print('Repair: python3 tools/precedent_session_check.py --apply')
        return 1
    print(f'session check OK: {len(rows) - len(unknown)} guarantee(s) in '
          f'effect' + (f', {len(unknown)} undetermined' if unknown else '') + '.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
