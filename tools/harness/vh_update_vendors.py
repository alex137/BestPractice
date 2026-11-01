# The harness tests for Update Vendors in a consuming repository
#
# tools/harness/vh_update_vendors.py -- part of the verification harness:
# Update Vendors in a consuming repository.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_update_deletes_a_shipped_voice_md():
    """An update deletes a root VOICE.md that is still the shipped template
    (comments aside) and drops its process/manifest.json entry, and asks for
    a conversion only when it carries real edits (2026-10-01: a consumer's
    unchanged VOICE.md became a practice file of `<undecided>` sections, and
    its leftover manifest entry failed practice_audit at staging)."""
    import tempfile
    import precedent_update as pu
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='shipped-voice-'))
    rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                         capture_output=True, text=True).stdout.strip()
    shipped = subprocess.run(['git', '-C', str(ROOT), 'show',
                              '41594ce8:templates/VOICE.md.template'],
                             capture_output=True, text=True).stdout
    try:
        if not shipped:
            cases.append(('this clone has the 2026-08-16 VOICE.md template '
                          '(a shallow clone needs --unshallow)', False, ''))
            raise RuntimeError('no history')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def repo(name, voice):
            r = tmp / name
            (r / 'process').mkdir(parents=True)
            (r / 'VOICE.md').write_text(voice, encoding='utf-8')
            (r / 'process' / 'manifest.json').write_text(json.dumps({'entries': [
                {'practice': 'voice', 'local_path': 'VOICE.md'},
                {'practice': 'other', 'local_path': 'X.md'}]}), encoding='utf-8')
            (r / 'precedent.json').write_text(json.dumps({'sources': [
                {'level': 'repo-local', 'name': 'local', 'path': 'local'}]}),
                encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(r)], env=env)
            subprocess.run(['git', '-C', str(r), 'add', '-A'], env=env)
            subprocess.run(['git', '-C', str(r), 'commit', '-qm', 'i'], env=env)
            return r
        # The install wrote the template without its header comment.
        body = pu._HTML_COMMENT.sub('', shipped).lstrip()
        same = repo('same', body)
        left = pu.legacy_root_docs(same, rev)
        entries = json.loads((same / 'process' / 'manifest.json').read_text())['entries']
        cases.append(('an unchanged VOICE.md is deleted, not left to convert',
                      not (same / 'VOICE.md').exists() and left == [], str(left)))
        cases.append(('...and its manifest entry goes, the rest stay',
                      [e['practice'] for e in entries] == ['other'], str(entries)))
        # 2026-10-17, very deep check's migration rehearsal: the visual
        # identity practice links project-voice.md, so deleting the default
        # without writing the practice an install writes left a dead link.
        voice = same / 'local' / 'practices' / 'project-voice.md'
        tmpl = (ROOT / 'templates' / 'local-practices' /
                'project-voice.md.template').read_text(encoding='utf-8')
        cases.append(('...and local/practices/project-voice.md is written from '
                      'its template, as an install writes it',
                      voice.is_file() and re.fullmatch(
                          re.escape(tmpl).replace(re.escape('<install date>'),
                                                  r'\d{4}-\d\d-\d\d'),
                          voice.read_text(encoding='utf-8')) is not None,
                      str(voice)))
        edited = repo('edited', body.replace('a sharp colleague typing quickly',
                                             'a calm, formal narrator'))
        left = pu.legacy_root_docs(edited, rev)
        cases.append(('an edited VOICE.md is kept and asked to be converted',
                      (edited / 'VOICE.md').exists()
                      and any(o == 'VOICE.md' and 'convert' in w for o, w in left),
                      str(left)))
    except RuntimeError:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an update deletes a shipped, unchanged VOICE.md and asks to convert '
          f'only real edits ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_update_runs_a_set_s_own_tests_after_an_engine_refresh():
    """Update Vendors in a practice set runs the set's own tests when it
    changed the set's engine copy, and stops on a red one before anything
    lands (precedent_update.set_tests_step, 2026-10-20). The ladder set's
    test_ladder_branches.sh first ran on main after an engine refresh
    merged, and was red. A case the set's own tests report not applicable
    there stops it too: five of the ladder's had, unseen, since they moved.
    CONTROLS: a repository that is not a set, and a set whose update
    changed no engine file, run nothing."""
    import tempfile, subprocess as _sp
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)

    class Rep:
        def __init__(self):
            self.steps = []

        def step(self, name, outcome):
            self.steps.append((name, outcome))
    cases = []
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'set'
        tests = repo / 'tools' / 'checks' / 'tests'
        tests.mkdir(parents=True)
        (tests / 'test_ok.sh').write_text('exit 0\n', encoding='utf-8')
        (repo / 'tools' / 'engine.py').write_text('x = 1\n', encoding='utf-8')
        g = lambda *a: _sp.run(['git', '-C', str(repo), *a], env=env,
                               capture_output=True, text=True)
        g('init', '-q')
        g('add', '-A')
        g('commit', '-qm', 'base')
        (repo / 'tools' / 'engine.py').write_text('x = 2\n', encoding='utf-8')
        rep = Rep()
        cases.append(('CONTROL: not a set, nothing runs',
                      pu.set_tests_step(repo, rep) is None and not rep.steps))
        (repo / 'precedent-source.json').write_text('{}', encoding='utf-8')
        rep = Rep()
        cases.append(('a set whose engine copy changed runs its tests, and green passes',
                      pu.set_tests_step(repo, rep) is None
                      and any('all 1 pass' in o for _n, o in rep.steps)))
        (tests / 'test_bad.sh').write_text('echo broke; exit 1\n', encoding='utf-8')
        rep = Rep()
        red = pu.set_tests_step(repo, rep)
        cases.append(('THE DISCRIMINATING CASE: a red set test stops the update, named',
                      bool(red) and 'test_bad.sh' in red and 'broke' in red))
        (tests / 'test_bad.sh').write_text('echo "N/A: zz case -- a file is not here"; exit 0\n',
                                           encoding='utf-8')
        rep = Rep()
        red = pu.set_tests_step(repo, rep)
        cases.append(('2026-10-28: a set test that passes but reports a case not '
                      'applicable, in its own repository, stops the update, named',
                      bool(red) and 'test_bad.sh' in red and 'zz case' in red))
        (tests / 'test_bad.sh').unlink()
        g('checkout', '-q', '--', 'tools/engine.py')
        rep = Rep()
        cases.append(('CONTROL: no engine file changed, nothing runs',
                      pu.set_tests_step(repo, rep) is None and not rep.steps))
    failed = [n for n, ok in cases if not ok]
    check(f'Update Vendors runs a set\'s own tests after an engine refresh '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_clears_the_refresh_branch_session_start_left():
    """Update Vendors, once it has staged the engine, deletes the local
    branches holding nothing but session start's engine refresh, and says
    so (precedent_update.superseded_refresh_step, 2026-11-01).

    Reported from an Update Vendors run over three practice sets: session
    start's precedent_refresh_sources.py committed the refresh on a local
    branch in each set, Update Vendors wrote the same engine again on a
    branch of its own, and every run left the session-start branch orphaned.
    CONTROLS: a branch with "engine-refresh" in its name that also holds a
    real commit is kept; the branch checked out is kept; a second call
    removes nothing and says nothing."""
    import tempfile, subprocess as _sp
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)

    class Rep:
        def __init__(self):
            self.steps = []

        def step(self, name, outcome):
            self.steps.append((name, outcome))
    cases = []
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        origin, repo = pathlib.Path(td) / 'origin.git', pathlib.Path(td) / 'set'
        g = lambda *a: _sp.run(['git', '-C', str(repo), *a], env=env,
                               capture_output=True, text=True)
        _sp.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)],
                env=env, capture_output=True)
        _sp.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env,
                capture_output=True)
        (repo / 'a.txt').write_text('a\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('remote', 'add', 'origin', str(origin)); g('push', '-q', 'origin', 'main')
        refresh = '2026-11-01-x-engine-refresh-a8d0e17c-aaaaa-bbbbb'
        g('checkout', '-qb', refresh)
        (repo / 'engine.py').write_text('e\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'Refresh the vendored engine to BestPractice a8d0e17c598b')
        mixed = '2026-11-01-x-engine-refresh-0000aaaa-ccccc-ddddd'
        g('checkout', '-qb', mixed)
        (repo / 'b.txt').write_text('b\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'A real change')
        g('checkout', '-q', 'main')
        rep = Rep()
        removed = pu.superseded_refresh_step(repo, rep)
        heads = g('for-each-ref', '--format=%(refname:short)', 'refs/heads').stdout.split()
        cases.append(('THE DISCRIMINATING CASE: the refresh-only branch is gone',
                      refresh not in heads and removed == [refresh]))
        cases.append(('...and the run says which', any(
            n == 'superseded refresh' and refresh in o for n, o in rep.steps)))
        cases.append(('CONTROL: a refresh-named branch with a real commit is kept',
                      mixed in heads))
        rep = Rep()
        cases.append(('CONTROL: a second call removes nothing and says nothing',
                      pu.superseded_refresh_step(repo, rep) == [] and not rep.steps))
        g('checkout', '-qb', refresh)
        (repo / 'engine.py').write_text('f\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'Refresh the vendored engine to BestPractice a8d0e17c598b')
        rep = Rep()
        cases.append(('CONTROL: the branch checked out is kept',
                      pu.superseded_refresh_step(repo, rep) == []
                      and refresh in g('for-each-ref', '--format=%(refname:short)',
                                       'refs/heads').stdout.split()))
    failed = [n for n, ok in cases if not ok]
    check(f'Update Vendors clears the refresh branch session start left '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_drops_the_dead_blank_blocklist_link():
    """Update Vendors drops the retired install pack's dead link to
    personal/README.md#blank-blocklist from a repository's process/ files,
    keeping the sentence, exactly as a consumer fixed its own by hand
    (2026-10-06). The same text with no link, and the link in a file
    outside process/, are left alone."""
    import tempfile as _tf
    import precedent_update as pu
    line = ("# Left blank at install ([`blank-blocklist`](personal/README.md"
            "#blank-blocklist)): Morgan doesn't use the\n")
    cases = []
    with _tf.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'process').mkdir()
        f = repo / 'process' / 'scrub_blocklist.txt'
        f.write_text('# head\n' + line + 'word\n', encoding='utf-8')
        other = repo / 'README.md'
        other.write_text(line, encoding='utf-8')
        fixed = pu.drop_dead_blank_blocklist_link(repo)
        cases.append(('the link is dropped and the sentence kept',
                      fixed == ['process/scrub_blocklist.txt'] and
                      f.read_text(encoding='utf-8') ==
                      "# head\n# Left blank at install: Morgan doesn't use the\nword\n"))
        cases.append(('a second run changes nothing',
                      pu.drop_dead_blank_blocklist_link(repo) == []))
        cases.append(('a file outside process/ is not touched',
                      other.read_text(encoding='utf-8') == line))
    failed = [n for n, ok in cases if not ok]
    check(f'Update Vendors drops the dead blank-blocklist link ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_update_seeds_the_session_load_registry():
    """Update Vendors gives a repository with no
    tools/session_load_budgets.json one seeded at today's sizes, so the
    session-load-budget check binds there instead of skipping on every run
    (Alex, 2026-10-04: "If it is already a best practice, why didn't we
    adopt?" -- a consumer's instructions file had grown to about 38,000
    tokens behind a skip). Both directions: an existing registry, however
    small, is never touched, and a second run writes nothing. A registry it
    seeds carries baseline approvals; one that existed without them is named
    in the report, never filled in (2026-10-06)."""
    import tempfile
    import precedent_update as pu
    name = 'Update Vendors seeds a missing session-load registry'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'CLAUDE.md').write_text('word ' * 4000, encoding='utf-8')
        (repo / 'AGENTS.md').write_text('word ' * 300, encoding='utf-8')
        seeded = pu.ensure_session_load_registry(repo)
        reg = json.loads((repo / 'tools' / 'session_load_budgets.json')
                         .read_text(encoding='utf-8'))
        s = reg.get('surfaces', {})
        cases.append(('both surfaces are declared, each ceiling at or above '
                      'what it measures', set(s) == {'CLAUDE.md', 'AGENTS.md'}
                      and all(s[k]['ceiling'] >= (seeded[k] or 0) for k in s)))
        cases.append(('the early-warning floor is on', reg.get('headroom_floor_pct') == 5))
        cases.append(('it says it was seeded at Update Vendors',
                      'Update Vendors' in s['CLAUDE.md'].get('_note', '')))
        ap = reg.get('approved_budgets') or {}
        cases.append(('a registry it seeds carries a baseline approval for every '
                      'budget, so budget-within-approval binds from the start '
                      '(2026-10-06)', bool(ap) and all(
                          e.get('strength') == 'baseline' and isinstance(e.get('max'), int)
                          and 'Update Vendors' in e.get('approved_by', '')
                          for e in ap.values())))
        cases.append(('...and the report then names no approval gap',
                      pu.approval_gap(repo) is None))
        cases.append(('...each at the number in force in THIS repo, never the '
                      'engine clone\'s own (2026-10-06: a consumer was seeded '
                      'with BestPractice\'s numbers, and its first check refused '
                      'all of them as unapproved raises)',
                      (ap.get('surfaces/CLAUDE.md') or {}).get('max')
                      == s['CLAUDE.md']['ceiling']))
        before = (repo / 'tools' / 'session_load_budgets.json').read_bytes()
        again = pu.ensure_session_load_registry(repo)
        cases.append(('a second run writes nothing', again is None and before ==
                      (repo / 'tools' / 'session_load_budgets.json').read_bytes()))
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'tools').mkdir()
        mine = '{"surfaces": {"CLAUDE.md": {"ceiling": 10}}}\n'
        (repo / 'tools' / 'session_load_budgets.json').write_text(mine, encoding='utf-8')
        (repo / 'CLAUDE.md').write_text('word ' * 4000, encoding='utf-8')
        cases.append(('an existing registry is never touched, even one over its ceiling',
                      pu.ensure_session_load_registry(repo) is None and
                      (repo / 'tools' / 'session_load_budgets.json').read_text(
                          encoding='utf-8') == mine))
        gap = pu.approval_gap(repo) or ''
        cases.append(('an existing registry with no approved_budgets is named in '
                      'the report, never filled in (a hand-made raise would be '
                      'recorded as approved)', 'no approved_budgets' in gap
                      and 'baseline' in gap and (repo / 'tools' /
                      'session_load_budgets.json').read_text(encoding='utf-8') == mine))
    # Morgan, 2026-10-10: "How do we AVOID this becoming a constant hassle
    # that the user has to think about all the time?" With history to read,
    # a registry no budget of which went up since its first commit is
    # recorded as the baseline without asking; one that went up is named,
    # and only the raised budget is asked about.
    def committed(ceiling_then, ceiling_now):
        td = tempfile.mkdtemp(prefix='budget-history-')
        repo = pathlib.Path(td)
        env = _fixture_git_env()
        subprocess.run(['git', 'init', '-q', str(repo)], env=env, capture_output=True)
        (repo / 'tools').mkdir()
        reg = repo / 'tools' / 'session_load_budgets.json'
        reg.write_text('{"surfaces": {"CLAUDE.md": {"ceiling": %d}}}\n'
                       % ceiling_then, encoding='utf-8')
        (repo / 'CLAUDE.md').write_text('word\n', encoding='utf-8')
        subprocess.run(['git', '-C', td, 'add', '-A'], env=env, capture_output=True)
        subprocess.run(['git', '-C', td, 'commit', '-qm', 'seed'], env=env,
                       capture_output=True)
        if ceiling_now != ceiling_then:
            reg.write_text('{"surfaces": {"CLAUDE.md": {"ceiling": %d}}}\n'
                           % ceiling_now, encoding='utf-8')
            subprocess.run(['git', '-C', td, 'commit', '-qam', 'raise'],
                           env=env, capture_output=True)
        return repo, reg
    repo, reg = committed(100, 80)
    note = pu.approval_gap(repo) or ''
    ap = json.loads(reg.read_text(encoding='utf-8')).get('approved_budgets') or {}
    cases.append(('THE DISCRIMINATING CASE: a registry whose budgets only went '
                  'down since its first commit is recorded as the baseline, '
                  'with no question for the person',
                  'recorded the budgets in force' in note
                  and 'Ask the person' not in note
                  and (ap.get('surfaces/CLAUDE.md') or {}).get('max') == 80
                  and 'first committed' in (ap.get('surfaces/CLAUDE.md') or {})
                  .get('approved_by', '')))
    shutil.rmtree(repo, ignore_errors=True)
    repo, reg = committed(100, 150)
    note = pu.approval_gap(repo) or ''
    cases.append(('a registry with a budget raised since its first commit is '
                  'never filled in, and the raised budget is named',
                  'Ask the person' in note and 'surfaces/CLAUDE.md' in note
                  and 'approved_budgets' not in reg.read_text(encoding='utf-8')))
    shutil.rmtree(repo, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_stale_freshness_also_says_delete_it():
    """PRECEDENT_FRESHNESS_ALSO, not needed since 2026-09-30, is told to be
    deleted rather than given a new value when every entry names a practice
    set or a retired precedent-team-* path, and Update Vendors' rename step
    says so too (reported 2026-10-03: the session check warned at every turn
    about the old team paths and offered a corrected value). An entry naming
    a repository nothing declares still keeps the variable worth having."""
    import tempfile
    name = 'a stale PRECEDENT_FRESHNESS_ALSO is told to be deleted'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_session_check as psc
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    saved = os.environ.get('PRECEDENT_FRESHNESS_ALSO')

    def row(value):
        os.environ['PRECEDENT_FRESHNESS_ALSO'] = value
        # offline: the row under test is local; only the fetch row is dropped.
        return [r for r in psc.checks(offline=True)
                if r[0].startswith('PRECEDENT_FRESHNESS_ALSO')][0]
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            pset = tmp / 'precedent-shared-fixture'
            pset.mkdir()
            (pset / 'precedent-source.json').write_text('{}', encoding='utf-8')
            other = tmp / 'some-project'
            (other / '.git').mkdir(parents=True)
            r = row(f'{tmp}/precedent-team-fixture=main;{pset}=main')
            cases.append(('old team paths plus a practice set: warned, and told to '
                          'delete the variable, never given a new value',
                          r[1] is False and 'Delete PRECEDENT_FRESHNESS_ALSO' in r[2]
                          and 'do not replace it' in r[2] and 'Set it to' not in r[2]))
            r = row(f'{pset}=main')
            cases.append(('only practice sets: not a warning, but said to be unneeded',
                          r[1] is True and 'not needed' in r[2]))
            r = row(f'{other}=main')
            cases.append(('a repository nothing declares keeps the variable worth '
                          'having', r[1] is True and 'Delete' not in r[2]))
            os.environ['PRECEDENT_FRESHNESS_ALSO'] = f'{tmp}/precedent-team-fixture=main'
            rep = pu.Report()
            pu.renamed_sources_step(tmp, rep, '')
            cases.append(('Update Vendors\' rename step notes the stale variable, to '
                          'delete, without holding up the update',
                          any(n == 'environment' and 'delete it' in o for n, o in rep.steps)
                          and not rep.left))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_FRESHNESS_ALSO', None)
        else:
            os.environ['PRECEDENT_FRESHNESS_ALSO'] = saved
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_vendors_retires_the_team_level_word():
    """Update Vendors rewrites `"level": "team"` to `"shared"` in a
    consumer's precedent.json on every run that finds one -- any source, not
    only a renamed set -- says so in one line, keeps every other byte, and
    does nothing the second time. A previously raw reader (the session
    check's sources-resolved row) also judges a `team`-level set as shared."""
    import tempfile, io, contextlib
    pu, pve, pr = _update_tools()
    step = getattr(pu, 'level_alias_step', None)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-team-level-'))
    try:
        repo = tmp / 'consumer'
        repo.mkdir()
        text = ('{\n  "_comment": ["kept as written"],\n  "sources": [\n'
                '    {"level": "universal", "name": "precedent", "path": "../BestPractice"},\n'
                '    {"level":"team", "name": "writing",\n'
                '     "path": "../writing"},\n'
                '    {"level": "shared", "name": "ladder", "path": "../ladder"},\n'
                '    {"level": "team", "name": "style", "path": "../style"}\n'
                '  ],\n  "note": "a team of two"\n}\n')
        (repo / 'precedent.json').write_text(text, encoding='utf-8')
        if step is None:
            cases.append(('precedent_update has level_alias_step()', False))
        else:
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep)
            after = (repo / 'precedent.json').read_text(encoding='utf-8')
            levels = {s['name']: s['level'] for s in json.loads(after)['sources']}
            cases.append(('both team-level sources now say shared',
                          levels == {'precedent': 'universal', 'writing': 'shared',
                                     'ladder': 'shared', 'style': 'shared'}, levels))
            cases.append(('every other byte is kept',
                          after == text.replace('"level":"team"', '"level":"shared"')
                          .replace('"level": "team"', '"level": "shared"')))
            lines = [o for _n, o in rep.steps if 'writing' in o]
            cases.append(('the report says so in one line, naming both',
                          len(lines) == 1 and 'style' in lines[0], rep.steps))
            rep2 = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep2)
            cases.append(('a second run changes nothing and says nothing',
                          (repo / 'precedent.json').read_text(encoding='utf-8') == after
                          and not rep2.steps, rep2.steps))
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import precedent_source_credentials as _psc
            import precedent_session_check as _sc
        finally:
            sys.path.pop(0)
        old = tmp / 'old'
        old.mkdir()
        (old / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'team', 'name': 'absent-set', 'path': '../absent-set'}]}),
            encoding='utf-8')
        env = {'HOME': str(tmp), 'PRECEDENT_USER_CONFIG': str(tmp / 'none.json')}
        un = [u for u in _psc.unresolved_private_sources(old, env) if u[1] == 'absent-set']
        cases.append(('a team-level set that is not on disk is reported unresolved, as shared',
                      [u[0] for u in un] == ['shared'], un))
        row = _sc.sources_resolved_row('set', 'msg', un)
        cases.append(('...and fails the sources-resolved row, token or no token',
                      row[1] is False, row))
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f' ({c[2]})' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'Update Vendors retires the `team` level word ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_dropped_set_and_proxy_and_template_refs():
    """Three findings from a consuming repository's two Update Vendors runs
    (2026-10-07). (1) Dropping a retired set lists the hand-written lines
    that still name it or count the sets -- a precedent.json comment, the
    instructions file -- and never a generated block or view. (2) The
    session proxy's refusal of GitHub's API is one plain line, not a
    warning naming every set, and GitHub's own Not Found still never drops
    a set. (3) A shipped template cites only practices universal carries:
    one pointed at go-update after it moved to the ladder set."""
    import tempfile
    import inspect
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as _pu
    import precedent_vendor_engine as _pve
    import github_budget as _gb
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / 'precedent.json').write_text(
            '{\n  "_comment": "Three team sets resolve beside this repo.",\n'
            '  "sources": [{"level": "shared", "name": "precedent-shared-live", '
            '"path": "../x"}]\n}\n', encoding='utf-8')
        (d / 'AGENTS.md').write_text(
            '# Repo\n\nA session that finds only four of five sources '
            'resolving stops.\nUse precedent-shared-old for craft.\nTwo check '
            'levels exist.\n<!-- BEGIN GENERATED: x -->\nprecedent-shared-old '
            'here\n<!-- END GENERATED -->\n'
            # 2026-10-10, a consumer: evidence, not practice sets.
            'Nobody states them up front; two sources reveal them:\n',
            encoding='utf-8')
        (d / 'MAP.md').write_text('<!-- GENERATED by build_views -->\n'
                                  'precedent-shared-old and three sets\n',
                                  encoding='utf-8')
        got = _pu.prose_about_dropped_sets(d, ['precedent-shared-old'])
        where = [w for w, _t, _y in got]
        cases.append(('a precedent.json comment counting the sets is listed',
                      'precedent.json:2' in where))
        cases.append(('an instructions line counting the sources is listed',
                      'AGENTS.md:3' in where))
        cases.append(('an instructions line naming the dropped set is listed',
                      'AGENTS.md:4' in where))
        cases.append(('a line counting something else is not',
                      'AGENTS.md:5' not in where))
        cases.append(('"two sources" about something other than practice '
                      'sets is not', 'AGENTS.md:9' not in where))
        cases.append(('a generated block and a generated view are left to '
                      'the sync', not any(w.startswith('MAP.md') or w == 'AGENTS.md:7'
                                          for w in where)))
        cases.append(('nothing is listed when nothing was dropped',
                      _pu.prose_about_dropped_sets(d, []) == []))
    cases.append(('the proxy\'s refusal is recognised',
                  _gb.is_proxy_refusal('not JSON: Access to this GitHub API '
                                       'path is not permitted through this proxy')))
    cases.append(('GitHub\'s Not Found is not the proxy',
                  not _gb.is_proxy_refusal('Not Found')))
    real = _pve.archived_declared_sources
    try:
        notes = [f'a: {_pve.PROXY_NOTE}', f'b: {_pve.PROXY_NOTE}']
        _pve.archived_declared_sources = lambda _r: (set(), list(notes))

        class Rep:
            def __init__(self):
                self.steps, self.left = [], []

            def step(self, n, o):
                self.steps.append(o)

            def leave(self, w, y):
                self.left.append((w, y))
        rep = Rep()
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / 'precedent.json').write_text(
                '{"sources": []}', encoding='utf-8')
            _pu.retired_sources_step(pathlib.Path(tmp), rep)
            # Changed 2026-10-12, a consuming repository's Update Vendors: a
            # line on every run about something no one can act on is said by
            # drop-retired, which is asked, and not by Update Vendors.
            cases.append(('proxied sets say nothing on Update Vendors',
                          rep.steps == [] and rep.left == []))
            notes[:] = [f'a: whether it is archived could not be read here '
                        f'({_pve.NO_ACCESS_NOTE}); left declared']
            rep = Rep()
            _pu.retired_sources_step(pathlib.Path(tmp), rep)
            cases.append(('...nor does a set this session has no API access to',
                          rep.steps == [] and rep.left == []))
            notes[:] = ['a: whether it is archived could not be read here '
                        '(curl exited 6); left declared']
            rep = Rep()
            _pu.retired_sources_step(pathlib.Path(tmp), rep)
            cases.append(('CONTROL: any other failure is still said, in one line',
                          len(rep.steps) == 1 and 'curl exited 6' in rep.steps[0]))
    finally:
        _pve.archived_declared_sources = real
    cases.append(('Not Found still never drops a set',
                  'Not Found' in inspect.getsource(_pve.archived_declared_sources)))
    cited = set()
    for f in (ROOT / 'templates').rglob('*'):
        if f.is_file():
            try:
                cited |= {(f.relative_to(ROOT).as_posix(), m) for m in re.findall(
                    r'practices? `([a-z0-9-]+)`', f.read_text(encoding='utf-8'))}
            except (UnicodeDecodeError, OSError):
                pass
    missing = sorted(f'{f} cites {s}' for f, s in cited
                     if not (ROOT / 'practices' / f'{s}.md').is_file()
                     or not re.search(r'^status:\s*active', (ROOT / 'practices' / f'{s}.md')
                                      .read_text(encoding='utf-8'), re.M))
    cases.append(('every practice a shipped template cites is one universal '
                  'carries in force' + (f' ({"; ".join(missing[:5])})' if missing else ''),
                  not missing))
    bad = [n for n, ok in cases if not ok]
    check(f'a dropped set\'s prose is listed, the proxy says so once, templates '
          f'cite only what universal carries ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_dropped_set_prose_successors_and_families():
    """Three gaps in Update Vendors' dropped-set step, from a consuming
    repository's update (2026-10-08). (1) A loader marker quoted in a
    sentence hid every line after it from the prose scan: generated text is
    what generated_blocks.py says it is, closing marker required. (2) A
    dropped set's successor -- a deletion record's `successors` or the set's
    own `retired` marker's `folded_into`, one reader for both -- is asked
    about when the repository neither declares it nor gets it from the
    person's own set, and the question says declaring covers everyone and
    bringing covers only the person. (3) Every string in precedent.json is
    read, a kept_template_divergences reason included, and a set is found by
    its family wildcard, its pre-rename name, a count of sets, and -- once no
    shared set is left -- by "the shared sources"."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as _pu
    import precedent_vendor_engine as _pve
    import precedent_resolve as _pr
    cases = []
    gone_names = ['precedent-shared-old', 'precedent-shared-older']
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': 'u'}],
            '_comment': ['See precedent-team-old for the history.'],
            'kept_template_divergences': {
                'AGENTS.md ### Session start': {
                    'reason': 'Attach the shared sources first, then bootstrap.'},
                'AGENTS.md ## Practice sources': {
                    'reason': 'Describes the universal copy and the two '
                              'precedent-shared-* sets beside it.'},
                'AGENTS.md ## Conventions': {'reason': 'Condensed on purpose.'}}},
            indent=2), encoding='utf-8')
        (d / 'AGENTS.md').write_text(
            '# Repo\n\nFor the `<!-- BEGIN GENERATED: precedent-loader -->` '
            'block, re-run the sync.\nThe sets are '
            '(`precedent-shared-old`, `precedent-shared-older`).\n'
            '<!-- BEGIN GENERATED: precedent-loader -->\nprecedent-shared-old\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        got = _pu.prose_about_dropped_sets(d, gone_names)
        where = {w: y for w, _t, y in got}
        cases.append(('(1) a set named after a marker quoted in prose is found',
                      'AGENTS.md:4' in where, sorted(where)))
        cases.append(('(1) ...and a real generated block is still skipped',
                      'AGENTS.md:6' not in where, sorted(where)))
        lines = (d / 'precedent.json').read_text(encoding='utf-8').splitlines()

        def line_of(s):
            return f'precedent.json:{next(i for i, x in enumerate(lines, 1) if s in x)}'
        cases.append(('(3) a kept_template_divergences reason naming the set '
                      'family is listed', line_of('precedent-shared-* sets') in where,
                      sorted(where)))
        cases.append(('(3) "the shared sources" is listed once none is declared',
                      line_of('Attach the shared sources') in where, sorted(where)))
        cases.append(('(3) a set\'s pre-rename name is listed',
                      line_of('precedent-team-old') in where, sorted(where)))
        cases.append(('(3) a reason about something else is not',
                      line_of('Condensed on purpose') not in where, sorted(where)))
        cases.append(('(3) nothing is ever edited',
                      'precedent-shared-* sets' in
                      (d / 'precedent.json').read_text(encoding='utf-8')))
        (d / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'precedent-shared-live', 'path': 'x'}],
            'note': 'Attach the shared sources first.'}), encoding='utf-8')
        cases.append(('(3) "the shared sources" is not listed while one is '
                      'still declared',
                      not [w for w, _t, _y in _pu.prose_about_dropped_sets(d, gone_names)
                           if w.startswith('precedent.json')]))

    # (2) Successors.
    cases.append(('(2) successors and folded_into read as one, universal left out',
                  _pr.successors_of({'successors': ['a-b'], 'folded_into':
                                     ['universal', 'a-b', 'c']}) == ['a-b', 'c']))
    real = json.loads(_pr.ENGINE_DELETED_SETS.read_text(encoding='utf-8'))
    cases.append(("(2) BestPractice's record names a successor for each "
                  'deleted set', all(_pr.successors_of(e) for e in real['sets'])))
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / 'repo').mkdir()
        (d / 'folded').mkdir()
        (d / 'folded' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'folded', 'retired': {'date': '2026-10-06',
                                           'folded_into': ['universal', 'heir']}}),
            encoding='utf-8')
        (d / 'repo' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'u'}]}),
            encoding='utf-8')
        dropped = [('folded', '../folded', 'it says it is retired'),
                   ('vanished', '../vanished', _pve.DELETED_WHY)]
        gone = {'vanished': {'successors': ['other-heir']}}
        nobody = (gone, [])
        got = _pve.undeclared_successors(d / 'repo', dropped, person=nobody)
        cases.append(("(2) a `retired` marker's folded_into and a deletion "
                      "record's successors are both asked about",
                      sorted((s, b) for s, _f, b in got)
                      == [('heir', False), ('other-heir', False)], got))
        mine = (gone, [d / 'heir'])
        got = _pve.undeclared_successors(d / 'repo', dropped, person=mine)
        cases.append(("(2) a successor the person's own set brings is marked so",
                      ('heir', ['folded'], True) in got, got))
        (d / 'repo' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'heir', 'path': '../heir'},
            {'level': 'shared', 'name': 'other-heir', 'path': '../oh'}]}),
            encoding='utf-8')
        cases.append(('(2) a declared successor is not asked about',
                      _pve.undeclared_successors(d / 'repo', dropped,
                                                 person=nobody) == []))
        # The step leaves the question, worded for a repository with others.
        (d / 'repo' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'u'}]}),
            encoding='utf-8')
        saved = (_pve.archived_declared_sources, _pve.drop_retired_sources,
                 _pve.undeclared_successors)

        class Rep:
            def __init__(self):
                self.steps, self.left = [], []

            def step(self, n, o):
                self.steps.append(o)

            def leave(self, w, y):
                self.left.append((w, y))
        try:
            _pve.archived_declared_sources = lambda _r: (set(), [])
            _pve.drop_retired_sources = lambda _r, _a: (dropped[:1], [])
            _pve.undeclared_successors = (
                lambda r, dr, person=None: saved[2](r, dr, person=nobody))
            rep = Rep()
            _pu.retired_sources_step(d / 'repo', rep)
        finally:
            (_pve.archived_declared_sources, _pve.drop_retired_sources,
             _pve.undeclared_successors) = saved
        asked = [y for w, y in rep.left if 'heir' in w]
        cases.append(('(2) Update Vendors leaves the question for the person',
                      len(asked) == 1, rep.left))
        cases.append(('(2) ...saying declaring covers everyone, bringing only you',
                      bool(asked) and 'everyone who works in this repository'
                      in asked[0] and 'covers only you' in asked[0], asked))
    bad = [c[0] + (f' ({c[2]})' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a dropped set\'s prose is found past a quoted marker and by its '
          f'family, and its successor is asked about ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_update_commit_note_leaves_out_the_vendored_catalogue():
    """Update Vendors' "name each of these in the commit message" list
    leaves out the section 0 catalogue at precedent.json's universal path,
    exactly as it leaves out tools/.

    Found 2026-10-31 by the very deep check's pass 1 update rehearsal: a
    consumer installed at a two-week-old commit and brought forward got
    every changed upstream practice listed one by one as a file "rewritten
    outside the vendored trees" -- VENDORED_PREFIXES knew only tools/ and
    the retired process/upstream/.

    Negative control, measured 2026-10-31: on the code before the fix the
    first case fails (the list holds precedent/universal/practices/a.md and
    precedent/universal/close_detect.json).
    """
    import tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-commit-note-'))
    genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp)], check=True)
        (tmp / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'}]}),
            encoding='utf-8')
        for rel in ('precedent/universal/practices/a.md',
                    'precedent/universal/close_detect.json',
                    'tools/x.py', 'practices/a.md', 'AGENTS.md'):
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text('x\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], check=True, env=genv)
        got = pu.rewritten_outside_vendored(tmp)
        cases.append(('the vendored catalogue is not listed as rewritten outside '
                      'the vendored trees',
                      not any('precedent/universal' in x for x in got), str(got)))
        cases.append(('a root file outside them still is, and practices/ is one line',
                      'A AGENTS.md' in got and 'tools/x.py' not in ' '.join(got)
                      and any(x.startswith('practices/ (1 practice file') for x in got),
                      str(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f"Update Vendors' commit note leaves out the vendored catalogue "
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_one_way_to_fetch_a_missing_commit():
    """precedent_local_edits.fetch_commit is the engine's one way to fetch a
    commit a clone lacks (2026-10-29); checkin.fetch_recorded_commit and
    precedent_update.range_readable go through it. Until then they were
    three implementations, and checkin's ran `--depth=1000` even in a full
    clone, which writes .git/shallow and turns that clone shallow."""
    import tempfile
    import precedent_local_edits as le
    import precedent_update as pu
    cases = []
    def git(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env={**os.environ, 'GIT_AUTHOR_NAME': 'f',
                              'GIT_AUTHOR_EMAIL': 'f@x', 'GIT_COMMITTER_NAME': 'f',
                              'GIT_COMMITTER_EMAIL': 'f@x'})
    with tempfile.TemporaryDirectory() as td:
        up = pathlib.Path(td) / 'up'
        git(td, 'init', '-q', '-b', 'main', str(up))
        for i in range(6):
            (up / 'f.txt').write_text(f'{i}\n')
            git(up, 'add', '-A')
            git(up, 'commit', '-q', '-m', f'c{i}')
        old = git(up, 'rev-parse', 'HEAD~4').stdout.strip()
        tip = git(up, 'rev-parse', 'HEAD').stdout.strip()
        # An old commit off main, as a force-pushed branch leaves one.
        git(up, 'checkout', '-q', '-b', 'side', old)
        (up / 'g.txt').write_text('side\n')
        git(up, 'add', '-A')
        git(up, 'commit', '-q', '-m', 'side')
        side = git(up, 'rev-parse', 'HEAD').stdout.strip()
        git(up, 'checkout', '-q', 'main')
        git(up, 'config', 'uploadpack.allowAnySHA1InWant', 'true')
        def shallow(c):
            return git(c, 'rev-parse', '--is-shallow-repository').stdout.strip() == 'true'

        full = pathlib.Path(td) / 'full'
        git(td, 'clone', '-q', '--single-branch', '--branch', 'main', str(up), str(full))
        # A bound shorter than the fixture's history, so a --depth fetch
        # into this full clone would visibly turn it shallow.
        saved_depth, le.FETCH_DEPTH = le.FETCH_DEPTH, 2
        try:
            got = le.fetch_commit(full, side, branch='main')
        finally:
            le.FETCH_DEPTH = saved_depth
        cases.append(('a full clone gets a commit off its branch by name',
                      got, str(got)))
        cases.append(('...and is still a full clone afterwards', not shallow(full),
                      'it turned shallow'))

        thin = pathlib.Path(td) / 'thin'
        git(td, 'clone', '-q', '--depth', '1', f'file://{up}', str(thin))
        cases.append(('the fixture clone starts without the old commit',
                      git(thin, 'cat-file', '-e', f'{old}^{{commit}}').returncode != 0, ''))
        got = le.fetch_commit(thin, old, branch='main')
        cases.append(('a depth-1 clone gets an old commit of its branch back', got, str(got)))

        thin2 = pathlib.Path(td) / 'thin2'
        git(td, 'clone', '-q', '--depth', '1', f'file://{up}', str(thin2))
        ok, why = pu.range_readable(thin2, old, tip)
        cases.append(('range_readable reads a range a depth-1 clone lacked', ok, why))
        ok, why = pu.range_readable(thin2, side, tip)
        cases.append(('...and says no for a commit that is not an ancestor',
                      not ok and 'not hold' in why, why))
        cases.append(('a missing commit with nowhere to fetch it from is False',
                      not le.fetch_commit(thin2, '0' * 40), ''))
    bad = [f'{c[0]}: {c[2]}' for c in cases if not c[1]]
    check(f'one way to fetch a commit a clone lacks ({len(cases)} stated cases)',
          not bad, '; '.join(bad))

def check_update_runs_code_at_least_as_new_as_it_applies():
    """Update Vendors runs code no older than the commit it applies
    (tools/precedent_update_driver.py; the plan and every case below are
    todo/todo-2026-10-11-update-vendors-runs-stale-driver-code.md's).

    The fixture is the incident: a BestPractice clone one commit behind
    origin/main, whose own update() is broken where the fetched commit's is
    not. The run must use the fetched code, say which commit ran, and leave
    the clone exactly as it was. Every case runs the FIXTURE's
    tools/precedent_update.py, never this repo's: SOURCE is whatever tree
    the script sits in, so running ROOT's copy would test nothing.

    The commits, on main: BOOT (this change, from the working tree) ->
    OLD (a break at the top of update()) -> NEW (the break replaced by a
    probe), NEW carrying a passed marker. Off them: AHEAD on NEW, SIDE on
    BOOT, LATE on NEW, with no marker.

    Owns its state (practice: fixture-owns-its-state): HOME, the user
    config and the global git config are the fixture's, and the harness-
    wide opt-out is cleared for every case that tests the rule.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-driver-'))
    cases = []
    hooks_marker = tmp / 'global-hook-fired'
    gcfg = tmp / 'gitconfig'
    gcfg.write_text('', encoding='utf-8')
    env = {**os.environ, 'HOME': str(tmp / 'home'),
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json'),
           'GIT_CONFIG_GLOBAL': str(gcfg), 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
    env.pop('PRECEDENT_UPDATE_RUN_IN_PLACE', None)
    env.pop('PRECEDENT_UPDATE_DRIVER', None)
    (tmp / 'home').mkdir()

    def sh(*argv, cwd, extra=None):
        r = subprocess.run(list(argv), cwd=str(cwd), env={**env, **(extra or {})},
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def git(cwd, *a):
        rc, out = sh('git', *a, cwd=cwd)
        if rc != 0:
            raise FixtureSetupError(f"git {' '.join(a)} (in {cwd}): {out.strip()[-200:]}")
        return out.strip()

    def commit_edit(work, msg, old, new):
        p = work / 'tools' / 'precedent_update.py'
        s = p.read_text(encoding='utf-8')
        if s.count(old) != 1:
            raise FixtureSetupError(f'{msg}: anchor not found once in update()')
        p.write_text(s.replace(old, new), encoding='utf-8')
        git(work, 'commit', '-qam', msg)
        return git(work, 'rev-parse', 'HEAD')

    anchor = "    rep = Report()\n    rep.pin_repo = repo\n"
    probe = ("    print('CHILD GUARD', subprocess.run([sys.executable, '-c', "
             "'import os; print(os.environ.get(\"PRECEDENT_UPDATE_DRIVER\"))'], "
             "capture_output=True, text=True).stdout.strip())\n")
    try:
        work = tmp / 'work'
        git(tmp, 'clone', '-q', '--shared', str(ROOT), str(work))
        git(work, 'checkout', '-q', '-B', 'main', _ref_including_worktree(ROOT))
        boot = git(work, 'rev-parse', 'HEAD')
        old = commit_edit(work, 'old', anchor,
                          "    print('STALE DRIVER RAN'); return 2\n" + anchor)
        new = commit_edit(work, 'new', "    print('STALE DRIVER RAN'); return 2\n",
                          probe)
        git(work, 'checkout', '-q', '-b', 'ahead')
        ahead = commit_edit(work, 'ahead', probe, probe + "    pass\n")
        git(work, 'checkout', '-q', '-b', 'side', boot)
        side = commit_edit(work, 'side', anchor, "    pass\n" + anchor)
        git(work, 'checkout', '-q', '-b', 'late', new)
        late = commit_edit(work, 'late', probe, probe + "    pass  # late\n")
        origin = tmp / 'origin.git'
        git(tmp, 'clone', '-q', '--bare', str(work), str(origin))
        git(origin, 'update-ref', 'refs/heads/main', new)
        git(origin, 'update-ref', 'refs/heads/staging', new)
        marker = f"refs/precedent/passed/{git(work, 'rev-parse', new + '^{tree}')}"
        git(origin, 'update-ref', marker, new)

        def clone(name, at):
            c = tmp / name
            git(tmp, 'clone', '-q', str(origin), str(c))
            git(c, 'checkout', '-q', '-B', 'main', at)
            git(c, 'branch', '-q', '-u', 'origin/main')
            return c

        def consumer(name, upstream=None):
            r = tmp / name
            r.mkdir()
            git(r, 'init', '-q', '-b', 'main')
            if upstream:
                (r / 'precedent.json').write_text(json.dumps(
                    {'upstream_branch': upstream}) + '\n', encoding='utf-8')
            return r

        def update(c, repo, *extra, only=False, more=None):
            add = dict(more or {})
            if only:
                add['PRECEDENT_UPDATE_BOOTSTRAP_ONLY'] = '1'
            return sh(sys.executable, str(c / 'tools' / 'precedent_update.py'),
                      '--repo', str(repo), *extra, cwd=repo, extra=add)

        def verdict(out):
            return {l.split(': ', 2)[1]: l.split(': ', 2)[2]
                    for l in out.splitlines()
                    if l.startswith('precedent_update_driver: ') and l.count(': ') >= 2}

        def state(c):
            return (git(c, 'rev-parse', 'HEAD'), git(c, 'branch', '--show-current'),
                    git(c, 'rev-parse', ':tools/precedent_update.py'),
                    git(c, 'status', '--porcelain'), git(c, 'worktree', 'list'))

        # ---- the incident, end to end ----
        behind = clone('behind', old)
        repo = consumer('consumer')
        hooks = tmp / 'hooks'
        hooks.mkdir()
        hook = hooks / 'post-checkout'
        hook.write_text(f'#!/bin/sh\ntouch {hooks_marker}\n', encoding='utf-8')
        hook.chmod(0o755)
        own_marker = tmp / 'own-hook-fired'
        own = behind / '.git' / 'hooks' / 'post-checkout'
        own.write_text(f'#!/bin/sh\ntouch {own_marker}\n', encoding='utf-8')
        own.chmod(0o755)
        gcfg.write_text(f'[core]\n\thooksPath = {hooks}\n', encoding='utf-8')
        # The hooks can fire: without the driver's empty hooks directory, a
        # worktree add runs the global one (the negative control).
        probe_tree = tmp / 'probe-tree'
        sh('git', 'worktree', 'add', '-q', '--detach', str(probe_tree), new, cwd=behind)
        hooks_can_fire = hooks_marker.exists()
        sh('git', 'worktree', 'remove', '--force', str(probe_tree), cwd=behind)
        hooks_marker.unlink(missing_ok=True)
        cases.append(('the hook control fires without the driver (so the case can fail)',
                      hooks_can_fire, ''))

        # A git shim first on PATH logs every call during the run.
        shim_dir, log = tmp / 'shim', tmp / 'git-calls.log'
        shim_dir.mkdir()
        real_git = shutil.which('git')
        (shim_dir / 'git').write_text(
            f'#!/bin/sh\nprintf "%s\\t%s\\n" "$PWD" "$*" >> {log}\n'
            f'exec {real_git} "$@"\n', encoding='utf-8')
        (shim_dir / 'git').chmod(0o755)
        before = state(behind)
        rc, out = update(behind, repo, more={'PATH': f"{shim_dir}:{env['PATH']}"})
        after = state(behind)
        drivers = behind / '.git' / 'precedent-update-drivers'
        cases.append(("the clone's own broken update() never ran",
                      'STALE DRIVER RAN' not in out, failure_detail(out, 300)))
        cases.append(('the run names the fetched commit as the code it ran',
                      f"ran {new[:12]}'s code from a temporary checkout" in out
                      and old[:12] in out, out[:300]))
        cases.append(('the fetched code ran the update (its LEFT FOR YOU on a bare repo)',
                      rc == 1 and 'no vendored loader engine' in out, f'rc={rc}'))
        cases.append(('the loop guard does not reach what the driver run spawns',
                      'CHILD GUARD None' in out, out[:300]))
        cases.append(('no output line names the drivers directory',
                      'precedent-update-drivers' not in out, ''))
        cases.append(("the clone's HEAD, branch, index, status and worktree list "
                      "are as they were", before == after, f'{before} != {after}'))
        left = sorted(p.name for p in drivers.iterdir()) if drivers.is_dir() else []
        cases.append(('the temporary checkout and its lock are gone',
                      left == ['no-hooks'], str(left)))
        cases.append(('no hook fired, global or the clone\'s own',
                      not hooks_marker.exists() and not own_marker.exists(), ''))
        calls = log.read_text(encoding='utf-8') if log.exists() else ''
        sensitive = re.compile(r'(?:^|\s)(symbolic-ref|push|checkout|switch|'
                               r'branch --show-current)(?:\s|$)')
        bad_calls = [l for l in calls.splitlines()
                     if sensitive.search(l.split('\t', 1)[-1])
                     and (str(behind) in l)]
        cases.append(('no HEAD-sensitive git call targets the clone or the worktree',
                      bool(calls) and not bad_calls, '; '.join(bad_calls[:3])))
        gcfg.write_text('', encoding='utf-8')

        # ---- the two tables, row by row, through the bootstrap-only seam ----
        def row(name, c, r, *extra, want, driver=None, data=None, warn=None, more=None):
            rc, out = update(c, r, *extra, only=True, more=more)
            v = verdict(out)
            ok = (rc == 0 and v.get('row') == want
                  and (driver is None or v.get('driver') == driver)
                  and (data is None or v.get('data') == data)
                  and (warn is None or (v.get('warning') != 'None') == warn))
            cases.append((name, ok, f"{v} rc={rc} {failure_detail(out, 200) if not v else ''}"))

        row('behind: run the newest green commit from a worktree', behind, repo,
            want='worktree', driver=new, data=new, warn=False)
        same = clone('same', new)
        row("same tools/ as the driver: in place", same, repo, want='same', driver=new)
        ahead_c = clone('ahead-clone', ahead)
        row('ahead of the driver (CI, a feature branch): in place', ahead_c, repo,
            want='ahead', driver=new)
        dirty = clone('dirty', old)
        with open(dirty / 'tools' / 'build_views.py', 'a', encoding='utf-8') as f:
            f.write('# edited\n')
        row('a tracked change in tools/: in place, with a warning', dirty, repo,
            want='dirty', warn=True)
        untracked = clone('untracked', old)
        (untracked / 'tools' / 'mine.py').write_text('', encoding='utf-8')
        row('an untracked .py in tools/: in place, with a warning', untracked, repo,
            want='dirty', warn=True)
        notes = clone('notes', old)
        (notes / 'tools' / 'notes.txt').write_text('', encoding='utf-8')
        row('an untracked non-Python file in tools/ does not count', notes, repo,
            want='worktree', driver=new)
        row('the opt-out runs in place', behind, repo, want='opt-out',
            more={'PRECEDENT_UPDATE_RUN_IN_PLACE': '1'})
        row('--from-ref on a diverged test commit: its own code', behind, repo,
            '--from-ref', side, want='worktree', driver=side, data=side)
        row('--take-anyway of a newer unmarked commit: that commit\'s code', behind,
            repo, '--take-anyway', late, want='worktree', driver=late, data=late)
        staging = consumer('staging-follower', upstream='staging')
        row('a staging follower takes the staging tip as G', behind, staging,
            want='worktree', driver=new, data=new)
        # A pin some weeks back: the data stays the pin, the code is G.
        pinned = consumer('pinned')
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_update as _pu
        import precedent_local_edits as _le
        _pu.record_pin(pinned, boot, 'main')
        row('a pin older than G: data is the pin, the driver is G', behind, pinned,
            want='worktree', driver=new, data=boot)
        row('--move drops the pin', behind, pinned, '--move', want='worktree',
            driver=new, data=new)

        # The bootstrap reads only: a stand-in commit at HEAD, a journal and
        # a pin, all byte-identical across a bootstrap-only run.
        (pinned / 'f.txt').write_text('x\n', encoding='utf-8')
        git(pinned, 'add', 'f.txt')
        git(pinned, 'commit', '-qm', 'base')
        (pinned / 'f.txt').write_text('y\n', encoding='utf-8')
        git(pinned, 'commit', '-qam', _pu.TEMP_COMMIT_MESSAGE + ' (left by a killed run)')
        gitdir = pinned / '.git'
        journal = gitdir / _le.JOURNAL_DIR
        journal.mkdir()
        (journal / 'journal.json').write_text('{"x": 1}\n', encoding='utf-8')

        def snapshot():
            files = sorted(str(p.relative_to(pinned)) + ':' +
                           hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in pinned.rglob('*')
                           if p.is_file() and '.git' not in p.relative_to(pinned).parts)
            jfiles = sorted(p.name + ':' + p.read_text(encoding='utf-8')
                            for p in journal.iterdir())
            return (git(pinned, 'rev-parse', 'HEAD'),
                    hashlib.sha256((gitdir / 'index').read_bytes()).hexdigest(),
                    jfiles, (gitdir / _pu.STAGED_RECORD).read_text(encoding='utf-8'),
                    git(pinned, 'status', '--porcelain'), files)
        first = snapshot()
        update(behind, pinned, only=True)
        cases.append(('the bootstrap writes nothing into the consumer',
                      snapshot() == first, ''))
        cases.append(('precedent.json is never in the swap journal',
                      _pu.vendored_layer_paths(pinned, ['precedent.json']) == [], ''))

        # No green commit: in place, warned, never a guessed tip.
        git(origin, 'update-ref', '-d', marker)
        row('no passed marker in the window: in place, with a warning', behind, repo,
            want='no-green', warn=True)
        git(origin, 'update-ref', marker, new)

        # Parallel runs: a live run's checkout survives another's cleanup, a
        # dead run's is removed. The live holder is another PROCESS holding
        # fcntl.flock (an in-process lockf would read as dead).
        par = clone('parallel', old)
        pdrivers = par / '.git' / 'precedent-update-drivers'
        pdrivers.mkdir()
        live, dead = pdrivers / '1-live-aaaaaa', pdrivers / '2-dead-bbbbbb'
        for t in (live, dead):
            git(par, 'worktree', 'add', '-q', '--detach', str(t), new)
            (pdrivers / f'{t.name}.lock').write_text('', encoding='utf-8')
        holder = subprocess.Popen(
            [sys.executable, '-c',
             'import fcntl, sys, time\n'
             f'f = open({str(pdrivers / (live.name + ".lock"))!r}, "a+")\n'
             'fcntl.flock(f, fcntl.LOCK_EX)\nprint("held", flush=True)\n'
             'time.sleep(120)\n'], stdout=subprocess.PIPE, text=True)
        try:
            holder.stdout.readline()
            update(par, repo)
            cases.append(("a live run's checkout survives another run's cleanup",
                          live.is_dir(), ''))
            cases.append(("a dead run's checkout and lock are removed",
                          not dead.exists() and not (pdrivers / f'{dead.name}.lock').exists(),
                          str(sorted(p.name for p in pdrivers.iterdir()))))
        finally:
            holder.kill()
            holder.wait()

        # The fallback: no worktree can be made, so the clone's own code runs
        # and says first that it may be older than what it applies -- after
        # only the line saying who the report is for, which frames it all
        # (inner-workings-for-code-owners).
        fb = clone('fallback', boot)
        (fb / '.git' / 'precedent-update-drivers').write_text('', encoding='utf-8')
        rc, out = update(fb, repo)
        summary = [ln for ln in out.split('== Update Vendors ==', 1)[-1]
                   .lstrip('\n').splitlines()
                   if not ln.startswith('  FOR YOU, NOT THE PERSON:')]
        cases.append(('a worktree that cannot be made: the warning comes first',
                      bool(summary) and summary[0].startswith('  WARNING: could not set '
                                                              'up a temporary checkout'),
                      summary[:2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_is_one_command():
    """tools/precedent_update.py runs Update Vendors end to end on a real
    consumer and ends in one of three outcomes, each asserted by its own
    words (practice: control-asserts-which-failure).

    The fixture is the state a consumer was really in on 2026-09-27: an
    engine vendored from main, a catalogue recorded against main, and a pin
    still naming precedent-beta-v01. That update stopped halfway on a hand
    edit and a question already answered (spec/ONE_COMMAND_UPDATE_PLAN.md).
    Here it must finish with nothing asked. The two LEFT FOR YOU cases are
    the controls that the tool does stop where a repo's own call is needed,
    and names the file.

    Owns its state (practice: fixture-owns-its-state): HOME and the user
    config are isolated, or this container's private sources resolve into
    the fixture and fail its view sync for reasons it never planted.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-'))
    cases = []
    ref = _ref_including_worktree(ROOT)
    env = {**os.environ, 'HOME': str(tmp / 'home'),
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json'),
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
    (tmp / 'home').mkdir()

    def sh(*argv, cwd):
        r = subprocess.run(list(argv), cwd=str(cwd), env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def consumer(name, catalogue=True):
        repo = tmp / name
        repo.mkdir()
        sh('git', 'init', '-q', '-b', 'main', cwd=repo)
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(ROOT)}]}) + '\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')
        _seed_fixture_engine(repo, 'consumer', env, cwd=repo)
        if catalogue:
            _rc, head = sh('git', 'rev-parse', f'origin/{pve_branch}', cwd=ROOT)
            (repo / 'process').mkdir()
            (repo / 'process' / 'manifest.json').write_text(json.dumps({
                'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                             'vendored_at': 'process/upstream',
                             'branch': pve_branch, 'commit': head.strip()},
                'entries': []}, indent=2) + '\n', encoding='utf-8')
            checkin = [sys.executable, str(ROOT / 'tools' / 'checkin.py')]
            sh(*checkin, 'update', str(ROOT), '--repo', str(repo), '--force', cwd=repo)
            m = json.loads((repo / 'process' / 'manifest.json').read_text())
            # The commit the mirror actually copied, never `head` above:
            # update fetches origin/<branch> in ROOT first, so when main has
            # moved since this clone's last fetch the two differ, the
            # recorded commit no longer matches the vendored tree, and the
            # run below stops on a "local change" it never planted
            # (2026-09-29, while other windows were promoting into main).
            m['upstream']['commit'] = m['upstream'].get('synced_from', head.strip())
            m['upstream']['branch'] = 'precedent-beta-v01'   # the retired pin
            (repo / 'process' / 'manifest.json').write_text(
                json.dumps(m, indent=2) + '\n', encoding='utf-8')
        sh('git', 'add', '-A', cwd=repo)
        sh('git', 'commit', '-qm', 'installed', cwd=repo)
        # A remote without a push: record's carry check fetches origin.
        sh('git', 'clone', '-q', '--bare', str(repo), str(tmp / f'{name}.git'), cwd=tmp)
        sh('git', 'remote', 'add', 'origin', str(tmp / f'{name}.git'), cwd=repo)
        sh('git', 'fetch', '-q', 'origin', cwd=repo)
        return repo

    def update(repo, *extra):
        return sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                  '--repo', str(repo), '--from-ref', ref, '--skip-check', *extra,
                  cwd=repo)

    def copy_of(src, name):
        # Every consumer below starts the same, so one is built and the rest
        # are copies, repository and bare origin, made before anything runs
        # on it: each gets its own, and nothing one does reaches another.
        repo, bare = tmp / name, tmp / f'{name}.git'
        shutil.copytree(src, repo, symlinks=True)
        shutil.copytree(tmp / f'{src.name}.git', bare, symlinks=True)
        sh('git', 'remote', 'set-url', 'origin', str(bare), cwd=repo)
        sh('git', 'fetch', '-q', 'origin', cwd=repo)
        return repo

    import precedent_vendor_engine as _pve
    pve_branch = _pve.SOURCE_BRANCH
    try:
        done = consumer('done')
        edited, local = copy_of(done, 'edited-engine'), copy_of(done, 'edited-catalogue')
        # The fixture's AGENTS.md is bare, so the first run rightly lists the
        # template's sections as this repo's call. Leaving them out is an
        # answer, and the refresh remembers it: the second run asks nothing.
        rc, out = update(done)
        cases.append(('the first run lists the template sections the repo lacks as '
                      'its own call: exit 1, LEFT FOR YOU',
                      rc == 1 and 'LEFT FOR YOU' in out and 'AGENTS.md "' in out,
                      failure_detail(out, 1500)))
        rc, out = update(done)
        pin = json.loads((done / 'process' / 'manifest.json').read_text())[
            'upstream']['branch']
        cases.append(('an install on the retired pin finishes with nothing asked: '
                      'exit 0 and DONE', rc == 0 and 'DONE -- nothing left' in out,
                      failure_detail(out, 1500)))
        # A repository with only main asked for no tiers: an update -- even
        # one run by a person on the ladder -- leaves it on main (Morgan,
        # 2026-10-02, strength: decided: "nothing creates tiers in a
        # repository that did not ask for them").
        landing = json.loads((done / 'precedent.json').read_text()).get('landing_branch')
        cases.append(('...its precedent.json, which named no landing branch, still '
                      'names none: the update gives a repository without tiers none',
                      landing is None, landing))
        _rc, heads = sh('git', 'ls-remote', '--heads', 'origin', cwd=done)
        cases.append(('...and origin, which had only main, still has only main',
                      'refs/heads/staging' not in heads, failure_detail(heads, 400)))
        # A repository that does ask -- its landing_branch names a tier --
        # gets whichever tier branch origin is missing.
        _pj = json.loads((done / 'precedent.json').read_text())
        _pj['landing_branch'] = 'staging'
        (done / 'precedent.json').write_text(json.dumps(_pj, indent=2) + '\n')
        sh('git', 'commit', '-qam', 'asks for tiers', cwd=done)
        update(done)
        _rc, heads = sh('git', 'ls-remote', '--heads', 'origin', cwd=done)
        cases.append(('...and once its precedent.json asks for tiers, the update '
                      'makes staging on origin',
                      'refs/heads/staging' in heads, failure_detail(heads, 400)))
        cases.append(('...its catalogue pin now names ' + pve_branch,
                      pin == pve_branch, pin))
        cases.append(('...and its loader views were regenerated',
                      'views: regenerated' in out and bv.BEGIN_MARKER in
                      (done / 'AGENTS.md').read_text() and
                      len((done / 'AGENTS.md').read_text()) > 200, failure_detail(out, 600)))

        with open(edited / 'tools' / 'precedent_show.py', 'a', encoding='utf-8') as f:
            f.write('# a local edit\n')
        rc, out = update(edited)
        cases.append(('a hand-edited engine file stops it: exit 1, LEFT FOR YOU, '
                      'naming the file', rc == 1 and 'LEFT FOR YOU' in out
                      and 'precedent_show.py' in out.split('LEFT FOR YOU', 1)[-1],
                      failure_detail(out, 1500)))

        target = next(p for p in sorted((local / 'process' / 'upstream' / 'practices')
                                        .glob('*.md')))
        with open(target, 'a', encoding='utf-8') as f:
            f.write('\nA line this repo added.\n')
        rc, out = update(local)
        cases.append(('a local change in the vendored catalogue stops it: exit 1, '
                      'LEFT FOR YOU, naming the file',
                      rc == 1 and f'process/upstream/practices/{target.name}' in out,
                      failure_detail(out, 1500)))

        # A practice SET renders MAP.md and GLOSSARY.md too, and its deep
        # check compares them to a fresh build. 2026-09-27: every set's
        # update failed that check on one MAP.md row for a new engine file,
        # because the views step ran only a consumer's sync tool.
        src = tmp / 'source-set'
        (src / 'practices').mkdir(parents=True)
        (src / 'practices' / 'fixture-rule.md').write_text(
            '---\nslug:        fixture-rule\ntitle:       A fixture rule\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  []\n'
            'occasion:    "when a fixture needs a practice"\ngates:       []\n'
            'index_clause: "a fixture rule"\nchecked_by:  null\ndefines:     []\n'
            'command:     null\nstatus:      active\nin_force_at: null\n'
            'supersedes:  []\noverrides:   null\nadded:       "2026-09-27"\n---\n\n'
            '## Rule\nA fixture rule.\n\n## Detail\nNone.\n\n## Why\nA test.\n\n'
            '## Story\nNone.\n\n## Install\nNothing.\n', encoding='utf-8')
        (src / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main',
             'visibility': 'public'}) + '\n', encoding='utf-8')
        (src / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')
        sh('git', 'init', '-q', '-b', 'main', cwd=src)
        _seed_fixture_engine(src, 'source', env, cwd=src)
        sh(sys.executable, 'tools/build_views.py', '--repo', '.', cwd=src)
        with open(src / 'MAP.md', 'a', encoding='utf-8') as f:
            f.write('| a row a newer engine would render differently |\n')
        sh('git', 'add', '-A', cwd=src)
        sh('git', 'commit', '-qm', 'installed, views stale', cwd=src)
        rc_before, _ = sh(sys.executable, 'tools/build_views.py', '--repo', '.',
                          '--check', cwd=src)
        rc, out = update(src)
        rc_after, check = sh(sys.executable, 'tools/build_views.py', '--repo', '.',
                             '--check', cwd=src)
        cases.append(("a practice set's stale MAP.md is rebuilt by the update, so "
                      "its deep check's view comparison passes",
                      rc_before != 0 and rc_after == 0 and rc == 0
                      and 'MAP.md' in out, failure_detail(out + check, 1500)))

        bare = tmp / 'no-engine'
        bare.mkdir()
        rc, out = update(bare)
        cases.append(('a repo with no vendored engine is sent to the migration, '
                      'not updated', rc == 1 and 'this is a migration' in out, failure_detail(out, 600)))

        # ...and a repo to be migrated still gets its branch tiers from here
        # (Morgan, 2026-09-27: "when migrating check for these and create them").
        classic = tmp / 'classic'
        classic.mkdir()
        sh('git', 'init', '-q', '-b', 'main', cwd=classic)
        (classic / 'README.md').write_text('# classic install\n', encoding='utf-8')
        sh('git', 'add', '-A', cwd=classic)
        sh('git', 'commit', '-qm', 'classic', cwd=classic)
        sh('git', 'clone', '-q', '--bare', str(classic), str(tmp / 'classic.git'), cwd=tmp)
        sh('git', 'remote', 'add', 'origin', str(tmp / 'classic.git'), cwd=classic)
        sh('git', 'fetch', '-q', 'origin', cwd=classic)
        rc, out = update(classic)
        _rc, heads = sh('git', 'ls-remote', '--heads', 'origin', cwd=classic)
        cases.append(('a repo still to be migrated is sent to the migration, and an '
                      'update gives it no tiers it did not ask for',
                      rc == 1 and 'this is a migration' in out
                      and 'refs/heads/staging' not in heads, failure_detail(out + heads, 800)))

        rc, out = sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                     '--repo', str(ROOT), cwd=ROOT)
        cases.append(('--repo naming the BestPractice clone itself is refused',
                      rc == 2 and 'is this BestPractice clone itself' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))
def check_update_rebaselines_what_it_asked_about_and_reviews_no_git_output():
    """Two Update Vendors faults found on one consumer, 2026-10-11.

    1. A file the update asked the person to edit (LEFT FOR YOU) and they
       edited as asked is part of the update: the rerun re-records its
       classic-manifest baseline, where before it took the edit for a local
       change and the basic check failed it as DRIFT.
    2. What git prints is never read as a warning: the upstream review read
       `git show` of the engine source and listed lines of code as items.

    Negative control, measured 2026-10-11 against staging at 982b077: the
    module has no asked_paths, earlier_asked or _is_git, and git output was
    appended to OUTPUTS, so every case fails."""
    import tempfile, json as _json, hashlib
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    need = ('asked_paths', 'record_asked', 'earlier_asked', '_is_git')
    if not all(hasattr(pu, n) for n in need):
        return False, 'precedent_update lacks ' + ', '.join(n for n in need if not hasattr(pu, n))
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t',
                                       '-c', 'user.email=t@example.invalid', *a],
                                      capture_output=True, text=True)
        g('init', '-q')
        (repo / 'AGENTS.md').write_text('# old\n', encoding='utf-8')
        (repo / 'local').mkdir()
        (repo / 'local' / 'v.md').write_text('x\n', encoding='utf-8')
        (repo / 'process').mkdir()
        old = hashlib.sha256(b'# old\n').hexdigest()
        (repo / 'process' / 'manifest.json').write_text(_json.dumps({
            'upstream': {'vendored_at': 'process/upstream'},
            'entries': [{'practice': 'instructions-file', 'local_path': 'AGENTS.md',
                         'upstream_path': 'templates/AGENTS.md.template',
                         'granularity': 'file', 'status': 'synced',
                         'local_sha256': old}]}), encoding='utf-8')
        g('add', '-A'); g('commit', '-q', '-m', 'base')
        left = [('AGENTS.md "### Two check levels"', 'replace the section'),
                ('local/v.md:142', 'template wording dropped'),
                ('retired set: x', 'no file'),
                ('missing.md:3', 'a file that is not there')]
        got = pu.asked_paths(left, repo)
        cases.append(('the asked files are read from the LEFT items, and only '
                      f'files that exist (got {got})', got == ['AGENTS.md', 'local/v.md']))
        pu.record_asked(repo, got)
        cases.append(('the next run reads them back',
                      pu.earlier_asked(repo) == {'AGENTS.md', 'local/v.md'}))
        (repo / 'AGENTS.md').write_text('# edited as asked\n', encoding='utf-8')
        done = pu.rebaseline_vendored_entries(repo, pu.earlier_asked(repo))
        rec = _json.loads((repo / 'process' / 'manifest.json').read_text())['entries'][0]
        cases.append(('an asked file edited as asked is re-baselined',
                      done == ['AGENTS.md'] and rec['local_sha256']
                      == hashlib.sha256(b'# edited as asked\n').hexdigest()))
        pu.record_asked(repo, [])
        cases.append(('a run that asks nothing clears the list',
                      pu.earlier_asked(repo) == set()))
        (repo / 'AGENTS.md').write_text('# a local change\n', encoding='utf-8')
        cases.append(('...and then an edit is a local change again, left as DRIFT',
                      pu.rebaseline_vendored_entries(repo, pu.earlier_asked(repo)) == []))
        pu.OUTPUTS.clear()
        pu.run(['git', '-C', str(repo), 'show', 'HEAD:AGENTS.md'], repo)
        cases.append(('git output is not read by the upstream review',
                      pu.OUTPUTS == []))
        pu.run([sys.executable, '-c', 'print("WARN: a real warning")'], repo)
        cases.append(('a tool step\'s output still is',
                      len(pu.OUTPUTS) == 1 and 'WARN: a real warning' in pu.OUTPUTS[0]))
        pu.OUTPUTS.clear()
    failed = [n for n, ok in cases if not ok]
    return not failed, '; '.join(failed) or f'{len(cases)} stated cases'


def check_merge_takes_the_vendor_update():
    """tools/precedent_merge_vendors.py, run at a merge, takes Update Vendors
    as a commit of its own when the update finishes, and takes everything it
    wrote back when it does not -- never blocking the merge, exit 0 every
    time (2026-10-02, Alex: "Can we set up a system so merge also does
    vendor updates?"). Each outcome is asserted by its own words and by the
    repository's state after it (practice: control-asserts-which-failure):

      - an upstream change, the update DONE: HEAD gains exactly one commit,
        it carries the change, and nothing is left staged or changed;
      - the update leaving calls for the person: HEAD unmoved, nothing left
        staged or changed, and the reason printed;
      - a tracked file changed and not committed: refused before anything
        runs, the person's edit untouched;
      - freshness saying nothing is behind: nothing runs at all.

    Negative control: before this tool existed the merge only printed the
    freshness notice, so every case fails for want of the file."""
    fx = _LocalEditsFixture('precedent-merge-vendors-')
    tool = ROOT / 'tools' / 'precedent_merge_vendors.py'
    cases = []

    def merge_vendors(repo, *extra):
        return fx.sh(sys.executable, str(tool), '--repo', str(repo), '--source',
                     str(ROOT), '--always', '--skip-check', *extra, cwd=repo)

    def clean(repo):
        return fx.git(repo, 'status', '--porcelain', '--untracked-files=no') == ''
    try:
        # --- DONE: committed on its own -------------------------------------
        repo = fx.consumer('done')
        seeded = fx.seeded_from(repo)
        fx.update(repo, seeded)          # answer the bare fixture's questions
        fx.commit(repo, 'first update')
        f = repo / 'tools' / 'precedent_show.py'
        up = f.read_bytes() + b'\n# upstream, taken at a merge\n'
        ref = fx.upstream(seeded, {'tools/precedent_show.py': up})
        head = fx.git(repo, 'rev-parse', 'HEAD')
        rc, out = merge_vendors(repo, '--from-ref', ref)
        parent = fx.git(repo, 'rev-parse', 'HEAD~1')
        msg = fx.git(repo, 'log', '-1', '--format=%B')
        cases.append(('an update that finishes is one commit of its own on top, '
                      'carrying the change, with nothing left over',
                      rc == 0 and 'VENDORS: updated, in commit' in out
                      and parent == head and f.read_bytes() == up and clean(repo)
                      and msg.startswith('Update Vendors at merge'),
                      failure_detail(out, 1500)))
        # The same update again: it finishes with nothing to stage. It is
        # current, not refused (2026-10-12: git refused the empty commit and
        # the step printed "NOT TAKEN ... commit was refused").
        head = fx.git(repo, 'rev-parse', 'HEAD')
        rc, out = merge_vendors(repo, '--from-ref', ref)
        cases.append(('an update with nothing to change says current, not refused',
                      rc == 0 and 'VENDORS: current' in out and 'NOT TAKEN' not in out
                      and fx.git(repo, 'rev-parse', 'HEAD') == head and clean(repo),
                      failure_detail(out, 1500)))

        # --- LEFT: everything taken back -------------------------------------
        repo = fx.consumer('left')     # bare AGENTS.md: the first run asks
        head = fx.git(repo, 'rev-parse', 'HEAD')
        rc, out = merge_vendors(repo, '--from-ref', fx.seeded_from(repo))
        cases.append(('an update that leaves calls for the person is taken back '
                      'whole, the reason printed, the merge not blocked',
                      rc == 0 and 'VENDORS: NOT TAKEN' in out and 'calls for the person' in out
                      and 'LEFT FOR YOU' in out
                      and fx.git(repo, 'rev-parse', 'HEAD') == head and clean(repo)
                      and fx.git(repo, 'diff', '--cached', '--name-only') == '',
                      failure_detail(out, 1500)))

        # --- a person's uncommitted edit: refused, untouched -----------------
        repo = fx.consumer('dirty')
        readme = repo / 'AGENTS.md'
        mine = readme.read_text(encoding='utf-8') + '\nmy unfinished edit\n'
        readme.write_text(mine, encoding='utf-8')
        rc, out = merge_vendors(repo, '--from-ref', fx.seeded_from(repo))
        cases.append(('a tracked file changed and not committed: refused before '
                      'anything runs, the edit left as it was',
                      rc == 0 and 'NOT TAKEN' in out and 'Nothing was run' in out
                      and readme.read_text(encoding='utf-8') == mine, failure_detail(out, 800)))

        # --- current: nothing runs -------------------------------------------
        rc, out = fx.sh(sys.executable, '-c', (
            'import sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_merge_vendors as mv\n'
            'mv.vendors_behind = lambda _r: ([], [])\n'
            'mv.refresh_views = lambda _r: print("VIEWS: asked")\n'
            'mv.subprocess.run = None  # running anything would raise\n'
            f'sys.exit(mv.run({str(repo)!r}))\n'), cwd=repo)
        cases.append(('nothing behind: says current and runs no update -- only '
                      'the views check, which has a test of its own',
                      rc == 0 and 'VENDORS: current' in out
                      and 'VIEWS: asked' in out, failure_detail(out, 800)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_reruns_pinned_to_its_first_commit():
    """An update worked over several rounds of LEFT FOR YOU takes the same
    source commit on every rerun until one reports DONE, says so, and says
    how to move.

    2026-10-08, from a consuming repository: each rerun fetched main again,
    so one update started at one commit and finished against another, and a
    decline already settled came back because upstream had changed that file
    again in between. The pin lives in the run-to-run record the FAILED-run
    restore already keeps in the git directory (precedent-update-staged.json).

    Here: two declines move at the first commit; the person re-decides one
    and leaves the other open, so every run stays LEFT; upstream then
    changes the settled one again. The followed branch's tip is stubbed
    (fetch a no-op, `rev-parse origin/main` answered), so it can move
    between runs.

    Negative control, measured 2026-10-08 against
    2026-10-08-produce-copy-check-y1ktn at ae07871f: the rerun mirrors the
    moved commit's text and asks about the settled decline again, and no run
    says it is pinned."""
    import hashlib
    import contextlib
    import io
    import precedent_vendor_engine as _pve
    branch = _pve.SOURCE_BRANCH
    fx = _LocalEditsFixture('precedent-update-pin-')
    cases = []
    sha = lambda b: hashlib.sha256(b).hexdigest()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    held_pin = getattr(pu, 'held_pin', lambda _repo: None)

    def run(repo, tip, *extra):
        return fx.sh(sys.executable, '-c', (
            'import sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_update as pu\n'
            'real = pu.run\n'
            'def run(argv, cwd):\n'
            '    if argv[:1] == ["git"] and "fetch" in argv:\n'
            '        return 0, ""\n'
            f'    if argv[:1] == ["git"] and "rev-parse" in argv and argv[-1] == "origin/{branch}":\n'
            f'        return 0, {tip!r} + "\\n"\n'
            '    return real(argv, cwd)\n'
            'pu.run = run\n'
            'pu.main_test_state = lambda sha, tests: ("passed", "stand-in")\n'
            f'sys.exit(pu.main(["--repo", {str(repo)!r}, "--skip-check", *{list(extra)!r}]))\n'),
            cwd=repo)

    try:
        repo = fx.consumer('pinned')
        seeded = fx.seeded_from(repo)
        settled, still = 'practices/verify-postcondition.md', 'practices/repo-is-memory.md'
        show = lambda rel: subprocess.run(['git', '-C', str(ROOT), 'show', f'{seeded}:{rel}'],
                                          capture_output=True).stdout
        old = {settled: show(settled), still: show(still)}
        (repo / 'process').mkdir()
        (repo / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream', 'branch': branch,
                         'commit': seeded, 'scrub_blocklist': None},
            'entries': [{'practice': pathlib.Path(rel).stem, 'upstream_path': rel,
                         'local_path': None, 'status': 'declined',
                         'declined_upstream_sha256': sha(old[rel]), 'notes': 'ours'}
                        for rel in (settled, still)]}, indent=2) + '\n', encoding='utf-8')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--force', '--from-ref', seeded, cwd=repo)
        fx.commit(repo, 'catalogue with two declines')
        fx.sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=repo)
        aud = repo / '.audit' / 'tools'
        aud.mkdir(parents=True)
        for n in ('practice_audit.py', 'generated_blocks.py'):
            shutil.copy(ROOT / 'tools' / n, aud / n)
        with open(repo / '.git' / 'info' / 'exclude', 'a', encoding='utf-8') as f:
            f.write('.audit/\n')
        once = old[settled] + b'\nThe first upstream change.\n'
        first = fx.upstream(seeded, {settled: once, still: old[still] + b'\nMoved.\n'})
        moved = fx.upstream(first, {settled: once + b'\nThe second upstream change.\n'})
        vendored = repo / 'process' / 'upstream' / settled
        engine = lambda: json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json').read_text(
            encoding='utf-8')).get('source_commit')
        asked = lambda out, rel: any('a decline to decide again' in l and rel in l
                                     for l in out.split('LEFT FOR YOU', 1)[-1].splitlines())

        rc1, out1 = run(repo, first)
        cases.append(('the first run is left for the person, and says what it is '
                      'pinned to and how to move',
                      rc1 == 1 and f'PINNED: a rerun takes {branch} @ {first[:12]}' in out1
                      and '--move' in out1.split('PINNED:', 1)[-1], failure_detail(out1, 1200)))
        fx.sh(sys.executable, str(aud / 'practice_audit.py'), '--redecide',
              'verify-postcondition', cwd=repo)
        rc2, out2 = run(repo, moved)
        cases.append(('the rerun after the branch moved takes the first commit again, '
                      'engine and catalogue both',
                      vendored.read_bytes() == once and engine() == first,
                      (engine(), failure_detail(out2, 1200))))
        cases.append(('...so the decline settled against it stays settled, and the '
                      'open one is still asked',
                      rc2 == 1 and not asked(out2, settled) and asked(out2, still),
                      failure_detail(out2.split('LEFT FOR YOU', 1)[-1], 1200)))
        cases.append(('...and its source line says it is pinned, that the branch moved, '
                      'and how to take it',
                      f'source: {branch} @ {first[:12]} -- pinned' in out2
                      and f'moved on to {moved[:12]}; --move takes it' in out2,
                      [l for l in out2.splitlines() if 'source:' in l]))
        rc3, out3 = run(repo, moved, '--move')
        held = held_pin(repo)
        cases.append(('--move takes the branch\'s newest commit and pins that instead, '
                      'so the settled decline is rightly asked again',
                      vendored.read_bytes() != once and engine() == moved
                      and f'moved, as asked, off {first[:12]}' in out3
                      and asked(out3, settled) and held and held['commit'] == moved
                      and f'PINNED: a rerun takes {branch} @ {moved[:12]}' in out3,
                      (rc3, held, failure_detail(out3, 1200))))
        # DONE drops the pin; LEFT keeps it, closing the report directly.
        for left, name in () if not hasattr(pu, 'record_pin') else ((True, 'a LEFT outcome keeps the pin'),
                           (False, 'a DONE outcome drops it, so the next update starts '
                                   'from the tip')):
            pu.record_pin(repo, moved, branch)
            rep = pu.Report()
            rep.pin_repo = repo
            if left:
                rep.leave('something', 'a call for the person')
            with contextlib.redirect_stdout(io.StringIO()):
                rep.close()
            held = held_pin(repo)
            cases.append((name, (held is not None) == left, held))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))

def check_local_edits_fetch_the_vendored_commit_from_upstream():
    """precedent_local_edits.py judges a consuming repository's edits to
    received files against the commit they were vendored from. Run from
    the consumer, that commit was never in the consumer's own history, so
    every file read "cannot judge" unless an upstream clone sat beside it
    (Alex, 2026-10-04: fold the vendor engines into the send/take loop).
    It now fetches that one commit from the upstream the manifest records.
    Both directions: with no upstream named, a missing commit is still
    reported missing, and a fetch creates no branch or tag."""
    import tempfile
    import precedent_local_edits as le
    name = 'local-edit status fetches the vendored-from commit from upstream'
    cases = []
    env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com')
    with tempfile.TemporaryDirectory() as td:
        up, mine = pathlib.Path(td) / 'up', pathlib.Path(td) / 'mine'
        for d in (up, mine):
            d.mkdir()
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(d)], env=env)
        (up / 'a.py').write_text('x = 1\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(up), 'add', '-A'], env=env)
        subprocess.run(['git', '-C', str(up), 'commit', '-qm', 'u'], env=env)
        sha = subprocess.run(['git', '-C', str(up), 'rev-parse', 'HEAD'],
                             capture_output=True, text=True).stdout.strip()
        (mine / 'b.py').write_text('y = 2\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(mine), 'add', '-A'], env=env)
        subprocess.run(['git', '-C', str(mine), 'commit', '-qm', 'm'], env=env)
        refs_before = subprocess.run(['git', '-C', str(mine), 'for-each-ref'],
                                     capture_output=True, text=True).stdout
        cases.append(('with no upstream named, the missing commit is reported missing',
                      not le._has_commit(mine, sha)))
        cases.append(('with the recorded upstream, the commit is fetched',
                      le._has_commit(mine, sha, str(up))
                      and le._show(mine, sha, 'a.py') == b'x = 1\n'))
        cases.append(('...and the clone stays complete: never marked shallow',
                      not (mine / '.git' / 'shallow').exists()
                      and subprocess.run(['git', '-C', str(mine), 'rev-parse',
                                          '--is-shallow-repository'], capture_output=True,
                                         text=True).stdout.strip() == 'false'))
        cases.append(('...and no branch or tag is created',
                      subprocess.run(['git', '-C', str(mine), 'for-each-ref'],
                                     capture_output=True, text=True).stdout == refs_before))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_a_sync_deletion_is_not_a_local_edit():
    """precedent_local_edits.py reads a file upstream has and a consumer's
    copy lacks as the consumer's own deletion -- and every later update then
    "keeps" it out. A file removed by a vendor sync (the copy rules once
    left it out) or never shipped at all is upstream's doing, not the
    consumer's: a consumer went without 46 live gotchas for days after
    gotchas/ shipped again on 2026-10-01 (found 2026-10-04). Both
    directions: a deletion the consumer committed on its own still counts."""
    import tempfile
    import precedent_local_edits as le
    name = 'a deletion made by a vendor sync is not a local edit'
    env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        (repo / 'process' / 'upstream' / 'gotchas').mkdir(parents=True)
        man = repo / 'process' / 'manifest.json'
        man.write_text('{"upstream": {\n  "commit": "aaa"\n}}\n')
        for n in ('synced-away.md', 'mine-away.md'):
            (repo / 'process' / 'upstream' / 'gotchas' / n).write_text('x\n')
        g('add', '-A'); g('commit', '-qm', 'vendor at aaa')
        (repo / 'process' / 'upstream' / 'gotchas' / 'synced-away.md').unlink()
        man.write_text('{"upstream": {\n  "commit": "bbb"\n}}\n')
        g('add', '-A'); g('commit', '-qm', 'a sync whose rules left the file out')
        (repo / 'process' / 'upstream' / 'gotchas' / 'mine-away.md').unlink()
        g('add', '-A'); g('commit', '-qm', 'the consumer deletes one itself')
        rel = lambda n: f'process/upstream/gotchas/{n}'
        cases.append(('removed by a sync: not a local edit',
                      not le._deleted_here(repo, rel('synced-away.md'))))
        cases.append(('never shipped here: not a local edit',
                      not le._deleted_here(repo, rel('never-had.md'))))
        cases.append(('removed by the consumer: still a local edit',
                      le._deleted_here(repo, rel('mine-away.md'))))
        # checkin.py's own guard asks the same question through
        # local_changes(); it once counted the sync's deletion and refused
        # every update (found 2026-10-04, after the fix above).
        src = pathlib.Path(td) / 'source'
        s = lambda *a: subprocess.run(['git', '-C', str(src), *a], env=env,
                                      capture_output=True, text=True)
        (src / 'gotchas').mkdir(parents=True)
        for n in ('synced-away.md', 'mine-away.md'):
            (src / 'gotchas' / n).write_text('x\n')
        s('init', '-q', '-b', 'main'); s('add', '-A'); s('commit', '-qm', 'upstream')
        head = s('rev-parse', 'HEAD').stdout.strip()
        ck = le._checkin(repo)
        drift = [p.as_posix() for p in (ck.local_changes(src, head) or [])]
        cases.append(("checkin's guard: the consumer's deletion only",
                      drift == ['gotchas/mine-away.md']))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_section0_catalogue_resolves_a_committed_edit():
    """A section 0 install's universal catalogue resolves a committed local
    edit when its own CATALOGUE_SYNC.json names the commit it was synced
    from -- that commit is BASE -- instead of refusing. Without that record
    there is no one BASE to merge with, and the existing cases in
    check_update_vendors_updates_a_section_0_catalogue and
    check_update_vendors_trusts_the_catalogues_own_sync_commit still expect
    the refusal (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md).

    Negative control, measured 2026-09-29: against vendor_universal_catalogue
    before this, both cases are refused ("carry local edits")."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    fx = _LocalEditsFixture('precedent-section0-edit-')
    env = _section0_fixture_env()
    cases = []
    try:
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        base = subprocess.run(['git', '-C', str(ROOT), 'show',
                               f'{head}:practices/park-it.md'],
                              capture_output=True).stdout
        lines = base.decode().splitlines(True)
        after = next(i for i, l in enumerate(lines) if i and l.strip() == '---') + 2
        record = json.dumps({'source_commit': head}).encode()

        # This repo added a line near the top, upstream one at the end. Since
        # 2026-10-08 (Morgan, decided) upstream's version is the default, so
        # it is taken and the rest of the edit is shown for the session.
        rev = fx.upstream(head, {'practices/park-it.md': base + b'\nUpstream: end.\n'})
        d = _section0_repo(fx.tmp, {
            'practices/park-it.md': _insert(base, 'Mine: near the top.\n', at=after),
            'CATALOGUE_SYNC.json': record}, env)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, rev)
        f = d / 'precedent' / 'universal' / 'practices' / 'park-it.md'
        got = f.read_bytes()
        pref = [t for o, _r, t in rep.edits if o == 'upstream-preferred']
        cases.append(('a committed edit upstream changed elsewhere is not refused: '
                      'upstream\'s version is taken, and the rest of the edit shown',
                      ok is True and not rep.left and got == base + b'\nUpstream: end.\n'
                      and pref and '+Mine: near the top.' in pref[0]
                      and ' keep --repo . ' in pref[0],
                      (rep.left, rep.edits, rep.steps)))

        # Conflict: both changed the same line.
        rev = fx.upstream(head, {'practices/park-it.md':
                                 _replace_line(base, 'Upstream: this line.\n', at=after)})
        d = _section0_repo(fx.tmp, {
            'practices/park-it.md': _replace_line(base, 'Mine: this line.\n', at=after),
            'CATALOGUE_SYNC.json': record}, env)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, rev)
        f = d / 'precedent' / 'universal' / 'practices' / 'park-it.md'
        took = [t for o, _r, t in rep.edits if o == 'took-upstream']
        cases.append(('a conflict takes upstream\'s version and names the commit '
                      'holding this repo\'s', ok is True and not rep.left
                      and b'Upstream: this line.' in f.read_bytes()
                      and took and 'git show' in took[0], (rep.left, rep.edits)))
    except (OSError, subprocess.CalledProcessError, StopIteration) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_merge_is_judged_by_the_landing_check():
    """A merge the rules made is judged by the repo's own landing-tier check
    at Update Vendors' step 5, not only by its own compile and test run
    (precedent_update.check_with_merge_fallback, 2026-09-29): red with the
    merge in place and green without it, upstream's version stands and the
    report says why; red either way, the merge is put back, since it was
    not the cause. The check itself is stubbed here, so each branch is
    decided by the file's content alone.

    Negative control, measured 2026-09-29: with step 5 calling
    judged_as_committed() directly, as it did before, the merged file is
    never taken back and the first case fails."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-merge-judged-'))
    cases = []
    real = pu.judged_as_committed
    try:
        repo = tmp / 'r'
        repo.mkdir()
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        f = repo / 'tools' / 'x.py'
        f.parent.mkdir()
        f.write_text('mine = 1\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'local edit')
        merged, new = b'mine = 1\nMERGED = 1\n', b'theirs = 1\n'

        def run(red_when):
            f.write_bytes(merged)
            rep = pu.Report()
            rep.edits = [(pu.le.MERGED, 'tools/x.py', 'merged')]
            rep.merges = {'tools/x.py': (merged, new)}
            pu.judged_as_committed = lambda _r, _a: (
                (1, 'red') if red_when(f.read_bytes()) else (0, 'green'))
            rc, _out = pu.check_with_merge_fallback(repo, rep, [], 'check for staging')
            return rc, rep

        rc, rep = run(lambda data: b'MERGED' in data)
        cases.append(('red with the merge and green without: upstream\'s version '
                      'stands, reported as rule 3 with the reason',
                      rc == 0 and f.read_bytes() == new
                      and rep.edits[0][0] == pu.le.TOOK_UPSTREAM
                      and 'failed with the merge in place' in rep.edits[0][2],
                      (rc, f.read_bytes(), rep.edits)))
        rc, rep = run(lambda data: True)
        cases.append(('red either way: the merge is put back and the failure '
                      'reported on it', rc == 1 and f.read_bytes() == merged
                      and rep.edits[0][0] == pu.le.MERGED
                      and any('not the cause' in o for _n, o in rep.steps),
                      (rc, f.read_bytes(), rep.steps)))
    finally:
        pu.judged_as_committed = real
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_judges_the_committed_tree():
    """precedent_update's deep check judges the staged update as it will be
    committed, then leaves the index and working tree exactly as it found
    them (2026-09-27: a consumer's update failed its deep check twice on
    staged-only effects -- a change-scope check reading every materialized
    practice as the repo's own prose, and a shipped test cloning HEAD -- and
    passed the moment the same tree was committed)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    name = 'Update Vendors judges the staged update as committed, and undoes the commit'
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='judged-as-committed-'))
    env_keep = {k: os.environ.get(k) for k in ('GIT_CONFIG_GLOBAL', 'GIT_AUTHOR_NAME',
                                                'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME',
                                                'GIT_COMMITTER_EMAIL', 'PRECEDENT_ALLOW_ANY_AUTHOR')}
    os.environ.update({'GIT_CONFIG_GLOBAL': str(tmp / 'gitconfig'), 'GIT_AUTHOR_NAME': 't',
                       'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
                       'GIT_COMMITTER_EMAIL': 't@t', 'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})

    def git(*a):
        return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True)
    try:
        repo = tmp / 'r'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], capture_output=True)
        (repo / 'a.md').write_text('one\n', encoding='utf-8')
        (repo / 'b.md').write_text('keep\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-qm', 'base')
        head = git('rev-parse', 'HEAD').stdout.strip()
        (repo / 'a.md').write_text('two\n', encoding='utf-8')
        git('add', 'a.md')
        (repo / 'b.md').write_text('an unstaged edit\n', encoding='utf-8')
        probe = [sys.executable, '-c',
                 'import subprocess,sys;'
                 'g=lambda *a: subprocess.run(["git",*a],capture_output=True,text=True);'
                 'ok = g("show","HEAD:a.md").stdout=="two\\n" and '
                 'g("diff","--cached","--quiet").returncode==0;'
                 'sys.exit(0 if ok else 1)']
        rc, out = pu.judged_as_committed(repo, probe)
        cases.append(('the check sees the staged update committed, with nothing staged',
                      rc == 0, failure_detail(out, 400)))
        cases.append(('...and afterwards HEAD is where it was, the update still staged, '
                      'the unstaged edit untouched',
                      git('rev-parse', 'HEAD').stdout.strip() == head
                      and git('diff', '--cached', '--name-only').stdout.split() == ['a.md']
                      and (repo / 'b.md').read_text() == 'an unstaged edit\n', ''))
        rc, out = pu.judged_as_committed(repo, [sys.executable, '-c', 'raise SystemExit(1)'])
        cases.append(('a red check is reported red, and the commit is still undone',
                      rc == 1 and git('rev-parse', 'HEAD').stdout.strip() == head
                      and git('diff', '--cached', '--name-only').stdout.split() == ['a.md'],
                      failure_detail(out, 400)))
        hook = repo / '.git' / 'hooks' / 'pre-commit'
        hook.write_text('#!/bin/sh\necho refused-by-hook >&2\nexit 1\n', encoding='utf-8')
        hook.chmod(0o755)
        rc, out = pu.judged_as_committed(repo, [sys.executable, '-c', 'pass'])
        cases.append(("a commit the repo's hooks refuse is reported, never worked around",
                      rc != 0 and 'could not be committed' in out
                      and git('rev-parse', 'HEAD').stdout.strip() == head, failure_detail(out, 400)))
        hook.unlink()
        git('reset', '-q')
        rc, out = pu.judged_as_committed(repo, [sys.executable, '-c', 'pass'])
        cases.append(('with nothing staged the check runs as it is, and nothing is committed',
                      rc == 0 and git('rev-parse', 'HEAD').stdout.strip() == head, failure_detail(out, 400)))
        # 2026-10-06, a consumer repository: a run under `timeout 590` got
        # SIGTERM in the deep check, skipped its `finally`, and left the
        # stand-in at HEAD; the rerun did not look.
        (repo / 'a.md').write_text('three\n', encoding='utf-8')
        git('add', 'a.md')
        git('commit', '-qm', pu.standin_message())
        cases.append(('a stand-in left at HEAD is undone at the start of a run, '
                      'its changes staged again',
                      bool(pu.undo_leftover_standin(repo))
                      and git('rev-parse', 'HEAD').stdout.strip() == head
                      and git('diff', '--cached', '--name-only').stdout.split() == ['a.md']
                      and (repo / 'a.md').read_text() == 'three\n', ''))
        git('commit', '-qm', 'a real commit')
        real = git('rev-parse', 'HEAD').stdout.strip()
        cases.append(('a commit with any other message is never touched',
                      pu.undo_leftover_standin(repo) is None
                      and git('rev-parse', 'HEAD').stdout.strip() == real, ''))
        (repo / 'a.md').write_text('four\n', encoding='utf-8')
        git('add', 'a.md')
        killer = (f'import os, signal, sys, time; sys.path.insert(0, {str(ROOT / "tools")!r}); '
                  'import precedent_update as pu; '
                  f'pu.judged_as_committed(__import__("pathlib").Path({str(repo)!r}), '
                  '[sys.executable, "-c", "import os,signal,time; '
                  'os.kill(os.getppid(), signal.SIGTERM); time.sleep(30)"])')
        k = subprocess.run([sys.executable, '-c', killer], capture_output=True, text=True,
                           timeout=60)
        cases.append(('a run sent SIGTERM mid-check still undoes its stand-in',
                      k.returncode != 0 and git('rev-parse', 'HEAD').stdout.strip() == real
                      and git('diff', '--cached', '--name-only').stdout.split() == ['a.md'],
                      f'rc {k.returncode}: {failure_detail(k.stderr, 300)}'))
    finally:
        for k, v in env_keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_adopts_engine_written_ahead():
    """precedent_update stages, as its own, engine files a source refresh
    wrote before it ran -- but only when every one of them hashes to what
    the pinned manifest records (2026-09-27: on all four of Morgan's sets
    the refresh had already written the pinned engine, the update said
    "already current", left both files unstaged as someone else's, and
    reported DONE on an update that would have committed nothing)."""
    import hashlib
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    name = 'Update Vendors adopts the pinned engine a refresh wrote ahead of it'
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='adopt-engine-'))
    try:
        repo = tmp / 'r'
        (repo / 'tools').mkdir(parents=True)
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / 'bootstrap').mkdir()
        files = {'tools/x.py': 'x = 1\n', '.claude/hooks/g.sh': 'exit 0\n',
                 'bootstrap/b.sh': 'true\n', 'tools/y.py': 'y = 1\n'}
        for rel, text in files.items():
            (repo / rel).write_text(text, encoding='utf-8')
        sha = lambda t: hashlib.sha256(t.encode()).hexdigest()
        pin = 'a' * 40

        def manifest(commit=pin, x=files['tools/x.py']):
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'source_commit': commit,
                'sha256': {'x.py': sha(x), 'y.py': sha(files['tools/y.py'])},
                'hooks_sha256': {'g.sh': sha(files['.claude/hooks/g.sh'])},
                'engine_paths_sha256': {'bootstrap/b.sh': sha(files['bootstrap/b.sh'])},
            }), encoding='utf-8')
        m = 'tools/ENGINE_MANIFEST.json'
        before = {m, 'tools/x.py', '.claude/hooks/g.sh', 'bootstrap/b.sh', 'notes.md'}
        manifest()
        got = pu.adopt_engine_output(repo, before, pin)
        cases.append(('the manifest and every uncommitted file it tracks, matching its '
                      'hashes, are taken as the update\'s -- and nothing it does not track',
                      sorted(got) == sorted([m, 'tools/x.py', '.claude/hooks/g.sh',
                                             'bootstrap/b.sh']), got))
        manifest(x='x = 2\n')
        got = pu.adopt_engine_output(repo, before, pin)
        cases.append(('one file that differs from the manifest means nothing is taken',
                      got == [], got))
        manifest(commit='b' * 40)
        got = pu.adopt_engine_output(repo, before, pin)
        cases.append(('a manifest naming another commit than the pin is not the update\'s',
                      got == [], got))
        manifest()
        got = pu.adopt_engine_output(repo, before - {m}, pin)
        cases.append(('a committed manifest takes nothing: the refresh did not run ahead',
                      got == [], got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_vendors_migrates_hand_written_views():
    """Update Vendors moves a repository's hand-written MAP.md and GLOSSARY.md
    into their source files and generates both from then on (spec/
    GENERATED_FILES_PLAN.md step 5), through migrate_views_step. The
    failures that matter: the step silently not running, a refusal that is
    not handed to the person, headings the headline rule will now flag that
    nobody is told about, and a rerun that reports work it did not do."""
    import tempfile, shutil as _shutil
    name = 'Update Vendors migrates hand-written views and says what is left'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    if not hasattr(pu, 'migrate_views_step'):
        not_applicable(name, 'this engine predates the migration step')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / 'consumer'
        (d / 'tools').mkdir(parents=True)
        for f in (ROOT / 'tools').glob('*.py'):
            _shutil.copy2(f, d / 'tools' / f.name)
        (d / 'practices').mkdir()
        (d / 'practices' / 'zz-fixture.md').write_text(
            '---\nslug:        zz-fixture\ntitle:       A fixture practice\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  ["fixture/**"]\n'
            'occasion:    "fixture"\ngates:       []\nindex_clause: "fixture"\n'
            'checked_by:  null\ndefines:     []\nstatus:      active\n'
            'in_force_at: null\nsupersedes:  []\noverrides:   null\nadded:       "2026-10-03"\n'
            'approved_by: "Fixture, 2026-10-03"\n---\n\n## Rule\nDo it.\n\n## Why\nBecause.\n\n'
            '## Story\nOnce.\n', encoding='utf-8')
        # The practice the provenance check enforces is in force here, as it
        # is in every repository that uses Precedent.
        _shutil.copy2(ROOT / 'practices' / 'generated-artifact-provenance.md',
                      d / 'practices' / 'generated-artifact-provenance.md')
        agents = ('# Agents\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                  '<!-- END GENERATED -->\n')
        (d / 'AGENTS.md').write_text(agents, encoding='utf-8')
        hand_map = '# Repository map\n\n## Known consumers\n\nOne.\n'
        (d / 'MAP.md').write_text(hand_map, encoding='utf-8')
        (d / 'GLOSSARY.md').write_text('# Our Names\n\n| A | B |\n|---|---|\n', encoding='utf-8')
        env = dict(os.environ, GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_AUTHOR_NAME='F',
                   GIT_AUTHOR_EMAIL='f@example.com', GIT_COMMITTER_NAME='F',
                   GIT_COMMITTER_EMAIL='f@example.com')
        # The loader block as a sync leaves it, as in any real repository.
        subprocess.run([sys.executable, str(d / 'tools' / 'build_views.py'), '--repo',
                        str(d), '--agents-only'], capture_output=True, env=env)
        subprocess.run(['git', 'init', '-q', str(d)], env=env, check=True)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'fixture'], env=env, check=True)
        def provenance():
            r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                                'generated-artifact-provenance'], cwd=str(d),
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr
        rc, out = provenance()
        cases.append(('before it migrates, the full check names a hand-written map '
                      'and the command that migrates it',
                      rc != 0 and 'MAP.md: is written by hand' in out
                      and 'precedent_migrate_views.py' in out))
        rep = pu.Report()
        pu.migrate_views_step(d, rep)
        rc, out = provenance()
        cases.append(('...and after, it passes', rc == 0))
        cases.append(('the step migrates both views and reports it',
                      any(n == 'views migrated' and 'MAP.md and GLOSSARY.md' in o
                          for n, o in rep.steps)
                      and (d / 'MAP.source.md').read_text(encoding='utf-8') == hand_map))
        # Since 2026-10-03 the moved source files are internal everywhere
        # (title_case.INTERNAL_FILES): the headline rule never reaches them,
        # so the step keeps their headings and asks nothing (2026-10-04, a
        # consumer was asked to recase two files no check judges).
        cases.append(('...and asks nothing of the moved headings, which no '
                      'headline check reaches, saying it kept them',
                      not any('title_case.py --write' in why for _w, why in rep.left)
                      and any(n == 'headings kept' and 'MAP.source.md' in o
                              for n, o in rep.steps)))
        rep = pu.Report()
        pu.migrate_views_step(d, rep)
        cases.append(('a rerun reports nothing and leaves nothing',
                      not rep.steps and not rep.left))
        # A migration that would lose text: handed to the person, nothing changed.
        for f in ('MAP.source.md', 'GLOSSARY.source.md'):
            (d / f).unlink()
        (d / 'MAP.md').write_text(hand_map, encoding='utf-8')
        (d / 'AGENTS.md').write_text('# Agents with no loader markers\n', encoding='utf-8')
        rep = pu.Report()
        pu.migrate_views_step(d, rep)
        cases.append(('a migration that would lose text is left for the person, '
                      'and nothing changed',
                      any(w == 'MAP.md / GLOSSARY.md' and 'without losing text' in why
                          for w, why in rep.left)
                      and not (d / 'MAP.source.md').exists()
                      and (d / 'MAP.md').read_text(encoding='utf-8') == hand_map))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_update_vendors_updates_a_section_0_catalogue():
    """Update Vendors replaces a section 0 install's vendored catalogue, and
    never reports DONE having skipped it.

    2026-09-28, a real section 0 consumer: the catalogue step ran only where
    process/manifest.json exists, so for precedent/universal/ it did nothing,
    printed nothing, and the update said DONE; the session copied the
    catalogue by hand. INSTALL.md section 2 step 0 had said what to do all
    along. Plants the three states and owns them (practice:
    fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                         capture_output=True, text=True).stdout.strip()
    want = sorted(subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '--name-only',
                                  rev, 'practices/'], capture_output=True,
                                 text=True).stdout.split())
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-section0-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def repo_with(sources, stale=True):
        d = pathlib.Path(tempfile.mkdtemp(dir=tmp))
        subprocess.run(['git', 'init', '-q', str(d)], env=env, check=True)
        (d / 'precedent.json').write_text(json.dumps({'sources': sources}),
                                          encoding='utf-8')
        if stale:
            (d / 'precedent' / 'universal' / 'practices').mkdir(parents=True)
            (d / 'precedent' / 'universal' / 'practices' / 'retired-long-ago.md'
             ).write_text('old\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'fixture'],
                       env=env, check=True)
        return d

    try:
        universal = [{'level': 'universal', 'name': 'precedent',
                      'path': 'precedent/universal'}]
        d = repo_with(universal)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev)
        got = sorted('practices/' + p.name for p in
                     (d / 'precedent' / 'universal' / 'practices').iterdir())
        cases.append(('a stale section 0 catalogue is replaced with the source '
                      'commit\'s practices/, exactly', ok is True and got == want))
        cases.append(('...and the report says so',
                      any(n == 'catalogue' and 'replaced' in o for n, o in rep.steps)))

        # The withdrawal record travels with the catalogue, and the sync's
        # removal guard reads it there (2026-10-04: a consumer vendoring the
        # catalogue this way had all fourteen of the ladder's rules refused
        # as lost on its first update after they left universal; the record
        # only ever reached the process/upstream/ mirror).
        import precedent_resolve as _pr
        import precedent_sync_views as _psv
        vend = d / 'precedent' / 'universal'
        withdrawn = _pr.withdrawn_record(vend)
        cases.append(('the withdrawal record is vendored beside the catalogue, at '
                      'the same commit, and reads back',
                      (vend / _pr.WITHDRAWN_RECORD).is_file()
                      and withdrawn == _pr.withdrawn_record(ROOT) and len(withdrawn) >= 14))
        if withdrawn:
            gone = sorted(withdrawn)[0]
            (d / 'MANIFEST.json').write_text(json.dumps({'practices': [
                {'slug': gone, 'source': 'precedent'}]}), encoding='utf-8')
            subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
            subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'manifest'],
                           env=env, check=True)
            lost = _psv._lost_practices(d, {'practices': {'kept': {}}, 'retired': []},
                                        [{'name': 'precedent', 'level': 'universal',
                                          'path': str(vend)}], ())
            cases.append(('...so a sync against that vendored catalogue lets a '
                          'withdrawn rule go without --allow-removals',
                          (gone, 'precedent') in lost.get('withdrawn_upstream', [])
                          and (gone, 'precedent') not in lost['blocking']))

        d = repo_with(universal)
        (d / 'precedent' / 'universal' / 'practices' / 'retired-long-ago.md'
         ).write_text('edited here\n', encoding='utf-8')
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev)
        cases.append(('an uncommitted local edit is refused, not overwritten',
                      ok is None and rep.left and
                      (d / 'precedent' / 'universal' / 'practices' /
                       'retired-long-ago.md').read_text() == 'edited here\n'))

        # Committed local edits, judged against the last-synced commit.
        last = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', f'{rev}~1'],
                              capture_output=True, text=True).stdout.strip()
        at_last = subprocess.run(['git', '-C', str(ROOT), 'show',
                                  f'{last}:practices/mistakes-become-rules.md'],
                                 capture_output=True).stdout
        d = repo_with(universal, stale=False)
        tree = d / 'precedent' / 'universal' / 'practices'
        tree.mkdir(parents=True)
        (tree / 'mistakes-become-rules.md').write_bytes(at_last)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'synced'], env=env, check=True)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, last)
        cases.append(('a file exactly as last synced is replaced',
                      ok is True and not rep.left))
        (tree / 'mistakes-become-rules.md').write_bytes(at_last + b'\nA line added here.\n')
        subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'edited'], env=env, check=True)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, last)
        # Since 2026-09-29 a committed edit is resolved, not refused, when
        # the catalogue's own record names BASE -- as it does here: the replace
        # above wrote it and the commit took it. Upstream has not changed the
        # file since, so rule 1 keeps the edit and lists it
        # (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md).
        cases.append(('a COMMITTED local edit is kept, not refused, when upstream '
                      'has not changed the file since the recorded sync',
                      ok is True and not rep.left
                      and (tree / 'mistakes-become-rules.md').read_bytes().endswith(b'added here.\n')
                      and [o for o, _r, _t in rep.edits] == ['still-local']))

        d = repo_with([{'level': 'universal', 'name': 'precedent',
                        'path': '../precedent'}], stale=False)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev)
        cases.append(('with no catalogue inside the repo, the report says there '
                      'was nothing to update -- never silence',
                      ok is True and any(n == 'catalogue' and 'none vendored' in o
                                         for n, o in rep.steps)))
    except (OSError, subprocess.CalledProcessError, AttributeError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def _section0_fixture_env():
    return dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
                GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
                GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
                PRECEDENT_ALLOW_ANY_AUTHOR='1')


def _section0_repo(parent, files, env):
    """A section 0 consumer whose precedent/universal/ holds `files`
    ({relative path: bytes}), committed. -> its root."""
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(dir=parent))
    subprocess.run(['git', 'init', '-q', str(d)], env=env, check=True)
    (d / 'precedent.json').write_text(json.dumps({'sources': [
        {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'}]}),
        encoding='utf-8')
    for rel, data in files.items():
        f = d / 'precedent' / 'universal' / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
    subprocess.run(['git', '-C', str(d), 'add', '-A'], env=env, check=True)
    subprocess.run(['git', '-C', str(d), 'commit', '-qm', 'fixture'], env=env, check=True)
    return d


def check_update_vendors_trusts_the_catalogues_own_sync_commit():
    """The section 0 catalogue step judges a local edit against the commit
    the CATALOGUE was last synced from, not the engine's.

    2026-09-28, a consumer: engine vendored at one commit, catalogue at an
    older one (recorded only in prose), and the step read the engine
    manifest's source_commit as the catalogue's -- 52 files refused as local
    edits, every one byte-identical to upstream at the catalogue's real
    commit. The step now writes its own CATALOGUE_SYNC.json and reads that;
    a consumer without one has each file checked against every version
    upstream ever had at that path."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    env = _section0_fixture_env()

    def git(*a):
        return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True)

    rev = git('rev-parse', 'HEAD').stdout.decode().strip()
    now_blob = git('rev-parse', f'{rev}:practices/mistakes-become-rules.md').stdout.strip()
    older = next((c for c in git('log', '--format=%H', rev, '--',
                                 'practices/mistakes-become-rules.md').stdout.decode().split()
                  if git('rev-parse', f'{c}:practices/mistakes-become-rules.md').stdout.strip()
                  not in (b'', now_blob)), None)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-catalogue-sync-'))
    try:
        if older is None:
            raise OSError('this clone holds no older mistakes-become-rules.md to plant')
        at_older = git('show', f'{older}:practices/mistakes-become-rules.md').stdout
        # The engine was synced at `rev`, the catalogue at `older`.
        d = _section0_repo(tmp, {'practices/mistakes-become-rules.md': at_older}, env)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, rev)
        cases.append(('with no record of its own, a file equal to an older upstream '
                      'version is not a local edit', ok is True and not rep.left))
        rec = d / 'precedent' / 'universal' / 'CATALOGUE_SYNC.json'
        try:
            got = json.loads(rec.read_text(encoding='utf-8')).get('source_commit')
        except (OSError, ValueError):
            got = None
        cases.append(('the replace records the commit it synced from', got == rev))

        d = _section0_repo(tmp, {'practices/mistakes-become-rules.md': at_older + b'\nMine.\n'}, env)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, rev)
        cases.append(('...and a real local edit is still refused',
                      ok is None and any('mistakes-become-rules.md' in w for w, _ in rep.left)))

        d = _section0_repo(tmp, {
            'practices/mistakes-become-rules.md': at_older,
            'CATALOGUE_SYNC.json': json.dumps({'source_commit': older}).encode()}, env)
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev, rev)
        cases.append(('with its own record, the catalogue is judged against the '
                      'commit it names', ok is True and not rep.left
                      and any(n == 'catalogue' and older[:12] in o
                              for n, o in rep.steps)))
    except (OSError, subprocess.CalledProcessError, AttributeError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_reruns_over_its_own_output():
    """"Run this again" after a FAILED update is not refused over the
    catalogue the failed run itself wrote.

    2026-09-28: the view sync failed after the section 0 catalogue was
    replaced, and the re-run refused because precedent/universal/practices
    held uncommitted changes -- the update's own output. Output it would
    write again byte for byte is recognised; a hand edit on top of it still
    refuses."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    env = _section0_fixture_env()
    rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                         capture_output=True, text=True).stdout.strip()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-catalogue-rerun-'))
    try:
        d = _section0_repo(tmp, {'practices/retired-long-ago.md': b'old\n'}, env)
        tree = d / 'precedent' / 'universal' / 'practices'
        rep = pu.Report()
        first = pu.vendor_universal_catalogue(d, rep, rev)
        rep = pu.Report()
        again = pu.vendor_universal_catalogue(d, rep, rev)
        cases.append(('a second run over the first run\'s uncommitted output goes ahead',
                      first is True and again is True and not rep.left))
        (tree / 'mistakes-become-rules.md').write_bytes((tree / 'mistakes-become-rules.md').read_bytes()
                                            + b'\nA hand edit.\n')
        rep = pu.Report()
        ok = pu.vendor_universal_catalogue(d, rep, rev)
        cases.append(('...and a hand edit on top of that output is still refused',
                      ok is None and any('mistakes-become-rules.md' in w for w, _ in rep.left)
                      and (tree / 'mistakes-become-rules.md').read_bytes().endswith(b'hand edit.\n')))
    except (OSError, subprocess.CalledProcessError, AttributeError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def _sync_views_fixture(tmp, universal, team):
    """A consumer with a universal catalogue inside it and one shared source
    beside it, each {slug: extra frontmatter lines}. -> (repo, team_dir,
    user_config, write) where write(dir, slug, extra) (re)writes a practice."""
    repo, team_dir = tmp / 'c', tmp / 'precedent-team-x'

    def write(where, slug, extra=''):
        (where / 'practices').mkdir(parents=True, exist_ok=True)
        status = '' if 'status:' in extra else 'status: active\n'
        (where / 'practices' / f'{slug}.md').write_text(
            f'---\nslug: {slug}\ntitle: The {slug} rule\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "doing {slug}"\n'
            f'index_clause: "do {slug}"\n{status}{extra}---\n'
            f'## Rule\nDo {slug}.\n\n## Story\nIt was not done.\n', encoding='utf-8')

    for slug, extra in universal.items():
        write(repo / 'precedent' / 'universal', slug, extra)
    for slug, extra in team.items():
        write(team_dir, slug, extra)
    (repo / 'AGENTS.md').write_text(
        f'# C\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
    (repo / 'precedent.json').write_text(json.dumps({
        'format_version': 1, 'base_branch': 'main', 'visibility': 'private',
        'sources': [{'level': 'universal', 'name': 'precedent',
                     'path': 'precedent/universal'},
                    {'level': 'team', 'name': 'precedent-team-x',
                     'path': str(team_dir)}]}), encoding='utf-8')
    user = tmp / 'u.json'
    user.write_text(json.dumps({'format_version': 1}), encoding='utf-8')
    for c in (['init', '-q', '-b', 'main'],
              ['config', 'user.email', 'harness@example.com'],
              ['config', 'user.name', 'Harness']):
        subprocess.run(['git', '-C', str(repo)] + c, capture_output=True)
    return repo, team_dir, user, write


def _sync_views_run(repo, user, commit=False):
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                        '--repo', str(repo), '--user-config', str(user)],
                       capture_output=True, text=True)
    if commit:
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'catalogue'],
                       capture_output=True)
    return r


def check_update_vendors_lets_an_override_through_the_view_sync():
    """A practice a declared source now OVERRIDES is not a lost rule.

    2026-09-28, a consumer's update: the view sync refused because it "would
    remove session-title-names-the-difference (from precedent)" -- the cause
    was an individual practice carrying `overrides:` on it, a removal as
    correct as a deduplication, which the sync already lets through. A
    retirement at its own source goes through too, and so, since this item
    closed the 2026-09-14 todo, does one retired at a source whose name
    changed since the manifest was committed. A rule that simply vanished
    still refuses."""
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        repo, team, user, write = _sync_views_fixture(
            tmp, {'names-the-difference': '', 'old-rule': '', 'keeper-u': ''},
            {'abbreviates-repo': '', 'keeper-t': ''})
        r = _sync_views_run(repo, user, commit=True)
        cases.append(('the fixture syncs and commits', r.returncode == 0))
        write(team, 'abbreviates-repo', 'overrides: names-the-difference\n')
        write(repo / 'precedent' / 'universal', 'old-rule',
              'status: retired\nin_force_at: none\n')
        r = _sync_views_run(repo, user)
        cases.append(('a slug a declared source overrides does not block the sync',
                      r.returncode == 0))
        cases.append(('...and the sync names what now stands in its place',
                      'abbreviates-repo' in r.stderr
                      and 'names-the-difference' in r.stderr))
        cases.append(('a slug retired at its own source goes through as well',
                      r.returncode == 0 and 'old-rule' in r.stderr))

        _sync_views_run(repo, user, commit=True)
        (repo / 'precedent' / 'universal' / 'practices' / 'keeper-u.md').unlink()
        r = _sync_views_run(repo, user)
        cases.append(('a rule its source simply stopped producing still refuses',
                      r.returncode != 0 and 'keeper-u' in r.stderr
                      and 'whose source is still declared' in r.stderr))
        write(repo / 'precedent' / 'universal', 'keeper-u')

        # The todo's condition: a retirement at a RENAMED source is told
        # apart from a source that is gone.
        cfg = json.loads((repo / 'precedent.json').read_text())
        cfg['sources'][1]['name'] = 'precedent-team-x-renamed'
        (repo / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        write(team, 'keeper-t', 'status: retired\nin_force_at: none\n')
        write(team, 'still-here')
        r = _sync_views_run(repo, user)
        cases.append(('a slug retired at a source renamed since the commit is a '
                      'retirement, not a dropped source',
                      r.returncode == 0 and 'keeper-t' in r.stderr))
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_asks_about_a_rule_in_force_nowhere():
    """IN FORCE NOWHERE reaches the person, and the sync stops contradicting it.

    2026-09-28, a consumer's update: the sync warned that a deduplicated
    practice's forwarding address named a set this consumer does not
    declare, then in the same run said "planted-branch-rule ... now in force as
    planted-branch-rule", and Update Vendors said DONE with the warning nowhere
    in its report. Whether that deduplication is acceptable is the person's
    call; this pins only that the question reaches them."""
    import io, contextlib, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        repo, team, user, write = _sync_views_fixture(
            tmp, {'planted-branch-rule': '', 'keeper-u': ''}, {'keeper-t': ''})
        _sync_views_run(repo, user, commit=True)
        write(repo / 'precedent' / 'universal', 'planted-branch-rule',
              'status: deduplicated\nin_force_at: planted-branch-rule\n')
        r = _sync_views_run(repo, user)
        out = r.stdout + r.stderr
        cases.append(('the fixture reaches IN FORCE NOWHERE',
                      'IN FORCE NOWHERE' in out and 'planted-branch-rule' in out))
        cases.append(('the sync no longer claims the rule is in force as itself',
                      'now in force as planted-branch-rule' not in out))
        # 2026-10-17 very deep check: the line after IN FORCE NOWHERE said
        # "so the removal is correct: planted-branch-rule (... which is IN
        # FORCE NOWHERE here -- see above)".
        cases.append(('nor calls a removal into nowhere correct: it says the '
                      'rule is lost here',
                      not any('removal is correct' in ln
                              and 'planted-branch-rule' in ln
                              for ln in out.splitlines())
                      and any('LOST here' in ln and 'planted-branch-rule' in ln
                              for ln in out.splitlines())))
        found = getattr(pu, 'in_force_nowhere', lambda o: [])(out)
        cases.append(('Update Vendors picks the warning out of the sync\'s output',
                      any('planted-branch-rule' in f for f in found)))
        rep = pu.Report()
        for f in found:
            getattr(rep, 'ask', rep.leave)('IN FORCE NOWHERE', f)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rep.close()
        text = buf.getvalue()
        cases.append(('...and its report asks the person, without holding the update',
                      rc == pu.DONE and 'QUESTION' in text
                      and 'planted-branch-rule' in text))
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_defaults_headroom_floor():
    """Update Vendors writes headroom_floor_pct (5) into a
    session_load_budgets.json that declares ceilings without it, which the
    full check's session-load-budget now refuses (2026-09-28, a consumer's
    Promote). A value already there -- `false` too -- is left alone."""
    import tempfile
    pu, _pve, _pr = _update_tools()
    ensure = getattr(pu, 'ensure_headroom_floor', None)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-headroom-'))
    try:
        (tmp / 'tools').mkdir()
        reg = tmp / 'tools' / 'session_load_budgets.json'
        text = '{\n  "_comment": ["mine"],\n  "surfaces": {"AGENTS.md": {"ceiling": 900}}\n}\n'
        reg.write_text(text)
        wrote = ensure(tmp) if ensure else None
        data = json.loads(reg.read_text())
        cases.append(('a registry with ceilings and no floor gets the default 5',
                      wrote is True and data.get('headroom_floor_pct') == 5))
        cases.append(('...keeping the rest of the file as written',
                      reg.read_text().endswith(text[1:])))
        reg.write_text('{"headroom_floor_pct": false, "surfaces": {"AGENTS.md": {"ceiling": 9}}}\n')
        cases.append(('a deliberate `false` is left alone',
                      bool(ensure) and ensure(tmp) is False
                      and json.loads(reg.read_text())['headroom_floor_pct'] is False))
    except (OSError, ValueError, KeyError, TypeError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('Update Vendors defaults a missing headroom_floor_pct',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_change_is_announced():
    """Landing a change to Update Vendors' code tells the session to tell
    the person and offer a one-repository trial (Morgan, 2026-10-20: "when
    there is a change to update vendors, tell the session user there was a
    change and recommend to him he run it").

    1. A change to precedent_update.py: the note, naming the file and
       offering a session rooted in one repository.
    2. NEGATIVE CONTROL: a change to a practice file: no note.
    3. NEGATIVE CONTROL: outside BestPractice (no verify_harness.py), the
       same change: no note -- a consumer runs the update, it does not
       write it."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branches as pb
    cases = []
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

    def g(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=env,
                              capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'tools').mkdir()
        (d / 'practices').mkdir()
        (d / 'tools' / 'verify_harness.py').write_text('\n')
        (d / 'tools' / 'precedent_update.py').write_text('a = 1\n')
        (d / 'practices' / 'zz.md').write_text('x\n')
        g(d, 'init', '-q')
        g(d, 'add', '-A')
        g(d, 'commit', '-qm', 'base')
        base = g(d, 'rev-parse', 'HEAD')
        (d / 'practices' / 'zz.md').write_text('y\n')
        g(d, 'commit', '-qam', 'doc')
        doc = g(d, 'rev-parse', 'HEAD')
        (d / 'tools' / 'precedent_update.py').write_text('a = 2\n')
        g(d, 'commit', '-qam', 'update')
        upd = g(d, 'rev-parse', 'HEAD')
        note = pb.update_vendors_note(d, doc, upd)
        cases.append(('a change to Update Vendors is announced, with a '
                      'one-repository trial offered',
                      'UPDATE VENDORS CHANGED (tools/precedent_update.py)' in note
                      and 'create_session' in note and 'one repository' in note,
                      note))
        cases.append(('NEGATIVE CONTROL: a practice change is not',
                      pb.update_vendors_note(d, base, doc) == '', ''))
        (d / 'tools' / 'verify_harness.py').unlink()
        cases.append(('NEGATIVE CONTROL: outside BestPractice, nothing',
                      pb.update_vendors_note(d, doc, upd) == '', ''))
    bad = [c for c in cases if not c[1]]
    return (not bad, '; '.join(f'{n}: {x}' for n, _ok, x in bad)
            or f'{len(cases)} cases')


def check_update_keeps_the_harness_go_ahead_with_its_content():
    """2026-10-19, two consuming repos: an Update Vendors run given the
    person's words for a .claude/settings.json change stopped before the
    end, the words (one run's environment) were gone, and the practice audit
    failed the file as DRIFT until it was re-recorded by hand. The words are
    now recorded with the content they approved and read back by a rerun;
    CONTROL: changed content needs new words."""
    import subprocess as _sp
    import tempfile
    import precedent_update as pu
    cases = []
    saved = os.environ.pop(pu.HARNESS_GO_AHEAD, None)
    try:
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            g = lambda *a: _sp.run(['git', '-C', str(d), *a], capture_output=True, text=True)
            g('init', '-q'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
            (d / '.claude').mkdir()
            sj = d / '.claude' / 'settings.json'
            sj.write_text('{}\n'); g('add', '-A'); g('commit', '-qm', 'c')
            sj.write_text('{"hooks": {}}\n')
            cases.append(('without words the change is held',
                          pu.held_harness_paths(d) == {'.claude/settings.json'}
                          and pu.harness_go_ahead(d) == '', pu.held_harness_paths(d)))
            pu.record_harness_go_ahead(d, 'yes, take the hook', {'.claude/settings.json'})
            cases.append(('a rerun on the same content reads the recorded words back',
                          pu.harness_go_ahead(d) == 'yes, take the hook'
                          and pu.held_harness_paths(d) == set(), pu.harness_go_ahead(d)))
            sj.write_text('{"hooks": {"Stop": []}}\n')
            cases.append(('CONTROL: content changed since needs new words',
                          pu.harness_go_ahead(d) == ''
                          and pu.held_harness_paths(d) == {'.claude/settings.json'}, ''))
    finally:
        if saved is not None:
            os.environ[pu.HARNESS_GO_AHEAD] = saved
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'Update Vendors keeps the harness go-ahead with its content '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_update_holds_a_settings_change_and_offers_it_again():
    """A .claude/ change Update Vendors asks the person about keeps its old
    manifest baseline until their words are given, and a read-only allow
    rule left uncommitted is offered again by a rerun on the same commit.

    WHY. 2026-10-16, Update Vendors in four voice repositories: the run
    staged an allow-list change for the person's words and re-recorded
    settings.json's baseline to the new content at once, so the session
    that set the change aside, as asked, failed the practice audit as
    DRIFT; and after the person approved, the rerun said DONE with the
    change nowhere, because the refresh's early exit never looked at
    settings.json. Planted: an uncommitted settings change is held without
    the words and not with them; a held path keeps its baseline, the same
    path unheld is re-recorded; a missing read-only rule is listed, a
    declined one is not, and the refresh's early exit asks about it."""
    import hashlib
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    import precedent_vendor_engine as pve
    cases = []
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a], env=env,
                                  capture_output=True, text=True)
        git('init', '-q', '-b', 'main')
        (repo / '.claude').mkdir()
        settings = repo / '.claude' / 'settings.json'
        settings.write_text('{"permissions": {"allow": []}}\n', encoding='utf-8')
        (repo / 'process').mkdir()
        old = hashlib.sha256(settings.read_bytes()).hexdigest()
        manifest = {'entries': [{'local_path': '.claude/settings.json', 'status': 'synced',
                                 'upstream_path': 'templates/harness/claude-code/settings.json',
                                 'local_sha256': old}]}
        (repo / 'process' / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        git('add', '-A'); git('commit', '-qm', 'base')
        settings.write_text('{"permissions": {"allow": ["Bash(python3 tools/x.py:*)"]}}\n',
                            encoding='utf-8')
        saved = os.environ.pop(pu.HARNESS_GO_AHEAD, None)
        try:
            held = pu.held_harness_paths(repo)
            cases.append(('without the person\'s words the settings change is held',
                          held == {'.claude/settings.json'}, held))
            os.environ[pu.HARNESS_GO_AHEAD] = 'Commit the .claude/settings.json allow-list change'
            cases.append(('CONTROL: with their words nothing is held',
                          pu.held_harness_paths(repo) == set(), pu.held_harness_paths(repo)))
        finally:
            os.environ.pop(pu.HARNESS_GO_AHEAD, None)
            if saved is not None:
                os.environ[pu.HARNESS_GO_AHEAD] = saved
        done = pu.rebaseline_vendored_entries(repo, {'.claude/settings.json'},
                                              hold={'.claude/settings.json'})
        kept = json.loads((repo / 'process' / 'manifest.json').read_text())['entries'][0]
        cases.append(('a held change keeps the old baseline, so setting it aside is not DRIFT',
                      done == [] and kept['local_sha256'] == old, (done, kept)))
        done = pu.rebaseline_vendored_entries(repo, {'.claude/settings.json'})
        cases.append(('CONTROL: the same change, not held, is re-recorded',
                      done == ['.claude/settings.json'], done))

    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        (dest / '.claude').mkdir()
        (dest / 'tools').mkdir()
        (dest / 'tools' / 'precedent_show.py').write_text('', encoding='utf-8')
        (dest / '.claude' / 'settings.json').write_text('{}', encoding='utf-8')
        rule = 'Bash(python3 tools/precedent_show.py *)'
        missing = pve._read_only_allow_missing(dest, [rule])
        cases.append(('a read-only rule the settings lack is listed',
                      missing == [('allow', rule)], missing))
        (dest / 'precedent.json').write_text(json.dumps({pve.DECLINED_ALLOW_KEY: [rule]}),
                                             encoding='utf-8')
        cases.append(('CONTROL: a declined rule is not offered again',
                      pve._read_only_allow_missing(dest, [rule]) == [], ''))
    src = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text(encoding='utf-8')
    exit_at = src.find('engine already current with')
    cases.append(('the refresh\'s "nothing to do" exit asks whether an allow rule is missing',
                  'and not allow_pending' in src[:exit_at]
                  and src.find('allow_pending = ') < exit_at, ''))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors holds a settings change\'s baseline and offers it again '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_update_derives_engine_moves_from_git():
    """THE GAP (2026-10-14). ENGINE_PATH_MOVES was a hand-kept map: an
    engine rename without a row repointed nothing, and every consumer naming
    the old path failed its next push on rename-updates-links. Since then
    the moves are the renames git sees under tools/ between the source
    commits an update goes from and to, with the table over them for what
    git cannot see.

    A source repository renames tools/zz_old.py to tools/zz_new.py and
    docs/a.md to docs/b.md between two commits. Cases:
    A. the tools/ rename is a move, with the table's rows still there;
    B. CONTROL: a rename outside tools/ is not;
    C. a consumer naming the old path has it repointed with those moves,
       and not with the table alone (the gap);
    D. an earlier commit git cannot read leaves the table, and says so."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    env = _fixture_git_env()
    cases = []
    with tempfile.TemporaryDirectory() as td:
        src, repo = pathlib.Path(td) / 'src', pathlib.Path(td) / 'consumer'

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a], env=env,
                                  capture_output=True, text=True).stdout.strip()
        for r in (src, repo):
            r.mkdir()
            git(r, 'init', '-q')
        (src / 'tools').mkdir()
        (src / 'docs').mkdir()
        body = ''.join(f'line {i}\n' for i in range(40))
        (src / 'tools' / 'zz_old.py').write_text(body, encoding='utf-8')
        (src / 'docs' / 'a.md').write_text(body, encoding='utf-8')
        git(src, 'add', '-A'); git(src, 'commit', '-qm', 'one')
        c1 = git(src, 'rev-parse', 'HEAD')
        git(src, 'mv', 'tools/zz_old.py', 'tools/zz_new.py')
        git(src, 'mv', 'docs/a.md', 'docs/b.md')
        git(src, 'commit', '-qm', 'two')
        c2 = git(src, 'rev-parse', 'HEAD')
        moves, note = pu.engine_path_moves(src, c1, c2)
        cases.append(('A. a tools/ rename is a move, the table kept',
                      moves.get('tools/zz_old.py') == 'tools/zz_new.py' and note is None
                      and all(moves.get(o) == n for o, n in pu.ENGINE_PATH_MOVES.items()),
                      moves))
        cases.append(('B. CONTROL: a rename outside tools/ is not',
                      'docs/a.md' not in moves, moves))
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'zz_new.py').write_text(body, encoding='utf-8')
        (repo / 'AGENTS.md').write_text('Run `tools/zz_old.py` first.\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'x')
        table_only = pu.repoint_renamed_engine_paths(repo)
        derived = dict(pu.repoint_renamed_engine_paths(repo, moves))
        text = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('C. the consumer is repointed with git\'s moves, not the table alone',
                      table_only == [] and derived == {'AGENTS.md': 1}
                      and 'tools/zz_new.py' in text and 'zz_old' not in text,
                      f'{table_only} {derived} {text!r}'))
        moves_d, note_d = pu.engine_path_moves(src, '0' * 40, c2)
        cases.append(('D. an unreadable earlier commit leaves the table, and says so',
                      moves_d == pu.ENGINE_PATH_MOVES and note_d
                      and 'hand-kept' in note_d, f'{moves_d} {note_d}'))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors derives engine moves from git ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n}: {d}' for n, d in bad))

def check_shipped_tests_name_their_owner_and_fail_at_home():
    """A check test a practice source ships runs in every consuming
    repository, against that repository's tree -- and until 2026-09-25 a
    failing one there was nobody's. Sessions in consumers reported "fails on
    the base branch too, not this change" and moved on, and one test stayed
    red for days: it staged a fixture under vendor/ with a plain `git add`,
    which a consumer ignoring vendor/ refuses and its home source never did.

    Two halves, each with its own way of regressing:

    * the generated tools/checks/tests/run_all.sh names the source of every
      failing test, says a shipped one is that source's bug, and tells the
      repo-local and unknown cases apart -- and stays silent about owners
      when everything passes (the negative control);
    * tools/precedent_consumer_shape.py fails, at home, the test that passes
      in its home layout and not in a consumer's, passes the same test once
      it stages with `git add -f`, and is wired into a practice source's
      full push check."""
    import importlib.util, shutil, tempfile
    name = ('a shipped test names its owner when it fails in a consumer, '
            'and a home-only test fails at home')
    materialize_tool = ROOT / 'tools' / 'precedent_materialize.py'
    shape_tool = ROOT / 'tools' / 'precedent_consumer_shape.py'
    push_tool = ROOT / 'tools' / 'precedent_push_check.py'
    if not (materialize_tool.exists() and shape_tool.exists() and push_tool.exists()):
        not_applicable(name, 'precedent_materialize.py, precedent_consumer_shape.py '
                             'or precedent_push_check.py is absent')
        return

    def load(mod_name, path):
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    pm = load('_pm_owner', materialize_tool)
    pcs = load('_pcs_owner', shape_tool)
    ppc = load('_ppc_owner', push_tool)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-shipped-tests-'))
    # The fixture owns git's configuration: a machine's own global excludes
    # would otherwise decide whether the "passes at home" premise holds
    # (practice: fixture-owns-its-state).
    (tmp / 'gitconfig').write_text('', encoding='utf-8')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith('GIT_CONFIG_')}
    env.update(GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
               GIT_CONFIG_NOSYSTEM='1', PRECEDENT_ALLOW_ANY_AUTHOR='1',
               GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com')

    def write_test(d, fname, body):
        d.mkdir(parents=True, exist_ok=True)
        (d / fname).write_text('#!/bin/bash\n' + body + '\n', encoding='utf-8')

    try:
        # --- half 1: the generated driver names the owner -----------------
        team, local = tmp / 'team', tmp / 'local-src'
        write_test(team / 'tools' / 'checks' / 'tests', 'test_bad.sh', 'exit 1')
        write_test(team / 'tools' / 'checks' / 'tests', 'test_good.sh', 'exit 0')
        write_test(local / 'tools' / 'checks' / 'tests', 'test_local_bad.sh', 'exit 1')
        sources = [{'name': 'precedent-team-fixture', 'level': 'shared',
                    'path': str(team)},
                   {'name': 'local', 'level': 'repo-local', 'path': str(local)}]
        plan = pm._plan_checks(sources, None)
        consumer_tests = tmp / 'consumer' / 'tools' / 'checks' / 'tests'
        consumer_tests.mkdir(parents=True)
        for rel_label, filename, _src, data in plan:
            if rel_label == 'checks/tests':
                (consumer_tests / filename).write_bytes(data)
        driver_text = (consumer_tests / 'run_all.sh').read_text(encoding='utf-8')
        # The table agrees with what the manifest records for each test: the
        # manifest's checks[] source comes from this same plan entry.
        table_ok = all(f"{fn}) owner={src};" in driver_text
                       for rel, fn, src, _d in plan
                       if rel == 'checks/tests' and fn != 'run_all.sh')
        cases.append(("the driver's owner table carries every materialized "
                      "test's source, as MANIFEST.json's checks[] records it",
                      table_ok))
        # A test nobody materialized: dropped in by hand, failing.
        write_test(consumer_tests, 'test_stray.sh', 'exit 1')
        r = subprocess.run(['bash', 'run_all.sh'], cwd=consumer_tests,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        cases.append(('the driver still exits 1 when a test fails',
                      r.returncode == 1, f'exit {r.returncode}'))
        cases.append(('a failing shipped test is named with its source and level',
                      "FAILED: test_bad.sh -- shipped by source "
                      "'precedent-team-fixture' (shared level)" in out))
        cases.append(('the driver says a shipped failure is not to be recorded '
                      'as pre-existing',
                      'Never record it here as pre-existing' in out))
        cases.append(("a repo-local test's failure is this repo's own to fix",
                      "FAILED: test_local_bad.sh -- this repo's own repo-local "
                      "source (local/): fix it here" in out))
        cases.append(('a test no source shipped is called out as such, not '
                      'pinned on a source',
                      'FAILED: test_stray.sh -- no source shipped it' in out))
        cases.append(('a passing test is never named as failed',
                      'FAILED: test_good.sh' not in out))
        found = ppc._finding_lines(out.splitlines())
        cases.append(("the push check's finding extraction carries the owner "
                      "line, so a refused push shows whose test failed",
                      any("shipped by source 'precedent-team-fixture'" in l
                          for l in found)))
        # Negative control: nothing failing, nothing said about owners.
        for f in ('test_bad.sh', 'test_local_bad.sh', 'test_stray.sh'):
            (consumer_tests / f).unlink()
        r = subprocess.run(['bash', 'run_all.sh'], cwd=consumer_tests,
                           capture_output=True, text=True, env=env)
        cases.append(('all passing: exit 0 and no ownership summary at all',
                      r.returncode == 0 and 'who owns each' not in r.stdout
                      and 'pre-existing' not in r.stdout))

        # --- half 2: consumer-shaped run fails a home-only test at home ---
        def source_repo(label, add_cmd):
            d = tmp / label
            write_test(d / 'tools' / 'checks' / 'tests', 'test_plant.sh',
                       'set -e\ns="$(mktemp -d)"\ngit init -q "$s"\n'
                       'mkdir -p "$s/vendor"\necho x > "$s/vendor/THIRD_PARTY.md"\n'
                       f'git -C "$s" {add_cmd} vendor/THIRD_PARTY.md\n'
                       'rm -rf "$s"\necho ok')
            subprocess.run(['git', 'init', '-q', str(d)], env=env,
                           capture_output=True)
            return d

        plain = source_repo('src-plain-add', 'add')
        forced = source_repo('src-forced-add', 'add -f')
        home = subprocess.run(['bash', 'test_plant.sh'],
                              cwd=plain / 'tools' / 'checks' / 'tests',
                              capture_output=True, text=True, env=env)
        cases.append(('premise: the plain-add test passes in its home layout',
                      home.returncode == 0, failure_detail(home.stdout + home.stderr, 200)))
        r = subprocess.run([sys.executable, str(shape_tool), '--repo', str(plain)],
                           capture_output=True, text=True, env=env)
        cases.append(('the consumer-shaped run fails it, naming the test and the '
                      'cause class',
                      r.returncode == 1 and 'FAILED: test_plant.sh -- fails in '
                      'a consumer-shaped copy of this repository' in r.stdout
                      and 'git add -f' in r.stdout,
                      f'exit {r.returncode}: {failure_detail(r.stdout, 300)}'))
        r = subprocess.run([sys.executable, str(shape_tool), '--repo', str(forced)],
                           capture_output=True, text=True, env=env)
        cases.append(('the same test staging with `git add -f` passes the '
                      'consumer-shaped run',
                      r.returncode == 0 and 'all 1 passed' in r.stdout,
                      f'exit {r.returncode}: {failure_detail(r.stdout, 300)}'))
        bare = tmp / 'no-tests'
        subprocess.run(['git', 'init', '-q', str(bare)], env=env, capture_output=True)
        r = subprocess.run([sys.executable, str(shape_tool), '--repo', str(bare)],
                           capture_output=True, text=True, env=env)
        cases.append(('a repo with no tests: exit 0, and it says there was '
                      'nothing to run',
                      r.returncode == 0 and 'nothing to run' in r.stdout))
        r = subprocess.run([sys.executable, str(shape_tool), '--repo',
                            str(tmp / 'team')], capture_output=True, text=True,
                           env=dict(env, GIT_CEILING_DIRECTORIES=str(tmp)))
        cases.append(('outside a git checkout: exit 2, said so',
                      r.returncode == 2 and 'not inside a git checkout' in r.stderr))
        base = {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'a.b',
                'GIT_CONFIG_VALUE_0': 'c'}
        merged = pcs.consumer_env('/x/ignore', base=base)
        cases.append(('the ignores are appended to GIT_CONFIG_COUNT entries '
                      'already set, never replacing them',
                      merged.get('GIT_CONFIG_COUNT') == '2'
                      and merged.get('GIT_CONFIG_KEY_0') == 'a.b'
                      and merged.get('GIT_CONFIG_KEY_1') == 'core.excludesFile'
                      and merged.get('GIT_CONFIG_VALUE_1') == '/x/ignore'))
        cases.append(('every test runs with no bytecode cache, set once here, '
                      'so no test needs its own PYTHONDONTWRITEBYTECODE',
                      merged.get('PYTHONDONTWRITEBYTECODE') == '1'))

        names = {kind: [n for n, _a, _r in ppc.PUSH_CHECKS[kind]]
                 for kind in ppc.PUSH_CHECKS}
        cases.append(("a practice source's full push check runs the "
                      'consumer-shaped suite, right after its own',
                      'consumer_shape' in names['source']
                      and names['source'].index('consumer_shape')
                      == names['source'].index('deep_check') + 1
                      and 'consumer_shape' not in ppc.BASIC_CHECKS))
        cases.append(('it ships with the engine every kind vendors',
                      "'precedent_consumer_shape.py'" in
                      (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text(
                          encoding='utf-8')))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_update_stages_what_a_late_step_writes():
    """Update Vendors stages what a step after its staging step wrote.

    2026-10-10, a consumer taking the update: the records step moved a
    record from process/retired_vocabulary.json into precedent.json after
    everything had been staged, so the update said DONE with both files
    modified and unstaged. The update now stages late output at the end,
    and still leaves alone what was uncommitted before it ran.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        env = _fixture_git_env()
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                      text=True, env=env)
        g('init', '-q', '-b', 'main')
        (repo / 'process').mkdir()
        (repo / 'process' / 'MIGRATION.md').write_text('We moved off OldPack.\n')
        vpath = repo / 'process' / 'retired_vocabulary.json'
        vpath.write_text(json.dumps({'terms': ['OldPack'],
                                     'exempt_files': ['process/MIGRATION.md']}, indent=2) + '\n')
        (repo / 'precedent.json').write_text(json.dumps({'sources': []}, indent=2) + '\n')
        (repo / 'notes.md').write_text('mine\n')
        g('add', '-A'); g('commit', '-qm', 'base')
        (repo / 'notes.md').write_text('mine, unfinished\n')
        before = pu.dirty_paths(repo)
        (repo / 'engine.txt').write_text('written by the update\n')
        pu.stage_update(repo, before)
        moved = pu.adopt_listed_records(repo, {'process/MIGRATION.md'})
        unstaged = set(g('diff', '--name-only').stdout.split())
        cases.append(('the fixture: the records step leaves both files unstaged, as reported',
                      moved == ['process/MIGRATION.md']
                      and {'precedent.json', 'process/retired_vocabulary.json'} <= unstaged,
                      str(unstaged)))
        late = pu.stage_late_output(repo, before)
        unstaged = set(g('diff', '--name-only').stdout.split())
        cached = set(g('diff', '--cached', '--name-only').stdout.split())
        cases.append(('THE DISCRIMINATING CASE: the late writes are staged',
                      {'precedent.json', 'process/retired_vocabulary.json'} <= cached
                      and sorted(late) == ['precedent.json', 'process/retired_vocabulary.json'],
                      f'late={late} cached={cached}'))
        cases.append(('the person\'s own unstaged edit is left as it was',
                      unstaged == {'notes.md'} and 'notes.md' not in cached, str(unstaged)))
        src = pathlib.Path(pu.__file__).read_text(encoding='utf-8')
        cases.append(('the update calls it after its last writing step, before the check',
                      src.index('late = stage_late_output(repo, before)')
                      > src.index('adopted = adopt_listed_records(')
                      and src.index('late = stage_late_output(repo, before)')
                      < src.index('return closing_check(repo, rep, skip_check)'), ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors stages what a late step writes ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_one_list_declares_a_record():
    """precedent.json's record_paths is the one list of records: the
    retired-names scrub reads it too, and Update Vendors moves a flagged
    file the person already listed in retired_vocabulary.json's
    exempt_files over to it.

    2026-10-10, a consumer (Morgan: "that is a good suggestion for
    upstream"): its migration record was exempt from the old-names scrub
    through exempt_files, and the citation check, which reads record_paths,
    still flagged six old practice names in it. Silencing both meant naming
    the file twice. exempt_files is NOT read as records: it also lists a
    materialized practices/ tree and live items that must name a retired
    secret, which are not records."""
    import tempfile
    name = 'one list declares a record'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    saved = pc.ROOT
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            (repo / 'process').mkdir()
            (repo / 'todo').mkdir()
            (repo / 'process' / 'MIGRATION.md').write_text(
                'We moved off OldPack on 2026-09-24.\n', encoding='utf-8')
            (repo / 'todo' / 'delete-secret.md').write_text(
                'Delete the OldPack secret.\n', encoding='utf-8')
            vocab = {'_comment': 'why', 'terms': ['OldPack'],
                     'exempt_files': ['process/MIGRATION.md', 'todo/delete-secret.md',
                                      'practices/']}
            vpath = repo / 'process' / 'retired_vocabulary.json'
            vpath.write_text(json.dumps(vocab) + '\n', encoding='utf-8')
            cpath = repo / 'precedent.json'
            cpath.write_text(json.dumps({'sources': []}, indent=2) + '\n', encoding='utf-8')
            pc.ROOT = repo

            def scrubbed():
                return sorted({f.where.split(':')[0] for f in pc._repo_retired_terms(vpath, None)})
            vpath.write_text(json.dumps({'terms': ['OldPack'], 'exempt_files': []}) + '\n',
                             encoding='utf-8')
            cases.append(('control: with no list, the scrub flags the record',
                          'process/MIGRATION.md' in scrubbed()))
            cpath.write_text(json.dumps({'sources': [], 'record_paths': [
                {'path': 'process/MIGRATION.md', 'reason': 'r'}]}, indent=2) + '\n',
                encoding='utf-8')
            cases.append(('THE DISCRIMINATING CASE: declared in record_paths alone, '
                          'the scrub leaves it', 'process/MIGRATION.md' not in scrubbed()))
            cases.append(('...and still flags a file on no list',
                          'todo/delete-secret.md' in scrubbed()))
            cpath.write_text(json.dumps({'sources': []}, indent=2) + '\n', encoding='utf-8')
            vpath.write_text(json.dumps(vocab) + '\n', encoding='utf-8')
            moved = pu.adopt_listed_records(repo, {'process/MIGRATION.md', 'tools/x.py'})
            cfg = json.loads(cpath.read_text(encoding='utf-8'))
            after = json.loads(vpath.read_text(encoding='utf-8'))
            cases.append(('Update Vendors moves the flagged, already-listed file to '
                          'record_paths, with a reason',
                          moved == ['process/MIGRATION.md']
                          and [e['path'] for e in cfg.get('record_paths', [])]
                          == ['process/MIGRATION.md']
                          and all(e.get('reason') for e in cfg['record_paths'])))
            cases.append(('...takes it off exempt_files, in the file\'s own one-line layout',
                          after['exempt_files'] == ['todo/delete-secret.md', 'practices/']
                          and vpath.read_text(encoding='utf-8').count('\n') == 1))
            cases.append(('...and never moves a directory or a file it did not flag',
                          'practices/' in after['exempt_files']
                          and 'todo/delete-secret.md' in after['exempt_files']))
            cases.append(('the scrub still leaves the moved record alone',
                          'process/MIGRATION.md' not in scrubbed()))
            cases.append(('a second run moves nothing',
                          pu.adopt_listed_records(repo, {'process/MIGRATION.md'}) == []))
    finally:
        pc.ROOT = saved
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_frontmatter_field_order_fixer():
    """frontmatter_yaml.reorder_fields: puts a practice's frontmatter into
    FIELD_ORDER and changes nothing else. On 2026-09-26 it rewrote 49 of 151
    practices here, so "nothing else" is the property that matters: a folded
    continuation line, a comment and its field, the alignment padding and
    the body all have to come through byte for byte.

    Stated cases, each with the shape it covers (practice:
    checks-plant-their-state), and a control that shows the finding comes
    from the order and not from the parse (practice:
    control-asserts-which-failure)."""
    fy = frontmatter_yaml
    cases = []
    body = '## Rule\nDo it.\n\n## Why\nBecause: yes.\nslug: not-a-field\n'
    messy = ('---\nslug:        fx\ntitle:       T\n'
             'ships:       []\n'
             'applies_to:  ["**"]\n'
             '# says why checked_by is null\n'
             'checked_by:  null\n'
             'approved_by: "a long approval folded\n'
             '   onto a second line"\n'
             'custom_field: 1\n'
             'tier:        on-demand\n'
             '---\n' + body)
    fixed = fy.reorder_fields(messy)
    want = ('---\nslug:        fx\ntitle:       T\n'
            'tier:        on-demand\n'
            'applies_to:  ["**"]\n'
            '# says why checked_by is null\n'
            'checked_by:  null\n'
            'ships:       []\n'
            'approved_by: "a long approval folded\n'
            '   onto a second line"\n'
            'custom_field: 1\n'
            '---\n' + body)
    cases.append(('a misordered file comes out in FIELD_ORDER, a comment '
                  'travelling with the field below it, a folded value with its '
                  'key, an unlisted field last, the body untouched',
                  fixed == want, repr(fixed)))
    cases.append(('the checker names the first field out of place',
                  '`applies_to:` comes after `ships:`' in (fy.field_order_problem(messy) or ''),
                  repr(fy.field_order_problem(messy))))
    cases.append(('the fixed file reads as in order, and fixing it again is a '
                  'no-op', fy.field_order_problem(fixed) is None
                  and fy.reorder_fields(fixed) == fixed, repr(fixed)))
    cases.append(('an unlisted field is reported by name',
                  fy.unlisted_fields(messy) == ['custom_field'],
                  repr(fy.unlisted_fields(messy))))
    dup = '---\nslug: a\ntier: x\nslug: b\n---\n'
    cases.append(('a repeated key is reported and left alone -- which copy is '
                  'meant is a person\'s call',
                  'more than once' in (fy.field_order_problem(dup) or '')
                  and fy.reorder_fields(dup) == dup, repr(fy.field_order_problem(dup))))
    cases.append(('QUIET: a file with no frontmatter is neither reported nor '
                  'rewritten', fy.field_order_problem(body) is None
                  and fy.reorder_fields(body) == body, ''))
    import precedent_move
    moved = precedent_move._rewrite_frontmatter(
        fixed, {'strength': 'assented', 'in_force_at': 'elsewhere'})
    cases.append(('precedent_move inserts a field the file lacked where '
                  'FIELD_ORDER puts it, not at the end -- appending was one of '
                  'the ways the order drifted',
                  fy.field_order_problem(moved.replace('custom_field: 1\n', '')) is None
                  and 'in_force_at: elsewhere\napproved_by:' in moved, repr(moved)))
    saved = fy.FIELD_ORDER
    try:
        fy.FIELD_ORDER = ('tier', 'slug', 'title', 'applies_to', 'checked_by',
                          'ships', 'approved_by')
        control = fy.field_order_problem(want)
    finally:
        fy.FIELD_ORDER = saved
    cases.append(('CONTROL: the same in-order file reads as out of order once '
                  'FIELD_ORDER says otherwise, so the verdict comes from the '
                  'constant', bool(control), repr(control)))
    # Update Vendors' tidy (practice: format-rules-grandfather): it fixes a
    # project repo's own source files in local/practices/, never the copy
    # the view sync renders into practices/, and leaves a file whose order
    # the fixer cannot settle for the warning to name.
    import tempfile, shutil
    import precedent_update as pu
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='tidy-order-'))
    try:
        (tmp / 'local' / 'practices').mkdir(parents=True)
        (tmp / 'practices').mkdir()
        out_of_order = ('---\nslug: a\ntitle: A\nindex_required: false\n'
                        'index_clause: "x"\nstatus: active\n---\n## Rule\nr\n')
        repeated = ('---\nslug: b\ntitle: B\ntitle: B2\nindex_required: '
                    'false\nindex_clause: "x"\n---\n## Rule\nr\n')
        (tmp / 'local/practices/a.md').write_text(out_of_order, encoding='utf-8')
        (tmp / 'local/practices/b.md').write_text(repeated, encoding='utf-8')
        (tmp / 'practices/a.md').write_text(out_of_order, encoding='utf-8')
        done = pu.tidy_field_order(tmp, 'consumer')
        cases.append(('Update Vendors tidies a project repo\'s own practice in '
                      'local/practices/ and leaves the rendered copy and an '
                      'unfixable file alone',
                      done == ['local/practices/a.md']
                      and not fy.field_order_problem(
                          (tmp / 'local/practices/a.md').read_text(encoding='utf-8'))
                      and (tmp / 'practices/a.md').read_text(encoding='utf-8') == out_of_order
                      and (tmp / 'local/practices/b.md').read_text(encoding='utf-8') == repeated,
                      repr(done)))
        cases.append(('in a practice set, whose practices/ IS the source, it '
                      'tidies practices/ too',
                      pu.tidy_field_order(tmp, 'source') == ['practices/a.md'], ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'frontmatter_yaml reorders practice frontmatter into FIELD_ORDER and '
          f'changes nothing else ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_merge_refreshes_stale_views_as_its_own_commit():
    """At a merge, views a moved source left stale are regenerated as a
    commit of their own -- and a refresh that would change hooks or
    settings is taken back and asks for the person's go-ahead instead.

    WHY. 2026-10-06: the push check stopped refusing a stale view a push
    did not bring, so the refresh it points at has to happen somewhere:
    here, where the vendor update already rides along. And auto mode holds
    a commit that changes .claude/ until the person says yes."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_merge_vendors as pmv
    env = _fixture_git_env()
    for harness in (False, True):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                          capture_output=True, text=True)
            g('init', '-q', '-b', 'main')
            (repo / 'tools').mkdir()
            (repo / '.claude').mkdir()
            (repo / '.claude' / 'settings.json').write_text('{}\n', encoding='utf-8')
            (repo / 'tools' / 'precedent_sync_views.py').write_text(
                'import pathlib, sys\n'
                'p = pathlib.Path("AGENTS.md")\n'
                'if "--check" in sys.argv:\n'
                '    sys.exit(0 if p.read_text() == "fresh\\n" else 1)\n'
                'p.write_text("fresh\\n")\n'
                'pathlib.Path("practices").mkdir(exist_ok=True)\n'
                'pathlib.Path("practices/new.md").write_text("x\\n")\n'
                + ('pathlib.Path(".claude/settings.json").write_text("{\\"hooks\\": {}}\\n")\n'
                   if harness else ''), encoding='utf-8')
            (repo / 'AGENTS.md').write_text('stale\n', encoding='utf-8')
            (repo / 'notes.txt').write_text('mine, untracked\n', encoding='utf-8')
            g('add', 'tools', '.claude', 'AGENTS.md'); g('commit', '-qm', 'base')
            head = g('rev-parse', 'HEAD').stdout.strip()
            saved_env = os.environ.pop(pmv.HARNESS_GO_AHEAD, None)
            saved_git = {k: os.environ.get(k) for k in env if k.startswith('GIT_')}
            os.environ.update({k: v for k, v in env.items() if k.startswith('GIT_')})
            try:
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    pmv.refresh_views(repo)
                said = buf.getvalue()
                moved = g('rev-parse', 'HEAD').stdout.strip() != head
                files = g('show', '--name-only', '--format=', 'HEAD').stdout.split()
                clean = g('status', '--porcelain', '--untracked-files=no').stdout == ''
                if not harness:
                    check('a stale view is refreshed in a commit of its own, '
                          'taking the new file and leaving untracked files alone',
                          moved and sorted(files) == ['AGENTS.md', 'practices/new.md']
                          and 'VIEWS: refreshed' in said
                          and (repo / 'notes.txt').is_file(), said + repr(files))
                else:
                    check('a refresh that changes .claude/ is taken back and asks '
                          'for the person\'s go-ahead',
                          not moved and clean and 'NOT REFRESHED' in said
                          and pmv.HARNESS_GO_AHEAD in said
                          and not (repo / 'practices' / 'new.md').exists(), said)
                    os.environ[pmv.HARNESS_GO_AHEAD] = 'yes, wire it'
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        pmv.refresh_views(repo)
                    msg = g('log', '-1', '--format=%B').stdout
                    check('...and with the person\'s words it commits, quoting them',
                          'yes, wire it' in msg and 'VIEWS: refreshed' in buf.getvalue(),
                          buf.getvalue() + msg)
            finally:
                os.environ.pop(pmv.HARNESS_GO_AHEAD, None)
                if saved_env is not None:
                    os.environ[pmv.HARNESS_GO_AHEAD] = saved_env
                for k, v in saved_git.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


def check_update_asks_before_changing_hooks():
    """Update Vendors names a change to hooks or settings as a question for
    the person, printed ahead of the commit, instead of meeting auto mode at
    it -- and still finishes, since it is not the repo's call (2026-10-06)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        (repo / 'a.md').write_text('a\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'x.py').write_text('', encoding='utf-8')
        g('add', '-A')
        check('CONTROL: an update touching no hook or setting asks nothing',
              pu.harness_changes(repo) == [], '')
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / '.claude' / 'hooks' / 'h.sh').write_text('', encoding='utf-8')
        g('add', '-A')
        got = pu.harness_changes(repo)
        ask = pu.harness_ask(got)
        check('a staged hook is named, with the go-ahead to ask for',
              got == ['.claude/hooks/h.sh'] and pu.HARNESS_GO_AHEAD in ask
              and '.claude/hooks/h.sh' in ask, repr(got) + ask)
        rep = pu.Report()
        rep.ask('hooks and settings', ask)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rep.close()
        check('...as a question for the person: the update still ends DONE, '
              'and the question is printed ahead of the commit',
              rc == pu.DONE and 'QUESTIONS FOR THE PERSON' in buf.getvalue()
              and '.claude/hooks/h.sh' in buf.getvalue(), failure_detail(buf.getvalue(), 600))


def check_update_keeps_hook_hashes_with_the_held_hooks():
    """While the hooks-and-settings question waits on the person's words,
    the engine manifest keeps the committed hooks' hashes, and the question
    only promises what the go-ahead run really records.

    WHY (2026-10-17, two consumers' updates). The refresh wrote the NEW
    hooks' hashes into tools/ENGINE_MANIFEST.json at once; committed
    without the held hooks, as the question invited, the next run called
    the old hooks "your local edit" and would not replace them. The
    question also said the go-ahead run "records these files' new
    baselines" for a .claude/settings.json that had none, and that
    committing without them "leaves nothing red", when the push check
    refused the push. And auto mode refused the rerun even with the
    person's sentence.

    Negative control: on staging's code there is no hold_hook_hashes or
    harness_baselines, and the question carries the old claims."""
    import tempfile, hashlib, json as _json
    name = 'an update keeps hook hashes with the held hooks'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    hold = getattr(pu, 'hold_hook_hashes', None)
    base = getattr(pu, 'harness_baselines', None)
    cases.append(('the updater has the hold and the baseline reader',
                  callable(hold) and callable(base)))
    if callable(hold) and callable(base):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_COMMITTER_NAME='T',
                       GIT_AUTHOR_EMAIL='t@example.invalid',
                       GIT_COMMITTER_EMAIL='t@example.invalid')

            def g(*a):
                return subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
            g('init', '-q')
            (repo / '.claude' / 'hooks').mkdir(parents=True)
            (repo / 'tools').mkdir()
            hook = repo / '.claude' / 'hooks' / 'h.sh'
            hook.write_text('old\n', encoding='utf-8')
            old = hashlib.sha256(b'old\n').hexdigest()
            mf = repo / 'tools' / 'ENGINE_MANIFEST.json'
            mf.write_text(_json.dumps({'hook_files': ['h.sh'],
                                       'hooks_sha256': {'h.sh': old}}), encoding='utf-8')
            (repo / '.claude' / 'settings.json').write_text('{}\n', encoding='utf-8')
            g('add', '-A')
            g('commit', '-q', '-m', 'base')
            # The refresh: new hook, new hash, a settings change; all staged.
            hook.write_text('new\n', encoding='utf-8')
            new = hashlib.sha256(b'new\n').hexdigest()
            mf.write_text(_json.dumps({'hook_files': ['h.sh'],
                                       'hooks_sha256': {'h.sh': new}}), encoding='utf-8')
            (repo / '.claude' / 'settings.json').write_text('{"a": 1}\n', encoding='utf-8')
            g('add', '-A')
            paths = pu.harness_changes(repo)
            done = hold(repo, paths, approved=False)
            staged = _json.loads(g('show', ':tools/ENGINE_MANIFEST.json').stdout or '{}')
            cases.append(('without the words, the staged manifest keeps the '
                          'committed hook\'s hash',
                          done == ['h.sh']
                          and (staged.get('hooks_sha256') or {}).get('h.sh') == old,
                          (done, staged)))
            done = hold(repo, paths, approved=True)
            staged = _json.loads(g('show', ':tools/ENGINE_MANIFEST.json').stdout or '{}')
            cases.append(('with the words, it records the staged hook\'s own hash',
                          done == ['h.sh']
                          and (staged.get('hooks_sha256') or {}).get('h.sh') == new,
                          (done, staged)))
            has, none = base(repo, paths)
            cases.append(('settings.json, with no recorded baseline, is said to '
                          'have none; the hook has one',
                          has == ['.claude/hooks/h.sh']
                          and none == ['.claude/settings.json'], (has, none)))
            ask = pu.harness_ask(paths, baselines=(has, none))
            cases.append(('the question promises no baseline that does not exist',
                          'records the new baselines of .claude/hooks/h.sh' in ask
                          and 'has no baseline to record for .claude/settings.json' in ask,
                          ask))
            cases.append(('...never says committing without them leaves nothing '
                          'red, and says to get the words first',
                          'leaves nothing red' not in ask
                          and 'Get the words before committing' in ask, ask))
            cases.append(('...and says auto mode may still need the one permission '
                          'prompt approved', 'permission prompt' in ask, ask))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + str(d)[:200] + ')' if d else ''}" for n, d in bad))


def check_update_asks_for_words_that_name_the_commit():
    """The hooks-and-settings question Update Vendors puts to the person,
    and the merge step's take-back of the same change, hand the session the
    exact sentence the person says -- naming the files and the change --
    and never ask for a bare yes.

    WHY. 2026-10-15, a consumer's Update Vendors: the question said "their
    yes is what lets the commit through"; the person answered "Yes approved.
    Booked", and auto mode refused the commit of .claude/settings.json as
    [Self-Modification]. "Commit the .claude/settings.json allow-list
    change" went through first time.

    Negative control, measured 2026-10-15: on staging's code the stated
    cases fail -- there is no harness_approval, and the question asks for a
    yes."""
    import inspect, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    import precedent_merge_vendors as pmv
    env = _fixture_git_env()
    cases = []
    approval = getattr(pu, 'harness_approval', None)
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        (repo / '.claude').mkdir()
        sj = repo / '.claude' / 'settings.json'
        sj.write_text(json.dumps({'permissions': {'allow': []}}) + '\n',
                      encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        sj.write_text(json.dumps({'permissions': {'allow': [
            'Bash(python3 tools/precedent_show.py:*)']}}) + '\n', encoding='utf-8')
        g('add', '-A')
        paths = pu.harness_changes(repo)
        cases_now = pu.harness_cases(repo, paths)
        ask = pu.harness_ask(paths, cases=cases_now)
        want = 'Commit the .claude/settings.json allow-list change'
        said = approval(paths, cases=cases_now) if approval else None
        cases.append(('an allow-list change is named as one, with its file',
                      said == want, repr(said)))
        cases.append(('...and the question gives that sentence to say',
                      f'To approve, say: "{want}"' in ask, ask))
        cases.append(('...and never asks for a yes, or says one is enough',
                      'yes-or-no' in ask and 'their yes is what' not in ask.lower()
                      and 'says yes' not in ask, ask))
        words = getattr(pmv, 'approval_words', None)
        got = words(repo, paths) if words else None
        cases.append(('the merge step, which takes the change back, has the '
                      'same sentence', got == want, repr(got)))
        cases.append(('...read before the take-back, from the staged change',
                      words is not None and 'approval_words(repo, harness)'
                      in inspect.getsource(pmv.refresh_views)
                      and 'approval_words(repo, harness)' in inspect.getsource(pmv.run),
                      ''))
    if approval:
        hook = approval(['.claude/hooks/h.sh'], cases=['a new hook file, h.sh'])
        cases.append(('a new hook file is named as one',
                      hook == 'Commit the .claude/hooks/h.sh hook file change', hook))
        two = approval(['.claude/settings.json', '.claude/hooks/h.sh'],
                       cases=['settings.json gains an entry for h.sh (Stop)',
                              'a new hook file, h.sh'])
        cases.append(('two files and two kinds are both named',
                      two == 'Commit the .claude/settings.json and '
                             '.claude/hooks/h.sh hook wiring and hook file change', two))
        last = approval(['.claude/hooks/h.sh'], last=True)
        cases.append(('the move to stubs is named as that',
                      'permanent stubs' in last and '.claude/hooks/h.sh' in last, last))
        cases.append(('...and its question gives the sentence too',
                      f'To approve, say: "{last}"' in pu.harness_ask(
                          ['.claude/hooks/h.sh'], last=True), ''))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors asks for words that name a hooks-or-settings commit, '
          f'never a yes ({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_update_rerun_after_left_for_you_still_drops_a_deleted_set():
    """Update Vendors, run again after a run that dropped a deleted set and
    stopped LEFT FOR YOU, still takes the view sync's removal of what that
    set held -- it does not refuse every rerun.

    WHY. 2026-10-10, a consumer's update to BestPractice 78d970b: the first
    run dropped precedent-shared-repo-maintenance and
    precedent-shared-working-style from precedent.json and stopped LEFT FOR
    YOU. The rerun found nothing left to drop, while the committed
    MANIFEST.json still recorded their practices, so the view sync refused
    every rerun ("source name is not among the sources precedent.json
    declares"). removals_this_update_caused only counted a set the run in
    hand had dropped.

    Negative control, measured 2026-10-10: on staging's code the second run
    fails on that refusal."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    fx = _LocalEditsFixture('precedent-rerun-dropped-')
    cases = []
    gone = 'precedent-shared-repo-maintenance'
    try:
        listed = {e.get('name') for e in json.loads(
            (ROOT / 'tools' / 'deleted_sets.json').read_text(encoding='utf-8'))['sets']}
        cases.append((f'CONTROL: {gone} is on the engine\'s deleted-set record',
                      gone in listed, sorted(listed)))
        repo = fx.consumer('c', {'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
            {'level': 'shared', 'name': gone, 'path': '../gone-set'}]})
        fx.sh(sys.executable, str(repo / 'tools' / 'precedent_sync_views.py'),
              '--repo', str(repo), cwd=repo)
        # What the repository held from before the set was listed: one of
        # its practices, materialized and recorded in MANIFEST.json.
        man = json.loads((repo / 'MANIFEST.json').read_text(encoding='utf-8'))
        text = (ROOT / 'practices' / 'park-it.md').read_text(encoding='utf-8')
        text = re.sub(r'^slug: .*$', 'slug: fixture-gone-rule', text, count=1, flags=re.M)
        (repo / 'practices' / 'fixture-gone-rule.md').write_text(text, encoding='utf-8')
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        man['practices'].append({'level': 'shared', 'links_rewritten': False,
                                 'sha256_16': h, 'slug': 'fixture-gone-rule',
                                 'source': gone, 'source_sha256_16': h})
        (repo / 'MANIFEST.json').write_text(json.dumps(man, indent=2) + '\n',
                                            encoding='utf-8')
        fx.commit(repo, 'held a rule from the set before it was deleted')
        ref = fx.seeded_from(repo)
        rc1, out1 = fx.update(repo, ref)
        declared = [x.get('name') for x in json.loads(
            (repo / 'precedent.json').read_text(encoding='utf-8'))['sources']]
        cases.append(('CONTROL: the first run drops the set and stops LEFT FOR '
                      'YOU, committing nothing',
                      rc1 == 1 and 'LEFT FOR YOU' in out1 and gone not in declared
                      and 'fixture-gone-rule' in out1, (rc1, failure_detail(out1, 1500))))
        rc2, out2 = fx.update(repo, ref)
        cases.append(('the rerun takes the removal of what the dropped set held, '
                      'instead of refusing it',
                      'not among the sources precedent.json declares' not in out2
                      and 'view sync failed' not in out2
                      and not (repo / 'practices' / 'fixture-gone-rule.md').exists(),
                      (rc2, failure_detail(out2, 2000))))
        # And each source of "dropped" on its own.
        cases.append(('an earlier run\'s drop is in the run-to-run record',
                      gone in pu.sets_this_update_dropped(repo, [])
                      if hasattr(pu, 'sets_this_update_dropped') else False, ''))
        if hasattr(pu, 'record_dropped_sets'):
            pu.clear_pin(repo)
            cases.append(('...and clearing the pin clears it',
                          'dropped_sets' not in pu._read_record(repo), pu._read_record(repo)))
            saved = pu.pve._person_sets
            try:
                pu.pve._person_sets = lambda: ({'listed-set': {}}, [])
                got = pu.sets_this_update_dropped(repo, [])
                cases.append(('a set on a deleted-set record counts, with no record '
                              'of this run', 'listed-set' in got, got))
                pu.pve._person_sets = lambda: ({'precedent': {}}, [])
                cases.append(('a set precedent.json still declares never counts',
                              'precedent' not in pu.sets_this_update_dropped(repo, []),
                              ''))
            finally:
                pu.pve._person_sets = saved
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        fx.close()
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'a rerun after LEFT FOR YOU still takes the removal of a dropped '
          f'set\'s practices ({len(cases)} stated cases)', not bad,
          '; '.join(bad)[:3000])


def check_update_judges_retired_sets_after_the_catalogue():
    """Update Vendors judges a retired set after the catalogue update, and
    takes the view sync's removals when every one came from a set it dropped
    itself -- never any other refused removal.

    WHY. 2026-10-06, a consumer's update: a retired set's last rules were
    being folded into universal in the same update, but the set was judged
    against the old catalogue, read as holding rules "in force nowhere
    else", and kept. And where an update did drop a set, its own view sync
    then refused to remove that set's practices, with no way through."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    cases = []
    try:
        src = (ROOT / 'tools' / 'precedent_update.py').read_text(encoding='utf-8')
        body = src[src.index('def update('):]
        at = body.index('dropped_sets = retired_sources_step(repo, rep)')
        cases.append(('the retired-set step runs after the catalogue and before '
                      'the views',
                      body.index('# 3. The catalogue') < at < body.index('# 4. The views')))
        refusal = ("refusing to WRITE: this sync would remove 2 practice(s) this "
                   "repository's committed MANIFEST.json records, whose source "
                   "name is not among the sources precedent.json declares -- "
                   "light-check (recorded from precedent-shared-repo-maintenance); "
                   "{second} (recorded from {src}). THREE things produce this")
        ok = refusal.format(second='fresh-before-write',
                            src='precedent-shared-repo-maintenance')
        cases.append(('every refused removal from a set it dropped: taken',
                      sorted(pu.removals_this_update_caused(
                          ok, ['precedent-shared-repo-maintenance']))
                      == ['fresh-before-write', 'light-check']))
        mixed = refusal.format(second='x-rule', src='precedent-renamed-set')
        cases.append(('one from a source it did not drop: left to the person',
                      pu.removals_this_update_caused(
                          mixed, ['precedent-shared-repo-maintenance']) == []))
        cases.append(('nothing dropped: nothing taken',
                      pu.removals_this_update_caused(ok, []) == []))
        cases.append(('a removal whose source is still declared: never taken',
                      pu.removals_this_update_caused(
                          ok + " whose source is still declared -- y (from z)",
                          ['precedent-shared-repo-maintenance']) == []))
        cases.append(('the update re-runs the sync with --allow-removals only then',
                      "removals_this_update_caused(\n            out, "
                      "sets_this_update_dropped(repo, dropped_sets))" in body
                      and "'--allow-removals'], repo)" in body))
    finally:
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'Update Vendors judges retired sets after the catalogue '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_takes_a_removal_its_source_decommissioned():
    """Update Vendors lets the view sync remove a practice the source
    deleted on purpose -- recorded in process/decommissioned_paths.json at
    the commit the update takes -- by name, and nothing else.

    WHY. 2026-10-11: BestPractice deleted retired-set-takes-only-its-
    retirement and recorded it there, and the first run of Update All
    Vendors showed every consumer's update would now FAIL on it: the sync
    refused the removal and offered only --allow-removals, a person's call
    made repo by repo. The update now names the recorded practices to the
    sync (--allow-removal SLUG); one it cannot match to the record is
    still refused."""
    cases = []
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        refusal = ("refusing to WRITE: this sync would remove 1 practice(s) "
                   "this repository's committed MANIFEST.json records, whose "
                   "source is still declared -- {items}. Two causes, and the "
                   "remedy differs")
        gone = 'retired-set-takes-only-its-retirement'
        at = '34cb52010423c3887caf502bba7b45553b1a4543'  # the deletion
        cases.append(('a recorded decommission: named to the sync',
                      pu.decommissioned_removals(refusal.format(
                          items=f'{gone} (from precedent)'), at) == [gone]))
        cases.append(('a practice the record does not list: refused',
                      pu.decommissioned_removals(refusal.format(
                          items='the-boildown (from precedent)'), at) == []))
        cases.append(('one listed and one not: refused',
                      pu.decommissioned_removals(refusal.format(
                          items=f'{gone} (from precedent); the-boildown '
                                f'(from precedent)'), at) == []))
        cases.append(('from a set, not the universal source: refused',
                      pu.decommissioned_removals(refusal.format(
                          items=f'{gone} (from acme-shared-writing)'),
                          at) == []))
        cases.append(('at a commit before the record says so: refused',
                      pu.decommissioned_removals(refusal.format(
                          items=f'{gone} (from precedent)'), at + '^') == []))
        sync = (ROOT / 'tools' / 'precedent_sync_views.py').read_text(
            encoding='utf-8')
        cases.append(('the sync takes --allow-removal SLUG and lets only '
                      'those slugs through',
                      "'--allow-removal'}" in sync
                      and "b[0] in set(allow_removal_of)" in sync))
    finally:
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'Update Vendors takes a removal its source decommissioned '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_decommission_fits_the_vendored_sync():
    """Update Vendors never hands the vendored view sync an option it lacks.
    A sync too old for --allow-removal gets --allow-removals, and the update
    then checks the sync removed only what the source decommissioned.

    WHY. 2026-10-11, two consuming repositories: an update pinned to
    33f77a7, older than the clone it ran from, vendored that commit's sync
    and then passed it "--allow-removal", which it rejected as an unknown
    option. Here the consumer's sync is a stand-in shaped like 33f77a7's
    (or like today's) that writes the MANIFEST.json each case plants.

    Negative control, measured 2026-10-11: with vendored_accepts stood in to
    say yes, which is what 0840ae0's update did, cases (a) to (d) go red on
    the old sync's "unknown option '--allow-removal'"."""
    import contextlib
    import io
    import tempfile
    pu, _pve, _pr = _update_tools()
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-decommission-sync-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')
    gone = 'retired-set-takes-only-its-retirement'
    committed = [('a-rule', 'precedent'), (gone, 'precedent'),
                 ('set-rule', 'precedent-shared-x'), ('moved-rule', 'precedent')]
    # Shaped like 33f77a7's main(): a fixed list of known options.
    old_sync = (
        'import json, pathlib, sys\n'
        'a = sys.argv[1:]\n'
        'known = {"--repo", "--user-config", "--for-branch"}\n'
        'for tok in a:\n'
        '    if tok.startswith("--") and tok not in known | {"--allow-removals"}:\n'
        '        sys.exit(f"precedent_sync_views FAIL: unknown option {tok!r}")\n'
        'repo = pathlib.Path(a[a.index("--repo") + 1])\n'
        '(repo / "argv.json").write_text(json.dumps(a))\n'
        '(repo / "MANIFEST.json").write_text((repo / "after.json").read_text())\n')
    new_sync = old_sync.replace('"--for-branch"}', '"--for-branch", \'--allow-removal\'}')

    def planted(name, after, sync):
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True)
        (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': s, 'source': src} for s, src in committed]}))
        (repo / 'tools' / 'precedent_sync_views.py').write_text(sync)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'installed'], env=env)
        (repo / 'after.json').write_text(json.dumps({'practices': [
            {'slug': s, 'source': src} for s, src in after]}))
        return repo

    def take(name, after, sync=old_sync, dropped=()):
        repo = planted(name, after, sync)
        rep = pu.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            rc, out = pu.take_decommissioned(
                repo, repo / 'tools' / 'precedent_sync_views.py', [gone],
                list(dropped), rep)
        argv = (json.loads((repo / 'argv.json').read_text())
                if (repo / 'argv.json').is_file() else [])
        return rc, out, argv, ' '.join(o for _n, o in rep.steps)
    try:
        only = [p for p in committed if p[0] != gone]
        rc, out, argv, said = take('a', only)
        cases.append(('(a) a sync too old for --allow-removal: run with '
                      '--allow-removals, and it removed only the decommissioned '
                      'practice, so the update goes on and says so',
                      rc == 0 and argv[-1:] == ['--allow-removals']
                      and 'predates --allow-removal' in said
                      and 'removed nothing else' in said, (rc, argv, said, failure_detail(out, 300))))
        rc, out, argv, said = take('b', [('a-rule', 'precedent'),
                                          ('moved-rule', 'precedent')])
        cases.append(('(b) ...and it also removed a practice from a source that '
                      'records nothing now (dropped or renamed): refused, by name',
                      rc == 1 and 'it also removed set-rule (from precedent-shared-x)'
                      in out and 'refused' in said, (rc, said, failure_detail(out, 400))))
        rc, out, argv, said = take('c', [('a-rule', 'precedent'),
                                          ('moved-rule', 'precedent')],
                                   dropped=['precedent-shared-x'])
        cases.append(('(c) ...unless this update dropped that set itself',
                      rc == 0, (rc, said, failure_detail(out, 300))))
        rc, out, argv, said = take('d', [('a-rule', 'precedent'),
                                          ('set-rule', 'precedent-shared-x')])
        cases.append(('(d) a removal from a source that still records practices '
                      'is not one the flag waived: taken',
                      rc == 0, (rc, said, failure_detail(out, 300))))
        rc, out, argv, said = take('e', only, sync=new_sync)
        cases.append(('(e) a sync that takes --allow-removal: named, slug by slug, '
                      'never --allow-removals',
                      rc == 0 and argv[-2:] == ['--allow-removal', gone]
                      and '--allow-removals' not in argv
                      and 'predates' not in said, (rc, argv, said)))
        src = (ROOT / 'tools' / 'precedent_update.py').read_text(encoding='utf-8')
        cases.append(('the update runs the decommission through take_decommissioned',
                      'rc, out = take_decommissioned(' in src))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'Update Vendors fits the decommission to the vendored sync '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_built_from_record_is_compared_and_orders_the_updates():
    """A copied-in source exports BUILT_FROM.json -- what its compiled files
    were built from, by git blob hash, naming the source a file came from.
    Update Vendors compares each named file with this repository's own copy
    of that source and refuses DONE on a difference (held copies are only
    reported); a copied-in source's folder counts as another repository's
    files for the generated-files list; Update All Vendors runs a repository
    after the ones it copies from (2026-11-01: a consumer got a writing-rules
    set by two routes, and the copy inside compiled prompts lagged the
    direct one with nothing saying so)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_update_all as pua
        import precedent_regenerate as preg
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        (repo / 'process' / 'rules').mkdir(parents=True)
        (repo / 'process' / 'voice').mkdir(parents=True)
        rules = repo / 'process' / 'rules' / 'RULES.md'
        rules.write_text('Write plainly.\n')
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'rules', 'path': 'process/rules',
             'vendored': True, 'repo': 'https://github.com/o/Rules'},
            {'level': 'shared', 'name': 'voice', 'path': 'process/voice',
             'vendored': True, 'exports_only': True,
             'repo': 'https://github.com/o/Voice'}]}))
        want = subprocess.run(['git', 'hash-object', str(rules)],
                              capture_output=True, text=True).stdout.strip()
        cases.append(('the blob hash is what git hash-object prints',
                      pu.git_blob_hash(rules.read_bytes()) == want))

        def record(blob):
            (repo / 'process' / 'voice' / 'BUILT_FROM.json').write_text(json.dumps(
                {'_generated_by': 'x', 'outputs': {'PROMPT.md': [
                    {'path': 'voicepack.json', 'blob': '0' * 40},
                    {'path': 'process/rules/RULES.md', 'blob': blob,
                     'source': 'rules', 'source_path': 'RULES.md'},
                    {'path': 'process/rules/GONE.md', 'blob': '1' * 40,
                     'source': 'rules', 'source_path': 'GONE.md'}]}}))

        class Rep:
            def __init__(self):
                self.left, self.steps = [], []

            def leave(self, what, why):
                self.left.append((what, why))

            def step(self, what, why):
                self.steps.append((what, why))

        record(want)
        rep = Rep()
        pu.built_from_step(repo, rep)
        cases.append(('the same content: nothing left, and a file this repo '
                      'does not hold is not compared', not rep.left))
        record('2' * 40)
        rep = Rep()
        pu.built_from_step(repo, rep)
        cases.append(('different content: LEFT, naming the file and the repo '
                      'to update first', len(rep.left) == 1
                      and 'RULES.md' in rep.left[0][1]
                      and 'o/Voice' in rep.left[0][1]
                      and 'GONE.md' not in rep.left[0][1]))
        cfg = json.loads((repo / 'precedent.json').read_text())
        cfg['sources'][0]['hold'] = 'on purpose'
        (repo / 'precedent.json').write_text(json.dumps(cfg))
        rep = Rep()
        pu.built_from_step(repo, rep)
        cases.append(('a held source is reported, never left',
                      not rep.left and any('held' in w for _, w in rep.steps)))
        trees = preg.vendored_trees(repo)
        cases.append(('every copied-in folder is another repository\'s files',
                      {'process/upstream/', 'process/rules/', 'process/voice/'}
                      <= set(trees)))
    order = pua.dependency_order(
        ['o/consumer', 'o/voice', 'o/rules', 'o/other'],
        {'o/consumer': {'o/voice', 'o/rules'}, 'o/voice': {'o/rules'}})
    cases.append(('a repository runs after the ones it copies from',
                  order.index('o/rules') < order.index('o/voice')
                  < order.index('o/consumer') and len(order) == 4))
    cases.append(('a cycle keeps the order given',
                  pua.dependency_order(['o/a', 'o/b'],
                                       {'o/a': {'o/b'}, 'o/b': {'o/a'}})
                  == ['o/a', 'o/b']))
    cases.append(('a source URL reads as owner/repo',
                  pua._repo_of('https://github.com/O/Voice.git') == 'o/voice'))
    bad = [n for n, ok in cases if not ok]
    check(f'a built-from record is compared, and orders the updates '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_all_vendors_skips_its_own_source():
    """precedent_update_all.py never updates the BestPractice repository it
    runs from -- that repository has a precedent.json too -- and refuses to
    run with no repositories named, rather than guessing a set."""
    import tempfile
    cases = []
    tool = str(ROOT / 'tools' / 'precedent_update_all.py')
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update_all as pua
        own = pua.source_repo()
    finally:
        sys.path.pop(0)
    cases.append(('the tool reads its own source from the clone it runs in',
                  own == 'alex137/bestpractice'))
    with tempfile.TemporaryDirectory() as tmp:
        if own:
            r = subprocess.run([sys.executable, tool, '--workdir', tmp,
                                '--no-push', own.upper()],
                               capture_output=True, text=True)
            cases.append(('its own source, in any case: SKIPPED, nothing '
                          'cloned', r.returncode == 0
                          and r.stdout.startswith('SKIPPED')
                          and not any(pathlib.Path(tmp).iterdir())))
        # 2026-10-20: copy-in shipped and broke the update twice in its
        # first day, once per consumer state no test planted. --rehearse
        # runs an unlanded commit against every consumer, and never pushes.
        import argparse as _ap
        ns = _ap.Namespace(rehearse='feature-x', copy_in=['zz=yes'],
                           answered_by='Zz, 2026-10-20: "yes"', no_push=False)
        cases.append(('a rehearsal hands its commit and the answers to each '
                      'update', pua.update_args(ns) == [
                          '--from-ref', 'feature-x', '--copy-in', 'zz=yes',
                          '--answered-by', 'Zz, 2026-10-20: "yes"']))
        import inspect as _inspect
        src = _inspect.getsource(pua.main)
        cases.append(('a rehearsal never pushes',
                      'if args.rehearse:\n        args.no_push = True' in src))
        r = subprocess.run([sys.executable, tool, '--workdir', tmp],
                           capture_output=True, text=True)
        cases.append(('no repositories named: refused by argparse',
                      r.returncode == 2 and 'OWNER/REPO' in r.stderr))
    bad = [n for n, ok in cases if not ok]
    check(f'Update All Vendors skips its own source '
          f'({len(cases)} stated cases)', not bad and cases, '; '.join(bad))


def check_copy_in_records_the_budget_it_brings():
    """A set copied in brings its occasion share into the repository's cap,
    and Update Vendors records that rise as approved, on the person's own
    copy-in answer, so budget-within-approval passes after a copy-in run.
    A rise larger than the copied sets' shares, or a set the person said
    no to, is not recorded, and the check still refuses.

    WHY. Morgan, 2026-10-28 (strength: decided): "Go, fix it at the engine
    root issue". One consumer's cap rose 150 with its copy-ins and was
    raised by hand on his words; the next consumer failed the same way,
    because approved_budgets is each repository's own."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
        import precedent_check as pc
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    words = 'Zz, 2026-10-20: "copy the shared sets in"'
    cases = []
    saved_eff, saved_root = bv.effective_budgets, pc.ROOT
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'tools').mkdir()
        (repo / 'process' / 'zz-set').mkdir(parents=True)
        (repo / 'process' / 'zz-set' / 'precedent-source.json').write_text(
            json.dumps({'name': 'zz-set', 'occasion_share_tokens': 750}))

        def run(in_force, answer='yes'):
            (repo / 'precedent.json').write_text(json.dumps({
                'sources': [{'level': 'shared', 'name': 'zz-set',
                             'path': 'process/zz-set', 'vendored': True}],
                'copy_in': {'zz-set': {'answer': answer, 'answered_by': words}}}))
            (repo / 'tools' / 'session_load_budgets.json').write_text(json.dumps({
                'approved_budgets': {'occasion_index': {
                    'max': 3650, 'strength': 'baseline',
                    'approved_by': 'baseline 2026-10-10: seeded'}}}))
            bv.effective_budgets = lambda *a, **k: {'occasion_index': in_force}
            said = pu.record_copy_in_budget(repo, today='2026-10-28')
            pc.ROOT = repo
            found = [str(f) for f in pc._budget_within_approval(None)]
            entry = json.loads((repo / 'tools' / 'session_load_budgets.json')
                               .read_text())['approved_budgets']['occasion_index']
            return said, found, entry
        try:
            said, found, entry = run(3800)
            cases.append(('a rise within the copied set\'s share is recorded on '
                          'the copy-in answer, and the check passes',
                          bool(said) and not found and entry['max'] == 3800
                          and words in entry['approved_by']
                          and entry.get('previous_max') == 3650,
                          f'{said} {found} {entry}'))
            said, found, entry = run(4500)
            cases.append(('CONTROL: a rise beyond the copied shares is not '
                          'recorded, and the check refuses',
                          said is None and entry['max'] == 3650
                          and any('occasion_index' in f for f in found),
                          f'{said} {found}'))
            said, found, entry = run(3800, answer='no')
            cases.append(('a set the person said no to explains nothing',
                          said is None and entry['max'] == 3650 and found,
                          f'{said} {found}'))
            said, _found, _entry = run(3650)
            cases.append(('nothing above the approval: nothing recorded',
                          said is None, str(said)))
            # 2026-10-28: a copy-in also moves the copied sets' share of the
            # session file from the person's brought budget to the repo's.
            import precedent_session_practices as psp
            saved_psp = (psp.collect, psp.render, psp.charged_to_repo,
                         psp.copied_share)
            surface = '.precedent/SESSION_PRACTICES.md'

            def run_surface(charged, share=71):
                (repo / 'precedent.json').write_text(json.dumps({
                    'sources': [{'level': 'shared', 'name': 'zz-set',
                                 'path': 'process/zz-set', 'vendored': True}],
                    'copy_in': {'zz-set': {'answer': 'yes', 'answered_by': words}}}))
                (repo / 'tools' / 'session_load_budgets.json').write_text(json.dumps({
                    'surfaces': {surface: {'ceiling': 400}},
                    'approved_budgets': {f'surfaces/{surface}': {
                        'max': 400, 'strength': 'baseline',
                        'approved_by': 'baseline 2026-10-09: seeded'}}}))
                bv.effective_budgets = lambda *a, **k: {}
                psp.collect = lambda *a, **k: ([], {}, [])
                psp.render = lambda *a, **k: 'x'
                psp.charged_to_repo = lambda r, n: (charged, 0, [], None)
                psp.copied_share = lambda r: share
                said = pu.record_copy_in_budget(repo, today='2026-10-28')
                reg = json.loads((repo / 'tools' / 'session_load_budgets.json')
                                 .read_text())
                return said, reg['surfaces'][surface]['ceiling'], \
                    reg['approved_budgets'][f'surfaces/{surface}']
            try:
                said, ceiling, appr = run_surface(414)
                cases.append(('the session file over its ceiling by no more '
                              'than the copies add: ceiling and approval rise '
                              'by that share, on the copy-in answer',
                              bool(said) and ceiling == 471 and appr['max'] == 471
                              and words in appr['approved_by'],
                              f'{said} {ceiling} {appr}'))
                said, ceiling, appr = run_surface(500)
                cases.append(('CONTROL: over by more than the copies add: '
                              'nothing raised', said is None and ceiling == 400
                              and appr['max'] == 400, f'{said} {ceiling}'))
            finally:
                (psp.collect, psp.render, psp.charged_to_repo,
                 psp.copied_share) = saved_psp
        finally:
            bv.effective_budgets, pc.ROOT = saved_eff, saved_root
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a copy-in records the occasion budget it brings '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_session_load_total_is_the_one_budget():
    """Where a repository declares `session_load_tokens`, the total of what a
    session loads is the one budget that refuses: tokens moving from one
    always-loaded file to another never refuse, the per-part checks stand
    aside, budget-within-approval asks only about the total, and Update
    Vendors copies the person's total, with their words, into the
    repository. A repository with no total keeps every per-part ceiling.

    WHY. Morgan, 2026-10-28 (strength: decided): "Go, one number
    everywhere", on spec/SESSION_LOAD_ONE_TOTAL_PLAN.md. Rules moved between
    sets, sets copied in and a fix to how a share is counted each moved
    tokens from one budget to another, and each asked him again while the
    session paid the same."""
    import tempfile
    import types
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
        import precedent_check as pc
        import precedent_update as pu
        import precedent_session_practices as psp
    finally:
        sys.path.pop(0)
    words = 'Zz, 2026-10-28: "one number everywhere"'
    cases = []
    saved_root, saved_bb = pc.ROOT, psp.brought_budget
    ctx = types.SimpleNamespace(base=None, changed=(), read_base=lambda rel: None)
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'repo'
        (repo / 'tools').mkdir(parents=True)
        (repo / '.precedent').mkdir()
        reg_path = repo / 'tools' / 'session_load_budgets.json'

        def files(agents, session):
            (repo / 'AGENTS.md').write_text('w ' * agents)
            (repo / 'CLAUDE.md').write_text('@AGENTS.md\n')
            (repo / '.precedent' / 'SESSION_PRACTICES.md').write_text('w ' * session)

        def registry(total=None, total_max=None):
            reg = {'headroom_floor_pct': 5,
                   'surfaces': {'AGENTS.md': {'ceiling': 1000},
                                'CLAUDE.md': {'ceiling': 100},
                                '.precedent/SESSION_PRACTICES.md': {'ceiling': 1000}},
                   'approved_budgets': {}}
            if total is not None:
                reg['session_load_tokens'] = total
                reg['approved_budgets']['session_load_tokens'] = {
                    'max': total if total_max is None else total_max,
                    'strength': 'decided', 'approved_by': words}
            reg_path.write_text(json.dumps(reg))

        def findings(fn):
            try:
                return [str(f) for f in fn(ctx)]
            except pc.NotApplicable:
                return None
        try:
            pc.ROOT = repo
            registry(total=3000)
            cases.append(('a declared total is the only budget in force',
                          bv.effective_budgets(repo, registry=reg_path)
                          == {'session_load_tokens': 3000},
                          str(bv.effective_budgets(repo, registry=reg_path))))
            # About 1,300 tokens each side: a rule "moved" from the
            # session file into AGENTS.md puts AGENTS.md over its old
            # 1,000 ceiling with the total unchanged.
            files(agents=1500, session=500)
            got = findings(pc._session_load_budget)
            cases.append(('tokens moved between files under the total: no '
                          'finding, though AGENTS.md is over its old ceiling',
                          got == [], str(got)))
            cases.append(('loader-within-caps stands aside under a total',
                          findings(pc._loader_within_caps) is None))
            cases.append(('session-file-allowances-fit stands aside under a total',
                          findings(pc._session_file_allowances_fit) is None))
            cases.append(('budget-within-approval passes the approved total',
                          findings(pc._budget_within_approval) == [],
                          str(findings(pc._budget_within_approval))))
            files(agents=1500, session=1500)
            got = findings(pc._session_load_budget)
            cases.append(('the total over its number refuses, naming each part',
                          bool(got) and any('session_load_tokens' in g
                                            and 'AGENTS.md' in g for g in got),
                          str(got)))
            registry(total=5000, total_max=3000)
            got = findings(pc._budget_within_approval)
            cases.append(('a total above what the person approved refuses',
                          bool(got) and any('session_load_tokens' in g for g in got),
                          str(got)))
            # CONTROL: no total, the same move refuses on the part's ceiling.
            registry()
            files(agents=1500, session=500)
            got = findings(pc._session_load_budget)
            cases.append(('CONTROL: with no total, a part over its own ceiling '
                          'still refuses', bool(got)
                          and any('AGENTS.md' in g for g in got), str(got)))
            # Update Vendors copies the person's total and their words.
            ind = pathlib.Path(td) / 'individual'
            ind.mkdir()

            def person(approval):
                man = {'name': 'zz-individual', 'session_load_tokens': 4000}
                if approval:
                    man['session_load_approval'] = {'strength': 'decided',
                                                    'approved_by': words}
                (ind / 'precedent-source.json').write_text(json.dumps(man))
            psp.brought_budget = lambda r=None, key='brought_sets_tokens': (
                (4000, str(ind)) if key == 'session_load_tokens' else (None, str(ind)))
            person(approval=False)
            said = pu.record_person_total(repo, today='2026-10-28')
            cases.append(('CONTROL: a total with no approval beside it is not '
                          'copied', said is None and 'session_load_tokens'
                          not in json.loads(reg_path.read_text()), str(said)))
            person(approval=True)
            said = pu.record_person_total(repo, today='2026-10-28')
            reg = json.loads(reg_path.read_text())
            entry = reg['approved_budgets'].get('session_load_tokens') or {}
            cases.append(("the person's total is copied with their words",
                          bool(said) and reg.get('session_load_tokens') == 4000
                          and entry.get('max') == 4000
                          and words in entry.get('approved_by', ''),
                          f'{said} {entry}'))
            cases.append(('copying it again changes nothing',
                          pu.record_person_total(repo, today='2026-10-29') is None))
            cases.append(('CONTROL: a repository within the copied total is not '
                          'told to reduce', 'Reduction pass' not in (said or '')))
            # 2026-10-29: a repository already over the person's total heard
            # only "set to 10,000", and every session check after was red.
            files(agents=40000, session=500)
            psp.brought_budget = lambda r=None, key='brought_sets_tokens': (
                (3500, str(ind)) if key == 'session_load_tokens' else (None, str(ind)))
            said = pu.record_person_total(repo, today='2026-10-29') or ''
            cases.append(('a total copied into a repository already loading more '
                          'says so, and names a Reduction pass as the next step',
                          'over it' in said and 'Reduction pass' in said, said))
            # 2026-10-29: the same run then reported DONE with nothing for the
            # person. Its close measures the total the way the session check
            # does and asks, so the overrun reaches the reply.
            import contextlib
            import io
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.session_load_total_step(repo, rep)
            asked = ' '.join(q for w, q in rep.asks if w == 'session-load total')
            cases.append(('an update that sets a total the repository already '
                          'exceeds asks the person at its close, with the parts',
                          'over the 3,500-token session_load_tokens total' in asked
                          and 'AGENTS.md ~' in asked
                          and 'reduction-pass' in asked, asked or rep.asks))
            # 2026-10-30 (Morgan, strength: decided): the session check
            # and the full check judged the same over-total repository two
            # ways -- FAIL at every session start, nothing at any gate.
            # Planted once, read by both: the session check warns, the full
            # check refuses only a change that grew a part, and the gate
            # prints the overrun.
            import precedent_session_check as psc
            registry(total=3500)
            files(agents=40000, session=500)
            saved_psc_root = psc.ROOT
            try:
                psc.ROOT = repo
                rows = psc._session_load_rows()
            finally:
                psc.ROOT = saved_psc_root
            cases.append(('THE DISCRIMINATING CASE: over a total, the session '
                          'check warns and does not fail',
                          len(rows) == 1 and rows[0][1] == psc.WARN
                          and 'over the 3,500-token' in rows[0][2], rows))
            not_grown = types.SimpleNamespace(
                base='HEAD', changed=('README.md',),
                read_base=lambda rel: (repo / rel).read_text())
            got = [str(f) for f in pc._session_load_budget(not_grown)]
            cases.append(('...the full check, on a change that grew nothing, '
                          'refuses nothing', not any(
                              'session_load_tokens' in g for g in got), got))
            grown = types.SimpleNamespace(
                base='HEAD', changed=('AGENTS.md',),
                read_base=lambda rel: 'w ' * 10 if rel == 'AGENTS.md'
                else (repo / rel).read_text())
            got = [str(f) for f in pc._session_load_budget(grown)]
            cases.append(('...and on a change that grew AGENTS.md it refuses',
                          any('session_load_tokens' in g for g in got), got))
            import session_load_trend as slt
            note = slt.headroom_notice(repo) or ''
            cases.append(('...and the merge and push gates print the overrun',
                          'OVER by' in note, note))
            files(agents=1500, session=500)
            try:
                psc.ROOT = repo
                rows = psc._session_load_rows()
            finally:
                psc.ROOT = saved_psc_root
            cases.append(('CONTROL: within the total, the session check row '
                          'is OK', len(rows) == 1 and rows[0][1] is True, rows))
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.session_load_total_step(repo, rep)
            cases.append(('CONTROL: within the total, the close asks nothing',
                          rep.asks == [] and any(n == 'session-load total'
                                                 for n, _o in rep.steps),
                          rep.asks or rep.steps))
            (repo / 'precedent.json').write_text(json.dumps({'sources': []}))
            cases.append(('a copy-in records nothing under a total',
                          pu.record_copy_in_budget(repo) is None))
        finally:
            pc.ROOT, psp.brought_budget = saved_root, saved_bb
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a declared session-load total is the one budget that refuses '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_all_reads_what_the_update_prints():
    """precedent_update_all.py reads precedent_update.py's report, so the
    two are pinned here through the real printers: both COMMIT MESSAGE forms
    reach the commit message, and questions the update calls optional hold
    nothing back, while a question block that is not called optional still
    stops the repository at ASK.

    WHY. 2026-10-28, one Update All run: the update had started printing the
    files it rewrote outside the vendored trees in a second form the parser
    never read, so three repositories' commits left them out; and a copy-in
    offer, which the update itself says it is complete without, stopped a
    fourth at ASK with nothing pushed."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_update_all as pua
    finally:
        sys.path.pop(0)
    cases = []
    rep = pu.Report()
    rep.commit_note = 'took the anyway path'
    rep.ask('copy-in zz', 'copy zz in? yes or no')
    saved = pu.rewritten_outside_vendored
    pu.rewritten_outside_vendored = lambda _repo: ['M AGENTS.md',
                                                  'A .claude/settings.json']
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rep._questions()
            print("\nDONE -- nothing left for this repo to decide. Ask the "
                  "question(s) above")
            rep._commit_note()
    finally:
        pu.rewritten_outside_vendored = saved
    out = buf.getvalue()
    note = pua._commit_note(out) or ''
    cases.append(('the in-these-words form reaches the commit message',
                  'took the anyway path' in note, note))
    cases.append(('every rewritten file reaches the commit message',
                  '  M AGENTS.md' in note and '  A .claude/settings.json' in note,
                  note))
    cases.append(('the update prints the mark Update All reads for an ask',
                  pua.ASKS_MARK in out))
    questions, optional = pua._questions(out)
    cases.append(('the questions are read, and read as optional',
                  questions == ['copy-in zz: copy zz in? yes or no'] and optional,
                  f'{questions} {optional}'))
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['git', 'init', '-q', tmp], check=True)
        (pathlib.Path(tmp) / 'f').write_text('x')
        subprocess.run(['git', '-C', tmp, 'add', 'f'], check=True)
        cases.append(('optional questions only: the run goes on to commit',
                      pua._outcome(pua.DONE, out, tmp) == 'DONE'))
        strict = out.replace(pua.OPTIONAL_MARK, 'answer these first')
        cases.append(('a question block not called optional: ASK',
                      pua._outcome(pua.DONE, strict, tmp) == 'ASK'))
    src = pathlib.Path(pua.__file__).read_text(encoding='utf-8')
    cases.append(('an optional question is printed on the repository\'s line',
                  "QUESTION for the person ({repo})" in src))
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'Update All reads what the update prints '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_all_moves_a_reused_clone_off_its_pin():
    """A clone an earlier Update All run kept carries that run's pin, and
    the rerun asks for the newest passed main again (--move), and says so;
    a fresh clone and a rehearsal are given no --move.

    WHY. 2026-10-28, Update All over seven repositories: a consumer stayed
    LEFT on a main two fixes old, "pinned: the commit this update started
    from", until its clone was deleted by hand."""
    import argparse as _ap, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_update_all as pua
    finally:
        sys.path.pop(0)
    cases = []
    ns = _ap.Namespace(rehearse=None, copy_in=[], answered_by='', no_push=False)
    cases.append(('a reused clone: --move', pua.update_args(ns, True) == ['--move']))
    cases.append(('a fresh clone: no --move', pua.update_args(ns, False) == []))
    ns.rehearse = 'feature-x'
    cases.append(('a rehearsal names its commit, and no --move',
                  pua.update_args(ns, True) == ['--from-ref', 'feature-x']))
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['git', 'init', '-q', tmp], env=_fixture_git_env(),
                       check=True)
        repo = pathlib.Path(tmp)
        # A commit the source clone holds, or the pin is dropped as unknown.
        pin = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                             capture_output=True, text=True).stdout.strip()
        pu.record_pin(repo, pin, 'main')
        kept = pu.take_pin(repo, 'main', move=False)
        cases.append(('NEGATIVE CONTROL: without --move the pin holds, and '
                      'nothing reads as moved',
                      kept[0] == pin and pua.moved_off_pin(
                          f'source: main @ {pin[:12]} -- {kept[1]}') == '',
                      repr(kept)))
        moved = pu.take_pin(repo, 'main', move=True)
        line = pua.moved_off_pin(f'  source: main @ bbbbbbbbbbbb -- {moved[1]}')
        cases.append(('with --move the pin is dropped, and the line the update '
                      'prints is the one Update All repeats',
                      moved[0] is None and pu.held_pin(repo) is None
                      and pin[:12] in line, f'{moved} {line!r}'))
    src = pathlib.Path(pua.__file__).read_text(encoding='utf-8')
    cases.append(('the run hands the reuse to the update and prints the move',
                  'update_args(args, reused)' in src
                  and "SOURCE for {repo}" in src))
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'Update All moves a reused clone off its pin '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_done_names_the_branch_to_commit_on():
    """An Update Vendors run on a tier branch ends by printing the command
    that moves the staged update onto a branch precedent_branch_name.py
    names; on a session branch it prints nothing of the kind; and DONE no
    longer speaks a shared set's vocabulary.

    WHY. 2026-10-09, a consumer: DONE said "commit, then run Go update's
    chain" without naming a branch, the session made one by hand, and the
    push check refused it as not made by tools/precedent_branch_name.py."""
    import tempfile, inspect
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as _pu
    import precedent_branch_name as _pbn
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td) / 'repo'
            g = ['git', '-C', str(repo), '-c', 'user.name=t', '-c',
                 'user.email=t@example.com']
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
            (repo / 'precedent.json').write_text('{"format_version": 1}\n',
                                                 encoding='utf-8')
            subprocess.run(g + ['add', '-A'], check=True)
            subprocess.run(g + ['commit', '-qm', 'x'], check=True)
            line = _pu.feature_branch_line(repo) or ''
            cases.append(('on main, DONE prints the switch command',
                          _pu.SWITCH_COMMAND in line, line))
            subprocess.run(g + ['switch', '-q', '-c', 'staging'], check=True)
            cases.append(('...and on staging',
                          _pu.SWITCH_COMMAND in (_pu.feature_branch_line(repo) or ''),
                          ''))
            subprocess.run(g + ['switch', '-q', '-c',
                                '2026-10-09-some-work-abcde-q7m2x'], check=True)
            cases.append(('on a session branch it prints nothing',
                          _pu.feature_branch_line(repo) is None, ''))
            # The harness's own name is the ladder's to refuse, at pre-push
            # (its branch_name_guard, 2026-10-16); the engine says nothing.
            subprocess.run(g + ['switch', '-q', '-c', 'claude/sleepy-shannon-1nilys'],
                           check=True)
            cases.append(('on the harness\'s own name the engine says nothing',
                          _pu.feature_branch_line(repo) is None, ''))
        name = subprocess.run([sys.executable, str(ROOT / 'tools' /
                                                   'precedent_branch_name.py'),
                               '--no-check', 'update-vendors'],
                              capture_output=True, text=True).stdout.strip()
        cases.append(('the command makes a <date>-...-<session>-<random> name',
                      bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-z0-9-]+-[a-z0-9]{5}-[a-z0-9]{5}',
                                        name)), name))
        done = inspect.getsource(_pu.Report.close)
        cases.append(('DONE calls it, and says nothing of "Go update"',
                      'feature_branch_line(' in done and 'Go update' not in done, ''))
        # 2026-10-28: on the ladder, landing below main is not the end --
        # the phrase carries the move into main, and DONE says so.
        cases.append(('DONE prints the line about going live',
                      'live_line(' in done, ''))
        saved = (_pu.pb.ladder_in_force, _pu.pb.landing_branch)
        try:
            here = pathlib.Path('.')
            for ladder, landing, want, what in (
                    (True, 'staging', True, 'on the ladder, landing on staging'),
                    (True, 'main', False, 'on the ladder, landing on main'),
                    (False, 'main', False, 'off the ladder'),
                    (None, 'staging', False, 'with no ladder helper')):
                _pu.pb.ladder_in_force = lambda r, u=None, v=ladder: v
                _pu.pb.landing_branch = lambda r, u=None, b=landing: (b, '')
                line = _pu.live_line(here)
                ok = (bool(line) and 'into main' in line) if want else line is None
                cases.append((f'{what}, DONE '
                              f'{"says" if want else "says nothing of"} going live',
                              ok, line or ''))
        finally:
            _pu.pb.ladder_in_force, _pu.pb.landing_branch = saved
    finally:
        sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'Update Vendors names the branch to commit on from a tier branch '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_update_done_names_the_update_branches_it_replaces():
    """DONE lists every earlier update branch whose engine is already in
    the one just taken, each with its delete link, and flags any that still
    carries a CI workflow main deleted; an update branch it cannot place is
    named apart, and a newer one is left alone.

    2026-11-01: a practice set kept three update branches from August,
    September and October that later updates had replaced; nothing ever said
    so, and two still carried workflows its main had deleted, so a push to
    either would have run them again. Morgan, 2026-11-01: "All the issues
    above - act, do the root fixes". The fixture plants a source clone with
    commits A <- B <- C, a checkout that just took B, and one origin branch
    for each state the listing tells apart.

    Negative control, measured 2026-11-01: with the call in Report.close
    removed, the DONE case fails; with the ancestor test dropped (every
    update branch listed), the newer-branch case fails."""
    import tempfile, inspect, json as _json
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as _pu
    import precedent_stale_branches as _psb
    cases = []
    saved = _psb._slug
    try:
        _psb._slug = lambda repo: ('o', 'r')
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                       GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com',
                       GIT_CONFIG_GLOBAL=str(td / 'gc'))
            (td / 'gc').write_text('', encoding='utf-8')

            def git(where, *a):
                return subprocess.run(['git', '-C', str(where), *a], env=env,
                                      capture_output=True, text=True)
            clone = td / 'bp'
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(clone)], env=env)
            shas = []
            for n in 'ABC':
                git(clone, 'commit', '-q', '--allow-empty', '-m', n)
                shas.append(git(clone, 'rev-parse', 'HEAD').stdout.strip())
            a, b, c = shas
            origin, repo = td / 'o.git', td / 'w'
            subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)],
                           env=env)
            subprocess.run(['git', 'clone', '-q', str(origin), str(repo)], env=env,
                           capture_output=True)
            git(repo, 'checkout', '-q', '-B', 'main')
            (repo / 'precedent.json').write_text('{"landing_branch": "staging"}\n',
                                                 encoding='utf-8')
            (repo / 'tools').mkdir()

            def manifest(commit):
                (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    _json.dumps({'source_commit': commit}), encoding='utf-8')
            manifest(a)
            git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'base')
            git(repo, 'push', '-q', 'origin', 'main', 'main:staging')

            def branch(name, commit=None, workflow=False, classic=None):
                git(repo, 'checkout', '-q', '-B', name, 'main')
                if commit:
                    manifest(commit)
                if classic:
                    (repo / 'tools' / 'ENGINE_MANIFEST.json').unlink()
                    (repo / 'process').mkdir(exist_ok=True)
                    (repo / 'process' / 'manifest.json').write_text(
                        _json.dumps({'upstream': {'commit': classic}}),
                        encoding='utf-8')
                if workflow:
                    (repo / '.github' / 'workflows').mkdir(parents=True,
                                                           exist_ok=True)
                    (repo / '.github' / 'workflows' / 'old.yml').write_text(
                        'on: push\n', encoding='utf-8')
                git(repo, 'add', '-A')
                git(repo, 'commit', '-qm', name, '--allow-empty')
                git(repo, 'push', '-q', 'origin', name)
            branch('2026-10-01-x-update-vendors-aaaaa-bbbbb', a, workflow=True)
            branch('claude/repo-vendor-updates-kkkkk', classic=a)
            branch('2026-10-30-x-engine-refresh-ccccc-ddddd', c)
            branch('update-vendors-unknown', '0' * 40)
            branch('update-vendors-short', a)
            branch('update-vendors-short-2', a)
            branch('some-feature-work', a)
            # This run's own checkout, which just took B.
            git(repo, 'checkout', '-q', '-B',
                '2026-11-01-x-update-vendors-eeeee-fffff', 'main')
            manifest(b)
            git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'this update')
            git(repo, 'push', '-q', 'origin', 'HEAD')
            out = '\n'.join(_pu.replaced_update_lines(repo, clone))
        link = 'https://github.com/o/r/branches/all?query='
        cases.append(('THE DISCRIMINATING CASE: an older update branch is '
                      'listed as replaced, with its delete link',
                      'REPLACED UPDATE BRANCHES' in out and
                      link + '2026-10-01-x-update-vendors-aaaaa-bbbbb' in out, out))
        cases.append(('...and flagged for the workflow main no longer has',
                      'still carries .github/workflows/old.yml' in out, out))
        cases.append(('a classic install\'s catalogue record places it too',
                      link + 'claude%2Frepo-vendor-updates-kkkkk' in out, out))
        cases.append(('an update branch newer than what was taken is left alone',
                      'engine-refresh-ccccc' not in out, out))
        cases.append(('an engine the clone cannot place is named apart, unlinked',
                      'UPDATE BRANCHES NOT PLACED' in out and
                      link + 'update-vendors-unknown' not in out and
                      'update-vendors-unknown' in out, out))
        cases.append(('a name inside another branch\'s is flagged, not linked',
                      link + 'update-vendors-short\n' not in out + '\n' and
                      'not linked: its filter would also show update-vendors-short-2'
                      in out, out))
        cases.append(('a branch that is not an update is never listed',
                      'some-feature-work' not in out, out))
        cases.append(('this run\'s own branch is never listed',
                      'eeeee-fffff' not in out, out))
        done = inspect.getsource(_pu.Report.close)
        cases.append(('DONE prints the listing',
                      'replaced_update_lines(' in done, ''))
    finally:
        _psb._slug = saved
        sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'Update Vendors names the update branches it replaces '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


def check_update_seeds_an_upstream_budget_for_a_vendored_tool():
    """Update Vendors writes upstream's run budget, and its note, for a
    vendored engine tool this repo does not budget, and asks only when the
    repo's own figure differs from one upstream just changed.

    WHY. 2026-10-07, a consuming repository: the update stopped with
    "upstream budgets the vendored tools/precedent_vendor_engine.py at 12 API
    call(s) a run and this repo's registry has no budget for it", and the
    session copied the 12 and its note in by hand -- nothing to decide,
    repeated in every consumer. Planted: a missing budget is seeded with its
    note; a tool not vendored here is not; the repo's own different figure
    is a question only once upstream's figure moved; a figure that is
    upstream's previous one follows upstream's move, its note with it,
    without a question (2026-10-12: a consumer was asked about 400 and 120,
    upstream's own old figures); a repo with no registry gets nothing
    written."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    cases = []
    env = _fixture_git_env()
    saved_source = pu.SOURCE
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        src, repo = td / 'src', td / 'repo'
        (src / 'tools').mkdir(parents=True)
        (repo / 'tools').mkdir(parents=True)
        g = lambda *a: subprocess.run(['git', '-C', str(src), *a], env=env,
                                      capture_output=True, text=True, check=True).stdout.strip()
        g('init', '-q', '-b', 'main')
        budgets = lambda rb: json.dumps({'run_budgets': rb}, indent=2) + '\n'
        (src / 'tools' / 'github_api_budgets.json').write_text(
            budgets({'kept.py': 3, 'follow.py': 400, '_follow_note': 'old'}),
            encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'before')
        before = g('rev-parse', 'HEAD')
        (src / 'tools' / 'github_api_budgets.json').write_text(budgets({
            'new_tool.py': 12, '_new_tool_note': 'one GET per set',
            'kept.py': 5, 'not_here.py': 4, 'follow.py': 600,
            '_follow_note': 'new'}), encoding='utf-8')
        g('commit', '-qam', 'after')
        after = g('rev-parse', 'HEAD')
        (repo / 'tools' / pve_manifest_name()).write_text(json.dumps(
            {'files': ['new_tool.py', 'kept.py', 'follow.py']}), encoding='utf-8')
        reg = repo / 'tools' / 'github_api_budgets.json'
        reg.write_text(budgets({'kept.py': 2, 'follow.py': 400,
                                '_follow_note': 'old'}), encoding='utf-8')
        try:
            pu.SOURCE = src
            seeded, asks, followed = pu.seed_engine_budgets(repo, after, before)
            got = json.loads(reg.read_text(encoding='utf-8'))['run_budgets']
            cases.append(('a missing budget is seeded with upstream\'s figure',
                          seeded == [('new_tool.py', 12)] and got.get('new_tool.py') == 12))
            cases.append(('...and its note', got.get('_new_tool_note') == 'one GET per set'))
            cases.append(('a tool not vendored here is not seeded', 'not_here.py' not in got))
            cases.append(('the repo\'s own figure stays', got.get('kept.py') == 2))
            cases.append(('a different figure is asked once upstream\'s moved',
                          asks == [('kept.py', 2, 5)]))
            cases.append(('upstream\'s previous figure follows its move, unasked',
                          followed == [('follow.py', 400, 600)]
                          and got.get('follow.py') == 600))
            cases.append(('...its note with it', got.get('_follow_note') == 'new'))
            _s, asks2, _f = pu.seed_engine_budgets(repo, after, after)
            cases.append(('...and not again when upstream\'s did not move', asks2 == []))
            reg.unlink()
            cases.append(('a repo with no registry gets nothing written',
                          pu.seed_engine_budgets(repo, after, before) == ([], [], [])
                          and not reg.exists()))
        finally:
            pu.SOURCE = saved_source
    bad = [n for n, ok in cases if not ok]
    check(f'Update Vendors seeds upstream\'s budget for a vendored tool '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def pve_manifest_name():
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    return _pve.MANIFEST_NAME


def check_push_check_skips_a_set_check_older_than_push_time_judging():
    """A check a practice SET ships reaches a repository on the set's own
    schedule, not the engine's (practice: vendor-rollout-disclosed, question
    3; Morgan, 2026-09-29). The push check runs the session-trailer check at
    every push since that day; an older copy of it reads the whole history,
    so run at every push it would refuse over any old commit on main -- the
    very failure the new copy removed. Discriminating cases: an old copy is
    not run at push time and does not fail the push; a new copy that finds
    something still refuses."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='push-time-'))
    cases = []
    try:
        (tmp / 'tools' / 'checks').mkdir(parents=True)
        script = tmp / 'tools' / 'checks' / 'check_session_trailer.py'
        body = ('import sys\nprint("VIOLATION: session-trailer")\n'
                'print("  commit 0123456789ab: no trailer")\nsys.exit(1)\n')
        checks = [('session_trailer',
                   [sys.executable, 'tools/checks/check_session_trailer.py'], 'x')]
        script.write_text(body, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            failed, _m, _t, _f = ppc.run(tmp, checks)
        cases.append(('an old copy is not run at push time', not failed,
                      repr(failed)))
        script.write_text('# --all-history\n' + body, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            failed, _m, _t, _f = ppc.run(tmp, checks)
        cases.append(('a new copy that finds something still refuses',
                      failed == ['session_trailer'], repr(failed)))
        # precedent_update.py's stand-in commit: its message is the tool's,
        # so the commit-judging checks stand aside there.
        os.environ[ppc.STANDIN_COMMIT_ENV] = '1'
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                failed, _m, _t, _f = ppc.run(tmp, checks)
        finally:
            os.environ.pop(ppc.STANDIN_COMMIT_ENV, None)
        cases.append(('under the update\'s stand-in commit, the trailer check '
                      'stands aside', not failed, repr(failed)))
        # ...and when an update's check is red, its report shows the finding
        # even when routine notices were printed after it.
        import precedent_update as pu
        red = '\n'.join(['      | VIOLATION: session-trailer',
                         '      |   commit 0123abcd: no trailer'] +
                        ['      build_views: y is status: retired'] * 40)
        shown = pu.tail(red)
        cases.append(('a red update report shows the finding, not the last '
                      'notices', 'commit 0123abcd' in shown, failure_detail(shown, 300)))
        # ...and every finding, never the first 22 then "..." (2026-09-30: a
        # consumer's update ended FAILED three times running, each showing a
        # few more stranded files than the last).
        many = '\n'.join(['      | VIOLATION: rename-updates-links'] +
                         [f'      |     doc{i}.md:3: still references x'
                          for i in range(60)] + ['      notice'] * 40)
        shown = pu.tail(many, repo=tmp)
        saved = tmp / pu.FULL_OUTPUT_NAME
        cases.append(('...every finding of it, not the first few',
                      all(f'doc{i}.md:3' in shown for i in range(60)),
                      failure_detail(shown, 300)))
        cases.append(('...and the whole output is saved, and named',
                      saved.is_file() and saved.read_text() == many
                      and pu.FULL_OUTPUT_NAME in shown, failure_detail(shown, 200)))
        # ...and the stand-in itself carries a Session: trailer, because the
        # session-trailer check also runs inside precedent_check.py and in
        # the set's own test, which judge the commit and not the variable
        # above (2026-09-30, a consumer's update ended FAILED on it).
        import subprocess
        repo = tmp / 'standin-repo'
        repo.mkdir()
        git = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                        capture_output=True, text=True)
        git('init', '-q')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.com')
        (repo / 'a.txt').write_text('one\n', encoding='utf-8')
        git('add', 'a.txt')
        git('commit', '-q', '-m', 'first\n\nSession: none available (test)')
        before = git('rev-parse', 'HEAD').stdout.strip()
        (repo / 'a.txt').write_text('two\n', encoding='utf-8')
        git('add', 'a.txt')
        judge = [sys.executable, '-c',
                 'import re, subprocess, sys\n'
                 'b = subprocess.run(["git", "log", "-1", "--format=%B"], '
                 'capture_output=True, text=True).stdout\n'
                 'print(b)\n'
                 'sys.exit(0 if re.search(r"^(?:Session|Claude-Session):'
                 '\\s+(\\S.*)$", b, re.M) else 1)\n']
        saved = os.environ.pop('PRECEDENT_SESSION_URL', None)
        try:
            rc, out = pu.judged_as_committed(repo, judge)
            cases.append(('the stand-in commit carries a Session: trailer',
                          rc == 0 and pu.TEMP_COMMIT_MESSAGE in out, failure_detail(out, 300)))
            os.environ['PRECEDENT_SESSION_URL'] = 'https://example.test/s/1'
            rc, out = pu.judged_as_committed(repo, judge)
            cases.append(('a session that hands over its link gets it on the '
                          'stand-in', 'Session: https://example.test/s/1' in out,
                          failure_detail(out, 300)))
        finally:
            os.environ.pop('PRECEDENT_SESSION_URL', None)
            if saved is not None:
                os.environ['PRECEDENT_SESSION_URL'] = saved
        cases.append(('the stand-in is undone and the change stays staged',
                      git('rev-parse', 'HEAD').stdout.strip() == before and
                      git('diff', '--cached', '--name-only').stdout.strip()
                      == 'a.txt', git('log', '--oneline').stdout))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the push check skips a set check older than push-time judging '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_clone_lock_makes_parallel_updates_wait():
    """A clone or pull of a shared set waits while another run holds that
    clone, and the source-clone fetch in Update Vendors is held the same way.

    THE INCIDENT (2026-10-10). Update Vendors started in four voice repos at
    once: they fetch into one BestPractice clone and pull the same brought
    sets, and one run stopped with "cannot lock ref 'refs/remotes/origin/main':
    is at X but expected Y". Run again alone, it worked. The DISCRIMINATING
    CASE is the first: a pull through precedent_source_bootstrap._try_sync
    while another process holds the clone's lock finishes only after that
    process lets go -- on the code before the lock it finished at once. The
    others prove the lock gives way when its holder exits, times out by name
    rather than racing, and wraps the update's own fetch.
    The fixture owns its repositories (fixture-owns-its-state)."""
    import importlib, io, tempfile, time
    sys.path.insert(0, str(ROOT / 'tools'))
    psb = importlib.import_module('precedent_source_bootstrap')
    lock = importlib.import_module('precedent_clone_lock')
    cases = []
    env = {**os.environ, 'GIT_CONFIG_GLOBAL': empty_gitconfig(),
           'GIT_CONFIG_NOSYSTEM': '1'}

    def git(*a, cwd=None):
        return subprocess.run(['git', *a], cwd=cwd, capture_output=True,
                              text=True, env=env)

    hold = ('import sys, time; sys.path.insert(0, sys.argv[1]); '
            'import precedent_clone_lock as l\n'
            'with l.held(sys.argv[2]):\n'
            '    print("held", flush=True); time.sleep(float(sys.argv[3]))\n')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        origin, clone = tmp / 'origin.git', tmp / 'set'
        git('init', '-q', '--bare', '-b', 'main', str(origin))
        work = tmp / 'work'
        git('init', '-q', '-b', 'main', str(work))
        (work / 'a.md').write_text('a\n', encoding='utf-8')
        git('add', '.', cwd=work)
        git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'a',
            cwd=work)
        git('push', '-q', str(origin), 'main', cwd=work)
        git('clone', '-q', '-b', 'main', str(origin), str(clone))

        holder = subprocess.Popen(
            [sys.executable, '-c', hold, str(ROOT / 'tools'), str(clone), '2'],
            stdout=subprocess.PIPE, text=True)
        holder.stdout.readline()                      # it holds the lock now
        start = time.monotonic()
        ok, out = psb._try_sync(str(origin), clone, branch='main')
        took = time.monotonic() - start
        holder.wait()
        cases.append(('THE DISCRIMINATING CASE: a pull while another run holds '
                      'the clone waits for it, then succeeds',
                      ok and took >= 1.5, f'ok={ok} took={took:.2f}s {out!r}'))

        holder = subprocess.Popen(
            [sys.executable, '-c', hold, str(ROOT / 'tools'), str(clone), '3'],
            stdout=subprocess.PIPE, text=True)
        holder.stdout.readline()
        try:
            with lock.held(clone, wait=0.5, say=io.StringIO()):
                timed_out = ''
        except TimeoutError as e:
            timed_out = str(e)
        holder.kill(); holder.wait()
        cases.append(('a lock held past the wait raises, naming the clone, '
                      'rather than going ahead', str(clone) in timed_out,
                      timed_out))
        start = time.monotonic()
        with lock.held(clone, wait=5):
            pass
        cases.append(('a killed holder lets go at once -- no stale lock',
                      time.monotonic() - start < 1, ''))
        cases.append(('the lock lives inside the clone\'s git directory',
                      lock.lock_path(clone) == clone / '.git' / lock.LOCK_NAME,
                      str(lock.lock_path(clone))))

    src = (ROOT / 'tools' / 'precedent_update.py').read_text(encoding='utf-8')
    fetch = src.find("'fetch', 'origin',\n")
    cases.append(("Update Vendors' source-clone fetch sits inside held(SOURCE)",
                  fetch > 0 and 'with held(SOURCE):' in src[max(0, fetch - 300):fetch],
                  ''))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'parallel updates wait their turn on a shared clone '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_update_rerun_rerecords_a_template_file_the_first_run_wrote():
    """A rerun of Update Vendors re-records the manifest hash of a file
    instantiated from a template that the first run rewrote and staged, so
    the practice audit does not fail it as DRIFT.

    THE INCIDENT (2026-10-10, two consumers). The first run rewrote
    .claude/settings.json from its template and stopped LEFT FOR YOU. The
    rerun counted the file as already uncommitted, not as its own output,
    left the old hash, and the audit failed it until someone ran
    `practice_audit.py --update-baseline --entry .claude/settings.json`.
    The DISCRIMINATING CASE is the first: on the code before
    this_updates_output the hash stayed stale. The second proves a file the
    person changed between the runs is still not re-recorded.
    The fixture owns its repository (fixture-owns-its-state)."""
    import hashlib, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    cases = []
    rel = '.claude/settings.json'
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        env = _fixture_git_env()
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        (repo / '.claude').mkdir()
        (repo / rel).write_text('{"old": true}\n', encoding='utf-8')
        old = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        (repo / 'process').mkdir()
        mf = repo / 'process' / 'manifest.json'

        def manifest():
            mf.write_text(json.dumps({'upstream': {'vendored_at': 'process/upstream'},
                                      'entries': [{
                'practice': 'claude-code-settings', 'status': 'synced',
                'upstream_path': 'templates/harness/claude-code/settings.json',
                'local_path': rel, 'granularity': 'file',
                'local_sha256': old}]}, indent=2) + '\n', encoding='utf-8')
        manifest()
        g('add', '.'); g('commit', '-qm', 'installed')

        # The first run: rewrites the file from the template, stages it, and
        # records it as its output -- then stops LEFT FOR YOU.
        (repo / rel).write_text('{"new": true}\n', encoding='utf-8')
        g('add', rel)
        pu.record_kept_output(repo, [rel])
        # The rerun: the file is dirty before it starts.
        before = pu.dirty_paths(repo)
        earlier = pu.earlier_runs_output(repo, before)
        got = pu.rebaseline_vendored_entries(
            repo, pu.this_updates_output(repo, before, earlier))
        new = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        rec = json.loads(mf.read_text(encoding='utf-8'))['entries'][0]['local_sha256']
        cases.append(('THE DISCRIMINATING CASE: the rerun re-records the hash of '
                      'the file the first run wrote', rel in got and rec == new,
                      f'got={got} rec={rec[:12]} file={new[:12]}'))

        # The person edits the staged file between the runs.
        manifest()
        (repo / rel).write_text('{"new": true, "mine": 1}\n', encoding='utf-8')
        before = pu.dirty_paths(repo)
        earlier = pu.earlier_runs_output(repo, before)
        got = pu.rebaseline_vendored_entries(
            repo, pu.this_updates_output(repo, before, earlier))
        rec = json.loads(mf.read_text(encoding='utf-8'))['entries'][0]['local_sha256']
        cases.append(('POSITIVE CONTROL: a change the person made between the '
                      'runs is not re-recorded', rel not in got and rec == old,
                      f'got={got}'))
    src = (ROOT / 'tools' / 'precedent_update.py').read_text(encoding='utf-8')
    cases.append(('the update re-records through this_updates_output',
                  'this_updates_output(repo, before, rep.earlier)' in src, ''))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a rerun re-records a template file the first run wrote '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_early_copy_in_yes_waits_for_the_set():
    """A yes given before the set can be copied is recorded and waits
    (Morgan, 2026-10-19: he said yes to his voice pack in a repository
    before its owner had Produced it, and the update then refused to sync
    anything, because the yes declared a copy with nothing behind it).

    1. The yes is recorded with why it waits, and nothing is declared.
    2. The set is not asked about again.
    3. NEGATIVE CONTROL: a later run while the set is still missing keeps
       waiting and declares nothing.
    4. Once the set reaches its own main, the next run declares it copied
       in, with its folder, and drops the wait."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='early-copy-in-yes-'))
    cases = []
    genv = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t'}
    saved = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',
                                            'PRECEDENT_GITHUB_USER')}

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=genv,
                              capture_output=True, text=True)
    try:
        origin = tmp / 'origins' / 'zz-voice.git'
        origin.parent.mkdir()
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=genv, check=True)
        voice = tmp / 'people' / 'zz-voice'
        subprocess.run(['git', 'clone', '-q', str(origin), str(voice)],
                       env=genv, capture_output=True, check=True)
        (voice / 'README.md').write_text('a voice repo, no pack yet\n')
        git(voice, 'add', '-A')
        git(voice, 'commit', '-qm', 'one')
        git(voice, 'push', '-q', 'origin', 'main')
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [],
             'offers': [{'name': 'zz-voice', 'repo_url': 'https://example.invalid/zz-voice',
                         'set_root': 'pack'}]}))
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind', 'path': str(ind)}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        os.environ['PRECEDENT_GITHUB_USER'] = 'zzme'
        host = tmp / 'host'
        host.mkdir()
        (host / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private',
             'maintainers': [{'github': 'zzme', 'name': 'Zzme'}],
             'sources': []}, indent=2))
        import precedent_update as pu

        def cfg():
            return json.loads((host / 'precedent.json').read_text())

        def declared():
            return [e for e in cfg().get('sources') or []
                    if e.get('name') == 'zz-voice']

        by = 'Zzme, 2026-10-19: "yes to the voice pack"'
        rep = pu.Report()
        pu.copy_in_step(host, rep, {'zz-voice': 'yes'}, by)
        rec = (cfg().get('copy_in') or {}).get('zz-voice') or {}
        cases.append(('an early yes is recorded with why it waits, and nothing '
                      'is declared',
                      rec.get('answer') == 'yes' and 'main' in rec.get('waits_on', '')
                      and not declared(), repr(cfg())[:500]))
        rep = pu.Report()
        pu.copy_in_step(host, rep)
        cases.append(('the set is not asked about again', not rep.asks,
                      repr(rep.asks)[:300]))
        cases.append(('NEGATIVE CONTROL: still missing, it keeps waiting',
                      not declared() and any('still waiting' in w
                                             for _k, w in rep.steps),
                      repr(rep.steps)[:400]))
        (voice / 'pack' / 'practices').mkdir(parents=True)
        (voice / 'pack' / 'practices' / 'zz-voice-rule.md').write_text(
            '---\nslug: zz-voice-rule\n---\n# v\n\n## Rule\n\nx\n')
        (voice / 'pack' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-voice', 'level': 'shared', 'visibility': 'private'}))
        git(voice, 'add', '-A')
        git(voice, 'commit', '-qm', 'pack')
        git(voice, 'push', '-q', 'origin', 'main')
        rep = pu.Report()
        pu.copy_in_step(host, rep)
        rec = (cfg().get('copy_in') or {}).get('zz-voice') or {}
        d = declared()
        cases.append(('once the set reaches its main, the next run declares it '
                      'with its folder and drops the wait',
                      len(d) == 1 and d[0].get('vendored') is True
                      and d[0].get('set_root') == 'pack'
                      and 'waits_on' not in rec and rec.get('answered_by') == by,
                      repr(cfg())[:500]))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an early copy-in yes waits for the set, then declares it '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:500]}" for n, d in bad))


def check_public_copy_in_needs_the_leak_check():
    """In a public repository, a yes to copying a set in is refused while
    the leak check cannot read the set (2026-10-20, Update All Vendors: the
    question said the check could not run, "there is no clone of the set on
    this machine", and still offered the copy).

    1. The question says it cannot be copied in yet, names where the clone
       goes, and offers only a no.
    2. A yes is not recorded, and the question is asked again.
    3. A no is recorded.
    4. NEGATIVE CONTROL: in a private repository the same yes is recorded
       (it waits for the set, as before).
    5. A yes recorded before the set could be read is not declared in a
       public repository while the leak check finds a line in it."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='public-copy-in-'))
    cases = []
    saved = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',
                                            'PRECEDENT_GITHUB_USER',
                                            'PRECEDENT_LEAK_BLOCKLIST')}
    genv = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t'}
    try:
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [],
             'offers': [{'name': 'zz-voice',
                         'repo_url': 'https://example.invalid/zz-voice'}]}))
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind',
                                                   'path': str(ind)}}))
        bl = tmp / 'private' / 'leak-blocklist.txt'
        bl.parent.mkdir()
        bl.write_text('zzsecretword\n')
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        os.environ['PRECEDENT_GITHUB_USER'] = 'zzme'
        os.environ['PRECEDENT_LEAK_BLOCKLIST'] = str(bl)
        import precedent_vendor_engine as pve
        import precedent_update as pu

        def host(name, vis):
            h = tmp / name
            h.mkdir()
            (h / 'precedent.json').write_text(json.dumps(
                {'format_version': 1, 'visibility': vis,
                 'maintainers': [{'github': 'zzme', 'name': 'Zzme'}],
                 'sources': []}, indent=2))
            return h

        def rec(h):
            return (json.loads((h / 'precedent.json').read_text())
                    .get('copy_in') or {}).get('zz-voice')

        pub = host('open', 'public')
        offer = {o['name']: o for o in pve.copy_in_offers(pub)}['zz-voice']
        q = pve.copy_in_question(offer)
        cases.append(('the question says it cannot be copied yet, where the '
                      'clone goes, and offers only a no',
                      'cannot be copied in yet' in q
                      and str(tmp / 'people' / 'zz-voice') in q
                      and 'zz-voice=no' in q and '=yes|no' not in q, q))
        by = 'Zzme, 2026-10-20: "yes"'
        rep = pu.Report()
        pu.copy_in_step(pub, rep, {'zz-voice': 'yes'}, by)
        cases.append(('a yes is not recorded, and the question is asked again',
                      rec(pub) is None and any('the yes was not recorded' in w
                                               for _k, w in rep.asks),
                      repr(rep.asks)[:400]))
        rep = pu.Report()
        pu.copy_in_step(pub, rep, {'zz-voice': 'no'}, 'Zzme, 2026-10-20: "no"')
        cases.append(('a no is recorded', (rec(pub) or {}).get('answer') == 'no',
                      repr(rec(pub))))
        q3 = pve.copy_in_question({o['name']: o for o in pve.copy_in_offers(
            host('closed0', 'private'))}['zz-voice'])
        cases.append(('an offered set this repository does not declare is '
                      'not said to be loaded here',
                      'stays out of this repository' in q3
                      and 'keep loading it' not in q3, q3))
        priv = host('closed', 'private')
        rep = pu.Report()
        pu.copy_in_step(priv, rep, {'zz-voice': 'yes'}, by)
        cases.append(('NEGATIVE CONTROL: in a private repository the yes is '
                      'recorded and waits', (rec(priv) or {}).get('answer') == 'yes'
                      and bool((rec(priv) or {}).get('waits_on')),
                      repr(rec(priv))))
        # 5. A waiting yes in a public repository, then the set arrives with
        # a private word in it.
        pub2 = host('open2', 'public')
        cfg = json.loads((pub2 / 'precedent.json').read_text())
        cfg['copy_in'] = {'zz-voice': {'answer': 'yes', 'answered_by': by,
                                       'waits_on': 'no clone'}}
        (pub2 / 'precedent.json').write_text(json.dumps(cfg, indent=2))
        origin = tmp / 'origins' / 'zz-voice.git'
        origin.parent.mkdir()
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=genv, check=True)
        voice = tmp / 'people' / 'zz-voice'
        subprocess.run(['git', 'clone', '-q', str(origin), str(voice)],
                       env=genv, capture_output=True, check=True)
        (voice / 'practices').mkdir()
        (voice / 'practices' / 'zz-v.md').write_text(
            '---\nslug: zz-v\n---\n# v\n\n## Rule\n\nzzsecretword\n')
        (voice / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-voice', 'level': 'shared', 'visibility': 'private'}))
        for a in (('add', '-A'), ('commit', '-qm', 'one'),
                  ('push', '-q', 'origin', 'main')):
            subprocess.run(['git', '-C', str(voice), *a], env=genv,
                           capture_output=True)
        got = pve.copy_in_pending(pub2)
        declared = [e for e in json.loads((pub2 / 'precedent.json').read_text())
                    .get('sources') or [] if e.get('name') == 'zz-voice']
        cases.append(('a waiting yes is not declared in a public repository '
                      'while the leak check finds a line',
                      not declared and any('zzsecretword' in w for _c, w in got),
                      repr(got)[:500]))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a public copy-in needs the leak check to have read the set '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:500]}" for n, d in bad))


def check_failed_rerun_keeps_an_uncommitted_copied_in_set():
    """A FAILED Update Vendors run's rerun puts back the engine files that run
    staged, and never a copied-in set's files.

    2026-10-19, a consuming repository: the first run copied a voice pack in
    (never committed, so not in HEAD) and ended FAILED; the rerun's put-back
    (restore_own_staged_output) took the copy's directory for part of the
    mirrored catalogue -- mirrored_prefixes() lists every vendored source's
    path -- and, finding it absent from HEAD, deleted every file. The
    copy's record, process/manifest_<set>.json, is outside that directory and
    stayed, so the refresh read the set as already copied and the sync then
    refused it as empty. Nothing writes a copy again from HEAD, so it is not
    the engine's to put back.

    Negative control, measured 2026-10-20 against staging at 75970f4a0: the
    copy's files are gone after the put-back and its record is still there."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='rerun-keeps-copy-'))
    genv = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t'}
    g = lambda *a: subprocess.run(['git', '-C', str(tmp), *a], env=genv,
                                  capture_output=True, text=True)
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp)], env=genv,
                       check=True)
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'engine.py').write_text('old\n')
        (tmp / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': []}, indent=2))
        g('add', '-A')
        g('commit', '-qm', 'init')
        # Run 1: refreshes the engine, copies a set in, then fails.
        (tmp / 'tools' / 'engine.py').write_text('new\n')
        (tmp / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': [
                {'level': 'shared', 'name': 'zz-voice',
                 'path': 'process/zz-voice', 'vendored': True}]}, indent=2))
        copy = tmp / 'process' / 'zz-voice'
        (copy / 'practices').mkdir(parents=True)
        (copy / 'precedent-source.json').write_text('{"name": "zz-voice"}')
        (copy / 'practices' / 'zz-voice-rule.md').write_text('# v\n')
        (tmp / 'process' / 'manifest_zz-voice.json').write_text(json.dumps(
            {'upstream': {'repo': 'https://example.invalid/zz-voice',
                          'vendored_at': 'process/zz-voice', 'commit': 'a' * 40}}))
        g('add', '-A')
        staged = g('diff', '--cached', '--name-only').stdout.split()
        pu.record_staged_output(tmp, staged)          # run 1 ended FAILED
        back = pu.restore_own_staged_output(tmp, pu.vendored_layer_paths)
        cases.append(('the engine file the failed run staged is put back',
                      (tmp / 'tools' / 'engine.py').read_text() == 'old\n',
                      repr(back)))
        cases.append(("the copied-in set's files stay, with its record",
                      (copy / 'precedent-source.json').is_file()
                      and (copy / 'practices' / 'zz-voice-rule.md').is_file()
                      and (tmp / 'process' / 'manifest_zz-voice.json').is_file(),
                      repr(back)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_copy_in_is_asked_once():
    """Part 6 of spec/VENDORED_SHARED_SETS.md (Morgan, 2026-10-19: "it's a
    question with each new repo and (one time) when we update vendors to
    the new system").

    1. The offers: every set the person brings, and every set they only
       offer. "yes" is suggested only for a brought set, in a private
       repository whose only code owner is the person; "no" otherwise.
    2. Update Vendors with no answers asks once per set and writes nothing.
    3. An answer is recorded, with who gave it; a yes declares the set
       copied in, and a ladder yes binds everyone through binds_everyone,
       which the ladder check then accepts.
    4. A recorded answer, yes or no, is never asked again.
    5. The refresh copies a yes in from the person's clone and records its
       commit, and takes every later move, a voice pack included, saying how
       far it moved; a set still saying "copy_refresh": "on-go-ahead" is
       taken anyway and the stale line named (2026-10-20). A copy the
       repository holds ("hold" in its precedent.json) is reported when it
       moves, not taken, and taken this once with --take-set; the freshness
       notice and the merge step call it held, never behind.
    6. NEGATIVE CONTROL: an answer with no quote is not recorded.
    7. The installer asks the same questions and records the same answers.
    8. The repository that holds an offered set (in a set_root folder) is
       not offered it, its origin read in https, ssh or proxy form."""
    import shutil, tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='copy-in-asked-once-'))
    cases = []
    genv = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t'}
    saved = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',
                                            'PRECEDENT_GITHUB_USER')}

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=genv,
                              capture_output=True, text=True)

    def make_set(name, extra):
        origin = tmp / 'origins' / f'{name}.git'
        origin.parent.mkdir(exist_ok=True)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=genv, check=True)
        clone = tmp / 'people' / name
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       env=genv, capture_output=True, check=True)
        (clone / 'practices').mkdir()
        (clone / 'practices' / f'{name}-rule.md').write_text(
            f'---\nslug: {name}-rule\n---\n# r\n\n## Rule\n\nx\n')
        (clone / 'precedent-source.json').write_text(json.dumps(
            {'name': name, 'level': 'shared', 'visibility': 'public', **extra}))
        git(clone, 'add', '-A')
        git(clone, 'commit', '-qm', 'one')
        git(clone, 'push', '-q', 'origin', 'main')
        return clone

    def make_host(hname, visibility, owners):
        host = tmp / hname
        host.mkdir()
        (host / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': visibility,
             'maintainers': [{'github': o, 'name': o.title()} for o in owners],
             'sources': []}, indent=2))
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(host)],
                       env=genv, check=True)
        git(host, 'add', '-A')
        git(host, 'commit', '-qm', 'init')
        return host

    try:
        ladder = make_set('zz-ladder', {'provides': ['ladder']})
        make_set('zz-writing', {})
        voice = make_set('zz-voice', {})
        # The voice pack's set lives in a folder of its repository
        # (set_root), as a real voice pack does beside its own install:
        # the root's manifest says nothing about go-aheads, the folder's does.
        (voice / 'pack' / 'practices').mkdir(parents=True)
        (voice / 'pack' / 'practices' / 'zz-voice-rule.md').write_text(
            '---\nslug: zz-voice-rule\n---\n# v\n\n## Rule\n\nx\n')
        (voice / 'pack' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-voice', 'level': 'shared', 'visibility': 'public',
             'copy_refresh': 'on-go-ahead'}))
        git(voice, 'add', '-A')
        git(voice, 'commit', '-qm', 'pack')
        git(voice, 'push', '-q', 'origin', 'main')
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual',
             'brings': [{'name': 'zz-ladder', 'repo_url': 'https://example.invalid/zz-ladder'},
                        {'name': 'zz-writing', 'repo_url': 'https://example.invalid/zz-writing'}],
             'offers': [{'name': 'zz-voice', 'repo_url': 'https://example.invalid/zz-voice',
                         'set_root': 'pack'}]}))
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind', 'path': str(ind)}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        os.environ['PRECEDENT_GITHUB_USER'] = 'zzme'
        import precedent_vendor_engine as pve
        import precedent_update as pu
        import precedent_install as pi

        mine = make_host('mine', 'private', ['zzme'])
        offers = {o['name']: o['default'] for o in pve.copy_in_offers(mine)}
        cases.append(('private, and only you own it: yes for what you bring, no '
                      'for what you only offer',
                      offers == {'zz-ladder': 'yes', 'zz-writing': 'yes',
                                 'zz-voice': 'no'}, repr(offers)))
        for hname, vis, owners, what in (
                ('open', 'public', ['zzme'], 'a public repository'),
                ('shared', 'private', ['zzme', 'zzother'],
                 'a private repository others own too')):
            h = make_host(hname, vis, owners)
            got = {o['default'] for o in pve.copy_in_offers(h)}
            cases.append((f'{what}: every default is no', got == {'no'},
                          repr(got)))

        before = (mine / 'precedent.json').read_text()
        rep = pu.Report()
        pu.copy_in_step(mine, rep)
        cases.append(('with no answers, Update Vendors asks once per set and '
                      'writes nothing',
                      sorted(q.split('?')[0] for _w, q in rep.asks)
                      == ['Copy zz-ladder into this repository',
                          'Copy zz-voice into this repository',
                          'Copy zz-writing into this repository']
                      and (mine / 'precedent.json').read_text() == before,
                      repr(rep.asks)[:600]))

        rep = pu.Report()
        pu.copy_in_step(mine, rep, {'zz-ladder': 'no'}, 'Zzme, 2026-10-19 said no')
        cfg = json.loads((mine / 'precedent.json').read_text())
        cases.append(('NEGATIVE CONTROL: an answer with no quote is not recorded',
                      'zz-ladder' not in (cfg.get('copy_in') or {}),
                      repr(cfg.get('copy_in'))))

        by = 'Zzme, 2026-10-19: "yes, copy it in"'
        rep = pu.Report()
        pu.copy_in_step(mine, rep, {'zz-ladder': 'yes', 'zz-voice': 'yes'}, by)
        cfg = json.loads((mine / 'precedent.json').read_text())
        decl = {e['name']: e for e in cfg['sources']}
        cases.append(('a yes is recorded with who gave it, and declares the set '
                      'copied in',
                      cfg['copy_in']['zz-ladder'] == {'answer': 'yes',
                                                      'answered_by': by}
                      and decl.get('zz-ladder', {}).get('vendored') is True
                      and decl['zz-ladder']['path'] == 'process/zz-ladder',
                      repr(cfg)[:600]))
        cases.append(('a ladder yes binds everyone, quoting the answer',
                      cfg.get('binds_everyone') == {'sets': ['zz-ladder'],
                                                    'approved_by': by},
                      repr(cfg.get('binds_everyone'))))
        cases.append(('only the unanswered set is still asked',
                      [q.split('?')[0] for _w, q in rep.asks]
                      == ['Copy zz-writing into this repository'],
                      repr(rep.asks)[:400]))

        rep = pu.Report()
        pu.refresh_copies_step(mine, rep)
        up = json.loads((mine / 'process' / 'manifest_zz-ladder.json')
                        .read_text()).get('upstream', {})
        # 2026-10-20: a copied set's manifest named no scrub list, so the
        # audit read it as process/scrub_blocklist.txt and FAILED in every
        # consumer without one -- a state this test never planted. 'mine'
        # has no list: the copy's manifest must opt out, with why, and the
        # audit must pass it.
        mf = json.loads((mine / 'process' / 'manifest_zz-ladder.json').read_text())
        import practice_audit as _pa, contextlib, io
        saved_root, _pa.ROOT = _pa.ROOT, mine
        try:
            got = []
            with contextlib.redirect_stdout(io.StringIO()):
                _pa.audit_manifest(mine / 'process' / 'manifest_zz-ladder.json',
                                   False, got, [], [])
            fails = [f for f in got if f.startswith('SCRUB')]
        finally:
            _pa.ROOT = saved_root
        cases.append(('in a repository with no scrub list, the copy opts out of '
                      'the outbound scrub, with why, and the audit passes it',
                      not (mine / 'process' / 'scrub_blocklist.txt').exists()
                      and mf['upstream'].get('scrub_blocklist', 'absent') is None
                      and 'ever sent up' in mf['upstream'].get(
                          '_scrub_blocklist_note', '')
                      and not fails, repr(mf['upstream'])[:400] + repr(fails)))
        cases.append(('the refresh copies a yes in and records its commit',
                      (mine / 'process' / 'zz-ladder' / 'practices'
                       / 'zz-ladder-rule.md').is_file()
                      and up.get('vendored_at') == 'process/zz-ladder'
                      and bool(up.get('commit')), failure_detail(repr(rep.steps), 600)))
        cases.append(('a voice pack is copied the first time, from its set_root '
                      'folder alone',
                      (mine / 'process' / 'zz-voice' / 'practices'
                       / 'zz-voice-rule.md').is_file()
                      and not (mine / 'process' / 'zz-voice' / 'pack').exists()
                      and json.loads((mine / 'precedent.json').read_text())
                      ['sources'][-1].get('set_root') == 'pack',
                      failure_detail(repr(rep.steps), 600)))

        import precedent_check as pc
        old_root = pc.ROOT
        try:
            pc.ROOT = mine
            found = pc._ladder_set_is_brought_not_declared(None)
        finally:
            pc.ROOT = old_root
        cases.append(('the ladder check accepts the copy the answer bound',
                      found == [], str([str(f) for f in found])))

        def voice_commit(slug):
            (voice / 'pack' / 'practices' / f'{slug}.md').write_text(
                f'---\nslug: {slug}\n---\n# l\n\n## Rule\n\ny\n')
            git(voice, 'add', '-A')
            git(voice, 'commit', '-qm', slug)

        def voice_has(slug):
            return (mine / 'process' / 'zz-voice' / 'practices'
                    / f'{slug}.md').is_file()

        # Morgan, 2026-10-20: voice packs refresh on a normal update. The
        # pack here still says "copy_refresh": "on-go-ahead", as the real
        # one did, so the retired line is ignored and named.
        voice_commit('zz-later')
        git(voice, 'push', '-q', 'origin', 'main')
        rep = pu.Report()
        pu.refresh_copies_step(mine, rep)
        said = [t for w, t in rep.steps if w == 'copy of zz-voice']
        cases.append(('a moved voice pack is taken on a normal update, with no '
                      'question, and the report says how far it moved',
                      voice_has('zz-later') and not rep.asks
                      and any(t.startswith('moved ') for t in said),
                      failure_detail(repr(rep.steps), 600) + repr(rep.asks)[:200]))
        cases.append(('a set still saying "copy_refresh" has the stale line named',
                      any('"copy_refresh"' in t and 'retired' in t for t in said),
                      repr(said)[:600]))

        cfg = json.loads((mine / 'precedent.json').read_text())
        for e in cfg['sources']:
            if e['name'] == 'zz-voice':
                e['hold'] = 'drafting chapter 9'
        (mine / 'precedent.json').write_text(json.dumps(cfg, indent=2))
        voice_commit('zz-held')
        # Moved is a question about the set's main, not the branch the clone
        # is on: an unpushed commit is not a move, and a clone sitting on an
        # older branch does not hide one (2026-10-19).
        rep = pu.Report()
        pu.refresh_copies_step(mine, rep)
        cases.append(('NEGATIVE CONTROL: a commit not on the set\'s main is not '
                      'reported as a move',
                      not any(w == 'copy of zz-voice' and 'has moved' in t
                              for w, t in rep.steps), failure_detail(repr(rep.steps), 400)))
        git(voice, 'push', '-q', 'origin', 'main')
        git(voice, 'checkout', '-q', '-b', 'zz-old', 'HEAD~1')
        rep = pu.Report()
        pu.refresh_copies_step(mine, rep)
        cases.append(('a copy the repository holds is reported when it moves, '
                      'not taken, whatever branch its clone is on',
                      any(w == 'copy of zz-voice' and 'drafting chapter 9' in t
                          and '--take-set zz-voice' in t for w, t in rep.steps)
                      and not rep.asks and not voice_has('zz-held'),
                      failure_detail(repr(rep.steps), 400)))
        import precedent_engine_freshness as fr
        import precedent_merge_vendors as pmv
        saved_tip = fr.upstream_tip
        fr.upstream_tip = lambda *a, **k: 'f' * 40
        try:
            out = io.StringIO()
            fr.report(mine, out=out)
            behind, _unknown = pmv.vendors_behind(mine)
        finally:
            fr.upstream_tip = saved_tip
        text = out.getvalue()
        cases.append(('the freshness notice calls a held copy held, and the merge '
                      'step does not count it behind',
                      'held -- zz-voice' in text and 'drafting chapter 9' in text
                      and not any('zz-voice' in b for b in behind),
                      failure_detail(text, 600) + repr(behind)[:300]))
        git(voice, 'checkout', '-q', 'main')
        rep = pu.Report()
        pu.refresh_copies_step(mine, rep, take_sets=('zz-voice',))
        cases.append(('--take-set takes a held copy this once',
                      voice_has('zz-held'), failure_detail(repr(rep.steps), 400)))
        # A copy whose files are gone is made again, held or not.
        shutil.rmtree(mine / 'process' / 'zz-voice')
        rep = pu.Report()
        pu.refresh_copies_step(mine, rep)
        cases.append(('a held copy whose files are gone is made again',
                      (mine / 'process' / 'zz-voice' / 'precedent-source.json').is_file()
                      and voice_has('zz-held'), failure_detail(repr(rep.steps), 400)))

        rep = pu.Report()
        pu.copy_in_step(mine, rep, {'zz-writing': 'no'}, by)
        rep2 = pu.Report()
        pu.copy_in_step(mine, rep2)
        cfg = json.loads((mine / 'precedent.json').read_text())
        cases.append(('a no is recorded, the set stays live, and nothing is '
                      'asked again', rep2.asks == []
                      and cfg['copy_in']['zz-writing']['answer'] == 'no'
                      and 'zz-writing' not in {e['name'] for e in cfg['sources']},
                      repr(rep2.asks)))

        # Morgan, 2026-10-19: a public repository is warned about first,
        # and "no" is named as loading the set at session start.
        q = pve.copy_in_question(pve.copy_in_offers(tmp / 'open')[0])
        cases.append(('a public repository\'s question warns first that what '
                      'is copied in becomes public',
                      q.startswith('WARNING: this repository is PUBLIC'), q))
        q = pve.copy_in_question(pve.copy_in_offers(tmp / 'shared')[0])
        cases.append(('NEGATIVE CONTROL: a private one carries no such warning, '
                      'and either says no keeps it loading at session start',
                      'PUBLIC' not in q
                      and 'No: keep loading it at session start' in q, q))
        own_set = make_host('a-set', 'private', ['zzme'])
        (own_set / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ladder', 'level': 'shared'}))
        got = pve.copy_in_offers(own_set)
        cases.append(('a practice set is offered nothing, least of all itself',
                      got == [], repr(got)))

        # The repository that holds an offered set in a folder of its own
        # (set_root) was offered that set, a copy of itself (2026-10-19). Its
        # origin is the offer's repo_url, written in another of the forms a
        # GitHub remote takes here.
        ind_man = ind / 'precedent-source.json'
        ind_saved = ind_man.read_text()
        m = json.loads(ind_saved)
        m['offers'][0]['repo_url'] = 'https://github.com/ZZOwner/zz-voice.git'
        ind_man.write_text(json.dumps(m))
        try:
            holder = make_host('holder', 'private', ['zzme'])
            git(holder, 'remote', 'add', 'origin',
                'http://local_proxy@127.0.0.1:9/git/zzowner/zz-voice')
            got = {o['name'] for o in pve.copy_in_offers(holder)}
            cases.append(('the repository holding an offered set is not offered '
                          'it, whatever form its origin is written in',
                          got == {'zz-ladder', 'zz-writing'}, repr(got)))
            other = make_host('other', 'private', ['zzme'])
            git(other, 'remote', 'add', 'origin',
                'https://github.com/zzowner/zz-elsewhere')
            got = {o['name'] for o in pve.copy_in_offers(other)}
            cases.append(('NEGATIVE CONTROL: a repository with another origin is '
                          'still offered it', 'zz-voice' in got, repr(got)))
        finally:
            ind_man.write_text(ind_saved)
        ids = [pve._repo_identity(u) for u in (
            'https://github.com/ZZOwner/zz-voice.git',
            'ssh://' + 'git' + '@github.com/zzowner/zz-voice',
            'http://local_proxy@127.0.0.1:9/git/zzowner/zz-voice/',
            'https://example.invalid/zzowner/zz-voice')]
        cases.append(('one repository reads as one identity in https, ssh and '
                      'proxy form; another host reads as none',
                      ids == ['zzowner/zz-voice'] * 3 + [''], repr(ids)))

        fresh = make_host('fresh', 'private', ['zzme'])
        lines = pi._copy_in(fresh, {}, '')
        asked = [l for l in lines if l.startswith('copy in, a question:')]
        lines2 = pi._copy_in(fresh, {'zz-writing': 'yes'}, by)
        cases.append(('the installer asks the same question, and copies a yes in',
                      len(asked) == 3 and any('copied to process/zz-writing' in l
                                              for l in lines2)
                      and (fresh / 'process' / 'zz-writing' / 'practices').is_dir(),
                      repr(lines + lines2)[:700]))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
        if 'checkin' in sys.modules:
            importlib.reload(sys.modules['checkin'])
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'whether to copy a set in is asked once per repository, and the '
          f'answer recorded ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:500]}" for n, d in bad))


def check_declared_exports_are_copied():
    """Files a source exports are copied in by Update Vendors, and a copy
    nothing declares fails the full check (Morgan, 2026-10-30, strength:
    decided: "The whole point of vendoring in and update vendors is when the
    original one changes and I run an update vendors in the repo, it gets the
    new version of everything that's vendored in").

    1. A copy declared "exports_only" takes the files the source's
       precedent-source.json exports and its manifest, never its practices
       or a file it does not export; nothing loads rules from it.
    2. A consumer's own "exports" list copies from a source with no
       precedent-source.json at all.
    3. A full copy brings the exports beside the practices.
    4. A moved source's refresh lists each changed file.
    5. A declared copy with no clone to refresh from is left for the
       person, never DONE. NEGATIVE CONTROL: with every clone there, nothing
       is left.
    6. The full check fails on an undeclared folder holding a .source-commit
       file, and on one whose file opens with an AUTO-SYNCED banner.
       NEGATIVE CONTROLS: the same marker inside a declared copy passes, and
       "vendored from" in the middle of a sentence is no banner."""
    import shutil, tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='declared-exports-'))
    cases = []
    genv = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t'}
    saved = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',
                                            'PRECEDENT_GITHUB_USER')}

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=genv,
                              capture_output=True, text=True)

    def make_source(name, files):
        origin = tmp / 'origins' / f'{name}.git'
        origin.parent.mkdir(exist_ok=True)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=genv, check=True)
        clone = tmp / 'people' / name
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       env=genv, capture_output=True, check=True)
        for rel, text in files.items():
            (clone / rel).parent.mkdir(parents=True, exist_ok=True)
            (clone / rel).write_text(text)
        git(clone, 'add', '-A')
        git(clone, 'commit', '-qm', 'one')
        git(clone, 'push', '-q', 'origin', 'main')
        return clone

    def make_host(hname, sources):
        host = tmp / hname
        host.mkdir()
        (host / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private',
             'sources': sources}, indent=2))
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(host)],
                       env=genv, check=True)
        git(host, 'add', '-A')
        git(host, 'commit', '-qm', 'init')
        return host

    try:
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual'}))
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind', 'path': str(ind)}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        os.environ['PRECEDENT_GITHUB_USER'] = 'zzme'
        voice = make_source('zz-voicex', {
            'precedent-source.json': json.dumps(
                {'name': 'zz-voicex', 'level': 'shared', 'visibility': 'public',
                 'exports': ['PROMPT.md', 'essentials']}),
            'practices/zz-voicex-rule.md':
                '---\nslug: zz-voicex-rule\n---\n# v\n\n## Rule\n\nx\n',
            'PROMPT.md': 'the compiled prompt, first\n',
            'essentials/one.md': 'essential one\n',
            'NOTES.md': 'not exported\n'})
        make_source('zz-rulesx', {'RULES.md': 'rule one\n'})
        import precedent_update as pu
        import precedent_resolve as pr
        import precedent_check as pc

        def entry(name, **kw):
            return {'level': 'shared', 'name': name, 'path': f'process/{name}',
                    'vendored': True, **kw}

        host = make_host('host', [entry('zz-voicex', exports_only=True),
                                  entry('zz-rulesx', exports_only=True,
                                        exports=['RULES.md'])])
        rep = pu.Report()
        pu.refresh_copies_step(host, rep)
        cv = host / 'process' / 'zz-voicex'
        cases.append(('an exports-only copy takes the exported file and folder '
                      'and the manifest, never the practices or an unexported file',
                      (cv / 'PROMPT.md').is_file()
                      and (cv / 'essentials' / 'one.md').is_file()
                      and (cv / 'precedent-source.json').is_file()
                      and not (cv / 'practices').exists()
                      and not (cv / 'NOTES.md').exists(),
                      failure_detail(repr(rep.steps), 700) + repr(rep.left)[:300]))
        cases.append(('a consumer-named export copies from a source with no '
                      'precedent-source.json',
                      (host / 'process' / 'zz-rulesx' / 'RULES.md').is_file(),
                      failure_detail(repr(rep.steps), 700) + repr(rep.left)[:300]))
        cases.append(('an exports-only copy is recorded like any copied-in set',
                      bool(json.loads((host / 'process' / 'manifest_zz-voicex.json')
                                      .read_text()).get('upstream', {}).get('commit')),
                      failure_detail(repr(rep.steps), 400)))
        listed = [n for _p, _l, n, _note in pr.vendored_source_paths(host)]
        cases.append(('nothing loads rules from an exports-only copy',
                      'zz-voicex' not in listed and 'zz-rulesx' not in listed,
                      repr(listed)))
        cases.append(('NEGATIVE CONTROL: with every clone there, nothing is left',
                      rep.left == [], repr(rep.left)))

        (voice / 'PROMPT.md').write_text('the compiled prompt, second\n')
        (voice / 'essentials' / 'two.md').write_text('essential two\n')
        git(voice, 'add', '-A')
        git(voice, 'commit', '-qm', 'two')
        git(voice, 'push', '-q', 'origin', 'main')
        rep = pu.Report()
        pu.refresh_copies_step(host, rep)
        said = ' | '.join(t for w, t in rep.steps if w == 'copy of zz-voicex')
        cases.append(('a moved source is taken, and the report lists each '
                      'changed file',
                      (cv / 'PROMPT.md').read_text() == 'the compiled prompt, second\n'
                      and 'PROMPT.md (changed)' in said
                      and 'essentials/two.md (added)' in said, said[:700]))

        full = make_host('full', [entry('zz-voicex')])
        rep = pu.Report()
        pu.refresh_copies_step(full, rep)
        fv = full / 'process' / 'zz-voicex'
        cases.append(('a full copy brings the exports beside the practices',
                      (fv / 'practices' / 'zz-voicex-rule.md').is_file()
                      and (fv / 'PROMPT.md').is_file()
                      and (fv / 'essentials' / 'two.md').is_file()
                      and not (fv / 'NOTES.md').exists(),
                      failure_detail(repr(rep.steps), 600) + repr(rep.left)[:300]))

        cfg = json.loads((host / 'precedent.json').read_text())
        cfg['sources'].append(entry('zz-nowhere', exports_only=True))
        (host / 'precedent.json').write_text(json.dumps(cfg, indent=2))
        rep = pu.Report()
        pu.refresh_copies_step(host, rep)
        cases.append(('a declared copy with no clone is left for the person, '
                      'never DONE',
                      any(w == 'copy of zz-nowhere' and 'no clone' in why
                          for w, why in rep.left), repr(rep.left)))

        old_root = pc.ROOT
        try:
            pc.ROOT = host
            (cv / '.source-commit').write_text('abc\n')
            (host / 'notes.md').write_text(
                '# Notes\n\nThis paragraph was vendored from upstream once.\n')
            got = pc._undeclared_copies()
            cases.append(('NEGATIVE CONTROL: a marker inside a declared copy, and '
                          '"vendored from" mid-sentence, are not findings',
                          got == {}, repr(got)))
            (host / 'external' / 'thing').mkdir(parents=True)
            (host / 'external' / 'thing' / '.source-commit').write_text('abc\n')
            (host / 'prompts').mkdir()
            (host / 'prompts' / 'P.md').write_text(
                '<!-- AUTO-SYNCED from another repository; do not edit -->\n# P\n')
            got = pc._undeclared_copies()
            cases.append(('an undeclared folder with a .source-commit file, and '
                          'one with an AUTO-SYNCED banner, are findings',
                          set(got) == {'external/thing', 'prompts'}, repr(got)))
            found = pc._copied_in_folder_is_declared(None)
            cases.append(('the check fails on them, naming the declaration',
                          len(found) == 2 and all('"vendored": true' in str(f)
                                                  for f in found),
                          str([str(f) for f in found])[:600]))
        finally:
            pc.ROOT = old_root
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
        if 'checkin' in sys.modules:
            importlib.reload(sys.modules['checkin'])
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'files a source exports are copied in by Update Vendors, and an '
          f'undeclared copy fails the full check ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:500]}" for n, d in bad))


def check_update_refuses_a_shortened_flag():
    """`precedent_update.py --take X` was ambiguous between --take-anyway and
    --take-set (2026-10-19). A shortened flag is refused, naming every flag
    it could mean in full, before anything runs; a full flag still parses."""
    cases = []
    for argv, want in ((['--take', 'abc'], '--take-anyway or --take-set'),
                       (['--take-a', 'abc'], 'in full: --take-anyway'),
                       (['--mo'], 'in full: --move')):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                            *argv], capture_output=True, text=True, timeout=60)
        cases.append((' '.join(argv), r.returncode != 0 and want in r.stdout,
                      failure_detail(r.stdout + r.stderr, 300)))
    # NEGATIVE CONTROL: a full flag is not refused as a shortening.
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                        '--take-set'], capture_output=True, text=True, timeout=60)
    cases.append(('--take-set in full', 'is not a flag' not in r.stdout
                  and 'expected one argument' in r.stderr, failure_detail(r.stdout + r.stderr, 300)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check('Update Vendors refuses a shortened flag, naming the full ones it '
          f'could mean ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d}' for n, d in bad))


def check_update_vendors_retires_pre_staging():
    """The upgrade off pre-staging, for anyone on the ladder since it was
    retired for everyone on 2026-10-14 (Morgan, 2026-10-09: "make sure we have a smooth upgrade process
    for each. Merging the branches, telling he can delete pre-staging,
    updating previous mentions/links within each repo"). Update Vendors'
    migration (tools/migration_retire_pre_staging.py), on a local bare origin:

    - work on pre-staging that staging lacks is brought into staging by
      --land's composition, with main's direct work; nothing is dropped and
      pre-staging itself is left where it was;
    - once pre-staging holds nothing staging lacks it is offered for
      deletion with the filtered branches-page link, and the stale-branch
      lister and the very deep check offer it too -- never staging or main;
    - a clear instruction and a link to this repo's pre-staging tree are
      repointed to staging; a dated line, a Story section, another
      repository's link and a gotcha are left alone and listed;
    - a second run changes nothing and says it is retired, with the link;
    - a conflict stops with nothing moved, nothing reworded and no offer;
    - once it is gone, nothing makes it again and the step says nothing;
    - off the ladder it sees nothing at all;
    - a precedent.json naming pre-staging is switched to staging whoever
      the maintainers are, but only by a second pass, once the repository's
      committed engine can land on staging. (Until 2026-10-14 only an
      explicit staging lander was moved, and only the sole maintainer could
      switch precedent.json.)"""
    import tempfile, json as _json
    name = 'Update Vendors retires pre-staging for anyone on the ladder'
    if not (ROOT / 'tools' / 'precedent_update.py').exists():
        not_applicable(name, 'tools/precedent_update.py is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # Who is running it comes from identity.json alone, never this
        # machine's own PRECEDENT_GITHUB_USER.
        env = dict(_stale_ref_fixture_env(tmp), PRECEDENT_GITHUB_USER='')
        work, git, _branches, tip = _promote_fixture(
            tmp, env, 'staging', ('main', 'staging', 'pre-staging'))
        bare = tmp / 'origin.git'
        # Origin answers as GitHub's o/r, so a delete link can be built.
        git(work, 'remote', 'set-url', 'origin', 'https://github.com/o/r.git')
        git(work, 'config', f'url.file://{bare}.insteadOf',
            'https://github.com/o/r.git')
        indiv = tmp / 'indiv'
        indiv.mkdir()
        (tmp / 'config.json').write_text(_json.dumps(
            {'individual': {'path': str(indiv)}}), encoding='utf-8')

        def person(**settings):
            (indiv / 'identity.json').write_text(_json.dumps(
                {'email': 'p' + chr(64) + 'example.com', **settings}),
                encoding='utf-8')

        agents = ('# Notes\n\n'
                  'Work lands on `pre-staging` and waits there.\n'
                  'See [the tree](https://github.com/o/r/tree/pre-staging/docs).\n'
                  '2026-10-01: we chose to push to pre-staging first.\n'
                  'Promote pre-staging into staging when ready.\n'
                  'Upstream keeps [its own](https://github.com/x/y/tree/pre-staging).\n'
                  '\n## Story\n\nSessions push to pre-staging here.\n'
                  '\n## Next\n\nOpen a pull request into pre-staging.\n'
                  '\n## Notes\n\n2026-10-07: handoff prompt, kept as sent:\n\n'
                  '    2. **Push to `pre-staging` (Booked) refused.**\n'
                  '\n- a list item\n    continued: push to `pre-staging`.\n'
                  '\nThe bug, found 2026-10-07, read as\nfollows: Push to '
                  '`pre-staging` (Booked) was refused.\n'
                  '\nIts first line, "Push to `pre-staging` (Booked) refused", '
                  'is the clue.\n')
        gotcha = 'gotchas/gotcha-2026-10-01-pushes.md'
        (work / 'gotchas').mkdir()
        (work / gotcha).write_text('# Trap\n\nPush to pre-staging failed.\n',
                                   encoding='utf-8')
        (work / 'AGENTS.md').write_text(agents, encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'docs')
        git(work, 'push', '-q', 'origin', 'HEAD:main', 'HEAD:staging',
            'HEAD:pre-staging')

        script = tmp / 'step.py'
        script.write_text(
            'import json, pathlib, sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_update as pu, precedent_branches as pb\n'
            'import precedent_stale_branches as sb\n'
            'import migration_retire_pre_staging as m\n'
            'repo = pathlib.Path(sys.argv[2])\n'
            'if sys.argv[1] == "step":\n'
            '    rep = pu.Report(); rep.before = set()\n'
            '    m.migrate(repo, rep, pu)\n'
            '    rep._migration_notes()\n'
            '    print("RESULT " + json.dumps({"steps": rep.steps, '
            '"left": rep.left, "retired": rep.migration_notes.get(m.HEADER, [])}))\n'
            'elif sys.argv[1] == "offers":\n'
            '    import very_deep_check as v\n'
            '    print("RESULT " + json.dumps({"never": pb.never_offered(repo), '
            '"stale": [b for b, _d in sb.stale_in(repo, fetch=True) or []], '
            '"vdc": sorted(v._never_deletable(repo))}))\n'
            'elif sys.argv[1] == "tiers":\n'
            '    print("RESULT " + json.dumps({"rc": pb.ensure_tiers(repo, '
            'apply=True, say=lambda *a: None)}))\n', encoding='utf-8')

        def call(what, **extra):
            p = subprocess.run([sys.executable, str(script), what, str(work)],
                               cwd=work, capture_output=True, text=True,
                               env=dict(env, **extra))
            line = next((l for l in p.stdout.splitlines()
                         if l.startswith('RESULT ')), None)
            res = _json.loads(line[len('RESULT '):]) if line else {}
            return res, p.stdout + p.stderr

        def commit_on(branch, path, text):
            git(work, 'fetch', '-q', 'origin')
            git(work, 'checkout', '-q', '-B', 'tmp-' + branch, f'origin/{branch}')
            (work / path).write_text(text, encoding='utf-8')
            git(work, 'add', '-A')
            git(work, 'commit', '-q', '-m', f'{path} on {branch}')
            git(work, 'push', '-q', 'origin', f'HEAD:refs/heads/{branch}')
            sha = git(work, 'rev-parse', 'HEAD').stdout.strip()
            git(work, 'checkout', '-q', 'main')
            git(work, 'reset', '-q', '--hard', 'origin/main')
            return sha

        def on(sha, branch):
            git(work, 'fetch', '-q', 'origin')
            return git(work, 'merge-base', '--is-ancestor', sha,
                       f'origin/{branch}').returncode == 0

        def tips():
            return tuple(tip(b) for b in ('main', 'staging', 'pre-staging'))

        def text(rel):
            return (work / rel).read_text(encoding='utf-8')

        waiting = commit_on('pre-staging', 'ps.txt', 'p\n')
        direct = commit_on('main', 'direct.txt', 'd\n')
        git(work, 'checkout', '-q', 'main')
        git(work, 'reset', '-q', '--hard', 'origin/main')
        link = 'https://github.com/o/r/branches/all?query=pre-staging'

        # --- off the ladder: nothing done, nothing said. Since 2026-10-14
        # pre-staging is retired for everyone ON the ladder, whatever their
        # own settings say; until then each of these people was left alone
        # too, and only an explicit staging lander was moved off it. ---
        before = tips()
        for label, settings in (
                ('off the ladder, landing on pre-staging',
                 dict(landing_branch='pre-staging', promote_only=True)),
                ('off the ladder, landing on staging',
                 dict(landing_branch='staging', promote_only=True))):
            person(**settings)
            res, out = call('step', PRECEDENT_NO_LADDERS='1')
            cases.append((f'{label}: the step does nothing and says nothing',
                          res == {'steps': [], 'left': [], 'retired': []}
                          and tips() == before and text('AGENTS.md') == agents,
                          failure_detail(out, 300)))
        # No case here protects pre-staging from deletion while it holds
        # work: the step above brings that work into staging first, and
        # nothing else in the engine treats pre-staging as a tier (Morgan,
        # 2026-10-17: "WE SHOULD DELETE PRE-STAGING EVERYWHERE").

        # --- the repository still makes pre-staging others' landing branch ---
        person(landing_branch='staging', promote_only=True, github='p-user')
        pj = text('precedent.json')

        def repo_lands_on_pre_staging(maintainers):
            data = dict(_json.loads(pj), landing_branch='pre-staging',
                        _landing_branch_comment=['Work lands on pre-staging here.'])
            if maintainers is not None:
                data['maintainers'] = [{'github': m} for m in maintainers]
            body = _json.dumps(data, indent=2) + '\n'
            (work / 'precedent.json').write_text(body, encoding='utf-8')
            return body

        # Until 2026-10-14 a precedent.json naming pre-staging kept it --
        # "others' landing branch" -- unless the person running the update
        # was the repository's only maintainer, and a person moving repo by
        # repo waited for the second pass. Nobody else lands there now, so
        # the value is switched whoever the maintainers are (below, with
        # two of them).
        body = repo_lands_on_pre_staging(['P-User', 'someone-else'])
        engine = work / 'tools' / 'precedent_branches.py'
        engine.write_text(text('tools/precedent_branches.py').replace(
            'def lands_on_staging(', 'def lands_elsewhere('), encoding='utf-8')
        git(work, 'commit', '-q', '-m', 'an engine from before', '--',
            'tools/precedent_branches.py')
        res, out = call('step')
        steps = res.get('steps') or []
        cases.append(('the first pass, its committed engine older: precedent.json '
                      'untouched, nothing moved, one line says the next run '
                      'moves it', text('precedent.json') == body
                      and tips() == before and not res.get('retired')
                      and len(steps) == 1 and steps[0][0] == 'pre-staging'
                      and 'run Update Vendors again' in steps[0][1],
                      str(steps)[:300]))
        git(work, 'reset', '-q', 'HEAD~1')
        git(work, 'checkout', '-q', 'HEAD', '--', 'tools/precedent_branches.py')
        # The second pass: the switch is made, whoever the maintainers are,
        # and the retirement runs in the same call below. A copy of a
        # practice from another source, which names pre-staging as an
        # instruction, is the source's to word, never this repository's.
        (work / 'practices').mkdir(exist_ok=True)
        borrowed = 'Push it to pre-staging.\n'
        (work / 'practices' / 'borrowed.md').write_text(borrowed, encoding='utf-8')
        (work / 'MANIFEST.json').write_text(_json.dumps({'practices': [
            {'slug': 'borrowed', 'source': 'precedent-individual'}]}),
            encoding='utf-8')
        git(work, 'add', 'practices/borrowed.md', 'MANIFEST.json')
        git(work, 'commit', '-q', '-m', 'a practice copied from a source')

        # --- the person who lands on staging, work waiting on pre-staging ---
        main_before, ps_before = tip('main'), tip('pre-staging')
        res, out = call('step')
        retired = res.get('retired') or []
        steps = res.get('steps') or []
        cases.append(('two maintainers, one of them running it: precedent.json\'s '
                      'landing_branch is switched to staging, every other byte '
                      'kept', text('precedent.json') == body.replace(
                          '"landing_branch": "pre-staging"',
                          '"landing_branch": "staging"'), text('precedent.json')))
        cases.append(('it is said in one line, before the retirement runs',
                      steps[:1] == [['precedent.json', 'landing_branch pre-staging '
                                     '-> staging: pre-staging is retired for '
                                     'everyone']]
                      and len(steps) == 2 and steps[1][0] == 'pre-staging',
                      str(steps)[:300]))
        cases.append(('the waiting work is brought into staging, with main\'s '
                      'direct work', on(waiting, 'staging') and on(direct, 'staging'),
                      failure_detail(out, 400)))
        cases.append(('nothing dropped: main and pre-staging did not move',
                      tip('main') == main_before and tip('pre-staging') == ps_before))
        cases.append(('the block says what was merged into staging',
                      any(l.startswith('merged into staging') for l in retired)
                      and any('ps.txt' in l for l in retired), str(retired)[:400]))
        cases.append(('and offers pre-staging for deletion with the filtered '
                      'link', any(l.endswith(link) for l in retired),
                      failure_detail(str(retired), 300)))
        now = text('AGENTS.md')
        cases.append(('a clear instruction is repointed',
                      'Work lands on `staging` and waits there.' in now
                      and 'Open a pull request into staging.' in now, now))
        cases.append(('a prompt quoted as an indented code block is left as '
                      'it was, and listed as code',
                      '    2. **Push to `pre-staging` (Booked) refused.**' in now
                      and any('AGENTS.md:21 (code block)' in l for l in retired),
                      str(retired)[:600]))
        cases.append(('an indented line that continues a list item is still '
                      'reworded', '    continued: push to `staging`.' in now, now))
        cases.append(('a sentence dated on its first line is history on every '
                      'line it wraps onto', 'follows: Push to `pre-staging` (Booked) '
                      'was refused.' in now
                      and any('AGENTS.md:27 (dated sentence, history)' in l
                              for l in retired), str(retired)[:700]))
        cases.append(('a phrase inside double quotes is a quotation, left as '
                      'it was', '"Push to `pre-staging` (Booked) refused"' in now
                      and any('AGENTS.md:29 (quotation, history)' in l
                              for l in retired), str(retired)[:700]))
        cases.append(('a link to this repo\'s pre-staging tree is repointed',
                      'https://github.com/o/r/tree/staging/docs' in now, now))
        cases.append(('a dated line, a Story section, a mention that is no '
                      'instruction and another repository\'s link are left',
                      '2026-10-01: we chose to push to pre-staging first.' in now
                      and 'Sessions push to pre-staging here.' in now
                      and 'Promote pre-staging into staging' in now
                      and 'github.com/x/y/tree/pre-staging' in now, now))
        cases.append(('each change and each mention left is listed, file:line',
                      any('reworded to staging: AGENTS.md:3 (instruction)' in l
                          for l in retired)
                      and any('AGENTS.md:5 (dated line, history)' in l
                              for l in retired)
                      and any('AGENTS.md:7 (link into another repository)' in l
                              for l in retired), str(retired)[:600]))
        cases.append(('a copy of another source\'s practice is left as it is, '
                      'and named with its source',
                      text('practices/borrowed.md') == borrowed
                      and any('practices/borrowed.md (from precedent-individual)' in l
                              for l in retired), str(retired)[:600]))
        cases.append(('the run that switched says precedent.json\'s comment, '
                      'one somebody wrote, still names pre-staging, and leaves it',
                      any(w == 'JSON comments naming pre-staging'
                          and why.endswith('precedent.json _landing_branch_comment')
                          for w, why in res.get('left', []))
                      and 'Work lands on pre-staging here.' in text('precedent.json'),
                      str(res.get('left'))[:600]))
        cases.append(('a gotcha is left alone, counted as history',
                      text(gotcha) == '# Trap\n\nPush to pre-staging failed.\n'
                      and any(l.startswith('left as history: 1 mention')
                              for l in retired), failure_detail(str(retired), 300)))
        res, out = call('offers')
        cases.append(('fully merged: never_offered drops pre-staging and keeps '
                      'staging and main', 'pre-staging' not in res.get('never', ['pre-staging'])
                      and {'staging', 'main'} <= set(res.get('never', []))
                      and 'pre-staging' not in res.get('vdc', ['pre-staging']),
                      failure_detail(out, 300)))
        # The stale-branch lister treats it as any branch since 2026-10-17:
        # offered once main has its work. Until then the step's own link
        # (above) is the offer.
        cases.append(('the stale-branch lister never offers staging or main',
                      not {'staging', 'main'} & set(res.get('stale', [])),
                      failure_detail(out, 300)))

        # --- a second run: nothing changes; it says retired, with the link ---
        # The person rewords the comment by hand, as the first run asked;
        # until then every run asks again
        # (check_update_vendors_replaces_the_old_landing_comment).
        (work / 'precedent.json').write_text(text('precedent.json').replace(
            'Work lands on pre-staging here.', 'Work lands on staging here.'),
            encoding='utf-8')
        before, docs = tips(), now
        res, out = call('step')
        retired = res.get('retired') or []
        cases.append(('a second run changes nothing',
                      tips() == before and text('AGENTS.md') == docs
                      and not any(l.startswith(('merged into', 'reworded'))
                                  for l in retired), str(retired)[:300]))
        cases.append(('and still says it is retired, with the link',
                      any(l.endswith(link) for l in retired), failure_detail(str(retired), 300)))
        cases.append(('and, the comment reworded, does not ask about it again',
                      not any(w.startswith(('precedent.json', 'JSON comments'))
                              for w, _ in res.get('left', [])),
                      str(res.get('left'))[:300]))

        # --- a conflict: nothing moves, nothing is reworded, no offer ---
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'reworded')
        git(work, 'push', '-q', 'origin', 'HEAD:main')
        commit_on('pre-staging', 'list.txt', 'from pre-staging\n')
        commit_on('staging', 'list.txt', 'from staging\n')
        (work / 'more.md').write_text('Push it to pre-staging.\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'more')
        before = tips()
        res, out = call('step')
        cases.append(('a conflict stops: nothing moved',
                      tips() == before, failure_detail(out, 300)))
        cases.append(('nothing reworded, and no delete offer',
                      text('more.md') == 'Push it to pre-staging.\n'
                      and not res.get('retired'), str(res)[:300]))
        cases.append(('it says what to do, naming --land',
                      any(w == 'pre-staging' and '--land' in why
                          and 'Nothing moved' in why
                          for w, why in res.get('left', [])), str(res)[:400]))

        # --- after the run that moved it, a new mention is deliberate ---
        # (2026-10-09, reported by another session: a note quoting the old
        # instruction was reworded on the update after the move.)
        import precedent_update as _pu_direct
        import migration_retire_pre_staging as _pu_direct_m
        _pu_direct_m.pu = _pu_direct
        _pu_direct = _pu_direct_m
        cases.append(('once the switch to staging is committed, later runs '
                      'reword nothing', not _pu_direct.rewords_this_run(work, False, False)))
        cases.append(('the run that switches, or brings pre-staging\'s work '
                      'in, rewords', _pu_direct.rewords_this_run(work, True, False)
                      and _pu_direct.rewords_this_run(work, False, True)))

        # --- once it is gone: never made again, and nothing said ---
        git(bare, 'update-ref', '-d', 'refs/heads/pre-staging')
        git(work, 'fetch', '-q', '--prune', 'origin')
        res, out = call('tiers')
        cases.append(('ensure_tiers does not make pre-staging again for them',
                      res.get('rc') == 0 and not tip('pre-staging'), failure_detail(out, 300)))
        res, out = call('step')
        # Since 2026-10-18 it still names the live mentions left -- until
        # then nothing read them once pre-staging was gone
        # (check_update_vendors_reports_live_pre_staging_mentions).
        left = res.get('left') or []
        cases.append(('and the step moves nothing, rewords nothing, and only '
                      'names the live mentions still left',
                      not res.get('steps') and not res.get('retired')
                      and [w for w, _ in left] == ['Markdown naming pre-staging']
                      and 'more.md:1' in left[0][1]
                      and text('more.md') == 'Push it to pre-staging.\n',
                      failure_detail(out, 300)))
    # Where it runs: a migration, which update() runs without naming it,
    # before the views are regenerated, so they render the reworded sources.
    import inspect
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as _pu
        src = inspect.getsource(_pu.update)
        runner = inspect.getsource(_pu.migrations_step)
    except Exception as e:                                   # noqa: BLE001
        src = runner = f'{type(e).__name__}: {e}'
    finally:
        sys.path.pop(0)
    step = src.find('migrations_step(repo, rep)')
    views = src.find("sync = repo / 'tools' / 'precedent_sync_views.py'")
    cases.append(('update() runs the migrations before it regenerates the '
                  'views', 0 <= step < views, src[:120] if step < 0 else ''))
    cases.append(('update() names no migration, and the runner finds this one '
                  'by its file name alone', 'pre_staging' not in src + runner
                  and "glob('migration_*.py')" in runner
                  and (ROOT / 'tools' / 'migration_retire_pre_staging.py').is_file(),
                  runner[:200]))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_update_in_force_nowhere_asks_once():
    """A rule in force nowhere is asked about until precedent.json records
    that it does not apply here, by slug or by the set it lives in, and
    then said in one line instead (2026-10-01, from a consumer's Update
    Vendors: sixteen of them asked on every update, under a header that
    contradicted itself)."""
    import contextlib, io, tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-nowhere-'))
    cases = []
    out = ('precedent_sync_views: IN FORCE NOWHERE -- planted-link-text '
           '(precedent-shared-repo-maintenance): status: deduplicated names '
           'in_force_at: planted-link-text, but nothing resolves it\n'
           'precedent_sync_views: IN FORCE NOWHERE -- old-rule (precedent): '
           'withdrawn from universal on 2026-09-20; in force in '
           '`acme-shared-writing` -- declare that set to keep it\n')
    try:
        repo = tmp / 'consumer'
        repo.mkdir()

        def run(cfg):
            (repo / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.in_force_nowhere_step(repo, rep, out)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rep.close()
            return rep, buf.getvalue()
        rep, text = run({})
        cases.append(('unrecorded, each is asked, with the snippet that records it',
                      len(rep.asks) == 2 and all('not_in_force_here' in q
                                                 for _w, q in rep.asks), str(rep.asks)))
        cases.append(('...naming the set when the finding knows it',
                      any('`acme-shared-writing`' in q for _w, q in rep.asks),
                      str(rep.asks)))
        cases.append(('the header no longer contradicts itself',
                      'blocks the update' not in text and 'before Go update'
                      not in text and 'QUESTIONS FOR THE PERSON' in text, failure_detail(text, 600)))
        rep, _ = run({'not_in_force_here': {'planted-link-text': 'we dropped that set',
                                            'acme-shared-writing': 'dropped'}})
        cases.append(('recorded by slug and by set, nothing is asked',
                      not rep.asks, str(rep.asks)))
        cases.append(('...and they are said in one step line',
                      [n for n, _o in rep.steps] == ['not in force here, on purpose'],
                      str(rep.steps)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors asks about a rule in force nowhere until it is '
          f'recorded ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_done_names_the_check_it_ran():
    """Update Vendors' DONE says which check it ran, that the full check did
    not run, and passes on a size-cap warning the check printed.

    2026-10-01, from a consumer's Update Vendors: the update printed "check
    for <its landing tier>: passed" and DONE; the consumer's full check then failed
    three ways on the same tree, one of them a size cap this update's own
    regenerated AGENTS.md block had pushed over. The basic check is right
    for the landing tier; reading as the push gate's all-clear was not."""
    import contextlib, io, tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-done-tier-'))
    cases = []
    real = pu.check_with_merge_fallback
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'precedent_push_check.py').write_text('', encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps(
            {'base_branch': 'main', 'staging_branch': 'staging',
             'landing_branch': 'staging', 'promote_only': True}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')

        def run(out):
            pu.check_with_merge_fallback = lambda _r, _rep, _a, _l: (0, out)
            rep = pu.Report()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = pu.closing_check(repo, rep)
            return rc, buf.getvalue()
        try:
            rc, out = run('precedent_push_check: all passed\n')
            cases.append(('the step names the tier it ran',
                          'basic check for staging: passed' in out, failure_detail(out, 600)))
            cases.append(('DONE says the full check was NOT run, and how to run it',
                          rc == pu.DONE and 'full check was NOT run' in out
                          and '--tier full' in out, failure_detail(out, 600)))
            rc, out = run('passed\nWARNING: over a session-load size cap '
                          '(changed_practice, above). The quick check lets it '
                          'through; the full check refuses it.\n')
            cases.append(('a size-cap warning the check printed is repeated '
                          'beside DONE', 'WARNING: over a session-load size cap'
                          in out.split('== Update Vendors ==')[-1], failure_detail(out, 600)))
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved
    finally:
        pu.check_with_merge_fallback = real
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors\' DONE names the check it ran and the one it did '
          f'not ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_finds_the_clone_by_its_origin():
    """The BestPractice clone is found by its origin remote, any case, at
    the attach tool's <owner>/<repo> path as well as ../BestPractice: by
    precedent_merge_vendors.find_source and by the update's own refusal of a
    vendored copy, which names the command to run.

    WHY. 2026-10-08, from a consumer: the attach tool cloned BestPractice at
    a lowercase alex137/bestpractice path, and the runbook's
    ../BestPractice found nothing there.

    Negative control, measured 2026-10-08: before the fix find_source
    returned None for this layout and pve had no find_source_clones."""
    import tempfile
    pu, pve, _pr = _update_tools()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_merge_vendors as pmv
    finally:
        sys.path.pop(0)
    env = _fixture_git_env()
    cases = []
    saved = os.environ.pop('PRECEDENT_SOURCE_CLONE', None)
    try:
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)

            def clone(rel, origin):
                d = base / rel
                (d / 'tools').mkdir(parents=True)
                (d / 'tools' / 'precedent_update.py').write_text('', encoding='utf-8')
                subprocess.run(['git', 'init', '-q', str(d)], env=env, capture_output=True)
                subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin', origin],
                               env=env, capture_output=True)
                return d.resolve()
            consumer = base / 'consumer'
            consumer.mkdir()
            subprocess.run(['git', 'init', '-q', str(consumer)], env=env, capture_output=True)
            decoy = clone('elsewhere', 'https://github.com/someone/other.git')
            cases.append(('CONTROL: a clone of another repository is not taken',
                          pve.find_source_clones(consumer) == []
                          and pmv.find_source(consumer) is None,
                          pve.find_source_clones(consumer)))
            attached = clone('alex137/bestpractice',
                             'http://127.0.0.1:1/git/alex137/BestPractice')
            got = pve.find_source_clones(consumer)
            cases.append(('the attach tool\'s lowercase alex137/bestpractice clone '
                          'is found by its origin', got == [attached], got))
            cases.append(('...by the merge step too',
                          pmv.find_source(consumer) == attached,
                          pmv.find_source(consumer)))
            cases.append(('...and the update\'s refusal names the command to run',
                          pu.clone_command(consumer) ==
                          'python3 ../alex137/bestpractice/tools/precedent_update.py '
                          '--repo .', pu.clone_command(consumer)))
            beside = clone('BestPractice', 'https://github.com/alex137/BestPractice.git')
            got = pve.find_source_clones(consumer)
            cases.append(('../BestPractice stays first when it is one',
                          got[:1] == [beside] and attached in got and decoy not in got,
                          got))
    finally:
        if saved is not None:
            os.environ['PRECEDENT_SOURCE_CLONE'] = saved
    runbook = (ROOT / 'practices' / 'vendor-update-runbook.md').read_text(encoding='utf-8')
    cases.append(('the runbook says the clone is any checkout whose origin is '
                  'BestPractice', 'any checkout whose origin is' in runbook, ''))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors finds the BestPractice clone by its origin '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_install_and_update_write_the_owners_zone():
    """In a repository with exactly one maintainer and no fallback_timezone,
    install and Update Vendors write that person's own zone as
    precedent.json's fallback_timezone when the person running them is that
    maintainer with a zone in their identity.json, and say so. A
    precedent.json that already has the key is never touched, whatever its
    value.

    WHY. 2026-10-08, from a consumer: a single person's repository never
    declared fallback_timezone, so its GitHub Actions job dated failure
    records and issue stamps in the engine's last resort (New York, the
    right team default) instead of its owner's zone. From then until
    2026-10-28 it was offered as a question; Morgan, 2026-10-28 (strength:
    decided): "Go, fix it in the engine; leave the shared sets" -- the
    owner's identity already declares the zone, so asking was the failure.

    Negative control, measured 2026-10-28: on the engine before this change
    (timezone_offer) the update asked and wrote nothing, so the 'written'
    cases fail there."""
    import tempfile
    pu, pve, _pr = _update_tools()
    cases = []
    # The session's own PRECEDENT_COMMIT_* override names a person and a
    # zone, which would answer for the fixture's identity.json.
    ours = ('PRECEDENT_USER_CONFIG', 'PRECEDENT_GITHUB_USER', 'PRECEDENT_COMMIT_EMAIL',
            'PRECEDENT_COMMIT_NAME', 'PRECEDENT_COMMIT_TZ')
    saved = {k: os.environ.get(k) for k in ours}
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            indiv = tmp / 'individual'
            indiv.mkdir()
            zone = 'America/Argentina/Buenos_Aires'
            ident = {'name': 'Solo', 'email': 'solo@example.com', 'github': 'solo',
                     'timezone': zone}
            (indiv / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')
            cfg = tmp / 'config.json'
            cfg.write_text(json.dumps({'individual': {'path': str(indiv)}}),
                           encoding='utf-8')
            for k in ours:
                os.environ.pop(k, None)
            os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
            repo = tmp / 'repo'
            repo.mkdir()

            def run(data, pretty=True):
                text = json.dumps(data, indent=2 if pretty else None) + '\n'
                (repo / 'precedent.json').write_text(text, encoding='utf-8')
                got = pve.apply_owner_timezone(repo)
                return got, json.loads((repo / 'precedent.json').read_text())
            one = {'maintainers': [{'github': 'solo'}], 'format_version': 1}
            got, after = run(one)
            cases.append(('one maintainer, who is running it, with a zone: written',
                          got == ('solo', zone)
                          and after == dict(one, fallback_timezone=zone), after))
            got, after = run(one, pretty=False)
            cases.append(('...also into a one-line precedent.json',
                          after.get('fallback_timezone') == zone
                          and after.get('maintainers') == one['maintainers'], after))
            got, after = run(dict(one, fallback_timezone='America/New_York'))
            cases.append(('a fallback_timezone already declared (a shared set\'s '
                          'New York): left as it is',
                          got is None and after['fallback_timezone'] == 'America/New_York',
                          after))
            got, after = run(dict(one, fallback_timezone=None))
            cases.append(('the key present but empty: left as it is',
                          got is None and after['fallback_timezone'] is None, after))
            for label, data in (
                    ('two maintainers', {'maintainers': [{'github': 'solo'},
                                                         {'github': 'other'}]}),
                    ('someone else running it', {'maintainers': [{'github': 'other'}]}),
                    ('no maintainers', {'format_version': 1})):
                got, after = run(data)
                cases.append((f'{label}: nothing written',
                              got is None and 'fallback_timezone' not in after, after))
            (indiv / 'identity.json').write_text(json.dumps(
                dict(ident, timezone='')), encoding='utf-8')
            got, after = run(one)
            cases.append(('no zone in identity.json: nothing written',
                          got is None and 'fallback_timezone' not in after, after))
            (indiv / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')

            (repo / 'precedent.json').write_text(json.dumps(one), encoding='utf-8')
            rep = pu.Report()
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                pu.maintainers_step(repo, rep)
            cases.append(('Update Vendors writes it, reports it, and asks nothing',
                          json.loads((repo / 'precedent.json').read_text()).get(
                              'fallback_timezone') == zone
                          and any(zone in str(s) for s in rep.steps)
                          and not any(w == 'time zone' for w, _q in rep.asks),
                          (rep.steps, rep.asks)))

            proj = tmp / 'installed'
            proj.mkdir()
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(proj)],
                           env=_fixture_git_env(), capture_output=True)
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                                str(proj), '--project-name', 'Solo'], cwd=str(ROOT),
                               env=dict({k: v for k, v in _fixture_git_env().items()
                                         if k not in ours},
                                        PRECEDENT_USER_CONFIG=str(cfg), HOME=str(tmp)),
                               capture_output=True, text=True)
            out = r.stdout + r.stderr
            cases.append(('install writes it too, and says so',
                          'time zone: wrote' in out
                          and json.loads((proj / 'precedent.json').read_text(
                              encoding='utf-8')).get('fallback_timezone') == zone,
                          failure_detail(out, 1200)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'install and Update Vendors write a single owner\'s zone as the '
          f'fallback, and leave a declared one alone ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_update_vendors_maps_a_task_kind_to_manual():
    """An open item filed as `kind: task` (or todo, action, chore) is moved
    to `manual` by Update Vendors' migration, and the report names it, so
    the update's generated-files step never stops on build_todo_index.py's
    refusal (2026-10-17, a document project's Update Vendors: it failed half
    way on "A `task` is usually `manual`"). A done item, and a kind that is
    already legal, are left alone; the update runs the migration unnamed."""
    import importlib.util, inspect, tempfile
    name = 'Update Vendors moves an open item\'s `task` kind to `manual`'
    path = ROOT / 'tools' / 'migration_todo_kind_synonyms.py'
    if not path.is_file():
        check(name, False, 'tools/migration_todo_kind_synonyms.py is missing')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec = importlib.util.spec_from_file_location('_vh_mig_kinds', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    pu, _pve, _pr = _update_tools()
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-task-kind-'))
    try:
        (tmp / 'todo').mkdir()

        def item(slug, kind, status):
            (tmp / 'todo' / f'todo-{slug}.md').write_text(
                f'---\nslug:              todo-{slug}\nkind:              {kind}\n'
                f'status:            {status}\n---\n## What\n\nBody `kind: task`.\n',
                encoding='utf-8')
        item('a', 'task', 'open')
        item('b', 'chore', 'done')
        item('c', 'verify', 'open')
        rep = pu.Report()
        mod.migrate(tmp, rep, pu)
        a = (tmp / 'todo' / 'todo-a.md').read_text(encoding='utf-8')
        cases.append(('an open `task` item becomes `manual`, frontmatter only',
                      'kind:              manual\n' in a and 'Body `kind: task`.' in a, a))
        cases.append(('a done item and a legal kind are untouched',
                      'kind:              chore' in (tmp / 'todo' / 'todo-b.md').read_text()
                      and 'kind:              verify' in (tmp / 'todo' / 'todo-c.md').read_text()))
        said = ' '.join(o for n, o in rep.steps if n == 'open items')
        cases.append(('the report names the file and what it was',
                      'todo/todo-a.md (was `task`)' in said, said))
        cases.append(('Update Vendors runs every migration file unnamed',
                      "glob('migration_*.py')" in inspect.getsource(pu.migrations_step)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_update_vendors_reports_dropped_template_wording():
    """An install-once file still carrying wording its template has since
    dropped is left for the person, by file and line -- and nothing else is.

    2026-09-28, very deep check: the files an install writes once from a
    template (the PR template, TODO.md, MAP.md ...) kept old wording -- a
    "TODO.md updated" checklist line, links to a retired branch -- and no
    update said so. The report must flag only an exact line an older
    version of the template carried and the current one does not, so a
    repo's own lines are never flagged; it must never write the file; and a
    file precedent.json records as kept on purpose, against the current
    template, must stop being listed."""
    import contextlib, inspect, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dropped-wording-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    cases = []
    saved_source = pu.SOURCE
    step = getattr(pu, 'dropped_template_lines_step', None)
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        tmpl = src / 'templates' / 'TODO.md.template'
        tmpl.write_text('# Open items live in this file for now\n'
                        '## Old\n'
                        '- [ ] TODO.md updated with the items opened and closed\n'
                        'See [the plan](https://example.com/blob/old-branch/spec/PLAN.md) for more.\n'
                        'Every open item is tracked in one place here.\n',
                        encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        tmpl.write_text('# Open items live under todo/ now\n'
                        'See [the plan](https://example.com/blob/staging/spec/PLAN.md) for more.\n'
                        'Every open item is tracked in one place here.\n',
                        encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v2')
        rev = git(src, 'rev-parse', 'HEAD').stdout.strip()

        repo = tmp / 'consumer'
        repo.mkdir()
        body = ('# Open items live in this file for now\n'
                '## Old\n'
                '- [ ] TODO.md updated with the items opened and closed\n'
                'See [the plan](https://example.com/blob/old-branch/spec/PLAN.md) for more.\n'
                'Every open item is tracked in one place here.\n'
                'Our own note about the billing export, written by this repo.\n')
        (repo / 'TODO.md').write_text(body, encoding='utf-8')
        pu.SOURCE = src

        if step is None:
            cases.append(('precedent_update has a dropped-template-wording step',
                          False, 'dropped_template_lines_step is missing'))
        else:
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            left = dict(rep.left)
            cases.append(('a line an older template carried and the current one '
                          'dropped is left for you, by file and line',
                          'TODO.md:3' in left and 'is template wording the current '
                          'template dropped: - [ ] TODO.md updated' in left['TODO.md:3'],
                          str(rep.left)))
            cases.append(('...and so is a reworded one, a link to a retired branch',
                          'TODO.md:4' in left and 'old-branch' in left['TODO.md:4']
                          and 'TODO.md:1' in left, str(rep.left)))
            cases.append(('a line the current template still carries, the '
                          'repo\'s own line, and a too-short heading are not',
                          sorted(left) == ['TODO.md:1', 'TODO.md:3', 'TODO.md:4'],
                          str(sorted(left))))
            cases.append(('the file is only reported, never written',
                          (repo / 'TODO.md').read_text(encoding='utf-8') == body, ''))
            cases.append(('the first item says how to record it as kept, with the '
                          'current template\'s hash',
                          any(pve.KEPT_DIVERGENCES_KEY in d and hashlib.sha256(
                              tmpl.read_bytes()).hexdigest() in d
                              for d in rep.details.get('TODO.md:1', [])),
                          str(rep.details)))

            sha = hashlib.sha256(tmpl.read_bytes()).hexdigest()
            (repo / 'precedent.json').write_text(json.dumps({
                pve.KEPT_DIVERGENCES_KEY: {'TODO.md': {
                    'reason': 'kept on purpose', 'template_sha256': sha}}}),
                encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            cases.append(('a file recorded as kept against the current template '
                          'is said once and not listed',
                          not rep.left and any(n == 'kept on purpose'
                                               for n, _o in rep.steps),
                          str(rep.left)))
            (repo / 'precedent.json').write_text(json.dumps({
                pve.KEPT_DIVERGENCES_KEY: {'TODO.md': {
                    'reason': 'kept on purpose', 'template_sha256': '0' * 64}}}),
                encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            # ONE QUESTION FOR A FILE KEPT WHOLE (2026-10-17, a consuming
            # repository): its kept rewrite was left as one item per line,
            # each saying "or drop the line"; and a line the update carried
            # in by itself went unsaid.
            cases.append(('...and asked again once the template has changed '
                          'since: one item for the file, never one per line',
                          sorted(dict(rep.left)) == ['TODO.md'], str(rep.left)))
            v1_sha = hashlib.sha256(git(src, 'show', f'{rev}~1:templates/'
                                        'TODO.md.template').stdout.encode()).hexdigest()
            (repo / 'precedent.json').write_text(json.dumps({
                pve.KEPT_DIVERGENCES_KEY: {'TODO.md': {
                    'reason': 'kept on purpose', 'template_sha256': v1_sha}}}),
                encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            said = ' '.join(dict(rep.left).values()) + ' ' + ' '.join(
                rep.details.get('TODO.md', []))
            cases.append(('...which never says to drop a line, shows what the '
                          'template changed, and the hash to record',
                          'drop the line' not in said
                          and 'what changed in templates/TODO.md.template' in said
                          and hashlib.sha256(tmpl.read_bytes()).hexdigest() in said,
                          said[:400]))
            git(repo, 'init', '-q')
            git(repo, 'add', 'TODO.md')
            git(repo, 'commit', '-qm', 'kept rewrite')
            (repo / 'TODO.md').write_text(
                body + 'A bullet the update carried in from the template.\n',
                encoding='utf-8')
            rep = pu.Report()
            rep.before = set()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            said = ' '.join(rep.details.get('TODO.md', []))
            cases.append(('...and says what this update already carried into it',
                          'already carried 1 line(s)' in said
                          and 'A bullet the update carried in' in said, said[:400]))
            git(repo, 'checkout', '-q', '--', 'TODO.md')
            shutil.rmtree(repo / '.git', ignore_errors=True)

            # A file that is, byte for byte, an older version of its
            # template was never made the repository's own: it takes the
            # current template, and says so -- one meant to be adapted (this
            # TODO.md) as well, since 2026-10-17 (untouched_install_copy).
            (repo / 'precedent.json').unlink()
            v1 = git(src, 'show', f'{rev}~1:templates/TODO.md.template').stdout
            (repo / 'TODO.md').write_text(v1, encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev)
            cases.append(('an adaptable template left exactly as installed takes '
                          'the current one, said once, not left for you',
                          not rep.left and (repo / 'TODO.md').read_bytes()
                          == tmpl.read_bytes()
                          and any(n == 'templates taken' for n, _o in rep.steps),
                          f'{rep.left} {rep.steps}'))
            (repo / 'TODO.md').unlink()
            prt = src / 'templates' / 'pull_request_template.md.template'
            pr_v1 = ('<!-- Copy verbatim, per INSTALL.md section 1. -->\n'
                     '## What changed\n')
            prt.write_text(pr_v1, encoding='utf-8')
            git(src, 'add', '-A')
            git(src, 'commit', '-qm', 'pr v1')
            prt.write_text('<!-- Copy verbatim, per INSTALL.md section 0. -->\n'
                           '## What changed\n', encoding='utf-8')
            git(src, 'add', '-A')
            git(src, 'commit', '-qm', 'pr v2')
            rev2 = git(src, 'rev-parse', 'HEAD').stdout.strip()
            pr = repo / '.github' / 'pull_request_template.md'
            pr.parent.mkdir()
            pr.write_text(pr_v1, encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev2)
            cases.append(('a copy-verbatim template that is word for word an older '
                          'version takes the current one, said once, not left for you',
                          not rep.left and any(n == 'templates taken'
                                               for n, _o in rep.steps)
                          and pr.read_bytes() == prt.read_bytes(),
                          f'{rep.left} {rep.steps}'))
            pr.write_text(pr_v1 + 'One line of our own.\n', encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev2)
            cases.append(('...but one edit of its own and it is only reported, '
                          'never written',
                          rep.left and pr.read_text(encoding='utf-8')
                          == pr_v1 + 'One line of our own.\n', str(rep.left)))
            pr.write_text(pr_v1, encoding='utf-8')
            (repo / 'precedent.json').write_text(json.dumps({
                pve.KEPT_DIVERGENCES_KEY: {'.github/pull_request_template.md': {
                    'reason': 'kept on purpose', 'template_sha256': '0' * 64}}}),
                encoding='utf-8')
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, rev2)
            cases.append(('...and a file recorded as kept is never written, even '
                          'when it is an older template word for word',
                          pr.read_text(encoding='utf-8') == pr_v1, str(rep.steps)))
            cases.append(('Update Vendors runs the step',
                          'dropped_template_lines_step(' in inspect.getsource(pu.update),
                          ''))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors reports install-once wording its template dropped '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_says_once_that_commands_moved_to_an_undeclared_set():
    """When an update leaves standing commands the old AGENTS.md listed in
    force nowhere here, because upstream moved their practices to an
    optional set this repository does not declare, it says so in one line:
    how many, and where -- never the phrases themselves.

    2026-10-17, very deep check: an update of an install from before
    2026-10-02 removed every ladder command from its instructions without a
    word (17 phrases, measured on a scratch install at 2026-10-01 main).
    By design for a repository off the ladder; the decision (the session's,
    under Morgan's delegation of 2026-10-17) is one line, without the words,
    which a person off the ladder never reads. Planted: an old index with
    two commands, one of them withdrawn to a set in upstream's record."""
    import tempfile
    pu, _pve, _pr = _update_tools()
    step = getattr(pu, 'moved_commands_step', None)
    name = 'Update Vendors says once that commands moved to a set this repo does not declare'
    if step is None:
        check(name, False, 'precedent_update has no moved_commands_step: the commands '
              'go without a word')
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-moved-commands-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    cases = []
    saved = pu.SOURCE
    try:
        src = tmp / 'source'
        (src / 'record').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(src)], env=env, capture_output=True)
        (src / pu.WITHDRAWN_RECORD).write_text(
            '- 2026-10-02: `zap-it` withdrawn from universal, deliberately; in force '
            'only from the shared set `precedent-shared-zap`, for the people who '
            'bring or declare it.\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(src), 'add', '-A'], env=env, capture_output=True)
        subprocess.run(['git', '-C', str(src), 'commit', '-qm', 'r'], env=env,
                       capture_output=True)
        rev = subprocess.run(['git', '-C', str(src), 'rev-parse', 'HEAD'],
                             capture_output=True, text=True).stdout.strip()
        pu.SOURCE = src
        old = ('## Occasion index\n\n```\n'
               'When a person says "Zap" or "Zap twice":\n'
               '  zap-it — do the zap\n'
               'When a person says "Keep":\n'
               '  keep-it — keep it\n```\n')
        new = ('## Occasion index\n\n```\nWhen a person says "Keep":\n'
               '  keep-it — keep it\n```\n')
        repo = tmp / 'repo'
        repo.mkdir()
        (repo / 'AGENTS.md').write_text(new, encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'}]}),
            encoding='utf-8')
        rep = pu.Report()
        step(repo, rep, old, rev)
        said = [o for n, o in rep.steps if n == 'standing commands']
        cases.append(('one line, with the count and the set',
                      len(said) == 1 and said[0].startswith('2 command phrase(s)')
                      and 'precedent-shared-zap' in said[0], str(rep.steps)))
        cases.append(('...never the phrases themselves', said and 'Zap' not in said[0],
                      str(said)))
        cases.append(('nothing is left for the person', not rep.left, str(rep.left)))
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'precedent-shared-zap', 'path': '../zap'}]}),
            encoding='utf-8')
        rep = pu.Report()
        step(repo, rep, old, rev)
        cases.append(('silent where the repo declares that set',
                      not [o for n, o in rep.steps if n == 'standing commands'],
                      str(rep.steps)))
        rep = pu.Report()
        step(repo, rep, new, rev)
        cases.append(('silent when nothing listed before is gone', not rep.steps,
                      str(rep.steps)))
    except OSError as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        pu.SOURCE = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_dropped_wording_reads_placeholders_filled():
    """A line that is the CURRENT template's line with its placeholders
    filled in is not dropped wording, even when it equals an older template
    line word for word.

    2026-10-01, from a consumer's Update Vendors: GETTING_STARTED.md's
    template once wrote `process/upstream/` and now writes `<upstream-docs>/`,
    and a §1 install is told to replace the second with the first. The
    install did exactly that, and the update listed the result as wording
    the template had dropped. A line an older template had that no current
    line can be filled in to produce is still listed."""
    import contextlib, io, tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dropped-filled-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    cases = []
    saved_source = pu.SOURCE
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        tmpl = src / 'templates' / 'TODO.md.template'
        tmpl.write_text('<!-- not just a mention in the install log under\n'
                        '     `process/upstream/`. Add a line whenever a future install step\n'
                        '     introduces a new one. -->\n'
                        'Read the guide in process/upstream/documentation before you start.\n',
                        encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        tmpl.write_text('<!-- not just a mention in the install log under\n'
                        '     `<upstream-docs>/`. Add a line whenever a future install step\n'
                        '     introduces a new one. -->\n'
                        'Read the guide at <upstream-docs> before you begin.\n',
                        encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v2')
        rev = git(src, 'rev-parse', 'HEAD').stdout.strip()

        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'TODO.md').write_text(
            '<!-- not just a mention in the install log under\n'
            '     `process/upstream/`. Add a line whenever a future install step\n'
            '     introduces a new one. -->\n'
            'Read the guide in process/upstream/documentation before you start.\n'
            # A line of the repository's own, so the file is not an
            # untouched install copy, which takes the current template whole.
            'Our own note about the planting calendar, written by this repo.\n',
            encoding='utf-8')
        pu.SOURCE = src
        rep = pu.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            pu.dropped_template_lines_step(repo, rep, rev)
        left = dict(rep.left)
        cases.append(('the current line with its placeholder filled in is not '
                      'listed, though an older template had it verbatim',
                      'TODO.md:2' not in left, str(rep.left)))
        cases.append(('a line no current line can be filled in to make still is',
                      'TODO.md:4' in left, str(rep.left)))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors reads a template\'s placeholders as filled in '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_names_what_others_changed_upstream():
    """Update Vendors' report carries what OTHER people changed upstream in
    what the update brings in, for the session to open its report with.

    WHY. Morgan, 2026-10-12 ("Yes, build it"): an Update Vendors in a
    consuming repository took in a colleague's new rules without a word
    about them, since the morning report covers only the repository a
    session works in. Planted: upstream gains a colleague's commit and one
    of the person's own between the two vendored commits -- only the
    colleague's is listed, with the instruction; no range, nothing; a
    person off the ladder, nothing; a commit the clone lacks, said plainly.
    CONTROL: the morning report's own block still reads as it did."""
    import tempfile
    pu, _pve, _pr = _update_tools()
    import precedent_commit_owners as od
    import precedent_identity as pi
    cases = []
    saved = (pu.SOURCE, pi.declared_identity, pu._off_ladder)
    with tempfile.TemporaryDirectory() as td:
        src = pathlib.Path(td) / 'source'
        src.mkdir()

        def commit(name, email, msg):
            env = dict(_fixture_git_env(), GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
                       GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
            (src / 'f.txt').write_text(msg, encoding='utf-8')
            subprocess.run(['git', '-C', str(src), 'add', '-A'], env=env,
                           capture_output=True)
            subprocess.run(['git', '-C', str(src), 'commit', '-qm', msg], env=env,
                           capture_output=True)
            return subprocess.run(['git', '-C', str(src), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True).stdout.strip()
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(src)], capture_output=True)
        old = commit('Me', 'me@example.com', 'where this repo last synced')
        commit('Colleague', 'them@example.com', 'Refuse an item that names no blocker')
        new = commit('Me', 'me@example.com', 'my own change')
        try:
            pu.SOURCE = src
            pi.declared_identity = lambda *_a, **_k: {'name': 'Me', 'email': 'me@example.com'}
            pu._off_ladder = lambda *_a, **_k: False
            block = pu.upstream_changes_block(pathlib.Path(td), old, new)
            cases.append(('a colleague\'s upstream commit is listed, with the '
                          'instruction to open the report with it',
                          'WHAT OTHERS CHANGED UPSTREAM' in block
                          and 'Colleague -- 1 commit(s)' in block
                          and 'Refuse an item that names no blocker' in block
                          and 'OPEN YOUR REPORT OF THIS UPDATE' in block, block))
            cases.append(('...and the person\'s own is not',
                          'my own change' not in block, block))
            cases.append(('nothing new upstream, nothing said',
                          pu.upstream_changes_block(pathlib.Path(td), new, new) == '', ''))
            got = pu.upstream_changes_block(pathlib.Path(td), '0' * 40, new)
            cases.append(('a commit the clone lacks is said plainly',
                          got.startswith('WHAT OTHERS CHANGED UPSTREAM: could not be read'),
                          got))
            # The shared sets, the same evening (Morgan: "yes extend it").
            setc = pathlib.Path(td) / 'a-set'
            setc.mkdir()
            env0 = _fixture_git_env()
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(setc)],
                           capture_output=True, env=env0)

            def set_commit(name, email, msg):
                env = dict(env0, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
                           GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
                (setc / 'p.md').write_text(msg, encoding='utf-8')
                subprocess.run(['git', '-C', str(setc), 'add', '-A'], env=env,
                               capture_output=True)
                subprocess.run(['git', '-C', str(setc), 'commit', '-qm', msg],
                               env=env, capture_output=True)
                return subprocess.run(['git', '-C', str(setc), 'rev-parse', 'HEAD'],
                                      capture_output=True, text=True).stdout.strip()
            s_old = set_commit('Me', 'me@example.com', 'set as last synced')
            s_new = set_commit('Colleague', 'them@example.com', 'A set rule changed')
            block = pu.upstream_changes_block(pathlib.Path(td), new, new,
                                              [('a-set', setc, s_old, s_new)])
            cases.append(('a colleague\'s change to a shared set is listed under '
                          'the set, with the instruction',
                          'a-set (' in block and 'A set rule changed' in block
                          and 'OPEN YOUR REPORT OF THIS UPDATE' in block, block))
            repo2 = pathlib.Path(td) / 'consumer'
            repo2.mkdir()

            def manifest(commit):
                (repo2 / 'MANIFEST.json').write_text(json.dumps({'sources': [
                    {'level': 'universal', 'name': 'precedent', 'path': '../source'},
                    {'level': 'shared', 'name': 'a-set', 'path': '../a-set',
                     'commit': commit}]}), encoding='utf-8')
            manifest(s_old)
            before = pu.set_pins(repo2)
            manifest(s_new)
            moved = pu.sets_moved(before, pu.set_pins(repo2))
            cases.append(('the sync\'s recorded commits say which set moved, and '
                          'from where to where (universal left to its own range)',
                          moved == [('a-set', setc.resolve(), s_old, s_new)], moved))
            # 2026-10-12, a consuming repository: cloud sessions clone with
            # --depth 1, the last-vendored commit was missing, and the block
            # said "could not be read" over 110 commits.
            shallow = pathlib.Path(td) / 'shallow'
            subprocess.run(['git', 'clone', '-q', '--depth', '1',
                            f'file://{src}', str(shallow)], capture_output=True,
                           env=_fixture_git_env())
            lacks = subprocess.run(['git', '-C', str(shallow), 'cat-file', '-e',
                                    f'{old}^{{commit}}'], capture_output=True).returncode
            got = pu.upstream_by_others(pathlib.Path(td), old, new, shallow)
            cases.append(('a depth-1 clone lacking the old commit is deepened and '
                          'read', lacks != 0 and got is not None
                          and any(w == 'Colleague' for _s, w, _t in got[0]), got))
            pu._off_ladder = lambda *_a, **_k: True
            cases.append(('a person off the ladder gets nothing',
                          pu.upstream_changes_block(pathlib.Path(td), old, new) == '', ''))
        finally:
            pu.SOURCE, pi.declared_identity, pu._off_ladder = saved
    listing = od.commit_listing([('a' * 40, 'Colleague', 'x')], [])
    cases.append(('CONTROL: the shared listing still says who, by person',
                  listing.startswith('The commits, to choose from')
                  and 'Colleague -- 1 commit(s):\n  aaaaaaaaa  x' in listing, listing))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors names what others changed upstream ({len(cases)} '
          f'stated cases)', not bad, '; '.join(bad))


def check_kept_pin_moves_across_a_comment_only_template_change():
    """A file kept on purpose against its template is not asked about again
    when the template's only change since the pin is inside an HTML
    comment; a change a reader sees is still asked, with the change shown.

    WHY. A consuming repository's Update Vendors, 2026-10-12: a kept
    GETTING_STARTED.md was left for the person again because the template's
    only change was in a comment ("INSTALL.md section 1" to "section 0").
    Planted: a consumer keeping a line the template dropped, pinned to v2;
    v3 changes only a comment (the pin moves, unasked); v3b changes a
    visible line (asked, and the question shows the line)."""
    import contextlib, hashlib, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-kept-comment-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    cases = []
    saved_source = pu.SOURCE
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        tmpl = src / 'templates' / 'TODO.md.template'

        def commit(text, msg):
            tmpl.write_text(text, encoding='utf-8')
            git(src, 'add', '-A')
            git(src, 'commit', '-qm', msg)
            return git(src, 'rev-parse', 'HEAD').stdout.strip()
        commit('<!-- see INSTALL.md section 1 -->\n# Open items\n\n'
               'Keep this list short and current.\n', 'v1')
        v2_text = ('<!-- see INSTALL.md section 1 -->\n# Open items\n\n'
                   'One file per item under todo/.\n')
        v2 = commit(v2_text, 'v2')
        v3 = commit(v2_text.replace('section 1', 'section 0'), 'v3')
        git(src, 'checkout', '-q', '-b', 'visible', v2)
        v3b = commit(v2_text.replace('One file per item', 'One file for each item'),
                     'v3b')
        pu.SOURCE = src

        def consumer(name):
            repo = tmp / name
            repo.mkdir()
            (repo / 'TODO.md').write_text('# Open items\n\nKeep this list short '
                                         'and current.\n', encoding='utf-8')
            (repo / 'precedent.json').write_text(json.dumps({
                pve.KEPT_DIVERGENCES_KEY: {'TODO.md': {
                    'reason': 'our list stays in one file',
                    'template_sha256': hashlib.sha256(v2_text.encode()).hexdigest()}}}),
                encoding='utf-8')
            return repo

        def run(repo, rev):
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.dropped_template_lines_step(repo, rep, rev)
            return rep

        repo = consumer('comment-only')
        rep = run(repo, v3)
        pin = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))[
            pve.KEPT_DIVERGENCES_KEY]['TODO.md']['template_sha256']
        want = hashlib.sha256(v2_text.replace('section 1', 'section 0')
                              .encode()).hexdigest()
        cases.append(('a comment-only change moves the pin, unasked',
                      not rep.left and pin == want
                      and any('changed only inside HTML comments' in str(s)
                              for s in rep.steps), f'{rep.left} {rep.steps}'))
        rep = run(repo, v3)
        cases.append(('...and the next update says it is kept, nothing more',
                      not rep.left and any('kept on purpose' in str(s)
                                           for s in rep.steps), str(rep.steps)))

        repo = consumer('visible')
        rep = run(repo, v3b)
        shown = '\n'.join(l for v in rep.details.values() for l in v)
        cases.append(('CONTROL: a change a reader sees is still asked, and the '
                      'question shows the changed line',
                      bool(rep.left) and 'what changed in templates/' in shown
                      and '+One file for each item under todo/.' in shown, shown))
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a kept pin moves across a comment-only template change '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_dropped_wording_reads_a_views_source():
    """Dropped template wording in a GENERATED MAP.md or GLOSSARY.md is
    reported in its source file, never in the view.

    Since 2026-10-03 those two views are rebuilt from MAP.source.md /
    GLOSSARY.source.md. The update still read the view, so a consumer was
    told to delete lines from MAP.md that the next sync wrote straight back,
    and the update never reached DONE (very deep check's install rehearsal,
    2026-10-05). Planted: an old template line in a generated MAP.md and in
    its MAP.source.md; the same in the directory form; a generated view with
    no source; and a hand-written MAP.md, which is still the repo's own and
    still read."""
    import contextlib, io, tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dropped-source-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    old = 'This map was written by the older template wording here.'
    own = 'Our own row about the planting calendar, written by this repo.\n'
    view = ('---\ngenerated_by: tools/build_views.py\n---\n# Map\n\n'
            + old + '\n')
    cases = []
    saved_source = pu.SOURCE
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        tmpl = src / 'templates' / 'MAP.md.template'
        tmpl.write_text('# Map\n\n' + old + '\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        tmpl.write_text('# Map\n\nThe current template says something else.\n',
                        encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v2')
        rev = git(src, 'rev-parse', 'HEAD').stdout.strip()
        pu.SOURCE = src

        def left_for(build):
            repo = tmp / f'consumer-{len(cases)}'
            repo.mkdir()
            build(repo)
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.dropped_template_lines_step(repo, rep, rev)
            return {k for k, _ in rep.left}

        def with_source(repo):
            (repo / 'MAP.md').write_text(view, encoding='utf-8')
            # A line of the repository's own: an untouched install copy
            # takes the current template whole instead (2026-10-17).
            (repo / 'MAP.source.md').write_text('# Map\n\n' + old + '\n'
                                                + own, encoding='utf-8')
        left = left_for(with_source)
        cases.append(('a generated view with a source file: the line is '
                      'reported in MAP.source.md, never in MAP.md',
                      any(k.startswith('MAP.source.md:') for k in left)
                      and not any(k.startswith('MAP.md:') for k in left),
                      str(left)))

        def with_folder(repo):
            (repo / 'MAP.md').write_text(view, encoding='utf-8')
            (repo / 'MAP.source').mkdir()
            (repo / 'MAP.source' / 'intro.md').write_text(old + '\n',
                                                         encoding='utf-8')
        left = left_for(with_folder)
        cases.append(('the directory form: reported in the entry file that '
                      'carries it', any(k.startswith('MAP.source/intro.md:')
                                        for k in left)
                      and not any(k.startswith('MAP.md:') for k in left),
                      str(left)))

        def no_source(repo):
            (repo / 'MAP.md').write_text(view, encoding='utf-8')
        left = left_for(no_source)
        cases.append(('a generated view with no source has nothing a person '
                      'can edit, so nothing is listed', not left, str(left)))

        def hand_written(repo):
            (repo / 'MAP.md').write_text('# Map\n\n' + old + '\n' + own,
                                         encoding='utf-8')
        left = left_for(hand_written)
        cases.append(('a hand-written MAP.md is the repo\'s own and still read',
                      any(k.startswith('MAP.md:') for k in left), str(left)))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors reports a generated view\'s dropped wording in its '
          f'source ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_fetches_brought_sets_before_the_views():
    """Update Vendors clones or pulls the sets the person's individual set
    brings before it syncs the views (2026-10-04: a consumer's first update
    after the ladder moved into a brought set ran in a session whose start
    predated the engine that clones it, and the sync listed the set's rules
    as lost). Function-level, with the fetch stood in: a fetched set is a
    step, one that could not be fetched is left for the person, none is
    silence, and in run order the step comes before the view sync."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    rep = pu.Report()
    pu.brought_sets_step(rep, fetch=lambda: [('fx-ladder', True, 'cloned')])
    cases.append(('a brought set fetched is reported as a step',
                  any(n == 'brought sets' and 'fx-ladder' in o for n, o in rep.steps)
                  and not rep.left))
    rep = pu.Report()
    pu.brought_sets_step(rep, fetch=lambda: [('fx-ladder', False, 'HTTP 404')])
    cases.append(('one that could not be fetched is left for the person, by name',
                  any('fx-ladder' in w and 'HTTP 404' in why for w, why in rep.left)))
    rep = pu.Report()
    pu.brought_sets_step(rep, fetch=lambda: [])
    cases.append(('a person who brings nothing hears nothing', not rep.steps
                  and not rep.left))
    src = (ROOT / 'tools' / 'precedent_update.py').read_text(encoding='utf-8')
    cases.append(('in run order, the step comes before the view sync',
                  0 < src.find('    brought_sets_step(rep, repo=repo)\n')
                  < src.find("    sync = repo / 'tools' / 'precedent_sync_views.py'")))
    bad = [n for n, ok in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_update_asks_headings_only_of_published_files():
    """Update Vendors' view migration asks for headline case only on a moved
    source file the headline-capitalization check itself would judge
    (title_case.is_outward). 2026-10-04, a consumer whose precedent.json
    declares `"output_paths": []` was asked to recase MAP.source.md and
    GLOSSARY.source.md, which nothing of its publishes. Driven with the
    migration and the heading tool stood in. CONTROL: a moved file the check
    does reach is still asked about."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import title_case as tc
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-migrate-headings-'))
    saved_run, saved_out = pu.run, tc.is_outward
    cases = []
    try:
        (tmp / 'tools').mkdir()
        for n in ('precedent_migrate_views.py', 'title_case.py'):
            (tmp / 'tools' / n).write_text('', encoding='utf-8')
        asked = []

        def fake_run(argv, cwd):
            if argv[1].endswith('precedent_migrate_views.py'):
                return 0, 'MAP.md -> MAP.source.md\nGLOSSARY.md -> GLOSSARY.source.md\n'
            asked.append(argv[2:])
            return 1, 'not headline case'
        pu.run = fake_run
        rep = pu.Report()
        pu.migrate_views_step(tmp, rep)
        cases.append(('moved source files nothing publishes are not asked about',
                      asked == [] and not rep.left
                      and any(n == 'headings kept' for n, _o in rep.steps),
                      (asked, rep.left, rep.steps)))
        tc.is_outward = lambda rel, root='.': rel == 'MAP.source.md'
        asked.clear()
        rep = pu.Report()
        pu.migrate_views_step(tmp, rep)
        cases.append(('CONTROL: one the check does reach is still asked about',
                      asked == [['MAP.source.md']] and rep.left, (asked, rep.left)))
    finally:
        pu.run, tc.is_outward = saved_run, saved_out
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_citations_skip_a_generated_block():
    """A citation inside a generated block of a hand-written file is not a
    line the repository can edit, so Update Vendors never lists it.

    THE INCIDENT (2026-10-08). precedent_update.py's "citations of a
    practice reworded or withdrawn -- read each" named lines inside
    AGENTS.md's loader block, which the next sync rewrites from the
    sources. precedent_practice_refs.scan_root counted a file as generated
    only when its first lines said so; a block inside a hand-written file
    (generated_blocks.py's two marker styles) stayed 'live'. Planted: one
    AGENTS.md citing a reworded slug by hand, inside the loader block, and
    inside a gen: block; only the hand-written line is listed."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import generated_blocks as gb
    import precedent_practice_refs as ppr
    import precedent_update as pu
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refs-gen-'))
    try:
        (tmp / 'AGENTS.md').write_text(
            '# Notes\n\n'
            'Hand-written: follow `upstream-fix` when fixing.\n\n'
            'More prose.\n\nAnd more, so the block opens past line 6.\n\n'
            f'{gb.LOADER_BEGIN}\n'
            'Resident: `upstream-fix` -- fix the cause where it lives.\n'
            f'{gb.LOADER_END}\n\n'
            '<!--gen:counts-->\n'
            'Also `upstream-fix`, in a doc_sync block.\n'
            '<!--/gen:counts-->\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], capture_output=True, check=True)
        rows = ppr.scan_root(tmp, {'upstream-fix'})
        kinds = {r[1]: r[4] for r in rows}
        cases.append(('the hand-written line is live', kinds.get(3) == 'live', kinds))
        cases.append(('the loader-block and gen-block lines are generated',
                      kinds.get(10) == 'generated' and kinds.get(14) == 'generated',
                      kinds))
        data = {'slugs': {'upstream-fix': 'Rule reworded'}, 'successors': {},
                'hits': [{'source': 'this repository', 'file': r[0], 'line': r[1],
                          'slug': r[2], 'form': r[3], 'kind': r[4],
                          'must_fix': ppr.must_fix(r)} for r in rows]}
        fix, read = pu.citation_findings(data)
        cases.append(('Update Vendors asks for a read of the hand-written line only',
                      fix == [] and read == ['AGENTS.md:3'], (fix, read)))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'citations inside a generated block are not listed for a read '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_installed_templates_follow_their_source():
    """A template a copied-in source ships for a consumer to install
    outside its copy -- a workflow its prompts' check runs in -- is
    refreshed by Update Vendors (Morgan, 2026-10-30, strength: decided).

    1. An installed workflow still holding the old template's text is
       rewritten with the new one, its approval pin moves with it, and what
       was installed is recorded; a second run changes nothing.
    2. CONTROL: a copy changed here is left alone and left for the person.
    3. ...or reported KEPT ON PURPOSE when precedent.json gives a reason.
    4. A template never installed here is named, never written in.
    5. An approval pinned to other text than the old template's is left
       for the approval check, though the unedited file is refreshed.
    6. declared_installs: the entry overrides the source on `to`, and a
       path that climbs out with `..` is dropped."""
    import hashlib, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-installs-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True)

    def sha(b):
        return hashlib.sha256(b).hexdigest()

    class Rep:
        def __init__(self):
            self.steps, self.left = [], []

        def step(self, label, what):
            self.steps.append(what)

        def leave(self, item, what):
            self.left.append((item, what))
    wf = '.github/workflows/prompt-check.yml'
    v1 = b'on: [pull_request]\njobs: {a: {runs-on: ubuntu-latest}}\n'
    v2 = v1 + b'# checks the prompts too\n'
    try:
        src = tmp / 'voice-x'
        (src / 'templates').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(src)], env=env, check=True)
        man = {'name': 'voice-x', 'level': 'shared',
               'installs': [{'from': 'templates/prompt-check.yml', 'to': wf},
                            {'from': 'templates/other.yml',
                             'to': '.github/workflows/other.yml'}]}
        (src / 'precedent-source.json').write_text(json.dumps(man))
        (src / 'templates' / 'prompt-check.yml').write_bytes(v1)
        (src / 'templates' / 'other.yml').write_bytes(b'x\n')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        c1 = git(src, 'rev-parse', 'HEAD').stdout.strip()
        (src / 'templates' / 'prompt-check.yml').write_bytes(v2)
        git(src, 'commit', '-qam', 'v2')
        entry = {'level': 'shared', 'name': 'voice-x', 'path': 'process/voice-x',
                 'vendored': True, 'exports_only': True}

        def consumer(installed_text, approval_sha=None, kept=None):
            r = tmp / 'r'
            shutil.rmtree(r, ignore_errors=True)
            (r / '.github' / 'workflows').mkdir(parents=True)
            (r / 'process').mkdir()
            if installed_text is not None:
                (r / wf).write_bytes(installed_text)
            cfg = {'sources': [entry]}
            if approval_sha:
                cfg['github_ci_approved'] = {wf: {
                    'sha256': approval_sha,
                    'approved_by': 'Morgan, 2026-10-01: "yes, install it"'}}
            if kept:
                cfg['kept_template_divergences'] = {wf: {'reason': kept}}
            (r / 'precedent.json').write_text(json.dumps(cfg))
            (r / 'process' / 'manifest_voice-x.json').write_text(
                json.dumps({'upstream': {'commit': c1}}))
            return r

        def run(r):
            rep = Rep()
            pu.refresh_installed_templates(r, rep, entry, src, src, man, c1)
            return rep

        r = consumer(v1, approval_sha=sha(v1))
        (r / 'process' / 'manifest_other.json').write_text(json.dumps({'entries': [
            {'practice': 'prompt-check', 'local_path': wf, 'status': 'synced',
             'local_sha256': sha(v1)},
            {'practice': 'edited-elsewhere', 'local_path': wf, 'status': 'synced',
             'local_sha256': sha(b'not the old text')}]}))
        rep = run(r)
        base = json.loads((r / 'process' / 'manifest_other.json').read_text())['entries']
        cases.append(('7. the drift baseline that recorded the old text moves to '
                      'the new (2026-11-01); one recording other text is left',
                      base[0]['local_sha256'] == sha(v2)
                      and base[1]['local_sha256'] == sha(b'not the old text')
                      and any('drift baseline' in s for s in rep.steps)))
        cfg = json.loads((r / 'precedent.json').read_text())
        appr = cfg['github_ci_approved'][wf]
        rec = json.loads((r / 'process' / 'manifest_voice-x.json').read_text())
        cases.append(('1. an unedited installed workflow takes the new template',
                      (r / wf).read_bytes() == v2 and not rep.left))
        cases.append(('1. ...its approval pin moves, the old words kept and the '
                      'reason added',
                      appr['sha256'] == sha(v2)
                      and appr['approved_by'].startswith('Morgan, 2026-10-01')
                      and 'Update Vendors' in appr['approved_by']))
        cases.append(('1. ...and what was installed is recorded',
                      rec.get('installed', {}).get(wf) == sha(v2)
                      and rec.get('upstream', {}).get('commit') == c1))
        before = (r / 'precedent.json').read_text()
        rep = run(r)
        cases.append(('1. ...a second run changes nothing',
                      (r / wf).read_bytes() == v2 and not rep.left
                      and (r / 'precedent.json').read_text() == before))
        cases.append(('4. a template never installed here is named, not written',
                      not (r / '.github' / 'workflows' / 'other.yml').exists()
                      and any('not installed here' in s for s in rep.steps)))

        edited = v1 + b'# ours\n'
        r = consumer(edited, approval_sha=sha(edited))
        rep = run(r)
        cases.append(('2. CONTROL: a copy changed here is left alone and left for you',
                      (r / wf).read_bytes() == edited
                      and [i for i, _w in rep.left] == [f'{wf} (from voice-x\'s '
                                                         f'templates/prompt-check.yml)']
                      and json.loads((r / 'precedent.json').read_text())
                      ['github_ci_approved'][wf]['sha256'] == sha(edited)))
        r = consumer(edited, kept='this repo runs one more step')
        rep = run(r)
        cases.append(('3. ...or KEPT ON PURPOSE with a recorded reason',
                      (r / wf).read_bytes() == edited and not rep.left
                      and any('KEPT ON PURPOSE' in s for s in rep.steps)))

        r = consumer(v1, approval_sha=sha(b'something else'))
        rep = run(r)
        cases.append(('5. an approval pinned to other text is left as it was',
                      (r / wf).read_bytes() == v2
                      and json.loads((r / 'precedent.json').read_text())
                      ['github_ci_approved'][wf]['sha256'] == sha(b'something else')))

        got = pu.declared_installs(
            {'installs': [{'from': 'templates/mine.yml', 'to': wf},
                          {'from': '../escape.yml', 'to': 'x.yml'}]}, man)
        cases.append(('6. the entry overrides the source on `to`; `..` is dropped',
                      dict((t, f) for f, t in got) == {
                          wf: 'templates/mine.yml',
                          '.github/workflows/other.yml': 'templates/other.yml'}))
    except (OSError, subprocess.CalledProcessError, TypeError, ValueError,
            KeyError, AttributeError) as ex:
        cases.append((f'fixture could not be built ({ex!r})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_adopts_an_earlier_runs_catalogue_mirror():
    """A re-run of Update Vendors stages the catalogue mirror an earlier run
    wrote, when the catalogue manifest names the pinned commit and every
    such file is upstream's at it (or gone where the mirror has none).
    2026-10-04, a consumer's fourth run: 80 process/upstream/ files of an
    earlier run's mirror were left unstaged beside a staged manifest naming
    the new commit. CONTROL: one edited file means nothing is taken."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-adopt-mirror-'))
    saved = pu.SOURCE
    cases = []
    try:
        pu.SOURCE = ROOT
        tree = tmp / 'process' / 'upstream'
        (tree / 'practices').mkdir(parents=True)
        upstream = subprocess.run(['git', '-C', str(ROOT), 'show', f'{head}:practices/park-it.md'],
                                  capture_output=True).stdout
        (tree / 'practices' / 'park-it.md').write_bytes(upstream)
        (tmp / 'process' / 'manifest.json').write_text(json.dumps({'upstream': {
            'vendored_at': 'process/upstream', 'commit': head}}), encoding='utf-8')
        before = {'process/upstream/practices/park-it.md',
                  'process/upstream/practices/zz-never-upstream.md',
                  'process/manifest.json', 'NOTES.md'}
        got = pu.adopt_catalogue_output(tmp, before, head)
        cases.append(('an earlier run\'s mirror, byte for byte upstream\'s, and a path '
                      'upstream has none of, are adopted with the manifest; the '
                      'person\'s own file is not',
                      set(got) == before - {'NOTES.md'}, got))
        (tree / 'practices' / 'park-it.md').write_bytes(upstream + b'mine\n')
        got = pu.adopt_catalogue_output(tmp, before, head)
        cases.append(('CONTROL: one edited file means nothing is taken', got == [], got))
        (tree / 'practices' / 'park-it.md').write_bytes(upstream)
        got = pu.adopt_catalogue_output(tmp, before, 'f' * 40)
        cases.append(('...nor when the manifest names another commit', got == [], got))
    finally:
        pu.SOURCE = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:300]}' for n, d in bad))


def check_refresh_refuses_an_untested_main():
    """precedent_vendor_engine.untested_tip_refusal: a bare refresh following
    main refuses a tip whose GitHub test is running or failed, naming
    Update Vendors and --take-anyway; it takes a passed one, and one GitHub
    cannot be asked about, with a notice. And precedent_update.kept_older_note
    says plainly when Update Vendors kept an older main. 2026-10-18: Update
    Vendors said a bare "already current", a session went around it with
    refresh, and refresh vendored a main whose test was still running."""
    import precedent_vendor_engine as pve
    import precedent_update as pu

    class FakeBranches:
        def __init__(self, state):
            self.state = state

        def github_tests(self, _clone, _sha):
            return [('.github/workflows/test.yml', True)]

        def passed_markers(self, _clone):
            return set()

        def github_test_state(self, _clone, _sha, _tests):
            return self.state
    tip = 'b8149f6' + '0' * 33
    got = {st: pve.untested_tip_refusal(ROOT, tip, pb=FakeBranches((st, 'why')))
           for st in ('running', 'failed', 'passed', 'unknown')}
    note = pu.kept_older_note('engine already current with main @ 1a426298cd85',
                              'main', tip, '1a426298cd85' + '0' * 28)
    check('a refresh refuses an untested main tip, and Update Vendors says '
          'when it kept an older one',
          all(got[st] and pve.TAKE_ANYWAY_FLAG in got[st] and 'precedent_update.py' in got[st]
              for st in ('running', 'failed'))
          and got['passed'] is None and got['unknown'] is None
          and 'b8149f60000' in note and 'no passing GitHub test yet' in note
          and pu.kept_older_note('x', 'main', tip, tip) == 'x',
          f'{got} / {note!r}')

    # 2026-10-20: a session-start refresh refused for every source because
    # main's newest commit had no finished test, leaving them all stale. It
    # now takes the newest main that passed, as Update Vendors does.
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-list', '--first-parent',
                           '--max-count=3', 'HEAD'], capture_output=True,
                          text=True).stdout.split()

    class PassesAt(FakeBranches):
        def __init__(self, passed):
            self.passed = passed

        def github_test_state(self, _clone, sha, _tests):
            return ('passed', '') if sha == self.passed else ('running', '')
    if len(head) == 3:
        took = pve.newest_passed_main(ROOT, head[0], pb=PassesAt(head[2]))
        none = pve.newest_passed_main(ROOT, head[0], pb=PassesAt('none'), window=3)
        check('a refresh takes the newest main that passed when the newest has '
              'not', took == (head[2], 2) and none == (None, 3),
              f'{took} / {none}')
    else:
        not_applicable('a refresh takes the newest main that passed',
                       'this clone has fewer than three first-parent commits')


def check_sync_keeps_the_map_and_links_after_a_removal():
    """A sync that removes practices keeps the repository around them whole
    (a consumer's report, 2026-10-02/03): it rewrote AGENTS.md, left eight
    dead links in a generated MAP.md with its own --check saying OK, and
    left two open items naming removed practices, which failed the next
    Promote.

    1. a link to a practice renamed upstream is repointed to its successor;
    2. a link to one withdrawn from universal is left, and reported with
       where the rule went;
    3. a generated MAP.md is rebuilt and no longer links the removed ones;
    4. CONTROL: a hand-made GLOSSARY.md (no generated_by header) is left
       byte for byte."""
    import tempfile, shutil
    import json as _json
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='sync-map-links-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-such-config.json'))
    for k in ('PRECEDENT_ASSUME_LADDER', 'PRECEDENT_NO_LADDERS'):
        env.pop(k, None)
    results = []
    try:
        uni = tmp / 'universal'
        (uni / 'practices').mkdir(parents=True)
        for slug in ('kept-rule', 'gone-rule', 'old-name'):
            (uni / 'practices' / f'{slug}.md').write_text(
                _move_fixture_practice(slug), encoding='utf-8')
        repo = tmp / 'consumer'
        (repo / 'todo').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env, check=True)
        (repo / 'AGENTS.md').write_text(
            f'# C\n\nSee [gone](practices/gone-rule.md).\n\n'
            f'{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main', 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(uni)}]}), encoding='utf-8')
        glossary = '# Our own glossary\n\nHand-written; see practices/gone-rule.md.\n'
        (repo / 'GLOSSARY.md').write_text(glossary, encoding='utf-8')
        item = ('# An open item\n\nSee [gone](../practices/gone-rule.md) and '
                '[old](../practices/old-name.md).\n')
        (repo / 'todo' / 'todo-x.md').write_text(item, encoding='utf-8')
        (repo / 'hooks').mkdir()
        hook = '#!/bin/sh\n# see practices/gone-rule.md\nexit 0\n'
        (repo / 'hooks' / 'h.sh').write_text(hook, encoding='utf-8')
        # A vendored engine file is BestPractice's, rewritten on every refresh:
        # never this repository's to fix, so never reported here.
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'eng.py').write_text('# reads practices/gone-rule.md\n',
                                               encoding='utf-8')
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer', 'files': ['eng.py']}), encoding='utf-8')
        sync = [sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                '--repo', str(repo)]
        r = subprocess.run(sync, env=env, capture_output=True, text=True)
        # A generated MAP.md, as a consumer that ran build_views has one.
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                        '--repo', str(repo)], env=env, capture_output=True, text=True)
        map_before = (repo / 'MAP.md').read_text(encoding='utf-8') \
            if (repo / 'MAP.md').is_file() else ''
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'first sync'],
                       env=env, check=True)
        results.append(('fixture: the first sync wrote the rules and a generated map',
                        r.returncode == 0 and 'practices/gone-rule.md' in map_before,
                        failure_detail(r.stdout + r.stderr, 300)))
        # Upstream: gone-rule withdrawn outright, old-name renamed new-name.
        (uni / 'practices' / 'gone-rule.md').unlink()
        (uni / 'record').mkdir()
        (uni / 'record' / 'WITHDRAWN_FROM_UNIVERSAL.md').write_text(
            '- 2026-10-02: `gone-rule` withdrawn from universal, deliberately; in '
            'force only from the shared set `fx-ladder`, for the people who '
            'bring or declare it.\n', encoding='utf-8')
        (uni / 'practices' / 'new-name.md').write_text(
            _move_fixture_practice('new-name'), encoding='utf-8')
        (uni / 'practices' / 'old-name.md').write_text(
            _move_fixture_practice('old-name').replace(
                'status:      active', 'status:      deduplicated')
            .replace('in_force_at: null', 'in_force_at: new-name'), encoding='utf-8')
        r = subprocess.run(sync, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        got = (repo / 'todo' / 'todo-x.md').read_text(encoding='utf-8')
        map_after = (repo / 'MAP.md').read_text(encoding='utf-8')
        results.append(('1: a link to a renamed rule is repointed to its successor',
                        '../practices/new-name.md' in got
                        and 'old-name.md' not in got, got + failure_detail(out, 300)))
        results.append(('2: a link to a withdrawn rule is left and reported with '
                        'where it went', '../practices/gone-rule.md' in got
                        and 'todo/todo-x.md:3: links `gone-rule`' in out
                        and 'fx-ladder' in out, failure_detail(out, 500)))
        results.append(('2b: ...and so is one in AGENTS.md\'s own text outside the '
                        'generated block, which the full check refuses just the same '
                        '(two consumers, 2026-10-03)',
                        'AGENTS.md:3: links `gone-rule`' in out
                        and not any(l.startswith('AGENTS.md:') and 'AGENTS.md:3:' not in l
                                    and 'gone-rule' in l for l in out.splitlines()),
                        failure_detail(out, 500)))
        results.append(('2c: ...and one in a tracked file that is not Markdown is '
                        'reported and left byte for byte (a consumer\'s hook, 2026-10-03)',
                        'hooks/h.sh:2: links `gone-rule`' in out
                        and (repo / 'hooks' / 'h.sh').read_text(encoding='utf-8') == hook,
                        failure_detail(out, 500)))
        results.append(('2d: ...but a vendored engine file is not, being upstream\'s',
                        'tools/eng.py' not in out, failure_detail(out, 500)))
        results.append(('3: the generated MAP.md is rebuilt without the removed rules',
                        r.returncode == 0 and 'practices/gone-rule.md' not in map_after
                        and 'practices/kept-rule.md' in map_after, failure_detail(out, 300)))
        results.append(('4: CONTROL: a hand-made GLOSSARY.md is left byte for byte',
                        (repo / 'GLOSSARY.md').read_text(encoding='utf-8') == glossary, ''))
        # 5. An EARLIER removal (a consumer rehearsal, 2026-10-04): the next
        # sync removes nothing, and a link to the rule the last one removed
        # is still reported -- the full check refuses it whichever update
        # took the rule out. A link to a rule still present is not.
        (repo / 'todo' / 'todo-y.md').write_text(
            '# Another\n\nSee [kept](../practices/kept-rule.md).\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'second sync'],
                       env=env, check=True)
        r = subprocess.run(sync, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        results.append(('5: a link to a rule an EARLIER update removed is still '
                        'reported when this sync removes nothing',
                        r.returncode == 0
                        and 'hooks/h.sh:2: links `gone-rule`, which is not in '
                            'practices/' in out
                        and 'todo/todo-x.md:3: links `gone-rule`' in out
                        and 'kept-rule' not in out, failure_detail(out, 500)))
        # 5b. ...and Update Vendors lists it for the person, as it lists this
        # sync's own: its parser read only "which this sync removed", so the
        # earlier removal was printed and never listed.
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import precedent_update as _pu
        finally:
            sys.path.pop(0)
        _rep = _pu.Report()
        _pu.removed_links_step(_rep, out)
        results.append(('5b: Update Vendors lists the earlier removal\'s links for the '
                        'person, saying an earlier update removed the rule',
                        any(w == 'hooks/h.sh:2' and 'an earlier update removed' in y
                            for w, y in _rep.left)
                        and any(w == 'todo/todo-x.md:3' for w, _y in _rep.left),
                        repr(_rep.left)[:400]))
    except (OSError, subprocess.CalledProcessError) as e:
        results.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [(n, d) for n, ok, d in results if not ok]
    check(f'a sync that removes practices repoints or reports every link to '
          f'them and keeps a generated map current ({len(results)} stated cases)',
          not failed, '; '.join(f'{n} -- {d}' for n, d in failed))


