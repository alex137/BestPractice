# The harness tests for the engine a consumer vendors
#
# tools/harness/vh_vendor_engine.py -- part of the verification harness:
# the engine a consumer vendors, and installing it.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_practice_set_workflows_converge():
    """A practice set's refresh removes a workflow nobody approved, keeps one
    the person approved, and asks only when genuinely in doubt: a file that
    runs something nothing local runs is held, and the session is told to
    ask keep or delete (2026-10-01). Before, a set "ran its own on purpose"
    and a leftover there was never cleared (Morgan: solve it "in the
    update, not just this file but others"; "Ask if genuinely in doubt")."""
    import contextlib, io, shutil, tempfile, hashlib
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-converge-'))
    cases = [('a practice set\'s CI converges', 'source' in pve.CI_CONVERGES_KINDS, '')]
    try:
        dest = tmp / 'set'
        wfs = dest / '.github' / 'workflows'
        wfs.mkdir(parents=True)
        git = lambda *a: subprocess.run(['git', '-C', str(dest), *a],
                                        capture_output=True, text=True)
        git('init', '-q')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.com')
        left = wfs / 'leftover.yml'
        left.write_text('on: push\njobs:\n  x:\n    runs-on: ubuntu-latest\n'
                        '    steps:\n      - uses: actions/checkout@v4\n', encoding='utf-8')
        kept = wfs / 'button.yml'
        kept.write_text('on: workflow_dispatch\njobs:\n  x:\n    runs-on: ubuntu-latest\n'
                        '    steps:\n      - uses: actions/checkout@v4\n', encoding='utf-8')
        (dest / 'precedent.json').write_text(json.dumps({'github_ci_approved': {
            '.github/workflows/button.yml': {
                'sha256': hashlib.sha256(kept.read_bytes()).hexdigest(),
                'approved_by': 'Dana, 2026-09-25: "keep the button"'}}}), encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'seed\n\nSession: none available (test)')
        pve._LEFT_FOR_YOU.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            removed = pve._remove_unapproved_workflows(dest, {}, 'source', None)
        cases.append(('a set\'s unapproved workflow is removed by the refresh',
                      not left.exists() and '.github/workflows/leftover.yml' in removed,
                      repr(removed)))
        cases.append(('...and one the person approved in their own words is kept '
                      '(their answer, once asked)', kept.exists(), repr(removed)))
        # Genuinely in doubt: it runs something the set's own checks do not.
        # Held, and the session is told to ask (2026-10-01).
        own = wfs / 'own.yml'
        wfs.mkdir(parents=True, exist_ok=True)
        own.write_text('on: push\njobs:\n  x:\n    runs-on: ubuntu-latest\n'
                       '    steps:\n      - run: python3 tools/zz_only_here.py\n',
                       encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'own\n\nSession: none available (test)')
        pve._LEFT_FOR_YOU.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            removed = pve._remove_unapproved_workflows(dest, {}, 'source', None)
        said = ' '.join(str(x) for x in pve._LEFT_FOR_YOU)
        cases.append(('a workflow running something nothing local runs is kept, '
                      'and the session is told to ask the person',
                      own.exists() and 'ASK THE PERSON' in said, said[:300]))
        pve._KEPT_LOUD.clear()
    finally:
        pve._LEFT_FOR_YOU.clear()
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a practice set\'s workflows converge, asking only when in doubt '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_freshness_covers_every_declared_source():
    """precedent_engine_freshness reports one row per way a DECLARED source
    is reached -- the engine manifest, a vendored tree's manifest, a live
    sibling clone -- and says BEHIND for each the moment its upstream
    moves, silence under --quiet while all are current, and NOT VERIFIED
    (never current) for one it cannot reach. Planted end to end
    (practice: checks-plant-their-state): the first version read one
    manifest, so a consumer's second shared set had no freshness check on
    either of its halves and nothing said so (2026-09-23).
    """
    import io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_engine_freshness as pef

    def git(cwd, *args):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def mkupstream(path, seed):
        path.mkdir()
        git(path, 'init', '-q', '-b', 'main')
        git(path, 'config', 'user.email', 'harness@example.com')
        git(path, 'config', 'user.name', 'harness')
        (path / seed).write_text('v1\n', encoding='utf-8')
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'first')
        return git(path, 'rev-parse', 'HEAD')

    def advance(path, seed):
        (path / seed).write_text('v2\n', encoding='utf-8')
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'second')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-freshness-'))
    saved_env = os.environ.get(pef.USER_CONFIG_ENV)
    try:
        # Two upstreams: the engine's origin and one shared set.
        engine_up = tmp / 'engine-upstream'
        set_up = tmp / 'set-upstream'
        engine_tip = mkupstream(engine_up, 'tools_marker.txt')
        set_tip = mkupstream(set_up, 'practices_marker.txt')
        # The consumer: engine manifest, universal manifest, the set's code
        # manifest, the set's live clone beside it, and a repo-local source.
        consumer = tmp / 'consumer'
        (consumer / 'tools').mkdir(parents=True)
        (consumer / 'process').mkdir()
        (consumer / 'local' / 'practices').mkdir(parents=True)
        set_clone = tmp / 'set'
        git(tmp, 'clone', '-q', str(set_up), str(set_clone))
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [
                {'level': 'universal', 'name': 'precedent',
                 'path': 'process/upstream'},
                {'level': 'shared', 'name': 'set', 'path': '../set',
                 'repo': 'set'},
                {'level': 'repo-local', 'name': 'local', 'path': 'local'},
            ]}), encoding='utf-8')
        (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'format_version': 1, 'kind': 'consumer',
            'source_repo': str(engine_up), 'source_branch': 'main',
            'source_commit': engine_tip, 'files': []}), encoding='utf-8')
        (consumer / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': str(engine_up), 'branch': 'main',
                         'commit': engine_tip,
                         'vendored_at': 'process/upstream'}}), encoding='utf-8')
        (consumer / 'process' / 'manifest_set.json').write_text(json.dumps({
            'upstream': {'repo': str(set_up), 'branch': 'main',
                         'commit': set_tip, 'vendored_at': 'process/set'}}),
            encoding='utf-8')
        # No individual set for this planted person.
        os.environ[pef.USER_CONFIG_ENV] = str(tmp / 'no-such-config.json')

        rows = pef.collect_targets(consumer)
        kinds = sorted(r['kind'] for r in rows)

        quiet_before = io.StringIO()
        pef.report(consumer, quiet=True, out=quiet_before)
        full_before = io.StringIO()
        pef.report(consumer, quiet=False, out=full_before)

        advance(engine_up, 'tools_marker.txt')
        advance(set_up, 'practices_marker.txt')
        quiet_after = io.StringIO()
        pef.report(consumer, quiet=True, out=quiet_after)
        after = quiet_after.getvalue()

        # A clone that catches up WHILE the run is going is judged on what it
        # holds when its row is printed (2026-10-06: a consumer's session
        # start called three clones BEHIND that were current minutes later).
        # The stand-in for upstream_tip fast-forwards the live clone as it is
        # asked, after the rows were read -- the race, made deterministic.
        real_tip = pef.upstream_tip

        def tip_and_catch_up(url, branch, clone=None):
            got = real_tip(url, branch, clone=clone)
            if str(url) == str(set_up):
                git(set_clone, 'pull', '-q', '--ff-only')
            return got
        pef.upstream_tip = tip_and_catch_up
        try:
            caught = io.StringIO()
            pef.report(consumer, quiet=True, out=caught)
        finally:
            pef.upstream_tip = real_tip
        caught_up = caught.getvalue()

        # An unreachable source: declared, vendored manifest points nowhere.
        (consumer / 'process' / 'manifest_set.json').write_text(json.dumps({
            'upstream': {'repo': str(tmp / 'gone'), 'branch': 'main',
                         'commit': set_tip, 'vendored_at': 'process/set'}}),
            encoding='utf-8')
        full_unreachable = io.StringIO()
        pef.report(consumer, quiet=False, out=full_unreachable)
        unreachable = full_unreachable.getvalue()

        cases = [
            ('four rows: engine, universal vendored, set vendored, set live '
             '(repo-local skipped)', kinds == ['engine', 'live', 'vendored', 'vendored']),
            ('--quiet says nothing while every source is current',
             quiet_before.getvalue() == ''),
            ('the full run says current for each of the four',
             full_before.getvalue().count('freshness: current --') == 4),
            ('the engine row reads BEHIND once its upstream moves',
             'ENGINE BEHIND UPSTREAM: vendored engine (tools/)' in after),
            ('the universal vendored tree, behind at the same commit, is named '
             'in the engine\'s line: one move, one line (2026-10-10)',
             'ENGINE BEHIND UPSTREAM: vendored engine (tools/) and precedent '
             '(universal) vendored at process/upstream have' in after
             and after.count(str(engine_up)) == 1),
            ('the shared set\'s vendored code reads BEHIND',
             'BEHIND UPSTREAM: set (shared) vendored at process/set' in after),
            ('the shared set\'s live clone reads BEHIND and names the refresh '
             'that brings it current, never a bare pull (engine output a '
             'refresh leaves there makes that pull refuse, 2026-09-30)',
             'BEHIND UPSTREAM: set (shared) live clone at' in after
             and f'--apply --path {set_clone}' in after
             and 'pull --ff-only' not in after),
            ('the notice names Update Vendors once',
             after.count('"Update Vendors"') == 1),
            ('a live clone that caught up while the run went is not called '
             'BEHIND (the control is the BEHIND row above, read without it)',
             'live clone at' not in caught_up
             and 'BEHIND UPSTREAM: set (shared) vendored at process/set' in caught_up),
            ('an unreachable upstream is NOT VERIFIED, not current',
             'NOT VERIFIED -- set (shared) vendored at process/set' in unreachable
             and 'current -- set (shared) vendored' not in unreachable),
        ]
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  freshness did NOT behave as stated: {name}")
        if not ok:
            print('  --- quiet after upstream moved ---')
            print(after)
        check(f'precedent_engine_freshness covers every declared source '
              f'({len(cases)} stated cases)', ok)
    finally:
        if saved_env is None:
            os.environ.pop(pef.USER_CONFIG_ENV, None)
        else:
            os.environ[pef.USER_CONFIG_ENV] = saved_env
        shutil.rmtree(tmp, ignore_errors=True)


def check_commit_rebuild_runs_outside_the_hook_git_env():
    """The commit-time rebuild runs its commands without the git hook's
    GIT_DIR/GIT_INDEX_FILE (2026-10-04). Inside the hook those point every
    git command at the repository being committed, so a rebuild that asks
    another repository's clone a question got this one's answer: a practice
    set's AGENTS.md came out with the person's individual practices inlined,
    and every set's Update Vendors failed its push check on it. Its own
    staging keeps the hook's index."""
    import tempfile, shutil
    name = 'the commit-time rebuild runs outside the git hook environment'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_regenerate as rg
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='regen-hook-env-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
               GIT_CONFIG_GLOBAL=empty_gitconfig())
    for k in ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_PREFIX',
              'GIT_COMMON_DIR'):
        env.pop(k, None)
    hook_vars = ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_PREFIX',
                 'GIT_COMMON_DIR')
    cases = []
    saved = {k: os.environ.get(k) for k in hook_vars}
    try:
        repo, other = tmp / 'repo', tmp / 'other'
        for d in (repo, other):
            subprocess.run(['git', 'init', '-q', str(d)], env=env, check=True)
        (repo / 'src.txt').write_text('x\n', encoding='utf-8')
        cmd = (f'python3 -c "import subprocess,pathlib;pathlib.Path(\'out.txt\')'
               f'.write_text(subprocess.run([\'git\',\'-C\',r\'{other}\','
               f'\'rev-parse\',\'--absolute-git-dir\'],capture_output=True,'
               f'text=True).stdout)"')
        subprocess.run(['git', '-C', str(repo), 'add', 'src.txt'], env=env, check=True)
        # The hook's environment, as git sets it for pre-commit.
        os.environ['GIT_DIR'] = str(repo / '.git')
        os.environ['GIT_INDEX_FILE'] = str(repo / '.git' / 'index')
        staged = rg.regenerate(repo, [{'path': 'out.txt', 'regenerate': cmd,
                                       'inputs': ['src.txt']}], say=lambda m: None)
        got = (repo / 'out.txt').read_text(encoding='utf-8').strip() \
            if (repo / 'out.txt').is_file() else ''
        cases.append(('a rebuild asking ANOTHER repository gets that repository\'s '
                      'answer, not the one being committed',
                      got == str((other / '.git').resolve()), got))
        idx = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--name-only'],
                             env=env, capture_output=True, text=True).stdout.split()
        cases.append(('...and what it rewrote is staged into the commit\'s index',
                      'out.txt' in idx and 'out.txt' in staged, f'{idx} {staged}'))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n} -- {d}' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_sync_does_not_call_a_held_back_check_an_orphan():
    """A sync names as orphaned only a check no practice file claims. A check
    whose own source's practice file names it in `checked_by` -- a rule that
    source keeps out of force on purpose, as a deduplicated copy whose check
    still runs in its own repository -- is not vendored and not reported.
    Reported from a consumer, 2026-10-06: every sync listed the individual
    set's three such checks as orphans."""
    import contextlib, io, tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    cases = []
    with _tf.TemporaryDirectory() as td:
        src = pathlib.Path(td) / 'set'
        (src / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        (src / 'practices').mkdir()
        for stem in ('kept', 'lost'):
            (src / 'tools' / 'checks' / f'check_{stem}.py').write_text('x = 1\n', encoding='utf-8')
            (src / 'tools' / 'checks' / 'tests' / f'test_{stem}.sh').write_text('true\n', encoding='utf-8')
        (src / 'practices' / 'kept.md').write_text(
            '---\nslug: kept\nchecked_by:  tools/checks/check_kept.py\n'
            'status:      deduplicated\n---\n## Rule\nx\n', encoding='utf-8')
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            plan = pm._plan_checks([{'name': 'set', 'path': str(src), 'level': 'shared'}],
                                   {'practices': {}})
        note = [l for l in err.getvalue().splitlines() if 'no practice in force' in l]
        note = note[0] if note else ''
        cases.append(('a check no practice file claims is still reported',
                      'check_lost.py' in note and 'test_lost.sh' in note))
        cases.append(('a check its own source\'s practice file claims is not',
                      'check_kept.py' not in note and 'test_kept.sh' not in note))
        cases.append(('...and neither is vendored here',
                      not any(name in ('check_kept.py', 'check_lost.py')
                              for _r, name, _s, _d in plan)))
    failed = [n for n, ok in cases if not ok]
    check(f'a sync does not call a held-back check an orphan ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_sync_carries_a_test_helper_with_its_test():
    """A set's test may bring one helper of its own: <name>_cases.py beside
    test_<name>.sh travels exactly when that test does, from the same
    source, and is never run as a test itself (2026-10-20). Until then the
    ladder set's cases file reached a consumer through a practice's
    `ships`, for no reason but that a test could carry only its .sh.
    CONTROLS: a helper whose test nothing claims, and one with no test at
    all, stay behind."""
    import contextlib, io, tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    cases = []
    with _tf.TemporaryDirectory() as td:
        src = pathlib.Path(td) / 'set'
        tests = src / 'tools' / 'checks' / 'tests'
        tests.mkdir(parents=True)
        for name in ('test_thing.sh', 'test_lost.sh'):
            (tests / name).write_text('true\n', encoding='utf-8')
        for name in ('thing_cases.py', 'lost_cases.py', 'alone_cases.py'):
            (tests / name).write_text('x = 1\n', encoding='utf-8')
        res = {'practices': {'thing': {'source': 'set', 'fm': {
            'ships': '["tools/thing/thing.py"]'}}}}
        with contextlib.redirect_stderr(io.StringIO()):
            plan = pm._plan_checks([{'name': 'set', 'path': str(src), 'level': 'shared'}], res)
        got = {name for rel, name, _s, _d in plan if rel == 'checks/tests'}
        driver = next((d.decode('utf-8') for rel, name, _s, d in plan
                       if name == pm.RUN_ALL_NAME), '')
        cases.append(('a claimed test brings its helper', 'thing_cases.py' in got
                      and 'test_thing.sh' in got))
        cases.append(('CONTROL: a helper whose test nothing claims stays behind',
                      'lost_cases.py' not in got and 'test_lost.sh' not in got))
        cases.append(('CONTROL: a helper with no test stays behind',
                      'alone_cases.py' not in got))
        cases.append(('the driver never runs a helper as a test',
                      'thing_cases.py' not in driver))
    failed = [n for n, ok in cases if not ok]
    check(f'a sync carries a test\'s helper with its test ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_retired_sets_are_dropped_only_when_nothing_is_lost():
    """Update Vendors and the very deep check drop a declared set that says it
    is retired, or that GitHub reports archived -- and only when every active
    rule it holds is in force in another declared source (Morgan,
    2026-10-06, option C). A set GitHub merely cannot find is never dropped:
    that is also what lost access looks like. Planted on a fixture
    repository with a universal source and three sets."""
    import inspect
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    import precedent_update as _pu
    import very_deep_check as _vdc
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-retired-'))
    cases = []
    # This machine's own person must not decide a case.
    NOBODY = ({}, [])

    def practice(where, slug):
        d = fx / where / 'practices'
        d.mkdir(parents=True, exist_ok=True)
        (d / f'{slug}.md').write_text(f'---\nslug: {slug}\nstatus: active\n---\n',
                                      encoding='utf-8')

    def manifest(where, retired=None):
        data = {'name': where}
        if retired is not None:
            data['retired'] = retired
        (fx / where / 'precedent-source.json').write_text(json.dumps(data),
                                                          encoding='utf-8')
    try:
        (fx / 'repo').mkdir()
        practice('uni', 'kept-rule')
        practice('folded', 'kept-rule')
        practice('orphaning', 'only-here')
        practice('live', 'live-rule')
        manifest('folded', {'date': '2026-10-06', 'folded_into': ['universal']})
        manifest('orphaning', True)
        manifest('live')
        cfg = ('{\n  "format_version": 1,\n  "_note": "kept as written",\n'
               '  "sources": [\n'
               '    {"level": "universal", "name": "uni", "path": "../uni"},\n'
               '    {"level": "shared", "name": "folded", "path": "../folded"},\n'
               '    {"level": "shared", "name": "orphaning", "path": "../orphaning"},\n'
               '    {"level": "shared", "name": "live", "path": "../live"}\n'
               '  ]\n}\n')
        pj = fx / 'repo' / 'precedent.json'
        pj.write_text(cfg, encoding='utf-8')
        dropped, kept = _pve.drop_retired_sources(fx / 'repo', apply=False, person=NOBODY)
        cases.append(('a dry run writes nothing', pj.read_text(encoding='utf-8') == cfg))
        dropped, kept = _pve.drop_retired_sources(fx / 'repo', person=NOBODY)
        names = [s['name'] for s in json.loads(pj.read_text(encoding='utf-8'))['sources']]
        cases.append(('a set that says it is retired, whose rules universal '
                      'carries, is dropped', 'folded' not in names
                      and [d[0] for d in dropped] == ['folded']))
        cases.append(('a retired set holding a rule nothing else carries is '
                      'kept, and the rule is named',
                      'orphaning' in names and kept
                      and kept[0][0] == 'orphaning' and kept[0][3] == ['only-here']))
        cases.append(('a set that says nothing is left alone', 'live' in names))
        cases.append(('the file keeps its own comments and layout',
                      '"_note": "kept as written"' in pj.read_text(encoding='utf-8')))
        practice('uni', 'live-rule')
        dropped, _k = _pve.drop_retired_sources(fx / 'repo', archived={'live'}, person=NOBODY)
        names = [s['name'] for s in json.loads(pj.read_text(encoding='utf-8'))['sources']]
        cases.append(('a set GitHub reports archived is dropped once its rules '
                      'are carried -- here the last entry in the list',
                      'live' not in names and pj.read_text(encoding='utf-8').count('{') == 3))
        # Two retired sets cannot vouch for each other's rule.
        practice('twin-a', 'shared-only')
        practice('twin-b', 'shared-only')
        manifest('twin-a', True)
        manifest('twin-b', True)
        pj2 = fx / 'repo2' / 'precedent.json'
        pj2.parent.mkdir()
        pj2.write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'uni', 'path': '../uni'},
            {'level': 'shared', 'name': 'twin-a', 'path': '../twin-a'},
            {'level': 'shared', 'name': 'twin-b', 'path': '../twin-b'}]}),
            encoding='utf-8')
        d2, k2 = _pve.drop_retired_sources(fx / 'repo2', apply=False, person=NOBODY)
        cases.append(('two retired sets holding the same rule do not vouch for '
                      'each other: both are kept', not d2 and len(k2) == 2))
        cases.append(('archived_declared_sources never turns an unanswered '
                      'question into "archived"',
                      'Not Found' in inspect.getsource(_pve.archived_declared_sources)
                      and "archived.add(name)" in inspect.getsource(
                          _pve.archived_declared_sources)))
        cases.append(('Update Vendors runs the drop', 'retired_sources_step(repo, rep)'
                      in inspect.getsource(_pu.update)))
        cases.append(('the very deep check reports it and writes nothing',
                      'RETIRED SETS' in inspect.getsource(_vdc)
                      and 'ARCHIVED_SOURCES, apply=False' in inspect.getsource(_vdc)))

        # A PERSON'S DELETED SETS (Morgan, 2026-10-08). The person's individual
        # set lists a set as deleted: it is dropped even with no clone left
        # to read, and even holding a rule nothing else carries; and a rule
        # the person's own set carries counts as carried.
        practice('mine', 'carried-by-me')
        practice('carried', 'carried-by-me')
        manifest('carried', True)
        pj3 = fx / 'repo3' / 'precedent.json'
        pj3.parent.mkdir()
        pj3.write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'uni', 'path': '../uni'},
            {'level': 'shared', 'name': 'carried', 'path': '../carried'},
            {'level': 'shared', 'name': 'vanished', 'path': '../vanished'},
            {'level': 'shared', 'name': 'orphaning', 'path': '../orphaning'}]}),
            encoding='utf-8')
        person = ({'vanished': {'date': '2026-10-08',
                                'reason': 'retired; repository being deleted'},
                   'orphaning': {'date': '2026-10-08', 'reason': ''}},
                  [fx / 'mine'])
        d3, k3 = _pve.drop_retired_sources(fx / 'repo3', person=person)
        # It says what the record says, never more (2026-10-10: a consumer
        # was told "its repository is deleted" of two repositories that
        # still answered, because the record said "being deleted").
        why = next((w for n, _p, w in d3 if n == 'vanished'), '')
        cases.append(("a deleted set's reason is the record's own words, not "
                      "a claim that its repository is gone",
                      'repository being deleted' in why
                      and 'repository is deleted' not in why))
        left = [x['name'] for x in json.loads(pj3.read_text(encoding='utf-8'))['sources']]
        cases.append(('a set the person deleted is dropped though its clone '
                      'is gone', 'vanished' not in left))
        cases.append(('...and though it holds a rule nothing else carries -- '
                      'the person said so', 'orphaning' not in left and not k3))
        cases.append(("a retired set whose rule only the person's own set "
                      'carries is dropped', 'carried' not in left))
        cases.append(('universal is never dropped', 'uni' in left))
        # A set declared at the older `team` level is the same set
        # (normalize_level): it is dropped too, not skipped (a consumer's
        # update, 2026-10-09, kept two deleted sets declared as `team`).
        pj5 = fx / 'repo5' / 'precedent.json'
        pj5.parent.mkdir()
        pj5.write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'uni', 'path': '../uni'},
            {'level': 'team', 'name': 'vanished', 'path': '../vanished'}]}),
            encoding='utf-8')
        _pve.drop_retired_sources(fx / 'repo5', person=person)
        left5 = [x['name'] for x in json.loads(pj5.read_text(encoding='utf-8'))['sources']]
        cases.append(('a deleted set declared at the older `team` level is '
                      'dropped too', left5 == ['uni'], left5))
        # Every session stops loading and cloning a deleted set at once.
        import precedent_resolve as _pr
        ind = fx / 'ind'
        ind.mkdir()
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'ind', 'deleted_sets': [{'name': 'vanished', 'date': '2026-10-08'}]}),
            encoding='utf-8')
        ucfg = fx / 'user.json'
        ucfg.write_text(json.dumps({'individual': {'path': str(ind)}}), encoding='utf-8')
        got = _pr.deleted_sets(user_config=ucfg)
        cases.append(("deleted_sets reads the person's list",
                      got.get('vanished', {}).get('from') == 'person', sorted(got)))
        cases.append(("...and BestPractice's own record, for every person",
                      all(got.get(n, {}).get('from') == 'engine' for n in
                          ('precedent-shared-repo-maintenance',
                           'precedent-shared-working-style')), sorted(got)))
        (fx / 'repo4').mkdir()
        (fx / 'repo4' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'vanished', 'path': '../vanished'},
            {'level': 'shared', 'name': 'live', 'path': '../live'}]}), encoding='utf-8')
        names = [n for _p, _l, n, _note in _pr.declared_source_paths(fx / 'repo4', ucfg)]
        cases.append(('the freshness guard no longer checks a deleted set',
                      'vanished' not in names and 'live' in names, names))
        loaded = [x['name'] for x in _pr.load_config(fx / 'repo4', user_config=str(ucfg))]
        cases.append(('a session no longer loads a deleted set',
                      'vanished' not in loaded, loaded))
        # An individual set's `brings` loses a deleted set at its Update
        # Vendors; anywhere else, the person is told their own set names it.
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'ind', 'brings': [
                {'name': 'precedent-shared-working-style', 'repo_url': 'https://github.com/o/a'},
                {'name': 'kept', 'repo_url': 'https://github.com/o/b'}]}), encoding='utf-8')
        saved_env = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        try:
            told = _pve.person_names_deleted(fx / 'repo4')
            cases.append(("an update elsewhere names the deleted set the person's "
                          'own individual set still brings',
                          [n for _w, n in told] == ['precedent-shared-working-style'], told))
            cases.append(('...and says nothing when run in that individual set itself',
                          _pve.person_names_deleted(ind) == []))
        finally:
            if saved_env is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_env
        dropped_b = _pve.drop_deleted_brings(ind)
        left_b = [b['name'] for b in json.loads(
            (ind / 'precedent-source.json').read_text(encoding='utf-8'))['brings']]
        cases.append(("Update Vendors in an individual set drops a deleted set "
                      'from its brings, and keeps the rest',
                      dropped_b == ['precedent-shared-working-style'] and left_b == ['kept'],
                      (dropped_b, left_b)))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [c[0] + (f' ({c[2]})' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a retired or archived set is dropped only when no rule is lost '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))
def check_install_records_the_commit_its_catalogue_came_from():
    """A fresh install writes CATALOGUE_SYNC.json naming the commit its
    practice catalogue was copied from, exactly when that is true.

    WHY. Only Update Vendors wrote it. A fresh install had none, so every
    session start said "freshness: NOT VERIFIED", the freshness tool said
    the catalogue's practices were "absent this session" while 180 sat on
    disk, and the first update judged local edits against no commit at all
    (very deep check, 2026-10-11, pass 1)."""
    import tempfile as _tf
    import precedent_install as _pi
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain',
                            '--', 'practices', 'precedent-source.json'],
                           capture_output=True, text=True).stdout.strip()
    with _tf.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        n = _pi._vendor_catalogue(dest)
        rec = dest / _pi.UNIVERSAL_PATH / 'CATALOGUE_SYNC.json'
        got = json.loads(rec.read_text()) if rec.is_file() else None
    if dirty:
        cases = [('a catalogue copied from uncommitted practices records no '
                  'commit it did not come from', got is None)]
    else:
        cases = [('the copy is there', n > 0),
                 ('its record names the commit it was copied from',
                  (got or {}).get('source_commit') == head)]
    failed = [c for c, ok in cases if not ok]
    check(f'an install records where its catalogue came from ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed) + f' -- {got}')


def check_install_names_the_other_assistants_adapters():
    """The installer wires the Claude Code adapter only, and a Codex or
    Gemini CLI adopter was never told to add theirs: SETUP.md asked which
    assistant would work in the repository and no later step used the
    answer, and INSTALL.md's adapter step spelled out Claude Code alone
    (very deep check, 2026-10-05, pass 1). The installer's report now names
    the adapters page, and both guides say what to add for each."""
    import shutil as _sh
    import tempfile as _tf
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-adapters-'))
    cases = []
    try:
        # The shared fresh install (_fresh_install_fixture), copied, not rerun.
        _rc, stdout, _err = _fresh_install_fixture(fx)
        tail = stdout.split('DONE.', 1)[-1]
        cases.append(("the install report's what-is-left names the adapters "
                      "page for another assistant",
                      'templates/harness/README.md' in tail
                      and 'Codex' in tail and 'Gemini CLI' in tail))
        setup = (ROOT / 'SETUP.md').read_text(encoding='utf-8')
        conv = setup.split('## The Conversation', 1)[-1]
        after = conv.split('python3 tools/precedent_install.py', 1)[-1]
        cases.append(('SETUP.md uses the which-assistant answer after the '
                      'install command', 'templates/harness/README.md' in after
                      and 'Codex' in after))
        inst = (ROOT / 'INSTALL.md').read_text(encoding='utf-8')
        cases.append(("INSTALL.md's adapter step covers Codex and Gemini CLI",
                      'templates/harness/codex/hooks.json' in inst
                      and '.codex/hooks.json' in inst
                      and 'templates/harness/gemini-cli/GEMINI.md' in inst
                      and '.gemini/settings.json' in inst))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'an adopter on another assistant is told to add its adapter '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_a_source_set_ships_no_ci_workflow():
    """A practice source installs no CI workflow, and an existing set loses
    the ones it has on its next refresh.

    Morgan, 2026-09-21 (strength: decided), reading his own usage export:
    127 of 143 billed minutes that day -- 89% -- came from four practice
    sets running two workflows each, while twelve consuming repos cost 16
    minutes between them. practice: source-sets-run-no-ci.

    THE EMPTINESS IS THE MECHANISM, and that is what needs asserting.
    `_remove_retired_ci_workflow_files` sweeps whatever a kind no longer
    ships, but ONLY for a kind it recognises -- so `source` being PRESENT
    and EMPTY propagates the deletion, while deleting the key would stop
    the sweep and leave every installed workflow in place forever. The two
    cases are one character apart in the source and opposite in effect.
    """
    import precedent_vendor_engine as pve

    cases = []
    src = pve.CI_WORKFLOW_TEMPLATES.get('source', None)
    cases.append(('a source ships no CI workflow', src == (), repr(src)))
    cases.append(('`source` is still a RECOGNISED kind, so the sweep runs '
                  '(an absent key would silently strand every installed '
                  'workflow)', 'source' in pve.CI_WORKFLOW_TEMPLATES,
                  str(sorted(pve.CI_WORKFLOW_TEMPLATES))))

    # A CONSUMER IS NOT A SOURCE. It keeps its leak gate, because a fork's
    # pushes never fire `push` in the receiving repository -- the one case
    # a single-owner set does not have.
    con = {installed for _t, installed in
           pve.CI_WORKFLOW_TEMPLATES.get('consumer', ())}
    cases.append(('a consumer still ships its leak gate',
                  '.github/workflows/leak-gate.yml' in con, str(sorted(con))))

    # And the sweep itself: a manifest tracking both old workflows, under
    # kind `source`, must mark both superseded.
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-nocisrc-'))
    try:
        repo = tmp / 'repo'
        (repo / 'tools').mkdir(parents=True)
        (repo / '.github' / 'workflows').mkdir(parents=True)
        old = ['.github/workflows/precedent-check.yml',
               '.github/workflows/leak-gate.yml']
        hashes = {}
        for rel in old:
            (repo / rel).write_text('name: old\n', encoding='utf-8')
            hashes[rel] = pve._sha256(repo / rel)
        manifest = {'kind': 'source', 'ci_workflow_files': old,
                    'ci_workflows_sha256': hashes}
        (repo / 'tools' / pve.MANIFEST_NAME).write_text(
            json.dumps(manifest), encoding='utf-8')
        dropped = pve._remove_retired_ci_workflow_files(repo, manifest, 'source')
        cases.append(('refreshing a SOURCE drops both tracked workflows',
                      set(dropped) == set(old), str(sorted(dropped))))
        cases.append(('and deletes them from disk',
                      not any((repo / r).exists() for r in old),
                      str([r for r in old if (repo / r).exists()])))

        # The guard that must NOT sweep: an unrecognised kind.
        repo2 = tmp / 'repo2'
        (repo2 / 'tools').mkdir(parents=True)
        (repo2 / '.github' / 'workflows').mkdir(parents=True)
        for rel in old:
            (repo2 / rel).write_text('name: old\n', encoding='utf-8')
        m2 = {'kind': 'a-future-kind', 'ci_workflow_files': old,
              'ci_workflows_sha256': hashes}
        (repo2 / 'tools' / pve.MANIFEST_NAME).write_text(
            json.dumps(m2), encoding='utf-8')
        pve._remove_retired_ci_workflow_files(repo2, m2, 'a-future-kind')
        cases.append(('an UNRECOGNISED kind sweeps nothing -- a typo in '
                      'somebody else\'s manifest must not delete their CI',
                      all((repo2 / r).exists() for r in old),
                      str([r for r in old if not (repo2 / r).exists()])))

        # THE ONE EXCEPTION (2026-10-28): a PUBLIC source gets the branch
        # cleanup workflow, so the branch cleanup page can show its button.
        # It runs only on a click, and a public repository is not billed.
        cleanup = '.github/workflows/precedent-branch-cleanup.yml'
        src = ROOT / 'templates' / 'github-actions'
        for name, vis in (('pub', 'public'), ('priv', 'private'), ('undeclared', None)):
            r = tmp / name
            (r / 'tools').mkdir(parents=True)
            if vis:
                (r / 'precedent.json').write_text(json.dumps({'visibility': vis}),
                                                  encoding='utf-8')
            m = {'kind': 'source'}
            (r / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps(m), encoding='utf-8')
            pve._refresh_ci_workflow_files(r, 'source', src, m)
        pub, priv, und = tmp / 'pub', tmp / 'priv', tmp / 'undeclared'
        ships = [rel for _t, rel in pve.ci_workflow_templates('source', pub)]
        cases.append(('a PUBLIC source ships the cleanup workflow and nothing else',
                      ships == [cleanup], str(ships)))
        cases.append(('a refresh writes it into a public source that has no '
                      'workflow at all', (pub / cleanup).is_file(), ''))
        cases.append(('...and records it, so no later check calls it unapproved',
                      cleanup in json.loads((pub / 'tools' / pve.MANIFEST_NAME)
                                            .read_text(encoding='utf-8'))
                      .get('ci_workflows_sha256', {}), ''))
        cases.append(('CONTROL: a private source ships none, and gets none',
                      pve.ci_workflow_templates('source', priv) == ()
                      and not (priv / '.github').exists(), ''))
        cases.append(('CONTROL: an undeclared visibility counts as private',
                      pve.ci_workflow_templates('source', und) == ()
                      and not (und / '.github').exists(), ''))
        # A set that goes private loses the copy on its next refresh.
        m = json.loads((pub / 'tools' / pve.MANIFEST_NAME).read_text(encoding='utf-8'))
        kept = pve._remove_retired_ci_workflow_files(pub, dict(m), 'source')
        cases.append(('while public, the sweep keeps it', not kept
                      and (pub / cleanup).is_file(), str(kept)))
        (pub / 'precedent.json').write_text(json.dumps({'visibility': 'private'}),
                                            encoding='utf-8')
        gone = pve._remove_retired_ci_workflow_files(pub, dict(m), 'source')
        cases.append(('once private, the sweep deletes it', gone == [cleanup]
                      and not (pub / cleanup).exists(), str(gone)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_refresh_repoints_a_retired_catalogue_pin():
    """The engine refresh moves a consumer's catalogue pin off a retired
    branch by itself, so no session has to hand-edit the file that says
    which upstream branch the repo tracks.

    2026-09-27: a consumer update stopped with the engine on main and
    process/manifest.json still on precedent-beta-v01. The edit that finishes
    the update was held by Claude Code's permission check, and the person was
    asked to re-make the 2026-09-25 decision (practice:
    vendor-update-runbook, step 1). Every install on an old pin stops there.

    The negative controls carry the weight: a pin to any other branch is
    somebody's choice, and a manifest vendoring something other than
    BestPractice has its own branch names -- neither may be touched.
    """
    import inspect, tempfile
    import precedent_vendor_engine as pve

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-catalogue-pin-'))

    def repo_with(name, upstream):
        repo = tmp / name
        (repo / 'process').mkdir(parents=True)
        (repo / 'process' / 'manifest.json').write_text(json.dumps(
            {'upstream': upstream, 'entries': []}, indent=2) + '\n',
            encoding='utf-8')
        return repo

    def pin(repo):
        return json.loads((repo / 'process' / 'manifest.json').read_text(
            encoding='utf-8'))['upstream']['branch']

    try:
        # Named here, not read from pve: an emptied list must fail this.
        for old in ('precedent-beta-v01', 'staging'):
            repo = repo_with(old, {'repo': 'https://github.com/alex137/BestPractice.git',
                                   'branch': old, 'commit': 'abc123'})
            wrote = pve.repoint_catalogue_pin(repo)
            m = json.loads((repo / 'process' / 'manifest.json').read_text(
                encoding='utf-8'))
            cases.append((f'a catalogue pinned to {old!r} is repointed to '
                          f'{pve.SOURCE_BRANCH!r}, nothing else in the '
                          f'manifest changes',
                          wrote is not None and pin(repo) == pve.SOURCE_BRANCH
                          and m['upstream']['commit'] == 'abc123'
                          and m['entries'] == [], json.dumps(m)))
            cases.append((f'a second run on the repointed {old!r} manifest '
                          f'writes nothing',
                          pve.repoint_catalogue_pin(repo) is None, pin(repo)))

        other = repo_with('other-branch', {'repo': 'https://github.com/alex137/BestPractice',
                                           'branch': 'some-feature'})
        cases.append(('a pin to any other branch is left alone',
                      pve.repoint_catalogue_pin(other) is None
                      and pin(other) == 'some-feature', pin(other)))

        foreign = repo_with('foreign', {'repo': 'https://github.com/someone/their-pack',
                                        'branch': 'staging'})
        cases.append(('`staging` in a manifest vendoring something other than '
                      'BestPractice is left alone',
                      pve.repoint_catalogue_pin(foreign) is None
                      and pin(foreign) == 'staging', pin(foreign)))

        cases.append(('a repo with no process/manifest.json is a no-op',
                      pve.repoint_catalogue_pin(tmp / 'nothing-here') is None, ''))

        # The call has to sit before refresh()'s already-current early exit:
        # the half-finished update this closes has an engine that is already
        # current, so a call placed only on the write path never runs there.
        src = inspect.getsource(pve.refresh)
        call, early = (src.find('repoint_catalogue_pin(ROOT)'),
                       src.find('already current with'))
        cases.append(('refresh() repoints before its already-current early exit',
                      -1 < call < early, f'call at {call}, early exit at {early}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_upstream_branch_declaration_is_followed():
    """A consuming repo may follow `staging` instead of main by declaring
    `"upstream_branch": "staging"` in its precedent.json (2026-10-05); one
    that declares nothing, or a value off the list, follows SOURCE_BRANCH.

    Asserted end to end where it lands: followed_branch() itself, the
    catalogue pin moving to the declared branch and back again when the
    declaration goes, and the engine manifest recording the branch the
    repo follows. The negative controls are a value off the list
    ('nightly'), deliberately not followable, and a pin to a feature branch,
    which stays somebody's own choice under either declaration.
    """
    import tempfile
    import precedent_vendor_engine as pve

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-upstream-branch-'))

    def repo_with(name, declared=None, pin=None):
        repo = tmp / name
        (repo / 'process').mkdir(parents=True)
        (repo / 'tools').mkdir()
        decl = {} if declared is None else {'upstream_branch': declared}
        (repo / 'precedent.json').write_text(json.dumps(decl) + '\n',
                                             encoding='utf-8')
        if pin is not None:
            (repo / 'process' / 'manifest.json').write_text(json.dumps(
                {'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                              'branch': pin, 'commit': 'abc123'},
                 'entries': []}, indent=2) + '\n', encoding='utf-8')
        return repo

    def pin(repo):
        return json.loads((repo / 'process' / 'manifest.json').read_text(
            encoding='utf-8'))['upstream']['branch']

    def declare(repo, value):
        decl = {} if value is None else {'upstream_branch': value}
        (repo / 'precedent.json').write_text(json.dumps(decl) + '\n',
                                             encoding='utf-8')

    try:
        plain = repo_with('plain')
        cases.append(('a repo that declares nothing follows main',
                      pve.followed_branch(plain) == 'main'
                      and pve.upstream_branch_problem(plain) is None,
                      pve.followed_branch(plain)))
        st = repo_with('staging', 'staging')
        cases.append(('a repo declaring staging follows staging',
                      pve.followed_branch(st) == 'staging'
                      and pve.upstream_branch_problem(st) is None,
                      pve.followed_branch(st)))
        pre = repo_with('pre', 'nightly')
        cases.append(('a value off the list is not followable: main, and the problem is said',
                      pve.followed_branch(pre) == 'main'
                      and 'nightly' in (pve.upstream_branch_problem(pre) or ''),
                      str(pve.upstream_branch_problem(pre))))
        cases.append(('a repo with no precedent.json follows main',
                      pve.followed_branch(tmp / 'nothing-here') == 'main', ''))

        moving = repo_with('moving', 'staging', pin='main')
        wrote = pve.repoint_catalogue_pin(moving)
        cases.append(('declaring staging moves a main catalogue pin to staging',
                      wrote is not None and pin(moving) == 'staging', pin(moving)))
        cases.append(('a second run writes nothing',
                      pve.repoint_catalogue_pin(moving) is None, pin(moving)))
        declare(moving, None)
        wrote = pve.repoint_catalogue_pin(moving)
        cases.append(('removing the declaration moves the pin back to main',
                      wrote is not None and pin(moving) == 'main', pin(moving)))

        feature = repo_with('feature', 'staging', pin='some-feature')
        cases.append(('a feature-branch pin is left alone under a staging declaration',
                      pve.repoint_catalogue_pin(feature) is None
                      and pin(feature) == 'some-feature', pin(feature)))

        engine = pathlib.Path(pve.__file__).resolve().parent
        out = repo_with('engine', 'staging')
        pve._write_engine_files(out / 'tools', engine, 'abc123',
                                kind=pve.DEFAULT_KIND)
        recorded = json.loads((out / 'tools' / pve.MANIFEST_NAME).read_text(
            encoding='utf-8')).get('source_branch')
        cases.append(('the engine manifest records the branch the repo follows',
                      recorded == 'staging', str(recorded)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))

def check_update_vendors_resolves_hook_and_engine_path_edits():
    """The resolution covers every file the engine manifest records a hash
    for, not only tools/: a hook it vendored into .claude/hooks/ and a path
    precedent.json declares under engine_paths -- the same drift and the
    same refusal before 2026-09-29. (Raised by the parallel session that
    built the same resolution; CI workflows stay out, per
    ci-workflow-approved.) The hook case is a real install
    (precedent_install.py), which records its hooks by hash; hooks a
    source's adapter writes are that source's, and not the engine's to
    resolve.

    Negative control, measured 2026-09-29: with engine_edits() reading only
    _local_drift, as it did the first day, both edits stop the refresh
    ("hand-edited since the last seed/refresh") and neither case passes."""
    fx = _LocalEditsFixture('precedent-local-edits-hooks-')
    cases = []
    try:
        # A declared engine path.
        repo = fx.consumer('paths', {'engine_paths': {'SETUP.md': 'docs/SETUP.md'}})
        seeded = fx.seeded_from(repo)
        fx.update(repo, seeded)             # writes and records the path
        fx.commit(repo, 'declared path installed')
        s = repo / 'docs' / 'SETUP.md'
        sb = s.read_bytes() if s.is_file() else b''
        s.write_bytes(_insert(sb, 'A line this repo added.\n', at=2))
        fx.commit(repo, 'a local fix to a declared path')
        rc, out = fx.update(repo, fx.upstream(seeded, {
            'SETUP.md': sb + b'\nUpstream added this line.\n'}))
        sn = s.read_bytes()
        # Since 2026-10-08 (Morgan, decided) upstream's version is the
        # default: taken, with the rest of the edit shown for the session.
        pref = _section(out, PREFERRED_GROUP)
        cases.append(('a committed edit to a path declared under engine_paths is '
                      'resolved, not refused: upstream\'s version taken, the rest '
                      'of the edit shown', bool(sb)
                      and 'hand-edited since the last seed' not in out
                      and b'A line this repo added.' not in sn
                      and b'Upstream added this line.' in sn
                      and 'docs/SETUP.md' in pref
                      and '+A line this repo added.' in pref,
                      failure_detail(pref or out, 2000)))

        # A hook, in a real install.
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
        m = json.loads((proj / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
        hook = next((n for n in sorted(m.get('hooks_sha256') or {})
                     if n.endswith('.sh')), None)
        cases.append(('the install records a hook by hash', bool(hook),
                      sorted(m.get('hooks_sha256') or {})))
        if hook:
            h = proj / '.claude' / 'hooks' / hook
            hb = h.read_bytes()
            h.write_bytes(_insert(hb, '# a local fix to this hook\n'))
            fx.commit(proj, 'a local fix to a hook')
            rc, out = fx.update(proj, fx.upstream(m['source_commit'], {
                f'templates/harness/claude-code/hooks/{hook}': hb + b'\n# upstream: hook\n'}))
            hn = h.read_bytes()
            pref = _section(out, PREFERRED_GROUP)
            cases.append(('a committed edit to a vendored hook is resolved, not '
                          'refused: upstream\'s version taken, the rest shown',
                          'hand-edited since the last seed' not in out
                          and b'# a local fix to this hook' not in hn
                          and b'# upstream: hook' in hn
                          and f'.claude/hooks/{hook}' in pref
                          and '+# a local fix to this hook' in pref,
                          failure_detail(pref or out, 2000)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_engine_fetch_reaches_main_in_a_single_branch_clone():
    """The engine refresh finds origin/main in a source clone taken with
    `git clone --single-branch --branch precedent-beta-v01`.

    A bare `git fetch origin main` there writes only FETCH_HEAD, because the
    clone's refspec covers the one branch it was cloned at, and the second
    refresh pass failed "has no main (neither origin/main nor a local branch
    of that name)" (2026-09-28, a consumer). Built from a local origin; no
    network."""
    import tempfile
    _pu, pve, _pr = _update_tools()
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-single-branch-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(*a):
        return subprocess.run(['git', *a], env=env, capture_output=True,
                              text=True, check=True).stdout.strip()
    got = None
    try:
        o = tmp / 'origin'
        git('init', '-q', '-b', 'precedent-beta-v01', str(o))
        (o / 'README').write_text('beta\n')
        git('-C', str(o), 'add', '-A')
        git('-C', str(o), 'commit', '-qm', 'beta')
        git('-C', str(o), 'checkout', '-qb', pve.SOURCE_BRANCH)
        (o / 'tools').mkdir()
        (o / 'tools' / pve.HERE.name).write_text('# the vendoring tool\n')
        git('-C', str(o), 'add', '-A')
        git('-C', str(o), 'commit', '-qm', 'main')
        main = git('-C', str(o), 'rev-parse', 'HEAD')
        c = tmp / 'clone'
        git('clone', '-q', '--depth', '1', '--single-branch', '--branch',
            'precedent-beta-v01', o.as_uri(), str(c))
        cases.append(('the fixture is a single-branch clone with no origin/main',
                      subprocess.run(['git', '-C', str(c), 'rev-parse', '--verify', '-q',
                                      f'origin/{pve.SOURCE_BRANCH}'], env=env,
                                     capture_output=True).returncode != 0))
        import io, contextlib
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                got, engine_dir = pve._source_tools_at(c, fetch=True)
            shutil.rmtree(engine_dir, ignore_errors=True)
        except SystemExit:
            got = None
        cases.append(('the refresh fetch lands origin/main and reads it', got == main))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('the engine refresh fetch reaches main in a single-branch source clone',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_leaves_mentions_of_a_deleted_file():
    """Every file that still names something the engine refresh deleted is
    put on Update Vendors' Left for you.

    2026-09-28, a consumer: the refresh deleted a retired
    bestpractice-docs.yml and only WARNed about a doc still naming it; the
    quick check passed and the full check refused on
    rename-updates-links at the Promote. The WARN is produced by the
    engine's own function, so the two cannot drift apart; a mention inside
    the vendored tree, and one already gone by report time, are not left."""
    import io, contextlib, tempfile
    pu, pve, _pr = _update_tools()
    mentions = getattr(pu, 'retired_mentions', None)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-mentions-'))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    try:
        wf = '.github/workflows/bestpractice-docs.yml'
        (tmp / 'docs').mkdir()
        (tmp / 'docs' / 'CI.md').write_text('# CI\n\nDocs build in `' + wf + '`.\n')
        (tmp / 'docs' / 'OLD.md').write_text('bestpractice-docs.yml ran here.\n')
        (tmp / 'process' / 'upstream').mkdir(parents=True)
        (tmp / 'process' / 'upstream' / 'STORY.md').write_text(wf + ' was retired.\n')
        subprocess.run(['git', 'init', '-q', str(tmp)], env=env, check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], env=env, check=True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            pve._warn_about_dependents(tmp, [wf], 'retired from this kind\'s CI workflow set')
        (tmp / 'docs' / 'OLD.md').write_text('nothing about it now\n')
        got = mentions(tmp, err.getvalue()) if mentions else None
        cases.append(('a doc still naming the deleted workflow is left, at its line',
                      bool(got) and ('docs/CI.md:3', wf) in got))
        cases.append(('a mention inside the vendored tree, or one gone since, is not',
                      bool(got) and [w for w, _g in got] == ['docs/CI.md:3']))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('Update Vendors leaves each mention of a file the refresh deleted',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_run_all_warns_when_checks_are_uncommitted():
    """The generated run_all.sh says, on a failure, when tools/checks/ has
    uncommitted changes -- and only then.

    A shipped test that clones the repo runs the COMMITTED checks, so
    before an update is committed it pairs new cases with old scripts and
    can fail on nothing (2026-09-28, test_file_header.sh in a consumer).
    Several shipped tests still clone; one note in the one driver every
    consumer generates covers them all. Plants both states."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-run-all-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')
    cases = []
    try:
        r = tmp / 'r'
        t = r / 'tools' / 'checks' / 'tests'
        t.mkdir(parents=True)
        (t / 'run_all.sh').write_text(pm._run_all_script({}), encoding='utf-8')
        (t / 'test_always_fails.sh').write_text('exit 1\n', encoding='utf-8')
        (r / 'tools' / 'checks' / 'check_x.py').write_text('print(1)\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(r)], env=env, check=True)
        subprocess.run(['git', '-C', str(r), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(r), 'commit', '-qm', 'base'], env=env, check=True)
        note = 'tools/checks/ has uncommitted changes'
        clean = subprocess.run(['bash', str(t / 'run_all.sh')], env=env,
                               capture_output=True, text=True).stdout
        (r / 'tools' / 'checks' / 'check_x.py').write_text('print(2)\n', encoding='utf-8')
        dirty = subprocess.run(['bash', str(t / 'run_all.sh')], env=env,
                               capture_output=True, text=True).stdout
        cases.append(('a failure with tools/checks/ uncommitted carries the note',
                      note in dirty))
        cases.append(('a failure with everything committed does not', note not in clean))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_run_all_trusts_only_unchanged_shipped_tests():
    """The generated run_all.sh runs only the CHECK, on the repo, for a
    shipped test whose test and check both still match what was shipped --
    and the full self-test for everything else.

    Its source already ran an unchanged self-test before shipping, so in a
    consumer it re-tested code nobody there touched: about 7 minutes of
    every Update Vendors and every merge in one consumer (2026-10-06).
    Plants the shapes that must NOT be trusted -- an edited test, an edited
    check, a repo-local test, the override -- with a self-test that marks a
    file when it runs, and a failing check that must still fail the run."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-run-all-trust-'))
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
    env.pop('PRECEDENT_RUN_ALL_SELF_TESTS', None)
    cases = []
    try:
        src = tmp / 'team'
        (src / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        (src / 'tools' / 'checks' / 'check_ok.py').write_text(
            'print("ok ran")\n', encoding='utf-8')
        (src / 'tools' / 'checks' / 'tests' / 'test_ok.sh').write_text(
            '#!/bin/bash\ntouch "$(dirname "$0")/selftest_ran"\n', encoding='utf-8')
        loc = tmp / 'local-src'
        (loc / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        (loc / 'tools' / 'checks' / 'check_mine.py').write_text('pass\n', encoding='utf-8')
        (loc / 'tools' / 'checks' / 'tests' / 'test_mine.sh').write_text(
            '#!/bin/bash\ntouch "$(dirname "$0")/local_ran"\n', encoding='utf-8')
        sources = [{'name': 'precedent-team-fixture', 'level': 'shared', 'path': str(src)},
                   {'name': 'local', 'level': 'repo-local', 'path': str(loc)}]
        plan = pm._plan_checks(sources, None)
        repo = tmp / 'consumer'
        for rel, fn, _s, data in plan:
            d = repo / 'tools' / rel
            d.mkdir(parents=True, exist_ok=True)
            (d / fn).write_bytes(data)
        tests = repo / 'tools' / 'checks' / 'tests'

        def run(extra=None):
            for m in ('selftest_ran', 'local_ran'):
                (tests / m).unlink(missing_ok=True)
            r = subprocess.run(['bash', 'run_all.sh'], cwd=tests, capture_output=True,
                               text=True, env=dict(env, **(extra or {})))
            return r, (tests / 'selftest_ran').exists(), (tests / 'local_ran').exists()

        r, self_ran, local_ran = run()
        cases.append(('an unchanged shipped test runs its check, not its self-test',
                      r.returncode == 0 and not self_ran and 'ok ran' in r.stdout))
        cases.append(('a repo-local test always runs its self-test', local_ran))
        r, self_ran, _ = run({'PRECEDENT_RUN_ALL_SELF_TESTS': '1'})
        cases.append(('PRECEDENT_RUN_ALL_SELF_TESTS=1 runs the shipped self-test', self_ran))
        (tests / 'test_ok.sh').write_text(
            (tests / 'test_ok.sh').read_text(encoding='utf-8') + '# edited\n', encoding='utf-8')
        r, self_ran, _ = run()
        cases.append(('an edited shipped test runs its self-test', self_ran))
        (tests / 'test_ok.sh').write_bytes(
            next(d for rel, fn, _s, d in plan if fn == 'test_ok.sh'))
        chk = repo / 'tools' / 'checks' / 'check_ok.py'
        chk.write_text('print("edited")\n', encoding='utf-8')
        r, self_ran, _ = run()
        cases.append(('an edited shipped check runs the self-test', self_ran))
        chk.write_bytes(next(d for rel, fn, _s, d in plan if fn == 'check_ok.py'))
        # A finding in the repo: rebuild the plan around a failing check, so
        # its fingerprint matches and only the check runs.
        (src / 'tools' / 'checks' / 'check_ok.py').write_text(
            'import sys\nprint("FINDING here")\nsys.exit(1)\n', encoding='utf-8')
        for rel, fn, _s, data in pm._plan_checks(sources, None):
            (repo / 'tools' / rel / fn).write_bytes(data)
        r, self_ran, _ = run()
        cases.append(("a trusted check's finding fails the run and is named as "
                      "this repo's to fix", r.returncode == 1 and not self_ran
                      and "this repo's to fix" in r.stdout))
    except (OSError, subprocess.CalledProcessError, StopIteration) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_survives_an_upstream_deletion():
    """An update that deletes a vendored .py file upstream dropped ends DONE,
    and the deep check judges the tree the commit will hold.

    2026-09-27, taking main into a real consumer: `checkin.py update` deleted
    tools/precedent_upstream_check.py and tools/upstream_watermark.json from
    process/upstream/, both dropped upstream by 0b5f0d650. The deletions sat
    unstaged, timestamps-carry-offset listed Python files from the index,
    `--cached` still named the deleted one, and the update came back FAILED
    on "could not be parsed" for a file that was gone.

    The fixture is that consumer, built the way a real one is: installed by
    precedent_install.py, with a catalogue vendored at 0b5f0d650's parent, so
    the update has to delete those two files. Two fixes, each asserted on its
    own: the check skips an index path missing from disk, and the update
    stages what it wrote and deleted before the check runs.
    Owns its state (practice: fixture-owns-its-state).

    The update runs with --skip-check, and the one check that failed that
    day runs on its own after it, with the deletion staged and then
    unstaged. The update's full check on this fixture took about 330 of
    the test's 350 seconds here and about 560 on GitHub's runner, the
    slowest check in the suite, while proving nothing the two fixes need
    (Morgan, 2026-10-08: "minor and very very long, so let's fix this
    right now"). Other update checks still run the update's own check.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-deletes-'))
    cases = []
    env = dict(os.environ, HOME=str(tmp / 'home'), PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
               GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='harness@example.com',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='harness@example.com')
    for k in ('CLAUDE_CODE_REMOTE', 'PRECEDENT_LEAK_BLOCKLIST'):
        env.pop(k, None)
    (tmp / 'home').mkdir()

    def sh(*argv, cwd):
        r = subprocess.run(list(argv), cwd=str(cwd), env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    DROPPED = 'process/upstream/tools/precedent_upstream_check.py'
    try:
        rc, before_drop = sh('git', 'rev-parse', '--verify', '-q', '0b5f0d650^', cwd=ROOT)
        before_drop = before_drop.strip()
        cases.append(('this clone has the history the fixture vendors from '
                      '(0b5f0d650^; a shallow clone needs --unshallow)',
                      rc == 0 and bool(before_drop), before_drop))
        if rc != 0:
            raise RuntimeError('no history')
        proj = tmp / 'proj'
        sh('git', 'init', '-q', '-b', 'main', str(proj), cwd=tmp)
        (proj / 'README.md').write_text('# Field Notes\n\nA newsletter about birds.\n',
                                        encoding='utf-8')
        sh('git', 'add', '-A', cwd=proj)
        sh('git', 'commit', '-qm', 'before Precedent', cwd=proj)
        rc, out = sh(sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                     str(proj), '--project-name', 'Field Notes', '--admin', 'dana', cwd=ROOT)
        cases.append(('the fixture installs', rc == 0, failure_detail(out, 800)))
        up = proj / 'process' / 'upstream'
        up.mkdir(parents=True)
        arch = subprocess.run(['git', '-C', str(ROOT), 'archive', before_drop],
                              capture_output=True)
        subprocess.run(['tar', '-x', '-C', str(up)], input=arch.stdout, check=True)
        (proj / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream',
                         'branch': 'precedent-beta-v01', 'commit': before_drop},
            'entries': []}, indent=2) + '\n', encoding='utf-8')
        # A term made fresh each run, never written in this file: the
        # catalogue this fixture vendors includes this very file, so a
        # literal term here is a blocklist hit on its own source once the
        # file reaches the branch the update reads (it did, on main,
        # 2026-09-27), whichever version of the file that branch holds.
        import uuid
        (proj / 'process' / 'scrub_blocklist.txt').write_text(
            f'# terms private to this project\nfieldnotes-{uuid.uuid4().hex}\n',
            encoding='utf-8')
        sh('git', 'add', '-A', cwd=proj)
        sh('git', 'commit', '-qm', 'installed, catalogue vendored', cwd=proj)
        sh('git', 'clone', '-q', '--bare', str(proj), str(tmp / 'origin.git'), cwd=tmp)
        sh('git', 'remote', 'add', 'origin', str(tmp / 'origin.git'), cwd=proj)
        sh('git', 'fetch', '-q', 'origin', cwd=proj)
        cases.append(('the vendored catalogue carries the file upstream later dropped',
                      (proj / DROPPED).is_file(), DROPPED))

        rc, out = sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                     '--repo', str(proj), '--from-ref', _ref_including_worktree(ROOT),
                     '--skip-check', cwd=proj)
        cases.append(('the update that deletes it ends DONE, not FAILED',
                      rc == 0 and 'DONE -- nothing left' in out, failure_detail(out, 2500)))
        cases.append(('...the file is gone from disk', not (proj / DROPPED).exists(), ''))
        _rc, staged = sh('git', 'diff', '--cached', '--name-status', '--', DROPPED, cwd=proj)
        cases.append(('...and its deletion is staged, so the check judges what the '
                      'commit will hold', staged.startswith('D'), staged))
        # The check that failed that day, on the tree as the update left it.
        rc, out = sh(sys.executable, 'tools/precedent_check.py', '--only',
                     'timestamps-carry-offset', cwd=proj)
        cases.append(('timestamps-carry-offset passes on the tree the update staged',
                      rc == 0 and 'could not be parsed' not in out, failure_detail(out, 800)))

        # The check on its own: a file deleted and NOT staged is still in the
        # index, and must not be reported as unparseable. The file is the
        # repo's own, not the dropped one: findings in the mirrored tree
        # process/upstream/ are set aside since then, so a deletion there
        # passed with or without the fix (found 2026-10-08, putting the fix
        # back out and watching this case still pass).
        sh('git', 'reset', '-q', cwd=proj)
        own = proj / 'tools' / 'zz_deleted_fixture.py'
        own.write_text('VALUE = 1\n', encoding='utf-8')
        sh('git', 'add', str(own), cwd=proj)
        sh('git', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'a file to delete',
           '--', str(own), cwd=proj)
        own.unlink()
        rc, out = sh(sys.executable, 'tools/precedent_check.py', '--only',
                     'timestamps-carry-offset', cwd=proj)
        cases.append(('timestamps-carry-offset passes over a deleted, unstaged file '
                      'instead of calling it unparseable',
                      rc == 0 and 'could not be parsed' not in out, failure_detail(out, 800)))
    except RuntimeError:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_converges_consumer_ci():
    """A consumer comes out of Update Vendors with upstream's workflows, and
    nobody is asked.

    2026-09-27, a real consumer: its hand-made light-check.yml ran on every
    push to main and every pull request, re-running checks its local push
    gate already ran. The update left it alone (the light check was written
    at install and never refreshed), and ci-workflow-approved then blocked
    every push with "show the person the file and ask". Morgan (strength:
    decided): "It should definitely definitely use the newer version from
    upstream ... so it shouldn't ask."

    The fixture is that consumer, installed by precedent_install.py, with
    the installed light check replaced by a hand-made one and three more
    workflows: one nobody approved (removed), one the person approved in
    their own words (kept), and one with uncommitted edits (kept, because
    its content exists nowhere else). Then the real one-command update.
    Owns its state (practice: fixture-owns-its-state).
    """
    import hashlib
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-ci-'))
    cases = []
    env = dict(os.environ, HOME=str(tmp / 'home'), PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
               GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='harness@example.com',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='harness@example.com')
    for k in ('CLAUDE_CODE_REMOTE', 'PRECEDENT_LEAK_BLOCKLIST'):
        env.pop(k, None)
    (tmp / 'home').mkdir()

    def sh(*argv, cwd):
        r = subprocess.run(list(argv), cwd=str(cwd), env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    wf = '.github/workflows/'
    LIGHT, EXTRA, KEPT, DIRTY, NEEDED, DECLARED = (
        wf + 'light-check.yml', wf + 'nightly.yml', wf + 'report.yml',
        wf + 'scratch.yml', wf + 'deploy.yml', wf + 'ours.yml')
    template = (ROOT / 'templates' / 'github-actions' /
                'light-check.yml.template').read_bytes()
    hand_made = ('name: Light check\non:\n  push:\n    branches: [main]\n'
                 '  pull_request:\njobs:\n  l:\n    runs-on: ubuntu-latest\n'
                 '    steps:\n      - uses: actions/checkout@v4\n'
                 '      - run: python3 tools/doc_lint.py\n'
                 '      - run: python3 tools/light_check.py\n')
    other = ('name: {}\non:\n  schedule:\n    - cron: "0 3 * * *"\njobs:\n'
             '  j:\n    runs-on: ubuntu-latest\n    steps:\n'
             '      - run: python3 tools/report_things.py\n')
    try:
        proj = tmp / 'proj'
        sh('git', 'init', '-q', '-b', 'main', str(proj), cwd=tmp)
        (proj / 'README.md').write_text('# Field Notes\n\nA newsletter about birds.\n',
                                        encoding='utf-8')
        sh('git', 'add', '-A', cwd=proj)
        sh('git', 'commit', '-qm', 'before Precedent', cwd=proj)
        rc, out = sh(sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                     str(proj), '--project-name', 'Field Notes', '--admin', 'dana',
                     cwd=ROOT)
        cases.append(('the fixture installs', rc == 0, failure_detail(out, 800)))
        # The repo's own light check exists, as in the real consumer, so
        # the local push check runs it.
        (proj / 'tools' / 'light_check.py').write_text(
            'print("ok")\n', encoding='utf-8')
        covered = other.replace('tools/report_things.py', 'tools/doc_lint.py')
        for rel, text in ((LIGHT, hand_made), (EXTRA, covered.format('nightly')),
                          (KEPT, other.format('report')),
                          (DIRTY, covered.format('scratch')),
                          (NEEDED, other.format('deploy')),
                          (DECLARED, covered.format('ours'))):
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_text(text, encoding='utf-8')
        cfg = json.loads((proj / 'precedent.json').read_text(encoding='utf-8'))
        cfg['github_ci_approved'] = {KEPT: {
            'sha256': hashlib.sha256((proj / KEPT).read_bytes()).hexdigest(),
            'approved_by': 'Dana, 2026-09-27: "keep the nightly report"'}}
        # The shape the real consumer was in: its own light check untracked
        # by the manifest, approved the way the old install wrote it.
        # A declaration under local_ci_workflows no longer keeps a
        # consumer's workflow (2026-09-27): only the person's approval does.
        cfg['local_ci_workflows'] = {DECLARED: 'a session said it was ours'}
        cfg['github_ci_approved'][LIGHT] = {
            'sha256': hashlib.sha256((proj / LIGHT).read_bytes()).hexdigest(),
            'approved_by': 'installed by precedent_install.py, 2026-09-25',
            'template': 'light-check.yml.template'}
        (proj / 'precedent.json').write_text(json.dumps(cfg, indent=2) + '\n',
                                             encoding='utf-8')
        mp = proj / 'tools' / 'ENGINE_MANIFEST.json'
        m = json.loads(mp.read_text(encoding='utf-8'))
        for key in ('ci_workflow_files', 'ci_workflows_sha256'):
            m.pop(key, None)
        m['ci_workflow_files'] = [r for r in [wf + 'leak-gate.yml']
                                  if (proj / r).is_file()]
        m['ci_workflows_sha256'] = {
            r: hashlib.sha256((proj / r).read_bytes()).hexdigest()
            for r in m['ci_workflow_files']}
        mp.write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
        sh('git', 'add', '-A', cwd=proj)
        sh('git', 'commit', '-qm', 'installed, with hand-made workflows', cwd=proj)
        (proj / DIRTY).write_text(covered.format('scratch') + '# local edit\n',
                                  encoding='utf-8')
        sh('git', 'clone', '-q', '--bare', str(proj), str(tmp / 'origin.git'), cwd=tmp)
        sh('git', 'remote', 'add', 'origin', str(tmp / 'origin.git'), cwd=proj)
        sh('git', 'fetch', '-q', 'origin', cwd=proj)

        rc, out = sh(sys.executable, str(ROOT / 'tools' / 'precedent_update.py'),
                     '--repo', str(proj), '--from-ref', _ref_including_worktree(ROOT),
                     '--skip-check', cwd=proj)
        cases.append(('the update finishes', rc in (0, 1), failure_detail(out, 2500)))
        cases.append(('the hand-made light check is now upstream\'s template, '
                      'unmodified', (proj / LIGHT).read_bytes() == template,
                      (proj / LIGHT).read_text(encoding='utf-8')[:300]))
        cases.append(('the workflow nobody approved is gone',
                      not (proj / EXTRA).exists(), ''))
        cases.append(('the report says both were done, and that there was '
                      'nothing to ask',
                      'replaced ' + LIGHT in out and 'removed ' + EXTRA in out
                      and 'nothing to ask' in out, failure_detail(out, 2500)))
        cases.append(('...and says what the removed file ran is already in the '
                      'local push check', 'doc_lint.py, which the local push '
                      'check already runs' in out, failure_detail(out, 2500)))
        cases.append(('NEGATIVE: a workflow running a script the local check '
                      'does not run is kept, and the report names the script',
                      (proj / NEEDED).is_file() and 'report_things.py' in out,
                      failure_detail(out, 2500)))
        cases.append(('...under a loud banner saying it was left alone, before '
                      'and after the summary',
                      out.count('GITHUB WORKFLOW LEFT ALONE') >= 2
                      and 'LEFT ALONE: ' + NEEDED in out, failure_detail(out, 2500)))
        todos = sorted((proj / 'todo').glob('todo-*-ci-workflow-left-alone-deploy.md'))
        cases.append(('...and an open to-do item records it',
                      len(todos) == 1 and 'status:            open'
                      in todos[0].read_text(encoding='utf-8')
                      and NEEDED in todos[0].read_text(encoding='utf-8'),
                      str(todos)))
        cases.append(('a workflow declared under local_ci_workflows, running '
                      'only what the local check runs, is removed like any other',
                      not (proj / DECLARED).exists(), failure_detail(out, 2500)))
        cases.append(('NEGATIVE: the workflow the person approved in their own '
                      'words is kept', (proj / KEPT).is_file(), ''))
        cases.append(('NEGATIVE: a workflow with uncommitted edits is kept, '
                      'since its content exists nowhere else',
                      (proj / DIRTY).is_file() and 'local edit' in
                      (proj / DIRTY).read_text(encoding='utf-8'), ''))
        m = json.loads(mp.read_text(encoding='utf-8'))
        cfg = json.loads((proj / 'precedent.json').read_text(encoding='utf-8'))
        cases.append(('the manifest now tracks the light check, and its stale '
                      'install approval is gone',
                      m.get('ci_workflows_sha256', {}).get(LIGHT)
                      == hashlib.sha256(template).hexdigest()
                      and LIGHT not in cfg.get('github_ci_approved', {})
                      and KEPT in cfg.get('github_ci_approved', {}),
                      f"{m.get('ci_workflows_sha256')} {cfg.get('github_ci_approved')}"))
        # Take away the two files the update rightly held back, so only what
        # it did is judged.
        sh('git', 'checkout', '-q', '--', DIRTY, cwd=proj)
        sh('git', 'rm', '-q', '--', DIRTY, NEEDED, cwd=proj)
        rc, out = sh(sys.executable, 'tools/precedent_check.py', '--only',
                     'ci-workflow-approved', cwd=proj)
        cases.append(('ci-workflow-approved passes afterwards, with no question '
                      'for anybody', rc == 0 and '0 violated' in out, failure_detail(out, 1500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_local_workflow_declaration_is_asked_once():
    """A converging repository's local_ci_workflows declaration becomes one
    keep-or-delete question, settled by the person's recorded words, and is
    not repeated after (2026-10-20, Update All Vendors: three private
    consumers were told on every update that the declaration "was not
    honoured; remove it from precedent.json", and nothing recorded a keep).

    1. A declared, unapproved workflow gets the question, naming the flag.
    2. NEGATIVE CONTROL: an answer with no quote is not recorded.
    3. A keep is recorded in github_ci_approved, pinned to the file, and
       the declaration goes.
    4. The next refresh asks nothing.
    5. A declaration beside an approval made by hand is dropped, said once."""
    import precedent_vendor_engine as pve
    import contextlib, io, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-local-wf-'))
    WF = '.github/workflows/own.yml'
    cases = []

    def make(name, cfg):
        repo = tmp / name
        (repo / '.github' / 'workflows').mkdir(parents=True)
        (repo / WF).write_text('name: own\non: push\njobs: {}\n')
        (repo / 'precedent.json').write_text(json.dumps(cfg, indent=2))
        return repo

    def settle(repo):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pve._settle_local_declarations(repo, 'consumer')
        return buf.getvalue()

    def cfg(repo):
        return json.loads((repo / 'precedent.json').read_text())

    try:
        r = make('declared', {'local_ci_workflows': {WF: 'runs our tests'}})
        out = settle(r)
        cases.append(('a declared, unapproved workflow gets the keep-or-delete '
                      'question with the flag',
                      out.startswith(pve.KEEP_WORKFLOW_ASK)
                      and f'--keep-workflow {WF}' in out
                      and 'local_ci_workflows' in cfg(r), out))
        ok, what = pve.record_ci_keep(r, WF, 'Zz, 2026-10-20 said keep')
        cases.append(('NEGATIVE CONTROL: an answer with no quote is not recorded',
                      not ok and 'github_ci_approved' not in cfg(r), what))
        ok, what = pve.record_ci_keep(r, WF, 'Zz, 2026-10-20: "keep it"')
        c = cfg(r)
        cases.append(('a keep is pinned in github_ci_approved and the '
                      'declaration goes',
                      ok and c['github_ci_approved'][WF]['sha256']
                      == pve._sha256(r / WF) and 'local_ci_workflows' not in c,
                      repr(c)))
        out = settle(r)
        cases.append(('the next refresh asks nothing', out == '', out))
        r2 = make('by-hand', {
            'local_ci_workflows': {WF: 'ours'},
            'github_ci_approved': {WF: {
                'sha256': '', 'approved_by': 'Zz, 2026-10-01: "keep"'}}})
        c = cfg(r2)
        c['github_ci_approved'][WF]['sha256'] = pve._sha256(r2 / WF)
        (r2 / 'precedent.json').write_text(json.dumps(c, indent=2))
        out = settle(r2)
        cases.append(('a declaration beside an approval is dropped, said once',
                      'local_ci_workflows' not in cfg(r2)
                      and 'removed the local_ci_workflows declaration' in out
                      and pve.KEEP_WORKFLOW_ASK not in out, out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c for c in cases if not c[1]]
    return (not bad, '; '.join(f'{n}: {d}' for n, _ok, d in bad)
            or f'{len(cases)} cases')


def check_engine_written_leftovers_leave_by_content():
    """A file an engine tool wrote into a consumer at run time, whose tool
    BestPractice has decommissioned, leaves on the next update when its
    content has that tool's shape; one that only shares the name stays.

    2026-10-20, Update All Vendors over 18 repositories: consumers still
    carried tools/others_did_watermark.json, decommissioned upstream on
    2026-10-10, and its header naming the deleted tool stopped their update
    on a rename-updates-links finding. Nothing removed it, because no
    manifest ever recorded a file the engine wrote at run time."""
    import precedent_vendor_engine as pve
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-engine-written-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='harness@example.com',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='harness@example.com')
    MARK = 'tools/others_did_watermark.json'
    stock = json.dumps({'_comment': [
        'What each person was last told about other people\'s commits.',
        'Written by tools/precedent_others_did.py onto the landing branch.'],
        'seen_by': {}}, indent=2) + '\n'
    own = json.dumps({'_comment': ['this repo\'s own file'], 'x': 1}) + '\n'

    def make(name, text, commit=True):
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True)
        (repo / MARK).write_text(text, encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], env=env, check=True)
        if commit:
            subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'b'],
                           env=env, check=True)
        return repo

    # What the source's decommission record says the retired tool left.
    written = [e for e in pve.source_retired_written(ROOT, worktree=True)
               if e[0] == MARK]

    def sweep(repo):
        pve._LEFT_FOR_YOU.clear()
        res = pve.retire_legacy_leftovers(repo, {}, 'consumer', written=written)
        left = [w for i, w in pve._LEFT_FOR_YOU if i == MARK]
        pve._LEFT_FOR_YOU.clear()
        return res, left

    cases = [('the source records what the retired others-did tool left in '
              'consumers', written == [(MARK, 'precedent_others_did.py',
                                        written[0][2] if written else '')],
              repr(written))]
    try:
        r = make('stock', stock)
        res, _left = sweep(r)
        regp = r / 'process' / 'decommissioned_paths.json'
        reg = (json.loads(regp.read_text(encoding='utf-8')) if regp.is_file()
               else {'decommissioned': []})
        cases.append(('the others-did mark the engine wrote is deleted and '
                      'recorded', not (r / MARK).exists() and MARK in res['deleted']
                      and [e['path'] for e in reg['decommissioned']] == [MARK],
                      repr(res)))
        r = make('own', own)
        res, left = sweep(r)
        cases.append(('NEGATIVE: a file with the name but not the shape is '
                      'kept, and said', (r / MARK).is_file() and bool(left)
                      and 'not its content' in left[0], repr(left)))
        r = make('untracked', stock, commit=False)
        res, left = sweep(r)
        cases.append(('NEGATIVE: an untracked copy is kept -- it is the only '
                      'one', (r / MARK).is_file() and bool(left)
                      and 'not tracked by git' in left[0], repr(left)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c for c in cases if not c[1]]
    return (not bad, '; '.join(f'{n}: {d}' for n, _ok, d in bad)
            or f'{len(cases)} cases')


def check_a_consumer_may_declare_a_ci_workflow_its_own():
    """A deliberately diverged CI workflow becomes a declaration, not a fight.

    2026-09-21, from a real Update Vendors pass across four practice sets:
    precedent-individual's precedent-check.yml diverges on purpose (an
    identity fold, and a note about a flag that repo does not want), so
    `refresh` refused -- correctly, since it cannot tell that edit from an
    accident. Both advertised escapes DESTROY the divergence: `--force`
    overwrites it now, and `record-ci` re-baselines the hash so the NEXT
    refresh overwrites it silently, which is worse. The session swapped the
    template in, refreshed, and restored the file by hand: a manoeuvre that
    works once and leaves nothing behind for whoever meets the same wall.

    Four states, and the last two are what keep it honest -- an exemption
    that anyone can take without saying why is an exemption nobody reads
    (practice: control-asserts-which-failure).
    """
    import precedent_vendor_engine as pve
    import tempfile

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-localci-'))
    try:
        repo = tmp / 'repo'
        (repo / '.github' / 'workflows').mkdir(parents=True)
        (repo / 'tools').mkdir()
        rel = '.github/workflows/precedent-check.yml'
        (repo / rel).write_text('name: diverged on purpose\n', encoding='utf-8')
        manifest = {'ci_workflow_files': [rel],
                    'ci_workflows_sha256': {rel: '0' * 64}}
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(manifest), encoding='utf-8')

        def cfg(obj):
            (repo / 'precedent.json').write_text(json.dumps(obj), encoding='utf-8')

        def drift():
            return pve._ci_workflow_drift(repo, manifest)

        cfg({'sources': []})
        cases.append(('with no declaration, a diverged workflow is still drift '
                      '(the refusal that exists today is not weakened)',
                      bool(drift()), str(drift())))

        cfg({'sources': [], 'local_ci_workflows': {rel: 'identity fold'}})
        cases.append(('a declared workflow is not drift', not drift(), str(drift())))
        cases.append(('a declared workflow is not "untracked" either',
                      not pve._untracked_ci_workflow_files(repo, manifest),
                      str(pve._untracked_ci_workflow_files(repo, manifest))))
        cases.append(('the reason is read back, for the report',
                      pve.local_ci_workflows(repo) == {rel: 'identity fold'},
                      str(pve.local_ci_workflows(repo))))

        # A REASON IS REQUIRED. An entry with none is ignored outright --
        # otherwise this is a silent opt-out with extra steps.
        cfg({'sources': [], 'local_ci_workflows': {rel: '   '}})
        cases.append(('an entry with an empty reason is ignored, and the '
                      'refusal stands', bool(drift())
                      and not pve.local_ci_workflows(repo), str(drift())))

        # A CONFIG THAT CANNOT BE READ MUST NOT WAIVE ANYTHING. Failing
        # open here would turn a typo into a silent overwrite.
        (repo / 'precedent.json').write_text('{ not json', encoding='utf-8')
        cases.append(('an unreadable precedent.json waives nothing',
                      bool(drift()) and pve.local_ci_workflows(repo) == {},
                      str(drift())))

        # And the wrong SHAPE is not a declaration either.
        cfg({'sources': [], 'local_ci_workflows': [rel]})
        cases.append(('a bare list is not a declaration -- the shape carries '
                      'the reason', bool(drift()), str(drift())))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_installer_no_terminal_tests_every_push_to_main():
    """An install for an assistant with no terminal (--no-terminal) writes
    precedent.json's "github_ci_main_test": "always", so the light check
    it writes tests every push to main in a private repository too; an
    install without it leaves the template's private-repository skip as it
    is.

    Found 2026-10-17 by the very deep check's install rehearsal: off the
    ladder, a private repository's light check ran on no pull request (its
    `if:` admits only branches Promote named), so an assistant with no
    terminal got no check anywhere, though SETUP.md's fifth question says
    that workflow is the only place a check can run for one. Decision chosen
    by the session under Morgan's delegation of 2026-10-17 ("Fix the other
    issues you found including the checks that never run. Tell me what you
    decide. I will be offline so don't wait for me. Approved, act, and
    Booked."): the existing "always" setting, written by the installer when
    the answers say no terminal.

    Negative control, measured 2026-10-17: on the code before the fix the
    installer refuses --no-terminal as an unknown argument.
    """
    import tempfile
    tool = str(ROOT / 'tools' / 'precedent_install.py')
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-no-terminal-'))
    env = dict(os.environ, PRECEDENT_USER_CONFIG=str(tmp / 'no-config.json'),
               GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    env.pop('PRECEDENT_GITHUB_USER', None)
    try:
        def install(name, *extra):
            proj = tmp / name
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(proj)], capture_output=True)
            (proj / 'README.md').write_text('# Notes\n\nA newsletter.\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(proj), 'add', '-A'], capture_output=True, env=env)
            subprocess.run(['git', '-C', str(proj), 'commit', '-qm', 'before'],
                           capture_output=True, env=env)
            r = subprocess.run([sys.executable, tool, str(proj), '--project-name', 'Notes',
                                '--visibility', 'private', *extra], cwd=str(ROOT),
                               capture_output=True, text=True, env=env)
            cfg = proj / 'precedent.json'
            doc = json.loads(cfg.read_text(encoding='utf-8')) if cfg.is_file() else {}
            wf = proj / '.github' / 'workflows' / 'light-check.yml'
            return r, doc, wf.read_text(encoding='utf-8') if wf.is_file() else ''
        r, doc, wf = install('chatgpt', '--no-terminal')
        cases.append(('--no-terminal installs, writes "always" and says so',
                      r.returncode == 0 and doc.get('github_ci_main_test') == 'always'
                      and "main's GitHub test: always" in r.stdout,
                      failure_detail(r.stdout + r.stderr, 600)))
        cases.append(('...and the light check it writes tests a private push to main',
                      "'main-test:always' == 'main-test:always'" in wf, wf[:200]))
        r, doc, wf = install('claude-code')
        cases.append(('CONTROL: without it, nothing is written and the template keeps its skip',
                      r.returncode == 0 and 'github_ci_main_test' not in doc
                      and "'main-test:individual' == 'main-test:always'" in wf,
                      failure_detail(r.stdout + r.stderr, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_installer_visibility_defaults_to_public_and_says_why():
    """The installer's visibility: --visibility when given, then an existing
    precedent.json, then GitHub's answer for a GitHub origin, and public
    when none of those can be read -- the direction a wrong answer can be
    undone from -- always with the reason.

    Found 2026-10-17 by the very deep check's install rehearsal: an absent
    --visibility silently meant private, which renders private-level sets
    into the tracked AGENTS.md, though precedent.json's own comment says an
    absent key counts as public. Decision chosen by the session under
    Morgan's delegation of 2026-10-17 ("Fix the other issues you found
    including the checks that never run. Tell me what you decide. I will be
    offline so don't wait for me. Approved, act, and Booked.").

    Negative control, measured 2026-10-17: on the code before the fix there
    is no _visibility and main() defaults the flag to 'private'.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
        import github_budget as gb
    finally:
        sys.path.pop(0)
    cases = []
    vis = getattr(pi, '_visibility', None)
    if vis is None:
        return False, '1 stated case', 'precedent_install has no _visibility: an absent flag means private'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-visibility-'))
    real_call = gb.call
    try:
        def repo(name, url=None):
            d = tmp / name
            subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
            if url:
                subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin', url],
                               capture_output=True)
            return d
        got = vis(repo('no-origin'), None)
        cases.append(('no origin: public, and says how to say private',
                      got[0] == 'public' and '--visibility private' in got[1], str(got)))
        got = vis(repo('elsewhere', str(tmp / 'bare.git')), None)
        cases.append(('an origin not on GitHub: public', got[0] == 'public', str(got)))
        got = vis(repo('given'), 'private')
        cases.append(('CONTROL: --visibility private is taken as given', got[0] == 'private', str(got)))
        d = repo('reinstall')
        (d / 'precedent.json').write_text(json.dumps({'visibility': 'private'}), encoding='utf-8')
        got = vis(d, None)
        cases.append(('a --force reinstall keeps what precedent.json declares',
                      got[0] == 'private', str(got)))
        gh = repo('on-github', 'https://github.com/someone/notes.git')
        gb.call = lambda path, **k: ({'private': True}, None) if path == 'repos/someone/notes' else (None, 'x')
        got = vis(gh, None)
        cases.append(("GitHub says private: private, and says it read GitHub",
                      got == ('private', 'read from GitHub: someone/notes is private'), str(got)))
        gb.call = lambda path, **k: (None, 'Not Found')
        got = vis(gh, None)
        cases.append(("GitHub cannot say: public, naming what GitHub answered",
                      got[0] == 'public' and 'Not Found' in got[1], str(got)))
    finally:
        gb.call = real_call
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_update_notes_workflow_changes_in_readme_platform_section():
    """2026-10-19, two consuming repos: Update Vendors changed engine
    workflows, wrote nothing in README.md's "If this repo ever leaves
    GitHub" section, and each repository's own pull-request check (a
    workflow change must touch that section) failed after Produce. The
    refresh now keeps one dated line there naming what it changed."""
    import subprocess as _sp
    import tempfile
    import precedent_vendor_engine as pve
    cases = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        g = lambda *a: _sp.run(['git', *a], cwd=d, capture_output=True, text=True)
        g('init', '-q'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        (d / '.github' / 'workflows').mkdir(parents=True)
        (d / '.github' / 'workflows' / 'light-check.yml').write_text('a\n')
        (d / 'README.md').write_text('# R\n\n## If this repo ever leaves GitHub\n\n'
                                     '- **light-check.yml** -- runs checks.\n\n'
                                     '## Next\n\nText.\n')
        g('add', '-A'); g('commit', '-qm', 'base')
        cases.append(('CONTROL: no workflow changed, README left alone',
                      not pve._note_workflow_changes_in_readme(d, 'abcdef1234', '2026-10-19'),
                      ''))
        (d / '.github' / 'workflows' / 'light-check.yml').write_text('b\n')
        (d / '.github' / 'workflows' / 'precedent-branch-cleanup.yml').write_text('c\n')
        wrote = pve._note_workflow_changes_in_readme(d, 'abcdef1234', '2026-10-19')
        text = (d / 'README.md').read_text()
        cases.append(('a changed and an added workflow are named in the section, '
                      'before the next heading',
                      wrote and text.index('runs checks') < text.index('`light-check.yml`, '
                                                                       '`precedent-branch-cleanup.yml`')
                      < text.index('## Next'), text))
        pve._note_workflow_changes_in_readme(d, '99999999aa', '2026-10-20')
        again = (d / 'README.md').read_text()
        cases.append(('the next refresh replaces its own line, never stacks another',
                      again.count('Changed by Update Vendors') == 1 and '2026-10-20' in again,
                      again))
        (d / 'README.md').write_text('# R\n\nNo such section.\n')
        cases.append(('CONTROL: a README without the section is left alone',
                      not pve._note_workflow_changes_in_readme(d, 'abcdef1234')
                      and (d / 'README.md').read_text() == '# R\n\nNo such section.\n', ''))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'Update Vendors notes its workflow changes in README\'s platform section '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_sync_removes_a_stale_ship_named_only_as_another_repos():
    """2026-10-19: an individual set stopped shipping tools/human_voice_check.py
    once a shared set shipped its own. Three consumers kept the stale copy
    because their docs said "OtherSet's tools/human_voice_check.py" and
    the sync's audit read any mention of the file name as a use of the copy.
    CONTROL: a plain mention still keeps it."""
    import subprocess as _sp
    import tempfile
    import hashlib as _h
    import precedent_materialize as pm
    cases = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        g = lambda *a: _sp.run(['git', '-C', str(d), *a], capture_output=True, text=True)
        g('init', '-q'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        g('remote', 'add', 'origin', 'https://github.com/acme/consumer.git')
        (d / 'tools').mkdir()
        f = d / 'tools' / 'voice_check.py'
        f.write_text('print(1)\n')
        h = _h.sha256(f.read_bytes()).hexdigest()[:16]
        (d / 'README.md').write_text("Copies OtherSet's `tools/voice_check.py` to external/.\n"
                                     'Source (in acme/OtherSet): tools/voice_check.py\n')
        g('add', '-A'); g('commit', '-qm', 'c')
        why = pm._stale_ship_keep_reason(d, 'tools/voice_check.py', h)
        cases.append(('a file named only as another repository\'s may go', why is None, why))
        (d / 'GUIDE.md').write_text('Run `python3 tools/voice_check.py` first.\n')
        g('add', '-A'); g('commit', '-qm', 'c2')
        why = pm._stale_ship_keep_reason(d, 'tools/voice_check.py', h)
        cases.append(('CONTROL: a plain mention still keeps it',
                      bool(why) and 'GUIDE.md' in why, why))
        import qualified_mention as qm
        link = 'See https://github.com/acme/consumer/blob/main/tools/voice_check.py'
        cases.append(('CONTROL: with no origin known, a link into a repository is '
                      'not "another repository\'s"',
                      not qm.mention_names_another_repo(link, 'tools/voice_check.py', None), ''))
    bad = [f'{n}: {x}' for n, ok, x in cases if not ok]
    check(f'the sync removes a stale ship named only as another repository\'s '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_archived_set_question_names_the_attach_fix():
    """When GitHub refuses to say whether a declared set is archived because
    the session has no API access to it, the note is one quiet line that
    asks for no access (2026-10-10: it asked for add_repo with access
    "push", a write grant for a read-only question, and a second consumer
    pushed back). Any other failure keeps its own words.

    THE INCIDENT (2026-10-10, a consumer's Update Vendors). Every run said
    "GitHub could not say whether it is archived (GitHub access to this
    repository is not enabled for this session ...)" and stopped there.
    The DISCRIMINATING CASE is the first. The fixture owns its repositories."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    import github_budget as _gbm
    cases = []
    saved = _gbm.call
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / 'repo'
        clone = pathlib.Path(td) / 'set'
        for d in (root, clone):
            subprocess.run(['git', 'init', '-q', str(d)], capture_output=True,
                           env=_fixture_git_env())
        subprocess.run(['git', '-C', str(clone), 'remote', 'add', 'origin',
                        'https://github.com/example/a-set'], capture_output=True,
                       env=_fixture_git_env())
        (root / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'a-set', 'path': '../set'}]}),
            encoding='utf-8')
        try:
            _gbm.call = lambda path, **_k: (None, 'GitHub access to this '
                                               'repository is not enabled for '
                                               'this session. Use add_repo.')
            _a, notes = pve.archived_declared_sources(root)
            # Changed 2026-10-10, a second consumer: asking for push access
            # to answer a read-only question is too much to ask. One quiet
            # line, no attach advice.
            cases.append(('THE DISCRIMINATING CASE: a not-attached refusal is one '
                          'quiet line that asks for no access',
                          len(notes) == 1 and 'push' not in notes[0]
                          and 'add_repo' not in notes[0]
                          and 'left declared' in notes[0], notes))
            # A public set answers without a login (2026-10-10, a consumer:
            # every run asked for push access to a public set).
            def public(path, auth=True, **_k):
                if auth:
                    return None, ('GitHub access to this repository is not '
                                  'enabled for this session. Use add_repo.')
                return {'full_name': 'example/a-set', 'archived': flag[0]}, None
            for flag in ([False], [True]):
                _gbm.call = public
                a, notes = pve.archived_declared_sources(root)
                cases.append((f'a public set {"archived" if flag[0] else "in use"} is '
                              'answered without a login, with no attach advice',
                              not notes and (a == {'a-set'}) == flag[0], (a, notes)))
            _gbm.call = lambda path, **_k: (None, 'curl exited 6')
            _a, notes = pve.archived_declared_sources(root)
            cases.append(('another failure keeps its own words, with no attach advice',
                          len(notes) == 1 and 'curl exited 6' in notes[0]
                          and 'add_repo' not in notes[0], notes))
            # 2026-10-11: a set on the deleted list was reported in one run
            # as dropped AND as "could not be read (Moved Permanently) ...
            # left declared". A deleted set is dropped without asking.
            import precedent_resolve as _prm
            saved_gone = _prm.deleted_sets
            asked = []
            _gbm.call = lambda path, **_k: (asked.append(path), (None, 'curl exited 6'))[1]
            try:
                _prm.deleted_sets = lambda *_a, **_k: {'a-set': 'deleted'}
                a, notes = pve.archived_declared_sources(root)
            finally:
                _prm.deleted_sets = saved_gone
            cases.append(('a set on the deleted list is not asked about at all',
                          not asked and not notes and not a, (asked, notes)))
            cases.append(('the proxy\'s refusal of a redirect is a proxy refusal',
                          _gbm.is_proxy_refusal('Numeric-ID repository paths '
                                                '(repositories/{id}/...) are not '
                                                'supported through this proxy.'), ''))
        finally:
            _gbm.call = saved
        # A renamed repository answers 301 with the new API address, and
        # call() follows it once (2026-10-11).
        class _R:
            def __init__(self, out):
                self.returncode, self.stdout, self.stderr = 0, out, ''
        seen = []
        def fake_run(argv, **_k):
            seen.append(argv[-1])
            if argv[-1].endswith('repos/example/old-name'):
                return _R(json.dumps({'message': 'Moved Permanently',
                                      'url': _gbm.API + 'repositories/42'}))
            return _R(json.dumps({'full_name': 'example/new-name', 'archived': True}))
        saved_run = _gbm.subprocess.run
        _gbm.subprocess.run = fake_run
        try:
            data, err = _gbm.call('repos/example/old-name', auth=False, cache=False)
        finally:
            _gbm.subprocess.run = saved_run
        cases.append(('a renamed repository\'s "Moved Permanently" is followed to '
                      'the address GitHub names',
                      err is None and isinstance(data, dict) and data.get('archived')
                      and len(seen) == 2, (data, err, seen)))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the archived-set question asks for no access it does not need '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_materialize_carries_harness_adapters():
    """tools/precedent_materialize.py — a practice source's HARNESS ADAPTERS
    travel with it, the way its checks already do.

    Until 2026-09-12 a source's `bootstrap/*.sh` reached a consuming repo's
    `.claude/hooks/` by hand-copy, per each practice's own Install section, so
    a repo carrying a copy went silently behind the moment the source's script
    changed. Measured twice in two days: findings fixed upstream briefed as
    open defects in the source, because they were really about the consuming
    repo's stale copy; and a `commit-identity.sh` about five kilobytes behind
    its source with every local check green.

    Every case here is a behaviour something would silently lose: the file
    lands EXECUTABLE (a hook that is not is a hook the harness never runs),
    it is recorded in MANIFEST.json (an unrecorded file reads as hand-dropped
    to a consumer's own orphan detection), a hand-edit afterwards is a drift()
    finding, a destination collision across sources refuses like a checks/
    one, and `.claude/settings.json` is REFUSED as a destination -- that file
    carries each consumer's own base branch, and copying it would silently
    repoint the freshness guard at the wrong one."""
    import shutil, subprocess, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-adapters-'))
    cases = []
    try:
        uni, team, consumer = tmp / 'universal', tmp / 'team', tmp / 'consumer'
        for root, slug in ((uni, 'uni-fixture'), (team, 'team-fixture')):
            p = root / 'practices' / f'{slug}.md'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
                f'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
                f'gates: []\nindex_clause: "x"\nchecked_by: null\ndefines: []\n'
                f'status: active\nsupersedes: []\noverrides: null\n'
                f'added: 2026-09-02\napproved_by: "harness, 2026-09-02"\n'
                f'source_practice_number: null\n---\n## Rule\nx\n\n'
                f'## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
                encoding='utf-8')
            boot = root / 'bootstrap'
            boot.mkdir(parents=True, exist_ok=True)
            (boot / 'guard.sh').write_text('#!/bin/bash\necho v1\n', encoding='utf-8')
            os.chmod(boot / 'guard.sh', 0o755)

        def declare(root, adapters):
            (root / 'precedent.json').write_text(
                json.dumps({'format_version': 1, 'adapters': adapters}),
                encoding='utf-8')

        declare(uni, [{'from': 'bootstrap/guard.sh',
                       'to': '.claude/hooks/guard.sh'}])
        declare(team, [])
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',  # a team source, run directly (2026-10-17)
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                        {'level': 'team', 'name': 'precedent-team-fixture',
                         'path': str(team)}]}), encoding='utf-8')

        # The fixture owns its HOME for the reason spelled out in
        # check_materialize_bridges_loader(): the resolver otherwise picks up
        # whatever individual source ~/.config/precedent names, and this
        # container's real one would then be declaring adapters into the
        # fixture consumer -- every verdict below would be about that source
        # instead (practices/fixture-owns-its-state.md).
        fixture_home = tmp / 'home'
        fixture_home.mkdir()
        env = {k: v for k, v in os.environ.items()
               if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
        env['HOME'] = str(fixture_home)
        tool = str(ROOT / 'tools' / 'precedent_materialize.py')

        def run():
            r = subprocess.run([sys.executable, tool, '--out', str(consumer),
                                '--repo', str(consumer)],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        installed = consumer / '.claude' / 'hooks' / 'guard.sh'
        rc, out = run()
        cases.append(('a declared harness adapter is installed at its declared '
                      'destination', rc == 0 and installed.is_file()))
        cases.append(('it lands EXECUTABLE -- a hook that is not is a hook the '
                      'harness silently never runs',
                      installed.is_file() and os.access(installed, os.X_OK)))
        # Every read below tolerates the file being absent: a regression in
        # the mechanism under test must report as named FAILING CASES, not as
        # a traceback that takes the whole harness run down before the later
        # refusal cases have even run (control-asserts-which-failure -- a
        # control proves a guard fires by what it SAYS, and a crash says
        # nothing about which of fifteen behaviours broke).
        mf = consumer / 'MANIFEST.json'
        manifest = (json.loads(mf.read_text(encoding='utf-8'))
                    if mf.is_file() else {})
        entry = [a for a in manifest.get('adapters', [])
                 if a.get('path') == '.claude/hooks/guard.sh']
        cases.append(('it is recorded in MANIFEST.json with its source and '
                      'hash, so it is a declared derived artifact rather than '
                      'a file a consumer reads as hand-dropped',
                      len(entry) == 1 and entry[0].get('source') == 'precedent'
                      and bool(entry[0].get('sha256_16'))))
        cases.append(('the fixture really owned its source set -- nothing '
                      'cloned an individual source into the fixture HOME',
                      not any(fixture_home.iterdir())))

        # --- a source that moves reaches the consumer on the next sync -----
        (uni / 'bootstrap' / 'guard.sh').write_text('#!/bin/bash\necho v2\n',
                                                    encoding='utf-8')
        rc, out = run()
        cases.append(('a change in the SOURCE reaches the consumer on the next '
                      'sync -- the whole point: no hand-copy step',
                      rc == 0 and installed.is_file()
                      and 'v2' in installed.read_text(encoding='utf-8')))
        cases.append(('and an ordinary update like that says nothing -- the '
                      'notice is for content this tree never recorded',
                      'REPLACED' not in out))

        # --- a hand-edit afterwards is drift, not silence ------------------
        installed.parent.mkdir(parents=True, exist_ok=True)
        installed.write_text('#!/bin/bash\necho hand edited\n', encoding='utf-8')
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_resolve as _pr, precedent_materialize as _pm
        _home = os.environ.get('HOME')
        try:
            os.environ['HOME'] = str(fixture_home)
            srcs = _pr.load_config(str(consumer), None)
            found = _pm.drift(srcs, _pr.resolve(srcs), consumer)
        finally:
            if _home is not None:
                os.environ['HOME'] = _home
        cases.append(('a hand-edit to an installed adapter is reported by '
                      'drift() -- the audit half, which a mechanism that only '
                      'copies would still owe',
                      any('.claude/hooks/guard.sh differs' in x for x in found)))

        # --- an edit no commit holds is kept, and said so -----------------
        # practice: repair-cannot-discard-work -- this consumer is not a git
        # checkout, so replacing the hand-edit would lose it for good.
        rc, out = run()
        cases.append(('a hand-edit no git commit holds is LEFT UNTOUCHED, '
                      'said so, and the file named',
                      rc == 0 and 'LEFT UNTOUCHED' in out
                      and 'REPLACED' not in out
                      and '.claude/hooks/guard.sh' in out, failure_detail(out, 300)))
        (consumer / '.claude' / 'hooks' / 'guard.sh').unlink()
        rc, out = run()
        cases.append(('deleting it and syncing again installs the source\'s '
                      'copy', rc == 0
                      and (consumer / '.claude' / 'hooks' / 'guard.sh').is_file()
                      and 'LEFT UNTOUCHED' not in out))

        # --- an adapter no source declares any more is reported, not deleted
        declare(uni, [])
        rc, out = run()
        cases.append(('an adapter no declared source publishes any more is '
                      'left in place and REPORTED -- `.claude/hooks/` is not '
                      "materialize()'s to empty, and the file may already be "
                      'wired into a settings.json this tool never reads',
                      rc == 0 and installed.is_file()
                      and 'no declared source publishes any more' in out))

        # --- refusals ------------------------------------------------------
        declare(uni, [{'from': 'bootstrap/guard.sh', 'to': '.claude/hooks/guard.sh'}])
        declare(team, [{'from': 'bootstrap/guard.sh', 'to': '.claude/hooks/guard.sh'}])
        rc, out = run()
        cases.append(('two sources installing to one destination refuses, the '
                      'same discipline a tools/checks/ filename collision gets',
                      rc == 1 and 'collision' in out))

        declare(team, [{'from': 'bootstrap/guard.sh', 'to': '.claude/settings.json'}])
        rc, out = run()
        cases.append(('.claude/settings.json is REFUSED as a destination -- it '
                      "carries each consumer's own base branch, and copying it "
                      'would silently repoint the freshness guard',
                      rc == 1 and 'does not travel' in out))

        declare(team, [{'from': 'bootstrap/guard.sh', 'to': '../escape.sh'}])
        rc, out = run()
        cases.append(('a destination walking out of the consuming repo with '
                      '".." refuses',
                      rc == 1 and 'walks above the consuming repo' in out))

        declare(team, [{'from': 'bootstrap/guard.sh',
                        'to': 'practices/guard.sh'}])
        rc, out = run()
        cases.append(("a destination inside materialize()'s own wiped "
                      'directories refuses -- the file would not survive its '
                      'own sync', rc == 1 and 'deletes and rewrites' in out))

        declare(team, [{'from': 'bootstrap/absent.sh', 'to': '.claude/hooks/absent.sh'}])
        rc, out = run()
        cases.append(('a declared adapter whose file is not in the source tree '
                      'WARNS and is skipped, never refuses -- the ordinary '
                      "cause is a stale clone of a repo the consumer does not "
                      'own',
                      rc == 0 and 'not in the source tree' in out
                      and not (consumer / '.claude' / 'hooks' / 'absent.sh').exists()))

        (team / 'precedent.json').write_text('{ not json', encoding='utf-8')
        rc, out = run()
        cases.append(("a source's unreadable precedent.json refuses rather "
                      'than silently reading as "publishes no adapters"',
                      rc == 1 and 'not readable JSON' in out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [c[0] for c in cases if not c[1]]
    check(f'precedent_materialize.py carries a source\'s harness adapters '
          f'({len(cases)} stated cases: installed executable and recorded in '
          f'the manifest, a source change reaching the consumer with no '
          f'hand-copy, a hand-edit reported by drift(), an edit no commit '
          f'holds kept loudly and an ordinary update quietly, an undeclared one '
          f'reported rather than deleted, and five refusals -- destination '
          f'collision, settings.json, "..", a wiped directory, and an '
          f'unreadable source config)',
          not bad, '; '.join(bad))


def check_sync_keeps_a_hook_whose_stub_has_no_script():
    """tools/precedent_materialize.py -- a sync never swaps a working hook
    for the pointer stub when the script the stub runs is not in the repo.

    2026-10-08: a source's adapters began shipping the stub, which runs
    tools/<its name>. In a consuming repo whose engine predated that move, a
    sync replaced its commit-identity, freshness-guard and individual-set
    hooks with pointers to scripts it did not have, so each printed one note
    and let everything through. A session caught it reading the diff; the
    sync said nothing. Now the working hook stays, the sync says why and
    what to run, --check agrees with what it kept, and once the script
    arrives the next sync installs the stub as an ordinary update."""
    import shutil, subprocess, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-held-hook-'))
    cases = []
    try:
        uni, consumer = tmp / 'universal', tmp / 'consumer'
        p = uni / 'practices' / 'uni-fixture.md'
        p.parent.mkdir(parents=True)
        p.write_text(
            '---\nslug: uni-fixture\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
            'gates: []\nindex_clause: "x"\nchecked_by: null\ndefines: []\n'
            'status: active\nsupersedes: []\noverrides: null\n'
            'added: 2026-10-08\napproved_by: "harness, 2026-10-08"\n'
            'source_practice_number: null\n---\n## Rule\nx\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')
        boot = uni / 'bootstrap'
        boot.mkdir()
        src = boot / 'guard.sh'
        src.write_text('#!/bin/bash\necho real guard\n', encoding='utf-8')
        os.chmod(src, 0o755)
        (uni / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'adapters': [
                {'from': 'bootstrap/guard.sh', 'to': '.claude/hooks/guard.sh'}]}),
            encoding='utf-8')
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(uni)}]}), encoding='utf-8')
        fixture_home = tmp / 'home'
        fixture_home.mkdir()
        env = {k: v for k, v in os.environ.items()
               if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
        env['HOME'] = str(fixture_home)
        tool = str(ROOT / 'tools' / 'precedent_materialize.py')

        def run():
            r = subprocess.run([sys.executable, tool, '--out', str(consumer),
                                '--repo', str(consumer)],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def drift():
            sys.path.insert(0, str(ROOT / 'tools'))
            import precedent_resolve as _pr, precedent_materialize as _pm
            home = os.environ.get('HOME')
            os.environ['HOME'] = str(fixture_home)
            try:
                srcs = _pr.load_config(str(consumer),
                                       str(fixture_home / 'no-user-config.json'))
                return _pm.drift(srcs, _pr.resolve(srcs), consumer)
            finally:
                if home is None:
                    os.environ.pop('HOME', None)
                else:
                    os.environ['HOME'] = home

        hook = consumer / '.claude' / 'hooks' / 'guard.sh'
        rc, out = run()
        stub = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
                / 'reply-gate.sh').read_bytes()
        src.write_bytes(stub)
        rc, out = run()
        text = hook.read_text(encoding='utf-8') if hook.is_file() else ''
        cases.append(('the source now ships the stub and tools/guard.sh is '
                      'missing: the working hook stays',
                      rc == 0 and 'real guard' in text, failure_detail(out, 400)))
        cases.append(('the sync says it kept it, why, and to run Update Vendors',
                      'KEPT' in out and '.claude/hooks/guard.sh' in out
                      and 'Update Vendors' in out, failure_detail(out, 400)))
        cases.append(('it stays executable', hook.is_file()
                      and os.access(hook, os.X_OK), ''))
        found = drift()
        cases.append(('--check agrees with the kept hook: no drift finding',
                      not any('guard.sh' in f for f in found),
                      str([f for f in found if 'guard.sh' in f] or found[:3])))

        (consumer / 'tools').mkdir(exist_ok=True)
        (consumer / 'tools' / 'guard.sh').write_text('#!/bin/bash\n',
                                                      encoding='utf-8')
        rc, out = run()
        text = hook.read_text(encoding='utf-8') if hook.is_file() else ''
        cases.append(('once tools/guard.sh is there, the next sync installs '
                      'the stub, quietly, as an ordinary update',
                      rc == 0 and 'PRECEDENT HOOK STUB' in text
                      and 'KEPT' not in out and 'REPLACED' not in out,
                      failure_detail(out, 400)))

        hook.unlink()
        (consumer / 'tools' / 'guard.sh').unlink()
        rc, out = run()
        cases.append(('with no hook installed there is nothing to lose: the '
                      'stub is written', rc == 0 and hook.is_file()
                      and 'PRECEDENT HOOK STUB' in hook.read_text(encoding='utf-8'),
                      failure_detail(out, 400)))
        # The individual-source stub runs one fixed script whatever name it
        # is installed under, so the kept-or-installed test reads that name
        # from the stub, never from the destination.
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_materialize as _pm
        hooks = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
        ind = (hooks / 'individual-source-bootstrap.sh.template').read_bytes()
        cases.append(('the individual-source stub is judged by the script it '
                      'names, not the name it is installed as',
                      _pm._stub_target(ind, '.claude/hooks/precedent-individual-'
                                       'bootstrap.sh')
                      == 'individual-source-bootstrap.sh'
                      and _pm._stub_target(stub, '.claude/hooks/guard.sh')
                      == 'guard.sh', ''))
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{c[0]} ({c[2]})' for c in cases if not c[1]]
    check(f'a sync keeps a working hook whose new stub has no script to run '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_session_ships_exclude_survives_another_worktree():
    """The session-ships block of info/exclude keeps an entry another work
    tree of the same clone still holds, and drops it once none does.

    2026-10-17, very deep check: info/exclude is shared by every linked
    worktree, and a session file built in a helper's worktree rewrote the
    block with only that worktree's ships. Three shipped tools, one from a
    private repository, went back to untracked in the main checkout, where a
    `git add -A` would have committed them."""
    import tempfile
    import precedent_materialize as pm
    _git = fixture_git
    cases = []
    with tempfile.TemporaryDirectory() as td:
        W = pathlib.Path(td)
        main = W / 'main'
        main.mkdir()
        _git(main, 'init', '-q', '-b', 'main')
        _git(main, 'config', 'user.email', 'harness@example.com')
        _git(main, 'config', 'user.name', 'Harness')
        (main / 'README.md').write_text('x\n')
        _git(main, 'add', '-A'); _git(main, 'commit', '-qm', 'one')
        _git(main, 'worktree', 'add', '-q', str(W / 'side'), '-b', 'side')
        (main / 'tools').mkdir()
        (main / 'tools' / 'private_tool.py').write_text('x = 1\n')
        pm._set_excluded(main, {'tools/private_tool.py'})
        untracked = lambda: _git(main, 'status', '--porcelain',
                                 '--untracked-files=all').stdout
        cases.append(('the main checkout\'s ship is hidden',
                      'private_tool.py' not in untracked()))
        pm._set_excluded(W / 'side', {'tools/other.py'})
        cases.append(('a rewrite from another worktree keeps it hidden',
                      'private_tool.py' not in untracked()))
        (main / 'tools' / 'private_tool.py').unlink()
        pm._set_excluded(W / 'side', {'tools/other.py'})
        ex = pm._exclude_file(main).read_text()
        cases.append(('once no worktree holds the file, its entry goes',
                      '/tools/private_tool.py' not in ex and '/tools/other.py' in ex))
    failed = [n for n, ok in cases if not ok]
    check(f'session-ships exclude survives another worktree ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_refresh_survives_an_upstream_rename():
    """A file removed upstream must not brick every consumer's refresh.

    `refresh` runs the consumer's OWN vendored copy of the vendoring tool,
    and that copy carries the file list it was vendored with. So the first
    refresh after upstream renames or drops an engine file asks git for a
    path that is genuinely gone. That used to be a hard exit:

      precedent_vendor_engine FAIL: precedent-beta-v01 @ <sha> has no
      tools/precedent_retire_path.py

    with no documented way forward -- the fix a consumer needs is inside the
    very file it cannot fetch. The tool's own comments already describe this
    shape for an ADDED file, where it merely stops one file short and the
    second pass converges; for a REMOVED file it was fatal. Reproduced
    2026-09-07 on a real consumer, renaming precedent_retire_path.py ->
    precedent_decommission.py.

    A missing source file is therefore a REMOVAL: skipped with a notice, and
    left out of the manifest rather than recorded as present. The second
    pass then runs the new list, which does not ask for it at all.

    THE ONE FILE THAT STAYS FATAL is the vendoring tool itself. It is what
    carries the corrected list, so without it there is no second pass and
    nothing to converge on -- and a missing one really does mean a broken
    ref rather than a removal. That distinction is the whole point of the
    case below: skipping everything would trade a loud failure for a silent
    one.
    """
    import tempfile, json as _json, shutil as _shutil, importlib
    vend = ROOT / 'tools' / 'precedent_vendor_engine.py'
    if not vend.exists():
        not_applicable('refresh survives an upstream rename',
                       'tools/precedent_vendor_engine.py is not present here')
        return

    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # A throwaway "upstream" whose tools/ is MISSING one file the
        # consumer's list still asks for -- exactly what a rename leaves.
        up = tmp / 'upstream'
        (up / 'tools').mkdir(parents=True)
        _ve = importlib.import_module('precedent_vendor_engine')
        for name in sorted(set(_ve.KINDS['consumer']) | {'routing_scope.json'}):
            if name == 'precedent_show.py':
                continue                      # the "renamed away" file
            src = ROOT / 'tools' / name
            if src.is_file():
                _shutil.copy2(src, up / 'tools' / name)
        subprocess.run(['git', '-C', str(up), 'init', '-q'], capture_output=True)
        for c in (['config', 'user.email', 'h@example.com'],
                  ['config', 'user.name', 'H']):
            subprocess.run(['git', '-C', str(up)] + c, capture_output=True)
        subprocess.run(['git', '-C', str(up), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(up), 'commit', '-qm', 'upstream'],
                       capture_output=True, env=env)
        up_head = subprocess.run(['git', '-C', str(up), 'rev-parse', 'HEAD'],
                                 capture_output=True, text=True).stdout.strip()

        # A consumer seeded from THIS tree -- so its list still names the file
        # the upstream above no longer has.
        cons = tmp / 'consumer'
        cons.mkdir()
        subprocess.run(['git', '-C', str(cons), 'init', '-q'], capture_output=True)
        r = subprocess.run(
            [sys.executable, str(vend), 'seed', str(cons), '--kind', 'consumer'],
            capture_output=True, text=True, timeout=300, env=env)
        if r.returncode != 0:
            not_applicable('refresh survives an upstream rename',
                           'could not seed a consumer engine here')
            return
        _shutil.copy2(vend, cons / 'tools' / 'precedent_vendor_engine.py')

        r = subprocess.run(
            [sys.executable, str(cons / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(up), '--force', '--from-ref', up_head],
            capture_output=True, text=True, timeout=600, cwd=str(cons), env=env)
        out = r.stdout + r.stderr
        cases.append(('a file removed upstream does not fail the refresh',
                      r.returncode == 0))
        cases.append(('and the run says the file was removed or renamed, '
                      'rather than reporting a broken clone',
                      'removed or renamed' in out))
        try:
            m = _json.loads((cons / 'tools' / 'ENGINE_MANIFEST.json')
                            .read_text(encoding='utf-8'))
        except (OSError, ValueError):
            m = {}
        cases.append(('the missing file is left OUT of the manifest, not '
                      'recorded as present',
                      'precedent_show.py' not in (m.get('files') or [])
                      and 'precedent_show.py' not in (m.get('sha256') or {})))
        cases.append(('every file the manifest DOES record exists on disk',
                      all((cons / 'tools' / f).is_file()
                          for f in (m.get('files') or []))))

        # THE MUST-STAY-FATAL CASE: the vendoring tool itself is gone.
        up2 = tmp / 'upstream-no-tool'
        _shutil.copytree(up, up2)
        (up2 / 'tools' / 'precedent_vendor_engine.py').unlink()
        subprocess.run(['git', '-C', str(up2), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(up2), 'commit', '-qm', 'drop the tool'],
                       capture_output=True, env=env)
        up2_head = subprocess.run(['git', '-C', str(up2), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True).stdout.strip()
        r2 = subprocess.run(
            [sys.executable, str(cons / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(up2), '--force', '--from-ref', up2_head],
            capture_output=True, text=True, timeout=600, cwd=str(cons), env=env)
        out2 = r2.stdout + r2.stderr
        cases.append(('a missing VENDORING TOOL is still fatal -- there is no '
                      'corrected list to converge on', r2.returncode != 0))
        cases.append(('and says that, rather than calling it a removal',
                      'not a removal' in out2))

    failed = [n for n, ok in cases if not ok]
    check(f'a file removed upstream does not brick a consumer refresh '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_refresh_never_rolls_a_newer_engine_back():
    """A repo whose vendored engine came from a BestPractice commit the
    source branch does not contain is AHEAD, not stale: the refresh leaves
    it, and the session-start survey says AHEAD.

    2026-10-02: a practice set made from a working branch recorded that
    branch's commit. Every session start compared it with main only for
    equality, called it stale, and wrote main's older engine over it in the
    working tree, deleting files the set had committed."""
    import tempfile, io, contextlib
    import precedent_vendor_engine as pve
    import precedent_refresh_sources as prs
    cases = []
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               GIT_AUTHOR_NAME='f', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='f', GIT_COMMITTER_EMAIL='f@x')
    g = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a], env=env,
                                        capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        bp = pathlib.Path(td) / 'bp'
        bp.mkdir()
        g(bp, 'init', '-q', '-b', 'main')
        g(bp, 'commit', '-q', '--allow-empty', '-m', 'A')
        old = g(bp, 'rev-parse', 'HEAD')
        g(bp, 'switch', '-q', '-c', 'side')
        g(bp, 'commit', '-q', '--allow-empty', '-m', 'B')
        side = g(bp, 'rev-parse', 'HEAD')
        g(bp, 'switch', '-q', 'main')
        g(bp, 'commit', '-q', '--allow-empty', '-m', 'C')
        tip = g(bp, 'rev-parse', 'HEAD')
        cases.append(('an engine from a branch main does not contain is ahead',
                      pve.engine_is_ahead(bp, side, tip) is True))
        cases.append(('an engine from an older main commit is stale, not ahead',
                      pve.engine_is_ahead(bp, old, tip) is False))
        cases.append(('a commit the clone cannot place is not called ahead',
                      pve.engine_is_ahead(bp, 'f' * 40, tip) is False))

        # refresh() itself: told the source branch is at `tip`, a repo
        # recording `side` is left untouched, and says why.
        repo = pathlib.Path(td) / 'repo'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'kind': 'source', 'source_commit': side, 'files': {}}),
            encoding='utf-8')
        scratch = pathlib.Path(td) / 'engine'
        scratch.mkdir()
        saved = (pve.ROOT, pve._source_tools_at)
        out = io.StringIO()
        try:
            pve.ROOT = repo
            pve._source_tools_at = lambda clone, kind, ref=None, fetch=True: (tip, scratch)
            with contextlib.redirect_stdout(out):
                pve.refresh(bp)
        except SystemExit as e:
            out.write(f'[exited {e}]')
        except Exception as e:
            # Unguarded, it goes on to copy the empty scratch engine over
            # the repo's: that attempt is the rollback this case refuses.
            out.write(f'[went ahead with the copy: {type(e).__name__}: {e}]')
        finally:
            pve.ROOT, pve._source_tools_at = saved
        manifest = json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json')
                              .read_text(encoding='utf-8'))
        cases.append(('refresh leaves a newer engine as it is, and says so',
                      'newer work, not older' in out.getvalue()
                      and manifest['source_commit'] == side
                      and sorted(p.name for p in (repo / 'tools').iterdir())
                      == ['ENGINE_MANIFEST.json'], failure_detail(out.getvalue(), 300)))

        # The survey's question, asked of a BestPractice checkout.
        saved_root = prs.ROOT
        try:
            prs.ROOT = bp
            cases.append(("the session-start survey calls it ahead, and an "
                          "older one not",
                          prs._engine_ahead_of(side, tip) is True
                          and prs._engine_ahead_of(old, tip) is False))
        finally:
            prs.ROOT = saved_root
    bad = [c[0] + (f' -- {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a refresh never rolls a newer engine back ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_seed_refuses_an_engine_main_lacks():
    """seed() and the bootstrap refuse to copy an engine from a commit main
    does not contain, before writing anything, unless told it is on
    purpose; told so, the manifest names the real branch beside a
    source_branch that still says what refresh follows.

    2026-10-02: a practice set made from a working branch recorded
    source_branch "main" over that branch's commit, and every session start
    rolled its engine back (check_refresh_never_rolls_a_newer_engine_back
    is the other half)."""
    import tempfile, io, contextlib
    import precedent_vendor_engine as pve
    import precedent_bootstrap_source as pbs
    cases = []
    env = dict(os.environ, GIT_AUTHOR_NAME='f', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='f', GIT_COMMITTER_EMAIL='f@x')
    g = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a], env=env,
                                        capture_output=True, text=True).stdout.strip()
    saved_env = os.environ.pop('PRECEDENT_SEED_OFF_MAIN', None)
    saved_off = pve.off_source_branch
    try:
        with tempfile.TemporaryDirectory() as td:
            bp = pathlib.Path(td) / 'bp'
            bp.mkdir()
            g(bp, 'init', '-q', '-b', 'main')
            g(bp, 'commit', '-q', '--allow-empty', '-m', 'A')
            old = g(bp, 'rev-parse', 'HEAD')
            g(bp, 'switch', '-q', '-c', 'feature-x')
            g(bp, 'commit', '-q', '--allow-empty', '-m', 'B')
            side = g(bp, 'rev-parse', 'HEAD')
            cases.append(('a commit main lacks is named by the branch it is on',
                          pve.off_source_branch(bp, side) == 'feature-x'))
            cases.append(('a commit main contains is not off main',
                          pve.off_source_branch(bp, old) is None))
            nomain = pathlib.Path(td) / 'nomain'
            nomain.mkdir()
            g(nomain, 'init', '-q', '-b', 'trunk')
            g(nomain, 'commit', '-q', '--allow-empty', '-m', 'A')
            cases.append(('with no main to ask, nothing is called off main',
                          pve.off_source_branch(nomain, g(nomain, 'rev-parse', 'HEAD'))
                          is None))

            pve.off_source_branch = lambda repo, commit: 'feature-x'
            dest = pathlib.Path(td) / 'refused'
            dest.mkdir()
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err), contextlib.redirect_stdout(err):
                    pve.seed(dest, kind='consumer')
                refused = ''
            except SystemExit as e:
                refused = str(e)
            cases.append(('seed refuses it, naming the branch and --off-main, '
                          'and writes nothing',
                          'REFUSED' in refused and 'feature-x' in refused
                          and '--off-main' in refused and not any(dest.iterdir()),
                          refused[:200]))

            dest = pathlib.Path(td) / 'told'
            dest.mkdir()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(err):
                pve.seed(dest, kind='consumer', off_main=True)
            m = json.loads((dest / 'tools' / 'ENGINE_MANIFEST.json')
                           .read_text(encoding='utf-8'))
            cases.append(('told --off-main, the manifest names the real branch '
                          'and keeps source_branch main',
                          m.get('source_branch') == pve.SOURCE_BRANCH
                          and m.get('seeded_from_branch') == 'feature-x', str(m)[:200]))

            bdest = pathlib.Path(td) / 'set'
            saved_warn = pbs._warn_if_clone_is_stale
            pbs._warn_if_clone_is_stale = lambda *_a: None
            try:
                pbs.bootstrap('shared', 'precedent-shared-zz', bdest,
                              approvers=[{'name': 'A B', 'github': 'ab'}])
                why = ''
            except pbs.BootstrapRefused as e:
                why = str(e)
            finally:
                pbs._warn_if_clone_is_stale = saved_warn
            cases.append(('the bootstrap refuses it before creating the set',
                          'feature-x' in why and '--off-main true' in why
                          and not bdest.exists(), why[:200]))
    finally:
        pve.off_source_branch = saved_off
        if saved_env is not None:
            os.environ['PRECEDENT_SEED_OFF_MAIN'] = saved_env
    bad = [c[0] + (f' -- {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'seed refuses an engine main lacks, unless told ({len(cases)} stated cases)',
          not bad, '; '.join(bad))

def check_refresh_removes_dropped_engine_files():
    """A file dropped from the engine set leaves every consumer, not just this repo.

    refresh() only ever added and overwrote. Rename or drop a file from KINDS
    and every consumer that already had it kept it forever: the new manifest
    stops listing it, so nothing tracks it, nothing updates it, and no later
    reader can tell whether it still does something. That is the exact state
    decommission-deletes-files exists to prevent, produced by the tool that
    distributes that practice.

    Found 2026-09-07 costing the retirement->decommission rename: the tool
    being renamed is IN the consumer engine set, so the rename would have
    pushed the new name out and left the old one beside it in perpetuity --
    two repos that day, and every consumer created afterwards.

    Safety rests entirely on the manifest. Only files the PREVIOUS manifest
    recorded as vendored are candidates, so a consuming repo's own tools/
    cannot be touched whatever it is named -- that is the case this test
    spends a fixture on, because getting it wrong deletes somebody's work
    rather than merely leaving litter.

    And a hand-edited copy is KEPT and reported. _local_drift already refuses
    the whole refresh over one unless --force, so arriving here modified
    means somebody asked to overwrite -- which is not the same as asking to
    throw the edit away.
    """
    import tempfile, json as _json, shutil as _shutil
    vend = ROOT / 'tools' / 'precedent_vendor_engine.py'
    if not vend.exists():
        not_applicable('refresh removes dropped engine files',
                       'tools/precedent_vendor_engine.py is not present here')
        return

    ref = _ref_including_worktree(ROOT)

    def _consumer(base):
        """Seed a real consumer engine from THIS working tree."""
        base.mkdir(parents=True)
        subprocess.run(['git', '-C', str(base), 'init', '-q'], capture_output=True)
        # The harness seed cache: the second and third consumers (and a later
        # run at the same checkout state) copy what the first seed wrote.
        rc, _out = _seed_fixture_engine(base, 'consumer', env, cwd=ROOT)
        if rc != 0:
            return None
        # AND OVERWRITE THE SEEDED TOOL WITH THIS WORKING TREE'S. `seed`
        # vendors via git, so it copies the COMMITTED engine -- a fixture
        # built on it silently tests the code as it was before your change.
        # Cost this exact test three red cases before the cause was found,
        # and cost the rename-updates-links test the same thing an hour
        # earlier, which is why it is spelled out in both.
        _shutil.copy2(vend, base / 'tools' / 'precedent_vendor_engine.py')
        return base

    def _manifest(base):
        return _json.loads(
            (base / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # HOME and the user config are the fixture's own (practice:
        # fixture-owns-its-state), which is also what lets the seed cache
        # key them.
        (tmp / 'home').mkdir()
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1', HOME=str(tmp / 'home'),
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
                   GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        base = _consumer(tmp / 'consumer')
        if base is None:
            not_applicable('refresh removes dropped engine files',
                           'could not seed a consumer engine here')
            return

        m = _manifest(base)
        victim = 'precedent_show.py'
        cases.append(('the fixture starts with the file it will drop',
                      victim in (m.get('files') or [])
                      and (base / 'tools' / victim).is_file()))

        # A file the engine NEVER vendored, sitting in the same directory.
        # Nothing may touch this, ever.
        own = base / 'tools' / 'this_repos_own_tool.py'
        own.write_text('# not the engine\'s\n', encoding='utf-8')

        # Simulate the drop by rewriting the PREVIOUS manifest to claim one
        # more file than the current KINDS list has -- which is exactly the
        # shape a real rename leaves behind.
        extra = 'precedent_retired_name.py'
        (base / 'tools' / extra).write_text('# stale vendored tool\n', encoding='utf-8')
        m['files'] = list(m.get('files') or []) + [extra]
        m.setdefault('sha256', {})[extra] = hashlib.sha256(
            (base / 'tools' / extra).read_bytes()).hexdigest()
        (base / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps(m, indent=2), encoding='utf-8')

        r = subprocess.run(
            [sys.executable, str(base / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(ROOT), '--force', '--from-ref', ref],
            capture_output=True, text=True, timeout=600, cwd=str(base), env=env)
        out = r.stdout + r.stderr

        cases.append(('a file the current set no longer includes is deleted',
                      not (base / 'tools' / extra).exists()))
        cases.append(('and the run says which file went, and why it was safe',
                      extra in out and 'no longer includes' in out))
        cases.append(("a file the engine never vendored is UNTOUCHED -- the "
                      "manifest is what makes this safe", own.is_file()))
        cases.append(('a file still in the set survives',
                      (base / 'tools' / victim).is_file()))

        # NEGATIVE CONTROL on the hand-edit rule: a dropped file whose
        # content no longer matches what was vendored is kept, not deleted.
        base2 = _consumer(tmp / 'edited')
        if base2 is not None:
            m2 = _manifest(base2)
            (base2 / 'tools' / extra).write_text('# stale\n', encoding='utf-8')
            m2['files'] = list(m2.get('files') or []) + [extra]
            m2.setdefault('sha256', {})[extra] = 'deadbeef' * 8   # wrong on purpose
            (base2 / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                _json.dumps(m2, indent=2), encoding='utf-8')
            r2 = subprocess.run(
                [sys.executable, str(base2 / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--force', '--from-ref', ref],
                capture_output=True, text=True, timeout=600, cwd=str(base2), env=env)
            out2 = r2.stdout + r2.stderr
            cases.append(('a hand-edited dropped file is KEPT',
                          (base2 / 'tools' / extra).is_file()))
            cases.append(('and said so, rather than deleted silently',
                          'hand-edited' in out2))

        # END TO END for the legacy sweep (2026-09-24): refresh() itself
        # calls it, before the drift check, and closes with "Left for you".
        # check_legacy_leftovers_retired_by_content covers the cases; this
        # covers the wiring, which is what a real install runs.
        base3 = _consumer(tmp / 'legacy')
        if base3 is not None:
            _shutil.copy2(ROOT / 'tools' / 'precedent_decommission.py',
                          base3 / 'tools' / 'precedent_decommission.py')
            wf = base3 / '.github' / 'workflows'
            wf.mkdir(parents=True)
            (wf / 'bestpractice-upstream-sync.yml').write_text(
                'on:\n  workflow_dispatch:\njobs:\n  u:\n    steps:\n'
                '      - uses: anthropics/claude-code-action@v1\n',
                encoding='utf-8')
            (wf / 'bestpractice-docs.yml').write_text(
                'on:\n  workflow_dispatch:\njobs:\n  d:\n    steps:\n'
                '      - run: python3 tools/our_own.py\n', encoding='utf-8')
            genv = dict(env, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='harness@example.com',
                        GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='harness@example.com')
            subprocess.run(['git', '-C', str(base3), 'add', '-A'],
                           capture_output=True, env=genv)
            subprocess.run(['git', '-C', str(base3), 'commit', '-qm', 'base'],
                           capture_output=True, env=genv)
            r3 = subprocess.run(
                [sys.executable, str(base3 / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--force', '--from-ref', ref],
                capture_output=True, text=True, timeout=600, cwd=str(base3), env=env)
            out3 = r3.stdout + r3.stderr
            cases.append(('refresh itself retires a stock-shaped legacy '
                          'workflow no manifest ever tracked',
                          not (wf / 'bestpractice-upstream-sync.yml').exists()))
            # A consumer's CI converges to upstream since 2026-09-27, but a
            # workflow running something the local push check does not run
            # is kept until that moves there (CI_CONVERGES_KINDS).
            cases.append(('and keeps a same-name file of the repo\'s own '
                          'that runs a script the local check does not, '
                          'naming it under "Left for you"',
                          (wf / 'bestpractice-docs.yml').is_file()
                          and 'Left for you' in out3 and 'our_own.py' in out3))

    failed = [n for n, ok in cases if not ok]
    check(f'refresh removes engine files the set no longer includes, and only '
          f'those ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_decommission_records_a_file_already_deleted():
    """THE INCIDENT (2026-10-20, #1317). A change deleted the engine tool
    precedent_switchboard_offer.py by hand and dropped it from the vendor
    list in the same commit. The push check then asked for its record and
    named this tool to write it, and this tool refused: the file was not
    tracked, so there was "no deletion to make". Cases: the audit of a file
    history shows deleted is clear and says only the record is owed; it is
    still read as vendored from the commit before the deletion, so --apply
    asks what it left; --left-nothing records it with [] and deletes
    nothing; a second --apply says it is already recorded; and a path that
    never existed keeps its old refusal."""
    import tempfile, shutil as _shutil, json as _json
    tool = ROOT / 'tools' / 'precedent_decommission.py'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-decom-gone-'))
    cases = []
    try:
        repo = tmp / 'upstream'
        genv = dict(os.environ, GIT_AUTHOR_NAME='t',
                    GIT_AUTHOR_EMAIL='harness@example.com',
                    GIT_COMMITTER_NAME='t',
                    GIT_COMMITTER_EMAIL='harness@example.com')

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=genv)

        def w(rel, text):
            f = repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')

        repo.mkdir()
        git('init', '-q')
        w('tools/precedent_vendor_engine.py',
          "ENGINE = ['kept_tool.py', 'gone_tool.py']\n")
        w('tools/kept_tool.py', '# kept\n')
        w('tools/gone_tool.py', '# about to be retired\n')
        w('process/decommissioned_paths.json', _json.dumps(
            {'decommissioned': [], 'exempt_files': []}))
        git('add', '-A')
        git('commit', '-qm', 'fixture')
        # What #1317 did: delete the tool and drop it from the list together.
        w('tools/precedent_vendor_engine.py', "ENGINE = ['kept_tool.py']\n")
        git('rm', '-q', 'tools/gone_tool.py')
        git('add', '-A')
        git('commit', '-qm', 'retire gone_tool by hand')

        def run(*extra):
            r = subprocess.run([sys.executable, str(tool), *extra],
                               capture_output=True, text=True, cwd=str(repo),
                               timeout=120)
            return r.returncode, r.stdout + r.stderr

        rc, out = run('tools/gone_tool.py')
        cases.append(('the audit of a file already deleted is clear and says '
                      'only the record is owed', rc == 0 and 'CLEAR' in out
                      and 'only the record is owed' in out, failure_detail(out, 1500)))
        rc, out = run('tools/gone_tool.py', '--reason', 'r', '--apply')
        cases.append(('it is read as vendored from before the deletion, so '
                      '--apply asks what it left', rc == 1
                      and 'is vendored into other repositories' in out,
                      failure_detail(out, 1500)))
        rc, out = run('tools/gone_tool.py', '--reason', 'r', '--apply',
                      '--left-nothing')
        reg = _json.loads((repo / 'process' / 'decommissioned_paths.json')
                          .read_text(encoding='utf-8'))['decommissioned']
        cases.append(('--left-nothing records it with [] and deletes nothing',
                      rc == 0 and [e['path'] for e in reg]
                      == ['tools/gone_tool.py']
                      and reg[0].get('left_in_consumers') == []
                      and (repo / 'tools' / 'kept_tool.py').exists(),
                      failure_detail(out, 1500) + str(reg)))
        git('add', '-A')
        git('commit', '-qm', 'record it')
        rc, out = run('tools/gone_tool.py', '--reason', 'r', '--apply',
                      '--left-nothing')
        cases.append(('a second --apply says it is already recorded',
                      rc == 1 and 'already records it' in out, failure_detail(out, 1500)))
        rc, out = run('tools/never_was.py')
        cases.append(('control: a path that never existed keeps its refusal',
                      rc == 1 and 'not tracked by git (or does not exist)' in out,
                      failure_detail(out, 1500)))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'decommission records a file already deleted by hand '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:800]}' for n, d in bad))


def check_main_test_repo_setting():
    """The repository's own github_ci_main_test has the final say over
    main's GitHub test (2026-10-01, spec/CI_CADENCE_PLAN.md, "The repository
    decides"): "individual" (the default), "never", "always" or a number of
    hours. Morgan: "I don't want the big bills to come back", and on two runs
    for one change: "no we don't want it run twice, no no no, not at all".

    THE INVARIANT THAT MATTERS MOST: in a private repository no change that
    lands on main is tested more than once, by any route -- a Promote, a
    pull request merged by hand, a direct push. Counted here by walking each
    route's events through the installed workflow (the template, or the
    template as Update Vendors writes it for "always") and Promote's own
    decision, for every combination of the repository's setting, the
    person's switch and hours, and the time since the last pass. Then the
    real refresh is run on a scratch consumer, both directions."""
    import importlib.util, itertools, json as _json, tempfile, time as _time
    name = 'the repository decides main\'s GitHub test, and no change is tested twice'
    try:
        import yaml as _yaml
    except ImportError:
        not_applicable(name, 'PyYAML is not installed, and the template is read with it')
        return
    tpl = ROOT / 'templates' / 'github-actions' / 'light-check.yml.template'
    srcs = {m: ROOT / 'tools' / f'{m}.py' for m in ('precedent_branches', 'precedent_vendor_engine')}
    if not tpl.is_file() or not all(p.exists() for p in srcs.values()):
        not_applicable(name, 'the light-check template or an engine module is absent')
        return

    def load(mod, alias):
        spec = importlib.util.spec_from_file_location(alias, srcs[mod])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    pb = load('precedent_branches', '_pb_repo_setting')
    pve = load('precedent_vendor_engine', '_pve_repo_setting')
    cases = []
    raw = tpl.read_bytes()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        always_repo = tmp / 'always-repo'
        always_repo.mkdir()
        (always_repo / 'precedent.json').write_text(_json.dumps(
            {'github_ci_main_test': 'always'}), encoding='utf-8')
        rendered = pve.render_ci_workflow(always_repo, raw)
        cases.append(('only "always" changes the file: the marker, and nothing else',
                      rendered != raw
                      and rendered == raw.replace(pve.MAIN_TEST_MARKER, pve.MAIN_TEST_ALWAYS)
                      and len([1 for a, b in zip(raw.splitlines(), rendered.splitlines())
                               if a != b]) == raw.count(pve.MAIN_TEST_MARKER)
                      and pb.MAIN_TEST_ALWAYS_TEXT.encode() in rendered
                      and pb.MAIN_TEST_ALWAYS_TEXT.encode() not in raw))
        for value in ('individual', 'never', 48, 0, 'Always', 'bogus', None):
            other = tmp / f'repo-{value}'
            other.mkdir()
            (other / 'precedent.json').write_text(_json.dumps(
                {} if value is None else {'github_ci_main_test': value}), encoding='utf-8')
            cases.append((f'github_ci_main_test {value!r} leaves the file byte-identical '
                          f'to the template', pve.render_ci_workflow(other, raw) == raw))

        # Parsed once per text: the table below asks starts() about the same
        # two workflow texts some 5,000 times, and parsing them every time
        # was nearly all of this check's 48 s (2026-10-31). Nothing writes
        # to what it returns.
        parsed = {}

        def wf(text):
            if text not in parsed:
                doc = _yaml.safe_load(text)
                parsed[text] = (doc.get('on', doc.get(True)) or {},
                                doc['jobs']['light-check']['if'])
            return parsed[text]

        def starts(text, event, branch, private, head_ref=''):
            on, expr = wf(text)
            if event not in on:
                return False
            trig = on.get(event)
            branches = trig.get('branches') if isinstance(trig, dict) else None
            if branches is not None and branch not in branches:
                return False
            return _gh_if(expr, event, private, head_ref)

        RAW, REN = raw.decode('utf-8'), rendered.decode('utf-8')
        for private in (True, False):
            kind = 'private' if private else 'public'
            for b in ('staging', 'claude/feature-x'):
                cases.append((f'"always", {kind}: a push to {b} still starts no runner',
                              not starts(REN, 'push', b, private)))
        cases.append(('"always", private: a push to main runs',
                      starts(REN, 'push', 'main', True)))
        cases.append(('"always", private: NO pull request into main runs -- not a due '
                      'copy, not a not-due one, not a hand-made one',
                      not any(starts(REN, 'pull_request', 'main', True, h) for h in
                              ('to-main-2026-10-01', pb.NOT_DUE_PREFIX + '2026-10-01',
                               'claude/feature-x', 'staging'))))

        # The table: every route a change takes to main, counted.
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
        installed = {'text': RAW}
        real_git = pb._git
        pb._git = lambda root, *a: (installed['text'] if a[:1] == ('show',)
                                    else real_git(root, *a))
        repo, me = tmp / 'repo', tmp / 'me'
        repo.mkdir()
        me.mkdir()
        cfg = tmp / 'config.json'
        cfg.write_text(_json.dumps({'individual': {'path': str(me)}}), encoding='utf-8')
        wrong, twice, rows = [], [], 0
        modes = (None, 'individual', 'never', 'always', 'always-not-installed', 0, 48, 'bogus')
        for vis, mode, sw, hrs, ago in itertools.product(
                ('public', 'private', None), modes, ('enabled', 'disabled', None),
                (0, 168, None), (1, 47, 49, 200, None)):
            private = vis == 'private'
            pj = {'base_branch': 'main'}
            if vis:
                pj['visibility'] = vis
            if mode is not None:
                pj['github_ci_main_test'] = 'always' if mode == 'always-not-installed' else mode
            (repo / 'precedent.json').write_text(_json.dumps(pj), encoding='utf-8')
            ident = {'email': 'me@example.com'}
            if sw is not None:
                ident['ci_workflows'] = sw
            if hrs is not None:
                ident['ci_every_hours'] = hrs
            (me / 'identity.json').write_text(_json.dumps(ident), encoding='utf-8')
            text = REN if mode == 'always' else RAW
            installed['text'] = text
            due, why = pb.main_test_due(repo, 'TIP', gh=GH(ago), user_config=cfg)
            copy = ('to-main-' if due else pb.NOT_DUE_PREFIX) + '2026-10-01'
            promote = (int(starts(text, 'pull_request', 'main', private, copy))
                       + int(starts(text, 'push', 'main', private)))
            hand = (int(starts(text, 'pull_request', 'main', private, 'claude/feature-x'))
                    + int(starts(text, 'push', 'main', private)))
            direct = int(starts(text, 'push', 'main', private))
            rows += 1
            # The rule, written out. Public: tested (its minutes are free, and
            # every push to main there is tested by decision of 2026-09-27).
            # Private: the repository's word, unless it says "individual".
            if not private:
                exp_promote_pr, exp_push = True, True
            else:
                eff = 'individual' if mode in (None, 'individual', 'always-not-installed') \
                    else 'never' if mode == 'bogus' else mode
                on_ = sw in ('enabled', None)
                if eff == 'never':
                    exp_promote_pr, exp_push = False, False
                elif eff == 'always':
                    exp_promote_pr, exp_push = False, True
                elif isinstance(eff, (int, float)):
                    exp_promote_pr = ago is None or ago >= eff
                    exp_push = False
                else:
                    h = hrs if isinstance(hrs, (int, float)) else 0
                    exp_promote_pr = on_ and (ago is None or ago >= h)
                    exp_push = False
            exp_promote = int(exp_promote_pr) + int(exp_push)
            label = f'{vis}/{mode}/{sw}/{hrs}h/last {ago}h'
            if promote != exp_promote or direct != int(exp_push) or (
                    private and hand != int(exp_push)):
                wrong.append(f'{label}: promote={promote} hand={hand} direct={direct}, '
                             f'expected promote={exp_promote} push={int(exp_push)} ({why[:80]})')
            if private and (promote > 1 or hand > 1 or direct > 1):
                twice.append(label)
        pb._git = real_git
        if saved_force is not None:
            os.environ[pb.FORCE_ENV] = saved_force
        cases.append((f'all {rows} combinations run exactly when the rule says, by '
                      f'every route: a Promote, a hand-made pull request, a direct push',
                      not wrong))
        cases.append(('in a private repository, NO route tests one change twice',
                      not twice))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'visibility': 'private', 'github_ci_main_test': 'bogus'}), encoding='utf-8')
        mode, _h, why = pb.main_test_mode(repo)
        cases.append(('a value that is none of the four reads as "never", and says so',
                      mode == 'never' and 'not "individual"' in why))

        # Update Vendors, for real, on a scratch consumer: "always" is written
        # into the file and recorded, and taken back out when it changes.
        import hashlib as _hl
        dest = tmp / 'consumer'
        (dest / 'tools').mkdir(parents=True)
        (dest / '.github' / 'workflows').mkdir(parents=True)
        # As a real consumer has it: the template installed, recorded in the
        # manifest, and committed -- the refresh replaces only a file git holds.
        (dest / 'tools' / 'ENGINE_MANIFEST.json').write_text(_json.dumps(
            {'kind': 'consumer', 'ci_workflow_files': ['.github/workflows/light-check.yml'],
             'ci_workflows_sha256': {'.github/workflows/light-check.yml':
                                     _hl.sha256(raw).hexdigest()}}), encoding='utf-8')
        installed_wf = dest / '.github' / 'workflows' / 'light-check.yml'
        installed_wf.write_bytes(raw)
        genv = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                    GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                    GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), PRECEDENT_ALLOW_ANY_AUTHOR='1')
        for a in (['init', '-q', '-b', 'main'], ['add', '-A'], ['commit', '-qm', 'install']):
            subprocess.run(['git', '-C', str(dest), *a], capture_output=True, env=genv)
        (dest / 'precedent.json').write_text(_json.dumps(
            {'visibility': 'private', 'github_ci_main_test': 'always'}), encoding='utf-8')
        tdir = ROOT / 'templates' / 'github-actions'
        man = _json.loads((dest / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
        pve._refresh_ci_workflow_files(dest, 'consumer', tdir, man)
        got = installed_wf.read_bytes()
        man = _json.loads((dest / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
        cases.append(('Update Vendors writes "always" into a repo that asks for it, and '
                      'records that file, so the workflow-approval check sees it as '
                      "the engine's own",
                      got == rendered and man.get('ci_workflows_sha256', {}).get(
                          '.github/workflows/light-check.yml') == _hl.sha256(got).hexdigest()))
        (dest / 'precedent.json').write_text(_json.dumps(
            {'visibility': 'private', 'github_ci_main_test': 'individual'}), encoding='utf-8')
        pve._refresh_ci_workflow_files(dest, 'consumer', tdir, man)
        cases.append(('...and takes it back out when the repo changes its mind',
                      installed_wf.read_bytes() == raw))
    failed = [n for n, ok in cases if not ok]
    detail = '; '.join(failed) + ((' | ' + ' | '.join(wrong[:4])) if wrong else '')
    check(f'{name} ({len(cases)} stated cases, {rows} table rows)', not failed, detail)


def check_freshness_quiet_says_when_a_source_is_unverified():
    """`precedent_engine_freshness.py --quiet`, which every session-start
    hook runs, prints one NOT VERIFIED line when a declared source could not
    be checked -- it printed nothing, which is what current looks like
    (the maintainers' drift-notice; very deep check, 2026-09-28).
    Planted: a consumer whose engine manifest points at an upstream that is
    not there. Controls: a current source stays silent, and a repo with no
    engine manifest at all (the engine's own origin) is not an unverified
    source."""
    import io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_engine_freshness as pef
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='freshness-quiet-'))
    saved_env = os.environ.get(pef.USER_CONFIG_ENV)
    cases = []
    try:
        os.environ[pef.USER_CONFIG_ENV] = str(tmp / 'no-such-config.json')
        up = tmp / 'upstream'
        up.mkdir()
        for args in (('init', '-q', '-b', 'main'),
                     ('config', 'user.email', 'harness@example.com'),
                     ('config', 'user.name', 'harness')):
            subprocess.run(['git', '-C', str(up), *args], check=True,
                           capture_output=True)
        (up / 'f.txt').write_text('v1\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(up), 'add', '-A'], check=True,
                       capture_output=True)
        subprocess.run(['git', '-C', str(up), 'commit', '-qm', 'first'],
                       check=True, capture_output=True)
        tip = subprocess.run(['git', '-C', str(up), 'rev-parse', 'HEAD'],
                             check=True, capture_output=True,
                             text=True).stdout.strip()

        def consumer(name, repo_url):
            c = tmp / name
            (c / 'tools').mkdir(parents=True)
            if repo_url is not None:
                (c / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                    'format_version': 1, 'kind': 'consumer',
                    'source_repo': repo_url, 'source_branch': 'main',
                    'source_commit': tip, 'files': []}), encoding='utf-8')
            return c

        def quiet(c):
            buf = io.StringIO()
            rc = pef.report(c, quiet=True, out=buf)
            return rc, buf.getvalue()

        rc, out = quiet(consumer('unreachable', str(tmp / 'gone')))
        cases.append(('THE CASE: --quiet says a source could not be verified',
                      'freshness: NOT VERIFIED -- 1 source(s) could not be '
                      'checked this session' in out
                      and 'not verified is not current' in out, out))
        cases.append(('the exit status is still 0', rc == 0, repr(rc)))
        _rc, out = quiet(consumer('current', str(up)))
        cases.append(('CONTROL: --quiet says nothing while every source is '
                      'current', out == '', out))
        _rc, out = quiet(consumer('origin', None))
        cases.append(('CONTROL: no engine manifest at all is not an '
                      'unverified source', out == '', out))
    finally:
        if saved_env is None:
            os.environ.pop(pef.USER_CONFIG_ENV, None)
        else:
            os.environ[pef.USER_CONFIG_ENV] = saved_env
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'freshness --quiet never lets not verified read as current '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_catalogue_hook_runs_the_freshness_notice():
    """The SessionStart hook every practice SET runs
    (templates/harness/claude-code/hooks/precedent-universal-catalogue.sh)
    runs `precedent_engine_freshness.py --quiet` and its lines reach the
    model through the hook's JSON -- a set never ran it, so a session in a
    set was never told its engine or a sibling clone had fallen behind
    (the maintainers' drift-notice; very deep check, 2026-09-28). Planted: a set
    whose vendored tools are stubs that print a marker. Control: a set whose
    engine predates the tool still starts cleanly."""
    import shutil, tempfile
    hook = ROOT / 'tools' / 'precedent-universal-catalogue.sh'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='catalogue-freshness-'))
    cases = []
    try:
        s = tmp / 'set'
        (s / 'tools').mkdir(parents=True)
        (s / 'tools' / 'precedent_session_practices.py').write_text(
            'print("render ran")\n', encoding='utf-8')
        (s / 'tools' / 'precedent_engine_freshness.py').write_text(
            'import sys\nprint("FRESHNESS-MARKER " + " ".join(sys.argv[1:]))\n',
            encoding='utf-8')
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(s))

        def run_hook():
            return subprocess.run(['bash', str(hook)], cwd=str(s), env=env,
                                  capture_output=True, text=True, timeout=60)

        p = run_hook()
        try:
            ctx = json.loads(p.stdout)['hookSpecificOutput']['additionalContext']
        except (ValueError, KeyError, TypeError):
            ctx = None
        cases.append(('the hook still prints one JSON object',
                      ctx is not None, p.stdout[:300] + p.stderr[:300]))
        cases.append(('THE CASE: the freshness notice reaches the model, run '
                      '--quiet', ctx is not None
                      and 'FRESHNESS-MARKER' in ctx and '--quiet' in ctx,
                      str(ctx)[:300]))
        (s / 'tools' / 'precedent_engine_freshness.py').unlink()
        p2 = run_hook()
        cases.append(('CONTROL: a set without the tool starts cleanly',
                      p2.returncode == 0 and 'render ran' in p2.stdout,
                      p2.stdout[:300] + p2.stderr[:300]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a practice set\'s SessionStart hook runs the freshness notice '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_bootstrap_source_engine_is_functional():
    """spec/BOOTSTRAP_NEW_SOURCES.md's newer claim, tested rather than
    trusted: precedent_bootstrap_source.py's output carries a real, working
    engine (tools/precedent_vendor_engine.py's seed()), not just files
    copied into place -- the same rigor check_materialize_bridges_loader()
    already applies to materialize()'s output, and check_bootstrap_source_
    produces_resolvable_set() above already applies to the practice content
    half of bootstrap's output. This is the engine half.

    Fixture: bootstrap one individual set, then run its OWN vendored copies
    of build_views.py/precedent_gate.py/precedent_paths.py/precedent_show.py
    IN PLACE (real subprocesses, cwd set to the bootstrapped dest, no --repo
    -- exactly how a source repo's own AGENTS.md tells a session to invoke
    them) against a second, fixture practice added after bootstrap, proving
    each command produces real output naming that practice -- not merely
    that the files exist and are byte-identical to something. Also asserts
    ENGINE_MANIFEST.json's recorded hashes actually match what got written
    (status() against this repo's own checkout must find zero drift right
    after a fresh seed), which is the property tools/precedent_vendor_
    engine.py's whole refresh-refusal mechanism depends on."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bootstrap-engine-'))
    cases = []
    try:
        bootstrap_tool = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        dest = tmp / 'engine-set'
        r = subprocess.run([sys.executable, bootstrap_tool, '--level', 'individual',
                            '--name', 'precedent-individual', '--dest', str(dest)],
                           capture_output=True, text=True)
        cases.append(('bootstrapping succeeds', r.returncode == 0, r.stdout + r.stderr))

        manifest_path = dest / 'tools' / 'ENGINE_MANIFEST.json'
        engine_files = ['build_views.py', 'precedent_gate.py', 'precedent_paths.py',
                        'precedent_show.py', 'split_practices.py',
                        'precedent_vendor_engine.py', 'routing_scope.json']
        cases.append(('every engine file is present',
                      all((dest / 'tools' / f).is_file() for f in engine_files),
                      str([f for f in engine_files if not (dest / 'tools' / f).is_file()])))
        cases.append(('ENGINE_MANIFEST.json exists and names the source repo',
                      manifest_path.is_file()
                      and 'BestPractice' in (manifest_path.read_text(encoding='utf-8')), ''))

        # -- the recorded sha256 for every file actually matches what's on
        # disk -- the exact property refresh()'s drift check relies on --
        import hashlib
        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {}
        mismatched = [f for f, h in manifest.get('sha256', {}).items()
                     if hashlib.sha256((dest / 'tools' / f).read_bytes()).hexdigest() != h]
        cases.append(('every recorded sha256 matches the file actually written',
                      manifest.get('sha256') and not mismatched, str(mismatched)))

        # -- status(), run from the bootstrapped set's OWN vendored copy of
        # the tool, against this repo's real checkout, finds zero drift
        # immediately after a fresh seed --
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(ROOT)], capture_output=True, text=True)
        cases.append(('status() against a real BestPractice checkout finds no drift '
                      'right after seeding', r.returncode == 0, r.stdout + r.stderr))


        # -- status() must not turn "this clone has no SOURCE_BRANCH" into
        # "upstream has moved". _git() discards exit codes, and a plain
        # `git rev-parse <missing-ref>` PRINTS THE REF NAME, so status() used to
        # bind clone_head='origin/<SOURCE_BRANCH>', find it != recorded, and
        # advise running `refresh` -- which, before refresh() became read-only,
        # would then check the reader's own BestPractice clone out onto
        # SOURCE_BRANCH. A false alarm wired to a destructive remedy. Fixed
        # 2026-09-06 while auditing every _git() call site in that tool.
        #
        # An initialized repo with no commits covers both halves at once: it has
        # no SOURCE_BRANCH, and its HEAD is unborn -- the one state where
        # `rev-parse HEAD` echoes 'HEAD' on stdout (a non-repo prints nothing,
        # which is why the plain form looked fine for years).
        norefs = tmp / 'clone-without-source-branch'
        norefs.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(norefs), 'init', '-q'], capture_output=True)
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(norefs)], capture_output=True, text=True)
        status_out = r.stdout + r.stderr
        cases.append(('status() on a clone with no SOURCE_BRANCH reports COULD NOT VERIFY '
                      'and does NOT claim upstream has moved',
                      'COULD NOT VERIFY' in status_out
                      and 'has moved since this engine' not in status_out,
                      status_out))

        # -- and the resolver underneath it. seed() does
        # `_head_commit(ROOT) or 'unknown'`, so a truthy 'HEAD' was recorded as
        # ENGINE_MANIFEST.json's source_commit, after which every status() and
        # refresh() compared a real hash against the string "HEAD" and reported
        # upstream as moved, permanently.
        import precedent_vendor_engine as _pve
        cases.append(("_rev() returns '' for an unborn HEAD rather than the string 'HEAD', "
                      "so seed()'s `or 'unknown'` fallback actually fires",
                      _pve._rev(norefs, 'HEAD') == '' and _pve._head_commit(norefs) == '',
                      f"_rev={_pve._rev(norefs, 'HEAD')!r} "
                      f"_head_commit={_pve._head_commit(norefs)!r}"))

        # -- add a second, fixture practice AFTER bootstrap (example-starter
        # alone proves too little: its own occasion text could coincidentally
        # match without the loader actually parsing frontmatter) --
        (dest / 'practices' / 'engine-fixture-slug.md').write_text(
            '---\nslug: engine-fixture-slug\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["fixture-only/**"]\n'
            'occasion: "testing the bootstrapped engine is functional"\n'
            'gates: []\n'
            # Asserts the slug lands in the rendered block, so it declares
            # its index line rather than inheriting one: its applies_to names
            # real paths, which is the shape build_views now omits from the
            # occasion index (practice: fixture-owns-its-state).
            'index_required: true\n'
            'index_clause: "engine-fixture-slug — a bootstrap-harness fixture"\n'
            'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
            'overrides: null\nadded: 2026-09-05\n'
            'approved_by: "harness, 2026-09-05"\nsource_practice_number: null\n'
            '---\n## Rule\nA fixture-only rule, present in no other repo.\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')
        (dest / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        # build_views.py --agents-only, run IN PLACE (no --repo), cwd == dest
        r = subprocess.run([sys.executable, 'tools/build_views.py', '--agents-only'],
                           capture_output=True, text=True, cwd=str(dest))
        agents_text = (dest / 'AGENTS.md').read_text(encoding='utf-8') if (dest / 'AGENTS.md').exists() else ''
        cases.append(('the vendored build_views.py, run in place with no --repo, '
                      'regenerates AGENTS.md naming the fixture practice',
                      r.returncode == 0 and 'engine-fixture-slug' in agents_text,
                      r.stdout + r.stderr))

        # precedent_gate.py --list, run in place
        r = subprocess.run([sys.executable, 'tools/precedent_gate.py', '--list'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_gate.py lists the real (trimmed) gate '
                      'vocabulary', r.returncode == 0 and 'merge' in r.stdout
                      and 'review' in r.stdout, r.stdout + r.stderr))

        # precedent_paths.py, run in place, against a path the fixture's
        # applies_to actually matches
        r = subprocess.run([sys.executable, 'tools/precedent_paths.py', 'fixture-only/x.md'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_paths.py matches the fixture practice by '
                      'its real applies_to glob', r.returncode == 0
                      and 'engine-fixture-slug' in r.stdout, r.stdout + r.stderr))

        # precedent_show.py, run in place
        r = subprocess.run([sys.executable, 'tools/precedent_show.py', 'engine-fixture-slug'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_show.py returns the fixture practice\'s '
                      'real Rule text', r.returncode == 0
                      and 'present in no other repo' in r.stdout, r.stdout + r.stderr))

        # -- refresh(), run from the bootstrapped set's OWN vendored copy of
        # the tool against this repo's real checkout, must leave that checkout
        # exactly where it stood. refresh() used to `git checkout
        # SOURCE_BRANCH` + `git pull` in the clone it reads FROM, which moved
        # the caller's repository: for a person, off the branch they were
        # working on; in CI, the workspace itself, mid-job, so every LATER
        # step in that job silently ran against SOURCE_BRANCH instead of the
        # commit under test. That is what PR #110 spent two rounds of
        # diagnosis on -- and `git status` stays clean the whole time (a
        # branch checkout leaves no dirty file to notice), which is why no
        # amount of content verification found it. Asserted against the real
        # ROOT on purpose: a fixture clone would not have caught the bug,
        # because the bug is precisely about which repo gets moved.
        def root_state():
            return tuple(subprocess.run(['git', '-C', str(ROOT)] + argv,
                                        capture_output=True, text=True).stdout.strip()
                         for argv in (['rev-parse', 'HEAD'],
                                      ['rev-parse', '--abbrev-ref', 'HEAD'],
                                      ['status', '--porcelain']))

        # --from-ref, computed rather than the literal 'HEAD': vendor the
        # tree under test -- including anything not yet committed, such as
        # a brand-new file not yet `git add`ed -- not whatever
        # origin/precedent-beta-v01 holds and not merely whatever HEAD
        # holds. Without it, adding a file to ENGINE_FILES turns this case
        # red until the addition is published, and a contributor's stale
        # local branch, OR simply an uncommitted edit, fails it with a
        # message that has nothing to do with the property this case
        # actually asserts. See _ref_including_worktree's own docstring.
        ref = _ref_including_worktree(ROOT)
        before = root_state()
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(ROOT), '--force', '--from-ref', ref],
                           capture_output=True, text=True)
        after = root_state()
        cases.append(('refresh() against a real BestPractice checkout leaves its HEAD, '
                      'branch and working tree exactly as they were -- it reads blobs, '
                      'it never checks the clone out',
                      before == after,
                      f'before={before}\nafter={after}\n{r.stdout}{r.stderr}'))
        cases.append(('refresh() against a real BestPractice checkout succeeds',
                      r.returncode == 0, r.stdout + r.stderr))

        # The ALREADY-CURRENT path -- no --force, nothing to write, an early
        # return. It had no case of its own, and that is how the identical
        # NameError (`_warn_catalogue_skew(dest, ...)`, where refresh's local
        # is dest_tools) shipped TWICE on 2026-09-06: once on the write path
        # and, a commit later, again on this one. Both printed their success
        # line before raising, so only an exit code ever showed it. A branch
        # with no case is a branch that gets a crash added to it.
        r2 = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                             'refresh', str(ROOT), '--from-ref', ref],
                            capture_output=True, text=True)
        cases.append(('refresh() on the already-current path returns cleanly '
                      'rather than raising after its own success message',
                      r2.returncode == 0 and 'Traceback' not in (r2.stdout + r2.stderr),
                      r2.stdout + r2.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'bootstrap_source\'s output engine is real and functional, not just present '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def _write_fixture_practice(path, slug, applies_to, rule_text):
    """Same frontmatter shape check_bootstrap_source_engine_is_functional's
    own fixture practice uses -- kept as a helper here because this check
    needs three of these (one per source level) instead of one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
        f'severity: default\napplies_to: {json.dumps(applies_to)}\n'
        f'occasion: "testing the vendored consumer engine"\n'
        f'gates: []\nindex_clause: "{slug} — a consumer-engine-harness fixture"\n'
        'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
        'overrides: null\nadded: 2026-09-05\n'
        'approved_by: "harness, 2026-09-05"\nsource_practice_number: null\n'
        f'---\n## Rule\n{rule_text}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
        encoding='utf-8')


def check_vendor_engine_consumer_case():
    """Tested rather than trusted: tools/precedent_vendor_
    engine.py's 'consumer' kind (added 2026-09-05, piloted against a real
    private consumer repo) produces a genuinely working
    four-source engine in a consumer repo, the same rigor
    check_bootstrap_source_engine_is_functional() already applies to the
    narrower source-set case -- not just that the right files land in the
    right place.

    Distinct from that check in what it has to prove: a source set's
    vendored engine only ever reads ONE practices/ directory (its own). A
    consumer's vendored engine has to actually RESOLVE three real, separate
    sources (universal = this repo's own checkout, a fixture shared set, a
    fixture repo-local set) through precedent_resolve.py/precedent_
    materialize.py/precedent_sync_views.py into one materialized tree
    BEFORE build_views.py/precedent_gate.py/precedent_paths.py/
    precedent_show.py have anything to read -- so this fixture wires all
    three, seeds the consumer's own vendored engine with `--kind consumer`,
    then proves a fixture practice AT EACH LEVEL survives the whole pipeline
    into AGENTS.md and into each command's real output."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-consumer-engine-'))
    cases = []
    # Same class of bug as the leak-gate blocklist-discovery fixture's own
    # 2026-09-08 gotcha (see its docstring above): precedent_resolve.py's
    # config-file self-heal reads $HOME/.config/precedent/config.json and
    # silently adds a fourth, undeclared individual source when that file
    # names one -- which it does on any container where a private source
    # has already been resolved once. This fixture's own precedent.json
    # declares exactly three sources; every subprocess below inherits the
    # ambient HOME unless isolated, so it picked up a real precedent-individual
    # clone as a bonus source nobody declared, and precedent_sync_views.py's
    # own IN FORCE NOWHERE check then correctly flagged that source's real
    # deduplicated practices as unresolvable -- against a source this fixture
    # never claimed to model. Found 2026-09-23: reproduced with `4 failed`
    # under the container's real HOME, `2 failed` (the two pre-existing,
    # unrelated failures) under an isolated one.
    saved_home = os.environ.get('HOME')
    isolated_home = tmp / 'isolated-home'
    isolated_home.mkdir()
    os.environ['HOME'] = str(isolated_home)
    try:
        consumer = tmp / 'consumer'
        team_dir = tmp / 'precedent-team-consumer-fixture'
        consumer.mkdir()

        # practice: fixture-owns-its-state -- this fixture declares exactly
        # three sources in its own precedent.json (universal, one fixture
        # shared set, one fixture repo-local set) and every assertion below
        # assumes only those three resolve. Without this, a session whose
        # REAL individual practice source is configured (an ordinary state
        # for an interactive Precedent session, not a broken one) leaks that
        # real, private source into precedent_resolve.py's ambient
        # user-level config lookup -- found 2026-09-22: the fixture then
        # failed with a REAL private practice's dedup finding
        # ("deliverables-carry-no-process (precedent-individual)") and a
        # REAL filename collision between BestPractice's own
        # tools/checks/check_buenos_aires_dates.py (tracked since commit
        # 9d16b6ae) and the real precedent-individual clone's same-named
        # script -- neither of which this fixture's own three declared
        # sources could ever produce. check_precedent_check_fires()'s run()
        # already isolates this the same way, for the same reason.
        env_iso = dict(os.environ)
        env_iso['PRECEDENT_USER_CONFIG'] = str(tmp / '.no-user-config.json')

        _write_fixture_practice(team_dir / 'practices' / 'consumer-fixture-team.md',
                                 'consumer-fixture-team', ['team-only/**'],
                                 'A shared-level fixture rule, present in no other repo.')
        _write_fixture_practice(consumer / 'local' / 'practices' / 'consumer-fixture-local.md',
                                 'consumer-fixture-local', ['local-only/**'],
                                 'A repo-local fixture rule, present in no other repo.')

        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'visibility': 'private',   # declared, not defaulted -- see above
            'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                {'level': 'team', 'name': 'precedent-team-consumer-fixture', 'path': str(team_dir)},
                {'level': 'repo-local', 'name': 'local', 'path': 'local'},
            ],
        }), encoding='utf-8')
        (consumer / 'AGENTS.md').write_text(
            f'# fixture consumer\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')

        # -- seed the consumer's OWN vendored engine, from THIS checkout,
        # exactly how INSTALL.md's consumer procedure runs it --
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
                            'seed', str(consumer), '--kind', 'consumer'],
                           capture_output=True, text=True)
        cases.append(('seeding the consumer engine succeeds', r.returncode == 0,
                      r.stdout + r.stderr))

        manifest_path = consumer / 'tools' / 'ENGINE_MANIFEST.json'
        consumer_files = ['build_views.py', 'precedent_gate.py', 'precedent_paths.py',
                          'precedent_show.py', 'split_practices.py',
                          'precedent_materialize.py', 'precedent_resolve.py',
                          'precedent_sync_views.py', 'precedent_vendor_engine.py',
                          'routing_scope.json']
        cases.append(('every consumer engine file is present -- all 8 content files plus '
                      'the vendoring tool itself',
                      all((consumer / 'tools' / f).is_file() for f in consumer_files),
                      str([f for f in consumer_files if not (consumer / 'tools' / f).is_file()])))

        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {}
        cases.append(("ENGINE_MANIFEST.json records kind: consumer",
                      manifest.get('kind') == 'consumer', str(manifest.get('kind'))))

        # -- an engine file hand-dropped beside a correctly vendored engine
        # is reported, not silently carried. Both directions, because the
        # real incident (precedent-team-repo-maintenance, 2026-09-06) looked
        # HEALTHY to every mechanism that existed: the manifest's own files
        # all matched, so drift detection saw nothing, while the stray file
        # -- from a later upstream commit -- broke build_views.py outright.
        def _vendor_status(repo):
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_vendor_engine.py'),
                 'status', str(ROOT)],
                capture_output=True, text=True, cwd=str(repo))
            return r.returncode, r.stdout + r.stderr

        rc_clean, out_clean = _vendor_status(consumer)
        cases.append(('a freshly seeded engine reports no untracked engine file',
                      'UNTRACKED ENGINE FILE' not in out_clean, out_clean[:400]))

        # The faithful shape of the real incident: the file sits on disk
        # while the manifest -- written at an EARLIER upstream commit, before
        # that file joined the engine -- does not record it. Planting it by
        # dropping the manifest entry rather than by adding a file is what
        # makes this the real case: every remaining recorded file still
        # matches, so drift detection stays silent, exactly as it did.
        manifest_backup = manifest_path.read_text(encoding='utf-8')
        older = json.loads(manifest_backup)
        older['files'] = [f for f in older['files'] if f != 'build_codeowners.py']
        older.get('sha256', {}).pop('build_codeowners.py', None)
        manifest_path.write_text(json.dumps(older, indent=2), encoding='utf-8')
        rc_stray, out_stray = _vendor_status(consumer)
        cases.append(('an engine file present on disk but absent from the manifest '
                      'is reported, and exits non-zero',
                      rc_stray == 1 and 'UNTRACKED ENGINE FILE' in out_stray
                      and 'build_codeowners.py' in out_stray, out_stray[:400]))

        # a file that is NOT an engine file is the repo's own business
        own = consumer / 'tools' / 'the_repos_own_script.py'
        own.write_text('# this repo wrote this itself\n', encoding='utf-8')
        rc_own, out_own = _vendor_status(consumer)
        cases.append(("a repo's own non-engine script in tools/ is not reported",
                      'the_repos_own_script.py' not in out_own, out_own[:400]))
        cases.append(('drift detection stayed silent on the same tree -- which is '
                      'why the untracked check had to exist separately',
                      'LOCAL DRIFT' not in out_stray, out_stray[:400]))
        manifest_path.write_text(manifest_backup, encoding='utf-8')
        own.unlink()

        # -- refresh converges on a repo whose engine predates an added file.
        # The commit matches; only the FILE SET is short. Before this, the
        # commit alone decided, so such a repo was told "already current"
        # forever and could never acquire the file -- reproduced across all
        # three of this account's practice sets on 2026-09-06, and the reason
        # one of them had a hand-copied build_codeowners.py in the first place.
        older = json.loads(manifest_path.read_text(encoding='utf-8'))
        older['files'] = [f for f in older['files'] if f != 'build_codeowners.py']
        older.get('sha256', {}).pop('build_codeowners.py', None)
        manifest_path.write_text(json.dumps(older, indent=2), encoding='utf-8')
        (consumer / 'tools' / 'build_codeowners.py').unlink()
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        # `seed` copies the working tree and records HEAD; this case needs
        # the two to be the same engine ("the recorded commit already
        # matches"). With an engine edit not yet committed they are not, the
        # refresh takes the ordinary upstream-moved path, and the case used
        # to fail with nothing saying why (2026-10-17). Said instead.
        dirty_engine = subprocess.run(
            ['git', '-C', str(ROOT), 'status', '--porcelain', '--', 'tools/',
             '.claude/hooks/', 'templates/'], capture_output=True,
            text=True).stdout.strip()
        r_conv = subprocess.run(
            [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(ROOT), '--from-ref', head],
            capture_output=True, text=True, cwd=str(consumer))
        out_conv = r_conv.stdout + r_conv.stderr
        restored = json.loads(manifest_path.read_text(encoding='utf-8'))
        cases.append(('refresh writes an engine file the manifest is missing even '
                      'when the recorded commit already matches',
                      (consumer / 'tools' / 'build_codeowners.py').is_file()
                      and 'build_codeowners.py' in restored.get('files', []),
                      out_conv[:500]))
        cases.append(('and says why it refreshed rather than claiming nothing to do',
                      'missing' in out_conv and 'nothing to do' not in out_conv,
                      ('COULD NOT BE JUDGED: this checkout has uncommitted engine '
                       'changes, so the seeded copy is not the recorded commit -- '
                       'commit them and run again: ' + dirty_engine[:200])
                      if dirty_engine else out_conv[:500]))

        # A MISSING file is a finding, not a crash. This read_bytes() used to
        # be unguarded, so a refresh that failed earlier in the fixture took
        # the WHOLE harness down with a FileNotFoundError -- 120-odd unrelated
        # checks never ran, and the traceback named a file
        # (build_codeowners.py) that had nothing to do with the cause.
        # Reproduced 2026-09-07 renaming a vendored engine file: fixtures
        # vendor from committed HEAD, so between the rename and its commit the
        # refresh legitimately fails, and this line turned that into a total
        # outage (practice: fail-gracefully).
        # THE MANIFEST TO CHECK IS THE ONE ON DISK NOW, not the snapshot taken
        # at line ~12486 before any of the refreshes above ran. Reading the
        # stale copy asserted "the pre-refresh shas describe the post-refresh
        # files", which is true only while the refresh changes nothing -- and
        # went red the first time a commit actually changed an engine file
        # (2026-09-14, adding precedent_close_detect.py to ENGINE_FILES),
        # naming precedent_vendor_engine.py, which the refresh had correctly
        # replaced and correctly re-recorded. The property worth checking is
        # the engine's postcondition: whatever the manifest records, the file
        # beside it matches (practice: fixture-owns-its-state).
        current = json.loads(manifest_path.read_text(encoding='utf-8'))
        missing = [f for f in current.get('sha256', {})
                   if not (consumer / 'tools' / f).is_file()]
        mismatched = [f for f, h in current.get('sha256', {}).items()
                      if (consumer / 'tools' / f).is_file()
                      and hashlib.sha256((consumer / 'tools' / f).read_bytes()).hexdigest() != h]
        cases.append(('every recorded sha256 matches the file actually written',
                      bool(current.get('sha256')) and not mismatched and not missing,
                      f'mismatched={mismatched} missing={missing}'))
        # …and the tool that rewrites itself is covered by it, which is the
        # one entry a stale read could never have caught.
        cases.append(('…including the vendoring tool, which the refresh '
                      'replaces with a copy of itself',
                      'precedent_vendor_engine.py' in current.get('sha256', {}),
                      f"recorded: {sorted(current.get('sha256', {}))[:4]}…"))

        # -- status(), run from the consumer's OWN vendored copy, against
        # this real checkout, finds zero drift right after seeding --
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(ROOT)], capture_output=True, text=True)
        cases.append(('status() against a real BestPractice checkout finds no drift '
                      'right after seeding', r.returncode == 0, r.stdout + r.stderr))

        # -- the drift-refusal / --force pair, the same property status()
        # depends on and that refresh() must actually honor (a real,
        # reproduced bug: --force used to no-op silently when the upstream
        # commit had not moved -- see refresh()'s own comment) --
        hand_edited = (consumer / 'tools' / 'build_views.py')
        original_bytes = hand_edited.read_bytes()
        hand_edited.write_bytes(original_bytes + b'\n# hand edit\n')

        # refresh() reads from a DISPOSABLE clone, never this repo's own
        # checkout. Handing it str(ROOT) is what moved the CI workspace
        # mid-job: refresh() used to `git checkout SOURCE_BRANCH` in the clone
        # it read FROM, so step 5 left the workspace on SOURCE_BRANCH and
        # every later step in the job silently ran against the wrong commit
        # (see precedent_vendor_engine._source_tools_at's docstring, and
        # check_bootstrap_source_engine_is_functional's own refresh case,
        # which asserts that no longer happens). refresh() is read-only now,
        # so str(ROOT) would no longer corrupt anything -- but a test that
        # vendors FROM a throwaway clone does not depend on that guarantee
        # continuing to hold, which is the point.
        upstream = tmp / 'upstream-clone'
        r = subprocess.run(['git', 'clone', '--quiet', str(ROOT), str(upstream)],
                           capture_output=True, text=True)
        cases.append(('a throwaway clone of this checkout is available to vendor from',
                      r.returncode == 0 and (upstream / '.git').exists(),
                      r.stdout + r.stderr))
        # Give the clone SOURCE_BRANCH by name so _source_tools_at resolves it
        # with no network and no assumption about which refs the caller's
        # checkout carries: on a GitHub Actions runner the workspace holds only
        # the ref under test, so `origin/<SOURCE_BRANCH>` need not exist at all.
        # Read the name from the tool rather than hardcoding it -- its own
        # docstring says SOURCE_BRANCH becomes 'main' once the beta lands.
        m = re.search(r"^SOURCE_BRANCH = '([^']+)'",
                      (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text(encoding='utf-8'),
                      re.M)
        cases.append(("precedent_vendor_engine.py's SOURCE_BRANCH is readable, so this "
                      "fixture cannot drift from it", m is not None, ''))
        source_branch = m.group(1) if m else 'precedent-beta-v01'
        # Repoint the clone's `origin` at ITSELF first. _source_tools_at
        # runs `git fetch origin <SOURCE_BRANCH>` before it resolves
        # anything, so with origin still pointing at this checkout that
        # fetch overwrites the ref set below with whatever commit THIS
        # checkout's local precedent-beta-v01 happens to sit at -- and the
        # fixture silently tested that commit instead of the tree under
        # test. It failed on any working tree ahead of that branch, with a
        # message about a missing tools/precedent_vendor_engine.py that had
        # nothing to do with the property being tested. Self-origin keeps
        # both resolution paths real while making the fetch a no-op.
        subprocess.run(['git', '-C', str(upstream), 'remote', 'set-url',
                        'origin', str(upstream)], capture_output=True, text=True)
        # BOTH refs, deliberately. `git clone` copies this checkout's own
        # refs/heads/* into the clone's refs/remotes/origin/*, and
        # _source_tools_at prefers origin/<SOURCE_BRANCH> over a local
        # branch of that name -- so setting only the local ref left the
        # clone vendoring from whatever commit THIS checkout's local
        # precedent-beta-v01 happens to sit at, not from the tree under
        # test. That made the case below fail on any working tree ahead of
        # (or behind) that branch, with a message about a missing
        # tools/precedent_vendor_engine.py that had nothing to do with the
        # property being tested. Both refs point at the clone's HEAD, so
        # this fixture tests THIS tree whichever resolution path wins.
        for ref in (f'refs/heads/{source_branch}',
                    f'refs/remotes/origin/{source_branch}'):
            subprocess.run(['git', '-C', str(upstream), 'update-ref', ref, 'HEAD'],
                           capture_output=True, text=True)
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream)], capture_output=True, text=True)
        cases.append(('refresh() without --force refuses a hand-edited vendored file',
                      r.returncode != 0 and 'hand-edited' in (r.stdout + r.stderr),
                      r.stdout + r.stderr))
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream), '--force'], capture_output=True, text=True)
        cases.append(('refresh() with --force actually overwrites the hand-edited file '
                      '(not a silent no-op), even when the upstream commit has not moved',
                      r.returncode == 0 and hand_edited.read_bytes() == original_bytes,
                      r.stdout + r.stderr))

        # -- and again from a clone with NO origin/<SOURCE_BRANCH> ref at all,
        # which is exactly what a GitHub Actions workspace yields: the runner
        # checks out only the ref under test, so a clone taken from it has no
        # remote-tracking branch for SOURCE_BRANCH. refresh() must fall back to
        # the local branch of that name. Regression test for a real CI failure
        # (2026-09-06): "precedent-beta-v01 @ origin/prece has no
        # tools/build_views.py" -- plain `git rev-parse <missing-ref>` exits
        # non-zero but ECHOES THE REF NAME on stdout, and _git() keeps stdout
        # while discarding the exit code, so the `or <fallback>` never fired and
        # the ref name was carried forward as if it were a commit hash. Forced
        # here rather than left to the environment, so both resolution paths are
        # covered wherever this runs.
        subprocess.run(['git', '-C', str(upstream), 'update-ref', '-d',
                        f'refs/remotes/origin/{source_branch}'],
                       capture_output=True, text=True)
        cases.append(('the throwaway clone really has no origin/<SOURCE_BRANCH> ref',
                      subprocess.run(['git', '-C', str(upstream), 'rev-parse', '--verify',
                                      '--quiet', f'origin/{source_branch}'],
                                     capture_output=True, text=True).returncode != 0, ''))
        # Assert on RESOLUTION, not on the file being rewritten: the first
        # refresh above already replaced the consumer's own vendored
        # precedent_vendor_engine.py with SOURCE_BRANCH's copy (the tool
        # travels with the engine it defines, by design), so round two runs
        # upstream's semantics, not this working tree's -- and upstream may
        # legitimately short-circuit with "already current". What must hold
        # either way is that SOURCE_BRANCH resolved to a real commit: the bug
        # this guards produced a hard failure naming a truncated ref NAME
        # where a hash belonged.
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream), '--force'], capture_output=True, text=True)
        out = r.stdout + r.stderr
        cases.append(('refresh() still resolves SOURCE_BRANCH from a clone with no '
                      'origin/<SOURCE_BRANCH>, falling back to the local branch instead '
                      'of carrying the ref NAME forward as a commit',
                      r.returncode == 0
                      and 'invalid object name' not in out
                      and f'@ origin/{source_branch[:12]}' not in out,
                      out))

        # -- the consumer's OWN vendored precedent_sync_views.py, run the way
        # a real consumer's AGENTS.md documents it (--repo .), resolves all
        # three sources and materializes + regenerates the loader block --
        r = subprocess.run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.'],
                           capture_output=True, text=True, cwd=str(consumer),
                           env=env_iso)
        cases.append(('precedent_sync_views.py --repo . resolves and materializes '
                      'cleanly', r.returncode == 0, r.stdout + r.stderr))

        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8') if (consumer / 'AGENTS.md').exists() else ''
        cases.append(('the regenerated AGENTS.md loader block names a real universal '
                      'practice (proves the universal source, not just the fixtures, '
                      'flowed through)', 'verify-postcondition' in agents_text, agents_text[:300]))

        team_practice = consumer / 'practices' / 'consumer-fixture-team.md'
        local_practice = consumer / 'practices' / 'consumer-fixture-local.md'
        cases.append(('the team fixture practice was materialized', team_practice.is_file(), ''))
        cases.append(('the repo-local fixture practice was materialized', local_practice.is_file(), ''))

        # -- precedent_gate.py / precedent_paths.py / precedent_show.py, run
        # IN PLACE (no --repo) against the materialized tree, same as the
        # source-set case's own rigor --
        r = subprocess.run([sys.executable, 'tools/precedent_gate.py', '--list'],
                           capture_output=True, text=True, cwd=str(consumer),
                           env=env_iso)
        cases.append(('the vendored precedent_gate.py lists the real (trimmed) gate '
                      'vocabulary against the materialized tree',
                      r.returncode == 0 and 'merge' in r.stdout, r.stdout + r.stderr))

        r = subprocess.run([sys.executable, 'tools/precedent_paths.py', 'team-only/x.md'],
                           capture_output=True, text=True, cwd=str(consumer),
                           env=env_iso)
        cases.append(('the vendored precedent_paths.py matches the team fixture by its '
                      'real applies_to glob', r.returncode == 0
                      and 'consumer-fixture-team' in r.stdout, r.stdout + r.stderr))

        r = subprocess.run([sys.executable, 'tools/precedent_show.py', 'consumer-fixture-local'],
                           capture_output=True, text=True, cwd=str(consumer),
                           env=env_iso)
        cases.append(("the vendored precedent_show.py returns the repo-local fixture's "
                      "real Rule text", r.returncode == 0
                      and 'repo-local fixture rule' in r.stdout, r.stdout + r.stderr))

        # -- a second sync, unchanged, is a clean --check (idempotency, and
        # the exact invocation a consumer's own session-start documents) --
        r = subprocess.run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.', '--check'],
                           capture_output=True, text=True, cwd=str(consumer),
                           env=env_iso)
        cases.append(('a second, unchanged sync passes --check cleanly (idempotent)',
                      r.returncode == 0, r.stdout + r.stderr))

    finally:
        if saved_home is None:
            os.environ.pop('HOME', None)
        else:
            os.environ['HOME'] = saved_home
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the vendored engine\'s "consumer" kind is real and functional against a real '
          f'four-source pipeline, not just present ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_vendor_engine_hook_drift_respects_adapters():
    """A declared source can own a hook file at the same destination this
    engine vendors -- precedent-individual declaring its own
    `bootstrap/freshness-guard.sh` as an adapter to
    `.claude/hooks/freshness-guard.sh` is the real case
    (precedent_materialize.py's ADAPTER_DECL_KEY). Before
    `_adapter_claimed_paths` existed, `status`/`refresh` compared that
    on-disk file -- legitimately overwritten by the source's own adapter --
    against this engine's OWN `hooks_sha256` and reported the divergence as
    a hand-edit; `refresh` refused outright. Reproduced verbatim in a real
    consumer repo, 2026-09-15.

    Fixture is deliberately NOT a full `seed` run (network/git resolution
    this property does not need): only precedent_vendor_engine.py itself is
    copied to `<consumer>/tools/`, so ROOT inside the copy resolves to
    `<consumer>` (practice: fixture-owns-its-state -- nothing here reads a
    real clone's git history, so nothing needs one).

    Each scenario below gets its OWN fresh consumer directory rather than
    reusing one across mutations: `refresh` really does rewrite the whole
    vendored tools/ tree from this checkout, and running it in a directory a
    later CONTROL case still reads from made that case's own
    `precedent_vendor_engine.py` copy read as untracked -- fixture
    contamination masquerading as a result (practice: fixture-owns-its-state
    again, one level up: the STATE a later case reads must be what THAT case
    set up, not what an earlier case left behind)."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-hook-adapter-'))
    cases = []
    try:
        engine_tool_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        engine_tool_hash = hashlib.sha256(engine_tool_bytes).hexdigest()
        # The hook as this engine last vendored it, and the hash it recorded.
        engine_hook_text = '#!/bin/sh\n# BestPractice-bundled freshness-guard\n'
        engine_hash = hashlib.sha256(engine_hook_text.encode('utf-8')).hexdigest()
        # The source's own adapter copy actually on disk -- different bytes,
        # different hash, exactly what precedent_materialize.py's adapters
        # mechanism writes on its next sync.
        adapter_hook_text = '#!/bin/sh\n# precedent-individual bootstrap/freshness-guard\n'
        adapter_hash16 = hashlib.sha256(adapter_hook_text.encode('utf-8')).hexdigest()[:16]

        def make_consumer(name, adapters):
            """A fresh consumer directory: this engine's own vendor tool
            (recorded in its manifest, so it is never itself flagged
            UNTRACKED ENGINE FILE and does not confound the assertions
            below), the mismatched hook, and precedent_materialize.py's own
            MANIFEST.json with the given `adapters` list (or no MANIFEST.json
            at all when `adapters` is None)."""
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / '.claude' / 'hooks').mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_tool_bytes)
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': 'consumer', 'source_commit': 'deadbeef',
                'files': ['precedent_vendor_engine.py'],
                'sha256': {'precedent_vendor_engine.py': engine_tool_hash},
                'hook_files': ['freshness-guard.sh'],
                'hooks_sha256': {'freshness-guard.sh': engine_hash},
            }), encoding='utf-8')
            (consumer / '.claude' / 'hooks' / 'freshness-guard.sh').write_text(
                adapter_hook_text, encoding='utf-8')
            if adapters is not None:
                (consumer / 'MANIFEST.json').write_text(json.dumps({
                    'generated_by': 'tools/precedent_materialize.py',
                    'sources': [], 'resident': {}, 'practices': [], 'checks': [],
                    'adapters': adapters, 'withheld': [], 'excluded_engine_dev': [],
                }), encoding='utf-8')
            return consumer

        def vendor_status(consumer):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                 'status', str(ROOT)],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        # -- claimed: a declared source's adapter owns this exact path --
        claimed_adapters = [
            {'path': '.claude/hooks/freshness-guard.sh', 'source': 'precedent-individual',
             'sha256_16': adapter_hash16, 'executable': True},
        ]
        consumer_claimed = make_consumer('claimed', claimed_adapters)
        rc_claimed, out_claimed = vendor_status(consumer_claimed)
        cases.append(("a hook a declared source's adapter owns is not reported as LOCAL "
                      "DRIFT even though its bytes differ from this engine's own record",
                      'LOCAL DRIFT' not in out_claimed, out_claimed[:500]))
        cases.append(("...and status still exits 0 on that divergence alone",
                      rc_claimed == 0, out_claimed[:500]))
        cases.append(("...and status names the claiming source instead of staying silent",
                      'precedent-individual' in out_claimed and 'freshness-guard.sh' in out_claimed,
                      out_claimed[:500]))

        # -- refresh: a SEPARATE fresh consumer, since a real refresh rewrites
        # the whole vendored tools/ tree from this checkout --
        consumer_refresh = make_consumer('refresh', claimed_adapters)
        r_refresh = subprocess.run(
            [sys.executable, str(consumer_refresh / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(ROOT)],
            capture_output=True, text=True, cwd=str(consumer_refresh))
        out_refresh = r_refresh.stdout + r_refresh.stderr
        cases.append(('refresh does not refuse over an adapter-owned divergence -- no '
                      '"hand-edited" FAIL demanding --force',
                      'hand-edited since the last seed/refresh' not in out_refresh,
                      out_refresh[:500]))

        # -- CONTROL: same mismatched bytes, no declared claim on the path.
        # Restores the exact pre-fix behavior, proving the assertions above
        # test the adapter check and not something that never fires
        # (practice: control-asserts-which-failure).
        consumer_bare = make_consumer('bare', [])
        rc_bare, out_bare = vendor_status(consumer_bare)
        cases.append(('CONTROL: the same mismatched hook, with no adapter claiming it, IS '
                      'reported as LOCAL DRIFT -- proves the exemption above is keyed on '
                      'the claim, not on hook files in general',
                      rc_bare == 1 and 'LOCAL DRIFT' in out_bare
                      and 'hand-edited' in out_bare, out_bare[:500]))

        # -- CONTROL: no MANIFEST.json at all (never materialized) behaves
        # the same as "no claim" -- the pre-existing behavior for a repo
        # that has not adopted the adapters mechanism.
        consumer_none = make_consumer('none', None)
        rc_none, out_none = vendor_status(consumer_none)
        cases.append(('CONTROL: with no MANIFEST.json at all, the same mismatch is still '
                      'reported as LOCAL DRIFT -- absence of the file is not mistaken for '
                      'a claim',
                      rc_none == 1 and 'LOCAL DRIFT' in out_none
                      and 'hand-edited' in out_none, out_none[:500]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f"a declared source's own adapter, not this engine, owns a hook it claims -- "
          f"status/refresh stop reading that as a hand-edit ({len(cases)} stated cases)",
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_vendor_engine_refresh_converges_with_adapter_owned_hooks():
    """Two refreshes in a row at one commit: the second is a no-op, even
    when a declared source's adapters own some of the hooks this repo wires.

    THE BUG. refresh() decided whether hooks were missing from its own
    computation of the wanted set, which left out the adapter exclusion
    _write_hook_files applies. commit-identity.sh and freshness-guard.sh,
    owned by the individual source's adapters in a real consumer, were
    skipped by the writer, never recorded in `hook_files`, and still counted
    as missing -- so every refresh printed the "one-time catch-up" NOTICE and
    rewrote every engine file at an unchanged commit. Reported 2026-09-25
    from a consumer's "Update Vendors" run; both questions now ask
    _vendorable_hook_names.

    Same fixture shape as check_vendor_engine_refreshes_ci_workflow_files
    (one fresh consumer per scenario, --from-ref to a ref carrying this
    working tree). The CONTROL drops the adapter claim, so the same wiring
    vendors all three hooks and still converges -- proving the fixture's
    settings.json is actually read, and that the no-op is not simply
    "hooks are never looked at"."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-hook-converge-'))
    cases = []
    try:
        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        owned = ('commit-identity.sh', 'freshness-guard.sh')
        vendored = 'stop-git-check.sh'
        adapter_text = '#!/bin/sh\n# the individual source\'s own copy\n'

        def make_consumer(name, claimed):
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            hooks = consumer / '.claude' / 'hooks'
            hooks.mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': 'consumer', 'source_commit': 'deadbeef',
                'files': ['precedent_vendor_engine.py'],
                'sha256': {'precedent_vendor_engine.py':
                           hashlib.sha256(engine_bytes).hexdigest()},
            }), encoding='utf-8')
            (consumer / '.claude' / 'settings.json').write_text(json.dumps({
                'hooks': {'SessionStart': [{'hooks': [
                    {'type': 'command',
                     'command': f'$CLAUDE_PROJECT_DIR/.claude/hooks/{n}'}
                    for n in (*owned, vendored)]}]},
            }), encoding='utf-8')
            if claimed:
                for n in owned:
                    (hooks / n).write_text(adapter_text, encoding='utf-8')
                (consumer / 'MANIFEST.json').write_text(json.dumps({
                    'generated_by': 'tools/precedent_materialize.py',
                    'adapters': [{'path': f'.claude/hooks/{n}',
                                  'source': 'precedent-individual'} for n in owned],
                }), encoding='utf-8')
            return consumer

        ref = _ref_including_worktree(ROOT)

        def run_refresh(consumer):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--from-ref', ref],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        def snapshot(consumer):
            return {str(f.relative_to(consumer)): (f.stat().st_mtime_ns, f.read_bytes())
                    for f in sorted(consumer.rglob('*'))
                    if f.is_file() and '__pycache__' not in f.parts}

        for label, claimed in (('adapter-owned', True), ('CONTROL: no adapter claim', False)):
            c = make_consumer(label.split(':')[0].replace(' ', '-'), claimed)
            rc1, out1 = run_refresh(c)
            before = snapshot(c)
            rc2, out2 = run_refresh(c)
            after = snapshot(c)
            changed = sorted(k for k in after if before.get(k) != after[k])
            manifest = json.loads(
                (c / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
            detail = f'first: rc={rc1} {out1[-600:]} || second: rc={rc2} {out2[-600:]}'
            cases.append((f'{label}: the first refresh succeeds', rc1 == 0, detail))
            cases.append((f'{label}: the second refresh at the same commit says '
                          f'"nothing to do"', rc2 == 0 and 'nothing to do' in out2, detail))
            cases.append((f'{label}: ...and prints no missing-hooks NOTICE',
                          'vendored hooks are missing' not in out2, detail))
            cases.append((f'{label}: ...and touches no file', not changed,
                          f'changed: {changed[:10]} -- {detail}'))
            # Not an exact list since 2026-09-25: a consumer refresh now also
            # wires and vendors every hook on HOOK_WIRING's consumer list
            # (check_vendor_engine_wires_a_new_hook_into_an_installed_repo).
            # What this test owns is the adapter exclusion, so that is what
            # it asserts.
            got = set(manifest.get('hook_files') or [])
            ok = (vendored in got and not (set(owned) & got)) if claimed \
                else set((*owned, vendored)) <= got
            cases.append((f'{label}: hook_files records the wired hooks this engine '
                          f'vendored and {"none" if claimed else "all"} of the '
                          f'adapter-owned ones', ok,
                          f"hook_files={manifest.get('hook_files')}"))
            if claimed:
                cases.append((f'{label}: the adapter-owned hooks keep the source\'s bytes',
                              all((c / '.claude' / 'hooks' / n).read_text(encoding='utf-8')
                                  == adapter_text for n in owned), detail))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f"refresh converges when a source's adapters own some wired hooks -- a second "
          f"refresh at the same commit is a no-op ({len(cases)} stated cases)",
          not bad,
          '; '.join(f"{n} -- {d[:900]}" for n, d in bad))


def check_vendor_engine_refreshes_ci_workflow_files():
    """"Update Vendors" refreshing tools/ and .claude/hooks/*.sh but never
    .github/workflows/*.yml is the bug this closes -- see
    precedent_vendor_engine.py's CI_WORKFLOW_TEMPLATES block (2026-09-18)
    and vendor-update-runbook.md step 3's own paragraph on it. Mirrors
    check_vendor_engine_hook_drift_respects_adapters' fixture shape: only
    precedent_vendor_engine.py itself is copied into each fake consumer
    (practice: fixture-owns-its-state -- nothing here needs a real seed or
    git history beyond what ROOT, the real upstream clone under test,
    already carries), and each scenario gets its OWN fresh consumer
    directory, for the same reason that test's docstring gives: a real
    refresh rewrites the whole vendored tools/ tree from this checkout, and
    a later CONTROL reading a directory an earlier case already refreshed
    would be reading contamination, not its own result.

    `kind: consumer` throughout, so CI_WORKFLOW_TEMPLATES['consumer']
    applies: one file, .github/workflows/leak-gate.yml, from
    leak-gate.yml.template.

    IT USED TO BE bestpractice-docs.yml, FROM doc-lint.yml.template, and
    that template was retired on 2026-09-21 when the Markdown lint left CI
    entirely. Repointed rather than deleted: what this fixture tests is the
    REFRESH MECHANISM -- does a vendored workflow get rewritten, left
    alone, or refused when hand-edited -- which is about any consumer CI
    workflow and never was about Markdown. Deleting it along with its
    subject would have quietly dropped coverage of the mechanism that
    propagates every CI workflow change to every installed repo."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ci-workflow-'))
    cases = []
    rel = '.github/workflows/leak-gate.yml'
    try:
        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        engine_hash = hashlib.sha256(engine_bytes).hexdigest()
        real_template = (ROOT / 'templates' / 'github-actions' /
                         'leak-gate.yml.template').read_bytes()
        real_hash = hashlib.sha256(real_template).hexdigest()
        # A stand-in for "whatever this file looked like when it was last
        # vendored" -- deliberately NOT real_template's bytes, so a refresh
        # that actually rewrote the file is distinguishable from one that
        # left it alone by content, not just by a hash comparison that could
        # coincidentally already match.
        stub = b'name: stub\n# an older vendored copy\n'
        stub_hash = hashlib.sha256(stub).hexdigest()
        edited = b'name: hand-edited\n# a real repo customized this\n'

        def make_consumer(name, wf_bytes, ci_recorded):
            """A fresh consumer: this engine's own vendor tool (recorded in
            its manifest, so it is never itself flagged UNTRACKED ENGINE
            FILE or LOCAL DRIFT and does not confound the assertions
            below), and one CI workflow file. `ci_recorded` is the
            manifest's ci_workflows_sha256 dict, or None to simulate a repo
            vendored before this feature existed (no such key at all)."""
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / '.github' / 'workflows').mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            manifest = {
                'kind': 'consumer', 'source_commit': 'deadbeef',
                'files': ['precedent_vendor_engine.py'],
                'sha256': {'precedent_vendor_engine.py': engine_hash},
            }
            if ci_recorded is not None:
                manifest['ci_workflow_files'] = sorted(ci_recorded)
                manifest['ci_workflows_sha256'] = ci_recorded
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(manifest), encoding='utf-8')
            if wf_bytes is not None:
                (consumer / rel).write_bytes(wf_bytes)
            # A git repo with everything committed, as every real consumer
            # is: since 2026-09-27 a consumer's refresh replaces a workflow
            # only when git holds its content (CI_CONVERGES_KINDS).
            genv = dict(os.environ, GIT_AUTHOR_NAME='t',
                        GIT_AUTHOR_EMAIL='harness@example.com',
                        GIT_COMMITTER_NAME='t',
                        GIT_COMMITTER_EMAIL='harness@example.com')
            for argv in (['init', '-q'], ['add', '-A'],
                         ['commit', '-qm', 'base']):
                subprocess.run(['git', '-C', str(consumer), *argv], env=genv,
                               capture_output=True)
            return consumer

        # Computed once, not the literal 'HEAD': this fixture tests a
        # mechanism landing in the SAME change as this test, so ROOT's own
        # origin/precedent-beta-v01 has not necessarily picked it up yet --
        # exactly the gap --from-ref exists to close (see
        # _source_tools_at's own docstring, and every other fixture here
        # that vendors a brand-new mechanic under test:
        # check_vendor_engine_consumer_case and
        # check_bootstrap_source_engine_is_functional both do the same).
        # Without it, a run before this PR reaches origin/precedent-beta-v01
        # vendors the OLD tool, the self-replacing second pass then runs
        # THAT copy -- missing this feature entirely -- against a manifest
        # the first (new) pass already updated, and the two passes
        # disagree. Literal 'HEAD' has the identical failure mode one
        # commit earlier: it misses the mechanism until this change is
        # actually committed, which _ref_including_worktree closes too
        # (see its own docstring).
        ref = _ref_including_worktree(ROOT)

        def run_refresh(consumer, extra=()):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--from-ref', ref, *extra],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        def manifest_of(consumer):
            return json.loads(
                (consumer / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))

        # -- A: matches the manifest (never hand-edited), differs from the
        # CURRENT template -- refresh() rewrites it and updates the hash --
        a = make_consumer('stale', stub, {rel: stub_hash})
        rc_a, out_a = run_refresh(a)
        cases.append(('a CI workflow file that matches its own manifest record but '
                      'differs from the current template is rewritten to that '
                      'template', (a / rel).read_bytes() == real_template, out_a[:800]))
        cases.append(('...and the manifest is updated to the NEW hash, not left '
                      'pointing at the stale one',
                      manifest_of(a).get('ci_workflows_sha256', {}).get(rel) == real_hash,
                      out_a[:800]))
        cases.append(('...and refresh says which CI workflow file it refreshed '
                      '(control-asserts-which-failure: the specific message, not just '
                      'a clean exit)',
                      rc_a == 0 and 'refreshed' in out_a and rel in out_a, out_a[:800]))

        # -- B: differs from the manifest record -- a hand-edit. Until
        # 2026-09-27 refresh refused the whole run over it. A consumer's CI
        # now converges to upstream (CI_CONVERGES_KINDS): the file is
        # replaced with the template, and the refresh says so --
        b = make_consumer('edited', edited, {rel: stub_hash})
        rc_b, out_b = run_refresh(b)
        cases.append(('a hand-edited CI workflow file in a consumer is replaced '
                      'with the current template, not refused',
                      rc_b == 0 and (b / rel).read_bytes() == real_template
                      and 'hand-edited since the last seed/refresh' not in out_b,
                      out_b[:800]))
        cases.append(('...and the refresh says it replaced it',
                      'CI workflow replaced: ' + rel in out_b, out_b[:800]))

        # -- B, NEGATIVE: the same hand-edit, never committed, is kept: its
        # content exists nowhere else (practice: repair-cannot-discard-work).
        b_dirty = make_consumer('edited-dirty', stub, {rel: stub_hash})
        (b_dirty / rel).write_bytes(edited)
        rc_bd, out_bd = run_refresh(b_dirty)
        cases.append(('NEGATIVE: an UNCOMMITTED hand edit is kept, and named '
                      'under Left for you',
                      rc_bd == 0 and (b_dirty / rel).read_bytes() == edited
                      and 'uncommitted edits' in out_bd, out_bd[:800]))

        # -- B, NEGATIVE: a hand edit that runs a script the local push
        # check does not run is held back, naming the script, so nothing
        # needed is lost --
        b_needed = make_consumer(
            'edited-needed',
            b'name: hand-edited\njobs:\n  j:\n    steps:\n'
            b'      - run: python3 tools/our_special.py\n', {rel: stub_hash})
        rc_bn, out_bn = run_refresh(b_needed)
        cases.append(('NEGATIVE: a hand edit running a script nothing local '
                      'runs is kept, and the script is named',
                      rc_bn == 0 and b'our_special.py' in (b_needed / rel).read_bytes()
                      and 'our_special.py' in out_bn and 'LEFT ALONE' in out_bn,
                      out_bn[:800]))

        # -- C: no manifest record at all -- a repo vendored before CI
        # workflows were tracked, or a hand-made copy. It used to get a
        # baseline and a second refresh; a consumer's is replaced now --
        c = make_consumer('catchup', stub, None)
        rc_c, out_c = run_refresh(c)
        cases.append(('an untracked CI workflow file in a consumer is replaced '
                      'on the first refresh, and tracked',
                      rc_c == 0 and (c / rel).read_bytes() == real_template
                      and manifest_of(c).get('ci_workflows_sha256', {}).get(rel)
                      == real_hash, out_c[:800]))
        rc_c2, out_c2 = run_refresh(c)
        cases.append(('CONTROL: a second refresh finds nothing to do for it',
                      rc_c2 == 0 and (c / rel).read_bytes() == real_template
                      and 'CI workflow replaced' not in out_c2, out_c2[:800]))

        # -- D: CI disabled (no workflow file installed at all) -- refresh
        # neither writes nor complains about it --
        d = make_consumer('disabled', None, None)  # no workflow file written at all
        rc_d, out_d = run_refresh(d)
        cases.append(('CONTROL: a consumer with no CI workflow file installed at all '
                      'is neither refused nor reported by the new mechanism -- '
                      'correctly absent, same as ci_workflows disabled',
                      rc_d == 0 and 'hand-edited' not in out_d and rel not in out_d,
                      out_d[:800]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'"Update Vendors" now refreshes an already-installed CI workflow file '
          f'body, not just tools/ and .claude/hooks/*.sh ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_template_history_includes_a_version_made_in_a_merge():
    """precedent_vendor_engine._read_template_sources lists every version a
    template has had, so an unedited consumer copy of ANY past version is
    recognised as stock. A version introduced by a merge commit was missing:
    `git log --raw` shows a merge no diff, so a consumer holding exactly that
    version read as locally edited and was never updated (very deep check,
    2026-09-28). Planted: a scratch repo whose template is edited only
    inside a merge commit."""
    import shutil, tempfile
    import precedent_vendor_engine as pve
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='template-history-merge-'))
    cases = []
    try:
        repo = tmp / 'src'
        (repo / 'templates').mkdir(parents=True)
        env = dict(os.environ, GIT_AUTHOR_NAME='fixture',
                   GIT_AUTHOR_EMAIL='fixture@invalid',
                   GIT_COMMITTER_NAME='fixture',
                   GIT_COMMITTER_EMAIL='fixture@invalid')

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a], env=env,
                                  capture_output=True, text=True, check=True
                                  ).stdout.strip()
        git('init', '-q', '-b', 'main')
        git('config', 'commit.gpgsign', 'false')
        tpl = repo / 'templates' / 'bootstrap.sh'
        tpl.write_text('#!/bin/bash\necho one\n', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'one')
        git('checkout', '-q', '-b', 'side')
        (repo / 'other.txt').write_text('x\n', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'side')
        git('checkout', '-q', 'main')
        git('merge', '-q', '--no-ff', '--no-commit', 'side')
        merged = b'#!/bin/bash\necho made in the merge\n'
        tpl.write_bytes(merged)
        git('add', '-A'); git('commit', '-q', '-m', 'merge with an edit')
        out = tmp / 'out'
        pve._read_template_sources(repo, 'HEAD', 'consumer', out)
        hist = json.loads((out / pve._TEMPLATE_HISTORY_NAME)
                          .read_text(encoding='utf-8'))
        blobs = set(hist.get('templates/bootstrap.sh') or ())
        cases.append(('the version a merge commit introduced is in the '
                      'history', pve._git_blob_id(merged) in blobs,
                      repr(sorted(blobs))))
        cases.append(('...and so is the ordinary earlier version',
                      pve._git_blob_id(b'#!/bin/bash\necho one\n') in blobs,
                      repr(sorted(blobs))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'template history counts a version made inside a merge commit '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_vendor_engine_refreshes_agents_md_sections():
    """Whatever the AGENTS.md template wrote at install was frozen from then
    on: refresh rewrote only the generated loader block, so no template fix
    reached an installed repo and nothing reported the drift -- see
    precedent_vendor_engine.py's AGENTS_MD_TEMPLATES block (2026-09-25) for
    the measured case. Also pins RETIRED_BRANCH_NAMES' report.

    THE FIXTURE OWNS ITS UPSTREAM (practice: fixture-owns-its-state), as
    check_vendor_engine_refreshes_bootstrap_sh's does: one synthetic commit
    on top of this working tree whose only change is a new, distinctive
    bullet in the loader template's "### Two check levels" section, so OLD
    and CUR are known whatever the real template picks up later.

    The discriminating cases are the edited section (never overwritten,
    --force included, and the report names the exact bullet it lacks), the
    missing section (reported, never written in, and quiet on the next
    run), and the untouched neighbours: a rewrite that moved one byte
    outside its own section would fail them
    (practice: control-asserts-which-failure)."""
    import shutil, tempfile
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-agents-md-sections-'))
    cases = []
    src = 'templates/AGENTS.md.loader.template'
    key = '### Two check levels'
    marker = 'FIXTURE BULLET ADDED UPSTREAM'
    try:
        base = _ref_including_worktree(ROOT)
        old = subprocess.run(['git', '-C', str(ROOT), 'show', f'{base}:{src}'],
                             capture_output=True, check=True).stdout.decode()
        # Anchored on the NEXT section's heading, not on a bullet's wording,
        # which changes whenever someone rewords "Two check levels" (it did
        # on 2026-09-25, the day this fixture landed).
        anchor = '\n\n### Build-environment gotchas'
        assert old.count(anchor) == 1, 'template anchor moved; repoint this fixture'
        added = (f'\n- **{marker}** — a bullet every stale copy of this '
                 f'section lacks, and nothing else does.')
        cur = old.replace(anchor, added + anchor)

        with tempfile.TemporaryDirectory(prefix='precedent-fixture-index-') as idx:
            env = dict(os.environ, GIT_INDEX_FILE=str(pathlib.Path(idx) / 'index'),
                       GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                       GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')

            def git(*args, data=None):
                return subprocess.run(['git', '-C', str(ROOT), *args], input=data,
                                      capture_output=True, env=env, check=True
                                      ).stdout.decode().strip()
            git('read-tree', base)
            blob = git('hash-object', '-w', '--stdin', data=cur.encode())
            git('update-index', '--cacheinfo', f'100644,{blob},{src}')
            ref = git('commit-tree', git('write-tree'), '-p', base, '-m',
                      'verify_harness: AGENTS.md section fixture (never pushed)')

        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        sha = lambda b: hashlib.sha256(b).hexdigest()
        subs = {'<precedent upstream URL>': pve.SOURCE_REPO, '<default-branch>': 'trunk'}
        stock_old = pve._instantiate(old, subs)
        # What a real install leaves: the generated block filled in (here
        # with a heading and a retired branch name of its own, neither of
        # which is any section's or report's business) and one section the
        # repo has made its own.
        generated = ('<!-- BEGIN GENERATED: precedent-loader -->\n'
                     '## Resident block\n\nLinks to blob/precedent-beta-v01/x.\n'
                     '<!-- END GENERATED -->')
        repo_old = stock_old.replace(
            '<!-- BEGIN GENERATED: precedent-loader -->\n<!-- END GENERATED -->',
            generated).replace(
            '| Open items: analyses, verifications, decisions | [TODO.md](TODO.md) |\n',
            '| Open items: analyses, verifications, decisions | [TODO.md](TODO.md) |\n'
            '| A row this repo added | `ours.md` |\n')
        assert generated in repo_old and 'A row this repo added' in repo_old, \
            'template shape moved; repoint this fixture'

        def section_of(text, k=key):
            lines = text.split('\n')
            spans = [(f, e) for kk, f, e in pve._md_sections(text) if kk == k]
            return pve._section_text(lines, *spans[0]) if spans else None

        old_sec = section_of(stock_old)
        cur_sec = pve._instantiate(section_of(cur), subs)

        def make_consumer(name, agents, recorded):
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            manifest = {'kind': 'consumer', 'source_commit': 'deadbeef',
                        'files': ['precedent_vendor_engine.py'],
                        'sha256': {'precedent_vendor_engine.py': sha(engine_bytes)}}
            if recorded is not None:
                manifest['agents_md_sections_sha256'] = recorded
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(manifest), encoding='utf-8')
            (consumer / 'precedent.json').write_text(
                json.dumps({'base_branch': 'trunk'}), encoding='utf-8')
            if agents is not None:
                (consumer / 'AGENTS.md').write_text(agents, encoding='utf-8')
            return consumer

        def run_refresh(consumer, extra=()):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--from-ref', ref, *extra],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        def recorded_of(consumer):
            m = json.loads((consumer / 'tools' / 'ENGINE_MANIFEST.json')
                           .read_text(encoding='utf-8'))
            return m.get('agents_md_sections_sha256') or {}

        def agents(consumer):
            return (consumer / 'AGENTS.md').read_text(encoding='utf-8')

        want_after = repo_old.replace(old_sec, cur_sec)
        assert want_after != repo_old

        # -- A: unedited (matches its recorded baseline), template moved --
        a = make_consumer('recorded-stale', repo_old,
                          {key: sha(old_sec.encode())})
        rc, out = run_refresh(a)
        cases.append(('an unedited section whose baseline is recorded is '
                      'rewritten to the current template, and not one byte '
                      'outside it moves -- the generated block and the '
                      'section this repo edited included',
                      rc == 0 and agents(a) == want_after, failure_detail(out, 900)))
        cases.append(('...its new baseline is the current section, and the '
                      'refresh names what it rewrote',
                      recorded_of(a).get(key) == sha(cur_sec.encode())
                      and "section(s) up to the current template" in out
                      and repr(key) in out, failure_detail(out, 900)))

        # -- B: nothing recorded, identical to a PAST template -- every
        # install before this date, the one-time catch-up --
        b = make_consumer('untracked-stale', repo_old, None)
        rc, out = run_refresh(b)
        cases.append(('an untracked section identical to a past version of '
                      'the template is recognised as stock and brought up to date',
                      rc == 0 and agents(b) == want_after
                      and recorded_of(b).get(key) == sha(cur_sec.encode()),
                      failure_detail(out, 900)))
        cases.append(('...a section already current, <default-branch> '
                      'substituted from precedent.json, is recorded as it is',
                      bool(recorded_of(b).get('## Git / workflow'))
                      and 'origin/trunk' in agents(b), failure_detail(out, 600)))
        cases.append(('...and the section this repo edited, lacking nothing, '
                      'is left alone, unrecorded and off the list',
                      'A row this repo added' in agents(b)
                      and not recorded_of(b).get(
                          '## Where things are (quick index — check here '
                          'BEFORE searching the repo)')
                      and 'AGENTS.md "## Where things are' not in out,
                      failure_detail(out, 900)))

        # -- C: edited section, baseline recorded --
        edited = repo_old.replace(old_sec, old_sec + '\n- A check this repo added.')
        for name, label, extra in (('edited', '', ()),
                                   ('edited-forced', ' with --force', ('--force',))):
            c = make_consumer(name, edited, {key: sha(old_sec.encode())})
            rc, out = run_refresh(c, extra)
            cases.append((f'an edited section is never overwritten{label}',
                          agents(c) == edited, failure_detail(out, 900)))
            report = [ln for ln in out.splitlines() if f'{src}:' in ln]
            cases.append((f'...the refresh still succeeds and reports it '
                          f'DIVERGED, naming exactly the missing upstream '
                          f'bullet{label}',
                          rc == 0 and f'DIVERGED: AGENTS.md "{key}"' in out
                          and len(report) == 1 and marker in report[0]
                          and report[0].endswith('-- missing'),
                          '\n'.join(report) or failure_detail(out, 1200)))
            cases.append((f'...its baseline is NOT moved onto the edit{label}',
                          recorded_of(c).get(key) == sha(old_sec.encode()),
                          failure_detail(out, 400)))
            cases.append((f'...and it is on the Left-for-you list{label}',
                          f'  - AGENTS.md "{key}": diverged from {src} and lacks 1'
                          in out, failure_detail(out, 900)))

        # -- D: the section is missing altogether --
        lacking = repo_old.replace(old_sec + '\n', '')
        assert section_of(lacking) is None
        d = make_consumer('missing-section', lacking, None)
        rc, out = run_refresh(d)
        cases.append(('a missing section is reported and put on the list, '
                      'never written in',
                      rc == 0 and agents(d) == lacking
                      and f'MISSING: AGENTS.md has no "{key}" section' in out
                      and f'  - AGENTS.md "{key}": the template has this section' in out,
                      failure_detail(out, 900)))
        cases.append(('...recorded as absent, so the next refresh leaves it '
                      'unsaid and off the list',
                      key in recorded_of(d) and recorded_of(d)[key] is None,
                      json.dumps(recorded_of(d))[:400]))
        rc, out = run_refresh(d)
        # A consuming repository's Update Vendors, 2026-10-12: the NOTE that
        # used to stand here came back on every update after the person had
        # been told once.
        cases.append(('...which it does: nothing about the section at all, '
                      'and the file still untouched',
                      rc == 0 and agents(d) == lacking and 'MISSING:' not in out
                      and f'"{key}" section' not in out
                      and f'AGENTS.md "{key}"' not in out, failure_detail(out, 900)))
        r = subprocess.run(
            [sys.executable, str(d / 'tools' / 'precedent_vendor_engine.py'),
             'status', str(ROOT)], capture_output=True, text=True, cwd=str(d))
        st = r.stdout + r.stderr
        cases.append(('...while status, which is asked, still names it as '
                      'left out on purpose',
                      f'AGENTS.md has no "{key}" section' in st
                      and 'recorded as left out on purpose' in st, failure_detail(st, 900)))

        # -- E, CONTROL: edited but carrying the new bullet too --
        complete = repo_old.replace(old_sec, cur_sec + '\n- Ours.')
        e = make_consumer('edited-complete', complete, None)
        rc, out = run_refresh(e)
        cases.append(('CONTROL: an edited section carrying every template '
                      'block is left alone and reported as lacking nothing',
                      rc == 0 and agents(e) == complete
                      and 'nothing to copy in' in out
                      and f'AGENTS.md "{key}":' not in out, failure_detail(out, 900)))

        # -- F: retired branch names -- reported by line, outside the
        # generated block only, and not on a line recording the rename --
        named = repo_old.replace(
            '## Git / workflow\n',
            '## Git / workflow\n\n- Clone `precedent-beta-v01` for reference.\n'
            '- `staging` (named `precedent-beta-v01` until 2026-09-25).\n', 1)
        f = make_consumer('retired-name', named, None)
        rc, out = run_refresh(f)
        # Counted in the file as the refresh left it: the scan runs after
        # the stale "### Two check levels" above it was rewritten.
        want_line = agents(f).split('\n').index(
            '- Clone `precedent-beta-v01` for reference.') + 1
        hit = [ln for ln in out.splitlines() if ln.startswith('RETIRED BRANCH NAME:')]
        cases.append(('a hand-written line naming a retired branch is '
                      'reported by line; the generated block and a line '
                      'recording the rename are not',
                      rc == 0 and len(hit) == 1
                      and f'1 line(s)' in hit[0] and f'AGENTS.md:{want_line}.' in hit[0],
                      '\n'.join(hit) or failure_detail(out, 900)))

        # -- G, CONTROL: no AGENTS.md -- never created --
        g = make_consumer('absent', None, None)
        rc, out = run_refresh(g)
        cases.append(('CONTROL: a consumer with no AGENTS.md is not given one',
                      rc == 0 and not (g / 'AGENTS.md').exists(), failure_detail(out, 800)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'"Update Vendors" brings an unedited AGENTS.md template section up '
          f'to date and reports what an edited or missing one lacks, never '
          f'overwriting it ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_kept_divergence_is_judged_block_by_block():
    """A kept template divergence is judged block by block (2026-10-31,
    precedent_vendor_engine's ONE VERDICT PER BLOCK). Measured that day in a
    consuming repository: six AGENTS.md sections waived on 2026-10-01 with
    one identical stock reason, and the copies lacked template lines nobody
    had judged; then a reduction pass moved four of them to a side file,
    where nothing compared them again.

    Cases, each against the engine's own words (practice:
    control-asserts-which-failure): a whole-section waiver with a reason and
    a matching pin is no longer kept; the same reason on two items is
    refused as stock even with every block judged; a judged item with its
    own reason is kept (the positive control); a "covered" quote that is
    not in the local text, a send-upstream with no link and a local-add-on
    whose practice is missing each fail by name, and "standardize" never
    rests; judge-kept records a verdict and refuses standardize; and a
    section moved out of AGENTS.md is still compared where it lives, both
    when it lacks a block (listed) and when it carries every one (quiet)."""
    import contextlib
    import io
    fx = _KeptDivergenceFixture('precedent-kept-blocks-')
    pve = fx.pve
    cases = []
    key = '### Session start'
    item = f'AGENTS.md {key}'
    try:
        tpl = fx.template(fx.AGENTS_SRC).decode()
        raw = pve._template_sections(tpl)[key][1]
        repo = fx.consumer('blocks')
        sec = pve._instantiate(raw, pve._agents_md_subs(repo))
        own = f'{key}\n\n- This repository starts its sessions its own way.'
        lacks = pve.missing_markdown_blocks(own, sec)
        titles = [t for _o, t, _h, _a in lacks]
        sha, carried = pve._sha_text(sec), pve._carried_sha(sec, lacks)
        fx.keep(repo, item, 'we start sessions our own way, on purpose here', sha)

        def verdict(it=item, local=own):
            return pve._kept_divergence(repo, it, sha, carried, titles, local)[0]

        cases.append(('a whole-section waiver (reason + matching pin, no block '
                      'verdicts) is no longer kept',
                      verdict() == 'unjudged', verdict()))
        cases.append(('...while the pin alone, asked without the blocks, still '
                      'matches (so nothing else that reads the pin moved)',
                      pve._kept_divergence(repo, item, sha, carried)[0] == 'kept', ''))
        fx.judge(repo, item, titles)
        cases.append(('POSITIVE CONTROL: every lacked block judged, own reason: kept',
                      verdict() == 'kept', verdict()))

        stock = ('This repository words this section in its own terms, so the '
                 'template wording is not copied in.')
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        cfg['kept_template_divergences'][item]['reason'] = stock
        cfg['kept_template_divergences']['AGENTS.md ## Conventions'] = {
            'reason': '  ' + stock.upper() + ' ', 'template_sha256': 'x'}
        fx.write_config(repo, cfg)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kept = pve._report_kept(repo, item, 'the template', sha, carried, titles, own)
        cases.append(('the same reason on two items (case and spacing aside) is '
                      'refused as stock, with every block judged',
                      verdict() == 'stock' and not kept
                      and 'word for word on another item' in buf.getvalue(),
                      buf.getvalue()[:600]))
        cfg['kept_template_divergences'][item]['reason'] = 'we start sessions our own way'
        del cfg['kept_template_divergences']['AGENTS.md ## Conventions']
        fx.write_config(repo, cfg)

        b0 = pve.block_id(titles[0])
        for v, want in (({'verdict': 'covered', 'quote': 'words nobody wrote here'},
                         'not in the local text'),
                        ({'verdict': 'covered', 'quote': 'its own way'}, None),
                        ({'verdict': 'send-upstream', 'detail': 'later'}, 'needs "detail"'),
                        ({'verdict': 'send-upstream',
                          'detail': 'https://github.com/OWNER/REPO/pull/1'}, None),
                        ({'verdict': 'local-add-on', 'practice': 'local/practices/gone.md'},
                         'must exist'),
                        ({'verdict': 'standardize'}, 'not a verdict to keep')):
            cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
            cfg['kept_template_divergences'][item]['blocks'][b0] = v
            fx.write_config(repo, cfg)
            probs = [w for i, _t, w in pve.block_problems(repo, item, titles, own) if i == b0]
            ok = (not probs) if want is None else (len(probs) == 1 and want in probs[0])
            cases.append((f'block verdict {v} -> {want or "holds"}', ok, probs))

        ok, msg = pve.judge_kept_block(repo, item, b0, 'standardize')
        cases.append(('judge-kept refuses standardize as a resting verdict',
                      not ok and 'a fix, not a verdict' in msg, msg))
        ok, msg = pve.judge_kept_block(repo, item, b0, 'covered', quote='its own way')
        stored = json.loads((repo / 'precedent.json').read_text(encoding='utf-8')
                            )['kept_template_divergences'][item]['blocks'][b0]
        cases.append(('judge-kept records a covered verdict with its quote',
                      ok and stored == {'verdict': 'covered', 'quote': 'its own way'},
                      (msg, stored)))

        # Moved out: AGENTS.md without the section, docs/ carrying it.
        moved = fx.consumer('moved')
        stock_md = (moved / 'AGENTS.md').read_text(encoding='utf-8')
        (moved / 'AGENTS.md').write_text(
            stock_md.replace(sec, f'{key}\n\nSee [docs/agents-detail.md](docs/agents-detail.md).')
            .replace(f'{key}\n\nSee', 'Session start: see'), encoding='utf-8')
        (moved / 'docs').mkdir()

        def report(side_text):
            (moved / 'docs' / 'agents-detail.md').write_text(
                '# Detail\n\n' + side_text + '\n', encoding='utf-8')
            plan = pve._agents_md_plan(moved, 'consumer', ROOT, {})
            buf = io.StringIO()
            left_before = list(pve._LEFT_FOR_YOU)
            with contextlib.redirect_stdout(buf):
                pve._report_agents_md(moved, ROOT, plan)
            if left_before is not None:
                pve._LEFT_FOR_YOU[:] = left_before
            return [r[3] for r in plan if r[0] == key], buf.getvalue()

        acts, out = report(own)
        cases.append(('a section moved to docs/ that lacks template blocks is '
                      'compared THERE and listed',
                      acts == ['moved'] and 'lives in docs/agents-detail.md' in out
                      and '(in docs/agents-detail.md) has local edits' in out,
                      (acts, out[:800])))
        acts, out = report(sec)
        cases.append(('...and one that carries every block is compared and quiet',
                      acts == ['moved'] and 'carries every block' in out
                      and 'DIVERGED' not in out, (acts, out[:800])))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {str(d)[:600]}' for n, d in bad))


def check_retired_template_sections_migrate_into_practices():
    """The AGENTS.md template sections that became practices on 2026-10-31
    (precedent_vendor_engine.RETIRED_AGENTS_MD_SECTIONS) leave an installed
    repository at its next Update Vendors with every rule still reachable.

    A consumer is installed from the template as it stood before the move,
    then edited the ways real ones are: one own bullet added to
    "Administrator requests", a real entry in "Review sensitivities", and a
    repo-local source declared. After one update: the stock sections are
    gone (Working in parallel, the merge runbook); the own bullet is in a
    local add-on practice with `adds_to: administrator-requests`, word for
    word, and the section is gone; the sensitivities list stays; and each
    retired section's practice reaches a session -- an occasion-index line
    in the regenerated AGENTS.md, or a gate. CONTROL: a consumer installed
    from today's template has nothing to retire."""
    fx = _KeptDivergenceFixture('precedent-retired-sections-')
    pve = fx.pve
    cases = []
    try:
        last_with = subprocess.run(
            ['git', '-C', str(ROOT), 'show', f'{fx.base}:{fx.AGENTS_SRC}'],
            capture_output=True, text=True).stdout
        if '## Administrator requests' in last_with:
            return (False, '0 stated cases', 'the template still carries the '
                    'retired sections; nothing to migrate')
        # The newest template version that still had them.
        log = subprocess.run(['git', '-C', str(ROOT), 'log', '--format=%H', fx.base,
                              '--', fx.AGENTS_SRC], capture_output=True, text=True
                             ).stdout.split()
        old_tpl = None
        for sha in log:
            t = subprocess.run(['git', '-C', str(ROOT), 'show', f'{sha}:{fx.AGENTS_SRC}'],
                               capture_output=True, text=True).stdout
            if '## Administrator requests you must know how to handle' in t:
                old_tpl = t
                break
        if old_tpl is None:
            return (False, '0 stated cases', 'no past template version with the '
                    'retired sections in this clone (shallow?)')
        control = fx.consumer('control')
        plan = pve._retired_agents_md_plan(control, 'consumer', ROOT)
        cases.append(('CONTROL: today\'s template has nothing to retire', plan == [], plan))

        repo = fx.consumer('old')
        agents = pve._instantiate(old_tpl, pve._agents_md_subs(repo))
        own = ('- **"Ship it"** -- this repository\'s own phrase for a release: '
               'build the site and post the link in the team channel.')
        agents = agents.replace('- **"Add project members"**', own + '\n- **"Add project members"**', 1)
        agents = agents.replace("- `<member>`: `<what to flag — e.g. tone changes to member-facing\n  pages>` — `<incident that showed it, date>`",
                                '- Dana: flag tone changes to the welcome page -- reverted 2026-09-02.')
        assert own in agents and 'Dana:' in agents, 'old template shape moved; repoint this fixture'
        (repo / 'AGENTS.md').write_text(agents, encoding='utf-8')
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        cfg['sources'].append({'level': 'repo-local', 'name': 'local', 'path': 'local'})
        fx.write_config(repo, cfg)
        (repo / 'local' / 'practices').mkdir(parents=True)
        fx.sh('git', 'add', '-A', cwd=repo)
        fx.sh('git', 'commit', '-qm', 'installed from the old template', cwd=repo)
        rc, out = fx.update(repo)
        after = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('the stock retired sections are removed and said so',
                      '## Working in parallel' not in after
                      and '### Merging a thread branch' not in after
                      and 'retired: agents.md "## working in parallel' in out.lower(),
                      failure_detail(out, 1500)))
        addon = repo / 'local' / 'practices' / 'administrator-requests-in-this-repo.md'
        text = addon.read_text(encoding='utf-8') if addon.is_file() else ''
        cases.append(('the own bullet moved word for word into a local add-on '
                      'practice that adds to administrator-requests, and the section went',
                      'adds_to:     administrator-requests' in text
                      and ' '.join(own.split()) in ' '.join(text.split())
                      and '## Administrator requests' not in after,
                      (text[:600], failure_detail(out, 800))))
        cases.append(('the review-sensitivities list with a real entry stays',
                      '### Review sensitivities (accumulated)' in after and 'Dana:' in after,
                      failure_detail(after, 800)))
        unreached = []
        for slug in sorted(set(pve.RETIRED_AGENTS_MD_SECTIONS.values())):
            fm = (ROOT / 'practices' / f'{slug}.md').read_text(encoding='utf-8')
            gated = re.search(r'^gates:\s*\[\s*"', fm, re.M) is not None
            if not (gated or f'  {slug} — ' in after):
                unreached.append(slug)
        cases.append(('every retired section\'s practice reaches a session: an '
                      'occasion-index line in the regenerated AGENTS.md, or a gate',
                      not unreached, unreached))
        cases.append(('the spoken phrases stay in the occasion index',
                      "What's waiting for me?" in after and 'Add project members' in after,
                      [ln for ln in after.split('\n') if 'administrator' in ln][:4]))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {str(d)[:900]}' for n, d in bad))


def check_exported_file_not_received_fails_the_copied_in_check():
    """Every test a declared source ships reaches the consuming repository,
    or the copied-in check fails (2026-10-31: a consumer's push check printed
    "no practice in force here claims these, not vendored" for two of a
    shared set's tests, and passed).

    Cases: a test claimed by no checked_by is left behind AND recorded as
    not received, and the exported-files-received check fails on it by
    name; a test whose header cites `practice: SLUG` for a practice in force
    here from its own source is claimed and copied (the fix at the source);
    CONTROL -- one citing a practice from ANOTHER source is still not
    received; and a MANIFEST.json with nothing left behind passes."""
    import contextlib
    import io
    import tempfile
    import types
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory(prefix='precedent-copied-in-') as td:
        td = pathlib.Path(td)
        src = td / 'set'
        (src / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        t = src / 'tools' / 'checks' / 'tests'
        (t / 'test_orphan.sh').write_text('#!/bin/bash\n# tests a data file\nexit 0\n')
        (t / 'test_cited.sh').write_text('#!/bin/bash\n# practice: act\nexit 0\n')
        (t / 'test_elsewhere.sh').write_text('#!/bin/bash\n# practice: other\nexit 0\n')
        sources = [{'name': 'the-set', 'path': str(src), 'level': 'team'}]
        res = {'practices': {
            'act': {'fm': {}, 'source': 'the-set', 'file': str(src / 'practices' / 'act.md')},
            'other': {'fm': {}, 'source': 'precedent', 'file': str(td / 'u' / 'other.md')}}}
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            plan = pm._plan_checks(sources, res)
        names = {name for _l, name, _s, _b in plan}
        cases.append(('a test cited by its header for a practice in force from its '
                      'own source is claimed', 'test_cited.sh' in names, sorted(names)))
        cases.append(('an unclaimed test is left behind and recorded as not received',
                      'test_orphan.sh' not in names and any('test_orphan.sh' in x
                                                            for x in pm._NOT_RECEIVED),
                      list(pm._NOT_RECEIVED)))
        cases.append(('CONTROL: a citation of another source\'s practice claims nothing',
                      'test_elsewhere.sh' not in names and any('test_elsewhere.sh' in x
                                                               for x in pm._NOT_RECEIVED),
                      list(pm._NOT_RECEIVED)))
        repo = td / 'consumer'
        repo.mkdir()
        fn = pc.CHECKS['exported-files-received']['fn']

        def run(data):
            (repo / 'MANIFEST.json').write_text(json.dumps(data), encoding='utf-8')
            old = pc.ROOT
            pc.ROOT = repo
            try:
                return fn(types.SimpleNamespace(root=repo))
            finally:
                pc.ROOT = old
        got = run({'not_received': list(pm._NOT_RECEIVED)})
        cases.append(('the copied-in check fails on each file not received, by name, '
                      'with the fix at the source',
                      len(got) == 2 and all('never received here' in f.detail
                                            and 'practice: SLUG' in f.detail for f in got),
                      [f.detail[:120] for f in got]))
        cases.append(('CONTROL: nothing left behind passes', run({'practices': []}) == [], ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {str(d)[:500]}' for n, d in bad))


def check_agents_templates_conventions_point_to_practices():
    """A `## Conventions` bullet in an AGENTS.md template that names a
    practice is a pointer to it: its bold lead, the practice, and a few
    words more, never the practice's rule said again.

    2026-10-08: taking the loader template's "## Conventions" and "## Practice
    sources", as Update Vendors asks, added about 1,100 tokens to a
    consumer's AGENTS.md and failed its landing check, mostly on bullets
    restating practices that already load when they apply. The verbatim
    check above did not catch them: they paraphrase. A bullet naming no
    practice -- template-only instruction such as commit credit -- is not
    held to this."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    bad = []
    for rel in ('templates/AGENTS.md.loader.template', 'templates/AGENTS.md.template'):
        text = (ROOT / rel).read_text(encoding='utf-8')
        lines = text.split('\n')
        span = [(a, b) for k, a, b in pve._md_sections(text) if k.strip() == '## Conventions']
        if rel.endswith('.loader.template'):
            # 2026-10-31: the loader template's Conventions became pointers
            # nowhere -- the practices load on their own, and commit credit
            # is practice commits-credit-the-driver. Holding it gone.
            if span:
                bad.append(f'{rel}: "## Conventions" is back; its bullets are '
                           f'practices now (RETIRED_AGENTS_MD_SECTIONS)')
            continue
        if len(span) != 1:
            bad.append(f'{rel}: no single "## Conventions" section')
            continue
        for offset, block in pve._md_blocks('\n'.join(lines[span[0][0]:span[0][1]])):
            slugs = [s for s in re.findall(r'practice\s+`([a-z0-9-]+)`', block)
                     if (ROOT / 'practices' / f'{s}.md').is_file()]
            if not slugs or not block.lstrip().startswith(('-', '*')):
                continue
            rest = re.sub(r'\*\*.*?\*\*', ' ', block, count=1)
            rest = re.sub(r'\(practice\s+`[a-z0-9-]+`[^)]*\)', ' ', rest)
            words = len(re.findall(r"[A-Za-z][\w'-]*", rest))
            if words > 12:
                bad.append(f'{rel}:{span[0][0] + offset + 1} names {slugs[0]} and '
                           f'adds {words} words of its own')
    check('an AGENTS.md template\'s Conventions bullet naming a practice only '
          'points to it', not bad, '; '.join(bad))


def check_update_seeds_budgets_on_the_run_that_reports_done():
    """Update Vendors seeds tools/session_load_budgets.json only on the run
    that reports DONE, measuring the files that run produced -- never on a
    run that leaves template sections for the person to copy in.

    2026-10-08, a consuming repository: run 1 seeded AGENTS.md at its size
    before the sections the same run listed (taking them put it at 8,101
    against 8,100), and the session-start file as the old engine had
    rendered it (practice: session-load-budget).

    1. a run with a section left for the person writes no registry;
    2. the next run, after the section is copied in, reports DONE and seeds
       AGENTS.md as it now stands -- the measurement is the file on disk;
    3. CONTROL: a consumer with nothing left is seeded on its first run, so
       the seed did not just stop happening."""
    fx = _KeptDivergenceFixture('precedent-done-ceiling-')
    pve, cases = fx.pve, []
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    # Repointed 2026-10-31, when Conventions left the template for practices.
    key = '## Git / workflow'
    reg_rel = pathlib.Path('tools') / 'session_load_budgets.json'

    def seeded(repo):
        reg = json.loads((repo / reg_rel).read_text(encoding='utf-8'))
        e = reg['surfaces']['AGENTS.md']
        return e['ceiling'], int(re.match(r'(\d+) tokens', e['_note']).group(1))
    try:
        tpl = pve._instantiate(fx.template(fx.AGENTS_SRC).decode(),
                               pve._agents_md_subs(fx.tmp))
        sec = pve._instantiate(pve._template_sections(
            fx.template(fx.AGENTS_SRC).decode())[key][1], pve._agents_md_subs(fx.tmp))
        assert sec in tpl, 'template shape moved; repoint this fixture'

        repo = fx.consumer('asked', agents=tpl.replace(sec + '\n\n', ''))
        rc, out = fx.update(repo)
        cases.append((f'1: a run that leaves a section for the person seeds '
                      f'nothing (exit {rc})',
                      rc == pu.LEFT and not (repo / reg_rel).exists()))
        # The person copies the section in where the template has it: just
        # before the heading that follows it there.
        agents = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        following = tpl.split(sec + '\n\n', 1)[1].split('\n', 1)[0]
        assert following and following in agents, 'no anchor to copy the section in at'
        (repo / 'AGENTS.md').write_text(agents.replace(
            following, sec + '\n\n' + following, 1), encoding='utf-8')
        fx.sh('git', 'add', '-A', cwd=repo)
        fx.sh('git', 'commit', '-qm', 'took the section', cwd=repo)
        rc, out = fx.update(repo)
        ok = rc == pu.DONE and (repo / reg_rel).exists()
        detail = ''
        if ok:
            ceiling, measured = seeded(repo)
            now = bv._approx_tokens((repo / 'AGENTS.md').read_text(encoding='utf-8'))
            ok = measured == now and ceiling >= now
            detail = f': measured {measured}, file {now}, ceiling {ceiling}'
        cases.append((f'2: the DONE run seeds AGENTS.md as it stands, section '
                      f'included (exit {rc}){detail}', ok))
        staged = subprocess.run(['git', '-C', str(repo), 'diff', '--cached',
                                 '--name-only'], capture_output=True,
                                text=True).stdout.split()
        cases.append(('2b: the seeded registry is staged with the update',
                      str(reg_rel) in staged))

        repo = fx.consumer('clean')
        rc, out = fx.update(repo)
        cases.append((f'3: CONTROL: nothing left, seeded on the first run '
                      f'(exit {rc})', rc == pu.DONE and (repo / reg_rel).exists()))
    except (OSError, ValueError, KeyError, AttributeError, AssertionError) as e:
        cases.append((f'fixture could not be read: {type(e).__name__}: {e}', False))
    finally:
        fx.close()
    bad = [n for n, ok in cases if not ok]
    check(f'Update Vendors seeds the session-load budgets on the run that '
          f'reports DONE ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_kept_agents_md_divergence_is_recorded():
    """An AGENTS.md section a repo words its own way ON PURPOSE can be
    recorded, and then Update Vendors finishes: DONE, exit 0 -- until
    upstream changes that section, when it is listed again. Before
    2026-09-28 nothing could record it: three consumers saw the same
    sections listed as LEFT FOR YOU on every update, one after writing the
    `diverged` manifest entry the runbook named, which nothing read
    (precedent_vendor_engine.KEPT_DIVERGENCES_KEY).

    Discriminating cases (practice: control-asserts-which-failure): the
    recorded section must go quiet (the fix), and must come BACK when the
    template's text for it moves and when the entry has no reason (the fix
    is a pinned decision, not a mute button). The CONTROL is the same
    consumer before anything is planted: DONE, so the exit code each case
    asserts comes from the planted section and nothing else."""
    fx = _KeptDivergenceFixture('precedent-kept-agents-md-')
    pve = fx.pve
    cases = []
    key = '### Session start'
    item = f'AGENTS.md {key}'
    try:
        tpl = fx.template(fx.AGENTS_SRC).decode()
        control = fx.consumer('control')
        rc, out = fx.update(control)
        cases.append(('CONTROL: the stock install takes an update with nothing '
                      'asked: exit 0, DONE', rc == 0 and 'DONE' in out, failure_detail(out, 1200)))

        subs = pve._agents_md_subs(control)
        stock = pve._instantiate(tpl, subs)
        raw = pve._template_sections(tpl)[key][1]
        sec = pve._instantiate(raw, subs)
        assert sec in stock, 'template shape moved; repoint this fixture'
        own = (f'{key}\n\n- This repo starts its sessions its own way, '
               f'written in its own words.')
        ours = stock.replace(sec, own)
        full_now = pve._sha_text(sec)

        def pin(section):
            # What a kept section is pinned to since 2026-09-30: the blocks
            # it carries, each block it lacks entirely standing as one line.
            return pve._carried_sha(section,
                                    pve.missing_markdown_blocks(own, section))
        sha_now = pin(sec)

        repo = fx.consumer('kept', agents=ours)
        rc, out = fx.update(repo)
        cases.append(('an unrecorded reworded section is LEFT FOR YOU, exit 1, '
                      'and the report prints the hash to record it with',
                      rc == 1 and f'AGENTS.md "{key}"' in out.split('LEFT FOR YOU')[-1]
                      and sha_now in out, failure_detail(out, 1500)))

        # Recorded the way an engine before 2026-09-30 printed it: the whole
        # section's hash. Still honoured, and narrowed to the pin above.
        titles = [t for _o, t, _h, _a in pve.missing_markdown_blocks(own, sec)]
        fx.keep(repo, item, 'we say this our own way', full_now)
        rc, out = fx.update(repo)
        cases.append(('since 2026-10-31 a reason alone no longer keeps it: each '
                      'block the section lacks is listed for its own verdict',
                      rc == 1 and 'whole-section waiver no longer holds' in out
                      and out.count('no verdict') >= len(titles) >= 1,
                      failure_detail(out, 1500)))
        first_out = out
        fx.judge(repo, item, titles)
        rc, out = fx.update(repo)
        cases.append(('THE FIX: recorded with a reason against the current '
                      'template, the next update is DONE, exit 0',
                      rc == 0 and 'DONE' in out and 'LEFT FOR YOU' not in out,
                      failure_detail(out, 1500)))
        entry = json.loads((repo / 'precedent.json').read_text(
            encoding='utf-8'))['kept_template_divergences'][item]
        cases.append(('...and the pin gains the blocks the section carries '
                      'beside the template\'s own text, and says so',
                      entry['template_sha256'] == full_now
                      and entry.get('carried_sha256') == sha_now
                      and 'now records both' in first_out + out,
                      failure_detail(first_out + out, 1500)))
        cases.append(('...and says it once, with the reason, as a note',
                      out.count('kept on purpose: ') == 2   # step line + summary
                      and 'we say this our own way' in out, failure_detail(out, 1500)))
        cases.append(('...and the section is left exactly as the repo wrote it',
                      'written in its own words' in
                      (repo / 'AGENTS.md').read_text(encoding='utf-8'), ''))

        # Upstream rewords a block this section does not carry at all
        # (2026-09-30: a placeholder renamed inside one missing bullet brought
        # a kept section back, and the consumer re-pinned it by hand).
        blocks = [t for o, t in pve._md_blocks(sec)]
        assert blocks and all(h == 'missing' for _o, _t, h, _a in
                              pve.missing_markdown_blocks(own, sec)), \
            'this fixture needs a section whose blocks are all missing'
        head, rest = raw.split('\n', 1)
        word = next(w for w in blocks[0][:60].split() if len(w) > 5 and w.isalpha())
        reworded = tpl.replace(raw, head + '\n' + rest.replace(word, word + 'x', 1))
        assert reworded != tpl
        rc, out = fx.update(repo, fx.upstream_with(fx.AGENTS_SRC,
                                                   reworded.encode()))
        # Since 2026-10-31 a lacked block is judged by its own words: a
        # rewording in its title is a new block to judge, and only that one
        # is asked about -- the pin still holds, so the section is not
        # listed as changed.
        reasked = [ln for ln in out.split('\n') if ln.rstrip().endswith('-- no verdict')]
        cases.append(('a rewording inside a block the section lacks entirely '
                      'asks for that one block\'s verdict, never "has changed since"',
                      rc == 1 and len(reasked) == 1 and 'has changed since' not in out,
                      failure_detail(out, 1500)))

        moved = tpl.replace(raw, raw + '\n- **FIXTURE BULLET** -- a sentence '
                                       'upstream added to this section later.')
        assert moved != tpl
        rc, out = fx.update(repo, fx.upstream_with(fx.AGENTS_SRC, moved.encode()))
        cases.append(('once upstream changes that section, it is LEFT FOR YOU '
                      'again, naming the change and the new hash',
                      rc == 1 and f'AGENTS.md "{key}"' in out.split('LEFT FOR YOU')[-1]
                      and 'FIXTURE BULLET' in out and 'has changed since' in out
                      and pin(pve._instantiate(
                          pve._template_sections(moved)[key][1], subs)) in out,
                      failure_detail(out, 1500)))

        # The consumer edits its OWN section: one sentence from a block it
        # lacked. Upstream never changed, so the decision holds (2026-10-01,
        # from a consumer's Update Vendors: the carried pin moved with the
        # local text and the report said upstream had changed).
        local = fx.consumer('local-edit', agents=ours)
        fx.keep(local, item, 'we say this our own way', full_now)
        fx.judge(local, item, titles)
        fx.update(local)
        first = blocks[0].split('\n')[0]
        text = (local / 'AGENTS.md').read_text(encoding='utf-8')
        (local / 'AGENTS.md').write_text(
            text.replace('written in its own words.',
                         'written in its own words.\n\n' + first, 1),
            encoding='utf-8')
        rc, out = fx.update(local)
        cases.append(('a local edit to a kept section keeps the decision: DONE, '
                      'exit 0, and never "upstream has changed"',
                      rc == 0 and 'DONE' in out and 'has changed since' not in out,
                      failure_detail(out, 1500)))

        bare = fx.consumer('unreasoned', agents=ours)
        fx.keep(bare, item, '', sha_now)
        rc, out = fx.update(bare)
        cases.append(('an entry with no reason is not honoured, and says so',
                      rc == 1 and 'not honoured' in out, failure_detail(out, 1500)))
    finally:
        fx.close()

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an AGENTS.md section kept on purpose is recorded once and Update '
          f'Vendors finishes, until upstream changes it ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:1500]}" for n, d in bad))


def check_absent_agents_md_section_is_asked_across_self_refresh():
    """A template section a consumer's AGENTS.md lacks is put on Left for
    you before it is ever recorded as left out on purpose -- including when
    the refresh replaces its own vendoring tool and runs a second pass.

    Measured 2026-09-28: the first pass reported the section MISSING,
    recorded it as absent, then cleared its Left-for-you list so the second
    pass could print its own; the second pass read "absent" as a decision
    already made and said only "left out, as at the last refresh". So the
    person was never asked, and check_update_vendors_is_one_command failed
    whenever the engine had uncommitted changes (seed vendors HEAD, the
    update vendors the working tree, so the tool replaced itself).

    Discriminating cases (practice: control-asserts-which-failure): the
    CONTROL takes the same refresh without the vendoring tool changing and
    must list the section; the case under test differs only in an upstream
    commit that changes the vendoring tool, and asserts the second pass
    really ran. The follow-up asserts the fix is not a mute removed: once
    asked, the next refresh remembers the answer and stays quiet -- since
    2026-10-12 entirely, where it used to print one NOTE line."""
    fx = _KeptDivergenceFixture('precedent-absent-section-')
    pve = fx.pve
    cases = []
    key = '### Session start'
    tool = 'tools/precedent_vendor_engine.py'
    listed = f'AGENTS.md "{key}"'

    def refresh(repo, ref):
        return fx.sh(sys.executable, str(repo / tool), 'refresh', str(ROOT),
                     '--from-ref', ref, cwd=repo)

    def left(out):
        return out.split('Left for you', 1)[1] if 'Left for you' in out else ''

    try:
        tpl = fx.template(fx.AGENTS_SRC).decode()
        raw = pve._template_sections(tpl)[key][1]
        stock = pve._instantiate(tpl, {'<precedent upstream URL>': pve.SOURCE_REPO,
                                       '<default-branch>': 'main'})
        sec = pve._instantiate(raw, {'<precedent upstream URL>': pve.SOURCE_REPO,
                                     '<default-branch>': 'main'})
        assert sec in stock, 'template shape moved; repoint this fixture'
        lacking = stock.replace(sec + '\n', '', 1)
        assert key not in lacking, 'section still present; repoint this fixture'

        control = fx.consumer('control', agents=lacking)
        # The vendoring tool exactly as seeded, so this refresh cannot
        # replace it, whatever state the working tree is in.
        same_tool = fx.upstream_with(tool, (control / tool).read_bytes())
        rc, out = refresh(control, same_tool)
        cases.append(('CONTROL: without a self-replacement, the missing section '
                      'is on Left for you',
                      rc == 0 and 'replaced the vendoring tool itself' not in out
                      and listed in left(out), failure_detail(out, 2000)))

        repo = fx.consumer('self-refresh', agents=lacking)
        moved_tool = fx.upstream_with(
            tool, fx.template(tool) + b'\n# verify_harness fixture: an upstream '
                                      b'change to the vendoring tool itself\n')
        rc, out = refresh(repo, moved_tool)
        cases.append(('the refresh replaced its own tool and ran the second pass',
                      rc == 0 and 'replaced the vendoring tool itself' in out,
                      failure_detail(out, 2000)))
        cases.append(('THE FIX: the missing section is on Left for you after the '
                      'second pass, not only recorded as absent',
                      listed in left(out), failure_detail(out, 2000)))
        recorded = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                              .read_text(encoding='utf-8')
                              ).get(pve.AGENTS_MD_SECTIONS_KEY) or {}
        cases.append(('...and it is recorded as absent for the next refresh',
                      key in recorded and recorded[key] is None, recorded))

        rc, out = refresh(repo, moved_tool)
        cases.append(('once asked, the next refresh remembers it: unsaid, and '
                      'not on Left for you',
                      rc == 0 and 'MISSING:' not in out
                      and f'"{key}" section' not in out
                      and listed not in left(out), failure_detail(out, 2000)))
    finally:
        fx.close()

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a section AGENTS.md lacks is asked about before it is recorded as left '
          f'out, across a self-replacing refresh too ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:1500]}" for n, d in bad))


def check_a_hook_wired_from_elsewhere_is_reported_as_wired():
    """A hook a repo calls in place, from a path of its own, is WIRED --
    reported as wired, and still not vendored
    (practice: control-asserts-which-failure).

    THE TWO QUESTIONS THIS PINS APART, because one function was answering
    both and could only be right about one. "What do we vendor?" must look
    only under `.claude/hooks/`: a repo that calls a script in place keeps one
    copy of it on purpose, and planting the engine's bundled copy beside it is
    double maintenance that reads as a hand-edit months later. "What does this
    repo already wire?" must not, or the report is simply false.

    THE COST, measured 2026-09-22 in `precedent-individual`. That repo authors
    these scripts and wires four of them straight out of its own tracked
    `bootstrap/`; its settings.json says so outright -- *"bootstrap/ IS a
    tracked directory of this repo, so every entry calls its script in place
    -- one file, no second copy to drift from it."* The refresh told it that
    `commit-identity.sh`, `freshness-guard.sh` and
    `precedent-universal-catalogue.sh` were "not wired in this repo's own
    .claude/settings.json". All three are wired, on consecutive lines of it.

    Worse than noise, because the NOTE beside it says to break the loop by
    hand -- copy the entry from upstream, re-run, and the file arrives.
    Following that here plants the second copy the repo deliberately does not
    keep. The discriminating case below is therefore the NEGATIVE one: wired
    from elsewhere must stay OUT of the vendoring set.

    The fixture owns its own tree (fixture-owns-its-state)."""
    import tempfile
    import precedent_vendor_engine as pve

    d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-wiring-'))
    try:
        (d / '.claude').mkdir(parents=True)
        (d / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
            'SessionStart': [
                {'hooks': [{'type': 'command',
                            'command': '$CLAUDE_PROJECT_DIR/bootstrap/'
                                       'in-place.sh'}]},
                {'hooks': [{'type': 'command',
                            'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/'
                                       'vendored.sh'}]},
            ]}}), encoding='utf-8')
        vendoring = pve._wired_hook_names(d)
        reporting = pve._wired_hook_names_anywhere(d)

        cases = [
            ('a hook wired from .claude/hooks/ is in the vendoring set',
             'vendored.sh' in vendoring, repr(sorted(vendoring))),
            ('THE DISCRIMINATING CASE: a hook wired in place from another '
             'path stays OUT of the vendoring set, so no second copy is '
             'planted beside it',
             'in-place.sh' not in vendoring, repr(sorted(vendoring))),
            ('...and is still reported as wired, so the NOTE cannot call it '
             'unwired and send somebody to hand-wire it',
             'in-place.sh' in reporting, repr(sorted(reporting))),
            ('a hook wired from nowhere is in neither set',
             'absent.sh' not in vendoring and 'absent.sh' not in reporting,
             f'{sorted(vendoring)} / {sorted(reporting)}'),
            ('an absent settings.json is empty in both, never an error',
             pve._wired_hook_names(d / 'nope') == set()
             and pve._wired_hook_names_anywhere(d / 'nope') == set(), ''),
        ]
        bad = [(n, det) for n, ok, det in cases if not ok]
        check(f'a hook wired in place from another path is reported as wired '
              f'and still not vendored ({len(cases)} stated cases, the '
              f'not-vendored one being the discriminating one)',
              not bad, '; '.join(f'{n} -- {det[:300]}' for n, det in bad))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check_vendor_engine_removes_a_hook_upstream_dropped():
    """THE GAP (found 2026-09-21 by the very deep check's deletion-
    propagation table, filed as
    todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer.md). This engine
    had two removal paths -- tools/ and .github/workflows/ -- and none for
    .claude/hooks/. A hook dropped upstream stayed installed in every
    consumer, and _write_hook_files then replaced `hook_files` with only
    what it had just written, so the manifest entry vanished as well: the
    file went on running, in every session, recorded by nothing.

    Four cases, and the last two are the ones that make this safe rather
    than merely working:

    A. a hook upstream no longer ships is deleted, and the manifest stops
       recording it.
    B. a hook that IS still shipped is untouched -- the sweep must key on
       what upstream ships, never on what this repo happens to wire.
    C. a hand-edited copy is KEPT and reported, the same standard the
       engine path uses: reaching here means somebody asked to overwrite,
       which is not the same as asking to throw an edit away.
    D. an EMPTY upstream hooks directory sweeps NOTHING. `available` comes
       from a directory glob, and an empty one is indistinguishable from
       "this checkout cannot see upstream" -- sweeping on that reading
       would delete every hook in the consumer, which is the failure this
       whole family exists to prevent."""
    import shutil, tempfile
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-hookdrop-'))
    cases = []
    try:
        def _fixture(name, *, edited=False, empty_upstream=False):
            repo = tmp / name
            (repo / 'tools').mkdir(parents=True)
            hooks = repo / pve.HOOK_DEST_DIR
            hooks.mkdir(parents=True)
            src = tmp / f'{name}-upstream'
            src.mkdir()
            body_gone = '#!/bin/sh\necho dropped\n'
            body_live = '#!/bin/sh\necho live\n'
            (hooks / 'zzz-dropped.sh').write_text(
                body_gone if not edited else body_gone + '# hand edit\n',
                encoding='utf-8')
            (hooks / 'zzz-live.sh').write_text(body_live, encoding='utf-8')
            if not empty_upstream:
                (src / 'zzz-live.sh').write_text(body_live, encoding='utf-8')
            (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps({
                'hook_files': ['zzz-dropped.sh', 'zzz-live.sh'],
                'hooks_sha256': {
                    'zzz-dropped.sh': hashlib.sha256(
                        body_gone.encode('utf-8')).hexdigest(),
                    'zzz-live.sh': hashlib.sha256(
                        body_live.encode('utf-8')).hexdigest()},
            }, indent=2), encoding='utf-8')
            available = set(pve._hook_file_names(src))
            removed = pve._remove_dropped_hook_files(
                repo, repo / 'tools' / pve.MANIFEST_NAME, available, src)
            manifest = json.loads(
                (repo / 'tools' / pve.MANIFEST_NAME).read_text(
                    encoding='utf-8'))
            return repo, hooks, removed, manifest

        _r, hooks_a, removed_a, manifest_a = _fixture('plain')
        cases.append(('A: the hook upstream dropped is deleted',
                      removed_a == ['zzz-dropped.sh']
                      and not (hooks_a / 'zzz-dropped.sh').exists(),
                      repr(removed_a)))
        cases.append(('A: the manifest stops recording it',
                      'zzz-dropped.sh' not in manifest_a.get('hook_files', [])
                      and 'zzz-dropped.sh' not in
                      manifest_a.get('hooks_sha256', {}),
                      json.dumps(manifest_a)[:300]))
        cases.append(('B: a hook upstream still ships is untouched',
                      (hooks_a / 'zzz-live.sh').exists()
                      and 'zzz-live.sh' in manifest_a.get('hook_files', []),
                      json.dumps(manifest_a)[:300]))

        _r2, hooks_c, removed_c, manifest_c = _fixture('edited', edited=True)
        cases.append(('C: a hand-edited copy is kept, not deleted',
                      removed_c == []
                      and (hooks_c / 'zzz-dropped.sh').exists(),
                      repr(removed_c)))

        _r3, hooks_d, removed_d, _m = _fixture('blind', empty_upstream=True)
        cases.append(('D: an empty upstream hooks/ sweeps nothing',
                      removed_d == []
                      and (hooks_d / 'zzz-dropped.sh').exists()
                      and (hooks_d / 'zzz-live.sh').exists(),
                      repr(removed_d)))

        # E (2026-09-28): the real update shape. The consumer's OLD copy of
        # the tool runs first and rewrites the manifest without the dropped
        # hook, so the manifest on disk no longer names it. The record from
        # before the update is the COMMITTED one, and _previous_manifest
        # reads it; without it this removed nothing, every time.
        repo_e = tmp / 'two-pass'
        (repo_e / 'tools').mkdir(parents=True)
        hooks_e = repo_e / pve.HOOK_DEST_DIR
        hooks_e.mkdir(parents=True)
        src_e = tmp / 'two-pass-upstream'
        src_e.mkdir()
        gone, live = '#!/bin/sh\necho dropped\n', '#!/bin/sh\necho live\n'
        (hooks_e / 'zzz-dropped.sh').write_text(gone, encoding='utf-8')
        (hooks_e / 'zzz-live.sh').write_text(live, encoding='utf-8')
        (src_e / 'zzz-live.sh').write_text(live, encoding='utf-8')
        mpath = repo_e / 'tools' / pve.MANIFEST_NAME
        sha = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()
        mpath.write_text(json.dumps({
            'files': ['zzz_dropped_tool.py'],
            'sha256': {'zzz_dropped_tool.py': 'x'},
            'hook_files': ['zzz-dropped.sh', 'zzz-live.sh'],
            'hooks_sha256': {'zzz-dropped.sh': sha(gone),
                             'zzz-live.sh': sha(live)}}), encoding='utf-8')
        for args in (['init', '-q'], ['add', '-A'],
                     ['-c', 'user.name=Fixture', '-c', 'user.email=f@invalid',
                      'commit', '-q', '-m', 'installed']):
            subprocess.run(['git', '-C', str(repo_e), *args], check=True,
                           capture_output=True)
        pass_one = {'files': [], 'sha256': {}}      # what the old copy wrote
        mpath.write_text(json.dumps(pass_one), encoding='utf-8')
        before = pve._previous_manifest(repo_e, pass_one)
        removed_e = pve._remove_dropped_hook_files(
            repo_e, mpath, set(pve._hook_file_names(src_e)), src_e,
            previous=before)
        cases.append(('E: after a self-replacing first pass, the committed '
                      'record still finds the dropped hook, and it is deleted',
                      removed_e == ['zzz-dropped.sh']
                      and not (hooks_e / 'zzz-dropped.sh').exists()
                      and (hooks_e / 'zzz-live.sh').exists(),
                      repr(removed_e)))
        cases.append(('E: and the engine file list the old pass forgot is '
                      'recovered the same way',
                      'zzz_dropped_tool.py' in before.get('files', []),
                      repr(before.get('files'))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a refresh removes a hook upstream dropped, and only that '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_vendor_engine_keeps_a_declared_engine_path():
    """`engine_paths` in a repo's precedent.json maps an upstream file onto a
    path of the repo's own, so `refresh` keeps it current instead of a person
    hand-syncing it. The case that produced it (2026-09-24):
    precedent-individual's bootstrap/commit-identity.sh, identical to
    templates/harness/claude-code/hooks/commit-identity.sh only because of
    four hand-sync commits, and unable to move because session-start.sh and
    the set's own `adapters` both reach it by that path.

    Function-level against a throwaway upstream git repo, plus two real
    `refresh` subprocesses for the refusals that happen BEFORE the upstream
    is read (so they need no network and no BestPractice clone):

    A. adopt: an identical local file with no record yet is adopted, not
       rewritten, and its hash recorded.
    B. refresh: upstream moves, the file follows, the hash follows, the
       executable bit is carried over.
    C. hand-edit: an edited copy is drift; `refresh` refuses on it.
    D. first run, NOT identical: refused, with a count of differing lines.
    E. forbidden: onto an adapter's TO, onto an engine-vendored path, or the
       same local path twice -- refused by `refresh` even with --force.
       CONTROL: an adapter's FROM is allowed (precedent-individual's case).
    F. a dropped declaration hands the file back: kept, no longer tracked.
    G. an upstream file that vanished leaves the local copy AND its record."""
    import shutil, tempfile, subprocess as sp
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-engine-paths-'))
    env = dict(os.environ)
    env.update({'GIT_CONFIG_GLOBAL': str(tmp / 'gitconfig'),
                'PRECEDENT_ALLOW_ANY_AUTHOR': '1',
                'GIT_AUTHOR_NAME': 'Harness', 'GIT_COMMITTER_NAME': 'Harness',
                'GIT_AUTHOR_EMAIL': 'harness@example.com',
                'GIT_COMMITTER_EMAIL': 'harness@example.com'})
    (tmp / 'gitconfig').write_text('', encoding='utf-8')
    UP, LOCAL = 'tpl/hooks/ident.sh', 'bootstrap/ident.sh'
    cases = []

    def git(d, *a):
        r = sp.run(['git', '-C', str(d), *a], capture_output=True, text=True,
                   env=env)
        if r.returncode != 0:
            raise RuntimeError(f'fixture setup: git {" ".join(a)}: '
                               f'{(r.stderr or r.stdout).strip()}')
        return r.stdout.strip()

    def upstream_commit(body, path=UP):
        f = upstream / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding='utf-8')
        f.chmod(0o755)
        git(upstream, 'add', '-A')
        git(upstream, 'commit', '-q', '-m', 'fixture')
        return git(upstream, 'rev-parse', 'HEAD')

    def make_repo(name, mapping, local_body=None, adapters=None):
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True)
        (repo / 'precedent.json').write_text(json.dumps(
            {pve.ENGINE_PATHS_KEY: mapping}), encoding='utf-8')
        (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps(
            {'kind': 'source', 'files': [], 'sha256': {}}), encoding='utf-8')
        if local_body is not None:
            (repo / LOCAL).parent.mkdir(parents=True, exist_ok=True)
            (repo / LOCAL).write_text(local_body, encoding='utf-8')
        if adapters is not None:
            (repo / 'MANIFEST.json').write_text(json.dumps(
                {'adapters': adapters}), encoding='utf-8')
        return repo

    def manifest_of(repo):
        return json.loads((repo / 'tools' / pve.MANIFEST_NAME).read_text(
            encoding='utf-8'))

    def one_pass(repo, commit):
        """What refresh() does with engine_paths, minus the engine files."""
        m = manifest_of(repo)
        mapping = pve.declared_engine_paths(repo)
        src = pve._read_engine_path_sources(upstream, commit, mapping)
        refused = pve._engine_path_first_run_refusals(repo, mapping, src, m)
        if refused:
            return refused
        pve._write_engine_paths(repo, mapping, src, m)
        return []

    def run_refresh(repo, *extra):
        tool = repo / 'tools' / 'precedent_vendor_engine.py'
        tool.write_bytes((ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes())
        m = manifest_of(repo)
        m['files'] = ['precedent_vendor_engine.py']
        m['sha256'] = {'precedent_vendor_engine.py': hashlib.sha256(
            tool.read_bytes()).hexdigest()}
        (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps(m),
                                                        encoding='utf-8')
        r = sp.run([sys.executable, str(tool), 'refresh', str(upstream),
                    *extra], capture_output=True, text=True, cwd=str(repo),
                   env=env)
        return r.returncode, r.stdout + r.stderr

    try:
        upstream = tmp / 'upstream'
        upstream.mkdir()
        git(upstream, 'init', '-q')
        v1 = '#!/bin/sh\necho v1\n'
        c1 = upstream_commit(v1)

        # A -- adopt
        repo_a = make_repo('adopt', {UP: LOCAL}, local_body=v1)
        before = (repo_a / LOCAL).stat().st_mtime_ns
        refused_a = one_pass(repo_a, c1)
        m_a = manifest_of(repo_a)
        cases.append(('A: an identical local file is adopted and its hash recorded',
                      refused_a == []
                      and m_a.get('engine_paths') == {LOCAL: UP}
                      and m_a.get('engine_paths_sha256', {}).get(LOCAL)
                      == hashlib.sha256(v1.encode()).hexdigest(),
                      json.dumps(m_a)[:300]))
        cases.append(('A: ...without being rewritten',
                      (repo_a / LOCAL).stat().st_mtime_ns == before, ''))

        # B -- refresh follows upstream
        (repo_a / LOCAL).chmod(0o644)
        v2 = '#!/bin/sh\necho v2\n'
        c2 = upstream_commit(v2)
        one_pass(repo_a, c2)
        m_b = manifest_of(repo_a)
        cases.append(('B: the file follows upstream, and so does its recorded hash',
                      (repo_a / LOCAL).read_text(encoding='utf-8') == v2
                      and m_b['engine_paths_sha256'][LOCAL]
                      == hashlib.sha256(v2.encode()).hexdigest()
                      and pve._engine_path_drift(repo_a, m_b) == [],
                      json.dumps(m_b)[:300]))
        cases.append(('B: the upstream executable bit is carried over',
                      os.access(repo_a / LOCAL, os.X_OK), ''))
        cases.append(('B: nothing is left to do once recorded',
                      pve._engine_paths_incomplete(repo_a, m_b) == [], ''))

        # C -- hand-edit is drift, and refresh refuses on it
        (repo_a / LOCAL).write_text(v2 + '# local edit\n', encoding='utf-8')
        drift_c = pve._engine_path_drift(repo_a, manifest_of(repo_a))
        cases.append(('C: a hand-edited copy is reported as drift',
                      drift_c and drift_c[0][0] == LOCAL
                      and 'hand-edited' in drift_c[0][1], repr(drift_c)))
        rc_c, out_c = run_refresh(repo_a)
        cases.append(('C: refresh refuses on it, before reading upstream',
                      rc_c != 0 and 'hand-edited since the last seed/refresh' in out_c
                      and LOCAL in out_c, failure_detail(out_c, 600)))

        # D -- first run, not identical
        repo_d = make_repo('differs', {UP: LOCAL},
                           local_body='#!/bin/sh\necho mine\necho extra\n')
        refused_d = one_pass(repo_d, c2)
        cases.append(('D: a non-identical file on first run is refused, with a line count',
                      len(refused_d) == 1 and refused_d[0][0] == LOCAL
                      and refused_d[0][1] > 0
                      and 'engine_paths_sha256' not in manifest_of(repo_d)
                      and 'mine' in (repo_d / LOCAL).read_text(encoding='utf-8'),
                      repr(refused_d)))
        repo_d2 = make_repo('absent', {UP: LOCAL})
        cases.append(('D: CONTROL -- an absent local file is simply written',
                      one_pass(repo_d2, c2) == []
                      and (repo_d2 / LOCAL).read_text(encoding='utf-8') == v2, ''))

        # E -- forbidden mappings, refused by refresh even with --force
        adapter_to = '.claude/hooks/ident.sh'
        repo_e1 = make_repo('onto-adapter', {UP: adapter_to},
                            adapters=[{'path': adapter_to, 'source': 'some-set'}])
        rc_e1, out_e1 = run_refresh(repo_e1, '--force')
        cases.append(("E: a mapping onto an adapter's TO is refused, even with --force",
                      rc_e1 != 0 and 'Not waived by --force' in out_e1
                      and 'some-set' in out_e1, failure_detail(out_e1, 600)))
        repo_e2 = make_repo('onto-engine', {UP: 'tools/precedent_vendor_engine.py'})
        rc_e2, out_e2 = run_refresh(repo_e2, '--force')
        cases.append(('E: a mapping onto an engine-vendored path is refused',
                      rc_e2 != 0 and 'already vendors this path' in out_e2,
                      failure_detail(out_e2, 600)))
        conflicts_twice = pve._engine_path_conflicts(
            tmp, {UP: LOCAL, 'tpl/other.sh': LOCAL}, {}, 'source')
        cases.append(('E: the same local path declared twice is refused',
                      len(conflicts_twice) == 1 and 'twice' in conflicts_twice[0][1],
                      repr(conflicts_twice)))
        repo_e3 = make_repo('adapter-from', {UP: LOCAL}, local_body=v2,
                            adapters=[{'path': adapter_to, 'source': 'some-set'}])
        cases.append(("E: CONTROL -- an adapter's FROM path is allowed",
                      pve._engine_path_conflicts(
                          repo_e3, pve.declared_engine_paths(repo_e3),
                          manifest_of(repo_e3), 'source') == [], ''))

        # F -- dropped declaration hands the file back
        repo_f = make_repo('dropped', {UP: LOCAL}, local_body=v2)
        one_pass(repo_f, c2)
        (repo_f / 'precedent.json').write_text('{}', encoding='utf-8')
        one_pass(repo_f, c2)
        m_f = manifest_of(repo_f)
        cases.append(('F: a dropped declaration leaves the file and stops tracking it',
                      (repo_f / LOCAL).is_file()
                      and 'engine_paths_sha256' not in m_f
                      and pve._engine_path_drift(repo_f, m_f) == [],
                      json.dumps(m_f)[:300]))

        # G -- upstream vanished
        repo_g = make_repo('vanished', {UP: LOCAL}, local_body=v2)
        one_pass(repo_g, c2)
        git(upstream, 'rm', '-q', UP)
        git(upstream, 'commit', '-q', '-m', 'drop')
        c3 = git(upstream, 'rev-parse', 'HEAD')
        one_pass(repo_g, c3)
        m_g = manifest_of(repo_g)
        cases.append(('G: an upstream file that vanished keeps the local copy and its record',
                      (repo_g / LOCAL).read_text(encoding='utf-8') == v2
                      and LOCAL in m_g.get('engine_paths_sha256', {}),
                      json.dumps(m_g)[:300]))

        # H -- carried by hand, identical to upstream (2026-10-03, found
        # rehearsing a Produce: precedent-individual carried upstream's
        # commit-identity.sh before a refresh, and every refresh after that
        # refused on it as a hand-edit). CONTROL: a real edit, same repo
        # shape, is still refused.
        v4 = '#!/bin/sh\necho v4\n'
        upstream_commit(v4)
        for body, refused_want, what in (
                (v4, False, 'a copy identical to upstream does not hold refresh up'),
                (v4 + '# mine\n', True, 'CONTROL: a real edit still does')):
            repo_h = make_repo('carried-' + str(refused_want), {UP: LOCAL},
                               local_body=v2)
            one_pass(repo_h, c2)
            (repo_h / LOCAL).write_text(body, encoding='utf-8')
            rc_h, out_h = run_refresh(repo_h, '--from-ref', 'HEAD')
            refused = 'hand-edited since the last seed/refresh' in out_h
            cases.append((f'H: {what}',
                          refused == refused_want and (refused_want or
                          'identical to upstream' in out_h),
                          f'rc={rc_h} {failure_detail(out_h, 500)}'))

        # I -- a TEMPLATE declared as an engine path is kept RENDERED, the
        # way a consumer's refresh renders it (2026-10-04: precedent-
        # individual's hand-rendered bootstrap hook fell behind its template
        # twice, and its adapter shipped the stale copy over every
        # consumer's). First run adopts a copy identical to the render;
        # CONTROL: the raw template's placeholders never reach the file.
        tpl_up = f'{pve.HOOK_SOURCE_DIR}/{pve.INDIVIDUAL_HOOK_TEMPLATE}'
        tpl_local = 'bootstrap/' + pve.INDIVIDUAL_HOOK
        raw = ('#!/bin/bash\nNAME="{{SOURCE_NAME}}"\nURL="{{SOURCE_REPO_URL}}"\n'
               'if [ "{{SOURCE_REPO_URL_SUBSTITUTED}}" != "yes" ]; then exit 0; fi\n')
        c_t = upstream_commit(raw, path=tpl_up)
        repo_i = make_repo('rendered', {tpl_up: tpl_local})
        (repo_i / tpl_local).parent.mkdir(parents=True, exist_ok=True)
        (repo_i / tpl_local).write_text(pve.render_individual_hook(raw),
                                        encoding='utf-8')
        refused_i = one_pass(repo_i, c_t)
        body_i = (repo_i / tpl_local).read_text(encoding='utf-8')
        cases.append(('I: a template engine path is adopted when the local copy '
                      'is its render, and kept rendered, never raw',
                      refused_i == [] and '{{' not in body_i
                      and 'NAME="precedent-individual"' in body_i
                      and tpl_local in manifest_of(repo_i).get('engine_paths_sha256', {}),
                      repr(refused_i) + body_i[:300]))
        c_t2 = upstream_commit(raw + '# moved upstream\n', path=tpl_up)
        one_pass(repo_i, c_t2)
        body_i2 = (repo_i / tpl_local).read_text(encoding='utf-8')
        cases.append(('I: when the template moves, the rendered copy follows it',
                      '# moved upstream' in body_i2 and '{{' not in body_i2
                      and os.access(repo_i / tpl_local, os.X_OK), body_i2[:300]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a declared engine_paths file is kept current by refresh, and never '
          f'adopted over a difference or onto a path something else writes '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_vendor_engine_retires_ci_workflow_files():
    """THE INCIDENT (2026-09-19, found in themorgan/precedent-individual).
    views-drift.yml.template was folded into the practice-set workflow
    template (itself retired 2026-10-01) as its own job (spec/CI_MINUTES_PLAN.md item 9), and the repos that
    hand-applied that fix the same day deleted their now-redundant
    views-drift.yml file -- but nothing told refresh() the old manifest
    entry was retired, so ci_workflows_sha256 kept a hash for a file that no
    longer existed. _ci_workflow_drift reads "recorded, but missing" as a
    hand-edit needing --force, so the NEXT refresh() in that repo would have
    refused the WHOLE run over a file a previous, correct fix had already
    removed.

    Two mechanisms this closes, tested here: RETIRED_CI_WORKFLOW_FILES +
    _remove_retired_ci_workflow_files (refresh() self-heals a stale
    retirement automatically), and the `record-ci` CLI subcommand
    (record_ci_workflow_files exposed standalone, clone-free, for the
    moment a CI workflow file is fixed BY HAND and needs the manifest told
    without a `refresh --force` overwriting the fix back to the generic
    template -- the other half of the same incident, found the same day in
    two real consumer repos).

    2026-09-20: _remove_retired_ci_workflow_files stopped only reporting a
    retired file still on disk and started deleting it -- but ONLY when its
    current sha256 still matches what the manifest had recorded, the same
    standard _ci_workflow_drift already uses for "not drifted" everywhere
    else in this module. Case B below now splits on exactly that hash
    match/mismatch, since it is now the entire question the old single case
    collapsed into one "always kept" assumption that would no longer be
    true.

    `kind: source` throughout, since RETIRED_CI_WORKFLOW_FILES' one entry
    (views-drift.yml) is a 'source'-kind retirement; CI_WORKFLOW_TEMPLATES
    is not, so leak-gate.yml.template is the live template refresh()
    always has to reach past the retired entry to apply.

    Fixture shape mirrors check_vendor_engine_refreshes_ci_workflow_files
    immediately above: only precedent_vendor_engine.py is copied into each
    fake consumer, and each scenario gets its own fresh directory."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ci-retire-'))
    cases = []
    # A CONSUMER, and its leak gate, since 2026-09-21. This fixture used
    # precedent-check.yml in a `source` set, which was a live tracked
    # workflow then and is not now: a source ships none
    # (practice: source-sets-run-no-ci), so a refresh correctly DELETES it
    # and the fixture's "it survives" expectation became the stale half.
    # The retirement mechanism under test is kind-agnostic; what it needs is
    # a workflow the kind still ships, and a consumer's leak gate is one.
    rel = '.github/workflows/leak-gate.yml'
    retired_rel = '.github/workflows/views-drift.yml'
    try:
        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        engine_hash = hashlib.sha256(engine_bytes).hexdigest()
        real_template = (ROOT / 'templates' / 'github-actions' /
                         'leak-gate.yml.template').read_bytes()
        stub = b'name: stub\n# an older vendored copy\n'
        stub_hash = hashlib.sha256(stub).hexdigest()
        retired_content = b'name: views-drift\n'
        retired_content_hash = hashlib.sha256(retired_content).hexdigest()

        def make_set(name, retired_still_on_disk, retired_hash_matches=False):
            """A fresh 'consumer' repo carrying a live leak-gate.yml
            (recorded, stale against the current template -- so a
            successful refresh is independently visible) plus a retired
            views-drift.yml manifest entry, with or without the file
            itself still sitting on disk.

            retired_hash_matches selects which of the two on-disk cases a
            still-present retired file is in: True records the file's OWN
            real hash (untouched since the manifest last looked -- safe to
            delete); False records a hash that does not match (stands in
            for a hand-edit since -- must be kept)."""
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / '.github' / 'workflows').mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            (consumer / rel).write_bytes(stub)
            retired_recorded = (retired_content_hash if retired_hash_matches
                                 else 'deadbeef' * 8)
            ci_hashes = {rel: stub_hash, retired_rel: retired_recorded}
            if retired_still_on_disk:
                (consumer / retired_rel).write_bytes(retired_content)
            manifest = {
                'kind': 'consumer', 'source_commit': 'deadbeef',
                'files': ['precedent_vendor_engine.py'],
                'sha256': {'precedent_vendor_engine.py': engine_hash},
                'ci_workflow_files': sorted(ci_hashes),
                'ci_workflows_sha256': ci_hashes,
            }
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(manifest), encoding='utf-8')
            return consumer

        # Computed, not the literal 'HEAD' -- see _ref_including_worktree's
        # own docstring: this vendors the tree under test, uncommitted
        # changes included, not just whatever HEAD happens to hold.
        ref = _ref_including_worktree(ROOT)

        def run_refresh(consumer):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--from-ref', ref],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        def manifest_of(consumer):
            return json.loads(
                (consumer / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))

        # -- A: retired entry, file already gone from disk (the real
        # precedent-individual shape) -- refresh succeeds, refreshes the
        # LIVE file, and drops the retired entry, all in one run --
        a = make_set('gone', retired_still_on_disk=False)
        rc_a, out_a = run_refresh(a)
        cases.append(('a retired, already-deleted CI workflow entry does NOT make '
                      'refresh refuse the run',
                      rc_a == 0, out_a[:800]))
        cases.append(('...the still-current file is refreshed to the current '
                      'template regardless',
                      (a / rel).read_bytes() == real_template, out_a[:800]))
        cases.append(('...and the retired entry is dropped from the manifest',
                      retired_rel not in manifest_of(a).get('ci_workflows_sha256', {}),
                      out_a[:800]))
        cases.append(('...reported by name, not a silent drop',
                      'views-drift.yml' in out_a and 'retired' in out_a, out_a[:800]))

        # -- B1: retired entry, file STILL on disk, UNTOUCHED since the
        # manifest last recorded its hash -- deleted, not just reported
        # (2026-09-20 change) --
        b1 = make_set('deleted', retired_still_on_disk=True, retired_hash_matches=True)
        rc_b1, out_b1 = run_refresh(b1)
        cases.append(('an untouched retired file (on-disk hash matches the manifest) '
                      'is deleted, and refresh still succeeds',
                      rc_b1 == 0 and not (b1 / retired_rel).is_file(), out_b1[:800]))
        cases.append(('...the manifest entry is dropped too',
                      retired_rel not in manifest_of(b1).get('ci_workflows_sha256', {}),
                      out_b1[:800]))
        cases.append(('...and the deletion is reported by name, not silent',
                      'views-drift.yml' in out_b1 and 'deleted' in out_b1, out_b1[:800]))

        # -- B2: retired entry, file STILL on disk, HAND-EDITED since the
        # manifest last recorded its hash -- kept and reported, never
        # deleted, matching refresh()'s existing hand-edit protection
        # everywhere else (_local_drift, _remove_dropped_engine_files) --
        b2 = make_set('kept', retired_still_on_disk=True, retired_hash_matches=False)
        rc_b2, out_b2 = run_refresh(b2)
        cases.append(('CONTROL: when the retired file has been hand-edited since, '
                      'refresh still succeeds and drops the manifest entry',
                      rc_b2 == 0 and retired_rel not in manifest_of(b2).get('ci_workflows_sha256', {}),
                      out_b2[:800]))
        cases.append(('...but the file itself is left on disk, not deleted',
                      (b2 / retired_rel).is_file(), out_b2[:400]))
        cases.append(('...and refresh WARNs that it was hand-edited rather than '
                      'staying silent about the leftover',
                      'hand-edited' in out_b2, out_b2[:800]))

        # -- C: `record-ci` re-baselines a hand-fixed file's hash, clone-free,
        # without touching content -- the other half of the same incident --
        c = tmp / 'hand-fixed'
        (c / 'tools').mkdir(parents=True)
        (c / '.github' / 'workflows').mkdir(parents=True)
        (c / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
        hand_fixed = b'name: leak-gate\n# hand-applied fix, correct content\n'
        (c / rel).write_bytes(hand_fixed)
        stale_manifest = {
            'kind': 'consumer', 'source_commit': 'deadbeef',
            'files': ['precedent_vendor_engine.py'],
            'sha256': {'precedent_vendor_engine.py': engine_hash},
            'ci_workflow_files': [rel],
            'ci_workflows_sha256': {rel: stub_hash},  # stale: predates the hand fix
        }
        (c / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps(stale_manifest), encoding='utf-8')
        r_c = subprocess.run(
            [sys.executable, str(c / 'tools' / 'precedent_vendor_engine.py'), 'record-ci'],
            capture_output=True, text=True, cwd=str(c))
        cases.append(('`record-ci` runs with no clone argument at all (unlike status/'
                      'refresh) and exits clean',
                      r_c.returncode == 0, (r_c.stdout + r_c.stderr)[:800]))
        cases.append(('...re-records the hash to match what is on disk NOW',
                      manifest_of(c).get('ci_workflows_sha256', {}).get(rel) ==
                      hashlib.sha256(hand_fixed).hexdigest(),
                      (r_c.stdout + r_c.stderr)[:800]))
        cases.append(('...without touching the hand-fixed content itself',
                      (c / rel).read_bytes() == hand_fixed, ''))
        r_c2 = subprocess.run(
            [sys.executable, str(c / 'tools' / 'precedent_vendor_engine.py'), 'record-ci'],
            capture_output=True, text=True, cwd=str(c))
        cases.append(('CONTROL: a second `record-ci` run, now already current, says so '
                      'rather than re-printing a change',
                      r_c2.returncode == 0 and 'nothing to do' in r_c2.stdout,
                      r_c2.stdout[:400]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a retired CI workflow template (views-drift.yml folded into '
          f'precedent-check.yml) self-heals on refresh instead of refusing, deletes '
          f'the file itself only when untouched since last recorded, and '
          f'`record-ci` re-baselines a hand-fixed file clone-free ({len(cases)} '
          f'stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_materialized_links_are_placed():
    """A practice's relative links are repointed for where the file lands.

    Practice files ship. A practice's links are written relative to its own
    directory in its own repository, and copied verbatim into a consuming
    repo they point at nothing -- `../tools/very_deep_check.py` and
    `../spec/ATTENTION_CEILING.md` are real in Precedent and absent from
    every repo that installs it. Every consuming repo was shipping ~60
    practice files with dead internal links, and
    precedent-team-repo-maintenance' own light check had already had to exempt
    materialized practices/ from its broken-link scan to stay green.

    Four behaviours, and the last two are why this is not a blanket
    rewrite: a link that already resolves where it lands must be left
    exactly as it is, and a link this cannot place confidently must be
    left alone rather than mangled -- the output is a copy of somebody
    else's content."""
    import shutil, tempfile, importlib.util

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-matlinks-'))
    cases = []
    try:
        spec = importlib.util.spec_from_file_location(
            '_pm_links', ROOT / 'tools' / 'precedent_materialize.py')
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)

        # An "upstream" source repo with a real remote and a real commit,
        # so the rewrite has something honest to point at.
        upstream = tmp / 'upstream'
        (upstream / 'practices').mkdir(parents=True)
        (upstream / 'spec').mkdir()
        (upstream / 'tools').mkdir()
        (upstream / 'spec' / 'THING.md').write_text('x\n', encoding='utf-8')
        (upstream / 'tools' / 'engine.py').write_text('x\n', encoding='utf-8')
        (upstream / 'practices' / 'sibling.md').write_text('x\n', encoding='utf-8')
        src = upstream / 'practices' / 'p.md'
        src.write_text(
            'See [spec/THING.md](../spec/THING.md) and [engine](../tools/engine.py).\n'
            'Sibling: [sibling](sibling.md). External: [x](https://example.com/a).\n'
            'Missing at the source: [gone](../spec/GONE.md).\n', encoding='utf-8')
        for argv in (['init', '-q'], ['config', 'user.email', 'h@e'],
                     ['config', 'user.name', 'h'],
                     ['remote', 'add', 'origin', 'https://github.com/acme/upstream.git'],
                     ['add', '-A'], ['commit', '-qm', 'seed']):
            subprocess.run(['git', '-C', str(upstream), *argv], capture_output=True)
        commit = subprocess.run(['git', '-C', str(upstream), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True).stdout.strip()

        consumer = tmp / 'consumer'
        (consumer / 'practices').mkdir(parents=True)
        (consumer / 'tools').mkdir()
        (consumer / 'tools' / 'engine.py').write_text('x\n', encoding='utf-8')
        out = pm._rewrite_links(src.read_bytes(), str(src), consumer,
                                sibling_slugs={'sibling'}).decode('utf-8')

        cases.append(('a target in another repository becomes a commit URL — '
                      'the branch could be deleted, the commit cannot',
                      f'https://github.com/acme/upstream/blob/{commit}/spec/THING.md'
                      in out, out))
        cases.append(('a sibling practice link is left exactly as it is — '
                      'recognised from the slug set this run is writing, not '
                      'from what happens to be on disk yet',
                      '](sibling.md)' in out, out))
        cases.append(('an external URL is left alone',
                      '](https://example.com/a)' in out, out))
        cases.append(('a link that already resolves where it LANDS is left '
                      'relative — the consumer has its own tools/engine.py, '
                      'so an absolute URL would send the reader to the wrong '
                      'copy', '](../tools/engine.py)' in out, out))
        cases.append(("a link already broken at the source is left alone, not "
                      "invented", '](../spec/GONE.md)' in out, out))

        # The repo-local direction: same family, opposite sign. A practice at
        # local/practices/x.md writing `../tools/` means local/tools/, which
        # is NOT what that link means once the file sits at practices/x.md.
        (consumer / 'local' / 'practices').mkdir(parents=True)
        (consumer / 'local' / 'tools').mkdir()
        (consumer / 'local' / 'tools' / 'own.py').write_text('x\n', encoding='utf-8')
        lsrc = consumer / 'local' / 'practices' / 'l.md'
        lsrc.write_text('Ours: [own](../tools/own.py).\n', encoding='utf-8')
        lout = pm._rewrite_links(lsrc.read_bytes(), str(lsrc), consumer).decode('utf-8')
        cases.append(('a repo-local source\'s link is recomputed as a relative '
                      'path from the new location, not turned into a URL — the '
                      'file is right there in the same repo',
                      '](../local/tools/own.py)' in lout, lout))

        # The privacy boundary. An individual source is named only in a
        # person's own user-level config -- load_config refuses one declared
        # in a shared repo -- so writing its repository's URL into a tracked
        # practices/ tree publishes exactly what that refusal protects, and
        # a consuming repo can be public.
        iout = pm._rewrite_links(src.read_bytes(), str(src), consumer,
                                 sibling_slugs={'sibling'},
                                 may_name_source_repo=False).decode('utf-8')
        cases.append(("an individual source's link is NOT turned into a URL "
                      "naming its private repository — the dead relative link "
                      "is the smaller failure",
                      'github.com/acme/upstream' not in iout
                      and '](../spec/THING.md)' in iout, iout))
        cases.append(('and the placements that do not name that repository '
                      'still happen for an individual source',
                      '](../tools/engine.py)' in iout and '](sibling.md)' in iout,
                      iout))

        # No remote, no rewrite: never guess a URL.
        noremote = tmp / 'noremote'
        (noremote / 'practices').mkdir(parents=True)
        (noremote / 'spec').mkdir()
        (noremote / 'spec' / 'THING.md').write_text('x\n', encoding='utf-8')
        nsrc = noremote / 'practices' / 'p.md'
        nsrc.write_text('See [t](../spec/THING.md).\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(noremote), 'init', '-q'], capture_output=True)
        nout = pm._rewrite_links(nsrc.read_bytes(), str(nsrc), consumer).decode('utf-8')
        cases.append(('a source with no usable remote leaves its links alone '
                      'rather than writing a URL it had to guess',
                      '](../spec/THING.md)' in nout, nout))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a materialized practice\'s links are placed for where the file '
          f'lands ({len(cases)} stated cases: another repo becomes a commit '
          f'URL; a sibling, an external URL, a link that already resolves, '
          f'and a link broken at the source are all left alone; a repo-local '
          f'source is recomputed relative; an individual source never names '
          f'its own private repository; no remote means no rewrite)',
          not bad, '; '.join(f"{n} -- {d[:160]}" for n, d in bad))


def check_practice_declared_hooks_are_wired():
    """A practice's `hooks:` declaration is parsed in one place, refused when
    it reaches past what the practice ships, and wired add-only by the sync.

    WHY. 2026-10-06: the writing set's planted-download-names shipped its
    script and a check requiring a SendUserFile hook, and said the hook was
    wired by hand. Nothing wired it, so a consumer failed that check right
    after a clean sync."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv
    import precedent_vendor_engine as pve
    import precedent_sync_views as psv
    good = {'ships': '["tools/dated_name.py"]',
            'hooks': '[{"event": "PreToolUse", "matcher": "SendUserFile", '
                     '"run": "tools/dated_name.py", "args": ["--hook"]}]'}
    hooks = bv.practice_hooks(good)
    check('a declared hook parses into the command the sync writes',
          [bv.hook_command(h) for h in hooks]
          == ['python3 $CLAUDE_PROJECT_DIR/tools/dated_name.py --hook'], repr(hooks))
    for why, raw in (
            ('a script the practice does not ship',
             '[{"event": "Stop", "run": "tools/other.py"}]'),
            ('a tool event with no matcher',
             '[{"event": "PreToolUse", "run": "tools/dated_name.py"}]'),
            ('an argument that is not a plain word',
             '[{"event": "Stop", "run": "tools/dated_name.py", "args": ["; rm x"]}]'),
            ('an event outside the list',
             '[{"event": "Notification", "run": "tools/dated_name.py"}]'),
            ('a command line of its own',
             '[{"event": "Stop", "run": "tools/dated_name.py", "command": "sh"}]')):
        try:
            bv.practice_hooks({**good, 'hooks': raw})
            refused = False
        except ValueError:
            refused = True
        check(f'a hooks: entry naming {why} is refused', refused, raw)
    check('CONTROL: no hooks: field declares nothing',
          bv.practice_hooks({'ships': '[]'}) == [], '')

    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'dated_name.py').write_text('', encoding='utf-8')
        practices = {'planted-download-names': {'fm': good}}
        entries, notes = psv._declared_practice_hooks(repo, practices)
        check('no settings.json: nothing is written, and none is created',
              pve.add_practice_hooks(repo, entries) == []
              and not (repo / '.claude').exists(), '')
        (repo / '.claude').mkdir()
        mine = {'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [
            {'type': 'command', 'command': 'echo mine'}]}]}}
        (repo / '.claude' / 'settings.json').write_text(json.dumps(mine),
                                                        encoding='utf-8')
        missing = pve.missing_practice_hooks(repo, entries)
        check('--check reports the declared hook as missing',
              [c for _e, _m, c in missing]
              == ['python3 $CLAUDE_PROJECT_DIR/tools/dated_name.py --hook'],
              repr(missing))
        added = pve.add_practice_hooks(repo, entries)
        got = json.loads((repo / '.claude' / 'settings.json').read_text())
        listed = json.loads((repo / pve.PRACTICE_HOOKS_FILE).read_text())['hooks']
        # Since 2026-10-07 into the file precedent-hooks.sh reads, never into
        # settings.json, where every addition was a question for the person.
        check('the sync lists it, under its own matcher, for the fixed '
              'precedent-hooks.sh entry, and settings.json is untouched',
              len(added) == 1 and got == mine
              and listed[0]['matcher'] == 'SendUserFile', json.dumps(listed))
        check('a second sync adds nothing',
              pve.add_practice_hooks(repo, entries) == []
              and pve.missing_practice_hooks(repo, entries) == [], '')
        (repo / 'precedent.json').write_text(json.dumps(
            {'declined_ships': {'tools/dated_name.py': 'not here'}}), encoding='utf-8')
        declined, _n = psv._declared_practice_hooks(repo, practices)
        check('a repo that declined the script gets no hook for it',
              declined == [], repr(declined))
        (repo / 'precedent.json').unlink()
        (repo / 'tools' / 'dated_name.py').unlink()
        absent, gone_notes = psv._declared_practice_hooks(repo, practices)
        check('a script not on disk gets no hook', absent == [], repr(absent))
        # 2026-10-17: never in silence -- a check the engine stopped carrying,
        # now a set's hook, was off in a repo that lacked the set's files.
        check('...and says so: the check is off here until the script arrives',
              any('planted-download-names' in n and 'not in this repository yet' in n
                  for n in gone_notes), repr(gone_notes))
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_update as _pu
        _rep = _pu.Report()
        if hasattr(_pu, 'hooks_not_here_step'):
            _pu.hooks_not_here_step(_rep, '\n'.join(
                f'precedent_sync_views: {n}' for n in gone_notes))
        _said = repr(getattr(_rep, '__dict__', {}))
        check('...and Update Vendors carries it into its report as a warning',
              'tools/dated_name.py' in _said and 'WARNING' in _said, failure_detail(_said, 300))
        bad, notes = psv._declared_practice_hooks(
            repo, {'x': {'fm': {**good, 'hooks': '[{"event": "Stop"}]'}}})
        check('a declaration that does not parse is a note, never a guess',
              bad == [] and notes and 'x:' in notes[0], repr(notes))


def check_install_and_update_name_the_code_owners():
    """Install and Update Vendors name a repository's code owners when it
    names none: everyone GitHub lists with edit access, in precedent.json's
    `maintainers`, or the person running it when GitHub cannot say. A list
    already set -- there, in approvers.json or a CODEOWNERS file -- is never
    touched.

    WHY. Morgan, 2026-10-06 (strength: decided): the code owners are "those
    who have access to edit *at that moment*. That becomes the started
    default." Fifteen of his repositories named nobody that day, which hid
    every code-owner practice from him in each of them."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    import precedent_audience as pa
    import github_budget as gb
    cases = []
    saved_call = gb.call
    saved_user = os.environ.get('PRECEDENT_GITHUB_USER')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-maintainers-'))
    try:
        def fresh(name, text='{\n  "base_branch": "main",\n  "sources": []\n}\n'):
            d = tmp / name
            d.mkdir()
            subprocess.run(['git', 'init', '-q', str(d)], env=_fixture_git_env(),
                           capture_output=True)
            (d / 'precedent.json').write_text(text, encoding='utf-8')
            return d

        a = fresh('a')
        got, how = pve.seed_maintainers(a, logins=['alice', 'Bob'], today='2026-10-06')
        cfg = json.loads((a / 'precedent.json').read_text(encoding='utf-8'))
        cases.append(('a repository naming nobody gets the list written',
                      got == ['alice', 'Bob']
                      and cfg.get('maintainers') == [{'github': 'alice'}, {'github': 'Bob'}],
                      f'{got} {cfg}'))
        cases.append(('...which the code-owner check then reads',
                      pa.owners(a)[0] == {'@alice', '@bob'}, str(pa.owners(a))))
        cases.append(('...keeping the rest of the file as it was',
                      (a / 'precedent.json').read_text(encoding='utf-8').endswith(
                          '  "base_branch": "main",\n  "sources": []\n}\n'), ''))
        got2, how2 = pve.seed_maintainers(a, logins=['mallory'])
        cases.append(('a list already set is never rewritten',
                      got2 == [] and 'already names' in how2, how2))

        # 2026-10-28: an approval names its person ("Name, date: ..."), and
        # a login alone matched none, so two consumers were fixed by hand.
        import precedent_identity as _pid
        saved_decl = _pid.declared_identity
        _pid.declared_identity = lambda repo, user_config=None: {
            'name': 'Fx Owner', 'github': 'fxowner', 'email': 'fx@example.invalid'}
        try:
            n1 = fresh('named')
            pve.seed_maintainers(n1, logins=['fxowner', 'other'], today='2026-10-28')
            m1 = json.loads((n1 / 'precedent.json').read_text(encoding='utf-8'))['maintainers']
            cases.append(("the person's own entry is written with their declared name, "
                          "and nobody else's is",
                          m1 == [{'github': 'fxowner', 'name': 'Fx Owner'},
                                 {'github': 'other'}], str(m1)))
            n2 = fresh('unnamed', '{\n  "maintainers": [{"github": "fxowner"}, '
                       '{"github": "other"}],\n  "sources": []\n}\n')
            got_n = pve.name_the_persons_maintainer(n2)
            m2 = json.loads((n2 / 'precedent.json').read_text(encoding='utf-8'))['maintainers']
            cases.append(("an existing entry with the person's login and no name gets "
                          "their name, and only that",
                          got_n == 'fxowner' and m2 == [
                              {'github': 'fxowner', 'name': 'Fx Owner'},
                              {'github': 'other'}], f'{got_n} {m2}'))
            cases.append(('...and a second run changes nothing',
                          pve.name_the_persons_maintainer(n2) == '', ''))
        finally:
            _pid.declared_identity = saved_decl

        b = fresh('b')
        (b / 'CODEOWNERS').write_text('* @carol\n', encoding='utf-8')
        got3, how3 = pve.seed_maintainers(b, logins=['dave'])
        cases.append(('a CODEOWNERS file counts as set',
                      got3 == [] and 'maintainers' not in json.loads(
                          (b / 'precedent.json').read_text(encoding='utf-8')), how3))

        gb.call = lambda path, **k: ([
            {'login': 'erin', 'type': 'User', 'permissions': {'push': True}},
            {'login': 'frank', 'type': 'User', 'permissions': {'pull': True}},
            {'login': 'helper[bot]', 'type': 'Bot', 'permissions': {'admin': True}},
            {'login': 'gina', 'type': 'User', 'permissions': {'admin': True}}], None)
        c = fresh('c')
        subprocess.run(['git', '-C', str(c), 'remote', 'add', 'origin',
                        'https://github.com/o/r.git'], capture_output=True)
        got4, how4 = pve.seed_maintainers(c, today='2026-10-06')
        cases.append(('from GitHub: everyone who can edit, readers and bots left out',
                      got4 == ['erin', 'gina'] and 'edit access' in how4, f'{got4} {how4}'))

        gb.call = lambda path, **k: (None, 'HTTP 403')
        os.environ['PRECEDENT_GITHUB_USER'] = 'hank'
        d = fresh('d')
        subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin',
                        'https://github.com/o/r.git'], capture_output=True)
        got5, how5 = pve.seed_maintainers(d, today='2026-10-06')
        cases.append(('GitHub unable to say: the person running it, and why',
                      got5 == ['hank'] and 'person running' in how5 and '403' in how5,
                      f'{got5} {how5}'))
        e = fresh('e')
        subprocess.run(['git', '-C', str(e), 'remote', 'add', 'origin',
                        'https://github.com/o/r.git'], capture_output=True)
        got6, how6 = pve.seed_maintainers(e, today='2026-10-11', fallback=['ivy'])
        cases.append(('GitHub unable to say and an administrator named at '
                      'install: that administrator, not the person running it',
                      got6 == ['ivy'] and 'administrator' in how6,
                      f'{got6} {how6}'))

        for f, needle in (('precedent_update.py', 'maintainers_step(repo, rep)'),
                          ('precedent_install.py', 'seed_maintainers(\n            dest')):
            cases.append((f'{f} runs it',
                          needle in (ROOT / 'tools' / f).read_text(encoding='utf-8'), ''))
    finally:
        gb.call = saved_call
        if saved_user is None:
            os.environ.pop('PRECEDENT_GITHUB_USER', None)
        else:
            os.environ['PRECEDENT_GITHUB_USER'] = saved_user
        shutil.rmtree(tmp, ignore_errors=True)
        sys.path.pop(0)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'install and update name the code owners when none are named '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_legacy_workflow_sweep_honours_the_persons_approval():
    """A workflow on the pre-Precedent names list that the person approved
    in github_ci_approved, in their own words and pinned to its content, is
    not left for the person again; one with no approval, or whose content
    has changed since, still is.

    WHY. 2026-10-28: a consumer's update dropped its local_ci_workflows
    declaration, which a consumer does not honour, and then stopped on its
    three approved checks, because this sweep read only that declaration."""
    import hashlib, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    rel = '.github/workflows/status-claims-check.yml'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        wf = root / rel
        wf.parent.mkdir(parents=True)
        wf.write_text('on: pull_request\njobs: {}\n', encoding='utf-8')

        def run(entry):
            (root / 'precedent.json').write_text(json.dumps(
                {'github_ci_approved': {rel: entry} if entry else {}}),
                encoding='utf-8')
            got = []
            orig = pve._left
            pve._left = lambda what, why: got.append(what)
            try:
                pve._retire_legacy_workflows(root, {}, 'consumer', None)
            finally:
                pve._left = orig
            return rel in got
        sha = hashlib.sha256(wf.read_bytes()).hexdigest()
        ok = {'sha256': sha,
              'approved_by': 'Zz, 2026-10-19: "yes, keep it"'}
        cases.append(('approved in the person\'s words, content unchanged: '
                      'not left again', not run(ok)))
        cases.append(('CONTROL: no approval: left for the person', run(None)))
        cases.append(('approved, but the content changed since: left',
                      run(dict(ok, sha256='0' * 64))))
        cases.append(('an approval that quotes nobody: left',
                      run(dict(ok, approved_by='Zz, 2026-10-19'))))
        # 2026-10-28, measured: an update starts the refresh with the
        # repository's own older engine, whose first pass had already left
        # the file; the second pass, finding it approved, must drop that.
        (root / 'precedent.json').write_text(json.dumps(
            {'github_ci_approved': {rel: ok}}), encoding='utf-8')
        pve._CARRIED_LEFT[:] = [(rel, 'found by the first pass')]
        try:
            pve._retire_legacy_workflows(root, {}, 'consumer', None)
            carried = [i for i, _w in pve._CARRIED_LEFT]
        finally:
            pve._CARRIED_LEFT.clear()
        cases.append(('approved: the first pass\'s finding of it is dropped too',
                      rel not in carried))
    bad = [n for n, ok_ in cases if not ok_]
    check(f'the pre-Precedent workflow sweep honours the person\'s approval '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_copy_in_clones_an_offered_set_it_said_yes_to():
    """An offered set this repository said yes to, with no clone on this
    machine, is cloned beside the individual set by the update itself and
    then copied in; one that cannot be cloned is named with the attach and
    the path; an offer nobody said yes to is not cloned.

    WHY. 2026-10-28, Update Vendors: a voice pack's yes read "not copied in
    yet, because there is no clone of the set on this machine", run after
    run, though the session could reach the set."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='offered-clone-'))
    cases = []
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    genv = _fixture_git_env()
    try:
        origin = tmp / 'origins' / 'zz-voice.git'
        origin.parent.mkdir()
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=genv, check=True)
        work = tmp / 'author'
        subprocess.run(['git', 'clone', '-q', str(origin), str(work)],
                       env=genv, capture_output=True, check=True)
        (work / 'practices').mkdir()
        (work / 'practices' / 'zz-v.md').write_text(
            '---\nslug: zz-v\n---\n# v\n\n## Rule\n\nSay it plainly.\n')
        (work / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-voice', 'level': 'shared', 'visibility': 'private'}))
        for a in (('add', '-A'), ('commit', '-qm', 'one'),
                  ('push', '-q', 'origin', 'main')):
            subprocess.run(['git', '-C', str(work), *a], env=genv,
                           capture_output=True, check=True)
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [],
             'offers': [{'name': 'zz-voice', 'repo_url': str(origin)},
                        {'name': 'zz-gone',
                         'repo_url': str(tmp / 'origins' / 'nowhere.git')},
                        {'name': 'zz-unasked', 'repo_url': str(origin)}]}))
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind',
                                                   'path': str(ind)}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        import precedent_vendor_engine as pve
        host = tmp / 'host'
        host.mkdir()
        by = 'Zzme, 2026-10-29: "yes"'
        (host / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private', 'sources': [],
             'copy_in': {'zz-voice': {'answer': 'yes', 'answered_by': by,
                                      'waits_on': 'there is no clone of the '
                                                  'set on this machine'}}},
            indent=2))
        got = pve.fetch_offered_clones(host, ['zz-gone'])
        clone = tmp / 'people' / 'zz-voice'
        cases.append(('a waiting yes: the set is cloned beside the individual '
                      'set', (clone / 'practices' / 'zz-v.md').is_file()
                      and any(w.startswith('zz-voice: cloned') for w in got),
                      repr(got)))
        gone = [w for w in got if w.startswith('zz-gone')]
        cases.append(('a set that cannot be cloned is named with the attach '
                      'and the path', len(gone) == 1 and 'add_repo' in gone[0]
                      and str(tmp / 'people' / 'zz-gone') in gone[0],
                      repr(gone)))
        cases.append(('NEGATIVE CONTROL: an offer nobody said yes to is not '
                      'cloned', not (tmp / 'people' / 'zz-unasked').exists()
                      and not any(w.startswith('zz-unasked') for w in got),
                      repr(got)))
        pending = pve.copy_in_pending(host)
        declared = [e for e in json.loads((host / 'precedent.json').read_text())
                    .get('sources') or [] if e.get('name') == 'zz-voice']
        cases.append(('...and the waiting yes is then declared copied in',
                      bool(declared), repr(pending)[:400]))
        cases.append(('a second run clones nothing again',
                      not any(w.startswith('zz-voice')
                              for w in pve.fetch_offered_clones(host))))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'copy-in clones an offered set it said yes to '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_engine_writes_the_persons_maintainer_name():
    """The update writes the person's declared name into their own
    maintainers entry when a different name was set there by hand, unless
    that would leave the repository's binds_everyone approval naming
    nobody; nobody else's entry is touched.

    WHY. 2026-10-28: two consumers carried "Morgan", set by hand before the
    engine wrote names, and a third the declared "Morgan F", because an
    entry with any name was never revisited."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
        import precedent_identity as _pid
    finally:
        sys.path.pop(0)
    cases = []
    saved = _pid.declared_identity
    _pid.declared_identity = lambda repo, user_config=None: {
        'name': 'Fx Owner', 'github': 'fxowner', 'email': 'fx@example.invalid'}

    def run(tmp, name, approval):
        d = pathlib.Path(tmp) / name
        d.mkdir()
        cfg = {'maintainers': [{'github': 'fxowner', 'name': name},
                               {'github': 'other', 'name': 'Other'}],
               'sources': []}
        if approval:
            cfg['binds_everyone'] = {'sets': ['zz'], 'approved_by': approval}
        (d / 'precedent.json').write_text(json.dumps(cfg, indent=2) + '\n')
        got = pve.name_the_persons_maintainer(d)
        return got, json.loads((d / 'precedent.json').read_text())['maintainers']

    try:
        with tempfile.TemporaryDirectory() as tmp:
            got, m = run(tmp, 'Fx', 'Fx, 2026-10-20: "yes"')
            cases.append(('a hand-set first name becomes the declared name, '
                          'which still matches the approval',
                          got == 'fxowner' and m == [
                              {'github': 'fxowner', 'name': 'Fx Owner'},
                              {'github': 'other', 'name': 'Other'}], f'{got} {m}'))
            got, m = run(tmp, 'Boss', 'Boss, 2026-10-20: "yes"')
            cases.append(('NEGATIVE CONTROL: a rename that would orphan the '
                          'approval is not made',
                          got == '' and m[0]['name'] == 'Boss', f'{got} {m}'))
            got, m = run(tmp, 'Fx Owner', None)
            cases.append(('the declared name already there: nothing written',
                          got == '', f'{got} {m}'))
    finally:
        _pid.declared_identity = saved
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the engine writes the person\'s maintainer name '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_second_pass_judgment_replaces_first_pass_left():
    """A section the second pass of a self-replacing refresh settles is not
    left for the person on the first pass's word.

    THE INCIDENT (2026-10-08, a consuming repository's Update Vendors). The
    report said "kept pin updated" for AGENTS.md's "### Session start" and,
    in the same run, still listed it under LEFT FOR YOU; the next run was
    clean. The first pass (the older engine copy) left the section; the
    second pass, with the new copy, re-pinned it -- and the first pass's
    item, carried over in _CARRIED_LEFT, was printed because the second
    pass had not found it itself. Planted: a kept section the second pass
    re-pins, carrying the first pass's item for it; and the control, an
    'absent' section, whose carried item is the one the second pass cannot
    find again and must keep."""
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    key = '### Session start'
    other = '### Two check levels'
    item = f'AGENTS.md {key}'
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        tpl, dest = td / 'tpl', td / 'dest'
        tpl.mkdir(); dest.mkdir()
        (tpl / 'T.md').write_text(
            f'# T\n\n{key}\n\n- **Our own line.** Fine.\n\n'
            f'- **Upstream block here.** It says a thing.\n', encoding='utf-8')
        (dest / 'AGENTS.md').write_text(
            f'# T\n\n{key}\n\n- **Our own line.** Fine.\n', encoding='utf-8')
        section = pve._template_sections(
            (tpl / 'T.md').read_text(encoding='utf-8'))[key][1]
        # Pinned on the template's text alone, as before 2026-10-01: this
        # pass matches it and upgrades it, printing PIN UPDATED.
        # Since 2026-10-31 the block it lacks needs its own verdict too.
        lacked = [t for _o, t, _h, _a in pve.missing_markdown_blocks(
            (dest / 'AGENTS.md').read_text(encoding='utf-8').split('\n', 2)[2], section)]
        (dest / 'precedent.json').write_text(json.dumps({
            pve.KEPT_DIVERGENCES_KEY: {item: {
                'reason': 'ours', 'template_sha256': pve._sha_text(section),
                'blocks': {pve.block_id(t): {'verdict': 'covered', 'quote': 'Our own line'}
                           for t in lacked}}}}),
            encoding='utf-8')
        pve._LEFT_FOR_YOU.clear()
        pve._CARRIED_LEFT[:] = [
            (f'AGENTS.md "{key}"', 'diverged from T.md and lacks 1 of its '
             'blocks (listed above)'),
            (f'AGENTS.md "{other}"', 'the template has this section and this '
             'file does not')]
        plan = [(key, 'T.md', 3, 'diverged', (2, 5)),
                (other, 'T.md', 9, 'absent', None)]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                pve._report_agents_md(dest, tpl, plan)
                pve.print_left_for_you()
        finally:
            pve._LEFT_FOR_YOU.clear()
            pve._CARRIED_LEFT.clear()
        out = buf.getvalue()
        left = out.split('Left for you', 1)[1] if 'Left for you' in out else ''
        cases.append(('this pass re-pinned the kept section', 'PIN UPDATED' in out))
        cases.append(('...and the first pass\'s item for it is not left',
                      key not in left))
        cases.append(('CONTROL: an absent section\'s carried item still is',
                      other in left))
    bad = [n for n, ok in cases if not ok]
    check(f'a section the second pass settles is not left on the first '
          f'pass\'s word ({len(cases)} stated cases)', not bad,
          '; '.join(bad) + ' :: ' + failure_detail(out, 600) if bad else '')


def check_kept_section_reports_upstreams_change_not_its_lacks():
    """A section kept on purpose whose template text changed is reported as
    upstream's own change since the pinned text, and re-pinned by itself
    when that change is formatting alone.

    WHY. 2026-10-07, a consuming repository's Update Vendors: two kept
    AGENTS.md sections came back as long "lacks" lists -- every block they
    have always left out on purpose -- when the template's only change to
    them was file names in code spans becoming links, found by a manual git
    diff. Planted: a links-only change re-pins and prints PIN UPDATED, with
    nothing left for the person; a change of words prints the template's
    diff and leaves one item; a pin no version of the template matches
    falls back to the full report."""
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    key = '## Admin requests'
    old = key + '\n\nEdit `tools/x.py` and run the check.\n'
    links = key + '\n\nEdit [tools/x.py](tools/x.py) and run the check.\n'
    words = key + '\n\nEdit [tools/x.py](tools/x.py) and run both checks.\n'
    item = f'AGENTS.md {key}'
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        tpl, dest = td / 'tpl', td / 'dest'
        tpl.mkdir(); dest.mkdir()
        (tpl / pve._AGENTS_MD_HISTORY_NAME).write_text(
            json.dumps({key: [old, links]}), encoding='utf-8')

        def run(section, pinned, local=None):
            (dest / 'precedent.json').write_text(json.dumps({pve.KEPT_DIVERGENCES_KEY: {
                item: {'reason': 'ours', 'template_sha256': pinned}}}), encoding='utf-8')
            pve._LEFT_FOR_YOU.clear()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                done = pve._report_stale_kept(dest, tpl, key, item, 'the template',
                                              section, pve._sha_text(section), 'c' * 64, {},
                                              local=local)
            entry = json.loads((dest / 'precedent.json').read_text(
                encoding='utf-8'))[pve.KEPT_DIVERGENCES_KEY][item]
            return done, buf.getvalue(), list(pve._LEFT_FOR_YOU), entry
        done, out, left, entry = run(links, pve._sha_text(old))
        cases.append(('a links-only change re-pins by itself',
                      done and 'PIN UPDATED' in out and not left
                      and entry['template_sha256'] == pve._sha_text(links)))
        done, out, left, entry = run(words, pve._sha_text(old))
        cases.append(('a change of words shows the template\'s own diff',
                      done and '-Edit `tools/x.py` and run the check.' in out
                      and '+Edit [tools/x.py](tools/x.py) and run both checks.' in out
                      and 'lacks' not in out))
        cases.append(('...leaves one item, and keeps the old pin',
                      len(left) == 1 and entry['template_sha256'] == pve._sha_text(old)))
        done, out, left, entry = run(words, 'f' * 64)
        cases.append(('a pin no template version matches falls back',
                      done is False and not out))
        # 2026-10-07: upstream's new wording already in the section -- the
        # consumer had written it first -- re-pins with nothing to decide.
        mine = key + '\n\nOur own lead line.\n\nEdit tools/x.py and run both checks.\n'
        done, out, left, entry = run(words, pve._sha_text(old), local=mine)
        cases.append(('a change of words this section already carries re-pins by itself',
                      done and 'PIN UPDATED' in out and 'already in' in out and not left
                      and entry['template_sha256'] == pve._sha_text(words)))
        theirs_old = key + '\n\nOur own lead line.\n\nEdit tools/x.py and run the check.\n'
        done, out, left, entry = run(words, pve._sha_text(old), local=theirs_old)
        cases.append(('one whose new wording is not here still leaves the call, '
                      'naming the re-pin command, never raw hashes',
                      done and len(left) == 1 and 'repin-kept' in left[0][1]
                      and '--confirmed' in left[0][1] and 'set its template_sha256' not in out
                      and '(listed above)' in left[0][1]))
        # 2026-10-08, Morgan (decided): upstream's wording is the default, and
        # this repository's is kept only where it does something different
        # and important -- so a change that reaches the kept lines says so.
        # 2026-10-14, Morgan (decided): keep only what is this repository's
        # own, and re-pin that without asking him; he hears only a close call.
        cases.append(('...and says the default is upstream\'s section, keeping this '
                      'repository\'s only where it is its own, re-pinned by the '
                      'session and asked only on a close call',
                      "the default is upstream's" in left[0][1]
                      and "this repository\'s own" in left[0][1]
                      and '--by-rule' in left[0][1] and 'close call' in left[0][1]
                      and 'remove the kept_template_divergences entry' in left[0][1]
                      and "the default is upstream's wording" in out))
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_update as _pu
        got = _pu.diverged_details(out)
        cases.append(('Update Vendors carries that diff under the item',
                      any(k.endswith(f'"{key}"') and any('run both checks' in l for l in v)
                          for k, v in got.items())))
    pve._LEFT_FOR_YOU.clear()
    bad = [n for n, ok in cases if not ok]
    check(f'a stale kept section shows upstream\'s change, not its lacks '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_kept_section_repins_a_change_that_misses_the_kept_lines():
    """A kept AGENTS.md section whose template changed only in lines the
    consumer carries as upstream wrote them re-pins by itself, with a report
    line; a change that touches a line the consumer changed still asks.

    WHY. 2026-10-08, a consuming repository: a kept section was re-raised
    with "with the person's yes, re-pin it" for a template rewording
    elsewhere in the section, which no difference the consumer kept could
    be affected by. The judgment is three-way, against the pinned template
    text (precedent_vendor_engine._change_touches_local), and conservative:
    a change beside a consumer's line counts as touching it, and no local
    text at all asks. The consumer's section is never rewritten.

    Negative control, measured 2026-10-08 against
    2026-10-08-produce-copy-check-y1ktn at ae07871f: the change elsewhere
    leaves an item for the person (the first case fails)."""
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    key = '## Working in this repo'
    para = lambda a, b, c, extra='': (f'{key}\n\n{a}\n\n{extra}{b}\n\n{c}\n')
    old = para('Run the light check first.', 'Then the deep check.', 'Push last.')
    local = para('Run our own light check first.', 'Then the deep check.', 'Push last.')
    elsewhere = para('Run the light check first.', 'Then the deep check.',
                     'Push only once both pass.')
    touching = para('Run the light check before every commit.', 'Then the deep check.',
                    'Push last.')
    beside = para('Run the light check first.', 'Then the deep check.', 'Push last.',
                  extra='A new paragraph upstream added here.\n\n')
    item = f'AGENTS.md {key}'
    touches = getattr(pve, '_change_touches_local', lambda *_a: None)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        tpl, dest = td / 'tpl', td / 'dest'
        tpl.mkdir(); dest.mkdir()
        (tpl / pve._AGENTS_MD_HISTORY_NAME).write_text(
            json.dumps({key: [old, elsewhere, touching, beside]}), encoding='utf-8')
        agents = f'# Repo\n\n{local}'

        def run(section, here):
            (dest / 'precedent.json').write_text(json.dumps({pve.KEPT_DIVERGENCES_KEY: {
                item: {'reason': 'we run our own light check',
                       'template_sha256': pve._sha_text(old)}}}), encoding='utf-8')
            (dest / 'AGENTS.md').write_text(agents, encoding='utf-8')
            pve._LEFT_FOR_YOU.clear()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                done = pve._report_stale_kept(dest, tpl, key, item, 'the template',
                                              section, pve._sha_text(section), 'c' * 64,
                                              {}, local=here)
            entry = json.loads((dest / 'precedent.json').read_text(
                encoding='utf-8'))[pve.KEPT_DIVERGENCES_KEY][item]
            return (done, buf.getvalue(), list(pve._LEFT_FOR_YOU), entry,
                    (dest / 'AGENTS.md').read_text(encoding='utf-8'))
        done, out, left, entry, after = run(elsewhere, local)
        cases.append(('a rewording of a line this section carries as upstream wrote it '
                      're-pins by itself, with a report line',
                      done and not left and 'PIN UPDATED' in out
                      and 'touches no line' in out
                      and entry['template_sha256'] == pve._sha_text(elsewhere),
                      (left, out)))
        cases.append(('...and the section keeps its own text', after == agents, after))
        done, out, left, entry, after = run(touching, local)
        cases.append(('a change to the line this section changed still asks, and keeps '
                      'the old pin',
                      done and len(left) == 1 and 'repin-kept' in left[0][1]
                      and entry['template_sha256'] == pve._sha_text(old), (left, out)))
        done, out, left, entry, after = run(beside, local)
        cases.append(('a paragraph added right beside that line counts as touching it: '
                      'asks', done and len(left) == 1
                      and entry['template_sha256'] == pve._sha_text(old), (left, out)))
        cases.append(('...wherever the matcher places the insertion among the blank '
                      'lines', all(touches(old, beside, local)
                                   for local in (local, local.replace('\n\n', '\n\n\n')))
                      and touches(
                          old, old.replace('Then the deep check.\n',
                                           'Then the deep check.\n\nAdded.\n'),
                          old.replace('Then the deep check.', 'Then ours.')), ''))
        done, out, left, entry, after = run(elsewhere, None)
        cases.append(('with no local text to read, it asks', done and len(left) == 1,
                      (left, out)))
        cases.append(('the read is three-way against the pinned text, either order',
                      touches(old, touching, local)
                      and not touches(old, elsewhere, local)
                      and not touches(old, local, elsewhere), ''))
    pve._LEFT_FOR_YOU.clear()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_refresh_adds_read_only_allow_rules():
    """The refresh adds the settings template's Precedent tool rules to a
    consumer's .claude/settings.json, add-only (2026-10-14: a consumer
    allowed none of them, and auto mode woke the person over a
    precedent_show.py read). Since 2026-10-17 (Morgan: "why not include all
    on that list except a small list we explicitly want to exclude ... to
    get the session user's permission", then "yes, build it") the template
    allows every engine tool with one rule and asks for the tools that land,
    produce, merge or update other repositories. THE DISCRIMINATING CASES:
    the broad rule is never written without every ask rule beside it, and a
    repository that declines an ask rule keeps
    its tools allowed one by one. Both go into the file in one write."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    tpl = (ROOT / pve.SETTINGS_TEMPLATE).read_text(encoding='utf-8')
    rules = pve.read_only_allow_rules(tpl)
    ask = pve.engine_ask_rules(tpl) if hasattr(pve, 'engine_ask_rules') else []
    broad = getattr(pve, 'ENGINE_ALLOW_RULE', None)
    cases.append(('the template allows every engine tool with one rule',
                  bool(broad) and broad in rules, rules))
    cases.append(('no write-capable rule is taken from the template as an allow',
                  rules and all(pve.is_read_only_allow_rule(r) for r in rules)
                  and not any('push' in r or 'checkin' in r or 'commit' in r for r in rules),
                  rules))
    cases.append(('every read-only tool outside precedent_* still has its own rule',
                  {pve._ALLOW_RULE_RE.match(r).group(1) for r in rules
                   if r != broad and pve._ALLOW_RULE_RE.match(r)}
                  >= {t for t in pve.READ_ONLY_ALLOW_TOOLS
                      if not t.startswith('precedent_')}, rules))
    # 2026-10-18: the template asks before nothing (Morgan: "I urgently need
    # a fix so you stop asking me so much").
    cases.append(('the template asks before nothing', ask == [], ask))

    def fixture(td, own, declined=()):
        dest = pathlib.Path(td)
        (dest / '.claude').mkdir()
        (dest / 'tools').mkdir()
        for t in pve.READ_ONLY_ALLOW_TOOLS:
            if t != 'routing_audit.py':
                (dest / 'tools' / t).write_text('', encoding='utf-8')
        sp = dest / '.claude' / 'settings.json'
        sp.write_text(json.dumps(own), encoding='utf-8')
        (dest / 'precedent.json').write_text(json.dumps(
            {pve.DECLINED_ALLOW_KEY: list(declined)}), encoding='utf-8')
        return dest, sp
    own = {'permissions': {'allow': ['Bash(make test)',
                                     'Bash(python3 tools/doc_lint.py)'],
                           'deny': ['Bash(python3 tools/routing_audit.py *)']},
           'hooks': {}}
    with tempfile.TemporaryDirectory() as td:
        dest, sp = fixture(td, own)
        before = sp.read_text(encoding='utf-8')
        try:
            pve._apply_read_only_allow(dest, rules, ask)
            ok_call = True
        except TypeError:
            ok_call = False
        after = json.loads(sp.read_text(encoding='utf-8'))
        perms = after['permissions']
        allow = perms['allow']
        cases.append(('THE DISCRIMINATING CASE: the broad rule is added on its own, '
                      'with no ask rule beside it',
                      ok_call and broad in allow and not perms.get('ask'), perms))
        cases.append(('what was there stays first and unchanged',
                      allow[:2] == own['permissions']['allow']
                      and perms['deny'] == own['permissions']['deny'], allow))
        cases.append(('a rule already allowed or denied, or for a tool not in tools/, '
                      'is not added',
                      allow.count('Bash(python3 tools/doc_lint.py)') == 1
                      and not any('routing_audit' in r for r in allow), allow))
        cases.append(('the change reads as refresh output, not a person\'s edit',
                      pve.settings_change_is_wiring_only(before, sp.read_text(encoding='utf-8')),
                      ''))
        cases.append(('a second run adds nothing',
                      ok_call and pve._apply_read_only_allow(dest, rules, ask) == [], ''))
    with tempfile.TemporaryDirectory() as td:
        dest, sp = fixture(td, own, declined=[broad])
        if ok_call:
            pve._apply_read_only_allow(dest, rules, ask)
        perms = json.loads(sp.read_text(encoding='utf-8'))['permissions']
        cases.append(('a repository that declines the broad rule does not get it',
                      broad not in perms['allow'], perms))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the refresh adds read-only Precedent tool allow rules ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))



def check_attaching_a_source_needs_no_prompt():
    """A session attaches and clones its declared practice sources with no
    permission prompt (Morgan, 2026-10-27: "This is a high priority fix";
    practice: attach-never-clone-individual). The template allows add_repo
    and register_repo_root; the refresh adds the clone command add_repo's
    reply prescribes, for the declared sources' owners only.
    THE DISCRIMINATING CASES: the reply's exact clone command matches a rule
    for a declared owner and no rule for any other owner, and a fixture
    whose individual set brings a second owner gets that owner's rules too."""
    import fnmatch
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    tpl = (ROOT / pve.SETTINGS_TEMPLATE).read_text(encoding='utf-8')
    rules = pve.read_only_allow_rules(tpl)
    cases.append(('the template allows add_repo and register_repo_root',
                  all(r in rules for r in pve.ATTACH_ALLOW_RULES), rules))
    clone = pve.clone_allow_rules(['owner'])

    def allowed(cmd, rs):
        return any(fnmatch.fnmatchcase(cmd, r[len('Bash('):-1])
                   for r in rs if r.startswith('Bash('))
    reply = ('GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 '
             'https://github.com/owner/precedent-individual '
             '/home/user/precedent-individual')
    cases.append(("THE DISCRIMINATING CASE: add_repo's clone command is allowed "
                  "for a declared owner", allowed(reply, clone), clone))
    cases.append(('and not for any other owner',
                  not allowed(reply.replace('owner', 'stranger'), clone), clone))
    cases.append(('the plain clone shape is allowed too',
                  allowed('git clone https://github.com/owner/x /home/user/x', clone),
                  clone))
    cases.append(('every clone rule reads as an engine rule, so a refresh that '
                  'adds one is not a person\'s edit',
                  all(pve.is_read_only_allow_rule(r) for r in clone), clone))
    cases.append(('an owner that is not a GitHub name gets no rule',
                  pve.clone_allow_rules(['a b', '*', '']) == [], ''))
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        ind = td / 'precedent-individual'
        ind.mkdir()
        (ind / 'precedent-source.json').write_text(json.dumps({'brings': [
            {'name': 'precedent-shared-x',
             'repo_url': 'https://github.com/example/precedent-shared-x'}]}),
            encoding='utf-8')
        cfg = td / 'config.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(ind),
            'repo_url': 'https://github.com/owner/precedent-individual'}}),
            encoding='utf-8')
        env = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',
                                              'PRECEDENT_SOURCE_BASE_URL')}
        os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
        os.environ.pop('PRECEDENT_SOURCE_BASE_URL', None)
        try:
            owners = pve.source_owners(td)
        finally:
            for k, v in env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    cases.append(('the owners are the individual set and the sets it brings',
                  owners == ['example', 'owner'], owners))
    tpl_allow, _ = pve._refresh_allow_rules('consumer', tpl, ROOT)
    src_allow, src_ask = pve._refresh_allow_rules('source', tpl, ROOT)
    cases.append(('THE DISCRIMINATING CASE for sets: a practice set gets the attach '
                  'rules too, and none of the engine tool rules',
                  all(r in src_allow for r in pve.ATTACH_ALLOW_RULES)
                  and pve.ENGINE_ALLOW_RULE not in src_allow and src_ask == []
                  and pve.ENGINE_ALLOW_RULE in tpl_allow, src_allow))
    cases.append(('a manifest with no kind gets nothing',
                  pve._refresh_allow_rules(None, tpl, ROOT) == ([], []), ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'attaching a declared practice source needs no prompt ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))

def check_document_project_agents_md_is_compared_with_its_own_template():
    """A repo made from templates/document-project/AGENTS.md is compared with
    that template, never the loader template (2026-10-17, issue #1172: a
    document project's update showed seven of its sections as DIVERGED and
    four loader-only sections as MISSING, and never reported real drift from
    its own template). Declared in precedent.json, or read from the headings
    only that template has; any other consumer is compared as before.

    Negative control: on staging's code there is no agents_md_templates, and
    the plan is the loader template's."""
    import tempfile, shutil
    name = 'a document project\'s AGENTS.md is compared with its own template'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    cases = []
    pick = getattr(pve, 'agents_md_templates', None)
    cases.append(('the engine picks a template per repository', callable(pick)))
    doc = ROOT / 'templates' / 'document-project' / 'AGENTS.md'
    loader = ROOT / 'templates' / 'AGENTS.md.loader.template'
    if callable(pick) and doc.is_file() and loader.is_file():
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            src = td / 'src'
            src.mkdir()
            pve._read_agents_md_sources(ROOT, 'HEAD', 'consumer', src)
            dest = td / 'repo'
            (dest / 'tools').mkdir(parents=True)
            shutil.copy(doc, dest / 'AGENTS.md')
            plan = pve._agents_md_plan(dest, 'consumer', src, {})
            used = {p[1] for p in plan}
            keys = {p[0] for p in plan}
            cases.append(('a document project is planned against its own template',
                          used == {'templates/document-project/AGENTS.md'}, used))
            cases.append(('...so no loader-only section is reported MISSING',
                          not any('Working in parallel' in k for k in keys)
                          and not any(p[3] == 'missing' for p in plan),
                          [(p[0], p[3]) for p in plan if p[3] != 'current']))
            shutil.copy(loader, dest / 'AGENTS.md')
            (dest / 'precedent.json').write_text(
                json.dumps({'agents_md_template': 'document-project'}), encoding='utf-8')
            cases.append(('declared in precedent.json, it is a document project '
                          'whatever its headings',
                          pick(dest, 'consumer') == ('templates/document-project/AGENTS.md',)))
            (dest / 'precedent.json').unlink()
            cases.append(('CONTROL: any other consumer is compared with the loader '
                          'template, as before',
                          pick(dest, 'consumer')[0] == 'templates/AGENTS.md.loader.template'))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + str(d)[:300] + ')' if d else ''}" for n, d in bad))


def check_repin_kept_records_the_persons_words():
    """`precedent_vendor_engine.py repin-kept` re-pins one kept AGENTS.md
    section against today's template and records who confirmed it and
    when -- the command the stale-kept call names, in place of two
    SHA-256 values pasted into precedent.json by hand, which a session's
    own safety checks refused as editing an audit record (2026-10-07). It
    refuses without the person's words, without a reason given with the
    decision, and for a section not recorded as kept; the reason it is given
    replaces the one recorded before (2026-10-13: a consumer's re-pin kept a
    reason describing a section that no longer existed in that form)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    key = '## Session start'
    tpl_text = f'# T\n\n{key}\n\nKeep this file\'s generated block current.\n'
    names = ('_read_agents_md_sources', '_rev', '_load_manifest')
    saved = {n: getattr(pve, n) for n in names}
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        dest = td / 'repo'
        (dest / 'tools').mkdir(parents=True)
        (dest / 'AGENTS.md').write_text(
            f'# Repo\n\n{key}\n\nOur own line.\n\nKeep this file\'s generated '
            f'block current.\n', encoding='utf-8')
        item = f'AGENTS.md {key}'
        (dest / 'precedent.json').write_text(json.dumps({pve.KEPT_DIVERGENCES_KEY: {
            item: {'reason': 'ours', 'template_sha256': 'f' * 64}}}), encoding='utf-8')
        src = pve.AGENTS_MD_TEMPLATES.get('consumer', ('AGENTS.md.template',))[0]
        try:
            def fake_read(clone, commit, kind, out):
                (out / src).parent.mkdir(parents=True, exist_ok=True)
                (out / src).write_text(tpl_text, encoding='utf-8')
                (out / pve._AGENTS_MD_HISTORY_NAME).write_text('{}', encoding='utf-8')
            pve._read_agents_md_sources = fake_read
            pve._rev = lambda repo, ref: 'a' * 40
            pve._load_manifest = lambda d: {'kind': 'consumer', 'source_commit': 'a' * 40}
            ok, msg = pve.repin_kept_section(td, 'AGENTS.md ## Session start', '',
                                             dest_root=dest, reason='still ours')
            cases.append(('refuses without the person\'s words', not ok, msg))
            before = (dest / 'precedent.json').read_text(encoding='utf-8')
            ok, msg = pve.repin_kept_section(td, item, 'Morgan: still kept', dest_root=dest)
            cases.append(('refuses without a reason, writing nothing',
                          not ok and '--reason' in msg
                          and (dest / 'precedent.json').read_text(encoding='utf-8') == before,
                          msg))
            ok, msg = pve.repin_kept_section(td, 'AGENTS.md ## Nowhere', 'yes',
                                             dest_root=dest, reason='x')
            cases.append(('refuses a section not recorded as kept', not ok, msg))
            ok, msg = pve.repin_kept_section(td, item, 'Morgan: still kept', dest_root=dest,
                                             reason='Our own line stays: it names our hook')
            entry = json.loads((dest / 'precedent.json').read_text(
                encoding='utf-8'))[pve.KEPT_DIVERGENCES_KEY][item]
            want = pve._sha_text(pve._instantiate(
                pve._template_sections(tpl_text)[key][1],
                pve._agents_md_subs(dest)))
            cases.append(('re-pins to today\'s template text',
                          ok and entry['template_sha256'] == want, f'{msg} {entry}'))
            cases.append(('...and records the person\'s words and the new reason, '
                          'not the one from before the decision',
                          entry.get('confirmed') == 'Morgan: still kept'
                          and entry.get('reason') == 'Our own line stays: it names our hook',
                          str(entry)))
            cases.append(('the command a stale kept section names carries --reason',
                          '--reason' in pve._repin_command(item), pve._repin_command(item)))
            # 2026-10-14, Morgan (decided): "Let repin-kept re-pin
            # repo-specific differences without asking me".
            ok, msg = pve.repin_kept_section(td, item, '', dest_root=dest,
                                             reason='our audits fill the placeholder',
                                             by_rule=True)
            entry = json.loads((dest / 'precedent.json').read_text(
                encoding='utf-8'))[pve.KEPT_DIVERGENCES_KEY][item]
            cases.append(('--by-rule re-pins without the person\'s words, recording '
                          'the standing rule and decided_by: rule',
                          ok and entry.get('decided_by') == 'rule'
                          and entry.get('confirmed') == pve.STANDING_KEEP_RULE
                          and 'standing rule' in msg, f'{msg} {entry}'))
            ok, msg = pve.repin_kept_section(td, item, 'Morgan: yes', dest_root=dest,
                                             reason='x', by_rule=True)
            cases.append(('--by-rule and --confirmed together are refused', not ok, msg))
            ok, msg = pve.repin_kept_section(td, item, 'Morgan: still kept', dest_root=dest,
                                             reason='close call, asked')
            entry = json.loads((dest / 'precedent.json').read_text(
                encoding='utf-8'))[pve.KEPT_DIVERGENCES_KEY][item]
            cases.append(('the person\'s words after a rule re-pin drop decided_by',
                          ok and 'decided_by' not in entry, str(entry)))
            cases.append(('the command a stale kept section names is --by-rule',
                          '--by-rule' in pve._repin_command(item)
                          and '--confirmed' not in pve._repin_command(item),
                          pve._repin_command(item)))
        finally:
            for n, f in saved.items():
                setattr(pve, n, f)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'repin-kept re-pins a kept section by the standing rule or the person\'s words '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:200]}' for n, d in bad))
def check_repo_names_compare_without_case():
    """Two spellings of one GitHub repository are one repository everywhere
    the engine compares them, and a raw comparison cannot come back
    (tools/precedent_repo_id.py; Morgan, 2026-10-31, decided: "the same
    repo with different capitalization should be treated equally").

    THE COST IT PAID FOR (2026-10-31). add_repo answers a capitalized
    owner/SomeSet in lowercase; a session followed it and the person was
    asked to approve one repository twice. The freshness check's
    `origin == repo_url` then read the lowercase clone of the declared
    capitalized source as NOT VERIFIED.

    Cases, both directions: the forms seen in the wild (https, .git, ssh,
    the local git proxy, a bare owner/repo) are one repository however they
    are capitalized; a different owner, and a case-sensitive host, are not;
    the declared spelling is what is written back; and the scanner the
    engine check runs flags the freshness check's old comparison (the
    negative control: the code before the fix) and passes the code now."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_repo_id as rid
    cases = []
    same = [('https://github.com/owner/SomeSet', 'https://github.com/owner/someset.git'),
            ('git' + '@github.com:owner/SomeSet.git', 'owner/someset'),
            ('http://local_proxy@127.0.0.1:41799/git/owner/someset',
             'https://github.com/owner/SomeSet/'),
            ('SomeSet', 'https://github.com/owner/someset')]
    for a, b in same:
        cases.append((f'{a} and {b} are one repository', rid.same_repo(a, b),
                      f'{rid.repo_key(a)} vs {rid.repo_key(b)}'))
    for a, b in [('https://github.com/a/x', 'https://github.com/b/x'),
                 ('https://git.example.org/a/Repo', 'https://git.example.org/a/repo'),
                 ('', ''), ('/home/user/x', 'x')]:
        cases.append((f'{a!r} and {b!r} are not one repository',
                      not rid.same_repo(a, b), 'same_repo said True'))
    wrote = rid.declared_spelling('https://github.com/owner/someset',
                                  declared=['https://github.com/owner/SomeSet'])
    cases.append(('the declared spelling is written back, never the origin',
                  wrote == 'https://github.com/owner/SomeSet', repr(wrote)))
    with tempfile.TemporaryDirectory() as d:
        before = pathlib.Path(d) / 'before.py'
        before.write_text(
            'def upstream_tip(repo_url, clone):\n'
            '    rc, origin = 0, git(clone)\n'
            '    if rc == 0 and origin and origin == repo_url:\n'
            '        return 1\n', encoding='utf-8')
        hits = rid.raw_comparisons(before)
        cases.append(("the scanner flags the freshness check's old `origin == "
                      "repo_url` (negative control)",
                      [l for l, _ in hits] == [3], repr(hits)))
        okd = pathlib.Path(d) / 'ok.py'
        okd.write_text('x = origin == repo_url  # repo-name-compare: ok -- a test\n',
                       encoding='utf-8')
        cases.append(('a line marked ok with a why is let through',
                      rid.raw_comparisons(okd) == [], repr(rid.raw_comparisons(okd))))
    now = rid.raw_comparisons(ROOT / 'tools' / 'precedent_engine_freshness.py')
    cases.append(('the freshness check now compares through the helper',
                  now == [], repr(now)))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'repository names compare without regard to case '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_copy_in_question_names_what_would_leak():
    """Morgan, 2026-10-19, on the question asked before copying a set into
    a public repository: "Maybe it should also run some sort of leak gate
    to review names of repos etc to make them general."

    1. A set whose practice names a repository under a private owner, and
       a word on the repository's own scrub list, gets both lines named.
    2. The set's own name in its own repository is not a hit.
    3. A file the copy never brings (the set's README) is not read.
    4. A carried set's files are read.
    5. The question lists the hits, or says the set is clean.
    6. NEGATIVE CONTROL: the same set with the lines made general is clean."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='copy-in-leaks-'))
    saved = os.environ.get('PRECEDENT_LEAK_BLOCKLIST')
    cases = []
    try:
        bl = tmp / 'private' / 'leak-blocklist.txt'
        bl.parent.mkdir()
        bl.write_text('# visibility-audit: private-owner zzowner -- every '
                      'repo is private\nzzsecretword\n')
        os.environ['PRECEDENT_LEAK_BLOCKLIST'] = str(bl)
        dest = tmp / 'dest'
        (dest / 'process').mkdir(parents=True)
        (dest / 'process' / 'scrub_blocklist.txt').write_text(
            '# this repo\'s words\nzzclientname\n')
        s = tmp / 'zz-set'
        (s / 'practices').mkdir(parents=True)
        (s / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-set', 'level': 'shared', 'visibility': 'public',
             'carries': [{'name': 'zz-inner', 'path': 'inner'}]}))
        rule = s / 'practices' / 'zz-rule.md'
        rule.write_text('---\nslug: zz-rule\n---\n# r\n\n## Rule\n\n'
                        'See zzowner/zz-hidden-repo for the story.\n'
                        'Found with zzclientname.\n')
        (s / 'README.md').write_text('zzowner/zz-readme-only\n')
        (s / 'inner' / 'practices').mkdir(parents=True)
        (s / 'inner' / 'practices' / 'zz-inner.md').write_text(
            '---\nslug: zz-inner\n---\n# i\n\n## Rule\n\nzzsecretword\n')
        hits, note = pve.copy_in_leaks(s, dest)
        joined = '\n'.join(hits)
        cases.append(('a private-owner repository is named',
                      'zzowner/zz-hidden-repo' in joined, joined))
        cases.append(("the repository's own scrub word is named",
                      'zzclientname' in joined, joined))
        cases.append(('a file the copy never brings is not read',
                      'zz-readme-only' not in joined, joined))
        cases.append(("a carried set's file is read",
                      'inner/practices/zz-inner.md' in joined, joined))
        cases.append(('the private list counts as configured', note == '', note))
        q = pve.copy_in_question({'name': 'zz-set', 'default': 'no',
                                  'why': 'w', 'public': True, 'clone': s,
                                  'leaks': hits, 'leak_note': note})
        cases.append(('the question lists the hits',
                      'would be published' in q and 'zz-hidden-repo' in q, q))
        # NEGATIVE CONTROL
        rule.write_text('---\nslug: zz-rule\n---\n# r\n\n## Rule\n\n'
                        'See a private repository for the story.\n')
        (s / 'inner' / 'practices' / 'zz-inner.md').write_text(
            '---\nslug: zz-inner\n---\n# i\n\n## Rule\n\nplain\n')
        hits2, _ = pve.copy_in_leaks(s, dest)
        cases.append(('NEGATIVE CONTROL: made general, the set is clean',
                      hits2 == [], hits2))
        q2 = pve.copy_in_question({'name': 'zz-set', 'default': 'no',
                                   'why': 'w', 'public': True, 'clone': s,
                                   'leaks': [], 'leak_note': ''})
        cases.append(('a clean set is said to be clean',
                      'found nothing' in q2, q2))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        else:
            os.environ['PRECEDENT_LEAK_BLOCKLIST'] = saved
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the copy-in question names the lines a public copy would '
          f'publish ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:500]}" for n, d in bad))


def check_a_sets_own_hooks_are_registered_in_a_session_rooted_in_it():
    """A practice set's own `hooks:` run in a session rooted in the set
    (2026-10-17 very deep check: precedent_materialize was not in the source
    engine's file list, so the session file printed "No module named
    'precedent_materialize'", and only a consumer's sync ever wrote
    process/practice_hooks.json, so no set registered its own hooks).

    Stated cases: a set's engine carries precedent_materialize.py and the
    module it imports; the session file run in a set registers the set's own
    practice hook in .precedent/practice_hooks.json; an engine without the
    module gets one plain sentence, never a ModuleNotFoundError."""
    import contextlib, io, shutil, tempfile
    import precedent_vendor_engine as pve
    import precedent_session_practices as psp_mod
    cases = [('a practice set\'s engine carries precedent_materialize.py and '
              'precedent_source_pins.py',
              {'precedent_materialize.py', 'precedent_source_pins.py'}
              <= set(pve.ENGINE_FILES), '')]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-set-hooks-'))
    try:
        s = tmp / 'zz-set'
        (s / 'practices').mkdir(parents=True)
        (s / 'tools').mkdir()
        (s / '.claude').mkdir()
        (s / '.claude' / 'settings.json').write_text('{"hooks": {}}', encoding='utf-8')
        (s / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'source', 'files': []}), encoding='utf-8')
        (s / 'tools' / 'zz_hook.py').write_text('print("hi")\n', encoding='utf-8')
        (s / 'precedent-source.json').write_text(
            json.dumps({'name': 'zz-set', 'level': 'shared'}), encoding='utf-8')
        (s / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'base_branch': 'main', 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}),
            encoding='utf-8')
        (s / 'practices' / 'zz-hooked.md').write_text(
            '---\nslug: zz-hooked\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
            'index_clause: "x"\nstatus: active\n'
            'ships: ["tools/zz_hook.py"]\n'
            'hooks: [{"event": "SessionStart", "run": "tools/zz_hook.py"}]\n'
            '---\n## Rule\nx\n\n## Story\nx\n', encoding='utf-8')
        for a in (['init', '-q', '-b', 'main'], ['add', '-A'],
                  ['-c', 'user.email=h@example.com', '-c', 'user.name=h',
                   'commit', '-qm', 'fixture']):
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(s), *a],
                           capture_output=True)
        env = dict(os.environ, PRECEDENT_USER_CONFIG=str(tmp / 'none.json'),
                   HOME=str(tmp / 'home'))
        r = subprocess.run([sys.executable, str(ROOT / 'tools' /
                                                'precedent_session_practices.py'),
                            '--repo', str(s), '--quiet'], capture_output=True,
                           text=True, env=env, cwd=str(s))
        hooks_f = s / '.precedent' / 'practice_hooks.json'
        listed = hooks_f.read_text(encoding='utf-8') if hooks_f.is_file() else ''
        cases.append(('the session file in a set registers the set\'s own practice '
                      'hook in .precedent/practice_hooks.json',
                      'tools/zz_hook.py' in listed and '"SessionStart"' in listed,
                      failure_detail(r.stdout + r.stderr, 600) + listed))

        saved = sys.modules.get('precedent_materialize')
        sys.modules['precedent_materialize'] = None      # import now fails
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                psp_mod.deliver_ships(str(s), [])
        finally:
            if saved is None:
                sys.modules.pop('precedent_materialize', None)
            else:
                sys.modules['precedent_materialize'] = saved
        said = err.getvalue()
        cases.append(('an engine without the module gets one plain sentence, not '
                      'a ModuleNotFoundError', 'ModuleNotFoundError' not in said
                      and 'does not carry tools/precedent_materialize.py' in said,
                      said))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a practice set\'s own hooks are registered in a session rooted in '
          f'it ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:600]}' for n, d in bad))


def check_installer_produces_a_clean_install():
    """tools/precedent_install.py, run against a scratch project as SETUP.md
    now runs it, yields a repo whose own gates come back clean -- and
    refuses to run twice.

    WHY (practice: cite-the-incident). The 2026-09-14 very deep check
    rehearsed INSTALL.md section 0 as written, four times over, and every
    roadblock was a document describing file operations that had drifted
    from the operations: a template's dead links, a workflow name no install
    creates, a check firing on a file the adopter never wrote. The installer
    performs the operations; this fixture is what keeps its output honest,
    by running the same checks a real adopter's first session would.

    The fixture owns its environment (practice: fixture-owns-its-state): no
    individual source, no hosted-session self-heal, no leak blocklist, and
    the global commit backstop waved for the fixture's own commit."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-installer-'))
    cases = []
    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
               PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
    for k in ('CLAUDE_CODE_REMOTE', 'PRECEDENT_LEAK_BLOCKLIST'):
        env.pop(k, None)

    def run(args, cwd):
        return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, env=env)

    def git(cwd, *args):
        r = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True,
                           text=True, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout

    try:
        proj = tmp / 'proj'
        proj.mkdir()
        git(proj.parent, 'init', '-q', '-b', 'main', str(proj))
        git(proj, 'config', 'user.email', 'harness@example.com')
        git(proj, 'config', 'user.name', 'Fixture')
        (proj / 'README.md').write_text('# Field Notes\n\nA newsletter about birds.\n',
                                        encoding='utf-8')
        git(proj, 'add', '-A')
        git(proj, 'commit', '-qm', 'the project before Precedent')

        tool = str(ROOT / 'tools' / 'precedent_install.py')
        r = run([sys.executable, tool, str(proj), '--project-name', 'Field Notes',
                 '--admin', 'dana'], ROOT)
        out = r.stdout + r.stderr
        cases.append(('the installer exits 0 on a fresh project', r.returncode == 0, failure_detail(out, 1500)))
        _who = subprocess.run(['git', '-C', str(proj), 'config', '--local', '--get',
                               'precedent.githubLogin'], capture_output=True, text=True)
        cases.append(("--admin is kept in the clone's git config as who \"you\" are, so "
                      'the code-owner practices reach the administrator with no '
                      'individual set (2026-10-17)',
                      _who.stdout.strip() == 'dana' and '@dana, kept in this clone' in out,
                      _who.stdout + failure_detail(out, 400)))
        cases.append(('it says the light check on the files it wrote passed',
                      'the light check on the written files: OK' in out, failure_detail(out, 800)))
        cases.append(('it names the placeholders it left rather than pretending there are none',
                      'placeholder(s) to adapt' in out, failure_detail(out, 800)))
        pj = proj / 'precedent.json'
        doc = json.loads(pj.read_text(encoding='utf-8')) if pj.is_file() else {}
        # No origin, so nothing can say whether it is private: public, the
        # safe direction, and the output says why (2026-10-17; until then
        # an absent --visibility silently meant private).
        cases.append(('precedent.json declares the base branch and the visibility explicitly, '
                      'and the output says why that visibility',
                      doc.get('base_branch') == 'main' and doc.get('visibility') == 'public'
                      and 'visibility: public (it has no origin yet' in out,
                      str(doc)[:300]))
        _map = (proj / 'MAP.md').read_text(encoding='utf-8') if (proj / 'MAP.md').is_file() else ''
        _src = (proj / 'MAP.source.md').read_text(encoding='utf-8') if (proj / 'MAP.source.md').is_file() else ''
        _gf = proj / 'tools' / 'generated_files.json'
        cases.append(('MAP.md and GLOSSARY.md start out generated, from source files '
                      'the install writes, and are on the project\'s own list '
                      '(spec/GENERATED_FILES_PLAN.md step 5)',
                      _src and _map.startswith('---\ngenerated_by: tools/build_views.py')
                      and _src.rstrip('\n') in _map
                      and (proj / 'GLOSSARY.source.md').is_file()
                      and _gf.is_file() and 'MAP.source.md' in _gf.read_text(encoding='utf-8'),
                      _map[:300]))
        agents = (proj / 'AGENTS.md').read_text(encoding='utf-8') if (proj / 'AGENTS.md').is_file() else ''
        cases.append(('AGENTS.md carries the generated loader block with the resident set in it',
                      bv.BEGIN_MARKER in agents and 'verify-postcondition' in agents, agents[:300]))
        gs = (proj / 'GETTING_STARTED.md').read_text(encoding='utf-8') if (proj / 'GETTING_STARTED.md').is_file() else ''
        # Outside comments: a comment that NAMES the placeholder keeps its
        # words since 2026-10-17 (precedent_install._substitute).
        cases.append(('GETTING_STARTED.md has the project name and the administrator filled in, '
                      'and no dead upstream-docs placeholder',
                      'Field Notes' in gs and '@dana' in gs
                      and '<upstream-docs>' not in re.sub(r'<!--.*?-->', '', gs, flags=re.S),
                      gs[:400]))
        # No individual source resolves here (PRECEDENT_USER_CONFIG points at
        # a file that does not exist), so ci_preference() has nothing to read
        # and the engine's own default applies (practice:
        # declared-default-is-applied) -- ENABLED since 2026-09-25, because
        # what it installs is now one light check on pull requests into main,
        # and a leak gate that never runs in a private repo
        # (spec/BRANCH_TIERS_PLAN.md). Since 2026-09-27 the light check also
        # triggers on a push to main, and its job skips that push unless the
        # repository is public -- so the push trigger must be scoped to main
        # and the job must carry that condition.
        _wfs = proj / '.github' / 'workflows'
        _lc = (_wfs / 'light-check.yml').read_text(encoding='utf-8') \
            if (_wfs / 'light-check.yml').exists() else ''
        _lg = (_wfs / 'leak-gate.yml').read_text(encoding='utf-8') \
            if (_wfs / 'leak-gate.yml').exists() else ''
        _lc_push = re.search(r'^  push:\n((?:    .*\n|\s*#.*\n)*)', _lc, re.M)
        cases.append(('nothing declares github_ci_workflows, so the installer writes the '
                      'light check -- pull requests into main, and pushes to main in a '
                      'public repo only -- and the leak gate, skipped in a private repo, '
                      'and GETTING_STARTED.md says so',
                      'branches: [main]' in _lc
                      and bool(_lc_push) and 'branches: [main]' in _lc_push.group(1)
                      and "github.event_name != 'push' || "
                          "github.event.repository.private != true" in _lc
                      and 'github.event.repository.private != true' in _lg
                      and 'Before anything reaches `main`' in gs,
                      gs[:600]))
        settings = proj / '.claude' / 'settings.json'
        stext = settings.read_text(encoding='utf-8') if settings.is_file() else ''
        cases.append(('the adapter is wired with no classic-layout allowlist entry, and every '
                      'hook it names is on disk',
                      bool(stext) and 'process/upstream' not in stext
                      and all((proj / '.claude' / 'hooks' / n).is_file() for n in
                              ('session-start.sh', 'freshness-guard.sh', 'commit-identity.sh',
                               'reply-gate.sh', 'precedent-paths.sh', 'stop-git-check.sh',
                               'stop-reply-check.sh')),
                      stext[:200]))

        git(proj, 'add', '-A')
        git(proj, 'commit', '-qm', 'Install Precedent')
        r = run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.', '--check'], proj)
        cases.append(('the committed tree is byte-identical to a fresh sync',
                      r.returncode == 0 and 'byte-identical' in r.stdout, r.stdout + r.stderr))
        r = run([sys.executable, 'tools/precedent_check.py'], proj)
        cases.append(("the project's own enforced checks come back 0 violated on the install",
                      r.returncode == 0 and ' 0 violated' in r.stdout,
                      '\n'.join(l for l in r.stdout.splitlines() if l.startswith(('VIOLATION', 'precedent_check:')))))

        r = run([sys.executable, tool, str(proj), '--project-name', 'Field Notes'], ROOT)
        cases.append(('a second run without --force is refused, naming the update path',
                      r.returncode == 1 and 'ENGINE_MANIFEST.json exists' in r.stderr
                      and 'INSTALL.md' in r.stderr, r.stderr[:300]))
        bare = tmp / 'not-a-repo'
        bare.mkdir()
        r = run([sys.executable, tool, str(bare), '--project-name', 'X'], ROOT)
        cases.append(('a directory that is not a git repository is refused with its own message',
                      r.returncode == 1 and 'not the root of a git repository' in r.stderr,
                      r.stderr[:300]))

        # The other direction (practice: control-asserts-which-failure -- a
        # default that can only say yes is not proven by the yes-case alone).
        # Since the default became enabled (2026-09-25), the direction to
        # prove is a DECLARED "disabled": nothing installed, and
        # GETTING_STARTED.md says so instead.
        indiv = tmp / 'indiv-ci-on'
        indiv.mkdir()
        (indiv / 'practices').mkdir()
        (indiv / 'practices' / 'fixture-only.md').write_text(
            '---\n'
            'slug:        fixture-only\n'
            'title:       "Fixture only"\n'
            'tier:        on-demand\n'
            'severity:    default\n'
            'applies_to:  []\n'
            'occasion:    "never -- this source exists only to give this fixture a '
            'non-empty practices/ directory"\n'
            'gates:       []\n'
            'index_clause: "fixture only, never routed for real"\n'
            'checked_by:  null\n'
            'defines:     []\n'
            'status:      active\n'
            'in_force_at: null\n'
            'supersedes:  []\n'
            'overrides:   null\n'
            'added:       null\n'
            'approved_by: "fixture"\n'
            '---\n'
            '## Rule\n'
            'Fixture only; never loaded for real.\n',
            encoding='utf-8')
        (indiv / 'identity.json').write_text(json.dumps({
            'format_version': 1, 'name': 'Dana', 'email': 'dana@example.com',
            'github_ci_workflows': 'disabled',
        }), encoding='utf-8')
        user_cfg = tmp / 'user-config-ci-on.json'
        user_cfg.write_text(json.dumps({'individual': {'path': str(indiv)}}), encoding='utf-8')
        proj2 = tmp / 'proj2'
        proj2.mkdir()
        git(proj2.parent, 'init', '-q', '-b', 'main', str(proj2))
        git(proj2, 'config', 'user.email', 'harness@example.com')
        git(proj2, 'config', 'user.name', 'Fixture')
        (proj2 / 'README.md').write_text('# Second Notes\n', encoding='utf-8')
        git(proj2, 'add', '-A')
        git(proj2, 'commit', '-qm', 'the second project before Precedent')
        env2 = dict(env, PRECEDENT_USER_CONFIG=str(user_cfg))
        r = subprocess.run([sys.executable, tool, str(proj2), '--project-name', 'Second Notes',
                            '--admin', 'dana'], cwd=str(ROOT), capture_output=True, text=True, env=env2)
        # leak-gate.yml, not bestpractice-docs.yml: the Markdown workflow was
        # retired 2026-09-21 and the leak gate is what a consumer now gets.
        wf2 = proj2 / '.github' / 'workflows' / 'leak-gate.yml'
        gs2 = (proj2 / 'GETTING_STARTED.md').read_text(encoding='utf-8') if (proj2 / 'GETTING_STARTED.md').is_file() else ''
        cases.append(('a declared github_ci_workflows: disabled installs no workflow, '
                      'and GETTING_STARTED.md carries the "off" paragraph',
                      r.returncode == 0 and not wf2.exists()
                      and not (proj2 / '.github' / 'workflows' / 'light-check.yml').exists()
                      and 'No GitHub Actions workflow was installed' in gs2,
                      failure_detail(r.stdout + r.stderr, 500)))
        # AND the Markdown lint is NOT a GitHub check any more -- the
        # direction that would otherwise go untested, since every assertion
        # above is about a file being present.
        cases.append(('...and no Markdown workflow is installed at all, on either path',
                      not (proj2 / '.github' / 'workflows' / 'bestpractice-docs.yml').exists()
                      and not (proj / '.github' / 'workflows' / 'bestpractice-docs.yml').exists(),
                      'bestpractice-docs.yml was retired 2026-09-21'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    check(f'tools/precedent_install.py yields a project whose own gates come back clean '
          f'({len(cases)} stated cases)', not failed,
          '; '.join(f'{n}: {d}' for n, _ok, d in failed))


def check_update_leaves_no_dead_manifest_entry():
    """Update Vendors never says DONE over a manifest entry naming a missing
    file, whichever step deleted it (2026-10-01, from a consumer's Update
    Vendors: the catalogue sweep removed a tree, its doc-lint entry stayed,
    and practice_audit.py failed after DONE). Asked of the result, so a
    deleting step written later is covered too.

    Stated cases: an entry inside the mirrored tree, and one for a file
    this update deleted, go with their files; one for the repo's own file,
    missing for no reason this update knows, is left for the person; a
    declined entry and one whose file exists are untouched."""
    import contextlib, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dead-manifest-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        (repo / 'process').mkdir(parents=True)
        (repo / 'docs').mkdir()
        (repo / 'docs' / 'here.md').write_text('x\n', encoding='utf-8')
        (repo / 'docs' / 'removed.md').write_text('x\n', encoding='utf-8')
        (repo / 'process' / 'upstream' / 'practices').mkdir(parents=True)
        (repo / 'process' / 'upstream' / 'practices' / 'p.md').write_text('x\n',
                                                                        encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}]}),
            encoding='utf-8')
        entries = [
            {'name': 'upstream:doc-lint', 'local_path': 'process/upstream/tools/doc_lint.py'},
            {'name': 'removed', 'local_path': 'docs/removed.md'},
            {'name': 'own', 'local_path': 'docs/never-there.md'},
            {'name': 'declined', 'local_path': 'docs/declined.md', 'status': 'declined',
             'notes': 'not for us'},
            {'name': 'here', 'local_path': 'docs/here.md'}]
        (repo / 'process' / 'manifest.json').write_text(
            json.dumps({'entries': entries}), encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        for a in (['init', '-q'], ['add', '-A'], ['commit', '-qm', 'base'],
                  ['rm', '-q', 'docs/removed.md']):
            subprocess.run(['git', '-C', str(repo), *a], capture_output=True, env=env)
        cases.append(('the shared question sees the three dead entries, not the '
                      'declined one',
                      sorted(n for _m, n, _r in pve.dead_manifest_entries(repo))
                      == ['own', 'removed', 'upstream:doc-lint'],
                      str(pve.dead_manifest_entries(repo))))
        rep = pu.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            pu.manifest_postcondition(repo, rep)
        left = [e['name'] for e in json.loads((repo / 'process' / 'manifest.json')
                                              .read_text(encoding='utf-8'))['entries']]
        cases.append(('entries in the mirror, and for a file this update deleted, '
                      'go with their files', left == ['own', 'declined', 'here'],
                      str(left)))
        cases.append(('...said in one step line', any(n == 'manifest' for n, _o in rep.steps),
                      str(rep.steps)))
        cases.append(('the repo\'s own missing file is left for the person, so '
                      'the run cannot say DONE',
                      [w for w, _y in rep.left] == ['process/manifest.json: own'],
                      str(rep.left)))
        cases.append(('the update runs the postcondition',
                      'manifest_postcondition(' in __import__('inspect').getsource(pu.update),
                      ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors leaves no manifest entry naming a missing file '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_a_reasked_left_out_section_is_not_asked_every_rerun():
    """A section recorded as left out, which a second pass asks about again
    (its first pass ran an engine older than the hand-over), is asked once
    per update, not on every re-run of it (2026-10-17, a document project's
    Update Vendors: the first pass runs the repository's committed engine,
    which an unfinished update has not committed, so every re-run asked the
    same four sections again and the run could not reach DONE until the
    engine was committed mid-update). The record is per source commit, in
    the git directory: another update asks again."""
    import contextlib, io, tempfile
    import precedent_vendor_engine as pve
    name = 'a re-asked left-out section is not asked on every re-run'
    if not hasattr(pve, '_report_agents_md'):
        not_applicable(name, '_report_agents_md is absent')
        return
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='reasked-'))
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)
        (tmp / 'AGENTS.md').write_text('# Notes\n', encoding='utf-8')
        plan = [('## Session setup', 'AGENTS.md.loader.template', 12, 'absent', None)]

        def run(commit):
            saved = list(pve._LEFT_FOR_YOU)
            pve._LEFT_FOR_YOU[:] = []
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    try:
                        pve._report_agents_md(tmp, tmp, plan, reask_absent=True,
                                              commit=commit)
                    except TypeError:
                        pve._report_agents_md(tmp, tmp, plan, reask_absent=True)
                left = list(pve._LEFT_FOR_YOU)
            finally:
                pve._LEFT_FOR_YOU[:] = saved
            return left, buf.getvalue()

        left, out = run('c1')
        cases.append(('the first re-run of an update asks again, as before',
                      any('Session setup' in i for i, _w in left), failure_detail(out, 200)))
        left, out = run('c1')
        cases.append(('the next re-run of the same update does not ask a '
                      'third time, and says why',
                      not left and 'not asked a third time' in out, failure_detail(out, 300)))
        left, out = run('c2')
        cases.append(('an update to another source commit asks again',
                      any('Session setup' in i for i, _w in left), failure_detail(out, 200)))
        tracked = subprocess.run(['git', '-C', str(tmp), 'status', '--porcelain',
                                  '--untracked-files=all'],
                                 capture_output=True, text=True).stdout
        cases.append(('the record lives in the git directory, never in the tree',
                      'reasked' not in tracked, tracked))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_refresh_replaces_a_past_individual_hook_rendering():
    """A copy of the individual-set hook that is a rendering of an older
    version of its template becomes the current stub, in any kind of repo;
    an edited copy is left as it is and reported; and BestPractice's own
    copy is the current stub.

    2026-10-17, very deep check: copies rendered before 2026-10-07, when the
    template became a stub, never became it -- the refresh wrote the file
    only when missing, and only for a consumer -- and BestPractice ran a
    stale 181-line copy of its own from precedent_resolve's self-heal.
    Decision (the session's, under Morgan's delegation of 2026-10-17):
    replace a copy matching any past rendering in the template's git
    history; never overwrite a hand-edited one (repair-cannot-discard-work).
    Planted: a source clone whose template has a long version 1 and a stub
    version 2; a repo with a version-1 rendering; one with that rendering
    plus a line of its own."""
    import contextlib, inspect, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    name = 'refresh replaces a past individual-hook rendering with the stub, never an edited copy'
    state_of = getattr(pve, 'individual_hook_copy_state', None)
    replace = getattr(pve, '_replace_past_individual_hook', None)
    if state_of is None or replace is None:
        check(name, False, 'precedent_vendor_engine has no individual_hook_copy_state / '
              '_replace_past_individual_hook: a stale copy is only ever written when missing')
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-individual-hook-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    cases = []
    try:
        src = tmp / 'source'
        tdir = src / pve.HOOK_SOURCE_DIR
        tdir.mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        t = tdir / pve.INDIVIDUAL_HOOK_TEMPLATE
        v1 = ('#!/bin/bash\n# all the logic, the old way\n'
              'NAME="{{SOURCE_NAME}}"\nURL="{{SOURCE_REPO_URL}}"\n'
              'if [ "{{SOURCE_REPO_URL_SUBSTITUTED}}" != yes ]; then exit 0; fi\n'
              'clone "$HOME/{{SOURCE_NAME}}"\n')
        t.write_text(v1, encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v1')
        v2 = ('#!/bin/bash\n# stub\nexport N="{{SOURCE_NAME}}"\n'
              'exec bash tools/individual-source-bootstrap.sh\n')
        t.write_text(v2, encoding='utf-8')
        git(src, 'add', '-A')
        git(src, 'commit', '-qm', 'v2')
        head = git(src, 'rev-parse', 'HEAD').stdout.strip()
        old = (v1.replace('{{SOURCE_NAME}}', 'precedent-individual')
                 .replace('{{SOURCE_REPO_URL}}', 'https://example.com/someone/set')
                 .replace('{{SOURCE_REPO_URL_SUBSTITUTED}}', 'yes'))

        def repo_with(text):
            r = tmp / f'repo-{len(cases)}'
            (r / pve.HOOK_DEST_DIR).mkdir(parents=True)
            (r / pve.HOOK_DEST_DIR / pve.INDIVIDUAL_HOOK).write_text(text, encoding='utf-8')
            return r, r / pve.HOOK_DEST_DIR / pve.INDIVIDUAL_HOOK

        r, f = repo_with(old)
        cases.append(('a version-1 rendering reads as a past rendering',
                      state_of(r, src, head)[0] == 'past', str(state_of(r, src, head)[0])))
        saved = list(pve._LEFT_FOR_YOU)
        with contextlib.redirect_stdout(io.StringIO()):
            wrote = replace(r, src, head)
        cases.append(('...and becomes the current stub, rendered',
                      wrote and f.read_text(encoding='utf-8')
                      == pve.render_individual_hook(v2), f.read_text(encoding='utf-8')[:200]))
        r, f = repo_with(old + 'echo "a line of our own"\n')
        pve._LEFT_FOR_YOU[:] = []
        with contextlib.redirect_stdout(io.StringIO()):
            wrote = replace(r, src, head)
        left = list(pve._LEFT_FOR_YOU)
        pve._LEFT_FOR_YOU[:] = saved
        cases.append(('an edited copy is never written, and is left for you',
                      not wrote and 'a line of our own' in f.read_text(encoding='utf-8')
                      and any(i.endswith(pve.INDIVIDUAL_HOOK) for i, _w in left),
                      str(left)))
        cases.append(('the refresh runs it, on its early exit too',
                      inspect.getsource(pve.refresh).count('_replace_past_individual_hook(') >= 2
                      and 'individual_hook_copy_state(' in inspect.getsource(pve.refresh), ''))
        own = ROOT / pve.HOOK_DEST_DIR / pve.INDIVIDUAL_HOOK
        tmpl_text = (ROOT / pve.HOOK_SOURCE_DIR / pve.INDIVIDUAL_HOOK_TEMPLATE).read_text(
            encoding='utf-8')
        cases.append(('BestPractice\'s own copy is the current stub',
                      own.is_file() and own.read_text(encoding='utf-8')
                      == pve.render_individual_hook(tmpl_text), str(own)))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_refresh_names_an_in_place_hook_no_engine_path_keeps():
    """A hook a repo wires from a path of its own is "nothing to do" only
    when precedent.json's engine_paths declares that path; one it does not
    declare is named once, with the fix.

    2026-10-17, very deep check: an individual set wires
    bootstrap/precedent-universal-catalogue.sh, a copy from 2026-09-20 that
    no engine_paths entry keeps current, and every refresh said there was
    NOTHING TO DO about it, so it stayed stale for good. Decision (the
    session's, under Morgan's delegation of 2026-10-17): say so once, with
    both fixes. Planted: two shipped hooks wired from bootstrap/, one of
    them declared in engine_paths."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-in-place-hook-'))
    cases = []
    try:
        src = tmp / 'hooks'
        src.mkdir()
        for n in ('kept-current.sh', 'left-stale.sh'):
            (src / n).write_text('#!/bin/bash\n', encoding='utf-8')
        repo = tmp / 'set'
        (repo / '.claude').mkdir(parents=True)
        (repo / 'tools').mkdir()
        (repo / 'tools' / pve.MANIFEST_NAME).write_text('{}\n', encoding='utf-8')
        (repo / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
            'SessionStart': [{'hooks': [
                {'type': 'command',
                 'command': '$CLAUDE_PROJECT_DIR/bootstrap/kept-current.sh'},
                {'type': 'command',
                 'command': '"$CLAUDE_PROJECT_DIR"/bootstrap/left-stale.sh'}]}]}}),
            encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({pve.ENGINE_PATHS_KEY: {
            f'{pve.HOOK_SOURCE_DIR}/kept-current.sh': 'bootstrap/kept-current.sh'}}),
            encoding='utf-8')
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            pve._write_hook_files(repo, src, previous={})
        out = err.getvalue()
        nothing = [l for l in out.splitlines() if 'NOTHING TO DO' in l]
        stale = [l for l in out.splitlines() if 'left-stale.sh' in l
                 and pve.ENGINE_PATHS_KEY in l]
        cases.append(('the declared in-place copy is still "nothing to do"',
                      any('kept-current.sh' in l for l in nothing), out[:600]))
        cases.append(('the undeclared one is never called "nothing to do"',
                      not any('left-stale.sh' in l for l in nothing), out[:600]))
        cases.append(('...and is named with both fixes: declare it, or wire .claude/hooks/',
                      stale and 'bootstrap/left-stale.sh' in stale[0]
                      and f'{pve.HOOK_DEST_DIR}/left-stale.sh' in stale[0], out[:600]))
        # The engine keeps "NOTE:" for what a person must judge, so the
        # ladder set's upstream review lists only those
        # (gotcha-2026-10-29-a-note-line-that-reports-a-state-lands-in-the-upstream-review).
        # "Nothing to do" is a state; the undeclared copy is a thing to judge.
        cases.append(('the "nothing to do" line is not a NOTE: line',
                      nothing and not any('NOTE:' in l for l in nothing), out[:600]))
        cases.append(('...and the undeclared copy, a thing to judge, still is',
                      stale and stale[0].startswith('NOTE:'), out[:600]))
        review = ROOT / 'tools' / 'ladder' / 'upstream_review.py'
        if review.is_file():
            import importlib.util
            spec = importlib.util.spec_from_file_location('_ladder_review', review)
            lr = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lr)
            listed = [l for _, l in lr.extract(out)]
            cases.append(("the ladder set's upstream review lists the undeclared copy "
                          'and not the "nothing to do" line',
                          any('left-stale.sh' in l for l in listed)
                          and not any('NOTHING TO DO' in l for l in listed), listed))
        manifest = json.loads((repo / 'tools' / pve.MANIFEST_NAME).read_text(encoding='utf-8'))
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            pve._write_hook_files(repo, src, previous=manifest)
        cases.append(('said once: a second refresh with the same state is silent',
                      'left-stale.sh' not in err.getvalue(), err.getvalue()[:400]))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'refresh names an in-place hook no engine_paths entry keeps current '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_retired_mentions_skip_what_the_repo_receives():
    """A mention of a file the refresh deleted is this repo's to fix only
    where the repo writes the file: never in the engine's own files or
    hooks, materialized practices, or the vendored catalogue -- neither in
    the refresh's warning nor on Update Vendors' Left for you.

    2026-10-17, very deep check: Update Vendors told a session to edit
    tools/precedent_bootstrap_source.py, precedent_vendor_engine.py and
    very_deep_check.py ("repoint or remove the mention; the full check
    refuses it"), vendored engine files, because retired_mentions() did not
    treat the engine manifest's files as received; and the refresh's own
    warning counted every received file, so every row in a consumer became
    a finding. The decommission audit got this exclusion on 2026-09-28.
    Planted: a consumer whose engine file, engine hook, materialized
    practice, vendored universal practice and own doc all name a deleted
    engine file."""
    import contextlib, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-received-mentions-'))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    gone = 'tools/precedent_retire_path.py'
    cases = []
    try:
        def put(rel, text):
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text, encoding='utf-8')
        line = f'Retire a path with `{gone}`.\n'
        put('docs/HOWTO.md', '# How We Work\n\n' + line)
        put('tools/precedent_vendor_engine.py', '# ' + line)
        put('.claude/hooks/session-start.sh', '# ' + line)
        put('practices/some-rule.md', line)
        put('precedent/universal/practices/other-rule.md', line)
        put('tools/' + pve.MANIFEST_NAME, json.dumps(
            {'files': ['precedent_vendor_engine.py'], 'hook_files': ['session-start.sh']}))
        put('MANIFEST.json', json.dumps({
            'generated_by': 'tools/precedent_materialize.py',
            'practices': [{'slug': 'some-rule'}]}))
        put('precedent.json', json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'}]}))
        subprocess.run(['git', 'init', '-q', str(tmp)], env=env, check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], env=env, check=True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            pve._warn_about_dependents(tmp, [gone], 'dropped from the engine')
        warned = [l for l in err.getvalue().splitlines() if 'still names it' in l]
        cases.append(('the refresh warns about the repo\'s own doc',
                      any('docs/HOWTO.md:3' in l for l in warned), err.getvalue()[:500]))
        cases.append(('...and about nothing it receives (engine file, hook, '
                      'materialized and vendored practices)',
                      len(warned) == 1, '\n'.join(warned)[:800]))
        planted = '\n'.join(
            f"WARN: precedent_vendor_engine: {gone} was dropped from the engine, and "
            f"{p}:1 still names it -- 'x'. Nothing here refuses."
            for p in ('tools/precedent_vendor_engine.py', '.claude/hooks/session-start.sh',
                      'docs/HOWTO.md'))
        got = pu.retired_mentions(tmp, planted)
        cases.append(('Update Vendors leaves only the repo\'s own file for the person, '
                      'never a vendored engine file or hook',
                      [w for w, _g in got] == ['docs/HOWTO.md:3'], str(got)))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'mentions of a deleted file skip what the repo receives '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_second_pass_drops_a_first_pass_unshipped_workflow_call():
    """A workflow the running engine ships is never left for the person as
    one "upstream does not ship", even when an older first pass said so.

    2026-10-17, very deep check: an Update Vendors rerun after a failed run
    puts the earlier run's engine files back to HEAD's, so the refresh's
    first pass is the old engine; it judged precedent-branch-cleanup.yml --
    written by the earlier run's new engine, so uncommitted -- by its own
    older list, and its "upstream does not ship it ... it has uncommitted
    edits" reached Left for you through the hand-over to the second pass.
    Reproduced on a scratch install from 2026-10-01: run, a failing basic
    check, a fixed rerun. Planted: that hand-over, carrying the call about a
    workflow this engine ships and one about a workflow it does not."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-carried-wf-'))
    cases = []
    saved = list(pve._CARRIED_LEFT), list(pve._LEFT_FOR_YOU)
    try:
        shipped = sorted(rel for _t, rel in pve.CI_WORKFLOW_TEMPLATES.get('consumer', ()))
        rel = next(r for r in shipped if 'branch-cleanup' in r) if any(
            'branch-cleanup' in r for r in shipped) else shipped[0]
        other = '.github/workflows/our-own.yml'
        dest = tmp / 'dest'
        (dest / '.github' / 'workflows').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(dest)], capture_output=True)
        (dest / rel).write_text('on: workflow_dispatch\njobs: {}\n', encoding='utf-8')
        (dest / 'precedent.json').write_text('{}\n', encoding='utf-8')
        why = ('upstream does not ship it and nobody approved it, so it goes, but '
               'it was not removed: it has uncommitted edits')
        pve._CARRIED_LEFT[:] = [(rel, why), (other, why)]
        pve._LEFT_FOR_YOU[:] = []
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            pve._remove_unapproved_workflows(dest, {}, 'consumer', None)
        carried = [i for i, _w in pve._CARRIED_LEFT]
        cases.append((f'the first pass\'s call about {rel}, which this engine ships, '
                      f'is dropped', rel not in carried, str(pve._CARRIED_LEFT)))
        cases.append(('...and one about a workflow it does not ship is kept',
                      other in carried, str(pve._CARRIED_LEFT)))
        cases.append(('the shipped workflow is left where it is', (dest / rel).is_file(), ''))
    except (OSError, StopIteration, IndexError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        pve._CARRIED_LEFT[:], pve._LEFT_FOR_YOU[:] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a second pass drops a first pass\'s call that a shipped workflow is '
          f'unshipped ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_noise_template_lines_and_a_secret_never_had():
    """Two lines every consumer's update printed and nobody could act on:
    the citations step listing AGENTS.md lines that are word for word the
    current template, and the refresh naming a legacy secret,
    PERSONAL_PACK_TOKEN, in repositories that never had it.

    2026-10-17, very deep check, both seen on a scratch install from
    2026-10-01 main. Now a cited line that is a line of the AGENTS.md
    template at the commit taken is left out (it is upstream's, and the
    refresh keeps it), and a legacy secret is named only where the
    repository's history ever carried the word. Planted: a citation on a
    template line and one on the repository's own line; a legacy workflow
    that reads one secret, in a repo whose history never named the legacy
    one, and in one whose history did."""
    import tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-noise-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)
    cases = []
    try:
        test = getattr(pu, '_stock_line_test', None)
        repo = tmp / 'consumer'
        repo.mkdir()
        tmpl_line = '  (practice `capture-gate`): did this thread\'s work imply anything'
        (repo / 'AGENTS.md').write_text('# Agents\n' + tmpl_line + '\n'
                                        'Our own note citing `capture-gate` here.\n',
                                        encoding='utf-8')
        data = {'slugs': {'capture-gate': 'Rule reworded'}, 'successors': {},
                'hits': [{'source': 'this repository', 'kind': 'live',
                          'slug': 'capture-gate', 'file': 'AGENTS.md', 'line': n}
                         for n in (2, 3)]}
        if test is None:
            cases.append(('the citations step can tell a template line', False,
                          'precedent_update has no _stock_line_test'))
        else:
            _fix, read = pu.citation_findings(
                data, stock=test(repo, {'AGENTS.md': {tmpl_line.strip()}}))
            cases.append(('a cited line that is the template\'s is left out; the '
                          'repo\'s own is still listed', read == ['AGENTS.md:3'],
                          str(read)))
        sync = '.github/workflows/bestpractice-upstream-sync.yml'
        text = ('name: sync\non:\n  workflow_dispatch:\njobs:\n  s:\n    steps:\n'
                '      - uses: anthropics/claude-code-action@v1\n        with:\n'
                '          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}\n')
        legacy = pve.LEGACY_SECRETS[0]

        def repo_with(name, history):
            r = tmp / name
            (r / '.github' / 'workflows').mkdir(parents=True)
            git(tmp, 'init', '-q', str(r))
            (r / 'README.md').write_text(history, encoding='utf-8')
            git(r, 'add', '-A')
            git(r, 'commit', '-qm', 'one')
            (r / 'README.md').write_text('now\n', encoding='utf-8')
            git(r, 'commit', '-qam', 'two')
            return r
        never = repo_with('never', 'a readme\n')
        got = pve._orphaned_secrets(never, {sync: text})
        cases.append(('a legacy secret the repo never carried is not named',
                      'ANTHROPIC_API_KEY' in got and legacy not in got, str(got)))
        had = repo_with('had', f'set {legacy} for the pack sync\n')
        got = pve._orphaned_secrets(had, {sync: text})
        cases.append(('...and one its history carried still is', legacy in got, str(got)))
    except OSError as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors drops template-line citations and a secret never had '
          f'({len(cases)} stated cases)', not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_freshness_reads_a_section0_catalogues_own_sync():
    """The session-start freshness notice reads a section 0 catalogue (the
    universal practices copied into the repository) by its own
    CATALOGUE_SYNC.json, as vendored at that commit, of the repository and
    branch the engine comes from. 2026-10-04, a consumer: 159 practices at
    precedent/universal/ were reported at every session start as "declared,
    but neither a vendored manifest nor a git clone is there -- its
    practices are absent this session". CONTROL: with no sync record, the
    same tree is still reported absent."""
    import shutil, tempfile
    import precedent_engine_freshness as pef
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-fresh-s0-'))
    saved = os.environ.get(pef.USER_CONFIG_ENV)
    os.environ[pef.USER_CONFIG_ENV] = str(tmp / 'no-user-config.json')
    cases = []
    try:
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'source_repo': 'https://github.com/o/Precedent', 'source_branch': 'main',
            'source_commit': 'a' * 40}), encoding='utf-8')
        (tmp / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'precedent/universal'}]}),
            encoding='utf-8')
        cat = tmp / 'precedent' / 'universal'
        (cat / 'practices').mkdir(parents=True)
        (cat / 'practices' / 'x.md').write_text('x\n', encoding='utf-8')
        rows = pef.collect_targets(tmp)
        cases.append(('CONTROL: with no sync record the catalogue reads absent',
                      any(r.get('kind') == 'absent' for r in rows), rows))
        (cat / 'CATALOGUE_SYNC.json').write_text(json.dumps({'source_commit': 'b' * 40}),
                                                 encoding='utf-8')
        rows = pef.collect_targets(tmp)
        vend = [r for r in rows if r.get('kind') == 'vendored']
        cases.append(('with its sync record it reads vendored at that commit, of the '
                      'engine\'s repository and branch, and never absent',
                      not any(r.get('kind') == 'absent' for r in rows) and len(vend) == 1
                      and vend[0].get('recorded') == 'b' * 40
                      and vend[0].get('url') == 'https://github.com/o/Precedent'
                      and vend[0].get('branch') == 'main', rows))
    finally:
        if saved is None:
            os.environ.pop(pef.USER_CONFIG_ENV, None)
        else:
            os.environ[pef.USER_CONFIG_ENV] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_update_vendors_onegplanning_findings():
    """Six upstream defects a consumer's Update Vendors hit on 2026-10-04,
    each planted here.

    1. gotchas/ was linked and never created; the update now starts it with
       the trap every install inherits, and names an inline copy left behind.
    2. A refreshed generator's output was left stale (todo/TODO.md): the
       update rebuilds what its staged inputs make due, and the check that
       would have said so runs at the basic tier.
    3. A placeholder filled without its backticks read as divergence.
    4. Repointing settings.json duplicated allow rules.
    5. Citations of live, merely reworded slugs in code, and any citation in
       an engine-owned file, were sent to the consumer to read.
    6. The start-up pip install threw its error away."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_vendor_engine as pve
        import precedent_push_check as ppc
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-oneg-findings-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True)
    try:
        r = tmp / 'r'
        subprocess.run(['git', 'init', '-q', str(r)], env=env, check=True)
        (r / 'AGENTS.md').write_text(
            '# A\n\n- **A session\'s checkout can be stale enough to look '
            'complete while missing real, merged work.**\n', encoding='utf-8')
        rep = pu.Report()
        seed = getattr(pu, 'gotchas_seed_step', None)
        if seed:
            seed(r, rep, 'HEAD')
        seeded = r / 'gotchas' / 'gotcha-2026-09-01-a-stale-checkout-looks-complete-with-no-error.md'
        cases.append(('1. a consumer with no gotchas/ gets the seed trap',
                      seeded.is_file() and '## Symptom' in seeded.read_text()))
        cases.append(('1. ...and is told to remove the inline copy',
                      any(w == 'AGENTS.md' and 'inline' in why for w, why in rep.left)))

        (r / 'tools').mkdir()
        (r / 'tools' / 'gen.py').write_text(
            'import pathlib, sys\n'
            'out = "generated v2\\n"\n'
            'if "--check" in sys.argv:\n'
            '    sys.exit(0 if pathlib.Path("OUT.md").read_text() == out else 1)\n'
            'pathlib.Path("OUT.md").write_text(out)\n', encoding='utf-8')
        (r / 'OUT.md').write_text('generated v1\n', encoding='utf-8')
        (r / 'tools' / 'generated_files.json').write_text(json.dumps({'files': [
            {'path': 'OUT.md', 'regenerate': 'python3 tools/gen.py',
             'check': ['tools/gen.py', '--check'], 'edit_instead': 'tools/gen.py'}]}))
        git(r, 'add', '-A')
        git(r, 'commit', '-qm', 'base')
        (r / 'tools' / 'gen.py').write_text(
            (r / 'tools' / 'gen.py').read_text() + '# refreshed\n', encoding='utf-8')
        git(r, 'add', 'tools/gen.py')
        rep = pu.Report()
        step = getattr(pu, 'regenerated_step', None)
        got = step(r, rep) if step else None
        cases.append(('2. a refreshed generator rebuilds and stages its output',
                      got == ['OUT.md']
                      and git(r, 'show', ':OUT.md').stdout == 'generated v2\n'))
        kinds_ok = all(any(e[0] == 'generated_files' for e in ppc.PUSH_CHECKS[k])
                       for k in ('source', 'consumer'))
        cases.append(('2. ...and the generated-files check runs at the basic tier',
                      'generated_files' in ppc.BASIC_CHECKS and kinds_ok))

        tmpl = ('## X\n\n- **Deep check** -- the full suite, and `<your own audits>`. '
                'Gates a push and a merge.\n')
        local = ('## X\n\n- **Deep check** -- the full suite, and python3 '
                 'tools/oneg_audit.py. Gates a push and a merge.\n')
        cases.append(('3. a placeholder filled without its backticks is carried',
                      pve.missing_markdown_blocks(local, tmpl) == []))
        cases.append(('3. ...and a sentence really dropped is still reported',
                      pve.missing_markdown_blocks('## X\n\nnothing here at all\n', tmpl) != []))
        # 2026-10-13, a consumer's Update Vendors: a repo with no audits of
        # its own drops the placeholder and the words joining it on.
        plus = ('## X\n\n- **Deep check** -- `push_check.py`, run bare, plus '
                '`<your own audits>`. It is what the push hook runs.\n')
        cases.append(('3. a placeholder dropped with its ", plus" is carried',
                      pve.missing_markdown_blocks(
                          '## X\n\n- **Deep check** -- `push_check.py`, run bare. '
                          'It is what the push hook runs.\n', plus) == []))
        cases.append(('3. ...and with its ", and"',
                      pve.missing_markdown_blocks(
                          '## X\n\n- **Deep check** -- the full suite. '
                          'Gates a push and a merge.\n', tmpl) == []))
        cases.append(('3. ...but rewording the words around it is still reported',
                      pve.missing_markdown_blocks(
                          '## X\n\n- **Deep check** -- `push_check.py`, run bare, then '
                          'nothing. It is what the push hook runs.\n', plus) != []))

        dedupe = getattr(pu, '_without_duplicate_permissions', None)
        doubled = json.dumps({'permissions': {'allow': [
            'Bash(python3 tools/doc_lint.py)', 'Bash(git status)',
            'Bash(python3 tools/doc_lint.py)']}}, indent=2)
        once = json.loads(dedupe(doubled)) if dedupe else {}
        cases.append(('4. a repointed allow list keeps one copy of each rule, in order',
                      once.get('permissions', {}).get('allow') ==
                      ['Bash(python3 tools/doc_lint.py)', 'Bash(git status)']))

        find = getattr(pu, 'citation_findings', None)
        data = {'slugs': {'upstream-fix': 'Rule reworded', 'gone': 'withdrawn'},
                'successors': {},
                'hits': [
                    {'source': 'this repository', 'kind': 'live', 'slug': 'upstream-fix',
                     'file': 'tools/bootstrap.sh', 'line': 389},
                    {'source': 'this repository', 'kind': 'live', 'slug': 'upstream-fix',
                     'file': '.claude/hooks/freshness-guard.sh', 'line': 13},
                    {'source': 'this repository', 'kind': 'live', 'slug': 'upstream-fix',
                     'file': 'docs/notes.md', 'line': 4},
                    {'source': 'this repository', 'kind': 'live', 'slug': 'gone',
                     'file': '.claude/hooks/freshness-guard.sh', 'line': 9,
                     'must_fix': True}]}
        fix, read = find(data, {'.claude/hooks/freshness-guard.sh'}) if find else (None, None)
        cases.append(('5. a reworded live slug is a read only in a document, and '
                      'nothing in an engine-owned file is reported',
                      fix == [] and read == ['docs/notes.md:4']))

        for rel in ('templates/bootstrap.sh', 'tools/bootstrap.sh'):
            boot = (ROOT / rel).read_text(encoding='utf-8')
            cases.append((f'6. {rel} keeps pip\'s error and checks the import after',
                          'pip install --quiet cmarkgfm markdown 2>"$_pip_log"' in boot
                          and 'pip install --quiet cmarkgfm markdown 2>/dev/null' not in boot
                          and "python3 -c 'import cmarkgfm, markdown'" in boot))
    except (OSError, subprocess.CalledProcessError, TypeError, ValueError,
            AttributeError, KeyError) as e:
        cases.append((f'fixture could not be built ({type(e).__name__}: {e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_materialize_run_directly_refuses_what_the_sync_withholds():
    """precedent_materialize.py RUN DIRECTLY refuses the two writes only its
    wrapper, precedent_sync_views.py, used to prevent (2026-10-17 very deep
    check, finding "running precedent_materialize.py directly in a public
    consumer copies private practice text into its tracked tree").

    Reproduced before the fix: a scratch consumer declaring `visibility:
    public` with an individual source got that set's practice under its
    tracked practices/, and MANIFEST.json recorded `withheld: []` beside the
    individual source's name and absolute path; with a declared source
    unreachable it printed "Materializing WITHOUT it" and wrote anyway.

    Stated cases: a public consumer with an individual source refuses, names
    the wrapper, and writes nothing; a declared source that is missing
    refuses and writes nothing; --allow-missing-sources proceeds; a private
    consumer with the same individual source materializes it (the control);
    and the wrapper itself still syncs the public consumer, withholding."""
    import tempfile, shutil
    import json as _json
    tool = str(ROOT / 'tools' / 'precedent_materialize.py')
    cases = []

    def practice(d, slug, canary):
        (d / 'practices').mkdir(parents=True, exist_ok=True)
        (d / 'practices' / f'{slug}.md').write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x happens"\n'
            f'index_clause: "do the thing"\nstatus: active\n---\n'
            f'## Rule\n{canary} applies.\n\n## Story\nBecause.\n',
            encoding='utf-8')

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        uni, ind = tmp / 'uni', tmp / 'ind'
        practice(uni, 'uni-rule', 'UNIVERSAL-TEXT')
        practice(ind, 'private-only', 'SECRET-CANARY-VALUE')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(_json.dumps({'format_version': 1, 'individual': {
            'name': 'precedent-individual', 'path': str(ind)}}), encoding='utf-8')
        empty_cfg = tmp / 'empty-user.json'
        empty_cfg.write_text(_json.dumps({'format_version': 1}), encoding='utf-8')

        def consumer(name, visibility, extra_sources=()):
            repo = tmp / name
            repo.mkdir()
            (repo / 'precedent.json').write_text(_json.dumps({
                'format_version': 1, 'base_branch': 'main',
                'visibility': visibility,
                'sources': [{'level': 'universal', 'name': 'precedent',
                             'path': str(uni)}, *extra_sources]}),
                encoding='utf-8')
            return repo

        def run(repo, cfg, *extra):
            env = dict(os.environ, HOME=str(tmp / 'home'))
            r = subprocess.run([sys.executable, tool, '--out', str(repo),
                                '--repo', str(repo), '--user-config', str(cfg),
                                *extra], capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def tree_text(repo):
            return '\n'.join(f.read_text(encoding='utf-8')
                             for f in repo.rglob('*') if f.is_file())

        pub = consumer('pub', 'public')
        rc, out = run(pub, user_cfg)
        cases.append(('a public consumer with an individual source refuses',
                      rc != 0 and 'refusing' in out, out))
        cases.append(('and names precedent_sync_views.py as the route',
                      'precedent_sync_views.py' in out, out))
        cases.append(('and writes no private text, no practices/ and no '
                      'MANIFEST.json', 'SECRET-CANARY-VALUE' not in tree_text(pub)
                      and not (pub / 'practices').exists()
                      and not (pub / 'MANIFEST.json').exists(), out))

        gone = consumer('gone', 'private', [{'level': 'team', 'name':
                        'precedent-team-gone', 'path': str(tmp / 'nowhere')}])
        rc, out = run(gone, empty_cfg)
        cases.append(('a declared source that did not resolve refuses',
                      rc != 0 and 'incomplete source set' in out
                      and 'precedent-team-gone' in out, out))
        cases.append(('and writes nothing', not (gone / 'practices').exists(), out))
        rc, out = run(gone, empty_cfg, '--allow-missing-sources')
        cases.append(('--allow-missing-sources proceeds past it',
                      rc == 0 and (gone / 'practices' / 'uni-rule.md').is_file(), out))

        # A set carries this module for its session file since 2026-10-17;
        # materializing into one would replace its own catalogue.
        aset = consumer('aset', 'private')
        (aset / 'tools').mkdir()
        (aset / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'source', 'files': []}), encoding='utf-8')
        practice(aset, 'own-rule', 'THE-SETS-OWN-TEXT')
        rc, out = run(aset, empty_cfg)
        cases.append(('a practice set refuses, and keeps its own practices/',
                      rc != 0 and 'practice set' in out
                      and (aset / 'practices' / 'own-rule.md').is_file()
                      and not (aset / 'practices' / 'uni-rule.md').exists(), out))

        priv = consumer('priv', 'private')
        rc, out = run(priv, user_cfg)
        cases.append(('control: a private consumer materializes the same '
                      'individual source', rc == 0 and
                      (priv / 'practices' / 'private-only.md').is_file(), out))

        import precedent_sync_views as psv
        pub2 = consumer('pub2', 'public')
        import build_views as _bv
        (pub2 / 'AGENTS.md').write_text(
            f'# Consumer\n\n{_bv.BEGIN_MARKER} -->\n{_bv.END_MARKER} -->\n',
            encoding='utf-8')
        try:
            psv.sync(str(pub2), user_config=str(user_cfg))
            err = ''
        except Exception as e:  # noqa: BLE001 -- reported as the case's detail
            err = repr(e)
        cases.append(('the wrapper still syncs the public consumer, withholding '
                      'the private text', not err
                      and (pub2 / 'practices' / 'uni-rule.md').is_file()
                      and 'SECRET-CANARY-VALUE' not in tree_text(pub2), err))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'precedent_materialize.py run directly refuses private text in a '
          f'public repo and an incomplete source set, naming the sync '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_a_renamed_engine_file_never_survives_a_reseed():
    """Renaming an engine file upstream must not leave the old one behind
    in an adopter's tree (practice: decommission-deletes-files,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. Upstream renamed `precedent_retire_path.py`
    to `precedent_decommission.py`. Three real practice sets were then
    found each carrying the dead file, and every mechanism reported them
    healthy. Three separate holes lined up:

      1. `refresh` on a stale copy exited hard on the missing old path, so
         the ONLY way forward was a reseed (fixed upstream the same day --
         the skip-and-converge path).
      2. `seed`, the documented recovery, never called
         _remove_dropped_engine_files at all: it wrote the new set and a
         manifest that had already forgotten the old name, leaving the file
         on disk untracked.
      3. `refresh`'s early exit returned on a matching commit before any
         cleanup could run, so no later run would ever remove it -- and its
         `set_incomplete` test looked only for MISSING wanted files, never
         for PRESENT unwanted ones.

    After (2), the file is in no list any mechanism consults: gone from
    KINDS, gone from the manifest. _untracked_engine_files is keyed on the
    current lists and is deliberately blind to it. That is why
    RETIRED_ENGINE_FILES exists -- a name, once shipped, cannot be derived
    back out of the code that stopped shipping it.

    Three cases, one per hole. The reseed case is the one that would have
    caught the incident; the other two are the paths that made it
    permanent.
    """
    import shutil, tempfile
    import json as _json
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'pve', ROOT / 'tools' / 'precedent_vendor_engine.py')
    pve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pve)

    results = []

    # MISSING IS A FAILURE, NOT A CRASH. Every symbol below is one this fix
    # introduced, so an engine that predates it raises AttributeError -- and
    # an uncaught one here takes the whole harness run down instead of
    # reporting one red check, which AGENTS.md records as its own hazard.
    # Reported as the absence it is (practice: fail-gracefully).
    missing_symbols = [n for n in ('RETIRED_ENGINE_FILES',
                                   '_retired_engine_files_present',
                                   '_remove_dropped_engine_files',
                                   '_seed_write')
                       if not hasattr(pve, n)]
    if missing_symbols:
        check('a renamed engine file never survives a reseed, and is '
              'reported when it already has (0 of 8 stated cases reached)',
              False,
              f"precedent_vendor_engine.py is missing "
              f"{', '.join(missing_symbols)} -- the removed-file cleanup is "
              f"not present in this engine at all, so a rename upstream "
              f"leaves the old file in every adopter's tree")
        return

    # The tombstone must not be empty in a way that makes every case below
    # vacuously true.
    results.append(('the engine records at least one retired file name',
                    bool(pve.RETIRED_ENGINE_FILES)))

    with tempfile.TemporaryDirectory() as tmp:
        tools = pathlib.Path(tmp) / 'tools'
        tools.mkdir(parents=True)
        dead = sorted(pve.RETIRED_ENGINE_FILES)[0]

        # CASE 1 -- a tombstoned file the manifest has FORGOTTEN is still
        # reported. This is the state a pre-fix reseed produced, and the one
        # nothing else could see.
        (tools / dead).write_text('# left behind by a rename\n')
        (tools / pve.MANIFEST_NAME).write_text(_json.dumps({
            'format_version': 1, 'kind': 'source', 'source_commit': 'x' * 40,
            'files': [], 'sha256': {}}), encoding='utf-8')
        reported = pve._retired_engine_files_present(tools)
        results.append(('an unrecorded retired file is reported',
                        [n for n, _ in reported] == [dead]))
        # ASSERT WHAT IT SAYS, not merely that it said something: the reason
        # is the whole value of the report, since the reader has no other
        # way to find out what the file was.
        results.append(('the report carries the reason it was retired',
                        bool(reported) and len(reported[0][1]) > 20))
        # It must NOT delete on its own -- see the function's own docstring.
        results.append(('reporting does not delete it',
                        (tools / dead).is_file()))

        # CASE 2 -- a tombstoned file the manifest still RECORDS is removed
        # by the sweep, which can hash-verify it first.
        (tools / pve.MANIFEST_NAME).write_text(_json.dumps({
            'format_version': 1, 'kind': 'source', 'source_commit': 'x' * 40,
            'files': [dead],
            'sha256': {dead: pve._sha256(tools / dead)}}), encoding='utf-8')
        manifest = pve._load_manifest(tools)
        pve._remove_dropped_engine_files(tools, manifest, 'source')
        results.append(('a recorded retired file is removed by the sweep',
                        not (tools / dead).is_file()))

        # CASE 2b -- SEEDING A REPO THAT HAS NO MANIFEST AT ALL still
        # works. This is seed's primary case, and the cleanup added above
        # broke it outright by reading the manifest through a helper that
        # sys.exit()s when there is none. Every fixture here had a manifest
        # already, so nothing caught it until a full harness run did.
        fresh = pathlib.Path(tmp) / 'never-vendored'
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
             'seed', str(fresh), '--kind', 'source'],
            capture_output=True, text=True, cwd=str(ROOT))
        results.append(('seeding a repo with no manifest at all still '
                        'succeeds', r.returncode == 0
                        and (fresh / 'tools' / pve.MANIFEST_NAME).is_file()))

    # CASE 3 -- seed() routes through the cleanup. Asserted structurally:
    # building a whole second checkout to seed from is a fixture bigger than
    # the property, and the property is simply that seed does not bypass it.
    src = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text()
    seed_body = src[src.index('def seed('):]
    seed_body = seed_body[:seed_body.index('\ndef ', 1)]
    results.append(('seed writes through _seed_write, which cleans up, '
                    'rather than calling _write_engine_files directly',
                    '_seed_write(' in seed_body
                    and '_write_engine_files(' not in seed_body))
    results.append(('_seed_write actually calls the cleanup',
                    '_remove_dropped_engine_files' in
                    src[src.index('def _seed_write('):
                        src.index('def seed(')]))
    # And refresh's early exit must consider orphans, not only absences.
    ref = src[src.index('def refresh('):]
    results.append(('refresh\'s early exit checks for orphaned files too',
                    'set_orphaned' in ref))

    failed = [n for n, ok in results if not ok]
    check(f'a renamed engine file never survives a reseed, and is reported '
          f'when it already has ({len(results)} stated cases)',
          not failed, '; '.join(failed))


