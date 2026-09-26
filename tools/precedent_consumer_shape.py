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
with git told to ignore what a typical consuming repository ignores
(CONSUMER_IGNORES below), and reports each test that fails that way. The
ignores are handed to git as core.excludesFile through GIT_CONFIG_COUNT, so
every git command the tests run inherits them -- including the ones inside
the scratch clones most tests build of this repository -- and nothing is
written to the repository or its history.

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
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

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

    print(f'precedent_consumer_shape: {len(tests)} test(s), with git '
          f'ignoring what a typical consumer does: '
          f'{" ".join(CONSUMER_IGNORES)}', flush=True)
    failed = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='consumer-shape-') as tmp:
        ignore_file = pathlib.Path(tmp) / 'consumer-gitignore'
        ignore_file.write_text('\n'.join(CONSUMER_IGNORES) + '\n',
                               encoding='utf-8')
        env = consumer_env(ignore_file)
        for i, t in enumerate(tests, 1):
            t0 = time.monotonic()
            p = subprocess.run(['bash', t.name], cwd=tests_dir, env=env,
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
        print(f'FAILED: {name} -- fails where git ignores what a consuming '
              f'repository typically ignores')
    print()
    print('Every repository that resolves this source runs these tests, and '
          'one that ignores any of')
    print('those paths sees each one above red and cannot fix it -- the test '
          'is this source\'s.')
    print('The usual cause is a fixture planted under an ignored path and '
          'staged with a plain')
    print('`git add`: stage fixtures with `git add -f`. If a test above also '
          'fails in the plain')
    print('run of this suite, fix that first -- this run only adds the '
          'ignores.')
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
