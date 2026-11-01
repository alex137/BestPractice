# The harness tests for the harness itself
#
# tools/harness/vh_harness_self.py -- part of the verification harness:
# the harness itself: the runner, --as-ci, its fixtures and their isolation.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_harness_drops_inherited_git_repository_variables():
    """A harness started under `git bisect run`, from a linked worktree,
    leaves the repository it was started in alone (2026-10-06).

    On 2026-10-01 a session bisected with a harness check as the test, from
    a linked worktree. `git bisect run` exports GIT_DIR, every fixture
    inherited it, and the fixture's `git init --bare` re-initialised the
    worktree's git directory as bare: `core.bare = true` in the main clone's
    shared config, and the fixture's commits on the worktree's HEAD
    (gotchas/gotcha-2026-10-01-a-harness-check-run-in-a-linked-worktree-
    turns-the-main-clone-bare.md).

    The fixture is a throwaway repository with a linked worktree, and a
    child process carrying GIT_DIR exactly as `git bisect run` sets it there,
    which then does what fixtures do: `git init --bare`, `git init`, a
    commit. THE CONTROL: the same child without importing this module does
    turn the main clone bare and moves the worktree's HEAD, so the fixture
    reproduces the trap and the import is what stops it
    (practice: control-asserts-which-failure)."""
    import tempfile
    name = ('the harness drops an inherited GIT_DIR, so a run under `git '
            'bisect run` in a linked worktree leaves the main clone alone')
    child = (
        'import os, subprocess, sys\n'
        'if sys.argv[2] == "import":\n'
        '    sys.path.insert(0, sys.argv[3]); import verify_harness\n'
        't = sys.argv[1]\n'
        'def g(*a, cwd=None):\n'
        '    subprocess.run(["git", *a], cwd=cwd, capture_output=True)\n'
        'g("init", "-q", "--bare", t + "/origin.git")\n'
        'g("init", "-q", t + "/proj")\n'
        'open(t + "/proj/f.txt", "w").write("fixture\\n")\n'
        'g("add", "-A", cwd=t + "/proj")\n'
        # Its own author: importing this module drops GIT_AUTHOR_*, and a
        # runner with an empty $HOME has no user.name to fall back on.
        'g("-c", "user.name=F", "-c", "user.email=f@example.com", "commit",\n'
        '  "-qm", "installed, catalogue vendored", cwd=t + "/proj")\n')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = {k: v for k, v in os.environ.items()
               if k not in GIT_REPOSITORY_ENV_VARS}
        env.update(GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
                   GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com')

        def git(*args, cwd):
            return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                                  capture_output=True, text=True).stdout.strip()

        def attempt(label, mode):
            main, linked = tmp / label / 'main', tmp / label / 'linked'
            main.mkdir(parents=True)
            git('init', '-q', '-b', 'main', cwd=main)
            git('commit', '-q', '--allow-empty', '-m',
                'base\n\nSession: none available (fixture)', cwd=main)
            git('worktree', 'add', '-q', '--detach', str(linked), 'HEAD',
                cwd=main)
            head = git('rev-parse', 'HEAD', cwd=linked)
            gitdir = git('rev-parse', '--absolute-git-dir', cwd=linked)
            work = tmp / label / 'fixture'
            work.mkdir()
            subprocess.run([sys.executable, '-c', child, str(work), mode,
                            str(ROOT / 'tools')],
                           cwd=str(linked), env=dict(env, GIT_DIR=gitdir),
                           capture_output=True, text=True)
            return (git('config', '--get', 'core.bare', cwd=main) == 'true',
                    git('rev-parse', 'HEAD', cwd=linked) != head,
                    (work / 'origin.git' / 'HEAD').is_file()
                    and bool(git('rev-parse', '-q', '--verify', 'HEAD',
                                 cwd=work / 'proj')))

        bare, moved, own = attempt('control', 'plain')
        cases.append((f'control: without the harness, the inherited GIT_DIR '
                      f'turns the main clone bare (bare={bare}) and moves the '
                      f'worktree\'s HEAD (moved={moved})', bare and moved))
        bare, moved, own = attempt('harness', 'import')
        cases.append((f'with the harness imported the main clone stays a work '
                      f'tree (bare={bare})', not bare))
        cases.append((f'...the worktree\'s HEAD does not move (moved={moved})',
                      not moved))
        cases.append((f'...and the fixture\'s repositories are its own '
                      f'(own={own})', own))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_harness_fixtures_run_no_background_maintenance():
    """A fixture's git never starts background maintenance, so copying a
    fixture right after a commit cannot race a lock file git is about to
    delete (issue #1207: check_precedent_check_fires died copying
    pristine/.git/objects/maintenance.lock). Run in a subprocess that imports
    this module, so it measures the block at the top of this file rather than
    whatever the container's own git config says; the control runs the same
    probe without the import and must see git's defaults."""
    import tempfile as _tf
    name = 'fixture git runs no background maintenance'
    probe = ('import subprocess, sys\n'
             'if sys.argv[1] == "import":\n'
             '    sys.path.insert(0, sys.argv[2]); import verify_harness\n'
             'r = subprocess.run(["git", "-C", sys.argv[3], "config", "--get",\n'
             '                    sys.argv[4]], capture_output=True, text=True)\n'
             'print(r.stdout.strip())\n')
    cases = []
    with _tf.TemporaryDirectory(prefix='harness-maint-') as td:
        env = {k: v for k, v in os.environ.items()
               if not k.startswith('GIT_CONFIG_')}
        subprocess.run(['git', 'init', '-q', td], env=env, capture_output=True)

        def ask(mode, key):
            return subprocess.run(
                [sys.executable, '-c', probe, mode, str(ROOT / 'tools'), td, key],
                env=env, capture_output=True, text=True).stdout.strip()
        for key, value in HARNESS_GIT_CONFIG:
            got = ask('import', key)
            cases.append((f'with the harness imported, {key} is {value} '
                          f'(got {got!r})', got == value))
        got = ask('plain', 'maintenance.auto')
        cases.append((f'control: without the import maintenance.auto is not '
                      f'forced off (got {got!r})', got != 'false'))
        planted = subprocess.run(
            [sys.executable, '-c',
             'import os, sys; sys.path.insert(0, sys.argv[1]); '
             'import verify_harness; print(os.environ["GIT_CONFIG_KEY_0"], '
             'os.environ["GIT_CONFIG_COUNT"])', str(ROOT / 'tools')],
            env=dict(env, GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='a.b',
                     GIT_CONFIG_VALUE_0='c'),
            capture_output=True, text=True).stdout.split()
        cases.append((f'an entry already in GIT_CONFIG_COUNT is kept, not '
                      f'replaced (got {planted})', planted == ['a.b', '3']))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_bare_all_runs_across_the_cores():
    """A bare `--all` is dispatched to run_as_ci with every planted case
    (2026-10-06: one process took about 31 minutes where the same set side
    by side takes about 11), and a shard, a filtered run, or an explicit
    serial run is not -- so nothing recurses and profiling stays possible."""
    import inspect
    cases = [
        ('a bare --all runs in parallel',
         _bare_all_runs_in_parallel(['--all'], {})),
        ('a shard process (no --all) does not',
         not _bare_all_runs_in_parallel([], {'PRECEDENT_HARNESS_ALL': '1'})),
        ('--all with PRECEDENT_CHECK_ONLY keeps its filter, in one process',
         not _bare_all_runs_in_parallel(['--all'],
                                        {'PRECEDENT_CHECK_ONLY': 'check_x'})),
        ('--all with PRECEDENT_CHECK_SKIP keeps its filter, in one process',
         not _bare_all_runs_in_parallel(['--all'],
                                        {'PRECEDENT_CHECK_SKIP': 'check_x'})),
        ('PRECEDENT_HARNESS_SERIAL=1 keeps the one-process run',
         not _bare_all_runs_in_parallel(['--all'],
                                        {'PRECEDENT_HARNESS_SERIAL': '1'})),
    ]
    import inspect
    src = inspect.getsource(run_as_ci)
    cases.append(('every_case gives each process PRECEDENT_HARNESS_ALL=1',
                  "env['PRECEDENT_HARNESS_ALL'] = '1'" in src
                  and 'if every_case:' in src))
    main_src = pathlib.Path(__file__).read_text(encoding='utf-8')
    cases.append(('the entry point dispatches it, and passes --record-times on',
                  "_done(run_as_ci(every_case=True,\n"
                  "                        record_times='--record-times' in sys.argv[1:]))"
                  in main_src))
    failed = [n for n, ok in cases if not ok]
    check(f'a bare --all runs across the cores ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_isolated_copy_carries_uncommitted_changes():
    """The isolated harness judges what the rest of the full check judges.

    2026-10-01: a full check run before a commit went green while the
    commit it was about to make added a check with no planted case. The
    isolated copy was a clone of HEAD, so the harness judged the commit
    before the change; reproduced on that commit, committed, the same run
    fails with "untested: ['whats-new']". _carry_uncommitted now writes the
    checkout's uncommitted state into the copy. The rule under test: a
    tracked edit, a deletion and an untracked file reach the copy, an
    ignored file does not, and a clean checkout carries nothing. Driven
    against a throwaway repository (a whole planted --as-ci run costs
    about nine minutes)."""
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = _stale_ref_fixture_env(tmp)
        src, dst = tmp / 'src', tmp / 'dst'

        def git(repo, *a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=env)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(src)],
                       capture_output=True, env=env)
        (src / 'kept.py').write_text('A = 1\n', encoding='utf-8')
        (src / 'gone.py').write_text('B = 1\n', encoding='utf-8')
        (src / '.gitignore').write_text('scratch/\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'base')

        def copy():
            import shutil
            shutil.rmtree(dst, ignore_errors=True)
            subprocess.run(['git', 'clone', '-q', str(src), str(dst)],
                           capture_output=True, env=env)
            return _carry_uncommitted(src, dst)
        cases.append(('a clean checkout carries nothing', copy() == 0, ''))
        (src / 'kept.py').write_text('A = 2\n', encoding='utf-8')
        (src / 'gone.py').unlink()
        (src / 'new_check.py').write_text('C = 3\n', encoding='utf-8')
        (src / 'scratch').mkdir()
        (src / 'scratch' / 'notes.txt').write_text('x', encoding='utf-8')
        n = copy()
        cases.append(('the edit, the deletion and the new file are counted',
                      n == 3, repr(n)))
        cases.append(('the tracked edit reaches the copy',
                      (dst / 'kept.py').read_text(encoding='utf-8') == 'A = 2\n', ''))
        cases.append(('the deletion reaches the copy',
                      not (dst / 'gone.py').exists(), ''))
        cases.append(('the untracked file reaches the copy',
                      (dst / 'new_check.py').is_file(), ''))
        cases.append(('an ignored file does not',
                      not (dst / 'scratch').exists(), ''))
    bad = [(n_, d) for n_, ok, d in cases if not ok]
    check(f'the isolated harness copy carries the checkout\'s uncommitted '
          f'changes ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n_}: {d}' for n_, d in bad))


def check_isolated_run_matches_the_runner():
    """_isolated_env() and _new_entries(), which decide whether the isolated
    run looks like GitHub's runner and whether it stayed that way. Pure
    functions, so this is cheap: the run itself is minutes, and is what the
    full check at staging executes."""
    import tempfile
    base = {'PATH': '/bin', 'HOME': '/root', 'TZ': 'America/Argentina/Buenos_Aires',
            'PRECEDENT_GIT_TOKEN': 't', 'PRECEDENT_SOURCE_BASE_URL': 'u',
            'PRECEDENT_INDIVIDUAL_REPO': 'r', 'PRECEDENT_COMMIT_NAME': 'n',
            'PRECEDENT_CHECK_ONLY': 'x', 'GIT_AUTHOR_NAME': 'a',
            'CLAUDE_PROJECT_DIR': '/p'}
    env = _isolated_env(base, '/tmp/empty-home')
    cases = [
        ('no source token, base URL or individual repo',
         not {'PRECEDENT_GIT_TOKEN', 'PRECEDENT_SOURCE_BASE_URL',
              'PRECEDENT_INDIVIDUAL_REPO'} & set(env)),
        ('no PRECEDENT_* or GIT_* variable leaks through except the ones set',
         {k for k in env if k.startswith(('PRECEDENT_', 'GIT_'))} ==
         {'PRECEDENT_USER_CONFIG', 'GIT_ALLOW_PROTOCOL', 'GIT_TERMINAL_PROMPT',
          'GIT_CONFIG_NOSYSTEM'}),
        ('an empty $HOME and a user config that does not exist',
         env['HOME'] == '/tmp/empty-home' and
         env['PRECEDENT_USER_CONFIG'].startswith('/tmp/empty-home/')),
        ('the runner\'s clock, UTC', env['TZ'] == 'UTC'),
        ('git may not fetch over a network', env['GIT_ALLOW_PROTOCOL'] == 'file'),
        ('PATH is kept', env['PATH'] == '/bin'),
        ('the base environment is not changed', base['TZ'] != 'UTC'),
    ]
    with tempfile.TemporaryDirectory() as td:
        (pathlib.Path(td) / 'BestPractice').mkdir()
        before = ['BestPractice']
        quiet = _new_entries(td, before)
        (pathlib.Path(td) / 'BestPractice-clone').mkdir()
        cases += [('nothing new beside the copy reads as isolated', quiet == []),
                  ('a sibling that appeared is named',
                   _new_entries(td, before) == ['BestPractice-clone'])]
    failed = [n for n, ok in cases if not ok]
    check(f'the isolated --as-ci run looks like GitHub\'s runner '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))
def check_seed_cache_copies_what_a_seed_writes():
    """The fixture seed cache (_seed_fixture_engine) holds its contract: a
    copy is byte-for-byte what a real seed writes, mode bits included, and
    the key moves whenever an input seed can read moves (practice:
    review-against-a-contract).

    Discriminating cases (practice: control-asserts-which-failure): the
    first seed into an empty cache really runs and its output says so; the
    second is a copy and says so; both trees equal a seed run with the cache
    off. The key cases use a scratch checkout as the root, never this one,
    so no other check running beside this one sees a dirty tree: an edited
    tracked file, an untracked file, a new commit, a different
    precedent.json in the destination, a variable in the environment and a
    file appearing in HOME each give a new key, and putting the edit back
    gives the old one."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-seed-cache-'))
    cases = []
    try:
        (tmp / 'home').mkdir()
        env = {**os.environ, 'HOME': str(tmp / 'home'),
               'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json'),
               'PRECEDENT_SEED_CACHE_DIR': str(tmp / 'cache'),
               'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
               'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
        env.pop('PRECEDENT_NO_SEED_CACHE', None)

        def dest(name, cfg='{"format_version": 1}\n'):
            d = tmp / name
            d.mkdir()
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(d)],
                           capture_output=True, env=env)
            (d / 'precedent.json').write_text(cfg, encoding='utf-8')
            (d / 'AGENTS.md').write_text('# fixture\n', encoding='utf-8')
            return d

        def tree(d):
            return {p.relative_to(d).as_posix():
                    (p.read_bytes() if p.is_file() else None, p.stat().st_mode)
                    for p in sorted(d.rglob('*'))
                    if '.git' not in p.relative_to(d).parts}

        real = dest('real')
        _seed_fixture_engine(real, 'consumer', {**env, 'PRECEDENT_NO_SEED_CACHE': '1'},
                             cwd=real)
        cases.append(('CONTROL: with the cache off nothing is kept',
                      not (tmp / 'cache').exists(), ''))
        # The key reads this checkout's refs, and a check running beside this
        # one may move them: Update Vendors fetches origin/<branch> in its
        # source clone, and in a CI checkout, which has no origin/main, that
        # creates the ref partway through the run. A key that moved between
        # the two seeds is a correct miss, not a broken cache, so the pair is
        # tried again in a fresh cache, up to three times, and only a pair
        # whose key held still is judged (2026-11-01, issue #1483: "the
        # second is a copy" failed on main's GitHub test and on no local run).
        moved = 0
        for attempt in range(3):
            cache_env = {**env, 'PRECEDENT_SEED_CACHE_DIR':
                         str(tmp / ('cache' if attempt == 0 else f'cache{attempt}'))}
            first, second = dest(f'first{attempt}'), dest(f'second{attempt}')
            still = dest(f'still{attempt}')     # never seeded: the key's yardstick
            k_before = _seed_cache_key(still, 'consumer', cache_env)
            rc1, out1 = _seed_fixture_engine(first, 'consumer', cache_env, cwd=first)
            rc2, out2 = _seed_fixture_engine(second, 'consumer', cache_env, cwd=second)
            if _seed_cache_key(still, 'consumer', cache_env) == k_before:
                break
            moved += 1
        cases.append(('the key held still for one first-and-second pair (a '
                      'check beside this one moved it in '
                      f'{moved} of {attempt + 1} tries)', moved < 3, ''))
        cases.append(('the first seed into an empty cache really runs',
                      rc1 == 0 and 'SEEDED' in out1, failure_detail(out1, 300)))
        cases.append(('the second is a copy, and says so',
                      rc2 == 0 and 'copied from the harness seed cache' in out2,
                      failure_detail(out2, 300)))
        want = tree(real)
        cases.append(('both trees are what a real seed writes, byte for byte and '
                      'mode for mode', len(want) > 10 and tree(first) == want
                      and tree(second) == want,
                      f'{len(want)} paths; first {tree(first) == want}, '
                      f'second {tree(second) == want}'))

        # The key, against a scratch checkout standing in for this one.
        root = tmp / 'root'
        (root / 'tools').mkdir(parents=True)
        engine = root / 'tools' / 'engine.py'
        engine.write_text('print("engine")\n', encoding='utf-8')
        git = lambda *a: subprocess.run(['git', '-C', str(root), *a],
                                        capture_output=True, env=env)
        git('init', '-q', '-b', 'main')
        git('add', '-A')
        git('commit', '-qm', 'base')
        probe = dest('probe')
        key = lambda e=env, d=probe: _seed_cache_key(d, 'consumer', e, root=root)
        base = key()
        cases.append(('the key is stable on unchanged inputs', base == key(), base))
        engine.write_text('print("edited")\n', encoding='utf-8')
        edited = key()
        engine.write_text('print("engine")\n', encoding='utf-8')
        cases.append(('an uncommitted edit to an engine file moves the key, and '
                      'putting it back restores it', edited != base and key() == base, ''))
        (root / 'tools' / 'new_engine.py').write_text('x = 1\n', encoding='utf-8')
        cases.append(('an untracked file moves the key', key() != base, ''))
        git('add', '-A')
        git('commit', '-qm', 'a new engine file')
        cases.append(('a new commit moves the key', key() != base, ''))
        now = key()
        other = dest('other', '{"format_version": 1, "upstream_branch": "staging"}\n')
        cases.append(('a different precedent.json in the destination moves the key',
                      key(d=other) != now, ''))
        cases.append(('a different PRECEDENT_ variable moves the key',
                      key({**env, 'PRECEDENT_ASSUME_LADDER': 'x'}) != now, ''))
        cases.append(('...and a fresh path for the user config, still absent, does not',
                      key({**env, 'PRECEDENT_USER_CONFIG': str(tmp / 'elsewhere.json')})
                      == now, ''))
        (tmp / 'home' / '.gitconfig').write_text('[user]\n\tname = x\n', encoding='utf-8')
        cases.append(('a file appearing in HOME moves the key', key() != now, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_failure_detail_puts_the_naming_line_first():
    """failure_detail() is what every failing case here reports a tool's
    output with (Morgan, 2026-10-31, strength: decided: "that should be a
    more general rule"; practice: control-asserts-which-failure). Planted:
    a VIOLATION line far above the tail survives, first; output with no such
    line comes back as exactly the tail it replaced."""
    cases = []
    filler = ''.join(f'checked file {i:03d}.md, nothing to say\n' for i in range(200))
    named = 'VIOLATION   planted-check: practices/x.md:3 -- the planted reason'
    long = f'{named}\n{filler}summary: 1 violated, 0 errored\n'
    raw = long[-300:]
    got = failure_detail(long, 300)
    cases.append(('CONTROL: the raw tail of the planted output drops the '
                  'VIOLATION line, so the case below needs the helper',
                  named not in raw, raw))
    cases.append(('a VIOLATION line far above the tail comes first',
                  got.startswith(named), got))
    cases.append(('the tail follows it, and the whole stays within the limit',
                  len(got) <= 300 and got.endswith(long[-60:]), f'{len(got)}: {got!r}'))
    clean = filler + 'summary: 0 violated\n'
    cases.append(('output with no failure-naming line is exactly the tail it '
                  'replaced', failure_detail(clean, 300) == clean[-300:],
                  failure_detail(clean, 300)))
    seen = filler + 'FAIL: the planted case\n'
    cases.append(('a FAIL line the tail already shows is not repeated',
                  failure_detail(seen, 120) == seen[-120:], failure_detail(seen, 120)))
    twice = f'{named}\n{named}\n{filler}'
    cases.append(('a line printed twice is shown once',
                  failure_detail(twice, 400).count(named) == 1, failure_detail(twice, 400)))
    trace = ('Traceback (most recent call last):\n  File "x.py", line 1\n'
             'ValueError: the planted error\n' + filler)
    cases.append(('a traceback and its exception line come first',
                  failure_detail(trace, 400).startswith('Traceback (most recent call last):\n'
                                                        'ValueError: the planted error'),
                  failure_detail(trace, 400)))
    quiet = 'summary: 0 failed, 1 error noted\n' + filler
    cases.append(('lower-case "failed" and "error" in ordinary output are not '
                  'pulled forward', failure_detail(quiet, 200) == quiet[-200:],
                  failure_detail(quiet, 200)))
    many = ''.join(f'VIOLATION   check-{i}: {"x" * 60}\n' for i in range(20)) + filler
    got = failure_detail(many, 400)
    cases.append(('many failure lines are capped at half the limit, and the '
                  'tail still fits', len(got) <= 400 and got.endswith(many[-100:])
                  and len(got.split('\n...\n')[0]) <= 200, got))
    cases.append(('a short output comes back whole',
                  failure_detail('ERROR: short', 300) == 'ERROR: short', ''))
    cases.append(('anything not a string is sliced exactly as before',
                  failure_detail(['a', 'b', 'c'], 2) == ['b', 'c'], ''))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'failure_detail puts the line naming a failure first, then the tail '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_no_fixture_points_git_config_at_dev_null():
    """No tool or test points GIT_CONFIG_GLOBAL (or GIT_CONFIG_SYSTEM) at
    /dev/null: one `git config --global` under it replaces the container's
    null device with an ordinary file (2026-10-10, and again 2026-10-31 in
    the very deep check's session). Fixtures use empty_gitconfig(), a fresh
    empty file each. Also: an inherited GIT_CONFIG_GLOBAL that is not a
    regular file is swapped for an empty one when the harness starts.

    Negative control: the scan fires on a planted line of each form."""
    name = 'no tool or fixture points git\'s global config at /dev/null'
    pat = re.compile(r'GIT_CONFIG_(?:GLOBAL|SYSTEM)\W{0,6}(?:=|:)\s*'
                     r'(?:os\.devnull|[\'"]?/dev/null)')
    hits = []
    for path in sorted((ROOT / 'tools').rglob('*')):
        if path.suffix not in ('.py', '.sh') or not path.is_file():
            continue
        for i, line in enumerate(path.read_text(encoding='utf-8', errors='replace')
                                 .splitlines(), 1):
            if line.lstrip().startswith('#') or 'pat = re.compile' in line:
                continue
            if pat.search(line) and 'planted' not in line:
                hits.append(f'{path.relative_to(ROOT)}:{i}')
    dn, var = 'os.' + 'devnull', 'GIT_CONFIG_' + 'GLOBAL'   # split, so this
    planted = [f"env = dict(os.environ, {var}={dn})",        # scan skips them
               f"os.environ['{var}'] = {dn}",
               f"{var}=/dev/null git config --global x y",
               f"'GIT_CONFIG_' 'SYSTEM': {dn}".replace("' '", '')]
    fires = all(pat.search(p) for p in planted)
    inherited = os.environ.get('GIT_CONFIG_GLOBAL')
    swapped = not inherited or os.path.isfile(inherited)
    check(name, not hits and fires and swapped,
          '; '.join(hits[:10]) if hits else
          ('the scan misses a planted form' if not fires else
           f'GIT_CONFIG_GLOBAL is {inherited}, not a regular file'))


def check_fixtures_own_the_credential_environment():
    """The harness's own result must not depend on whether the container it
    runs in happens to carry a private-source credential
    (practice: fixture-owns-its-state).

    THE INCIDENT (2026-09-11). Two checks below build a scenario where NO
    credential is available -- check_source_credentials' "with no base url
    the shared source is named on stderr as NOT in force", and
    check_individual_source_bootstrap_self_heals' "--write-session-hook with
    NO --repo-url ... degrades quietly" -- and then spawned a subprocess
    carrying the container's own environment. Since 2026-09-10 a real
    session carries PRECEDENT_GIT_TOKEN and PRECEDENT_SOURCE_BASE_URL
    (INSTALL.md section 8), so the subprocess found a URL after all and did
    the thing the case says it must not do. Measured on one tree with no code
    change: `4 failed` with the variables set, `2 failed` under `env -u`.
    Neither run was wrong about itself, which is the whole problem -- a
    harness result nobody can read.

    The two fixtures were fixed first by popping both variables in their own
    run() helpers, which is right where a reader meets the hazard and is kept.
    The scrub at the top of this file is the half that covers the fixture
    nobody has written yet, for the reason fixture-owns-its-state states
    outright: it inherits the same invisible dependency and will not notice.
    This check is what stops that scrub being deleted or quietly outgrown.

    Case 3 is the controlling one, and it is a real negative control rather
    than a re-reading of case 1: it PLANTS both variables in a subprocess's
    environment and imports this module there, so it measures the scrub
    doing its job rather than the container happening to be clean. Case 4 is
    the other direction -- a fixture that genuinely wants a credential must
    still be able to set one, or check_source_credentials could not test the
    credentialed half at all."""
    probe_dir = str(ROOT / 'tools')
    cases = []

    cases.append(('this process carries neither credential variable, whatever '
                  'the container set',
                  all(v not in os.environ for v in CREDENTIAL_ENV_VARS),
                  repr({v: os.environ.get(v) for v in CREDENTIAL_ENV_VARS})))

    # An ordinary fixture subprocess, spawned the way every fixture here
    # spawns one: env=dict(os.environ).
    r = subprocess.run(
        [sys.executable, '-c',
         'import json, os, sys; print(json.dumps([os.environ.get(v) for v in '
         'sys.argv[1:]]))', *CREDENTIAL_ENV_VARS],
        capture_output=True, text=True, env=dict(os.environ))
    cases.append(('a subprocess spawned with env=dict(os.environ) -- what '
                  'every fixture here does -- carries neither either',
                  r.returncode == 0 and json.loads(r.stdout or '[1]') ==
                  [None] * len(CREDENTIAL_ENV_VARS),
                  r.stdout + r.stderr))

    # THE CONTROLLING CASE: both planted, then this module imported.
    planted = {**os.environ,
               'PRECEDENT_GIT_TOKEN': 'planted-not-a-real-token',
               'PRECEDENT_SOURCE_BASE_URL': 'https://planted.invalid'}
    r2 = subprocess.run(
        [sys.executable, '-c',
         f'import sys; sys.path.insert(0, {probe_dir!r}); '
         'import json, os, verify_harness as vh; '
         'print(json.dumps([os.environ.get(v) for v in vh.CREDENTIAL_ENV_VARS]))'],
        capture_output=True, text=True, env=planted)
    tail = (r2.stdout or '').strip().splitlines()[-1:] or ['']
    cases.append(('with both variables PLANTED in the environment, importing '
                  'this module removes them -- the scrub, measured rather '
                  'than assumed',
                  r2.returncode == 0 and json.loads(tail[0] or '[1]') ==
                  [None] * len(CREDENTIAL_ENV_VARS),
                  failure_detail(r2.stdout, 400) + failure_detail(r2.stderr, 400)))

    # And the other direction.
    r3 = subprocess.run(
        [sys.executable, '-c',
         'import os; print(os.environ.get("PRECEDENT_GIT_TOKEN"))'],
        capture_output=True, text=True,
        env={**os.environ, 'PRECEDENT_GIT_TOKEN': 'fixture-planted'})
    cases.append(('a fixture that sets a credential EXPLICITLY still gets it '
                  '-- the scrub clears the ambient one, it does not make a '
                  'credential unreachable',
                  r3.stdout.strip() == 'fixture-planted',
                  r3.stdout + r3.stderr))

    # THE SAME SHAPE, THIRD INSTANCE: the freshness also-list. Planted and
    # measured exactly like the credential pair above, because the failure it
    # caused was worse -- a guard fixture inheriting it walked out of its own
    # temporary clone into this container's real attached repositories and
    # blocked on one it could not fetch, turning two checks red on every
    # machine that has the variable set and leaving them green everywhere
    # else.
    r4 = subprocess.run(
        [sys.executable, '-c',
         f'import sys; sys.path.insert(0, {probe_dir!r}); '
         'import os, verify_harness as vh; '
         'print(os.environ.get("PRECEDENT_FRESHNESS_ALSO"))'],
        capture_output=True, text=True,
        env={**os.environ,
             'PRECEDENT_FRESHNESS_ALSO': '/planted/repo=main'})
    tail4 = (r4.stdout or '').strip().splitlines()[-1:] or ['']
    cases.append(('with PRECEDENT_FRESHNESS_ALSO planted, importing this '
                  'module removes it too -- a guard fixture checks the '
                  'repository it built and no other',
                  r4.returncode == 0 and tail4[0] == 'None',
                  failure_detail(r4.stdout, 400) + failure_detail(r4.stderr, 400)))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'no fixture inherits the private-source credential or the '
          f'freshness also-list from the container ({len(cases)} stated '
          f'cases, the planted variables being the controlling ones)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_every_tempdir_cleanup_retries():
    """A transient `Directory not empty` on a TemporaryDirectory's cleanup
    is retried for every check, not one (2026-10-05, the recurrence on a
    second check), and a directory that never empties still raises with
    its contents."""
    import tempfile
    cases = []
    real = shutil.rmtree
    calls = {'n': 0}

    def once_busy(path, *a, **k):
        calls['n'] += 1
        if calls['n'] == 1:
            raise OSError(39, 'Directory not empty')
        return real(path, *a, **k)

    def always_busy(path, *a, **k):
        raise OSError(39, 'Directory not empty')
    try:
        shutil.rmtree = once_busy
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / 'f').write_text('x')
        shutil.rmtree = real
        cases.append(('a delete that fails once is retried and the directory goes',
                      calls['n'] == 2 and not os.path.exists(d)))
        shutil.rmtree = always_busy
        said = ''
        try:
            with tempfile.TemporaryDirectory() as d2:
                (pathlib.Path(d2) / 'left').write_text('x')
        except OSError as e:
            said = str(e)
        shutil.rmtree = real
        cases.append(('...one that never empties still raises, naming what is left',
                      'still not empty' in said and 'left' in said))
    finally:
        shutil.rmtree = real
        for leftover in [x for x in (locals().get('d2'),) if x]:
            real(leftover, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_as_ci_parts_partition_the_suite():
    """`--as-ci` runs its shards side by side and deals CI's rest shard into
    parts (_as_ci_runs). Whatever the job count, every check must run in
    exactly one process, the heavy shard must be CI's own, and every part
    must still go by PRECEDENT_CHECK_SKIP -- the filter path CI's rest
    shard takes.

    WHY. 2026-09-30: the serial run cost a landing check about sixteen
    minutes on a four-core session. A split that dropped or doubled a check
    would be faster and wrong, and nothing else would notice."""
    cases = []
    names = sorted(n for n, v in globals().items()
                   if n.startswith('check_') and callable(v))

    def covered(env_extra):
        if 'PRECEDENT_CHECK_ONLY' in env_extra:
            return set(env_extra['PRECEDENT_CHECK_ONLY'].split(','))
        return set(names) - set(env_extra.get('PRECEDENT_CHECK_SKIP', '').split(','))

    for jobs in (1, 2, 3, 4, 7):
        runs = _as_ci_runs(jobs, names)
        seen = collections.Counter(n for _l, e in runs for n in covered(e))
        doubled = sorted(n for n, c in seen.items() if c > 1)
        missing = sorted(set(names) - set(seen))
        cases.append((f'{jobs} job(s): every check runs exactly once',
                      not doubled and not missing,
                      f'doubled {doubled[:3]} missing {missing[:3]}'))
        heavy = [e for _l, e in runs if 'PRECEDENT_CHECK_ONLY' in e]
        cases.append((f'{jobs} job(s): the heavy shard is the one CI runs',
                      heavy == [e for _l, e in CI_SHARDS if 'PRECEDENT_CHECK_ONLY' in e],
                      str(heavy)[:200]))
        cases.append((f'{jobs} job(s): every other part runs by SKIP',
                      all('PRECEDENT_CHECK_SKIP' in e for _l, e in runs
                          if 'PRECEDENT_CHECK_ONLY' not in e), ''))
        cases.append((f'{jobs} job(s): {max(jobs, len(CI_SHARDS))} process(es)',
                      len(runs) == max(jobs, len(CI_SHARDS)), str(len(runs))))
    # Dealt by recorded time: even parts, the same on every machine.
    planted = {'check_a': 50.0, 'check_b': 40.0, 'check_c': 30.0,
               'check_d': 20.0, 'check_e': 10.0}
    fake = sorted(planted) + ['check_f', 'check_g']
    dealt = _deal_by_time(fake, 2, planted, 5.0)
    loads = sorted(sum(planted.get(n, 5.0) for n in part) for part in dealt)
    cases.append(('the slowest checks are spread, not bunched',
                  loads == [80.0, 80.0], str(dealt)))
    cases.append(('the deal is the same whatever order the names come in',
                  _deal_by_time(list(reversed(fake)), 2, planted, 5.0) == dealt, ''))
    cases.append(('with no record, every check still runs exactly once',
                  sorted(n for part in _deal_by_time(fake, 3, {}) for n in part)
                  == sorted(fake), ''))
    cases.append(('the job count is a constant, not the machine\'s cores',
                  AS_CI_JOBS == 4, str(AS_CI_JOBS)))
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-times-'))
    try:
        _write_check_times({'check_a': 12.34, 'check_b': 1.0}, 'test', tmp / 't.json')
        got = _check_times(tmp / 't.json')
        cases.append(('a written record reads back', got[0] == {'check_a': 12.3,
                      'check_b': 1.0} and got[1] is not None, str(got)))
        cases.append(('an unreadable record deals by name',
                      _check_times(tmp / 'missing.json') == ({}, None), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rec = _check_times()[0]
    stale = sorted(set(rec) - set(names))
    cases.append(('the committed record names only checks that exist',
                  not stale, f'stale: {stale[:3]} (python3 tools/verify_harness.py '
                             f'--record-new-times drops them, in seconds)'))
    failed = [(n, d) for n, ok, d in cases if not ok]
    check(f'--as-ci parts partition the suite ({len(cases)} stated cases)',
          not failed, '; '.join(f'{n}: {d}' for n, d in failed))


def check_as_ci_says_why_a_shard_failed():
    """`--as-ci` prints, for a failed shard, its FAIL: lines and the tail of
    its stderr -- not just `SHARD FAILED (exit 1)`.

    WHY. Found 2026-09-28: a failed shard said only its exit status, so
    learning which case failed, or what traceback killed the shard, meant
    rerunning four minutes of suite by hand."""
    cases = []
    proc = subprocess.CompletedProcess(
        args=[], returncode=1,
        stdout='PASS: a\nFAIL: the broken case -- why it broke\nPASS: b\n',
        stderr='\n'.join(f'noise {i}' for i in range(30)) + '\nTraceback: boom\n')
    out = '\n'.join(_shard_failure_detail(proc))
    cases.append(('the failing case is named', 'FAIL: the broken case -- why it broke' in out))
    cases.append(('the end of stderr is shown', 'Traceback: boom' in out and 'noise 29' in out))
    lines = out.splitlines()
    cases.append(('only the last 20 lines of stderr',
                  '    noise 10' not in lines and '    noise 11' in lines))
    multi = subprocess.CompletedProcess(
        args=[], returncode=1, stderr='',
        stdout=('PASS: a\nFAIL: the long one -- first line\n'
                'the cause, on line two\nand line three\nPASS: b\n'
                'FAIL: the huge one\n' + '\n'.join(f'row {i}' for i in range(100))
                + '\nN/A:  c -- skipped\n'))
    out = '\n'.join(_shard_failure_detail(multi))
    cases.append(("a multi-line failure keeps every line of its text, and "
                  "nothing of the next verdict's",
                  'the cause, on line two' in out and 'and line three' in out
                  and 'PASS: b' not in out))
    cases.append(('a very long one is cut at 40 lines, and says so',
                  'row 38' in out and 'row 39' not in out
                  and 'cut at 40 lines' in out and 'N/A:' not in out))
    empty = subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr='')
    cases.append(('a shard that said nothing is said to have said nothing',
                  'no FAIL: line' in '\n'.join(_shard_failure_detail(empty))))
    failed = [n for n, ok in cases if not ok]
    check(f'--as-ci names why a shard failed ({len(cases)} stated cases)',
          not failed, '; '.join(failed))




def check_a_check_leaves_no_foreign_engine_module_behind():
    """After every check the harness forgets any engine module the check
    left loaded from outside this repository's tools/, and any import path
    it added outside this repository (_drop_foreign_engine_modules, run by
    the wrapper every check goes through).

    2026-10-31: a landing's background run died on check_repo_reference_
    allowlist, "module 'leak_gate' has no attribute '_ref_key'", because an
    earlier check had run a practice set's ladder tools in this process and
    they left the set's older vendored leak_gate in sys.modules. The fixture
    plants a foreign tools/ holding its own leak_gate, imports it the way
    those tools did, and calls the cleanup.

    Negative control: before the cleanup the foreign module is what an
    import of leak_gate returns -- the state the red run was in."""
    import tempfile
    name = 'a check leaves no foreign engine module behind for the next one'
    cases = []
    saved = sys.modules.get('leak_gate')
    with tempfile.TemporaryDirectory() as td:
        foreign = pathlib.Path(td) / 'tools'
        foreign.mkdir()
        (foreign / 'leak_gate.py').write_text('WHO = "a foreign copy"\n', encoding='utf-8')
        path_before = list(sys.path)
        sys.modules.pop('leak_gate', None)
        sys.path.insert(0, str(foreign))
        import importlib
        planted = importlib.import_module('leak_gate')
        cases.append(('NEGATIVE CONTROL: the foreign copy is what an import returns '
                      'before the cleanup', getattr(planted, 'WHO', None) == 'a foreign copy'))
        dropped = _drop_foreign_engine_modules(path_before)
        cases.append(('the cleanup forgets it, by name',
                      'leak_gate' in dropped and 'leak_gate' not in sys.modules))
        cases.append(('...and takes the foreign tools/ off the import path',
                      str(foreign) not in sys.path))
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            again = importlib.import_module('leak_gate')
        finally:
            sys.path.remove(str(ROOT / 'tools'))
        cases.append(("the next import is this repository's own",
                      pathlib.Path(again.__file__).resolve().parent
                      == (ROOT / 'tools').resolve()))
        kept = _drop_foreign_engine_modules(list(sys.path))
        cases.append(("this repository's own module is kept",
                      'leak_gate' not in kept and 'leak_gate' in sys.modules))
    if saved is not None:
        sys.modules['leak_gate'] = saved
    bad = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))
