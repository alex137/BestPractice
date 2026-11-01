# The harness tests for checks that fit no one area
#
# tools/harness/vh_misc.py -- part of the verification harness:
# checks that fit no one area.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_owned_paths_previews_the_boundary():
    """precedent_owned_paths.py names every touched owned path with its
    owner, says the rest is the contributor's, and never reads a missing
    CODEOWNERS as a clean change.

    The tool is spec/CONTRIBUTOR_ACCESS.md's finding 6 (2026-09-14): the
    contributor cannot see the CODEOWNERS line, so the session says before
    the pull request what will wait for review. Each case asserts the words
    the tool prints for THAT case, not that something was printed (practice:
    control-asserts-which-failure); the no-CODEOWNERS case is the one that
    matters most, since a boundary that is missing must not render as a
    change that is clean (practice: fail-gracefully)."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_owned_paths as pop

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-owned-'))
    cases = []

    def git(*args):
        return subprocess.run(['git', '-C', str(tmp), '-c', 'user.name=fixture',
                               '-c', 'user.email=fixture@example.com', *args],
                              capture_output=True, text=True)

    try:
        git('init', '-q')
        git('checkout', '-q', '-b', 'main')
        (tmp / '.github').mkdir()
        (tmp / 'docs').mkdir()
        (tmp / '.github' / 'CODEOWNERS').write_text(
            '/.github/ @maint\n/settings.md @maint\n*.secret @maint @other\n'
            '/docs/generated/ @maint\n/docs/generated/free.md\n', encoding='utf-8')
        (tmp / 'docs' / 'hello.md').write_text('hi\n', encoding='utf-8')
        (tmp / 'settings.md').write_text('s\n', encoding='utf-8')
        (tmp / 'precedent.json').write_text('{"base_branch": "main"}', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'init')
        git('checkout', '-q', '-b', 'work')
        (tmp / 'docs' / 'hello.md').write_text('hi\nmore\n', encoding='utf-8')
        (tmp / 'settings.md').write_text('s\nx\n', encoding='utf-8')
        (tmp / 'docs' / 'key.secret').write_text('k\n', encoding='utf-8')
        (tmp / 'docs' / 'generated').mkdir()
        (tmp / 'docs' / 'generated' / 'free.md').write_text('f\n', encoding='utf-8')
        (tmp / 'docs' / 'generated' / 'index.md').write_text('i\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'work')

        r = pop.assess(tmp, base='main')
        owned = {p: (o, pat) for p, o, pat in r['owned']}
        cases.append(('an owned path is named with its owner and the rule that owns it',
                      owned.get('settings.md') == (['@maint'], '/settings.md'), str(owned)))
        cases.append(('a basename pattern owns a file at any depth, with every listed owner',
                      owned.get('docs/key.secret') == (['@maint', '@other'], '*.secret'), str(owned)))
        cases.append(('a directory pattern owns what is under it',
                      'docs/generated/index.md' in owned, str(owned)))
        cases.append(('the LAST matching rule wins, so a later line with no owner frees a file',
                      'docs/generated/free.md' in r['free'], str(r['free'])))
        cases.append(('an unowned document is reported free',
                      'docs/hello.md' in r['free'], str(r['free'])))
        words = pop.plain_words(r)
        cases.append(('the sentence names who has to look and which files, and offers the split',
                      '@maint and @other have to look' in words and 'settings.md' in words
                      and 'yours to merge' in words and 'go in on their own now' in words, words))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pop.main(['--repo', str(tmp), '--base', 'main', '--check'])
        cases.append(('--check exits 1 when an owned path is touched, and the report names it',
                      code == 1 and 'OWNED  settings.md' in out.getvalue(), out.getvalue()))

        # A docs-only change: the sentence says it is theirs, and --check passes.
        git('checkout', '-q', 'main')
        git('checkout', '-q', '-b', 'docs-only')
        (tmp / 'docs' / 'hello.md').write_text('hi\nz\n', encoding='utf-8')
        git('commit', '-q', '-am', 'docs')
        r = pop.assess(tmp, base='main')
        words = pop.plain_words(r)
        cases.append(('a documents-only change is reported as the contributor\'s to merge',
                      not r['owned'] and 'yours to merge' in words
                      and 'nothing here needs anyone else' in words, words))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pop.main(['--repo', str(tmp), '--base', 'main', '--check'])
        cases.append(('--check exits 0 on a documents-only change', code == 0, out.getvalue()))

        # An uncommitted edit is in the preview too.
        (tmp / 'settings.md').write_text('s\nuncommitted\n', encoding='utf-8')
        r = pop.assess(tmp, base='main')
        cases.append(('an uncommitted edit to an owned path is in the preview',
                      any(p == 'settings.md' for p, _, _ in r['owned']), str(r['owned'])))
        git('checkout', '-q', '--', 'settings.md')

        # No base ref: the preview says so instead of reporting a clean change.
        r = pop.assess(tmp, base='no-such-ref')
        cases.append(('an unresolvable base is said out loud, never read as clean',
                      r['base'] is None and 'no base ref resolved' in r['note']
                      and 'NOT in this preview' in r['note'], r['note']))

        # A pattern the tool cannot match is reported, not skipped.
        (tmp / '.github' / 'CODEOWNERS').write_text('/settings.md @maint\n!/never.md @x\n',
                                                     encoding='utf-8')
        r = pop.assess(tmp, base='main')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pop.report(r)
        cases.append(('an untranslatable pattern is reported by line, never silently skipped',
                      r['untranslatable'] == [('!/never.md', 2)]
                      and "pattern '!/never.md' is not one this tool can match" in out.getvalue(),
                      out.getvalue()))

        # THE ONE THAT MATTERS: no CODEOWNERS is NO BOUNDARY, not a clean change.
        (tmp / '.github' / 'CODEOWNERS').unlink()
        r = pop.assess(tmp, base='main')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pop.report(r)
        cases.append(('a missing CODEOWNERS is reported as NO BOUNDARY, never as a clean change',
                      r['codeowners'] is None and 'NO BOUNDARY' in out.getvalue()
                      and 'boundary is missing, not that the change is clean' in out.getvalue(),
                      out.getvalue()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_owned_paths.py previews the CODEOWNERS boundary in the '
          f'contributor\'s words ({len(cases)} stated cases: owner named, basename '
          f'pattern, directory pattern, last-match-wins, free file, the sentence, '
          f'--check red, docs-only sentence, --check green, uncommitted edit, '
          f'unresolvable base, untranslatable pattern, no CODEOWNERS)',
          not bad, '; '.join(f"{n}: {d}" for n, d in bad))


def check_session_trailer_check_ships_with_the_engine():
    """The commit-trailer check is the engine's own, not a shared set's.

    Until 2026-10-06 check_session_trailer.py lived only in the
    repository-maintenance set, so folding that set away would have stopped
    every repository checking trailers, silently (very deep check,
    2026-10-05). Morgan, 2026-10-06: the link back to the session goes on
    every commit, except where there is none to give -- a person committing
    without an AI assistant, or a link hidden from the session -- and then
    the trailer says so. Planted, against the engine's own copy run on a
    fixture repository: a commit with no trailer fires; `Session:`,
    `Claude-Session:` and an explicit `Session: none available (...)` pass;
    a commit origin already has is not judged again."""
    import shutil as _sh
    import tempfile as _tf
    script = ROOT / 'tools' / 'checks' / 'check_session_trailer.py'
    cases = []
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-trailer-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')
    env.pop('PRECEDENT_CHECK_RANGE', None)

    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], env=env,
                              capture_output=True, text=True)

    def check_says():
        r = subprocess.run([sys.executable, str(script)], cwd=str(repo),
                           env=dict(env, PRECEDENT_CHECK_ROOT=str(repo)),
                           capture_output=True, text=True)
        return r.returncode

    def commit(name, message):
        (repo / name).write_text(name, encoding='utf-8')
        git('add', name)
        git('commit', '-qm', message)

    try:
        cases.append(('the check ships in the engine\'s own tools/checks/',
                      script.is_file()))
        origin = fx / 'origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(origin)], env=env)
        repo = fx / 'repo'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], env=env)
        git('remote', 'add', 'origin', str(origin))
        # A consumer of this engine's universal catalogue and nothing else,
        # so "in force" is the catalogue's answer, not the person's sets.
        env['PRECEDENT_USER_CONFIG'] = str(fx / 'no-user-config.json')
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}),
            encoding='utf-8')
        git('add', 'precedent.json')
        commit('a', 'first\n\nSession: https://claude.ai/code/session_x')
        git('push', '-q', 'origin', 'main')
        commit('b', 'no trailer at all')
        cases.append(('a commit with no trailer fires', check_says() == 1))
        git('commit', '-q', '--amend', '-m',
            'by hand\n\nSession: none available (committed without an AI assistant)')
        cases.append(('an explicit "none available" trailer passes -- the '
                      'exception Morgan named', check_says() == 0))
        git('commit', '-q', '--amend', '-m',
            'from Claude Code\n\nClaude-Session: https://claude.ai/code/session_y')
        cases.append(('Claude-Session: passes', check_says() == 0))
        git('commit', '-q', '--amend', '-m', 'no trailer again')
        git('push', '-q', 'origin', 'main')
        cases.append(('a commit origin already has is not judged again',
                      check_says() == 0))
        # The revert exemption lives in session-trailer's Detail since
        # 2026-10-17, its old practice deduplicated to it: the check must
        # still skip a revert, which it stopped doing when it asked only
        # for the old slug.
        sha = git('rev-parse', 'HEAD').stdout.strip()
        commit('c', f'Revert "no trailer again"\n\nThis reverts commit {sha}.')
        cases.append(('THE CASE: a revert with no trailer passes where '
                      'session-trailer is in force', check_says() == 0))
        git('commit', '-q', '--amend', '-m', 'undo the last change by hand')
        cases.append(('CONTROL: an undo made by hand, with its own message, '
                      'still needs the trailer', check_says() == 1))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'the commit-trailer check ships with the engine and judges what a '
          f'push carries ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_upholds_is_a_listed_field():
    """`upholds:` is a field the practice format lists, so a practice carrying
    it raises no warning. A project repository linked its practices to its
    risk page with it before the format listed it, and every check warned
    (Morgan, 2026-10-06: "we want to eliminate warnings"). A field the
    format still does not list goes on warning, so the case is not a
    blanket pass."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import frontmatter_yaml as _fy
    base = ('---\nslug: x\ntitle: X\ntier: on-demand\nseverity: default\n'
            'defines: []\n{extra}status: active\n---\n## Rule\nx\n')
    with_upholds = base.format(extra='upholds: ["spec/RISK.md"]\n')
    with_unknown = base.format(extra='zz_not_a_field: 1\n')
    cases = [
        ('a practice carrying upholds: lists no unknown field',
         not _fy.unlisted_fields(with_upholds)),
        ('...and is in field order', not _fy.field_order_problem(with_upholds)),
        ('a field the format does not list is still reported',
         bool(_fy.unlisted_fields(with_unknown))),
        ('the format spec lists it',
         'upholds:' in (ROOT / 'spec' / 'PRACTICE_FORMAT.md').read_text(encoding='utf-8')),
    ]
    # A repository's OWN fields (2026-10-06): declared in precedent.json, never
    # reported, sorted after the spec's fields; a declared name the spec
    # lists is ignored, so the spec's meaning wins.
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'precedent.json').write_text(json.dumps(
            {'own_frontmatter_fields': ['zz_not_a_field', 'status']}), encoding='utf-8')
        own = _fy.own_fields(repo)
        cases += [
            ('a field precedent.json declares as its own is not reported',
             own == ('zz_not_a_field',) and not _fy.unlisted_fields(with_unknown, own)),
            ('...and sorts after every listed field without a complaint',
             not _fy.field_order_problem(base.format(extra='').replace(
                 'status: active\n', 'status: active\nzz_not_a_field: 1\n'))),
            ('...while one it does not declare is still reported',
             bool(_fy.unlisted_fields(with_unknown.replace('zz_not_a_field', 'zz_other'), own))),
            ('a repository with no precedent.json declares nothing',
             _fy.own_fields(repo / 'nowhere') == ()),
        ]
    bad = [n for n, ok in cases if not ok]
    check(f'upholds: is a listed practice field, and a repository may declare '
          f'its own ({len(cases)} stated cases)', not bad, '; '.join(bad))
def check_model_audit_changed_selects_only_what_a_change_reaches():
    """model_audit --changed audits only the models a change can reach: a
    manifest or blocklist change selects none, an engine no model loads
    selects none, the engine a shim loads by path selects the model behind
    that shim, and memo plumbing the host lists selects none (2026-10-02: a
    consumer's merges carried vendored engine files under tools/ that no
    model loads, and each re-audited all 59 of its models). The engine's
    own self-check builds the scratch repository and states the cases.

    Negative control, measured 2026-10-02: with the old rule (any .py
    changed under tools/ or process/ audits everything) the self-check
    fails on the unloaded engine and the path-loaded one."""
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'model_audit.py'),
                        '--self-check'], capture_output=True, text=True, cwd=str(ROOT))
    out = r.stdout + r.stderr
    return (r.returncode == 0 and 'self-check OK' in out, 'model_audit --self-check',
            out[-1200:])


def check_upstream_fix_sets_up_the_fix_in_the_source():
    """tools/upstream_fix.py PATH, the one command the doc_lint finding above
    names: on a planted source repo, its clone and a consumer vendoring one
    file, it opens a branch in the clone off the landing branch, never edits
    the copy, refuses a file of the consumer's own and a dirty clone."""
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'upstream_fix.py'),
                        '--self-check'], capture_output=True, text=True,
                       env=_fixture_git_env())
    check('upstream_fix.py sets up the fix in the source (its --self-check)',
          r.returncode == 0, failure_detail(r.stdout + r.stderr, 600))


def check_seeded_prompt_gate_refuses_an_unlabelled_prompt():
    """seeded-prompt-gate.sh (practice: seeded-prompt-names-its-origin).

    Added 2026-09-23, after a session put a message into another session's
    live conversation with its session link at the END, and the receiving
    session could not tell it from the person typing. The hook refuses a
    session-creating or session-messaging call whose text does not name a
    session id on its first line. Asserted both ways: the refusal fires on
    the incident's own shape, and every case that must pass does -- a gate
    that refuses ordinary work is a gate somebody switches off.
    """
    import shutil
    import subprocess
    hook = ROOT / 'tools' / 'seeded-prompt-gate.sh'
    if not hook.exists():
        return (False, '', f'{hook} does not exist')
    if not shutil.which('jq'):
        return (True, 'jq absent -- the hook fails open, nothing to assert', '')

    def decision(payload, env_extra=None):
        env = {k: v for k, v in os.environ.items()
               if k != 'CLAUDE_CODE_REMOTE_SESSION_ID'}
        env.update(env_extra or {})
        r = subprocess.run(['bash', str(hook)], input=json.dumps(payload)
                           if not isinstance(payload, str) else payload,
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            return f'exit {r.returncode}'
        if not r.stdout.strip():
            return 'allow'
        try:
            out = json.loads(r.stdout)['hookSpecificOutput']
        except (ValueError, KeyError):
            return 'unparseable'
        return out.get('permissionDecision', 'allow'), out.get(
            'permissionDecisionReason', '')

    header = ('Sent automatically by the session "t" (session_01AbCdEfGh) '
              '-- https://claude.ai/code/session_01AbCdEfGh. Nobody typed this.')
    cases = []
    d = decision({'tool_name': 'mcp__Claude_Code_Remote__create_session',
                  'tool_input': {'prompt': 'Do step 1 of the migration.\n'
                                           'From session_01AbCdEfGh'}})
    cases.append(('the incident shape -- session named last -- is refused',
                  isinstance(d, tuple) and d[0] == 'deny'))
    cases.append(('the refusal hands back the line to use',
                  isinstance(d, tuple) and 'Nobody typed this' in d[1]))
    d = decision({'tool_name': 'mcp__Claude_Code_Remote__send_later',
                  'tool_input': {'message': 'check CI'}},
                 {'CLAUDE_CODE_REMOTE_SESSION_ID': 'cse_01XyZ12345'})
    cases.append(('a remote session is handed its own session id',
                  isinstance(d, tuple) and 'session_01XyZ12345' in d[1]))
    for tool, field in (('fire_trigger', 'text'), ('create_trigger', 'prompt'),
                        ('update_trigger', 'prompt'), ('send_later', 'message')):
        d = decision({'tool_name': f'mcp__any-server__{tool}',
                      'tool_input': {field: 'merge it'}})
        cases.append((f'{tool} without a header is refused, whatever the '
                      f'server is called',
                      isinstance(d, tuple) and d[0] == 'deny'))
    must_pass = [
        ('a header on the first line passes, after blank lines',
         {'tool_name': 'mcp__S__create_session',
          'tool_input': {'prompt': '\n  ' + header + '\nDo it.'}}),
        ('a call carrying no text passes',
         {'tool_name': 'mcp__S__update_trigger',
          'tool_input': {'trigger_id': 't', 'enabled': False}}),
        ('an unrelated tool passes',
         {'tool_name': 'Bash', 'tool_input': {'command': 'echo hi'}}),
        ('an unparseable payload passes (fail open)', 'not json'),
    ]
    for name, payload in must_pass:
        cases.append((name, decision(payload) == 'allow'))
    failed = [n for n, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_routing_audit_coverage():
    """routing_audit.py's coverage() -- the mechanical half of the routing
    audit (practices/routing-audit.md) -- against real practices already in
    the catalogue, not a synthetic fixture: PRACTICES_DIR is hardcoded in
    routing_audit.py (it reads the real tree, deliberately, the same way
    this file's own PRACTICES_DIR is), so the planted case is choosing real
    judgment-only practices with known narrow globs and asserting on their
    known, checkable behavior -- the checkable-gets-checked discipline
    applied to the routing audit's own tool, per spec/UNBUILT_PLAN_ITEMS.md
    ("Part 2"), which found this half had never actually been exercised.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_ra', ROOT / 'tools' / 'routing_audit.py')
    ra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ra)

    practices = {slug: globs for slug, globs, _rule, _f in ra.judgment_only_practices()}
    problems = []

    def want(slug):
        if slug not in practices:
            problems.append(f"fixture practice {slug!r} is no longer judgment-only "
                            f"or no longer active -- pick a replacement fixture")
            return False
        return True

    # A narrow glob that should match: lead-with-what-it-is names README.md
    # explicitly (not '**').
    if want('lead-with-what-it-is'):
        hits = {slug for slug, _path in ra.coverage(['README.md'])}
        if 'lead-with-what-it-is' not in hits:
            problems.append("coverage(['README.md']) missed lead-with-what-it-is, "
                            "whose applies_to names README.md directly")

    # A file none of the narrow-glob fixtures should match -- catches a glob
    # implementation that over-matches (e.g. '**' leaking through, or a bad
    # path-matching call) as well as one that under-matches.
    unrelated_hits = {slug for slug, _path in ra.coverage(['tools/verify_harness.py'])}
    for slug in ('lead-with-what-it-is', 'pr-template-honest-gates', 'parallel-artifact-ledger'):
        if slug in practices and slug in unrelated_hits:
            problems.append(f"coverage(['tools/verify_harness.py']) false-positived "
                            f"on {slug}, whose applies_to does not match this path")

    # The practice's own stated design: applies_to: ['**'] carries no routing
    # signal (routing_audit.coverage() drops it deliberately -- "narrow = [g
    # for g in globs if g != '**']; if not narrow: continue") and must never
    # surface as a coverage hit for any file, even one everything matches.
    if want('registry-source-of-truth'):
        wildcard_hits = {slug for slug, _path in ra.coverage(['README.md', 'AGENTS.md'])}
        if 'registry-source-of-truth' in wildcard_hits:
            problems.append("coverage() surfaced registry-source-of-truth (applies_to: "
                            "['**']) as a hit -- '**' is not a routing signal and must "
                            "be excluded, per the tool's own docstring")

    # A glob scoped to a directory that does not include the probe file.
    if want('pr-template-honest-gates'):
        hits = {slug for slug, _path in ra.coverage(['.github/pull_request_template.md'])}
        if 'pr-template-honest-gates' not in hits:
            problems.append("coverage(['.github/pull_request_template.md']) missed "
                            "pr-template-honest-gates")

    check('routing audit coverage() matches narrow applies_to globs correctly, '
          'in both directions, and drops \'**\' as a non-signal (5 stated cases '
          'against real catalogue fixtures)',
          not problems, '; '.join(problems))


def check_detect_restated_fires():
    """`precedent_detect.py restated` (Stage 1's cross-source duplicate-Rule
    scan) had zero harness coverage before this deep-check pass -- a real
    run against all three real sources together (this repo, and both
    private sets, once populated) found nothing, which is consistent with
    there being no actual restatement today, but is indistinguishable from
    the detector being silently broken without a planted case that proves
    it still fires. Two throwaway sources, one practice each: a near-exact
    reword (should fire) and a genuinely unrelated Rule (should not)."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-detect-restated-'))

    def write_practice(path, slug, rule):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x"\ngates: []\n'
            f'index_clause: "x"\nchecked_by: null\ndefines: []\nstatus: active\n'
            f'supersedes: []\noverrides: null\nadded: 2026-09-02\n'
            f'approved_by: "harness, 2026-09-02"\nsource_practice_number: null\n'
            f'---\n## Rule\n{rule}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')

    try:
        src_a, src_b = tmp / 'source-a', tmp / 'source-b'
        write_practice(src_a / 'practices' / 'reworded-one.md', 'reworded-one',
                        'After any state-changing operation, check the state you '
                        'wanted, not that the command reported success.')
        write_practice(src_b / 'practices' / 'reworded-two.md', 'reworded-two',
                        'After any state changing operation check the state you '
                        'actually wanted, never just that the command reported success.')
        write_practice(src_b / 'practices' / 'unrelated.md', 'unrelated',
                        'Slide decks are built by the deck engine and delivered '
                        'as a viewable file attached to the same reply.')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_detect.py'),
                             'restated', '--against', f'{src_a},{src_b}'],
                            capture_output=True, text=True)
        out = r.stdout + r.stderr
        fires_on_reword = (r.returncode == 0 and "'reworded-one'" in out
                            and "'reworded-two'" in out and '1 pair' in out)
        silent_on_unrelated = "'unrelated'" not in out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    check('precedent_detect.py restated fires (2 stated cases: a genuine '
          'reword across sources is caught, an unrelated Rule in the same '
          'run is not)',
          fires_on_reword and silent_on_unrelated,
          f'fires_on_reword={fires_on_reword} silent_on_unrelated={silent_on_unrelated}')


def check_reach_key_self_check():
    """reach_key.py's own property checks: a change the solve can run moves
    the key, one it cannot does not -- functions, constants, import-time
    patches, and class methods one at a time (a method moves the key only
    when reached code names it), plus early cutoff through `stop`."""
    name = 'reach_key keys a solve on the code it can reach, a method at a time'
    tool = ROOT / 'tools' / 'reach_key.py'
    if not tool.is_file():
        not_applicable(name, 'tools/reach_key.py is absent')
        return
    p = subprocess.run([sys.executable, str(tool), '--self-check'], capture_output=True, text=True)
    check(name, p.returncode == 0 and 'PASS' in p.stdout, failure_detail((p.stdout + p.stderr).strip(), 400))


def check_content_record_self_check():
    """content_record.py's own property checks: a fresh record holds; a
    changed file, listing, existence or environment variable is each
    reported as moved; ignored names never count; the two text schemes
    are frozen to their literal digests."""
    name = 'content_record reports exactly what moved, under frozen schemes'
    tool = ROOT / 'tools' / 'content_record.py'
    if not tool.is_file():
        not_applicable(name, 'tools/content_record.py is absent')
        return
    p = subprocess.run([sys.executable, str(tool), '--self-check'], capture_output=True, text=True)
    check(name, p.returncode == 0 and 'OK' in p.stdout, failure_detail((p.stdout + p.stderr).strip(), 400))


def check_ledger_ignores_checkout_layout():
    """A fact taken where .git is a directory (a clone) holds where it is a
    file (a worktree), and the reverse: the repository's own .git entry says
    how it was checked out, never what the work read. Found 2026-10-07: a
    ledger written by a landing worktree re-ran every model in every clone,
    and rewrote itself, inside each full check."""
    name = 'a ledger fact holds across a clone and a worktree of the same tree'
    tool = ROOT / 'tools' / 'fact_ledger.py'
    if not tool.is_file():
        not_applicable(name, 'tools/fact_ledger.py is absent')
        return
    spec = importlib.util.spec_from_file_location('_fl_layout', tool)
    fl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fl)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / 'a.txt').write_text('one')
        (root / '.git').mkdir()
        led = fl.Ledger(root)
        f = led.make('doc.md', 'block', 's.py', 'code', b'out', [['x', '.git'], ['f', 'a.txt']])
        recorded = any(r[1] == '.git' for r in f['reads'])
        legacy = dict(f, reads=f['reads'] + [['x', '.git', 'dir']])
        (root / '.git').rmdir()
        (root / '.git').write_text('gitdir: elsewhere')
        held = fl.Ledger(root).reads_hold(f) and fl.Ledger(root).reads_hold(legacy)
        (root / 'a.txt').write_text('two')
        moved = not fl.Ledger(root).reads_hold(f)
    check(name, not recorded and held and moved,
          f'.git recorded: {recorded}; holds across the layouts: {held}; '
          f'a real change still fails it: {moved}')


def check_model_audit_ledger():
    """model_audit with a ledger audits each model in its own process and
    records a fact for a clean audit; a model whose fact holds is not run
    again, a change to its self-check or to a file it read runs it, and a
    failing audit is never recorded. A scratch repository with one model
    that counts its own runs."""
    name = 'model_audit skips a model whose clean audit still holds, and re-runs a changed one'
    engine = ROOT / 'tools' / 'model_audit.py'
    needs = [engine, ROOT / 'tools' / 'fact_ledger.py', ROOT / 'tools' / 'reach_key.py',
             ROOT / 'tools' / 'content_record.py']
    if not all(p.is_file() for p in needs):
        not_applicable(name, 'model_audit.py, fact_ledger.py, content_record.py or reach_key.py is absent')
        return
    import tempfile as _tf
    bad = []
    with _tf.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / '.git').mkdir()
        (d / 'tools').mkdir()
        for p in needs:
            shutil.copy2(p, d / 'tools' / p.name)
        (d / 'limit.txt').write_text('10\n')
        (d / 'model.py').write_text(
            'import os\n'
            'def value():\n'
            '    return 3\n'
            'def self_check():\n'
            '    open(os.path.join(os.path.dirname(__file__), "runs.log"), "a").write("x")\n'
            '    lim = int(open(os.path.join(os.path.dirname(__file__), "limit.txt")).read())\n'
            '    return [] if value() < lim else ["value over the limit"]\n')
        (d / 'shim.py').write_text(
            'import importlib.util, sys\n'
            'spec = importlib.util.spec_from_file_location("ma_engine", "tools/model_audit.py")\n'
            'e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)\n'
            'e.INSTRUMENTED = ["model.py"]\n'
            'e.LEDGER = "audit.jsonl"\n'
            'sys.exit(e.main())\n')

        def audit():
            p = subprocess.run([sys.executable, 'shim.py'], cwd=d, capture_output=True, text=True)
            return p.returncode

        def runs():
            f = d / 'runs.log'
            return len(f.read_text()) if f.is_file() else 0
        steps = [
            ('the first audit', lambda: None, True, 0),
            ('an unchanged tree', lambda: None, False, 0),
            ('a comment in the model', lambda: (d / 'model.py').write_text(
                '# a note\n' + (d / 'model.py').read_text()), False, 0),
            ('a function the self-check calls', lambda: (d / 'model.py').write_text(
                (d / 'model.py').read_text().replace('return 3', 'return 4')), True, 0),
            ('a file the self-check read (now failing)', lambda: (d / 'limit.txt').write_text('2\n'), True, 1),
            ('the same failing tree again', lambda: None, True, 1),
        ]
        n = 0
        for what, edit, should_run, should_fail in steps:
            edit()
            rc = audit()
            ran = runs() > n
            n = runs()
            if ran != should_run:
                bad.append(f'{what}: the model {"was" if ran else "was not"} audited')
            if bool(rc) != bool(should_fail):
                bad.append(f'{what}: the audit exited {rc}')
    check(name, not bad, '; '.join(bad))


def check_workflow_write_gate_refuses_api_writes():
    """practice: ci-workflow-approved, 2026-09-26. A session can write a file
    straight onto GitHub with a file-write tool, and no push gate sees it.
    workflow-write-gate.sh refuses that for a workflow file, on both tools,
    and lets every other file through."""
    import shutil
    hook = ROOT / 'tools' / 'workflow-write-gate.sh'
    cases = []
    if not shutil.which('jq'):
        check('workflow-write-gate.sh refuses a workflow written through '
              'the API -- NOT RUN: no jq here, and the hook fails open '
              'without it', True, '')
        return

    def run(payload):
        p = subprocess.run(['bash', str(hook)], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=60)
        return '"deny"' in p.stdout, p.stdout

    denied, out = run({'tool_name': 'mcp__github__create_or_update_file',
                       'tool_input': {'path': '.github/workflows/new.yml',
                                      'content': 'on: push'}})
    cases.append(('create_or_update_file on a workflow is refused, naming '
                  'the practice', denied and 'ci-workflow-approved' in out
                  and '.github/workflows/new.yml' in out))
    denied, out = run({'tool_name': 'mcp__github__push_files',
                       'tool_input': {'files': [
                           {'path': 'README.md', 'content': 'x'},
                           {'path': '.github/workflows/ci.yaml',
                            'content': 'on: push'}]}})
    cases.append(('push_files carrying one workflow among other files is '
                  'refused', denied and '.github/workflows/ci.yaml' in out))
    denied, _ = run({'tool_name': 'mcp__github__push_files',
                     'tool_input': {'files': [{'path': 'README.md'},
                                              {'path': 'docs/workflows.yml'}]}})
    cases.append(('CONTROL: ordinary files, even one named like a workflow '
                  'outside .github/workflows, pass', not denied))
    same = (ROOT / 'tools' / 'workflow-write-gate.sh')
    cases.append(("this repo runs the byte-identical copy it ships",
                  same.is_file() and same.read_bytes() == hook.read_bytes()))
    bad = [c[0] for c in cases if not c[1]]
    check(f'workflow-write-gate.sh refuses a workflow written straight onto '
          f'GitHub and passes everything else ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_philosophy_readme_lists_every_file():
    """philosophy/README.md's list names every file in philosophy/, and no other.

    The page was cut back to one sentence and that list on 2026-09-09, on
    Morgan's instruction, with "updated as the files are changed" as the
    standing requirement. A list that is a document's whole content and is
    maintained by hand is a list that goes stale the first time somebody
    adds a file in a hurry -- and the drift is invisible, because a missing
    entry looks exactly like a directory that never had that file.

    Set comparison, not order: the page orders by importance, which is a
    judgment no check should be holding an opinion about. The recipe at
    philosophy/doc-recipes/README.recipe.md is what this enforces.
    """
    d = ROOT / 'philosophy'
    readme = d / 'README.md'
    if not readme.is_file():
        not_applicable('philosophy README lists every file',
                       'philosophy/README.md does not exist -- not a pass')
        return
    on_disk = {p.name + ('/' if p.is_dir() else '')
               for p in d.iterdir() if p.name != 'README.md'}
    text = readme.read_text(encoding='utf-8')
    listed = set()
    for name in on_disk:
        target = name if name.endswith('/') else name
        if f']({target})' in text:
            listed.add(name)
    # An entry the page names that is not on disk is the other half: a link
    # left behind by a rename reads as a live document until somebody clicks.
    import re as _re
    linked = set(_re.findall(r'\]\((?!\.\.?/|https?:)([^)#]+)\)', text))
    stale = {L for L in linked
             if not (d / L.rstrip('/')).exists()}
    missing = on_disk - listed
    check('philosophy/README.md lists every file in philosophy/ '
          f'({len(on_disk)} on disk)',
          not missing and not stale,
          '; '.join(
              ([f'not listed: {", ".join(sorted(missing))}'] if missing else [])
              + ([f'listed but absent: {", ".join(sorted(stale))}'] if stale else [])))


def check_philosophy_citations_run_both_ways():
    """Every item-to-item citation in philosophy/ is answered by the cited item.

    The essays cite each other by slug. A citation written in one direction
    only leaves the cited item with no way back, which is the whole thing
    philosophy/doc-recipes/backlinks.recipe.md exists to prevent -- and it
    is invisible by inspection, since a one-way link looks exactly like a
    correct one from the citing end.

    The return reference is prose somebody wrote, never generated, so this
    can only report the gap and name the item whose text is missing a
    sentence. tools/philosophy_backlinks.py is the engine; running it here
    is what keeps the convention from being advisory-only
    (checkable-gets-checked).
    """
    tool = ROOT / 'tools' / 'philosophy_backlinks.py'
    if not tool.is_file():
        not_applicable('philosophy citations run both ways',
                       'tools/philosophy_backlinks.py does not exist -- not a pass')
        return
    r = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT),
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    check('every philosophy/ citation runs both ways',
          r.returncode == 0,
          out.replace('\n', ' ')[:400])


def check_a_sessions_own_merge_rebuilds_generated_conflicts():
    """precedent_resolve_merge.py finishes a session's own `git merge` that
    stopped only on generated files, with the landing's own resolver
    (2026-10-18: MAP.md conflicted in a session's merge and was rebuilt by
    hand). Planted: a view declared in precedent.json's `generated` list,
    built from two sources each branch changes. CONTROL: a hand-written
    conflict is named and left alone."""
    import tempfile
    name = "a session's own merge rebuilds conflicted generated files"
    tool = ROOT / 'tools' / 'precedent_resolve_merge.py'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        r = pathlib.Path(td) / 'r'
        env = dict(_fixture_git_env())

        def git(*a):
            return subprocess.run(['git', '-C', str(r), *a], capture_output=True,
                                  text=True, env=env)

        def resolve():
            return subprocess.run([sys.executable, str(tool)], cwd=str(r),
                                  capture_output=True, text=True, env=env)
        (r / 'tools').mkdir(parents=True)
        (r / 'tools' / 'gen.py').write_text(
            'import pathlib\n'
            'src = sorted(pathlib.Path("src").glob("*.txt"))\n'
            'pathlib.Path("VIEW.md").write_text("".join(p.read_text() for p in src))\n',
            encoding='utf-8')
        (r / 'precedent.json').write_text(json.dumps(
            {'generated': [{'paths': ['VIEW.md'], 'rebuild': ['tools/gen.py']}]}),
            encoding='utf-8')
        (r / 'src').mkdir()
        (r / 'src' / 'a.txt').write_text('a\n', encoding='utf-8')
        (r / 'notes.md').write_text('base\n', encoding='utf-8')
        git('init', '-q', '-b', 'main')
        subprocess.run([sys.executable, 'tools/gen.py'], cwd=str(r))
        git('add', '-A'); git('commit', '-qm', 'base')
        git('checkout', '-qb', 'other')
        (r / 'src' / 'b.txt').write_text('b\n', encoding='utf-8')
        subprocess.run([sys.executable, 'tools/gen.py'], cwd=str(r))
        git('add', '-A'); git('commit', '-qm', 'theirs adds b')
        git('checkout', '-q', 'main')
        (r / 'src' / 'c.txt').write_text('c\n', encoding='utf-8')
        subprocess.run([sys.executable, 'tools/gen.py'], cwd=str(r))
        git('add', '-A'); git('commit', '-qm', 'ours adds c')
        m = git('merge', '-q', '--no-edit', 'other')
        cases.append(('the fixture merge really stops on the view',
                      m.returncode != 0 and 'VIEW.md' in git(
                          'diff', '--name-only', '--diff-filter=U').stdout, m.stdout))
        out = resolve()
        view = (r / 'VIEW.md').read_text(encoding='utf-8')
        cases.append(('THE DISCRIMINATING CASE: the view is rebuilt from both '
                      'sides\' sources and staged',
                      out.returncode == 0 and view == 'a\nb\nc\n'
                      and not git('diff', '--name-only', '--diff-filter=U').stdout.strip(),
                      failure_detail(out.stdout, 300) + repr(view)))
        git('commit', '-q', '--no-edit')
        git('checkout', '-qb', 'hand', 'HEAD~1')
        (r / 'notes.md').write_text('theirs\n', encoding='utf-8')
        git('commit', '-qam', 'theirs notes')
        git('checkout', '-q', 'main')
        (r / 'notes.md').write_text('ours\n', encoding='utf-8')
        git('commit', '-qam', 'ours notes')
        git('merge', '-q', '--no-edit', 'hand')
        out = resolve()
        cases.append(('CONTROL: a hand-written conflict is named, and the merge '
                      'is left as it was', out.returncode == 1
                      and 'notes.md' in out.stdout and 'NOT resolved' in out.stdout
                      and 'notes.md' in git('diff', '--name-only',
                                            '--diff-filter=U').stdout,
                      failure_detail(out.stdout, 300)))
        git('merge', '--abort')
        out = resolve()
        cases.append(('with no merge in progress it says so',
                      out.returncode == 2 and 'no merge' in out.stdout, out.stdout))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_runbook_names_the_postcondition_after_a_merge():
    """vendor-update-runbook step 12 makes the merge tool's own result the
    postcondition for the turn that merges, and moves the confirming fetch
    to the next turn; the auto-mode gotcha records that a SUCCESSFUL merge
    starts the refusals too.

    WHY. 2026-10-09, a consumer: after a merge that went through, a
    read-only fetch and grep to confirm it were refused as "Merge Without
    Review" until the person spoke. The runbook said to verify, and the
    only verification the turn could still run was the tool's answer."""
    run = (ROOT / 'practices' / 'vendor-update-runbook.md').read_text(encoding='utf-8')
    step = run.split('12. **Publish it', 1)[-1].split('\n## ', 1)[0]
    got = (ROOT / 'gotchas' /
           'gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md'
           ).read_text(encoding='utf-8')
    cases = [
        ('step 12 names the merge tool\'s result as the postcondition',
         'merged: true' in step and 'postcondition' in step),
        ('...and puts the confirming fetch at the start of the next turn, '
         'or leaves it to the next stage\'s tool, saying which',
         'next turn' in step and "next stage's own tool" in step),
        ('the gotcha has the 2026-10-09 case of a merge that succeeded',
         '2026-10-09' in got and 'merge that succeeds' in got),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'the runbook names what a merging turn can still verify '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_todo_progress_discriminates():
    """The open-item pass reports a resemblance and stays quiet otherwise
    (practice: control-asserts-which-failure).

    THE MEASUREMENT THAT SHAPED IT. On its first run against this repository
    the candidate list returned 13 of 83 items for one ordinary day's work,
    because AGENTS.md is cited by more than a third of the open items and
    touched by nearly every change. A list like that is read once. Suppressing
    paths cited across the whole file took it to 5, every one plausible.

    So the discriminating cases here are the QUIET ones: a change touching
    only a widely-cited file must report nothing, and a change touching
    nothing an item names must report nothing. A tool that always finds
    something is a tool nobody reads. The fixture owns its own tree."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import todo_progress as tp

    TODO = (
        '# TODO\n\n'
        '1. <a id="alpha"></a>**An item about the widget.** It names\n'
        '   [tools/widget.py](tools/widget.py) and also [AGENTS.md](AGENTS.md).\n'
        '   **Disposition:** wait\n\n'
        '2. <a id="beta"></a>**An item about the gadget.** It names\n'
        '   `tools/gadget.py` in a code span, and [AGENTS.md](AGENTS.md).\n'
        '   **Remind:** whether the gadget survives (2026-09-13, Morgan)\n'
        '   **Disposition:** ask (2026-09-13, Morgan)\n\n'
        '3. <a id="gamma"></a>**~~A finished item.~~** **DONE 2026-09-13.** It\n'
        '   names [tools/widget.py](tools/widget.py) too.\n\n'
        '4. <a id="delta"></a>**An item naming the common file and the\n'
        '   widget.** [AGENTS.md](AGENTS.md) and\n'
        '   [tools/widget.py](tools/widget.py) -- so widget.py is cited by TWO\n'
        '   live items and gadget.py by one, which is the only reason the\n'
        '   ordering case below has anything to order.\n'
        '   **Disposition:** wait\n')

    ignore = tp.common_paths(TODO)
    cases = []

    cases.append(('a file most items name is suppressed, so it cannot be the '
                  'thing that matches', 'AGENTS.md' in ignore, repr(ignore)))
    cases.append(('and a file only one item names is not suppressed',
                  'tools/widget.py' not in ignore, repr(ignore)))

    got = tp.candidates(TODO, {'tools/widget.py'}, ignore)
    cases.append(('a change touching a named file reports every LIVE item '
                  'naming it',
                  sorted(c[1] for c in got) == ['alpha', 'delta'], repr(got)))
    cases.append(('and a DONE item naming the same file is not reported',
                  'gamma' not in [c[1] for c in got], repr(got)))

    got = tp.candidates(TODO, {'tools/gadget.py'}, ignore)
    cases.append(('a path named in a code span counts, not only a link',
                  [c[1] for c in got] == ['beta'], repr(got)))

    got = tp.candidates(TODO, {'AGENTS.md'}, ignore)
    cases.append(('THE QUIET CASE: a change touching only the widely-cited '
                  'file reports NOTHING', got == [], repr(got)))

    got = tp.candidates(TODO, {'tools/unrelated.py'}, ignore)
    cases.append(('and a change touching nothing any item names reports '
                  'nothing', got == [], repr(got)))

    rem = tp.reminders(TODO)
    cases.append(('a **Remind:** item is surfaced with what to remind about',
                  len(rem) == 1 and rem[0][1] == 'beta'
                  and 'survives' in rem[0][2], repr(rem)))

    # ORDERING. A hit on a file few items cite says more about that item than
    # a hit on one half the queue mentions in passing. Measured: the broad
    # merge that landed this tool produced 13 candidates across eight files
    # with none dominating -- not wrong, and still more than anybody reads.
    # `gadget.py` is cited once here, `widget.py` twice, so the gadget item
    # must sort first whatever order the file lists them in.
    got = tp.candidates(TODO, {'tools/widget.py', 'tools/gadget.py'}, ignore)
    cases.append(('THE ORDERING CASE: the item matched on the rarer path '
                  'sorts first, so a truncated list keeps the strongest hits',
                  [c[1] for c in got][0] == 'beta'
                  and sorted(c[1] for c in got) == ['alpha', 'beta', 'delta'],
                  repr(got)))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the open-item pass matches what an item names and stays quiet '
          f'otherwise ({len(cases)} stated cases, the two quiet ones being '
          f'the discriminating pair)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_instantiated_template_links_survive_the_copy():
    """A file a template tells you to COPY INTO A REPO ROOT cannot carry a
    link that only resolves from the template's own directory.

    templates/document-project/'s README says "copy every file
    in this directory into its root", and its AGENTS.md linked
    `../AGENTS.md.loader.template` and `../../INSTALL.md`. Both resolve
    inside templates/ and are dead the moment the file is where it is
    supposed to end up -- and the same file already linked three other
    upstream documents by absolute URL, so the convention was established
    and these two simply missed it. Found 2026-09-10 installing
    precedent-beta-v01 into a real project; nothing here looked for it.

    The rule is about the DESTINATION, not the file: a template's own
    README is read where it sits and is deleted at instantiation (its step
    6 says so), so `../harness/README.md` is correct THERE and wrong in
    AGENTS.md. So this excludes the READMEs and checks everything else.

    An upward link is the only failure mode: a link INTO the template's own
    subtree (`.claude/settings.json`, `precedent.json`) copies along with
    the file and keeps working."""
    import re
    template_root = ROOT / 'templates' / 'document-project'
    if not template_root.is_dir():
        check('instantiated template files carry no links that die on the '
              'copy', True, '')
        return
    link_re = re.compile(r'\]\(\s*(\.\./[^)\s]*)')
    bad = []
    for f in sorted(template_root.rglob('*.md')):
        if f.name == 'README.md':
            continue          # read in place, deleted at instantiation
        for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            for target in link_re.findall(line):
                bad.append(f'{f.relative_to(ROOT)}:{i} -> {target}')
    check('every file this template copies into a repo root links upstream '
          'documents absolutely, not by a path that only resolves inside '
          'templates/',
          not bad,
          '; '.join(bad))


def check_set_words_leave_out_the_set_itself_by_name():
    """A set checked out somewhere other than its clone -- the worktree
    `--run-tests` makes -- is still that set, so set_words.sets_with_words
    leaves it out by name, not only by path. 2026-10-18: the ladder set's
    full check on main judged the ladder's own practices for using the
    ladder's words, because the clone a person brings sat at another path.
    A different set's words are still returned (the control)."""
    import set_words as sw
    import tempfile
    words = {'patterns': [{'kind': 'a zz word', 'regex': r'\bZzword\b',
                           'matches': ['Zzword'], 'never_matches': ['zzword']}]}
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
        try:
            for d, name in (('clone', 'zz-set'), ('other', 'zz-other'),
                            ('wt', 'zz-set')):
                (tmp / d / '.git').mkdir(parents=True)
                (tmp / d / 'precedent-source.json').write_text(json.dumps(
                    {'name': name, 'level': 'shared', 'owned_words': words}))
            (tmp / 'wt' / 'precedent.json').write_text(json.dumps({'sources': [
                {'level': 'shared', 'name': 'zz-set', 'path': '../clone'},
                {'level': 'shared', 'name': 'zz-other', 'path': '../other'}]}))
            got = sorted(n for n, *_ in sw.sets_with_words(tmp / 'wt'))
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved
    check('a set checked out in a second place does not judge its own words',
          got == ['zz-other'], f'sets_with_words gave {got}')


def check_moves_core_names_exist_in_the_engine():
    """Every name precedent_branches.MOVES_CORE declares -- what a set's
    moves module may call on the engine as `core.<name>` -- exists in the
    engine. 2026-10-20: the ladder's moves module called 47 engine names
    with no contract, so a rename broke Promote everywhere and only the
    set's own test, after an engine refresh, would see it. The other half,
    that the module calls only declared names, is the ladder set's test."""
    import precedent_branches as pb
    declared = getattr(pb, 'MOVES_CORE', ())
    missing = [n for n in declared if not hasattr(pb, n)]
    dupes = sorted({n for n in declared if declared.count(n) > 1})
    check(f'every name the engine declares for a moves module exists '
          f'({len(declared)} declared)',
          declared and not missing and not dupes,
          f'missing: {missing}; declared twice: {dupes}')


def check_set_words_hold_a_practice_printed_part_to_output_patterns():
    """set_words.file_hits holds a practice's printed part -- title,
    index_clause and ## Rule, what the gates print word for word -- to a
    set's output patterns, and leaves its Detail, its Story and the excused
    ordinary phrase alone. 2026-10-20: "staging" in two universal Rules
    reached the gates' output and only the full suite's
    check_ladder_off_engine_says_no_ladder_words saw it, because the quick
    check read files with file patterns alone."""
    import set_words as sw
    import tempfile
    words = sw.Words('zz-set', {'output_patterns': [
        {'kind': 'a zz tier', 'regex': r'(?<![/\w-])zztier\b',
         'matches': ['on zztier'], 'never_matches': ['tree/zztier']}]})
    practice = ('---\nslug: zz\ntitle: "Zz"\nindex_clause: "{clause}"\n'
                'status: active\n---\n## Rule\n{rule}\n\n## Detail\n'
                'Detail names zztier.\n\n## Story\nStory names zztier.\n')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / 'zz.md'

        def got(clause='plain', rule='Plain rule.'):
            f.write_text(practice.format(clause=clause, rule=rule))
            return [(n, m) for n, _k, m in sw.file_hits(f, words)]
        cases.append(('a Rule naming the word is a hit', got(rule='Land on zztier.') == [(8, 'zztier')]))
        cases.append(('an index_clause naming it is a hit', got(clause='land on zztier') == [(4, 'zztier')]))
        cases.append(('CONTROL: Detail and Story naming it are not', got() == []))
        sw.EXCUSED_IN_OUTPUT += ('zztier document',)
        try:
            cases.append(('an excused phrase is not',
                          got(rule='Write a zztier document.') == []))
        finally:
            sw.EXCUSED_IN_OUTPUT = sw.EXCUSED_IN_OUTPUT[:-1]
    bad = [n for n, ok in cases if not ok]
    check(f'a practice\'s printed part is held to output patterns ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_filtered_check_does_not_break_the_unpack_family():
    """A check filtered out by PRECEDENT_CHECK_ONLY/SKIP must unpack
    through `check('<name>', *check_foo())` without raising, and must land
    as N/A -- never as a pass.

    Both halves have been wrong in production. Before 2026-09-21 the
    stand-in returned a truthy value and a skipped check REPORTED SUCCESS;
    the fix for that returned None instead, which made `*None` a TypeError
    at all 10 unpack sites the moment either variable was set. CI is the
    only caller that sets them, so a full local run passed 244/0 while
    both sharded deep-check jobs died before their first verdict. This
    check is the control that refuses either regression.

    practice: control-asserts-which-failure -- the negative case below is
    the old None-returning stand-in, which must still raise.
    """
    import subprocess
    cases, bad = [], []
    probe = (
        "import os, sys\n"
        "sys.path.insert(0, %r)\n"
        "os.environ['PRECEDENT_CHECK_ONLY'] = 'check_nothing_matches_this'\n"
        "import verify_harness as vh\n"
        "vh._install_check_filter()\n"
        "stand_in = vh.check_advisory_requirement_never_blocks\n"
        "got = stand_in()\n"
        "assert got is not None, 'stand-in returned None -- *None will raise'\n"
        "assert got[0] is vh._CHECK_FILTERED_OUT, 'first element is not the sentinel'\n"
        "vh.PASSED.clear(); vh.FAILED.clear(); vh.NA.clear()\n"
        "vh.check('fixture', *stand_in())\n"
        "assert not vh.PASSED, 'a filtered check reported SUCCESS'\n"
        "assert not vh.FAILED, 'a filtered check reported a FAILURE'\n"
        "assert len(vh.NA) == 1, 'a filtered check was not recorded as N/A'\n"
        "print('ok')\n"
    ) % str(ROOT / 'tools')
    r = subprocess.run([sys.executable, '-c', probe],
                       capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0 or 'ok' not in r.stdout:
        bad.append('the filtered-check stand-in no longer unpacks as N/A: '
                   + (r.stderr.strip().splitlines() or ['(no stderr)'])[-1])
    cases.append('filtered check unpacks and lands as N/A')

    # Negative control: the shape the bug had must still be an error.
    ctl = subprocess.run(
        [sys.executable, '-c',
         "def f(*a, **k):\n    return None\n"
         "def check(name, ok, detail='', failure=''):\n    pass\n"
         "try:\n    check('x', *f())\n"
         "except TypeError:\n    print('raised')\n"],
        capture_output=True, text=True)
    if 'raised' not in ctl.stdout:
        bad.append('negative control did not raise -- this check proves nothing')
    cases.append('negative control (None stand-in) still raises')

    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


