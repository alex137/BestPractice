#!/usr/bin/env python3
"""Say whether this repo's VENDORED engine has fallen behind upstream.

THE GAP THIS CLOSES. Every check in this system runs inside one repository.
Nothing compared a consuming repo against the upstream it vendored from, so
a fix merged upstream reached an installed repo only when somebody
remembered to run "Update Vendors" there -- and nothing anywhere said which
repos had not. Measured 2026-09-20: 18 of 22 repositories had never taken
one. That is also why running a deep check could never find a stale vendored
tree; not a gap in its passes, a gap in what any pass could see.

A REMINDER IS WHAT ALREADY FAILED, so this is built to run without being
remembered: from the session-start hook, and from precedent_gate.py's push
and merge moments. It PRINTS and never refreshes anything -- the same shape
precedent_upstream_check.py has had since 2026-09-08, at Morgan's own
request: "I don't want it to merge invisibly, I'd like to do it in a session
when I'm there."

  python3 tools/precedent_engine_freshness.py           # the notice
  python3 tools/precedent_engine_freshness.py --files   # + what changed
  python3 tools/precedent_engine_freshness.py --quiet   # only if behind

EXIT STATUS IS 0 IN EVERY CASE, including no network, no manifest and a
malformed one. A session start that a network hiccup can block is worse than
the staleness it was guarding against (practice: fail-gracefully). `--files`
needs to fetch upstream objects and is therefore NOT what the hook runs.
"""
import argparse
import json
import pathlib
import subprocess
import sys

MANIFEST = pathlib.Path('tools') / 'ENGINE_MANIFEST.json'


def _git(*args, cwd=None, timeout=25):
    """-> (rc, stdout). Never raises: a missing git, a timeout and a failed
    fetch are all the same answer here, "could not look"."""
    try:
        p = subprocess.run(('git',) + args, cwd=cwd, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ''


def read_manifest(root):
    f = pathlib.Path(root) / MANIFEST
    if not f.is_file():
        return None, (f'no {MANIFEST} -- this repo has never vendored the '
                      f'engine, or is the engine\'s own origin')
    try:
        return json.loads(f.read_text(encoding='utf-8')), None
    except (OSError, ValueError) as e:
        return None, f'{MANIFEST} could not be read ({type(e).__name__})'


def upstream_tip(repo_url, branch):
    rc, out = _git('ls-remote', repo_url, f'refs/heads/{branch}')
    if rc != 0 or not out:
        return None
    return out.split()[0]


def changed_files(root, repo_url, recorded, tip, tracked):
    """-> (added, removed, changed) among the files this manifest tracks, or
    None when upstream objects could not be fetched. Deliberately separate
    from the notice: this costs a network fetch of real objects, and the
    notice must stay cheap enough to run at every session start."""
    rc, _ = _git('fetch', '--quiet', '--depth', '50', repo_url, tip, cwd=root)
    if rc != 0:
        rc, _ = _git('fetch', '--quiet', repo_url, tip, cwd=root)
        if rc != 0:
            return None
    rc, out = _git('diff', '--name-status', f'{recorded}..{tip}', cwd=root)
    if rc != 0:
        return None
    # NOT filtered to what this manifest ALREADY tracks, and that was the
    # first version's bug. A file upstream started shipping since this repo
    # vendored is not in this manifest yet -- so filtering by `tracked`
    # dropped exactly the case that matters most, "upstream now has
    # something you do not have". Caught by running it against a real repo
    # and noticing leak_gate.py and very_deep_check.py, both newly vendored
    # that same day, absent from the output.
    #
    # So: everything under tools/ and templates/github-actions/, whether or
    # not this repo has it. `tracked` is kept only to mark which lines this
    # repo is already carrying, since "changed under you" and "new to you"
    # read differently to somebody deciding whether to refresh.
    tracked = {f'tools/{n}' for n in tracked}
    added, removed, changed = [], [], []
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        status, path = parts[0][:1], parts[-1]
        if not (path.startswith('tools/')
                or path.startswith('templates/github-actions/')):
            continue
        mark = path if path in tracked else f'{path} (NOT YET VENDORED HERE)'
        (added if status == 'A' else removed if status == 'D'
         else changed).append(mark)
    return sorted(added), sorted(removed), sorted(changed)


def report(root='.', with_files=False, quiet=False, out=sys.stdout):
    manifest, why = read_manifest(root)
    if manifest is None:
        if not quiet:
            print(f'engine freshness: not checked -- {why}', file=out)
        return 0
    url = manifest.get('source_repo')
    branch = manifest.get('source_branch')
    recorded = manifest.get('source_commit')
    if not (url and branch and recorded):
        if not quiet:
            print('engine freshness: not checked -- the manifest does not '
                  'record source_repo, source_branch and source_commit',
                  file=out)
        return 0

    tip = upstream_tip(url, branch)
    if tip is None:
        if not quiet:
            print(f'engine freshness: NOT VERIFIED -- could not reach {url} '
                  f'({branch}). Whether this repo\'s vendored engine is '
                  f'current is unknown this session.', file=out)
        return 0
    if tip == recorded:
        if not quiet:
            print(f'engine freshness: current -- vendored engine matches '
                  f'{branch} at {recorded[:12]}', file=out)
        return 0

    print(f'ENGINE BEHIND UPSTREAM: this repo vendored {recorded[:12]}; '
          f'{url} {branch} is now at {tip[:12]}.', file=out)
    print('  Nothing has been changed -- this is a notice. To take it: '
          '"Update Vendors" (practices/vendor-update-runbook.md).', file=out)

    if with_files:
        result = changed_files(root, url, recorded, tip,
                               manifest.get('files') or [])
        if result is None:
            print('  (could not fetch upstream objects, so WHICH files moved '
                  'is unknown -- the commit difference above still stands)',
                  file=out)
        else:
            added, removed, changed = result
            for label, names in (('added upstream', added),
                                 ('REMOVED upstream', removed),
                                 ('changed upstream', changed)):
                if names:
                    print(f'  {label} ({len(names)}): {", ".join(names)}',
                          file=out)
            if not (added or removed or changed):
                print('  no tracked engine file or CI template changed '
                      'between those commits', file=out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--root', default='.')
    ap.add_argument('--files', action='store_true',
                    help='also name which tracked files moved (needs a fetch)')
    ap.add_argument('--quiet', action='store_true',
                    help='print only when this repo is actually behind')
    a = ap.parse_args(argv)
    return report(a.root, with_files=a.files, quiet=a.quiet)


if __name__ == '__main__':
    sys.exit(main())
