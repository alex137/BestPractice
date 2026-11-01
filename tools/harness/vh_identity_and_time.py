# The harness tests for commit identity
#
# tools/harness/vh_identity_and_time.py -- part of the verification harness:
# commit identity, authorship and the clock.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_sync_says_which_copy_of_a_claimed_check_runs():
    """A check whose name a practice in force claims is claimed, whichever
    source supplies the file. Where the claiming source ships its own copy,
    that copy runs and the sync says so in one plain line -- never "no
    practice in force here claims these". Where it ships none, another
    source's copy is the one vendored.

    THE INCIDENT (2026-10-08). Every sync in a consumer warned that nothing
    claimed universal's tools/checks/check_commit_author.py and
    check_buenos_aires_dates.py, while planted-author-rule and planted-dates-rule
    were in force there from the person's individual set, which ships and
    claims its own copies.

    1. the claiming source's copy is the one vendored, and said to run;
    2. the other source's copy is not reported as claimed by nothing;
    3. claimed but shipped only by another source: that copy is vendored;
    4. CONTROL: a check nothing claims is still reported;
    5. CONTROL: two sources that both claim and ship one file still refuse."""
    import contextlib, io, tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    cases = []

    def ship(root, *stems):
        (root / 'tools' / 'checks' / 'tests').mkdir(parents=True, exist_ok=True)
        for stem in stems:
            (root / 'tools' / 'checks' / f'check_{stem}.py').write_text(
                f'# {root.name}\n', encoding='utf-8')
            (root / 'tools' / 'checks' / 'tests' / f'test_{stem}.sh').write_text(
                'true\n', encoding='utf-8')

    def practice(slug, stem, source):
        return {'fm': {'slug': slug,
                       'checked_by': f'tools/checks/check_{stem}.py'},
                'source': source}

    with _tf.TemporaryDirectory() as td:
        uni, ind = pathlib.Path(td) / 'precedent', pathlib.Path(td) / 'individual'
        ship(uni, 'commit_author', 'solo', 'lost')
        ship(ind, 'commit_author')
        sources = [{'name': 'precedent', 'path': str(uni), 'level': 'universal'},
                   {'name': 'precedent-individual', 'path': str(ind),
                    'level': 'individual'}]
        res = {'practices': {
            'planted-author-rule': practice('planted-author-rule', 'commit_author',
                                      'precedent-individual'),
            'solo': practice('solo', 'solo', 'precedent-individual')}}
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            plan = pm._plan_checks(sources, res)
        said = err.getvalue()
        orphan = next((l for l in said.splitlines() if 'no practice in force' in l), '')
        got = {(rel, name): src for rel, name, src, _d in plan}
        cases.append(('1: the claiming source\'s copy is vendored, and said to run',
                      got.get(('checks', 'check_commit_author.py')) == 'precedent-individual'
                      and got.get(('checks/tests', 'test_commit_author.sh')) == 'precedent-individual'
                      and 'check_commit_author.py runs from precedent-individual' in said,
                      said))
        cases.append(('2: the other copy is not called claimed by nothing',
                      'commit_author' not in orphan, orphan))
        cases.append(('3: claimed, shipped only by another source: that copy is vendored',
                      got.get(('checks', 'check_solo.py')) == 'precedent'
                      and 'solo' not in orphan, f'{got} {orphan}'))
        cases.append(('4: CONTROL: a check nothing claims is still reported',
                      'check_lost.py (precedent)' in orphan, orphan))
        res['practices']['commit-author-u'] = practice('planted-author-rule', 'commit_author',
                                                       'precedent')
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                pm._plan_checks(sources, res)
            refused = False
        except pm.MaterializeError:
            refused = True
        cases.append(('5: CONTROL: two claiming sources that both ship it still refuse',
                      refused, ''))
    failed = [(n, d) for n, ok, d in cases if not ok]
    check(f'a sync says which copy of a claimed check runs ({len(cases)} '
          f'stated cases)', not failed, '; '.join(f'{n}: {d[:200]}' for n, d in failed))


def check_very_deep_check_record_pass_needs_a_green_suite():
    """--record-pass refuses a pass, for a run from 2026-11-01 on, until a
    green whole-suite `verify_harness.py --all --record-times` run has
    finished since the run started -- and, for done or partial, since the
    pass recorded before it (step 7: the suite re-run after each pass). The
    green run stamps tools/harness_check_times.json's green_full_run, and a
    later write keeps the stamp.

    The 2026-10-30 run's step-2 suite failed a case; the case was fixed and
    the suite never re-run green, so question 27 had no fresh times, and no
    pass was followed by a re-run. Controls: a green run after the right
    moment records; a run dated before 2026-11-01 records as it always did;
    a repository with no harness of its own is not asked."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-green-suite-'))
    try:
        repo, ledger = _vdc_guard_repo(tmp / 'a', green=None)
        rc, err, run = _vdc_record(vdc, '2=done', ledger, repo)
        cases.append(('THE CASE: no green whole-suite run at all -- refused, '
                      'naming the command to re-run until green',
                      rc == 1 and not run['passes']
                      and 'no green whole-suite run since this run started' in err
                      and "re-run `python3 tools/verify_harness.py --all "
                          "--record-times --because 'very deep check, step 2'` "
                          "until it is green" in err, err))
        repo, ledger = _vdc_guard_repo(tmp / 'b', green='2026-11-01T08:00:00-03:00')
        rc, err, run = _vdc_record(vdc, '2=done', ledger, repo)
        cases.append(('THE CASE: the green run finished before this run '
                      'started -- refused',
                      rc == 1 and not run['passes']
                      and '2026-11-01T08:00:00-03:00' in err, err))
        repo, ledger = _vdc_guard_repo(tmp / 'c', green='2026-11-01T10:00:00-03:00')
        rc, err, run = _vdc_record(vdc, '2=done', ledger, repo)
        cases.append(('CONTROL: a green run after the run started records the '
                      'pass, and the entry names that green run',
                      rc == 0 and run['passes'][0].get('suite_green')
                      == '2026-11-01T10:00:00-03:00', err))
        prev = [{'pass': '1', 'status': 'done',
                 'recorded': '2026-11-01T11:00:00-03:00'}]
        repo, ledger = _vdc_guard_repo(tmp / 'd', green='2026-11-01T10:00:00-03:00',
                                       passes=prev,
                                       run_extra={'consumer': {'checked': 'x'}})
        rc, err, run = _vdc_record(vdc, '3=done', ledger, repo)
        cases.append(('THE CASE: pass 1 was recorded after the last green run '
                      '-- pass 3 is refused (the suite was not re-run)',
                      rc == 1 and len(run['passes']) == 1
                      and 'since pass 1 was recorded' in err, err))
        rc, err, run = _vdc_record(
            vdc, "3=not run,skipped=all of it,agreed='skip 3'", ledger, repo)
        cases.append(('CONTROL: `not run` needs the green run since the start '
                      'only, not since the pass before it',
                      rc == 0 and len(run['passes']) == 2, err))
        repo, ledger = _vdc_guard_repo(tmp / 'e', green='2026-11-01T12:00:00-03:00',
                                       passes=prev)
        rc, err, run = _vdc_record(vdc, '3=done', ledger, repo)
        cases.append(('CONTROL: a green re-run after pass 1 was recorded lets '
                      'pass 3 record', rc == 0 and len(run['passes']) == 2, err))
        repo, ledger = _vdc_guard_repo(tmp / 'f', green=None, date='2026-10-31')
        rc, err, run = _vdc_record(vdc, '2=whatever', ledger, repo)
        cases.append(('CONTROL: a run dated before 2026-11-01 records as before',
                      rc == 0 and run['passes'][0]['status'] == 'whatever', err))
        repo, ledger = _vdc_guard_repo(tmp / 'g', harness=False)
        rc, err, run = _vdc_record(vdc, '2=done', ledger, repo)
        cases.append(('CONTROL: a repository with no harness of its own is not '
                      'asked for a green run', rc == 0, err))
        # The stamp: written by a green --all run, kept by every other write.
        times = tmp / 'times.json'
        _write_check_times({'check_a': 1.0}, 'm', path=times,
                           green='2026-11-01T10:00:00-03:00')
        _write_check_times({'check_a': 2.0}, 'm2', path=times)
        kept = json.loads(times.read_text(encoding='utf-8'))
        cases.append(('a later write of the times file keeps green_full_run',
                      kept.get('green_full_run') == '2026-11-01T10:00:00-03:00'
                      and kept['seconds'] == {'check_a': 2.0}, repr(kept)))
        src = pathlib.Path(__file__).read_text(encoding='utf-8')
        cases.append(('only a green run of every case (--all) stamps it',
                      'if recorded:' in src and 'if every_case:' in src
                      and "green = precedent_time.stamp_iso(ROOT)" in src
                      and "only a green run records them" in src, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'--record-pass needs a green whole-suite run since the run started '
          f'and since the pass before it ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_bot_authored_commits_are_warned_where_no_person_is_declared():
    """The commit-author check's bot half judges a pull request's commits in
    CI, where nobody is declared (2026-10-06).

    Five commits authored `noreply@anthropic.com` at +0000 reached
    BestPractice's main on 2026-10-02 through a pull request merged on
    GitHub. The check that should have refused them reads only commits on no
    remote, and stands down where no identity is declared -- both true of
    every GitHub Actions runner -- so nothing ever judged them.

    The fixture is a runner's state: git's global identity is the bot, no
    PRECEDENT_COMMIT_*, no user config, and a pull-request branch already on
    the remote, carrying one bot commit. THE CONTROLS: the same branch with
    the bot commit re-authored passes the bot half and still SKIPS the whole
    check with the identity half's own wording, so the stand-down is real and
    the bot address is what fails; and the default scope over the pushed
    branch sees nothing, which is why CI passes a range
    (practice: control-asserts-which-failure)."""
    import tempfile, json as _json, shutil as _shutil
    name = ('Commit author: a bot-authored commit in a pull request\'s range '
            'is WARNED about, never refused, where no person is declared')
    script = ROOT / 'tools' / 'check_commit_author.py'
    need = [script, ROOT / 'tools' / 'precedent_session_check.py',
            ROOT / 'tools' / 'precedent_identity.py',
            ROOT / 'tools' / 'commit_checks_common.py']
    absent = [str(p.relative_to(ROOT)) for p in need if not p.exists()]
    if absent:
        not_applicable(name, f'not in this tree: {absent}')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        ambient, _person, person_git = _engine_commit_env(tmp)
        bot_git = dict(person_git, GIT_AUTHOR_NAME='Claude',
                       GIT_AUTHOR_EMAIL='noreply@anthropic.com')
        bare, work = tmp / 'origin.git', tmp / 'work'
        (work / 'tools' / 'checks').mkdir(parents=True)
        for p in need:
            dest = work / p.relative_to(ROOT)
            _shutil.copy2(p, dest)

        def git(*args, env=person_git, cwd=work):
            return subprocess.run(['git', '-C', str(cwd), *args],
                                  capture_output=True, text=True, env=env)

        def commit(msg, env=person_git):
            return git('commit', '-q', '--allow-empty', '-m',
                       f'{msg}\n\nSession: none available (fixture)', env=env)

        def run(*args, rng=None):
            env = dict(ambient)
            if rng:
                env['PRECEDENT_CHECK_RANGE'] = rng
            p = subprocess.run([sys.executable, str(work / 'tools'
                                                    / script.name), *args],
                               cwd=str(work), capture_output=True, text=True,
                               env=env)
            return p.returncode, p.stdout + p.stderr

        git('init', '-q', '--bare', str(bare), cwd=tmp)
        git('init', '-q', '-b', 'main')
        git('remote', 'add', 'origin', str(bare))
        git('add', '-A')
        commit('the base')
        git('push', '-q', 'origin', 'main')
        git('checkout', '-q', '-b', 'pr')
        commit('a person\'s change')
        commit('a change the harness authored', env=bot_git)
        bot_sha = git('rev-parse', 'HEAD').stdout.strip()
        commit('another person\'s change')
        # On the remote, as a pull request's branch is by the time CI runs.
        git('push', '-q', 'origin', 'pr')
        rng = 'origin/main..HEAD'

        rc, out = run('--bot-authors-only', '--range', rng)
        cases.append((f'--bot-authors-only over the pull request\'s range '
                      f'warns about the bot commit and does not refuse it -- '
                      f'an emergency fallback (Morgan, 2026-10-06) '
                      f'(rc={rc}, {out[:200]!r})',
                      rc == 0 and 'WARNING' in out and bot_sha[:12] in out
                      and 'noreply@anthropic.com' in out))
        rc, out = run(rng=rng)
        cases.append((f'the whole check, with nobody declared and '
                      f'PRECEDENT_CHECK_RANGE set, warns too rather than '
                      f'standing down silently (rc={rc}, {out[:200]!r})',
                      rc == 0 and 'WARNING' in out and bot_sha[:12] in out))
        rc, out = run('--bot-authors-only')
        cases.append((f'control: the default scope over the pushed branch '
                      f'reads nothing -- why CI passes the range (rc={rc})',
                      rc == 0))

        cfg = work / 'precedent.json'
        cfg.write_text(_json.dumps({'grandfathered_commit_shas': [
            {'sha': bot_sha, 'note': 'fixture: published before the check'}]}),
            encoding='utf-8')
        rc, out = run('--bot-authors-only', '--range', rng)
        cases.append((f'a grandfathered bot commit is exempt, without a '
                      f'warning (rc={rc}, {out[:200]!r})',
                      rc == 0 and 'WARNING' not in out))
        cfg.unlink()

        # THE CONTROL: the same branch, the bot commit re-authored.
        git('reset', '-q', '--hard', 'HEAD~2')
        commit('a change the harness authored, re-authored')
        commit('another person\'s change')
        rc, out = run('--bot-authors-only', '--range', rng)
        cases.append((f'control: re-authored, the bot half passes (rc={rc}, '
                      f'{out[:200]!r})', rc == 0))
        rc, out = run(rng=rng)
        cases.append((f'control: re-authored, the whole check still stands '
                      f'down in its own words (rc={rc}, {out[:200]!r})',
                      rc == 2 and 'no identity is declared' in out))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_install_report_lists_only_placeholders_an_adopter_fills():
    """The installer's "placeholders to adapt" list leaves out a generated
    block and a backslash-escaped `\\<date\\>`.

    Found 2026-10-31 by the very deep check's pass 1 install rehearsal: every
    fresh install listed `AGENTS.md:37: <their city>` -- a word inside a
    practice's Rule in the generated loader block, which the sync rewrites,
    so "adapting" it is a hand-edit the next sync undoes -- and TODO.md's
    `todo-\\<date\\>-\\<slug\\>`, a file-name pattern the template escapes on
    purpose.

    Negative control, measured 2026-10-31: on the code before the fix both
    of the first two cases fail (the report holds `<their city>` and
    `<date\\>`); the third, a real placeholder, is listed either way.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-placeholders-'))
    cases = []
    try:
        (tmp / 'AGENTS.md').write_text(
            '# Notes\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '"about 15 minutes, done around 15:35 <their city> time".\n'
            '<!-- END GENERATED -->\n\n'
            'Items are named *todo-\\<date\\>-\\<slug\\>*.\n'
            '| <key deliverable> | <path> |\n', encoding='utf-8')
        left = pi._placeholders_left(tmp, ['AGENTS.md'])
        cases.append(('a word inside a generated block is not a placeholder to adapt',
                      not any('their city' in x for x in left), str(left)))
        cases.append(('a backslash-escaped angle bracket is not a placeholder',
                      not any('date' in x or 'slug' in x for x in left), str(left)))
        cases.append(('a real placeholder outside both is still listed',
                      left == ['AGENTS.md:8: <key deliverable>', 'AGENTS.md:8: <path>'],
                      str(left)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the install report lists only placeholders an adopter fills '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_practice_links_travel_holds_a_set_to_its_copy_in():
    """A shared or individual set is copied in to process/<set>/, so a
    `../tools/X` link from one of its practices resolves inside that copy,
    which carries tools/checks/ and the files its practices name
    (checkin._files_rules_name) -- never the engine.

    Found 2026-10-29: precedent-shared-ladder had 18 links like
    `../tools/precedent_branch_name.py`, dead in every copy-in consumer,
    and practice-links-travel counted each one as a vendored engine file
    that travels. One fixture, three runs, each asserting printed text:
      1. a shared set's engine link IS reported, with an absolute URL;
      2. its link to a file a practice names in `checked_by` is not;
      3. the same tree declared universal does not report the engine link
         -- the engine is vendored into a consumer's own tools/ there --
         while it still reads the file (the runner link, which a
         universal source does not carry, is reported).
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='links-travel-copy-in-'))
    try:
        fx = tmp / 'precedent-shared-fixture'
        (fx / 'tools' / 'fixture_tool').mkdir(parents=True)
        (fx / 'practices').mkdir()
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        for name in ('precedent_check.py', 'checkin.py', 'precedent_time.py'):
            shutil.copy(ROOT / 'tools' / name, fx / 'tools' / name)
        (fx / 'tools' / 'fixture_tool' / 'run.py').write_text(
            'print(1)\n', encoding='utf-8')
        (fx / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'kind': 'source',
            'source_repo': 'https://github.com/example/upstream',
            'source_branch': 'main',
            'files': ['precedent_check.py'],
        }), encoding='utf-8')
        (fx / 'practices' / 'fixture-copy-in.md').write_text(
            '---\nslug:        fixture-copy-in\ntitle:       A set rule\n'
            'tier:        on-demand\nseverity:    default\n'
            'applies_to:  []\noccasion:    "the fixture runs"\n'
            'gates:       []\nindex_clause: "the fixture runs"\n'
            'checked_by:  "tools/fixture_tool/run.py"\ndefines:     []\n'
            'status:      active\nsupersedes:  []\noverrides:   null\n'
            'added:       2026-10-29\napproved_by: "fixture"\n---\n'
            '## Rule\nStamp it with [the clock](../tools/precedent_time.py); '
            '[the runner](../tools/fixture_tool/run.py) checks it.\n\n'
            '## Story\nWritten for this control; no incident is claimed.\n',
            encoding='utf-8')
        (fx / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main',
             'visibility': 'public',
             'sources': [{'level': 'universal', 'name': 'precedent',
                          'path': os.path.relpath(ROOT, fx)}]}),
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin',
                        'https://github.com/example/precedent-shared-fixture.git'],
                       cwd=fx, capture_output=True)

        def run(level):
            (fx / 'precedent-source.json').write_text(json.dumps(
                {'name': 'precedent-shared-fixture', 'level': level,
                 'visibility': 'public'}), encoding='utf-8')
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only',
                 'practice-links-travel'],
                cwd=fx, capture_output=True, text=True, env=env)

        shared = run('shared')
        cases.append(('a shared set\'s ../tools/ engine link is reported, '
                      'with an absolute URL as the repair',
                      shared.returncode != 0
                      and 'fixture-copy-in.md:' in shared.stdout
                      and '../tools/precedent_time.py` is an engine file'
                      in shared.stdout
                      and ('/tools/precedent_time.py' in shared.stdout),
                      f'rc={shared.returncode} ' + failure_detail(shared.stdout, 500)))
        cases.append(('its link to a file a practice names in checked_by '
                      'travels with the copy-in',
                      'fixture_tool/run.py' not in shared.stdout,
                      failure_detail(shared.stdout, 500)))
        universal = run('universal')
        cases.append(('the same engine link from a universal source travels',
                      'fixture-copy-in.md:' in universal.stdout
                      and 'precedent_time.py' not in universal.stdout,
                      f'rc={universal.returncode} ' + failure_detail(universal.stdout, 500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'practice-links-travel holds a shared or individual set to what '
          f'its copy-in carries ({len(cases)} stated cases, each asserting '
          f'the printed text)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_install_rehearsal_small_findings_2026_10_17():
    """The small findings of the 2026-10-17 install rehearsal, one stated
    case each: the installer leaves a template comment that NAMES a
    placeholder as written and does not list it as one to adapt; the
    README entry block goes under a title's description, not between the
    two; practice_audit's not-applicable line in a consumer does not call
    it the upstream repo; the access check does not count the vendored
    universal catalogue as another repository; the CI cadence row never
    says "every push runs CI"; and the freshness guard tells a repository
    with no origin to add one, not to fetch from it.

    Decisions chosen by the session under Morgan's delegation of 2026-10-17
    ("Fix the other issues you found including the checks that never run.
    Tell me what you decide. I will be offline so don't wait for me.
    Approved, act, and Booked.").

    Negative control, measured 2026-10-17: every case fails on the code
    before the fix.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
        import precedent_access_check as pac
        import precedent_session_check as psck
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rehearsal-small-'))
    genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    try:
        # 1. Placeholders named inside a comment.
        tpl = ('<!-- `<upstream-docs>` IS ONE OF THOSE PLACEHOLDERS.\n'
               '     Replace <angle-bracket> placeholders. -->\n'
               '[A](<upstream-docs>/x.md) and <their city>\n')
        try:
            out = pi._substitute(tpl, {'<upstream-docs>': 'https://u'}, outside_comments=True)
        except TypeError:                 # an installer with no such switch
            out = pi._substitute(tpl, {'<upstream-docs>': 'https://u'})
        cases.append(('a comment naming a placeholder keeps its words; the text outside is filled',
                      '`<upstream-docs>` IS ONE OF' in out and '[A](https://u/x.md)' in out,
                      out))
        d = tmp / 'ph'
        d.mkdir()
        (d / 'A.md').write_text(out, encoding='utf-8')
        left = pi._placeholders_left(d, ['A.md'])
        cases.append(('a placeholder named inside a comment is not listed as one to adapt',
                      left == ['A.md:3: <their city>'], str(left)))
        # 2. README block under the description.
        r = tmp / 'readme'
        r.mkdir()
        (r / 'README.md').write_text('# Bird Notes\n\nA newsletter about birds.\n',
                                     encoding='utf-8')
        pi._readme(r, 'Bird Notes', None)
        text = (r / 'README.md').read_text(encoding='utf-8')
        cases.append(('the README entry block goes under the description, not between it '
                      'and the title',
                      text.index('A newsletter about birds.') < text.index('bestpractice-agent-entry'),
                      text[:200]))
        # 3. practice_audit's not-applicable line in a consumer.
        pa = tmp / 'consumer' / 'tools'
        shutil.copytree(ROOT / 'tools', pa, ignore=shutil.ignore_patterns(
            '__pycache__', 'verify_harness.py', '*.json'))
        ra = subprocess.run([sys.executable, str(pa / 'practice_audit.py')], capture_output=True,
                            text=True, cwd=str(pa.parent), timeout=120)
        said = ra.stdout + ra.stderr
        cases.append(("practice_audit's not-applicable line does not call a consumer the "
                      'upstream repo', 'NOT APPLICABLE' in said
                      and 'upstream repo itself' not in said
                      and 'installed onto the loader' in said, failure_detail(said, 300)))
        # 4. The access check's targets.
        c = tmp / 'access'
        subprocess.run(['git', 'init', '-q', str(c)], capture_output=True)
        (c / 'precedent' / 'universal' / 'practices').mkdir(parents=True)
        shared = tmp / 'shared-set'
        (shared / 'practices').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(shared)], capture_output=True)
        (c / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'},
            {'level': 'shared', 'name': 'shared-set', 'path': '../shared-set'},
            {'level': 'repo-local', 'name': 'local', 'path': 'local'}]}), encoding='utf-8')
        _saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
        try:
            got = [label for label, _p in pac.targets(str(c))]
        finally:
            if _saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = _saved
        cases.append(('the vendored universal catalogue is this checkout, not one more repo '
                      'to answer for; a sibling set still is',
                      'this checkout' in got and "shared source 'shared-set'" in got
                      and not any(l.startswith('universal') for l in got), str(got)))
        # 5. The CI cadence row's words.
        q = tmp / 'cadence'
        subprocess.run(['git', 'init', '-q', str(q)], capture_output=True)
        (q / 'precedent.json').write_text(json.dumps({'base_branch': 'main'}), encoding='utf-8')
        saved_root, saved_cfg = psck.ROOT, os.environ.get('PRECEDENT_USER_CONFIG')
        try:
            psck.ROOT = q
            os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
            row = psck._ci_cadence_row()
        finally:
            psck.ROOT = saved_root
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
        cases.append(('the CI cadence row says what it decides ([skip ci]), never that every '
                      'push runs CI', 'every push runs CI' not in row[2]
                      and '[skip ci]' in row[2], str(row)))
        # 6. The freshness guard in a repository with no origin.
        g = tmp / 'no-origin'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(g)], capture_output=True)
        subprocess.run(['git', '-C', str(g), 'commit', '-q', '--allow-empty', '-m', 'i'],
                       capture_output=True, env=genv)
        sent = tmp / 'sentinels'
        sent.mkdir()
        rg = subprocess.run(['bash', str(ROOT / 'tools' / 'freshness-guard.sh'), 'pre-write', 'main'],
                            input=json.dumps({'session_id': 'no-origin-fixture',
                                              'tool_name': 'Write',
                                              'tool_input': {'command': ''}}),
                            env=dict(genv, TMPDIR=str(sent), CLAUDE_PROJECT_DIR=str(g)),
                            capture_output=True, text=True, cwd=str(g), timeout=120)
        cases.append(('the freshness guard tells a repository with no origin to add one, not '
                      'to fetch from it', 'no origin yet' in rg.stderr
                      and 'git remote add origin' in rg.stderr
                      and 'Run: git fetch origin' not in rg.stderr, failure_detail(rg.stderr, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_individual_skeleton_ci_comment_is_true():
    """The individual-set skeleton keeps "github_ci_workflows": "disabled",
    and its comment says what is true: that an absent key means enabled
    (ci_preference's default since 2026-09-25), which workflows the key
    governs, and why the skeleton ships disabled -- naming no template that
    no longer exists.

    Found 2026-10-17 by the very deep check: the comment said an absent
    key means disabled and named two templates retired 2026-09-21. Decision
    chosen by the session under Morgan's delegation of 2026-10-17 ("Fix the
    other issues you found including the checks that never run. Tell me what
    you decide. I will be offline so don't wait for me. Approved, act, and
    Booked."): keep "disabled", the cautious start, and make the comment
    true.

    Negative control, measured 2026-10-17: the comment before the fix fails
    the absent-means and named-template cases.
    """
    import re as _re
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_identity as pid
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    tpl = ROOT / 'templates' / 'practice-set-individual' / 'identity.json.template'
    doc = json.loads(tpl.read_text(encoding='utf-8'))
    comment = ' '.join(doc.get('_github_ci_workflows_comment') or [])
    named = set(_re.findall(r'[\w.-]+\.yml(?:\.template)?', comment))
    shipped = {pathlib.Path(rel).name for _t, rel in pve.CI_WORKFLOW_TEMPLATES['consumer']}
    shipped |= {t for t, _rel in pve.CI_WORKFLOW_TEMPLATES['consumer']}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ind = pathlib.Path(td)
        (ind / 'identity.json').write_text(json.dumps({'email': 'a@example.com'}),
                                           encoding='utf-8')
        absent_enabled = pid.ci_preference(ind)['enabled']
    cases = [
        ('the skeleton still ships "disabled"', doc.get('github_ci_workflows') == 'disabled',
         repr(doc.get('github_ci_workflows'))),
        ('the comment says absent means enabled, as ci_preference does',
         absent_enabled and 'ABSENT MEANS ENABLED' in comment, comment[:300]),
        ('it says why the skeleton ships disabled', 'ON PURPOSE' in comment, comment[:300]),
        ('every workflow it names is one the engine ships',
         bool(named) and named <= shipped, f'{sorted(named)} vs {sorted(shipped)}'),
    ]
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_installer_base_branch_asks_origin_before_the_current_branch():
    """With origin/HEAD unset -- which is how `git remote add origin` and a
    push leave it -- the installer asks origin for its default branch, then
    looks for origin's main, before taking the branch checked out; and it
    never says "(no origin)" about a repository that has one.

    Found 2026-10-17 by the very deep check's install rehearsal: a project
    given its origin that way, installed from a feature branch, recorded the
    feature branch as its base branch. Decision chosen by the session under
    Morgan's delegation of 2026-10-17 ("Fix the other issues you found
    including the checks that never run. Tell me what you decide. I will be
    offline so don't wait for me. Approved, act, and Booked.").

    Negative control, measured 2026-10-17: on the code before the fix the
    first three cases answer the feature branch, "(no origin)".
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-base-branch-'))
    genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], capture_output=True,
                              text=True, env=genv)

    def project(name, origin_head='main'):
        bare = tmp / f'{name}.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', origin_head, str(bare)],
                       capture_output=True)
        d = tmp / name
        subprocess.run(['git', 'init', '-q', '-b', origin_head, str(d)], capture_output=True)
        git(d, 'commit', '-q', '--allow-empty', '-m', 'init')
        git(d, 'remote', 'add', 'origin', str(bare))
        git(d, 'push', '-q', 'origin', origin_head)
        git(d, 'switch', '-q', '-c', 'feature/install-precedent')
        return d, bare

    try:
        d, _ = project('plain')
        unset = git(d, 'symbolic-ref', '-q', 'refs/remotes/origin/HEAD').returncode != 0
        got = pi._base_branch(d, None)
        cases.append(('origin/HEAD unset after remote add + push: origin is asked, and '
                      'its default is the base branch, not the feature branch',
                      unset and got[0] == 'main' and 'no origin' not in got[1], str(got)))
        d, _ = project('trunk', origin_head='trunk')
        got = pi._base_branch(d, None)
        cases.append(("origin's own default answers, whatever it is called",
                      got[0] == 'trunk', str(got)))
        d, _ = project('offline')
        git(d, 'fetch', '-q', 'origin')
        git(d, 'remote', 'set-url', 'origin', str(tmp / 'gone.git'))
        got = pi._base_branch(d, None)
        cases.append(("origin unreachable: origin's main, already fetched, answers",
                      got[0] == 'main' and 'no origin' not in got[1], str(got)))
        d = tmp / 'no-origin'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(d)], capture_output=True)
        git(d, 'commit', '-q', '--allow-empty', '-m', 'init')
        git(d, 'switch', '-q', '-c', 'feature')
        got = pi._base_branch(d, None)
        cases.append(('CONTROL: no origin at all: the branch checked out, said as such',
                      got == ('feature', 'inferred from the branch checked out now (no origin)'),
                      str(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_update_repoints_engine_paths_that_moved():
    """Update Vendors rewrites live mentions of an engine path that moved
    (ENGINE_PATH_MOVES) in the consumer's own text, and leaves history as
    written.

    THE INCIDENT (2026-10-10, a consumer's Update Vendors): the commit
    checks moved from tools/checks/ to tools/, the first run listed nothing,
    and the second failed its push check on four live mentions of the old
    paths -- a _comment in precedent.json and three open todo items. The
    DISCRIMINATING CASE is those two kinds of file."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    old, new = 'tools/checks/check_commit_author.py', 'tools/check_commit_author.py'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        env = _fixture_git_env()
        subprocess.run(['git', 'init', '-q', str(repo)], env=env, capture_output=True)
        (repo / 'tools').mkdir()
        (repo / new).write_text('# engine\n', encoding='utf-8')
        (repo / 'todo').mkdir()
        files = {
            'precedent.json': '{"_comment": "author check: %s"}\n' % old,
            'todo/todo-2026-10-01-open.md': ('---\nstatus: open\n---\n'
                                             f'Run `{old}` on the range.\n'),
            'todo/todo-2026-10-01-closed.md': ('---\nstatus: done\n---\n'
                                               f'Ran `{old}`.\n'),
            # 2026-10-14, a consumer's Update Vendors: a closed item's
            # relative link to the old path failed the link check.
            'todo/todo-2026-10-02-closed-link.md': (
                '---\nstatus: done\n---\n'
                f'Flagged by [check_commit_author.py](../{old}#top).\n'),
            'todo/todo-2026-10-02-open-link.md': (
                '---\nstatus: open\n---\n'
                f'See [the check](../{old}).\n'),
            'NOTES.md': (f'The check was renamed from {old}.\n\n'
                         f'Both: {old} became {new}.\n\n'
                         f'## Story\n\nIt lived at {old}.\n'),
        }
        for rel, body in files.items():
            (repo / rel).write_text(body, encoding='utf-8')
        subprocess.run(['git', '-C', td, 'add', '-A'], env=env, capture_output=True)
        subprocess.run(['git', '-C', td, 'commit', '-qm', 'x'], env=env, capture_output=True)
        done = dict(pu.repoint_renamed_engine_paths(repo))
        read = lambda rel: (repo / rel).read_text(encoding='utf-8')
        cases.append(('THE DISCRIMINATING CASE: precedent.json and an open todo '
                      'item name the new path',
                      new in read('precedent.json') and old not in read('precedent.json')
                      and new in read('todo/todo-2026-10-01-open.md')
                      and old not in read('todo/todo-2026-10-01-open.md'), done))
        cases.append(('a closed todo item is history, left as written',
                      old in read('todo/todo-2026-10-01-closed.md'), ''))
        cases.append(('a closed item\'s relative link has its target repointed, '
                      'its link text and anchor kept',
                      read('todo/todo-2026-10-02-closed-link.md').endswith(
                          f'[check_commit_author.py](../{new}#top).\n'),
                      read('todo/todo-2026-10-02-closed-link.md')))
        cases.append(('an open item\'s ../ relative link is repointed too',
                      f'(../{new})' in read('todo/todo-2026-10-02-open-link.md'),
                      read('todo/todo-2026-10-02-open-link.md')))
        cases.append(('a sentence saying it was renamed, a line already naming the '
                      'new path, and a Story section are left as written',
                      read('NOTES.md') == files['NOTES.md'], read('NOTES.md')))
        cases.append(('it reports what it changed, file by file',
                      set(done) == {'precedent.json', 'todo/todo-2026-10-01-open.md',
                                    'todo/todo-2026-10-02-closed-link.md',
                                    'todo/todo-2026-10-02-open-link.md'},
                      done))
        cases.append(('a second run changes nothing',
                      pu.repoint_renamed_engine_paths(repo) == [], ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors repoints engine paths that moved ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_saved_individual_copy_loads_for_its_owner_only():
    """Part 4 of the copied-in shared sets plan (Morgan, 2026-10-19,
    strength: assented). In a private repository the sync writes a person's
    individual set into practices/ as a saved copy, and records whose it is
    in MANIFEST.json. It loads for that person alone:

    1. The record: the individual source's entry carries its owner's
       github, name, email and zone; no other entry does.
    2. The tracked AGENTS.md block carries none of the set, and says so;
       practices/ still holds it.
    3. Set missing, this session is the owner's: the session file loads the
       saved copy and tells the first reply, show, gate and paths serve it,
       and engine commits are authored as the owner, in the owner's zone.
    4. NEGATIVE CONTROL -- set missing, someone else's session: none of it.
       Before this change the saved copy was served to anyone.
    5. Owner unknown (GitHub knows nobody, nothing declared): none of it,
       and the session file says why.
    6. A copy with no owner record (synced before this): none of it."""
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='saved-individual-copy-'))
    cases = []
    tools = ROOT / 'tools'

    def practice(path, slug, rule, tier='on-demand', applies_to='["**"]',
                 gates='[]'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\n'
            f'severity: default\napplies_to: {applies_to}\noccasion: "testing"\n'
            f'gates: {gates}\nindex_clause: "a fixture"\nchecked_by: null\n'
            f'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
            f'added: null\napproved_by: "harness"\n---\n\n## Rule\n{rule}\n\n'
            f'## Detail\n\n## Why\n\n## Story\n\n## Install\n', encoding='utf-8')

    try:
        ind = tmp / 'people' / 'zz-owner-set'
        practice(ind / 'practices' / 'zz-personal.md', 'zz-personal',
                 'The owner\'s own resident Rule.', tier='resident')
        practice(ind / 'practices' / 'zz-routed.md', 'zz-routed',
                 'The owner\'s routed Rule.', applies_to='["fixture/*.md"]',
                 gates='["reply"]')
        (ind / 'identity.json').write_text(json.dumps(
            {'name': 'Owner O', 'email': 'o@example.com', 'github': 'owner-o',
             'timezone': 'Asia/Tokyo'}), encoding='utf-8')
        uni = tmp / 'uni'
        practice(uni / 'practices' / 'zz-universal.md', 'zz-universal',
                 'The universal Rule.', tier='resident')
        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(uni)}]}), encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            '# Fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-owner-set',
                                                   'path': str(ind)}}))
        none_cfg = str(tmp / 'no-config.json')
        base = {k: v for k, v in os.environ.items()
                if k not in ('PRECEDENT_GITHUB_USER', 'PRECEDENT_COMMIT_EMAIL',
                             'PRECEDENT_COMMIT_NAME', 'PRECEDENT_COMMIT_TZ', 'TZ')}

        def run(tool, *args, user_config=none_cfg, who=None):
            env = {**base, 'PRECEDENT_USER_CONFIG': user_config}
            if who:
                env['PRECEDENT_GITHUB_USER'] = who
            r = subprocess.run([sys.executable, str(tools / tool), *args],
                               cwd=str(repo), env=env, capture_output=True,
                               text=True)
            return r.returncode, r.stdout + r.stderr

        rc, out = run('precedent_sync_views.py', '--repo', str(repo),
                      '--user-config', str(ucfg), user_config=str(ucfg))
        man = json.loads((repo / 'MANIFEST.json').read_text())
        owners = {s['level']: s.get('owner') for s in man['sources']}
        cases.append(('the saved copy records its owner, and only it does',
                      rc == 0 and owners.get('individual') == {
                          'github': 'owner-o', 'name': 'Owner O',
                          'email': 'o@example.com', 'timezone': 'Asia/Tokyo'}
                      and owners.get('universal') is None,
                      f'{owners} {failure_detail(out, 600)}'))
        agents = (repo / 'AGENTS.md').read_text()
        cases.append(('the tracked block carries none of the set; practices/ '
                      'keeps it', 'zz-personal' not in agents
                      and 'INDIVIDUAL source' not in agents
                      and 'zz-universal' in agents
                      and (repo / 'practices' / 'zz-personal.md').is_file(),
                      failure_detail(agents, 800)))

        def session(who):
            rc, out = run('precedent_session_practices.py', '--repo', str(repo),
                          who=who)
            f = repo / '.precedent' / 'SESSION_PRACTICES.md'
            return out + (f.read_text() if f.is_file() else '')

        def served(who):
            got = {}
            got['session'] = 'own resident Rule' in session(who)
            got['show'] = 'own resident Rule' in run(
                'precedent_show.py', 'zz-personal', '--repo', str(repo), who=who)[1]
            got['gate'] = 'zz-routed' in run(
                'precedent_gate.py', 'reply', '--repo', str(repo), who=who)[1]
            got['paths'] = 'zz-routed' in run(
                'precedent_paths.py', 'fixture/a.md', '--repo', str(repo),
                who=who)[1]
            return got

        mine = served('owner-o')
        out = session('owner-o')
        cases.append(('set missing, the owner\'s session: the saved copy is '
                      'served everywhere, and the first reply is told',
                      all(mine.values()) and 'saved copy, last changed' in out,
                      f'{mine} {failure_detail(out, 500)}'))
        rc, env_out = run('precedent_identity.py', '--commit-env', str(repo),
                          who='owner-o')
        cases.append(('...and engine commits are the owner\'s, in their zone',
                      'GIT_AUTHOR_EMAIL=o@example.com' in env_out
                      and 'TZ=Asia/Tokyo' in env_out, env_out))
        rc, ident = run('precedent_audience.py', '--saved-owner-identity',
                        '--repo', str(repo), who='owner-o')
        cases.append(('...and the commit hook is handed name, email and zone',
                      ident.splitlines()[:3] == ['Owner O', 'o@example.com',
                                                 'Asia/Tokyo'], ident))

        theirs = served('someone-else')
        rc, ident = run('precedent_audience.py', '--saved-owner-identity',
                        '--repo', str(repo), who='someone-else')
        rc, env_out = run('precedent_identity.py', '--commit-env', str(repo),
                          who='someone-else')
        cases.append(('NEGATIVE CONTROL: someone else\'s session is served '
                      'none of it, and is never authored as the owner',
                      not any(theirs.values()) and not ident.strip()
                      and 'o@example.com' not in env_out,
                      f'{theirs} {ident} {env_out}'))

        nobody = served(None)
        out = session(None)
        cases.append(('owner unknown: none of it, and the session file says why',
                      not any(nobody.values()) and 'was not loaded' in out,
                      f'{nobody} {failure_detail(out, 400)}'))

        for src in man['sources']:
            src.pop('owner', None)
        (repo / 'MANIFEST.json').write_text(json.dumps(man))
        legacy = served('owner-o')
        cases.append(('a copy with no owner record loads for nobody',
                      not any(legacy.values()), repr(legacy)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the saved copy of an individual set loads for its owner only '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:500]}" for n, d in bad))


def check_commit_identity_derives_declared_timezone():
    """The declared timezone reaches the SESSION, not just the refusal message.

    The pre-commit backstop refuses a commit whose offset contradicts a
    declared timezone, and tells the person to rerun under `TZ=...`. Correct,
    and on its own it is a chore with no end: a hook cannot export TZ into the
    shells a session runs later, so the remedy gets retyped on every commit
    forever. 2026-09-07 the person running such a session said so plainly --
    "I'd rather a permanent fix than my having to do that manually."

    So the hook derives `env.TZ` into .claude/settings.local.json, which the
    harness reads for the whole of the NEXT session. Four properties have to
    hold together, and the fixture must be hermetic to test any of them: an
    early version of this test set no PRECEDENT_USER_CONFIG, so the case for
    "no declared zone" resolved the real user config, found a real declared
    zone, and reported a failure against completely correct behaviour.
      1. a DECLARED zone is written; a GUESSED one never is (writing a guess
         would enforce something nobody said).
      2. identity.json stays the source of truth -- a stale TZ already in the
         file is re-derived, not respected (registry-source-of-truth).
      3. nothing else in the file is disturbed, and an unparseable one is left
         entirely alone rather than overwritten.
      4. the file is per-machine, so the hook warns when it is not gitignored.
    """
    import tempfile, json as _json
    hook = ROOT / 'tools' / 'commit-identity.sh'
    if not hook.exists():
        not_applicable('commit-identity derives the declared timezone into '
                       'the session',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    env = dict(os.environ)
    # Hermetic: without this the hook resolves the REAL user config and the
    # "no zone declared" case silently becomes a "zone declared" case.
    env['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
    env.pop('PRECEDENT_COMMIT_TZ', None)
    # And HOME, or the hook writes the REAL ~/.gitconfig and the REAL global
    # hooks directory. It gained that behaviour on 2026-09-07 and this
    # fixture -- which declares Europe/Berlin -- promptly set this machine's
    # global identity to a test value and installed a Berlin-offset backstop,
    # which then refused the very commit landing the fix. A test that mutates
    # the environment it runs in is not a test.
    _home = tempfile.mkdtemp(prefix='ci-home-')
    env['HOME'] = _home
    # And the system clock, for the same reason and one step worse: this
    # fixture declares Europe/Berlin, and the hook now REPOINTS the machine's
    # zone file at a declared zone. Without this the harness would put the
    # container on Berlin time and every later commit in the session would be
    # refused by the backstop for an offset the harness itself caused.
    env['PRECEDENT_LOCALTIME'] = os.path.join(_home, 'localtime')

    def _repo(base, zone, settings=None, gitignore=None):
        base.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(base), 'init', '-q'],
                       capture_output=True)
        if zone:
            (base / 'identity.json').write_text(_json.dumps(
                {'name': 'T', 'email': 't@example.com', 'timezone': zone}),
                encoding='utf-8')
        if settings is not None:
            (base / '.claude').mkdir(exist_ok=True)
            (base / '.claude' / 'settings.local.json').write_text(
                settings, encoding='utf-8')
        if gitignore is not None:
            (base / '.gitignore').write_text(gitignore, encoding='utf-8')
        e = dict(env, CLAUDE_PROJECT_DIR=str(base))
        r = subprocess.run(['bash', str(hook)], capture_output=True,
                           text=True, env=e, timeout=120)
        return base / '.claude' / 'settings.local.json', r

    def _tz(f):
        try:
            return _json.loads(f.read_text(encoding='utf-8'))['env']['TZ']
        except Exception:
            return None

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        f, r = _repo(tmp / 'declared', 'America/Argentina/Buenos_Aires')
        cases.append(('a declared zone lands in settings.local.json',
                      _tz(f) == 'America/Argentina/Buenos_Aires'))
        cases.append(('and the hook still exits 0', r.returncode == 0))
        before = f.read_bytes()
        e = dict(env, CLAUDE_PROJECT_DIR=str(tmp / 'declared'))
        r2 = subprocess.run(['bash', str(hook)], capture_output=True,
                            text=True, env=e, timeout=120)
        cases.append(('a second run rewrites nothing', f.read_bytes() == before))
        cases.append(('and says nothing about it',
                      'settings.local.json' not in r2.stderr))

        # A person whose zone could not be resolved gets the DECLARED
        # FALLBACK written, not nothing. This assertion is the reverse of
        # what it was before 2026-09-09 (practice: timestamps-carry-offset):
        # writing nothing left the container on UTC, so every unidentified
        # person's commits and generated dates came out +0000 and could not
        # be ordered against anyone else's. The fallback is applied for that
        # reason and still never ENFORCED -- case 3 below holds that line.
        #
        # The expected value is DERIVED, never typed here. Typed, it is a
        # fourth copy of a constant that already lives in four places, and on
        # 2026-09-10 -- when the engine fallback moved off one person's zone
        # onto a generic one -- these two assertions were the only thing that
        # failed, because they were the copies nobody knew to change.
        f, r3 = _repo(tmp / 'guessed', None)
        cases.append((f'an unresolved zone still writes the declared fallback '
                      f'({_declared_fallback_tz()})',
                      _tz(f) == _declared_fallback_tz()))
        cases.append(('and says out loud that it is a fallback, not this '
                      "person's own zone",
                      'DECLARED FALLBACK' in r3.stderr))

        f, _ = _repo(tmp / 'existing', 'Europe/Berlin',
                     settings='{"env":{"OTHER":"keep"},'
                              '"permissions":{"allow":["Bash(ls)"]}}')
        try:
            d = _json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            d = {}
        cases.append(('an existing file keeps its other keys',
                      d.get('env', {}).get('TZ') == 'Europe/Berlin'
                      and d.get('env', {}).get('OTHER') == 'keep'
                      and d.get('permissions', {}).get('allow') == ['Bash(ls)']))

        f, _ = _repo(tmp / 'stale', 'Europe/Berlin',
                     settings='{"env":{"TZ":"UTC"}}')
        cases.append(('a stale TZ is re-derived, not respected',
                      _tz(f) == 'Europe/Berlin'))

        f, _ = _repo(tmp / 'broken', 'Europe/Berlin', settings='not json at all')
        cases.append(('an unparseable settings file is left untouched',
                      f.read_text(encoding='utf-8') == 'not json at all'))

        _, r = _repo(tmp / 'ignored', 'Europe/Berlin',
                     gitignore='.claude/settings.local.json\n')
        cases.append(('no gitignore warning when the file IS ignored',
                      'NOT gitignored' not in r.stderr))
        _, r = _repo(tmp / 'notignored', 'Europe/Berlin')
        cases.append(('the gitignore warning fires when it is not',
                      'NOT gitignored' in r.stderr))

    failed = [n for n, ok in cases if not ok]
    check(f'commit-identity derives the declared timezone into the session '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_commit_identity_leaves_a_laptops_global_config_alone():
    """On a local session (Claude Code on a person's own machine), the
    commit-identity hook sets the identity for this checkout only and leaves
    the global git identity, the global core.hooksPath and the system clock
    alone, saying so; in a cloud container it writes all three as before.

    Found 2026-10-17 by the very deep check's install rehearsal: the first
    session on a local machine rewrote the developer's global identity and
    set a global core.hooksPath, which silences every other repository's
    .git/hooks, and no document said so. Decision chosen by the session
    under Morgan's delegation of 2026-10-17 ("Fix the other issues you found
    including the checks that never run. Tell me what you decide. I will be
    offline so don't wait for me. Approved, act, and Booked."): repo-local
    config only on a local session, cloud unchanged.

    Hermetic: a scratch HOME and global config, a scratch clock file
    (PRECEDENT_LOCALTIME), TZ pinned -- the machine's own clock and config
    are never touched. Negative control, measured 2026-10-17: on the code
    before the fix the local run wrote the global identity, core.hooksPath
    and the clock file.
    """
    import tempfile
    hook = ROOT / 'tools' / 'commit-identity.sh'
    zone = 'Asia/Tokyo'
    if not pathlib.Path('/usr/share/zoneinfo', zone).exists():
        return True, f'not applicable: no zoneinfo for {zone}', ''
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def run(name, **extra):
            repo = tmp / name / 'repo'
            home = tmp / name / 'home'
            home.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
            gcfg = home / '.gitconfig'
            gcfg.write_text('', encoding='utf-8')
            e = {k: v for k, v in os.environ.items()
                 if k not in ('CLAUDE_CODE_REMOTE', 'PRECEDENT_LOCAL_SESSION',
                              'PRECEDENT_COMMIT_NAME', 'PRECEDENT_COMMIT_EMAIL',
                              'PRECEDENT_COMMIT_TZ')}
            e.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(gcfg), TZ='UTC',
                     CLAUDE_PROJECT_DIR=str(repo),
                     PRECEDENT_LOCALTIME=str(tmp / name / 'localtime'),
                     PRECEDENT_GLOBAL_HOOKS=str(home / 'git-hooks'),
                     PRECEDENT_USER_CONFIG=str(home / 'no-config.json'),
                     PRECEDENT_COMMIT_NAME='Dana Dev',
                     PRECEDENT_COMMIT_EMAIL='dana@example.com',
                     PRECEDENT_COMMIT_TZ=zone, **extra)
            r = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                               timeout=120, env=e)

            def gget(key, where):
                return subprocess.run(['git', 'config', '--file', str(where), '--get', key],
                                      capture_output=True, text=True).stdout.strip()
            return {'local_email': gget('user.email', repo / '.git' / 'config'),
                    'global_email': gget('user.email', gcfg),
                    'hooks_path': gget('core.hooksPath', gcfg),
                    'clock': os.path.lexists(tmp / name / 'localtime'),
                    'err': r.stderr}

        lap = run('laptop')
        cases.append(('a local session sets the identity for this checkout',
                      lap['local_email'] == 'dana@example.com', str(lap)[:400]))
        cases.append(('...and leaves the global identity, core.hooksPath and the clock alone',
                      not lap['global_email'] and not lap['hooks_path'] and not lap['clock'],
                      str(lap)[:600]))
        cases.append(('...and says what it left alone',
                      'local session -- the identity is set for this checkout only' in lap['err']
                      and 'global git identity' in lap['err']
                      and 'core.hooksPath' in lap['err'], failure_detail(lap['err'], 600)))
        cloud = run('cloud', CLAUDE_CODE_REMOTE='true')
        cases.append(('CONTROL: a cloud container still writes the global identity, '
                      'core.hooksPath and the clock',
                      cloud['global_email'] == 'dana@example.com' and bool(cloud['hooks_path'])
                      and cloud['clock'] and 'local session' not in cloud['err'],
                      str(cloud)[:600]))
        marked = run('marked', CLAUDE_CODE_REMOTE='true', PRECEDENT_LOCAL_SESSION='1')
        cases.append(('PRECEDENT_LOCAL_SESSION=1 marks a local session for any harness',
                      not marked['global_email'] and not marked['hooks_path'],
                      str(marked)[:400]))
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_commit_identity_prevents_the_wrong_offset():
    """The declared zone is made TRUE for the session, not merely enforced.

    Three mechanisms already existed and every one of them acts after git has
    resolved an offset: the pre-commit backstop refuses the commit, the
    prepare-commit-msg twin refuses the merge, and the settings.local.json
    derivation applies from the NEXT session because the harness reads
    environment before hooks run. So on a fresh container's first commit --
    the case that matters -- the person is told to retype `TZ=... git commit`
    and the wrong offset was produced in the first place. Asked 2026-09-08:
    "why do we have it do the wrong offset and block it rather than prevent
    the wrong offset?" -- and the honest answer was that nothing prevented it.

    git falls back to the SYSTEM zone when TZ is unset, and the system zone is
    the one lever a hook can move mid-session that every later shell, tool and
    `git merge` picks up without cooperating. So the hook repoints it.

    Measured here that day: the container's zone was Etc/UTC, TZ was unset in
    every tool shell, and .claude/settings.local.json already declared the
    right zone and was inert.

    The two must-not-do cases are the point of the test, not the happy path.
    A GUESSED zone is never written to the machine -- it is not enforced for
    the same reason, and moving a container's clock on a guess is worse than
    a warning. And an unwritable clock must WARN and name the fallback, never
    fall through claiming success.
    """
    import tempfile, json as _json
    hook = ROOT / 'tools' / 'commit-identity.sh'
    if not hook.exists():
        not_applicable('commit-identity prevents the wrong offset',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    ZONE = 'America/Argentina/Buenos_Aires'
    if not pathlib.Path('/usr/share/zoneinfo', ZONE).exists():
        not_applicable('commit-identity prevents the wrong offset',
                       f'no zoneinfo for {ZONE} on this machine')
        return

    def _env(home, localtime, now='UTC'):
        e = dict(os.environ)
        # Hermetic on every axis the hook writes: the clock, the global git
        # config, the global hooks dir, and the user-level config it would
        # otherwise resolve a REAL declared zone from.
        e['HOME'] = home
        e['PRECEDENT_LOCALTIME'] = localtime
        e['PRECEDENT_GLOBAL_HOOKS'] = os.path.join(home, 'git-hooks')
        e['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
        e.pop('PRECEDENT_COMMIT_TZ', None)
        # And what the container's clock currently READS, which the hook
        # compares against before deciding to act. Without pinning this, the
        # test passes only while the machine is on some OTHER zone: the first
        # full-harness run after the fix landed reported four failures, purely
        # because the fix had already put this container on the declared zone
        # and the hook was correctly doing nothing.
        e['TZ'] = now
        return e

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def _repo(name, zone):
            base = tmp / name
            base.mkdir(parents=True)
            subprocess.run(['git', '-C', str(base), 'init', '-q'],
                           capture_output=True)
            if zone:
                (base / 'identity.json').write_text(_json.dumps(
                    {'name': 'T', 'email': 't@example.com',
                     'timezone': zone}), encoding='utf-8')
            return base

        # 1. a DECLARED zone repoints the clock.
        declared = _repo('declared', ZONE)
        home = str(tmp / 'h1'); os.makedirs(home)
        lt = str(tmp / 'lt1')
        r = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                           timeout=120,
                           env=dict(_env(home, lt), CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('a declared zone repoints the system zone file',
                      os.path.islink(lt)
                      and os.readlink(lt) == f'/usr/share/zoneinfo/{ZONE}'))
        cases.append(('and says what it did, and why it is prevention',
                      'prevention' in r.stderr and ZONE in r.stderr))

        # 2. an UNRESOLVED zone repoints the clock too, to the declared
        # fallback. Reversed 2026-09-09 (practice: timestamps-carry-offset):
        # this used to assert the machine was left alone, which in practice
        # meant left on the container's UTC. See the fallback's own note in
        # precedent.json for why applying beats abstaining, and why applying
        # is still not enforcing.
        guessed = _repo('guessed', None)
        home = str(tmp / 'h2'); os.makedirs(home)
        lt2 = str(tmp / 'lt2')
        r2 = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                            timeout=120,
                            env=dict(_env(home, lt2), CLAUDE_PROJECT_DIR=str(guessed)))
        cases.append((f'an unresolved zone repoints the clock to the fallback '
                      f'({_declared_fallback_tz()})',
                      os.path.islink(lt2) and os.readlink(lt2)
                      == f'/usr/share/zoneinfo/{_declared_fallback_tz()}'))
        cases.append(('and names it a fallback rather than this person\'s zone',
                      'DECLARED FALLBACK' in r2.stderr))
        # 2b. ...but only over the container's UTC. A clock already on a
        # real zone was set by someone, and a guess leaves it alone
        # (2026-10-11: a scratch repo with no identity moved a machine on
        # Buenos Aires to the fallback).
        home = str(tmp / 'h2b'); os.makedirs(home)
        lt2b = str(tmp / 'lt2b')
        subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                       timeout=120,
                       env=dict(_env(home, lt2b, now='Asia/Tokyo'),
                                CLAUDE_PROJECT_DIR=str(guessed)))
        cases.append(('a guess never moves a clock already on a real zone',
                      not os.path.lexists(lt2b)))
        # The line that must NOT move: applied is not enforced. A hook run
        # that resolved no zone leaves the pre-commit backstop with no
        # offset to refuse on.
        pre = pathlib.Path(guessed) / '.git' / 'hooks' / 'pre-commit'
        cases.append(('and the backstop still refuses no offset, because '
                      'nobody declared one',
                      pre.exists()
                      and 'expected_offset=""' in pre.read_text(encoding='utf-8')))

        # 3. an unreachable clock warns and names the fallback. A missing
        # parent dir, not a chmod: this runs as root in the container, where
        # a chmod control would pass for the wrong reason.
        home = str(tmp / 'h3'); os.makedirs(home)
        r3 = subprocess.run(
            ['bash', str(hook)], capture_output=True, text=True, timeout=120,
            env=dict(_env(home, str(tmp / 'no-such-dir' / 'lt3')),
                     CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('an unwritable clock warns rather than claiming success',
                      'not writable' in r3.stderr
                      and 'prevention' not in r3.stderr))
        cases.append(('and names the backstop as what still catches it',
                      'backstop will refuse' in r3.stderr))

        # 4. already on the declared zone: no write, no message. A hook that
        # announces itself every session is one people stop reading.
        home = str(tmp / 'h4'); os.makedirs(home)
        lt4 = str(tmp / 'lt4')
        r4 = subprocess.run(
            ['bash', str(hook)], capture_output=True, text=True, timeout=120,
            env=dict(_env(home, lt4, now=ZONE), CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('a clock already on the declared zone is left alone, '
                      'silently', not os.path.lexists(lt4)
                      and 'system timezone was' not in r4.stderr))

    failed = [n for n, ok in cases if not ok]
    check(f'commit-identity prevents the wrong offset, not only refuses it '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_commit_identity_ci_cadence():
    """The CI cadence step tags a commit [skip ci] only when every condition
    in spec/CI_CADENCE_PLAN.md holds, and leaves it alone on any doubt.

    Each skip case below is paired with the case that must NOT skip, because
    the failure that matters is silent: a commit tagged when it should not be
    means CI never ran and nothing says so. The default is the case Morgan
    named, 2026-09-24: with no number declared, CI runs on every push.
    """
    import tempfile, json as _json
    hook = ROOT / 'tools' / 'commit-identity.sh'
    if not hook.exists():
        not_applicable('commit-identity applies the CI cadence',
                       '.claude/hooks/commit-identity.sh is not present here')
        return
    if not pathlib.Path('/usr/share/zoneinfo/UTC').exists():
        not_applicable('commit-identity applies the CI cadence',
                       'no zoneinfo for UTC on this machine')
        return

    SKIP = '[skip ci]'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def _setup(name, personal=None, repo_cfg=None, branches=None):
            base = tmp / name
            home = base / 'home'
            home.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', '--bare', str(base / 'origin.git')],
                           capture_output=True)
            work = base / 'work'
            subprocess.run(['git', 'clone', '-q', str(base / 'origin.git'), str(work)],
                           capture_output=True)
            ident = {'name': 'T', 'email': 't@example.com', 'timezone': 'UTC'}
            if personal is not None:
                ident['ci_every_hours'] = personal
            if branches is not None:
                ident['ci_on_branches'] = branches
            (work / 'identity.json').write_text(_json.dumps(ident), encoding='utf-8')
            cfg = {'visibility': 'private', 'base_branch': 'main'}
            cfg.update(repo_cfg or {})
            cfg = {k: v for k, v in cfg.items() if v is not None}
            (work / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
            env = dict(os.environ)
            for k in ('PRECEDENT_COMMIT_TZ', 'PRECEDENT_COMMIT_EMAIL',
                      'PRECEDENT_COMMIT_NAME', 'PRECEDENT_CI_NOW'):
                env.pop(k, None)
            env.update(HOME=str(home), TZ='UTC',
                       PRECEDENT_LOCALTIME=str(base / 'lt'),
                       PRECEDENT_GLOBAL_HOOKS=str(home / 'git-hooks'),
                       PRECEDENT_USER_CONFIG='/nonexistent/precedent-config.json',
                       CLAUDE_PROJECT_DIR=str(work))
            subprocess.run(['git', '-C', str(work), 'checkout', '-q', '-b', 'main'],
                           capture_output=True, env=env)
            subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                           timeout=120, env=env)
            return work, env

        def _commit(work, env, msg, *extra, old=False, **more):
            e = dict(env, **more)
            if old:
                e['GIT_COMMITTER_DATE'] = '2000-01-01T00:00:00+0000'
            subprocess.run(['git', '-C', str(work), 'add', '-A'], capture_output=True, env=e)
            subprocess.run(['git', '-C', str(work), 'commit', '-q', '--allow-empty',
                            '-m', msg, *extra], capture_output=True, text=True, env=e)
            return subprocess.run(['git', '-C', str(work), 'log', '-1', '--format=%B'],
                                  capture_output=True, text=True, env=e).stdout

        def _push(work, env):
            subprocess.run(['git', '-C', str(work), 'push', '-q', 'origin', 'main'],
                           capture_output=True, env=env)

        # The main line: X=48, private, on the primary branch.
        work, env = _setup('main-line', personal=48)
        cad = pathlib.Path(env['PRECEDENT_GLOBAL_HOOKS']) / 'precedent-ci-cadence'
        cases.append(('the session-start hook writes the cadence script beside '
                      'the global hooks, with the personal value baked in',
                      cad.exists() and 'PERSONAL_CI_EVERY_HOURS = 48'
                      in cad.read_text(encoding='utf-8')))
        _commit(work, env, 'old', old=True)
        _push(work, env)
        a = _commit(work, env, 'A')
        cases.append(('CI that is due runs: the first commit after a quiet '
                      'stretch is not tagged', SKIP not in a))
        b = _commit(work, env, 'B')
        cases.append(('a second commit before the same push is not tagged '
                      'either -- it measures origin, not local history',
                      SKIP not in b))
        _push(work, env)
        c = _commit(work, env, 'C', '-m', 'Body.', '-m', 'Co-Authored-By: X <x@y>')
        cases.append(('a commit within X hours of a CI run on origin is tagged',
                      SKIP in c))
        cases.append(('and the tag goes after the subject, leaving the trailer '
                      'block last', c.startswith('C\n\n[skip ci]')
                      and c.rstrip().endswith('Co-Authored-By: X <x@y>')))
        d = _commit(work, env, 'D', PRECEDENT_CI_NOW='1')
        cases.append(('PRECEDENT_CI_NOW=1 forces a run', SKIP not in d))
        subprocess.run(['git', '-C', str(work), 'checkout', '-q', '-b', 'feature'],
                       capture_output=True, env=env)
        e = _commit(work, env, 'E')
        cases.append(('ci_every_hours alone never tags a working branch -- '
                      'that is ci_on_branches, left at its default here',
                      SKIP not in e))

        # The default: nothing declared means every push.
        work, env = _setup('default')
        _commit(work, env, 'old'); _push(work, env)
        f = _commit(work, env, 'F')
        cases.append(('with no ci_every_hours declared, a recent CI run still '
                      'does not skip the next one (the default is 0)',
                      SKIP not in f))

        # The repo's own value wins, both ways.
        work, env = _setup('repo-zero', personal=48, repo_cfg={'ci_every_hours': 0})
        _commit(work, env, 'old'); _push(work, env)
        g = _commit(work, env, 'G')
        cases.append(('a repo declaring ci_every_hours 0 runs CI every push '
                      'whatever the personal value', SKIP not in g))
        work, env = _setup('repo-48', personal=0, repo_cfg={'ci_every_hours': 48})
        _commit(work, env, 'old'); _push(work, env)
        h = _commit(work, env, 'H')
        cases.append(('a repo declaring its own cadence is honoured over a '
                      'personal 0', SKIP in h))

        # github_ci_main_test, the repository's final say (2026-10-01).
        work, env = _setup('main-test-always', personal=48,
                           repo_cfg={'github_ci_main_test': 'always'})
        _commit(work, env, 'old'); _push(work, env)
        m1 = _commit(work, env, 'M1')
        cases.append(('github_ci_main_test "always" never tags a commit on main, '
                      'whatever the personal hours: every push there is tested',
                      SKIP not in m1))
        work, env = _setup('main-test-hours', personal=0,
                           repo_cfg={'github_ci_main_test': 48})
        _commit(work, env, 'old'); _push(work, env)
        m2 = _commit(work, env, 'M2')
        cases.append(('github_ci_main_test 48 is the hours, over a personal 0',
                      SKIP in m2))
        work, env = _setup('main-test-individual', personal=48,
                           repo_cfg={'github_ci_main_test': 'individual'})
        _commit(work, env, 'old'); _push(work, env)
        m3 = _commit(work, env, 'M3')
        cases.append(('github_ci_main_test "individual" hands it to the personal hours',
                      SKIP in m3))

        # Doubt runs CI.
        work, env = _setup('public', personal=48, repo_cfg={'visibility': None})
        _commit(work, env, 'old'); _push(work, env)
        i = _commit(work, env, 'I')
        cases.append(('a repo that does not declare itself private is never '
                      'tagged', SKIP not in i))
        work, env = _setup('bad-value', personal='48')
        _commit(work, env, 'old'); _push(work, env)
        j = _commit(work, env, 'J')
        cases.append(('a value that is not a number counts as 0', SKIP not in j))
        work, env = _setup('no-origin-ref', personal=48)
        _commit(work, env, 'old')
        k = _commit(work, env, 'K')
        cases.append(('with no origin/<base_branch> to measure, CI runs',
                      SKIP not in k))

        # The branch switch, ci_on_branches (Morgan, 2026-09-24). False tags
        # every commit off the primary branch; the primary branch keeps its
        # own rule, which here is 0 -- every push.
        def _branch(work, env, name='feature'):
            subprocess.run(['git', '-C', str(work), 'checkout', '-q', '-b', name],
                           capture_output=True, env=env)

        work, env = _setup('branches-off', branches=False)
        cad = pathlib.Path(env['PRECEDENT_GLOBAL_HOOKS']) / 'precedent-ci-cadence'
        cases.append(('the personal ci_on_branches value is baked into the '
                      'cadence script', cad.exists() and 'PERSONAL_CI_ON_BRANCHES'
                      ' = False' in cad.read_text(encoding='utf-8')))
        _commit(work, env, 'old'); _push(work, env)
        m = _commit(work, env, 'M')
        cases.append(('ci_on_branches false leaves the primary branch to its '
                      'own cadence (0 here, so not tagged)', SKIP not in m))
        _branch(work, env)
        n = _commit(work, env, 'N')
        cases.append(('ci_on_branches false tags a commit on a working branch',
                      SKIP in n))
        o = _commit(work, env, 'O', '-m', 'Body.', '-m', 'Co-Authored-By: X <x@y>')
        cases.append(('every one of them, not just the first, and after the '
                      'subject', o.startswith('O\n\n[skip ci]')
                      and o.rstrip().endswith('Co-Authored-By: X <x@y>')))
        q = _commit(work, env, 'Q', PRECEDENT_CI_NOW='1')
        cases.append(('PRECEDENT_CI_NOW=1 forces a run on a working branch too',
                      SKIP not in q))
        work, env = _setup('branches-no-origin', branches=False)
        _branch(work, env)
        r = _commit(work, env, 'R')
        cases.append(('a working branch is tagged with nothing pushed yet -- '
                      'the switch does not measure origin', SKIP in r))

        work, env = _setup('branches-default')
        _branch(work, env)
        t = _commit(work, env, 'T')
        cases.append(('with no ci_on_branches declared, a working branch is '
                      'never tagged (the default is true)', SKIP not in t))
        work, env = _setup('branches-bad', branches='false')
        _branch(work, env)
        u = _commit(work, env, 'U')
        cases.append(('a ci_on_branches value that is not the boolean false '
                      'counts as true', SKIP not in u))
        work, env = _setup('branches-repo-zero', branches=False,
                           repo_cfg={'ci_every_hours': 0})
        _branch(work, env)
        v = _commit(work, env, 'V')
        cases.append(('a repo declaring ci_every_hours 0 runs CI on its working '
                      'branches too, whatever the personal switch', SKIP not in v))
        work, env = _setup('branches-repo-off', repo_cfg={'ci_on_branches': False})
        _branch(work, env)
        w = _commit(work, env, 'W')
        cases.append(('a repo declaring its own ci_on_branches false is honoured '
                      'over a personal default', SKIP in w))
        work, env = _setup('branches-public', branches=False,
                           repo_cfg={'visibility': None})
        _branch(work, env)
        x = _commit(work, env, 'X')
        cases.append(('a repo that does not declare itself private is never '
                      'tagged on a branch either', SKIP not in x))

        # The github_ci_ names (spec/BRANCH_TIERS_PLAN.md): read first, the
        # old ci_ names still read where they are absent.
        work, env = _setup('new-name-hours')
        ident = _json.loads((work / 'identity.json').read_text(encoding='utf-8'))
        ident['github_ci_every_hours'] = 48
        (work / 'identity.json').write_text(_json.dumps(ident), encoding='utf-8')
        subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                       timeout=120, env=env)
        _commit(work, env, 'old'); _push(work, env)
        y = _commit(work, env, 'Y')
        cases.append(('the personal github_ci_every_hours is read', SKIP in y))
        work, env = _setup('new-name-repo', repo_cfg={'github_ci_on_branches': False})
        _branch(work, env)
        z = _commit(work, env, 'Z')
        cases.append(("a repo's github_ci_on_branches is read", SKIP in z))
        work, env = _setup('both-names', repo_cfg={'ci_on_branches': False,
                                                   'github_ci_on_branches': True})
        _branch(work, env)
        zz = _commit(work, env, 'ZZ')
        cases.append(('where a file carries both names, github_ci_ wins',
                      SKIP not in zz))

    failed = [n for n, ok in cases if not ok]
    check(f'commit-identity applies the CI cadence only when every condition '
          f'holds ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_push_check_rewrites_global_hooks_older_than_their_writer():
    """The push check rewrites the machine-wide git hooks when the script
    that writes them differs from the one that wrote them -- by content.

    THE BUG (2026-10-29). commit-identity.sh writes the global pre-push,
    refusal text and all, at session start only. A fix to that text
    (3dd840e70) merged into a running container's checkout left pushes
    refused with the old words until the next session start. Hermetic: a
    global git config of its own, a hooks directory holding an old pre-push,
    and a stand-in writer, so the machine's real hooks are never touched.

    THE SECOND BUG (the same day). The first fix compared write times: four
    clones with a byte-identical writer, one checked out after the hooks
    were written, and every --land printed "rewrote the global git hooks"
    over nothing. Now the writer stamps its sha256 beside the hooks.

    A. hooks with no stamp and old text are rewritten, and it says so;
    B. the same writer, written later than the hooks, does not run (the
       second bug: before the content stamp, B printed the note);
    C. a changed writer reruns and says so;
    D. hooks with no stamp whose bytes the writer leaves as they are are
       rewritten silently;
    E. a writer that leaves the hooks alone (a newer engine's) is quiet;
    F. CONTROL: a hooks directory this engine never wrote is left alone;
    G. the real commit-identity.sh writes the stamp this reads."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='global-hooks-refresh-'))
    saved = os.environ.get('GIT_CONFIG_GLOBAL')
    try:
        hooks = tmp / 'hooks'
        hooks.mkdir()
        cfg = tmp / 'gitconfig'
        cfg.write_text(f'[core]\n\thooksPath = {hooks}\n', encoding='utf-8')
        os.environ['GIT_CONFIG_GLOBAL'] = str(cfg)
        pre_push = hooks / 'pre-push'
        stamp = hooks / '.precedent-hooks-writer'
        writer = tmp / 'commit-identity.sh'

        def write_writer(text):
            writer.write_text(
                f'#!/bin/bash\nprintf "# precedent:commit-identity\\n{text}\\n" '
                f'> "{pre_push}"\n'
                f'sha256sum "$0" | cut -c1-64 > "{stamp}"\n', encoding='utf-8')

        def hook(text, stamped=None):
            pre_push.write_text(f'# precedent:commit-identity\n{text}\n',
                                encoding='utf-8')
            if stamped is None:
                stamp.unlink(missing_ok=True)
            else:
                stamp.write_text(stamped + '\n', encoding='utf-8')
        sha = lambda: hashlib.sha256(writer.read_bytes()).hexdigest()
        refresh = getattr(ppc, 'refresh_global_hooks', None)
        text = lambda: pre_push.read_text(encoding='utf-8')

        write_writer('NEW TEXT')
        hook('OLD TEXT')
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('A. unstamped hooks with old text are rewritten, and '
                      'it says so',
                      'NEW TEXT' in text() and bool(note) and 'rewrote' in note,
                      f'{note!r}'))
        hook('OLD TEXT', stamped=sha())
        t0 = time.time()
        os.utime(pre_push, (t0 - 60,) * 2)
        os.utime(writer, (t0,) * 2)
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('B. the same writer, written after the hooks, does not '
                      'run and prints nothing',
                      'OLD TEXT' in text() and note is None, f'{note!r}'))
        old_sha = sha()
        write_writer('CHANGED TEXT')
        hook('NEW TEXT', stamped=old_sha)
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('C. a changed writer reruns and says so, as information '
                      'rather than a NOTE an upstream review would list',
                      'CHANGED TEXT' in text() and bool(note)
                      and 'rewrote' in note and 'NOTE' not in note, f'{note!r}'))
        hook('CHANGED TEXT')
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('D. unstamped hooks the writer leaves byte-identical '
                      'are stamped silently',
                      note is None and stamp.is_file()
                      and stamp.read_text().strip() == sha(), f'{note!r}'))
        writer.write_text('#!/bin/bash\nexit 0\n', encoding='utf-8')
        hook('NEWER ENGINE', stamped='0' * 64)
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('E. a writer that leaves the hooks alone is quiet',
                      'NEWER ENGINE' in text() and note is None, f'{note!r}'))
        write_writer('NEW TEXT')
        pre_push.write_text('#!/bin/sh\necho somebody else\n', encoding='utf-8')
        stamp.unlink(missing_ok=True)
        note = refresh(ROOT, script=writer) if refresh else None
        cases.append(('F. CONTROL: a hook this engine never wrote is left alone',
                      'somebody else' in text() and note is None, f'{note!r}'))
        real = (ROOT / 'tools' / 'commit-identity.sh').read_text(encoding='utf-8')
        cases.append(('G. commit-identity.sh writes the writer stamp',
                      '.precedent-hooks-writer' in real, ''))
    finally:
        if saved is None:
            os.environ.pop('GIT_CONFIG_GLOBAL', None)
        else:
            os.environ['GIT_CONFIG_GLOBAL'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + ' -- ' + c[2] for c in cases if not c[1]]
    check(f'the push check rewrites global hooks whose writer changed, by '
          f'content ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_global_pre_push_runs_the_leak_gate():
    """The global pre-push hook commit-identity.sh writes runs the leak gate
    over every commit a push would publish, on any branch, before the
    repository's own pre-push -- so a plain `git push` is checked locally,
    whatever harness is or is not loaded.

    THE INCIDENT (2026-10-10). A session rooted above its repositories, which
    never loads the harness's push gate, pushed a working branch with a
    private repository's name in a commit; nothing ran. Morgan, the same
    day: "it's important that leak-gate goes to every branch, but the check
    must be local to avoid lots of github minutes billing issues". The
    DISCRIMINATING CASE is the first: on the hook before this, the push
    went through. The fixture owns its repositories and its HOME."""
    import shutil, tempfile
    cases = []
    ci_hook = ROOT / 'tools' / 'commit-identity.sh'
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home')}
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        (tmp / 'home').mkdir()
        # An empty file of its own rather than /dev/null, so this fixture
        # never depends on the device being one.
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        g = lambda cwd, *a, **e: subprocess.run(
            ['git', '-C', str(cwd), *a], capture_output=True, text=True,
            env={**env, **e})
        bare, work = tmp / 'origin.git', tmp / 'work'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        g(tmp, 'init', '-q', '-b', 'main', str(work))
        (work / 'tools').mkdir()
        for name in ('leak_gate.py', 'leak-blocklist.default.txt'):
            shutil.copy(ROOT / 'tools' / name, work / 'tools' / name)
        (work / 'identity.json').write_text(json.dumps(
            {'name': 'T', 'email': 't@example.com', 'timezone': 'UTC'}),
            encoding='utf-8')
        (work / 'a.md').write_text('a\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base')
        g(work, 'remote', 'add', 'origin', f'file://{bare}')
        g(work, 'push', '-q', 'origin', 'main')
        hooks = tmp / 'hooks'
        # The global config the hook is pointed at is a symlink to an empty
        # file, standing in for /dev/null: git reads it, and it is not a
        # regular file (a device cannot be made without root, a fifo would
        # block git's read, a directory stops git outright). On 2026-10-10
        # this very test, run with the fixture's GIT_CONFIG_GLOBAL=/dev/null,
        # had `git config --global` replace the container's /dev/null with
        # an ordinary file.
        (tmp / 'empty').write_text('', encoding='utf-8')
        decoy = tmp / 'not-a-file'
        decoy.symlink_to(tmp / 'empty')
        subprocess.run(['bash', str(ci_hook)], capture_output=True, text=True,
                       timeout=120,
                       env=dict(env, CLAUDE_PROJECT_DIR=str(work),
                                GIT_CONFIG_GLOBAL=str(decoy),
                                PRECEDENT_COMMIT_NAME='T',
                                PRECEDENT_COMMIT_EMAIL='t@example.com',
                                PRECEDENT_GLOBAL_HOOKS=str(hooks),
                                PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                                PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
        cases.append(('the hook never writes a global config that is not a '
                      'regular file -- it is left exactly as it was',
                      decoy.is_symlink() and (tmp / 'empty').read_text() == '',
                      ''))
        g(work, 'config', 'core.hooksPath', str(hooks))
        home_path = '/' + 'Users/someone/notes'       # assembled: see check_leak_gate_fires
        (work / 'b.md').write_text(f'see {home_path}\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'notes', '--no-verify')
        (work / 'b.md').write_text('clean\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'scrub', '--no-verify')
        r = g(work, 'push', 'origin', 'HEAD:refs/heads/feature')
        cases.append(('THE DISCRIMINATING CASE: a branch push carrying a leak a '
                      'later commit scrubbed is refused, saying why',
                      r.returncode != 0 and 'push refused: the leak gate' in r.stderr
                      and not g(work, 'ls-remote', 'origin', 'feature').stdout.strip(),
                      failure_detail(r.stderr, 600)))
        r = g(work, 'push', 'origin', 'HEAD:refs/heads/feature',
              PRECEDENT_SKIP_LEAK_GATE='1')
        cases.append(('PRECEDENT_SKIP_LEAK_GATE=1 lets one push through, and says so',
                      r.returncode == 0 and 'leak gate SKIPPED' in r.stderr,
                      failure_detail(r.stderr, 400)))
        (work / 'c.md').write_text('c\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'clean', '--no-verify')
        r = g(work, 'push', 'origin', 'HEAD:refs/heads/feature')
        cases.append(('a clean push goes through, judging only the new commit',
                      r.returncode == 0, failure_detail(r.stderr, 400)))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the global pre-push runs the leak gate on every push '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_global_backstop_runs_person_fixer():
    """The commit backstop runs the person's own commit-time fixer --
    `bootstrap/pre-commit-fix` in their individual source -- before every
    commit (Morgan, 2026-09-27: a version header a session left unbumped;
    prevent the miss, don't just catch it sooner). Three things are pinned:
    the fixer runs; what it stages lands in the SAME commit; and a fixer that
    fails never refuses the commit, because a fixer is not a gate."""
    import tempfile, json as _json
    name = "the commit backstop runs the person's pre-commit fixer and never lets it refuse"
    ci_hook = ROOT / 'tools' / 'commit-identity.sh'
    if not ci_hook.exists():
        not_applicable(name, '.claude/hooks/commit-identity.sh is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        home, hooks = tmp / 'home', tmp / 'git-hooks'
        home.mkdir()
        indiv = tmp / 'indiv'
        (indiv / 'bootstrap').mkdir(parents=True)
        (indiv / 'identity.json').write_text(_json.dumps(
            {'name': 'T', 'email': 't@example.com', 'timezone': 'UTC'}),
            encoding='utf-8')
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(indiv)}}),
                       encoding='utf-8')
        mark = tmp / 'ran'
        fixer = indiv / 'bootstrap' / 'pre-commit-fix'
        order = tmp / 'order'
        fixer.write_text('#!/bin/sh\necho ran >> "%s"\necho fixer >> "%s"\n'
                         'echo fixed > FIXED.txt\n'
                         'git add FIXED.txt\nexit 3\n' % (mark, order), encoding='utf-8')
        fixer.chmod(0o755)
        env = dict(os.environ, HOME=str(home), TZ='UTC',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(cfg),
                   PRECEDENT_GLOBAL_HOOKS=str(hooks),
                   PRECEDENT_LOCALTIME=str(tmp / 'lt'))
        env.pop('PRECEDENT_ALLOW_ANY_AUTHOR', None)
        env.pop('PRECEDENT_COMMIT_TZ', None)
        work = tmp / 'work'
        subprocess.run(['git', 'init', '-q', str(work)], capture_output=True, env=env)
        subprocess.run(['bash', str(ci_hook)], capture_output=True, text=True,
                       timeout=120, env=dict(env, CLAUDE_PROJECT_DIR=str(work)))
        cases.append(('the global pre-commit calls the fixer by its resolved path',
                      str(fixer) in (hooks / 'pre-commit').read_text(encoding='utf-8')
                      if (hooks / 'pre-commit').exists() else False))
        (work / 'a.txt').write_text('a\n', encoding='utf-8')
        # The engine's rebuild of generated files, stubbed to record when it
        # ran: it must come after the fixer, or a header the fixer stamps on
        # a source (MAP.source.md, say) leaves the view built from the old one.
        (work / 'tools').mkdir()
        (work / 'tools' / 'precedent_regenerate.py').write_text(
            'open(%r, "a").write("regenerate\\n")\n' % str(order), encoding='utf-8')
        subprocess.run(['git', '-C', str(work), 'add', 'a.txt'],
                       capture_output=True, env=env)
        c = subprocess.run(['git', '-C', str(work), '-c', 'user.name=T', '-c',
                            'user.email=t@example.com', 'commit', '-q', '-m', 'x'],
                           capture_output=True, text=True, env=env)
        cases.append(('the fixer runs before the commit', mark.exists()))
        cases.append(('a fixer that exits non-zero does not refuse the commit',
                      c.returncode == 0))
        files = subprocess.run(['git', '-C', str(work), 'show', '--name-only',
                                '--format=', 'HEAD'], capture_output=True,
                               text=True, env=env).stdout.split()
        cases.append(('what the fixer stages lands in the same commit',
                      'FIXED.txt' in files))
        ran = order.read_text(encoding='utf-8').split() if order.exists() else []
        cases.append(('the fixer runs before the rebuild of generated files, so a '
                      'source it stamps is what the view is built from',
                      ran == ['fixer', 'regenerate']))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


@_without_session_id
def _engine_commit_fixture(tmp, name, kind, git_env):
    """A repository with an origin, the REAL engine files the engine-commit
    checks exercise, and stubs for the gates they do not. -> (work, bare).
    The stubs pass; test_in_copy.sh leaves a marker naming the checkout it
    ran in when CS_MARK is set, so a caller can prove consumer_shape ran."""
    import json as _json, shutil as _shutil
    bare, work = tmp / f'{name}.git', tmp / name
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'beta', str(bare)],
                   env=git_env, capture_output=True)
    (work / 'tools' / 'checks' / 'tests').mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', '-b', 'beta', str(work)],
                   env=git_env, capture_output=True)
    real = ['precedent_branches.py', 'precedent_push_check.py',
            'precedent_identity.py', 'precedent_time.py',
            'precedent_consumer_shape.py']
    for f in real:
        _shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
    stubs = {
        'precedent_check.py': (
            'import sys\n'
            'CHECKS = {"x": {"binds_publishers": True}}\n'
            'if __name__ == "__main__":\n'
            '    print("precedent_check: 3 passed, 0 violated")\n'),
        'leak_gate.py': '',
        'doc_lint.py': '',
        # consumer_shape imports these two for what a consumer receives.
        'build_views.py': ('def _engine_tool_paths(): return set()\n'
                           'def _json_str(v): return v\n'
                           'def ships_paths(fm): return []\n'),
        'split_practices.py': 'def _read_practice_file(p): return {}, {}\n',
    }
    for f, body in stubs.items():
        (work / 'tools' / f).write_text(body, encoding='utf-8')
    (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(_json.dumps(
        {'kind': kind, 'files': real + list(stubs)}), encoding='utf-8')
    tests = work / 'tools' / 'checks' / 'tests'
    (tests / 'run_all.sh').write_text('exit 0\n', encoding='utf-8')
    (tests / 'test_in_copy.sh').write_text(
        'top="$(git rev-parse --show-toplevel)" || exit 1\n'
        'git rev-parse -q --verify HEAD >/dev/null || exit 1\n'
        '[ -z "$(git status --porcelain --untracked-files=no)" ] || '
        '{ git status --porcelain; exit 1; }\n'
        '[ -n "${CS_MARK:-}" ] && echo "ran in $(basename "$top")" >> "$CS_MARK"\n'
        'exit 0\n', encoding='utf-8')
    (work / 'precedent.json').write_text(_json.dumps({'base_branch': 'beta'}),
                                         encoding='utf-8')
    (work / 'list.txt').write_text('a\n', encoding='utf-8')
    for args in (['add', '-A'], ['commit', '-q', '-m', 'init'],
                 ['remote', 'add', 'origin', f'file://{bare}'],
                 ['push', '-q', 'origin', 'beta']):
        subprocess.run(['git', '-C', str(work), *args], env=git_env,
                       capture_output=True, text=True)
    return work, bare


def _engine_commit_env(tmp):
    """-> (ambient, person, person_git). `ambient` is what a hookless session
    had on 2026-09-26: git's global identity is the container's bot, no
    ~/.config/precedent/config.json, and a TZ that is not the person's --
    and nothing else from this machine (practice: fixture-owns-its-state).
    `person` is the PRECEDENT_COMMIT_* declaration on top of it;
    `person_git` authors the fixture's OWN commits as the person, so the
    only commits that can come out as the bot are the ones the engine made."""
    gcfg = tmp / 'gitconfig'
    gcfg.write_text('[user]\n\tname = Claude\n\temail = noreply@anthropic.com\n',
                    encoding='utf-8')
    ambient = {k: v for k, v in os.environ.items()
               if not k.startswith(('GIT_', 'PRECEDENT_', 'CLAUDE_'))
               and k != 'TZ'}
    ambient.update(GIT_CONFIG_GLOBAL=str(gcfg), GIT_CONFIG_NOSYSTEM='1',
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-config.json'),
                   PRECEDENT_ALLOW_ANY_AUTHOR='1', TZ='America/New_York')
    person = dict(ambient, PRECEDENT_COMMIT_NAME='Pat Person',
                  PRECEDENT_COMMIT_EMAIL='pat@example.com',
                  PRECEDENT_COMMIT_TZ='Asia/Kolkata')
    person_git = dict(ambient, GIT_AUTHOR_NAME='Pat Person',
                      GIT_AUTHOR_EMAIL='pat@example.com',
                      GIT_COMMITTER_NAME='Pat Person',
                      GIT_COMMITTER_EMAIL='pat@example.com')
    return ambient, person, person_git


def check_history_checks_never_ride_a_reused_pass():
    """A recorded or shared pass is keyed on the TREE; commit_author and
    commit_dates judge COMMITS (2026-09-26).

    Two commits can carry one tree with different authors -- the merge a
    Promote makes has exactly the tree its checked parents had. On
    2026-09-26 Promote reused another checkout's pass for the same tree in
    four repositories, "nothing to re-run", and the bot-authored merges it
    had just made went out with commit_author never having seen them. So a
    reused pass still runs the two history checks.

    Both ways a pass is reused are built here: this checkout's own record,
    and a receipt another checkout published to origin. THE CONTROL: the
    same reuse over a commit the declared person made still passes, and says
    it reused the pass -- so the failure is the author, and the reuse path
    is the one being exercised (practice: control-asserts-which-failure)."""
    import tempfile, shutil as _shutil
    name = 'History checks never ride a reused pass'
    author_check = ROOT / 'tools' / 'check_commit_author.py'
    if not author_check.exists():
        not_applicable(name, 'tools/check_commit_author.py is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        ambient, person, person_git = _engine_commit_env(tmp)
        bot_git = dict(ambient, GIT_AUTHOR_NAME='Claude',
                       GIT_AUTHOR_EMAIL='noreply@anthropic.com')
        work, bare = _engine_commit_fixture(tmp, 'work', 'consumer', person_git)
        _shutil.copy2(author_check, work / 'tools' / author_check.name)
        _shutil.copy2(ROOT / 'tools' / 'commit_checks_common.py',
                      work / 'tools' / 'commit_checks_common.py')

        def git(cwd, *args, env=person_git):
            return subprocess.run(['git', '-C', str(cwd), *args],
                                  capture_output=True, text=True, env=env)

        def gate(cwd, *extra):
            p = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                                '--tier', 'full', '--because', 'harness case', *extra], cwd=cwd,
                               capture_output=True, text=True, env=person)
            return p.returncode, p.stdout + p.stderr

        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'carry the author check')
        git(work, 'push', '-q', 'origin', 'beta')
        git(work, 'checkout', '-q', '-b', 'feature')
        (work / 'list.txt').write_text('checked\n', encoding='utf-8')
        git(work, 'commit', '-qam', 'the checked files')
        rc, out = gate(work)
        cases.append((f'the fixture tree passes the full check and is recorded '
                      f'(rc={rc})', rc == 0 and 'recorded for tree' in out))
        git(work, 'push', '-q', 'origin', 'feature')

        # Same tree, a commit by the bot on top: the local record is reused.
        git(work, 'commit', '-q', '--allow-empty', '-m', 'bot merge', env=bot_git)
        rc, out = gate(work, '--gate')
        cases.append((f'a pass THIS checkout recorded for the tree does not '
                      f'wave through a bot-authored commit with the same tree '
                      f'(rc={rc}, {out.strip()[-200:]!r})',
                      rc == 1 and 'already passed' in out
                      and 'FAILED -- commit_author' in out
                      and 'noreply@anthropic.com' in out))

        # THE CONTROL: the same reuse over the person's own commit.
        git(work, 'reset', '-q', '--hard', 'HEAD~1')
        git(work, 'commit', '-q', '--allow-empty', '-m', 'person merge')
        rc, out = gate(work, '--gate')
        cases.append((f'control: the same reused pass over a commit the '
                      f'declared person made passes, and says it reused the '
                      f'files (rc={rc}, {out.strip()[-160:]!r})',
                      rc == 0 and 'already passed' in out
                      and 'judge commits rather than files' in out))

        # A receipt another checkout published, reused from a fresh clone.
        other = tmp / 'other'
        git(tmp, 'clone', '-q', '-b', 'feature', f'file://{bare}', str(other))
        git(other, 'commit', '-q', '--allow-empty', '-m', 'bot merge',
            env=bot_git)
        rc, out = gate(other, '--gate')
        cases.append((f'a pass SHARED by another checkout does not wave '
                      f'through a bot-authored commit either (rc={rc}, '
                      f'{out.strip()[-200:]!r})',
                      rc == 1 and 'in another checkout' in out
                      and 'FAILED -- commit_author' in out))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_identity_mechanism_check_reaches_a_stubbed_hook():
    """check_commit_author's prevention half runs where the hook is a stub
    (2026-10-17).

    Since 2026-10-07 every hook in .claude/hooks/ is one stub that runs
    tools/<its name>, so `precedent:commit-identity` is in
    tools/commit-identity.sh and in no hook file. find_identity_script()
    looked for it only in the hook files, found nothing in BestPractice or
    any consumer, and the half that RUNS the identity hook and tries the
    wrong-author commit returned no findings -- a pass -- without running.
    Found by the very deep check (pass 2, question 15).

    THE PLANT: a consumer whose stubbed hook delegates to a
    tools/commit-identity.sh that carries the marker and sets no identity --
    the check must report the identity it failed to set. THE CONTROLS: the
    real engine script beside the same stub passes with no findings, and a
    stub whose tools/ script lacks the marker is not taken for the identity
    hook (practice: control-asserts-which-failure)."""
    import tempfile, shutil as _shutil
    name = 'The identity mechanism check reaches a stubbed hook'
    stub = ROOT / '.claude' / 'hooks' / 'commit-identity.sh'
    real = ROOT / 'tools' / 'commit-identity.sh'
    if not stub.is_file() or not real.is_file():
        not_applicable(name, '.claude/hooks/commit-identity.sh or '
                             'tools/commit-identity.sh is absent here')
        return
    probe = ('import json, sys; sys.path.insert(0, "tools"); '
             'import check_commit_author as c; s = c.find_identity_script(); '
             'print(json.dumps([s.name if s else None, '
             'c.mechanism_findings() if s else []]))')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        def fixture(label, script_text):
            repo = pathlib.Path(td) / label
            (repo / '.claude' / 'hooks').mkdir(parents=True)
            _shutil.copytree(ROOT / 'tools', repo / 'tools',
                             ignore=_shutil.ignore_patterns('__pycache__'))
            _shutil.copy2(stub, repo / '.claude' / 'hooks' / stub.name)
            _shutil.copy2(ROOT / '.claude' / 'settings.json',
                          repo / '.claude' / 'settings.json')
            if script_text is not None:
                (repo / 'tools' / 'commit-identity.sh').write_text(
                    script_text, encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(repo)],
                           capture_output=True)
            subprocess.run(['git', '-C', str(repo), 'add', '-A'],
                           capture_output=True)
            env = dict(os.environ, PRECEDENT_COMMIT_NAME='Fixture Person',
                       PRECEDENT_COMMIT_EMAIL='fixture@example.com',
                       PRECEDENT_COMMIT_TZ='UTC')
            p = subprocess.run([sys.executable, '-c', probe], cwd=str(repo),
                               capture_output=True, text=True, env=env,
                               timeout=120)
            try:
                return json.loads(p.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                return [None, ['probe failed: ' + (p.stderr or p.stdout)[-300:]]]

        broken = fixture('broken', '#!/bin/bash\n# precedent:commit-identity\n'
                                   'exit 0\n')
        cases.append(('a stub whose engine script sets no identity is found '
                      'and reported', broken[0] == 'commit-identity.sh'
                      and any('user.name' in f for f in broken[1]),
                      repr(broken)[:400]))
        good = fixture('good', None)
        cases.append(('the real engine script behind the same stub passes',
                      good == ['commit-identity.sh', []], repr(good)[:400]))
        unmarked = fixture('unmarked', '#!/bin/bash\nexit 0\n')
        cases.append(('a stub whose tools/ script lacks the marker is not '
                      'taken for the identity hook', unmarked[0] is None,
                      repr(unmarked)[:400]))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_github_ci_setting_names():
    """The three GitHub settings are named `github_ci_*` since 2026-09-25
    (spec/BRANCH_TIERS_PLAN.md); every reader takes the new name first and
    the old `ci_*` one where it is absent. The failure that matters is
    silent: a renamed key nobody reads falls back to the default, and for
    the workflow switch the default decides whether a workflow is installed
    at all."""
    import tempfile, json as _json
    name = 'the github_ci_ setting names are read, and the old ci_ names still are'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_identity as pi
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        nocfg = str(repo / 'none.json')

        def pref(ident):
            (repo / 'identity.json').write_text(_json.dumps(
                dict({'name': 'T', 'email': 't@example.com'}, **ident)), encoding='utf-8')
            return pi.ci_preference(repo, nocfg)['enabled']
        cases.append(('github_ci_workflows "enabled" is read',
                      pref({'github_ci_workflows': 'enabled'})))
        cases.append(('the old ci_workflows is still read',
                      pref({'ci_workflows': 'enabled'})))
        cases.append(('where both appear, github_ci_workflows wins',
                      not pref({'ci_workflows': 'enabled',
                                'github_ci_workflows': 'disabled'})))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def _declared_fallback_tz():
    """This repository's declared last-resort timezone, read from the engine
    rather than typed into a test.

    precedent_check.py's `timestamps-carry-offset` asserts that
    precedent_time.FALLBACK_TZ and both copies of commit-identity.sh agree,
    so reading any one of them is reading all three -- and reading beats
    restating, which is what turned a one-line value change into two mystery
    failures once already.

    NOT precedent.json, since 2026-09-14: a repo's own `fallback_timezone`
    is the rung that OVERRIDES these three, and is free to differ. The
    fixtures below run where no repo-level value applies, so the engine
    constant is the right thing to read for them."""
    import precedent_time
    return precedent_time.FALLBACK_TZ


def check_repo_may_declare_its_own_fallback_zone():
    """A repo's own `fallback_timezone` overrides the engine's; drift BETWEEN
    the engine files is still a violation.

    Both directions, because only one of them was ever wrong and the wrong
    one looks exactly like the right one from inside the check. Until
    2026-09-14 `timestamps-carry-offset` compared FOUR holders as one
    equality set -- precedent.json plus the three engine files -- and so
    reported a repo exercising the documented rung-5 override as "the
    declared fallback zone disagrees". Reproduced in a private consumer
    declaring America/Argentina/Buenos_Aires against untouched engine files:
    red check, correct runtime behaviour.

    A control that only planted the drift would have passed before the fix
    too (practice: control-asserts-which-failure), so the override case is
    the one that carries this.
    """
    import shutil, tempfile, json as _json

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-tz-rung-'))
    try:
        # Only what the check reads: precedent.json, the catalogue and the
        # engine, and not this harness, whose parse was most of each run.
        # The check lists untracked files too, so a git init is enough and
        # nothing is committed. The whole checkout, added and committed,
        # took 29-61 s; this takes about 4 (2026-10-31).
        repo = tmp / 'repo'
        repo.mkdir()
        shutil.copy2(ROOT / 'precedent.json', repo / 'precedent.json')
        shutil.copytree(ROOT / 'practices', repo / 'practices', symlinks=True)
        shutil.copytree(ROOT / 'tools', repo / 'tools', symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc',
                                                      'prompts', 'verify_harness.py'))
        subprocess.run(['git', '-C', str(repo), 'init', '-q'], check=True)

        def run():
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
            env['PRECEDENT_USER_CONFIG'] = str(repo / '.no-user-config.json')
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_check.py'),
                 '--only', 'timestamps-carry-offset'],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        cfg = repo / 'precedent.json'
        data = _json.loads(cfg.read_text(encoding='utf-8'))
        data['fallback_timezone'] = 'America/Argentina/Buenos_Aires'
        cfg.write_text(_json.dumps(data, indent=2) + '\n', encoding='utf-8')
        rc_override, out_override = run()
        check('a repo declaring its own fallback_timezone, with the engine '
              'files untouched, passes timestamps-carry-offset (rung 5 '
              'overrides rung 6 -- it is not drift)',
              rc_override == 0, failure_detail(out_override.strip(), 400))

        eng = repo / 'tools' / 'precedent_time.py'
        eng.write_text(eng.read_text(encoding='utf-8').replace(
            "FALLBACK_TZ = 'America/New_York'",
            "FALLBACK_TZ = 'Europe/Madrid'"), encoding='utf-8')
        rc_drift, out_drift = run()
        check('the engine\'s own fallback zone drifting between '
              'precedent_time.py and the commit hooks IS still reported, by '
              'that name',
              rc_drift != 0 and 'engine' in out_drift.lower()
              and 'fallback zone disagrees' in out_drift,
              failure_detail(out_drift.strip(), 400))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_commit_identity_copies_are_identical():
    """The hook exists three times and every copy must be the same file.

    templates/harness/claude-code/hooks/ is what an adopter instantiates,
    .claude/hooks/ is what this repo runs on itself (a drift there is this
    repo failing to run what it ships), and the individual practice source
    carries a third copy that session-start.sh runs for ATTACHED repos, whose
    own hooks never fire. 2026-09-07 the merge backstop -- the fix for git
    not running pre-commit on a merge commit, which is how a wrong-offset
    commit reached main in the first place -- was added to the individual
    source's copy alone and sat there unpropagated for hours, so the repo
    that defines the fix did not have it. parallel-artifact-ledger names this
    exact shape; this makes it mechanical instead.
    """
    import hashlib as _h
    here = ROOT / 'tools' / 'commit-identity.sh'
    tmpl = ROOT / 'tools' / 'commit-identity.sh'
    if not (here.exists() and tmpl.exists()):
        not_applicable('every copy of commit-identity.sh is byte-identical',
                       'not every copy is present in this tree')
        return
    digests = {p: _h.sha256(p.read_bytes()).hexdigest()
               for p in (here, tmpl)}
    # The individual source is outside this repo and only sometimes attached,
    # so it is compared when reachable and skipped -- named -- when not.
    #
    # WHICH clone of the individual source. There are routinely two on one
    # machine and they are not interchangeable: the config-named one
    # (~/.config/precedent/config.json), which precedent-individual-bootstrap.sh
    # `git pull --ff-only`s from origin at every session start, and an
    # ATTACHED sibling beside this repo, which is the one a session actually
    # edits and pushes from. The attached one therefore wins here. Comparing
    # against the config-named clone instead reports drift for every
    # uncommitted edit in progress -- which this check did on its very first
    # run, against a change being made three directories away. That is the
    # same two-clone trap AGENTS.md's gotchas section already records; the
    # rule that resolves it is: the pulled clone can only ever be BEHIND, so
    # it is never the better evidence of what the source says.
    third, note = None, ''
    try:
        import json as _json
        cfg = pathlib.Path(os.environ.get(
            'PRECEDENT_USER_CONFIG',
            str(pathlib.Path.home() / '.config' / 'precedent' / 'config.json')))
        path = None
        if cfg.exists():
            path = (_json.loads(cfg.read_text(encoding='utf-8'))
                    .get('individual') or {}).get('path')
        cands = []
        if path:
            attached = ROOT.parent / pathlib.Path(path).name
            if attached != ROOT and attached.is_dir():
                cands.append(attached)
            cands.append(pathlib.Path(path))
        for base in cands:
            cand = base / 'bootstrap' / 'commit-identity.sh'
            # Since 2026-10-07 a set carries the hook STUB, which runs the
            # engine's script and holds no logic of its own, so it never
            # matches the script byte for byte. Only a full copy can lag.
            if cand.exists() and b'# PRECEDENT HOOK STUB.' in cand.read_bytes():
                third = 'stub'
                break
            if cand.exists():
                third = cand
                digests[cand] = _h.sha256(cand.read_bytes()).hexdigest()
                break
    except Exception:
        pass

    # EVERY OTHER ATTACHED SOURCE'S COPY, and this is where the check had a
    # hole. It compared three copies -- this repo's two and the individual
    # source's -- and a SHARED set carries one too, at .claude/hooks/. Nothing
    # looked there, so both shared sets sat three generations behind
    # (2026-09-07: missing the merge backstop, the timezone derivation AND
    # the global identity fix) while this check reported every copy
    # identical. A check that names the copies it compares is only as good
    # as that list, so the list is now discovered rather than written down.
    #
    # SIBLINGS ARE NOT THE WHOLE LIST EITHER (2026-09-14). A declared source
    # lives wherever its config says -- this repo's own container keeps the
    # individual set at $HOME while everything else sits under another
    # parent -- so the glob is UNIONED with what the resolver declares
    # rather than trusted on its own. Same assumption, same failure shape as
    # gotchas/gotcha-2026-09-14-the-session-start-identity-block-reaches-every-precedent-rep.md, which is what sent somebody looking for the
    # rest of them.
    team_dirs = list(ROOT.parent.glob('precedent-team-*'))
    try:
        import precedent_resolve as _pr
        team_dirs += [pathlib.Path(x['path']).expanduser()
                      for x in _pr.load_config(ROOT)
                      if x.get('level') == 'team' and x.get('path')]
    except Exception:
        pass
    seen_dirs = set()
    for sib in sorted(team_dirs):
        real = str(sib.resolve())
        if real in seen_dirs:
            continue
        seen_dirs.add(real)
        cand = sib / '.claude' / 'hooks' / 'commit-identity.sh'
        if cand.exists() and b'# PRECEDENT HOOK STUB.' in cand.read_bytes():
            continue
        if cand.exists():
            digests[cand] = _h.sha256(cand.read_bytes()).hexdigest()
    if third == 'stub':
        note = (' (the individual source carries the hook stub, which holds no '
                'logic of its own, so it was not compared)')
    elif third is None:
        note = (' (the individual source\'s copy was not reachable from here '
                'and was NOT compared)')
    uniq = set(digests.values())
    check(f'every reachable copy of commit-identity.sh is byte-identical '
          f'({len(digests)} copies found){note}',
          len(uniq) == 1,
          '; '.join(f'{p.relative_to(ROOT) if ROOT in p.parents else p}='
                    f'{d[:12]}' for p, d in digests.items()))


def check_person_zone_wins_in_a_shared_rooted_session():
    """The person's declared zone wins over a repo's fallback, whichever repo
    the session is rooted in (Morgan, 2026-09-25: "I meant the repo timezone
    to be a fallback, in case there is no defined individual timezone
    defined", strength: decided).

    The failure this pins, measured that day: a session rooted in a shared
    repo, the person named by PRECEDENT_COMMIT_NAME/EMAIL with no
    PRECEDENT_COMMIT_TZ, their zone declared only in their individual
    source's identity.json. commit-identity.sh never read that zone, so the
    session ran on the repo's New York fallback, and the global backstop it
    generated enforced no offset at all -- three -0400 commits reached the
    individual source, one of them a Promote merge, and only the full check
    noticed.

    The control is the person with no zone: the repo's fallback is applied
    and nothing is refused, exactly as before."""
    import tempfile
    name = "the person's zone wins over a repo's fallback in a shared-rooted session"
    script = ROOT / 'tools' / 'commit-identity.sh'
    if not script.exists():
        not_applicable(name, '.claude/hooks/commit-identity.sh is not present here')
        return
    BA, NY = 'America/Argentina/Buenos_Aires', 'America/New_York'
    cases = []

    def run(declare_zone):
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            home = tmp / 'home'
            home.mkdir()
            indiv = tmp / 'individual'
            indiv.mkdir()
            ident = {'name': 'Morgan F', 'email': 'm@example.com'}
            if declare_zone:
                ident['timezone'] = BA
            (indiv / 'identity.json').write_text(json.dumps(ident), encoding='utf-8')
            cfg = tmp / 'config.json'
            cfg.write_text(json.dumps({'individual': {'path': str(indiv)}}),
                           encoding='utf-8')
            env = dict(os.environ, HOME=str(home), PRECEDENT_USER_CONFIG=str(cfg),
                       PRECEDENT_COMMIT_NAME='Morgan F',
                       PRECEDENT_COMMIT_EMAIL='m@example.com',
                       PRECEDENT_LOCALTIME=str(tmp / 'localtime'), TZ=NY)
            for k in ('PRECEDENT_ALLOW_ANY_AUTHOR', 'PRECEDENT_COMMIT_TZ'):
                env.pop(k, None)

            def g(*a, cwd=None, extra=None):
                return subprocess.run(['git'] + list(a), capture_output=True,
                                      text=True, env=dict(env, **(extra or {})),
                                      cwd=str(cwd) if cwd else None, timeout=120)

            shared = tmp / 'shared'
            shared.mkdir()
            g('init', '-q', str(shared))
            (shared / 'precedent.json').write_text(
                json.dumps({'fallback_timezone': NY}), encoding='utf-8')
            subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(shared)), timeout=180)
            local = shared / '.claude' / 'settings.local.json'
            try:
                session_tz = json.loads(local.read_text())['env']['TZ']
            except Exception:
                session_tz = None
            other = tmp / 'other'
            other.mkdir()
            g('init', '-q', str(other))
            (other / 'f').write_text('x', encoding='utf-8')
            g('add', 'f', cwd=other)
            wrong = g('commit', '-m', 'ny', cwd=other, extra={'TZ': NY})
            refused = 'declared timezone' in (wrong.stdout + wrong.stderr)
            right = g('commit', '-q', '-m', 'ba', cwd=other, extra={'TZ': BA})
            probe = subprocess.run(
                [sys.executable, '-c',
                 'import sys; sys.path.insert(0, sys.argv[1]); '
                 'import precedent_time, precedent_identity; '
                 'print(precedent_time.resolved(sys.argv[2])[1]); '
                 'print(precedent_identity.declared_identity(sys.argv[2])["timezone"])',
                 str(ROOT / 'tools'), str(shared)],
                capture_output=True, text=True, env=env, timeout=60).stdout.split()
            return session_tz, refused, right.returncode == 0, probe

    tz, refused, ok, probe = run(declare_zone=True)
    cases.append(('the session takes the person\'s zone, not the repo\'s New '
                  'York fallback', tz == BA))
    cases.append(('the global backstop refuses a New York commit in another repo',
                  refused))
    cases.append(('and lets the person\'s own offset through', ok))
    cases.append(('precedent_time.py stamps the person\'s zone over TZ and the '
                  'repo fallback', probe[:1] == [BA]))
    cases.append(('declared_identity() carries the person\'s zone under a '
                  'name/email override', probe[1:2] == [BA]))
    tz, refused, ok, probe = run(declare_zone=False)
    cases.append(('control: with no personal zone the repo fallback applies',
                  tz == NY and probe[:1] == [NY]))
    cases.append(('and nothing is refused over a zone nobody declared',
                  not refused))
    failed = [c for c, ok_ in cases if not ok_]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_identity_reaches_a_repo_that_did_not_exist_yet():
    """The commit identity covers repos ATTACHED AFTER the hook ran.

    Three wrong-author incidents in two days, each "fixed", each recurring,
    because every fix was aimed at the wrong scope. A SessionStart hook
    configures the checkouts that exist when it fires. A repository attached
    mid-turn with `add_repo`, cloned, or `git init`ed during the session was
    never seen by that pass -- and inherits the container's GLOBAL identity,
    which is the agent bot account. The per-checkout fix cannot cover it even
    in principle, and no amount of care in the session can either: the third
    incident happened to a session that had already written two documents
    about the first two.

    Measured rather than reasoned about, 2026-09-07: `git config --global
    user.email` read `noreply@anthropic.com`, and a repository created
    seconds later committed as `Claude <noreply@anthropic.com>`.

    So the identity is set GLOBALLY, and a backstop is installed at
    `core.hooksPath`, which is the one hook location that reaches a
    repository that does not exist yet.

    THE TWO CASES THAT MUST NOT FIRE are what make it safe. `core.hooksPath`
    makes git look there AND NOWHERE ELSE, so a global hooks directory
    silently disables every repository's own `.git/hooks/*` -- a worse bug
    than the one being fixed. Each hook therefore chains to the repository's
    own hook of the same name first. And a merely INFERRED identity is never
    written globally: a guess in global config follows the user into every
    unrelated repository on the machine.

    practice: control-asserts-which-failure. The chaining case caught its own
    fixture: it planted the "repository's own" hook via
    `rev-parse --git-path hooks`, which RESPECTS core.hooksPath, so with the
    backstop installed it wrote into the global directory and the test failed
    against a working chain. `--absolute-git-dir` is the resolution that
    means what it says.
    """
    import tempfile
    script = ROOT / 'tools' / 'commit-identity.sh'
    if not script.exists():
        not_applicable('the commit identity reaches a later-attached repo',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        home = tmp / 'home'
        home.mkdir()
        env = dict(os.environ)
        env['HOME'] = str(home)
        # Its `git config --global` must land in this HOME: an inherited
        # GIT_CONFIG_GLOBAL would send it elsewhere -- on 2026-10-31, to
        # /dev/null, which it replaced.
        env.pop('GIT_CONFIG_GLOBAL', None)
        env['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
        env.pop('PRECEDENT_ALLOW_ANY_AUTHOR', None)
        env.pop('PRECEDENT_COMMIT_EMAIL', None)
        env.pop('PRECEDENT_COMMIT_TZ', None)
        env.pop('CCR_SESSION_ACCOUNT_EMAIL', None)
        # The GitHub lookup is pinned to a fixture, never the network: under
        # a proxy that injects credentials the real call succeeds and names
        # the real person, which would decide the "guessed" case below for
        # whoever happens to run the harness (practice: fixture-owns-its-state).
        env['PRECEDENT_GITHUB_USER_URL'] = (tmp / 'no-such-github.json').as_uri()
        ZONE = 'America/Argentina/Buenos_Aires'

        def g(*a, cwd=None):
            return subprocess.run(['git'] + list(a), capture_output=True,
                                  text=True, env=env,
                                  cwd=str(cwd) if cwd else None, timeout=120)

        # The container's starting condition, reproduced.
        g('config', '--global', 'user.name', 'Claude')
        g('config', '--global', 'user.email', 'noreply@anthropic.com')

        src = tmp / 'individual'
        src.mkdir()
        g('init', '-q', str(src))
        (src / 'identity.json').write_text(
            '{"name":"Morgan F","email":"m@example.com","timezone":"%s"}' % ZONE,
            encoding='utf-8')
        r = subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(src)), timeout=180)
        first = r.stderr

        cases = [
            ('the global identity stops being the bot',
             g('config', '--global', 'user.email').stdout.strip() == 'm@example.com'),
            ('and the displacement is announced',
             'GLOBAL git identity was the container' in first),
        ]

        # THE REGRESSION: a repository that did not exist when the hook ran.
        later = tmp / 'attached-later'
        later.mkdir()
        g('init', '-q', str(later))
        (later / 'f').write_text('x', encoding='utf-8')
        g('add', 'f', cwd=later)
        subprocess.run(['git', 'commit', '-q', '-m', 'later'], cwd=str(later),
                       capture_output=True, text=True,
                       env=dict(env, TZ=ZONE), timeout=120)
        cases.append(('a repo created AFTER the hook commits as the person',
                      g('log', '-1', '--format=%ae', cwd=later).stdout.strip()
                      == 'm@example.com'))

        # The backstop still refuses if something overrides identity anyway.
        g('config', 'user.email', 'noreply@anthropic.com', cwd=later)
        (later / 'g').write_text('y', encoding='utf-8')
        g('add', 'g', cwd=later)
        r = subprocess.run(['git', 'commit', '-m', 'bot'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        out = r.stdout + r.stderr
        cases.append(('a bot-authored commit is refused there',
                      "container's own agent account" in out))
        cases.append(('and the refusal names itself as the global backstop',
                      'GLOBAL backstop' in out))
        # 2026-10-07: the refusal also fixes the repository, so the same
        # commit run again goes through as the person -- no git config line
        # to copy out of the message by hand.
        cases.append(('the refusal writes the person into that repository\'s '
                      'own config, and says so',
                      g('config', '--local', 'user.email', cwd=later).stdout.strip()
                      == 'm@example.com' and 'Run the same commit again' in out))
        r = subprocess.run(['git', 'commit', '-q', '-m', 'bot-again'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        cases.append(('and the same commit, run again, lands as the person',
                      r.returncode == 0 and g('log', '-1', '--format=%ae', cwd=later)
                      .stdout.strip() == 'm@example.com'))

        # THE PERSON'S ZONE, IN EVERY REPO THEY COMMIT TO (Morgan,
        # 2026-09-25, evening: "I meant the repo timezone to be a fallback,
        # in case there is no defined individual timezone defined"). That
        # morning this case had been flipped to let the attached repo take
        # any offset, and the same day a session wrote -0400 commits into
        # the individual source with nothing refusing them. Back to the
        # original assertion: refused here too.
        g('config', 'user.email', 'm@example.com', cwd=later)
        r = subprocess.run(['git', 'commit', '-m', 'tz'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ='UTC'), timeout=120)
        cases.append(("a wrong-offset commit is refused in a repo that is "
                      "not the person's individual source too",
                      'declared timezone' in (r.stdout + r.stderr)))
        g('config', 'user.name', 'Morgan F', cwd=src)
        g('config', 'user.email', 'm@example.com', cwd=src)
        (src / 'z').write_text('z', encoding='utf-8')
        g('add', 'z', cwd=src)
        r = subprocess.run(['git', 'commit', '-m', 'tz'], cwd=str(src),
                           capture_output=True, text=True,
                           env=dict(env, TZ='UTC'), timeout=120)
        cases.append(('the individual source itself still refuses a '
                      'wrong-offset commit', 'declared timezone' in
                      (r.stdout + r.stderr)))
        r = subprocess.run(['git', 'commit', '-q', '-m', 'ok'], cwd=str(src),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        cases.append(('and a correct commit there is not blocked',
                      r.returncode == 0))

        # MUST NOT FIRE 1: a repository's own hook is not disabled.
        own = tmp / 'own-hooks'
        own.mkdir()
        g('init', '-q', str(own))
        hd = pathlib.Path(g('rev-parse', '--absolute-git-dir',
                            cwd=own).stdout.strip()) / 'hooks'
        hd.mkdir(parents=True, exist_ok=True)
        (hd / 'pre-commit').write_text(
            '#!/bin/sh\necho "REPO OWN HOOK RAN" >&2\nexit 1\n', encoding='utf-8')
        (hd / 'pre-commit').chmod(0o755)
        (own / 'f').write_text('z', encoding='utf-8')
        g('add', 'f', cwd=own)
        r = subprocess.run(['git', 'commit', '-m', 'chain'], cwd=str(own),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        out = r.stdout + r.stderr
        cases.append(("a repository's OWN pre-commit hook still runs",
                      'REPO OWN HOOK RAN' in out))
        cases.append(('and its refusal is still honoured',
                      not g('log', '--oneline', cwd=own).stdout.strip()))

        # MUST NOT FIRE 2: a GUESSED identity never reaches global config.
        g('config', '--global', '--unset', 'core.hooksPath')
        g('config', '--global', 'user.email', 'noreply@anthropic.com')
        bare = tmp / 'bare'
        bare.mkdir()
        g('init', '-q', str(bare))
        r = subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(bare)), timeout=180)
        cases.append(('a GUESSED identity is not written globally',
                      g('config', '--global', 'user.email').stdout.strip()
                      == 'noreply@anthropic.com'))
        cases.append(('and the hook still exits 0', r.returncode == 0))

        # THE AUTHENTICATED ACCOUNT (Alex, 2026-09-30: "Or at least have a
        # unique identifier for me"). The GitHub account the session is
        # logged in as, WITH its numeric id, is one person -- not a guess --
        # so it earns the global identity and the global backstop, and a
        # repository attached later commits as that person. It does NOT earn
        # the exact-author refusal: a different author there still passes.
        gh_ok = tmp / 'github-user.json'
        gh_ok.write_text('{"login":"octo","id":42,"name":"Octo Cat"}',
                         encoding='utf-8')
        authd = tmp / 'authd'
        authd.mkdir()
        g('init', '-q', str(authd))
        r = subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(authd),
                                    PRECEDENT_GITHUB_USER_URL=gh_ok.as_uri()),
                           timeout=180)
        cases.append(('an AUTHENTICATED account is written globally',
                      g('config', '--global', 'user.email').stdout.strip()
                      == '42+octo@users.noreply.github.com'))
        # Said in one line, because this rung runs only when no identity.json
        # is on disk, which is when the commit-author check stands down
        # (2026-09-30, agreed with a consumer session).
        cases.append(('and the hook says the identity came from the account, '
                      'not identity.json',
                      'not from identity.json' in r.stderr
                      and '42+octo@users.noreply.github.com' in r.stderr))
        cases.append(('and its global backstop is installed',
                      bool(g('config', '--global', 'core.hooksPath').stdout.strip())))
        other = tmp / 'attached-after-authd'
        other.mkdir()
        g('init', '-q', str(other))
        g('config', 'user.name', 'Someone Else', cwd=other)
        g('config', 'user.email', 'else@example.com', cwd=other)
        (other / 'f').write_text('x', encoding='utf-8')
        g('add', 'f', cwd=other)
        r = subprocess.run(['git', 'commit', '-q', '-m', 'else'], cwd=str(other),
                           capture_output=True, text=True, env=env, timeout=120)
        cases.append(('but a different author is not refused on it',
                      r.returncode == 0))

        # An answer with no numeric id is still a guess.
        g('config', '--global', '--unset', 'core.hooksPath')
        g('config', '--global', 'user.email', 'noreply@anthropic.com')
        gh_noid = tmp / 'github-user-noid.json'
        gh_noid.write_text('{"login":"octo","name":"Octo Cat"}', encoding='utf-8')
        noid = tmp / 'noid'
        noid.mkdir()
        g('init', '-q', str(noid))
        subprocess.run(['bash', str(script)], capture_output=True, text=True,
                       env=dict(env, CLAUDE_PROJECT_DIR=str(noid),
                                PRECEDENT_GITHUB_USER_URL=gh_noid.as_uri()),
                       timeout=180)
        cases.append(('an account answer with no id is not written globally',
                      g('config', '--global', 'user.email').stdout.strip()
                      == 'noreply@anthropic.com'))

    failed = [n for n, ok in cases if not ok]
    check(f'the commit identity reaches a repo attached after the hook ran '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_global_hooks_are_never_downgraded():
    """An engine never replaces the global hooks a newer engine wrote.

    2026-10-10: every repository's session start rewrites the one global
    hooks directory, so the last to start wins, and one with an older
    engine put back the plain pre-push -- the leak gate and the failed-tree
    refusal stopped running on every push. The writer now records
    GLOBAL_HOOKS_VERSION and leaves a newer directory alone.
    """
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / 'home').mkdir()
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        work = tmp / 'work'
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home'),
               'GIT_CONFIG_GLOBAL': str(tmp / 'gitconfig')}
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(work)], env=env,
                       capture_output=True)
        hooks = tmp / 'hooks'
        hooks.mkdir()

        def install():
            return subprocess.run(
                ['bash', str(ROOT / 'tools' / 'commit-identity.sh')],
                capture_output=True, text=True, timeout=120,
                env=dict(env, CLAUDE_PROJECT_DIR=str(work),
                         PRECEDENT_COMMIT_NAME='T', PRECEDENT_COMMIT_EMAIL='t@example.com',
                         PRECEDENT_GLOBAL_HOOKS=str(hooks),
                         PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                         PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
        stamp = hooks / '.precedent-hooks-version'
        (hooks / 'pre-push').write_text('#!/bin/sh\n# a newer engine wrote this\n')
        stamp.write_text('29991231\n')
        r = install()
        cases.append(('THE DISCRIMINATING CASE: a newer engine\'s hooks are left as they are, '
                      'and it says so', 'a newer engine wrote this' in (hooks / 'pre-push').read_text()
                      and 'written by a newer engine' in r.stderr, failure_detail(r.stderr, 400)))
        (hooks / 'pre-push').write_text('#!/bin/sh\n# an older engine wrote this\n')
        stamp.write_text('20200101\n')
        install()
        pp = (hooks / 'pre-push').read_text()
        cases.append(('an older engine\'s hooks are replaced with this one\'s',
                      'an older engine wrote this' not in pp and 'leak gate' in pp, pp[:200]))
        cases.append(('the directory records this engine\'s version',
                      stamp.read_text().strip().isdigit()
                      and int(stamp.read_text()) > 20200101, stamp.read_text()))
        stamp.unlink()
        (hooks / 'pre-push').write_text('#!/bin/sh\n# no stamp at all\n')
        install()
        cases.append(('a directory with no stamp (an engine older than it) is rewritten',
                      'no stamp at all' not in (hooks / 'pre-push').read_text(), ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the global hooks are never downgraded ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_global_pre_push_refuses_a_tree_the_full_sweep_failed():
    """A tree `precedent_check.py --full-sweep` just failed is refused by the
    global pre-push, from any session root.

    2026-10-17: a session rooted in /home/user, above every repository it
    worked in, ran none of their harness hooks. Twice it chained a push
    after a full sweep piped into `tail`, and the push went out over a
    failing sweep. The global pre-push refused a tree the PUSH check had
    failed (check_global_pre_push_refuses_a_tree_the_check_failed); the
    sweep wrote nothing there. Now a failing whole-tree sweep on a clean
    tree writes it down, a passing one clears only its own entry, and the
    hook commit-identity.sh writes does the refusing."""
    import inspect
    import tempfile
    import precedent_check as _pc
    import precedent_push_check as _ppc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home'),
               'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        (tmp / 'home').mkdir()
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        g = lambda cwd, *a, **e: subprocess.run(
            ['git', '-C', str(cwd), *a], capture_output=True, text=True,
            env={**env, **e})
        bare, work = tmp / 'origin.git', tmp / 'work'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        g(tmp, 'init', '-q', '-b', 'main', str(work))
        (work / 'a.md').write_text('a\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base')
        g(work, 'remote', 'add', 'origin', f'file://{bare}')
        g(work, 'push', '-q', 'origin', 'main')
        hooks = tmp / 'hooks'
        subprocess.run(['bash', str(ROOT / 'tools' / 'commit-identity.sh')],
                       capture_output=True, text=True, timeout=120,
                       env=dict(env, CLAUDE_PROJECT_DIR=str(work),
                                PRECEDENT_COMMIT_NAME='T',
                                PRECEDENT_COMMIT_EMAIL='t@example.com',
                                PRECEDENT_GLOBAL_HOOKS=str(hooks),
                                PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                                PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
        g(work, 'config', 'core.hooksPath', str(hooks))
        g(work, 'checkout', '-q', '-b', 'feature')
        (work / 'b.md').write_text('b\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'work', '--no-verify')
        tree = g(work, 'rev-parse', 'HEAD^{tree}').stdout.strip()
        # A new ref each time: a push with nothing to send runs no pre-push.
        pushes = iter(range(100))
        push = lambda: g(work, 'push', 'origin',
                         f'HEAD:refs/heads/feature-{next(pushes)}')
        record = getattr(_pc, 'record_sweep_result', None)
        cases.append(('precedent_check has a sweep recorder, and main() calls '
                      'it under --full-sweep', record is not None
                      and 'record_sweep_result(ROOT' in inspect.getsource(_pc.main),
                      ''))
        if record is None:
            record = lambda *_a: None
        (work / 'a.md').write_text('dirty\n', encoding='utf-8')
        record(work, ['catalogue-carries-stories'])
        g(work, 'checkout', '-q', '--', 'a.md')
        cases.append(('a sweep of uncommitted edits writes nothing: it did not '
                      'judge the committed tree', push().returncode == 0, ''))
        record(work, ['catalogue-carries-stories'])
        p = push()
        cases.append(('THE DISCRIMINATING CASE: a push of the tree the sweep just '
                      'failed is refused, naming the sweep and the practice',
                      p.returncode != 0 and 'full-sweep' in p.stderr
                      and 'catalogue-carries-stories' in p.stderr, failure_detail(p.stderr, 500)))
        record(work, [])
        cases.append(('once a sweep passes on the same tree, it pushes',
                      push().returncode == 0, ''))
        _ppc.note_failed_tree(work, tree, ['doc_lint'])
        record(work, [])
        cases.append(('a passing sweep leaves a push-check failure on the same '
                      'tree for the push check to clear', push().returncode != 0,
                      ''))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the global pre-push refuses a tree the full sweep failed '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_global_pre_push_refuses_a_tree_the_check_failed():
    """A tree the push check last failed is refused by the global pre-push.

    2026-10-10: a session rooted in one repository worked in another as an
    attached clone. That repository's harness hooks never loaded, its push
    gate among them, and a push went through right after
    precedent_push_check printed "FAILED -- changed_practice ... do not push
    past it". The check now writes the failed tree down in the git
    directory, and the global pre-push hook (every repository, any
    harness) refuses that tree until a pass clears it. The fixture runs the
    real push check with stub checks, and the hook commit-identity.sh
    writes.
    """
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home'),
               'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        (tmp / 'home').mkdir()
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        g = lambda cwd, *a, **e: subprocess.run(
            ['git', '-C', str(cwd), *a], capture_output=True, text=True,
            env={**env, **e})
        bare, work = tmp / 'origin.git', tmp / 'work'
        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        g(tmp, 'init', '-q', '-b', 'main', str(work))
        (work / 'tools').mkdir()
        for f in ('precedent_push_check.py', 'precedent_branches.py',
                  'precedent_merge_check.py'):
            shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'consumer'}), encoding='utf-8')
        for t in ('precedent_check', 'leak_gate', 'doc_lint'):
            (work / 'tools' / f'{t}.py').write_text(
                'import pathlib, sys\n'
                + ('print("precedent_check: 3 passed, 0 violated")\n'
                   if t == 'precedent_check' else '')
                + f'sys.exit(1 if pathlib.Path("FAIL").exists() and "{t}" == "doc_lint" else 0)\n',
                encoding='utf-8')
        (work / '.gitignore').write_text('FAIL\n__pycache__/\n', encoding='utf-8')
        (work / 'a.md').write_text('a\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base')
        g(work, 'remote', 'add', 'origin', f'file://{bare}')
        g(work, 'push', '-q', 'origin', 'main')
        hooks = tmp / 'hooks'
        subprocess.run(['bash', str(ROOT / 'tools' / 'commit-identity.sh')],
                       capture_output=True, text=True, timeout=120,
                       env=dict(env, CLAUDE_PROJECT_DIR=str(work),
                                PRECEDENT_COMMIT_NAME='T',
                                PRECEDENT_COMMIT_EMAIL='t@example.com',
                                PRECEDENT_GLOBAL_HOOKS=str(hooks),
                                PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                                PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
        g(work, 'config', 'core.hooksPath', str(hooks))
        g(work, 'checkout', '-q', '-b', 'feature')
        (work / 'b.md').write_text('b\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'work', '--no-verify')
        (work / 'FAIL').write_text('1', encoding='utf-8')
        pc = lambda: subprocess.run([sys.executable, 'tools/precedent_push_check.py'],
                                    cwd=str(work), capture_output=True, text=True,
                                    env=env, timeout=300)
        r = pc()
        cases.append(('the fixture push check really fails',
                      r.returncode != 0 and 'FAILED' in r.stdout, failure_detail(r.stdout, 400)))
        p = g(work, 'push', 'origin', 'HEAD:refs/heads/feature')
        cases.append(('THE DISCRIMINATING CASE: a push of the tree that just '
                      'failed is refused, naming the failed check',
                      p.returncode != 0 and 'precedent_push_check FAILED on exactly '
                      'this tree' in p.stderr and 'doc_lint' in p.stderr
                      and not g(work, 'ls-remote', 'origin', 'feature').stdout.strip(),
                      failure_detail(p.stderr, 500)))
        # 2026-10-20: the refusal ended by naming its own bypass, handed to
        # a session at the moment it was told no. It names the fix only;
        # the variable is documented for a person to choose.
        cases.append(('the refusal names what to fix, never the variable that '
                      'skips it', 'PRECEDENT_SKIP_' not in p.stderr
                      and 'push once it passes' in p.stderr, failure_detail(p.stderr, 400)))
        p = g(work, 'push', 'origin', 'HEAD:refs/heads/feature',
              PRECEDENT_SKIP_FAILED_TREE='1')
        cases.append(('PRECEDENT_SKIP_FAILED_TREE=1 lets one push through, and says so',
                      p.returncode == 0 and 'SKIPPED' in p.stderr, failure_detail(p.stderr, 400)))
        (work / 'c.md').write_text('c\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'more', '--no-verify')
        p = g(work, 'push', 'origin', 'HEAD:refs/heads/feature')
        cases.append(('a different tree, never checked, is not refused by this',
                      p.returncode == 0, failure_detail(p.stderr, 400)))
        r = pc()
        g(work, 'reset', '-q', '--hard', 'HEAD~1')
        (work / 'FAIL').unlink()
        r = pc()
        p = g(work, 'push', '-f', 'origin', 'HEAD:refs/heads/feature')
        cases.append(('once the same tree passes, it pushes',
                      r.returncode == 0 and p.returncode == 0,
                      failure_detail(r.stdout, 300) + failure_detail(p.stderr, 300)))
        # 2026-10-20: the practice-hook refusal ended by naming the variable
        # that skips it, too. A stub precedent_hooks.py stands in for a
        # practice's pre-push hook that refuses.
        (work / 'tools' / 'precedent_hooks.py').write_text(
            'import sys\nprint("fixture practice: not this push", file=sys.stderr)\n'
            'sys.exit(1)\n', encoding='utf-8')
        (work / 'd.md').write_text('d\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'hooked', '--no-verify')
        p = g(work, 'push', 'origin', 'HEAD:refs/heads/feature')
        cases.append(("a practice hook's refusal names what to do, never the "
                      "variable that skips it",
                      p.returncode != 0 and 'a practice in force here refused it'
                      in p.stderr and 'Do what it says' in p.stderr
                      and 'PRECEDENT_SKIP_' not in p.stderr, failure_detail(p.stderr, 400)))
        p = g(work, 'push', 'origin', 'HEAD:refs/heads/feature',
              PRECEDENT_SKIP_PRACTICE_PUSH_HOOKS='1')
        cases.append(('PRECEDENT_SKIP_PRACTICE_PUSH_HOOKS=1, a person\'s choice, '
                      'still lets one push through and says so',
                      p.returncode == 0 and 'SKIPPED' in p.stderr, failure_detail(p.stderr, 400)))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the global pre-push refuses a tree the push check failed '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))

def check_leak_gate_in_a_worktree_push_reads_its_own_repo():
    """A push from a worktree stands the leak gate down in a private
    repository, as a push from the clone itself does.

    2026-10-11: Booked and Promote compose in a worktree and push from it,
    and git runs the pre-push hook there with GIT_DIR set. The gate then
    asked git for the repository's top from inside tools/, got tools/ back,
    found no precedent.json, never saw that the repository declares itself
    private, and refused two private repositories' landings for naming their
    owner's other private repositories. The fixture uses the real gate and
    the real hook commit-identity.sh writes.
    """
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home'),
               'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        (tmp / 'home').mkdir()
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        g = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a],
                                           capture_output=True, text=True, env=env)
        hooks = tmp / 'hooks'
        for vis in ('private', 'public'):
            bare, work = tmp / f'{vis}.git', tmp / vis
            g(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
            g(tmp, 'init', '-q', '-b', 'main', str(work))
            (work / 'tools').mkdir()
            for f in ('leak_gate.py', 'leak-blocklist.default.txt'):
                shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
            (work / 'precedent.json').write_text(
                json.dumps({'visibility': vis}), encoding='utf-8')
            (work / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
            (work / 'a.md').write_text('a\n', encoding='utf-8')
            g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base', '--no-verify')
            g(work, 'remote', 'add', 'origin', f'file://{bare}')
            g(work, 'push', '-q', '--no-verify', 'origin', 'main')
            if not hooks.is_dir():
                subprocess.run(['bash', str(ROOT / 'tools' / 'commit-identity.sh')],
                               capture_output=True, text=True, timeout=120,
                               env=dict(env, CLAUDE_PROJECT_DIR=str(work),
                                        PRECEDENT_COMMIT_NAME='T',
                                        PRECEDENT_COMMIT_EMAIL='t@example.com',
                                        PRECEDENT_GLOBAL_HOOKS=str(hooks),
                                        PRECEDENT_LOCALTIME=str(tmp / 'lt'),
                                        PRECEDENT_USER_CONFIG='/nonexistent/c.json'))
            g(work, 'config', 'core.hooksPath', str(hooks))
            wt = tmp / f'{vis}-wt'
            g(work, 'worktree', 'add', '-q', '--detach', str(wt), 'main')
            (wt / 'b.md').write_text('what the ' + 'fu' + 'ck\n', encoding='utf-8')
            g(wt, 'add', '-A'); g(wt, 'commit', '-qm', 'a hit', '--no-verify')
            p = g(wt, 'push', 'origin', 'HEAD:refs/heads/main')
            cases.append((vis, p))
        priv, pub = dict(cases)['private'], dict(cases)['public']
        check('the fixture has the global pre-push hook commit-identity.sh writes',
              (hooks / 'pre-push').is_file(), sorted(p.name for p in tmp.iterdir()))
        check('THE DISCRIMINATING CASE: a push from a worktree of a private '
              'repository stands the leak gate down instead of scanning it',
              priv.returncode == 0, failure_detail(priv.stderr, 600))
        check('CONTROL: the same push in a public repository is still refused',
              pub.returncode != 0 and 'leak gate' in pub.stderr.lower(),
              failure_detail(pub.stderr, 400))


def check_date_check_skips_commits_github_made():
    """The commit-date check does not judge a commit GitHub itself committed
    -- its merge button, a squash, or the test merge refs/pull/N/merge the
    merge gate judges -- since GitHub writes those in UTC whoever the author
    is. The person's own commit beside it is still judged, and
    PRECEDENT_CHECK_RANGE narrows what is judged, as in the author check.

    WHY. 2026-10-10, a consumer: the merge gate refused every GitHub-button
    merge, because the test merge carried the person as author and a
    "+0000" date. The same skip already stood in check_session_trailer.py.
    Since 2026-10-10 this is the one copy, the engine's tools/.

    Negative control, measured 2026-10-10: on staging's copy the GitHub
    commit is a finding and the range is ignored."""
    import tempfile
    cases = []
    script = ROOT / 'tools' / 'check_commit_dates.py'
    zone = 'America/Argentina/Buenos_Aires'
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        env = {**_fixture_git_env(), 'PRECEDENT_COMMIT_NAME': 'harness',
               'PRECEDENT_COMMIT_EMAIL': 'harness@example.com',
               'PRECEDENT_COMMIT_TZ': zone, 'PRECEDENT_CHECK_ROOT': str(repo),
               'PRECEDENT_USER_CONFIG': str(repo / 'no-config.json')}
        env.pop('PRECEDENT_CHECK_RANGE', None)
        g = lambda *a, **e: subprocess.run(['git', '-C', str(repo), *a],
                                           env={**env, **e}, capture_output=True,
                                           text=True)
        g('init', '-q', '-b', 'main')
        (repo / 'identity.json').write_text(json.dumps(
            {'name': 'harness', 'email': 'harness@example.com', 'timezone': zone}),
            encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'identity', TZ=zone, GIT_AUTHOR_NAME='harness',
          GIT_AUTHOR_EMAIL='harness@example.com')
        run = lambda **e: subprocess.run([sys.executable, str(script)],
                                         env={**env, **e}, capture_output=True,
                                         text=True)
        r = run()
        cases.append(('CONTROL: the clean fixture passes', r.returncode == 0,
                      failure_detail(r.stdout, 400)))
        (repo / 'm.txt').write_text('m\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'Merge 1234 into 5678', TZ='UTC',
          GIT_AUTHOR_NAME='harness', GIT_AUTHOR_EMAIL='harness@example.com',
          GIT_COMMITTER_NAME='GitHub', GIT_COMMITTER_EMAIL='noreply@github.com')
        r = run()
        cases.append(('a UTC commit GitHub committed is not a finding',
                      r.returncode == 0, failure_detail(r.stdout, 400)))
        (repo / 'p.txt').write_text('p\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'own', TZ='UTC', GIT_AUTHOR_NAME='harness',
          GIT_AUTHOR_EMAIL='harness@example.com')
        own = g('rev-parse', '--short=12', 'HEAD').stdout.strip()
        r = run()
        cases.append(("the person's own UTC commit beside it still is",
                      r.returncode == 1 and f'commit {own}' in r.stdout,
                      failure_detail(r.stdout, 400)))
        r = run(PRECEDENT_CHECK_RANGE='HEAD~2..HEAD~1')
        cases.append(('PRECEDENT_CHECK_RANGE narrows what is judged',
                      r.returncode == 0, failure_detail(r.stdout, 400)))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the commit-date check skips commits GitHub made and honors a range '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_update_takes_an_untouched_install_copy():
    """An install-once file still exactly as an install wrote it -- its
    placeholders filled in, the install's own per-file text put in -- takes
    the current template whole, filled in with the same values; one the
    repository edited is still only read, line by line, and left for you.

    2026-10-17, very deep check: an untouched install from 2026-10-01 could
    not finish an update without seven hand calls, all upstream rewording in
    GETTING_STARTED.md, MAP.md and project-voice.md, because only a template
    copied verbatim was recognised as unedited. Decision (the session's,
    under Morgan's delegation of 2026-10-17): compare each file with the
    template as installed. Planted: a GETTING_STARTED.md template whose
    version 1 names `<project name>` and `<install date>` and whose version
    2 rewords a line and adds one; a MAP.md template carrying the row the
    install replaces; a consumer whose GETTING_STARTED.md was then extended
    in the working tree by an earlier step of the same run; and a copy with
    one line of the repository's own."""
    import contextlib, io, tempfile
    pu, _pve, _pr = _update_tools()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-untouched-copy-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    if not hasattr(pi, 'per_file_substitutions'):
        check('Update Vendors takes an untouched install copy whole, and still '
              'asks about an edited one', False,
              'precedent_install.per_file_substitutions is missing: the install\'s '
              'own per-file text is not one table the update can read')
        return
    row = next(iter(pi.per_file_substitutions(True)['MAP.source.md']))
    gs1 = ('# Getting started with <project name>\n\n'
           'This page was written for <project name> on <install date>.\n'
           'Ask the person who looks after this project before changing it.\n'
           'The old wording that the next template version rewords here.\n')
    gs2 = ('# Getting started with <project name>\n\n'
           'This page was written for <project name> on <install date>.\n'
           'Ask the person who looks after this project before changing it.\n'
           'The new wording that replaced the older sentence in this place.\n'
           'A paragraph upstream added later, which no install has yet.\n')
    map1 = '# Map\n\nThe older wording of the map template sits here.\n' + row + '\n'
    map2 = '# Map\n\nThe current wording of the map template sits here.\n' + row + '\n'
    values = {'<project name>': 'Garden Planner', '<install date>': '2026-10-01'}

    def filled(text, name):
        text = pi._substitute(text, pi.per_file_substitutions(True).get(name, {}))
        return pi._substitute(text, values)

    cases = []
    saved_source = pu.SOURCE
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        (src / 'templates' / 'GETTING_STARTED.md').write_text(gs1, encoding='utf-8')
        (src / 'templates' / 'MAP.md.template').write_text(map1, encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        (src / 'templates' / 'GETTING_STARTED.md').write_text(gs2, encoding='utf-8')
        (src / 'templates' / 'MAP.md.template').write_text(map2, encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v2')
        rev = git(src, 'rev-parse', 'HEAD').stdout.strip()
        pu.SOURCE = src

        def run(build, before=None):
            repo = tmp / f'consumer-{len(cases)}'
            repo.mkdir()
            git(tmp, 'init', '-q', str(repo))
            build(repo)
            rep = pu.Report()
            rep.before = before
            with contextlib.redirect_stdout(io.StringIO()):
                pu.dropped_template_lines_step(repo, rep, rev)
            return repo, rep

        def untouched(repo):
            (repo / 'GETTING_STARTED.md').write_text(filled(gs1, 'GETTING_STARTED.md'),
                                                     encoding='utf-8')
            (repo / 'MAP.md').write_text(filled(map1, 'MAP.source.md'), encoding='utf-8')
        repo, rep = run(untouched)
        cases.append(('an untouched copy with placeholders filled takes the current '
                      'template, filled in with the same values, not left for you',
                      not rep.left and (repo / 'GETTING_STARTED.md').read_text(
                          encoding='utf-8') == filled(gs2, 'GETTING_STARTED.md'),
                      f'{rep.left} {rep.steps}'))
        cases.append(('...and so does one carrying the install\'s own per-file text',
                      (repo / 'MAP.md').read_text(encoding='utf-8')
                      == filled(map2, 'MAP.source.md'), f'{rep.steps}'))
        cases.append(('...said once, naming the files',
                      [o for n, o in rep.steps if n == 'templates taken'] and
                      'GETTING_STARTED.md' in dict(rep.steps).get('templates taken', ''),
                      f'{rep.steps}'))

        def written_ahead(repo):
            untouched(repo)
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'install')
            with (repo / 'GETTING_STARTED.md').open('a', encoding='utf-8') as f:
                f.write('A disclosure an earlier step of this run added.\n')
        repo, rep = run(written_ahead, before=set())
        cases.append(('a file clean when the run started is judged on its committed '
                      'text, so an earlier step\'s addition does not make it edited',
                      not rep.left and (repo / 'GETTING_STARTED.md').read_text(
                          encoding='utf-8') == filled(gs2, 'GETTING_STARTED.md'),
                      f'{rep.left}'))

        def edited(repo):
            untouched(repo)
            with (repo / 'GETTING_STARTED.md').open('a', encoding='utf-8') as f:
                f.write('Our committee reads this page first, every season.\n')
        repo, rep = run(edited)
        left = dict(rep.left)
        cases.append(('a copy with one line of the repository\'s own is never '
                      'written, and its dropped line is still left for you',
                      'GETTING_STARTED.md:5' in left
                      and 'Our committee' in (repo / 'GETTING_STARTED.md').read_text(
                          encoding='utf-8')
                      and 'old wording' in (repo / 'GETTING_STARTED.md').read_text(
                          encoding='utf-8'), f'{rep.left}'))
    except (OSError, ValueError, KeyError, StopIteration) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors takes an untouched install copy whole, and still asks '
          f'about an edited one ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_retired_mentions_match_the_full_path_only():
    """A file is left as still naming a deleted or moved path only when it
    names the whole path, the way rename-updates-links reads it: never by
    its file name alone, and never as the tail of a longer path.

    2026-10-17, a document project's Update Vendors: precedent.json lines
    the same run had repointed to tools/check_commit_author.py, and the
    engine manifest's bare check_commit_author.py at its new home, were left
    as still naming tools/checks/check_commit_author.py, because the scan
    matched the file name. The next run, with no edit, listed none."""
    import tempfile
    pu, _pve, _pr = _update_tools()
    name = 'a mention of a deleted path is the whole path, not its file name'
    if not hasattr(pu, 'retired_mentions'):
        not_applicable(name, 'retired_mentions is absent')
        return
    gone = 'tools/checks/check_commit_author.py'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-full-path-'))
    cases = []
    try:
        files = {
            'repointed.json': '{"run": "python3 tools/check_commit_author.py"}\n',
            'bare.md': 'The check is check_commit_author.py now.\n',
            'longer.md': 'A pack ships process/pack/tools/checks/check_commit_author.py.\n',
            'old.md': f'Run `{gone}` before pushing.\n',
            'relative/doc.md': f'See [it](../{gone}).\n',
        }
        for rel, text in files.items():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text, encoding='utf-8')
        planted = '\n'.join(
            f"WARN: precedent_vendor_engine: {gone} was moved, and {rel}:1 "
            f"still names it -- 'x'. Nothing here refuses."
            for rel in files)
        got = sorted(w for w, _g in pu.retired_mentions(tmp, planted))
        cases.append(('the whole path, and one written with ../ in front, are '
                      'left for the person',
                      'old.md:1' in got and 'relative/doc.md:1' in got, str(got)))
        cases.append(('a line already repointed, a bare file name, and a longer '
                      'path ending in it are not',
                      got == ['old.md:1', 'relative/doc.md:1'], str(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_relayed_authorization_reader():
    """A relayed authorization is actionable only where the PERSON declared
    it (practice: relayed-authorization), and the declaration has to be
    unforgeable by the thing carrying the relay.

    The failure this came from, 2026-09-14: a session relayed a real
    `Go merge` to a session that could reach the repository, three times,
    and was refused every time -- correctly, since a message asserting an
    approval is indistinguishable from a message inventing one. The fix
    moves the evidence into the person's own identity.json, so these cases
    assert the three outcomes SEPARATELY (a declared yes, a declared no,
    and nobody having been asked are three different states with three
    different remedies) and, above all, that the environment cannot
    manufacture the yes."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_identity as pi

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-relay-'))
    cases = []
    saved = {k: os.environ.pop(k) for k in
             ('PRECEDENT_COMMIT_EMAIL', 'PRECEDENT_COMMIT_NAME',
              'PRECEDENT_COMMIT_TZ') if k in os.environ}
    try:
        empty_cfg = tmp / 'no-individual.json'
        empty_cfg.write_text('{"individual": null}', encoding='utf-8')

        def _set(name, **extra):
            d = tmp / name
            d.mkdir()
            body = {'name': 'Fixture Person', 'email': 'fixture@example.com'}
            body.update(extra)
            (d / 'identity.json').write_text(json.dumps(body), encoding='utf-8')
            return d

        yes = _set('accepts', relayed_authorization='accepted')
        got = pi.relayed_authorization(yes, user_config=empty_cfg)
        cases.append(('a declared "accepted" licenses acting on a relay',
                      got['accepted'] is True and got['value'] == 'accepted',
                      str(got)))
        cases.append(('and names the file it read, so a reply can say where '
                      'the permission came from',
                      str(yes) in got['source'], str(got)))

        no = _set('refuses', relayed_authorization='refused')
        got_no = pi.relayed_authorization(no, user_config=empty_cfg)
        cases.append(('a declared "refused" does not',
                      got_no['accepted'] is False and got_no['value'] == 'refused',
                      str(got_no)))

        silent = _set('silent')
        got_silent = pi.relayed_authorization(silent, user_config=empty_cfg)
        cases.append(('an ABSENT field is refused, not accepted -- a person '
                      'who never heard of the field agreed to nothing',
                      got_silent['accepted'] is False and got_silent['value'] == '',
                      str(got_silent)))

        odd = _set('odd', relayed_authorization='yes please')
        cases.append(('and so is any other value -- only the exact string '
                      'counts, so a typo fails closed',
                      pi.relayed_authorization(odd, user_config=empty_cfg)['accepted'] is False,
                      ''))

        shared = tmp / 'shared-consumer'
        shared.mkdir()
        raised = None
        try:
            pi.relayed_authorization(shared, user_config=empty_cfg)
        except pi.NoDeclaredIdentity as e:
            raised = e
        cases.append(('a repo resolving no identity at all raises '
                      'NoDeclaredIdentity -- "nobody was asked" is its own '
                      'outcome, distinct from a declared refusal',
                      raised is not None, 'it returned an answer instead'))
        cases.append(('and the message says what to do instead, rather than '
                      'only that it failed',
                      raised is not None and 'stop at the pull request' in str(raised),
                      str(raised)))

        cfg = tmp / 'user-config.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'fixture-individual', 'path': str(yes)}}), encoding='utf-8')
        cases.append(('a SHARED repo resolves the declaration from the '
                      "person's individual source, which is what makes one "
                      'declaration cover every project they work in',
                      pi.relayed_authorization(shared, user_config=cfg)['accepted'] is True,
                      ''))

        # THE SECURITY CASE. declared_identity() honours PRECEDENT_COMMIT_*;
        # this must not, or the permission is grantable by whatever set the
        # environment rather than by the person.
        os.environ['PRECEDENT_COMMIT_EMAIL'] = 'override@example.com'
        os.environ['PRECEDENT_COMMIT_NAME'] = 'Someone Else'
        try:
            env_raised = False
            try:
                pi.relayed_authorization(shared, user_config=empty_cfg)
            except pi.NoDeclaredIdentity:
                env_raised = True
            cases.append(('PRECEDENT_COMMIT_* cannot manufacture acceptance: '
                          'with the variables set and no identity.json in '
                          'reach, the answer is still "nobody declared this"',
                          env_raised, 'the environment answered for a person'))
            cases.append(('and it cannot flip a declared refusal either',
                          pi.relayed_authorization(no, user_config=empty_cfg)['accepted'] is False,
                          ''))
        finally:
            os.environ.pop('PRECEDENT_COMMIT_EMAIL', None)
            os.environ.pop('PRECEDENT_COMMIT_NAME', None)

        # The CLI is what a receiving session actually runs, so its three
        # exit codes are part of the contract, not an implementation detail.
        for label, home_repo, want_code, want_word in (
                ('accepted -> 0', yes, 0, 'ACCEPTED'),
                ('refused  -> 1', no, 1, 'REFUSED'),
                ('undeclared -> 2', shared, 2, 'UNDECLARED')):
            probe = (
                'import sys, pathlib\n'
                f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
                'import precedent_identity as pi\n'
                f'pi.relayed_authorization.__module__\n'
                'code = 0\n'
                'try:\n'
                f'    r = pi.relayed_authorization({str(home_repo)!r}, user_config={str(empty_cfg)!r})\n'
                '    code = 0 if r["accepted"] else 1\n'
                '    print("ACCEPTED" if r["accepted"] else "REFUSED")\n'
                'except pi.NoDeclaredIdentity:\n'
                '    code = 2\n'
                '    print("UNDECLARED")\n'
                'sys.exit(code)\n')
            out = subprocess.run([sys.executable, '-c', probe],
                                 capture_output=True, text=True)
            cases.append((f'the reader\'s reported outcome and exit code agree '
                          f'({label})',
                          out.returncode == want_code and want_word in out.stdout,
                          f'rc={out.returncode} out={out.stdout.strip()!r}'))

        cli = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_identity.py'),
                              '--relay'], capture_output=True, text=True)
        cases.append(('`precedent_identity.py --relay` runs in this repo and '
                      'names one of the three outcomes',
                      any(w in cli.stdout for w in ('ACCEPTED', 'REFUSED', 'UNDECLARED')),
                      f'rc={cli.returncode} out={cli.stdout.strip()[:120]!r}'))

        skeleton = (ROOT / 'templates' / 'practice-set-individual'
                    / 'identity.json.template').read_text(encoding='utf-8')
        cases.append(('the individual skeleton ships the field, so a set '
                      'created after this is asked the question instead of '
                      'defaulting silently',
                      '"relayed_authorization"' in skeleton, ''))
        cases.append(('and ships it as refused -- the skeleton never hands '
                      'out a standing yes nobody chose',
                      '"relayed_authorization": "refused"' in skeleton, ''))
    finally:
        os.environ.update(saved)
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a relayed authorization is actionable only where the person '
          f'declared it ({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


