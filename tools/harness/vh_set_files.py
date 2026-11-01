# The harness tests for the set-files registry: what a copy of a shared set carries
#
# tools/harness/vh_set_files.py -- part of the verification harness: the
# registry of files the engine reads from a set's own folder
# (tools/precedent_set_files.py), the copier that carries them
# (tools/checkin.py), and the three checks that keep the list true
# (set-file-registered, set-copy-complete, set-file-decided), from
# spec/SET_COPY_CARRIES_WHAT_THE_ENGINE_READS_PLAN.md (2026-11-01).
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace (tools/harness_parts.py).
# Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# No docstring up here: one would replace verify_harness.py's own __doc__.


def _sf_env(tmp):
    """The fixture's own identity and user config, so this machine's sets
    never resolve into it (practice: fixture-owns-its-state)."""
    (tmp / 'no-config.json').write_text('{}', encoding='utf-8')
    return {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
            'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t',
            'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}


def _sf_git(env, d, *a):
    return subprocess.run(['git', '-C', str(d), *a], env=env,
                          capture_output=True, text=True)


def _sf_make_set(tmp, env, name, files, manifest_extra=None):
    """-> (clone, commit): a shared set `name` with a bare origin, holding
    practices/zz-rule.md, its precedent-source.json and `files`
    ({set-relative path: text})."""
    origin = tmp / f'{name}.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)],
                   env=env, check=True)
    clone = tmp / name
    subprocess.run(['git', 'clone', '-q', str(origin), str(clone)], env=env,
                   capture_output=True, check=True)
    _sf_git(env, clone, 'checkout', '-q', '-b', 'main')
    (clone / 'practices').mkdir(parents=True, exist_ok=True)
    (clone / 'practices' / 'zz-rule.md').write_text(
        '---\nslug: zz-rule\n---\n# zz\n\n## Rule\n\nx\n', encoding='utf-8')
    (clone / 'precedent-source.json').write_text(json.dumps(
        {'name': name, 'level': 'shared', 'visibility': 'public',
         **(manifest_extra or {})}), encoding='utf-8')
    for rel, text in files.items():
        (clone / rel).parent.mkdir(parents=True, exist_ok=True)
        (clone / rel).write_text(text, encoding='utf-8')
    _sf_git(env, clone, 'add', '-A')
    _sf_git(env, clone, 'commit', '-qm', 'one')
    _sf_git(env, clone, 'push', '-q', 'origin', 'main')
    return clone, _sf_git(env, clone, 'rev-parse', 'HEAD').stdout.strip()


def _sf_make_host(tmp, env, hname, entries):
    """-> a private consuming repository declaring `entries` (source
    entries), each with an empty copy record."""
    h = tmp / hname
    (h / 'process').mkdir(parents=True)
    (h / 'precedent.json').write_text(json.dumps({
        'format_version': 1, 'visibility': 'private', 'sources': entries}),
        encoding='utf-8')
    for e in entries:
        (h / 'process' / f"manifest_{e['name']}.json").write_text(json.dumps(
            {'upstream': {'branch': 'main'}}), encoding='utf-8')
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(h)], env=env, check=True)
    _sf_git(env, h, 'add', '-A')
    _sf_git(env, h, 'commit', '-qm', 'init')
    return h


def _sf_checkin(env, host, name, verb, clone, *flags):
    return subprocess.run(
        [sys.executable, str(ROOT / 'tools' / 'checkin.py'), '--source', name,
         '--repo', str(host), verb, str(clone), *flags],
        env=env, capture_output=True, text=True)


def _sf_entry(name, **extra):
    return {'name': name, 'level': 'shared', 'path': f'process/{name}',
            'vendored': True, **extra}


def _sf_load_check(root):
    """-> precedent_check loaded fresh, judging `root`."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc_set_files', ROOT / 'tools' / 'precedent_check.py')
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)
    pc.ROOT = pathlib.Path(root)
    return pc


def _sf_run(pc, slug):
    """-> ('findings', [str]) or ('skipped', reason) for one check."""
    try:
        got = pc.CHECKS[slug]['fn'](None)
    except pc.NotApplicable as e:
        return 'skipped', str(e)
    return 'findings', [f'{f.where}: {f.detail}' for f in got]


class _SfRep:
    def __init__(self):
        self.steps, self.left = [], []

    def step(self, name, outcome):
        self.steps.append((name, outcome))

    def leave(self, what, why):
        self.left.append((what, why))


_SF_ALL_FILES = {
    'reply_check.json': json.dumps([{'id': 'zz-says', 'require_any': ['ZZ'],
                                     'why': 'fixture'}]),
    'close_detect.json': json.dumps([{'id': 'zz-close', 'why': 'fixture'}]),
    'our_language.json': json.dumps({'words': [
        {'word': 'Zzword', 'meaning': 'a fixture word'}]}),
    'BUILT_FROM.json': json.dumps({'outputs': {}}),
}


def check_set_file_readers_open_only_registered_files():
    """The readers of a set's own folder open only files the registry lists
    (plan review, 2): the reply check, close detection, the vocabulary list,
    Update Vendors' BUILT_FROM comparison and the materializer's adapter
    plan run against a fixture set under an audit hook (sys.addaudithook),
    which records every file opened under the set's folder. A static scan
    cannot see a name built at run time; this can.

    THE CASE: every file opened is registered, and every one the registry
    ships is in a whole copy of the set. NEGATIVE CONTROL: a planted reader
    that opens an unregistered zz_extra.json is caught, by name. Fails on
    the engine before 2026-11-01: its copy lacks our_language.json and
    BUILT_FROM.json, which the readers open."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-files-audit-'))
    cases = []
    try:
        env = _sf_env(tmp)
        host = _sf_make_host(tmp, env, 'host', [_sf_entry('zz-set')])
        copy = host / 'process' / 'zz-set'
        (copy / 'practices').mkdir(parents=True)
        (copy / 'practices' / 'zz-rule.md').write_text(
            '---\nslug: zz-rule\n---\n# zz\n\n## Rule\n\nx\n', encoding='utf-8')
        (copy / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-set', 'level': 'shared'}), encoding='utf-8')
        for rel, text in _SF_ALL_FILES.items():
            (copy / rel).write_text(text, encoding='utf-8')
        (copy / 'precedent.json').write_text('{}', encoding='utf-8')
        (copy / 'zz_extra.json').write_text('{}', encoding='utf-8')
        probe = (
            'import json, os, pathlib, sys\n'
            'tools, host, set_dir, plant = sys.argv[1:5]\n'
            'sys.path.insert(0, tools)\n'
            'set_dir = pathlib.Path(set_dir).resolve()\n'
            'opened = set()\n'
            'def hook(ev, args):\n'
            '    if ev != "open" or not args:\n'
            '        return\n'
            '    try:\n'
            '        p = pathlib.Path(os.fsdecode(args[0])).resolve()\n'
            '        opened.add(p.relative_to(set_dir).as_posix())\n'
            '    except Exception:\n'
            '        pass\n'
            'sys.addaudithook(hook)\n'
            'import precedent_reply_check as rc, precedent_close_detect as cd\n'
            'import precedent_vocabulary as voc, precedent_update as pu\n'
            'import precedent_materialize as pm, precedent_resolve as pr\n'
            'rc.declared_requirements(host)\n'
            'cd.declared(host)\n'
            'voc.all_words(pathlib.Path(host))\n'
            'pu.built_from_differences(pathlib.Path(host))\n'
            'try:\n'
            '    pm._plan_adapters(pr.load_config(host))\n'
            'except Exception:\n'
            '    pass\n'
            'if plant == "1":\n'
            '    (set_dir / "zz_extra.json").read_text()\n'
            'import precedent_set_files as psf\n'
            'print(json.dumps([sorted(r for r in opened if not psf.registered(r)),\n'
            '                  sorted(opened)]))\n')

        def opened_unregistered(plant):
            r = subprocess.run([sys.executable, '-c', probe, str(ROOT / 'tools'),
                                str(host), str(copy), plant],
                               env=env, cwd=str(host), capture_output=True, text=True)
            try:
                return json.loads(r.stdout.strip().splitlines()[-1]), r
            except (ValueError, IndexError):
                return [None, []], r
        (got, seen), r = opened_unregistered('0')
        want = {'reply_check.json', 'close_detect.json', 'our_language.json',
                'BUILT_FROM.json', 'precedent.json'}
        cases.append(('the readers really ran: each opened its registered file',
                      want <= set(seen), repr(seen) + ' '
                      + failure_detail(r.stdout + r.stderr, 400)))
        cases.append(('THE CASE: the readers open no file the registry does not '
                      'list', got == [],
                      repr(got) + ' ' + failure_detail(r.stdout + r.stderr, 400)))
        (got, _seen), r = opened_unregistered('1')
        cases.append(('NEGATIVE CONTROL: a planted reader of zz_extra.json is '
                      'caught by name', got == ['zz_extra.json'],
                      repr(got) + ' ' + failure_detail(r.stdout + r.stderr, 400)))
        # And the property the registry exists for, end to end: what the
        # readers open in a set is in a whole copy of it -- except what the
        # registry keeps home (precedent.json). On the engine before
        # 2026-11-01 our_language.json and BUILT_FROM.json never arrived.
        files = dict(_SF_ALL_FILES, **{'precedent.json': '{}'})
        clone, _c = _sf_make_set(tmp, env, 'zz-live', files)
        host2 = _sf_make_host(tmp, env, 'host2', [_sf_entry('zz-live')])
        rc2 = _sf_checkin(env, host2, 'zz-live', 'update', clone, '--force')
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_set_files as psf
        stays = {e['name'] for e in psf.SET_FILES if e['copy'] != 'ship'}
        lacking = sorted(rel for rel in want - stays
                         if not (host2 / 'process' / 'zz-live' / rel).is_file())
        cases.append(('THE CASE, end to end: every file the readers open in a set '
                      'is in a whole copy of it', lacking == [],
                      repr(lacking) + ' ' + failure_detail(rc2.stdout + rc2.stderr, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the readers of a set\'s folder open only registered files '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_copy_fills_what_an_older_copy_lacks():
    """THE INCIDENT (2026-11-01). A voice repository's copy of the ladder set
    held reply_check.json and not our_language.json: the copier's hand-kept
    list named two files, and the vocabulary list reads a third from every
    source's folder. Here a copy made the old way (no our_language.json, no
    set_files record) is refreshed:

    1. the copy now carries our_language.json;
    2. its manifest records set_files and the commit, in the copy's write;
    3. Update Vendors' completeness step says, once, that it added the file
       and what the file carries -- and leaves nothing for the person;
    4. a second refresh adds nothing and says nothing new.
    Fails on the engine before this change: step 1 does not happen."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-files-fill-'))
    cases = []
    try:
        env = _sf_env(tmp)
        clone, commit = _sf_make_set(tmp, env, 'zz-set', {
            'reply_check.json': _SF_ALL_FILES['reply_check.json'],
            'our_language.json': _SF_ALL_FILES['our_language.json']})
        host = _sf_make_host(tmp, env, 'host', [_sf_entry('zz-set')])
        copy = host / 'process' / 'zz-set'
        # What an engine from before the registry left: the set's practices,
        # its manifest and reply_check.json, a record with no set_files.
        shutil.copytree(clone / 'practices', copy / 'practices')
        for rel in ('precedent-source.json', 'reply_check.json'):
            shutil.copy2(clone / rel, copy / rel)
        mpath = host / 'process' / 'manifest_zz-set.json'
        mpath.write_text(json.dumps({'upstream': {
            'branch': 'main', 'commit': commit, 'synced_from': commit,
            'vendored_at': 'process/zz-set'}}), encoding='utf-8')
        _sf_git(env, host, 'add', '-A')
        _sf_git(env, host, 'commit', '-qm', 'an older copy')
        import precedent_update as pu
        was = pu._copy_digest(copy)
        r1 = _sf_checkin(env, host, 'zz-set', 'update', clone)
        r2 = _sf_checkin(env, host, 'zz-set', 'record', clone, '--note', 't')
        cases.append(('THE CASE: the refresh fills our_language.json',
                      (copy / 'our_language.json').is_file(),
                      failure_detail(r1.stdout + r1.stderr + r2.stdout + r2.stderr, 400)))
        up = json.loads(mpath.read_text(encoding='utf-8')).get('upstream') or {}
        cases.append(('...and records set_files and the commit it copied',
                      up.get('set_files') == ['precedent-source.json',
                                              'reply_check.json', 'our_language.json']
                      and up.get('set_files_commit') == commit, repr(up)))
        rep = _SfRep()
        pu.set_copy_complete_step(host, rep, _sf_entry('zz-set'), clone, was,
                                  pu._copy_digest(copy))
        added = [o for _n, o in rep.steps if o.startswith('added our_language.json')]
        cases.append(('...and Update Vendors says once that it added it, and why, '
                      'leaving nothing for the person',
                      len(added) == 1 and 'vocabulary' in added[0] and not rep.left,
                      repr(rep.steps) + repr(rep.left)))
        _sf_git(env, host, 'add', '-A')
        _sf_git(env, host, 'commit', '-qm', 'filled')
        was = pu._copy_digest(copy)
        r3 = _sf_checkin(env, host, 'zz-set', 'update', clone)
        rep = _SfRep()
        pu.set_copy_complete_step(host, rep, _sf_entry('zz-set'), clone, was,
                                  pu._copy_digest(copy))
        cases.append(('a second refresh copies nothing and reports nothing new',
                      'nothing to do' in r3.stdout and not rep.steps and not rep.left,
                      failure_detail(r3.stdout + r3.stderr, 300) + repr(rep.steps)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a copy of a set is filled with every registered file it lacked '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_set_copy_complete_advisory_then_finding():
    """set-copy-complete (consumer side): a note while a copy predates the
    registry, a finding once its record exists and a registered file is
    gone, a kept local edit named as kept and never a finding, and a
    could-not-verify when the recorded commit cannot be read.

    1. A copy with no set_files record: SKIPPED, naming what the next
       Update Vendors fills -- never a violation, so a consumer's main does
       not go red the day the engine moves.
    2. After the refresh: no finding.
    3. NEGATIVE CONTROL: our_language.json deleted from the copy: a finding
       naming it and what it carries.
    4. A kept local edit to reply_check.json (kept_template_divergences,
       with a reason): no finding; the skip line says it is kept.
    5. No clone of the set here: presence only, said as could-not-verify.
    Fails on the engine before this change: there is no such check."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-files-complete-'))
    cases = []
    try:
        env = _sf_env(tmp)
        clone, commit = _sf_make_set(tmp, env, 'zz-set', {
            'reply_check.json': _SF_ALL_FILES['reply_check.json'],
            'our_language.json': _SF_ALL_FILES['our_language.json']})
        host = _sf_make_host(tmp, env, 'host', [_sf_entry('zz-set')])
        copy = host / 'process' / 'zz-set'
        shutil.copytree(clone / 'practices', copy / 'practices')
        for rel in ('precedent-source.json', 'reply_check.json'):
            shutil.copy2(clone / rel, copy / rel)
        mpath = host / 'process' / 'manifest_zz-set.json'
        mpath.write_text(json.dumps({'upstream': {
            'branch': 'main', 'commit': commit, 'synced_from': commit,
            'vendored_at': 'process/zz-set'}}), encoding='utf-8')
        _sf_git(env, host, 'add', '-A')
        _sf_git(env, host, 'commit', '-qm', 'an older copy')
        pc = _sf_load_check(host)
        pc._set_clone = lambda e: clone
        kind, got = _sf_run(pc, 'set-copy-complete')
        cases.append(('1. a copy from before the registry is a note naming what '
                      'the next update fills', kind == 'skipped'
                      and 'predates' in got and 'our_language.json' in got, got))
        _sf_checkin(env, host, 'zz-set', 'update', clone)
        _sf_checkin(env, host, 'zz-set', 'record', clone)
        kind, got = _sf_run(pc, 'set-copy-complete')
        cases.append(('2. after the refresh, no finding', kind == 'findings'
                      and got == [], got))
        (copy / 'our_language.json').unlink()
        kind, got = _sf_run(pc, 'set-copy-complete')
        cases.append(('3. NEGATIVE CONTROL: a registered file gone from a '
                      'recorded copy is a finding naming it',
                      kind == 'findings' and len(got) == 1
                      and 'our_language.json is missing' in got[0]
                      and 'vocabulary' in got[0], got))
        shutil.copy2(clone / 'our_language.json', copy / 'our_language.json')
        (copy / 'reply_check.json').write_text('[]', encoding='utf-8')
        cfg = json.loads((host / 'precedent.json').read_text(encoding='utf-8'))
        cfg['kept_template_divergences'] = {
            'process/zz-set/reply_check.json': {'reason': 'fixture: kept on purpose'}}
        (host / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        kind, got = _sf_run(pc, 'set-copy-complete')
        cases.append(('4. a kept local edit is named as kept, never a finding',
                      kind == 'skipped' and 'kept' in got
                      and 'reply_check.json' in got, got))
        cfg.pop('kept_template_divergences')
        (host / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        shutil.copy2(clone / 'reply_check.json', copy / 'reply_check.json')
        pc._set_clone = lambda e: None
        kind, got = _sf_run(pc, 'set-copy-complete')
        cases.append(('5. with no clone of the set here, a could-not-verify',
                      kind == 'skipped' and 'cannot be read here' in got, got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'set-copy-complete is a note before the registry and a finding after '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_set_file_registered_catches_bind_and_join():
    """set-file-registered (BestPractice): the scan finds a read from a
    source's folder however it is spelled, including the shape that hid the
    first bug -- a name bound from a source's path, and the file joined on a
    line of its own (precedent_reply_check.py did exactly this).

    1. THE CASE: `root = pathlib.Path(s['path'])` then `root / 'zz_new.json'`
       is found, by line.
    2. A direct join on X['path'], a constant and a chain are found too.
    3. NEGATIVE CONTROL: a registered name, a `# set-file: ok -- why` line
       and a join on a path that is not a source's are not findings.
    4. This repository's own tools/ hold no unregistered read.
    Fails on the engine before this change: there is no scan."""
    cases = []
    pc = _sf_load_check(ROOT)
    two = ("def f(s):\n"
           "    root = pathlib.Path(s['path'])\n"
           "    return root / 'zz_new.json'\n")
    cases.append(('1. THE CASE: a bind on one line and a join on the next',
                  pc.set_file_reads(two) == [(3, 'zz_new.json')],
                  repr(pc.set_file_reads(two))))
    other = ("NAME = 'zz_const.json'\n"
             "def g(src, e, repo):\n"
             "    a = pathlib.Path(src['path']) / NAME\n"
             "    b = repo / str(e['path']) / 'zz_chain' / 'x.json'\n"
             "    return a, b\n")
    cases.append(('2. a constant, and a chain under a source path',
                  pc.set_file_reads(other) == [(3, 'zz_const.json'),
                                               (4, 'zz_chain/x.json')],
                  repr(pc.set_file_reads(other))))
    quiet = ("def h(s, repo):\n"
             "    a = pathlib.Path(s['path']) / 'reply_check.json'\n"
             "    b = pathlib.Path(s['path']) / 'zz.json'  # set-file: ok -- fixture\n"
             "    c = repo / 'zz_not_a_source.json'\n"
             "    return a, b, c\n")
    found = [rel for _ln, rel in pc.set_file_reads(quiet)
             if not pc._psf.registered(rel)]
    cases.append(('3. NEGATIVE CONTROL: registered, allowed and non-source joins '
                  'are not findings', found == [], repr(found)))
    kind, got = _sf_run(pc, 'set-file-registered')
    cases.append(('4. this repository\'s tools/ hold no unregistered read',
                  kind == 'findings' and got == [], got))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'set-file-registered finds every read from a source\'s folder '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_set_file_decided_in_a_practice_set():
    """set-file-decided (in a practice set) and the first update that turns
    it on.

    1. THE CASE: an undecided top-level NOTES.md is a finding naming the two
       ways to decide it, once the set's marker is written.
    2. A `stays` line with a reason decides it; a standard set-repository
       file (approvers.json, spec/) and a dot-entry need none.
    3. A `stays` line with no reason is itself a finding.
    4. A shared set whose precedent.json declares `adapters` is a finding: a
       copy never carries precedent.json.
    5. Before the marker (the set's first Update Vendors with this engine)
       the same findings are a note, never a stop.
    6. The first update's step notes NOTES.md and marks the set "noted":
       its own closing check and the push landing it stay a note. The next
       update makes the check strict; the one after does nothing.
    7. NEGATIVE CONTROL: an individual set is left out.
    Fails on the engine before this change: there is no such check."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_set_files as psf
    import precedent_update as pu
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-files-decided-'))
    cases = []
    try:
        env = _sf_env(tmp)
        s = tmp / 'zz-set'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(s)], env=env, check=True)
        (s / 'practices').mkdir()
        (s / 'practices' / 'zz-rule.md').write_text(
            '---\nslug: zz-rule\n---\n# zz\n\n## Rule\n\nx\n', encoding='utf-8')
        (s / 'spec').mkdir()
        (s / 'spec' / 'X.md').write_text('x\n', encoding='utf-8')
        (s / 'tools').mkdir()
        (s / 'approvers.json').write_text('{}', encoding='utf-8')
        (s / '.gitignore').write_text('x\n', encoding='utf-8')
        (s / 'NOTES.md').write_text('notes\n', encoding='utf-8')
        (s / 'precedent.json').write_text('{}', encoding='utf-8')
        man = {'name': 'zz-set', 'level': 'shared'}

        def write_manifest(**extra):
            (s / 'precedent-source.json').write_text(json.dumps({**man, **extra}),
                                                     encoding='utf-8')
            _sf_git(env, s, 'add', '-A')
            _sf_git(env, s, 'commit', '-qm', 'x')
        write_manifest()
        em = s / 'tools' / 'ENGINE_MANIFEST.json'
        em.write_text(json.dumps({'kind': 'source',
                                  psf.DECIDED_MARKER_KEY: '2026-11-01'}),
                      encoding='utf-8')
        _sf_git(env, s, 'add', '-A')
        _sf_git(env, s, 'commit', '-qm', 'engine')
        pc = _sf_load_check(s)
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('1. THE CASE: an undecided NOTES.md is a finding with both '
                      'ways to decide it', kind == 'findings' and len(got) == 1
                      and got[0].startswith('NOTES.md') and '"stays"' in got[0]
                      and 'precedent_set_files.py' in got[0], got))
        write_manifest(stays={'NOTES.md': "this repository's own notes"})
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('2. a stays line with a reason decides it; standard files '
                      'need none', kind == 'findings' and got == [], got))
        write_manifest(stays={'NOTES.md': ''})
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('3. a stays line with no reason is a finding',
                      kind == 'findings' and any('no reason given' in g for g in got),
                      got))
        write_manifest(stays={'NOTES.md': 'fixture'})
        (s / 'precedent.json').write_text(json.dumps(
            {'adapters': [{'from': 'a', 'to': 'b'}]}), encoding='utf-8')
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('4. adapters in a shared set\'s precedent.json is a finding',
                      kind == 'findings' and len(got) == 1
                      and got[0].startswith('precedent.json')
                      and 'adapters' in got[0], got))
        (s / 'precedent.json').write_text('{}', encoding='utf-8')
        write_manifest()
        em.write_text(json.dumps({'kind': 'source'}), encoding='utf-8')
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('5. before the marker, the same finding is a note',
                      kind == 'skipped' and 'NOTES.md' in got
                      and 'not made this strict here yet' in got, got))
        rep = _SfRep()
        pu.set_files_decided_step(s, rep)
        marked = json.loads(em.read_text(encoding='utf-8')).get(psf.DECIDED_MARKER_KEY)
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('6. the first update notes NOTES.md and marks it noted; its '
                      'own check, and the push that lands it, stay a note',
                      any('NOTES.md' in o and 'not a stop' in o for _n, o in rep.steps)
                      and str(marked).startswith(psf.DECIDED_NOTED)
                      and kind == 'skipped' and not rep.left,
                      repr(rep.steps) + repr(marked) + repr((kind, got))))
        rep2 = _SfRep()
        pu.set_files_decided_step(s, rep2)
        marked = json.loads(em.read_text(encoding='utf-8')).get(psf.DECIDED_MARKER_KEY)
        kind, got = _sf_run(pc, 'set-file-decided')
        rep3 = _SfRep()
        pu.set_files_decided_step(s, rep3)
        cases.append(('6b. the next update makes it strict, and the third does '
                      'nothing', any('strict here from now on' in o
                                     for _n, o in rep2.steps)
                      and not str(marked).startswith(psf.DECIDED_NOTED)
                      and kind == 'findings' and got and got[0].startswith('NOTES.md')
                      and not rep3.steps,
                      repr(rep2.steps) + repr(marked) + repr((kind, got)) + repr(rep3.steps)))
        write_manifest(level='individual')
        kind, got = _sf_run(pc, 'set-file-decided')
        cases.append(('7. NEGATIVE CONTROL: an individual set is left out',
                      kind == 'skipped' and 'individual' in got, got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'set-file-decided decides every top-level file of a shared set '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_a_copy_never_carries_a_copy():
    """A copy never carries another source's copy (Morgan, 2026-11-01), and
    the narrowing the review asked for keeps `carries` working.

    1. THE CASE: a set rooted at its repository's top (set_root '') that
       exports process/zz-other/, its own copy of another set (recorded in
       process/manifest_zz-other.json), is refused, by name, nothing copied.
    2. ...and one exporting process/upstream/ the same way.
    3. A consumer whose copy ALREADY holds that nested copy carries on: the
       update succeeds and names it with the decommission line.
    4. A carried set the carrier writes, that the consumer also declares as
       a source of its own, still copies.
    5. A files-only copy takes its exports and precedent-source.json and
       nothing else: no registered file, no set_files record.
    Fails on the engine before this change: case 1 copies the nested copy."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-files-nested-'))
    cases = []
    try:
        env = _sf_env(tmp)
        files = {'process/zz-other/practices/o.md': '---\nslug: o\n---\n# o\n\n## Rule\n\nx\n',
                 'process/zz-other/precedent-source.json': '{"name": "zz-other"}',
                 'process/manifest_zz-other.json': '{"upstream": {}}',
                 'process/upstream/practices/u.md': 'u\n',
                 'RULES.md': 'rules\n', **_SF_ALL_FILES}
        clone, _c = _sf_make_set(tmp, env, 'zz-nest', files,
                                 {'exports': ['RULES.md', 'process/zz-other']})
        host = _sf_make_host(tmp, env, 'host', [_sf_entry('zz-nest')])
        r = _sf_checkin(env, host, 'zz-nest', 'update', clone, '--force')
        out = r.stdout + r.stderr
        cases.append(('1. THE CASE: an export that is another set\'s copy is '
                      'refused, nothing copied', r.returncode != 0
                      and 'process/zz-other' in out
                      and "never carries another source's copy" in out
                      and not (host / 'process' / 'zz-nest').exists(),
                      failure_detail(out, 400)))
        clone2, _c = _sf_make_set(tmp, env, 'zz-nest2', files,
                                  {'exports': ['process/upstream']})
        host2 = _sf_make_host(tmp, env, 'host2', [_sf_entry('zz-nest2')])
        r = _sf_checkin(env, host2, 'zz-nest2', 'update', clone2, '--force')
        out = r.stdout + r.stderr
        cases.append(('2. ...and one exporting process/upstream/',
                      r.returncode != 0 and 'universal catalogue' in out,
                      failure_detail(out, 400)))
        held = host / 'process' / 'zz-nest' / 'process' / 'zz-other'
        held.mkdir(parents=True, exist_ok=True)
        (held / 'precedent-source.json').write_text('{"name": "zz-other"}',
                                                    encoding='utf-8')
        r = _sf_checkin(env, host, 'zz-nest', 'update', clone, '--force')
        out = r.stdout + r.stderr
        cases.append(('3. a nested copy already here is named with its '
                      'decommission line, and the update carries on',
                      r.returncode == 0 and 'nested copy' in out
                      and 'precedent_decommission.py' in out,
                      failure_detail(out, 400)))
        inner = {'inner/practices/i.md': '---\nslug: i\n---\n# i\n\n## Rule\n\nx\n',
                 'inner/precedent-source.json': json.dumps(
                     {'name': 'zz-inner', 'level': 'shared', 'visibility': 'public'})}
        carrier, _c = _sf_make_set(tmp, env, 'zz-carrier', inner,
                                   {'carries': [{'name': 'zz-inner', 'path': 'inner'}]})
        host3 = _sf_make_host(tmp, env, 'host3', [
            _sf_entry('zz-carrier'), _sf_entry('zz-inner')])
        r = _sf_checkin(env, host3, 'zz-carrier', 'update', carrier, '--force')
        cases.append(('4. a carried set the consumer also declares still copies',
                      r.returncode == 0 and (host3 / 'process' / 'zz-carrier' / 'inner'
                                             / 'practices' / 'i.md').is_file(),
                      failure_detail(r.stdout + r.stderr, 400)))
        only, _c = _sf_make_set(tmp, env, 'zz-only', {'RULES.md': 'r\n', **_SF_ALL_FILES},
                                {'exports': ['RULES.md']})
        host4 = _sf_make_host(tmp, env, 'host4', [_sf_entry('zz-only', exports_only=True)])
        r = _sf_checkin(env, host4, 'zz-only', 'update', only, '--force')
        ocopy = host4 / 'process' / 'zz-only'
        held_files = sorted(p.relative_to(ocopy).as_posix() for p in ocopy.rglob('*')
                            if p.is_file()) if ocopy.is_dir() else []
        up = json.loads((host4 / 'process' / 'manifest_zz-only.json').read_text(
            encoding='utf-8')).get('upstream') or {}
        cases.append(('5. a files-only copy takes its exports and nothing else',
                      held_files == ['RULES.md', 'precedent-source.json']
                      and 'set_files' not in up,
                      repr(held_files) + repr(up) + failure_detail(r.stdout + r.stderr, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a copy of a set never carries another source\'s copy '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))
