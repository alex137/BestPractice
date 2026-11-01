# The harness tests for attaching
#
# tools/harness/vh_source_setup.py -- part of the verification harness:
# attaching, refreshing and moving practice sources.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_freshness_reads_a_private_source_through_its_clone():
    """A live source clone whose only credential is its own local
    credential.helper is reported current or behind, never NOT VERIFIED.

    Found 2026-09-30: upstream_tip() ran `git ls-remote <url>` from outside
    the clone, where a private source's credential does not reach, so every
    session printed "NOT VERIFIED ... could not reach". The same ls-remote
    against `origin` inside the clone succeeds. Git is stubbed to answer
    exactly that way: the bare URL refused, `origin` answered only from the
    clone. CONTROL: with no clone to ask from, the same row is NOT VERIFIED,
    so the verdict comes from asking inside the clone. Also: a behind live
    clone's remedy is the refresh, never a bare pull (engine output a
    refresh leaves there makes that pull refuse)."""
    import contextlib, io, tempfile
    import precedent_engine_freshness as pef
    cases = []
    url = 'https://github.com/example/private-set.git'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='freshness-private-'))
    clone = str(tmp / 'private-set')
    saved = (pef._git, pef.collect_targets)

    def fake_git(*args, cwd=None, timeout=25):
        if args[:3] == ('remote', 'get-url', 'origin') and cwd == clone:
            return 0, url
        if args[:2] == ('ls-remote', 'origin') and cwd == clone:
            return 0, 'abc123\trefs/heads/main'
        if args[:1] == ('ls-remote',):
            return 128, ''      # no credential out here
        return saved[0](*args, cwd=cwd, timeout=timeout)

    def run(recorded, path):
        row = {'label': 'set (shared) live clone', 'kind': 'live', 'url': url,
               'branch': 'main', 'recorded': recorded}
        if path:
            row['path'] = path
        pef.collect_targets = lambda root='.': [row]
        buf = io.StringIO()
        pef.report(str(tmp), out=buf)
        return buf.getvalue()

    try:
        pef._git = fake_git
        out = run('abc123', clone)
        cases.append(('a current private clone reads current, not NOT VERIFIED',
                      'current' in out and 'NOT VERIFIED' not in out, out))
        out = run('old999', clone)
        cases.append(('a behind private clone reads BEHIND, not NOT VERIFIED',
                      'BEHIND UPSTREAM' in out and 'NOT VERIFIED' not in out, out))
        cases.append(('...and its remedy is the refresh, never a bare pull',
                      'precedent_refresh_sources.py --apply --path' in out
                      and 'pull --ff-only' not in out, out))
        out = run('abc123', None)
        cases.append(('CONTROL: with no clone to ask from, the same row is NOT VERIFIED',
                      'NOT VERIFIED' in out, out))
    finally:
        pef._git, pef.collect_targets = saved
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the freshness notice reads a private source through its own clone '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_session_check_suggests_anchored_also_list():
    """The session check suggests PRECEDENT_FRESHNESS_ALSO anchored where
    each kind of set lives, never as absolute paths (2026-09-30).

    Sessions kept flipping the variable between /home/user/... and ~/...,
    each flip breaking half of it, and the suggestion this row printed was
    what restarted it: absolute paths read off one disk. A shared set beside
    the project is written $CLAUDE_PROJECT_DIR/../<name>, as every repo
    declares it; the individual set in $HOME is ~/<name>; and each form
    expands back to the real directory."""
    import tempfile
    import precedent_session_check as psc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='anchored-also-'))
    saved = (psc.ROOT, os.environ.get('HOME'), os.environ.get('CLAUDE_PROJECT_DIR'))
    try:
        home, work = tmp / 'home', tmp / 'work'
        for d in (home / 'precedent-individual', work / 'precedent-shared-acme',
                  work / 'project'):
            (d / '.git').mkdir(parents=True)
        psc.ROOT = (work / 'project').resolve()
        os.environ['HOME'] = str(home.resolve())
        os.environ['CLAUDE_PROJECT_DIR'] = str(psc.ROOT)
        got = dict(psc._attachable_sources())
        cases.append(('the individual set in $HOME is written ~/<name>',
                      '~/precedent-individual' in got, str(got)))
        cases.append(('a shared set beside the project is written '
                      '$CLAUDE_PROJECT_DIR/../<name>',
                      '$CLAUDE_PROJECT_DIR/../precedent-shared-acme' in got, str(got)))
        cases.append(('no absolute path is suggested',
                      not any(p.startswith('/') for p in got), str(got)))
        back = pathlib.Path(psc._expand_source_path(
            '$CLAUDE_PROJECT_DIR/../precedent-shared-acme')).resolve()
        cases.append(('the anchored form expands to the real clone',
                      back == (work / 'precedent-shared-acme').resolve(), str(back)))
    finally:
        psc.ROOT = saved[0]
        for k, val in (('HOME', saved[1]), ('CLAUDE_PROJECT_DIR', saved[2])):
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session check suggests the also-list anchored, never absolute '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_source_base_url_defaults_to_the_token_account():
    """Where the private sets live defaults to the account the token belongs
    to, kept in the user config once worked out (2026-09-30, agreed with a
    consumer session).

    PRECEDENT_SOURCE_BASE_URL was one more value to set in every environment,
    and for most people it named the token's own account. Stated cases, with
    GitHub's answer from a fixture (the same PRECEDENT_GITHUB_USER_URL the
    commit-identity hook reads) and a throwaway user config: the variable
    still wins; unset, the account is used and kept; a later run with GitHub
    unreachable still has it; with nothing known it is empty, never a guess."""
    import tempfile
    import precedent_source_credentials as psc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='base-url-'))
    try:
        gh = tmp / 'user.json'
        gh.write_text('{"login": "octo", "id": 42}', encoding='utf-8')
        cfg = tmp / 'config.json'
        env = {'PRECEDENT_USER_CONFIG': str(cfg), 'PRECEDENT_GITHUB_USER_URL': gh.as_uri()}
        got, _ = psc.source_base_url(dict(env, PRECEDENT_SOURCE_BASE_URL='https://example.com/org'))
        cases.append(('the variable still wins', got == 'https://example.com/org', got))
        got, where = psc.source_base_url(env)
        cases.append(('unset, the token\'s account is used',
                      got == 'https://github.com/octo', f'{got} {where}'))
        kept = json.loads(cfg.read_text(encoding='utf-8')).get('source_base_url')
        cases.append(('and kept in the user config', kept == 'https://github.com/octo', str(kept)))
        got, where = psc.source_base_url(dict(env, PRECEDENT_GITHUB_USER_URL=(tmp / 'gone').as_uri()))
        cases.append(('a later run with GitHub unreachable still has it',
                      got == 'https://github.com/octo' and 'config' in where, f'{got} {where}'))
        cfg.unlink()
        got, _ = psc.source_base_url(dict(env, PRECEDENT_GITHUB_USER_URL=(tmp / 'gone').as_uri()))
        cases.append(('with nothing known it is empty, never a guess', got == '', got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the private sets\' location defaults to the token\'s account '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:200]}" for n, d in bad))


def check_session_start_charges_brought_sets_to_the_person():
    """The session-start check holds the sets a person brings to that
    person's `brought_sets_tokens` budget, never to the repository's ceiling,
    as the full check's session-load-budget already did (2026-10-03).
    Reported from a consumer, 2026-10-06: its ceiling, set before the ladder
    started arriving by `brings`, failed a guarantee at every session start.
    Planted with stand-ins for the share and the budget."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_session_check as psc
        import precedent_session_practices as psp
    finally:
        sys.path.pop(0)
    # charged_to_repo reads both renders through _brought_renders since
    # 2026-10-09, so the stand-in replaces that: 1500 with the brought set,
    # 900 without it, a share of 600.
    saved = (psp._brought_renders, psp.brought_budget)
    cases = []
    try:
        psp._brought_renders = lambda repo=None: (1500, 900, ['acme-shared-ladder'])
        psp.brought_budget = lambda repo=None: (700, '/ind')
        n, note, over = psc._charge_brought_share(1500)
        cases.append(('the brought share leaves the repository\'s count',
                      n == 900 and 'which you bring' in note and over is None))
        psp.brought_budget = lambda repo=None: (500, '/ind')
        n, note, over = psc._charge_brought_share(1500)
        cases.append(('over the person\'s own budget, that is what is reported',
                      n == 900 and over and 'brought_sets_tokens' in over))
        psp.brought_budget = lambda repo=None: (None, '/ind')
        n, note, over = psc._charge_brought_share(1500)
        cases.append(('no budget declared: charged to the repository, as before',
                      n == 1500 and note == '' and over is None))
        psp._brought_renders = lambda repo=None: (None, None, [])
        psp.brought_budget = lambda repo=None: (700, '/ind')
        cases.append(('nothing brought: unchanged',
                      psc._charge_brought_share(1500) == (1500, '', None)))
    finally:
        psp._brought_renders, psp.brought_budget = saved
    failed = [nm for nm, ok in cases if not ok]
    check(f'the session-start check charges brought sets to the person '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_move_dedupe_stub_names_the_slug_alone():
    """A deduplicated stub written by tools/precedent_move.py says the rule
    is in force under its slug, and names no set as where it is in force.

    WHY (very deep check, 2026-10-05, pass 3). The stub used to end "the
    rule is in force there as `<slug>`", "there" being the destination set.
    When repo-maintenance and working-style folded into universal, every
    stub that pointed at them kept saying so, and each sentence became
    false while nothing broke: lookup is by slug. The dated "Moved to ...
    on <date>" line before it is history and keeps the destination."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-stub-'))
    env = _move_fixture_env(tmp)
    cases = []

    def run(args):
        return subprocess.run([sys.executable, *args], cwd=str(ROOT),
                              capture_output=True, text=True, env=env)

    try:
        tool = str(ROOT / 'tools' / 'precedent_move.py')
        boot = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        team = tmp / 'precedent-shared-zzfold'
        r = run([boot, '--level', 'team', '--name', 'precedent-shared-zzfold',
                 '--dest', str(team), '--approver', 'Fixture Approver:fixture-gh'])
        cases.append(('the fixture set bootstraps', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 400)))
        (team / 'practices' / 'zz-stub.md').write_text(
            _move_fixture_practice('zz-stub'), encoding='utf-8')
        clone = tmp / 'precedent-clone'
        (clone / 'practices').mkdir(parents=True)
        r = run([tool, '--slug', 'zz-stub', '--from', 'team', '--from-path', str(team),
                 '--to', 'universal', '--to-path', str(clone),
                 '--approved-by', 'Fixture Approver'])
        cases.append(('team -> universal drafts', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 400)))
        r = run([tool, '--slug', 'zz-stub', '--from', 'team', '--from-path', str(team),
                 '--to', 'universal', '--to-path', str(clone),
                 '--approved-by', 'Fixture Approver', '--dedupe-only'])
        text = (team / 'practices' / 'zz-stub.md').read_text(encoding='utf-8')
        tail = text.split('This copy is deduplicated', 1)[-1].split('\n', 1)[0]
        cases.append(('--dedupe-only writes the deduplicated stub',
                      r.returncode == 0 and 'status:      deduplicated' in text,
                      failure_detail(r.stdout + r.stderr, 400)))
        cases.append(('the stub says the rule is in force under its slug',
                      'the rule stays in force under its slug, `zz-stub`' in tail,
                      tail))
        cases.append(('the stub names no set as where the rule is in force',
                      'in force there' not in text and 'precedent-clone' not in tail
                      and 'universal' not in tail, tail))
        cases.append(('the dated move line before it still names where it went',
                      'Moved to the universal set' in text, failure_detail(text, 500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'a deduplicated stub names the slug alone, never a set that may '
          f'later fold ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_update_never_fetches_the_repo_it_updates():
    """Update Vendors in a set the person's individual set brings -- the
    ladder set, updated from its own clone -- does not fetch that clone as a
    brought set: mid-update it is on a branch with staged changes, and the
    fetch refused the update over itself (2026-10-07). Any other brought set
    is still fetched."""
    import tempfile, inspect
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_bootstrap as _psb
    import precedent_resolve as _pr
    import precedent_update as _pu
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        (t / 'ladder' / '.git').mkdir(parents=True)
        (t / 'ind').mkdir()
        cfg = t / 'config.json'
        cfg.write_text(json.dumps({'individual': {'path': str(t / 'ind')}}),
                       encoding='utf-8')
        real_brought, real_env = _pr.brought_sources, os.environ.get(_pr.USER_CONFIG_ENV)
        try:
            _pr.brought_sources = lambda p, warn=False: [
                {'name': 'ladder', 'repo': 'https://example.invalid/ladder.git',
                 'path': str(t / 'ladder')}]
            os.environ[_pr.USER_CONFIG_ENV] = str(cfg)
            got = _psb.sources_from_brings(retries=1, skip=[t / 'ladder'])
            cases.append(('the repo being updated is not fetched, and says so',
                          got == [('ladder', True, 'this repository itself, the '
                                   'one being updated: not fetched')], repr(got)))
            got = _psb.sources_from_brings(retries=1)
            cases.append(('without skip it is still fetched (here: an attempt that '
                          'fails on the fixture, not a skip)',
                          bool(got) and 'not fetched' not in got[0][2], repr(got)[:200]))
            # 2026-10-08, the shape that held two updates: the brought set is
            # a real clone, on a branch another update in the same session
            # just made. It is read as it stands, a note naming the branch,
            # never a stop.
            lad = t / 'ladder-real'
            genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                        GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
            for a in (['init', '-q', '-b', 'main', str(lad)], ):
                subprocess.run(['git', *a], env=genv, capture_output=True)
            (lad / 'practices').mkdir()
            (lad / 'practices' / 'r.md').write_text('x\n', encoding='utf-8')
            for a in (['add', '-A'], ['commit', '-qm', 'r'],
                      ['checkout', '-qb', 'session-update']):
                subprocess.run(['git', '-C', str(lad), *a], env=genv, capture_output=True)
            _pr.brought_sources = lambda p, warn=False: [
                {'name': 'ladder', 'repo': f'file://{lad}', 'path': str(lad)}]
            got = _psb.sources_from_brings(retries=1)
            cases.append(('a brought set on another session\'s working branch is '
                          'read as it stands, naming the branch',
                          len(got) == 1 and got[0][1] is True
                          and "'session-update'" in got[0][2], repr(got)[:300]))
            branch_now = subprocess.run(['git', '-C', str(lad), 'rev-parse', '--abbrev-ref',
                                         'HEAD'], capture_output=True, text=True).stdout.strip()
            cases.append(('...and stays on that branch', branch_now == 'session-update',
                          branch_now))
            rep = _pu.Report()
            _pu.brought_sets_step(rep, fetch=lambda: got)
            cases.append(('...and the update reports it as a step, leaving nothing '
                          'for the person',
                          not rep.left and any('session-update' in o
                                               for _n, o in rep.steps),
                          repr(rep.steps)[:300]))
        finally:
            _pr.brought_sources = real_brought
            if real_env is None:
                os.environ.pop(_pr.USER_CONFIG_ENV, None)
            else:
                os.environ[_pr.USER_CONFIG_ENV] = real_env
    cases.append(('Update Vendors passes the repo it updates',
                  'brought_sets_step(rep, repo=repo)' in inspect.getsource(_pu.update),
                  ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors never fetches the repo it is updating as a brought '
          f'set ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_individual_bootstrap_says_to_fill_in_identity():
    """Bootstrapping an individual set ends by naming the identity.json
    fields still holding placeholders, and a shared set's report does not.

    Found 2026-10-31 by the very deep check's pass 1 practice-move
    rehearsal: an individual set bootstrapped as FOR_DEVELOPERS.md says,
    then committed, failed its own full sweep -- check_commit_author wanted
    the author '{{PERSON_NAME}}' -- and the closing report had said only
    that the set needs a git remote.

    Negative control, measured 2026-10-31: on the code before the fix the
    first case fails (no FILL IN line).
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-bootstrap-identity-'))
    (tmp / 'home').mkdir()
    env = dict(_isolated_env(os.environ, tmp / 'home'), PRECEDENT_SEED_OFF_MAIN='1')
    cases = []
    try:
        outs = {}
        for level, extra in (('individual', []),
                             ('shared', ['--approver', 'A Person:aperson'])):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                                '--level', level, '--name', f'vh-{level}', '--dest',
                                str(tmp / level), '--off-main', 'true', *extra],
                               capture_output=True, text=True, env=env, timeout=300)
            outs[level] = r.stdout + r.stderr
        tail = outs['individual'].split('BOOTSTRAPPED:', 1)[-1]
        cases.append(("an individual set's report names identity.json's unfilled fields",
                      'FILL IN identity.json' in tail and 'name, email, timezone' in tail,
                      failure_detail(tail, 500)))
        cases.append(("a shared set's report does not",
                      'BOOTSTRAPPED:' in outs['shared']
                      and 'FILL IN identity.json' not in outs['shared'],
                      failure_detail(outs['shared'], 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'an individual bootstrap says to fill in identity.json '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_refresh_from_ref_off_the_branch_is_recorded():
    """A refresh --from-ref of a commit the followed branch lacks records
    that in the manifest (seeded_from_branch), as seed --off-main does, so
    the manifest never claims main for a commit main does not have
    (2026-10-17: a practice set's manifest said source_branch main over a
    BestPractice feature-branch commit, refreshed with --from-ref).

    Negative control: on staging's code there is no from_ref_off_branch and
    refresh writes no seeded_from_branch."""
    import inspect, tempfile
    name = 'a refresh --from-ref off the followed branch is recorded'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    cases = []
    fn = getattr(pve, 'from_ref_off_branch', None)
    cases.append(('the engine can tell an off-branch commit', callable(fn)))
    if callable(fn):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_COMMITTER_NAME='T',
                       GIT_AUTHOR_EMAIL='t@example.invalid',
                       GIT_COMMITTER_EMAIL='t@example.invalid')

            def g(*a):
                return subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True).stdout.strip()
            g('init', '-q', '-b', pve.FOLLOWED_BRANCH)
            g('commit', '-q', '--allow-empty', '-m', 'on the branch')
            on = g('rev-parse', 'HEAD')
            g('checkout', '-q', '-b', 'feature')
            g('commit', '-q', '--allow-empty', '-m', 'only on a feature branch')
            off = g('rev-parse', 'HEAD')
            got = fn(repo, off)
            cases.append(('a feature-branch commit is named as off the branch',
                          bool(got) and off[:12] in got
                          and pve.FOLLOWED_BRANCH in got, got))
            cases.append(('CONTROL: a commit on the branch is not',
                          fn(repo, on) is None, fn(repo, on)))
    src = inspect.getsource(pve.refresh) if hasattr(pve, 'refresh') else ''
    cases.append(('refresh writes it into the manifest',
                  'seeded_from=off_branch' in src))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + str(d)[:200] + ')' if d else ''}" for n, d in bad))


def check_a_stale_source_clone_is_made_current_not_reported_clean():
    """The loop that put four sources 17 to 34 commits behind.

    The refresh writes engine files into a source clone and never commits
    them -- deliberately, `this tool never publishes`. The clone is then
    dirty, so the next session's ff-only pull refuses and the refresh's own
    dirty-guard skips. Nothing exited non-zero and the closing line read
    `applied.` either way, so it ran that way for weeks while every session
    start reported success. Every dirty path in all four clones was engine
    output nobody had hand-edited: the tool's own output disarmed the tool.

    Morgan, 2026-09-21 (strength: decided): make it current, do not merely
    check. So the four behaviours that carry that are asserted here against
    real git repositories rather than inferred from a passing run -- above
    all the TWO REFUSALS, which are what keep "discard the engine's output"
    from becoming "discard somebody's work" (practice:
    control-asserts-which-failure)."""
    import importlib.util as _ilu
    import tempfile
    spec = _ilu.spec_from_file_location(
        '_rs_probe', ROOT / 'tools' / 'precedent_refresh_sources.py')
    try:
        rs = _ilu.module_from_spec(spec)
        spec.loader.exec_module(rs)
    except Exception as exc:                     # noqa: BLE001
        return (False, '', f'precedent_refresh_sources.py would not import: {exc}')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-stale-source-'))

    def git(repo, *args):
        return subprocess.run(['git', '-C', str(repo), *args],
                              capture_output=True, text=True)

    def new_repo(name):
        # fixture-owns-its-state: its own identity and its own branch name,
        # so a machine's global git config cannot change the answer.
        r = tmp / name
        r.mkdir(parents=True)
        git(r, 'init', '--quiet', '--initial-branch', 'main')
        git(r, 'config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        git(r, 'config', 'user.name', 'Fixture')
        return r

    cases = []
    try:
        origin = new_repo('origin')
        (origin / 'tools').mkdir()
        manifest = {'format_version': 1, 'kind': 'source',
                    'source_branch': 'main', 'files': ['engine_a.py'],
                    'hook_files': [], 'ci_workflow_files': []}
        (origin / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(manifest), encoding='utf-8')
        (origin / 'tools' / 'engine_a.py').write_text('v1\n', encoding='utf-8')
        (origin / 'practices').mkdir()
        (origin / 'practices' / 'p.md').write_text('one\n', encoding='utf-8')
        # A generated view, TRACKED the way a real source clone tracks it --
        # case 8 below rewrites it to prove build_views' output is discarded
        # and restored rather than deleted.
        (origin / 'MAP.md').write_text('generated, v1\n', encoding='utf-8')
        (origin / 'precedent.json').write_text('{"base_branch": "main"}',
                                               encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '--quiet', '-m', 'first')

        clone = tmp / 'clone'
        subprocess.run(['git', 'clone', '--quiet', str(origin), str(clone)],
                       capture_output=True, text=True)
        # fixture-owns-its-state, same as new_repo above: a CLONE inherits no
        # identity, so without these two lines every `git commit` below falls
        # back to the machine's global config. On a developer box that config
        # exists and the commits land; in CI it does not, the commits fail
        # silently, and the "diverged clone" this fixture believes it built is
        # just a clone sitting at origin -- which make_current then correctly
        # fast-forwards, failing the two refusal cases for the one reason they
        # were never testing. Reported 2026-09-21 by the sharded CI job, after
        # a crash in the check filter stopped masking it.
        git(clone, 'config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        git(clone, 'config', 'user.name', 'Fixture')

        # origin moves on; the clone does not.
        (origin / 'practices' / 'p.md').write_text('two\n', encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '--quiet', '-m', 'second')

        # 1. The engine's own output is recognised as the engine's.
        (clone / 'tools' / 'engine_a.py').write_text('v2\n', encoding='utf-8')
        engine, other = rs.classify_dirt(clone)
        cases.append(('a modified manifest-listed file is engine dirt',
                      engine == ['tools/engine_a.py'] and not other,
                      f'engine={engine} other={other}'))

        # 2. A person's file is NEVER the engine's, even beside engine dirt.
        #    IT MUST BE TRACKED AND MODIFIED -- not because `??` is safe
        #    (since 2026-09-22 an untracked OWNED path is engine dirt, case
        #    8 below), but because a tracked, modified, unowned file is the
        #    one shape where only the owned-set decides. Built any other way
        #    the case passes on the status code and exercises nothing --
        #    proven by planting "every modified file is engine output" and
        #    watching it pass anyway.
        (clone / 'practices' / 'mine.md').write_text('hand\n', encoding='utf-8')
        git(clone, 'add', '-A')
        git(clone, 'commit', '--quiet', '-m', 'a file of my own')
        (clone / 'practices' / 'mine.md').write_text('hand, edited\n',
                                                     encoding='utf-8')
        engine, other = rs.classify_dirt(clone)
        cases.append(("a TRACKED, MODIFIED file the manifest does not list "
                      "is a person's",
                      'practices/mine.md' in other
                      and 'practices/mine.md' not in engine,
                      f'engine={engine} other={other}'))
        git(clone, 'checkout', '--', 'practices/mine.md')
        git(clone, 'reset', '--quiet', '--hard', 'HEAD~1')

        # 3. make_current brings it current, and the file it discarded was
        #    only ever the engine's.
        ok, note = rs.make_current(clone, 'main')
        counts = git(clone, 'rev-list', '--left-right', '--count',
                     'origin/main...HEAD').stdout.split()
        cases.append(('a behind clone with engine dirt is made current',
                      ok and counts == ['0', '0'], f'{note} counts={counts}'))
        cases.append(('and its working tree carries the new content',
                      (clone / 'practices' / 'p.md').read_text().strip() == 'two',
                      (clone / 'practices' / 'p.md').read_text().strip()))

        # 4. A PERSON'S dirt refuses, and changes nothing. The whole safety
        #    of part 2 rests on this one.
        (origin / 'practices' / 'p.md').write_text('three\n', encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '--quiet', '-m', 'third')
        git(clone, 'fetch', '--quiet', 'origin', 'main')
        (clone / 'practices' / 'mine.md').write_text('hand\n', encoding='utf-8')
        git(clone, 'add', '-A')
        git(clone, 'commit', '--quiet', '-m', 'a file of my own')
        (clone / 'practices' / 'mine.md').write_text('mid-review\n',
                                                     encoding='utf-8')
        engine, other = rs.classify_dirt(clone)
        cases.append(("a person's dirt is reported so the caller can refuse",
                      other == ['practices/mine.md']
                      and 'practices/mine.md' not in engine, f'other={other}'))
        cases.append(("and that edit is still on disk, unread by the engine",
                      (clone / 'practices' / 'mine.md').read_text().strip()
                      == 'mid-review', 'changed'))
        git(clone, 'checkout', '--', 'practices/mine.md')
        git(clone, 'reset', '--quiet', '--hard', 'HEAD~1')
        git(clone, 'merge', '--ff-only', 'origin/main')

        # 5. A DIVERGED clone refuses, and changes nothing.
        (clone / 'practices' / 'local.md').write_text('local\n', encoding='utf-8')
        git(clone, 'add', '-A')
        git(clone, 'commit', '--quiet', '-m', 'local only')
        (origin / 'practices' / 'p.md').write_text('four\n', encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '--quiet', '-m', 'fourth')
        head_before = git(clone, 'rev-parse', 'HEAD').stdout.strip()
        # The fixture asserts its own setup: if the local commit did not
        # land, everything below tests a clone that never diverged.
        _ahead = git(clone, 'rev-list', '--count', 'origin/main..HEAD').stdout.strip()
        cases.append(('the fixture really built a diverged clone',
                      _ahead == '1', f'{_ahead} local commit(s), expected 1'))
        ok, note = rs.make_current(clone, 'main')
        head_after = git(clone, 'rev-parse', 'HEAD').stdout.strip()
        cases.append(('a diverged clone refuses rather than rebasing anybody',
                      not ok and 'local commit' in note, note))
        cases.append(('and its HEAD is exactly where it was',
                      head_before == head_after,
                      f'{head_before[:12]} -> {head_after[:12]}'))
        cases.append(('and the unpushed commit is still there',
                      (clone / 'practices' / 'local.md').is_file(), 'gone'))

        # 6. The postcondition is real: make_current returns False when the
        #    tree did not arrive, rather than trusting the command.
        src = (ROOT / 'tools' / 'precedent_refresh_sources.py').read_text(
            encoding='utf-8')
        cases.append(('make_current verifies HEAD against origin afterwards',
                      'verify-postcondition' in src
                      and 'merge reported success but HEAD is' in src, ''))

        # 7. A skip is not a success -- the line and the exit code both.
        cases.append(('a skipped source is named and exits non-zero',
                      'NOT APPLIED to' in src
                      and 'return 1 if (failed or skipped) else 0' in src, ''))

        # 8. THE 2026-09-22 WIDENING. A newly vendored engine file arrives
        #    UNTRACKED, not modified, so `M`-only classification read it as
        #    somebody's uncommitted work: three source clones skipped their
        #    refresh, and the container scanner called the container unsafe
        #    on every reply. Planted on a clean clone so the two new shapes
        #    are the only dirt in it.
        fresh = tmp / 'fresh'
        subprocess.run(['git', 'clone', '--quiet', str(origin), str(fresh)],
                       capture_output=True, text=True)
        git(fresh, 'config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        git(fresh, 'config', 'user.name', 'Fixture')
        manifest_new = dict(manifest, files=['engine_a.py', 'engine_new.py'])
        (fresh / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(manifest_new), encoding='utf-8')
        (fresh / 'tools' / 'engine_new.py').write_text('just vendored\n',
                                                        encoding='utf-8')
        (fresh / 'MAP.md').write_text('regenerated\n', encoding='utf-8')
        (fresh / 'notes.md').write_text('mine, and new\n', encoding='utf-8')
        engine, other = rs.classify_dirt(fresh)
        cases.append(('an UNTRACKED file the manifest names is engine dirt, '
                      'not a person\'s uncommitted work',
                      'tools/engine_new.py' in engine
                      and 'tools/engine_new.py' not in other,
                      f'engine={engine} other={other}'))
        cases.append(('a regenerated MAP.md is engine dirt although no '
                      'manifest list names it',
                      'MAP.md' in engine and 'MAP.md' not in other,
                      f'engine={engine} other={other}'))
        cases.append(("negative control: an untracked file the manifest does "
                      "NOT name is still a person's",
                      'notes.md' in other and 'notes.md' not in engine,
                      f'engine={engine} other={other}'))
        cases.append(('negative control: AGENTS.md is not claimed -- only its '
                      'loader block is generated',
                      'AGENTS.md' not in rs.engine_owned_paths(fresh), ''))

        # 8b. THE LAG THE WIDENING ABOVE DID NOT CLOSE (2026-09-22, same
        #     day). Everything above reads the DESTINATION's manifest, which
        #     is a snapshot of its last refresh. A file added to ENGINE_FILES
        #     upstream is written into the clone before any manifest names
        #     it, so it was still classified as a person's work -- and the
        #     refresh that would record it is the very thing the
        #     misclassification skips, so the lag sustained itself.
        #     `precedent_container_safe.py` joined ENGINE_FILES on 2026-09-21
        #     and made the archive gate red on every reply in a real set the
        #     next day, about a file byte-identical to one already tracked
        #     and pushed upstream. Read off the engine's own lists, which do
        #     not lag.
        import precedent_vendor_engine as _ve
        lagging = sorted(set(_ve.ENGINE_FILES) - set(manifest_new['files']))[0]
        (fresh / 'tools' / lagging).write_text('newly vendored\n',
                                               encoding='utf-8')
        (fresh / 'tools' / 'my_own_script.py').write_text('mine\n',
                                                          encoding='utf-8')
        engine, other = rs.classify_dirt(fresh)
        cases.append((f'an engine file THIS manifest does not name yet '
                      f'({lagging}) is still engine dirt -- the engine\'s own '
                      f'lists do not lag the way a vendored snapshot does',
                      f'tools/{lagging}' in engine
                      and f'tools/{lagging}' not in other,
                      f'engine={engine} other={other}'))
        cases.append(("THE DISCRIMINATING CASE: a repo's OWN script under "
                      "tools/, named in neither engine list, is still a "
                      "person's work -- the widening adds engine names, it "
                      "does not claim tools/",
                      'tools/my_own_script.py' in other
                      and 'tools/my_own_script.py' not in engine,
                      f'engine={engine} other={other}'))
        (fresh / 'tools' / lagging).unlink()
        (fresh / 'tools' / 'my_own_script.py').unlink()

        # 8c. A SET'S DECLARED engine_paths (2026-10-01). precedent-individual
        #     keeps its own copies of two hooks in bootstrap/; the refresh
        #     writes them and records each, keyed by the local path, with the
        #     sha256 it wrote. engine_owned_paths read every manifest list but
        #     that one, so both hooks read as a person's work after every
        #     refresh and the archive gate went red on every reply. Owned only
        #     while the recorded hash still matches: these paths sit outside
        #     the engine's own directories, so a hand edit stays a person's.
        import hashlib as _hl
        #     TRACKED first, as in the real set: git reports a wholly
        #     untracked directory as the directory, never the file in it.
        (fresh / 'bootstrap').mkdir(exist_ok=True)
        hook = fresh / 'bootstrap' / 'commit-identity.sh'
        hook.write_text('as committed\n', encoding='utf-8')
        git(fresh, 'add', 'bootstrap/commit-identity.sh')
        git(fresh, 'commit', '--quiet', '-m', 'the set keeps its own hook')
        hook.write_text('refreshed\n', encoding='utf-8')
        manifest_ep = dict(
            manifest_new,
            engine_paths={'bootstrap/commit-identity.sh':
                          'templates/harness/claude-code/hooks/commit-identity.sh'},
            engine_paths_sha256={'bootstrap/commit-identity.sh':
                                 _hl.sha256(b'refreshed\n').hexdigest()})
        (fresh / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(manifest_ep), encoding='utf-8')
        engine, other = rs.classify_dirt(fresh)
        cases.append(('a declared engine path the refresh just wrote is '
                      'engine dirt, not a person\'s work',
                      'bootstrap/commit-identity.sh' in engine
                      and 'bootstrap/commit-identity.sh' not in other,
                      f'engine={engine} other={other}'))
        hook.write_text('refreshed, then edited by hand\n', encoding='utf-8')
        engine, other = rs.classify_dirt(fresh)
        cases.append(("negative control: the same path edited by hand after "
                      "the refresh is a person's again",
                      'bootstrap/commit-identity.sh' in other
                      and 'bootstrap/commit-identity.sh' not in engine,
                      f'engine={engine} other={other}'))
        git(fresh, 'reset', '--quiet', 'HEAD~1')      # keeps the dirt 9 uses
        hook.unlink()
        (fresh / 'bootstrap').rmdir()
        (fresh / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(manifest_new), encoding='utf-8')

        # 9. …and discarding it works. `git checkout --` fails outright on a
        #    path git has never tracked, so widening the classification
        #    without widening the discard would have turned a working
        #    refresh into a refusal.
        (origin / 'practices' / 'p.md').write_text('five\n', encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '--quiet', '-m', 'fifth')
        (fresh / 'notes.md').unlink()          # leave only engine dirt behind
        ok9, note9 = rs.make_current(fresh, 'main')
        counts9 = git(fresh, 'rev-list', '--left-right', '--count',
                      'origin/main...HEAD').stdout.split()
        cases.append(('a clone dirty with an UNTRACKED engine file is still '
                      'made current', ok9 and counts9 == ['0', '0'],
                      f'{note9} counts={counts9}'))
        cases.append(('and the untracked engine file was removed, for the '
                      'refresh that follows to write again',
                      not (fresh / 'tools' / 'engine_new.py').exists(),
                      'still there'))
        cases.append(('and the TRACKED generated view was restored, not '
                      'removed -- the two kinds of engine dirt take '
                      'different routes',
                      (fresh / 'MAP.md').is_file()
                      and 'regenerated' not in (fresh / 'MAP.md').read_text(),
                      'MAP.md is gone or still holds the stale render'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases, two refusals among them',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_source_sets_can_learn_they_are_stale():
    """A vendored source set must have some way to find out its engine is old.

    2026-09-06: `precedent-individual` and `precedent-team-tms` both sat at
    ef8b5d09 while this branch moved more than two hundred commits past it,
    and both were generating a loader block with a defect fixed upstream
    days earlier. Nothing was broken -- there was simply no channel through
    which "your copy is behind" could reach anyone. It surfaced because a
    session happened to have a clone attached and happened to run a check by
    hand.

    A CONSUMER repo never had this problem: it vendors process/upstream/ and
    its bootstrap runs a freshness check at session start. The asymmetry was
    the defect, and these cases assert the three channels that close it, so
    that removing any one of them fails here rather than going quiet for
    another two hundred commits.
    """
    cases = []

    # 1. No source template ships a scheduled workflow, and that is the
    #    decision, not an omission (2026-09-06). One was added here and
    #    pulled back out the same day: a cron job that phones a remote every
    #    week and opens pull requests is a real imposition on every adopter
    #    who inherits it, and a universal template is exactly the wrong place
    #    to make that choice for people. This case exists so the file cannot
    #    reappear here without someone deciding to put it back.
    #
    #    The 2026-09-06 comment here used to end "it lives at the individual
    #    level now, for whoever wants it". SUPERSEDED 2026-09-14: it lives
    #    nowhere. Morgan killed the weekly refresh outright -- "No weekly
    #    updates ... this is now really complex and deserves hand attention"
    #    -- after two scheduled runs produced two abandoned branches, a 100%
    #    report rate against a 0% landing rate. The replacement is a person
    #    saying "Update Vendors" by hand. So this assertion is no longer the
    #    narrow "not in a TEMPLATE" claim it was written as; it is now the
    #    universal one, and the individual-level copy it used to point at is
    #    being removed in the practice sets (not reachable from this repo).
    for level in ('individual', 'team'):
        wf = ROOT / 'templates' / f'practice-set-{level}' / '.github' / 'workflows' / 'engine-refresh.yml'
        cases.append((f'the {level} source template ships no scheduled workflow '
                      f'(no repository runs one, decided 2026-09-14)',
                      not wf.exists(), str(wf.relative_to(ROOT)) if wf.exists() else ''))

    # 2. The bootstrap tool warns when the clone it is seeding FROM is behind.
    bs = (ROOT / 'tools' / 'precedent_bootstrap_source.py').read_text(encoding='utf-8')
    cases.append(('bootstrap warns when seeding from a stale checkout',
                  '_warn_if_clone_is_stale' in bs and '_warn_if_clone_is_stale(network)' in bs, ''))

    # 3. A session working HERE is told about stale attached sources.
    tool = ROOT / 'tools' / 'precedent_refresh_sources.py'
    cases.append(('precedent_refresh_sources.py exists', tool.is_file(), ''))
    hook = (ROOT / '.claude' / 'hooks' / 'session-start.sh').read_text(encoding='utf-8')
    cases.append(('the session-start hook runs it',
                  'precedent_refresh_sources.py' in hook, ''))

    if tool.is_file():
        # Both directions, against real fixtures: a set recording this
        # checkout's own tip is current; one recording anything else is not.
        # Without the "current" case, a detector that called everything stale
        # would pass.
        import shutil, tempfile
        import importlib.util
        spec = importlib.util.spec_from_file_location('_prs', tool)
        prs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prs)
        tip, _ref = prs.head_commit()
        tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-staleness-'))
        try:
            def fake_set(name, commit):
                d = tmp / name
                (d / 'tools').mkdir(parents=True)
                (d / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    json.dumps({'format_version': 1, 'kind': 'source',
                                'source_commit': commit}), encoding='utf-8')
                return d
            if tip:
                current = fake_set('current-set', tip)
                stale = fake_set('stale-set', '0' * 40)
                # Refreshed in the working tree, older engine committed: the
                # state every set clone is in after a session-start refresh.
                held = fake_set('uncommitted-set', '1' * 40)
                for a in (['init', '-q', '-b', 'main'], ['add', '-A'],
                          ['-c', 'user.name=t', '-c', 'user.email=t@t',
                           'commit', '-qm', 'older engine']):
                    subprocess.run(['git', '-C', str(held), *a], capture_output=True)
                (held / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    json.dumps({'format_version': 1, 'kind': 'source',
                                'source_commit': tip}), encoding='utf-8')
                _t, _r, found = prs.survey([str(current), str(stale), str(held)])
                by = {e['repo'].name: e for e in found}
                cases.append(('a set recording this tip reports as current',
                              by.get('current-set', {}).get('stale') is False,
                              str(by.get('current-set'))))
                cases.append(('a set recording an older commit reports as STALE',
                              by.get('stale-set', {}).get('stale') is True,
                              str(by.get('stale-set'))))
                # The two hashes are BestPractice's, so the report names
                # BestPractice: beside a set's name, "origin/main is ..." read
                # as the set's own main (2026-09-30).
                import contextlib as _cl, io as _io
                real_survey = prs.survey
                prs.survey = lambda _extra: (tip, f'origin/{prs.SOURCE_BRANCH}',
                                             found)
                try:
                    buf = _io.StringIO()
                    with _cl.redirect_stdout(buf):
                        prs.main([])
                finally:
                    prs.survey = real_survey
                said = buf.getvalue()
                lines = [l for l in said.splitlines()
                         if l.strip().startswith(('STALE', 'ok'))
                         and ('current-set' in l or 'stale-set' in l)]
                cases.append(('each STALE and ok line names BestPractice as '
                              'the repo whose commits it compares',
                              len(lines) == 2 and all('BestPractice' in l
                                                      for l in lines),
                              failure_detail(said, 600)))
                held_line = next((l for l in said.splitlines()
                                  if 'uncommitted-set' in l), '')
                cases.append(('a refreshed working tree over an older committed '
                              'engine says both, and how it lands: Update '
                              'Vendors in that set (2026-10-01)',
                              'working tree current' in held_line
                              and 'committed engine is 111111111111' in held_line
                              and 'only in this container' in held_line
                              and '"Update Vendors" in uncommitted-set' in held_line,
                              held_line))
                cur_line = next((l for l in said.splitlines()
                                 if 'current-set' in l and 'uncommitted' not in l), '')
                cases.append(('...and a clone with nothing committed to compare '
                              'says engine current, as before',
                              'engine current' in cur_line, cur_line))
            else:
                cases.append(('the staleness fixtures could run (needs '
                              f'origin/{prs.SOURCE_BRANCH} fetched)', False,
                              'branch not resolvable in this clone'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a vendored source set can learn its engine is stale '
          f'({len(cases)} stated cases: no templated cron, bootstrap warning, '
          f'attached-source detector)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_a_person_with_no_individual_set_can_be_a_code_owner():
    """A person with no individual set is known by the administrator the
    installer was told (--admin), or by the GitHub account the session's
    token belongs to, so the practices for code owners reach them.

    Found 2026-10-17 by the very deep check's install rehearsal: with no
    individual set, viewer() knew only PRECEDENT_GITHUB_USER (documented
    nowhere an adopter reads), so the administrator who had just installed
    the project was a code owner nowhere and 28 practices stayed hidden,
    Update Vendors among them; --admin did not help. Decision chosen by the
    session under Morgan's delegation of 2026-10-17 ("Fix the other issues
    you found including the checks that never run. Tell me what you decide.
    I will be offline so don't wait for me. Approved, act, and Booked.").

    Negative control, measured 2026-10-17: on the code before the fix, the
    git-config and token cases below fail (not a code owner), and the
    nothing-known control fails only on naming PRECEDENT_GITHUB_USER.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-viewer-'))
    cases = []
    try:
        env = {**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        for k in ('PRECEDENT_GITHUB_USER', 'PRECEDENT_COMMIT_EMAIL'):
            env.pop(k, None)
        nobody = tmp / 'github-knows-nobody.json'
        nobody.write_text('{}', encoding='utf-8')
        env['PRECEDENT_GITHUB_USER_URL'] = nobody.as_uri()

        def repo(name):
            d = tmp / name
            subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
            (d / 'precedent.json').write_text(json.dumps(
                {'maintainers': [{'github': 'dana'}]}), encoding='utf-8')
            return d

        def audience(d, **extra):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_audience.py'),
                                '--repo', str(d)], capture_output=True, text=True,
                               env=dict(env, **extra))
            return r.stdout.strip()

        a = repo('nothing-known')
        out = audience(a)
        cases.append(('CONTROL: nothing known about the person -- in doubt, hidden, '
                      'and PRECEDENT_GITHUB_USER is named as a way to say who you are',
                      out.startswith('not a code owner:') and 'PRECEDENT_GITHUB_USER' in out,
                      out))
        b = repo('admin-recorded')
        subprocess.run(['git', '-C', str(b), 'config', 'precedent.githubLogin', 'dana'],
                       capture_output=True)
        out = audience(b)
        cases.append(("the login the installer kept in the clone's git config (--admin) "
                      'makes the administrator a code owner', out.startswith('code owner:'), out))
        c = repo('token-account')
        me = tmp / 'github-says-dana.json'
        me.write_text(json.dumps({'login': 'dana', 'id': 7}), encoding='utf-8')
        out = audience(c, PRECEDENT_GITHUB_USER_URL=me.as_uri())
        cases.append(("the account the session's token belongs to makes its owner a code owner",
                      out.startswith('code owner:'), out))
        kept = subprocess.run(['git', '-C', str(c), 'config', '--get', 'precedent.githubLogin'],
                              capture_output=True, text=True).stdout.strip()
        out = audience(c)
        cases.append(('...and it is kept, so the next session needs no lookup',
                      kept == 'dana' and out.startswith('code owner:'), f'{kept!r}: {out}'))
        out = audience(c, PRECEDENT_GITHUB_USER='someone-else')
        cases.append(('CONTROL: a declared username still outranks what was kept',
                      out.startswith('not a code owner:'), out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_set_bootstrap_defers_to_a_newer_engine_copy():
    """2026-10-19: an individual set's vendored precedent_source_bootstrap,
    from before "one tree per source", cloned a shared set into a second
    folder half an hour after the fix reached main. A set's copy now hands
    its run to the same file in a BestPractice clone strictly ahead of the
    commit the set's manifest records."""
    import subprocess as _sp
    import tempfile
    import precedent_source_bootstrap as psb
    cases = []
    url = 'https://github.com/alex137/BestPractice'
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        bp, st = t / 'BestPractice', t / 'set' / 'tools'
        (bp / 'tools').mkdir(parents=True); st.mkdir(parents=True)
        g = lambda *a: _sp.run(['git', '-C', str(bp), *a], capture_output=True, text=True)
        g('init', '-q'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        g('remote', 'add', 'origin', url + '.git')
        tool = bp / 'tools' / 'precedent_source_bootstrap.py'
        tool.write_text('# old\n'); g('add', '-A'); g('commit', '-qm', 'old')
        old = g('rev-parse', 'HEAD').stdout.strip()
        tool.write_text('# new\n'); g('commit', '-qam', 'new')
        new = g('rev-parse', 'HEAD').stdout.strip()
        man = lambda c, u=url: (st / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'source_commit': c, 'source_repo': u}))
        ask = lambda: psb.newer_engine_copy(here=st, candidates=[bp])
        man(old)
        cases.append(('a set vendored from an older commit defers to the clone\'s copy',
                      ask() == tool, ask()))
        man(new)
        cases.append(('CONTROL: a set on the clone\'s own commit runs its own copy',
                      ask() is None, ''))
        man('0' * 40)
        cases.append(('CONTROL: a recorded commit the clone lacks proves nothing',
                      ask() is None, ''))
        man(old, 'https://github.com/someone/Else')
        cases.append(('CONTROL: a clone of another repository is never used',
                      ask() is None, ''))
        man(old)
        os.environ[psb.DEFERRED_ENV] = '1'
        try:
            cases.append(('CONTROL: a run already deferred never defers again',
                          ask() is None, ''))
        finally:
            os.environ.pop(psb.DEFERRED_ENV, None)
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'a set\'s bootstrap defers to a newer engine copy ({len(cases)} stated cases)',
          not bad, '; '.join(map(str, bad)))


def check_source_clone_is_pinned_to_a_branch():
    """A source clone must not ask the remote which branch to use.

    `git clone <url> <dir>` with no --branch checks out whatever the server's
    HEAD symref names -- a setting on a web page, invisible to every tool
    here. 2026-09-09: two practice-source repositories had that setting
    pointed at a feature branch, so every session-start clone of them landed
    on an older tree, and a plain sync from a consuming repo would have
    written that older text over newer committed text, deleting a practice's
    Story block and a clause of its Rule, reporting success. The consuming
    repo had never been stale.

    Three cases, and the third is the one that decides whether the fix is
    safe rather than merely effective: a source clone can be somebody's
    working copy, and a pin that quietly moves a dirty checkout would trade
    one silent loss for another."""
    import tempfile
    import precedent_source_bootstrap as psb

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    def branch_of(p):
        return git(p, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()

    cases = []
    with tempfile.TemporaryDirectory() as td:
        W = pathlib.Path(td)
        src = W / 'src'
        src.mkdir()
        git(src, 'init', '-q', '-b', 'main')
        (src / 'rule.md').write_text('old\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        git(src, 'branch', 'claude/feature')
        (src / 'rule.md').write_text('NEWER, with the Story block\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'b')
        # The measured situation: the server's default is a feature branch
        # whose tree is behind main.
        git(src, 'symbolic-ref', 'HEAD', 'refs/heads/claude/feature')
        url = f'file://{src}'

        clone = W / 'clone'
        ok, out = psb._try_sync(url, clone)
        cases.append((f'a fresh clone lands on the pinned branch, not the '
                      f'remote\'s default (got {branch_of(clone)!r}, {out!r})',
                      ok and branch_of(clone) == 'main'))
        cases.append(('and therefore has the newer content the default branch '
                      'lacks',
                      'Story block' in (clone / 'rule.md').read_text(encoding='utf-8')))

        # An existing clone already sitting wrong: the half that made the real
        # incident persist, since `git pull --ff-only` pulls whatever branch
        # the checkout is on.
        #
        # Since 2026-10-07 it is reported, never moved, whoever made it: a
        # clone this tool made can be a session's working copy too, and one
        # set's Update Vendors switched another set's working branch to main
        # (todo-2026-10-07-one-sets-update-moves-another-sets-working-branch).
        git(clone, 'checkout', '-q', 'claude/feature')
        ok, out = psb._try_sync(url, clone)
        cases.append((f'an existing clone on another branch is left there and '
                      f'reported, with the command that moves it '
                      f'(got {branch_of(clone)!r}, {out!r})',
                      (not ok) and branch_of(clone) == 'claude/feature'
                      and f'checkout main' in out))
        # The working-branch shape itself: made locally from main, clean,
        # nothing committed yet -- what was switched that night.
        git(clone, 'checkout', '-q', '-b', 'session-update', 'main')
        ok, out = psb._try_sync(url, clone)
        cases.append((f'a clean branch a session just made is not switched '
                      f'(got {branch_of(clone)!r})',
                      (not ok) and branch_of(clone) == 'session-update'))
        git(clone, 'checkout', '-q', 'main')

        # Only a clone THIS tool made is moved (CLONE_MARKER). A checkout
        # the harness or a person made may be a session's working copy: a
        # practice set declares universal at ../BestPractice, and
        # BestPractice declares it at `.`, itself.
        cases.append(('a clone the tool made carries its marker',
                      psb._is_marked_clone(clone)))
        foreign = W / 'foreign'
        git(W, 'clone', '-q', '--branch', 'main', str(src), str(foreign))
        git(foreign, 'checkout', '-q', 'claude/feature')
        ok, out = psb._try_sync(url, foreign)
        cases.append((f'a checkout the tool did NOT make is left on its branch '
                      f'(got {branch_of(foreign)!r}, {out!r})',
                      (not ok) and branch_of(foreign) == 'claude/feature'
                      and "may be a session's working copy" in out))
        # ...and is still RECORDED as the source (2026-09-28): the refusal
        # protects the checkout, it must not take the source out of force.
        (foreign / 'practices').mkdir(exist_ok=True)
        cfg = W / 'config.json'
        ok, out = psb.ensure_source('individual', 'fixture-individual', url,
                                    foreign, cfg, retries=1, sleep=lambda s: None)
        recorded = (json.loads(cfg.read_text(encoding='utf-8'))
                    .get('individual', {}).get('path') if cfg.exists() else None)
        cases.append((f'an individual checkout left on its branch is still '
                      f'recorded as the source (ok={ok}, path={recorded!r}, '
                      f'{out!r})',
                      ok and recorded is not None
                      and pathlib.Path(recorded).resolve() == foreign.resolve()
                      and branch_of(foreign) == 'claude/feature'))
        itself = W / 'itself'
        git(W, 'clone', '-q', '--branch', 'main', str(src), str(itself))
        (itself / 'practices').mkdir()
        (itself / 'precedent.json').write_text(json.dumps({
            'base_branch': 'main', 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        git(itself, 'checkout', '-q', 'claude/feature')
        res = psb.sources_from_repo(itself)
        cases.append((f'a source declared at `.` does not move the repo itself '
                      f'(got {branch_of(itself)!r}, {res!r})',
                      branch_of(itself) == 'claude/feature'
                      and res and 'declared inside this repository' in res[0][2]))

        git(clone, 'checkout', '-q', 'claude/feature')
        (clone / 'rule.md').write_text('work nobody committed\n', encoding='utf-8')
        ok, out = psb._try_sync(url, clone)
        cases.append(('a wrong-branch clone with uncommitted work is REFUSED, '
                      'naming both branches, not silently moved',
                      (not ok) and 'claude/feature' in out and "'main'" in out))
        cases.append(('and that uncommitted work is still there',
                      'work nobody committed' in
                      (clone / 'rule.md').read_text(encoding='utf-8')))

        # THE ONE CASE THE PIN GIVES WAY. A source whose only branch is
        # named something else must still clone: git's default branch name is
        # per-machine, so whoever created that set may never have decided it,
        # and refusing would take its practices out of force for a naming
        # accident. Distinct from the incident, where the pinned branch DID
        # exist and the remote's default named a different one.
        other = W / 'other'
        other.mkdir()
        git(other, 'init', '-q', '-b', 'master')
        (other / 'r.md').write_text('x\n', encoding='utf-8')
        git(other, 'add', '-A')
        git(other, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        oc = W / 'other-clone'
        ok, out = psb._try_sync(f'file://{other}', oc)
        cases.append((f'a source with no branch of that name clones anyway '
                      f'rather than falling out of force (got '
                      f'{branch_of(oc) if oc.exists() else None!r}, {out!r})',
                      ok and branch_of(oc) == 'master'))

    failed = [n for n, ok in cases if not ok]
    check(f'a source clone is pinned to a branch rather than asking the '
          f'remote ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_generator_wires_every_template_guard_mode():
    """The generator must not fall behind the adapter template again.

    Three files describe how session hooks get wired: the adapter template
    at templates/harness/claude-code/settings.json, whose own _comment calls
    itself the canonical wiring; this repo's .claude/settings.json,
    dogfooding it; and _install_session_hooks() in
    precedent_bootstrap_source.py, which is what a newly bootstrapped source
    actually receives. The third fell behind the first around 2026-09-06 --
    it wired SessionStart and PreToolUse and not UserPromptSubmit -- so every
    set bootstrapped after that date silently lacked the freshness guard's
    `user-prompt` mode. That is the only mode that keeps firing: SessionStart
    is spent at the start and pre-write at the first write, so a session left
    open across a break has spent both and nothing rechecks the checkout
    however far origin moves underneath it. All five real downstream sets sat
    in that state for days and none of them knew.

    NOT strict equality, deliberately. The adapter legitimately wires MORE
    than the generator installs -- a Stop hook, session-start.sh,
    precedent-paths.sh -- so asserting the same event set would fail on
    arrival and force an unrelated design decision about which of those a
    bootstrapped set should get. The assertion is CONTAINMENT of the guard's
    modes, plus commit-identity.sh wired on both sides.

    Modes, never whole command strings: the base branch is passed explicitly
    and differs per repo on purpose -- this repo's own base is
    precedent-beta-v01, not main -- so comparing commands would report that
    deliberate difference as drift.

    Both sides are derived at runtime. A hardcoded list of expected modes
    would be a FOURTH copy of this wiring, and copies of this wiring drifting
    from one another is the exact failure being checked."""
    import tempfile
    import precedent_bootstrap_source as pbs
    cases = []
    want = pbs._template_guard_modes()
    cases.append(('the adapter template wires at least one guard mode, so '
                  'there is something to compare against', bool(want)))
    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        pbs._install_session_hooks(dest, 'main')
        have = pbs._source_guard_modes(dest)
        gap = sorted(want - have)
        cases.append((f'the generator wires every guard mode the adapter '
                      f'does (missing: {gap or "none"})', not gap))

        settings = dest / '.claude' / 'settings.json'
        tmpl_text = (ROOT / 'templates' / 'harness' / 'claude-code'
                     / 'settings.json').read_text(encoding='utf-8')
        gen_text = settings.read_text(encoding='utf-8')
        cases.append(('commit-identity.sh is wired by the adapter and by the '
                      'generator alike',
                      'commit-identity.sh' in tmpl_text
                      and 'commit-identity.sh' in gen_text))

        # A hook that is not executable silently never runs, which is why
        # _install_session_hooks chmods; assert the property, not the call.
        cases.append(('both installed hooks are executable',
                      all(os.access(dest / '.claude' / 'hooks' / n, os.X_OK)
                          for n in pbs.SESSION_HOOKS)))

        # The negative control, run rather than asserted in a report: with
        # the UserPromptSubmit block taken back out, the comparison above has
        # to name exactly the mode that went (practice:
        # control-asserts-which-failure -- a check that cannot fail is not a
        # check, and "it failed" is not evidence it failed for the reason
        # claimed).
        data = json.loads(gen_text)
        data['hooks'].pop('UserPromptSubmit', None)
        settings.write_text(json.dumps(data), encoding='utf-8')
        reverted = sorted(want - pbs._source_guard_modes(dest))
        cases.append((f'with the UserPromptSubmit wiring removed the same '
                      f'comparison names exactly user-prompt (got '
                      f'{reverted})', reverted == ['user-prompt']))

    failed = [n for n, ok in cases if not ok]
    check(f'the generator wires every guard mode the adapter template does '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_session_check_reports_a_dead_also_list_entry():
    """The also-list fails SILENTLY by design, so something has to say so.

    An entry naming a path that is not there is skipped with a note and never
    blocked on -- a config typo must not wedge a session. The cost is that a
    variable which looks set reads as coverage while covering nothing, which
    is exactly what this project's own environment did: it named
    /home/user/precedent-individual while the clone was at
    /root/precedent-individual, and skipped it every session from the day the
    variable was first set until 2026-09-11. Nothing was broken enough to
    notice (practice: checkable-gets-checked).

    The row must agree with the guard rather than approximate it -- both
    expand the same way, or the check passes a value the guard then drops --
    so the expansion is asserted directly here, both the forms that must
    resolve and the absent path that must NOT be rescued by expanding."""
    import precedent_session_check as psc

    cases = []
    home, proj = '/tmp/fixture-home', '/tmp/fixture-proj'
    saved = {k: os.environ.get(k)
             for k in ('HOME', 'CLAUDE_PROJECT_DIR', 'PRECEDENT_FRESHNESS_ALSO')}
    # (Since 2026-10-03 the row never offers a value to set; the pinned list
    # below stays so neither case can pass by reading this machine.)
    # The row's "Set it to: ..." half existed only when there was something to
    # suggest, and what there is to suggest is whatever clones happen to sit
    # beside this checkout. Asserting that text while leaving the machine to
    # decide it is a fixture that passes on a developer's container (sibling
    # sources on disk) and fails in CI (none), which is exactly what it did.
    # Own it instead: pin the source list, and assert the empty case too,
    # since an environment with nothing attachable is a real one
    # (practice: fixture-owns-its-state).
    saved_sources = psc._attachable_sources
    psc._attachable_sources = lambda: [('/fixture/src', 'main')]
    try:
        os.environ['HOME'] = home
        os.environ['CLAUDE_PROJECT_DIR'] = proj
        for written, want in (('~/precedent-individual',
                               f'{home}/precedent-individual'),
                              ('$HOME/x', f'{home}/x'),
                              ('${HOME}/x', f'{home}/x'),
                              ('~', home),
                              ('$CLAUDE_PROJECT_DIR/x', f'{proj}/x'),
                              ('/already/absolute', '/already/absolute')):
            got = psc._expand_source_path(written)
            cases.append((f'{written!r} expands to {want!r} (got {got!r})',
                          got == want))

        # A tilde that is not a path prefix is not a home reference -- and a
        # path is allowed to legitimately contain one.
        got = psc._expand_source_path('/opt/a~b')
        cases.append((f"'/opt/a~b' is left alone (got {got!r})",
                      got == '/opt/a~b'))

        # The row itself, in the three states that matter. Names, not exit
        # codes: several rows can be red at once
        # (practice: control-asserts-which-failure).
        def row():
            for name, ok, detail in psc.checks():
                if 'PRECEDENT_FRESHNESS_ALSO' in name:
                    return ok, detail
            return 'MISSING', ''

        os.environ['PRECEDENT_FRESHNESS_ALSO'] = '/definitely/not/here=main'
        ok, detail = row()
        # Never a value to set instead (2026-10-03): the guard checks every
        # declared set on its own since 2026-09-30, so a suggested value naming
        # them was the stale advice a session reported. Drop the entry.
        cases.append((f'a dead entry is reported NOT in effect, naming the '
                      f'path and saying to drop it, never a value to set '
                      f'(ok={ok!r})',
                      ok is False and '/definitely/not/here' in detail
                      and 'Drop each' in detail
                      and 'PRECEDENT_FRESHNESS_ALSO=' not in detail))

        os.environ['PRECEDENT_FRESHNESS_ALSO'] = 'no-equals-sign'
        ok, detail = row()
        cases.append((f'an entry with no =<base branch> is reported too '
                      f'(ok={ok!r})',
                      ok is False and 'no =<base branch>' in detail))

        del os.environ['PRECEDENT_FRESHNESS_ALSO']
        ok, detail = row()
        # Since 2026-09-30 the guard checks every DECLARED set without the
        # variable, so unset is fine; the row says the variable is only for
        # repositories nothing declares.
        cases.append((f'unset is fine now -- the guard checks declared sets '
                      f'itself (ok={ok!r})',
                      ok is True and 'not set' in detail
                      and 'declare' in detail))

        # With nothing attachable there is nothing to suggest, and the row
        # must still be red and still name the dead path -- the finding is
        # the point, the suggestion is a convenience.
        psc._attachable_sources = lambda: []
        os.environ['PRECEDENT_FRESHNESS_ALSO'] = '/definitely/not/here=main'
        ok, detail = row()
        cases.append((f'a dead entry is still reported when there is nothing '
                      f'to suggest (ok={ok!r})',
                      ok is False and '/definitely/not/here' in detail
                      and 'Set it to:' not in detail))
        psc._attachable_sources = lambda: [('/fixture/src', 'main')]

        # THE CONTROL. A real repository on disk must NOT be reported dead,
        # or the row is just "always red" and says nothing.
        os.environ['HOME'] = saved['HOME'] or home
        os.environ['PRECEDENT_FRESHNESS_ALSO'] = f'{ROOT}=main'
        ok, detail = row()
        cases.append((f'an entry naming a real repository passes (ok={ok!r}, '
                      f'{detail[:60]!r})', ok is True))
    finally:
        psc._attachable_sources = saved_sources
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    failed = [n for n, ok in cases if not ok]
    check(f'the session check reports an also-list entry that names nothing '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_session_check_covers_the_universal_clone():
    """The source-clone freshness row read only directories named
    precedent-*, so a practice set's ../BestPractice sat 224 commits behind
    its origin while every set reported current (2026-09-30). Planted with
    real git: a set declaring `../BestPractice`, whose clone is one commit
    behind its origin's main, while the clone's own precedent.json declares
    another base branch. Discriminating cases: the declared universal clone
    is listed and judged at main, not at its own base_branch; the row
    reports it behind with a fast-forward-only remedy; and the clone itself
    is left exactly where it was."""
    import shutil, subprocess, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_check as psc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='universal-clone-'))
    saved_root, saved_att = psc.ROOT, psc._attachable_sources
    cases = []
    try:
        def git(*a, cwd=tmp):
            return subprocess.run(['git', '-c', 'user.name=T', '-c',
                                   'user.email=t@t', *a], cwd=str(cwd),
                                  capture_output=True, text=True)
        up = tmp / 'up.git'
        work = tmp / 'work'
        git('init', '-q', '--bare', '-b', 'main', str(up))
        git('clone', '-q', str(up), str(work))
        (work / 'precedent.json').write_text(
            json.dumps({'base_branch': 'staging'}), encoding='utf-8')
        git('add', '-A', cwd=work)
        git('commit', '-qm', 'one', cwd=work)
        git('push', '-q', 'origin', 'HEAD:main', cwd=work)
        clone = tmp / 'BestPractice'
        git('clone', '-q', '-b', 'main', str(up), str(clone))
        (work / 'x').write_text('two\n', encoding='utf-8')
        git('add', '-A', cwd=work)
        git('commit', '-qm', 'two', cwd=work)
        git('push', '-q', 'origin', 'HEAD:main', cwd=work)
        before = git('rev-parse', 'HEAD', cwd=clone).stdout.strip()
        setdir = tmp / 'precedent-a-set'
        setdir.mkdir()
        (setdir / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent',
             'path': '../BestPractice'}]}), encoding='utf-8')
        psc.ROOT = setdir
        psc._attachable_sources = lambda: []
        declared = psc._declared_source_clones()
        cases.append(('the declared universal clone is listed, judged at main',
                      declared == [(str(clone.resolve()), 'main')],
                      repr(declared)))
        row = [r for r in psc.checks() if 'current with its own origin' in r[0]]
        ok, detail = (row[0][1], str(row[0][2])) if row else ('MISSING', '')
        cases.append(('THE CASE THIS EXISTS FOR: the row reports it behind, '
                      'with a fast-forward-only remedy',
                      ok is False and 'BestPractice' in detail
                      and 'merge --ff-only origin/main' in detail, detail[:400]))
        cases.append(('...and the clone is left where it was',
                      git('rev-parse', 'HEAD', cwd=clone).stdout.strip() == before,
                      ''))
    finally:
        psc.ROOT, psc._attachable_sources = saved_root, saved_att
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session check covers the universal clone a set declares '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_session_check_never_calls_an_unfetched_clone_current():
    """A source clone that never fetched must not report itself current.

    THE INCIDENT, 2026-09-23. `_clone_behind` compared each clone against
    its own remote-tracking ref and never fetched, so a clone that had not
    fetched since it was made measured itself against its own stale copy of
    origin, counted zero, and the row said CURRENT. This container's
    precedent-shared-working-style clone sat six commits behind for a whole
    session that way. Two practices that had been MOVED into that set read
    as present in no source at all, and the session told its user three
    times that two rules had been silently switched off. They had not been;
    the copies had landed upstream hours earlier.

    So the row has three states now, and this pins all three. The one that
    must never come back is a silent True.

    Everything is stubbed rather than read off the machine: a fixture that
    lets the container decide passes on a developer box and fails in CI
    (practice: fixture-owns-its-state)."""
    import tempfile
    import precedent_session_check as psc

    cases = []
    name_wanted = 'clone is current with its own origin'
    saved_sources = psc._attachable_sources
    saved_behind = psc._clone_behind

    def row(offline=False):
        for name, ok, detail in psc.checks(offline=offline):
            if name_wanted in name:
                return ok, str(detail)
        return 'MISSING', ''

    try:
        psc._attachable_sources = lambda: [('~/precedent-individual', 'main')]

        # A fetch happened and there is nothing to take -> the only True.
        psc._clone_behind = lambda path, fetch=True, **_kw: ('current', '')
        ok, _ = row()
        cases.append(('a clone confirmed current by a real fetch passes',
                      ok is True, ''))

        # THE REGRESSION THIS EXISTS FOR: nothing fetched, so "zero commits
        # behind" means nothing. Undetermined, never green.
        psc._clone_behind = lambda path, fetch=True, **_kw: (
            'unverified', 'not fetched -- offline path')
        ok, detail = row()
        cases.append(('a clone that could not be compared is NOT reported '
                      'current', ok is None, f'ok={ok!r}'))
        cases.append(('and the row says it is unmeasured rather than clean',
                      'UNMEASURED' in detail, detail[:90]))

        # Behind stays a hard failure, including off a stale ref.
        psc._clone_behind = lambda path, fetch=True, **_kw: (
            'behind', '6 commit(s) behind origin/main')
        ok, detail = row()
        cases.append(('a clone measured behind still fails',
                      ok is False and '6 commit(s)' in detail, detail[:90]))

        # The offline path must not fetch -- that is the whole reason it
        # exists -- and must still be capable of reporting a positive
        # "behind" reading.
        seen = {}

        def _spy(path, fetch=True, **_kw):
            seen['fetch'] = fetch
            return 'behind', '2 commit(s) behind origin/main'

        psc._clone_behind = _spy
        ok, _ = row(offline=True)
        cases.append(('the offline path asks for no fetch',
                      seen.get('fetch') is False, repr(seen)))
        cases.append(('and still reports a clone it can see is behind',
                      ok is False, f'ok={ok!r}'))
    finally:
        psc._attachable_sources = saved_sources
        psc._clone_behind = saved_behind

    # AND THE FUNCTION ITSELF, against real git rather than a stub. The
    # cases above pin the ROW's three states; this pins the thing that
    # actually broke -- that `_clone_behind` fetches before it compares. A
    # stub cannot show that, and a stub is what would have let the original
    # bug through: every caller was correct, the comparison was simply made
    # against a ref nothing had refreshed.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='clone-behind-'))
    try:
        upstream, clone = tmp / 'upstream', tmp / 'clone'
        def g(cwd, *a):
            subprocess.run(['git', '-C', str(cwd), *a], check=True,
                           capture_output=True)
        upstream.mkdir()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(upstream)],
                       check=True, capture_output=True)
        g(upstream, 'config', 'user.email', 'harness@example.com')
        g(upstream, 'config', 'user.name', 'harness')
        (upstream / 'f.txt').write_text('one\n')
        g(upstream, 'add', '-A')
        g(upstream, 'commit', '-qm', 'one')
        subprocess.run(['git', 'clone', '-q', str(upstream), str(clone)],
                       check=True, capture_output=True)
        # The clone is current and has fetched: the only shape that is True.
        v, _ = psc._clone_behind(str(clone), fetch=True)
        cases.append(('a freshly cloned tree reads as current',
                      v == 'current', v))
        # Upstream moves. The clone has NOT fetched, so its own
        # remote-tracking ref still says zero -- the exact bug.
        (upstream / 'f.txt').write_text('two\n')
        g(upstream, 'add', '-A')
        g(upstream, 'commit', '-qm', 'two')
        v_off, _ = psc._clone_behind(str(clone), fetch=False)
        cases.append(('WITHOUT a fetch a stale clone is unverified, never '
                      'current', v_off == 'unverified', v_off))
        v_on, phrase = psc._clone_behind(str(clone), fetch=True)
        cases.append(('WITH a fetch the same clone is measured behind',
                      v_on == 'behind' and '1 commit' in phrase,
                      f'{v_on}: {phrase}'))
        # ON ITS OWN LANDING LINE (2026-10-18): a set declaring base main
        # and landing staging, checked out at origin/staging while main
        # carries a direct commit staging lacks, is current -- and the same
        # clone behind origin/staging is still behind.
        (upstream / 'precedent.json').write_text(
            '{"base_branch": "main", "landing_branch": "staging"}\n')
        g(upstream, 'add', '-A')
        g(upstream, 'commit', '-qm', 'declare')
        g(upstream, 'branch', 'staging')
        g(upstream, 'checkout', '-q', 'staging')
        (upstream / 's.txt').write_text('staged\n')
        g(upstream, 'add', '-A')
        g(upstream, 'commit', '-qm', 'staged work')
        g(upstream, 'checkout', '-q', 'main')
        (upstream / 'm.txt').write_text('direct\n')
        g(upstream, 'add', '-A')
        g(upstream, 'commit', '-qm', 'direct to main')
        g(clone, 'fetch', '-q', 'origin',
          '+refs/heads/staging:refs/remotes/origin/staging')
        g(clone, 'checkout', '-q', '-B', 'work', 'origin/staging')
        v_l, phrase = psc._clone_behind(str(clone), fetch=True)
        cases.append(('a clone at its own landing branch, behind only what '
                      'main has and staging lacks, is current',
                      v_l == 'current' and 'origin/staging' in phrase,
                      f'{v_l}: {phrase}'))
        v_m, phrase = psc._clone_behind(str(clone), fetch=True, branch='main')
        cases.append(('the same clone read at a caller-named main is behind',
                      v_m == 'behind', f'{v_m}: {phrase}'))
        cases.append(('CONTROL: a branch carrying what main lacks is not '
                      'called landed', 'has landed' not in phrase, phrase))
        # A LANDED BRANCH LEFT CHECKED OUT (2026-11-01): still behind, and
        # the phrase says it landed and gives the one move back to base.
        g(clone, 'fetch', '-q', 'origin', '+refs/heads/main:refs/remotes/origin/main')
        g(clone, 'checkout', '-q', '-B', 'landed', 'origin/main~1')
        v_d, phrase = psc._clone_behind(str(clone), fetch=True, branch='main')
        cases.append(('a landed branch left checked out is behind, and says it '
                      'landed and how to go back',
                      v_d == 'behind' and 'checked out on landed, which has '
                      'landed' in phrase and f'git -C {clone} switch main' in phrase,
                      f'{v_d}: {phrase}'))
        g(clone, 'checkout', '-q', '-B', 'work', 'origin/staging~1')
        v_b, phrase = psc._clone_behind(str(clone), fetch=True)
        cases.append(('a clone behind its own landing branch is still behind',
                      v_b == 'behind', f'{v_b}: {phrase}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_session_check_stamps_at_session_start():
    """The "still on the branch it started on" row takes its baseline from
    the session-start hook, and a move onto a tier branch after the work
    landed is normal; a move that strands work still fails.

    WHY. 2026-10-09, a consumer: the baseline was written by the check's
    first run, mid-session on a feature branch, and after a promote left
    the checkout on main the row said "started on <feature>, now on main",
    wrong on both counts."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_check as psc
    cases = []
    for f in ('tools/bootstrap.sh', 'templates/bootstrap.sh',
              '.claude/hooks/session-start.sh'):
        cases.append((f'{f} records the start (--stamp-start)',
                      '--stamp-start' in (ROOT / f).read_text(encoding='utf-8'), ''))
    with tempfile.TemporaryDirectory() as t:
        repo = pathlib.Path(t) / 'repo'
        repo.mkdir()

        def git(*args):
            p = subprocess.run(['git', '-C', str(repo), *args],
                               capture_output=True, text=True)
            return p.returncode, p.stdout.strip(), p.stderr.strip()

        def commit(msg, name='f'):
            (repo / name).write_text(msg)
            git('add', '-A')
            git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', msg)

        git('init', '-q', '-b', 'main')
        commit('one')
        git('branch', 'staging')
        git('checkout', '-q', '-b', '2026-10-09-feature-abcde')
        stamp = psc.session_stamp_path(git)
        stamp.write_text('somewhere-else\n0000\n')
        cases.append(('the session-start stamp overwrites an older record with '
                      'the branch the session starts on',
                      psc.stamp_session_start(stamp, git)
                      and stamp.read_text().split()[0] == '2026-10-09-feature-abcde',
                      stamp.read_text()))
        commit('feature work', 'g')
        # Promoted: merged into staging (and origin's copy), and main
        # takes the same content as a commit of its own, not a merge.
        git('checkout', '-q', 'staging')
        git('-c', 'user.name=t', '-c', 'user.email=t@t', 'merge', '-q', '--no-ff',
            '-m', 'land', '2026-10-09-feature-abcde')
        git('update-ref', 'refs/remotes/origin/staging', 'staging')
        git('checkout', '-q', 'main')
        commit('feature work, copied onto main', 'g')
        r = psc._session_branch_row(stamp, git)
        cases.append(('after a promote leaves the checkout on main, the row '
                      'passes: the start branch\'s work is on a tier',
                      bool(r) and r[1] is True and 'tier branch' in r[2], str(r)))
        # Stranded: a new start branch with work on no tier, then main.
        git('checkout', '-q', '-b', '2026-10-09-other-abcde')
        psc.stamp_session_start(stamp, git)
        commit('unmerged work', 'h')
        git('checkout', '-q', 'main')
        r = psc._session_branch_row(stamp, git)
        cases.append(('a move onto main that leaves work on no tier still fails',
                      bool(r) and r[1] is False, str(r)))
        # A linked worktree: the stamp lives in its own git directory.
        wt = pathlib.Path(t) / 'wt'
        git('worktree', 'add', '-q', '-b', 'wt-branch', str(wt), 'main')

        def wgit(*args):
            p = subprocess.run(['git', '-C', str(wt), *args],
                               capture_output=True, text=True)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        path = psc.session_stamp_path(wgit)
        cases.append(('in a linked worktree the stamp goes in its own git '
                      'directory, which exists', path.parent.is_dir()
                      and psc.stamp_session_start(path, wgit), str(path)))
    sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session check takes its baseline from session start '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_session_check_adopts_a_detached_start():
    """A cloud session starts detached and moves onto its branch: not a jump.

    Found 2026-09-30 on a dependent repo's cloud session: the stamp recorded
    `HEAD` (git's name for a detached checkout), the harness then moved the
    session onto its assigned branch, and the row failed on every prompt for
    the life of the session. A warning that fires every time is one nobody
    reads, which is how the real jump it exists for would slip past.

    The rule under test: a detached start adopts the branch it moves onto
    when that branch carries the start commit, and still fails when it does
    not; a move between named branches still fails. Driven against a
    throwaway repository, never this checkout (practice:
    fixture-owns-its-state)."""
    import subprocess
    import tempfile
    import precedent_session_check as psc

    cases = []
    with tempfile.TemporaryDirectory() as t:
        repo = pathlib.Path(t)

        def git(*args):
            p = subprocess.run(['git', '-C', str(repo), *args],
                               capture_output=True, text=True)
            return p.returncode, p.stdout.strip(), p.stderr.strip()

        def commit(msg):
            (repo / 'f').write_text(msg)
            git('add', 'f')
            git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', msg)

        git('init', '-q', '-b', 'main')
        commit('one')
        stamp = repo / '.git' / 'precedent-session-branch'

        def row():
            r = psc._session_branch_row(stamp, git)
            return (r[1], r[2]) if r else ('MISSING', '')

        # Detached start: the first run records HEAD and the commit.
        _, c1, _ = git('rev-parse', 'HEAD')
        git('checkout', '-q', '--detach')
        ok, detail = row()
        cases.append(('the first run records a baseline', ok is None, detail))
        cases.append(('the stamp carries the start commit',
                      c1 in stamp.read_text(), stamp.read_text()))

        # The harness moves the session onto its branch: passes, and adopts.
        git('checkout', '-q', '-b', 'claude/work')
        ok, detail = row()
        cases.append(('a detached start moving onto a branch that carries it passes',
                      ok is True, detail))
        cases.append(('the branch becomes the new baseline',
                      stamp.read_text().split()[0] == 'claude/work',
                      stamp.read_text()))
        ok, detail = row()
        cases.append(('and stays green on the next run', ok is True, detail))

        # A later jump between named branches, leaving work behind on the
        # one it started on, is still the finding it was.
        commit('work on claude/work that main lacks')
        git('checkout', '-q', 'main')
        ok, detail = row()
        cases.append(('a move between named branches that strands work still fails',
                      ok is False and 'claude/work' in detail, detail))

        # Booked merged it, and the session moved onto the branch that now
        # carries it: carried, not stranded (2026-10-01).
        git('-c', 'user.name=t', '-c', 'user.email=t@t', 'merge', '-q',
            '--no-ff', '-m', 'Booked', 'claude/work')
        ok, detail = row()
        cases.append(('a move onto a branch that carries all of the start '
                      'branch passes', ok is True and 'carries all' in detail, detail))
        cases.append(('...and that branch becomes the baseline',
                      stamp.read_text().split()[0] == 'main', stamp.read_text()))

        # A named start, then the session's own new branch from it: passes.
        import time as _time
        git('checkout', '-q', 'main')
        _, c_main, _ = git('rev-parse', 'HEAD')
        stamp.write_text(f'main\n{c_main}\n')
        os.utime(stamp, (_time.time() - 60, _time.time() - 60))
        git('checkout', '-q', '-b', 'claude/own-feature')
        ok, detail = row()
        cases.append(("a named start moving onto the session's own new branch passes",
                      ok is True and 'created' in detail, detail))
        cases.append(('and that branch becomes the baseline',
                      stamp.read_text().split()[0] == 'claude/own-feature',
                      stamp.read_text()))

        # The ladder's move: the session starts on main and branches from
        # staging, which lacks main's newest commit (2026-10-01).
        git('checkout', '-q', 'main')
        git('branch', '-f', 'staging', 'HEAD')
        git('branch', '-f', 'side', 'HEAD')
        commit('main moves on: a Produce merge staging lacks')
        _, c_main, _ = git('rev-parse', 'HEAD')
        stamp.write_text(f'main\n{c_main}\n')
        os.utime(stamp, (_time.time() - 60, _time.time() - 60))
        git('checkout', '-q', '-b', 'claude/ladder', 'staging')
        ok, detail = row()
        cases.append(('a new branch made from staging, which lacks the '
                      'start commit, passes', ok is True, detail))
        # The same move as a cloud session makes it, from origin's copy
        # (`git checkout -b feat origin/staging`).
        git('checkout', '-q', 'main')
        git('update-ref', 'refs/remotes/origin/staging', 'staging')
        stamp.write_text(f'main\n{c_main}\n')
        os.utime(stamp, (_time.time() - 60, _time.time() - 60))
        git('checkout', '-q', '-b', 'claude/ladder-origin', 'origin/staging')
        ok, detail = row()
        cases.append(('...and so does one made from origin/staging',
                      ok is True, detail))
        git('checkout', '-q', 'main')
        stamp.write_text(f'main\n{c_main}\n')
        os.utime(stamp, (_time.time() - 60, _time.time() - 60))
        git('checkout', '-q', '-b', 'claude/off-side', 'side')
        ok, detail = row()
        cases.append(('...but one made from a non-tier branch that lacks it '
                      'still fails', ok is False, detail))
        git('checkout', '-q', 'main')

        # A branch that existed before the stamp is still a jump.
        git('branch', 'older-branch', 'main')
        stamp.write_text(f'main\n{c_main}\n')
        os.utime(stamp, (_time.time() + 60, _time.time() + 60))
        git('checkout', '-q', 'older-branch')
        ok, detail = row()
        cases.append(('a move onto a branch that existed before the session still fails',
                      ok is False and 'older-branch' in detail, detail))
        git('checkout', '-q', 'main')

        # A detached start whose commit the new branch lacks still fails.
        git('checkout', '-q', '--detach', 'claude/work')
        commit('made while detached')
        _, c2, _ = git('rev-parse', 'HEAD')
        stamp.write_text(f'HEAD\n{c2}\n')
        git('checkout', '-q', 'main')
        ok, detail = row()
        cases.append(('a branch that strands the detached commit still fails',
                      ok is False and c2[:12] in detail, detail))

        # Detached at a commit origin already has (main's tip, a Produce merge)
        # and work cut from staging, which lacks it: nothing is stranded
        # (2026-10-17, a false warning at every turn).
        git('update-ref', 'refs/remotes/origin/main', 'main')
        _, c_main_tip, _ = git('rev-parse', 'main')
        stamp.write_text(f'HEAD\n{c_main_tip}\n')
        git('checkout', '-q', '-B', 'claude/from-staging', 'staging')
        ok, detail = row()
        cases.append(('a detached start at a commit origin has, then a branch '
                      'cut from staging that lacks it, passes',
                      ok is True and 'already has' in detail, detail))
        git('checkout', '-q', 'main')
        git('update-ref', '-d', 'refs/remotes/origin/main')

        # An older one-line stamp recording HEAD is adopted, not failed.
        stamp.write_text('HEAD\n')
        ok, detail = row()
        cases.append(('an older one-line detached stamp is adopted',
                      ok is True, detail))

    bad = [(n, d) for n, good, d in cases if not good]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_session_check_reports_a_source_cloned_twice():
    """Two clones of one practice source is the quietest failure there is.

    Everything keeps working -- the resolver picks one, the freshness guard
    checks whichever the also-list names, a session edits whichever
    directory it landed in -- and nothing says the other exists. Then they
    diverge and a practice written this morning is simply not in force,
    with no error anywhere to read.

    Found 2026-09-21 on this project's own container: three shared sets
    cloned twice, once under $HOME and once beside this checkout, and one
    of the three already divergent between its copies. The tell was in the
    also-list suggestion, which was honestly naming seven entries for four
    sources.

    The source list is pinned rather than read off the machine, for the
    reason the row above this one records: a fixture that lets the
    container decide passes on a developer box and fails in CI
    (practice: fixture-owns-its-state)."""
    import precedent_session_check as psc

    cases = []
    name_wanted = 'cloned exactly once'
    saved_sources = psc._attachable_sources
    saved_head = psc._git_head

    def row():
        # offline: the row under test is local; only the fetch row is dropped.
        for name, ok, detail in psc.checks(offline=True):
            if name_wanted in name:
                return ok, detail
        return 'MISSING', ''

    try:
        # One clone each -> the row is green.
        psc._attachable_sources = lambda: [('~/precedent-individual', 'main'),
                                           ('/elsewhere/precedent-team', 'main')]
        psc._git_head = lambda path: (0, 'aaaaaaa')
        ok, detail = row()
        cases.append(('one clone per source passes', ok is True, str(detail)))

        # Two clones, same head -> still a finding: agreeing today says
        # nothing about tomorrow, and only one of them is being read.
        psc._attachable_sources = lambda: [('~/precedent-team', 'main'),
                                           ('/home/user/precedent-team', 'main')]
        ok, detail = row()
        cases.append(('two clones at the same commit is still reported',
                      ok is False, str(detail)))
        cases.append(('it names both paths',
                      '~/precedent-team' in str(detail)
                      and '/home/user/precedent-team' in str(detail),
                      str(detail)))
        cases.append(('an agreeing pair is NOT called diverged',
                      'DIVERGED' not in str(detail), str(detail)))

        # Two clones, different heads -> the divergence is said out loud.
        heads = {'/home/user/precedent-team': 'bbbbbbb'}
        psc._git_head = lambda path: (0, heads.get(str(path), 'aaaaaaa'))
        ok, detail = row()
        cases.append(('a diverged pair says DIVERGED',
                      ok is False and 'DIVERGED' in str(detail), str(detail)))

        # A clone that cannot be read is a row, never a traceback.
        psc._git_head = lambda path: (1, '')
        ok, detail = row()
        cases.append(('an unreadable clone still produces a row',
                      ok is False and 'unreadable' in str(detail), str(detail)))
    finally:
        psc._attachable_sources = saved_sources
        psc._git_head = saved_head

    bad = [(n, d) for n, good, d in cases if not good]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def _individual_two_routes_fixture(tmp):
    """Shared by the two checks below: an individual-set "remote" served at a
    HOSTED url that git rewrites to a local directory, so the bootstrap takes
    its hosted-url path with no network. Returns (url, rewrite, git,
    run_main, row): `rewrite` is the git environment doing that, run_main
    runs the bootstrap's main() in-process under a fake HOME and project
    dir, and row() reads the session check's "cloned exactly once" row
    against that same fake layout (practice:
    fixture-owns-its-state -- nothing here may read the real $HOME, the real
    config or the real attach workspace)."""
    import contextlib
    import io
    import precedent_session_check as psc
    import precedent_source_bootstrap as psb

    srv = tmp / 'srv'
    source = srv / 'acct' / 'precedent-individual'
    source.mkdir(parents=True)
    url = 'https://example.invalid/acct/precedent-individual'
    rewrite = {'GIT_CONFIG_COUNT': '1',
               'GIT_CONFIG_KEY_0': f'url.file://{srv}/.insteadOf',
               'GIT_CONFIG_VALUE_0': 'https://example.invalid/'}

    def git(cwd, *args, check=True):
        r = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                            '-c', 'user.email=harness@example.com',
                            '-c', 'user.name=harness', *args],
                           cwd=str(cwd), capture_output=True, text=True,
                           env={**os.environ, **rewrite})
        if check and r.returncode:
            raise RuntimeError(f'git {args}: {r.stderr}')
        return r

    git(source, 'init', '-q', '-b', 'main')
    (source / 'practices').mkdir()
    (source / 'practices' / 'x.md').write_text(
        '---\nslug: harness-fixture\ntitle: Fixture\ntier: on-demand\n'
        'severity: default\napplies_to: ["**"]\noccasion: "testing"\n'
        'index_clause: "a harness fixture"\nchecked_by: null\n'
        'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
        'added: null\napproved_by: "harness"\n---\n\n## Rule\nFixture.\n\n'
        '## Detail\n\n## Why\n\n## Story\n\n## Install\n', encoding='utf-8')
    git(source, 'add', '-A')
    git(source, 'commit', '-qm', 'seed')

    @contextlib.contextmanager
    def fake(home, consumer):
        saved = {k: os.environ.get(k) for k in
                 ('HOME', 'PRECEDENT_PROJECT_DIR', 'CLAUDE_PROJECT_DIR',
                  'PRECEDENT_GIT_TOKEN', 'CLAUDECODE', 'CLAUDE_CODE_REMOTE',
                  'PRECEDENT_HARNESS', 'PRECEDENT_SOURCE_HOME', *rewrite)}
        os.environ.update({'HOME': str(home),
                           'PRECEDENT_PROJECT_DIR': str(consumer), **rewrite})
        os.environ.pop('CLAUDE_PROJECT_DIR', None)
        os.environ.pop('PRECEDENT_GIT_TOKEN', None)
        # The harness, and so the home folder, is the fixture's to say:
        # $HOME, the layout these cases pin. Inherited, a cloud session's
        # CLAUDE_CODE_REMOTE put the tree in the attach folder here and in
        # $HOME on GitHub's runner (tools/source_homes.json; the web layout
        # is check_one_tree_per_source_whichever_way_links_run's).
        for k in ('CLAUDECODE', 'CLAUDE_CODE_REMOTE', 'PRECEDENT_SOURCE_HOME'):
            os.environ.pop(k, None)
        os.environ['PRECEDENT_HARNESS'] = 'default'
        try:
            yield
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def run_main(home, consumer, repo_url=url):
        err = io.StringIO()
        with fake(home, consumer), contextlib.redirect_stderr(err):
            psb.main(['--level', 'individual',
                      '--name', 'precedent-individual', '--repo-url', repo_url,
                      '--clone', str(home / 'precedent-individual'),
                      '--config',
                      str(home / '.config' / 'precedent' / 'config.json'),
                      '--remote-only', 'false'])
        return err.getvalue()

    def row(home, consumer):
        saved_root = psc.ROOT
        psc.ROOT = consumer
        try:
            with fake(home, consumer):
                for name, ok, detail in psc.checks(offline=True):
                    if 'cloned exactly once' in name:
                        return ok, detail
        finally:
            psc.ROOT = saved_root
        return 'MISSING', ''

    return url, rewrite, git, run_main, row


def check_shared_set_leaves_a_link_at_the_attach_path():
    """A shared set's clone leaves a link where a repo-attach tool would
    clone it, as the individual set's always did, so attaching the set
    mid-session finds the one tree instead of making a second copy
    (2026-10-18: precedent-shared-ladder, brought by the individual set and
    cloned in $HOME, was cloned again beside the repositories by a session
    that attached it, and the person had to approve removing the copy).
    tools/precedent_source_bootstrap.py: _link_attach, attach_workspace."""
    import tempfile, contextlib, io
    name = 'a shared set leaves a link at the attach path'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_source_bootstrap as psb
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        srv = tmp / 'srv'
        source = srv / 'acct' / 'precedent-shared-x'
        source.mkdir(parents=True)
        url = 'https://example.invalid/acct/precedent-shared-x'
        rewrite = {'GIT_CONFIG_COUNT': '1',
                   'GIT_CONFIG_KEY_0': f'url.file://{srv}/.insteadOf',
                   'GIT_CONFIG_VALUE_0': 'https://example.invalid/'}

        def git(cwd, *args):
            return subprocess.run(['git', '-c', 'user.email=h@example.com',
                                   '-c', 'user.name=h', *args], cwd=str(cwd),
                                  capture_output=True, text=True,
                                  env={**os.environ, **rewrite})
        git(source, 'init', '-q', '-b', 'main')
        (source / 'practices').mkdir()
        (source / 'practices' / 'x.md').write_text('x\n', encoding='utf-8')
        git(source, 'add', '-A')
        git(source, 'commit', '-qm', 'seed')
        home, ws = tmp / 'home', tmp / 'ws'
        home.mkdir()
        ws.mkdir()
        saved = {k: os.environ.get(k) for k in rewrite}
        os.environ.update(rewrite)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                ok, out = psb.ensure_source('shared', 'precedent-shared-x', url,
                                            home / 'precedent-shared-x', None,
                                            retries=1, retry_delay=0,
                                            workspace=ws)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        attach = ws / 'precedent-shared-x'
        cases.append(('cloning a shared set in $HOME links the attach path to it',
                      ok and attach.is_symlink()
                      and attach.resolve() == (home / 'precedent-shared-x').resolve(),
                      str(out)[:300]))
        tree = home / 'precedent-shared-x'
        other = tmp / 'ws2'
        (other / 'precedent-shared-x').mkdir(parents=True)
        (other / 'precedent-shared-x' / 'mine.txt').write_text('m', encoding='utf-8')
        psb._link_attach('precedent-shared-x', url, tree, workspace=other)
        cases.append(('a path already there is never touched',
                      not (other / 'precedent-shared-x').is_symlink()
                      and (other / 'precedent-shared-x' / 'mine.txt').is_file()))
        third = tmp / 'ws3'
        third.mkdir()
        psb._link_attach('precedent-shared-x', 'file:///x/precedent-shared-x',
                         tree, workspace=third)
        cases.append(('a source that is not hosted gets no attach link',
                      not (third / 'precedent-shared-x').exists()))
        # Where the attach tool clones: beside a project that is a
        # repository, and INSIDE a session root that is not one -- a session
        # rooted above its repos (2026-10-19: rooted at /home/user, the
        # parent read /home, and a shared set was cloned twice).
        repo_proj, above = tmp / 'wsr' / 'proj', tmp / 'above'
        repo_proj.mkdir(parents=True)
        above.mkdir()
        git(repo_proj, 'init', '-q')
        saved_proj = os.environ.get('PRECEDENT_PROJECT_DIR')
        try:
            os.environ['PRECEDENT_PROJECT_DIR'] = str(repo_proj)
            beside = psb.attach_workspace()
            os.environ['PRECEDENT_PROJECT_DIR'] = str(above)
            inside = psb.attach_workspace()
        finally:
            if saved_proj is None:
                os.environ.pop('PRECEDENT_PROJECT_DIR', None)
            else:
                os.environ['PRECEDENT_PROJECT_DIR'] = saved_proj
        cases.append(('the attach path sits beside a project that is a '
                      'repository, and inside a session root that is not',
                      beside == repo_proj.parent and inside == above,
                      f'{beside} {inside}'))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))

def check_individual_hook_run_by_hand_links_the_attached_set():
    """The individual-set bootstrap hook, run BY HAND from a session's own
    shell -- where neither CLAUDE_PROJECT_DIR nor PRECEDENT_PROJECT_DIR is
    set -- links $HOME/precedent-individual to the copy the attach tool
    already cloned beside the project, instead of cloning a second one.

    Measured 2026-10-02 in a sandbox shaped like a consumer session: the
    set attached at <workspace>/precedent-individual, no user config, the
    hook run first with CLAUDE_PROJECT_DIR set (linked) and then without it
    (a second full clone). A consumer's session whose hook was not wired had
    to run it by hand, and got the second copy. The engine finds the attach
    copy through the project dir (attach_workspace), so the hook now works
    its repo out from its own path and exports it.

    Hermetic: the attached copy sits on a working branch, which the engine
    uses as it stands and never pulls, so nothing reaches the network; its
    origin is a hosted-looking URL on a reserved domain only so the engine
    treats it as a hosted source. CONTROL: the same run with the project dir
    pointed at an unrelated directory finds no attach copy and does not
    link -- otherwise the case would pass however the link was made."""
    import tempfile
    tmpl = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
            / 'individual-source-bootstrap.sh.template')
    if not tmpl.is_file():
        not_applicable('a hand-run individual hook links the attached set',
                       'no hook template in this tree')
        return
    url = 'https://example.invalid/acct/precedent-individual'
    env0 = {k: v for k, v in os.environ.items()
            if k not in ('CLAUDE_PROJECT_DIR', 'PRECEDENT_PROJECT_DIR',
                         'PRECEDENT_INDIVIDUAL_REPO', 'PRECEDENT_GIT_TOKEN',
                         'XDG_CONFIG_HOME')}
    env0.update(CLAUDE_CODE_REMOTE='true', GIT_TERMINAL_PROMPT='0',
                PRECEDENT_SOURCE_BASE_URL='https://example.invalid/acct',
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)
        ws, home = w / 'ws', w / 'home'
        proj = ws / 'proj'
        (proj / 'tools').mkdir(parents=True)
        (proj / '.claude' / 'hooks').mkdir(parents=True)
        # A project is a repository; one that is not is a session rooted
        # above its repos, whose attach copies sit in it, not beside it
        # (attach_workspace, 2026-10-19).
        subprocess.run(['git', 'init', '-q', str(proj)], env=env0,
                       capture_output=True)
        home.mkdir()
        for name in ('precedent_source_bootstrap.py',
                     'precedent_source_credentials.py',
                     # what the rendered stub runs, since 2026-10-07
                     'individual-source-bootstrap.sh'):
            shutil.copy(ROOT / 'tools' / name, proj / 'tools' / name)
        hook = proj / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        hook.write_text(tmpl.read_text(encoding='utf-8')
                        .replace('{{SOURCE_NAME}}', 'precedent-individual')
                        .replace('{{SOURCE_REPO_URL_SUBSTITUTED}}', 'yes')
                        .replace('{{SOURCE_REPO_URL}}', ''), encoding='utf-8')
        attached = ws / 'precedent-individual'
        subprocess.run(['git', 'init', '-q', '-b', 'work', str(attached)],
                       env=env0, capture_output=True)
        (attached / 'practices').mkdir()
        (attached / 'practices' / 'x.md').write_text('x\n')
        subprocess.run(['git', '-C', str(attached), 'add', '-A'], env=env0,
                       capture_output=True)
        subprocess.run(['git', '-C', str(attached), 'commit', '-qm', 'x'],
                       env=env0, capture_output=True)
        subprocess.run(['git', '-C', str(attached), 'remote', 'add', 'origin',
                        url], env=env0, capture_output=True)

        def run(extra=None):
            env = dict(env0, HOME=str(home), **(extra or {}))
            return subprocess.run(['bash', str(hook)], env=env, cwd=str(w),
                                  capture_output=True, text=True, timeout=120)

        r = run()
        link = home / 'precedent-individual'
        cases.append(('run by hand with no project dir in the environment, '
                      'the hook links $HOME/precedent-individual to the '
                      'attached copy instead of cloning a second one',
                      link.is_symlink() and link.resolve() == attached.resolve(),
                      failure_detail(r.stdout + r.stderr, 500)))
        if link.is_symlink():
            link.unlink()
        shutil.rmtree(home / '.config', ignore_errors=True)
        other = w / 'elsewhere'
        other.mkdir()
        r = run({'PRECEDENT_PROJECT_DIR': str(other)})
        cases.append(('CONTROL: with the project dir pointed elsewhere there '
                      'is no attach copy to find, and nothing is linked',
                      not link.is_symlink(), failure_detail(r.stdout + r.stderr, 500)))
        # The individual set runs its own copy from <set>/bootstrap/, one
        # level down, not two: "two levels up" named the directory above
        # the repo there (2026-10-04). Git's answer is the repo itself.
        subprocess.run(['git', 'init', '-q', str(proj)], env=env0, capture_output=True)
        (proj / 'bootstrap').mkdir()
        shallow = proj / 'bootstrap' / 'precedent-individual-bootstrap.sh'
        shutil.copy(hook, shallow)
        shutil.rmtree(home / '.config', ignore_errors=True)
        r = subprocess.run(['bash', str(shallow)], env=dict(env0, HOME=str(home)),
                           cwd=str(w), capture_output=True, text=True, timeout=120)
        cases.append(('run by hand from a repo\'s bootstrap/, one level down, '
                      'the hook still finds that repo and links the attached '
                      'copy beside it',
                      link.is_symlink() and link.resolve() == attached.resolve(),
                      failure_detail(r.stdout + r.stderr, 500)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a hand-run individual-set hook links the attached set '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


def check_missing_brought_set_names_a_fetch_that_runs():
    """The session check's row for a set the individual set brings that is
    not on disk named `python3 tools/precedent_source_bootstrap.py` bare,
    which refuses to run without four arguments (2026-10-19: a brought set was
    missing and the named fix failed). The row now names an add_repo per
    set and the session-start hook's own fetch, and that fetch must parse."""
    import importlib, shlex, tempfile
    name = ('a brought set that is missing is fetched by a command the '
            'bootstrap accepts')
    sys.path.insert(0, str(ROOT / 'tools'))
    sc = importlib.import_module('precedent_session_check')
    pr = importlib.import_module('precedent_resolve')
    boot = importlib.import_module('precedent_source_bootstrap')
    saved = (pr.brought_sources, sc._individual_path, boot._home_rule,
             os.environ.get('CLAUDE_CODE_REMOTE'))
    with tempfile.TemporaryDirectory() as tmp:
        try:
            sc._individual_path = lambda: pathlib.Path(tmp)
            pr.brought_sources = lambda *a, **k: [
                {'level': 'shared', 'name': 'sh', 'path': f'{tmp}/sh',
                 'repo': 'https://github.com/someone-else/Some-Set.git',
                 'brought': True}]
            rows = sc._brought_sets_rows()
            detail = rows[0][2] if rows else ''
            cmd = detail.split('then ', 1)[-1]
            argv = shlex.split(cmd)[2:]
            os.environ.pop('CLAUDE_CODE_REMOTE', None)
            try:
                parsed = boot.main(argv + ['--remote-only', 'true']) == 0
            except SystemExit:
                parsed = False
        finally:
            (pr.brought_sources, sc._individual_path, boot._home_rule, remote) = saved
            if remote is not None:
                os.environ['CLAUDE_CODE_REMOTE'] = remote
    cases = [
        ('the row fails', bool(rows) and rows[0][1] is False),
        ('it names add_repo for the set, owner and repository from its URL',
         'add_repo someone-else/Some-Set (read access)' in detail),
        ("it names the session-start hook's fetch",
         cmd.startswith('python3 tools/precedent_source_bootstrap.py --teams-from')),
        ('the bootstrap accepts that command', parsed),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + (f' -- row: {detail}' if failed else ''))


def check_individual_set_has_one_tree_whichever_route_cloned_it():
    """The individual set got cloned twice, reported by two consumer sessions
    on 2026-09-28. The source bootstrap clones it to $HOME/precedent-
    individual; the repo-attach tool, which sessions must call because it is
    what grants push access, replies "clone it to /home/user/<name>" -- the
    directory the project lives in. Where $HOME is elsewhere, that is two
    working trees, and in one report they had already diverged.

    Both orders are pinned, because each route can come first: a session
    with no environment credential attaches and clones before the resolver's
    self-heal runs the bootstrap; a session with one gets the bootstrap's
    clone at session start and follows the attach reply afterwards. Either
    way there must be one tree, both paths must reach it, and the session
    check's "cloned exactly once" row must be green.

    The last case is the control on the guard that keeps fixtures hermetic:
    a file:// source has no attach clone to meet, so the workspace is never
    touched for one."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='individual-one-tree-'))
    cases = []
    try:
        url, rewrite, git, run_main, row = _individual_two_routes_fixture(tmp)

        def layout(tag):
            home, work = tmp / tag / 'home', tmp / tag / 'work'
            consumer = work / 'consumer'
            home.mkdir(parents=True)
            consumer.mkdir(parents=True)
            # A project is a repository; one that is not is a session
            # rooted above its repos (attach_workspace, 2026-10-19).
            git(tmp, 'init', '-q', str(consumer))
            return home, work, consumer

        # --- attach first: the session cloned where the reply said ---------
        home, work, consumer = layout('attach-first')
        cfg = home / '.config' / 'precedent' / 'config.json'
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'precedent-individual',
            'path': str(home / 'precedent-individual'), 'repo_url': url}}))
        git(tmp, 'clone', '-q', url, str(work / 'precedent-individual'))
        out = run_main(home, consumer)
        at_home = home / 'precedent-individual'
        cases.append(('attach first: the bootstrap makes no second clone under '
                      '$HOME, only a link to the attach clone',
                      at_home.is_symlink() and at_home.resolve()
                      == (work / 'precedent-individual').resolve(),
                      f'symlink={at_home.is_symlink()} exists={at_home.exists()} '
                      f'{failure_detail(out, 300)}'))
        named = json.loads(cfg.read_text()).get('individual', {}).get('path', '')
        cases.append(('attach first: the config now names the attach clone',
                      pathlib.Path(named).resolve()
                      == (work / 'precedent-individual').resolve(), named))
        ok, detail = row(home, consumer)
        cases.append(('attach first: the session check row is green',
                      ok is True, str(detail)))

        # --- bootstrap first: the session then follows the attach reply ----
        home, work, consumer = layout('bootstrap-first')
        out = run_main(home, consumer)
        at_work = work / 'precedent-individual'
        cases.append(('bootstrap first: the attach path is a link to the '
                      "bootstrap's clone",
                      at_work.is_symlink() and at_work.resolve()
                      == (home / 'precedent-individual').resolve(),
                      f'symlink={at_work.is_symlink()} exists={at_work.exists()} '
                      f'{failure_detail(out, 300)}'))
        second = git(tmp, 'clone', '-q', url, str(at_work), check=False)
        cases.append(("bootstrap first: the clone the attach reply suggests "
                      'stops at "already exists" instead of making a copy',
                      second.returncode != 0
                      and 'already exists' in second.stderr,
                      f'rc={second.returncode} {failure_detail(second.stderr, 200)}'))
        ok, detail = row(home, consumer)
        cases.append(('bootstrap first: the session check row is green',
                      ok is True, str(detail)))

        # --- attach first, healed from a shell tool call --------------------
        # The route a session with no environment credential actually takes:
        # the resolver's self-heal runs the project's bootstrap hook from
        # inside a tool call, where no project-dir variable is set. The
        # resolver has to hand the project dir on, or the bootstrap cannot
        # see the attach clone and makes a second one.
        home, work, consumer = layout('self-heal')
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}))
        hook = consumer / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        hook.parent.mkdir(parents=True)
        hook.write_text(
            '#!/bin/bash\n'
            f'python3 "{ROOT / "tools" / "precedent_source_bootstrap.py"}" '
            f'--level individual --name precedent-individual --repo-url "{url}" '
            '--clone "$HOME/precedent-individual" '
            '--config "$HOME/.config/precedent/config.json"\n')
        git(tmp, 'clone', '-q', url, str(work / 'precedent-individual'))
        env = {k: v for k, v in os.environ.items() if k not in
               ('CLAUDE_PROJECT_DIR', 'PRECEDENT_PROJECT_DIR',
                'PRECEDENT_GIT_TOKEN')}
        env.update({'HOME': str(home), 'CLAUDE_CODE_REMOTE': 'true',
                    'PRECEDENT_USER_CONFIG':
                        str(home / '.config' / 'precedent' / 'config.json'),
                    **rewrite})
        r = subprocess.run([sys.executable,
                            str(ROOT / 'tools' / 'precedent_resolve.py'),
                            '--repo', str(consumer), '--json'],
                           capture_output=True, text=True, env=env, timeout=300)
        at_home = home / 'precedent-individual'
        cases.append(("healed from a shell: the resolver's self-heal reuses the "
                      'attach clone rather than cloning a second copy',
                      at_home.is_symlink() and at_home.resolve()
                      == (work / 'precedent-individual').resolve(),
                      f'symlink={at_home.is_symlink()} exists={at_home.exists()} '
                      f'rc={r.returncode} {failure_detail(r.stderr, 300)}'))

        # --- control: a local source never reaches the workspace -----------
        home, work, consumer = layout('local-url')
        run_main(home, consumer,
                 repo_url=f'file://{tmp / "srv" / "acct" / "precedent-individual"}')
        cases.append(('control: a file:// source is cloned to $HOME and leaves '
                      'the workspace alone',
                      (home / 'precedent-individual' / '.git').is_dir()
                      and not os.path.lexists(work / 'precedent-individual'),
                      str(sorted(p.name for p in work.iterdir()))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, good, d in cases if not good]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_individual_set_diverged_copies_are_reported_not_clobbered():
    """The worse of the two 2026-09-28 reports: the bootstrap's copy and a
    hand clone at the attach path had DIVERGED. Collapsing them is not a
    startup hook's call -- the hand clone can hold commits nobody pushed --
    so the bootstrap must report both and touch neither (practice:
    repair-cannot-discard-work). This pins the report and the untouched
    work: a local commit, an uncommitted file, both copies still real
    directories, and the session check still red rather than hidden."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='individual-diverged-'))
    cases = []
    try:
        url, _rewrite, git, run_main, row = _individual_two_routes_fixture(tmp)
        home, work = tmp / 'home', tmp / 'work'
        consumer = work / 'consumer'
        home.mkdir()
        consumer.mkdir(parents=True)
        git(tmp, 'init', '-q', str(consumer))   # a project is a repository
        at_home, at_work = home / 'precedent-individual', work / 'precedent-individual'
        git(tmp, 'clone', '-q', url, str(at_home))
        git(tmp, 'clone', '-q', url, str(at_work))
        # Work only the hand clone holds: one commit, one uncommitted file.
        (at_work / 'practices' / 'mine.md').write_text('local\n')
        git(at_work, 'add', '-A')
        git(at_work, 'commit', '-qm', 'unpushed work')
        local_head = git(at_work, 'rev-parse', 'HEAD').stdout.strip()
        (at_work / 'draft.txt').write_text('not committed\n')
        # And upstream moves, so the bootstrap's pull diverges the pair.
        source = tmp / 'srv' / 'acct' / 'precedent-individual'
        (source / 'practices' / 'y.md').write_text('upstream\n')
        git(source, 'add', '-A')
        git(source, 'commit', '-qm', 'upstream moves')

        out = run_main(home, consumer)
        cases.append(('both copies are still real directories -- nothing was '
                      'replaced by a link or removed',
                      (at_home / '.git').is_dir() and not at_home.is_symlink()
                      and (at_work / '.git').is_dir() and not at_work.is_symlink(),
                      f'home_link={at_home.is_symlink()} '
                      f'work_link={at_work.is_symlink()}'))
        cases.append(("the hand clone's unpushed commit and uncommitted file "
                      'are intact',
                      git(at_work, 'rev-parse', 'HEAD').stdout.strip() == local_head
                      and (at_work / 'draft.txt').is_file(),
                      git(at_work, 'log', '--oneline', '-3').stdout))
        cases.append(('the bootstrap REPORTS the pair: both paths, DIVERGED, '
                      'the unpushed work, and that nothing was touched',
                      str(at_home) in out and str(at_work) in out
                      and 'DIVERGED' in out and 'unpushed' in out
                      and 'Neither was touched' in out, failure_detail(out, 600)))
        named = json.loads((home / '.config' / 'precedent' / 'config.json')
                           .read_text()).get('individual', {}).get('path')
        cases.append(("the config still names the bootstrap's copy",
                      named == str(at_home), str(named)))
        ok, detail = row(home, consumer)
        cases.append(('the session check stays red and says DIVERGED',
                      ok is False and 'DIVERGED' in str(detail), str(detail)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, good, d in cases if not good]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_bootstrap_writes_what_real_sets_converged_on():
    """A newly bootstrapped set starts with what every real set ended up
    writing for itself by hand (very deep check, 2026-09-28, CONVERGENT
    DRIFT): the shipped Claude Code CLAUDE.md byte for byte rather than a
    shorter stub of its own, a "Working in this repo" section describing
    the mechanism, and a precedent-source.json whose `visibility` is what
    the person said -- all three real shared sets are public and each had
    to correct a hard-coded "private" by hand. The discriminating case: the
    default is still private."""
    import shutil, tempfile
    tool = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bootstrap-conv-'))
    cases = []
    try:
        pub, priv = tmp / 'pub', tmp / 'priv'
        for dest, extra in ((pub, ['--visibility', 'public']), (priv, [])):
            r = subprocess.run([sys.executable, tool, '--level', 'shared',
                                '--name', 'precedent-shared-zzfixture',
                                '--dest', str(dest), '--approver',
                                'Fixture Person:fixture', *extra],
                               capture_output=True, text=True)
            cases.append((f'bootstrap succeeds ({dest.name})',
                          r.returncode == 0, failure_detail(r.stdout + r.stderr, 300)))
        vis = lambda d: json.loads((d / 'precedent-source.json').read_text(
            encoding='utf-8')).get('visibility')
        cases.append(('--visibility public is recorded', vis(pub) == 'public',
                      repr(vis(pub))))
        cases.append(('THE DISCRIMINATING CASE: the default stays private',
                      vis(priv) == 'private', repr(vis(priv))))
        shipped = (ROOT / 'templates' / 'harness' / 'claude-code' /
                   'CLAUDE.md').read_text(encoding='utf-8')
        cases.append(('CLAUDE.md is the shipped adapter, byte for byte',
                      (pub / 'CLAUDE.md').read_text(encoding='utf-8') == shipped,
                      ''))
        agents = (pub / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('AGENTS.md carries the Working in this repo section, '
                      'with the approval line for a shared set',
                      '## Working in this repo' in agents
                      and 'approvers.json' in agents, failure_detail(agents, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a new practice set starts with what real sets converged on '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_bootstrap_does_what_a_first_update_vendors_adds():
    """A newly bootstrapped set already has what its first Update Vendors
    used to add: baseline approvals for every session-load budget in force,
    the person's one session-load total with their own approval, and the
    branch tiers said -- through the same functions that run calls
    (seed_baseline_approvals, record_person_total, ensure_tiers).

    2026-10-30, very deep check, CONVERGENT DRIFT: both shared sets carried
    those lines and the generator wrote none (Morgan, 2026-10-31, strength:
    assented). Controls: an individual set with no approval for its total
    gives no total; off the ladder nothing about tiers is written or said;
    and with seed_baseline_approvals neutered the registry has no approvals,
    so the first case is the fix's and not the fixture's."""
    import contextlib, io, tempfile
    import build_views as bv
    import precedent_bootstrap_source as pbs
    import precedent_update as pu
    tool = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)

        def individual(name, approval):
            d = w / name
            d.mkdir()
            man = {'level': 'individual', 'name': 'precedent-individual',
                   'session_load_tokens': 9000}
            if approval:
                man['session_load_approval'] = {'strength': 'decided',
                                                'approved_by': 'Fixture, 2026-10-28: "yes, 9k"'}
            (d / 'precedent-source.json').write_text(json.dumps(man), encoding='utf-8')
            cfg = w / f'{name}.json'
            cfg.write_text(json.dumps({'individual': {
                'name': 'precedent-individual', 'path': str(d)}}), encoding='utf-8')
            return cfg

        def env_for(cfg, ladder):
            env = dict(os.environ, HOME=str(w / 'home'), PRECEDENT_USER_CONFIG=str(cfg))
            for k in ('PRECEDENT_ASSUME_LADDER', 'PRECEDENT_NO_LADDERS'):
                env.pop(k, None)
            env['PRECEDENT_ASSUME_LADDER' if ladder else 'PRECEDENT_NO_LADDERS'] = '1'
            return env

        def boot(dest, cfg, ladder):
            r = subprocess.run([sys.executable, tool, '--level', 'shared', '--name',
                                'precedent-shared-zzfirstupdate', '--dest', str(dest),
                                '--approver', 'Fixture Person:fixture',
                                '--off-main', 'true'],
                               env=env_for(cfg, ladder), capture_output=True, text=True)
            reg = dest / 'tools' / 'session_load_budgets.json'
            data = json.loads(reg.read_text(encoding='utf-8')) if reg.is_file() else {}
            pj = dest / 'precedent.json'
            return r, data, (json.loads(pj.read_text(encoding='utf-8'))
                             if pj.is_file() else {})

        with_total = individual('ind-approved', True)
        r, data, pj = boot(w / 'set', with_total, ladder=True)
        cases.append(('the bootstrap succeeds', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 300)))
        ap = data.get('approved_budgets') or {}
        in_force = bv.effective_budgets(w / 'set', registry=w / 'set' / 'tools'
                                        / 'session_load_budgets.json')
        unapproved = sorted(k for k, v in in_force.items() if isinstance(v, int)
                            and not (isinstance((ap.get(k) or {}).get('max'), int)
                                     and v <= ap[k]['max']))
        cases.append(('THE DISCRIMINATING CASE: every budget in force has an '
                      'approval at or above it from the first commit',
                      bool(ap) and not unapproved, f'unapproved: {unapproved}'))
        cases.append(('each per-part approval is the baseline, said to come from '
                      'the bootstrap', all(e.get('strength') == 'baseline'
                                           and 'at bootstrap' in e.get('approved_by', '')
                                           for k, e in ap.items()
                                           if k != 'session_load_tokens'), str(ap)[:300]))
        tot = ap.get('session_load_tokens') or {}
        cases.append(("the person's one total is copied with their own approval",
                      data.get('session_load_tokens') == 9000 and tot.get('max') == 9000
                      and tot.get('strength') == 'decided'
                      and 'Fixture, 2026-10-28' in tot.get('approved_by', '')
                      and 'set generator' in tot.get('approved_by', ''), str(tot)))
        cases.append(('on the ladder, the set lands on staging and the command '
                      'that makes staging on origin is said',
                      pj.get('landing_branch') == 'staging'
                      and '--ensure-tiers --apply' in r.stdout, failure_detail(r.stdout, 300)))

        r, data, _ = boot(w / 'set-noappr', individual('ind-bare', False), ladder=True)
        cases.append(('CONTROL: a total with no approval beside it is not copied',
                      r.returncode == 0 and 'session_load_tokens' not in data
                      and 'session_load_tokens' not in (data.get('approved_budgets') or {}),
                      str(data)[:300]))

        r, data, pj = boot(w / 'set-off', with_total, ladder=False)
        cases.append(('CONTROL: off the ladder no landing branch is written and '
                      'no tier is said', r.returncode == 0
                      and 'landing_branch' not in pj and 'ensure-tiers' not in r.stdout,
                      failure_detail(r.stdout, 300)))

        saved_env = {k: os.environ.get(k) for k in
                     ('HOME', 'PRECEDENT_USER_CONFIG', 'PRECEDENT_NO_LADDERS',
                      'PRECEDENT_ASSUME_LADDER')}
        saved_seed = pu.seed_baseline_approvals
        try:
            os.environ.update(env_for(with_total, ladder=False))
            os.environ.pop('PRECEDENT_ASSUME_LADDER', None)
            pu.seed_baseline_approvals = lambda *a, **k: False
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                pbs.bootstrap('shared', 'precedent-shared-zzneutered', w / 'set-neutered',
                              approvers=[{'name': 'Fixture Person', 'github': 'fixture'}],
                              off_main=True)
            data = json.loads((w / 'set-neutered' / 'tools' / 'session_load_budgets.json')
                              .read_text(encoding='utf-8'))
            cases.append(('NEGATIVE CONTROL: with seed_baseline_approvals neutered '
                          'only the person\'s total is approved, every per-part '
                          'budget is not', set(data.get('approved_budgets') or {})
                          == {'session_load_tokens'}, str(data.get('approved_budgets'))[:300]))
        finally:
            pu.seed_baseline_approvals = saved_seed
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a new practice set starts with what its first Update Vendors '
          f'added ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_views_drift_gate_reaches_a_source_set():
    """A generated view's header may only name a command that EXISTS where
    the view does, and a set that generates views ships something that runs
    it.

    THE INCIDENT (2026-09-11, TODO.md's
    loader-comment-names-an-unvendored-check). Every view build_views.py
    writes -- AGENTS.md's loader block, MAP.md, GLOSSARY.md -- carried a
    header saying `tools/verify_harness.py`'s regeneration check fails the
    build on drift. This file is deliberately not vendored into a source set
    (precedent_vendor_engine.py's own comment), so in every private set the
    one line telling a session the block was protected named a file that is
    not there. It cost an individual set three stale practices in MAP.md,
    one of them missing from its table from the day it landed: nobody
    looked, because the header said somebody already was.

    Two properties, and the first is the general one -- it fails for ANY
    tool a future header names that a source set does not get, not just for
    verify_harness.py:

      1. Regenerate the views inside a fixture set built from ENGINE_FILES
         alone, and require every `*.py` named in their generated headers to
         exist in that set's own tools/.
      2. `build_views.py --check` -- what the headers now name, and what the
         set's own full sweep runs -- actually gates there: exit 0 clean,
         non-zero on one planted line.

    Plus the shipping half, since a practice set runs no CI (2026-09-21):
    precedent_bootstrap_source.py installs no workflow into a new set, and
    does not report one missing. The workflow template sets once ran was
    retired on 2026-10-01.

    The fixture copies ENGINE_FILES out of THIS working tree, for the same
    reason check_precedent_check_degrades_in_a_source_set does: seeding from
    a committed ref would leave this check one commit behind the engine
    change it is meant to test.
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-views-gate-'))
    cases = []
    try:
        dest = tmp / 'srcset'
        (dest / 'tools').mkdir(parents=True)
        (dest / 'practices').mkdir()
        for name in pve.ENGINE_FILES:
            src = ROOT / 'tools' / name
            if src.is_file():
                shutil.copy2(src, dest / 'tools' / name)
        shutil.copy2(ROOT / 'tools' / 'routing_scope.json',
                     dest / 'tools' / 'routing_scope.json')
        # Two real practices, so the resident set and the occasion index
        # both have something to render rather than exercising the
        # empty-catalogue path.
        for slug in ('repo-is-memory', 'verify-postcondition'):
            shutil.copy2(ROOT / 'practices' / f'{slug}.md',
                         dest / 'practices' / f'{slug}.md')
        (dest / 'AGENTS.md').write_text(
            '# Fixture set instructions\n\n'
            '<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        def bv(*args):
            r = subprocess.run([sys.executable, str(dest / 'tools' / 'build_views.py'),
                                '--repo', str(dest), *args],
                               capture_output=True, text=True, cwd=str(dest))
            return r.returncode, r.stdout + r.stderr

        rc, out = bv()
        cases.append(('a source set built from ENGINE_FILES alone can generate '
                      'its own views', rc == 0, out))

        # Every tool a generated header names has to be present HERE. The
        # headers are the first lines of MAP.md and GLOSSARY.md and the
        # first comment inside AGENTS.md's markers, so reading the first
        # 1200 characters of each covers all three without parsing.
        vendored = {p.name for p in (dest / 'tools').glob('*.py')}
        for name in ('AGENTS.md', 'MAP.md', 'GLOSSARY.md'):
            head = (dest / name).read_text(encoding='utf-8')[:1200]
            named = set(re.findall(r'[\w/]*?(\w+\.py)\b', head))
            absent = sorted(n for n in named if n not in vendored)
            cases.append((f"{name}'s generated header names no tool this set "
                          f"does not have", not absent,
                          f"names {', '.join(absent)}, absent from a source "
                          f"set's tools/ -- a header a session reads instead "
                          f"of checking" if absent else ''))

        rc, out = bv('--check')
        cases.append(('build_views.py --check passes on the freshly generated '
                      'views', rc == 0, out))

        with (dest / 'MAP.md').open('a', encoding='utf-8') as fh:
            fh.write('\n<!-- planted drift -->\n')
        rc, out = bv('--check')
        cases.append(('build_views.py --check fails on one planted line -- the '
                      'command the headers and the shipped workflow both name '
                      'actually gates', rc != 0 and 'MAP.md' in out, out))

        # The shipping half: no workflow. The practice-set template, whose
        # views-drift steps ran this same command in CI, was retired on
        # 2026-10-01 (a set runs no CI since 2026-09-21); the cases below
        # pin that the bootstrap installs none and asks for none.
        cases.append(('the retired practice-set workflow template is gone',
                      not (ROOT / 'templates' / 'github-actions' /
                           ('precedent-check' + '.yml.template')).exists(), ''))

        import precedent_bootstrap_source as pbs
        newset = tmp / 'bootstrapped'
        # FIXTURE OWNS ITS STATE (2026-09-16): _install_workflows is gated on
        # ci_workflows since that date, resolved from newset/identity.json
        # (falling back to whatever individual source the runner happens to
        # have, which this fixture must never depend on). Writing the field
        # explicitly is what makes the "adopter opted in" case below test
        # opting in, rather than an ambient default this fixture did not set.
        newset.mkdir(parents=True, exist_ok=True)
        (newset / 'identity.json').write_text(
            json.dumps({'email': 'fixture@example.com', 'ci_workflows': 'enabled'}),
            encoding='utf-8')
        # REWRITTEN 2026-09-21 (practice: source-sets-run-no-ci). This pair
        # used to assert that an opted-in set RECEIVES precedent-check.yml,
        # and that verify() reports its absence as a defect. Both are now
        # false by decision rather than by accident: a source ships no CI
        # workflow at all, so WORKFLOW_TEMPLATES is empty and there is
        # nothing for an opt-in to install.
        #
        # The flag is left readable rather than ripped out, and this case is
        # what stops that being a quiet lie: `ci_workflows: enabled` is
        # honoured and still installs NOTHING, because the shipping list is
        # empty -- so a set that opts in is not silently different from one
        # that does not, and nobody discovers months later that a flag they
        # set did something.
        installed = [pathlib.Path(f) for f in pbs._install_workflows(newset)]
        cases.append(('a set that opts IN still gets no workflow -- a source '
                      'ships none, so the opt-in has nothing to install',
                      installed == []
                      and not (newset / '.github').exists(),
                      str(installed)))
        missing = pbs.verify('individual', newset)
        cases.append(('and verify() does NOT report the absent workflow as a '
                      'defect -- it is the rule now, not a gap',
                      not any('precedent-check.yml' in m for m in missing),
                      '; '.join(missing)))

        # THE NEW DEFAULT (2026-09-16, declared-default-is-applied): a set
        # that never declares ci_workflows -- the ordinary case, per
        # GITHUB_ACTIONS.md's "Controlling Actions Minutes" -- gets neither
        # workflow written, and verify() does not call that a defect. A
        # separate dest, so this does not disturb the opted-in fixture above.
        undeclared = tmp / 'bootstrapped-undeclared'
        undeclared.mkdir(parents=True, exist_ok=True)
        (undeclared / 'identity.json').write_text(
            json.dumps({'email': 'fixture2@example.com'}), encoding='utf-8')
        installed_off = pbs._install_workflows(undeclared)
        cases.append(('a set that never declares ci_workflows gets neither '
                      'workflow written',
                      installed_off == []
                      and not (undeclared / '.github').exists(),
                      str(installed_off)))
        missing_off = pbs.verify('individual', undeclared)
        cases.append(('verify() does not call a correctly-disabled set '
                      'missing its CI workflows',
                      not any('views-drift.yml' in m or 'precedent-check.yml' in m
                              for m in missing_off),
                      '; '.join(missing_off)))

        # The CLI route, pinned because three documents name it. verify()
        # was reachable only from this harness until 2026-09-11, while
        # GITHUB_ACTIONS.md, TODO.md and the templates README all told
        # operators to run `--verify <path>` -- a command named in a
        # document and absent from the tool, which is the defect the rest
        # of this check exists to stop, one level up.
        r = subprocess.run([sys.executable,
                            str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                            '--verify', str(newset), '--level', 'individual'],
                           capture_output=True, text=True)
        cases.append(('`--verify PATH` exists, exits non-zero on an '
                      'incomplete set, and names what is missing',
                      r.returncode == 1 and r.stdout.strip() != '',
                      (r.stdout + r.stderr).strip()))
        # AND IT NO LONGER NAMES A CI WORKFLOW (2026-09-21, practice:
        # source-sets-run-no-ci). This pair used to assert the opposite --
        # that `--verify` reports a missing precedent-check.yml, and that
        # installing it removes exactly that line. Both described a world
        # where a source was expected to carry CI. It is not, so reporting
        # its absence would send every adopter to install something this
        # repo deliberately stopped shipping.
        cases.append(('`--verify` does NOT report a missing CI workflow -- a '
                      'source is not expected to have one',
                      'precedent-check.yml' not in r.stdout
                      and 'leak-gate.yml' not in r.stdout,
                      r.stdout.strip()))
        # The control the pair above still needs: _install_workflows must be
        # a genuine no-op here, not merely quiet. If it ever writes again,
        # the verify() report must not silently change shape underneath it.
        before = set(pbs.verify('individual', newset))
        pbs._install_workflows(newset)
        after = set(pbs.verify('individual', newset))
        cases.append(('installing workflows changes nothing, because there '
                      'are none to install',
                      before == after,
                      f"before={len(before)} after={len(after)}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for label, ok, detail in cases:
        check(label, ok, detail if not ok else '')


def check_refresh_sources_leaves_an_attached_consumer_alone():
    """precedent_refresh_sources.py --apply, which the SessionStart hook runs
    over every repo beside this checkout, writes into a CONSUMER only when
    --path named it. On 2026-09-26 an attached consumer got five hook files
    and a settings.json line on every start, two adapter-owned hooks
    overwritten, and nothing committed -- so its own refresh refused to run
    and the stop hook read the container as holding unsaved work.

    Both worlds planted (practice: checks-plant-their-state): the consumer
    found by the session-start scan is reported and byte-identical after,
    and the same fixture with the guard neutered IS written, so the quiet
    case is shown to come from the guard (practice:
    control-asserts-which-failure). Hermetic: the scan and the tip are
    pointed at a temporary directory, and nothing is fetched."""
    import contextlib, io, json as _j, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-leaves-consumer-'))

    def plant():
        repo = tmp / 'consumer'
        shutil.rmtree(repo, ignore_errors=True)
        (repo / 'tools').mkdir(parents=True)
        (repo / '.claude').mkdir()
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(_j.dumps(
            {'kind': 'consumer', 'source_commit': 'fixture-old'}), encoding='utf-8')
        (repo / '.claude' / 'settings.json').write_text('{}\n', encoding='utf-8')
        return repo

    def snapshot(repo):
        return {str(f.relative_to(repo)): f.read_bytes()
                for f in sorted(repo.rglob('*')) if f.is_file()}

    def run(repo, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = prs.main(argv)
        return rc, buf.getvalue()

    saved = (prs.candidate_dirs, prs.head_commit, prs._may_write)
    try:
        repo = plant()
        prs.candidate_dirs = lambda extra=(): [repo, *(pathlib.Path(x).resolve()
                                                       for x in extra)]
        prs.head_commit = lambda: ('fixture-tip', 'origin/fixture')
        before = snapshot(repo)
        rc, out = run(repo, ['--apply'])
        cases.append(('an attached consumer the session-start scan finds is '
                      'reported LEFT ALONE, in the tool\'s own words',
                      'LEFT ALONE: a consumer repo' in out, failure_detail(out, 600)))
        cases.append(('...and not one byte of it changes',
                      snapshot(repo) == before, failure_detail(out, 600)))
        # Said once, as a consumer (2026-10-04): no STALE row beside the
        # LEFT ALONE block, no BRANCH row (nothing syncs from a consumer),
        # and no set hooks reported "present" in a repo that never had them.
        rows = [l for l in out.splitlines() if str(repo) in l or 'consumer' in l]
        cases.append(('a stale consumer is said once: the LEFT ALONE block names '
                      'its engine as behind, with no STALE row beside it',
                      'behind BestPractice' in out
                      and not any(l.lstrip().startswith('STALE') for l in rows),
                      failure_detail(out, 800)))
        cases.append(('...and it gets no BRANCH or set-hook row',
                      'BRANCH on' not in out and 'hooks present' not in out
                      and 'hooks not wired' not in out, failure_detail(out, 800)))
        cases.append(('...and the run says it wrote nothing, exiting 0',
                      rc == 0 and 'nothing written' in out, failure_detail(out, 600)))
        cases.append(('a practice set is still one --apply may write into',
                      prs._may_write({'kind': 'source', 'repo': str(repo)}), ''))
        cases.append(('a consumer named with --path is one it may write into',
                      prs._may_write({'kind': 'consumer', 'repo': str(repo)},
                                     {repo.resolve()}), ''))
        repo = plant()
        before = snapshot(repo)
        prs._may_write = lambda entry, asked=(): True
        rc, out = run(repo, ['--apply'])
        cases.append(('CONTROL: with the guard neutered the same consumer is '
                      'not left alone, so the quiet case above came from the guard',
                      'LEFT ALONE' not in out, failure_detail(out, 600)))
    finally:
        prs.candidate_dirs, prs.head_commit, prs._may_write = saved
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session-start refresh never writes into an attached consumer '
          f'nobody named ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_refresh_sources_pulls_a_set_behind_its_own_origin():
    """A practice-set clone behind its OWN origin is fast-forwarded at
    session start even when its engine is current.

    Found 2026-09-30: "stale" meant only "this set's engine is behind
    BestPractice", and with no engine stale --apply returned "all current"
    before any fast-forward, so a clone 13 commits behind its own main ran
    a session on stale rules while the freshness notice said BEHIND for
    the same clone. Real git, hermetic: a bare origin, the set's clone, one
    commit pushed past it from elsewhere. CONTROL: the same clone with an
    uncommitted edit is left where it is, and says why."""
    import contextlib, io, json as _j, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-own-origin-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env).stdout.strip()

    names = ('candidate_dirs', 'head_commit', 'ensure_source_credentials',
             '_repairable', 'branch_state')
    saved = {n: getattr(prs, n) for n in names}
    try:
        origin, seed, clone = tmp / 'origin.git', tmp / 'seed', tmp / 'set'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        g(tmp, 'clone', '-q', str(origin), str(seed))
        (seed / 'tools').mkdir()
        (seed / 'tools' / 'ENGINE_MANIFEST.json').write_text(_j.dumps(
            {'kind': 'source', 'source_commit': 'fixture-tip'}), encoding='utf-8')
        (seed / 'precedent.json').write_text('{"base_branch": "main"}\n', encoding='utf-8')
        (seed / 'practices.md').write_text('one\n', encoding='utf-8')
        g(seed, 'add', '-A'); g(seed, 'commit', '-qm', 'one'); g(seed, 'push', '-q', 'origin', 'main')
        g(tmp, 'clone', '-q', str(origin), str(clone))
        (seed / 'practices.md').write_text('one\ntwo\n', encoding='utf-8')
        g(seed, 'commit', '-qam', 'two'); g(seed, 'push', '-q', 'origin', 'main')
        tip = g(seed, 'rev-parse', 'HEAD')

        prs.candidate_dirs = lambda extra=(): [clone.resolve()]
        prs.head_commit = lambda: ('fixture-tip', 'origin/fixture')
        prs.ensure_source_credentials = lambda found: []
        prs._repairable = lambda e: False
        prs.branch_state = lambda repo: None

        def run():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = prs.main(['--apply'])
            return rc, buf.getvalue()

        # CONTROL first: dirty, so it must stay behind and say so. A clean
        # consumer is reported after it, so its row is the last one printed
        # before the note (2026-10-01: the note sat under a consumer's row,
        # unnamed, and was read as that consumer's).
        consumer = tmp / 'consumer'
        (consumer / 'tools').mkdir(parents=True)
        (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(_j.dumps(
            {'kind': 'consumer', 'source_commit': 'an-older-engine'}),
            encoding='utf-8')
        g(tmp, 'init', '-q', '-b', 'main', str(consumer))
        g(consumer, 'add', '-A'); g(consumer, 'commit', '-qm', 'consumer')
        prs.candidate_dirs = lambda extra=(): [clone.resolve(), consumer.resolve()]
        (clone / 'scratch.txt').write_text('mine\n', encoding='utf-8')
        rc, out = run()
        cases.append(('CONTROL: a dirty clone behind its origin is left where it is',
                      g(clone, 'rev-parse', 'HEAD') != tip, failure_detail(out, 400)))
        cases.append(('...and the run says why, pointing at a re-run',
                      'uncommitted changes of its own' in out and '--apply' in out,
                      failure_detail(out, 400)))
        note = next((l for l in out.splitlines()
                     if 'uncommitted changes of its own' in l), '')
        cases.append(('...on a line that names the set it is about, never the '
                      'consumer whose row was printed last',
                      prs._label(clone.resolve()) in note
                      and prs._label(consumer.resolve()) not in note, note))
        prs.candidate_dirs = lambda extra=(): [clone.resolve()]
        (clone / 'scratch.txt').unlink()

        rc, out = run()
        cases.append(('engine current, clean clone behind its own origin: it ends current',
                      g(clone, 'rev-parse', 'HEAD') == tip, failure_detail(out, 400)))
        cases.append(('...and the line names what it compared',
                      'its own origin/main' in out and 'engine current' in out, failure_detail(out, 400)))

        # Engine output a refresh left uncommitted is not a person's work:
        # the clone is still brought current, and the engine written again
        # (2026-09-30: every clone carries it, and a bare pull refused).
        (seed / 'practices.md').write_text('one\ntwo\nthree\n', encoding='utf-8')
        g(seed, 'commit', '-qam', 'three'); g(seed, 'push', '-q', 'origin', 'main')
        tip = g(seed, 'rev-parse', 'HEAD')
        (clone / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            '{"kind": "source", "source_commit": "fixture-tip", "x": 1}', encoding='utf-8')
        applied = []
        saved['classify_dirt'] = prs.classify_dirt
        saved['apply_to'] = prs.apply_to
        prs.classify_dirt = lambda repo: (
            (['tools/ENGINE_MANIFEST.json'] if g(repo, 'status', '--porcelain') else []), [])
        prs.apply_to = lambda e, commit=False, branch=None: (applied.append(e['repo']), [])[1]
        rc, out = run()
        cases.append(('a clone carrying only engine output is still brought current',
                      g(clone, 'rev-parse', 'HEAD') == tip, failure_detail(out, 400)))
        cases.append(('...and its engine is written again over the new tree',
                      len(applied) == 1, f'{applied} {failure_detail(out, 300)}'))
    finally:
        for n, f in saved.items():
            setattr(prs, n, f)
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session-start refresh pulls a set clone behind its own origin '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_removed_engine_path_is_found_in_the_sets_beside():
    """An engine path this branch removes, still named in a practice set
    beside the checkout, is reported -- and the set's own vendored copy of
    the file, which its next refresh removes, is not.

    WHY (2026-10-18). tools/ladder_words.py moved from the engine into a
    set; a comment in that set kept naming the engine path, and only the
    set's next Update Vendors stopped on it."""
    import json as _j, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='stranded-in-sets-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    saved = prs.candidate_dirs
    try:
        def make(name, kind):
            r = tmp / name
            (r / 'tools').mkdir(parents=True)
            (r / 'tools' / 'ENGINE_MANIFEST.json').write_text(_j.dumps(
                {'kind': kind, 'files': ['gone_words.py', 'kept.py']}))
            (r / 'tools' / 'gone_words.py').write_text('# tools/gone_words.py\n')
            (r / 'MAP.md').write_text('---\ngenerated_by: tools/build_views.py\n'
                                      '---\n[tools/gone_words.py](x)\n')
            (r / 'precedent-source.json').write_text(
                '{"_c": "moved from the engine\'s tools/gone_words.py"}\n')
            subprocess.run(['git', 'init', '-q', str(r)], capture_output=True)
            subprocess.run(['git', '-C', str(r), 'add', '-A'], capture_output=True)
            subprocess.run(['git', '-C', str(r), 'commit', '-qm', 'x'],
                           capture_output=True, env=env)
            return r
        a_set, consumer = make('a-set', 'source'), make('consumer', 'consumer')
        prs.candidate_dirs = lambda extra=(): [a_set, consumer]
        got = prs.stranded_in_sets(['tools/gone_words.py'])
        where = [w for _l, w, _o in got]
        cases.append(('the live mention in the set is reported',
                      any(w.startswith('precedent-source.json:') for w in where),
                      repr(got)))
        cases.append(('...not the set\'s vendored copy, its generated MAP.md, '
                      'nor a consumer',
                      len(got) == 1, repr(got)))
        cases.append(('a path no set vendors finds nothing',
                      prs.stranded_in_sets(['tools/never_vendored.py']) == [],
                      ''))
    finally:
        prs.candidate_dirs = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{c[0]} ({c[2]})' for c in cases if not c[1]]
    check(f'a removed engine path still named in a set beside is reported '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_refresh_sources_branch_line_only_when_the_tree_is_older():
    """The session-start BRANCH line ("BRANCH on X -- expected main") is
    printed only when the clone could actually sync older text: off its
    expected branch AND not containing origin/<expected>.

    WHY (2026-10-18). A session checked out on its designated branch,
    sitting exactly at origin/main, read the warning three times at start
    for a revert that could not happen. Real git: a clone at origin/main on
    another branch name, one past it, and one behind it -- only the last
    keeps the line."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-branch-line-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env).stdout.strip()
    try:
        origin, clone = tmp / 'origin.git', tmp / 'set'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        g(tmp, 'clone', '-q', str(origin), str(clone))
        for n in ('one', 'two'):
            (clone / 'f.txt').write_text(n + '\n', encoding='utf-8')
            g(clone, 'add', '-A'); g(clone, 'commit', '-qm', n)
        g(clone, 'push', '-q', 'origin', 'main')
        g(clone, 'checkout', '-q', '-b', 'claude/session-branch')
        cases.append(('at origin/main under another name: no line',
                      prs.holds_expected_tree(clone, 'main'), ''))
        (clone / 'g.txt').write_text('mine\n', encoding='utf-8')
        g(clone, 'add', '-A'); g(clone, 'commit', '-qm', 'mine')
        cases.append(('past origin/main: no line',
                      prs.holds_expected_tree(clone, 'main'), ''))
        g(clone, 'checkout', '-q', '-B', 'claude/session-branch', 'main~1')
        cases.append(('behind origin/main: the line stays',
                      not prs.holds_expected_tree(clone, 'main'), ''))
        cases.append(('no origin/<expected> at all: the line stays',
                      not prs.holds_expected_tree(clone, 'nowhere'), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] for c in cases if not c[1]]
    check(f'the session-start BRANCH line fires only for an older tree '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_refresh_sources_reads_a_fetched_main():
    """The engine tip session start compares each set's engine against is
    BestPractice's main as origin has it now, never the last copy this
    clone happened to fetch.

    THE BUG (2026-10-29). Session start reported all three sets' engines
    STALE against origin/main d04672e86b31, nine days old in a clone that
    had not fetched it; the real main was aa34219d3. Real git, hermetic: a
    bare origin, a clone, one commit pushed to origin's main after the
    clone. CONTROL: with origin unreachable, the old copy is named, with
    its date.

    Negative control, measured 2026-10-29: head_commit as it was reads the
    clone's old origin/main, so the first case fails."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    saved_root = prs.ROOT
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-fetched-main-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t',
               GIT_COMMITTER_DATE='2026-10-20T12:00:00+00:00',
               GIT_AUTHOR_DATE='2026-10-20T12:00:00+00:00')

    def g(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), '-c', 'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env).stdout.strip()
    try:
        origin, seed, clone = tmp / 'origin.git', tmp / 'seed', tmp / 'clone'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        g(tmp, 'clone', '-q', str(origin), str(seed))
        (seed / 'f.txt').write_text('one\n', encoding='utf-8')
        g(seed, 'add', '-A'); g(seed, 'commit', '-qm', 'one'); g(seed, 'push', '-q', 'origin', 'main')
        g(tmp, 'clone', '-q', str(origin), str(clone))
        old = g(clone, 'rev-parse', 'origin/main')
        (seed / 'f.txt').write_text('two\n', encoding='utf-8')
        g(seed, 'commit', '-qam', 'two'); g(seed, 'push', '-q', 'origin', 'main')
        new = g(seed, 'rev-parse', 'HEAD')
        prs.ROOT = clone                  # what the tool reads as BestPractice
        tip, ref = prs.head_commit()
        cases.append(('main pushed after the clone: the tip is the new main',
                      tip == new and ref == 'origin/main', f'{tip} {ref}'))
        g(seed, 'commit', '-q', '--allow-empty', '-m', 'three')
        g(seed, 'push', '-q', 'origin', 'main')
        g(clone, 'remote', 'set-url', 'origin', str(tmp / 'gone.git'))
        tip, ref = prs.head_commit()
        cases.append(('CONTROL: origin unreachable -- the copy here is used, '
                      'and the ref says it was not fetched and how old it is',
                      tip == new and 'could not fetch' in ref
                      and '2026-10-20' in ref and old != new, f'{tip} {ref}'))
    finally:
        prs.ROOT = saved_root
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + ' -- ' + c[2] for c in cases if not c[1]]
    check(f'session start compares engines against a fetched main '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_refresh_sources_never_fetches_the_branch_a_clone_sits_on():
    """THE BUG (2026-10-14). A session that attaches a set gets the clone
    on the session's own branch, which origin has never had. For a set
    declaring no base_branch, the branch to bring it current on fell back
    to the branch it sat on, so session start printed "FAIL current: could
    not fetch origin/claude/..." and NOT APPLIED for precedent-shared-ladder
    while the two sets declaring main were brought current. Since then the
    target is the declared branch, else the bootstrap's pin, never the
    current one. Real git, hermetic: a bare origin with no HEAD symref in
    the clone, the clone on a local-only branch, origin one commit ahead.

    A. the branch it is brought current on is main, not the one it sits on;
    B. make_current on it fetches main and fast-forwards, and the clone is
       NOT switched off its branch (todo-2026-10-07-one-sets-update-moves-
       another-sets-working-branch);
    C. CONTROL: with a commit of its own there, it is refused, unchanged;
    D. a declared base_branch still wins."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-starter-branch-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), '-c', 'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env).stdout.strip()
    cases = []
    try:
        seed, origin = tmp / 'seed', tmp / 'origin.git'
        seed.mkdir()
        g(seed, 'init', '-q', '-b', 'main')
        (seed / 'precedent.json').write_text('{}\n', encoding='utf-8')
        g(seed, 'add', '-A'); g(seed, 'commit', '-qm', 'one')
        subprocess.run(['git', 'clone', '-q', '--bare', str(seed), str(origin)],
                       capture_output=True)

        def starter(name):
            c = tmp / name
            subprocess.run(['git', 'clone', '-q', str(origin), str(c)], capture_output=True)
            g(c, 'remote', 'set-head', 'origin', '-d')
            g(c, 'checkout', '-q', '-b', 'claude/starter-abc12')
            return c
        clone, own = starter('clone'), starter('own')
        (own / 'mine.md').write_text('mine\n', encoding='utf-8')
        g(own, 'add', '-A'); g(own, 'commit', '-qm', 'mine')
        own_head = g(own, 'rev-parse', 'HEAD')
        (seed / 'p.md').write_text('two\n', encoding='utf-8')
        g(seed, 'add', '-A'); g(seed, 'commit', '-qm', 'two')
        g(seed, 'push', '-q', str(origin), 'main')

        want = prs._pinned_branch(clone)
        cases.append(('A. brought current on main, not the branch it sits on',
                      want == 'main', want))
        ok, note = prs.make_current(clone, want)
        cases.append(('B. fetched main and fast-forwarded, still on its own branch',
                      ok and g(clone, 'rev-parse', 'HEAD') == g(seed, 'rev-parse', 'HEAD')
                      and g(clone, 'rev-parse', '--abbrev-ref', 'HEAD')
                      == 'claude/starter-abc12', note))
        cases.append(('B2. ...and the line names the branch that moved '
                      '(2026-10-18: a working branch moved with only "now at '
                      'origin/main" said)',
                      'moved branch claude/starter-abc12' in note, note))
        ok_o, note_o = prs.make_current(own, prs._pinned_branch(own))
        cases.append(('C. CONTROL: a commit of its own is refused, unchanged',
                      not ok_o and g(own, 'rev-parse', 'HEAD') == own_head
                      and 'local commit' in note_o, note_o))
        (clone / 'precedent.json').write_text('{"base_branch": "trunk"}\n',
                                              encoding='utf-8')
        cases.append(('D. a declared base_branch still wins',
                      prs._pinned_branch(clone) == 'trunk', prs._pinned_branch(clone)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'refresh never fetches the branch a source clone sits on '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_refresh_sources_leaves_the_base_branch_clean():
    """The session-start refresh commits on a dated local branch of its own
    and returns the set to its base branch with nothing uncommitted
    (2026-10-07: it left 21 engine files as edits on a set's main
    checkout, and the stop hook then asked a session to commit and push
    them -- on main). Real git: a second run for the same engine tip names
    the branch it already made rather than make another, and a refresh that
    changes nothing leaves no branch behind."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-branch-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(*a):
        return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                              text=True, env=env).stdout.strip()
    saved = prs.apply_to
    try:
        repo = tmp / 'set'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        (repo / 'engine.txt').write_text('old\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')

        def fake_apply(e, commit=False, branch=None, body='new\n'):
            (repo / 'engine.txt').write_text(body, encoding='utf-8')
            g('checkout', '-q', '-B', branch)
            g('add', '-A')
            r = subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'refresh'],
                               capture_output=True, text=True, env=env)
            return [('refresh', True, ''), ('branch', True, ''),
                    ('commit', r.returncode == 0, r.stdout + r.stderr)]
        prs.apply_to = fake_apply
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': 'abcdef1234567'}, 'main')
        branches = g('branch', '--format=%(refname:short)').split()
        made = [b for b in branches if '-engine-refresh-abcdef12-' in b]
        cases.append(('the refresh is committed on a dated branch of its own',
                      len(made) == 1, f'{branches} {steps}'))
        cases.append(('...and the set is back on main', g('branch', '--show-current') == 'main',
                      g('branch', '--show-current')))
        cases.append(('...with nothing uncommitted', g('status', '--porcelain') == '',
                      g('status', '--porcelain')))
        cases.append(('...and main itself unchanged',
                      (repo / 'engine.txt').read_text(encoding='utf-8') == 'old\n', ''))
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': 'abcdef1234567'}, 'main')
        cases.append(('a second run for the same tip names that branch and makes no other',
                      'already committed on local branch' in steps[0][2]
                      and len([b for b in g('branch', '--format=%(refname:short)').split()
                               if 'engine-refresh' in b]) == 1, str(steps)))
        prs.apply_to = lambda e, commit=False, branch=None: fake_apply(e, commit, branch, 'old\n')
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': '9999999912345'}, 'main')
        cases.append(('a refresh that changes nothing leaves no branch behind',
                      not [b for b in g('branch', '--format=%(refname:short)').split()
                           if '-engine-refresh-99999999-' in b]
                      and g('branch', '--show-current') == 'main', str(steps)))

        # SUPERSEDED REFRESH BRANCHES GO, AND THE RUN SAYS SO (2026-10-17).
        # A commit with the tool's own subject, as apply_to really writes it.
        def real_apply(e, commit=False, branch=None, body='newer\n'):
            (repo / 'engine.txt').write_text(body, encoding='utf-8')
            g('checkout', '-q', '-B', branch)
            g('add', '-A')
            subprocess.run(['git', '-C', str(repo), 'commit', '-qm',
                            prs.REFRESH_SUBJECT + e['tip'][:8]],
                           capture_output=True, text=True, env=env)
            return [('refresh', True, ''), ('commit', True, 'committed')]
        prs.apply_to = lambda e, commit=False, branch=None: real_apply(e, commit, branch, 'v1\n')
        prs.apply_on_its_own_branch({'repo': repo, 'tip': '1111111112345'}, 'main')
        older = [b for b in g('branch', '--format=%(refname:short)').split()
                 if '-engine-refresh-11111111-' in b]
        g('checkout', '-q', '-b', 'keep-engine-refresh-mine', 'main')
        (repo / 'mine.txt').write_text('work\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', prs.REFRESH_SUBJECT + 'x')
        (repo / 'mine2.txt').write_text('more\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'my own work')
        g('checkout', '-q', 'main')
        prs.apply_to = lambda e, commit=False, branch=None: real_apply(e, commit, branch, 'v2\n')
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': '2222222212345'}, 'main')
        now = g('branch', '--format=%(refname:short)').split()
        said = ' '.join(d for _s, _ok, d in steps)
        cases.append(('a newer refresh removes the older refresh-only branch',
                      bool(older) and older[0] not in now
                      and any('-engine-refresh-22222222-' in b for b in now),
                      f'{now} {steps}'))
        cases.append(('...and names it in what the run reports',
                      bool(older) and older[0] in said and 'removed 1' in said, said[:300]))
        cases.append(('...and never a branch carrying work of its own',
                      'keep-engine-refresh-mine' in now, str(now)))

        # A REFRESH THAT STOPS SHORT OF ITS COMMIT IS UNDONE (2026-10-20: a
        # refused commit left the ladder set's checkout on the refresh
        # branch with 22 engine paths staged, read as unsaved work). The
        # engine is written, a new file among it, and the commit refuses.
        def refused_apply(e, commit=False, branch=None):
            (repo / 'engine.txt').write_text('half\n', encoding='utf-8')
            (repo / 'new_engine.py').write_text('x\n', encoding='utf-8')
            g('checkout', '-q', '-B', branch)
            g('add', '-A')
            return [('refresh', True, ''), ('branch', True, ''),
                    ('commit', False, 'REFUSED, nothing committed: no identity')]
        prs.apply_to = refused_apply
        before_engine = (repo / 'engine.txt').read_text(encoding='utf-8')
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': '3333333312345'}, 'main')
        cases.append(('a refresh whose commit is refused is undone: back on main, nothing '
                      'uncommitted, no refresh branch left',
                      g('branch', '--show-current') == 'main'
                      and g('status', '--porcelain') == ''
                      and not (repo / 'new_engine.py').exists()
                      and (repo / 'engine.txt').read_text(encoding='utf-8') == before_engine
                      and not [b for b in g('branch', '--format=%(refname:short)').split()
                               if '-engine-refresh-33333333-' in b], str(steps)))
        cases.append(('...and the run says it undid it, in its own words',
                      any(s[0] == 'undone' and s[1]
                          and 'did not commit, so it was undone' in s[2]
                          for s in steps), str(steps)))
        # CONTROL: a person's uncommitted file was there first. Nothing is
        # reset, and the row says why (practice: repair-cannot-discard-work).
        (repo / 'person.txt').write_text('mine\n', encoding='utf-8')
        steps = prs.apply_on_its_own_branch({'repo': repo, 'tip': '4444444412345'}, 'main')
        cases.append(('with a person\'s edit already there, nothing is reset and the row '
                      'says NOT undone',
                      (repo / 'person.txt').read_text(encoding='utf-8') == 'mine\n'
                      and any(s[0] == 'undone' and not s[1] and 'NOT undone' in s[2]
                              for s in steps), str(steps)))
    finally:
        prs.apply_to = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the session-start refresh leaves the set\'s base branch clean '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_refresh_sources_path_names_the_whole_target():
    """`--apply --path X` writes into X and nothing else. It used to ADD X to
    the scan, so refreshing one named set also rewrote every other set beside
    the checkout and under $HOME -- on 2026-09-26, the session's own source
    clones, left holding uncommitted engine output nobody had asked for.

    Both worlds planted (practice: checks-plant-their-state): two stale
    practice sets, one named; only the named one reaches the writers, the
    other is reported LEFT ALONE. CONTROL: the same fixture with no --path
    writes both, so the quiet case comes from the scoping (practice:
    control-asserts-which-failure). Hermetic: the writers are stubbed to
    record who they were called for, and nothing is fetched."""
    import contextlib, io, json as _j, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-path-scope-'))

    def plant(name):
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True, exist_ok=True)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(_j.dumps(
            {'kind': 'source', 'source_commit': 'fixture-old'}), encoding='utf-8')
        return repo.resolve()

    names = ('candidate_dirs', 'head_commit', 'apply_to', 'repair_hooks',
             'classify_dirt', 'make_current', '_declared_base_branch',
             'ensure_source_credentials')
    saved = {n: getattr(prs, n) for n in names}
    wrote = []
    try:
        a, b = plant('named-set'), plant('other-set')
        prs.candidate_dirs = lambda extra=(): [a, b]
        prs.head_commit = lambda: ('fixture-tip', 'origin/fixture')
        prs.ensure_source_credentials = lambda found: []
        prs.classify_dirt = lambda repo: ([], [])
        prs.make_current = lambda repo, want: (True, 'fixture')
        prs._declared_base_branch = lambda repo: 'main'
        prs.repair_hooks = lambda repo: (wrote.append(pathlib.Path(repo).resolve()),
                                         (True, 'fixture'))[1]
        prs.apply_to = lambda e, commit=False, branch=None: (
            wrote.append(pathlib.Path(e['repo']).resolve()), [])[1]

        def run(argv):
            wrote.clear()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                prs.main(argv)
            return set(wrote), buf.getvalue()

        got, out = run(['--apply', '--path', str(a)])
        cases.append(('the set --path names is written', a in got, failure_detail(out, 600)))
        cases.append(('...and the set it does not name is not', b not in got,
                      failure_detail(out, 600)))
        cases.append(('...and is reported LEFT ALONE as not named',
                      'LEFT ALONE: not named' in out, failure_detail(out, 600)))
        got, out = run(['--apply'])
        cases.append(('CONTROL: with no --path both sets are written, so the '
                      'quiet case above came from the scoping',
                      a in got and b in got, failure_detail(out, 600)))
    finally:
        for n, f in saved.items():
            setattr(prs, n, f)
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'refresh --apply --path writes only the repos it names '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_refresh_sources_lists_a_linked_tree_once():
    """candidate_dirs() returns one entry per working tree. The source
    bootstrap leaves a symlink at the attach path pointing to the declared
    clone; the refresh used to list both, fetch the one tree twice under two
    labels, and on 2026-09-29 print one as failed and the other as current,
    which read as a duplicate clone that did not exist.

    Planted: a checkout, a declared clone outside its parent, and a sibling
    symlink to that clone. CONTROL: a second, separate tree at a sibling path
    is still listed, so the dedupe is by tree and not by name (practice:
    control-asserts-which-failure). Hermetic: ROOT and declared_paths are
    stubbed, nothing is fetched."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_refresh_sources as prs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refresh-linked-tree-'))
    saved = (prs.ROOT, prs.declared_paths)
    try:
        work, home = tmp / 'work', tmp / 'home'
        checkout = work / 'consumer'
        declared = home / 'precedent-individual'
        for d in (checkout, declared):
            d.mkdir(parents=True)
        (work / 'precedent-individual').symlink_to(declared,
                                                   target_is_directory=True)
        prs.ROOT = checkout
        prs.declared_paths = lambda: [declared.resolve()]
        got = [p.resolve() for p in prs.candidate_dirs()]
        cases.append(('a sibling symlink to the declared clone is one entry',
                      got.count(declared.resolve()) == 1, str(got)))
        cases.append(('...and the checkout itself is not listed',
                      checkout.resolve() not in got, str(got)))
        other = work / 'acme-shared-writing'
        other.mkdir()
        got = [p.resolve() for p in prs.candidate_dirs()]
        cases.append(('CONTROL: a separate sibling tree is still listed',
                      other.resolve() in got
                      and got.count(declared.resolve()) == 1, str(got)))
    finally:
        prs.ROOT, prs.declared_paths = saved
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'refresh lists a symlinked source tree once '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_stale_source_paths_accepts_the_universal_pair():
    """The universal source is `precedent` at `../BestPractice` by design --
    precedent_bootstrap_source.py writes that pair -- so the stale-path
    report must not tell anyone to repoint it; `../precedent` names no clone.
    A real mismatch is still caught (practice: control-asserts-which-failure)."""
    import json as _j, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='stale-source-paths-'))
    try:
        (tmp / 'precedent.json').write_text(_j.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '../BestPractice'},
            {'level': 'shared', 'name': 'acme-shared-writing',
             'path': '../acme-shared-writing'},
            {'level': 'shared', 'name': 'precedent-shared-x',
             'path': '../precedent-team-x'}]}), encoding='utf-8')
        got = [n for n, _p, _w in pve.stale_source_paths(tmp)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check('stale_source_paths leaves the universal precedent/../BestPractice '
          'pair alone and still flags a renamed set',
          got == ['precedent-shared-x'], f'flagged: {got}')

def check_refresh_wired_settings_is_not_lost_work():
    """A source clone's .claude/settings.json that differs from its commit
    only by hook entries the refresh wires in is engine output, not a
    person's work. On 2026-09-26 all four set clones read as "uncommitted
    changes" over exactly that, and the archive gate said "Don't archive
    this session" on every reply about an edit the next session's refresh
    makes again. The file is also a person's, so the other half matters as
    much: any edit that is not that exact shape stays theirs.

    Stated cases for the shape test, then both halves through
    classify_dirt in a real clone, with a control (practice:
    control-asserts-which-failure)."""
    import tempfile
    import precedent_vendor_engine as pve
    import precedent_refresh_sources as rs
    cases = []
    cmd = '$CLAUDE_PROJECT_DIR/.claude/hooks/'
    base = {'permissions': {'allow': ['Bash(git status)']},
            'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [
                {'type': 'command', 'command': cmd + 'freshness-guard.sh pre-write main'}]}]}}

    def with_hooks(extra_pre=(), new_groups=(), perms=None):
        d = json.loads(json.dumps(base))
        d['hooks']['PreToolUse'][0]['hooks'].extend(extra_pre)
        d['hooks']['PreToolUse'].extend(new_groups)
        if perms is not None:
            d['permissions'] = perms
        return json.dumps(d, indent=2)

    before = json.dumps(base, indent=2)
    wf = {'type': 'command', 'command': cmd + 'workflow-write-gate.sh'}
    wired = with_hooks(new_groups=[{'matcher': pve.WORKFLOW_WRITE_MATCHER,
                                    'hooks': [wf]}])
    shape = pve.settings_change_is_wiring_only
    cases.append(('a new group holding a hook HOOK_WIRING lists is wiring',
                  shape(before, wired), wired))
    cases.append(('an entry appended to an existing group is wiring',
                  shape(before, with_hooks(extra_pre=[
                      {'type': 'command', 'command': cmd + 'doc-lint-gate.sh'}])), ''))
    cases.append(("a person's permissions edit beside the wiring is NOT",
                  not shape(before, with_hooks(
                      new_groups=[{'matcher': 'x', 'hooks': [wf]}],
                      perms={'allow': ['Bash(*)']})), ''))
    cases.append(('read-only Precedent tool allow rules the refresh appends are '
                  'refresh output (2026-10-14)',
                  shape(before, with_hooks(new_groups=[{'matcher': 'x', 'hooks': [wf]}],
                                           perms={'allow': [
                                               'Bash(git status)',
                                               'Bash(python3 tools/precedent_show.py *)']}))
                  and shape(json.dumps(dict(base, permissions={'allow': ['Bash(ls)']})),
                            json.dumps(dict(base, permissions={'allow': [
                                'Bash(ls)', 'Bash(python3 tools/doc_lint.py)']}))), ''))
    cases.append(('a hook HOOK_WIRING does not list is NOT',
                  not shape(before, with_hooks(extra_pre=[
                      {'type': 'command', 'command': cmd + 'my-own-hook.sh'}])), ''))
    edited = json.loads(before)
    edited['hooks']['PreToolUse'][0]['hooks'][0]['command'] += ' --loud'
    cases.append(('an existing entry changed in place is NOT',
                  not shape(before, json.dumps(edited)), ''))
    cases.append(('no change, or unparseable JSON, is NOT',
                  not shape(before, before) and not shape(before, '{oops'), ''))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='wired-settings-'))
    try:
        def git(*a):
            return subprocess.run(['git', '-C', str(tmp), *a],
                                  capture_output=True, text=True)
        git('init', '--quiet')
        git('config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        git('config', 'user.name', 'Fixture')
        (tmp / '.claude').mkdir()
        sp_ = tmp / '.claude' / 'settings.json'
        sp_.write_text(before + '\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '--quiet', '-m', 'first')
        sp_.write_text(wired + '\n', encoding='utf-8')
        engine, other = rs.classify_dirt(tmp)
        cases.append(('classify_dirt: refresh-wired settings.json is engine dirt',
                      engine == ['.claude/settings.json'] and not other,
                      f'engine={engine} other={other}'))
        sp_.write_text(with_hooks(new_groups=[{'matcher': 'x', 'hooks': [wf]}],
                                  perms={'allow': ['Bash(*)']}) + '\n',
                       encoding='utf-8')
        engine, other = rs.classify_dirt(tmp)
        cases.append(("classify_dirt: a person's edit to it stays theirs",
                      other == ['.claude/settings.json'] and not engine,
                      f'engine={engine} other={other}'))
        sp_.write_text(wired + '\n', encoding='utf-8')
        saved = pve.HOOK_WIRING
        try:
            pve.HOOK_WIRING = {}
            engine, other = rs.classify_dirt(tmp)
        finally:
            pve.HOOK_WIRING = saved
        cases.append(('CONTROL: with HOOK_WIRING empty the same file is a '
                      "person's, so the verdict comes from the wiring list",
                      other == ['.claude/settings.json'] and not engine,
                      f'engine={engine} other={other}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a settings.json the refresh only wired hooks into is engine output, '
          f'and any other edit to it is a person\'s ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_refreshed_agents_block_is_not_lost_work():
    """A source clone's AGENTS.md whose only change is inside its generated
    blocks is the refresh's output; any change outside them is a person's.

    On 2026-10-05 a startup refresh rewrote precedent-shared-ladder's loader
    block, AGENTS.md read as uncommitted work, the clone was not brought up
    to its own origin/main and the container check said the session could
    not be archived -- over a block a rebuild reproduced byte for byte. The
    file is mostly a person's prose, so the other half matters as much."""
    import tempfile
    import precedent_refresh_sources as rs
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='agents-block-'))
    head = '# Notes\n\nA person wrote this.\n\n'
    block = ('<!-- BEGIN GENERATED: precedent-loader -->\n{}\n'
             '<!-- END GENERATED -->\n')
    tail = '\n## Working here\n\nMore prose.\n'
    try:
        def git(*a):
            return subprocess.run(['git', '-C', str(tmp), *a],
                                  capture_output=True, text=True)
        git('init', '--quiet')
        git('config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        git('config', 'user.name', 'Fixture')
        f = tmp / 'AGENTS.md'
        f.write_text(head + block.format('old index') + tail, encoding='utf-8')
        git('add', '-A')
        git('commit', '--quiet', '-m', 'first')

        def verdict(text):
            f.write_text(text, encoding='utf-8')
            return rs.classify_dirt(tmp)
        engine, other = verdict(head + block.format('new index\nlonger') + tail)
        cases.append(('a rewritten loader block alone is engine dirt',
                      engine == ['AGENTS.md'] and not other,
                      f'engine={engine} other={other}'))
        engine, other = verdict(head.replace('wrote', 'edited') +
                                block.format('new index') + tail)
        cases.append(("one word of prose changed beside it is a person's",
                      other == ['AGENTS.md'] and not engine,
                      f'engine={engine} other={other}'))
        engine, other = verdict(head + tail)
        cases.append(("the block removed is a person's, never engine output",
                      other == ['AGENTS.md'] and not engine,
                      f'engine={engine} other={other}'))
        git('checkout', '--quiet', '--', 'AGENTS.md')
        f.write_text('# Notes\n\nNo block at all.\n', encoding='utf-8')
        git('commit', '--quiet', '-am', 'no block')
        engine, other = verdict('# Notes\n\nNo block, edited.\n')
        cases.append(("CONTROL: a file with no generated block is a person's",
                      other == ['AGENTS.md'] and not engine,
                      f'engine={engine} other={other}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an AGENTS.md the refresh only rewrote the generated block of is '
          f'engine output, and any other edit to it is a person\'s '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))

def check_individual_set_is_charged_to_its_own_budget():
    """When the person's individual set declares `individual_set_tokens`, its
    share of the session file is charged to that budget, not to each
    repository's ceiling; over that budget is a finding of its own.
    Undeclared, nothing changes.

    WHY. Morgan, 2026-10-20 (strength: decided, "7 option 1"): in a voice
    repository ~1,176 of ~1,510 tokens were the individual set, against a
    400-token ceiling, and every session start there failed for rules the
    repository cannot shorten. The measurements are stood in here, so the
    case checks the charge, not this machine's sets.

    Negative control, measured 2026-10-20 on the old code: with the budget
    declared the repository is still charged ~1,510."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_practices as psp
    import precedent_session_check as psc
    import precedent_check as pc
    cases = []
    saved = {k: getattr(psp, k) for k in ('individual_share', '_brought_renders',
                                          'brought_budget')}
    key = getattr(psp, 'INDIVIDUAL_BUDGET_KEY', 'individual_set_tokens')
    declared = {'v': 1500}
    try:
        psp.individual_share = lambda repo: 1176
        psp._brought_renders = lambda repo: (None, None, [])
        psp.brought_budget = lambda repo=None, key0='brought_sets_tokens', **kw: (
            (declared['v'] if kw.get('key', key0) == key else None), '/nowhere')
        got = psp.charged_to_repo(ROOT, 1510)[0]
        cases.append(('THE DISCRIMINATING CASE: declared, the repository is charged '
                      'only its own part', got == 334, repr(got)))
        _charged, note, over = psc._charge_brought_share(1510)
        cases.append(('...the session check names the individual share against its '
                      'budget, not over it', '~1,176 from your individual set' in note
                      and over is None, repr((note, over))))
        cases.append(('...and no longer says the repository pays for it',
                      psc._individual_part(1510, 400) == '', ''))
        declared['v'] = 1000
        _charged, note, over = psc._charge_brought_share(1510)
        cases.append(('over its own budget: the session check says so',
                      bool(over) and key in over and '1,000' in over, repr(over)))
        _charged, finding = pc._charge_brought_share(1510)
        cases.append(('...and the full check finds it, naming the budget',
                      finding is not None and key in str(getattr(finding, 'detail',
                                                                  finding)),
                      repr(finding)))
        declared['v'] = None
        got = psp.charged_to_repo(ROOT, 1510)[0]
        cases.append(('negative control: undeclared, the repository is charged the '
                      'whole file, as before', got == 1510, repr(got)))
    finally:
        for k, v in saved.items():
            setattr(psp, k, v)
        sys.path.pop(0)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the individual set is charged to its own budget when it declares one '
          f'({len(cases)} stated cases)', not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_session_check_names_a_declared_retired_set():
    """The session check fails one row when precedent.json still declares a
    set that says it is retired, and names the update that drops it.

    WHY. 2026-10-06, a consumer still declared two sets retired that day;
    one rewrote a check on its way out, a check reading its clone refused
    every push while the view sync said all was current, and nothing said
    "retired" anywhere."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_check as psc
    cases = []
    saved = psc.ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            repo, old = td / 'repo', td / 'old-set'
            (old / 'practices').mkdir(parents=True)
            repo.mkdir()
            (repo / 'precedent.json').write_text(json.dumps({'sources': [
                {'level': 'shared', 'name': 'old-set', 'path': '../old-set'}]}),
                encoding='utf-8')
            psc.ROOT = repo
            cases.append(('an active set: no row', psc._retired_sources_rows() == []))
            (old / 'precedent-source.json').write_text(json.dumps(
                {'retired': {'date': '2026-10-06', 'folded_into': ['universal']}}),
                encoding='utf-8')
            rows = psc._retired_sources_rows()
            cases.append(('a retired one: one failing row naming it and the update',
                          len(rows) == 1 and rows[0][1] is False
                          and 'old-set' in rows[0][2]
                          and 'precedent_update.py' in rows[0][2]))
    finally:
        psc.ROOT = saved
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'the session check names a declared set that retired itself '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_source_bootstrap_keeps_what_git_said():
    """precedent_source_bootstrap keeps git's output for a failed clone
    where the credentials check can quote it, removes it once the clone
    succeeds, and tries once more only after a failure that can pass on its
    own -- HTTP 429 or a dropped network, never an access failure.

    WHY. 2026-10-09: a consumer's session saw "look at what git said" and
    had nothing to look at; the hook's stderr had scrolled past at session
    start."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_bootstrap as _psb
    cases = []
    for text, want in (('error: RPC failed; HTTP 429 curl 22', True),
                       ('fatal: unable to access: Connection reset by peer', True),
                       ('fatal: unable to access: Could not resolve host: x', True),
                       ('fatal: Authentication failed for https://x', False),
                       ('error: RPC failed; HTTP 403 curl 22', False),
                       ('remote: Repository not found.', False)):
        cases.append((f'transient({text!r}) is {want}',
                      _psb._transient(text) is want, ''))
    saved = _psb._try_sync
    try:
        for first, want_calls, want_ok in (
                ('error: RPC failed; HTTP 429', 2, True),
                ('fatal: Authentication failed', 1, False)):
            calls, sleeps = [], []

            def fake(url, path, branch=None, _first=first):
                calls.append(url)
                return (False, _first) if len(calls) == 1 else (True, '')
            _psb._try_sync = fake
            with tempfile.TemporaryDirectory() as td:
                ok, _ = _psb.ensure_source('shared', 'x', 'file:///nowhere',
                                           pathlib.Path(td) / 'x', None,
                                           sleep=sleeps.append)
            cases.append((f'after {first!r}: {want_calls} attempt(s)',
                          len(calls) == want_calls and ok is want_ok
                          and len(sleeps) == want_calls - 1,
                          f'calls={len(calls)} ok={ok} sleeps={sleeps}'))
    finally:
        _psb._try_sync = saved
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        env_was = os.environ.get(_psb.CLONE_NOTES_ENV)
        os.environ[_psb.CLONE_NOTES_ENV] = str(td / 'notes.json')
        try:
            repo = td / 'repo'
            repo.mkdir()
            (repo / 'precedent.json').write_text(json.dumps({'sources': [
                {'level': 'shared', 'name': 'precedent-shared-fx',
                 'path': '../precedent-shared-fx'}]}), encoding='utf-8')
            base = td / 'origin'
            base.mkdir()
            _psb.sources_from_repo(repo, base_url=base.as_uri())
            note = _psb.read_clone_failures().get('precedent-shared-fx') or {}
            cases.append(('a failed clone leaves git\'s own output, kept for '
                          'the later gate', bool(note.get('output')), str(note)))
            src = base / 'precedent-shared-fx'
            (src / 'practices').mkdir(parents=True)
            (src / 'practices' / 'a.md').write_text('x\n', encoding='utf-8')
            g = ['git', '-C', str(src), '-c', 'user.name=t', '-c',
                 'user.email=t@example.com']
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(src)], check=True)
            subprocess.run(g + ['add', '-A'], check=True)
            subprocess.run(g + ['commit', '-qm', 'x'], check=True)
            res = _psb.sources_from_repo(repo, base_url=base.as_uri())
            cases.append(('...and once the clone succeeds the note is gone',
                          'precedent-shared-fx' not in _psb.read_clone_failures()
                          and any(ok for _, ok, _ in res), str(res)))
        finally:
            if env_was is None:
                os.environ.pop(_psb.CLONE_NOTES_ENV, None)
            else:
                os.environ[_psb.CLONE_NOTES_ENV] = env_was
    sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the source bootstrap keeps what git said and retries only a '
          f'transient failure ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_source_credentials():
    """tools/precedent_source_credentials.py, and the one property that
    matters most about it: the token never leaves the environment.

    The mechanism exists because `add_repo` refuses across GitHub owners
    (reproduced 2026-09-09 as a session's first tool call), so a private
    practice source has to be reachable some other way. What it cannot do is
    trade that problem for a worse one -- a secret written into a clone's
    .git/config, or into an argument list, is a secret somebody commits
    later. Cases 2, 3 and 7 are that property, asserted three ways.

    Every case here is hermetic: a file:// fixture, a fixture HOME, and a
    fixture repo whose precedent.json this test wrote
    (practice: fixture-owns-its-state). Nothing touches the network, and no
    case reads this container's own real credentials.

    NEGATIVE CONTROL, RUN 2026-09-09 rather than assumed
    (practice: control-asserts-which-failure). The helper was rewritten to
    interpolate the token's VALUE instead of its variable name, and case 2's
    "the token itself never appears in the arguments" went red, printing the
    fixture token in its own failure detail. So the case can fail, and it
    fails for the reason it claims to watch."""
    import shutil, tempfile

    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    import precedent_source_bootstrap as psb   # BASE_URL_ENV lives with the
    # tool that clones, not with the tool that reports -- the bootstrap has
    # to keep working in a tree vendored before the credentials module
    # existed, so it owns nothing it cannot resolve alone.

    TOKEN = 'fixture-token-never-a-real-one'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-source-cred-'))
    cases = []
    try:
        tool = ROOT / 'tools' / 'precedent_source_credentials.py'
        url = 'https://github.com/example/precedent-individual'

        # --- 1: no token, no credential flags ------------------------------
        args = psc.credential_args(url, env={})
        cases.append(('no token means no credential flags at all',
                      args == [], repr(args)))

        # --- 2: a token produces flags, and is NOT in them ------------------
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN})
        joined = ' '.join(args)
        cases.append(('a token produces a helper that git can use',
                      len(args) == 4 and args[0] == '-c'
                      and 'credential.helper=' in args[1]
                      and psc.TOKEN_ENV in joined, repr(args)))
        cases.append(('the token itself never appears in the arguments -- '
                      'only the NAME of the variable git should read',
                      TOKEN not in joined, repr(args)))

        # --- 3: a hostile username cannot break out of the helper snippet ---
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN,
                                             psc.TOKEN_USER_ENV: 'evil; rm -rf /'})
        cases.append(('a username that is not a plain identifier falls back '
                      'to the default rather than reaching the shell',
                      'rm -rf' not in ' '.join(args)
                      and f'username={psc.DEFAULT_TOKEN_USER}' in ' '.join(args),
                      repr(args)))
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN,
                                             psc.TOKEN_USER_ENV: 'git-user_1.x'})
        cases.append(('a legitimate username override is honoured',
                      'username=git-user_1.x' in ' '.join(args), repr(args)))

        # --- 3b: the opt-in inherit mode -----------------------------------
        # Measured 2026-09-09 rather than reasoned about: `inherit` against a
        # real cross-owner private repo in this container was REFUSED by
        # GitHub ("Invalid username or token"), which is the outcome the mode
        # exists to make legible -- a credential was sent and rejected, not
        # absent. These cases assert the wiring that produced that outcome.
        inh = {psc.TOKEN_ENV: psc.INHERIT, 'GITHUB_TOKEN': TOKEN}
        cases.append(('inherit resolves to the NAME of the variable that '
                      'actually holds a token',
                      psc.token_var(inh) == 'GITHUB_TOKEN', str(psc.token_var(inh))))
        args = psc.credential_args(url, env=inh)
        joined = ' '.join(args)
        cases.append(('...and the helper interpolates THAT variable, so the '
                      'literal word "inherit" is never sent as a password',
                      'password=$GITHUB_TOKEN' in joined
                      and psc.INHERIT not in joined, repr(args)))
        cases.append(('...and the inherited token itself still never appears '
                      'in the arguments', TOKEN not in joined, repr(args)))
        empty_inh = {psc.TOKEN_ENV: psc.INHERIT}
        cases.append(('inherit with nothing to inherit is NO credential, not '
                      'the word "inherit" sent as one',
                      psc.token_var(empty_inh) is None
                      and psc.credential_args(url, env=empty_inh) == [],
                      repr(psc.credential_args(url, env=empty_inh))))
        # --- 4: only https gets the credential -----------------------------
        for scheme in (f'file://{tmp}/x', 'ssh://example.invalid/x'  # deliberately userless: a fixture URL
                       # carrying user@host reads as an email address
                       # to the leak gate, which scans this file too,
                       'http://example.com/x'):
            args = psc.credential_args(scheme, env={psc.TOKEN_ENV: TOKEN})
            cases.append((f'a {scheme.split(":")[0]}:// url is never offered '
                          f'the credential', args == [], repr(args)))

        # --- 5: assess() tells the three states apart ----------------------
        repo = tmp / 'consumer'
        (repo / 'local').mkdir(parents=True)
        home_empty = tmp / 'home-empty'
        (home_empty / '.config' / 'precedent').mkdir(parents=True)
        (home_empty / '.config' / 'precedent' / 'config.json').write_text(
            '{"format_version": 1}\n', encoding='utf-8')

        def write_cfg(team_path, level='team', name='precedent-team-fixture'):
            sources = [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                       {'level': 'repo-local', 'name': 'local', 'path': 'local'}]
            if team_path is not None:
                sources.insert(1, {'level': level, 'name': name,
                                   'path': team_path})
            (repo / 'precedent.json').write_text(
                json.dumps({'format_version': 1, 'sources': sources}), encoding='utf-8')

        # A set declared the CURRENT way, "level": "shared", and missing.
        # Until 2026-09-29 only the old spelling "team" was read here, so this
        # set was skipped and never reported missing -- the retired word hid
        # the bug. Both spellings must be reported.
        write_cfg('../precedent-shared-fixture', level='shared',
                  name='precedent-shared-fixture')
        why = psc.unresolved_private_sources(repo, env={'HOME': str(home_empty)})
        cases.append(('a missing set declared as level "shared" is reported '
                      'missing, by name, as a shared set',
                      any(lv == 'shared' and n == 'precedent-shared-fixture'
                          for lv, n, _ in why), str(why)))
        write_cfg('../precedent-team-fixture')
        why = psc.unresolved_private_sources(repo, env={'HOME': str(home_empty)})
        cases.append(('...and one declared with the old spelling "team" still is',
                      any(n == 'precedent-team-fixture' for _, n, _ in why),
                      str(why)))
        env_no_token = {'HOME': str(home_empty)}
        verdict, message = psc.assess(repo, env=env_no_token)
        cases.append(('an unresolved private source with no token reads as '
                      'MISSING, and the message names the variable to set',
                      verdict == 'missing' and psc.TOKEN_ENV in message,
                      f'{verdict}: {message}'))

        verdict, message = psc.assess(repo, env={**env_no_token, psc.TOKEN_ENV: TOKEN})
        cases.append(('the same repo WITH a token reads as SET -- a missing '
                      'credential is explicitly not the explanation',
                      verdict == 'set' and 'not the explanation' in message,
                      f'{verdict}: {message}'))
        # The session check's row on that verdict. Until 2026-10-02 it passed
        # on SET with an empty detail, so a declared set that did not exist
        # showed green while its practices were absent all session.
        import precedent_session_check as psck
        unresolved = psc.unresolved_private_sources(
            repo, env={**env_no_token, psc.TOKEN_ENV: TOKEN})
        name, ok, detail = psck.sources_resolved_row(verdict, message,
                                                     unresolved)
        cases.append(('...and the session check FAILS its sources row on SET '
                      'when a DECLARED shared set did not resolve, naming it '
                      '-- a token being set never makes a missing set green',
                      ok is False and 'precedent-team-fixture' in detail,
                      f'{ok}: {detail}'))
        only_ind = [('individual', 'precedent-individual', 'no config')]
        cases.append(('...but SET with only the individual set unresolved '
                      'passes, with its message: a token alone is read as a '
                      'sign of an individual set the person may not have',
                      psck.sources_resolved_row('set', 'why', only_ind)[1:]
                      == (True, 'why'),
                      str(psck.sources_resolved_row('set', 'why', only_ind))))
        cases.append(('...while OK passes silently and UNCONFIGURED passes '
                      'with its message',
                      psck.sources_resolved_row('ok', 'x')[1:] == (True, '')
                      and psck.sources_resolved_row('unconfigured', 'why')[1:]
                      == (True, 'why'),
                      str((psck.sources_resolved_row('ok', 'x'),
                           psck.sources_resolved_row('unconfigured', 'why')))))
        cases.append(('...and MISSING fails with its message',
                      psck.sources_resolved_row('missing', 'why')[1:]
                      == (False, 'why'),
                      str(psck.sources_resolved_row('missing', 'why'))))

        verdict, message = psc.assess(repo, env={**env_no_token, **empty_inh})
        cases.append(('...and assess says which of the two missing states it '
                      'is: asked to inherit, nothing there',
                      verdict == 'missing' and 'nothing to inherit' in message,
                      f'{verdict}: {message}'))
        verdict, message = psc.assess(repo, env={**env_no_token, **inh})
        cases.append(('an inherited credential reads as SET and names where '
                      'it came from, since a harness token is usually scoped '
                      'to other repositories and will be refused',
                      verdict == 'set' and 'inherited from GITHUB_TOKEN' in message,
                      f'{verdict}: {message}'))

        # both sources genuinely present -> nothing to say
        team = tmp / 'precedent-team-fixture'
        (team / 'practices').mkdir(parents=True)
        indiv = tmp / 'indiv'
        (indiv / 'practices').mkdir(parents=True)
        home_ok = tmp / 'home-ok'
        (home_ok / '.config' / 'precedent').mkdir(parents=True)
        (home_ok / '.config' / 'precedent' / 'config.json').write_text(
            json.dumps({'format_version': 1,
                        'individual': {'name': 'precedent-individual',
                                       'path': str(indiv)}}), encoding='utf-8')
        verdict, _ = psc.assess(repo, env={'HOME': str(home_ok)})
        cases.append(('every private source on disk reads as ok, with or '
                      'without a token', verdict == 'ok', verdict))
        cases.append(('and remind() then says nothing at all, so the tools '
                      'that call it stay quiet',
                      psc.remind(repo, env={'HOME': str(home_ok)}) is None,
                      str(psc.remind(repo, env={'HOME': str(home_ok)}))))

        # --- 5b: the THREE ways there is no individual source ---------------
        # Reported 2026-09-13 from a live container: PRECEDENT_GIT_TOKEN set,
        # the private repo reachable, nothing retired, and no user config at
        # all -- and this tool answered "<path> declares no individual
        # source", a statement about a file that did not exist, wrapped in a
        # credential remedy and a retirement clause neither of which applied.
        # An absent config, a malformed one and one that parses and names
        # none are three states with three remedies; `.get('individual')`
        # made them one. Each case below asserts the words ITS branch alone
        # prints (practice: control-asserts-which-failure).
        #
        # Every env here is a literal dict, so the fixture owns whether this
        # is a hosted session -- which is the axis the verdict turns on.
        home_absent = tmp / 'home-absent'          # never created: that is the case
        home_bad = tmp / 'home-bad'
        (home_bad / '.config' / 'precedent').mkdir(parents=True)
        (home_bad / '.config' / 'precedent' / 'config.json').write_text(
            '{not json', encoding='utf-8')

        for home, state, words in (
            (home_absent, 'absent', 'does not exist'),
            (home_bad, 'malformed', 'did not parse as JSON'),
            (home_empty, 'declares none', 'declares no individual source'),
        ):
            # The repo-name variable is the sign that this person HAS an
            # individual set; without any such sign a missing set is "none"
            # (asserted separately, just below).
            why = psc.unresolved_private_sources(
                repo, env={'HOME': str(home), 'PRECEDENT_INDIVIDUAL_REPO': 'file:///fixture/precedent-individual'})
            cases.append((f'a user config that is {state} is REPORTED as '
                          f'{state}, not as "declares no individual source" '
                          f'for all three', any(words in w for _, _, w in why),
                          str(why)))

        why = psc.unresolved_private_sources(
            repo, env={'HOME': str(home_absent), 'CLAUDE_CODE_REMOTE': 'true'})
        cases.append(('on a hosted session with no user config and NO sign of an individual set '
                      '(no token, base URL, repo name or clone), nothing is '
                      'reported unresolved -- the person has none',
                      why == [], str(why)))

        for home, state, words in (
            (home_absent, 'an absent', 'does not exist at all'),
            (home_bad, 'a malformed', 'did not parse as JSON'),
            (home_empty, 'a declares-nothing', 'names no individual source'),
        ):
            verdict, message = psc.assess(repo, env={'HOME': str(home),
                                                     psc.TOKEN_ENV: TOKEN})
            cases.append((f'...and on a local machine {state} config reads '
                          f'as UNCONFIGURED with its own remedy -- never as a '
                          f'credential or a retirement, which cannot write a '
                          f'config file',
                          verdict == 'unconfigured' and words in message
                          and 'RETIRED' not in message,
                          f'{verdict}: {message[:260]}'))

        # A config that will not PARSE is the one state no credential has
        # ever fixed, so it reads the same way on a hosted session too.
        verdict, message = psc.assess(repo, env={'HOME': str(home_bad),
                                                 'CLAUDE_CODE_REMOTE': 'true',
                                                 psc.TOKEN_ENV: TOKEN})
        cases.append(('a config that will not parse is UNCONFIGURED on a '
                      'hosted session as well: a token cannot repair a '
                      'syntax error', verdict == 'unconfigured', verdict))

        # ...while the two states a FAILED CLONE also leaves behind keep the
        # access path there, because the bootstrap writes the config only
        # after a clone succeeds. Claiming "not an access problem" there
        # would be the same over-reading in the other direction.
        for home, state in ((home_absent, 'an absent'),
                            (home_empty, 'a declares-nothing')):
            verdict, message = psc.assess(repo, env={'HOME': str(home),
                                                     'CLAUDE_CODE_REMOTE': 'true',
                                                     psc.TOKEN_ENV: TOKEN})
            cases.append((f'on a HOSTED session {state} config is NOT '
                          f'claimed to be free of access trouble -- it is '
                          f'what a failed clone leaves -- but the retirement '
                          f'clause goes, since no repo declares an individual '
                          f'source',
                          verdict == 'set' and 'RETIRED' not in message
                          and 'only after a clone SUCCEEDS' in message,
                          f'{verdict}: {message[:260]}'))

        # The one individual failure that IS about access: the config named a
        # path and the clone is not at it. Unchanged, retirement clause and all.
        home_gone = tmp / 'home-gone'
        (home_gone / '.config' / 'precedent').mkdir(parents=True)
        (home_gone / '.config' / 'precedent' / 'config.json').write_text(
            json.dumps({'individual': {'name': 'precedent-individual',
                                       'path': str(tmp / 'nowhere')}}),
            encoding='utf-8')
        verdict, message = psc.assess(repo, env={'HOME': str(home_gone),
                                                 psc.TOKEN_ENV: TOKEN})
        cases.append(('a config that DOES declare a source whose clone is '
                      'missing still reads as an access problem, retirement '
                      'clause and all -- the new verdict must not swallow it',
                      verdict == 'set' and 'RETIRED' in message
                      and 'not cloned at' in message,
                      f'{verdict}: {message[:260]}'))

        # --- 5c: PRECEDENT_USER_CONFIG is honoured here too -----------------
        # It was not, until 2026-09-13, and this file was the ONLY reporter in
        # the engine that ignored it: precedent_resolve.py,
        # precedent_session_check.py, precedent_identity.py and
        # precedent_time.py all read it. So somebody who had pointed it at a
        # good config was told the DEFAULT path declared no individual source
        # -- a false alarm naming a file they had deliberately not used.
        elsewhere = tmp / 'elsewhere-config.json'
        elsewhere.write_text(json.dumps(
            {'individual': {'name': 'precedent-individual', 'path': str(indiv)}}),
            encoding='utf-8')
        verdict, message = psc.assess(repo, env={'HOME': str(home_absent),
                                                 psc.USER_CONFIG_ENV: str(elsewhere),
                                                 psc.TOKEN_ENV: TOKEN})
        cases.append((f'{psc.USER_CONFIG_ENV} points the individual lookup at '
                      f'another config, exactly as it does everywhere else in '
                      f'the engine -- a good config there reads as OK, not as '
                      f'a complaint about the default path',
                      verdict == 'ok', f'{verdict}: {message[:200]}'))
        path, code = psc.individual_config_state({'HOME': str(home_absent),
                                                  psc.USER_CONFIG_ENV: str(elsewhere)})
        cases.append(('...and the path it reports is the one it actually '
                      'read', path == elsewhere and code == 'declared',
                      f'{path} {code}'))

        # --- 6: the CLI's own contract -------------------------------------
        def run(*args, env_extra=None):
            # Scrub BOTH credential variables, not just the token. A case
            # below asserts what happens with NO base url, and this harness
            # runs in a container that normally HAS one -- so the subprocess
            # inherited a real base url, tried to clone from github.com, and
            # failed on "could not read Username" instead of reporting the
            # variable as unset. The case was testing a state the fixture had
            # never established (practice: fixture-owns-its-state). Any case
            # that wants either variable supplies it through env_extra, which
            # is the only way to tell "the fixture set this" from "the
            # container happened to carry it".
            #
            # CLAUDE_CODE_REMOTE and PRECEDENT_USER_CONFIG are scrubbed for
            # the same reason, added 2026-09-13 with the config-state
            # verdict below: assess() now branches on whether this is a
            # hosted session, and resolves the user config through
            # PRECEDENT_USER_CONFIG when it is set. A container that carries
            # either -- this one carries CLAUDE_CODE_REMOTE=true -- would
            # decide the outcome of cases the fixture believes it set up
            # with HOME alone, and the harness would pass here and fail on
            # somebody's laptop. An ABSENCE is state the fixture owns too.
            env = dict(os.environ)
            env.pop(psc.TOKEN_ENV, None)
            env.pop(psb.BASE_URL_ENV, None)
            env.pop('CLAUDE_CODE_REMOTE', None)
            env.pop(psc.USER_CONFIG_ENV, None)
            if env_extra:
                env.update(env_extra)
            r = subprocess.run([sys.executable, *args], capture_output=True,
                               text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        # CLAUDE_CODE_REMOTE is set BY THE FIXTURE, not inherited: on a
        # hosted session an empty user config is also what a clone that
        # failed for want of a credential leaves behind, so MISSING is the
        # right reading there and 'unconfigured' is the right reading on a
        # local machine. Both are asserted, a few lines apart.
        hosted = {'HOME': str(home_empty), 'CLAUDE_CODE_REMOTE': 'true',
                  'PRECEDENT_INDIVIDUAL_REPO': 'file:///fixture/precedent-individual'}
        rc, out = run(str(tool), '--repo', str(repo), env_extra=hosted)
        cases.append(('the CLI reports MISSING and still exits 0 -- a missing '
                      'credential degrades a session, never takes one down',
                      rc == 0 and 'MISSING' in out, f'rc={rc} {out[:300]}'))
        rc, out = run(str(tool), '--repo', str(repo), '--check',
                      env_extra=hosted)
        cases.append(('--check is the one caller that exits 1 on MISSING',
                      rc == 1 and 'MISSING' in out, f'rc={rc} {out[:300]}'))
        rc, out = run(str(tool), '--repo', str(repo), '--check',
                      env_extra={'HOME': str(home_empty)})
        cases.append(('...but the SAME state on a local machine is '
                      'UNCONFIGURED and exits 0: nothing there is in the '
                      'wrong state, and no credential is what is missing',
                      rc == 0 and 'UNCONFIGURED' in out, f'rc={rc} {out[:300]}'))
        rc, out = run(str(tool), '--repo', str(repo), '--check',
                      env_extra={'HOME': str(home_ok)})
        cases.append(('--check exits 0 when every source is on disk '
                      '(the negative control: this case must be able to fail '
                      'the one above)', rc == 0 and 'OK' in out,
                      f'rc={rc} {out[:300]}'))

        # --- 7: end to end, the token never reaches disk --------------------
        source = tmp / 'source-repo'
        source.mkdir()
        for cmd in (['init', '-q'], ['config', 'user.email', 'harness@example.com'],
                    ['config', 'user.name', 'harness']):
            subprocess.run(['git', '-C', str(source), *cmd], check=True,
                           capture_output=True, text=True)
        (source / 'practices').mkdir()
        (source / 'practices' / 'p.md').write_text('fixture\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(source), 'add', '-A'], check=True,
                       capture_output=True, text=True)
        subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'seed'],
                       check=True, capture_output=True, text=True)

        bootstrap = ROOT / 'tools' / 'precedent_source_bootstrap.py'
        clone, config = tmp / 'clone', tmp / 'cfg.json'
        rc, out = run(str(bootstrap), '--level', 'individual', '--name',
                      'precedent-individual', '--repo-url', f'file://{source}',
                      '--clone', str(clone), '--config', str(config),
                      '--remote-only', 'false',
                      env_extra={psc.TOKEN_ENV: TOKEN})
        cloned = (clone / 'practices' / 'p.md').is_file()
        on_disk = ''
        for f in (clone / '.git' / 'config', config):
            if f.is_file():
                on_disk += f.read_text(encoding='utf-8')
        cases.append(('the bootstrap clones with a token set, and the token '
                      'is in NEITHER the clone\'s git config NOR the config '
                      'file it writes', rc == 0 and cloned and TOKEN not in on_disk,
                      f'rc={rc} cloned={cloned} {out[:300]}'))

        # --- 8: a shared source is cloned by path, and records nothing --------
        # A real repo to clone FROM, named the way the set is named: the URL
        # is built as <base>/<name>, which is the whole convention under test.
        remotes = tmp / 'remotes'
        remotes.mkdir()
        subprocess.run(['git', 'clone', '-q', f'file://{source}',
                        str(remotes / 'precedent-team-fixture')], check=True,
                       capture_output=True, text=True)
        write_cfg('../team-fixture-clone')
        rc, out = run(str(bootstrap), '--teams-from', str(repo),
                      '--remote-only', 'false',
                      env_extra={psb.BASE_URL_ENV: f'file://{remotes}',
                                 'HOME': str(home_empty)})
        # the fixture set is named precedent-team-fixture, so file://<tmp>/precedent-team-fixture
        cases.append(('--teams-from clones each declared shared source to the '
                      'sibling path the repo declares',
                      rc == 0 and (repo.parent / 'team-fixture-clone' / 'practices').is_dir(),
                      f'rc={rc} {out[:400]}'))
        cases.append(('...and writes no user config for it: a shared source '
                      'resolves by path, so there is nothing to record',
                      not (home_empty / '.config' / 'precedent' / 'config.json')
                      .read_text(encoding='utf-8').count('team'),
                      (home_empty / '.config' / 'precedent' / 'config.json')
                      .read_text(encoding='utf-8')))

        # --- 9: no base url is REPORTED, never silently skipped -------------
        shutil.rmtree(repo.parent / 'team-fixture-clone', ignore_errors=True)
        rc, out = run(str(bootstrap), '--teams-from', str(repo),
                      '--remote-only', 'false', env_extra={'HOME': str(home_empty)})
        cases.append(('with no base url the shared source is named on stderr as '
                      'NOT in force, rather than passing quietly',
                      rc == 0 and psb.BASE_URL_ENV in out
                      and 'NOT in force' in out, f'rc={rc} {out[:300]}'))

        # --- 9b: a failed clone names WHICH failure it was -----------------
        # Each branch asserts the words that branch alone prints
        # (practice: control-asserts-which-failure): "it failed" is the
        # report that sends somebody to re-issue a credential that was fine.
        # The two live strings were taken from real git output against
        # github.com on 2026-09-09, not invented -- one with no credential,
        # one with a deliberately invalid PRECEDENT_GIT_TOKEN.
        for output, want in (
            ("fatal: could not read Username for 'https://github.com': "
             "terminal prompts disabled", 'NO CREDENTIAL was available'),
            ('remote: Invalid username or token. Password authentication is '
             'not supported for Git operations.', 'AUTHENTICATION was refused'),
            ('remote: Repository not found.', 'NOT FOUND'),
            ('error: some unrelated network thing', 'it'),
        ):
            got = psb._diagnose(output)
            cases.append((f'a clone failure reading {output[:38]!r} is '
                          f'diagnosed as {want!r}, not merely as a failure',
                          # the fallback is asserted as an EXACT value: 'it'
                          # is a substring of half the English language, so
                          # `want in got` would pass on any branch at all.
                          (got == want if want == 'it' else want in got), got))

        # --- 10: the announced degradation when the module is not vendored --
        lonely = tmp / 'lonely-tools'
        lonely.mkdir()
        shutil.copy(bootstrap, lonely / bootstrap.name)
        rc, out = run(str(lonely / bootstrap.name), '--level', 'individual',
                      '--name', 'x', '--repo-url', f'file://{source}',
                      '--clone', str(tmp / 'clone2'), '--config', str(tmp / 'c2.json'),
                      '--remote-only', 'false', env_extra={psc.TOKEN_ENV: TOKEN})
        cases.append(('a bootstrap vendored WITHOUT the credentials module '
                      'says so when a token is set, naming the file and the '
                      'remedy -- it does not ignore the token in silence',
                      'precedent_source_credentials.py is not beside this file' in out
                      and 'precedent_vendor_engine.py refresh' in out,
                      f'rc={rc} {out[:400]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the private-source credential never reaches disk or argv, and its '
          f'absence is reported ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_vendored_engine_reads_the_consumer_root():
    """An engine copy vendored INSIDE another repo reads that repo's
    precedent.json -- not the vendored tree's own copy of BestPractice's.

    THE INCIDENT (practice: cite-the-incident). 2026-09-14, `Update Vendors`
    in a consumer on the classic layout: engine at `process/upstream/tools/`,
    the consumer's precedent.json two levels above it. Both runbook steps that
    reconcile sources default `--repo` to the engine's own parent, and the
    vendored tree -- being a whole copy of this repository -- HAS a
    precedent.json there. So step 7 reported three declared shared sources
    missing, by name, at `<consumer>/process/precedent-team-*`, and step 8
    left the same three UNVERIFIED. Both readings were false, both were
    specific enough to be believed, and the runbook passes no --repo.

    Hermetic: every path below is a directory this test created, and the
    helper is called with an explicit engine_root, so nothing reads this
    container's own layout (practice: fixture-owns-its-state).

    NEGATIVE CONTROL, RUN 2026-09-14 rather than assumed
    (practice: control-asserts-which-failure). `consuming_repo_root` was
    replaced with its own pre-fix behaviour -- return the engine root
    unconditionally -- and case 1 went red against the same fixture, printing
    `<consumer>/process/upstream` as its detail. So the case can fail, it
    fails on the condition it claims to watch rather than on an absent
    fixture, and its failure detail names the wrong root out loud."""
    import shutil, tempfile

    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vendored-root-'))
    cases = []
    try:
        consumer = tmp / 'consumer'
        engine = consumer / 'process' / 'upstream'
        (engine / 'tools').mkdir(parents=True)
        (consumer / 'process' / 'manifest.json').write_text(json.dumps(
            {'upstream': {'vendored_at': 'process/upstream'}}), encoding='utf-8')
        # Both precedent.json files exist, which is the whole trap: the wrong
        # one parses fine and declares sources at paths nothing resolves.
        (consumer / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': []}), encoding='utf-8')
        (engine / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': []}), encoding='utf-8')

        got = psc.consuming_repo_root(engine)
        cases.append(('a vendored engine resolves to the CONSUMING repo root, '
                      'not to the vendored tree it sits in',
                      got == consumer.resolve(), str(got)))

        # --- 2: a repo that is not a vendoring consumer is untouched --------
        plain = tmp / 'plain'
        (plain / 'tools').mkdir(parents=True)
        got = psc.consuming_repo_root(plain / 'tools')
        cases.append(('a repo with no vendoring manifest keeps the old '
                      'default, so a practice set behaves exactly as before',
                      got == (plain / 'tools').resolve(), str(got)))

        # --- 3: a manifest that does NOT claim this tree is not believed ----
        other = tmp / 'other'
        other_engine = other / 'process' / 'upstream'
        (other_engine / 'tools').mkdir(parents=True)
        (other / 'process' / 'manifest.json').write_text(json.dumps(
            {'upstream': {'vendored_at': 'process/somewhere-else'}}),
            encoding='utf-8')
        got = psc.consuming_repo_root(other_engine)
        cases.append(('a manifest whose vendored_at points somewhere else is '
                      'not read as a claim on this tree',
                      got == other_engine.resolve(), str(got)))

        # --- 4: a malformed manifest fails soft rather than raising ---------
        bad = tmp / 'bad'
        bad_engine = bad / 'process' / 'upstream'
        (bad_engine / 'tools').mkdir(parents=True)
        (bad / 'process' / 'manifest.json').write_text('{not json',
                                                       encoding='utf-8')
        got = psc.consuming_repo_root(bad_engine)
        cases.append(('an unreadable manifest degrades to the old default '
                      'instead of taking the tool down',
                      got == bad_engine.resolve(), str(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a vendored engine copy reads the consuming repo\'s sources '
          f'({len(cases)} stated cases)',
          not bad_cases,
          '; '.join(f'{n} -- {d[:400]}' for n, d in bad_cases))


def check_source_clone_keeps_its_credential():
    """A synced source clone carries the credential helper in its OWN config,
    so git commands run inside it later can authenticate too.

    THE INCIDENT (practice: cite-the-incident), 2026-09-11.
    precedent_source_credentials.credential_args covers exactly one git
    invocation -- the clone. The clone it produces remembered nothing of it,
    so every later command inside it met a private remote with no credential
    and failed on `could not read Username for 'https://github.com'` with
    PRECEDENT_GIT_TOKEN sitting right there in the environment. Because
    PRECEDENT_FRESHNESS_ALSO names those clones, the freshness guard's
    pre-write mode fetched each one, failed, and blocked -- and blocked again
    on every retry, since its once-per-session sentinel is only written after
    the checks pass. A session could run nothing but `git` for its first six
    tool calls, and the block named the SOURCE's branch while the project dir
    sat on another, so it read as the project's own checkout being broken.

    Case 4 is the one that would have caught it: not "a helper is configured"
    but "git, run plainly inside the clone with no -c flags, actually answers
    with the credential". `git credential fill` is that question asked
    directly, and it needs no network.

    TWO NEGATIVE CONTROLS, RUN 2026-09-11 rather than assumed, because the
    two halves fail independently (practice: control-asserts-which-failure).
    Neutering persist_credential_helper so it writes nothing turned cases
    2, 3 and 4 red -- and case 4 failed printing
    `fatal: could not read Username for 'https://github.com'`, which is the
    incident's own message, from git, unprompted. Separately, deleting
    _persist_credential's call from ensure_source turned only case 5's two
    red, with everything else green: the helper still worked, nothing
    called it.

    Hermetic: a file:// origin for the clone, an https remote written into
    it afterwards to exercise the https-only rule, a fixture token, and a
    fixture HOME. No network."""
    import shutil, tempfile

    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    import precedent_source_bootstrap as psb

    TOKEN = 'fixture-token-never-a-real-one'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-clone-cred-'))
    cases = []
    try:
        source = tmp / 'source-repo'
        source.mkdir()
        for cmd in (['init', '-q', '-b', 'main'],
                    ['config', 'user.email', 'harness@example.com'],
                    ['config', 'user.name', 'harness']):
            subprocess.run(['git', '-C', str(source), *cmd], check=True,
                           capture_output=True, text=True)
        (source / 'practices').mkdir()
        (source / 'practices' / 'p.md').write_text('fixture\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(source), 'add', '-A'], check=True,
                       capture_output=True, text=True)
        subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'seed'],
                       check=True, capture_output=True, text=True)

        env = {psc.TOKEN_ENV: TOKEN}
        https = 'https://github.com/example/precedent-individual'

        # --- 1: nothing to persist is not a failure, and writes nothing -----
        quiet = tmp / 'quiet'
        subprocess.run(['git', 'clone', '-q', f'file://{source}', str(quiet)],
                       check=True, capture_output=True, text=True)
        wrote = psc.persist_credential_helper(quiet, f'file://{source}', env=env)
        got = subprocess.run(['git', '-C', str(quiet), 'config', '--get-all',
                              'credential.helper'], capture_output=True, text=True)
        cases.append(('a non-https remote is never given the credential, and '
                      'nothing is written into its config',
                      wrote is False and got.stdout.strip() == '',
                      f'wrote={wrote} config={got.stdout!r}'))
        cases.append(('no token means nothing is written either',
                      psc.persist_credential_helper(quiet, https, env={}) is False,
                      'persist returned truthy with an empty environment'))

        # --- 2..4: an https remote gets a usable, secret-free helper --------
        clone = tmp / 'clone'
        subprocess.run(['git', 'clone', '-q', f'file://{source}', str(clone)],
                       check=True, capture_output=True, text=True)
        subprocess.run(['git', '-C', str(clone), 'remote', 'set-url', 'origin',
                        https], check=True, capture_output=True, text=True)
        wrote = psc.persist_credential_helper(clone, https, env=env)
        cfg = (clone / '.git' / 'config').read_text(encoding='utf-8')
        cases.append(('an https remote gets the helper written into the '
                      "clone's own config", wrote is True
                      and psc.TOKEN_ENV in cfg, f'wrote={wrote} {failure_detail(cfg, 400)}'))
        cases.append(('...and the token itself is NOT in that config -- only '
                      'the NAME of the variable git should read',
                      TOKEN not in cfg, failure_detail(cfg, 400)))

        # --- 3: idempotent. A session-start hook runs this every session ----
        for _ in range(3):
            psc.persist_credential_helper(clone, https, env=env)
        entries = subprocess.run(['git', '-C', str(clone), 'config', '--get-all',
                                  'credential.helper'], capture_output=True,
                                 text=True).stdout.splitlines()
        cases.append(('re-running does not accumulate helper entries: the '
                      'empty reset plus one helper, however many times it runs',
                      len(entries) == 2 and entries[0] == ''
                      and entries[1].startswith('!f()'),
                      f'{len(entries)} entrie(s): {entries!r}'))

        # --- 4: git, run PLAINLY inside the clone, answers with the token ---
        # The property the incident was about. No -c flags, no credential
        # args -- just git, in that directory, the way a hook or a person
        # runs it. `credential fill` asks git the same question a fetch asks
        # and needs no network.
        filled = subprocess.run(
            ['git', '-C', str(clone), 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n\n',
            capture_output=True, text=True,
            env={**os.environ, psc.TOKEN_ENV: TOKEN,
                 'GIT_TERMINAL_PROMPT': '0'})
        cases.append(('git run plainly inside the clone -- no -c flags -- '
                      'answers with the credential from the environment',
                      f'password={TOKEN}' in filled.stdout
                      and f'username={psc.DEFAULT_TOKEN_USER}' in filled.stdout,
                      f'rc={filled.returncode} {filled.stdout[:200]} '
                      f'{filled.stderr[:200]}'))

        # --- 5: the bootstrap actually calls it, on EVERY successful sync ---
        # The wiring, which is the half a unit test of the helper cannot
        # reach. It is asserted by recording the call rather than by reading
        # the resulting config, because ensure_source can only be exercised
        # hermetically against a file:// origin -- and a file:// origin is
        # exactly the case that correctly gets no credential (case 1). So the
        # https behaviour is cases 2-4's to prove, and this is only "the
        # bootstrap asks".
        #
        # Both halves matter. A FRESH clone needs it or the clone is unusable
        # tomorrow; an EXISTING one needs it or every clone made before this
        # landed stays broken forever, which is most of the ones on disk.
        calls = []
        original = psb._persist_credential
        psb._persist_credential = lambda c, u: calls.append((str(c), u))
        try:
            fresh = tmp / 'fresh'
            ok_fresh, _ = psb.ensure_source(
                'individual', 'precedent-individual', f'file://{source}',
                fresh, tmp / 'cfg.json', branch='main')
            existing = tmp / 'existing'
            subprocess.run(['git', 'clone', '-q', f'file://{source}',
                            str(existing)], check=True, capture_output=True,
                           text=True)
            ok_existing, _ = psb.ensure_source(
                'individual', 'precedent-individual', f'file://{source}',
                existing, tmp / 'cfg.json', branch='main')
        finally:
            psb._persist_credential = original
        cases.append(('a FRESH clone is offered the helper',
                      ok_fresh and (str(fresh), f'file://{source}') in calls,
                      f'ok={ok_fresh} calls={calls!r}'))
        cases.append(('and so is an EXISTING one, on every later sync -- '
                      'which is the repair path for every clone made before '
                      'this landed',
                      ok_existing and (str(existing), f'file://{source}') in calls,
                      f'ok={ok_existing} calls={calls!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a synced source clone keeps the credential helper in its own '
          f'config, with no secret in it ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_source_credentials_reach_clones_nothing_syncs():
    """The two paths a source clone actually takes at session start, neither
    of which run_sync's persist could reach.

    THE INCIDENT (practice: cite-the-incident), 2026-09-11, HOURS AFTER the
    persist above landed and with every one of its five cases green. Four
    private sources sat on disk, PRECEDENT_GIT_TOKEN was set, and not one
    clone carried a helper: the freshness guard fetched each, failed, and
    refused every non-git tool call of the session -- the identical failure
    the persist was written to end.

    The persist was real; the paths were wrong. run_sync called it, and:

      * sources_from_repo's ALREADY-ON-DISK branch calls _try_sync directly and
        never enters run_sync -- so every team clone after its first session
        was synced and left credential-less.
      * the individual source is not synced at session start while it looks
        usable at all: session-start.sh leaves it to precedent_resolve.py's
        self-heal, which a healthy clone never triggers. Nothing syncs it, so
        no sync-time repair can reach it.

    Case 5 of the check above covers ensure_source, passed throughout, and
    was blind to both -- which is why this is a separate check and not
    another case there (practice: control-asserts-which-failure: a control
    proves the guard fires, and that one fires on a path production does not
    take).

    NEGATIVE CONTROLS, run rather than assumed. Reverting the persist in
    _try_sync back into run_sync alone turns case 1 red and leaves 2-4 green;
    deleting ensure_source_credentials' write turns 2 red and leaves 1 green.
    The two halves fail independently, so both are stated.

    Hermetic: file:// origins, an https remote written in afterwards, a
    fixture token. No network."""
    import shutil, tempfile

    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    import precedent_source_bootstrap as psb
    import precedent_refresh_sources as prs

    TOKEN = 'fixture-token-never-a-real-one'
    https = 'https://github.com/example/precedent-team-fixture'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-cred-paths-'))
    cases = []
    try:
        source = tmp / 'source-repo'
        source.mkdir()
        for cmd in (['init', '-q', '-b', 'main'],
                    ['config', 'user.email', 'harness@example.com'],
                    ['config', 'user.name', 'harness']):
            subprocess.run(['git', '-C', str(source), *cmd], check=True,
                           capture_output=True, text=True)
        (source / 'practices').mkdir()
        (source / 'practices' / 'p.md').write_text('fixture\n', encoding='utf-8')
        (source / 'precedent.json').write_text('{"base_branch": "main"}\n',
                                               encoding='utf-8')
        subprocess.run(['git', '-C', str(source), 'add', '-A'], check=True,
                       capture_output=True, text=True)
        subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'seed'],
                       check=True, capture_output=True, text=True)

        # --- 1: a team clone ALREADY ON DISK is offered the helper ----------
        # The regression itself. Recorded rather than read out of the config,
        # for case 5's reason above: a file:// origin correctly gets none.
        consumer = tmp / 'consumer'
        (consumer / 'sibling-team').mkdir(parents=True)
        (consumer / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'team', 'name': 'precedent-team-fixture',
             'path': 'sibling-team'}]}), encoding='utf-8')
        subprocess.run(['git', 'clone', '-q', f'file://{source}',
                        str(consumer / 'sibling-team')], check=True,
                       capture_output=True, text=True)
        calls = []
        original = psb._persist_credential
        psb._persist_credential = lambda c, u: calls.append((str(c), u))
        try:
            results = psb.sources_from_repo(consumer)
        finally:
            psb._persist_credential = original
        on_disk = str((consumer / 'sibling-team').resolve())
        cases.append(('a team clone that is ALREADY ON DISK is offered the '
                      'helper on its session-start sync -- the path that '
                      'bypasses run_sync entirely',
                      any(c[0] == on_disk for c in calls),
                      f'results={results!r} calls={calls!r}'))

        # --- 2: a clone NOTHING syncs is repaired by the session-start walk -
        attached = tmp / 'attached'
        subprocess.run(['git', 'clone', '-q', f'file://{source}',
                        str(attached)], check=True, capture_output=True,
                       text=True)
        subprocess.run(['git', '-C', str(attached), 'remote', 'set-url',
                        'origin', https], check=True, capture_output=True,
                       text=True)
        saved = os.environ.get(psc.TOKEN_ENV)
        os.environ[psc.TOKEN_ENV] = TOKEN
        try:
            repaired = prs.ensure_source_credentials([{'repo': attached}])
            cfg = (attached / '.git' / 'config').read_text(encoding='utf-8')
            cases.append(('an attached source clone with NO helper is '
                          'repaired, and the token itself is not written',
                          repaired and psc.TOKEN_ENV in cfg and TOKEN not in cfg,
                          f'repaired={repaired!r} {failure_detail(cfg, 400)}'))

            # --- 3: an existing helper is somebody's own, and is left alone -
            again = prs.ensure_source_credentials([{'repo': attached}])
            cases.append(('a clone that already has a helper is left alone, '
                          'so this is idempotent and does not overwrite a '
                          "person's own credential manager",
                          again == [], f'second pass repaired {again!r}'))
        finally:
            if saved is None:
                os.environ.pop(psc.TOKEN_ENV, None)
            else:
                os.environ[psc.TOKEN_ENV] = saved

        # --- 4: no token, nothing written anywhere -------------------------
        bare = tmp / 'bare'
        subprocess.run(['git', 'clone', '-q', f'file://{source}', str(bare)],
                       check=True, capture_output=True, text=True)
        subprocess.run(['git', '-C', str(bare), 'remote', 'set-url', 'origin',
                        https], check=True, capture_output=True, text=True)
        os.environ.pop(psc.TOKEN_ENV, None)
        none_written = prs.ensure_source_credentials([{'repo': bare}])
        got = subprocess.run(['git', '-C', str(bare), 'config', '--get-all',
                              'credential.helper'], capture_output=True,
                             text=True).stdout.strip()
        cases.append(('with no token there is nothing to write, and nothing '
                      'is written', none_written == [] and got == '',
                      f'repaired={none_written!r} config={got!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the credential helper reaches the source clones no run_sync ever '
          f'touches ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_attached_sets_sources_are_synced():
    """Session start syncs what every ATTACHED practice set reads, not only
    the root's own sources (2026-10-02). Measured that day: the individual set
    at $HOME read its universal rules from a clone of its own,
    $HOME/BestPractice, made at one session start and never pulled again --
    131 commits behind, and the set's session file and the reply gate's
    session-load figure were built from it.

    Two-parent fixture: a project under one parent, the individual set under
    a fake $HOME, the set declaring universal at ../BestPractice. Cases, each
    asserting the tool's own words or the clone's own state:
      1. the set's universal clone is fast-forwarded by the walk;
      2. it stays on the branch its manifest pins (main), not the universal
         repo's own declared base_branch (staging) -- the existing-clone
         path used to pass no branch and moved it;
      3. the set's session file is re-rendered because a source it reads
         moved, though it was minutes old;
      4. with nothing moved, a second run leaves that render alone;
      5. a checkout the tool did not clone is left as it is, and says so;
      6. a checkout named as the session's project is skipped, and says so."""
    import shutil, tempfile
    import precedent_source_bootstrap as psb
    import precedent_resolve as pr

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    def commit(repo, name, text):
        (repo / name).write_text(text, encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit',
            '-qm', name)

    stub = ('#!/usr/bin/env python3\n'
            'import pathlib, sys\n'
            'repo = sys.argv[sys.argv.index("--repo") + 1]\n'
            'out = pathlib.Path(repo) / ".precedent"\n'
            'out.mkdir(parents=True, exist_ok=True)\n'
            '(out / "SESSION_PRACTICES.md").write_text("rendered", encoding="utf-8")\n')

    saved = {k: os.environ.get(k) for k in (
        'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG', 'CLAUDE_PROJECT_DIR', 'PRECEDENT_PROJECT_DIR',
        pr.SELF_HEAL_RENDER_ENV)}
    for k in saved:                       # practice: fixture-owns-its-state
        os.environ.pop(k, None)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='attached-sets-sync-'))
    cases = []
    try:
        # The universal origin: main and staging, base_branch staging.
        up = tmp / 'origin-bp'
        up.mkdir()
        git(up, 'init', '-q', '-b', 'main')
        (up / 'practices').mkdir()
        (up / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'staging', 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        commit(up, 'practices/rule.md', 'v1\n')
        git(up, 'branch', 'staging')
        url = f'file://{up}'

        home = tmp / 'home'
        proj_parent = tmp / 'work'
        home.mkdir()
        proj_parent.mkdir()
        project = proj_parent / 'project'
        project.mkdir()
        git(project, 'init', '-q', '-b', 'main')
        (project / 'precedent.json').write_text(json.dumps({'sources': []}),
                                                encoding='utf-8')

        indiv = home / 'precedent-individual'
        (indiv / 'tools').mkdir(parents=True)
        git(indiv, 'init', '-q', '-b', 'main')
        (indiv / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent',
             'path': '../BestPractice'}]}), encoding='utf-8')
        (indiv / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'source_branch': 'main'}), encoding='utf-8')
        tool = indiv / 'tools' / 'precedent_session_practices.py'
        tool.write_text(stub, encoding='utf-8')
        tool.chmod(0o755)
        cfg = tmp / 'config.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(indiv)}}),
            encoding='utf-8')
        os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)

        # The set's universal clone, made by the tool, then left behind.
        clone = home / 'BestPractice'
        ok, out = psb._try_sync(url, clone, branch='main')
        commit(up, 'practices/rule.md', 'v2, the newer rule\n')
        render = indiv / '.precedent' / 'SESSION_PRACTICES.md'
        render.parent.mkdir()
        render.write_text('old render', encoding='utf-8')
        past = time.time() - 120          # minutes old: fresh by age alone
        os.utime(render, (past, past))

        res = psb.sources_from_attached_sets(project)
        head = git(clone, 'rev-parse', 'HEAD').stdout.strip()
        tip = git(up, 'rev-parse', 'main').stdout.strip()
        branch = git(clone, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        cases.append(('the attached set\'s universal clone is fast-forwarded',
                      ok and head == tip, f'head={head[:8]} tip={tip[:8]} {res!r}'))
        cases.append(('and stays on its pinned main, not the universal '
                      'repo\'s own base_branch (staging)',
                      branch == 'main', f'branch={branch!r}'))
        cases.append(('the set\'s render is rebuilt because a source it reads '
                      'moved, though it was minutes old',
                      render.read_text(encoding='utf-8') == 'rendered',
                      render.read_text(encoding='utf-8')))

        render.write_text('kept', encoding='utf-8')
        os.utime(render, None)
        psb.sources_from_attached_sets(project)
        cases.append(('with nothing moved, a second run leaves the render '
                      'alone',
                      render.read_text(encoding='utf-8') == 'kept',
                      render.read_text(encoding='utf-8')))

        os.remove(clone / '.git' / psb.CLONE_MARKER)
        commit(up, 'practices/rule.md', 'v3\n')
        res = psb.sources_from_attached_sets(project)
        msgs = ' | '.join(m for _s, _n, _o, m in res)
        cases.append(('a checkout the tool did not clone is left as it is, and '
                      'says so',
                      git(clone, 'rev-parse', 'HEAD').stdout.strip() == tip
                      and 'not cloned by this tool' in msgs, msgs))

        psb._mark_clone(clone)
        os.environ['CLAUDE_PROJECT_DIR'] = str(clone)
        res = psb.sources_from_attached_sets(project)
        msgs = ' | '.join(m for _s, _n, _o, m in res)
        cases.append(('a checkout named as the session\'s project is skipped, '
                      'and says so',
                      git(clone, 'rev-parse', 'HEAD').stdout.strip() == tip
                      and 'a session is working in this checkout' in msgs, msgs))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'session start syncs the sources every attached practice set reads, '
          f'pinned, skipping working copies, and re-renders a set whose '
          f'sources moved ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_attached_sets_sync_is_safe_for_everyone():
    """The adversarial half of check_attached_sets_sources_are_synced: the
    walk runs at EVERY session start, for people with no practice set of
    their own and for people whose BestPractice copy is their own work
    (2026-10-02, run before the change was landed). Cases, each through the
    real CLI where it is about what a person sees:
      1. a person's own ../BestPractice working copy -- feature branch,
         unpushed commit, half-done edit -- is untouched, and nothing is said;
      2. a set's universal clone that is missing is not cloned at session
         start;
      3. a set with a broken precedent.json adds no message and no traceback;
      4. a tool-made clone that cannot fast-forward (its own commit, origin
         moved on) keeps that commit and is reported in ONE line naming the
         set;
      5. a set with no engine manifest still keeps its universal clone on
         main, never the universal repo's own base_branch;
      6. a source ref stamped in the future does not make the render stale
         on every call."""
    import contextlib, io, shutil, tempfile
    import precedent_source_bootstrap as psb
    import precedent_resolve as pr

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    def commit(repo, name, text):
        f = repo / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit',
            '-qm', name)

    def head(r):
        return git(r, 'rev-parse', 'HEAD').stdout.strip()

    def cli(project):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(err):
            rc = psb.main(['--sources-from', str(project), '--remote-only',
                           'false'])
        return rc, err.getvalue().strip()

    saved = {k: os.environ.get(k) for k in (
        'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG', 'CLAUDE_PROJECT_DIR', 'PRECEDENT_PROJECT_DIR',
        pr.SELF_HEAL_RENDER_ENV, 'PRECEDENT_SOURCE_BASE_URL')}
    for k in saved:                       # practice: fixture-owns-its-state
        os.environ.pop(k, None)
    os.environ['PRECEDENT_SOURCE_BASE_URL'] = 'file:///nonexistent-base'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='attached-sets-safe-'))
    cases = []
    try:
        up = tmp / 'origin-bp'
        up.mkdir()
        git(up, 'init', '-q', '-b', 'main')
        (up / 'practices').mkdir()
        (up / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'staging'}), encoding='utf-8')
        commit(up, 'practices/rule.md', 'v1\n')
        git(up, 'branch', 'staging')
        url = f'file://{up}'

        def layout(tag, manifest=True, raw=None):
            base = tmp / tag
            home, work = base / 'home', base / 'work'
            project = work / 'project'
            project.mkdir(parents=True)
            home.mkdir()
            git(project, 'init', '-q', '-b', 'main')
            (project / 'precedent.json').write_text('{"sources": []}',
                                                    encoding='utf-8')
            ind = home / 'precedent-individual'
            (ind / 'tools').mkdir(parents=True)
            git(ind, 'init', '-q', '-b', 'main')
            (ind / 'precedent.json').write_text(raw if raw is not None else
                json.dumps({'sources': [{'level': 'universal',
                                         'name': 'precedent',
                                         'path': '../BestPractice'}]}),
                encoding='utf-8')
            if manifest:
                # source_repo is what a fresh universal clone is made from, so
                # case 2 can tell "did not clone" from "had no URL to clone".
                (ind / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    json.dumps({'source_branch': 'main', 'source_repo': url}),
                    encoding='utf-8')
            cfg = base / 'config.json'
            cfg.write_text(json.dumps({'individual': {
                'name': 'precedent-individual', 'path': str(ind)}}),
                encoding='utf-8')
            os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
            return project, ind, home / 'BestPractice'

        # 1. the person's own working copy
        project, ind, bp = layout('own-copy')
        git(tmp, 'clone', '-q', str(up), str(bp))
        git(bp, 'checkout', '-q', '-b', 'my-feature')
        commit(bp, 'practices/mine.md', 'my work\n')
        (bp / 'practices' / 'rule.md').write_text('half-done\n', encoding='utf-8')
        commit(up, 'practices/rule.md', 'v2\n')
        before = (head(bp), git(bp, 'status', '--porcelain').stdout)
        rc, out = cli(project)
        after = (head(bp), git(bp, 'status', '--porcelain').stdout)
        cases.append(('a person\'s own BestPractice working copy is untouched '
                      'and nothing is said', rc == 0 and before == after
                      and 'precedent_source_bootstrap' not in out, out))

        # 2. a missing universal clone is not cloned
        project, ind, bp = layout('missing')
        rc, out = cli(project)
        cases.append(('a set\'s missing universal clone is not cloned at '
                      'session start', rc == 0 and not bp.exists(), out))

        # 3. a broken set adds nothing
        project, ind, bp = layout('broken', raw='{ not json')
        rc, out = cli(project)
        cases.append(('a set with a broken precedent.json adds no message and '
                      'no traceback', rc == 0 and 'Traceback' not in out
                      and 'precedent_source_bootstrap' not in out, out))

        # 4. a diverged tool-made clone: kept, and said once
        project, ind, bp = layout('diverged')
        psb._try_sync(url, bp, branch='main')
        commit(bp, 'practices/local.md', 'local\n')
        local = head(bp)
        commit(up, 'practices/rule.md', 'v3\n')
        rc, out = cli(project)
        lines = [l for l in out.splitlines() if 'precedent_source_bootstrap' in l]
        cases.append(('a clone that cannot fast-forward keeps its commit and is '
                      'reported in one line naming the set',
                      rc == 0 and head(bp) == local and len(lines) == 1
                      and 'was not brought up to date' in lines[0]
                      and str(ind) in lines[0], out))

        # 5. no manifest: still main
        project, ind, bp = layout('no-manifest', manifest=False)
        psb._try_sync(url, bp, branch='main')
        commit(up, 'practices/rule.md', 'v4\n')
        rc, out = cli(project)
        br = git(bp, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        cases.append(('a set with no engine manifest keeps its universal clone '
                      'on main', br == 'main' and head(bp) == head(up),
                      f'branch={br!r} {out}'))

        # 6. a future-stamped ref does not re-render forever (its own layout,
        # so it does not lean on case 5's branch)
        project, ind, bp = layout('future')
        psb._try_sync(url, bp, branch='main')
        tool = ind / 'tools' / 'precedent_session_practices.py'
        tool.write_text('raise SystemExit("rendered when it should not")\n',
                        encoding='utf-8')
        render = ind / '.precedent' / 'SESSION_PRACTICES.md'
        render.parent.mkdir(exist_ok=True)
        render.write_text('kept', encoding='utf-8')
        ref = bp / '.git' / 'refs' / 'heads' / 'main'
        fut = time.time() + 30 * 86400
        os.utime(ref, (fut, fut))
        res = pr._self_heal_stale_render(ind)
        cases.append(('a source ref stamped in the future does not make the '
                      'render stale', res == 'fresh', f'result={res!r}'))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the attached-set sync is safe for people with no set, a hand-made '
          f'BestPractice copy, a broken set or a stuck clone '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:400]}" for n, d in bad))

def check_self_heal_universal_source_leaves_no_bytecode():
    """precedent_resolve.py's _self_heal_universal_source() runs
    tools/precedent_source_bootstrap.py AS A SUBPROCESS, inside the very
    repo it is healing -- the same shape as the build_views.py subprocess
    precedent_bootstrap_source.py already runs with -B, and for the same
    reason: precedent_source_bootstrap.py's own _credential_args() imports
    precedent_source_credentials from ITS OWN DIRECTORY, and an ordinary
    (non -B) interpreter caches that import as a .pyc right there.

    THE BUG THIS LOCKS IN. Found chasing an intermittent very_deep_check.py
    false positive (tools/__pycache__/precedent_source_credentials.cpython-
    311.pyc reading as bootstrap drift, sometimes as a byte mismatch and
    sometimes as "this set does not have it") -- traced with strace -f to
    exactly this subprocess, launched without -B. The drift check has its
    own exclusion for a stray .pyc now (see check_very_deep_check_bootstrap_
    drift's stray-pycache case), which stops the false positive from being
    reported as drift; this check is the other half, on the file that
    actually writes it, so the same litter cannot reappear under some other
    caller that isn't behind a drift check at all -- a real set's tools/
    directory, session after session, whenever the universal source has not
    been cloned next to it yet.

    THE FIXTURE IS MINIMAL RATHER THAN A REAL BOOTSTRAPPED SET (contrast
    check_very_deep_check_bootstrap_drift's fresh()): only the two files
    _self_heal_universal_source's subprocess actually reads are copied in
    (precedent_source_bootstrap.py itself, and precedent_source_credentials.py
    so the import it triggers is the real one, not an ImportError that would
    make this pass for the wrong reason), plus the two small JSON files that
    tell it what to clone. No network call is required to exercise the bug:
    precedent_source_bootstrap.py's _sync_once() calls _credential_args()
    -- the import that writes the .pyc -- as its first line, before it runs
    any git command, so the clone attempt below is expected to fail offline
    and that failure is not what this check is about."""
    import shutil, tempfile
    import precedent_resolve as _pr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-self-heal-'))
    try:
        repo_root = tmp / 'set'
        tools_dir = repo_root / 'tools'
        tools_dir.mkdir(parents=True)
        shutil.copy2(ROOT / 'tools' / 'precedent_source_bootstrap.py',
                     tools_dir / 'precedent_source_bootstrap.py')
        shutil.copy2(ROOT / 'tools' / 'precedent_source_credentials.py',
                     tools_dir / 'precedent_source_credentials.py')
        (repo_root / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                        'path': '../universal-sibling-not-yet-cloned'}],
        }), encoding='utf-8')
        # A source_repo that fails at once, locally: the .pyc is written by
        # _credential_args()'s import before any git command, so the real
        # remote (most of this check's time, and an outbound call) adds
        # nothing to what it asserts.
        (tools_dir / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'source_repo': (tmp / 'no-such-remote.git').as_uri(),
            'source_branch': 'precedent-beta-v01',
        }), encoding='utf-8')

        _pr._self_heal_universal_source(repo_root)

        stray = tools_dir / '__pycache__'
        check('_self_heal_universal_source runs precedent_source_bootstrap.py '
              'with -B, so it leaves no __pycache__ in the repo it just healed',
              not stray.exists(),
              f'{stray} exists, containing: '
              f'{sorted(p.name for p in stray.iterdir())}' if stray.exists()
              else '(not reproduced this run)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_bootstrapping_a_set_reaches_no_network_unless_asked():
    """precedent_bootstrap_source.py reaches nothing outside the machine
    unless --network true asks: no fetch for its staleness warning, and the
    resolver's self-heals -- the individual set's hook and the universal
    clone -- are off for everything it runs, then put back.

    2026-10-17, very deep check: bootstrapping a SHARED set with a scratch
    HOME and the token variables unset asked GitHub whose the session's
    token was, cloned the operator's private individual set into the
    scratch home and wrote a user config naming it -- the new set's view
    build ran the resolver, whose self-heal ran the set's individual hook --
    against a docstring saying the tool touches no remote. Reproduced the
    same day; with this change the scratch home stays empty and git's trace
    shows no remote at all. Decision (the session's, under Morgan's
    delegation of 2026-10-17): no network unless a flag asks for it.
    Planted: a hosted-session environment and a repo whose individual hook
    and universal bootstrap tool each leave a marker when run."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_resolve as pr
        import precedent_bootstrap_source as pbs
    finally:
        sys.path.pop(0)
    name = 'bootstrapping a set reaches no network unless asked'
    key = getattr(pr, 'NO_SELF_HEAL_ENV', None)
    if key is None:
        check(name, False, 'precedent_resolve has no NO_SELF_HEAL_ENV: nothing can keep '
              'the self-heals from cloning while a set is bootstrapped')
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-no-network-'))
    saved = {k: os.environ.get(k) for k in (key, 'CLAUDE_CODE_REMOTE', 'HOME',
                                            pr.USER_CONFIG_ENV)}
    cases = []
    try:
        repo = tmp / 'set'
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / 'tools').mkdir()
        hook_marker, tool_marker = tmp / 'hook-ran', tmp / 'tool-ran'
        (repo / pr.INDIVIDUAL_BOOTSTRAP_HOOK).write_text(
            f'#!/bin/bash\ntouch {hook_marker}\n', encoding='utf-8')
        (repo / 'tools' / 'precedent_source_bootstrap.py').write_text(
            f'import pathlib\npathlib.Path({str(tool_marker)!r}).touch()\n',
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin',
                        'https://example.invalid/set.git'], capture_output=True)
        os.environ['HOME'] = str(tmp / 'home')
        os.environ['CLAUDE_CODE_REMOTE'] = 'true'
        os.environ.pop(pr.USER_CONFIG_ENV, None)
        os.environ[key] = '1'
        a = pr._self_heal_individual_source(repo)
        b = pr._self_heal_universal_source(repo)
        cases.append(('with the switch set, neither self-heal runs anything',
                      a == b == 'not-asked' and not hook_marker.exists()
                      and not tool_marker.exists(), f'{a} {b}'))
        os.environ.pop(key)
        pr._self_heal_individual_source(repo)
        pr._self_heal_universal_source(repo)
        cases.append(('...and without it both still do, in a hosted session (control)',
                      hook_marker.exists() and tool_marker.exists(), ''))
        calls = []
        saved_git = pbs._git
        pbs._git = lambda *args: (calls.append(args), (True, '0'))[1]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                pbs._warn_if_clone_is_stale()
            no_fetch = not any(c and c[0] == 'fetch' for c in calls)
            calls.clear()
            with contextlib.redirect_stderr(io.StringIO()):
                pbs._warn_if_clone_is_stale(True)
            fetched = any(c and c[0] == 'fetch' for c in calls)
        finally:
            pbs._git = saved_git
        cases.append(('the staleness warning fetches only with --network true',
                      no_fetch and fetched, ''))
        seen = {}
        saved_inner = pbs._bootstrap
        pbs._bootstrap = lambda *a, **k: seen.setdefault('env', os.environ.get(key))
        try:
            pbs.bootstrap('shared', 'x', tmp / 'x')
            inside = seen.pop('env', None)
            after = os.environ.get(key)
            pbs.bootstrap('shared', 'x', tmp / 'x', network=True)
            asked = seen.pop('env', None)
        finally:
            pbs._bootstrap = saved_inner
        cases.append(('bootstrap() switches the self-heals off for its run, and back',
                      inside == '1' and after is None and asked is None,
                      f'{inside} {after} {asked}'))
        cases.append(('the docstring says so', 'NO NETWORK UNLESS ASKED' in (pbs.__doc__ or ''),
                      ''))
    except OSError as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_move_fixes_mentions_of_the_moved_practice():
    """After a move withdraws the source copy, tools/precedent_move.py fixes
    what still says the practice lives there -- in both sets and in every
    other repository in force -- and leaves history as written.

    WHY. Morgan, 2026-09-28 (strength: decided), on a finding that moves
    repaired broken links but nothing searched for other mentions: "I don't
    need a detailed report but for those problems to be solved." Measured
    the same day: the individual set's own README and a sibling practice
    still linked the stub of a practice that had left the set.

    Every planted mention is asserted by its resulting text, and so is every
    planted non-mention -- a dated line, a Story, an unrelated line naming
    the old set -- because a fixer that rewrote everything would pass the
    first half alone."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-mentions-'))
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
    env.pop('CLAUDE_CODE_REMOTE', None)

    def run(args, extra_env=None):
        return subprocess.run([sys.executable, *args], cwd=str(ROOT),
                              capture_output=True, text=True,
                              env=dict(env, **(extra_env or {})))

    def practice(slug, rule, story):
        return ('---\nslug:        ' + slug + '\n'
                'title:       A fixture practice\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["fixture/**"]\noccasion:    "fixture"\n'
                'gates:       []\nindex_clause: "fixture"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nin_force_at: null\n'
                'supersedes:  []\noverrides:   null\nadded:       "2026-09-14"\n'
                'approved_by: "Fixture, 2026-09-14"\n---\n\n## Rule\n' + rule
                + '\n\n## Why\nBecause.\n\n## Story\n' + story + '\n')

    results = []
    try:
        team, indiv, other = (tmp / 'precedent-team-fixture',
                              tmp / 'precedent-individual', tmp / 'other')
        # The pair every move check starts from, bootstrapped once and copied
        # (_move_fixture_sets).
        _move_fixture_sets(tmp)
        (other / 'docs').mkdir(parents=True)
        (indiv / 'practices' / 'zz-moves.md').write_text(
            practice('zz-moves', 'Do the thing.', 'A dated incident.'))
        (indiv / 'practices' / 'zz-cites.md').write_text(practice(
            'zz-cites', 'Follow [zz-moves](zz-moves.md#rule) first.',
            'Once [zz-moves](zz-moves.md) lived here.'))
        (indiv / 'NOTES.md').write_text(
            'Present: `zz-moves` is a precedent-individual rule.\n\n'
            'History: on 2026-09-01 `zz-moves` sat in precedent-individual.\n')
        (team / 'NOTES.md').write_text(
            'See [zz-moves](../precedent-individual/practices/zz-moves.md).\n')
        (other / 'docs' / 'x.md').write_text(
            'URL https://github.com/example/precedent-individual/blob/main/practices/'
            'zz-moves.md here\n'
            'path ../precedent-individual/practices/zz-moves.md here\n'
            'unrelated precedent-individual line\n\n'
            '`precedent-individual` has this check vendored -- `zz-moves`\n\n'
            'This set shows the shape in '
            '[zz-moves](../../precedent-individual/practices/zz-moves.md).\n')
        for repo in (indiv, team, other):
            subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
            subprocess.run(['git', '-C', str(repo), 'add', '-A'],
                           capture_output=True)
        r = run([str(ROOT / 'tools' / 'precedent_move.py'), '--slug', 'zz-moves',
                 '--from', 'individual', '--from-path', str(indiv),
                 '--to', 'team', '--to-path', str(team),
                 '--approved-by', 'Fixture Approver'],
                {'PRECEDENT_MOVE_MENTION_REPOS': str(other)})
        cites = (indiv / 'practices' / 'zz-cites.md').read_text()
        inotes = (indiv / 'NOTES.md').read_text()
        tnotes = (team / 'NOTES.md').read_text()
        x = (other / 'docs' / 'x.md').read_text()
        results = [
            ('the move completes', r.returncode == 0),
            ('a sibling link to the stub becomes the backticked slug, never a '
             'URL into the other set', 'Follow `zz-moves` first.' in cites),
            ('a present-tense line naming the old set names the new one',
             '`zz-moves` is a precedent-team-fixture rule' in inotes),
            ('a link in the destination set is re-pointed at its own copy',
             '[zz-moves](practices/zz-moves.md)' in tnotes),
            ('a URL to the old copy in another repo becomes the slug',
             'URL `zz-moves` here' in x),
            ('a path to the old copy names the new set',
             'path ../precedent-team-fixture/practices/zz-moves.md here' in x),
            ('a dated line is history and stays as written',
             'on 2026-09-01 `zz-moves` sat in precedent-individual.' in inotes),
            ('the Story stays as written',
             'Once [zz-moves](zz-moves.md) lived here.' in cites),
            ('a line about the old set that does not name the practice stays',
             'unrelated precedent-individual line' in x),
            ('a line naming the old set for another reason keeps it '
             '(where it lives is the only claim rewritten)',
             '`precedent-individual` has this check vendored -- `zz-moves`' in x),
            ('a fixed link inside a sentence saying the practice is HERE is '
             'named for a person to reword',
             'reword by hand: other/docs/x.md:' in r.stdout),
            ('each repository changed is named for committing',
             'mentions fixed in:' in r.stdout and str(other) in r.stdout),
        ]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in results if not ok]
    check(f'a practice move fixes what still says it lives where it was, and '
          f'leaves history alone ({len(results)} stated cases)',
          bool(results) and not failed, '; '.join(failed))


def check_move_tool_lands_then_deduplicates():
    """tools/precedent_move.py does spec/MOVING_PRACTICES.md's two steps in
    the one safe order, records the move at both ends, and refuses the
    states the procedure says never to produce.

    WHY (practice: cite-the-incident). The procedure told a mover to feed an
    existing practice's four sections through precedent_candidate.py, which
    takes one --proposed-rule string; every move was a hand copy and the
    deduplication was done from memory. Morgan, 2026-09-14: "I've had bumps
    doing that." The fixture owns its environment (practice:
    fixture-owns-its-state): no individual source, no hosted-session
    self-heal, the commit backstop waved."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-'))
    cases = []
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'),
               # The mention fix reads only the fixture sets, never the real
               # repositories this clone resolves.
               PRECEDENT_MOVE_MENTION_REPOS='')
    env.pop('CLAUDE_CODE_REMOTE', None)

    def run(args, cwd=ROOT):
        return subprocess.run([sys.executable, *args], cwd=str(cwd),
                              capture_output=True, text=True, env=env)

    def practice(slug, story='A dated incident.'):
        return ('---\nslug:        ' + slug + '\n'
                'title:       A fixture practice\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["fixture/**"]\noccasion:    "fixture"\n'
                'gates:       []\nindex_clause: "fixture"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nin_force_at: null\n'
                'supersedes:  []\noverrides:   null\nadded:       "2026-09-14"\n'
                'approved_by: "Fixture, 2026-09-14"\n---\n\n## Rule\nDo the thing.\n\n'
                '## Why\nBecause.\n\n## Story\n' + story + '\n')

    try:
        tool = str(ROOT / 'tools' / 'precedent_move.py')
        team, indiv = tmp / 'precedent-team-fixture', tmp / 'precedent-individual'
        # The pair every move check starts from, bootstrapped once and copied
        # (_move_fixture_sets).
        boots = _move_fixture_sets(tmp)
        (rc1, out1), (rc2, out2) = boots['team'], boots['individual']
        cases.append(('both fixture sets bootstrap', rc1 == 0 and rc2 == 0,
                      failure_detail(out1 + out2, 600)))
        (indiv / 'practices' / 'zz-moves.md').write_text(practice('zz-moves'), encoding='utf-8')
        (indiv / 'practices' / 'zz-no-story.md').write_text(practice('zz-no-story', ''), encoding='utf-8')

        # -- the move, individual -> team --
        r = run([tool, '--slug', 'zz-moves', '--from', 'individual', '--from-path', str(indiv),
                 '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver',
                 '--strength', 'decided'])
        cases.append(('individual -> team completes', r.returncode == 0, r.stdout + r.stderr))
        dest = (team / 'practices' / 'zz-moves.md')
        src = (indiv / 'practices' / 'zz-moves.md')
        dtext = dest.read_text(encoding='utf-8') if dest.is_file() else ''
        stext = src.read_text(encoding='utf-8')
        cases.append(('the destination copy is active, carries the Rule and Story verbatim, '
                      'the approval, and its strength',
                      'status:      active' in dtext and 'Do the thing.' in dtext
                      and 'A dated incident.' in dtext and 'Fixture Approver' in dtext
                      and 'strength: decided' in dtext, dtext[:600]))
        cases.append(('the source copy is deduplicated, points at the slug, and its Story '
                      'says where it went',
                      'status:      deduplicated' in stext and 'in_force_at: zz-moves' in stext
                      and 'Moved to the shared set `precedent-team-fixture`' in stext, failure_detail(stext, 400)))
        cases.append(('the disclosure names both sets and the level',
                      'DISCLOSE TO THE HUMAN' in r.stdout and 'shared set precedent-team-fixture' in r.stdout
                      and 'individual set precedent-individual' in r.stdout, failure_detail(r.stdout, 400)))

        # -- sibling links that do not travel are re-homed by the move itself --
        # On 2026-09-23 a moved practice kept its relative links to siblings
        # that stayed in a private set, and the hand repair pointed them at
        # that set by URL. The move now does the repair: a universal
        # practice gets its universal URL, anything else its backticked slug.
        (indiv / 'practices' / 'zz-left-behind.md').write_text(
            practice('zz-left-behind'), encoding='utf-8')
        (indiv / 'practices' / 'zz-links.md').write_text(
            practice('zz-links', 'See [`zz-left-behind`](zz-left-behind.md), '
                     '[the rule](zz-left-behind.md#rule), '
                     '[park-it](park-it.md) and `[kept](zz-left-behind.md)`.'),
            encoding='utf-8')
        r = run([tool, '--slug', 'zz-links', '--from', 'individual', '--from-path', str(indiv),
                 '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver'])
        ltext = ((team / 'practices' / 'zz-links.md').read_text(encoding='utf-8')
                 if (team / 'practices' / 'zz-links.md').is_file() else '')
        cases.append(('a move re-homes sibling links that do not travel: the backticked '
                      'slug for a set practice, the universal URL for a universal one, '
                      'and a link inside a code span untouched',
                      r.returncode == 0
                      and 'See `zz-left-behind`, the rule (`zz-left-behind`)' in ltext
                      and '/practices/park-it.md)' in ltext
                      and '`[kept](zz-left-behind.md)`' in ltext
                      and str(indiv) not in ltext and 'precedent-individual/blob' not in ltext
                      and 'rewrote a sibling link' in r.stdout,
                      failure_detail(r.stdout + r.stderr, 600) + failure_detail(ltext, 400)))

        # -- a consumer resolving both sets sees the practice from the team, once --
        consumer = tmp / 'consumer'
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                        {'level': 'team', 'name': 'precedent-team-fixture', 'path': str(team)}],
        }), encoding='utf-8')
        cfg = tmp / 'user-config.json'
        cfg.write_text(json.dumps({'individual': {'name': 'precedent-individual',
                                                  'path': str(indiv)}}), encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                            '--repo', str(consumer), '--json'],
                           capture_output=True, text=True,
                           env=dict(env, PRECEDENT_USER_CONFIG=str(cfg)))
        try:
            resolved = json.loads(r.stdout)
        except json.JSONDecodeError:
            resolved = {}
        levels = {p['slug']: p['level'] for p in resolved.get('practices', [])}
        cases.append(('a consumer resolving both sets gets the moved practice from the '
                      'team, once, and the deduplicated copy is not reported as a collision',
                      levels.get('zz-moves') == 'shared'
                      and not resolved.get('blocked'), (r.stdout + r.stderr)[:600]))

        # -- the resolver names a forwarding address that resolves nowhere --
        # (the rehearsal of 2026-09-14 found that only this harness ever
        # asked; a set or a consumer ran the shape check alone)
        ipath = indiv / 'practices' / 'zz-moves.md'
        itext = ipath.read_text(encoding='utf-8')
        ipath.write_text(itext.replace('in_force_at: zz-moves', 'in_force_at: zz-nowhere'),
                         encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                            '--repo', str(consumer), '--json'],
                           capture_output=True, text=True,
                           env=dict(env, PRECEDENT_USER_CONFIG=str(cfg)))
        try:
            dangling = json.loads(r.stdout).get('dangling') or []
        except json.JSONDecodeError:
            dangling = []
        cases.append(('a deduplicated copy whose in_force_at resolves nowhere is reported '
                      'by the resolver itself, not only by this harness',
                      any(d.get('slug') == 'zz-moves' and 'does not resolve IN FORCE' in d.get('why', '')
                          for d in dangling), failure_detail(r.stdout + r.stderr, 500)))
        ipath.write_text(itext, encoding='utf-8')

        # -- a copy-and-delete, the thing the procedure says never to do, is named by sync --
        (consumer / 'AGENTS.md').write_text('# notes\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                                            '<!-- END GENERATED -->\n', encoding='utf-8')
        (team / 'practices' / 'zz-copied.md').write_text(practice('zz-copied'), encoding='utf-8')
        cenv = dict(env, PRECEDENT_USER_CONFIG=str(cfg))
        subprocess.run(['git', 'init', '-q'], cwd=str(consumer), capture_output=True)
        sync_tool = str(ROOT / 'tools' / 'precedent_sync_views.py')
        r = subprocess.run([sys.executable, sync_tool, '--repo', str(consumer)],
                           capture_output=True, text=True, env=cenv)
        subprocess.run(['git', 'add', '-A'], cwd=str(consumer), capture_output=True)
        subprocess.run(['git', '-c', 'user.name=fx', '-c', 'user.email=fx',
                        'commit', '-q', '-m', 'sync'], cwd=str(consumer),
                       capture_output=True, env=cenv)
        cases.append(('the consumer committed a synced MANIFEST.json recording zz-copied from the team',
                      r.returncode == 0 and 'zz-copied' in (consumer / 'MANIFEST.json').read_text(encoding='utf-8'),
                      failure_detail(r.stdout + r.stderr, 400)))
        shutil.copy(team / 'practices' / 'zz-copied.md', indiv / 'practices' / 'zz-copied.md')
        (team / 'practices' / 'zz-copied.md').unlink()
        r = subprocess.run([sys.executable, sync_tool, '--repo', str(consumer)],
                           capture_output=True, text=True, env=cenv)
        cases.append(('copying the file to the other set and deleting the original is named '
                      'as a copy-and-delete by the next sync, and the sync still writes',
                      r.returncode == 0 and 'copy-and-delete' in r.stderr
                      and 'zz-copied was recorded from precedent-team-fixture' in r.stderr,
                      failure_detail(r.stdout + r.stderr, 500)))
        (team / 'practices' / 'zz-copied.md').write_text(
            (indiv / 'practices' / 'zz-copied.md').read_text(encoding='utf-8')
            .replace('status:      active', 'status:      deduplicated')
            .replace('in_force_at: null', 'in_force_at: zz-copied'), encoding='utf-8')
        r = subprocess.run([sys.executable, sync_tool, '--repo', str(consumer)],
                           capture_output=True, text=True, env=cenv)
        cases.append(('and a deduplicated copy left at the source, pointing across, is a record: '
                      'the same sync says nothing',
                      r.returncode == 0 and 'copy-and-delete' not in r.stderr,
                      failure_detail(r.stdout + r.stderr, 500)))

        # -- refusals, each by its own message --
        r = run([tool, '--slug', 'zz-no-story', '--from', 'individual', '--from-path', str(indiv),
                 '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver'])
        cases.append(('an empty Story is refused, naming the fill-it-first rule',
                      r.returncode == 1 and 'empty ## Story' in r.stderr, r.stderr[:300]))
        cases.append(('and the refusal wrote nothing',
                      not (team / 'practices' / 'zz-no-story.md').exists(), ''))
        r = run([tool, '--slug', 'zz-moves', '--from', 'team', '--from-path', str(team),
                 '--to', 'individual', '--to-path', str(indiv), '--approved-by', 'Anyone'])
        cases.append(('a destination that already carries the slug is refused',
                      r.returncode == 1 and 'already exists' in r.stderr, r.stderr[:300]))
        (team / 'practices' / 'zz-team-only.md').write_text(practice('zz-team-only'), encoding='utf-8')
        (indiv / 'practices' / 'zz-second.md').write_text(practice('zz-second'), encoding='utf-8')
        r = run([tool, '--slug', 'zz-second', '--from', 'individual', '--from-path', str(indiv),
                 '--to', 'team', '--to-path', str(team), '--approved-by', 'Nobody'])
        cases.append(('an approver not listed in the shared set is refused by name',
                      r.returncode == 1 and 'not in' in r.stderr and 'approver' in r.stderr,
                      r.stderr[:300]))
        # -- universal -> team duplicates, never deduplicates, on landing;
        # only a deliberate --dedupe-only --accept-reach-loss withdraws the
        # universal copy. A fixture universal clone, not this checkout's own
        # practices/, the same reason 'team -> universal' below uses one. --
        uclone = tmp / 'precedent-universal-fixture'
        (uclone / 'practices').mkdir(parents=True)
        (uclone / 'practices' / 'zz-universal.md').write_text(practice('zz-universal'), encoding='utf-8')
        r = run([tool, '--slug', 'zz-universal', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'universal', '--to-path', str(uclone), '--approved-by', 'Fixture Approver'])
        cases.append(('universal -> universal is refused as nothing to move',
                      r.returncode == 1 and 'nothing to move' in r.stderr, r.stderr[:300]))
        r = run([tool, '--slug', 'zz-universal', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver'])
        utext = (uclone / 'practices' / 'zz-universal.md').read_text(encoding='utf-8')
        ttext2 = (team / 'practices' / 'zz-universal.md').read_text(encoding='utf-8') \
            if (team / 'practices' / 'zz-universal.md').is_file() else ''
        cases.append(('universal -> team lands at the destination and completes',
                      r.returncode == 0 and 'status:      active' in ttext2, r.stdout + r.stderr))
        cases.append(('the universal copy stays ACTIVE, not deduplicated -- both are in force',
                      'status:      active' in utext and 'in_force_at: null' in utext
                      and 'Also landed' in utext, failure_detail(utext, 500)))
        cases.append(('the disclosure says both copies are in force and names the deliberate '
                      'withdrawal command',
                      'ALSO lives' in r.stdout and 'NOT deduplicated' in r.stdout
                      and '--dedupe-only --accept-reach-loss' in r.stdout, failure_detail(r.stdout, 500)))
        r = run([tool, '--slug', 'zz-universal', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--dedupe-only'])
        cases.append(('--dedupe-only on a universal source is refused without --accept-reach-loss',
                      r.returncode == 1 and '--accept-reach-loss' in r.stderr, r.stderr[:400]))
        cases.append(('and the refusal left the universal copy untouched',
                      (uclone / 'practices' / 'zz-universal.md').read_text(encoding='utf-8') == utext, ''))
        r = run([tool, '--slug', 'zz-universal', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--dedupe-only', '--accept-reach-loss'])
        utext = (uclone / 'practices' / 'zz-universal.md').read_text(encoding='utf-8')
        cases.append(('--dedupe-only --accept-reach-loss withdraws the universal copy',
                      r.returncode == 0 and 'status:      deduplicated' in utext
                      and 'in_force_at: zz-universal' in utext
                      and 'WITHDRAWN from universal' in r.stdout, r.stdout + r.stderr))

        # -- team -> universal drafts, leaves the source active, and dedupes on request --
        clone = tmp / 'precedent-clone'
        clone.mkdir()
        (clone / 'practices').mkdir()
        r = run([tool, '--slug', 'zz-team-only', '--from', 'team', '--from-path', str(team),
                 '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Fixture Approver'])
        ttext = (team / 'practices' / 'zz-team-only.md').read_text(encoding='utf-8')
        cases.append(('team -> universal drafts into the clone and leaves the source ACTIVE',
                      r.returncode == 0 and (clone / 'practices' / 'zz-team-only.md').is_file()
                      and 'status:      active' in ttext and 'DRAFTED' in r.stdout,
                      r.stdout + r.stderr))
        cases.append(('the draft says the clone\'s own generated surfaces were (or here could not be) '
                      'regenerated, and when it is safe to --dedupe-only: after the merge AND '
                      'after every consumer has taken the catalogue',
                      'tools/build_views.py' in r.stdout and 'doc_sync.py' in r.stdout
                      and 'every repository consuming' in r.stdout, failure_detail(r.stdout, 700)))
        r = run([tool, '--slug', 'zz-team-only', '--from', 'team', '--from-path', str(team),
                 '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Fixture Approver',
                 '--dedupe-only'])
        ttext = (team / 'practices' / 'zz-team-only.md').read_text(encoding='utf-8')
        cases.append(('--dedupe-only afterwards withdraws the source copy',
                      r.returncode == 0 and 'status:      deduplicated' in ttext
                      and 'in_force_at: zz-team-only' in ttext, r.stdout + r.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'tools/precedent_move.py lands first, deduplicates second, and refuses the '
          f'unsafe states by name ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def _move_fixture_sets(tmp, which=('team', 'individual')):
    """Bootstrap the move checks' starting sets into `tmp`:
    precedent-team-fixture, a shared set at the `team` level with the
    fixture approver, and precedent-individual, an individual set -- what
    every move check below bootstrapped for itself, with the same arguments.
    Through _fixture_tree_cache, so a run bootstraps the pair once and each
    check copies the sets it names in `which`.
    -> {level: (returncode, output)} for each of them."""
    def build(root, env):
        env = dict(env, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        got = {}
        for level, name in _MOVE_SETS.items():
            extra = ['--approver', 'Fixture Approver:fixture-gh'] if level == 'team' else []
            r = subprocess.run([sys.executable,
                                str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                                '--level', level, '--name', name, '--dest', str(root / name),
                                *extra], capture_output=True, text=True, env=env,
                               cwd=str(ROOT))
            got[f'{level} rc'], got[f'{level} out'] = str(r.returncode), r.stdout + r.stderr
        return all(got[f'{lv} rc'] == '0' for lv in _MOVE_SETS), got
    out = _fixture_tree_cache('move-sets 1', tmp, build,
                              only=[_MOVE_SETS[w] for w in which])
    return {w: (int(out[f'{w} rc']), out[f'{w} out']) for w in which}


def check_move_tool_covers_every_direction_and_team_removals():
    """The directions check_move_tool_lands_then_deduplicates does not run
    -- team to individual, universal to individual, individual to universal
    -- and the approval a TEAM REMOVAL needs, which the tool never checked.

    WHY. A very deep check on 2026-09-28 rehearsed every direction and found
    three things this fixture now holds: spec/MOVING_PRACTICES.md said the
    harness moved a practice "through every direction" when it ran three;
    a team copy was deduplicated on the DESTINATION's approval alone, and
    `--dedupe-only` from a team asked for no name at all, though the
    procedure says removing a team's practice is that team's approvers'
    call; and a universal draft with no ## Install passed every fast check
    and failed the harness. Separately, the Story line a move appends went
    to the end of the FILE, which is inside ## Install whenever the file
    has one -- so it is planted with one here."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-dirs-'))
    env = _move_fixture_env(tmp)
    cases = []

    def run(*args):
        return subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_move.py'),
                               *args], cwd=str(ROOT), capture_output=True, text=True,
                              env=env)

    def text(p):
        return p.read_text(encoding='utf-8') if p.is_file() else ''

    try:
        team, indiv = tmp / 'precedent-team-fixture', tmp / 'precedent-individual'
        # The pair every move check starts from, bootstrapped once and copied
        # (_move_fixture_sets).
        _move_fixture_sets(tmp)
        uclone = tmp / 'precedent-universal-fixture'
        (uclone / 'practices').mkdir(parents=True)
        P = _move_fixture_practice
        (team / 'practices' / 'zz-down.md').write_text(
            P('zz-down', install='Nothing to install.'), encoding='utf-8')
        (team / 'practices' / 'zz-guarded.md').write_text(P('zz-guarded'), encoding='utf-8')
        (uclone / 'practices' / 'zz-out.md').write_text(P('zz-out'), encoding='utf-8')
        (indiv / 'practices' / 'zz-up.md').write_text(P('zz-up'), encoding='utf-8')

        # -- team -> individual: a removal from the team needs ITS approver --
        r = run('--slug', 'zz-guarded', '--from', 'team', '--from-path', str(team),
                '--to', 'individual', '--to-path', str(indiv), '--approved-by', 'Somebody Else')
        cases.append(('team -> individual by a name the team does not list is refused as a '
                      'REMOVAL needing that team\'s approver, and writes nothing',
                      r.returncode == 1 and 'removing a practice from a shared set' in r.stderr
                      and not (indiv / 'practices' / 'zz-guarded.md').exists()
                      and 'status:      active' in text(team / 'practices' / 'zz-guarded.md'),
                      failure_detail(r.stderr, 400)))
        r = run('--slug', 'zz-down', '--from', 'team', '--from-path', str(team),
                '--to', 'individual', '--to-path', str(indiv), '--approved-by', 'Fixture Approver')
        src, dest = text(team / 'practices' / 'zz-down.md'), text(indiv / 'practices' / 'zz-down.md')
        story = src[src.find('## Story'):src.find('## Install')]
        cases.append(('team -> individual lands active and deduplicates the team copy',
                      r.returncode == 0 and 'status:      active' in dest
                      and 'status:      deduplicated' in src and 'in_force_at: zz-down' in src,
                      failure_detail(r.stdout + r.stderr, 500)))
        cases.append(('the team copy\'s Story line names who approved the removal, and sits '
                      'in ## Story -- not after ## Install, where nothing reads a Story',
                      'removal from `precedent-team-fixture` approved by Fixture Approver'
                      # An individual set is named only as one outside it
                      # (2026-10-17).
                      in story and 'Moved to an individual set' in story
                      and src.rstrip().endswith('Nothing to install.'), failure_detail(src, 700)))

        # -- --dedupe-only from a team needs --approved-by at all --
        (indiv / 'practices' / 'zz-guarded.md').write_text(P('zz-guarded'), encoding='utf-8')
        r = run('--slug', 'zz-guarded', '--from', 'team', '--from-path', str(team),
                '--to', 'individual', '--to-path', str(indiv), '--dedupe-only')
        cases.append(('--dedupe-only from a shared set with no --approved-by is refused',
                      r.returncode == 1 and '--approved-by' in r.stderr
                      and 'status:      active' in text(team / 'practices' / 'zz-guarded.md'),
                      failure_detail(r.stderr, 400)))

        # -- universal -> individual: duplicate, then a deliberate withdrawal --
        r = run('--slug', 'zz-out', '--from', 'universal', '--from-path', str(uclone),
                '--to', 'individual', '--to-path', str(indiv), '--approved-by', 'Owner')
        u = text(uclone / 'practices' / 'zz-out.md')
        cases.append(('universal -> individual lands the copy and keeps the universal one ACTIVE',
                      r.returncode == 0 and 'status:      active' in u
                      and 'status:      active' in text(indiv / 'practices' / 'zz-out.md'),
                      failure_detail(r.stdout + r.stderr, 500)))
        r = run('--slug', 'zz-out', '--from', 'universal', '--from-path', str(uclone),
                '--to', 'individual', '--to-path', str(indiv), '--dedupe-only',
                '--accept-reach-loss', '--approved-by', 'Owner')
        u = text(uclone / 'practices' / 'zz-out.md')
        # The universal clone is public: the individual set is named only as
        # one there (2026-10-17), and still reads back as a withdrawal.
        cases.append(('universal -> individual withdraws with --accept-reach-loss, and the '
                      'Story line says where (an individual set, unnamed) and who approved it',
                      r.returncode == 0 and 'status:      deduplicated' in u
                      and '--accept-reach-loss (approved by Owner)' in u
                      and 'in force only from an individual set now' in u
                      and 'precedent-individual' not in u,
                      failure_detail(r.stdout + r.stderr, 500)))

        # -- individual -> universal: a draft, given the ## Install it lacked --
        clone = tmp / 'precedent-clone'
        (clone / 'practices').mkdir(parents=True)
        r = run('--slug', 'zz-up', '--from', 'individual', '--from-path', str(indiv),
                '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Owner')
        draft = clone / 'practices' / 'zz-up.md'
        try:
            _fm, secs = sp._read_practice_file(draft)
        except Exception:                                    # noqa: BLE001
            secs = {}
        cases.append(('individual -> universal drafts, leaves the source active, and gives '
                      'the draft the ## Install every universal practice carries -- saying so',
                      r.returncode == 0 and 'install' in secs and 'DRAFTED' in r.stdout
                      and 'ADDED an empty ## Install' in r.stdout
                      and 'status:      active' in text(indiv / 'practices' / 'zz-up.md'),
                      failure_detail(r.stdout + r.stderr, 500)))

        # -- a universal draft is put in the spec's field order, and an
        #    on-demand one with no applies_to_why is told to add it
        #    (2026-10-05: five drafts from working-style failed the deep
        #    check on both) --
        import frontmatter_yaml
        shuffled = P('zz-order').replace('in_force_at: null\n', '').replace(
            'approved_by: "Fixture, 2026-09-14"\n',
            'approved_by: "Fixture, 2026-09-14"\nin_force_at: null\n')
        (indiv / 'practices' / 'zz-order.md').write_text(shuffled, encoding='utf-8')
        r = run('--slug', 'zz-order', '--from', 'individual', '--from-path', str(indiv),
                '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Owner')
        drafted = text(clone / 'practices' / 'zz-order.md')
        cases.append(('a universal draft from a file whose fields are out of the spec\'s '
                      'order lands in order, and the tool asks for the applies_to_why '
                      'an on-demand practice there must carry',
                      r.returncode == 0 and frontmatter_yaml.field_order_problem(shuffled)
                      and drafted and not frontmatter_yaml.field_order_problem(drafted)
                      and 'ADD an applies_to_why' in r.stdout,
                      failure_detail(r.stdout + r.stderr, 500)))

        # -- a universal draft whose check IS registered there gets its
        #    checked_by repointed from the set's script to the engine
        #    (2026-10-05: five drafts from repo-maintenance each carried
        #    a tools/checks/ path universal does not have) --
        (indiv / 'practices' / 'default-branch.md').write_text(
            P('default-branch').replace(
                'checked_by:  null', 'checked_by:  "tools/checks/check_default_branch.py"'),
            encoding='utf-8')
        r = run('--slug', 'default-branch', '--from', 'individual', '--from-path', str(indiv),
                '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Owner')
        cases.append(('a universal draft whose check universal registers names '
                      'tools/precedent_check.py, not the set\'s script, and says so',
                      r.returncode == 0 and 'REPOINTED checked_by' in r.stdout
                      and 'checked_by:  "tools/precedent_check.py"'
                      in text(clone / 'practices' / 'default-branch.md'),
                      failure_detail(r.stdout + r.stderr, 500)))

        # -- a universal draft whose check universal does not register: a
        #    refusal, not a traceback (2026-10-05, moving assorted-notes) --
        (indiv / 'practices' / 'zz-checked.md').write_text(
            P('zz-checked').replace(
                'checked_by:  null', 'checked_by:  "tools/checks/check_zz_checked.py"'),
            encoding='utf-8')
        r = run('--slug', 'zz-checked', '--from', 'individual', '--from-path', str(indiv),
                '--to', 'universal', '--to-path', str(clone), '--approved-by', 'Owner')
        cases.append(('a universal draft whose checked_by universal does not register is '
                      'refused by name, with no traceback, and writes nothing',
                      r.returncode == 1 and 'precedent_move FAIL' in r.stderr
                      and 'Traceback' not in r.stderr
                      and not (clone / 'practices' / 'zz-checked.md').exists(),
                      failure_detail(r.stderr, 500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'tools/precedent_move.py runs the remaining directions and asks a team\'s own '
          f'approver before removing its practice ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_move_tool_names_sets_truly_and_keeps_approvals_current():
    """tools/precedent_move.py names each set as the set declares itself,
    never names an individual set outside it, keeps every approved_by true
    after the step that changes it, and says when a move puts a set over
    its ceiling (2026-10-17 very deep check, findings on the move tool).

    Stated cases, each against the defect it pins:
      - a set checked out under another directory name is named by its
        precedent-source.json, in Story and in approval;
      - after --dedupe-only --accept-reach-loss the set copy's approved_by
        no longer says a universal copy "stays active";
      - shared -> individual takes the individual owner's yes (checked
        against identity.json) and a shared approver's for the removal
        (--removal-approved-by), and writes no individual set's name into
        the shared set, its Story or its mentions;
      - an individual -> universal draft does not name the individual set;
      - the --dedupe-only after a move into universal rewrites the
        "pending PR review" approval when git shows the merge, and says
        what to write when it does not;
      - "`x` lives in universal, which ..." is named for a person, a link
        repointed inside "... is the universal copy" is too, and a prose
        rewrite on a line with no link gets no "its link now points" note;
      - a move that puts a set over its declared ceiling says so;
      - a universal rule withdrawn to an individual set is never told to
        "declare that set"."""
    import shutil, tempfile
    import precedent_resolve as pr
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-names-'))
    env = _move_fixture_env(tmp)
    cases = []

    def run(*args):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_move.py'),
                            *args], cwd=str(ROOT), capture_output=True, text=True,
                           env=env)
        return r, r.stdout + r.stderr

    def text(p):
        return p.read_text(encoding='utf-8') if p.is_file() else ''

    def git(repo, *a):
        return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C',
                               str(repo), *a], capture_output=True, text=True)

    def commit_all(repo, msg='fixture'):
        git(repo, 'add', '-A')
        git(repo, '-c', 'user.email=h@example.com', '-c', 'user.name=h',
            'commit', '-qm', msg)

    try:
        boot = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        # The shared set's checkout directory is NOT its name.
        shared, indiv = tmp / 'shared-two-checkout', tmp / 'zz-person-set'
        subprocess.run([sys.executable, boot, '--level', 'shared', '--name',
                        'precedent-shared-real', '--dest', str(shared),
                        '--approver', 'Fixture Approver:fixture-gh'],
                       capture_output=True, text=True, env=env)
        subprocess.run([sys.executable, boot, '--level', 'individual', '--name',
                        'zz-person-set', '--dest', str(indiv)],
                       capture_output=True, text=True, env=env)
        ident = json.loads(text(indiv / 'identity.json') or '{}')
        ident.update(name='Pat Owner', github='pat-owner')
        (indiv / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')
        uclone = tmp / 'BestPractice'
        (uclone / 'practices').mkdir(parents=True)
        (uclone / 'docs').mkdir()
        P = _move_fixture_practice
        (uclone / 'practices' / 'zz-out.md').write_text(P('zz-out'), encoding='utf-8')
        (uclone / 'docs' / 'notes.md').write_text(
            '# Notes\n\n`zz-out` lives in universal, which every consumer '
            'resolves.\n', encoding='utf-8')
        (shared / 'practices' / 'zz-down.md').write_text(P('zz-down'), encoding='utf-8')
        (shared / 'NOTES.md').write_text(
            '# Notes\n\n'
            '- `zz-down` (precedent-shared-real) is the rule we pair with.\n\n'
            '- [zz-out](https://github.com/example/BestPractice/blob/main/'
            'practices/zz-out.md) is the universal copy we lean on.\n\n'
            '- `zz-hab` (zz-person-set) is the habit rule this set leans on.\n',
            encoding='utf-8')
        (indiv / 'practices' / 'zz-up.md').write_text(P('zz-up'), encoding='utf-8')
        (indiv / 'practices' / 'zz-hab.md').write_text(P('zz-hab'), encoding='utf-8')
        for repo in (shared, indiv, uclone):
            git(repo, 'init', '-q', '-b', 'main')
            commit_all(repo)

        # -- universal -> shared, then the deliberate withdrawal --
        r, out = run('--slug', 'zz-out', '--from', 'universal', '--from-path',
                     str(uclone), '--to', 'shared', '--to-path', str(shared),
                     '--approved-by', 'Fixture Approver')
        commit_all(shared)
        commit_all(uclone)
        r, out = run('--slug', 'zz-out', '--from', 'universal', '--from-path',
                     str(uclone), '--to', 'shared', '--to-path', str(shared),
                     '--dedupe-only', '--accept-reach-loss', '--approved-by',
                     'Fixture Approver')
        u, s = text(uclone / 'practices' / 'zz-out.md'), text(shared / 'practices' / 'zz-out.md')
        cases.append(('a set checked out under another directory is named by its '
                      'precedent-source.json in the universal Story',
                      r.returncode == 0 and '`precedent-shared-real`' in u
                      and 'shared-two-checkout' not in u, failure_detail(out, 600)))
        cases.append(('after --dedupe-only --accept-reach-loss the set copy no longer '
                      'says a universal copy stays active',
                      'where a copy stays active' not in s
                      and 'deduplicated there on' in s, s[:900]))
        cases.append(('"`x` lives in universal, which ..." is named for a person, '
                      'not passed over', 'could not fix: BestPractice/docs/notes.md:3'
                      in out, failure_detail(out, 900)))
        cases.append(('a link repointed inside "... is the universal copy we lean on" '
                      'is named for rewording', 'shared-two-checkout/NOTES.md:5' in out
                      and 'still calls it the universal copy' in out, failure_detail(out, 900)))

        # -- shared -> individual: two approvals, and no individual name in the shared set --
        r, out = run('--slug', 'zz-down', '--from', 'shared', '--from-path', str(shared),
                     '--to', 'individual', '--to-path', str(indiv),
                     '--approved-by', 'Somebody Else',
                     '--removal-approved-by', 'Fixture Approver')
        cases.append(('landing in an individual set by a name its identity.json does '
                      'not declare is refused', r.returncode == 1
                      and 'not the owner' in out, failure_detail(out, 500)))
        r, out = run('--slug', 'zz-down', '--from', 'shared', '--from-path', str(shared),
                     '--to', 'individual', '--to-path', str(indiv),
                     '--approved-by', 'Pat Owner',
                     '--removal-approved-by', 'Fixture Approver')
        sd, notes = text(shared / 'practices' / 'zz-down.md'), text(shared / 'NOTES.md')
        cases.append(('shared -> individual takes the owner for the landing and a '
                      'shared approver for the removal (--removal-approved-by)',
                      r.returncode == 0 and 'status:      deduplicated' in sd
                      and 'removal from `precedent-shared-real` approved by Fixture '
                      'Approver' in sd, failure_detail(out, 600)))
        cases.append(('the shared stub and the shared set\'s mentions never name the '
                      'individual set', 'zz-person-set' not in sd
                      and 'Moved to an individual set' in sd
                      and '`zz-down` (an individual set)' in notes
                      and 'zz-down` (zz-person-set)' not in notes, failure_detail(sd, 500) + notes))

        # -- individual -> shared: a prose rewrite with no link gets no link note --
        r, out = run('--slug', 'zz-hab', '--from', 'individual', '--from-path', str(indiv),
                     '--to', 'shared', '--to-path', str(shared),
                     '--approved-by', 'Fixture Approver')
        cases.append(('a prose rewrite on a line with no link gets no "its link now '
                      'points" note', r.returncode == 0
                      and 'NOTES.md:7 -- its link' not in out
                      and '`zz-hab` (precedent-shared-real)' in text(shared / 'NOTES.md'),
                      failure_detail(out, 600)))

        # -- individual -> universal: the draft names no individual set --
        r, out = run('--slug', 'zz-up', '--from', 'individual', '--from-path', str(indiv),
                     '--to', 'universal', '--to-path', str(uclone), '--approved-by', 'Pat Owner')
        d = text(uclone / 'practices' / 'zz-up.md')
        cases.append(('an individual -> universal draft says "moved from an individual '
                      'set", never its name', r.returncode == 0
                      and 'moved from an individual set' in d and 'zz-person-set' not in d,
                      d[:700]))
        r, out = run('--slug', 'zz-up', '--from', 'individual', '--from-path', str(indiv),
                     '--to', 'universal', '--to-path', str(uclone), '--dedupe-only')
        cases.append(('its --dedupe-only before the merge says the placeholder must be '
                      'rewritten, and leaves it', r.returncode == 0
                      and 'still says approved_by "pending PR review"' in out
                      and 'pending PR review' in text(uclone / 'practices' / 'zz-up.md'),
                      failure_detail(out, 600)))
        # Merged: origin/main has the draft.
        (indiv / 'practices' / 'zz-up2.md').write_text(P('zz-up2'), encoding='utf-8')
        run('--slug', 'zz-up2', '--from', 'individual', '--from-path', str(indiv),
            '--to', 'universal', '--to-path', str(uclone), '--approved-by', 'Pat Owner')
        bare = tmp / 'origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(bare)], capture_output=True)
        commit_all(uclone, 'Draft zz-up2 (#41)')
        git(uclone, 'remote', 'add', 'origin', str(bare))
        git(uclone, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
        git(uclone, 'fetch', '-q', 'origin')
        r, out = run('--slug', 'zz-up2', '--from', 'individual', '--from-path', str(indiv),
                     '--to', 'universal', '--to-path', str(uclone), '--dedupe-only')
        d2 = text(uclone / 'practices' / 'zz-up2.md')
        cases.append(('its --dedupe-only after the merge rewrites the placeholder from '
                      'git', r.returncode == 0 and 'pending PR review' not in d2
                      and 'merged in PR #41' in d2 and 'drafted' in d2, d2[:800]))

        # -- a move that puts a set over its declared ceiling says so --
        reg_f = shared / 'tools' / 'session_load_budgets.json'
        reg = json.loads(text(reg_f) or '{"surfaces": {}}')
        reg.setdefault('surfaces', {}).setdefault('AGENTS.md', {})['ceiling'] = 10
        reg_f.write_text(json.dumps(reg), encoding='utf-8')
        (indiv / 'practices' / 'zz-big.md').write_text(P('zz-big'), encoding='utf-8')
        r, out = run('--slug', 'zz-big', '--from', 'individual', '--from-path', str(indiv),
                     '--to', 'shared', '--to-path', str(shared),
                     '--approved-by', 'Fixture Approver')
        cases.append(('a move that leaves a set over its declared ceiling warns, naming '
                      'the set and the ceiling',
                      'WARNING: precedent-shared-real: AGENTS.md is now' in out
                      and 'ceiling of 10' in out, failure_detail(out, 600)))

        # -- withdrawn to an individual set: never "declare that set" --
        (uclone / 'practices' / 'zz-gone.md').write_text(P('zz-gone'), encoding='utf-8')
        commit_all(uclone)
        run('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
            '--to', 'individual', '--to-path', str(indiv), '--approved-by', 'Pat Owner')
        r, out = run('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                     '--to', 'individual', '--to-path', str(indiv), '--dedupe-only',
                     '--accept-reach-loss', '--approved-by', 'Pat Owner')
        g = text(uclone / 'practices' / 'zz-gone.md')
        res = pr.resolve([{'level': 'universal', 'name': 'precedent',
                           'path': str(uclone)}])
        why = ' '.join(d_.get('why', '') for d_ in res.get('dangling', ())
                       if d_.get('slug') == 'zz-gone')
        cases.append(('a universal rule withdrawn to an individual set names no set '
                      'in the public clone, and is never told to "declare that set"',
                      r.returncode == 0 and 'zz-person-set' not in g
                      and 'user config' in why and 'declare that set' not in why,
                      why or failure_detail(g, 500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'tools/precedent_move.py names sets as they declare themselves, keeps '
          f'an individual set\'s name inside it, keeps approvals true and warns '
          f'on a ceiling ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_move_withdrawal_from_universal_leaves_universal_green():
    """Withdrawing a universal practice (`--dedupe-only --accept-reach-loss`)
    leaves nothing behind that turns the universal clone's own checks red,
    and a consumer that no longer gets the rule is told where it went.

    WHY. Rehearsed 2026-09-28: the withdrawal left a `routing_audit_state.json`
    rotation entry for the slug (routing-audit: stale bookkeeping) and a
    `# practice: <slug>` citation under tools/ (code-cites-practice: cites a
    practice that is not active). And every consumer's sync then said IN FORCE
    NOWHERE "-- this is the deduplication that silently loses a rule" about
    two practices withdrawn on purpose, with the set named in their Story."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-withdraw-'))
    env = _move_fixture_env(tmp)
    cases = []

    def run(*args):
        return subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_move.py'),
                               *args], cwd=str(ROOT), capture_output=True, text=True,
                              env=env)

    try:
        team = tmp / 'precedent-team-fixture'
        # The team set every move check starts from, bootstrapped once and
        # copied (_move_fixture_sets).
        _move_fixture_sets(tmp, ('team',))
        uclone = tmp / 'precedent'
        (uclone / 'practices').mkdir(parents=True)
        (uclone / 'tools').mkdir()
        (uclone / 'practices' / 'zz-gone.md').write_text(
            _move_fixture_practice('zz-gone', install='Nothing.'), encoding='utf-8')
        (uclone / 'practices' / 'zz-stays.md').write_text(
            _move_fixture_practice('zz-stays'), encoding='utf-8')
        state = uclone / 'tools' / 'routing_audit_state.json'
        state.write_text(json.dumps({'zz-gone': {'commit': 'x', 'last_reviewed': '2026-09-01'},
                                     'zz-stays': {'commit': 'x', 'last_reviewed': '2026-09-01'}},
                                    indent=2, sort_keys=True) + '\n', encoding='utf-8')
        code = uclone / 'tools' / 'thing.py'
        code.write_text('x = 1  # practice: zz-gone\n', encoding='utf-8')

        r = run('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver')
        cases.append(('the universal practice lands in the team, duplicated', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 400)))
        before = (uclone / 'practices' / 'zz-gone.md').read_text(encoding='utf-8')
        r = run('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                '--to', 'team', '--to-path', str(team), '--dedupe-only', '--accept-reach-loss')
        cases.append(('the withdrawal is refused while the clone\'s tools/ still cite the '
                      'practice, naming the file and line, and writes nothing',
                      r.returncode == 1 and 'tools/thing.py:1' in r.stderr
                      and (uclone / 'practices' / 'zz-gone.md').read_text(encoding='utf-8') == before
                      and 'zz-gone' in json.loads(state.read_text(encoding='utf-8')),
                      failure_detail(r.stderr, 400)))
        code.write_text('x = 1  # counts one thing\n', encoding='utf-8')
        r = run('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                '--to', 'team', '--to-path', str(team), '--dedupe-only', '--accept-reach-loss')
        st = json.loads(state.read_text(encoding='utf-8'))
        cases.append(('with the citation reworded, the withdrawal runs and drops the '
                      'practice\'s routing-audit entry, and only that one',
                      r.returncode == 0 and 'zz-gone' not in st and 'zz-stays' in st
                      and 'routing_audit_state.json' in r.stdout, failure_detail(r.stdout + r.stderr, 500)))

        # A consumer declaring only this universal source: the stub resolves
        # nowhere, and the warning says it was withdrawn and to which set.
        consumer = tmp / 'consumer'
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uclone)}]}),
            encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                            '--repo', str(consumer), '--json'],
                           capture_output=True, text=True, env=env)
        try:
            dangling = json.loads(r.stdout).get('dangling') or []
        except json.JSONDecodeError:
            dangling = []
        d = next((x for x in dangling if x.get('slug') == 'zz-gone'), {})
        cases.append(('a consumer that no longer gets the rule is told it was withdrawn from '
                      'universal, when, and which set to declare to keep it -- not that a '
                      'deduplication silently lost it',
                      d.get('withdrawn_to') == 'precedent-team-fixture'
                      and 'withdrawn from universal on' in d.get('why', '')
                      and 'declare that set to keep it' in d.get('why', '')
                      and 'silently loses' not in d.get('why', ''),
                      failure_detail(r.stdout + r.stderr, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'withdrawing a universal practice leaves the universal clone\'s own checks '
          f'green and tells a consumer where the rule went ({len(cases)} stated cases)',
          not failed, '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_session_check_names_commits_on_origin_off_main():
    """A set's clone checked out at the set's staging was reported "6
    unpushed commit(s) ahead" of main (2026-10-05): they were on origin,
    only not on main. Unpushed now means on no origin branch; commits on
    another origin branch are named by that branch, and are not stale."""
    import shutil, tempfile
    import precedent_session_check as psc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-clone-ahead-'))
    env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}

    def git(where, *args):
        return subprocess.run(['git', '-C', str(where), *args], env=env,
                              capture_output=True, text=True)
    cases = []
    try:
        bare, cl = tmp / 'o.git', tmp / 'clone'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)],
                       env=env, capture_output=True)
        subprocess.run(['git', 'clone', '-q', str(bare), str(cl)], env=env,
                       capture_output=True)
        git(cl, 'checkout', '-q', '-b', 'main')
        (cl / 'a').write_text('1\n')
        git(cl, 'add', '-A'), git(cl, 'commit', '-qm', 'one')
        git(cl, 'push', '-q', 'origin', 'main')
        git(cl, 'checkout', '-q', '-b', 'staging')
        (cl / 'a').write_text('2\n')
        git(cl, 'commit', '-qam', 'two')
        git(cl, 'push', '-q', 'origin', 'staging')
        git(cl, 'checkout', '-q', '--detach', 'origin/staging')
        old = os.environ.copy()
        os.environ.update(env)
        try:
            v, phrase = psc._clone_behind(str(cl), fetch=True, branch='main')
            cases.append(('a clone at the set\'s staging is not stale and nothing '
                          'is called unpushed', v == 'current'
                          and 'unpushed' not in phrase and 'on origin' in phrase
                          and 'origin/staging' in phrase, f'{v}: {phrase}'))
            (cl / 'a').write_text('3\n')
            git(cl, 'commit', '-qam', 'three')
            v, phrase = psc._clone_behind(str(cl), fetch=True, branch='main')
            cases.append(('CONTROL: a commit on no origin branch is unpushed',
                          v == 'behind' and '1 unpushed commit(s) ahead' in phrase,
                          f'{v}: {phrase}'))
        finally:
            os.environ.clear()
            os.environ.update(old)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {d}' for n, d in bad))


def check_move_mention_fix_reads_list_items_and_names_what_it_cannot_fix():
    """The mention fix judges history a list item at a time, and names a
    current mention it could not rewrite instead of passing over it.

    WHY. Rehearsed 2026-09-28 on a real universal withdrawal: a numbered
    list in a sibling practice had one item saying "(verified 2026-08-28)",
    so the whole list read as history and the two current links to the
    withdrawn practice in a later item were neither fixed nor reported."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-move-lists-'))
    env = _move_fixture_env(tmp)
    cases = []
    try:
        team, indiv = tmp / 'precedent-team-fixture', tmp / 'precedent-individual'
        # The pair every move check starts from, bootstrapped once and copied
        # (_move_fixture_sets).
        _move_fixture_sets(tmp)
        (indiv / 'practices' / 'zz-moves.md').write_text(
            _move_fixture_practice('zz-moves'), encoding='utf-8')
        (indiv / 'NOTES.md').write_text(
            '1. **Drag** -- pointer events, verified 2026-08-28 in a frame.\n'
            '2. **Frontier** -- where it applies\n'
            '   ([zz-moves](practices/zz-moves.md)), the render opens there.\n'
            '3. Oddly phrased: precedent-individual keeps `zz-moves` close.\n',
            encoding='utf-8')
        for repo in (indiv, team):
            subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
            subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_move.py'),
                            '--slug', 'zz-moves', '--from', 'individual', '--from-path', str(indiv),
                            '--to', 'team', '--to-path', str(team),
                            '--approved-by', 'Fixture Approver'],
                           cwd=str(ROOT), capture_output=True, text=True, env=env)
        notes = (indiv / 'NOTES.md').read_text(encoding='utf-8')
        cases.append(('the move completes', r.returncode == 0, failure_detail(r.stdout + r.stderr, 400)))
        cases.append(('a current link in a list item is fixed although a SIBLING item is dated',
                      '(`zz-moves`), the render opens there.' in notes, notes))
        cases.append(('the dated item itself stays as written',
                      'verified 2026-08-28 in a frame.' in notes, notes))
        cases.append(('a current line naming the old set beside the practice that no rewrite '
                      'recognized is named "could not fix", with its line',
                      'could not fix: precedent-individual/NOTES.md:4' in r.stdout,
                      failure_detail(r.stdout, 600)))
        cases.append(('and a line that WAS fixed is not also reported as unfixed',
                      'could not fix: precedent-individual/NOTES.md:3' not in r.stdout,
                      failure_detail(r.stdout, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [c for c in cases if not c[1]]
    check(f'a move\'s mention fix reads each list item on its own and names what it could '
          f'not fix ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_bootstrapped_shared_set_carries_current_codeowners():
    """A shared set bootstrapped with an approver gets a CODEOWNERS generated
    from its approvers.json, and verify() reports one that is missing or
    stale in a set carrying the generator.

    WHY. Found 2026-09-28: bootstrap wrote approvers.json and no CODEOWNERS,
    so the approvers a new set declared enforced nothing until somebody
    remembered build_codeowners.py, and verify() called the set complete."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_bootstrap_source as pbs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-boot-codeowners-'))
    env = _move_fixture_env(tmp)
    cases = []
    try:
        team = tmp / 'precedent-team-fixture'
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                            '--level', 'team', '--name', 'precedent-team-fixture',
                            '--dest', str(team), '--approver', 'Fixture Approver:fixture-gh'],
                           capture_output=True, text=True, env=env)
        co = team / 'CODEOWNERS'
        cases.append(('bootstrap writes a CODEOWNERS naming the approver',
                      r.returncode == 0 and co.is_file()
                      and '@fixture-gh' in co.read_text(encoding='utf-8'),
                      failure_detail(r.stdout + r.stderr, 400)))
        # This clone's generator, not the set's vendored copy: bootstrap
        # vendors from committed blobs, so in an uncommitted tree the set's
        # copy can be an older generator than the one that wrote the file.
        chk = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_codeowners.py'),
                              '--repo', str(team), '--check'],
                             capture_output=True, text=True)
        cases.append(('and build_codeowners --check calls it current',
                      chk.returncode == 0, chk.stdout + chk.stderr))
        cases.append(('verify() raises no CODEOWNERS row on the fresh set',
                      not [m for m in pbs.verify('shared', team) if 'CODEOWNERS' in m], ''))
        co.unlink(missing_ok=True)
        cases.append(('verify() reports a missing CODEOWNERS in a set that carries the generator',
                      any('CODEOWNERS is missing or not current' in m
                          for m in pbs.verify('shared', team)), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [c for c in cases if not c[1]]
    check(f'a bootstrapped shared set carries a current CODEOWNERS and verify() checks it '
          f'({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_access_probe_separates_refusal_from_silence():
    """`can_land_here` must answer 'handoff' ONLY for a real permission
    refusal, and 'unknown' for everything else (practice: session-text).

    THE INCIDENT THE PROBE EXISTS FOR (2026-09-10): a session rooted in a
    private practice set built a seven-commit patch for a repo it could not
    push to, and sat blocked four days having spent about a hundred dollars
    reaching a branch nobody could land. The probe now runs at session start
    so nobody has to remember to ask.

    THE DISTINCTION THIS CHECK DEFENDS is the one that makes the answer worth
    printing. A network blip classified as 'handoff' tells a session it has no
    access where it has plenty -- and the remedy it then reaches for is
    spawning a session nobody needed. Collapsing 'unknown' into 'handoff'
    would make every case below still "work", which is exactly why the
    negative control is here: case 5 neuters the refusal vocabulary and
    asserts the verdict FLIPS, so a classifier that answered 'handoff'
    unconditionally could not pass this.

    Case 1 is a real end-to-end push --dry-run over file://, so the probe is
    measured doing its actual job rather than only its string handling."""
    import tempfile, subprocess as _sp
    import precedent_access_check as pac

    results = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # fixture-owns-its-state: this fixture asserts on what git can reach,
        # so it owns the credential environment rather than inheriting the
        # container's. A real token here would send the probe at the network.
        env = dict(os.environ)
        for var in ('PRECEDENT_GIT_TOKEN', 'PRECEDENT_SOURCE_BASE_URL'):
            env.pop(var, None)

        # 1. A genuinely writable remote answers 'land'. file:// (not a bare
        # path) because git only treats it as a transport that way.
        bare = tmp / 'origin.git'
        _sp.run(['git', 'init', '--quiet', '--bare', str(bare)], check=True, env=env)
        work = tmp / 'work'
        work.mkdir()
        for cmd in (['git', 'init', '--quiet', '-b', 'main'],
                    ['git', 'remote', 'add', 'origin', f'file://{bare}']):
            _sp.run(cmd, cwd=work, check=True, env=env)
        (work / 'f.txt').write_text('x', encoding='utf-8')
        _sp.run(['git', 'add', '.'], cwd=work, check=True, env=env)
        _sp.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@e',
                 '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'c'],
                cwd=work, check=True,
                env={**env, 'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})
        verdict, detail = pac.can_land_here(str(work))
        results.append(('a writable remote answers land', verdict == 'land', detail))

        # 2. A directory that is not a repo at all: 'unknown', and the detail
        # says which failure (practice: control-asserts-which-failure).
        plain = tmp / 'not-a-repo'
        plain.mkdir()
        v2, d2 = pac.can_land_here(str(plain))
        results.append(('a non-repo answers unknown', v2 == 'unknown', d2))

        # 3. A path with no clone at all names its own reason, verbatim.
        v3, d3 = pac.can_land_here(str(tmp / 'nothing-here'))
        results.append(('a missing clone says "no local clone to probe"',
                        v3 == 'unknown' and d3 == 'no local clone to probe', d3))

        # 4/5. The classifier, driven with canned git output so the two
        # branches are measured rather than hoped for. Restored in a finally:
        # a monkeypatch left installed would silently rewire every later check.
        real = pac._run_git
        try:
            pac._run_git = lambda repo, *a: (
                1, '', "remote: Permission to x/y denied to z.\nfatal: 403")
            v4, d4 = pac.can_land_here(str(work))
            results.append(('a 403 answers handoff and quotes the server',
                            v4 == 'handoff' and 'denied' in d4.lower(), d4))

            pac._run_git = lambda repo, *a: (
                1, '', 'fatal: unable to access: Could not resolve host: github.com')
            v5, d5 = pac.can_land_here(str(work))
            results.append(('an unreachable host answers unknown, NOT handoff',
                            v5 == 'unknown', f'{v5}: {d5}'))

            # NEGATIVE CONTROL. Same failure, refusal vocabulary removed: the
            # verdict must move off 'handoff'. If this case passes as
            # 'handoff', the classifier is not reading the message at all and
            # case 4 above proves nothing.
            pac._run_git = lambda repo, *a: (1, '', 'fatal: something else entirely')
            v6, d6 = pac.can_land_here(str(work))
            results.append(('a refusal with no refusal words is NOT handoff',
                            v6 != 'handoff', f'{v6}: {d6}'))
        finally:
            pac._run_git = real

        # 6. very_deep_check must be using THIS definition, not a second copy.
        # The probe was moved down into the vendored file precisely so one
        # definition serves both; a re-added local copy would pass every case
        # above while drifting from what adopters actually run.
        import very_deep_check as _vdc
        results.append(('very_deep_check imports the probe rather than copying it',
                        _vdc.can_land_here is pac.can_land_here,
                        repr(getattr(_vdc.can_land_here, '__module__', '?'))))

    failed = [f'{n} [{d}]' for n, ok, d in results if not ok]
    check(f'the access probe separates a refusal from silence '
          f'({len(results)} stated cases, including a negative control that '
          f'flips the verdict)',
          not failed, '; '.join(failed) if failed else '')
