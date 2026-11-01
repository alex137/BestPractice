# The harness tests for the leak gate and outbound privacy
#
# tools/harness/vh_leak_and_privacy.py -- part of the verification harness:
# the leak gate and outbound privacy.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_leak_gate_fires():
    """The gate's own behaviour, as stated cases against a throwaway repo.

    WHY THIS EXISTS, AND WHY IT IS NOT A SECOND COPY OF THE GATE'S LOGIC.
    Running the gate on this tree (the pre-push hook, the push check and the
    leak-gate workflow all do; a harness check that did the same was retired
    2026-10-31) is a check on the TREE, not on the GATE -- it passes just as
    happily when the gate has stopped looking. Three real misses were found
    exactly there, each of which printed a confident "leak gate OK" on a push
    that would have published a private term:

      * a file added in one commit and removed in a later one in the same
        push, invisible to the net `git diff A..B` the gate used;
      * a leak in a STAGED blob, cleaned up in the working tree afterwards,
        because the gate read the file off disk rather than out of git;
      * a leak in a COMMIT MESSAGE, which was never scanned at all.

    So this check asserts what the gate is supposed to DO, from outside it:
    plant each case in a scratch repository, run the gate as a subprocess,
    and require the exit status. Every case here fails against the gate as it
    stood before those fixes. The blocked words are invented for this check --
    the whole point of the vocabulary layer is that a real list cannot live
    in this repo.
    """
    import shutil, tempfile

    def git(cwd, *args, check_rc=True):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-leakgate-'))
    try:
        repo = tmp / 'repo'
        (repo / 'tools').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'leak_gate.py', repo / 'tools' / 'leak_gate.py')
        # The default blocklist is a REQUIRED companion of the gate, not an
        # optional extra: load_default_blocklist() exits fatally without it,
        # deliberately, because a missing default would silently restore the
        # state where the vocabulary layer never runs. So anywhere the gate
        # is installed, this file goes too -- found by these fixtures going
        # red the moment the file was introduced, which is the guard working.
        shutil.copy(ROOT / 'tools' / 'leak-blocklist.default.txt',
                    repo / 'tools' / 'leak-blocklist.default.txt')
        blocklist = tmp / 'blocklist.txt'          # OUTSIDE the repo, as required
        blocklist.write_text('zorbulon\n\\bproject[- ]nightjar\\b\n', encoding='utf-8')
        scratch_home = tmp / 'home'                # see gate() below
        scratch_home.mkdir()

        git(repo, 'init', '-q')
        git(repo, 'config', 'user.email', 'harness@example.com')
        git(repo, 'config', 'user.name', 'harness')
        (repo / 'ok.md').write_text('nothing sensitive here\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'base')
        base = git(repo, 'rev-parse', 'HEAD')

        def gate(*args, blocklist_set=True):
            # HOME IS PART OF THE ABSENCE, not just the variable. Since
            # 2026-09-12 an unset PRECEDENT_LEAK_BLOCKLIST falls back to the
            # individual set named in ~/.config/precedent/config.json -- so a
            # fixture that only pops the variable inherits the CONTAINER's
            # real private list and asserts the opposite of what it ran
            # (practice: fixture-owns-its-state; the same shape cost an hour
            # on 2026-09-08 with three other variables). Pointing HOME at an
            # empty directory is what makes "no blocklist configured" true.
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
            env['HOME'] = str(scratch_home)
            if blocklist_set:
                env['PRECEDENT_LEAK_BLOCKLIST'] = str(blocklist)
            return subprocess.run(
                [sys.executable, str(repo / 'tools' / 'leak_gate.py'), *args],
                capture_output=True, text=True, cwd=str(repo), env=env).returncode

        cases = []

        # 1. a clean tree and a clean range must PASS -- a check that only ever
        #    fails is as useless as one that only ever passes.
        cases.append(('a clean tree passes', gate() == 0))
        cases.append(('a clean range passes', gate('--range', f'{base}..HEAD') == 0))

        # 2. a leak on disk
        (repo / 'leak.md').write_text('about Project Nightjar\n', encoding='utf-8')
        cases.append(('a blocked term in an untracked file fails', gate() == 1))
        (repo / 'leak.md').unlink()

        # 3. a leak added and then removed inside one push
        (repo / 'gone.md').write_text('about Project Nightjar\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'add')
        git(repo, 'rm', '-q', 'gone.md'); git(repo, 'commit', '-qm', 'remove')
        cases.append(('a term added then removed inside one push fails',
                      gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)

        # 4. a leak in the staged blob, cleaned in the working tree
        (repo / 'staged.md').write_text('about Project Nightjar\n', encoding='utf-8')
        git(repo, 'add', 'staged.md')
        (repo / 'staged.md').write_text('clean\n', encoding='utf-8')
        cases.append(('a term in a staged blob fails even when the file on disk is '
                      'clean', gate('--staged') == 1))
        git(repo, 'reset', '-q'); (repo / 'staged.md').unlink()

        # 5. a leak in a commit message
        git(repo, 'commit', '-q', '--allow-empty', '-m', 'work for Project Nightjar')
        cases.append(('a term in a commit message fails',
                      gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)

        # 6. structural rules still fire, and on a blob rather than a file
        # Assembled rather than written literally: spelled out, this fixture
        # would trip the gate's own home-directory rule on THIS file, and a
        # check that cannot be scanned by the gate it tests is a check that
        # gets deleted rather than fixed.
        home_path = '/' + 'Users/someone/notes'
        (repo / 'notes.md').write_text(f'see {home_path}\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'home path')
        (repo / 'notes.md').write_text('clean\n', encoding='utf-8')
        cases.append(('a structural rule fires on the committed blob, not the working '
                      'tree', gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)

        # 6b. structural PATH rules must be case-insensitive. Regression
        # case: the FORBIDDEN_PATHS regexes had no re.I, so a directory
        # named the way a person actually types it -- "Individual/",
        # "Candidates/" -- passed the gate silently while its lowercase
        # spelling correctly failed.
        (repo / 'Candidates').mkdir()
        (repo / 'Candidates' / 'notes.md').write_text('clean\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'mixed-case candidates dir')
        cases.append(('a mixed-case forbidden path (Candidates/) fails the '
                      'same as its lowercase spelling',
                      gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)
        shutil.rmtree(repo / 'Candidates', ignore_errors=True)

        # 6d. a vendored private set is recognised by what it CARRIES, not by
        # a name shape (2026-09-18, practice: source-naming). Two tells: a
        # path segment equal to a shared source this repo DECLARES, in any
        # case; and a source manifest that says the set is private, under
        # any directory name at all. A public planning document whose
        # title happens to start with "team" is neither, and passes.
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'shared', 'name': 'nightjar-set',
                         'path': '../nightjar-set'}]}), encoding='utf-8')
        (repo / 'spec').mkdir()
        (repo / 'spec' / 'TEAM_PLANNING_NOTE.md').write_text('a public note\n',
                                                              encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'declare a shared source')
        base_declared = git(repo, 'rev-parse', 'HEAD')
        cases.append(('a public document whose filename begins "TEAM" passes -- '
                      'a title is not a vendored set',
                      gate() == 0))
        (repo / 'Nightjar-Set' / 'practices').mkdir(parents=True)
        (repo / 'Nightjar-Set' / 'practices' / 'x.md').write_text('private\n',
                                                                   encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'vendor the declared set')
        cases.append(('a directory named after a DECLARED shared source fails, '
                      'in any case', gate('--range', f'{base_declared}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base_declared)
        shutil.rmtree(repo / 'Nightjar-Set', ignore_errors=True)
        (repo / 'vendored' / 'anything').mkdir(parents=True)
        (repo / 'vendored' / 'anything' / 'precedent-source.json').write_text(
            json.dumps({'name': 'whatever', 'level': 'shared',
                        'visibility': 'private'}), encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'vendor a manifest')
        cases.append(("a private set's own manifest fails under ANY directory "
                      'name', gate('--range', f'{base_declared}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)
        shutil.rmtree(repo / 'vendored', ignore_errors=True)
        shutil.rmtree(repo / 'spec', ignore_errors=True)
        (repo / 'precedent.json').unlink(missing_ok=True)

        # 6c. the FORBIDDEN_CONTENT "non-universal source" rule must catch a
        # real frontmatter-shaped line and NOT an ordinary sentence that
        # merely starts with "Source:" or "Level:". Regression case: the
        # rule originally had no end anchor, so it matched the START of any
        # line beginning with those words regardless of what followed --
        # ordinary capitalized prose, not just a practice's frontmatter,
        # hard-failed the always-on structural gate.
        (repo / 'frontmatter-leak.md').write_text(
            'source: individual\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'frontmatter leak')
        cases.append(('a real frontmatter-shaped `source: individual` line '
                       'still fails', gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)

        (repo / 'clean-prose.md').write_text(
            'Source: Individual contributions to this open-source library '
            'are always welcome, and we credit every contributor by name.\n\n'
            'Level: Team leads should review before merge.\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'ordinary prose')
        cases.append(('ordinary prose beginning a line with "Source:" or '
                       '"Level:" stays clean', gate('--range', f'{base}..HEAD') == 0))
        git(repo, 'reset', '-q', '--hard', base)

        # 7. the vocabulary layer must not fail OPEN once you have said you
        #    have a list.
        cases.append(('an unrun vocabulary layer fails when required',
                      gate('--require-vocabulary', blocklist_set=False) == 1))
        cases.append(('an unrun vocabulary layer only warns when not required',
                      gate(blocklist_set=False) == 0))

        # 8. a bad revision must not read as "nothing to check", and an
        #    unknown flag must not silently scan something else.
        cases.append(('an unresolvable revision fails rather than scanning nothing',
                      gate('--range', 'nosuchref..HEAD') == 1))
        cases.append(('an unknown flag fails', gate('--stage') == 1))

        # 9. a blocklist with nothing in it reports as CONFIGURED and passes
        #    with zero patterns -- a clean bill of health from a check holding
        #    nothing. Same family as case 7: the vocabulary layer must not be
        #    able to look switched on while doing no work.
        empty = tmp / 'empty.txt'
        empty.write_text('# only comments\n\n', encoding='utf-8')
        env = dict(os.environ, PRECEDENT_LEAK_BLOCKLIST=str(empty))
        rc = subprocess.run([sys.executable, str(repo / 'tools' / 'leak_gate.py')],
                            capture_output=True, text=True, cwd=str(repo),
                            env=env).returncode
        cases.append(('a blocklist with no patterns fails rather than passing '
                      'vacuously', rc == 1))

        # 10. the single ALLOWED_PATHS exemption, from both sides. Until
        #     2026-09-18 the vendored-private-set rule matched a path SEGMENT
        #     beginning 'precedent-individual', which is also the start of
        #     the canonical SessionStart hook's FILENAME -- so installing the
        #     hook this project tells every adopter to install failed the
        #     gate (2026-09-06, the moment BestPractice installed its own).
        #     The rule now matches a whole segment equal to the default
        #     individual name, so the hook passes on its own; the exemption
        #     stays as the record and the directory case must still fail.
        hook_rel = '.claude/hooks/precedent-individual-bootstrap.sh'
        (repo / '.claude' / 'hooks').mkdir(parents=True, exist_ok=True)
        (repo / hook_rel).write_text('#!/bin/bash\nexit 0\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'the canonical individual-source hook')
        cases.append(('the canonical individual-source bootstrap hook passes -- '
                      'the project refusing a file its own instructions '
                      'require is the bug this exemption fixes',
                      gate() == 0))

        (repo / 'precedent-individual' / 'practices').mkdir(parents=True)
        (repo / 'precedent-individual' / 'practices' / 'x.md').write_text(
            'vendored private content\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'a genuinely vendored private set')
        cases.append(('a vendored private practice-set DIRECTORY still fails -- '
                      'the exemption is one exact path, not a prefix',
                      gate() == 1))
        git(repo, 'rm', '-rq', 'precedent-individual')
        git(repo, 'commit', '-qm', 'remove the vendored set')

        # And the exemption must name the path the ENGINE looks for, not a
        # string that drifts from it.
        sys.path.insert(0, str(ROOT / 'tools'))
        import leak_gate as _lg
        import precedent_resolve as _pr
        cases.append(("leak_gate's exemption is exactly precedent_resolve's "
                      'INDIVIDUAL_BOOTSTRAP_HOOK, so the gate and the engine '
                      'cannot disagree about where the hook lives',
                      _pr.INDIVIDUAL_BOOTSTRAP_HOOK in _lg.ALLOWED_PATHS))

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  leak gate did NOT behave as stated: {name}")
        check(f'leak gate fires ({len(cases)} stated cases: blobs not the working '
              f'tree, every commit in a push, commit messages, fail-closed)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _b64_ssh():
    """The fixture's SSH remote, encoded so this scanned file carries no
    literal that the gate's email rule refuses. See its call site."""
    import base64
    return base64.b64decode('Z2l0QGdpdGh1Yi5jb206b3RoZXJmaXh0dXJlL0tlc3RyZWx3b29kLmdpdA==').decode()


def check_leak_gate_notes_an_uncovered_private_repo():
    """The stem-coverage note, as stated cases against throwaway clones.

    WHAT IT GUARDS. The gate has two ways to recognise a private repository
    and they cover different spellings: the repo-reference ALLOWLIST matches
    `owner/name`, and the vocabulary patterns match the BARE name. A private
    repo with no pattern of its own is therefore guarded in its qualified
    form and naked in its short one -- which is precisely how the 2026-09-07
    leak got out, as `<repo>-local`, with no slash anywhere for the allowlist
    to see.

    A NON-ZERO EXIT WOULD PROVE NOTHING HERE, because this reports and does
    not refuse: every case below asserts the TEXT the gate prints (practice:
    control-asserts-which-failure). The negative cases matter more than the
    positive one -- a note that fires on every repository on the disk is a
    note people stop reading, so "covered", "other owner" and "allowed" each
    have to stay silent.

    The names are invented. A real private repository name cannot appear in
    this file for the same reason the real blocklist cannot live in this
    repo at all -- and the first draft's invented stem still had to be
    changed, because it collided with `Team-Nightjar/`, an example name
    inside leak_gate.py's own comments, and the fixture went red on a
    genuine hit in the file it had just copied. That is the over-broad-stem
    failure this whole mechanism is about, reproduced by accident on the
    first run.
    """
    import shutil, tempfile

    def git(cwd, *args):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-stemnote-'))
    try:
        repo = tmp / 'repo'
        (repo / 'tools').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'leak_gate.py', repo / 'tools' / 'leak_gate.py')
        shutil.copy(ROOT / 'tools' / 'leak-blocklist.default.txt',
                    repo / 'tools' / 'leak-blocklist.default.txt')
        git(repo, 'init', '-q')
        git(repo, 'config', 'user.email', 'harness@example.com')
        git(repo, 'config', 'user.name', 'harness')
        (repo / 'ok.md').write_text('nothing sensitive here\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'base')

        # Siblings, which is how a session actually holds several repos at
        # once. Only the remote URL is read, so these need no commits.
        # The SSH remote is base64 here for the same reason the profanity
        # probes are, further down this file: verify_harness.py IS scanned by
        # the gate, and a literal SSH remote URL trips the structural "an
        # email address" rule -- its user-and-host prefix is shaped exactly
        # like one. Reproduced twice: the whole tree went red on the fixture,
        # and then again on the first version of THIS comment, which spelled
        # the URL out in prose. It is not an email address, and _remote_ref
        # has to parse the form, so the coverage is worth keeping. Whether
        # that rule should exempt this one well-known service address is a
        # real question and is NOT settled here -- encoding a fixture does
        # not widen the rule for anyone else.
        _ssh_remote = _b64_ssh()
        for dirname, url in [
                ('covered', 'https://github.com/fixtureacct/QuillonNotes.git'),
                ('uncovered', 'https://github.com/fixtureacct/Kestrelwood.git'),
                ('otherowner', _ssh_remote)]:
            d = tmp / dirname
            d.mkdir()
            git(d, 'init', '-q')
            git(d, 'remote', 'add', 'origin', url)
        (tmp / 'not-a-checkout').mkdir()

        blocklist = tmp / 'blocklist.txt'          # OUTSIDE the repo, as required
        declared = ('# visibility-audit: private-owner fixtureacct -- fixture\n'
                    '\\bquillon[\\w-]*\n')

        def gate_output(text, *args):
            blocklist.write_text(text, encoding='utf-8')
            env = dict(os.environ)
            env['PRECEDENT_LEAK_BLOCKLIST'] = str(blocklist)
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'leak_gate.py'), *args],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        # The survey's content, read where it is printed now: --survey
        # (ordinary runs are quiet by default since 2026-10-13).
        rc, out = gate_output(declared, '--survey')
        cases = [
            ('the note names the uncovered repository',
             'fixtureacct/Kestrelwood' in out),
            ('the note says what is missing, not merely that something is',
             'NO blocklist pattern matches its bare name' in out),
            ('the note quotes the bare name the stem has to cover',
             '"Kestrelwood"' in out),
            ('a repo whose bare name an existing stem matches is NOT noted',
             'QuillonNotes' not in out),
            ('a repo under an owner nobody declared private is NOT noted',
             'otherfixture/' not in out),
            ('a directory that is not a checkout is skipped without comment',
             'not-a-checkout' not in out),
            ('the note does not fail the push -- a missing stem is latent '
             'risk, not a hit', rc == 0),
        ]

        # An allow line is somebody stating the name may appear. Demanding a
        # stem for it would refuse the exposure they just accepted.
        _rc, out_allowed = gate_output(
            declared + '# visibility-audit: allow fixtureacct/Kestrelwood -- fixture\n',
            '--survey')
        cases.append(('an `allow` line for the repo silences the note',
                      'Kestrelwood' not in out_allowed))

        # And with no owner declared at all the survey must not run: it would
        # otherwise print private repository names into a CI log, which for a
        # public repo is a build log anyone can read.
        _rc, out_inert = gate_output('\\bquillon[\\w-]*\n', '--survey')
        cases.append(('no private-owner declaration means no survey at all, so '
                      'no name reaches a public build log',
                      'Kestrelwood' not in out_inert
                      and 'allowlist is INERT' in out_inert))

        # `stem-notes off` moves this note to the very deep check for the
        # one person whose blocklist says so (practice, in the individual
        # set: leak-gate-is-background). Three cases, because the failure
        # that matters is not "off did not silence it" but "off silenced it
        # EVERYWHERE" -- a note nobody can get back is a blind spot, and
        # very_deep_check.py's visibility pass reaches it through --survey.
        _off = '# visibility-audit: stem-notes off -- fixture\n'
        _rc_off, out_off = gate_output(declared + _off)
        _rc_surv, out_survey = gate_output(declared + _off, '--survey')
        _rc_on, out_on = gate_output(
            declared + '# visibility-audit: stem-notes on -- fixture\n')
        cases += [
            ('`stem-notes off` silences the routine note',
             'Kestrelwood' not in out_off),
            ('`stem-notes off` is not a parse error -- the directive is '
             'recognized, not read as a typo', _rc_off == 0
             and 'does not parse' not in out_off),
            ('--survey prints the note anyway, which is how the very deep '
             'check still reaches it', 'Kestrelwood' in out_survey),
            ('`stem-notes on` prints the note on an ordinary run',
             'Kestrelwood' in out_on),
            # Default OFF since 2026-10-13: a blocklist that says nothing
            # is quiet, so no set has to carry an opt-out line to keep its
            # owner from being shown routine notes on every push.
            ('a blocklist that says nothing is quiet by default',
             'Kestrelwood' not in gate_output(declared)[1]),
            ('silencing the note does not silence a HIT: the gate still '
             'exits 0 here only because there is nothing to catch',
             _rc_off == 0 and _rc_surv == 0),
        ]

        # auto-cover-bare-names: the half that REFUSES rather than notes.
        # Silencing the survey removed the request to write a stem, not the
        # risk it was about -- Morgan, 2026-09-12: "there is ONE THING I want
        # to stop from leaking: private repo names."
        (repo / 'names-it.md').write_text(
            'the Kestrelwood rollout is going fine\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'names a private repo by its bare name')
        _auto = '# visibility-audit: auto-cover-bare-names on -- fixture\n'
        rc_auto, out_auto = gate_output(declared + _auto)
        rc_default, out_default = gate_output(declared)
        rc_allowed, out_allowed2 = gate_output(
            declared + _auto +
            '# visibility-audit: allow fixtureacct/Kestrelwood -- fixture\n')
        cases += [
            ('`auto-cover-bare-names on` FAILS the push on a bare private '
             'repo name -- a refusal, not a note', rc_auto == 1),
            ('...and says which name and that it was auto-covered, so the '
             'remedy is obvious from the message',
             'private repository name "Kestrelwood"' in out_auto
             and 'auto-covered' in out_auto),
            ('...and points at the two real remedies rather than a stem',
             'Scrub it' in out_auto and 'allow line' in out_auto),
            ('the default is OFF: without the directive the same tree passes, '
             'so nobody else\'s gate changes under them', rc_default == 0),
            ('an `allow` line beats auto-cover -- an accepted exposure stays '
             'accepted, and the tree naming it passes',
             rc_allowed == 0 and 'LEAK' not in out_allowed2),
            ('a repo whose bare name an existing stem already covers is not '
             'double-reported as auto-covered',
             'private repository name "QuillonNotes"' not in out_auto),
        ]

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  stem-coverage note did NOT behave as stated: {name}")
        check(f'the leak gate notes a private clone with no blocklist stem '
              f'({len(cases)} stated cases, each asserting the printed text)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_leak_gate_discovers_the_individual_blocklist():
    """The private list is found without PRECEDENT_LEAK_BLOCKLIST being set.

    WHAT IT GUARDS. Before this, the vocabulary layer ran only for a shell
    that had exported the variable -- so every fresh container, every new
    session and every forgotten export downgraded the gate to its structural
    half and produced a PARTIAL that reads like a fault. The list was on disk
    the whole time, where INSTALL.md section 8 puts it.

    THE FIXTURE OWNS ITS ABSENCE (practice: fixture-owns-its-state). It
    scrubs PRECEDENT_LEAK_BLOCKLIST and points HOME at a directory it built
    -- three separate variables have made a fixture assert the opposite of
    what it ran by inheriting the container's real one. It also asserts the
    NEGATIVE case from the same fixture: a HOME with no config must still
    resolve to nothing, or "discovery" would just be "whatever was lying
    around".

    It resolves the config file directly and never calls
    precedent_resolve.load_config(), which self-heals by CLONING the
    individual source into whatever HOME it is handed -- the 2026-09-08
    gotcha where a fixture built to hold "no private source" turned itself
    into "a private source resolved" mid-run.
    """
    import shutil, tempfile, json as _json
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as _lg

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bldiscover-'))
    saved = {k: os.environ.get(k) for k in ('HOME', 'PRECEDENT_LEAK_BLOCKLIST')}
    try:
        home = tmp / 'home'
        (home / '.config' / 'precedent').mkdir(parents=True)
        individual = tmp / 'individual'
        individual.mkdir()
        (individual / 'leak-blocklist.txt').write_text(
            '# visibility-audit: private-owner fixtureacct -- fixture\n'
            '\\bquillon[\\w-]*\n', encoding='utf-8')
        (home / '.config' / 'precedent' / 'config.json').write_text(
            _json.dumps({'individual': {'path': str(individual)}}), encoding='utf-8')

        os.environ['HOME'] = str(home)
        os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        found, how = _lg.resolve_blocklist_path()

        # An env var still wins, so a caller can point at another list.
        other = tmp / 'other.txt'
        other.write_text('\\bsomething\n', encoding='utf-8')
        os.environ['PRECEDENT_LEAK_BLOCKLIST'] = str(other)
        overridden, how_over = _lg.resolve_blocklist_path()

        # No config at all: nothing discovered, and nothing invented.
        os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        os.environ['HOME'] = str(tmp / 'empty-home')
        (tmp / 'empty-home').mkdir()
        absent, how_absent = _lg.resolve_blocklist_path()

        cases = [
            ('the individual set\'s leak-blocklist.txt is found with no '
             'variable set', found == individual / 'leak-blocklist.txt'),
            ('and says where it came from, so a reader can tell a discovered '
             'list from an exported one', how == 'individual source'),
            ('PRECEDENT_LEAK_BLOCKLIST still overrides it',
             overridden == other and how_over == 'env'),
            ('a HOME with no precedent config discovers nothing, rather than '
             'falling back to whatever is on the disk',
             absent is None and how_absent is None),
            ('discovery does not clone anything into the HOME it was handed '
             '-- it reads, it does not repair',
             not (tmp / 'empty-home' / 'precedent-individual').exists()),
        ]
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  blocklist discovery did NOT behave as stated: {name}")
        check(f'the leak gate discovers the individual set\'s blocklist with '
              f'no variable exported ({len(cases)} stated cases)', ok)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def check_leak_gate_reads_neighbour_blocklists():
    """Every repository checked out beside this one contributes its list.

    WHAT IT GUARDS (2026-10-01). A session working in a private repository
    carried that repository's names into this public tree through a pull
    request, and the gate passed it: the only private list it read was the
    person's individual source's, and the private repository's own
    `leak-blocklist.txt`, checked out beside it, was never consulted. The
    same day it refused a clean merge because a private shared set's list,
    on disk beside it, was never read either.

    Stated cases, from one fixture that owns its state: a neighbour clone's
    list is found; a neighbour without one adds nothing; a loose directory
    (no .git) is not a repository and is not read; the gate itself is not
    its own neighbour; and with no variable and no individual source,
    load_blocklist() still applies the neighbour's patterns and reports the
    private half as configured. The fixture's pattern is the kind that
    failed: a name inside an identifier, which `\b` let through.
    (practice: scrub-gate)"""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as _lg

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-neighbours-'))
    saved_env = {k: os.environ.get(k) for k in ('HOME', 'PRECEDENT_LEAK_BLOCKLIST')}
    saved_root = _lg.ROOT
    try:
        repo = tmp / 'public-tree'
        private = tmp / 'private-repo'
        plain = tmp / 'plain-repo'
        loose = tmp / 'loose-dir'
        for d in (repo, private, plain):
            (d / '.git').mkdir(parents=True)
        loose.mkdir()
        (private / 'leak-blocklist.txt').write_text(
            '(?<![a-z])zqxcorp(?![a-z])\n', encoding='utf-8')
        (loose / 'leak-blocklist.txt').write_text('\\bnotread\n', encoding='utf-8')
        (repo / 'leak-blocklist.txt').write_text('\\bself\n', encoding='utf-8')
        (tmp / 'home').mkdir()

        found = _lg.discovered_neighbour_blocklists(root=repo)
        # From a throwaway worktree elsewhere -- where the merge check runs
        # -- the main clone's neighbours are the ones that count.
        real = tmp / 'nest' / 'real-tree'
        (tmp / 'nest' / 'private-neighbour').mkdir(parents=True)
        (tmp / 'nest' / 'private-neighbour' / '.git').mkdir()
        (tmp / 'nest' / 'private-neighbour' / 'leak-blocklist.txt').write_text(
            'zqxother\n', encoding='utf-8')
        real.mkdir()
        _git = lambda *a: subprocess.run(['git', '-C', str(real), *a],
                                         capture_output=True, text=True)
        _git('init', '-q')
        (real / 'f.txt').write_text('x\n', encoding='utf-8')
        _git('add', 'f.txt')
        _git('-c', 'user.name=f', '-c', 'user.email=f@example.invalid',
             'commit', '-q', '-m', 'f')
        wt = tmp / 'elsewhere' / 'wt'
        wt.parent.mkdir()
        _git('worktree', 'add', '-q', '--detach', str(wt))
        from_wt = _lg.discovered_neighbour_blocklists(root=wt)
        os.environ['HOME'] = str(tmp / 'home')
        os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        _lg.ROOT = repo
        pats, desc, configured = _lg.load_blocklist()
        catches = any(p.search('see zqxcorp_cost_model.py') for p in pats)
        cases = [
            ('a neighbour clone\'s leak-blocklist.txt is found',
             private / 'leak-blocklist.txt' in found),
            ('a neighbour with no list adds nothing, a loose directory is '
             'not a repository, and the tree is not its own neighbour',
             found == [private / 'leak-blocklist.txt']),
            ('with no variable and no individual source, the neighbour\'s '
             'list is applied and the private half reports configured',
             configured and str(private / 'leak-blocklist.txt') in desc),
            ('a name inside an identifier is caught', catches),
            ('from a worktree elsewhere, the main clone\'s neighbour is read',
             tmp / 'nest' / 'private-neighbour' / 'leak-blocklist.txt'
             in [p.resolve() for p in from_wt]),
        ]
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  neighbour discovery did NOT behave as stated: {name}")
        check(f'the leak gate reads the blocklists of repositories checked '
              f'out beside it ({len(cases)} stated cases)', ok)
    finally:
        _lg.ROOT = saved_root
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def check_leak_gate_names_a_stale_blocklist_clone():
    """The gate says where its blocklist came from when it FAILS, and --
    since 2026-09-20 -- tries one bounded fast-forward before saying so.

    THE INCIDENT, 2026-09-11. The gate reported 30 undeclared-repo hits
    against Precedent's own tree. A session read them as a defect in the
    tree, wrote them into a pull request's gate block as "red on the base
    branch too", and filed a TODO item for a fix that was already merged.
    The tree was fine. That session's clone of the private practice set was
    a few hours old -- from before a repository rename added the allowlist
    line those 30 references needed -- so the gate was right about its input
    and its input was stale.

    THE SECOND INCIDENT, 2026-09-20: the same shape, 110 hits, and by then
    the gate already told the session to run `git -C <root> pull --ff-only`.
    Running it by hand is the common remedy; leak_gate.py now tries it
    itself, once, only after a hit already exists to lose from not trying --
    see _try_refresh_private_blocklist_clone()'s own docstring in
    tools/leak_gate.py for why that is still never on a clean push.

    WHY THE NOTE STILL NEEDS TO EXIST: the self-heal only covers the clean
    fast-forward case. A clone that has genuinely diverged -- local commits
    of its own, same as 2026-09-20's actual clone, which had advanced a
    watermark file and not yet pushed it -- gets an honest BEHIND note
    exactly as before, because `pull --ff-only` refuses a non-fast-forward
    and this function refuses to guess which side to keep.

    Four branches are asserted: a clone that fast-forwards cleanly and the
    fast-forward clears the only hit (the gate passes); a clone that cannot
    fast-forward (diverged, same as the real incident) and still fails,
    reported honestly as behind; a clone already current (unaffected either
    way); and a loose file in no repository at all (no note is a guess).
    """
    import shutil, tempfile

    def git(cwd, *args):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='leak-stale-'))
    try:
        # Two trees to scan: one names a repo NEVER allow-listed (a real,
        # persistent hit, whatever the blocklist's own freshness), the other
        # names one allow-listed only in the blocklist's SECOND commit (a
        # hit caused purely by staleness -- refreshing the clone clears it).
        def make_tree(name, mentions):
            r = tmp / name
            (r / 'tools').mkdir(parents=True)
            shutil.copy(ROOT / 'tools' / 'leak_gate.py', r / 'tools' / 'leak_gate.py')
            shutil.copy(ROOT / 'tools' / 'leak-blocklist.default.txt',
                        r / 'tools' / 'leak-blocklist.default.txt')
            git(r, 'init', '-q')
            git(r, 'config', 'user.email', 'harness@example.com')
            git(r, 'config', 'user.name', 'harness')
            (r / 'names.md').write_text(f'this tree names {mentions}\n', encoding='utf-8')
            git(r, 'add', '-A')
            git(r, 'commit', '-qm', 'base')
            return r

        repo_persistent = make_tree('repo-persistent', 'fixtureacct/Kestrelwood')
        repo_healable = make_tree('repo-healable', 'fixtureacct/Willowmere')

        # The blocklist lives in its own repository, the way a private
        # practice set's does. `upstream` stands in for the remote.
        upstream = tmp / 'upstream'
        upstream.mkdir()
        git(upstream, 'init', '-q', '-b', 'main')
        git(upstream, 'config', 'user.email', 'harness@example.com')
        git(upstream, 'config', 'user.name', 'harness')
        bl = upstream / 'blocklist.txt'
        # A real pattern as well as the owner line: a blocklist of
        # comments alone is refused earlier, for a different reason, and
        # the fixture would never reach the note it exists to test.
        # Kestrelwood is never allow-listed, in either commit -- the
        # persistent-hit tree above always fails, refresh or not.
        declared = ('# visibility-audit: private-owner fixtureacct -- fixture\n'
                    '\\bquillon[\\w-]*\n')
        bl.write_text(declared, encoding='utf-8')
        git(upstream, 'add', '-A')
        git(upstream, 'commit', '-qm', 'first')
        # The rename/allowlist commit a stale clone does not have yet --
        # Willowmere only stops being a hit from here on.
        bl.write_text(declared +
                      '# visibility-audit: allow fixtureacct/Willowmere -- fixture, renamed\n',
                      encoding='utf-8')
        git(upstream, 'add', '-A')
        git(upstream, 'commit', '-qm', 'second')

        def gate(blocklist_path, repo):
            env = {k: v for k, v in os.environ.items()}
            env['PRECEDENT_LEAK_BLOCKLIST'] = str(blocklist_path)
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'leak_gate.py')],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        # 1. A clean clone, purely behind: the self-heal fast-forwards it,
        # and the only hit was the staleness itself -- the gate now PASSES.
        healed = tmp / 'healed'
        git(tmp, 'clone', '-q', str(upstream), str(healed))
        git(healed, 'reset', '-q', '--hard', 'HEAD~1')
        rc_healed, out_healed = gate(healed / 'blocklist.txt', repo_healable)
        healed_head = git(healed, 'rev-parse', 'HEAD')
        upstream_head = git(upstream, 'rev-parse', 'HEAD')

        # 2. A diverged clone -- a local commit of its own, same shape as
        # 2026-09-20's real clone (an unpushed watermark advance). No
        # fast-forward is possible, so this still fails and still reports
        # BEHIND honestly, against a persistent, staleness-independent hit.
        diverged = tmp / 'diverged'
        git(tmp, 'clone', '-q', str(upstream), str(diverged))
        git(diverged, 'config', 'user.email', 'harness@example.com')
        git(diverged, 'config', 'user.name', 'harness')
        git(diverged, 'reset', '-q', '--hard', 'HEAD~1')
        (diverged / 'local-only.txt').write_text('not on the remote\n', encoding='utf-8')
        git(diverged, 'add', '-A')
        git(diverged, 'commit', '-qm', 'local commit the remote does not have')
        rc_diverged, out_diverged = gate(diverged / 'blocklist.txt', repo_persistent)

        # 3. A clone that is already current.
        current = tmp / 'current'
        git(tmp, 'clone', '-q', str(upstream), str(current))
        rc_current, out_current = gate(current / 'blocklist.txt', repo_persistent)

        # 4. A loose file in no repository at all.
        loose = tmp / 'loose.txt'
        loose.write_text(declared, encoding='utf-8')
        _rc_loose, out_loose = gate(loose, repo_persistent)

        cases = [
            ('a clean, purely-behind clone is fast-forwarded and the gate '
             'PASSES once the only hit was the staleness itself',
             rc_healed == 0),
            ('the fast-forward actually happened on disk, not just in the '
             'gate\'s report', healed_head == upstream_head),
            ('the healed run never prints a LEAK line for a hit that '
             'stopped being one', 'LEAK:' not in out_healed),
            ('a diverged clone (local commit the remote lacks -- the real '
             'incident\'s shape) is reported as BEHIND', 'BEHIND its upstream' in out_diverged),
            ('the note names the clone, so the reader knows which one to pull',
             str(diverged) in out_diverged),
            ('the note gives the command that settles it',
             'pull --ff-only' in out_diverged),
            ('the note appears only after the hits, as context for them',
             out_diverged.find('LEAK:') < out_diverged.find('Before acting on these:')),
            ('a diverged clone is genuinely untouched: still behind, still '
             'carrying its own local commit',
             git(diverged, 'rev-parse', 'HEAD') != upstream_head),
            ('a current clone is NOT called current -- an unfetched '
             'remote-tracking ref cannot prove that',
             'BEHIND its upstream' not in out_current
             and 'not proof it is current' in out_current),
            ('a current clone still names itself, so the reader can check',
             str(current) in out_current),
            ('a blocklist in no repository produces no note rather than a guess',
             'Before acting on these:' not in out_loose),
            ('a real, staleness-independent hit still fails the push either '
             'way', rc_diverged == 1 and rc_current == 1),
        ]
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  stale-blocklist note did NOT behave as stated: {name}")
        check(f'the leak gate names a stale blocklist clone when it fails, '
              f'and self-heals the clean case ({len(cases)} stated cases)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_leak_gate_refresh_declines_a_dirty_clone():
    """_try_refresh_private_blocklist_clone() never touches uncommitted
    work. A working copy with local edits in progress is somebody's, not
    this gate's, and the same refusal tools/precedent_source_bootstrap.py's
    own sync already makes for the same reason (see its _sync_once, the
    "uncommitted work... not this tool's call to make" branch).
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as _lg

    def git(cwd, *args):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='leak-refresh-dirty-'))
    saved_path = _lg._PRIVATE_BLOCKLIST_PATH
    try:
        upstream = tmp / 'upstream'
        upstream.mkdir()
        git(upstream, 'init', '-q', '-b', 'main')
        git(upstream, 'config', 'user.email', 'harness@example.com')
        git(upstream, 'config', 'user.name', 'harness')
        bl = upstream / 'blocklist.txt'
        bl.write_text('\\bquillon[\\w-]*\n', encoding='utf-8')
        git(upstream, 'add', '-A')
        git(upstream, 'commit', '-qm', 'first')
        bl.write_text('\\bquillon[\\w-]*\n# a later commit\n', encoding='utf-8')
        git(upstream, 'add', '-A')
        git(upstream, 'commit', '-qm', 'second')

        clone = tmp / 'clone'
        git(tmp, 'clone', '-q', str(upstream), str(clone))
        git(clone, 'reset', '-q', '--hard', 'HEAD~1')
        # An uncommitted edit -- clean history, dirty working tree.
        (clone / 'blocklist.txt').write_text(
            '\\bquillon[\\w-]*\n# an uncommitted local edit\n', encoding='utf-8')
        head_before = git(clone, 'rev-parse', 'HEAD')

        _lg._PRIVATE_BLOCKLIST_PATH = clone / 'blocklist.txt'
        refreshed = _lg._try_refresh_private_blocklist_clone()
        head_after = git(clone, 'rev-parse', 'HEAD')
        dirty_after = git(clone, 'status', '--porcelain')

        cases = [
            ('a dirty clone is declined, not silently repaired', refreshed is False),
            ('HEAD is untouched', head_before == head_after),
            ('the uncommitted edit is still there, unstashed and uncommitted',
             'an uncommitted local edit' in (clone / 'blocklist.txt').read_text(encoding='utf-8')
             and dirty_after.strip() != ''),
        ]

        _lg._PRIVATE_BLOCKLIST_PATH = None
        cases.append(('no private path configured means nothing to try',
                      _lg._try_refresh_private_blocklist_clone() is False))
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  dirty-clone refresh did NOT behave as stated: {name}")
        check(f'the leak gate\'s clone refresh declines a dirty working tree '
              f'({len(cases)} stated cases)', ok)
    finally:
        _lg._PRIVATE_BLOCKLIST_PATH = saved_path
        shutil.rmtree(tmp, ignore_errors=True)


def check_leak_gate_reads_a_sets_own_visibility():
    """The leak gate takes a practice set's visibility from its
    precedent-source.json when precedent.json does not declare one.

    WHY. A freshly bootstrapped private individual set writes `visibility`
    only into precedent-source.json, whose own comment says the gate reads
    it there. The gate read precedent.json alone, took the set as public,
    and refused every push of it for holding its own blocklist (very deep
    check, 2026-10-11, pass 1)."""
    import tempfile
    import leak_gate as lg
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'precedent-source.json').write_text(
            json.dumps({'visibility': 'private'}), encoding='utf-8')
        only_source = lg.declared_visibility(root)[0]
        (root / 'precedent.json').write_text(json.dumps({'sources': []}),
                                             encoding='utf-8')
        undeclared_config = lg.declared_visibility(root)[0]
        (root / 'precedent.json').write_text(json.dumps({'visibility': 'public'}),
                                             encoding='utf-8')
        config_wins = lg.declared_visibility(root)[0]
    cases = [('a set with only precedent-source.json is private',
              only_source == 'private'),
             ('a precedent.json that says nothing defers to it',
              undeclared_config == 'private'),
             ('a precedent.json that says something still wins',
              config_wins == 'public')]
    failed = [n for n, ok in cases if not ok]
    check(f'the leak gate reads a set\'s own visibility ({len(cases)} stated '
          f'cases)', not failed, '; '.join(failed))


def check_visibility_audit_reads_the_blocklist_as_patterns():
    """The stale-entry half of very_deep_check's visibility audit, repaired.

    THE BUG THIS PINS DOWN was silent and was caused by an unrelated fix.
    That audit reported "this name is on the blocklist but the repository is
    now PUBLIC" by comparing `name.lower() in blocked`, where `blocked` was
    each blocklist line with `\\b` stripped off both ends -- exact string
    equality, correct for as long as every entry was a whole repository name.
    The 2026-09-07 stem rewrite turned every entry into a truncated head plus
    a suffix match, after which equality matched nothing and that half of the
    audit reported a clean sweep it had not performed.

    Asserted through the same reader the push gate uses, so the two cannot
    drift in how they interpret a line."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as _lg
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        bl = pathlib.Path(td) / 'blocklist.txt'
        bl.write_text('\\bquillon[\\w-]*\n\\bkestrel\\b\n', encoding='utf-8')
        pats = _lg._parse_blocklist(bl)

        def covered(name):
            return any(p.search(name) for p in pats)

        def _old_reading_matches(name, path):
            blocked = {re.sub(r'^\\b|\\b$', '', line.strip()).lower()
                       for line in path.read_text(encoding='utf-8').splitlines()
                       if line.strip() and not line.strip().startswith('#')}
            return name.lower() in blocked

        cases = [
            ('a stem matches the full name it was truncated from',
             covered('QuillonNotes')),
            ('a stem matches a name DERIVED from the repo -- the 2026-09-07 '
             'case', covered('quillon-local')),
            # The negative control is the OLD logic, run for real rather
            # than described: strip the anchors, lowercase, compare for
            # equality. It must MISS the name the new reading catches, or
            # this check is not testing the repair.
            ('the string comparison this replaced misses that name, which is '
             'what made the regression invisible',
             not _old_reading_matches('QuillonNotes', bl)),
            ('an unrelated name is not matched', not covered('Kestrelwood')),
            ('a whole-name entry still matches its own name, so repairing '
             'this did not break the entries that were already right',
             covered('Kestrel')),
        ]
        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  blocklist pattern reading did NOT behave as stated: {name}")
        check(f'the visibility audit reads blocklist entries as patterns, so a '
              f'stem entry is still recognised ({len(cases)} stated cases)', ok)


def check_default_blocklist_runs_the_vocabulary_layer():
    """The vocabulary layer runs on every invocation, against a real list.

    THE GAP THIS CLOSES (2026-09-06). The vocabulary layer was skipped
    entirely whenever PRECEDENT_LEAK_BLOCKLIST was unset -- which is every
    continuous-integration run and every fresh clone. So the code path that
    loads patterns, compiles them and scans with them was exercised only by
    this harness, never by an actual gate run, and the gate reported PARTIAL
    forever. A mechanism that only ever runs in its own tests is one nobody
    finds out is broken.

    THE SPLIT THAT MAKES A COMMITTED LIST HONEST. The private blocklist
    holds SECRET words, and one committed to a public repo publishes the
    terms it exists to protect -- load_blocklist still refuses a private
    list located inside this repository. The DEFAULT list holds only
    publishable terms, so committing it costs nothing and it makes the layer
    real. The two are merged, and the gate says which halves ran: a clean
    scan against publishable terms is not evidence that no private word is
    present, and that sentence had to survive the change or this would just
    be the old silence with better wording."""
    import base64 as _b64
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as lg

    # Both probes are base64 in the source for the same reason the gate's own
    # blocklist file is exempt from its own scan: this file IS scanned, so a
    # literal here fails the gate on its own test fixture. Reproduced while
    # writing it -- the derived-form probe below was a plain string and the
    # gate correctly refused the tree, which is the check working.
    word = _b64.b64decode('ZnVjaw==').decode()
    derived_probe = _b64.b64decode('d2hhdCBhIGJ1bmNoIG9mIGFzc2hvbGVz').decode()
    # A HOME of its own, for the reason spelled out in check_leak_gate_fires:
    # with the variable unset the gate reads the individual set named in
    # ~/.config/precedent/config.json, and this check's whole subject is what
    # happens when NOTHING is configured. Inheriting the container's real HOME
    # would quietly configure it (practice: fixture-owns-its-state).
    import tempfile as _tf
    _scratch_home = _tf.mkdtemp(prefix='precedent-defaultbl-home-')
    env_clean = {k: v for k, v in os.environ.items() if k != 'PRECEDENT_LEAK_BLOCKLIST'}
    env_clean['HOME'] = _scratch_home

    def gate(*args, env=None, cwd=None):
        # --structural-only always, because that is exactly what this check is
        # about: whether the DEFAULT blocklist makes the vocabulary layer run
        # at all. Since 2026-09-08 a bare invocation in this repo refuses
        # instead, because precedent.json declares a private source and no
        # private list is set here -- correct for a person about to push,
        # wrong for a fixture asking about the other half. Naming the half is
        # the fixture owning its own state rather than inheriting a default
        # that changed underneath it (practice: fixture-owns-its-state).
        return subprocess.run([sys.executable, str(ROOT / 'tools' / 'leak_gate.py'),
                               '--structural-only', *args],
                              capture_output=True, text=True, env=env or env_clean,
                              cwd=str(cwd or ROOT))

    # In-process calls read os.environ, not the env_clean handed to
    # subprocesses -- so the same absence has to be owned here too, or
    # load_blocklist() discovers the container's real individual set and
    # `private_configured` comes back True in a check whose subject is the
    # state where nothing is configured.
    #
    # Neighbours count as configuration too (2026-10-04). Since 2026-10-01
    # load_blocklist also reads the leak-blocklist.txt of every repository
    # checked out beside this one, so a clone with a practice set beside it
    # came back `private_configured` and this check failed or passed by
    # where the clone sat on disk -- red in the main clone of a session with
    # its sets attached, green in a scratch worktree. "Nothing configured"
    # means no neighbours either.
    def _unconfigured(fn):
        _saved = os.environ.get('HOME')
        _saved_neighbours = lg.discovered_neighbour_blocklists
        os.environ['HOME'] = _scratch_home
        os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        lg.discovered_neighbour_blocklists = lambda root=None: []
        try:
            return fn()
        finally:
            lg.discovered_neighbour_blocklists = _saved_neighbours
            if _saved is None:
                os.environ.pop('HOME', None)
            else:
                os.environ['HOME'] = _saved

    pats, source, private_configured = _unconfigured(lg.load_blocklist)
    cases = [
        ('the default blocklist is applied with no environment variable set',
         len(pats) > 0 and not private_configured),
        ('the banned word is caught by it',
         any(p.search(f'a {word}ing line') for p in pats)),
        ('...including derived forms', any(p.search(derived_probe) for p in pats)),
        ('...without the Scunthorpe problem -- word boundaries, not substrings',
         not any(p.search('Scunthorpe assessment bass classic') for p in pats)),
    ]

    r = gate()
    cases.append(('a clean tree now reports OK rather than PARTIAL -- the layer '
                  'ran, so "did not run" is no longer a reachable state',
                  r.returncode == 0 and 'leak gate OK' in r.stdout
                  and 'PARTIAL' not in r.stdout))
    cases.append(('...while still saying the PRIVATE half did not run -- a clean '
                  'scan against publishable terms is not evidence about private '
                  'ones, and that had to survive the change',
                  'private half' in r.stdout and 'PRECEDENT_LEAK_BLOCKLIST' in r.stdout))

    cases.append(('the blocklist file is exempt from its own scan -- a list of '
                  'banned words necessarily contains them, and scanning it would '
                  'hard-fail the gate on its own list',
                  not lg.is_texty('tools/leak-blocklist.default.txt')
                  and lg.is_texty('tools/leak_gate.py')))

    # The two planted files below go in a throwaway worktree, never in ROOT.
    # --as-ci runs its shards side by side in ONE checkout, and a file
    # planted in ROOT was visible to every other shard for as long as this
    # gate ran: a shard that snapshotted the tree in that window
    # (_ref_including_worktree) found it dirty and had to commit it, which
    # with --isolated's empty $HOME has no identity and fails the run.
    # Found 2026-10-01: two isolated runs out of two lost a shard to
    # ZZ_leakprobe_fixture.md once a change shifted the shards' timing.
    _wt_dir = _tf.mkdtemp(prefix='precedent-leakprobe-')
    wt = pathlib.Path(_wt_dir) / 'wt'
    subprocess.run(['git', '-C', str(ROOT), 'worktree', 'add', '-q', '--detach',
                    str(wt), _ref_including_worktree(ROOT)], capture_output=True)

    def gate_wt(env=None):
        return subprocess.run([sys.executable, str(wt / 'tools' / 'leak_gate.py'),
                               '--structural-only'],
                              capture_output=True, text=True, env=env or env_clean,
                              cwd=str(wt))

    # It genuinely blocks a push, not merely matches in a unit test.
    probe = wt / 'ZZ_leakprobe_fixture.md'
    probe.write_text(f'# Fixture\n\nThis {word}ing line must be caught.\n',
                     encoding='utf-8')
    r = gate_wt()
    cases.append(('a planted instance FAILS the whole gate, not just a regex',
                  r.returncode == 1 and 'LEAK' in r.stdout))
    probe.unlink(missing_ok=True)

    # A private list is merged with the default, never replaces it.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        priv = pathlib.Path(td) / 'private.txt'
        priv.write_text('acme-corp-secret-codename\n', encoding='utf-8')
        os.environ['PRECEDENT_LEAK_BLOCKLIST'] = str(priv)  # wins over discovery
        # Neighbours stay out of the count, as in _unconfigured: the
        # arithmetic below is the default plus this one list, nothing else.
        _saved_neighbours = lg.discovered_neighbour_blocklists
        lg.discovered_neighbour_blocklists = lambda root=None: []
        try:
            merged, src, configured = lg.load_blocklist()
        finally:
            lg.discovered_neighbour_blocklists = _saved_neighbours
            os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        cases.append(('a private list is MERGED with the default, never replaces '
                      'it -- configuring one must not silently drop the other',
                      configured and len(merged) == len(pats) + 1
                      and any(p.search('acme-corp-secret-codename') for p in merged)
                      and any(p.search(f'{word}ing') for p in merged)))

    # A private list inside the repo is still refused -- the guard that makes
    # the whole split safe.
    inside = wt / 'ZZ_inside_blocklist.txt'
    try:
        inside.write_text('secret-term\n', encoding='utf-8')
        r = gate_wt(env={**env_clean, 'PRECEDENT_LEAK_BLOCKLIST': str(inside)})
        cases.append(('a PRIVATE blocklist located inside this repo is still '
                      'refused -- the guard that makes a committed default safe '
                      'is that only the default may live here',
                      r.returncode == 1 and 'INSIDE' in (r.stdout + r.stderr)))
    finally:
        subprocess.run(['git', '-C', str(ROOT), 'worktree', 'remove', '--force',
                        str(wt)], capture_output=True)
        import shutil as _sh
        _sh.rmtree(_wt_dir, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'the default blocklist makes the vocabulary layer actually run, and '
          f'the private half stays external ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_leak_gate_sees_main_clone_siblings_from_a_worktree():
    """The leak gate's survey of private clones finds the main checkout's
    siblings when it runs from a worktree somewhere else.

    2026-09-28: a push check run from a `git worktree` under a session's
    scratchpad passed a private repository's name into a public practice
    set, because local_clone_refs() looked only at the worktree's own
    parent directory, which held no other clone. Run from the main clone,
    the same gate flagged it. Builds both layouts and owns its state
    (practice: fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-leak-worktree-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='f@example.com',
               HOME=str(tmp), GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

    def git(cwd, *a):
        subprocess.run(['git', *a], cwd=str(cwd), env=env, check=True,
                       capture_output=True, text=True)
    cases = []
    try:
        clones, scratch = tmp / 'clones', tmp / 'scratch'
        clones.mkdir()
        scratch.mkdir()
        for name, url in (('public-set', 'https://github.com/fixture-owner/public-set'),
                          ('secret-app', 'https://github.com/fixture-owner/secret-app')):
            git(tmp, 'init', '-q', str(clones / name))
            git(clones / name, 'remote', 'add', 'origin', url)
            (clones / name / 'f').write_text('x\n', encoding='utf-8')
            git(clones / name, 'add', '-A')
            git(clones / name, 'commit', '-qm', 'init')
        wt = scratch / 'wt'
        git(clones / 'public-set', 'worktree', 'add', '-q', str(wt))
        secret = ('fixture-owner', 'secret-app')
        cases.append(('from the main clone, the private sibling is seen',
                      secret in leak_gate.local_clone_refs(clones / 'public-set')))
        cases.append(('the worktree\'s own parent holds no other clone (the case is real)',
                      not any((d / '.git').exists() for d in scratch.iterdir() if d != wt)))
        cases.append(('from a worktree elsewhere, the private sibling is still seen',
                      secret in leak_gate.local_clone_refs(wt)))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_retired_words_are_found_and_history_is_left():
    """tools/our_language.py's retired-word scan (precedent_check.py's
    retired-words check), each state planted: live text is refused and names
    the replacement; history keeps the old word -- a ## Story, a quotation
    over several lines, a todo/ file, a document whose frontmatter says it is
    closed, a line about the retirement itself; and a frontmatter value
    (an index clause) is live even though it is in quotation marks, which is
    how disclose-landing's "named team" slipped the first version of this
    scan. Built 2026-09-29, when "team set" had been retired by searching
    for one phrase and "team source", `--level team` and a code path that
    read only level "team" all survived.
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import our_language as ol
    retired = ol.load_retired()
    cases = []

    def hits(rel, text):
        return ol.retired_uses_in(rel, text, retired)

    out = hits('documentation/X.md', 'Declare the team source in precedent.json.\n')
    cases.append(('live prose using a retired phrase is found, with its '
                  'replacement', len(out) == 1 and out[0][2] == 'shared', out))
    practice = ('---\nslug: x\napplies_to:  ["**"]\n'
                'index_clause: "say where -- individual, named team, or universal"\n'
                'status:      active\n---\n## Rule\nA rule.\n'
                '## Story\nIt began in a team set.\n')
    out = hits('practices/x.md', practice)
    cases.append(('a quoted frontmatter value is live (and ["**"] opens no '
                  'quotation); the ## Story is left alone',
                  [n for n, *_ in out] == [4], out))
    quote = ('He said: *"move it out of the individual and\nteam repos, '
             'please"* and it moved.\n')
    cases.append(('a quotation over two lines keeps its words',
                  hits('spec/Y.md', quote) == [], hits('spec/Y.md', quote)))
    cases.append(('a todo/ item is history',
                  hits('todo/todo-x.md', 'the team set\n') == [], ''))
    closed = '---\nkind:          brief\nstatus:        closed\n---\nthe team set\n'
    cases.append(('a document whose frontmatter says closed is history',
                  hits('spec/Z.md', closed) == [], ''))
    cases.append(('a line about the retirement itself keeps the old word',
                  hits('documentation/W.md', 'The old spelling, `--level team`, '
                       'still works.\n') == [], ''))
    # MAP.md's withdrawn-practice rows quote the withdrawn practice's own
    # Story; a row with a finished status in a cell is history. The same
    # phrase in a row of an active practice is still live (the control).
    rows = ('| [a](practices/a.md) | deduplicated | `b` | It hit the three '
            'team sets. |\n| [c](practices/c.md) | active | the team sets |\n')
    out = hits('MAP.md', rows)
    cases.append(('a table row with a finished status is history; an active '
                  'row is still live', [n for n, *_ in out] == [2], out))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('retired words are found in live text and left alone in history',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_leak_gate_note_says_when_no_private_list_is_declared():
    """With no private blocklist declared anywhere -- no individual set in
    the user config, no requireVocabulary, no private source in
    precedent.json -- the leak gate's allowlist note says none is declared
    and that nothing is missing; with one declared but unreadable, it still
    says that list was not reachable.

    Found 2026-10-17 by the very deep check's install rehearsal: a new
    person with no individual set was told their "private blocklist ... was
    not reachable" and to set PRECEDENT_GIT_TOKEN, sending them to look for
    a list they never had. Decision chosen by the session under Morgan's
    delegation of 2026-10-17 ("Fix the other issues you found including the
    checks that never run. Tell me what you decide. I will be offline so
    don't wait for me. Approved, act, and Booked.").

    Negative control, measured 2026-10-17: before the fix both runs print
    the not-reachable note.
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-leak-none-'))
    genv = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
                GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    try:
        repo = tmp / 'repo'
        (repo / 'tools').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'leak_gate.py', repo / 'tools' / 'leak_gate.py')
        shutil.copy(ROOT / 'tools' / 'leak-blocklist.default.txt',
                    repo / 'tools' / 'leak-blocklist.default.txt')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        (repo / 'ok.md').write_text('nothing sensitive here\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True, env=genv)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'base'],
                       capture_output=True, env=genv)

        def gate(home):
            e = {k: v for k, v in genv.items()
                 if k not in ('PRECEDENT_LEAK_BLOCKLIST', 'PRECEDENT_USER_CONFIG')}
            e['HOME'] = str(home)
            r = subprocess.run([sys.executable, str(repo / 'tools' / 'leak_gate.py')],
                               capture_output=True, text=True, cwd=str(repo), env=e,
                               timeout=300)
            return r.returncode, r.stdout + r.stderr
        new = tmp / 'new-person'
        new.mkdir()
        rc, out = gate(new)
        cases.append(('nothing declared: the note says none is declared, nothing is missing, '
                      'and asks for no token',
                      rc == 0 and 'no private blocklist is declared here' in out
                      and 'not reachable' not in out and 'PRECEDENT_GIT_TOKEN' not in out,
                      failure_detail(out, 500)))
        old = tmp / 'has-a-set'
        (old / '.config' / 'precedent').mkdir(parents=True)
        (old / '.config' / 'precedent' / 'config.json').write_text(json.dumps(
            {'individual': {'path': str(tmp / 'absent-individual')}}), encoding='utf-8')
        rc, out = gate(old)
        cases.append(('CONTROL: an individual set is named but its list is not on disk: '
                      'still "not reachable", with the remedy',
                      'not reachable in this session' in out, failure_detail(out, 500)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_repo_reference_allowlist():
    """A private repo name cannot reach a public tree by nobody predicting it.

    The vocabulary layer is a list of literal strings, so it blocks the names
    somebody remembered and nothing else. On 2026-09-07 that failed in both
    directions in one day: it missed a private repository nobody had listed,
    and it blocked two names that had since become public, forcing 88 hits
    clearable only by deleting content about public files.

    So for REPOSITORY REFERENCES the default is inverted. An owner is declared
    private-by-default and every `owner/name` mention is refused unless an
    `allow` line gives a reason. The set of names you may mention is small and
    known; the set of repositories you might create is unbounded. Inverting
    puts the work where the knowledge is.

    It runs in the PUSH gate, offline, which is the whole reason it is a
    declaration rather than an API call -- very_deep_check.py's visibility
    audit asks GitHub, and a push gate cannot.

    Proven on its first real run: it caught an abandoned private fork named in
    this public tree that nobody had ever blocklisted, and its own manual's
    example, which had used a real account name.
    """
    import tempfile
    gate = ROOT / 'tools' / 'leak_gate.py'
    if not gate.exists():
        not_applicable('the repo-reference allowlist refuses an undeclared name',
                       'tools/leak_gate.py is not present here')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    import importlib
    lg = importlib.import_module('leak_gate')

    cases = []
    with tempfile.TemporaryDirectory() as td:
        bl = pathlib.Path(td) / 'blocklist.txt'
        bl.write_text(
            '# visibility-audit: private-owner acct -- repos private by default\n'
            '# visibility-audit: allow acct/named-on-purpose -- declared source\n'
            r'\bSomeSecretTerm\b' + '\n', encoding='utf-8')
        owners, allowed = lg.parse_repo_policy(bl)

        cases.append(('the private-owner declaration parses',
                      owners.get('acct', '').startswith('repos private')))
        cases.append(('the allow declaration parses, with its reason',
                      allowed.get(lg._ref_key('acct/named-on-purpose')) == 'declared source'))

        def refs(text):
            return [r for _n, r in lg.repo_ref_hits(text, owners, allowed)]

        cases.append(('an UNDECLARED repo under that owner is refused',
                      refs('see acct/secret-thing for details')
                      == ['acct/secret-thing']))
        cases.append(('a github.com URL form is refused too',
                      refs('https://github.com/acct/other-thing')
                      == ['acct/other-thing']))

        # The must-not-fire cases: without these the rule is unusable.
        cases.append(('an ALLOWED repo passes',
                      refs('see acct/named-on-purpose here') == []))
        cases.append(('another owner is untouched',
                      refs('see someoneelse/anything here') == []))
        cases.append(('a fraction or ratio is not a repo reference',
                      refs('16px/1.45 and 287/290 and 10/10') == []))
        cases.append(('a path segment is not a reference',
                      refs('vendor/acct/thing and a/b/c') == []))
        cases.append(('NO owner declared means the rule is inert',
                      lg.repo_ref_hits('acct/secret-thing', {}, {}) == []))

        # GRAMMAR OF THE DIRECTIVES THEMSELVES. Both patterns are
        # single-line, so a reason on the next comment line drops the whole
        # directive -- silently, until 2026-09-11. Every case below was
        # measured before the check was written, including the two that must
        # NOT fire: characterizing the behaviour is what says which of these
        # is a bug and which is the documented cost.
        def errs(body):
            f = pathlib.Path(td) / f'g{abs(hash(body))}.txt'
            f.write_text(body + '\n', encoding='utf-8')
            return lg.repo_policy_errors(f)

        good = ('# visibility-audit: private-owner acct -- one line, fine\n'
                '# visibility-audit: allow acct/one -- reason on the same line')
        cases.append(('a well-formed policy file produces no errors',
                      errs(good) == []))

        # Direction 1: a line that announces a directive and parses as neither.
        e = errs(good + '\n# visibility-audit: allow acct/two')
        cases.append(('a directive with no ` -- reason` is an error, '
                      'naming its line number',
                      len(e) == 1 and e[0][0] == 3 and 'separator' in e[0][2]))

        e = errs(good + '\n# visibility-audit: allw acct/two -- typo in the verb')
        cases.append(('a TYPO\'d directive is an error, not an ordinary comment',
                      len(e) == 1 and e[0][0] == 3
                      and 'not a recognized directive' in e[0][2]))

        # The reason-on-the-next-line case: parses as NOTHING at all today.
        e = errs(good + '\n# visibility-audit: allow acct/two --'
                        '\n#   the reason, pushed onto its own line')
        cases.append(('a reason on the NEXT line is an error (the directive '
                      'would otherwise vanish silently)',
                      len(e) == 1 and e[0][0] == 3 and 'empty' in e[0][2]))

        # Direction 2, the must-not-fire half.
        # The WRAPPED reason parses, with the reason truncated at the line
        # end. Lossy, not unsafe, and nothing can tell it from a terse
        # reason -- so it must NOT be reported, and this locks that in.
        wrapped = (good + '\n# visibility-audit: allow acct/two -- a reason that '
                          'begins here and\n#   continues onto this second line')
        cases.append(('a WRAPPED reason is not an error (documented '
                      'truncation, not a failure)', errs(wrapped) == []))
        _o, _a = lg.parse_repo_policy(
            pathlib.Path(td) / f'g{abs(hash(wrapped))}.txt')
        cases.append(('...and it parses with the reason TRUNCATED at the '
                      'line end, which is why it is only a note',
                      _a.get(lg._ref_key('acct/two')) == 'a reason that begins here and'))

        cases.append(('a plain continuation comment is not flagged on its own',
                      errs(good + '\n#   just an ordinary comment line') == []))
        cases.append(('a doubly-commented doc EXAMPLE is not flagged',
                      errs(good + '\n#   # visibility-audit: allow owner/name '
                                  '-- why the exposure is accepted') == []))

        # Allow lines under a rule that never runs: every one of them reads as
        # a deliberate authorization and enforces nothing.
        e = errs('# visibility-audit: allow acct/one -- named on purpose\n'
                 '# visibility-audit: allow acct/two -- also on purpose')
        cases.append(('allow lines with NO private-owner line are an error',
                      len(e) == 1 and e[0][0] == 0 and 'INERT' in e[0][2]))
        cases.append(('...but allow lines WITH one are fine', errs(good) == []))

        # Regression guard for the shipped files: the hard failure must not
        # fire on this repo's own template or committed default. The template
        # placeholder `<name>` did not parse, so before this was doubly
        # commented a fresh copy failed the gate at the one moment nobody can
        # debug it.
        for _f in (ROOT / 'templates' / 'leak-blocklist.txt.template',
                   ROOT / 'tools' / 'leak-blocklist.default.txt'):
            if _f.exists():
                cases.append((f'the shipped {_f.name} parses clean',
                              lg.repo_policy_errors(_f) == []))

        # End to end: the gate EXITS on a malformed policy rather than
        # printing OK. A unit-level error list nobody acts on is the same
        # fail-open in a new place.
        bad = pathlib.Path(td) / 'malformed.txt'
        bad.write_text('# visibility-audit: private-owner acct --\n'
                       '#   reason on the next line\n'
                       r'\bSomeSecretTerm\b' + '\n', encoding='utf-8')
        rb = subprocess.run([sys.executable, str(gate)], capture_output=True,
                            text=True, cwd=str(ROOT), timeout=300,
                            env=dict(os.environ,
                                     PRECEDENT_LEAK_BLOCKLIST=str(bad)))
        cases.append(('a malformed policy file FAILS the gate', rb.returncode != 0))
        cases.append(('...and the failure names the line number',
                      'malformed.txt:1' in (rb.stdout + rb.stderr)))

        # ...and an inert rule SAYS SO. A clone that never declared an owner
        # would otherwise get a clean OK covering a rule that inspected
        # nothing -- the fail-open shape the vocabulary layer already learned
        # to announce.
        import tempfile as _tf
        quiet = pathlib.Path(_tf.mkdtemp()) / 'b.txt'
        quiet.write_text('\\bsome-term\\b\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(gate)], capture_output=True,
                           text=True, cwd=str(ROOT), timeout=300,
                           env=dict(os.environ, PRECEDENT_LEAK_BLOCKLIST=str(quiet)))
        cases.append(('an undeclared owner is ANNOUNCED, not silent',
                      'repo-reference allowlist is INERT' in (r.stdout + r.stderr)))

        # The template must not hand out permission for the one thing the
        # resolver refuses: a shared repo naming an individual source.
        tmpl = ROOT / 'templates' / 'leak-blocklist.txt.template'
        if tmpl.exists():
            t = tmpl.read_text(encoding='utf-8')
            cases.append(('the template tells an adopter to declare their own '
                          'account', 'private-owner YOUR-GITHUB-ACCOUNT' in t))
            cases.append(('and warns against pre-allowing an individual source',
                          'Do NOT pre-allow your INDIVIDUAL source' in t))
            cases.append(('and no allow line for an individual source is '
                          'shipped uncommented',
                          not re.search(r'^visibility-audit:\s*allow\s+\S+/precedent-individual',
                                        t, re.M)))

        # And it reaches the gate's own scan, not just the helper.
        units = [('f.md', 'f.md', 'text naming acct/undeclared-one here')]
        hits = lg.scan(units, [], (owners, allowed))
        cases.append(('scan() surfaces it as a hit',
                      any('acct/undeclared-one' in str(h) for h in hits)))
        cases.append(('and the hit says how to declare it',
                      any('visibility-audit: allow' in str(h) for h in hits)))

    failed = [n for n, ok in cases if not ok]
    check(f'the repo-reference allowlist refuses an undeclared private name '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_leak_gate_email_rule_skips_an_ipv4_host():
    """The email rule skips user@IPv4: the session proxy's git remote,
    http://local_proxy@127.0.0.1:PORT/git/owner/repo, is no address.

    WHY. 2026-10-20: the gate refused that remote as an email address, and
    two files split the remote's string in two to get past it.
    They are whole again; this proves the rule, not the split, lets them
    through. Negative control, measured 2026-10-20 on the old pattern: the
    remote is refused and a split is the only way past."""
    gate = ROOT / 'tools' / 'leak_gate.py'
    if not gate.exists():
        not_applicable('the email rule skips an IPv4 host',
                       'tools/leak_gate.py is not present here')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    import importlib
    lg = importlib.import_module('leak_gate')
    sys.path.pop(0)

    def email_hits(text):
        return [h for h in lg.scan([('f.py', 'f.py', text)], [], private_names=set(),
                                   structural_exempt={}, public_email_domains={})
                if h[2] == 'an email address']

    at = '@'
    cases = [
        ('THE DISCRIMINATING CASE: the proxy remote is not an address',
         email_hits('http://local_proxy' + at + '127.0.0.1:9/git/o/r') == []),
        ('a bare user@IPv4 is not one either',
         email_hits('x' + at + '10.0.0.1') == []),
        ('negative control: a real address is still refused',
         len(email_hits('a.person' + at + 'corp-domain.com')) == 1),
        ('negative control: a domain that only starts with digits is still one',
         len(email_hits('x' + at + '10.0.0.1x.com')) == 1),
        ('no file in this tree splits the proxy remote to get past the rule',
         not any("'local_proxy' + '" + at in (ROOT / 'tools' / f).read_text(encoding='utf-8')
                 for f in ('verify_harness.py', 'precedent_vendor_engine.py'))),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'the email rule skips an IPv4 host ({len(cases)} stated cases)', not bad,
          '; '.join(bad))


def check_leak_gate_honors_a_declared_public_email_domain():
    """An address at a domain its owner declared public passes the email rule.

    2026-10-01: a public browser add-on's Firefox ID must be shaped like an
    address, and its real one sat at its owner's domain, in the manifest and
    in the store-listing copy. The built-in "an email address" rule refused
    every push, and nothing a consuming repo could declare reached it. The
    owner decided the domain is public; this is that decision, written once
    in the person's own blocklist, reaching the content rule and nothing
    else.
    """
    import tempfile
    gate = ROOT / 'tools' / 'leak_gate.py'
    if not gate.exists():
        not_applicable('the leak gate honors a declared public email domain',
                       'tools/leak_gate.py is not present here')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    import importlib
    lg = importlib.import_module('leak_gate')

    def email_hits(text, domains, blocklist=()):
        hits = lg.scan([('f.json', 'f.json', text)], list(blocklist),
                       private_names=set(), structural_exempt={},
                       public_email_domains=domains)
        return [h for h in hits if h[2] == 'an email address' or
                h[2].startswith('blocklist')]

    cases = []
    with tempfile.TemporaryDirectory() as td:
        bl = pathlib.Path(td) / 'blocklist.txt'
        bl.write_text(
            '# leak-gate: public-email-domain owner-domain.org -- '
            'the owner publishes it\n'
            '# leak-gate: public-email-domain no-reason.org --\n',
            encoding='utf-8')
        doms = lg.parse_public_email_domains(bl)
        cases.append(('the declaration parses, with its reason',
                      doms.get('owner-domain.org') == 'the owner publishes it'))
        cases.append(('a declaration with no reason declares nothing',
                      'no-reason.org' not in doms))
        cases.append(('and the gate refuses that line as unparsed',
                      [n for n, _l, _w in lg.repo_policy_errors(bl)] == [2]))

        # The prefix is the rollout: an engine that predates the directive
        # must read the line as a comment, never as an unparsed
        # `visibility-audit:` directive, or one line in a person's list
        # fails every older repo's push check.
        cases.append(('the directive does not wear the visibility-audit '
                      'prefix older engines refuse when unknown',
                      not any(lg.VIS_AUDIT_ANNOUNCE_RE.match(l.strip())
                              for l in bl.read_text().splitlines())))

        # Every address is assembled here, never written whole: this file
        # is in a public tree, and a whole one would trip the rule it tests.
        at = '@'
        addon = '"id": "an-addon' + at + 'owner-domain.org"'
        cases.append(('undeclared, the address is refused',
                      len(email_hits(addon, {})) == 1))
        cases.append(('declared, the address passes',
                      email_hits(addon, doms) == []))
        cases.append(('a subdomain of a declared domain passes',
                      email_hits('x' + at + 'mail.owner-domain.org', doms) == []))
        cases.append(('another domain is still refused',
                      len(email_hits('x' + at + 'other-domain.org', doms)) == 1))
        cases.append(('a lookalike ending is still refused',
                      len(email_hits('x' + at + 'notowner-domain.org', doms)) == 1))
        cases.append(('the declared domain inside a longer one is still refused',
                      len(email_hits('x' + at + 'owner-domain.org.evil.io', doms)) == 1))
        banned = [re.compile(r'owner-domain\.org')]
        cases.append(('a blocklist term naming the domain still refuses it',
                      len(email_hits(addon, doms, banned)) == 1))
        cases.append(('scan with no declaration argument refuses, as before',
                      len([h for h in lg.scan([('f', 'f', addon)], [],
                                              private_names=set(),
                                              structural_exempt={})
                           if h[2] == 'an email address']) == 1))
    for name, ok in cases:
        check(f'leak gate public email domain: {name}', ok)


def check_leak_gate_scans_the_consuming_repo():
    """The leak gate scans the repo it is INSTALLED IN, not its own vendor dir.

    Vendored at <repo>/process/upstream/tools/, `parents[1]` is
    process/upstream/ -- so in the repositories that actually hold private
    content, this gate scanned BestPractice's own mirrored tree and reported
    it clean while the consuming repo's tracked files were never opened.
    Found 2026-09-07 refreshing a real consumer: "893 unit(s) ... clean",
    which is BestPractice's file count, in a repo tracking 1060.
    precedent_check.py hit exactly this and fixed it the same way months
    earlier; nobody carried the fix across to the gate whose whole job is
    keeping private content out of a public push.

    And the second half, which the first made necessary: the gate's premise
    is publication -- its own refusal says "a push is a publication" -- which
    is false in a private consumer. Scanning one for real lit up 111 hits for
    naming the owner's own private repositories inside a repository that is
    itself private. Shipping the ROOT fix alone would have turned every
    private consumer's gate red over content never at risk, and a gate that
    cries wolf in every install is one people switch off.

    An ABSENT visibility field is NOT private: omitting it counts as public
    here as everywhere else in the engine, because the failure is asymmetric
    -- assuming public costs false hits, assuming private costs a permanent
    publication.
    """
    import tempfile, json as _json, shutil as _shutil
    gate = ROOT / 'tools' / 'leak_gate.py'
    if not gate.exists():
        not_applicable('the leak gate scans the consuming repo',
                       'tools/leak_gate.py is not present here')
        return

    def _consumer(base, visibility, extra_file=None):
        """A repo with the gate VENDORED, as a real install has it."""
        vend = base / 'process' / 'upstream' / 'tools'
        vend.mkdir(parents=True)
        _shutil.copy2(gate, vend / 'leak_gate.py')
        for name in ('leak-blocklist.default.txt',):
            src = ROOT / 'tools' / name
            if src.exists():
                _shutil.copy2(src, vend / name)
        cfg = {'format_version': 1, 'sources': []}
        if visibility:
            cfg['visibility'] = visibility
        (base / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        (base / 'own-file.md').write_text(extra_file or '# just this repo\n',
                                          encoding='utf-8')
        subprocess.run(['git', '-C', str(base), 'init', '-q'], capture_output=True)
        for c in (['config', 'user.email', 'harness@example.com'],
                  ['config', 'user.name', 'Harness']):
            subprocess.run(['git', '-C', str(base)] + c, capture_output=True)
        subprocess.run(['git', '-C', str(base), 'add', '-A'], capture_output=True)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        subprocess.run(['git', '-C', str(base), 'commit', '-qm', 'base'],
                       capture_output=True, env=env)
        return base

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # ROOT resolves to the CONSUMER, not process/upstream.
        pub = _consumer(tmp / 'pub', 'public')
        r = subprocess.run(
            [sys.executable, str(pub / 'process' / 'upstream' / 'tools' / 'leak_gate.py')],
            capture_output=True, text=True, cwd=str(pub), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1'))
        out = r.stdout + r.stderr
        # The consumer tracks a handful of files; BestPractice tracks ~900.
        # Any count in the hundreds means it scanned the vendored tree.
        m = re.search(r'(\d+) unit\(s\)', out)
        counted = int(m.group(1)) if m else -1
        tracked = len([x for x in subprocess.run(
            ['git', '-C', str(pub), 'ls-files'], capture_output=True,
            text=True).stdout.splitlines() if x])
        cases.append(('a vendored gate scans the CONSUMING repo, not its own '
                      'vendor directory', 0 <= counted <= tracked))
        cases.append(('and the count matches the consumer, not upstream',
                      counted != 893))

        # A private consumer stands down, and SAYS it inspected nothing.
        priv = _consumer(tmp / 'priv', 'private')
        r = subprocess.run(
            [sys.executable, str(priv / 'process' / 'upstream' / 'tools' / 'leak_gate.py')],
            capture_output=True, text=True, cwd=str(priv), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1'))
        out = r.stdout + r.stderr
        cases.append(('a private consumer stands the gate down',
                      'NOT APPLICABLE' in out and r.returncode == 0))
        cases.append(('and says plainly that it is not a pass',
                      'NOT a pass' in out))
        # Since 2026-09-28 that is the upstream source's own leak gate: a
        # loader install has no practice_audit.py, which the message used
        # to name.
        cases.append(('and names what still guards the export path',
                      'scans it on arrival' in out))

        # A private repo holding its OWN private blocklist -- the individual
        # source -- stands down; a public one holding it still fails.
        (priv / 'leak-blocklist.txt').write_text('secretterm\n', encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(priv / 'process' / 'upstream' / 'tools' / 'leak_gate.py')],
            capture_output=True, text=True, cwd=str(priv), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                     PRECEDENT_LEAK_BLOCKLIST=str(priv / 'leak-blocklist.txt')))
        out = r.stdout + r.stderr
        cases.append(('a private repo holding its own blocklist stands down '
                      'rather than failing', 'NOT APPLICABLE' in out
                      and 'INSIDE' not in out and r.returncode == 0))
        (pub / 'leak-blocklist.txt').write_text('secretterm\n', encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(pub / 'process' / 'upstream' / 'tools' / 'leak_gate.py')],
            capture_output=True, text=True, cwd=str(pub), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                     PRECEDENT_LEAK_BLOCKLIST=str(pub / 'leak-blocklist.txt')))
        out = r.stdout + r.stderr
        cases.append(('a public repo holding the blocklist still fails, naming '
                      'it', r.returncode != 0 and 'INSIDE' in out))

        # ABSENT visibility must NOT be read as private.
        none = _consumer(tmp / 'none', None)
        r = subprocess.run(
            [sys.executable, str(none / 'process' / 'upstream' / 'tools' / 'leak_gate.py')],
            capture_output=True, text=True, cwd=str(none), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1'))
        out = r.stdout + r.stderr
        cases.append(('an ABSENT visibility field still scans -- omitting it '
                      'is not a way to switch the gate off',
                      'NOT APPLICABLE' not in out))

    failed = [n for n, ok in cases if not ok]
    check(f'the leak gate scans the consuming repo, and stands down only '
          f'where nothing is published ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_leak_gate_reads_a_declared_visibility_before_the_owner_default():
    """THE BUG (2026-10-14). The leak gate's failure line in
    precedent-shared-writing, whose precedent.json declares it public, read
    "is private (its owner is declared private by default), so this push
    publishes nothing by itself": own_repo_private read only the owner
    policy. A session reading that line can take a real leak in a public
    tree as harmless. Since then the repository's own declaration comes
    first and the owner default only when it declares nothing.

    A. a repo declaring public under a private-by-default owner is public,
       and says why;
    B. CONTROL: the same repo declaring nothing takes the owner default;
    C. a repo declaring private under an owner not declared private is
       private."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as lg
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='leak-visibility-'))
    policy = ({'privowner': 'test'}, {})
    cases = []
    try:
        def repo(name, owner, visibility):
            r = tmp / name
            r.mkdir()
            subprocess.run(['git', 'init', '-q', str(r)], capture_output=True)
            subprocess.run(['git', '-C', str(r), 'remote', 'add', 'origin',
                            f'https://github.com/{owner}/{name}.git'],
                           capture_output=True)
            cfg = {} if visibility is None else {'visibility': visibility}
            (r / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            return r
        a = lg.own_repo_private(policy, repo('pub', 'privowner', 'public'))
        cases.append(('A. declared public under a private-by-default owner is public',
                      a[0] == 'privowner/pub' and a[1] is False and 'public' in a[2], a))
        b = lg.own_repo_private(policy, repo('undeclared', 'privowner', None))
        cases.append(('B. CONTROL: declaring nothing takes the owner default',
                      b[1] is True and 'owner' in b[2], b))
        c = lg.own_repo_private(policy, repo('priv', 'openowner', 'private'))
        cases.append(('C. declared private under an open owner is private',
                      c[1] is True and 'private' in c[2], c))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'the leak gate reads a declared visibility before the owner default '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))

def check_outbound_privacy_gate_refuses_and_scan_finds():
    """A request leaving the machine never carries the person's private
    details (outbound-privacy; Alex, 2026-10-18: "Do all of the above").
    The gate refuses an outbound request holding a private term and logs it
    with the term masked; lets a clean one and a non-network command
    through; the scan finds a past outbound call holding a term in a
    transcript and in an agent's transcript beside it, and the Stop hook
    reports it once -- once per session, not once per repository whose hook
    runs in it (2026-10-20: one tool call reported from two repositories)."""
    import tempfile, json as _json, os as _os
    name = 'the outbound-privacy gate refuses private details and the scan finds them'
    gate = ROOT / 'tools' / 'outbound-privacy-gate.sh'
    if not gate.exists():
        not_applicable(name, 'tools/outbound-privacy-gate.sh is absent')
        return
    cases = []
    email = 'someone.private@example.org'
    env = dict(_os.environ, CLAUDE_CODE_USER_EMAIL=email)
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        for d in ('tools', '.precedent'):
            (tmp / d).mkdir()
        for f in ('outbound_privacy_gate.py', 'outbound_privacy_scan.py',
                  'outbound-privacy-gate.sh', 'outbound-privacy-scan.sh'):
            (tmp / 'tools' / f).write_text((ROOT / 'tools' / f).read_text(encoding='utf-8'), encoding='utf-8')
        (tmp / '.precedent' / 'private_terms.txt').write_text('# a comment\n12 Hidden Lane\nab\n', encoding='utf-8')

        def run_gate(tool, tool_input):
            p = subprocess.run(['bash', str(tmp / 'tools' / 'outbound-privacy-gate.sh')],
                               input=_json.dumps({'tool_name': tool, 'tool_input': tool_input}),
                               capture_output=True, text=True, cwd=tmp, env=env)
            return p.returncode, p.stdout + p.stderr

        rc, out = run_gate('Bash', {'command': f'curl -A "x ({email})" https://example.com'})
        cases.append(('a curl carrying the email is refused', rc == 2 and 'OUTBOUND PRIVACY' in out, failure_detail(out, 200)))
        log = tmp / '.precedent' / 'outbound_refusals.jsonl'
        text = log.read_text(encoding='utf-8') if log.exists() else ''
        cases.append(('the refusal is logged with the term masked',
                      '[private term 1]' in text and email not in text, failure_detail(text, 200)))
        rc, _ = run_gate('WebSearch', {'query': 'parcels to 12 hidden lane'})
        cases.append(('a search holding a listed term is refused, case ignored', rc == 2))
        rc, _ = run_gate('Bash', {'command': 'curl https://example.com'})
        cases.append(('a clean request goes through', rc == 0))
        rc, _ = run_gate('Bash', {'command': f'echo {email} > notes.txt'})
        cases.append(('a command that reaches no network goes through', rc == 0))
        rc, _ = run_gate('WebFetch', {'url': 'https://example.com/ab'})
        cases.append(('a term under 5 characters is ignored', rc == 0))
        # 2026-10-31 (and 2026-10-20): a local commit carries the author's
        # address and the session trailer's URL; neither makes it outbound.
        commit = (f'git add a && git -c user.email="{email}" commit -q '
                  f'--author="A <{email}>" -F - <<\'EOF\'\nsubject\n\n'
                  'Claude-Session: https://claude.ai/code/session_x\nEOF\n'
                  'git log -1')
        rc, out = run_gate('Bash', {'command': commit})
        cases.append(('a local commit with the address and a trailer URL goes through',
                      rc == 0, failure_detail(out, 200)))
        rc, _ = run_gate('Bash', {'command': f'git commit -m "see https://a.b" '
                                             f'--author="A <{email}>"'})
        cases.append(('...and with the URL in -m', rc == 0))
        rc, _ = run_gate('Bash', {'command': commit + f'\ncurl -H "From: {email}" https://example.com'})
        cases.append(('NEGATIVE CONTROL: a commit followed by a curl carrying the '
                      'address is still refused', rc == 2))
        rc, _ = run_gate('Bash', {'command': f"python3 - <<'EOF'\nimport urllib.request\n"
                                             f"urllib.request.urlopen('https://x/?{email}')\nEOF"})
        cases.append(('NEGATIVE CONTROL: an inline script that reaches the network '
                      'with the address is still refused', rc == 2))
        sess = tmp / 'proj' / 'sess.jsonl'
        (tmp / 'proj' / 'sess' / 'subagents').mkdir(parents=True)
        call = lambda cid, cmd: _json.dumps({'timestamp': '2026-10-18T00:00:00Z', 'message': {
            'role': 'assistant', 'content': [{'type': 'tool_use', 'id': cid, 'name': 'Bash',
                                              'input': {'command': cmd}}]}}) + '\n'
        refused = _json.dumps({'timestamp': '2026-10-18T00:00:01Z', 'message': {
            'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 't3',
                                         'is_error': True, 'content':
                                         'PreToolUse:Bash hook error: OUTBOUND PRIVACY: this '
                                         'request would send the person\'s private details off '
                                         'the machine'}]}}) + '\n'
        sess.write_text(call('t1', 'ls')
                        + call('t3', f'curl -H "From: {email}" https://example.com')
                        + refused, encoding='utf-8')
        (tmp / 'proj' / 'sess' / 'subagents' / 'agent-x.jsonl').write_text(
            call('t2', f'wget --header "From: {email}" https://example.com'), encoding='utf-8')

        def run_scan(repo=tmp):
            p = subprocess.run(['bash', str(repo / 'tools' / 'outbound-privacy-scan.sh')],
                               input=_json.dumps({'transcript_path': str(sess)}),
                               capture_output=True, text=True, cwd=repo, env=env)
            return p.returncode, p.stdout + p.stderr

        rc, out = run_scan()
        cases.append(("the Stop hook reports an agent's past request, masked",
                      rc == 2 and 'wget' in out and email not in out, failure_detail(out, 200)))
        cases.append(('NEGATIVE CONTROL: a request the gate refused is not reported as sent',
                      'curl' not in out, failure_detail(out, 200)))
        rc, _ = run_scan()
        cases.append(('and reports it once', rc == 0))
        # A second repository in the same session: its own copy of the hook,
        # its own .precedent/, the same transcript.
        other = tmp / 'other'
        for d in ('tools', '.precedent'):
            (other / d).mkdir(parents=True)
        for f in ('outbound_privacy_gate.py', 'outbound_privacy_scan.py',
                  'outbound-privacy-scan.sh'):
            (other / 'tools' / f).write_text((tmp / 'tools' / f).read_text(encoding='utf-8'),
                                             encoding='utf-8')
        (other / '.precedent' / 'private_terms.txt').write_text(
            (tmp / '.precedent' / 'private_terms.txt').read_text(encoding='utf-8'), encoding='utf-8')
        rc, out = run_scan(other)
        cases.append(("another repository's hook in the same session stays quiet",
                      rc == 0, failure_detail(out, 200)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_leak_gate_reads_other_clones_as_themselves_inside_a_hook():
    """Inside a git hook the leak gate still reads every other clone as
    itself, lets a repository name itself, and says where the push goes.

    2026-10-10, a private consumer: a push wrote the repository's own name
    into one of its files and the gate refused it as a "private repository
    name"; it said "Precedent is a branch of a PUBLIC repo" of a private
    one; and it gave the blocklist clone's HEAD as the commit being pushed.
    A git hook sets GIT_DIR, and every `git -C <other clone>` then answered
    about the repository being pushed. The fixture sets GIT_DIR as a hook
    does: a sibling clone's private name must still be caught.
    """
    import tempfile
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        base = {**_fixture_git_env(), 'GIT_CONFIG_GLOBAL': str(tmp / 'gitconfig'),
                'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        def g(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=base)
        clones = tmp / 'clones'
        def clone(name, files):
            d = clones / name
            d.mkdir(parents=True)
            g(d, 'init', '-q', '-b', 'main')
            g(d, 'remote', 'add', 'origin', f'https://github.com/acme/{name}.git')
            for rel, text in files.items():
                (d / rel).parent.mkdir(parents=True, exist_ok=True)
                (d / rel).write_text(text, encoding='utf-8')
            g(d, 'add', '-A'); g(d, 'commit', '-qm', f'{name} base')
            return d
        blk = clone('blocks', {'leak-blocklist.txt':
            '# visibility-audit: private-owner acme -- every repo private\n'
            '# visibility-audit: auto-cover-bare-names on -- names must not leak\n'
            'zzfixturetermzz\n'})
        (blk / 'note.txt').write_text('second\n', encoding='utf-8')
        g(blk, 'add', '-A'); g(blk, 'commit', '-qm', 'second')
        blk_head = g(blk, 'log', '-1', '--format=%h').stdout.strip()
        clone('hiddenproj', {'a.txt': 'x\n'})
        work = clone('ownrepo', {})
        (work / 'tools').mkdir()
        for f in ('leak_gate.py', 'leak-blocklist.default.txt'):
            shutil.copy2(ROOT / 'tools' / f, work / 'tools' / f)
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'tools')
        start = g(work, 'rev-parse', 'HEAD').stdout.strip()
        hook_env = dict(base, GIT_DIR=str(work / '.git'),
                        PRECEDENT_LEAK_BLOCKLIST=str(blk / 'leak-blocklist.txt'))
        def gate(rev):
            return subprocess.run([sys.executable, 'tools/leak_gate.py', '--range',
                                   f'{start}..{rev}'], cwd=str(work), env=hook_env,
                                  capture_output=True, text=True, timeout=120)
        (work / 'own.md').write_text('This is the ownrepo notes file.\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'own name')
        r = gate('HEAD')
        cases.append(('a repository writing its own name is not refused',
                      r.returncode == 0, failure_detail(r.stdout + r.stderr, 500)))
        (work / 'other.md').write_text('See hiddenproj for the rest.\n', encoding='utf-8')
        g(work, 'add', '-A'); g(work, 'commit', '-qm', 'other name')
        pushed = g(work, 'log', '-1', '--format=%h').stdout.strip()
        r = gate('HEAD')
        out = r.stdout + r.stderr
        cases.append(('THE DISCRIMINATING CASE: inside a hook, a sibling private '
                      'clone\'s name is still caught', r.returncode != 0
                      and 'private repository name "hiddenproj"' in out, failure_detail(out, 600)))
        cases.append(('the failure says this repository is private, not that a '
                      'push to it is a publication', 'acme/ownrepo is private' in out
                      and 'PUBLIC' not in out, failure_detail(out, 400)))
        cases.append(('the blocklist clone\'s HEAD is its own, not the pushed commit',
                      f'HEAD {blk_head}' in out and f'HEAD {pushed}' not in out,
                      failure_detail(out, 400)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the leak gate reads other clones as themselves inside a hook '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))


def check_retired_team_level_spares_ordinary_english():
    """The retired "team (as a level)" word must not catch "team" meaning a
    group of people, which its own registry entry says is not retired: its
    pattern matched "at the team level" (2026-10-17 very deep check). THE
    CASE: ordinary English passes. CONTROLS: the level sense is still
    caught, hyphenated or not."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import our_language as ol
    retired = [r for r in ol.load_retired() if r[0] == 'team (as a level)']
    pats = retired[0][2] if retired else []
    hit = lambda t: any(p.search(t) for p in pats)
    cases = [
        ('the retired word is registered', bool(pats), ''),
        ('THE CASE: "decided at the team level" is ordinary English',
         not hit('decided at the team level'), ''),
        ('nor "on a team level"', not hit('work on a team level'), ''),
        ('CONTROL: "a team-level practice" is still caught',
         hit('a team-level practice'), ''),
        ('CONTROL: "kept at team level" and "the team level needs a rule" '
         'are still caught', hit('kept at team level')
         and hit('the team level needs a rule'), ''),
    ]
    bad = [c[0] for c in cases if not c[1]]
    check(f'the retired team-level word spares ordinary English '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_leak_gate_reads_the_written_private_repo_list():
    """The leak gate refuses a private repository's bare name from the
    person's written list (private-repos.txt beside their blocklist), not
    only from clones on this disk (2026-10-14: a session with no clone of a
    private consumer wrote its name into a public engine docstring on
    2026-10-06). THE DISCRIMINATING CASE is a listed repository with no
    clone anywhere on disk."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import leak_gate as lg
    cases = []
    with tempfile.TemporaryDirectory() as top:
        # One level down, so the siblings local_clone_refs surveys are this
        # fixture's own and never the machine's /tmp (2026-10-14: GitHub's
        # runner holds an unreadable directory there).
        td = pathlib.Path(top) / 'repo'
        td.mkdir()
        bl = td / 'leak-blocklist.txt'
        bl.write_text('# visibility-audit: private-owner someone -- theirs\n',
                      encoding='utf-8')
        cases.append(('no list file, no listed repositories',
                      lg.listed_private_refs(bl) == set(), ''))
        (td / lg.PRIVATE_REPOS_NAME).write_text(
            '# a comment\nsomeone/secret-garden  # trailing comment\n'
            'not a ref line\nother/elsewhere\n', encoding='utf-8')
        refs = lg.listed_private_refs(bl)
        cases.append(('owner/name lines are read, comments and prose skipped',
                      refs == {('someone', 'secret-garden'), ('other', 'elsewhere')},
                      refs))
        owners, allowed = lg.parse_repo_policy(bl)
        pats = lg.auto_private_name_patterns(refs, owners, allowed)
        hits = lg.scan([('NOTES.md', 'NOTES.md', 'a session in secret-garden read it\n')],
                       [], (owners, allowed), pats)
        cases.append(('THE DISCRIMINATING CASE: a listed name with no clone is refused',
                      any('secret-garden' in str(h) for h in hits), hits))
        cases.append(('a listed repository under an owner nobody declared private is not',
                      [n for _p, n in pats] == ['secret-garden'], pats))
        cases.append(('no clone on disk, so nothing is named for adding',
                      lg.unlisted_private_clones(td, bl, owners, allowed) == [], ''))
        # Simulated, since a chmod does not stop root: the sibling's `.git`
        # answers PermissionError, as /tmp/snap-private-tmp/.git did.
        locked = pathlib.Path(top) / 'locked'
        locked.mkdir()
        real_exists = pathlib.Path.exists

        def exists(self, *a, **k):
            if self == locked / '.git':
                raise PermissionError(13, 'Permission denied', str(self))
            return real_exists(self, *a, **k)
        pathlib.Path.exists = exists
        try:
            refs_ok = isinstance(lg.local_clone_refs(td), set)
        except OSError as e:
            refs_ok = e
        finally:
            pathlib.Path.exists = real_exists
        cases.append(('an unreadable sibling is skipped, never a crash', refs_ok is True,
                      refs_ok))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the leak gate reads the written private-repository list ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_push_check_walks_every_commit_it_publishes():
    """The push check runs the leak gate over every commit the push would
    publish, messages included, not only over the tree they end at.

    THE INCIDENT (2026-10-10). One commit named a private repository in a
    test fixture; the next scrubbed it. The landing's quick checks ran the
    leak gate on the final tree, which was clean, and the first commit went
    out to a public branch with the name in it. The DISCRIMINATING CASE is
    the first: no planned check walked the commits before. The others prove
    the range is what the push publishes -- a leak a later commit scrubbed
    still fails, and once those commits are on a remote nothing is
    re-judged -- and that a tree already passed does not skip it.
    The fixture owns its repositories (fixture-owns-its-state)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    cases = []
    planned = {n: a for n, a, _r in ppc.plan(ROOT, tier=ppc.BASIC)[1]}
    walk = planned.get('leak_gate_commits') or []
    cases.append(('THE DISCRIMINATING CASE: a basic push plans the leak gate '
                  'over the commits it publishes',
                  walk[-2:] == ['--range', ppc.LEAK_COMMITS_RANGE]
                  and str(walk[1]).endswith('leak_gate.py'), walk))
    cases.append(('a tree that already passed still walks the commits',
                  'leak_gate_commits' in ppc.HISTORY_CHECKS, ''))
    cases.append(('the full tier walks them too',
                  'leak_gate_commits' in {n for n, _a, _r in ppc.plan(ROOT)[1]}, ''))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-leakwalk-'))
    try:
        env = {**_fixture_git_env(), 'HOME': str(tmp / 'home')}
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        (tmp / 'home').mkdir()
        g = lambda *a: subprocess.run(['git', '-C', str(tmp / 'repo'), *a],
                                      env=env, capture_output=True, text=True)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(tmp / 'origin.git')], env=env, capture_output=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp / 'repo')],
                       env=env, capture_output=True)
        repo = tmp / 'repo'
        (repo / 'tools').mkdir()
        for name in ('leak_gate.py', 'leak-blocklist.default.txt'):
            shutil.copy(ROOT / 'tools' / name, repo / 'tools' / name)
        (repo / 'ok.md').write_text('fine\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('remote', 'add', 'origin', str(tmp / 'origin.git'))
        g('push', '-q', 'origin', 'main')
        home_path = '/' + 'Users/someone/notes'       # assembled: see check_leak_gate_fires
        (repo / 'notes.md').write_text(f'see {home_path}\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'notes')
        (repo / 'notes.md').write_text('clean\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'scrub')

        def gate(*args):
            return subprocess.run([sys.executable, 'tools/leak_gate.py', *args],
                                  cwd=str(repo), env=env, capture_output=True,
                                  text=True).returncode
        cases.append(('CONTROL: the final tree is clean', gate() == 0, ''))
        cases.append(('a leak a later commit scrubbed fails the commit walk',
                      gate('--range', ppc.LEAK_COMMITS_RANGE) == 1, ''))
        g('push', '-q', 'origin', 'main')
        cases.append(('once the commits are on a remote, they are not re-judged',
                      gate('--range', ppc.LEAK_COMMITS_RANGE) == 0, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the push check walks every commit it publishes '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_leak_gate_refuses_a_fresh_container():
    """A repo that declares a private source must not pass the leak gate with
    the vocabulary layer unrun, even with no git config anywhere.

    THE INCIDENT, 2026-09-08, reported by a session after it had already
    pushed: it could attach neither private source, so there was no blocklist
    to load; no `precedent.requireVocabulary` existed in that fresh container
    to make the absence fatal; the gate printed PARTIAL, **exited 0**, and the
    push went through into a public repository with only the structural rules
    applied. "The check silently did not run" and "the check passed" were the
    same exit code -- the exact failure the requireVocabulary docstring says
    must not happen. The setting simply was not reachable where it mattered.

    THE FIX UNDER TEST is that the requirement is now DERIVED from
    precedent.json, which is tracked and therefore survives a fresh
    container, as well as configured. So the discriminating pair is cases 1
    and 2: the same environment, the same absent config, differing only in
    whether precedent.json declares a private source.

    Case 3 is the half a careless fix breaks -- continuous integration has no
    private list by design and must still pass, opting out BY NAME.
    Case 4 asserts the refusal names the RIGHT reason: the message used to
    assert the git-config trigger unconditionally, which after this change
    would send a reader to a setting that was not set and could not be unset
    (practice: control-asserts-which-failure).
    """
    import tempfile, shutil

    def run(cwd, *extra, blocklist=None):
        env = {k: v for k, v in os.environ.items() if k != 'PRECEDENT_LEAK_BLOCKLIST'}
        env['PRECEDENT_ALLOW_ANY_AUTHOR'] = '1'
        # HOME points at an empty directory, or ~/.config/precedent/config.json
        # injects this MACHINE's individual source into every fixture -- which
        # resolves, which makes every case read as "a private source resolved"
        # regardless of what the fixture declared. Caught while writing the
        # declared-but-unresolved case, and it is the fourth instance of this
        # shape in one day (practice: fixture-owns-its-state).
        env['HOME'] = str(_fixture_home)
        if blocklist:
            env['PRECEDENT_LEAK_BLOCKLIST'] = blocklist
        r = subprocess.run([sys.executable, str(cwd / 'tools' / 'leak_gate.py'), *extra],
                           capture_output=True, text=True, cwd=str(cwd), env=env)
        return r.returncode, r.stdout + r.stderr

    def build(tmp, sources):
        repo = pathlib.Path(tmp) / 'r'
        (repo / 'tools').mkdir(parents=True)
        # precedent_resolve.py and its companions, or _private_sources_resolved
        # cannot import it, falls back to DECLARATION, and every case below
        # reads the same -- the distinction under test would not be exercised
        # at all while the check still passed.
        _seed_consumer_engine(repo / 'tools',
                              extra=('leak_gate.py',
                                     'leak-blocklist.default.txt',
                                     'routing_scope.json',
                                     'glossary_terms.json'))
        (repo / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'public', 'sources': sources}),
            encoding='utf-8')
        (repo / 'README.md').write_text('# ordinary\n\nnothing private here.\n',
                                        encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        # No `precedent.requireVocabulary` is set anywhere: that IS the
        # fresh-container shape this check is about.
        return repo

    _fixture_home = pathlib.Path(tempfile.mkdtemp())

    cases = []
    UNIVERSAL = [{'level': 'universal', 'name': 'precedent', 'path': '.'}]
    # A private source that RESOLVES: its directory exists and carries a
    # practices/ tree, so the session can read its text.
    PRIVATE = UNIVERSAL + [{'level': 'team', 'name': 'precedent-team-x',
                            'path': '../precedent-team-x'}]

    # Each `tmp` below is a throwaway git repo torn down at the end of its
    # own block -- manual mkdtemp + _rmtree_retrying rather than
    # `tempfile.TemporaryDirectory()`'s own cleanup, which crashed this
    # entire check once on a CI runner over a transient ENOTEMPTY
    # (_rmtree_retrying's own docstring has the incident).
    tmp = tempfile.mkdtemp()
    try:
        repo = build(tmp, PRIVATE)
        (pathlib.Path(tmp) / 'precedent-team-x' / 'practices').mkdir(parents=True)
        (pathlib.Path(tmp) / 'precedent-team-x' / 'practices' / 'zz.md').write_text(
            '---\nslug: zz\ntitle: Z\ntier: on-demand\nseverity: default\n'
            'applies_to: ["**"]\noccasion: "t"\nindex_clause: "t"\n'
            'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
            'overrides: null\nadded: null\napproved_by: "h"\n---\n\n'
            '## Rule\nZ.\n\n## Story\nZ.\n', encoding='utf-8')
        rc, out = run(repo)
        cases.append(('a private source that RESOLVED, with no blocklist, '
                      'refuses -- its text is in context, so a private term '
                      'could reach the tree through it',
                      rc == 1 and 'FAIL' in out, failure_detail(out, 400)))
        cases.append(('and the refusal says the source RESOLVED, not merely '
                      'that precedent.json declares one',
                      'RESOLVED this session' in out, failure_detail(out, 400)))
        rc3, out3 = run(repo, '--structural-only')
        cases.append(('the same repo PASSES under --structural-only, so CI '
                      'still works', rc3 == 0, failure_detail(out3, 300)))
        cases.append(('and still says the private half did not run, rather '
                      'than reporting a clean bill',
                      'private ones were not' in out3, failure_detail(out3, 300)))
    finally:
        _rmtree_retrying(tmp)

    tmp = tempfile.mkdtemp()
    try:
        repo = build(tmp, UNIVERSAL)
        rc2, out2 = run(repo)
        cases.append(('a repo declaring NO private source is unaffected -- it '
                      'never had a vocabulary layer to lose, so this did not '
                      'become a gate everybody has to appease',
                      rc2 == 0, failure_detail(out2, 300)))
    finally:
        _rmtree_retrying(tmp)

    # THE CORRECTION, and the case that matters most: declared but NOT
    # resolved. The first version of this gate refused here too, which blocked
    # a real session out of pushing at all -- its commit "dies with the
    # container". The session that could not attach the source never read its
    # text and has nothing from it to leak; refusing bought no safety and cost
    # repo-is-memory. The path below simply does not exist.
    tmp = tempfile.mkdtemp()
    try:
        repo = build(tmp, UNIVERSAL + [{'level': 'team', 'name': 'precedent-team-absent',
                                        'path': '../precedent-team-absent'}])
        rc4, out4 = run(repo)
        cases.append(('a private source DECLARED but not resolved ALLOWS the '
                      'push -- the session could not read it, so it has '
                      'nothing from it to leak',
                      rc4 == 0, failure_detail(out4, 400)))
        cases.append(('and it says so loudly, naming the residual risk it '
                      'does NOT cover rather than reporting a clean bill',
                      'nothing from them to leak' in out4
                      and 'some other way' in out4, failure_detail(out4, 400)))
    finally:
        _rmtree_retrying(tmp)

    _rmtree_retrying(str(_fixture_home))

    ok = all(c[1] for c in cases)
    check(f'the leak gate requires the blocklist when a private source '
          f'RESOLVED, and not merely when one is declared ({len(cases)} '
          f'stated cases, config absent throughout)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


def check_structural_only_actually_drops_the_private_half():
    """`--structural-only` must make the gate's verdict INDEPENDENT of
    whether a private blocklist is reachable -- that is the whole point of
    the flag, and it is what lets a CI runner and a developer's machine
    agree on the same tree.

    THE INCIDENT, 2026-09-21, and it took three corrections in one day.
    The flag originally only cleared whether the vocabulary layer was
    REQUIRED, never whether it was APPLIED. The first fix dropped BOTH
    blocklist halves, which over-shot: the default list is committed and
    publishable, so CI can and should keep running it. The second fix
    dropped the private half correctly -- and a sibling session measuring
    the flag against a real practice set STILL saw private patterns fire.
    There were three routes, not one:

      1. the vocabulary patterns themselves (the one that was fixed),
      2. the repo-reference policy and its owner rules, read from the SAME
         private file, plus the auto-derived bare-name patterns, which come
         from the sibling CLONES ON THIS DISK, and
      3. the self-heal, which reloaded the FULL blocklist as soon as a run
         had any hit at all -- so the flag worked on a clean tree and
         stopped working on exactly the runs whose verdict mattered.

    ROUTE 3 IS WHY THIS PLANTS A TREE THAT FAILS UNDER THE FLAG, not only
    one that passes -- though see the note at its own case: the reload is
    guarded, and this fixture cannot yet make it fire. A detector verified against a clean tree alone is
    indistinguishable from a broken one: under the flag a clean tree never
    reaches the self-heal, so route 3 stays invisible. The discriminating
    fixture trips a DEFAULT-list pattern -- reaching the self-heal -- while
    also containing a name only the PRIVATE list knows. If the reload comes
    back, that name is in the output. It must not be."""
    import tempfile

    _home = pathlib.Path(tempfile.mkdtemp())

    def run(cwd, *extra, blocklist=None):
        env = {k: v for k, v in os.environ.items()
               if k != 'PRECEDENT_LEAK_BLOCKLIST'}
        env['PRECEDENT_ALLOW_ANY_AUTHOR'] = '1'
        env['HOME'] = str(_home)          # practice: fixture-owns-its-state
        if blocklist:
            env['PRECEDENT_LEAK_BLOCKLIST'] = blocklist
        r = subprocess.run(
            [sys.executable, str(cwd / 'tools' / 'leak_gate.py'), *extra],
            capture_output=True, text=True, cwd=str(cwd), env=env)
        return r.returncode, r.stdout + r.stderr

    cases = []
    tmp = tempfile.mkdtemp()
    try:
        repo = pathlib.Path(tmp) / 'r'
        (repo / 'tools').mkdir(parents=True)
        _seed_consumer_engine(repo / 'tools',
                              extra=('leak_gate.py',
                                     'leak-blocklist.default.txt',
                                     'routing_scope.json',
                                     'glossary_terms.json'))
        (repo / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'public',
             'sources': [{'level': 'universal', 'name': 'precedent',
                          'path': '.'}]}), encoding='utf-8')

        # A word the COMMITTED default list already matches, read out of the
        # shipped file rather than hardcoded -- so editing that list cannot
        # silently leave this check trying to trip a pattern that is gone.
        _default = (repo / 'tools' / 'leak-blocklist.default.txt').read_text(
            encoding='utf-8')
        _seed = None
        for _line in _default.splitlines():
            _m = re.match(r'^\\b([a-z]{3,})', _line.strip())
            if _m:
                _seed = _m.group(1)
                break
        cases.append(('the fixture found a literal word in the shipped '
                      'DEFAULT list to trip -- without one, route 3 is '
                      'never reached and this check would pass while '
                      'proving nothing',
                      _seed is not None, f'default list: {failure_detail(_default, 300)!r}'))
        _seed = _seed or 'zzzznotfound'

        # The private list: a vocabulary pattern AND an owner declared
        # private-by-default, so the repo-reference rule has something to
        # enforce. Both come out of this one file, which is route 2.
        priv = pathlib.Path(tmp) / 'private-blocklist.txt'
        priv.write_text(
            '# private fixture list\n'
            '# visibility-audit: private-owner fixtureowner -- fixture\n'
            r'\bZarquonProject\b' + '\n', encoding='utf-8')

        (repo / 'README.md').write_text(
            '# fixture\n\n'
            'ZarquonProject is a private name only the private list knows.\n'
            'fixtureowner/UndeclaredThing is an undeclared repo reference.\n'
            f'The word {_seed} is on the committed default list.\n',
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'],
                       capture_output=True)

        # DIRTY DIRECTION FIRST. Without the flag, with the private list
        # reachable, both private routes must fire -- otherwise the clean
        # direction below proves nothing at all about the flag.
        rc_full, out_full = run(repo, blocklist=str(priv))
        cases.append(('WITHOUT the flag the private vocabulary pattern '
                      'fires -- the control that makes route 1+3 mean '
                      'something',
                      rc_full == 1 and 'ZarquonProject' in out_full,
                      failure_detail(out_full, 500)))
        cases.append(('WITHOUT the flag the private repo-reference policy '
                      'fires too -- the control for route 2',
                      'UndeclaredThing' in out_full, failure_detail(out_full, 500)))

        rc_so, out_so = run(repo, '--structural-only', blocklist=str(priv))
        cases.append(('WITH the flag the run still FAILS -- it tripped the '
                      'committed default list, which must keep biting in CI',
                      rc_so == 1, failure_detail(out_so, 500)))
        cases.append(('...and names the default-list word, so the failure '
                      'is the one intended', _seed in out_so, failure_detail(out_so, 500)))
        # ROUTE 3 IS GUARDED BUT NOT EXERCISED HERE, said plainly rather
        # than counted as covered: _try_refresh_private_blocklist_clone()
        # returns False in this fixture (there is no clone to fast-forward),
        # so the reload never runs even with the guard removed. What this
        # case proves is route 1 on a run that HAS hits. Exercising the
        # reload needs a real git clone as the private source; filed rather
        # than claimed (practice: speculation-is-marked).
        cases.append(('ROUTE 1: the private vocabulary name is NOT named, '
                      'on a run that HAD a hit -- the state in which the '
                      'flag used to quietly stop working',
                      'ZarquonProject' not in out_so, failure_detail(out_so, 800)))
        cases.append(('ROUTE 2: no undeclared-repo finding, since the owner '
                      'policy lives in the private file this run did not '
                      'read', 'UndeclaredThing' not in out_so,
                      failure_detail(out_so, 800)))
        cases.append(('the output says the private half was skipped rather '
                      'than reporting a clean bill over it',
                      'private half skipped' in out_so, failure_detail(out_so, 500)))

        # THE REPRODUCIBILITY CLAIM ITSELF: the same flag with no private
        # list reachable at all -- what a CI runner sees -- must reach the
        # same verdict on the same tree.
        rc_ci, out_ci = run(repo, '--structural-only')
        cases.append(('same flag with NO private list reachable gives the '
                      'SAME exit code -- the verdict does not depend on the '
                      'machine, which is the only reason the flag exists',
                      rc_ci == rc_so, f'{rc_ci} vs {rc_so}: {failure_detail(out_ci, 400)}'))
    finally:
        _rmtree_retrying(tmp)
        _rmtree_retrying(str(_home))

    ok = all(c[1] for c in cases)
    check(f'--structural-only drops every route the private half reaches, '
          f'including on a run that HAS hits ({len(cases)} stated cases)',
          ok, '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


