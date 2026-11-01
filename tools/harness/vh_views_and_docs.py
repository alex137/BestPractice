# The harness tests for generated views
#
# tools/harness/vh_views_and_docs.py -- part of the verification harness:
# generated views, the doc tools and the todo index.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_titles_match_source(files, original_practices_by_number):
    """A practice's title is what MAP.md shows and what a person reads to
    decide whether to open it -- and it was entirely unchecked. Every title
    in the catalogue could have been rewritten with the harness green."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        orig = original_practices_by_number.get(fm.get('source_practice_number'))
        if orig is None:
            continue
        # _json_str, not the raw field: a title containing ': ' has to be
        # quoted for the frontmatter to be valid YAML at all (see
        # split_practices._yaml_scalar), and the quotes are encoding, not
        # content. Comparing raw would report ten false title rewrites.
        if bv._json_str(fm.get('title', '')).strip() != orig['title'].strip():
            ok = False
            print(f"  {f.name}: title differs from PRACTICES.md\n"
                  f"      file:   {bv._json_str(fm.get('title',''))!r}\n"
                  f"      source: {orig['title']!r}")
    check('titles match the source catalogue exactly', ok)


def check_reachability(files):
    """A GATE counts, and it did not until 2026-09-14. This check was written
    before gates existed and knew three channels: a check, a narrow glob, an
    occasion-index line. tools/routing_scope.json's own note has called gates
    "the fourth loading channel" since phase 4, and tools/build_views.py's
    over-budget message names step 1 of its reduction menu as "give the
    practice a REAL applies_to glob or a `gates:` entry and drop its
    `occasion:`" -- a move this check then refused, so the menu's cheapest
    step was unreachable. Found by taking it: landing
    next-steps-after-commit put the occasion index 33 tokens over its
    ceiling, dropping its occasion: was step 1, and the harness called a
    practice the stop hook refuses every turn over "unreachable". A gate is a
    real invocation point (tools/precedent_gate.py resolves and prints it),
    which is the whole test this check applies to the other three."""
    ok = True
    for stem, (fm, sections, f) in files.items():
        if fm.get('tier') != 'on-demand':
            continue
        # A practice not in force (deduplicated into another, or retired)
        # binds nothing, so there is nothing for a session to reach: its
        # text lives in the practice it names, or nowhere by decision.
        if (fm.get('status') or 'active').strip().strip('"') != 'active':
            continue
        checked_by = fm.get('checked_by', 'null')
        applies_to = fm.get('applies_to', '[]')
        occasion = fm.get('occasion', '""')
        gates = fm.get('gates', '[]')
        has_checked_by = checked_by not in ('null', '')
        has_narrow_applies = applies_to not in ('[]', '["**"]', '')
        has_occasion = occasion not in ('""', "''", '')
        has_gate = gates.strip() not in ('[]', 'null', '')
        if not (has_checked_by or has_narrow_applies or has_occasion or has_gate):
            ok = False
            print(f"  UNREACHABLE: {f.name} (slug={stem}) has no checked_by, "
                  f"no narrower-than-** applies_to, no occasion and no gate")
    check('reachability (every on-demand practice has checked_by / narrow applies_to / occasion / gate)', ok)
def check_rename_links_leaves_dated_records_alone():
    """rename-updates-links leaves history alone: a generated view, a closed
    todo item, a `## Story` section and a declared record file each name a
    deleted path as it was (2026-09-30, a consumer's promote refused on all
    four after an Update Vendors deleted files its records cited). Nothing
    caught it upstream: the check only ever ran on this repo's own
    deletions, whose few records its own exemption list covers.

    A throwaway consumer run through the real check. CONTROLS, which must
    still fire: a live document, an OPEN todo item, and a gotcha's Fix
    section naming the same deleted path."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='dated-records-'))
    gone = 'process/upstream/templates/harness/LEDGER.md'
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        shutil.copy(ROOT / 'practices' / 'rename-updates-links.md', up / 'practices')
        (repo / gone).parent.mkdir(parents=True, exist_ok=True)
        (repo / gone).write_text('ledger\n', encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}],
            'record_paths': [{'path': 'process/MIGRATION_RECORD.md',
                              'reason': 'the migration as it happened'}]}), encoding='utf-8')
        files = {
            'gotchas/INDEX.md': f'---\ngenerated_by: tools/build_gotcha_index.py\n---\n- `{gone}` tripped it\n',
            'todo/todo-2026-09-12-closed.md': f'---\nstatus: done\n---\n## What\nRead `{gone}`.\n',
            'todo/todo-2026-09-25-open.md': f'---\nstatus: open\n---\n## What\nE2 trips on `{gone}`:117.\n',
            'gotchas/gotcha-2026-09-06-x.md': (f'---\nstatus: live\n---\n## Symptom\nx\n## Story\n'
                                               f'We ran `cat {gone}`.\n## Fix\nEdit `{gone}`.\n'),
            'process/MIGRATION_RECORD.md': f'Moved `{gone}` on 2026-09-18.\n',
            'README.md': f'See `{gone}`.\n',
        }
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        g('checkout', '-q', '-b', 'update-vendors')
        g('rm', '-q', gone); g('commit', '-qm', 'the hop deletes it')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'rename-updates-links'], cwd=str(repo), capture_output=True,
                           text=True, env=env, timeout=300)
        out = r.stdout + r.stderr
        for rel, why in (('gotchas/INDEX.md', 'a generated view'),
                         ('todo/todo-2026-09-12-closed.md', 'a closed todo item'),
                         ('gotchas/gotcha-2026-09-06-x.md:7', 'a Story section'),
                         ('process/MIGRATION_RECORD.md', 'a declared record file')):
            cases.append((f'{why} is left alone', rel not in out, failure_detail(out, 400)))
        for rel, why in (('README.md:1', 'a live document'),
                         ('todo/todo-2026-09-25-open.md', 'an OPEN todo item'),
                         ('gotchas/gotcha-2026-09-06-x.md:9', "a gotcha's Fix")):
            cases.append((f'CONTROL: {why} is still flagged', rel in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'rename-updates-links leaves dated records alone, and still reads live text '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_views_refuse_to_drop_hand_edits():
    """A line typed into a generated MAP.md that no version of MAP.source.md
    holds is a hand edit, and the rebuild names it rather than erasing it; a
    line the source itself dropped, and a practice or tool index row, are not
    (2026-10-12: a row typed into a consumer's MAP.md was erased by the next
    Update Vendors without a word)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
    finally:
        sys.path.pop(0)
    name = 'a rebuild names the lines typed into a generated view by hand'
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        (tmp / 'MAP.source.md').write_text('| A | the row the source keeps |\n')
        old = ('| A | the row the source keeps |\n| B | a row typed into MAP.md by hand |\n'
               '| [some-practice](practices/some-practice.md) | on-demand | x |\n')
        new = '| A | the row the source keeps |\n'
        got = bv.hand_edits(tmp, tmp / 'MAP.md', old, new, 'MAP.source.md')
        cases = [('the hand-typed row is named', got == ['| B | a row typed into MAP.md by hand |']),
                 ('a practice index row is not', all('practices/' not in g for g in got)),
                 ('nothing is named when the rebuild keeps every line',
                  bv.hand_edits(tmp, tmp / 'MAP.md', new, new, 'MAP.source.md') == []),
                 ('a line the source still holds is not',
                  bv.hand_edits(tmp, tmp / 'MAP.md', old.replace('| B | a row typed into MAP.md by hand |\n', ''),
                                '', 'MAP.source.md') == [])]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_render_contents_can_be_switched_off():
    """A document with three sections gets a contents list and back-links;
    the same document carrying doc_html.NO_CONTENTS_MARK gets neither
    (2026-10-11: a short page whose author had asked for no contents list
    got one back when a redraft added sections)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_html as dh
    finally:
        sys.path.pop(0)
    name = 'the contents list is generated, and a document can switch it off'
    body = ('<h1>T</h1>\n' + ''.join(f'<h2 id="s{i}">S{i}</h2>\n<p>x</p>\n' for i in range(3)))
    on = dh._wire_contents(body)
    off = dh._wire_contents(dh.NO_CONTENTS_MARK + '\n' + body)
    cases = [('three sections get a contents list', 'nav class="contents"' in on),
             ('three sections get back-links', 'contents-back' in on),
             ('the mark switches the list off', 'nav class="contents"' not in off),
             ('the mark switches the back-links off', 'contents-back' not in off)]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_untracked_renders_use_source_fingerprints():
    """A host that stops committing its renders (doc_html RENDERS_TRACKED =
    False) cannot judge a page by the render's own hash: a render carries
    its build time and differs on every build (2026-10-04). The ledger then
    records a fingerprint of the sources. Both directions: a rebuild with
    the same sources stays published; a source edit makes the page
    unpublished."""
    import json as _json, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_html as dh
    finally:
        sys.path.pop(0)
    name = 'untracked renders are judged by their sources, not their own hash'
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / 'a.md').write_text('# A\n')
    (tmp / 'a.html').write_text('<p>built at 1</p>')
    led = tmp / 'shared.json'
    saved = {k: getattr(dh, k) for k in ('ROOT', 'RENDER_LEDGER', 'THREAD_LEDGER', 'RENDERS_TRACKED',
             '_current_branch', '_default_branch', '_changed_vs_base', '_render_units')}
    cases = []
    try:
        dh.ROOT, dh.RENDER_LEDGER, dh.THREAD_LEDGER = tmp, str(led), None
        dh.RENDERS_TRACKED = False
        dh._current_branch = lambda: 'main'
        dh._default_branch = lambda: 'main'
        dh._changed_vs_base = lambda: set()
        dh._render_units = lambda: [('a.html', ['a.md'], 'https://shared.example/a')]
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            dh.record_published(['a.html'], trunk=True)
        rec = _json.loads(led.read_text()).get('a.html')
        cases.append(('the ledger records the source fingerprint, not the render hash',
                      rec == dh._fingerprint(['a.md']) and rec != dh._sha256(tmp / 'a.html')))
        (tmp / 'a.html').write_text('<p>built at 2</p>')
        cases.append(('a rebuild from the same sources stays published',
                      dh.stale(trunk=True)[1] == []))
        (tmp / 'a.md').write_text('# A, edited\n')
        (tmp / 'a.html').write_text('<p>built at 3</p>')
        cases.append(('a source edit makes the page unpublished',
                      [r for r, _u in dh.stale(trunk=True)[1]] == ['a.html']))
    finally:
        for k, v in saved.items():
            setattr(dh, k, v)
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_todo_migrate_refuses_a_subdirectory():
    """todo_migrate.py writes only into the repository root's todo/.

    2026-10-01, from a consumer's Update Vendors: `--repo docs` wrote 33
    items under docs/todo/, which build_todo_index.py and every check never
    read, and they sat invisible for 13 days. A --repo below the root is
    refused before anything is written; the root itself still migrates."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='todo-migrate-root-'))
    cases = []
    try:
        repo = tmp / 'proj'
        (repo / 'docs').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        (repo / 'docs' / 'TODO.md').write_text(
            '# TODO\n\n- **An item** -- something to do.\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'todo_migrate.py'),
                            '--repo', str(repo / 'docs'), '--source', 'todo.md',
                            '--apply'], capture_output=True, text=True, timeout=120)
        cases.append(('a --repo below the repository root is refused',
                      r.returncode != 0 and 'not the repository root' in
                      (r.stdout + r.stderr), failure_detail(r.stdout + r.stderr, 300)))
        cases.append(('...and writes nothing',
                      not (repo / 'docs' / 'todo').exists(), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'todo_migrate.py refuses to write items below the repository root '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_loader_caps_unmeasured_without_a_declared_source():
    """loader-within-caps says COULD NOT VERIFY, never a violation and never a
    pass, where a declared source is not on disk (2026-09-30).

    A consumer's GitHub test runs on a bare checkout, with none of the
    sibling practice sets it declares. `build_views.py --budgets` only reads,
    but it fell through to the refusal meant for WRITING a block from an
    incomplete set, so the test failed on every private consumer that
    declares a shared set. Nothing caught it here: BestPractice is public,
    so its own loader block leaves every private source out and never needs
    one on disk. A throwaway private consumer, run through the real tools."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='caps-unmeasured-'))
    try:
        c = tmp / 'consumer'
        (c / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, c / 'tools' / f.name)
        # Per-part caps bind only where no session-load total is declared
        # (build_views.TOTAL_KEY); this fixture tests them, so it has none.
        _drop_session_load_total(c / 'tools' / 'session_load_budgets.json')
        shutil.copytree(ROOT / 'practices', c / 'up' / 'practices')
        (c / 'precedent.json').write_text(json.dumps({'visibility': 'private', 'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'up'},
            {'level': 'shared', 'name': 'precedent-shared-missing',
             'path': '../precedent-shared-missing'}]}), encoding='utf-8')
        (c / 'AGENTS.md').write_text('# Notes\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                                     '<!-- END GENERATED -->\n', encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        subprocess.run(['git', 'init', '-q'], cwd=c, env=env)
        subprocess.run(['git', 'add', '-A'], cwd=c, env=env)
        subprocess.run(['git', 'commit', '-qm', 'x'], cwd=c, env=env)
        r = subprocess.run([sys.executable, 'tools/build_views.py', '--budgets',
                            '--agents-only'], cwd=c, capture_output=True, text=True,
                           timeout=300)
        cases.append(('--budgets only reads: exit 0 and says it measured nothing',
                      r.returncode == 0 and 'budgets NOT VERIFIED' in r.stdout,
                      failure_detail(r.stdout + r.stderr, 300)))
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'loader-within-caps'], cwd=c, capture_output=True,
                           text=True, timeout=300)
        out = r.stdout + r.stderr
        cases.append(('loader-within-caps is not violated', '0 violated' in out, failure_detail(out, 400)))
        cases.append(('...and says COULD NOT VERIFY, not a pass',
                      'COULD NOT VERIFY  loader-within-caps' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'loader-within-caps cannot verify without a declared source, and says so '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_loader_block_with_an_absent_individual_set():
    """A private consumer's loader block carries no individual set, so it is
    judged the same with or without one (2026-10-19, replacing 2026-10-09).

    Until 2026-10-19 the block of a private consumer carried the person's
    individual practices and a "machine-dependent" paragraph, and a bare
    runner with no individual set could only call it COULD NOT VERIFY (a
    consuming repository's pull request into main once failed on exactly
    that, 2026-10-09). Part 4 of the copied-in shared sets plan took the
    individual set out of every private repository's tracked block: everyone
    there reads it, and a person's own rules bind that person alone. So the
    block no longer depends on whose machine regenerated it.

    A throwaway private consumer whose block was generated with a fixture
    individual set: (a) the block carries none of it; (b) with no user
    config, every reader verifies it and passes; (c) with the user config,
    the same; (d) a hand-edit is still violated."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='individual-absent-'))
    try:
        c = tmp / 'consumer'
        (c / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, c / 'tools' / f.name)
        shutil.copytree(ROOT / 'practices', c / 'up' / 'practices')
        # The practice the provenance check enforces is in force here, as in
        # every repository that uses Precedent (its materialized practices/).
        (c / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'generated-artifact-provenance.md',
                    c / 'practices' / 'generated-artifact-provenance.md')
        fm = ('---\nslug:        {slug}\ntitle:       A fixture practice\n'
              'tier:        {tier}\nseverity:    default\napplies_to:  ["fixture/**"]\n'
              'occasion:    "fixture"\ngates:       []\nindex_clause: "fixture"\n'
              'checked_by:  null\ndefines:     []\nstatus:      active\n'
              'in_force_at: null\nsupersedes:  []\noverrides:   null\nadded:       "2026-10-09"\n'
              'approved_by: "Fixture, 2026-10-09"\n---\n\n## Rule\n{rule}\n\n'
              '## Why\nBecause.\n\n## Story\nOnce.\n')
        (c / 'local' / 'practices').mkdir(parents=True)
        (c / 'local' / 'practices' / 'zz-local.md').write_text(
            fm.format(slug='zz-local', tier='on-demand', rule='Do it here.'),
            encoding='utf-8')
        ind = tmp / 'fixture-individual'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'practices' / 'zz-personal.md').write_text(
            fm.format(slug='zz-personal', tier='resident',
                      rule='**Say it plainly.** A fixture individual rule.'),
            encoding='utf-8')
        cfg = tmp / 'user-config.json'
        cfg.write_text(json.dumps({'individual': {'name': 'fixture-individual',
                                                  'path': str(ind)}}),
                       encoding='utf-8')
        (c / 'precedent.json').write_text(json.dumps({'visibility': 'private', 'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': 'up'},
            {'level': 'repo-local', 'name': 'local', 'path': 'local'}]}),
            encoding='utf-8')
        (c / 'AGENTS.md').write_text('# Notes\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                                     '<!-- END GENERATED -->\n', encoding='utf-8')
        base = {k: v for k, v in os.environ.items()
                if k not in ('PRECEDENT_GIT_TOKEN', 'CLAUDE_CODE_REMOTE')}
        base.update(GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_AUTHOR_NAME='t',
                    GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t',
                    GIT_COMMITTER_EMAIL='t@t')
        with_set = dict(base, PRECEDENT_USER_CONFIG=str(cfg))
        without = dict(base, PRECEDENT_USER_CONFIG=str(tmp / 'no-such-config.json'))

        def run(env, *argv):
            r = subprocess.run([sys.executable, *argv], cwd=c, capture_output=True,
                               text=True, timeout=300, env=env)
            return r.returncode, r.stdout + r.stderr

        run(with_set, 'tools/build_views.py', '--agents-only')
        agents = (c / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('(a) the block carries no individual practice and no '
                      'machine-dependent paragraph',
                      'zz-personal' not in agents
                      and 'came from an INDIVIDUAL source' not in agents
                      and 'individual)' not in agents, agents[:600]))
        subprocess.run(['git', 'init', '-q'], cwd=c, env=base)
        subprocess.run(['git', 'add', '-A'], cwd=c, env=base)
        subprocess.run(['git', 'commit', '-qm', 'x'], cwd=c, env=base)

        def provenance(env):
            return run(env, 'tools/precedent_check.py', '--only',
                       'generated-artifact-provenance')

        # (b) No individual set here, as on a bare GitHub runner.
        rc, out = run(without, 'tools/build_views.py', '--check', '--agents-only')
        cases.append(('(b) without the set, build_views --check verifies and '
                      'passes', rc == 0 and 'NOT VERIFIABLE' not in out
                      and '--check FAIL' not in out, failure_detail(out, 400)))
        rc, out = provenance(without)
        cases.append(('(b) without the set, provenance passes',
                      rc == 0 and '1 passed' in out and '0 violated' in out
                      and 'COULD NOT VERIFY' not in out, failure_detail(out, 600)))
        # (c) The person's individual set resolves: the same verdict.
        rc, out = provenance(with_set)
        cases.append(('(c) with the set, provenance passes',
                      rc == 0 and '1 passed' in out and '0 violated' in out
                      and 'COULD NOT VERIFY' not in out, failure_detail(out, 600)))
        # (d) ...and a hand-edit is still caught.
        (c / 'AGENTS.md').write_text(agents.replace(
            '<!-- END GENERATED -->', 'A line edited in by hand.\n<!-- END GENERATED -->'),
            encoding='utf-8')
        rc, out = provenance(without)
        cases.append(('(d) a hand-edit is still violated', rc != 0
                      and '1 violated' in out and 'stale or hand-edited' in out,
                      failure_detail(out, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a private consumer\'s loader block carries no individual set, and '
          f'is verified with or without one ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_whats_new_skips_precedents_own_updates():
    """tools/precedent_whats_new.py -- a day whose only change brought
    Precedent's own files in (an Update Vendors) is quiet in a consuming
    repository: its news log is about that repository (Morgan, 2026-10-08:
    "it is about what is happening in THAT repo not what is happening in
    Precedent"). The repository's own work on the same footing still counts,
    and so does a hand edit to its instructions; in a repository that
    vendors nothing (BestPractice itself) a tools/ change is news."""
    import datetime as _dt, tempfile
    import precedent_whats_new as pwn
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='whats-new-vendored-'))
    try:
        def g(cwd, *a, when=None):
            env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                       GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
            if when:
                env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = when
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env).stdout.strip()

        def make(name, vendored):
            repo = tmp / name
            g(tmp, 'init', '-q', '-b', 'main', str(repo))
            files = {'precedent.json': '{"fallback_timezone": "UTC"}\n',
                     'README.md': '# x\n'}
            if vendored:
                files.update({
                    'tools/ENGINE_MANIFEST.json': json.dumps(
                        {'kind': 'consumer', 'files': ['engine.py'],
                         'hook_files': ['gate.sh']}),
                    'process/manifest.json': json.dumps(
                        {'upstream': {'vendored_at': 'process/upstream'}}),
                    'tools/engine.py': 'v1\n'})
            for rel, text in files.items():
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text(text, encoding='utf-8')
            g(repo, 'add', '-A'); g(repo, 'commit', '-qm', 'init',
                                     when='2026-09-01T12:00:00+00:00')
            return repo

        def commit(repo, files, when):
            for rel, text in files.items():
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text(text, encoding='utf-8')
            g(repo, 'add', '-A'); g(repo, 'commit', '-qm', 'c', when=when)

        def day(repo, d):
            tz = _dt.timezone.utc
            start = _dt.datetime.combine(d, _dt.time(0), tzinfo=tz)
            return pwn.changes_between(repo, 'main', start,
                                       start + _dt.timedelta(days=1))

        c = make('consumer', True)
        commit(c, {'tools/engine.py': 'v2\n', 'process/upstream/a.md': 'x\n',
                   'MAP.md': 'map\n', '.claude/hooks/gate.sh': 'stub\n'},
               '2026-09-02T12:00:00+00:00')
        commit(c, {'notes/plan.md': 'own work\n'}, '2026-09-03T12:00:00+00:00')
        commit(c, {'tools/engine.py': 'v3\n', 'notes/plan.md': 'more\n'},
               '2026-09-04T12:00:00+00:00')
        commit(c, {'AGENTS.md': 'own instructions\n'}, '2026-09-05T12:00:00+00:00')
        g(c, 'rm', '-q', 'tools/engine.py')
        g(c, 'commit', '-qm', 'drop', when='2026-09-06T12:00:00+00:00')
        cases += [
            ('a day of only vendored files and the views beside them is quiet',
             day(c, _dt.date(2026, 9, 2)) is None),
            ("the repository's own work is news",
             day(c, _dt.date(2026, 9, 3)) is not None),
            ('a commit mixing vendored files and its own work is news',
             day(c, _dt.date(2026, 9, 4)) is not None),
            ('a hand edit to its instructions alone is news',
             day(c, _dt.date(2026, 9, 5)) is not None),
            ('an update deleting a file it vendored is quiet too',
             day(c, _dt.date(2026, 9, 6)) is None),
        ]
        b = make('upstream', False)
        commit(b, {'tools/engine.py': 'v2\n'}, '2026-09-02T12:00:00+00:00')
        cases.append(('in a repository that vendors nothing, a tools/ change is news',
                      day(b, _dt.date(2026, 9, 2)) is not None))
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] for c in cases if not c[1]]
    check(f"What's new leaves Precedent's own updates out of a repository's "
          f"news ({len(cases)} stated cases)", not bad, '; '.join(bad))


def check_whats_new_log_mechanics():
    """tools/precedent_whats_new.py, the mechanics behind "What's new?"
    (practice: whats-new, 2026-09-30).

    A throwaway repository with main's history on chosen days (UTC, the
    repo's declared zone): a day with a change, an empty day, a day whose
    only commit touches the log itself, and a day that adds a document.
    Stated cases: the first run lists exactly the two real days, newest
    document named, and names the quiet ones; an entry's heading carries
    its weekday, --check flags an entry not in the shape (heading, opening
    line, a bold key phrase per bullet), and headline case leaves the
    slug alone; --mark covers them and a second run lists none; a day
    that has not finished cannot be marked; the later of this checkout's
    log and main's is read; an entry naming an approval is flagged; the
    log never ships to another project."""
    import datetime as _dt, tempfile
    import precedent_whats_new as pwn
    import checkin as _ck
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='whats-new-'))
    today = _dt.date(2026, 9, 10)
    try:
        origin, repo = tmp / 'origin.git', tmp / 'repo'

        def g(cwd, *a, when=None):
            env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                       GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
            if when:
                env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = when
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env).stdout.strip()

        def commit(rel, text, msg, when):
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
            g(repo, 'add', '-A'); g(repo, 'commit', '-qm', msg, when=when)

        g(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        g(tmp, 'init', '-q', '-b', 'main', str(repo))
        g(repo, 'remote', 'add', 'origin', str(origin))
        (repo / 'precedent.json').write_text('{"fallback_timezone": "UTC"}\n',
                                             encoding='utf-8')
        commit('a.txt', '0', 'before the window', '2026-08-01T12:00:00Z')
        commit('a.txt', '1', 'Faster start-up', '2026-09-05T12:00:00Z')
        # 2026-09-06: nothing.
        commit('WHATS_NEW.md', '# What\'s new\n', 'Log only', '2026-09-07T12:00:00Z')
        commit('docs/PHILOSOPHY.md', 'why\n', 'A new philosophy note', '2026-09-08T12:00:00Z')
        g(repo, 'push', '-q', 'origin', 'main')
        g(repo, 'fetch', '-q', 'origin')

        _tz, through, days = pwn.missing_days(repo, today=today)
        got = [d.isoformat() for d, _ in days]
        cases.append(('the first run lists only the days main changed, the log\'s own '
                      'commit left out', got == ['2026-09-05', '2026-09-08'], str(got)))
        _tz, _t, back = pwn.missing_days(repo, today=today, since=_dt.date(2026, 8, 1))
        got_back = [d.isoformat() for d, _ in back]
        cases.append(('--since backfills a first run from the day it names',
                      got_back == ['2026-08-01', '2026-09-05', '2026-09-08'], str(got_back)))
        _tz, _t, _active, quiet = pwn.scan_days(repo, today=today)
        got_quiet = [d.isoformat() for d in quiet]
        cases.append(('a quiet day, and one whose only change is the log, is named '
                      'as quiet rather than dropped silently',
                      got_quiet == ['2026-09-03', '2026-09-04', '2026-09-06',
                                    '2026-09-07', '2026-09-09'], str(got_quiet)))
        cases.append(('a heading carries its weekday',
                      pwn.heading_for(_dt.date(2026, 9, 30), 'a-slug')
                      == '## Wednesday 2026-09-30: a-slug',
                      pwn.heading_for(_dt.date(2026, 9, 30), 'a-slug')))
        good = (f'## Wednesday 2026-09-30: safer-merges\n\n{pwn.HEADLINE}\n\n'
                f'- **A change** (a name)\n')
        old = '## 2026-09-30\n\n**A summary of the bullets.**\n\n- A change\n'
        wrong_day = good.replace('Wednesday', 'Tuesday')
        no_line = good.replace(pwn.HEADLINE, '**Merges got safer.**')
        no_bold = good.replace('**A change**', 'A change')
        backticked = good.replace('safer-merges', '`safer-merges`')
        mid_bold = good.replace('**A change** (a name)', 'A **change** (a name)')
        cases.append(('an entry in the shape passes, and the old shape, a wrong '
                      'weekday, a summary headline, a bullet with no bold key '
                      'phrase, one whose bold is mid-sentence and a backticked '
                      'slug are each flagged',
                      pwn.shape_problems(good) == []
                      and len(pwn.shape_problems(old)) == 3
                      and len(pwn.shape_problems(wrong_day)) == 1
                      and len(pwn.shape_problems(no_line)) == 1
                      and len(pwn.shape_problems(no_bold)) == 1
                      and len(pwn.shape_problems(backticked)) == 1
                      and len(pwn.shape_problems(mid_bold)) == 1,
                      str([pwn.shape_problems(t) for t in
                           (good, old, wrong_day, no_line, no_bold, backticked,
                            mid_bold)])))
        bare = good.replace('(a name)', '(`docs/GUIDE.md` and `tools/run.py`)')
        linked = good.replace('(a name)', '([`docs/GUIDE.md`](docs/GUIDE.md), '
                              '`python3 tools/run.py`, `practices/*.md`)')
        got_bare = pwn.unlinked_files(bare)
        got_linked = pwn.unlinked_files(linked)
        cases.append(('a file an entry names without a link is flagged, and a '
                      'linked one, a command line and a glob are not',
                      [n for _, n in got_bare] == ['docs/GUIDE.md', 'tools/run.py']
                      and got_linked == [],
                      f'{got_bare} {got_linked}'))
        import title_case as _tc
        kept = _tc.title_case('Wednesday 2026-09-30: safer-merges')
        compound = _tc.title_case('a lock-in for safer-merges')
        cases.append(('headline case leaves a dated heading\'s slug alone, and '
                      'still capitalizes a compound elsewhere',
                      kept == 'Wednesday 2026-09-30: safer-merges'
                      and compound == 'A Lock-In for Safer-Merges',
                      f'{kept!r} {compound!r}'))
        added = dict((d.isoformat(), ch['added']) for d, ch in days).get('2026-09-08', [])
        cases.append(('a day\'s new document is listed', 'docs/PHILOSOPHY.md' in added,
                      str(added)))
        ok, msg = pwn.mark(repo, _dt.date(2026, 9, 8), today=today)
        _tz, through, days = pwn.missing_days(repo, today=today)
        cases.append(('--mark covers them, and a second run lists none',
                      ok and through == _dt.date(2026, 9, 8) and days == [],
                      f'{msg} {through} {days}'))
        ok, msg = pwn.mark(repo, today, today=today)
        cases.append(('a day that has not finished cannot be marked', not ok, msg))
        # main's log is ahead of this checkout's: the later one is read.
        (repo / 'WHATS_NEW.md').write_text('---\nchecked_through: 2026-09-09\n---\n',
                                           encoding='utf-8')
        g(repo, 'commit', '-qam', 'log', when='2026-09-10T01:00:00Z')
        g(repo, 'push', '-q', 'origin', 'main'); g(repo, 'fetch', '-q', 'origin')
        g(repo, 'reset', '-q', '--hard', 'HEAD~1')
        _text, later = pwn.read_state(repo)
        cases.append(('the later of this checkout\'s log and main\'s is read',
                      later == _dt.date(2026, 9, 9), str(later)))
        hits = pwn.approval_lines('---\nchecked_through: 2026-09-09\n---\n'
                                  '## 2026-09-09\n- Faster start-up (approved by M)\n'
                                  '- Shorter instructions (about 800 tokens)\n')
        cases.append(('an entry naming an approval is flagged, and only it',
                      [n for n, _ in hits] == [5], str(hits)))
        # The reply check's declared pairing, read from reply_check.json
        # itself: a reply showing the log opens with the log's link.
        import re as _re
        decl = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
            encoding='utf-8')) if r.get('practice') == 'whats-new']
        pair = (decl[0].get('require_paired_with') or [{}])[0] if decl else {}

        def refused(reply):
            return bool(_re.search(pair.get('if_matches', '(?!)'), reply, _re.I | _re.M)
                        and not _re.search(pair.get('must_also_match', ''), reply,
                                           _re.I | _re.M))
        linked = ('**The log:** [WHATS_NEW.md](https://x/WHATS_NEW.md). Check '
                  'here daily.\n\n' + pwn.HEADLINE + '\n')
        late = 'Wrote one day.\n\n' + linked
        cases.append(('a reply showing the log is refused unless its first line '
                      'carries the log\'s link; one that does not show it is '
                      'untouched',
                      bool(pair) and not refused(linked) and refused(late)
                      and not refused('Nothing about the log here.\n'),
                      str(pair)[:200]))
        rule = _ck.vendoring_rule('WHATS_NEW.md')
        cases.append(('a project\'s log never ships to another project',
                      bool(rule) and rule[1] is False, str(rule)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the What\'s new log lists the days it lacks, and only those '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_doc_lint_strict_refuses_the_gate_scope():
    """--strict is the very-deep-check sweep and must never become the gate
    that was withdrawn on 2026-09-21 (practice: very-deep-check).

    The withdrawn version promoted doc_lint's warning classes to gating on
    the CHANGED-FILE scope, and refused a one-line edit over 111 warnings
    that predated it. What keeps the rebuilt flag from drifting back is one
    refusal in main(), and a refusal nothing tests is a refusal somebody
    deletes as dead code.

    Asserts the guard's own words, not just a non-zero exit
    (control-asserts-which-failure): doc_lint has three exit-2 paths and a
    bare returncode check cannot tell them apart.
    And the negative control runs the SAME argv without --strict, so a
    refusal that had become unconditional would show up as the clean case
    going red rather than as two passing tests."""
    script = ROOT / 'tools' / 'doc_lint.py'

    def run(*argv):
        r = subprocess.run([sys.executable, str(script), *argv],
                           cwd=str(ROOT), capture_output=True, text=True,
                           timeout=300)
        return r.returncode, (r.stdout or '') + (r.stderr or '')

    cases = []
    rc, out = run('--strict')
    cases.append(('--strict with no scope is refused, in its own words',
                  rc == 2 and '--strict needs a scope' in out
                  and 'not a gate' in out))
    rc, out = run('--bogus')
    cases.append(('an unknown option is refused rather than ignored',
                  rc == 2 and 'unknown option(s): --bogus' in out))
    # Negative control: the refusal is conditional on --strict. Without it,
    # the same scopeless invocation is the ordinary changed-files gate and
    # must not print the refusal at all.
    rc, out = run()
    cases.append(('the same scopeless run WITHOUT --strict is not refused '
                  '(the guard is conditional, not blanket)',
                  '--strict needs a scope' not in out and rc != 2))

    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        if not passed:
            print(f"  doc_lint --strict did NOT behave as stated: {name}")
    check(f'doc_lint --strict refuses the withdrawn gate scope '
          f'({len(cases)} stated cases)', ok)


def check_build_views_refuses_a_long_index_clause():
    """build_views.py refuses an on-demand index_clause over the limit that
    this repo wrote or changed, and only that one.

    2026-09-26: a clause was extended to 81 characters and build_views
    rendered it silently; only this harness knew the limit, and a push to
    the landing branch does not run it. The writer finds out from the tool it
    runs. Three states: an over-long clause the base already had passes
    (practice sets carry older ones), the same file edited is refused, and
    a consumer, whose practices/ is materialized from other sources, is
    never refused."""
    import tempfile
    n = bv.INDEX_CLAUSE_MAX + 1
    long_clause = 'x' * n

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a],
                              capture_output=True, text=True, env=env)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        git(root, 'init', '-q', '-b', 'main')
        (root / 'practices').mkdir()
        f = root / 'practices' / 'p.md'
        f.write_text(f'---\nindex_clause: "{long_clause}"\n---\n',
                     encoding='utf-8')
        (root / 'precedent.json').write_text('{"base_branch": "main"}\n',
                                             encoding='utf-8')
        # A practice set: a repo that authors the practices it ships.
        (root / 'tools').mkdir()
        (root / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            '{"kind": "source"}', encoding='utf-8')
        git(root, 'add', '-A')
        git(root, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        git(root, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        fm = {'tier': 'on-demand', 'index_clause': long_clause}
        practices = [(fm, {}, f)]
        cases.append(('an over-long clause the base branch already had is '
                      'not refused', bv.over_long_index_clauses(practices, root) == []))
        edited = long_clause + 'y'
        f.write_text(f'---\nindex_clause: "{edited}"\n---\n', encoding='utf-8')
        got = bv.over_long_index_clauses(
            [({'tier': 'on-demand', 'index_clause': edited}, {}, f)], root)
        cases.append((f'the same clause edited is refused, with its length '
                      f'(got {got!r})', got == [(f, n + 1)]))
        # doc_lint asks the same question at the commit the clause is
        # written in (2026-10-02: a practice set's over-long clause was
        # committed and pushed, and refused only at the Debut).
        body = lambda c: (f'---\nslug: p\ntier: on-demand\nindex_clause: "{c}"\n'
                          f'---\n\n## Rule\n\nDo it.\n')
        saved_root = dl.ROOT
        try:
            dl.ROOT = root
            f.write_text(body(long_clause), encoding='utf-8')
            git(root, 'add', '-A')
            git(root, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'b')
            git(root, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
            untouched = dl.check_index_clause('practices/p.md')
            f.write_text(body(edited), encoding='utf-8')
            refused = dl.check_index_clause('practices/p.md')
        finally:
            dl.ROOT = saved_root
        cases.append(('doc_lint, at the commit: an over-long clause the base '
                      'already had passes, the same clause edited is refused '
                      f'with its length (got {untouched!r} / {refused!r})',
                      untouched is None and bool(refused) and str(n + 1) in refused))
        (root / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            '{"kind": "consumer"}', encoding='utf-8')
        cases.append(('a consumer is never refused -- its practices are '
                      'other sources\' to fix',
                      bv.over_long_index_clauses(
                          [({'tier': 'on-demand', 'index_clause': edited}, {}, f)],
                          root) == []))
    failed = [c for c, ok in cases if not ok]
    check(f'build_views refuses a long index_clause the writer just wrote '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))
def check_map_reads_each_tools_own_summary():
    """MAP.md's engine table is read from each tool's own docstring, never
    from a hand-typed table inside the generator (spec/GENERATED_FILES_PLAN.md
    step 1; Morgan, 2026-10-03: generated files are never hand-edited, a
    change goes into their sources). The failures that matter: a tool's row
    that does not follow its file, a new tool missing from the map, and the
    hand table coming back."""
    import importlib.util as _ilu, tempfile, shutil as _shutil
    name = 'MAP.md reads each tool\'s own summary line'
    src = ROOT / 'tools' / 'build_views.py'
    if not src.exists():
        not_applicable(name, 'tools/build_views.py is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tools = pathlib.Path(td) / 'tools'
        tools.mkdir()
        for f in ('build_views.py', 'split_practices.py', 'summary_text.py'):
            _shutil.copy2(ROOT / 'tools' / f, tools / f)
        (tools / 'zz_fixture_tool.py').write_text(
            '"""Says what the fixture tool is, on one line\n\nLonger text.\n"""\n',
            encoding='utf-8')
        spec = _ilu.spec_from_file_location('_bv_summary_fixture', tools / 'build_views.py')
        bv = _ilu.module_from_spec(spec)
        sys.path.insert(0, str(tools))
        try:
            spec.loader.exec_module(bv)
            out = bv.render_map_md([])
            cases.append(('a tool\'s row is the first line of its own docstring',
                          '| [tools/zz_fixture_tool.py](tools/zz_fixture_tool.py) | '
                          'Says what the fixture tool is, on one line |' in out))
            (tools / 'zz_fixture_tool.py').write_text(
                '"""Says something new\n"""\n', encoding='utf-8')
            out = bv.render_map_md([])
            cases.append(('editing the tool\'s docstring changes its row, with '
                          'nothing else to edit', '| Says something new |' in out))
            (tools / 'zz_fixture_tool.py').write_text('x = 1\n', encoding='utf-8')
            try:
                bv.render_map_md([])
                stopped = ''
            except SystemExit as e:
                stopped = str(e)
            cases.append(('a tool with no docstring stops the build, naming the '
                          'file to describe', 'tools/zz_fixture_tool.py' in stopped
                          and 'no module docstring' in stopped))
            cases.append(('the hand-typed table is gone from the generator',
                          not hasattr(bv, 'TOOLS_DESCRIPTIONS')))
            # Only the engine's own repository may call its map Precedent's
            # own; a set's or a consumer's map describes that repository.
            here = pathlib.Path(td) / 'elsewhere'
            (here / 'tools').mkdir(parents=True)
            (here / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}', encoding='utf-8')
            (tools / 'zz_fixture_tool.py').write_text('"""A tool\n"""\n', encoding='utf-8')
            cases.append(('a map outside the engine\'s own repository introduces '
                          'that repository, not Precedent',
                          "Precedent's own repo map" not in bv.render_map_md([], root=here)
                          and "This repository's map" in bv.render_map_md([], root=here)
                          and "Precedent's own repo map" in bv.render_map_md([], root=td)))
        finally:
            sys.path.pop(0)
    real = sorted(p.name for p in (ROOT / 'tools').glob('*.py'))
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as _bv
        undescribed = [n for n in real if not _bv.tool_summary(ROOT / 'tools' / n)]
    finally:
        sys.path.pop(0)
    cases.append(('every tool here has a summary line', not undescribed))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + (f' -- undescribed: {undescribed}' if undescribed else ''))


def check_where_things_are_from_one_source():
    """WHERE_THINGS_ARE.md and AGENTS.md's short table are both generated
    from where_things_are.json (spec/GENERATED_FILES_PLAN.md step 2; Morgan,
    2026-10-03: a copy cites its original or is generated from one source).
    The failures that matter: the two tables disagreeing again, a row
    pointing at a path that does not exist, and a short table out of order
    or missing its pointer to the full page."""
    import json as _json, tempfile
    name = 'WHERE_THINGS_ARE.md and AGENTS.md\'s short table come from one source'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
    finally:
        sys.path.pop(0)
    if not hasattr(bv, 'render_where_things_are'):
        not_applicable(name, 'this engine predates where_things_are.json')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'here.md').write_text('x\n', encoding='utf-8')
        src = {'intro': ['Intro line.'], 'rows': [
            {'looking_for': 'Second quick', 'go_to': '[here.md](here.md)', 'quick': 2},
            {'looking_for': 'Full page only', 'go_to': '[here.md](here.md#a)'},
            {'looking_for': 'First quick', 'go_to': '[out](https://example.com)', 'quick': 1}]}
        (root / bv.WHERE_SOURCE).write_text(_json.dumps(src), encoding='utf-8')
        data = bv._where_source(root)
        page = bv.render_where_things_are(data)
        cases.append(('the full page carries every row, labelled as generated',
                      page.startswith('---\ngenerated_by: tools/build_views.py')
                      and all(f"| {r['looking_for']} |" in page for r in src['rows'])))
        agents = (f'before\n{bv.QUICK_BEGIN}\nstale hand row\n{bv.QUICK_END}\nafter\n')
        out = bv.splice_quick_index(agents, data)
        body = out[out.index(bv.QUICK_BEGIN):out.index(bv.QUICK_END)]
        cases.append(('the short table carries only the quick rows, in their '
                      'order, then the pointer to the full page',
                      'stale hand row' not in body and 'Full page only' not in body
                      and body.index('First quick') < body.index('Second quick')
                      < body.index('Anything else — the full index')
                      and out.startswith('before\n') and out.endswith('after\n')))
        try:
            bv.splice_quick_index('no markers\n', data)
            said = ''
        except SystemExit as e:
            said = str(e)
        cases.append(('a source with nowhere to write the short table stops the '
                      'build and says so', 'markers' in said))
        src['rows'].append({'looking_for': 'Moved away', 'go_to': '[gone](gone/file.md)'})
        (root / bv.WHERE_SOURCE).write_text(_json.dumps(src), encoding='utf-8')
        try:
            bv._where_source(root)
            said = ''
        except SystemExit as e:
            said = str(e)
        cases.append(('a row linking to a path that does not exist stops the '
                      'build, naming the row', 'gone/file.md' in said
                      and 'Moved away' in said))
    real = ROOT / bv.WHERE_SOURCE
    if real.is_file():
        agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        page = (ROOT / bv.WHERE_PAGE).read_text(encoding='utf-8')
        short = agents[agents.index(bv.QUICK_BEGIN):agents.index(bv.QUICK_END)]
        rows = [l for l in short.splitlines() if l.startswith('| ')
                and not l.startswith(('| Looking', '| Anything else'))]
        cases.append(('here, every row of AGENTS.md\'s short table is in the full '
                      'page word for word', rows and all(r in page for r in rows)))
        reg = _json.loads((ROOT / 'tools' / 'generated_files.json').read_text(encoding='utf-8'))
        paths = {(e.get('path'), e.get('part')) for e in reg.get('files', [])}
        cases.append(('both are in the list of generated files',
                      (bv.WHERE_PAGE, None) in paths
                      and ('AGENTS.md', bv.QUICK_BEGIN) in paths))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_commit_rebuilds_generated_files():
    """The commit backstop rebuilds the generated files whose inputs a commit
    touches and stages them (spec/GENERATED_FILES_PLAN.md step 3; Morgan,
    2026-10-03: generated files are auto-updated as their sources change).
    The failures that matter: a stale generated file committed with no one
    noticing; a rebuild that sweeps unstaged work into the commit or
    overwrites it unrecoverably (practice: repair-cannot-discard-work); a
    fixer that blocks a commit; and running what cannot be rebuilt offline."""
    import json as _json, tempfile, shutil as _shutil
    name = 'a commit rebuilds and stages the generated files its sources feed'
    tool = ROOT / 'tools' / 'precedent_regenerate.py'
    hook_src = ROOT / 'tools' / 'commit-identity.sh'
    if not tool.exists() or not hook_src.exists():
        not_applicable(name, 'tools/precedent_regenerate.py or the commit hook is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work = tmp / 'work'
        (work / 'tools').mkdir(parents=True)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), HOME=str(tmp))

        def git(*a):
            return subprocess.run(['git', '-C', str(work), *a],
                                  capture_output=True, text=True, env=env)
        git('init', '-q', '-b', 'main')
        _shutil.copy2(tool, work / 'tools' / 'precedent_regenerate.py')
        # A generator that writes OUT.md from src/*.txt and leaves a mark
        # each time it runs; one that always fails; one that must never run.
        (work / 'tools' / 'gen.py').write_text(
            'import pathlib\n'
            'pathlib.Path("RAN").write_text("x")\n'
            'parts = sorted(pathlib.Path("src").glob("*.txt"))\n'
            'pathlib.Path("OUT.md").write_text("".join(p.read_text() for p in parts))\n',
            encoding='utf-8')
        (work / 'tools' / 'snap.py').write_text(
            'import pathlib\npathlib.Path("SNAP_RAN").write_text("x")\n', encoding='utf-8')
        (work / 'src').mkdir()
        (work / 'src' / 'a.txt').write_text('a\n', encoding='utf-8')
        (work / 'OUT.md').write_text('a\n', encoding='utf-8')
        (work / 'SNAP.md').write_text('snapshot\n', encoding='utf-8')
        (work / 'tools' / 'generated_files.json').write_text(_json.dumps({'files': [
            {'path': 'OUT.md', 'generated_by': 'tools/gen.py', 'edit_instead': 'src/*.txt',
             'regenerate': 'python3 tools/gen.py', 'check': ['tools/gen.py']},
            {'path': 'SNAP.md', 'generated_by': 'tools/snap.py', 'edit_instead': None,
             'regenerate': 'python3 tools/snap.py', 'check': None}]}), encoding='utf-8')
        (work / '.gitignore').write_text('RAN\nSNAP_RAN\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'init')
        # The real hook's fixer block, cut from commit-identity.sh, as this
        # fixture's own pre-commit hook.
        text = hook_src.read_text(encoding='utf-8')
        start = text.index("# The engine's own commit-time fixer")
        end = text.index('esac', start) + len('esac')
        block = text[start:end].replace('\\$', '$')
        hooks = tmp / 'hooks'
        hooks.mkdir()
        (hooks / 'pre-commit').write_text('#!/bin/sh\n' + block + '\nexit 0\n', encoding='utf-8')
        (hooks / 'pre-commit').chmod(0o755)
        git('config', 'core.hooksPath', str(hooks))

        def commit(msg):
            r = git('commit', '-q', '-m', msg)
            return r.returncode, r.stdout + r.stderr

        # 1. A source changes; the generated file is rebuilt and in the commit.
        (work / 'src' / 'b.txt').write_text('b\n', encoding='utf-8')
        git('add', 'src/b.txt')
        rc, out = commit('add a source')
        shown = git('show', 'HEAD:OUT.md').stdout
        cases.append(('a commit touching a source carries the rebuilt generated '
                      'file, and says so', rc == 0 and shown == 'a\nb\n'
                      and 'rebuilt and staged OUT.md' in out))
        # 2. Nothing the generator reads: it does not run.
        (work / 'RAN').unlink()
        (work / 'notes.txt').write_text('n\n', encoding='utf-8')
        git('add', 'notes.txt')
        rc, out = commit('unrelated')
        cases.append(('an unrelated commit runs no generator', rc == 0
                      and not (work / 'RAN').exists()))
        # Its own generator changes, which would make any other entry due.
        (work / 'tools' / 'snap.py').write_text(
            'import pathlib\npathlib.Path("SNAP_RAN").write_text("y")\n', encoding='utf-8')
        git('add', 'tools/snap.py')
        rc, out = commit('touch the snapshot generator')
        cases.append(('an entry nothing offline can rebuild never runs, even when '
                      'its own generator changes', rc == 0
                      and not (work / 'SNAP_RAN').exists()))
        # 3. Unstaged changes of the session's own in the generated file:
        # rebuilt, NOT staged, and said.
        (work / 'OUT.md').write_text('a\nb\nmy unstaged note\n', encoding='utf-8')
        (work / 'src' / 'c.txt').write_text('c\n', encoding='utf-8')
        git('add', 'src/c.txt')
        rc, out = commit('source with unstaged generated edits')
        cases.append(('a generated file with unstaged changes is not swept into '
                      'the commit, and the commit says so',
                      rc == 0 and 'NOT added to this commit' in out
                      and git('show', 'HEAD:OUT.md').stdout == 'a\nb\n'))
        git('checkout', '-q', '--', 'OUT.md')
        # 4. A staged hand edit to the generated file, then a source change:
        # rebuilt and committed, and the hand edit kept, not lost.
        (work / 'OUT.md').write_text('hand edit\n', encoding='utf-8')
        (work / 'src' / 'd.txt').write_text('d\n', encoding='utf-8')
        git('add', 'OUT.md', 'src/d.txt')
        rc, out = commit('hand edit plus source')
        kept = work / '.git' / 'precedent-regenerate' / 'OUT.md'
        cases.append(('a hand edit the rebuild replaces is kept, said, and the '
                      'commit carries the rebuilt file', rc == 0
                      and kept.is_file() and kept.read_text() == 'hand edit\n'
                      and 'is kept at' in out
                      and git('show', 'HEAD:OUT.md').stdout == 'a\nb\nc\nd\n'))
        # 4b. A generated block inside a hand-written document (doc_sync.py's
        # kind) is refreshed when a commit touches what its script reads, and
        # a document with unstaged changes of its own is not swept in.
        (work / 'tools' / 'doc_sync.py').write_text(
            'import pathlib, sys\n'
            'n = len(list(pathlib.Path("src").glob("*.txt")))\n'
            'p = pathlib.Path("BLOCKS.md")\n'
            'new = f"Sources: <!--gen:n-->{n}<!--/gen:n-->\\n" + p.read_text().split("\\n", 1)[1]\n'
            'if "--write" in sys.argv and new != p.read_text():\n'
            '    p.write_text(new); print("[doc_sync] WROTE BLOCKS.md [n]")\n',
            encoding='utf-8')
        (work / 'BLOCKS.md').write_text('Sources: <!--gen:n-->0<!--/gen:n-->\nHand text.\n',
                                        encoding='utf-8')
        git('add', 'tools/doc_sync.py', 'BLOCKS.md')
        git('commit', '-q', '-m', 'a document with a generated block')
        cases.append(('a generated block inside a document is refreshed and committed '
                      'with the change that moved it',
                      git('show', 'HEAD:BLOCKS.md').stdout.startswith(
                          'Sources: <!--gen:n-->4<!--/gen:n-->')))
        (work / 'BLOCKS.md').write_text(
            (work / 'BLOCKS.md').read_text(encoding='utf-8') + 'My unstaged edit.\n',
            encoding='utf-8')
        (work / 'src' / 'f.txt').write_text('f\n', encoding='utf-8')
        (work / 'tools' / 'gen.py').write_text(
            'import pathlib\n'
            'parts = sorted(pathlib.Path("src").glob("*.txt"))\n'
            'pathlib.Path("OUT.md").write_text("".join(p.read_text() for p in parts))\n',
            encoding='utf-8')
        git('add', 'src/f.txt', 'tools/gen.py')
        rc, out = commit('a source, with an unstaged edit in the document')
        cases.append(('...but a document with unstaged changes of its own is not '
                      'swept into the commit, and it says so',
                      rc == 0 and 'Hand text.\n' == git('show', 'HEAD:BLOCKS.md').stdout.split('\n', 1)[1]
                      and 'blocks in BLOCKS.md' in out and 'NOT added' in out))
        git('checkout', '-q', '--', 'BLOCKS.md')
        # 4c. A page tools/doc_html.py renders is re-rendered when its source
        # or the renderer is in the commit, from the renderer's own --list,
        # with no entry in generated_files.json (2026-10-12: a render nothing
        # rebuilt went stale on main and failed unrelated merges).
        (work / 'tools' / 'doc_html.py').write_text(
            'import pathlib, sys\n'
            'if "--list" in sys.argv:\n'
            '    print("  PAGE.md  ->  PAGE.html  (Page)")\n'
            'else:\n'
            '    pathlib.Path("RENDERED").write_text("x")\n'
            '    src = pathlib.Path(sys.argv[1])\n'
            '    src.with_suffix(".html").write_text("<p>" + src.read_text() + "</p>v1")\n',
            encoding='utf-8')
        (work / 'PAGE.md').write_text('one\n', encoding='utf-8')
        (work / 'PAGE.html').write_text('stale', encoding='utf-8')
        (work / '.gitignore').write_text('RAN\nSNAP_RAN\nRENDERED\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'a rendered page')
        (work / 'PAGE.md').write_text('two\n', encoding='utf-8')
        git('add', 'PAGE.md')
        rc, out = commit('the page source changes')
        cases.append(('a page whose source is in the commit is re-rendered into it',
                      rc == 0 and git('show', 'HEAD:PAGE.html').stdout == '<p>two\n</p>v1'
                      and 're-rendered and staged PAGE.html' in out))
        (work / 'RENDERED').unlink()
        (work / 'notes2.txt').write_text('n\n', encoding='utf-8')
        git('add', 'notes2.txt')
        rc, out = commit('nothing the page reads')
        cases.append(('a commit touching neither the page nor the renderer renders '
                      'nothing', rc == 0 and not (work / 'RENDERED').exists()))
        text_r = (work / 'tools' / 'doc_html.py').read_text(encoding='utf-8')
        (work / 'tools' / 'doc_html.py').write_text(text_r.replace('</p>v1', '</p>v2'),
                                                    encoding='utf-8')
        git('add', 'tools/doc_html.py')
        rc, out = commit('the renderer changes')
        cases.append(('a change to the renderer re-renders every page it lists',
                      rc == 0 and git('show', 'HEAD:PAGE.html').stdout == '<p>two\n</p>v2'))
        # 5. A generator that fails never blocks the commit.
        (work / 'tools' / 'gen.py').write_text('raise SystemExit(3)\n', encoding='utf-8')
        (work / 'src' / 'e.txt').write_text('e\n', encoding='utf-8')
        git('add', 'tools/gen.py', 'src/e.txt')
        rc, out = commit('a broken generator')
        cases.append(('a failing generator never blocks the commit, and says '
                      'what failed', rc == 0 and 'failed' in out))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_source_directory_splits_and_assembles():
    """MAP.source.md and GLOSSARY.source.md may live as directories, one
    file per heading and per table row, so two branches that each add a row
    add two files and never conflict (build_views.py, THE SOURCE AS A
    DIRECTORY; Alex, 2026-10-04). What can go wrong is all loss or drift:
    a split that changes a word, a row added between two others that lands
    in the wrong place, a heading inside a code fence taken for a section,
    a repository holding both forms with nobody told, a commit to the
    directory that does not rebuild the view, and a view that stops
    carrying the repository's own text."""
    import tempfile, fnmatch
    import precedent_migrate_views as mv
    name = 'a source directory splits and assembles word for word'
    cases = []
    text = ('# Repository map\n\nIntro line.\n\n'
            '## Layout\n\nWhat lives where.\n\n| Path | What |\n|---|---|\n'
            '| `a/` | first |\n| `b/` | second |\n| `c/` | third |\n\nAfter the table.\n\n'
            '## Notes\n\n```\n## not a heading\n```\n\nPlain.\n')
    entries = mv.split_entries(text)
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / 'MAP.source'
        for rel, content in entries.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(content, encoding='utf-8')
        cases.append(('the split reassembles to the same text, exactly',
                      bv.assemble_source_dir(d) == text.strip('\n')))
        sec = [r for r in entries if r.endswith('/' + bv.SECTION_HEAD)]
        cases.append(('the table section is split into head, rows and tail',
                      len(sec) == 1 and sum(1 for r in entries if r.startswith(
                          sec[0].split('/')[0] + '/')) == 5))
        cases.append(('a heading inside a code fence is not a section',
                      not any('not-a-heading' in r for r in entries)))
        secdir = d / sec[0].split('/')[0]
        (secdir / '0015-ab.md').write_text('| `ab/` | between |\n', encoding='utf-8')
        out = bv.assemble_source_dir(d)
        cases.append(('a row added as 0015- lands between rows 0010- and 0020-',
                      out.index('`a/`') < out.index('`ab/`') < out.index('`b/`')))
        cases.append(('the directory counts as the source',
                      bv.has_own_source(td, 'MAP.source.md')
                      and bv.own_source_label(td, 'MAP.source.md') == 'MAP.source/'))
        (pathlib.Path(td) / 'MAP.source.md').write_text('x\n', encoding='utf-8')
        try:
            bv.own_source_path(td, 'MAP.source.md')
            both = False
        except SystemExit:
            both = True
        cases.append(('holding both the file and the directory is refused', both))
    entry = next(e for e in json.loads((ROOT / 'tools' / 'generated_files.json')
                                       .read_text(encoding='utf-8'))['files']
                 if e.get('path') == 'MAP.md' and not e.get('part'))
    cases.append(('a commit to a row file rebuilds MAP.md',
                  any(fnmatch.fnmatch('MAP.source/0020-layout/0015-ab.md', g)
                      for g in entry['inputs'])))
    # End to end: a repository's one-file source split, then its view rebuilt.
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'practices' / 'zz-fixture.md').write_text(
            '---\nslug:        zz-fixture\ntitle:       A fixture practice\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  ["fixture/**"]\n'
            'occasion:    "fixture"\ngates:       []\nindex_clause: "fixture"\n'
            'checked_by:  null\ndefines:     ["Fixture Term"]\nstatus:      active\n'
            'in_force_at: null\nsupersedes:  []\noverrides:   null\nadded:       "2026-10-04"\n'
            'approved_by: "Fixture, 2026-10-04"\n---\n\n## Rule\nDo it.\n\n## Why\nBecause.\n\n'
            '## Story\nOnce.\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            '# Agents\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        (repo / 'MAP.source.md').write_text(text, encoding='utf-8')
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'), '--repo',
                        str(repo), '--views-only'], capture_output=True, text=True)
        before = (repo / 'MAP.md').read_text(encoding='utf-8') if (repo / 'MAP.md').exists() else ''
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_migrate_views.py'),
                            '--repo', str(repo), '--split'], capture_output=True, text=True)
        after = (repo / 'MAP.md').read_text(encoding='utf-8') if (repo / 'MAP.md').exists() else ''
        strip_label = lambda t: t.split('\n---\n', 1)[-1]
        cases.append(('--split replaces the file with the directory',
                      r.returncode == 0 and (repo / 'MAP.source').is_dir()
                      and not (repo / 'MAP.source.md').exists()))
        cases.append(('...and the rebuilt view carries the same text',
                      bool(before) and strip_label(before) == strip_label(after)
                      and 'Intro line.' in after and '`c/`' in after))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_split_file_round_trips():
    """Any Markdown index of headings and pipe tables can be kept as a
    directory, one file per row, and joined back into the file people read
    (practice: shared-index-is-a-directory; Alex, 2026-10-12, "yes do the
    directory split"). What can go wrong is loss: a split that does not
    rebuild the file byte for byte, a row added between two others that
    lands elsewhere, a join that silently drops a row typed into the view,
    a split of a file that is already generated, a view the generated-files
    list does not name, and row links the light check reads against the
    wrong folder."""
    import tempfile
    import precedent_migrate_views as mv
    import doc_lint
    name = 'any index splits into a directory and joins back byte for byte'
    cases = []
    tool = ROOT / 'tools' / 'precedent_migrate_views.py'
    text = ('# Where things are\n\nIntro, with a [link](docs/a.md).\n\n'
            '| Looking for | Go to |\n|---|---|\n| alpha | [a](docs/a.md) |\n'
            '| beta | b |\n| gamma | c |\n\nAfter the table.\n\n'
            '## Codes\n\n| Code | Means |\n|---|---|\n| AB | one |\n| CD | two |\n')

    def run(repo, *args):
        return subprocess.run([sys.executable, str(tool), '--repo', str(repo), *args],
                              capture_output=True, text=True)
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'generated_files.json').write_text('{"files": []}\n',
                                                             encoding='utf-8')
        (repo / 'docs').mkdir()
        (repo / 'docs' / 'a.md').write_text('# A\n', encoding='utf-8')
        (repo / 'INDEX.md').write_text(text, encoding='utf-8')
        r = run(repo, '--split-file', 'INDEX.md', '--check')
        cases.append(('--check says what it would do and changes nothing',
                      r.returncode == 0 and 'would split' in r.stdout
                      and not (repo / 'INDEX').exists()))
        r = run(repo, '--split-file', 'INDEX.md')
        view = (repo / 'INDEX.md').read_text(encoding='utf-8')
        cases.append(('--split-file moves the text into INDEX/ and keeps INDEX.md '
                      'as a labelled view whose body is the original, byte for byte',
                      r.returncode == 0 and (repo / 'INDEX').is_dir()
                      and 'generated_by: tools/precedent_migrate_views.py' in view
                      and mv.view_body(view) == text))
        rows = sorted(str(p.relative_to(repo / 'INDEX'))
                      for p in (repo / 'INDEX').rglob('*.md'))
        cases.append(('each table row is its own file',
                      sum(1 for x in rows if '/' in x and not x.endswith(
                          ('_head.md', '_tail.md'))) == 5))
        entry = [e for e in json.loads((repo / 'tools' / 'generated_files.json')
                                       .read_text(encoding='utf-8'))['files']
                 if e.get('path') == 'INDEX.md']
        cases.append(('the view is listed with the join as its check',
                      len(entry) == 1 and '--join' in entry[0]['check']
                      and entry[0]['check'][-1] == '--check'))
        cases.append(('--join --check finds the view current',
                      run(repo, '--join', 'INDEX', '--out', 'INDEX.md', '--check')
                      .returncode == 0))
        sec = sorted(p for p in (repo / 'INDEX').iterdir() if p.is_dir())[0]
        first = sorted(x.name for x in sec.iterdir() if x.name[0].isdigit())
        (sec / '0015-new.md').write_text('| alpha-two | new |\n', encoding='utf-8')
        stale = run(repo, '--join', 'INDEX', '--out', 'INDEX.md', '--check')
        cases.append(('a new row file makes --check fail and name the view',
                      stale.returncode == 1 and 'INDEX.md' in stale.stdout))
        r = run(repo, '--join', 'INDEX', '--out', 'INDEX.md')
        out = (repo / 'INDEX.md').read_text(encoding='utf-8')
        cases.append(('a row added as 0015- lands between 0010- and 0020-',
                      r.returncode == 0 and first[:2] == ['0010-alpha.md', '0020-beta.md']
                      and out.index('| alpha |') < out.index('alpha-two')
                      < out.index('| beta |')))
        (repo / 'INDEX.md').write_text(out + '| typed | by hand |\n', encoding='utf-8')
        r = run(repo, '--join', 'INDEX', '--out', 'INDEX.md')
        cases.append(('a row typed into the view is never dropped silently',
                      r.returncode == 1 and 'typed | by hand' in r.stdout
                      and 'typed | by hand' in (repo / 'INDEX.md').read_text(
                          encoding='utf-8')))
        row = sec / '0010-alpha.md'
        cases.append(('a row link is read against the view, not the row folder',
                      doc_lint.index_entry_base(row) == repo
                      and doc_lint.check_broken_links(row) == []))
        (repo / 'COPY.md').write_text(out, encoding='utf-8')
        r = run(repo, '--split-file', 'COPY.md')
        cases.append(('a generated view is never split again',
                      r.returncode == 1 and 'generated already' in r.stdout
                      and not (repo / 'COPY').exists()))
        (repo / 'GAPS.md').write_text(text.replace('\n\n## Codes', '\n\n\n## Codes'),
                                      encoding='utf-8')
        r = run(repo, '--split-file', 'GAPS.md')
        refused = r.returncode == 1 and not (repo / 'GAPS').exists()
        r = run(repo, '--split-file', 'GAPS.md', '--normalize-blank-lines')
        cases.append(('a file differing only in blank lines needs '
                      '--normalize-blank-lines',
                      refused and r.returncode == 0 and (repo / 'GAPS').is_dir()))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_split_and_join_take_edits_made_where_they_belong():
    """Three faults a downstream repo hit on 2026-10-12, the day --split-file
    and --join shipped. (1) Rewording an existing entry file and joining was
    refused as a hand edit to the view, because the guard compared the view
    with the directory as it is now: the source's recent history now counts
    as source, so the old wording passes -- MAP.md's rebuild through
    build_views.py included -- while a line really typed into the view is
    still refused. (2) A row naming
    plan_v1.md was filed as ...-plan-v1.md, a name no-version-suffix then
    refuses. (3) A heading with no blank line above it was called a change
    of words, so --normalize-blank-lines was never offered."""
    import tempfile
    import precedent_migrate_views as mv
    name = 'split and join take edits made in the directory, and only those'
    cases = []
    tool = ROOT / 'tools' / 'precedent_migrate_views.py'

    def run(repo, *args):
        return subprocess.run([sys.executable, str(tool), '--repo', str(repo), *args],
                              capture_output=True, text=True)

    def git(repo, *args):
        return subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c',
                               'user.email=t@t', *args], capture_output=True, text=True)
    text = ('# Index\n\nThe old intro wording.\n\n| Doc | What |\n|---|---|\n'
            '| [plan_v1.md](docs/plan_v1.md) | the plan |\n| [budget-rev3.xlsx](b.xlsx) | money |\n'
            '| alpha | a |\n')
    with tempfile.TemporaryDirectory() as td:
        for committed in (False, True):
            repo = pathlib.Path(td) / f'r{int(committed)}'
            repo.mkdir()
            git(repo, 'init', '-q')
            (repo / 'tools').mkdir()
            (repo / 'tools' / 'generated_files.json').write_text('{"files": []}\n',
                                                                 encoding='utf-8')
            (repo / 'INDEX.md').write_text(text, encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'one file')
            r = run(repo, '--split-file', 'INDEX.md')
            if committed:
                git(repo, 'add', '-A')
                git(repo, 'commit', '-qm', 'split')
            head = next((repo / 'INDEX').rglob('_head.md'))
            head.write_text(head.read_text(encoding='utf-8').replace(
                'The old intro wording.', 'The new intro wording.'), encoding='utf-8')
            if committed:
                git(repo, 'commit', '-qam', 'reword')
            r = run(repo, '--join', 'INDEX', '--out', 'INDEX.md')
            view = (repo / 'INDEX.md').read_text(encoding='utf-8')
            how = 'committed' if committed else 'not yet committed'
            cases.append((f'rewording an entry file ({how}) rebuilds the view',
                          r.returncode == 0 and 'The new intro wording.' in view
                          and 'old intro' not in view, failure_detail(r.stdout, 300)))
        # A real hand edit on top of a directory edit: refused, naming the
        # typed line and not the directory's old text.
        head.write_text(head.read_text(encoding='utf-8').replace(
            'The new intro wording.', 'A third wording.'), encoding='utf-8')
        (repo / 'INDEX.md').write_text(view.replace('| alpha | a |', '| alpha | typed by hand |'),
                                       encoding='utf-8')
        r = run(repo, '--join', 'INDEX', '--out', 'INDEX.md')
        cases.append(('a line typed into the view is still refused, and named',
                      r.returncode == 1 and 'typed by hand' in r.stdout
                      and 'new intro wording' not in r.stdout
                      and 'typed by hand' in (repo / 'INDEX.md').read_text(encoding='utf-8'),
                      failure_detail(r.stdout, 300)))
        # Old wording git never saw cannot be told from a typed line: the
        # refusal names it and says --force is safe for it.
        fresh = pathlib.Path(td) / 'fresh'
        fresh.mkdir()
        git(fresh, 'init', '-q')
        (fresh / 'INDEX.md').write_text(text, encoding='utf-8')
        run(fresh, '--split-file', 'INDEX.md')
        fhead = next((fresh / 'INDEX').rglob('_head.md'))
        fhead.write_text(fhead.read_text(encoding='utf-8').replace('old intro', 'new intro'),
                         encoding='utf-8')
        r = run(fresh, '--join', 'INDEX', '--out', 'INDEX.md')
        cases.append(('old wording never committed is named, with --force said to be safe',
                      r.returncode == 1 and 'old intro' in r.stdout
                      and '--force is safe' in r.stdout, failure_detail(r.stdout, 400)))
        names = sorted(p.name for p in (repo / 'INDEX').rglob('*.md'))
        cases.append(('a row naming plan_v1.md gets no version suffix in its file name',
                      not any(re.search(r'-(?:v\d+|rev\d+)(?:-[a-z]+)?\.md$', n) for n in names)
                      and any(n.endswith('-plan.md') for n in names)
                      and any(n.endswith('-budget.md') for n in names), ', '.join(names)))
        # (3) a heading straight under a paragraph line.
        tight = '# T\n\nSome prose.\n### Next\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n'
        (repo / 'TIGHT.md').write_text(tight, encoding='utf-8')
        r = run(repo, '--split-file', 'TIGHT.md')
        offered = r.returncode == 1 and '--normalize-blank-lines' in r.stdout
        r = run(repo, '--split-file', 'TIGHT.md', '--normalize-blank-lines')
        cases.append(('a heading with no blank line above it is a blank-line '
                      'difference --normalize-blank-lines accepts',
                      offered and r.returncode == 0 and (repo / 'TIGHT').is_dir(),
                      failure_detail(r.stdout, 300)))
        cases.append(('a real change of words is still not the same words',
                      not mv._same_words('Some prose.\n\n### Next', 'Some prose.\n\n### Other')
                      and mv._same_words('Some prose.\n### Next', 'Some prose.\n\n### Next'),
                      ''))
        # MAP.md through build_views.py: a committed reword of a MAP.source/
        # row rebuilds the map; a row typed into MAP.md is still refused.
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'practices' / 'zz-fixture.md').write_text(
            '---\nslug:        zz-fixture\ntitle:       A fixture practice\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  ["fixture/**"]\n'
            'occasion:    "fixture"\ngates:       []\nindex_clause: "fixture"\n'
            'checked_by:  null\ndefines:     ["Fixture Term"]\nstatus:      active\n'
            'in_force_at: null\nsupersedes:  []\noverrides:   null\nadded:       "2026-10-12"\n'
            'approved_by: "Fixture, 2026-10-12"\n---\n\n## Rule\nDo it.\n\n## Why\nBecause.\n\n'
            '## Story\nOnce.\n', encoding='utf-8')
        (repo / 'MAP.source' / '0010-layout').mkdir(parents=True)
        (repo / 'MAP.source' / '0010-layout' / '_head.md').write_text(
            '## Layout\n\n| Path | What |\n|---|---|\n', encoding='utf-8')
        row = repo / 'MAP.source' / '0010-layout' / '0010-a.md'
        row.write_text('| `a/` | the first wording |\n', encoding='utf-8')
        (repo / 'MAP.source' / '0010-layout' / '0020-b.md').write_text(
            '| `b/` | bee |\n', encoding='utf-8')
        bvs = lambda: subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                                      '--repo', str(repo), '--views-only'],
                                     capture_output=True, text=True)
        git(repo, 'init', '-q')
        bvs()
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'map')
        row.write_text('| `a/` | the second wording |\n', encoding='utf-8')
        git(repo, 'commit', '-qam', 'reword a row')
        r = bvs()
        cases.append(('a committed reword of a MAP.source/ row rebuilds MAP.md',
                      r.returncode == 0 and 'second wording' in
                      (repo / 'MAP.md').read_text(encoding='utf-8'), failure_detail(r.stdout + r.stderr, 300)))
        m = (repo / 'MAP.md').read_text(encoding='utf-8')
        (repo / 'MAP.md').write_text(m.replace('| `b/` | bee |', '| `b/` | bee, typed here |'),
                                     encoding='utf-8')
        r = bvs()
        cases.append(('a row typed into MAP.md is still refused',
                      r.returncode == 1 and 'typed here' in r.stderr, failure_detail(r.stdout + r.stderr, 300)))
    failed = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(f'{n} -- {d}' for n, d in failed))


def check_migrate_views_keeps_every_word():
    """precedent_migrate_views.py moves a hand-written MAP.md and GLOSSARY.md
    into MAP.source.md and GLOSSARY.source.md and generates both from then
    on (spec/GENERATED_FILES_PLAN.md step 5; Morgan, 2026-10-03). The
    failures that matter are all losses: a word of the repository's own text
    missing after regeneration, a failed migration that leaves things half
    changed (practice: repair-cannot-discard-work), a view a vendor update
    already overwrote that cannot be brought back, and a second run that
    disturbs a migrated repository."""
    import tempfile, json as _json
    name = 'migrating the views keeps every word a repository wrote'
    tool = ROOT / 'tools' / 'precedent_migrate_views.py'
    if not tool.exists():
        not_applicable(name, 'tools/precedent_migrate_views.py is absent')
        return
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'practices').mkdir(parents=True)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(pathlib.Path(td) / 'gitconfig'),
                   PRECEDENT_USER_CONFIG=str(pathlib.Path(td) / 'none.json'))

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)

        def migrate(*a):
            r = subprocess.run([sys.executable, str(tool), '--repo', str(repo), *a],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr
        (repo / 'practices' / 'zz-fixture.md').write_text(
            '---\nslug:        zz-fixture\ntitle:       A fixture practice\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  ["fixture/**"]\n'
            'occasion:    "fixture"\ngates:       []\nindex_clause: "fixture"\n'
            'checked_by:  null\ndefines:     ["Fixture Term"]\nstatus:      active\n'
            'in_force_at: null\nsupersedes:  []\noverrides:   null\nadded:       "2026-10-03"\n'
            'approved_by: "Fixture, 2026-10-03"\n---\n\n## Rule\nDo it.\n\n## Why\nBecause.\n\n'
            '## Story\nOnce.\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            '# Agents\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        hand_map = ('<!-- Last updated: 2026-09-30 by Someone, to version 7 -->\n'
                    '# Repository map\n\nOur one deliverable is [THE_THING.md](THE_THING.md).\n\n'
                    '## Known consumers\n\n| Repo | Since |\n|---|---|\n| a/b | 2026-09-01 |\n')
        hand_glossary = '# Canonical names\n\n## Our names\n\n| Name | Meaning |\n|---|---|\n| HVR | Human voice rules |\n'
        (repo / 'MAP.md').write_text(hand_map, encoding='utf-8')
        (repo / 'GLOSSARY.md').write_text(hand_glossary, encoding='utf-8')
        (repo / 'todo').mkdir()
        (repo / 'todo' / 'TODO.md').write_text(
            '---\ngenerated_by: tools/build_todo_index.py\nedit_instead: "todo/todo-*.md"\n'
            'note: "Generated."\n---\n# TODO\n', encoding='utf-8')
        (repo / 'process' / 'upstream').mkdir(parents=True)
        (repo / 'process' / 'upstream' / 'GLOSSARY.md').write_text(
            '---\ngenerated_by: tools/build_views.py\nedit_instead: "x"\n---\n# Upstream\n',
            encoding='utf-8')
        agents_before = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        git('init', '-q', '-b', 'main')
        git('add', '-A')
        git('commit', '-q', '-m', 'hand-written views')
        first = git('rev-parse', 'HEAD').stdout.strip()

        rc, out = migrate('--check')
        cases.append(('--check says what it would do and changes nothing',
                      rc == 0 and 'would move MAP.md into MAP.source.md' in out
                      and not (repo / 'MAP.source.md').exists()
                      and (repo / 'MAP.md').read_text(encoding='utf-8') == hand_map))
        rc, out = migrate()
        m = (repo / 'MAP.md').read_text(encoding='utf-8')
        g = (repo / 'GLOSSARY.md').read_text(encoding='utf-8')
        cases.append(('each hand-written view moves into its source byte for byte',
                      rc == 0 and (repo / 'MAP.source.md').read_text(encoding='utf-8') == hand_map
                      and (repo / 'GLOSSARY.source.md').read_text(encoding='utf-8') == hand_glossary))
        cases.append(('...and the generated map carries every word of it, then the '
                      'catalogue, labelled as generated from the source',
                      m.startswith('---\ngenerated_by: tools/build_views.py')
                      and 'MAP.source.md' in m.split('---', 2)[1]
                      and hand_map.rstrip('\n') in m
                      and m.index(hand_map.rstrip('\n')) < m.index('## The practice catalogue')
                      and '[zz-fixture](practices/zz-fixture.md)' in m))
        cases.append(('...and the generated glossary carries its own names, then '
                      'the names the practices define',
                      hand_glossary.rstrip('\n') in g and '| Fixture Term |' in g))
        reg = _json.loads((repo / 'tools' / 'generated_files.json').read_text(encoding='utf-8'))
        cases.append(('...and both are in the repository\'s own list, with their '
                      'sources as inputs, beside every other file that says it is '
                      'generated, read from its own label -- never a vendored copy of '
                      'another repository\'s',
                      {e['path']: e['edit_instead'] for e in reg['files']}
                      == {'MAP.md': 'MAP.source.md', 'GLOSSARY.md': 'GLOSSARY.source.md',
                          'todo/TODO.md': 'todo/todo-*.md'}))
        cases.append(('...and AGENTS.md is never touched: its loader block is the '
                      'view sync\'s to write',
                      (repo / 'AGENTS.md').read_text(encoding='utf-8') == agents_before))
        before = m
        rc, out = migrate()
        cases.append(('a second run finds nothing to do and changes nothing',
                      rc == 0 and 'nothing to migrate' in out
                      and (repo / 'MAP.md').read_text(encoding='utf-8') == before))
        (repo / 'MAP.source.md').write_text(hand_map + '\nA new line.\n', encoding='utf-8')
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                        '--repo', str(repo)], capture_output=True, text=True, env=env)
        cases.append(('afterwards the map follows its source',
                      'A new line.' in (repo / 'MAP.md').read_text(encoding='utf-8')))

        # A view a vendor update already overwrote: brought back from the
        # commit the person names.
        git('add', '-A')
        git('commit', '-q', '-m', 'migrated')
        (repo / 'MAP.source.md').unlink()
        git('commit', '-q', '-am', 'lose the source, as an overwrite did')
        rc, out = migrate('--restore-map-from', first)
        cases.append(('--restore-map-from brings back the hand-written map from '
                      'the named commit', rc == 0
                      and (repo / 'MAP.source.md').read_text(encoding='utf-8') == hand_map))
        rc, out = migrate('--restore-map-from', 'HEAD')
        cases.append(('...never restores over a source that already exists',
                      rc != 0 and 'already exists' in out
                      and (repo / 'MAP.source.md').read_text(encoding='utf-8') == hand_map))
        (repo / 'MAP.source.md').unlink()
        rc, out = migrate('--restore-map-from', 'HEAD')
        cases.append(('...and refuses a commit where the map was already generated',
                      rc != 0 and 'already generated' in out
                      and not (repo / 'MAP.source.md').exists()))

        # A migration that cannot keep the text leaves nothing changed.
        (repo / 'MAP.source.md').unlink(missing_ok=True)
        (repo / 'GLOSSARY.source.md').unlink(missing_ok=True)
        (repo / 'MAP.md').write_text(hand_map, encoding='utf-8')
        (repo / 'GLOSSARY.md').write_text(hand_glossary, encoding='utf-8')
        (repo / 'AGENTS.md').write_text('# Agents, with no loader markers\n', encoding='utf-8')
        rc, out = migrate()
        cases.append(('a migration that cannot regenerate puts everything back and '
                      'says so', rc == 1 and 'REFUSED' in out
                      and not (repo / 'MAP.source.md').exists()
                      and not (repo / 'GLOSSARY.source.md').exists()
                      and (repo / 'MAP.md').read_text(encoding='utf-8') == hand_map
                      and (repo / 'GLOSSARY.md').read_text(encoding='utf-8') == hand_glossary))

        # Views a vendor update already overwrote, with no source file and no
        # list: nothing to migrate, but the list is still written, or a commit
        # that adds a source never rebuilds the view. Found 2026-10-03 in a
        # real consumer whose map and glossary were overwritten on 2026-09-15.
        (repo / 'AGENTS.md').write_text(agents_before, encoding='utf-8')
        (repo / 'MAP.md').write_text(
            '---\ngenerated_by: tools/build_views.py\nedit_instead: "practices/*.md"\n'
            '---\n# Repository map\n', encoding='utf-8')
        (repo / 'GLOSSARY.md').write_text(
            '---\ngenerated_by: tools/build_views.py\nedit_instead: "practices/*.md"\n'
            '---\n# Canonical names\n', encoding='utf-8')
        (repo / 'tools' / 'generated_files.json').unlink(missing_ok=True)
        # ...but their history holds the hand-written views, with a heading
        # and a row the overwrite took. An empty source would make that loss
        # permanent, which is what happened to that consumer on 2026-10-05.
        rc, out = migrate()
        cases.append(('views already generated whose history holds hand-written '
                      'ones with entries they lost: refused, naming the commit to '
                      'restore from, with nothing written',
                      rc == 1 and 'REFUSED' in out and f'--restore-from {first}' in out
                      and not (repo / 'MAP.source.md').exists()
                      and not (repo / 'GLOSSARY.source.md').exists()))
        rc, out = migrate('--find-lost')
        cases.append(('--find-lost names each lost heading and row, and changes nothing',
                      rc == 1 and '## Known consumers' in out and '| a/b |' in out
                      and '| HVR |' in out and not (repo / 'MAP.source.md').exists()))
        rc, out = migrate('--accept-loss')
        lst = repo / 'tools' / 'generated_files.json'
        listed = ({e['path']: e.get('edit_instead') for e in
                   _json.loads(lst.read_text(encoding='utf-8'))['files']}
                  if lst.is_file() else {})
        cases.append(('with --accept-loss, views already generated, with no source '
                      'and no list: each gets an empty source, as a fresh install '
                      'would, and the list names both',
                      rc == 0 and 'nothing to migrate' in out
                      and listed.get('MAP.md') == 'MAP.source.md'
                      and listed.get('GLOSSARY.md') == 'GLOSSARY.source.md'
                      and (repo / 'MAP.source.md').is_file()
                      and (repo / 'MAP.source.md').read_text(encoding='utf-8') == ''
                      and (repo / 'GLOSSARY.source.md').is_file()
                      and (repo / 'GLOSSARY.source.md').read_text(encoding='utf-8') == ''))
        cases.append(('...and each view now names its source, with AGENTS.md untouched',
                      'MAP.source.md' in (repo / 'MAP.md').read_text(encoding='utf-8')
                      .split('---', 2)[1]
                      and 'GLOSSARY.source.md' in (repo / 'GLOSSARY.md')
                      .read_text(encoding='utf-8').split('---', 2)[1]
                      and (repo / 'AGENTS.md').read_text(encoding='utf-8') == agents_before))
        rc, out = migrate('--restore-from', first)
        cases.append(('--restore-from fills both empty sources from the named commit, '
                      'and nothing is lost afterwards',
                      rc == 0
                      and (repo / 'MAP.source.md').read_text(encoding='utf-8') == hand_map
                      and (repo / 'GLOSSARY.source.md').read_text(encoding='utf-8')
                      == hand_glossary
                      and migrate('--find-lost')[0] == 0))

        # A hand-written map and no glossary at all: the migration makes no
        # glossary, and the list names nothing that is not there. Found
        # 2026-10-03 in a consumer whose glossary lives in docs/: it came out
        # with a new root GLOSSARY.md and a list pointing at a missing
        # GLOSSARY.source.md, which generated-files-registered refused.
        for f in ('MAP.source.md', 'GLOSSARY.source.md', 'GLOSSARY.md'):
            (repo / f).unlink(missing_ok=True)
        (repo / 'tools' / 'generated_files.json').unlink(missing_ok=True)
        (repo / 'MAP.md').write_text(hand_map, encoding='utf-8')
        rc, out = migrate()
        listed = ({e['path']: e.get('edit_instead') for e in
                   _json.loads(lst.read_text(encoding='utf-8'))['files']}
                  if lst.is_file() else {})
        cases.append(('a repository with no glossary gets none, and its list names '
                      'only the map and its real source',
                      rc == 0 and not (repo / 'GLOSSARY.md').exists()
                      and not (repo / 'GLOSSARY.source.md').exists()
                      and listed.get('MAP.md') == 'MAP.source.md'
                      and 'GLOSSARY.md' not in listed))
        # ...and no later rebuild makes one either: the commit backstop runs
        # build_views --views-only whenever MAP.source.md changes, and it
        # wrote a root GLOSSARY.md each time, untracked, in that consumer.
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                        '--repo', str(repo), '--views-only'],
                       capture_output=True, text=True, env=env)
        cases.append(('...and a later views-only rebuild does not create one either',
                      not (repo / 'GLOSSARY.md').exists()
                      and (repo / 'MAP.md').is_file()))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_stale_view_names_its_real_cause():
    """The view sync's check names why a generated MAP.md or GLOSSARY.md is
    stale, and only the view that is. build_views.py prints the drift on
    stdout and, for a person who brings a set, a notice on stderr after it;
    the sync quoted the last line of both together, so a hand edit to MAP.md
    was reported as the brought-set notice, against both views. Found
    2026-10-03 rehearsing a consumer's push check after Update Vendors."""
    import tempfile
    name = 'a stale generated view is reported with its own cause, and only that view'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_sync_views as sv
    finally:
        sys.path.pop(0)
    if not hasattr(sv, '_refresh_generated_views'):
        not_applicable(name, 'precedent_sync_views has no _refresh_generated_views')
        return
    header = '---\ngenerated_by: tools/build_views.py\nedit_instead: "x"\n---\n# View\n'
    real_run = sv.subprocess.run
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'MAP.md').write_text(header, encoding='utf-8')
        (repo / 'GLOSSARY.md').write_text(header, encoding='utf-8')
        sv.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(
            a[0] if a else [], 1,
            stdout='build_views --check FAIL: hand-edited or stale, drifted from '
                   'regeneration: MAP.md\n',
            stderr='build_views: acme-shared-ladder deferred to '
                   '.precedent/SESSION_PRACTICES.md -- brought by the person working '
                   'here, not declared by this repository.\n')
        try:
            got = ' '.join(sv._refresh_generated_views(repo, check=True))
        finally:
            sv.subprocess.run = real_run
    check(name, 'hand-edited or stale' in got and 'MAP.md' in got
          and 'deferred' not in got and 'GLOSSARY.md' not in got, got)


def check_tracked_views_read_the_same_whoever_regenerates():
    """The standing instruction in a tracked AGENTS.md points at
    .precedent/SESSION_PRACTICES.md only when a source THIS REPOSITORY
    declares is deferred there, never because the person regenerating it
    brings a set of their own. Found 2026-10-03 on a real consumer's copy:
    counting a brought set wrote the pointer for whoever brings one, so
    build_views.py and the view sync disagreed and the repository's full
    check failed for every such person after an engine update."""
    name = 'a tracked view reads the same whoever regenerates it'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_views as bv
    finally:
        sys.path.pop(0)
    import tempfile
    cases = []
    real = bv.sources_for_tracked_block
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'precedent.json').write_text('{"sources": []}', encoding='utf-8')
        try:
            bv.sources_for_tracked_block = lambda r, d: (
                [], [{'name': 'acme-shared-ladder', 'brought': True}], [])
            only_brought = bv.defers_any_source(root)
            bv.sources_for_tracked_block = lambda r, d: (
                [], [{'name': 'acme-shared-ladder', 'brought': True},
                     {'name': 'acme-shared-writing'}], [])
            declared_too = bv.defers_any_source(root)
        finally:
            bv.sources_for_tracked_block = real
    cases.append(('a set only the person brings does not put the pointer in a '
                  'tracked file', only_brought is False))
    cases.append(('...while a source the repository declares and defers still does',
                  declared_too is True))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_stale_views_say_why_and_stop_at_the_push():
    """A repository's generated views going stale because a practice source
    changed is said with its cause and its command, and stops the push to
    the landing branch, not only the Debut (2026-10-03: a reduction pass retired
    practices in the shared sets, a consumer was never re-synced, and the
    full check's message sent its session after missing sources). The
    failures that matter: a stale view that passes the basic tier, a message
    that does not name the cause, and a check that fails a push only because
    a source is not cloned here."""
    import tempfile, json as _json
    name = 'stale generated views say why, and stop at the push'
    tool = ROOT / 'tools' / 'precedent_sync_views.py'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        universal, consumer = tmp / 'u', tmp / 'consumer'
        (universal / 'practices').mkdir(parents=True)
        def practice(slug, rule):
            (universal / 'practices' / f'{slug}.md').write_text(
                f'---\nslug: {slug}\ntitle: Fixture\ntier: resident\nseverity: default\n'
                f'applies_to: ["**"]\noccasion: "x"\ngates: []\nindex_clause: "x"\n'
                f'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
                f'overrides: null\nadded: null\napproved_by: "x"\nsource_practice_number: null\n'
                f'---\n## Rule\n{rule}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
                encoding='utf-8')
        practice('uni-fixture', 'A universal fixture rule.')
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(_json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(universal)}]}),
            encoding='utf-8')
        (consumer / 'AGENTS.md').write_text('# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                                            '<!-- END GENERATED -->\n', encoding='utf-8')
        user_cfg = tmp / 'none.json'

        def run(*extra):
            r = subprocess.run([sys.executable, str(tool), '--repo', str(consumer),
                                '--user-config', str(user_cfg), *extra],
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr
        run()
        rc, out = run('--check')
        cases.append(('right after a sync, the check passes', rc == 0))
        practice('uni-fixture', 'The same rule, reworded upstream.')
        rc, out = run('--check')
        cases.append(('a source that changed since the sync fails the check, naming '
                      'the cause and the command',
                      rc != 0 and 'practice source this repository declares changed' in out
                      and 'Fix: python3 tools/precedent_sync_views.py --repo .' in out))
        import shutil as _shutil
        _shutil.rmtree(universal)
        rc, out = run('--check', '--skip-unresolved')
        cases.append(('...while a source that is not here at all is said and skipped '
                      'when asked, never read as stale views',
                      rc == 0 and 'SKIPPED' in out and 'could not be resolved' in out))
        rc, out = run('--check')
        cases.append(('...and without --skip-unresolved it still fails, saying first '
                      'that a source is missing, so the differences are not read as '
                      'stale views', rc != 0 and 'did not resolve here' in out))
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_push_check as _ppc
    finally:
        sys.path.pop(0)
    step = [s for s in _ppc.PUSH_CHECKS['consumer'] if s[0] == 'views_sync']
    cases.append(('a repository that uses Precedent runs the check at the basic '
                  'tier, skipping sources it cannot reach',
                  'views_sync' in _ppc.BASIC_CHECKS and step
                  and '--skip-unresolved' in step[0][1]))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_generated_views_regenerate():
    # "hand-editing a generated view fails a check" (Sequence row 2, done-when).
    # Runs build_views.py --check as a real subprocess, not an in-process
    # import-and-call: bv.build_loader_block() can sys.exit() (over the
    # resident token budget, or missing BEGIN/END markers), which is a clean
    # process exit but would be an uncaught SystemExit escaping straight
    # through this function if called in-process, taking the whole harness
    # down with a raw traceback instead of a reported FAIL line.
    result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'), '--check'],
                             capture_output=True, text=True)
    name = 'generated views regenerate byte-identically (AGENTS.md loader block, MAP.md, GLOSSARY.md)'
    said = result.stdout + result.stderr
    # build_views.py exits 0 when a source the block was built from is not
    # here: that is not a pass, so it is said (2026-10-09).
    if result.returncode == 0 and 'NOT VERIFIABLE' in said:
        not_applicable(name, next(l for l in said.splitlines()
                                  if 'NOT VERIFIABLE' in l).strip())
        return
    ok = result.returncode == 0
    check(name, ok, said.strip() if not ok else '')


def check_resident_rule_links_are_placed_for_the_block():
    """A resident practice's Rule links are repointed for the file the block
    lands in, and an unplaceable one is said out loud instead of mangled.

    THE INCIDENT (2026-09-11). A `tier: resident` practice's ## Rule is
    copied verbatim into the loader block, which lands in AGENTS.md at the
    repository ROOT -- while the Rule was written in practices/, one
    directory down. An individual set's new practice carried the only link
    in the whole resident block, `[audience-register](audience-register.md)`,
    and it reached a consuming repo as a hard doc_lint BROKEN RELATIVE LINK
    inside a generated region no session there is allowed to edit. It was
    patched at the source by dropping the markup, which holds by convention
    only.

    Four behaviours, and the last two are the ones that keep the fix from
    being worse than the bug: a link that cannot be placed is LEFT as its
    author wrote it, never turned into an absolute URL that would name a
    private repository, and never into a machine-specific path out of the
    tree (practice: control-asserts-which-failure -- each case asserts the
    text produced, not merely that something happened)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rulelinks-'))
    cases = []
    try:
        repo = tmp / 'repo'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'tools' / 'checks').mkdir(parents=True)
        (repo / 'tools' / 'checks' / 'check_x.py').write_text('x\n', encoding='utf-8')
        (repo / 'practices' / 'sibling.md').write_text('y\n', encoding='utf-8')
        rule = ("See [a](sibling.md), [b](../tools/checks/check_x.py), "
                "[c](https://example.com/x), [d](#rule) and [e](gone.md).")
        placed, unplaced = bv._place_rule_links(
            rule, repo / 'practices' / 'p.md', repo)
        cases.append(('a sibling practice citation is repointed at '
                      'practices/ for a block rendered at the repo root',
                      '[a](practices/sibling.md)' in placed))
        cases.append(("a practice's own check script is repointed at "
                      'tools/checks/, and an absolute URL and a bare '
                      'fragment are untouched',
                      '[b](tools/checks/check_x.py)' in placed
                      and '[c](https://example.com/x)' in placed
                      and '[d](#rule)' in placed))
        cases.append(('a link to a file that is not there is left exactly as '
                      'written, and reported as unplaceable',
                      '[e](gone.md)' in placed and unplaced == ['gone.md']))

        # A Rule that SHOWS a reader what a link looks like is exactly the
        # practice that would carry one, and rewriting it would edit the
        # prose this file only relays. doc_lint skips both regions for the
        # same reason.
        literal = ("Prose [a](sibling.md), a span `[b](sibling.md)`, and\n"
                   "```\n[c](sibling.md)\n```\nthen [d](sibling.md).")
        placed_lit, _ = bv._place_rule_links(
            literal, repo / 'practices' / 'p.md', repo)
        cases.append(('a link inside a code span or a fenced block is left '
                      'alone, while the prose links around it are placed',
                      placed_lit.count('(practices/sibling.md)') == 2
                      and '`[b](sibling.md)`' in placed_lit
                      and '\n[c](sibling.md)\n' in placed_lit))

        # Rendered one directory DOWN (.precedent/SESSION_PRACTICES.md), a
        # link out of practices/ legitimately climbs -- so "starts with .."
        # is not the test, and this is the case that proves it is not.
        placed_down, _ = bv._place_rule_links(
            rule, repo / 'practices' / 'p.md', repo / '.precedent', repo)
        cases.append(('a block rendered below the repo root gets ../ links, '
                      'not a refusal',
                      '[a](../practices/sibling.md)' in placed_down
                      and '[b](../tools/checks/check_x.py)' in placed_down))

        # THE PRIVACY CASE. A team or individual practice resolves from a
        # clone outside the consuming repo, where no relative link reaches.
        outside = tmp / 'precedent-individual'
        (outside / 'practices').mkdir(parents=True)
        (outside / 'practices' / 'sibling.md').write_text('y\n', encoding='utf-8')
        placed_out, unplaced_out = bv._place_rule_links(
            "See [a](sibling.md).", outside / 'practices' / 'p.md',
            repo / '.precedent', repo)
        cases.append(('a practice resolved from a source clone OUTSIDE the '
                      'repo is left as written -- no absolute URL naming the '
                      'source, no path out of the tree',
                      placed_out == "See [a](sibling.md)."
                      and unplaced_out == ['sibling.md']
                      and str(outside) not in placed_out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        if not passed:
            print(f"  build_views did NOT place a resident Rule's links as "
                  f"stated: {name}")
    check(f"a resident Rule's relative links are placed for the block's own "
          f"directory ({len(cases)} stated cases, including the two "
          f"unplaceable shapes)", ok)


def check_build_views_summary_matches_what_it_wrote():
    """build_views.py's summary line reports the block it actually wrote.

    THE INCIDENT (2026-09-07). The summary re-derived its figures with a
    second build_loader_block() call, from the single-source catalogue,
    while the block itself had been built from the multi-source resolve. A
    run printed "resident 7/69 practices" and wrote a file whose own header
    said "7 of 72" -- the artifact was right and the line a session reads to
    confirm the run was wrong, which is the worse half to have wrong. It
    surfaced only because a merge happened to add repo-local practices and
    somebody read both numbers in the same minute.

    Runs against a COPY: this is a real write run, not --check, because the
    disagreement lived between what was printed and what was written and
    only a write produces both.
    """
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-summary-'))
    try:
        repo = tmp / 'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', 'prompts'))
        r = subprocess.run(
            [sys.executable, str(repo / 'tools' / 'build_views.py')],
            capture_output=True, text=True, cwd=str(repo))
        if r.returncode != 0:
            check('build_views summary reports the block it wrote', False,
                  f'build_views exited {r.returncode}: '
                  f'{(r.stdout + r.stderr).strip()[:300]}')
            return
        m_out = re.search(r'resident (\d+)/(\d+) practices, ~(\d+) tokens',
                          r.stdout)
        header = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        m_file = re.search(
            r'## Resident block \(~(\d+) of \d+ token budget, '
            r'(\d+) of (\d+) practices', header)
        if not m_out or not m_file:
            check('build_views summary reports the block it wrote', False,
                  f'could not parse both figures (stdout matched: '
                  f'{bool(m_out)}, AGENTS.md matched: {bool(m_file)})')
            return
        printed = (int(m_out.group(1)), int(m_out.group(2)), int(m_out.group(3)))
        written = (int(m_file.group(2)), int(m_file.group(3)), int(m_file.group(1)))
        check('build_views summary reports the block it wrote '
              '(resident, total and token count all match AGENTS.md)',
              printed == written,
              f'printed {printed}, wrote {written}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_new_rule_shows_its_debt_and_booked_names_it():
    """When a sync brings in an enforced practice, or changes one, its check
    runs once across the repository and what does not hold yet is listed --
    a note, never a refusal; and at Booked, --changed-files-only names the
    findings it set aside by check and file, not just a count (2026-10-07:
    a one-file note was refused four times over files it never touched)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_sync_views as _sv
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / 'practices').mkdir()
        (d / 'practices' / 'dated-names.md').write_text(
            '---\nchecked_by: check_dated_names.py\n---\n## Rule\nDate at end.\n'
            '## Why\nx\n', encoding='utf-8')
        (d / 'practices' / 'prose.md').write_text(
            '---\nchecked_by: null\n---\n## Rule\nx\n', encoding='utf-8')
        out = ('VIOLATION  dated-names\n    content/sources/book.epub: no date\n'
               '  the rule:\n    Date at end.\n')
        ran = []

        def fake(slug):
            ran.append(slug)
            return out
        lines = _sv.standing_findings_of_arrivals(d, {}, run=fake)
        cases.append(('a newly arrived enforced practice is checked, and its '
                      'finding named', ran == ['dated-names'] and lines
                      and 'content/sources/book.epub' in lines[0]))
        cases.append(('...as a note that refuses nothing',
                      bool(lines) and 'Nothing is refused' in lines[0]))
        ran.clear()
        cases.append(('an unchanged practice is not re-checked',
                      _sv.standing_findings_of_arrivals(
                          d, _sv._checked_rules(d), run=fake) == [] and not ran))
        before = _sv._checked_rules(d)
        (d / 'practices' / 'dated-names.md').write_text(
            '---\nchecked_by: check_dated_names.py\n---\n## Rule\nDate last.\n'
            '## Why\nx\n', encoding='utf-8')
        cases.append(('a changed Rule is checked again',
                      bool(_sv.standing_findings_of_arrivals(d, before, run=fake))))
    src = (ROOT / 'tools' / 'precedent_sync_views.py').read_text(encoding='utf-8')
    cases.append(('the sync prints it after writing',
                  'standing_findings_of_arrivals(repo, rules_before)' in src))
    pc = (ROOT / 'tools' / 'precedent_check.py').read_text(encoding='utf-8')
    cases.append(('Booked names what it set aside, by check and file',
                  "set_aside.setdefault(slug, []).append(" in pc
                  and "for slug_, files in sorted(set_aside.items()):" in pc))
    bad = [n for n, ok in cases if not ok]
    check(f'a new rule shows its debt at the sync, and Booked names what it '
          f'set aside ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_codeowners_check_is_a_check():
    """`build_codeowners.py --check` verifies without writing, and its output
    is a function of its source rather than of when it ran.

    TWO DEFECTS, both found 2026-09-06 by a caller trying to VERIFY that
    CODEOWNERS was current and instead dirtying the tree mid-PR:

      1. `--check` was not a flag at all. main() ignored argv, so the flag
         fell through and the tool WROTE -- a checker that answers "is this
         current?" by making it current cannot return a wrong answer, and
         cannot return a useful one. Same shape as verify-postcondition's
         own rule one level up: the check reported success by causing the
         state it was asked to confirm.
      2. The header stamped `git rev-parse HEAD`, so regenerating produced a
         diff after EVERY commit whether or not approvers changed. A derived
         file must be a function of its SOURCE; stamped with the time it was
         built, "is it current?" has no stable answer.

    BestPractice has no approvers.json -- it is not a shared set -- so none of
    this is exercised by the tree, and that is exactly why it went unnoticed
    while the tool was private to one shared set. The fixture supplies one.
    Now that build_codeowners.py is in ENGINE_FILES, every source set the
    bootstrap creates inherits whichever behavior this has."""
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-codeowners-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        shutil.copy(ROOT / 'tools' / 'build_codeowners.py', tmp / 'tools')
        approvers = tmp / 'approvers.json'
        codeowners = tmp / 'CODEOWNERS'
        approvers.write_text(
            '{"approvers": [{"name": "A", "github": "a"}, '
            '{"name": "B", "github": "b"}]}', encoding='utf-8')

        def run(*args):
            return subprocess.run(
                [sys.executable, str(tmp / 'tools' / 'build_codeowners.py'), *args],
                capture_output=True, text=True)

        r = run('--check')
        cases.append(('--check on a missing CODEOWNERS fails', r.returncode == 1))
        cases.append(('...and does NOT create it -- a checker that repairs is '
                      'a builder, and the caller cannot tell the two apart '
                      'afterwards', not codeowners.exists()))

        cases.append(('a plain run writes it', run().returncode == 0 and codeowners.is_file()))
        first = codeowners.read_bytes()
        cases.append(('--check on a current file passes', run('--check').returncode == 0))
        cases.append(('...having written nothing', codeowners.read_bytes() == first))

        run()
        cases.append(('regeneration is byte-identical when approvers.json is '
                      'unchanged -- the HEAD-sha churn that made every check '
                      'a false positive is gone', codeowners.read_bytes() == first))

        codeowners.write_bytes(first + b'# hand edit\n')
        cases.append(('a hand-edited CODEOWNERS is detected', run('--check').returncode == 1))

        run()
        approvers.write_text(
            '{"approvers": [{"name": "A", "github": "a"}]}', encoding='utf-8')
        cases.append(('a changed approver list is detected',
                      run('--check').returncode == 1))

        run()
        stable = codeowners.read_bytes()
        r = run('--chekc')
        cases.append(('a MISSPELLED flag is refused, not silently treated as '
                      '"no arguments" -- that fall-through is defect 1, and '
                      'doing the destructive thing on a typo is how it hid',
                      r.returncode != 0 and codeowners.read_bytes() == stable))

        approvers.unlink()
        cases.append(('an individual set (no approvers.json) exits 0 with a '
                      'note rather than failing', run('--check').returncode == 0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'build_codeowners --check verifies without writing, and its output '
          f'depends on its source not its build time ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_status_contract():
    """A practice that is not `active` must say where its rule went.

    THE INCIDENT (2026-09-06). `status: retired` recorded that a rule stopped
    applying here but never whether anything replaced it. The forwarding
    address lived only as English prose in `## Story`, which no tool reads, so
    "deduplicated safely" and "dropped and forgotten" were indistinguishable to
    every check in the system. A routine per-commit check was dropped on the
    authority of an unrelated occasional one -- the two rules resembled each
    other, and resemblance was accepted as coverage. Nothing failed, because
    nothing could: no check had anything to compare.

    The vocabulary is the fix, and this is what gives it teeth
    (spec/PRACTICE_FORMAT.md, "Status"):

      active         no forwarding address; the rule applies here.
      deduplicated   the COPY is redundant; `in_force_at:` names a slug that
                     must RESOLVE IN FORCE, or `engine`.
      retired        wanted nowhere; `in_force_at: none` and a real ## Story.

    WHAT THIS CHECK REFUSES TO CLAIM. "Resolves in force" is only answerable
    against the actually-declared sources. When any of them is unreachable --
    a sibling clone this session does not have -- the resolved set is
    incomplete, and a "does not resolve" verdict would be an artifact of the
    missing checkout rather than a finding. In that case this degrades to the
    SHAPE check (a forwarding address is present and well-formed) and says so
    in its own name, rather than reporting a weaker check as the stronger
    one."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as _bv
    import precedent_resolve as _pr

    # --- can we resolve for real this run? --------------------------------
    slug_in_force, resolution = None, 'shape only'
    try:
        sources = _pr.load_config(str(ROOT))
        res = _pr.resolve(sources)
        if res['missing']:
            gone = ', '.join(m['name'] for m in res['missing'])
            resolution = f'shape only -- source(s) unreachable this run: {gone}'
        else:
            in_force = set(res['practices'])
            slug_in_force = in_force.__contains__
            resolution = f'resolved against {len(sources)} source(s)'
    except Exception as e:                                # noqa: BLE001
        resolution = f'shape only -- sources unresolvable ({type(e).__name__}: {e})'

    # --- 1. every practice file in every source this repo owns -------------
    violations, scanned = [], 0
    dirs = [ROOT / 'practices']
    local = ROOT / 'local' / 'practices'
    if local.is_dir():
        dirs.append(local)
    for d in dirs:
        for f in sorted(d.glob('*.md')):
            try:
                fm, sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            scanned += 1
            v = _bv.status_contract_violation(fm, sections, slug_in_force)
            if v:
                violations.append(f"{f.relative_to(ROOT)}: {v}")
    check(f'status contract holds for every practice in this repo '
          f'({scanned} scanned, {resolution})',
          not violations, '; '.join(violations[:8]))

    # --- 2. the contract actually refuses each way of getting it wrong -----
    # BestPractice's own catalogue is 100% active, so without these the check
    # above passes vacuously and would go on passing if the validator were
    # gutted. Each case is a rule from the table in this docstring.
    def fm_of(status, in_force_at=None):
        d = {'status': status}
        if in_force_at is not None:
            d['in_force_at'] = in_force_at
        return d

    story = {'story': 'It stopped mattering when we dropped the tool.'}
    live = {'header-caps'}.__contains__
    cases = [
        ('an active practice with a forwarding address is contradictory',
         _bv.status_contract_violation(fm_of('active', 'header-caps')) is not None),
        ('an ordinary active practice is clean',
         _bv.status_contract_violation(fm_of('active')) is None),
        ('deduplicated with no in_force_at is refused -- this is exactly the '
         '"dropped and forgotten" case that used to be indistinguishable',
         _bv.status_contract_violation(fm_of('deduplicated')) is not None),
        ('deduplicated pointing at a slug that IS in force is accepted',
         _bv.status_contract_violation(fm_of('deduplicated', 'header-caps'),
                                       slug_in_force=live) is None),
        ('deduplicated pointing at a slug that is NOT in force is refused -- '
         'a surviving copy that is itself gone is not a surviving copy',
         _bv.status_contract_violation(fm_of('deduplicated', 'deep-check'),
                                       slug_in_force=live) is not None),
        ('deduplicated with in_force_at: engine is accepted -- the successor '
         'is code, not a slug',
         _bv.status_contract_violation(fm_of('deduplicated', 'engine'),
                                       slug_in_force=live) is None),
        ('deduplicated with in_force_at: none is refused -- in force nowhere '
         'is retirement, and needs retirement\'s evidence',
         _bv.status_contract_violation(fm_of('deduplicated', 'none')) is not None),
        ('retired pointing at a live slug is refused -- if the rule survives '
         'there, it was deduplicated',
         _bv.status_contract_violation(fm_of('retired', 'header-caps'), story,
                                       slug_in_force=live) is not None),
        ('retired with in_force_at: none and a real Story is accepted',
         _bv.status_contract_violation(fm_of('retired', 'none'), story) is None),
        ('retired with an empty Story is refused -- the one status no '
         'mechanism can verify must say why in prose',
         _bv.status_contract_violation(fm_of('retired', 'none'), {'story': ''})
         is not None),
        ('an unrecognized status is reported rather than waved through',
         _bv.status_contract_violation(fm_of('superseded', 'header-caps'))
         is not None),
        ('...and is NOT in force, so an unknown status fails closed',
         not _bv.is_in_force(fm_of('superseded'))),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'the status contract refuses each way of getting it wrong '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))

    # --- 3. the new word is wired to the FILTER, not just to the validator --
    # A status can be spelled correctly in the spec, validated correctly here,
    # and still be loaded into every session if the loader's own predicate
    # never learned it. That is the shape of the original defect, so it gets
    # its own end-to-end case rather than being assumed from case 2.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dedup-'))
    try:
        (tmp / 'practices').mkdir()
        src = ROOT / 'practices'
        (tmp / 'practices' / 'repo-is-memory.md').write_text(
            (src / 'repo-is-memory.md').read_text(encoding='utf-8'), encoding='utf-8')
        dedup = (src / 'verify-postcondition.md').read_text(encoding='utf-8')
        dedup = re.sub(r'^status:(\s+)active$', r'status:\1deduplicated', dedup,
                       count=1, flags=re.M)
        dedup = re.sub(r'^in_force_at: null$', 'in_force_at: repo-is-memory',
                       dedup, count=1, flags=re.M)
        if 'deduplicated' not in dedup or 'in_force_at: repo-is-memory' not in dedup:
            raise RuntimeError('fixture did not actually become deduplicated')
        (tmp / 'practices' / 'verify-postcondition.md').write_text(dedup, encoding='utf-8')
        (tmp / 'AGENTS.md').write_text(
            '<!-- BEGIN GENERATED: precedent-loader -->\n<!-- END GENERATED -->\n',
            encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'build_views.py'),
             '--repo', str(tmp), '--agents-only'], capture_output=True, text=True)
        rendered = (tmp / 'AGENTS.md').read_text(encoding='utf-8')
        e2e = [
            ('a deduplicated practice is absent from the generated loader block',
             r.returncode == 0 and 'verify-postcondition' not in rendered),
            ('the active practice beside it is still emitted',
             'repo-is-memory' in rendered),
            ('the drop is announced by status name, not silently',
             'verify-postcondition' in r.stderr and 'deduplicated' in r.stderr),
        ]
        # ...and `precedent show` MARKS it rather than refusing, because a
        # session naming a slug explicitly is asking "what happened to this?"
        s = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_show.py'),
             'verify-postcondition', '--repo', str(tmp)],
            capture_output=True, text=True)
        e2e += [
            ('precedent show still resolves the slug rather than refusing it',
             s.returncode == 0),
            ('...and marks it NOT IN FORCE, naming where the rule lives now',
             'NOT IN FORCE' in s.stdout and 'repo-is-memory' in s.stdout),
            ('...with the marking ABOVE the rule text, so a session that '
             'stops reading early cannot take it as current',
             'NOT IN FORCE' in s.stdout.split('\n\n')[0]),
        ]
        bad_e2e = [n for n, ok in e2e if not ok]
        check(f'the deduplicated status is honored by the loading channels, '
              f'not merely spelled correctly ({len(e2e)} stated cases)',
              not bad_e2e,
              '; '.join(bad_e2e) + f' || build_views: {r.stdout}{r.stderr} '
              f'|| show: {s.stdout}{s.stderr}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_scope_field_is_legal_and_matches_this_spec():
    """`scope:` is a real filter, and the spec's list of what carries it is
    the list, not a description of one.

    THE INCIDENT (2026-09-22). spec/PRACTICE_FORMAT.md's `scope` section
    named four practices as tagged `engine-dev`. The tree carried three,
    and not the same three: `cross-source-rollout` had been tagged on
    2026-09-15 by a classification sweep that never touched this paragraph,
    and `very-deep-check` and `full-practice-audit` were deliberately
    UNTAGGED on 2026-09-21 because each declares a standing `command:` and
    `engine-dev` withholds the practice from a consuming repo -- the
    incident `vocabulary-reaches-the-consumer` is registered for. A deep
    check read the tree against the stale paragraph, and filed a considered
    decision as silent drift: the proposal that came out of it was to
    revert both files, which `vocabulary-reaches-the-consumer` refuses.
    Measured before writing this, by making the change and running it.

    So the expensive failure was not a bad VALUE. It was a documented list
    and a tree disagreeing with nothing to notice, and the cost was a
    session's work spent proposing a revert of a one-day-old decision.

    WHAT THIS CANNOT DO, said plainly. It cannot catch a practice somebody
    MEANT to scope and did not. `scope: null` is dropped by the one null
    policy in split_practices.parse_frontmatter_fields, for every field in
    both formats, so `scope: null` and no `scope:` line are the same input
    to every consumer in the engine and nothing downstream can recover the
    difference. Authoring the list in the spec and comparing it here is the
    answer to that, and it is why part 3 below is the part that matters.
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as _bv

    cases = []

    # --- 1. every declared scope is one of the two legal values -----------
    dirs = [(ROOT / 'practices', False)]
    local = ROOT / 'local' / 'practices'
    if local.is_dir():
        dirs.append((local, True))
    scanned, tagged = 0, set()
    for d, repo_local in dirs:
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            scanned += 1
            v = _bv.scope_violation(fm, repo_local=repo_local)
            cases.append((f'{f.relative_to(ROOT)}: scope is legal',
                          v is None, v or ''))
            if not repo_local and _bv._is_engine_dev_scoped(fm):
                tagged.add(fm.get('slug', f.stem).strip())

    # --- 2. the spec's own list, read out of the paragraph that claims it --
    # Anchored on the authored lead-in. A reworded paragraph fails HERE,
    # loudly, rather than quietly finding no links and declaring the tree
    # empty-and-agreeing -- which is the shape of vacuous pass this whole
    # check exists to stop (practice: scripts-assert-properties).
    spec = (ROOT / 'spec' / 'PRACTICE_FORMAT.md').read_text(encoding='utf-8')
    anchor = '**Tagged\n`engine-dev` today:**'
    named = None
    if anchor in spec:
        para = spec.split(anchor, 1)[1].split('\n\n', 1)[0]
        named = set(re.findall(r'\]\(\.\./practices/([a-z0-9-]+)\.md\)', para))
    cases.append(('spec/PRACTICE_FORMAT.md still carries the authored '
                  '`Tagged engine-dev today:` list this check reads',
                  bool(named), 'anchor or links not found -- reword the '
                  'paragraph and this check goes blind, so it fails instead'))

    if named:
        cases.append(('the tree\'s engine-dev practices are exactly the ones '
                      'that paragraph names', named == tagged,
                      f'spec names {sorted(named)}, tree carries '
                      f'{sorted(tagged)}'))

    # --- 3. and it refuses each way of getting it wrong --------------------
    # Without these, parts 1 and 2 pass vacuously on a clean tree and would
    # go on passing if the validator were gutted (practice:
    # checkable-gets-checked -- wire it in with a firing test).
    planted = [
        ({'slug': 'x', 'scope': 'adopter'}, False,
         'a value that is neither legal'),
        ({'slug': 'x', 'scope': 'engine_dev'}, False,
         'the underscore spelling of the legal one'),
        ({'slug': 'x', 'scope': 'any-adopter'}, False, 'the explicit default'),
        ({'slug': 'x', 'scope': 'engine-dev'}, False, 'the other legal value'),
        ({'slug': 'x'}, False, 'an absent field'),
    ]
    for fm, repo_local, what in planted:
        got = _bv.scope_violation(fm, repo_local=repo_local)
        want_violation = fm.get('scope') not in (None, 'any-adopter',
                                                 'engine-dev')
        cases.append((f'planted: {what} is '
                      f'{"refused" if want_violation else "accepted"}',
                      bool(got) == want_violation, repr(got)))

    cases.append(('planted: a repo-local practice declaring engine-dev is '
                  'flagged as redundant',
                  bool(_bv.scope_violation({'slug': 'x',
                                            'scope': 'engine-dev'},
                                           repo_local=True)), ''))
    cases.append(('planted: a repo-local practice declaring any-adopter is '
                  'not flagged -- only engine-dev is the redundant one',
                  _bv.scope_violation({'slug': 'x', 'scope': 'any-adopter'},
                                      repo_local=True) is None, ''))

    # And the list comparison itself, on a doctored spec paragraph: it must
    # report a name the tree does not carry, not shrug.
    doctored = {'routing-audit', 'a-practice-that-is-not-there'}
    cases.append(('planted: a spec list naming a practice the tree does not '
                  'carry is a mismatch', doctored != tagged, ''))

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_retired_practices_leave_the_views():
    """A practice that is not in force must not be in the loader block.

    build_views.py never read `status:` at all -- not in load_practices, not
    in the loader-block build, nowhere -- so a retired practice went on being
    emitted into AGENTS.md, MAP.md and GLOSSARY.md exactly like an active
    one. precedent_resolve.py had it right and printed `not in force`; the
    two channels disagreed, and the one a session actually loads was the
    wrong one.

    BestPractice's own catalogue has no retired practice, which is precisely
    why nothing here caught it: found 2026-09-06 in a private shared set whose
    generated AGENTS.md listed all three of its retired practices, one of
    them retired that same day. So this case supplies a retired practice of
    its own rather than relying on the tree having one."""
    import tempfile, shutil
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-retired-'))
    try:
        (tmp / 'practices').mkdir()
        src = ROOT / 'practices'
        active = (src / 'repo-is-memory.md').read_text(encoding='utf-8')
        (tmp / 'practices' / 'repo-is-memory.md').write_text(active, encoding='utf-8')
        retired = (src / 'verify-postcondition.md').read_text(encoding='utf-8')
        retired = re.sub(r'^status:(\s+)active$', r'status:\1retired', retired,
                         count=1, flags=re.M)
        if 'status:      retired' not in retired and 'status: retired' not in retired:
            raise RuntimeError('fixture did not actually become retired')
        (tmp / 'practices' / 'verify-postcondition.md').write_text(retired, encoding='utf-8')
        (tmp / 'AGENTS.md').write_text(
            '<!-- BEGIN GENERATED: precedent-loader -->\n<!-- END GENERATED -->\n',
            encoding='utf-8')

        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'build_views.py'),
             '--repo', str(tmp), '--agents-only'],
            capture_output=True, text=True)
        rendered = (tmp / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('a retired practice is absent from the generated loader '
                      'block -- retirement is not cosmetic',
                      r.returncode == 0 and 'verify-postcondition' not in rendered,
                      r.stdout + r.stderr + '\n---\n' + rendered))
        cases.append(('an active practice in the same directory is still '
                      'emitted -- the filter drops the retired one, not the '
                      'catalogue', 'repo-is-memory' in rendered, rendered))
        cases.append(('the drop is announced, not silent -- a retirement that '
                      'vanishes without a word is the same failure one size '
                      'down',
                      'verify-postcondition' in r.stderr and 'retired' in r.stderr,
                      r.stdout + r.stderr))

        sys.path.insert(0, str(ROOT / 'tools'))
        import build_views as _bv
        import precedent_resolve as _pr
        cases.append(('the loader and the resolver share one definition of '
                      '"in force", so they cannot drift apart again',
                      _pr.IN_FORCE_STATUS is _bv.IN_FORCE_STATUS,
                      f'{_pr.IN_FORCE_STATUS!r} vs {_bv.IN_FORCE_STATUS!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a retired practice leaves the generated views ({len(cases)} '
          f'stated cases)', not bad,
          '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_resident_subset(files):
    # Phase 1's always-loaded set was every practice, unconditionally (no
    # tier existed yet). The post-migration resident set must be a STRICT
    # subset of that -- i.e. fewer than all of them, and within the token
    # budget build_views.py enforces at build time (a build over budget
    # already exits nonzero there; this check additionally confirms the
    # curation actually happened rather than defaulting everything resident).
    resident = [stem for stem, (fm, _s, _f) in files.items() if fm.get('tier') == 'resident']
    ok = 0 < len(resident) < len(files)
    check('resident subset (curated resident tier is a strict, non-empty subset of all practices)',
          ok, f"{len(resident)} of {len(files)} practices are resident")


def check_lint_runs_the_hosts_shim():
    """A consumer configures doc_lint from a host shim, but the push check
    runs the engine file directly, so the consumer's settings never reached
    its gate (2026-10-04: a folder the consumer had exempted failed its
    push). A consumer names its shim in tools/doc_lint_host.json, and
    running the engine runs the shim. Both directions: with no host file
    the engine runs as itself."""
    import tempfile, shutil
    name = 'doc_lint hands off to the host shim a consumer names'
    env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        (repo / 'tools').mkdir()
        for f in ('doc_lint.py', 'frontmatter_yaml.py', 'generated_blocks.py',
                  'declared_base_branch.py'):
            shutil.copy(ROOT / 'tools' / f, repo / 'tools' / f)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}\n')
        (repo / 'host').mkdir()
        (repo / 'host' / 'lint_shim.py').write_text(
            'import sys\nprint("HOST SHIM RAN", sys.argv[1:])\nsys.exit(0)\n')
        run = lambda: subprocess.run([sys.executable, 'tools/doc_lint.py', '--all'],
                                     cwd=repo, capture_output=True, text=True, env=env)
        r = run()
        cases.append(('with no host file the engine runs as itself',
                      'HOST SHIM RAN' not in r.stdout))
        (repo / 'tools' / 'doc_lint_host.json').write_text('{"shim": "host/lint_shim.py"}\n')
        r = run()
        cases.append(('with a host file, running the engine runs the shim, with its arguments',
                      "HOST SHIM RAN ['--all']" in r.stdout and r.returncode == 0))
        (repo / 'tools' / 'doc_lint_host.json').write_text('{"shim": "host/missing.py"}\n')
        r = run()
        cases.append(('a host file naming a missing shim fails loudly',
                      r.returncode != 0 and 'does not exist' in (r.stdout + r.stderr)))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_lint_refuses_an_open_item_waiting_on_an_upstream_fix():
    """An open item about a fix in another repository has to link the pull
    request that makes it (practice: todo-is-a-handoff, 2026-10-06: in one
    consumer four such items sat for one to two weeks, each an hour's fix).
    doc_lint refuses one at the commit; it leaves alone the same item with a
    PR link, an item blocked on an outside quote, and a closed item."""
    import tempfile, shutil
    name = 'doc_lint refuses an open item waiting on an upstream fix'
    env = _fixture_git_env()
    # `disposition: ask` keeps the stated-reason arm beside this one
    # (check_lint_refuses_an_open_item_that_names_no_blocker) out of these
    # cases: they are about the upstream arm only.
    head = ('---\nslug: {slug}\nkind: manual\nstatus: {status}\n'
            'disposition: ask\n'
            'blocked_on: {blocked}\nnoted: 2026-10-06\n---\n## What\n\n{body}\n')
    items = {
        'vendored-path': ('open', 'null', 'The check in tools/doc_lint.py '
                          'misreads a fence; needs a change upstream.', True),
        'with-pr-link': ('open', 'null', 'The check in tools/doc_lint.py '
                         'misreads a fence; fixed in '
                         'https://github.com/example/Engine/pull/12, waiting '
                         'on its review.', False),
        'outside-quote': ('open', 'vendor quotes from two cell makers',
                          'Needs source access to example.com for the '
                          'price sheet.', False),
        'closed': ('done', 'null', 'The check in tools/doc_lint.py misread '
                   'a fence.', False),
        'source-in-reason': ('open', 'push access to some-set', 'A rule '
                             'there is worded wrong.', True),
        # A link to a vendored file is reading (2026-10-07, a consumer's
        # check-in item linking the install runbook); the link's own text
        # naming the file still counts.
        'reading-link': ('open', 'null', 'Follow [the runbook]'
                         '(../tools/doc_lint.py) at each check-in.', False),
        'named-in-link-text': ('open', 'null', '[tools/doc_lint.py]'
                               '(../tools/doc_lint.py) misreads a fence.', True),
        # Running a vendored tool is using it (2026-10-08, a consumer's item
        # saying to run a vendored tool was refused): the program argument
        # of an interpreter in a code span or a fence does not count; the
        # same path as a later argument, or in prose beside it, does.
        'runs-in-span': ('open', 'null', 'Run `python3 tools/doc_lint.py '
                         '--fix todo/x.md` before each commit.', False),
        'runs-in-fence': ('open', 'null', 'At each check-in:\n\n```\n'
                          'bash ../tools/doc_lint.py\n'
                          '/usr/bin/env python3 -I tools/doc_lint.py --repo .\n'
                          '```', False),
        'argument-in-span': ('open', 'null', '`grep -n fence tools/doc_lint.py` '
                             'shows the misread.', True),
        'later-argument': ('open', 'null', '`python3 tools/other.py '
                           'tools/doc_lint.py` shows the misread.', True),
        'runs-and-names': ('open', 'null', 'Run `python3 tools/doc_lint.py`; '
                           'tools/doc_lint.py misreads a fence.', True),
        # 2026-10-10, a consumer's Update Vendors: an item asking whether the
        # person grandfathers three commits quoted a check's output, which
        # names its own script, and was refused as an upstream fix. A fence
        # is quoted material; and an item whose stated reason is a person
        # says what it waits on.
        'quoted-output': ('open', 'null', 'The check said:\n\n```\n'
                          'FAIL tools/doc_lint.py: 3 commit(s) out of zone\n```'
                          '\n\nGrandfather them, or rewrite?', False),
        'waiting-on-a-person': ('open', 'the person, to say whether to '
                                'grandfather them', 'tools/doc_lint.py refuses '
                                'three old commits.', False),
        'reason-names-a-source': ('open', 'a fix in some-set', 'tools/doc_lint.py '
                                  'misreads a fence.', True),
    }
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        for f in ('doc_lint.py', 'frontmatter_yaml.py', 'generated_blocks.py',
                  'declared_base_branch.py',
                  'precedent_engine_freshness.py', 'precedent_resolve.py'):
            shutil.copy(ROOT / 'tools' / f, repo / 'tools' / f)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'source_repo': 'https://github.com/example/Engine',
             'source_branch': 'main', 'source_commit': 'x',
             'files': ['doc_lint.py']}))
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'some-set', 'path': '../some-set'}]}))
        (repo / 'todo').mkdir()
        for slug, (status, blocked, body, _fires) in items.items():
            (repo / 'todo' / f'todo-2026-10-06-{slug}.md').write_text(
                head.format(slug=slug, status=status, blocked=blocked, body=body))
        for slug, (_s, _b, _body, fires) in items.items():
            rel = f'todo/todo-2026-10-06-{slug}.md'
            r = subprocess.run([sys.executable, 'tools/doc_lint.py', rel],
                               cwd=repo, capture_output=True, text=True, env=env)
            fired = (r.returncode == 1 and 'WAITING ON AN UPSTREAM FIX' in r.stdout
                     and 'tools/upstream_fix.py' in r.stdout)
            quiet = r.returncode == 0 and 'UPSTREAM FIX' not in r.stdout
            cases.append((f'{slug}: {"fires" if fires else "passes"}',
                          fired if fires else quiet))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_lint_refuses_an_open_item_that_names_no_blocker():
    """Every open item a change adds says what it waits on (practice:
    todo-is-a-handoff, 2026-10-12: a downstream spec's "What Is Not Yet
    Settled" list and an unchecked box queued checks a few searches would
    have done, and two of them killed the design once done). doc_lint
    refuses an unchecked box, or a list item under an open-list heading,
    with no `(needs: ...)` naming a reason the session cannot clear itself,
    and an open item file with nothing in blocked_on or waiting_on. It
    leaves alone a stated reason, a checked or struck item, a fence, a list
    under any other heading, the checklist marker, and -- in the commit
    gate's scope -- an old item on a line the change did not touch."""
    import tempfile, shutil
    name = 'doc_lint refuses an open item that names no blocker'
    env = _fixture_git_env()
    docs = {
        'bare-box': ('- [ ] Check the lifting standard\n', True),
        'box-with-decision': ('- [ ] Pick the rotor (needs: decision -- the '
                              'owner, between two quotes)\n', False),
        'box-with-test': ('- [ ] Spar strength (needs: test, a coupon pull '
                          'on the real layup)\n', False),
        'box-another-repo': ('- [ ] Fix the parser (needs: a fix in another '
                             'repository)\n', True),
        'box-decision-no-who': ('- [ ] Pick one (needs: decision)\n', True),
        'box-pr-no-link': ('- [ ] Land the engine fix (needs: pr)\n', True),
        'box-pr-linked': ('- [ ] Land the engine fix (needs: pr '
                          'https://github.com/example/Engine/pull/7)\n', False),
        'box-out-of-scope': ('- [ ] Wind-tunnel the fairing (out of scope: a '
                             'week of tunnel time this session has no part '
                             'in)\n', False),
        'box-waiting-external': ('- [ ] Price the cells (waiting on: external '
                                 '-- the supplier\'s quote)\n', False),
        'reason-on-continuation': ('- [ ] Check the clearance against the\n'
                                   '  drawing (needs: access, refused by the '
                                   'drawing vault)\n', False),
        'checked-box': ('- [x] Check the lifting standard\n', False),
        'fenced-box': ('```\n- [ ] Check the lifting standard\n```\n', False),
        'unsettled-list': ('## What Is Not Yet Settled\n\n'
                           '- The current edition of the standard\n', True),
        'open-questions-numbered': ('## Open questions\n\n'
                                    '1. Which alloy?\n', True),
        'unsettled-list-with-reasons': (
            '## Still to settle\n\n- The yield strength (needs: test -- a '
            'coupon from the mill lot)\n', False),
        'list-under-other-heading': ('## Design\n\n- The current edition '
                                     'of the standard\n', False),
        'open-list-ends-at-next-heading': (
            '## Next steps\n\n- Ship it (needs: decision -- the owner)\n\n'
            '## Design\n\n- A plain point\n', False),
        'title-is-not-a-list': ('# A TODO is a handoff\n\n- A plain point\n',
                                False),
        'struck-item': ('## Open items\n\n- ~~Check the standard~~ done\n',
                        False),
        'item-marker': ('- [ ] Sign the form <!--checklist-->\n', False),
        'document-marker': ('<!--checklist-->\n\n- [ ] Sign the form\n',
                            False),
    }
    items = {
        'no-reason': ('open', 'null', 'null', 'manual', True),
        'blocked': ('open', '"the owner, on the budget"', 'null', 'manual', False),
        'waiting': ('open', 'null', '"the supplier\'s quote"', 'manual', False),
        'a-decision': ('open', 'null', 'null', 'decision', False),
        'closed': ('done', 'null', 'null', 'manual', False),
        'links-its-pr': ('open', 'null', 'null', 'manual', False),
    }
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        for f in ('doc_lint.py', 'frontmatter_yaml.py', 'generated_blocks.py',
                  'declared_base_branch.py',
                  'precedent_engine_freshness.py', 'precedent_resolve.py',
                  'title_case.py'):
            shutil.copy(ROOT / 'tools' / f, repo / 'tools' / f)
        (repo / 'docs').mkdir()
        for slug, (body, _fires) in docs.items():
            (repo / 'docs' / f'{slug}.md').write_text(body)
        (repo / 'todo').mkdir()
        for slug, (status, blocked, waiting, kind, _f) in items.items():
            (repo / 'todo' / f'todo-2026-10-12-{slug}.md').write_text(
                f'---\nslug: {slug}\nkind: {kind}\nstatus: {status}\n'
                f'blocked_on: {blocked}\nwaiting_on: {waiting}\n'
                f'noted: 2026-10-12\n---\n## What\n\n- [ ] A step\n'
                + ('\nWaits on https://github.com/example/Engine/pull/9.\n'
                   if slug == 'links-its-pr' else ''))

        def lint(*args):
            return subprocess.run([sys.executable, 'tools/doc_lint.py', *args],
                                  cwd=repo, capture_output=True, text=True,
                                  env=env)
        runs = [(f'docs/{s}.md', f) for s, (_b, f) in docs.items()]
        runs += [(f'todo/todo-2026-10-12-{s}.md', v[-1]) for s, v in items.items()]
        for rel, fires in runs:
            r = lint(rel)
            fired = (r.returncode == 1 and 'SAYS NOTHING BLOCKS IT' in r.stdout
                     and 'could this session do it now?' in r.stdout)
            quiet = r.returncode == 0 and 'SAYS NOTHING BLOCKS IT' not in r.stdout
            cases.append((f'{rel}: {"fires" if fires else "passes"}',
                          fired if fires else quiet))
        # The commit gate's scope: an old item is backlog, a new one fails.
        def git(*a):
            subprocess.run(['git', *a], cwd=repo, env=env, capture_output=True)
        shutil.rmtree(repo / 'todo')
        spec = repo / 'docs' / 'spec.md'
        spec.write_text('# Spec\n\n## What Is Not Yet Settled\n\n'
                        '- An old question\n')
        git('add', '-A')
        git('commit', '-qm', 'base')
        git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        spec.write_text(spec.read_text() + '\nA new paragraph.\n')
        r = lint()
        cases.append(('an old item, on a line the change did not touch, is '
                      'backlog', r.returncode == 0 and 'An old question' in r.stdout))
        spec.write_text(spec.read_text() + '\n- [ ] A new check\n')
        r = lint()
        cases.append(('a new unchecked box in the same change fails the gate',
                      r.returncode == 1 and 'A new check' in r.stdout))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_content_paths_skip_session_work_checks():
    """A file under precedent.json's `content_paths` -- the person's own
    to-do list or notes -- is skipped by the checks about session work: the
    open-item check (practice: todo-is-a-handoff) and the unglossed-acronym
    warning (practice: acronyms-glossary). The same lines anywhere else
    still fire, and a content file still gets the link check.

    WHY. Reported by a consuming repository, 2026-10-13: a personal to-do
    repository's own list was refused line by line, every `- [ ]` asked for
    a `(needs: ...)`, though the boxes are the person's list and no session
    left them behind. Planted: one declared folder and one declared file,
    each holding a bare box and an unglossed acronym; the same text in an
    undeclared file is the control."""
    import tempfile, shutil
    env = _fixture_git_env()
    body = ('# Mine\n\nThe QZXV plan.\n\n- [ ] Buy the paint\n')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        # The whole engine's modules: precedent_resolve, the one reader of
        # content_paths, imports several of its siblings, and a fixture
        # missing one would declare nothing and test nothing.
        for f in (ROOT / 'tools').glob('*.py'):
            shutil.copy(f, repo / 'tools' / f.name)
        (repo / 'GLOSSARY.md').write_text('# Glossary\n\n- **API** -- a fixture term\n')
        (repo / 'precedent.json').write_text(json.dumps({'content_paths': [
            {'path': 'lists/', 'reason': 'my own to-do lists'}, 'NOTES.md']}))
        for rel in ('lists/home.md', 'NOTES.md', 'docs/spec.md'):
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(body)
        (repo / 'lists' / 'linked.md').write_text(
            '# Linked\n\nSee [the plan](missing-plan.md).\n')

        def lint(rel):
            return subprocess.run([sys.executable, 'tools/doc_lint.py', rel],
                                  cwd=repo, capture_output=True, text=True,
                                  env=env)
        for rel in ('lists/home.md', 'NOTES.md'):
            r = lint(rel)
            cases.append((f'{rel} (declared content): a bare box passes',
                          r.returncode == 0
                          and 'SAYS NOTHING BLOCKS IT' not in r.stdout, f'rc={r.returncode} {r.stdout} {r.stderr}'))
            cases.append((f'{rel} (declared content): an unglossed acronym is '
                          'not reported', 'UNGLOSSED ACRONYMS' not in r.stdout
                          and 'QZXV' not in r.stdout, r.stdout))
        r = lint('docs/spec.md')
        cases.append(('CONTROL: the same box outside content_paths still fails',
                      r.returncode == 1 and 'SAYS NOTHING BLOCKS IT' in r.stdout
                      and 'Buy the paint' in r.stdout, r.stdout))
        cases.append(('CONTROL: the same acronym outside content_paths is still '
                      'reported', 'UNGLOSSED ACRONYMS' in r.stdout
                      and 'docs/spec.md:3: QZXV' in r.stdout, r.stdout))
        r = lint('lists/linked.md')
        cases.append(('a content file still gets the broken-link check',
                      r.returncode == 1 and 'missing-plan.md' in r.stdout, r.stdout))
    bad = [f'{n}: {d[:900]}' for n, ok, d in cases if not ok]
    check(f'content_paths skip the session-work checks and nothing else '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_additions_load_with_their_rule():
    """An addition (`adds_to: SLUG`, Morgan, 2026-10-09, "Option 1") loads
    with the rule it adds to and costs no occasion-index line of its own.

    Cases: lands_in_occasion_index() refuses an addition even with
    index_required: true, and the rendered block carries the base's line and
    not the addition's, nor a resident addition's Rule; precedent_show.py on
    the base prints the addition from ANOTHER declared source, under its own
    heading; on the addition, names the base; on a deduplicated slug, shows
    the live rule with its additions, including one written against the old
    name; the gate that prints the base prints the addition after it, though
    the addition registers no gate; the spoken-commands line for a base
    marks how many additions it has. CONTROL: a rule nobody adds to shows
    no addition heading."""
    import shutil, tempfile
    import build_views as bv
    import precedent_session_practices as psp
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-adds-to-'))
    P = _addition_fixture_practice
    try:
        added = P('its-addition', adds='base-rule',
                  extra='index_required: true\n',
                  occasion='a person says \\"Do The Fixture\\"',
                  rule='The addition says more.')
        d = tmp / 'render' / 'practices'
        d.mkdir(parents=True)
        (d / 'base-rule.md').write_text(P('base-rule'), encoding='utf-8')
        (d / 'its-addition.md').write_text(added, encoding='utf-8')
        (d / 'resident-addition.md').write_text(
            P('resident-addition', tier='resident', adds='base-rule',
              rule='RESIDENT ADDITION TEXT.'), encoding='utf-8')
        loaded = bv.load_practices(d, announce=False)
        fms = {f['slug']: f for f, _s, _f in loaded}
        cases.append(('an addition never lands in the occasion index, even with '
                      'index_required: true',
                      bv.lands_in_occasion_index(fms['its-addition']) is False
                      and bv.lands_in_occasion_index(fms['base-rule']) is True, ''))
        block, _t, _c = bv.build_loader_block(loaded, block_dir=d.parent)
        cases.append(('the rendered block lists the base and not the addition, '
                      'and carries no resident addition',
                      'base-rule' in block and 'its-addition' not in block
                      and 'RESIDENT ADDITION TEXT.' not in block, failure_detail(block, 600)))

        base, extra = tmp / 'set-base', tmp / 'set-extra'
        for s, name in ((base, 'fx-set-base'), (extra, 'fx-set-extra')):
            (s / 'practices').mkdir(parents=True)
            (s / 'precedent-source.json').write_text(
                json.dumps({'name': name, 'level': 'shared'}), encoding='utf-8')
        (base / 'practices' / 'base-rule.md').write_text(
            P('base-rule', gates='["review"]', rule='The base rule.'),
            encoding='utf-8')
        (base / 'practices' / 'old-rule.md').write_text(
            P('old-rule', status='deduplicated', to='base-rule'), encoding='utf-8')
        (base / 'practices' / 'lonely-rule.md').write_text(
            P('lonely-rule', rule='Nobody adds to this.'), encoding='utf-8')
        (extra / 'practices' / 'its-addition.md').write_text(added, encoding='utf-8')
        (extra / 'practices' / 'old-name-addition.md').write_text(
            P('old-name-addition', adds='old-rule', rule='Written against the old name.'),
            encoding='utf-8')
        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'precedent.json').write_text(json.dumps({'format_version': 1, 'sources': [
            {'level': 'shared', 'name': 'fx-set-base', 'path': str(base)},
            {'level': 'shared', 'name': 'fx-set-extra', 'path': str(extra)}]}),
            encoding='utf-8')
        env = {**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json')}

        def tool(*args):
            r = subprocess.run([sys.executable, *args], capture_output=True,
                               text=True, env=env, timeout=120)
            return r.returncode, r.stdout + r.stderr

        def show(slug):
            return tool(str(ROOT / 'tools' / 'precedent_show.py'), '--repo',
                        str(repo), slug)
        rc, out = show('base-rule')
        cases.append(('show on the base prints the addition from the other source',
                      rc == 0 and 'The base rule.' in out
                      and 'Addition in force here (from shared/fx-set-extra): '
                          'its-addition' in out
                      and 'The addition says more.' in out
                      and out.index('The base rule.') < out.index('The addition says more.'),
                      failure_detail(out, 600)))
        cases.append(('...including one written against a deduplicated name',
                      'Written against the old name.' in out, failure_detail(out, 600)))
        rc, out = show('its-addition')
        cases.append(('show on the addition names the rule it adds to',
                      rc == 0 and 'The addition says more.' in out
                      and 'Adds to `base-rule`' in out, failure_detail(out, 400)))
        rc, out = show('old-rule')
        cases.append(('show on a deduplicated slug attaches the additions to the '
                      'live rule',
                      rc == 0 and 'old-rule -> base-rule' in out
                      and 'its-addition' in out, failure_detail(out, 600)))
        rc, out = show('lonely-rule')
        cases.append(('CONTROL: a rule nobody adds to shows no addition',
                      rc == 0 and 'Nobody adds to this.' in out
                      and 'Addition in force here' not in out, failure_detail(out, 300)))
        rc, out = tool(str(ROOT / 'tools' / 'precedent_gate.py'), 'review',
                       '--repo', str(repo))
        cases.append(('the gate that prints the base prints its addition after it',
                      'The base rule.' in out and 'The addition says more.' in out
                      and out.index('The base rule.') < out.index('The addition says more.'),
                      failure_detail(out, 600)))

        cmd = P('spoken-rule', extra='command:     {"Do The Fixture": "A fixture."}\n')
        cd = tmp / 'spoken'
        cd.mkdir()
        (cd / 'spoken-rule.md').write_text(cmd, encoding='utf-8')
        (cd / 'spoken-addition.md').write_text(
            P('spoken-addition', adds='spoken-rule'), encoding='utf-8')
        spoken = psp.spoken_block(bv.load_practices(cd, announce=False))
        cases.append(('the spoken-commands line marks the base\'s additions, and '
                      'adds no line for one',
                      '(+ 1 addition here)' in spoken
                      and 'spoken-addition' not in spoken, spoken))
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_thread_renders_never_touch_the_shared_ledger():
    """doc_html's thread ledger: on a working branch a render the branch
    changed is checked against, and recorded in, the thread's own local
    ledger with its own artifact URL; the shared ledger and the shared URLs
    are the trunk's alone (origin: several branches publishing to one
    shared URL overwrote each other). Both directions: on the trunk, or
    with --trunk, or with no thread ledger configured, the shared ledger
    governs as before."""
    import json, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_html as dh
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / 'a.html').write_text('<p>v2</p>')
    shared, thread = tmp / 'shared.json', tmp / 'thread.json'
    shared.write_text(json.dumps({'a.html': dh._sha256(tmp / 'a.html')}))
    saved = {k: getattr(dh, k) for k in ('ROOT', 'RENDER_LEDGER', 'THREAD_LEDGER',
             '_current_branch', '_default_branch', '_changed_vs_base', '_render_units')}
    branch = ['feature']
    try:
        dh.ROOT, dh.RENDER_LEDGER, dh.THREAD_LEDGER = tmp, str(shared), str(thread)
        dh._current_branch = lambda: branch[0]
        dh._default_branch = lambda: 'main'
        dh._changed_vs_base = lambda: {'a.html'}
        dh._render_units = lambda: [('a.html', [], 'https://shared.example/a')]
        _b, on_branch = dh.stale()
        _b, trunk_flag = dh.stale(trunk=True)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            dh.record_published(['a.html@https://thread.example/a'])
        after = dh.stale()[1]
        rec = json.loads(thread.read_text()).get('a.html', {})
        shared_kept = json.loads(shared.read_text()) == {'a.html': dh._sha256(tmp / 'a.html')}
        branch[0] = 'main'
        _b, on_trunk = dh.stale()
        dh.THREAD_LEDGER = None
        branch[0] = 'feature'
        _b, unconfigured = dh.stale()
    finally:
        for k, v in saved.items():
            setattr(dh, k, v)
        shutil.rmtree(tmp, ignore_errors=True)
    cases = [
        ('a branch render with no thread artifact is unpublished',
         [r for r, _w in on_branch] == ['a.html']),
        ('--trunk checks the shared ledger, which is current', trunk_flag == []),
        ('recording on a branch writes the thread URL and hash',
         rec.get('url') == 'https://thread.example/a' and bool(rec.get('sha'))),
        ('after recording, the branch is current', after == []),
        ('the shared ledger is untouched by a branch record', shared_kept),
        ('on the trunk the shared ledger governs', on_trunk == []),
        ('no thread ledger configured: the shared ledger governs', unconfigured == []),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'thread renders never touch the shared ledger ({len(cases)} stated '
          f'cases)', not failed, '; '.join(failed))


def check_update_vendors_reports_what_it_says_it_lists():
    """Three smaller update-tool defects a consumer's update hit on
    2026-09-28, each pinned to the function that fixes it.

    - "(listed above)" listed nothing: the engine prints each diverged
      file's missing blocks, and Update Vendors kept only the Left-for-you
      line. diverged_details() carries them through.
    - A practice renamed upstream (go-merge -> go-update, status
      deduplicated at its own source) blocked the view sync until someone
      re-ran it with --allow-removals. _lost_practices() now files it as
      withdrawn upstream, and a slug its source simply stopped producing
      still blocks.
    - Every run rewrote MANIFEST.json's generated_at_utc and nothing else.
      write_manifest() keeps the stamp when the content is unchanged, and
      moves it when anything else changed."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_sync_views as psv
        import precedent_materialize as pm
    finally:
        sys.path.pop(0)
    cases = []
    out = ('DIVERGED: AGENTS.md "Two check levels" (line 88) has local edits, so '
           'refresh leaves it alone. It lacks 1 block(s):\n'
           '    templates/AGENTS.md.template:120 "run_all" -- add it\n'
           '        lacks: "A failing test the deep check ran"\n'
           'Left for you\n'
           '  - AGENTS.md "Two check levels": lacks 1 of its blocks (listed above)\n')
    det = getattr(pu, 'diverged_details', lambda o: {})(out)
    cases.append(('the missing sentences of a diverged section reach the report',
                  any('lacks: "A failing test' in l
                      for l in det.get('AGENTS.md "Two check levels"', []))))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-report-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')
    try:
        repo = tmp / 'r'
        subprocess.run(['git', 'init', '-q', str(repo)], env=env, check=True)
        (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': 'kept', 'source': 'precedent'},
            {'slug': 'renamed-away', 'source': 'precedent'},
            {'slug': 'went-missing', 'source': 'precedent'}]}), encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'm'], env=env, check=True)
        res = {'practices': {'kept': {'source': 'precedent'}},
               'retired': [{'slug': 'renamed-away', 'source': 'precedent',
                            'fm': {'status': 'deduplicated', 'in_force_at': 'kept'}}]}
        lost = psv._lost_practices(repo, res, [{'name': 'precedent'}], ())
        cases.append(('a slug deduplicated at its own source does not block the sync',
                      ('renamed-away', 'precedent') in lost.get('withdrawn_upstream', [])
                      and ('renamed-away', 'precedent') not in lost['blocking']))
        cases.append(('a slug its source simply stopped producing still blocks',
                      ('went-missing', 'precedent') in lost['blocking']))
        # Deleted outright by --withdraw-from-universal: no stub, only the
        # universal source's record line (2026-10-03, a consumer rehearsal:
        # the first sync after the ladder left universal refused on all of
        # its rules). CONTROL: went-missing, with no record line, still blocks.
        uni = tmp / 'universal'
        (uni / 'record').mkdir(parents=True)
        (uni / 'record' / 'WITHDRAWN_FROM_UNIVERSAL.md').write_text(
            '# Rules withdrawn\n\n- 2026-10-02: `deleted-on-purpose` withdrawn '
            'from universal, deliberately; in force only from the shared set '
            '`fx-ladder`, for the people who bring or declare it.\n'
            # The retired-name shape (2026-10-04: a consumer's update was
            # refused on plan-it and push-directly, which the record named
            # only in this shape).
            '- 2026-10-02: `retired-stub` (a retired name that forwarded to a '
            'ladder rule) withdrawn from universal, deliberately; kept as '
            'history in the shared set `fx-ladder`, beside the rule it '
            'forwards to. Approved by F.\n',
            encoding='utf-8')
        (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': 'deleted-on-purpose', 'source': 'precedent'},
            {'slug': 'retired-stub', 'source': 'precedent'},
            {'slug': 'went-missing', 'source': 'precedent'}]}), encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'commit', '-qam', 'm2'], env=env, check=True)
        lost = psv._lost_practices(repo, {'practices': {'kept': {}}, 'retired': []},
                                   [{'name': 'precedent', 'level': 'universal',
                                     'path': str(uni)}], ())
        cases.append(('a rule deleted from universal with a record line does not block',
                      ('deleted-on-purpose', 'precedent') in lost.get('withdrawn_upstream', [])
                      and ('deleted-on-purpose', 'precedent') not in lost['blocking']))
        cases.append(('a retired name recorded as kept as history does not block',
                      ('retired-stub', 'precedent') in lost.get('withdrawn_upstream', [])
                      and ('retired-stub', 'precedent') not in lost['blocking']))
        cases.append(('CONTROL: beside it, a rule with no record line still blocks',
                      ('went-missing', 'precedent') in lost['blocking']))
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(uni)}]}), encoding='utf-8')
        _went = psv._where_removed_went(repo, tmp / 'no-user-config.json',
                                        ['retired-stub'])
        cases.append(("a removed retired name is reported as history, never as "
                      "a rule in force",
                      'kept as history in `fx-ladder`' in _went['retired-stub'][1]
                      and 'in force' not in _went['retired-stub'][1]))
        import checkin as _ci
        cases.append(('the withdrawal record ships with the catalogue, and the '
                      'rest of record/ does not',
                      _ci._in_copy('record/WITHDRAWN_FROM_UNIVERSAL.md')
                      and not _ci._in_copy('record/anything-else.md')))

        mf = tmp / 'MANIFEST.json'
        write = getattr(pm, 'write_manifest', None)
        if write is None:
            cases.append(('precedent_materialize has write_manifest()', False))
        else:
            write(mf, {'generated_at_utc': '2026-01-01T00:00:00+00:00', 'practices': [1]})
            write(mf, {'generated_at_utc': '2026-09-28T09:00:00+00:00', 'practices': [1]})
            cases.append(('an unchanged snapshot keeps its generated_at_utc',
                          json.loads(mf.read_text())['generated_at_utc']
                          == '2026-01-01T00:00:00+00:00'))
            write(mf, {'generated_at_utc': '2026-09-28T09:00:00+00:00', 'practices': [2]})
            cases.append(('a changed snapshot gets the new generated_at_utc',
                          json.loads(mf.read_text())['generated_at_utc']
                          == '2026-09-28T09:00:00+00:00'))
    except (OSError, subprocess.CalledProcessError, KeyError, TypeError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_session_file_warning_does_not_count_against_its_ceiling():
    """The over-target warning precedent_session_practices.py writes into
    .precedent/SESSION_PRACTICES.md is left out when the file is measured
    against its ceiling, by precedent_check.py and session_load_trend.py
    alike, and nothing else is. precedent-individual, 2026-09-30: 5,155
    tokens without the warning, 5,211 with it, against a 5,200 ceiling, so
    every Promote refused on a file only the warning pushed over."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv
    import precedent_session_practices as psp
    import precedent_check as pc
    import session_load_trend as slt
    rel = '.precedent/SESSION_PRACTICES.md'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-session-warning-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        body = '# Practices in force here\n\n' + 'A rule a session reads. ' * 60 + '\n'
        n = bv._approx_tokens(body)
        (tmp / 'tools' / 'session_load_budgets.json').write_text(json.dumps(
            {'surfaces': {rel: {'target': n // 2, 'ceiling': n + 5}}}),
            encoding='utf-8')
        written = psp._with_target_warning(tmp, body)
        cases.append(('over target, the file carries the warning',
                      psp.TARGET_WARNING_MARK in written, written[:200]))
        cases.append(('and the warning alone takes it over its ceiling',
                      bv._approx_tokens(written) > n + 5,
                      bv._approx_tokens(written)))
        for name, measure in (('precedent_check', pc._as_measured),
                              ('session_load_trend', slt.as_measured)):
            got = measure(rel, written)
            cases.append((f'{name} measures it without the warning, exactly '
                          f'the content', got == body, got[:200]))
            cases.append((f'{name} leaves every other surface as it is',
                          measure('AGENTS.md', written) == written, ''))
        # One measurement, not two that happen to agree (2026-10-30).
        cases.append(('precedent_check measures with session_load_trend\'s '
                      'own functions and surface list',
                      pc._as_measured is slt.as_measured
                      and pc.SESSION_LOAD_SURFACES is slt.SURFACES, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n_, det) for n_, ok, det in cases if not ok]
    check('the session file\'s over-target warning never counts against its '
          'ceiling', not bad, '; '.join(f'{n_}: {det!r}' for n_, det in bad))


def check_session_practices_drop_what_agents_md_carries():
    """The session-practices file leaves out wrapping its repo's AGENTS.md
    already carries word for word -- and ONLY that.

    2026-09-24, precedent-individual: universal promoted one practice to
    resident and the set's .precedent/SESSION_PRACTICES.md went to 5,266
    tokens against a 5,200 ceiling. None of the overflow was the set's own
    text, and a good part of it was not practice text at all: the standing
    instruction's first two sentences and the omitted-index note, both
    already in the tracked AGENTS.md the same session loads. build_loader_block
    now takes `carried` and drops a sentence it finds there. The cases pin
    both directions, because a drop that fires on a near-match would silently
    take an instruction away from a repo whose AGENTS.md says something else.
    """
    import shutil, tempfile
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-carried-'))
    cases = []
    try:
        pdir = tmp / 'practices'
        pdir.mkdir()
        for slug, gates, applies in (('spoken', '[]', '[]'),
                                     ('gated', '["reply"]', '["**"]')):
            (pdir / f'{slug}.md').write_text(
                f'---\nslug: {slug}\ntitle: T\ntier: on-demand\nseverity: default\n'
                f'applies_to: {applies}\noccasion: "a person says {slug}"\n'
                f'gates: {gates}\nindex_clause: "the {slug} clause"\nchecked_by: null\n'
                f'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
                f'added: 2026-09-24\napproved_by: "harness fixture"\n---\n'
                f'## Rule\nR.\n\n## Why\nx\n\n## Story\n\n## Install\nx\n',
                encoding='utf-8')
        practices = bv.load_practices(pdir)
        full, _t, _c = bv.build_loader_block(practices, block_dir=tmp)
        instr = full.split('## Standing instruction', 1)[-1].split('<!--', 1)[0]
        note = next((l for l in full.splitlines()
                     if l.startswith('(More on-demand')), '')
        cases.append(('the fixture renders both pieces with nothing carried, so '
                      'the cases below test a drop and not an absence',
                      '## Standing instruction' in full and bool(note)))

        # Carried word for word, wrapped differently -- dropped.
        wrapped = '\n'.join(' '.join(instr.split()).replace('. ', '.\n')
                            .split('\n')) + '\n' + note.replace(' -- ', '\n-- ')
        b, _t, _c = bv.build_loader_block(practices, block_dir=tmp,
                                          carried=wrapped)
        cases.append(('a standing instruction AGENTS.md carries word for word '
                      '(however it wraps) is not repeated',
                      '## Standing instruction' not in b))
        cases.append(('...nor is the omitted-index note',
                      '(More on-demand' not in b))
        cases.append(('...while the practices themselves still render',
                      'the spoken clause' in b))

        # A DIFFERENT gate list: only the list is news.
        other = ' '.join(instr.split()).replace('precedent_gate.py reply',
                                                'precedent_gate.py merge')
        b, _t, _c = bv.build_loader_block(practices, block_dir=tmp,
                                          carried=other)
        tail = b.split('## Standing instruction', 1)[-1]
        cases.append(('where AGENTS.md names different gates, this block keeps '
                      'its own gate list and drops only the shared why',
                      'precedent_gate.py reply`.' in tail
                      and 'no path glob reaches those' not in tail
                      and 'Before starting work' not in tail))

        # Not carried at all -- nothing dropped.
        b, _t, _c = bv.build_loader_block(practices, block_dir=tmp,
                                          carried='# an AGENTS.md that says '
                                                  'something else entirely\n')
        cases.append(('a repo whose AGENTS.md lacks them keeps both, whole',
                      b == full))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] for c in cases if not c[1]]
    check(f'the session-practices block drops only what AGENTS.md carries word '
          f'for word ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_land_rebuilds_generated_content_without_a_header():
    """A land's conflict in generated content with no `generated_by:` header
    is rebuilt, and a refusal never calls generated content hand-written.

    2026-10-16: a land in a repository writing a book conflicted on a
    doc_sync block (<!--gen:word-count-->) inside its manuscript and on a
    generated .docx. Neither carries a header, so _generator_of missed both,
    and the land stopped saying "the same lines of hand-written text
    changed on both sides". Now: a conflict entirely inside gen blocks is
    resolved hunk by hunk to one side and doc_sync --write rewrites the
    block, keeping the other side's clean prose edits; a file the
    repository declares under "generated" in precedent.json is rebuilt by
    the command it names; and each refusal says which kind of stop it is.
    """
    import ast, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-gen-conflict-'))
    cases = []

    def repo(name, files, ours, theirs, extra=None):
        r = tmp / name
        r.mkdir()
        def git(*a, **kw):
            return fixture_git(r, *a, **kw)
        git('init', '-q')
        git('config', 'user.email', 'fixture@example.com')
        git('config', 'user.name', 'fixture')
        for rel, data in {**files, **(extra or {})}.items():
            f = r / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data if isinstance(data, bytes) else data.encode())
        git('add', '-A')
        git('commit', '-qm', 'base')
        git('checkout', '-qb', 'other')
        for rel, data in theirs.items():
            (r / rel).write_bytes(data if isinstance(data, bytes) else data.encode())
        git('commit', '-qam', 'theirs')
        git('checkout', '-q', '-')
        for rel, data in ours.items():
            (r / rel).write_bytes(data if isinstance(data, bytes) else data.encode())
        git('commit', '-qam', 'ours')
        merged = git('merge', '-q', 'other', allow_failure=True)
        return r, merged.returncode != 0

    def resolve(r):
        script = tmp / f'run-{r.name}.py'
        script.write_text(f"""
import sys
sys.path.insert(0, {str(ROOT / 'tools')!r})
import precedent_branches as pb
print(repr(pb._resolve_by_regenerating({str(r)!r}, say=lambda *a: None)))
""", encoding='utf-8')
        out = subprocess.run([sys.executable, str(script)], capture_output=True,
                             text=True)
        try:
            got = ast.literal_eval(out.stdout.strip())
        except (ValueError, SyntaxError):
            return None, out.stdout + out.stderr
        # An older return shape reads as a named failure, never an IndexError.
        return (got if isinstance(got, tuple) and len(got) == 3 else None,
                out.stdout + out.stderr)

    # A stand-in doc_sync: rewrites every word-count block with the count of
    # the words outside it, and records that it ran with --write.
    doc_sync = (
        "import pathlib, re, sys\n"
        "assert '--write' in sys.argv\n"
        "p = pathlib.Path(sys.argv[sys.argv.index('--only') + 1])\n"
        "t = p.read_text()\n"
        "words = len(re.sub(r'<!--gen:word-count-->.*?<!--/gen:word-count-->',"
        " '', t, flags=re.S).split())\n"
        "p.write_text(re.sub(r'(<!--gen:word-count-->\\n).*?(<!--/gen:word-count-->)',"
        " lambda m: m.group(1) + f'words: {words}\\n' + m.group(2), t, flags=re.S))\n")
    prose = ['Chapter one.'] + [f'Line {i} of the story.' for i in range(12)]

    def manuscript(count, first='Chapter one.', last='The end.'):
        body = [first] + prose[1:]
        return ('\n'.join(body[:6]) + '\n<!--gen:word-count-->\n'
                f'words: {count}\n<!--/gen:word-count-->\n'
                + '\n'.join(body[6:]) + f'\n{last}\n')

    try:
        # --- a conflict only inside a gen block --------------------------
        r, conflicted = repo('block', {'MANUSCRIPT.md': manuscript(10),
                                       'tools/doc_sync.py': doc_sync},
                             ours={'MANUSCRIPT.md': manuscript(11)},
                             theirs={'MANUSCRIPT.md': manuscript(
                                 12, last='The end, revised.')})
        cases.append(('the fixture merge conflicts inside the gen block',
                      conflicted, ''))
        got, err = resolve(r)
        text = (r / 'MANUSCRIPT.md').read_text(encoding='utf-8')
        cases.append(('a conflict only inside a doc_sync block is resolved, '
                      'not refused', got is not None and got[0] is True
                      and got[1] == ['MANUSCRIPT.md'], f'{got} {failure_detail(err, 300)}'))
        cases.append(("...keeping the other side's clean edit to the prose, "
                      'with no conflict markers left',
                      'The end, revised.' in text and '<<<<<<<' not in text,
                      failure_detail(text, 200)))
        cases.append(('...and doc_sync --write rewrote the block afresh',
                      f'words: {len(re.sub(r"<!--gen:word-count-->.*?<!--/gen:word-count-->", "", text, flags=re.S).split())}' in text,
                      failure_detail(text, 200)))

        # --- the same file, but a hunk in the prose -----------------------
        r, conflicted = repo('prose', {'MANUSCRIPT.md': manuscript(10),
                                       'tools/doc_sync.py': doc_sync},
                             ours={'MANUSCRIPT.md': manuscript(11, first='Ours.')},
                             theirs={'MANUSCRIPT.md': manuscript(12, first='Theirs.')})
        got, err = resolve(r)
        cases.append(('a hunk in the prose around a gen block still stops, as '
                      'hand-written text', conflicted and got is not None
                      and got[0] is False and got[1] == ['MANUSCRIPT.md']
                      and 'hand-written' in got[2], f'{got} {failure_detail(err, 300)}'))

        # --- an output the repository declares ----------------------------
        decl = json.dumps({'generated': [{'paths': ['output/*.docx'],
                                          'rebuild': ['tools/build_book.py']}]})
        build = ("import pathlib\n"
                 "pathlib.Path('output/book.docx').write_bytes(b'PK\\x03\\x04rebuilt')\n")
        r, conflicted = repo('declared', {'output/book.docx': b'PK\x03\x04\x85base',
                                          'precedent.json': decl,
                                          'tools/build_book.py': build},
                             ours={'output/book.docx': b'PK\x03\x04\x85ours'},
                             theirs={'output/book.docx': b'PK\x03\x04\x85theirs'})
        got, err = resolve(r)
        cases.append(('a declared generated .docx that conflicts is rebuilt by '
                      'the command precedent.json names',
                      conflicted and got is not None and got[0] is True
                      and (r / 'output' / 'book.docx').read_bytes()
                      == b'PK\x03\x04rebuilt', f'{got} {failure_detail(err, 300)}'))

        # --- a builder that writes dated names -------------------------
        # It deletes the conflicted file and writes today's: the new file
        # must be staged, or the land commits the deletion and loses the
        # rebuilt document (2026-10-17).
        dated = ("import pathlib\n"
                 "for f in pathlib.Path('output').glob('*.docx'):\n"
                 "    f.unlink()\n"
                 "pathlib.Path('output/book-2099-01-01.docx').write_bytes(b'PK\\x03\\x04dated')\n")
        r, conflicted = repo('dated', {'output/book-2026-10-16.docx': b'PK\x03\x04\x85base',
                                       'precedent.json': decl,
                                       'tools/build_book.py': dated},
                             ours={'output/book-2026-10-16.docx': b'PK\x03\x04\x85ours'},
                             theirs={'output/book-2026-10-16.docx': b'PK\x03\x04\x85theirs'})
        got, err = resolve(r)
        staged = fixture_git(r, 'diff', '--cached', '--name-status').stdout
        cases.append(('a builder that writes a dated name: the new file is staged '
                      'and the old one removed, never the deletion alone',
                      conflicted and got is not None and got[0] is True
                      and 'output/book-2099-01-01.docx' in staged
                      and 'conflict markers' not in str(got), f'{got} {staged} {failure_detail(err, 300)}'))

        # --- the harness timing list: both sides' times kept -------------
        tj = lambda secs, note: json.dumps({'measured': note, 'seconds': secs},
                                           indent=1) + '\n'
        r, conflicted = repo('times', {'tools/harness_check_times.json':
                                       tj({'check_a': 1.0}, 'base')},
                             ours={'tools/harness_check_times.json':
                                   tj({'check_a': 1.0, 'check_b': 2.0}, 'base; ours')},
                             theirs={'tools/harness_check_times.json':
                                     tj({'check_a': 1.0, 'check_c': 3.0}, 'base; theirs')})
        got, err = resolve(r)
        merged = json.loads((r / 'tools' / 'harness_check_times.json')
                            .read_text(encoding='utf-8'))
        cases.append(('a conflicted harness timing list keeps both sides\' times',
                      conflicted and got is not None and got[0] is True
                      and set(merged['seconds']) == {'check_a', 'check_b', 'check_c'}
                      and 'ours' in merged['measured'] and 'theirs' in merged['measured'],
                      f'{got} {merged} {failure_detail(err, 300)}'))

        # --- a declared rebuild that fails says so -----------------------
        r, conflicted = repo('failing', {'output/book.docx': b'PK\x03\x04\x85base',
                                         'precedent.json': decl,
                                         'tools/build_book.py': 'raise SystemExit(3)\n'},
                             ours={'output/book.docx': b'PK\x03\x04\x85ours'},
                             theirs={'output/book.docx': b'PK\x03\x04\x85theirs'})
        got, err = resolve(r)
        cases.append(('a rebuild that fails stops the land and says the rebuild '
                      'failed -- never "hand-written"',
                      conflicted and got is not None and got[0] is False
                      and 'could not rebuild' in got[2]
                      and 'hand-written' not in got[2], f'{got} {failure_detail(err, 300)}'))
    except FixtureSetupError as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a land rebuilds generated content that carries no header '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))


def check_materialize_bridges_loader():
    """tools/precedent_materialize.py — the deep-check session's own answer
    to spec/PHASE5_BRIEF.md's named gap: precedent_resolve.py is the only
    multi-source-aware tool; build_views.py/precedent_paths.py/
    precedent_gate.py/precedent_check.py all read a single local practices/
    directory. Proven for real (not just unit-tested here) against the two
    real private sets by that session; this harness case is the planted,
    repeatable version: two throwaway sources (one universal-shaped, one
    team-shaped) with a deliberate tools/checks/ filename collision AND a
    resident-budget overage, confirming both refuse, then a clean pair
    materializes and an unmodified build_views.py run against the output
    actually produces a resident block naming a practice from EACH source
    (not just proving files got copied)."""
    import shutil, subprocess, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-materialize-'))

    def write_practice(path, slug, rule, tier='on-demand', occasion='x',
                       checked_by='null'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "{occasion}"\n'
            f'gates: []\nindex_clause: "x"\nchecked_by: {checked_by}\ndefines: []\n'
            f'status: active\nsupersedes: []\noverrides: null\n'
            f'added: 2026-09-02\napproved_by: "harness, 2026-09-02"\n'
            f'source_practice_number: null\n---\n## Rule\n{rule}\n\n'
            f'## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')

    def write_check(path, body='VIOLATION: fixture\n'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'#!/usr/bin/env python3\nprint({body!r})\n', encoding='utf-8')

    cases = []
    try:
        uni, team = tmp / 'universal', tmp / 'team'
        # Both fixture practices CLAIM the same check filename, which is
        # what makes the collision below a real one: since 2026-09-06
        # materialize only vendors a script some resolved practice's
        # `checked_by` names, so an unclaimed pair would simply be dropped
        # and never collide.
        write_practice(uni / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture Rule.', tier='resident',
                        checked_by='"tools/checks/check_shared_name.py"')
        write_practice(team / 'practices' / 'team-fixture.md', 'team-fixture',
                        'A team fixture Rule.', tier='resident',
                        checked_by='"tools/checks/check_shared_name.py"')
        write_check(uni / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(team / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(uni / 'tools' / 'checks' / 'tests' / 'test_shared_name.sh',
                    body='fixture\n')
        # Claimed by nothing: a script whose practice was retired, or lost
        # its slug to a higher-precedence source. Must not be vendored --
        # precedent-team-repo-maintenance' retired `deep-check` shipped exactly
        # this into a consuming repo, where it registered under its own
        # filename and reported "not in force" forever.
        write_check(uni / 'tools' / 'checks' / 'check_orphan.py')
        write_check(uni / 'tools' / 'checks' / 'tests' / 'test_orphan.sh',
                    body='fixture\n')

        consumer = tmp / 'consumer'
        (consumer).mkdir()
        # Declared private: run directly, materialize refuses a team-level
        # source's text in a public (or undeclared) repo since 2026-10-17.
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                        {'level': 'team', 'name': 'precedent-team-fixture', 'path': str(team)}]
        }), encoding='utf-8')

        materialize_tool = str(ROOT / 'tools' / 'precedent_materialize.py')

        def run(*extra):
            r = subprocess.run([sys.executable, materialize_tool, '--out', str(consumer),
                                 '--repo', str(consumer), *extra],
                                capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        # --- a tools/checks/ filename collision across sources refuses -----
        rc, out = run()
        cases.append(('a checks/ filename collision across two sources refuses',
                      rc == 1 and 'collision' in out))

        # --- a same-named copy in a source whose practice does NOT claim it
        # is left behind, never a collision (2026-09-23: the universal tree
        # began carrying its own copies of the individual set's commit
        # checks, and the first sync in a migrating consumer refused) -------
        write_practice(uni / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture Rule.', tier='resident')
        rc, out = run()
        # Since 2026-10-08 the sync names which copy runs instead of calling
        # the other one unclaimed (check_sync_says_which_copy_of_a_claimed_check_runs).
        cases.append(('a copy only ANOTHER source claims is left behind, not a '
                      'collision', rc == 0 and 'collision' not in out
                      and 'check_shared_name.py runs from precedent-team-fixture' in out
                      and "precedent's copy is not vendored" in out))
        cases.append(('and the claiming source\'s copy is the one vendored',
                      (consumer / 'tools' / 'checks' / 'check_shared_name.py').is_file()))
        write_practice(uni / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture Rule.', tier='resident',
                        checked_by='"tools/checks/check_shared_name.py"')

        # --- an over-budget combined resident set refuses -------------------
        (team / 'tools' / 'checks' / 'check_shared_name.py').unlink()
        huge_rule = ' '.join(['word'] * 2000)
        write_practice(team / 'practices' / 'huge-fixture.md', 'huge-fixture',
                        huge_rule, tier='resident')
        rc, out = run()
        cases.append(('an over-budget combined resident set refuses to materialize',
                      rc == 1 and 'over' in out and 'budget' in out))

        # --- a clean pair materializes, and an UNMODIFIED build_views.py run
        # against the output actually shows both sources' resident practices --
        (team / 'practices' / 'huge-fixture.md').unlink()
        rc, out = run()
        materialized_ok = (rc == 0 and (consumer / 'MANIFEST.json').exists()
                            and (consumer / 'practices' / 'uni-fixture.md').exists()
                            and (consumer / 'practices' / 'team-fixture.md').exists())

        # --- every MANIFEST.json path (practices AND checks) actually
        # resolves to a file on disk -- regression case for a doubled
        # tools/checks/checks/ segment in checks[].path entries -------------
        manifest_paths_ok = False
        manifest_paths_detail = ''
        if materialized_ok:
            manifest = json.loads((consumer / 'MANIFEST.json').read_text(encoding='utf-8'))
            entries = ([('practices', e['slug'], f"practices/{e['slug']}.md")
                        for e in manifest.get('practices', [])]
                       + [('checks', e['path'], e['path'])
                          for e in manifest.get('checks', [])])
            missing = [label for _, label, rel in entries if not (consumer / rel).exists()]
            manifest_paths_ok = not missing
            manifest_paths_detail = f"missing on disk: {missing}" if missing else ''
        cases.append(('every MANIFEST.json practices[]/checks[] path resolves to a '
                      'real file on disk', manifest_paths_ok, manifest_paths_detail))

        cases.append(("a check script no resolved practice's checked_by names "
                      "is not vendored, and neither is its test",
                      materialized_ok
                      and not (consumer / 'tools' / 'checks' / 'check_orphan.py').exists()
                      and not (consumer / 'tools' / 'checks' / 'tests' / 'test_orphan.sh').exists()))
        cases.append(('a claimed check script and its test ARE vendored',
                      materialized_ok
                      and (consumer / 'tools' / 'checks' / 'check_shared_name.py').exists()
                      and (consumer / 'tools' / 'checks' / 'tests' / 'test_shared_name.sh').exists()))

        (consumer / 'tools').mkdir(parents=True, exist_ok=True)
        # summary_text.py since 2026-09-25: build_views.py imports it at
        # module level, as it does split_practices.py.
        for f in ('build_views.py', 'split_practices.py', 'summary_text.py'):
            shutil.copyfile(ROOT / 'tools' / f, consumer / 'tools' / f)
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'build_views.py')],
                            capture_output=True, text=True, cwd=str(consumer))
        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8') \
            if (consumer / 'AGENTS.md').exists() else ''
        cases.append(('a clean materialize + unmodified build_views.py run produces '
                      "a resident block naming BOTH sources' practices, not just one",
                      materialized_ok and r.returncode == 0
                      and 'uni-fixture' in agents_text and 'team-fixture' in agents_text))

        # --- the SAME scenario again, but run tools/build_views.py IN PLACE
        # (no copy) with --repo pointed at the fixture, instead of copying
        # the script into the fixture's own tools/ first. Before build_views
        # accepted --repo, this was the only way to test it against content
        # that isn't its own -- ROOT was always computed as two folders up
        # from wherever the running copy physically sat, so a script that
        # never moved could never be pointed elsewhere. This case is kept
        # ALONGSIDE the copy-based case above, not in place of it: a
        # consuming repo's own vendored copy (the documented, still-current
        # INSTALL.md model) is the copy-based shape, and a future vendored
        # engine invoked with --repo (this request's own stated motivation)
        # is this one -- both invocation styles have to keep working.
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r2 = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                              '--repo', str(consumer), '--agents-only'],
                             capture_output=True, text=True)
        agents_text2 = (consumer / 'AGENTS.md').read_text(encoding='utf-8') \
            if (consumer / 'AGENTS.md').exists() else ''
        cases.append(("the real, un-relocated build_views.py run with --repo (no copy) "
                      "produces a resident block naming BOTH sources' practices too",
                      materialized_ok and r2.returncode == 0
                      and 'uni-fixture' in agents_text2 and 'team-fixture' in agents_text2))
        # The GENERATED test driver. tools/checks/tests/run_all.sh is the one
        # file this tool writes rather than copies: every source ships its own,
        # so copying would force a winner, but `deep-check` requires the file to
        # exist -- so before 2026-09-06 no consuming repo could satisfy that
        # practice, and its far more useful half (each check has a test; no test
        # outlives its check) never ran, because the check returns early on the
        # missing file. Twelve properties, each with its own way of regressing:
        # four about the generated driver itself, then eight about the 2026-09-12
        # change that stopped REPORTING the replaced source copy as a dropped
        # file and started reporting the one thing a person can act on -- a
        # source driver that does not declare itself local.
        run_all = consumer / 'tools' / 'checks' / 'tests' / 'run_all.sh'
        run_all_text = run_all.read_text(encoding='utf-8') if run_all.is_file() else ''
        cases.append(('the test driver is generated into the consumer even though '
                      'no source file was copied for it',
                      materialized_ok and run_all.is_file()))
        # deep-check greps for this exact glob; a driver naming specific tests
        # would pass a bare existence test while silently skipping new ones.
        cases.append(('the generated driver globs test_*.sh rather than naming '
                      'tests, so it runs whatever THIS repo materialized',
                      'test_*.sh' in run_all_text))
        # An unrecorded file is indistinguishable from a hand-dropped orphan to
        # a consuming repo's own orphan detection, which reads MANIFEST.json.
        manifest_path = consumer / 'MANIFEST.json'
        recorded = []
        if manifest_path.is_file():
            recorded = [c for c in json.loads(
                manifest_path.read_text(encoding='utf-8')).get('checks', [])
                if c.get('path', '').endswith('tests/run_all.sh')]
        cases.append(('the generated driver is recorded in MANIFEST.json, so a '
                      "consumer's orphan detection does not read it as hand-dropped",
                      len(recorded) == 1))
        # A repo that materialized no tests leaves the glob unexpanded; without
        # the guard the driver runs a file literally named test_*.sh and reports
        # a failure that is really an empty set.
        empty_dir = tmp / 'empty-driver'
        empty_dir.mkdir(parents=True, exist_ok=True)
        (empty_dir / 'run_all.sh').write_text(run_all_text or 'exit 1\n', encoding='utf-8')
        r3 = subprocess.run(['bash', 'run_all.sh'], cwd=str(empty_dir),
                            capture_output=True, text=True)
        cases.append(('the generated driver exits 0 in a repo that materialized '
                      'no tests, rather than failing on the unexpanded glob',
                      bool(run_all_text) and r3.returncode == 0))

        # --- the source's OWN driver: replaced, not dropped, and asked to
        # say so. Before 2026-09-12 a source's run_all.sh fell into the
        # generic `skipped` bucket and printed "not a per-check file, not
        # vendored" on every sync forever -- true about the source's copy,
        # and read by more than one person as "so this repo has no driver",
        # which cost a cross-repo investigation to settle. The line is gone;
        # what replaced it names a source whose driver does not declare
        # itself local, and goes silent once the source declares. `helper.py`
        # is the control: a file that really WAS dropped must still report
        # under the old wording, or this change has simply muted a real
        # signal along with the misleading one. ---------------------------
        #
        # These two runs own their SOURCE SET, which the cases above do not
        # need to: precedent.json names two fixture sources, but the resolver
        # also picks up whatever individual source ~/.config/precedent names,
        # and this container's real one ships an undeclared driver. Left
        # inherited, the silence case can never pass no matter what the
        # fixture does -- it would be measuring this container, which is
        # practices/fixture-owns-its-state.md exactly. HOME is redirected to
        # a directory the fixture made; CLAUDE_CODE_REMOTE is dropped as well
        # because precedent_resolve's self-heal CLONES the individual source
        # into whatever HOME it is handed, but only in a hosted session, so
        # unsetting it is what keeps the fixture HOME actually empty.
        fixture_home = tmp / 'driver-home'
        fixture_home.mkdir(parents=True, exist_ok=True)
        iso_env = {k: v for k, v in os.environ.items()
                   if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
        iso_env['HOME'] = str(fixture_home)

        def run_isolated():
            r = subprocess.run([sys.executable, materialize_tool,
                                 '--out', str(consumer), '--repo', str(consumer)],
                                capture_output=True, text=True, env=iso_env)
            return r.returncode, r.stdout + r.stderr

        team_checks = team / 'tools' / 'checks'
        write_check(team_checks / 'helper.py')
        team_driver = team_checks / 'tests' / 'run_all.sh'
        team_driver.parent.mkdir(parents=True, exist_ok=True)
        team_driver.write_text('#!/bin/bash\n# a local driver\nexit 0\n',
                               encoding='utf-8')

        rc4, out4 = run_isolated()
        skip_line4 = next((ln for ln in out4.splitlines()
                           if 'not a per-check file, not vendored' in ln), '')
        marker = 'LOCAL DRIVER -- not shipped to consumers'
        cases.append(("a source driver that does not declare itself local warns, "
                      "naming that source",
                      'does not say so' in out4
                      and 'precedent-team-fixture' in out4))
        cases.append(('that warning states the remedy -- the exact marker line '
                      'to add -- rather than only naming the problem',
                      marker in out4))
        cases.append(('the undeclared driver still MATERIALIZES: it warns, it '
                      'does not fail, and the generated driver is still written',
                      rc4 == 0 and run_all.is_file()))
        cases.append(("a file that really was dropped still reports under the "
                      "existing 'not a per-check file, not vendored' wording",
                      'helper.py' in skip_line4))
        cases.append(('that wording no longer names run_all.sh, which is '
                      'replaced rather than dropped',
                      bool(skip_line4) and 'run_all.sh' not in skip_line4))

        team_driver.write_text(f'#!/bin/bash\n# {marker}\nexit 0\n',
                               encoding='utf-8')
        rc5, out5 = run_isolated()
        cases.append(('the warning goes SILENT once the source declares its '
                      'driver local -- silence is the compliance signal',
                      rc5 == 0 and 'does not say so' not in out5))
        cases.append(('the generated driver is still written for a source that '
                      'declares its own',
                      rc5 == 0 and run_all.is_file()))
        # If this fails, the silence case above was measuring this container's
        # own individual source rather than the fixture's two sources, and
        # every verdict either way is worthless.
        cases.append(('the isolated runs really did own their source set -- '
                      'nothing cloned an individual source into the fixture HOME',
                      not any(fixture_home.iterdir())))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_materialize.py bridges the loader ({len(cases)} stated cases: '
          f'a checks/ collision refuses, an over-budget combined set refuses, a clean '
          f"materialize feeds both a copied and an in-place --repo build_views.py "
          f"both sources' content, and the test driver is generated rather than "
          f'copied -- present, globbing, recorded in the manifest, exiting 0 '
          f'on an empty test set, and warning only about a source driver that '
          f'does not declare itself local, silently once it does)',
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_sync_refuses_to_lose_a_recorded_practice():
    """A sync will not silently drop a rule the repository already published.

    The incident, 2026-09-07: promoting two practices out of a shared set into
    the universal catalogue left every consumer pinned before the promotion
    with them in NEITHER source, so its next sync deleted both. `--check`
    named them; a real sync rmtree's practices/ and says nothing.

    THE BASELINE IS THE COMMITTED MANIFEST, and that is the whole design. A
    first attempt compared the working tree against the plan and had to be
    reverted -- it fired on a public repo withholding by design, on a sync
    already carrying --allow-missing-sources, and on a fixture re-syncing
    after its sources changed. "The tree differs from the plan" is true
    constantly. "This repository committed a catalogue containing rule X and
    X is about to vanish" is narrow enough to refuse on. The four cases below
    are the four that distinction has to get right.
    """
    import tempfile, shutil
    sync_tool = str(ROOT / 'tools' / 'precedent_sync_views.py')

    def _repo(tmp, extra_source=True):
        repo, team = tmp / 'c', tmp / 'precedent-team-x'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'team-x-rule.md').write_text(
            '---\nslug: team-x-rule\ntitle: The rig is used\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "changing firmware"\n'
            'index_clause: "use the rig"\nstatus: active\n---\n'
            '## Rule\nUse the rig.\n\n## Story\nIt drifted.\n', encoding='utf-8')
        # A SECOND practice, so removing the first does not empty the source.
        # An existing guard already refuses a source that went completely
        # empty ("a sync would quietly drop that whole catalogue"), and the
        # first version of this fixture tripped that one instead of the one
        # under test -- a fixture proving the wrong thing passes just as
        # confidently as one proving the right thing.
        (team / 'practices' / 'team-x-keeper.md').write_text(
            '---\nslug: team-x-keeper\ntitle: The bench is logged\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "logging bench time"\n'
            'index_clause: "log the bench"\nstatus: active\n---\n'
            '## Rule\nLog it.\n\n## Story\nIt was not logged.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# C\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
        srcs = [{'level': 'universal', 'name': 'precedent',
                 'path': 'precedent/universal'}]
        if extra_source:
            srcs.append({'level': 'team', 'name': 'precedent-team-x',
                         'path': str(team)})
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'visibility': 'private', 'sources': srcs}), encoding='utf-8')
        user = tmp / 'u.json'
        user.write_text(json.dumps({'format_version': 1}), encoding='utf-8')
        for c in (['init', '-q', '-b', 'main'],
                  ['config', 'user.email', 'harness@example.com'],
                  ['config', 'user.name', 'Harness']):
            subprocess.run(['git', '-C', str(repo)] + c, capture_output=True)
        return repo, team, user

    def _sync(repo, user, *flags):
        return subprocess.run(
            [sys.executable, sync_tool, '--repo', str(repo),
             '--user-config', str(user)] + list(flags),
            capture_output=True, text=True)

    def _commit(repo):
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'catalogue'],
                       capture_output=True)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 1. NO COMMITTED MANIFEST -- a fresh install has nothing to lose.
        repo, team, user = _repo(tmp)
        r = _sync(repo, user)
        cases.append(('a repo with no committed manifest syncs freely',
                      r.returncode == 0))

        # 2. The real case: publish a catalogue, then the source stops
        #    producing the rule while STILL being declared.
        _commit(repo)
        (team / 'practices' / 'team-x-rule.md').unlink()
        r = _sync(repo, user)
        cases.append(('a recorded practice vanishing from a still-declared '
                      'source REFUSES', r.returncode != 0))
        cases.append(('and it names the slug and its source',
                      'team-x-rule' in r.stderr and 'precedent-team-x' in r.stderr))
        cases.append(('and the practice file survives the refusal',
                      (repo / 'practices' / 'team-x-rule.md').exists()))

        # 3. --allow-removals is the deliberate override.
        r = _sync(repo, user, '--allow-removals')
        cases.append(('--allow-removals permits it',
                      r.returncode == 0
                      and not (repo / 'practices' / 'team-x-rule.md').exists()))

        # 4. DROPPING the source: refused too, since 2026-09-14. This used
        #    to assert returncode == 0 on the reasoning that a drop is a
        #    decision somebody just made -- and the matching is by NAME, so
        #    a RENAME is indistinguishable from a drop here and would have
        #    been written under the same reassuring message. Case 5 is the
        #    one that could not be told apart; this one is its twin.
        repo2, team2, user2 = _repo(tmp / 'b')
        _sync(repo2, user2); _commit(repo2)
        cfg = json.loads((repo2 / 'precedent.json').read_text())
        cfg['sources'] = [s for s in cfg['sources'] if s['level'] != 'team']
        (repo2 / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        r = _sync(repo2, user2)
        cases.append(('an undeclared recorded source REFUSES rather than '
                      'deleting', r.returncode != 0))
        # practice: control-asserts-which-failure -- a non-zero exit proves
        # nothing about WHICH guard fired, and the fixture above can trip at
        # least two others. Assert the three states this message names.
        cases.append(('and the refusal names all three states it cannot '
                      'tell apart',
                      all(w in r.stderr for w in ('DROPPED', 'RENAMED',
                                                  'RETIRED'))))
        cases.append(('and it says which practices are at stake',
                      'team-x-rule' in r.stderr))
        cases.append(('and the practice files survive the refusal',
                      (repo2 / 'practices' / 'team-x-rule.md').exists()))
        r = _sync(repo2, user2, '--allow-removals')
        cases.append(('--allow-removals proceeds once you know which it is',
                      r.returncode == 0
                      and not (repo2 / 'practices' / 'team-x-rule.md').exists()))

        # 5. THE INCIDENT ITSELF, and it takes two changes to reproduce.
        #    A rename ALONE deletes nothing: the source still resolves and
        #    still produces the same slugs, so nothing is lost and the guard
        #    has no occasion to fire -- asserted below, because a fixture
        #    that cannot tell a safe rename from a dangerous one would make
        #    this whole case unfalsifiable. The damage needs a rename PLUS a
        #    practice that really does go: then the slug is lost, the
        #    recorded source name matches nothing, and before 2026-09-14
        #    that was written and reported as the person having dropped the
        #    source on purpose. The 2026-09-14 removals were correct only
        #    because the four practices were retired upstream as well.
        repo3, team3, user3 = _repo(tmp / 'c2')
        _sync(repo3, user3); _commit(repo3)
        cfg = json.loads((repo3 / 'precedent.json').read_text())
        for s in cfg['sources']:
            if s['level'] == 'team':
                s['name'] = 'precedent-team-x-renamed'
        (repo3 / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        r = _sync(repo3, user3)
        cases.append(('a rename ALONE loses nothing and is not refused',
                      r.returncode == 0
                      and (repo3 / 'practices' / 'team-x-rule.md').exists()))
        _commit(repo3)
        (team3 / 'practices' / 'team-x-rule.md').unlink()
        r = _sync(repo3, user3)
        cases.append(('a rename PLUS a real removal refuses instead of '
                      'deleting under a dropped-source message',
                      r.returncode != 0))
        cases.append(('and the practice survives that refusal',
                      (repo3 / 'practices' / 'team-x-rule.md').exists()))

    failed = [n for n, ok in cases if not ok]
    check(f'a sync refuses to lose a practice the committed manifest records '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_todo_migrate_reads_a_consumers_list():
    """todo_migrate.py carries a consumer's own TODO.md across, not only the
    one this repository migrated.

    2026-10-06, a consumer migrating its list hit three things at once: every
    item older than 2026-09-06 was told it "predates anchor tracking (every
    anchor was retrofitted 2026-09-06)" -- this repository's history, in a
    file that never had an anchor; every root-relative link in an item broke
    when the item moved into todo/; and two closed bullet shapes,
    `- [x] ~~**Title**~~` and a plain `- [x] text`, parsed as nothing.
    Unit-level, on a git fixture whose commit dates the cases choose."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import todo_migrate as tm
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='todo-migrate-consumer-'))
    saved_today = tm.TODAY
    try:
        repo = tmp / 'proj'
        repo.mkdir()

        def git(*a, date=None):
            env = dict(os.environ)
            if date:
                env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = f'{date}T12:00:00+00:00'
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                            '-c', 'user.name=harness',
                            '-c', 'user.email=harness@example.com', *a],
                           cwd=str(repo), capture_output=True, check=True, env=env)

        def commit(text, date):
            (repo / 'TODO.md').write_text(text, encoding='utf-8')
            git('add', '-A')
            git('commit', '-qm', 'todo', date=date)

        git('init', '-q')
        commit('# TODO\n\n- [ ] **Plain old item** -- no anchor ever.\n\n'
               '- **Retrofitted item** -- anchored later.\n', '2026-01-01')
        commit('# TODO\n\n- [ ] **Plain old item** -- no anchor ever.\n\n'
               '- <a id="retrofitted-item"></a>**Retrofitted item** -- '
               'anchored later.\n\n'
               '- <a id="born-anchored"></a>**Born anchored** -- one commit.\n',
               '2026-02-01')
        text = ('# TODO\n\n- [ ] **Plain old item** -- no anchor ever. See '
                '[the plan](spec/PLAN.md), [here](#top), '
                '[web](https://example.com), [up](../x.md), [root](/y.md).\n\n'
                '- <a id="retrofitted-item"></a>**Retrofitted item** -- '
                'anchored later.\n\n'
                '- <a id="born-anchored"></a>**Born anchored** -- one commit.\n\n'
                '- [ ] **Never committed item** -- not in any history.\n\n'
                '- [x] ~~**Struck closed item**~~ -- finished.\n\n'
                '- [x] A plain closed line\n')
        (repo / 'TODO.md').write_text(text, encoding='utf-8')
        tm.TODAY = '2026-10-06'
        items = tm.parse_todo_items(text)
        plan = {it.title: (body, floor) for it, _p, _fm, body, _n, floor
                in tm.build_plan(items, repo, 'TODO.md', 'todo')}
        by_title = {it.title: it for it in items}

        def notes(body):
            return body.split('## Notes', 1)[-1]

        body, floor = plan.get('Plain old item', ('', None))
        cases.append(('an item with no anchor, found in history, is not '
                      'called a floor and names no anchor retrofit',
                      floor is False and 'anchor' not in notes(body)
                      and '2026-09-06' not in body, failure_detail(body, 300)))
        cases.append(('a root-relative link gains ../ as the item moves '
                      'into todo/', '(../spec/PLAN.md)' in body, body[:300]))
        cases.append(('#anchors, URLs, ../ and /root links are left alone',
                      all(t in body for t in ('(#top)', '(https://example.com)',
                                              '(../x.md)', '(/y.md)'))
                      and '../../' not in body and '(..//' not in body,
                      body[:300]))
        body, floor = plan.get('Retrofitted item', ('', None))
        cases.append(('an anchor added to an older item writes the '
                      'retrofit note, with no fixed date',
                      floor is True and 'predates its anchor' in body
                      and '2026-09-06' not in body, failure_detail(body, 300)))
        body, floor = plan.get('Born anchored', ('', None))
        cases.append(('CONTROL: an item anchored from its first commit is '
                      'not a floor', floor is False, failure_detail(body, 300)))
        body, floor = plan.get('Never committed item', ('', None))
        cases.append(('an item found nowhere in history gets the neutral '
                      'floor note, naming no anchor',
                      floor is True and 'not found' in notes(body)
                      and 'anchor' not in notes(body), failure_detail(body, 300)))
        struck = by_title.get('Struck closed item')
        cases.append(('`- [x] ~~**Title**~~` is a closed item of its own',
                      struck is not None and struck.checked is True,
                      sorted(by_title)))
        plain = by_title.get('A plain closed line')
        cases.append(('`- [x] text` is a closed item of its own',
                      plain is not None and plain.checked is True,
                      sorted(by_title)))
        cases.append(('CONTROL: the open checkbox item stays open',
                      by_title.get('Plain old item') is not None
                      and by_title['Plain old item'].checked is False, ''))
        cases.append(('every item parsed, none swallowed', len(items) == 6,
                      sorted(by_title)))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        tm.TODAY = saved_today
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'todo_migrate.py carries a consumer\'s list ({len(cases)} stated '
          f'cases)', not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_todo_migrate_needs_a_migrated_item():
    """THE INCIDENT (2026-09-28, the same migration rehearsal as the case
    above). todo_migrate.py failed, build_todo_index.py then wrote its index
    over an empty todo/, and todo-migrate-available-but-unused went green:
    it asked only whether todo/ existed. Zero items had moved and every
    old-format bullet was still in TODO.md.

    Unit-level: the subject is one tree check's verdict over three layouts,
    and a whole pipeline run would only add minutes to reach it."""
    import tempfile, shutil as _shutil, json as _json
    import precedent_check as pc
    if not hasattr(pc, '_todo_migrate_available_but_unused'):
        not_applicable('todo-migrate needs a migrated item',
                       'the check is not present in this precedent_check.py')
        return

    class _Ctx:
        def read(self, rel):
            try:
                return (pc.ROOT / rel).read_text(encoding='utf-8')
            except OSError:
                return ''

    old_root, old_manifest = pc.ROOT, pc._ENGINE_MANIFEST
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-todo-mig-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'todo_migrate.py').write_text('# vendored\n')
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps({'kind': 'consumer'}))
        (tmp / 'TODO.md').write_text(
            '# Repo TODO\n\n- [ ] **An old-format item, never migrated.**\n')
        (tmp / 'todo').mkdir()
        (tmp / 'todo' / 'TODO.md').write_text('# Open items\n\n(none)\n')
        (tmp / 'todo' / 'CLOSED.md').write_text('# Closed items\n')
        pc.ROOT, pc._ENGINE_MANIFEST = tmp, None

        def verdict():
            return [str(f) for f in pc._todo_migrate_available_but_unused(_Ctx())]

        cases.append(('a todo/ holding only the generated index, with the '
                      'old bullets still in TODO.md, fires',
                      bool(verdict()), verdict()))
        (tmp / 'todo' / 'todo-2026-09-28-an-item.md').write_text('# item\n')
        cases.append(('CONTROL: one migrated todo/todo-*.md item clears it',
                      verdict() == [], verdict()))
        (tmp / 'todo' / 'todo-2026-09-28-an-item.md').unlink()
        (tmp / 'TODO.md').write_text('# TODO has moved\n\nSee todo/.\n')
        cases.append(('CONTROL: TODO.md as the redirect stub clears it',
                      verdict() == [], verdict()))
    finally:
        pc.ROOT, pc._ENGINE_MANIFEST = old_root, old_manifest
        _shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'todo-migrate-available-but-unused wants a migrated item, not an '
          f'empty todo/ ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d}' for n, d in bad))

def check_doc_lint_exempts_links_in_a_mirrored_tree():
    """A vendored catalogue's relative links are not this repo's to fix, so
    they never fail its gate -- and since 2026-10-08 doc_lint reports them as
    upstream's rather than skipping them (it did not report them at all from
    2026-09-14). The repo's own broken link in the same run still fails.

    Both directions in one fixture, because the failure mode of a blanket
    exemption is silence in the half that matters (practice:
    control-asserts-which-failure). An INSTALL.md §0 install copies the
    catalogue to precedent/universal/practices/ verbatim, so every
    `../tools/...` in a practice file lands nowhere -- dozens of findings
    per run, in files the adopter must not edit.
    """
    import shutil, tempfile, json as _json

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-mirror-lint-'))
    try:
        repo = tmp / 'repo'
        repo.mkdir()
        shutil.copytree(ROOT / 'tools', repo / 'tools')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': 'precedent/universal'}]}), encoding='utf-8')
        mirror = repo / 'precedent' / 'universal' / 'practices'
        mirror.mkdir(parents=True)
        (mirror / 'some-practice.md').write_text(
            # The heading skip is deliberate: with its links exempt, a
            # mirror file carrying nothing else would produce no findings
            # at all, and the third case below could not tell "scanned,
            # links exempt" from "never scanned".
            '# X\n\n### Skipped level\n\nSee [the engine](../tools/very_deep_check.py).\n',
            encoding='utf-8')
        # A vendored TEMPLATE: its links name the tree it is instantiated
        # into, as upstream's own check reads them (templates/ under the
        # source root, not this repo's). Found 2026-10-08: a consumer's
        # Update Vendors reported a vendored template's `gotchas/` as broken
        # on every run, while upstream's check of the same line passed.
        tpl = repo / 'precedent' / 'universal' / 'templates' / 'proj'
        tpl.mkdir(parents=True)
        (tpl / 'AGENTS.md').write_text(
            '# Agents\n\nTraps live under [gotchas/](gotchas/).\n', encoding='utf-8')
        (repo / 'docs').mkdir()
        (repo / 'docs' / 'mine.md').write_text(
            '# Mine\n\nSee [nothing](../nowhere/absent.md).\n', encoding='utf-8')
        for args in (['init', '-q'], ['add', '-A']):
            subprocess.run(['git', '-C', str(repo), *args], check=True,
                           capture_output=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.email=h@example.com',
                        '-c', 'user.name=harness', 'commit', '-qm', 'baseline'],
                       check=True, capture_output=True)
        r = subprocess.run([sys.executable, str(repo / 'tools' / 'doc_lint.py'),
                            '--all'], capture_output=True, text=True, cwd=str(repo))
        out = r.stdout + r.stderr
        broken = [l for l in out.splitlines() if '(no such file)' in l]
        # 2026-10-08: reported, never hidden -- under the upstream note, and
        # never failing this repo (Morgan: checks stop skipping vendored
        # files silently).
        cases_out = out
        check('doc_lint REPORTS a broken relative link inside a mirrored tree '
              'as upstream\'s to fix, instead of skipping it silently',
              any('precedent/universal/' in l for l in broken)
              and "upstream's to fix" in out and 'Prompt Please' in out,
              '; '.join(broken)[:300])
        (repo / 'docs' / 'mine.md').write_text('# Mine\n\nNothing broken.\n',
                                               encoding='utf-8')
        r2 = subprocess.run([sys.executable, str(repo / 'tools' / 'doc_lint.py'),
                             'precedent/universal/practices/some-practice.md'],
                            capture_output=True, text=True, cwd=str(repo))
        check('...and a mirrored tree\'s broken link never fails this repo\'s gate',
              r2.returncode == 0 and 'precedent/universal/' in (r2.stdout + r2.stderr),
              f'exit {r2.returncode}: {failure_detail(r2.stdout + r2.stderr, 300)}')
        check('a vendored template\'s link to a path its instance will hold '
              '(`gotchas/`) is read as upstream reads it, not reported as broken',
              not any('templates/proj/AGENTS.md' in l for l in broken)
              and any('some-practice.md' in l for l in broken),
              '; '.join(broken)[:300])
        check('doc_lint still reports the repo\'s OWN broken relative link '
              'in the same run',
              any('docs/mine.md' in l for l in broken),
              '; '.join(broken)[:300] or 'no broken-link findings at all')
        check('a mirrored tree is still scanned for everything else (the '
              'exemption is the link check alone)',
              'precedent/universal/practices/some-practice.md' in out
              or 'vendored upstream tree' in out,
              failure_detail(out.strip(), 300))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_doc_sync_reads_a_consumers_own_pairs():
    """doc_sync.py is vendored, and its PAIRS list is BestPractice's. In a
    consumer it told the session to "replace PAIRS in tools/doc_sync.py",
    an edit the engine refresh then refuses (2026-09-30, a consumer's
    Update Vendors). Planted consumer (a tools/ENGINE_MANIFEST.json beside
    the copied tool). Discriminating cases: with no pairs file there is
    nothing to sync and no advice to edit the vendored file; a pairs file
    is what it reads, so one naming an absent document says so and points
    at that file; a malformed one fails loudly."""
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='doc-sync-consumer-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)
        for n in ('doc_sync.py', 'generated_blocks.py'):
            shutil.copy2(ROOT / 'tools' / n, tmp / 'tools' / n)
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            '{"kind": "consumer"}\n', encoding='utf-8')

        def run():
            r = subprocess.run([sys.executable, 'tools/doc_sync.py'],
                               cwd=str(tmp), capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr
        rc, out = run()
        cases.append(('THE CASE THIS EXISTS FOR: with no pairs file, nothing '
                      'to sync and no advice to edit the vendored tool',
                      rc == 0 and 'tools/doc_sync.py with' not in out
                      and 'NOT APPLICABLE' not in out, f'rc={rc} {failure_detail(out, 300)}'))
        (tmp / 'tools' / 'doc_sync_pairs.json').write_text(json.dumps(
            {'pairs': [['docs/absent.md', 'table', 'tools/model.py']]}),
            encoding='utf-8')
        rc, out = run()
        cases.append(('the repo\'s own pairs file is what it reads',
                      'docs/absent.md' in out
                      and 'tools/doc_sync_pairs.json' in out, failure_detail(out, 300)))
        (tmp / 'tools' / 'doc_sync_pairs.json').write_text(
            json.dumps({'pairs': [['only-two', 'parts']]}), encoding='utf-8')
        rc, out = run()
        cases.append(('a malformed pairs file fails loudly',
                      rc != 0 and 'each pair is' in out, f'rc={rc} {failure_detail(out, 200)}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'doc_sync reads a consumer\'s own pairs, never asks it to edit '
          f'the vendored tool ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_sets_carry_the_todo_and_gotcha_index_tools():
    """A practice set keeps its own todo/ and gotchas/, so the engine every
    set carries has the tools that rebuild their generated indexes.
    build_todo_index.py moved into ENGINE_FILES on 2026-09-19 when sets
    turned out to keep todo items; build_gotcha_index.py stayed
    consumer-only until 2026-10-19, when a private set was made with nine
    gotchas and a generated gotchas/INDEX.md its own engine could not
    rebuild, so its generated-files check could never pass. Fails on the
    old list."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    missing = [t for t in ('build_todo_index.py', 'build_gotcha_index.py')
               if t not in pve.ENGINE_FILES]
    twice = [t for t in ('build_todo_index.py', 'build_gotcha_index.py')
             if pve.CONSUMER_ENGINE_FILES.count(t) != 1]
    return (not missing and not twice, '2 tools',
            f'not in ENGINE_FILES: {missing}; not exactly once for a consumer: {twice}')


def _codex_hooks_file_problems(data):
    """-> [str] every way `data` would not parse as a Codex hooks.json.

    Mirrors codex-rs/config/src/hook_config.rs at openai/codex main 46fdd5e
    (read 2026-09-28): HooksFile is deny_unknown_fields with only
    `description` and `hooks`, events are the twelve names in
    codex-rs/hooks/src/lib.rs, and a command handler carries `type`,
    `command` and optional `timeout` (seconds), `statusMessage`, `async`,
    `commandWindows`, `additionalContextLimit`. A problem here is a file
    Codex would refuse whole, with a warning nobody reads."""
    problems = []
    extra = sorted(set(data) - {'description', 'hooks'})
    if extra:
        problems.append('top-level keys Codex rejects: ' + ', '.join(extra))
    known = {'type', 'command', 'timeout', 'statusMessage', 'async',
             'commandWindows', 'command_windows', 'additionalContextLimit'}
    for event, groups in (data.get('hooks') or {}).items():
        if event not in _CODEX_HOOK_EVENTS:
            problems.append(f'unknown event {event!r}')
            continue
        for group in groups:
            for h in group.get('hooks', []):
                if h.get('type') != 'command' or not h.get('command'):
                    problems.append(f'{event}: a handler that is not a command: {h!r}')
                bad = sorted(set(h) - known)
                if bad:
                    problems.append(f'{event}: unknown handler keys {bad}')
                if 'timeout' in h and not isinstance(h['timeout'], int):
                    problems.append(f'{event}: timeout must be whole seconds')
    return problems


def check_codex_hooks_template_runs_the_claude_gates():
    """templates/harness/codex/hooks.json wires the claude-code adapter's
    own gate scripts into Codex (2026-09-28). Two things could make it a
    parallel on paper only, and each is planted here:

    - Codex parses hooks.json with deny_unknown_fields, so a `_comment`
      key -- the convention every settings.json in this repo uses -- makes
      it drop the whole file. Planted by adding one.
    - Codex sets no project-directory variable for a hooks.json hook and
      runs it in the session's working directory, which need not be the
      repository root. The template's commands resolve the root
      themselves. Planted by running the naive `bash .claude/hooks/...`
      form from a subdirectory: it must fail to find the script, where the
      template's form denies the commit.

    The gate is fed the PreToolUse payload Codex sends for its shell tool
    (tool_name "Bash", tool_input {"command": ...}, per
    codex-rs/hooks/src/events/pre_tool_use.rs), and must answer with the
    hookSpecificOutput deny Codex's own tests accept. The Stop command must
    exit 2 with a reason on stderr, which Codex turns into a continuation.
    None of this runs Codex itself; it checks the file and the scripts
    against what the source says Codex does."""
    import tempfile

    path = ROOT / 'templates' / 'harness' / 'codex' / 'hooks.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    hooks_dir = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
    cases = []
    cases.append(('the template parses as a Codex hooks.json',
                  not _codex_hooks_file_problems(data),
                  '; '.join(_codex_hooks_file_problems(data))))
    planted = dict(data, _comment='x')
    cases.append(('PLANTED: a _comment key is caught as a file Codex rejects',
                  any('_comment' in p for p in _codex_hooks_file_problems(planted)), ''))
    commands = [h['command'] for groups in data['hooks'].values()
                for g in groups for h in g['hooks']]
    named = sorted({m for c in commands
                    for m in re.findall(r'\.claude/hooks/([\w.-]+\.sh)', c)})
    missing = [n for n in named if not (hooks_dir / n).is_file()]
    cases.append(('every .claude/hooks script the template runs is one the '
                  'claude-code adapter ships', named and not missing, repr(missing)))

    lint_cmd = next(c for c in commands if 'doc-lint-gate.sh' in c)
    stop_cmd = next(c for c in commands if 'stop-git-check.sh' in c)
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'repo'
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / 'tools').mkdir()
        (repo / 'sub').mkdir()
        for n in named:
            shutil.copy(hooks_dir / n, repo / '.claude' / 'hooks' / n)
            # The stub runs its script from tools/, as an install has it.
            shutil.copy(ROOT / 'tools' / n, repo / 'tools' / n)
        # A stand-in linter: a finding on stdout, exit 1 -- what the gate
        # reads as "refuse", as distinct from a crash.
        (repo / 'tools' / 'doc_lint.py').write_text(
            'import sys\nprint("BAD.md:1: planted finding")\nsys.exit(1)\n',
            encoding='utf-8')
        env = dict(os.environ)
        env.pop('CLAUDE_PROJECT_DIR', None)
        env['GIT_CONFIG_GLOBAL'] = str(pathlib.Path(td) / 'gitconfig')
        pathlib.Path(env['GIT_CONFIG_GLOBAL']).write_text('', encoding='utf-8')

        def _git(*a):
            subprocess.run(['git', '-C', str(repo), *a], check=True,
                           capture_output=True, env=env)
        _git('init', '-q', '-b', 'main')
        (repo / 'BAD.md').write_text('# bad\n', encoding='utf-8')
        _git('add', 'BAD.md')
        payload = json.dumps({'session_id': 's', 'turn_id': 't',
                              'cwd': str(repo / 'sub'),
                              'hook_event_name': 'PreToolUse',
                              'tool_name': 'Bash',
                              'tool_input': {'command': 'git commit -m x'},
                              'tool_use_id': 'u'})

        def _sh(cmd, stdin=''):
            return subprocess.run(['sh', '-c', cmd], cwd=str(repo / 'sub'),
                                  input=stdin, capture_output=True,
                                  text=True, env=env, timeout=60)
        r = _sh(lint_cmd, payload)
        try:
            decision = json.loads(r.stdout)['hookSpecificOutput']['permissionDecision']
        except Exception:
            decision = None
        cases.append(('run from a subdirectory with a Codex Bash payload, the '
                      'template\'s doc-lint command denies the commit',
                      r.returncode == 0 and decision == 'deny',
                      f'rc={r.returncode} out={failure_detail(r.stdout, 300)} err={failure_detail(r.stderr, 300)}'))
        naive = _sh('bash .claude/hooks/doc-lint-gate.sh', payload)
        cases.append(('PLANTED: the naive relative command, from the same '
                      'subdirectory, never reaches the gate',
                      naive.returncode != 0 and 'deny' not in naive.stdout,
                      f'rc={naive.returncode} out={failure_detail(naive.stdout, 200)}'))

        _git('remote', 'add', 'origin', str(pathlib.Path(td) / 'nowhere'))
        s = _sh(stop_cmd, json.dumps({'hook_event_name': 'Stop',
                                      'stop_hook_active': False}))
        cases.append(('the Stop command exits 2 with a reason on stderr over a '
                      'staged, uncommitted file',
                      s.returncode == 2 and 'Uncommitted changes' in s.stderr,
                      f'rc={s.returncode} err={failure_detail(s.stderr, 300)}'))

    bad = [(n, e) for n, ok, e in cases if not ok]
    check(f'the codex hooks.json template parses as Codex reads it and runs the '
          f'claude-code gates ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {e}' for n, e in bad))


def check_bare_sync_warning_ignores_prose_mentions():
    """_warn_bare_sync_invocations flags a real bare invocation of
    precedent_sync_views.py, never a shell guard or a markdown link that
    merely mentions the filename.

    Reproduced 2026-09-17 against this repo's own tools/bootstrap.sh: its
    shell guard `if [ -f tools/precedent_sync_views.py ]; then` sits one
    line above the real invocation (which already carries `--repo`), and
    the old regex -- `precedent_sync_views\\.py(?![^\\n]*--repo)` -- matched
    the substring anywhere on a line, so the guard line and a markdown link
    target ([tools/precedent_sync_views.py](tools/precedent_sync_views.py))
    both false-positived as bare invocations. (practice:
    control-asserts-which-failure -- a "no output" pass proves nothing on
    its own, so the negative control below restores the old regex and
    checks the false positive comes back.)
    """
    import contextlib, io, tempfile as _tempfile
    import precedent_vendor_engine as _pve

    def _run(text):
        # practice: fixture-owns-its-state -- a fresh scratch tree each
        # call, never the real repo, so nothing here depends on what this
        # repo's own bootstrap.sh happens to contain today.
        with _tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / 'tools').mkdir()
            (root / 'tools' / 'bootstrap.sh').write_text(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                _pve._warn_bare_sync_invocations(root)
            return out.getvalue()

    guard_and_real = (
        "if [ -f tools/precedent_sync_views.py ]; then\n"
        "  python3 tools/precedent_sync_views.py --repo . --check\n"
        "fi\n")
    link_only = (
        "See [tools/precedent_sync_views.py](tools/precedent_sync_views.py) "
        "for details.\n")
    genuinely_bare = "python3 tools/precedent_sync_views.py\n"

    cases = [
        ('a shell guard next to a real --repo invocation is not flagged',
         'NOTICE' not in _run(guard_and_real)),
        ('a markdown link target is not flagged',
         'NOTICE' not in _run(link_only)),
        ('a genuinely bare invocation is still flagged',
         'NOTICE' in _run(genuinely_bare)),
    ]

    # Negative control: the pre-fix regex (any occurrence of the filename
    # not later followed by --repo on the same line) DOES false-positive on
    # the guard line -- proving the two positive cases above are evidence of
    # the fix, not of a fixture that never exercises the old bug.
    old_re = re.compile(r'precedent_sync_views\.py(?![^\n]*--repo)')
    cases.append(('negative control: the old regex flags the shell guard',
                  bool(old_re.search(guard_and_real.splitlines()[0]))))

    failed = [n for n, ok in cases if not ok]
    check(f'_warn_bare_sync_invocations ignores prose mentions '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_sync_views_cross_source():
    """tools/precedent_sync_views.py -- the one-command glue over
    precedent_materialize.py + build_views.py --agents-only that a
    CONSUMING repo (all four sources at once) actually runs, as opposed to
    the two tools it wraps, each already covered by their own harness
    case. Built and this case added 2026-09-03 alongside the precedence
    reorder and the repo-local level -- the fixture below is what caught
    two real bugs before either shipped: precedent_materialize.py deleting
    a repo-local source's own file before reading it (a self-referential
    `path: "."` source), and this tool's resident-count-by-level header
    counting every resolved practice instead of only the resident ones."""
    import shutil, tempfile

    def write_practice(path, slug, rule, tier='on-demand', occasion='x'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\nseverity: default\n'
            f'applies_to: ["**"]\noccasion: "{occasion}"\ngates: []\n'
            f'index_clause: "x"\nchecked_by: null\ndefines: []\nstatus: active\n'
            f'supersedes: []\noverrides: null\nadded: null\napproved_by: "x"\n'
            f'source_practice_number: null\n---\n## Rule\n{rule}\n\n## Why\nx\n\n'
            f'## Story\nx\n\n## Install\nx\n', encoding='utf-8')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-sync-views-'))
    cases = []
    try:
        consumer = tmp / 'consumer'
        universal, team, individual = tmp / 'u', tmp / 't', tmp / 'i'

        write_practice(universal / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture rule.', tier='resident')
        # The team fixture's Rule carries a SIBLING PRACTICE LINK, which is
        # legal in a practice file (practice: practice-links-travel) and was
        # dead in the consumer until 2026-09-11: a resident Rule is embedded
        # verbatim in a block that lands at the repo ROOT, one directory up
        # from where the link was written. A PRIVATE source is the case that
        # was reported, and it is the hard one -- the practice text comes
        # from a clone outside this repo, and only the MATERIALIZED copy is
        # placeable.
        write_practice(team / 'practices' / 'team-fixture.md', 'team-fixture',
                        'A team fixture rule, citing [ind-fixture](ind-fixture.md).',
                        tier='resident')
        write_practice(individual / 'practices' / 'ind-fixture.md', 'ind-fixture',
                        'An individual fixture rule.', occasion='doing individual things')
        # repo-local at a SUBDIRECTORY, per the recommended convention --
        # this is what keeps its hand-authored source apart from the
        # materialized output, both of which land under `consumer/`.
        write_practice(consumer / 'local' / 'practices' / 'local-fixture.md',
                        'local-fixture', 'A repo-local fixture rule.',
                        occasion='doing local things')

        # visibility DECLARED, not defaulted: this fixture is a PRIVATE
        # consumer, which is the case it exercises -- all four sources
        # materialized into one tracked tree. An undeclared visibility now
        # counts as public (build_views.repo_is_public), which would
        # correctly withhold the team and individual sources and make this
        # test assert the wrong thing for the right reason.
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(universal)},
                        {'level': 'team', 'name': 'precedent-team-fixture', 'path': str(team)},
                        {'level': 'repo-local', 'name': 'local', 'path': 'local'}]
        }), encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({
            'individual': {'name': 'precedent-individual', 'path': str(individual)}}), encoding='utf-8')
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        sync_tool = str(ROOT / 'tools' / 'precedent_sync_views.py')

        def run(*extra):
            r = subprocess.run([sys.executable, sync_tool, '--repo', str(consumer),
                                 '--user-config', str(user_cfg), *extra],
                                capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('a clean sync across all four sources exits 0', rc == 0, out))

        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('the resident block names BOTH resident sources, not just one',
                      'uni-fixture' in agents_text and 'team-fixture' in agents_text))
        # The individual set is not in a private consumer's tracked block
        # (2026-10-19): it reaches its person through the session file.
        cases.append(('the resident-count-by-level header counts only the '
                      'RESIDENT practices, of the three the block carries',
                      '2 of 3 practices (1 shared, 1 universal)' in agents_text))
        cases.append(('the occasion index reaches the on-demand repo-local '
                      'practice, and not the individual one',
                      'local-fixture' in agents_text and '  ind-fixture \u2014' not in agents_text))
        cases.append(('the repo-local source file at its OWN subdirectory '
                      'survives the sync untouched',
                      (consumer / 'local' / 'practices' / 'local-fixture.md').exists()))

        cases.append(("a resident Rule's sibling-practice link is repointed "
                      "at practices/ for the root the block lands in, even "
                      "though the practice text came from a source clone "
                      "outside this repo",
                      '[ind-fixture](practices/ind-fixture.md)' in agents_text,
                      agents_text[agents_text.find('team-fixture'):][:200]))
        cases.append(('and no absolute URL naming the private source repo is '
                      'minted to do it',
                      str(team) not in agents_text and 'http' not in
                      agents_text.split('## Occasion index')[0]))

        rc2, out2 = run('--check')
        cases.append(('--check on a just-synced, unmodified AGENTS.md exits 0',
                      rc2 == 0, out2))

        (consumer / 'AGENTS.md').write_text(
            agents_text.replace('uni-fixture', 'HAND-EDITED'), encoding='utf-8')
        rc3, out3 = run('--check')
        cases.append(('--check on a hand-edited AGENTS.md exits 1, not silently 0',
                      rc3 == 1, out3))

        # the exact bug this fixture was built to catch (2026-09-03): a
        # repo-local source declared at the bare repo root (`path: "."`)
        # used to crash precedent_materialize.py, or worse, silently
        # destroy its own hand-authored file the moment another source won
        # a shared slug. A later deep-check audit the same day found the
        # crash fix didn't close the silent-overwrite case, or a second,
        # worse case (materialize()'s own output read back as if this
        # source had authored it on the NEXT run) -- materialize() now
        # refuses this combination outright, unconditionally, rather than
        # attempting to make source == destination safe.
        #
        # repo-local itself can no longer even REACH this fixture:
        # precedent_resolve.py's load_config now requires a repo-local
        # source's `path` to be exactly "local" (see check_source_precedence's
        # own bare-root and other-subdirectory-name cases), so `path: "."`
        # for `level: "repo-local"` is refused before materialize() runs at
        # all. This fixture uses `level: "universal"` instead -- still a
        # perfectly legal `path: "."` (this repo's own precedent.json does
        # exactly that, self-hosting) -- to keep materialize()'s
        # level-agnostic `_self_referential_sources` guard itself under
        # test, on a configuration that is still allowed to reach it.
        selfref = tmp / 'selfref'
        write_practice(selfref / 'practices' / 'local-only.md', 'local-only',
                        'A self-referential universal rule.')
        (selfref / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'}]
        }), encoding='utf-8')
        (selfref / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        original_selfref = (selfref / 'practices' / 'local-only.md').read_bytes()
        r_self = subprocess.run([sys.executable, sync_tool, '--repo', str(selfref)],
                                 capture_output=True, text=True)
        cases.append(("a repo-local source declared at the bare repo root "
                      "(`path: \".\"`) is refused outright, loudly, naming "
                      "the subdirectory convention, rather than crashing or "
                      "silently materializing over its own source",
                      r_self.returncode == 1
                      and 'declares its `path` as this run' in (r_self.stdout + r_self.stderr)
                      and 'subdirectory' in (r_self.stdout + r_self.stderr)
                      and (selfref / 'practices' / 'local-only.md').read_bytes()
                          == original_selfref,
                      r_self.stdout + r_self.stderr))

        # the shadow-and-second-run case: a self-referential source at path
        # "." shares a slug with a HIGHER-precedence source -- this must
        # also refuse before any file is touched, not just the
        # single-source case above. `level: "universal"` again, for the
        # same reason as selfref above -- repo-local at "." can no longer
        # reach materialize() at all, so this exercises the same
        # lowest-precedence-loses-and-must-not-be-destroyed shape with
        # universal (still below team) standing in for it.
        selfref2 = tmp / 'selfref2'
        other = tmp / 'precedent-team-other'
        write_practice(selfref2 / 'practices' / 'shared.md', 'shared',
                        'HAND-AUTHORED -- MUST SURVIVE.')
        write_practice(other / 'practices' / 'shared.md', 'shared',
                        'TEAM VERSION.')
        (selfref2 / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'team', 'name': 'precedent-team-other', 'path': str(other)},
                        {'level': 'universal', 'name': 'precedent', 'path': '.'}]
        }), encoding='utf-8')
        (selfref2 / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r_self2 = subprocess.run([sys.executable, sync_tool, '--repo', str(selfref2)],
                                  capture_output=True, text=True)
        cases.append(('a self-referential source shadowed by a '
                      'higher-precedence source is refused before its own '
                      'file is touched, not silently overwritten',
                      r_self2.returncode == 1
                      and 'MUST SURVIVE' in
                          (selfref2 / 'practices' / 'shared.md').read_text(encoding='utf-8'),
                      r_self2.stdout + r_self2.stderr))
        # --- --check writes NOTHING (2026-09-06) --------------------------
        # It used to guard only the AGENTS.md write while materialize() ran
        # underneath it unconditionally, so the documented read-only drift
        # check rewrote practices/, tools/checks/ and MANIFEST.json every
        # time a session ran it. Found against a real four-source consumer,
        # where it made a genuine light-check failure vanish by overwriting
        # the drifted file, and -- with one source unreachable, the ordinary
        # state of a session before add_repo has run -- deleted 57 tracked
        # files while printing a check verdict. Both directions are pinned:
        # the clean case must not write, and the unreachable-source case
        # must not delete.
        run()  # take a clean sync first, so any later difference is the check's

        def snapshot():
            out = {}
            for sub in ('practices', 'tools'):
                d = consumer / sub
                for f in sorted(d.rglob('*')) if d.is_dir() else []:
                    if f.is_file():
                        out[str(f.relative_to(consumer))] = f.read_bytes()
            mf = consumer / 'MANIFEST.json'
            if mf.is_file():
                out['MANIFEST.json'] = mf.read_bytes()
            return out

        before = snapshot()
        rc_chk, out_chk = run('--check')
        cases.append(('--check on an already-synced repo exits 0',
                      rc_chk == 0, out_chk))
        cases.append(('--check writes nothing at all -- not practices/, not '
                      'tools/checks/, not MANIFEST.json',
                      snapshot() == before,
                      f'{len(set(before) ^ set(snapshot()))} file(s) added/removed'))

        # A source that cannot be reached is the ordinary state of a fresh
        # session, not an error state. --check must report it, never act on it.
        hidden = tmp / 't-hidden'
        team.rename(hidden)
        try:
            rc_gone, out_gone = run('--check')
            after_gone = snapshot()
        finally:
            hidden.rename(team)
        cases.append(('--check with a source unreachable FAILS rather than '
                      'reporting clean', rc_gone != 0, out_gone))
        cases.append(('--check with a source unreachable deletes nothing -- '
                      'the tree is byte-identical afterwards',
                      after_gone == before,
                      f'{len(set(before) - set(after_gone))} file(s) deleted'))
        cases.append(('and it names the missing practice rather than only '
                      'the loader block',
                      'team-fixture' in out_gone, out_gone))

        # Real drift must still be reported, or the two cases above could be
        # satisfied by a --check that reports nothing at all.
        victim = consumer / 'practices' / 'uni-fixture.md'
        victim.write_text(victim.read_text(encoding='utf-8') + '\nhand-edited\n',
                          encoding='utf-8')
        rc_drift, out_drift = run('--check')
        cases.append(('a hand-edited materialized practice is reported as '
                      'drift', rc_drift != 0 and 'uni-fixture' in out_drift,
                      out_drift))
        run()  # restore the fixture for the cases below

        # --- the OTHER writer of the same block must agree with this one ---
        # Both commands are documented for a consuming repo: session start
        # runs precedent_sync_views.py, and generated-artifact-provenance
        # runs `build_views.py --check` on every precedent_check.py. They
        # rendered different header lines for the same catalogue ("6 of 61
        # practices (6 universal)" vs "6 of 61 practices"), because only
        # sync_views passed source_levels -- a permanent, unresolvable
        # "hand-edited or stale" report in every consuming repo, whichever
        # ran last. build_views.py now reads the levels back out of
        # MANIFEST.json, so the two agree by construction.
        bv_tool = str(ROOT / 'tools' / 'build_views.py')
        # Both writers read the fixture's own person, never the real one:
        # build_views.py takes it from the environment, and with the real
        # config it rendered whoever was running the harness (2026-10-02).
        own_env = dict(os.environ, PRECEDENT_USER_CONFIG=str(user_cfg))
        subprocess.run([sys.executable, sync_tool, '--repo', str(consumer),
                        '--user-config', str(user_cfg)],
                       capture_output=True, text=True, env=own_env)
        r_agree = subprocess.run([sys.executable, bv_tool, '--repo', str(consumer),
                                  '--agents-only', '--check'],
                                 capture_output=True, text=True, env=own_env)
        cases.append(('build_views.py --check agrees with the block '
                      'precedent_sync_views.py just wrote (one loader block, '
                      'two documented writers)',
                      r_agree.returncode == 0, r_agree.stdout + r_agree.stderr))
        before_agents = (consumer / 'AGENTS.md').read_text(encoding='utf-8')
        subprocess.run([sys.executable, bv_tool, '--repo', str(consumer),
                        '--agents-only'], capture_output=True, text=True,
                       env=own_env)
        cases.append(('and running build_views.py for real changes nothing',
                      (consumer / 'AGENTS.md').read_text(encoding='utf-8')
                      == before_agents))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_sync_views.py syncs a consuming repo across all four '
          f'sources ({len(cases)} stated cases: clean sync, both resident '
          f'sources shown, correct level-of-resident counting, occasion '
          f'index reaches on-demand practices, --check both directions, a '
          f"resident Rule's sibling link placed at practices/ for the root "
          f'the block lands in with no URL minted for the private source it '
          f'came from, a '
          f'self-referential source is refused rather than crashed or '
          f'silently overwritten, alone or shadowed, and build_views.py '
          f'--check agrees with what this tool wrote)',
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_doc_sync_ledger():
    """doc_sync's ledger skips a block whose code fingerprint, recorded reads
    and output all still hold, and re-emits it when any of the three moves.
    Built in a scratch repository with one script and one document; the
    script counts its own emits in a file the hook does not track (a write,
    not a read)."""
    name = ('doc_sync skips an unchanged block (and one whose self-check alone changed) and '
            're-emits one whose code, data or text moved')
    engine = ROOT / 'tools' / 'doc_sync.py'
    rk = ROOT / 'tools' / 'reach_key.py'
    if not engine.is_file() or not rk.is_file():
        not_applicable(name, 'tools/doc_sync.py or tools/reach_key.py is absent')
        return
    import tempfile as _tf
    bad = []
    with _tf.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / '.git').mkdir()
        (d / 'tools').mkdir()
        shutil.copy2(engine, d / 'tools' / 'doc_sync.py')
        shutil.copy2(rk, d / 'tools' / 'reach_key.py')
        # everything doc_sync imports beside it (generated_blocks since staging's shared marker reader)
        for f in ('fact_ledger.py', 'content_record.py', 'generated_blocks.py'):
            if (ROOT / 'tools' / f).is_file():
                shutil.copy2(ROOT / 'tools' / f, d / 'tools' / f)
        (d / 'data.txt').write_text('7\n')
        model = (
            'import os, sys\n'
            'def value():\n'
            '    here = __file__.rsplit("/", 1)[0]\n'
            '    extra = (1 if os.path.exists(here + "/FLAG") else 0) + int(os.environ.get("TOY_FLAG", "0"))\n'
            '    return int(open(here + "/data.txt").read()) * 2 + extra\n'
            'def unrelated():\n'
            '    return 1\n'
            'def emit_table():\n'
            '    open(__file__.rsplit("/", 1)[0] + "/emits.log", "a").write("x")\n'
            '    return f"| v |\\n|---|\\n| {value()} |"\n'
            'def self_check():\n'
            '    return value() == 14\n'
            'EMITTERS = {"table": emit_table}\n'
            'if __name__ == "__main__":\n'
            '    if len(sys.argv) == 3 and sys.argv[1] == "--emit":\n'
            '        print(EMITTERS[sys.argv[2]]())\n'
            '        sys.exit(0)\n'
            '    if len(sys.argv) == 2 and sys.argv[1] == "--self-check":\n'
            '        sys.exit(0 if self_check() else 1)\n'
        )
        (d / 'model.py').write_text(model)
        (d / 'doc.md').write_text('# Doc\n\n<!--gen:table-->\n<!--/gen:table-->\n\nNumbers by: model.py\n')
        (d / 'shim.py').write_text(
            'import importlib.util, sys\n'
            'spec = importlib.util.spec_from_file_location("ds_engine", "tools/doc_sync.py")\n'
            'e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)\n'
            'e.PAIRS = [("doc.md", "table", "model.py")]\n'
            'e.LEDGER = "ledger.jsonl"\n'
            'e.DOC_GLOB = "*.md"\n'
            'e.main()\n')

        toy_env = {}

        def gate(*extra):
            env = {k: v for k, v in os.environ.items() if k not in ('PYTHONNOUSERSITE', 'TOY_FLAG')}
            env.update(toy_env)
            p = subprocess.run([sys.executable, 'shim.py', *extra], cwd=d, capture_output=True,
                               text=True, env=env)
            return p.returncode, p.stdout + p.stderr

        def emits():
            f = d / 'emits.log'
            return len(f.read_text()) if f.is_file() else 0
        rc, out = gate('--write')
        if rc != 0 or '| 14 |' not in (d / 'doc.md').read_text():
            bad.append(f'the first --write did not fill the block: {failure_detail(out, 300)}')
        if not (d / 'ledger.jsonl').is_file():
            bad.append('no ledger fact was recorded')
        n = emits()
        steps = [
            ('an unchanged tree', lambda: None, False, 0),
            ('a function the emit never calls', lambda: (d / 'model.py').write_text(
                (d / 'model.py').read_text().replace('return 1', 'return 2')), False, 0),
            # the dispatch branch an --emit run cannot take (a self-check, a
            # smoke mode) is left out of the block's fingerprint
            ('the self-check the emit never runs', lambda: (d / 'model.py').write_text(
                (d / 'model.py').read_text().replace('value() == 14', 'value() >= 14')), False, 0),
            ('a function the emit calls (same output)', lambda: (d / 'model.py').write_text(
                (d / 'model.py').read_text().replace('* 2 + extra', '* 2 + 0 + extra')), True, 0),
            ('a data file the emit read', lambda: (d / 'data.txt').write_text('8\n'), True, 1),
            ('a hand edit inside the block', lambda: (d / 'doc.md').write_text(
                (d / 'doc.md').read_text().replace('| 16 |', '| 99 |')), True, 1),
            # what no open() shows: a file the emit only tests for, and an
            # environment variable it reads
            ('a file the emit tests for appearing', lambda: (d / 'FLAG').write_text(''), True, 1),
            ('an environment variable the emit reads', lambda: toy_env.update(TOY_FLAG='3'), True, 1),
            # the emitter table rebound outside its literal: the block's key
            # must cover the new entry
            ('the emitter table rebound by |=', lambda: (d / 'model.py').write_text(
                (d / 'model.py').read_text().replace(
                    'EMITTERS = {"table": emit_table}\n',
                    'EMITTERS = {"table": emit_table}\ndef emit_other():\n    return emit_table() + " "\n'
                    'EMITTERS |= {"table": emit_other}\n')), True, 1),
        ]
        for what, edit, should_emit, should_fail in steps:
            edit()
            rc, out = gate()
            ran = emits() > n
            n = emits()
            if ran != should_emit:
                bad.append(f'{what}: the block {"was" if ran else "was not"} emitted')
            if bool(rc) != bool(should_fail):
                bad.append(f'{what}: the gate exited {rc}')
            if should_fail:
                gate('--write')
                n = emits()
    check(name, not bad, '; '.join(bad))


def check_doc_sync_fails_fast():
    """doc_sync runs emits concurrently; the first one that fails stops the
    rest and the gate exits at once, instead of waiting for the slowest
    emit beside it (origin 2026-09-28: a script that crashed in its first
    second was reported fourteen minutes later, twice). A scratch repository
    with one emit that sleeps a minute and one that fails."""
    name = 'doc_sync stops every other emit when one fails'
    engine = ROOT / 'tools' / 'doc_sync.py'
    if not engine.is_file():
        not_applicable(name, 'tools/doc_sync.py is absent')
        return
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / '.git').mkdir()
        (d / 'tools').mkdir()
        shutil.copy2(engine, d / 'tools' / 'doc_sync.py')
        for f in ('reach_key.py', 'fact_ledger.py', 'content_record.py', 'generated_blocks.py'):
            if (ROOT / 'tools' / f).is_file():
                shutil.copy2(ROOT / 'tools' / f, d / 'tools' / f)
        (d / 'slow.py').write_text('import time\ntime.sleep(60)\nprint("x")\n')
        (d / 'bad.py').write_text('import time\ntime.sleep(1)\nraise SystemExit("broken")\n')
        (d / 'doc.md').write_text('<!--gen:a-->\n<!--/gen:a-->\n<!--gen:b-->\n<!--/gen:b-->\n'
                                  'Numbers by: slow.py bad.py\n')
        (d / 'shim.py').write_text(
            'import importlib.util\n'
            'spec = importlib.util.spec_from_file_location("ds_engine", "tools/doc_sync.py")\n'
            'e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)\n'
            'e.PAIRS = [("doc.md", "a", "slow.py"), ("doc.md", "b", "bad.py")]\n'
            'e.DOC_GLOB = "*.md"\n'
            'e.main()\n')
        t0 = time.time()
        p = subprocess.run([sys.executable, 'shim.py'], cwd=d, capture_output=True, text=True,
                           env={**os.environ, 'DOC_SYNC_JOBS': '2'}, timeout=120)
        took = time.time() - t0
    check(name, p.returncode != 0 and took < 20 and 'bad.py' in p.stderr,
          f'exit {p.returncode} after {took:.0f}s: {failure_detail((p.stdout + p.stderr).strip(), 300)}')


def check_doc_sync_keeps_finished_blocks():
    """doc_sync settles each block as its own emit finishes: written, given
    its ledger fact, the ledger saved. A run killed partway, or stopped by a
    failing emit, keeps every block it finished, and the next run skips them
    (origin 2026-10-18: two container restarts each threw away a run more
    than two hours in, because blocks and facts were written only at the
    end). A scratch repository: two quick blocks in one document, one slow
    block, then one failing block."""
    name = 'doc_sync keeps the blocks a killed or failed run finished, and the next run skips them'
    engine = ROOT / 'tools' / 'doc_sync.py'
    if not engine.is_file() or not (ROOT / 'tools' / 'reach_key.py').is_file():
        not_applicable(name, 'tools/doc_sync.py or tools/reach_key.py is absent')
        return
    import signal as _sig
    import tempfile as _tf
    bad = []

    def model(value, before=''):
        return ('import os, sys, time\n'
                'def emit_table():\n'
                '    open(__file__.rsplit("/", 1)[0] + "/emits.log", "a").write(__file__[-6:-3])\n'
                f'    {before or "pass"}\n'
                f'    return "| v |\\n|---|\\n| {value} |"\n'
                'EMITTERS = {"%s": emit_table}\n'
                'if __name__ == "__main__":\n'
                '    if len(sys.argv) == 3 and sys.argv[1] == "--emit":\n'
                '        print(EMITTERS[sys.argv[2]]())\n'
                '        sys.exit(0)\n')
    with _tf.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / '.git').mkdir()
        (d / 'tools').mkdir()
        shutil.copy2(engine, d / 'tools' / 'doc_sync.py')
        for f in ('reach_key.py', 'fact_ledger.py', 'content_record.py', 'generated_blocks.py'):
            if (ROOT / 'tools' / f).is_file():
                shutil.copy2(ROOT / 'tools' / f, d / 'tools' / f)
        (d / 'm_aa.py').write_text(model(1) % 'a')
        (d / 'm_bb.py').write_text(model(2) % 'b')
        (d / 'm_cc.py').write_text(model(3, 'time.sleep(120)') % 'c')
        (d / 'doc.md').write_text('<!--gen:a-->\n<!--/gen:a-->\n<!--gen:b-->\n<!--/gen:b-->\n'
                                  'Numbers by: m_aa.py m_bb.py\n')
        (d / 'slow.md').write_text('<!--gen:c-->\n<!--/gen:c-->\nNumbers by: m_cc.py\n')
        (d / 'shim.py').write_text(
            'import importlib.util\n'
            'spec = importlib.util.spec_from_file_location("ds_engine", "tools/doc_sync.py")\n'
            'e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)\n'
            'e.PAIRS = [("doc.md", "a", "m_aa.py"), ("doc.md", "b", "m_bb.py"),\n'
            '           ("slow.md", "c", "m_cc.py")]\n'
            'e.LEDGER = "ledger.jsonl"\n'
            'e.DOC_GLOB = "*.md"\n'
            'e.main()\n')
        env = {**os.environ, 'DOC_SYNC_JOBS': '3'}
        env.pop('PYTHONNOUSERSITE', None)

        def emits():
            f = d / 'emits.log'
            return f.read_text() if f.is_file() else ''

        def facts():
            f = d / 'ledger.jsonl'
            return {json.loads(ln)['block'] for ln in f.read_text().splitlines()} if f.is_file() else set()
        # 1. killed partway: the quick blocks are on disk with their facts
        p = subprocess.Popen([sys.executable, 'shim.py', '--write'], cwd=d, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < 60 and facts() != {'a', 'b'}:
            time.sleep(0.2)
        os.killpg(p.pid, _sig.SIGKILL)
        p.communicate()
        doc = (d / 'doc.md').read_text()
        if '| 1 |' not in doc or '| 2 |' not in doc:
            bad.append(f'a killed run lost a block it had finished: {doc!r}')
        if facts() != {'a', 'b'}:
            bad.append(f'a killed run left facts for {sorted(facts())}, not a and b')
        if '| 3 |' in (d / 'slow.md').read_text():
            bad.append('the slow block was written although its emit was killed')
        # 2. the next run skips what finished and emits only the rest
        (d / 'm_cc.py').write_text(model(3) % 'c')
        before = emits()
        r = subprocess.run([sys.executable, 'shim.py', '--write'], cwd=d, env=env,
                           capture_output=True, text=True, timeout=120)
        ran = emits()[len(before):]
        if r.returncode != 0 or ran != '_cc' or '| 3 |' not in (d / 'slow.md').read_text():
            bad.append(f'the next run emitted {ran!r} (want only _cc), exit {r.returncode}: '
                       f'{failure_detail(r.stdout + r.stderr, 300)}')
        # 3. a failing emit stops the run, and the blocks already done stay done
        (d / 'm_aa.py').write_text(model(11) % 'a')
        (d / 'm_cc.py').write_text(model(3, 'time.sleep(3); raise SystemExit("broken")') % 'c')
        (d / 'slow.md').write_text('<!--gen:c-->\n<!--/gen:c-->\nNumbers by: m_cc.py\n')
        r = subprocess.run([sys.executable, 'shim.py', '--write'], cwd=d, env=env,
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 or '| 11 |' not in (d / 'doc.md').read_text():
            bad.append(f'a failed run kept no finished block (exit {r.returncode}): '
                       f'{failure_detail(r.stdout + r.stderr, 300)}')
        # 4. the check (no --write) still writes no document
        (d / 'm_bb.py').write_text(model(22) % 'b')
        (d / 'm_cc.py').write_text(model(3) % 'c')
        r = subprocess.run([sys.executable, 'shim.py'], cwd=d, env=env,
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 or '| 22 |' in (d / 'doc.md').read_text() or 'DRIFT' not in r.stdout:
            bad.append(f'the check without --write changed a document or passed drift '
                       f'(exit {r.returncode})')
    check(name, not bad, '; '.join(bad))


def check_markdown_required_only_where_doc_html_runs():
    """`markdown` is tools/doc_html.py's package alone, so the session check
    and the push check ask for it only where doc_html.py is present and in
    use (precedent_push_check.gate_packages).

    THE INCIDENT (2026-10-08). The session check required `markdown` in
    every repository, though a practice set gets no doc_html.py and a
    consumer receives one it may never run. Planted: a practice set (no
    doc_html.py); a consumer whose only mentions of doc_html are in the
    vendored engine; the same consumer with its own shim loading it; and a
    repository whose doc_html.py is its own (no manifest, as here). The
    session check's row is judged with `markdown` stubbed absent."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    import precedent_session_check as psc
    cases = []

    def plant(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='gate-pkgs-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], capture_output=True)
        return d

    manifest = json.dumps({'kind': 'consumer',
                           'files': ['doc_html.py', 'precedent_check.py']})
    consumer = {'tools/ENGINE_MANIFEST.json': manifest,
                'tools/doc_html.py': 'import markdown\n',
                'tools/precedent_check.py': '# doc_html.py is a renderer\n',
                'tools/my_tool.py': 'print("ours")\n'}
    shim = dict(consumer, **{'tools/render_host.py': 'import doc_html\n'})
    planted = [
        ('a practice set without doc_html.py', {'tools/x.py': ''}, False),
        ('a consumer that never runs doc_html.py', consumer, False),
        ('CONTROL: a consumer whose own shim loads it', shim, True),
        ('CONTROL: a repository whose doc_html.py is its own',
         {'tools/doc_html.py': 'import markdown\n'}, True),
    ]
    absent = lambda m: m != 'markdown'
    for name, files, wants in planted:
        d = plant(files)
        try:
            pkgs = ppc.gate_packages(d)
            row = psc.gate_packages_row(d, importable=absent)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        cases.append((f'{name}: markdown {"asked" if wants else "not asked"} for',
                      ('markdown' in pkgs) == wants and 'cmarkgfm' in pkgs
                      and row[1] == (not wants)
                      and (('markdown' in row[2]) == wants),
                      f'{pkgs} {row[1]} {row[2][:80]!r}'))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'markdown is required only where tools/doc_html.py runs '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_promote_runs_doc_html_only_where_it_is_in_use():
    """A Promote rebuilds the composed tree's renders with tools/doc_html.py
    only where doc_html is in use (precedent_push_check.doc_html_in_use, the
    rule gate_packages already keeps), and a vendored doc_html.py renders a
    consumer's own list, never BestPractice's.

    THE INCIDENT (2026-10-08). precedent_branches.py --promote ran
    tools/doc_html.py in a consuming repository that declined
    sortable-table-renderer and failed: "no such document:
    <tree>/spec/PREFORK_AUDIT.md", a BestPractice-only document from the
    DOCS list the vendored file carried.

    1. a consumer that never runs doc_html: the Promote does not run it;
    2. CONTROL: the same consumer with its own shim loading it: it runs;
    3. the real doc_html.py in a consumer with no tools/doc_html_host.json
       registers nothing, so a bare run renders nothing and succeeds;
    4. its host file's list is what it registers;
    5. CONTROL: where doc_html.py is the repo's own, its list is its own."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    cases = []
    manifest = json.dumps({'kind': 'consumer', 'files': ['doc_html.py']})
    stub = ('import pathlib, sys\n'
            'pathlib.Path(__file__).resolve().parents[1].joinpath("ran").write_text("x")\n'
            'sys.exit("doc_html FAIL: no such document: spec/PREFORK_AUDIT.md")\n')

    def plant(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='promote-doc-html-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], capture_output=True)
        return d

    consumer = {'tools/ENGINE_MANIFEST.json': manifest, 'tools/doc_html.py': stub}
    shim = dict(consumer, **{'tools/render_host.py': 'import doc_html\n'})
    for name, files, wants in (
            ('1: a consumer that never runs doc_html', consumer, False),
            ('2: CONTROL: a consumer whose own shim loads it', shim, True)):
        d = plant(files)
        said = []
        try:
            pb._rebuild_generated(d, said.append)
            ran = (d / 'ran').exists()
        finally:
            shutil.rmtree(d, ignore_errors=True)
        cases.append((f'{name}: doc_html {"runs" if wants else "does not run"}',
                      ran == wants, f'ran={ran} {said}'))

    try:
        import markdown  # noqa: F401  doc_html's own package
        have_md = True
    except ImportError:
        have_md = False
    if have_md:
        real = (ROOT / 'tools' / 'doc_html.py').read_text(encoding='utf-8')

        def listed(files):
            d = plant(dict(files, **{'tools/doc_html.py': real}))
            try:
                r = subprocess.run([sys.executable, str(d / 'tools' / 'doc_html.py'),
                                    '--list'], capture_output=True, text=True, cwd=d)
                bare = subprocess.run([sys.executable, str(d / 'tools' / 'doc_html.py')],
                                      capture_output=True, text=True, cwd=d)
                return r.stdout, bare.returncode, r.stderr + bare.stderr
            finally:
                shutil.rmtree(d, ignore_errors=True)
        out, rc, err = listed({'tools/ENGINE_MANIFEST.json': manifest})
        cases.append(('3: a consumer with no host file registers nothing and a '
                      'bare run succeeds', out.strip() == '' and rc == 0,
                      f'{out!r} rc={rc} {failure_detail(err, 200)!r}'))
        out, rc, err = listed({'tools/ENGINE_MANIFEST.json': manifest,
                               'tools/doc_html_host.json': json.dumps(
                                   {'docs': [['notes/ours.md', 'Ours']]}),
                               'notes/ours.md': '# Ours\n\n| a | b |\n|---|---|\n| 1 | 2 |\n'})
        cases.append(('4: the host file\'s list is what it registers',
                      'notes/ours.md' in out and 'PREFORK' not in out and rc == 0,
                      f'{out!r} rc={rc} {failure_detail(err, 200)!r}'))
        out, rc, err = listed({})
        cases.append(('5: CONTROL: its own doc_html.py keeps its own list',
                      'spec/PREFORK_AUDIT.md' in out, f'{out!r}'))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a Promote runs doc_html only where it is in use, over the '
          f'repository\'s own render list ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_render_names_files_by_title():
    """A render shows a linked file's title, never its bare filename.

    The repo convention links a document by its filename
    (`[x_model.py](x_model.py)`), which reads fine on the forge and means
    nothing to a reader of the rendered page, who never sees the
    repository. On 2026-10-01 a consumer's published pages showed a dozen
    code filenames in every footer. render() now retitles a
    link whose text IS the target's filename (alone, or followed by a
    section mark): a markdown target by its `# ` title, anything else by a
    humanized filename. A link written with words keeps them.
    (practice: deliverables-look-like-output)"""
    import importlib.util, tempfile, shutil
    spec = importlib.util.spec_from_file_location(
        '_doc_html_titles', ROOT / 'tools' / 'doc_html.py')
    try:
        dh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dh)
    except Exception as e:
        not_applicable('a render names linked files by title',
                       f'tools/doc_html.py could not be imported ({e}) -- '
                       f'not a pass')
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='render-titles-',
                                        dir=ROOT))
    cases = []
    try:
        (tmp / 'study.md').write_text("# The Cable Study — what binds\n\nBody.\n",
                                      encoding='utf-8')
        (tmp / 'cable_sizing_model_v1.py').write_text('"""x"""\n',
                                                     encoding='utf-8')
        (tmp / 'page.md').write_text(
            "# Page\n\n"
            "Numbers by: [cable_sizing_model_v1.py](cable_sizing_model_v1.py).\n\n"
            "See [study.md](study.md) and [study.md §3](study.md#x).\n\n"
            "Also [the study itself](study.md) and "
            "[a site](https://example.com/a.md).\n", encoding='utf-8')
        out = tmp / 'page.html'
        dh.render(tmp / 'page.md', out, 'Page')
        body = out.read_text(encoding='utf-8').split('<main>', 1)[1]
        cases.append(('a code link shows its humanized name',
                      '>Cable sizing model</a>' in body))
        cases.append(('a markdown link shows its title',
                      '>The Cable Study — what binds</a>' in body))
        cases.append(('a filename-and-section link keeps the section',
                      '>The Cable Study — what binds §3</a>' in body))
        cases.append(('a link written with words keeps them',
                      '>the study itself</a>' in body))
        cases.append(('an external link is untouched',
                      '>a site</a>' in body))
        cases.append(('no bare filename is left as link text',
                      '>study.md' not in body
                      and '>cable_sizing_model_v1.py<' not in body))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    for n in bad:
        print(f"  render-title case did not behave as stated: {n}")
    check(f'a render names linked files by title, never by filename '
          f'({len(cases)} stated cases)', not bad)


def check_rendered_docs_are_current():
    """Every committed HTML render still matches its markdown source.

    tools/doc_html.py writes a .html beside each document in its own DOCS
    registry, and nothing checked that the committed render was still the
    one that source produces. It was not: on 2026-09-06 an accidental bare
    run of the tool -- during the sweep for tools that write when they
    should not -- regenerated spec/PREFORK_AUDIT.html and picked up a whole
    paragraph the source had gained and the render had never been rebuilt
    for. A stale render is worse than no render: it is a page that looks
    current, is linked as the readable view of the document, and disagrees
    with it silently.

    generated-artifact-provenance already holds this property for the
    generated VIEWS (MAP.md, GLOSSARY.md, AGENTS.md's block); this is the
    same property for the rendered ones, which that check does not reach.

    The build stamp is excluded from the comparison: it is the one line
    that legitimately differs on every run, so comparing it would make this
    fail constantly and mean nothing.
    """
    import importlib.util, re as _re, tempfile, shutil
    spec = importlib.util.spec_from_file_location(
        '_doc_html', ROOT / 'tools' / 'doc_html.py')
    try:
        dh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dh)
    except Exception as e:
        not_applicable('rendered documents are current',
                       f'tools/doc_html.py could not be imported ({e}) -- '
                       f'not a pass')
        return
    if not getattr(dh, 'DOCS', None):
        not_applicable('rendered documents are current',
                       'doc_html.py registers no documents, so there is '
                       'no render to compare')
        return

    # the stamp is a <time> element since 2026-09-14 (reader-local rewrite,
    # dependent repo #1's check-in); the old <div> form is still masked so the
    # check stays green across the boundary commit.
    STAMP = _re.compile(
        r'<(?:div|time) class="renderstamp"[^>]*>[^<]*</(?:div|time)>')
    stale, missing = [], []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='render-check-'))
    try:
        for rel, title in dh.DOCS:
            src = ROOT / rel
            committed = src.with_suffix('.html')
            if not src.is_file():
                missing.append(f'{rel} (source missing)')
                continue
            if not committed.is_file():
                missing.append(str(committed.relative_to(ROOT)))
                continue
            out = tmp / (pathlib.Path(rel).stem + '.html')
            dh.render(src, out, title)
            a = STAMP.sub('', committed.read_text(encoding='utf-8'))
            b = STAMP.sub('', out.read_text(encoding='utf-8'))
            if a != b:
                stale.append(str(committed.relative_to(ROOT)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    check(f'every registered document\'s HTML render is current '
          f'({len(dh.DOCS)} registered)',
          not stale and not missing,
          '; '.join(
              ([f'stale: {", ".join(stale)}'] if stale else [])
              + ([f'missing: {", ".join(missing)}'] if missing else [])))


def _looks_like_help(tool, out):
    """Does this output actually answer --help, or is it the tool running?

    The test is the tool's own module docstring: a help answer contains a
    real run of it. Deliberately not an exact match -- argparse prints its
    own usage/description rather than the raw docstring, and that is a
    perfectly good help answer.
    """
    import ast
    try:
        doc = ast.get_docstring(ast.parse(tool.read_text(encoding='utf-8')))
    except Exception:
        return True                      # unparseable: not this check's call
    if not doc:
        return True                      # nothing to compare against
    o = ' '.join(out.split()).lower()
    if 'usage:' in o:                    # argparse-generated help
        return True
    for line in doc.strip().splitlines():
        line = ' '.join(line.split())
        if len(line) >= 40 and line.lower() in o:
            return True
    return False


def check_a_failure_item_lists_the_index_it_creates():
    """Filing the first open item in a repo lists the index files it makes.

    2026-10-10, a consumer with no todo/ yet: the lander filed each failed
    landing as an open item, build_todo_index.py wrote todo/TODO.md and
    todo/CLOSED.md, and the push check refused them -- "say they are
    generated by tools/build_todo_index.py and are not listed in
    tools/generated_files.json". The failure record was lost and nothing
    was filed. The builders now list their own outputs in the repo's list,
    and the lander commits that list with the item. The fixture runs the
    lander's own failure path on a scratch consumer, against the real
    generated-files check.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-failure-item-'))
    cases = []
    try:
        origin, work = tmp / 'o.git', tmp / 'w'
        env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-config.json'))
        def git(*a, cwd=work):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env)
        git('init', '-q', '--bare', '-b', 'main', str(origin), cwd=tmp)
        git('clone', '-q', str(origin), str(work), cwd=tmp)
        git('checkout', '-q', '-b', 'main')
        # The files git tracks, never the whole folder: a brought set ships
        # tools into a session untracked (.git/info/exclude), and one naming
        # a private repository made the global leak gate refuse this
        # fixture's first push, failing the case on any machine with that
        # set (2026-10-16; practice: fixture-owns-its-state).
        for rel in subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--', 'tools'],
                                  capture_output=True, text=True).stdout.split():
            if rel != 'tools/verify_harness.py':
                (work / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, work / rel)
        (work / 'tools' / 'generated_files.json').write_text(
            json.dumps({'files': []}) + '\n', encoding='utf-8')
        (work / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'consumer'}), encoding='utf-8')
        (work / 'precedent.json').write_text('{}\n', encoding='utf-8')
        (work / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
        git('add', '-A'); git('commit', '-qm', 'base'); git('push', '-q', 'origin', 'main')
        script = tmp / 'run.py'
        script.write_text(f"""
import json, sys
sys.path.insert(0, {str(work / 'tools')!r})
import land_next as ln
ln.TRUNK = 'main'
ln.BASIC_CHECK = [sys.executable, 'tools/precedent_check.py', '--only',
                  'generated-files-registered']
print(json.dumps(ln.file_failure(ln.ROOT, 'Landing failed: feat/x', 'push rejected 3 times',
                                 'feat/x lands')))
""", encoding='utf-8')
        p = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                           cwd=str(work), env=env, timeout=300)
        filed = (p.stdout.strip().splitlines() or ['""'])[-1]
        why = (p.stdout + p.stderr)[-500:]
        git('fetch', '-q', 'origin', 'main')
        on = git('ls-tree', '-r', '--name-only', 'origin/main').stdout.split()
        listed = json.loads(git('show', 'origin/main:tools/generated_files.json').stdout
                            or '{"files": []}')['files']
        cases.append(('the lander files the failure item on a repo with no todo/ yet',
                      filed.strip('"').startswith('todo/') and 'todo/TODO.md' in on
                      and 'todo/CLOSED.md' in on, why))
        cases.append(('...and the repo\'s own list now names both index files',
                      {e['path'] for e in listed} >= {'todo/TODO.md', 'todo/CLOSED.md'},
                      str(listed)))
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'generated-files-registered'], capture_output=True,
                           text=True, cwd=str(work), env=env, timeout=300)
        cases.append(('the generated-files check passes on what was pushed',
                      r.returncode == 0 and ' 0 violated' in r.stdout, failure_detail(r.stdout, 400)))
        before = (work / 'tools' / 'generated_files.json').read_text()
        subprocess.run([sys.executable, 'tools/build_todo_index.py'], cwd=str(work),
                       env=env, capture_output=True)
        cases.append(('a second build lists nothing twice',
                      (work / 'tools' / 'generated_files.json').read_text() == before, ''))
        (work / 'gotchas').mkdir()
        g = subprocess.run([sys.executable, 'tools/build_gotcha_index.py'], cwd=str(work),
                           env=env, capture_output=True, text=True)
        names = {e['path'] for e in json.loads(
            (work / 'tools' / 'generated_files.json').read_text())['files']}
        cases.append(('the gotcha index lists itself the same way',
                      'gotchas/INDEX.md' in names, failure_detail(g.stdout, 300)))
        bare = tmp / 'nolist'
        shutil.copytree(work / 'tools', bare / 'tools')
        (bare / 'tools' / 'generated_files.json').unlink()
        subprocess.run([sys.executable, str(bare / 'tools' / 'build_todo_index.py'),
                        '--repo', str(bare)], env=env, capture_output=True)
        cases.append(('a repo that keeps no list is not given one',
                      (bare / 'todo' / 'TODO.md').is_file()
                      and not (bare / 'tools' / 'generated_files.json').exists(), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a failure item lists the index it creates ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))

def check_review_page_lists_practices_that_may_overlap():
    """The review page's third part lists practice pairs that read alike --
    across sources and within one -- with the session's verdict beside each
    (Morgan, 2026-09-29, strength: decided). Discriminating cases: the same
    slug in two sources is listed whatever its score; two differently named
    rules saying the same thing in different sources are listed; an
    unrelated pair is not; and a verdict passed in is shown beside its pair
    while an unjudged one says so."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_review_page as rp
    PRACTICE = ('---\nslug: {slug}\ntitle: "{title}"\ntier: on-demand\n'
                'severity: advisory\napplies_to: ["**"]\n'
                'occasion: "{occ}"\ngates: []\nindex_clause: "{occ}"\n'
                'checked_by: null\ndefines: []\nstatus: active\n'
                'in_force_at: null\nsupersedes: []\noverrides: null\n'
                'added: null\napproved_by: "fixture"\n---\n## Rule\n{rule}\n')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='overlap-'))
    cases = []
    try:
        def put(src, slug, title, occ, rule):
            d = tmp / src / 'practices'
            d.mkdir(parents=True, exist_ok=True)
            (d / f'{slug}.md').write_text(PRACTICE.format(
                slug=slug, title=title, occ=occ, rule=rule), encoding='utf-8')
        twin = ('Name the spreadsheet column after the quarterly invoice '
                'ledger reconciliation total, never a vague heading.')
        put('uni', 'ledger-column-names', 'Ledger columns', 'naming a ledger column', twin)
        put('shr', 'invoice-heading-words', 'Invoice headings', 'naming a ledger column', twin)
        put('uni', 'same-rule', 'Same', 'a thing happens', 'Harbour pilots board early.')
        put('shr', 'same-rule', 'Same', 'a thing happens', 'Harbour pilots board early.')
        put('uni', 'weather-log', 'Weather', 'logging rain', 'Record barometric pressure hourly at the lighthouse.')
        put('shr', 'recipe-salt', 'Salt', 'seasoning soup', 'Taste the broth before adding coarse kosher salt.')
        sources = [{'name': 'uni', 'level': 'universal', 'path': str(tmp / 'uni')},
                   {'name': 'shr', 'level': 'shared', 'path': str(tmp / 'shr')}]
        pairs = rp.similar_pairs(sources)
        keys = {rp._pair_key(p): p['kind'] for p in pairs}
        k_same = frozenset(('uni:same-rule', 'shr:same-rule'))
        k_twin = frozenset(('uni:ledger-column-names', 'shr:invoice-heading-words'))
        k_none = frozenset(('uni:weather-log', 'shr:recipe-salt'))
        cases.append(('the same slug in two sources is listed as such',
                      keys.get(k_same) == 'same slug', repr(keys)))
        cases.append(('two rules saying the same thing in different sources '
                      'are listed', keys.get(k_twin) == 'different sources',
                      repr(keys)))
        cases.append(('an unrelated pair is not listed', k_none not in keys,
                      repr(keys)))
        by_source = [{'name': 'uni', 'level': 'universal', 'slug': None,
                      'prefix': '', 'practices': []},
                     {'name': 'shr', 'level': 'shared', 'slug': None,
                      'prefix': '', 'practices': []}]
        page = rp.render(by_source, [], pairs=pairs, verdicts=[
            {'a': 'uni:same-rule', 'b': 'shr:same-rule',
             'verdict': 'ZZVERDICTZZ keep the universal copy'}])
        cases.append(('a verdict is shown beside its pair, and an unjudged '
                      'pair says so', 'ZZVERDICTZZ' in page
                      and 'Not judged yet.' in page, failure_detail(page, 800)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the review page lists practices that may overlap '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_review_page_carries_every_source_and_is_never_committed():
    """The very deep check hands the person one session-only page: every
    branch they can delete, with a link each, and every active practice by
    source -- universal, this repo's own, individual, shared -- private sets
    included, and nothing of it committed (Morgan, 2026-09-28, strength:
    decided). It replaced a practice list committed into the public
    spec/VERY_DEEP_CHECK.md, which had to hold the private sets back, so he
    never got the whole list.

    Discriminating cases: a private source's clause IS on the page (the old
    committed list could never carry it); an unlanded branch and a tier
    branch are NOT offered for deletion while a landed one is; and a path
    git would track is refused. The fixture owns its repos."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import precedent_review_page as rp

    MARKER = 'ZZPRIVATEMARKERZZ an individual clause the page must carry'
    PRACTICE = (
        '---\nslug: {slug}\ntitle: fixture\ntier: on-demand\n'
        'severity: advisory\nscope: any-adopter\napplies_to: ["**"]\n'
        'occasion: "a fixture fires"\ngates: []\n'
        'index_clause: "{clause}"\nchecked_by: null\ndefines: []\n'
        'status: active\nin_force_at: null\nsupersedes: []\noverrides: null\n'
        'added: null\napproved_by: "fixture"\n---\n'
        '## Rule\nFixture text.\n')
    env = dict(os.environ, GIT_AUTHOR_NAME='fixture',
               GIT_AUTHOR_EMAIL='fixture@invalid', GIT_COMMITTER_NAME='fixture',
               GIT_COMMITTER_EMAIL='fixture@invalid')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True).stdout

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='review-page-'))
    cases = []
    real_scope = vdc.enumerate_scope
    try:
        origin = tmp / 'origin.git'
        git(tmp, 'init', '-q', '--bare', str(origin))
        root = tmp / 'root'
        (root / 'practices').mkdir(parents=True)
        git(root, 'init', '-q', '-b', 'main')
        git(root, 'config', 'commit.gpgsign', 'false')
        (root / '.gitignore').write_text('.precedent/\n', encoding='utf-8')
        (root / 'practices' / 'uni-practice.md').write_text(
            PRACTICE.format(slug='uni-practice', clause='a universal clause'),
            encoding='utf-8')
        git(root, 'add', '-A'); git(root, 'commit', '-q', '-m', 'base')
        git(root, 'remote', 'add', 'origin', str(origin))
        git(root, 'checkout', '-q', '-b', 'landed-branch')
        (root / 'a.txt').write_text('a\n', encoding='utf-8')
        git(root, 'add', '-A'); git(root, 'commit', '-q', '-m', 'landed')
        git(root, 'checkout', '-q', 'main')
        git(root, 'merge', '-q', '--ff-only', 'landed-branch')
        git(root, 'checkout', '-q', '-b', 'live-work')
        (root / 'b.txt').write_text('b\n', encoding='utf-8')
        git(root, 'add', '-A'); git(root, 'commit', '-q', '-m', 'unlanded')
        git(root, 'checkout', '-q', 'main')
        git(root, 'branch', '-q', 'staging')
        git(root, 'push', '-q', 'origin', 'main', 'staging', 'landed-branch',
            'live-work')
        git(root, 'fetch', '-q', 'origin')
        srcs = []
        for level, name in (('individual', 'fx-individual'),
                            ('shared', 'fx-shared')):
            d = tmp / name / 'practices'
            d.mkdir(parents=True)
            clause = MARKER if level == 'individual' else 'a shared clause'
            (d / f'{name}-rule.md').write_text(
                PRACTICE.format(slug=f'{name}-rule', clause=clause),
                encoding='utf-8')
            srcs.append({'level': level, 'name': name, 'path': str(d.parent)})
        sources = [srcs[1], {'level': 'universal', 'name': 'precedent',
                             'path': str(root)}, srcs[0]]
        vdc.enumerate_scope = lambda repo=None, user_config=None: {
            'sources': sources}
        page = rp.write(root, day='fixture').read_text(encoding='utf-8')
        cases.append(('THE CASE THIS EXISTS FOR: a private source\'s clause '
                      'is on the page', MARKER in page, page[:200]))
        order = [page.find('uni-practice'), page.find('fx-individual-rule'),
                 page.find('fx-shared-rule')]
        cases.append(('practices run universal, then individual, then shared',
                      -1 not in order and order == sorted(order), repr(order)))
        cases.append(('a landed branch is offered with a delete link',
                      'branches/all?query=landed-branch' in page, failure_detail(page, 600)))
        cases.append(('an unlanded branch and a tier branch are not',
                      'query=live-work' not in page
                      and 'query=staging' not in page
                      and 'query=main' not in page, failure_detail(page, 600)))
        cases.append(('the page is written where git ignores it',
                      subprocess.run(['git', '-C', str(root), 'check-ignore',
                                      '-q', str(root / rp.DEFAULT_OUT)]
                                     ).returncode == 0, str(rp.DEFAULT_OUT)))
        try:
            rp.write(root, out='tracked-page.html')
            refused = False
        except SystemExit:
            refused = True
        cases.append(('a path git would track is refused', refused, ''))
        src = (ROOT / 'tools' / 'very_deep_check.py').read_text(encoding='utf-8')
        doc = (ROOT / 'spec' / 'VERY_DEEP_CHECK.md').read_text(encoding='utf-8')
        cases.append(('the run no longer writes the catalogue into the '
                      'public spec document',
                      "_update_spec_doc_block(repo_root, 'practice-catalogue'"
                      not in src and 'vdc-embed:practice-catalogue' not in doc,
                      ''))
    finally:
        vdc.enumerate_scope = real_scope
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the review page carries every source and is never committed '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))

def check_very_deep_check_catalogue_loads_are_quiet():
    """The very deep check loads every catalogue several times a run, and
    build_views.load_practices() printed its not-in-force roster to stderr
    each time -- about 120 lines a run; the generator's "hook script(s) ...
    not wired" NOTE printed once per source. `announce=False` silences the
    roster for a caller that reports what is in force itself, the default
    still announces, and the generator's NOTE prints once per shape
    (2026-09-28)."""
    import tempfile, shutil, io, contextlib
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-quiet-'))
    cases = []
    try:
        pdir = tmp / 'practices'
        pdir.mkdir()
        (pdir / 'zz-live.md').write_text(
            '---\nslug: zz-live\nstatus: active\n---\n\n## Rule\n\nLive.\n',
            encoding='utf-8')
        (pdir / 'zz-gone.md').write_text(
            '---\nslug: zz-gone\nstatus: retired\n---\n\n## Rule\n\nGone.\n',
            encoding='utf-8')
        loud, quiet = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(loud):
            a = bv.load_practices(pdir)
        try:
            with contextlib.redirect_stderr(quiet):
                b = bv.load_practices(pdir, announce=False)
        except TypeError as exc:
            b = None
            quiet.write(f'TypeError: {exc}')
        cases.append(('CONTROL: the default still announces a dropped practice',
                      'zz-gone is status' in loud.getvalue(), loud.getvalue()))
        cases.append(('THE CASE: announce=False is quiet and returns the same',
                      b is not None and quiet.getvalue() == ''
                      and [f.name for _fm, _s, f in b]
                      == [f.name for _fm, _s, f in a], quiet.getvalue()))
        cat = io.StringIO()
        with contextlib.redirect_stderr(cat):
            rows = vdc._practice_catalogue_rows(
                [{'level': 'shared', 'name': 'zz', 'path': str(tmp)}])
        cases.append(('the very deep check\'s catalogue read is quiet',
                      cat.getvalue() == '' and len(rows) == 1,
                      cat.getvalue()[:300]))
        vdc._GENERATOR_STDERR_SEEN.clear()
        gen = io.StringIO()
        with contextlib.redirect_stderr(gen):
            vdc._pass_generator_stderr_once(
                'NOTE: zzfixture: 3 hook script(s) are not wired (a.sh, b.sh)\n')
            vdc._pass_generator_stderr_once(
                'NOTE: zzfixture: 4 hook script(s) are not wired (a.sh, b.sh, c.sh)\n'
                'NOTE: zzfixture: a different message\n')
        lines = gen.getvalue().splitlines()
        cases.append(('the generator\'s repeated NOTE prints once, and a '
                      'different one still prints',
                      len(lines) == 2 and 'a different message' in lines[1],
                      gen.getvalue()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'catalogue loads inside the very deep check are quiet and the '
          f'generator NOTE prints once ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_shared_helpers_have_one_copy():
    """The declared-base-branch helper and the commit checks' shared helpers
    each live in one file and are imported (2026-10-17 very deep check: nine
    tools carried `_declared_base_branch` in three wordings, and the two
    commit-identity checks five helpers verbatim, under a comment calling it
    forced that had been stale since both became engine files on 2026-10-10).
    THE CASE: the declared-base-branch check names a tool that defines its
    own copy again. CONTROLS: a tool that imports the helper, and doc_html.py
    (which runs alone in a host repository), are not named."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='one-helper-'))
    real_root = pc.ROOT
    try:
        tools = tmp / 'tools'
        tools.mkdir()
        shutil.copy(ROOT / 'tools' / 'declared_base_branch.py', tools)
        copy = ("def _declared_base_branch(root):\n"
                "    import json, pathlib\n"
                "    return json.loads((pathlib.Path(root) / 'precedent.json')"
                ".read_text()).get('base_branch')\n")
        (tools / 'own_copy.py').write_text(copy, encoding='utf-8')
        (tools / 'doc_html.py').write_text(copy, encoding='utf-8')
        (tools / 'imports_it.py').write_text(
            "from declared_base_branch import declared_base_branch as "
            "_declared_base_branch\n\n"
            "def branch(root):\n"
            "    return _declared_base_branch(root) or 'refs/remotes/origin/HEAD'\n",
            encoding='utf-8')
        pc.ROOT = tmp
        try:
            found = {f.where for f in pc._declared_base_branch_is_read(None)}
        finally:
            pc.ROOT = real_root
        cases.append(('THE CASE: a tool defining its own copy of the helper is '
                      'named', 'tools/own_copy.py' in found, sorted(found)))
        cases.append(('CONTROL: a tool importing the helper, and doc_html.py, '
                      'are not', not ({'tools/imports_it.py', 'tools/doc_html.py',
                                       'tools/declared_base_branch.py'} & found),
                      sorted(found)))
        # This tree itself is not scanned here: precedent_check.py runs the
        # same scan on it as the tree check `declared-base-branch` in every
        # full check, and it was nearly all of this test's time.
    finally:
        pc.ROOT = real_root
        shutil.rmtree(tmp, ignore_errors=True)
    for name in ('check_commit_author.py', 'check_commit_dates.py'):
        text = (ROOT / 'tools' / name).read_text(encoding='utf-8')
        cases.append((f'{name} imports the shared helpers and carries none of '
                      f'their bodies',
                      'import commit_checks_common' in text
                      and 'for name in ("precedent_identity", "precedent_resolve")'
                      not in text
                      and 'def _git_ok(' not in text
                      and 'grandfathered_commit_shas entry for' not in text,
                      name))
    bad = [c[0] + ' -- ' + str(c[2])[:300] for c in cases if not c[1]]
    check(f'the declared-base-branch helper and the commit checks\' helpers '
          f'each have one copy, imported ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_build_views_says_what_it_decides():
    """build_views told a public repository that a public shared set was "a
    private source", when it decides by level, not visibility; and its --help
    recommended --agents-only for a practice set, which every set's own
    instructions forbid (2026-10-17 very deep check). THE CASE: the note
    for a shared set excluded from a public repository's block says it is
    kept out by level and calls no set private. CONTROL: --help no longer
    recommends --agents-only for a set."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='bv-wording-'))
    try:
        (tmp / 'precedent.json').write_text(
            json.dumps({'visibility': 'public', 'sources': []}), encoding='utf-8')
        declared = [{'name': 'a-public-set', 'level': 'shared',
                     'path': str(tmp / 'a-public-set')}]
        _t, deferred, notes = bv._split_declared(tmp, declared)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    note = ' '.join(notes)
    helptext = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                               '--help'], capture_output=True, text=True).stdout
    cases = [
        ('the shared set is kept out of a public repository\'s block',
         [s['name'] for s in deferred] == ['a-public-set'], note),
        ('THE CASE: the note says it is kept out by level, and calls no '
         'set private', 'by level' in note and 'a private source' not in note,
         note),
        ('CONTROL: --help does not recommend --agents-only for a set',
         'does NOT use it' in helptext
         and 'source repo\n      # vendoring' not in helptext, ''),
    ]
    bad = [c[0] + ' -- ' + str(c[2])[:300] for c in cases if not c[1]]
    check(f'build_views says what it decides: by level, and the full command '
          f'for a set ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_tools_answer_help_without_writing():
    """`--help` is safe and informative on every tool in tools/.

    Two properties, both learned the hard way on 2026-09-06 by a sweep that
    simply ran `--help` across every script here to see what came back:

    * **It is answered, with exit 0.** The tools split three ways before that
      sweep -- a hard `FAIL: unknown option '--help'`, a silent fall-through
      that ran the whole audit as though nothing had been asked, or the
      docstring printed with a non-zero exit. `--help` is the first thing any
      reader types, and documentation/FOR_DEVELOPERS.md points a
      public audience straight at these commands.

    * **It writes nothing.** tools/resplit_sections.py defaulted to WRITING:
      any argument it did not recognise, `--help` included, fell through to
      the write branch and silently rewrote 46 tracked practice files,
      reverting every edit made to them since phase 1.5 -- no confirmation,
      no diff, and the damage surfaced two steps later as an unrelated
      doc_sync DRIFT that looked like a numbers problem. A destructive
      DEFAULT on a spent migration tool is the dangerous shape: the safe mode
      has to be the one you get by accident.

    Run against a throwaway copy of the tracked tree, never against the real
    one -- a check for "does this tool clobber the repo" must not be able to
    clobber the repo while finding out.
    """
    import hashlib, shutil, tempfile
    tracked = subprocess.run(['git', 'ls-files'], cwd=str(ROOT),
                             capture_output=True, text=True)
    if tracked.returncode != 0 or not tracked.stdout.strip():
        not_applicable('tools answer --help without writing',
                       'git ls-files returned nothing here, so there is no '
                       'tracked tree to copy and compare -- not a pass')
        return

    files = [f for f in tracked.stdout.splitlines() if f]
    # Only tracked tools: the copy below holds only tracked files, and a
    # tool a session-start hook drops into tools/ untracked (a shared set's
    # adapter, kept out by .git/info/exclude) ran there without its
    # neighbours and exited 2 (2026-10-14: three such tools failed this in a
    # session, while GitHub, which has none of them, passed).
    tools = sorted(ROOT / f for f in files
                   if f.startswith('tools/') and f.count('/') == 1
                   and f.endswith('.py'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='help-sweep-'))
    try:
        for rel in files:
            src = ROOT / rel
            if not src.is_file():
                continue
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        def snapshot():
            out = {}
            for rel in files:
                f = tmp / rel
                if f.is_file():
                    out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
            return out

        before = snapshot()
        # A module with no `if __name__ == '__main__'` block is a library
        # (tools/table_fmt.py is one): it is imported, never invoked, so
        # "answer --help" is not a property it can have. Named here rather
        # than quietly dropped, so the exemption stays visible.
        libraries = [t for t in tools
                     if "__main__" not in t.read_text(encoding='utf-8')]
        tools = [t for t in tools if t not in libraries]
        bad_exit, silent, not_help = [], [], []

        # SIDE BY SIDE (2026-10-31): about 150 interpreters, one after
        # another, were nearly all of this check's 16 s. They run in the
        # same copy; the snapshot after all of them still catches any write,
        # and the results are judged below in the tools' own order. The
        # whole tracked tree is still copied: a tool whose --help fell
        # through to a write needs the files it would rewrite to be there,
        # or the copy would hide exactly what this check is for.
        def _help(tool):
            return subprocess.run([sys.executable, str(tmp / 'tools' / tool.name),
                                   '--help'],
                                  cwd=str(tmp), capture_output=True, text=True,
                                  timeout=120)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=os.cpu_count() or 2) as _pool:
            _answers = list(_pool.map(_help, tools))
        for tool, r in zip(tools, _answers):
            if r.returncode != 0:
                bad_exit.append(f'{tool.name} exited {r.returncode}')
            elif not r.stdout.strip():
                silent.append(tool.name)
            elif not _looks_like_help(tool, r.stdout):
                # Exit 0 with output is NOT enough. A tool that simply
                # ignores an unrecognised flag runs its whole normal job and
                # exits 0, which passed every property above while answering
                # nothing -- build_views.py did exactly that until
                # 2026-09-06, silently regenerating MAP.md, GLOSSARY.md and
                # AGENTS.md's block on `--help`. In THIS repo those are
                # already current, so even the "writes nothing" property
                # held: an identical rewrite is invisible to a hash. It was
                # only visible in a consuming repo, where the same command
                # would have rewritten drifted views. So the output itself
                # has to be checked against the tool's own docstring.
                not_help.append(tool.name)
        after = snapshot()
        wrote = sorted(set(before) & set(after)
                       - {k for k in before if before[k] == after.get(k)})
        wrote += sorted(set(after) - set(before))

        check(f'every tool answers --help with exit 0 ({len(tools)} tools; '
              f'{len(libraries)} import-only module(s) exempt: '
              f'{", ".join(t.name for t in libraries) or "none"})',
              not bad_exit, '; '.join(bad_exit))
        check('every tool\'s --help actually prints something',
              not silent, ', '.join(silent))
        check('every tool\'s --help answers with its own usage text, rather '
              'than running the tool',
              not not_help, ', '.join(not_help))
        check('no tool writes to the tree when asked for --help',
              not wrote,
              f'{len(wrote)} file(s) changed: ' + ', '.join(wrote[:8]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_frontmatter_is_real_yaml():
    """The fence says YAML, so a real YAML parser has to accept it.

    This repo's own reader takes everything after the first colon and is
    happy with `title: Build/buy: decompose before deciding`. PyYAML is
    not -- the second colon opens a nested mapping and it rejects the
    whole block. Ten of sixty-one practice files shipped that way, and
    nothing here noticed for as long as the format existed, because
    nothing here parses its own output the way the people downstream do.

    Found 2026-09-06 from the other side: a consuming repo's own light
    check, which uses PyYAML, reported them as invalid. A format whose
    only conforming parser is its author's is not a format, so the check
    belongs on the producing side. Skipped with a notice where PyYAML
    isn't installed rather than passing on having parsed nothing.

    The parse itself lives in frontmatter_yaml.py, shared with
    doc_lint.py's own (touched-files-only) copy of this same check -- one
    parser, not two drifting ones."""
    if not frontmatter_yaml.HAVE_YAML:
        not_applicable('every --- fence holds valid YAML',
                        'PyYAML is not installed here, so nothing was parsed '
                        '-- `pip install pyyaml` to run it')
        return
    # Every tracked markdown file that OPENS with a --- fence, not only
    # practices/. A consuming repo vendors this whole tree and runs its own
    # YAML-based checks over all of it; four decisions/ records were
    # unparseable for a different reason than the practices were -- values
    # continued across lines with no block-scalar indicator -- and turned a
    # consumer's own commit gate red on vendored upstream content.
    bad = []
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '*.md'],
                             capture_output=True, text=True).stdout.split()
    for rel in tracked:
        f = ROOT / rel
        try:
            text = f.read_text(encoding='utf-8')
        except OSError:
            continue
        err = frontmatter_yaml.frontmatter_yaml_error(text)
        if err:
            bad.append((rel, err))
    for n, why in bad:
        print(f"  {n}: frontmatter is not valid YAML -- {why}")
    check(f"every tracked markdown file that opens a --- fence has "
          f"frontmatter a real YAML library accepts, not only this repo's "
          f"own reader ({len(tracked)} file(s) scanned)", not bad)


def check_sync_names_files_still_naming_removed_checks():
    """A sync that removes a check script or test names, in the same run,
    every file of the repository's own that still names it -- by path, or by
    the script's name with or without its suffix.

    WHY. 2026-10-06, a consumer: a sync removed four check scripts and their
    tests, and three later rounds of checks each found more files still
    naming them, one commit and one re-run per round."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_sync_views as psv
    env = _fixture_git_env()
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            run = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                            capture_output=True, text=True)
            run('init', '-q', '-b', 'main')
            files = {
                'tools/light_check.py': '# runs check_old_rule.py first\n',
                'todo/todo-x.md': 'See [it](../tools/checks/check_old_rule.py).\n',
                'gotchas/g.md': 'Unrelated: check_old_rule_two.py stays.\n',
                'tools/checks/check_other.py': '# check_old_rule\n',
                'notes.md': 'the stem alone: check_old_rule ran\n',
            }
            for rel, text in files.items():
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text(text, encoding='utf-8')
            run('add', '-A')
            run('commit', '-qm', 'x')
            got = psv._mentions_of_removed_files(
                repo, ['tools/checks/check_old_rule.py', 'practices/old-rule.md'])
            named = sorted({g.split(':', 1)[0] for g in got})
            cases.append(('the light check, the open item and the bare name are '
                          'each named, with their line',
                          named == ['notes.md', 'todo/todo-x.md', 'tools/light_check.py']
                          and all(':1 still names' in g for g in got)))
            cases.append(('a longer name that only starts the same is not',
                          'gotchas/g.md' not in named))
            cases.append(('materialized checks are not this repository\'s to fix',
                          'tools/checks/check_other.py' not in named))
            cases.append(('a removed practice is left to the link scan',
                          not any('old-rule.md' in g for g in got)))
    finally:
        sys.path.pop(0)
    bad = [n for n, ok in cases if not ok]
    check(f'a sync names every file still naming a check it removed '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_vdc_is_a_known_acronym_everywhere():
    """VDC (very deep check) is in the engine glossary registry, which ships
    to every repository and renders bold into each one's GLOSSARY.md, where
    doc_lint reads its known acronyms -- so a repository that receives
    practices/very-deep-check.md no longer gets an unglossed-acronym warning
    for a quoted "add that to VDC".

    WHY. 2026-10-09, a consumer: doc_lint flagged VDC in its copy of that
    practice. BestPractice never saw it, because its own corpus happens to
    use "vdc" as a word (very_deep_check imported as _vdc), which a
    consumer's corpus does not."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as _bv
    import precedent_vendor_engine as _pve
    import doc_lint as _dl
    sys.path.pop(0)
    terms = {t['term']: t for t in _bv._engine_glossary_terms(ROOT)}
    text = (ROOT / 'practices' / 'very-deep-check.md').read_text(encoding='utf-8')
    # What a consumer's doc_lint knows: the stoplist plus its glossary's
    # bold terms, which for the engine vocabulary are these terms. No
    # corpus: a consumer's corpus need not use "vdc" as a word.
    known = set(_dl.ACRONYM_STOP) | {t.upper() for t in terms}
    saved = _dl.looks_like_a_word
    _dl.looks_like_a_word = lambda tok: False
    try:
        flagged = [f for f in _dl.scan_unglossed(text, known,
                                                 'practices/very-deep-check.md')
                   if 'VDC' in str(f)]
    finally:
        _dl.looks_like_a_word = saved
    cases = [
        ('the engine glossary defines VDC, pointing at very-deep-check',
         'VDC' in terms and terms['VDC'].get('see') == 'practices/very-deep-check.md'),
        ('...and the registry ships with the engine',
         'glossary_terms.json' in _pve.ENGINE_FILES),
        ('GLOSSARY.md here carries it bold, where doc_lint reads it',
         '| **VDC** |' in (ROOT / 'GLOSSARY.md').read_text(encoding='utf-8')),
        ('a consumer\'s doc_lint, with no corpus help, does not flag VDC in '
         'very-deep-check.md', 'VDC' in text and not flagged),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'VDC is a known acronym in every repository that gets the engine '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_sync_names_a_field_its_engine_does_not_know():
    """The sync says, in plain words, when a practice uses a frontmatter
    field this engine does not know: the set needs a newer engine, so Update
    Vendors first.

    WHY. Morgan, 2026-10-07 (strength: decided): a practice set started
    using `hooks:` before a consuming repository's engine could wire it, the
    old engine ignored the field, and it surfaced as a check finding nobody
    there could fix. Planted: an unknown field is named, with the remedy; a
    field the source declares as its own is not; a practice using only
    known fields is not."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_sync_views as psv
    cases = []
    with tempfile.TemporaryDirectory() as td:
        src = pathlib.Path(td) / 'set'
        (src / 'practices').mkdir(parents=True)
        fm = '---\nslug: {s}\ntier: on-demand\n{extra}---\n## Rule\nR.\n'
        for s, extra in (('uses-new', 'future_field: x\n'), ('plain', ''),
                         ('declared', 'house_field: y\n')):
            (src / 'practices' / f'{s}.md').write_text(fm.format(s=s, extra=extra))
        (src / 'precedent.json').write_text(json.dumps(
            {'own_frontmatter_fields': ['house_field']}))
        live = {s: {'file': str(src / 'practices' / f'{s}.md'), 'source': 'a-set'}
                for s in ('uses-new', 'plain', 'declared')}
        notes = psv.fields_this_engine_does_not_know(live)
        cases.append(('an unknown field is named, with Update Vendors as the remedy',
                      len(notes) == 1 and notes[0].startswith('uses-new (a-set)')
                      and '`future_field:`' in notes[0] and 'Update Vendors' in notes[0]))
        cases.append(('a field the source declares as its own is not',
                      not any(n.startswith('declared') for n in notes)))
        cases.append(('a practice using only known fields is not',
                      not any(n.startswith('plain') for n in notes)))
    bad = [n for n, ok in cases if not ok]
    check(f'the sync names a field its engine does not know ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_duplicated_resident_text_detector():
    """Text an always-loaded file repeats from the catalogue is found, and the
    generated block is not mistaken for it
    (practice: control-asserts-which-failure).

    WHY IT EXISTS. "Delete what is duplicated" is the first and cheapest of
    session-load-budget's three reduction moves -- the text is provably
    reachable on demand, so cutting it costs a session nothing -- and it is the
    one nobody can find without reading everything. Two hand passes over this
    repo's instructions file found 903 tokens of it; nothing mechanical was
    looking.

    THE CASE THAT MAKES IT A CONTROL rather than a demo is the generated
    block: it is a copy of practice text ON PURPOSE. A detector that reported
    it would be reporting the loader working, would fire on every repo that
    ever ran build_views.py, and would be switched off within a week -- and
    then nothing would be looking again. The fixture owns its own tree
    (fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    SENTENCE = ('A session that hits this trap pays for it twice over, once '
                'in the hour it loses and once in the confident wrong answer '
                'it carries forward into everything after it.')
    PRACTICE = ('---\nslug: fixture-rule\n---\n## Rule\n' + SENTENCE +
                '\n\n## Story\nIt happened on a Tuesday.\n')

    def run(agents_body):
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            (d / 'practices').mkdir()
            (d / 'practices' / 'fixture-rule.md').write_text(
                PRACTICE, encoding='utf-8')
            return pc.duplicated_resident_text(d, agents_body)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    cases = []

    hits = run('# notes\n\nSome preamble.\n\n' + SENTENCE + '\n')
    cases.append(('text repeated from a practice file is reported, naming that '
                  'file',
                  len(hits) == 1 and hits[0][0] == 'practices/fixture-rule.md',
                  repr(hits)))

    hits = run('# notes\n\n' + SENTENCE.replace('trap', '`trap`').replace(
        'hour', '**hour**') + '\n')
    cases.append(('markup does not hide it -- backticks and bolding are '
                  'normalized away', len(hits) == 1, repr(hits)))

    generated = ('# notes\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
                 + SENTENCE + '\n<!-- END GENERATED -->\n')
    hits = run(generated)
    cases.append(('THE DISCRIMINATING CASE: the same sentence inside the '
                  'GENERATED block raises nothing -- that copy is the loader '
                  'working', hits == [], repr(hits)))

    hits = run('# notes\n\nA session that hits this trap pays for it twice '
               'over, and then we did something else entirely.\n')
    cases.append(('a short coincidental overlap is below the run threshold and '
                  'is not reported', hits == [], repr(hits)))

    hits = run('# notes\n\nNothing here resembles the practice at all.\n')
    cases.append(('unrelated prose raises nothing', hits == [], repr(hits)))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'duplicated always-loaded text is detected, and the generated block '
          f'is not ({len(cases)} stated cases, the generated block being the '
          f'discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_universal_occasion_share_is_capped():
    """Every source declares its share of a consumer's occasion index, and a
    consumer's cap is the sum of what its sources declare (Morgan,
    2026-09-29: the universal share, strength: assented; a share per set and
    the summed cap, strength: decided). Discriminating cases: this
    repository's real share fits its own declared allowance; the same build
    refuses with the allowance set below the share; a consumer whose sources
    all declare one is capped at their sum plus the repo-local allowance;
    and one whose source declares none falls back to the single literal."""
    import contextlib
    import io
    import json as _json
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as bv
    cases = []
    share = bv.occasion_share(bv.load_practices(announce=False))
    allowed = bv.own_occasion_allowance(ROOT)
    cases.append((f'the real share (~{share}) fits the declared allowance ({allowed})',
                  allowed is not None and 0 < share <= allowed,
                  f'share {share}, allowance {allowed}'))
    # Over its allowance, --check warns and --budgets refuses: a size cap
    # warns at the quick check and refuses at the full check
    # (Morgan, 2026-09-30, strength: decided).
    real, argv, strict = bv.own_occasion_allowance, sys.argv, bv.STRICT_BUDGETS
    # The share's cap binds only where no session-load total is declared
    # (build_views.TOTAL_KEY); this tests it, so the total is set aside.
    real_total = bv.session_load_total
    bv.session_load_total = lambda *a, **k: None
    bv.own_occasion_allowance = lambda root: 10
    for flag in ('--check', '--budgets'):
        sys.argv = ['build_views.py', flag]
        err = io.StringIO()
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(err):
                bv.main()
            refused, why = False, f'build_views {flag} returned'
        except SystemExit as e:
            refused = "source's share" in str(e.code)
            why = str(e.code)[:300]
        finally:
            bv.own_occasion_allowance, sys.argv = real, argv
            bv.STRICT_BUDGETS = strict
            bv.own_occasion_allowance = lambda root: 10
        if flag == '--check':
            cases.append(('a share over its allowance warns at --check, and '
                          'does not refuse', not refused
                          and "source's share" in err.getvalue(),
                          why + ' | ' + failure_detail(err.getvalue(), 300)))
        else:
            cases.append(('...and --budgets, the full check\'s, refuses it',
                          refused, why))
    bv.own_occasion_allowance = real
    bv.session_load_total = real_total
    d = pathlib.Path(tempfile.mkdtemp())
    try:
        for name, level, share_ in (('uni', 'universal', 2000),
                                    ('shr', 'shared', 300)):
            (d / name).mkdir()
            (d / name / 'practices').mkdir()
            man = {'name': 'precedent' if level == 'universal' else name,
                   'level': level}
            if share_:
                man['occasion_share_tokens'] = share_
            (d / name / 'precedent-source.json').write_text(
                _json.dumps(man), encoding='utf-8')
        # The declared sources are passed in, not resolved: a resolve here
        # would also pick up whatever individual source this machine's own
        # user config declares, and the sum would depend on the machine.
        srcs = [{'level': 'universal', 'name': 'precedent', 'path': str(d / 'uni')},
                {'level': 'shared', 'name': 'shr', 'path': str(d / 'shr')},
                {'level': 'repo-local', 'name': 'local', 'path': str(d / 'local')}]
        cap, why = bv.derived_occasion_cap(d, srcs)
        want = 2000 + 300 + bv.REPO_LOCAL_OCCASION_TOKENS
        cases.append(('a consumer is capped at the sum of its sources\' '
                      'allowances plus its repo-local allowance',
                      cap == want, f'{cap} ({why}), wanted {want}'))
        (d / 'shr' / 'precedent-source.json').write_text(
            _json.dumps({'name': 'shr', 'level': 'shared'}), encoding='utf-8')
        cap2, why2 = bv.derived_occasion_cap(d, srcs)
        cases.append(('MID-MIGRATION: a source that declares no allowance yet '
                      'counts at its measured share (0 for an empty catalogue '
                      'here), is named, and does not drop the whole repo back '
                      'to the single fallback',
                      cap2 == 2000 + bv.REPO_LOCAL_OCCASION_TOKENS
                      and 'shr' in why2 and 'measured' in why2,
                      f'{cap2} ({why2})'))
        (d / 'uni' / 'precedent-source.json').unlink()
        cap3, why3 = bv.derived_occasion_cap(d, srcs)
        cases.append(('MID-MIGRATION: a vendored universal tree with no '
                      'precedent-source.json, as an older Update Vendors wrote '
                      'it, still builds', cap3 is not None and 'measured' in why3,
                      f'{cap3} ({why3})'))

        # A PRACTICE SET's block carries its own catalogue and defers
        # universal, so its cap is its own allowance -- never universal's,
        # and never 0 because universal is not cloned beside it. GitHub's
        # test for the first version refused a bootstrapped set at a 0-token
        # cap on exactly that (2026-09-29).
        pset = d / 'pset'
        (pset / 'practices').mkdir(parents=True)
        (pset / 'precedent.json').write_text(_json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(d / 'no-universal-clone-here')}]}),
            encoding='utf-8')
        (pset / 'precedent-source.json').write_text(_json.dumps(
            {'name': 'pset', 'level': 'shared', 'occasion_share_tokens': 123}),
            encoding='utf-8')
        env_keep = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(d / 'no-user-config.json')
        try:
            cap4, why4 = bv.block_occasion_cap(pset)
            (pset / 'precedent-source.json').write_text(_json.dumps(
                {'name': 'pset', 'level': 'shared'}), encoding='utf-8')
            cap5, why5 = bv.block_occasion_cap(pset)
        finally:
            if env_keep is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = env_keep
        cases.append(('a practice set is capped at its own allowance, with '
                      'universal deferred and not cloned beside it',
                      cap4 == 123, f'{cap4} ({why4})'))
        cases.append(('MID-MIGRATION: a practice set that declares no '
                      'allowance yet keeps the single fallback, never a 0 cap',
                      cap5 == bv.OCCASION_INDEX_BUDGET_TOKENS
                      and 'declares no' in why5, f'{cap5} ({why5})'))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'each source\'s occasion-index share is capped, and a consumer\'s '
          f'cap is their sum ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_todo_index_check_survives_midnight():
    """build_todo_index.py --check rebuilds against the date the committed
    TODO.md records, so an index built yesterday, or in a zone behind this
    one, is not drift (practice: control-asserts-which-failure).

    THE INCIDENT (2026-09-29). --as-ci --isolated runs under TZ=UTC, already
    the 30th while Buenos Aires was on the 29th: every Age cell came out one
    day greater, generated-files-registered called todo/TODO.md out of date,
    and the deep check refused a push that had not touched todo/. The
    DISCRIMINATING CASE is the first: built in UTC-12, checked in UTC+14,
    which are always on different dates. It fails on the code before
    `as_of`. The second proves real drift is still caught.

    The fixture owns its tree and its zone (fixture-owns-its-state)."""
    import contextlib, importlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    todo = importlib.import_module('build_todo_index')
    cases = []
    keep = os.environ.get('PRECEDENT_COMMIT_TZ')
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        tdir = repo / 'todo'
        tdir.mkdir()
        item = tdir / 'todo-2026-09-01-an-item.md'
        item.write_text('---\nslug: todo-2026-09-01-an-item\nstatus: open\n'
                        'kind: analysis\nnoted: 2026-09-01\ndisposition: wait\n'
                        '---\n\n## What\n\n**An item.**\n', encoding='utf-8')
        out = io.StringIO()
        try:
            os.environ['PRECEDENT_COMMIT_TZ'] = 'Etc/GMT+12'      # UTC-12
            todo.main(['--repo', str(repo)])
            built = (tdir / 'TODO.md').read_text(encoding='utf-8')
            os.environ['PRECEDENT_COMMIT_TZ'] = 'Etc/GMT-14'      # UTC+14
            with contextlib.redirect_stdout(out):
                rc = todo.main(['--repo', str(repo), '--check'])
            said = out.getvalue()
            cases.append(('THE DISCRIMINATING CASE: an index built in UTC-12 '
                          'checks clean in UTC+14, a day later',
                          rc == 0 and '0 drift' in said, f'rc={rc} {said!r}'))
            cases.append(('the file records the date its ages were computed on',
                          getattr(todo, 'recorded_as_of', lambda _p: None)(
                              tdir / 'TODO.md') is not None
                          and 'as_of:' in built, built[:300]))
            item.write_text(item.read_text(encoding='utf-8')
                            .replace('An item.', 'A renamed item.'),
                            encoding='utf-8')
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = todo.main(['--repo', str(repo), '--check'])
            said = out.getvalue()
            cases.append(('POSITIVE CONTROL: an item changed after the build is '
                          'still drift, named by the index\'s own message',
                          rc == 1 and 'DRIFT in' in said and 'TODO.md' in said,
                          f'rc={rc} {said!r}'))
        finally:
            if keep is None:
                os.environ.pop('PRECEDENT_COMMIT_TZ', None)
            else:
                os.environ['PRECEDENT_COMMIT_TZ'] = keep
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the TODO index check does not go stale at midnight '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_todo_index_refuses_an_unknown_kind():
    """An open item whose kind TODO.md has no table for fails the build,
    rather than vanishing from the open-items list.

    THE INCIDENT (2026-10-10). Two engine bugs were filed as `kind: bug`;
    the index built clean and listed neither. The DISCRIMINATING CASE is
    the first: it passed on the code before this check. The others prove a
    known kind still builds and a closed item keeps whatever kind it had.
    The fixture owns its tree (fixture-owns-its-state)."""
    import contextlib, importlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    todo = importlib.import_module('build_todo_index')
    cases = []

    def build(kind, status):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            (repo / 'todo').mkdir()
            closed = 'closed: 2026-10-10\n' if status != 'open' else ''
            (repo / 'todo' / 'todo-2026-10-10-an-item.md').write_text(
                f'---\nslug: todo-2026-10-10-an-item\nstatus: {status}\n'
                f'kind: {kind}\nnoted: 2026-10-10\n{closed}disposition: wait\n'
                '---\n\n## What\n\n**An item.**\n', encoding='utf-8')
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    todo.main(['--repo', str(repo)])
            except SystemExit as e:
                return str(e.code), ''
            return '', (repo / 'todo' / 'TODO.md').read_text(encoding='utf-8')

    err, _ = build('bug', 'open')
    cases.append(('THE DISCRIMINATING CASE: an open `kind: bug` item fails '
                  'the build and names the kinds that exist',
                  'kind:' in err and 'analysis' in err, err))
    err, _ = build('task', 'open')
    cases.append(('the refusal names all four kinds, one line each, and suggests '
                  '`manual` for a `task` (2026-10-10: it named two, and the '
                  'consumer found `manual` by reading the source)',
                  all(f'`{k}`' in err for k in ('analysis', 'verify', 'manual',
                                                 'decision'))
                  and 'A `task` is usually `manual`' in err, err))
    err, out = build('analysis', 'open')
    cases.append(('POSITIVE CONTROL: an open analysis item builds and is listed',
                  not err and 'todo-2026-10-10-an-item' in out, err))
    err, _ = build('bug', 'done')
    cases.append(('a closed item is not refused for its kind', not err, err))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the TODO index refuses an open item of unknown kind '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_session_load_target_is_reported_each_reply():
    """Over its `target`, an always-loaded file is reported for The Boildown
    in every reply (practice: session-load-budget; Morgan, 2026-09-29: "at
    the 4000 level, you get warnings, with every session to bring it
    down"). Over its `hard_ceiling`, nothing refuses a commit in the repo
    that loads the file: that block was retired on 2026-09-30, unused
    (Morgan: "Since it's never used then let's retire it completely.
    Approved. Act.", strength: decided), because the ceiling is enforced
    where the file's text is written (session-file-allowances-fit). The
    last case runs the REAL .claude/hooks/doc-lint-gate.sh against a
    registry that still carries the old switch, so a hook that grew the
    block back fails here.

    The fixture owns its tree (fixture-owns-its-state)."""
    import tempfile
    import importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    slt = importlib.import_module('session_load_trend')
    gate = importlib.import_module('precedent_gate')
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / 'fixture'
        (repo / 'tools').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'session_load_trend.py', repo / 'tools')
        shutil.copy(ROOT / 'tools' / 'build_views.py', repo / 'tools')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        for k, v in (('user.name', 'Fixture'), ('user.email', 'f@example.com')):
            subprocess.run(['git', '-C', str(repo), 'config', k, v], check=True)
        (repo / 'AGENTS.md').write_text('word ' * 200, encoding='utf-8')
        (repo / 'tools' / 'session_load_budgets.json').write_text(
            json.dumps({'headroom_floor_pct': 5, 'surfaces': {'AGENTS.md': {
                'ceiling': 100000, 'hard_ceiling': 100, 'target': 50,
                'block_commits': True}}}), encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'base'], check=True)

        rows = slt.over_target(repo)
        cases.append(('a file over its target is listed with its target and '
                      'ceiling', rows and rows[0][0] == 'AGENTS.md'
                      and rows[0][2] == 50 and rows[0][3] == 100, repr(rows)))
        lines = gate._over_target(repo, siblings=False)
        cases.append(('the reply gate reports it for The Boildown',
                      lines and 'over its 50-token target' in lines[0]
                      and 'hard ceiling 100' in lines[0], repr(lines)))

        hook = ROOT / 'tools' / 'doc-lint-gate.sh'
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
        r = subprocess.run(['bash', str(hook)], input=json.dumps(
            {'tool_input': {'command': 'git commit -m change'}}),
            capture_output=True, text=True, env=env)
        cases.append(('over its hard ceiling, with the retired switch still '
                      'in the registry, the real commit-time hook lets the '
                      'commit through', r.returncode == 0
                      and 'COMMIT REFUSED' not in r.stderr,
                      f'rc={r.returncode} {failure_detail(r.stderr, 300)!r}'))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an always-loaded file over its target is reported each reply, '
          f'and nothing refuses a commit over its hard ceiling '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_update_vendors_refreshes_a_template_own_comment():
    """A line the template dropped from its own instruction comment (the
    `<!-- Template: ... -->` header) is replaced by the current template's
    comment and said once, not left for a person; text outside that comment
    is still only reported, and a comment the repository wrote into is
    never written.

    WHY. 2026-10-15, a consumer's Update Vendors: upstream renumbered
    "INSTALL.md §1" to "§0" inside the header comment of four templates, and
    the run stopped on four LEFT FOR YOU lines until a person edited one
    line in each file by hand -- the same four in every consumer.

    Negative control, measured 2026-10-15: on staging's code the comment
    line is left for the person and the file is unchanged."""
    import contextlib, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-template-comment-'))
    env = dict(_fixture_git_env(), GIT_CONFIG_NOSYSTEM='1')
    git = lambda cwd, *a: subprocess.run(['git', '-C', str(cwd), *a], env=env,
                                         capture_output=True, text=True)
    cases = []
    saved_source = pu.SOURCE
    head = ('<!-- Template: instantiate per Precedent INSTALL.md §{n} (practice x).\n'
            '     This file is deliberately tiny and stays that way. -->\n')
    body_v1 = ('# Open items\n'
               'Write every open item as a checkbox in this file.\n'
               'Every open item is tracked in one place here.\n')
    body_v2 = ('# Open items\n'
               'Every open item is tracked in one place here.\n')
    try:
        src = tmp / 'source'
        (src / 'templates').mkdir(parents=True)
        git(tmp, 'init', '-q', str(src))
        tmpl = src / 'templates' / 'TODO.md.template'
        tmpl.write_text(head.format(n=1) + body_v1, encoding='utf-8')
        git(src, 'add', '-A'); git(src, 'commit', '-qm', 'v1')
        v2_head = head.format(n=0).replace(
            ' -->\n', '\n     Do not rewrite it into a checkbox list. -->\n')
        tmpl.write_text(v2_head + body_v2, encoding='utf-8')
        git(src, 'add', '-A'); git(src, 'commit', '-qm', 'v2')
        rev = git(src, 'rev-parse', 'HEAD').stdout.strip()
        pu.SOURCE = src
        repo = tmp / 'consumer'
        repo.mkdir()
        own = 'Our own note about the billing export, written by this repo.\n'
        todo = repo / 'TODO.md'

        def run():
            rep = pu.Report()
            with contextlib.redirect_stdout(io.StringIO()):
                pu.dropped_template_lines_step(repo, rep, rev)
            return rep

        todo.write_text(head.format(n=1) + body_v1 + own, encoding='utf-8')
        rep = run()
        text = todo.read_text(encoding='utf-8')
        cases.append(('the template\'s own comment takes the current one, said once',
                      text.startswith(v2_head)
                      and any(n == 'template comment refreshed' for n, _o in rep.steps),
                      f'{text[:300]!r} {rep.steps}'))
        cases.append(('...and the renumbered line is not left for you',
                      not any('§1' in str(v) for v in dict(rep.left).values()),
                      str(rep.left)))
        cases.append(('a dropped line outside the comment is still left, at its '
                      'line in the file as written',
                      'TODO.md:5' in dict(rep.left)
                      and text.splitlines()[4].startswith('Write every open item'),
                      f'{rep.left}'))
        cases.append(('...and it, and the repo\'s own line, are not written',
                      text.endswith(body_v1 + own), repr(text[-200:])))

        mine = head.format(n=1).replace('stays that way.', 'stays that way. Ours: keep it.')
        todo.write_text(mine + body_v2, encoding='utf-8')
        rep = run()
        cases.append(('a comment the repository wrote into is never written, and '
                      'is still left for you',
                      todo.read_text(encoding='utf-8') == mine + body_v2
                      and 'TODO.md:1' in dict(rep.left), f'{rep.left} {rep.steps}'))

        todo.write_text(head.format(n=1) + body_v2, encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({
            pve.KEPT_DIVERGENCES_KEY: {'TODO.md': {
                'reason': 'kept on purpose', 'template_sha256': '0' * 64}}}),
            encoding='utf-8')
        run()
        cases.append(('a file recorded as kept is never written',
                      todo.read_text(encoding='utf-8') == head.format(n=1) + body_v2,
                      ''))
        (repo / 'precedent.json').unlink()
        rep = run()
        cases.append(('...and without the record, a file whose only dropped line '
                      'was in the comment leaves nothing for you',
                      not rep.left and todo.read_text(encoding='utf-8') == v2_head + body_v2,
                      f'{rep.left} {rep.steps}'))
    except (OSError, ValueError, AttributeError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pu.SOURCE = saved_source
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors refreshes a template\'s own instruction comment, and '
          f'only that ({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_dependents_warning_skips_a_wholly_generated_view():
    """The refresh's "still names it" warning leaves out a file a generator
    writes whole, which the update rebuilds from its sources a moment later,
    and still reads a file only partly generated (2026-10-17, a consuming
    repository's Update Vendors: MAP.md was warned about for naming two
    engine tools the refresh had removed, and the view rebuild then dropped
    both lines). A source still naming the tool is warned about as before."""
    import contextlib, io, tempfile
    import precedent_vendor_engine as pve
    name = 'the dependents warning skips a wholly generated view'
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-generated-dependents-'))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    gone = 'tools/retired_words.py'
    try:
        def put(rel, text):
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text, encoding='utf-8')
        put('MAP.md', f'| `{gone}` | a tool |\n')
        put('AGENTS.md', f'Run `{gone}` by hand.\n')
        put('docs/HOWTO.md', f'Use `{gone}`.\n')
        put('tools/generated_files.json', json.dumps({'files': [
            {'path': 'MAP.md', 'generated_by': 'tools/build_views.py'},
            {'path': 'AGENTS.md', 'part': '<!-- BEGIN GENERATED: x -->',
             'generated_by': 'tools/build_views.py'}]}))
        subprocess.run(['git', 'init', '-q', str(tmp)], env=env, check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], env=env, check=True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            pve._warn_about_dependents(tmp, [gone], 'removed from this kind\'s engine set')
        warned = err.getvalue()
        cases.append(('a wholly generated MAP.md naming the removed tool is not '
                      'warned about', 'MAP.md:' not in warned, warned[:400]))
        cases.append(('...while a hand-written doc and a partly generated '
                      'AGENTS.md still are',
                      'docs/HOWTO.md:1' in warned and 'AGENTS.md:1' in warned,
                      warned[:400]))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_sync_check_passes_from_another_checkout():
    """A view sync, committed, then `precedent_sync_views.py --check` from a
    worktree of the same commit, passes: nothing is stale. 2026-10-04: a
    consumer's Promote, which checks its composition in a throwaway
    worktree, failed every time on "MANIFEST.json differs from what a fresh
    sync writes" -- the manifest recorded each source's resolved absolute
    path, so the worktree's own path differed for the two sources inside
    the repository. Another machine differs the same way.

    CONTROL 1: a source outside the repository is compared by level and
    name, so a manifest recording it somewhere else still passes; changing
    its NAME still fails. CONTROL 2: a source inside the repository recorded
    at a different relative path still fails."""
    import shutil, tempfile
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-sync-worktree-'))
    env = {**os.environ, 'HOME': str(tmp / 'home'),
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json'),
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t',
           'PRECEDENT_ALLOW_ANY_AUTHOR': '1'}
    cases = []
    try:
        (tmp / 'home').mkdir()
        repo = tmp / 'consumer'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env,
                       capture_output=True)
        (repo / 'local' / 'practices').mkdir(parents=True)
        (repo / 'local' / 'practices' / 'zz-local.md').write_text(
            _move_fixture_practice('zz-local'), encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                        {'level': 'repo-local', 'name': 'local', 'path': 'local'}]})
            + '\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')

        def sync(where, *extra):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                                '--repo', str(where), *extra], cwd=str(where), env=env,
                               capture_output=True, text=True, timeout=600)
            return r.returncode, r.stdout + r.stderr

        rc, out = sync(repo)
        mf = repo / 'MANIFEST.json'
        recorded = json.loads(mf.read_text(encoding='utf-8')).get('sources') if mf.is_file() else None
        cases.append(('the sync records the source inside the repository as it is '
                      'declared, relative', rc == 0 and recorded is not None
                      and {'level': 'repo-local', 'name': 'local', 'path': 'local'} in recorded,
                      f'rc={rc} {recorded!r} {failure_detail(out, 400)}'))
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, capture_output=True)
        made = subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'synced'], env=env,
                              capture_output=True, text=True)
        wt = tmp / 'elsewhere' / 'composed'
        added = subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '-q', str(wt),
                                'HEAD'], env=env, capture_output=True, text=True)
        cases.append(('fixture: the sync is committed and checked out in a worktree '
                      'elsewhere', made.returncode == 0 and added.returncode == 0
                      and (wt / 'MANIFEST.json').is_file(),
                      failure_detail(made.stderr + added.stderr, 400)))
        rc, out = sync(wt, '--check')
        cases.append(('--check from a worktree of the same commit passes',
                      rc == 0, failure_detail(out, 600)))

        def with_sources(edit):
            data = json.loads((wt / 'MANIFEST.json').read_text(encoding='utf-8'))
            data['sources'] = [edit(dict(e)) for e in data['sources']]
            (wt / 'MANIFEST.json').write_text(json.dumps(data, indent=2) + '\n',
                                              encoding='utf-8')
        original = (wt / 'MANIFEST.json').read_text(encoding='utf-8')
        with_sources(lambda e: {**e, 'path': '/another/machine/BestPractice'}
                     if e['level'] == 'universal' else e)
        rc, out = sync(wt, '--check')
        cases.append(('CONTROL 1: a source outside the repository recorded at '
                      'another path still passes', rc == 0, failure_detail(out, 400)))
        (wt / 'MANIFEST.json').write_text(original, encoding='utf-8')
        with_sources(lambda e: {**e, 'name': 'renamed'} if e['level'] == 'universal' else e)
        rc, out = sync(wt, '--check')
        cases.append(('CONTROL 1: ...and the same source under another name fails',
                      rc != 0 and 'MANIFEST.json differs' in out, failure_detail(out, 400)))
        (wt / 'MANIFEST.json').write_text(original, encoding='utf-8')
        with_sources(lambda e: {**e, 'path': 'elsewhere'} if e['name'] == 'local' else e)
        rc, out = sync(wt, '--check')
        cases.append(('CONTROL 2: a source inside the repository recorded at '
                      'another relative path fails',
                      rc != 0 and 'MANIFEST.json differs' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:500]}' for n, d in bad))


def _pin_fixture_practice(slug, rule):
    return (_move_fixture_practice(slug)
            .replace('Do the thing.', rule))


def check_views_check_reads_a_set_at_the_commit_it_was_synced_at():
    """A consumer's views check reads each shared set at the commit its
    MANIFEST.json records syncing it at, never at whatever branch the set's
    clone has checked out (2026-10-05). Reported from a consumer: its
    landing tier took a set's Booked change, session start left the set's
    clone on main, and every push was refused for "drift" in files it never
    touched -- with a remedy, a plain sync, that rolled the Booked change
    back. Twice in one session.

    Each direction: a staging carrying a Booked-not-Produced set change
    passes; a write from a clone that lacks it is refused rather than
    rolling it back; a push to staging or main carrying a set commit the set
    has not landed on that rung is refused, with Booking or Producing it in
    the set as the remedy, and passes once it has; a hand-edited generated file still
    fails; a manifest written before pins gets one inferred; uncommitted
    edits in a set's clone are never taken into a consumer."""
    import shutil, tempfile
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-views-pin-'))
    env = {**os.environ, 'HOME': str(tmp / 'home'),
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json'),
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t',
           'PRECEDENT_ALLOW_ANY_AUTHOR': '1'}
    cases = []

    def git(where, *args):
        return subprocess.run(['git', '-C', str(where), *args], env=env,
                              capture_output=True, text=True)

    try:
        (tmp / 'home').mkdir()
        # The universal source is a plain directory: nothing to pin.
        uni = tmp / 'u'
        (uni / 'practices').mkdir(parents=True)
        (uni / 'practices' / 'uni-rule.md').write_text(
            _pin_fixture_practice('uni-rule', 'A universal rule.'), encoding='utf-8')
        # The shared set: a clone of a bare origin, with both rungs.
        bare, st = tmp / 'origin-set.git', tmp / 'precedent-shared-fixture'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)],
                       env=env, capture_output=True)
        subprocess.run(['git', 'clone', '-q', str(bare), str(st)], env=env,
                       capture_output=True)
        rule = st / 'practices' / 'set-rule.md'
        rule.parent.mkdir(parents=True)

        def set_commit(text, msg):
            # Resident, so the version reaches AGENTS.md's loader block and
            # not only the materialized practice.
            rule.write_text(_pin_fixture_practice('set-rule', text).replace(
                'tier:        on-demand', 'tier:        resident'),
                encoding='utf-8')
            git(st, 'add', '-A')
            git(st, 'commit', '-qm', msg)
            return git(st, 'rev-parse', 'HEAD').stdout.strip()

        git(st, 'checkout', '-q', '-b', 'main')
        set_commit('Version one.', 'v1')
        git(st, 'branch', 'staging')
        git(st, 'push', '-q', 'origin', 'main', 'staging')
        # Version two is on a working branch of the set, not Booked yet.
        git(st, 'checkout', '-q', '-b', 'feature', 'main')
        v2 = set_commit('Version two.', 'v2')
        git(st, 'push', '-q', 'origin', 'feature')

        repo = tmp / 'consumer'
        subprocess.run(['git', 'init', '-q', '-b', 'staging', str(repo)],
                       env=env, capture_output=True)
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                        {'level': 'shared', 'name': 'precedent-shared-fixture',
                         'path': str(st)}]}) + '\n', encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')

        def sync(*extra):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                                '--repo', str(repo), *extra], cwd=str(repo), env=env,
                               capture_output=True, text=True, timeout=600)
            return r.returncode, r.stdout + r.stderr

        def pinned():
            data = json.loads((repo / 'MANIFEST.json').read_text(encoding='utf-8'))
            return {e['name']: e.get('commit') for e in data['sources']}

        def taken():
            return (repo / 'practices' / 'set-rule.md').read_text(encoding='utf-8')

        # The consumer takes v2 from the set's working branch.
        rc, out = sync()
        pins = pinned() if rc == 0 else {}
        cases.append(('a sync records the commit it read the set at, and none for a '
                      'plain-directory source',
                      rc == 0 and pins.get('precedent-shared-fixture') == v2
                      and pins.get('precedent') is None and 'Version two.' in taken(),
                      f'rc={rc} {pins} {failure_detail(out, 500)}'))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'take v2')

        # The rung: staging may not carry what the set has not Booked.
        rc, out = sync('--check', '--for-branch', 'staging')
        cases.append(('a push to staging carrying a set commit the set has not '
                      'Booked is refused, with Book as the remedy and never a sync',
                      rc != 0 and 'Book it in precedent-shared-fixture' in out
                      and 'Do NOT sync' in out, f'rc={rc} {failure_detail(out, 600)}'))
        # The set Books v2: its working branch merged into its staging.
        git(st, 'checkout', '-q', 'staging')
        git(st, 'merge', '-q', '--no-ff', '-m', 'Book v2', 'feature')
        git(st, 'push', '-q', 'origin', 'staging')

        # Session start leaves the set's clone on main.
        git(st, 'checkout', '-q', 'main')
        rc, out = sync('--check')
        cases.append(('the views check passes with the clone on main: it reads the '
                      'set at the recorded commit (the reported refusal)',
                      rc == 0, failure_detail(out, 600)))
        # build_views --check, which generated-artifact-provenance runs, asks
        # the same question of the same tree. It read the clone as it stood,
        # and called AGENTS.md stale where the sync's check called it
        # byte-identical (a consumer's main, 2026-10-15).
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                            '--repo', str(repo), '--check'], cwd=str(repo), env=env,
                           capture_output=True, text=True, timeout=600)
        # This consumer has no MAP.md or GLOSSARY.md, and no engine manifest:
        # the sync writes no view a repository lacks, and build_views --check
        # knows it for a consumer by its materialized MANIFEST.json (it
        # failed on both here until 2026-10-15).
        cases.append(('...and so does build_views --check: AGENTS.md is read from '
                      'the set at the same recorded commit, with the clone on v1, '
                      'and no view the sync never writes is called drift',
                      r.returncode == 0 and 'Version two.' not in
                      git(st, 'show', 'HEAD:practices/set-rule.md').stdout,
                      failure_detail(r.stdout + r.stderr, 600)))
        rc, out = sync('--check', '--for-branch', 'staging')
        cases.append(('...and, once the set has Booked it, a push to staging '
                      'passes: the set has v2 on its own staging', rc == 0, failure_detail(out, 600)))
        rc, out = sync()
        cases.append(('a sync from the clone on main is REFUSED rather than rolling '
                      'the Booked change back, and writes nothing',
                      rc != 0 and 'roll those changes back' in out
                      and 'origin/staging' in out and 'Version two.' in taken(),
                      f'rc={rc} {failure_detail(out, 600)}'))
        git(st, 'checkout', '-q', '--detach', 'origin/staging')
        rc, out = sync()
        cases.append(('CONTROL: from the clone at the set\'s staging, the same '
                      'sync goes through and changes nothing',
                      rc == 0 and not git(repo, 'status', '--porcelain', '--',
                                          'practices').stdout.strip(),
                      f'rc={rc} {failure_detail(out, 400)}'))
        git(repo, 'checkout', '-q', '--', '.')
        git(st, 'checkout', '-q', 'main')

        # The rung: main may not carry what the set has not Produced.
        rc, out = sync('--check', '--for-branch', 'main')
        cases.append(('a push to main carrying the set\'s staging-only commit is '
                      'refused, with Produce as the remedy',
                      rc != 0 and 'Produce it in precedent-shared-fixture' in out,
                      f'rc={rc} {failure_detail(out, 600)}'))
        rc, out = sync('--rung-only', '--for-branch', 'main')
        cases.append(('the push check\'s own rung step (--rung-only) refuses the same '
                      'push without rendering anything',
                      rc != 0 and 'Produce it in precedent-shared-fixture' in out
                      and 'Do NOT sync' in out, f'rc={rc} {failure_detail(out, 400)}'))
        git(st, 'checkout', '-q', 'main')
        git(st, 'merge', '-q', '--no-ff', '-m', 'Produce', 'origin/staging')
        git(st, 'push', '-q', 'origin', 'main')
        rc_s, out_s = sync('--check', '--for-branch', 'staging')
        rc_m, out_m = sync('--check', '--for-branch', 'main')
        cases.append(('once the set has Produced it, both pushes pass',
                      rc_s == 0 and rc_m == 0, f'{failure_detail(out_s, 300)} | {failure_detail(out_m, 300)}'))
        rc, out = sync('--rung-only', '--for-branch', 'main')
        cases.append(('...and so does the rung step', rc == 0, failure_detail(out, 300)))

        # A hand-edited generated file fails on every rung.
        good = taken()
        (repo / 'practices' / 'set-rule.md').write_text(
            good.replace('Version two.', 'Edited by hand.'), encoding='utf-8')
        failed = []
        for b in (None, 'staging', 'main'):
            rc, out = sync('--check', *(['--for-branch', b] if b else []))
            if rc == 0 or 'set-rule.md differs' not in out:
                failed.append(f'{b}: rc={rc} {failure_detail(out, 200)}')
        cases.append(('a hand-edited materialized practice fails the check on every '
                      'rung', not failed, '; '.join(failed)))
        (repo / 'practices' / 'set-rule.md').write_text(good, encoding='utf-8')

        # A set moving on is said, never refused.
        git(st, 'checkout', '-q', 'staging')
        git(st, 'merge', '-q', '--ff-only', 'origin/staging')
        set_commit('Version three.', 'v3')
        git(st, 'push', '-q', 'origin', 'staging')
        git(st, 'checkout', '-q', 'main')
        rc, out = sync('--check', '--for-branch', 'staging')
        cases.append(('a newer set commit on staging is a note, not a refusal',
                      rc == 0 and 'differs from what this repository took' in out,
                      f'rc={rc} {failure_detail(out, 500)}'))

        # A manifest written before pins: the pin is inferred from history.
        mf = repo / 'MANIFEST.json'
        original = mf.read_text(encoding='utf-8')
        data = json.loads(original)
        for e in data['sources']:
            e.pop('commit', None)
        mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        rc, out = sync('--check')
        cases.append(('a manifest with no pins passes with the clone on main: the '
                      'commit whose practices match is found and named',
                      rc == 0 and 'matched' in out, f'rc={rc} {failure_detail(out, 500)}'))
        mf.write_text(original, encoding='utf-8')

        # Uncommitted edits in a set's clone never reach the consumer.
        git(st, 'checkout', '-q', '--detach', 'origin/staging')
        rule.write_text(_pin_fixture_practice('set-rule', 'Uncommitted.'),
                        encoding='utf-8')
        rc, out = sync()
        cases.append(('a sync from a clone with uncommitted practice edits takes '
                      'its commit, not the edits, and says so',
                      rc == 0 and 'Uncommitted.' not in taken()
                      and 'were NOT taken' in out
                      and pinned().get('precedent-shared-fixture')
                      == git(st, 'rev-parse', 'HEAD').stdout.strip(),
                      f'rc={rc} {failure_detail(out, 500)}'))
        rc, out = sync('--check')
        cases.append(('...and its own check passes straight after',
                      rc == 0, failure_detail(out, 400)))
        cases.append(('no worktree is left behind in the set\'s clone',
                      len(git(st, 'worktree', 'list').stdout.splitlines()) == 1,
                      git(st, 'worktree', 'list').stdout))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:600]}' for n, d in bad))


def check_generated_index_of_nothing_yet_passes():
    """generated-files-registered passes a repository whose generated index
    has no sources YET -- gotchas/INDEX.md with no gotcha written -- when the
    index's own generator check passes. 2026-10-04, a consumer with no
    gotchas: listed, "edit_instead ... matches nothing here"; unlisted,
    "gotchas/INDEX.md ... is not listed", so no state passed.

    CONTROL 1: the same entry whose generator check FAILS is still reported
    as pointing nowhere. CONTROL 2: an edit_instead whose directory does not
    exist is still reported, check passing or not."""
    import shutil, tempfile
    import precedent_check as pc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-empty-index-'))
    saved = pc.ROOT
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True)
        (tmp / 'gotchas').mkdir()
        (tmp / 'tools').mkdir()
        (tmp / 'gotchas' / 'INDEX.md').write_text(
            '---\ngenerated_by: tools/build_gotcha_index.py\n---\n\n# None yet\n',
            encoding='utf-8')
        gen = tmp / 'tools' / 'build_gotcha_index.py'

        def registry(glob):
            (tmp / 'tools' / 'generated_files.json').write_text(json.dumps({'files': [
                {'path': 'gotchas/INDEX.md', 'generated_by': 'tools/build_gotcha_index.py',
                 'edit_instead': glob, 'regenerate': 'python3 tools/build_gotcha_index.py',
                 'check': ['tools/build_gotcha_index.py', '--check']}]}), encoding='utf-8')
            subprocess.run(['git', '-C', str(tmp), 'add', '-A'], capture_output=True)

        def nowhere(check_rc, glob='gotchas/gotcha-*.md'):
            gen.write_text(f'import sys\nsys.exit({check_rc})\n', encoding='utf-8')
            registry(glob)
            pc.ROOT = tmp
            found = pc._generated_files_registered(None)
            return any("matches nothing" in f.detail for f in found), found

        hit, found = nowhere(0)
        cases.append(('an index of no gotchas yet, its generator check passing, is '
                      'not reported as pointing nowhere', not hit,
                      [f.detail for f in found]))
        hit, found = nowhere(1)
        cases.append(('CONTROL 1: with its generator check failing, it is', hit,
                      [f.detail for f in found]))
        hit, found = nowhere(0, 'nowhere/gotcha-*.md')
        cases.append(('CONTROL 2: a glob into a directory that does not exist is '
                      'reported, check passing or not', hit, [f.detail for f in found]))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:300]}' for n, d in bad))


def check_sync_refuses_a_rule_waiting_on_a_brought_set_by_name():
    """A sync that would drop a person's rule because the set providing its
    `requires:` capability is not on disk refuses with that reason and the
    remedy, and never points at --allow-removals. 2026-10-04, a consumer's
    update: ladder-required and promote-only read as removed, the refusal
    offered --allow-removals for "the source DELETED the file", and following
    it would have deleted two of the person's own rules. CONTROL: a rule its
    source really stopped producing still gets the old refusal."""
    import shutil, tempfile
    import build_views as bv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-sync-waiting-'))
    ind = tmp / 'precedent-individual'
    (ind / 'practices').mkdir(parents=True)
    (ind / 'precedent-source.json').write_text(json.dumps({
        'name': 'precedent-individual', 'level': 'individual'}), encoding='utf-8')
    for slug in ('zz-mine', 'zz-goes'):
        (ind / 'practices' / f'{slug}.md').write_text(
            _move_fixture_practice(slug), encoding='utf-8')
    (tmp / 'user-config.json').write_text(json.dumps({'individual': {
        'name': 'precedent-individual', 'path': str(ind)}}), encoding='utf-8')
    env = {**os.environ, 'HOME': str(tmp), 'PRECEDENT_USER_CONFIG': str(tmp / 'user-config.json'),
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
           'GIT_COMMITTER_EMAIL': 't@t', 'PRECEDENT_ALLOW_ANY_AUTHOR': '1'}
    env.pop('PRECEDENT_NO_LADDERS', None)
    repo = tmp / 'consumer'
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env,
                       capture_output=True)
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}),
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')

        def sync():
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                                '--repo', str(repo)], cwd=str(repo), env=env,
                               capture_output=True, text=True, timeout=600)
            return r.returncode, r.stdout + r.stderr
        rc, out = sync()
        recorded = json.loads((repo / 'MANIFEST.json').read_text()).get('practices') \
            if (repo / 'MANIFEST.json').is_file() else []
        cases.append(('fixture: the first sync records the person\'s two rules',
                      rc == 0 and {'zz-mine', 'zz-goes'} <= {e.get('slug') for e in recorded},
                      failure_detail(out, 500)))
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], env=env, capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'synced'], env=env,
                       capture_output=True)
        # The person's set now brings a ladder set that is not on disk, and
        # one rule requires what it provides.
        (ind / 'precedent-source.json').write_text(json.dumps({
            'name': 'precedent-individual', 'level': 'individual',
            'brings': [{'name': 'fx-ladder', 'repo_url': 'https://example.invalid/o/fx-ladder'}]}),
            encoding='utf-8')
        mine = ind / 'practices' / 'zz-mine.md'
        mine.write_text(mine.read_text().replace(
            'defines:     []\n', 'defines:     []\nrequires:    ["ladder"]\n'), encoding='utf-8')
        rc, out = sync()
        cases.append(('a rule waiting on a brought set that is not on disk is refused '
                      'by that reason, naming the set and the remedy',
                      rc != 0 and 'zz-mine (from precedent-individual, requires ladder)' in out
                      and '`fx-ladder`, brought by your individual set, is not on disk' in out,
                      failure_detail(out, 700)))
        cases.append(('...and the refusal never offers --allow-removals as the answer',
                      'is the answer, not a workaround' not in out
                      and 'Do NOT pass --allow-removals' in out, failure_detail(out, 700)))
        mine.write_text(mine.read_text().replace('requires:    ["ladder"]\n', ''),
                        encoding='utf-8')
        (ind / 'practices' / 'zz-goes.md').unlink()
        rc, out = sync()
        cases.append(('CONTROL: a rule its source stopped producing still gets the '
                      'old refusal', rc != 0 and 'zz-goes (from precedent-individual)' in out
                      and 'requires ladder' not in out, failure_detail(out, 700)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:700]}' for n, d in bad))


def check_heading_anchor_keeps_combining_marks():
    """GitHub's heading anchor keeps combining marks -- its rule is Ruby's
    \\p{Word}: letters, marks, decimal digits, connector punctuation -- and
    Python's \\w does not. A pointed Hebrew heading lost its vowel points in
    doc_lint's anchor and doc_html's id, so a working link read as broken and
    the push was refused (2026-10-05, a consumer's manuscript table of
    contents; the id was measured against GitHub's own render)."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_lint, doc_html
    finally:
        sys.path.pop(0)
    heading = 'Be \u201cNavon\u201d: \u201c\u05e0\u05b8\u05d1\u05d5\u05b9\u05df\u201d\u2014Penetrate'
    want = 'be-navon-\u05e0\u05b8\u05d1\u05d5\u05b9\u05dfpenetrate'
    cases = [
        ('doc_lint keeps the vowel points in the anchor', doc_lint.heading_slug(heading) == want),
        ("doc_html's heading id is the same anchor", doc_html.heading_slug(heading) == want),
        ('an ordinary heading is unchanged',
         doc_lint.heading_slug('A `code` & thing_x (2026)') == 'a-code--thing_x-2026'
         and doc_html.heading_slug('A <code>code</code> &amp; thing_x (2026)')
         == 'a-code--thing_x-2026'),
    ]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-anchor-marks-'))
    try:
        # The lint checks an anchor only inside the repository its own
        # script sits in, so the document and a copy of the tools share one.
        subprocess.run(['git', 'init', '-q', str(tmp)], check=True)
        shutil.copytree(ROOT / 'tools', tmp / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        doc = tmp / 'manuscript.md'
        doc.write_text(f'# Contents\n\n- [Navon](#{want})\n\n## {heading}\n\nText.\n',
                       encoding='utf-8')
        r = subprocess.run([sys.executable, str(tmp / 'tools' / 'doc_lint.py'), str(doc)],
                           capture_output=True, text=True, cwd=str(tmp))
        cases.append(('a link to the pointed heading passes the lint',
                       r.returncode == 0 and want not in (r.stdout + r.stderr)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_views_follow_the_header_stamp_and_consumer_check_skips_absent_views():
    """Two Update Vendors defects a consumer hit on 2026-10-04.

    1. precedent_update.py stamped MAP.source.md's version header AFTER the
       views step had built MAP.md from it, and MAP.md copies that header, so
       the basic check failed on a stale MAP.md on every run.
       rebuild_views_after_stamp() builds the views again when a stamped path
       is a view's source, re-stages only a view the update had staged, and
       says so when the build fails.
    2. `build_views.py --check` demanded a root GLOSSARY.md that a consumer
       whose glossary lives in docs/ never has; the 2026-10-03 fix covered
       --views-only only. A consumer's check now skips a view it lacks and
       has no source for, and BestPractice's own check still calls a deleted
       view drift."""
    import io, contextlib, tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import build_views as bv
    finally:
        sys.path.pop(0)
    rebuild = getattr(pu, 'rebuild_views_after_stamp', None)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-stamp-views-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True)
    try:
        r = tmp / 'r'
        subprocess.run(['git', 'init', '-q', str(r)], env=env, check=True)
        (r / 'tools').mkdir()
        # A stand-in build: MAP.md carries the generated header and copies
        # its source's version line, the thing the real build does.
        (r / 'tools' / 'build_views.py').write_text(
            'import pathlib, sys\n'
            'src = pathlib.Path("MAP.source.md").read_text().strip()\n'
            'pathlib.Path("MAP.md").write_text("---\\ngenerated_by: '
            'tools/build_views.py\\n---\\n" + src + "\\n")\n'
            'if pathlib.Path("FAIL").exists():\n'
            '    sys.exit("build_views FAIL: planted")\n', encoding='utf-8')
        (r / 'MAP.source.md').write_text('version: 1\n', encoding='utf-8')
        subprocess.run([sys.executable, 'tools/build_views.py'], cwd=r, check=True)
        git(r, 'add', '-A')
        git(r, 'commit', '-qm', 'base')
        # The update edits the source and the views step builds MAP.md from it.
        (r / 'MAP.source.md').write_text('version: 1\nedited\n', encoding='utf-8')
        subprocess.run([sys.executable, 'tools/build_views.py'], cwd=r, check=True)
        git(r, 'add', 'MAP.source.md', 'MAP.md')
        # Then the stamp bumps the source's version, after the build.
        (r / 'MAP.source.md').write_text('version: 2\nedited\n', encoding='utf-8')
        git(r, 'add', 'MAP.source.md')
        got = rebuild(r, ['MAP.source.md']) if rebuild else None
        cases.append(('1. a stamped source builds its view again and re-stages it',
                      got == ['MAP.md']
                      and 'version: 2' in git(r, 'show', ':MAP.md').stdout))
        before = (r / 'MAP.md').read_text()
        (r / 'MAP.md').write_text(before + 'x\n')
        cases.append(('1. ...a stamp of anything else builds nothing',
                      rebuild is not None and rebuild(r, ['AGENTS.md']) == []
                      and (r / 'MAP.md').read_text().endswith('x\n')))
        git(r, 'commit', '-qm', 'staged')
        (r / 'MAP.source.md').write_text('version: 3\nedited\n', encoding='utf-8')
        git(r, 'add', 'MAP.source.md')
        (r / 'MAP.md').write_text(before)
        got = rebuild(r, ['MAP.source.md']) if rebuild else None
        staged = git(r, 'diff', '--cached', '--name-only').stdout.split()
        cases.append(('1. ...a view the update had not staged is rebuilt but left unstaged',
                      got == [] and 'MAP.md' not in staged))
        (r / 'FAIL').write_text('')
        try:
            said = rebuild(r, ['MAP.source.md']) if rebuild else None
        except RuntimeError as e:
            said = str(e)
        cases.append(('1. ...and a failed build is said, by its own words',
                      isinstance(said, str) and 'build_views FAIL: planted' in said))

        repo = tmp / 'bp'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', 'prompts'))
        (repo / 'GLOSSARY.md').unlink()
        # where_things_are.json links GLOSSARY.md, and its own guard would
        # refuse first; the view check is what this case judges.
        (repo / 'where_things_are.json').unlink()

        def check_names_glossary(consumer):
            saved, saved_argv = getattr(bv, 'repo_is_consumer', None), sys.argv
            bv.repo_is_consumer = lambda root: consumer
            sys.argv = ['build_views.py', '--repo', str(repo), '--check']
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    try:
                        bv.main()
                    except SystemExit as e:
                        buf.write(f'\n{e.code}\n')
            finally:
                sys.argv = saved_argv
                if saved is None:
                    del bv.repo_is_consumer
                else:
                    bv.repo_is_consumer = saved
            out = buf.getvalue()
            return 'drifted from regeneration' in out and 'GLOSSARY.md' in out
        cases.append(("2. a consumer's --check does not demand a GLOSSARY.md it never had",
                      not check_names_glossary(True)))
        cases.append(("2. ...BestPractice's own --check still calls a deleted one drift",
                      check_names_glossary(False)))
        cases.append(('2. ...and the consumer test reads the manifest kind, nothing else',
                      hasattr(bv, 'repo_is_consumer')
                      and not bv.repo_is_consumer(ROOT)))
    except (OSError, subprocess.CalledProcessError, TypeError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_declared_exports_consumer_snags():
    """Seven snags four consumer sessions hit on 2026-10-30, moving their
    copies onto declared exports. Each has a case and a control.

    (a) Update Vendors finds a source's clone whatever its folder's case,
        or by its origin; an unrelated clone is still not taken.
    (b) A copy taken for its exports alone is resolved when it is on disk,
        unresolved when it is not.
    (c) A rebuild that only moves a version stamp's number is no hand edit;
        a line typed into the view still is.
    (d) A workflow step running a copied-in source's tool runs locally; a
        step under an undeclared process/ folder is still only named.
    (e) light-check's link sweep skips a closed todo item and a Story
        section, as rename-updates-links does; an open item still fails.
    (f) A section missing from AGENTS.md whose `##` section precedent.json
        records as kept is left out on purpose; unrecorded, it is missing.
    (g) doc_lint leaves a process/ path in a declared output document
        unlinked; in any other document it still asks for the link."""
    import tempfile, shutil, types
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_resolve as pr
        import precedent_source_credentials as psc
        import build_views as bv
        import precedent_push_check as ppc
        import precedent_check as pc
        import precedent_vendor_engine as pve
        import doc_lint as dl
        import title_case
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-exports-snags-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True)

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    try:
        # (a)
        name = 'harness-voice-source-q7'
        base = tmp / 'a'
        declared = base / 'consumer' / 'process' / name
        subprocess.run(['git', 'init', '-q', str(base / 'Harness-Voice-Source-Q7')],
                       env=env, check=True)
        got = pr.clone_elsewhere(name, str(declared), any_clone=True, near=[base])
        cases.append(('(a) a clone named in another case is found',
                      got is not None and got.name == 'Harness-Voice-Source-Q7'))
        shutil.rmtree(base / 'Harness-Voice-Source-Q7')
        subprocess.run(['git', 'init', '-q', str(base / 'checkout')], env=env, check=True)
        git(base / 'checkout', 'remote', 'add', 'origin',
            f'https://example.com/someone/{name.upper()}.git')
        got = pr.clone_elsewhere(name, str(declared), any_clone=True, near=[base])
        cases.append(('(a) ...and one under any folder name, by its origin',
                      got is not None and got.name == 'checkout'))
        git(base / 'checkout', 'remote', 'set-url', 'origin',
            'https://example.com/someone/another-repo.git')
        cases.append(('(a) CONTROL: a clone of another repository is not taken',
                      pr.clone_elsewhere(name, str(declared), any_clone=True,
                                         near=[base]) is None))

        # (b)
        r = tmp / 'b'
        write(r / 'precedent.json', json.dumps({'sources': [
            {'level': 'shared', 'name': 'voice-x', 'path': 'process/voice-x',
             'vendored': True, 'exports_only': True}]}))
        write(r / 'process' / 'voice-x' / 'prompts' / 'p.md', 'x\n')

        def unresolved():
            return [n for _l, n, _w in psc.unresolved_private_sources(
                r, env={'CLAUDE_CODE_REMOTE': 'true'}) if n == 'voice-x']
        cases.append(('(b) an exports-only copy on disk is resolved', unresolved() == []))
        shutil.rmtree(r / 'process' / 'voice-x')
        cases.append(('(b) CONTROL: ...and unresolved when it is not there',
                      unresolved() == ['voice-x']))

        # (c)
        c = tmp / 'c'
        src = c / 'MAP.source.md'
        write(src, '<!-- version: 3 -->\n# Map\n\nA row.\n')
        old = ('---\ngenerated_by: tools/build_views.py\n---\n'
               '<!-- version: 2 -->\n# Map\n\nA row.\n')
        new = old.replace('version: 2', 'version: 3')
        cases.append(('(c) a re-stamped version line is not a hand edit',
                      bv.hand_edits_against(c, old, new, [src]) == []))
        typed = old.replace('A row.\n', 'A row.\nTyped by hand, version 2.\n')
        cases.append(('(c) CONTROL: a typed line, even one naming a version, still is',
                      bv.hand_edits_against(c, typed, new, [src])
                      == ['Typed by hand, version 2.']))

        # (d)
        d = tmp / 'd'
        write(d / 'precedent.json', json.dumps({
            'sources': [{'level': 'shared', 'name': 'voice-x',
                         'path': 'process/voice-x', 'vendored': True,
                         'exports_only': True}],
            'github_ci_approved': {'.github/workflows/prompts.yml': {}}}))
        write(d / '.github' / 'workflows' / 'prompts.yml',
              'on: [pull_request]\njobs:\n  t:\n    runs-on: ubuntu-latest\n'
              '    steps:\n'
              '      - name: Check the prompts\n'
              '        run: python3 process/voice-x/tools/build_x_prompt.py --check\n'
              '      - name: Check another\n'
              '        run: python3 process/nobody/tools/y.py --check\n')
        checks, unrun = ppc.approved_workflow_checks(d)
        cases.append(("(d) a copied-in source's tool step runs locally",
                      any(argv[1:] == ['process/voice-x/tools/build_x_prompt.py',
                                       '--check'] for _n, argv, _r in checks)))
        cases.append(('(d) CONTROL: an undeclared folder\'s step is only named',
                      not any('process/nobody' in ' '.join(argv)
                              for _n, argv, _r in checks)
                      and any('process/nobody' in u[2] for u in unrun)))

        # (e)
        e = tmp / 'e'
        subprocess.run(['git', 'init', '-q', str(e)], env=env, check=True)
        write(e / 'todo' / 'todo-2026-01-01-closed.md',
              '---\nstatus: done\n---\n# Closed\n\nSee [gone](../gone.md).\n')
        write(e / 'notes.md', '# Notes\n\nLive text.\n\n## Story\n\n'
              'It was in [gone](gone.md).\n')
        write(e / 'todo' / 'todo-2026-01-02-open.md',
              '---\nstatus: open\n---\n# Open\n\nSee [gone](../gone.md).\n')
        git(e, 'add', '-A')
        found = {f.path for f in pc._light_check(types.SimpleNamespace(root=e))}
        cases.append(('(e) a closed item and a Story section are history to the sweep',
                      'todo/todo-2026-01-01-closed.md' not in found
                      and 'notes.md' not in found))
        cases.append(('(e) CONTROL: an open item\'s dead link still fails',
                      'todo/todo-2026-01-02-open.md' in found))

        # (f)
        f = tmp / 'f'
        tpl = (ROOT / 'templates' / 'AGENTS.md.loader.template').read_text(encoding='utf-8')
        keys = [k for k, _a, _b in pve._md_sections(tpl)]
        # Repointed 2026-10-31, when "Working in parallel" and its
        # sensitivities list left the template for a practice.
        parent = '## <Deliverable build workflow>'
        sub = '### Two check levels'
        write(f / 'AGENTS.md', '# Agents\n\n## Something of its own\n\nText.\n')

        def action(key, kept):
            write(f / 'precedent.json', json.dumps(
                {'kept_template_divergences': kept} if kept else {}))
            plan = pve._agents_md_plan(f, 'consumer', ROOT, {})
            return {k: a for k, _s, _n, a, _sp in plan}.get(key)
        moved = {f'AGENTS.md {parent}': {'reason': 'moved to docs/agents-detail.md'}}
        cases.append(('(f) template still has the sections this case reads',
                      parent in keys and sub in keys))
        cases.append(("(f) a moved section's missing subsection is left out on purpose",
                      action(sub, moved) == 'absent'))
        cases.append(('(f) CONTROL: unrecorded, it is missing',
                      action(sub, None) == 'missing'))
        cases.append(('(f) CONTROL: ...and another section is still missing',
                      action('## Git / workflow', moved) == 'missing'))

        # (g)
        g = tmp / 'g'
        write(g / 'precedent.json', json.dumps({'output_paths': ['out']}))
        line = 'Built from `process/voice-x/prompts/p.md` each time.\n'
        write(g / 'out' / 'README.md', '# Out\n\n' + line)
        write(g / 'notes' / 'README.md', '# Notes\n\n' + line)
        saved = dl.ROOT
        dl.ROOT = g
        title_case._PATHS_CONFIG.pop(str(g.absolute()), None)
        try:
            out_u = dl.check_file('out/README.md')[1]
            notes_u = dl.check_file('notes/README.md')[1]
        finally:
            dl.ROOT = saved
        cases.append(('(g) a process/ path in an output document is not asked to be a link',
                      out_u == []))
        cases.append(('(g) CONTROL: ...in a working document it still is',
                      [r for _i, r in notes_u] == ['process/voice-x/prompts/p.md']))
    except (OSError, subprocess.CalledProcessError, TypeError, ValueError,
            KeyError, AttributeError) as ex:
        cases.append((f'fixture could not be built ({ex!r})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_codeowners_stamp_hashes_only_the_registry():
    """CODEOWNERS' stamp is a hash of the registry it is rendered from, so a
    key in precedent.json that has nothing to do with it does not make the
    file read stale -- and a file stamped the old way still checks OK.

    WHY. Found 2026-09-28: the stamp hashed the whole precedent.json, and
    every Update Vendors writes `landing_branch` into it, so the template's
    own .github/CODEOWNERS read "hand-edited or stale" with no change to its
    maintainers or owned paths."""
    import importlib, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_codeowners as bco
    importlib.reload(bco)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-codeowners-stamp-'))
    cases = []

    def check_rc(root):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            return bco.main(check_only=True, root=root)

    def write(root):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            return bco.main(check_only=False, root=root)

    try:
        proj = tmp / 'project'
        proj.mkdir()
        cfg = {'maintainers': [{'name': 'M', 'github': 'maint'}],
               'owned_paths': [{'path': '/tools/', 'why': 'machinery'}]}
        (proj / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        write(proj)
        cases.append(('a freshly written project CODEOWNERS checks OK', check_rc(proj) == 0))
        (proj / 'precedent.json').write_text(json.dumps(dict(cfg, landing_branch='staging'),
                                                        indent=4), encoding='utf-8')
        cases.append(('an unrelated key (and reformatting) in precedent.json leaves it current',
                      check_rc(proj) == 0))
        (proj / 'precedent.json').write_text(json.dumps(dict(
            cfg, maintainers=[{'name': 'N', 'github': 'other'}])), encoding='utf-8')
        cases.append(('a change to the maintainers is still detected', check_rc(proj) == 1))

        cset = tmp / 'set'
        cset.mkdir()
        (cset / 'approvers.json').write_text(json.dumps(
            {'_comment': ['one'], 'approvers': [{'name': 'A', 'github': 'a'}]}), encoding='utf-8')
        write(cset)
        (cset / 'approvers.json').write_text(json.dumps(
            {'_comment': ['one', 'two'], 'approvers': [{'name': 'A', 'github': 'a'}]}),
            encoding='utf-8')
        cases.append(('a set\'s comment changing leaves its CODEOWNERS current', check_rc(cset) == 0))
        # The pre-2026-09-28 stamp: whole-file hash, old wording.
        try:
            (cset / 'CODEOWNERS').write_text(bco.render(
                [{'name': 'A', 'github': 'a'}], bco._file_hash(cset / 'approvers.json'),
                legacy=True), encoding='utf-8')
            legacy_ok = check_rc(cset) == 0
        except (AttributeError, TypeError):
            legacy_ok = False
        cases.append(('a CODEOWNERS stamped the old way still checks OK for one release',
                      legacy_ok))
        cases.append(('the template project\'s committed CODEOWNERS checks OK',
                      check_rc(ROOT / 'templates' / 'document-project') == 0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'CODEOWNERS is stamped with a hash of its registry, not the whole file '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_public_consumer_does_not_materialize_private_text():
    """A public consumer repo's TRACKED practices/ tree must not carry a
    private source's practice text (practice: very-deep-check, found by it).

    build_views.py already refuses to render a private source into a public
    repo's loader block, and precedent_materialize.py already refuses to
    mint a private repo's URL into the materialized tree -- but the whole
    practice FILE was copied in regardless, which discloses strictly more
    than the link so carefully withheld. Reproduced on a real fresh install
    built from INSTALL.md section 0: thirteen individual-level practices
    landed in a `visibility: public` consumer's tracked tree, one of them
    carrying a person's name and email address.

    Three properties, because fixing the first alone breaks the others:

    1. No private-level text in a public consumer's tree.
    2. NOTHING ELSE IS LOST. The private sources are dropped and the set
       RE-RESOLVED, not filtered out of a finished result -- a private
       practice can win a slug a publishable source also declares, and
       deleting the winner does not promote the runner-up. Filtering lost
       a universal practice exactly this way.
    3. The two renderers agree. precedent_sync_views.py must pass the same
       `omits_private` build_views.py computes for itself, or the standing
       instruction differs between them and `generated-artifact-provenance`
       reports the file the documented install step just wrote as
       hand-edited -- with no state of the repo able to satisfy it.

    A PRIVATE consumer is the control: nothing may be withheld there."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import build_views as bv

    def _consumer(tmp, visibility):
        repo = tmp / f'consumer-{visibility}'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (repo / 'AGENTS.md').write_text(
            f'# Consumer\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n',
            encoding='utf-8')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'visibility': visibility,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': 'precedent/universal'}]}), encoding='utf-8')
        return repo

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # A stand-in individual source, declared the only way one may be:
        # in a user-level config, never in the repo's own tracked file.
        ind = tmp / 'precedent-individual'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'practices' / 'private-only.md').write_text(
            '---\nslug: private-only\ntitle: A private rule\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "x happens"\n'
            'index_clause: "do the private thing"\nstatus: active\n---\n'
            '## Rule\nSECRET-CANARY-VALUE applies.\n\n## Story\nBecause.\n',
            encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(_json.dumps(
            {'format_version': 1,
             'individual': {'name': 'precedent-individual',
                            'path': str(ind)}}),
            encoding='utf-8')

        results = []
        pub = _consumer(tmp, 'public')
        psv.sync(str(pub), user_config=str(user_cfg))
        pub_tree = sorted(f.name for f in (pub / 'practices').glob('*.md'))
        pub_text = '\n'.join(
            f.read_text(encoding='utf-8') for f in (pub / 'practices').glob('*.md'))
        # Every universal practice that is IN FORCE, not every file on
        # disk. A `status: retired` or `deduplicated` practice stays in the
        # tree as its own retirement record and is deliberately not
        # materialized -- precedent_materialize.py resolves the in-force
        # set, it does not copy a directory. Comparing against the raw glob
        # was correct only while the catalogue happened to hold no retired
        # practice; it failed the moment one did (2026-09-07,
        # merge-authorization-keyword), reporting a real, intended omission
        # as private-text filtering. (practice: verify-decomposition -- the
        # count was right, what it counted was not.)
        # Same reasoning as the status exclusion above, one axis over:
        # scope: engine-dev is a SECOND, deliberate reason a practice never
        # materializes into a consumer, orthogonal to status. Added when
        # that field landed -- this assertion would otherwise fail the
        # moment any practice declared it, exactly as it did for the first
        # retired/deduplicated practice.
        universal = sorted(
            f.name for f in PRACTICES_DIR.glob('*.md')
            if not re.search(r'^status:\s*(retired|deduplicated)\s*$',
                             f.read_text(encoding='utf-8'), re.M)
            and not re.search(r'^scope:\s*engine-dev\s*$',
                              f.read_text(encoding='utf-8'), re.M))

        results.append(('a public consumer materializes no private practice file',
                        'private-only.md' not in pub_tree))
        results.append(('nor any of its text',
                        'SECRET-CANARY-VALUE' not in pub_text))
        results.append(('and loses nothing the universal source defines -- the '
                        'set is re-resolved, not filtered',
                        set(universal) <= set(pub_tree)))
        # The other side of the same property, so relaxing the assertion
        # above cannot quietly become "materialize whatever you like": a
        # practice the catalogue has retired must be ABSENT. Conditional
        # because a catalogue with nothing retired has nothing to assert,
        # and a vacuous case that always passes is worse than no case.
        retired = sorted(set(f.name for f in PRACTICES_DIR.glob('*.md'))
                         - set(universal))
        if retired:
            results.append((f'and materializes no retired practice '
                            f'({len(retired)} in the catalogue) -- a '
                            f'retirement record is not an in-force rule',
                            not (set(retired) & set(pub_tree))))
        # The real property: regenerating with build_views.py must not change
        # the AGENTS.md that sync just wrote. That byte-comparison IS what
        # generated-artifact-provenance's check performs.
        after_sync = (pub / 'AGENTS.md').read_text(encoding='utf-8')
        # Run it the way the check does -- as its own process, against the
        # consumer's own root -- rather than reaching into an internal.
        shutil.copy(ROOT / 'tools' / 'build_views.py', pub / 'tools_bv.py')
        subprocess.run([sys.executable, str(pub / 'tools_bv.py'), '--agents-only'],
                       cwd=str(pub), capture_output=True, text=True)
        (pub / 'tools_bv.py').unlink(missing_ok=True)
        results.append(('build_views.py regenerates byte-identically to what '
                        'sync wrote, so generated-artifact-provenance can pass',
                        (pub / 'AGENTS.md').read_text(encoding='utf-8') == after_sync))

        priv = _consumer(tmp, 'private')
        psv.sync(str(priv), user_config=str(user_cfg))
        priv_tree = sorted(f.name for f in (priv / 'practices').glob('*.md'))
        results.append(('CONTROL: a private consumer still gets the private '
                        'practice -- nothing is withheld where the tree is not '
                        'published', 'private-only.md' in priv_tree))

        failed = [n for n, ok in results if not ok]
        check(f'a public consumer repo never materializes private practice '
              f'text into its tracked tree ({len(results)} stated cases, a '
              f'private consumer being the control)',
              not failed, '; '.join(failed) if failed else '')


def check_consumer_sync_counts_what_a_brought_set_provides():
    """A consumer's sync leaves a brought set out of the tracked tree
    (spec/LADDER_OPT_IN_PLAN.md D6) but must still count it when deciding
    what is in force. Found by a consumer rehearsal, 2026-10-03: the sync
    filtered brought sets out BEFORE resolving, so an individual set's
    `requires: ["ladder"]` rules dropped out of every consumer, and a
    deduplicated individual rule pointing at a ladder rule read IN FORCE
    NOWHERE.

    1. the individual rule that requires the ladder is materialized;
    2. a deduplicated stub pointing at a rule in the brought set is not
       reported in force nowhere;
    3. the brought set's own rule is still never written into the tree;
    4. CONTROL: a person who brings nothing does not get the rule that
       requires the ladder -- the fix counts what is brought, nothing more."""
    import tempfile, shutil, contextlib, io
    import json as _json
    import precedent_sync_views as psv
    import precedent_resolve as pr
    import build_views as bv

    def rule(slug, extra=''):
        return _move_fixture_practice(slug).replace(
            'status:      active\n', 'status:      active\n' + extra)

    saved = {k: os.environ.get(k) for k in (
        'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG', pr.NO_LADDERS_ENV)}
    for k in saved:                       # practice: fixture-owns-its-state
        os.environ.pop(k, None)
    results = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            uni = tmp / 'universal'
            (uni / 'practices').mkdir(parents=True)
            (uni / 'practices' / 'plain-rule.md').write_text(
                rule('plain-rule'), encoding='utf-8')
            # A rule the REPOSITORY declares that needs the ladder: a brought
            # set never switches it on, or a committed view would differ by
            # who regenerated it (found by the full suite, 2026-10-03).
            (uni / 'practices' / 'repo-needs-ladder.md').write_text(
                rule('repo-needs-ladder', 'requires:    ["ladder"]\n'),
                encoding='utf-8')
            lad = tmp / 'people' / 'fx-ladder'
            (lad / 'practices').mkdir(parents=True)
            (lad / 'precedent-source.json').write_text(_json.dumps({
                'name': 'fx-ladder', 'level': 'shared', 'provides': ['ladder']}),
                encoding='utf-8')
            (lad / 'practices' / 'fx-stage.md').write_text(
                rule('fx-stage'), encoding='utf-8')

            def person(name, brings):
                ind = tmp / name / 'precedent-individual'
                (ind / 'practices').mkdir(parents=True)
                (ind / 'precedent-source.json').write_text(_json.dumps({
                    'name': 'precedent-individual', 'level': 'individual',
                    'brings': brings}), encoding='utf-8')
                (ind / 'practices' / 'needs-ladder.md').write_text(
                    rule('needs-ladder', 'requires:    ["ladder"]\n'),
                    encoding='utf-8')
                (ind / 'practices' / 'old-stage.md').write_text(
                    rule('old-stage').replace('status:      active',
                                              'status:      deduplicated')
                    .replace('in_force_at: null', 'in_force_at: fx-stage'),
                    encoding='utf-8')
                if brings:
                    os.symlink(lad, ind.parent / 'fx-ladder')
                cfg = tmp / f'{name}.json'
                cfg.write_text(_json.dumps({'format_version': 1, 'individual': {
                    'name': 'precedent-individual', 'path': str(ind)}}),
                    encoding='utf-8')
                return cfg

            for who, brings in (('brings', [{'name': 'fx-ladder',
                                             'repo_url': 'https://example.com/fx.git'}]),
                                ('plain', [])):
                cfg = person(who, brings)
                repo = tmp / f'consumer-{who}'
                repo.mkdir()
                (repo / 'AGENTS.md').write_text(
                    f'# C\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n',
                    encoding='utf-8')
                (repo / 'precedent.json').write_text(_json.dumps({
                    'format_version': 1, 'base_branch': 'main',
                    'visibility': 'private',
                    'sources': [{'level': 'universal', 'name': 'precedent',
                                 'path': str(uni)}]}), encoding='utf-8')
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    psv.sync(str(repo), user_config=str(cfg))
                tree = {f.name for f in (repo / 'practices').glob('*.md')}
                if who == 'brings':
                    results.append(('1: the rule that requires the ladder is '
                                    'materialized for the person who brings it',
                                    'needs-ladder.md' in tree, sorted(tree)))
                    results.append(('2: a stub pointing at a brought rule is not '
                                    'in force nowhere',
                                    'IN FORCE NOWHERE -- old-stage' not in err.getvalue(),
                                    failure_detail(err.getvalue(), 400)))
                    results.append(('3: the brought set\'s own rule is never written',
                                    'fx-stage.md' not in tree, sorted(tree)))
                    results.append(('3b: a rule the repository declares that '
                                    'needs the ladder stays out, whoever syncs',
                                    'repo-needs-ladder.md' not in tree, sorted(tree)))
                else:
                    results.append(('4: CONTROL: a person who brings nothing does '
                                    'not get it', 'needs-ladder.md' not in tree
                                    and 'plain-rule.md' in tree, sorted(tree)))
            # 5. A rule the individual set held, synced into the tree, then
            # moved to the brought set on purpose (2026-10-28: eleven such
            # moves read "the rule is LOST here", and a session relayed it
            # as a loss). The copy still goes; the line says where it went.
            ind = tmp / 'brings' / 'precedent-individual'
            stub = (ind / 'practices' / 'old-stage.md').read_text(encoding='utf-8')
            (ind / 'practices' / 'old-stage.md').write_text(
                rule('old-stage'), encoding='utf-8')
            repo = tmp / 'consumer-brings'
            with contextlib.redirect_stderr(io.StringIO()):
                psv.sync(str(repo), user_config=str(tmp / 'brings.json'))
            before = (repo / 'practices' / 'old-stage.md').exists()
            # The removal guard reads the COMMITTED MANIFEST.json.
            for a in (['init', '-q'], ['add', '-A'],
                      ['-c', 'user.name=T', '-c', 'user.email=t@example.com',
                       '-c', 'core.hooksPath=/dev/null', 'commit', '-q', '-m', 's']):
                subprocess.run(['git', '-C', str(repo), *a], capture_output=True)
            (ind / 'practices' / 'old-stage.md').write_text(stub, encoding='utf-8')
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                psv.sync(str(repo), user_config=str(tmp / 'brings.json'))
            said = err.getvalue()
            results.append(('5: a rule moved to a brought set is removed from '
                            'the tree and said to load from that set, not LOST',
                            before and not (repo / 'practices' / 'old-stage.md').exists()
                            and 'LOST' not in said and 'IN FORCE NOWHERE' not in said
                            and 'now loads as fx-stage from `fx-ladder`, brought '
                                'by your individual set' in said,
                            failure_detail(said, 600)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    failed = [(n, d) for n, ok, d in results if not ok]
    check(f'a consumer sync counts what a brought set provides, and still '
          f'never writes it ({len(results)} stated cases)',
          not failed, '; '.join(f'{n} -- {d}' for n, d in failed))


def check_sync_refuses_to_write_from_incomplete_sources():
    """precedent_sync_views.py must not rewrite a repo's tracked tree when a
    declared source did not resolve (practice: very-deep-check, found by it).

    materialize() rebuilds practices/ by delete-and-rewrite, so an
    unreachable source does not merely go unrendered: every practice it
    contributed is DELETED from the tracked tree, with AGENTS.md and
    MANIFEST.json rewritten to match, one warning line, and exit 0. The diff
    reads as a deliberate removal.

    That is the CI state by definition -- a private team or individual
    source is unreachable in every continuous-integration checkout, which is
    exactly where an unattended sync would run. build_views.py already
    refuses this in as many words; this tool, the one the install and
    migration documents actually tell an adopter to run, did the opposite.
    The --check half of the same bug was found and fixed on 2026-09-06; the
    writing half was left, and it is the half that deletes.

    The two escape hatches are asserted too, because a refusal with no way
    past it would just be a different way to strand someone: --check must
    still inspect without writing, and --allow-missing-sources must still
    let a deliberate removal through."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import precedent_materialize as _pm
    import build_views as bv
    pm_MaterializeError = _pm.MaterializeError

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        repo, team = tmp / 'consumer', tmp / 'precedent-team-widgets'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'widget-rule.md').write_text(
            '---\nslug: widget-rule\ntitle: Widgets are tested on the rig\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "changing widget firmware"\n'
            'index_clause: "test firmware on the rig, never the simulator"\n'
            'status: active\n---\n## Rule\nUse the rig.\n\n## Story\nIt drifted.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# Consumer\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n',
            encoding='utf-8')
        cfg = repo / 'precedent.json'
        cfg.write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main', 'visibility': 'private',
            'sources': [
                {'level': 'universal', 'name': 'precedent',
                 'path': 'precedent/universal'},
                {'level': 'team', 'name': 'precedent-team-widgets',
                 'path': str(team)}]}), encoding='utf-8')
        empty_user = tmp / 'user.json'
        empty_user.write_text(_json.dumps({'format_version': 1}), encoding='utf-8')

        psv.sync(str(repo), user_config=str(empty_user))
        landed = (repo / 'practices' / 'widget-rule.md').exists()

        # Now the CI state: the sibling clone is simply not there.
        shutil.rmtree(team)

        refused = False
        try:
            psv.sync(str(repo), user_config=str(empty_user))
        except pm_MaterializeError:
            refused = True
        survived = (repo / 'practices' / 'widget-rule.md').exists()

        # --check must still work: CI needs to inspect without writing.
        checked_ok = True
        try:
            psv.sync(str(repo), user_config=str(empty_user), check=True)
        except pm_MaterializeError:
            checked_ok = False
        survived_check = (repo / 'practices' / 'widget-rule.md').exists()

        # And the deliberate removal must still be possible.
        psv.sync(str(repo), user_config=str(empty_user), allow_missing=True)
        removed_on_request = not (repo / 'practices' / 'widget-rule.md').exists()

        results = [
            ('the shared practice lands while its source is reachable', landed),
            ('an unreachable declared source REFUSES the write', refused),
            ('and the tracked practice it contributed survives', survived),
            ('--check still inspects without writing', checked_ok and survived_check),
            ('--allow-missing-sources still permits a deliberate removal',
             removed_on_request),
        ]
        failed = [n for n, ok in results if not ok]
        check(f'precedent_sync_views refuses to rewrite a tracked tree from an '
              f'incomplete source set ({len(results)} stated cases, the '
              f'unreachable-in-CI source being the controlling case)',
              not failed, '; '.join(failed) if failed else '')


def check_withdrawn_table_never_links_a_successor_it_does_not_have():
    """The withdrawn-practices table must not link a successor that lives in
    another source (practice: doc-references-are-links,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. The withdrawn table landed that morning and
    rendered `in_force_at:` as `[slug](practices/slug.md)` unconditionally.
    The first shared set to regenerate with it produced MAP.md linking
    `practices/headline-capitalization.md` -- a UNIVERSAL practice, in a repo
    that has no such file -- and that set then failed its own `light-check`
    on a broken relative link, inside a generated file its own header tells
    it never to hand-edit. Unfixable from within that repo.

    Deduplication is exactly the case where this bites: a team or individual
    rule is dropped BECAUSE a universal one already says it, so the successor
    is in a different repo more often than not. `in_force_at:` names a slug,
    never a source, so the renderer cannot assume locality.

    Both directions are asserted. A local successor must still be a link --
    fixing this by never linking would be a regression that no
    broken-link check could catch, since nothing at all would be broken.
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'bv', ROOT / 'tools' / 'build_views.py')
    bv = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(bv)
    finally:
        sys.path.pop(0)

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        pdir = pathlib.Path(tmp) / 'practices'
        pdir.mkdir(parents=True)
        # The successor that IS here.
        (pdir / 'local-successor.md').write_text('x')
        here = pdir / 'gone-local.md'
        here.write_text('x')
        away = pdir / 'gone-away.md'
        away.write_text('x')

        def row(slug, target, f):
            return ({'slug': slug, 'status': 'deduplicated',
                     'in_force_at': target},
                    {'Story': 'Because.'}, str(f))

        out = '\n'.join(bv._render_withdrawn([
            row('gone-local', 'local-successor', here),
            row('gone-away', 'no-such-practice', away),
        ]))

        results.append(('a successor present in this repo is still linked',
                        '[local-successor](practices/local-successor.md)' in out))
        results.append(('a successor that is NOT in this repo is not linked',
                        '(practices/no-such-practice.md)' not in out))
        # Assert what it says instead: silence would satisfy the case above.
        results.append(('the absent successor is still named, so the reader '
                        'can find it', 'no-such-practice' in out))
        results.append(('and is told where to look',
                        'another source' in out))

    failed = [n for n, ok in results if not ok]
    check(f'the withdrawn table never links a successor this repo does not '
          f'have ({len(results)} stated cases)', not failed,
          '; '.join(failed) + (f' [rendered: {failure_detail(out, 300)!r}]' if failed else ''))


def check_summary_fields_drop_links_before_the_cut():
    """Every generator that copies prose into a one-line or length-capped
    field drops the prose's links BEFORE cutting it (tools/summary_text.py;
    practice: control-asserts-which-failure).

    THE INCIDENT, 2026-09-25. build_todo_index.py cut an item's title at
    `[:120]`, and in a consumer repo the cut landed inside a link's URL,
    leaving "(../meeting-notes/<name>-" open in todo/TODO.md. Harmless while
    that row was last; once a row came after it, the consumer's link checker
    paired the stray "(" with the next row's ")" and reported a broken link.
    This repo's own TODO.md and CLOSED.md already carried three such cut
    links, unnoticed.

    Each case builds prose whose link STRADDLES that generator's cut, and
    first asserts that a naive cut of it really is unbalanced -- otherwise a
    fixture that drifted off the cut would pass with the fix deleted. Then
    it asserts the generated field carries no "](" and balanced parentheses.
    """
    import tempfile
    import importlib.util

    def load(name):
        spec = importlib.util.spec_from_file_location(
            f'_sumtext_{name}', ROOT / 'tools' / f'{name}.py')
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.path.pop(0)
        return mod

    def straddling(limit):
        """Prose whose one link opens 12 characters before `limit`."""
        lead = 'w' * (limit - 12 - 1) + ' '
        return (lead + '[the notes](../meeting-notes/some-person-and-morgan-'
                '2026-09-25.md) and the rest of the sentence after it.')

    def naive_is_broken(text, limit):
        cut = text[:limit]
        return '](' in cut and cut.count('(') != cut.count(')')

    def clean(field):
        return '](' not in field and field.count('(') == field.count(')')

    results = []
    for limit in (120, 80, 400):
        results.append((f'fixture: a naive [:{limit}] cut really is broken',
                        naive_is_broken(straddling(limit), limit)))

    todo = load('build_todo_index')
    gotcha = load('build_gotcha_index')
    views = load('build_views')
    migrate = load('todo_migrate')

    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        tdir = repo / 'todo'
        tdir.mkdir()
        blocked = straddling(80).replace('"', "'")
        for slug, status in (('todo-2026-09-25-open-one', 'open'),
                             ('todo-2026-09-25-closed-one', 'done')):
            (tdir / f'{slug}.md').write_text(
                f'---\nslug: {slug}\nstatus: {status}\nkind: analysis\n'
                f'noted: 2026-09-25\nclosed: 2026-09-25\ndisposition: wait\n'
                f'blocked_on: "{blocked}"\n---\n\n## What\n\n'
                f'**{straddling(120)}**\n', encoding='utf-8')
        rc = todo.main(['--repo', str(repo)])
        results.append(('build_todo_index ran on the fixture', rc == 0))
        for name, want in (('TODO.md', 'todo-2026-09-25-open-one'),
                           ('CLOSED.md', 'todo-2026-09-25-closed-one')):
            text = (tdir / name).read_text(encoding='utf-8')
            rows = [l for l in text.splitlines() if want in l]
            results.append((f'{name} carries the fixture row', bool(rows)))
            for row in rows:
                cells = row.strip('|').split(' | ')
                results.append((f'{name}: the row still links its own item',
                                cells[0].strip().endswith(f'({want}.md)')))
                results.append((f'{name}: every copied cell is unlinked and '
                                f'balanced', all(clean(c) for c in cells[1:])))

        gdir = repo / 'gotchas'
        gdir.mkdir()
        (gdir / 'gotcha-2026-09-25-x.md').write_text(
            '---\nslug: gotcha-2026-09-25-x\nstatus: live\nnoted: 2026-09-25\n'
            f'---\n\n## Symptom\n\n{straddling(120)}\n\n## Story\n\nx\n',
            encoding='utf-8')
        rc = gotcha.main(['--repo', str(repo)])
        line = [l for l in (gdir / 'INDEX.md').read_text(encoding='utf-8')
                .splitlines() if 'gotcha-2026-09-25-x' in l]
        results.append(('gotcha INDEX: the symptom is unlinked, the story '
                        'link stays', rc == 0 and len(line) == 1
                        and clean(line[0].split('** [story]')[0])
                        and line[0].endswith('(gotcha-2026-09-25-x.md)')))

    reason = views._withdrawn_reason({'story': straddling(397)})
    results.append(('MAP.md withdrawn reason: unlinked and balanced at the '
                    '400 cut', clean(reason) and reason.endswith('...')))

    items = migrate.parse_todo_items(
        '# TODO\n\n- <a id="x"></a> ' + straddling(80 - 20) + '\n')
    results.append(('todo_migrate fallback title: unlinked and balanced at '
                    'the 80 cut', len(items) == 1 and clean(items[0].title)))

    # precedent_land.py: a practice landed without its own index_clause gets
    # one cut from its proposed rule at 76, and that clause is printed in
    # every occasion index that lists the practice.
    land = load('precedent_land')
    results.append(('fixture: a naive [:76] cut really is broken',
                    naive_is_broken(straddling(76), 76)))
    fm = land._render_practice({'slug': 'zzz-cut', 'title': 'Cut'},
                               straddling(76), 'observed', 'harness',
                               'universal')
    clause = next((l for l in fm.splitlines()
                   if l.startswith('index_clause:')), '')
    results.append(('precedent_land default index_clause: unlinked and '
                    'balanced at the 76 cut',
                    bool(clause) and clean(clause.split(':', 1)[1])))

    failed = [n for n, ok in results if not ok]
    check(f'summary fields drop links before the cut ({len(results)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_assumed_visibility_never_deletes_practices():
    """An ASSUMED visibility must never remove practice files that are
    already in a consumer's tree (practice: very-deep-check, reported by a
    real repo).

    repo_is_public() treats an undeclared `visibility` as public, and that
    default is right: it fails safe against publishing private practice text
    into a world-readable repo, which is the failure that motivated it.

    It fails UNSAFE in the other direction. An existing PRIVATE consumer that
    never declared the field loses every team- and individual-level practice
    from its tracked tree on its next sync -- silently, as a committable diff
    that reads like a deliberate removal. Reported 2026-09-07 by a real
    private repo updating to this engine: 15 practices would have gone, and
    the person caught it only by checking that repo's actual visibility by
    hand.

    So the assumption is allowed to WITHHOLD, and not allowed to DELETE. A
    declared visibility proceeds either way -- that is someone choosing.
    Three states, all asserted, because fixing this by simply reverting the
    default would restore the publication hazard it was written for."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import precedent_materialize as _pm
    import build_views as bv

    def _fixture(tmp, visibility):
        repo, team = tmp / 'consumer', tmp / 'team-src'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'team-only-rule.md').write_text(
            '---\nslug: team-only-rule\ntitle: A rule only this team has\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "doing team things"\nindex_clause: "do the team thing"\n'
            'status: active\n---\n## Rule\nDo it.\n\n## Story\nDecided.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# c\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
        cfg = {'format_version': 1, 'base_branch': 'main',
               'sources': [
                   {'level': 'universal', 'name': 'precedent',
                    'path': 'precedent/universal'},
                   {'level': 'team', 'name': 'precedent-team-x',
                    'path': str(team)}]}
        if visibility:
            cfg['visibility'] = visibility
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        return repo

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        user = tmp / 'user.json'
        user.write_text(_json.dumps({'format_version': 1}), encoding='utf-8')
        results = []

        # Seed a PRIVATE consumer that really carries the shared practice.
        repo = _fixture(tmp, 'private')
        psv.sync(str(repo), user_config=str(user))
        seeded = (repo / 'practices' / 'team-only-rule.md').exists()
        results.append(('a private consumer materializes the shared practice', seeded))

        # Now the reported state: the declaration goes away.
        cfg = _json.loads((repo / 'precedent.json').read_text())
        cfg.pop('visibility', None)
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        refused = False
        try:
            psv.sync(str(repo), user_config=str(user))
        except _pm.MaterializeError:
            refused = True
        results.append(('an ASSUMED visibility refuses rather than deleting',
                        refused))
        results.append(('and the practice file survives the refusal',
                        (repo / 'practices' / 'team-only-rule.md').exists()))

        # Declared private: keep it. This is the control that stops the fix
        # from simply blocking every consumer.
        cfg['visibility'] = 'private'
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        psv.sync(str(repo), user_config=str(user))
        results.append(('declaring private keeps it',
                        (repo / 'practices' / 'team-only-rule.md').exists()))

        # Declared public: withhold it. The publication hazard the default
        # exists for must still be closed.
        cfg['visibility'] = 'public'
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        psv.sync(str(repo), user_config=str(user))
        results.append(('declaring public still withholds it',
                        not (repo / 'practices' / 'team-only-rule.md').exists()))

        failed = [n for n, ok in results if not ok]
        check(f'an assumed visibility withholds but never deletes '
              f'({len(results)} stated cases: seeded, refused, survived, and '
              f'both declared states)',
              not failed, '; '.join(failed) if failed else '')


def check_due_reminder_reaches_the_reply():
    """build_todo_index.remind() -- the reply gate's DUE REMINDER block
    (practice: todo-reminder, the-boildown item 10). Against a planted
    todo/ (fixture-owns-its-state: every field an assertion reads is
    written here): only an open `ask` item whose remind_on has arrived is
    due, the longest-due is named first, one an earlier reply already
    carries is skipped, and nothing due prints nothing."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_todo_index as bti

    def item(slug, **fm):
        fields = {'slug': slug, 'title': f'"{slug} title"', 'status': 'open',
                  'kind': 'manual', 'noted': '2026-01-01'}
        fields.update(fm)
        body = ''.join(f'{k}: {v}\n' for k, v in fields.items())
        return f'---\n{body}---\n## What\nx\n'

    def run(files, replies=None):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-due-'))
        try:
            for name, text in files.items():
                p = d / 'todo' / f'{name}.md'
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding='utf-8')
            transcript = None
            if replies is not None:
                transcript = d / 't.jsonl'
                transcript.write_text(''.join(
                    json.dumps({'type': 'assistant', 'message': {
                        'usage': {}, 'content': [{'type': 'text', 'text': r}]}})
                    + '\n' for r in replies), encoding='utf-8')
            return bti.remind(d, str(transcript) if transcript else None)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    files = {
        'todo-2026-01-01-older': item('todo-2026-01-01-older',
                                      disposition='ask', remind_on='2020-01-02'),
        'todo-2026-01-01-oldest': item('todo-2026-01-01-oldest',
                                       disposition='ask', remind_on='2020-01-01'),
        'todo-2026-01-01-future': item('todo-2026-01-01-future',
                                       disposition='ask', remind_on='2999-01-01'),
        'todo-2026-01-01-waiting': item('todo-2026-01-01-waiting',
                                        disposition='wait', remind_on='2020-01-01'),
        'todo-2026-01-01-finished': item('todo-2026-01-01-finished',
                                         status='done', disposition='ask',
                                         remind_on='2020-01-01'),
    }
    cases = []
    out = run(files)
    cases.append(('the longest-due open ask item is named, and counts the '
                  'one other due', 'todo-2026-01-01-oldest.md' in out
                  and '1 other reminder' in out, out))
    out = run(files, ['earlier: see todo/todo-2026-01-01-oldest.md'])
    cases.append(('an item an earlier reply already carried is skipped for '
                  'the next one', 'todo-2026-01-01-older.md' in out, out))
    out = run(files, ['todo-2026-01-01-oldest and todo-2026-01-01-older'])
    cases.append(('every due item already shown prints nothing', out == '', out))
    out = run({k: v for k, v in files.items()
               if k not in ('todo-2026-01-01-oldest', 'todo-2026-01-01-older')})
    cases.append(('not yet due, wait, and done items print nothing',
                  out == '', out))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a due reminder reaches the reply gate, by date, once per '
          f'conversation ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:200]!r}' for n, d in bad))


def check_typography_finishes_outward_text_and_every_engine_page():
    """practice: curly-quotes. typography.py is the one copy of the rules
    that turn Markdown's plain keys into finished typography for an outside
    reader, and finish_html.finish() runs every HTML page the engine writes
    through it. Its cases moved here with the practice on 2026-10-16, from
    the writing set's test_typography.sh.

    Each direction: `--` becomes an em dash and a number range an en dash,
    while a date, a code, a code span, a link address and an escape stay as
    typed; quotes curl, around an inline tag too; an HTML page changes only
    in the text a reader sees, never in a tag, an attribute, a comment, a
    script or code, and a second run changes nothing. finish() applies it,
    and hands a page back as built where typography.py is missing or too old
    for HTML. -> (ok, detail, failure)."""
    import shutil, subprocess as sp_, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import typography as ty
    S = ty.smarten
    cases = []
    for given, want in [
            ("word--word", "word\u2014word"), ("a -- b", "a \u2014 b"),
            ("x---y", "x\u2014y"), ("a ---- rule", "a ---- rule"),
            ("1990-2000", "1990\u20132000"), ("pages 10-20", "pages 10\u201320"),
            ("9-5, 3:00-5:00, 2.5-3", "9\u20135, 3:00\u20135:00, 2.5\u20133"),
            ("on 2026-10-13", "on 2026-10-13"), ("555-123-4567", "555-123-4567"),
            ("PR-173, B-52, 1-on-1, 10-K", "PR-173, B-52, 1-on-1, 10-K"),
            ("Monday-Friday", "Monday-Friday"),
            ("a \u2014 b \u2013 c \u201cq\u201d", "a \u2014 b \u2013 c \u201cq\u201d"),
            ('a "quote" and it\'s', "a \u201cquote\u201d and it\u2019s"),
            ('**"bold"**', "**\u201cbold\u201d**"),
            (ty.LINK_OPEN + "https://x/1990-2000--a" + ty.LINK_MID + "t",
             ty.LINK_OPEN + "https://x/1990-2000--a" + ty.LINK_MID + "t"),
            ("1990\\-2000", "1990\\-2000"),
            ("run `git push --force` -- now", "run `git push --force` \u2014 now"),
            ("`1990-2000` and 1990-2000", "`1990-2000` and 1990\u20132000")]:
        got = S(given)
        cases.append((f'smarten({given!r})', got == want, f'{got!r}, wanted {want!r}'))
    H = getattr(ty, 'smarten_html', None)
    for given, want in [
            ('<p>The shape ("if we build this, here&#x27;s what") -- done.</p>',
             '<p>The shape (\u201cif we build this, here\u2019s what\u201d) \u2014 done.</p>'),
            ('<p>"<b>word</b>" and <a href="x--y.html" title="a \'t\'">it\'s</a></p>',
             '<p>\u201c<b>word</b>\u201d and <a href="x--y.html" title="a \'t\'">it\u2019s</a></p>'),
            ('<pre>git push --force "x"</pre><p>"a"</p>',
             '<pre>git push --force "x"</pre><p>\u201ca\u201d</p>'),
            ('<p>run <code>--check</code> -- and 1990-2000</p>',
             '<p>run <code>--check</code> \u2014 and 1990\u20132000</p>'),
            ('<!-- a -- "b" --><script>var a="--";</script><p>&quot;q&quot; &amp; 2026-10-16</p>',
             '<!-- a -- "b" --><script>var a="--";</script><p>\u201cq\u201d &amp; 2026-10-16</p>'),
            ('<li>"one"</li><li>"two"</li>', '<li>\u201cone\u201d</li><li>\u201ctwo\u201d</li>')]:
        got = H(given) if H else None
        cases.append((f'smarten_html({given[:40]!r})', got == want and H(want) == want,
                      f'{got!r}, wanted {want!r}'))

    page = '<p>"a" -- b</p>'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-finish-html-'))
    try:
        def run(typography):
            d = tmp / str(len(cases))
            d.mkdir()
            shutil.copy(ROOT / 'tools' / 'finish_html.py', d / 'finish_html.py')
            if typography is not None:
                (d / 'typography.py').write_text(typography, encoding='utf-8')
            r = sp_.run([sys.executable, '-c',
                         'import sys; sys.path.insert(0, sys.argv[1]); '
                         'from finish_html import finish; '
                         'sys.stdout.write(finish(sys.argv[2]))', str(d), page],
                        capture_output=True, text=True)
            return r.stdout
        got = run((ROOT / 'tools' / 'typography.py').read_text(encoding='utf-8'))
        cases.append(('finish() applies the engine\'s typography to a page',
                      got == '<p>\u201ca\u201d \u2014 b</p>', got))
        got = run(None)
        cases.append(('finish() without typography.py beside it: the page as built',
                      got == page, got))
        got = run('def smarten(s):\n    return s\n')
        cases.append(('finish() with a typography.py too old for HTML: the page as built',
                      got == page, got))
        # A file a set used to ship and the engine now carries is never
        # named as a leftover to delete by hand (precedent_materialize).
        import precedent_materialize as pm_
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'files': ['typography.py']}), encoding='utf-8')
        owned = pm_._engine_owned(repo)
        cases.append(('an engine file a set used to ship is not a stale ship',
                      owned == {'tools/typography.py'}
                      and pm_._engine_owned(tmp / 'nowhere') == set(), repr(owned)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


