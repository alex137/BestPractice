# The harness tests for session start
#
# tools/harness/vh_session_start.py -- part of the verification harness:
# session start: bootstrap, hooks, Python, freshness.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_freshness_guard_checks_declared_sets():
    """The freshness guard checks every practice set a repo declares, with
    PRECEDENT_FRESHNESS_ALSO unset, and a declared set warns, never blocks
    (2026-09-30, agreed with a consumer session).

    Sessions kept rewriting the variable between two absolute forms and each
    rewrite broke half of it; everything it named was already declared. A
    throwaway project whose precedent.json declares ../set, with the engine's
    precedent_resolve.py beside it, and a set clone that falls behind its
    own origin. Both guard copies. CONTROL: the same stale set, not
    declared, goes unnoticed, so the finding comes from the declaration."""
    import tempfile
    # The installed stub and the template stub, each running tools/'s script.
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    env0 = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    env0.pop('PRECEDENT_FRESHNESS_ALSO', None)
    cases = []

    def git(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a], env=env0,
                              capture_output=True, text=True)

    for guard in guards:
        tag = guard.relative_to(ROOT).as_posix()
        with tempfile.TemporaryDirectory() as td:
            w = pathlib.Path(td)
            (w / 'sentinels').mkdir()

            def make(name):
                bare, seed, clone = w / f'{name}.git', w / f'{name}-seed', w / name
                subprocess.run(['git', 'init', '-q', '--bare', str(bare)], env=env0)
                subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)], env=env0)
                git(seed, 'remote', 'add', 'origin', str(bare))
                (seed / 'f').write_text('a\n')
                git(seed, 'add', 'f'); git(seed, 'commit', '-qm', 'a')
                git(seed, 'push', '-q', 'origin', 'main')
                subprocess.run(['git', 'clone', '-q', '-b', 'main', str(bare), str(clone)],
                               env=env0, capture_output=True)
                return seed, clone

            proj_seed, proj = make('proj')
            set_seed, setc = make('set')
            # The whole engine, as a consumer has it: the resolver imports
            # its neighbours.
            (proj / 'tools').mkdir()
            for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
                shutil.copy(f, proj / 'tools' / f.name)
            (set_seed / 'f').write_text('a\nb\n')
            git(set_seed, 'commit', '-qam', 'b'); git(set_seed, 'push', '-q', 'origin', 'main')

            def run(mode, session, declared):
                (proj / 'precedent.json').write_text(json.dumps({'sources': (
                    [{'level': 'shared', 'name': 'set', 'path': '../set'}] if declared else [])}))
                env = dict(env0, TMPDIR=str(w / 'sentinels'), CLAUDE_PROJECT_DIR=str(proj),
                           PRECEDENT_USER_CONFIG=str(w / 'no-user-config.json'))
                r = subprocess.run(['bash', str(guard), mode, 'main'],
                                   input=json.dumps({'session_id': session, 'tool_name': 'Write',
                                                     'tool_input': {'command': ''}}),
                                   env=env, capture_output=True, text=True, cwd=str(proj))
                return r.returncode, r.stderr

            rc, err = run('pre-write', 'undeclared', declared=False)
            cases.append((f'{tag}: CONTROL: an undeclared stale set goes unnoticed (rc={rc})',
                          rc == 0 and str(setc) not in err))
            tip = git(set_seed, 'rev-parse', 'HEAD').stdout.strip()
            rc, err = run('pre-write', 'declared-clean', declared=True)
            head = git(setc, 'rev-parse', 'HEAD').stdout.strip()
            cases.append((f'{tag}: a clean declared set behind its origin is brought '
                          f'current with the variable unset, and never blocks (rc={rc})',
                          rc == 0 and 'declared practice set' in err and head == tip))
            git(setc, 'reset', '-q', '--hard', 'HEAD~1')
            (setc / 'f').write_text('local edit\n')
            rc, err = run('pre-write', 'declared-dirty', declared=True)
            cases.append((f'{tag}: a dirty declared set behind its origin WARNS and does '
                          f'not block (rc={rc})',
                          rc == 0 and 'WARN: freshness-guard: declared practice set' in err))
            git(setc, 'checkout', '-q', '--', 'f')
            rc, err = run('session-start', 'declared-start', declared=True)
            cases.append((f'{tag}: session start names the declared set it checks (rc={rc})',
                          rc == 0 and 'also checking declared practice set' in err))
    failed = [n for n, ok in cases if not ok]
    check(f'the freshness guard checks declared practice sets without the variable '
          f'({len(cases)} stated cases, both copies)', not failed, '; '.join(failed))


def check_bootstrap_local_steps_run_and_dead_lines_are_named():
    """A consumer's own session-start steps have a place that runs and that
    no refresh touches, and steps stranded after the template's `exit 0`
    are named (2026-09-30, a real consumer: three of its own steps landed
    after `exit 0` in a hand merge and never ran again, unreported).

    Stated cases: a tools/bootstrap.sh with commands after its top-level
    `exit` is reported, naming the lines, under its DIVERGED block and on
    the Left-for-you list; the same steps in tools/bootstrap.local.sh, with
    bootstrap.sh identical to the template, run and leave it `current`."""
    import contextlib, io, tempfile
    import precedent_vendor_engine as pve
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='bootstrap-local-'))
    template = (ROOT / 'templates' / 'bootstrap.sh').read_text(encoding='utf-8')
    try:
        dead = tmp / 'dead'
        (dead / 'tools').mkdir(parents=True)
        (dead / 'tools' / 'bootstrap.sh').write_text(
            template + 'git clone -q https://example.invalid/ref ref || true\necho own step\n',
            encoding='utf-8')
        plan = pve._template_instance_plan(dead, 'consumer', ROOT, {})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pve._report_diverged_template_instances(dead, ROOT, plan)
        out = buf.getvalue()
        cases.append(('lines after the top-level exit are named as never running',
                      'never run' in out and 'bootstrap.local.sh' in out, failure_detail(out, 400)))
        at, lines = pve.dead_after_exit((dead / 'tools' / 'bootstrap.sh').read_text())
        cases.append(('and it is exactly the two commands after the exit',
                      len(lines) == 2 and lines[0] == at + 1, f'{at} {lines}'))
        cases.append(('the template itself has nothing after its exit',
                      pve.dead_after_exit(template) == (None, []), ''))

        live = tmp / 'live'
        (live / 'tools').mkdir(parents=True)
        (live / 'tools' / 'bootstrap.sh').write_text(template, encoding='utf-8')
        (live / 'tools' / 'bootstrap.local.sh').write_text(
            'echo ran > "$MARK"\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=live)
        mark = tmp / 'marker'
        r = subprocess.run(['bash', 'tools/bootstrap.sh'], cwd=live, capture_output=True,
                           text=True, timeout=180, env=dict(os.environ, MARK=str(mark)))
        cases.append(('the same steps in tools/bootstrap.local.sh run',
                      mark.is_file() and r.returncode == 0, failure_detail(r.stdout + r.stderr, 300)))
        plan = pve._template_instance_plan(live, 'consumer', ROOT, {})
        cases.append(('and tools/bootstrap.sh is current, not DIVERGED',
                      [a for _s, rel, a in plan if rel == 'tools/bootstrap.sh'] == ['current'],
                      str(plan)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a consumer\'s own bootstrap steps run from bootstrap.local.sh, and '
          f'dead lines after exit are named ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_bootstrap_new_branch_compared_to_landing_branch():
    """A branch not yet on origin is checked against the person's landing
    branch, in the template a consumer receives as well as in this repo's
    own copy (2026-10-01, from a consumer's Update Vendors: every branch cut
    from the landing tier was warned "cut from a stale base", because main
    holds the Promote merge commits that tier never gets, and only
    tools/bootstrap.sh had learned the tiers).

    Stated cases, for templates/bootstrap.sh and tools/bootstrap.sh alike: a
    branch made from origin/staging, with a commit of its own, in a repo
    whose landing branch is staging and whose main is one Produce ahead, is
    checked against origin/staging and draws no stale-base warning.
    And the two copies of that block are the same text, so one cannot learn
    a case the other has not."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='bootstrap-landing-'))

    def git(cwd, *a):
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True)
    try:
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(tmp / 'origin.git')], check=True)
        w = tmp / 'w'
        subprocess.run(['git', 'clone', '-q', str(tmp / 'origin.git'), str(w)],
                       capture_output=True)
        git(w, 'config', 'user.email', 'fixture@example.invalid')
        git(w, 'config', 'user.name', 'fixture')
        (w / 'precedent.json').write_text(
            '{"base_branch": "main", "staging_branch": "staging", '
            '"landing_branch": "staging"}\n')
        git(w, 'add', '.')
        git(w, 'commit', '-qm', 'init')
        git(w, 'push', '-q', 'origin', 'main', 'main:staging')
        git(w, 'commit', '-q', '--allow-empty', '-m', 'Produce: staging into main')
        git(w, 'push', '-q', 'origin', 'main')
        git(w, 'fetch', '-q', 'origin')
        git(w, 'checkout', '-q', '-b', 'feat', 'origin/staging')
        git(w, 'commit', '-q', '--allow-empty', '-m', 'work of its own')
        (w / 'tools').mkdir()
        shutil.copy(ROOT / 'tools' / 'precedent_branches.py', w / 'tools')
        (w / '.git' / 'info' / 'exclude').write_text('tools/\n')
        env = dict(os.environ, PRECEDENT_LOCAL_SESSION='1',
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
                   CLAUDE_PROJECT_DIR=str(w))
        for rel in ('templates/bootstrap.sh', 'tools/bootstrap.sh'):
            shutil.copy(ROOT / rel, w / 'tools' / 'bootstrap.sh')
            r = subprocess.run(['bash', 'tools/bootstrap.sh'], cwd=w, env=env,
                               capture_output=True, text=True, timeout=180)
            out = r.stdout + r.stderr
            cases.append((f'{rel}: a new branch is checked against origin/staging',
                          'Checking it against origin/staging' in out, failure_detail(out, 400)))
            cases.append((f'{rel}: and draws no stale-base warning',
                          'stale base' not in out, failure_detail(out, 400)))

        def block(rel):
            t = (ROOT / rel).read_text(encoding='utf-8')
            a = t.find('  # Not on origin yet:')
            b = t.find('SKIPPED, not passed', a)
            return t[a:b] if a >= 0 and b > a else None
        cases.append(('the two copies of the new-branch block are the same text',
                      block('templates/bootstrap.sh') is not None
                      and block('templates/bootstrap.sh') == block('tools/bootstrap.sh'),
                      'templates/bootstrap.sh and tools/bootstrap.sh differ between '
                      '"# Not on origin yet:" and "SKIPPED, not passed"'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a new branch is compared with the landing branch by both bootstrap '
          f'copies ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_update_written_files_name_no_mirrored_engine():
    """A file only an update writes names no `process/upstream/tools/`
    path: every update since the catalogue copy left tools/ out removes that
    directory, so a fallback to it is dead text (2026-09-30, found by a
    consumer's session reading its own bootstrap.sh). The individual-set
    hook is different: it also arrives by a set's sync, which can reach a
    repo that has not updated, so it keeps the fallback -- but tries the
    repo's own tools/ first."""
    cases = []
    for rel in ('templates/bootstrap.sh',
                'templates/harness/claude-code/hooks/push-check-gate.sh',
                'templates/harness/claude-code/hooks/merge-check-gate.sh',
                'templates/github-actions/light-check.yml.template',
                'templates/harness/codex/README.md',
                'templates/harness/gemini-cli/README.md'):
        hits = [n for n, l in enumerate((ROOT / rel).read_text(
                    encoding='utf-8').splitlines(), 1)
                if 'process/upstream/tools/' in l and not l.lstrip().startswith('#')]
        cases.append((f'{rel} runs nothing from process/upstream/tools/',
                      not hits, f'lines {hits}'))
    # ...nor does any shipped tool tell a person to run something from there:
    # its docstring and --help are what a session copies (2026-10-01,
    # practice_audit.py and checkin.py still did).
    told = [f.name for f in sorted((ROOT / 'tools').glob('*.py'))
            if f.name != 'verify_harness.py'
            and 'python3 process/upstream/tools/' in f.read_text(encoding='utf-8')]
    cases.append(('no shipped tool says to run anything from process/upstream/tools/',
                  not told, str(told)))
    # The logic behind the individual-set hook's stub (2026-10-07).
    hook = (ROOT / 'tools' / 'individual-source-bootstrap.sh').read_text(encoding='utf-8')
    # The fallback after `:-` is the hook's own idea of its repo since
    # 2026-10-02 (a hand run sets no project dir); `.` before that.
    engines = re.findall(r'^\s*ENGINE="\$\{CLAUDE_PROJECT_DIR:-[^}]*\}/(\S+?)"', hook, re.M)
    cases.append(('the individual-set hook tries tools/ before the mirror',
                  engines[:1] == ['tools/precedent_source_bootstrap.py'], str(engines)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'files only an update writes run no mirrored engine '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_glob_semantics():
    ok = True
    for path, glob, expected in GLOB_CASES:
        got = pp.path_matches(path, glob)
        if got != expected:
            ok = False
            print(f"  {path!r} vs {glob!r}: expected {expected}, got {got}")
    check(f'path-glob semantics ({len(GLOB_CASES)} stated cases: `**` crosses "/", '
          f'`*` does not, paths normalize to repo-root-relative)', ok)


def check_symlinked_root_path_matching():
    """A path reached through a symlinked route to the repo root (a
    symlinked workspace, a Docker bind mount) must normalize the same as
    the real path. Regression case: normalize_path() used to compare only
    against ROOT's OWN resolved spelling, so a symlinked absolute path fell
    through untouched and an exact-filename glob (README.md, used by real
    practices) silently stopped matching -- no error, just a routing miss
    an ordinary session would never think to suspect."""
    import tempfile
    link = pathlib.Path(tempfile.mkdtemp(prefix='precedent-symlink-')) / 'repo-link'
    try:
        link.symlink_to(ROOT)
        exact = pp.path_matches(str(link / 'README.md'), 'README.md')
        broad = pp.path_matches(str(link / 'README.md'), '**/*.md')
        cases = [('exact-filename and broad globs match the same as the '
                  'real path', exact and broad)]

        # A relative symlink -- not just an absolute one -- must resolve the
        # same way. pathlib.Path.resolve() genuinely handles a relative
        # symlink target, but nothing had ever exercised that path here.
        rel_dir = link.parent / 'rel-repo-link'
        rel_target = os.path.relpath(ROOT, link.parent)
        rel_dir.symlink_to(rel_target)
        cases.append(('a RELATIVE symlinked repo root matches the same as '
                      'the real path',
                      pp.path_matches(str(rel_dir / 'README.md'), 'README.md')
                      and pp.path_matches(str(rel_dir / 'README.md'), '**/*.md')))
        rel_dir.unlink()

        # A symlink LOOP must degrade, not crash. normalize_path() used to
        # call pathlib.Path.resolve() unguarded, which raises RuntimeError
        # on a loop (a -> b -> a) -- an uncaught exception that would take
        # down every caller (the PreToolUse hook, behavioral_replay.py) for
        # a path that merely happens to contain a loop somewhere in it,
        # rather than falling through the way an unresolvable path already
        # does elsewhere in this function.
        loop_a, loop_b = link.parent / 'loop-a', link.parent / 'loop-b'
        loop_b.symlink_to(loop_a)
        loop_a.symlink_to(loop_b)
        try:
            pp.path_matches(str(loop_a / 'README.md'), '**/*.md')
            loop_ok = True
        except Exception as e:
            loop_ok = False
            print(f"  a symlink loop raised instead of degrading: {e!r}")
        cases.append(('a symlink loop degrades instead of crashing', loop_ok))
        loop_a.unlink(missing_ok=True)
        loop_b.unlink(missing_ok=True)

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  symlinked-root path matching did NOT behave as "
                      f"stated: {name}")
        check(f'symlinked repo root ({len(cases)} stated cases: absolute, '
              f'relative, and a symlink loop)', ok)
    finally:
        link.unlink(missing_ok=True)
        link.parent.rmdir()


def check_fresh_install_reaches_its_code_owner_practices():
    """On a fresh install, layered-practice-packs counts the session file as
    the channel that carries the practices for code owners, now that
    .claude/hooks/session-start.sh is a shim to tools/session-start.sh,
    which runs tools/bootstrap.sh, which writes the session file.

    Found 2026-10-31 by the very deep check's pass 1 install rehearsal: a
    correct fresh install's full sweep reported drift-notice,
    full-practice-audit, install and rule-scope-ask as "reachable by no
    channel", while its first session start had just written all four into
    .precedent/SESSION_PRACTICES.md. The check followed the settings
    command one level (to tools/session-start.sh), which names bootstrap.sh
    and not the session-practices tool.

    Negative control, measured 2026-10-31: on the code before the fix the
    first case fails (the four advisories are printed) and the second does
    not see the session-file line.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-owner-reach-'))
    # A newcomer's machine: no individual set, no PRECEDENT_* variables, an
    # empty HOME -- this session's own sets resolving into the fixture is
    # what the first draft of this test measured instead
    # (fixture-owns-its-state).
    (tmp / 'home').mkdir()
    genv = dict(_isolated_env(os.environ, tmp / 'home'),
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com',
                PRECEDENT_SEED_OFF_MAIN='1')
    tmp = tmp / 'proj'
    cases = []
    try:
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp)], check=True, env=genv)
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                        str(tmp), '--project-name', 'Fixture', '--visibility', 'private',
                        '--admin', 'fixture-admin'],
                       capture_output=True, text=True, env=genv)
        # The seed copies the engine as committed; the check under test is
        # this tree's, committed or not.
        shutil.copy2(ROOT / 'tools' / 'precedent_check.py', tmp / 'tools' / 'precedent_check.py')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                            '--only', 'layered-practice-packs'],
                           capture_output=True, text=True, cwd=str(tmp), env=genv)
        out = r.stdout + r.stderr
        cases.append(('no code-owner practice reads as reachable by no channel',
                      'install is in force here but reachable by no channel' not in out
                      and 'drift-notice is in force here but reachable by no channel'
                      not in out and '0 errored' in out, failure_detail(out, 600)))
        cases.append(('they are counted as reaching the session through its file',
                      'reach this session through .precedent/SESSION_PRACTICES.md' in out
                      and 'drift-notice' in out.split('SESSION_PRACTICES.md', 1)[-1],
                      out[:600]))
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a fresh install reaches its code-owner practices through the '
          f'session file ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_session_start_says_when_bootstrap_is_missing():
    """tools/session-start.sh says so when tools/bootstrap.sh is not there,
    locally and in the cloud, instead of doing nothing silently (local) or
    failing its exec (cloud).

    Found 2026-10-31 by the very deep check's pass 1 migration rehearsal: a
    classic install that had run step 7 (seed and refresh) had the engine's
    tools/session-start.sh and no tools/bootstrap.sh, which step 8
    instantiates; a local session start then printed nothing at all.

    Negative control, measured 2026-10-31: on the code before the fix the
    local case prints nothing and the cloud case exits 127 with bash's own
    "No such file or directory".
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-no-bootstrap-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        for remote in ('', 'true'):
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp), CLAUDE_CODE_REMOTE=remote)
            r = subprocess.run(['bash', str(ROOT / 'tools' / 'session-start.sh')],
                               capture_output=True, text=True, env=env, cwd=str(tmp),
                               stdin=subprocess.DEVNULL, timeout=60)
            said = r.stdout + r.stderr
            cases.append((f'{"cloud" if remote else "local"}: exits 0 and says '
                          f'tools/bootstrap.sh is not here',
                          r.returncode == 0 and 'tools/bootstrap.sh is not here' in said,
                          f'exit {r.returncode}: {failure_detail(said, 300)}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'session start says when tools/bootstrap.sh is missing '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_engine_carries_no_branch_naming_enforcement():
    """The branch-naming rule is the ladder set's act, and so is every check
    of it: its tools/branch_name_guard.py refuses at git's pre-push and
    notes the first commit (Morgan, 2026-10-16, strength: decided:
    "Enforcement should live in the same support repo where the practice
    is"). Until then the refusal and both notes lived here, switched on only
    when the ladder loaded, and went quiet when it failed to clone. Pinned:
    the engine's naming tool builds names and judges none; the push check
    refuses no name; no engine hook notes a commit; and the engine's
    pre-push hook point runs a practice's declared hook, refusing on its
    failure, and refuses outright while a source did not load."""
    import json as _json
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_branch_name as _bn
    import precedent_push_check as _ppc
    import precedent_vendor_engine as _pve
    import precedent_hooks as _ph
    cases = [
        ('precedent_branch_name.py judges no name',
         not any(hasattr(_bn, n) for n in ('name_refusal', 'harness_name_note',
                                            'commit_note', 'is_harness_name'))),
        ('the push check refuses and notes no branch name',
         not any(hasattr(_ppc, n) for n in ('_branch_name_refusal',
                                             '_branch_name_notes'))),
        ('no engine hook notes a commit',
         not any(n.startswith('branch-name-commit-note') for n in _pve.HOOK_SCRIPT_FILES)
         and not any(p.name.startswith('branch-name-commit-note')
                     for p in (ROOT / 'tools').iterdir())
         and 'branch-name-commit-note' not in
         (ROOT / 'tools' / 'hook_wiring.json').read_text(encoding='utf-8')),
        ('the global pre-push runs the practices\' pre-push hooks',
         'precedent_hooks.py' in (ROOT / 'tools' / 'commit-identity.sh').read_text(
             encoding='utf-8') and '--git pre-push' in
         (ROOT / 'tools' / 'commit-identity.sh').read_text(encoding='utf-8')),
    ]
    with _tf.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'process').mkdir()
        (root / 'tools').mkdir()
        (root / 'tools' / 'refuse.py').write_text(
            'import sys\nsys.exit(1 if "bad" in sys.stdin.read() else 0)\n',
            encoding='utf-8')
        (root / 'process' / 'practice_hooks.json').write_text(_json.dumps({
            'hooks': [{'event': 'pre-push', 'matcher': None,
                       'command': 'python3 $CLAUDE_PROJECT_DIR/tools/refuse.py'}]}),
            encoding='utf-8')
        saved = _ph.unloaded_sources
        try:
            _ph.unloaded_sources = lambda *_a, **_k: []
            cases.append(('a declared pre-push hook that passes lets the push through',
                          _ph.run_git_hook('pre-push', ['origin', 'u'],
                                           'refs/heads/ok\n', root=root) == 0))
            cases.append(('...and one that fails refuses it',
                          _ph.run_git_hook('pre-push', ['origin', 'u'],
                                           'refs/heads/bad\n', root=root) == 1))
            _ph.unloaded_sources = lambda *_a, **_k: [('some-set', 'acme/some-set')]
            cases.append(('a source that did not load refuses the push before any hook',
                          _ph.run_git_hook('pre-push', [], 'refs/heads/ok\n',
                                           root=root) == 1))
        finally:
            _ph.unloaded_sources = saved
    sys.path.pop(0)
    failed = [n for n, ok in cases if not ok]
    check(f'the engine carries no branch-naming enforcement, and its pre-push '
          f'hook point runs the practices\' hooks ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_update_reports_every_blocker_before_the_slow_check():
    """Update Vendors reports every blocker it can find cheaply in one run
    and starts the slow check only when there are none (2026-10-02: a large
    consumer's run 1 spent half an hour on its full check, failed it, and
    only run 3 stopped on a template divergence known before run 1's check
    began). Two independent items left for the person: both named in one
    run, and the check never started. None left but the basic tier red: its
    findings reported, the full tier never started. Both green: the full
    tier runs. The check is stubbed, so each case is decided by what the
    stub was asked.

    Negative control, measured 2026-10-02 against staging at 1c2403f: the
    check runs with items left (the first case fails), and only the full
    tier is ever asked for (the second fails)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-update-blockers-'))
    cases = []
    real = pu.judged_as_committed, pu.pb.landing_branch, pu.pb.tier_for_branch
    try:
        repo = tmp / 'r'
        (repo / 'tools').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], capture_output=True)
        (repo / 'tools' / 'precedent_push_check.py').write_text('', encoding='utf-8')
        pu.pb.landing_branch = lambda _r, *a, **k: ('staging', 'fixture')
        pu.pb.tier_for_branch = lambda _r, _b, *a, **k: (pu.pb.FULL, 'fixture')
        asked = []

        def stub(red_tiers):
            def judged(_repo, argv):
                tier = argv[argv.index('--tier') + 1] if '--tier' in argv else 'full'
                asked.append(tier)
                return (1, f'{tier} finding') if tier in red_tiers else (0, 'green')
            return judged

        def run(red_tiers, left=()):
            asked.clear()
            pu.judged_as_committed = stub(red_tiers)
            rep = pu.Report()
            for what, why in left:
                rep.leave(what, why)
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = pu.closing_check(repo, rep)
            return rc, buf.getvalue()

        rc, out = run({'full'}, [('tools/bootstrap.sh', 'diverged from the template'),
                                 ('AGENTS.md "Session setup"', 'missing a template section')])
        left = out.split('LEFT FOR YOU', 1)[-1]
        cases.append(('two items left: both named in one run, and no check started',
                      rc == pu.LEFT and 'tools/bootstrap.sh' in left
                      and 'AGENTS.md "Session setup"' in left and asked == [],
                      (asked, failure_detail(out, 1200))))
        rc, out = run({'basic', 'full'})
        cases.append(('none left, the basic tier red: its finding reported, the full '
                      'tier never started', rc == pu.FAILED and 'basic finding' in out
                      and asked == ['basic'], (asked, failure_detail(out, 1200))))
        rc, out = run(set())
        cases.append(('none left, both green: the full tier runs after the basic',
                      rc == pu.DONE and asked == ['basic', 'full'], (asked, failure_detail(out, 1200))))
    finally:
        pu.judged_as_committed, pu.pb.landing_branch, pu.pb.tier_for_branch = real
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_second_consumer_findings():
    """Five update-tool defects a consumer's Update Vendors hit on
    2026-09-28, each pinned where it is fixed and each planted here.

    1. A failed update dropped its Left-for-you list, and with it the line
       naming bootstrap.sh as lacking the shared-set clone block -- the very
       block whose absence failed the check.
    2. The check failed on file-header for a regenerated AGENTS.md whose
       version the commit would have stamped. stamp_headers() stamps first,
       and re-stages only what was already staged.
    3. A `synced` manifest entry inside the vendored tree kept its old hash
       after the mirror rewrote the file, so the audit reported DRIFT on an
       upstream change. rebaseline_vendored_entries() re-records those, and
       nothing outside the tree.
    4. A workflow the engine took over kept its outside-vendoring exemption,
       whose reason ("this repo's own") was now false.
    5. The engine line said "(was <new commit>)": the second pass read the
       manifest the first had rewritten."""
    import io, contextlib, hashlib, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    cases = []
    # Each fix is judged on its own, so a control run against the old code
    # shows every one of them red rather than stopping at the first gap.
    for n in ('engine_summary', 'stamp_headers', 'rebaseline_vendored_entries'):
        if not hasattr(pu, n):
            setattr(pu, n, None)

    rep = pu.Report()
    rep.leave('tools/bootstrap.sh', 'lacks 2 of its blocks (listed below)')
    rep.details['tools/bootstrap.sh'] = ['    templates/bootstrap.sh:42 "Clone every shared practice set"']
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rep.close('the check for staging is red')
    text = buf.getvalue()
    cases.append(('1. a FAILED update still prints what it left for the person, with detail',
                  'tools/bootstrap.sh' in text and 'Clone every shared practice set' in text
                  and text.index('tools/bootstrap.sh') < text.index('FAILED:')))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-consumer-update-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True, check=True)
    try:
        r = tmp / 'r'
        subprocess.run(['git', 'init', '-q', str(r)], env=env, check=True)
        (r / 'tools' / 'checks').mkdir(parents=True)
        # A stand-in header fixer: appends a stamp to every .md it finds, the
        # observable thing the real one does to a file it bumps.
        (r / 'tools' / 'checks' / 'check_file_header.py').write_text(
            'import pathlib, sys\n'
            'if "--fix" in sys.argv:\n'
            '    for p in pathlib.Path(".").glob("*.md"):\n'
            '        p.write_text(p.read_text() + "stamped\\n")\n', encoding='utf-8')
        (r / 'AGENTS.md').write_text('v1\n', encoding='utf-8')
        (r / 'NOTES.md').write_text('mine\n', encoding='utf-8')
        git(r, 'add', '-A')
        git(r, 'commit', '-qm', 'base')
        (r / 'AGENTS.md').write_text('v2\n', encoding='utf-8')
        git(r, 'add', 'AGENTS.md')
        (r / 'NOTES.md').write_text('mine, edited, not staged\n', encoding='utf-8')
        stamped = pu.stamp_headers(r) if pu.stamp_headers else None
        staged = git(r, 'diff', '--cached', '--name-only').stdout.split()
        cases.append(('2. the header is stamped and re-staged before the check',
                      stamped == ['AGENTS.md'] and 'AGENTS.md' in staged
                      and git(r, 'show', ':AGENTS.md').stdout.endswith('stamped\n')))
        cases.append(("2. ...and a file the person left unstaged stays unstaged",
                      'NOTES.md' not in staged))

        (r / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        (r / 'process' / 'upstream' / 'tools' / 'doc_lint.py').write_text('new upstream\n')
        (r / 'tools' / 'bootstrap.sh').write_text('edited here\n')
        (r / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'vendored_at': 'process/upstream'},
            'entries': [
                {'practice': 'doc-lint', 'status': 'synced', 'granularity': 'file',
                 'local_path': 'process/upstream/tools/doc_lint.py', 'local_sha256': 'old'},
                {'practice': 'bootstrap', 'status': 'synced', 'granularity': 'file',
                 'local_path': 'tools/bootstrap.sh', 'local_sha256': 'old'}]}))
        rebased = (pu.rebaseline_vendored_entries(r)
                   if pu.rebaseline_vendored_entries else None)
        entries = json.loads((r / 'process' / 'manifest.json').read_text())['entries']
        cases.append(('3. a synced entry inside the vendored tree is re-baselined',
                      rebased == ['process/upstream/tools/doc_lint.py'] and
                      entries[0]['local_sha256'] == hashlib.sha256(b'new upstream\n').hexdigest()))
        cases.append(('3. ...and one outside it still reads as drift',
                      entries[1]['local_sha256'] == 'old'))
        # 3b. A generated view outside the tree is the generator's output:
        # re-recorded whenever it differs, on any run (2026-10-04, a
        # consumer's MAP.md, regenerated between two runs, failed as DRIFT).
        (r / 'MAP.md').write_text('---\ngenerated_by: tools/build_views.py\n---\n\n# Map\n',
                                  encoding='utf-8')
        data = json.loads((r / 'process' / 'manifest.json').read_text())
        data['entries'].append({'practice': 'orientation-map', 'status': 'synced',
                                'granularity': 'file', 'local_path': 'MAP.md',
                                'upstream_path': 'templates/MAP.md.template',
                                'local_sha256': 'old'})
        (r / 'process' / 'manifest.json').write_text(json.dumps(data))
        rebased = pu.rebaseline_vendored_entries(r)
        entries = json.loads((r / 'process' / 'manifest.json').read_text())['entries']
        cases.append(('3b. a generated view outside the tree is re-baselined on a run '
                      'that did not itself rewrite it',
                      'MAP.md' in (rebased or []) and entries[-1]['local_sha256'] != 'old'))
        cases.append(('3b. ...while the hand-kept file beside it still reads as drift',
                      entries[1]['local_sha256'] == 'old'))

        wf = '.github/workflows/light-check.yml'
        (r / 'precedent.json').write_text(json.dumps({
            'github_ci_approved': {wf: {'sha256': 'x', 'approved_by': 'y'}},
            'ci_workflow_outside_vendoring_exempt': [
                {'path': wf, 'reason': "this repo's own"},
                {'path': '.github/workflows/other.yml', 'reason': 'kept'}]}))
        with contextlib.redirect_stdout(io.StringIO()):
            pve._drop_ci_approvals(r, [wf])
        cfg = json.loads((r / 'precedent.json').read_text())
        cases.append(("4. a converged workflow's exemption leaves with its approval",
                      wf not in (cfg.get('github_ci_approved') or {}) and
                      [e['path'] for e in cfg.get('ci_workflow_outside_vendoring_exempt', [])]
                      == ['.github/workflows/other.yml']))
    except (OSError, subprocess.CalledProcessError, KeyError, TypeError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out = ('precedent_vendor_engine refresh OK (consumer): 59 file(s) refreshed from main '
           '@ e8a2bc67cc8d (was 37fc3b551579)\n'
           'precedent_vendor_engine refresh OK (consumer): 61 file(s) refreshed from main '
           '@ e8a2bc67cc8d (was e8a2bc67cc8d)\n')
    cases.append(('5. the engine line names the commit the repo was on before the refresh',
                  bool(pu.engine_summary) and
                  '(was 37fc3b551579)' in pu.engine_summary(out, '37fc3b55157907e6')))
    cases.append(('5. the engine hands its second pass the pre-refresh commit',
                  hasattr(pve, '_WAS_COMMIT_ENV')))
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_update_vendors_rebaselines_a_file_now_identical_to_upstream():
    """A synced manifest entry OUTSIDE the vendored tree whose file the
    update replaced with exactly upstream's copy gets its baseline moved.

    2026-09-28, a consumer: .claude/hooks/session-start.sh was rewritten to
    the current template, byte for byte process/upstream/templates/harness/
    claude-code/hooks/session-start.sh, and its entry kept the old hash, so
    practice_audit reported DRIFT at the Promote. One that differs from
    upstream still reads as drift."""
    import hashlib, tempfile
    pu, _pve, _pr = _update_tools()
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rebaseline-'))
    try:
        up = 'templates/harness/claude-code/hooks/session-start.sh'
        (tmp / 'process' / 'upstream' / pathlib.Path(up).parent).mkdir(parents=True)
        (tmp / 'process' / 'upstream' / up).write_text('#!/bin/sh\n# new template\n')
        (tmp / '.claude' / 'hooks').mkdir(parents=True)
        (tmp / '.claude' / 'hooks' / 'session-start.sh').write_text('#!/bin/sh\n# new template\n')
        (tmp / 'process' / 'upstream' / 'templates' / 'x.md').write_text('upstream x\n')
        (tmp / 'X.md').write_text('edited here\n')
        (tmp / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'vendored_at': 'process/upstream'},
            'entries': [
                {'practice': 'session-start', 'status': 'synced', 'granularity': 'file',
                 'local_path': '.claude/hooks/session-start.sh', 'upstream_path': up,
                 'local_sha256': 'old'},
                {'practice': 'x', 'status': 'synced', 'granularity': 'file',
                 'local_path': 'X.md', 'upstream_path': 'templates/x.md',
                 'local_sha256': 'old'}]}))
        done = pu.rebaseline_vendored_entries(tmp)
        entries = json.loads((tmp / 'process' / 'manifest.json').read_text())['entries']
        cases.append(('a file now identical to its upstream_path is re-baselined',
                      done == ['.claude/hooks/session-start.sh'] and entries[0]['local_sha256']
                      == hashlib.sha256(b'#!/bin/sh\n# new template\n').hexdigest()))
        cases.append(('...and one that differs from upstream still reads as drift',
                      entries[1]['local_sha256'] == 'old'))
        # 2026-10-02: a file instantiated from a template that THIS run
        # rewrote (a migration's AGENTS.md, settings.json, .gitignore) is
        # re-recorded even though it is not upstream's text; the same file
        # NOT rewritten by the run is still drift.
        done = pu.rebaseline_vendored_entries(tmp, rewritten={'X.md'})
        entries = json.loads((tmp / 'process' / 'manifest.json').read_text())['entries']
        cases.append(('a template-instantiated file this run rewrote is '
                      're-baselined though it differs from upstream',
                      done == ['X.md'] and entries[1]['local_sha256']
                      == hashlib.sha256(b'edited here\n').hexdigest()))
        (tmp / 'X.md').write_text('edited again by a person\n')
        done = pu.rebaseline_vendored_entries(tmp, rewritten={'OTHER.md'})
        cases.append(('...and the same file, when the run did not touch it, '
                      'still reads as drift', done == []))

        # The scrub-blocklist decision. No key and no default file fails
        # the audit; a public repo gets an explicit null with its reason, a
        # repo not declared public is asked, never decided for.
        ensure = getattr(pu, 'ensure_scrub_blocklist_decision', None)
        (tmp / 'precedent.json').write_text(json.dumps({'visibility': 'private'}))
        cases.append(('a repo not declared public is asked about its scrub '
                      'blocklist, not given a null',
                      ensure is not None and ensure(tmp) == 'ask'
                      and 'scrub_blocklist' not in json.loads(
                          (tmp / 'process' / 'manifest.json').read_text())['upstream']))
        (tmp / 'precedent.json').write_text(json.dumps({'visibility': 'public'}))
        got = ensure(tmp) if ensure else None
        upd = json.loads((tmp / 'process' / 'manifest.json').read_text())['upstream']
        cases.append(('a public repo with no list gets scrub_blocklist: null, '
                      'with its reason beside it',
                      got == 'null' and 'scrub_blocklist' in upd
                      and upd['scrub_blocklist'] is None
                      and 'public' in upd.get('_scrub_blocklist_note', '')))
        cases.append(('...and a second run leaves the decision alone',
                      ensure(tmp) is None if ensure else False))
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('Update Vendors moves the baseline of a file it made identical to upstream',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_legacy_leftovers_retired_by_content():
    """The old install's leftovers leave an install on its next refresh,
    recognised by CONTENT -- tracked or not, hand-paused or not -- and a file
    that only shares a name is kept and reported.

    Morgan, 2026-09-24 (strength: decided): "this needs to be deleted from
    ALL installs". Measured that day in six installs: `bestpractice-docs.yml`,
    retired three days earlier, survived in all five that had it, because
    both removers only considered a path the manifest had recorded while its
    hash still matched. Two had hand-paused it (hash mismatch, kept), three
    had never tracked it (invisible).

    THE NEGATIVE CONTROLS ARE THE POINT. The 2026-09-20 sweep deleted nine
    live checks by trusting names (spec/CI_MINUTES_PLAN.md item 14), so
    every deletion case below is paired with the same name in a shape that
    must survive: hand-authored content, a live trigger, uncommitted edits,
    and `light-check.yml`, which is on no list at all."""
    import precedent_vendor_engine as pve
    import practice_audit as pa
    import contextlib, io, tempfile

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-legacy-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='harness@example.com',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='harness@example.com')

    def g(repo, *a):
        return subprocess.run(['git', '-C', str(repo), *a], env=env,
                              capture_output=True, text=True)

    sync_stock = ('name: BestPractice sync\non:\n  # schedule:\n  #   - cron: x\n'
                  '  workflow_dispatch:\njobs:\n  update:\n    runs-on: u\n'
                  '    steps:\n      - uses: actions/checkout@v4\n'
                  '      - uses: anthropics/claude-code-action@v1\n'
                  '        with:\n          anthropic_api_key: '
                  '${{ secrets.ANTHROPIC_API_KEY }}\n')
    docs_paused = ('name: Precedent documentation checks\non:\n'
                   '  # push:\n  workflow_dispatch:\njobs:\n  m:\n'
                   '    steps:\n      - uses: actions/checkout@v4\n'
                   '      - uses: actions/setup-python@v5\n'
                   '      - run: python -m pip install cmarkgfm\n'
                   '      - run: python3 process/upstream/tools/doc_lint.py\n')
    docs_own = ('name: our docs\non:\n  workflow_dispatch:\njobs:\n  m:\n'
                '    steps:\n      - uses: actions/checkout@v4\n'
                '      - run: python3 tools/our_own_check.py\n')
    light = ('name: light\non:\n  workflow_dispatch:\njobs:\n  l:\n'
             '    steps:\n      - uses: actions/checkout@v4\n'
             '      - run: python3 tools/light_check.py\n')

    def make(name, files, manifest=None):
        repo = tmp / name
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding='utf-8')
        if manifest is not None:
            (repo / 'tools').mkdir(parents=True, exist_ok=True)
            (repo / 'tools' / pve.MANIFEST_NAME).write_text(
                json.dumps(manifest), encoding='utf-8')
        g(repo, 'init', '-q')
        g(repo, 'add', '-A')
        g(repo, 'commit', '-qm', 'base')
        return repo

    def sweep(repo, kind='consumer'):
        mp = repo / 'tools' / pve.MANIFEST_NAME
        m = json.loads(mp.read_text(encoding='utf-8')) if mp.is_file() else {}
        pve._LEFT_FOR_YOU.clear()
        pve._remove_retired_ci_workflow_files(repo, m, kind)
        res = pve.retire_legacy_leftovers(repo, m, kind)
        left = list(pve._LEFT_FOR_YOU)
        pve._LEFT_FOR_YOU.clear()
        return res, left

    def left_names(left, rel):
        return [why for item, why in left if item == rel]

    SYNC = '.github/workflows/bestpractice-upstream-sync.yml'
    DOCS = '.github/workflows/bestpractice-docs.yml'
    LIGHT = '.github/workflows/light-check.yml'
    try:
        # 1. A stock-shaped legacy workflow goes, untracked -- and tracked.
        r1 = make('untracked', {SYNC: sync_stock, LIGHT: light},
                  {'kind': 'consumer'})
        res, left = sweep(r1)
        cases.append(('an UNTRACKED stock-shaped upstream sync is deleted',
                      not (r1 / SYNC).exists(), str(res)))
        regp = r1 / 'process' / 'decommissioned_paths.json'
        reg = (json.loads(regp.read_text(encoding='utf-8')) if regp.is_file()
               else {'decommissioned': []})
        cases.append(('and recorded in process/decommissioned_paths.json',
                      [e['path'] for e in reg['decommissioned']] == [SYNC],
                      str(reg['decommissioned'])))
        cases.append(('and its deletion is staged, so decommission-deletes-'
                      'files sees it gone', SYNC not in g(r1, 'ls-files').stdout,
                      g(r1, 'status', '--short').stdout))
        cases.append(('the secrets only it read are named for the person',
                      {'ANTHROPIC_API_KEY'} <= set(res['secrets']),
                      str(res['secrets'])))
        # 2026-10-17: a legacy secret name this repo never carried is not
        # (check_legacy_secret_named_only_where_the_repo_had_it).
        cases.append(('...and a legacy secret it never carried is not',
                      'PERSONAL_PACK_TOKEN' not in res['secrets'],
                      str(res['secrets'])))
        cases.append(('NEGATIVE: light-check.yml is never touched, whatever '
                      'it runs', (r1 / LIGHT).is_file(), ''))

        tracked_hash = 'f' * 64      # recorded, then hand-edited since
        r1b = make('tracked', {SYNC: sync_stock},
                   {'kind': 'consumer', 'ci_workflow_files': [SYNC],
                    'ci_workflows_sha256': {SYNC: tracked_hash}})
        sweep(r1b)
        cases.append(('a TRACKED copy whose hash no longer matches is deleted '
                      'by content too', not (r1b / SYNC).exists(), ''))

        # 2. The hand-paused bestpractice-docs.yml shape (two real installs),
        #    with the `diverged` process/manifest.json entry three carried.
        pm = {'upstream': {'vendored_at': 'process/upstream'},
              'entries': [{'practice': 'doc-lint-workflow',
                           'local_path': DOCS, 'status': 'diverged'},
                          {'practice': 'other', 'local_path': 'X.md'}]}
        r2 = make('paused', {DOCS: docs_paused,
                             'process/manifest.json': json.dumps(pm, indent=2)},
                  {'kind': 'consumer', 'ci_workflow_files': [DOCS],
                   'ci_workflows_sha256': {DOCS: tracked_hash}})
        sweep(r2)
        cases.append(('the hand-paused bestpractice-docs.yml is deleted',
                      not (r2 / DOCS).exists(), ''))
        entries = json.loads((r2 / 'process' / 'manifest.json').read_text(
            encoding='utf-8'))['entries']
        cases.append(('its process/manifest.json entry goes with it, and '
                      'only that one', [e['practice'] for e in entries]
                      == ['other'], str(entries)))

        # 3-4. A practice SOURCE converges like a consumer (2026-10-01): a
        #    recognised leftover goes even on a live trigger, and a file that
        #    runs something nothing local runs is held and asked about. Until
        #    then a source was the one kind that kept every workflow.
        r3 = make('own', {DOCS: docs_own}, {'kind': 'source'})
        res, left = sweep(r3, 'source')
        cases.append(('in a practice source, a same-name hand-authored '
                      'workflow running its own script is held, and the '
                      'person is asked', (r3 / DOCS).is_file()
                      and any('ASK THE PERSON' in w for w in left_names(left, DOCS)),
                      str(left)))
        live = sync_stock.replace('  workflow_dispatch:', '  push:\n  '
                                  'workflow_dispatch:')
        r4 = make('live', {SYNC: live}, {'kind': 'source'})
        res, left = sweep(r4, 'source')
        cases.append(('in a practice source, a stock-shaped file on a LIVE '
                      'trigger goes too', not (r4 / SYNC).is_file(), str(res)))

        # 4c. In a CONSUMER both of those go (2026-09-27, CI_CONVERGES_KINDS):
        #     the checks run locally, so a live workflow nobody approved is
        #     what the change exists to stop. Committed and clean, so git
        #     history keeps the content.
        docs_covered = docs_own.replace('tools/our_own_check.py',
                                        'tools/doc_lint.py')
        r4c = make('consumer-live', {SYNC: live, DOCS: docs_covered},
                   {'kind': 'consumer'})
        res, left = sweep(r4c)
        cases.append(('in a consumer, a live leftover of the old install and a '
                      'hand-authored workflow running only what the local '
                      'push check runs are removed, with nothing left to ask',
                      not (r4c / SYNC).exists() and not (r4c / DOCS).exists()
                      and not left_names(left, SYNC)
                      and not left_names(left, DOCS),
                      f'{res} {left}'))
        # 4d. NEGATIVE: nothing needed is lost. A workflow running a script
        #     the local push check does not run is kept, and the report names
        #     the script (Morgan, 2026-09-27: "it should do a check first to
        #     make sure nothing needed is being lost").
        r4d = make('consumer-needed', {DOCS: docs_own}, {'kind': 'consumer'})
        res, left = sweep(r4d)
        cases.append(('NEGATIVE: in a consumer, a workflow running a script the '
                      'local push check does not run is kept, naming it',
                      (r4d / DOCS).is_file() and any(
                          'our_own_check.py' in w and 'LEFT ALONE' in w
                          for w in left_names(left, DOCS)), f'{res} {left}'))

        # 4b. NEGATIVE: uncommitted edits are never destroyed.
        r4b = make('dirty', {SYNC: sync_stock}, {'kind': 'consumer'})
        (r4b / SYNC).write_text(sync_stock + '# local edit\n', encoding='utf-8')
        sweep(r4b)
        cases.append(('NEGATIVE: a copy with uncommitted edits is kept',
                      (r4b / SYNC).is_file(), ''))

        # 5. Hooks. The tombstone ships empty (no hook was ever retired), so
        #    the mechanism is exercised with a planted entry.
        saved = dict(pve.RETIRED_HOOK_FILES)
        try:
            pve.RETIRED_HOOK_FILES.clear()
            pve.RETIRED_HOOK_FILES.update({
                'old-gate.sh': ('retired in a test', lambda t: 'OLD-GATE' in t),
                'wired-old.sh': ('retired in a test', lambda t: 'OLD-GATE' in t),
                'mine.sh': ('retired in a test', lambda t: 'OLD-GATE' in t)})
            settings = {'hooks': {'Stop': [{'hooks': [{
                'type': 'command',
                'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/wired-old.sh'}]}]}}
            r5 = make('hooks', {
                '.claude/hooks/old-gate.sh': '#!/bin/sh\n# OLD-GATE\n',
                '.claude/hooks/wired-old.sh': '#!/bin/sh\n# OLD-GATE\n',
                '.claude/hooks/mine.sh': '#!/bin/sh\necho ours\n',
                '.claude/settings.json': json.dumps(settings)},
                {'kind': 'consumer'})
            res, left = sweep(r5)
            cases.append(('an UNTRACKED retired hook nothing calls is removed',
                          not (r5 / '.claude/hooks/old-gate.sh').exists(),
                          str(res)))
            cases.append(('NEGATIVE: a hand-authored hook under a retired name '
                          'is kept', (r5 / '.claude/hooks/mine.sh').is_file(),
                          ''))
            cases.append(('NEGATIVE: a retired hook settings.json still calls '
                          'is kept, and the report says to un-wire it',
                          (r5 / '.claude/hooks/wired-old.sh').is_file() and any(
                              'still wired' in w for w in left_names(
                                  left, '.claude/hooks/wired-old.sh')),
                          str(left)))
        finally:
            pve.RETIRED_HOOK_FILES.clear()
            pve.RETIRED_HOOK_FILES.update(saved)
        cases.append(('the shipped hook tombstone is a dict the sweep reads',
                      isinstance(pve.RETIRED_HOOK_FILES, dict), ''))

        # 6. ci_debounce_minutes, removed without reformatting the file.
        cfg = ('{\n  "format_version": 1,\n  "_comment": ["keep  spacing"],\n'
               '  "ci_debounce_minutes": 360,\n  "_ci_debounce_minutes_retired": '
               '["a note"],\n  "sources": []\n}\n')
        r6 = make('debounce', {'precedent.json': cfg,
                               'identity.json': '{"ci_debounce_minutes": 30}\n'},
                  {'kind': 'consumer'})
        sweep(r6)
        after = (r6 / 'precedent.json').read_text(encoding='utf-8')
        cases.append(('ci_debounce_minutes is removed from precedent.json',
                      'ci_debounce_minutes"' not in after.replace(
                          '_ci_debounce_minutes_retired', ''), after))
        cases.append(('NEGATIVE: every other byte stays, including a '
                      'comment key that names the field',
                      after == cfg.replace('  "ci_debounce_minutes": 360,\n',
                                           ''), after))
        cases.append(('and from identity.json, as its last member',
                      json.loads((r6 / 'identity.json').read_text(
                          encoding='utf-8')) == {}, ''))

        # 7. Stale source paths, and a hardcoded identity.
        pj = {'sources': [
            {'name': 'precedent-shared-acme',
             'path': '../precedent-team-acme', 'level': 'shared'},
            {'name': 'precedent-shared-other',
             'path': '../precedent-shared-other', 'level': 'shared'}]}
        r7 = make('paths', {'precedent.json': json.dumps(pj),
                            'tools/bootstrap.sh':
                                'git config user.name "A Person"\n'
                                'git config --global user.email "$email"\n'},
                  {'kind': 'consumer'})
        with contextlib.redirect_stdout(io.StringIO()):
            _res, left = sweep(r7)
        flagged = [i for i, _w in left if i.startswith('precedent.json source')]
        # Repointed, not reported, since 2026-09-28: the rename is fixed, and
        # nothing is cloned at the old path here to make the move unsafe.
        paths7 = [s['path'] for s in json.loads(
            (r7 / 'precedent.json').read_text(encoding='utf-8'))['sources']]
        cases.append(('a stale ../precedent-team-* source path is repointed',
                      paths7 == ['../precedent-shared-acme',
                                 '../precedent-shared-other']
                      and not any('acme' in i for i in flagged),
                      f'{paths7} {flagged}'))
        cases.append(('NEGATIVE: a current ../precedent-shared-* path is not',
                      not any('other' in i for i in flagged),
                      str(flagged)))
        ids = [i for i, _w in left if i.startswith('tools/bootstrap.sh')]
        cases.append(('a literal git identity is reported; one read from a '
                      'variable is not', ids == ['tools/bootstrap.sh:1'],
                      str(ids)))

        # 8. An install with no ENGINE_MANIFEST is detected and routed to
        #    the migration -- by practice_audit, the tool it CAN run.
        def install(name, manifest):
            root = tmp / name
            (root / 'process' / 'upstream' / 'practices').mkdir(parents=True)
            (root / 'precedent.json').write_text(json.dumps(
                {'sources': [{'name': 'precedent', 'level': 'universal',
                              'path': 'process/upstream'}]}), encoding='utf-8')
            (root / 'AGENTS.md').write_text(pa.LOADER_MARKER + '\n',
                                            encoding='utf-8')
            if manifest:
                (root / 'tools').mkdir()
                (root / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}')
            return root
        gap = pa.engine_gap(install('unmigrated', False))
        cases.append(('no tools/ENGINE_MANIFEST.json is detected and routed '
                      'to the migration document',
                      bool(gap) and 'MIGRATING_EXISTING_INSTALLS' in gap,
                      str(gap)))
        cases.append(('NEGATIVE: a migrated install is not flagged',
                      pa.engine_gap(install('migrated', True)) is None, ''))
        classic = install('classic', False)
        (classic / 'AGENTS.md').write_text('no block\n', encoding='utf-8')
        cases.append(('NEGATIVE: a classic install is left to check 5, which '
                      'already says migrate, whole',
                      pa.engine_gap(classic) is None, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_engine_checks_can_be_reached_by_what_you_touched():
    """A check with no practice file could only ever be reached by its
    rotation turn.

    THE INCIDENT (2026-09-22). `dogfooded-hooks-match-template` exists to
    catch a fix landing in `.claude/hooks/` and not in the template every
    other repo installs. Exactly that happened, in the same session that
    hardened the hook -- and the check stayed silent, because it was not in
    that commit's rotation slice and nothing about touching the file could
    summon it. `_scoped_tree_slugs` tier 2 reads its globs from
    `practices/<slug>.md`, and an engine-property check has none by design,
    so all eighteen of them fell straight through to the rotation. It
    surfaced only because a session ran it by name on a hunch.

    Asserted here rather than left to the selector's own shape: a scheduler
    that quietly reaches less than it claims is the failure mode, and it
    looks identical to everything being fine.
    """
    import importlib
    cases = []
    try:
        pc = importlib.import_module('precedent_check')
    except Exception as e:
        return (False, '', f'precedent_check would not import: {e}')

    saved = pc._touched_files
    try:
        tree = sorted(sl for sl in pc.CHECKS if pc.CHECKS[sl]['scope'] == 'tree')

        def selected_for(*paths):
            pc._touched_files = lambda: list(paths)
            return set(pc._scoped_tree_slugs(tree))

        # Both sides of the pair reach it -- a fix can land in either copy.
        for side in ('.claude/hooks/freshness-guard.sh',
                     'templates/harness/claude-code/hooks/freshness-guard.sh'):
            cases.append((f'touching {side} selects '
                          f'dogfooded-hooks-match-template',
                          'dogfooded-hooks-match-template' in selected_for(side)))

        # ...and it is selection, not "everything always runs": an unrelated
        # file must not force it. (The rotation may still pick it up, which
        # is why this asserts against a file list chosen to sit in no
        # declared glob, not against the check being absent generally.)
        pc._touched_files = lambda: ['README.md']
        forced = pc._scoped_tree_slugs(tree, buckets=set())
        cases.append(('an unrelated file does not force-select it',
                      'dogfooded-hooks-match-template' not in forced))

        # The declared set and the known-undeclared set must together cover
        # every engine-property tree check, or a new one has gone dark
        # without anyone choosing that.
        engine = {sl for sl in tree
                  if not pc.CHECKS[sl].get('practice_backed', True)}
        declared = {sl for sl in engine if pc.CHECKS[sl].get('selects_on')}
        unaccounted = engine - declared - ENGINE_CHECKS_WITHOUT_DECLARED_PATHS
        cases.append((f'every engine-property check is either declared or '
                      f'listed as knowingly undeclared '
                      f'(unaccounted: {sorted(unaccounted) or "none"})',
                      not unaccounted))

        # The list may only shrink. A name in it that HAS declared paths is
        # a stale entry, not a failure -- but it must be removed, or the
        # list stops meaning anything.
        stale = ENGINE_CHECKS_WITHOUT_DECLARED_PATHS & declared
        cases.append((f'the knowingly-undeclared list carries no stale '
                      f'entries (stale: {sorted(stale) or "none"})',
                      not stale))
    finally:
        pc._touched_files = saved

    failed = [n for n, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_one_python():
    """practice one-python: a tool that starts Python by name, and a workflow
    on another version than the declared one, are refused; sys.executable,
    a fixture string and a matching workflow pass. And precedent_python
    reads the declaration, defaults it, and adds the engine's own packages.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    import precedent_python as pp

    def judge(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-one-python-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        subprocess.run(['git', '-C', str(d), 'init', '-q'], capture_output=True)
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in pc._one_python(pc.Ctx(paths=['x'])))
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    cases = []
    out = judge({'tools/a.py': "import subprocess\nsubprocess.run(['python3', 'b.py'])\n"})
    cases.append(('a tool starting python3 by name is refused', 'tools/a.py:2' in out, out))
    out = judge({'tools/a.py': "import subprocess as sp\nsp.check_output(('python', 'b.py'))\n"})
    cases.append(('...and `python` in a tuple, through an alias', 'tools/a.py:2' in out, out))
    out = judge({'tools/a.py': "import subprocess, sys\nsubprocess.run([sys.executable, 'b.py'])\n"
                               "FIXTURE = \"subprocess.run(['python3', 'x.py'])\"\n"})
    cases.append(('sys.executable passes, and a fixture string is prose', out == '', out))
    wf = 'jobs:\n  t:\n    steps:\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "{}"\n'
    out = judge({'precedent.json': '{"python": {"version": "3.12"}}\n',
                 '.github/workflows/t.yml': wf.format('3.11'), 'tools/a.py': 'x = 1\n'})
    cases.append(('a workflow on another version is refused', '3.11' in out and '3.12' in out, out))
    out = judge({'.github/workflows/t.yml': wf.format(pp.DEFAULT_VERSION), 'tools/a.py': 'x = 1\n'})
    cases.append(('no declaration: the default, matched by the workflow, passes', out == '', out))

    d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-one-python-decl-'))
    try:
        cases.append(('no precedent.json: the default version and the engine packages',
                      pp.declared(d) == (pp.DEFAULT_VERSION, pp.BASE_PACKAGES), pp.declared(d)))
        (d / 'precedent.json').write_text('{"python": {"version": "3.13", "packages": ["numpy", "markdown"]}}')
        got = pp.declared(d)
        cases.append(('a declaration is read, the engine packages added once',
                      got == ('3.13', ['cmarkgfm', 'markdown', 'numpy']), got))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    exe = pp.interpreter(pp.DEFAULT_VERSION) or sys.executable
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-one-python-env-'))
    env = dict(os.environ, CLAUDE_ENV_FILE=str(tmp / 'env'), XDG_CACHE_HOME=str(tmp / 'cache'))
    try:
        r = subprocess.run([sys.executable, '-c',
                            'import sys; sys.path.insert(0, sys.argv[1]); import precedent_python as pp; '
                            'd = pp.make_shims(sys.argv[2], "9.9"); print(d); print(pp.export_path(d) or "ok")',
                            str(ROOT / 'tools'), exe], env=env, capture_output=True, text=True)
        lines = r.stdout.split()
        shim = pathlib.Path(lines[0]) if lines else tmp
        written = (tmp / 'env').read_text() if (tmp / 'env').exists() else ''
        v = subprocess.run([str(shim / 'python3'), '-c', 'import sys; print(sys.executable)'],
                           capture_output=True, text=True).stdout.strip()
        cases.append(('setup links python3 to the declared Python and puts it first on PATH '
                      'through the session environment file',
                      lines[-1:] == ['ok'] and f'export PATH="{shim}:$PATH"' in written
                      and pathlib.Path(v).resolve() == pathlib.Path(exe).resolve(),
                      (r.stdout, failure_detail(r.stderr, 300), written, v)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # The Python hooks run (2026-10-16): the session file never reaches a
    # hook, so setup, which runs inside one, also gives the engine packages
    # to the Python running it -- and leaves it alone when that IS the
    # declared one (a shim resolves to it).
    saved_install = pp.install
    calls = []
    try:
        pp.install = lambda e, p: calls.append((e, list(p))) or ''
        pp.hook_install('/usr/bin/python3.12', running='/usr/bin/python3.13')
        cases.append(('setup also installs the engine packages into the Python '
                      'hooks run, when it is not the declared one',
                      calls == [('/usr/bin/python3.13', pp.BASE_PACKAGES)], calls))
        calls.clear()
        pp.hook_install(exe, running=exe)
        cases.append(('...and does nothing when that Python is the declared one',
                      calls == [], calls))
        pp.install = lambda e, p: 'pip refused'
        why = pp.hook_install('/usr/bin/python3.12', running='/usr/bin/python3.13')
        cases.append(('...and a failure there names the hook Python',
                      'Python hooks run' in why and 'python3.13' in why, why))
    finally:
        pp.install = saved_install

    # Which Python a hook's python3 IS (2026-10-16). Claude Code starts a hook
    # with its own PATH, so each tools/*.sh that starts python3 (and the
    # bootstrap template a consumer's own copy comes from) carries one
    # block putting <checkout>/.precedent/python-bin first, and setup leaves
    # that link. Run the real block, cut from a real gate, with a PATH that
    # has no shim on it: with the link its python3 is the declared one,
    # without it python3 is whatever PATH gave (never a refusal).
    start, end = '# THE DECLARED PYTHON (', 'PATH="$_precedent_pybin:$PATH"; fi\n'
    blocks = {}
    for f in sorted((ROOT / 'tools').glob('*.sh')) + [ROOT / 'templates' / 'bootstrap.sh']:
        text = f.read_text(encoding='utf-8')
        if 'python3 ' not in text:
            continue
        a = text.find(start)
        b = text.find(end, a)
        first_py = min((m.start() for m in re.finditer(r'python3 ', text)
                        if not text[text.rfind('\n', 0, m.start()) + 1:m.start()].lstrip().startswith('#')),
                       default=-1)
        blocks[str(f.relative_to(ROOT))] = text[a:b + len(end)] if 0 <= a < b and (first_py < 0 or b < first_py) else None
    missing = sorted(n for n, v in blocks.items() if v is None)
    cases.append(('every hook script that starts python3 puts the declared Python first, '
                  'before its first python3, in one identical block',
                  not missing and len({v for v in blocks.values()}) == 1,
                  f'missing or after the first python3 in {missing}' if missing
                  else f'{len(set(blocks.values()))} different copies'))
    block = blocks.get('tools/push-check-gate.sh') or ''
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-one-python-hook-'))
    try:
        (tmp / 'tools').mkdir()
        probe = tmp / 'tools' / 'probe.sh'
        probe.write_text('#!/usr/bin/env bash\nset -euo pipefail\n' + block
                         + 'command -v python3 || echo none\n')
        shims = tmp / 'shims'
        shims.mkdir()
        (shims / 'python3').write_text('#!/bin/sh\necho declared\n')
        (shims / 'python3').chmod(0o755)
        bare_path = '/usr/local/bin:/usr/bin:/bin'
        run = lambda: subprocess.run(['bash', str(probe)], cwd='/', capture_output=True, text=True,
                                     env={'PATH': bare_path, 'HOME': str(tmp)})
        r = run()
        cases.append(('...with no link, a hook keeps the python3 PATH gave it and runs on',
                      r.returncode == 0 and str(tmp) not in r.stdout, (r.stdout, failure_detail(r.stderr, 300))))
        cases.append(('...setup links the declared Python for the hooks',
                      pp.link_for_hooks(shims, tmp) == ''
                      and os.readlink(tmp / '.precedent' / 'python-bin') == str(shims),
                      sorted(str(x) for x in tmp.rglob('*'))))
        r = run()
        cases.append(('...and then a hook started with no shim on its PATH, from another '
                      'directory, runs the declared python3',
                      r.returncode == 0 and r.stdout.strip() == str(tmp / '.precedent' / 'python-bin' / 'python3'),
                      (r.stdout, failure_detail(r.stderr, 300))))
        other = tmp / 'other'
        other.mkdir()
        cases.append(('...and setup run again for another version repoints the link',
                      pp.link_for_hooks(other, tmp) == ''
                      and os.readlink(tmp / '.precedent' / 'python-bin') == str(other),
                      os.readlink(tmp / '.precedent' / 'python-bin')))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, det) for n, ok, det in cases if not ok]
    check(f'one Python: tools start Python with sys.executable, workflows match the '
          f'declared version, and setup makes python3 mean it ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_bootstrap_says_the_python_warning_once():
    """In a local session, both bootstrap.sh copies run the Python check
    once, so a machine whose python3 is not the declared version hears the
    warning once per session start, not twice.

    Found 2026-10-17 by the very deep check's install rehearsal, on Python
    3.13: `check >/dev/null || check` ran the check again on failure, and
    the warning, on stderr both times, printed twice. Decision chosen by the
    session under Morgan's delegation of 2026-10-17 ("Fix the other issues
    you found including the checks that never run. Tell me what you decide.
    I will be offline so don't wait for me. Approved, act, and Booked.").

    Negative control, measured 2026-10-17: both copies before the fix run
    the stub twice.
    """
    import tempfile
    cases = []
    for rel in ('tools/bootstrap.sh', 'templates/bootstrap.sh'):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / 'tools').mkdir()
            shutil.copy(ROOT / rel, d / 'tools' / 'bootstrap.sh')
            (d / 'tools' / 'precedent_python.py').write_text(
                'import pathlib, sys\n'
                'f = pathlib.Path(__file__).with_name("calls")\n'
                'f.write_text(f.read_text() + "x" if f.exists() else "x")\n'
                'print("precedent_python: python3 here is 3.13", file=sys.stderr)\n'
                'sys.exit(1)\n', encoding='utf-8')
            r = subprocess.run(['bash', 'tools/bootstrap.sh'], cwd=str(d), capture_output=True,
                               text=True, timeout=120,
                               env=dict(os.environ, PRECEDENT_LOCAL_SESSION='1'))
            calls = (d / 'tools' / 'calls').read_text() if (d / 'tools' / 'calls').exists() else ''
            cases.append((f'{rel}: the check runs once and its warning prints once',
                          calls == 'x' and r.stderr.count('python3 here is 3.13') == 1,
                          f'{len(calls)} call(s); {failure_detail(r.stderr, 300)}'))
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_vendored_container_scan_knows_a_refresh_branch():
    """A copy of precedent_container_safe.py standing alone -- as it is
    vendored into a source set or a consumer, without
    precedent_refresh_sources.py beside it -- leaves a local branch holding
    only a session-start engine refresh out of "work only here", and still
    reports a local branch holding real work.

    2026-10-29: a consumer container held one such branch per source clone
    after every worker restart, and the vendored scan called the container
    NOT SAFE TO LOSE over them, twice in one day, because the test for a
    refresh branch was imported from a file that is not vendored and the
    import failed silently.

    practice: control-asserts-which-failure -- the work branch is the control.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vendored-safe-'))
    cases = []
    try:
        lone = tmp / 'tools'
        lone.mkdir()
        shutil.copy(ROOT / 'tools' / 'precedent_container_safe.py', lone)
        origin, repo = tmp / 'origin.git', tmp / 'clone'
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x',
               'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}

        def git(*a, cwd=repo):
            return subprocess.run(['git', *a], cwd=str(cwd), env=env,
                                  capture_output=True, text=True)
        git('init', '-q', '--bare', '-b', 'main', str(origin), cwd=tmp)
        git('init', '-q', '-b', 'main', str(repo), cwd=tmp)
        (repo / 'a.txt').write_text('a\n')
        git('add', '-A'); git('commit', '-qm', 'base')
        git('remote', 'add', 'origin', str(origin)); git('push', '-q', 'origin', 'main')
        git('checkout', '-qb', '2026-10-29-x-engine-refresh-79b768aa-aaaaa-bbbbb')
        (repo / 'engine.py').write_text('e\n')
        git('add', '-A')
        git('commit', '-qm', 'Refresh the vendored engine to BestPractice 79b768aaba0b')
        git('checkout', '-q', 'main')

        def scan():
            code = ('import sys, json; sys.path.insert(0, sys.argv[1]); '
                    'import precedent_container_safe as c; '
                    'print(json.dumps(c.scan_one(sys.argv[2])["unsafe"]))')
            r = subprocess.run([sys.executable, '-I', '-c', code, str(lone),
                                str(repo)], capture_output=True, text=True,
                               cwd=str(tmp))
            return json.loads(r.stdout or 'null') if r.returncode == 0 else r.stderr[-200:]

        got = scan()
        cases.append(('a lone copy leaves a refresh-only branch out',
                      got == [], f'got {got}'))
        git('checkout', '-qb', 'real-work')
        (repo / 'b.txt').write_text('b\n')
        git('add', '-A'); git('commit', '-qm', 'A real change')
        git('checkout', '-q', 'main')
        got = scan()
        cases.append(('control: a lone copy still reports a branch of real work',
                      isinstance(got, list) and len(got) == 1
                      and 'real-work' in got[0]
                      and 'engine-refresh' not in got[0], f'got {got}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_container_check_lists_commands_still_running():
    """tools/precedent_container_safe.py lists every shell the session's
    agent started that is still running (2026-09-28: two wait loops ran five
    hours after their script finished, because `pgrep -f` matched the
    loop's own command line, while this tool called the container clean).
    Planted process tables, no real processes. Discriminating cases: the
    check's own ancestor shell, the agent's non-shell children and another
    person's terminal are never listed; with no agent above it, nothing is
    listed rather than guessed."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_container_safe as pcs
    WRAP = ("/bin/bash -c source /root/.claude/shell-snapshots/s.sh && eval "
            "'until ! pgrep -f scratchpad/x/runcases.py >/dev/null; do sleep 5; "
            "done' < /dev/null && pwd -P")
    rows = [
        (1, 0, '06:00:00', '/sbin/init'),
        (100, 1, '06:00:00', '/opt/claude-code/bin/claude --output-format=stream-json'),
        (200, 100, '05:12:32', WRAP),
        (201, 200, '00:00:03', 'sleep 5'),
        (300, 100, '00:00:01', '/bin/bash -c python3 tools/precedent_container_safe.py'),
        (301, 300, '00:00:01', 'python3 tools/precedent_container_safe.py'),
        (400, 100, '06:00:00', 'node /opt/mcp/server.js'),
        (500, 1, '03:00:00', '-zsh'),
    ]
    cases = []
    got = pcs.still_running(rows, me=301)
    cases.append(('THE CASE THIS EXISTS FOR: the stray wait loop is listed, '
                  'with what it runs', [r['pid'] for r in got] == [200]
                  and 'pgrep -f scratchpad/x/runcases.py' in got[0]['command']
                  and got[0]['elapsed'] == '05:12:32', repr(got)))
    cases.append(('the shell running the check itself is never listed',
                  all(r['pid'] != 300 for r in got), repr(got)))
    cases.append(("the agent's own non-shell children and another terminal "
                  'are never listed', all(r['pid'] not in (400, 500) for r in got),
                  repr(got)))
    # A hook the harness fired for the same event is the agent's child too,
    # and is not the session's work (2026-09-30: freshness-guard.sh beside
    # the reply gate forbade the archive line). A real background command,
    # and a hook script the session itself ran in its own tool shell, still
    # are.
    hooks = rows + [
        (600, 100, '00:00:02', '/bin/sh -c $CLAUDE_PROJECT_DIR/.claude/hooks/'
                               'freshness-guard.sh user-prompt staging'),
        (601, 100, '00:00:01', '/bin/bash -c cd "${GEMINI_PROJECT_DIR:-.}" && '
                               'bash .claude/hooks/stop-git-check.sh'),
        (602, 100, '00:10:00', "/bin/bash -c source /root/.claude/shell-snapshots/"
                               "s.sh && eval 'sleep 600' < /dev/null && pwd -P"),
        (603, 100, '00:05:00', "/bin/bash -c source /root/.claude/shell-snapshots/"
                               "s.sh && eval 'bash .claude/hooks/push-check-gate.sh "
                               "&' < /dev/null && pwd -P"),
    ]
    got_h = [r['pid'] for r in pcs.still_running(hooks, me=301)]
    cases.append(('a hook fired beside the check, in any adapter\'s form, is '
                  'not listed', not {600, 601} & set(got_h), repr(got_h)))
    cases.append(('...while a real `sleep 600`, and a hook script the session '
                  'ran itself, still are', {200, 602, 603} <= set(got_h),
                  repr(got_h)))
    human = [(1, 0, '1:00', '/sbin/init'), (10, 1, '1:00', 'tmux'),
             (11, 10, '1:00', '-zsh'), (12, 11, '0:01', 'python3 x.py'),
             (13, 10, '1:00', '-zsh')]
    cases.append(("run from a person's own terminal, with no agent above it, "
                  'nothing is listed', pcs.still_running(human, me=12) == [],
                  repr(pcs.still_running(human, me=12))))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the container check lists commands still running '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_archive_check_sees_work_left_in_a_scratch_folder():
    """A file left in a scratch folder makes the container unsafe to lose,
    the same as an uncommitted file in a checkout; a folder holding only a
    page published on purpose does not; and the folder is given up by its
    own name with the existing **Checkout disposition:** line.

    2026-10-11: a session built 189 summaries in its scratch folder, had
    the filing refused, and moved on. The checkout scan could not see them,
    so the archive line would have passed and the work gone with the
    container. Morgan: "EVERYTHING MUST GO INTO A REPO." """
    import json as _json, re as _re, tempfile
    import precedent_container_safe as pcs
    scanner = ROOT / 'tools' / 'precedent_container_safe.py'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        sess = pathlib.Path(td) / 'abcd1234-5678-session' / 'scratchpad'
        sess.mkdir(parents=True)

        def scan():
            return subprocess.run(
                [sys.executable, str(scanner), '--only', str(ROOT),
                 '--scratch', str(sess), '--json', '--no-processes'],
                capture_output=True, text=True)

        def unsafe_names(r):
            try:
                return [e.get('name') for e in
                        _json.loads(r.stdout or '{}').get('unsafe') or []]
            except ValueError:
                return ['unreadable: ' + r.stdout[:200]]

        r = scan()
        cases.append(('an empty scratch folder is safe',
                      'scratch:abcd1234' not in unsafe_names(r), r.stdout[:300]))
        (sess / pcs._BRANCH_PAGE).write_text('<p>published</p>', encoding='utf-8')
        r = scan()
        cases.append(('a folder holding only the branch page, published on '
                      'purpose, is safe',
                      'scratch:abcd1234' not in unsafe_names(r), r.stdout[:300]))
        copy = sess / 'artifact-files' / 'some-artifact-id'
        copy.mkdir(parents=True)
        (copy / 'index.html').write_text('<p>a live page, read</p>', encoding='utf-8')
        r = scan()
        cases.append(("a copy the Artifact tool saved of a published page is "
                      "safe", 'scratch:abcd1234' not in unsafe_names(r),
                      r.stdout[:300]))
        # A commit-message draft, once committed, is not work only here
        # (2026-10-13: msg.txt refused an archive line after its commit
        # had been pushed and merged). The commit carries a line the
        # ci-cadence hook adds; a draft with a line the commit lacks is
        # still unsafe.
        repo = pathlib.Path(td) / 'repo'
        repo.mkdir()
        _g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                       capture_output=True, text=True)
        _g('init', '-q')
        draft = ('Bump the engine to 6023cd4\n\nWhy: the vendored copy was '
                 'behind.\n\nCo-Authored-By: someone <x@example.com>\n')
        (sess / 'msg.txt').write_text(draft, encoding='utf-8')
        landed = draft.replace('\n\nWhy', '\n\n[skip ci] -- working branch '
                               '(github_ci_on_branches)\n\nWhy')
        _g('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit',
           '-q', '--allow-empty', '-m', landed)

        def scan_repo():
            return subprocess.run(
                [sys.executable, str(scanner), '--only', str(repo),
                 '--scratch', str(sess), '--json', '--no-processes'],
                capture_output=True, text=True)

        r = scan_repo()
        cases.append(('a commit-message draft already committed is safe, '
                      'past the line a commit-msg hook added',
                      'scratch:abcd1234' not in unsafe_names(r), r.stdout[:300]))
        (sess / 'msg.txt').write_text(draft + 'A line never committed.\n',
                                      encoding='utf-8')
        r = scan_repo()
        cases.append(('a draft holding a line the commit lacks is unsafe',
                      'scratch:abcd1234' in unsafe_names(r)
                      and 'msg.txt' in r.stdout, r.stdout[:300]))
        (sess / 'msg.txt').unlink()
        # A helper's worktree whose branch is on origin is safe to lose,
        # and said so; one with a commit no remote has is not (2026-10-18:
        # a folder of landed helper worktrees read NOT SAFE every time).
        bare = pathlib.Path(td) / 'origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(bare)],
                       capture_output=True)
        _g('remote', 'add', 'origin', str(bare))
        _g('push', '-q', 'origin', 'HEAD:refs/heads/helper')
        _g('fetch', '-q', 'origin')
        wt = sess / 'helper-wt'
        _g('worktree', 'add', '-q', '--detach', str(wt), 'origin/helper')
        r = scan_repo()
        plain = subprocess.run(
            [sys.executable, str(scanner), '--only', str(repo), '--scratch',
             str(sess), '--no-processes'], capture_output=True, text=True)
        cases.append(('a helper worktree whose HEAD is on origin is safe to '
                      'lose, and the report says so',
                      'scratch:abcd1234' not in unsafe_names(r)
                      and 'safe to lose' in plain.stdout,
                      r.stdout[:300] + plain.stdout[:300]))
        subprocess.run(['git', '-C', str(wt), '-c', 'user.name=t', '-c',
                        'user.email=t@example.com', 'commit', '-q',
                        '--allow-empty', '-m', 'only here'], capture_output=True)
        r = scan_repo()
        cases.append(('...and one holding a commit no remote has is not',
                      'scratch:abcd1234' in unsafe_names(r), r.stdout[:300]))
        _g('worktree', 'remove', '--force', str(wt))
        (sess / 'out').mkdir()
        (sess / 'out' / 'summaries.txt').write_text('189 lines\n', encoding='utf-8')
        r = scan()
        cases.append(('a file left there makes the container unsafe, under the '
                      "folder's own name", r.returncode == 1
                      and 'scratch:abcd1234' in unsafe_names(r), r.stdout[:300]))
        cases.append(('the report lists the file',
                      'out/summaries.txt' in r.stdout, r.stdout[:300]))
        r2 = subprocess.run([sys.executable, str(scanner), '--only', str(ROOT),
                             '--no-processes'], capture_output=True, text=True)
        cases.append(('with --only and no --scratch, no scratch folder is read',
                      'scratch:' not in r2.stdout, r2.stdout[:300]))
    rules = _json.loads((ROOT / 'reply_check.json').read_text(encoding='utf-8'))
    marker = next((x['unless_reply_declares_loss']['marker']
                   for x in (rules if isinstance(rules, list)
                             else rules.get('requirements') or [])
                   if isinstance(x, dict)
                   and (x.get('unless_reply_declares_loss') or {}).get('marker')), None)
    line = ('**Checkout disposition:** scratch:abcd1234 -- discard (a draft '
            'already filed in the repo)')
    cases.append(('the existing disposition line gives a scratch folder up by '
                  'that name', bool(marker) and bool(_re.search(
                      marker.replace('{name}', _re.escape('scratch:abcd1234')),
                      line, _re.I)), str(marker)))
    failed = [c for c in cases if not c[1]]
    return (not failed, f'{len(cases)} stated cases',
            '; '.join(f'{c[0]}: {c[2]}' for c in failed))


def check_a_pushed_branch_in_a_shallow_clone_is_safe():
    """A branch pushed from a shallow, single-branch clone is safe, and both
    checks that ask say so (2026-10-17, the root issues of a session).

    `git clone --depth 1` -- what attaching a repository mid-session runs --
    fetches the default branch only, so `git push -u` of a feature branch
    leaves no refs/remotes/origin/<branch>. precedent_container_safe and
    precedent_session_check both reported the pushed commit as on no
    remote, and the archive line was held over work that was safe. The
    control: a commit that really is unpushed is still reported.
    """
    import shutil, tempfile
    name = 'a branch pushed from a shallow clone is not reported as unpushed'
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_container_safe as pcs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-shallow-push-'))
    cases = []
    try:
        seed, origin, clone = tmp / 'seed', tmp / 'origin.git', tmp / 'clone'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(seed))
        fixture_git(seed, 'config', 'user.email', 'fixture@example.com')
        fixture_git(seed, 'config', 'user.name', 'fixture')
        (seed / 'a.txt').write_text('a\n', encoding='utf-8')
        fixture_git(seed, 'add', '-A')
        fixture_git(seed, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'base')
        fixture_git(tmp, 'clone', '-q', '--bare', str(seed), str(origin))
        fixture_git(tmp, 'clone', '-q', '--depth', '1', f'file://{origin}', str(clone))
        fixture_git(clone, 'config', 'user.email', 'fixture@example.com')
        fixture_git(clone, 'config', 'user.name', 'fixture')
        fixture_git(clone, 'checkout', '-q', '-b', 'feature')
        (clone / 'b.txt').write_text('b\n', encoding='utf-8')
        fixture_git(clone, 'add', '-A')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'work')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'push', '-q', '-u',
                    'origin', 'feature')
        cases.append(('the fixture reproduces it: no tracking ref after the push',
                      fixture_git(clone, 'rev-parse', '--verify', '-q',
                                  'refs/remotes/origin/feature',
                                  allow_failure=True).returncode != 0, ''))
        got = pcs.scan_one(clone)
        cases.append(('the pushed commit is not reported as on no remote',
                      not any('on no remote' in u for u in got['unsafe']),
                      str(got['unsafe'])))
        (clone / 'c.txt').write_text('c\n', encoding='utf-8')
        fixture_git(clone, 'add', '-A')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'more')
        got = pcs.scan_one(clone)
        cases.append(('control: a commit that is really unpushed is reported',
                      any('1 commit(s) on no remote' in u for u in got['unsafe']),
                      str(got['unsafe'])))
    except FixtureSetupError as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_container_check_sees_other_local_branches():
    """Work on a local branch that is not checked out is work only here; a
    branch holding nothing but session start's engine refresh is engine
    output the next refresh writes again (2026-10-17: a set's clone held
    three such branches and the check, reading HEAD alone, saw none).
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_container_safe as pcs
    name = 'the container check sees work on branches that are not checked out'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-other-branches-'))
    cases = []
    try:
        seed, origin, clone = tmp / 'seed', tmp / 'origin.git', tmp / 'clone'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(seed))
        for d in (seed,):
            fixture_git(d, 'config', 'user.email', 'fixture@example.com')
            fixture_git(d, 'config', 'user.name', 'fixture')
        (seed / 'a.txt').write_text('a\n', encoding='utf-8')
        fixture_git(seed, 'add', '-A')
        fixture_git(seed, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'base')
        fixture_git(tmp, 'clone', '-q', '--bare', str(seed), str(origin))
        fixture_git(tmp, 'clone', '-q', str(origin), str(clone))
        fixture_git(clone, 'config', 'user.email', 'fixture@example.com')
        fixture_git(clone, 'config', 'user.name', 'fixture')

        def branch_with(name_, subject):
            fixture_git(clone, 'checkout', '-q', '-b', name_)
            (clone / f'{name_}.txt').write_text('x\n', encoding='utf-8')
            fixture_git(clone, 'add', '-A')
            fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', subject)
            fixture_git(clone, 'checkout', '-q', 'main')
        branch_with('2026-10-17-x-engine-refresh-abcd1234-zz',
                    'Refresh the vendored engine to BestPractice abcd1234ef56')
        got = pcs.scan_one(clone)
        cases.append(('a branch holding only an engine refresh is not work at risk',
                      not any('other local branches' in u for u in got['unsafe']),
                      str(got['unsafe'])))
        # 2026-10-19: a refresh made on top of a local merge of work the
        # remote already has -- the merge itself never pushed -- was called
        # work at risk, "(1)", on every archive check.
        fixture_git(clone, 'checkout', '-q', '-b', 'side')
        (clone / 'side.txt').write_text('s\n', encoding='utf-8')
        fixture_git(clone, 'add', '-A')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'side')
        fixture_git(clone, 'push', '-q', 'origin', 'side')
        fixture_git(clone, 'checkout', '-q', '-b', 'merged', 'main')
        (clone / 'main-only.txt').write_text('m\n', encoding='utf-8')
        fixture_git(clone, 'add', '-A')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'main-only')
        fixture_git(clone, 'push', '-q', 'origin', 'merged')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'merge', '-q',
                    '--no-edit', 'side')
        fixture_git(clone, 'checkout', '-q', '-b',
                    '2026-10-14-x-engine-refresh-0bad1234-mm')
        (clone / 'refresh.txt').write_text('r\n', encoding='utf-8')
        fixture_git(clone, 'add', '-A')
        fixture_git(clone, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm',
                    'Refresh the vendored engine to BestPractice 0bad1234ef56')
        fixture_git(clone, 'checkout', '-q', 'main')
        fixture_git(clone, 'branch', '-q', '-D', 'merged', 'side')
        got = pcs.scan_one(clone)
        cases.append(('a refresh over an unpushed merge of pushed work is not work at risk',
                      not any('other local branches' in u for u in got['unsafe']),
                      str(got['unsafe'])))
        import precedent_refresh_sources as prs
        cases.append(('the refresh tool still keeps that branch: a merge can '
                      'carry a conflict resolution',
                      '2026-10-14-x-engine-refresh-0bad1234-mm'
                      not in prs.refresh_only_branches(clone, 'HEAD'), ''))
        branch_with('half-done', 'real work, never pushed')
        got = pcs.scan_one(clone)
        cases.append(('a branch with real unpushed work is named',
                      any('other local branches no remote has: half-done (1)' in u
                          for u in got['unsafe']), str(got['unsafe'])))
    except FixtureSetupError as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_consumer_bootstrap_clones_declared_sources():
    """templates/bootstrap.sh must clone the shared sets a consumer declares,
    before it checks the loader block against them.

    Until 2026-09-26 it did not: the only session-start step that cloned
    declared sources was precedent-universal-catalogue.sh, which consumers
    decline, so a consumer's declared set was missing from every fresh
    container and its loader block read as drifted (gotchas/, 2026-09-26).
    Asserted with precedent_check's own pattern, so the template and the
    check that fails a repo without the step cannot disagree about what the
    step looks like. The negative control strips the step and must stop
    matching."""
    import precedent_check as pc
    text = (ROOT / 'templates' / 'bootstrap.sh').read_text(encoding='utf-8')
    code = '\n'.join(l for l in text.splitlines()
                     if not l.lstrip().startswith('#'))
    m = pc._SOURCE_CLONE_RE.search(code)
    sync = code.find('precedent_sync_views.py --repo . --check')
    stripped = '\n'.join(l for l in code.splitlines()
                         if 'precedent_source_bootstrap.py' not in l)
    cases = [
        ('the template runs precedent_source_bootstrap.py --sources-from', bool(m)),
        ('and runs it before the loader-block check',
         bool(m) and sync != -1 and m.start() < sync),
        ('negative control: without that line the pattern finds nothing',
         not pc._SOURCE_CLONE_RE.search(stripped)),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'the consumer bootstrap template clones declared shared sets '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_verify_reports_a_source_wired_for_fewer_moments():
    """verify() asked whether a hook RUNS and never at which moments, so a
    source wired for fewer moments than the adapter wires it for audited
    perfectly clean. That is structurally why the five downstream sets sat
    mis-wired for days: the check that should have caught it could not.

    The three cases below are the ones that decide whether the fix is right
    rather than merely present -- a wiring check is easy to write in a way
    that is correct on the standard layout and wrong everywhere else."""
    import tempfile
    import precedent_bootstrap_source as pbs

    def _wiring_findings(root, cmds):
        (root / '.claude').mkdir(parents=True, exist_ok=True)
        (root / '.claude' / 'settings.json').write_text(json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [
                {'type': 'command', 'command': c} for c in cmds]}]}}),
            encoding='utf-8')
        return [m for m in pbs.verify('team', root) if 'NOT WIRED' in m]

    D = '$CLAUDE_PROJECT_DIR'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 1. PATH INDEPENDENCE. The individual set wires its guard from a
        # tracked bootstrap/ directory rather than .claude/hooks/, on purpose
        # -- one copy, nothing to drift from it -- and its own practice
        # documents that layout. A check that reads the directory instead of
        # the declared command calls that set broken, which would make the
        # check wrong rather than the set.
        a = tmp / 'bootstrap-layout'
        found = _wiring_findings(a, [
            f'{D}/bootstrap/freshness-guard.sh {m} main'
            for m in sorted(pbs._template_guard_modes())])
        cases.append((f'a source wiring every mode from bootstrap/ rather '
                      f'than .claude/hooks/ is clean (got {found})', not found))

        # 2. THE NEGATIVE CASE. One mode removed, and the finding has to name
        # that mode -- not merely be non-empty.
        b = tmp / 'missing-user-prompt'
        found = _wiring_findings(b, [
            f'{D}/.claude/hooks/freshness-guard.sh session-start main',
            f'{D}/.claude/hooks/freshness-guard.sh pre-write main'])
        cases.append((f'a source missing one mode is reported, naming that '
                      f'mode (got {found})',
                      len(found) == 1 and 'user-prompt' in found[0]
                      and 'NOT WIRED' in found[0]))

        # 3. DIRECTION. want - have, never the reverse: a source wiring more
        # than the adapter is doing something deliberate, not something broken.
        c = tmp / 'wires-extra'
        found = _wiring_findings(c, [
            f'{D}/.claude/hooks/freshness-guard.sh {m} main'
            for m in sorted(pbs._template_guard_modes()) + ['some-future-mode']])
        cases.append((f'a source wiring MORE modes than the adapter is not '
                      f'flagged (got {found})', not found))

    failed = [n for n, ok in cases if not ok]
    check(f'verify() reports a source wired for fewer moments than the '
          f'adapter ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_session_start_says_did_not_load_only_after_cloning():
    """Session start opened with "BEFORE ANY OTHER WORK: these practice
    sources did not load" on a fresh container (2026-10-19) for two sets
    that loaded seconds later, and named one of them twice. Two causes:
    BestPractice's own .claude/hooks/session-start.sh wrote the practices
    file, and that notice, before the step that clones the shared sets
    (tools/bootstrap.sh, which says it keeps the same order, had them the
    right way round); and precedent_hooks.unloaded_sources listed a set
    once per folder that declares it. Both fail on the old code."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_hooks as ph
        import precedent_resolve as pr
    finally:
        sys.path.pop(0)
    cases = []
    for rel in ('.claude/hooks/session-start.sh', 'tools/bootstrap.sh'):
        text = (ROOT / rel).read_text(encoding='utf-8')
        clone = text.find('precedent_source_bootstrap.py --teams-from')
        render = text.find('python3 tools/precedent_session_practices.py')
        cases.append((f'{rel} clones the sources before it says which loaded',
                      0 <= clone < render, f'clone at {clone}, render at {render}'))
    saved = (pr.declared_source_paths, ph._attach_hints)
    try:
        pr.declared_source_paths = lambda root: [
            ('/nowhere/a/precedent-shared-x', 'shared', 'precedent-shared-x', ''),
            ('/nowhere/b/precedent-shared-x', 'shared', 'precedent-shared-x', '')]
        ph._attach_hints = lambda root: {'precedent-shared-x': 'acct/precedent-shared-x'}
        rows = ph.unloaded_sources(ROOT)
    finally:
        pr.declared_source_paths, ph._attach_hints = saved
    cases.append(('a set two folders declare is named once',
                  rows == [('precedent-shared-x', 'acct/precedent-shared-x')], str(rows)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_freshness_guard_checks_attached_repositories():
    """PRECEDENT_FRESHNESS_ALSO, carried up from a downstream set 2026-09-11.

    A hook fires for the project dir and nothing else, so a repository the
    session merely has ATTACHED -- `add_repo`, a SessionStart clone, the
    sibling clone a shared practice source resolves to -- runs none of its own
    freshness checking however correctly its guard is installed (AGENTS.md's
    gotchas carry the general form of this). An environment variable is the
    one thing that follows a session into every repository it touches, which
    is the same reasoning that put PRECEDENT_COMMIT_* at the top of the
    identity chain.

    THE CONTROL IS THE POINT. Case 2 runs the identical stale attached repo
    with the variable unset and requires it to pass in silence -- otherwise
    case 1 proves only that something exited 2, not that the also-list is
    what found it, and the check would keep passing if the mechanism were
    deleted tomorrow. Case 3 holds the other edge: an entry naming a path
    that is not there is a config typo, not a stale checkout, and blocking on
    it would wedge every session over a mistyped value and teach people to
    unset the variable. Each case asserts the guard's own words rather than
    an exit status (practice: control-asserts-which-failure) -- exit 2 is
    also what the stale-base case returns, and exit 0 is what a spent
    sentinel returns.

    Both copies are run, this repo's own and the one an adopter instantiates,
    for the reason parallel-artifact-ledger names."""
    import tempfile

    # The installed stub and the template stub, each running tools/'s script.
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    missing = [str(g.relative_to(ROOT)) for g in guards if not g.exists()]
    if missing:
        not_applicable('the freshness guard checks attached repositories',
                       f'not in this tree: {missing}')
        return

    env0 = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    env0.pop('PRECEDENT_FRESHNESS_ALSO', None)

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env0,
                              capture_output=True, text=True)

    cases = []
    for guard in guards:
        tag = guard.relative_to(ROOT).as_posix()
        with tempfile.TemporaryDirectory() as td:
            w = pathlib.Path(td)
            # The guard's once-per-session sentinel lives in TMPDIR keyed by
            # session id. The ids below are fixed strings, so without a
            # fixture-owned TMPDIR the SECOND run in a container finds every
            # sentinel already there and every case exits 0 in silence --
            # which would read as a pass if these asserted exit codes alone
            # (practice: fixture-owns-its-state).
            sentinels = w / 'sentinels'
            sentinels.mkdir()

            def run(project, session, also=None, home=None):
                env = dict(env0, TMPDIR=str(sentinels),
                           CLAUDE_PROJECT_DIR=str(project))
                if home is not None:
                    env['HOME'] = str(home)
                if also is None:
                    env.pop('PRECEDENT_FRESHNESS_ALSO', None)
                else:
                    env['PRECEDENT_FRESHNESS_ALSO'] = also
                r = subprocess.run(
                    ['bash', str(guard), 'pre-write', 'main'],
                    input=json.dumps({'session_id': session,
                                      'tool_name': 'Write',
                                      'tool_input': {'command': ''}}),
                    env=env, capture_output=True, text=True, cwd=str(project))
                return r.returncode, r.stderr

            def make(name):
                """A real origin, not a URL: the guard fetches and compares,
                so there has to be something on the other end."""
                bare, seed, clone = (w / f'{name}.git', w / f'{name}-seed',
                                     w / name)
                subprocess.run(['git', 'init', '-q', '--bare', str(bare)],
                               env=env0)
                subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)],
                               env=env0)
                git(seed, 'remote', 'add', 'origin', str(bare))
                (seed / 'f').write_text('a\n')
                git(seed, 'add', 'f'); git(seed, 'commit', '-qm', 'a')
                git(seed, 'push', '-q', 'origin', 'main')
                subprocess.run(['git', 'clone', '-q', '-b', 'main', str(bare),
                                str(clone)], env=env0, capture_output=True)
                return seed, clone

            _, proj = make('proj')
            other_seed, other = make('other')

            # The attached repo falls one commit behind its own origin, clean
            # tree. The project dir stays perfectly current throughout, so
            # anything found here was found through the also-list.
            (other_seed / 'f').write_text('a\nb\n')
            git(other_seed, 'commit', '-qam', 'b')
            git(other_seed, 'push', '-q', 'origin', 'main')
            git(other, 'fetch', '-q', 'origin', 'main')
            behind = git(other, 'rev-list', '--count',
                         'HEAD..origin/main').stdout.strip()
            cases.append((f'{tag}: the fixture attached repo really is behind '
                          f'its origin (got {behind!r})', behind == '1'))

            rc, err = run(proj, 'also-stale', also=f'{other}=main')
            cases.append((f'{tag}: a stale ATTACHED repo is acted on through '
                          f'PRECEDENT_FRESHNESS_ALSO (rc={rc})',
                          rc == 2 and 'fast-forwarded' in err))
            # THE BLOCK NAMES THE CHECKOUT (2026-10-02). Every message speaks
            # of '$branch' and origin/$base alone, so a block on an attached
            # clone read as being about the project's own branch and cost a
            # consumer session a diagnosis round.
            cases.append((f'{tag}: ...and the block names that attached '
                          f'checkout, not the project, and says to run git '
                          f'there (stderr={err.strip()[-160:]!r})',
                          f'in {other} --' in err and 'NOT this project' in err
                          and f'git -C {other}' in err))

            # THE CONTROL. Same stale repo, variable unset: the gap the
            # mechanism closes has to be demonstrably open without it.
            git(other, 'reset', '-q', '--hard', 'HEAD~1')
            rc, err = run(proj, 'also-unset')
            cases.append((f'{tag}: with the variable unset that same stale '
                          f'attached repo goes unnoticed -- the gap being '
                          f'closed (rc={rc}, stderr={err.strip()[:60]!r})',
                          rc == 0 and not err.strip()))

            rc, err = run(proj, 'also-bad',
                          also=f'{w / "ghost"}=main;no-equals-sign')
            cases.append((f'{tag}: an unresolvable also-list entry is NOTEd '
                          f'and skipped, never blocked on (rc={rc})',
                          rc == 0 and 'is not a git repository' in err
                          and "no \'=<base branch>\'" in err))

            # $HOME EXPANSION. An individual practice source lives at
            # $HOME/precedent-individual and $HOME differs between
            # containers, so an absolute path written on one names nothing on
            # the next -- which is what this project's own environment had
            # been doing, unnoticed, for the whole life of the variable.
            # Nothing expands a value read back out of a variable, so the
            # guard has to do it. HOME is set to the fixture, never inherited
            # (practice: fixture-owns-its-state).
            for form in ('~/other=main', '$HOME/other=main',
                         '${HOME}/other=main'):
                git(other, 'reset', '-q', '--hard', 'HEAD~1')
                rc, err = run(proj, f'also-home-{form[:3]}', also=form,
                              home=w)
                cases.append((f'{tag}: {form!r} resolves against HOME rather '
                              f'than being taken literally (rc={rc})',
                              rc == 2 and 'fast-forwarded' in err))
                git(other, 'merge', '-q', '--ff-only', 'origin/main')

            # The control: expansion must not turn an absent path into a
            # pass. It still skips, and the note names BOTH forms, because
            # the two differing is the whole diagnosis.
            rc, err = run(proj, 'also-home-ghost', also='~/ghost=main',
                          home=w)
            cases.append((f'{tag}: an expanded path that is still not there '
                          f'skips, naming the entry as written (rc={rc})',
                          rc == 0 and "(from '~/ghost')" in err))

            # THE DECLARED BASE WINS FOR AN ATTACHED REPO (2026-09-26). A
            # practice source is read from main, and its own staging is
            # ahead of main by design until a Promote. The guard used to let
            # the person's landing branch (staging) replace the entry's
            # declared "=main", so a source sitting correctly on main was
            # "missing N commits from origin/staging" and every tool call
            # of the session was refused. A stub precedent_branches.py makes
            # --landing answer staging, the way a real source's does.
            def tiered(repo_seed, repo):
                tools = repo_seed / 'tools'
                tools.mkdir(exist_ok=True)
                (tools / 'precedent_branches.py').write_text(
                    'import sys\n'
                    'if "--landing" in sys.argv: print("staging")\n')
                git(repo_seed, 'add', 'tools')
                git(repo_seed, 'commit', '-qm', 'landing stub')
                git(repo_seed, 'push', '-q', 'origin', 'main')
                git(repo_seed, 'checkout', '-qb', 'staging')
                (repo_seed / 'g').write_text('unpromoted\n')
                git(repo_seed, 'add', 'g')
                git(repo_seed, 'commit', '-qm', 'unpromoted')
                git(repo_seed, 'push', '-q', 'origin', 'staging')
                git(repo_seed, 'checkout', '-q', 'main')
                git(repo, 'fetch', '-q', 'origin')
                git(repo, 'merge', '-q', '--ff-only', 'origin/main')

            tiered(other_seed, other)
            rc, err = run(proj, 'also-declared-main', also=f'{other}=main')
            cases.append((f'{tag}: an attached source on main is checked '
                          f'against its DECLARED base, not the landing '
                          f'branch staging (rc={rc}, '
                          f'stderr={err.strip()[:90]!r})',
                          rc == 0 and 'staging' not in err))

            # THE CONTROL: the project dir, with no declared base, still
            # takes the landing override -- work written there lands on
            # staging, so a main checkout behind it is still refused.
            # Without this the case above would pass if the landing override
            # were deleted outright.
            proj2_seed, proj2 = make('proj2')
            tiered(proj2_seed, proj2)
            rc, err = run(proj2, 'project-landing')
            cases.append((f'{tag}: the project dir itself is still held to '
                          f'the landing branch (rc={rc})',
                          rc == 2 and 'origin/staging' in err))
            cases.append((f'{tag}: ...and a block on the project itself reads '
                          f'as before, naming no other checkout',
                          'NOT this project' not in err))

    failed = [n for n, ok in cases if not ok]
    check(f'the freshness guard checks attached repositories '
          f'({len(cases)} stated cases, both copies)',
          not failed, '; '.join(failed))


def check_session_deepen_stays_narrow():
    """THE SESSION-START DEEPEN IS A STRETCH, AND NOTHING WIDENS OR SHORTENS
    IT BY ACCIDENT (2026-10-31, todo/todo-2026-09-14-session-start-deepen-is-tentative.md).
    Session start used to `git fetch --unshallow`, 23 seconds and 33 MB on
    this repository by then; it now deepens the branch checked out and the
    landing branch by 100 generations, and freshness-guard.sh used to undo
    that at its first check by deepening every shallow clone by 500. Planted
    on a 300-commit origin, each case stating its control:

    1. session start's block deepens a depth-1 clone to about 100 commits,
       not the whole 300, and leaves it shallow;
    2. the guard leaves such a clone alone when its counts are provable --
       one tip contains the other -- and still fast-forwards a merely-behind
       one (g37's case, answered by the plain fetch, not a deepen);
    3. the guard still deepens a pair that LOOKS diverged (the control that
       the g37 repair is not gone);
    4. the guard's base fetch never shortens a clone that holds more than
       100 generations (it used `--depth=200`, which cuts a deeper clone);
    5. with session start's failure marker present, the guard retries the
       deepen and removes the marker."""
    import tempfile
    guard = ROOT / 'tools' / 'freshness-guard.sh'
    hook = ROOT / '.claude' / 'hooks' / 'session-start.sh'
    first, last = ('# Give this checkout a working stretch of HISTORY',
                   '# FRESHNESS LIVES IN')
    if not guard.exists() or not hook.exists() \
            or first not in hook.read_text() or last not in hook.read_text():
        not_applicable('session-start deepen stays narrow',
                       'no freshness-guard.sh, or no session-start deepen '
                       'block, in this tree')
        return
    env0 = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com',
                GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    env0.pop('PRECEDENT_FRESHNESS_ALSO', None)

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env0,
                              capture_output=True, text=True)

    def count(cwd, ref='--all'):
        out = git(cwd, 'rev-list', '--count', ref).stdout.strip()
        return int(out or 0)

    def shallow(cwd):
        return git(cwd, 'rev-parse', '--is-shallow-repository').stdout.strip() == 'true'

    def run_guard(cwd, mode='session-start', base='main'):
        return subprocess.run(['bash', str(guard), mode, base], cwd=str(cwd),
                              env=dict(env0, CLAUDE_PROJECT_DIR=str(cwd)),
                              capture_output=True, text=True)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)
        bare, seed = w / 'o.git', w / 'seed'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)],
                       env=env0, capture_output=True)
        # 300 linear commits in one fast-import, then a `work` branch two
        # commits further on, so a base and a branch differ.
        stream = []
        for i in range(1, 301):
            msg, body = f'c{i}', f'{i}\n'
            stream += [f'commit refs/heads/main', f'mark :{i}',
                       f'committer t <t@example.com> {1700000000 + i} +0000',
                       f'data {len(msg)}', msg]
            if i > 1:
                stream.append(f'from :{i - 1}')
            stream += ['M 644 inline f.txt', f'data {len(body)}', body]
        subprocess.run(['git', f'--git-dir={bare}', 'fast-import', '--quiet'],
                       input='\n'.join(stream) + '\n', text=True, env=env0,
                       capture_output=True)
        subprocess.run(['git', 'clone', '-q', str(bare), str(seed)], env=env0,
                       capture_output=True)
        git(seed, 'checkout', '-q', '-b', 'work')
        for n in ('w1', 'w2'):
            (seed / f'{n}.txt').write_text(n + '\n')
            git(seed, 'add', '-A'); git(seed, 'commit', '-qm', n)
        git(seed, 'push', '-q', 'origin', 'work')
        url = f'file://{bare}'

        def clone(name, branch='main'):
            d = w / name
            subprocess.run(['git', 'clone', '-q', '--depth', '1', '-b', branch,
                            url, str(d)], env=env0, capture_output=True)
            git(d, 'config', 'precedent.freshness.intervalSeconds', '0')
            return d

        # 1. Session start's own block, lifted from the hook as it ships.
        d = clone('start')
        text = hook.read_text()
        block = text[text.index("# Repair a single-branch clone's refspec"):
                     text.index(last)]
        r = subprocess.run(['bash', '-c', 'set -euo pipefail\n' + block],
                           cwd=str(d), env=env0, capture_output=True, text=True)
        n = count(d, 'HEAD')
        cases.append((f'1: session start deepens a depth-1 clone by a '
                      f'stretch, not the whole history ({n} of 300 commits, '
                      f'rc={r.returncode})',
                      r.returncode == 0 and 90 <= n <= 110 and shallow(d)))

        # 2. A narrow clone whose counts are provable is left narrow, and a
        # merely-behind one is still fast-forwarded.
        before = count(d)
        g = run_guard(d)
        cases.append((f'2a: the guard leaves a narrow clone narrow when its '
                      f'counts are provable ({before} -> {count(d)} commits)',
                      count(d) == before and shallow(d)))
        git(seed, 'checkout', '-q', 'main')
        for n in ('m1', 'm2', 'm3'):
            (seed / f'{n}.txt').write_text(n + '\n')
            git(seed, 'add', '-A'); git(seed, 'commit', '-qm', n)
        git(seed, 'push', '-q', 'origin', 'main')
        tip = git(seed, 'rev-parse', 'HEAD').stdout.strip()
        before = count(d)
        g = run_guard(d)
        cases.append((f'2b: a merely-behind narrow clone is fast-forwarded, '
                      f'not deepened ({before} -> {count(d)} commits)',
                      git(d, 'rev-parse', 'HEAD').stdout.strip() == tip
                      and count(d) == before + 3 and shallow(d)))

        # 3. Control: a pair that looks diverged is still deepened.
        d3 = clone('diverged')
        git(d3, 'fetch', '-q', '--deepen=5', 'origin', 'main')
        git(d3, 'reset', '-q', '--hard', 'HEAD~4')
        (d3 / 'local.txt').write_text('local\n')
        git(d3, 'add', '-A'); git(d3, 'commit', '-qm', 'local')
        git(d3, 'fetch', '-q', '--depth=1', 'origin', 'main')
        before = count(d3)
        g = run_guard(d3)
        cases.append((f'3: control -- a pair that looks diverged is still '
                      f'deepened ({before} -> {count(d3)} commits)',
                      count(d3) > before + 50))

        # 4. The base fetch never shortens a deeper clone.
        d4 = clone('deep', 'work')
        git(d4, 'config', '--add', 'remote.origin.fetch',
            '+refs/heads/*:refs/remotes/origin/*')
        git(d4, 'fetch', '-q', '--deepen=250', 'origin', 'work', 'main')
        before = count(d4, 'origin/main')
        g = run_guard(d4, base='main')
        cases.append((f'4: the base fetch never shortens a clone holding more '
                      f'than its bound (origin/main {before} -> '
                      f'{count(d4, "origin/main")} commits)',
                      before > 200 and count(d4, 'origin/main') >= before))

        # 5. Session start's failure marker makes the guard retry its deepen.
        d5 = clone('marker')
        gd = pathlib.Path(git(d5, 'rev-parse', '--absolute-git-dir').stdout.strip())
        (gd / 'PRECEDENT_SHALLOW_UNRESOLVED').write_text('')
        before = count(d5, 'HEAD')
        g = run_guard(d5)
        cases.append((f'5: with the failure marker, the guard retries the '
                      f'deepen and clears the marker ({before} -> '
                      f'{count(d5, "HEAD")} commits)',
                      count(d5, 'HEAD') > 50
                      and not (gd / 'PRECEDENT_SHALLOW_UNRESOLVED').exists()))

    failed = [n for n, ok in cases if not ok]
    check(f'session-start deepen stays narrow ({len(cases)} stated cases: '
          f'a stretch at start, left narrow when provable, still deepened '
          f'when diverged, never shortened, retried on the marker)',
          not failed, '; '.join(failed))


def check_freshness_guard_user_prompt_never_resets_mid_session():
    """`mode_user_prompt` delegates to `mode_session_start` (see the file's
    own comment on that delegation), which carries a diverged-but-clean
    auto-reconcile (rescue-ref then `git reset --hard origin/<branch>`)
    whose safety argument is specific to the real SessionStart call: nothing
    reachable from local HEAD can be this session's own work yet, because
    the session has not taken a turn. That premise is false by the time a
    later `UserPromptSubmit` fires the same delegation, and until fixed
    2026-09-20 the code did not distinguish the two callers, so a real local
    commit was discarded mid-session (recovered only because the rescue ref
    and the reflog both happened to survive) --
    gotchas/gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess.md.

    THE CONTROL IS THE POINT, same shape as the other freshness-guard
    checks: the identical diverged-and-clean fixture run through
    `session-start` still auto-reconciles (rescue ref, HEAD moves to
    origin) -- proving the assertion below is about the CALLER, not about
    the reconcile behavior having been deleted outright."""
    import tempfile

    # The installed stub and the template stub, each running tools/'s script.
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    missing = [str(g.relative_to(ROOT)) for g in guards if not g.exists()]
    if missing:
        not_applicable('freshness guard user-prompt never resets mid-session',
                       f'not in this tree: {missing}')
        return

    env0 = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    env0.pop('PRECEDENT_FRESHNESS_ALSO', None)

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env0,
                              capture_output=True, text=True)

    cases = []
    for guard in guards:
        tag = guard.relative_to(ROOT).as_posix()
        # A guard with no diverged-branch repair at all (it just warns) has
        # nothing here to regress -- checked rather than assumed, so a silent
        # skip never reads as a pass. Keyed on the MERGE since 2026-09-23,
        # when the reset was removed from every mode: keying on the reset
        # would have skipped every case below the day it went.
        has_reconcile = 'merge --no-edit "origin/$branch"' in guard.read_text()
        if not has_reconcile:
            cases.append((f'{tag}: has no auto-reconcile to guard against '
                          f'(checked, not assumed -- nothing to fix here)',
                          True))
            continue

        with tempfile.TemporaryDirectory() as td:
            w = pathlib.Path(td)

            def make_diverged(name):
                """A clean clone one commit ahead of a LOCAL commit and one
                commit behind origin -- the exact shape the bug fires on.
                Each caller gets its own paths: two independent fixtures are
                built in the same temp dir (one per mode under test), and
                reusing 'seed'/'clone' across them silently re-initialized
                the first one instead of building a second."""
                bare, seed, clone = w / f'{name}-o.git', w / f'{name}-seed', w / f'{name}-clone'
                subprocess.run(['git', 'init', '-q', '--bare', str(bare)], env=env0)
                subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)], env=env0)
                git(seed, 'remote', 'add', 'origin', str(bare))
                (seed / 'f').write_text('a\n')
                git(seed, 'add', 'f'); git(seed, 'commit', '-qm', 'a')
                git(seed, 'push', '-q', 'origin', 'main')
                subprocess.run(['git', 'clone', '-q', '-b', 'main', str(bare), str(clone)],
                               env=env0, capture_output=True)
                (seed / 'f').write_text('a\nb\n')
                git(seed, 'commit', '-qam', 'b')
                git(seed, 'push', '-q', 'origin', 'main')
                (clone / 'g').write_text('local\n')
                git(clone, 'add', 'g'); git(clone, 'commit', '-qm', 'local work')
                git(clone, 'config', 'precedent.freshness.intervalSeconds', '0')
                return clone

            def run(project, mode):
                env = dict(env0, CLAUDE_PROJECT_DIR=str(project))
                r = subprocess.run(['bash', str(guard), mode, 'main'],
                                   env=env, capture_output=True, text=True,
                                   cwd=str(project))
                return r.returncode, r.stderr

            clone = make_diverged('up')
            local_sha = git(clone, 'rev-parse', 'HEAD').stdout.strip()
            origin_sha = git(clone, 'rev-parse', 'origin/main').stdout.strip()

            rc, err = run(clone, 'user-prompt')
            after = git(clone, 'rev-parse', 'HEAD').stdout.strip()

            def reachable(cwd, sha):
                return git(cwd, 'merge-base', '--is-ancestor', sha,
                           'HEAD').returncode == 0

            # WHAT THIS TEST ASSERTS CHANGED ON 2026-09-22, AND WHY IT IS NOW
            # STRICTER RATHER THAN LOOSER. It used to require HEAD to be
            # exactly where it was, as a proxy for the property the
            # 2026-09-20 incident actually cost: a local commit was
            # DISCARDED. Reporting-and-doing-nothing satisfies that proxy --
            # and so does every other way of leaving the drift in place, which
            # is what shipped, and what had the person reconciling by hand two
            # days later. A merge fails the proxy while satisfying the
            # property completely: both parents stay on the branch, so the
            # local commit is still reachable afterwards. So the proxy is
            # replaced by the property itself, plus the two things the proxy
            # never checked at all -- that the drift is genuinely repaired,
            # and that a merge which CANNOT complete leaves the checkout
            # untouched rather than half-applied.
            cases.append((f'{tag}: user-prompt repairs a diverged clean '
                          f'branch instead of leaving it drifted (rc={rc})',
                          rc == 0 and 'MERGED origin/' in err
                          and 'never reset away' in err))
            cases.append((f'{tag}: user-prompt KEEPS the local commit the '
                          f'2026-09-20 bug discarded -- still reachable from '
                          f'HEAD, never reset away',
                          reachable(clone, local_sha)))
            cases.append((f'{tag}: user-prompt never resets -- HEAD is not '
                          f'origin\'s tip with the local work dropped',
                          after != origin_sha))
            cases.append((f'{tag}: user-prompt actually brings origin in, so '
                          f'the drift is gone rather than re-reported next '
                          f'prompt',
                          reachable(clone, origin_sha)))
            rescue_up = git(clone, 'for-each-ref',
                            f'refs/freshness-guard/pre-merge/main-{local_sha[:12]}').stdout.strip()
            cases.append((f'{tag}: user-prompt rescues the pre-merge tip to '
                          f'its own ref as well',
                          local_sha[:12] in rescue_up))

            # THE CONFLICT CONTROL. A merge that cannot complete must leave
            # nothing half-applied: the next tool call in that session would
            # otherwise meet a conflicted index it never asked for.
            conflict = make_diverged('cf')
            (conflict / 'f').write_text('a\nCONFLICTING\n')
            git(conflict, 'commit', '-qam', 'conflicting local edit')
            before_cf = git(conflict, 'rev-parse', 'HEAD').stdout.strip()
            rc3, err3 = run(conflict, 'user-prompt')
            after_cf = git(conflict, 'rev-parse', 'HEAD').stdout.strip()
            unmerged = git(conflict, 'diff', '--name-only',
                           '--diff-filter=U').stdout.strip()
            cases.append((f'{tag}: a CONFLICTING mid-session merge is aborted '
                          f'and reported, leaving HEAD where it was (rc={rc3})',
                          rc3 == 0 and after_cf == before_cf
                          and 'CONFLICTS' in err3 and not unmerged))

            # SESSION-START, 2026-09-23: the identical fixture is merged there
            # too, never reset. It used to `reset --hard` to origin here --
            # the verb the fresh-before-write practice rules out by name --
            # so this asserts the property that practice protects: the local
            # commit is still on the branch afterwards, and origin is in.
            clone2 = make_diverged('ss')
            local_sha2 = git(clone2, 'rev-parse', 'HEAD').stdout.strip()
            # NOT read yet: the clone's own refs/remotes/origin/main is
            # whatever it was at clone time until something fetches, so the
            # commit just pushed to the bare repo above is invisible here
            # until the guard's own fetch (inside `run`) catches it up.
            rc2, err2 = run(clone2, 'session-start')
            origin_sha2 = git(clone2, 'rev-parse', 'origin/main').stdout.strip()
            cases.append((f'{tag}: session-start merges a diverged clean '
                          f'branch rather than resetting it (rc={rc2})',
                          rc2 == 0 and 'MERGED origin/' in err2
                          and 'reconciled it to origin' not in err2))
            cases.append((f'{tag}: session-start KEEPS the local commit on '
                          f'the branch and brings origin in',
                          reachable(clone2, local_sha2)
                          and reachable(clone2, origin_sha2)))
            no_reset = git(clone2, 'for-each-ref',
                           'refs/freshness-guard/pre-reset/').stdout.strip()
            cases.append((f'{tag}: session-start leaves no pre-reset ref, '
                          f'because nothing was reset',
                          not no_reset))

    failed = [n for n, ok in cases if not ok]
    check(f'freshness guard: a diverged clean branch is merged in every '
          f'mode and never reset -- no local work discarded '
          f'({len(cases)} stated cases, both copies)',
          not failed, '; '.join(failed))


def check_freshness_guard_waves_through_a_branch_origin_never_saw():
    """The guard's two fetch failures are not the same failure.

    `git fetch origin <branch>` exits non-zero both when origin is
    unreachable and when origin simply has no such ref, and `pre-write`
    treated them identically: it exited 2, which refused the first write of
    every newly created branch. A branch with no remote counterpart has
    nothing to be behind, so there is no staleness there to refuse. The cost
    was not the refusal but the remedy -- the block's own message names
    `git fetch origin <branch>`, which cannot succeed against a ref that does
    not exist, so the only way forward a session finds is
    `git config precedent.freshness.override true`, which switches the guard
    off for that checkout permanently, including the stale-base check that
    catches the real incident. `session-start` had the same bug in its milder
    form: a WARN saying freshness was NOT verified, on every new branch.

    BOTH DIRECTIONS ARE ASSERTED, not only the one being fixed. A guard
    relaxed until it stops complaining is not a guard, so the unreachable
    origin must still block -- and per control-asserts-which-failure, the
    block is asserted by the message it prints, never by the exit code alone:
    exit 2 is also what the stale-base case returns, one case over.

    The third case is the one that makes the fix safe rather than merely
    quiet: a branch absent from origin AND built on a stale base must STILL
    be refused. Waving the missing counterpart through has to leave the
    base-branch check running, since that is the check the whole guard exists
    for.

    Both copies are run -- the one this repo uses on itself and the one an
    adopter instantiates -- because a fix that reaches only one of them is
    the drift parallel-artifact-ledger names."""
    import tempfile

    # The installed stub and the template stub, each running tools/'s script.
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    missing = [str(g.relative_to(ROOT)) for g in guards if not g.exists()]
    if missing:
        not_applicable('freshness-guard waves through a branch origin has '
                       'never seen', f'not in this tree: {missing}')
        return

    # env is built inside the `with` below and closed over here, so every
    # setup command runs under the SAME environment the guard does. Without
    # it these ran on the container's own git identity, and the fixture's
    # premise ("every ambient input that can change the result is set here")
    # was true of the guard's environment and false of its own: on a machine
    # with a global identity the setup commits succeeded and the check
    # passed, on CI -- which has none -- `git commit` died with "Author
    # identity unknown", origin/main never advanced, and case 4's stale base
    # never existed. The guard then correctly exited 0 and was reported as
    # the failure (practice: fixture-owns-its-state).
    #
    # The exit code is checked for the same reason it is checked everywhere
    # else in this tree: a setup step that fails silently produces a fixture
    # measuring nothing while looking like it measured something.
    env = {}

    def _git(d, *a, allow_failure=False):
        r = subprocess.run(['git', '-C', str(d), *a],
                           capture_output=True, text=True, env=env or None)
        if not allow_failure and r.returncode != 0:
            raise RuntimeError(
                'freshness-guard fixture setup failed: git %s (exit %d): %s'
                % (' '.join(a), r.returncode, (r.stderr or r.stdout).strip()))
        return r

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # fixture-owns-its-state: every ambient input that can change the
        # result is set here. TMPDIR carries the guard's per-session
        # sentinel, so a stale one from the real session would make
        # pre-write exit 0 without running a single check -- which is a
        # green result meaning nothing at all. GIT_CONFIG_GLOBAL empties the
        # container's global identity AND its core.hooksPath backstop, which
        # would otherwise refuse these fixture commits.
        env.clear()
        env.update(os.environ)
        env.pop('CLAUDE_PROJECT_DIR', None)
        env['TMPDIR'] = str(tmp / 'sentinels')
        (tmp / 'sentinels').mkdir()
        env['PRECEDENT_ALLOW_ANY_AUTHOR'] = '1'
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = 'Harness'
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = \
            'harness@example.com'

        def _run(guard, cwd, mode, session):
            payload = json.dumps({'session_id': session,
                                  'tool_name': 'Write',
                                  'tool_input': {'file_path': 'x'}})
            return subprocess.run(['bash', str(guard), mode, 'main'],
                                  cwd=str(cwd), input=payload,
                                  capture_output=True, text=True, env=env)

        origin = tmp / 'origin'
        subprocess.run(['git', 'init', '-q', '--bare', str(origin)],
                       capture_output=True, text=True, env=env, check=True)
        seed = tmp / 'seed'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)],
                       capture_output=True, text=True, env=env, check=True)
        (seed / 'f.txt').write_text('one\n', encoding='utf-8')
        _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'one')
        _git(seed, 'remote', 'add', 'origin', str(origin))
        _git(seed, 'push', '-q', 'origin', 'main')
        # A bare repo's HEAD defaults to refs/heads/master, so without this
        # every clone below lands on an unborn HEAD and the base check has
        # no commits to read -- a fixture that measures nothing while
        # looking like it measured something.
        _git(origin, 'symbolic-ref', 'HEAD', 'refs/heads/main')

        def _clone(name, branch):
            d = tmp / name
            subprocess.run(['git', 'clone', '-q', str(origin), str(d)],
                           capture_output=True, text=True, env=env, check=True)
            _git(d, 'checkout', '-q', '-b', branch)
            return d

        for guard in guards:
            tag = ('installed' if guard.parent.parent.parent == ROOT
                   else 'template')

            # 1. The branch origin has never seen: not blocked.
            d = _clone(f'absent-{tag}', 'brand-new-branch')
            r = _run(guard, d, 'pre-write', f'absent-{tag}')
            cases.append((f'{tag}: pre-write does not block a branch absent '
                          f'from origin (exit {r.returncode})',
                          r.returncode == 0))

            # 2. session-start says so instead of warning it could not check.
            r = _run(guard, d, 'session-start', f'absent-ss-{tag}')
            cases.append((f'{tag}: session-start reports the absent branch '
                          f'rather than an unverified fetch',
                          r.returncode == 0
                          and 'does not exist on origin yet' in r.stderr
                          and 'could not fetch' not in r.stderr))

            # 3. THE OTHER DIRECTION. An unreachable origin still blocks, and
            # the block is identified by its message: exit 2 alone would
            # also match case 4.
            d = _clone(f'unreachable-{tag}', 'another-new-branch')
            _git(d, 'remote', 'set-url', 'origin', str(tmp / 'no-such-repo'))
            r = _run(guard, d, 'pre-write', f'unreachable-{tag}')
            cases.append((f'{tag}: pre-write still blocks when origin is '
                          f'unreachable, naming the fetch it could not make '
                          f'(exit {r.returncode})',
                          r.returncode == 2
                          and 'could not fetch origin/another-new-branch'
                          in r.stderr))

            # 4. Waving the missing counterpart through must not skip the
            # base-branch check, which is the one the guard exists for.
            d = _clone(f'stale-base-{tag}', 'stale-based-branch')
            (seed / 'g.txt').write_text('two\n', encoding='utf-8')
            _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'two')
            _git(seed, 'push', '-q', 'origin', 'main')
            r = _run(guard, d, 'pre-write', f'stale-base-{tag}')
            cases.append((f'{tag}: a branch absent from origin is still '
                          f'refused when its base moved (exit '
                          f'{r.returncode})',
                          r.returncode == 2
                          and 'missing 1 commit(s) from origin/main'
                          in r.stderr))
            _git(seed, 'reset', '-q', '--hard', 'HEAD~1')
            _git(seed, 'push', '-q', '--force', 'origin', 'main')

    failed = [n for n, ok in cases if not ok]
    check(f'freshness-guard separates a branch origin never saw from an '
          f'origin it could not reach ({len(cases)} stated cases, both '
          f'copies: absent branch waved through at pre-write and named at '
          f'session-start, unreachable origin still blocked, stale base '
          f'still refused)',
          not failed, '; '.join(failed))


def check_freshness_guard_lets_a_read_through_on_a_stale_branch():
    """On a branch whose base moved, pre-write lets a read-only Bash command
    through and still refuses the session's first write, the same session's
    included.

    2026-10-28: a read-only review session rooted on a feature branch four
    commits behind its base was refused its first command, and could read
    the branch only after setting precedent.freshness.override, which turns
    the guard off for that checkout for good. Reading a branch as it stands
    is what a review does; writing on a stale one is what the guard stops.

    Negative control, measured 2026-10-29: without _read_only_command's
    early exit the read case is refused (exit 2) and this check fails."""
    import tempfile
    guards = [ROOT / '.claude' / 'hooks' / 'freshness-guard.sh',
              ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'freshness-guard.sh']
    missing = [str(g.relative_to(ROOT)) for g in guards if not g.exists()]
    if missing:
        not_applicable('freshness-guard lets a read through on a stale branch',
                       f'not in this tree: {missing}')
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
            subprocess.run(['git', '-C', str(d), *a], capture_output=True,
                           text=True, env=env, check=True)

        origin, seed = tmp / 'origin', tmp / 'seed'
        subprocess.run(['git', 'init', '-q', '--bare', str(origin)],
                       capture_output=True, env=env, check=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)],
                       capture_output=True, env=env, check=True)
        (seed / 'f.txt').write_text('one\n', encoding='utf-8')
        _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'one')
        _git(seed, 'remote', 'add', 'origin', str(origin))
        _git(seed, 'push', '-q', 'origin', 'main')
        _git(origin, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        d = tmp / 'review'
        subprocess.run(['git', 'clone', '-q', str(origin), str(d)],
                       capture_output=True, env=env, check=True)
        _git(d, 'checkout', '-q', '-b', 'feature-under-review')
        (seed / 'g.txt').write_text('two\n', encoding='utf-8')
        _git(seed, 'add', '-A'); _git(seed, 'commit', '-qm', 'two')
        _git(seed, 'push', '-q', 'origin', 'main')

        def _run(guard, session, tool, tool_input):
            payload = json.dumps({'session_id': session, 'tool_name': tool,
                                  'tool_input': tool_input})
            return subprocess.run(['bash', str(guard), 'pre-write', 'main'],
                                  cwd=str(d), input=payload,
                                  capture_output=True, text=True, env=env)

        for guard in guards:
            tag = ('installed' if guard.parent.parent.parent == ROOT
                   else 'template')
            r = _run(guard, f'r-{tag}', 'Bash', {'command': 'cat f.txt | head -5'})
            cases.append((f'{tag}: a read-only command is let through on a '
                          f'stale branch (exit {r.returncode})', r.returncode == 0))
            r = _run(guard, f'r-{tag}', 'Bash', {'command': 'echo x > f.txt'})
            cases.append((f'{tag}: ...and the same session\'s first write is '
                          f'still refused, naming the missing commit (exit '
                          f'{r.returncode})', r.returncode == 2
                          and 'missing 1 commit(s) from origin/main' in r.stderr))
            r = _run(guard, f'w-{tag}', 'Write', {'file_path': 'f.txt'})
            cases.append((f'{tag}: a Write is refused (exit {r.returncode})',
                          r.returncode == 2))
            r = _run(guard, f's-{tag}', 'Bash', {'command': "sed -i s/one/two/ f.txt"})
            cases.append((f'{tag}: an in-place sed is a write, refused (exit '
                          f'{r.returncode})', r.returncode == 2))
    failed = [n for n, ok in cases if not ok]
    check(f'freshness-guard lets a read through on a stale branch and refuses '
          f'the write ({len(cases)} stated cases, both copies)',
          not failed, '; '.join(failed))


def check_bootstrap_separates_an_unpushed_branch_from_a_failed_fetch():
    """bootstrap.sh's freshness block, the same split
    check_freshness_guard_waves_through_a_branch_origin_never_saw asserts
    for the hook.

    `git fetch origin <branch>` fails with "couldn't find remote ref" on a
    branch that has never been pushed -- every fresh Claude Code web
    session -- and bootstrap.sh read that as a failed fetch, opening the
    session on "could not fetch -- freshness NOT verified" with nothing to
    be stale against. Reported 2026-09-25 from a consumer's session.

    Four cases per copy (the template an adopter instantiates, and this
    repo's own tools/bootstrap.sh): an unpushed branch is NOTEd, not WARNed;
    one cut from a stale base with no commits of its own is fast-forwarded;
    one with commits of its own on a stale base is WARNed about the base;
    and an unreachable origin still prints the unverified-fetch WARN,
    asserted by its message (control-asserts-which-failure)."""
    import tempfile

    scripts = [ROOT / 'templates' / 'bootstrap.sh', ROOT / 'tools' / 'bootstrap.sh']
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # A stub pip so the script's first line never reaches the network,
        # and an empty global config so no ambient identity or hooksPath
        # decides whether the fixture commits succeed (fixture-owns-its-state).
        (tmp / 'bin').mkdir()
        (tmp / 'bin' / 'pip').write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        (tmp / 'bin' / 'pip').chmod(0o755)
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        env = dict(os.environ)
        env.pop('CLAUDE_PROJECT_DIR', None)
        env['PATH'] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
        env['GIT_CONFIG_GLOBAL'] = str(tmp / 'gitconfig')
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = 'Harness'
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = 'harness@example.com'

        def _git(d, *a):
            r = subprocess.run(['git', '-C', str(d), *a],
                               capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise RuntimeError('bootstrap fixture setup failed: git %s: %s'
                                   % (' '.join(a), (r.stderr or r.stdout).strip()))
            return r

        origin = tmp / 'origin'
        _git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origin))
        seed = tmp / 'seed'
        _git(tmp, 'init', '-q', '-b', 'main', str(seed))
        _git(seed, 'commit', '-q', '--allow-empty', '-m', 'one')
        _git(seed, 'remote', 'add', 'origin', str(origin))
        _git(seed, 'push', '-q', 'origin', 'main')

        def _clone(name, branch):
            d = tmp / name
            _git(tmp, 'clone', '-q', str(origin), str(d))
            _git(d, 'checkout', '-q', '-b', branch)
            (d / 'precedent.json').write_text('{"base_branch": "main"}', encoding='utf-8')
            (d / '.git' / 'info' / 'exclude').write_text('precedent.json\n', encoding='utf-8')
            return d

        def _advance_base():
            _git(seed, 'commit', '-q', '--allow-empty', '-m', 'moved')
            _git(seed, 'push', '-q', 'origin', 'main')

        def _run(script, d):
            return subprocess.run(['bash', str(script)], cwd=str(d),
                                  capture_output=True, text=True, env=env).stderr

        for script in scripts:
            tag = str(script.relative_to(ROOT))
            d = _clone(f'absent-{script.parent.name}', 'unpushed')
            err = _run(script, d)
            cases.append((f'{tag}: an unpushed branch is named, not reported as an '
                          f'unverified fetch',
                          'is not on origin yet' in err and 'could not fetch' not in err,
                          failure_detail(err, 400)))

            d = _clone(f'stale-clean-{script.parent.name}', 'unpushed-stale')
            _advance_base()
            err = _run(script, d)
            cases.append((f'{tag}: an unpushed branch with no commits of its own, cut '
                          f'from a stale base, is fast-forwarded to it',
                          'fast-forwarded' in err
                          and _git(d, 'rev-parse', 'HEAD').stdout
                          == _git(d, 'rev-parse', 'origin/main').stdout, failure_detail(err, 400)))

            d = _clone(f'stale-own-{script.parent.name}', 'unpushed-own')
            _git(d, 'commit', '-q', '--allow-empty', '-m', 'mine')
            _advance_base()
            err = _run(script, d)
            cases.append((f'{tag}: an unpushed branch with commits of its own on a stale '
                          f'base is warned about the base, not moved',
                          'missing 1 commit(s) from origin/main' in err
                          and 'fast-forwarded' not in err, failure_detail(err, 400)))

            d = _clone(f'unreachable-{script.parent.name}', 'unpushed-unreachable')
            _git(d, 'remote', 'set-url', 'origin', str(tmp / 'no-such-repo'))
            err = _run(script, d)
            cases.append((f'{tag}: CONTROL: an unreachable origin still WARNs that '
                          f'freshness is not verified',
                          'could not fetch origin/unpushed-unreachable' in err
                          and 'freshness NOT verified' in err, failure_detail(err, 400)))

    bad = [(n, e) for n, ok, e in cases if not ok]
    check(f'bootstrap.sh separates a branch origin never saw from a fetch that failed '
          f'({len(cases)} stated cases, both copies)',
          not bad, '; '.join(f'{n} -- {e}' for n, e in bad))


def _session_start_tools_missing_from_bootstrap(hook_text, boot_text):
    """-> sorted tools/*.py names the hook RUNS that the bootstrap never runs.

    Only a `python3 ... tools/X.py` invocation counts, and comment lines are
    skipped: a script named in a comment or a WARN message is a citation,
    not a step, and counting it would let a mention stand in for the call."""
    def _run(text):
        return {m for line in text.splitlines()
                if not line.lstrip().startswith('#')
                for m in re.findall(r'python3\s+\S*?tools/(\w+)\.py', line)}
    return sorted(_run(hook_text) - _run(boot_text))


def check_bootstrap_runs_every_tool_session_start_runs():
    """tools/bootstrap.sh is the parallel templates/harness/PARALLELS.md
    names for .claude/hooks/session-start.sh on codex, gemini-cli and
    grok-build, so every tools/*.py the hook runs, the script runs too.

    Found by the 2026-09-28 very deep check: the hook ran
    precedent_engine_freshness.py and the beta-branch watermark check (now
    precedent_others_did.py, in the ladder set since 2026-10-17) and the script ran neither, while the PARALLELS.md row still called it a
    parallel -- the same gap, one step smaller, that the 2026-09-21 row
    records (three steps of seven). Planted by deleting the engine freshness
    call from a copy of the script: the missing name must come back."""
    hook = (ROOT / '.claude' / 'hooks' / 'session-start.sh').read_text(encoding='utf-8')
    boot = (ROOT / 'tools' / 'bootstrap.sh').read_text(encoding='utf-8')
    missing = _session_start_tools_missing_from_bootstrap(hook, boot)
    planted_boot = '\n'.join(ln for ln in boot.splitlines()
                             if 'precedent_engine_freshness.py' not in ln
                             or ln.lstrip().startswith('#'))
    planted = _session_start_tools_missing_from_bootstrap(hook, planted_boot)
    check('tools/bootstrap.sh runs every tools/*.py .claude/hooks/session-start.sh runs',
          not missing, 'the hook runs these and the script does not: '
          + ', '.join(missing))
    check('...PLANTED: a bootstrap.sh without the engine freshness call is caught by name',
          planted == ['precedent_engine_freshness'], repr(planted))
def check_gemini_settings_template_keeps_stdout_clean():
    """templates/harness/gemini-cli/settings.json wires tools/bootstrap.sh
    into Gemini CLI's SessionStart hook (2026-09-28). Gemini CLI parses a
    hook's stdout as JSON and treats anything else as a failed parse
    (google-gemini/gemini-cli docs/hooks/index.md, "Strict JSON
    requirements"), and bootstrap.sh prints to stdout on purpose. So the
    command sends it to stderr, and runs from $GEMINI_PROJECT_DIR because a
    hook's working directory is not promised to be the project root.

    Planted: the same command without the redirect leaks the script's
    stdout. Uses a stand-in bootstrap.sh that prints a line and leaves a
    marker, run from a different directory. The template also wires
    stop-git-check.sh to AfterAgent, whose exit 2 retries the turn with
    stderr as the prompt; that half is checked against the real script."""
    import tempfile

    data = json.loads((ROOT / 'templates' / 'harness' / 'gemini-cli'
                       / 'settings.json').read_text(encoding='utf-8'))
    events = {'BeforeTool', 'AfterTool', 'BeforeAgent', 'AfterAgent',
              'BeforeModel', 'AfterModel', 'BeforeToolSelection',
              'SessionStart', 'SessionEnd', 'PreCompress', 'Notification'}
    cases = [('every event the template names is a Gemini CLI hook event',
              set(data.get('hooks', {})) <= events, repr(sorted(data.get('hooks', {}))))]
    cmd = data['hooks']['SessionStart'][0]['hooks'][0]['command']
    with tempfile.TemporaryDirectory() as td:
        proj = pathlib.Path(td) / 'proj'
        (proj / 'tools').mkdir(parents=True)
        (proj / 'tools' / 'bootstrap.sh').write_text(
            'echo "bootstrap says hello"\n: > ran.marker\n', encoding='utf-8')
        env = dict(os.environ, GEMINI_PROJECT_DIR=str(proj))

        def _sh(c):
            return subprocess.run(['sh', '-c', c], cwd=td, capture_output=True,
                                  text=True, env=env, timeout=60)
        r = _sh(cmd)
        cases.append(('the command runs bootstrap.sh in the project and prints '
                      'nothing to stdout',
                      r.returncode == 0 and (proj / 'ran.marker').exists()
                      and r.stdout == '' and 'hello' in r.stderr,
                      f'rc={r.returncode} out={r.stdout!r} err={failure_detail(r.stderr, 200)!r}'))
        leaky = _sh(cmd.replace(' 1>&2', ''))
        cases.append(('PLANTED: without the redirect the script\'s line reaches stdout',
                      'hello' in leaky.stdout, repr(leaky.stdout)))

        # AfterAgent: exit 2 with the reason on stderr is Gemini CLI's
        # "retry with this as the prompt" (docs/hooks/reference.md), the
        # contract Claude Code's Stop has. The script must also keep stdout
        # empty, and honour stop_hook_active, which AfterAgent sends.
        after = data['hooks'].get('AfterAgent', [])
        stop_cmds = [h['command'] for g in after for h in g['hooks']
                     if 'stop-git-check.sh' in h['command']]
        cases.append(('AfterAgent runs stop-git-check.sh', len(stop_cmds) == 1,
                      repr(stop_cmds)))
        if stop_cmds:
            (proj / '.claude' / 'hooks').mkdir(parents=True)
            shutil.copy(ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
                        / 'stop-git-check.sh', proj / '.claude' / 'hooks')
            # The stub runs its script from tools/, as an install has it.
            (proj / 'tools').mkdir(exist_ok=True)
            shutil.copy(ROOT / 'tools' / 'stop-git-check.sh', proj / 'tools')
            genv = dict(env, GIT_CONFIG_GLOBAL=str(pathlib.Path(td) / 'gitconfig'))
            pathlib.Path(genv['GIT_CONFIG_GLOBAL']).write_text('', encoding='utf-8')
            for a in (('init', '-q', '-b', 'main'),
                      ('remote', 'add', 'origin', str(pathlib.Path(td) / 'none'))):
                subprocess.run(['git', '-C', str(proj), *a], check=True,
                               capture_output=True, env=genv)

            def _stop(active):
                return subprocess.run(
                    ['sh', '-c', stop_cmds[0]], cwd=td, capture_output=True,
                    text=True, env=genv, timeout=60,
                    input=json.dumps({'hook_event_name': 'AfterAgent',
                                      'stop_hook_active': active}))
            s = _stop(False)
            cases.append(('over untracked files, AfterAgent exits 2 with the '
                          'reason on stderr and nothing on stdout',
                          s.returncode == 2 and 'Untracked files' in s.stderr
                          and s.stdout == '', f'rc={s.returncode} out={s.stdout!r}'))
            s2 = _stop(True)
            cases.append(('...and lets the retry end when stop_hook_active is set',
                          s2.returncode == 0, f'rc={s2.returncode}'))
    bad = [(n, e) for n, ok, e in cases if not ok]
    check(f'the gemini-cli settings template runs bootstrap.sh with a JSON-clean '
          f'stdout ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {e}' for n, e in bad))


def check_maintainer_heartbeat_names_a_missing_maintainer_once():
    """tools/precedent_heartbeat.py, practice master-maintainer: a beat
    lands on the coord branch and never on the trunk, reads back as fresh,
    and a session start in a repository whose heartbeat is missing or stale
    is told to tell the person, with the prompt that starts one.

    2026-10-20 (S. Alexander Jacobson, strength: decided): one standing
    maintainer per repository replaces the per-person switchboard, and its
    heartbeat is what makes a dead one visible. Negative controls: a
    repository that declares no maintainer hears nothing, and a fresh beat
    says nothing."""
    import tempfile
    tool = ROOT / 'tools' / 'precedent_heartbeat.py'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        remote, work = pathlib.Path(td) / 'remote.git', pathlib.Path(td) / 'work'
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
        env.pop('CLAUDE_PROJECT_DIR', None)

        def git(*a, cwd=None):
            return subprocess.run(['git', *a], cwd=cwd, env=env, capture_output=True,
                                  text=True, timeout=60)
        git('init', '-q', '--bare', str(remote))
        git('clone', '-q', str(remote), str(work))
        cfg = {'base_branch': 'main', 'maintainer': {'title': 'Master maintainer (t)',
               'prompt_file': 'process/jobs/maintainer.md', 'stale_after_hours': 24}}
        (work / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        git('add', '.', cwd=work)
        git('commit', '-qm', 'init', cwd=work)
        git('push', '-q', 'origin', 'HEAD:main', cwd=work)

        def run(*a):
            return subprocess.run([sys.executable, str(tool), '--repo', str(work), *a],
                                  env=env, capture_output=True, text=True, timeout=60)
        r = run('--hook')
        cases.append(('THE DISCRIMINATING CASE: no heartbeat yet, and session start '
                      'is told the repository has no maintainer, with the prompt',
                      'NO LIVE MASTER MAINTAINER' in r.stdout
                      and 'process/jobs/maintainer.md' in r.stdout, r.stdout + r.stderr))
        trunk = git('rev-parse', 'origin/main', cwd=work).stdout
        r = run('beat')
        git('fetch', '-q', 'origin', cwd=work)
        cases.append(('a beat lands on the side branch, reads back fresh, and leaves '
                      'the trunk alone',
                      r.returncode == 0 and git('rev-parse', 'origin/main', cwd=work).stdout == trunk
                      and git('ls-remote', '--heads', 'origin', 'coord',
                              cwd=work).stdout.strip() != '', r.stdout + r.stderr))
        r = run('--hook')
        cases.append(('negative control: a fresh heartbeat says nothing',
                      not r.stdout, r.stdout))
        cfg['maintainer']['stale_after_hours'] = 0
        (work / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        r = run('--hook')
        cases.append(('a heartbeat past its limit is named as stale',
                      'NO LIVE MASTER MAINTAINER' in r.stdout and 'hours old' in r.stdout,
                      r.stdout + r.stderr))
        (work / 'precedent.json').write_text(json.dumps({'base_branch': 'main'}),
                                             encoding='utf-8')
        r = run('--hook')
        cases.append(('negative control: a repository with no maintainer block hears '
                      'nothing', not r.stdout, r.stdout))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the maintainer heartbeat names a missing maintainer once '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_session_hooks_allow_read_only_tools_at_user_level():
    """A session opened above several repositories reads none of their
    permission rules (Claude Code's settings docs), so the runner adds the
    read-only Precedent tool rules to user-level settings, add-only
    (2026-10-14). THE DISCRIMINATING CASE: a write-capable rule a repository
    allows (git push) never reaches user level, and what the user file
    already holds -- its hooks, its own allow and deny rules -- is kept.
    Since 2026-10-18 the one rule that allows every engine tool arrives on
    its own: no rule makes landing, Produce or merging ask (2026-10-17 to
    2026-10-18 they did)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_run_session_hooks as rsh
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / 'home'
        repo = root / 'consumer'
        (repo / '.git').mkdir(parents=True)
        (repo / '.claude').mkdir()
        (repo / '.claude' / 'settings.json').write_text(json.dumps({'permissions': {
            'allow': ['Bash(git push -u origin *)',
                      'Bash(python3 tools/doc_lint.py *)']}}), encoding='utf-8')
        user = pathlib.Path(td) / 'user-settings.json'
        mine = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command',
                                                       'command': 'true'}]}]},
                'permissions': {'allow': ['Bash(ls)'],
                                'deny': ['Bash(python3 tools/precedent_gate.py *)']}}
        user.write_text(json.dumps(mine), encoding='utf-8')
        rsh.run(root, log=pathlib.Path(td) / 'log', say=lambda m: None,
                user_settings=user)
        got = json.loads(user.read_text(encoding='utf-8'))
        allow = got['permissions']['allow']
        cases.append(('THE DISCRIMINATING CASE: no write-capable rule reaches user level',
                      not any('push' in r for r in allow), allow))
        cases.append(('the read-only rules arrive, from the repository and the template',
                      'Bash(python3 tools/doc_lint.py *)' in allow
                      and 'Bash(python3 tools/precedent_*)' in allow, allow))
        asked = got['permissions'].get('ask') or []
        cases.append(('THE DISCRIMINATING CASE (2026-10-18): no ask rule reaches '
                      'user level, so landing, Produce and the merge never wait '
                      'for a click', asked == [], asked))
        cases.append(('what the user file held is kept, and a denied rule is not added',
                      got['hooks'] == mine['hooks'] and allow[0] == 'Bash(ls)'
                      and got['permissions']['deny'] == mine['permissions']['deny']
                      and 'Bash(python3 tools/precedent_gate.py *)' not in allow, got))
        before = user.read_text(encoding='utf-8')
        rsh.run(root, log=pathlib.Path(td) / 'log', say=lambda m: None,
                user_settings=user)
        cases.append(('a second session start changes nothing',
                      user.read_text(encoding='utf-8') == before, ''))
        # A container that ran the runner from 2026-10-17 to 2026-10-19 holds
        # the ask rules it wrote then; they come out, and the person's own
        # ask rule stays (Morgan, 2026-10-19: "Go").
        held = dict(mine, permissions=dict(mine['permissions'], ask=[
            'Bash(python3 tools/precedent_branches.py --land *)',
            'mcp__github__merge_pull_request', 'Bash(rm -rf *)']))
        user.write_text(json.dumps(held), encoding='utf-8')
        rsh.run(root, log=pathlib.Path(td) / 'log', say=lambda m: None,
                user_settings=user)
        left = json.loads(user.read_text(encoding='utf-8'))['permissions'].get('ask')
        cases.append(('THE DISCRIMINATING CASE (2026-10-19): the ask rules this '
                      'runner wrote while the engine shipped them are taken back '
                      'out, and the person\'s own ask rule stays',
                      left == ['Bash(rm -rf *)'], left))
        user.write_text('{oops', encoding='utf-8')
        rsh.run(root, log=pathlib.Path(td) / 'log', say=lambda m: None,
                user_settings=user)
        cases.append(('a user file that does not parse is left as it was',
                      user.read_text(encoding='utf-8') == '{oops', ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'session start allows read-only Precedent tools at user level '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_session_hooks_run_for_a_session_opened_above_the_repos():
    """tools/precedent_run_session_hooks.py runs each repository's own
    SessionStart hooks when a session is opened in the directory ABOVE them
    -- the multi-repo shape in which Claude Code runs no repo's hooks at all
    (gotcha-2026-09-25; very deep check, 2026-09-28). Planted: two repos
    whose hook records the CLAUDE_PROJECT_DIR it saw and prints context; the
    discriminating case is a root WITH its own settings, where the native
    hooks already ran and the runner must do nothing."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_run_session_hooks as rsh
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='session-hooks-above-'))
    cases = []
    try:
        root = tmp / 'root'
        for name in ('alpha', 'beta'):
            repo = root / name
            (repo / '.git').mkdir(parents=True)
            (repo / '.claude').mkdir()
            (repo / '.claude' / 'settings.json').write_text(json.dumps({
                'hooks': {'SessionStart': [{'hooks': [{
                    'type': 'command',
                    'command': 'echo "$CLAUDE_PROJECT_DIR" > "$CLAUDE_PROJECT_DIR/ran"; '
                               'echo "$PRECEDENT_SESSION_ROOT" > "$CLAUDE_PROJECT_DIR/root"; '
                               'echo "context from ' + name + '"'}]}]}}),
                encoding='utf-8')
        (root / 'not-a-repo').mkdir()
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ran = rsh.run(root, log=tmp / 'log', say=lambda m: None)
        out = buf.getvalue()
        for name in ('alpha', 'beta'):
            seen = (root / name / 'ran')
            cases.append((f'{name}\'s own hook ran, with its own project dir',
                          seen.is_file() and seen.read_text().strip()
                          == str((root / name).resolve()), repr(ran)))
        cases.append(('each hook is told the folder the session was opened in '
                      '(PRECEDENT_SESSION_ROOT, 2026-11-01)',
                      (root / 'alpha' / 'root').is_file()
                      and (root / 'alpha' / 'root').read_text().strip()
                      == str(root.resolve()), repr(ran)))
        cases.append(('what each hook printed reaches the session as one '
                      'context block', 'context from alpha' in out
                      and 'context from beta' in out, out[:300]))
        (root / 'alpha' / 'ran').unlink()
        (root / '.claude').mkdir()
        (root / '.claude' / 'settings.json').write_text('{}', encoding='utf-8')
        # A setup script that writes the hook to /home/user/.claude rather
        # than ~/.claude gives the non-repository root settings of its own;
        # those are not a repository's hooks, so the runner still runs.
        with contextlib.redirect_stdout(io.StringIO()):
            ran_folder = rsh.run(root, log=tmp / 'log', say=lambda m: None)
        cases.append(('a root that is a plain folder with settings of its own '
                      'still runs its repos\' hooks',
                      (root / 'alpha' / 'ran').is_file(), repr(ran_folder)))
        (root / 'alpha' / 'ran').unlink(missing_ok=True)
        (root / '.git').mkdir()
        ran2 = rsh.run(root, log=tmp / 'log', say=lambda m: None)
        cases.append(('THE DISCRIMINATING CASE: a root that is a repository '
                      'with its own settings runs nothing (its hooks ran '
                      'natively)',
                      ran2 == [] and not (root / 'alpha' / 'ran').exists(),
                      repr(ran2)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a session opened above its repos still runs their SessionStart '
          f'hooks ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_hook_notes_are_said_when_they_change():
    """The notes about hooks this engine leaves unvendored -- one a source's
    adapters keep, ones this repo does not wire -- are printed by a refresh
    when that state changes, not on every refresh; `status` names them.

    WHY. A consuming repository's Update Vendors, 2026-10-12: those notes
    are states, never tasks, and came out on every refresh, so every
    update's upstream review listed eight items with nothing to do.
    Planted: a consumer wiring two hooks, one of them kept by an adapter.
    The first write says the unwired note and never the adapter one (a
    consumer, 2026-10-13: six adapter notes on a first update, none a
    task); a second with the same state says neither; the adapter claim dropped, the change is said; status lists
    what the record holds."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    cases = []
    src = ROOT / pve.HOOK_SOURCE_DIR
    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        (dest / 'tools').mkdir()
        (dest / '.claude' / 'hooks').mkdir(parents=True)
        mpath = dest / 'tools' / pve.MANIFEST_NAME
        mpath.write_text(json.dumps({'kind': 'consumer', 'files': []}), encoding='utf-8')
        (dest / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
            'SessionStart': [{'hooks': [
                {'type': 'command', 'command': f'$CLAUDE_PROJECT_DIR/.claude/hooks/{n}'}
                for n in ('freshness-guard.sh', 'stop-git-check.sh')]}]}}),
            encoding='utf-8')
        claim = json.dumps({'generated_by': 'tools/precedent_materialize.py',
                            'adapters': [{'path': '.claude/hooks/freshness-guard.sh',
                                          'source': 'precedent-individual'}]})
        (dest / 'MANIFEST.json').write_text(claim, encoding='utf-8')

        def write(previous):
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                pve._write_hook_files(dest, src, previous=previous)
            return err.getvalue()

        def manifest():
            return json.loads(mpath.read_text(encoding='utf-8'))
        out = write(None)
        cases.append(('the first refresh says the unwired ones and never the '
                      'adapter-kept hook', 'is not vendored by this engine' not in out
                      and "adapters mechanism owns" not in out
                      and 'are not wired in this repo' in out, failure_detail(out, 600)))
        rec = manifest().get(pve.HOOKS_NOT_VENDORED_KEY) or {}
        cases.append(('...and records what it said',
                      rec.get('adapters') == {'freshness-guard.sh': 'precedent-individual'}
                      and bool(rec.get('not_wired')), str(rec)))
        out = write(manifest())
        cases.append(('the next refresh, nothing changed, says neither',
                      'is not vendored by this engine' not in out
                      and 'are not wired in this repo' not in out, failure_detail(out, 600)))
        (dest / 'MANIFEST.json').unlink()
        out = write(manifest())
        cases.append(('a change -- the adapter claim gone -- is said',
                      'are not wired in this repo' in out
                      and not (manifest().get(pve.HOOKS_NOT_VENDORED_KEY) or {}).get('adapters'),
                      failure_detail(out, 600)))
        (dest / 'MANIFEST.json').write_text(claim, encoding='utf-8')
        write(manifest())
        saved_root = pve.ROOT
        try:
            pve.ROOT = dest
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                try:
                    pve.status(ROOT)
                except SystemExit:
                    pass
        finally:
            pve.ROOT = saved_root
        st = buf.getvalue()
        cases.append(('status names what the record holds, adapters included',
                      'leaves unvendored' in st
                      and "kept by 'precedent-individual'" in st, failure_detail(st, 800)))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the unvendored-hook notes are said when they change ({len(cases)} '
          f'stated cases)', not bad, '; '.join(bad))


def check_vendor_engine_wires_a_new_hook_into_an_installed_repo():
    """THE BUG (todo-2026-09-21-a-new-hook-cannot-reach-an-installed-
    consumer.md). Vendoring was gated on the repo's own settings.json and a
    refresh never wrote it, so a hook added upstream could not reach a repo
    that was already installed. Since 2026-09-25 a refresh ADDS the entries
    HOOK_WIRING gives the repo's kind, then vendors as before.

    The fixture is an installed consumer as it would really look: the
    consumer template with its base branch set to `trunk`, minus the entries
    a repo installed before they existed would lack (doc-lint-gate.sh,
    commit-identity-once.sh, and the user-prompt freshness guard), plus a
    hook of its own in the Bash group and a declared decline for
    stop-reply-check.sh. Cases:

    A. the missing hooks are wired and their files arrive, on one refresh;
    B. the base branch is read off the repo's own freshness-guard entries,
       never assumed to be `main`;
    C. ADD-ONLY: every entry the repo had is still there, in order, and its
       own hook keeps its group -- the new Bash entry joins that group;
    D. the declined hook is neither wired nor vendored;
    E. a second refresh at the same commit is a no-op, byte for byte;
    F. CONTROL: the same repo with no `kind` in its manifest is not wired at
       all -- guessing a kind is how a consumer would get a set's hooks;
    G. a repo that never ran freshness-guard.sh (a classic install migrated
       onto the loader, 2026-10-02) gets all three entries from
       precedent.json's base_branch, and the run says where the branch came
       from -- until then the refresh printed "not guessed. Wire it by
       hand", a remedy the harness refuses a session;
    H. CONTROL: with neither an entry nor a base_branch, nothing is wired
       and the NOTE says what to set;
    I. the gitignore template is merged, so the per-machine settings file
       and the private .precedent/ channel are ignored;
    J. for a person with an individual set, the individual-set bootstrap
       hook is written from its template with NO repository URL and wired
       FIRST in SessionStart -- migration step 4 used to make this a manual
       run a session is refused; every other case runs with no individual
       signal at all, HOME pointed at the fixture, which is its control."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-hook-wiring-'))
    cases = []
    try:
        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        template = json.loads((ROOT / 'templates' / 'harness' / 'claude-code'
                               / 'settings.json').read_text(encoding='utf-8'))
        dropped = ('doc-lint-gate.sh', 'commit-identity-once.sh',
                   'freshness-guard.sh user-prompt', 'stop-reply-check.sh')

        def make_repo(name, with_kind, drop=dropped, base_branch=None):
            repo = tmp / name
            (repo / 'tools').mkdir(parents=True)
            (repo / '.claude' / 'hooks').mkdir(parents=True)
            (repo / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            man = {'source_commit': 'deadbeef',
                   'files': ['precedent_vendor_engine.py'],
                   'sha256': {'precedent_vendor_engine.py':
                              hashlib.sha256(engine_bytes).hexdigest()}}
            if with_kind:
                man['kind'] = 'consumer'
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(man), encoding='utf-8')
            hooks = {}
            for event, groups in template['hooks'].items():
                for g in groups:
                    kept = [dict(h, command=h['command'].replace(' main', ' trunk'))
                            for h in g['hooks']
                            if not any(d in h['command'] for d in drop)]
                    if g.get('matcher') == 'Bash':
                        kept.insert(0, {'type': 'command',
                                        'command': '$CLAUDE_PROJECT_DIR/tools/my-own.sh'})
                    if kept:
                        hooks.setdefault(event, []).append(dict(g, hooks=kept))
            (repo / '.claude' / 'settings.json').write_text(
                json.dumps({'hooks': hooks}, indent=2) + '\n', encoding='utf-8')
            cfg = {'declined_adapters': [
                {'path': '.claude/hooks/stop-reply-check.sh',
                 'reason': 'this repo gates replies elsewhere'}]}
            if base_branch:
                cfg['base_branch'] = base_branch
            (repo / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            return repo, hooks

        ref = _ref_including_worktree(ROOT)

        # No individual signal unless a case adds one: whether the person
        # running a refresh has an individual set decides case J, so the
        # container's own token and $HOME must not decide it here
        # (practice: fixture-owns-its-state).
        home = tmp / 'home'
        home.mkdir()
        base_env = {k: v for k, v in os.environ.items()
                    if k not in ('PRECEDENT_GIT_TOKEN', 'PRECEDENT_SOURCE_BASE_URL',
                                 'PRECEDENT_INDIVIDUAL_REPO', 'XDG_CONFIG_HOME')}
        base_env['HOME'] = str(home)

        def run_refresh(repo, extra_env=None):
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--from-ref', ref],
                capture_output=True, text=True, cwd=str(repo),
                env=dict(base_env, **(extra_env or {})))
            return r.returncode, r.stdout + r.stderr

        def commands(settings, event=None):
            return [h['command'] for ev, gs in settings['hooks'].items()
                    if event in (None, ev) for g in gs for h in g['hooks']]

        repo, before = make_repo('consumer', True)
        rc1, out1 = run_refresh(repo)
        after = json.loads((repo / '.claude' / 'settings.json').read_text(encoding='utf-8'))
        cmds = commands(after)
        detail = f'rc={rc1} {out1[-900:]}'
        cases.append(('the refresh succeeds', rc1 == 0, detail))
        for name in ('doc-lint-gate.sh', 'commit-identity-once.sh'):
            cases.append((f'A: {name} is wired', any(name in c for c in cmds),
                          repr(cmds)))
            cases.append((f'A: ...and its file arrived on the same refresh',
                          (repo / '.claude' / 'hooks' / name).is_file(), detail))
        cases.append(('B: the re-added freshness guard carries the repo\'s own '
                      'base branch, trunk, not main',
                      any(c.endswith('freshness-guard.sh user-prompt trunk')
                          for c in commands(after, 'UserPromptSubmit')), repr(cmds)))
        kept_in_order = all(
            [h['command'] for h in g['hooks']][:len(og['hooks'])]
            == [h['command'] for h in og['hooks']]
            for event, ogs in before.items()
            for og, g in zip(ogs, after['hooks'][event]))
        cases.append(('C: every entry the repo already had is still there, in '
                      'its group, in order', kept_in_order, repr(after)[:900]))
        bash_groups = [g for g in after['hooks']['PreToolUse']
                       if g.get('matcher') == 'Bash']
        cases.append(('C: the new Bash entry joined the repo\'s existing Bash '
                      'group beside its own hook, not a second group',
                      len(bash_groups) == 1 and any(
                          'doc-lint-gate.sh' in h['command']
                          for h in bash_groups[0]['hooks']), repr(bash_groups)))
        gi = (repo / '.gitignore').read_text(encoding='utf-8') \
            if (repo / '.gitignore').is_file() else ''
        cases.append(('I: the refresh merged the gitignore template, so the '
                      'per-machine settings file commit-identity.sh writes and '
                      'the private .precedent/ channel are ignored before the '
                      'next session start writes either (2026-10-02)',
                      '.claude/settings.local.json' in gi.splitlines()
                      and '.precedent/' in gi.splitlines(), failure_detail(gi, 300)))
        cases.append(('D: the declined hook is not wired',
                      not any('stop-reply-check.sh' in c for c in cmds), repr(cmds)))
        cases.append(('D: ...and not vendored',
                      not (repo / '.claude' / 'hooks' / 'stop-reply-check.sh').exists(),
                      detail))
        snap = (repo / '.claude' / 'settings.json').read_bytes()
        rc2, out2 = run_refresh(repo)
        cases.append(('E: a second refresh at the same commit has nothing to do',
                      rc2 == 0 and 'nothing to do' in out2, failure_detail(out2, 600)))
        cases.append(('E: ...and leaves settings.json byte-identical',
                      (repo / '.claude' / 'settings.json').read_bytes() == snap, ''))

        ctl, ctl_before = make_repo('no-kind', False)
        ctl_snap = (ctl / '.claude' / 'settings.json').read_bytes()
        rc3, out3 = run_refresh(ctl)
        cases.append(('F CONTROL: a manifest with no kind gets no wiring at all',
                      (ctl / '.claude' / 'settings.json').read_bytes() == ctl_snap,
                      f'rc={rc3} {failure_detail(out3, 600)}'))
        cases.append(('F CONTROL: ...and no .gitignore merge -- a practice set '
                      'keeps its own', not (ctl / '.gitignore').exists(), ''))

        no_guard = dropped + ('freshness-guard.sh',)
        mig, _ = make_repo('migrated', True, drop=no_guard, base_branch='trunk')
        rc4, out4 = run_refresh(mig)
        mig_cmds = commands(json.loads(
            (mig / '.claude' / 'settings.json').read_text(encoding='utf-8')))
        guards = sorted(c.split('freshness-guard.sh ', 1)[1]
                        for c in mig_cmds if 'freshness-guard.sh' in c)
        cases.append(('G: a repo that never ran the guard gets all three '
                      'entries, on precedent.json\'s base_branch',
                      rc4 == 0 and guards == ['pre-write trunk',
                                              'session-start trunk',
                                              'user-prompt trunk'],
                      f'rc={rc4} {guards} {failure_detail(out4, 600)}'))
        cases.append(('G: ...and the run says the branch came from '
                      'precedent.json, with no "wire it by hand" NOTE',
                      "precedent.json's base_branch" in out4
                      and 'Wire it by hand' not in out4, failure_detail(out4, 900)))
        bare, _ = make_repo('no-base', True, drop=no_guard)
        rc5, out5 = run_refresh(bare)
        bare_cmds = commands(json.loads(
            (bare / '.claude' / 'settings.json').read_text(encoding='utf-8')))
        cases.append(('J CONTROL: with no individual signal the individual-'
                      'set hook is neither written nor wired',
                      not (repo / '.claude' / 'hooks'
                           / 'precedent-individual-bootstrap.sh').exists()
                      and not any('precedent-individual-bootstrap' in c
                                  for c in cmds), repr(cmds)[:400]))
        ind, _ = make_repo('individual', True, base_branch='trunk')
        rc6, out6 = run_refresh(ind, {'PRECEDENT_GIT_TOKEN': 'fixture-not-a-token'})
        ind_set = json.loads((ind / '.claude' / 'settings.json')
                             .read_text(encoding='utf-8'))
        first = ind_set['hooks']['SessionStart'][0]['hooks'][0]['command']
        hook = ind / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        body = hook.read_text(encoding='utf-8') if hook.is_file() else ''
        cases.append(('J: a person with an individual set gets the bootstrap '
                      'hook written and wired FIRST in SessionStart',
                      rc6 == 0 and hook.is_file()
                      and first.endswith('/.claude/hooks/precedent-individual-bootstrap.sh'),
                      f'rc={rc6} first={first!r} {failure_detail(out6, 500)}'))
        cases.append(('J: ...rendered with no repository URL and no '
                      'placeholder left, so nothing about the person is baked '
                      'into a repo that may be public',
                      'PRECEDENT_INDIVIDUAL_DEFAULT_URL=""' in body and '{{' not in body
                      and 'fixture-not-a-token' not in body, body[:200]))
        rc7, out7 = run_refresh(ind, {'PRECEDENT_GIT_TOKEN': 'fixture-not-a-token'})
        cases.append(('J: ...and a second refresh has nothing to do',
                      rc7 == 0 and 'nothing to do' in out7, failure_detail(out7, 400)))

        cases.append(('H CONTROL: with no entry and no base_branch the guard '
                      'is not wired, and the NOTE names base_branch to set',
                      not any('freshness-guard.sh' in c for c in bare_cmds)
                      and 'Set base_branch in precedent.json' in out5,
                      f'rc={rc5} {failure_detail(out5, 900)}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f"a refresh wires a hook its kind's list names into an installed repo, "
          f"add-only, and the file arrives on the same run ({len(cases)} stated "
          f"cases)", not bad, '; '.join(f'{n} -- {d[:700]}' for n, d in bad))

def check_vendor_engine_refreshes_bootstrap_sh():
    """Nothing delivered a templates/bootstrap.sh change to an installed
    consumer -- see precedent_vendor_engine.py's TEMPLATE_INSTANCES block
    (2026-09-25) for the measured case: a consumer whose bootstrap.sh was
    the stock template minus two blocks added two days earlier, told
    "already current -- nothing to do" by every refresh.

    THE FIXTURE OWNS ITS UPSTREAM (practice: fixture-owns-its-state). It
    builds one synthetic commit on top of this working tree whose only change
    is a new, distinctive block in templates/bootstrap.sh, so the tree under
    test always has exactly one known past version (OLD) and one current
    version (CUR) -- however shallow this clone's own history is, and
    whatever real edits the template picks up later. The commit is an object
    only: no ref points at it and nothing is checked out.

    Seven cases, one fresh consumer each. The discriminating ones are the
    edited copies: never overwritten, --force included, and the report names
    the exact block a copy lacks rather than just calling it different
    (practice: control-asserts-which-failure)."""
    import shutil, tempfile
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bootstrap-instance-'))
    cases = []
    rel = 'tools/bootstrap.sh'
    marker = 'FIXTURE BLOCK ADDED UPSTREAM'
    try:
        base = _ref_including_worktree(ROOT)
        old = subprocess.run(['git', '-C', str(ROOT), 'show',
                              f'{base}:templates/bootstrap.sh'],
                             capture_output=True, check=True).stdout
        added = (f'# {marker} -- the block a stale copy lacks\n'
                 'if [ -f tools/fixture_probe.py ]; then\n'
                 '  python3 tools/fixture_probe.py --fixture-only || true\n'
                 'fi\n\n').encode()
        tail = b'# A bootstrap that blocks startup'
        assert old.count(tail) == 1, 'template tail moved; repoint this fixture'
        cur = old.replace(tail, added + tail)

        with tempfile.TemporaryDirectory(prefix='precedent-fixture-index-') as idx:
            env = dict(os.environ, GIT_INDEX_FILE=str(pathlib.Path(idx) / 'index'),
                       GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                       GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')

            def git(*args, data=None):
                return subprocess.run(['git', '-C', str(ROOT), *args], input=data,
                                      capture_output=True, env=env, check=True
                                      ).stdout.decode().strip()
            git('read-tree', base)
            blob = git('hash-object', '-w', '--stdin', data=cur)
            git('update-index', '--cacheinfo', f'100755,{blob},templates/bootstrap.sh')
            ref = git('commit-tree', git('write-tree'), '-p', base, '-m',
                      'verify_harness: bootstrap.sh fixture (never pushed)')

        engine_bytes = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_bytes()
        sha = lambda b: hashlib.sha256(b).hexdigest()

        def make_consumer(name, boot_bytes, recorded):
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / 'tools' / 'precedent_vendor_engine.py').write_bytes(engine_bytes)
            manifest = {'kind': 'consumer', 'source_commit': 'deadbeef',
                        'files': ['precedent_vendor_engine.py'],
                        'sha256': {'precedent_vendor_engine.py': sha(engine_bytes)}}
            if recorded is not None:
                manifest['template_instances_sha256'] = {rel: recorded}
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(manifest), encoding='utf-8')
            if boot_bytes is not None:
                (consumer / rel).write_bytes(boot_bytes)
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
            return (m.get('template_instances_sha256') or {}).get(rel)

        # -- A: unedited (matches its recorded baseline), template moved --
        a = make_consumer('recorded-stale', old, sha(old))
        rc, out = run_refresh(a)
        cases.append(('an unedited bootstrap.sh whose baseline is recorded is '
                      'rewritten to the current template',
                      rc == 0 and (a / rel).read_bytes() == cur, failure_detail(out, 800)))
        cases.append(('...its new baseline is the current template, and the '
                      'refresh says what it did',
                      recorded_of(a) == sha(cur)
                      and 'brought tools/bootstrap.sh up to the current template' in out,
                      failure_detail(out, 800)))

        # -- B: nothing recorded, byte-identical to a PAST template -- every
        # install that predates tracking, the measured case --
        b = make_consumer('untracked-stale', old, None)
        rc, out = run_refresh(b)
        cases.append(('an untracked bootstrap.sh identical to a past version of '
                      'the template is recognised as stock and brought up to date',
                      rc == 0 and (b / rel).read_bytes() == cur
                      and recorded_of(b) == sha(cur), failure_detail(out, 800)))

        # -- C: edited (an old copy plus a local line), baseline recorded --
        edited = old.replace(tail, b'echo "a line this repo added"\n\n' + tail)
        for name, label, extra in (('edited', '', ()),
                                   ('edited-forced', ' with --force', ('--force',))):
            c = make_consumer(name, edited, sha(old))
            rc, out = run_refresh(c, extra)
            cases.append((f'an edited bootstrap.sh is never overwritten{label}',
                          (c / rel).read_bytes() == edited, failure_detail(out, 800)))
            cases.append((f'...the refresh still succeeds and reports it DIVERGED, '
                          f'naming the missing upstream block{label}',
                          rc == 0 and f'DIVERGED: {rel}' in out
                          and marker in out and '-- missing' in out, failure_detail(out, 1200)))
            cases.append((f'...its baseline is NOT moved onto the edit{label}, so a '
                          f'later refresh cannot mistake it for stock',
                          recorded_of(c) == sha(old), failure_detail(out, 400)))

        # -- D: a copy missing one block the template has always had, and
        # nothing else -- names THAT block, and not the one it does carry --
        blocks = pve._shell_blocks(cur.decode())
        victim = next(b for b in blocks
                      if any('precedent_engine_freshness.py --quiet' in ln for ln in b[2]))
        cur_lines = cur.decode().splitlines(keepends=True)
        start = victim[0] - 1
        end = start
        while end < len(cur_lines) and cur_lines[end].strip():
            end += 1
        lacking = ''.join(cur_lines[:start] + cur_lines[end:]).encode()
        d = make_consumer('missing-a-block', lacking, None)
        rc, out = run_refresh(d)
        report = [ln for ln in out.splitlines() if 'templates/bootstrap.sh:' in ln]
        cases.append(('THE DISCRIMINATING CASE: a copy missing one block is left '
                      'alone and the report names exactly that block, missing',
                      rc == 0 and (d / rel).read_bytes() == lacking
                      and len(report) == 1
                      and f'templates/bootstrap.sh:{victim[0]} ' in report[0]
                      and report[0].endswith('-- missing'), '\n'.join(report) or failure_detail(out, 800)))
        cases.append(('...and it lands on the Left-for-you list, where step 10 '
                      'of the runbook works from',
                      f'  - {rel}: diverged from templates/bootstrap.sh and lacks 1' in out,
                      failure_detail(out, 800)))

        # -- E, CONTROL: edited but carrying every block -- no lacks list --
        extra_line = cur.replace(tail, b'echo "ours"\n\n' + tail)
        e = make_consumer('edited-complete', extra_line, None)
        rc, out = run_refresh(e)
        cases.append(('CONTROL: an edited copy that carries every template block '
                      'is left alone and reported as lacking nothing',
                      rc == 0 and (e / rel).read_bytes() == extra_line
                      and 'carries every block' in out and 'Left for you' not in out,
                      failure_detail(out, 800)))

        # -- F: already the current template, nothing recorded -- recorded --
        f = make_consumer('current', cur, None)
        rc, out = run_refresh(f)
        cases.append(('a copy already identical to the template gets a baseline '
                      'and is otherwise untouched',
                      rc == 0 and (f / rel).read_bytes() == cur
                      and recorded_of(f) == sha(cur) and 'DIVERGED' not in out,
                      failure_detail(out, 800)))

        # -- G: no bootstrap.sh at all -- never recreated --
        g = make_consumer('absent', None, None)
        rc, out = run_refresh(g)
        cases.append(('CONTROL: a consumer with no bootstrap.sh is not given one',
                      rc == 0 and not (g / rel).exists(), failure_detail(out, 800)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'"Update Vendors" delivers templates/bootstrap.sh to an unedited copy '
          f'and reports what an edited one lacks, never overwriting it '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:800]}" for n, d in bad))

def check_template_text_edit_trips_the_commit_check():
    """A commit in a consuming repository that edits text the Precedent
    template wrote is refused at commit time with the two answers (fix it
    upstream, or keep it as this repository's own), until one is recorded
    (2026-10-31, tools/upstream_edits.py staged_template_edits; Morgan: a
    fix made in a consumer to BestPractice's text becomes a fork nobody
    decided).

    Cases, each against the tool's own words: editing a template-written
    AGENTS.md section is refused, through the real commit hook too
    (tools/doc-lint-gate.sh, deny with the answers); CONTROLS -- editing the
    repository's own section, an engine refresh that records the new text
    in the same commit, and an edit with a kept entry recorded in the same
    commit all pass; editing an unedited tools/bootstrap.sh is refused."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_vendor_engine as pve
        import upstream_edits as ue
    finally:
        sys.path.pop(0)
    cases = []
    env = _fixture_git_env()
    with tempfile.TemporaryDirectory(prefix='precedent-template-edit-') as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        tpl_sec = '### Session start\n\n- Run the bootstrap first, every session, before work.'
        agents = ('# Agents\n\n' + tpl_sec + '\n\n## Our own section\n\n- Ours to word.\n')
        boot = '#!/bin/bash\necho template\n'
        (repo / 'tools').mkdir()
        for name in ('upstream_edits.py', 'precedent_vendor_engine.py', 'generated_blocks.py',
                     'doc-lint-gate.sh', 'doc_lint.py'):
            if (ROOT / 'tools' / name).is_file():
                shutil.copy2(ROOT / 'tools' / name, repo / 'tools' / name)
        (repo / 'AGENTS.md').write_text(agents, encoding='utf-8')
        (repo / 'tools' / 'bootstrap.sh').write_text(boot, encoding='utf-8')
        manifest = {'agents_md_sections_sha256': {'### Session start': pve._sha_text(tpl_sec)},
                    'template_instances_sha256': {
                        'tools/bootstrap.sh': hashlib.sha256(boot.encode()).hexdigest()}}
        mpath = repo / 'tools' / 'ENGINE_MANIFEST.json'
        mpath.write_text(json.dumps(manifest), encoding='utf-8')
        (repo / 'precedent.json').write_text('{}\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'installed')

        def staged(**files):
            g('reset', '-q', '--hard', 'HEAD')
            for rel, text in files.items():
                (repo / rel.replace('__', '/')).write_text(text, encoding='utf-8')
            g('add', '-A')
            return ue.staged_template_edits(repo)

        edited = agents.replace('every session, before work', 'every session')
        got = staged(**{'AGENTS.md': edited})
        cases.append(('editing a template-written section is refused, naming it',
                      len(got) == 1 and '"### Session start" is text the Precedent '
                      'template wrote, and this commit edits it' in got[0], got))
        hook_in = json.dumps({'tool_input': {'command': 'git commit -m x'}})
        r = subprocess.run(['bash', str(repo / 'tools' / 'doc-lint-gate.sh')],
                           input=hook_in, capture_output=True, text=True,
                           env={**env, 'CLAUDE_PROJECT_DIR': str(repo)}, cwd=str(repo))
        cases.append(('...and through the real commit hook: deny, with both answers',
                      '"deny"' in r.stdout and 'it belongs upstream' in r.stdout
                      and 'true only here' in r.stdout, (failure_detail(r.stdout, 500), failure_detail(r.stderr, 300))))
        got = staged(**{'AGENTS.md': agents.replace('Ours to word.', 'Ours, reworded.')})
        cases.append(('CONTROL: editing the repository\'s own section passes', got == [], got))
        m2 = dict(manifest, agents_md_sections_sha256={
            '### Session start': pve._sha_text(edited.split('\n\n## Our')[0].split('# Agents\n\n')[1])})
        got = staged(**{'AGENTS.md': edited, 'tools__ENGINE_MANIFEST.json': json.dumps(m2)})
        cases.append(('CONTROL: an engine refresh recording the new text in the same '
                      'commit passes', got == [], got))
        got = staged(**{'AGENTS.md': edited, 'precedent.json': json.dumps(
            {'kept_template_divergences': {'AGENTS.md ### Session start': {
                'reason': 'we run it only on the web'}}})})
        cases.append(('CONTROL: an edit with a kept entry recorded in the same commit '
                      'passes', got == [], got))
        got = staged(**{'tools__bootstrap.sh': boot + 'echo ours\n'})
        cases.append(('editing the template\'s tools/bootstrap.sh is refused',
                      len(got) == 1 and 'tools/bootstrap.sh is the Precedent template' in got[0],
                      got))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {str(d)[:600]}' for n, d in bad))


def check_past_template_text_is_taken_over_a_stale_record():
    """A section or template copy identical to a past version of its
    template is taken, whatever hash the manifest records for it. 2026-10-17,
    a consuming repo's Update Vendors: AGENTS.md "### Merging a thread
    branch" carried the loader template's own earlier step 0b word for word,
    but its recorded hash did not match, so the plan said 'diverged' without
    looking at the template's history and the run stopped LEFT FOR YOU on a
    call the person had already made (take upstream; keep only what is the
    repo's own).

    Discriminating cases: the stale record must now plan 'adopt' (the fix);
    a matching record still plans 'refresh'; text no template ever had still
    plans 'diverged'; and a section precedent.json records as kept on
    purpose stays 'diverged', so the fix never overwrites a decision. The
    same four for tools/bootstrap.sh, whose plan had the same order."""
    import precedent_vendor_engine as pve
    cases = []
    tmp = pathlib.Path(_tempfile_for_env.mkdtemp(prefix='precedent-stale-record-'))
    try:
        key = '### Merging a thread branch'
        old = f'{key}\n\n0b. There is no local check-in mirror yet.'
        new = f'{key}\n\n0b. Send it with tools/checkin.py push.'
        tpl = tmp / 'tpl'
        (tpl / 'templates').mkdir(parents=True)
        (tpl / 'templates/AGENTS.md.loader.template').write_text(
            f'# AGENTS\n\n{new}\n', encoding='utf-8')
        (tpl / pve._AGENTS_MD_HISTORY_NAME).write_text(
            json.dumps({key: [old, new]}), encoding='utf-8')
        boot_old, boot_new = '#!/bin/sh\necho old\n', '#!/bin/sh\necho new\n'
        (tpl / 'templates/bootstrap.sh').write_text(boot_new, encoding='utf-8')
        (tpl / pve._TEMPLATE_HISTORY_NAME).write_text(json.dumps(
            {'templates/bootstrap.sh': [pve._git_blob_id(boot_old.encode()),
                                        pve._git_blob_id(boot_new.encode())]}),
            encoding='utf-8')

        def plan(name, section, boot, record, kept=False):
            c = tmp / name
            (c / 'tools').mkdir(parents=True)
            (c / 'AGENTS.md').write_text(f'# AGENTS\n\n{section}\n',
                                         encoding='utf-8')
            (c / 'tools/bootstrap.sh').write_text(boot, encoding='utf-8')
            cfg = {'base_branch': 'main'}
            if kept:
                cfg[pve.KEPT_DIVERGENCES_KEY] = {
                    f'AGENTS.md {key}': {'reason': 'ours', 'template_sha256': 'x'},
                    'tools/bootstrap.sh': {'reason': 'ours', 'template_sha256': 'x'}}
            (c / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            manifest = {pve.AGENTS_MD_SECTIONS_KEY: {key: record(section)},
                        pve.TEMPLATE_INSTANCES_KEY: {
                            'tools/bootstrap.sh': record(boot, file=True)}}
            a = [p[3] for p in pve._agents_md_plan(c, 'consumer', tpl, manifest)
                 if p[0] == key]
            b = [p[2] for p in pve._template_instance_plan(c, 'consumer', tpl,
                                                            manifest)]
            return a, b

        def stale(text, file=False):
            return '0' * 64

        def matching(text, file=False):
            if file:
                return hashlib.sha256(text.encode()).hexdigest()
            return pve._sha_text(text)

        got = plan('control', old, boot_old, matching)
        cases.append(('CONTROL: a past version matching its record is refreshed',
                      got == (['refresh'], ['refresh']), got))
        got = plan('stale', old, boot_old, stale)
        cases.append(('THE FIX: a past version under a stale record is adopted',
                      got == (['adopt'], ['adopt']), got))
        got = plan('own', f'{key}\n\nOur own words.', '#!/bin/sh\necho ours\n',
                   stale)
        cases.append(('text no template version had is still diverged',
                      got == (['diverged'], ['diverged']), got))
        got = plan('kept', old, boot_old, stale, kept=True)
        cases.append(('a past version recorded as kept on purpose stays diverged',
                      got == (['diverged'], ['diverged']), got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n}: got {d}' for n, ok, d in cases if not ok]
    check('a past template version is taken over a stale recorded hash',
          not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_kept_bootstrap_divergence_is_recorded():
    """tools/bootstrap.sh, on the same terms as the AGENTS.md check above.
    The measured case, 2026-09-28: a consumer's copy was the template plus
    one package on the pip line, reported LEFT FOR YOU on every update.
    Recorded against the template's hash it is DONE; when the template
    changes it is listed again."""
    fx = _KeptDivergenceFixture('precedent-kept-bootstrap-')
    pve = fx.pve
    cases = []
    rel = 'tools/bootstrap.sh'
    try:
        tpl = fx.template(fx.BOOT_SRC)
        # Found, not quoted: the template's package list changes (markdown
        # joined it on 2026-10-01), and so does where pip's error goes (a
        # file the warning quotes, 2026-10-05); either broke a quoted line.
        pips = re.findall(rb'pip install --quiet [\w ]+?(?= 2>)', tpl)
        assert len(pips) == 1, 'template pip line moved; repoint this fixture'
        ours = tpl.replace(pips[0], pips[0] + b' pyyaml')
        sha_now = hashlib.sha256(tpl).hexdigest()

        repo = fx.consumer('kept', boot=ours)
        rc, out = fx.update(repo)
        cases.append(('CONTROL: unrecorded, the one-line difference is LEFT FOR '
                      'YOU, exit 1, with the hash to record it with',
                      rc == 1 and f'{rel}: diverged' in out and sha_now in out,
                      failure_detail(out, 1500)))

        fx.keep(repo, rel, 'our scripts import yaml', sha_now)
        fx.judge(repo, rel, [t for _n, t, _h in fx.pve.missing_template_blocks(
            ours.decode(), tpl.decode())])
        rc, out = fx.update(repo)
        cases.append(('THE FIX: recorded with a reason, the next update is DONE, '
                      'exit 0, and names it once as kept on purpose',
                      rc == 0 and 'DONE' in out and 'LEFT FOR YOU' not in out
                      and 'our scripts import yaml' in out, failure_detail(out, 1500)))
        cases.append(('...and the file keeps its own line',
                      (repo / rel).read_bytes() == ours, ''))

        tail = b'# A bootstrap that blocks startup'
        assert tpl.count(tail) == 1, 'template tail moved; repoint this fixture'
        moved = tpl.replace(tail, b'# FIXTURE BLOCK ADDED UPSTREAM\n'
                                  b'python3 tools/fixture_probe.py || true\n\n' + tail)
        rc, out = fx.update(repo, fx.upstream_with(fx.BOOT_SRC, moved))
        cases.append(('once upstream changes the template, it is LEFT FOR YOU '
                      'again, naming the new block and the new hash',
                      rc == 1 and f'{rel}: diverged' in out
                      and 'FIXTURE BLOCK ADDED UPSTREAM' in out
                      and hashlib.sha256(moved).hexdigest() in out, failure_detail(out, 1500)))
    finally:
        fx.close()

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a tools/bootstrap.sh kept on purpose is recorded once and Update '
          f'Vendors finishes, until upstream changes the template '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:1500]}" for n, d in bad))


def check_legacy_bootstrap_shim_is_replaced():
    """A pre-Precedent tools/bootstrap.sh that only wraps
    process/upstream/tools/bootstrap.sh runs BestPractice's OWN bootstrap,
    not the template. It was reported as a diverged copy lacking every
    template block, and step 10(d) forbade the one correct fix, replacing
    it. Now a pure shim is replaced with the template, and the report says
    so; a shim carrying lines of its own is never replaced (practice:
    repair-cannot-discard-work) -- the NEGATIVE case, which is also what
    shows the replacement comes from recognising the shim, not from
    replacing every diverged copy."""
    fx = _KeptDivergenceFixture('precedent-legacy-shim-')
    cases = []
    rel = 'tools/bootstrap.sh'
    shim = (b'#!/bin/bash\n'
            b'# Host shim (practice: engine-plus-host-shims): the logic lives\n'
            b'# in the vendored upstream tree.\n'
            b'set -euo pipefail\n'
            b'cd "$(dirname "$0")/.."\n'
            b'exec bash process/upstream/tools/bootstrap.sh "$@"\n')
    try:
        tpl = fx.template(fx.BOOT_SRC)
        repo = fx.consumer('shim', boot=shim)
        rc, out = fx.update(repo)
        cases.append(('a pure legacy shim is replaced with the template',
                      (repo / rel).read_bytes() == tpl, failure_detail(out, 1500)))
        cases.append(('...the update says so, and finishes: exit 0, DONE',
                      rc == 0 and 'DONE' in out and 'replaced: ' + rel in out
                      and 'process/upstream/tools/bootstrap.sh' in out, failure_detail(out, 1500)))

        own = shim.replace(b'exec bash', b'pip install --quiet pyyaml\nexec bash')
        kept = fx.consumer('shim-with-own-line', boot=own)
        rc, out = fx.update(kept)
        cases.append(('NEGATIVE: a shim with a line of its own is left alone, '
                      'LEFT FOR YOU, and named as the old wrapper',
                      rc == 1 and (kept / rel).read_bytes() == own
                      and "the old install's wrapper" in out, failure_detail(out, 1500)))
    finally:
        fx.close()

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a legacy tools/bootstrap.sh shim around upstream\'s own bootstrap is '
          f'recognised and replaced with the template ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:1500]}" for n, d in bad))

def check_answer_first_gate_holds_a_change_until_the_question_is_answered():
    """A change waits until the person's question has an answer in words
    (answer-first-ask-before-long-work; Morgan, 2026-10-17: "if I ask a
    question, you answer it BEFORE you implement a change ... Make that
    change enforcement stronger"). That day his message approved a landing
    and asked for a workflow change's details; the session wrote "Landing
    first, since you approved it." and landed. The gate, through the fixed
    precedent-hooks.sh entry: a commit, push, merge, landing, edit outside
    /tmp or GitHub write is refused while his latest message (typed, or
    sent mid-turn) asks something and fewer than 50 words have answered
    it; reading never is; a message that asks nothing holds nothing."""
    import tempfile, json as _json
    name = 'the answer-first gate holds a change until the question is answered'
    gate = ROOT / 'tools' / 'answer-first-gate.sh'
    if not gate.exists():
        not_applicable(name, 'tools/answer-first-gate.sh is absent')
        return
    cases = []

    def human(text, queued=False):
        if queued:
            return {'type': 'attachment', 'attachment': {
                'type': 'queued_command', 'prompt': text,
                'origin': {'kind': 'human'}}}
        return {'type': 'user', 'origin': {'kind': 'human'},
                'message': {'role': 'user', 'content': text}}

    def said(text):
        return {'type': 'assistant', 'message': {'role': 'assistant',
                'content': [{'type': 'text', 'text': text}]}}

    notice = {'type': 'user', 'origin': {'kind': 'task-notification'},
              'message': {'role': 'user', 'content': 'a job finished?'}}
    answer = said(' '.join(['word'] * 60))

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def run(records, tool='Bash', tool_input=None, via_hooks=False):
            tr = tmp / 'transcript.jsonl'
            tr.write_text(''.join(_json.dumps(r) + '\n' for r in records),
                          encoding='utf-8')
            payload = _json.dumps({
                'tool_name': tool, 'transcript_path': str(tr),
                'tool_input': tool_input if tool_input is not None
                else {'command': 'git push -u origin HEAD'}})
            argv = (['python3', str(ROOT / 'tools' / 'precedent_hooks.py'),
                     'PreToolUse'] if via_hooks else ['bash', str(gate)])
            p = subprocess.run(argv, input=payload, capture_output=True,
                               text=True, cwd=ROOT)
            return p.returncode, p.stdout + p.stderr

        asked = human('approved. On the workflow change - give me the details, I missed it.')
        rc, out = run([asked, said('Landing first, since you approved it.')])
        cases.append(('a push after "Landing first" with the question open is '
                      'refused, quoting it', rc == 2 and 'ANSWER FIRST' in out
                      and 'give me the details' in out, failure_detail(out, 200)))
        rc, out = run([asked, answer])
        cases.append(('once answered, the push goes through', rc == 0, failure_detail(out, 200)))
        rc, _ = run([human('yes to both, and booked')])
        cases.append(('a message that asks nothing holds nothing', rc == 0))
        rc, _ = run([human('yes to both'), answer,
                     human('why did main go red?', queued=True)])
        cases.append(('a question sent mid-turn holds the next change',
                      rc == 2))
        # 2026-10-20: a seeded prompt full of regex had the first file write
        # of the session it started refused, its question marks read as
        # questions (todo/todo-2026-10-20-root-issues-from-ladder-landing-check.md,
        # item 3).
        rc, _ = run([human('Port the anchor `(?<=\\bthen\\s)(?:land|merge)` '
                           'and the suffix:\n```\n(?![^()\\n]*\\))\n```\nThen push.')])
        cases.append(('question marks in code spans and fenced blocks are not '
                      'questions', rc == 0))
        rc, _ = run([human('Anchor the trigger with (?<=\\bthen\\s) and push.')])
        cases.append(('a regex group opening "(?" is not a question', rc == 0))
        rc, _ = run([human('Sent automatically by the session "X" -- '
                           'https://claude.ai/code/session_01X. Nobody typed this.\n'
                           'For: a new session.\nGive me the details in the todo '
                           'item, then fix it. Why it broke?')])
        cases.append(('a seeded handoff, opening with its origin line, holds nothing',
                      rc == 0))
        rc, _ = run([human('Is `x?` the cause? Explain.')])
        cases.append(('NEGATIVE CONTROL: a real question beside a code span still '
                      'holds', rc == 2))
        rc, _ = run([asked, notice])
        cases.append(('a notice is not the person: their question still holds',
                      rc == 2))
        rc, _ = run([asked], tool_input={'command': 'grep -rn push tools/'})
        cases.append(('reading is never held', rc == 0))
        # A path outside /tmp whatever ROOT is: a checkout under /tmp (a
        # worktree a landing's background run makes, 2026-10-31) made
        # ROOT/README.md read as scratch, and this case failed there only.
        rc, _ = run([asked], tool='Edit',
                    tool_input={'file_path': '/srv/precedent-fixture/README.md'})
        cases.append(('an edit to the work is held', rc == 2))
        rc, _ = run([asked], tool='Edit',
                    tool_input={'file_path': '/tmp/scratch/notes.md'})
        cases.append(('an edit to scratch under /tmp is not', rc == 0))
        rc, _ = run([asked], tool='mcp__github__merge_pull_request',
                    tool_input={'pullNumber': 1})
        cases.append(('a pull request merged on GitHub is held', rc == 2))
        # 2026-10-20 (Morgan: "Can you make the enforcement of that
        # stronger?"): the session rebuilt and published the branch page
        # for its archive line before answering a plain question.
        rc, out = run([asked], tool='Artifact',
                      tool_input={'file_path': '/tmp/x/page.html',
                                  'url': 'https://claude.ai/artifact/x'})
        cases.append(('an Artifact publish is held', rc == 2
                      and 'ANSWER FIRST' in out, failure_detail(out, 200)))
        rc, _ = run([asked], tool='Artifact',
                    tool_input={'action': 'read',
                                'url': 'https://claude.ai/artifact/x'})
        cases.append(('an Artifact read is not', rc == 0))
        rc, out = run([asked], tool_input={
            'command': 'python3 tools/precedent_stale_branches.py --fetch '
                       '--html /tmp/x/branch-cleanup.html'})
        cases.append(('building the branch page is held', rc == 2
                      and 'ANSWER FIRST' in out, failure_detail(out, 200)))
        rc, out = run([asked], tool='Artifact', via_hooks=True,
                      tool_input={'file_path': '/tmp/x/page.html'})
        cases.append(('an Artifact publish is held through the fixed '
                      'precedent-hooks.sh entry', rc == 2
                      and 'ANSWER FIRST' in out, failure_detail(out, 200)))
        rc, out = run([asked, said('Landing first.')], via_hooks=True)
        cases.append(('it runs through the fixed precedent-hooks.sh entry '
                      '(tools/hook_wiring.json)', rc == 2 and 'ANSWER FIRST' in out,
                      failure_detail(out, 200)))

        # 2026-10-18: Claude Code records a message -- its text and the tool
        # call it ends in -- after PreToolUse runs, so the answer written
        # with the guarded call is not there on the first read. A session
        # answered in about a hundred words; the gate counted 11 and refused
        # its merge three times.
        def call(tid):
            return {'type': 'assistant', 'message': {'role': 'assistant',
                    'content': [{'type': 'tool_use', 'id': tid,
                                 'name': 'Bash', 'input': {}}]}}

        def run_late(records, tid, late, delay=0.5):
            tr = tmp / 'transcript.jsonl'
            tr.write_text(''.join(_json.dumps(r) + '\n' for r in records),
                          encoding='utf-8')
            proc = subprocess.Popen(['bash', str(gate)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, cwd=ROOT)
            proc.stdin.write(_json.dumps({
                'tool_name': 'Bash', 'transcript_path': str(tr),
                'tool_use_id': tid,
                'tool_input': {'command': 'git push -u origin HEAD'}}))
            proc.stdin.close()
            time.sleep(delay)
            with tr.open('a', encoding='utf-8') as fh:
                fh.write(''.join(_json.dumps(r) + '\n' for r in late))
            out = proc.stdout.read() + proc.stderr.read()
            return proc.wait(), out

        short = said('Short answer.')
        rc, out = run_late([asked, short], 'toolu_late',
                           [answer, call('toolu_late')])
        cases.append(('an answer recorded with the guarded call after the '
                      'gate first reads still counts', rc == 0, failure_detail(out, 200)))
        rc, out = run_late([asked, short], 'toolu_never', [], delay=0)
        cases.append(('a transcript that never records the guarded call lets '
                      'it through, saying so', rc == 0
                      and 'has not recorded toolu_never' in out, failure_detail(out, 200)))
        rc, out = run_late([asked, short, call('toolu_here')], 'toolu_here', [],
                           delay=0)
        cases.append(('once the guarded call is recorded, a short answer is '
                      'still refused', rc == 2 and 'ANSWER FIRST' in out,
                      failure_detail(out, 200)))
        # 2026-10-19 (Morgan: "okay, go fix"): a mid-turn answer of about
        # 45 words or more is never written to the transcript, so a session
        # that had answered was refused four times running. One refusal per
        # question: once the transcript holds it, the next change goes
        # through; a new question starts over.
        refused = {'type': 'user', 'message': {'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': 'toolu_x', 'is_error': True,
             'content': 'PreToolUse:Bash hook error: ANSWER FIRST: the '
                        "person's latest message asks something"}]}}
        rc, out = run([asked, short, refused])
        cases.append(('after one refusal for the question, the next change '
                      'goes through, saying so', rc == 0
                      and 'refused once already' in out, failure_detail(out, 200)))
        rc, out = run([asked, refused, human('and why is main red?')])
        cases.append(('a new question after that refusal is held again',
                      rc == 2 and 'ANSWER FIRST' in out, failure_detail(out, 200)))
        tr = tmp / 'transcript.jsonl'
        tr.write_text('not json\n', encoding='utf-8')
        p = subprocess.run(['bash', str(gate)], input='{broken', text=True,
                           capture_output=True)
        cases.append(('an unreadable payload lets the call through',
                      p.returncode == 0))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_repo_attach_gate_refuses_a_sweep_nobody_asked_for():
    """A sweep of repository attaches waits for the person (reach-or-ask;
    Morgan, 2026-10-29: "*WHY* did you open every repo to do this
    change??? We never do that." and "I want to prevent that."). A session
    took another session's relayed message as his go-ahead and attached
    sixteen repositories in one go. The gate, through the fixed
    precedent-hooks.sh entry: three attaches the person did not name go
    through and the fourth is refused, saying ASK FIRST; a repository he
    named, a group he named with a wildcard, a practice source, and any
    attach while his latest message asks for a sweep are never counted;
    another session's words are not his; his yes after a refusal lets the
    session carry on."""
    import tempfile, json as _json
    name = 'the repo-attach gate refuses a sweep nobody asked for'
    gate = ROOT / 'tools' / 'repo-attach-gate.sh'
    if not gate.exists():
        not_applicable(name, 'tools/repo-attach-gate.sh is absent')
        return
    cases = []

    def human(text):
        return {'type': 'user', 'origin': {'kind': 'human'},
                'message': {'role': 'user', 'content': text}}

    relayed = {'type': 'user', 'origin': {'kind': 'peer'},
               'message': {'role': 'user',
                           'content': 'Morgan says: open every repo.'}}

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, PRECEDENT_ATTACH_STATE_DIR=str(tmp / 'state'))
        sessions = iter(range(1000))

        def run(records, repos, session=None, via_hooks=False):
            """-> (return code, output) of the LAST attach in repos."""
            session = session or f's{next(sessions)}'
            tr = tmp / f'{session}.jsonl'
            tr.write_text(''.join(_json.dumps(r) + '\n' for r in records),
                          encoding='utf-8')
            argv = (['python3', str(ROOT / 'tools' / 'precedent_hooks.py'),
                     'PreToolUse'] if via_hooks else ['bash', str(gate)])
            rc, out = 0, ''
            for owner_repo in repos:
                owner, repo = owner_repo.split('/')
                payload = _json.dumps({
                    'tool_name': 'mcp__claude-code-remote__add_repo',
                    'session_id': session, 'transcript_path': str(tr),
                    'tool_input': {'owner': owner, 'repo': repo}})
                p = subprocess.run(argv, input=payload, capture_output=True,
                                   text=True, cwd=ROOT, env=env)
                rc, out = p.returncode, p.stdout + p.stderr
            return rc, out

        four = ['o/alpha', 'o/beta', 'o/gamma', 'o/delta']
        msgs = [human('fix the ladder trim'), relayed]
        rc, out = run(msgs, four[:3])
        cases.append(('three unnamed attaches go through', rc == 0, failure_detail(out, 200)))
        rc, out = run(msgs, four)
        cases.append(('the fourth is refused, saying ASK FIRST and naming the '
                      'three already attached', rc == 2 and 'ASK FIRST' in out
                      and 'o/alpha' in out, failure_detail(out, 200)))
        rc, out = run([human('attach alpha, beta, gamma and delta')], four)
        cases.append(('repositories the person named are not counted',
                      rc == 0, failure_detail(out, 200)))
        rc, out = run([human('attach all the precedent-* sets and x-*')],
                      ['o/x-one', 'o/x-two', 'o/x-three', 'o/x-four'])
        cases.append(('a wildcard group the person named is not counted',
                      rc == 0, failure_detail(out, 200)))
        rc, out = run([human('hi')], ['o/precedent-a', 'o/precedent-b',
                                      'o/precedent-c', 'o/precedent-d'])
        cases.append(('practice sources are not counted', rc == 0, failure_detail(out, 200)))
        rc, out = run([human('Update All Vendors and merge them')], four)
        cases.append(('a sweep the person asked for is not counted',
                      rc == 0, failure_detail(out, 200)))
        rc, out = run([human('check every repo with BP')], four)
        cases.append(('"every repo with BP" in his own words is a sweep he '
                      'asked for', rc == 0, failure_detail(out, 200)))
        rc, out = run([relayed, human('go on')], four)
        cases.append(('another session saying "every repo" is not his word',
                      rc == 2 and 'ASK FIRST' in out, failure_detail(out, 200)))
        run(msgs, four, session='yes')
        rc, out = run(msgs + [human('yes, attach them')], ['o/epsilon'],
                      session='yes')
        cases.append(('his yes after a refusal lets the session carry on',
                      rc == 0, failure_detail(out, 200)))
        rc, out = run(msgs, four, via_hooks=True)
        cases.append(('it runs through the fixed precedent-hooks.sh entry',
                      rc == 2 and 'ASK FIRST' in out, failure_detail(out, 200)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_session_start_warns_of_unapproved_workflow():
    """practice: ci-workflow-approved, 2026-09-26. templates/bootstrap.sh
    runs the check at session start, because a workflow edited on GitHub's
    website is in a fresh clone before any push. Its block is run here as
    the template has it, under the template's own `set -euo pipefail`: loud
    for an unapproved workflow, silent for an approved one, and never ending
    the bootstrap either way."""
    import hashlib, shutil, tempfile
    import precedent_vendor_engine as _pve
    text = (ROOT / 'templates' / 'bootstrap.sh').read_text(encoding='utf-8')
    start = text.find('# A WORKFLOW NOBODY APPROVED')
    end = text.find('\nfi\n', start)
    block = text[start:end + 4] if start >= 0 and end > 0 else ''
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-wf-sessionstart-'))
    rel = '.github/workflows/light-check.yml'
    body = 'name: Light check\non:\n  pull_request:\n    branches: [main]\n'
    cases = [('the template carries the block', bool(block))]
    try:
        def run(approve):
            c = tmp / ('approved' if approve else 'unapproved')
            (c / 'tools').mkdir(parents=True)
            (c / '.github' / 'workflows').mkdir(parents=True)
            for n in _pve.KINDS['consumer']:
                if n.endswith('.py') and (ROOT / 'tools' / n).is_file():
                    shutil.copy2(ROOT / 'tools' / n, c / 'tools' / n)
            (c / rel).write_text(body)
            (c / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
                {'kind': 'consumer', 'files': [], 'sha256': {},
                 'ci_workflow_files': [], 'ci_workflows_sha256': {}}))
            cfg = {'sources': []}
            if approve:
                cfg['github_ci_approved'] = {rel: {
                    'sha256': hashlib.sha256(body.encode()).hexdigest(),
                    'approved_by': 'Morgan, 2026-09-26: "keep it"'}}
            (c / 'precedent.json').write_text(json.dumps(cfg))
            script = 'set -euo pipefail\n' + block + '\necho REACHED-END\n'
            p = subprocess.run(['bash', '-c', script], cwd=str(c),
                               capture_output=True, text=True, timeout=120)
            return p.stdout + p.stderr
        loud, quiet = run(False), run(True)
        cases += [
            ('an unapproved workflow prints the WARNING naming the file',
             'WARNING: a GitHub Actions workflow here has no approval' in loud
             and rel in loud),
            ('...and the bootstrap still runs to the end', 'REACHED-END' in loud),
            ('CONTROL: an approved workflow prints nothing but the end',
             quiet.strip() == 'REACHED-END'),
        ]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] for c in cases if not c[1]]
    check(f'session start warns of an unapproved workflow, stays silent for '
          f'an approved one, and never ends the bootstrap '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_source_shape_is_verified():
    """A source is checked for the shape its skeleton defines, and for the
    shape its CONSUMERS need.

    precedent_bootstrap_source.py only ever ran for sources it created. A
    source migrated into place -- assembled by hand from an older system --
    never passed through it, and nothing afterwards asked whether it came
    out right. Both of this project's migrated sets were missing a skeleton
    file, and had been since migration (2026-09-06).

    File presence alone was the first version and was not enough: an
    approvers.json with no approvers, or an approver with no `github`, is
    present and useless -- build_codeowners.py refuses exactly those, so a
    source carrying one is already broken and has only not been run against
    yet. "Well-formed" is defined here by what a real consumer of the file
    needs, never by a wish list."""
    import importlib.util, tempfile, shutil, json as _json
    spec = importlib.util.spec_from_file_location(
        '_bss', ROOT / 'tools' / 'precedent_bootstrap_source.py')
    bss = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bss)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        def fixture(level, **edits):
            d = pathlib.Path(td) / f'src{len(cases)}{level}{len(edits)}'
            shutil.copytree(ROOT / 'templates' / f"practice-set-{ {'team': 'shared'}.get(level, level) }", d)
            (d / 'practices').mkdir(exist_ok=True)
            (d / 'practices' / 'x.md').write_text('---\nslug: x\n---\n## Rule\nx\n',
                                                  encoding='utf-8')
            if level == 'team':
                (d / 'approvers.json').write_text(_json.dumps(
                    {'approvers': [{'name': 'A', 'github': 'a'}]}), encoding='utf-8')
                (d / 'approvers.json.template').unlink(missing_ok=True)
            else:
                (d / 'config.json.sample').write_text(_json.dumps(
                    {'individual': {'name': 'n', 'path': '/p'}}), encoding='utf-8')
            (d / 'leak-blocklist.txt').write_text('# blank\n', encoding='utf-8')
            # The skeleton's README is full of {{PLACEHOLDER}}s by design;
            # bootstrap fills them. A fixture standing in for a FINISHED
            # source has to fill them too -- verify() caught this fixture
            # itself the first time it ran, which is the check working.
            (d / 'README.md').write_text('# A finished set\n', encoding='utf-8')
            # The two session hooks live in the harness adapter, not in
            # either skeleton (one copy per level would drift, and
            # _copy_skeleton writes plain text, while a hook without its
            # executable bit silently never runs) -- so a fixture standing
            # in for a FINISHED source installs them the same way
            # bootstrap() does, rather than by copying a tree that was
            # never going to contain them.
            bss._install_session_hooks(d)
            # Same reasoning for the CI gates: they live in
            # templates/github-actions/, not in either skeleton, and
            # bootstrap() installs them. A fixture standing in for a
            # FINISHED source has them (a set that does not is reported,
            # which check_views_drift_gate_reaches_a_source_set asserts).
            bss._install_workflows(d)
            # And the universal-catalogue wiring, added 2026-09-13: the
            # declaration in the set's own precedent.json plus the
            # .gitignore line, both written by bootstrap(). A fixture
            # standing in for a FINISHED source has them, or the two
            # verify() rows that report a set which reads none of the
            # universal practices fire here and the "complete set is
            # well-formed" cases below stop meaning anything.
            # _install_session_hooks() above already wired the two
            # SessionStart steps, since they are in the settings payload it
            # writes.
            bss.ensure_universal_source(d)
            bss.ensure_precedent_gitignore(d)
            # And the set's own AGENTS.md with the loader markers, written
            # by bootstrap() since 2026-09-14 (a set without one fails its
            # own build_views.py). Written here without the generator run,
            # which a fixture with no tools/ cannot do.
            bss._write_instructions_and_views(d, level, 'a-fixture-set')
            for rel, text in edits.items():
                if text is None:
                    (d / rel).unlink(missing_ok=True)
                else:
                    (d / rel).write_text(text, encoding='utf-8')
            return d

        cases.append(('a complete shared set is well-formed',
                      bss.verify('team', fixture('team')) == []))
        cases.append(('a complete individual set is well-formed',
                      bss.verify('individual', fixture('individual')) == []))
        cases.append(('a set with no AGENTS.md is reported, naming what fails without it',
                      any('AGENTS.md' in f and 'build_views' in f for f in bss.verify(
                          'team', fixture('team', **{'AGENTS.md': None})))))
        cases.append(('an AGENTS.md without the loader markers is reported too',
                      any('BEGIN GENERATED' in f for f in bss.verify(
                          'team', fixture('team', **{'AGENTS.md': '# notes, no markers\n'})))))
        cases.append(('a source with no session hooks is reported -- they are '
                      'the one part of a source\'s shape that does not live '
                      'in the skeleton',
                      any('freshness-guard' in f for f in bss.verify(
                          'team', fixture('team',
                                          **{'.claude/hooks/freshness-guard.sh': None})))))
        # A source is free to keep its hooks somewhere other than where
        # bootstrap() writes them, as long as settings.json points at them:
        # what the shape check is really asking is whether the hook RUNS.
        # A real one does exactly this (its hooks live in bootstrap/), and
        # the literal-path check reported that working source as broken.
        _relocated = fixture('team', **{'.claude/hooks/freshness-guard.sh': None})
        (_relocated / 'bootstrap').mkdir(exist_ok=True)
        (_relocated / 'bootstrap' / 'freshness-guard.sh').write_text('#!/bin/sh\n')
        # Every mode the adapter wires, not just session-start: this fixture
        # stands in for a FINISHED source, and a finished source wires all of
        # them -- the real set this is modelled on was measured wiring exactly
        # the adapter's three. Wiring one made it a stand-in for a source that
        # is correct about WHERE its hooks live and wrong about WHEN they run,
        # which is a different fixture with a different purpose. Derived
        # rather than listed so this does not become another copy of the
        # wiring that drifts (see
        # check_generator_wires_every_template_guard_mode).
        (_relocated / '.claude' / 'settings.json').write_text(_json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [
                {'type': 'command',
                 'command': f'$CLAUDE_PROJECT_DIR/bootstrap/freshness-guard.sh '
                            f'{_mode} main'}
                for _mode in sorted(bss._template_guard_modes())]}]}}))
        cases.append(('a session hook kept outside .claude/hooks/ but wired by '
                      'the source\'s own settings.json is NOT reported missing',
                      not any('freshness-guard' in f
                              for f in bss.verify('team', _relocated))))

        # The negative control for that leniency: wired at a path where
        # nothing is installed must still be reported, or the check above
        # would accept any settings.json that merely mentions the name.
        _dangling = fixture('team', **{'.claude/hooks/freshness-guard.sh': None})
        (_dangling / '.claude' / 'settings.json').write_text(_json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [{'type': 'command',
             'command': '$CLAUDE_PROJECT_DIR/bootstrap/freshness-guard.sh'}]}]}}))
        cases.append(('a hook wired at a path where no file exists is still '
                      'reported missing',
                      any('freshness-guard' in f
                          for f in bss.verify('team', _dangling))))

        cases.append(('a report names the harness adapter, not the skeleton, '
                      'for the files the skeleton has never shipped',
                      all('templates/harness/claude-code/hooks/' in f
                          for f in bss.verify('team', fixture(
                              'team', **{'.claude/hooks/commit-identity.sh': None}))
                          if 'commit-identity' in f)))

        cases.append(('a missing skeleton file is reported',
                      any('leak-blocklist' in f for f in bss.verify(
                          'team', fixture('team', **{'leak-blocklist.txt': None})))))
        cases.append(('an approvers.json with no approvers is reported -- '
                      'build_codeowners.py refuses exactly this',
                      any('no approvers' in f for f in bss.verify(
                          'team', fixture('team', **{'approvers.json':
                              _json.dumps({'approvers': []})})))))
        cases.append(('an approver with no github is reported',
                      any('"github"' in f for f in bss.verify(
                          'team', fixture('team', **{'approvers.json':
                              _json.dumps({'approvers': [{'name': 'A'}]})})))))
        cases.append(('an unfilled {{PLACEHOLDER}} is reported -- bootstrapped '
                      'and never finished',
                      any('unfilled' in f for f in bss.verify(
                          'team', fixture('team',
                                          **{'leak-blocklist.txt': 'a {{NAME}} b'})))))
        cases.append(('an individual config missing individual.path is reported',
                      any('individual.path' in f for f in bss.verify(
                          'individual', fixture('individual', **{'config.json.sample':
                              _json.dumps({'individual': {'name': 'n'}})})))))
        d = fixture('team')
        for f in (d / 'practices').glob('*.md'):
            f.unlink()
        cases.append(('a source with no practice files is reported',
                      any('no practice files' in x for x in bss.verify('team', d))))

    bad = [n for n, ok in cases if not ok]
    for n in bad:
        print(f"  source-shape case did not behave as stated: {n}")
    check(f'a source is verified for shape AND well-formedness '
          f'({len(cases)} stated cases)', not bad)


def check_deleted_set_is_not_an_unresolved_source():
    """A declared shared set whose repository is deleted is never counted as
    an unresolved or unverified source, and every tool that would have
    counted it says, in one line, that it is deleted and that Update Vendors
    removes it.

    WHY. 2026-10-09, a consumer after Update Vendors: session start skipped
    two deleted sets on purpose (precedent_source_bootstrap), and then the
    credentials check reported them as "did not resolve ... a credential IS
    set ... look at what git said", the freshness notice counted them in
    "NOT VERIFIED -- 2 source(s)", and the session blamed git and the proxy
    and cloned one by hand. Also: what git said for a real clone failure is
    kept and quoted, and the session check's row on a deleted set never
    tells it the set still holds rules or reads from a clone."""
    import tempfile, io
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr
    import precedent_source_credentials as _psc
    import precedent_engine_freshness as _pef
    import precedent_session_check as _psck
    cases = []
    try:
        eng = json.loads(_pr.ENGINE_DELETED_SETS.read_text(encoding='utf-8'))
        gone = (eng.get('sets') or [{}])[0].get('name')
    except (OSError, ValueError):
        gone = None
    if not gone:
        not_applicable('a deleted set is not an unresolved source',
                       'tools/deleted_sets.json lists no set to plant')
        sys.path.pop(0)
        return
    saved_env = {k: os.environ.get(k) for k in ('PRECEDENT_USER_CONFIG',)}
    saved_root = _psck.ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            repo, home = td / 'repo', td / 'home'
            repo.mkdir()
            ucfg = home / '.config' / 'precedent' / 'config.json'
            ucfg.parent.mkdir(parents=True)
            ucfg.write_text('{"format_version": 1}\n', encoding='utf-8')
            os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
            notes = td / 'notes.json'

            def declare(*names):
                (repo / 'precedent.json').write_text(json.dumps({
                    'format_version': 1, 'sources': [
                        {'level': 'universal', 'name': 'precedent', 'path': '.'}]
                    + [{'level': 'shared', 'name': n, 'path': f'../{n}'}
                       for n in names]}), encoding='utf-8')

            env = {'HOME': str(home), 'PRECEDENT_USER_CONFIG': str(ucfg),
                   'CLAUDE_CODE_REMOTE': 'true',
                   'PRECEDENT_CLONE_NOTES': str(notes)}
            declare(gone)
            why = _psc.unresolved_private_sources(repo, env=env)
            cases.append(('a declared deleted set is not unresolved',
                          not any(n == gone for _, n, _ in why), str(why)))
            verdict, msg = _psc.assess(repo, env=env)
            cases.append(('with nothing else missing the verdict is OK, with a '
                          'note that it is deleted and Update Vendors removes it',
                          verdict == 'ok' and f'{gone} is on the list of deleted sets' in msg
                          and 'Update Vendors removes it' in msg,
                          f'{verdict}: {msg}'))
            live = 'precedent-shared-live-fixture'
            declare(gone, live)
            notes.write_text(json.dumps({live: {
                'output': 'error: RPC failed; HTTP 429 curl 22 too many requests',
                'when': '2026-10-09T10:00:00-0300'}}), encoding='utf-8')
            verdict, msg = _psc.assess(repo, env={**env, _psc.TOKEN_ENV: 'tok'})
            named = msg.split('did not resolve (', 1)[-1].split(')', 1)[0]
            cases.append(('a real missing set still reads SET and is named; the '
                          'deleted one is not among the unresolved',
                          verdict == 'set' and live in named and gone not in named,
                          f'{verdict}: {msg}'))
            cases.append(('...the deleted one gets its note there too',
                          f'{gone} is on the list of deleted sets' in msg, msg))
            cases.append(('...and what git said when it last tried the real one '
                          'is quoted', 'HTTP 429' in msg, msg))

            declare(gone)
            out = io.StringIO()
            _pef.report(repo, quiet=True, out=out)
            text = out.getvalue()
            cases.append(('the freshness notice does not count a deleted set as '
                          'not verified, and says it is deleted',
                          'NOT VERIFIED' not in text and f'{gone} is on the list of deleted sets' in text,
                          text))
            rows = _pef.collect_targets(repo)
            cases.append(('...and has no row reading it as a source',
                          not any(gone in str(r.get('label')) for r in rows), str(rows)))

            _psck.ROOT = repo
            rows = _psck._retired_sources_rows()
            detail = rows[0][2] if rows else ''
            cases.append(('the session check says a deleted set is never cloned '
                          'by hand, and never that the update keeps it',
                          len(rows) == 1 and 'never cloned by hand' in detail
                          and 'when every rule it holds' not in detail, detail))
    finally:
        _psck.ROOT = saved_root
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a deleted set is never counted as an unresolved or unverified '
          f'source ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


def check_hook_changes_never_touch_dot_claude():
    """Nothing an engine change can do to a hook touches .claude/: every hook
    there is one permanent stub running tools/<its name>, HOOK_WIRING takes
    no new hook, and a hook added later runs through the fixed
    precedent-hooks.sh entries, combined into one answer.

    WHY. Morgan, 2026-10-07 (strength: decided): "It should no longer ask."
    Claude Code's auto mode holds any commit that changes .claude/ for the
    person's yes; the hook scripts had changed on 27 days in a month and
    settings.json on 9, so nearly every Update Vendors asked. Planted: the
    stubs are byte-identical and each runs its script, in BestPractice and
    from an installed copy; HOOK_WIRING is the frozen list; the dispatcher
    runs a listed hook for its tool only, leaves a declined one out, and
    combines a deny, a block, an exit 2, context and a timeout the way
    separate entries would have been read."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    import precedent_hooks as ph
    cases = []
    tdir = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
    stubs = sorted(tdir.glob('*.sh'))
    stub = stubs[0].read_bytes()
    cases.append(('every shipped hook is the one stub, byte for byte',
                  all(f.read_bytes() == stub for f in stubs)))
    cases.append(('each stub has its script in tools/, shipped with the engine',
                  all((ROOT / 'tools' / f.name).is_file()
                      and f.name in pve.HOOK_SCRIPT_FILES
                      and f.name in pve.ENGINE_FILES
                      and f.name in pve.CONSUMER_ENGINE_FILES for f in stubs)))
    mine = [f for f in (ROOT / '.claude' / 'hooks').glob('*.sh')
            if (tdir / f.name).is_file()
            and f.name not in ('reply-gate.sh', 'session-start.sh',
                               'stop-git-check.sh', 'stop-reply-check.sh')]
    cases.append(('BestPractice runs the same stubs',
                  bool(mine) and all(f.read_bytes() == stub for f in mine)))
    wired = {(ev, n) for k in pve.HOOK_WIRING.values() for ev, _m, n, _a in k}
    cases.append(('HOOK_WIRING takes no new hook: add it to tools/hook_wiring.json',
                  wired == HOOK_WIRING_FROZEN))
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'repo'
        (repo / 'tools').mkdir(parents=True)
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        for n in ('precedent_hooks.py', 'precedent-hooks.sh'):
            shutil.copy(ROOT / 'tools' / n, repo / 'tools' / n)
        shutil.copy(tdir / 'precedent-hooks.sh', repo / '.claude' / 'hooks' / 'precedent-hooks.sh')
        shutil.copy(tdir / 'wait-loop-gate.sh', repo / '.claude' / 'hooks' / 'wait-loop-gate.sh')
        shutil.copy(ROOT / 'tools' / 'wait-loop-gate.sh', repo / 'tools' / 'wait-loop-gate.sh')
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text('{"kind": "consumer"}')
        (repo / 'tools' / 'refuse.sh').write_text(
            'cat >/dev/null; echo \'{"hookSpecificOutput": {"hookEventName": '
            '"PreToolUse", "permissionDecision": "deny", '
            '"permissionDecisionReason": "planted refusal"}}\'\n')
        (repo / 'tools' / 'hook_wiring.json').write_text(json.dumps({'consumer': [
            {'event': 'PreToolUse', 'matcher': 'Bash', 'script': 'refuse.sh'}]}))

        def run(name, event_args, payload):
            r = subprocess.run(['bash', str(repo / '.claude' / 'hooks' / name), *event_args],
                               input=json.dumps(payload), capture_output=True, text=True,
                               env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
            return r.returncode, r.stdout, r.stderr
        rc, out, _e = run('wait-loop-gate.sh', [], {'tool_input': {'command': 'pgrep -f x'}})
        cases.append(('an installed stub runs its script from tools/',
                      rc == 0 and '"deny"' in out))
        rc, out, _e = run('precedent-hooks.sh', ['PreToolUse'], {'tool_name': 'Bash'})
        cases.append(('the dispatcher runs a listed hook for its tool',
                      rc == 0 and 'planted refusal' in out))
        rc, out, _e = run('precedent-hooks.sh', ['PreToolUse'], {'tool_name': 'Read'})
        cases.append(('...and not for another tool', rc == 0 and out == ''))
        rc, out, _e = run('precedent-hooks.sh', ['Stop'], {})
        cases.append(('...nor at another event', rc == 0 and out == ''))
        (repo / 'precedent.json').write_text(json.dumps(
            {'declined_adapters': [{'path': 'tools/refuse.sh', 'reason': 'x'}]}))
        rc, out, _e = run('precedent-hooks.sh', ['PreToolUse'], {'tool_name': 'Bash'})
        cases.append(('a declined hook does not run', rc == 0 and out == ''))
    deny = ('a', 0, json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny', 'permissionDecisionReason': 'no A'}}), '', False)
    allow = ('b', 0, json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
             'permissionDecision': 'allow', 'additionalContext': 'ctx B'}}), 'note B\n', False)
    rc, out, err = ph.combine('PreToolUse', [deny, allow])
    got = json.loads(out)['hookSpecificOutput']
    cases.append(('a deny wins over an allow, and context and notes are kept',
                  rc == 0 and got['permissionDecision'] == 'deny'
                  and got['permissionDecisionReason'] == 'no A'
                  and got['additionalContext'] == 'ctx B' and 'note B' in err))
    rc, out, err = ph.combine('PreToolUse', [allow])
    cases.append(('an allow alone is not passed on',
                  'permissionDecision' not in json.loads(out)['hookSpecificOutput']))
    rc, out, err = ph.combine('Stop', [('c', 2, '', 'stop: unpushed\n', False), allow])
    cases.append(('an exit 2 blocks, with its stderr', rc == 2 and 'unpushed' in err))
    rc, out, _e = ph.combine('Stop', [('d', 0, json.dumps({'decision': 'block',
                                                          'reason': 'no Boildown'}), '', False)])
    cases.append(('a block decision is passed on',
                  json.loads(out) == {'decision': 'block', 'reason': 'no Boildown'}))
    rc, out, _e = ph.combine('SessionStart', [('e', 0, 'plain context\n', '', False),
                                              ('f', 0, json.dumps({'hookSpecificOutput': {
                                                  'additionalContext': 'json context'}}), '', False)])
    cases.append(('plain stdout at SessionStart is context, joined with JSON context',
                  json.loads(out)['hookSpecificOutput']['additionalContext']
                  == 'plain context\n\njson context'))
    rc, out, err = ph.combine('PreToolUse', [('g', None, '', 'g ran past its 60s\n', True)])
    cases.append(('a hook past its timeout is a note, not a block',
                  rc == 0 and out == '' and 'past its' in err))
    bad = [n for n, ok in cases if not ok]
    check(f'a hook change never touches .claude/ ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_audit_says_where_a_moved_bootstrap_section_went():
    """The practice audit, finding a manifest section entry's marker missing
    from tools/bootstrap.sh and present in tools/bootstrap.local.sh, names
    that file and the local_path to set.

    THE INCIDENT (2026-10-10, a consumer). Its style-pack freshness line
    was moved into tools/bootstrap.local.sh when the engine's template took
    over tools/bootstrap.sh, and its manifest entry kept naming bootstrap.sh;
    the audit warned "section_marker not found" on every run, with no hint
    where the section went. The DISCRIMINATING CASE is the first. The second
    proves a marker found nowhere still gets the plain warning.
    The fixture owns its repository (fixture-owns-its-state)."""
    import shutil, tempfile
    cases = []
    marker = 'process/stylepack/tools/pack_sync.py fresh'
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)],
                       env=_fixture_git_env(), capture_output=True)
        (repo / 'tools').mkdir()
        for name in ('practice_audit.py', 'generated_blocks.py'):
            shutil.copy2(ROOT / 'tools' / name, repo / 'tools')
        (repo / 'tools' / 'bootstrap.sh').write_text('#!/bin/sh\nexit 0\n',
                                                    encoding='utf-8')
        (repo / 'process' / 'stylepack').mkdir(parents=True)

        def run(local_text):
            (repo / 'tools' / 'bootstrap.local.sh').write_text(local_text,
                                                              encoding='utf-8')
            (repo / 'process' / 'manifest_stylepack.json').write_text(json.dumps({
                'upstream': {'repo': 'example/pack', 'vendored_at': 'process/stylepack',
                             'scrub_blocklist': None},
                'entries': [{'practice': 'bootstrap-freshness-stylepack',
                             'upstream_path': 'templates/x.template',
                             'local_path': 'tools/bootstrap.sh',
                             'granularity': 'section', 'section_marker': marker,
                             'status': 'synced'}]}), encoding='utf-8')
            r = subprocess.run([sys.executable, 'tools/practice_audit.py'],
                               cwd=str(repo), capture_output=True, text=True,
                               env=_fixture_git_env())
            return [l for l in (r.stdout + r.stderr).splitlines()
                    if 'section_marker' in l]

        got = run(marker + ' 2>/dev/null || true\n')
        cases.append(('THE DISCRIMINATING CASE: the warning names '
                      'tools/bootstrap.local.sh and the local_path to set',
                      any('it is in tools/bootstrap.local.sh' in l
                          and 'local_path to tools/bootstrap.local.sh' in l
                          for l in got), got))
        got = run('echo nothing here\n')
        cases.append(('a marker found nowhere keeps the plain warning',
                      got and not any('bootstrap.local.sh' in l for l in got), got))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the audit says where a moved bootstrap section went '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_session_start_hook_runs_bootstrap_locally():
    """The Claude Code adapter's SessionStart hook runs tools/bootstrap.sh in
    a local session too, marked PRECEDENT_LOCAL_SESSION=1, and bootstrap.sh
    then skips only what belongs to a container.

    Until 2026-09-28 the hook exited unless CLAUDE_CODE_REMOTE=true, so a
    local Claude Code session got none of bootstrap.sh. Morgan approved
    running it locally, with the package install left out there. Planted: a
    bootstrap.sh that records it ran and what the variable said; an old one
    that never reads the variable (not run locally, since it would pip
    install); and both real bootstrap scripts with a fake pip and a fake
    commit-identity.sh on the path, run local and remote."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-local-session-'))
    hook = ROOT / 'tools' / 'session-start.sh'
    base = {k: v for k, v in os.environ.items()
            if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
    base['GIT_CEILING_DIRECTORIES'] = str(tmp)
    cases = []

    def run(script, cwd, **extra):
        return subprocess.run(['bash', str(script)], cwd=str(cwd),
                              env=dict(base, **extra), capture_output=True,
                              text=True, timeout=60)

    try:
        proj = tmp / 'proj'
        (proj / 'tools').mkdir(parents=True)
        record = tmp / 'ran.txt'
        (proj / 'tools' / 'bootstrap.sh').write_text(
            '#!/bin/bash\n'
            f'echo "ran local=${{PRECEDENT_LOCAL_SESSION:-unset}}" > "{record}"\n',
            encoding='utf-8')
        r = run(hook, proj, CLAUDE_PROJECT_DIR=str(proj))
        got = record.read_text(encoding='utf-8').strip() if record.exists() else ''
        cases.append(('with CLAUDE_CODE_REMOTE unset the hook runs bootstrap.sh, '
                      'with PRECEDENT_LOCAL_SESSION=1',
                      r.returncode == 0 and got == 'ran local=1',
                      f'rc={r.returncode} record={got!r} {failure_detail(r.stderr, 300)}'))
        record.unlink(missing_ok=True)
        r = run(hook, proj, CLAUDE_PROJECT_DIR=str(proj), CLAUDE_CODE_REMOTE='true')
        got = record.read_text(encoding='utf-8').strip() if record.exists() else ''
        cases.append(('...and a remote session runs it without the mark',
                      r.returncode == 0 and got == 'ran local=unset',
                      f'rc={r.returncode} record={got!r}'))

        old = tmp / 'old'
        (old / 'tools').mkdir(parents=True)
        (old / 'tools' / 'bootstrap.sh').write_text(
            f'#!/bin/bash\necho ran > "{record}"\n', encoding='utf-8')
        record.unlink(missing_ok=True)
        r = run(hook, old, CLAUDE_PROJECT_DIR=str(old))
        cases.append(('a bootstrap.sh that never reads the variable is not run '
                      'locally, and the hook says why without failing',
                      r.returncode == 0 and not record.exists()
                      and 'predates local sessions' in r.stderr,
                      f'rc={r.returncode} ran={record.exists()} {failure_detail(r.stderr, 300)}'))
        r = run(hook, old, CLAUDE_PROJECT_DIR=str(old), CLAUDE_CODE_REMOTE='true')
        cases.append(('...but still is on a remote session', record.exists(), ''))

        fakebin = tmp / 'bin'
        fakebin.mkdir()
        calls = tmp / 'calls.txt'
        (fakebin / 'pip').write_text(f'#!/bin/sh\necho pip >> "{calls}"\n',
                                     encoding='utf-8')
        os.chmod(fakebin / 'pip', 0o755)
        path = f'{fakebin}{os.pathsep}{base.get("PATH", "")}'
        for rel in ('templates/bootstrap.sh', 'tools/bootstrap.sh'):
            work = tmp / ('w-' + rel.replace('/', '-'))
            (work / '.claude' / 'hooks').mkdir(parents=True)
            (work / '.claude' / 'hooks' / 'commit-identity.sh').write_text(
                f'#!/bin/sh\necho identity >> "{calls}"\n', encoding='utf-8')
            # A copy inside the fixture, never ROOT's own: the script puts
            # its checkout's .precedent/python-bin first on PATH, and this
            # checkout's real one would shadow the fake pip
            # (practice: fixture-owns-its-state).
            (work / 'tools').mkdir()
            script = work / 'tools' / 'bootstrap.sh'
            shutil.copy2(ROOT / rel, script)
            for local in (True, False):
                calls.unlink(missing_ok=True)
                extra = {'PATH': path}
                if local:
                    extra['PRECEDENT_LOCAL_SESSION'] = '1'
                r = run(script, work, **extra)
                did = calls.read_text(encoding='utf-8').split() if calls.exists() else []
                if local:
                    cases.append((f'{rel}, local: no pip install and no '
                                  f'commit-identity.sh, and one line saying so',
                                  r.returncode == 0 and did == []
                                  and 'local session -- skipped pip install' in r.stderr,
                                  f'rc={r.returncode} calls={did} {failure_detail(r.stderr, 300)}'))
                else:
                    cases.append((f'{rel}, remote: both still run',
                                  r.returncode == 0 and did == ['pip', 'identity'],
                                  f'rc={r.returncode} calls={did} {failure_detail(r.stderr, 300)}'))
    except (OSError, subprocess.SubprocessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the SessionStart hook runs bootstrap.sh in a local session, minus '
          f'the container steps ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_harness_times_merge_without_a_conflict():
    """Two branches that each record a test, one of them deleting another,
    merge tools/harness_check_times.json with no conflict, and the deleted
    test stays deleted (2026-10-17). That day the file conflicted on nearly
    every merge -- one shared "measured" line every recording appended to,
    default_seconds rewritten each time, neighbouring inserts -- and a
    union resolve brought back five timings #1180 had removed, turning the
    --as-ci partition case red. Now: .gitattributes names a merge driver,
    session start configures it in the clone (precedent_session_check.py
    --merge-drivers, from session-start.sh and bootstrap.sh), and
    --record-new-times leaves the shared fields alone and drops a removed
    test's time itself. Fails on the old code: no driver, so git leaves
    the conflict."""
    import tempfile, json as _json, shutil as _shutil, re as _re
    name = 'the harness times file merges without a conflict'
    script = ROOT / 'tools' / 'harness_times_merge.py'
    boot = ROOT / 'tools' / 'bootstrap.sh'
    attrs = ROOT / '.gitattributes'
    cases = []
    attr_ok = attrs.is_file() and 'tools/harness_check_times.json merge=precedent-harness-times' \
        in attrs.read_text(encoding='utf-8')
    cases.append(('.gitattributes names the driver for the times file', attr_ok))
    # Configured at session start by BOTH harnesses (2026-10-18: only
    # bootstrap.sh did, and Claude Code never runs it).
    import precedent_session_check as _psc
    starts = [ROOT / '.claude' / 'hooks' / 'session-start.sh', boot]
    cases.append(('session-start.sh and bootstrap.sh both configure it',
                  script.is_file() and all(
                      f.is_file() and 'precedent_session_check.py --merge-drivers'
                      in f.read_text(encoding='utf-8') for f in starts),
                  'a session start that never calls --merge-drivers'))
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / 'r'
        env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_COMMITTER_NAME='T',
                   GIT_AUTHOR_EMAIL='t@example.invalid',
                   GIT_COMMITTER_EMAIL='t@example.invalid',
                   GIT_CONFIG_GLOBAL=str(pathlib.Path(td) / 'gc'),
                   GIT_CONFIG_NOSYSTEM='1')

        def git(*a, cwd=repo):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env)

        def times(seconds, measured='2026-10-09, 4 cores', default=0.3):
            (repo / 'tools' / 'harness_check_times.json').write_text(_json.dumps(
                {'about': 'x', 'measured': measured, 'default_seconds': default,
                 'seconds': dict(sorted(seconds.items()))}, indent=1) + '\n',
                encoding='utf-8')

        (repo / 'tools').mkdir(parents=True)
        git('init', '-q', '-b', 'main', str(repo), cwd=td)
        if script.is_file():
            _shutil.copy2(script, repo / 'tools' / script.name)
        if attrs.is_file():
            _shutil.copy2(attrs, repo / '.gitattributes')
        missing = _psc.missing_merge_drivers(repo)
        cases.append(('the session check reports the clone that lacks it '
                      f'(missing={missing})',
                      missing == ['precedent-harness-times']))
        _psc.configure_merge_drivers(repo)
        missing = _psc.missing_merge_drivers(repo)
        cases.append((f'...and --merge-drivers sets it (missing={missing})',
                      missing == []))
        base = {'check_a': 1.0, 'check_b': 2.0, 'check_c': 3.0}
        times(base)
        git('add', '-A')
        git('commit', '-q', '-m', 'base')
        git('checkout', '-q', '-b', 'ours')
        times({**base, 'check_ca': 4.0}, measured='2026-10-09, 4 cores; 1 added',
              default=0.5)
        git('commit', '-q', '-am', 'ours records check_ca')
        git('checkout', '-q', '-b', 'theirs', 'main')
        rest = {k: v for k, v in base.items() if k != 'check_c'}
        times({**rest, 'check_cb': 5.0}, measured='2026-10-09, 4 cores; 2 added',
              default=0.4)
        git('commit', '-q', '-am', 'theirs deletes check_c, records check_cb')
        git('checkout', '-q', 'ours')
        r = git('merge', '--no-edit', 'theirs')
        cases.append(('merging the two branches leaves no conflict', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 200)))
        try:
            got = _json.loads((repo / 'tools' / 'harness_check_times.json')
                              .read_text(encoding='utf-8'))['seconds']
        except (OSError, ValueError, KeyError):
            got = {}
        cases.append(('both new tests are kept, and the test one side deleted '
                      'stays deleted',
                      got == {'check_a': 1.0, 'check_b': 2.0, 'check_ca': 4.0,
                              'check_cb': 5.0}, str(got)))
        # A worktree shares the clone's config, as the stages' merges use.
        wt = pathlib.Path(td) / 'wt'
        git('branch', '-q', 'later', 'main')
        git('worktree', 'add', '-q', str(wt), 'later')
        (wt / 'tools' / 'harness_check_times.json').write_text(_json.dumps(
            {'about': 'x', 'measured': '2026-10-09, 4 cores', 'default_seconds': 0.3,
             'seconds': {**base, 'check_cc': 6.0}}, indent=1) + '\n', encoding='utf-8')
        git('commit', '-q', '-am', 'later records check_cc', cwd=wt)
        r = git('merge', '--no-edit', 'ours', cwd=wt)
        cases.append(('a merge in a worktree uses the same driver', r.returncode == 0,
                      failure_detail(r.stdout + r.stderr, 200)))
    path = pathlib.Path(tempfile.mkdtemp()) / 't.json'
    try:
        _write_check_times({'check_a': 9.0}, 'm', path=path, default=0.3)
        kept = _json.loads(path.read_text(encoding='utf-8')).get('default_seconds')
    except TypeError:
        kept = None
    finally:
        _shutil.rmtree(path.parent, ignore_errors=True)
    cases.append(('recording keeps default_seconds as recorded', kept == 0.3, str(kept)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_freshness_guard_writes_no_origin_into_a_repo_without_one():
    """The freshness guard widens a single-branch clone's refspec, and must
    leave a repository with NO origin exactly as it found it.

    THE INCIDENT (very deep check, 2026-10-17, pass 1). A fresh install has
    no origin until its first push, and INSTALL.md section 0 step 8 tells the
    person to give it one. The guard's `_widen_refspec` ran `git config --add
    remote.origin.fetch ...` unconditionally, which on such a repository
    creates a [remote "origin"] section with no URL -- after which the
    ordinary `git remote add origin URL` fails with "remote origin already
    exists". tools/bootstrap.sh had carried the same guard since 2026-09-14;
    the freshness guard did not. The positive control keeps the widening
    itself: a single-branch clone must still be widened."""
    import tempfile
    guard = ROOT / 'tools' / 'freshness-guard.sh'
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        env = {k: v for k, v in os.environ.items()
               if not k.startswith('PRECEDENT_')}

        def run_guard(repo):
            subprocess.run(['bash', str(guard), 'session-start', 'main'],
                           cwd=repo, input='', capture_output=True, text=True,
                           env={**env, 'CLAUDE_PROJECT_DIR': str(repo)},
                           timeout=120)

        bare_repo = tmp / 'no-origin'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(bare_repo))
        run_guard(bare_repo)
        remotes = fixture_git(bare_repo, 'config', '--get-regexp',
                              r'^remote\.', allow_failure=True).stdout.strip()
        cases.append((f'a repository with no origin gets no remote section '
                      f'(got {remotes!r})', not remotes))
        added = fixture_git(bare_repo, 'remote', 'add', 'origin',
                            str(tmp / 'somewhere.git'), allow_failure=True)
        cases.append(('`git remote add origin` still works afterwards',
                      added.returncode == 0))

        up = tmp / 'up'
        fixture_git(tmp, 'init', '-q', '-b', 'main', str(up))
        fixture_git(up, 'config', 'user.email', 'harness@example.com')
        fixture_git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('x\n')
        fixture_git(up, 'add', '-A')
        fixture_git(up, 'commit', '-qm', 'base')
        narrow = tmp / 'narrow'
        subprocess.run(['git', 'clone', '-q', '--single-branch', '--branch',
                        'main', f'file://{up}', str(narrow)],
                       capture_output=True, text=True)
        run_guard(narrow)
        spec = fixture_git(narrow, 'config', '--get-all',
                           'remote.origin.fetch').stdout
        cases.append(('a single-branch clone is still widened',
                      'refs/heads/*' in spec))

    failed = [n for n, ok in cases if not ok]
    check(f'the freshness guard writes no origin into a repository without '
          f'one, and still widens a single-branch clone ({len(cases)} cases)',
          not failed, '; '.join(failed) if failed else '')


