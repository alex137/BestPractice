#!/usr/bin/env python3
"""precedent_consumer_shape.py -- run a practice source's own check tests
the way a consuming repository will run them, so a test that only works in
its home layout fails at home, before it ships.

WHY. A source's tools/checks/tests/test_*.sh are materialized into every
repository that resolves the source, and they run there against THAT
repository's tree. Anything a test quietly assumes about its home -- above
all, which paths git ignores -- is an assumption about someone else's
repository once it ships. Measured 2026-09-25: a test planted a fixture at
vendor/THIRD_PARTY.md and ran a plain `git add` on it. In the source's own
repository nothing ignored vendor/, so it passed on every run there. In a
consuming repository whose .gitignore ignored vendor/ (a dependency
manager's directory), git refused the add and the test failed -- on every
run, for days, with each session there calling it "pre-existing" and moving
on, because that test was not theirs to fix and nothing said whose it was.

WHAT THIS DOES. Runs every tools/checks/tests/test_*.sh in this repository
the way a consumer will, in two respects at once, and reports each test that
fails that way:

  1. git ignores what a typical consuming repository ignores
     (CONSUMER_IGNORES below). The ignores are handed to git as
     core.excludesFile through GIT_CONFIG_COUNT, so every git command the
     tests run inherits them -- including the ones inside the scratch
     clones most tests build of this repository.
  2. the source's own tools/ is not there (since 2026-09-26). The tests run
     in a scratch COPY of this repository from which every tools/ file a
     consumer does not receive has been removed: what stays is the vendored
     engine, tools/checks/, and every file a practice here declares in
     `ships:` (practice: practice-carries-its-files). A test that reads a
     source-only script -- create-word-doc's test copied
     tools/create_word_doc.py, which no consumer had -- fails here, at home.

Nothing is written to the repository or its history: the copy is a
throwaway directory, its removed files are marked skip-worktree in the
COPY's own index so `git status` there stays as clean as the real one, and
it sits beside symlinks to this repository's siblings, so a test that looks
for `$ROOT/../BestPractice` finds it exactly as it does at home.

Why not a scratch clone with those entries committed to its .gitignore,
which reads more like "a consumer": the commit that adds them is a commit
the tests then see. Tried 2026-09-25 against a real source's suite: its
commit-author and commit-date tests both went red on that one commit, which
says nothing about a consumer and would have buried the real finding. An
exclude file has the same effect on `git add`, `git status` and
`git check-ignore` with no commit at all. What it does NOT reproduce: a
check that reads the .gitignore FILE's text itself, rather than asking git,
sees the source's own .gitignore here.

While the tests run, the person's own core.excludesFile is replaced, not
added to (git keeps one), so a test cannot lean on a global ignore that
only this machine has either (practice: fixture-owns-its-state).

WHO RUNS IT. precedent_push_check.py, in a practice source's full tier,
right after the source's own suite (practice: two-check-levels). By hand:

    python3 tools/precedent_consumer_shape.py [--repo DIR]

Exit status: 0 every test passed, or there is no tools/checks/tests/ to
run (said so); 1 a test failed in the consumer shape; 2 could not run (not
a git checkout, or a git too old for GIT_CONFIG_COUNT).
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent

# What a typical consuming repository's .gitignore carries: dependency
# directories, build output, virtual environments, logs and local secrets.
# The first four are the ones a real consumer has been measured ignoring;
# the rest are as common, and a test the list catches by accident is still a
# test that assumed its home layout. ONE list -- nothing else restates it
# (practice: registry-source-of-truth).
CONSUMER_IGNORES = (
    'vendor/', 'node_modules/', 'build/', 'dist/', 'target/', 'out/',
    'coverage/', '.venv/', 'venv/', '__pycache__/', '*.log', '.env',
)
TAIL_LINES = 15


def _git_toplevel(start):
    p = subprocess.run(['git', '-C', str(start), 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    out = p.stdout.strip()
    return pathlib.Path(out) if p.returncode == 0 and out else None


def _git_supports_config_env():
    """GIT_CONFIG_COUNT arrived in git 2.31. An older git ignores it without
    a word, which would make every test pass here for the wrong reason."""
    p = subprocess.run(['git', 'version'], capture_output=True, text=True)
    m = re.search(r'(\d+)\.(\d+)', p.stdout)
    return bool(m) and (int(m.group(1)), int(m.group(2))) >= (2, 31)


def consumer_env(ignore_file, base=None):
    """`base` (default: this process's environment) with core.excludesFile
    appended to any GIT_CONFIG_COUNT entries already there, never replacing
    them."""
    env = dict(os.environ if base is None else base)
    try:
        n = int(env.get('GIT_CONFIG_COUNT') or 0)
    except ValueError:
        n = 0
    env[f'GIT_CONFIG_KEY_{n}'] = 'core.excludesFile'
    env[f'GIT_CONFIG_VALUE_{n}'] = str(ignore_file)
    env['GIT_CONFIG_COUNT'] = str(n + 1)
    return env


def consumer_tools(root):
    """-> {tools/<path>} a consumer receives, of what sits under `root`'s
    tools/: the vendored engine (what this repository's own
    ENGINE_MANIFEST.json records, plus every name the engine lists for
    either kind), everything under tools/checks/, and every file an active
    practice here ships. Everything else under tools/ is the source's own."""
    keep = {'tools/ENGINE_MANIFEST.json'}
    try:
        manifest = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json')
                              .read_text(encoding='utf-8'))
        keep |= {f'tools/{n}' for n in manifest.get('files') or []
                 if isinstance(n, str)}
    except (OSError, ValueError, AttributeError):
        pass
    sys.path.insert(0, str(HERE))
    try:
        import build_views as bv
        import split_practices as sp
    except Exception:                               # practice: fail-gracefully
        return None
    keep |= bv._engine_tool_paths()
    for path in sorted((root / 'practices').glob('*.md')):
        try:
            fm, _sections = sp._read_practice_file(path)
            if bv._json_str(fm.get('status', '"active"')) not in ('', 'active'):
                continue
            keep |= set(bv.ships_paths(fm))
        except Exception:                           # practice: fail-gracefully
            continue
    return keep


def source_only_tools(root, keep):
    """-> sorted [tools/<path>] under `root` that a consumer does not
    receive -- the files the consumer-shaped copy leaves out."""
    tools = root / 'tools'
    if not tools.is_dir():
        return []
    out = []
    for f in sorted(tools.rglob('*')):
        if not f.is_file() and not f.is_symlink():
            continue
        rel = f.relative_to(root).as_posix()
        if rel.startswith('tools/checks/') or '__pycache__' in f.parts:
            continue
        if rel not in keep:
            out.append(rel)
    return out


def consumer_copy(root, tmp, drop):
    """Copy `root` into `tmp`/<its name>, beside symlinks to each of its
    real siblings, and remove `drop` from the copy. -> the copy's path.

    `.git` is copied as it is, so the copy has the same branch, remotes,
    history and uncommitted changes as the original -- only the dropped
    files differ, and each tracked one is marked skip-worktree in the
    copy's own index so that difference is not itself a change a test can
    see. A `.git` FILE (a linked worktree or a submodule) points at an
    index the copy would share with the original, so that shape is refused
    by the caller before this runs."""
    dest = pathlib.Path(tmp) / root.name
    shutil.copytree(root, dest, symlinks=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    for sibling in sorted(root.parent.iterdir()):
        if sibling.name != root.name:
            try:
                (pathlib.Path(tmp) / sibling.name).symlink_to(sibling)
            except OSError:
                pass
    tracked = set(subprocess.run(
        ['git', '-C', str(dest), 'ls-files', '-z', '--', 'tools'],
        capture_output=True, text=True).stdout.split('\0'))
    for rel in drop:
        (dest / rel).unlink(missing_ok=True)
    hide = [rel for rel in drop if rel in tracked]
    if hide:
        subprocess.run(['git', '-C', str(dest), 'update-index',
                        '--skip-worktree', '--', *hide],
                       capture_output=True, text=True)
    return dest


def run(root):
    """-> exit status, having printed a line per test and a verdict."""
    tests_dir = root / 'tools' / 'checks' / 'tests'
    tests = sorted(tests_dir.glob('test_*.sh')) if tests_dir.is_dir() else []
    if not tests:
        print('precedent_consumer_shape: no tools/checks/tests/test_*.sh in '
              'this repository -- nothing ships from here, nothing to run')
        return 0
    if not _git_supports_config_env():
        print('precedent_consumer_shape: could not run -- this git is older '
              'than 2.31 and would ignore the consumer ignores silently',
              file=sys.stderr)
        return 2
    if not (root / '.git').is_dir():
        print('precedent_consumer_shape: could not run -- .git here is not a '
              'directory (a linked worktree or a submodule), and a copy of '
              'this checkout would share its index with the original. Run it '
              'from the main checkout', file=sys.stderr)
        return 2
    keep = consumer_tools(root)
    if keep is None:
        print('precedent_consumer_shape: could not run -- the engine beside '
              'this script (build_views.py, split_practices.py) did not '
              'import, so what a consumer receives is unknown',
              file=sys.stderr)
        return 2
    drop = source_only_tools(root, keep)

    print(f'precedent_consumer_shape: {len(tests)} test(s), with git '
          f'ignoring what a typical consumer does: '
          f'{" ".join(CONSUMER_IGNORES)}', flush=True)
    if drop:
        print(f'  and without this source\'s own tools/, which no consumer '
              f'receives: {" ".join(drop)}', flush=True)
    else:
        print('  (every tools/ file here reaches consumers, so the copy '
              'lacks nothing)', flush=True)
    failed = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='consumer-shape-') as tmp:
        ignore_file = pathlib.Path(tmp) / 'consumer-gitignore'
        ignore_file.write_text('\n'.join(CONSUMER_IGNORES) + '\n',
                               encoding='utf-8')
        env = consumer_env(ignore_file)
        copy_root = consumer_copy(root, pathlib.Path(tmp) / 'tree', drop)
        copy_tests = copy_root / 'tools' / 'checks' / 'tests'
        for i, t in enumerate(tests, 1):
            t0 = time.monotonic()
            p = subprocess.run(['bash', t.name], cwd=copy_tests, env=env,
                               capture_output=True, text=True)
            took = time.monotonic() - t0
            # practice: slow-steps-report-and-cache -- a suite of real
            # tests takes most of a minute; say where it is as it goes.
            left = len(tests) - i
            if p.returncode == 0:
                print(f'[{i}/{len(tests)}] {t.name}: passed in {took:.0f}s '
                      f'({left} left)', flush=True)
                continue
            failed.append(t.name)
            print(f'[{i}/{len(tests)}] {t.name}: failed (exit {p.returncode}) '
                  f'in {took:.0f}s ({left} left); last lines of its output:',
                  flush=True)
            for line in (p.stdout + p.stderr).rstrip().splitlines()[-TAIL_LINES:]:
                print(f'      | {line}')
    total = time.monotonic() - started

    if not failed:
        print(f'precedent_consumer_shape: all {len(tests)} passed in '
              f'{total:.0f}s')
        return 0
    print()
    for name in failed:
        print(f'FAILED: {name} -- fails in a consumer-shaped copy of this '
              f'repository')
    print()
    print('Every repository that resolves this source runs these tests, and '
          'sees each one above')
    print('red and cannot fix it -- the test is this source\'s. The two usual '
          'causes:')
    print('  - a fixture planted under a path consumers ignore and staged '
          'with a plain `git add`:')
    print('    stage fixtures with `git add -f`;')
    print('  - a tools/ file the test reads that no consumer receives (listed '
          'above): declare it in')
    print('    the owning practice\'s `ships:` so every consumer gets it '
          '(practice-carries-its-files).')
    print('If a test above also fails in the plain run of this suite, fix '
          'that first.')
    return 1


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__)
        return 0
    root = None
    if '--repo' in argv:
        i = argv.index('--repo')
        if i + 1 >= len(argv):
            print('precedent_consumer_shape: --repo needs a directory',
                  file=sys.stderr)
            return 2
        root = _git_toplevel(argv[i + 1])
    else:
        root = _git_toplevel(pathlib.Path.cwd())
    if root is None:
        print('precedent_consumer_shape: not inside a git checkout; nothing '
              'to run', file=sys.stderr)
        return 2
    return run(root)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
