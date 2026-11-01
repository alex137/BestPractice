# The harness tests for the push check
#
# tools/harness/vh_push_check.py -- part of the verification harness:
# the push check, test reach, test review and load budgets.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_worktree_snapshot_needs_no_git_identity():
    """_ref_including_worktree() snapshots a dirty tree with no git identity
    anywhere -- empty $HOME, no global or system config -- the shape of the
    isolated --as-ci run and of GitHub's runner (2026-09-30: a full check
    failed with "Author identity unknown" and named no test)."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='snapshot-identity-'))
    saved = {k: os.environ.get(k) for k in ('HOME', 'GIT_CONFIG_NOSYSTEM',
                                              'GIT_CONFIG_GLOBAL', 'GIT_AUTHOR_NAME',
                                              'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME',
                                              'GIT_COMMITTER_EMAIL', 'EMAIL')}
    try:
        repo = tmp / 'r'
        repo.mkdir()
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        subprocess.run(['git', 'init', '-q', str(repo)], env=env)
        (repo / 'a.txt').write_text('one\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c',
                        'user.email=t@t', 'commit', '-qm', 'base'], env=env)
        (repo / 'b.txt').write_text('new\n', encoding='utf-8')
        os.environ.update(HOME=str(tmp / 'empty-home'), GIT_CONFIG_NOSYSTEM='1',
                          GIT_CONFIG_GLOBAL=empty_gitconfig())
        for k in ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME',
                  'GIT_COMMITTER_EMAIL', 'EMAIL'):
            os.environ.pop(k, None)
        try:
            ref = _ref_including_worktree(repo)
            ok, det = True, ref
        except SystemExit as e:
            ok, det = False, str(e)
        cases.append(('a dirty tree is snapshotted with no identity configured',
                      ok, failure_detail(det, 200)))
        if ok:
            listed = subprocess.run(['git', '-C', str(repo), 'ls-tree', '--name-only',
                                     ref], capture_output=True, text=True).stdout.split()
            cases.append(('...and the snapshot holds the new file',
                          'b.txt' in listed, str(listed)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    # ...and when a shard does fail, the push check's report names it.
    import precedent_push_check as ppc
    out = ['  SHARD FAILED (exit 1)', '  last 20 line(s) of its stderr:',
           '      SKIP (filtered out by PRECEDENT_CHECK_ONLY/SKIP): check_x',
           '    verify_harness FAIL: could not create a scratch commit: why',
           '    *** Please tell me who you are.']
    found = ppc._finding_lines(out)
    cases.append(('the push check\'s report picks a failed shard and its reason',
                  out[0] in found and out[3] in found and out[2] not in found,
                  str(found), ))
    # A shard that died before any verdict names its traceback instead.
    out = ['  SHARD FAILED (exit 1)', '  last 3 line(s) of its stderr:',
           '    SKIP (filtered out by PRECEDENT_CHECK_ONLY/SKIP): check_x',
           '    Traceback (most recent call last):',
           '    KeyError: \'shard_probe\'',
           '=== here, the not-applicable slice ===',
           '  unrelated tail line']
    found = ppc._finding_lines(out)
    cases.append(('...and a shard with no FAIL: line is reported by its stderr',
                  out[4] in found and out[3] in found and out[2] not in found
                  and out[6] not in found,
                  str(found), ))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the working-tree snapshot needs no git identity ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_received_hooks_and_moved_engine_files():
    """A consumer's vendored hooks count as received, and a mirrored engine
    file that lives on in its own tools/ is moved, not gone (2026-09-30).

    Found in a real consumer after an Update Vendors that crossed the
    catalogue copy leaving tools/ out: the push check's rename-updates-links
    asked it to repoint `process/upstream/tools/precedent_push_check.py` in
    two vendored hooks (which the next refresh overwrites) and in its own
    tools/bootstrap.sh (template text naming a guarded fallback). Nothing
    caught it upstream because received_owners() was only ever tested on
    tools/ files, and rename-updates-links only on this repo's own layout.

    A throwaway consumer, run through precedent_check.py itself. CONTROL: a
    README naming a mirrored tool that has NO copy in tools/ is still
    reported, so the quiet cases come from the fix, not a blind check."""
    import tempfile
    import precedent_practice_refs as ppr
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='received-hooks-'))
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        for f in (ROOT / 'tools').glob('*.py'):
            shutil.copy(f, repo / 'tools' / f.name)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'kind': 'consumer', 'files': ['precedent_push_check.py'],
            'hook_files': ['push-check-gate.sh'],
            'engine_paths': {'bootstrap/commit-identity.sh': 'x'},
            'ci_workflow_files': ['.github/workflows/light-check.yml']}), encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'sources': {'precedent': {
            'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}}}),
            encoding='utf-8')
        up = repo / 'process' / 'upstream' / 'tools'
        up.mkdir(parents=True)
        (up.parent / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'rename-updates-links.md',
                    up.parent / 'practices' / 'rename-updates-links.md')
        (up / 'precedent_push_check.py').write_text('# mirrored\n', encoding='utf-8')
        (up / 'gone_tool.py').write_text('# mirrored, no copy in tools/\n', encoding='utf-8')
        fallback = ('for c in tools/precedent_push_check.py '
                    'process/upstream/tools/precedent_push_check.py; do :; done\n')
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / '.claude' / 'hooks' / 'push-check-gate.sh').write_text(fallback, encoding='utf-8')
        (repo / 'tools' / 'bootstrap.sh').write_text(fallback, encoding='utf-8')
        # ...but an unguarded call in a script of the repo's own is a step
        # that stops running (2026-10-01).
        (repo / 'tools' / 'steps.sh').write_text(
            'python3 process/upstream/tools/precedent_push_check.py\n', encoding='utf-8')
        (repo / 'README.md').write_text('See process/upstream/tools/gone_tool.py.\n',
                                        encoding='utf-8')
        # A command, not a fallback (2026-10-01, from a consumer's Update
        # Vendors): it fails "No such file" once the mirror is gone.
        (repo / 'AGENTS.md').write_text(
            'Before pushing, run `python3 process/upstream/tools/precedent_push_check.py`.\n',
            encoding='utf-8')
        (repo / '.claude' / 'settings.json').write_text(json.dumps({'permissions': {
            'allow': ['Bash(python3 process/upstream/tools/precedent_push_check.py:*)']}},
            indent=2) + '\n', encoding='utf-8')
        owners = ppr.received_owners(repo)
        cases.append(('a vendored hook is received',
                      ppr.received_owner('.claude/hooks/push-check-gate.sh', owners)
                      == 'the vendored engine', str(owners.get('.claude/hooks/push-check-gate.sh'))))
        cases.append(('a declared engine path is received',
                      ppr.received_owner('bootstrap/commit-identity.sh', owners) is not None, ''))
        cases.append(('a CI workflow is not, so ci-workflow-approved still judges it',
                      ppr.received_owner('.github/workflows/light-check.yml', owners) is None, ''))
        cases.append(('tools/bootstrap.sh stays the repo\'s own',
                      ppr.received_owner('tools/bootstrap.sh', owners) is None, ''))

        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        g('checkout', '-q', '-b', 'update-vendors')
        g('rm', '-rq', 'process/upstream/tools'); g('commit', '-qm', 'the hop')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'rename-updates-links'], cwd=str(repo), capture_output=True,
                           text=True, env=env, timeout=300)
        out = r.stdout + r.stderr
        cases.append(('the vendored hook\'s fallback is not a finding',
                      '.claude/hooks/push-check-gate.sh' not in out, failure_detail(out, 500)))
        cases.append(('nor is tools/bootstrap.sh\'s, since tools/ carries the file',
                      'tools/bootstrap.sh:' not in out, failure_detail(out, 500)))
        cases.append(('CONTROL: a mirrored tool with no copy in tools/ is still reported',
                      'README.md:1' in out and 'gone_tool.py' in out, failure_detail(out, 500)))
        cases.append(('an AGENTS.md command naming the moved file is reported, '
                      'with where it is now',
                      'AGENTS.md:1' in out and 'is at tools/precedent_push_check.py now'
                      in out, failure_detail(out, 800)))
        cases.append(('...and so is a .claude/settings.json allowlist entry',
                      '.claude/settings.json:' in out, failure_detail(out, 800)))
        cases.append(('...and an unguarded call in the repo\'s own shell script',
                      'tools/steps.sh:1' in out, failure_detail(out, 800)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'vendored hooks are received, and an engine file moved to tools/ '
          f'is not gone ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_very_deep_check_test_worth_judges_what_changed():
    """very_deep_check.py's TEST WORTH section (tools/test_review.py): every
    harness test and test script is listed with its recorded time; a test
    naming a retired thing carries that lead; a test with no verdict is
    new, a keep whose time more than doubled or that gained a lead comes
    back, a cheapen or retire is owed, and a verdict for a test that is gone
    is stale; a keep without its importance is a registry problem; and the
    write-up gets one `## Test review` block that a second write replaces.

    Added 2026-10-17 with the section (practice: very-deep-check, Pass 2's
    question 27; Morgan: "review all TESTS to see if all tests are relevant
    and important"). The repository is a temporary one the test builds
    (practice: fixture-owns-its-state); each case asserts the tool's own
    words or status (practice: control-asserts-which-failure)."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import test_review as tr
    import very_deep_check as vdc

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vdc-tests-'))
    try:
        (tmp / 'tools' / 'tests').mkdir(parents=True)
        (tmp / 'spec').mkdir()
        (tmp / 'tools' / 'verify_harness.py').write_text(
            'def check_quiet():\n    """Guards a thing still in use."""\n    return 1\n\n'
            'def check_grew():\n    """Got slow."""\n    return 2\n\n'
            'def check_old_tier():\n    """The tier."""\n    return "zz-gone-tier"\n\n'
            'def check_owed():\n    """To retire."""\n    return 3\n\n'
            'def helper():\n    return 4\n', encoding='utf-8')
        (tmp / 'tools' / 'harness_check_times.json').write_text(json.dumps({
            'measured': '2026-10-09, 4 cores, --as-ci', 'seconds': {
                'check_quiet': 0.4, 'check_grew': 9.0, 'check_old_tier': 2.0,
                'check_owed': 1.0}}), encoding='utf-8')
        (tmp / 'tools' / 'tests' / 'test_thing.sh').write_text(
            '#!/bin/sh\n# Two-direction test for the thing.\nexit 0\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(tmp)], check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], check=True)
        keep = {'verdict': 'keep', 'importance': 'medium', 'why': 'w',
                'date': '2026-10-17', 'by': 'agent'}
        (tmp / 'tools' / 'test_verdicts.json').write_text(json.dumps({
            'retired': [{'what': 'the zz tier', 'retired': '2026-10-14',
                         'patterns': [r'\bzz-gone-tier\b']}],
            'verdicts': {
                'check_quiet': dict(keep, seconds=0.4),
                'check_grew': dict(keep, seconds=2.0),
                'check_owed': {'verdict': 'retire', 'why': 'covered elsewhere',
                               'date': '2026-10-17', 'by': 'agent'},
                'check_gone': dict(keep, seconds=1.0),
                'tools/tests/test_thing.sh': {'verdict': 'keep', 'why': 'w',
                                              'date': '2026-10-17', 'by': 'agent'}}}),
            encoding='utf-8')
        r = tr.review(tmp)
        by = {t['name']: t for t in r['tests']}
        cases.append(('every check_* and every test script is listed, a helper is not',
                      sorted(by) == ['check_grew', 'check_old_tier', 'check_owed',
                                     'check_quiet', 'tools/tests/test_thing.sh'],
                      repr(sorted(by))))
        cases.append(('a harness test carries its recorded time; a script is untimed',
                      by['check_grew']['seconds'] == 9.0
                      and by['tools/tests/test_thing.sh']['seconds'] is None, ''))
        cases.append(('a test naming a retired thing carries that lead and is judged first',
                      by['check_old_tier']['leads'] == ['names the zz tier (retired 2026-10-14)']
                      and tr.to_judge(r)[0]['name'] == 'check_old_tier',
                      repr(by['check_old_tier']['leads'])))
        cases.append(('a test with no verdict is unjudged',
                      by['check_old_tier']['status'] == 'unjudged', ''))
        cases.append(('a keep whose time more than doubled is judged again, saying so',
                      by['check_grew']['status'] == 'rejudge'
                      and 'more than doubled' in ' '.join(by['check_grew']['why_rejudge']),
                      repr(by['check_grew'])))
        cases.append(('a current keep stays judged (the quiet half)',
                      by['check_quiet']['status'] == 'judged', ''))
        cases.append(('a retire verdict on a test still there is owed',
                      by['check_owed']['status'] == 'owed', ''))
        cases.append(('a verdict for a test that is gone is stale',
                      r['stale'] == ['check_gone'], repr(r['stale'])))
        # A practice set keeps no retired list of its own: its tests are
        # read against the list of the repo running the check (2026-10-18).
        aset = tmp / 'aset'
        (aset / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        (aset / 'tools' / 'checks' / 'tests' / 'test_old.sh').write_text(
            '#!/bin/sh\n# Uses the old tier.\necho zz-gone-tier\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(aset)], check=True)
        subprocess.run(['git', '-C', str(aset), 'add', '-A'], check=True)
        alone = {t['name']: t['leads'] for t in tr.review(aset)['tests']}
        joined = {t['name']: t['leads'] for t in tr.review(aset, also=(tmp,))['tests']}
        cases.append(('a set\'s test is read against the running repo\'s retired '
                      'list, and only when that repo is named',
                      alone.get('tools/checks/tests/test_old.sh') == []
                      and joined.get('tools/checks/tests/test_old.sh')
                      == ['names the zz tier (retired 2026-10-14)'],
                      repr(alone) + ' / ' + repr(joined)))
        shutil.rmtree(aset, ignore_errors=True)
        cases.append(('a keep without its importance is a registry problem, '
                      'and the test stays unjudged',
                      any('tools/tests/test_thing.sh' in p and 'importance' in p
                          for p in r['problems'])
                      and by['tools/tests/test_thing.sh']['status'] == 'unjudged',
                      repr(r['problems'])))
        text = tr.render_text(r)
        cases.append(('the text counts what is judged and what is to judge, '
                      'and says when the times were measured',
                      'Judged 1; to judge: 2 never judged, 1 to judge again, 1 '
                      'cheapen/retire owed.' in text
                      and 'Times measured 2026-10-09, 4 cores' in text, text))
        md = tr.render_markdown([('fixture', r)])
        cases.append(('the block gives time by importance and the slowest against it',
                      '| medium | 2 | 9 |' in md and '| `check_grew` | 9.0 | keep | medium |' in md,
                      md))
        doc = tmp / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        doc.write_text('# Run\n\nBody.\n', encoding='utf-8')
        # Times from an earlier day are said to be stale before judging;
        # today's are not (2026-10-17: a list said 777 s for a test that
        # took 266 s that day).
        stale_out = io.StringIO()
        with contextlib.redirect_stdout(stale_out):
            vdc.test_worth_section([('fixture', tmp)], tmp)
        times_f = tmp / 'tools' / 'harness_check_times.json'
        rec = json.loads(times_f.read_text(encoding='utf-8'))
        rec['measured'] = f'{vdc.precedent_time.today(tmp)}, 4 cores, --as-ci'
        times_f.write_text(json.dumps(rec), encoding='utf-8')
        fresh_out = io.StringIO()
        with contextlib.redirect_stdout(fresh_out):
            vdc.test_worth_section([('fixture', tmp)], tmp)
        cases.append(('times from an earlier day are flagged before judging, '
                      'today\'s are not',
                      "TIMES ARE NOT TODAY'S (measured 2026-10-09" in stale_out.getvalue()
                      and 'TIMES ARE NOT TODAY' not in fresh_out.getvalue(),
                      failure_detail(stale_out.getvalue(), 600) + ' || ' + failure_detail(fresh_out.getvalue(), 300)))
        with contextlib.redirect_stdout(io.StringIO()):
            (tmp / 'tools' / 'tests' / 'test_thing.sh').unlink()
            vdc.test_worth_section([('fixture', tmp)], tmp)
        body = doc.read_text(encoding='utf-8')
        cases.append(('the write-up gets one ## Test review block, replaced on the second write',
                      body.count('## Test review') == 1 and body.startswith('# Run\n\nBody.\n')
                      and '4 test(s)' in body and '5 test(s)' not in body, body))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'very_deep_check.py\'s TEST WORTH lists every test and judges what changed '
          f'({len(cases)} stated cases: inventory, time, leads, new, again, owed, '
          f'stale, malformed, times\' age, a set read against the running repo, '
          f'write-up block)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))


def check_test_review_times_script_tests():
    """`test_review.py --time-scripts` runs each test script once and records
    what each that passed took in the repo's tools/script_test_times.json,
    and inventory() then reports those seconds. Controls: before the file
    exists every script is untimed, as it was; a failing script is named,
    left out of the file and stays untimed; and the run exits 1 for it.

    Added 2026-10-31 (Morgan, strength: decided: "Yes do the test review and
    redo the incident verdicts"): inventory() gave every script None, so a
    practice set's totals said "0 timed" and the rule that judges a keep
    again when its time more than doubled could never fire for a script.
    The repository is a temporary one built here (practice:
    fixture-owns-its-state)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import test_review as tr

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-script-times-'))
    try:
        tests = tmp / 'tools' / 'checks' / 'tests'
        tests.mkdir(parents=True)
        (tests / 'test_slow.sh').write_text(
            '#!/bin/sh\n# Takes a measurable moment.\nsleep 0.3\nexit 0\n', encoding='utf-8')
        (tests / 'test_quick.py').write_text(
            '"""Passes at once."""\nimport sys\nsys.exit(0)\n', encoding='utf-8')
        (tests / 'test_broken.sh').write_text(
            '#!/bin/sh\n# Fails.\necho "FAIL: the planted failure"\nexit 1\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(tmp)], check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], check=True)
        slow, quick, broken = (f'tools/checks/tests/{n}' for n in
                               ('test_slow.sh', 'test_quick.py', 'test_broken.sh'))

        before = {t['name']: t['seconds'] for t in tr.inventory(tmp)}
        cases.append(('CONTROL: with no times file every script is untimed, as before',
                      before == {slow: None, quick: None, broken: None}, repr(before)))
        run = subprocess.run([sys.executable, str(ROOT / 'tools' / 'test_review.py'),
                              '--time-scripts', '--repo', str(tmp)],
                             capture_output=True, text=True, timeout=120)
        out = run.stdout + run.stderr
        cases.append(('the run exits 1 and names the failing script as not recorded',
                      run.returncode == 1
                      and f'FAILED' in out and f'{broken} (exit 1; not recorded)' in out
                      and '2 of 3 script(s) timed' in out, failure_detail(out, 600)))
        try:
            rec = json.loads((tmp / 'tools' / 'script_test_times.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as e:
            rec = {'error': str(e)}
        cases.append(('THE CASE: both passing scripts are recorded, the failing one is not',
                      sorted((rec.get('seconds') or {})) == sorted([slow, quick])
                      and 'cores' in str(rec.get('measured')) and rec.get('_comment'),
                      repr(rec)))
        after = {t['name']: t['seconds'] for t in tr.inventory(tmp)}
        cases.append(('THE CASE: inventory() reports the recorded seconds; the '
                      'failing script stays untimed',
                      isinstance(after.get(slow), float) and after[slow] >= 0.3
                      and isinstance(after.get(quick), float) and after.get(broken) is None,
                      repr(after)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'test_review.py --time-scripts records what each passing test script '
          f'took and inventory() reads it ({len(cases)} stated cases: untimed '
          f'before, failing one named, recorded, read back)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))


def check_full_run_asks_first():
    """A full run started by hand states its cost and refuses without
    --because; a filtered run, a run with a go-ahead, a caller that was
    asked, and GitHub's runner start; a recorded time is quoted back."""
    import tempfile
    cases = []
    r = _full_run_refusal([], {})
    cases.append(('a bare run by hand is refused', r is not None))
    cases.append(('...and the refusal states a time in minutes',
                  bool(r and re.search(r'\d+ minutes', r))))
    cases.append(('...and says how to give the go-ahead',
                  bool(r and '--because' in r)))
    cases.append(('--as-ci by hand is refused too',
                  _full_run_refusal(['--as-ci'], {}) is not None))
    cases.append(('--all by hand is refused too',
                  _full_run_refusal(['--all'], {}) is not None))
    cases.append(('--because with words starts it',
                  _full_run_refusal(['--because', 'Morgan: run it'], {}) is None))
    cases.append(('--because with no words does not',
                  _full_run_refusal(['--because'], {}) is not None))
    cases.append(('a filtered run starts',
                  _full_run_refusal([], {'PRECEDENT_CHECK_ONLY': 'check_x'}) is None))
    cases.append(('a shard (SKIP) starts',
                  _full_run_refusal([], {'PRECEDENT_CHECK_SKIP': 'check_x'}) is None))
    cases.append(('a caller that was asked starts',
                  _full_run_refusal(['--as-ci'], {HARNESS_ASKED_ENV: 'push check'}) is None))
    cases.append(("GitHub's runner starts",
                  _full_run_refusal([], {'GITHUB_ACTIONS': 'true'}) is None))
    with tempfile.TemporaryDirectory() as tmp:
        f = pathlib.Path(tmp) / 'timings.json'
        _record_full_run('--as-ci', 9 * 60 + 10, 0, f)
        cases.append(('a recorded run is quoted back',
                      '9 minutes the last time on this machine'
                      in _full_run_cost('--as-ci', f)))
        _record_full_run('--as-ci', 60, 2, f)
        cases.append(('a run that crashed records nothing',
                      '9 minutes' in _full_run_cost('--as-ci', f)))
    src = pathlib.Path(__file__).read_text(encoding='utf-8')
    pc = (ROOT / 'tools' / 'precedent_push_check.py').read_text(encoding='utf-8')
    vd = (ROOT / 'tools' / 'very_deep_check.py').read_text(encoding='utf-8')
    cases.append(('the entry point refuses before anything runs',
                  'refusal = _full_run_refusal(sys.argv[1:], os.environ)' in src))
    cases.append(('the push check passes its own reason',
                  "'--isolated', '--because'" in pc))
    cases.append(("the very deep check's step 2 passes its own reason",
                  "str(harness), '--all',\n" in vd
                  and "'--record-times', '--because'," in vd))
    failed = [n for n, ok in cases if not ok]
    check(f'a full run started by hand states its cost and asks first '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_harness_reach_selects_what_a_change_reaches():
    """A scoped run picks exactly the checks a change can reach
    (tools/harness_reach.py), and the recorder sees what a child reads.

    WHY (2026-10-12). GitHub ran all 677 checks, twice, for a change to
    three engine files that about 83 of them exercise; Alex asked for
    checks limited to the changes actually made. A scoped run is only as
    good as its selection: one that quietly picks too few looks exactly
    like a green suite. So every rule the selection rests on is planted
    here, the ones that must pick a check and the ones that must not."""
    import tempfile
    spec = importlib.util.spec_from_file_location(
        '_harness_reach_t', ROOT / 'tools' / 'harness_reach.py')
    hr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hr)
    cases = []
    base_src = ('X = 1\n\ndef f():\n    return 1\n\ndef g():\n    return 2\n\n'
                'def outer():\n    def inner():\n        return 3\n    return inner\n')
    cases.append(('a comment or a blank line reaches no code unit',
                  hr.changed_units(base_src, base_src.replace('def g', '# note\n\ndef g'))
                  == set()))
    cases.append(('a changed body reaches only its own def',
                  hr.changed_units(base_src, base_src.replace('return 1', 'return 9'))
                  == {'f'}))
    cases.append(('a changed constant reaches the module\'s top level',
                  hr.changed_units(base_src, base_src.replace('X = 1', 'X = 2'))
                  == {'<module>'}))
    cases.append(('a new def is a unit of its own and leaves the top level alone',
                  hr.changed_units(base_src, base_src + '\ndef h():\n    return 5\n')
                  == {'h'}))
    cases.append(('a changed nested def reaches it and the def around it',
                  hr.changed_units(base_src, base_src.replace('return 3', 'return 4'))
                  == {'outer', 'outer.inner'}))
    cases.append(('a file that does not parse reaches everything in it',
                  hr.changed_units(base_src, 'def (') is None))
    cases.append(('code objects map to their def',
                  [hr.unit_of(q) for q in ('a.<locals>.<lambda>', '<module>',
                                           'C.m', 'a.<locals>.b.<locals>.<genexpr>',
                                           '<lambda>')]
                  == ['a', '<module>', 'C.m', 'a.b', '<module>']))

    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'r'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'practices').mkdir()

        def git(*a):
            subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                           check=True, env={**os.environ, 'GIT_AUTHOR_NAME': 't',
                                            'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
                                            'GIT_COMMITTER_EMAIL': 't@t'})
        (repo / 'tools' / 'm.py').write_text(base_src, encoding='utf-8')
        (repo / 'data.json').write_text('{}\n', encoding='utf-8')
        (repo / 'practices' / 'a.md').write_text('a\n', encoding='utf-8')
        git('init', '-q')
        git('add', '-A')
        git('commit', '-q', '-m', 'base')
        base = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        ledger = {'version': hr.VERSION, 'commit': base, 'checks': {
            'check_runs_f': {'c': {'tools/m.py': ['f']}},
            'check_runs_g': {'c': {'tools/m.py': ['g']}},
            'check_reads_data': {'f': ['data.json']},
            'check_lists_practices': {'d': ['practices']},
            'check_tests_a_path': {'x': ['missing.txt']},
            'check_unseen': {'o': ['git run against the repository itself']},
        }}
        names = set(ledger['checks']) | {'check_new'}

        def picked():
            sel, _why, full = hr.select(ledger, base, None, names, root=repo)
            return full or sorted(sel)
        always = ['check_new', 'check_unseen']
        cases.append(('no change: only the new check and the unseen one run',
                      picked() == always, picked()))
        (repo / 'tools' / 'm.py').write_text(base_src.replace('return 1', 'return 9'),
                                             encoding='utf-8')
        cases.append(('THE DISCRIMINATING CASE: a changed def picks the check that '
                      'ran it and not the one that ran its neighbour',
                      picked() == sorted(always + ['check_runs_f']), picked()))
        (repo / 'tools' / 'm.py').write_text(base_src.replace('def g', '# c\ndef g'),
                                             encoding='utf-8')
        cases.append(('a comment-only change picks nothing more',
                      picked() == always, picked()))
        (repo / 'tools' / 'm.py').write_text(base_src.replace('X = 1', 'X = 2'),
                                             encoding='utf-8')
        cases.append(('a changed top level picks every check that ran the file',
                      picked() == sorted(always + ['check_runs_f', 'check_runs_g']),
                      picked()))
        (repo / 'tools' / 'm.py').write_text(base_src, encoding='utf-8')
        (repo / 'data.json').write_text('{"a": 1}\n', encoding='utf-8')
        cases.append(('a changed data file picks the check that read it',
                      picked() == sorted(always + ['check_reads_data']), picked()))
        (repo / 'data.json').write_text('{}\n', encoding='utf-8')
        (repo / 'practices' / 'b.md').write_text('b\n', encoding='utf-8')
        cases.append(('a new file picks the check that listed its directory',
                      picked() == sorted(always + ['check_lists_practices']), picked()))
        (repo / 'practices' / 'b.md').unlink()
        (repo / 'missing.txt').write_text('now here\n', encoding='utf-8')
        cases.append(('a file appearing where a check tested for it picks that check',
                      picked() == sorted(always + ['check_tests_a_path']), picked()))
        (repo / 'missing.txt').unlink()
        (repo / 'tools' / 'harness_reach.py').write_text('# changed\n', encoding='utf-8')
        cases.append(('a change to the selection machinery runs the whole suite',
                      isinstance(picked(), str) and 'machinery' in picked(), picked()))
        (repo / 'tools' / 'harness_reach.py').unlink()
        cases.append(('a ledger from another format runs the whole suite',
                      hr.select({'version': -1}, base, None, names, root=repo)[2]
                      == 'no usable ledger'))

        # The recorder, end to end, in a child: the code it ran and the
        # file it read, against the check named in its environment.
        (repo / 'tools' / 'reader.py').write_text(
            'import json, pathlib\n\ndef read():\n'
            '    return json.loads((pathlib.Path(__file__).parents[1] / "data.json").read_text())\n',
            encoding='utf-8')
        out = pathlib.Path(td) / 'rec'
        out.mkdir()
        env = hr.record_env(out, root=repo)
        env['HARNESS_REACH_CHECK'] = 'check_planted'
        subprocess.run([sys.executable, '-c',
                        'import sys; sys.path.insert(0, sys.argv[1]); '
                        'import reader; reader.read()', str(repo / 'tools')],
                       env=env, capture_output=True, text=True, timeout=120)
        rec = hr.merge(out, base)['checks'].get('check_planted', {})
        cases.append(('a child\'s run code is recorded against its check, by def',
                      'read' in rec.get('c', {}).get('tools/reader.py', ()), rec))
        cases.append(('...and the file it read',
                      'data.json' in rec.get('f', ()), rec))
        cases.append(('...and nothing it could not see', not rec.get('o'), rec))
        # A copy is not a read; reading the copy is a read of the original.
        for label, code, want in (
                ('a file only copied out of the repository is not read',
                 'import shutil, sys; shutil.copy(sys.argv[1] + "/data.json", sys.argv[2] + "/c.json")',
                 False),
                ('...and reading the copy reads the original',
                 'import shutil, sys; shutil.copy(sys.argv[1] + "/data.json", sys.argv[2] + "/c.json"); '
                 'open(sys.argv[2] + "/c.json").read()', True)):
            outc = pathlib.Path(td) / f'recc{int(want)}'
            outc.mkdir()
            scratch = pathlib.Path(td) / f'scratch{int(want)}'
            scratch.mkdir()
            env = hr.record_env(outc, root=repo)
            env['HARNESS_REACH_CHECK'] = 'check_planted'
            subprocess.run([sys.executable, '-c', code, str(repo), str(scratch)],
                           env=env, capture_output=True, text=True, timeout=120)
            rec = hr.merge(outc, base)['checks'].get('check_planted', {})
            cases.append((label, ('data.json' in rec.get('f', ())) == want, rec))
        # A copy made by reading and writing the bytes, as the engine's own
        # vendoring does, is no read either -- and a copy another process
        # made is known by its bytes. Big enough that identical bytes mean
        # something (harness_reach_hook._SMALLEST).
        big = '{"k": "' + 'x' * 200 + '"}\n'
        (repo / 'big.json').write_text(big, encoding='utf-8')
        (repo / 'tools' / 'run_me.py').write_text(
            'def go():\n    return ' + repr('y' * 200) + '\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'big')
        copy_rw = ('import pathlib, sys; r, s = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); '
                   '(s / "b.json").write_bytes((r / "big.json").read_bytes()); '
                   '(s / "run_me.py").write_bytes((r / "tools" / "run_me.py").read_bytes())')
        for label, codes, want_f, want_c in (
                ('a file copied by reading and writing its bytes is not read', [copy_rw], False, False),
                ('...a changed copy is still a read of the original',
                 ['import pathlib, sys; r, s = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); '
                  '(s / "b.json").write_text((r / "big.json").read_text() + "more")'], True, False),
                ('...and a copy one process made, read and run by another, is the original',
                 [copy_rw, 'import sys; sys.path.insert(0, sys.argv[2]); '
                  'open(sys.argv[2] + "/b.json").read(); import run_me; run_me.go()'], True, True)):
            outc = pathlib.Path(td) / f'recrw{len(cases)}'
            outc.mkdir()
            scratch = pathlib.Path(td) / f'scratchrw{len(cases)}'
            scratch.mkdir()
            env = hr.record_env(outc, root=repo)
            env['HARNESS_REACH_CHECK'] = 'check_planted'
            for code in codes:
                subprocess.run([sys.executable, '-c', code, str(repo), str(scratch)],
                               env=env, capture_output=True, text=True, timeout=120)
            rec = hr.merge(outc, base)['checks'].get('check_planted', {})
            got_f = 'big.json' in rec.get('f', ())
            got_c = 'go' in rec.get('c', {}).get('tools/run_me.py', ())
            cases.append((label, got_f == want_f and got_c == want_c, rec))
        # A cached reader's first run is kept against it, and a later check
        # that calls it inherits what that run read.
        outk = pathlib.Path(td) / 'reck'
        outk.mkdir()
        (outk / 'parent-1.json').write_text(json.dumps({
            'checks': {'check_first': {'c': [['tools/m.py', 'f']], 'f': ['data.json']},
                       'check_later': {'c': [['tools/m.py', 'f']]},
                       'check_other': {'c': [['tools/m.py', 'g']]}},
            'imports': {'tools/m.py::f': {'f': ['data.json']}}}), encoding='utf-8')
        merged = hr.merge(outk, base)['checks']
        cases.append(('a later caller of a cached reader inherits what its first run read, '
                      'and a check that never called it does not',
                      'data.json' in merged['check_later'].get('f', ())
                      and 'data.json' not in merged['check_other'].get('f', ()), merged))
        out2 = pathlib.Path(td) / 'rec2'
        out2.mkdir()
        env = hr.record_env(out2, root=repo)
        env['HARNESS_REACH_CHECK'] = 'check_planted'
        subprocess.run([sys.executable, '-c',
                        'import subprocess, sys; subprocess.run(["git", "-C", sys.argv[1], '
                        '"log", "-1"], capture_output=True)', str(repo)],
                       env=env, capture_output=True, text=True, timeout=120)
        rec = hr.merge(out2, base)['checks'].get('check_planted', {})
        cases.append(('git run against the repository itself is recorded as unseen, '
                      'so that check always runs', any('git' in o for o in rec.get('o', ())),
                      rec))
    bad = [f'{c[0]}{": " + repr(c[2])[:300] if len(c) > 2 else ""}'
           for c in cases if not c[1]]
    check(f'a scoped run picks the checks a change reaches ({len(cases)} stated cases)',
          not bad, '; '.join(bad)[:3000])

def _already_tested_step(text):
    """-> the `run:` script of the step with `id: already` in a workflow's
    text, dedented, or '' when there is none. Read by line, not by PyYAML:
    GitHub's runner has none (see workflow_triggers_text)."""
    lines = text.splitlines()
    try:
        at = lines.index('        id: already')
    except ValueError:
        return ''
    try:
        start = lines.index('        run: |', at) + 1
    except ValueError:
        return ''
    body = []
    for line in lines[start:]:
        if line.strip() and not line.startswith(' ' * 10):
            break
        body.append(line[10:])
    return '\n'.join(body).rstrip() + '\n'


def check_push_to_main_skips_what_already_passed():
    """A push to main re-runs main's GitHub test only when its exact files
    have not already passed that same workflow -- and runs it whenever that
    is not certain.

    Morgan, 2026-09-27 (strength: decided): the second GitHub run of a
    Promote "should not run the second time ... if it had just run before,
    and nothing had changed". The decision is a shell step shipped twice --
    this repo's deep-check.yml and the consumer light-check template -- so
    the two copies must be the same text, and the text is run here against
    a real git history with a stand-in for GitHub's API.

    THE NEGATIVE CASES ARE THE POINT. A skip that fires wrongly is a gate
    that silently stops gating, so each skip is paired with the same shape
    where it must run: main moved under the pull request, nothing passed
    yet, the API unreachable, and identical files that reached main by
    another route (the other parent is not inside the tested commit).
    Owns its state (practice: fixture-owns-its-state)."""
    import tempfile
    cases = []
    wf = (ROOT / '.github' / 'workflows' / 'deep-check.yml')
    tpl = ROOT / 'templates' / 'github-actions' / 'light-check.yml.template'
    s_wf = _already_tested_step(wf.read_text(encoding='utf-8')) if wf.is_file() else ''
    s_tpl = _already_tested_step(tpl.read_text(encoding='utf-8'))
    cases.append(('the consumer template carries the skip step', bool(s_tpl.strip()), ''))
    if wf.is_file():
        cases.append(('deep-check.yml carries the same skip step, word for word',
                      s_wf == s_tpl, ''))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-already-tested-'))
    try:
        repo = tmp / 'repo'
        env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='h@example.com',
                   GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='h@example.com',
                   HOME=str(tmp))

        def git(*a):
            r = subprocess.run(['git', *a], cwd=str(repo), env=env,
                               capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stderr)
            return r.stdout.strip()

        def commit(name, body='x\n', msg=None):
            (repo / name).write_text(body, encoding='utf-8')
            git('add', '-A')
            git('commit', '-qm', msg or name)
            return git('rev-parse', 'HEAD')

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env, check=True)
        commit('a')
        # 1. The ordinary Promote merge: the head already contains main.
        git('checkout', '-qb', 'h1')
        h1 = commit('b')
        git('checkout', '-q', 'main')
        git('merge', '-q', '--no-ff', '-m', 'm1', 'h1')
        m1 = git('rev-parse', 'HEAD')
        # 2. Main moved under the pull request: the merge lands files the
        #    head never had.
        base = m1
        commit('c')
        git('checkout', '-qb', 'h2', base)
        h2 = commit('d')
        git('checkout', '-q', 'main')
        git('merge', '-q', '--no-ff', '-m', 'm2', 'h2')
        m2 = git('rev-parse', 'HEAD')
        # 3. Identical files by another route: main added `e`, the head added
        #    the same `e` on its own. Same tree, but main's commit is not
        #    inside the head, so the head's run never saw main's history.
        base = m2
        commit('e', 'same\n')
        git('checkout', '-qb', 'h3', base)
        # Its own message, or git would make it the very commit main has
        # (same parent, tree, author and second) and the case would test
        # nothing.
        commit('e', 'same\n', msg='e, added on the head')
        h3 = commit('f')
        git('checkout', '-q', 'main')
        git('merge', '-q', '--no-ff', '-m', 'm3', 'h3')
        m3 = git('rev-parse', 'HEAD')
        same_tree = (git('rev-parse', f'{m3}^{{tree}}') == git('rev-parse', f'{h3}^{{tree}}')
                     and subprocess.run(['git', 'merge-base', '--is-ancestor', 'main^1', h3],
                                        cwd=str(repo), env=env).returncode != 0)
        # 4. A direct push: one parent, tested (or not) as itself.
        c4 = commit('g')

        fake = tmp / 'bin'
        fake.mkdir()
        passed = tmp / 'passed.txt'
        (fake / 'gh').write_text(
            '#!/bin/sh\n'
            '[ -n "${FAKE_GH_FAIL:-}" ] && exit 1\n'
            'case "$2" in\n'
            '  */actions/runs/*) echo 42 ;;\n'
            '  */actions/workflows/42/runs*)\n'
            '    sha=$(printf %s "$2" | sed \'s/.*head_sha=\\([0-9a-f]*\\).*/\\1/\')\n'
            '    case "$2" in\n'
            '      *status=success*)\n'
            '        if grep -qx "$sha" "$FAKE_GH_PASSED"; then echo 1; else echo 0; fi ;;\n'
            '      *) if grep -qx "$sha" "$FAKE_GH_RUNNING" 2>/dev/null; then echo 1; else echo 0; fi ;;\n'
            '    esac ;;\n'
            '  *) exit 1 ;;\n'
            'esac\n', encoding='utf-8')
        os.chmod(fake / 'gh', 0o755)
        script = tmp / 'step.sh'
        script.write_text(s_tpl, encoding='utf-8')

        running = tmp / 'running.txt'

        def decide(sha, passed_shas, fail=False, running_shas=()):
            passed.write_text(''.join(s + '\n' for s in passed_shas), encoding='utf-8')
            running.write_text(''.join(s + '\n' for s in running_shas), encoding='utf-8')
            out, summ = tmp / 'out', tmp / 'summary'
            out.write_text('')
            summ.write_text('')
            e = dict(env, PATH=f'{fake}:{env.get("PATH", "")}', GITHUB_SHA=sha,
                     GITHUB_REPOSITORY='o/r', GITHUB_RUN_ID='7',
                     GITHUB_OUTPUT=str(out), GITHUB_STEP_SUMMARY=str(summ),
                     FAKE_GH_PASSED=str(passed), FAKE_GH_RUNNING=str(running))
            if fail:
                e['FAKE_GH_FAIL'] = '1'
            r = subprocess.run(['bash', str(script)], cwd=str(repo), env=e,
                               capture_output=True, text=True)
            return r.returncode, out.read_text(), summ.read_text()

        rc, out, summ = decide(m1, [h1])
        cases.append(('a merge whose head already held main, head passed: skips, and says so',
                      rc == 0 and 'skip=true' in out and h1 in summ, out + summ))
        rc, out, _ = decide(m1, [])
        cases.append(('...the same merge with no passing run: runs', 'skip=false' in out, out))
        rc, out, _ = decide(m1, [h1], fail=True)
        cases.append(('...the same merge with the API unreachable: runs', 'skip=false' in out, out))
        rc, out, _ = decide(m2, [h2])
        cases.append(('main moved under the pull request, head passed: runs',
                      'skip=false' in out, out))
        cases.append(('the fixture really has identical files by another route', same_tree, ''))
        rc, out, _ = decide(m3, [h3])
        cases.append(('identical files, but main\'s commit is not inside the tested head: runs',
                      'skip=false' in out, out))
        rc, out, _ = decide(c4, [c4])
        cases.append(('a direct push of a commit that already passed: skips',
                      'skip=true' in out, out))
        rc, out, _ = decide(c4, [m3])
        cases.append(('a direct push of new files, its parent passed: runs',
                      'skip=false' in out, out))
        # 2026-10-12: a direct-route merge lands while its pull request's
        # own run of the same files is still going; main waits on that
        # run's verdict instead of starting a second one beside it.
        rc, out, summ = decide(m1, [], running_shas=[h1])
        cases.append(('THE DISCRIMINATING CASE: merged while the head\'s own run of the '
                      'same files is still going: defers to it, and says so',
                      'skip=true' in out and 'deferred=true' in out
                      and 'being tested' in summ, out + summ))
        rc, out, _ = decide(m1, [h1])
        cases.append(('...a head that already passed is not a deferral, so a '
                      'failure issue may close', 'deferred=false' in out, out))
        rc, out, _ = decide(m2, [], running_shas=[h2])
        cases.append(('main moved under the pull request, its run still going: runs '
                      '(that run tests other files)', 'skip=false' in out, out))
    except RuntimeError as e:
        cases.append(('the fixture builds', False, failure_detail(str(e), 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_consumer_basic_tier_runs_the_practice_audit():
    """A consumer's push to its landing branch runs the practice audit's two checks,
    scrub-gate and practice-export-loop (2026-10-02). A classic install
    migrated onto the loader carried stale manifest baselines and no scrub
    blocklist; both are practice_audit findings, which ran only inside the
    full sweep, so every Booked passed and the first Debut failed on both.
    They are range-judged like the other basic checks, so a finding already
    on a tier branch never blocks a working branch's push. CONTROL: the
    upstream kind is unchanged -- it has no process/ layer to audit."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-basic-audit-'))
    try:
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'consumer'}), encoding='utf-8')
        kind, checks = ppc.plan(tmp, tmp / 'tools', tier=ppc.BASIC)
        names = [n for n, _a, _r in checks]
        argvs = {n: a for n, a, _r in checks}
        cases.append(('a consumer\'s basic tier runs scrub-gate and '
                      'practice-export-loop',
                      kind == 'consumer' and 'scrub_gate' in names
                      and 'practice_export_loop' in names, repr(names)))
        cases.append(('...each through precedent_check --only, whose VIOLATION '
                      'lines the range judgement can compare',
                      argvs.get('scrub_gate', [])[-2:] == ['--only', 'scrub-gate']
                      and argvs.get('practice_export_loop', [])[-2:]
                      == ['--only', 'practice-export-loop'], repr(argvs)))
        cases.append(('...and both are range-judged',
                      {'scrub_gate', 'practice_export_loop'} <= ppc.RANGE_JUDGED,
                      repr(ppc.RANGE_JUDGED)))
        up = [n for n, _a, _r in ppc.PUSH_CHECKS['upstream']]
        cases.append(('CONTROL: the upstream kind does not run them',
                      'scrub_gate' not in up and 'practice_export_loop' not in up,
                      repr(up)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a consumer\'s landing push runs the practice audit '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_retiring_an_engine_tool_asks_what_it_left():
    """A change deleting a vendored engine file is refused until the
    decommission record says what the tool left in the repositories it ran
    in (Morgan, 2026-10-20: "When retiring an engine tool, ask what it left
    in other repositories ... please implement this one").

    1. Deleting a file the engine vendored at the base, with no answer:
       one problem, naming the file and the flag.
    2. NEGATIVE CONTROL: an answer of [] (it left nothing) clears it.
    3. NEGATIVE CONTROL: a deleted tools/ file the engine never vendored
       is not asked about.
    4. precedent_decommission records the answer on the tool's entry."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    import precedent_decommission as pd
    cases = []
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=env,
                              capture_output=True, text=True)
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'tools').mkdir()
        (d / 'process').mkdir()
        (d / 'tools' / 'precedent_vendor_engine.py').write_text(
            "KINDS = {'consumer': ['zz_marker_tool.py']}\n")
        (d / 'tools' / 'zz_marker_tool.py').write_text('print(1)\n')
        (d / 'tools' / 'zz_own_script.py').write_text('print(2)\n')
        (d / pd.REGISTRY).write_text(json.dumps({'decommissioned': []}))
        g(d, 'init', '-q', '-b', 'base')
        g(d, 'add', '-A')
        g(d, 'commit', '-qm', 'base')
        g(d, 'switch', '-q', '-c', 'work')
        g(d, 'rm', '-q', 'tools/zz_marker_tool.py', 'tools/zz_own_script.py')
        g(d, 'commit', '-qm', 'retire')
        got = ppc._retired_engine_files_unanswered(d, 'base')
        cases.append(('deleting a vendored engine file with no answer is one '
                      'problem naming it and the flag',
                      len(got) == 1 and got[0].startswith('tools/zz_marker_tool.py')
                      and '--left-in-consumers' in got[0], repr(got)))
        cases.append(('NEGATIVE CONTROL: a tools/ file the engine never '
                      'vendored is not asked about',
                      not any('zz_own_script' in x for x in got), repr(got)))
        (d / pd.REGISTRY).write_text(json.dumps({'decommissioned': [
            {'path': 'tools/zz_marker_tool.py', 'reason': 'r',
             'decommissioned_at': '2026-10-20', pd.LEFT_IN_CONSUMERS_KEY: []}]}))
        g(d, 'commit', '-qam', 'answer')
        got = ppc._retired_engine_files_unanswered(d, 'base')
        cases.append(('NEGATIVE CONTROL: "it left nothing" answers it',
                      got == [], repr(got)))
        (d / pd.REGISTRY).write_text(json.dumps({'decommissioned': []}))
        pd.record_decommissioned(d, ['tools/zz_marker_tool.py'], 'r',
                                 left=['tools/zz_mark.json'])
        e = json.loads((d / pd.REGISTRY).read_text())['decommissioned'][0]
        cases.append(('the decommission tool records what it left on the '
                      "tool's entry", e.get(pd.LEFT_IN_CONSUMERS_KEY)
                      == ['tools/zz_mark.json'], repr(e)))
    bad = [c for c in cases if not c[1]]
    return (not bad, '; '.join(f'{n}: {x}' for n, _ok, x in bad)
            or f'{len(cases)} cases')


def check_every_verdict_returning_check_is_recorded():
    """A verdict nobody reads is not a check.

    Most `check_*` functions here report by calling `check(name, ok, detail)`
    themselves and return nothing. A newer family instead ends in
    `return (not bad, detail, failure)` and is recorded by its CALL SITE --
    `check('...', *check_foo())`. Call one of those bare and it still runs,
    so an exception still fails the suite, but a returned False is dropped on
    the floor and the run prints `0 failed`.

    Found 2026-09-21 by noticing that adding two checks left the total at
    233. NINE were in that state: eight called bare, and one never called at
    all. Eight of the nine had been written that same week, which is the
    whole argument for asserting the wiring instead of the behaviour -- the
    mistake is invisible in every way a person reads a passing run, and it
    is the kind you make once per new check.

    So this reads the source rather than the results: every function whose
    body ends in a verdict tuple must appear in `main()` as an argument to
    `check(`, not as a bare statement, and must appear at all. And since
    2026-09-22, the wider hole: every `check_*` defined here is named
    somewhere else in the file, whichever way it reports.

    The scan is precedent_push_check.unrecorded_harness_checks, since
    2026-10-20, so the quick tier runs it too whenever this file changes
    (the test after this one proves it); this full-run copy is the
    backstop."""
    import precedent_push_check as ppc
    src = harness_parts.read_all(ROOT)
    bad = ppc.unrecorded_harness_checks(src)
    defined = len(re.findall(r'^def check_[a-z_0-9]+\(', src, re.M))
    return (not bad, f'{defined} check(s), all recorded',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_changed_files_refuses_an_uncalled_harness_check():
    """A branch adding a check_* that main() never calls is refused by the
    quick tier, before staging, naming the function.

    Until 2026-10-20 only the full run asked, so
    check_branch_policy_seam_asks_a_set_and_keeps_the_engine_answer reached
    main uncalled and turned it red (#1286/#1287). The control is the same
    file with the call wired in; the third case, a verdict-returning check
    called bare, is the older family the scan exists for."""
    import tempfile
    base = ('def check(name, ok, detail=""):\n    pass\n\n\n'
            'def main():\n    pass\n')
    added = ('\n\ndef check_zz_uncalled():\n'
             '    check("zz", True)\n')
    verdict = ('\n\ndef check_zz_verdict():\n    bad = []\n'
               '    return (not bad, "d", "")\n')
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        rel = 'tools/verify_harness.py'
        commit, run = _changed_files_fixture(td / 'uncalled', {rel: base})
        commit({rel: base + added})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(td / 'wired', {rel: base})
        commit2({rel: base.replace('def main():\n    pass',
                                   'def main():\n    check_zz_uncalled()')
                 + added})
        rc2, out2 = run2()
        commit3, run3 = _changed_files_fixture(td / 'bare', {rel: base})
        commit3({rel: base + verdict + '\n\ndef _go():\n'
                 '    check_zz_verdict()\n'})
        rc3, out3 = run3()
    want = ('tools/verify_harness.py: check_zz_uncalled defined but never '
            'called from main()')
    cases = [
        ('an uncalled check_ is refused, by name', rc == 1 and want in out),
        ('control: the same check, called from main(), is not refused',
         want not in out2),
        ('a verdict-returning check called bare is refused, by name',
         rc3 == 1 and 'check_zz_verdict called bare' in out3),
    ]
    bad = [n for n, ok in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(bad) + ('' if not bad else
                                 f' -- {out[-400:]} | {out3[-400:]}'))


def check_push_to_staging_runs_own_checks_inside_a_budget():
    """2026-10-19: two consuming repos' Produce merged a change their own
    pull-request check was certain to fail, because since 2026-10-17 a push
    to main takes the basic tier and a repository's own approved workflow
    steps ran only at the Debut. They now run before a change reaches
    staging (Morgan: "before it's even pushed to staging"), split across a
    budget so a slow one is stopped and left to GitHub, never a failure and
    never minutes."""
    import subprocess as _sp
    import tempfile
    import precedent_push_check as ppc
    cases = []
    wf = ('name: Own\non:\n  pull_request:\n    branches: [main]\njobs:\n  check:\n'
          '    runs-on: ubuntu-latest\n    steps:\n'
          '      - name: Check out repository\n        uses: actions/checkout@v4\n'
          '      - name: Check {n}\n        run: python3 tools/{n}.py\n')
    scripts = {'fast_check': 'pass', 'failing_check': 'raise SystemExit(1)',
               'slow_check': 'import time; time.sleep(30)'}
    saved = ppc.OWN_CHECKS_BUDGET_SECONDS
    ppc.OWN_CHECKS_BUDGET_SECONDS = 3
    try:
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / 'tools').mkdir(); (d / '.github' / 'workflows').mkdir(parents=True)
            approved = {}
            for n, body in scripts.items():
                (d / 'tools' / f'{n}.py').write_text(body + '\n')
                rel = f'.github/workflows/{n}.yml'
                (d / rel).write_text(wf.format(n=n))
                approved[rel] = {'sha256': 'x', 'approved_by': 't'}
            (d / 'precedent.json').write_text(json.dumps({'github_ci_approved': approved}))
            own = ppc.own_checks_before_staging(d)
            by = {n: next((c for c in own if f'tools/{n}.py' in c[0]), None) for n in scripts}
            cases.append(('each approved workflow step is planned before staging',
                          all(by.values()), [c[0] for c in own]))
            run = lambda c: _sp.run(c[1], cwd=d, capture_output=True, text=True, timeout=60)
            if all(by.values()):
                cases.append(('a passing step passes', run(by['fast_check']).returncode == 0, ''))
                # 2026-10-20: the push check's own loop read argv[1] of a
                # wrapped step, looked for a file named "-c", and reported
                # every one as "could not run here".
                import contextlib, io
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    failed, missing, _t, _f = ppc.run(d, [by['fast_check']])
                cases.append(('the push check runs a wrapped step, never reports '
                              'it as a tool the repo lacks',
                              not failed and not missing, failure_detail(buf.getvalue(), 400)))
                cases.append(('a failing step fails, as GitHub would',
                              run(by['failing_check']).returncode == 1, ''))
                r = run(by['slow_check'])
                cases.append(('a step past its share of the budget is stopped and left to '
                              'GitHub, not failed', r.returncode == 0 and 'left to GitHub'
                              in r.stdout, r.stdout + r.stderr))
            cases.append(('CONTROL: a tool the list already runs is not run twice',
                          not ppc.own_checks_before_staging(
                              d, planned=[f'tools/{n}.py' for n in scripts]), ''))
    finally:
        ppc.OWN_CHECKS_BUDGET_SECONDS = saved
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'a push to staging runs the repository\'s own checks inside a budget '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_push_check_refuses_a_deleted_test_that_keeps_its_time():
    """2026-10-30: 7e5d9d26 deleted two harness tests and left their recorded
    times, and the full suite's partition case failed on main until a very
    deep check ran it. The push check already refused a new test with no
    time; a deleted test that keeps one is the same record gone wrong."""
    import subprocess as _sp
    import tempfile
    import precedent_push_check as ppc
    cases = []
    g = lambda d, *a: _sp.run(['git', '-C', str(d), *a], capture_output=True,
                              text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'tools').mkdir()
        g(d, 'init', '-q')
        g(d, 'config', 'user.email', 't@example.com')
        g(d, 'config', 'user.name', 't')
        h = d / 'tools' / 'verify_harness.py'
        times = d / 'tools' / 'harness_check_times.json'
        h.write_text('def check_kept():\n    pass\n\n\ndef check_gone():\n    pass\n')
        times.write_text(json.dumps({'seconds': {'check_kept': 1, 'check_gone': 1}}))
        g(d, 'add', '-A'); g(d, 'commit', '-qm', 'base')
        base = g(d, 'rev-parse', 'HEAD')
        h.write_text('def check_kept():\n    pass\n')
        g(d, 'commit', '-qam', 'delete a test')
        files = ['tools/verify_harness.py']
        problems = []
        ppc._new_tests_have_times(d, base, files, problems)
        cases.append(('a deleted test that keeps its recorded time is refused, by name',
                      any('deletes 1 test(s) whose recorded time is still kept' in p
                          and 'check_gone' in p for p in problems), problems))
        times.write_text(json.dumps({'seconds': {'check_kept': 1}}))
        g(d, 'commit', '-qam', 'drop its time')
        problems = []
        ppc._new_tests_have_times(d, base, files, problems)
        cases.append(('CONTROL: the same deletion with its time dropped passes',
                      not problems, problems))
        h.write_text('def check_kept():\n    pass\n\n\ndef check_new():\n    pass\n')
        g(d, 'commit', '-qam', 'add a test')
        problems = []
        ppc._new_tests_have_times(d, base, files, problems)
        cases.append(('a new test with no recorded time is still refused',
                      any('adds 1 test(s) with no recorded time' in p for p in problems),
                      problems))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'the push check refuses a deleted test that keeps its recorded time '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_push_check_refuses_an_added_raw_tail_report():
    """The push check refuses a change that ADDS a failure report which is
    the raw tail of a tool's output, and judges only the added lines
    (Morgan, 2026-10-31, strength: decided: "that should be a more general
    rule"; practices: control-asserts-which-failure, checks-read-only-the-work)."""
    import subprocess as _sp
    import tempfile
    import precedent_push_check as ppc
    cases = []
    g = lambda d, *a: _sp.run(['git', '-C', str(d), *a], capture_output=True,
                              text=True, check=True).stdout.strip()
    words = "reports a failure as the raw tail of a tool's output"
    old = ("def check_old():\n"
           "    out = 'x'\n"
           "    check('old', True, out[-300:])\n")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'tools').mkdir()
        g(d, 'init', '-q')
        g(d, 'config', 'user.email', 't@example.com')
        g(d, 'config', 'user.name', 't')
        h = d / 'tools' / 'verify_harness.py'
        h.write_text(old)
        g(d, 'add', '-A'); g(d, 'commit', '-qm', 'base')
        base = g(d, 'rev-parse', 'HEAD')
        files = ['tools/verify_harness.py']

        def judge(body):
            h.write_text(old + '\n\n' + body)
            g(d, 'commit', '-qam', 'change')
            problems = []
            ppc._added_raw_tail_reports(d, base, files, problems)
            return problems

        problems = judge("def check_new():\n"
                         "    out = 'y'\n"
                         "    check('new', 'a' in out, out[-400:])\n")
        cases.append(('an added raw tail in a check() detail is refused, by line, '
                      "in the guard's own words, naming the helper",
                      len(problems) == 1 and words in problems[0]
                      and 'tools/verify_harness.py:8:' in problems[0]
                      and '`failure_detail(out, 400)`' in problems[0], problems))
        cases.append(('the untouched old raw tail is not judged',
                      not any('verify_harness.py:3:' in p for p in problems), problems))
        problems = judge("def check_new():\n"
                         "    cases = []\n"
                         "    cases.append(('new', True,\n"
                         "                  (r.stdout + r.stderr)[-200:]))\n")
        cases.append(('an added raw tail in a cases.append() detail is refused',
                      len(problems) == 1 and words in problems[0]
                      and 'failure_detail(r.stdout + r.stderr, 200)' in problems[0],
                      problems))
        problems = judge("def check_new():\n"
                         "    out = 'y'\n"
                         "    check('new', 'a' in out, failure_detail(out, 400))\n")
        cases.append(('CONTROL: the same report through failure_detail() passes',
                      not problems, problems))
        problems = judge("def check_new():\n"
                         "    out = 'y'\n"
                         "    check('new', 'a' in out[-50:], '')\n")
        cases.append(('CONTROL: a tail the case asserts on, not reports, is not '
                      'refused', not problems, problems))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'the push check refuses an added raw-tail failure report '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_changed_files_asks_a_new_check_for_its_test():
    """A check added without its test, or without SOURCE_ROOT, is refused on
    the commit that adds it, and the refusal names what to write.

    check_deep_check.py refuses both, but judges the whole tree, so the
    changed-files scope a quick-tier push runs dropped its finding: in a
    consumer repo four repo-local checks landed with neither, and nothing
    said so until a Promote ran the full check (2026-09-28). The clean case
    is the control -- the same check with its test and SOURCE_ROOT passes.
    """
    import tempfile
    name = 'the changed-files check asks a new check for its test and SOURCE_ROOT'
    with tempfile.TemporaryDirectory() as td:
        commit, run = _changed_files_fixture(pathlib.Path(td) / 'bare')
        commit({'local/tools/checks/check_zzbare.py': 'import sys\nsys.exit(0)\n'})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(pathlib.Path(td) / 'ok')
        commit2({'local/tools/checks/check_zzok.py': _FIXTURE_CHECK_HEAD,
                 'local/tools/checks/tests/test_zzok.sh':
                     'python3 -c "print(1)" # check_zzok.py\nexit 0\n'})
        rc2, out2 = run2()
    cases = [
        ('a new check with no test is refused', rc == 1),
        ('the refusal names the test file to add, where the check lives',
         'add local/tools/checks/tests/test_zzbare.sh' in out),
        ('and gives the SOURCE_ROOT and ROOT lines to write',
         'SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent'
         in out and 'PRECEDENT_CHECK_ROOT' in out),
        ('control: the same shape with its test and SOURCE_ROOT passes',
         rc2 == 0),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 500)} / {failure_detail(out2, 300)}'))


def check_changed_files_fetches_a_base_a_single_branch_clone_lacks():
    """The per-file step of a push to staging fetches origin/staging when
    the clone has no such ref, and refuses -- never passes -- when the base
    still names no commit.

    2026-10-31, a consumer's very deep check: its clone fetched main alone,
    so origin/staging did not exist there, the diff against it failed and
    read as empty, and the step said "0 changed file(s) checked, 0
    problem(s)" over a commit that changed 26 files, Python among them. The
    fixture is that clone: an origin with main and staging, cloned with
    --single-branch, and a branch changing a Python file that does not
    compile."""
    import contextlib, io, tempfile
    name = ('the changed-files check fetches a base a single-branch clone '
            'lacks, and refuses one that names no commit')
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), '-c',
                               'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env)
    spec = importlib.util.spec_from_file_location(
        'ppc_single_branch', ROOT / 'tools' / 'precedent_push_check.py')
    ppc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppc)

    def run(repo, since):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ppc.changed_files_check(repo, since)
        return rc, buf.getvalue()
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        seed, origin, clone = td / 'seed', td / 'origin.git', td / 'clone'
        seed.mkdir()
        git(seed, 'init', '-q', '-b', 'main')
        (seed / 'README.md').write_text('fixture\n', encoding='utf-8')
        git(seed, 'add', '-A'); git(seed, 'commit', '-qm', 'base')
        git(seed, 'branch', 'staging')
        subprocess.run(['git', 'clone', '-q', '--bare', str(seed), str(origin)],
                       capture_output=True, env=env)
        subprocess.run(['git', 'clone', '-q', '--single-branch', '-b', 'main',
                        str(origin), str(clone)], capture_output=True, env=env)
        had_ref = git(clone, 'rev-parse', '--verify', '-q',
                      'origin/staging').returncode == 0
        git(clone, 'switch', '-q', '-c', 'work')
        (clone / 'tools').mkdir()
        (clone / 'tools' / 'broken.py').write_text('def (:\n', encoding='utf-8')
        git(clone, 'add', '-A'); git(clone, 'commit', '-qm', 'a broken file')
        rc, out = run(clone, 'origin/staging')
        rc2, out2 = run(clone, 'origin/no-such-branch')
    cases = [
        ('the fixture is the trap: the clone starts with no origin/staging',
         not had_ref),
        ('the missing base is fetched and the broken file is found',
         rc == 1 and 'tools/broken.py: does not compile' in out),
        ('...never the empty pass', '0 changed file(s) checked' not in out),
        ('a base that still names no commit is refused, and says it is not a '
         'pass', rc2 == 1 and 'names no commit here' in out2
         and 'this is not a pass' in out2),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 400)} / {failure_detail(out2, 300)}'))


def check_changed_files_asks_a_changed_glob_for_its_reason():
    """The per-file step of a landing refuses a practice whose applies_to
    changed while its applies_to_why did not, the comparison routing-reason
    makes at the Debut and around Produce.

    2026-10-31: a landing on staging added tools/harness/** to two
    practices' globs and left both reasons as they were. Every landing
    passed, and the move into main was refused for it. Morgan, 2026-11-01:
    "Fix at the root". Planted both ways: the glob alone is refused, naming
    the file; the glob with its reason passes; a practice new on the branch
    has no old reason and passes."""
    import contextlib, io, tempfile
    name = 'the changed-files check asks a changed glob for its reason'
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), '-c',
                               'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env)
    spec = importlib.util.spec_from_file_location(
        'ppc_glob_reason', ROOT / 'tools' / 'precedent_push_check.py')
    ppc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ppc)

    def practice(glob, why):
        return ('---\nslug:        zz\ntitle:       "zz"\ntier:        on-demand\n'
                f'applies_to:  ["{glob}"]\napplies_to_why: "{why}"\n'
                'status:      active\n---\n\n## Rule\n\nzz.\n')

    def run(repo, since):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ppc.changed_files_check(repo, since)
        return rc, buf.getvalue()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'r'
        (repo / 'practices').mkdir(parents=True)
        git(repo, 'init', '-q', '-b', 'main')
        f = repo / 'practices' / 'zz.md'
        f.write_text(practice('a/**', 'Where a lives.'), encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'base')
        base = git(repo, 'rev-parse', 'HEAD').stdout.strip()
        f.write_text(practice('b/**', 'Where a lives.'), encoding='utf-8')
        git(repo, 'commit', '-qam', 'glob alone')
        rc, out = run(repo, base)
        f.write_text(practice('b/**', 'Where b lives, since a moved.'), encoding='utf-8')
        git(repo, 'commit', '-qam', 'and its reason')
        rc2, out2 = run(repo, base)
        (repo / 'practices' / 'new.md').write_text(
            practice('c/**', 'Where c lives.'), encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'a new practice')
        rc3, out3 = run(repo, base)
    cases = [
        ('a glob changed with its reason left alone is refused, naming the '
         'file and both globs',
         rc == 1 and 'practices/zz.md: applies_to changed since' in out
         and 'applies_to_why did not' in out and 'b/**' in out),
        ('control: the same glob change with its reason updated passes',
         rc2 == 0 and 'applies_to_why did not' not in out2),
        ('a practice new on the branch has no old reason to compare, and '
         'passes', rc3 == 0 and 'new.md' not in out3),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else
                               f' -- {failure_detail(out, 400)} / {failure_detail(out2, 300)}'))


def check_changed_files_runs_one_copy_of_a_repo_local_test():
    """A repo-local test and its materialized copy change together, and only
    the materialized copy runs -- the one run_all.sh runs. Running both put
    the same `cd "$(dirname "$0")/../../.."` in local/ once and at the root
    once, and a test written for one failed from the other, only in the gate
    (a consumer report, 2026-09-28). The control: with no materialized copy
    (BestPractice's own local/), the original still runs.
    """
    import tempfile
    name = 'the changed-files check runs one copy of a repo-local test'
    test = ('cd "$(dirname "$0")/../../.."\n'
            '[ -d local ] || { echo "not at the repo root"; exit 1; }\n'
            '# check_zzloc.py\n')
    with tempfile.TemporaryDirectory() as td:
        commit, run = _changed_files_fixture(pathlib.Path(td) / 'both')
        commit({'local/tools/checks/check_zzloc.py': _FIXTURE_CHECK_HEAD,
                'local/tools/checks/tests/test_zzloc.sh': test,
                'tools/checks/check_zzloc.py': _FIXTURE_CHECK_HEAD,
                'tools/checks/tests/test_zzloc.sh': test})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(pathlib.Path(td) / 'local-only')
        commit2({'local/tools/checks/check_zzsolo.py': _FIXTURE_CHECK_HEAD,
                 'local/tools/checks/tests/test_zzsolo.sh':
                     '# check_zzsolo.py\nexit 0\n'})
        rc2, out2 = run2()
    cases = [
        ('with both copies changed, only the materialized one is named, for '
         'the Debut', rc == 0 and '1 test(s) of changed checks run at the '
         'Debut, not here: tools/checks/tests/test_zzloc.sh' in out),
        ('control: with no materialized copy, the original is named',
         rc2 == 0 and 'local/tools/checks/tests/test_zzsolo.sh' in out2),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 500)} / {failure_detail(out2, 300)}'))
def check_for_change_adds_what_the_reach_ledger_picks():
    """THE BUG (2026-10-14, main red, run 38570778970). for_change_plan
    picked tests by the functions they name; GitHub's scoped run picks by
    harness_reach's ledger of what each test ran.
    check_vendor_engine_wires_a_new_hook_into_an_installed_repo runs the
    refresh in a child process and names none of its functions, so the
    local plan never picked it, even at --budget 1500, and main went red.
    Since then the plan adds the ledger's picks under the same budget.

    One scratch repository, tools/zzmod.py's f() changed. Cases:
    A. without a ledger, the child-process test is not picked (the bug);
    B. with one, the test the ledger saw run f() is picked, one remove out;
    C. a test whose reach the ledger never fully saw is picked too, ranked
       after B's, so a tight budget names it rather than running it;
    D. CONTROL: a test the ledger saw run only another function is not;
    E. CONTROL: a ledger from a failing run adds nothing;
    F. a change to the recording machinery adds nothing and says GitHub's
       run will run the whole suite;
    G. a fixture the harness starts never reads the live ledger: one did,
       as a worktree of this repository sharing its refs, and main went red
       on check_changed_files_only_judges_the_change (run 38607892096)."""
    import tempfile
    import harness_reach
    name = '--for-change adds the tests the reach ledger picks'
    harness = ('import subprocess\n'
               'def check_child():\n'
               "    subprocess.run(['python3', 'runner.py'])\n"
               'def check_blind():\n'
               "    subprocess.run(['git', 'status'])\n"
               'def check_other():\n'
               "    subprocess.run(['python3', 'other.py'])\n")
    times = json.dumps({'default_seconds': 1.0,
                        'seconds': {'check_child': 5.0, 'check_blind': 20.0}})
    base = {'tools/verify_harness.py': harness,
            'tools/zzmod.py': 'def f():\n    return 1\n\ndef g():\n    return 1\n',
            'tools/harness_check_times.json': times}
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'repo'
        repo.mkdir()

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), '-c',
                                   'core.hooksPath=/dev/null', *a],
                                  capture_output=True, text=True, env=env)
        git('init', '-q', '-b', 'main')
        for r_, text in base.items():
            (repo / r_).parent.mkdir(parents=True, exist_ok=True)
            (repo / r_).write_text(text, encoding='utf-8')
        git('add', '-A'); git('commit', '-qm', 'base')
        since = git('rev-parse', 'HEAD').stdout.strip()
        ledger = {'version': harness_reach.VERSION, 'commit': since, 'green': True,
                  'checks': {
                      'check_child': {'c': {'tools/zzmod.py': ['f']}},
                      'check_blind': {'o': ['git status run against the repository itself']},
                      'check_other': {'c': {'tools/zzmod.py': ['g']}}}}
        (repo / 'tools' / 'zzmod.py').write_text(
            'def f():\n    return 2\n\ndef g():\n    return 1\n', encoding='utf-8')
        git('commit', '-qam', 'change f')
        bare = for_change_plan(repo, since, budget=60, ledger={})
        wide = for_change_plan(repo, since, budget=60, ledger=ledger)
        tight = for_change_plan(repo, since, budget=10, ledger=ledger)
        red = for_change_plan(repo, since, budget=60, ledger=dict(ledger, green=False))
        (repo / 'tools' / 'harness_reach.py').write_text('# machinery\n', encoding='utf-8')
        git('add', '-A'); git('commit', '-qm', 'machinery')
        mach = for_change_plan(repo, since, budget=60, ledger=ledger)
        # G: a harness run plans its fixtures without the live ledger. The
        # scratch repository stands in for this one, so the default load
        # is reached; the load itself is a stand-in that counts.
        loads = []
        saved = (globals()['ROOT'], harness_reach.load_ledger,
                 os.environ.get(FOR_CHANGE_LEDGER_OFF_ENV))
        globals()['ROOT'] = repo
        harness_reach.load_ledger = lambda fetch=True: loads.append(1) or {}
        try:
            os.environ[FOR_CHANGE_LEDGER_OFF_ENV] = '1'
            for_change_plan(repo, since, budget=60)
            off = len(loads)
            os.environ.pop(FOR_CHANGE_LEDGER_OFF_ENV)
            for_change_plan(repo, since, budget=60)
            on = len(loads) - off
        finally:
            globals()['ROOT'], harness_reach.load_ledger = saved[0], saved[1]
            if saved[2] is None:
                os.environ.pop(FOR_CHANGE_LEDGER_OFF_ENV, None)
            else:
                os.environ[FOR_CHANGE_LEDGER_OFF_ENV] = saved[2]
    cases = [
        ('A. without a ledger the child-process test is not picked',
         'check_child' not in bare['run'] + bare['deferred']),
        ('B. with one, the test the ledger saw run f() runs',
         'check_child' in wide['run']),
        ('C. a test whose reach was never fully seen is picked, after B\'s: '
         'a tight budget runs B and names C',
         'check_blind' in wide['run'] and tight['run'] == ['check_child']
         and tight['deferred'] == ['check_blind']),
        ('D. CONTROL: a test that ran only g() is not picked',
         'check_other' not in wide['run'] + wide['deferred']),
        ('E. CONTROL: a ledger from a failing run adds nothing',
         not red['run'] and not red['deferred']),
        ('F. a machinery change adds nothing and says the whole suite runs',
         'check_child' not in mach['run'] + mach['deferred']
         and any('whole suite' in n for n in mach['unmapped'])),
        ('G. under a harness run the live ledger is never read; without the '
         'mark it is', off == 0 and on == 1),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else ' -- ' + json.dumps(
              {'bare': bare, 'wide': wide, 'tight': tight, 'red': red,
               'mach': mach}, default=str)[:1500]))

def check_changed_files_runs_the_harness_tests_a_change_reaches():
    """The changed-files step never starts the harness, and a check script's
    change NAMES every test that names it, for the Debut, without running
    one (Morgan, 2026-10-16: tests run at the Debut and around Produce,
    never before a push). It used to run `verify_harness.py --for-change`
    (2026-10-11), which made a landing's quick check take minutes.

    The first half is the push side of check_for_change_runs_the_tests_a_
    change_reaches: a fake harness that fails is a refusal naming the
    failure, and one that only defers tests passes with its note shown
    (2026-10-11, after a243d9c0). The second is the philosophy pair: two
    scripts share test_philosophy_scoping.sh, and pairing by name ran no
    test for either. The control: a change with no Python under tools/
    never starts the harness.
    """
    import contextlib, io, tempfile
    name = 'the changed-files check runs no test before a push'
    fake = ('import sys, pathlib\n'
            "if '--for-change' in sys.argv:\n"
            "    pathlib.Path('ran-for-change').write_text(' '.join(sys.argv[1:]))\n"
            "    print('for-change: running 1 test(s), about 1 s: check_zz')\n"
            "    print('for-change: NOT RUN HERE: 1 test(s) over the budget')\n"
            "    if pathlib.Path('tools/fail').exists():\n"
            "        print('FAIL: zz broke')\n"
            "        sys.exit(1)\n")
    pair_test = ('# check_zzpa.py and check_zzpb.py share this test\n'
                 'touch "$(dirname "$0")/../../../../pair-test-ran"\nexit 0\n')
    with tempfile.TemporaryDirectory() as td:
        commit, run = _changed_files_fixture(pathlib.Path(td) / 'fails',
                                             {'tools/verify_harness.py': fake})
        commit({'tools/zzmod.py': 'X = 1\n', 'tools/fail': ''})
        rc, out = run()
        ran1 = (pathlib.Path(td) / 'fails' / 'repo' / 'ran-for-change').is_file()
        commit2, run2 = _changed_files_fixture(pathlib.Path(td) / 'passes',
                                               {'tools/verify_harness.py': fake})
        commit2({'tools/zzmod.py': 'X = 2\n'})
        err2 = io.StringIO()
        with contextlib.redirect_stderr(err2):
            rc2, out2 = run2()
        ran2 = (pathlib.Path(td) / 'passes' / 'repo' / 'ran-for-change').is_file()
        commit3, run3 = _changed_files_fixture(pathlib.Path(td) / 'docs',
                                               {'tools/verify_harness.py': fake})
        commit3({'notes.md': 'words\n'})
        rc3, out3 = run3()
        ran3 = (pathlib.Path(td) / 'docs' / 'repo' / 'ran-for-change').is_file()
        commit4, run4 = _changed_files_fixture(pathlib.Path(td) / 'pair', {
            'local/tools/checks/check_zzpa.py': _FIXTURE_CHECK_HEAD,
            'local/tools/checks/check_zzpb.py': _FIXTURE_CHECK_HEAD,
            'local/tools/checks/tests/test_zzpair.sh': pair_test})
        commit4({'local/tools/checks/check_zzpb.py': _FIXTURE_CHECK_HEAD + '# edit\n'})
        rc4, out4 = run4()
        ran4 = (pathlib.Path(td) / 'pair' / 'repo' / 'pair-test-ran').is_file()
    cases = [
        ('a change to Python under tools/ never starts the harness, even one '
         'whose tests would fail', rc == 0 and not ran1
         and 'FAIL: zz broke' not in out),
        ('...nor a passing one', rc2 == 0 and not ran2),
        ('control: a documents-only change never starts it either',
         rc3 == 0 and not ran3),
        ('a check script names the shared test that names it, and runs none',
         rc4 == 0 and not ran4 and 'local/tools/checks/tests/test_zzpair.sh'
         in out4),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else
                              f' -- {failure_detail(out, 400)} / {failure_detail(out2, 300)} / {failure_detail(out4, 300)}'))


def check_a_new_test_lands_with_its_time():
    """A commit that adds a harness test carries its recorded time, or the
    per-file step refuses it, naming --record-new-times (Morgan, 2026-10-16:
    "The new heavy tests should be in the batch of tests as they land on
    the branch"). A hundred tests went unrecorded after 2026-10-09 and were
    dealt as default_seconds. The control: with the time recorded, it
    passes; and a change that adds no test is not asked.
    """
    import tempfile
    name = 'a new harness test lands with its recorded time'
    times = lambda names: json.dumps({'seconds': {n: 1.0 for n in names}})
    # Each planted test is called from main(), as a real one is: the quick
    # tier refuses an uncalled harness test (unrecorded_harness_checks), and
    # an uncalled one here would fail the controls for the wrong reason.
    def harness(bodies):
        return (''.join(f'def {n}():\n    {b}\n' for n, b in bodies.items())
                + 'def main():\n' + ''.join(f'    {n}()\n' for n in bodies))
    with tempfile.TemporaryDirectory() as td:
        base = {'tools/verify_harness.py': harness({'check_old': 'pass'}),
                'tools/harness_check_times.json': times(['check_old'])}
        added = harness({'check_old': 'pass', 'check_zz_new': 'pass'})
        commit, run = _changed_files_fixture(pathlib.Path(td) / 'bare', base)
        commit({'tools/verify_harness.py': added})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(pathlib.Path(td) / 'timed', base)
        commit2({'tools/verify_harness.py': added,
                 'tools/harness_check_times.json': times(['check_old', 'check_zz_new'])})
        rc2, out2 = run2()
        commit3, run3 = _changed_files_fixture(pathlib.Path(td) / 'edit', base)
        commit3({'tools/verify_harness.py': harness({'check_old': 'return 1'})})
        rc3, out3 = run3()
    cases = [
        ('a new test with no recorded time is refused, naming the command',
         rc == 1 and 'adds 1 test(s) with no recorded time (check_zz_new)' in out
         and '--record-new-times' in out),
        ('control: with its time recorded, it passes', rc2 == 0),
        ('control: an edit that adds no test is not asked', rc3 == 0),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 300)} / {failure_detail(out2, 300)}'))


def check_push_check_list_is_never_refused():
    """`precedent_push_check.py --list` runs nothing and pushes nothing, so
    the refusals about what a push may carry never stop it (2026-10-17).

    It was refused whenever main had commits staging lacked, and the harness
    test that reads its list went red at the Debut for a reason unrelated to
    any change. The control: the same refusal still stops a real check run.
    """
    import contextlib, io
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    name = 'the push check\'s --list is never refused'
    saved = (ppc._promote_only_refusal, ppc._full_tier_refusal)
    ppc._promote_only_refusal = lambda root, argv: 'main has 6 commit(s) staging lacks'
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc_list = ppc.main(['--list'])
        listed = out.getvalue()
        out2, err2 = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out2), contextlib.redirect_stderr(err2):
            rc_run = ppc.main(['--tier', 'basic'])
    finally:
        ppc._promote_only_refusal, ppc._full_tier_refusal = saved
    cases = [
        ('--list prints the list while the refusal holds',
         rc_list == 0 and 'tools/leak_gate.py' in listed
         and 'REFUSED' not in err.getvalue(), err.getvalue()[-200:]),
        ('control: the refusal still stops a check run',
         rc_run == 1 and 'REFUSED -- main has 6 commit(s)' in err2.getvalue(), ''),
    ]
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_hooks_share_one_quote_blanking_block():
    """Every hook that asks "does this command run X" carries the same
    quote-blanking block, byte for byte (2026-09-30). They ship one by one,
    so they cannot import it; a fix to one copy only would bring back the
    quoted-pipe misread in the others."""
    hooks = ROOT / 'tools'   # the hooks' scripts, behind their stubs (2026-10-07)
    names = ['push-check-gate.sh', 'commit-identity-push-gate.sh',
             'doc-lint-gate.sh', 'merge-check-gate.sh']
    blocks = {}
    for n in names:
        text = (hooks / n).read_text(encoding='utf-8')
        a = text.find('# THE COMMAND WITH ITS QUOTED TEXT BLANKED')
        b = text.find('[[ -n "$bare" ]] || bare="$cmd"', a)
        blocks[n] = text[a:b] if a >= 0 and b > a else None
    missing = [n for n, v in blocks.items() if v is None]
    distinct = {v for v in blocks.values() if v is not None}
    check('every command-reading hook carries the one quote-blanking block',
          not missing and len(distinct) == 1,
          f'missing in {missing}' if missing else
          f'{len(distinct)} different copies')


def check_push_check_gate():
    """Everything CI used to run on a push now runs before it, locally
    (Morgan, 2026-09-25: "the same list of everything we used to run (just
    locally we do it, not via the github ci/cd)"). tools/precedent_push_check.py
    holds the list; push-check-gate.sh refuses a session's `git push` until it
    passes.

    The cases that matter are the silent ones: a push let through with a
    failing check, a push the gate did not recognise as one, a list that
    has quietly fallen behind the workflows it replaces, and a repository's
    own pre-push hook that the global core.hooksPath switched off -- which
    is how templates/hooks/pre-push sat dead in every repo that installed it
    until this was written."""
    import tempfile, json as _json, re as _re, shutil as _shutil
    name = 'the push check runs what CI ran, and the gate refuses on a failure'
    hook = ROOT / 'tools' / 'push-check-gate.sh'
    tool = ROOT / 'tools' / 'precedent_push_check.py'
    if not hook.exists() or not tool.exists():
        not_applicable(name, 'push-check-gate.sh or precedent_push_check.py is absent')
        return
    if not _shutil.which('jq'):
        not_applicable(name, 'no jq on this machine; the gate fails open without it')
        return
    cases = []

    # 1. The upstream list covers every tool a workflow here runs. A workflow
    #    added later, with no local twin, is exactly the drift this names.
    listed = subprocess.run([sys.executable, str(tool), '--list'], cwd=ROOT,
                            capture_output=True, text=True).stdout
    ran = set()
    for wf in (ROOT / '.github' / 'workflows').glob('*.yml'):
        ran |= set(_re.findall(r'python3?\s+tools/(\w+)\.py',
                               wf.read_text(encoding='utf-8')))
    missing = sorted(t for t in ran if f'tools/{t}.py' not in listed)
    cases.append((f'the upstream list names every tool a workflow here runs'
                  f'{" (missing: " + ", ".join(missing) + ")" if missing else ""}',
                  bool(ran) and not missing))

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # PRECEDENT_USER_CONFIG points at nothing, so no real person's
        # identity.json reaches the fixture (practice: fixture-owns-its-state).
        # Without it, a machine whose individual set turns promote_only on
        # refused the clean push to main below as a promotion-only branch:
        # red on every such machine, green in CI, which has no individual
        # source.
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a],
                                  capture_output=True, text=True, env=env)

        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        git(tmp, 'init', '-q', '-b', 'main', str(work))
        _shutil.copy2(tool, work / 'tools' / 'precedent_push_check.py')
        if (ROOT / 'tools' / 'precedent_branches.py').exists():
            _shutil.copy2(ROOT / 'tools' / 'precedent_branches.py',
                          work / 'tools' / 'precedent_branches.py')
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer'}), encoding='utf-8')
        # Stand-ins for the three consumer tools: each fails when a tracked
        # FAIL file names it, so a failure is a property of the tree pushed.
        # precedent_check's stand-in prints the summary line the push check
        # requires; a planted "zero" in FAIL makes it report 0 passed.
        for t in ('precedent_check', 'leak_gate', 'doc_lint'):
            (work / 'tools' / f'{t}.py').write_text(
                'import pathlib, sys\n'
                'f = pathlib.Path("FAIL")\n'
                'body = f.read_text() if f.exists() else ""\n'
                + ('print("precedent_check: %d passed, 0 violated" % '
                   '(0 if "zero" in body else 3))\n'
                   if t == 'precedent_check' else '')
                # precedent_check.py also answers as the basic tier's
                # ci_workflows (--only ci-workflow-approved), a check of
                # its own: fail it only when FAIL names that one.
                # ...and as the quick tier's changed_practice (--changed-files-only).
                + ('name = ("ci_workflows" if "ci-workflow-approved" in '
                   'sys.argv else "scrub_gate" if "scrub-gate" in sys.argv else '
                   '"practice_export_loop" if "practice-export-loop" in '
                   'sys.argv else "rename_links" if '
                   '"rename-updates-links" in sys.argv else '
                   '"generated_files" if '
                   '"generated-files-registered" in '
                   'sys.argv else "changed_practice" if "--changed-files-only" '
                   'in sys.argv else "precedent_check")\n'
                   if t == 'precedent_check' else f'name = "{t}"\n')
                + 'fail = name in body\n'
                # A failure that prints its finding and then pages of noise,
                # as precedent_check does with every SKIPPED check after its
                # VIOLATION block.
                + f'if fail and "noisy" in body:\n'
                  f'    print("VIOLATION  planted-{t}")\n'
                  f'    print("    the buried finding")\n'
                  f'    print("\\n".join(["SKIPPED filler"] * 150))\n'
                + 'sys.exit(1 if fail else 0)\n',
                encoding='utf-8')
        # The deep-check driver, when a repo has one, is on the list too.
        drv = work / 'tools' / 'checks' / 'tests' / 'run_all.sh'
        drv.parent.mkdir(parents=True)
        drv.write_text('#!/bin/bash\ncd "$(dirname "$0")/../../.."\n'
                       '[ -f FAIL ] && grep -q deep_check FAIL && exit 1\nexit 0\n',
                       encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'init')

        elsewhere = tmp / 'elsewhere'
        elsewhere.mkdir()

        def gate(command, cwd=work, project=work):
            payload = _json.dumps({'tool_input': {'command': command},
                                   'cwd': str(cwd)})
            p = subprocess.run(['bash', str(hook)], input=payload, text=True,
                               capture_output=True, timeout=300,
                               env=dict(env, CLAUDE_PROJECT_DIR=str(project)))
            return '"deny"' in p.stdout, p.stdout

        # No branch is fully checked before a push by default any more
        # (main and staging since 2026-10-17): the full check before a push is for a person whose
        # branch_push_checks says full.
        full_person = tmp / 'full-person'
        full_person.mkdir()
        (full_person / 'identity.json').write_text(_json.dumps(
            {'email': 'full@example.com', 'branch_push_checks': 'full'}),
            encoding='utf-8')
        full_cfg = tmp / 'full-config.json'
        full_cfg.write_text(_json.dumps(
            {'individual': {'path': str(full_person)}}), encoding='utf-8')

        def full_gate(command):
            saved = env.get('PRECEDENT_USER_CONFIG')
            env['PRECEDENT_USER_CONFIG'] = str(full_cfg)
            try:
                return gate(command)
            finally:
                if saved is None:
                    env.pop('PRECEDENT_USER_CONFIG')
                else:
                    env['PRECEDENT_USER_CONFIG'] = saved

        denied, out_main = gate('git push origin main')
        record = work / '.git' / 'precedent-push-check.json'
        cases.append(('a clean tree passing every check is let through',
                      not denied))
        cases.append(('and the pass is recorded against the tree',
                      record.is_file()))
        # A harness-given branch name is the ladder set's to refuse, at
        # git's pre-push (its branch_name_guard, 2026-10-16); this gate
        # judges no name.
        denied, out = gate('git push origin HEAD:refs/heads/claude/peaceful-ritchie-3u31td')
        cases.append(('the push gate judges no branch name: the ladder set\'s '
                      'own pre-push guard does', not denied))
        cases.append(('a push with nothing to note hands the session nothing',
                      '"additionalContext"' not in out_main))

        (work / 'FAIL').write_text('leak_gate', encoding='utf-8')
        git(work, 'add', 'FAIL')
        git(work, 'commit', '-q', '-m', 'break the leak gate')
        denied, out = gate('git push origin main')
        cases.append(('a tree failing one check is refused, and the refusal '
                      'names that check', denied and 'leak_gate' in out))
        (work / 'FAIL').write_text('leak_gate noisy', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'bury the finding under noise')
        denied, out = gate('git push origin main')
        cases.append(('a finding printed before pages of noise still reaches '
                      'the refusal, which shows only the tail',
                      denied and 'the buried finding' in out))
        (work / 'FAIL').write_text('leak_gate', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'plain leak gate failure again')
        denied, _ = gate('git commit -q -n -m x && git push')
        cases.append(("`git commit -n && git push` is still a push: -n "
                      "belongs to the commit", denied))
        denied, _ = gate('git push --dry-run origin main')
        cases.append(('a dry run sends nothing and is let through', not denied))
        denied, _ = gate('echo "then run git push" > notes.txt')
        cases.append(('`git push` quoted inside another command is not a push',
                      not denied))
        # todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command,
        # verbatim: the `|` inside the grep pattern is not a pipe.
        denied, _ = gate('cd /home/user/BestPractice && sed -n 1,80p '
                         'tools/checkin.py; echo ----; grep -n "^def \\|'
                         'REFUSES\\|upstream.commit\\|scrub\\|leak_gate\\|'
                         'git push\\|def main" tools/checkin.py | head -90')
        cases.append(('a quoted grep pattern holding `\\|git push` is not a '
                      'push', not denied))
        denied, _ = gate("git commit -m 'a | git push; in a message' -q")
        cases.append(('nor is one inside a single-quoted message', not denied))
        denied, _ = gate('cat <<EOF > notes.txt\ngit push origin main\nEOF')
        cases.append(('nor one on a heredoc line', not denied))
        denied, _ = gate('git status; git push origin main')
        cases.append(('a real push after `;` is still a push', denied))
        denied, _ = gate('echo ok | git push origin main')
        cases.append(('and after `|`', denied))
        denied, _ = gate('echo "a | b" && git push origin main')
        cases.append(('and after `&&`, behind a quoted pipe', denied))
        denied, _ = gate(f'git -C {work} push origin main', cwd=elsewhere,
                         project=elsewhere)
        cases.append(('`git -C <repo> push` from another project checks the '
                      'repository actually pushed', denied))
        denied, _ = gate(f'cd {work} && git push origin main', cwd=elsewhere,
                         project=elsewhere)
        cases.append(('so does a leading `cd <repo> &&`', denied))
        # A `git -C` that belongs to a later command, not to the push, names
        # a repository nothing is pushed to (2026-10-20: a push in one repo
        # was refused over `git -C <another> worktree remove` after it).
        denied, _ = gate(f'git push origin main; git -C {work} worktree list',
                         cwd=elsewhere, project=elsewhere)
        cases.append(('a later `git -C <other> ...` does not make <other> '
                      'the repository pushed', not denied))
        # Two `cd`s, the push belonging to the second (2026-10-28: a
        # feature-branch push in one repo was refused as a push to another
        # repo's main, because the gate read the command's FIRST `cd`).
        denied, _ = gate(f'cd {elsewhere} && ls; cd {work} && git push origin main',
                         cwd=elsewhere, project=elsewhere)
        cases.append(('with two `cd`s, the repository pushed is the one the '
                      'last `cd` before the push enters', denied))
        denied, _ = gate(f'cd {work} && ls; cd {elsewhere} && git push origin main',
                         cwd=elsewhere, project=elsewhere)
        cases.append(('and an earlier `cd <repo>` does not make <repo> the '
                      'repository pushed', not denied))
        denied, _ = gate(f'git commit -q -m "cd {work}" && git push origin main',
                         cwd=elsewhere, project=elsewhere)
        cases.append(('a `cd` inside a quoted message is not a `cd`',
                      not denied))

        (work / 'FAIL').write_text('zero', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'a run that checks nothing')
        # Pushed to staging by a person whose pushes are fully checked.
        denied, out = full_gate('git push origin HEAD:staging')
        cases.append(('a precedent_check run that passed ZERO checks is '
                      'refused although it exits 0', denied and 'ZERO' in out))
        (work / 'FAIL').write_text('deep_check', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'break the deep check suite')
        denied, out = full_gate('git push origin HEAD:staging')
        cases.append(("a repo's own deep-check suite (tools/checks/tests/"
                      "run_all.sh) runs, and its failure refuses the push",
                      denied and 'deep_check' in out))
        git(work, 'rm', '-q', 'FAIL')
        git(work, 'commit', '-q', '-m', 'fix it')
        denied, _ = gate('git push origin main')
        cases.append(('fixing the finding lets the push through', not denied))
        (work / 'FAIL').write_text('doc_lint', encoding='utf-8')
        git(work, 'add', 'FAIL')     # staged, not committed
        (work / 'FAIL').write_text('doc_lint', encoding='utf-8')
        denied, _ = gate('git push origin main')
        cases.append(('a pass recorded for the committed tree is not reused '
                      'over uncommitted edits that fail', denied))
        git(work, 'reset', '-q', '--hard')

        # The branch tiers (spec/BRANCH_TIERS_PLAN.md): precedent_check is
        # full-only, leak_gate is basic. The environment's own person must
        # not decide these, so no user config resolves.
        if (work / 'tools' / 'precedent_branches.py').exists():
            env['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
            (work / 'FAIL').write_text('precedent_check', encoding='utf-8')
            git(work, 'add', 'FAIL')
            git(work, 'commit', '-q', '-m', 'break a full-only check')
            denied, _ = gate('git push -u origin feature')
            cases.append(('a push to a working branch gets the basic check: a '
                          'failing full-only check does not refuse it', not denied))
            denied, _ = gate('git push origin HEAD:staging')
            cases.append(('so does a push to staging, where work lands', not denied))
            # The practice checks on the changed files run at the Debut and
            # around Produce, never before a push (Morgan, 2026-10-16): a
            # landing push no longer runs them, so their failure refuses
            # neither it nor a working branch's push.
            (work / 'FAIL').write_text('changed_practice', encoding='utf-8')
            git(work, 'commit', '-q', '-am', 'break the changed-files practice run')
            denied, out = gate('git push origin HEAD:staging')
            cases.append(('a push to staging does not run the practice checks '
                          'on the files it changes -- they wait for the Debut',
                          not denied and 'changed_practice' not in out))
            denied, _ = gate('git push -u origin feature')
            cases.append(('nor does a push to a working branch', not denied))
            (work / 'FAIL').write_text('precedent_check', encoding='utf-8')
            git(work, 'commit', '-q', '-am', 'back to a full-only failure')
            denied, out = full_gate('git push origin HEAD:staging')
            cases.append(('the same tree pushed by a person whose '
                          'branch_push_checks says full is refused by the full '
                          'check -- the basic pass just recorded does not '
                          'satisfy it', denied and 'precedent_check' in out))
            denied, out = full_gate('git push origin main feature')
            cases.append(('one push naming main and a branch that person '
                          'checks fully is checked fully',
                          denied and 'precedent_check' in out))
            (work / 'FAIL').write_text('leak_gate', encoding='utf-8')
            git(work, 'commit', '-q', '-am', 'break the leak gate again')
            denied, out = gate('git push origin feature')
            cases.append(('the leak gate runs on a working-branch push too',
                          denied and 'leak_gate' in out))
            git(work, 'rm', '-q', 'FAIL')
            git(work, 'commit', '-q', '-m', 'fix it again')
            denied, _ = full_gate('git push origin main')
            again = subprocess.run(
                [sys.executable, 'tools/precedent_push_check.py', '--gate',
                 '--push-command', 'origin feature'],
                cwd=work, capture_output=True, text=True, env=env).stdout
            cases.append(('a full pass satisfies a later basic gate on the same '
                          'tree', not denied and 'already passed' in again))
            env.pop('PRECEDENT_USER_CONFIG')

        # A pass is shared through origin, so a second checkout -- another
        # window -- does not re-run the suite on files the first one passed
        # (Morgan, 2026-09-25). And only exactly those files, at that tier.
        env['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
        hub = tmp / 'hub.git'
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(hub))
        git(work, 'remote', 'add', 'origin', f'file://{hub}')
        git(work, 'push', '-q', 'origin', 'HEAD:refs/heads/main')

        def run_check(cwd, *a):
            return subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                                   *a], cwd=cwd, capture_output=True, text=True,
                                  env=env).stdout

        # Staging, the landing branch, takes the quick check, so asking for
        # the full suite says why.
        ran = run_check(work, '--tier', 'full', '--because',
                        'the shared-receipt test needs a full pass')
        files = git(hub, 'ls-tree', '-r', '--name-only',
                    'precedent-check-receipts').stdout.split()
        cases.append(('a full pass is published to origin as a receipt',
                      any(f.startswith('receipts/') for f in files)))
        # The run says the push plainly (2026-10-17): no document said a
        # check writes to origin, and the old line ("receipt shared with
        # every checkout") never said it pushed, or where.
        cases.append(('the run says in plain words that it pushed a pass '
                      'receipt, to which branch, on origin, and how to stop it',
                      'pushed a pass receipt to precedent-check-receipts on '
                      'origin' in ran and 'PRECEDENT_NO_SHARED_PASS=1' in ran))
        other = tmp / 'other'
        git(tmp, 'clone', '-q', f'file://{hub}', str(other))
        got = run_check(other, '--gate', '--tier', 'full')
        cases.append(('another checkout of the same files does not re-run the '
                      'suite, and says the pass came from elsewhere',
                      'already passed the full check at' in got
                      and 'another checkout' in got))
        msg = git(hub, 'log', '-1', '--format=%B', 'precedent-check-receipts').stdout
        cases.append(('the receipt branch carries no file of the repository, '
                      'and its commits skip CI',
                      bool(files) and all(f == 'ORDER' or f.startswith('receipts/')
                                          for f in files)
                      and '[skip ci]' in msg))
        (other / 'list.txt').write_text('changed\n', encoding='utf-8')
        git(other, 'add', 'list.txt')
        git(other, 'commit', '-q', '-m', 'one change')
        got = run_check(other, '--gate', '--tier', 'full')
        cases.append(('one changed file and the suite runs again',
                      'already passed' not in got and 'all passed' in got))
        (work / 'basic.txt').write_text('b\n', encoding='utf-8')
        git(work, 'add', 'basic.txt')
        git(work, 'commit', '-q', '-m', 'basic only')
        run_check(work, '--tier', 'basic')
        git(work, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
        git(other, 'fetch', '-q', 'origin')
        git(other, 'checkout', '-q', '--detach', 'origin/main')
        got = run_check(other, '--gate', '--tier', 'full')
        cases.append(('a shared BASIC pass never satisfies a full gate',
                      'already passed' not in got and 'all passed' in got))
        env.pop('PRECEDENT_USER_CONFIG')

        # A shallow clone is deepened before anything runs: history checks
        # on a shallow clone skip, and a skip would read as a pass here.
        shallow = tmp / 'shallow'
        git(tmp, 'clone', '-q', '--depth', '1', f'file://{work}', str(shallow))
        was = git(shallow, 'rev-parse', '--is-shallow-repository').stdout.strip()
        subprocess.run([sys.executable, 'tools/precedent_push_check.py'],
                       cwd=shallow, capture_output=True, text=True, env=env)
        now = git(shallow, 'rev-parse', '--is-shallow-repository').stdout.strip()
        cases.append(('a shallow clone is deepened before the checks run',
                      was == 'true' and now == 'false'))

        plain = tmp / 'plain'
        git(tmp, 'init', '-q', str(plain))
        denied, _ = gate(f'git -C {plain} push', cwd=plain, project=plain)
        cases.append(('a repository without the push check is let through',
                      not denied))

        # The global pass-through: a repo's own pre-push runs, and decides.
        ci_hook = ROOT / 'tools' / 'commit-identity.sh'
        if ci_hook.exists():
            home = tmp / 'home'
            home.mkdir()
            (work / 'identity.json').write_text(_json.dumps(
                {'name': 'T', 'email': 't@example.com', 'timezone': 'UTC'}),
                encoding='utf-8')
            hooks = home / 'git-hooks'
            subprocess.run(['bash', str(ci_hook)], capture_output=True,
                           text=True, timeout=120,
                           env=dict(env, HOME=str(home), CLAUDE_PROJECT_DIR=str(work),
                                    PRECEDENT_GLOBAL_HOOKS=str(hooks),
                                    PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                                    PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
            own = work / '.git' / 'hooks' / 'pre-push'
            own.write_text('#!/bin/sh\nread line; echo "OWN $1 $line"; exit 7\n',
                           encoding='utf-8')
            own.chmod(0o755)
            p = subprocess.run([str(hooks / 'pre-push'), 'origin'], cwd=work,
                               input='ref-line\n', capture_output=True,
                               text=True, env=env)
            cases.append(("the global hooks directory passes pre-push through to "
                          "the repository's own hook, arguments, stdin and "
                          "refusal intact",
                          (hooks / 'pre-push').exists() and p.returncode == 7
                          and 'OWN origin ref-line' in p.stdout))

    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_global_gate_runs_a_repos_gate_only_from_above():
    """tools/precedent_global_gate.sh, run from the user-level settings the
    cloud setup script writes, runs the engine's merge or push gate for a
    session opened above its repositories, hands the hook input through,
    names the engine's repository as the project, and stays out where the
    project's own settings already wire that gate.

    2026-10-19 (Morgan: "Go"): a session opened in /home/user ran none of
    the repositories' gates, so its merges into main went unchecked (#1206,
    #1217). Negative control: without the wrapper nothing runs from above."""
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)
        engine, above, inside = w / 'engine', w / 'above', w / 'above' / 'repo'
        (engine / 'tools').mkdir(parents=True)
        (inside / '.claude').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'precedent_global_gate.sh',
                    engine / 'tools' / 'precedent_global_gate.sh')
        (engine / 'tools' / 'push-check-gate.sh').write_text(
            '#!/bin/bash\nprintf "RAN project=%s input=%s" '
            '"$CLAUDE_PROJECT_DIR" "$(cat)"\n', encoding='utf-8')
        (inside / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
            'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command',
                'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/push-check-gate.sh'}]}]}}),
            encoding='utf-8')

        def run(gate, project):
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
            return subprocess.run(['bash', str(engine / 'tools' / 'precedent_global_gate.sh'),
                                   gate], input='{"tool_name":"Bash"}', env=env,
                                  capture_output=True, text=True, timeout=60)
        r = run('push-check-gate.sh', above)
        cases.append(('THE DISCRIMINATING CASE: from above the repositories the '
                      'gate runs, with the hook input and the engine as project',
                      r.returncode == 0 and f'RAN project={engine.resolve()}' in r.stdout
                      and 'input={"tool_name":"Bash"}' in r.stdout,
                      r.stdout + r.stderr))
        r = run('push-check-gate.sh', inside)
        cases.append(('inside a repository that wires the gate itself, nothing '
                      'runs twice', r.returncode == 0 and 'RAN' not in r.stdout,
                      r.stdout + r.stderr))
        r = run('rm-everything.sh', above)
        cases.append(('a name that is not one of the two gates runs nothing',
                      r.returncode == 0 and 'RAN' not in r.stdout
                      and 'no gate named' in r.stderr, r.stdout + r.stderr))
        r = run('merge-check-gate.sh', above)
        cases.append(('a gate missing beside it fails open and says so',
                      r.returncode == 0 and 'is not beside this file' in r.stderr,
                      r.stdout + r.stderr))
        # The reply check (2026-10-19): it names no repository, so it runs in
        # the one the hook input's cwd is in, else in the engine's, and its
        # refusal (exit 2) reaches Claude Code.
        (engine / 'tools' / 'stop-reply-check.sh').write_text(
            '#!/bin/bash\ncat >/dev/null; printf "RAN pwd=%s" "$PWD"; exit 2\n',
            encoding='utf-8')
        repo = above / 'work'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'precedent_gate.py').write_text('', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)

        def run_stop(cwd):
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(above))
            return subprocess.run(['bash', str(engine / 'tools' / 'precedent_global_gate.sh'),
                                   'stop-reply-check.sh'], input=json.dumps({'cwd': str(cwd)}),
                                  env=env, capture_output=True, text=True, timeout=60)
        r = run_stop(repo)
        cases.append(('the reply check runs in the repository the session was '
                      'working in, and its refusal comes through',
                      r.returncode == 2 and f'RAN pwd={repo.resolve()}' in r.stdout,
                      (r.returncode, r.stdout + r.stderr)))
        r = run_stop(above)
        cases.append(('from a folder in no repository, it runs in the engine\'s',
                      r.returncode == 2 and f'RAN pwd={engine.resolve()}' in r.stdout,
                      (r.returncode, r.stdout + r.stderr)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the user-level gate runs a repository\'s gate only from above '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_switchboard_runs_the_hooks_of_the_repo_an_action_is_about():
    """tools/precedent_run_repo_hooks.py, called from the user-level line for
    each moment, runs the hooks of the repository an action is about -- the
    file it writes, the folder a command cds into, the prompt's folder --
    filtered by matcher, passes a refusal and a JSON denial through, does
    nothing in a session opened inside a repository, and with no repository
    named runs only the two gates that find their own.

    2026-10-19 (Morgan: "Okay, let's do it, Act and Booked"): a session opened
    above its repositories ran none of their hooks but the few the setup
    script named one at a time. Negative control: the same Edit with the
    session opened inside the repository runs nothing (native hooks do)."""
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        engine = root / 'engine'
        (engine / 'tools').mkdir(parents=True)
        for name in ('precedent_run_repo_hooks.py', 'precedent_hooks.py',
                     'precedent_session_check.py', 'harness_times_merge.py'):
            shutil.copy(ROOT / 'tools' / name, engine / 'tools' / name)
        (engine / '.claude').mkdir()
        (engine / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
            'PreToolUse': [{'matcher': 'Bash', 'hooks': [
                {'type': 'command', 'command': 'echo ENGINE-PUSH # push-check-gate.sh'},
                {'type': 'command', 'command': 'echo ENGINE-OTHER'}]}]}}), encoding='utf-8')

        def repo(name, hooks):
            r = root / name
            (r / '.claude').mkdir(parents=True)
            (r / '.claude' / 'settings.json').write_text(json.dumps({'hooks': hooks}),
                                                        encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(r)], check=True)
            return r
        a = repo('a', {
            'PreToolUse': [
                {'matcher': 'Edit|Write', 'hooks': [{'type': 'command',
                 'command': 'echo "A refuses $CLAUDE_PROJECT_DIR" >&2; exit 2'}]},
                {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'echo A-BASH'}]}],
            'UserPromptSubmit': [{'hooks': [{'type': 'command', 'command': 'echo A-PROMPT'}]}]})
        b = repo('b', {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command',
            'command': 'echo \'{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
                       '"permissionDecision": "deny", "permissionDecisionReason": "B says no"}}\''}]}]})

        def run(event, payload, project=root):
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project))
            return subprocess.run([sys.executable, str(engine / 'tools' / 'precedent_run_repo_hooks.py'),
                                   event], input=json.dumps(payload), env=env,
                                  capture_output=True, text=True, timeout=60)
        r = run('PreToolUse', {'cwd': str(root), 'tool_name': 'Edit',
                               'tool_input': {'file_path': str(a / 'x.md')}})
        cases.append(('THE DISCRIMINATING CASE: an edit in a repository runs its Edit '
                      'hook, as that repository, and the refusal comes through',
                      r.returncode == 2 and f'A refuses {a.resolve()}' in r.stderr
                      and 'A-BASH' not in r.stdout, (r.returncode, r.stdout, r.stderr)))
        r = run('PreToolUse', {'cwd': str(root), 'tool_name': 'Edit',
                               'tool_input': {'file_path': str(a / 'x.md')}}, project=a)
        cases.append(('negative control: opened inside the repository, nothing runs',
                      r.returncode == 0 and not r.stdout and not r.stderr,
                      (r.returncode, r.stdout, r.stderr)))
        r = run('PreToolUse', {'cwd': str(root), 'tool_name': 'Bash',
                               'tool_input': {'command': f'cd {a} && ls'}})
        cases.append(('a command that cds into a repository runs that one\'s Bash hooks',
                      r.returncode == 0 and 'A-BASH' in r.stdout + r.stderr, (r.stdout, r.stderr)))
        r = run('PreToolUse', {'cwd': str(root), 'tool_name': 'Bash',
                               'tool_input': {'command': f'git -C {b} status'}})
        cases.append(('a JSON denial from the repository is handed back as it is',
                      r.returncode == 0 and '"permissionDecision": "deny"' in r.stdout,
                      (r.stdout, r.stderr)))
        r = run('UserPromptSubmit', {'cwd': str(a), 'prompt': 'hi'})
        cases.append(('a prompt runs the hooks of the folder the session is working in',
                      r.returncode == 0 and 'A-PROMPT' in r.stdout, (r.stdout, r.stderr)))
        r = run('PreToolUse', {'cwd': str(root), 'tool_name': 'Bash',
                               'tool_input': {'command': 'ls'}})
        cases.append(('a command in no repository runs only the self-locating gates',
                      'ENGINE-PUSH' in r.stdout + r.stderr and 'ENGINE-OTHER' not in r.stdout + r.stderr,
                      (r.stdout, r.stderr)))
        r = run('Nonsense', {})
        cases.append(('an unknown moment runs nothing', r.returncode == 0
                      and 'usage' in r.stdout, r.stdout))
        # 2026-10-29: a clone made after session start (the attach tool's)
        # never had its merge drivers set, and its session check warned on
        # every turn. The switchboard sets them before running its hooks.
        a_tools = a / 'tools'
        a_tools.mkdir()
        shutil.copy(ROOT / 'tools' / 'harness_times_merge.py', a_tools)
        (a / '.gitattributes').write_text(
            'tools/harness_check_times.json merge=precedent-harness-times\n',
            encoding='utf-8')

        def driver():
            return subprocess.run(['git', '-C', str(a), 'config', '--get',
                                   'merge.precedent-harness-times.driver'],
                                  capture_output=True, text=True).stdout.strip()
        before = driver()
        r = run('UserPromptSubmit', {'cwd': str(a), 'prompt': 'hi'})
        cases.append(('running a late clone\'s hooks sets the merge driver its '
                      '.gitattributes names, which no session start set',
                      not before and 'harness_times_merge.py' in driver(),
                      (before, driver(), r.stderr)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the switchboard runs the hooks of the repository an action is about '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:240]}' for n, d in bad))


def check_cloud_setup_script_writes_each_hook_once():
    """The setup script documentation/CLOUD_SETUP.md gives for the cloud
    environment writes the session-start runner and the merge and push
    gates into the user-level settings, keeps what the file held, and run
    again adds nothing.

    2026-10-19: its duplicate test looked for the command in the file's JSON
    text, where the command's quotes are escaped, so every run added the
    hook again; nothing ran the script, so nothing noticed. Negative
    control: that test writes each hook twice and fails the first case."""
    import tempfile, re as _re
    text = (ROOT / 'documentation' / 'CLOUD_SETUP.md').read_text(encoding='utf-8')
    m = _re.search(r'^mkdir -p ~/\.claude\n.*?^PY$', text, _re.M | _re.S)
    if not m:
        check('the cloud setup script writes each hook once', False,
              'no setup script found in documentation/CLOUD_SETUP.md')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        home = pathlib.Path(td)
        (home / '.claude').mkdir()
        (home / '.claude' / 'settings.json').write_text(json.dumps(
            {'permissions': {'allow': ['Bash(ls)']}, 'hooks': {'PreToolUse': [
                {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command':
                 'f=$(ls -d /home/user/*/tools/precedent_global_gate.sh); '
                 'bash "$f" push-check-gate.sh || true'}]}]}}), encoding='utf-8')
        env = dict(os.environ, HOME=str(home))
        for _ in range(2):
            r = subprocess.run(['sh', '-c', m.group(0)], env=env,
                               capture_output=True, text=True, timeout=60)
        got = json.loads((home / '.claude' / 'settings.json').read_text(encoding='utf-8'))
        pairs = [(name, h['command']) for name, ev in got.get('hooks', {}).items()
                 for e in ev for h in e.get('hooks', [])]
        cmds = [c for _n, c in pairs]
        cases.append(('THE DISCRIMINATING CASE: run twice, each hook is there once',
                      r.returncode == 0 and len(pairs) == len(set(pairs)) == 5,
                      cmds or failure_detail(r.stderr, 300)))
        names = sorted(n for n, _c in pairs)
        switch = [c for n, c in pairs if n != 'SessionStart']
        cases.append(('one line per moment: session start, then the switchboard '
                      'for the prompt, both tool-call moments and the end of a reply',
                      names == sorted(['SessionStart', 'UserPromptSubmit', 'PreToolUse',
                                       'PostToolUse', 'Stop'])
                      and all('precedent_run_repo_hooks.py' in c for c in switch),
                      pairs))
        cases.append(('no switchboard line swallows a refusal with "|| true"',
                      switch and not any('|| true' in c for c in switch), switch))
        cases.append(('what the file held is kept, and an older script\'s '
                      'one-gate line is gone so nothing runs twice',
                      got.get('permissions') == {'allow': ['Bash(ls)']}
                      and not any('precedent_global_gate.sh' in c for c in cmds), got))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the cloud setup script writes each hook once ({len(cases)} '
          f'stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_push_check_streams_a_gate_progress_live():
    """precedent_push_check.run() passes a gate's stderr through while the
    gate is still running -- it captured everything, so verify_harness's
    progress and time-remaining lines were invisible for about four minutes
    (practice: slow-steps-report-and-cache; very deep check, 2026-09-28).
    Planted: a gate that prints a progress line to stderr and then waits for
    a file that only this process's stderr creates on seeing that line, so
    it passes only if the line arrived while the gate was alive. Control: a
    failing gate's stdout and stderr still both reach its failure report."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='push-check-stream-'))
    cases = []
    try:
        (tmp / 'gates').mkdir()
        sentinel = tmp / 'seen'
        (tmp / 'gates' / 'slow.py').write_text(
            'import pathlib, sys, time\n'
            'print("  -- 1/2 checks done, ~3s remaining", file=sys.stderr, '
            'flush=True)\n'
            'deadline = time.monotonic() + 8\n'
            f'while not pathlib.Path({str(sentinel)!r}).exists():\n'
            '    if time.monotonic() > deadline:\n'
            '        print("progress was not seen live"); sys.exit(1)\n'
            '    time.sleep(0.05)\n'
            'print("slow gate done")\n', encoding='utf-8')
        (tmp / 'gates' / 'bad.py').write_text(
            'import sys\nprint("VIOLATION: zz-out-line")\n'
            'print("zz-err-line", file=sys.stderr)\nsys.exit(1)\n',
            encoding='utf-8')

        class Watcher(io.StringIO):
            def write(self, text):
                if 'remaining' in text:
                    sentinel.write_text('x', encoding='utf-8')
                return super().write(text)

        err, out = Watcher(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            failed, missing, _total, _findings = ppc.run(tmp, [
                ('zz_slow', [sys.executable, 'gates/slow.py'], 'nothing'),
                ('zz_bad', [sys.executable, 'gates/bad.py'], 'nothing')])
        cases.append(('THE CASE: a gate\'s progress line reached stderr while '
                      'it ran', 'zz_slow' not in failed
                      and '~3s remaining' in err.getvalue(),
                      f'failed={failed} err={err.getvalue()[:300]}'))
        cases.append(('CONTROL: a failing gate is still reported with its '
                      'stdout and stderr', failed == ['zz_bad']
                      and 'zz-out-line' in out.getvalue()
                      and 'zz-err-line' in out.getvalue(),
                      f'failed={failed} out={failure_detail(out.getvalue(), 400)}'))
        cases.append(('nothing is reported missing', missing == [],
                      repr(missing)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the push check shows a long gate\'s progress as it runs '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_full_tier_needs_a_reason_on_a_quick_landing():
    """`--tier full` is refused where the landing branch takes the quick
    tier, unless a reason is given (Morgan, 2026-10-01, strength: decided:
    "Go, do both, then Booked"). The same day the bare run was fixed, a
    session still typed `--tier full` before every quick landing and
    wrote it into its helpers' briefs. Stated cases: refused on a quick
    landing (staging); allowed with --because; untouched for --gate, for
    a named push, and on a landing branch that is fully checked."""
    import tempfile
    import precedent_push_check as ppc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='full-tier-reason-'))
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)

        def landing(branch):
            (tmp / 'precedent.json').write_text(json.dumps(
                {'base_branch': 'main', 'landing_branch': branch}), encoding='utf-8')
        # The quick landing is staging, for a person who lands there.
        (tmp / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'main', 'staging_branch': 'staging',
             'landing_branch': 'staging', 'promote_only': True}), encoding='utf-8')
        full = ['--tier', 'full']
        cases.append(('refused on a quick landing (staging, for a person who '
                      'lands there)',
                      bool(ppc._full_tier_refusal(tmp, full)), ''))
        cases.append(('...and the refusal says how to ask anyway',
                      '--because' in (ppc._full_tier_refusal(tmp, full) or ''), ''))
        for extra in (['--because', 'testing'], ['--gate'],
                      ['--push-command', 'origin HEAD:staging']):
            cases.append((f'allowed with {extra[0]}',
                          ppc._full_tier_refusal(tmp, full + extra) is None, ''))
        cases.append(('--tier basic is never refused',
                      ppc._full_tier_refusal(tmp, ['--tier', 'basic']) is None, ''))
        cases.append(('--because is a known option',
                      ppc.unknown_arguments(full + ['--because', 'x']) == [], ''))
        # main is quick before the push since 2026-10-17, so --tier full
        # there needs its reason as staging's does.
        landing('main')
        cases.append(('refused on a landing branch of main too, which is '
                      'quick before the push since 2026-10-17',
                      bool(ppc._full_tier_refusal(tmp, full)), ''))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'--tier full needs a reason where the landing branch is quick '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_bare_push_check_takes_the_landing_tier():
    """precedent_push_check.py run with no destination checks what a push
    to the person's landing branch gets (Morgan, 2026-10-01, strength:
    assented). A session ran it bare before every quick landing and paid
    the ~11-minute suite each time. Stated cases: bare, with a quick
    landing -- staging, for a person who lands there -- it becomes a push
    there at the basic tier; a landing on main still runs full; --tier full and a named
    push are left exactly as given."""
    import contextlib, io, tempfile
    import precedent_push_check as ppc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='bare-push-check-'))
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)

        def landing(branch):
            (tmp / 'precedent.json').write_text(json.dumps(
                {'base_branch': 'main', 'staging_branch': 'staging',
                 'landing_branch': branch, 'promote_only': True}),
                encoding='utf-8')
        # The quick landing is staging, for a person who lands there.
        landing('staging')
        with contextlib.redirect_stdout(io.StringIO()):
            argv = ppc._default_destination(tmp, [])
        cases.append(('bare, it names a push to the landing branch',
                      argv == ['--push-command', 'origin HEAD:staging'], str(argv)))
        cases.append(('...which is the basic tier',
                      ppc._tier_from_args(tmp, argv)[0] == ppc.BASIC,
                      str(ppc._tier_from_args(tmp, argv))))
        (tmp / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'main', 'landing_branch': 'main'}), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            argv = ppc._default_destination(tmp, [])
        # Since 2026-10-17 a push to main takes the quick checks too, and the
        # full suite runs after it (Morgan: "the full tests should happen
        # after that"); a landing branch of main is no longer fully checked
        # before the push.
        cases.append(('a landing branch of main takes the quick checks too',
                      ppc._tier_from_args(tmp, argv)[0] == ppc.BASIC,
                      str(ppc._tier_from_args(tmp, argv))))
        for given in (['--tier', 'full'], ['--push-command', 'origin x']):
            cases.append((f'{given} is left as given',
                          ppc._default_destination(tmp, list(given)) == given, ''))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a bare push check takes the landing branch\'s tier '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_push_check_refuses_an_unknown_option():
    """precedent_push_check.py refuses an option it does not know, exit 2,
    naming the ones it does -- and still takes every one it reads.

    Found 2026-09-30: the pull request template named
    `precedent_push_check.py --changed-files-only`, an option this file
    never had. It was ignored silently and the full ~14-minute suite ran,
    twice, where a seconds-long quick check was meant."""
    import precedent_push_check as ppc
    t0 = time.time()
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_push_check.py'),
                        '--changed-files-only'], capture_output=True, text=True,
                       cwd=str(ROOT), timeout=60)
    cases = [
        ('an unknown option exits 2', r.returncode == 2, str(r.returncode)),
        ('and names itself and the valid ones',
         '--changed-files-only' in r.stderr and '--push-command' in r.stderr,
         r.stderr[-300:]),
        ('and runs nothing', time.time() - t0 < 30 and 'passed in' not in r.stdout,
         r.stdout[-200:]),
        ('the hook\'s own arguments are all known',
         ppc.unknown_arguments(['--gate', '--push-command', 'origin staging']) == [], ''),
        ('--changed-files-check takes its REF, or none',
         ppc.unknown_arguments(['--changed-files-check', 'origin/x', '--list']) == []
         and ppc.unknown_arguments(['--changed-files-check', '--gate']) == [], ''),
        ('the merge gate\'s arguments are all known',
         ppc.unknown_arguments(['--gate', '--tier', 'full']) == []
         and ppc.unknown_arguments(['--changed-since', 'origin/staging']) == [], ''),
        ('a stray positional is refused too',
         ppc.unknown_arguments(['--gate', 'oops']) == ['oops'], ''),
    ]
    failed = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'precedent_push_check.py refuses an unknown option ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_push_check_runs_cheap_checks_first():
    """precedent_push_check.run() moves the slow checks (the harness suite,
    the deep-check suites) behind every fast one, and skips them once a fast
    one has failed -- the push is refused either way. Origin 2026-09-28: a
    merge gate spent ten minutes on the harness suite before reporting stale
    generated views, a one-second finding, then ten more on the fixed push.
    Asserted on the function itself, with stand-in checks that record the
    order they ran in."""
    name = 'the push check runs its slow checks last, and not after a fast failure'
    tool = ROOT / 'tools' / 'precedent_push_check.py'
    if not tool.is_file():
        not_applicable(name, 'precedent_push_check.py is absent')
        return
    spec = importlib.util.spec_from_file_location('ppc_cheap_first', tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import tempfile as _tf
    bad = []
    with _tf.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        log = d / 'order.txt'
        def stand_in(label, code):
            f = d / f'{label}.py'
            f.write_text(f'open({str(log)!r}, "a").write({label!r} + "\\n")\n'
                         f'raise SystemExit({code})\n')
            return (label, [sys.executable, str(f)], 'stand-in')
        checks = [stand_in('verify_harness', 0), stand_in('fast_ok', 0), stand_in('fast_bad', 1),
                  stand_in('deep_check', 0)]
        env_all = os.environ.pop('PRECEDENT_PUSH_CHECK_ALL', None)
        try:
            import contextlib as _cl, io as _io
            with _cl.redirect_stdout(_io.StringIO()):
                failed, _m, _t, _f = mod.run(d, checks)
            ran = log.read_text().split()
            if ran != ['fast_ok', 'fast_bad']:
                bad.append(f'with a fast failure, ran {ran}, expected the fast checks only')
            if failed != ['fast_bad']:
                bad.append(f'reported {failed} as failed')
            log.unlink()
            os.environ['PRECEDENT_PUSH_CHECK_ALL'] = '1'
            with _cl.redirect_stdout(_io.StringIO()):
                mod.run(d, checks)
            ran = log.read_text().split()
            if ran != ['fast_ok', 'fast_bad', 'verify_harness', 'deep_check']:
                bad.append(f'under PRECEDENT_PUSH_CHECK_ALL=1, ran {ran}')
        finally:
            os.environ.pop('PRECEDENT_PUSH_CHECK_ALL', None)
            if env_all is not None:
                os.environ['PRECEDENT_PUSH_CHECK_ALL'] = env_all
    check(name, not bad, '; '.join(bad))


def check_push_check_records_over_its_own_ledgers():
    """A push-check run that refreshes a fact ledger (practice: gate-ledger)
    still records its pass for the commit, and leaves the ledger in place;
    real uncommitted work still blocks the record.

    Origin 2026-10-02, a consumer repository: the model audit rewrote its
    ledger as the full suite ran, the suite passed in 799 s over a tree it
    had dirtied itself, the pass was NOT recorded, and the push gate ran
    the whole suite again and timed out -- twice. The fixture's doc_lint
    stand-in saves a ledger through the real fact_ledger.py, so the run
    dirties its own tree exactly that way. The negative control is the same
    run with an ordinary tracked file edited. Owns its state (practice:
    fixture-owns-its-state)."""
    import tempfile, json as _json, shutil as _shutil
    name = 'the push check records its pass over fact ledgers it refreshed itself'
    tool = ROOT / 'tools' / 'precedent_push_check.py'
    needed = [tool, ROOT / 'tools' / 'fact_ledger.py', ROOT / 'tools' / 'content_record.py']
    if not all(f.is_file() for f in needed):
        not_applicable(name, 'precedent_push_check.py or the fact ledger engine is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1', PRECEDENT_NO_SHARED_PASS='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'))
        env.pop('FACT_LEDGER_WRITTEN', None)

        def git(*a):
            return subprocess.run(['git', '-C', str(work), *a], capture_output=True,
                                  text=True, env=env).stdout.strip()

        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(work)], env=env,
                       capture_output=True)
        for f in needed + [ROOT / 'tools' / 'precedent_branches.py']:
            if f.is_file():
                _shutil.copy2(f, work / 'tools' / f.name)
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer'}), encoding='utf-8')
        for t in ('precedent_check', 'leak_gate', 'doc_lint'):
            body = 'import sys\n'
            if t == 'precedent_check':
                body += 'print("precedent_check: 3 passed, 0 violated")\n'
            if t == 'doc_lint':
                # a gate that refreshes its fact ledger as it runs, as the
                # model audit and doc_sync do
                body += ('import importlib.util, pathlib, time\n'
                         'here = pathlib.Path(__file__).resolve().parent\n'
                         'spec = importlib.util.spec_from_file_location("fl", here / "fact_ledger.py")\n'
                         'fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)\n'
                         'led = fl.Ledger(here.parent, "audit_ledger.jsonl")\n'
                         'led.put({"doc": "m.py", "block": "#audit", "at": time.time_ns()})\n'
                         'led.save()\n')
            body += 'sys.exit(0)\n'
            (work / 'tools' / f'{t}.py').write_text(body, encoding='utf-8')
        (work / 'audit_ledger.jsonl').write_text('', encoding='utf-8')
        (work / 'notes.txt').write_text('a\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'init')
        record = work / '.git' / 'precedent-push-check.json'

        def run_check(*a):
            p = subprocess.run([sys.executable, 'tools/precedent_push_check.py', *a],
                               cwd=work, capture_output=True, text=True, env=env)
            return p.stdout + p.stderr

        out = run_check('--tier', 'full', '--because', 'the ledger test')
        dirty = git('status', '--porcelain', '--untracked-files=no')
        cases.append(('the run dirtied its own tree with the ledger (the bug\'s '
                      'precondition)', dirty.endswith('audit_ledger.jsonl')))
        cases.append(('and still recorded the pass for the commit',
                      'recorded for tree' in out and 'NOT recorded' not in out
                      and record.is_file()))
        cases.append(('saying it refreshed the ledger and left it to commit',
                      'refreshed 1 fact ledger' in out and 'audit_ledger.jsonl' in out))
        cases.append(('the refreshed ledger is left in place, not discarded',
                      bool((work / 'audit_ledger.jsonl').read_text().strip())))
        out = run_check('--gate', '--tier', 'full')
        cases.append(('the push gate then finds the pass, the ledger still '
                      'uncommitted, and runs nothing', 'already passed' in out))

        # Negative control: real uncommitted work blocks the record, before
        # or after a ledger refresh, and the gate does not reuse the pass.
        record.unlink(missing_ok=True)
        (work / 'notes.txt').write_text('b\n', encoding='utf-8')
        out = run_check('--tier', 'full', '--because', 'the ledger test')
        cases.append(('an edited tracked file still blocks the record',
                      'NOT recorded' in out and not record.is_file()))
        out = run_check('--gate', '--tier', 'full')
        cases.append(('and the gate runs the suite rather than reuse a pass',
                      'already passed' not in out))
        git('checkout', '--', 'notes.txt')
        git('commit', '-q', '-am', 'commit the ledger')
        out = run_check('--tier', 'full', '--because', 'the ledger test')
        cases.append(('a run over a committed ledger records as before',
                      'recorded for tree' in out))
    bad = [c for c, ok in cases if not ok]
    check(name, not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_push_check_installs_gate_packages():
    """precedent_push_check.py installs the packages the gates import before
    it runs anything, and stops at once, naming them, when it cannot --
    rather than letting verify_harness fail minutes later without saying a
    package was absent (2026-09-14, 2026-09-26). Hermetic: import and install
    are stubbed, so nothing is fetched (practice: control-asserts-which-failure:
    the present case never calls the installer)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    cases, calls = [], []
    have = {'present'}
    ok, note = ppc.ensure_gate_packages(('present',), have.__contains__,
                                        lambda m: calls.append(list(m)) or '')
    cases.append(('all present: ok, silent, installer never called',
                  ok and note == '' and not calls, f'{ok} {note!r} {calls}'))
    ok, note = ppc.ensure_gate_packages(
        ('present', 'absent'), have.__contains__,
        lambda m: (calls.append(list(m)), have.update(m))[1] or '')
    cases.append(('one missing: installs exactly that one and says so',
                  ok and calls[-1] == ['absent'] and 'installed absent' in note,
                  f'{ok} {note!r} {calls}'))
    ok, note = ppc.ensure_gate_packages(('gone',), lambda m: False,
                                        lambda m: 'no network')
    cases.append(('install fails: not ok, and the note names the package',
                  not ok and 'gone' in note and 'pip install gone' in note,
                  f'{ok} {note!r}'))
    cases.append(('the list matches the session check\'s row',
                  ppc.GATE_PACKAGES == ('cmarkgfm', 'markdown'), ''))
    # ...and both startup scripts install every one of them. A fresh
    # consumer container installed cmarkgfm alone, and the session check
    # reported "missing markdown" at every session start (2026-10-01, from
    # a consumer's Update Vendors).
    import re as _re
    for rel in ('templates/bootstrap.sh', 'tools/bootstrap.sh'):
        text = (ROOT / rel).read_text(encoding='utf-8')
        m = _re.search(r'^\s*pip install --quiet ([^\n|]*?)\s*2>', text, _re.M)
        got = set(m.group(1).split()) if m else set()
        cases.append((f'{rel} installs every gate package',
                      set(ppc.GATE_PACKAGES) <= got, f'installs {sorted(got)}'))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the push check installs the gate packages or stops naming them '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))

def _push_gate_fixture(tmp, real_modules=()):
    """A consumer-shaped repository with a bare origin, for the push-check
    cases below. The basic tier's checks are stand-ins, except the modules
    named in `real_modules` ('*' for every one), copied from this engine,
    and the leak gate and lint, which always pass. The author check is a
    full-history stand-in, the shape an older vendored copy has, flagging
    every commit by 'Mallory'; the workflow check flags every workflow file
    that APPROVED does not name, in precedent_check's own output shape.
    -> (work, env, git)."""
    import json as _json, shutil as _shutil
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
               GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
               PRECEDENT_NO_SHARED_PASS='1')

    def git(cwd, *a, **kw):
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=dict(env, **kw))

    origin, work = tmp / 'origin.git', tmp / 'work'
    git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
    git(tmp, 'init', '-q', '-b', 'main', str(work))
    git(work, 'remote', 'add', 'origin', str(origin))
    tools = work / 'tools'
    (tools / 'checks').mkdir(parents=True)
    if real_modules == '*':
        real_modules = tuple(p.stem for p in (ROOT / 'tools').glob('*.py')
                             if p.name != 'verify_harness.py')
    for m in ('precedent_push_check', 'precedent_branches', *real_modules):
        _shutil.copy2(ROOT / 'tools' / f'{m}.py', tools / f'{m}.py')
    (tools / 'ENGINE_MANIFEST.json').write_text(
        _json.dumps({'kind': 'consumer'}), encoding='utf-8')
    for t in ('leak_gate', 'doc_lint'):
        (tools / f'{t}.py').write_text('import sys\nsys.exit(0)\n', encoding='utf-8')
    if 'precedent_check' not in real_modules:
        (tools / 'precedent_check.py').write_text(
            'import pathlib, sys\n'
            'if __name__ == "__main__":\n'
            '    bad = []\n'
            '    if "ci-workflow-approved" in sys.argv:\n'
            '        ok = pathlib.Path("APPROVED").read_text().split() '
            'if pathlib.Path("APPROVED").exists() else []\n'
            '        wf = pathlib.Path(".github/workflows")\n'
            '        bad = sorted(f"{p}" for p in wf.glob("*.yml") '
            'if p.name not in ok) if wf.is_dir() else []\n'
            '    if bad:\n'
            '        print("\\nVIOLATION  ci-workflow-approved")\n'
            '        for b in bad:\n'
            '            print(f"    {b}: has no approval")\n'
            '        print("  the rule:")\n'
            '        print("    a workflow needs the person\'s words")\n'
            '    print("\\nprecedent_check: %d passed, %d violated" '
            '% (0 if bad else 1, 1 if bad else 0))\n'
            '    sys.exit(1 if bad else 0)\n', encoding='utf-8')
    (tools / 'check_commit_author.py').write_text(
        '#!/usr/bin/env python3\n'
        '"""Stand-in: every commit reachable from HEAD, as older copies read."""\n'
        '# practice: planted-author-rule\n'
        'import subprocess, sys\n'
        'log = subprocess.run(["git", "log", "--format=%H|%an"], '
        'capture_output=True, text=True).stdout.split()\n'
        'bad = [l.split("|")[0] for l in log if l.endswith("|Mallory")]\n'
        'if bad:\n'
        '    print("VIOLATION: planted-author-rule")\n'
        '    for sha in bad:\n'
        '        print(f"  commit {sha[:12]}: author is \'Mallory\', expected \'T\'")\n'
        '    print("\\nthe rule:\\n  commits carry the declared author")\n'
        '    sys.exit(1)\n', encoding='utf-8')
    git(work, 'add', '-A')
    git(work, 'commit', '-q', '-m', 'init')
    return work, env, git


def check_push_gate_judges_only_what_a_working_branch_brings():
    """A push to a working branch is refused over what it brings, never over
    findings already on origin's tier branches.

    2026-09-28, a consumer: the push gate's basic tier refused a push of a
    claude/* branch -- commit_author over two old commits already on main,
    ci_workflows over a workflow already on main -- and the Stop hook
    refused to end the turn with the commit unpushed. The session could
    neither push nor stop until the person answered, and nothing the push
    could do would have fixed either finding."""
    import tempfile
    name = ('a working-branch push is judged on what it brings; findings '
            'already on a tier branch are reported, not blocking')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work, env, git = _push_gate_fixture(tmp)

        def push_check(dest):
            p = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                                '--gate', '--push-command', f'origin {dest}'],
                               cwd=work, capture_output=True, text=True, env=env,
                               timeout=300)
            return p.returncode, p.stdout + p.stderr

        (work / 'm.txt').write_text('old\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'an old commit by someone else',
            GIT_AUTHOR_NAME='Mallory', GIT_AUTHOR_EMAIL='m@example.com')
        (work / '.github' / 'workflows').mkdir(parents=True)
        (work / '.github' / 'workflows' / 'old.yml').write_text('on: push\n',
                                                               encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'an old unapproved workflow')
        git(work, 'push', '-q', 'origin', 'main')
        git(work, 'checkout', '-q', '-b', 'claude/fix')
        (work / 'fix.txt').write_text('fix\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'the session\'s own fix')

        rc, out = push_check('claude/fix')
        cases.append(('a claude/* branch bringing a clean commit onto main\'s '
                      'old findings is let through, and says what it found'
                      f' (exit {rc}: {out.strip().splitlines()[-1:]})',
                      rc == 0 and 'reported, not blocking' in out
                      and 'commit_author' in out and 'ci_workflows' in out))
        rc, _ = push_check('main')
        cases.append(('the same findings still refuse a push to main, a tier '
                      'branch', rc == 1))

        (work / '.github' / 'workflows' / 'new.yml').write_text(
            'on: push\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'a new unapproved workflow')
        rc, out = push_check('claude/fix')
        cases.append(('a workflow the branch itself adds still refuses it, '
                      'naming that file', rc == 1 and 'new.yml' in out))
        git(work, 'reset', '-q', '--hard', 'HEAD~1')

        (work / 'm2.txt').write_text('new\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'a new commit by someone else',
            GIT_AUTHOR_NAME='Mallory', GIT_AUTHOR_EMAIL='m@example.com')
        new = git(work, 'rev-parse', 'HEAD').stdout.strip()
        rc, out = push_check('claude/fix')
        cases.append(('a wrong-author commit the branch brings still refuses '
                      'it, naming that commit', rc == 1 and new[:12] in out))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_push_check_runs_approved_workflow_steps():
    """The push check runs each plain `python3 tools/<x>.py` step of a
    workflow the repo keeps in precedent.json's github_ci_approved, in its
    full tier and never before a push (since 2026-10-17); never a workflow the engine installs, a step calling an engine
    file, or a tool its own list already runs; and names each other step
    once.

    WHY. 2026-10-10, a consumer's Update Vendors and Produce: every local
    tier passed a change its own platform-docs-check.yml then failed as
    GitHub's test on the pull request into main -- a fix and a second
    Produce. Nothing local ran that workflow's check.

    Negative control, measured 2026-10-10: on staging's code there is no
    approved_workflow_checks, and plan() lists none of these steps."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        wf = repo / '.github' / 'workflows'
        wf.mkdir(parents=True)
        (repo / 'tools').mkdir()
        (wf / 'own-check.yml').write_text(
            'jobs:\n  check:\n    steps:\n'
            '      - uses: actions/checkout@v4\n'
            '      - name: Docs are current\n'
            '        run: python3 tools/check_docs.py --strict\n'
            '      - name: Two at once\n'
            '        run: |\n'
            '          python3 tools/build_a.py --check\n'
            '          python3 tools/build_b.py --check\n'
            '      - name: Engine step\n'
            '        run: python3 tools/precedent_check.py\n'
            '      - name: A shell check\n'
            '        run: |\n'
            '          test -s README.md\n'
            '          grep -q x README.md\n'
            '      - name: Setup\n'
            '        run: python -m pip install pyyaml\n', encoding='utf-8')
        (wf / 'light-check.yml').write_text(
            'jobs:\n  c:\n    steps:\n      - run: python3 tools/light.py\n',
            encoding='utf-8')
        (wf / 'unapproved.yml').write_text(
            'jobs:\n  c:\n    steps:\n      - run: python3 tools/never.py\n',
            encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'github_ci_approved': {
            '.github/workflows/own-check.yml': {'sha256': 'x', 'approved_by': 'p'},
            '.github/workflows/light-check.yml': {'sha256': 'x', 'approved_by': 'p'}}}),
            encoding='utf-8')
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'files': ['precedent_check.py'], 'ci_workflow_files': []}), encoding='utf-8')
        checks, unrun = (ppc.approved_workflow_checks(repo)
                         if hasattr(ppc, 'approved_workflow_checks') else ([], []))
        argvs = [c[1][1:] for c in checks]
        cases.append(('a plain step, with its arguments, is a check',
                      ['tools/check_docs.py', '--strict'] in argvs, argvs))
        # They are tests, so the full tier runs them and the quick tier never
        # does (2026-10-17: they had run at every tier, outside BASIC_CHECKS).
        man = repo / 'tools' / 'ENGINE_MANIFEST.json'
        kept = man.read_text(encoding='utf-8')
        man.write_text(json.dumps(dict(json.loads(kept), kind='consumer')),
                       encoding='utf-8')
        _k, full_plan = ppc.plan(repo, engine=repo / 'tools', tier=ppc.FULL)
        _k, basic_plan = ppc.plan(repo, engine=repo / 'tools', tier=ppc.BASIC)
        man.write_text(kept, encoding='utf-8')
        cases.append(('a workflow check runs in the full tier, never before a push',
                      any(n.startswith('workflow ') for n, _a, _r in full_plan)
                      and not any(n.startswith('workflow ') for n, _a, _r in basic_plan),
                      ([n for n, _a, _r in full_plan], [n for n, _a, _r in basic_plan])))
        cases.append(("each line of a block step is its own check",
                      ['tools/build_a.py', '--check'] in argvs
                      and ['tools/build_b.py', '--check'] in argvs, argvs))
        cases.append(('a step calling an engine file is left to the engine',
                      not any(a[0] == 'tools/precedent_check.py' for a in argvs), argvs))
        cases.append(('a workflow the engine installs is skipped, whatever the '
                      'manifest recorded', not any(a[0] == 'tools/light.py' for a in argvs),
                      argvs))
        cases.append(('an unapproved workflow is not read',
                      not any(a[0] == 'tools/never.py' for a in argvs), argvs))
        cases.append(('a shell step is named once, setup is not',
                      [(w, st) for w, st, _c in unrun]
                      == [('.github/workflows/own-check.yml', 'A shell check')], unrun))
        # 2026-10-10, a consumer whose workflows ARE its product (a live
        # sync with secrets): every step was called a missed check, and a
        # quoted argument was rejected outright.
        (wf / 'product.yml').write_text(
            'on:\n  push:\n    branches: [main]\njobs:\n  s:\n    steps:\n'
            '      - name: Sync\n        run: python3 tools/sync.py --live\n'
            '      - name: Verify the sync\n        run: php bin/verify.php\n',
            encoding='utf-8')
        (wf / 'button.yml').write_text(
            'on:\n  workflow_dispatch:\njobs:\n  s:\n    steps:\n'
            '      - name: Live test\n        run: python3 tools/live_test.py\n',
            encoding='utf-8')
        (wf / 'on-change.yml').write_text(
            'on: [pull_request]\njobs:\n  s:\n    steps:\n'
            '      - name: Record a failure\n'
            '        run: python3 tools/file_todo.py file "$RUN_URL" "$OUTCOME"\n'
            '      - name: Lint the docs\n'
            '        run: python3 tools/doc_check.py --root "docs dir" --strict\n'
            '      - name: Test with the run\n'
            '        run: python3 tools/test_run.py "$RUN_URL"\n'
            '      - name: Deploy\n        run: python3 tools/deploy.py\n',
            encoding='utf-8')
        approved = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        approved['github_ci_approved'].update({
            '.github/workflows/product.yml': {'sha256': 'x', 'approved_by': 'p',
                                              'role': 'deliverable'},
            '.github/workflows/button.yml': {'sha256': 'x', 'approved_by': 'p'},
            '.github/workflows/on-change.yml': {'sha256': 'x', 'approved_by': 'p'}})
        (repo / 'precedent.json').write_text(json.dumps(approved), encoding='utf-8')
        checks, unrun = ppc.approved_workflow_checks(repo)
        argvs = [c[1][1:] for c in checks]
        named = [(pathlib.Path(w).name, st) for w, st, _c in unrun]
        cases.append(('a workflow marked deliverable is neither run nor named',
                      not any(a[0] == 'tools/sync.py' for a in argvs)
                      and not any(w == 'product.yml' for w, _s in named), (argvs, named)))
        cases.append(('a button-only workflow is never a change\'s test',
                      not any(a[0] == 'tools/live_test.py' for a in argvs)
                      and not any(w == 'button.yml' for w, _s in named), (argvs, named)))
        cases.append(('a quoted argument is run, unquoted',
                      ['tools/doc_check.py', '--root', 'docs dir', '--strict'] in argvs, argvs))
        cases.append(('a step that is not a check is neither run nor named',
                      not any(a[0] in ('tools/deploy.py', 'tools/file_todo.py') for a in argvs)
                      and ('on-change.yml', 'Deploy') not in named
                      and ('on-change.yml', 'Record a failure') not in named, (argvs, named)))
        cases.append(('a check reading GitHub\'s environment is named, never run',
                      ('on-change.yml', 'Test with the run') in named
                      and not any(a[0] == 'tools/test_run.py' for a in argvs), (argvs, named)))
        # 2026-10-10, later: a product's alarm drill. Its steps ran only
        # after a failure and only from the button with an input set, and
        # one appended the words "alerting test" to a list; all three were
        # named as GitHub-only checks.
        (wf / 'drill.yml').write_text(
            'on:\n  push:\n  workflow_dispatch:\n    inputs:\n      drill:\n        type: boolean\n'
            'jobs:\n  s:\n    steps:\n'
            '      - name: File the alerting test as a todo item\n'
            '        if: ${{ (failure() || cancelled()) && inputs.drill }}\n'
            '        run: python3 tools/todo.py file "$RUN_URL"\n'
            '      - name: Report the alerting test\n'
            '        if: ${{ inputs.drill }}\n'
            '        run: gh issue create --title x\n'
            '      - name: Commit state\n'
            '        run: |\n'
            '          parts+=("file the alerting test as a todo item")\n'
            '          git commit -m "state"\n'
            '      - name: Run the tests even after a failure\n'
            '        if: ${{ always() }}\n'
            '        run: make test\n', encoding='utf-8')
        approved = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        approved['github_ci_approved']['.github/workflows/drill.yml'] = {
            'sha256': 'x', 'approved_by': 'p'}
        (repo / 'precedent.json').write_text(json.dumps(approved), encoding='utf-8')
        _c, unrun = ppc.approved_workflow_checks(repo)
        drill = [st for w, st, _c in unrun if w.endswith('drill.yml')]
        cases.append(('THE DISCRIMINATING CASE: steps that run only after a failure or '
                      'only on a manual input are not checks',
                      'File the alerting test as a todo item' not in drill
                      and 'Report the alerting test' not in drill, drill))
        cases.append(('words inside a quoted string are not what a step runs',
                      'Commit state' not in drill, drill))
        cases.append(('a test step run "always()" is still named',
                      'Run the tests even after a failure' in drill, drill))
        (wf / 'drill.yml').unlink()
        del approved['github_ci_approved']['.github/workflows/drill.yml']
        (repo / 'precedent.json').write_text(json.dumps(approved), encoding='utf-8')
        import precedent_update as _pu

        class _Rep:
            def __init__(self):
                self.lines = []

            def step(self, n, o):
                self.lines.append(o)
        rep = _Rep()
        _pu.approved_workflows_step(repo, rep)
        said = [l for l in rep.lines if 'only on GitHub' in l]
        cases.append(('Update Vendors names them in one line: a count and the files',
                      len(said) == 1 and '2 check step(s)' in said[0]
                      and 'on-change.yml' in said[0] and 'own-check.yml' in said[0]
                      and 'deliverable' in said[0], rep.lines))
    # In this repository, deep-check.yml's steps call tools the push check
    # already runs at its own tier, so a basic push never gains the suite.
    _kind, basic = ppc.plan(ROOT, tier=ppc.BASIC)
    cases.append(("BestPractice's own deep-check.yml adds nothing to a basic push",
                  not any(n.startswith('workflow ') for n, _a, _r in basic),
                  [n for n, _a, _r in basic]))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the push check runs the local steps of approved workflows '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_push_check_honours_not_binding():
    """precedent_push_check.py honours a repo's `not_binding` exactly as
    precedent_check.py does, by asking precedent_check's own
    load_exemptions().

    2026-09-28, a consumer: its precedent.json declared planted-author-rule not
    binding, precedent_check reported it EXEMPT, and the push check ran
    tools/checks/check_commit_author.py directly anyway and refused a push
    over two old commits already on main."""
    import tempfile, json as _json
    name = 'the push check honours not_binding the way precedent_check does'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # The real engine modules, so the exemption is read by
        # precedent_check itself.
        work, env, git = _push_gate_fixture(tmp, real_modules='*')
        # The practice the author check enforces is found by its checked_by,
        # never by a name the engine carries (2026-10-16).
        (work / 'practices').mkdir(exist_ok=True)
        (work / 'practices' / 'planted-author-rule.md').write_text(
            '---\nslug:        planted-author-rule\n'
            'checked_by:  tools/check_commit_author.py\n---\n## Rule\nx\n',
            encoding='utf-8')
        (work / 'm.txt').write_text('x\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'a commit by someone else',
            GIT_AUTHOR_NAME='Mallory', GIT_AUTHOR_EMAIL='m@example.com')

        def push_check():
            p = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                                '--tier', 'basic'], cwd=work, capture_output=True,
                               text=True, env=env, timeout=300)
            return p.returncode, p.stdout + p.stderr

        rc, out = push_check()
        cases.append(('with no exemption the author check still refuses',
                      rc == 1 and 'commit_author' in out))
        reason = 'many people commit here, so no one author binds it'
        (work / 'precedent.json').write_text(_json.dumps(
            {'not_binding': [{'slug': 'planted-author-rule', 'reason': reason}]}),
            encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'declare planted-author-rule not binding')
        pc = subprocess.run([sys.executable, '-c',
                             'import sys; sys.path.insert(0, "tools"); '
                             'import precedent_check as pc; '
                             'print(sorted(pc.load_exemptions()[0]))'],
                            cwd=work, capture_output=True, text=True, env=env)
        cases.append(("precedent_check's own load_exemptions() reads it as "
                      "exempt (the fixture is real)",
                      "['planted-author-rule']" in pc.stdout))
        rc, out = push_check()
        cases.append((f'declared not binding, the push check skips it, says '
                      f'EXEMPT with the reason, and passes (exit {rc})',
                      rc == 0 and 'EXEMPT' in out and reason in out))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_lander_lands_where_booked_does_and_says_why_a_push_failed():
    """The queue lander lands on the landing branch, stops on a refused push
    with its reason, and takes no vendor step under --no-vendor.

    2026-10-10, a consumer whose precedent.json says "landing_branch":
    "staging" and has no lander block: land_next.py landed a docs branch on
    main, because it read only base_branch. Its three attempts each said
    "master moved" while the trunk sat still -- a pre-push hook refused
    every push and its reason was thrown away. And with --no-vendor it still
    took the vendor step once the branch landed. The fixture is a scratch
    origin with main and staging, and a lander from this engine.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-lander-trunk-'))
    cases = []
    try:
        script = tmp / 'run.py'
        script.write_text(f"""
import json, os, pathlib, subprocess, sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                  PRECEDENT_USER_CONFIG={str(tmp / 'no-config.json')!r},
                  GIT_CONFIG_GLOBAL={str(tmp / 'gitconfig')!r})
pathlib.Path({str(tmp / 'gitconfig')!r}).write_text('')
import land_next as ln, land_queue
td = pathlib.Path({str(tmp)!r})
ln.report_failure = lambda *a: ''
ln.retry_pause = lambda attempt: None
origin, work = td / 'o.git', td / 'w'
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g = lambda *a: ln.git(work, *a)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
g('add', '-A'); g('commit', '-qm', 'base'); g('push', '-q', 'origin', 'main')
g('push', '-q', 'origin', 'main:staging')
out = {{'trunk': ln.lander_config(work)['trunk']}}
ln.TRUNK = out['trunk']
def queue(b, f):
    g('checkout', '-q', '-B', b, 'origin/staging'); (work / f).write_text(f)
    g('add', '-A'); g('commit', '-qm', b); g('push', '-q', 'origin', b)
    g('checkout', '-q', '--detach', 'origin/staging')
    land_queue.request(store, b, repo=work)
store = land_queue._store(work)
vend = td / 'vend.py'
vend.write_text("import pathlib; pathlib.Path({str(tmp / 'vendored')!r}).write_text('1'); print('VENDORS: updated')\\n")
queue('feat/docs', 'docs.md')
rc = ln.land_queue_run(work, vendor=False, gates=[], push_check=['true'], bestpractice=None,
                       store=store, sync_cmd=None, vendor_cmd=['python3', str(vend)])
g('fetch', '-q', 'origin', 'main', 'staging')
out['landed'] = dict(rc=rc, on_staging='docs.md' in g('ls-tree', '--name-only', 'origin/staging').stdout,
                     on_main='docs.md' in g('ls-tree', '--name-only', 'origin/main').stdout,
                     vendored=(td / 'vendored').exists())
hook = origin / 'hooks' / 'pre-receive'
hook.write_text('#!/bin/sh\\nwhile read o n r; do [ "$r" = refs/heads/staging ] || continue; '
                'echo "refused by the fixture hook: private name found" >&2; exit 1; done\\nexit 0\\n')
hook.chmod(0o755)
queue('feat/blocked', 'blocked.md')
attempts = []
real = ln.check_and_push
ln.check_and_push = lambda repo, pc: (attempts.append(1), real(repo, pc))[1]
rc = ln.land_queue_run(work, vendor=False, gates=[], push_check=['true'], bestpractice=None,
                       store=store, sync_cmd=None)
st = {{e['branch']: e for e in land_queue.entries(store)}}['feat/blocked']
out['refused'] = dict(rc=rc, attempts=len(attempts), status=st['status'], detail=st.get('detail', ''))
import precedent_branches as pb
pb._check = lambda *a, **k: (True, 'stub check')
g('fetch', '-q', 'origin')
said = []
rc, verdict = pb._land_composed(work, g('rev-parse', 'origin/feat/blocked').stdout.strip(),
                                'feat/blocked', 'staging', 'the fixture', said.append)
out['land'] = dict(rc=rc, verdict=verdict, said='\\n'.join(said))
print(json.dumps(out))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        ld, rf = out.get('landed') or {}, out.get('refused') or {}
        cases.append(('THE DISCRIMINATING CASE: landing_branch "staging" with no lander '
                      'block makes the trunk staging', out.get('trunk') == 'staging',
                      str(out.get('trunk')) if out else failure_detail(p.stdout + p.stderr, 1500)))
        cases.append(('...and the branch lands on staging, not main',
                      ld.get('rc') == 0 and ld.get('on_staging') and not ld.get('on_main'),
                      str(ld) or why))
        cases.append(('--no-vendor takes no vendor step, even after a landing',
                      ld and not ld.get('vendored'), str(ld)))
        cases.append(('a push the remote refuses, with the trunk still, is tried once',
                      rf.get('attempts') == 1 and rf.get('status') == 'failed', str(rf) or why))
        cases.append(('...and the failure says the trunk did not move and quotes the '
                      'refusal', 'did not move' in rf.get('detail', '')
                      and 'refused by the fixture hook' in rf.get('detail', ''),
                      failure_detail(rf.get('detail', ''), 300)))
        la = out.get('land') or {}
        cases.append(('--land, refused the same way, says staging did not move and '
                      'quotes the refusal (2026-10-11: it said "staging moved")',
                      la.get('rc') == 1 and 'did not move' in la.get('said', '')
                      and 'refused by the fixture hook' in la.get('said', '')
                      and 'moved while this ran' not in la.get('verdict', '')
                      and 'refused' in la.get('verdict', ''),
                      failure_detail(str(la), 500) or why))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the lander lands where Booked does and says why a push failed '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))


def check_stale_views_judged_on_what_a_push_brings():
    """views_sync is judged on what a push to a working branch brings: a
    stale view the fork point shows too is reported, one the push makes is
    still refused.

    WHY. 2026-10-06: a practice source a consumer declares moved, its views
    went stale, and a one-line content push to a feature branch was refused
    for it."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    check('views_sync is one of the checks judged on what a push brings',
          'views_sync' in ppc.RANGE_JUDGED, '')
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        (repo / 'tools').mkdir()
        stub = repo / 'tools' / 'views_stub.py'
        stub.write_text(
            'import pathlib, sys\n'
            'sys.path.insert(0, sys.argv[1])\n'
            'import precedent_sync_views as psv\n'
            'v = pathlib.Path("VIEW.md").read_text().strip()\n'
            'if v != "fresh":\n'
            '    print(psv.findings_block([f"VIEW.md is {v}"]), file=sys.stderr)\n'
            '    sys.exit("precedent_sync_views --check FAIL")\n', encoding='utf-8')
        (repo / 'VIEW.md').write_text('stale\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base, already stale')
        g('checkout', '-qb', 'work')
        (repo / 'content.md').write_text('one line\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'a content push')
        import precedent_sync_views as psv
        block = psv.findings_block(['AGENTS.md is stale', 'practices/x.md differs'])
        check('the real sync\'s --check findings read as finding lines',
              ppc.violation_lines((block + '\nprecedent_sync_views --check FAIL: '
                                   'x').splitlines())
              == ['AGENTS.md is stale', 'practices/x.md differs'], block)
        argv = [sys.executable, str(stub), str(ROOT / 'tools')]
        out = subprocess.run(argv, cwd=repo, capture_output=True, text=True)
        lines = (out.stdout + out.stderr).splitlines()
        check('a stale view the fork point shows too is not refused',
              ppc.already_landed(repo, argv, lines, ['main']) is not None, '')
        (repo / 'VIEW.md').write_text('hand-edited\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'a hand edit')
        out = subprocess.run(argv, cwd=repo, capture_output=True, text=True)
        lines = (out.stdout + out.stderr).splitlines()
        check('CONTROL: a view this push edits by hand is still refused',
              ppc.already_landed(repo, argv, lines, ['main']) is None, repr(lines))


def check_over_target_line_says_whose_load_and_how_to_break_it_down():
    """The over-target line names the file it measured, whose sessions load
    it, and the command that breaks it down entry by entry; the breakdown
    lists each resident entry and occasion group with its source.

    WHY. 2026-10-06, a consumer: every reply gate printed another set's
    session file as over target, which read as this session's own load,
    and with one number to go on the session proposed trimming a practice
    whose line was not in that file."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_gate as pg
    import session_load_trend as slt
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            work = pathlib.Path(td) / 'work'
            (work / 'tools').mkdir(parents=True)
            (work / 'tools' / 'session_load_budgets.json').write_text(json.dumps(
                {'surfaces': {'AGENTS.md': {'target': 50}}}), encoding='utf-8')
            (work / 'AGENTS.md').write_text(
                '# A\n\n## Resident block (~1 of 9 token budget)\n\n'
                '**big-rule.** ' + 'word ' * 120 + '\n\n**small-rule.** short.\n\n'
                '## Occasion index\n\n```\nWhen a thing happens:\n'
                '  one-rule — does one thing\n  two-rule — does two\n'
                'When another happens:\n  three-rule — three\n```\n',
                encoding='utf-8')
            got = pg._over_target(work, siblings=False)
            cases.append(('the line names the full path it measured',
                          len(got) == 1 and str(work / 'AGENTS.md') in got[0]))
            cases.append(('...whose sessions load it',
                          len(got) == 1 and 'loaded by this session' in got[0]))
            cases.append(('...and the breakdown command',
                          len(got) == 1 and '--breakdown AGENTS.md' in got[0]))
            rows = slt.breakdown(work, 'AGENTS.md')
            labels = [(k, l) for _n, k, l, _s in rows]
            cases.append(('the breakdown lists each resident entry, largest first',
                          labels[0] == ('resident', 'big-rule')
                          and ('resident', 'small-rule') in labels))
            cases.append(('...and each occasion group with its practices',
                          ('index', 'one-rule, two-rule') in labels
                          and ('index', 'three-rule') in labels))
            cases.append(('...and the parts add up to the file as the cap measures it',
                          sum(r[0] for r in rows) == slt.approx_tokens(
                              (work / 'AGENTS.md').read_text(encoding='utf-8'))))
    finally:
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'the over-target line says whose load it is and how to break it '
          f'down ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_gates_promise_no_override():
    """No gate that refuses a commit, push or merge tells the session it may
    go ahead by saying so: none of them has a way through.

    WHY. 2026-10-06, a consumer: push-check-gate.sh ended "To push anyway
    you must say so explicitly and say why", and there was no such
    override -- the push check itself says "do not push past it"."""
    bad = []
    for d in (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks',
              ROOT / '.claude' / 'hooks'):
        for f in sorted(d.glob('*.sh')):
            if re.search(r'anyway you must\s+say so', f.read_text(encoding='utf-8')):
                bad.append(str(f.relative_to(ROOT)))
    check('no gate promises an override it does not have', not bad,
          'still promising one: ' + ', '.join(bad))


def check_gate_refusals_are_worded_by_their_tools():
    """The commit, push and merge gates refuse in their tool's words, passed
    on by the hook, and carry no refusal prose of their own.

    WHY. 2026-10-07, a consuming repository's Update Vendors: the only change
    to three hooks was one closing sentence, and Claude Code's auto mode holds
    a commit touching a hook for a person's yes, so the person was asked to
    approve a rewording he could not judge -- in every repository, at every
    rewording. Planted: each hook asks its tool with --hook-reason and holds
    none of the tool's sentences; a fake tool's answer is what the hook
    denies with, word for word; a tool too old to answer still gets a refusal
    carrying its findings; each tool's own text carries the run's output."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import doc_lint as _dl
    import precedent_push_check as _ppc
    import precedent_merge_check as _pmc
    cases = []
    hooks = ROOT / 'tools'   # the real scripts, behind the stubs since 2026-10-07
    owned = {'doc-lint-gate.sh': 'FAILED on the Markdown staged',
             'push-check-gate.sh': 'Nothing lets a push past this',
             'merge-check-gate.sh': 'Nothing lets a merge past this',
             'commit-identity-push-gate.sh': 'asymmetry is the whole reason'}
    for name, phrase in owned.items():
        text = (hooks / name).read_text(encoding='utf-8')
        cases.append((f'{name} asks its tool for the words', '--hook-reason' in text))
        cases.append((f'{name} holds none of them', phrase not in text))
        cases.append((f'{name} is what .claude/hooks runs, through its stub',
                      (ROOT / '.claude' / 'hooks' / name).read_bytes()
                      == (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
                          / name).read_bytes()))
    cases.append(('doc_lint words its refusal around the findings',
                  'x.md:1: bad' in (_dl.hook_reason('refused', 'x.md:1: bad') or '')))
    cases.append(('the push check words a failure and a timeout',
                  'F1' in (_ppc.hook_reason('1', 'F1', top='/r') or '')
                  and 'cd /r' in (_ppc.hook_reason('124', '', top='/r') or '')
                  and _ppc.hook_reason('0', '') is None))
    cases.append(('the merge check words before and after the merge',
                  'F2' in (_pmc.hook_reason('1', 'F2') or '')
                  and (_pmc.hook_reason('landed-1', 'F3') or '').endswith('F3')
                  and _pmc.hook_reason('2', '') is None))
    # 2026-10-03 and 2026-10-05: a session read a refused `git commit &&
    # git push` as "committed, push refused". Each refusal now says, before
    # the findings, that nothing in the command ran.
    marker = 'FINDING-NR'
    for label, text in (('the commit gate', _dl.hook_reason('refused', marker) or ''),
                        ('the push gate on a failure', _ppc.hook_reason('1', marker) or ''),
                        ('the push gate on a timeout', _ppc.hook_reason('124', marker) or ''),
                        ('the merge gate', _pmc.hook_reason('1', marker) or ''),
                        ('the commit-identity push gate',
                         _ppc.hook_reason('identity', marker) or '')):
        said = text.find('Nothing in the refused command ran')
        cases.append((f'{label} says nothing in the refused command ran, before the findings',
                      0 <= said < text.find(marker) and 'git status' in text))
    fake = ('import sys\n'
            'if "--hook-reason" in sys.argv:\n'
            '    {answer}\n'
            'print("FINDING-7"); sys.exit(1)\n')
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        for label, answer, want in (
                ('the hook denies with the tool\'s words, word for word',
                 'sys.stdout.write("TOOL SAYS " + sys.stdin.read().strip()); sys.exit(0)',
                 lambda r: r == 'TOOL SAYS FINDING-7'),
                ('a tool too old to answer still gets a refusal with its findings',
                 'sys.exit(2)', lambda r: 'FINDING-7' in r and 'refused' in r)):
            repo = td / label[:12].replace(' ', '-')
            (repo / 'tools').mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
            (repo / 'tools' / 'precedent_push_check.py').write_text(
                fake.format(answer=answer), encoding='utf-8')
            payload = json.dumps({'tool_input': {'command': 'git push origin x'},
                                  'cwd': str(repo)})
            r = subprocess.run(['bash', str(hooks / 'push-check-gate.sh')], input=payload,
                               capture_output=True, text=True,
                               env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
            try:
                reason = json.loads(r.stdout)['hookSpecificOutput']['permissionDecisionReason']
            except (ValueError, KeyError):
                reason = ''
            cases.append((label, want(reason)))
        # The commit-identity push gate, run for real: a check that finds
        # something, and this repo's own tool wording the refusal.
        repo = td / 'identity'
        (repo / 'tools' / 'checks').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        shutil.copy(ROOT / 'tools' / 'precedent_push_check.py', repo / 'tools')
        (repo / 'tools' / 'check_commit_author.py').write_text(
            'print("AUTHOR-FINDING-9"); raise SystemExit(1)\n', encoding='utf-8')
        payload = json.dumps({'tool_input': {'command': 'git commit -m x && git push'},
                              'cwd': str(repo)})
        r = subprocess.run(['bash', str(hooks / 'commit-identity-push-gate.sh')],
                           input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
        try:
            reason = json.loads(r.stdout)['hookSpecificOutput']['permissionDecisionReason']
        except (ValueError, KeyError):
            reason = ''
        cases.append(('the commit-identity push gate denies in its tool\'s words, '
                      'saying nothing ran',
                      'commit-identity push gate REFUSED' in reason
                      and 0 <= reason.find('Nothing in the refused command ran')
                      < reason.find('AUTHOR-FINDING-9')))
        # A `git -C` on an earlier command names no repository pushed
        # (2026-10-28): the gate once read the command's first `-C` and
        # skipped every check on a push to this repo.
        other = td / 'other'
        subprocess.run(['git', 'init', '-q', str(other)], capture_output=True)
        payload = json.dumps({'tool_input': {'command':
                              f'git -C {other} status; git push origin x'},
                              'cwd': str(repo)})
        r = subprocess.run(['bash', str(hooks / 'commit-identity-push-gate.sh')],
                           input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
        cases.append(('an earlier `git -C <other> ...` does not skip the '
                      'commit-identity push gate', '"deny"' in r.stdout))
        payload = json.dumps({'tool_input': {'command':
                              f'git -C {other} push origin x'},
                              'cwd': str(repo)})
        r = subprocess.run(['bash', str(hooks / 'commit-identity-push-gate.sh')],
                           input=payload, capture_output=True, text=True,
                           env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
        cases.append(('while the push\'s own `git -C <other> push` still does',
                      '"deny"' not in r.stdout))
    bad = [n for n, ok in cases if not ok]
    check(f'the gates refuse in their tools\' words ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_load_ceiling_blocks_only_the_change_that_grew_it():
    """session-load-budget refuses an over-ceiling surface only when the
    change in scope grew it; growth from a source the change did not touch
    prints at the merge and push gates instead (S. Alexander Jacobson,
    2026-10-16). The discriminating case is the first: a consumer's
    session-start file over its ceiling, on a branch that touched neither
    precedent.json, its repo-local source nor the registry -- the filing
    record that was held off trunk for hours."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def approx(text):
        return len(text.split())

    class Ctx:
        def __init__(self, base, changed, base_text=None):
            self.base, self.changed, self._bt = base, changed, base_text

        def read_base(self, rel):
            return self._bt

    sp = '.precedent/SESSION_PRACTICES.md'
    grew = pc._change_grew_surface
    cases = [
        ('THE DISCRIMINATING CASE: the session-start file over its ceiling on '
         'a branch that touched none of its owned inputs is not this '
         'change\'s finding',
         not grew(Ctx('abc', ['patents/x.md']), sp, 334, approx)),
        ('the same file IS the change\'s when it touched precedent.json',
         grew(Ctx('abc', ['precedent.json']), sp, 334, approx)),
        ('...or the registry, which set the ceiling',
         grew(Ctx('abc', ['tools/session_load_budgets.json']), sp, 334, approx)),
        ('a tracked surface the change made bigger is the change\'s',
         grew(Ctx('abc', ['AGENTS.md'], 'a b c'), 'AGENTS.md', 5, approx)),
        ('a tracked surface already that size before the change is not',
         not grew(Ctx('abc', ['x.md'], 'a b c d e'), 'AGENTS.md', 5, approx)),
        ('a surface new in this change is the change\'s',
         grew(Ctx('abc', ['AGENTS.md'], None), 'AGENTS.md', 5, approx)),
        ('with no change in scope (a clean trunk sweep) it is reported as '
         'before',
         grew(Ctx(None, []), sp, 334, approx)),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'an over-ceiling surface blocks only the change that grew it '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_engine_tools_say_which_repo_they_read():
    """An engine tool run from inside ANOTHER repo says so, loudly, and names
    the repo it measured in every output mode (precedent_which_repo.py).

    THE COST IT PAID FOR (2026-09-29). A "Reduction pass" session ran
    `cd ~/precedent-individual && python3 ~/BestPractice/tools/session_load_trend.py`.
    The script reads the repo its own file lives in, so it reported
    BestPractice's figures under a header that named no repo, and the session
    told Morgan his individual set was over a ceiling when it was not
    (gotchas/gotcha-2026-09-29-engine-tools-measure-their-own-repo-not-the-cwd.md).

    Discriminating cases, both directions: from a different git repo the
    warning appears, names both repos and points at that repo's own copy of
    the tool; from inside ROOT, and from a directory in no repo at all, it
    does not. The measured repo's name is in the text header, the --since
    ledger header, and a `repo` field in --json."""
    import subprocess as _sp
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_which_repo as pwr
    script = ROOT / 'tools' / 'session_load_trend.py'
    mine = pwr.describe(ROOT)['name']
    cases = []

    def run(cwd, *extra):
        r = _sp.run([sys.executable, str(script), '--days', '1', '--cap', '2',
                     *extra], cwd=str(cwd), capture_output=True, text=True,
                    timeout=300)
        return r.stdout, r.stderr

    other = pathlib.Path(tempfile.mkdtemp()) / 'some-other-repo'
    bare = pathlib.Path(tempfile.mkdtemp())
    try:
        other.mkdir()
        _sp.run(['git', 'init', '-q', str(other)], check=True)
        (other / 'tools').mkdir()
        (other / 'tools' / 'session_load_trend.py').write_text('# stub\n')

        out, err = run(other)
        cases.append(('from another repo, the warning names both repos and '
                      'that repo\'s own copy',
                      'WRONG REPO' in err and mine in err
                      and 'some-other-repo' in err
                      and str(other / 'tools' / 'session_load_trend.py') in err,
                      err[:600]))
        cases.append(('the text header names the measured repo',
                      out.startswith(f'SESSION LOAD -- {mine}'), out[:300]))

        out, err = run(ROOT)
        cases.append(('from inside ROOT there is no warning',
                      'WRONG REPO' not in err, err[:600]))

        out, err = run(bare)
        cases.append(('from a directory in no repo there is no warning',
                      'WRONG REPO' not in err, err[:600]))

        out, err = run(other, '--json')
        try:
            repo = json.loads(out).get('repo') or {}
        except ValueError:
            repo = {}
        cases.append(('--json carries a repo field naming the measured repo',
                      repo.get('name') == mine, out[:300]))

        out, err = run(ROOT, '--since', 'HEAD')
        cases.append(('the --since ledger header names the measured repo',
                      out.startswith(f'REDUCTION LEDGER -- {mine}'), out[:300]))
        out, err = run(ROOT, '--since', 'HEAD', '--json')
        try:
            repo = json.loads(out).get('repo') or {}
        except ValueError:
            repo = {}
        cases.append(('--since --json carries the repo field too',
                      repo.get('name') == mine, out[:300]))

        leaky = pwr.origin_url  # credentials never reach a report
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            _sp.run(['git', 'init', '-q', str(d)], check=True)
            _sp.run(['git', '-C', str(d), 'remote', 'add', 'origin',
                     'https://x-access-token:' + 'tok' + '@github.com/o/r.git'],
                    check=True)
            url = leaky(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        cases.append(('an origin URL loses its credentials',
                      url == 'https://github.com/o/r', repr(url)))
    finally:
        shutil.rmtree(other.parent, ignore_errors=True)
        shutil.rmtree(bare, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'engine tools say which repo they read, and warn from another '
          f'repo ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_headroom_notice_watches_the_resident_block():
    """headroom_notice() also speaks when the generated resident block is
    near its own allocation, not only when a whole file nears its ceiling
    (very deep check, 2026-09-28: an individual set's block sat at ~539 of
    550 tokens, the file far from its ceiling, and nothing said so until a
    practice edit would have failed to build). Discriminating case: a block
    at 98% of its budget inside a file with no ceiling pressure at all."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import session_load_trend as slt
    real = slt.registry
    slt.registry = lambda: {'headroom_floor_pct': 5, 'surfaces': {}}
    cases = []
    try:
        for used, want in ((539, True), (440, False)):
            d = pathlib.Path(tempfile.mkdtemp())
            try:
                (d / 'AGENTS.md').write_text(
                    f'# x\n\n## Resident block (~{used} of 550 token budget, '
                    f'4 of 17 practices)\n\nbody\n', encoding='utf-8')
                note = slt.headroom_notice(root=d)
            finally:
                shutil.rmtree(d, ignore_errors=True)
            said = bool(note) and 'resident block' in note
            cases.append((f'a block at {used} of 550 is '
                          + ('reported' if want else 'left quiet'),
                          said == want, repr(note)))
    finally:
        slt.registry = real
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the headroom notice watches the resident block\'s own budget '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_update_on_stubs_stages_nothing_under_claude():
    """A consumer whose hooks are already the permanent stubs takes an
    update that changes a hook's real script (tools/push-check-gate.sh) and
    the engine's own wiring (tools/hook_wiring.json), and nothing under
    .claude/ is staged -- so there is no go-ahead to ask for. Whatever an
    update still stages there is named for what it is: a hook for a new
    event type, a settings.json path rewrite, a new hook file.

    WHY. 2026-10-08, from a consumer's Update Vendors: the update stopped
    for the person's yes on .claude/ changes after the move to stubs
    (2026-10-07) was meant to end that, and the question said only that
    files under .claude/ changed.

    Measured 2026-10-08: the first half already held on the landing branch (the
    stubs do keep .claude/ still), so it stands as a guard; the second half
    failed before harness_cases() -- the question named the paths only."""
    pu, _pve, _pr = _update_tools()
    fx = _LocalEditsFixture('precedent-stub-update-')
    cases = []
    try:
        proj = fx.tmp / 'installed'
        fx.sh('git', 'init', '-q', '-b', 'main', str(proj), cwd=fx.tmp)
        (proj / 'README.md').write_text('# Notes\n', encoding='utf-8')
        fx.commit(proj, 'before')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'precedent_install.py'), str(proj),
              '--project-name', 'Notes', cwd=ROOT)
        fx.commit(proj, 'installed')
        fx.sh('git', 'clone', '-q', '--bare', str(proj), str(fx.tmp / 'installed.git'),
              cwd=fx.tmp)
        fx.sh('git', 'remote', 'add', 'origin', str(fx.tmp / 'installed.git'), cwd=proj)
        fx.sh('git', 'fetch', '-q', 'origin', cwd=proj)
        hook = proj / '.claude' / 'hooks' / 'push-check-gate.sh'
        stubs = sorted(proj.glob('.claude/hooks/*.sh'))
        cases.append(('CONTROL: the install leaves every hook a stub',
                      hook.is_file() and stubs and all(
                          pu.STUB_MARKER in p.read_text(encoding='utf-8') for p in stubs),
                      [p.name for p in stubs]))
        seeded = json.loads((proj / 'tools' / 'ENGINE_MANIFEST.json')
                            .read_text(encoding='utf-8'))['source_commit']
        body = (ROOT / 'tools' / 'push-check-gate.sh').read_bytes()
        wiring = json.loads((ROOT / 'tools' / 'hook_wiring.json').read_text(encoding='utf-8'))
        wiring['consumer'] = list(wiring.get('consumer') or []) + [
            {'event': 'PreToolUse', 'matcher': 'Bash', 'script': 'wait-loop-gate.sh'}]
        # The install vendored this checkout's working tree; a practice
        # edited and not yet committed here would read as a local edit
        # against a commit built from HEAD, so the upstream commit carries
        # those files as they are on disk.
        dirty = subprocess.run(['git', '-C', str(ROOT), 'diff', '--name-only', 'HEAD',
                                '--', 'practices/'], capture_output=True,
                               text=True).stdout.split()
        changes = {rel: (ROOT / rel).read_bytes() for rel in dirty
                   if (ROOT / rel).is_file()}
        changes.update({
            'tools/push-check-gate.sh': body + b'\n# upstream changed what the hook does\n',
            'tools/hook_wiring.json': (json.dumps(wiring, indent=2) + '\n').encode()})
        rev = fx.upstream(seeded, changes)
        rc, out = fx.update(proj, rev)
        staged = fx.git(proj, 'diff', '--cached', '--name-only')
        cases.append(('CONTROL: the update took both changes, staged in tools/',
                      'tools/push-check-gate.sh' in staged
                      and 'tools/hook_wiring.json' in staged, (rc, staged, failure_detail(out, 800))))
        cases.append(('...and staged nothing under .claude/, so it asks nothing',
                      '.claude/' not in staged and 'hooks and settings' not in out,
                      (staged, failure_detail(out, 800))))

        # What is still staged there is named for what it is.
        repo = fx.tmp / 'named'
        fx.sh('git', 'init', '-q', '-b', 'main', str(repo), cwd=fx.tmp)
        stub = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' /
                'push-check-gate.sh').read_text(encoding='utf-8')
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / '.claude' / 'hooks' / 'push-check-gate.sh').write_text(stub, encoding='utf-8')
        cmd = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/push-check-gate.sh'
        settings = lambda d: (json.dumps({'hooks': d}, indent=2) + '\n')
        entry = lambda c, m=None: [dict({'hooks': [{'type': 'command', 'command': c}]},
                                        **({'matcher': m} if m else {}))]
        (repo / '.claude' / 'settings.json').write_text(
            settings({'PreToolUse': entry(cmd, 'Bash')}), encoding='utf-8')
        fx.commit(repo, 'stubs')
        (repo / '.claude' / 'settings.json').write_text(settings({
            'PreToolUse': entry('bash .claude/hooks/push-check-gate.sh', 'Bash'),
            'Notification': entry('"$CLAUDE_PROJECT_DIR"/.claude/hooks/notice-gate.sh')}),
            encoding='utf-8')
        (repo / '.claude' / 'hooks' / 'notice-gate.sh').write_text(stub, encoding='utf-8')
        fx.sh('git', 'add', '-A', cwd=repo)
        paths = pu.harness_changes(repo)
        got = pu.harness_cases(repo, paths)
        ask = pu.harness_ask(paths, cases=got)
        cases.append(('a hook for a new event type is named as one',
                      any('new event type, Notification' in c for c in got), got))
        cases.append(('a settings.json path rewrite is named as one',
                      any('rewrites the path of push-check-gate.sh' in c for c in got), got))
        cases.append(('a new hook file is named as one',
                      any(c == 'a new hook file, notice-gate.sh' for c in got), got))
        cases.append(('...and the question carries them',
                      'new event type' in ask and 'rewrites the path' in ask
                      and pu.HARNESS_GO_AHEAD in ask, ask))
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        fx.close()
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'an update on stub hooks stages nothing under .claude/, and names '
          f'whatever it does stage there ({len(cases)} stated cases)',
          not bad, '; '.join(bad)[:3000])


def check_size_cap_warning_names_the_cap():
    """The size-cap warning the push check ends on, and Update Vendors
    repeats, names the file, its measured size, the limit and the check
    tier that measured it, and points "above" at nothing.

    WHY. 2026-10-08, from a consumer's Update Vendors: the report said
    "over a session-load size cap (changed_practice, above)". A passing
    step's output is never printed, so "above" pointed nowhere, and the
    update kept only that first line -- no file, figure or limit.

    Negative control, measured 2026-10-08: before the fix the push check's
    line carried only the step name and ", above", and the update passed it
    on as it was -- every case but the controls failed."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_push_check as ppc
    finally:
        sys.path.pop(0)
    pu, _pve, _pr = _update_tools()
    cases = []
    saved = (list(ppc.CAP_WARNED), list(ppc.CAP_DETAILS))
    real = pu.check_with_merge_fallback
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-cap-warning-'))
    try:
        (tmp / 'step.py').write_text(
            'import sys\n'
            'print("\\nWARNING    session-load-budget \\u2014 over a size cap. The '
            'quick check lets it through; the full check refuses it.")\n'
            'print("    AGENTS.md: 6,549 tokens, every session, over its declared '
            'ceiling of 6,000. Run the reduction pass -- delete what is duplicated")\n'
            'print("  the rule:")\n'
            'print("build_views WARNING: resident block is ~2100 tokens, over the '
            '2000-token hard cap -- demote or retire a resident practice. Written '
            'anyway: the quick check lets it through", file=sys.stderr)\n',
            encoding='utf-8')
        ppc.CAP_WARNED[:], ppc.CAP_DETAILS[:] = [], []
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            failed, _m, _t, _f = ppc.run(tmp, [('changed_practice',
                                                [sys.executable, 'step.py'], 'x')])
            ppc._cap_warning_last('basic')
        line = next((l for l in buf.getvalue().splitlines()
                     if l.startswith('WARNING: over a session-load size cap')), '')
        cases.append(('CONTROL: the step passed and its warning was noticed',
                      not failed and ppc.CAP_WARNED == ['changed_practice'],
                      failure_detail(buf.getvalue(), 600)))
        cases.append(('the closing line names the file, its size and its limit',
                      'AGENTS.md: 6,549 tokens' in line and 'ceiling of 6,000' in line,
                      line))
        cases.append(('...and build_views\' loader-block cap, with its figures',
                      '~2100 tokens, over the 2000-token hard cap' in line, line))
        cases.append(('...and the tier and step that measured it, with no "above"',
                      "basic check's changed_practice step" in line
                      and 'above' not in line, line))

        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'precedent_push_check.py').write_text('', encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'main', 'landing_branch': 'staging'}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
        try:
            for said, want in ((line, 'AGENTS.md: 6,549 tokens'),
                               ('WARNING: over a session-load size cap '
                                '(changed_practice, above).', '(changed_practice)')):
                pu.check_with_merge_fallback = lambda _r, _rep, _a, _l, o=said: (
                    0, 'passed\n' + o + '\n')
                rep = pu.Report()
                with contextlib.redirect_stdout(io.StringIO()):
                    pu.closing_check(repo, rep)
                w = ' '.join(rep.warnings)
                cases.append((f'the update carries the check\'s line whole '
                              f'({"current" if said is line else "older"} wording), '
                              f'with no dangling "above"',
                              want in w and 'above' not in w, w))
        finally:
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
    finally:
        ppc.CAP_WARNED[:], ppc.CAP_DETAILS[:] = saved
        pu.check_with_merge_fallback = real
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the size-cap warning names the file, figure, limit and tier '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_push_destination_reaches_the_views_check():
    """The push check knows the branch a push goes to, so a set's commits
    are held to that rung (2026-10-05): from --push-command, the highest
    rung it writes to; --destination, which Promote passes, wins. The rung
    test is its own uncached step, never part of a recorded step's argv."""
    import precedent_push_check as ppc
    cases = [
        ('a push to a working branch and main is judged as main',
         ppc._destination(ROOT, ['--push-command', 'origin feat main']) == 'main'),
        ('a push to an ordinary branch is that branch',
         ppc._destination(ROOT, ['--push-command', 'origin HEAD:some-feature'])
         == 'some-feature'),
        ('--destination wins',
         ppc._destination(ROOT, ['--destination', 'staging', '--push-command',
                                 'origin main']) == 'staging'),
        ('no destination named, none assumed',
         ppc._destination(ROOT, ['--gate']) is None),
    ]
    orig = ppc.repo_kind
    try:
        ppc.repo_kind = lambda _e=None: 'consumer'
        steps = dict((n, v) for n, v, _r in ppc.plan(ROOT, tier='full')[1])
    finally:
        ppc.repo_kind = orig
    cases.append(('the recorded steps carry no destination, so a pass for one '
                  'branch is still reused for the same tree going to another '
                  '(the first version broke Promote\'s reuse of a full pass)',
                  'views_sync' in steps
                  and all('--for-branch' not in v for v in steps.values())))
    cases.append(('the rung step stands aside outside a consumer, and with no '
                  'destination', ppc._rung_refusal(ROOT, 'upstream', 'main') is None
                  and ppc._rung_refusal(ROOT, 'consumer', None) is None))
    bad = [c[0] for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_land_times_fallback_keeps_a_deleted_test_deleted():
    """The land tool's fallback for a conflicted harness timing list merges
    three ways, so a test one side deleted stays deleted.

    2026-10-19 (relayed root issue 4): precedent_branches._merge_times_file
    wrote the union of both sides, which brings a deleted test back -- the
    #1180/#1181 bug harness_times_merge.py was written to stop. Negative
    control: the union code keeps check_b and fails the first case."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    cases = []
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)
        env = {**os.environ, **_fixture_git_env()}
        g = lambda *a: subprocess.run(['git', '-C', str(w), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        f = w / pb.TIMES_FILE
        f.parent.mkdir(parents=True)
        def put(measured, secs):
            f.write_text(json.dumps({'measured': measured, 'seconds': secs},
                                    indent=1) + '\n', encoding='utf-8')
        put('base', {'check_a': 1.0, 'check_b': 2.0})
        g('add', '-A'); g('commit', '-qm', 'base')
        g('checkout', '-q', '-b', 'theirs')
        put('theirs added c', {'check_a': 1.0, 'check_b': 2.0, 'check_c': 3.0})
        g('commit', '-qam', 'add c')
        g('checkout', '-q', 'main')
        put('ours removed b', {'check_a': 1.0})
        g('commit', '-qam', 'drop b')
        conflicted = g('merge', '-q', 'theirs').returncode != 0
        wrote = pb._merge_times_file(w)
        got = json.loads(f.read_text(encoding='utf-8')) if wrote else {}
        secs = got.get('seconds') or {}
        cases.append(('THE DISCRIMINATING CASE: the test one side deleted '
                      'stays deleted', conflicted and wrote and 'check_b' not in secs,
                      str(got)))
        cases.append(('...and the test the other side added is kept',
                      secs.get('check_c') == 3.0 and secs.get('check_a') == 1.0,
                      str(got)))
        cases.append(('...and both sides\' notes are kept',
                      'theirs added c' in got.get('measured', '')
                      and 'ours removed b' in got.get('measured', ''), str(got)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the land tool\'s timing-list fallback merges three ways '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))


def check_consumer_rehearsal_smaller_faults():
    """Three smaller faults a consumer rehearsal found, 2026-10-03.

    1. precedent_push_check.py --tier with a name that is not a tier ran the
       full suite silently, skipping --tier full's --because refusal; it is
       refused now. CONTROL: --tier basic --list is not refused.
    2. precedent_update.py --from-ref took the engine from the ref and the
       catalogue from the tracked branch. checkin.py update takes the ref now:
       a ref that names no commit is refused by name, which only happens if
       it reached update().
    3. The follow-up for rules cited in other repositories called a rule a
       sync removed from a consumer's practices/ "deleted by this branch". A
       slug the base's committed MANIFEST.json recorded is skipped. CONTROL:
       one it did not record is still reported."""
    import tempfile, shutil, types
    import precedent_check as pc
    cases = []
    r = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                        '--tier', 'main'], cwd=str(ROOT), capture_output=True,
                       text=True, timeout=120)
    cases.append(('1: --tier main is refused as not a tier',
                  r.returncode == 1 and "'main' is not a tier" in r.stderr,
                  f'rc={r.returncode} {failure_detail(r.stderr, 200)}'))
    r = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                        '--tier', 'basic', '--list'], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=120)
    cases.append(('1: CONTROL: --tier basic --list is not refused',
                  'is not a tier' not in r.stderr, failure_detail(r.stderr, 200)))
    r = subprocess.run([sys.executable, 'tools/checkin.py', 'update', str(ROOT),
                        '--from-ref', 'no-such-ref-anywhere'], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=120)
    cases.append(('2: checkin update reads --from-ref',
                  "--from-ref 'no-such-ref-anywhere' does not name a commit"
                  in (r.stdout + r.stderr), failure_detail(r.stdout + r.stderr, 300)))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='followup-synced-'))
    saved_root = pc.ROOT
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), PRECEDENT_ALLOW_ANY_AUTHOR='1')
    try:
        repo = tmp / 'consumer'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env, check=True)
        (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': 'synced-rule', 'source': 'precedent'}]}), encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'base'], env=env, check=True)
        base = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        other = tmp / 'other-set'
        other.mkdir()
        ppr = types.SimpleNamespace(
            changed_slugs=lambda root, b: {'synced-rule': 'deleted',
                                           'own-rule': 'deleted'},
            source_roots=lambda root: [('here', root), ('other-set', other)],
            scan_root=lambda root, gone, succ, skip=None: [
                ('x.md', 1, slug, 'link', 'k', 's', 'l') for slug in sorted(gone)],
            must_fix=lambda row: True,
            received_paths=lambda root: set())
        pc.ROOT = repo
        got = pc._withdrawn_here_cited_elsewhere(ppr, base, {}, {})
        said = ' '.join(str(g) for g in got)
        cases.append(('3: a rule the base manifest recorded is not called '
                      'deleted by this branch', '`synced-rule`' not in said, said[:300]))
        cases.append(('3: CONTROL: a rule it did not record is still reported',
                      '`own-rule`' in said, said[:300]))
    finally:
        pc.ROOT = saved_root
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [(n, d) for n, ok, d in cases if not ok]
    check(f'three smaller faults from the consumer rehearsal stay fixed '
          f'({len(cases)} stated cases)', not failed,
          '; '.join(f'{n} -- {d}' for n, d in failed))


