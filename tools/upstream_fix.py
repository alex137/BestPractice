#!/usr/bin/env python3
"""Sets up the fix to a vendored file where it comes from -- names the source repository and the file's path there, and opens a branch in that source's clone off its landing branch; never edits the copy

Set up the fix to a vendored file in the repository it comes from.

code-cites-practice: todo-is-a-handoff

    python3 tools/upstream_fix.py tools/doc_lint.py
    python3 tools/upstream_fix.py process/upstream/practices/some-rule.md
    python3 tools/upstream_fix.py --self-check

WHY THIS EXISTS (2026-10-06). Sessions that hit a bug in a file this repo
copies from somewhere else kept filing an open item -- "blocked on push
access to X", "needs a change in the engine" -- instead of fixing it
upstream in the same turn. In one consumer four such items sat for one to
two weeks, each an hour's fix. The work that made it feel blocked was
finding out where the file comes from and getting a branch to fix it on.
This does both in one command, so the open item it replaces is a pull
request instead (practice: todo-is-a-handoff; doc_lint.py refuses an open
item about an upstream fix that links no pull request, and names this).

WHAT IT DOES:
  1. says which source PATH came from: the repository, its path there, the
     branch it was vendored from, and the local clone if one exists (the
     source's declared path when that is a clone outside this repo, else a
     clone named after the repository beside this one);
  2. when that clone exists and is clean, fetches its landing branch and
     creates a branch there off it -- named by the clone's own
     tools/precedent_branch_name.py when it has one, else
     fix/<file-stem>-<date>;
  3. prints the file to edit and the next steps.

It never edits the vendored copy here: the next Update Vendors replaces it,
and the fix belongs upstream (practice: upstream-fix). It never pushes.
What counts as vendored is precedent_engine_freshness.vendored_entries(),
the same answer doc_lint.py's check reads.

Exit status: 0 the branch is ready (or --no-branch said where), 1 PATH is
not vendored here, 3 the source is known but no branch could be made (no
clone, a dirty clone, a fetch that failed) -- the output says which.
"""
import argparse
import datetime
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_engine_freshness as pef  # noqa: E402


def _run(args, cwd, env=None):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           timeout=120, env=env)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def landing_branch(clone, recorded):
    """The clone's own answer when it carries precedent_branches.py, else the
    branch this repo vendored from, else the clone's origin HEAD."""
    tool = clone / 'tools' / 'precedent_branches.py'
    if tool.is_file():
        rc, out = _run([sys.executable, str(tool), '--landing'], clone)
        if rc == 0 and out.split():
            return out.split()[0]
    if recorded:
        return recorded
    rc, ref = _run(['git', 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD'], clone)
    return ref.split('/', 1)[1] if rc == 0 and '/' in ref else 'main'


def _today():
    """The person's date, never the container's (practice:
    timestamps-carry-offset)."""
    try:
        import precedent_time
        return precedent_time.today()
    except Exception:                                        # noqa: BLE001
        return datetime.datetime.now().astimezone().date().isoformat()


def branch_name(clone, upstream_path):
    stem = pathlib.PurePosixPath(upstream_path or 'fix').stem or 'fix'
    tool = clone / 'tools' / 'precedent_branch_name.py'
    if tool.is_file():
        rc, out = _run([sys.executable, str(tool), 'fix', stem], clone)
        lines = [ln for ln in out.splitlines() if ln.strip() and ' ' not in ln.strip()]
        if rc == 0 and lines:
            return lines[-1].strip()
    return f'fix/{stem}-{_today()}'


def fix(root, path, make_branch=True, out=sys.stdout):
    root = pathlib.Path(root).resolve()
    rel = pathlib.Path(path)
    if rel.is_absolute():
        try:
            rel = rel.resolve().relative_to(root)
        except ValueError:
            print(f'{path} is not inside {root}.', file=out)
            return 1
    e = pef.origin_of(root, rel.as_posix())
    if e is None:
        print(f'{rel.as_posix()} is not vendored here: it is this repo\'s own '
              f'file, so fix it here.', file=out)
        return 1
    repo = e.get('repo') or '(no repository recorded)'
    print(f"{e['local']} is a copy, from {e['source']}:", file=out)
    print(f'  repository   {repo}', file=out)
    print(f"  path there   {e['upstream'] or '(the repository root)'}", file=out)
    if e.get('branch'):
        print(f"  vendored from branch {e['branch']}", file=out)
    clone = e.get('clone')
    if clone is None:
        name = pef._repo_basename(e.get('repo')) or e['source']
        print(f'\nNo clone of it beside this repo. Attach it with push access '
              f'(add_repo, or ask for access if it is refused) and clone it to '
              f'{root.parent / name}, then run this again.', file=out)
        return 3
    print(f'  local clone  {clone}', file=out)
    target = clone / e['upstream'] if e['upstream'] else clone
    land = landing_branch(clone, e.get('branch'))
    if not make_branch:
        print(f'\n--no-branch: edit {target} on a branch off {land} there.', file=out)
        return 0
    rc, dirty = _run(['git', 'status', '--porcelain'], clone)
    if rc != 0 or dirty:
        print(f'\n{clone} has uncommitted changes, so no branch was made '
              f'there. Commit or set them aside, then run this again.', file=out)
        return 3
    rc, msg = _run(['git', 'fetch', '--quiet', 'origin', land], clone)
    if rc != 0:
        print(f'\nCould not fetch {land} in {clone}: {msg[-300:]}', file=out)
        return 3
    name = branch_name(clone, e['upstream'])
    rc, msg = _run(['git', 'switch', '--quiet', '--no-track', '-c', name,
                    f'origin/{land}'], clone)
    if rc != 0:
        print(f'\nCould not create {name} in {clone}: {msg[-300:]}', file=out)
        return 3
    print(f'\nBranch {name} is checked out in {clone}, off origin/{land}.', file=out)
    print(f'\nNext:\n'
          f'  1. edit {target} (never the copy here)\n'
          f'  2. run that repository\'s own checks\n'
          f'  3. push {name} and open a pull request into {land}\n'
          f'  4. link the pull request in the open item, which waits only on '
          f'its review\n'
          f'  5. once it lands, take it here with Update Vendors', file=out)
    return 0


def self_check():
    """A planted source repo, its clone beside a consumer, and a consumer that
    vendors one file from it: the branch is made in the clone, off the
    landing branch, and the copy is untouched; a file of the consumer's own
    is refused; a dirty clone is refused."""
    import io
    import json
    import os
    import tempfile
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
               GIT_CONFIG_GLOBAL=os.devnull)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        bare = td / 'remote' / 'Engine.git'
        work = td / 'seed'
        _run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)], td, env)
        _run(['git', 'init', '-q', '-b', 'main', str(work)], td, env)
        (work / 'tools').mkdir()
        (work / 'tools' / 'thing.py').write_text('upstream\n')
        _run(['git', 'add', '.'], work, env)
        _run(['git', 'commit', '-qm', 'seed'], work, env)
        _run(['git', 'push', '-q', str(bare), 'main'], work, env)
        clone = td / 'Engine'
        _run(['git', 'clone', '-q', str(bare), str(clone)], td, env)
        consumer = td / 'consumer'
        (consumer / 'tools').mkdir(parents=True)
        (consumer / 'tools' / 'thing.py').write_text('copy\n')
        (consumer / 'own.md').write_text('mine\n')
        (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'source_repo': str(bare), 'source_branch': 'main',
             'source_commit': 'x', 'files': ['thing.py']}))
        buf = io.StringIO()
        rc = fix(consumer, 'tools/thing.py', out=buf)
        _, head = _run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], clone)
        _, base = _run(['git', 'merge-base', 'HEAD', 'origin/main'], clone)
        _, tip = _run(['git', 'rev-parse', 'origin/main'], clone)
        cases.append(('a vendored file gets a branch in its source clone, off '
                      'the landing branch',
                      rc == 0 and head.startswith('fix/thing-') and base == tip
                      and str(clone / 'tools' / 'thing.py') in buf.getvalue()))
        cases.append(('the vendored copy is never edited',
                      (consumer / 'tools' / 'thing.py').read_text() == 'copy\n'))
        cases.append(("a file of the repo's own is refused",
                      fix(consumer, 'own.md', out=io.StringIO()) == 1))
        (clone / 'tools' / 'thing.py').write_text('half-done\n')
        cases.append(('a dirty clone gets no branch',
                      fix(consumer, 'tools/thing.py', out=io.StringIO()) == 3))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print(f"  {'ok  ' if ok else 'FAIL'} {n}")
    print(f"upstream_fix self-check: {len(cases) - len(bad)}/{len(cases)} passed")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('path', nargs='?', help='a path in this repo that is a vendored copy')
    ap.add_argument('--repo', default='.', help='this repo\'s root (default: .)')
    ap.add_argument('--no-branch', action='store_true',
                    help='say where the fix goes, make no branch')
    ap.add_argument('--self-check', action='store_true',
                    help='run the planted-fixture test and exit')
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if not a.path:
        ap.error('give the vendored path to fix')
    return fix(a.repo, a.path, make_branch=not a.no_branch)


if __name__ == '__main__':
    sys.exit(main())
