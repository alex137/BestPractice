# The harness tests for the very deep check and the fleet audit
#
# tools/harness/vh_very_deep_check.py -- part of the verification harness:
# the very deep check and the fleet audit.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def _changed_touches(*rel_paths):
    """True if this push touched any of `rel_paths` -- same changed-scope
    principle check_machine_readable_files_parse already uses ("did I just
    break something", not "is the whole repo well"; the whole-tree sweep is
    very_deep_check.py's on-demand job), reused here for a handful of the
    slower checks below that exist to test very_deep_check.py's own logic
    rather than this repo's practice content.

    Deliberately scoped to the DIRECT file(s) each caller names, not those
    files' own transitive imports: a change to one of very_deep_check.py's
    helper modules that alters its behavior without touching
    very_deep_check.py or the named file itself would not be caught here --
    only by a later on-demand very deep check run. That is a real, accepted
    gap (documented at each call site), not an oversight: enumerating a
    transitive closure by hand goes stale the moment those imports change,
    and a check that silently narrows itself is worse than one that says
    plainly what it does not cover.

    parse_check.changed() itself never silently narrows: with no base
    branch to diff against (e.g. a shallow clone with no ancestor in
    common), it falls back to the WHOLE tracked tree and labels the scope
    accordingly -- so `touched` is still True in that fallback case, same
    as if this returned unscoped.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_parse_check', ROOT / 'tools' / 'parse_check.py')
    pcheck = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcheck)
    changed_paths, scope = pcheck.changed(ROOT)
    changed_set = set(changed_paths)
    return any(p in changed_set for p in rel_paths), scope
def check_visibility_audit_reads_repo_names_out_of_prose():
    """The visibility audit's reference finder takes the name a sentence
    means, once (practice: very-deep-check).

    WHY. On 2026-10-11 it read "see owner/name." as a repository called
    "name." beside "name", and api.github.com/repos/OWNER/NAME as a
    repository "OWNER" of an owner called "repos" -- sixteen extra names in
    this tree, each one a GitHub call over the run's declared budget."""
    import very_deep_check as vdc
    text = ('see https://github.com/acme/widget. then '
            'https://api.github.com/repos/acme/toolkit/actions, '
            '*https://www.github.com/acme/star.* and "acme/quoted." '
            'and https://github.com/acme/plain')
    urls = set(vdc._URL_REF_RE.findall(text))
    bare = set(vdc._bare_ref_re({'acme'}).findall(text))
    cases = [
        ('a sentence-ending period is not part of the name',
         ('acme', 'widget') in urls and ('acme', 'widget.') not in urls),
        ('an API path names the repository after /repos/',
         ('acme', 'toolkit') in urls
         and not any(o == 'repos' for o, _ in urls)),
        ('a period before closing punctuation ends the name too',
         ('acme', 'star') in urls),
        ('a plain URL still reads as before', ('acme', 'plain') in urls),
        ('bare prose under a known owner drops its period as well',
         ('acme', 'quoted') in bare and ('acme', 'quoted.') not in bare),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'the visibility audit reads repository names out of prose '
          f'({len(cases)} stated cases)', not failed,
          '; '.join(failed) + f' -- urls {sorted(urls)}, bare {sorted(bare)}')


def check_very_deep_check_boundary_audit_reads_the_setting():
    """very_deep_check.py's CONTRIBUTOR BOUNDARY section reports a stale
    generated CODEOWNERS as a finding, a repo with no registry as drawing no
    boundary, and GitHub's answer -- or its absence -- in its own words.

    Added 2026-09-14 with the section (practice: very-deep-check, pass 2:
    a boundary is a setting, not a document). The API is stubbed at the
    module boundary of precedent_boundary_check, and each case asserts the
    printed row for that case (practice: control-asserts-which-failure);
    the fixture owns the three token variables the tool reads
    (practice: fixture-owns-its-state)."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import precedent_boundary_check as pbc
    import build_codeowners as bco

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vdc-boundary-'))
    cases = []
    real_fetch = pbc.fetch_protection
    saved = {k: os.environ.get(k) for k in ('PRECEDENT_GITHUB_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN')}
    good = {'required_pull_request_reviews': {'require_code_owner_reviews': True,
                                              'required_approving_review_count': 0},
            'enforce_admins': {'enabled': True}}
    try:
        for k in saved:
            os.environ.pop(k, None)
        project = tmp / 'project'
        project.mkdir()
        subprocess.run(['git', 'init', '-q', str(project)], capture_output=True)
        subprocess.run(['git', '-C', str(project), 'remote', 'add', 'origin',
                        'https://github.com/example/doc-project.git'], capture_output=True)
        (project / 'precedent.json').write_text(json.dumps({
            'base_branch': 'main',
            'maintainers': [{'name': 'M', 'github': 'maint'}],
            'owned_paths': [{'path': '/.github/', 'why': 'workflows'}]}), encoding='utf-8')
        bare = tmp / 'bare'
        bare.mkdir()
        (bare / 'precedent.json').write_text('{"base_branch": "main"}', encoding='utf-8')
        sources = [{'level': 'team', 'name': 'fixture-team', 'path': str(bare)}]

        def run(root, skip_api=False):
            out = io.StringIO()
            f, n = vdc.boundary_audit(root, sources, skip_api=skip_api, out=out)
            return f, n, out.getvalue()

        f, n, out = run(project)
        cases.append(('a project whose registry has no generated CODEOWNERS yet is a finding',
                      any('does not exist' in x for x in f) and 'FINDING' in out, out))
        cases.append(('a repo with no registry is reported as drawing no boundary, never as clean',
                      'draws no boundary' in out and not any('fixture-team' in x for x in f), out))

        with contextlib.redirect_stdout(io.StringIO()):
            bco.main(check_only=False, root=project)
        (project / '.github' / 'CODEOWNERS').write_text('/.github/ @someone-else\n', encoding='utf-8')
        f, n, out = run(project, skip_api=True)
        cases.append(('a hand-edited CODEOWNERS is a finding naming the mismatch',
                      any('does not match' in x for x in f), out))
        cases.append(('--skip-liveness leaves protection unasked and says so as a note, not a pass',
                      any('not asked' in x for x in n) and 'not asked' in out, out))

        with contextlib.redirect_stdout(io.StringIO()):
            bco.main(check_only=False, root=project)
        f, n, out = run(project)
        cases.append(('a current CODEOWNERS with no token is UNVERIFIED -- a note, never a finding',
                      not f and any('UNVERIFIED' in x for x in n) and 'not a pass' in ''.join(n), out))

        os.environ['GITHUB_TOKEN'] = 'ghp_NOTAREALTOKEN' + 'y' * 8
        pbc.fetch_protection = lambda o, nm, b, tok: (200, good)
        f, n, out = run(project)
        cases.append(('protection on and CODEOWNERS current is a PASS row with no finding',
                      not f and 'PASS' in out and 'shaped as the plan needs' in out, out))
        pbc.fetch_protection = lambda o, nm, b, tok: (404, {'message': 'Branch not protected'})
        f, n, out = run(project)
        cases.append(('an unprotected base branch is a finding naming it',
                      any('NOT protected' in x for x in f), out))

        # A practice set draws its boundary with approvers.json, and the
        # setting that makes it bind is not read: a note, so the section
        # never prints "current and on" over it (2026-10-17).
        aset = tmp / 'aset'
        aset.mkdir()
        (aset / 'approvers.json').write_text(json.dumps({
            'format_version': 1,
            'approvers': [{'name': 'A', 'github': 'approver'}]}), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            bco.main(check_only=False, root=aset)
        out = io.StringIO()
        f, n = vdc.boundary_audit(aset, [], out=out)
        out = out.getvalue()
        cases.append(('a set drawn by approvers.json says protection was not '
                      'read -- a note, never clean',
                      not f and any('approvers.json' in x and 'not a pass' in x
                                    for x in n) and 'current' in out, out))
    finally:
        pbc.fetch_protection = real_fetch
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'very_deep_check.py\'s CONTRIBUTOR BOUNDARY reads the setting, not the '
          f'document ({len(cases)} stated cases: missing file, no registry, '
          f'hand-edited file, --skip-liveness, no token, PASS, unprotected, a set\'s '
          f'approvers.json)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))


def check_very_deep_check_warnings_are_judged_not_just_counted():
    """very_deep_check.py's WARNINGS section: every warning group is open,
    excluded for good, excluded until a date, or past that date and open
    again; an exclusion that matches nothing is stale; a malformed one is a
    registry problem and is not applied; and the write-up gets a
    `## Warnings` block that a second write replaces rather than repeats.

    Added 2026-10-11 with the section (practice: very-deep-check, Pass 2
    question 24). review() is pure and takes a fixed date, and the registry
    and write-up live in a temporary repo the fixture builds
    (practice: fixture-owns-its-state). Each case asserts the tool's own
    words or status (practice: control-asserts-which-failure)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import warning_review as wr
    import very_deep_check as vdc

    cases = []
    lint_out = ('noise\ndoc_lint strict json: ' + json.dumps({'scanned': 3, 'classes': {
        'unlinked file reference': {'INSTALL.md': 5, 'todo/a.md': 2, 'spec/x.md': 1}}}))
    groups = wr.doc_lint_groups(lint_out)
    cases.append(('doc_lint\'s --json line becomes one group per (class, file)',
                  groups is not None and sorted((g['path'], g['count']) for g in groups)
                  == [('INSTALL.md', 5), ('spec/x.md', 1), ('todo/a.md', 2)], repr(groups)))
    cases.append(('a doc_lint with no --json line is reported unread, never as clean',
                  wr.doc_lint_groups('doc_lint --strict FAIL: 3 finding(s)') is None, ''))
    pc_out = ('ADVISORY   some-check — findings below do not fail this run\n'
              '    practices/a.md: says a thing\n    practices/a.md: says another\n'
              '  the rule:\n    rule text: not a finding\n'
              'SKIPPED    other — not a warning\n')
    pcg = wr.precedent_check_groups(pc_out)
    cases.append(('an advisory check\'s findings group by check and file, and its rule text is not one',
                  [(g['kind'], g['path'], g['count']) for g in pcg] == [('some-check', 'practices/a.md', 2)],
                  repr(pcg)))
    cases.append(('the session check\'s `??` rows are not collected: they '
                  'change from session to session, so an exclusion of one '
                  'goes stale',
                  not any(src[0] == 'precedent_session_check'
                          for src in wr.LINE_SOURCES),
                  [src[0] for src in wr.LINE_SOURCES]))
    lg = wr.line_groups('build_views', 'WARNING', 'build_views WARNING: 3 over\nbuild_views WARNING: 4 over\nok\n',
                        re.compile(r'\bWARNING:\s*(.+)'))
    cases.append(('WARNING lines differing only in a number are one group',
                  len(lg) == 1 and lg[0]['count'] == 2 and lg[0]['text'] == 'N over', repr(lg)))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vdc-warnings-'))
    try:
        (tmp / 'tools').mkdir()
        (tmp / 'spec').mkdir()
        (tmp / 'tools' / 'warning_exclusions.json').write_text(json.dumps({'exclusions': [
            {'source': 'doc_lint', 'kind': 'unlinked file reference', 'path': 'todo/*',
             'term': 'permanent', 'why': 'closed records are history', 'decided': '2026-10-11', 'by': 'agent'},
            {'source': 'doc_lint', 'kind': 'unlinked file reference', 'path': 'spec/*',
             'term': 'temporary', 'why': 'linking next run', 'revisit': '2026-10-01',
             'decided': '2026-09-01', 'by': 'agent'},
            {'source': 'doc_lint', 'kind': 'process residue', 'path': '*',
             'term': 'permanent', 'why': 'gone now', 'decided': '2026-09-01', 'by': 'agent'},
            {'source': 'doc_lint', 'kind': 'x', 'term': 'permanent', 'decided': '2026-10-11', 'by': 'agent'},
            {'source': 'doc_lint', 'kind': 'y', 'term': 'permanent', 'why': 'w',
             'decided': '2026-10-11', 'by': 'Morgan'},
        ]}), encoding='utf-8')
        entries, problems = wr.load_registry(tmp)
        cases.append(('an exclusion with no reason is a registry problem and is not applied',
                      any('exclusion 4 is missing why' in p for p in problems) and len(entries) == 3,
                      repr(problems)))
        cases.append(('a person\'s exclusion without its strength is a registry problem',
                      any('exclusion 5' in p and 'decision-strength' in p for p in problems),
                      repr(problems)))
        result = wr.review(groups, entries, ['doc_lint'], today='2026-10-11')
        status = {r['path']: r['status'] for r in result['rows']}
        cases.append(('an unmatched group is open', status.get('INSTALL.md') == 'open', repr(status)))
        cases.append(('a permanent exclusion holds', status.get('todo/a.md') == 'excluded, permanent', repr(status)))
        cases.append(('a temporary exclusion past its revisit date is lapsed, open again',
                      status.get('spec/x.md') == 'lapsed', repr(status)))
        future = wr.review(groups, entries, ['doc_lint'], today='2026-09-15')
        cases.append(('a temporary exclusion before its date holds',
                      {r['path']: r['status'] for r in future['rows']}.get('spec/x.md') == 'excluded, temporary',
                      repr(future['rows'])))
        cases.append(('an exclusion matching nothing is stale',
                      [e['kind'] for e in result['stale']] == ['process residue'], repr(result['stale'])))
        unread = wr.review(groups, entries, [], today='2026-10-11')
        cases.append(('a source that was not read proves no exclusion stale', not unread['stale'],
                      repr(unread['stale'])))
        # status_in (2026-10-30): only the files whose own frontmatter says
        # they are finished; the live one beside them stays open.
        (tmp / 'gotchas').mkdir()
        (tmp / 'gotchas' / 'gotcha-old.md').write_text('---\nstatus:   retired\n---\nx\n',
                                                       encoding='utf-8')
        (tmp / 'gotchas' / 'gotcha-live.md').write_text('---\nstatus:   live\n---\nx\n',
                                                        encoding='utf-8')
        ent = [{'source': 'doc_lint', 'kind': 'unlinked file reference',
                'path': 'gotchas/gotcha-*.md', 'status_in': ['retired'], 'term': 'permanent',
                'why': 'history', 'decided': '2026-10-30', 'by': 'agent', '_index': 1}]
        gs = [{'source': 'doc_lint', 'kind': 'unlinked file reference', 'path': f'gotchas/{n}',
               'text': '', 'count': 1} for n in ('gotcha-old.md', 'gotcha-live.md')]
        st = {r['path']: r['status'] for r in
              wr.review(gs, ent, ['doc_lint'], today='2026-10-30', root=tmp)['rows']}
        cases.append(('a status_in exclusion takes the retired file and leaves the live one '
                      'beside it open',
                      st == {'gotchas/gotcha-old.md': 'excluded, permanent',
                             'gotchas/gotcha-live.md': 'open'}, repr(st)))
        reg = json.loads((tmp / 'tools' / 'warning_exclusions.json').read_text(encoding='utf-8'))
        reg['exclusions'].append({k: v for k, v in ent[0].items() if k != '_index'})
        (tmp / 'tools' / 'warning_exclusions.json').write_text(json.dumps(reg), encoding='utf-8')
        cases.append(('status_in is a known registry key',
                      not any('unknown key' in p for p in wr.load_registry(tmp)[1]),
                      repr(wr.load_registry(tmp)[1])))
        text = wr.render_text(result, problems, [], previous=9)
        cases.append(('the text names the open count against the previous run',
                      'Open at the previous run: 9; now: 6.' in text, text))
        md = wr.render_markdown(result, problems, [], previous=9, start=8)
        cases.append(('the block names this run\'s decisions, with who made them',
                      'Exclusions decided this run: 1.' in md and 'by the session -- closed records are history' in md,
                      md))
        bare = tmp / 'no-registry'
        bare.mkdir()
        md2 = wr.render_markdown(result, problems, [], repo_root=bare)
        cases.append(('with no registry file the block links none (a dead '
                      'link refused the run record in a set)',
                      '](../tools/warning_exclusions.json)' not in md2
                      and 'creates the registry' in md2, md2))
        doc = tmp / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        doc.write_text('# Run\n\nBody.\n', encoding='utf-8')
        vdc._write_warnings_block(tmp, 'FIRST')
        vdc._write_warnings_block(tmp, 'SECOND')
        body = doc.read_text(encoding='utf-8')
        cases.append(('the write-up gets one ## Warnings block, replaced on the second write',
                      body.count('## Warnings') == 1 and 'SECOND' in body and 'FIRST' not in body
                      and body.startswith('# Run\n\nBody.\n'), body))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'very_deep_check.py\'s WARNINGS judges every group, not just counts them '
          f'({len(cases)} stated cases: parsing, open, permanent, temporary, lapsed, '
          f'stale, malformed, write-up block)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))


def check_very_deep_check_token_budgets_are_shown_and_fire_tested():
    """very_deep_check.py's TOKEN BUDGETS section: every budget gets a row
    with its number whether or not it is over; a limit above the person's
    approved max is NOT APPROVED; a repo's own check that reports a planted
    overage is 'fired', one that passes it is 'DID NOT FIRE', one already
    red unplanted is 'not run'; and the write-up gets one `## Token budgets`
    block that a second write replaces.

    Added 2026-10-17 with the section (Morgan: "even if they all pass,
    share the exact numbers, the limits ... in the very deep check
    document"). The fixture repo and its stand-in precedent_check.py are
    built here (practice: fixture-owns-its-state); each case asserts the
    tool's own words (practice: control-asserts-which-failure)."""
    import io, shutil, subprocess, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc

    honest = (
        "import json, pathlib, sys\n"
        "root = pathlib.Path(__file__).resolve().parent.parent\n"
        "reg = json.loads((root / 'tools' / 'session_load_budgets.json').read_text())\n"
        "n = int(len((root / 'AGENTS.md').read_text().split()) * 1.3)\n"
        "slug = sys.argv[sys.argv.index('--only') + 1]\n"
        "bad = {'session-load-budget': n > reg['surfaces']['AGENTS.md']['ceiling'],\n"
        "       'budget-within-approval': reg['surfaces']['AGENTS.md']['ceiling'] >\n"
        "           reg['approved_budgets']['surfaces/AGENTS.md']['max'],\n"
        "       'loader-within-caps': reg.get('resident_block_tokens', 9) < 5}.get(slug, False)\n"
        "print(f'precedent_check: {0 if bad else 1} passed, {1 if bad else 0} violated, 0 advisory')\n")
    blind = "print('precedent_check: 1 passed, 0 violated, 0 advisory')\n"
    red = "print('precedent_check: 0 passed, 1 violated, 0 advisory')\n"

    def make(tmp, engine, ceiling=100, approved=100):
        (tmp / 'tools').mkdir(parents=True)
        (tmp / 'spec').mkdir()
        (tmp / 'AGENTS.md').write_text(' '.join(['word'] * 40) + '\n', encoding='utf-8')
        (tmp / 'tools' / 'session_load_budgets.json').write_text(json.dumps({
            'resident_block_tokens': 100,
            'surfaces': {'AGENTS.md': {'ceiling': ceiling}},
            'approved_budgets': {'surfaces/AGENTS.md': {'max': approved}}}), encoding='utf-8')
        (tmp / 'tools' / 'precedent_check.py').write_text(engine, encoding='utf-8')
        (tmp / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md').write_text('# Run\n\nBody.\n', encoding='utf-8')
        for cmd in (['init', '-q'], ['add', '-A'],
                    ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x']):
            subprocess.run(['git', '-C', str(tmp)] + cmd, check=True, capture_output=True)

    cases, tmps = [], []
    try:
        def fresh():
            t = pathlib.Path(tempfile.mkdtemp(prefix='vdc-budgets-')) / 'r'
            tmps.append(t.parent)
            return t
        a = fresh(); make(a, honest)
        rows = vdc.budget_rows(a, 'a')
        agents = [r for r in rows if r['what'] == 'AGENTS.md']
        cases.append(('a passing budget still gets its row, number and limit',
                      len(agents) == 1 and agents[0]['measured'] == 52 and agents[0]['limit'] == 100
                      and vdc._budget_status(agents[0]) == 'ok', repr(rows)))
        cases.append(('within the headroom floor is near',
                      vdc._budget_status(dict(agents[0], measured=97)) == 'near', ''))
        cases.append(('over the limit is OVER',
                      vdc._budget_status(dict(agents[0], measured=101)).startswith('OVER'), ''))
        cases.append(('a limit above the approved max is NOT APPROVED',
                      'NOT APPROVED' in vdc._budget_status(dict(agents[0], limit=150)), ''))
        fires = {f[1]: f[3] for f in vdc.budget_fire_test(a, 'a')}
        cases.append(('an honest check fires on every plant it can carry',
                      fires.get('AGENTS.md ceiling lowered under its size') == 'fired'
                      and fires.get('AGENTS.md ceiling raised 5,000 with no approval') == 'fired'
                      and fires.get('resident-block cap lowered under its size') == 'fired', repr(fires)))
        cases.append(('a plant with no budget to plant on is not run, never fired',
                      fires.get('session-file ceiling lowered under its size') == 'not run', repr(fires)))
        wt = subprocess.run(['git', '-C', str(a), 'worktree', 'list'], capture_output=True, text=True).stdout
        cases.append(('the throwaway worktree is gone afterwards', wt.count('\n') == 1, wt))
        b = fresh(); make(b, blind)
        fires_b = {f[1]: f[3] for f in vdc.budget_fire_test(b, 'b')}
        cases.append(('a check that passes a planted overage is DID NOT FIRE',
                      fires_b.get('AGENTS.md ceiling lowered under its size') == 'DID NOT FIRE', repr(fires_b)))
        c = fresh(); make(c, red)
        fires_c = {f[1]: (f[3], f[4]) for f in vdc.budget_fire_test(c, 'c')}
        got = fires_c.get('AGENTS.md ceiling lowered under its size')
        cases.append(('a check already red unplanted proves nothing: not run',
                      got and got[0] == 'not run' and 'unplanted' in got[1], repr(fires_c)))
        vdc.token_budgets_section([('a', a)], a, fire=False, out=io.StringIO())
        vdc.token_budgets_section([('a', a)], a, fire=False, out=io.StringIO())
        body = (a / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md').read_text(encoding='utf-8')
        cases.append(('the write-up gets one ## Token budgets block with the numbers, even all passing',
                      body.count('## Token budgets') == 1 and '| 52 | 100 | 52% |' in body
                      and body.startswith('# Run\n\nBody.\n'), body))
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'very_deep_check.py\'s TOKEN BUDGETS shows every number and proves the checks fire '
          f'({len(cases)} stated cases: rows, near, over, unapproved, fired, not run, '
          f'did not fire, cleanup, write-up block)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))


def check_very_deep_check_lists_the_longest_rules():
    """very_deep_check.py's LONGEST RULES section: the longest quarter of a
    repo's active Rules (n/4 rounded half up, at least one), longest first,
    by words in the `## Rule` section alone; a retired practice is not
    counted however long its Rule, and a long Detail does not make a Rule
    long. In a public repo a private set's slugs stay out of the write-up's
    `## Long Rules` block, which a second write replaces; and the account
    check refuses a run from 2026-11-01 on whose account has no such block.

    Added 2026-10-31 with the section (practice: very-deep-check, Pass 3;
    Morgan, strength: assented: "maybe we add to very deep check to always
    review like the 25% of all the rules that are the longest in that repo
    and shorten them like you did?"). The repositories are temporary ones
    the test builds (practice: fixture-owns-its-state); each case asserts
    the tool's own words (practice: control-asserts-which-failure)."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import precedent_check as pc

    def practice(d, slug, rule_words, status='active', detail_words=0):
        (d / 'practices').mkdir(parents=True, exist_ok=True)
        body = ('---\nslug:        ' + slug + '\nstatus:      ' + status
                + '\n---\n## Rule\n' + ' '.join(['must'] * rule_words) + '\n'
                + ('\n## Detail\n' + ' '.join(['how'] * detail_words) + '\n'
                   if detail_words else ''))
        (d / 'practices' / f'{slug}.md').write_text(body, encoding='utf-8')

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vdc-long-rules-'))
    try:
        repo, priv = tmp / 'repo', tmp / 'private-set'
        # Seven active: the quarter is (7 + 2) // 4 = 2. The retired one and
        # the long-Detail one are the controls.
        for slug, n in (('fx-a', 40), ('fx-b', 300), ('fx-c', 120),
                        ('fx-d', 300), ('fx-e', 10), ('fx-f', 75)):
            practice(repo, slug, n)
        practice(repo, 'fx-retired', 5000, status='retired')
        practice(repo, 'fx-long-detail', 20, detail_words=5000)
        r = vdc.longest_rules(repo / 'practices')
        cases.append(('the longest quarter, longest first, ties by slug',
                      r['listed'] == [('fx-b', 300), ('fx-d', 300)], repr(r)))
        cases.append(('a retired practice is not counted and a long Detail '
                      'is not a long Rule',
                      r['active'] == 7 and r['median'] == 75, repr(r)))
        practice(priv, 'fx-private-one', 30)
        (priv / 'precedent-source.json').write_text(
            json.dumps({'name': 'fx-private', 'level': 'individual',
                        'visibility': 'private'}), encoding='utf-8')
        cases.append(('a set of one lists its one Rule',
                      vdc.longest_rules(priv / 'practices')['listed']
                      == [('fx-private-one', 30)], ''))
        (repo / 'spec').mkdir()
        (repo / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'public'}), encoding='utf-8')
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        doc.write_text('# Run\n\nBody.\n', encoding='utf-8')
        sources = [{'name': 'precedent', 'level': 'universal', 'path': str(repo)},
                   {'name': 'fx-private', 'level': 'individual', 'path': str(priv)}]
        for _ in range(2):
            out = io.StringIO()
            listed = vdc.longest_rules_section(sources, repo, out=out)
        body = doc.read_text(encoding='utf-8')
        cases.append(('the console names every listed slug and says what the '
                      'session does with it',
                      listed == 3 and 'fx-private-one' in out.getvalue()
                      and 'never cut\n  to a quota' in out.getvalue(),
                      failure_detail(out.getvalue(), 600)))
        cases.append(('the write-up gets one ## Long Rules block, replaced on '
                      'the second write, a private set named in general terms',
                      body.count('## Long Rules') == 1
                      and '`fx-b` 300, `fx-d` 300' in body
                      and 'fx-private' not in body
                      and 'a private individual set' in body, body))
        # The account check, through the real function with its ROOT on the
        # fixture: a run from 2026-11-01 on owes the block.
        (repo / 'record').mkdir()
        (repo / 'record' / 'very-deep-check-ledger.json').write_text(json.dumps(
            {'runs': [{'date': '2026-11-01', 'run_id': 'fx', 'passes': [
                {'pass': str(n), 'status': 'done'} for n in (1, 2, 3, 4)]}]}),
            encoding='utf-8')
        whole = ('---\nopened: 2026-11-01\n---\n# Run\n\n## Checks by stage\n\n'
                 'x\n\n## Test review\n\nx\n')
        saved = pc.ROOT
        try:
            pc.ROOT = repo
            doc.write_text(whole, encoding='utf-8')
            missing = ' | '.join(str(getattr(f, 'detail', f))
                                 for f in pc._very_deep_check_write_up(None))
            doc.write_text(whole + '\n## Long Rules\n\nx\n', encoding='utf-8')
            # Only this block's finding: from 2026-11-01 the account owes
            # more than its headings (check_very_deep_check_account_shows_
            # the_work holds the rest).
            present = [f for f in pc._very_deep_check_write_up(None)
                       if 'Long Rules' in str(getattr(f, 'detail', f))]
        finally:
            pc.ROOT = saved
        cases.append(('the account check refuses a 2026-11-01 run with no '
                      '## Long Rules, and passes one with it',
                      'no `## Long Rules` section' in missing and not present,
                      missing + ' || ' + repr(present)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'very_deep_check.py\'s LONGEST RULES lists the longest quarter of '
          f'active Rules ({len(cases)} stated cases: order, controls, a set of '
          f'one, console, write-up block, account check)',
          not bad, '; '.join(f"{n}: {d[:300]}" for n, d in bad))
def check_very_deep_check_record_pass_partial_needs_what_and_who():
    """--record-pass, for a run from 2026-11-01 on, takes only done, partial
    or not run, and a partial or not-run pass carries `skipped=` (what was
    not done) and `agreed=` (the person's words). Values may hold commas.

    The 2026-10-30 run recorded all four passes `partial` with no list of
    what was skipped and no words from the person agreeing, though the Rule
    says a narrowed run is said up front and agreed. Controls: `done` needs
    neither; a partial pass with both records them in the ledger."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-partial-'))
    # The green run has to come after the pass this test records at the
    # real clock, so it is read from the clock too: a fixed stamp here
    # failed the CONTROL from 2026-11-01 10:00 on (practice:
    # fixture-owns-its-state).
    import datetime as _dt
    green = (_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=-3)))
             + _dt.timedelta(days=1)).isoformat(timespec='seconds')
    try:
        repo, ledger = _vdc_guard_repo(tmp / 'a', green=green)
        rc, err, run = _vdc_record(vdc, '2=partial,findings=3,note=two helpers',
                                   ledger, repo)
        cases.append(("THE CASE: partial with neither -- refused in its own "
                      "words, nothing written",
                      rc == 1 and not run['passes']
                      and "pass 2 is 'partial' and does not say what was "
                          "skipped and who agreed" in err
                      and "skipped='<what this pass did not do>' and "
                          "agreed='<the person's words, quoted>'" in err, err))
        rc, err, run = _vdc_record(vdc, '2=partial,skipped=questions 9, 10',
                                   ledger, repo)
        cases.append(('THE CASE: partial with what but not who -- refused',
                      rc == 1 and not run['passes'], err))
        rc, err, run = _vdc_record(vdc, "4=not run,agreed='fine'", ledger, repo)
        cases.append(('THE CASE: not run with who but not what -- refused',
                      rc == 1 and not run['passes'], err))
        rc, err, run = _vdc_record(vdc, '2=half done', ledger, repo)
        cases.append(('THE CASE: a status nobody defined -- refused',
                      rc == 1 and "must be done, partial or not run, not "
                                  "'half done'" in err, err))
        rc, err, run = _vdc_record(
            vdc, "2=partial,findings=3,skipped=questions 9, 10 and 27,"
                 "agreed=\"Morgan: skip 9, 10 and 27 today\",note=two helpers, merged",
            ledger, repo)
        p = (run['passes'] or [{}])[0]
        cases.append(('CONTROL: partial with both records them, commas and all, '
                      'and note= still runs to the end',
                      rc == 0 and p.get('skipped') == 'questions 9, 10 and 27'
                      and p.get('agreed') == 'Morgan: skip 9, 10 and 27 today'
                      and p.get('findings') == 3
                      and p.get('note') == 'two helpers, merged', repr(p)))
        rc, err, run = _vdc_record(vdc, '3=done,findings=1', ledger, repo)
        cases.append(('CONTROL: done needs neither', rc == 0, err))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'--record-pass: partial and not run carry skipped= and agreed= '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_very_deep_check_pass_one_needs_a_consumer():
    """--record-pass 1=..., for a run from 2026-11-01 on, refuses until the
    run has a consumer entry: `consumer=PATH`, a consumer repository it
    checked (one with tools/ENGINE_MANIFEST.json), or `consumer_declined=`,
    the person's words. A run inside a consumer is its own. The ledger
    records whether, never which: a consumer is often private.

    Step 6 says to ask for a real consumer before pass 1; the 2026-10-30
    run never did, and its pass 1 said "No real consumer attached"."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-consumer-'))
    green = '2026-11-01T10:00:00-03:00'
    try:
        repo, ledger = _vdc_guard_repo(tmp / 'a', green=green)
        rc, err, run = _vdc_record(vdc, '1=done', ledger, repo)
        cases.append(('THE CASE: no consumer and no words -- refused',
                      rc == 1 and not run['passes']
                      and 'pass 1 needs a real consumer repository' in err
                      and "consumer_declined='<their words, quoted>'" in err, err))
        plain = tmp / 'not-a-consumer'
        plain.mkdir()
        rc, err, run = _vdc_record(vdc, f'1=done,consumer={plain}', ledger, repo)
        cases.append(('THE CASE: consumer= names a directory that is no '
                      'consumer -- refused',
                      rc == 1 and 'is not a consumer repository' in err, err))
        cons = tmp / 'private-consumer-name'
        (cons / 'tools').mkdir(parents=True)
        (cons / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}', encoding='utf-8')
        rc, err, run = _vdc_record(vdc, f'1=done,consumer={cons}', ledger, repo)
        cases.append(('CONTROL: a real consumer records, and the ledger keeps '
                      'no path or name of it',
                      rc == 0 and run.get('consumer', {}).get('checked')
                      and 'private-consumer-name' not in ledger.read_text(), err))
        rc, err, run = _vdc_record(vdc, '1=done,findings=2', ledger, repo)
        cases.append(('CONTROL: once on record, pass 1 can be recorded again '
                      'without it', rc == 0, err))
        repo, ledger = _vdc_guard_repo(tmp / 'b', green=green)
        rc, err, run = _vdc_record(
            vdc, "1=done,consumer_declined='Morgan: no consumer today, go on'",
            ledger, repo)
        cases.append(("CONTROL: the person's words declining one record",
                      rc == 0 and run.get('consumer', {}).get('declined')
                      == 'Morgan: no consumer today, go on', err))
        repo, ledger = _vdc_guard_repo(tmp / 'c', green=green, consumer=True)
        rc, err, run = _vdc_record(vdc, '1=done', ledger, repo)
        cases.append(('CONTROL: a run inside a consumer is its own consumer',
                      rc == 0, err))
        repo, ledger = _vdc_guard_repo(tmp / 'd', green=green)
        rc, err, run = _vdc_record(vdc, '2=done', ledger, repo)
        cases.append(('CONTROL: only pass 1 asks', rc == 0, err))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'--record-pass 1 needs a consumer, or the person declining one '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))
def check_very_deep_check_account_reads_the_ledger_and_the_questions():
    """The account check, for a run from 2026-11-01 on: the quiet-sections
    answer names this run's date and answers every section the component
    ledger names as quiet and every section the run could not measure (the
    same quiet_sections() the printed read uses); `## Pass 2` lists every
    Pass 2 question the practice in force numbers, each answered, partly or
    not attempted; and record/automated_actions.md was rewritten or
    confirmed unchanged in the run.

    The 2026-10-30 run copied its quiet-sections answer from the 2026-10-17
    run, left two unmeasured sections unanswered, summarised Pass 2's
    questions as ranges with none listed one by one, and did not touch the
    schedules inventory. Control: the account that does all of it passes."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-account-ledger-'))
    try:
        repo = _vdc_account_fixture(tmp)
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        got = _vdc_account_findings(pc, repo)
        cases.append(('CONTROL: the complete account passes', got == '', got))

        def planted(old, new):
            doc.write_text(_VDC_G_ACCOUNT.replace(old, new, 1), encoding='utf-8')
            return _vdc_account_findings(pc, repo)
        got = planted('2026-11-01: QUIET ONE', '2026-10-17: QUIET ONE')
        cases.append(("THE CASE: the answer is an earlier run's",
                      "the component ledger was not read for this run -- it "
                      "does not name this run's date, 2026-11-01" in got, got))
        got = planted(' CANNOT COUNT kept: it needs GitHub.', '')
        cases.append(('THE CASE: a section the run could not measure is not '
                      'answered', 'it does not answer CANNOT COUNT' in got, got))
        got = planted(' QUIET ONE kept, a cheap guard.', '')
        cases.append(('THE CASE: a quiet section is not answered',
                      'it does not answer QUIET ONE' in got, got))
        got = planted('## Quiet sections, answered\n', '## Ledger thoughts\n')
        cases.append(('THE CASE: no answer anywhere',
                      'no `### Quiet sections, answered` heading' in got, got))
        (repo / 'spec' / 'VERY_DEEP_CHECK.md').write_text(
            '# Record\n\n### Quiet sections, answered\n\n2026-11-01: QUIET ONE '
            'kept; CANNOT COUNT kept.\n', encoding='utf-8')
        got = _vdc_account_findings(pc, repo)
        cases.append(('CONTROL: the answer may sit in the run record instead',
                      'component ledger' not in got, got))
        (repo / 'spec' / 'VERY_DEEP_CHECK.md').unlink()
        got = planted('| 2a | not attempted |\n', '')
        cases.append(('THE CASE: a Pass 2 question is missing',
                      'Pass 2 does not list every question -- missing 2a' in got
                      and 'missing 2a, ' not in got, got))
        got = planted('| 2 | partly: half of it |', '| 2 | looked at it |')
        cases.append(('THE CASE: a question with no answer word counts as '
                      'missing', 'missing 2.' in got, got))
        doc.write_text(_VDC_G_ACCOUNT, encoding='utf-8')
        sched = repo / 'record' / 'automated_actions.md'
        sched.write_text('# Schedules\n\nConfirmed unchanged on 2026-10-30.\n',
                         encoding='utf-8')
        got = _vdc_account_findings(pc, repo)
        cases.append(('THE CASE: the schedules inventory was confirmed in an '
                      'earlier run only',
                      'record/automated_actions.md was not rewritten or '
                      'confirmed in this run' in got, got))
        sched.unlink()
        got = _vdc_account_findings(pc, repo)
        cases.append(('THE CASE: no schedules inventory at all',
                      'record/automated_actions.md was not written in this '
                      'run' in got, got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check account answers the component ledger, every '
          f'Pass 2 question and the schedules ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_very_deep_check_account_blocks_postdate_the_last_fix():
    """Every block the run writes into its account is stamped with when it
    was measured, `--refresh-blocks` rewrites them all without a ledger row,
    and the account check, for a run from 2026-11-01 on, refuses a warnings,
    checks-by-stage, set-independence or test-review block stamped before
    the run's last commit to tools/ or practices/ (by author date, between
    the run's start and its last recorded pass). The ledger keeps what the
    account is held to: the incidents a run listed, the tests it left.

    The 2026-10-30 run's account showed blocks that still reported bugs
    fixed hours earlier. Controls: a block measured after the last fix
    passes, and a commit after the last pass is not the run's."""
    import contextlib, io, shutil, subprocess as sp, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    import very_deep_check as vdc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-account-blocks-'))
    try:
        repo = _vdc_account_fixture(tmp)
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'

        def git(*a, date=None):
            env = dict(os.environ, GIT_AUTHOR_NAME='fx', GIT_AUTHOR_EMAIL='fx@x',
                       GIT_COMMITTER_NAME='fx', GIT_COMMITTER_EMAIL='fx@x')
            if date:
                env['GIT_AUTHOR_DATE'] = date
            return sp.run(['git', '-c', 'core.hooksPath=/dev/null',
                           '-c', 'commit.gpgsign=false', *a], cwd=str(repo),
                          env=env, capture_output=True, text=True)
        git('init', '-q')
        git('add', '-A')
        git('commit', '-qm', 'start', date='2026-11-01T08:00:00-03:00')
        (repo / 'tools' / 'fix.py').write_text('x = 1\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-qm', 'a fix', date='2026-11-01T12:00:00-03:00')

        def stamped(stamp):
            body = _VDC_G_ACCOUNT.replace(
                '<!--vdc-embed:test-review: never hand-edit -->\n',
                '<!--vdc-embed:test-review: never hand-edit -->\n'
                + (f'<!--vdc-measured: {stamp} -->\n' if stamp else ''))
            doc.write_text(body, encoding='utf-8')
            return _vdc_account_findings(pc, repo)
        got = stamped('2026-11-01T11:00:00-03:00')
        cases.append(('THE CASE: a block measured before the last fix',
                      "the account's generated blocks predate the run's last "
                      "fix (2026-11-01T12:00:00-03:00): test-review "
                      "(2026-11-01T11:00:00-03:00)" in got
                      and '--refresh-blocks' in got, got))
        got = stamped(None)
        cases.append(('THE CASE: a block with no stamp',
                      'test-review (no stamp)' in got, got))
        got = stamped('2026-11-01T12:30:00-03:00')
        cases.append(('CONTROL: a block measured after the last fix passes',
                      got == '', got))
        (repo / 'tools' / 'later.py').write_text('y = 1\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-qm', 'later', date='2026-11-02T10:00:00-03:00')
        got = stamped('2026-11-01T12:30:00-03:00')
        cases.append(("CONTROL: a commit after the run's last pass is not the "
                      "run's fix", got == '', got))
        # The tool stamps what it writes.
        (repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md').write_text(
            '# Run\n', encoding='utf-8')
        vdc._write_run_block(repo, vdc.STAGES_EMBED, 'Checks by stage',
                             'CHECKS BY STAGE', 'body')
        text = (repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md').read_text(
            encoding='utf-8')
        cases.append(('the tool stamps every block it writes',
                      re.search(r'<!--vdc-embed:checks-by-stage[^>]*-->\n'
                                r'<!--vdc-measured: \d{4}-\d{2}-\d{2}T[^ ]+ -->'
                                r'\nbody', text) is not None, text))
        src = (ROOT / 'tools' / 'very_deep_check.py').read_text(encoding='utf-8')
        cases.append(('--refresh-blocks rewrites the four blocks the check '
                      'reads, and adds no ledger row',
                      "if '--refresh-blocks' in args:" in src
                      and all(f in src.split("if '--refresh-blocks' in args:")[1]
                              .split('return 0')[0]
                              for f in ('warnings_section(', 'checks_by_stage_section(',
                                        'set_independence_section(',
                                        'test_worth_section(')), ''))
        led = vdc.RunLedger(path=tmp / 'ledger.json', repo=tmp)
        with contextlib.redirect_stdout(io.StringIO()):
            led.start('INCIDENT COVERAGE', kind='read')
            led.end(findings=0, extra={'listed': ['gotcha-a']})
        cases.append(('the ledger row keeps what the account is held to',
                      led.components[-1].get('listed') == ['gotcha-a'], ''))
        cases.append(('the full run records the incidents listed and the tests '
                      'left to judge',
                      "extra={'listed': [r[1] for r in _ic_rows]}" in src
                      and "extra={'to_judge': _tw_by_repo}" in src, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check account\'s blocks postdate the run\'s last fix '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_orphan_scan_reads_who_claims_a_script():
    """The very deep check's ORPHANS section names a check script whose
    practice is gone. It went by filename alone, so a script named for an
    older slug read as an orphan while its practice's `checked_by` named it
    and the same run executed it (very deep check, 2026-10-05). A script is
    owned when a practice's `checked_by` or its own `# practice:` line names
    a practice that exists; only a script nothing claims is reported."""
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as _vdc
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-orphan-'))
    cases = []
    try:
        (fx / 'practices').mkdir()
        (fx / 'tools' / 'checks').mkdir(parents=True)
        (fx / 'practices' / 'new-name.md').write_text(
            '---\nslug: new-name\nchecked_by: tools/checks/check_by_field.py\n---\n',
            encoding='utf-8')
        checks = fx / 'tools' / 'checks'
        (checks / 'check_by_field.py').write_text('print(1)\n', encoding='utf-8')
        (checks / 'check_by_header.py').write_text(
            '# practice: new-name\nprint(1)\n', encoding='utf-8')
        (checks / 'check_header_names_a_ghost.py').write_text(
            '# practice: gone-name\nprint(1)\n', encoding='utf-8')
        (checks / 'check_nobody.py').write_text('print(1)\n', encoding='utf-8')
        out = ' '.join(_vdc._orphan_scan(fx))
        cases.append(('a script a practice\'s checked_by names is not an orphan',
                      'check_by_field.py' not in out))
        cases.append(('a script whose own header names an existing practice is '
                      'not an orphan', 'check_by_header.py' not in out))
        cases.append(('a header naming a practice that does not exist is still '
                      'an orphan', 'check_header_names_a_ghost.py' in out))
        cases.append(('a script nothing claims is an orphan',
                      'check_nobody.py' in out))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'the orphan scan reads who claims a check script '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_generated_files_candidates_are_repo_rooted_claims():
    """The very deep check's GENERATED FILES section asks the session to
    judge tracked files a tool may write that tools/generated_files.json
    does not list. It matched a basename written under ANY directory and
    the bare word "generated", so six hand-kept files came back every run
    (very deep check, 2026-10-05, pass 2). It now counts a write only at the
    file's full path in this repo, a heading only when it claims to be
    generated, and honours the registry's not_generated verdicts."""
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as _vdc
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-genfiles-'))
    cases = []
    try:
        def put(rel, text):
            (fx / rel).parent.mkdir(parents=True, exist_ok=True)
            (fx / rel).write_text(text, encoding='utf-8')
        put('tools/writer.py',
            "def seed(dest):\n"
            "    (dest / 'out' / 'budgets.json').write_text('{}')\n"
            "def fixture(out):\n"
            "    (out / 'settings.json').write_text('{}')\n"
            "def mine(ROOT):\n"
            "    (ROOT / 'out' / 'built.json').write_text('{}')\n"
            "def judged(ROOT):\n"
            "    (ROOT / 'kept.json').write_text('{}')\n")
        put('out/budgets.json', '{}\n')
        put('settings.json', '{}\n')
        put('out/built.json', '{}\n')
        put('kept.json', '{}\n')
        put('docs/slide.md', '# Method\n\nOffice formats are generated outputs.\n')
        put('docs/view.md', '# A view\n\nGenerated by tools/x.py -- do not hand-edit.\n')
        put('tools/generated_files.json', json.dumps({
            'files': [],
            'not_generated': [
                {'path': 'kept.json', 'reason': 'hand-kept; a key is set in place'},
                {'path': 'gone.json', 'reason': 'was hand-kept'}]}))
        subprocess.run(['git', 'init', '-q', str(fx)], check=True)
        subprocess.run(['git', '-C', str(fx), 'add', '-A'], check=True)
        got = dict(_vdc.unlisted_generated_candidates(fx))
        cases.append(('a same-named file a tool writes under another '
                      'directory is not a candidate',
                      'out/budgets.json' not in got and 'settings.json' not in got))
        cases.append(('a write at the full path in this repo is',
                      'out/built.json' in got))
        cases.append(('the bare word "generated" is not a claim',
                      'docs/slide.md' not in got))
        cases.append(('"generated by ... do not hand-edit" is',
                      'docs/view.md' in got))
        cases.append(('a not_generated verdict is honoured',
                      'kept.json' not in got))
        cases.append(('a not_generated entry for a file that is gone comes back',
                      'gone.json' in got))
        reg = json.loads((ROOT / 'tools' / 'generated_files.json').read_text(encoding='utf-8'))
        seeded = {e.get('path'): e.get('reason') for e in reg.get('not_generated') or []}
        cases.append(('this repo records the six judged hand-kept files, each with a reason',
                      all(seeded.get(p) for p in (
                          '.claude/settings.json', 'precedent.json',
                          'tools/routing_scope.json', 'tools/session_load_budgets.json',
                          'deck/sample/slides/04_working_method.md',
                          'spec/GENERATED_FILES_PLAN.md'))))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'GENERATED FILES asks only about repo-rooted writes and real '
          f'claims, and honours not_generated ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_incident_coverage_reads_what_the_gotcha_names():
    """The very deep check's INCIDENT COVERAGE searched tools/ and
    practices/ for each gotcha's slug, and nothing else. Most gotchas name
    their own planted case in their Fix and no tool names the gotcha back,
    so they read as cited by nothing (very deep check, 2026-10-05, pass 2:
    nine of twelve). It now reads the check_ names a Fix gives and confirms
    each is a planted case, reports one that does not exist, credits a case
    that exercises a mechanism the Fix names, and counts a written
    "Prevention: nothing mechanical, deliberately, because ..." as an
    answer."""
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as _vdc
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-incidents-'))
    cases = []
    try:
        (fx / 'tools' / 'checks').mkdir(parents=True)
        (fx / 'gotchas').mkdir()
        (fx / 'tools' / 'verify_harness.py').write_text(
            'def check_real_case():\n    pass\n\n'
            'def check_other_case():\n    engine_is_newer(1)\n', encoding='utf-8')
        (fx / 'tools' / 'checks' / 'check_some_script.py').write_text('', encoding='utf-8')

        def gotcha(slug, fix, story=''):
            (fx / 'gotchas' / f'{slug}.md').write_text(
                f'---\nslug: {slug}\nstatus: live\nnoted: 2026-10-01\n---\n'
                f'## Symptom\n\nx\n\n## Story\n\n{story or "x"}\n\n## Fix\n\n{fix}\n',
                encoding='utf-8')
        gotcha('gotcha-a-named', 'Planted case `check_real_case`.')
        gotcha('gotcha-b-missing', 'Planted case `check_gone_case`.')
        gotcha('gotcha-c-script', 'Refused by `check_some_script`.')
        gotcha('gotcha-d-written', 'By hand.\n\n**Prevention: nothing mechanical, '
                                   'deliberately**, because the\nfix is a '
                                   'person\'s setting.')
        gotcha('gotcha-e-mechanism', 'The refresh asks `engine_is_newer` now.')
        gotcha('gotcha-f-story-only', 'By hand.', story='Written `*check_foo()`.')
        gotcha('gotcha-g-nothing', 'By hand.')
        _s, rows, note = _vdc._incident_coverage(fx, since='2026-09-01')
        got = {r[1]: (r[4] if len(r) > 4 else {}) for r in rows}
        cases.append(('every gotcha filed since is a row', not note and len(got) == 7))
        cases.append(('a check_ name the Fix gives is a planted case',
                      got.get('gotcha-a-named', {}).get('cases') == ['check_real_case']))
        cases.append(('a check_ name nothing defines is a finding',
                      got.get('gotcha-b-missing', {}).get('missing') == ['check_gone_case']))
        cases.append(('a check script under tools/checks/ is named as one',
                      got.get('gotcha-c-script', {}).get('scripts') == ['check_some_script']))
        cases.append(('a written Prevention: answer is read',
                      (got.get('gotcha-d-written', {}).get('written') or '')
                      .startswith('nothing mechanical, deliberately')))
        cases.append(('a case exercising a mechanism the Fix names is credited',
                      got.get('gotcha-e-mechanism', {}).get('exercised')
                      == [('check_other_case', 'engine_is_newer')]))
        cases.append(('code quoted in a Story names no case',
                      not got.get('gotcha-f-story-only', {}).get('missing')))
        g = got.get('gotcha-g-nothing', {})
        cases.append(('a gotcha with none of these has nothing to show',
                      bool(g) and not any(g.values())))
        # The two real gotchas, read on their own: a scratch tree holding just
        # their files, never this whole repository, which was half this
        # check's time for two rows.
        named = ('gotcha-2026-09-30-auto-mode-refuses-a-bare-'
                 'promote-into-main-as-a-production',
                 'gotcha-2026-09-28-stale-shallow-entries-for-'
                 'deleted-branches-survive-unshallow')
        two = fx / 'two-real'
        (two / 'gotchas').mkdir(parents=True)
        (two / 'tools').mkdir()
        (two / 'tools' / 'verify_harness.py').write_text('', encoding='utf-8')
        for s in named:
            if (ROOT / 'gotchas' / f'{s}.md').is_file():
                _sh.copy2(ROOT / 'gotchas' / f'{s}.md', two / 'gotchas' / f'{s}.md')
        real = {r[1]: (r[4] if len(r) > 4 else {})
                for r in _vdc._incident_coverage(two, since='2026-09-28')[1]}
        cases.append(('the two gotchas with no mechanical prevention say so, '
                      'and why', all(
                          (real.get(s) or {}).get('written', '') or ''
                          for s in named)))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'INCIDENT COVERAGE reads the planted case and the Prevention answer '
          f'a gotcha gives ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_fix_sweep_judges_in_force_by_the_targets_resolver():
    """FIX SWEEP decides whether a new detector's practice is in force in a
    repository by that repository's own resolver, not by a practices/<slug>.md
    in its copy (2026-10-17 very deep check: in each set 17 of 18 rows read
    SKIPPED, "not in force here", though every set declares universal).

    Stated cases: a practice the set's resolver puts in force from universal
    is run against the set's copy, not skipped; the real set is left as it
    was; one cause behind most skips is said once, ONE CAUSE, the way CHECK
    COVERAGE says it, and a spread of causes is not."""
    import shutil, tempfile
    import very_deep_check as _vdc
    import precedent_vendor_engine as pve
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-fix-sweep-'))
    try:
        s = tmp / 'zz-set'
        (s / 'practices').mkdir(parents=True)
        (s / 'tools').mkdir()
        for name in pve.ENGINE_FILES:
            src = ROOT / 'tools' / name
            if src.is_file() and name != 'verify_harness.py':
                shutil.copy2(src, s / 'tools' / name)
        (s / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'source', 'files': []}), encoding='utf-8')
        (s / 'precedent-source.json').write_text(
            json.dumps({'name': 'zz-set', 'level': 'shared'}), encoding='utf-8')
        (s / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'base_branch': 'main', 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}),
            encoding='utf-8')
        (s / 'practices' / 'zz-own.md').write_text(
            '---\nslug: zz-own\ntitle: Fixture\ntier: on-demand\nseverity: default\n'
            'applies_to: ["**"]\noccasion: "x"\nindex_clause: "x"\nstatus: active\n'
            '---\n## Rule\nx\n\n## Story\nx\n', encoding='utf-8')
        for a in (['init', '-q', '-b', 'main'], ['add', '-A'],
                  ['-c', 'user.email=h@example.com', '-c', 'user.name=h',
                   'commit', '-qm', 'fixture']):
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(s), *a],
                           capture_output=True)
        saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'none.json')
        # The sweep as the run calls it, with its detector list planted.
        real_added = _vdc._detectors_added
        _vdc._detectors_added = lambda *_a, **_k: (['one-python'], '', '')
        try:
            _since, _slugs, rows, _note, _cav = _vdc._fix_sweep(
                ROOT, [('zz-set', str(s))], since='2026-01-01')
        finally:
            _vdc._detectors_added = real_added
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved
        label, verdicts, why = rows[0] if rows else ('zz-set', None, 'no row')
        got = verdicts[0] if verdicts else (None, None, why)
        cases.append(('a practice the set resolves from universal is run on the '
                      'copy, not skipped', got[1] not in (None, 'SKIPPED')
                      and 'in force here by its resolver' in (got[2] or ''),
                      repr(got)))
        status = subprocess.run(['git', '-C', str(s), 'status', '--porcelain',
                                 '--untracked-files=all'],
                                capture_output=True, text=True).stdout
        cases.append(('the real set is left as it was', status.strip() == ''
                      and not (s / 'process').exists(), status))
        _one_cause = getattr(_vdc, '_one_skip_cause', lambda v: '')
        one = _one_cause([('a', 'SKIPPED', 'no file'),
                                    ('b', 'SKIPPED', 'no file'),
                                    ('c', 'clean', '')])
        spread = _one_cause([('a', 'SKIPPED', 'x'), ('b', 'SKIPPED', 'y'),
                                       ('c', 'clean', '')])
        cases.append(('one cause behind most skips is said once, ONE CAUSE; a '
                      'spread of causes is not', one.startswith('ONE CAUSE 2 of 3')
                      and spread == '', repr((one, spread))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the fix sweep judges a detector in force by the target repository\'s '
          f'resolver ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:600]}' for n, d in bad))


def check_fix_sweep_copy_keeps_its_neighbours():
    """The very deep check's fix sweep runs each new detector against a COPY
    of every repo in force. A check that looks beside the repo for a source
    cloned there (the ladder set an individual set brings) found nothing
    beside a bare temporary copy, so the ladder-words check reported the
    individual set in violation of a rule it is exempt from (very deep
    check, 2026-10-05). The copy now sits beside links to the real repo's
    siblings, and cleaning it up must never reach through those links."""
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as _vdc
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-sweep-'))
    cases = []
    try:
        (fx / 'me').mkdir()
        (fx / 'neighbour').mkdir()
        (fx / 'neighbour' / 'keep.txt').write_text('x', encoding='utf-8')
        (fx / 'a-file').write_text('x', encoding='utf-8')
        scratch = fx / 'scratch'
        scratch.mkdir()
        _vdc._link_siblings(fx / 'me', scratch)
        link = scratch / 'neighbour'
        cases.append(('a sibling directory is linked beside the copy',
                      link.is_symlink() and (link / 'keep.txt').is_file()))
        cases.append(('the repo itself is not linked -- the copy takes its place',
                      not (scratch / 'me').exists()))
        cases.append(('a plain file beside the repo is not linked',
                      not (scratch / 'a-file').exists()))
        _sh.rmtree(scratch, ignore_errors=True)
        cases.append(('cleaning up the copy leaves the real sibling untouched',
                      (fx / 'neighbour' / 'keep.txt').is_file()))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'the fix sweep\'s copy of a repo sees that repo\'s neighbours '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_instruction_files_name_repos_that_exist():
    """A repository named in an always-loaded instructions file is asked
    about, and the pattern that finds those names does not find noise.

    2026-09-21: an Update Vendors pass found a consuming repo's AGENTS.md
    naming a private voice-definition repository under its old name, twice
    -- the session-start step and a tool's description -- after the real
    one had been renamed, in the file whose own step 1 warns about a source
    name going stale silently. `repo-reference-allowlist` asks whether a name may be
    MENTIONED; `repos_in_force_audit` asks whether a SOURCE exists. A name
    in prose is neither, so it was checked for permission and never for
    existence.

    THE NOISE CONTROL IS THE LOAD-BEARING CASE. An unanchored owner/name
    pattern matches `practices/park-it.md` and `tools/doc_lint.py` on
    nearly every line of an instructions file, and a probe that reports
    fifty phantom repositories is one nobody runs twice. Anchoring on
    owners seen in real remotes is what makes it usable, so both halves are
    asserted (practice: control-asserts-which-failure).
    """
    import very_deep_check as vdc
    import tempfile

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-refs-'))
    try:
        repo = tmp / 'repo'
        repo.mkdir()
        (repo / 'AGENTS.md').write_text(
            '# Instructions\n\n'
            'Clone realowner/RealRepo at session start.\n'
            'See practices/park-it.md and tools/doc_lint.py for the rest.\n'
            'Upstream is https://github.com/otherowner/Upstream for now.\n'
            'Look in spec/PLAN.md, todo/TODO.md and documentation/X.md too.\n',
            encoding='utf-8')
        rows = [('fixture', 'https://github.com/realowner/Anchor', str(repo))]

        cases.append(('the owner is learned from a real remote',
                      vdc._known_owners(rows) == {'realowner'},
                      str(vdc._known_owners(rows))))

        refs = vdc._repo_refs_in_instruction_files(rows)
        keys = set(refs)
        cases.append(('a bare owner/name with a KNOWN owner is found',
                      ('realowner', 'RealRepo') in keys, str(sorted(keys))))
        cases.append(('a full github.com URL is found even for an unknown owner',
                      ('otherowner', 'Upstream') in keys, str(sorted(keys))))
        noise = {k for k in keys
                 if k[0] in ('practices', 'tools', 'spec', 'todo',
                             'documentation')}
        cases.append(('a repo-relative path is NOT read as a repository '
                      '(the case that decides whether this is usable)',
                      not noise, f'noise: {sorted(noise)}'))
        cases.append(('it records WHERE each name was seen, so a fix can '
                      'reach every occurrence',
                      refs.get(('realowner', 'RealRepo')) == ['fixture:AGENTS.md'],
                      str(refs.get(('realowner', 'RealRepo')))))

        # No known owners at all -- the bare pattern must not be built from
        # an empty alternation, which would match everything or explode.
        norows = [('fixture', 'https://example.invalid/x/y.git', str(repo))]
        bare_only = vdc._repo_refs_in_instruction_files(norows)
        cases.append(('with no known owner, only full URLs are found and '
                      'nothing crashes',
                      set(bare_only) == {('otherowner', 'Upstream')},
                      str(sorted(bare_only))))

        # A file that is not there is skipped, not fatal.
        (repo / 'AGENTS.md').unlink()
        cases.append(('an absent instructions file is skipped, not an error',
                      vdc._repo_refs_in_instruction_files(rows) == {},
                      str(vdc._repo_refs_in_instruction_files(rows))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_very_deep_check_finds_a_second_list_of_practices():
    """very_deep_check.py's SECOND LISTS OF PRACTICES helper, planted both
    ways: a hand-kept JSON naming every practice is a candidate; the same
    list in MAP.md (a generated view) and a file naming only a few are not.
    Checked against the real case too: tools/routing_scope.json as it stood
    before 2026-09-29 is the file this exists to catch.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-second-list-'))
    try:
        slugs = [f'rule-{i}' for i in range(10)]
        (d / 'practices').mkdir()
        for s in slugs:
            (d / 'practices' / f'{s}.md').write_text(
                f'---\nslug:        {s}\nstatus:      active\n---\n## Rule\nDo.\n',
                encoding='utf-8')
        listing = json.dumps({s: {'why': 'kept by hand'} for s in slugs})
        (d / 'routing.json').write_text(listing, encoding='utf-8')
        (d / 'MAP.md').write_text('\n'.join(slugs), encoding='utf-8')
        (d / 'NOTES.md').write_text(' '.join(slugs[:3]), encoding='utf-8')
        # Every practice cited, one per test, far apart: a big test file,
        # not a list (2026-10-31: tools/verify_harness.py was a candidate on
        # every run for exactly this shape).
        filler = 'x = 1\n' * (getattr(vdc, 'WINDOW_LINES_PER_SLUG', 10) * len(slugs))
        (d / 'tests.py').write_text(''.join(
            f'# (practice: {s})\n{filler}' for s in slugs), encoding='utf-8')
        subprocess.run(['git', '-C', str(d), 'init', '-q'], capture_output=True)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], capture_output=True)
        found = [rel for rel, _n, _t in vdc._second_practice_lists(d)]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    check('the very deep check names a hand-kept list of every practice, and '
          'not a generated view, a file naming a few, or a file citing each '
          'one far apart',
          found == ['routing.json'], repr(found))

    # The real case, where history holds it: routing_scope.json as it stood
    # before dcaa1c94 retired it, against practice files for its own keys.
    real = subprocess.run(['git', '-C', str(ROOT), 'show',
                           'dcaa1c94^:tools/routing_scope.json'],
                          capture_output=True, text=True)
    if real.returncode != 0:
        not_applicable('the very deep check names the real routing_scope.json',
                 'dcaa1c94 is not in this clone (a shallow checkout)')
        return
    d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-second-list-real-'))
    try:
        (d / 'practices').mkdir()
        for s in json.loads(real.stdout)['practices']:
            (d / 'practices' / f'{s}.md').write_text(
                f'---\nslug:        {s}\nstatus:      active\n---\n## Rule\nDo.\n',
                encoding='utf-8')
        (d / 'tools').mkdir()
        (d / 'tools' / 'routing_scope.json').write_text(real.stdout,
                                                        encoding='utf-8')
        subprocess.run(['git', '-C', str(d), 'init', '-q'], capture_output=True)
        subprocess.run(['git', '-C', str(d), 'add', '-A'], capture_output=True)
        found = [rel for rel, _n, _t in vdc._second_practice_lists(d)]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    check('the very deep check names the real routing_scope.json',
          found == ['tools/routing_scope.json'], repr(found))


def check_very_deep_check_finds_vendored_surplus():
    """very_deep_check.py's VENDORED SURPLUS helpers, planted both ways.
    Upstream: a file nothing else that ships names is UNNAMED, and one named
    by another shipped file, by import, or through its folder is not.
    Downstream: a consumer whose copy holds gotchas/ and a byte-identical
    second copy of its own tools/ file is reported for both; the same
    consumer after the copy is trimmed is quiet. The real case is
    2026-09-30's: a consumer's process/upstream/ held 543 files, the
    engine among them twice, and the section before this one checked only
    the checkout the run started in."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    cases = []
    d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-surplus-'))
    try:
        up = d / 'up'
        for rel, text in {
                'tools/used.py': 'import helper\n',
                'tools/helper.py': 'X = 1\n',
                'tools/orphan.py': 'print("nobody runs me")\n',
                'templates/kit/deep/a.txt': 'a\n',
                'INSTALL.md': 'copy templates/kit/deep/ and run used.py\n',
                }.items():
            (up / rel).parent.mkdir(parents=True, exist_ok=True)
            (up / rel).write_text(text, encoding='utf-8')
        shipped = {rel: (rel, 'engine') for rel in
                   ('tools/used.py', 'tools/helper.py', 'tools/orphan.py',
                    'templates/kit/deep/a.txt', 'INSTALL.md')}
        unnamed = vdc._named_anywhere_else(shipped, up)
        cases.append(('only the file nothing names is UNNAMED',
                      unnamed == ['tools/orphan.py'], unnamed))

        body = 'def main():\n    return 0\n' * 20
        c = d / 'consumer'
        for rel, text in {
                'tools/checkin.py': body,
                'tools/ENGINE_MANIFEST.json': '{"kind": "consumer"}\n',
                'process/upstream/tools/checkin.py': body,
                'process/upstream/spec/PLAN.md': 'a plan\n',
                'process/upstream/practices/p.md': 'a rule\n',
                }.items():
            (c / rel).parent.mkdir(parents=True, exist_ok=True)
            (c / rel).write_text(text, encoding='utf-8')
        subprocess.run(['git', '-C', str(c), 'init', '-q'], capture_output=True)
        subprocess.run(['git', '-C', str(c), 'add', '-A'], capture_output=True)
        found = vdc._consumer_surplus(c)
        cases.append(('a consumer holding spec/ and a second tools/ copy '
                      'is reported for both',
                      len(found) == 2 and 'spec/ 1' in found[0]
                      and 'tools/ 1' in found[0]
                      and 'held twice' in found[1], found))
        subprocess.run(['git', '-C', str(c), 'rm', '-q', '-r', '-f',
                        'process/upstream/tools', 'process/upstream/spec'],
                       capture_output=True)
        found = vdc._consumer_surplus(c)
        cases.append(('the trimmed consumer is quiet', found == [], found))
        cases.append(('the consumer is found beside the checkout',
                      any(p.name == 'consumer' for _n, p in
                          vdc._consumers_in_session(up)), ''))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('the very deep check names what a consumer receives that it has no '
          'use for, or holds twice',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_set_independence_holds_only_what_a_waiting_part_names():
    """The very deep check's SET INDEPENDENCE holds back only the tools/
    files a part of the plan still headed "Waiting" names (2026-10-19,
    piece 6: part 3 was built, and its files are held no more). Made-up
    plan text."""
    import tempfile
    import very_deep_check as vdc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'spec').mkdir()
        plan = root / vdc._SETS_PLAN
        plan.write_text('# Plan\n\n## 1. Built: one\n\n`tools/zz_built.py`\n\n'
                        '## 2. Waiting on someone: two\n\n`tools/zz_held.py` and '
                        '[x](../tools/zz_also.py)\n\n## 3. Built: three\n\n'
                        '`tools/zz_done.py`\n', encoding='utf-8')
        got = vdc._waiting_files(root)
        cases.append(('only a Waiting part\'s files are held',
                      got == {'zz_held.py', 'zz_also.py'}, repr(got)))
        plan.write_text(plan.read_text().replace('## 2. Waiting on someone',
                                                 '## 2. Built'), encoding='utf-8')
        got = vdc._waiting_files(root)
        cases.append(('once that part is built, nothing is held', got == set(), repr(got)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'set independence holds only what a Waiting part names '
          f'({len(cases)} stated cases)', not bad, '; '.join(f'{n} -- {d}' for n, d in bad))


def check_visibility_audit_skips_only_fixture_names():
    """The visibility audit does not spend an API call on a name only a test
    mentions, under an owner nothing else names -- and still asks about a
    real owner a fixture happens to name (2026-10-30 very deep check: 187
    GitHub calls against a declared 150, 110 of 149 names fixture-only).

    Control: a name in a test whose owner is named in a document is kept."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as v
    refs = {('zz-made-up', 'a'): ['tools/verify_harness.py'],
            ('zz-made-up', 'b'): ['tools/checks/tests/test_x.sh'],
            ('realacct', 'in-test'): ['tools/verify_harness.py'],
            ('realacct', 'documented'): ['README.md'],
            ('mixed', 'both'): ['tools/verify_harness.py', 'INSTALL.md']}
    keep, skipped = v._drop_fixture_only_refs(refs)
    cases = [('a made-up owner named only in tests is skipped, and listed',
              skipped == ['zz-made-up/a', 'zz-made-up/b'], skipped),
             ('control: a real owner named in a document is still asked about '
              'where only a test names the repository',
              ('realacct', 'in-test') in keep, sorted(keep)),
             ('a name a document also mentions is asked about',
              ('mixed', 'both') in keep and ('realacct', 'documented') in keep,
              sorted(keep))]
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'the visibility audit skips only fixture-only names ({len(cases)} stated '
          f'cases)', not bad, '; '.join(bad))


def check_ci_fleet_audit_skips_deleted_sets():
    """The fleet audit never asks GitHub about a deleted practice set
    (practice: ci-workflow-approved).

    WHY. discover() takes every clone beside this checkout, and a session
    that attached a set before it was deleted still has the clone. On
    2026-10-11 the audit asked about two deleted sets, got the proxy's
    refusal for every question, listed both as NOT REACHED, and ran over
    its declared API budget."""
    import tempfile
    import ci_fleet_audit as cfa
    import precedent_resolve as pr

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for name in ('BestPractice', 'live-set', 'gone-set'):
            d = tmp / name
            d.mkdir()
            fixture_git(d, 'init', '-q')
            fixture_git(d, 'remote', 'add', 'origin',
                        f'https://github.com/acme/{name}.git')
        real = pr.deleted_sets
        pr.deleted_sets = lambda *a, **k: {'gone-set': {}}
        try:
            found = cfa.discover(tmp / 'BestPractice')
        finally:
            pr.deleted_sets = real
    cases = [
        ('a live clone beside the checkout is audited',
         'acme/live-set' in found),
        ('a deleted set\'s clone is not', 'acme/gone-set' not in found),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'the fleet audit skips deleted sets ({len(cases)} stated cases)',
          not failed, '; '.join(failed) + f' -- found {found}')


def check_ci_fleet_audit_reads_github_not_the_clone():
    """practice: ci-workflow-approved, 2026-09-26. The push-time check sees
    only a session's own pushes; tools/ci_fleet_audit.py asks GitHub, so it
    sees a workflow edited on the website, one left on a side branch, and a
    repository it cannot reach. Planted against a fake GitHub, so the
    verdicts are a property of the code, not of the network."""
    import base64, datetime, hashlib, io
    import ci_fleet_audit as cfa

    def b64(t):
        return base64.b64encode(t.encode()).decode()

    approved = 'name: ok\non:\n  pull_request:\n    branches: [main]\n'
    rogue = 'name: rogue\non:\n  push:\n    branches: [main]\n'
    side = 'name: side\non:\n  push:\n'
    quiet = 'name: quiet\non:\n  pull_request:\n'
    cron = ('name: nightly\non:\n  schedule:\n    - cron: "15 3 * * *"\n')
    sha = hashlib.sha256(approved.encode()).hexdigest()
    cfg = {'github_ci_approved': {'.github/workflows/ok.yml': {
        'sha256': sha, 'approved_by': 'Morgan, 2026-09-26: "yes, that one"'}}}
    blobs = {'b-ok': approved, 'b-rogue': rogue, 'b-side': side,
             'b-quiet': quiet, 'b-cron': cron}

    def listing(names):
        return [{'name': n, 'type': 'file', 'sha': b} for n, b in names]

    def fake(path):
        o = 'repos/o/r'
        routes = {
            f'{o}': {'default_branch': 'main', 'private': True},
            f'{o}/actions/workflows?per_page=100': {'workflows': []},
            f'{o}/contents/precedent.json?ref=main':
                {'content': b64(json.dumps(cfg))},
            f'{o}/branches?per_page=100':
                [{'name': 'main'}, {'name': 'stale'}, {'name': 'calm'},
                 {'name': 'old'}],
            # 'stale' and 'calm' had commits this week; 'old' has had none
            # for a month, so it must not be read at all.
            f'{o}/branches/stale': {'commit': {'commit': {'committer':
                {'date': '2026-09-24T10:00:00Z'}}}},
            f'{o}/branches/calm': {'commit': {'commit': {'committer':
                {'date': '2026-09-25T10:00:00Z'}}}},
            f'{o}/branches/old': {'commit': {'commit': {'committer':
                {'date': '2026-08-20T10:00:00Z'}}}},
            f'{o}/contents/.github/workflows?ref=old': listing(
                [('side.yml', 'b-side'), ('ghost.yml', 'b-side')]),
            f'{o}/contents/.github/workflows?ref=main': listing(
                [('ok.yml', 'b-ok'), ('rogue.yml', 'b-rogue'),
                 ('nightly.yml', 'b-cron')]),
            f'{o}/contents/.github/workflows?ref=stale': listing(
                [('ok.yml', 'b-ok'), ('side.yml', 'b-side')]),
            f'{o}/contents/.github/workflows?ref=calm': listing(
                [('ok.yml', 'b-ok'), ('quiet.yml', 'b-quiet')]),
        }
        if path.startswith(f'{o}/actions/runs'):
            return {'total_count': 2, 'workflow_runs': [
                {'path': '.github/workflows/rogue.yml', 'event': 'push',
                 'created_at': '2026-09-25T10:00:00Z'},
                {'path': '.github/workflows/gone.yml', 'event': 'push',
                 'created_at': '2026-09-24T10:00:00Z'}]}, None
        if path.startswith(f'{o}/git/blobs/'):
            return {'content': b64(blobs[path.rsplit('/', 1)[1]])}, None
        if path in routes:
            return routes[path], None
        if path.startswith('repos/o/unreached'):
            return {'message': 'GitHub access to this repository is not '
                               'enabled for this session.'}, None
        return {'message': 'Not Found'}, None

    today = datetime.date(2026, 9, 26)
    r = cfa.audit_repo('o/r', call=fake, today=today)
    u = cfa.audit_repo('o/unreached', call=fake, today=today)
    rows = '\n'.join(f'{v} {t}' for v, t in r['rows'])
    buf = io.StringIO()
    n = cfa.render([r, u], out=buf)
    out = buf.getvalue()
    cases = [
        ('CONTROL: a workflow approved at this exact content is OK',
         any(
             v == 'OK' and 'ok.yml [main]' in t for v, t in r['rows'])),
        ('a workflow nobody approved (say, edited on the website) is a '
         'FINDING that names its push-on-main cost',
         any(v == 'FINDING' and 'rogue.yml [main]' in t
             and 'APPROVED BY NOBODY' in t and 'every merge bills a run' in t
             for v, t in r['rows'])),
        ('a side branch whose workflow runs on its own push is a FINDING',
         any(v == 'FINDING' and 'side.yml on branch stale' in t
             for v, t in r['rows'])),
        ('CONTROL: a side branch whose workflow cannot run on a push is '
         'only counted', 'quiet.yml' not in rows
         and '1 workflow version(s) on 1 side branch(es)' in rows),
        ('a workflow GitHub ran this week that is not on main is a FINDING',
         any(v == 'FINDING' and 'gone.yml: not on main' in t
             for v, t in r['rows'])),
        ('a schedule shows among its workflow\'s triggers, and there is no '
         'separate cron table', "schedule ['15 3 * * *']" in out
         and 'CRON' not in out),
        ('a repository it cannot reach is NOT REACHED, never clean',
         not u['reached'] and 'NOT REACHED' in out and 'o/unreached' in out),
        ('the totals line counts the findings it printed',
         f'ci_fleet_audit: {n} finding(s) in 1 repo(s) reached; 1 not '
         f'reached.' in out and n == 4),
        ('a branch with no commit in 7 days is counted, never read',
         'ghost.yml' not in out and 'branch old' not in out
         and '1 side branch(es) with no commit in 7 days not read' in rows),
        # GitHub's runner has no PyYAML (2026-09-26: this check went red
        # there on the staging-into-main pull request, green in every
        # session). The line reader must give push_fires the same answers.
        ('without PyYAML the line reader gives push_fires the same answers',
         all(cfa.push_fires(cfa._on_plain(t), b) == want for t, b, want in (
             (rogue, 'main', True), (side, 'stale', True),
             (quiet, 'calm', False), (cron, 'main', False),
             (approved, 'main', False),
             ('on: push\n', 'x', True), ('on: [pull_request, push]\n', 'x', True),
             ('on:\n  push:\n    tags:\n      - "v*"\n', 'main', False),
             ('on:\n  push:\n    branches-ignore:\n      - x\n', 'x', False),
             ('on:\n  push:\n    branches-ignore:\n      - x\n', 'y', True),
             ('"on":\n  push:\n    branches: [rel/*]\n', 'rel/1', True)))),
        ('a push trigger limited to tags never fires on a branch push',
         not cfa.push_fires({'push': {'tags': ['v*']}}, 'main')
         and cfa.push_fires({'push': {'branches': ['rel/*']}}, 'rel/1')
         and not cfa.push_fires({'push': {'branches-ignore': ['x']}}, 'x')),
    ]
    bad = [c[0] for c in cases if not c[1]]
    check(f'ci_fleet_audit reads GitHub: approved passes, an unapproved '
          f'workflow, a push-triggered side branch and a stray run are '
          f'findings, schedules show as triggers, the unreachable is named '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(bad) + ' -- ' + failure_detail(out, 1500))


def check_ci_fleet_audit_names_when_a_workflow_left_main():
    """practice: ci-workflow-approved, 2026-11-01. A workflow GitHub ran
    that is not on the default branch now was reported as "not on main, yet
    GitHub ran it", even when it had been deleted from main on purpose and
    every run came before the deletion (a practice set's light-check.yml,
    deleted 2026-10-19, last run 2026-10-17). The note now asks main's
    history for the commit that took it off, says when, and names the side
    branches that still carry it. Planted against a fake GitHub."""
    import base64, datetime
    import ci_fleet_audit as cfa

    def b64(t):
        return base64.b64encode(t.encode()).decode()

    push = 'name: x\non:\n  push:\n'
    calls = []

    def fake(path):
        calls.append(path)
        o = 'repos/o/r'
        routes = {
            f'{o}': {'default_branch': 'main', 'private': True},
            f'{o}/actions/workflows?per_page=100': {'workflows': []},
            f'{o}/contents/precedent.json?ref=main':
                {'content': b64(json.dumps({}))},
            f'{o}/contents/.github/workflows?ref=main': [],
            f'{o}/branches?per_page=100':
                [{'name': 'main'}, {'name': 'side'}, {'name': 'old'}],
            f'{o}/branches/side': {'commit': {'commit': {'committer':
                {'date': '2026-10-31T10:00:00Z'}}}},
            f'{o}/branches/old': {'commit': {'commit': {'committer':
                {'date': '2026-08-20T10:00:00Z'}}}},
            f'{o}/contents/.github/workflows?ref=side':
                [{'name': 'carried.yml', 'type': 'file', 'sha': 'b-push'}],
            # deleted.yml left main on 2026-10-19, after its last run.
            f'{o}/commits?path=.github/workflows/deleted.yml&sha=main'
            f'&per_page=1': [{'sha': '1ae858b0000', 'commit': {'committer':
                {'date': '2026-10-19T12:00:00Z'}}}],
            # never.yml was never on main: no commit there touched it.
            f'{o}/commits?path=.github/workflows/never.yml&sha=main'
            f'&per_page=1': [],
            # carried.yml left main on 2026-10-10 and ran after that, from
            # the side branch that still has it.
            f'{o}/commits?path=.github/workflows/carried.yml&sha=main'
            f'&per_page=1': [{'sha': 'abc1234ffff', 'commit': {'committer':
                {'date': '2026-10-10T12:00:00Z'}}}],
        }
        if path.startswith(f'{o}/actions/runs'):
            return {'total_count': 4, 'workflow_runs': [
                {'path': '.github/workflows/deleted.yml', 'event': 'push',
                 'created_at': '2026-10-17T10:00:00Z'},
                {'path': '.github/workflows/deleted.yml', 'event': 'push',
                 'created_at': '2026-10-15T10:00:00Z'},
                {'path': '.github/workflows/never.yml', 'event': 'push',
                 'created_at': '2026-10-30T10:00:00Z'},
                {'path': '.github/workflows/carried.yml', 'event': 'push',
                 'created_at': '2026-10-31T10:00:00Z'}]}, None
        if path.startswith(f'{o}/git/blobs/'):
            return {'content': b64(push)}, None
        if path in routes:
            return routes[path], None
        return {'message': 'Not Found'}, None

    r = cfa.audit_repo('o/r', call=fake, today=datetime.date(2026, 11, 1))
    rows = r['rows']
    text = '\n'.join(f'{v} {t}' for v, t in rows)

    def row(name):
        return [(v, t) for v, t in rows if t.startswith(
            f'.github/workflows/{name}.yml:')]

    deleted, never, carried = row('deleted'), row('never'), row('carried')
    commit_calls = [c for c in calls if '/commits?' in c]
    cases = [
        ('a workflow deleted from main after its last run names the date and '
         'commit, says every run came before it, and is only a NOTE',
         len(deleted) == 1 and deleted[0][0] == 'NOTE'
         and 'removed from main on 2026-10-19 (1ae858b)' in deleted[0][1]
         and 'came before that' in deleted[0][1]
         and 'yet GitHub ran it' not in deleted[0][1]),
        ('it says the stale branch not read may still carry it',
         len(deleted) == 1
         and 'the 1 side branch(es) not read may still carry it'
         in deleted[0][1]),
        ('CONTROL: a workflow never on main keeps the old wording, and says '
         'it never was',
         len(never) == 1 and never[0][0] == 'FINDING'
         and 'not on main and never was, yet GitHub ran it' in never[0][1]),
        ('a workflow removed from main that ran after, from a side branch '
         'that still has it, names that branch and stays a FINDING',
         len(carried) == 1 and carried[0][0] == 'FINDING'
         and 'removed from main on 2026-10-10 (abc1234), yet GitHub ran it '
         'after that' in carried[0][1]
         and 'still on side branch(es) side' in carried[0][1]),
        ('one extra call per such workflow, no more', len(commit_calls) == 3),
    ]
    bad = [c[0] for c in cases if not c[1]]
    check(f'ci_fleet_audit names when a workflow left main, and the side '
          f'branches still carrying it ({len(cases)} stated cases)',
          not bad, '; '.join(bad) + ' -- ' + failure_detail(text, 1500))


def check_very_deep_check_workflow_liveness_scan():
    """tools/very_deep_check.py's _workflow_liveness_scan is the mechanical
    half of Pass 2 item 18 (practices/very-deep-check.md) -- it enumerates
    candidates by content tracking, the same underlying
    precedent_vendor_engine._untracked_ci_workflow_files this repo's
    precedent_check.py registration also calls, so both surfaces agree by
    construction rather than by two hand-kept implementations (Pass 2's own
    item 8: "are there two of anything that should be one?"). This tests
    the function directly, not through the full very_deep_check.py CLI --
    no session-level scope to set up, and the CLI paths (freshness,
    source resolution) are exercised elsewhere."""
    import shutil, tempfile
    import very_deep_check as vdc

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-wf-liveness-'))
    try:
        (tmp / 'tools').mkdir(parents=True)
        (tmp / '.github' / 'workflows').mkdir(parents=True)
        (tmp / '.github/workflows/bestpractice-docs.yml').write_text('name: docs\n')
        (tmp / '.github/workflows/light-check.yml').write_text('name: light\n')
        (tmp / '.github/workflows/hand-authored.yml').write_text('name: hand\n')
        manifest = {'kind': 'consumer',
                    'ci_workflow_files': ['.github/workflows/bestpractice-docs.yml']}
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(manifest))
        (tmp / 'precedent.json').write_text(json.dumps({
            'ci_workflow_outside_vendoring_exempt': [
                {'path': '.github/workflows/hand-authored.yml',
                 'reason': 'a repo-specific check'}]}))

        found = vdc._workflow_liveness_scan(tmp)
        cases = [
            ('the tracked file is never reported',
             not any('bestpractice-docs.yml' in f for f in found), found),
            ('the untracked file IS reported as a CANDIDATE, never a verdict',
             any('light-check.yml' in f and 'CANDIDATE' in f for f in found),
             found),
            ('the exempted file, with its reason declared, is not reported',
             not any('hand-authored.yml' in f for f in found), found),
        ]

        # CONTROL: no manifest at all -- [] returned, never a crash, never
        # a spurious candidate for a repo nothing was ever vendored into.
        no_manifest = tmp / 'no-manifest-case'
        (no_manifest / '.github' / 'workflows').mkdir(parents=True)
        (no_manifest / '.github/workflows/anything.yml').write_text('name: x\n')
        cases.append(('CONTROL: a repo with no ENGINE_MANIFEST.json at all '
                      'returns no candidates, not a crash',
                      vdc._workflow_liveness_scan(no_manifest) == [], None))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'very_deep_check._workflow_liveness_scan enumerates workflow-'
          f'file candidates by content tracking, honours a declared '
          f'exemption, and never crashes on an unvendored repo '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d}" for n, d in bad))


def check_very_deep_check_fixes_a_renamed_repository():
    """When GitHub answers a named repository under a new full name, the very
    deep check repoints the clone's remote and rewrites every CURRENT
    reference, leaving history as written (Morgan, 2026-09-29, strength:
    decided). Discriminating cases: a live line changes; a practice's
    ## Story, a todo/ record and a line about the rename keep the old name;
    the origin remote follows; and a new name that is private is not written
    into a public repository."""
    import io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='rename-fix-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='f', GIT_AUTHOR_EMAIL='f@invalid',
               GIT_COMMITTER_NAME='f', GIT_COMMITTER_EMAIL='f@invalid')

    def git(*a):
        return subprocess.run(['git', '-C', str(tmp), *a], env=env,
                              capture_output=True, text=True).stdout.strip()
    cases = []
    try:
        git('init', '-q')
        (tmp / 'practices').mkdir()
        (tmp / 'todo').mkdir()
        (tmp / 'README.md').write_text(
            'Clone https://github.com/acme/old-tool to start.\n'
            'It was renamed from acme/old-tool in 2026.\n', encoding='utf-8')
        (tmp / 'practices' / 'x.md').write_text(
            '---\nslug: x\nstatus: active\n---\n## Rule\nUse acme/old-tool.\n\n'
            '## Story\nWe first used acme/old-tool.\n', encoding='utf-8')
        (tmp / 'todo' / 'todo-x.md').write_text('acme/old-tool was slow.\n',
                                                encoding='utf-8')
        (tmp / 'NOTES.md').write_text('See acme/secret-old.\n', encoding='utf-8')
        git('add', '-A'); git('commit', '-q', '-m', 'x')
        git('remote', 'add', 'origin', 'https://github.com/acme/old-tool.git')
        vdc.fix_repo_renames({('acme', 'old-tool'): 'acme/new-tool',
                              ('acme', 'secret-old'): 'acme/secret-new'},
                             [tmp], private={'acme/secret-new'},
                             out=io.StringIO())
        readme = (tmp / 'README.md').read_text(encoding='utf-8')
        prac = (tmp / 'practices' / 'x.md').read_text(encoding='utf-8')
        cases.append(('a live reference is rewritten',
                      'github.com/acme/new-tool to start' in readme, readme))
        cases.append(('a line about the rename keeps the old name',
                      'renamed from acme/old-tool' in readme, readme))
        cases.append(('the Rule changes and the Story keeps its history',
                      'Use acme/new-tool.' in prac
                      and 'first used acme/old-tool' in prac, prac))
        cases.append(('a todo record is left as written',
                      'acme/old-tool' in (tmp / 'todo' / 'todo-x.md').read_text(),
                      'todo rewritten'))
        cases.append(('the origin remote follows the rename',
                      git('remote', 'get-url', 'origin')
                      == 'https://github.com/acme/new-tool.git',
                      git('remote', 'get-url', 'origin')))
        cases.append(('a private new name is not written into a public repo',
                      'acme/secret-old' in (tmp / 'NOTES.md').read_text(),
                      (tmp / 'NOTES.md').read_text()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check fixes a renamed repository '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:300]}" for n, d in bad))


def check_branch_report_keeps_private_names_out_of_a_public_tree():
    """The very deep check's tracked branch report (record/stale_branches.md,
    and the safe-to-delete embed in spec/VERY_DEEP_CHECK.md) never carries a
    held-back source's branches or a branch name the leak blocklist matches,
    in a public repo -- and holds nothing back in a private one (practice:
    very-deep-check; control-asserts-which-failure).

    THE INCIDENT (2026-09-28). The first run with the individual source's
    blocklist resolved wrote a branch named after a private project into
    this public repo's record/stale_branches.md, and its own push gate
    refused the result. The same file had carried the private individual
    set's branch names, authors and dates since 2026-09-19 -- the
    disclosure the practice catalogue was fixed for on 2026-09-24, in the
    file next to it.

    The fixture owns its own tree: a temp repo, a temp blocklist named by
    the environment variable the push gate reads, and hand-built scan
    results, so no git history or network is involved."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import leak_gate

    SECRET = 'zzfixtureprivateproject-branch'
    SET_BRANCH = 'claude/zzfixture-private-set-branch'
    PLAIN = 'claude/zzfixture-plain-branch'

    def row(name, stale=False):
        return {'name': name, 'last': '2026-09-01', 'age_days': 3,
                'author': 'Fixture', 'stale': stale}

    def scans(root, ind):
        return {
            'checkout': {'path': str(root), 'target': 'staging',
                         'merged': [row(SECRET, stale=True), row(PLAIN)],
                         'merged_elsewhere': [],
                         'unmerged': [dict(row('claude/zz-unmerged'),
                                           ahead=1, verdict='fixture')]},
            'individual source fixture-individual': {
                'path': str(ind), 'target': 'main',
                'merged': [row(SET_BRANCH)], 'merged_elsewhere': [],
                'unmerged': []},
        }

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='branch-report-privacy-'))
    old_env = os.environ.get(leak_gate.BLOCKLIST_ENV)
    try:
        bl = tmp / 'blocklist.txt'
        bl.write_text('zzfixtureprivateproject\n', encoding='utf-8')
        os.environ[leak_gate.BLOCKLIST_ENV] = str(bl)
        for vis in ('public', 'private'):
            root = tmp / vis
            ind = tmp / (vis + '-individual')
            for d in (root, ind):
                d.mkdir()
            (root / 'precedent.json').write_text(
                json.dumps({'format_version': 1, 'visibility': vis}),
                encoding='utf-8')
            sources = [
                {'level': 'universal', 'name': 'precedent', 'path': str(root)},
                {'level': 'individual', 'name': 'fixture-individual',
                 'path': str(ind)}]
            sc = scans(root, ind)
            held, redact = vdc._branch_report_privacy(root, sources, sc)
            out = vdc._write_branch_report(sc, root / 'report.md', root,
                                           held_back=held, redact=redact)
            text = out.read_text(encoding='utf-8')
            embed = vdc._merged_stale_checkout_markdown(sc['checkout'],
                                                        redact=redact)
            if vis == 'public':
                cases.append(('THE CASE THIS EXISTS FOR: a blocklisted branch '
                              'name never reaches a public tracked report',
                              SECRET not in text and SECRET not in embed,
                              text[:300]))
                cases.append(('a held-back source\'s branches stay out of it',
                              SET_BRANCH not in text and 'Held back' in text,
                              failure_detail(text, 600)))
                cases.append(('an ordinary branch is still listed',
                              PLAIN in text, text[:600]))
            else:
                cases.append(('THE DISCRIMINATING CASE: a private repo holds '
                              'nothing back', SECRET in text
                              and SET_BRANCH in text and not held
                              and not redact, text[:300]))
    finally:
        if old_env is None:
            os.environ.pop(leak_gate.BLOCKLIST_ENV, None)
        else:
            os.environ[leak_gate.BLOCKLIST_ENV] = old_env
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the branch report keeps blocklisted names and held-back sources '
          f'out of a public repo\'s tracked files, and only there '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_very_deep_check_reads_live_and_names_landing_work():
    """The very deep check says what it reads against the live `main`, and
    names what the landing branch carries that is not live yet (practice:
    very-deep-check -- read main, write through the landing branch; Morgan,
    2026-09-28). Planted: a clone on a branch equal to main (reads the live
    version), then the same clone on a branch that differs (a NOTE), and a
    staging carrying one file main lacks (named, so a finding in it is
    checked there before it is fixed twice)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-live-landing-'))
    cases = []
    def git(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), '-c', 'user.name=F',
                               '-c', 'user.email=f@invalid', *a],
                              capture_output=True, text=True, check=True).stdout
    try:
        origin, work, clone = tmp / 'origin.git', tmp / 'work', tmp / 'clone'
        subprocess.run(['git', 'init', '-q', '--bare', str(origin)], check=True)
        work.mkdir()
        git(work, 'init', '-q', '-b', 'main')
        (work / 'precedent.json').write_text(
            json.dumps({'format_version': 1, 'base_branch': 'main',
                        'staging_branch': 'staging', 'landing_branch': 'staging'}),
            encoding='utf-8')
        (work / 'a.md').write_text('live\n', encoding='utf-8')
        git(work, 'add', '-A'); git(work, 'commit', '-q', '-m', 'live')
        git(work, 'remote', 'add', 'origin', str(origin))
        git(work, 'push', '-q', 'origin', 'main')
        git(work, 'checkout', '-q', '-b', 'staging')
        (work / 'zz-not-live.md').write_text('waiting\n', encoding='utf-8')
        git(work, 'add', '-A'); git(work, 'commit', '-q', '-m', 'unpromoted')
        git(work, 'push', '-q', 'origin', 'staging')
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)], check=True)
        git(clone, 'fetch', '-q', 'origin', 'staging:refs/remotes/origin/staging')
        git(clone, 'checkout', '-q', '-b', 'work', 'origin/main')
        rows = vdc._live_vs_landing(clone)
        text = ' | '.join(f'{v} {m}' for v, m in rows)
        cases.append(('a branch equal to main reads the live version',
                      any(v == 'OK' and 'live version' in m for v, m in rows),
                      text))
        cases.append(('the landing branch\'s not-yet-live file is named',
                      any('zz-not-live.md' in m for v, m in rows), text))
        (clone / 'a.md').write_text('edited\n', encoding='utf-8')
        git(clone, 'commit', '-qam', 'edit')
        rows = vdc._live_vs_landing(clone)
        text = ' | '.join(f'{v} {m}' for v, m in rows)
        cases.append(('THE DISCRIMINATING CASE: a branch that differs from '
                      'main is not reported as reading the live version',
                      not any('live version' in m for v, m in rows)
                      and any('differs from the live' in m for v, m in rows),
                      text))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check says whether it reads the live main, and what '
          f'the landing branch has not yet made live ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_very_deep_check_blocked_on_and_net_empty_branches():
    """Two very deep check signals that reported something that was not
    there (2026-09-28 very deep check, approved by Morgan).

    BLOCKED-ON NAMES SOMETHING GONE resolved every path in an item's
    `blocked_on` against this tree, so a path that only exists in a
    consumer (`process/upstream`, `tools/ENGINE_MANIFEST.json`) read as
    gone. Planted: one item per shape -- the classic layout, the engine's
    manifest, a path the item frames as a consumer's, a backticked path
    that does exist at the root (read from todo/ before, so gone) -- none
    reported; and one path genuinely gone, still reported.

    UNLANDED WORK counted a branch whose commits cancel out (a change and
    its revert) as carrying unlanded work. Planted beside a branch with
    real work, which must still read as unlanded."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-blocked-netempty-'))
    cases = []

    def item(slug, blocked):
        return ('---\n'
                f'slug:              {slug}\n'
                'kind:              analysis\n'
                'status:            open\n'
                'disposition:       wait\n'
                f'blocked_on:        {json.dumps(blocked)}\n'
                'noted:             2026-01-01\n'
                '---\n\n## What\n\n'
                f'**{slug} title.**\n')
    try:
        repo = tmp / 'repo'
        (repo / 'todo').mkdir(parents=True)
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'real_tool.py').write_text('x\n', encoding='utf-8')
        planted = {
            'todo-2026-01-01-classic':
                'make the gate quiet under the `process/upstream` layout.',
            'todo-2026-01-01-manifest':
                'the engine reads its kind from `tools/ENGINE_MANIFEST.json`.',
            'todo-2026-01-01-framed':
                'a consumer that carries `tools/consumer_config.json` says so.',
            'todo-2026-01-01-exists':
                'a fix to `tools/real_tool.py`.',
            'todo-2026-01-01-gone':
                'the fix in `tools/retired_tool.py`.',
        }
        for slug, blocked in planted.items():
            (repo / 'todo' / f'{slug}.md').write_text(item(slug, blocked),
                                                      encoding='utf-8')
        out = '\n'.join(vdc._open_item_sweep(repo))
        block = out.split('BLOCKED-ON NAMES SOMETHING GONE', 1)[-1] \
            if 'BLOCKED-ON NAMES SOMETHING GONE' in out else ''
        block = block.split('OLDEST', 1)[0]
        for slug in ('classic', 'manifest', 'framed', 'exists'):
            cases.append((f'a {slug} path is not reported as gone',
                          f'todo-2026-01-01-{slug}' not in block, out))
        cases.append(('THE CONTROL: a path genuinely gone from this tree is '
                      'still reported',
                      'todo-2026-01-01-gone' in block
                      and 'missing: tools/retired_tool.py' in block, out))

        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        fixture_git(up, 'init', '-q', '-b', 'main')
        fixture_git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        fixture_git(up, 'config', 'user.email', 'harness@example.com')
        fixture_git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        fixture_git(up, 'add', '-A'); fixture_git(up, 'commit', '-qm', 'base')
        fixture_git(up, 'checkout', '-q', '-b', 'cancels-out')
        (up / 'base.txt').write_text('base\nadded\n')
        fixture_git(up, 'commit', '-qam', 'add a line')
        (up / 'base.txt').write_text('base\n')
        fixture_git(up, 'commit', '-qam', 'take it back out')
        fixture_git(up, 'checkout', '-q', 'main')
        fixture_git(up, 'checkout', '-q', '-b', 'real-work')
        (up / 'feature.txt').write_text('unlanded\n')
        fixture_git(up, 'add', '-A')
        fixture_git(up, 'commit', '-qm', 'unlanded work')
        fixture_git(up, 'checkout', '-q', 'main')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        scan = vdc.scan_branches(work, 'main')
        rows = {r['name']: r for r in (scan or {}).get('unmerged', [])}
        ce = rows.get('cancels-out', {})
        rw = rows.get('real-work', {})
        cases.append(('a branch whose commits cancel out reads as net-empty',
                      (ce.get('verdict') or '').startswith(
                          'net-empty: its commits cancel out; nothing to land'),
                      repr(ce)))
        cases.append(('THE CONTROL: a branch with real work still CARRIES it',
                      not rw.get('net_empty')
                      and 'CARRIES' in (rw.get('verdict') or ''), repr(rw)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check reports neither a consumer-only path as gone '
          f'nor a net-empty branch as unlanded work ({len(cases)} stated '
          f'cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_very_deep_check_refuses_unknown_flags_before_the_ledger():
    """very_deep_check.py refuses an argument it does not read, with its
    usage and exit 2, before the ledger is touched; and --record-pass lands
    on the last COMPLETED run, never on an aborted one after it (practice:
    very-deep-check).

    THE INCIDENT (filed 2026-09-21, still true 2026-09-28). `--check`,
    `--explain`, `--list` and `--dry-run` -- real flags in sibling tools --
    each started a full run and appended an incomplete row to the ledger,
    which then became "the last run" for every since-the-last-run section,
    and the row a hand-worked --record-pass attached to."""
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-unknown-flag-'))
    cases = []
    try:
        ledger = tmp / 'ledger.json'
        for flag in ('--check', '--dry-run', '--explain', '--list'):
            r = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
                 '--repo', str(tmp), '--ledger', str(ledger), flag],
                capture_output=True, text=True, cwd=str(tmp), timeout=120)
            cases.append((f'{flag} refuses with exit 2 and the usage, and '
                          f'writes no ledger',
                          r.returncode == 2 and 'unknown argument' in r.stderr
                          and 'Exit: 1 if any repo in force' in r.stderr
                          and not ledger.exists(),
                          f'exit {r.returncode}; ledger exists: '
                          f'{ledger.exists()}; {failure_detail(r.stderr, 300)}'))
        # A valued flag's value is not an unknown argument (the control).
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--ledger', str(tmp / 'none.json'), '--record-pass', '2=done'],
            capture_output=True, text=True, cwd=str(tmp), timeout=120)
        cases.append(('CONTROL: a known valued flag is not refused as unknown',
                      'unknown argument' not in r.stderr, failure_detail(r.stderr, 300)))

        good = tmp / 'good.json'
        good.write_text(json.dumps({'runs': [
            {'run_id': 'R-COMPLETE', 'completed': True, 'components': []},
            {'run_id': 'R-ABORTED', 'completed': False, 'components': []},
        ]}), encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--ledger', str(good), '--record-pass', '3=done,findings=2'],
            capture_output=True, text=True, cwd=str(tmp), timeout=120)
        runs = json.loads(good.read_text(encoding='utf-8'))['runs']
        cases.append(('THE CASE: --record-pass lands on the last completed '
                      'run, not the aborted one after it, and says so',
                      r.returncode == 0
                      and len(runs[0].get('passes') or []) == 1
                      and not runs[1].get('passes')
                      and 'did not complete' in r.stderr,
                      f'exit {r.returncode}; {runs}; {failure_detail(r.stderr, 300)}'))
        # Recording the same pass on the same run again replaces it
        # (2026-10-17): it used to append a second entry for pass 3.
        for arg in ('3=done,findings=5,note=recounted', '2=done'):
            r = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
                 '--ledger', str(good), '--record-pass', arg],
                capture_output=True, text=True, cwd=str(tmp), timeout=120)
        passes = json.loads(good.read_text(encoding='utf-8'))['runs'][0].get(
            'passes') or []
        threes = [p for p in passes if p.get('pass') == '3']
        cases.append(('THE CASE: the same pass recorded again on the same run '
                      'replaces its entry, and a different pass is added',
                      len(threes) == 1 and threes[0].get('findings') == 5
                      and threes[0].get('note') == 'recounted'
                      and [p.get('pass') for p in passes] == ['3', '2'],
                      f'{passes}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'very_deep_check refuses an unknown flag before the ledger, and '
          f'--record-pass targets the last completed run '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_identity_reality_reads_grandfathering_the_bot_and_a_shallow_clone():
    """IDENTITY REALITY subtracts the repo's own grandfathered_commit_shas,
    calls a commit by the container's bot address a FINDING rather than
    "another author", and says when a shallow clone truncated its window
    (practice: very-deep-check, pass 2; 2026-09-28: eight bot-authored
    commits on a shared set's main read as "not a finding")."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-identity-'))
    cases = []
    try:
        up = tmp / 'up'
        up.mkdir()
        fixture_git(up, 'init', '-q', '-b', 'main')

        def commit(msg, name, email):
            (up / 'f.txt').write_text(msg + '\n', encoding='utf-8')
            fixture_git(up, 'add', '-A')
            fixture_git(up, '-c', 'core.hooksPath=/dev/null',
                        '-c', f'user.name={name}', '-c', f'user.email={email}',
                        'commit', '-qm', msg)
            return fixture_git(up, 'rev-parse', 'HEAD').stdout.strip()

        commit('other', 'Someone Else', 'someone@example.com')
        old_bot = commit('bot, grandfathered', 'Claude', vdc.BOT_EMAIL)
        new_bot = commit('bot, live', 'Claude', vdc.BOT_EMAIL)
        (up / 'precedent.json').write_text(json.dumps({
            'grandfathered_commit_shas': [
                {'sha': old_bot, 'note': 'fixture: exempted on purpose'}]}),
            encoding='utf-8')
        rows, notes = vdc._identity_reality(up)
        text = '\n'.join(f'{v} {m}' for v, m in rows) + '\n' + '\n'.join(notes)
        bot_rows = [m for v, m in rows if v == 'FINDING' and vdc.BOT_EMAIL in m]
        cases.append(('THE CASE: a bot-authored commit is a FINDING, not '
                      'another author',
                      len(bot_rows) == 1 and 'other authors' not in
                      ' '.join(n for n in notes if vdc.BOT_EMAIL in n), text))
        cases.append(('a grandfathered commit is subtracted, and said so',
                      bot_rows and bot_rows[0].startswith('1 commit')
                      and old_bot[:9] not in bot_rows[0]
                      and new_bot[:9] in bot_rows[0]
                      and any('1 grandfathered' in n for n in notes), text))
        cases.append(('CONTROL: a person\'s commit is still only a note',
                      any('someone@example.com' in n for n in notes), text))
        cases.append(('CONTROL: a full clone says nothing about shallowness',
                      not any('shallow' in n for n in notes), text))

        shallow = tmp / 'shallow'
        subprocess.run(['git', 'clone', '-q', '--depth', '1', f'file://{up}',
                        str(shallow)], capture_output=True, text=True)
        rows2, notes2 = vdc._identity_reality(shallow)
        cases.append(('a shallow clone says where its history starts and '
                      'that the window is truncated',
                      any(n.startswith('(shallow: history starts ')
                          and 'window truncated' in n for n in notes2),
                      '\n'.join(notes2)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'IDENTITY REALITY subtracts grandfathered commits, flags the bot '
          f'address and names a shallow window ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


def check_config_keys_counts_a_key_a_practice_reads():
    """CONFIG KEYS names the practice through which a SESSION reads a key,
    and does not count that key as read by nothing (practice:
    very-deep-check, pass 2; 2026-09-28: `writeup_dir`, read by whoever
    follows write-it-up, reported as read by nothing on every run)."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-config-keys-'))
    cases = []
    try:
        repo, other = tmp / 'repo', tmp / 'other'
        for d in (repo / 'tools', repo / 'practices', other / 'practices'):
            d.mkdir(parents=True)
        (repo / 'precedent.json').write_text(json.dumps({
            'zz_read_by_script': 1, 'zz_read_by_session': 2,
            'zz_read_by_other_set': 3, 'zz_read_by_nothing': 4}),
            encoding='utf-8')
        (repo / 'tools' / 'reader.py').write_text(
            "KEY = 'zz_read_by_script'\n", encoding='utf-8')
        (repo / 'practices' / 'zz-session-rule.md').write_text(
            '---\nslug: zz-session-rule\n---\n\n## Rule\n\nRead '
            '`zz_read_by_session` from precedent.json.\n', encoding='utf-8')
        (other / 'practices' / 'zz-other-rule.md').write_text(
            '---\nslug: zz-other-rule\n---\n\n## Rule\n\nSet '
            '"zz_read_by_other_set" where it applies.\n', encoding='utf-8')
        rows, note = vdc._config_key_reads(
            repo, [('repo', str(repo)), ('other set', str(other))])
        by = {r[1]: r for r in rows}
        try:
            cases.append(('THE CASE: a key a practice names is read by a '
                          'session through that practice',
                          by['zz_read_by_session'][4] == ['zz-session-rule'],
                          repr(by.get('zz_read_by_session'))))
            cases.append(('a practice in ANOTHER repo in force counts too',
                          by['zz_read_by_other_set'][4] == ['zz-other-rule'],
                          repr(by.get('zz_read_by_other_set'))))
            cases.append(('CONTROL: a key nothing names stays read by nothing',
                          by['zz_read_by_nothing'][2] == []
                          and by['zz_read_by_nothing'][4] == [],
                          repr(by.get('zz_read_by_nothing'))))
            cases.append(('CONTROL: a key a script reads is not searched '
                          'further', by['zz_read_by_script'][2] != []
                          and by['zz_read_by_script'][4] == [],
                          repr(by.get('zz_read_by_script'))))
        except (KeyError, IndexError) as exc:
            cases.append(('rows carry the practice readers',
                          False, f'{type(exc).__name__}: {exc}; {rows!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'CONFIG KEYS names the practice a session reads a key through '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_moved_claims_skips_narrated_deletions_and_templates():
    """MOVED CLAIMS reports a sentence saying work moved to a file that is
    not there -- but not one NARRATING that the destination was later
    deleted (the same line or the next three), and not one naming a file
    this repo ships as `templates/**/<name>.template` (practice:
    very-deep-check, pass 3; 2026-09-28: eight rows across two repos, every
    one a history sentence about precedent-check.yml)."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-moved-'))
    cases = []
    try:
        fixture_git(tmp, 'init', '-q', '-b', 'main')
        (tmp / 'templates' / 'kind').mkdir(parents=True)
        (tmp / 'templates' / 'kind' / 'zzshipped.yml.template').write_text(
            'x\n', encoding='utf-8')
        (tmp / 'a.md').write_text(
            'Its checks were folded into zzgoneone.yml, which a refresh '
            'later deleted.\n', encoding='utf-8')
        (tmp / 'b.md').write_text(
            'On the 19th the checks were folded into zzgonetwo.yml as steps.\n'
            'That was safe while it lasted.\n\n'
            'The destination went with it two days later.\n',
            encoding='utf-8')
        (tmp / 'c.md').write_text(
            'The workflow now lives in zzshipped.yml for every consumer.\n',
            encoding='utf-8')
        (tmp / 'd.md').write_text(
            'The check now lives in zzmissing.yml.\n', encoding='utf-8')
        (tmp / 'e.md').write_text(
            'The check has moved to zzfar.yml.\n\n\n\n\n'
            'Much later, an unrelated file was deleted.\n', encoding='utf-8')
        fixture_git(tmp, 'add', '-A')
        rows = vdc._moved_claims(tmp) or []
        targets = {r[3] for r in rows}
        cases.append(('THE CASE: a claim whose own sentence says the '
                      'destination was deleted is history, not a row',
                      'zzgoneone.yml' not in targets, repr(rows)))
        cases.append(('...and so is one whose next lines say it went with it',
                      'zzgonetwo.yml' not in targets, repr(rows)))
        cases.append(('a file shipped as templates/**/<name>.template exists',
                      'zzshipped.yml' not in targets, repr(rows)))
        cases.append(('CONTROL: a live claim naming a missing file is a row',
                      'zzmissing.yml' in targets, repr(rows)))
        cases.append(('CONTROL: a deletion four or more lines on does not '
                      'excuse it', 'zzfar.yml' in targets, repr(rows)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'MOVED CLAIMS skips narrated deletions and templated targets and '
          f'still reports a live one ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_ci_fleet_audit_counts_each_workflow_past_the_sample():
    """ci_fleet_audit.py reads at most RUN_PAGES pages of a repo's runs. In
    a repo busier than that, each workflow's "Last 30 days" is GitHub's own
    total_count for that workflow, one call each, or "at least N" where
    that cannot be asked -- never its share of the sample printed as the
    count (practice: ci-workflow-approved, 2026-09-28). Planted against a
    fake GitHub."""
    import base64, datetime
    import ci_fleet_audit as cfa

    def b64(t):
        return base64.b64encode(t.encode()).decode()

    busy = 'name: busy\non:\n  pull_request:\n'
    other = 'name: other\non:\n  pull_request:\n'
    calls = []

    def fake(path, total=450, per_wf=None):
        calls.append(path)
        o = 'repos/o/r'
        if path == o:
            return {'default_branch': 'main', 'private': False}, None
        if path == f'{o}/actions/workflows?per_page=100':
            return {'workflows': [
                {'id': 7, 'path': '.github/workflows/busy.yml',
                 'state': 'active'},
                {'id': 8, 'path': '.github/workflows/other.yml',
                 'state': 'active'}]}, None
        if path.startswith(f'{o}/actions/workflows/7/runs'):
            return {'total_count': 420, 'workflow_runs': []}, None
        if path.startswith(f'{o}/actions/workflows/8/runs'):
            return {'message': 'Server Error'}, 'HTTP 500'
        if path.startswith(f'{o}/actions/runs'):
            return {'total_count': total, 'workflow_runs': [
                {'path': '.github/workflows/busy.yml', 'event': 'push',
                 'created_at': '2026-09-25T10:00:00Z'}] * 90 + [
                {'path': '.github/workflows/other.yml', 'event': 'push',
                 'created_at': '2026-09-25T10:00:00Z'}] * 10}, None
        if path == f'{o}/contents/.github/workflows?ref=main':
            return [{'name': 'busy.yml', 'type': 'file', 'sha': 'b-busy'},
                    {'name': 'other.yml', 'type': 'file', 'sha': 'b-other'}], None
        if path.startswith(f'{o}/git/blobs/'):
            return {'content': b64({'b-busy': busy, 'b-other': other}[
                path.rsplit('/', 1)[1]])}, None
        if path == f'{o}/branches?per_page=100':
            return [{'name': 'main'}], None
        return {'message': 'Not Found'}, None

    today = datetime.date(2026, 9, 26)
    r = cfa.audit_repo('o/r', call=fake, today=today)
    rows = {t.split(' [')[0]: t for _v, t in r['rows'] if ' [' in t}
    busy_t = rows.get('.github/workflows/busy.yml', '')
    other_t = rows.get('.github/workflows/other.yml', '')
    n_wf_calls = sum(1 for c in calls if '/actions/workflows/' in c
                     and '/runs' in c)

    calls.clear()
    small = cfa.audit_repo('o/r', call=lambda p: fake(p, total=300),
                           today=today)
    small_t = {t.split(' [')[0]: t for _v, t in small['rows'] if ' [' in t}
    n_small = sum(1 for c in calls if '/actions/workflows/' in c
                  and '/runs' in c)
    cases = [
        ('THE CASE: past the sample, a workflow\'s count is GitHub\'s own',
         '420 runs (GitHub\'s own count' in busy_t, busy_t),
        ('where its own count cannot be asked, it says "at least"',
         'at least 30 runs (of the newest 300 read' in other_t, other_t),
        ('the sample is never printed as the count',
         'Last 30 days: 270 runs' not in busy_t, busy_t),
        ('one extra call per workflow, no more',
         n_wf_calls == 2, f'{n_wf_calls} calls'),
        ('CONTROL: a repo the sample covers costs no extra call and prints '
         'its exact count', n_small == 0
         and '270 runs (push 270)' in small_t.get(
             '.github/workflows/busy.yml', ''),
         f'{n_small} calls; {small_t}'),
    ]

    # GitHub's filtered listing stops counting (2026-10-17): BestPractice's
    # repository total read 2500 while two workflows' own counts were 1027
    # and 2394. A count at the cap is "at least", and parts that add up to
    # more than the whole are said. Planted, no API call.
    def capped(path):
        o = 'repos/o/r'
        if path.startswith(f'{o}/actions/workflows/7/runs'):
            return {'total_count': 1027, 'workflow_runs': []}, None
        if path.startswith(f'{o}/actions/workflows/8/runs'):
            return {'total_count': cfa.LISTING_CAP, 'workflow_runs': []}, None
        return fake(path, total=cfa.LISTING_CAP)
    big = cfa.audit_repo('o/r', call=capped, today=today)
    texts = [t for _v, t in big['rows']]
    big_t = {t.split(' [')[0]: t for t in texts if ' [' in t}
    cases += [
        ('THE CASE: a repository total at the listing cap is "at least"',
         any(t.startswith(f'at least {cfa.LISTING_CAP} runs in') for t in texts),
         texts),
        ('so is a workflow\'s own count at the cap',
         f'at least {cfa.LISTING_CAP} runs' in big_t.get(
             '.github/workflows/other.yml', ''), big_t),
        ('per-workflow counts that add up to more than the total are named',
         any(f'add up to {1027 + cfa.LISTING_CAP} runs' in t for t in texts),
         texts),
        ('CONTROL: counts under the cap that add up are left as numbers',
         not any('add up to' in t or t.startswith('at least')
                 for _v, t in small['rows']), small['rows']),
    ]
    bad = [c[0] + ' -- ' + str(c[2])[:300] for c in cases if not c[1]]
    check(f'ci_fleet_audit counts each workflow past the 300-run sample '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_vendored_surplus_counts_a_folder_a_consumer_is_told_to_search():
    """VENDORED SURPLUS named every retired gotcha as shipped to nobody, but
    environment-gotchas tells a session in a consumer to grep
    `process/upstream/gotchas/`: a search is a reader, and it names no file
    (2026-10-17 very deep check). THE CASE: a file in a folder a shipped
    file names by its consumer path is not UNNAMED. CONTROL: a file in a
    folder nothing names still is."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-surplus-'))
    try:
        for rel, text in {
                'practices/env.md': 'grep `process/upstream/gotchas/` first\n',
                'gotchas/gotcha-old.md': 'a retired trap\n',
                'misc/stray.md': 'nobody names me\n'}.items():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text, encoding='utf-8')
        shipped = {f'process/upstream/{r}': (r, 'copy')
                   for r in ('practices/env.md', 'gotchas/gotcha-old.md',
                             'misc/stray.md')}
        unnamed = vdc._named_anywhere_else(shipped, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cases = [
        ('THE CASE: a gotcha in the folder a practice tells consumers to grep '
         'is not unnamed',
         'process/upstream/gotchas/gotcha-old.md' not in unnamed, unnamed),
        ('CONTROL: a file in a folder nothing names is still unnamed',
         'process/upstream/misc/stray.md' in unnamed, unnamed),
    ]
    bad = [c[0] + ' -- ' + str(c[2]) for c in cases if not c[1]]
    check(f'VENDORED SURPLUS counts a folder consumers are told to search as '
          f'read ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_machine_readable_files_parse():
    """Every JSON and YAML file this change TOUCHED still parses.

    Changed-scope on purpose. This gates a push and runs constantly, so its
    question is "did I just break something", not "is the whole repo well".
    The whole-tree sweep is the very deep check's job
    (`tools/very_deep_check.py`), which is on-demand and is the only place a
    file nobody has touched in months gets looked at again.

    Nothing here parsed a YAML or JSON file at all until 2026-09-06 -- not
    .github/workflows/deep-check.yml, the file that RUNS this check in CI,
    and not precedent.json, MANIFEST.json, ENGINE_MANIFEST.json or
    routing_scope.json, each read by exactly one tool that would report its
    own confusing failure rather than "this file is malformed". A broken
    workflow is the worst of them: GitHub skips it silently, so the gate
    stops running and every push looks as green as the day before. That is
    the worst shape a check can have, and it applied to the check-running
    check itself."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_parse_check', ROOT / 'tools' / 'parse_check.py')
    pcheck = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcheck)

    paths, scope = pcheck.changed(ROOT)
    failures, parsed, skipped = pcheck.validate(ROOT, paths)
    n = len(pcheck.candidates(ROOT, paths))
    for rel, why in failures:
        print(f"  {rel}: {why}")
    if skipped:
        not_applicable(f'{", ".join(skipped)} files in scope were not parsed',
                       'no parser installed here (pip install pyyaml) -- a '
                       'file nobody parsed is not a file that parses')
    check(f'every JSON/YAML file this change touched parses '
          f'({n} in scope; {scope})', not failures)

    # Scripts a workflow actually invokes, as opposed to mentions in prose.
    # Same class as vendored-engine-file-refs-resolve: a job calling a
    # missing script fails on every run, and nothing says so until somebody
    # reads a CI log. Whole-tree because there are three of them.
    RUN_SCRIPT = re.compile(r'python3?\s+((?:tools|process|deck)/[\w/.-]+\.py)')
    workflows = [f for f in pcheck.tracked(ROOT) if '/workflows/' in f]
    missing = []
    for rel in workflows:
        text = (ROOT / rel).read_text(encoding='utf-8')
        for name in sorted(set(RUN_SCRIPT.findall(text))):
            if not (ROOT / name).is_file():
                missing.append((rel, name))
    for rel, name in missing:
        print(f"  {rel}: runs {name}, which does not exist")
    check(f'every script a workflow runs exists ({len(workflows)} workflow '
          f'file(s))', not missing)


def check_split_projection_is_costed_and_ordered():
    """A flagged section made of entries gets the costed split table
    (practice: control-asserts-which-failure).

    WHY. Told a section is 9,000 tokens and that splitting is an option, a
    person still cannot choose -- the question is always "what would that
    leave, and what would it cost me". On 2026-09-13 those figures existed
    only because a session was asked to compute them; the deep read that
    flagged the section could have handed them over and did not.

    The discriminating case is a section with no entries to split: a
    projection there would be inventing a saving nobody can take
    (no-invented-specifics). The fixture owns its own tree."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc

    entry = ('- **A trap that bites.** It failed on a Tuesday and cost an '
             'hour. The remedy is to read the exit code. A third sentence '
             'carries the reason. A fourth carries the caveat.\n')
    section = ('## Gotchas\n\n' + entry * 12)
    proj = vdc._split_projection(section)

    cases = []
    cases.append(('a section of 12 entries is costed at all', bool(proj), proj))
    cases.append(('it names all four rows, cheapest first',
                  'bolded lead only' in proj and 'lead + 1 sentence' in proj
                  and 'lead + 2 sentences' in proj and 'lead + 3 sentences' in proj,
                  proj))

    import re as _re
    saves = [int(x.replace(',', ''))
             for x in _re.findall(r'saves\s+([\d,]+)', proj)]
    cases.append(('THE ORDERING CASE: keeping more text saves less, strictly '
                  '-- a table that did not would be arithmetic nobody can act on',
                  len(saves) == 4 and all(saves[i] > saves[i + 1] for i in range(3)),
                  repr(saves)))
    cases.append(('it says the figures bound the saving rather than predicting it',
                  'bounds the saving' in proj, proj))
    cases.append(('and that the text moves out whole either way',
                  'moves out whole' in proj, proj))

    cases.append(('THE DISCRIMINATING CASE: a section with no entries to split '
                  'is not costed at all',
                  vdc._split_projection('## Prose\n\nJust paragraphs here.\n') == '',
                  repr(vdc._split_projection('## Prose\n\nJust paragraphs.\n'))))
    cases.append(('and neither is a section with too few entries to be worth it',
                  vdc._split_projection('## Gotchas\n\n' + entry * 3) == '',
                  repr(vdc._split_projection('## Gotchas\n\n' + entry * 3))))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the split projection is costed, ordered, and absent where there is '
          f'nothing to split ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_settled_marker_scan_is_scoped_and_follows_the_split():
    """The SESSION LOAD pass's settled-trap signal reads gotcha entries, and
    only gotcha entries (practice: control-asserts-which-failure).

    THE INCIDENT (2026-09-13), and it failed in both directions in one commit.
    The scan walked every markdown bullet in the instructions file, which was
    harmless only while the gotchas were the file's one bulleted list. A
    reduction pass turned the standing commands into bullets, so the last of
    them swallowed 8,582 tokens of unrelated sections and reported it as one
    entry whose trap was settled. The SAME pass then split the gotchas into an
    index plus a record, and the bodies this signal reads left the file -- so
    it dropped from two real findings to zero. **Zero findings is what a clean
    section looks like**, which is why this needs a control rather than a
    reading: nothing about the output said it had stopped working.

    The fixture owns its own tree (fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc

    STORY = ('It failed on 2026-09-13 and cost an hour. That is fixed now in '
             'the tree, so the entry may be archivable.\n')
    LIVE = ('It failed on 2026-09-13 and cost an hour. Nothing has changed '
            'since, and it still bites every session.\n')

    def run(agents, record=None):
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            (d / 'AGENTS.md').write_text(agents, encoding='utf-8')
            if record is not None:
                (d / 'record').mkdir()
                (d / 'record' / 'GOTCHAS.md').write_text(record, encoding='utf-8')
            _rows, msgs = vdc._session_load(d)
            return '\n'.join(m for m in msgs if m.startswith('note'))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    PREAMBLE = ('# fixture\n\n- **"Update Vendors"** a standing command, not a '
                'gotcha. It is fixed now.\n\n')
    SPLIT = (PREAMBLE + '## Build-environment gotchas -- do NOT rediscover '
             'these\n\n'
             '- **A settled trap.** [story](record/GOTCHAS.md#g1)\n\n'
             '- **A live trap.** [story](record/GOTCHAS.md#g2)\n\n'
             '## Working in this repo\n\n- **A convention.** It is fixed now.\n')
    RECORD = ('# Gotchas\n\n## 1. <a id="g1"></a>Settled\n\n' + STORY +
              '\n## 2. <a id="g2"></a>Live\n\n' + LIVE)

    cases = []
    out = run(SPLIT, RECORD)
    cases.append(('THE REGRESSION CASE: a settled marker in the RECORD is '
                  'found, not lost with the bodies',
                  'Settled' not in out and 'A settled trap' in out, out))
    cases.append(('and the live entry beside it is not reported',
                  'A live trap' not in out, out))
    cases.append(('a bullet OUTSIDE the gotchas section is not parsed as an '
                  'entry -- the 8,582-token false positive',
                  'Update Vendors' not in out and 'A convention' not in out,
                  out))

    unsplit = (PREAMBLE + '## Build-environment gotchas -- do NOT rediscover '
               'these\n\n- **A settled trap.** ' + STORY +
               '\n- **A live trap.** ' + LIVE +
               '\n## Working in this repo\n\n- **A convention.** It is fixed now.\n')
    out = run(unsplit)
    cases.append(('an UNSPLIT section still reports its own settled entry',
                  'A settled trap' in out and 'A live trap' not in out
                  and 'Update Vendors' not in out, out))

    no_section = ('# fixture\n\n- **A bullet.** It is fixed now.\n\n## Other\n')
    out = run(no_section)
    cases.append(('THE DISCRIMINATING CASE: a file with no gotchas section '
                  'raises nothing at all', out == '', out))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the settled-trap signal is scoped to gotcha entries and follows a '
          f'split ({len(cases)} stated cases, both directions of the '
          f'2026-09-13 regression covered)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_session_load_reports_a_file_over_its_own_declared_ceiling():
    """The SESSION LOAD pass compares each FILE to the ceiling its own repo
    declared, and not only each SECTION to the review threshold
    (practice: control-asserts-which-failure).

    THE INCIDENT (2026-09-22). Three mechanisms each looked like they covered
    this and none did. The pass measured `## ` sections against
    `section_review_tokens` and never opened
    `tools/session_load_budgets.json`; `precedent_check.py`'s
    session-load-budget check did exactly the right comparison and SKIPPED in
    any repo without `practices/session-load-budget.md`; and
    `session_load_trend.py` reported it correctly and only when asked. So
    precedent-individual's AGENTS.md sat at 2,276 tokens against a declared
    1,800 -- 29% over -- with every check green.

    THE DISCRIMINATING CASE is the first one below, and it is what makes this
    a control rather than a demonstration: the overage SPREAD THIN. The real
    file's largest section was 990 tokens against a 2,500 threshold, so the
    section signal was not merely quiet, it was correct -- there was nothing
    section-sized to report. A fixture whose overage sits in one fat section
    would pass on the old code too, and prove nothing.

    The fixture owns its own tree (fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import build_views as bv

    PARA = ('Some ordinary instructions prose that a session reads before it '
            'does any work at all, and which nobody would call remarkable. ')

    def repo(sections, para_repeats, ceiling, registry=True):
        d = pathlib.Path(tempfile.mkdtemp())
        body = PARA * para_repeats
        (d / 'AGENTS.md').write_text(
            '# fixture\n\n' + ''.join(f'## Section {i}\n\n{body}\n\n'
                                     for i in range(1, sections + 1)),
            encoding='utf-8')
        if registry:
            (d / 'tools').mkdir()
            (d / 'tools' / 'session_load_budgets.json').write_text(
                json.dumps({'surfaces': {'AGENTS.md': {'ceiling': ceiling}}}),
                encoding='utf-8')
        return d

    def run(d):
        try:
            rows, msgs = vdc._session_load(d)
            return (sum(n for _, _, n in rows),
                    max([n for _, _, n in rows] or [0]),
                    [m for m in msgs if m.startswith('OVER CEILING')])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    cases = []

    total, largest, hits = run(repo(5, 40, 1800))
    cases.append((
        'THE DISCRIMINATING CASE: a file over its ceiling with the overage '
        'spread across sections, none of them section-sized, is reported',
        hits and largest < vdc._SECTION_FLAG_TOKENS and total > 1800,
        f'total={total} largest={largest} flag={vdc._SECTION_FLAG_TOKENS} '
        f'hits={hits!r}'))
    cases.append(('and the finding names the measurement, the ceiling and the '
                  'registry it came from',
                  hits and 'AGENTS.md' in hits[0]
                  and f'{total:,}' in hits[0] and '1,800' in hits[0]
                  and 'session_load_budgets.json' in hits[0], repr(hits)))
    cases.append(('and it says the remedy is the reduction pass, never a '
                  'raise -- session-load-budget\'s own line',
                  hits and 'NEVER raise the ceiling' in hits[0]
                  and 'reduction-pass' in hits[0], repr(hits)))

    total, _largest, hits = run(repo(5, 40, 20000))
    cases.append(('a file INSIDE its declared ceiling raises nothing, however '
                  'many sections it has', hits == [],
                  f'total={total} hits={hits!r}'))

    # A TARGET below the ceiling (practice: very-deep-check, Morgan
    # 2026-10-01): over it asks for a reduction pass, under it says nothing.
    def targeted(target):
        d = repo(5, 40, 20000)
        (d / 'tools' / 'session_load_budgets.json').write_text(
            json.dumps({'surfaces': {'AGENTS.md': {'ceiling': 20000,
                                                   'target': target}}}),
            encoding='utf-8')
        try:
            _rows, msgs = vdc._session_load(d)
            return [m for m in msgs if m.startswith('OVER TARGET')]
        finally:
            shutil.rmtree(d, ignore_errors=True)
    hits = targeted(1800)
    cases.append(('a file inside its ceiling but over its declared TARGET is '
                  'reported, and the finding asks for the practice-by-practice '
                  'review', hits and 'practice-by-practice' in hits[0]
                  and '1,800' in hits[0], repr(hits)))
    hits = targeted(20000)
    cases.append(('a file under its target raises no target finding',
                  hits == [], repr(hits)))

    total, _largest, hits = run(repo(5, 40, 1800, registry=False))
    cases.append(('a repo that declares NO ceiling is not tested against an '
                  'invented one', hits == [], f'total={total} hits={hits!r}'))

    # The ceiling signal must not have swallowed the section signal it was
    # added beside: both questions, both answers, in the same run.
    d = repo(1, 900, 20000)
    total, largest, hits = None, None, None
    try:
        rows, msgs = vdc._session_load(d)
        largest = max(n for _, _, n in rows)
        section_hits = [m for m in msgs if m.startswith('REVIEW')]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    cases.append(('the section signal it was added ALONGSIDE still fires on a '
                  'fat section inside its ceiling',
                  largest >= vdc._SECTION_FLAG_TOKENS and section_hits != [],
                  f'largest={largest} hits={section_hits!r}'))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a file over the ceiling its own repo declared is reported by the '
          f'SESSION LOAD pass ({len(cases)} stated cases, the spread-thin '
          f'overage being the discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_gotcha_currency_signals_fire():
    """tools/very_deep_check.py's gotcha-currency pass actually fires, and
    fires on the right entry (practice: control-asserts-which-failure).

    WHY A CONTROL RATHER THAN A RE-READING. The pass exists to catch an entry
    that still READS as live while the tree renamed or deleted the remedy it
    names. On the day it was written every one of its strong signals scored
    zero against this repository -- which is the good outcome and also means
    nothing had ever proved the signals work. A check that has only ever
    reported "none" is indistinguishable from one that cannot report anything
    at all, and this file already carries three entries of that exact shape.

    So this builds a fixture section carrying one entry per signal and asserts
    the SPECIFIC message each produces, not merely that something was
    reported. The fifth case is the discriminating one: a clean, dated entry
    naming a file that is present must raise nothing, or the pass is an alarm
    rather than a signal and its output would be ignored within a week.

    The fixture owns its own tree (fixture-owns-its-state): its own AGENTS.md
    and its own tools/ directory, so the result does not depend on what this
    repository happens to contain today."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc

    cases = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'tools').mkdir()
        (d / 'tools' / 'real.py').write_text(
            'def check_that_exists():\n    pass\n', encoding='utf-8')
        (d / 'AGENTS.md').write_text(
            '# fixture\n\n## Build-environment gotchas -- do NOT rediscover '
            'these\n\n'
            '- **A remedy that is gone.** Measured 2026-09-10. Run\n'
            '  [tools/deleted_tool.py](tools/deleted_tool.py) to repair it.\n\n'
            '- **A stale entry nobody has re-measured.** Measured 2019-01-02,\n'
            '  and the fix is `tools/real.py`.\n\n'
            '- **A slug that does not exist.** 2026-09-10: run\n'
            '  `python3 tools/precedent_check.py --only no-such-check-slug`.\n\n'
            '- **A fixture that was renamed.** 2026-09-10, held by\n'
            '  `check_that_is_gone`.\n\n'
            '- **A clean live entry.** 2026-09-10, and `tools/real.py` is\n'
            '  still there, held by `check_that_exists`.\n\n'
            '## Next\n', encoding='utf-8')

        rows, msgs = vdc._gotchas_currency(d)
        out = '\n'.join(msgs)

        for label, want in (
                ('a named remedy missing from the tree is reported by path',
                 'tools/deleted_tool.py'),
                ('an entry whose newest date is past the threshold is named '
                 'with that date',
                 'nothing re-measured since 2019-01-02'),
                ('a --only slug precedent_check.py does not answer to is '
                 'reported',
                 'no-such-check-slug'),
                ('a named fixture that no longer exists is reported',
                 'check_that_is_gone')):
            cases.append((label, want in out, failure_detail(out, 600)))

        clean = [r for r in rows if 'clean live entry' in r[2].lower()]
        cases.append(('THE DISCRIMINATING CASE: a dated entry naming a file '
                      'that is present raises nothing',
                      bool(clean) and not clean[0][3],
                      repr(clean[:1])))
        cases.append(('every entry is costed, so a reduction pass can be '
                      'ordered by what it would save',
                      bool(rows) and all(isinstance(r[0], int) and r[0] > 0
                                         for r in rows),
                      repr([r[0] for r in rows])))
        cases.append(('it proposes and never edits -- the fixture AGENTS.md '
                      'is byte-identical afterwards',
                      (d / 'AGENTS.md').read_text(encoding='utf-8').endswith(
                          '## Next\n'),
                      'fixture AGENTS.md was modified'))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the gotcha-currency pass fires on each signal and stays silent on '
          f'a clean entry ({len(cases)} stated cases, the clean entry being '
          f'the discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_planted_sweep_runs_only_in_a_named_whole_suite_run():
    """check_precedent_check_fires, every planted case, runs only in a
    whole-suite run asked for by name: the nightly and by-hand GitHub runs,
    --all (the very deep check), a ledger recording. A scoped run -- the
    pull request into main, the push after a Produce, a Debut, a landing's
    run -- leaves it out, even when the change reaches most of the suite.

    WHY. Morgan, 2026-10-29 (strength: decided): "let's NO LONGER RUN the
    full 519 second test of everything on main ... it should run when I do
    a 'very deep test'; and also ... in the nightly tests". It read files
    nearly every commit touches, so every scoped run picked it."""
    cases = []
    for env, every, want in (
            ({}, False, False),
            ({'PRECEDENT_HARNESS_FULL': ''}, False, False),
            ({'PRECEDENT_HARNESS_FULL': '0'}, False, False),
            ({'PRECEDENT_HARNESS_FULL': '1'}, False, True),
            ({'HARNESS_REACH_RECORD': '/tmp/x'}, False, True),
            ({}, True, True)):
        got = _planted_sweep_runs(every, env)
        cases.append((f'env={env} --all={every}: planted sweep runs={want}',
                      got == want, f'got {got}'))
    import inspect
    src = inspect.getsource(run_as_ci)
    cases.append(('run_as_ci drops the planted shard and the name when the sweep '
                  'is not asked for',
                  'if not _planted_sweep_runs(every_case):' in src
                  and "!= _PLANTED_SUITE" in src
                  and 'selected - {_PLANTED_SUITE}' in src, ''))
    wf = (ROOT / '.github' / 'workflows' / 'deep-check.yml').read_text(encoding='utf-8')
    cases.append(("the nightly and by-hand GitHub runs still ask for the whole suite",
                  "PRECEDENT_HARNESS_FULL: ${{ (github.event_name == 'schedule' || "
                  "github.event_name == 'workflow_dispatch') && '1' || '' }}" in wf
                  and "cron: '17 7 * * *'" in wf, ''))
    vdc = (ROOT / 'tools' / 'very_deep_check.py').read_text(encoding='utf-8')
    cases.append(('the very deep check still runs verify_harness --all',
                  'verify_harness.py --all' in vdc, ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the planted-case sweep runs only in a whole-suite run asked for by '
          f'name ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_very_deep_check_reads_a_worktree_and_runs_the_suite_last():
    """Two faults the 2026-10-17 very deep check paid for in its own run.

    A linked worktree is its own checkout: the branch scan and the
    live-session sweep asked whether `.git` is a directory, which in a
    worktree it is not, and skipped both for every helper working in one.
    A subdirectory of a checkout (a repo-local source) and a plain folder
    must still read as not their own.

    And --with-harness runs after the declared sources' freshness gate, not
    before it: a run spent 27 minutes on the suite and was then refused in
    seconds for a stale source (practice: gates-fail-fast). That half reads
    main()'s own order, since running the tool end to end here would cost
    the suite it is about."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git
    cases = []
    with tempfile.TemporaryDirectory() as td:
        W = pathlib.Path(td)
        repo = W / 'repo'
        repo.mkdir()
        _git(repo, 'init', '-q', '-b', 'main')
        _git(repo, 'config', 'user.email', 'harness@example.com')
        _git(repo, 'config', 'user.name', 'Harness')
        (repo / 'local').mkdir()
        (repo / 'local' / 'f.txt').write_text('x\n')
        _git(repo, 'add', '-A'); _git(repo, 'commit', '-qm', 'one')
        _git(repo, 'worktree', 'add', '-q', str(W / 'wt'), '-b', 'side')
        plain = W / 'plain'
        plain.mkdir()
        cases.append(('a clone is its own checkout', vdc._own_checkout(repo)))
        cases.append(('a linked worktree is its own checkout',
                      vdc._own_checkout(W / 'wt')))
        cases.append(('a folder inside a checkout is not',
                      not vdc._own_checkout(repo / 'local')))
        cases.append(('a plain folder is not', not vdc._own_checkout(plain)))
        cases.append(('the live-session sweep reads a worktree',
                      vdc.recent_activity(W / 'wt', 14) is not None))
    src = (ROOT / 'tools' / 'very_deep_check.py').read_text(encoding='utf-8')
    body = src[src.index('def main():'):]
    gate = body.find('not provably current')
    late = body.find('if with_harness:\n        _planted_section()')
    cases.append(('--with-harness runs after the source freshness gate',
                  0 <= gate < late))
    failed = [n for n, ok in cases if not ok]
    check(f'very deep check reads a worktree and runs the suite last '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_very_deep_check_registers_its_own_records():
    """The very deep check lists the record files it writes in the checked
    repo's generated-files registry, once each, and only when they exist.

    2026-10-17: in all three practice sets, committing the run record the
    tool asks for failed generated-files-registered, because a set's
    registry lists only its views and cannot list a file that does not
    exist yet."""
    import tempfile
    import very_deep_check as vdc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'tools').mkdir()
        reg = repo / 'tools' / 'generated_files.json'
        reg.write_text('{"files": [{"path": "MAP.md"}]}\n', encoding='utf-8')
        cases.append(('nothing is listed before the files exist',
                      vdc.register_run_outputs(repo) == []))
        (repo / 'record').mkdir()
        for e in vdc.RUN_OUTPUT_ENTRIES:
            (repo / e['path']).write_text('x\n', encoding='utf-8')
        added = vdc.register_run_outputs(repo)
        paths = [e.get('path') for e in json.loads(reg.read_text())['files']]
        cases.append(('both record files are listed once they exist, and the '
                      'set\'s own entry is kept',
                      sorted(added) == sorted(e['path'] for e in vdc.RUN_OUTPUT_ENTRIES)
                      and paths[0] == 'MAP.md' and len(paths) == 3))
        cases.append(('a second run adds nothing',
                      vdc.register_run_outputs(repo) == []))
        bare = repo / 'bare'
        (bare / 'record').mkdir(parents=True)
        cases.append(('a repo with no registry is left alone',
                      vdc.register_run_outputs(bare) == []
                      and not (bare / 'tools').exists()))
    failed = [n for n, ok in cases if not ok]
    check(f'very deep check registers its own record files ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_freshness_gate_fires():
    """The very deep check's freshness gate, as stated cases against
    throwaway repos (practice: very-deep-check).

    WHY AS FIXTURES RATHER THAN AGAINST THIS TREE. A gate that refuses a
    stale checkout is invisible when the checkout is current: running it
    here proves only that this clone happens to be up to date, which is a
    fact about the clone. The states that matter -- behind, diverged, dirty,
    branch-never-pushed -- have to be built. Both halves are asserted: that
    it refuses what it should, and that it does NOT refuse what it
    shouldn't, since a gate that fires on correct work is worse than none.

    The freshen half carries negative controls deliberately. Fast-forwarding
    a diverged branch deletes commits nobody asked it to delete, and a dirty
    tree left half-merged is worse than a stale one left alone -- so those
    two are asserted to change nothing, not merely to warn."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        upstream, work = tmp / 'upstream', tmp / 'work'
        upstream.mkdir()
        _git(upstream, 'init', '-q', '-b', 'main')
        _git(upstream, 'config', 'user.email', 'harness@example.com')
        _git(upstream, 'config', 'user.name', 'Harness')
        (upstream / 'f.txt').write_text('one\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'one')
        subprocess.run(['git', 'clone', '-q', f'file://{upstream}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')

        results = []
        results.append(('current clone passes',
                        vdc.freshness(work)['status'] == 'current'))

        # A repo with no origin at all is not stale -- there is nothing to be
        # behind. Refusing it would fail every fixture repo pass 1 builds.
        solo = tmp / 'solo'; solo.mkdir()
        _git(solo, 'init', '-q', '-b', 'main')
        _git(solo, 'config', 'user.email', 'harness@example.com')
        _git(solo, 'config', 'user.name', 'Harness')
        (solo / 'f.txt').write_text('x\n')
        _git(solo, 'add', '-A'); _git(solo, 'commit', '-qm', 'x')
        results.append(('a repo with no origin is not reported stale',
                        vdc.freshness(solo)['status'] == 'no-remote'))

        # Not a git checkout at all: a repo-local source inside the parent.
        plain = tmp / 'plain'; plain.mkdir()
        results.append(('a non-checkout directory is skipped, not failed',
                        vdc.freshness(plain)['status'] == 'not-a-checkout'))

        # Behind.
        (upstream / 'f.txt').write_text('one\ntwo\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'two')
        v = vdc.freshness(work)
        results.append(('a clone behind origin is refused',
                        v['status'] == 'behind' and v['behind'] == 1))

        # --freshen on a DIRTY tree must decline and change nothing.
        (work / 'scratch.txt').write_text('uncommitted\n')
        before = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        v_dirty = vdc.freshen(work, vdc.freshness(work, fetch=False))
        after = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        results.append(('--freshen declines a dirty tree and moves nothing',
                        v_dirty['status'] == 'behind' and before == after))
        (work / 'scratch.txt').unlink()

        # --freshen on a clean tree that is behind must actually advance it.
        v_clean = vdc.freshen(work, vdc.freshness(work, fetch=False))
        results.append(('--freshen fast-forwards a clean tree that is behind',
                        v_clean['status'] == 'current'))

        # Diverged: --freshen must refuse, and the local commit must survive.
        (upstream / 'f.txt').write_text('one\ntwo\nthree\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'three')
        (work / 'local.txt').write_text('mine\n')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'local only')
        v = vdc.freshness(work)
        mine = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        v2 = vdc.freshen(work, v)
        results.append(('a diverged clone is refused, and --freshen leaves its '
                        'local commit alone',
                        v['status'] == 'diverged' and v2['status'] == 'diverged'
                        and _git(work, 'rev-parse', 'HEAD').stdout.strip() == mine
                        and (work / 'local.txt').exists()))

        # A branch that exists only locally: the network is fine, so the
        # verdict must say so rather than blaming the fetch.
        _git(work, 'checkout', '-q', '-b', 'never-pushed')
        v = vdc.freshness(work)
        results.append(('a local-only branch reports branch-not-on-origin, '
                        'not a fetch failure',
                        v['status'] == 'branch-not-on-origin'))
        # ...and its remedy is to bring the base in, not to push: the
        # branch is behind origin/main here, and pushing it would only buy
        # a second refusal (2026-10-17).
        results.append(('a local-only branch behind the base is told to '
                        'bring the base in, never to push',
                        'merge origin/main' in (v['remedy'] or '')
                        and 'push -u' not in (v['remedy'] or '')))

        # Detached, as a cloud session hands an attached repo over: at
        # origin's base it is current, with nothing unpushed; behind it, it
        # is refused (2026-10-17).
        _git(work, 'fetch', '-q', 'origin')
        _git(work, 'checkout', '-q', '--detach', 'origin/main')
        v = vdc.freshness(work)
        results.append(('a detached HEAD at origin/main reads clean, with '
                        'nothing unpushed',
                        v['status'] in vdc.FRESHNESS_CLEAN and v['ahead'] == 0))
        _git(work, 'checkout', '-q', '--detach', 'origin/main~1')
        v = vdc.freshness(work)
        results.append(('a detached HEAD behind origin/main is refused',
                        v['status'] == 'detached'))

        # A repo whose declared base is `staging`, with staging AHEAD of
        # main: the practice says to read main from a branch cut from
        # origin/main, and until 2026-10-31 the gate refused exactly that
        # branch because it does not contain origin/staging. The control
        # beside it, a branch cut behind origin/main, must still be refused.
        _git(upstream, 'checkout', '-q', '-b', 'staging')
        (upstream / 'precedent.json').write_text('{"base_branch": "staging"}\n')
        (upstream / 's.txt').write_text('landed, not live\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'staging only')
        _git(upstream, 'checkout', '-q', 'main')
        _git(work, 'fetch', '-q', 'origin', 'staging:refs/remotes/origin/staging')
        _git(work, 'checkout', '-q', '-b', 'read-main', 'origin/main')
        (work / 'precedent.json').write_text('{"base_branch": "staging"}\n')
        v = vdc.freshness(work)
        results.append(('a branch cut from origin/main reads clean where the '
                        'base is a staging branch ahead of main',
                        v['status'] in vdc.FRESHNESS_CLEAN))
        _git(work, 'checkout', '-q', '-b', 'read-old-main', 'origin/main~1')
        v = vdc.freshness(work)
        results.append(('a branch cut behind origin/main is still refused '
                        'where the base is staging',
                        v['status'] == 'branch-not-on-origin'))
        (work / 'precedent.json').unlink()

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check refuses a stale repo ({len(results)} stated '
              f'cases: a current clone, a remoteless repo, a non-checkout, a '
              f'behind clone, --freshen against dirty and clean trees, a '
              f'diverged clone whose commit must survive, a local-only '
              f'branch, and a branch cut from main where the base is staging)',
              not failed,
              '; '.join(failed) if failed else '')


def check_no_tool_defines_a_function_twice():
    """2026-10-31: a second top-level `_stamp` in very_deep_check.py, added
    by a change that never ran the branch sweep's tests, silently replaced
    the first; every branch row lost its date and two very deep check
    tests failed only in the whole suite. Python keeps the last definition
    without a word, so this reads every engine file's top level for a name
    defined twice. The control plants a file that does it."""
    import ast
    import collections
    import tempfile

    # The AST decides, and a line scan decides which files it has to read
    # (2026-10-31: parsing all of tools/*.py was 5-14 s, nearly all of it
    # verify_harness.py; the scan reads them all in a tenth of a second).
    # A top-level def or class always starts at column 0, so the scan sees
    # every name tree.body holds, as often or more often (more when a
    # string carries a column-0 `def`, as two files' fixtures do): a file
    # where the scan sees no name twice cannot have one the AST sees twice.
    # Measured the same day, the scan's names equalled the AST's in 141 of
    # the 143 files and were a superset in the other two.
    scan = re.compile(r'^(?:async[ \t]+)?(?:def|class)[ \t]+(\w+)', re.M)

    def twice(path):
        text = path.read_text(encoding='utf-8')
        if all(v < 2 for v in collections.Counter(scan.findall(text)).values()):
            return []
        tree = ast.parse(text)
        names = collections.Counter(
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        return sorted(k for k, v in names.items() if v > 1)

    found = {}
    for path in sorted((ROOT / 'tools').glob('*.py')):
        try:
            dup = twice(path)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        if dup:
            found[path.name] = dup
    with tempfile.TemporaryDirectory() as td:
        planted = pathlib.Path(td) / 'planted.py'
        planted.write_text('def a():\n    pass\n\n\ndef a():\n    pass\n',
                           encoding='utf-8')
        control = twice(planted) == ['a']
        # A second `def a` at column 0 inside a string is no definition:
        # the scan flags the file and the AST clears it.
        quoted = pathlib.Path(td) / 'quoted.py'
        quoted.write_text('def a():\n    pass\n\n\nTEXT = """\ndef a():\n'
                          '    pass\n"""\n', encoding='utf-8')
        control_quoted = twice(quoted) == []
    check('no engine tool defines the same top-level name twice (a planted '
          'file that does is caught)',
          not found and control and control_quoted,
          f'defined twice: {found}' if found else
          'the planted file was not caught' if not control else
          'a `def` inside a string was counted as a definition')


def check_unmerged_branch_verdicts():
    """The unmerged half of the very deep check's branch sweep (practice:
    very-deep-check).

    The case that carries this check is the rebased branch. `merge-base
    --is-ancestor` reads commit identity, so a branch whose every patch was
    replayed onto the integration branch stays "unmerged" forever while
    carrying no work at all. Reporting that as unlanded is not a cosmetic
    error: it is the finding that teaches a reader to wave the whole list
    through, at which point the genuinely-unlanded branch beside it goes
    with them. So both are asserted here, side by side in one fixture --
    one branch that really carries work, one that only appears to."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A branch whose one commit is genuinely not on main.
        _git(up, 'checkout', '-q', '-b', 'real-work')
        (up / 'feature.txt').write_text('unlanded\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'unlanded work')

        # A branch whose commit is replayed onto main -- a different commit
        # hash, an identical patch. This is the squash/rebase shape.
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'checkout', '-q', '-b', 'already-landed')
        (up / 'landed.txt').write_text('landed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'landed work')
        patch = _git(up, 'format-patch', '-1', '--stdout').stdout
        _git(up, 'checkout', '-q', 'main')
        (tmp / 'p.patch').write_text(patch)
        _git(up, 'am', '-q', str(tmp / 'p.patch'))
        # Reword the replayed commit. `git am` preserves the author and the
        # author date, so with the same message, tree and parent it produces
        # a BYTE-IDENTICAL commit whenever both commits land in the same
        # second -- and then the branch really is an ancestor of main and
        # the fixture silently tests nothing. That made this case pass or
        # fail on the clock (observed both ways within one minute). A
        # reworded commit is also the truer shape: a squash-merge rewrites
        # the message.
        _git(up, 'commit', '-q', '--amend', '-m', 'landed work (squashed)')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        scan = vdc.scan_branches(work, 'main')
        rows = {r['name']: r for r in (scan or {}).get('unmerged', [])}

        results = [
            ('both branches are reported as not merged',
             set(rows) == {'real-work', 'already-landed'}),
            ('a branch carrying genuinely unlanded work is counted as such',
             rows.get('real-work', {}).get('unique') == 1
             and 'CARRIES' in (rows.get('real-work', {}).get('verdict') or '')),
            ('a rebased branch is NOT reported as unlanded work',
             rows.get('already-landed', {}).get('unique') == 0
             and 'ALREADY LANDED' in (rows.get('already-landed', {}).get('verdict') or '')),
            ('every unmerged branch carries a verdict, never none',
             all(r.get('verdict') for r in rows.values())),
            ('each row carries the evidence the verdict rests on',
             all(r.get('ahead') is not None and r.get('last')
                 for r in rows.values())),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check tells unlanded work from a rebased branch '
              f'({len(results)} stated cases, the rebased one being the '
              f'controlling case)',
              not failed, ('; '.join(failed) + ' -- rows: ' + repr(rows)[:600])
              if failed else '')


def check_moved_claims_says_when_it_could_not_read_the_tree():
    """`_moved_claims` returns UNKNOWN, not "clean", when its own read fails
    (practices: checks-plant-their-state, control-asserts-which-failure).

    THE SHAPE, which is the endgame rehearsal's defect in a second function.
    `_moved_claims` builds a set of every tracked basename and uses it to
    SUPPRESS rows: a target found among them is a real file named without
    its path, not a broken claim. The set came from `git ls-files` with the
    failure coerced to an empty set -- so a failed read did not merely lose
    information, it switched the suppression off, and every
    under-qualified name became a row asserting no such file exists.
    Findings manufactured out of a read that did not happen, which is
    exactly how a `git ls-files` failure in `endgame_merge` made every file
    on the integration branch look silently dropped.

    Both halves. The loud one: the read fails, the answer is None and the
    caller prints CANNOT TELL rather than counting a clean repository. The
    quiet one: against a real tree it still returns a list, because a guard
    that has learned to answer UNKNOWN to everything is not a guard."""
    import tempfile
    import very_deep_check as vdc

    # A scratch repository with two tracked files, never this tree: the quiet
    # half asks only that a readable tree answers with a list, and reading
    # this whole repository for it was most of this check's time.
    td = tempfile.TemporaryDirectory(prefix='moved-claims-')
    root = pathlib.Path(td.name)
    (root / 'docs').mkdir()
    (root / 'README.md').write_text('# fixture\n\nSee docs/notes.md.\n', encoding='utf-8')
    (root / 'docs' / 'notes.md').write_text('Moved to docs/gone.md.\n', encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(root)], capture_output=True)
    subprocess.run(['git', '-C', str(root), 'add', '-A'], capture_output=True)

    real = vdc._moved_claims(root)

    original = vdc._run_git

    def fail_ls_files(repo, *args, _o=original, **kw):
        if args and args[0] == 'ls-files':
            return (128, '', 'fatal: simulated -- ls-files unreadable')
        return _o(repo, *args, **kw)

    vdc._run_git = fail_ls_files
    try:
        unreadable = vdc._moved_claims(root)
    finally:
        vdc._run_git = original
        td.cleanup()

    results = [
        ('PLANTED, `git ls-files` fails: the answer is UNKNOWN (None)',
         unreadable is None),
        ('...and specifically NOT an empty list, which reads as clean',
         unreadable != []),
        ('the quiet half: a readable tree still answers with a list',
         isinstance(real, list)),
    ]
    failed = [name for name, ok in results if not ok]
    return (not failed,
            (f"{'; '.join(failed)} -- unreadable={unreadable!r}, "
             f"real={type(real).__name__}") if failed else '')

def check_endgame_merge_finds_the_silent_drop():
    """The endgame-merge rehearsal (practice: very-deep-check, pass 4).

    THE CASE THAT CARRIES THIS CHECK is the file that disappears without a
    conflict. A reverted merge on the base branch splits the integration
    branch's files into two classes, and only one of them is visible: a file
    touched again since the merge base conflicts and stops the merge, while
    a file untouched since simply does not arrive -- no conflict, no
    message. The 2026-09-07 rehearsal that missed this checked two files,
    found both present, and concluded the trap did not fire; both happened
    to be in the visible class.

    So a non-zero finding count is NOT what is asserted here. The fixture
    plants one file of each class and this check asserts WHICH path lands in
    WHICH set by name -- a rehearsal that reported the conflicting file and
    stayed silent about the dropped one would satisfy any count-based
    assertion while reproducing the exact miss.

    The clean case is asserted beside it, from the same fixture with the
    revert undone: a check that cannot come back clean is one that will be
    ignored the first time it is inconvenient."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # The integration branch, with the two classes of file on it.
        _git(up, 'checkout', '-q', '-b', 'beta')
        (up / 'keep.txt').write_text('one\n')
        (up / 'drop.txt').write_text('one\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'beta work')

        # The accident: beta merged into main, then reverted. The revert
        # undoes the FILES and leaves the COMMITS in main's log, which is
        # what makes git treat them as already merged afterwards.
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '--no-ff', '-q', '-m', 'accidental merge', 'beta')
        merge_sha = _git(up, 'rev-parse', 'HEAD').stdout.strip()
        _git(up, 'revert', '-m', '1', '--no-edit', merge_sha)

        # Beta carries on: one of the two files is touched again (so it will
        # conflict), one is not (so it will vanish), plus new work that
        # never existed on main at all.
        _git(up, 'checkout', '-q', 'beta')
        (up / 'keep.txt').write_text('two\n')
        (up / 'later.txt').write_text('new\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'more beta work')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)

        # THE GIT IDENTITY IS PLANTED, BOTH WAYS, and that is the point of
        # this block. This check used to read whatever identity the machine
        # happened to have: a session container has a global one, a CI
        # runner does not, and `git merge` REFUSES without it -- so the
        # rehearsal did nothing, the index still held only the base branch,
        # and every file on beta came back named as silently dropped. Green
        # here, red in continuous integration for five runs, with the code
        # identical in both (2026-09-22). Neither arm below reads the real
        # machine. practice: checks-plant-their-state.
        def _endgame(identity, **kw):
            saved = {k: os.environ.get(k)
                     for k in ('GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM')}
            if not identity:
                os.environ['GIT_CONFIG_GLOBAL'] = empty_gitconfig()
                os.environ['GIT_CONFIG_SYSTEM'] = empty_gitconfig()
            try:
                return vdc.endgame_merge(work, target='beta', base='main',
                                         **kw) or {}
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

        r = _endgame(identity=True)
        dropped, conflicts = set(r.get('dropped') or []), set(r.get('conflicts') or [])
        bare = _endgame(identity=False)
        bare_dropped = set(bare.get('dropped') or [])
        bare_conflicts = set(bare.get('conflicts') or [])

        # Same fixture, revert undone: the merge must come back clean.
        _git(up, 'revert', '--no-edit', 'HEAD')   # revert the revert
        _git(work, 'fetch', '-q', 'origin')
        clean = _endgame(identity=True)

        # AND A MERGE THAT GENUINELY CANNOT RUN MUST SAY SO. Planted with a
        # global config the rehearsal cannot satisfy -- signature
        # verification on, against unsigned fixture commits -- which makes
        # `git merge` exit 128 having done nothing, exactly as the missing
        # identity did. Without this case the error path is never executed
        # and the old behaviour (report it as every file dropped) could come
        # back with every check still green.
        blocked_cfg = tmp / 'blocked.gitconfig'
        blocked_cfg.write_text('[merge]\n\tverifySignatures = true\n',
                               encoding='utf-8')
        saved_cfg = os.environ.get('GIT_CONFIG_GLOBAL')
        os.environ['GIT_CONFIG_GLOBAL'] = str(blocked_cfg)
        try:
            blocked = vdc.endgame_merge(work, target='beta', base='main') or {}
        finally:
            if saved_cfg is None:
                os.environ.pop('GIT_CONFIG_GLOBAL', None)
            else:
                os.environ['GIT_CONFIG_GLOBAL'] = saved_cfg

        worktrees = _git(work, 'worktree', 'list').stdout.strip().splitlines()

        # AND A RESULT THAT CANNOT BE READ MUST SAY SO TOO. The merge runs
        # here; what fails is the pair of reads that learn what it did, and
        # each of them used to coerce its own failure to an empty set. An
        # `ls-files` that fails leaves `present` holding only the conflicts,
        # so `expected - present` names almost every file on the integration
        # branch -- the identical fabricated drop list the refusal path used
        # to produce, reached by a different route. Planted by failing each
        # read in turn, because the two are separate `if rc == 0` branches
        # and one being guarded says nothing about the other.
        # practice: checks-plant-their-state.
        unreadable = {}
        for failing in ('diff', 'ls-files'):
            original_run = vdc._run_git

            def fail_one_read(repo, *args, _f=failing, _o=original_run, **kw):
                if args and args[0] == _f:
                    return (128, '', f'fatal: simulated -- {_f} unreadable')
                return _o(repo, *args, **kw)

            vdc._run_git = fail_one_read
            try:
                unreadable[failing] = _endgame(identity=True)
            finally:
                vdc._run_git = original_run

        results = [
            ('the file untouched since the merge base is named as dropped',
             'drop.txt' in dropped),
            ('the file touched since the merge base is a CONFLICT, not a drop',
             'keep.txt' in conflicts and 'keep.txt' not in dropped),
            ('work newer than the merge base arrives cleanly, in neither set',
             'later.txt' not in dropped and 'later.txt' not in conflicts),
            ('the run is reported as carrying findings',
             r.get('status') == 'findings'),
            ('undoing the revert makes the same merge come back clean',
             clean.get('status') == 'clean' and not clean.get('dropped')),
            ('the throwaway worktree is removed, whatever the outcome',
             len(worktrees) == 1),
            ('PLANTED, no global git identity: the same answer, not a merge '
             'that silently did nothing',
             bare_dropped == dropped and bare_conflicts == conflicts
             and bare.get('status') == r.get('status')),
            ('PLANTED, a merge git refuses outright: reported as error, '
             'never as findings',
             blocked.get('status') == 'error'),
            ('...and the note carries git\'s own words rather than a '
             'fabricated drop list',
             'signature' in (blocked.get('note') or '').lower()
             and not blocked.get('dropped')),
            ('PLANTED, the merge ran but `git diff` could not be read: '
             'error and no drop list, never a finding',
             unreadable['diff'].get('status') == 'error'
             and not unreadable['diff'].get('dropped')
             and 'UNKNOWN' in (unreadable['diff'].get('note') or '')),
            ('PLANTED, the merge ran but `git ls-files` could not be read: '
             'the same, since the two reads are guarded separately',
             unreadable['ls-files'].get('status') == 'error'
             and not unreadable['ls-files'].get('dropped')
             and 'UNKNOWN' in (unreadable['ls-files'].get('note') or '')),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the endgame-merge rehearsal names the silently-dropped path '
              f'({len(results)} stated cases; the drop/conflict split is the '
              f'controlling one)',
              not failed,
              (f"{'; '.join(failed)} -- dropped={sorted(dropped)}, "
               f"conflicts={sorted(conflicts)}") if failed else '')


def check_very_deep_check_never_offers_a_tier_branch_for_deletion():
    """The very deep check never offers staging, main, staging's old name or
    Promote's lock branch for deletion, merged or not.

    WHY. Morgan, 2026-09-28 (strength: decided): the sweep must never offer
    to delete a tier branch. Every Promote fast-forwards the lower tiers, so
    right after one the ancestor test calls them and precedent-beta-v01
    "merged" -- and the branch sweep protected only the declared base and
    the default branch, so they came back as safe to delete, each with a
    one-click link. staging itself had been deleted from
    a merge page two days earlier.

    Discriminating: a merged feature branch in the same fixture must still
    be listed WITH its link, or a sweep that listed nothing would pass."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git
    tiers = ['main', 'staging', 'precedent-beta-v01', 'precedent-promote-lock']
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        # Right after a Promote: every tier at one commit, so the ancestor
        # test calls every one of them "merged" into every other.
        for b in tiers[1:]:
            _git(up, 'branch', b)
        _git(up, 'branch', 'claude/finished-work')
        (up / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'staging'}) + '\n')
        _git(up, 'checkout', '-q', 'staging')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'declare staging')
        _git(up, 'checkout', '-q', 'main')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*')
        vdc._NEVER_DELETABLE_CACHE.clear()
        # Scanned from a checkout on main, so staging is not the
        # checked-out branch the old code happened to exclude.
        scan = vdc.scan_branches(work, exclude=('main',)) or {}
        listed = [r['name'] for k in ('merged', 'merged_elsewhere', 'unmerged')
                  for r in scan.get(k) or []]
        # A GitHub remote now, after the scan's own fetches, so a delete
        # link is minted at all.
        _git(work, 'config', 'remote.origin.url',
             'https://github.com/example/fixture.git')
        vdc._NEVER_DELETABLE_CACHE.clear()
        gh_url = {b: vdc._branch_url(work, b)
                  for b in tiers + ['claude/finished-work']}
        row = {'name': 'stag', 'last': None, 'age_days': None,
               'filter_shows_tier': vdc._tiers_shown_by_filter(work, 'stag')}
        warn = '\n'.join(vdc._delete_row_lines(row, str(work)))
        results = [
            ('no tier branch appears in any list of the sweep',
             not [b for b in tiers if b in listed]),
            ('a finished feature branch in the same fixture IS listed '
             '(discriminating: an empty sweep would pass the case above)',
             'claude/finished-work' in listed),
            ('no delete link is ever minted for a tier branch',
             all(gh_url[b] is None for b in tiers)),
            ('the feature branch still gets its delete link',
             bool(gh_url['claude/finished-work'])),
            ('a filter that would also show a tier row says so on the row',
             '`staging`' in warn and 'never delete' in warn),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check never offers a tier branch for deletion '
              f'({len(results)} stated cases)', not failed,
              '; '.join(failed) + f' -- listed {listed}')


def check_very_deep_check_skips_the_board_branches():
    """`coord` holds the lease board, the landing queue and the maintainer
    heartbeat; `result-cache` the shared result cache. Both are orphan
    histories that hold machinery, never work. Before 2026-10-31 the branch
    sweep listed `coord` as unmerged with "deepen and re-check", which no
    depth can settle, and the review page had no rule keeping it off.

    Discriminating cases: the board branches are in no list and get no
    delete link, while an ordinary orphan branch in the same fixture IS
    listed (an empty sweep would pass the first case), and on this full
    clone its verdict says the branch shares no history rather than
    telling the reader to deepen (practice: very-deep-check)."""
    import tempfile
    import very_deep_check as vdc
    import precedent_review_page as rp

    _git = fixture_git
    board = ['coord', 'result-cache']
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        for b in board + ['claude/stray-orphan']:
            _git(up, 'checkout', '-q', '--orphan', b)
            _git(up, 'rm', '-rq', '--cached', '.')
            (up / 'base.txt').unlink()
            (up / 'leases').mkdir(exist_ok=True)
            (up / 'leases' / 'x.json').write_text(f'{{"b": "{b}"}}\n')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', f'{b} record')
            _git(up, 'checkout', '-q', '-f', 'main')
            _git(up, 'clean', '-qfd')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*')
        vdc._NEVER_DELETABLE_CACHE.clear()
        scan = vdc.scan_branches(work, 'main') or {}
        rows = {r['name']: r for k in ('merged', 'merged_elsewhere', 'unmerged')
                for r in scan.get(k) or []}
        _git(work, 'config', 'remote.origin.url',
             'https://github.com/example/fixture.git')
        vdc._NEVER_DELETABLE_CACHE.clear()
        links = {b: vdc._branch_url(work, b) for b in board}
        page = [name for name, _d in rp.landed_branches(work)]
        stray = (rows.get('claude/stray-orphan') or {}).get('verdict') or ''
        results = [
            ('no board branch appears in any list of the sweep',
             not [b for b in board if b in rows]),
            ('no delete link is minted for a board branch',
             all(links[b] is None for b in board)),
            ('the review page offers no board branch',
             not [b for b in board if b in page]),
            ('an ordinary orphan branch in the same fixture IS listed',
             'claude/stray-orphan' in rows),
            ('...and on a full clone its verdict says it shares no history, '
             'not "deepen"',
             'shares no history' in stray and 'Deepen' not in stray),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check skips the board branches '
              f'({len(results)} stated cases)', not failed,
              '; '.join(failed) + f' -- listed {sorted(rows)}; stray: {stray}')


def check_very_deep_check_walks_every_tier_pair():
    """The drift scan and the merge rehearsal ask about every tier pair
    origin carries: main into staging, and the merge a Promote makes
    (staging into main).

    WHY. Until 2026-09-28 both asked about one pair only, the declared base
    against the default branch. Asserted by WHICH commit comes back for
    WHICH pair, so a scan that returned nothing everywhere fails."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'staging'}) + '\n')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        _git(up, 'branch', 'staging')
        (up / 'hotfix.txt').write_text('fixed on main\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'hotfix straight to main')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*')
        pairs = vdc.tier_pairs(work)
        d = vdc.base_branch_drift(work, 'staging', 'main') or {}
        subjects = [c['subject'] for c in d.get('commits') or []]
        e = vdc.endgame_merge(work, 'staging', 'main') or {}
        results = [
            ('main into staging is the one drift pair',
             pairs.get('drift') == [('staging', 'main')]),
            ('the rehearsal is the merge a Promote makes, staging into main',
             pairs.get('endgame') == [('staging', 'main')]),
            ('the fix pushed straight to main is found missing from staging',
             'hotfix straight to main' in subjects),
            ('the Promote merge is actually rehearsed, not skipped',
             e.get('status') in ('clean', 'findings')),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check walks every tier pair ({len(results)} '
              f'stated cases)', not failed,
              '; '.join(failed) + f' -- pairs {pairs}, drift {subjects}, '
              f'endgame {e.get("status")} {e.get("note")}')


def check_base_branch_drift_ignores_carried_work():
    """The base-branch drift scan (practice: very-deep-check, pass 4).

    THE CASE THAT CARRIES THIS CHECK is the change that was CARRIED rather
    than merged. Work reaches a long-lived integration branch by being
    rewritten into that branch's own shape at least as often as by being
    merged, so commit identity says "never arrived" about content that
    landed weeks ago. A scan that listed those would hand the person a list
    mostly made of work already here, and a list that is mostly noise is
    waved through whole -- which is the failure this section exists to
    prevent, not to cause.

    So a non-zero count is not what is asserted. The fixture plants one
    commit of each class on the base branch -- one whose patch also exists
    on the integration branch, one that does not -- and this check asserts
    WHICH subject comes back by name. It also asserts the two shapes that
    must never render as clean: a base branch with nothing new (clean), and
    a repo whose branch IS its base (None -- nothing can drift from
    itself, which is a skip, not a pass)."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A fix lands on main, and the same patch is carried onto the branch
        # as its own commit -- different sha, identical content.
        (up / 'fix.txt').write_text('fixed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'carried fix')
        _git(up, 'checkout', '-q', '-b', 'beta', 'HEAD~1')
        (up / 'fix.txt').write_text('fixed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'the same fix, carried')

        # And one that nobody ever brought across.
        _git(up, 'checkout', '-q', 'main')
        (up / 'stranded.txt').write_text('never carried\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'never carried across')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'fetch', '-q', 'origin', 'beta:refs/remotes/origin/beta')
        r = vdc.base_branch_drift(work, target='beta', base='main') or {}
        subjects = [c['subject'] for c in (r.get('commits') or [])]

        # Same fixture, with the stranded commit carried across too: the
        # scan must be able to come back clean, or it will be ignored.
        _git(up, 'checkout', '-q', 'beta')
        (up / 'stranded.txt').write_text('never carried\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'carried that one too')
        _git(up, 'checkout', '-q', 'main')
        _git(work, 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*')
        clean = vdc.base_branch_drift(work, target='beta', base='main') or {}

        same = vdc.base_branch_drift(work, target='main', base='main')

        results = [
            ('the commit nobody carried is listed by subject',
             'never carried across' in subjects),
            ('the commit whose patch was CARRIED across is not listed',
             'carried fix' not in subjects),
            ('the run is reported as carrying findings',
             r.get('status') == 'findings'),
            ('the listed row carries the file it touched',
             any('stranded.txt' in (c.get('files') or [])
                 for c in (r.get('commits') or []))),
            ('carrying the last one across makes the scan come back clean',
             clean.get('status') == 'clean' and not clean.get('commits')),
            ('a repo whose branch IS its base is a skip, not a clean pass',
             same is None),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the base-branch drift scan lists unlanded work and ignores '
              f'carried work ({len(results)} stated cases; the carried/'
              f'stranded split is the controlling one)',
              not failed,
              (f"{'; '.join(failed)} -- subjects={subjects}, "
               f"status={r.get('status')}") if failed else '')


def check_branch_scan_sees_every_branch():
    """The branch sweep must enumerate what ORIGIN has, not what this clone
    happened to fetch (practice: very-deep-check).

    THE CASE THAT CARRIES THIS CHECK is the single-branch clone, which is
    not an edge case: it is what the harness hands every remote session
    (AGENTS.md's add_repo entry), and the freshness gate above fetches only
    the ONE branch it compares. `scan_branches` reads `refs/remotes/origin`,
    so on such a clone it enumerated two refs on a repo with forty and
    reported "(none)" -- which reads as a clean sweep, not as a scan that
    never ran. That is the same empty-result-reads-as-pass failure AGENTS.md
    records for the `scope: 'tree'` checks, and it costs more here: the
    sweep IS pass 4's branch bullet, so a false all-clear silently ends the
    only step that would have found unlanded work.

    Both halves are asserted. The first is the fix: a narrow clone must
    still see every branch. The second is the negative control that keeps
    the fix honest -- when origin genuinely cannot be reached, the scan must
    say it could not tell, NOT fall back to the empty lists that started
    this. A repair that turns one silent wrong answer into another is not a
    repair."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up = tmp / 'up'; up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        for b in ('landed', 'open-one', 'open-two'):
            _git(up, 'checkout', '-q', '-b', b)
            (up / f'{b}.txt').write_text(b + '\n')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', b)
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', 'landed', '-m', 'merge landed')

        # Exactly what the harness produces: one branch, one refspec.
        narrow = tmp / 'narrow'
        subprocess.run(['git', 'clone', '-q', '--single-branch', '--branch',
                        'main', f'file://{up}', str(narrow)],
                       capture_output=True, text=True)
        refs_before = len([r for r in _git(
            narrow, 'for-each-ref', '--format=%(refname:short)',
            'refs/remotes/origin').stdout.splitlines() if r])

        scan = vdc.scan_branches(narrow, 'main') or {}
        merged = {r['name'] for r in (scan.get('merged') or [])}
        unmerged = {r['name'] for r in (scan.get('unmerged') or [])}

        results = [
            ('the fixture really is a narrow clone (else this proves nothing)',
             refs_before <= 2),
            ('a merged branch on origin is found even though the clone never '
             'fetched it', 'landed' in merged),
            ('both unmerged branches on origin are found',
             {'open-one', 'open-two'} <= unmerged),
            ('the scan reports itself complete when it reached origin',
             not scan.get('unfetched') and not scan.get('unreachable')),
        ]

        # NEGATIVE CONTROL: origin unreachable. Empty lists are now a lie, so
        # the scan must mark itself incomplete rather than report them bare.
        dark = tmp / 'dark'
        subprocess.run(['git', 'clone', '-q', '--single-branch', '--branch',
                        'main', f'file://{up}', str(dark)],
                       capture_output=True, text=True)
        _git(dark, 'remote', 'set-url', 'origin', 'file:///nonexistent/gone.git')
        d = vdc.scan_branches(dark, 'main') or {}
        results.append(
            ('an unreachable origin is reported as "cannot tell", never as an '
             'empty (clean) sweep',
             not d.get('merged') and not d.get('unmerged')
             and bool(d.get('unreachable'))))

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check\'s branch sweep sees every branch origin '
              f'has, not only what this clone fetched ({len(results)} stated '
              f'cases, the single-branch clone being the controlling case and '
              f'an unreachable origin the negative control)',
              not failed, '; '.join(failed) if failed else '')


def _vdc_drift_copy_set(src, src_name, dest, name):
    """Copy a set the generator wrote at `src` under the name `src_name` to
    `dest`, as the generator would have written it there under `name`.

    The generator writes its own destination path ({{DEST_PATH}}) and the
    set's name into its files, and nothing else differs between two runs:
    measured 2026-10-31, `diff -r` of two runs into different directories,
    and of two team sets with different names, differed only in those two
    strings and in __pycache__, which the drift check skips and this copy
    leaves out. So the copy is byte for byte what a fresh run writes, at
    about a hundredth of its cost (practice: slow-steps-report-and-cache).
    A `src` the generator never wrote is not copied, so `dest` stays absent,
    exactly as after a run that failed."""
    src, dest = pathlib.Path(src), pathlib.Path(dest)
    if not src.is_dir():
        return
    shutil.copytree(src, dest, symlinks=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    swaps = [(str(src).encode(), str(dest).encode())]
    if name != src_name:
        swaps.append((src_name.encode(), name.encode()))
    for p in dest.rglob('*'):
        if p.is_symlink() or not p.is_file():
            continue
        data = new = p.read_bytes()
        for a, b in swaps:
            new = new.replace(a, b)
        if new != data:
            p.write_bytes(new)


class _VdcDriftGeneratorMemo:
    """While open, very_deep_check's own call to the generator
    (bootstrap_source.bootstrap, run once per set by _bootstrap_drift_one)
    generates once per distinct input and hands every later call a copy
    (_vdc_drift_copy_set). The inputs are its arguments but the name, which
    the copy substitutes, and PRECEDENT_SEED_OFF_MAIN, so a call made
    without the harness's off-main allowance still runs the generator for
    real. Restores the real generator on close, whatever happened."""

    def __init__(self, vdc, where):
        self.bs, self.where, self.made = vdc.bootstrap_source, pathlib.Path(where), {}

    def __enter__(self):
        self.real = real = self.bs.bootstrap

        def memo(level, name, dest, **kw):
            key = (level, json.dumps(kw, sort_keys=True, default=str),
                   os.environ.get('PRECEDENT_SEED_OFF_MAIN'))
            if key not in self.made:
                src = self.where / f'reference-{len(self.made)}'
                real(level, name, src, **kw)
                self.made[key] = (src, name)
            src, src_name = self.made[key]
            _vdc_drift_copy_set(src, src_name, dest, name)
        self.bs.bootstrap = memo
        return self

    def __exit__(self, *exc):
        if getattr(self, 'real', None) is not None:
            self.bs.bootstrap = self.real
        return False


def check_very_deep_check_bootstrap_drift():
    """very_deep_check's BOOTSTRAP DRIFT section compares what the generator
    writes TODAY against a set that already exists (practice:
    very-deep-check, pass 1).

    WHY A FIXTURE RATHER THAN A GLANCE. The two checks that look like this
    one -- bootstrap_source.verify() and _template_freshness() -- both ask
    which files exist, and a drift check that silently compared nothing
    would read exactly like a clean one. So every case below asserts the
    MESSAGE, not the exit status (practice: control-asserts-which-failure):
    a hand-edit and an older vendoring differ only in the remedy printed,
    and getting that backwards sends somebody to refresh over their own
    work.

    The COLLAPSE is asserted too, and it is not cosmetic. The first real run
    (2026-09-11, four live sets) printed 60 lines carrying about six facts,
    because a set vendored at an older commit differs in every engine file
    at once. A check that long is a check nobody reads, so one older
    vendoring prints as one row -- and the fixture pins that it stays one
    row while a genuine per-file finding still gets its own.

    Each case bootstraps its own set (practice: fixture-owns-its-state): the
    states are mutually exclusive, so sharing one directory across them
    would make every case depend on the order of the ones before it."""
    # practice: slow-steps-report-and-cache -- this fixture is one of the
    # harness's slowest (~22s of a ~250s run, measured), rebuilding and
    # diffing real vendored sets to test very_deep_check.py's own drift
    # logic. Change-scoped like check_machine_readable_files_parse, on the
    # same reasoning: this gates a push and runs constantly, so it only
    # needs to ask "did THIS push break bootstrap-drift detection", not
    # "is bootstrap-drift detection healthy in general" -- the latter is
    # very_deep_check.py's own on-demand job. See _changed_touches()'s
    # docstring for the residual gap this narrower scope accepts.
    name = 'very_deep_check reports bootstrap drift against a real set'
    touched, scope = _changed_touches('tools/very_deep_check.py',
                                       'tools/precedent_bootstrap_source.py')
    if not touched:
        not_applicable(name, f'neither tools/very_deep_check.py nor '
                             f'tools/precedent_bootstrap_source.py changed '
                             f'({scope})')
        return
    import hashlib, shutil, tempfile
    import very_deep_check as vdc

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-drift-harness-'))
    cases = []

    # Each case still gets a set of its own; the generator runs once, and
    # each case gets a copy of what it wrote (_vdc_drift_copy_set), as
    # does each reference set the drift check generates
    # (_VdcDriftGeneratorMemo). Twenty generator runs became three:
    # 96 s to about 15 s (2026-10-31).
    pristine = tmp / '_pristine'

    def fresh(tag):
        dest = tmp / tag
        if not pristine.exists():
            subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                            '--level', 'individual', '--name', 'precedent-individual',
                            '--dest', str(pristine)], capture_output=True, text=True)
        _vdc_drift_copy_set(pristine, 'precedent-individual', dest,
                            'precedent-individual')
        return dest, [{'level': 'individual', 'name': 'precedent-individual',
                       'path': str(dest)}]

    memo = _VdcDriftGeneratorMemo(vdc, tmp / '_references')
    memo.where.mkdir()
    try:
        memo.__enter__()
        dest, src = fresh('clean')
        out = vdc._bootstrap_drift(src)
        cases.append(('a set the generator just wrote reports no drift at all',
                      out == [], repr(out)))

        # The harness allows an off-main seed process-wide
        # (PRECEDENT_SEED_OFF_MAIN), which hid this for as long as the
        # section existed: on a branch main lacks, the generator refused and
        # every set read "could not be run" (very deep check, 2026-10-05).
        # The fixture set above was seeded with the allowance; the drift
        # comparison itself must not need it.
        saved_seed = os.environ.pop('PRECEDENT_SEED_OFF_MAIN', None)
        try:
            out_bare = vdc._bootstrap_drift(src)
        finally:
            if saved_seed is not None:
                os.environ['PRECEDENT_SEED_OFF_MAIN'] = saved_seed
        cases.append(('without the harness\'s off-main allowance the '
                      'comparison still runs, whatever branch this is',
                      not any('could not be run' in m for m in out_bare),
                      repr(out_bare)))

        cases.append(('no resolved source reads as a SKIP, in those words, '
                      'never as clean',
                      any('NOT compared' in m and 'skip' in m.lower()
                          for m in vdc._bootstrap_drift([])),
                      repr(vdc._bootstrap_drift([]))))

        # A file the skeleton hands over ("edit this file freely afterward,
        # it is yours") must never be a finding.
        dest, src = fresh('owned')
        readme = dest / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8') + '\nmine\n', encoding='utf-8')
        out = vdc._bootstrap_drift(src)
        cases.append(('an edited skeleton file is a note, not a FINDING',
                      out and all(m.startswith('note') for m in out)
                      and 'README.md' in out[0], repr(out)))

        # The seeded session-load budgets are measured from the set's
        # rendered session file, which differs between generations, and are
        # the set's own once written: a difference is a note, never a
        # FINDING (2026-09-29, a Promote refused over exactly this).
        dest, src = fresh('budgets')
        budgets = dest / 'tools' / 'session_load_budgets.json'
        budgets.write_text(budgets.read_text(encoding='utf-8').replace(
            'Ceiling is current', 'Ceiling, reviewed by hand, is current'),
            encoding='utf-8')
        out = vdc._bootstrap_drift(src)
        cases.append(('changed session-load budgets are a note, not a FINDING',
                      out and all(m.startswith('note') for m in out)
                      and 'session_load_budgets.json' in ' '.join(out), repr(out)))

        # A vendored engine file edited in place: the remedy is upstream, and
        # refreshing over it would destroy the edit. Named per file, because
        # which file was hand-edited is the whole content of the finding.
        dest, src = fresh('handedit')
        show = dest / 'tools' / 'precedent_show.py'
        show.write_text(show.read_text(encoding='utf-8') + '\n# local tweak\n', encoding='utf-8')
        out = vdc._bootstrap_drift(src)
        cases.append(('a hand-edited engine file is a FINDING that names the '
                      'file and says to move it upstream, not to refresh',
                      any(m.startswith('FINDING') and 'precedent_show.py' in m
                          and 'hand-edited in place' in m for m in out), repr(out)))

        # An engine file missing from a set whose engine is otherwise current
        # is its own news: nothing explains it away.
        dest, src = fresh('missing')
        (dest / 'tools' / 'precedent_time.py').unlink()
        out = vdc._bootstrap_drift(src)
        cases.append(('a missing engine file is named on its own line when the '
                      'engine is otherwise current',
                      any('precedent_time.py' in m and 'does not have it' in m
                          for m in out), repr(out)))

        # The same file recorded in the manifest: a faithful vendoring of an
        # older upstream commit. One fact, one row, whatever the file count --
        # and a file the engine gained since folds into that same row rather
        # than printing as a second, unrelated-looking finding.
        dest, src = fresh('behind')
        show = dest / 'tools' / 'precedent_show.py'
        show.write_text('# an older upstream version\n', encoding='utf-8')
        manifest = dest / 'tools' / 'ENGINE_MANIFEST.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['sha256']['precedent_show.py'] = hashlib.sha256(show.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(data, indent=2), encoding='utf-8')
        (dest / 'tools' / 'precedent_time.py').unlink()
        out = vdc._bootstrap_drift(src)
        findings = [m for m in out if m.startswith('FINDING')]
        cases.append(('an older vendoring is ONE finding, saying refresh, '
                      'carrying the absent file with it',
                      len(findings) == 1 and 'refresh' in findings[0]
                      and 'OLDER upstream vendoring' in findings[0]
                      and 'precedent_time.py' in findings[0]
                      and 'hand-edited' not in findings[0], repr(out)))

        # A set's generated views are rebuilt from ITS OWN practices, so they
        # differ from an empty set's by construction: they are judged by the
        # set's own views check, never against the generator (2026-10-06,
        # AGENTS.md, MAP.md and GLOSSARY.md reported as drift in every set).
        dest, src = fresh('views')
        prac = next((dest / 'practices').glob('*.md'), None)
        if prac is not None:
            twin = dest / 'practices' / 'zz-own-rule.md'
            twin.write_text(prac.read_text(encoding='utf-8').replace(
                f'slug:        {prac.stem}', 'slug:        zz-own-rule', 1),
                encoding='utf-8')
        subprocess.run([sys.executable, str(dest / 'tools' / 'build_views.py')],
                       cwd=str(dest), capture_output=True, text=True)
        out = vdc._bootstrap_drift(src)
        cases.append(('views rebuilt from the set\'s own practices are not drift',
                      not any(m.startswith('FINDING') and
                              any(v in m for v in ('AGENTS.md', 'MAP.md', 'GLOSSARY.md'))
                              for m in out), repr(out)))
        mp = dest / 'MAP.md'
        mp.write_text(mp.read_text(encoding='utf-8') + '\nhand edit\n', encoding='utf-8')
        out = vdc._bootstrap_drift(src)
        cases.append(('...but a view that is not current with them is a FINDING '
                      'naming the file', any(m.startswith('FINDING') and 'MAP.md' in m
                                             and 'not current' in m for m in out),
                      repr(out)))
        dest, src = fresh('declared')
        ps = dest / 'precedent-source.json'
        data = json.loads(ps.read_text(encoding='utf-8'))
        data['subject'] = 'a subject this set chose for itself'
        ps.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        out = vdc._bootstrap_drift(src)
        cases.append(('the set\'s own precedent-source.json is a note, never drift',
                      not any(m.startswith('FINDING') and 'precedent-source.json' in m
                              for m in out), repr(out)))
    finally:
        memo.__exit__(None, None, None)
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'very_deep_check reports bootstrap drift against a real set '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {d[:600]}' for n, d in bad))


def check_very_deep_check_convergent_drift():
    """very_deep_check's CONVERGENT DRIFT section compares the sets against
    EACH OTHER, not each set against the template (practice:
    very-deep-check, pass 1).

    WHY THIS NEEDS A FIXTURE OF ITS OWN. The three checks either side of it
    all measure one set against one template, so a change every set made
    identically reads as healthy in all of them -- which is exactly the
    failure this section exists to catch, and exactly the failure a broken
    version of it would keep producing silently. Every case asserts the
    MESSAGE rather than a count (practice: control-asserts-which-failure),
    because "no set converged" and "nothing was compared" render as the same
    empty list and mean opposite things.

    THE THRESHOLD IS PINNED AT TWO, in both directions: one set changing a
    file is a person living in their set and must NOT be a finding, and two
    sets changing it the same way must be. A check that fired on one set
    would report every set's own README forever.

    THE DIRECTION IS PINNED AS UNKNOWN. Convergence says the sets and the
    generator disagree systematically; it does not say which side is right,
    and the first live run met exactly the ambiguous case (three shared sets
    sharing an OLDER freshness-guard.sh, not a change the template was
    missing). A finding that asserted "the template is wrong" would send
    somebody to copy a stale build upstream.

    Untracked files are pinned as NOT drift -- the first live run reported a
    harness-written `.claude/settings.local.json` in all three shared sets,
    which is container state, not a shape the skeleton is missing."""
    # practice: slow-steps-report-and-cache -- this fixture is one of the
    # harness's slowest (~32s of a ~250s run, measured), bootstrapping two
    # real sets to test very_deep_check.py's own drift logic. Change-scoped
    # like check_machine_readable_files_parse -- see that function's and
    # _changed_touches()'s docstrings for the reasoning and the residual
    # gap this narrower scope accepts.
    name = 'very_deep_check reports convergent drift across sets'
    touched, scope = _changed_touches('tools/very_deep_check.py',
                                       'tools/precedent_bootstrap_source.py')
    if not touched:
        not_applicable(name, f'neither tools/very_deep_check.py nor '
                             f'tools/precedent_bootstrap_source.py changed '
                             f'({scope})')
        return
    import shutil, tempfile
    import very_deep_check as vdc

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-converge-harness-'))
    cases = []

    # Four sets of their own, one generator run: each is a copy of the
    # first with its name and path substituted (_vdc_drift_copy_set), and
    # the drift check's reference sets are too (_VdcDriftGeneratorMemo).
    # Twelve generator runs became two: 84 s to about 8 s (2026-10-31).
    pristine = tmp / '_pristine'

    def fresh(tag):
        dest = tmp / tag
        if not pristine.exists():
            subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                            '--level', 'team', '--name', 'precedent-team-pristine',
                            '--dest', str(pristine), '--approver', 'Fixture:fixture'],
                           capture_output=True, text=True)
        _vdc_drift_copy_set(pristine, 'precedent-team-pristine', dest,
                            'precedent-team-' + tag)
        subprocess.run(['git', 'init', '-q', str(dest)], capture_output=True)
        subprocess.run(['git', '-C', str(dest), 'add', '-A'], capture_output=True)
        return dest, {'level': 'team', 'name': 'precedent-team-' + tag,
                      'path': str(dest)}

    memo = _VdcDriftGeneratorMemo(vdc, tmp / '_references')
    memo.where.mkdir(parents=True)
    try:
        memo.__enter__()
        a_dir, a = fresh('alpha')
        b_dir, b = fresh('beta')

        collect = {}
        vdc._bootstrap_drift([a, b], collect=collect)
        out = vdc._convergent_drift(collect)
        cases.append(('two sets the generator just wrote converge on nothing',
                      [m for m in out if m.startswith('FINDING')] == [],
                      repr(out)))

        cases.append(('an uncollected run reads as a SKIP, in those words',
                      any('skip' in m.lower() for m in vdc._convergent_drift(None)),
                      repr(vdc._convergent_drift(None))))

        cases.append(('a level with ONE source says so rather than printing '
                      'nothing',
                      any(m.startswith('note') and 'converge' in m
                          for m in vdc._convergent_drift(
                              {('team', 'README.md'): {'solo': frozenset()}})),
                      repr(vdc._convergent_drift(
                          {('team', 'README.md'): {'solo': frozenset()}}))))

        # ONE set changing a file is a person, not a template gap.
        line = 'a distinctive line no skeleton ships anywhere at all'
        with (a_dir / 'README.md').open('a', encoding='utf-8') as fh:
            fh.write('\n' + line + '\n')
        subprocess.run(['git', '-C', str(a_dir), 'add', '-A'], capture_output=True)
        collect = {}
        vdc._bootstrap_drift([a, b], collect=collect)
        out = vdc._convergent_drift(collect)
        cases.append(('ONE set changing a file is never a finding',
                      not [m for m in out if m.startswith('FINDING')],
                      repr(out)))

        # The SECOND set making the same change is.
        with (b_dir / 'README.md').open('a', encoding='utf-8') as fh:
            fh.write('\n' + line + '\n')
        subprocess.run(['git', '-C', str(b_dir), 'add', '-A'], capture_output=True)
        collect = {}
        vdc._bootstrap_drift([a, b], collect=collect)
        out = vdc._convergent_drift(collect)
        findings = [m for m in out if m.startswith('FINDING')]
        cases.append(('TWO sets making the same change is one finding, naming '
                      'the file, quoting the line, and both sets',
                      len(findings) == 1 and 'README.md' in findings[0]
                      and 'alpha' in findings[0] and 'beta' in findings[0]
                      and any(line in m for m in out), repr(out)))
        cases.append(('the finding does NOT assert which side is wrong',
                      bool(findings) and 'readings' in findings[0]
                      and 'OLDER' in findings[0], repr(findings)))

        # A skeleton-owned file is where this had to work: BOOTSTRAP DRIFT
        # downgrades it to a note per set, which is why convergence across
        # sets is the only thing that can see it.
        cases.append(('it fires on a SKELETON-OWNED file, which per-set drift '
                      'reports only as a note',
                      bool(findings) and 'README.md' in findings[0],
                      repr(findings)))
        converged = collect     # alpha and beta, read again by the ledger cases

        # Untracked is container state, never drift. The file itself has to
        # be untracked, not merely the edit: an earlier version of this case
        # appended to an already-staged README and asserted the filter had
        # failed, when what it had actually built was a tracked file with an
        # uncommitted change -- which IS drift (practice: fixture-owns-its-
        # state; the fixture inherited a staging state it did not set).
        c_dir, c = fresh('gamma')
        d_dir, d = fresh('delta')
        for _d in (c_dir, d_dir):
            subprocess.run(['git', '-C', str(_d), 'rm', '--cached', '-q',
                            'README.md'], capture_output=True)
            with (_d / 'README.md').open('a', encoding='utf-8') as fh:
                fh.write('\nan untracked convergent line nobody committed\n')
        collect = {}
        vdc._bootstrap_drift([c, d], collect=collect)
        out = vdc._convergent_drift(collect)
        cases.append(('an UNTRACKED shared change is not drift',
                      not any('untracked convergent line' in m for m in out),
                      repr(out)))

        # The dedup ledger (VERY_DEEP_CHECK_DEDUP_LEDGER_PROPOSAL.md,
        # precedent-individual, proposed by Morgan 2026-09-20). Reuses the
        # alpha/beta pair already converged above on README.md's shared
        # line, so DECIDED has a real FINDING to suppress rather than a
        # synthetic one.
        def write_ledger(d, entries):
            (d / 'very-deep-check-decisions.json').write_text(
                json.dumps({'entries': entries}), encoding='utf-8')

        # alpha and beta have not changed since they converged above, so
        # the collect from that run is what a second run would give.
        collect = converged

        out = vdc._convergent_drift(collect, sources=[a, b])
        cases.append(('no ledger present -> ordinary FINDING, unchanged '
                      '(must not regress)',
                      any(m.startswith('FINDING') and 'README.md' in m
                          for m in out)
                      and not any(m.startswith('DECIDED') for m in out),
                      repr(out)))

        decided = {'section': 'CONVERGENT DRIFT', 'key': 'README.md',
                   'verdict': 'intentional-customization', 'note': 'fixture',
                   'decided_by': 'Fixture', 'decided': '2026-09-20'}
        write_ledger(a_dir, [decided])
        write_ledger(b_dir, [decided])
        out = vdc._convergent_drift(collect, sources=[a, b])
        cases.append(('every converged set decided the SAME verdict -> '
                      'DECIDED, not FINDING',
                      any(m.startswith('DECIDED') and 'README.md' in m
                          and 'intentional-customization' in m for m in out)
                      and not any(m.startswith('FINDING') and 'README.md' in m
                                  for m in out),
                      repr(out)))

        write_ledger(b_dir, [])
        out = vdc._convergent_drift(collect, sources=[a, b])
        cases.append(('only ONE of the converged sets decided -> FINDING, '
                      'annotated with the partial verdict',
                      any(m.startswith('FINDING') and 'README.md' in m
                          for m in out)
                      and any('alpha decided intentional-customization' in m
                              for m in out)
                      and any('beta undecided' in m for m in out),
                      repr(out)))

        expired = dict(decided, revisit='2020-01-01')
        write_ledger(a_dir, [expired])
        write_ledger(b_dir, [expired])
        out = vdc._convergent_drift(collect, sources=[a, b])
        cases.append(("a decision whose revisit date has passed expires -> "
                      "FINDING again, not DECIDED",
                      any(m.startswith('FINDING') and 'README.md' in m
                          for m in out)
                      and not any(m.startswith('DECIDED') for m in out),
                      repr(out)))

        write_ledger(a_dir, [{'section': 'CONVERGENT DRIFT',
                              'key': 'a-file-nobody-ships.md',
                              'verdict': 'tracked-elsewhere', 'note': 'fixture',
                              'decided_by': 'Fixture', 'decided': '2026-09-20'}])
        write_ledger(b_dir, [])
        out = vdc._convergent_drift(collect, sources=[a, b])
        cases.append(('a ledger entry naming a file no longer present -> '
                      'ORPHANED LEDGER ENTRY, not silently ignored',
                      any(m.startswith('ORPHANED LEDGER ENTRY')
                          and 'a-file-nobody-ships.md' in m and 'alpha' in m
                          for m in out),
                      repr(out)))

        # Ledger files sit on disk in both fixtures at this point (the
        # orphan case above wrote them). Every existing caller of
        # _convergent_drift() passes no `sources` at all, so this asserts
        # that omitting it ignores those files completely rather than
        # picking them up implicitly.
        out = vdc._convergent_drift(collect)
        cases.append(('sources omitted (every caller before this change) '
                      'ignores ledger files on disk entirely -- ordinary '
                      'FINDING, no DECIDED, no ORPHANED, no ledger line',
                      any(m.startswith('FINDING') and 'README.md' in m
                          for m in out)
                      and not any(m.startswith(('DECIDED', 'ORPHANED'))
                                  or m.strip().startswith('ledger:')
                                  for m in out),
                      repr(out)))
    finally:
        memo.__exit__(None, None, None)
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'very_deep_check reports convergent drift across sets '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {d[:600]}' for n, d in bad))


def check_very_deep_check_authenticates_its_own_fetches():
    """very_deep_check's network calls carry the credential the environment
    holds (practice: very-deep-check; upstream-fix).

    THE INCIDENT (2026-09-10). In a session where the credential route was
    working exactly as INSTALL.md section 8 describes -- all four private
    sources cloned before the first turn -- the very deep check refused to
    read a line: every source failed its freshness gate with "could not read
    Username for 'https://github.com'". The token was fine. `_run_git`
    shelled out to plain `git` while the credential lived behind a helper
    only precedent_source_bootstrap.py passed, so a source could be cloned
    at session start and then not fetched by the check that reads it.

    The controlling case is the NEGATIVE one: with no token in the
    environment the flags must be absent entirely. A tool that always
    passes a helper offers a credential to whatever transport is
    configured, and would pass a naive "are the flags there" assertion
    while being the worse bug.
    """
    import very_deep_check as vdc
    import tempfile

    real_env = dict(os.environ)
    try:
        os.environ.pop('PRECEDENT_GIT_TOKEN', None)
        vdc._ORIGIN_URL.clear()
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / 'r'
            repo.mkdir()
            subprocess.run(['git', '-C', str(repo), 'init', '-q'],
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin',
                            'https://github.com/example/example'],
                           capture_output=True, text=True)

            no_token = vdc._credential_args(repo)

            os.environ['PRECEDENT_GIT_TOKEN'] = 'not-a-real-token'
            vdc._ORIGIN_URL.clear()
            with_token = vdc._credential_args(repo)

            # A file:// remote needs no credential and must never be offered
            # one, whatever the environment holds.
            local = pathlib.Path(tmp) / 'l'
            local.mkdir()
            subprocess.run(['git', '-C', str(local), 'init', '-q'],
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', str(local), 'remote', 'add', 'origin',
                            f'file://{tmp}/upstream'], capture_output=True, text=True)
            vdc._ORIGIN_URL.clear()
            local_args = vdc._credential_args(local)

            results = [
                ('no token in the environment means no credential flags at '
                 'all (the controlling case)', no_token == []),
                ('a token in the environment produces credential flags',
                 bool(with_token)),
                ('the flags clear any helper configured elsewhere first',
                 'credential.helper=' in with_token),
                ('the token VALUE never appears in the argument list',
                 not any('not-a-real-token' in a for a in with_token)),
                ('the helper names the variable instead',
                 any('PRECEDENT_GIT_TOKEN' in a for a in with_token)),
                ('a file:// remote is never offered a credential',
                 local_args == []),
                ('network subcommands are recognised by name, so a fetch '
                 'added later is covered too',
                 {'fetch', 'ls-remote', 'pull'} <= vdc._NETWORK_GIT),
                ('a non-network subcommand is not given credential flags',
                 'log' not in vdc._NETWORK_GIT and 'config' not in vdc._NETWORK_GIT),
            ]
            failed = [name for name, ok in results if not ok]
            check(f'the very deep check authenticates its own fetches '
                  f'({len(results)} stated cases, an empty environment being '
                  f'the negative control)',
                  not failed, '; '.join(failed) if failed else '')
    finally:
        os.environ.clear()
        os.environ.update(real_env)
        vdc._ORIGIN_URL.clear()


def check_branch_sweep_sees_work_landed_on_the_base_branch():
    """A branch merged into the BASE branch, and never into the integration
    branch, is reported as finished work rather than as unlanded
    (practice: very-deep-check, pass 4).

    THE CASE THAT CARRIES THIS CHECK (asked 2026-09-12, by Morgan: "Alex
    likely has branches on main from bestpractice from weeks ago"). A repo
    whose work is pinned to an integration branch has TWO branches work can
    land on, and the sweep tested one. Everything merged into the base
    branch alone therefore reported as `CARRIES n unlanded commit(s)`, with
    a verdict demanding somebody merge or close it -- forever, since nothing
    about it will ever change. That is the failure that ends a list: the
    false rows outnumber the true ones, so the reader stops reading, and the
    genuinely unlanded branch beside them goes unread too.

    Both directions are asserted, because a fix that swept everything into
    the "already landed" bucket would pass a one-sided version of this."""
    import tempfile
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        # The integration branch, forked from main and moved on, so that
        # "merged into main" and "merged into the integration branch" are
        # genuinely different questions here.
        _git(up, 'checkout', '-q', '-b', 'beta')
        (up / 'beta.txt').write_text('beta\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'beta work')

        # Landed on main only -- the class this check is about.
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'checkout', '-q', '-b', 'landed-on-main')
        (up / 'old.txt').write_text('old\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'old work')
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', '-m', 'merge old work',
             'landed-on-main')

        # Landed nowhere -- the row that must still demand a verdict.
        _git(up, 'checkout', '-q', 'beta')
        _git(up, 'checkout', '-q', '-b', 'really-unlanded')
        (up / 'new.txt').write_text('new\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'genuinely unlanded')
        # Leave the upstream on main before cloning. A clone takes its
        # origin/HEAD from whatever the remote has checked out, and that is
        # what tells the sweep which OTHER branch is protected -- with the
        # upstream sitting on beta, main itself reads as an ordinary branch
        # carrying unlanded work, which is both a wrong fixture and a real
        # shape worth knowing about.
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        scan = vdc.scan_branches(work, 'beta') or {}
        elsewhere = {r['name']: r for r in scan.get('merged_elsewhere') or []}
        unmerged = {r['name'] for r in scan.get('unmerged') or []}
        merged = {r['name'] for r in scan.get('merged') or []}

        results = [
            ('a branch merged into the base branch is reported as merged '
             'there', 'landed-on-main' in elsewhere),
            ('and names WHICH branch already carries it',
             elsewhere.get('landed-on-main', {}).get('into') == 'main'),
            ('and is no longer reported as carrying unlanded work',
             'landed-on-main' not in unmerged),
            ('a branch landed on neither still demands a verdict',
             'really-unlanded' in unmerged),
            ('and is not swept into the merged lists',
             'really-unlanded' not in elsewhere
             and 'really-unlanded' not in merged),
            ('every branch row names who last touched it, so a verdict can '
             'be routed rather than skipped',
             all(r.get('author')
                 for r in (list(elsewhere.values())
                           + list(scan.get('unmerged') or [])))),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check tells work landed on the base branch from '
              f'work landed nowhere ({len(results)} stated cases)',
              not failed, '; '.join(failed) if failed else '')


def check_session_sweep_reports_the_repo_half():
    """The repo half of the live-session sweep reports what landed recently,
    what is sitting uncommitted, and says plainly that it is a half
    (practice: very-deep-check).

    THE GAP (asked 2026-09-12, by Morgan: "do a sweep of live sessions
    against the repo to see if there's anything recent being missed"). Every
    other part of this check reads the repository against itself, so none of
    them can see a session that ran, decided something and left nothing
    behind -- the loss `repo-is-memory` names and nothing looks for.

    THE CONTROLLING CASE is the window, not the listing. A sweep that
    silently used its own default where a repo declared a window would
    report about a period nobody asked about, and would look exactly like a
    working feature -- the same failure the declared stale threshold has its
    own check for."""
    import tempfile, datetime
    import very_deep_check as vdc

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        # One commit inside any plausible window, one far outside it. Dates
        # forced through the commit environment: a fixture that reads the
        # clock for the property it is asserting is testing the clock
        # (practice: fixture-owns-its-state).
        for branch, days in (('recent-work', 1), ('ancient-work', 400)):
            when = (datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S%z')
            _git(up, 'checkout', '-q', 'main')
            _git(up, 'checkout', '-q', '-b', branch)
            (up / f'{branch}.txt').write_text(branch + '\n')
            _git(up, 'add', '-A')
            subprocess.run(['git', '-C', str(up), 'commit', '-qm', branch],
                           capture_output=True, text=True,
                           env={**os.environ,
                                'GIT_AUTHOR_DATE': when,
                                'GIT_COMMITTER_DATE': when,
                                'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})
        _git(up, 'checkout', '-q', 'main')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)

        act = vdc.recent_activity(work, 14) or {}
        names = {b['name'] for b in act.get('branches', [])}
        subjects = {c['subject'] for c in act.get('commits', [])}
        # Uncommitted work is the same loss one step earlier, and the
        # cheapest thing here to see.
        (work / 'scratch.txt').write_text('never committed\n')
        dirty = vdc.recent_activity(work, 14) or {}
        wide = vdc.recent_activity(work, 500) or {}
        # A file this run writes itself is not somebody's lost work when the
        # run made it dirty (2026-10-11: the branch page the run had just
        # written was reported as uncommitted work). One already dirty
        # before the run still is.
        (work / 'scratch.txt').unlink()
        # The fixture owns its identity: the full check runs with no global
        # git config, where a commit with none is refused.
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'record').mkdir(exist_ok=True)
        (work / 'record' / 'stale_branches.md').write_text('old\n')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'page')
        vdc._snapshot_dirty(work)
        (work / 'record' / 'stale_branches.md').write_text('this run\n')
        own = vdc.recent_activity(work, 14) or {}
        (work / 'scratch.txt').write_text('never committed\n')
        vdc._snapshot_dirty(work)
        theirs = vdc.recent_activity(work, 14) or {}
        vdc._DIRTY_AT_START.pop(str(work.resolve()), None)

        results = [
            ('a branch pushed inside the window is reported',
             'recent-work' in names),
            ('a branch last touched outside it is not',
             'ancient-work' not in names),
            ('the same window governs the commit list',
             'recent-work' in subjects and 'ancient-work' not in subjects),
            ('a wider window reaches further back, so the window is the '
             'input and not a fixed horizon',
             'ancient-work' in {b['name'] for b in wide.get('branches', [])}),
            ('every row names who did it',
             all(b.get('author') for b in act.get('branches', []))),
            ('work sitting in the working tree is counted',
             dirty.get('dirty') == 1),
            ('and a clean tree is reported as clean, not as unknown',
             act.get('dirty') == 0),
            ('a file this run wrote itself is not counted as lost work',
             own.get('dirty') == 0),
            ('work that was uncommitted before the run still is',
             theirs.get('dirty') == 2),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check reports the repo half of the session '
              f'sweep ({len(results)} stated cases, the window being the '
              f'controlling one)',
              not failed, '; '.join(failed) if failed else '')


def check_merged_branches_carry_a_date_and_a_staleness_verdict():
    """A merged, undeleted branch is reported with the date it last moved
    and whether it is past the declared stale threshold
    (practice: very-deep-check, pass 4).

    THE GAP (asked 2026-09-10, by Morgan, of a real sweep). The merged half
    of the branch sweep was a bare list of names. That list ends in a
    deletion, and a name with no date cannot be acted on: the branch merged
    this morning and the one merged last quarter render identically, so the
    reader either deletes blind or -- what actually happens -- defers the
    whole list again. Measured on this repo the same day: 69 merged
    branches, median age 3 days, oldest 39, and no way to see any of that.

    The threshold is a DECLARED input, so the controlling case here is not
    "does 30 days work" but "does the declared number reach the sweep at
    all" -- a default silently overriding a repo's own value would mark the
    wrong branches and look exactly like a working feature.
    """
    import very_deep_check as vdc
    import tempfile, datetime

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # Two merged branches at KNOWN ages, straddling the threshold. The
        # dates are forced through the commit environment rather than taken
        # from the clock, so this fixture owns its own state and cannot pass
        # or fail on when it happens to run (practice: fixture-owns-its-state
        # -- the neighbouring unmerged-verdict check was made to fail on the
        # clock exactly once, which is why this is explicit here).
        for branch, days in (('long-done', 400), ('just-landed', 1)):
            when = (datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S%z')
            _git(up, 'checkout', '-q', 'main')
            _git(up, 'checkout', '-q', '-b', branch)
            (up / f'{branch}.txt').write_text(branch + '\n')
            _git(up, 'add', '-A')
            subprocess.run(['git', '-C', str(up), 'commit', '-qm', branch],
                           capture_output=True, text=True,
                           env={**os.environ,
                                'GIT_AUTHOR_DATE': when,
                                'GIT_COMMITTER_DATE': when,
                                'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})
            _git(up, 'checkout', '-q', 'main')
            _git(up, 'merge', '-q', '--no-ff', '-m', f'merge {branch}', branch)

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)

        scan = vdc.scan_branches(work, 'main', stale_days=90) or {}
        rows = {r['name']: r for r in (scan.get('merged') or [])}

        results = [
            ('both merged branches are reported as merged',
             set(rows) == {'long-done', 'just-landed'}),
            ('every merged row carries the date it last moved',
             all(r.get('last') and r.get('age_days') is not None
                 for r in rows.values())),
            ('the age is the real one, not the date of the merge or the clone',
             rows.get('long-done', {}).get('age_days', 0) >= 399),
            ('a branch past the threshold is marked stale',
             rows.get('long-done', {}).get('stale') is True),
            ('a branch inside the threshold is NOT marked stale',
             rows.get('just-landed', {}).get('stale') is False),
            ('the scan reports which threshold it applied',
             scan.get('stale_days') == 90),
        ]

        # NEGATIVE CONTROL, and the controlling case: the same fixture at a
        # threshold that puts BOTH branches on the recent side. If the
        # passed-in number were ignored in favour of the default, 'long-done'
        # would still read stale and every assertion above would still pass.
        loose = vdc.scan_branches(work, 'main', stale_days=1000) or {}
        loose_rows = {r['name']: r for r in (loose.get('merged') or [])}
        results.append(
            ('the DECLARED threshold decides, not a default compiled in -- '
             'at 1000 days nothing is stale',
             loose_rows and not any(r.get('stale') for r in loose_rows.values())))

        # And a repo declaring its own value gets it without being asked.
        (work / 'precedent.json').write_text(
            json.dumps({'format_version': 1, 'branch_stale_days': 90}), encoding='utf-8')
        declared = vdc.scan_branches(work, 'main') or {}
        results.append(
            ("a repo's own precedent.json branch_stale_days is read when no "
             "threshold is passed",
             declared.get('stale_days') == 90))

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check dates every merged branch and marks the '
              f'stale ones ({len(results)} stated cases, a threshold that '
              f'makes nothing stale being the negative control)',
              not failed, '; '.join(failed) if failed else '')


def check_branch_report_writes_delete_links_to_a_committable_file():
    """The branch sweep's own write-up lands in a committable file with a
    real, clickable link on every row -- not only in whichever session's
    transcript happened to print it (practice: very-deep-check, pass 4;
    repo-is-memory).

    THE GAP (Morgan, reading a Sunday run: "I don't remember getting that").
    scan_branches() and _branch_url() already compute everything the list
    needs; nothing wrote it anywhere but stdout, which is exactly the run
    that happened and was never seen again. _write_branch_report() is the
    fix, and this proves both halves: the merged-and-stale row carries a
    working delete link, and the unmerged row carries both a branches-page
    link and a compare-view link -- the actual owner/repo slug parsed from
    origin, not a placeholder.
    """
    import very_deep_check as vdc
    import tempfile, datetime

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A branch merged long enough ago to land on the STALE side, so the
        # test exercises the row this feature exists for -- the safest
        # deletions, the ones a bare name never got acted on (see the
        # neighbouring check's own Story).
        when = (datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=200)).strftime('%Y-%m-%dT%H:%M:%S%z')
        _git(up, 'checkout', '-q', '-b', 'old-merged')
        (up / 'a.txt').write_text('a\n')
        _git(up, 'add', '-A')
        subprocess.run(['git', '-C', str(up), 'commit', '-qm', 'old work'],
                       capture_output=True, text=True,
                       env={**os.environ, 'GIT_AUTHOR_DATE': when,
                            'GIT_COMMITTER_DATE': when,
                            'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', '-m', 'merge old', 'old-merged')

        _git(up, 'checkout', '-q', '-b', 'wip-unmerged')
        (up / 'b.txt').write_text('b\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'unlanded work')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        # A REAL GitHub slug, parsed from origin -- the assertions below
        # check for this exact URL, so a version that hardcoded a link or
        # dropped the parse silently would not pass.
        _git(work, 'remote', 'set-url', 'origin',
             'https://github.com/alex137/fixture-repo.git')

        scan = vdc.scan_branches(work, 'main', stale_days=90) or {}
        out_path = tmp / 'record' / 'stale-branches.md'
        vdc._write_branch_report({'checkout': scan}, out_path, work)
        text = out_path.read_text(encoding='utf-8')

        results = [
            ('the file exists at the path asked for',
             out_path.is_file()),
            ('the merged-and-stale branch is listed',
             'old-merged' in text),
            ('its row carries a real GitHub delete link, not a placeholder',
             'https://github.com/alex137/fixture-repo/branches/all?query=old-merged'
             in text),
            ('the unmerged branch is listed with its verdict',
             'wip-unmerged' in text and 'CARRIES 1 unlanded commit' in text),
            ('the unmerged row carries a compare-view link',
             'https://github.com/alex137/fixture-repo/compare/main...wip-unmerged'
             in text),
            ('the file says plainly that it is generated, and what to do '
             'instead of editing it',
             'generated_by: tools/very_deep_check.py' in text
             and "Don't edit here" in text),
        ]

        # NEGATIVE CONTROL: a non-GitHub origin gets no link at all --
        # _branch_url and _compare_url both return None for it, and a
        # version that silently fell back to a hardcoded or empty link
        # instead of omitting the row's link entirely is what this catches.
        _git(work, 'remote', 'set-url', 'origin', 'https://example.com/x/y.git')
        scan2 = vdc.scan_branches(work, 'main', stale_days=90) or {}
        out2 = tmp / 'record' / 'stale-branches-2.md'
        vdc._write_branch_report({'checkout': scan2}, out2, work)
        text2 = out2.read_text(encoding='utf-8')
        results.append(
            ('a non-GitHub origin gets no delete or compare link at all, '
             'rather than a wrong one',
             'old-merged' in text2 and 'https://' not in text2))

        failed = [name for name, ok in results if not ok]
        check(f'the branch sweep writes a committable report carrying real '
              f'delete and compare links ({len(results)} stated cases, a '
              f'non-GitHub origin producing no link at all being the '
              f'negative control)',
              not failed, '; '.join(failed) if failed else '')


def check_unlanded_work_is_reported_before_the_passes():
    """The very deep check must surface unlanded work BEFORE its checklist,
    not with the branch verdicts at the end (practice: very-deep-check).

    THE INCIDENT. The 2026-09-07 run rediscovered two missing source files
    from scratch, wrote them up as findings, and filed them as open TODO
    items -- while the fixes sat finished on a branch from the previous day,
    in both private sets, named in those branches' own commit subjects.
    Nothing had asked what was sitting unmerged, because the branch list only
    printed after every pass had already been worked.

    The sweep's two halves have different costs and different jobs. Deciding
    a branch's fate is judgment and stays in pass 4. Knowing what already
    exists is a list, costs nothing, and is the only step in the whole check
    that prevents work rather than finding it -- so it has to come first, and
    ORDER is the property, which is what this asserts.

    A branch carrying no unique commits (rebased or squash-merged in) must
    NOT appear here: it is a deletion candidate, not unlanded work, and
    listing it would train the reader to skim the section that exists to be
    read."""
    import tempfile, shutil
    import json as _json

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A branch carrying real, unlanded work.
        _git(up, 'checkout', '-q', '-b', 'carries-work')
        (up / 'fix.txt').write_text('the fix nobody landed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'a fix that never landed')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        (work / 'practices').mkdir()
        shutil.copy(next(PRACTICES_DIR.glob('*.md')), work / 'practices')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'declare a source')
        _git(work, 'push', '-q', 'origin', 'main')

        # HERMETIC, and it was not before.
        #
        # very_deep_check.py resolves the INDIVIDUAL source from a user-level
        # config outside any repo, so this fixture -- which declares one
        # universal source and nothing else -- was silently reaching the
        # machine's real precedent-individual clone. Its own output gave this
        # away once the failure detail above started printing it: a run
        # against a scratch repo was reporting "FRESHNESS -- declared
        # sources ... individual source 'precedent-individual'".
        #
        # That made the fixture inherit ambient state it never declared, and
        # the freshness gate is a HARD REFUSAL that returns before printing
        # anything -- so whenever that real clone was behind, diverged, or
        # slow to fetch, this check failed on a repository it is not testing.
        # It ran green for weeks and failed twice in the session that found
        # it, unreproducible in twelve isolated runs, which is exactly what a
        # test reading state it does not own looks like.
        #
        # Pointing PRECEDENT_USER_CONFIG at a path inside the temp directory
        # gives the resolver a config that legitimately declares no
        # individual source, so the fixture tests the fixture.
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
        # The sections that reach the network are skipped: this reads the
        # UNLANDED WORK block and where the checklist starts, neither of
        # which they print, and the CI FLEET AUDIT that --skip-liveness
        # skips was 181 of a run's 182 s (measured 2026-10-31). The branch
        # scan, which prints UNLANDED WORK, stays on.
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--repo', str(work), '--checklist',
             '--skip-liveness', '--skip-visibility', '--skip-endgame-merge'],
            capture_output=True, text=True, cwd=str(work), env=env)
        out = r.stdout

        results = []
        results.append(('the run produced output at all', bool(out.strip())))
        has_block = 'UNLANDED WORK' in out
        results.append(('unlanded work gets its own block', has_block))
        if has_block and 'Pass 1 —' in out:
            results.append(('it is printed BEFORE the checklist the session '
                            'works from -- the whole point',
                            out.index('UNLANDED WORK') < out.index('Pass 1 —')))
        else:
            results.append(('it is printed BEFORE the checklist the session '
                            'works from -- the whole point', False))
        # Named IN THE BLOCK, not merely somewhere above the checklist: the
        # LIVE SESSIONS section a few lines below lists every recently
        # pushed branch, so the wider slice passed even with the block's
        # branch list deleted (found 2026-10-31 by breaking it on purpose,
        # as check_shallow_clone_never_fabricates_unlanded_work already
        # found for itself).
        block = out.split('UNLANDED WORK', 1)[-1] if has_block else ''
        for end in ('\nLIVE SESSIONS', '\nREPOSITORY VISIBILITY', 'Pass 1 —'):
            block = block.split(end, 1)[0]
        results.append(('the branch carrying unlanded work is named',
                        'carries-work' in block))

        failed = [n for n, ok in results if not ok]
        # SAY WHAT THE TOOL ACTUALLY DID when this fails.
        #
        # This check ran green for weeks and then failed twice inside one
        # session (2026-09-07), both times reporting only which of its four
        # stated cases were false -- which is the symptom, never the cause.
        # It could not be reproduced in twelve isolated runs, so the cause is
        # something about a loaded full run, and the detail as written threw
        # away the one piece of evidence that would name it: what
        # very_deep_check.py itself printed and exited with. `UNLANDED WORK`
        # is printed UNCONDITIONALLY whenever the branch scan is not skipped,
        # so its absence means the tool returned before reaching that line --
        # most likely the freshness gate refusing, which it is designed to do
        # as a hard refusal rather than a warning. That is a guess until a
        # failing run says so itself, which is what this detail is for.
        #
        # Same lesson as the failure recap in main(): a count is not a
        # diagnosis, and re-running is what destroys the evidence.
        detail = ''
        if failed:
            tail = (out or '')[-400:].replace('\n', ' | ')
            detail = (f"{'; '.join(failed)} "
                      f"[very_deep_check.py exited {r.returncode}; "
                      f"stdout tail: {tail!r}; "
                      f"stderr tail: {(r.stderr or '')[-300:]!r}]")
        check(f'the very deep check reports unlanded work before its passes, '
              f'not after ({len(results)} stated cases)',
              not failed, detail)


def check_very_deep_check_records_its_components():
    """Every run records what each of its sections returned and cost, and a
    section it did not run is recorded as skipped rather than as clean
    (practice: very-deep-check).

    THE POINT OF THE LEDGER is a question no single run can answer -- which
    parts of this check stopped earning their place -- so the properties
    that matter are all about what survives to the NEXT run: the file is
    written, an unrun section is distinguishable from a quiet one, a run
    that aborted at the freshness gate still leaves its trace, and the
    quiet-section question is asked only once there are enough runs to ask
    it (QUIET_RUNS_BEFORE_QUESTION), never extrapolated from one.

    Each case asserts the tool's own words, not merely a non-zero exit
    (practice: control-asserts-which-failure): 'skipped' as a recorded
    status, 'first run in the ledger', 'FOUND NOTHING, ACROSS EVERY
    RECORDED RUN', and --record-pass's own refusal text.
    """
    import tempfile, shutil
    import json as _json

    _git = fixture_git

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        (work / 'practices').mkdir()
        shutil.copy(next(PRACTICES_DIR.glob('*.md')), work / 'practices')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'declare a source')
        _git(work, 'push', '-q', 'origin', 'main')

        # The fixture owns every ambient input it is graded on
        # (practice: fixture-owns-its-state): its own user config, so no real
        # individual source resolves, and its own ledger path, so the
        # repository's committed ledger is neither read nor written.
        ledger = tmp / 'ledger.json'
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))

        def _run():
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
                 '--repo', str(work), '--ledger', str(ledger),
                 '--skip-liveness', '--skip-visibility',
                 '--skip-branch-scan', '--skip-endgame-merge'],
                capture_output=True, text=True, cwd=str(work), env=env)

        first = _run()
        results = [('the run writes a ledger', ledger.is_file())]
        data = {}
        if ledger.is_file():
            try:
                data = _json.loads(ledger.read_text(encoding='utf-8'))
            except ValueError as exc:
                results.append((f'the ledger parses ({exc})', False))
        runs = (data.get('runs') or [])
        rows = runs[-1].get('components', []) if runs else []
        by_name = {r.get('name'): r for r in rows}
        results.append(('one run is recorded', len(runs) == 1))
        results.append(('a section that ran carries a countable result',
                        any(r.get('findings') is not None for r in rows)))
        results.append(('a section that ran carries its printed cost',
                        any(r.get('output_tokens', 0) > 0 for r in rows)))
        # The controlling case: --skip-branch-scan must not read as clean.
        branch_row = by_name.get('BRANCHES -- verdicts owed', {})
        results.append(("a skipped section is recorded 'skipped', never "
                        "as a clean zero",
                        branch_row.get('status') == 'skipped'
                        and branch_row.get('findings') is None))
        results.append(('one run says so rather than extrapolating',
                        'first run in the ledger' in first.stdout))
        results.append(('one run does NOT yet name a quiet section',
                        'FOUND NOTHING, ACROSS EVERY RECORDED RUN'
                        not in first.stdout))

        import very_deep_check as vdc
        for _ in range(max(0, vdc.QUIET_RUNS_BEFORE_QUESTION - 1)):
            last = _run()
        results.append((f'at {vdc.QUIET_RUNS_BEFORE_QUESTION} runs the quiet '
                        f'sections are named',
                        'FOUND NOTHING, ACROSS EVERY RECORDED RUN'
                        in last.stdout))

        # --record-pass: the good case lands, the malformed one refuses in
        # its own words and writes nothing.
        ok = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--ledger', str(ledger), '--record-pass', '2=done,findings=3'],
            capture_output=True, text=True, env=env)
        data2 = _json.loads(ledger.read_text(encoding='utf-8'))
        passes = (data2.get('runs') or [{}])[-1].get('passes') or []
        results.append(('a hand-worked pass is recorded against the run',
                        ok.returncode == 0 and len(passes) == 1
                        and passes[0].get('findings') == 3))
        bad = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--ledger', str(ledger), '--record-pass', 'nonsense'],
            capture_output=True, text=True, env=env)
        results.append(('a malformed --record-pass refuses in its own words',
                        bad.returncode != 0
                        and '--record-pass wants PASS=STATUS' in bad.stderr))
        data3 = _json.loads(ledger.read_text(encoding='utf-8'))
        results.append(('and writes nothing when it refuses',
                        data3 == data2))

        # A run that ABORTS still leaves its trace. Losing it would lose the
        # only evidence the aborted run produced -- and would also make the
        # ledger's own averages quietly wrong, since the sections it never
        # reached would simply be missing rather than marked. A tracked
        # file that does not parse is the tool's own hard stop, taken here
        # because it fires deterministically and offline.
        (work / 'broken.json').write_text('{not json', encoding='utf-8')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'a file that does not parse')
        before = len(_json.loads(ledger.read_text(encoding='utf-8'))['runs'])
        aborted = _run()
        after = _json.loads(ledger.read_text(encoding='utf-8'))['runs']
        results.append(('a run that aborts mid-check is still recorded',
                        aborted.returncode != 0 and len(after) == before + 1))
        results.append(('and is marked incomplete rather than counted as a '
                        'clean run',
                        bool(after) and after[-1].get('completed') is False
                        and len(after[-1].get('components', [])) >= 1))
        results.append(("the aborting section's own result is kept",
                        bool(after) and any(
                            r.get('name') == 'MACHINE-READABLE FILES'
                            and r.get('findings') == 1
                            for r in after[-1].get('components', []))))

        # THE LEDGER BELONGS TO THE REPO BEING CHECKED. With the path
        # anchored at this engine's own checkout, every fixture above
        # appended a row about a temporary directory to THIS repository's
        # ledger -- six inside one harness run, each a full 20-section row.
        # The cross-run read is a comparison, so a foreign row moves every
        # number in it rather than merely adding noise. Found 2026-09-11, by
        # reading the ledger the first real run produced.
        home_ledger = ROOT / 'record' / 'very-deep-check-ledger.json'
        before_rows = None
        if home_ledger.is_file():
            try:
                before_rows = len(_json.loads(
                    home_ledger.read_text(encoding='utf-8')).get('runs') or [])
            except ValueError:
                before_rows = None
        subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--repo', str(work), '--skip-liveness', '--skip-visibility',
             '--skip-branch-scan', '--skip-endgame-merge'],
            capture_output=True, text=True, cwd=str(work), env=env)
        own = work / 'record' / 'very-deep-check-ledger.json'
        results.append(("a run with no --ledger records into the CHECKED "
                        "repo's own ledger", own.is_file()))
        if before_rows is not None and home_ledger.is_file():
            after_rows = len(_json.loads(
                home_ledger.read_text(encoding='utf-8')).get('runs') or [])
            results.append(("and never into this engine's checkout",
                            after_rows == before_rows))

        failed = [n for n, ok_ in results if not ok_]
        detail = ''
        if failed:
            detail = (f"{'; '.join(failed)} "
                      f"[first run exited {first.returncode}; stdout tail: "
                      f"{(first.stdout or '')[-300:]!r}; stderr tail: "
                      f"{(first.stderr or '')[-200:]!r}]")
        check(f'the very deep check records what each of its parts returned '
              f'and cost ({len(results)} stated cases)', not failed, detail)


@_without_session_id
def check_shallow_clone_never_fabricates_unlanded_work():
    """A branch whose merge base is out of reach must never be reported as
    carrying a COUNT of unlanded commits (practice: very-deep-check,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. The unlanded-work scan told a session that
    three branches of `precedent-individual` carried 22 commits of unlanded
    work. All three were plain ancestors of `main` -- every commit already
    landed, nothing to read. The scan had run against a shallow clone, where
    `git cherry` cannot find a merge base and answers by calling every commit
    unique.

    WHY THE EXISTING GUARD DID NOT FIRE. _unmerged_row already handled a
    shallow clone -- by checking `git cherry`'s exit code. There is no
    non-zero exit to catch: git exits 0 and prints a wrong answer, which is
    this repo's recurring shape (AGENTS.md records the same for `%P`
    reporting no parents and `rev-parse` printing a ref name where a hash
    belongs). A guard written for the wrong failure mode reads as coverage
    and is none.

    The direction of the error is what makes it expensive rather than merely
    wrong. This section exists to tell a session which branches to go read
    BEFORE the passes, so a fabricated count spends exactly the reading it
    was built to save -- and it fabricates in the environment every fresh
    session starts in.

    TWO CASES, because the fix has two outcomes and only one is a refusal.
    Deepening usually rescues the comparison, so the common path is a CORRECT
    answer, not an UNKNOWN one -- a control that only asserted the refusal
    would be satisfied by a tool that refused on every branch it saw.

    WHICH CASE DISCRIMINATES, measured rather than assumed: replayed against
    the pre-fix code, CASE 2 fails (on "no count of unlanded commits is
    invented" -- the bug itself) and CASE 1 PASSES. Case 1 is a regression
    guard on the right answer, NOT evidence the bug is caught, and a later
    session must not read it as such. The reason is worth knowing before
    trusting any fixture built this way: _fetch_all_heads falls back to an
    unbounded `git fetch origin` when its bounded one fails, so a local
    fixture gets full history handed to it and the buggy comparison comes
    out right anyway. In the wild the bounded fetch SUCCEEDED and simply did
    not reach far enough, no fallback ran, and the fabricated count stood --
    which is why the incident needed a real repository to show up at all.
    """
    # practice: slow-steps-report-and-cache -- this fixture is one of the
    # harness's slowest (~16s of a ~250s run, measured), building real git
    # history to test very_deep_check.py's shallow-clone handling.
    # Change-scoped like check_machine_readable_files_parse -- see that
    # function's and _changed_touches()'s docstrings for the reasoning and
    # the residual gap this narrower scope accepts. NOT scoped on "are
    # shallow clones still common" (this docstring's own account says they
    # remain the default environment every fresh session starts in) --
    # scoped only on whether THIS push touched the code under test, which
    # holds regardless of how common shallow clones are in the wild.
    name = ('a shallow clone never fabricates a count of unlanded work, and '
            'says so when it cannot tell')
    touched, scope = _changed_touches('tools/very_deep_check.py')
    if not touched:
        not_applicable(name, f'tools/very_deep_check.py did not change ({scope})')
        return
    import shutil, tempfile
    import json as _json

    _git = fixture_git

    def _seed(up):
        _git(up, 'init', '-q', '-b', 'main')
        # `up` is a working clone, not a bare one, so git refuses a push to
        # the branch it has checked out. Two fixtures pushed to it anyway and
        # never noticed, because nothing looked at the exit code.
        _git(up, 'config', 'receive.denyCurrentBranch', 'ignore')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        _git(up, 'checkout', '-q', '-b', 'fully-landed')
        (up / 'g.txt').write_text('work that DID land\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'landed work')
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', 'fully-landed', '-m', 'merge it')
        # Deeper than the tool's routine --depth=50, so the merge base is
        # genuinely out of reach of a shallow clone. See the docstring.
        # Seventy commits, each adding f{i}.txt, written by one fast-import
        # rather than 140 git add/commit calls, which each paid the commit
        # hooks: 13 s to well under one (2026-10-31).
        stamp = int(time.time())
        stream = []
        for i in range(70):
            msg, body = f'later {i}\n', f'later {i}\n'
            stream += ['commit refs/heads/main',
                       f'committer Harness <harness@example.com> {stamp + i} +0000',
                       f'data {len(msg)}', msg.rstrip('\n')]
            if i == 0:
                stream.append('from refs/heads/main^0')
            stream += [f'M 100644 inline f{i}.txt', f'data {len(body)}',
                       body.rstrip('\n')]
        r = subprocess.run(['git', '-C', str(up), 'fast-import', '--quiet'],
                           input='\n'.join(stream) + '\n', text=True,
                           capture_output=True)
        if r.returncode != 0:
            raise FixtureSetupError(f'git fast-import (in {up}) exited '
                                    f'{r.returncode}: {r.stderr.strip()[-300:]}')
        _git(up, 'reset', '-q', '--hard', 'main')

    def _consumer(work, tmp):
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        (work / 'practices').mkdir(exist_ok=True)
        shutil.copy(next(PRACTICES_DIR.glob('*.md')), work / 'practices')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'declare a source')

    def _run(work, tmp):
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
        # Network-bound sections skipped, as in
        # check_unlanded_work_is_reported_before_the_passes: the branch scan
        # is the code under test, and it stays on.
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--repo', str(work), '--checklist',
             '--skip-liveness', '--skip-visibility', '--skip-endgame-merge'],
            capture_output=True, text=True, cwd=str(work), env=env)
        # THE UNLANDED WORK BLOCK ONLY, not everything printed before the
        # checklist. This used to slice at 'Pass 1 --' and assert that a
        # branch name did not appear anywhere above it, which was a proxy
        # for "no fabricated count" that held only while nothing else
        # printed branch names. The live-session sweep prints them a few
        # lines below this block, so the proxy started failing on correct
        # output (2026-09-12). Scope the assertion to the section that is
        # actually under test.
        out = r.stdout
        if 'UNLANDED WORK' not in out:
            return r, out.split('Pass 1 —')[0]
        block = out.split('UNLANDED WORK', 1)[1]
        for end in ('\nLIVE SESSIONS', '\nREPOSITORY VISIBILITY', 'Pass 1 —'):
            if end in block:
                block = block.split(end, 1)[0]
        return r, block

    results = []
    diag = []

    # The history is built once and each case copies it: both cases start
    # from the same seeded repository, and neither writes to the original.
    seeded = pathlib.Path(tempfile.mkdtemp(prefix='precedent-shallow-seed-'))
    try:
        (seeded / 'up').mkdir(); _seed(seeded / 'up')
        _shallow_cases(seeded / 'up', _consumer, _run, results, diag)
    finally:
        shutil.rmtree(seeded, ignore_errors=True)

    failed = [n for n, ok in results if not ok]
    detail = ''
    if failed:
        detail = f"{'; '.join(failed)} [{'; '.join(diag)}]"
    check(f'a shallow clone never fabricates a count of unlanded work, and '
          f'says so when it cannot tell ({len(results)} stated cases)',
          not failed, detail)


def _shallow_cases(seeded, _consumer, _run, results, diag):
    """check_shallow_clone_never_fabricates_unlanded_work's two cases,
    each on its own copy of the `seeded` history."""
    import shutil, tempfile
    _git = fixture_git

    # CASE 1 -- the real incident: shallow clone, origin still reachable.
    # The tool must deepen and give the CORRECT answer (nothing unlanded),
    # never a fabricated count.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        shutil.copytree(seeded, up, symlinks=True)
        subprocess.run(['git', 'clone', '-q', '--depth', '1',
                        f'file://{up}', str(work)], capture_output=True)
        shallow = _git(work, 'rev-parse',
                       '--is-shallow-repository').stdout.strip()
        _consumer(work, tmp)
        _git(work, 'push', '-q', 'origin', 'main')
        r, head = _run(work, tmp)
        diag.append(f'case1 exit={r.returncode} shallow={shallow!r}')
        # The fixture must be the thing under test: a clone that quietly came
        # back full would make every case below pass for the wrong reason.
        results.append(('case 1: the fixture clone really is shallow',
                        shallow == 'true'))
        results.append(('case 1: the run reached the unlanded-work block',
                        'UNLANDED WORK' in r.stdout))
        # THE BUG ITSELF.
        results.append(('case 1: a fully-landed branch is NOT reported as '
                        'carrying unlanded commits',
                        'fully-landed' not in head))
        results.append(('case 1: and the scan says so affirmatively, rather '
                        'than falling silent',
                        'No branch carries unlanded work' in head))

    # CASE 2 -- deepening cannot rescue it. The tool must REFUSE, in words
    # that name the cause and the remedy.
    #
    # The origin here is itself a SHALLOW bare clone, so it is perfectly
    # reachable and simply has no deeper history to serve. Breaking the
    # origin outright was tried first and does not reach this code at all:
    # the freshness gate refuses the whole run before the branch scan, which
    # is correct behaviour and the wrong fixture.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        deep, mid, work = tmp / 'deep', tmp / 'mid', tmp / 'work'
        shutil.copytree(seeded, deep, symlinks=True)
        subprocess.run(['git', 'clone', '-q', '--bare', '--depth', '1',
                        f'file://{deep}', str(mid)], capture_output=True)
        _git(mid, 'fetch', '-q', '--depth=1', 'origin',
             '+refs/heads/fully-landed:refs/heads/fully-landed')
        subprocess.run(['git', 'clone', '-q', f'file://{mid}', str(work)],
                       capture_output=True)
        _git(work, 'fetch', '-q', 'origin',
             '+refs/heads/*:refs/remotes/origin/*')
        _consumer(work, tmp)
        _git(work, 'push', '-q', 'origin', 'main')
        r, head = _run(work, tmp)
        diag.append(f'case2 exit={r.returncode}')
        results.append(('case 2: the unmeasurable branch is reported at all',
                        'fully-landed' in head))
        results.append(('case 2: it is named as undetermined, not counted',
                        'COULD NOT DETERMINE' in head))
        # ASSERT THE MESSAGE, not merely the absence of the wrong one --
        # silence satisfies "no fabricated count" just as well, and silence
        # is the other way this fails.
        results.append(('case 2: the reason is the unreachable merge base',
                        'no merge base' in head))
        results.append(('case 2: the remedy is a bounded deepen',
                        '--depth=5000' in head))
        results.append(('case 2: no count of unlanded commits is invented',
                        'commit(s) with no patch-equivalent' not in head))
        # The false all-clear is the failure this check exists for.
        results.append(('case 2: the all-clear is NOT printed alongside an '
                        'unmeasurable branch',
                        'No branch carries unlanded work' not in head))


def check_doc_currency_finds_a_stale_document():
    """The documentation-currency sweep must find a document its subject
    outran, and must not invent one (practice: change-updates-its-docs).

    WHY EACH CASE IS HERE. The sweep is the backstop for a rule that lives
    in a person's habits, so a version of it that always says "none" is
    indistinguishable from a repository whose documents are all current --
    and would be believed, because that is the reassuring answer.

    THE ONE THAT MATTERS IS CASE 2, and it is built with the commits in a
    deliberate order: the document is committed FIRST, the thing it
    describes SECOND. Reverse those two and every implementation passes,
    including one that never compares timestamps at all. Case 1 is the
    unplanted control for it -- the same fixture with the second commit
    absent -- and case 1 alone does NOT discriminate, for the same reason.

    CASE 3 covers the half that fails silently in the real world: a spoken
    command nobody wrote down. The fixture plants a practice defining a
    capitalized phrase and a page that does not contain it. A run that only
    checks timestamps passes cases 1 and 2 and fails this one.

    CASE 6 is the shallow-clone reflex this repository has been bitten by
    four times: an unanswerable history must read UNKNOWN, never "current".
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'vdc_doc', ROOT / 'tools' / 'very_deep_check.py')
    vdc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(vdc)
    finally:
        sys.path.pop(0)

    if not hasattr(vdc, '_doc_currency'):
        check('the documentation-currency sweep discriminates '
              '(0 of 7 stated cases reached)', False,
              'very_deep_check.py has no _doc_currency -- nothing compares a '
              'document against what it describes')
        return

    def git(cwd, *args, check_rc=True):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True, env=env)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def build(tmp, with_later_change, page_text, practice_text):
        repo = pathlib.Path(tmp) / 'repo'
        (repo / 'documentation').mkdir(parents=True)
        (repo / 'practices').mkdir()
        (repo / 'tools').mkdir()
        git(repo.parent, 'init', '-q', str(repo))
        git(repo, 'config', 'user.email', 'harness@example.com')
        git(repo, 'config', 'user.name', 'Fixture')
        (repo / 'practices' / 'zzz-command.md').write_text(
            practice_text, encoding='utf-8')
        (repo / 'tools' / 'doc_coverage.json').write_text(json.dumps({
            'documents': {
                'documentation/PAGE.md': {
                    'describes': ['practices/zzz-command.md'],
                    'why': 'fixture',
                    'must_mention': 'spoken-commands',
                },
            },
            'must_mention': {'spoken-commands': {'why': 'fixture'}},
        }), encoding='utf-8')
        (repo / 'documentation' / 'PAGE.md').write_text(page_text,
                                                        encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'page and practice together')
        if with_later_change:
            # The ONLY thing that separates case 1 from case 2, and it has to
            # be a genuinely later commit: --date alone does not move %ct.
            time.sleep(1.1)
            (repo / 'practices' / 'zzz-command.md').write_text(
                practice_text + '\nA later change nobody wrote up.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'change the practice, leave the page')
        return repo

    GOOD_PRACTICE = (
        '---\nslug:        zzz-command\ntitle:       A command\n'
        'tier:        on-demand\nseverity:    default\n'
        'applies_to:  ["**"]\noccasion:    "testing"\n'
        'index_clause: "a fixture"\nchecked_by:  null\n'
        'defines:     []\ncommand:     {"Zorp It": "do the thing"}\n'
        'status:      active\nsupersedes:  []\n'
        'overrides:   null\nadded:       null\napproved_by: "fixture"\n'
        '---\n\n## Rule\nSay it.\n')
    PAGE_WITH = '# Page\n\nSay **Zorp It** to do the thing.\n'
    PAGE_WITHOUT = '# Page\n\nThis page teaches you nothing.\n'

    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, False, PAGE_WITH, GOOD_PRACTICE)
        found, notes = vdc._doc_currency(repo)
        cases.append(('a page committed WITH its subject reports no REVIEW',
                      not any('REVIEW' in f for f in found),
                      str(found)[:400]))
        cases.append(('and the spoken command it does carry is reported as '
                      'present, not silently skipped',
                      any('Zorp It' in n for n in notes), str(notes)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, True, PAGE_WITH, GOOD_PRACTICE)
        found, _notes = vdc._doc_currency(repo)
        review = [f for f in found if 'REVIEW' in f]
        cases.append(('a page whose subject changed AFTER it reports REVIEW',
                      len(review) == 1, str(found)[:400]))
        cases.append(('and the finding names the commit that outran it, so a '
                      'reader can go and look',
                      bool(review) and 'change the practice, leave the page'
                      in review[0], str(review)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, False, PAGE_WITHOUT, GOOD_PRACTICE)
        found, _notes = vdc._doc_currency(repo)
        cases.append(('a spoken command missing from the page that teaches '
                      'the vocabulary is a FINDING, even with every '
                      'timestamp current',
                      any('Zorp It' in f and 'FINDING' in f for f in found),
                      str(found)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        # An empty repository: git can date nothing. UNKNOWN, never current.
        repo = pathlib.Path(tmp) / 'bare'
        (repo / 'documentation').mkdir(parents=True)
        (repo / 'tools').mkdir()
        git(repo.parent, 'init', '-q', str(repo))
        (repo / 'tools' / 'doc_coverage.json').write_text(json.dumps({
            'documents': {'documentation/PAGE.md': {
                'describes': [], 'why': 'fixture'}}}), encoding='utf-8')
        (repo / 'documentation' / 'PAGE.md').write_text('# Page\n',
                                                        encoding='utf-8')
        found, notes = vdc._doc_currency(repo)
        cases.append(('a document git cannot date reads as UNKNOWN or '
                      'uncommitted, never as current',
                      any('documentation/PAGE.md' in n for n in notes),
                      str(notes)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / 'noreg'
        repo.mkdir()
        found, notes = vdc._doc_currency(repo)
        cases.append(('a repository with no registry says so and finds '
                      'nothing, rather than crashing',
                      found == [] and any('doc_coverage.json' in n
                                          for n in notes),
                      str((found, notes))[:400]))

    ok = all(c[1] for c in cases)
    check(f'the documentation-currency sweep discriminates '
          f'({len(cases)} stated cases, each built so a sweep that skipped '
          f'the comparison would fail it)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


def check_template_freshness_reads_the_skeleton_correctly():
    """The reverse-direction skeleton check must not invent gaps, and must
    not call one repo's habit a finding (practice: very-deep-check).

    WHY IT EXISTS. `precedent_bootstrap_source.verify()` reads a skeleton and
    asks whether a real source has everything in it. Nothing asked the
    reverse until 2026-09-08, so a skeleton could drift below reality and a
    newly bootstrapped source would be created missing something every real
    one has. That is how the individual skeleton came to ship no
    `identity.json` -- the file that decides whether the commit hook ENFORCES
    an author-date offset or merely guesses one.

    TWO FAILURES ON ITS FIRST RUN, both asserted here because both make the
    section useless in opposite ways:

      1. It reported `config.json.sample` as a gap. The skeleton plainly
         ships that file -- the scan stripped the `.sample` suffix and
         recorded only `config.json`, while a real source keeps the sample
         name verbatim. A check that flags what the template already has
         teaches the reader to skim it.
      2. Everything was labelled FINDING, including a level with exactly ONE
         resolved source. One repo is not evidence of a shape, and a
         permanent list of that repo's own working documents is the same
         noise problem from the other side.
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'vdc', ROOT / 'tools' / 'very_deep_check.py')
    vdc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(vdc)
    finally:
        sys.path.pop(0)

    results = []
    if not hasattr(vdc, '_template_freshness'):
        check('the template-freshness scan reads the skeleton correctly '
              '(0 of 5 stated cases reached)', False,
              'very_deep_check.py has no _template_freshness -- the reverse '
              'direction is not checked at all')
        return

    with tempfile.TemporaryDirectory() as tmp:
        # A source carrying exactly what the individual skeleton ships,
        # suffixes and all, plus one extra file.
        src = pathlib.Path(tmp) / 'a-source'
        (src / 'practices').mkdir(parents=True)
        skel = ROOT / 'templates' / 'practice-set-individual'
        for f in skel.iterdir():
            if f.is_file():
                (src / f.name).write_text('x')
        (src / 'ONLY_HERE.md').write_text('x')

        out = vdc._template_freshness(
            [{'level': 'individual', 'name': 'fixture', 'path': str(src)}])
        joined = ' | '.join(out)

        # THE FALSE POSITIVE.
        results.append(('a file the skeleton ships under its own '
                        '.sample/.template name is NOT reported as a gap',
                        'config.json' not in joined))
        # One source is not evidence.
        results.append(('a level with one source is reported as a note, not '
                        'a FINDING', 'FINDING' not in joined))
        results.append(('and says plainly that one source proves nothing',
                        'only ONE source' in joined))
        # It still has to SAY something -- silence would pass the two cases
        # above just as well, and silence is how the gap survived.
        results.append(('the file the skeleton really lacks is still named',
                        'ONLY_HERE.md' in joined))

        # OPTIONAL CONTENT is not shape. Two sources that each declare a
        # reply rule both carry reply_check.json; a missing one means "no
        # requirement", so the skeleton correctly ships none. Control: a
        # file both carry that IS shape-like is still a FINDING, so the
        # silence above is the exemption and not a blind scan.
        two = []
        for name in ('one', 'two'):
            s = pathlib.Path(tmp) / name
            (s / 'practices').mkdir(parents=True)
            (s / 'reply_check.json').write_text('[]')
            (s / 'BOTH_HAVE.md').write_text('x')
            two.append({'level': 'shared', 'name': name, 'path': str(s)})
        out2 = ' | '.join(vdc._template_freshness(two))
        results.append(('reply_check.json that two sets carry is not a '
                        'template gap', 'reply_check.json' not in out2))
        results.append(('a file two sets carry that the skeleton lacks is '
                        'still a FINDING (control)',
                        'FINDING' in out2 and 'BOTH_HAVE.md' in out2))

    # The gap that motivated all of this must actually be closed.
    results.append(('the individual skeleton now ships an identity file',
                    any(f.name.startswith('identity.json')
                        for f in (ROOT / 'templates' /
                                  'practice-set-individual').iterdir())))

    failed = [n for n, ok in results if not ok]
    check(f'the template-freshness scan reads the skeleton correctly '
          f'({len(results)} stated cases)', not failed,
          '; '.join(failed) + (f' [scan said: {joined!r}]' if failed else ''))


def check_todo_and_gotcha_sweeps():
    """very_deep_check.py's two Part 3 sweeps -- _open_item_sweep and
    _gotcha_retirement_candidates -- against planted fixtures
    (fixture-owns-its-state: each fixture writes every field its own
    assertion depends on)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    import precedent_time as ptime

    today = ptime.today(ROOT)

    def todo_item(slug, **fields):
        base = dict(kind='analysis', status='open', disposition='wait',
                   remind_on='null', blocked_on='null', batch='null',
                   decision='null', decision_strength='null',
                   waiting_on='null', noted=today, closed='null')
        base.update(fields)
        lines = ['---', f'slug:              {slug}']
        for k in ('kind', 'domain', 'severity', 'status', 'disposition',
                 'remind_on', 'blocked_on', 'batch', 'decision',
                 'decision_strength', 'waiting_on', 'noted', 'closed'):
            v = base.get(k, 'null')
            lines.append(f'{k}:{"":<{18-len(k)}} {v}')
        lines += ['---', '', '## What', '', f'**{slug} title.**', '']
        return '\n'.join(lines)

    def make_repo(todo_files=None, gotcha_files=None):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-sweep-'))
        for name, content in (todo_files or {}).items():
            (d / 'todo').mkdir(exist_ok=True)
            (d / 'todo' / name).write_text(content, encoding='utf-8')
        for name, content in (gotcha_files or {}).items():
            (d / 'gotchas').mkdir(exist_ok=True)
            (d / 'gotchas' / name).write_text(content, encoding='utf-8')
        return d

    cases = []

    d = make_repo(todo_files={
        'todo-2026-01-01-unblocked.md': todo_item(
            'todo-2026-01-01-unblocked', noted='2026-01-01'),
    })
    out = vdc._open_item_sweep(d)
    cases.append(('an open, kind:analysis item with no blocked_on is listed '
                  'as UNBLOCKED', any('UNBLOCKED' in o for o in out), repr(out)))
    shutil.rmtree(d)

    d = make_repo(todo_files={
        'todo-2026-01-01-blocked.md': todo_item(
            'todo-2026-01-01-blocked', noted='2026-01-01',
            blocked_on='"see `tools/nonexistent_tool.py`"'),
    })
    out = vdc._open_item_sweep(d)
    cases.append(('...and one WITH a blocked_on is not', not any(
        'UNBLOCKED' in o and 'blocked' in o for o in out), repr(out)))
    cases.append(('a blocked_on naming a file that is not in the tree is '
                  'flagged', any('GONE' in o for o in out)
                  and any('nonexistent_tool' in o for o in out), repr(out)))
    shutil.rmtree(d)

    d = make_repo(todo_files={
        'todo-2026-01-01-real.md': todo_item(
            'todo-2026-01-01-real', noted='2026-01-01',
            blocked_on='"see `AGENTS.md`"'),
    })
    (d / 'AGENTS.md').write_text('# real file\n', encoding='utf-8')
    out = vdc._open_item_sweep(d)
    cases.append(('...and one naming a file that DOES exist is not '
                  '(negative control for the same signal)',
                  not any('GONE' in o for o in out), repr(out)))
    shutil.rmtree(d)

    d = make_repo(todo_files={
        'todo-2026-01-01-overdue.md': todo_item(
            'todo-2026-01-01-overdue', noted='2026-01-01',
            disposition='ask', remind_on='"2020-01-01"'),
    })
    out = vdc._open_item_sweep(d)
    cases.append(('a disposition: ask item whose remind_on is years past is '
                  'reported as a Reminder well past due',
                  any('OVERDUE' in o.upper() or 'PAST DUE' in o.upper()
                      for o in out), repr(out)))
    shutil.rmtree(d)

    d = make_repo(todo_files={
        'todo-2026-01-01-done.md': todo_item(
            'todo-2026-01-01-done', noted='2026-01-01', status='done',
            closed='"2026-01-02"'),
    })
    out = vdc._open_item_sweep(d)
    cases.append(('a status: done item is not surfaced by any signal -- the '
                  'sweep reads OPEN items only',
                  out == [] or all('done' not in o for o in out), repr(out)))
    shutil.rmtree(d)

    GOTCHA_BASE = ('---\nslug: {slug}\nstatus: {status}\nnoted: 2026-01-01\n'
                  'severity: null\nretired: {retired}\n'
                  'retires_when: {rw}\n---\n## Symptom\nx\n')
    d = make_repo(gotcha_files={
        'gotcha-2026-01-01-a.md': GOTCHA_BASE.format(
            slug='gotcha-2026-01-01-a', status='live', retired='null',
            rw='"a check refuses this"'),
    })
    out = vdc._gotcha_retirement_candidates(d)
    cases.append(('a live gotcha with retires_when set is surfaced',
                  any('gotcha-2026-01-01-a' in o for o in out), repr(out)))
    shutil.rmtree(d)

    d = make_repo(gotcha_files={
        'gotcha-2026-01-01-b.md': GOTCHA_BASE.format(
            slug='gotcha-2026-01-01-b', status='live', retired='null',
            rw='null'),
    })
    out = vdc._gotcha_retirement_candidates(d)
    cases.append(('...and one with retires_when still null is not '
                  '(negative control -- this is the state every migrated '
                  'entry starts in)', out == [], repr(out)))
    shutil.rmtree(d)

    d = make_repo(gotcha_files={
        'gotcha-2026-01-01-c.md': GOTCHA_BASE.format(
            slug='gotcha-2026-01-01-c', status='retired', retired='"2026-01-02"',
            rw='"nothing has hit this since 2026-01-01"'),
    })
    out = vdc._gotcha_retirement_candidates(d)
    cases.append(('an ALREADY-retired gotcha is not surfaced even with '
                  'retires_when set -- there is nothing left to judge',
                  out == [], repr(out)))
    shutil.rmtree(d)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the open-item and gotcha-retirement sweeps report the signals '
          f'Part 3 names, and no more ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


