#!/usr/bin/env python3
"""At a merge: when the vendored engine or catalogue is behind, runs Update Vendors from the BestPractice clone and commits the result on its own, or takes it all back and says why; never blocks the merge

precedent_merge_vendors.py -- a merge takes the vendor update with it.

Run from a consuming repository at a merge, after the base branch has been
merged in and committed and before the result is pushed:

    python3 tools/precedent_merge_vendors.py

It asks precedent_engine_freshness.py whether the vendored engine or a
vendored catalogue is behind its upstream. Nothing behind: it says so and
stops, in about the time a fetch takes. Something behind: it runs Update
Vendors (the source clone's tools/precedent_update.py, which carries its
own check) and then does one of two things, never a third:

  DONE      the update is committed as a commit of its own, so it can be
            read, reverted or cherry-picked apart from the work it rode in
            with, and the merge pushes it.
  NOT TAKEN the update left something for a person to decide, or its check
            is red, or it could not run. Everything it wrote is taken back
            -- only what it wrote; a run that would touch anything else is
            refused before it starts -- and the reason is printed. The
            merge goes ahead without it.

Then, whether or not anything was behind, it asks the repository's own
precedent_sync_views.py whether a moved practice source left the views
stale, and if so refreshes them as one more commit of their own (VIEWS:
refreshed), or takes the refresh back and says why (VIEWS: ... NOT
REFRESHED) -- refresh_views says when.

It never blocks a merge: the exit status is 0 in every one of those
outcomes, and 2 only for a call it could not make sense of. Whatever it
printed belongs in the reply, because "not taken" is a question waiting for
the person.

WHY (2026-10-02, Alex: "Can we set up a system so merge also does vendor
updates?"). The freshness notice already printed at every merge gate --
"ENGINE BEHIND UPSTREAM ... To take it: Update Vendors" -- and a notice is
what had already failed: on 2026-09-20 18 of 22 repositories had never taken
an update, and the ones that did took it in one painful batch. A merge is
the moment a branch is being checked and pushed anyway, so the update rides
there, small and often.

Preconditions, each refused with its reason rather than worked around:
no merge in progress (commit it first), and no tracked file changed but
uncommitted (the update's output must be the only thing in its commit, and
the only thing taken back). Untracked files are left alone, as Update
Vendors always leaves them.

Run:
  python3 tools/precedent_merge_vendors.py              # at a merge
  python3 tools/precedent_merge_vendors.py --check-only # only say whether it would
  python3 tools/precedent_merge_vendors.py --always     # update without asking freshness
  python3 tools/precedent_merge_vendors.py --source DIR # the BestPractice clone to run
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
STAGED_RECORD = 'precedent-update-staged.json'   # precedent_update.py's
DONE, LEFT, FAILED = 0, 1, 2                     # precedent_update.py's exits


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          text=True)


def vendors_behind(repo):
    """-> (behind lines, could-not-verify lines) from the freshness check.
    Only what Update Vendors moves counts: the vendored engine and a
    vendored catalogue. A live clone behind its own origin is a pull, not
    an update."""
    sys.path.insert(0, str(HERE))
    try:
        import precedent_engine_freshness as fr
    finally:
        sys.path.pop(0)
    behind, unknown, tips = [], [], {}
    for row in fr.collect_targets(repo):
        if row.get('kind') not in ('engine', 'vendored'):
            continue
        if row.get('problem'):
            if not row.get('nothing_vendored'):
                unknown.append(f"{row['label']}: {row['problem']}")
            continue
        key = (row['url'], row['branch'])
        if key not in tips:
            tips[key] = fr.upstream_tip(*key)
        tip = tips[key]
        if tip is None:
            unknown.append(f"{row['label']}: could not reach {row['url']}")
        elif tip != row['recorded']:
            behind.append(f"{row['label']} has {row['recorded'][:12]}; "
                          f"{row['branch']} is at {tip[:12]}")
    return behind, unknown


def find_source(repo, given=None):
    """-> the BestPractice clone whose precedent_update.py to run, or None.
    `--source`, then PRECEDENT_SOURCE_CLONE, then the universal source
    precedent.json declares by path, then a BestPractice clone beside the
    repo. The update refuses to run from a vendored copy, so the clone is
    the only place it can come from."""
    cands = []
    if given:
        cands.append(pathlib.Path(given))
    if os.environ.get('PRECEDENT_SOURCE_CLONE'):
        cands.append(pathlib.Path(os.environ['PRECEDENT_SOURCE_CLONE']))
    try:
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cfg = {}
    for src in cfg.get('sources') or []:
        if src.get('level') == 'universal' and src.get('path'):
            p = pathlib.Path(src['path'])
            cands.append(p if p.is_absolute() else repo / p)
    cands.append(repo.parent / 'BestPractice')
    for c in cands:
        c = c.resolve()
        if c != repo and (c / 'tools' / 'precedent_update.py').is_file() \
                and (c / '.git').exists():
            return c
    return None


def preconditions(repo):
    """-> why it may not run here, or None."""
    gitdir = _git(repo, 'rev-parse', '--absolute-git-dir').stdout.strip()
    if not gitdir:
        return 'not a git checkout'
    if (pathlib.Path(gitdir) / 'MERGE_HEAD').exists():
        return ('a merge is in progress -- commit it first, so the update '
                'is a commit of its own after it')
    dirty = [l[3:] for l in _git(repo, 'status', '--porcelain=v1',
                                 '--untracked-files=no').stdout.splitlines() if l]
    if dirty:
        return (f'{len(dirty)} tracked file(s) changed and not committed '
                f'({", ".join(dirty[:5])}{" ..." if len(dirty) > 5 else ""}) -- '
                f'commit them first, so the update is the only thing in its '
                f'commit and the only thing taken back if it is not taken')
    if _git(repo, 'rev-parse', '--verify', '--quiet', 'HEAD').returncode != 0:
        return 'the branch has no commit yet'
    return None


def take_back(repo):
    """Undo what an Update Vendors run left in a tree that was clean of
    tracked changes when it began: every path it staged goes back to HEAD,
    and a path it added goes. Untracked files nobody staged are left. Its
    record of a failed run goes too, since nothing it recorded is there."""
    names = _git(repo, 'diff', '--cached', '--name-only', '--no-renames', '-z').stdout
    names = [n for n in names.split('\0') if n]
    unstaged = _git(repo, 'diff', '--name-only', '--no-renames', '-z').stdout
    names += [n for n in unstaged.split('\0') if n and n not in names]
    for i in range(0, len(names), 200):
        batch = names[i:i + 200]
        _git(repo, 'reset', '-q', 'HEAD', '--', *batch)
    for n in names:
        if _git(repo, 'cat-file', '-e', f'HEAD:{n}').returncode == 0:
            _git(repo, 'checkout', '-q', 'HEAD', '--', n)
        else:
            f = repo / n
            if f.is_file() or f.is_symlink():
                f.unlink()
    gitdir = _git(repo, 'rev-parse', '--absolute-git-dir').stdout.strip()
    rec = pathlib.Path(gitdir) / STAGED_RECORD if gitdir else None
    if rec and rec.is_file():
        rec.unlink()
    return names


def _summary(out):
    """The update's own closing report, from its `== Update Vendors ==`
    banner on: what each step did and what it left."""
    i = out.rfind('== Update Vendors ==')
    return out[i:].strip() if i >= 0 else out.strip()[-3000:]


def commit_update(repo, source, out):
    head = _git(source, 'rev-parse', '--short=12', 'HEAD').stdout.strip()
    try:
        manifest = json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json')
                              .read_text(encoding='utf-8'))
        landed = (manifest.get('source_commit') or '')[:12]
        branch = manifest.get('source_branch') or 'main'
    except (OSError, ValueError):
        landed, branch = head, 'main'
    msg = (f'Update Vendors at merge: BestPractice {branch} @ {landed}\n\n'
           f'Taken by tools/precedent_merge_vendors.py, as a commit of its own '
           f'so it can be read or reverted apart from the merge.\n\n'
           + '\n'.join(l for l in _summary(out).splitlines()
                       if l.startswith('  ') and ': ' in l)[:4000] + '\n')
    sid = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID', '').strip()
    if sid:
        sid = sid if sid.startswith('session_') else f'session_{sid}'
        msg += f'\nSession: https://claude.ai/code/{sid}\n'
    before = _git(repo, 'rev-parse', 'HEAD').stdout.strip()
    r = subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-F', '-'],
                       input=msg, capture_output=True, text=True)
    after = _git(repo, 'rev-parse', 'HEAD').stdout.strip()
    if r.returncode != 0 or after == before:
        return None, (r.stdout + r.stderr).strip()[-800:]
    return after, ''


VIEWS_TOOL = 'tools/precedent_sync_views.py'
# The person's words letting a commit change .claude/ (hooks, settings):
# Claude Code's auto mode holds such a commit as self-modification, so
# without them nothing here writes one -- it says so instead.
HARNESS_GO_AHEAD = 'PRECEDENT_HARNESS_GO_AHEAD'


def _untracked(repo):
    out = _git(repo, 'ls-files', '--others', '--exclude-standard', '-z').stdout
    return {n for n in out.split('\0') if n}


def refresh_views(repo):
    """Regenerate views a moved practice source left stale, as a commit of
    their own -- the views' half of what a merge takes along. Prints one
    VIEWS: line; never blocks the merge.

    WHY (2026-10-06). A source this repository declares moved, its
    generated views went stale, and every push was refused for it -- a
    one-line content push to a feature branch included. The push check now
    reports a staleness the push did not bring, and this is where the
    refresh it points at happens: at the merge, the way the vendor update
    rides along, so pre-staging and above stay fresh."""
    tool = repo / VIEWS_TOOL
    if not tool.is_file():
        return
    probe = subprocess.run([sys.executable, str(tool), '--repo', '.', '--check',
                            '--skip-unresolved'], cwd=str(repo),
                           capture_output=True, text=True)
    if probe.returncode == 0:
        return
    why = preconditions(repo)
    if why:
        print(f'VIEWS: stale, NOT REFRESHED -- {why}.')
        return
    before = _untracked(repo)
    r = subprocess.run([sys.executable, str(tool), '--repo', '.'], cwd=str(repo),
                       capture_output=True, text=True)
    new = sorted(_untracked(repo) - before)
    if new:
        _git(repo, 'add', '--', *new)
    _git(repo, 'add', '-u')
    staged = [n for n in _git(repo, 'diff', '--cached', '--name-only').stdout
              .splitlines() if n]
    if r.returncode != 0:
        take_back(repo)
        print('VIEWS: stale, NOT REFRESHED -- the sync failed, and what it '
              'wrote was taken back:')
        print('\n'.join('  ' + l for l in (r.stdout + r.stderr)
                        .strip().splitlines()[-12:]))
        return
    if not staged:
        return
    harness = [n for n in staged if n.startswith('.claude/')]
    words = os.environ.get(HARNESS_GO_AHEAD, '').strip()
    if harness and not words:
        take_back(repo)
        print(f'VIEWS: stale, NOT REFRESHED -- the refresh changes '
              f'{", ".join(harness)}, and Claude Code\'s auto mode holds a '
              f'commit that changes hooks or settings until the person says '
              f'yes. Nothing was committed. Ask the person, naming those '
              f'files; with their yes, run again with '
              f'{HARNESS_GO_AHEAD}="<their words>".')
        return
    msg = ('Views refreshed at merge: a declared practice source moved\n\n'
           'Taken by tools/precedent_merge_vendors.py, as a commit of its own '
           'so it can be read or reverted apart from the merge.\n\n'
           + '\n'.join(f'  {n}' for n in staged[:60]) + '\n'
           + (f'\nHooks and settings changed with the person\'s go-ahead: '
              f'"{words}"\n' if harness else ''))
    c = subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-F', '-'],
                       input=msg, capture_output=True, text=True)
    if c.returncode != 0:
        take_back(repo)
        print(f'VIEWS: stale, NOT REFRESHED -- the commit was refused, so the '
              f'refresh was taken back:\n{(c.stdout + c.stderr).strip()[-600:]}')
        return
    sha = _git(repo, 'rev-parse', '--short=12', 'HEAD').stdout.strip()
    print(f'VIEWS: refreshed, in commit {sha} of its own ({len(staged)} '
          f'file(s)). Push it with the merge.')


def run(repo, source=None, check_only=False, always=False, extra=()):
    """-> exit status, printing one VENDORS: line first and the detail
    after it."""
    repo = pathlib.Path(repo).resolve()
    if not (repo / 'tools' / 'ENGINE_MANIFEST.json').is_file():
        print('VENDORS: nothing vendored here (no tools/ENGINE_MANIFEST.json), '
              'so there is nothing to update.')
        return 0
    if not always:
        behind, unknown = vendors_behind(repo)
        if not behind:
            if unknown:
                print('VENDORS: NOT VERIFIED -- could not tell whether anything '
                      'is behind, so nothing was updated:')
                for line in unknown:
                    print(f'  {line}')
            else:
                print('VENDORS: current -- nothing to update.')
            if not check_only:
                refresh_views(repo)
            return 0
        print('VENDORS: behind upstream:')
        for line in behind:
            print(f'  {line}')
    if check_only:
        print('VENDORS: --check-only, so nothing was run.')
        return 0
    why = preconditions(repo)
    if why:
        print(f'VENDORS: NOT TAKEN -- {why}. Nothing was run.')
        return 0
    clone = find_source(repo, source)
    if clone is None:
        print('VENDORS: NOT TAKEN -- no BestPractice clone found to run Update '
              'Vendors from (--source DIR, PRECEDENT_SOURCE_CLONE, a universal '
              'source declared by path in precedent.json, or ../BestPractice). '
              'Nothing was run.')
        return 0
    print(f'VENDORS: updating from {clone} -- Update Vendors, with its own '
          f'check; this takes minutes, not seconds.', flush=True)
    r = subprocess.run([sys.executable, str(clone / 'tools' / 'precedent_update.py'),
                        '--repo', str(repo), *extra],
                       cwd=str(repo), capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode == DONE:
        sha, err = commit_update(repo, clone, out)
        if sha:
            print(f'VENDORS: updated, in commit {sha[:12]} of its own. Push it '
                  f'with the merge.')
            print(_summary(out))
            return 0
        taken = take_back(repo)
        print(f'VENDORS: NOT TAKEN -- the update finished but its commit was '
              f'refused, so its {len(taken)} path(s) were taken back:\n{err}')
        return 0
    taken = take_back(repo)
    what = ('it left calls for the person' if r.returncode == LEFT else
            'its check is red, or a step could not run')
    print(f'VENDORS: NOT TAKEN -- {what}. Its {len(taken)} written path(s) '
          f'were taken back and the merge goes ahead without it. To take it: '
          f'"Update Vendors" on its own, working what it lists below.')
    print(_summary(out))
    refresh_views(repo)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--repo', default='.', help='the consuming repo (default: .)')
    ap.add_argument('--source', default=None, help='the BestPractice clone to run')
    ap.add_argument('--check-only', action='store_true',
                    help='say whether anything is behind, and stop')
    ap.add_argument('--always', action='store_true',
                    help='run the update without asking the freshness check')
    ap.add_argument('--from-ref', default=None,
                    help='passed to precedent_update.py: vendor this commit')
    ap.add_argument('--skip-check', action='store_true',
                    help="passed to precedent_update.py: leave out its check "
                         "(the push gate still runs one)")
    a = ap.parse_args(argv)
    extra = (['--from-ref', a.from_ref] if a.from_ref else []) + \
        (['--skip-check'] if a.skip_check else [])
    return run(a.repo, a.source, a.check_only, a.always, extra)


if __name__ == '__main__':
    sys.exit(main())
