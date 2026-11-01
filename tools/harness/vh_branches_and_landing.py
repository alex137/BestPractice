# The harness tests for branches
#
# tools/harness/vh_branches_and_landing.py -- part of the verification harness:
# branches, landing, merging and main's test.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_boundary_check_never_passes_unread():
    """precedent_boundary_check.py reports PASS only for protection shaped
    the way the plan needs, FAIL for each way it can be wrong, and
    UNVERIFIED -- never PASS -- when it could not ask GitHub.

    The tool is spec/CONTRIBUTOR_ACCESS.md's finding 5 (2026-09-14): a
    forgotten branch-protection step leaves Write as unrestricted write
    with nothing saying so. The API call is stubbed -- a harness case may
    not depend on the network, and no protected repository is reachable
    from a hosted session anyway. Each verdict asserts its own printed
    words (practice: control-asserts-which-failure); the token never
    appears in what is printed, and the fixture owns every environment
    variable the tool reads (practice: fixture-owns-its-state)."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_boundary_check as pbc

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-boundary-'))
    cases = []
    # Assembled so the leak gate does not read `<anything>@github.com` as an
    # address; the value is what must NOT come back out.
    token = 'ghp_NOTAREALTOKEN' + 'x' * 8
    env_with = {'GITHUB_TOKEN': token}
    calls = []

    def stub(status, body):
        def fetch(owner, name, branch, tok):
            calls.append((owner, name, branch, tok))
            return status, body
        return fetch

    good = {'required_pull_request_reviews': {'require_code_owner_reviews': True,
                                              'required_approving_review_count': 0},
            'enforce_admins': {'enabled': True}}

    def run(env, fetch, branch=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            r = pbc.assess(tmp, branch=branch, env=env, fetch=fetch)
            pbc.report(r)
        return r, out.getvalue()

    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)
        subprocess.run(['git', '-C', str(tmp), 'remote', 'add', 'origin',
                        'https://github.com/example/doc-project.git'], capture_output=True)
        (tmp / '.github').mkdir()
        (tmp / '.github' / 'CODEOWNERS').write_text('/.github/ @maint\n', encoding='utf-8')
        (tmp / 'precedent.json').write_text('{"base_branch": "trunk"}', encoding='utf-8')

        r, out = run({}, stub(200, good))
        cases.append(('no token is UNVERIFIED and says which variables to set, and GitHub is not called',
                      r['verdict'] == 'UNVERIFIED' and 'no token in the environment' in out
                      and 'UNVERIFIED is not a pass' in out and not calls, out))

        r, out = run(env_with, stub(200, good))
        cases.append(('protection shaped as the plan needs, plus CODEOWNERS in the tree, is PASS',
                      r['verdict'] == 'PASS' and 'boundary-check: PASS' in out
                      and 'merge their own documents and nothing else' in out, out))
        cases.append(('the declared base branch is what gets asked about, and the token is passed',
                      calls and calls[-1][:3] == ('example', 'doc-project', 'trunk')
                      and calls[-1][3] == token, str(calls)))
        cases.append(('the token is never printed', token not in out, out))

        r, out = run(env_with, stub(200, good), branch='other')
        cases.append(('--branch overrides the declared base', calls[-1][2] == 'other', str(calls[-1])))

        r, out = run(env_with, stub(404, {'message': 'Branch not protected'}))
        cases.append(('an unprotected base branch is FAIL and says what to turn on',
                      r['verdict'] == 'FAIL' and 'NOT protected' in out
                      and 'require review from code owners' in out, out))

        r, out = run(env_with, stub(403, {'message': 'Upgrade to GitHub Pro or make this repository public to enable this feature.'}))
        cases.append(('protection unavailable on the plan is FAIL, not UNVERIFIED -- it is an answer',
                      r['verdict'] == 'FAIL' and 'not available on this repository\'s plan' in out, out))

        r, out = run(env_with, stub(403, {'message': 'Resource not accessible by integration'}))
        cases.append(('a 403 that is a refusal to answer is UNVERIFIED and names the scope needed',
                      r['verdict'] == 'UNVERIFIED' and 'administration read' in out, out))

        r, out = run(env_with, stub(401, {'message': 'Bad credentials'}))
        cases.append(('a refused token is UNVERIFIED', r['verdict'] == 'UNVERIFIED'
                      and 'refused the token (401)' in out, out))

        r, out = run(env_with, stub(None, 'timed out'))
        cases.append(('an unreachable network is UNVERIFIED with the error',
                      r['verdict'] == 'UNVERIFIED' and 'could not reach GitHub: timed out' in out, out))

        body = {'required_pull_request_reviews': {'require_code_owner_reviews': True,
                                                  'required_approving_review_count': 1}}
        r, out = run(env_with, stub(200, body))
        cases.append(('required approvals above 0 is FAIL and names the bottleneck',
                      r['verdict'] == 'FAIL' and 'required approvals is 1, not 0' in out, out))

        body = {'required_pull_request_reviews': {'require_code_owner_reviews': False,
                                                  'required_approving_review_count': 0}}
        r, out = run(env_with, stub(200, body))
        cases.append(('code-owner review not required is FAIL',
                      r['verdict'] == 'FAIL' and 'review from code owners is not required' in out, out))

        r, out = run(env_with, stub(200, {'enforce_admins': {'enabled': False}}))
        cases.append(('no pull-request requirement is FAIL, and admin bypass is a note beside it',
                      r['verdict'] == 'FAIL' and 'a pull request is not required' in out
                      and 'note: administrators can bypass' in out, out))

        (tmp / '.github' / 'CODEOWNERS').unlink()
        r, out = run(env_with, stub(200, good))
        cases.append(('good protection with no CODEOWNERS in the tree is FAIL',
                      r['verdict'] == 'FAIL' and 'no CODEOWNERS file in the tree' in out
                      and r['codeowners'] is None, out))

        subprocess.run(['git', '-C', str(tmp), 'remote', 'set-url', 'origin',
                        'https://git.example.com/example/doc-project.git'], capture_output=True)
        before = len(calls)
        r, out = run(env_with, stub(200, good))
        cases.append(('a non-github remote is UNVERIFIED and GitHub is not asked',
                      r['verdict'] == 'UNVERIFIED' and 'not a github.com remote' in out
                      and len(calls) == before, out))

        # main() --check: UNVERIFIED and FAIL exit 1, PASS exits 0. The module's
        # fetch and the process environment are both owned here and restored.
        subprocess.run(['git', '-C', str(tmp), 'remote', 'set-url', 'origin',
                        'https://github.com/example/doc-project.git'], capture_output=True)
        (tmp / '.github' / 'CODEOWNERS').write_text('/.github/ @maint\n', encoding='utf-8')
        real_fetch = pbc.fetch_protection
        saved = {k: os.environ.get(k) for k in ('PRECEDENT_GITHUB_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN')}
        try:
            for k in saved:
                os.environ.pop(k, None)
            pbc.fetch_protection = stub(200, good)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = pbc.main(['--repo', str(tmp), '--check'])
            cases.append(('--check exits 1 on UNVERIFIED (no token), and 0 without --check',
                          code == 1 and 'UNVERIFIED' in out.getvalue(), out.getvalue()))
            with contextlib.redirect_stdout(io.StringIO()):
                code0 = pbc.main(['--repo', str(tmp)])
            cases.append(('without --check an UNVERIFIED run exits 0', code0 == 0, str(code0)))
            os.environ['GITHUB_TOKEN'] = token
            with contextlib.redirect_stdout(io.StringIO()):
                code = pbc.main(['--repo', str(tmp), '--check'])
            cases.append(('--check exits 0 on PASS', code == 0, str(code)))
            pbc.fetch_protection = stub(404, {'message': 'Branch not protected'})
            with contextlib.redirect_stdout(io.StringIO()):
                code = pbc.main(['--repo', str(tmp)])
            cases.append(('a FAIL exits 1 with or without --check', code == 1, str(code)))
        finally:
            pbc.fetch_protection = real_fetch
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_boundary_check.py passes only protection shaped as the plan '
          f'needs and never reads "could not look" as a pass ({len(cases)} stated '
          f'cases: no token, PASS, declared branch, token unprinted, --branch, '
          f'unprotected, plan, refused 403, 401, network, approvals, no code-owner '
          f'review, no PR requirement, no CODEOWNERS, non-github remote, and the '
          f'four exit codes)',
          not bad, '; '.join(f"{n}: {d}" for n, d in bad))


def check_main_test_issue_names_the_failing_cases():
    """--as-ci writes one line per failing case to the file
    PRECEDENT_HARNESS_FAILURES names, and the workflow's "main's test
    failed" issue reads it. Issue #1402 (2026-10-29) said only "could not
    be read; open the run", and the failing case had to be dug out of the
    job log by hand."""
    import tempfile
    cases = []
    two = subprocess.CompletedProcess([], 1, stdout=(
        'PASS: fine\nFAIL: the first thing broke\n  why it broke\n'
        'N/A: skipped\nFAIL: the second thing broke\n'), stderr='')
    got = _failing_case_lines('heavy', two)
    cases.append(('each FAIL: verdict is one line, without its failure text',
                  got == ['the first thing broke', 'the second thing broke'], got))
    died = subprocess.CompletedProcess([], 1, stdout='PASS: fine\n',
                                       stderr='Traceback\nKeyError\n')
    got = _failing_case_lines('part 2 of 3', died)
    cases.append(('a shard that died before a verdict is named as such',
                  len(got) == 1 and got[0].startswith('shard part 2 of 3: exit 1')
                  and 'no FAIL: line' in got[0], got))
    saved = os.environ.get('PRECEDENT_HARNESS_FAILURES')
    try:
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / 'failures.txt'
            f.write_text('a stale case from an earlier run\n', encoding='utf-8')
            os.environ['PRECEDENT_HARNESS_FAILURES'] = str(f)
            _write_failing_cases(['one', 'two'])
            got = f.read_text(encoding='utf-8')
            cases.append(('the file holds one line per case', got == 'one\ntwo\n', got))
            _write_failing_cases([])
            got = f.read_text(encoding='utf-8')
            cases.append(('a green run empties it, so a stale file never speaks',
                          got == '', got))
            os.environ.pop('PRECEDENT_HARNESS_FAILURES')
            _write_failing_cases(['three'])
            cases.append(('with the variable unset nothing is written',
                          f.read_text(encoding='utf-8') == '', ''))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_HARNESS_FAILURES', None)
        else:
            os.environ['PRECEDENT_HARNESS_FAILURES'] = saved
    wf = ROOT / '.github' / 'workflows' / 'deep-check.yml'
    if wf.is_file():
        text = wf.read_text(encoding='utf-8')
        cases.append(('deep-check.yml sets the file for the harness and the issue reads it',
                      'PRECEDENT_HARNESS_FAILURES: ${{ runner.temp }}/harness-failures.txt' in text
                      and '"$RUNNER_TEMP/harness-failures.txt"' in text, ''))
    bad = [f'{c[0]}: {c[2]!r}' for c in cases if not c[1]]
    check(f"main's test-failed issue names the failing cases ({len(cases)} stated cases)",
          not bad, '; '.join(bad))

def check_main_test_pass_closes_the_issue():
    """When main's test passes on main's CURRENT head, deep-check.yml closes
    any open main-test-failed issue, with a comment linking the run -- from
    the deep-check job when its run on main passed, and from the
    already-tested job when a push to main skipped that run because the
    same files had already passed, and from a passing pull request into
    main when main's head now holds exactly the files that run tested
    (2026-10-17, Morgan: "yes to both": Produce merges at once, main's own
    run stands aside for the pull request's, and issue #1174 stayed open
    after main was green). Never on a failure, never on another branch,
    never into another base, and never when main's files differ from what
    this run tested.

    WHY (2026-10-10, relayed from another session, checked here): issue
    #1036 stayed open about eleven hours while main's test passed at least
    three times, and the next session was sent to fix a green main.

    The skipped-run half is this session's own addition to the relayed
    plan: a push to main whose files already passed skips the deep-check
    job, so a close step only there would never run on that push.

    The script is run against a stand-in `gh` on PATH, so the
    head-comparison is exercised, not matched as text.

    Negative control, measured 2026-10-10 against origin/staging at
    277bc30c: no close step in either job, and no script."""
    import tempfile
    wf = ROOT / '.github' / 'workflows' / 'deep-check.yml'
    script = ROOT / 'tools' / 'close_main_test_issue.sh'
    text = wf.read_text(encoding='utf-8') if wf.is_file() else ''
    cases = []
    deep = text.split('\n  deep-check:', 1)[-1]
    tested = text.split('\n  already-tested:', 1)[-1].split('\n  deep-check:', 1)[0]
    block = _workflow_step_block(deep, "Close the issue when main's test passes again")
    body = '\n'.join(block)
    cases.append(('the deep-check job has the close step', bool(block), wf.name))
    steps = re.findall(r'^      - name:\s*(.+)$', deep, re.M)
    cases.append(('it runs after the harness, and the failure step stays last',
                  "Close the issue when main's test passes again" in steps
                  and 'verification harness' in ' '.join(
                      steps[:steps.index("Close the issue when main's test passes again")])
                  and steps[-1] == "Open an issue when main's test fails", steps))
    m = re.search(r'^\s+if:\s*>-?\s*\n((?:\s{10,}.*\n)+)', body + '\n', re.M) \
        or re.search(r'^\s+if:\s*(.+)$', body, re.M)
    expr = ' '.join(m.group(1).split()) if m else ''
    runs = [
        ('push', 'refs/heads/main', '', False, True),
        ('workflow_dispatch', 'refs/heads/main', '', False, True),
        ('pull_request', 'refs/pull/9/merge', 'main', False, True),
        ('pull_request', 'refs/pull/9/merge', 'main', True, False),
        ('pull_request', 'refs/pull/9/merge', 'staging', False, False),
        ('push', 'refs/heads/main', '', True, False),
        ('push', 'refs/heads/feature', '', False, False),
        ('workflow_dispatch', 'refs/heads/feature', '', False, False),
    ]
    for event, ref, base, failed, want in runs:
        try:
            got = _actions_if(expr, event, ref, base, failed) if expr else None
        except Exception as e:                                # noqa: BLE001
            got = f'unreadable: {e}'
        cases.append((f'{event} on {ref}{" into " + base if base else ""}, '
                      f'{"failed" if failed else "passed"}: '
                      f'{"closes" if want else "does nothing"}',
                      got is want, (expr, got)))
    skip_block = '\n'.join(_workflow_step_block(
        tested, 'Close the issue when these files already passed'))
    cases.append(('the already-tested job closes it too, only when it skipped the run',
                  "if: steps.already.outputs.skip == 'true'" in skip_block
                  and 'close_main_test_issue.sh' in skip_block, skip_block[:300]))
    perms = re.search(r'^    permissions:\s*\n((?:      .*\n)+)', tested, re.M)
    got = sorted(l.strip() for l in (perms.group(1) if perms else '').splitlines()
                 if l.strip() and not l.strip().startswith('#'))
    cases.append(('the already-tested job adds issues: write to the two read '
                  'permissions, and nothing else',
                  got == ['actions: read', 'contents: read', 'issues: write'], got))
    cases.append(('both steps run the one script and cannot turn a run red',
                  'close_main_test_issue.sh' in body
                  and 'continue-on-error: true' in body
                  and 'continue-on-error: true' in skip_block, ''))

    def run(head, issues, gh_fails=False, head_tree=None):
        # head_tree: main's head's files -- 'tested' for exactly the files
        # this run tested (a real commit's tree), anything else for others.
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            log = d / 'gh.log'
            fake = d / 'gh'
            sha, tree = 'a' * 40, 'c' * 40
            if head_tree is not None:
                g = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_COMMITTER_NAME='T',
                         GIT_AUTHOR_EMAIL='t@example.invalid',
                         GIT_COMMITTER_EMAIL='t@example.invalid')
                repo = d / 'repo'
                subprocess.run(['git', 'init', '-q', str(repo)], env=g)
                (repo / 'f').write_text('x\n', encoding='utf-8')
                subprocess.run(['git', '-C', str(repo), 'add', 'f'], env=g)
                subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'x'], env=g)
                sha = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                     capture_output=True, text=True).stdout.strip()
                real = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD^{tree}'],
                                      capture_output=True, text=True).stdout.strip()
                tree = real if head_tree == 'tested' else head_tree
            fake.write_text(
                '#!/bin/sh\n'
                f'echo "$*" >> "{log}"\n'
                + ('exit 1\n' if gh_fails else '')
                + 'case "$*" in\n'
                f'  *commit.tree.sha*) echo "{tree}"; exit 0 ;;\n'
                'esac\n'
                + 'case "$1 $2" in\n'
                f'  "api repos/o/r/commits/main") echo "{head}" ;;\n'
                f'  "issue list") printf "{issues}" ;;\n'
                'esac\nexit 0\n', encoding='utf-8')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=f'{d}:{os.environ.get("PATH", "")}',
                       GH_REPO='o/r', GITHUB_SHA=sha, GH_TOKEN='x',
                       RUN_URL='https://example.invalid/run/1', HOW='this run passed')
            r = subprocess.run(['bash', str(script)], env=env,
                               capture_output=True, text=True,
                               cwd=str(d / 'repo') if head_tree is not None else None)
            calls = log.read_text(encoding='utf-8') if log.is_file() else ''
            return r.returncode, calls, r.stdout
    if script.is_file():
        rc, calls, out = run('a' * 40, '1036\\n')
        cases.append(('THE DISCRIMINATING CASE: a pass on main\'s head comments with '
                      'the run and closes the open issue',
                      rc == 0 and 'issue comment 1036' in calls
                      and 'https://example.invalid/run/1' in calls
                      and 'issue close 1036 --reason completed' in calls, calls + out))
        rc, calls, out = run('b' * 40, '1036\\n')
        cases.append(('main moved past the commit this run tested: nothing is closed',
                      rc == 0 and 'issue close' not in calls
                      and 'issue list' not in calls, calls + out))
        rc, calls, out = run('b' * 40, '1174\\n', head_tree='tested')
        cases.append(('a pull request\'s run (its test merge is never main\'s '
                      'head) closes it once main holds exactly the files it tested',
                      rc == 0 and 'issue close 1174 --reason completed' in calls,
                      calls + out))
        rc, calls, out = run('b' * 40, '1174\\n', head_tree='d' * 40)
        cases.append(('...and closes nothing while main\'s files differ (not '
                      'merged yet, or main moved on)',
                      rc == 0 and 'issue close' not in calls, calls + out))
        rc, calls, out = run('a' * 40, '', gh_fails=True)
        cases.append(('GitHub unreachable: a warning, exit 0, nothing closed',
                      rc == 0 and 'issue close' not in calls
                      and '::warning::' in out, calls + out))
    else:
        cases.append(('tools/close_main_test_issue.sh exists', False, 'missing'))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_session_start_lists_a_red_main_first():
    """At session start, an open main-test-failed issue is the first line
    tools/open_failures.py prints, ahead of the failures filed under todo/;
    a GitHub that cannot be read is one line saying so; a repository whose
    workflows never open such an issue asks GitHub nothing. And this repo's
    own Claude Code session-start hook runs it before anything else that
    prints, which it never ran at all before 2026-10-09 (only
    tools/bootstrap.sh did).

    Negative control, measured 2026-10-09 against origin/main at d14a6fd6:
    open_failures.py has no report_lines and reads no issue, and the hook
    does not run it."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import open_failures as of
    finally:
        sys.path.pop(0)
    report = getattr(of, 'report_lines', None)
    label = getattr(of, 'MAIN_TEST_LABEL', 'main-test-failed')
    cases = []

    class Gh:
        def __init__(self, answer):
            self.answer, self.calls = answer, []

        def call(self, path, cache=True, **_kw):
            self.calls.append(path)
            return self.answer

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-red-main-'))
    try:
        def repo(name, with_label):
            r = tmp / name
            (r / '.github' / 'workflows').mkdir(parents=True)
            (r / '.github' / 'workflows' / 'test.yml').write_text(
                f'on: push\n# opens {label if with_label else "nothing"}\n', encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(r)], capture_output=True)
            subprocess.run(['git', '-C', str(r), 'remote', 'add', 'origin',
                            'https://github.com/owner/name.git'], capture_output=True)
            of.write_item(r, 'Landing failed: feat/x', 'boom', 'It lands.', '2026-10-09')
            return r
        red = repo('red', True)
        gh = Gh(([{'number': 7, 'title': "main's test failed",
                   'html_url': 'https://github.com/owner/name/issues/7'},
                  {'number': 8, 'title': 'a pull request', 'pull_request': {}}], None))
        lines = report(red, gh) if report else []
        cases.append(('an open main-test-failed issue is the first line, the todo/ '
                      'failures after it',
                      len(lines) >= 3 and lines[0].startswith("MAIN'S TEST FAILED: issue #7")
                      and 'issues/7' in lines[0] and lines[1].startswith('OPEN FAILURES (1)')
                      and not any('#8' in l for l in lines), lines))
        cases.append(('...asked once, of the repository\'s own issues, by label',
                      gh.calls == [f'repos/owner/name/issues?labels={label}'
                                   f'&state=open&per_page=20'], gh.calls))
        down = Gh((None, 'curl exited 6'))
        lines = report(red, down) if report else []
        cases.append(('GitHub cannot be read: one line says so, and the todo/ '
                      'failures still follow',
                      len(lines) >= 2 and lines[0].startswith("MAIN'S TEST NOT CHECKED, because ")
                      and lines[0].index('curl exited 6') < lines[0].index("GitHub's issues")
                      and '(' not in lines[0] and lines[1].startswith('OPEN FAILURES'),
                      lines))
        quiet = Gh(([], None))
        lines = report(repo('plain', False), quiet) if report else ['no report_lines']
        cases.append(('a repository whose workflows open no such issue asks GitHub '
                      'nothing', quiet.calls == [] and lines[0].startswith('OPEN FAILURES'),
                      (quiet.calls, lines)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    hook = (ROOT / '.claude' / 'hooks' / 'session-start.sh')
    calls = re.findall(r'^\s*python3\s+(?:"[^"]*/)?(?:tools/)?([\w.]+\.py)', hook.read_text(
        encoding='utf-8') if hook.is_file() else '', re.M)
    cases.append(('this repo\'s Claude Code session-start hook runs open_failures.py '
                  'before any other tool', calls[:1] == ['open_failures.py'], calls[:4]))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_alerting_test_is_listed_as_a_test():
    """A job's deliberate alerting test files an item that session start
    lists as a test to confirm, never as a failure, and that closes on the
    person's answer rather than on another run.

    2026-10-09, a private consuming repository: its sync's alerting test
    failed as intended, filed the usual blocker, and every session then
    opened with "the sync failed" until another Actions run cleared it.

    Negative control, measured 2026-10-09 against origin/staging at
    331e011e: write_item takes no alerting_test, and there is no
    alerting_tests or close_item."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import open_failures as of
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-alert-test-'))
    try:
        try:
            real = of.write_item(tmp, 'The sync failed', 'boom', 'A run succeeds.',
                                 '2026-10-09')
            test = of.write_item(tmp, 'The alerting test ran', 'refused', 'They confirm.',
                                 '2026-10-09', alerting_test=True)
        except TypeError as e:
            return (False, '0 stated cases', f'write_item takes no alerting_test: {e}')
        head = test.read_text(encoding='utf-8').split('\n---', 1)[0]
        cases.append(('the test item is no blocker, and is the person\'s to confirm',
                      'severity:          null' in head and 'kind:              manual' in head,
                      head))
        cases.append(('it is not one of the failures',
                      [f for f, _ in of.open_items(tmp)] == [real], of.open_items(tmp)))
        lines = of.report_lines(tmp)
        at = [i for i, l in enumerate(lines) if l.startswith('ALERTING TESTS (1)')]
        cases.append(('session start lists it after the failures, as a test, with the '
                      'way to close it',
                      lines[:1] and lines[0].startswith('OPEN FAILURES (1)') and at
                      and 'not failures' in lines[at[0]] and '--close' in lines[at[0]]
                      and lines[at[0] + 1].endswith('The alerting test ran')
                      and not any('alerting test ran' in l for l in lines[:at[0]]), lines))
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'open_failures.py'),
                            '--close', str(test), '--because', 'Morgan: the alert arrived'],
                           capture_output=True, text=True)
        text = test.read_text(encoding='utf-8')
        cases.append(('--close closes it on the answer, saying what closed it',
                      r.returncode == 0 and 'status:            done' in text
                      and 'closed:            "' in text and '- [x] **' in text
                      and 'closed: Morgan: the alert arrived' in text
                      and of.alerting_tests(tmp) == [], (r.returncode, r.stderr, failure_detail(text, 200))))
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'open_failures.py'),
                            '--close', str(test), '--because', 'again'],
                           capture_output=True, text=True)
        cases.append(('closing it twice is refused', r.returncode == 1, r.returncode))
        lines = of.report_lines(tmp)
        cases.append(('once closed, session start no longer lists it',
                      not any(l.startswith('ALERTING TESTS') for l in lines), lines))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_merge_gate_judges_the_declared_base():
    """The merge gate judges a pull request by the base GitHub declares, and
    guesses from branch tips only when it cannot read it.

    2026-09-28: staging had just been made at main's commit, so a pull
    request into staging matched both by tip and the gate announced "main
    is a fully checked branch"."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_merge_check as pmc
    finally:
        sys.path.pop(0)
    tips = ['main', 'staging']
    if not hasattr(pmc, 'choose_bases'):
        return (False, '0 stated cases', 'precedent_merge_check.py has no '
                'choose_bases(): the base is still guessed from branch tips')
    cases = [
        ('two branches at one commit, declared base staging: judged as staging',
         pmc.choose_bases('staging', tips) == ['staging']),
        ('no declared base (GitHub unreadable): every tip match, strictest decides',
         pmc.choose_bases(None, tips) == tips),
        ('a declared base with no tip match still wins',
         pmc.choose_bases('staging', []) == ['staging']),
    ]
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_code_owners_only_practices_reach_only_code_owners():
    """A practice marked `visible_to: code-owners` reaches only a person the
    repository names as a code owner, and a stale-branch listing never names
    main, staging or an engine branch.

    Morgan, 2026-10-05 (strength: decided): rules about running a repository
    "should NOT be shown to a user who is NOT a CODEOWNER"; in doubt, hidden;
    and the branch list never names a tier branch.

    practice: control-asserts-which-failure -- each hidden case asserts the
    reason printed, and the controls prove an owner, an unmarked practice and
    a merged branch all still come through.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-audience-'))
    cases = []
    try:
        env = {**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        env.pop('PRECEDENT_GITHUB_USER', None)
        env.pop('PRECEDENT_COMMIT_EMAIL', None)

        def audience(repo, user):
            e = dict(env)
            if user:
                e['PRECEDENT_GITHUB_USER'] = user
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_audience.py'),
                                '--repo', str(repo)], capture_output=True, text=True, env=e)
            return r.stdout.strip()

        a = tmp / 'with-codeowners'
        (a / '.github').mkdir(parents=True)
        (a / '.github' / 'CODEOWNERS').write_text('*  @Owner-One @org/team\n', encoding='utf-8')
        cases.append(('a CODEOWNERS entry makes a code owner, whatever the case',
                      audience(a, 'owner-one').startswith('code owner:'), audience(a, 'owner-one')))
        cases.append(('someone CODEOWNERS does not name is not one',
                      audience(a, 'someone').startswith('not a code owner:'), audience(a, 'someone')))
        cases.append(('no username declared: hidden, and the fix named',
                      'add "github"' in audience(a, ''), audience(a, '')))
        b = tmp / 'with-maintainers'
        b.mkdir()
        (b / 'precedent.json').write_text(json.dumps(
            {'maintainers': [{'name': 'M', 'github': 'maint'}]}), encoding='utf-8')
        cases.append(("no CODEOWNERS: precedent.json's maintainers answer instead",
                      audience(b, 'maint').startswith('code owner:'), audience(b, 'maint')))
        # A commit-email override (as a cloud environment sets) still takes
        # the username from the person's own identity.json.
        ind = tmp / 'individual'
        ind.mkdir()
        (ind / 'identity.json').write_text(json.dumps(
            {'email': 'm@example.com', 'github': 'maint'}), encoding='utf-8')
        (tmp / 'config.json').write_text(json.dumps(
            {'individual': {'path': str(ind)}}), encoding='utf-8')
        e2 = dict(env, PRECEDENT_USER_CONFIG=str(tmp / 'config.json'),
                  PRECEDENT_COMMIT_EMAIL='m@example.com')
        r2 = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_audience.py'),
                             '--repo', str(b)], capture_output=True, text=True, env=e2)
        cases.append(('with a commit-email override, the username still comes '
                      'from identity.json', r2.stdout.startswith('code owner:'),
                      r2.stdout + r2.stderr))
        c = tmp / 'nobody'
        c.mkdir()
        cases.append(('no owners named anywhere: in doubt, hidden',
                      'names no code owners' in audience(c, 'maint'), audience(c, 'maint')))
        # Nothing declared, but a GitHub origin: the account that owns the
        # repository is its owner (2026-10-06: a consumer's only member was
        # refused the Produce rule because nothing named him).
        o = tmp / 'owned'
        o.mkdir()
        subprocess.run(['git', 'init', '-q', str(o)], capture_output=True)
        subprocess.run(['git', '-C', str(o), 'remote', 'add', 'origin',
                        'https://github.com/Repo-Owner/some-repo.git'],
                       capture_output=True)
        cases.append(("nothing declared: the GitHub origin's owner is a code owner",
                      audience(o, 'repo-owner').startswith('code owner:'),
                      audience(o, 'repo-owner')))
        cases.append(("...and someone else is still not one",
                      audience(o, 'someone').startswith('not a code owner:'),
                      audience(o, 'someone')))

        # precedent_show prints the marked practice to an owner only.
        (b / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'deep-check.md', b / 'practices')
        shutil.copy(ROOT / 'practices' / 'repo-is-memory.md', b / 'practices')

        def show(user, slug):
            e = dict(env, PRECEDENT_GITHUB_USER=user)
            return subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_show.py'),
                                   '--repo', str(b), slug], capture_output=True,
                                  text=True, env=e).stdout
        cases.append(('precedent_show hides a marked practice from a stranger, saying why',
                      'code owners only' in show('stranger', 'deep-check'),
                      show('stranger', 'deep-check')[:200]))
        cases.append(('CONTROL: an owner reads it',
                      'code owners only' not in show('maint', 'deep-check')
                      and 'audit' in show('maint', 'deep-check'),
                      show('maint', 'deep-check')[:200]))
        cases.append(('CONTROL: an unmarked practice reaches everyone',
                      'code owners only' not in show('stranger', 'repo-is-memory'),
                      show('stranger', 'repo-is-memory')[:200]))

        # The stale-branch listing.
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_stale_branches as sb
        genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                    GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        origin, work = tmp / 'origin.git', tmp / 'work'

        def g(*a, cwd=work):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=genv)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)],
                       capture_output=True)
        subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
        (work / 'a.txt').write_text('a\n'); g('add', '-A'); g('commit', '-qm', 'a')
        g('push', '-q', 'origin', 'HEAD:main')
        for b_ in ('staging', 'precedent-promote-lock', 'claude/done'):
            g('push', '-q', 'origin', f'HEAD:refs/heads/{b_}')
        g('checkout', '-q', '-b', 'claude/open')
        (work / 'b.txt').write_text('b\n'); g('add', '-A'); g('commit', '-qm', 'b')
        g('push', '-q', 'origin', 'claude/open')
        g('fetch', '-q', 'origin')
        listed = [b_ for b_, _d in (sb.stale_in(work) or [])]
        cases.append(('a branch already in main is listed', 'claude/done' in listed, listed))
        cases.append(('never main, staging or an engine branch',
                      not {'main', 'staging', 'precedent-promote-lock'} & set(listed),
                      listed))
        cases.append(('CONTROL: a branch with work main lacks is not listed',
                      'claude/open' not in listed, listed))
        # An engine branch's old name, once its data- copy holds all of it,
        # is listed: nothing reads it (2026-10-13).
        g('push', '-q', 'origin', 'origin/precedent-promote-lock:refs/heads/data-promote-lock')
        g('fetch', '-q', 'origin')
        listed = [b_ for b_, _d in (sb.stale_in(work) or [])]
        cases.append(('an old engine branch its data- copy holds is listed',
                      'precedent-promote-lock' in listed
                      and 'data-promote-lock' not in listed, listed))
        g('checkout', '-q', '-b', 'held', 'origin/precedent-promote-lock')
        g('commit', '-q', '--allow-empty', '-m', 'held by an older engine')
        g('push', '-q', '-f', 'origin', 'HEAD:precedent-promote-lock')
        g('fetch', '-q', 'origin')
        listed = [b_ for b_, _d in (sb.stale_in(work) or [])]
        cases.append(('CONTROL: an old engine branch with a claim its data- copy '
                      'lacks is not listed', 'precedent-promote-lock' not in listed,
                      listed))
        # The receipts' old name stays off even once its data- copy holds
        # all of it: an older engine still wrote it on 2026-10-28
        # (precedent_data_branches.KEPT_OLD_NAMES; Morgan, 2026-10-31,
        # strength: assented).
        g('checkout', '-q', 'main')
        g('push', '-q', 'origin', 'HEAD:refs/heads/precedent-check-receipts')
        g('push', '-q', 'origin', 'HEAD:refs/heads/data-check-receipts')
        g('fetch', '-q', 'origin')
        listed = [b_ for b_, _d in (sb.stale_in(work) or [])]
        cases.append(('the receipts\' old name is not listed though its data- '
                      'copy holds it', 'precedent-check-receipts' not in listed
                      and 'data-check-receipts' not in listed, listed))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_branch_cleanup_button():
    """The branch cleanup page's delete-all button: shown always for a
    public repository, for a private one only once its own number of hours
    has passed since that repository's last cleanup run, and started only
    by a person -- the tool behind it deletes nothing outside its workflow
    (spec/BRANCH_CLEANUP_BUTTON_PLAN.md).

    WHY. Morgan, 2026-10-16 (strength: decided): "on both [private] and
    public, NEVER run the cleanup automatically ... for public ones, the
    button is always there; for private ones, the button only appears if
    the tracker for that says it can be shown", with "a second variable
    next to me ... 336 for now", and the per-branch list kept as it is.
    Planted: the setting and its doubt cases; the due rule for public,
    private never run, private within and past the hours, not installed;
    GitHub's run history (a failure does not count, a running one does,
    an error is unknown); the merge of GitHub's history, the saved record
    and the page's click; the line and the round trip through a saved
    page; --delete-merged refusing outside its workflow and, inside it,
    deleting only a merged branch while skipping an open pull request's
    source and an unmerged branch; the template's single trigger; no
    engine tool starting it; and a refresh adding the workflow beside an
    installed one."""
    import datetime
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as sb
    import precedent_branches as pb
    import precedent_vendor_engine as pve
    cases = []
    utc = datetime.timezone.utc
    now = datetime.datetime(2026, 10, 16, 12, 0, tzinfo=utc)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        none_cfg = td / 'no-config.json'

        def ident(value):
            d = {'name': 'P', 'email': 'p@example.com'}
            if value is not None:
                d['github_branch_cleanup_every_hours'] = value
            (td / 'identity.json').write_text(json.dumps(d), encoding='utf-8')
            return pb.branch_cleanup_cadence(td, user_config=none_cfg)[0]
        cases.append(('the person\'s 336 is read', ident(336) == 336.0, ident(336)))
        cases.append(('CONTROL: unset is 0, the button shown', ident(None) == 0.0, ''))
        cases.append(('not a number is 0', ident('two weeks') == 0.0, ''))
        cases.append(('a negative number is 0', ident(-5) == 0.0, ''))
        (td / 'identity.json').unlink()
        (td / 'precedent.json').write_text(json.dumps(
            {'github_branch_cleanup_every_hours': 48}), encoding='utf-8')
        got = pb.branch_cleanup_cadence(td, user_config=none_cfg)[0]
        cases.append(('the repository\'s own number when the person has none',
                      got == 48.0, got))

    def st(private, last, hours=336, installed=True):
        return {'owner': 'o', 'repo': 'r', 'installed': installed, 'private': private,
                'hours': hours, 'last': last, 'checked': now.isoformat()}
    day_ago = (now - datetime.timedelta(days=1)).isoformat()
    weeks_ago = (now - datetime.timedelta(days=15)).isoformat()
    cases.append(('public: always shown, even just after a run',
                  sb.cleanup_due(st(False, day_ago), now) == (True, None), ''))
    cases.append(('private, never run: shown',
                  sb.cleanup_due(st(True, ''), now) == (True, None), ''))
    shown, back = sb.cleanup_due(st(True, day_ago), now)
    cases.append(('private, run a day ago with 336 hours: hidden until 336 hours after it',
                  not shown and back == now - datetime.timedelta(days=1)
                  + datetime.timedelta(hours=336), (shown, back)))
    cases.append(('private, run fifteen days ago: shown',
                  sb.cleanup_due(st(True, weeks_ago), now) == (True, None), ''))
    cases.append(('private, visibility unknown: shown',
                  sb.cleanup_due(st(None, day_ago), now) == (True, None), ''))
    cases.append(('private with no number: shown',
                  sb.cleanup_due(st(True, day_ago, hours=0), now) == (True, None), ''))
    cases.append(('not installed: never a link',
                  sb.cleanup_due(st(False, '', installed=False), now) == (False, None), ''))

    class GH:
        def __init__(self, answer):
            self.answer = answer

        def call(self, path, cache=True):
            return self.answer
    runs = {'workflow_runs': [
        {'status': 'completed', 'conclusion': 'failure', 'created_at': '2026-10-15T10:00:00Z'},
        {'status': 'completed', 'conclusion': 'success', 'created_at': '2026-10-01T10:00:00Z'}]}
    got = sb.last_cleanup_run('o/r', GH((runs, None)))
    cases.append(('a failed run does not count; the success before it does',
                  got == '2026-10-01T10:00:00Z', got))
    got = sb.last_cleanup_run('o/r', GH(({'workflow_runs': [
        {'status': 'in_progress', 'conclusion': None, 'created_at': '2026-10-16T11:00:00Z'}]}, None)))
    cases.append(('a run still going counts', got == '2026-10-16T11:00:00Z', got))
    cases.append(('no runs at all: never run',
                  sb.last_cleanup_run('o/r', GH(({'workflow_runs': []}, None))) == '', ''))
    cases.append(('GitHub not answering: unknown',
                  sb.last_cleanup_run('o/r', GH((None, 'timed out'))) is None, ''))
    cases.append(('no session access to GitHub: unknown',
                  sb.last_cleanup_run('o/r', None) is None, ''))

    click = (now - datetime.timedelta(hours=2)).isoformat()
    prev = [st(True, weeks_ago), dict(st(True, weeks_ago), repo='carried')]
    clicked = {'o/r': click, 'o/carried': click}
    merged = sb.merge_cleanup([st(True, '')], prev, clicked)
    cases.append(('GitHub says never run: a click that started nothing is dropped',
                  merged[('o', 'r')]['last'] == '', merged[('o', 'r')]))
    merged = sb.merge_cleanup([st(True, None)], prev, clicked)
    cases.append(('GitHub not answering: the newer of the saved run and the click',
                  merged[('o', 'r')]['last'] == click, merged[('o', 'r')]))
    cases.append(('a repository this run did not ask keeps its record, with the click',
                  merged[('o', 'carried')]['last'] == click, merged.get(('o', 'carried'))))

    line = sb._cleanup_line('o', 'r', 3, st(True, day_ago), now)
    cases.append(('a private repository within its hours: link hidden, the date shown',
                  'class="del-all"' in line and ' hidden>Delete every' in line
                  and 'Delete-all button back on 29 Oct.' in line, line))
    line = sb._cleanup_line('o', 'r', 3, st(False, day_ago), now)
    cases.append(('a public one: the link, to the workflow\'s page',
                  sb.workflow_link('o', 'r') in line and ' hidden>Delete every' not in line, line))
    line = sb._cleanup_line('o', 'r', 3, st(False, '', installed=False), now)
    # 2026-10-20 (Morgan: "just give it to me and say nothing else"): a
    # section without the button says nothing about why.
    cases.append(('not installed: no link and no explanation', line == '', line))
    line = sb._cleanup_line('o', 'r', 3, dict(st(False, '', installed=False), source=True), now)
    cases.append(('a practice set: no link and no explanation', line == '', line))
    doc = sb.repo_doc('o', 'r', [('done-branch', '2026-10-01')], now.isoformat(),
                      cleanup=st(True, day_ago), now=now)
    cases.append(('a repository\'s section keeps every row beside the button',
                  'branches/all?query=done-branch' in doc['section']
                  and 'class="cleanup"' in doc['section'], ''))
    cases.append(('its document keeps the record, for the next refresh',
                  doc['cleanup']['last'] == day_ago, doc['cleanup']))
    cases.append(('a document records the format that wrote it',
                  doc['format'] == sb.PAGE_FORMAT >= 4, doc['format']))

    # Every delete below runs in a throwaway repository whose origin is a
    # local bare one: with its guard broken, this test must still never
    # reach a real remote (practice: never-delete-a-remote-branch; 2026-10-16,
    # a negative control run against this checkout tried GitHub, which
    # refused).
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        origin, work = td / 'origin.git', td / 'work'

        def git(*a, cwd=None):
            return subprocess.run(['git', *a], cwd=cwd or work, env=env,
                                  capture_output=True, text=True)
        git('init', '-q', '--bare', '-b', 'main', str(origin), cwd=td)
        git('clone', '-q', str(origin), str(work), cwd=td)
        (work / 'f').write_text('1\n')
        git('add', 'f'); git('commit', '-qm', 'base')
        for b in ('merged-one', 'open-pr', 'staging'):
            git('branch', b)
        git('switch', '-q', '-c', 'unmerged')
        (work / 'g').write_text('2\n')
        git('add', 'g'); git('commit', '-qm', 'not in main')
        git('switch', '-q', 'main')
        git('push', '-q', 'origin', 'main', 'merged-one', 'open-pr', 'staging', 'unmerged')
        git('fetch', '-q', 'origin')
        said = []
        code = sb.delete_merged(work, env={}, say=said.append)
        heads = git('ls-remote', '--heads', 'origin').stdout.count('refs/heads/')
        cases.append(('--delete-merged refuses outside its workflow, in its own words',
                      code == 2 and heads == 5 and 'runs only inside the '
                      'precedent-branch-cleanup workflow' in ' '.join(said), (code, heads, said)))
        said = []
        code = sb.delete_merged(work, keep=['main'], skip_heads=['open-pr'],
                                env={'GITHUB_ACTIONS': 'true',
                                     'GITHUB_EVENT_NAME': 'workflow_dispatch'},
                                say=said.append)
        left = sorted(l.split('refs/heads/')[-1] for l in
                      git('ls-remote', '--heads', 'origin').stdout.splitlines())
        cases.append(('inside its workflow: the merged branch goes, and only it',
                      code == 0 and left == ['main', 'open-pr', 'staging', 'unmerged'],
                      (code, left, said)))
        cases.append(('an open pull request\'s source is skipped, and said',
                      any('open-pr' in l and 'open pull request' in l for l in said), said))

    tpl = (ROOT / 'templates' / 'github-actions' / 'branch-cleanup.yml.template'
           ).read_text(encoding='utf-8')
    body = re.sub(r'(?m)^\s*#.*$', '', tpl)
    on = re.search(r'(?ms)^on:\n(.*?)^\S', body)
    cases.append(('the workflow\'s only trigger is a person\'s click',
                  on is not None and on.group(1).split() == ['workflow_dispatch:'],
                  on.group(1) if on else 'no on:'))
    # The one call that starts it is the page's all-public button, run by a
    # person's click through their own GitHub connector; Python never does.
    starts = re.compile(r'actions_run_trigger|run_workflow|/dispatches|workflow run\b')
    starters = []
    for f in (ROOT / 'tools').glob('*.py'):
        if f.name == 'verify_harness.py':
            continue
        txt = f.read_text(encoding='utf-8', errors='ignore')
        if f.name == 'precedent_stale_branches.py':
            # Its prose and the page it renders may name the call; its
            # Python may not make it.
            import ast as _ast
            lines = txt.splitlines(keepends=True)
            for node in reversed(_ast.parse(txt).body):
                names = [t.id for t in getattr(node, 'targets', [])
                         if isinstance(t, _ast.Name)]
                if (names and names[0] in ('_PAGE', 'PAGE_CAPABILITIES')) or (
                        isinstance(node, _ast.Expr) and isinstance(
                            getattr(node, 'value', None), _ast.Constant)):
                    del lines[node.lineno - 1:node.end_lineno]
            txt = ''.join(lines)
        if sb.CLEANUP_WORKFLOW in txt and ('dispatches' in txt or starts.search(txt)):
            starters.append(f.name)
    cases.append(('no engine tool can start it', starters == [], starters))
    script = sb._PAGE
    run = script.find('function runPublic(){')
    end = script.find('\n  }\n', run)
    cases.append(('the page starts it only from the all-public button\'s click',
                  script.count("method:'run_workflow'") == 1 and run != -1
                  and run < script.index("method:'run_workflow'") < end
                  and script.count('runPublic') == 2
                  and "all.addEventListener('click',runPublic)" in script, ''))
    cases.append(('the page may call one GitHub tool and nothing else',
                  sb.PAGE_CAPABILITIES['mcp']['servers']
                  == [{'server': sb.GITHUB_CONNECTOR, 'tools': ['actions_run_trigger']}],
                  sb.PAGE_CAPABILITIES))

    def public(state, rows=(('p1', '2026-10-01'), ('p2', '2026-10-02'))):
        return sb.repo_doc('o', 'pub', list(rows), now.isoformat(), cleanup=state,
                           now=now)['public']
    cases.append(('the all-public button covers a public repository, carried or not',
                  public(st(False, '')) and sb.repo_doc(
                      'o', 'gone', [('g', '2026-10-01')], '2026-10-01T00:00:00+00:00',
                      cleanup=st(False, ''), fresh=False, now=now)['public'], ''))
    cases.append(('...and never a private or unknown one',
                  not public(st(True, '')) and not public(st(None, '')), ''))
    cases.append(('CONTROL: a public repository without the workflow is left out',
                  not public(dict(st(False, ''), installed=False)), ''))
    cases.append(('CONTROL: nor one with nothing to delete', not public(st(False, ''), ()), ''))
    cases.append(('the page builds the all-public button from those, counting their rows',
                  "r.public&&r.section" in script and 'id="del-public"' in script
                  and "(r.branches||[]).length" in script, ''))
    cases.append(('any cleanup click checks off that repository\'s rows',
                  "function started(p)" in script and "started(p); });" in script
                  and "pub.forEach(started)" in script, ''))

    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        (dest / 'tools').mkdir()
        wf = dest / '.github' / 'workflows'
        wf.mkdir(parents=True)
        src = ROOT / 'templates' / 'github-actions'
        rendered = pve.render_ci_workflow(dest, (src / 'light-check.yml.template').read_bytes())
        (wf / 'light-check.yml').write_bytes(rendered)
        import hashlib as _h
        man = {'ci_workflows_sha256': {'.github/workflows/light-check.yml':
                                       _h.sha256(rendered).hexdigest()}}
        (dest / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps(man), encoding='utf-8')
        refreshed, _c, _r = pve._refresh_ci_workflow_files(dest, 'consumer', src, man)
        cases.append(('a refresh adds the cleanup workflow beside an installed one',
                      (wf / 'precedent-branch-cleanup.yml').is_file()
                      and '.github/workflows/precedent-branch-cleanup.yml' in refreshed,
                      refreshed))
        (wf / 'light-check.yml').unlink()
        (wf / 'precedent-branch-cleanup.yml').unlink()
        pve._refresh_ci_workflow_files(dest, 'consumer', src, man)
        cases.append(('CONTROL: with no workflow installed (GitHub workflows off), none is added',
                      not (wf / 'precedent-branch-cleanup.yml').exists(), ''))
        # 2026-10-16, a consumer's Update Vendors: the workflow was added with
        # no word in the repository's own guide, and its basic check refused
        # it (github-setup-disclosed). The refresh now writes the bullet.
        guide = dest / 'GETTING_STARTED.md'
        guide.write_text('# Getting started\n\n- **Before anything** reaches main.\n'
                         '- **Your writing is checked before it is saved, not after.**\n',
                         encoding='utf-8')
        (wf / 'light-check.yml').write_bytes(rendered)
        refreshed, _c, _r = pve._refresh_ci_workflow_files(dest, 'consumer', src, man)
        text = guide.read_text(encoding='utf-8')
        cases.append(('the refresh that adds the workflow says so in the guide, '
                      'before the writing bullet',
                      'GETTING_STARTED.md' in refreshed
                      and text.index('precedent-branch-cleanup.yml')
                      < text.index('Your writing is checked'), text))
        again = pve._disclose_added_workflow(
            dest, '.github/workflows/precedent-branch-cleanup.yml', 'branch-cleanup.yml.template')
        cases.append(('a guide that already names it is left alone',
                      again is False and text == guide.read_text(encoding='utf-8'), ''))
        guide.write_text('# A guide of its own\n', encoding='utf-8')
        pve._LEFT_FOR_YOU.clear()
        pve._disclose_added_workflow(
            dest, '.github/workflows/precedent-branch-cleanup.yml', 'branch-cleanup.yml.template')
        cases.append(('a guide with no place for it is left for the person, with the text',
                      guide.read_text(encoding='utf-8') == '# A guide of its own\n'
                      and any('GETTING_STARTED.md' in str(i) for i in pve._LEFT_FOR_YOU),
                      pve._LEFT_FOR_YOU))
        pve._LEFT_FOR_YOU.clear()
        # 2026-10-19, two consuming repos: an older guide with the template's
        # checks heading but neither anchor bullet, and the workflow already
        # installed by an earlier refresh that could not say so. The old code
        # wrote nothing on that refresh and never asked again on later ones.
        guide.write_text('# Getting started\n\n## For the administrator\n\n'
                         '### Automatic checks installed for this project\n\n'
                         '- **A check runs on pull requests.**\n\n'
                         '### Updates happen when you ask\n\nSay so.\n',
                         encoding='utf-8')
        assert (wf / 'precedent-branch-cleanup.yml').is_file()
        refreshed, _c, _r = pve._refresh_ci_workflow_files(dest, 'consumer', src, man)
        text = guide.read_text(encoding='utf-8')
        cases.append(('a refresh that finds the workflow already there still writes the '
                      'bullet, at the end of the checks section of an older guide',
                      'GETTING_STARTED.md' in refreshed
                      and text.index('A check runs') < text.index('precedent-branch-cleanup.yml')
                      < text.index('### Updates happen'), text))
        refreshed, _c, _r = pve._refresh_ci_workflow_files(dest, 'consumer', src, man)
        cases.append(('CONTROL: the next refresh leaves the guide alone',
                      'GETTING_STARTED.md' not in refreshed
                      and guide.read_text(encoding='utf-8') == text, refreshed))
        pve._LEFT_FOR_YOU.clear()
    import precedent_install as _pi
    cases.append(('the installer\'s guide paragraph carries the same bullet, one copy',
                  pve.CI_DISCLOSURES['branch-cleanup.yml.template'] in _pi._CI_PARAGRAPH_ON
                  and _pi._CI_PARAGRAPH_ON in (ROOT / 'templates' / 'GETTING_STARTED.md'
                                               ).read_text(encoding='utf-8'), ''))
    import precedent_update as _pu
    picked = _pu.vendored_layer_paths(ROOT, ['.github/workflows/precedent-branch-cleanup.yml',
                                             '.github/workflows/light-check.yml',
                                             '.github/workflows/someones-own.yml'])
    cases.append(('a rerun puts the engine\'s own workflows back with the engine, and '
                  'only those (the old engine never judges a file it lacks)',
                  sorted(picked) == ['.github/workflows/light-check.yml',
                                     '.github/workflows/precedent-branch-cleanup.yml'], picked))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the branch cleanup page\'s delete-all button ({len(cases)} stated cases)',
          not bad, '; '.join(map(str, bad)))


def check_wait_main_test_finds_a_merged_pull_requests_head():
    """2026-10-19: --wait-main-test COPY could not find its commit after the
    merge -- GitHub deletes the branch, and a shallow clone cannot resolve
    it. It now takes a pull request number, and looks a gone branch up as a
    pull request's head. CONTROL: a branch that resolves is used as before."""
    import subprocess as _sp
    import tempfile
    import precedent_branches as pb
    cases = []
    head = 'a' * 40

    class FakeGH:
        def __init__(self):
            self.asked = []

        def call(self, path, cache=True):
            self.asked.append(path)
            pr = {'number': 7, 'head': {'sha': head, 'ref': 'x-promote-to-main-y'},
                  'base': {'ref': 'main'}}
            if path.endswith('/pulls/7'):
                return pr, None
            if '/pulls?state=all&head=acme:x-promote-to-main-y' in path:
                return [pr], None
            return [], None
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        g = lambda *a: _sp.run(['git', '-C', str(d), *a], capture_output=True, text=True)
        g('init', '-q', '-b', 'main'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        g('remote', 'add', 'origin', 'https://github.com/acme/consumer.git')
        g('commit', '-q', '--allow-empty', '-m', 'c')
        local = g('rev-parse', 'HEAD').stdout.strip()
        g('branch', 'still-here')
        gh = FakeGH()
        cases.append(('a pull request number gives its head commit and branch',
                      pb.resolve_main_test_target(d, '#7', gh=gh) == (head, 'x-promote-to-main-y'),
                      gh.asked))
        cases.append(('a branch GitHub deleted is found as a pull request\'s head',
                      pb.resolve_main_test_target(d, 'x-promote-to-main-y', gh=gh)
                      == (head, 'x-promote-to-main-y'), gh.asked))
        cases.append(('CONTROL: a branch that resolves here is used as before',
                      pb.resolve_main_test_target(d, 'still-here', gh=gh) == (local, 'still-here'),
                      ''))
        cases.append(('CONTROL: a name nothing knows gives nothing',
                      pb.resolve_main_test_target(d, 'nope', gh=gh) == (None, None), ''))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'--wait-main-test finds a merged pull request\'s head ({len(cases)} stated cases)',
          not bad, '; '.join(map(str, bad)))


def check_stale_branches_lists_one_repository_once():
    """precedent_stale_branches.py lists a repository once, however it is
    reached.

    Reported 2026-10-08 from a consuming repository: the stale-branch page
    listed one repository twice, because `_repos()` keyed on the origin's
    (owner, name) exactly as spelled, and the same repository was reached
    as .../bestpractice and .../BestPractice. GitHub names are
    case-insensitive, so the key is now casefolded, keeping the first
    spelling seen; and a path that reaches a directory already seen (a
    link, or a case-insensitive filesystem) is skipped outright.

    CONTROL: a different repository is still listed."""
    import tempfile
    import types
    name = 'the stale-branch listing names one repository once'
    if not (ROOT / 'tools' / 'precedent_stale_branches.py').exists():
        not_applicable(name, 'tools/precedent_stale_branches.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_stale_branches as sb
    finally:
        sys.path.pop(0)
    cases = []
    saved = sys.modules.get('precedent_container_safe')
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def repo(dirname, url):
            d = tmp / dirname
            subprocess.run(['git', 'init', '-q', str(d)], capture_output=True, check=True)
            subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin', url],
                           capture_output=True, check=True)
            return d
        first = repo('BestPractice', 'https://github.com/Alex137/BestPractice.git')
        second = repo('bestpractice-2', 'https://github.com/alex137/bestpractice')
        other = repo('other', 'https://github.com/alex137/something-else.git')
        link = tmp / 'linked'
        link.symlink_to(first, target_is_directory=True)

        def listed(found):
            sys.modules['precedent_container_safe'] = types.SimpleNamespace(
                checkouts=lambda: list(found))
            try:
                return sb._repos()
            finally:
                if saved is None:
                    sys.modules.pop('precedent_container_safe', None)
                else:
                    sys.modules['precedent_container_safe'] = saved

        sb_github = sb._github
        sb._github = lambda: None
        try:
            got = listed([first, second, other])
        finally:
            sb._github = sb_github
        slugs = [s_ for _p, s_ in got]
        cases.append(('two clones whose origins differ only in case are one '
                      f'repository, shown as first spelled ({slugs})',
                      slugs.count(('Alex137', 'BestPractice')) == 1
                      and not any(s_ == ('alex137', 'bestpractice') for s_ in slugs)))
        cases.append((f'CONTROL: a different repository is still listed ({slugs})',
                      ('alex137', 'something-else') in slugs and len(slugs) == 2))
        sb._github = lambda: None
        try:
            got = listed([link, first, other])
        finally:
            sb._github = sb_github
        cases.append(('one clone reached through two paths is listed once '
                      f'({[str(p_) for p_, _s in got]})', len(got) == 2))
        # GitHub's own spelling for a clone the attach tool made from a
        # lowercase URL (2026-10-17); unchanged when GitHub cannot answer.
        answers = {'repos/alex137/bestpractice':
                   ({'full_name': 'alex137/BestPractice'}, None)}
        fake = types.SimpleNamespace(
            call=lambda path, **_k: answers.get(path, (None, '404 Not Found')))
        real_github = sb._github
        sb._github = lambda: fake
        try:
            got = [s_ for _p, s_ in listed([second, other])]
        finally:
            sb._github = real_github
        cases.append(('a clone whose origin is all lowercase is shown as GitHub '
                      f'spells it ({got})', ('alex137', 'BestPractice') in got))
        cases.append(('...and one GitHub does not answer for keeps its own '
                      f'spelling ({got})', ('alex137', 'something-else') in got))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_promote_names_a_binary_conflict():
    """A Promote whose merge conflicts on a binary file stops and names it.

    2026-10-05: a Debut in a repository that keeps Word files conflicted on
    one, and _generator_of read the file's index stage as UTF-8 text to look
    for a `generated_by:` header. A .docx is binary, so the Promote died
    with a UnicodeDecodeError traceback instead of saying which file
    conflicted. A binary file carries no header, so it counts as
    hand-written: the merge stops and the file is named.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-binary-conflict-'))
    cases = []
    try:
        r = tmp / 'r'
        r.mkdir()
        def git(*a):
            return subprocess.run(['git', '-C', str(r), *a], capture_output=True)
        git('init', '-q')
        git('config', 'user.email', 'fixture@example.com')
        git('config', 'user.name', 'fixture')
        doc = r / 'out.docx'
        doc.write_bytes(b'PK\x03\x04\x85\x00base')
        git('add', '.')
        git('commit', '-qm', 'base')
        git('checkout', '-qb', 'other')
        doc.write_bytes(b'PK\x03\x04\x85\x00theirs')
        git('commit', '-qam', 'theirs')
        git('checkout', '-q', '-')
        doc.write_bytes(b'PK\x03\x04\x85\x00ours')
        git('commit', '-qam', 'ours')
        merged = git('merge', '-q', 'other')
        cases.append(('the fixture merge really conflicts on the binary file',
                      merged.returncode != 0
                      and b'out.docx' in git('diff', '--name-only',
                                             '--diff-filter=U').stdout,
                      failure_detail(merged.stdout.decode(errors='replace'), 300)))
        script = tmp / 'run.py'
        script.write_text(f"""
import sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
import precedent_branches as pb
print(repr(pb._resolve_by_regenerating({str(r)!r}, say=lambda *a: None)))
""", encoding='utf-8')
        out = subprocess.run([sys.executable, str(script)], capture_output=True,
                             text=True)
        cases.append(('resolving it does not crash', out.returncode == 0
                      and 'Traceback' not in out.stderr, failure_detail(out.stderr, 500)))
        cases.append(("...and reports the binary file as the conflict that "
                      "stops the merge, saying nothing here rebuilds it",
                      out.stdout.strip().startswith("(False, ['out.docx'], ")
                      and 'no generator here rebuilds it' in out.stdout,
                      failure_detail(out.stdout.strip(), 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a Promote names a binary merge conflict ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_very_deep_check_lists_checks_by_stage():
    """The very deep check's CHECKS BY STAGE reads, from a repository's own
    push check and branch tool, what runs before and after Booked, Produce
    and the Debut, and flags anything but the closed quick tier before a
    push (Morgan, 2026-10-17, strength: decided; practice: very-deep-check,
    Pass 2's question 25).

    WHY. Checks crept into the pushes twice: by 2026-10-16 a landing's quick
    check took 218 s (spec/TESTS_RUN_AT_THE_DEBUT_PLAN.md). The quick tier's
    own test sees BASIC_CHECKS; it could not see a move that called the full
    tier before pushing, or a repository's workflow checks that ran at every
    tier outside that set.

    Planted cases, on a copy of tools/: Booked's land made to run the full
    tier, and doc_sync slipped into the quick tier without an approval. The
    control: this repository's own tools flag neither."""
    import tempfile
    vdc = ROOT / 'tools' / 'very_deep_check.py'
    name = 'the very deep check lists the checks by stage and flags extra ones before a push'

    def read(tree):
        # No person's config: a set they bring would supply its own moves.
        env = dict(os.environ, PRECEDENT_USER_CONFIG=str(pathlib.Path(tree) / 'no-config.json'))
        p = subprocess.run([sys.executable, str(vdc), '--stage-checks-json', str(tree)],
                           capture_output=True, text=True, timeout=120, env=env)
        try:
            return json.loads(p.stdout)
        except ValueError:
            return {'error': (p.stderr or p.stdout)[-400:]}
    cases = []
    real = read(ROOT)
    tiers = {r.get('fn'): r.get('tier') for r in real.get('routes') or []}
    texts = [t for _l, t in real.get('findings') or []]
    cases.append(('Booked lands with the quick tier, and the Debut runs the full one',
                  tiers.get('_land_composed') == 'basic'
                  and tiers.get('_run_tests') == 'full', real.get('error') or tiers))
    cases.append(('every move that runs a check is named by a stage',
                  not any('no stage names it' in t for t in texts), texts))
    cases.append(('control: the real quick tier holds nothing unapproved',
                  all(q.get('approved') for q in real.get('quick') or [])
                  and real.get('quick'), real.get('quick')))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-stages-'))
    try:
        shutil.copytree(ROOT / 'tools', tmp / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        pb = tmp / 'tools' / 'precedent_branches.py'
        src = pb.read_text(encoding='utf-8')
        land = "ok, out = _check(root, wt, BASIC, dest=staging, since=stip)"
        cases.append(('the planted line is still where Booked lands', land in src, ''))
        pb.write_text(src.replace(land, "ok, out = _check(root, wt, FULL, dest=staging)", 1),
                      encoding='utf-8')
        ppc = tmp / 'tools' / 'precedent_push_check.py'
        src = ppc.read_text(encoding='utf-8')
        basic = 'BASIC_CHECKS = set(BASIC_CHECKS_APPROVED)'
        cases.append(('the planted line is still where the quick tier is built',
                      basic in src, ''))
        ppc.write_text(src.replace(basic, basic + " | {'doc_sync'}", 1), encoding='utf-8')
        planted = read(tmp)
        texts = [t for lvl, t in planted.get('findings') or [] if lvl == 'VIOLATION']
        cases.append(('a land onto staging that runs the full tier is a violation',
                      any(t.startswith('Booked') and 'full' in t for t in texts),
                      planted.get('error') or texts))
        cases.append(('a check in the quick tier with no approval is a violation',
                      any(t.startswith('doc_sync runs before every push') for t in texts),
                      texts))
        # THE MOVES A SET SUPPLIES ARE READ TOO (2026-10-30 very deep check:
        # Produce lives in a set's branch_moves tool, and the scan read only
        # precedent_branches.py, so it printed "`--full` on request: none").
        # A planted moves tool, named the way the engine finds one -- the
        # branch_moves key -- never by a set's name.
        (tmp / 'tools' / 'zz_moves.py').write_text(
            'core = None\n'
            'def _promote_to_main(root, wt):\n'
            '    return core._check(root, wt, core.FULL, dest=core.MAIN)\n'
            'def _promote_to_main_fast(root, wt):\n'
            '    return core._check(root, wt, core.BASIC, dest=core.MAIN)\n'
            'def main(root, argv):\n    return 0\n', encoding='utf-8')
        (tmp / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-moves', 'level': 'shared', 'branch_moves': 'tools/zz_moves.py'}),
            encoding='utf-8')
        moved = read(tmp)
        got = {r.get('fn'): (r.get('tier'), r.get('file')) for r in moved.get('routes') or []}
        cases.append(('Produce in a set\'s moves tool is read: the fast move runs the '
                      'quick tier, --full the full one, each from that file',
                      got.get('_promote_to_main_fast') == ('basic', 'tools/zz_moves.py')
                      and got.get('_promote_to_main') == ('full', 'tools/zz_moves.py'),
                      moved.get('error') or got))
        mv = tmp / 'tools' / 'zz_moves.py'
        mv.write_text(mv.read_text(encoding='utf-8').replace(
            'core.BASIC, dest=core.MAIN', 'core.FULL, dest=core.MAIN'), encoding='utf-8')
        texts = [t for lvl, t in read(tmp).get('findings') or [] if lvl == 'VIOLATION']
        cases.append(('a fast move into main in a set\'s moves tool that runs the full '
                      'tier is a violation, naming that file',
                      any('fast move' in t and 'tools/zz_moves.py' in t for t in texts),
                      texts))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as v
    trig = v._workflow_triggers(
        'on:\n  push:\n    branches: [main]\n  pull_request:\n    branches:\n'
        '      - main\n      - "release/*"\n  schedule:\n    - cron: x\njobs:\n')
    cases.append(('a workflow\'s push and pull-request branches are read',
                  trig == {'push': ['main'], 'pull_request': ['main', 'release/*']}, trig))
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_a_land_rebuilds_dated_outputs_two_days_left():
    """Two branches that rebuilt a dated document on different days merge
    without a conflict and leave two copies; the land rebuilds the declared
    output over the composed tree and keeps one (2026-10-17). The control:
    a land that touched no declared output rebuilds nothing.
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    name = 'a land leaves one dated copy of a declared output, not two'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dated-land-'))
    cases = []
    try:
        r = tmp / 'r'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(r))
        fixture_git(r, 'config', 'user.email', 'fixture@example.com')
        fixture_git(r, 'config', 'user.name', 'fixture')
        (r / 'tools').mkdir()
        (r / 'output').mkdir()
        (r / 'tools' / 'build_book.py').write_text(
            "import pathlib\n"
            "for f in pathlib.Path('output').glob('*.docx'):\n"
            "    f.unlink()\n"
            "pathlib.Path('output/book-2099-01-01.docx').write_bytes(b'built')\n",
            encoding='utf-8')
        (r / 'precedent.json').write_text(json.dumps({'generated': [{
            'paths': ['output/*.docx'], 'rebuild': ['tools/build_book.py']}]}),
            encoding='utf-8')
        (r / 'output' / 'book-2026-10-15.docx').write_bytes(b'older')
        (r / 'notes.md').write_text('x\n', encoding='utf-8')
        fixture_git(r, 'add', '-A')
        fixture_git(r, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'base')
        start = fixture_git(r, 'rev-parse', 'HEAD').stdout.strip()
        (r / 'notes.md').write_text('y\n', encoding='utf-8')
        fixture_git(r, '-c', 'core.hooksPath=/dev/null', 'commit', '-qam', 'prose only')
        got = pb._commit_declared_rebuilt(r, r, start, say=lambda *a: None)
        cases.append(('control: a land that touched no declared output rebuilds '
                      'nothing', got == [], str(got)))
        start = fixture_git(r, 'rev-parse', 'HEAD').stdout.strip()
        (r / 'output' / 'book-2026-10-16.docx').write_bytes(b'one day')
        (r / 'output' / 'book-2026-10-17.docx').write_bytes(b'the next')
        fixture_git(r, 'add', '-A')
        fixture_git(r, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm',
                    'two branches, two days, merged')
        got = pb._commit_declared_rebuilt(r, r, start, say=lambda *a: None)
        tree = sorted(fixture_git(r, 'ls-tree', '-r', '--name-only', 'HEAD',
                                  'output').stdout.split())
        cases.append(('the composed tree keeps one copy, the rebuilt one',
                      tree == ['output/book-2099-01-01.docx'], f'{tree} {got}'))
    except FixtureSetupError as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_a_land_in_a_shallow_clone_is_not_a_conflict():
    """A shallow clone that lacks the commit where staging and main parted
    made --land say "main conflicts with staging" (2026-10-20); git had only
    refused unrelated histories. The composition now deepens the clone and
    merges; one still too shallow says so. The control: a real conflict is
    still a conflict. The negative control: with the deepening neutered, the
    shallow case reads as something else, so the case can fail.
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    name = 'a land in a shallow clone deepens it, and never calls it a conflict'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-shallow-land-'))
    cases = []
    steps, reach = pb.DEEPEN_STEPS, pb._reach_merge_base
    quiet = lambda *a: None

    def commit(d, path, text):
        (d / path).write_text(text, encoding='utf-8')
        fixture_git(d, 'add', '-A')
        fixture_git(d, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', path)

    def clone(tag, *depth):
        c = tmp / tag
        fixture_git(tmp, 'clone', '-q', *depth, '--no-single-branch',
                    (tmp / 'origin.git').as_uri(), str(c))
        fixture_git(c, 'config', 'user.email', 'fixture@example.com')
        fixture_git(c, 'config', 'user.name', 'fixture')
        fixture_git(c, 'checkout', '-q', '-B', 'staging', 'origin/staging')
        return c, fixture_git(c, 'rev-parse', 'origin/main').stdout.strip()

    def compose(c, mtip):
        return pb._compose(c, c, [('main', mtip, 'Bring main in')], 'staging', quiet)
    try:
        seed = tmp / 'seed'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(seed))
        fixture_git(seed, 'config', 'user.email', 'fixture@example.com')
        fixture_git(seed, 'config', 'user.name', 'fixture')
        commit(seed, 'shared.md', 'base\n')
        fixture_git(seed, 'branch', 'staging')
        for i in range(5):
            commit(seed, f'm{i}.md', f'{i}\n')
        fixture_git(seed, 'checkout', '-q', 'staging')
        for i in range(5):
            commit(seed, f's{i}.md', f'{i}\n')
        fixture_git(tmp, 'clone', '-q', '--bare', str(seed), str(tmp / 'origin.git'))

        c, mtip = clone('deepened', '--depth=2')
        cases.append(('the fixture clone is shallow and lacks the merge base',
                      fixture_git(c, 'merge-base', 'HEAD', mtip, allow_failure=True)
                      .returncode != 0, ''))
        conflict, merged = compose(c, mtip)
        cases.append(('a shallow clone is deepened and main merges in',
                      conflict is None and merged == ['main'], str(conflict)))

        pb.DEEPEN_STEPS = (1,)
        c, mtip = clone('too-shallow', '--depth=2')
        conflict, merged = compose(c, mtip)
        why = conflict[3] if conflict else ''
        cases.append(('one deepening cannot fix says the clone is too shallow',
                      why.startswith(pb.TOO_SHALLOW) and 'unshallow' in why, why))
        pb._reach_merge_base = lambda *a, **k: None
        c, mtip = clone('neutered', '--depth=2')
        conflict, _m = compose(c, mtip)
        why = conflict[3] if conflict else ''
        cases.append(('negative control: with the deepening neutered, the shallow '
                      'case no longer says too shallow',
                      bool(conflict) and not why.startswith(pb.TOO_SHALLOW), why))
        pb.DEEPEN_STEPS, pb._reach_merge_base = steps, reach

        commit(seed, 'shared.md', 'staging side\n')
        fixture_git(seed, 'checkout', '-q', 'main')
        commit(seed, 'shared.md', 'main side\n')
        fixture_git(seed, 'push', '-q', str(tmp / 'origin.git'), 'main', 'staging')
        c, mtip = clone('conflict')
        conflict, _m = compose(c, mtip)
        why = conflict[3] if conflict else ''
        cases.append(('control: a real conflict in a full clone is still a '
                      'conflict, not too shallow',
                      bool(conflict) and not why.startswith(pb.TOO_SHALLOW)
                      and 'share no history' not in why, why))
    except FixtureSetupError as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pb.DEEPEN_STEPS, pb._reach_merge_base = steps, reach
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_branch_tiers():
    """The branch tiers (spec/BRANCH_TIERS_PLAN.md, Morgan, 2026-09-25,
    since narrowed): every push gets the basic check unless the person's
    `branch_push_checks` says full -- main and staging alike since
    2026-10-17 (main's full suite runs after the push, staging's at the
    Debut). tools/precedent_branches.py
    holds the rule; this pins what it answers.

    The cases that matter are the ones that would land unchecked work: a
    push whose destination cannot be read must come out FULL, and a typo in
    the setting must come out FULL."""
    import tempfile, json as _json
    name = 'branch tiers: every branch takes the quick checks unless the person asks for full'
    tool = ROOT / 'tools' / 'precedent_branches.py'
    if not tool.exists():
        not_applicable(name, 'tools/precedent_branches.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   PRECEDENT_ALLOW_ANY_AUTHOR='1')
        repo = tmp / 'repo'
        subprocess.run(['git', 'init', '-q', '-b', 'topic', str(repo)],
                       capture_output=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '--allow-empty',
                        '-m', 'x'], capture_output=True, env=env)
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'precedent-beta-v01'}), encoding='utf-8')
        nocfg = str(tmp / 'no-config.json')
        indiv = tmp / 'indiv'
        indiv.mkdir()
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(indiv)}}),
                       encoding='utf-8')

        def tier(branch, user_config=nocfg):
            return pb.tier_for_branch(repo, branch, user_config)[0]

        cases.append(('a working branch is basic by default', tier('claude/x') == 'basic'))
        cases.append(('main takes the quick checks; its full suite runs after '
                      'the push (2026-10-17)', tier('main') == 'basic'))
        cases.append(('staging under its new name takes the quick checks too, '
                      'like any branch (2026-10-17)',
                      tier('staging') == 'basic'))
        cases.append(("the repo's declared base_branch, its staging tier under "
                      "the old name, takes the quick checks: work lands there "
                      "(2026-10-17)",
                      tier('precedent-beta-v01') == 'basic'))
        cases.append(('staging_branch() names the declared branch until the '
                      'rename', pb.staging_branch(repo) == 'precedent-beta-v01'))

        (indiv / 'identity.json').write_text(_json.dumps(
            {'email': 'p@example.com', 'branch_push_checks': 'full'}), encoding='utf-8')
        cases.append(("the person's identity.json can raise other branches to "
                      "full", tier('claude/x', str(cfg)) == 'full'))
        cases.append(("...staging among them",
                      tier('precedent-beta-v01', str(cfg)) == 'full'))
        (indiv / 'identity.json').write_text(_json.dumps(
            {'email': 'p@example.com', 'branch_push_checks': 'bassic'}), encoding='utf-8')
        cases.append(('a value that is neither basic nor full is checked fully',
                      tier('claude/x', str(cfg)) == 'full'))
        (indiv / 'identity.json').write_text(_json.dumps(
            {'email': 'p@example.com', 'branch_push_checks': 'basic'}), encoding='utf-8')
        cases.append(('nothing the setting says raises main before the push',
                      tier('main', str(cfg)) == 'basic'))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'precedent-beta-v01', 'branch_push_checks': 'full'}),
            encoding='utf-8')
        cases.append(("a repo's own precedent.json wins over the person",
                      tier('claude/x', str(cfg)) == 'full'))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main'}), encoding='utf-8')
        cases.append(('a repo whose base_branch is main, with no staging '
                      'branch yet, promotes into main -- never into a staging '
                      'branch it does not have -- and a person with no '
                      'landing_branch lands there too',
                      pb.staging_branch(repo) == 'main'
                      and tier('staging') == 'basic'
                      and pb.landing_branch(repo, nocfg)[0] == 'main'))

        # Morgan, 2026-09-27 (strength: decided): the person's own
        # landing_branch wins; the repo's is the default for everyone who
        # names none; the built-in default stays staging.
        ident_before = (indiv / 'identity.json').read_text(encoding='utf-8')
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'nightly'}),
            encoding='utf-8')
        # A value that is neither staging nor main is one this engine does
        # not know: the repository's reads as the staging tier and says so,
        # and unknown_landing() names it for --land to refuse on.
        unknown_repo = pb.landing_branch(repo, str(cfg))
        cases.append(("a repo's own landing_branch applies to a person who names "
                      "none, and a value the engine does not know there reads "
                      "as the staging tier, saying why",
                      unknown_repo[0] == pb.staging_branch(repo)
                      and 'which this engine does not know, so it reads as '
                          'staging; --land refuses until it is fixed'
                      in unknown_repo[1]))
        said = pb.unknown_landing(repo, str(cfg)) or ''
        cases.append(("...and unknown_landing() names the value and where it is",
                      "landing_branch is 'nightly' in this repo's precedent.json, "
                      "a branch this engine does not know" in said))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'staging'}), encoding='utf-8')
        (indiv / 'identity.json').write_text(_json.dumps(
            {'email': 'p@example.com', 'landing_branch': 'nightly'}), encoding='utf-8')
        unknown_person = pb.landing_branch(repo, str(cfg))
        cases.append(("the person's own unknown value is passed over as if unset: "
                      "the repo's staging applies",
                      unknown_person[0] == pb.staging_branch(repo)
                      and "this repo's precedent.json" in unknown_person[1]))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'nightly'}), encoding='utf-8')
        (indiv / 'identity.json').write_text(_json.dumps(
            {'email': 'p@example.com', 'landing_branch': 'main'}), encoding='utf-8')
        cases.append(("the person's own landing_branch wins over the repo's",
                      pb.landing_branch(repo, str(cfg))[0] == 'main'))
        (indiv / 'identity.json').write_text(ident_before, encoding='utf-8')
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'staging'}), encoding='utf-8')
        kept = not pb.ensure_repo_landing(repo) and pb.precedent_json(repo).get(
            'landing_branch') == 'staging'
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main'}), encoding='utf-8')
        # A repository with no tiers asked for none: an update by a ladder
        # user leaves it on main (Morgan, 2026-10-02, strength: decided --
        # "nothing creates tiers in a repository that did not ask for
        # them"); a fresh install by that person is the asking.
        not_on_update = not pb.ensure_repo_landing(repo) and \
            'landing_branch' not in pb.precedent_json(repo)
        wrote = pb.ensure_repo_landing(repo, new_install=True, user_config=str(cfg))
        again = pb.ensure_repo_landing(repo, new_install=True, user_config=str(cfg))
        cases.append(('the repo default is written once, as staging, at a fresh '
                      'install, never by an update into a repository without '
                      'tiers, and never over a value the repo already has',
                      kept and not_on_update and wrote and not again and
                      pb.precedent_json(repo).get('landing_branch') == 'staging'
                      and pb.precedent_json(repo).get('base_branch') == 'main'))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main'}), encoding='utf-8')
        # A new repository starts on staging whatever the person declares
        # (2026-10-11).
        default_before = pb.repo_landing_default(repo, str(cfg))[0]
        (indiv / 'identity.json').write_text(_json.dumps(
            {**_json.loads(ident_before), 'promote_only': True}), encoding='utf-8')
        promote_default = pb.repo_landing_default(repo, str(cfg))[0]
        (indiv / 'identity.json').write_text(_json.dumps(
            {**_json.loads(ident_before), 'landing_branch': 'staging'}),
            encoding='utf-8')
        declared_default = pb.repo_landing_default(repo, str(cfg))[0]
        (indiv / 'identity.json').write_text(ident_before, encoding='utf-8')
        cases.append(('a new repository lands on staging for everyone, '
                      'whatever the person declares',
                      default_before == 'staging'
                      and promote_default == 'staging'
                      and declared_default == 'staging'))

        def targets(args):
            return pb.push_targets(repo, args)
        cases.append(('`origin some-feature` writes some-feature',
                      targets('origin some-feature') == ['some-feature']))
        cases.append(('`-u origin a b` writes a and b',
                      targets('-u origin a b') == ['a', 'b']))
        cases.append(('`origin +x:refs/heads/main` writes main',
                      targets('origin +x:refs/heads/main') == ['main']))
        cases.append(('`origin HEAD` writes the current branch',
                      targets('origin HEAD') == ['topic']))
        cases.append(('a bare push writes the current branch',
                      targets('') == ['topic']))
        cases.append(('`--tags` cannot be read, so it is None',
                      targets('--tags') is None))
        cases.append(('a tag refspec is not a branch, so it is None',
                      targets('origin v1:refs/tags/v1') is None))
        cases.append(('an unreadable push is checked fully',
                      pb.tier_for_push(repo, '--all', nocfg)[0] == 'full'))
        cases.append(('a push naming a working branch and main takes the quick '
                      'checks', pb.tier_for_push(repo, 'origin feat main', nocfg)[0] == 'basic'))
        subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '--detach'],
                       capture_output=True, env=env)
        cases.append(('a bare push from a detached HEAD cannot be read',
                      targets('') is None))
        # `git switch -c X && git push` from a detached HEAD: the hook runs
        # before the switch, and once ran the 14-minute full tier for it
        # (2026-10-20). Unread, it gets the landing branch's tier; the hook
        # names the branch the push will run on, and that is read instead.
        landing = pb.landing_branch(repo, nocfg)[0]
        landing_tier = pb.tier_for_branch(repo, landing, nocfg)[0]
        cases.append(('an unread bare push gets the landing branch\'s tier, '
                      'not the full one',
                      pb.tier_for_push(repo, '', nocfg)[0] == landing_tier
                      and 'landing branch' in pb.tier_for_push(repo, '', nocfg)[1]))
        sw = pb.branch_switched_to
        cases.append(('`git switch -c X && git push` runs the push on X',
                      sw(repo, 'git switch -c new-x && git push') == 'new-x'))
        cases.append(('`git checkout -b X; git push -u origin X` reads X',
                      sw(repo, 'git checkout -b y ; git push -u origin y') == 'y'))
        cases.append(('`git checkout FILE` changes no branch',
                      sw(repo, 'git checkout notes.md && git push') is None))
        cases.append(('`git checkout BRANCH` does',
                      sw(repo, 'git checkout topic && git push') == 'topic'))
        cases.append(('a switch AFTER the push is not read',
                      sw(repo, 'git push && git switch -c later') is None))
        old_env = os.environ.get(pb.PUSH_FROM_ENV)
        os.environ[pb.PUSH_FROM_ENV] = 'new-x'
        try:
            named = targets('')
            named_tier = pb.tier_for_push(repo, '', nocfg)
        finally:
            if old_env is None:
                os.environ.pop(pb.PUSH_FROM_ENV, None)
            else:
                os.environ[pb.PUSH_FROM_ENV] = old_env
        cases.append(('the branch the hook names is where a bare push goes',
                      named == ['new-x'] and 'landing branch' not in named_tier[1]))
        # 2026-10-31: `git checkout -b "$(...)" ... && git push -u origin
        # HEAD` was read as a push from the branch it left (main) and
        # refused as one. The hook blanks quoted text, so it sees spaces.
        made = ('git checkout -q -b "$(python3 tools/precedent_branch_name.py x)" '
                'origin/staging && git commit -q -m m && git push -u origin HEAD')
        blanked = ('git checkout -q -b "                                      " '
                   'origin/staging && git commit -q -m " " && git push -u origin HEAD')
        cases.append(('a branch made from a command substitution is unreadable, '
                      'never "no change"',
                      sw(repo, made) == pb.SWITCH_UNREADABLE
                      and sw(repo, blanked) == pb.SWITCH_UNREADABLE
                      and sw(repo, 'git switch "$B" && git push') == pb.SWITCH_UNREADABLE))
        os.environ[pb.PUSH_FROM_ENV] = pb.SWITCH_UNREADABLE
        try:
            unread = targets('-u origin HEAD')
            unread_tier = pb.tier_for_push(repo, '-u origin HEAD', nocfg)
        finally:
            if old_env is None:
                os.environ.pop(pb.PUSH_FROM_ENV, None)
            else:
                os.environ[pb.PUSH_FROM_ENV] = old_env
        cases.append(('...so its push goes nowhere readable: the landing '
                      'branch\'s tier, not the branch the command leaves',
                      unread is None and 'landing branch' in unread_tier[1]))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_merge_check_gate():
    """A pull request merged through GitHub is a push no push gate sees
    (spec/BRANCH_TIERS_PLAN.md, hole 1). merge-check-gate.sh runs
    tools/precedent_merge_check.py before the merge tool: the push check, on
    the merge GitHub would make, at the tier of the base branch.

    The fixture is a local "origin" carrying refs/pull/N/head and
    refs/pull/N/merge the way GitHub does. The cases that matter are the
    ones that would land unchecked work: a pull request into staging, for a
    person whose branch_push_checks says full, must get the full check; a base that cannot be matched must get it too; and a base branch
    sitting at the same commit as that branch -- exactly how
    AGENTS.md's merge-target rule began, and how this check's first live
    run misread a real pull request -- must not be mistaken for the
    working branch alone."""
    import tempfile, json as _json, shutil as _shutil
    name = 'the merge gate checks what a GitHub merge would land, at its base branch\'s tier'
    hook = ROOT / 'tools' / 'merge-check-gate.sh'
    engine = ROOT / 'tools' / 'precedent_merge_check.py'
    if not hook.exists() or not engine.exists():
        not_applicable(name, 'merge-check-gate.sh or precedent_merge_check.py is absent')
        return
    if not _shutil.which('jq'):
        not_applicable(name, 'no jq on this machine; the gate fails open without it')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-config.json'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a],
                                  capture_output=True, text=True, env=env)

        bare = tmp / 'alex' / 'proj.git'
        bare.parent.mkdir()
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        git(tmp, 'init', '-q', '-b', 'main', str(work))
        # precedent_repo_id is how the gate finds the checkout by its origin
        # (2026-10-31); every real repository has it with the engine.
        for f in ('precedent_push_check.py', 'precedent_branches.py',
                  'precedent_merge_check.py', 'precedent_repo_id.py'):
            _shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
        # precedent_time is copied as every real repository has it
        # (2026-10-19: without it each import fell back quietly, the copy
        # was named "copy-<unix time>", and no case could tell).
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer'}), encoding='utf-8')
        for t in ('precedent_check', 'leak_gate', 'doc_lint'):
            (work / 'tools' / f'{t}.py').write_text(
                'import pathlib, sys\n'
                'f = pathlib.Path("FAIL")\n'
                'body = f.read_text() if f.exists() else ""\n'
                + ('print("precedent_check: 3 passed, 0 violated")\n'
                   if t == 'precedent_check' else '')
                # precedent_check.py also answers as the basic tier's
                # ci_workflows (--only ci-workflow-approved), a check of
                # its own: fail it only when FAIL names that one.
                # ...and as the changed-files run (--changed-files-only).
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
                + 'sys.exit(1 if name in body else 0)\n',
                encoding='utf-8')
        # The tiers exist here, so a landing into staging holds it still.
        (work / 'precedent.json').write_text(
            _json.dumps({'landing_branch': 'staging'}), encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'init')
        git(work, 'remote', 'add', 'origin', f'file://{bare}')
        git(work, 'push', '-q', 'origin', 'main')
        # Since 2026-10-17 a pull request into main takes the quick checks
        # and its full suite runs after the merge (Morgan: "the full tests
        # should happen after that"), and so does one into staging: the
        # full check before a merge is for a
        # person whose branch_push_checks says full, and staging is the
        # base these cases use for one.
        git(work, 'checkout', '-q', '-b', 'staging')
        (work / 'staging.txt').write_text('staging', encoding='utf-8')
        git(work, 'add', 'staging.txt')
        git(work, 'commit', '-q', '-m', 'staging')
        git(work, 'push', '-q', 'origin', 'staging')
        git(work, 'checkout', '-q', 'main')
        # A base branch of its own, one commit past main.
        git(work, 'checkout', '-q', '-b', 'fb')
        (work / 'fb.txt').write_text('fb', encoding='utf-8')
        git(work, 'add', 'fb.txt')
        git(work, 'commit', '-q', '-m', 'fb')
        git(work, 'push', '-q', 'origin', 'fb')
        full_person = tmp / 'full-person'
        full_person.mkdir()
        (full_person / 'identity.json').write_text(_json.dumps(
            {'email': 'full@example.com', 'branch_push_checks': 'full'}),
            encoding='utf-8')
        full_cfg = tmp / 'full-config.json'
        full_cfg.write_text(_json.dumps(
            {'individual': {'path': str(full_person)}}), encoding='utf-8')

        def pull(number, base, fail):
            """Publish pull request `number` into `base` whose head plants
            FAIL=`fail`, with the test merge GitHub would make."""
            git(work, 'checkout', '-q', '-B', f'head{number}', base)
            (work / 'FAIL').write_text(fail, encoding='utf-8')
            git(work, 'add', 'FAIL')
            git(work, 'commit', '-q', '-m', f'pr {number}')
            git(work, 'push', '-q', 'origin', f'head{number}:refs/pull/{number}/head')
            git(work, 'checkout', '-q', '-B', f'merge{number}', base)
            git(work, 'merge', '-q', '--no-ff', '-m', f'merge {number}', f'head{number}')
            git(work, 'push', '-q', 'origin', f'merge{number}:refs/pull/{number}/merge')
            git(work, 'checkout', '-q', 'main')

        pull(7, 'staging', 'precedent_check')
        pull(6, 'main', 'precedent_check')
        pull(8, 'fb', 'precedent_check')
        pull(9, 'fb', 'leak_gate')
        # 10: a test merge whose first parent is no branch's tip.
        git(work, 'checkout', '-q', '-b', 'gone', 'main')
        (work / 'gone.txt').write_text('gone', encoding='utf-8')
        git(work, 'add', 'gone.txt')
        git(work, 'commit', '-q', '-m', 'gone')
        pull(10, 'gone', 'precedent_check')
        # 11: a working branch sitting at main's own commit, named so that
        # origin lists it BEFORE main -- the order that made this check's
        # first live run read a pull request into the staging branch as one
        # into a working branch.
        git(work, 'push', '-q', 'origin', 'staging:aaa-topic')

        def gate(payload, project=work):
            p = subprocess.run(['bash', str(hook)], input=_json.dumps(payload),
                               text=True, capture_output=True, timeout=300,
                               env=dict(env, CLAUDE_PROJECT_DIR=str(project)))
            return '"deny"' in p.stdout, p.stdout + p.stderr

        def mcp(number, owner='alex', repo='proj'):
            return gate({'tool_name': 'mcp__github__merge_pull_request',
                         'tool_input': {'owner': owner, 'repo': repo,
                                        'pullNumber': number},
                         'cwd': str(work)})

        denied, out = mcp(6)
        cases.append(('a pull request into main gets the quick check, so a '
                      'full-only failure is let through for the full suite '
                      'after the merge', not denied and '(basic)' in out))
        lock_log = lambda: git(bare, 'log', '--format=%s', 'precedent-promote-lock').stdout
        denied, out = mcp(7)
        cases.append(('a pull request into staging gets the quick check like '
                      'any other, so a full-only failure is let through for '
                      'the Debut', not denied and '(basic)' in out))
        before = lock_log()
        denied, out = mcp(8)
        cases.append(('a pull request into a working branch gets the basic '
                      'check, so the same failure is let through', not denied))
        cases.append(('...and holds nothing still, since a working branch is '
                      'not a tier anyone else lands on', lock_log() == before))
        denied, out = mcp(9)
        cases.append(('the basic check still refuses a failing leak gate',
                      denied and 'leak_gate' in out))
        # From here on, a person whose pushes are fully checked.
        env['PRECEDENT_USER_CONFIG'] = str(full_cfg)
        denied, out = mcp(7)
        cases.append(('a pull request into staging, for a person whose '
                      'branch_push_checks says full, gets the full check, and a '
                      'failing full-only check refuses the merge',
                      denied and 'merge check REFUSED' in out
                      and 'precedent_check' in out))
        held_log = lock_log()
        cases.append(('...staging was held still while that check ran: the gate '
                      'claimed the Promote lock for the landing and freed it '
                      'after', 'landing pull request #7 into' in held_log
                      and held_log.splitlines()[0] == 'free [skip ci]'))
        denied, out = mcp(10)
        cases.append(('a base that matches no branch on origin is checked '
                      'fully', denied and 'unmatched base' in out))
        pull(11, 'staging', 'precedent_check')
        denied, out = mcp(11)
        cases.append(('a base sitting at the same commit as staging is checked '
                      'fully, not read as the working branch alone',
                      denied and 'precedent_check' in out))
        denied, out = gate({'tool_name': 'Bash',
                            'tool_input': {'command': 'gh pr merge 7 --merge'},
                            'cwd': str(work)})
        cases.append(('`gh pr merge N` is checked the same way, the repository '
                      'read from origin', denied and 'precedent_check' in out))
        denied, out = gate({'tool_name': 'Bash',
                            'tool_input': {'command': 'echo "gh pr merge 7"'},
                            'cwd': str(work)})
        cases.append(('`gh pr merge` quoted inside another command is not a '
                      'merge', not denied and not out.strip()))
        denied, out = mcp(7, owner='nobody')
        cases.append(('no checkout of the repository: let through, and said',
                      not denied and 'NOTE: merge-check-gate' in out))
        tiers_file = (work / 'precedent.json').read_text(encoding='utf-8')
        (work / 'precedent.json').unlink()
        before = lock_log()
        mcp(7)
        cases.append(('a repository without the tiers holds nothing still: '
                      'no tier declared, so the lock branch is not touched',
                      lock_log() == before))
        (work / 'precedent.json').write_text(tiers_file, encoding='utf-8')

        # Another window holds main still (a Promote, or its own landing):
        # a fresh claim on the lock branch, made the way Promote makes one.
        empty = git(work, 'hash-object', '-t', 'tree', '/dev/null').stdout.strip()
        tip = git(bare, 'rev-parse', 'precedent-promote-lock').stdout.strip()
        claim = git(work, 'commit-tree', empty, '-p', tip, '-m',
                    'held by another window [skip ci]').stdout.strip()
        git(work, 'push', '-q', 'origin', f'{claim}:refs/heads/precedent-promote-lock')
        denied, out = mcp(7)
        cases.append(('while another window holds staging, a merge into it is '
                      'refused at once, naming the holder, and no check starts',
                      denied and 'held by another window' in out
                      and 'out of date' in out
                      and 'precedent_push_check:' not in out))
        cases.append(('...and the other window\'s claim is left as it was',
                      git(bare, 'rev-parse', 'precedent-promote-lock').stdout.strip()
                      == claim))
        # Free the claim above, as its holder would, before landing more.
        git(work, 'push', '-q', 'origin', git(work, 'commit-tree', empty, '-p', claim,
            '-m', 'free [skip ci]').stdout.strip() + ':refs/heads/precedent-promote-lock')
        # AFTER THE MERGE (PostToolUse). GitHub's merge is simulated by
        # pushing a merge commit to main; the hook is handed its sha the way
        # the merge tool answers.
        def landed(number, sha):
            p = subprocess.run(
                ['bash', str(hook)], text=True, capture_output=True, timeout=300,
                input=_json.dumps({'hook_event_name': 'PostToolUse',
                                   'tool_name': 'mcp__github__merge_pull_request',
                                   'tool_input': {'owner': 'alex', 'repo': 'proj',
                                                  'pullNumber': number},
                                   'tool_response': _json.dumps({'sha': sha, 'merged': True}),
                                   'cwd': str(work)}),
                env=dict(env, CLAUDE_PROJECT_DIR=str(work)))
            return p.stdout, p.stdout + p.stderr

        def tip(ref):
            return git(bare, 'rev-parse', ref).stdout.strip()

        # 12: nothing moves between the check and the merge.
        pull(12, 'staging', '')
        denied, out = mcp(12)
        merge12 = git(work, 'rev-parse', 'merge12').stdout.strip()
        git(work, 'push', '-q', 'origin', 'merge12:staging')
        stdout, out = landed(12, merge12)
        cases.append(('after a merge where nothing moved, what landed is the tree '
                      'the gate passed: its pass is reused and nothing is said',
                      not denied and not stdout.strip() and 'as checked' in out))
        # 13: staging moves in the gap to a commit that makes the merge fail.
        git(work, 'fetch', '-q', 'origin')
        git(work, 'checkout', '-q', '-B', 'head13', 'origin/staging')
        (work / 'pr13.txt').write_text('pr13', encoding='utf-8')
        git(work, 'add', 'pr13.txt')
        git(work, 'commit', '-q', '-m', 'pr 13')
        git(work, 'push', '-q', 'origin', 'head13:refs/pull/13/head')
        git(work, 'checkout', '-q', '-B', 'gap', 'origin/staging')
        (work / 'FAIL').write_text('precedent_check', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'another window lands in the gap')
        git(work, 'push', '-q', 'origin', 'gap:staging')
        git(work, 'checkout', '-q', '-B', 'merge13', 'gap')
        git(work, 'merge', '-q', '--no-ff', '-m', 'merge 13', 'head13')
        merge13 = git(work, 'rev-parse', 'merge13').stdout.strip()
        git(work, 'push', '-q', 'origin', 'merge13:staging')
        git(work, 'checkout', '-q', 'main')
        stdout, out = landed(13, merge13)
        after = tip('staging')
        cases.append(('after a merge where staging moved in the gap and what landed '
                      'fails its full check, the session is told',
                      '"block"' in stdout and 'MOVED' in out and 'FAILED' in out))
        cases.append(('...and staging is put back to the tree the other window '
                      'landed, by a new commit on top of the merge',
                      after != merge13
                      and git(bare, 'rev-parse', 'staging^{tree}').stdout
                      == git(work, 'rev-parse', 'gap^{tree}').stdout
                      and git(bare, 'rev-parse', 'staging^').stdout.strip() == merge13))
        cases.append(('...while the pull request\'s own branch keeps the work',
                      tip('refs/pull/13/head') == git(work, 'rev-parse', 'head13').stdout.strip()))
        # The same failure, with staging moved on again: never reverted over it.
        git(work, 'fetch', '-q', 'origin')
        git(work, 'checkout', '-q', '-B', 'later', 'origin/staging')
        (work / 'later.txt').write_text('later', encoding='utf-8')
        git(work, 'add', 'later.txt')
        git(work, 'commit', '-q', '-m', 'yet another landing')
        git(work, 'push', '-q', 'origin', 'later:staging')
        git(work, 'checkout', '-q', 'main')
        moved_on = tip('staging')
        stdout, out = landed(13, merge13)
        cases.append(('a base that moved on past the merge is reported, never '
                      'reverted over', tip('staging') == moved_on and 'NOT reverted' in out))
        stdout, out = subprocess.run(
            ['bash', str(hook)], text=True, capture_output=True, timeout=60,
            input=_json.dumps({'hook_event_name': 'PostToolUse',
                               'tool_name': 'mcp__github__merge_pull_request',
                               'tool_input': {'owner': 'alex', 'repo': 'proj',
                                              'pullNumber': 13},
                               'tool_response': 'failed to merge pull request',
                               'cwd': str(work)}),
            env=dict(env, CLAUDE_PROJECT_DIR=str(work))).stdout, ''
        cases.append(('a merge that did not happen is left alone', not stdout.strip()))
        wts = git(work, 'worktree', 'list').stdout.strip().splitlines()
        refs = git(work, 'for-each-ref', 'refs/precedent-merge-check').stdout.strip()
        cases.append(('no worktree and no fetched pull request ref is left '
                      'behind', len(wts) == 1 and not refs))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_promote_only_and_tier_branches():
    """Two 2026-09-25 additions to the branch tiers (spec/BRANCH_TIERS_PLAN.md).

    `promote_only`, a per-person opt-in: with it on, staging and main take
    work only by promotion. That day five changes reached a practice
    source's main without passing the tier below it, and nothing refused
    any of them. The cases that matter: it is OFF unless a person turns it on
    (Morgan asked for it as his own rule, not everyone's), a direct push or
    an off-tier pull request is refused with the way round named, and the
    promotion route itself -- staging into main -- is never refused. An ambiguous base is not refused either,
    since two branches at one commit is the normal state right after
    Promote.

    `--ensure-tiers`, the migration step that gives a repository both tier
    branches. A repo whose staging tier was main gains a real `staging`
    branch and a `staging_branch` key, and keeps `base_branch` -- which also
    pins a practice source's session clone -- exactly as it was."""
    import tempfile, json as _json, shutil as _shutil
    name = ('promote_only refuses direct pushes and off-tier merges for the '
            'person who sets it; --ensure-tiers makes staging')
    tool = ROOT / 'tools' / 'precedent_branches.py'
    if not tool.exists():
        not_applicable(name, 'tools/precedent_branches.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    if not hasattr(pb, 'direct_push_refusal'):
        check(name, False, 'precedent_branches.py has no direct_push_refusal')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   GIT_CONFIG_NOSYSTEM='1',
                   PRECEDENT_USER_CONFIG=str(tmp / 'config.json'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a],
                                  capture_output=True, text=True, env=env)

        bare = tmp / 'origin.git'
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        git(tmp, 'init', '-q', '-b', 'main', str(work))
        for f in ('precedent_push_check.py', 'precedent_branches.py', 'precedent_time.py'):
            _shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer'}), encoding='utf-8')
        # A repository whose staging tier is main: the shape every practice
        # source and most installs had on 2026-09-25.
        # The repository asks for tiers (its landing_branch names one):
        # promote_only means something only where there are tiers to
        # promote through (Morgan, 2026-10-02, strength: decided).
        (work / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'staging'}),
            encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'init')
        git(work, 'remote', 'add', 'origin', f'file://{bare}')
        git(work, 'push', '-q', 'origin', 'main')

        indiv = tmp / 'indiv'
        indiv.mkdir()
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(indiv)}}),
                       encoding='utf-8')

        def person(**settings):
            (indiv / 'identity.json').write_text(_json.dumps(
                {'email': 'p@example.com', **settings}), encoding='utf-8')

        def push_refused(args):
            return pb.direct_push_refusal(work, args, str(cfg))

        def merge_refused(bases, heads):
            return pb.merge_refusal(work, bases, heads, str(cfg))

        # --- off unless the person turns it on ---
        person()
        cases.append(('off by default: a push to main is not refused',
                      push_refused('origin main') is None))
        cases.append(('off by default: a pull request into main from a working '
                      'branch is not refused',
                      merge_refused(['main'], ['claude/x']) is None))
        person(promote_only='yes')
        cases.append(('only a literal true turns it on', push_refused('origin main') is None))

        # --- on ---
        person(promote_only=True)
        why = push_refused('origin main') or ''
        cases.append(('on: a push to main is refused, naming the setting and the '
                      'way round: with no staging branch yet, make one and '
                      'land there', 'promote_only is on' in why
                      and '--ensure-tiers --apply' in why and 'Promote' in why, why))
        cases.append(('on: a refspec onto main is refused too',
                      push_refused('origin HEAD:main') is not None))
        cases.append(('on: a push to staging is refused',
                      push_refused('origin staging') is not None))
        # The first landing (promote-only's first-install exception, Morgan,
        # 2026-10-08): a push into a remote holding no branch at all creates
        # main and goes through; the remote above, which has main, refuses.
        empty = tmp / 'empty.git'
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(empty))
        git(work, 'remote', 'add', 'fresh', f'file://{empty}')
        cases.append(('on: the first push into an empty remote creates main and '
                      'goes through', push_refused('fresh HEAD:main') is None))
        cases.append(('on: a remote that cannot be asked keeps the push refused',
                      push_refused('nosuchremote main') is not None))
        cases.append(('on: a push to a working branch goes through',
                      push_refused('origin claude/x') is None))
        cases.append(('on: staging into main is the promotion route, never refused',
                      merge_refused(['main'], ['staging']) is None))
        # A to-main- copy left behind when staging moved (2026-10-06): the
        # refusal says it is out of date and to make a fresh one, never to
        # retarget it.
        why = merge_refused(['main'], ['to-main-20261006T090733-0300']) or ''
        cases.append(('on: a stale to-main copy into main is refused as out of '
                      'date, with a fresh Produce as the remedy',
                      'out of date' in why and 'Never retarget' in why, why))
        why = merge_refused(['staging'], ['claude/x']) or ''
        cases.append(('on: a working branch into staging is refused while there '
                      'is no staging branch, saying to make one',
                      '--ensure-tiers --apply' in why, why))
        cases.append(('on: a working branch straight into main is refused',
                      merge_refused(['main'], ['claude/x']) is not None))
        # promote-only's red-main exception (Morgan, 2026-10-11, assented):
        # a fix built on main's tip goes straight in while main's own GitHub
        # test is red; green, or not built on main, it is refused as before.
        mtip = git(work, 'rev-parse', 'main').stdout.strip()
        git(work, 'commit', '-q', '--allow-empty', '-m', 'fix main')
        fix_sha = git(work, 'rev-parse', 'HEAD').stdout.strip()
        git(work, 'reset', '-q', '--hard', mtip)
        git(work, 'fetch', '-q', 'origin')
        saved_failed = pb.main_test_failed
        try:
            pb.main_test_failed = lambda _root: True
            cases.append(('on: while main\'s test is red, a fix built on main '
                          'goes straight into main',
                          pb.merge_refusal(work, ['main'], ['claude/fix'],
                                           str(cfg), head_sha=fix_sha) is None))
            cases.append(('on: while main\'s test is red, a branch not built on '
                          "main's tip is still refused",
                          pb.merge_refusal(work, ['main'], ['claude/old'], str(cfg),
                                           head_sha='0' * 40) is not None))
            pb.main_test_failed = lambda _root: False
            cases.append(('on: with main\'s test green, the same fix is refused',
                          pb.merge_refusal(work, ['main'], ['claude/fix'],
                                           str(cfg), head_sha=fix_sha) is not None))
            # 2026-10-28: a practice set runs no GitHub test, so a fix-main
            # branch with no recorded failure was told "only from staging".
            why = pb.merge_refusal(work, ['main'],
                                   ['2026-10-28-zz-fix-main-a-word-ab-cd'],
                                   str(cfg), head_sha=fix_sha) or ''
            cases.append(('on: a fix-main branch with no red verdict here is told '
                          'what is missing and how to record it, never only '
                          '"from staging"', 'is a fix for a red main' in why
                          and '--run-tests main' in why, why))
        finally:
            pb.main_test_failed = saved_failed
        # ...and red means the full local suite too, where GitHub's test was
        # not due: Produce says to fix main at once if `--run-tests main`
        # fails, and that fix was refused (a consumer, 2026-10-19).
        rmtip = pb._remote_tip(work, pb.MAIN)
        record = pb._run_tests_path(work)
        try:
            pb._record_run_tests(work, {'branch': pb.MAIN, 'commit': rmtip,
                                        'result': 'failed', 'failed': []})
            cases.append(('on: a failed full local suite on main\'s own tip is a red '
                          'main', pb.main_test_failed(work) is True))
            pb._record_run_tests(work, {'branch': pb.MAIN, 'commit': '0' * 40,
                                        'result': 'failed', 'failed': []})
            cases.append(('on: one recorded on an older main is not',
                          pb.main_test_failed(work) is False))
            pb._record_run_tests(work, {'branch': pb.MAIN, 'commit': rmtip,
                                        'result': 'passed', 'failed': []})
            cases.append(('on: nor is a passed one', pb.main_test_failed(work) is False))
        finally:
            if record:
                pathlib.Path(record).unlink(missing_ok=True)
        # promote-only's content exception (Morgan, 2026-10-13, decided): a
        # change touching only declared content_paths goes straight into
        # main; anything else beside it, precedent.json included, does not.
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import precedent_resolve  # noqa: F401 -- content_only reads it
        finally:
            sys.path.pop(0)
        base_tip = git(work, 'rev-parse', 'main').stdout.strip()
        (work / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'landing_branch': 'staging',
             'content_paths': ['content/']}), encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'declare content')
        git(work, 'push', '-q', 'origin', 'HEAD:main')
        decl_tip = git(work, 'rev-parse', 'HEAD').stdout.strip()

        def change(*files):
            git(work, 'reset', '-q', '--hard', decl_tip)
            for f in files:
                (work / f).parent.mkdir(parents=True, exist_ok=True)
                (work / f).write_text('- [ ] buy milk\n', encoding='utf-8')
            git(work, 'add', '-A')
            git(work, 'commit', '-q', '-m', 'add')
            return git(work, 'rev-parse', 'HEAD').stdout.strip()
        try:
            sha = change('content/list.md')
            cases.append(('on: a change only to content_paths is pushed straight '
                          'to main', push_refused('origin HEAD:main') is None))
            cases.append(('on: ...and its pull request into main is merged',
                          pb.merge_refusal(work, ['main'], ['claude/add'],
                                           str(cfg), head_sha=sha) is None))
            sha = change('content/list.md', 'notes.md')
            cases.append(('on: a file outside content_paths beside it is refused',
                          push_refused('origin HEAD:main') is not None
                          and pb.merge_refusal(work, ['main'], ['claude/add'],
                                               str(cfg), head_sha=sha) is not None))
            git(work, 'reset', '-q', '--hard', decl_tip)
            (work / 'precedent.json').write_text(_json.dumps(
                {'base_branch': 'main', 'landing_branch': 'staging',
                 'content_paths': ['content/', 'notes.md']}), encoding='utf-8')
            git(work, 'commit', '-q', '-am', 'widen content')
            cases.append(('on: widening content_paths in the same change is refused',
                          push_refused('origin HEAD:main') is not None))
        finally:
            git(work, 'push', '-q', '-f', 'origin', f'{base_tip}:refs/heads/main')
            git(work, 'reset', '-q', '--hard', base_tip)
            git(work, 'fetch', '-q', 'origin')
        cases.append(('on: an ambiguous base (a working branch and staging at '
                      'one commit) is not refused',
                      merge_refused(['claude/y', 'staging'], ['claude/x']) is None))
        (work / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'promote_only': False}), encoding='utf-8')
        cases.append(("a repository's own precedent.json overrides the person, "
                      'as every branch setting does', push_refused('origin main') is None))
        (work / 'precedent.json').write_text(_json.dumps({'base_branch': 'main'}),
                                             encoding='utf-8')

        # The push gate's own entry point refuses before running anything.
        p = subprocess.run([sys.executable, 'tools/precedent_push_check.py', '--gate',
                            '--push-command', 'origin main'], cwd=work,
                           capture_output=True, text=True, env=env)
        cases.append(('the push gate refuses a direct push to main, exit 1, with '
                      'the refusal in its output',
                      p.returncode == 1 and 'REFUSED' in p.stderr
                      and 'promote_only is on' in p.stderr,
                      f'exit {p.returncode}: {failure_detail(p.stdout + p.stderr, 300)}'))

        # --- ensure-tiers ---
        def branches(*a):
            q = subprocess.run([sys.executable, 'tools/precedent_branches.py', *a],
                               cwd=work, capture_output=True, text=True, env=env)
            return q.returncode, q.stdout + q.stderr

        def tip(b):
            return git(work, 'ls-remote', 'origin', f'refs/heads/{b}').stdout.split('\t')[0]

        rc, out = branches('--ensure-tiers')
        cases.append(('report mode on a main-only repo: exit 1, naming what is '
                      'missing, changing nothing',
                      rc == 1 and 'missing' in out and not tip('staging'),
                      failure_detail(out, 300)))
        rc, out = branches('--ensure-tiers', '--apply')
        data = _json.loads((work / 'precedent.json').read_text(encoding='utf-8'))
        cases.append(('--apply creates staging on origin at main',
                      rc == 0 and tip('staging') == tip('main')
                      and bool(tip('main')), failure_detail(out, 300)))
        cases.append(('--apply writes staging_branch and leaves base_branch on main',
                      data.get('staging_branch') == 'staging'
                      and data.get('base_branch') == 'main'))
        cases.append(('the staging tier is now the staging branch',
                      pb.staging_branch(work) == 'staging'))
        rc, out = branches('--ensure-tiers')
        cases.append(('a second report finds both present, exit 0',
                      rc == 0 and 'both present' in out, failure_detail(out, 200)))

        # --- Promote's own merge commits carry the repository's zone ---
        # 2026-09-25: an individual source refused its own Promote because
        # the merge commit this module made carried the container's -0400.
        # PRECEDENT_COMMIT_TZ is the ladder's override rung, so it is cleared
        # here: the case is about which zone the REPOSITORY declares. So is
        # the user-level config: since the evening of 2026-09-25 its
        # individual source supplies the person's zone (rung 3), and this
        # machine's own person must not decide the case.
        saved = {k: os.environ.pop(k) for k in ('PRECEDENT_COMMIT_TZ',
                                                  'PRECEDENT_USER_CONFIG')
                 if k in os.environ}
        os.environ['PRECEDENT_USER_CONFIG'] = str(work / 'no-user-config.json')
        old_tz = os.environ.get('TZ')
        try:
            (work / 'identity.json').write_text(_json.dumps(
                {'email': 'p@example.com',
                 'timezone': 'America/Argentina/Buenos_Aires'}), encoding='utf-8')
            zone_decl = pb._merge_env(work).get('TZ')
            (work / 'identity.json').unlink()
            os.environ['TZ'] = 'Asia/Tokyo'
            zone_env = pb._merge_env(work).get('TZ')
        finally:
            if old_tz is None:
                os.environ.pop('TZ', None)
            else:
                os.environ['TZ'] = old_tz
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
            os.environ.update(saved)
        cases.append(("Promote's merge commits are dated in the zone the "
                      "repository's identity.json declares",
                      zone_decl == 'America/Argentina/Buenos_Aires', str(zone_decl)))
        cases.append(('with no zone declared, they keep the environment TZ, as '
                      'before', zone_env == 'Asia/Tokyo', str(zone_env)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_main_test_minutes_rule():
    """Morgan, 2026-10-01: "I really want to make sure that github minutes
    only run if it's main AND (it's a public repo OR (that user's
    precedent-individual has it enabled AND it's been the # of hours or more
    listed in ci_every_hours))".

    Three independent views of the same rule, so one cannot hide a mistake
    in another: (1) the light-check template's own `on:` and job `if:`,
    evaluated against every event that could start it; (2) every combination
    of visibility, switch, hours and time since the last pass, through
    Promote's decision AND the template together, compared with the rule;
    (3) a real Promote into main in a scratch repository, reading the branch
    name it actually pushed. The deliberate exceptions -- where it runs
    although the rule alone would not -- are asserted separately and named,
    so a change to any of them is a visible decision, not drift."""
    import importlib.util, itertools, json as _json, shutil as _shutil, tempfile
    import time as _time
    name = "GitHub minutes run only on main, and in a private repo only when switched on and due"
    src = ROOT / 'tools' / 'precedent_branches.py'
    tpl = ROOT / 'templates' / 'github-actions' / 'light-check.yml.template'
    try:
        import yaml as _yaml
    except ImportError:
        not_applicable(name, 'PyYAML is not installed, and the template is read with it')
        return
    if not src.exists() or not tpl.is_file():
        not_applicable(name, 'tools/precedent_branches.py or the light-check template is absent')
        return
    spec = importlib.util.spec_from_file_location('_pb_minutes', src)
    pb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pb)
    cases = []
    doc = _yaml.safe_load(tpl.read_text(encoding='utf-8'))
    on = doc.get('on', doc.get(True)) or {}
    expr = doc['jobs']['light-check']['if']

    def starts(event, branch, private, head_ref=''):
        """-> True when GitHub would start a runner: a trigger matches, then
        the job's if: holds. `branch` is the pushed branch, or the pull
        request's base."""
        trig = on.get(event, None) if isinstance(on, dict) else None
        if event not in on:
            return False
        branches = (trig or {}).get('branches') if isinstance(trig, dict) else None
        if branches is not None and branch not in branches:
            return False
        return _gh_if(expr, event, private, head_ref)

    # (1) Every event shape, against the rule's first half: never off main.
    for private in (False, True):
        kind = 'private' if private else 'public'
        for b in ('staging', 'claude/feature-x'):
            cases.append((f'{kind}: a push to {b} starts no runner',
                          not starts('push', b, private)))
            cases.append((f'{kind}: a pull request into {b} starts no runner',
                          not starts('pull_request', b, private, 'claude/feature-x')))
    cases.append(('public: a push to main runs (a public repo tests every push to main)',
                  starts('push', 'main', False)))
    cases.append(('private: a push to main starts no runner, ever',
                  not starts('push', 'main', True)))
    cases.append(('private: a Promote copy that is NOT DUE starts no runner',
                  not starts('pull_request', 'main', True, pb.NOT_DUE_PREFIX + '2026-10-01')))
    cases.append(('public: a not-due name is ignored, and the test runs',
                  starts('pull_request', 'main', False, pb.NOT_DUE_PREFIX + '2026-10-01')))
    cases.append(('private: a Promote copy that IS due runs',
                  starts('pull_request', 'main', True, 'to-main-2026-10-01')))
    cases.append(('private: a pull request into main from a working branch -- not a '
                  'Promote copy, so nobody judged it -- starts no runner',
                  not starts('pull_request', 'main', True, 'claude/feature-x')))
    cases.append(('...nor one from staging itself',
                  not starts('pull_request', 'main', True, 'staging')))
    cases.append(('...nor "x-to-main-...": the copy name is matched as a prefix',
                  not starts('pull_request', 'main', True, 'x-to-main-2026-10-01')))
    # The session-branch names a Promote's copies carry since 2026-10-06.
    cases.append(('private: a copy named like a session branch that IS due runs',
                  starts('pull_request', 'main', True,
                         'claude/2026-10-06-promote-to-main-y1ktn')))
    cases.append(('private: one that is NOT DUE starts no runner',
                  not starts('pull_request', 'main', True,
                             'claude/2026-10-06-promote-to-main-not-due-y1ktn')))
    cases.append(('...and what Promote names them is what the template reads',
                  pb.is_main_copy('claude/2026-10-06-promote-to-main-y1ktn')
                  and pb.is_main_copy('claude/2026-10-06-promote-to-main-not-due-y1ktn')
                  and pb.COPY_NAME_MARKER in tpl.read_text(encoding='utf-8')))
    # A DELIBERATE EXCEPTION, named so it stays a decision: GitHub's if: has
    # no pattern matching, so a hand-named branch whose slug happens to say
    # "promote-to-main" reads as a copy there. It would run one test on a
    # private pull request into main; the engine's own reading is exact.
    cases.append(('EXCEPTION: a branch whose slug says promote-to-main runs there, '
                  'and only there -- the engine does not take it for a copy',
                  starts('pull_request', 'main', True,
                         'claude/2026-10-06-merge-promote-to-main-docs-y1ktn')
                  and not pb.is_main_copy('claude/2026-10-06-merge-promote-to-main-docs-y1ktn')))
    cases.append(('public: a pull request into main from a working branch runs',
                  starts('pull_request', 'main', False, 'claude/feature-x')))
    cases.append(('a run started by hand runs in either kind of repository',
                  starts('workflow_dispatch', 'main', True)
                  and starts('workflow_dispatch', 'main', False)))

    # (2) The whole table, through Promote's decision and the template.
    saved_force = os.environ.pop(pb.FORCE_ENV, None)
    WF = '.github/workflows/light-check.yml'
    now = _time.time()

    class GH:
        def __init__(self, hours_ago):
            self.hours_ago = hours_ago

        def call(self, path, cache=True):
            if self.hours_ago is None:
                return {'workflow_runs': []}, None
            return {'workflow_runs': [{
                'path': WF, 'status': 'completed', 'conclusion': 'success',
                'head_branch': 'to-main-2026-09-20', 'html_url': 'U',
                'created_at': _time.strftime('%Y-%m-%dT%H:%M:%SZ', _time.gmtime(
                    now - self.hours_ago * 3600))}]}, None
    pb._slug = lambda root: 'o/r'
    pb.github_tests = lambda root, sha: [(WF, True)]
    real_git = pb._git
    pb._git = lambda root, *a: (('on: {}\n# ' + pb.NOT_DUE_PREFIX) if a[:1] == ('show',)
                                else '' if a[:2] == ('diff', '--name-only')
                                else real_git(root, *a))
    wrong = []
    rows = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        repo, me = tmp / 'repo', tmp / 'me'
        repo.mkdir()
        me.mkdir()
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(me)}}), encoding='utf-8')
        visibilities = ('public', 'private', None)
        switches = ('enabled', 'disabled', 'disable', None)      # None = not declared
        hours_set = (0, 24, 168, None, 'weekly')                 # None = not declared
        last_pass = (1, 23, 25, 167, 169, 1000, None)            # hours ago; None = never
        for vis, sw, hrs, ago in itertools.product(visibilities, switches, hours_set, last_pass):
            pj = {'base_branch': 'main'}
            if vis:
                pj['visibility'] = vis
            (repo / 'precedent.json').write_text(_json.dumps(pj), encoding='utf-8')
            ident = {'email': 'me@example.com'}
            if sw is not None:
                ident['ci_workflows'] = sw
            if hrs is not None:
                ident['ci_every_hours'] = hrs
            (me / 'identity.json').write_text(_json.dumps(ident), encoding='utf-8')
            private = vis == 'private'
            due, why = pb.main_test_due(repo, 'TIP', gh=GH(ago), user_config=cfg)
            copy = ('to-main-' if due else pb.NOT_DUE_PREFIX) + '2026-10-01'
            ran = starts('pull_request', 'main', private, copy)
            # The rule, written out as Morgan wrote it. An undeclared or
            # non-numeric hours value is 0 (every Promote); an undeclared
            # switch is on (his "assume yes"); a typo is off.
            on_ = sw in ('enabled', None)
            h = hrs if isinstance(hrs, (int, float)) and not isinstance(hrs, bool) else 0
            elapsed = ago is None or ago >= h
            expected = (not private) or (on_ and elapsed)
            rows += 1
            if ran != expected:
                wrong.append(f'{vis}/{sw}/{hrs}h/last {ago}h ago: ran={ran}, rule says '
                             f'{expected} ({why})')
        cases.append((f'all {rows} combinations of visibility, switch, hours and time '
                      f'since the last pass run exactly when the rule says',
                      not wrong))

        # The deliberate exceptions: each RUNS although the rule alone would
        # not, because its inputs say the window cannot be trusted. Asserted,
        # so dropping one is a decision someone makes in this file.
        (repo / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'visibility': 'private'}), encoding='utf-8')
        (me / 'identity.json').write_text(_json.dumps(
            {'email': 'me@example.com', 'ci_workflows': 'enabled', 'ci_every_hours': 168}),
            encoding='utf-8')
        d, _ = pb.main_test_due(repo, 'TIP', gh=GH(10), user_config=cfg)
        cases.append(('baseline for the exceptions: enabled, 168h, passed 10h ago -> not due',
                      d is False))

        class FailGH(GH):
            def call(self, path, cache=True):
                data, _ = super().call(path)
                data['workflow_runs'].insert(0, dict(data['workflow_runs'][0],
                                                     conclusion='failure', created_at=_time.strftime(
                                                         '%Y-%m-%dT%H:%M:%SZ', _time.gmtime(now - 3600))))
                return data, None

        class DownGH:
            def call(self, path, cache=True):
                return None, 'HTTP 503'
        exceptions = [
            ('a failed newest run', lambda: pb.main_test_due(repo, 'TIP', gh=FailGH(10), user_config=cfg)),
            ('GitHub not answering', lambda: pb.main_test_due(repo, 'TIP', gh=DownGH(), user_config=cfg)),
        ]
        for label, fn in exceptions:
            d, why = fn()
            cases.append((f'EXCEPTION, runs inside the window: {label} ({why[:60]})', d is True))
        pb._git = lambda root, *a: ('on: {}\n' if a[:1] == ('show',) else ''
                                    if a[:2] == ('diff', '--name-only') else real_git(root, *a))
        d, why = pb.main_test_due(repo, 'TIP', gh=GH(10), user_config=cfg)
        cases.append(('EXCEPTION, runs inside the window: an installed workflow older '
                      'than the skip (it would run anyway)', d is True))
        pb._git = real_git
        os.environ[pb.FORCE_ENV] = '1'
        d, why = pb.main_test_due(repo, 'TIP', gh=GH(10), user_config=cfg)
        os.environ.pop(pb.FORCE_ENV, None)
        cases.append((f'EXCEPTION, a person asking: {pb.FORCE_ENV}=1 runs it', d is True))

        # (3), a real Promote into main and the branch name it pushes, is
        # tested with the move itself, in the set that ships it (2026-10-19,
        # spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md piece 5c).
    if saved_force is not None:
        os.environ[pb.FORCE_ENV] = saved_force
    failed = [n for n, ok in cases if not ok]
    detail = '; '.join(failed) + ((' | ' + ' | '.join(wrong[:5])) if wrong else '')
    check(f'{name} ({len(cases)} stated cases, {rows} table rows)', not failed, detail)


def check_private_repo_skipped_gate_is_not_main_test():
    """A workflow GitHub never runs in this repository is not one of main's
    GitHub tests, and nothing else changes (2026-10-09).

    THE INCIDENT. In a private consuming repository the pull request into
    main showed the light check passed and leak-gate.yml "skipped": its
    template gates its only job on `github.event.repository.private != true`.
    A skipped run never counts as a pass, so --wait-main-test said
    "leak-gate.yml never ran on it. Do not merge" on every pull request,
    for good, and the Promote blamed an Update Vendors that would bring the
    same file. One definition, precedent_branches.skipped_by_design, read by
    github_tests and precedent_ci_verified alike.

    The engine half (2026-10-20): what github_tests, skipped_by_design,
    main_test_due and precedent_ci_verified say, and that each shipped
    template carries the not-due skip exactly when NOT_DUE_SKIP_TEMPLATES
    says so. The wait on main's test that reads them is the ladder set's,
    and its half of this case is tested there.

    THE NEGATIVE CASES ARE THE POINT: the same skipped run in a public
    repository, and a skipped workflow that is NOT gated on privacy in a
    private one, still never read as passed."""
    import importlib.util, json as _json, subprocess as _sp, tempfile
    name = 'a workflow skipped by design in a private repository is not main\'s GitHub test'
    src = ROOT / 'tools' / 'precedent_branches.py'
    tpl_dir = ROOT / 'templates' / 'github-actions'
    leak_tpl, light_tpl = (tpl_dir / 'leak-gate.yml.template',
                           tpl_dir / 'light-check.yml.template')
    if not (src.exists() and leak_tpl.is_file() and light_tpl.is_file()):
        not_applicable(name, 'precedent_branches.py or a workflow template is absent')
        return
    spec = importlib.util.spec_from_file_location('_pb_skipped_by_design', src)
    pb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pb)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_ci_verified as pciv
    finally:
        sys.path.pop(0)
    cases = []
    for t in sorted(tpl_dir.glob('*.yml.template')):
        wf = t.name[:-len('.template')]
        cases.append((f'NOT_DUE_SKIP_TEMPLATES names {wf} exactly when its template '
                      f'carries the not-due skip',
                      (pb.NOT_DUE_PREFIX in t.read_text(encoding='utf-8'))
                      == (wf in pb.NOT_DUE_SKIP_TEMPLATES)))
    LEAK, LIGHT, OTHER = ('.github/workflows/leak-gate.yml',
                          '.github/workflows/light-check.yml',
                          '.github/workflows/other.yml')
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'repo'
        wfd = repo / '.github' / 'workflows'
        wfd.mkdir(parents=True)

        def git(*a):
            return _sp.run(['git', *a], cwd=repo, env=env, capture_output=True,
                           text=True, check=True).stdout.strip()

        def commit(visibility, files):
            pj = {'base_branch': 'main', 'github_ci_main_test': 168}
            if visibility:
                pj['visibility'] = visibility
            (repo / 'precedent.json').write_text(_json.dumps(pj), encoding='utf-8')
            for p in list(wfd.iterdir()):
                p.unlink()
            for path, text in files.items():
                (repo / path).write_text(text, encoding='utf-8')
            git('add', '-A')
            git('commit', '-q', '--allow-empty', '-m', 'fixture')
            return git('rev-parse', 'HEAD')

        git('init', '-q', '-b', 'main')
        # Named, as this repository's own leak-gate.yml is:
        # precedent_ci_verified expects only a workflow with a `name:`.
        real = {LEAK: 'name: Leak gate\n' + leak_tpl.read_text(encoding='utf-8'),
                LIGHT: light_tpl.read_text(encoding='utf-8')}
        # Gated, but not on privacy: skipped for its own reason.
        other = ('name: Other\non:\n  pull_request:\n    branches: [main]\n'
                 'jobs:\n  other:\n    if: github.event_name == \'push\'\n'
                 '    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n')
        # Two jobs, only one gated on privacy: the other still runs.
        half = ('name: Half\non:\n  pull_request:\njobs:\n  a:\n'
                '    if: ${{ github.event.repository.private != true }}\n'
                '    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n'
                '  b:\n    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n')
        # The negated form, and a privacy gate that is one `&&` part.
        negated = ('name: Neg\non:\n  pull_request:\njobs:\n  n:\n'
                   '    if: >-\n      (!github.event.repository.private)\n'
                   '      && github.actor != \'bot\'\n'
                   '    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n')

        def run(path, conclusion):
            return {'path': path, 'status': 'completed', 'conclusion': conclusion,
                    'created_at': '2026-10-09T12:00:00Z', 'html_url': 'U'}

        class GH:
            def __init__(self, runs):
                self.runs = runs

            def call(self, path, cache=True):
                if path == 'repos/o/r':
                    return {'full_name': 'o/r'}, None
                if '/pulls' in path:
                    return [], None
                if '/actions/workflows/' in path:
                    wf = path.split('/actions/workflows/')[1].split('/')[0]
                    return {'workflow_runs': [
                        dict(r, head_branch='main', created_at='2026-10-09T12:00:00Z')
                        for r in self.runs if r['path'].endswith('/' + wf)
                        and r['conclusion'] == 'success']}, None
                return {'workflow_runs': self.runs}, None

        pb._slug = lambda root: 'o/r'
        incident = [run(LIGHT, 'success'), run(LEAK, 'skipped')]

        sha = commit('private', real)
        cases.append(('(a) private repo: leak-gate.yml is not one of main\'s GitHub '
                      'tests there, and the light check still is',
                      [p for p, _ in pb.github_tests(repo, sha)] == [LIGHT]))
        cases.append(('...and precedent_ci_verified does not expect it either',
                      'Leak gate' not in ' '.join(pciv.expected_workflows(repo, 'x', 'main'))
                      and pciv.expected_workflows(repo, 'x', 'main')))
        due, why = pb.main_test_due(repo, sha, gh=GH(incident))
        cases.append(('(d) the due check no longer sends a private repo to Update '
                      'Vendors over leak-gate.yml', 'Update Vendors' not in why
                      and 'leak-gate' not in why))
        sha = commit('public', real)
        cases.append(('(b) in a public repository leak-gate.yml is one of main\'s '
                      'GitHub tests', LEAK in [p for p, _ in pb.github_tests(repo, sha)]))
        cases.append(('...and precedent_ci_verified still expects it there',
                      'Leak gate' in pciv.expected_workflows(repo, 'x', 'main')))
        sha = commit(None, real)
        cases.append(('...and in a repository that declares no visibility',
                      LEAK in [p for p, _ in pb.github_tests(repo, sha)]))
        sha = commit('private', dict(real, **{OTHER: other}))
        cases.append(('(c) private repo, a workflow NOT gated on privacy stays one '
                      'of main\'s GitHub tests', OTHER in [p for p, _ in pb.github_tests(repo, sha)]))
        sha = commit('private', {LIGHT: real[LIGHT],
                                 '.github/workflows/half.yml': half})
        cases.append(('...nor one with a job the privacy gate does not reach',
                      '.github/workflows/half.yml' in [p for p, _ in pb.github_tests(repo, sha)]))
        sha = commit('private', {LIGHT: real[LIGHT],
                                 '.github/workflows/neg.yml': negated})
        cases.append(('the negated form, as one && part of a folded if:, is the '
                      'same gate', [p for p, _ in pb.github_tests(repo, sha)] == [LIGHT]))
        cases.append(('the light check\'s own if:, privacy only inside an ||, is '
                      'never read as skipped by design',
                      not pb.skipped_by_design(repo, real[LIGHT])))
        sha = commit('private', {LIGHT: real[LIGHT], OTHER: other})
        due, why = pb.main_test_due(repo, sha, gh=GH([run(LIGHT, 'success')]))
        cases.append(('(d) a workflow no shipped template gives the not-due skip is '
                      'due, and the advice does not name Update Vendors',
                      due is True and 'other.yml' in why and 'Update Vendors' not in why))
        sha = commit('private', {LIGHT: 'on:\n  pull_request:\n    branches: [main]\n'
                                        'jobs:\n  x:\n    runs-on: ubuntu-latest\n'})
        due, why = pb.main_test_due(repo, sha, gh=GH([]))
        cases.append(('...while an old light-check.yml, whose template does carry it, '
                      'is still sent to Update Vendors',
                      due is True and 'Update Vendors' in why))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_main_test_cadence():
    """Main's GitHub test runs at most once every github_ci_every_hours in a
    private repository, decided by Promote before GitHub starts anything
    (spec/CI_CADENCE_PLAN.md, "Promote decides", 2026-10-01).

    The engine half (2026-10-20): the cadence, the due decision, how a run
    reads, and the template and workflow names they rely on. What a
    Promote names its copy and how the wait answers a not-due one are the
    ladder set's, tested there.

    THE NEGATIVE CASES ARE THE POINT: a skip that fires wrongly is main
    going untested. Each "not due" is paired with the shape where it must
    run -- a public repo, an expired window, a failed newest run, GitHub not
    answering, a workflow that cannot skip yet, a batch that changes a
    workflow, PRECEDENT_CI_NOW=1. And a skipped run must never read as a
    failure: GitHub records one, free, on every private push to main."""
    import importlib.util, json as _json, tempfile, time as _time
    name = "main's GitHub test runs at most once every github_ci_every_hours"
    src = ROOT / 'tools' / 'precedent_branches.py'
    if not src.exists():
        not_applicable(name, 'tools/precedent_branches.py is absent')
        return
    spec = importlib.util.spec_from_file_location('_pb_cadence', src)
    pb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pb)
    cases = []
    tpl = (ROOT / 'templates' / 'github-actions' / 'light-check.yml.template')
    tpl_text = tpl.read_text(encoding='utf-8') if tpl.is_file() else ''
    cases.append(('the light-check template names the very branch prefix Promote '
                  'gives a not-due copy',
                  f"startsWith(github.head_ref, '{pb.NOT_DUE_PREFIX}')" in tpl_text))
    saved_env = os.environ.get(pb.FORCE_ENV)
    os.environ.pop(pb.FORCE_ENV, None)
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        repo, me = tmp / 'repo', tmp / 'me'
        repo.mkdir()
        me.mkdir()
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(me)}}), encoding='utf-8')

        def setup(visibility='private', mine=None, theirs=None):
            pj = {'base_branch': 'main'}
            if visibility:
                pj['visibility'] = visibility
            if theirs is not None:
                pj['github_ci_every_hours'] = theirs
            (repo / 'precedent.json').write_text(_json.dumps(pj), encoding='utf-8')
            ident = {'email': 'me@example.com'}
            if mine is not None:
                ident['ci_every_hours'] = mine
            (me / 'identity.json').write_text(_json.dumps(ident), encoding='utf-8')

        setup('public', mine=168)
        cases.append(('a public repository is tested on every Promote, whatever '
                      'the person sets', pb.main_test_cadence(repo, cfg)[0] == 0))
        setup(None, mine=168)
        cases.append(('...and so is one that declares no visibility',
                      pb.main_test_cadence(repo, cfg)[0] == 0))
        setup(mine=168, theirs=0)
        h, where = pb.main_test_cadence(repo, cfg)
        cases.append(("in Promote the person's value wins over the repository's 0 "
                      '(Morgan: "if it conflicts, and I run promote, it still skips it")',
                      h == 168 and str(me) in where))
        setup(theirs=6)
        cases.append(("with no personal value, the repository's own applies",
                      pb.main_test_cadence(repo, cfg)[0] == 6))
        setup(mine='weekly')
        cases.append(('a value that is not a number means every Promote',
                      pb.main_test_cadence(repo, cfg)[0] == 0))
        setup(mine=True)
        cases.append(('...and so does true', pb.main_test_cadence(repo, cfg)[0] == 0))

        WF = '.github/workflows/light-check.yml'
        now = _time.time()

        def iso(hours_ago):
            return _time.strftime('%Y-%m-%dT%H:%M:%SZ', _time.gmtime(now - hours_ago * 3600))

        def run(hours_ago, conclusion='success', branch='to-main-2026-09-30'):
            return {'path': WF, 'status': 'completed', 'conclusion': conclusion,
                    'head_branch': branch, 'created_at': iso(hours_ago),
                    'html_url': 'U'}

        class GH:
            def __init__(self, runs, fail=None):
                self.runs, self.fail = runs, fail

            def call(self, path, cache=True):
                if self.fail:
                    return None, self.fail
                return {'workflow_runs': self.runs}, None

        pb._slug = lambda root: 'o/r'
        skipping = 'on: {}\n# ' + pb.NOT_DUE_PREFIX + '\n'
        shown = {'text': skipping, 'diff': ''}
        real_git = pb._git

        def fake_git(root, *args):
            if args[:1] == ('show',):
                return shown['text']
            if args[:2] == ('diff', '--name-only'):
                return shown['diff']
            return real_git(root, *args)
        pb._git = fake_git
        pb.github_tests = lambda root, sha: [(WF, True)]
        setup(mine=168)

        def due(runs, **kw):
            return pb.main_test_due(repo, 'TIP', gh=GH(runs, kw.get('fail')),
                                    user_config=cfg)
        d, why = due([run(10), run(1, 'skipped', 'main')])
        cases.append(('a pass 10 hours ago with a 168-hour window is NOT DUE, says when '
                      'the next one is, and a newer skipped run changes nothing',
                      d is False and 'next one is due' in why))
        d, why = due([run(200)])
        cases.append(('a pass 200 hours ago is due', d is True and '200h ago' in why))
        d, why = due([run(1, 'failure', 'main'), run(10)])
        cases.append(('a failed newest run keeps it due inside the window, with its link',
                      d is True and 'failure' in why and 'U' in why))
        d, why = due([run(10, branch='claude/some-feature')])
        cases.append(('a pass on a working branch does not count for main',
                      d is True and 'no passing run' in why))
        d, why = due([], fail='HTTP 403')
        cases.append(('GitHub not answering means it runs', d is True and '403' in why))
        shown['text'] = 'on: {}\n'
        d, why = due([run(10)])
        cases.append(('a workflow installed before the not-due skip existed is always '
                      'due, so a "not due" wait never merges under a running test',
                      d is True and 'predates' in why))
        shown['text'] = skipping
        shown['diff'] = '.github/workflows/light-check.yml\ntools/ENGINE_MANIFEST.json\n'
        d, why = due([run(10)])
        cases.append(('a batch changing a workflow or the vendored engine is NOT forced '
                      '(Morgan: "I might update the vendored engines a lot")', d is False))
        shown['diff'] = ''
        os.environ[pb.FORCE_ENV] = '1'
        d, why = due([run(10)])
        os.environ.pop(pb.FORCE_ENV, None)
        cases.append((f'{pb.FORCE_ENV}=1 makes it due', d is True))
        setup(mine=168)
        pj = _json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        (repo / 'precedent.json').write_text(_json.dumps(
            dict(pj, github_ci_workflows='disabled')), encoding='utf-8')
        d, why = due([run(1000)])
        cases.append(("with no personal switch, the repository's own \"disabled\" "
                      'means no test, however long ago it passed',
                      d is False and "this repo's precedent.json" in why))
        (me / 'identity.json').write_text(_json.dumps(
            {'email': 'me@example.com', 'ci_every_hours': 168,
             'ci_workflows': 'enabled'}), encoding='utf-8')
        d, why = due([run(1000)])
        cases.append(("...and the person's \"enabled\" wins over it", d is True))
        setup(mine=0)
        d, why = due([run(10)])
        cases.append(('a value of 0 is every Promote', d is True))

        ok_run = {'path': WF, 'status': 'completed', 'conclusion': 'success',
                  'created_at': '2026-09-30T10:00:00Z', 'head_sha': 'SHA'}
        skipped = dict(ok_run, conclusion='skipped', created_at='2026-09-30T11:00:00Z')

        class RunsGH:
            def call(self, path, cache=True):
                if '/pulls' in path:
                    return [], None
                return {'workflow_runs': [ok_run, skipped]}, None
        st, _why = pb.github_test_state(repo, 'SHA', [(WF, True)], RunsGH())
        cases.append(('a skipped run newer than a pass reads "passed", never "failed" '
                      '(every private push to main records one)', st == 'passed'))

        # 2026-10-19: the push run on main skipped its test while the pull
        # request's run was still going, finished `success`, and was read as
        # main's verdict; the pull request's run failed (issue #1242).
        pr_fail = {'id': 1, 'path': WF, 'status': 'completed', 'conclusion': 'failure',
                   'created_at': '2026-10-19T14:24:40Z', 'head_sha': 'HEAD',
                   'html_url': 'U'}
        push_ok = {'id': 2, 'path': WF, 'status': 'completed', 'conclusion': 'success',
                   'created_at': '2026-10-19T14:25:34Z', 'head_sha': 'SHA'}

        def runs_gh(on_sha, jobs_of):
            class G:
                def call(self, path, cache=True):
                    if path.endswith('/pulls'):
                        return [{'head': {'sha': 'HEAD'}, 'base': {'ref': 'main'},
                                 'number': 1240}], None
                    if '/jobs' in path:
                        return {'jobs': jobs_of}, None
                    if 'head_sha=HEAD' in path:
                        return {'workflow_runs': [pr_fail]}, None
                    return {'workflow_runs': on_sha}, None
            return G()
        hollow_jobs = [{'name': pb.DECISION_JOB, 'conclusion': 'success'},
                       {'name': 'test', 'conclusion': 'skipped'}]
        st, why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                       runs_gh([push_ok], hollow_jobs))
        cases.append(('a push run that tested nothing, newer than its pull '
                      'request\'s failed run, reads "failed" (2026-10-19)',
                      st == 'failed' and 'U' in why))
        st, _why = pb.github_test_state(
            repo, 'SHA', [(WF, True)],
            runs_gh([push_ok], [dict(j, conclusion='success') for j in hollow_jobs]))
        cases.append(('CONTROL: a push run that did run its test, and passed, '
                      'still decides', st == 'passed'))
        pr_fail_saved, pr_fail = pr_fail, dict(pr_fail, path='other.yml')
        st, _why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                        runs_gh([push_ok], hollow_jobs))
        pr_fail = pr_fail_saved
        cases.append(('a run that tested nothing and is the only run is kept: '
                      'it reads "passed", never "never ran"', st == 'passed'))
        # 2026-10-28, measured: the push run on main finished green in 21s
        # having tested nothing, while the pull request's run went on for
        # eleven minutes. "running" was right; the detail now says where.
        pr_busy = dict(pr_fail, status='in_progress', conclusion=None)
        pr_fail_saved, pr_fail = pr_fail, pr_busy
        st, why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                       runs_gh([push_ok], hollow_jobs))
        pr_fail = pr_fail_saved
        cases.append(('a finished push run that tested nothing, with its pull '
                      'request\'s run still going: "running", naming the pull '
                      'request and that the commit\'s own run deferred (2026-10-28)',
                      st == 'running' and 'on pull request #1240' in why
                      and 'tested nothing' in why))
        # 2026-10-27: the pull request's run failed while the push run on
        # main was still going, so main read "running" and the red-main fix
        # was refused straight into main; the newest FINISHED run decides
        # when asked so, which main_test_failed does.
        push_busy = dict(push_ok, status='in_progress', conclusion=None)
        st, _why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                        runs_gh([push_busy], hollow_jobs))
        cases.append(('a push run still going, newer than its pull request\'s '
                      'failed run, reads "running"', st == 'running'))
        st, why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                       runs_gh([push_busy], hollow_jobs),
                                       completed_only=True)
        cases.append(('...and, finished runs only, "failed": the verdict main has '
                      '(2026-10-27)', st == 'failed' and 'U' in why))
        st, _why = pb.github_test_state(repo, 'SHA', [(WF, True)],
                                        runs_gh([push_busy, dict(push_ok, id=3,
                                                 created_at='2026-10-19T14:20:00Z')],
                                                hollow_jobs), completed_only=True)
        cases.append(('CONTROL: finished runs only, an older pass on main itself '
                      'does not hide the pull request\'s newer failure',
                      st == 'failed'))
        wf_text = (ROOT / '.github' / 'workflows' / 'deep-check.yml').read_text(
            encoding='utf-8')
        cases.append(("precedent_branches.DECISION_JOB is deep-check.yml's "
                      'already-tested job name',
                      f'name: {pb.DECISION_JOB}\n' in wf_text))
    if saved_env is not None:
        os.environ[pb.FORCE_ENV] = saved_env
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_main_test_without_individual_source():
    """Main's GitHub test with NO individual source at all -- someone who has
    never set up a precedent-individual, or whose config names one that is
    not there. Morgan, 2026-10-01: "does this version still work if the
    user has no precedent-individual file? Did you test for that?"

    Nothing personal is declared, so the defaults apply: GitHub tests count
    as on and the hours are 0, which in a private repository means every
    Promote is tested (what it did before any of this), and the
    repository's own github_ci_main_test still has the final say. Also a
    broken identity.json, and one with no email (never read as a person's),
    and the commit hook's cadence script writing a personal 0."""
    import importlib.util, json as _json, tempfile
    name = 'with no individual source, main\'s GitHub test falls back to the defaults'
    tpl = ROOT / 'templates' / 'github-actions' / 'light-check.yml.template'
    src = ROOT / 'tools' / 'precedent_branches.py'
    hook = ROOT / 'tools' / 'commit-identity.sh'
    try:
        import yaml as _yaml
    except ImportError:
        not_applicable(name, 'PyYAML is not installed, and the template is read with it')
        return
    if not (tpl.is_file() and src.exists() and hook.is_file()):
        not_applicable(name, 'the template, precedent_branches.py or commit-identity.sh is absent')
        return
    spec = importlib.util.spec_from_file_location('_pb_no_individual', src)
    pb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pb)
    doc = _yaml.safe_load(tpl.read_text(encoding='utf-8'))
    on = doc.get('on', doc.get(True)) or {}
    expr = doc['jobs']['light-check']['if']
    raw = tpl.read_text(encoding='utf-8')
    rendered = raw.replace("'main-test:individual'", "'main-test:always'")

    def runs(text, event, private, head_ref=''):
        e = _yaml.safe_load(text)['jobs']['light-check']['if']
        return event in on and _gh_if(e, event, private, head_ref)

    WF = '.github/workflows/light-check.yml'

    class GH:
        def call(self, path, cache=True):
            return {'workflow_runs': [{
                'path': WF, 'status': 'completed', 'conclusion': 'success',
                'head_branch': 'to-main-2026-09-30', 'created_at': '2099-01-01T00:00:00Z'}]}, None
    pb._slug = lambda root: 'o/r'
    pb.github_tests = lambda root, sha: [(WF, True)]
    installed = {'text': raw}
    real_git = pb._git
    pb._git = lambda root, *a: installed['text'] if a[:1] == ('show',) else real_git(root, *a)
    saved_force = os.environ.pop(pb.FORCE_ENV, None)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        repo = tmp / 'repo'
        repo.mkdir()
        broken, noemail = tmp / 'broken', tmp / 'noemail'
        broken.mkdir()
        noemail.mkdir()
        (broken / 'identity.json').write_text('{ this is not json', encoding='utf-8')
        (noemail / 'identity.json').write_text(_json.dumps(
            {'ci_workflows': 'disabled', 'ci_every_hours': 168}), encoding='utf-8')
        configs = {'no config file at all': tmp / 'nonexistent.json'}
        for label, target in (('a config naming a set that is not there', tmp / 'gone'),
                              ('an identity.json that is not valid JSON', broken),
                              ('an identity.json with no email', noemail)):
            c = tmp / f'cfg-{target.name}.json'
            c.write_text(_json.dumps({'individual': {'path': str(target)}}), encoding='utf-8')
            configs[label] = c
        # The passing run is in the future, so every hours value is "not due":
        # anything that still runs is running because the hours are 0.
        for label, cfg in configs.items():
            on_, _ = pb.main_test_switch(repo, cfg)
            hours, _ = pb.main_test_cadence(repo, cfg)
            for mode, exp_pr, exp_push in (
                    (None, True, False), ('individual', True, False), ('never', False, False),
                    (48, False, False), (0, True, False), ('always', False, True)):
                pj = {'base_branch': 'main', 'visibility': 'private'}
                if mode is not None:
                    pj['github_ci_main_test'] = mode
                (repo / 'precedent.json').write_text(_json.dumps(pj), encoding='utf-8')
                installed['text'] = rendered if mode == 'always' else raw
                due, why = pb.main_test_due(repo, 'TIP', gh=GH(), user_config=cfg)
                copy = ('to-main-' if due else pb.NOT_DUE_PREFIX) + '2026-10-01'
                pr = runs(installed['text'], 'pull_request', True, copy)
                push = runs(installed['text'], 'push', True)
                cases.append((f'{label}, github_ci_main_test {mode!r}: pull request '
                              f'{"runs" if exp_pr else "skipped"}, push to main '
                              f'{"runs" if exp_push else "skipped"}',
                              pr == exp_pr and push == exp_push and on_ is True and hours == 0))
            (repo / 'precedent.json').write_text(_json.dumps(
                {'base_branch': 'main', 'visibility': 'public'}), encoding='utf-8')
            installed['text'] = raw
            due, _ = pb.main_test_due(repo, 'TIP', gh=GH(), user_config=cfg)
            cases.append((f'{label}, a public repo: still tested',
                          due and runs(raw, 'push', False)))
        # The commit hook's cadence script, written with no individual source.
        home = tmp / 'home'
        work = tmp / 'work'
        home.mkdir()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(work)], capture_output=True)
        (work / 'precedent.json').write_text(_json.dumps(
            {'base_branch': 'main', 'visibility': 'private'}), encoding='utf-8')
        env = dict(os.environ, HOME=str(home), TZ='UTC',
                   PRECEDENT_GLOBAL_HOOKS=str(home / 'git-hooks'),
                   PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'nonexistent.json'),
                   CLAUDE_PROJECT_DIR=str(work))
        for k in ('PRECEDENT_COMMIT_TZ', 'PRECEDENT_COMMIT_EMAIL', 'PRECEDENT_COMMIT_NAME'):
            env.pop(k, None)
        r = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                           timeout=120, env=env)
        scripts = list(tmp.rglob('precedent-ci-cadence'))
        body = scripts[0].read_text(encoding='utf-8') if scripts else ''
        cases.append(('with no individual source the session-start hook still runs, and '
                      'its cadence script carries a personal 0 hours and branches on',
                      r.returncode == 0 and 'PERSONAL_CI_EVERY_HOURS = 0' in body
                      and 'PERSONAL_CI_ON_BRANCHES = True' in body))
    pb._git = real_git
    if saved_force is not None:
        os.environ[pb.FORCE_ENV] = saved_force
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_merge_gate_sees_a_workflow_that_never_ran():
    """The merge gate's CI check: a green pull request is not the question.

    THE INCIDENT, 2026-09-23. A pull request showed a green tick. One of two
    workflows had run on its head commit; the other -- verify_harness,
    precedent_check, doc_sync -- never fired, although the identical trigger
    had produced a run for the four previous pull requests on the same
    branch. GitHub re-attaches a branch's historical runs to whatever pull
    request is open on it, so four runs earned by EARLIER pull requests read
    as this one's history. The merge was one call from landing on an
    unchecked tree.

    Pinned here: every verdict, that UNVERIFIED never reads as clean, and
    the parser case that the tool's own first run got wrong -- a workflow
    whose `on:` block only MENTIONS pull_request in a comment is not
    pull-request-triggered.

    The network is stubbed throughout. A test that actually called GitHub
    would spend the shared unauthenticated allowance this tool is careful
    about, and would fail on a runner with no egress
    (practice: fixture-owns-its-state)."""
    import tempfile
    import precedent_ci_verified as pciv

    cases = []
    saved_git, saved_fetch = pciv._git, pciv._fetch_runs
    saved_jobs = pciv._fetch_jobs

    def stub_git(root, *a):
        if a[:1] == ('rev-parse',) and 'HEAD' in a and '--abbrev-ref' in a:
            return True, 'claude/some-branch'
        if a[:1] == ('rev-parse',):
            return True, 'abc123def4567890'
        if a[:1] == ('config',):
            return True, 'https://github.com/alex137/BestPractice.git'
        if a[:1] == ('branch',):
            return True, '  origin/claude/some-branch'
        return True, ''

    def run(runs, expected=('Deep check', 'Leak gate')):
        pciv._fetch_runs = lambda slug, sha: (runs, '')
        pciv.expected_workflows = lambda root, branch='', base='': set(expected)
        return pciv.verdict('.')

    saved_expected = pciv.expected_workflows
    try:
        pciv._git = stub_git
        ok = [{'name': 'Deep check', 'status': 'completed',
               'conclusion': 'success', 'run_number': 2},
              {'name': 'Leak gate', 'status': 'completed',
               'conclusion': 'success', 'run_number': 2}]
        state, _ = run(ok)
        cases.append(('both workflows green for this commit is VERIFIED',
                      state == pciv.VERIFIED, state))
        cases.append(('and the gate says nothing at all',
                      pciv.remind('.') == '', repr(pciv.remind('.'))))

        # THE INCIDENT: one workflow ran, the other produced no run.
        state, lines = run([r for r in ok if r['name'] == 'Leak gate'])
        cases.append(('a workflow with NO run for this commit is NOT_RUN, '
                      'never verified', state == pciv.NOT_RUN, state))
        cases.append(('and it names the workflow that is missing',
                      any('Deep check' in x and 'NO RUN' in x for x in lines),
                      '; '.join(lines)[:110]))
        said = pciv.remind('.')
        cases.append(('the gate says DID NOT RUN, not "failed"',
                      'DID NOT RUN' in said, said[:80]))

        pciv._fetch_jobs = lambda url: ([{'conclusion': 'failure',
                                          'runner_name': 'GitHub Actions 7',
                                          'runner_id': 7}], '')
        state, _ = run([dict(ok[0], conclusion='failure', jobs_url='j'), ok[1]])
        cases.append(('a failed run is FAILED, told apart from not running',
                      state == pciv.FAILED, state))

        # THE 2026-10-05 STALL: the run says `failure`, but its only job was
        # cancelled without ever getting a machine. Not a finding.
        idle_job = {'conclusion': 'cancelled', 'runner_name': '', 'runner_id': 0}
        pciv._fetch_jobs = lambda url: ([idle_job,
                                         {'conclusion': 'success',
                                          'runner_name': 'GitHub Actions 3',
                                          'runner_id': 3}], '')
        state, lines = run([dict(ok[0], conclusion='failure', jobs_url='j'), ok[1]])
        said = pciv.remind('.')
        cases.append(('a run whose failing jobs never got a machine is '
                      'NEVER_STARTED, and the gate does not say FAILED',
                      state == pciv.NEVER_STARTED and 'FAILED' not in said
                      and 'NEVER STARTED' in said, said[:90]))
        cases.append(('a job that DID get a machine and was cancelled is still '
                      'a failure, never excused as never started',
                      not pciv.never_started([dict(idle_job, runner_name='GitHub '
                                                   'Actions 9', runner_id=9)])
                      and not pciv.never_started([])
                      and pciv.never_started([idle_job]), ''))
        pciv._fetch_jobs = lambda url: (None, 'GitHub answered 403')
        state, _ = run([dict(ok[0], conclusion='failure', jobs_url='j'), ok[1]])
        cases.append(('when the jobs cannot be read, a red run stays FAILED',
                      state == pciv.FAILED, state))
        asked = []
        pciv._fetch_jobs = lambda url: (asked.append(url), ([], ''))[1]
        run(ok)
        cases.append(('a green commit costs no jobs request at all',
                      asked == [], repr(asked)))
        state, _ = run([dict(ok[0], status='in_progress', conclusion=None),
                        ok[1]])
        cases.append(('an unfinished run is RUNNING, not success',
                      state == pciv.RUNNING, state))

        # Cannot ask -> never clean. This is the same distinction the source
        # freshness row was rewritten for the same day.
        pciv._fetch_runs = lambda slug, sha: (None, 'GitHub answered 403')
        state, _ = pciv.verdict('.')
        cases.append(('a request that could not be made is UNVERIFIED, never '
                      'VERIFIED', state == pciv.UNVERIFIED, state))

        # An unpushed commit is answered without spending a request at all.
        spent = []
        pciv._fetch_runs = lambda slug, sha: (spent.append(1), ([], ''))[1]
        pciv._git = lambda root, *a: (
            (True, '') if a[:1] == ('branch',) else stub_git(root, *a))
        state, _ = pciv.verdict('.')
        cases.append(('an unpushed commit is NOT_RUN and costs no API call',
                      state == pciv.NOT_RUN and not spent, f'{state} {spent}'))
    finally:
        pciv._git, pciv._fetch_runs = saved_git, saved_fetch
        pciv._fetch_jobs = saved_jobs
        pciv.expected_workflows = saved_expected

    # THE PARSER CASE the tool got wrong on its first run: `pull_request:`
    # inside a COMMENT is not a trigger. Real files, since this is a text
    # reader and a stub would prove nothing about it.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='ci-verified-'))
    try:
        wf = tmp / '.github' / 'workflows'
        wf.mkdir(parents=True)
        (wf / 'commented.yml').write_text(
            'name: Commented\non:\n'
            '  # the unexamined `pull_request:` line came with it\n'
            '  push:\n    branches: [main]\n\njobs: {}\n')
        (wf / 'real.yml').write_text(
            'name: Real\non:\n  pull_request:\n'
            '    types: [opened]\n\njobs: {}\n')
        (wf / 'everybranch.yml').write_text(
            'name: Everywhere\non:\n  push:\n\njobs: {}\n')
        got = pciv.expected_workflows(str(tmp), 'some-feature-branch')
        cases.append(('a pull_request mentioned only in a COMMENT is not a '
                      'trigger', 'Commented' not in got, str(sorted(got))))
        cases.append(('a real pull_request trigger is expected',
                      'Real' in got, str(sorted(got))))
        cases.append(('push with no branch filter is expected on any branch',
                      'Everywhere' in got, str(sorted(got))))
        on_main = pciv.expected_workflows(str(tmp), 'main')
        cases.append(('push scoped to main IS expected on main',
                      'Commented' in on_main, str(sorted(on_main))))
        # A pull_request trigger scoped to main is not expected on a pull
        # request into staging (2026-09-30: the merge gate said "CI DID
        # NOT RUN" for deep-check.yml on every one), and is into main.
        (wf / 'mainonly.yml').write_text(
            'name: MainOnly\non:\n  pull_request:\n    branches: [main]\n'
            '    types: [opened]\n\n  push:\n    branches: [main]\n\njobs: {}\n')
        into_pre = pciv.expected_workflows(str(tmp), 'claude/feature', 'staging')
        cases.append(('a main-only pull_request is not expected into staging',
                      'MainOnly' not in into_pre and 'Real' in into_pre,
                      str(sorted(into_pre))))
        into_main = pciv.expected_workflows(str(tmp), 'to-main-x', 'main')
        cases.append(('and is expected into main',
                      'MainOnly' in into_main, str(sorted(into_main))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok_, d in cases if not ok_]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_freshness_guard_never_tells_a_tier_branch_to_merge():
    """On a tier branch the stale-base remedy is a new working branch.

    Reported 2026-10-08 from a consuming repository: a session on main was
    told "Bring it up to date deliberately: git merge origin/staging",
    which makes the local main diverge from origin/main. On main or
    staging the guard now says to start a working branch from
    origin/<base> with `git switch --no-track -c`, named by
    precedent_branch_name.py where the checkout has it -- `--no-track`
    because `git checkout -b X origin/staging` makes X track the tier,
    and a bare `git push` would then land there.

    CONTROL: a working branch on the same stale base still gets the merge.
    Both modes that print the remedy are run (session-start's WARN and
    pre-write's block), through both hook copies."""
    import tempfile
    name = 'the freshness guard never tells a tier branch to merge its base'
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    missing = [str(g.relative_to(ROOT)) for g in guards if not g.exists()]
    if missing:
        not_applicable(name, f'not in this tree: {missing}')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ)
        env.pop('CLAUDE_PROJECT_DIR', None)
        env['TMPDIR'] = str(tmp / 'sentinels')
        (tmp / 'sentinels').mkdir()
        env['PRECEDENT_ALLOW_ANY_AUTHOR'] = '1'
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = 'Harness'
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = 'harness@example.com'

        def _git(d, *a):
            r = subprocess.run(['git', '-C', str(d), *a],
                               capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise RuntimeError('tier-remedy fixture setup failed: git %s: %s'
                                   % (' '.join(a), (r.stderr or r.stdout).strip()))
            return r

        origin = tmp / 'origin'
        _git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        seed = tmp / 'seed'
        _git(tmp, 'init', '-q', '-b', 'main', str(seed))
        (seed / 'tools').mkdir()
        (seed / 'tools' / 'precedent_branch_name.py').write_text(
            'print("2026-10-08-x-abcde")\n', encoding='utf-8')
        _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'one')
        _git(seed, 'remote', 'add', 'origin', str(origin))
        _git(seed, 'push', '-q', 'origin', 'main', 'main:staging', 'main:feature')
        _git(seed, 'commit', '-q', '--allow-empty', '-m', 'on staging only')
        _git(seed, 'push', '-q', 'origin', 'main:staging')

        def _run(guard, cwd, mode, session):
            payload = json.dumps({'session_id': session, 'tool_name': 'Write',
                                  'tool_input': {'file_path': 'x'}})
            return subprocess.run(['bash', str(guard), mode, 'staging'],
                                  cwd=str(cwd), input=payload,
                                  capture_output=True, text=True, env=env)

        for guard in guards:
            tag = ('installed' if guard.parent.parent.parent == ROOT
                   else 'template')
            for branch, tier in (('main', True), ('feature', False)):
                d = tmp / f'{tag}-{branch}'
                _git(tmp, 'clone', '-q', str(origin), str(d))
                if branch != 'main':
                    _git(d, 'checkout', '-q', branch)
                for mode in ('session-start', 'pre-write'):
                    err = _run(guard, d, mode, f'{tag}-{branch}-{mode}').stderr
                    said = 'missing 1 commit(s) from origin/staging' in err
                    if tier:
                        ok = (said and 'is a tier branch' in err
                              and 'git switch --no-track -c' in err
                              and 'tools/precedent_branch_name.py' in err
                              and 'origin/staging' in err
                              and 'Bring it up to date' not in err)
                        what = (f'{tag} {mode}: on main, the remedy is a new '
                                f'untracked branch named by the naming tool, not '
                                f'a merge')
                    else:
                        ok = (said and 'git merge origin/staging' in err
                              and 'is a tier branch' not in err)
                        what = (f'{tag} {mode}: CONTROL: a working branch is '
                                f'still told to merge its base')
                    cases.append((what, ok, failure_detail(err, 500)))
            # Main itself was not touched by either run.
            cases.append((f'{tag}: the guard moved nothing on main',
                          _git(tmp / f'{tag}-main', 'rev-parse', 'HEAD').stdout
                          == _git(tmp / f'{tag}-main', 'rev-parse', 'origin/main').stdout,
                          ''))

    bad = [(n, e) for n, ok, e in cases if not ok]
    check(f'{name} ({len(cases)} stated cases, both copies)',
          not bad, '; '.join(f'{n} -- {e}' for n, e in bad))


def check_freshness_guard_leaves_a_source_on_its_tier_when_opened_above():
    """In a session opened above its repositories, a clone on its tier is a
    source, and every block names its checkout with a `git -C` remedy.

    Reported 2026-11-01 from an Update Vendors run opened in /home/user over
    BestPractice and three practice sets, all on main. The switchboard
    (precedent_run_repo_hooks.py) ran BestPractice's guard with BestPractice
    as the project, so main was refused for lacking staging's commits, and
    its remedy moved the clone onto a branch from origin/staging -- after
    which the session check said the universal clone was "1 behind
    origin/main". The block named only 'main', so it never said which of the
    four clones it meant; its relative `$(python3 tools/...)` did not
    resolve from the parent folder; and `cd <repo> && git switch ...` was
    refused, since only a literal "git *" counted as git.

    Cases, with PRECEDENT_SESSION_ROOT naming the folder above:
      - main, current with origin/main, staging ahead: not blocked, not
        moved, and the note names the clone and a literal `git -C` remedy;
      - a working branch on a stale base: blocked, the block names the
        clone and says `git -C <clone> merge origin/staging`;
      - `cd <clone> && git ...` is let through a block; `cd <clone> && rm`
        is not.
    CONTROL: the same main with no PRECEDENT_SESSION_ROOT (a session rooted
    in the clone) is still refused with the tier remedy."""
    import tempfile
    name = 'the freshness guard leaves a source on its tier when opened above'
    guard = ROOT / '.claude' / 'hooks' / 'freshness-guard.sh'
    if not guard.exists():
        not_applicable(name, 'no .claude/hooks/freshness-guard.sh in this tree')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ)
        env.pop('CLAUDE_PROJECT_DIR', None)
        env.pop('PRECEDENT_SESSION_ROOT', None)
        env['TMPDIR'] = str(tmp / 'sentinels')
        (tmp / 'sentinels').mkdir()
        env['PRECEDENT_ALLOW_ANY_AUTHOR'] = '1'
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = 'Harness'
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = 'harness@example.com'

        def _git(d, *a):
            r = subprocess.run(['git', '-C', str(d), *a],
                               capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise RuntimeError('opened-above fixture setup failed: git %s: %s'
                                   % (' '.join(a), (r.stderr or r.stdout).strip()))
            return r

        origin = tmp / 'origin'
        _git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        seed = tmp / 'seed'
        _git(tmp, 'init', '-q', '-b', 'main', str(seed))
        (seed / 'tools').mkdir()
        (seed / 'tools' / 'precedent_branch_name.py').write_text(
            'print("2026-11-01-x-work-from-staging-abcde")\n', encoding='utf-8')
        _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'one')
        _git(seed, 'remote', 'add', 'origin', str(origin))
        _git(seed, 'push', '-q', 'origin', 'main', 'main:staging', 'main:feature')
        _git(seed, 'commit', '-q', '--allow-empty', '-m', 'on staging only')
        _git(seed, 'push', '-q', 'origin', 'main:staging')
        above = tmp / 'home'
        above.mkdir()

        def _run(cwd, session, opened_above, tool='Write', command=None):
            e = dict(env)
            if opened_above:
                e['PRECEDENT_SESSION_ROOT'] = str(above)
            ti = {'command': command} if command else {'file_path': 'x'}
            payload = json.dumps({'session_id': session, 'tool_name': tool,
                                  'tool_input': ti})
            return subprocess.run(['bash', str(guard), 'pre-write', 'staging'],
                                  cwd=str(cwd), input=payload,
                                  capture_output=True, text=True, env=e)

        src = above / 'source'
        _git(tmp, 'clone', '-q', str(origin), str(src))
        before = _git(src, 'rev-parse', 'HEAD').stdout
        r = _run(src, 'src-above', True)
        cases.append(('opened above: main, current with origin/main, is not blocked',
                      r.returncode == 0, failure_detail(r.stderr, 500)))
        cases.append(('...and its note names the clone and a literal git -C remedy',
                      str(src) in r.stderr and 'not moved or blocked' in r.stderr
                      and f'git -C {src} switch --no-track -c '
                          '2026-11-01-x-work-from-staging-abcde origin/staging' in r.stderr
                      and '$(' not in r.stderr, failure_detail(r.stderr, 500)))
        cases.append(('...and the clone did not move',
                      _git(src, 'branch', '--show-current').stdout.strip() == 'main'
                      and _git(src, 'rev-parse', 'HEAD').stdout == before, ''))

        rooted = tmp / 'rooted'
        _git(tmp, 'clone', '-q', str(origin), str(rooted))
        r = _run(rooted, 'rooted', False)
        cases.append(('CONTROL: rooted in the clone, main is still refused with '
                      'the tier remedy', r.returncode == 2
                      and 'is a tier branch' in r.stderr, failure_detail(r.stderr, 500)))

        work = above / 'work'
        _git(tmp, 'clone', '-q', str(origin), str(work))
        _git(work, 'checkout', '-q', 'feature')
        r = _run(work, 'work-above', True)
        cases.append(('opened above: a stale working branch is blocked, naming '
                      'its clone and a git -C merge', r.returncode == 2
                      and f'in {work} (this session was opened in {above}' in r.stderr
                      and f'git -C {work} merge origin/staging' in r.stderr,
                      failure_detail(r.stderr, 500)))
        r = _run(work, 'work-cd-git', True, tool='Bash',
                 command=f'cd {work} && git merge origin/staging --no-edit')
        cases.append(('`cd <clone> && git ...` is let through', r.returncode == 0,
                      failure_detail(r.stderr, 500)))
        r = _run(work, 'work-cd-rm', True, tool='Bash',
                 command=f'cd {work} && rm -f x')
        cases.append(('`cd <clone> && rm ...` is not', r.returncode == 2,
                      failure_detail(r.stderr, 500)))

    bad = [(n, e) for n, ok, e in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {e}' for n, e in bad))


def check_tier_branches_are_never_a_pull_requests_source():
    """No tier branch is ever the SOURCE of a merged pull request, and a
    missing staging is rebuilt.

    2026-09-26: the pull request of staging into main (#629) was opened
    FROM staging, and staging was deleted right after it merged. The
    repository's "automatically delete head branches" setting was measured
    OFF afterwards, so the cause is not established; the "Delete branch"
    button a merged pull request's page offers for its source is the
    likeliest. Whatever it was, a tier branch that is never a pull
    request's source cannot be deleted that way: the merge gate
    refuses a pull request whose head is a tier branch of the same
    repository (a fork's branch of that name is someone else's), and
    `--ensure-tiers --apply` rebuilds a missing staging from the old name
    kept in step with it, else from main -- where it had looked for staging
    itself and given up."""
    import tempfile, json as _json
    name = 'a tier branch is never a pull request source, and a missing staging is rebuilt'
    tool = ROOT / 'tools' / 'precedent_branches.py'
    if not tool.exists() or not (ROOT / 'tools' / 'precedent_merge_check.py').exists():
        not_applicable(name, 'precedent_branches.py or precedent_merge_check.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_merge_check as pmc
    finally:
        sys.path.pop(0)
    tiers = ['main', 'staging', 'precedent-beta-v01']
    cases = [
        ('a pull request FROM staging, same repository, is refused',
         bool(pmc.tier_source_refusal('staging', 'o/r', 'o', 'r', tiers))),
        ('...and the refusal says how: a throwaway copy',
         'promote-to-main' in (pmc.tier_source_refusal('staging', 'o/r', 'o', 'r', tiers) or '')
         or 'refs/heads/to-main-' in (pmc.tier_source_refusal('staging', 'o/r', 'o', 'r', tiers) or '')),
        ('so is one from main',
         bool(pmc.tier_source_refusal('main', 'o/r', 'o', 'r', tiers))),
        ("a fork's branch named staging is not refused",
         pmc.tier_source_refusal('staging', 'someone/r', 'o', 'r', tiers) is None),
        ('an ordinary working branch is not refused',
         pmc.tier_source_refusal('claude/x', 'o/r', 'o', 'r', tiers) is None),
        ('an unreadable head (no network) is not refused -- fail open',
         pmc.tier_source_refusal(None, None, 'o', 'r', tiers) is None),
    ]
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-config.json'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a],
                                  capture_output=True, text=True, env=env)

        bare = tmp / 'origin.git'
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        git(tmp, 'init', '-q', '-b', 'main', str(work))
        for f in ('precedent_branches.py', 'precedent_push_check.py', 'precedent_time.py'):
            if (ROOT / 'tools' / f).exists():
                (work / 'tools' / f).write_bytes((ROOT / 'tools' / f).read_bytes())
        (work / 'precedent.json').write_text(_json.dumps({'base_branch': 'staging'}),
                                             encoding='utf-8')
        (work / 'f').write_text('1', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'one')
        git(work, 'remote', 'add', 'origin', f'file://{bare}')
        git(work, 'push', '-q', 'origin', 'main', 'main:staging')
        (work / 'f').write_text('2', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'two')
        git(work, 'push', '-q', 'origin', 'HEAD:staging', 'HEAD:precedent-beta-v01')
        want = git(work, 'rev-parse', 'HEAD').stdout.strip()

        def tip(b):
            return git(work, 'ls-remote', 'origin', f'refs/heads/{b}').stdout.split('\t')[0]

        def ensure():
            return subprocess.run([sys.executable, 'tools/precedent_branches.py',
                                   '--ensure-tiers', '--apply'], cwd=work,
                                  capture_output=True, text=True, env=env)

        git(work, 'push', '-q', 'origin', ':staging')
        r = ensure()
        # Retired 2026-10-11 (todo-2026-09-26-retire-precedent-beta-v01): the
        # old name is never a source any more, even when it is ahead.
        cases.append(('a deleted staging is rebuilt from main, never from '
                      'the retired old name',
                      tip('staging') == tip('main') != want,
                      failure_detail(r.stdout + r.stderr, 300)))
        git(work, 'push', '-q', 'origin', ':staging', ':precedent-beta-v01')
        r = ensure()
        cases.append(('with no old name either, it is rebuilt from main',
                      tip('staging') == tip('main') != '', failure_detail(r.stdout + r.stderr, 300)))
        # Any other branch is never a source either, even ahead of main.
        (work / 'f').write_text('3', encoding='utf-8')
        git(work, 'commit', '-q', '-am', 'three')
        git(work, 'push', '-q', 'origin', 'HEAD:some-feature')
        git(work, 'push', '-q', 'origin', ':staging')
        r = ensure()
        cases.append(('with an ordinary branch ahead of main, staging is '
                      'still rebuilt from main',
                      tip('staging') == tip('main') != tip('some-feature'),
                      failure_detail(r.stdout + r.stderr, 300)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{c} [{d}]' if d else c for c, d in bad))


def check_creation_pipeline_fires():
    """Phase 5's own done-when, tested directly rather than trusted from a
    manual smoke test: "a candidate can be raised, promoted and landed end
    to end; a candidate failing any of the four criteria is refused with a
    reason" (PRACTICE_ENGINE_PLAN.md, Sequence). Not registered as a
    `checked_by` in tools/precedent_check.py -- same reasoning
    check_decision_records_not_inline already states for itself: no single
    practices/*.md file backs "the creation pipeline works," so registering
    it there would inflate ENFORCEMENT.md's coverage count with a phantom
    row.

    Fixture is a throwaway individual-shaped repo (practices/ + candidates/)
    against THIS repo's real universal catalogue for the non-duplication and
    checked_by-registration cases, since those need a real, populated
    CHECKS registry and a real existing slug to collide with -- a fixture
    catalogue of one or two invented practices would not exercise either."""
    import shutil, tempfile

    def pyrun(*args, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        r = subprocess.run([sys.executable, *args], capture_output=True,
                           text=True, env=env)
        return r.returncode, r.stdout + r.stderr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-pipeline-'))
    cases = []
    try:
        repo = tmp / 'fixture-individual'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'candidates').mkdir(parents=True)

        cand_tool = str(ROOT / 'tools' / 'precedent_candidate.py')
        promote_tool = str(ROOT / 'tools' / 'precedent_promote.py')
        land_tool = str(ROOT / 'tools' / 'precedent_land.py')

        def make_candidate(slug, **extra):
            args = [cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                    '--slug', slug, '--title', slug, '--signal', 'explicit-instruction',
                    '--raised-by', 'harness', '--observed', 'a fixture incident',
                    '--proposed-rule', extra.pop('rule', f'Always do the {slug} thing.')]
            for k, v in extra.items():
                args += [f'--{k}', str(v)]
            rc, out = pyrun(*args)
            if rc != 0:
                raise RuntimeError(f"fixture candidate creation failed: {out}")
            # The rule this came from (slug match-parsed-id-not-prefix)
            # was retired on 2026-09-11 with the maintainers' set
            # review -- the fix stands, the standing instruction does
            # not. Left uncited on purpose: `glob(f'{slug}-*.md')`
            # also matches every LONGER slug sharing this one's prefix, so
            # this helper could hand back a different candidate entirely.
            # It is the exact bug the prefix case below tests for, in the
            # helper that builds that case's fixtures; the call site there
            # had already been hand-narrowed to 'prefix-2*.md' to work
            # around it, which is the workaround that names the defect.
            # Matched on each file's own parsed slug instead.
            found = []
            for f in sorted((repo / 'candidates').glob('*.md')):
                fm, _sections = sp._read_practice_file(f)
                if (fm.get('slug') or '').strip('" ') == slug:
                    found.append(f)
            if not found:
                raise RuntimeError(
                    f"fixture candidate for slug {slug!r} was created but no "
                    f"candidates/*.md parses back to that slug")
            return found[-1]

        # --- criterion 1: recurrence or real cost ---------------------------
        f1 = make_candidate('pipeline-fixture-c1', recurrence=1)
        rc, out = pyrun(promote_tool, '--file', str(f1), '--level', 'individual')
        cases.append(('criterion 1 (recurrence/cost) refuses a lone, costless candidate',
                      rc == 1 and 'criterion 1' in out and 'recurrence or real cost' in out))
        f1b = make_candidate('pipeline-fixture-c1b', recurrence=1, occasion='a fixture occasion',
                            **{'cost-if-once': 'a stated one-time cost'})
        rc, out = pyrun(promote_tool, '--file', str(f1b), '--level', 'individual')
        cases.append(('criterion 1 passes on a stated one-time cost '
                      '(reachability also satisfied, so only criterion 1 is isolated)',
                      rc == 0 and 'PROMOTED' in out))

        # --- criterion 2: reachability ---------------------------------------
        f2 = make_candidate('pipeline-fixture-c2', recurrence=2)
        rc, out = pyrun(promote_tool, '--file', str(f2), '--level', 'individual')
        cases.append(('criterion 2 (reachability) refuses a wide-open, occasion-less candidate',
                      rc == 1 and 'criterion 2' in out and 'reachability' in out))

        # --- criterion 3: non-duplication (against THIS repo's real catalogue) ---
        real_slug = 'verify-postcondition'
        f3 = make_candidate(real_slug, recurrence=2, occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f3), '--level', 'individual',
                        '--against', str(ROOT))
        cases.append(('criterion 3 (non-duplication) refuses an exact-slug collision '
                      'with a real existing practice',
                      rc == 1 and 'criterion 3' in out and 'non-duplication' in out))

        # --- non-duplication defaults to checking the candidate's OWN repo too --
        # Deep-check regression case: --against used to default to ROOT alone
        # regardless of the candidate's level, so promoting an individual/shared
        # candidate with no explicit --against silently never checked it
        # against that repo's own catalogue.
        (repo / 'practices' / 'pipeline-fixture-owncatalogue.md').write_text(
            '---\nslug: pipeline-fixture-owncatalogue\ntitle: Fixture\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "x"\ngates: []\nindex_clause: "x"\nchecked_by: null\n'
            'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
            'added: 2026-09-02\napproved_by: "harness, 2026-09-02"\n'
            'source_practice_number: null\n---\n## Rule\nAlways do the fixture thing.\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')
        f3b = make_candidate('pipeline-fixture-owncatalogue', recurrence=2,
                              occasion='a fixture occasion',
                              rule='Always do the fixture thing.')
        rc, out = pyrun(promote_tool, '--file', str(f3b), '--level', 'individual')
        cases.append(("non-duplication's default --against catches a collision with "
                      "the candidate's OWN repo, not just this repo (universal)",
                      rc == 1 and 'criterion 3' in out and 'non-duplication' in out))

        # --- criterion 4: budget ----------------------------------------------
        huge_rule = ' '.join(['word'] * 3000)  # ~3900 tokens at 1.3/word, alone over the 2000 cap
        f4 = make_candidate('pipeline-fixture-c4', recurrence=2, tier='resident', rule=huge_rule)
        # The cap binds only where no session-load total is declared
        # (build_views.TOTAL_KEY), and the promote tool reads the registry
        # beside its own engine -- so both are run from an engine copy, first
        # with the total dropped (refuses), then with one planted (measures).
        engine = tmp / 'engine'
        shutil.copytree(ROOT / 'tools', engine / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        engine_reg = engine / 'tools' / 'session_load_budgets.json'
        engine_promote = str(engine / 'tools' / 'precedent_promote.py')
        _drop_session_load_total(engine_reg)
        rc, out = pyrun(engine_promote, '--file', str(f4), '--level', 'individual')
        cases.append(('criterion 4 (budget) refuses a resident request that blows the cap',
                      rc == 1 and 'criterion 4' in out and 'budget' in out))
        reg4 = json.loads(engine_reg.read_text(encoding='utf-8'))
        reg4['session_load_tokens'] = 10000
        engine_reg.write_text(json.dumps(reg4, indent=2) + '\n', encoding='utf-8')
        rc, out = pyrun(engine_promote, '--file', str(f4), '--level', 'individual')
        cases.append(('criterion 4 (budget) measures, never refuses, under a '
                      'declared session-load total',
                      'criterion 4' not in out
                      and 'session-load-budget holds the sum' in out))

        # --- full pass: create, promote, land, and the file really parses -----
        f5 = make_candidate('pipeline-fixture-pass', recurrence=2, occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f5), '--level', 'individual')
        promoted = rc == 0 and 'PROMOTED' in out
        rc, out = pyrun(land_tool, '--file', str(f5), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        landed_file = repo / 'practices' / 'pipeline-fixture-pass.md'
        parses = False
        if landed_file.exists():
            try:
                sp._read_practice_file(landed_file)
                parses = True
            except sp.PracticeFileError:
                parses = False
        cases.append(('a fully-valid candidate promotes, lands, and the landed '
                      'file parses as a real practice',
                      promoted and rc == 0 and landed_file.exists() and parses))

        # --- landing hard-refuses an unregistered checked_by claim -------------
        f6 = make_candidate('pipeline-fixture-checkedby', recurrence=2,
                            **{'checked-by': 'tools/doc_lint.py'})
        rc, out = pyrun(land_tool, '--file', str(f6), '--level', 'universal',
                        '--against', str(ROOT))
        cases.append(("landing refuses a checked_by naming a real file that is not "
                      "registered in precedent_check.py's CHECKS",
                      rc == 1 and 'not a key in' in out
                      and not (ROOT / 'practices' / 'pipeline-fixture-checkedby.md').exists()))

        # --- landing marks the source candidate promoted, not left open ---------
        # Deep-check regression case: `status: promoted` was a declared valid
        # value nothing ever set -- a landed candidate stayed `status: open`
        # forever, so `list --status open` kept surfacing it as if it still
        # needed a decision.
        f5b = make_candidate('pipeline-fixture-marks-promoted', recurrence=2,
                              occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f5b), '--level', 'individual')
        rc, out = pyrun(land_tool, '--file', str(f5b), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        landed_fm, _ = pcand._parse_frontmatter(f5b.read_text(encoding='utf-8'))
        cases.append(('landing rewrites the source candidate to status: promoted',
                      rc == 0 and landed_fm.get('status') == 'promoted'))

        # --- landing hard-refuses an unlisted team approver ---------------------
        f7 = make_candidate('pipeline-fixture-approver', recurrence=2, occasion='x')
        rc, out = pyrun(land_tool, '--file', str(f7), '--level', 'team',
                        '--path', str(ROOT), '--approved-by', 'Someone Not An Approver')
        # ROOT has no approvers.json at all -- refused for that reason, which is
        # itself the right failure mode (never landed without one to check against).
        cases.append(('landing refuses a team candidate when there is no '
                      'approvers.json to check the named approver against',
                      rc == 1 and not (ROOT / 'practices' / 'pipeline-fixture-approver.md').exists()))

        # --- disclose-landing: landing states plainly what happened and where --
        # Added 2026-09-03 after Morgan asked directly whether this was
        # already happening -- it wasn't guaranteed, only implied by the
        # tools' own file paths. The tools now print an unconditional
        # DISCLOSE TO THE HUMAN line naming the level, the location, and
        # whether it's already in force; this is that line's own test, not
        # a proxy for it, so a future edit that quietly drops the line fails
        # here rather than only in a live conversation.
        f9 = make_candidate('pipeline-fixture-disclose-individual', recurrence=2,
                             occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f9), '--level', 'individual')
        rc, out = pyrun(land_tool, '--file', str(f9), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        cases.append(('landing an individual practice discloses it as the '
                      "person's own set, already in force",
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'YOUR OWN individual practice set' in out
                      and str(repo) in out))

        # A dynamic execution test for the universal disclosure line would
        # need to actually land into ROOT/practices/ (precedent_land.py
        # hardcodes universal's dest_dir to this repo's own tree) -- the
        # checked_by-refusal case above deliberately avoids ever doing that
        # for real, and this test follows the same caution rather than risk
        # a stray file in this repo's real, public catalogue on a crash
        # mid-test. A static source check is the honest, zero-risk substitute.
        land_src = (ROOT / 'tools' / 'precedent_land.py').read_text(encoding='utf-8')
        cases.append(('precedent_land.py source still carries the universal '
                      'DISCLOSE line (static check -- see comment above for why '
                      'this is not an execution test)',
                      'DISCLOSE TO THE HUMAN' in land_src
                      and 'DRAFT ONLY' in land_src))

        # --- a same-day, same-slug raise registers as recurrence, never fails --
        # Deep-check regression case: cmd_create used to hard-refuse a second
        # same-day raise of the same slug ("already exists"), silently dropping
        # exactly the recurrence signal Stage 1 exists to capture.
        rc_a, out_a = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                             '--slug', 'pipeline-fixture-sameday', '--title', 't',
                             '--signal', 'explicit-instruction', '--raised-by', 'harness',
                             '--observed', 'first raise', '--proposed-rule', 'r',
                             '--occasion', 'a fixture occasion')
        rc_b, out_b = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                             '--slug', 'pipeline-fixture-sameday', '--title', 't',
                             '--signal', 'explicit-instruction', '--raised-by', 'harness',
                             '--observed', 'second raise, same day', '--proposed-rule', 'r',
                             '--occasion', 'a fixture occasion')
        sameday_files = sorted((repo / 'candidates').glob('pipeline-fixture-sameday-*.md'))
        rc, out = pyrun(promote_tool, '--file', str(sameday_files[0]), '--level', 'individual')
        cases.append(('a second same-day raise of the same slug does not fail, and '
                      'registers as recurrence rather than needing recurrence hand-bumped',
                      rc_a == 0 and rc_b == 0 and len(sameday_files) == 2
                      and rc == 0 and 'PROMOTED' in out))

        # --- recurrence counting matches on the parsed slug, not a filename prefix --
        # Deep-check regression case: counting file_count via glob(f'{slug}-*.md')
        # let a candidate named e.g. 'foo-bar' inflate 'foo''s recurrence count,
        # since 'foo-bar-<date>.md' also matches the glob 'foo-*.md'.
        # The short slug's own file, kept from its own creation. This line
        # used to be a hand-narrowed `glob('pipeline-fixture-prefix-2*.md')`
        # -- a workaround for make_candidate() globbing by prefix and handing
        # back the LONGER candidate created just below. The helper matches on
        # each file's parsed slug now, so no narrowing is needed and the test
        # no longer contains a private instance of the bug it tests for.
        # ORDER MATTERS, and is the negative control. The LONGER slug is
        # created first, so a prefix glob (`glob(f'{slug}-*.md')`, sorted,
        # last) hands back 'pipeline-fixture-prefix-longer-<date>.md' when
        # asked for the short slug -- 'l' sorts after the date's '2'. Created
        # the other way round, the old prefix-matching helper returns the
        # right file by luck and this case proves nothing. Reordered
        # 2026-09-06, after a control run showed exactly that: reverting the
        # helper to the prefix glob still passed.
        make_candidate('pipeline-fixture-prefix-longer', recurrence=1,
                        **{'cost-if-once': 'unrelated candidate, shares a slug prefix'})
        f_prefix = make_candidate('pipeline-fixture-prefix', recurrence=1)
        rc, out = pyrun(promote_tool, '--file', str(f_prefix), '--level', 'individual')
        cases.append(("a differently-slugged candidate sharing a name prefix "
                      "('foo-bar' alongside 'foo') never inflates the shorter "
                      "slug's recurrence count",
                      rc == 1 and 'criterion 1' in out and 'actual file count 1' in out))

        # --- Observed text quoting the Proposed Rule heading does not corrupt the split --
        # Deep-check regression case: a naive first-match split on '## Proposed
        # Rule' truncates Observed and folds the rest of it into the Rule the
        # moment Observed narrates something that itself contains that literal
        # heading line -- a real risk for a candidate ABOUT a heading collision.
        f8 = make_candidate(
            'pipeline-fixture-heading', recurrence=2, occasion='x',
            observed='the output contained a line reading\n## Proposed Rule\nwhich confused a naive parser',
            rule='The real proposed rule text.')
        rc, out = pyrun(promote_tool, '--file', str(f8), '--level', 'individual')
        cases.append(("an Observed section that quotes the literal '## Proposed "
                      "Rule' heading does not corrupt the extracted Rule text",
                      rc == 0 and 'The real proposed rule text.' in out
                      and 'confused a naive parser' not in out))

        # --- team --as-issue: authority, not access, decides the path ---------
        # Added 2026-09-02 after a real dependent-repo session worked through
        # exactly when a team candidate needs to become a GitHub Issue rather
        # than a quiet candidates/ file: only when whoever's raising it is NOT
        # a listed approver. A listed approver's own say-so already lands a
        # shared practice directly (precedent_land.py), so --as-issue and the
        # nudge below are both about authority, never about git access.
        team_repo = tmp / 'precedent-team-fixture'
        (team_repo / 'candidates').mkdir(parents=True)
        (team_repo / 'approvers.json').write_text(
            json.dumps({'approvers': [{'name': 'Approved Person', 'github': 'approved-gh'}]}),
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=team_repo, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin',
                        'https://github.com/fixture-owner/fixture-team.git'],
                       cwd=team_repo, check=True)

        f10 = make_candidate('pipeline-fixture-disclose-team', recurrence=2, occasion='x')
        rc, out = pyrun(promote_tool, '--file', str(f10), '--level', 'team')
        rc, out = pyrun(land_tool, '--file', str(f10), '--level', 'team',
                        '--path', str(team_repo), '--approved-by', 'Approved Person')
        cases.append(('landing a shared practice by a real approver discloses the '
                      'named shared set, already in force for everyone on it',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'SHARED practice set' in out and str(team_repo) in out
                      and "'Approved Person'" in out))

        def make_issue_draft(raised_by, **extra):
            gh_repo = extra.pop('github_repo', None)
            args = [cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                    '--as-issue', 'true',
                    '--slug', extra.pop('slug', 'pipeline-fixture-issue'),
                    '--title', 't', '--signal', 'explicit-instruction',
                    '--raised-by', raised_by, '--observed', 'a fixture incident',
                    '--proposed-rule', 'Always do the fixture thing.',
                    '--occasion', 'a fixture occasion', '--recurrence', '2']
            if gh_repo:
                args += ['--github-repo', gh_repo]
            return pyrun(*args)

        rc, out = make_issue_draft('Someone Not An Approver', slug='pipeline-fixture-issue-a')
        no_file_written = not any(team_repo.glob('candidates/pipeline-fixture-issue-a-*.md'))
        cases.append(('team --as-issue drafts a GitHub Issue body and URL, and '
                      'writes nothing to candidates/, for a non-approver',
                      rc == 0
                      and 'github.com/fixture-owner/fixture-team/issues/new' in out
                      and 'labels=precedent-candidate' in out
                      and no_file_written))

        rc, out = make_issue_draft('Approved Person', slug='pipeline-fixture-issue-b')
        cases.append(('team --as-issue nudges toward landing directly when '
                      "--raised-by is already a listed approver, by name",
                      rc == 0 and 'already a listed approver' in out))

        rc, out = make_issue_draft('approved-gh', slug='pipeline-fixture-issue-c')
        cases.append(('the same nudge fires matching on the github handle, '
                      'not just the display name',
                      rc == 0 and 'already a listed approver' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                        '--slug', 'pipeline-fixture-disclose-cand-i', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'harness',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('raising an individual candidate discloses it as a '
                      "proposal in the person's own set, not yet a practice",
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'YOUR OWN individual set' in out and str(repo) in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                        '--slug', 'pipeline-fixture-disclose-cand-t', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'Approved Person',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('an approver filing a team candidate (rather than landing '
                      'directly) discloses which shared set it sits in and that it '
                      'still needs a yes',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'SHARED set at' in out and str(team_repo) in out
                      and 'already an approver' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                        '--slug', 'pipeline-fixture-disclose-cand-n', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'Someone Not An Approver',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('a non-approver filing a plain team candidate (forgetting '
                      '--as-issue) gets an explicit warning that nothing is '
                      'watching for it, not just a quiet file',
                      rc == 0 and 'DISCLOSE TO THE HUMAN, PLAINLY' in out
                      and 'NOT a listed approver' in out and '--as-issue' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                        '--as-issue', 'true', '--slug', 'pipeline-fixture-issue-d',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--as-issue is refused for --level individual '
                      '(no one else to notify)',
                      rc == 1 and 'only applies to --level shared' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'universal',
                        '--slug', 'pipeline-fixture-disclose-cand-u', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'harness',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('raising a universal candidate discloses it as a proposal '
                      'for everyone, not yet a practice for anyone',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'proposal for EVERYONE using Precedent' in out))

        no_remote_repo = tmp / 'fixture-team-no-remote'
        (no_remote_repo / 'candidates').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q'], cwd=no_remote_repo, check=True)
        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(no_remote_repo),
                        '--as-issue', 'true', '--slug', 'pipeline-fixture-issue-e',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--as-issue refuses cleanly, without guessing, when the '
                      'repo has no detectable GitHub remote and --github-repo '
                      'was not given',
                      rc == 1 and 'could not detect a GitHub owner/repo' in out
                      and '--github-repo' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(no_remote_repo),
                        '--as-issue', 'true', '--github-repo', 'override-owner/override-repo',
                        '--slug', 'pipeline-fixture-issue-f',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--github-repo overrides remote detection entirely, for '
                      'a repo git could not identify on its own',
                      rc == 0 and 'github.com/override-owner/override-repo/issues/new' in out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'creation pipeline fires ({len(cases)} stated cases: all four '
          f'promotion criteria refuse individually and pass together, '
          f'landing enforces registered-check and named-approver invariants)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_land_refusal_says_whether_a_pull_request_gets_checks():
    """When a landing is refused and sent through a pull request, the land
    tool says whether any workflow checks a pull request into that branch,
    and with none, to merge at once.

    WHY (2026-10-18). The refusal said "merge it once its checks pass"; no
    workflow ran on pull requests into staging, and a session waited on a
    check that never started until Morgan asked if anything was happening."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    # No PyYAML guard: GitHub's runner has none, and this test used to
    # report itself not applicable there (#1218), so CI never ran the path.
    # pull_request_checks reads workflows itself now (workflow_triggers).
    cases = []
    dash = ('name: x\n"on":\n  # comment\n  pull_request:\n    branches:\n'
            '      - main  # trailing\n      - \'rel/*\'\n  workflow_dispatch:\n'
            'jobs: {}\n')
    got = pb.workflow_triggers(dash)
    cases.append(('a quoted on:, comments and a dash list of branches are read',
                  got == {'pull_request': {'branches': ['main', 'rel/*']},
                          'workflow_dispatch': {}}, str(got)))
    got = pb.workflow_triggers('on: push\njobs: {}\n')
    cases.append(('a single inline event is read', got == {'push': {}}, str(got)))
    cases.append(('a file with no on: cannot be told',
                  pb.workflow_triggers('jobs: {}\n') is None, ''))
    with tempfile.TemporaryDirectory() as t:
        wf = pathlib.Path(t) / '.github' / 'workflows'
        wf.mkdir(parents=True)
        (wf / 'ci.yml').write_text(
            'on:\n  pull_request:\n    branches: [main]\n  push:\n'
            '    branches: [main]\njobs: {}\n', encoding='utf-8')
        cases.append(('a pull request into staging gets no check',
                      pb.pull_request_checks(t, 'staging') == [], ''))
        cases.append(('a pull request into main gets ci.yml',
                      pb.pull_request_checks(t, 'main') == ['ci.yml'], ''))
        note = pb.pull_request_route_note(t, 'staging', checks_ran=True)
        cases.append(('with none, after the quick checks, the note says '
                      'merge straight away',
                      'merge it straight away' in note
                      and 'passed on this composition' in note
                      and 'Do not wait' in note, note))
        note = pb.pull_request_route_note(t, 'staging')
        cases.append(('called with two arguments (a plain push), the note '
                      'never says the quick checks passed, and names the '
                      'command to run them',
                      'passed' not in note
                      and 'python3 tools/precedent_push_check.py' in note
                      and 'Nothing has run the quick checks' in note, note))
        saved = pb.pull_request_checks
        pb.pull_request_checks = lambda root, base: None
        try:
            unread = pb.pull_request_route_note(t, 'staging')
            unread_ran = pb.pull_request_route_note(t, 'staging',
                                                    checks_ran=True)
        finally:
            pb.pull_request_checks = saved
        cases.append(('workflows unreadable, nothing run: the note says to '
                      'run the quick checks, not that they passed',
                      'having passed' not in unread
                      and 'python3 tools/precedent_push_check.py' in unread,
                      unread))
        cases.append(('workflows unreadable, after the quick checks: the note '
                      'says they passed',
                      'the quick checks above having passed' in unread_ran,
                      unread_ran))
        (wf / 'any.yml').write_text('on: [pull_request]\njobs: {}\n',
                                    encoding='utf-8')
        cases.append(('a bare pull_request trigger covers every base',
                      pb.pull_request_checks(t, 'staging') == ['any.yml'], ''))
    cases.append(('the land tool prints the note after a pull-request refusal',
                  'pull_request_route_note(root, staging, checks_ran=True)' in
                  (ROOT / 'tools' / 'precedent_branches.py').read_text(
                      encoding='utf-8'), ''))
    bad = [f'{c[0]} ({c[2]})' for c in cases if not c[1]]
    check(f'a land refusal says whether a pull request gets checks '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_staging_tier_is_never_main_where_origin_has_staging():
    """THE BUG (2026-10-14, precedent-shared-ladder). A repository declaring
    base_branch "main" and landing_branch "staging", with no staging_branch,
    took main as its staging tier: staging_branch() fell back to
    base_branch. --landing printed "main" above its own reason line naming
    staging, --land refused, and --promote looked for a tier that no longer
    exists. Since then main is not the staging tier where the repo
    lands on staging and origin has that branch.

    A. base main, landing staging, origin has staging: the tier is staging,
       and --landing's answer agrees with its reason;
    B. CONTROL: the same repo whose origin has no staging branch still
       promotes into main (a staging branch it does not have is never named);
    C. CONTROL: base main with no landing_branch stays main."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='staging-tier-'))
    nocfg = str(tmp / 'no-config.json')
    cases = []

    def g(*a):
        return subprocess.run(['git', *a], capture_output=True, text=True, env=env)
    try:
        seed = tmp / 'seed'
        g('init', '-q', '-b', 'main', str(seed))
        g('-C', str(seed), 'commit', '-q', '--allow-empty', '-m', 'x')
        bare_with, bare_without = tmp / 'with.git', tmp / 'without.git'
        g('clone', '-q', '--bare', str(seed), str(bare_without))
        g('-C', str(seed), 'branch', 'staging')
        g('clone', '-q', '--bare', str(seed), str(bare_with))

        def clone(bare, name, cfg):
            c = tmp / name
            g('clone', '-q', str(bare), str(c))
            (c / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            return c
        both = {'base_branch': 'main', 'landing_branch': 'staging'}
        a = clone(bare_with, 'a', both)
        land_a = pb.landing_branch(a, nocfg)
        cases.append(('A. origin has staging: the tier is staging, and --landing '
                      'agrees with its reason',
                      pb.staging_branch(a) == 'staging'
                      and (land_a[0] == 'staging' or 'staging' not in land_a[1]),
                      f'{pb.staging_branch(a)} {land_a}'))
        b = clone(bare_without, 'b', both)
        cases.append(('B. CONTROL: no staging on origin still promotes into main',
                      pb.staging_branch(b) == 'main', pb.staging_branch(b)))
        c = clone(bare_with, 'c', {'base_branch': 'main'})
        cases.append(('C. CONTROL: no landing_branch stays main',
                      pb.staging_branch(c) == 'main', pb.staging_branch(c)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'the staging tier is never main where origin has staging '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_landers_wait_their_turn_for_the_lock():
    """Both landers hold the lock Promote takes, and wait while it is held.

    2026-10-10, a consumer: one session landed small edits on its landing
    branch every thirty to sixty seconds, and the queue lander's six
    attempts over two runs all ended "push rejected; master kept moving".
    Each attempt took about 25 seconds of merge, resync and check, then
    started over at once, so it could never win. Neither lander took the
    lock Promote and the merge gate already take. Now both do, from the
    merge to the push, and a busy lock is waited out with a growing,
    jittered pause rather than refused. The fixture: a scratch origin, a
    second window holding the lock when the lander starts and freeing it
    during the first wait, and a gate that records who holds the lock while
    the lander checks.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-lock-'))
    cases = []
    try:
        script = tmp / 'run.py'
        script.write_text(f"""
import json, os, pathlib, subprocess, sys, time
sys.path.insert(0, {str(ROOT / 'tools')!r})
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com')
import precedent_branches as pb
import land_next as ln
import land_queue
td = pathlib.Path({str(tmp)!r})
out = {{}}
# The backoff on its own: busy twice, then held.
seen, now = [], [0.0]
states = iter([('busy', 'w1'), ('busy', 'w1'), ('held', 'c')])
real_claim = pb._lock_claim
pb._lock_claim = lambda root, say, what=None: next(states)
def nap(s):
    seen.append(s); now[0] += s
r = pb.wait_for_landing_lock('.', 'x', say=lambda *a: None, sleep=nap,
                             clock=lambda: now[0], jitter=lambda: 0.5)
out['backoff'] = [r, list(seen)]
pb._lock_claim = lambda root, say, what=None: ('busy', 'w2')
seen.clear(); now[0] = 0.0
r = pb.wait_for_landing_lock('.', 'x', say=lambda *a: None, limit=60, sleep=nap,
                             clock=lambda: now[0], jitter=lambda: 0.9)
out['gives_up'] = [r, now[0]]
pb._lock_claim = real_claim
# --land: a lock that never frees lands nothing; a held one is released.
released, composed = [], []
pb.lands_on_staging = lambda root: (True, 'fixture')
pb._git = lambda root, *a: 'abc123' if a[0] == 'rev-parse' else ''
pb._run = lambda root, *a, **k: subprocess.CompletedProcess(a, 0, '', '')
pb._land_composed = lambda *a: (composed.append(a[2]), (0, 'LANDED at x'))[1]  # root, sha, label, ...
pb.wait_for_landing_lock = lambda root, what, say: ('busy', 'held by w3')
out['land_busy'] = [list(pb._land('.', 'feat', 'feat', 'staging', lambda *a: None)), list(composed)]
pb.wait_for_landing_lock = lambda root, what, say: ('held', 'c9')
pb._lock_release = lambda root, held, say: released.append(held)
out['land_held'] = [list(pb._land('.', 'feat', 'feat', 'staging', lambda *a: None)), list(composed), released]
import importlib; importlib.reload(pb)
# The queue lander, end to end on a scratch origin.
ln.report_failure = lambda *a: ''
ln.TRUNK, ln.SHARED_CACHES, ln.LEDGERS = 'master', ('.cache',), ()
origin, work, other = td / 'o.git', td / 'w', td / 'other'
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'master', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g = lambda *a: ln.git(work, *a)
g('checkout', '-q', '-b', 'master')
(work / 'base.txt').write_text('b\\n')
(work / 'gate.py').write_text(
    "import subprocess,pathlib\\n"
    "subprocess.run(['git','fetch','-q','origin','precedent-promote-lock'])\\n"
    "s=subprocess.run(['git','log','-1','--format=%s','FETCH_HEAD'],capture_output=True,text=True).stdout\\n"
    "pathlib.Path({str(tmp / 'during')!r}).write_text(s)\\n")
g('add', '-A'); g('commit', '-qm', 'base'); g('push', '-q', 'origin', 'master')
g('checkout', '-q', '-b', 'feat/x'); (work / 'x.txt').write_text('x\\n')
g('add', '-A'); g('commit', '-qm', 'x'); g('push', '-q', 'origin', 'feat/x')
g('checkout', '-q', 'master')
subprocess.run(['git', 'clone', '-q', str(origin), str(other)], capture_output=True)
os.environ['PRECEDENT_SESSION_NAME'] = 'other window'
state, held = pb._lock_claim(other, lambda *a: None)
os.environ['PRECEDENT_SESSION_NAME'] = 'the lander'
out['other_claimed'] = state
waits = []
def free_on_first_wait(s):
    waits.append(s)
    if len(waits) == 1:
        pb._lock_release(other, held, lambda *a: None)
time.sleep = free_on_first_wait
store = land_queue._store(work)
land_queue.request(store, 'feat/x', repo=work)
rc = ln.land_queue_run(work, gates=[('gate', ['python3', 'gate.py'])], push_check=['true'],
                       bestpractice=None, store=store, sync_cmd=None)
g('fetch', '-q', 'origin', 'master', 'precedent-promote-lock')
out['lander'] = dict(rc=rc, waits=len(waits),
                     landed='x.txt' in g('ls-tree', '--name-only', 'origin/master').stdout,
                     during=(td / 'during').read_text() if (td / 'during').exists() else '',
                     after=g('log', '-1', '--format=%s', 'origin/precedent-promote-lock').stdout.strip())
print(json.dumps(out))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=180)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        b = out.get('backoff') or [[None], []]
        cases.append(('a busy lock is waited out: two waits, then it is held',
                      b[0] == ['held', 'c'] and len(b[1]) == 2, why if not out else str(b)))
        cases.append(('each wait is longer than the last (5s, then 10s, at the '
                      'middle of the jitter)', b[1] == [5.0, 10.0], str(b[1])))
        gu = out.get('gives_up') or [[None], 0]
        cases.append(('a lock held past the limit returns busy, and the waits '
                      'never run past the limit', gu[0] == ['busy', 'w2'] and gu[1] <= 60,
                      str(gu)))
        lb = out.get('land_busy') or [[None, ''], ['?']]
        cases.append(('--land with the lock still held lands nothing and says '
                      'why', lb[0][0] == 1 and 'landing lock' in lb[0][1] and lb[1] == [],
                      str(lb)))
        lh = out.get('land_held') or [[None], [], []]
        cases.append(('--land with the lock held by itself lands, and frees '
                      'the lock after', lh[0][0] == 0 and lh[1] == ['feat'] and lh[2] == ['c9'],
                      str(lh)))
        ld = out.get('lander') or {}
        cases.append(('the queue lander waits while another window holds the '
                      'lock, then lands', out.get('other_claimed') == 'held'
                      and ld.get('rc') == 0 and ld.get('landed') and ld.get('waits', 0) >= 1,
                      str(ld) or why))
        cases.append(('...holding the lock itself while its gate runs',
                      'held by the lander' in ld.get('during', '')
                      and 'landing feat/x on master' in ld.get('during', ''),
                      ld.get('during', '')))
        cases.append(('...and frees it once it has landed',
                      ld.get('after', '').startswith('free'), ld.get('after', '')))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'landers wait their turn for the lock ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_land_tells_the_push_hooks_what_it_lands():
    """--land's push names the branch it lands, and runs in the person's own
    checkout, so a pre-push hook a practice declares can judge what is being
    landed and not only where it goes.

    2026-10-17, the very deep check: a branch named by the cloud harness was
    landed on staging by a bare --land while a practice's pre-push hook was
    in force against that very name. git's pre-push sees only
    `<sha> refs/heads/staging` for a landing, the push ran from a throwaway
    worktree where hooks listed in the checkout's untracked files are not,
    and nothing said what was being landed. Morgan, 2026-10-17: "Fix the
    other issues you found including the checks that never run". The
    fixture's pre-push hook records what it was told and where it ran.

    Negative control, measured 2026-10-17: with the push made from the
    worktree with no variable (the code before this), the first two cases
    fail."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-source-'))
    cases = []
    try:
        log = tmp / 'hook.log'
        hooks = tmp / 'hooks'
        hooks.mkdir()
        (hooks / 'pre-push').write_text(
            '#!/bin/sh\ncat >/dev/null\n'
            f'printf "%s|%s\\n" "$PRECEDENT_LANDING_SOURCE" '
            f'"$(git rev-parse --show-toplevel)" >> {str(log)!r}\nexit 0\n',
            encoding='utf-8')
        (hooks / 'pre-push').chmod(0o755)
        script = tmp / 'run.py'
        script.write_text(f"""
import json, os, pathlib, subprocess, sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                  PRECEDENT_USER_CONFIG={str(tmp / 'no-config.json')!r},
                  GIT_CONFIG_GLOBAL={str(tmp / 'gitconfig')!r})
os.environ.pop('PRECEDENT_LANDING_SOURCE', None)
pathlib.Path({str(tmp / 'gitconfig')!r}).write_text('')
import precedent_branches as pb
td = pathlib.Path({str(tmp)!r})
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), *a], capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
g('config', 'core.hooksPath', {str(hooks)!r})
g('checkout', '-q', '-b', 'claude/demo-work-abcdef')
(work / 'x.md').write_text('x\\n'); g('add', '-A'); g('commit', '-qm', 'work')
pb._check = lambda *a, **k: (True, 'stub check')
said = []
rc, verdict = pb._land_composed(work, g('rev-parse', 'HEAD').stdout.strip(),
                                'claude/demo-work-abcdef', 'staging', 'the fixture',
                                said.append)
g('fetch', '-q', 'origin')
print(json.dumps(dict(rc=rc, verdict=verdict, said='\\n'.join(said)[-400:],
                      landed='x.md' in g('ls-tree', '--name-only', 'origin/staging').stdout)))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        seen = log.read_text(encoding='utf-8').splitlines() if log.exists() else []
        source, _, top = (seen[-1] if seen else '').partition('|')
        cases.append(('THE DISCRIMINATING CASE: the pre-push hook is told the '
                      'branch being landed', source == 'claude/demo-work-abcdef',
                      str(seen) or why))
        cases.append(('...and runs in the person\'s own checkout, where untracked '
                      'hook lists live, not in the throwaway worktree',
                      bool(top) and pathlib.Path(top).resolve()
                      == (tmp / 'w').resolve(), str(seen) or why))
        cases.append(('...and the landing still lands',
                      out.get('rc') == 0 and out.get('landed'), str(out) or why))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'--land tells the push\'s hooks what it lands ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_land_hands_over_the_landed_branchs_delete_link():
    """A --land ends by naming the branch it landed as done, with the
    one-click delete link (branch-delete-links): no pull request merged it,
    so GitHub's auto-delete never will.

    2026-11-01: one practice set's origin held seventeen merged branches,
    every one landed by --land or Produce, and nothing ever said any of them
    was done. Morgan, 2026-11-01: "All the issues above - act, do the root
    fixes". The fixture lands a pushed branch through _land_composed, then
    asks landed_branch_line about three branches it must stay quiet on.

    Negative control, measured 2026-11-01: with the call in _land_composed
    removed, the first case fails."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-done-'))
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
import precedent_branches as pb
import precedent_stale_branches as psb
psb._slug = lambda repo: ('o', 'r')
td = pathlib.Path({str(tmp)!r})
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), *a], capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
g('checkout', '-q', '-b', 'claude/demo-work-abcdef')
(work / 'x.md').write_text('x\\n'); g('add', '-A'); g('commit', '-qm', 'work')
g('push', '-q', 'origin', 'claude/demo-work-abcdef')
pb._check = lambda *a, **k: (True, 'stub check')
said = []
rc, verdict = pb._land_composed(work, g('rev-parse', 'HEAD').stdout.strip(),
                                'claude/demo-work-abcdef', 'staging', 'the fixture',
                                said.append)
g('fetch', '-q', 'origin')
landed = g('rev-parse', 'origin/staging').stdout.strip()
# Moved after it was landed: origin's branch carries a commit staging lacks.
(work / 'y.md').write_text('y\\n'); g('add', '-A'); g('commit', '-qm', 'more')
g('push', '-q', 'origin', 'claude/demo-work-abcdef')
moved = pb.landed_branch_line(work, 'claude/demo-work-abcdef', 'staging', landed)
g('checkout', '-q', '-b', 'never-pushed')
unpushed = pb.landed_branch_line(work, 'never-pushed', 'staging', landed)
tier = pb.landed_branch_line(work, 'main', 'staging', landed)
print(json.dumps(dict(rc=rc, said='\\n'.join(said), moved=moved,
                      unpushed=unpushed, tier=tier)))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        said = out.get('said', '')
        url = 'https://github.com/o/r/branches/all?query=claude%2Fdemo-work-abcdef'
        cases.append(('THE DISCRIMINATING CASE: the landing names the landed '
                      'branch as done, with its filtered delete link',
                      out.get('rc') == 0 and 'DONE WITH claude/demo-work-abcdef'
                      in said and url in said, said[-500:] or why))
        cases.append(('...and says never to delete it yourself',
                      'never-delete-a-remote-branch' in said, said[-300:] or why))
        cases.append(('a branch that moved after it was landed is not offered',
                      out.get('moved') == '', str(out.get('moved')) or why))
        cases.append(('a branch origin does not have is not offered',
                      out.get('unpushed') == '', str(out.get('unpushed')) or why))
        cases.append(('a tier branch is never offered',
                      out.get('tier') == '', str(out.get('tier')) or why))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'--land hands over the landed branch\'s delete link ({len(cases)} '
          f'stated cases)', not bad, '; '.join(f'{n} ({d})' for n, d in bad))


def check_land_confirm_says_whether_what_landed_was_checked():
    """--land-confirm COMMIT, after a landing's pull request was merged by
    hand, says whether staging took the checked composition as it was, and
    when staging had moved first, runs the quick checks on what landed.

    THE BUG (2026-10-29). On #1334 staging moved while the landing's pull
    request was open; GitHub merged it into the newer staging, so what
    landed was a tree no quick check had run on, and nothing said so.
    Hermetic: a bare origin, a composition commit, staging taking it four
    ways; the quick check is a stub that records what it was run on.

    Negative control, measured 2026-10-29: before land_confirm there was no
    such step, and the fixture fails at its first call."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-confirm-'))
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
import precedent_branches as pb
td = pathlib.Path({str(tmp)!r})
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), '-c', 'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
base = g('rev-parse', 'HEAD').stdout.strip()
ran = []
verdict = [True]
pb._check = lambda root, wt, *a, **k: (ran.append(subprocess.run(
    ['git', '-C', str(wt), 'rev-parse', 'HEAD'], capture_output=True,
    text=True).stdout.strip()) or (verdict[0], 'stub check output'))
def comp(name):                   # --land composes on staging's tip
    g('fetch', '-q', 'origin')
    g('checkout', '-q', '-B', name, 'origin/staging')
    (work / (name + '.md')).write_text(name + '\\n'); g('add', '-A'); g('commit', '-qm', name)
    return g('rev-parse', 'HEAD').stdout.strip()
def confirm(sha):
    said = []
    rc = pb.land_confirm(work, sha, said.append)
    return rc, '\\n'.join(said)
out = {{}}
a = comp('a')
out['not_landed'] = confirm(a)
g('push', '-q', 'origin', a + ':refs/heads/staging')
out['ff'] = confirm(a)
b = comp('b')
g('checkout', '-q', '-B', 's', 'origin/staging'); g('merge', '-q', '--no-ff', '--no-edit', b)
g('push', '-q', 'origin', 's:staging')
out['no_ff'] = confirm(b)
# staging moves while the pull request for c is open, then GitHub merges c
c = comp('c')
g('checkout', '-q', '-B', 's', 'origin/staging')
(work / 'other.md').write_text('o\\n'); g('add', '-A'); g('commit', '-qm', 'someone else landed')
g('merge', '-q', '--no-ff', '--no-edit', c)
landed = g('rev-parse', 'HEAD').stdout.strip()
g('push', '-q', 'origin', 's:staging')
ran.clear()
out['moved_pass'] = confirm(c) + (list(ran),)
verdict[0] = False
ran.clear()
out['moved_fail'] = confirm(c) + (list(ran),)
out['landed'] = landed
print(json.dumps(out))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        if not out:
            cases.append(('the fixture ran', False, why))
        else:
            r = out['not_landed']
            cases.append(('a composition staging does not hold: NOT LANDED, exit 1',
                          r[0] == 1 and 'NOT LANDED' in r[1], str(r)))
            r = out['ff']
            cases.append(('staging took the composition itself: LANDED AS CHECKED',
                          r[0] == 0 and 'LANDED AS CHECKED' in r[1], str(r)))
            r = out['no_ff']
            cases.append(('a merge commit onto an unmoved staging: LANDED AS CHECKED',
                          r[0] == 0 and 'LANDED AS CHECKED' in r[1], str(r)))
            r = out['moved_pass']
            cases.append(('THE DISCRIMINATING CASE: staging moved first -- said, and '
                          'the quick checks run on the commit that landed',
                          r[0] == 0 and 'moved before the pull request merged' in r[1]
                          and 'CHECKED NOW' in r[1] and r[2] == [out['landed']], str(r)))
            r = out['moved_fail']
            cases.append(('...and when they fail there: LANDED, AND FAILING, exit 1',
                          r[0] == 1 and 'LANDED, AND FAILING' in r[1], str(r)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + ' -- ' + c[2][:300] for c in cases if not c[1]]
    check(f'--land-confirm says whether what landed was checked '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_land_sent_to_a_pull_request_carries_mains_work():
    """A landing refused for the pull-request route pushes the composition
    it checked -- staging, main's direct work and the branch -- to the
    branch, so the pull request from it is not refused for lacking main.

    2026-10-19: a change to tools/verify_harness.py was refused by --land
    ("This one takes a pull request"); the pull request from the branch as
    it stood lacked main's four direct commits, and the push check and
    merge guard sent the session back to --land. The way out was a hand
    merge of origin/main. The fixture's pre-push hook refuses a push to
    staging as the real one does; main carries a commit staging lacks.

    Negative control, measured 2026-10-19: without
    _carry_composition_to_branch the branch on origin lacks main's commit
    and the first case fails.

    Negative control, measured 2026-10-29: without the `local` comparison in
    _carry_composition_to_branch the unpushed-commit case fails."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-pr-'))
    cases = []
    try:
        hooks = tmp / 'hooks'
        hooks.mkdir()
        (hooks / 'pre-push').write_text(
            '#!/bin/sh\nwhile read l ls r rs; do\n'
            '  case "$r" in refs/heads/staging) echo "push refused: this one '
            'takes a pull request" >&2; exit 1;; esac\ndone\nexit 0\n',
            encoding='utf-8')
        (hooks / 'pre-push').chmod(0o755)
        script = tmp / 'run.py'
        script.write_text(f"""
import json, os, pathlib, subprocess, sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                  PRECEDENT_USER_CONFIG={str(tmp / 'no-config.json')!r},
                  GIT_CONFIG_GLOBAL={str(tmp / 'gitconfig')!r})
pathlib.Path({str(tmp / 'gitconfig')!r}).write_text('')
import precedent_branches as pb
td = pathlib.Path({str(tmp)!r})
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), *a], capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
g('checkout', '-q', '-b', 'claude/engine-change-abcdef')
(work / 'x.md').write_text('x\\n'); g('add', '-A'); g('commit', '-qm', 'work')
g('push', '-q', 'origin', 'claude/engine-change-abcdef')
g('checkout', '-q', 'main')
(work / 'direct.md').write_text('d\\n'); g('add', '-A'); g('commit', '-qm', 'direct')
g('push', '-q', 'origin', 'main')
g('checkout', '-q', 'claude/engine-change-abcdef')
g('config', 'core.hooksPath', {str(hooks)!r})
pb._check = lambda *a, **k: (True, 'stub check')
said = []
rc, verdict = pb._land_composed(work, g('rev-parse', 'HEAD').stdout.strip(),
                                'claude/engine-change-abcdef', 'staging', 'the fixture',
                                said.append)
g('fetch', '-q', 'origin')
files = g('ls-tree', '--name-only', 'origin/claude/engine-change-abcdef').stdout.split()
g('checkout', '-q', '-b', 'claude/fix-main-abcdef', 'origin/main')
(work / 'y.md').write_text('y\\n'); g('add', '-A'); g('commit', '-qm', 'fix')
fix = g('rev-parse', 'HEAD').stdout.strip()
g('push', '-q', 'origin', 'claude/fix-main-abcdef')
said2 = []
pb._land_composed(work, fix, 'claude/fix-main-abcdef', 'staging', 'the fixture', said2.append)
g('fetch', '-q', 'origin')
fix_moved = g('rev-parse', 'origin/claude/fix-main-abcdef').stdout.strip() != fix
# 2026-10-28: a branch cut from main whose LOCAL tip holds a commit never
# pushed. Origin's tip carries all of main, so the old shortcut said
# "lacks nothing" and the unpushed commit was left out of the pull request.
g('checkout', '-q', '-b', 'claude/unpushed-abcdef', 'origin/main')
(work / 'u.md').write_text('u\\n'); g('add', '-A'); g('commit', '-qm', 'pushed')
g('push', '-q', 'origin', 'claude/unpushed-abcdef')
(work / 'v.md').write_text('v\\n'); g('add', '-A'); g('commit', '-qm', 'never pushed')
unpushed = g('rev-parse', 'HEAD').stdout.strip()
said4 = []
pb._land_composed(work, unpushed, 'claude/unpushed-abcdef', 'staging', 'the fixture', said4.append)
g('fetch', '-q', 'origin')
unpushed_carried = g('merge-base', '--is-ancestor', unpushed,
                     'origin/claude/unpushed-abcdef').returncode == 0
# 2026-10-20: a branch carrying all of main's work that does NOT merge
# cleanly into staging (staging moved on) gets the checked composition,
# never "lacks nothing".
g('checkout', '-q', '-B', 'stg', 'origin/staging')
(work / 'z.md').write_text('staging\\n'); g('add', '-A'); g('commit', '-qm', 'staging moved')
g('-c', 'core.hooksPath=/dev/null', 'push', '-q', 'origin', 'stg:staging')
g('checkout', '-q', '-b', 'claude/behind-staging-abcdef', 'origin/main')
(work / 'z.md').write_text('branch\\n'); g('add', '-A'); g('commit', '-qm', 'clash')
g('push', '-q', 'origin', 'claude/behind-staging-abcdef')
g('merge', '-q', '-X', 'ours', '--no-edit', 'origin/staging')
comp = g('rev-parse', 'HEAD').stdout.strip()
said3 = pb._carry_composition_to_branch(work, 'claude/behind-staging-abcdef', comp, 'staging')
g('fetch', '-q', 'origin')
behind_moved = g('rev-parse', 'origin/claude/behind-staging-abcdef').stdout.strip() == comp
behind_moved = behind_moved and comp != g('rev-parse', 'HEAD^1').stdout.strip()
print(json.dumps(dict(rc=rc, verdict=verdict, said='\\n'.join(said)[-600:], files=files,
                      fix_moved=fix_moved, said2='\\n'.join(said2)[-300:],
                      said3=said3, behind_moved=behind_moved,
                      unpushed_carried=unpushed_carried,
                      said4='\\n'.join(said4)[-300:],
                      staging=g('ls-tree', '--name-only', 'origin/staging').stdout.split())))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        files = out.get('files') or []
        cases.append(('THE DISCRIMINATING CASE: the branch on origin now carries '
                      'main\'s direct commit and its own work',
                      'direct.md' in files and 'x.md' in files, str(out) or why))
        cases.append(('...staging did not move, and the landing says it was refused',
                      out.get('rc') == 1 and 'x.md' not in (out.get('staging') or [])
                      and 'REFUSED' in (out.get('verdict') or ''), str(out) or why))
        cases.append(('...and the reply says the branch now carries the checked '
                      'composition', 'now carries the composition' in
                      (out.get('said') or ''), str(out) or why))
        cases.append(('a branch cut from main already carries its work and is '
                      'left where it is, so a red-main fix\'s head never moves',
                      out.get('fix_moved') is False
                      and 'as it stands lacks nothing' in (out.get('said2') or ''),
                      str(out) or why))
        cases.append(('a branch with all of main\'s work that conflicts with '
                      'staging gets the checked composition, not "lacks nothing"',
                      out.get('behind_moved') is True
                      and 'now carries the composition' in (out.get('said3') or ''),
                      str(out) or why))
        cases.append(('a branch whose local tip holds a commit origin lacks gets '
                      'the checked composition pushed, never "lacks nothing" '
                      '(2026-10-28)',
                      out.get('unpushed_carried') is True
                      and 'as it stands lacks nothing' not in (out.get('said4') or ''),
                      str(out) or why))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a landing sent to a pull request carries main\'s work '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))

def check_land_skips_a_push_the_pull_request_guard_would_refuse():
    """--land on a change the repository's own pull-request guard would
    refuse goes to the pull-request route without trying the push.

    2026-10-30: a branch touching tools/verify_harness.py was pushed at
    staging, the guard refused it, and only then did the tool print the
    pull-request route. The fixture's pre-push hook records any push aimed
    at staging and refuses it, as the real guard does. Two worlds: a change
    to tools/verify_harness.py (no push tried, the route still printed and
    the branch carries the composition) and a change to a plain file (the
    push is tried, as before).

    Negative control, measured 2026-10-30: with _takes_pull_request
    returning [] the first case fails -- the hook records the push."""
    import tempfile
    # A PLANTED GUARD, never a set's own file (2026-10-30 very deep check,
    # SET INDEPENDENCE). The real guard is a practice set's, and this test
    # read it from a sibling clone by the set's name: an engine test that
    # depended on one set being attached, and skipped on GitHub where none
    # is. What the engine owns is the contract _takes_pull_request calls --
    # in_force(), changed(root, base, tip), risky(root, paths, rev) -- so the
    # fixture plants a guard that keeps it and calls one file risky.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-skip-'))
    guard = tmp / 'landing_pr_guard.py'
    guard.write_text(
        'import subprocess\n'
        'def in_force():\n    return True\n'
        'def changed(root, base, tip):\n'
        '    r = subprocess.run(["git", "-C", str(root), "diff", "--name-only",\n'
        '                        f"{base}...{tip}"], capture_output=True, text=True)\n'
        '    return None if r.returncode else [p for p in r.stdout.splitlines() if p]\n'
        'def risky(root, paths, rev):\n'
        '    return [p for p in paths if p == "tools/verify_harness.py"]\n',
        encoding='utf-8')
    cases = []
    try:
        hooks = tmp / 'hooks'
        hooks.mkdir()
        tried = tmp / 'tried'
        (hooks / 'pre-push').write_text(
            '#!/bin/sh\nwhile read l ls r rs; do\n'
            f'  case "$r" in refs/heads/staging) echo "$ls" >> {str(tried)!r}; '
            'echo "push refused: this one takes a pull request" >&2; exit 1;; '
            'esac\ndone\nexit 0\n', encoding='utf-8')
        (hooks / 'pre-push').chmod(0o755)
        script = tmp / 'run.py'
        script.write_text(f"""
import json, os, pathlib, shutil, subprocess, sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                  PRECEDENT_USER_CONFIG={str(tmp / 'no-config.json')!r},
                  GIT_CONFIG_GLOBAL={str(tmp / 'gitconfig')!r})
os.environ.pop('PRECEDENT_NO_LADDERS', None)
pathlib.Path({str(tmp / 'gitconfig')!r}).write_text('')
import precedent_branches as pb
td = pathlib.Path({str(tmp)!r})
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), *a], capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
(work / 'tools').mkdir()
shutil.copy({str(guard)!r}, work / 'tools')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
g('config', 'core.hooksPath', {str(hooks)!r})
pb._check = lambda *a, **k: (True, 'stub check')
out = {{}}
for name, path in (('gating', 'tools/verify_harness.py'), ('plain', 'x.md')):
    g('checkout', '-q', '-b', 'claude/' + name + '-abcdef', 'origin/staging')
    (work / path).write_text(name + '\\n'); g('add', '-A'); g('commit', '-qm', name)
    g('-c', 'core.hooksPath=/dev/null', 'push', '-q', 'origin', 'claude/' + name + '-abcdef')
    tried = pathlib.Path({str(tried)!r})
    before = tried.read_text() if tried.exists() else ''
    said = []
    rc, verdict = pb._land_composed(work, g('rev-parse', 'HEAD').stdout.strip(),
                                    'claude/' + name + '-abcdef', 'staging',
                                    'the fixture', said.append)
    after = tried.read_text() if tried.exists() else ''
    out[name] = dict(rc=rc, verdict=verdict, said='\\n'.join(said)[-900:],
                     pushed=after != before)
print(json.dumps(out))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=300)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-600:]
        gating, plain = out.get('gating') or {}, out.get('plain') or {}
        cases.append(('THE DISCRIMINATING CASE: a change to tools/verify_harness.py '
                      'is never pushed at staging',
                      gating.get('pushed') is False and gating.get('rc') == 1,
                      (str(gating) if gating else why)))
        cases.append(('...it says no push was tried, and why, naming the file',
                      'with no push tried' in (gating.get('said') or '')
                      and 'tools/verify_harness.py' in (gating.get('verdict') or ''),
                      (str(gating) if gating else why)))
        cases.append(('...and still takes the pull-request route',
                      'now carries the composition' in (gating.get('said') or '')
                      or 'lacks nothing' in (gating.get('said') or ''),
                      (str(gating) if gating else why)))
        cases.append(('a change to a plain file still tries the push',
                      plain.get('pushed') is True
                      and 'the push was refused' in (plain.get('said') or ''),
                      (str(plain) if plain else why)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'--land skips a push the pull-request guard would refuse '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))

def check_one_fix_mends_two_red_landings_in_a_row():
    """--fixing takes several red landings joined by commas, and the fix's
    run starts from the oldest red base, so it covers all of them
    (2026-11-01: two landings went red one after the other; --fixing for
    either one left the other refusing the fix, with no way to name both)."""
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-two-reds-'))
    cases = []
    try:
        repo = tmp / 'r'
        repo.mkdir()
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                      capture_output=True, text=True).stdout.strip()
        g('init', '-q')
        shas = []
        for n in range(4):
            (repo / 'f').write_text(str(n))
            g('add', 'f')
            g('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', str(n))
            shas.append(g('rev-parse', 'HEAD'))
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import precedent_branches as pb
        finally:
            sys.path.pop(0)
        d = pb._reach_dir(repo)
        d.mkdir(parents=True, exist_ok=True)
        # Landing 1 (base shas[0]) went red, then landing 2 (base shas[1]).
        for i, (landed, since) in enumerate(((shas[1], shas[0]),
                                              (shas[2], shas[1]))):
            (d / f'{landed[:12]}-{i}.json').write_text(json.dumps(
                {'landed': landed, 'since': since, 'status': 'failed',
                 'label': f'red {i}', 'failing': [f'case {i}']}))
        one = pb.reach_gate(repo, shas[2][:12])
        cases.append(('THE CASE: naming only the second red still refuses, '
                      'and names the first',
                      bool(one[0]) and shas[1][:12] in one[0], one[0]))
        none = pb.reach_gate(repo, None)
        cases.append(('the refusal hands over one --fixing for both',
                      f'--fixing {shas[1][:12]},{shas[2][:12]}' in none[0]
                      or f'--fixing {shas[2][:12]},{shas[1][:12]}' in none[0],
                      none[0]))
        both = pb.reach_gate(repo, f'{shas[2][:12]},{shas[1][:12]}')
        cases.append(('CONTROL: naming both lets the fix through',
                      both[0] == '', both[0]))
        cases.append(("CONTROL: the fix's run starts from the oldest red base",
                      both[2] == shas[0], str(both[2])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'one --fixing mends two red landings in a row ({len(cases)} '
          f'stated cases)', not bad,
          '; '.join(f'{n} -- {str(x)[:200]}' for n, x in bad))


def check_land_holds_while_its_reached_tests_are_red():
    """--land starts the harness checks a landing reaches in the background
    and records the verdict; the next --land refuses while it is red unless
    it names itself the fix; and a change that takes a pull request has
    that pull request opened and merged by --land itself.

    Morgan, 2026-10-31 (strength: assented, "Yes on all four"), from the
    root issues of the 2026-10-30 very deep check's session: staging went
    red twice from checks only that run reaches, and about ten landings
    stopped for a pull request the session merged a minute later by hand.

    The fixture: a bare origin with staging, a stub harness whose verdict a
    file decides (red while it exists), a planted pull-request guard that
    calls tools/gate.py risky, and a stub GitHub API on localhost that
    merges by moving staging on the bare origin.

    Negative controls: with the run turned off a landing only prints the
    command and records nothing; with the automatic pull request off, a
    gating change stops at the printed steps and staging does not move."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-land-reach-'))
    cases = []
    try:
        script = tmp / 'run.py'
        script.write_text(f"""
import http.server, json, os, pathlib, subprocess, sys, threading, time
sys.path.insert(0, {str(ROOT / 'tools')!r})
td = pathlib.Path({str(tmp)!r})
(td / 'gitconfig').write_text('')
os.environ.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                  GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                  PRECEDENT_USER_CONFIG=str(td / 'no-config.json'),
                  GIT_CONFIG_GLOBAL=str(td / 'gitconfig'))
os.environ.pop('PRECEDENT_NO_LADDERS', None)
import precedent_branches as pb
origin, work = td / 'o.git', td / 'w'
g = lambda *a: subprocess.run(['git', '-C', str(work), *a], capture_output=True, text=True)
subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)])
subprocess.run(['git', 'clone', '-q', str(origin), str(work)], capture_output=True)
g('checkout', '-q', '-B', 'main')
(work / 'precedent.json').write_text('{{"landing_branch": "staging"}}\\n')
(work / 'tools').mkdir()
(work / 'tools' / 'harness_reach.py').write_text('')
(work / 'tools' / 'verify_harness.py').write_text(
    'import os, pathlib, sys\\n'
    'red = pathlib.Path(' + repr(str(td / 'red')) + ')\\n'
    'out = os.environ.get("PRECEDENT_HARNESS_FAILURES")\\n'
    'if red.exists():\\n'
    '    out and pathlib.Path(out).write_text("case one\\\\n")\\n'
    '    sys.exit(1)\\n'
    'out and pathlib.Path(out).write_text("")\\n')
(work / 'tools' / 'landing_pr_guard.py').write_text(
    'import subprocess\\n'
    'def in_force():\\n    return True\\n'
    'def changed(root, base, tip):\\n'
    '    r = subprocess.run(["git", "-C", str(root), "diff", "--name-only",\\n'
    '                        f"{{base}}...{{tip}}"], capture_output=True, text=True)\\n'
    '    return None if r.returncode else [p for p in r.stdout.splitlines() if p]\\n'
    'def risky(root, paths, rev):\\n'
    '    return [p for p in paths if p == "tools/gate.py"]\\n')
g('add', '-A'); g('commit', '-qm', 'base')
g('push', '-q', 'origin', 'main', 'main:staging')
pb._check = lambda *a, **k: (True, 'stub check')
pb.lands_on_staging = lambda root, user_config=None: (True, 'the fixture lands on staging')
out = {{}}

def branch(name, path):
    g('fetch', '-q', 'origin', 'staging')
    g('checkout', '-q', '-B', name, 'origin/staging')
    (work / path).write_text(name + '\\n'); g('add', '-A'); g('commit', '-qm', name)
    g('push', '-q', '-f', 'origin', name)
    return name

def land(name, fixing=None):
    said = []
    rc = pb.land(work, name, said.append, fixing=fixing)
    return rc, '\\n'.join(said)

def wait_record(sha):
    f = pb._reach_dir(work) / (sha[:12] + '.json')
    for _ in range(120):
        try:
            rec = json.loads(f.read_text())
            if rec.get('status') != 'running':
                return rec
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    return {{'status': 'timeout'}}

def staging_tip():
    return subprocess.run(['git', '-C', str(origin), 'rev-parse', 'staging'],
                          capture_output=True, text=True).stdout.strip()

os.environ['PRECEDENT_LAND_REACH_RUN'] = '1'
os.environ['PRECEDENT_LAND_AUTO_PR'] = '0'
(td / 'red').write_text('')
rc, said = land(branch('b1', 'x.md'))
one = staging_tip()
out['first'] = dict(rc=rc, started='STARTED IN THE BACKGROUND' in said,
                    rec=wait_record(one))
rc, said = land(branch('b2', 'y.md'))
out['held'] = dict(rc=rc, said=said[-700:], moved=staging_tip() != one)
(td / 'red').unlink()
rc, said = land('b2', fixing=one[:12])
two = staging_tip()
first_after = json.loads((pb._reach_dir(work) / (one[:12] + '.json')).read_text())
out['fix'] = dict(rc=rc, moved=two != one, first=first_after.get('status'),
                  rec=wait_record(two), since_ok=wait_record(two).get('since')
                  == out['first']['rec'].get('since'))
rd = pb._reach_dir(work)
(rd / 'aaaaaaaaaaaa.json').write_text(json.dumps({{'landed': 'a' * 40,
    'since': 'b' * 40, 'status': 'failed', 'label': 'x'}}))
os.environ['PRECEDENT_LAND_REACH_RUN'] = '0'
said_confirm = pb.start_reach_run(work, 'c' * 40, two, 'y', fixing='aaaaaaaaaaaa')
out['confirm_route'] = dict(since_ok=('PRECEDENT_HARNESS_SINCE=' + 'b' * 40) in said_confirm,
                            fixed=json.loads((rd / 'aaaaaaaaaaaa.json').read_text())['status'])
rc, said = land(branch('b3', 'z.md'))
three = staging_tip()
out['off'] = dict(rc=rc, printed='NEXT, IN THE BACKGROUND' in said,
                  recorded=(pb._reach_dir(work) / (three[:12] + '.json')).exists())

class Api(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code); self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length') or 0))
        self.reply(201, {{'number': 7}})
    def do_PUT(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)))
        r = subprocess.run(['git', '-C', str(origin), 'update-ref', 'refs/heads/staging',
                            body['sha']], capture_output=True)
        self.reply(200 if r.returncode == 0 else 405,
                   {{'merged': r.returncode == 0, 'sha': body['sha']}})
srv = http.server.HTTPServer(('127.0.0.1', 0), Api)
threading.Thread(target=srv.serve_forever, daemon=True).start()
pb._github_repo = lambda root: ('o', 'r')
os.environ.update(GITHUB_TOKEN='fixture-token',
                  PRECEDENT_GITHUB_API=f'http://127.0.0.1:{{srv.server_port}}')
rc, said = land(branch('b4', 'tools/gate.py'))
out['manual'] = dict(rc=rc, moved=staging_tip() != three,
                     steps='--land-confirm' in said)
os.environ['PRECEDENT_LAND_AUTO_PR'] = '1'
rc, said = land('b4')
four = staging_tip()
out['auto'] = dict(rc=rc, moved=four != three, said=said[-600:],
                   confirmed='LANDED AS CHECKED' in said, pr='#7' in said)
srv.shutdown()
print(json.dumps(out))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True,
                           text=True, cwd=str(tmp), timeout=600)
        try:
            out = json.loads(p.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {}
        why = (p.stdout + p.stderr)[-2500:]
        first, held, fix = out.get('first') or {}, out.get('held') or {}, out.get('fix') or {}
        off, manual, auto = out.get('off') or {}, out.get('manual') or {}, out.get('auto') or {}
        cases.append(('a landing starts its reached-tests run and records it red',
                      first.get('rc') == 0 and first.get('started')
                      and (first.get('rec') or {}).get('status') == 'failed'
                      and (first.get('rec') or {}).get('failing') == ['case one'],
                      str(first) if first else why))
        cases.append(('THE DISCRIMINATING CASE: the next landing is refused while '
                      'it is red, naming the failing case and the fix route',
                      held.get('rc') == 1 and not held.get('moved')
                      and 'case one' in (held.get('said') or '')
                      and '--fixing' in (held.get('said') or ''),
                      str(held) if held else why))
        cases.append(('...a landing that names itself the fix lands, marks the red '
                      'one fixed, and its own run covers both and passes',
                      fix.get('rc') == 0 and fix.get('moved')
                      and fix.get('first') == 'fixed'
                      and (fix.get('rec') or {}).get('status') == 'passed'
                      and fix.get('since_ok'),
                      str(fix) if fix else why))
        cr = out.get('confirm_route') or {}
        cases.append(('...and by the --land-confirm route too, the fix starts from '
                      'the red run\'s base and marks it fixed',
                      cr.get('since_ok') and cr.get('fixed') == 'fixed',
                      str(cr) if cr else why))
        cases.append(('NEGATIVE CONTROL: with the run off, a landing prints the '
                      'command and records nothing',
                      off.get('rc') == 0 and off.get('printed')
                      and not off.get('recorded'), str(off) if off else why))
        cases.append(('NEGATIVE CONTROL: with the automatic pull request off, a '
                      'gating change stops at the printed steps',
                      manual.get('rc') == 1 and not manual.get('moved')
                      and manual.get('steps'), str(manual) if manual else why))
        cases.append(('a gating change has its pull request opened and merged by '
                      '--land, and confirmed as checked',
                      auto.get('rc') == 0 and auto.get('moved') and auto.get('pr')
                      and auto.get('confirmed'), str(auto) if auto else why))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'--land holds while its reached tests are red, and lands its own '
          f'pull request ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))

def check_branch_name_counts_local_branches():
    """A branch name a local branch already has is taken, as one origin has
    is.

    2026-10-11: a rollout merged its update branch, and the next run asked
    for a name again. Origin had deleted nothing, the branch name was free
    there only because the previous one had been pushed under another, and
    the tool handed back the name a merged LOCAL branch still had -- so
    `git switch -c` refused it and the rollout script stopped without a
    word. The tool now asks the checkout's own branches too.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branch_name as pbn
    finally:
        sys.path.pop(0)
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        g = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a], env=env,
                                           capture_output=True, text=True)
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(tmp / 'o.git'))
        g(tmp, 'clone', '-q', str(tmp / 'o.git'), str(tmp / 'w'))
        w = tmp / 'w'
        g(w, 'checkout', '-q', '-B', 'main')
        (w / 'a').write_text('a'); g(w, 'add', '-A'); g(w, 'commit', '-qm', 'a')
        g(w, 'push', '-q', 'origin', 'main')
        first = '2026-10-11-update-vendors-abcde-q7m2x'
        g(w, 'branch', first)
        saved_env = dict(os.environ)
        os.environ.update(env)
        # The session's own declared username must not reach the names
        # this expects (2026-10-16).
        os.environ['PRECEDENT_USER_CONFIG'] = os.devnull
        os.environ.pop('PRECEDENT_GITHUB_USER', None)
        try:
            name, notes = pbn.build(['update', 'vendors'], date='2026-10-11',
                                    tail='abcde', rand='q7m2x',
                                    exists=lambda n: pbn.taken(n, w))
            check('a name only a local branch has is taken: the tool draws new '
                  'random characters in the same place, never a third part',
                  name != first and re.fullmatch(
                      r'2026-10-11-update-vendors-abcde-[a-z0-9]{5}', name)
                  is not None, f'{name} {notes}')
            check('and says why', any('local branch' in n for n in notes), notes)
            free, _ = pbn.build(['other', 'work'], date='2026-10-11', tail='abcde',
                                rand='q7m2x', exists=lambda n: pbn.taken(n, w))
            check('CONTROL: a name nothing has is handed out as it is',
                  free == '2026-10-11-other-work-abcde-q7m2x', free)
        finally:
            os.environ.clear(); os.environ.update(saved_env)


def check_landed_check_names_the_tier_that_ran():
    """After a merge, the line says whether the base moved from the trees,
    and names the check that actually ran.

    2026-10-10, a consuming repository's fast move into main: the merge
    check printed "main MOVED ... It has now had its own full check" when
    main had not moved and only the quick check had run, because "landed as
    checked" needed words only the full tier prints. A session believing it
    may skip the full check it still owes. Planted: a merge whose tree is
    the head's, one where the base moved, and one squash-merged."""
    import tempfile
    name = 'the merge check says whether the base moved and which check ran'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_merge_check as pmc
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1')

        def git(*a):
            return subprocess.run(['git', '-C', str(tmp / 'r'), *a], capture_output=True,
                                  text=True, env=env).stdout.strip()

        subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp / 'r')], env=env)
        (tmp / 'r' / 'a').write_text('1', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'base')
        git('checkout', '-q', '-b', 'pr')
        (tmp / 'r' / 'b').write_text('1', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'the change')
        git('checkout', '-q', 'main')
        git('merge', '-q', '--no-ff', '-m', 'merge, main still', 'pr')
        still = git('rev-parse', 'HEAD')
        git('reset', '-q', '--hard', 'HEAD^1')
        (tmp / 'r' / 'c').write_text('1', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'another window')
        git('merge', '-q', '--no-ff', '-m', 'merge, main moved', 'pr')
        moved = git('rev-parse', 'HEAD')
        squash = git('rev-parse', 'HEAD^1')
        cases.append(('a merge holding the head\'s tree is "as checked"',
                      pmc.same_tree_as_checked(tmp / 'r', still) is True))
        cases.append(('a merge after the base moved is not',
                      pmc.same_tree_as_checked(tmp / 'r', moved) is False))
        cases.append(('a commit with no second parent cannot be told',
                      pmc.same_tree_as_checked(tmp / 'r', squash) is None))
    rc, line = pmc.landed_verdict('main', 7, 'a' * 40, 'basic', 0, 'passed', True)
    cases.append(('a fast move that kept main still: landed as checked, never MOVED',
                  rc == 0 and 'as checked' in line and 'MOVED' not in line))
    cases.append(('...it names the quick check, and says the full check is still owed',
                  'quick check' in line and 'full check' in line
                  and 'own full check' not in line))
    rc, line = pmc.landed_verdict('main', 7, 'a' * 40, 'basic', 0, 'passed', False)
    cases.append(('a base that moved says MOVED and the quick check, not "full"',
                  'MOVED' in line and 'quick check' in line and 'own full check' not in line))
    rc, line = pmc.landed_verdict('staging', 7, 'a' * 40, 'full', 0, 'passed', False)
    cases.append(('a full check on a moved base says so', 'MOVED' in line and 'full check' in line))
    rc, line = pmc.landed_verdict('staging', 7, 'a' * 40, 'full', 0,
                                  'this exact tree already passed', None)
    cases.append(('with no second parent, the recorded pass still reads as checked',
                  'as checked' in line))
    cases.append(('a failure is left to the revert path',
                  pmc.landed_verdict('main', 7, 'a' * 40, 'full', 1, 'x', False) is None))
    rc, line = pmc.landed_verdict('main', 7, 'a' * 40, 'full', 2, 'boom', True)
    cases.append(('could-not-check exits 2 and never says MOVED on a still base',
                  rc == 2 and 'MOVED' not in line and 'boom' in line))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_merge_gate_waits_for_a_current_merge_ref():
    """The merge gate judges GitHub's test merge only once its second parent
    is the pull request's current head.

    2026-09-28, measured: a session pushed a fix to a pull request's head
    and merged at once. The gate judged refs/pull/N/merge as it stood before
    the push -- the old head, still carrying the bug -- refused, and called
    it "the merge GitHub would make". A minute later the merge ref had the
    new head as its second parent and the same merge passed. The GitHub
    head lookup is stubbed; the refs live in a bare origin."""
    import tempfile, io, contextlib
    name = ('the merge gate never judges a test merge of an older head as '
            'the current one')
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_merge_check as pmc
        import github_budget
    finally:
        sys.path.pop(0)
    cases = []
    saved_env = dict(os.environ)
    saved_call, saved_sleep = github_budget.call, getattr(pmc, '_sleep', None)
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1',
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env).stdout.strip()

        origin = tmp / 'o' / 'r.git'
        origin.parent.mkdir()
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        src = tmp / 'src'
        git(tmp, 'init', '-q', '-b', 'main', str(src))
        (src / 'tools').mkdir()
        # The push check this gate runs: fails while BUG is in the tree.
        (src / 'tools' / 'precedent_push_check.py').write_text(
            'import pathlib, sys\n'
            'bug = pathlib.Path("BUG").exists()\n'
            'print("precedent_push_check: FAILED -- BUG is here" if bug '
            'else "precedent_push_check: all passed")\n'
            'sys.exit(1 if bug else 0)\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-q', '-m', 'base')
        base = git(src, 'rev-parse', 'HEAD')
        git(src, 'checkout', '-q', '-b', 'feature')
        (src / 'BUG').write_text('x\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-q', '-m', 'the change, with its bug')
        old = git(src, 'rev-parse', 'HEAD')
        git(src, 'rm', '-q', 'BUG')
        git(src, 'commit', '-q', '-m', 'fix the bug')
        new = git(src, 'rev-parse', 'HEAD')

        def test_merge(head):
            tree = git(src, 'rev-parse', f'{head}^{{tree}}')
            return git(src, 'commit-tree', tree, '-p', base, '-p', head, '-m', 'merge')
        merge_old, merge_new = test_merge(old), test_merge(new)
        git(src, 'push', '-q', str(origin), 'main', f'{new}:refs/heads/feature',
            f'{new}:refs/pull/7/head', f'{merge_old}:refs/pull/7/merge',
            f'{merge_new}:refs/heads/merge-new-keep')
        checkout = tmp / 'checkout'
        git(tmp, 'clone', '-q', str(origin), str(checkout))

        def stub_call(path, *a, **kw):
            return ({'head': {'ref': 'feature', 'sha': new,
                              'repo': {'full_name': 'o/r'}},
                     'base': {'ref': 'main'}}, None)

        def run(catches_up):
            git(src, 'push', '-q', '-f', str(origin), f'{merge_old}:refs/pull/7/merge')
            slept = []

            def stub_sleep(_s):
                slept.append(_s)
                if catches_up and len(slept) == 1:
                    git(src, 'push', '-q', '-f', str(origin),
                        f'{merge_new}:refs/pull/7/merge')
            pmc._sleep = stub_sleep
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = pmc.main(['--owner', 'o', '--repo', 'r', '--number', '7',
                               '--search', str(checkout)])
            return rc, buf.getvalue()

        try:
            os.environ.update({k: env[k] for k in (
                'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM', 'PRECEDENT_USER_CONFIG',
                'PRECEDENT_ALLOW_ANY_AUTHOR')})
            github_budget.call = stub_call
            rc, out = run(catches_up=True)
            cases.append((f'a stale test merge is waited out, and the rebuilt '
                          f'one is judged and passes (exit {rc})',
                          rc == 0 and merge_new[:12] in out
                          and merge_old[:12] not in out))
            rc, out = run(catches_up=False)
            cases.append((f'a test merge that never catches up is not judged; '
                          f'the current head is, and the output says so (exit {rc})',
                          rc == 0 and 'older head' in out and new[:12] in out
                          and merge_old[:12] not in out))
            git(src, 'push', '-q', '-f', str(origin), f'{merge_new}:refs/pull/7/merge')
            slept = []
            pmc._sleep = slept.append
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = pmc.main(['--owner', 'o', '--repo', 'r', '--number', '7',
                               '--search', str(checkout)])
            cases.append(('a current test merge is judged at once, with no wait',
                          rc == 0 and not slept and merge_new[:12] in buf.getvalue()))
        except Exception as e:                                # noqa: BLE001
            cases.append((f'the gate raised {type(e).__name__}: {e}', False))
        finally:
            os.environ.clear()
            os.environ.update(saved_env)
            github_budget.call = saved_call
            if saved_sleep is not None:
                pmc._sleep = saved_sleep
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_data_branches_are_named_for_the_ladder():
    """The engine's long-lived data branches are `data-<what>` in a ladder
    repository and keep their old names everywhere else, and a ladder
    repository's first write copies the old branch to the new name, leaving
    the old one where it was (precedent_data_branches.py).

    WHY. Morgan, 2026-10-11 (strength: decided): "'data-' for permanent
    branches is great and approved (maybe we also rename existing ones?) BUT
    maybe this should be in 'ladder' only, because Alex might not want this
    and we don't want to touch his." The controls are the non-ladder cases:
    nothing there ever gains a data- branch. Once a repository has moved,
    everyone in it follows, so receipts and the lock stay shared. And while
    a window on an older engine holds the old lock, a Promote here waits."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_data_branches as pdb
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    env = _fixture_git_env()
    cases = []
    saved_env = dict(os.environ)
    os.environ.update(env)
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            g = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a],
                                               capture_output=True, text=True)

            def fresh(tag, with_old=True):
                origin, work = td / f'{tag}.git', td / tag
                g(td, 'init', '-q', '--bare', '-b', 'main', str(origin))
                g(td, 'init', '-q', '-b', 'main', str(work))
                g(work, 'remote', 'add', 'origin', str(origin))
                (work / 'f').write_text('x')
                g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base')
                g(work, 'push', '-q', 'origin', 'main')
                if with_old:
                    g(work, 'push', '-q', 'origin',
                      'main:refs/heads/precedent-check-receipts')
                return origin, work

            def heads(origin):
                return set(g(origin, 'for-each-ref', '--format=%(refname:short)',
                             'refs/heads').stdout.split())

            o, w = fresh('plain')
            read = pdb.name(w, pdb.RECEIPTS, ladder=False)[0]
            write = pdb.name_for_write(w, pdb.RECEIPTS, ladder=False)
            cases.append(('CONTROL: not on the ladder, the old name is read and '
                          'written, and no data- branch appears',
                          read == write == 'precedent-check-receipts'
                          and 'data-check-receipts' not in heads(o),
                          f'{read} {write} {heads(o)}'))
            o, w = fresh('plain-empty', with_old=False)
            cases.append(('CONTROL: not on the ladder with nothing there yet, '
                          'the old name',
                          pdb.name_for_write(w, pdb.RECEIPTS, ladder=False)
                          == 'precedent-check-receipts', ''))

            o, w = fresh('ladder')
            old_tip = g(o, 'rev-parse', 'precedent-check-receipts').stdout.strip()
            read = pdb.name(w, pdb.RECEIPTS, ladder=True)[0]
            said = []
            write = pdb.name_for_write(w, pdb.RECEIPTS, ladder=True, say=said.append)
            new_tip = g(o, 'rev-parse', 'data-check-receipts').stdout.strip()
            cases.append(('a ladder repository not moved yet reads the old branch',
                          read == 'precedent-check-receipts', read))
            cases.append(('its first write makes data- at the old tip and says so; '
                          'the old branch stays where it was',
                          write == 'data-check-receipts' and new_tip == old_tip
                          and g(o, 'rev-parse', 'precedent-check-receipts')
                          .stdout.strip() == old_tip
                          and any('made from precedent-check-receipts' in m for m in said),
                          f'{write} {new_tip[:8]} {old_tip[:8]} {said}'))
            # 2026-10-30 very deep check (Morgan, 2026-10-31, assented): an
            # older engine still wrote the receipts' old name on 2026-10-28,
            # so its copy keeps it and offers no delete link.
            cases.append(('the receipts\' old name is kept, never offered for deletion',
                          any('no deletion list offers it' in m for m in said)
                          and not any('left for you to delete' in m for m in said),
                          str(said)))
            o2, w2 = fresh('ladder-lock', with_old=False)
            g(w2, 'push', '-q', 'origin', 'main:refs/heads/precedent-promote-lock')
            said2 = []
            pdb.name_for_write(w2, pdb.LOCK, ladder=True, say=said2.append)
            cases.append(('CONTROL: the lock\'s old name, which no older engine '
                          'needs kept, is still handed over to delete',
                          any('left for you to delete' in m for m in said2), str(said2)))
            cases.append(('once moved, everyone there follows, on the ladder or not',
                          pdb.name(w, pdb.RECEIPTS, ladder=False)[0]
                          == pdb.name_for_write(w, pdb.RECEIPTS, ladder=False)
                          == 'data-check-receipts', ''))
            o, w = fresh('ladder-empty', with_old=False)
            cases.append(('a ladder repository with nothing there yet starts on data-',
                          pdb.name_for_write(w, pdb.RECEIPTS, ladder=True)
                          == 'data-check-receipts', ''))
            cases.append(('every data- branch, and the old names, are records',
                          pdb.is_data_branch('data-leases')
                          and pdb.is_data_branch('precedent-promote-lock')
                          and not pdb.is_data_branch('2026-10-11-data-fix-abcde-q7m2x')
                          and 'data-promote-lock' in pdb.every_name(), ''))

            # The lock: this repository is on data-promote-lock; a window on an
            # older engine holds the old name. A Promote here must wait.
            o, w = fresh('lock', with_old=False)
            g(w, 'push', '-q', 'origin', 'main:refs/heads/data-promote-lock')
            held = g(w, 'commit-tree', '4b825dc642cb6eb9a060e54bf8d69288fbee4904',
                     '-m', 'held by an older window [skip ci]').stdout.strip()
            g(w, 'push', '-q', 'origin', f'{held}:refs/heads/precedent-promote-lock')
            pdb._CACHE.clear()
            state, info = pb._lock_claim(w, say=lambda m: None)
            cases.append(('a fresh hold on the old lock name makes a Promote here wait',
                          state == 'busy' and 'older window' in info, f'{state} {info}'))
            free = g(w, 'commit-tree', '4b825dc642cb6eb9a060e54bf8d69288fbee4904',
                     '-p', held, '-m', 'free [skip ci]').stdout.strip()
            g(w, 'push', '-q', 'origin', f'{free}:refs/heads/precedent-promote-lock')
            state, info = pb._lock_claim(w, say=lambda m: None)
            claimed = g(o, 'log', '-1', '--format=%s', 'data-promote-lock').stdout
            cases.append(('CONTROL: once the old name is free, the claim is taken on '
                          'data-promote-lock, not the old name',
                          state == 'held' and claimed.startswith('held by')
                          and g(o, 'log', '-1', '--format=%s',
                                'precedent-promote-lock').stdout.startswith('free'),
                          f'{state} {info} {claimed}'))
            pb._lock_release(w, info, say=lambda m: None)
            cases.append(('...and released there',
                          g(o, 'log', '-1', '--format=%s', 'data-promote-lock')
                          .stdout.startswith('free'), ''))
    finally:
        os.environ.clear(); os.environ.update(saved_env)
        pdb._CACHE.clear()
    failed = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'data branches are named for the ladder ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_promote_commits_carry_a_session_trailer():
    """A commit the Promote tool writes itself -- the rebuild of generated
    files during a composition -- carries a session trailer the trailer
    check accepts: the session's link, or the explicit no-session form.

    WHY. 2026-10-07, a Debut: main carried a commit staging lacked, the
    composition rebuilt the generated files and committed them with no
    trailer, and the full check refused the Promote's own commit."""
    import re as _re
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    cases = []
    trailer = _re.compile(r'^(?:Session|Claude-Session):\s+(\S.*)$', _re.M)
    saved = pb._this_session_id
    try:
        pb._this_session_id = lambda: '01Fixture'
        t1 = pb._session_trailer()
        cases.append(('with a session: its link, which the check accepts',
                      t1.endswith('session_01Fixture') and bool(trailer.search(t1))))
        pb._this_session_id = lambda: ''
        t2 = pb._session_trailer()
        cases.append(('without one: the explicit no-session form',
                      t2 == 'Session: none available (precedent_branches.py)'
                      and bool(trailer.search(t2))))
    finally:
        pb._this_session_id = saved
        sys.path.pop(0)
    import inspect as _inspect
    cases.append(('the rebuild commit uses it',
                  '_session_trailer()' in _inspect.getsource(pb._commit_rebuilt)))
    bad = [n for n, ok in cases if not ok]
    check(f'a commit the Promote tool writes carries a session trailer '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_promote_marks_other_sessions_commits():
    """A Promote's batch list marks each commit that is not this session's
    work: not on the --work branch, and not carrying this session's
    Claude-Session line.

    WHY. 2026-10-06, a Produce in a shared set carried one session's change
    and another session's Update Vendors, listed alike; auto mode held the
    move until the person approved a commit nobody had named to them."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    env = _fixture_git_env()
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            run = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                            capture_output=True, text=True)
            run('init', '-q', '-b', 'main')
            def commit(name, msg):
                (repo / name).write_text(name, encoding='utf-8')
                run('add', name)
                run('commit', '-qm', msg)
                return run('rev-parse', 'HEAD').stdout.strip()
            mine = '\n\nClaude-Session: https://claude.ai/code/session_01Fixture'
            other = '\n\nClaude-Session: https://claude.ai/code/session_01Other'
            base = commit('base', 'base')
            # Another session Books first; this session's branch is cut after,
            # so it carries that commit -- the case the branch test got wrong.
            commit('o', "another session's, Booked before the branch was cut" + other)
            run('switch', '-qc', 'work')
            commit('a', 'mine, on the work branch' + mine)
            run('switch', '-q', 'main')
            run('merge', '-q', '--no-ff', '-m', 'book work', 'work')
            commit('b', 'mine, Booked from another branch' + mine)
            commit('c', "someone else's, no session line")
            batch = pb._new_commits(repo, base, 'main')
            shown, others = pb.mark_other_work(repo, batch, 'work', sid='01Fixture')
            subj = lambda ls: [l.split(' ', 1)[1] for l in ls]
            cases.append(('four commits in the batch', len(batch) == 4))
            cases.append(("another session's commit is marked even though it is "
                          "on this session's branch",
                          "another session's, Booked before the branch was cut"
                          in subj(others)))
            cases.append(('a commit with no session line is marked',
                          "someone else's, no session line" in subj(others)))
            cases.append(("this session's commits are not, on its branch or off it",
                          len(others) == 2
                          and sum(pb.OTHER_WORK_MARK in l for l in shown) == 2))
            cases.append(('the note names how many and asks for them by name',
                          '2 of these' in pb._other_work_note(others, 'work')
                          and pb._other_work_note([], 'work') == ''))
            shown, others = pb.mark_other_work(repo, batch, 'work', sid='')
            cases.append(('with no session ID nothing is marked, and the note says '
                          'the list was not judged',
                          others is None and shown == batch
                          and 'unknown' in pb._other_work_note(others, 'work')))
    finally:
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'a Promote marks the commits that are not this session\'s work '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_stale_branches_skip_a_reverted_merge():
    """A branch whose pull-request merge main reverted is never offered for
    deletion; once merged again, it is.

    WHY. 2026-10-12: a pull request was merged and reverted within the hour,
    and the revert told its author to fix the work on the branch and merge
    again. Its tip was in main, so the cleanup page offered the branch for
    deletion. Planted: main merges `feat` as #5, then `Revert pull request
    #5` -- not listed; a git-style revert naming the merge commit -- not
    listed; merged again as #6 -- listed. CONTROL: a merged branch nobody
    reverted is listed throughout."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as sb
    cases = []
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        origin, work = td / 'origin.git', td / 'work'

        def g(*a, cwd=None):
            return subprocess.run(['git', '-C', str(cwd or work), *a], env=env,
                                  capture_output=True, text=True)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)],
                       capture_output=True, env=env)
        subprocess.run(['git', 'clone', '-q', str(origin), str(work)],
                       capture_output=True, env=env)
        (work / 'a.txt').write_text('a\n'); g('add', '-A'); g('commit', '-qm', 'a')
        g('push', '-q', 'origin', 'HEAD:main')
        for name in ('feat', 'other'):
            g('checkout', '-q', '-b', name, 'main')
            (work / f'{name}.txt').write_text(name); g('add', '-A')
            g('commit', '-qm', name); g('push', '-q', 'origin', name)
        g('checkout', '-q', 'main')
        g('merge', '-q', '--no-ff', 'other', '-m', 'Merge pull request #4 from o/other')
        g('merge', '-q', '--no-ff', 'feat', '-m', 'Merge pull request #5 from o/feat')
        merge5 = g('rev-parse', 'HEAD').stdout.strip()
        g('revert', '--no-edit', '-m', '1', 'HEAD')
        g('commit', '-q', '--amend', '-m', 'Revert pull request #5: it failed its check')
        g('push', '-q', 'origin', 'HEAD:main'); g('fetch', '-q', 'origin')

        def listed():
            return [b for b, _d in (sb.stale_in(work) or [])]
        cases.append(('a merge main reverted by "Revert pull request #N" is not '
                      'offered', 'feat' not in listed(), listed()))
        cases.append(('CONTROL: a merged branch nobody reverted is offered',
                      'other' in listed(), listed()))
        g('reset', '-q', '--hard', merge5)
        g('revert', '--no-edit', '-m', '1', 'HEAD')
        g('push', '-q', '-f', 'origin', 'HEAD:main'); g('fetch', '-q', 'origin')
        cases.append(('...nor one reverted by git\'s "This reverts commit <merge>"',
                      'feat' not in listed(), listed()))
        g('checkout', '-q', 'feat'); g('merge', '-q', 'origin/main', '-m', 'take main')
        (work / 'feat.txt').write_text('feat, fixed'); g('add', '-A')
        g('commit', '-qm', 'fix')
        g('push', '-q', 'origin', 'feat'); g('checkout', '-q', 'main')
        g('merge', '-q', '--no-ff', 'feat', '-m', 'Merge pull request #6 from o/feat')
        g('push', '-q', 'origin', 'HEAD:main'); g('fetch', '-q', 'origin')
        cases.append(('merged again, it is offered', 'feat' in listed(), listed()))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the cleanup page never offers a branch whose merge was reverted '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_branch_cleanup_page_script_parses():
    """The branch cleanup page's script parses, and the page reads its rows
    from its own database: no row, tick or self-save is written into it.

    WHY (2026-10-27). Moving the page to its database, the live page read
    through for the last time had `repository's` inside a single-quoted
    string in its script: a syntax error, so nothing on the page ran -- no
    ticks, no delete-all buttons, no Open next -- and nothing had noticed.
    Planted: the page's script, under node when node is installed, must
    parse; a copy with the same apostrophe unescaped must not (the CONTROL
    that the check can fail)."""
    import shutil
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as _sb
    name = 'the branch cleanup page\'s script parses and reads its database'
    page = _sb.render_page()
    m = re.search(r'<script>(.*)</script>', page, re.S)
    js = m.group(1) if m else ''
    cases = [('the page carries a script', bool(js), ''),
             ('it reads its rows from the database, live',
              "window.claude.use('db')" in js and "collection('repos').onSnapshot" in js, ''),
             ('it writes only its own ticks and clicks',
              "db.doc('ticks/'" in js and "db.doc('clicks/'" in js
              and "doc('repos/" not in js, ''),
             ('nothing republishes the page', "use('artifact')" not in js
              and 'publish(' not in js, ''),
             ('the page holds no rows of its own', 'data-k=' not in page
              and 'branch-data' not in page, ''),
             ('the rows a session writes are editors\' only',
              {'path': _sb.DB_REPOS, 'write': 'admin'}
              in _sb.PAGE_CAPABILITIES['db']['rules'], _sb.PAGE_CAPABILITIES)]
    node = shutil.which('node')
    if node and js:
        with tempfile.TemporaryDirectory() as td:
            good, bad = pathlib.Path(td) / 'page.js', pathlib.Path(td) / 'bad.js'
            good.write_text(js, encoding='utf-8')
            bad.write_text(js.replace("repository\\'s", "repository's"), encoding='utf-8')
            r = subprocess.run([node, '--check', str(good)], capture_output=True, text=True,
                               timeout=60)
            cases.append(('node parses the page\'s script', r.returncode == 0,
                          (r.stderr or '')[:300]))
            r = subprocess.run([node, '--check', str(bad)], capture_output=True, text=True,
                               timeout=60)
            cases.append(('CONTROL: the apostrophe the live page carried does not parse',
                          r.returncode != 0, ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))


def check_branch_cleanup_refresh_writes_only_what_it_checked():
    """A refresh of the branch cleanup page writes a document for each
    repository this session checked and leaves every other one alone; a
    write over a document is pinned to the version it was listed at; a page
    from before the database seeds it.

    WHY. 2026-10-12: a session with fewer repositories open than the last
    one published over the page and wiped the rows the wider session had
    listed, so the page was merged on every refresh; and that merge needed
    a read of the whole page, about 98,000 tokens on 2026-10-27. With one
    document a repository nothing is merged: a repository this run did not
    check is simply not written. Planted: a listing holding A and B; a run
    that checked A (now empty) and C. A is rewritten empty, C created, B
    untouched; a run that checked a repository with nothing in it, not in
    the listing, writes nothing for it; a listed document without a version
    is refused, nothing written; --versions takes pairs or the listing's
    own lines; a pre-database page seeds the repositories this run did not
    check, less its ticked rows and any branch the engine keeps; --html now
    refuses and writes nothing."""
    import contextlib
    import datetime
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as _sb
    cases = []
    now = datetime.datetime(2026, 10, 27, 15, 0, tzinfo=datetime.timezone.utc)
    then = '2026-10-20T10:00:00+00:00'
    listing = {_sb.doc_id('o', 'A'): (3, {'owner': 'o', 'repo': 'A', 'checked': then,
                                          'branches': [['a-done', '2026-10-01']]}),
               _sb.doc_id('o', 'B'): (5, {'owner': 'o', 'repo': 'B', 'checked': then,
                                          'branches': [['b-done', '2026-10-02']]})}
    docs = _sb.build_docs([('o', 'C', [('c-done', '2026-10-04')])], [],
                          [('o', 'a'), ('o', 'C'), ('o', 'D')], [], [], listing, now=now)
    cases.append(('A is rewritten (case aside), C created, B and the empty D not written',
                  sorted(docs) == [_sb.doc_id('o', 'A'), _sb.doc_id('o', 'C')], sorted(docs)))
    cases.append(('...A with nothing left on it, C with its row, both dated now',
                  docs[_sb.doc_id('o', 'A')]['branches'] == []
                  and docs[_sb.doc_id('o', 'C')]['branches'] == [['c-done', '2026-10-04']]
                  and docs[_sb.doc_id('o', 'C')]['checked'].startswith('2026-10-27'), ''))
    with tempfile.TemporaryDirectory() as td:
        writes = _sb.db_writes(docs, listing, pathlib.Path(td))
        pins = {w['doc_id']: w.get('if_version') for w in writes}
        cases.append(('the write over A is pinned to its listed version; C is a create',
                      pins == {_sb.doc_id('o', 'A'): 3, _sb.doc_id('o', 'C'): None}, pins))
        cases.append(('each write names a file holding its document',
                      all(json.loads(pathlib.Path(w['file_path']).read_text())['repo']
                          for w in writes), ''))
    cases.append(('--versions takes pairs and the listing\'s own lines',
                  _sb.parse_versions('o--a=3 - "o--b"  772 bytes  version 5  "/x/o--b.json"')
                  == {'o--a': 3, 'o--b': 5}, ''))
    cases.append(('a document id keeps only what an id may hold',
                  _sb.doc_id('Own er', 'Re/po') == 'own_er--re_po', _sb.doc_id('Own er', 'Re/po')))
    legacy = ('<script type="application/json" id="branch-data">' + json.dumps({
        'format': 3, 'built': then,
        'done': {'B/b-done': '2026-10-21T00:00:00Z'},
        'repos': [{'owner': 'o', 'repo': 'B', 'checked': then,
                   'branches': [['b-done', '2026-10-02'], ['b-kept', '2026-10-03'],
                                ['precedent-promote-lock', '2026-10-01']]},
                  {'owner': 'o', 'repo': 'A', 'checked': then,
                   'branches': [['a-done', '2026-10-01']]}],
        'waiting': [{'owner': 'o', 'repo': 'W', 'checked': then, 'staging': 'staging',
                     'commits': 2, 'oldest': '2026-10-10'}],
        'cleanup': [], 'clicked': {}}) + '</script>')
    seeded = _sb.build_docs([], [], [('o', 'A')], [], [], {}, now=now, seed_text=legacy)
    b = seeded.get(_sb.doc_id('o', 'B'), {})
    cases.append(('a pre-database page seeds B under its own date, less its ticked row '
                  'and the engine\'s branch',
                  b.get('branches') == [['b-kept', '2026-10-03']]
                  and b.get('checked') == then, b.get('branches')))
    cases.append(('...and its waiting row for a repository with nothing to delete',
                  (seeded.get(_sb.doc_id('o', 'W')) or {}).get('waiting')
                  == {'staging': 'staging', 'commits': 2, 'oldest': '2026-10-10'}, ''))
    cases.append(('CONTROL: a repository this run checked is not seeded from it',
                  _sb.doc_id('o', 'A') not in seeded, sorted(seeded)))
    real_collect, real_waiting, real_person = _sb.collect, _sb.collect_waiting, _sb._person
    real_github = _sb._github
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / 'repos').mkdir()
        (td / 'repos' / 'o--c.json').write_text(json.dumps(
            {'owner': 'o', 'repo': 'C', 'checked': then, 'branches': []}))

        def collect(fetch=False, seen=None):
            if seen is not None:
                seen.extend([('o', 'C')])
            return [('o', 'C', [('c-done', '2026-10-04')])], []

        def run(*args):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = _sb.main(list(args))
            return rc, buf.getvalue()
        try:
            _sb.collect = collect
            _sb.collect_waiting = lambda fetch=False, seen=None: []
            _sb._person = lambda: {'branch_cleanup_page': 'https://claude.ai/artifact/x'}
            _sb._github = lambda: None
            rc, said = run('--db-docs', str(td))
            cases.append(('a listed document with no version is refused, nothing written',
                          rc == 2 and not (td / 'out').exists()
                          and 'Nothing written' in said, said))
            rc, said = run('--db-docs', str(td), '--versions', 'o--c=7')
            writes = json.loads(said.strip().splitlines()[-1]) if rc == 0 else []
            cases.append(('with its version, the batch line pins it',
                          rc == 0 and [w.get('if_version') for w in writes] == [7], failure_detail(said, 300)))
            rc, said = run('--html', str(td / 'page.html'))
            cases.append(('--html refuses and points at the database route',
                          rc == 2 and not (td / 'page.html').exists()
                          and '--db-docs' in said, said))
        finally:
            _sb.collect, _sb.collect_waiting, _sb._person = real_collect, real_waiting, real_person
            _sb._github = real_github
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'a branch-page refresh writes only what it checked ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_branch_cleanup_open_next_is_a_real_link():
    """A repository's open-in-tabs control is a real link to its first
    branch, and the page's script never calls window.open.

    WHY (Morgan, 2026-10-19: the button to open them all in new tabs
    "didn't work"). It called window.open once per branch, which inside an
    artifact returns nothing for almost every viewer, and a browser opens
    one tab per click anyway; it opened nothing and blamed pop-ups. A real
    link always opens, so it is one, moved to the next branch per click."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_stale_branches as _sb
    finally:
        sys.path.pop(0)
    two = _sb.repo_doc('o', 'r', [('a/one', '2026-10-01'), ('b-two', '2026-10-02')],
                       '2026-10-27T00:00:00+00:00')['section']
    one = _sb.repo_doc('o', 'r', [('a/one', '2026-10-01')],
                       '2026-10-27T00:00:00+00:00')['section']
    tag = two.split('class="open-next"', 1)[-1].split('>', 1)[0] \
        if 'class="open-next"' in two else ''
    cases = [
        ('two branches carry the link', bool(tag)),
        ('it points at the first branch, filtered', 'query=a%2Fone' in two.split(
            'class="open-next"', 1)[0].rsplit('<a', 1)[-1] + tag, tag),
        ('it opens in a new tab', 'target="_blank"' in tag, tag),
        ('one branch has no link', 'class="open-next"' not in one),
        ('no script calls window.open', 'window.open(' not in _sb._PAGE),
    ]
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the cleanup page opens the next branch with a real link '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + str(d) + ')' if d else ''}" for n, d in bad))


def check_branch_cleanup_page_never_offers_main_and_marks_moved_engine_names():
    """The page never offers main, staging or a live data- branch, from any
    path, and an engine branch's old name is offered only from this run's
    own check, marked as the moved name it is; its runtime version is left
    where it was published.

    WHY (2026-10-17, from two consuming repos' sessions). The page listed
    precedent-promote-lock and precedent-check-receipts as deletable, and
    its intro said the engine's own branches are never listed. Both were
    old names whose data- copies held their whole history -- listed on
    purpose since 2026-10-13 -- but nothing on the page said so, and two
    sessions reported them as engine branches offered by mistake. A
    republish reported an older runtime version, and nothing said whether
    to move it.

    Planted through repo_doc: a fresh repository carrying main, a live
    data- branch, a moved old name and an ordinary branch; a carried one
    whose saved rows hold an old engine name and an ordinary branch."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_stale_branches as _sb
    finally:
        sys.path.pop(0)
    cases = []
    page = _sb.repo_doc('o', 'fresh', [('main', '2026-10-01'),
                                       ('data-promote-lock', '2026-10-02'),
                                       ('precedent-promote-lock', '2026-10-03'),
                                       ('feat-a', '2026-10-04')],
                        '2026-10-27T00:00:00+00:00')['section'] + _sb.repo_doc(
        'o', 'saved', [('precedent-check-receipts', '2026-10-05'), ('feat-b', '2026-10-06')],
        '2026-10-16T12:00:00+00:00', fresh=False)['section']
    offered = set(re.findall(r'data-k="([^"]+)"', page))
    cases.append(('main is never offered', 'fresh/main' not in offered, sorted(offered)))
    cases.append(('a live data- branch is never offered',
                  'fresh/data-promote-lock' not in offered))
    cases.append(('an ordinary branch is, fresh or carried',
                  {'fresh/feat-a', 'saved/feat-b'} <= offered))
    row = page.split('fresh/precedent-promote-lock', 1)[-1].split('</li>', 1)[0]
    cases.append(('a moved old name from this run\'s own check is offered, marked '
                  'as the data- branch\'s old name',
                  'fresh/precedent-promote-lock' in offered
                  and 'data-promote-lock' in row and 'Old name of' in row,
                  row[:200]))
    cases.append(('an old engine name carried from a saved page is not offered',
                  'saved/precedent-check-receipts' not in offered))
    # 2026-10-20 (Morgan: "don't [explain], just give it to me and say
    # nothing else"): the page is the list, with no paragraphs about it.
    cases.append(('the page carries no explanatory intro',
                  'class="lede"' not in _sb._PAGE and 'Checking a branch off' not in _sb._PAGE))
    cases.append(('the count is of what is offered (3)', len(offered) == 3, sorted(offered)))
    cases.append(('one list of engine branch names, from the data-branch module',
                  getattr(_sb, 'ENGINE_BRANCHES', frozenset()) >= {
                      'precedent-promote-lock', 'precedent-check-receipts'}
                  and getattr(_sb, 'ENGINE_BRANCHES', frozenset()) <= _sb.NEVER))
    src = (ROOT / 'tools' / 'precedent_stale_branches.py').read_text(encoding='utf-8')
    cases.append(('the publish line says to leave the runtime version as it is',
                  'omit `contract`' in getattr(_sb, 'PAGE_RUNTIME_LINE', '')
                  and '+ PAGE_RUNTIME_LINE' in src))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the cleanup page never offers main and marks moved engine names '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + str(d) + ')' if d else ''}" for n, d in bad))


def check_branch_cleanup_page_lists_staging_waiting_to_go_live():
    """The branch-cleanup page lists each repository whose staging carries a
    change main lacks, and merges that list across sessions the way it
    merges branches.

    WHY. 2026-10-16, Morgan retired chief-of-staff, whose Promotion Reviews
    said on request which repositories had staging waiting for main; the
    check moved onto this page, which every closing session refreshes.
    Planted: a real repository whose staging is ahead of main by one change
    (listed), one whose staging only merged main back in (level, not
    listed), one with no staging (no row); a saved page whose waiting row
    for a repository this run did not check is left alone, and one for a
    repository this run checked and found level is rewritten without it; a
    pre-database page with branches gone but a waiting row still seeds it."""
    import datetime
    import subprocess as _sp
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as _sb
    cases = []

    def git(cwd, *a):
        return _sp.run(['git', '-C', str(cwd), *a], capture_output=True, text=True,
                       env={**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                            'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'})
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        origin, work = td / 'origin.git', td / 'work'
        git(td, 'init', '-q', '--bare', str(origin))
        git(td, 'init', '-q', '-b', 'main', str(work))
        (work / 'a.txt').write_text('one\n')
        git(work, 'add', '.'); git(work, 'commit', '-qm', 'one')
        git(work, 'remote', 'add', 'origin', str(origin))
        git(work, 'push', '-q', 'origin', 'main')
        cases.append(('no staging tier, no row',
                      _sb.waiting_in(work) is None, _sb.waiting_in(work)))
        git(work, 'switch', '-qc', 'staging')
        (work / 'a.txt').write_text('two\n')
        git(work, 'commit', '-qam', 'two')
        git(work, 'push', '-q', 'origin', 'staging')
        git(work, 'fetch', '-q', 'origin')
        got = _sb.waiting_in(work)
        cases.append(('staging ahead of main by one change is waiting',
                      got is not None and got[0] == 'staging' and got[1] == 1, got))
        git(work, 'switch', '-q', 'main')
        git(work, 'merge', '-q', '--ff-only', 'staging')
        (work / 'b.txt').write_text('fix\n')
        git(work, 'add', '.'); git(work, 'commit', '-qm', 'fix on main')
        git(work, 'push', '-q', 'origin', 'main')
        git(work, 'switch', '-q', 'staging')
        git(work, 'merge', '-q', '--no-ff', '-m', 'main back in', 'main')
        git(work, 'push', '-q', 'origin', 'staging')
        git(work, 'fetch', '-q', 'origin')
        cases.append(('CONTROL: a staging that only merged main back in is level',
                      _sb.waiting_in(work) is None, _sb.waiting_in(work)))
    then = datetime.datetime(2026, 10, 14, 12, 0, tzinfo=datetime.timezone.utc)
    now = then + datetime.timedelta(days=2)
    listing = {_sb.doc_id('o', 'Kept'): (2, {'owner': 'o', 'repo': 'Kept',
                                             'checked': then.isoformat(), 'branches': [],
                                             'waiting': {'staging': 'staging', 'commits': 2,
                                                         'oldest': '2026-10-10'}}),
               _sb.doc_id('o', 'Level'): (4, {'owner': 'o', 'repo': 'Level',
                                              'checked': then.isoformat(), 'branches': [],
                                              'waiting': {'staging': 'staging', 'commits': 1,
                                                          'oldest': '2026-10-12'}})}
    docs = _sb.build_docs([], [('o', 'New', 'staging', 3, '2026-10-15')], [],
                          [('o', 'level'), ('o', 'New')], [], listing, now=now,
                          tz='America/Argentina/Buenos_Aires')
    cases.append(('a repository this run checked and found level is rewritten with no '
                  'row; New gets its row; Kept, not checked, is left alone',
                  sorted(docs) == [_sb.doc_id('o', 'Level'), _sb.doc_id('o', 'New')]
                  and docs[_sb.doc_id('o', 'Level')]['waiting'] is None
                  and docs[_sb.doc_id('o', 'New')]['waiting']['commits'] == 3, sorted(docs)))
    li = docs[_sb.doc_id('o', 'New')]['waiting_li']
    cases.append(('the row links GitHub\'s comparison and counts the commits',
                  'github.com/o/New/compare/main...staging' in li and '3 commits' in li, li))
    cases.append(('the page heads the rows Waiting to go live and dates one checked '
                  'before the newest', 'Waiting to go live' in _sb._PAGE
                  and 'r.checked!==newest.checked' in _sb._PAGE, ''))
    old = ('<script type="application/json" id="branch-data">' + json.dumps({
        'format': 2, 'repos': [], 'waiting': [
            {'owner': 'o', 'repo': 'Kept', 'checked': then.isoformat(), 'staging': 'staging',
             'commits': 2, 'oldest': '2026-10-10'}]}) + '</script>')
    cases.append(('a pre-database page with no branches but a waiting row still seeds it',
                  _sb.is_page(old) and (_sb.build_docs([], [], [], [], [], {}, now=now,
                                                       seed_text=old)
                                        .get(_sb.doc_id('o', 'Kept')) or {}).get('waiting')
                  == {'staging': 'staging', 'commits': 2, 'oldest': '2026-10-10'}, ''))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the branch-cleanup page lists staging waiting to go live ({len(cases)} '
          f'stated cases)', not bad, '; '.join(bad))


def check_branch_cleanup_page_is_one_page_updated_in_place():
    """The branch-cleanup page says when it was built, in the person's zone;
    its ticks belong to that build; and the person's saved page address is
    read from their identity.json and printed for the session to publish to.

    WHY. 2026-10-11, Morgan: one pinned cleanup page that every closing
    session updates, instead of a new link per session. Between closes the
    page shows the last list, so it must say how old that is; and a refreshed
    list must start unticked, or a branch ticked but never deleted would
    hide. Planted: a declared zone names its city; an unreadable one falls
    back to UTC; two builds carry two tick keys; an identity.json with the
    address yields it, one without yields nothing."""
    import datetime
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as _sb
    import precedent_identity as _pid
    cases = []
    at = datetime.datetime(2026, 10, 11, 18, 5, tzinfo=datetime.timezone.utc)
    line = _sb.built_line(at, 'America/Argentina/Buenos_Aires')
    cases.append(('a declared zone names its city', line ==
                  'Refreshed 11 Oct 2026, 15:05 Buenos Aires time', line))
    line = _sb.built_line(at, 'Not/A_Zone')
    cases.append(('CONTROL: an unreadable zone falls back to UTC',
                  line == 'Refreshed 11 Oct 2026, 18:05 UTC', line))
    doc = _sb.repo_doc('o', 'r', [('old-branch', '2026-10-01')], at.isoformat())
    cases.append(('a repository carries when it was checked, and the page heads '
                  'itself Refreshed from the newest',
                  doc['checked_text'] == 'Checked 11 Oct 2026, 18:05 UTC.'
                  and "replace(/^Checked /,'Refreshed ')" in _sb._PAGE, doc['checked_text']))
    cases.append(('a tick counts only for the check it was made on',
                  't.built===r.checked' in _sb._PAGE
                  and "set({built:r.checked" in _sb._PAGE, ''))
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        ident = {'name': 'P', 'email': 'p@example.com',
                 'branch_cleanup_page': 'https://claude.ai/code/artifact/x'}
        (td / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')
        saved = os.environ.pop('PRECEDENT_COMMIT_EMAIL', None)
        try:
            got = _sb.saved_page(_pid.declared_identity(td, user_config=td / 'none'))
            cases.append(('the saved address is read from identity.json',
                          got == ident['branch_cleanup_page'], got))
            del ident['branch_cleanup_page']
            (td / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')
            got = _sb.saved_page(_pid.declared_identity(td, user_config=td / 'none'))
            cases.append(('CONTROL: no address saved, none given', got == '', got))
        finally:
            if saved is not None:
                os.environ['PRECEDENT_COMMIT_EMAIL'] = saved
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the branch-cleanup page is one page updated in place ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_engine_tools_allowed_and_none_asks():
    """With the settings template as shipped, Claude Code lets every engine
    tool run, the ones that land, produce, merge and update other
    repositories included, and asks the person before none of them. From
    2026-10-17 to 2026-10-18 the template's permissions.ask made those stop
    for the person's click every time (Morgan, 2026-10-18: "I urgently need
    a fix so you stop asking me so much"). Matching follows Claude Code's
    documented rules (code.claude.com/docs/en/permissions, read
    2026-10-17): deny, then ask, then allow, the first match deciding; a
    `*` matches any text, spaces included. A tool added later needs no
    settings change. Fails on the 2026-10-17 template: --land asked."""
    import re as _re
    name = 'every engine tool runs, and none asks'
    tmpl = ROOT / 'templates' / 'harness' / 'claude-code' / 'settings.json'
    if not tmpl.is_file():
        not_applicable(name, 'no Claude Code settings template here')
        return
    perms = json.loads(tmpl.read_text(encoding='utf-8')).get('permissions') or {}

    def matches(rule, command):
        m = _re.fullmatch(r'Bash\((.*)\)', rule)
        if not m:
            return False
        pat = '.*'.join(_re.escape(p) for p in m.group(1).split('*'))
        return _re.fullmatch(pat, command) is not None

    def decide(command):
        for key in ('deny', 'ask', 'allow'):
            if any(matches(r, command) for r in perms.get(key) or []):
                return key
        return 'unlisted'
    want = [
        'python3 tools/precedent_brand_new_tool.py --any args',
        'python3 tools/precedent_show.py act',
        'python3 tools/precedent_check.py --full-sweep',
        'python3 tools/precedent_branches.py --landing',
        'python3 tools/precedent_branches.py --run-tests',
        'python3 tools/precedent_branches.py --land',
        'python3 tools/precedent_branches.py --land 2026-10-17-x-y',
        'python3 tools/precedent_branches.py --promote --to main --work b',
        'python3 tools/precedent_update.py --repo .',
        'python3 tools/precedent_update_all.py --list',
        'python3 tools/precedent_vendor_engine.py refresh --from x',
        'python3 tools/precedent_local_edits.py send',
        'python3 tools/precedent_merge_check.py --pr 1',
        'python3 tools/doc_lint.py README.md',
    ]
    cases = [(f'{cmd!r} -> allow', decide(cmd) == 'allow', decide(cmd)) for cmd in want]
    cases.append(('the template asks before nothing', not perms.get('ask'),
                  str(perms.get('ask'))[:200]))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (got ' + d + ')' if d else ''}" for n, d in bad))


def check_update_merge_lines_carry_the_full_head():
    """Every line that tells a session how to merge -- Update Vendors' DONE,
    Promote's merge lines, the runbook's step 12 -- says the merge tool takes
    the full 40-character head commit or none.

    WHY. 2026-10-08, a consumer: the session merged Update Vendors' own pull
    request with a 7-character expected head SHA, GitHub refused it, and the
    failed merge left auto mode refusing even read-only commands until the
    person spoke (gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge).

    Negative control, measured 2026-10-08: before the fix DONE named no head
    at all, _at_head gave only the bare SHA, and the runbook and gotcha said
    nothing of a short SHA -- every case below failed but the first."""
    import contextlib, io
    pu, _pve, _pr = _update_tools()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    sha = 'b' * 40
    cases = [('Promote\'s merge line carries all 40 characters',
              sha in pb._at_head(sha))]
    cases.append(('...and says the merge tool takes all 40 or none',
                  '40' in pb._at_head(sha) and 'or no expected head' in pb._at_head(sha)))
    for asks in ([], [('q', 'a question')]):
        rep = pu.Report()
        rep.asks = list(asks)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rep.close()
        out = buf.getvalue().split('DONE', 1)[-1]
        cases.append((f'DONE{" with a question" if asks else ""} says to merge '
                      f'with the full 40-character head, and how to read it',
                      rc == pu.DONE and '40-character' in out
                      and 'git rev-parse HEAD' in out and 'git ls-remote' in out,
                      failure_detail(out, 500)))
    runbook = (ROOT / 'practices' / 'vendor-update-runbook.md').read_text(encoding='utf-8')
    step12 = runbook.split('12. **Publish it', 1)[-1].split('## Detail', 1)[0]
    cases.append(('the runbook\'s step 12 says the merge needs the full '
                  '40-character head or none',
                  'full 40-character head commit, or none' in step12))
    gotcha = (ROOT / 'gotchas' /
              'gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md'
              ).read_text(encoding='utf-8')
    cases.append(('the gotcha records that a failed merge starts the spiral too',
                  '7-character' in gotcha and 'a merge that fails' in gotcha))
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'every merge instruction carries the full head commit '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_landing_waits_for_a_missing_ladder_set():
    """A brought set that is not on disk yet does not read as "off the
    ladder" (2026-10-30 very deep check: `precedent_branches.py --landing`
    said main in a session whose person brings the ladder set, before the set
    was cloned, and staging after -- the wrong answer being the one that
    skips staging).

    Fixture world, in a repository whose precedent.json declares staging:
      1. the brought set is missing: --landing says staging, and why says the
         ladder cannot be read and names the set; the ladder's own --status
         says so too; the session check's landing row is not a pass;
      2. control: the brought set is on disk and provides nothing -- main,
         as for anyone off the ladder;
      3. the brought set is on disk and provides the ladder -- staging;
      4. PRECEDENT_NO_LADDERS with the set missing -- main, never a guess."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='landing-missing-set-'))
    cases = []
    try:
        home = tmp / 'home'
        ind = home / 'precedent-individual'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps({
            'name': 'precedent-individual', 'level': 'individual',
            'brings': [{'name': 'fixture-ladder',
                        'repo_url': 'https://github.com/example/fixture-ladder'}]}),
            encoding='utf-8')
        cfg = tmp / 'cfg.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(ind)}}), encoding='utf-8')
        repo = tmp / 'repo'
        repo.mkdir()
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'sources': [],
            'base_branch': 'staging', 'landing_branch': 'staging'}),
            encoding='utf-8')
        import precedent_branches as pb
        import precedent_ladder as pl
        import precedent_session_check as psc

        def landing(**extra):
            saved = {k: os.environ.get(k) for k in (
                'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_NO_LADDERS',
                'PRECEDENT_USER_CONFIG')}
            try:              # practice: fixture-owns-its-state
                for k in saved:
                    os.environ.pop(k, None)
                os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
                os.environ.update(extra)
                branch, why = pb.landing_branch(repo, user_config=str(cfg))
                status = pl.status_sentence(repo, user_config=str(cfg))
                old_root, psc.ROOT = psc.ROOT, repo
                try:
                    row = psc._landing_row()
                finally:
                    psc.ROOT = old_root
                return branch, why, status, row
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

        out, why, status, row = landing()
        cases.append(('the brought set is missing: staging, and why names the set and '
                      'says the ladder cannot be read',
                      out == 'staging' and 'cannot be read' in why
                      and 'fixture-ladder' in why, f'{out!r} {why!r}'))
        cases.append(('the ladder\'s --status says it cannot be read, naming the set',
                      'cannot be read' in status and 'fixture-ladder' in status, status))
        cases.append(('the session check\'s landing row is not a pass while it is a guess',
                      row[1] is None, repr(row)))
        out, why, _st, _row = landing(PRECEDENT_NO_LADDERS='1')
        cases.append(('PRECEDENT_NO_LADDERS with the set missing: main, never a guess',
                      out == 'main', f'{out!r} {why!r}'))
        brought = home / 'fixture-ladder'
        (brought / 'practices').mkdir(parents=True)
        (brought / 'precedent-source.json').write_text(json.dumps({
            'name': 'fixture-ladder', 'level': 'shared', 'visibility': 'public',
            'subject': 'a fixture', 'code': []}), encoding='utf-8')
        out, why, _st, row = landing()
        cases.append(('control: on disk and providing nothing, main, as for anyone off '
                      'the ladder, and the row is a pass',
                      out == 'main' and 'cannot be read' not in why and row[1] is True,
                      f'{out!r} {why!r} {row!r}'))
        man = json.loads((brought / 'precedent-source.json').read_text(encoding='utf-8'))
        man['provides'] = ['ladder']
        (brought / 'precedent-source.json').write_text(json.dumps(man), encoding='utf-8')
        out, why, _st, _row = landing()
        cases.append(('on disk and providing the ladder: staging, from the repository',
                      out == 'staging' and 'cannot be read' not in why,
                      f'{out!r} {why!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [c for c in cases if not c[1]]
    check(f'a brought set not on disk yet leaves the landing branch on staging, '
          f'never a guess of main ({len(cases)} stated cases)',
          not failed, '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_a_landing_names_the_checks_it_reaches():
    """After a landing on staging, the land tool prints the command that
    runs, in the background, the harness checks that landing reaches --
    measured from the tip it landed on (PRECEDENT_HARNESS_SINCE), not from
    the ledger's commit -- and prints nothing where there is no harness.

    WHY. Morgan, 2026-10-29 (strength: decided): "Let's have the test of
    only what's relevant (what you built for alex) run upon each staging".
    That day's Produce turned main red on five tests left stale by landings
    that each reached them."""
    import tempfile, importlib.util
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    cases = []
    line = pb.reached_checks_next(ROOT, 'abc123', 'my-branch')
    cases.append(('the line names the since-commit, --as-ci and a reason',
                  'PRECEDENT_HARNESS_SINCE=abc123 python3 tools/verify_harness.py --as-ci'
                  in line and '--because "landing my-branch on staging' in line
                  and 'IN THE BACKGROUND' in line, line[:200]))
    cases.append(('no since-commit, no line', pb.reached_checks_next(ROOT, '', 'b') == '', ''))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-reached-next-'))
    try:
        (tmp / 'tools').mkdir()
        cases.append(('a repository without the harness gets no line',
                      pb.reached_checks_next(tmp, 'abc123', 'b') == '', ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    spec = importlib.util.spec_from_file_location(
        '_hr_since', ROOT / 'tools' / 'harness_reach.py')
    hr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hr)
    seen = []
    hr.load_ledger = lambda fetch=True: {'commit': 'ledgercommit', 'checks': {}}
    hr.select = lambda ledger, base, head, names, root=None: (
        seen.append(base) or (set(names[:1]), {}, None))
    saved = os.environ.pop(hr.SINCE_ENV, None), os.environ.pop('PRECEDENT_HARNESS_FULL', None)
    try:
        _sel, acc = hr.plan(['check_x', 'check_y'])
        os.environ[hr.SINCE_ENV] = 'landedontip'
        _sel, acc2 = hr.plan(['check_x', 'check_y'])
    finally:
        os.environ.pop(hr.SINCE_ENV, None)
        if saved[0] is not None:
            os.environ[hr.SINCE_ENV] = saved[0]
        if saved[1] is not None:
            os.environ['PRECEDENT_HARNESS_FULL'] = saved[1]
    cases.append(('unset, the plan measures from the ledger commit',
                  seen[:1] == ['ledgercommit'] and 'since ledgercommi' in acc, f'{seen} {acc}'))
    cases.append(('set, it measures from the landed-on tip',
                  seen[1:2] == ['landedontip'] and 'since landedontip' in acc2, f'{seen} {acc2}'))
    sys.path.pop(0)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a landing names the checks it reaches ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_upstream_review_only_for_a_code_owner_on_the_ladder():
    """A set's step_review (precedent_resolve.load_set_tool, 2026-10-17):
    the engine finds the tool a set names in its precedent-source.json, and
    a stage writes the lines the tool hands back into the commit it lands.
    Made-up set and tool; the real review, and who sees it, are tested in
    the set that ships it.

    - a set that names a step_review: the stage shows its report and its
      trailer line goes into the landing commit;
    - the tool answers None (it does not apply to this person): nothing is
      shown and the commit is left untouched;
    - no set names one, or the named file is not there: nothing, no error;
    - a named path outside tools/: never loaded."""
    import tempfile
    import precedent_branches as pb
    import precedent_resolve as pr
    cases = []
    tool = (
        'TRAILER = "Zz-seen:"\n'
        'import os\n'
        'def prepare(root, stage, text="", extra=(), rev_range=None):\n'
        '    if os.environ.get("ZZ_OFF"):\n'
        '        return None, None\n'
        '    return [("abc", "WARN: one thing")], []\n'
        'def trailer_lines(items):\n'
        '    return [f"Zz-seen: {fp} {t}" for fp, t in items]\n'
        'def report(stage, new, old, recording):\n'
        '    return [f"ZZ REVIEW ({stage}): {len(new)}", recording or "none"]\n')

    def head_msg(wt):
        return subprocess.run(['git', '-C', str(wt), 'log', '-1', '--format=%B'],
                              capture_output=True, text=True).stdout

    saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
    with tempfile.TemporaryDirectory() as td:
        wt = pathlib.Path(td) / 'repo'
        wt.mkdir()
        os.environ['PRECEDENT_USER_CONFIG'] = str(pathlib.Path(td) / 'no-config.json')
        try:
            fixture_git(wt, 'init', '-q', '-b', 'main')
            fixture_git(wt, 'config', 'user.email', 'h@example.com')
            fixture_git(wt, 'config', 'user.name', 'H')
            fixture_git(wt, 'commit', '-q', '--allow-empty', '-m', 'base')
            base = subprocess.run(['git', '-C', str(wt), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True).stdout.strip()
            fixture_git(wt, 'commit', '-q', '--allow-empty', '-m', 'Land x')
            lines, written = pb._upstream_review(wt, wt, 'booked', 'out', f'{base}..HEAD')
            cases.append(('no set names a step_review: nothing, no error',
                          lines == [] and not written, repr(lines)))
            (wt / 'tools' / 'zz').mkdir(parents=True)
            (wt / 'tools' / 'zz' / 'zz_review.py').write_text(tool, encoding='utf-8')
            (wt / 'precedent-source.json').write_text(json.dumps({
                'name': 'zz-set', 'level': 'shared',
                'step_review': 'tools/zz/zz_review.py'}), encoding='utf-8')
            cases.append(('the engine finds the tool the set names',
                          pr.set_tool(wt, 'step_review') == wt / 'tools' / 'zz' / 'zz_review.py',
                          repr(pr.set_tool(wt, 'step_review'))))
            os.environ['ZZ_OFF'] = '1'
            try:
                lines, written = pb._upstream_review(wt, wt, 'booked', 'out', f'{base}..HEAD')
            finally:
                os.environ.pop('ZZ_OFF', None)
            cases.append(('the tool says it does not apply: nothing shown, '
                          'the commit untouched',
                          lines == [] and not written
                          and 'Zz-seen:' not in head_msg(wt), repr(lines)))
            lines, written = pb._upstream_review(wt, wt, 'booked', 'out', f'{base}..HEAD')
            cases.append(('the tool applies: its report is shown and its line '
                          'goes into the landing commit',
                          written and 'Zz-seen: abc WARN: one thing' in head_msg(wt)
                          and any('ZZ REVIEW (booked): 1' in l for l in lines),
                          f'{lines} {head_msg(wt)!r}'))
            lines, written = pb._upstream_review(wt, None, 'zz-stage', 'out', f'{base}..HEAD')
            cases.append(('with no commit to write into, the report is shown and '
                          'nothing is written',
                          not written and any('ZZ REVIEW (zz-stage)' in l for l in lines),
                          repr(lines)))
            (wt / 'precedent-source.json').write_text(json.dumps({
                'name': 'zz-set', 'level': 'shared',
                'step_review': '../outside.py'}), encoding='utf-8')
            cases.append(('a named path outside tools/ is never loaded',
                          pr.load_set_tool(wt, 'step_review') is None, ''))
        finally:
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a stage runs the step_review a set names, and only that '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_branch_policy_seam_asks_a_set_and_keeps_the_engine_answer():
    """The branch policy seam (piece 5a, 2026-10-19): which branches are
    tiers, how hard a push to one is checked, and whether work reaches main
    only by promotion are asked of the module a set names as
    `branch_policy` in its precedent-source.json. Made-up set and policy.

    - no set names one: the engine's own answers, unchanged;
    - a set names one and the ladder is in force: its answers win, and main
      stays a tier whatever it says;
    - a question it does not define, an answer of the wrong shape, or a
      tier this engine does not know: the engine's answer;
    - a policy that raises: the engine's answer, no error;
    - off the ladder: never asked."""
    import tempfile
    import precedent_branches as pb
    cases = []
    policy = (
        'import os\n'
        'def tier_branches(root, default, user_config=None):\n'
        '    if os.environ.get("ZZ_BAD"):\n'
        '        return "not a list"\n'
        '    if os.environ.get("ZZ_RAISE"):\n'
        '        raise RuntimeError("boom")\n'
        '    return ["zz-tier"]\n'
        'def tier_for_branch(root, branch, default, user_config=None):\n'
        '    if branch == "zz-odd":\n'
        '        return ("loud", "a tier nobody knows")\n'
        '    return ("full", "zz says full for " + branch)\n')
    saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
    saved_ladder = pb.ladder_in_force
    with tempfile.TemporaryDirectory() as td:
        wt = pathlib.Path(td) / 'repo'
        wt.mkdir()
        os.environ['PRECEDENT_USER_CONFIG'] = str(pathlib.Path(td) / 'no-config.json')
        try:
            fixture_git(wt, 'init', '-q', '-b', 'main')
            pb.ladder_in_force = lambda root, user_config=None: True
            engine = (pb._engine_tier_branches(wt),
                      pb._engine_tier_for_branch(wt, 'feature-x'),
                      pb._engine_promote_only(wt))
            cases.append(('no set names a branch policy: the engine answers',
                          (pb.tier_branches(wt), pb.tier_for_branch(wt, 'feature-x'),
                           pb.promote_only(wt)) == engine, repr(engine)))
            (wt / 'tools' / 'zz').mkdir(parents=True)
            (wt / 'tools' / 'zz' / 'zz_policy.py').write_text(policy, encoding='utf-8')
            (wt / 'precedent-source.json').write_text(json.dumps({
                'name': 'zz-set', 'level': 'shared',
                'branch_policy': 'tools/zz/zz_policy.py'}), encoding='utf-8')
            got = pb.tier_branches(wt)
            cases.append(("the set's answer wins, and main stays a tier",
                          got == ['main', 'zz-tier'], repr(got)))
            got = pb.tier_for_branch(wt, 'feature-x')
            cases.append(("the set's check level wins",
                          got == ('full', 'zz says full for feature-x'), repr(got)))
            got = pb.tier_for_branch(wt, 'zz-odd')
            cases.append(('a tier this engine does not know: the engine answers',
                          got == pb._engine_tier_for_branch(wt, 'zz-odd'), repr(got)))
            got = pb.promote_only(wt)
            cases.append(('a question the policy does not define: the engine answers',
                          got == pb._engine_promote_only(wt), repr(got)))
            for env, name in (('ZZ_BAD', 'an answer of the wrong shape'),
                              ('ZZ_RAISE', 'a policy that raises')):
                os.environ[env] = '1'
                try:
                    got = pb.tier_branches(wt)
                finally:
                    os.environ.pop(env, None)
                cases.append((f'{name}: the engine answers, no error',
                              got == engine[0], repr(got)))
            pb.ladder_in_force = lambda root, user_config=None: False
            got = pb.tier_branches(wt)
            cases.append(('off the ladder the policy is never asked',
                          got == engine[0], repr(got)))
        finally:
            pb.ladder_in_force = saved_ladder
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the branch policy a set names answers, and the engine keeps '
          f'every answer it cannot use ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_promote_is_handed_to_the_moves_a_set_names():
    """The moves a set provides (piece 5b, 2026-10-19): `--promote` and
    `--wait-main-test` are handed, arguments unchanged, to the module a set
    names as `branch_moves` in its precedent-source.json, bound to the
    engine that called it. Made-up set and module; the real moves are
    tested in the set that ships them.

    - no set names one: both commands refuse, exit 2, and push nothing;
    - a set names one: its main() gets the arguments as typed, bound to
      this engine, and its exit status is the command's;
    - a module that fails to load, or has no main(): refused, as if there
      were none."""
    import tempfile
    cases = []
    moves = (
        'import json, pathlib\n'
        'core = None\n'
        'def bind(engine):\n'
        '    global core\n'
        '    core = engine\n'
        'def main(root, argv):\n'
        '    pathlib.Path(root, "zz-called.json").write_text(json.dumps(\n'
        '        {"argv": argv, "bound": callable(getattr(core, "land", None))}))\n'
        '    return 7\n')
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_USER_CONFIG=str(tmp / 'no-config.json'))
        work = tmp / 'work'
        bare = tmp / 'origin.git'
        fixture_git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(work))
        fixture_git(work, 'config', 'user.email', 'h@example.com')
        fixture_git(work, 'config', 'user.name', 'H')
        fixture_git(work, 'commit', '-q', '--allow-empty', '-m', 'base')
        fixture_git(work, 'remote', 'add', 'origin', str(bare))
        fixture_git(work, 'push', '-q', 'origin', 'main', 'main:staging')

        def run(*args):
            p = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_branches.py'),
                                *args], cwd=str(work), env=env,
                               capture_output=True, text=True, timeout=120)
            return p.returncode, p.stdout + p.stderr

        def heads():
            return subprocess.run(['git', '-C', str(work), 'ls-remote', '--heads',
                                   'origin'], capture_output=True, text=True).stdout

        before = heads()
        for args in (('--promote', '--to', 'main'), ('--wait-main-test', 'main')):
            rc, out = run(*args)
            cases.append((f'no set names any moves: {args[0]} refuses and pushes nothing',
                          rc == 2 and 'is a move a practice set provides' in out
                          and heads() == before, f'rc={rc} {failure_detail(out, 200)}'))
        (work / 'tools' / 'zz').mkdir(parents=True)
        (work / 'tools' / 'zz' / 'zz_moves.py').write_text(moves, encoding='utf-8')
        (work / 'precedent-source.json').write_text(json.dumps({
            'name': 'zz-set', 'level': 'shared',
            'branch_moves': 'tools/zz/zz_moves.py'}), encoding='utf-8')
        rc, out = run('--promote', '--to', 'main', '--work', 'x')
        try:
            called = json.loads((work / 'zz-called.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            called = {}
        cases.append(("a set names its moves: they get the arguments as typed, "
                      "bound to this engine, and their exit status is the command's",
                      rc == 7 and called.get('argv') == ['--promote', '--to', 'main',
                                                         '--work', 'x']
                      and called.get('bound') is True, f'rc={rc} {called} {failure_detail(out, 200)}'))
        for broken, why in (('raise RuntimeError("boom")\n', 'fails to load'),
                            ('x = 1\n', 'has no main()')):
            (work / 'tools' / 'zz' / 'zz_moves.py').write_text(broken, encoding='utf-8')
            rc, out = run('--promote')
            cases.append((f'a module that {why} is refused as if there were none',
                          rc == 2 and 'is a move a practice set provides' in out,
                          f'rc={rc} {failure_detail(out, 200)}'))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Promote is handed to the moves a set names, and refused without '
          f'them ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_branch_name_follows_the_convention():
    """A session's feature branch is `<prefix><date>-<slug>-<session>-<random>`,
    the session part being the end of the session's ID (practice: act), and
    the random part on every name (Morgan, 2026-10-11).

    The controlling case is the session ID: given the harness's
    `cse_<id>`, the name ends in that ID's last five characters, lowercased,
    so the branch leads back to its session. The rest are the fallbacks the
    rule promises -- no ID means random characters and a note saying so, a
    name already on origin draws new random ones and a note, an origin that cannot
    be asked is said rather than read as "not there" -- and the refusal of a
    slug with no words in it, asserted by its own message."""
    import tempfile
    import precedent_branch_name as pbn

    _git = fixture_git
    results = []
    # No user-level config and no declared username: the names below carry
    # none, and a session whose own config declares one otherwise failed
    # here on a change that had nothing to do with naming (2026-10-16).
    saved = {k: os.environ.pop(k, None)
             for k in ('CLAUDE_CODE_REMOTE_SESSION_ID', 'CLAUDECODE',
                       'PRECEDENT_USER_CONFIG', 'PRECEDENT_GITHUB_USER')}
    try:
        os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = 'cse_01SQeHb3tgRrvXtsoviaWpkv'
        os.environ['CLAUDECODE'] = '1'
        os.environ['PRECEDENT_USER_CONFIG'] = os.devnull
        name, notes = pbn.build(['Feature', 'branch naming!'], date='2026-10-01',
                                rand='q7m2x')
        os.environ.pop('CLAUDECODE')
        results.append(('the session ID\'s end, lowercased, then the random part, '
                        'with no prefix even under Claude Code',
                        name == '2026-10-01-feature-branch-naming-awpkv-q7m2x'
                        and not notes))
        a, _ = pbn.build(['x'], date='2026-10-01')
        b, _ = pbn.build(['x'], date='2026-10-01')
        results.append(('every name gets random characters after the session part, '
                        'so two the same day differ without a clash',
                        re.fullmatch(r'2026-10-01-x-awpkv-[a-z0-9]{5}', a) is not None
                        and a != b))

        os.environ.pop('CLAUDE_CODE_REMOTE_SESSION_ID')
        a, notes_a = pbn.build(['x'], date='2026-10-01')
        b, _ = pbn.build(['x'], date='2026-10-01')
        results.append(('no session ID: random lowercase characters in the session '
                        'part too, said',
                        re.fullmatch(r'2026-10-01-x-[a-z0-9]{5}-[a-z0-9]{5}', a)
                        is not None and a != b
                        and any('no session ID found' in n for n in notes_a)))

        name, _ = pbn.build(['One two', 'three-four', 'five six SEVEN'],
                            date='2026-10-01', prefix='', tail='abcde', rand='q7m2x')
        results.append(('the slug keeps six words, lowercase',
                        name == '2026-10-01-one-two-three-four-five-six-abcde-q7m2x'))

        try:
            pbn.build(['!!', '--'], tail='abcde')
            results.append(('a slug with no words is refused', False))
        except ValueError as e:
            results.append(('a slug with no words is refused',
                            'no usable words for the slug' in str(e)))

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            up = tmp / 'up'; up.mkdir()
            _git(up, 'init', '-q', '-b', 'main')
            _git(up, 'config', 'user.email', 'harness@example.com')
            _git(up, 'config', 'user.name', 'Harness')
            (up / 'f.txt').write_text('base\n')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
            taken = 'claude/2026-10-01-feature-branch-naming-awpkv-q7m2x'
            _git(up, 'branch', taken)
            clone = tmp / 'clone'
            subprocess.run(['git', 'clone', '-q', f'file://{up}', str(clone)],
                           capture_output=True, text=True)
            exists = lambda n: pbn.on_origin(n, clone)
            name, notes = pbn.build(['feature branch naming'], date='2026-10-01',
                                    prefix='claude/', tail='awpkv', rand='q7m2x',
                                    exists=exists)
            results.append(('a name already on origin draws new random characters '
                            'in the same place',
                            name != taken and re.fullmatch(
                                r'claude/2026-10-01-feature-branch-naming-awpkv-'
                                r'[a-z0-9]{5}', name) is not None
                            and any('already taken' in n and 'origin' in n for n in notes)))
            name, notes = pbn.build(['fresh'], date='2026-10-01', prefix='claude/',
                                    tail='awpkv', rand='q7m2x', exists=exists)
            results.append(('a free name is left as it is (negative control)',
                            name == 'claude/2026-10-01-fresh-awpkv-q7m2x' and not notes))

            _git(clone, 'remote', 'set-url', 'origin', str(tmp / 'nowhere'))
            name, notes = pbn.build(['fresh'], date='2026-10-01', prefix='claude/',
                                    tail='awpkv', rand='q7m2x',
                                    exists=lambda n: pbn.on_origin(n, clone))
            results.append(('an origin that cannot be asked is said, not read as free',
                            name == 'claude/2026-10-01-fresh-awpkv-q7m2x'
                            and any('could not ask origin' in n for n in notes)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    failed = [n for n, ok in results if not ok]
    check(f'a feature branch is named <date>-<slug>-<id>, the id from the '
          f'session ID, with the stated fallbacks ({len(results)} cases, the '
          f'session ID the controlling one)',
          not failed, '; '.join(failed) if failed else '')


