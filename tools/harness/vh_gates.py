# The harness tests for the reply check and the hook gates
#
# tools/harness/vh_gates.py -- part of the verification harness:
# the reply check and the hook gates.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


@_without_session_id
def check_reply_gate_names_work_not_yet_landed():
    """Committed, pushed, and sitting on a branch nobody merges from is a
    state the stop hook cannot report and the person kept paying for.

    Morgan, 2026-09-21 (strength: decided): "if there are changes that are
    committed but NOT YET ON main/precedent-beta-v01/primary-branch-in-that-
    repo, then the Boildown section MUST MUST tell me that and recommend I
    do that, so I don't miss doing it."

    TWO THINGS ALREADY LOOKED AND NEITHER ANSWERS THIS. The stop hook
    refuses a turn ending with uncommitted or unpushed work -- but it fires
    AFTER the reply is composed, so it can only reject the turn and cost the
    reply twice, never put a line in the Boildown. And "pushed" is not the
    question: a feature branch can be pushed while the work sits where
    nothing merges from.

    So this runs in the reply gate, before the reply, and asks whether HEAD
    is ahead of the branch the repo actually lands work on -- `base_branch`
    from precedent.json, falling back to origin/HEAD.
    """
    import precedent_gate as pg
    import tempfile

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-unlanded-'))
    try:
        up = tmp / 'up.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(up)], check=True)
        repo = tmp / 'repo'
        subprocess.run(['git', 'init', '-q', '-b', 'trunk', str(repo)], check=True)

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True)
        g('config', 'user.name', 'Harness Fixture')
        # Assembled rather than written literally: the leak gate reads any
        # a@b as an email address and refuses the push, which it did to the
        # first version of this fixture. The address still has to be VALID
        # for `git commit` to accept it.
        g('config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
        (repo / 'precedent.json').write_text(
            json.dumps({'base_branch': 'trunk', 'sources': []}), encoding='utf-8')
        (repo / 'a.txt').write_text('one\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'first')
        g('remote', 'add', 'origin', str(up))
        g('push', '-q', '-u', 'origin', 'trunk')

        cases.append(('on the base branch, with nothing ahead, it says nothing',
                      pg._unlanded_work(repo, siblings=False) == [], str(pg._unlanded_work(repo, siblings=False))))

        # A commit on a feature branch -- the exact shape that gets forgotten.
        g('switch', '-q', '-c', 'feature')
        (repo / 'b.txt').write_text('two\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'second')
        got = pg._unlanded_work(repo, siblings=False)
        cases.append(('a commit on a feature branch is reported',
                      len(got) == 1, str(got)))
        cases.append(('it names the branch it is NOT on, which is the '
                      'actionable half',
                      bool(got) and "'trunk'" in got[0], str(got)))
        cases.append(('it counts the commits', bool(got) and ' 1 commit' in got[0],
                      str(got)))

        # OFF THE LADDER, A TRUNK NOT NAMED main. Off the ladder the gate
        # took the tier name `main` as the branch to compare against; in a
        # repository whose trunk is `trunk` (or master) origin/main does not
        # exist, nothing counted ahead, and the archive line passed over an
        # unmerged branch (a consumer whose trunk is master, 2026-10-25).
        _ladder_was = pg._ladder
        pg._ladder = lambda root: False
        try:
            off = pg._unlanded_work(repo, siblings=False)
        finally:
            pg._ladder = _ladder_was
        cases.append(('off the ladder, a trunk not named main is still the '
                      'branch the commit is NOT on', len(off) == 1
                      and "'trunk'" in off[0], str(off)))

        # PUSHING THE FEATURE BRANCH CHANGES NOTHING -- that is the whole
        # point, and it is what the stop hook's "unpushed" test misses.
        g('push', '-q', '-u', 'origin', 'feature')
        after = pg._unlanded_work(repo, siblings=False)
        cases.append(('pushing the feature branch does NOT clear it -- pushed '
                      'is not landed', len(after) == 1, str(after)))

        # Merging it does.
        g('switch', '-q', 'trunk'); g('merge', '-q', 'feature')
        g('push', '-q', 'origin', 'trunk')
        cases.append(('merging into the base branch clears it',
                      pg._unlanded_work(repo, siblings=False) == [], str(pg._unlanded_work(repo, siblings=False))))

        # A SQUASH merge clears it too. The squashed commit on trunk is new,
        # so the branch's own commits never become its ancestors and
        # rev-list counts them ahead forever; this reported NOT YET LANDED
        # on every turn after a real squash merge, 2026-09-24. Two commits,
        # so no per-commit patch-id can match the squash.
        g('switch', '-q', '-c', 'squashed')
        (repo / 'c.txt').write_text('three\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'third')
        (repo / 'c.txt').write_text('three, revised\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'fourth')
        g('switch', '-q', 'trunk'); g('merge', '-q', '--squash', 'squashed')
        g('commit', '-qm', 'squash of squashed')
        g('push', '-q', 'origin', 'trunk')
        g('switch', '-q', 'squashed')
        got = pg._unlanded_work(repo, siblings=False)
        cases.append(('a squash-merged branch is not reported', got == [], str(got)))

        # The base moving on with someone else's work must not bring the
        # false report back -- a whole-tree comparison would.
        g('switch', '-q', 'trunk')
        (repo / 'd.txt').write_text('elsewhere\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'unrelated')
        g('push', '-q', 'origin', 'trunk')
        g('switch', '-q', 'squashed')
        got = pg._unlanded_work(repo, siblings=False)
        cases.append(('it stays cleared after the base moves on', got == [], str(got)))

        # And real work on top of the squashed branch is still reported.
        (repo / 'c.txt').write_text('three, revised again\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'fifth')
        got = pg._unlanded_work(repo, siblings=False)
        cases.append(('a real commit after the squash is still reported',
                      len(got) == 1 and "'trunk'" in got[0], str(got)))
        g('switch', '-q', 'trunk')

        # A repo with no precedent.json still works, via origin/HEAD.
        (repo / 'precedent.json').unlink()
        g('add', '-A'); g('commit', '-qm', 'drop config')
        g('push', '-q', 'origin', 'trunk')
        cases.append(('a repo with no precedent.json does not crash',
                      isinstance(pg._unlanded_work(repo, siblings=False), list), 'raised'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_reply_gate_prints_a_note_from_a_set_tool():
    """precedent_gate._note_from_tool (2026-10-17): a set's reply_check.json
    may name, as `note_from_tool`, a tool the set ships here, and the reply
    gate prints what it says among the hard requirements. Made-up tool and
    names; the engine knows nothing of what the note is about.

    - a tool that prints a line: the line is printed, tagged with its source;
    - a tool that prints nothing, or fails: nothing, and the gate goes on;
    - a path outside tools/, or one that walks up with "..": never run;
    - the reply check itself treats the key as known, never as a rule this
      engine cannot evaluate."""
    import contextlib, io, tempfile
    import precedent_gate as pg
    import precedent_reply_check as prc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'tools').mkdir()
        (root / 'tools' / 'zz_note.py').write_text(
            'print("ZZ NOTE: the planted line")\n', encoding='utf-8')
        (root / 'tools' / 'zz_quiet.py').write_text('', encoding='utf-8')
        (root / 'tools' / 'zz_fails.py').write_text(
            'print("SHOULD NOT SHOW"); raise SystemExit(1)\n', encoding='utf-8')
        (root / 'outside.py').write_text(
            'open("ran-outside", "w").write("x")\nprint("OUTSIDE")\n',
            encoding='utf-8')
        for spec, want, what in (
                ({'run': 'tools/zz_note.py'}, ['ZZ NOTE: the planted line'],
                 'a tool that prints a line'),
                ({'run': 'tools/zz_quiet.py'}, [], 'a tool that prints nothing'),
                ({'run': 'tools/zz_fails.py'}, [], 'a tool that fails'),
                ({'run': 'tools/no_such.py'}, [], 'a tool that is not there'),
                ({'run': 'outside.py'}, [], 'a path outside tools/'),
                ({'run': 'tools/../outside.py'}, [], 'a path that walks up'),
                ({'run': 'tools/zz_note.py', 'args': [1]}, [], 'an argument that is not a string')):
            got = pg._note_from_tool(root, spec)
            cases.append((f'{what}: {want or "nothing"}', got == want, repr(got)))
        cases.append(('a path outside tools/ was never run',
                      not (root / 'ran-outside').exists(), 'it ran'))
        rc = root / 'repo'
        (rc / 'tools').mkdir(parents=True)
        (rc / 'tools' / 'zz_note.py').write_text(
            'print("ZZ NOTE from the set")\n', encoding='utf-8')
        out = io.StringIO()
        saved = prc.declared_requirements
        prc.declared_requirements = lambda _r: ([{
            '_source': 'shared/zz-set', 'note_from_tool': {'run': 'tools/zz_note.py'},
            'require_one_of': ['ZZ']}], [])
        try:
            with contextlib.redirect_stdout(out):
                pg._print_hard_requirements(rc)
        finally:
            prc.declared_requirements = saved
        cases.append(('the reply gate prints it among the hard requirements, '
                      'tagged with its source',
                      '- [shared/zz-set] ZZ NOTE from the set' in out.getvalue(),
                      failure_detail(out.getvalue(), 300)))
    cases.append(('the reply check knows the key, so it is never reported as a '
                  'rule this engine cannot evaluate',
                  prc._unknown_predicates({'note_from_tool': {}, 'practice': 'x'}) == [],
                  repr(prc._unknown_predicates({'note_from_tool': {}}))))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the reply gate prints a note a set\'s own tool gives it '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_reply_check_names_what_it_cannot_evaluate():
    """A reply requirement nobody can evaluate, and a source nobody can
    reach, must both say so.

    A source's reply_check.json is read LIVE from that source's checkout;
    the engine that evaluates it is VENDORED into the consuming repo. Two
    files, two routes, stale independently -- so a source can declare a
    BLOCKING requirement the consumer's older engine has never heard of.
    Measured 2026-09-21 against the requirement added the same day: current
    engine 1 violation, an engine without the branch 0 violations and total
    silence.

    The mirror case is the same failure from the other side: a source whose
    checkout is not on disk contributes nothing, and until the same day said
    nothing either, while this function's own docstring claimed it became a
    note. A set whose sibling BestPractice clone is missing gets none of
    universal's blocking reply rules and no hint of it.

    Reported, never enforced, in both directions: the REPLY is not what is
    wrong -- the vendored copy is old, or a clone is absent -- and refusing
    somebody's turn over that punishes the wrong thing at the wrong moment.
    """
    import precedent_reply_check as prc
    cases = []
    text = '## The Boildown\n\nnothing to see.\n'

    v = prc.violations(text, [{'practice': 'p', '_source': 'universal/precedent',
                               'require_some_future_predicate': [{'a': 1}]}])
    cases.append(('an unknown predicate produces a record',
                  len(v) == 1, str(v)))
    cases.append(('it is ADVISORY -- an old engine must not refuse a reply',
                  bool(v) and v[0].get('advisory') is True, str(v)))
    cases.append(('it names the remedy',
                  bool(v) and 'precedent_vendor_engine.py refresh' in v[0]['message'],
                  str(v)))
    cases.append(('it names the source',
                  bool(v) and 'universal/precedent' in v[0]['message'], str(v)))

    # Negative controls: every key a real requirement carries is known, and
    # a `_`-prefixed key is a comment, not a predicate.
    known = prc.violations(text, [{'practice': 'p', '_source': 'u',
                                   'require_heading_matching': 'boildown',
                                   'why': 'because', 'advisory': True,
                                   'checks_practice_at': 'practices/p.md'}])
    cases.append(('a fully-known requirement raises no unknown-predicate record',
                  not [x for x in known if x['kind'] == 'unknown_predicate'],
                  str(known)))
    # `inherits` is handled by _settle; until 2026-10-11 it was missing from
    # the known keys, and every turn printed "NOT ENFORCED HERE" for the
    # ladder set's rule that uses it, naming a refresh that changed nothing.
    inherited = prc.violations(text, [{'practice': 'p', '_source': 'u',
                                       'id': 'x', 'inherits': True,
                                       'require_heading_matching': 'boildown'}])
    cases.append(('a requirement that inherits raises no unknown-predicate '
                  'record', not [x for x in inherited
                                 if x['kind'] == 'unknown_predicate'],
                  str(inherited)))
    commented = prc.violations(text, [{'practice': 'p', '_source': 'u',
                                       'require_heading_matching': 'boildown',
                                       '_comment': 'a note to a human'}])
    cases.append(('an _-prefixed key is a comment, not an unknown predicate',
                  not [x for x in commented if x['kind'] == 'unknown_predicate'],
                  str(commented)))

    # THE LIVE REGISTRY must be complete: every predicate this engine has a
    # branch for is in KNOWN_REQUIREMENT_KEYS, or its own requirement would
    # report itself as unevaluable. Read from this module's source rather
    # than listed here, so adding a predicate cannot forget this.
    src = (ROOT / 'tools' / 'precedent_reply_check.py').read_text(encoding='utf-8')
    branches = set(re.findall(r"r\.get\('(require_[a-z_]+)'\)", src))
    missing = sorted(branches - set(prc.KNOWN_REQUIREMENT_KEYS))
    cases.append(('every predicate the engine evaluates is in '
                  'KNOWN_REQUIREMENT_KEYS', not missing, f'missing: {missing}'))

    # And the reachability half, against a real scratch config.
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-replysrc-'))
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent',
             'path': '../not-there'}]}),
            encoding='utf-8')
        _reqs, notes = prc.declared_requirements(str(fx))
        cases.append(('a source that is not on disk becomes a NOTE, not silence',
                      any('not on disk' in n for n in notes), str(notes)))
        cases.append(('the note says the requirement is unknown, not absent',
                      any('unknown, not' in n for n in notes), str(notes)))
        # 2026-10-20: a set's own checkout left the set out of its sources
        # (is_repository_itself), so its own reply rules were not in force
        # while working in it. Read once, at the set's level, after universal.
        st = tmp / 'a-set'
        (st / 'practices').mkdir(parents=True)
        (st / 'precedent-source.json').write_text(json.dumps(
            {'name': 'fixture-set', 'level': 'shared'}), encoding='utf-8')
        (st / 'precedent.json').write_text(json.dumps({'sources': []}),
                                           encoding='utf-8')
        (st / 'reply_check.json').write_text(json.dumps([
            {'practice': 'p', 'id': 'fixture-own-rule',
             'require_heading_matching': 'boildown'},
            {'practice': 'p', 'require_heading_matching': 'fixture-unkeyed'}]),
            encoding='utf-8')
        own, _notes = prc.declared_requirements(str(st))
        cases.append(("a set's own checkout loads the set's own reply rules",
                      [r.get('_source') for r in own
                       if r.get('id') == 'fixture-own-rule'] == ['shared/fixture-set'],
                      str([r.get('_source') for r in own])))
        (st / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'fixture-set', 'path': '.'}]}),
            encoding='utf-8')
        own, _notes = prc.declared_requirements(str(st))
        cases.append(('...and only once when it also declares itself',
                      len([r for r in own if r.get('require_heading_matching')
                           == 'fixture-unkeyed']) == 1,
                      str([r.get('_source') for r in own])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_declared_loss_unblocks_the_archive_line():
    """The exception Morgan's rule always carried, and the code never had --
    plus the marker route added after the phrase list turned out to be the
    same bug in a different shape.

    `require_container_safe_if_says` blocks "You can archive this session"
    whenever any checkout in the container holds work no remote has. Its own
    stated rule ends "(unless the work is intended to be lost!)", and its
    refusal text tells the reader to "say in the reply that it is meant to
    be lost" -- neither of which the code implemented. On 2026-09-23 a
    session said precisely that, in those words, in three consecutive
    replies, and was refused all three times; each one therefore closed by
    telling Morgan NOT to archive a session he could safely archive.

    A gate that forces a false statement has stopped being a safety
    mechanism, so the escape is real now -- and deliberately not a password.
    The reply must ALSO name every unsafe checkout, which is what keeps the
    2026-09-22 case that built the rule caught: a session that had never
    looked at the clone holding six unpushed commits could not have named
    it. Both halves are asserted here, and so is the failure of each half
    alone (practice: control-asserts-which-failure).

    THE MARKER ROUTE, ADDED LATER THE SAME DAY. The phrase list still made a
    session guess an exact string: a later session said the same substance
    ("safe to let the container reclaim them") in its own words, twice, and
    was refused both times for matching none of the four fixed phrases.
    Morgan: "That rule, as you read it, it makes no sense... if there's some
    way to force it to fire, that would be great." `unless_reply_declares_
    loss.marker` is a `**Checkout disposition:** NAME -- discard` line
    checked PER CHECKOUT, which is also strictly narrower than the phrase
    route's "name them all somewhere in the reply": a reply naming two
    checkouts and giving only one a disposition line must still fail, which
    the cases below assert as its own negative control."""
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location(
        '_rc_loss', ROOT / 'tools' / 'precedent_reply_check.py')
    try:
        rc = _ilu.module_from_spec(spec)
        spec.loader.exec_module(rc)
    except Exception as exc:                     # noqa: BLE001
        return (False, '', f'precedent_reply_check.py would not import: {exc}')

    rule = None
    for r, _n in [(x, None) for x in (rc.declared_requirements(str(ROOT))[0] or [])]:
        if r.get('require_container_safe_if_says'):
            rule = r
            break
    if rule is None:
        return (False, '', 'no rule declares require_container_safe_if_says')

    cases = [('the rule declares the escape phrases',
              bool((rule.get('unless_reply_declares_loss') or {}).get('phrases')),
              str(rule.get('unless_reply_declares_loss'))),
             ('the rule declares the marker template',
              bool((rule.get('unless_reply_declares_loss') or {}).get('marker')),
              str(rule.get('unless_reply_declares_loss'))),
             ('the key is known to the predicate reader',
              'unless_reply_declares_loss' in rc.KNOWN_REQUIREMENT_KEYS, '')]

    # Stub the scanner so this asserts the PREDICATE, not this container's
    # current disk -- which changes between runs and would make the case
    # pass or fail for reasons that have nothing to do with the logic.
    real = rc._unsafe_checkout_names
    try:
        rc._unsafe_checkout_names = lambda: ['precedent-individual', 'BestPractice']
        for label, text, want in (
            ('both named plus the phrase releases it',
             'the commits in ~/precedent-individual and in BestPractice are '
             'meant to be lost', True),
            ('a different declared phrase also works',
             '~/precedent-individual and BestPractice are intended to be '
             'discarded', True),
            ('naming only one of two does not',
             '~/precedent-individual is meant to be lost', False),
            ('the phrase alone, naming nothing, does not',
             'it is all meant to be lost', False),
            ('naming both without the phrase does not',
             'there is work in ~/precedent-individual and in BestPractice',
             False),
            ('the marker route, both dispositioned, releases it',
             '**Checkout disposition:** precedent-individual -- discard '
             '(superseded)\n**Checkout disposition:** BestPractice -- '
             'discard (test fixture)', True),
            ('the marker with an em-dash and no parenthetical still works',
             '**Checkout disposition:** precedent-individual — discard\n'
             '**Checkout disposition:** BestPractice — discard', True),
            ('the marker route is PER CHECKOUT -- one dispositioned line '
             'does not cover a second unsafe checkout the reply never '
             'mentions',
             '**Checkout disposition:** precedent-individual -- discard '
             '(superseded)', False),
            ('a disposition line for the wrong checkout name does not '
             'match the one that is actually unsafe',
             '**Checkout disposition:** some-other-repo -- discard\n'
             '**Checkout disposition:** BestPractice -- discard', False),
        ):
            got = rc._declares_loss(rule, text)
            cases.append((label, got is want, f'got {got}'))

        # A scanner that cannot say WHICH checkout leaves no way to verify
        # the naming half, so the escape must not be available at all.
        rc._unsafe_checkout_names = lambda: []
        cases.append(('an unreadable scanner closes the escape',
                      rc._declares_loss(rule, 'it is meant to be lost') is False,
                      'the escape opened with no names to check'))
    finally:
        rc._unsafe_checkout_names = real

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases, fail-closed among them',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_filename_separator_knows_names_it_did_not_choose():
    """Two names the separator check used to count as a directory's own
    choice, each planted beside a name using the other separator.

    - A file name a TOOL fixes (reply_check.json, read by
      precedent_reply_check.CONFIG_NAME, beside the very deep check's
      very-deep-check-decisions.json): the check now collects every
      *_NAME / *_FILENAME / *_MANIFEST constant from the engine's tools, so a
      set holding both is clean without an exemption. Before 2026-09-29 the
      list was hand-kept and held one name, and the individual set exempted
      its whole root to get past it.
    - An ISO date in a stem (REPORT_2026-09-19.md beside NOTES_X.md): the
      date's hyphens are ISO 8601's, not a separator anybody chose.
    Plus the loud half: a genuinely mixed pair still fails, and the message
    leads with fixing the cause, the exemption last.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def judge(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-separator-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        subprocess.run(['git', '-C', str(d), 'init', '-q'], capture_output=True)
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in pc._filename_separator(pc.Ctx(paths=['x'])))
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    cases = []
    fixed = pc.ENGINE_FIXED_FILENAMES
    cases.append(('the fixed names are read from the tools, not listed by hand',
                  {'reply_check.json', 'very-deep-check-decisions.json',
                   'close_detect.json', 'precedent-source.json'} <= fixed,
                  sorted(fixed)))
    out = judge({'reply_check.json': '[]\n',
                 'very-deep-check-decisions.json': '{}\n'})
    cases.append(('two tool-fixed names with different separators are clean',
                  out == '', out))
    out = judge({'spec/REPORT_2026-09-19.md': '# r\n',
                 'spec/NOTES_X.md': '# n\n'})
    cases.append(('an ISO date inside a stem is not a "-" separator',
                  out == '', out))
    # 2026-10-08: the hook scripts Update Vendors writes into a consumer's
    # tools/ are named by the engine, so beside the consumer's own
    # snake_case script they are no mix. Planted as a consumer: the
    # manifest lists them, and one of them is also on the engine's own
    # shipping list (the BestPractice half of the same answer).
    import precedent_vendor_engine as pve
    hooks = ['artifact-publish-gate.sh', 'commit-identity-once.sh',
             'wait-loop-gate.sh']
    manifest = json.dumps({'kind': 'consumer', 'files': hooks,
                           'hook_files': ['reply-gate.sh']}) + '\n'
    consumer = {'tools/ENGINE_MANIFEST.json': manifest,
                'tools/my_own_script.sh': '#!/bin/sh\n',
                '.claude/hooks/reply-gate.sh': '#!/bin/sh\n',
                '.claude/hooks/my_hook.sh': '#!/bin/sh\n'}
    consumer.update({f'tools/{h}': '#!/bin/sh\n' for h in hooks})
    cases.append(('the planted scripts are ones the engine really ships',
                  set(hooks) <= set(pve.HOOK_SCRIPT_FILES), hooks))
    out = judge(consumer)
    cases.append(('a consumer\'s vendored hyphenated scripts beside its own '
                  'snake_case one are clean', out == '', out))
    out = judge({'tools/my_own_script.sh': '#!/bin/sh\n',
                 'tools/my-other-script.sh': '#!/bin/sh\n',
                 'tools/ENGINE_MANIFEST.json': manifest})
    cases.append(('CONTROL: two repo-own scripts with different separators '
                  'still fail', 'tools/' in out and 'first fix the cause' in out,
                  out))
    # 2026-10-28: copy-in names each copied set's record after the set,
    # hyphens and all, beside process/'s own snake_case files.
    copied = {'precedent.json': json.dumps({'sources': [
                  {'level': 'shared', 'name': 'zz-set', 'path': 'process/zz-set',
                   'vendored': True}]}) + '\n',
              'process/manifest_zz-set.json': '{}\n',
              'process/decommissioned_paths.json': '{}\n'}
    out = judge(copied)
    cases.append(('a copied-in set\'s manifest beside process/\'s own '
                  'snake_case file is clean', out == '', out))
    out = judge(dict(copied, **{'precedent.json': '{"sources": []}\n'}))
    cases.append(('CONTROL: the same manifest with no copy-in declared is '
                  'still a mix', 'process/' in out, out))
    out = judge({'notes/a-b.md': '# a\n', 'notes/c_d.md': '# c\n'})
    cases.append(('a genuinely mixed directory still fails, leading with '
                  'the root fix', 'first fix the cause' in out
                  and out.index('first fix the cause') < out.index('Exempt'), out))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('filename-separator does not count names a tool fixes, files the '
          'engine ships, or an ISO date, and still refuses a real mix, root '
          'fix first',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_loader_block_advertises_only_live_channels():
    """A generated loader block must not name a channel this source does not fill.

    2026-09-06, precedent-team-tms: that set deleted its bootstrap
    placeholder, leaving one resident practice and no on-demand ones. Its
    generated block still carried an occasion index rendering as an empty
    ``` ``` box, and a standing instruction telling every session to
    consult that index and to run four `precedent_gate.py` commands --
    ALL FOUR of which exit FAIL there, because no practice in that set
    registers a gate. The three sections and the four gate names were
    emitted unconditionally, so the block described the ENGINE's channels
    rather than the ones the SOURCE actually fills.

    Why this is worse than cosmetic, and why it earns a check rather than
    a careful reading: the standing instruction is the one part of the
    block that tells a session what to DO. A session that runs a command
    the block advertised and gets FAIL back learns that the block is
    decorative, and that lesson applies to the parts that were true.

    Fixture-driven on purpose. This repo's own catalogue fills every
    channel, so nothing here can exercise the empty states -- which is
    precisely why the defect survived in a vendored copy for as long as it
    did. Each case was verified by reverting the fix and watching it fail.
    """
    import importlib.util, shutil, tempfile

    def fixture(root, *, tier=None, gates='[]'):
        (root / 'practices').mkdir(parents=True, exist_ok=True)
        (root / 'tools').mkdir(parents=True, exist_ok=True)
        (root / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        if tier is not None:
            (root / 'practices' / 'only.md').write_text(
                f'---\nslug: only\ntitle: Only\ntier: {tier}\nseverity: default\n'
                f'applies_to: ["**"]\noccasion: "doing the only thing"\n'
                f'gates: {gates}\nindex_clause: "the only clause"\nchecked_by: null\n'
                f'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
                f'added: 2026-09-06\napproved_by: "harness fixture"\n---\n'
                f'## Rule\nThe only rule.\n\n## Why\nx\n\n## Story\n\n## Install\nx\n',
                encoding='utf-8')
        return root

    def block_of(root):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                            '--agents-only', '--repo', str(root)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return f'BUILD FAILED: {(r.stdout + r.stderr)[:200]}'
        text = (root / 'AGENTS.md').read_text(encoding='utf-8')
        return text.split('BEGIN GENERATED: precedent-loader -->', 1)[1] \
                   .split('<!-- END GENERATED', 1)[0]

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-loader-empty-'))
    cases = []
    try:
        # (1) resident-only: precedent-team-tms's exact shape.
        b = block_of(fixture(tmp / 'resident_only', tier='resident'))
        cases.append(('a resident-only source gets no empty occasion index',
                      '## Occasion index' not in b, b.strip()[:160]))
        cases.append(('a resident-only source is not told to run a gate command '
                      'no practice registers',
                      'precedent_gate.py' not in b, b.strip()[:160]))
        cases.append(('a resident-only source is not told to consult an index '
                      'that does not exist',
                      'occasion index above' not in b, b.strip()[:160]))
        cases.append(('a resident-only source still gets its resident block',
                      '## Resident block' in b and 'The only rule.' in b, b.strip()[:160]))

        # (2) on-demand-only: the mirror image, an empty resident heading.
        b = block_of(fixture(tmp / 'ondemand_only', tier='on-demand'))
        cases.append(('an on-demand-only source gets no empty resident block heading',
                      '## Resident block' not in b, b.strip()[:160]))
        cases.append(('an on-demand-only source still gets its occasion index',
                      '## Occasion index' in b and 'the only clause' in b, b.strip()[:160]))

        # (3) no practices at all: a freshly bootstrapped source.
        b = block_of(fixture(tmp / 'empty'))
        cases.append(('a source with no practices says so, rather than emitting '
                      'three empty headings',
                      'no practices in force' in b and '## Standing instruction' not in b,
                      b.strip()[:160]))

        # (4) a live gate IS advertised -- the negative control for the three
        # "not advertised" cases above, which would all pass on a generator
        # that simply never mentioned a gate.
        b = block_of(fixture(tmp / 'gated', tier='on-demand', gates='["reply"]'))
        cases.append(('a source WITH a gated practice is told to run that gate',
                      'precedent_gate.py reply' in b, b.strip()[:160]))
        cases.append(('and is told only about that gate, not the whole vocabulary',
                      'merge|review' not in b and 'push' not in b, b.strip()[:160]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the generated loader block advertises only channels this source fills '
          f'({len(cases)} stated cases over four fixture shapes)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_gate_channel():
    """The gate channel, as stated cases against the real registry.

    A gate that loads nothing is the failure this channel is most prone to: a
    runbook step citing a gate nobody registered prints nothing and exits 0,
    which is indistinguishable from a gate that legitimately had nothing to
    say. Every case below was verified by breaking it -- an unknown gate name
    in a practice file, an emptied gate, a gate dropped from the vocabulary.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pg', ROOT / 'tools' / 'precedent_gate.py')
    pg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pg)

    vocab = pg.gate_vocabulary()
    by_gate = pg.practices_by_gate()
    cases = []

    cases.append(('the gate vocabulary is non-empty', bool(vocab)))

    declared = set()
    bad_names = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        fm, _sections = sp._read_practice_file(f)
        try:
            gates = json.loads(fm.get('gates', '[]') or '[]')
        except json.JSONDecodeError:
            bad_names.append(f"{fm['slug']}: gates is not a JSON array")
            continue
        for g in gates:
            declared.add(g)
            if g not in vocab:
                bad_names.append(f"{fm['slug']} names unknown gate {g!r}")
    cases.append(('every gate a practice names is in the closed vocabulary',
                  not bad_names, '; '.join(bad_names[:4])))

    empty = [g for g in vocab if not by_gate.get(g)]
    cases.append(('no gate in the vocabulary is empty -- an empty gate is a step '
                  'that loads nothing and looks like it worked',
                  not empty, f"empty: {empty}" if empty else ''))

    unused = sorted(set(vocab) - declared)
    cases.append(('no gate is declared but unreachable', not unused,
                  f"declared with no practice: {unused}" if unused else ''))

    # the command itself, run as a subprocess -- the channel as a caller uses it
    # A practice another resolved source replaces (`overrides:`) is not in
    # force and is rightly left out -- present only where that source
    # resolves, as a person's individual set does beside this checkout.
    #
    # EVERY GATE RUN STARTS AT ONCE, AND EACH IS RUN ONCE (2026-10-31). The
    # reply gate takes about 10 s, and this function ran it three times
    # (here, again for the --brief comparison, and push again for the
    # SessionStart case below), one after another. precedent_gate.py writes
    # nothing, so the runs are independent: all of them start here, the
    # Stop-hook pair runs while they work, and the --brief and push cases
    # read the same `reply` and `push` results this loop judges.
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_gate as _pg

    def _gate_popen(*args):
        return subprocess.Popen([sys.executable, str(ROOT / 'tools' / 'precedent_gate.py'),
                                 *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=str(ROOT))
    _gate_procs = {g: _gate_popen(g) for g in sorted(vocab)}
    _gate_procs[('no-such-gate',)] = _gate_popen('no-such-gate')
    _gate_procs[('reply', '--brief')] = _gate_popen('reply', '--brief')
    _gate_runs = {}

    # The Stop-hook pair below, started now so it runs beside the gates:
    # the two runs stay one after the other, in the order they always ran.
    import tempfile, threading
    _stop_runs = {}

    def _stop_pair():
        with tempfile.TemporaryDirectory() as _td:
            _t = pathlib.Path(_td) / 't.jsonl'
            _t.write_text(json.dumps({'type': 'user', 'message': {
                'role': 'user', 'content': 'hi'}}) + '\n', encoding='utf-8')
            for k, payload in (('with', json.dumps({'transcript_path': str(_t)})),
                               ('without', '{}')):
                _stop_runs[k] = subprocess.run(
                    ['bash', str(ROOT / 'tools' / 'stop-reply-check.sh')], input=payload,
                    capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    _stop_thread = threading.Thread(target=_stop_pair, daemon=True)
    _stop_thread.start()

    def _gate_run(key):
        if key not in _gate_runs:
            if key not in _gate_procs:
                _gate_procs[key] = _gate_popen(*((key,) if isinstance(key, str) else key))
            proc = _gate_procs[key]
            out, err = proc.communicate()
            _gate_runs[key] = subprocess.CompletedProcess(proc.args, proc.returncode,
                                                          out, err)
        return _gate_runs[key]

    for g in sorted(vocab):
        r = _gate_run(g)
        replaced = _pg.resolved_gate_practices(str(ROOT), g)[3]
        ok = r.returncode == 0 and all(s in r.stdout for s in by_gate[g]
                                       if s not in replaced)
        cases.append((f'`precedent_gate.py {g}` returns every practice registered to it', ok,
                      (r.stdout + r.stderr).strip()[:120] if not ok else ''))

    r = _gate_run(('no-such-gate',))
    cases.append(('an unknown gate fails loudly rather than printing nothing',
                  r.returncode != 0 and 'no gate named' in (r.stdout + r.stderr)))

    # the push gate must actually be wired, or it is a channel nobody reaches
    hook = ROOT / 'templates' / 'hooks' / 'pre-push'
    cases.append(('the push gate is wired into templates/hooks/pre-push',
                  hook.exists() and 'precedent_gate' in hook.read_text(errors='ignore')))

    # the reply gate must actually be wired too -- a 2026-09-04 gate audit
    # found it was not: routing_scope.json names this gate's moment as "the
    # stop hook", but the only stop-hook script any adapter ships never
    # called precedent_gate.py at all. Checked in both the template a
    # dependent repo installs and this repo's own instantiated copy, so
    # neither can drift back to cited-only without this case catching it.
    # Since 2026-10-17 this repo's own .claude/hooks/ copy is the engine
    # stub, which runs tools/<same name>; its wiring is the script it runs.
    def _hook_text(hook):
        text = hook.read_text(errors='ignore') if hook.exists() else ''
        if 'PRECEDENT HOOK STUB' in text:
            real = ROOT / 'tools' / hook.name
            return real.read_text(errors='ignore') if real.exists() else ''
        return text

    for stop_hook in (ROOT / 'tools' / 'stop-reply-check.sh',
                      ROOT / '.claude' / 'hooks' / 'stop-reply-check.sh'):
        cases.append((f'the reply gate is wired into {stop_hook.relative_to(ROOT)}',
                      stop_hook.exists() and 'precedent_gate' in _hook_text(stop_hook)))

    # 2026-09-13: the reply gate gained a second invocation point and a
    # blocking half, and both are wiring claims that can drift back to
    # cited-only exactly as the first one did.
    #
    # UserPromptSubmit is where the gate reaches the reply it is ABOUT. Stop
    # fires after the reply is composed and its output is not fed back to the
    # model on a clean exit, so the advisory print had never once reached the
    # turn it was meant to govern.
    for settings in (ROOT / 'templates' / 'harness' / 'claude-code' / 'settings.json',
                     ROOT / '.claude' / 'settings.json'):
        data = json.loads(settings.read_text(encoding='utf-8'))
        wired = [h.get('command', '') for blk in data.get('hooks', {}).get('UserPromptSubmit', [])
                 for h in blk.get('hooks', [])]
        cases.append((f'the reply gate is wired at UserPromptSubmit in '
                      f'{settings.relative_to(ROOT)}',
                      any('reply-gate.sh' in c for c in wired),
                      f'UserPromptSubmit wires {wired}'))
    for hook in (ROOT / 'tools' / 'reply-gate.sh',
                 ROOT / '.claude' / 'hooks' / 'reply-gate.sh'):
        cases.append((f'{hook.relative_to(ROOT)} exists and is executable -- a '
                      f'hook a settings.json declares and disk does not have is '
                      f'the failure the harness reports as nothing at all',
                      hook.is_file() and os.access(hook, os.X_OK)))
    for stop_hook in (ROOT / 'tools' / 'stop-reply-check.sh',
                      ROOT / '.claude' / 'hooks' / 'stop-reply-check.sh'):
        cases.append((f'the BLOCKING reply check is called from '
                      f'{stop_hook.relative_to(ROOT)}',
                      'precedent_reply_check' in _hook_text(stop_hook)))

    # 2026-09-15: the Stop hook's own advisory print of the reply gate went
    # unbriefed for over a year -- `precedent_gate.py reply` with no
    # `--brief`, printing every reply-gate practice's full text on every
    # single Stop, unconditionally, on top of the SAME list reply-gate.sh
    # already prints in brief form at the START of the turn. Nothing above
    # caught it: 'precedent_gate' and 'precedent_reply_check' are both
    # substrings of the un-briefed call too. Found from a person describing
    # the result plainly -- a wall of text at the end of every session.
    for stop_hook in (ROOT / 'tools' / 'stop-reply-check.sh',
                      ROOT / '.claude' / 'hooks' / 'stop-reply-check.sh'):
        cases.append((f'{stop_hook.relative_to(ROOT)} calls the reply gate '
                      f'--brief, not the full Rules, on every Stop',
                      'precedent_gate.py" reply --brief' in _hook_text(stop_hook)))

    # 2026-10-30: the Stop hook ran the gate without passing on the
    # transcript its payload names, so a refused stop always said "no
    # transcript reached this gate" beside the compact requirement -- read
    # as a path lost to a worker restart. Planted transcript: the sentence
    # is gone; no path in the payload (the control): it is back.
    no_path = 'no transcript reached this gate'
    _stop_thread.join()
    _runs = _stop_runs
    cases.append(('the Stop hook hands the gate the transcript its payload names',
                  no_path not in _runs['with'].stdout + _runs['with'].stderr
                  and no_path in _runs['without'].stdout + _runs['without'].stderr,
                  f"with: {failure_detail(_runs['with'].stderr, 300)!r}; without: "
                  f"{failure_detail(_runs['without'].stderr, 300)!r}"))

    # --brief is the per-turn form, and its promise is that it is CHEAP. A
    # regression that printed full Rules there would not fail any case above.
    r_full = _gate_run('reply')
    r_brief = _gate_run(('reply', '--brief'))
    cases.append(('`precedent_gate.py reply --brief` is much smaller than the '
                  'full gate -- it fires on every prompt',
                  r_brief.returncode == 0
                  and 0 < len(r_brief.stdout.split()) < len(r_full.stdout.split()) / 2,
                  f'{len(r_brief.stdout.split())} words vs {len(r_full.stdout.split())}'))

    # The session-guarantee reminder, added 2026-09-14. A session whose
    # SessionStart hooks never ran reads instructions it cannot satisfy, and
    # tools/precedent_session_check.py has been able to say so since
    # 2026-09-08 -- via AGENTS.md's banner, which a session can skip, and did
    # (gotchas/gotcha-2026-09-13-pip-install-cmarkgfm-or-tools-doclint-py-s-strikethrough-che.md). The gate is the route it cannot skip, so these
    # cases assert the PRINTED TEXT in both directions rather than the call
    # (practice: control-asserts-which-failure).
    spec_c = importlib.util.spec_from_file_location(
        '_psck', ROOT / 'tools' / 'precedent_session_check.py')
    psck = importlib.util.module_from_spec(spec_c)
    spec_c.loader.exec_module(psck)

    real_checks = psck.checks
    try:
        psck.checks = lambda offline=True: [
            ('a guarantee that holds', True, ''),
            ('a guarantee that does not', False, 'the effect is absent. More.'),
            ('a guarantee nobody could measure', None, 'undetermined'),
        ]
        block = psck.remind(prefix='precedent gate')
        cases.append(('remind() names the broken guarantee, its first sentence '
                      'and the full-report command',
                      'a guarantee that does not' in block
                      and 'the effect is absent' in block
                      and 'precedent_session_check.py' in block,
                      block[:120]))
        cases.append(('remind() stays silent about a guarantee that HOLDS and '
                      'about one nobody could measure -- a nag that fires on '
                      '"cannot tell" is a nag that gets ignored',
                      'a guarantee that holds' not in block
                      and 'nobody could measure' not in block, block[:120]))
        psck.checks = lambda offline=True: [('all fine', True, '')]
        cases.append(('remind() prints NOTHING when every guarantee is in '
                      'effect -- the control, and the normal case',
                      psck.remind() == '', repr(psck.remind())[:80]))
    finally:
        psck.checks = real_checks

    # ...and the gate actually carries it, asserted against whatever this
    # container's real state is, so the case is meaningful in both a healthy
    # session and a broken one.
    broken = psck.failing_guarantees()
    r_gate = _gate_run('push')
    said = 'SessionStart guarantee(s) NOT in effect' in r_gate.stdout
    cases.append(('a gate reports broken SessionStart guarantees, and says '
                  'nothing when there are none',
                  said == bool(broken),
                  f'{len(broken)} broken, gate {"did" if said else "did not"} say so'))

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'gate-triggered channel ({len(cases)} stated cases: closed vocabulary, '
          f'no empty gate, every gate resolves, unknown gates fail loudly, '
          f'push and reply actually wired, and a gate reports a session whose '
          f'SessionStart guarantees are down)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_reply_gate_sees_every_source():
    """The gate channel must serve EVERY source, not just the repo's own tree.

    Until 2026-09-13 precedent_gate.py read exactly one directory --
    `<root>/practices/` -- so in any repo whose sources resolve as clones
    rather than through precedent_materialize.py, a team, individual or
    repo-local practice declaring `gates: ["reply"]` had no invocation point
    at all. Measured here that day: three individual practices about how a
    reply is written were registered to the reply gate and reached a session
    only through the occasion index, which fires only if the session
    recognises the occasion. A gate whose whole promise is reach-without-
    judgment kept that promise for one level and broke it for three.

    Every case is run against a fixture repo built here, owning all of its
    own state (practice: fixture-owns-its-state) -- no user config, no
    sibling clone, nothing inherited from the container -- and each is
    verified by its negative control: remove the second source and the same
    command must stop naming its practice."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-gate-sources-'))
    try:
        def practice(path, slug, clause):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'---\nslug: {slug}\ntitle: {slug}\ntier: on-demand\n'
                f'severity: default\napplies_to: ["**"]\n'
                f'occasion: "a fixture"\ngates: ["reply"]\n'
                f'index_clause: "{clause}"\nchecked_by: null\ndefines: []\n'
                f'status: active\nsupersedes: []\noverrides: null\n'
                f'added: 2026-09-13\napproved_by: "harness, 2026-09-13"\n---\n'
                f'## Rule\nThe {slug} rule text.\n\n## Why\nx\n\n'
                f'## Story\nx\n\n## Install\nx\n', encoding='utf-8')

        fx = tmp / 'fixture'
        practice(fx / 'practices' / 'fixture-universal-reply.md',
                 'fixture-universal-reply', 'the universal one')
        practice(fx / 'local' / 'practices' / 'fixture-local-reply.md',
                 'fixture-local-reply', 'the repo-local one')
        (fx / 'tools').mkdir(parents=True, exist_ok=True)
        (fx / 'tools' / 'routing_scope.json').write_text(json.dumps(
            {'_note': [], 'practices': {},
             'gates': {'reply': 'ending a turn and writing the reply'}}),
            encoding='utf-8')

        def declare(*extra):
            (fx / 'precedent.json').write_text(json.dumps({
                'format_version': 1, 'base_branch': 'main', 'visibility': 'private',
                'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'}] + list(extra),
            }), encoding='utf-8')

        def gate(*args):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_gate.py'),
                 '--repo', str(fx), 'reply', *args],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        declare({'level': 'repo-local', 'name': 'local', 'path': 'local'})
        r = gate()
        cases.append(('the reply gate names a practice from a NON-universal '
                      'source', 'fixture-local-reply' in r.stdout, r.stderr[:120]))
        cases.append(("...and still names the repo's own", 
                      'fixture-universal-reply' in r.stdout, r.stdout[:120]))
        cases.append(('a non-universal practice is labelled with its level, so '
                      'a session can see which source binds it',
                      'repo-local' in r.stdout))

        # the control: the same command, one source fewer
        declare()
        r2 = gate()
        cases.append(('the negative control: with the second source undeclared '
                      'the same command no longer names its practice',
                      'fixture-local-reply' not in r2.stdout
                      and 'fixture-universal-reply' in r2.stdout))

        # --- the BLOCKING half, against the same fixture ---
        bad = tmp / 'bad.md'
        bad.write_text('Some work.\n\n**What you need to do:** merge it.\n', encoding='utf-8')
        good = tmp / 'good.md'
        good.write_text('Some work.\n\n## Next Steps\n\n- **Merge it**\n\n'
                        'You can close this session.\n', encoding='utf-8')

        def replycheck(text):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(text)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        # No source declares a reply_check.json yet: the engine must have NO
        # opinion of its own about how a reply ends. A universal engine that
        # shipped one person's closing convention would bind every adopter to
        # it (practice: rule-level-by-reach).
        declare({'level': 'repo-local', 'name': 'local', 'path': 'local'})
        r3 = replycheck(bad)
        cases.append(('with no reply_check.json declared, a reply breaking every '
                      'rule is NOT blocked -- the engine ships the mechanism, not '
                      'the requirement', r3.returncode == 0, r3.stderr[:160]))

        (fx / 'local' / 'reply_check.json').write_text(json.dumps({
            'practice': 'fixture-local-reply',
            'require_heading_matching': 'next step',
            'require_one_of': ['You can close this session',
                               "Don't close this session"],
        }), encoding='utf-8')

        r4 = replycheck(bad)
        # control-asserts-which-failure: a non-zero exit is not evidence. The
        # message has to name WHICH requirement the reply missed.
        cases.append(('a declared requirement blocks a reply that misses it',
                      r4.returncode == 2, f'exit {r4.returncode}'))
        cases.append(('...and names the missing HEADING specifically',
                      'MARKDOWN HEADING' in r4.stderr, r4.stderr[:160]))
        cases.append(('...and names the missing closing sentence specifically',
                      'close this session' in r4.stderr, r4.stderr[:160]))
        cases.append(('...and names the practice that required it',
                      'fixture-local-reply' in r4.stderr, r4.stderr[:160]))

        r5 = replycheck(good)
        cases.append(('a reply that meets the requirement is not blocked',
                      r5.returncode == 0, r5.stderr[:160]))

        # 2026-09-14: the block message has to say SENTENCE when only a
        # sentence is missing. A source revised its required closing sentence
        # that morning, so every reply already carrying the heading was
        # refused for the sentence alone -- and a message that asked for "the
        # missing closing section(s)" got a whole second `## Next Steps`
        # block written under the first. Morgan: *"you repeated the 'next
        # steps' section two times."* The two messages are asserted against
        # each other below, so neither can quietly become the other.
        has_heading = tmp / 'has-heading.md'
        has_heading.write_text('Some work.\n\n## Next Steps\n\n- **Merge it**\n\n'
                               'Nothing about the session either way.\n', encoding='utf-8')
        r7 = replycheck(has_heading)
        cases.append(('a reply with the heading but not the sentence is still '
                      'blocked', r7.returncode == 2, f'exit {r7.returncode}'))
        cases.append(('...and the block says the heading is already there and '
                      'must not be written again -- the whole point, since the '
                      'refused reply has already been shown',
                      'ALREADY CARRIES every closing heading' in r7.stderr
                      and 'Do NOT repeat the closing section' in r7.stderr,
                      r7.stderr[:240]))
        cases.append(('...and the per-requirement line says where the sentence '
                      'goes instead of implying a new section',
                      'do NOT write that section a second time' in r7.stderr,
                      r7.stderr[:240]))
        cases.append(('...and it does NOT ask for a closing SECTION, which is '
                      'the wording that produced the duplicate',
                      'closing section(s)' not in r7.stderr, r7.stderr[:240]))
        # The negative control for the case above: the same check on a reply
        # that really is missing the heading must still ask for the section,
        # so "closing section(s) is absent" is a real distinction and not a
        # string that left the file altogether.
        cases.append(('the control: a reply missing the HEADING is still asked '
                      'for the whole closing section',
                      'closing section(s)' in r4.stderr
                      and 'ALREADY CARRIES every closing heading' not in r4.stderr,
                      r4.stderr[:240]))

        # A blocking gate may never refuse a reply that FOLLOWED the rule, so
        # the apostrophe the terminal renders and the one a person types have
        # to be the same sentence to it.
        curly = tmp / 'curly.md'
        curly.write_text('Work.\n\n## Next steps\n\n- **x**\n\n'
                         'Don\u2019t close this session until you answer.\n', encoding='utf-8')
        r6 = replycheck(curly)
        cases.append(('a curly apostrophe is the same sentence as a typed one',
                      r6.returncode == 0, r6.stderr[:160]))

        # A turn with no prose (tool use only) has no closing line to check.
        empty = tmp / 'empty.md'
        empty.write_text('', encoding='utf-8')
        cases.append(('an empty reply is not blocked', replycheck(empty).returncode == 0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the reply gate serves every source and its declared requirements '
          f'block ({len(cases)} stated cases, each with its control)',
          not bad_cases,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad_cases))


def check_advisory_requirement_never_blocks():
    """`"advisory": true` on a reply_check.json requirement makes an unmet
    one detectable (--explain, and violations() for any programmatic
    caller) but never lets it refuse the turn -- unlike an ordinary
    requirement in the same file, which still does.

    Added 2026-09-17 alongside downgrading the-boildown's own archive and
    compact sentences to advisory (Morgan, direct instruction: "note these
    aren't binding, it's just recommendations"). practice:
    control-asserts-which-failure -- the positive case alone proves
    nothing; the negative control below is the same fixture with
    `advisory` removed, which must go back to blocking.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-advisory-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')

        def declare(advisory):
            req = {'practice': 'fixture-advisory',
                   'require_heading_matching': 'fixture heading',
                   'require_one_of': ['fixture sentence one', 'fixture sentence two']}
            if advisory:
                req['advisory'] = True
            (fx / 'reply_check.json').write_text(json.dumps(req), encoding='utf-8')

        bad = tmp / 'bad.md'
        bad.write_text('## Fixture Heading\n\nNeither fixed sentence is here.\n',
                       encoding='utf-8')

        def replycheck():
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(bad)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        def explain():
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--explain'],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        declare(advisory=True)
        r = replycheck()
        cases.append(('an advisory requirement does not block a reply that '
                      'misses its sentence', r.returncode == 0, f'exit {r.returncode}'))
        e = explain()
        cases.append(('--explain still names it, and marks it ADVISORY',
                      'ADVISORY' in e.stdout, e.stdout[:200]))

        # The negative control: same fixture, `advisory` removed -- must go
        # back to blocking, or the positive case above proves nothing.
        declare(advisory=False)
        r2 = replycheck()
        cases.append(('negative control: the same requirement without '
                      '"advisory" blocks the same reply',
                      r2.returncode == 2, f'exit {r2.returncode}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok, *_ in cases if not ok]
    check(f'an advisory reply_check.json requirement is detected but never '
          f'blocks ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_contradiction_requirement_blocks():
    """`require_no_contradiction` catches a reply that asserts a fixed
    sentence AND, elsewhere in the same reply, a plain-language phrase that
    means the opposite -- "nothing blocking" beside "Don't archive this
    session", or a still-open/waiting-on-you phrase beside "You can archive
    this session".

    The incident: 2026-09-20, a reply's own bullets said "no open work is
    blocking either way" and then closed with "Don't archive this session"
    -- caught by the person, not by any check. This is the check.
    (practice: the-boildown, cite-the-incident)

    practice: control-asserts-which-failure -- each positive case asserts
    the guard's own "cannot both be true" message, not just a non-zero
    exit; the negative controls (the same text with only one half present)
    prove the match is on the PAIR, not on either phrase alone.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-contradiction-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-contradiction',
            'require_no_contradiction': [
                {'if_says': "Don't archive this session",
                 'must_not_say_matching':
                     r'\bno[\w\s]{0,20}?blocking\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))|'
                     r'\bnothing[\w\s]{0,15}?(?:blocking|outstanding|pending|left to do)\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))'},
                {'if_says': 'You can archive this session',
                 'must_not_say_matching':
                     r'\bstill (?:open|pending|blocking|waiting)\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))|'
                     r'\bwaiting on (?:you|your)\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))|'
                     r'\bblocked on\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))|'
                     r'\bneeds? your (?:approval|input|answer|review)\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))|'
                     r'\bnot yet (?:pushed|merged|committed)\b(?!\s+(?:there\b|on (?:it|that|this)\b|for (?:it|that|this)\b))'},
            ],
        }]), encoding='utf-8')

        def write(name, text):
            p = tmp / name
            p.write_text(text, encoding='utf-8')
            return p

        def replycheck(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(path)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        # Positive: the actual incident shape, reproduced verbatim in kind.
        bad1 = write('bad1.md',
                      '## The Boildown\n\n- Nothing further needed on this front.\n\n'
                      "Don't archive this session -- happy to keep going, but no "
                      'open work is blocking either way.\n')
        r1 = replycheck(bad1)
        cases.append(('the "no open work is blocking" + "don\'t archive" pair is '
                       'refused, naming the contradiction',
                       r1.returncode == 2 and 'cannot both be true' in r1.stderr,
                       r1.stderr[:200]))

        # Positive: the reverse pairing.
        bad2 = write('bad2.md',
                      '## The Boildown\n\n- The pull request is still open.\n\n'
                      'You can archive this session.\n')
        r2 = replycheck(bad2)
        cases.append(('the "still open" + "you can archive" pair is refused',
                       r2.returncode == 2 and 'cannot both be true' in r2.stderr,
                       r2.stderr[:200]))

        # Negative control 1: the archive sentence alone, no contradicting
        # phrase anywhere -- must pass, or the check is matching the
        # sentence by itself rather than the pair.
        clean1 = write('clean1.md',
                        "## The Boildown\n\nDon't archive this session -- PR #9 "
                        'is still waiting on your review.\n')
        r3 = replycheck(clean1)
        cases.append(("negative control: \"don't archive\" alone (with a "
                       'DIFFERENT, non-contradicting reason) is not blocked',
                       r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:160]}'))

        # Negative control 2: the contradicting phrase alone, no fixed
        # sentence present -- must pass, since there is no pair to compare.
        clean2 = write('clean2.md',
                        '## The Boildown\n\nNothing blocking, work continues.\n')
        r4 = replycheck(clean2)
        cases.append(('negative control: the phrase alone with neither fixed '
                       'sentence present is not blocked',
                       r4.returncode == 0, f'exit {r4.returncode}: {r4.stderr[:160]}'))

        # The second incident, same day: this check's own first landing was
        # refused by itself -- the reply describing the new check quoted
        # both trigger phrases AND both contradiction patterns, in single
        # quotes, while explaining the fix. Citing a phrase as a string is
        # not asserting it; double-quoted citation is now exempt, single is
        # deliberately NOT (an apostrophe in "Don't" makes a single-quote
        # span delimiter unsafe -- see _strip_quoted_spans()'s docstring).
        meta_dq = write(
            'meta_dq.md',
            '## Boildown\n\nA reply asserting "Don\'t archive this session" can '
            'no longer also contain a "nothing blocking" phrase, and "You can '
            'archive this session" can no longer co-occur with a "still open" '
            'phrase.\n\nYou can archive this session -- the fix is pushed.\n')
        r5 = replycheck(meta_dq)
        cases.append(('a reply CITING both trigger phrases and both '
                       'contradiction patterns in double quotes, while its own '
                       'real (unquoted) verdict matches neither, is not blocked',
                       r5.returncode == 0, f'exit {r5.returncode}: {r5.stderr[:200]}'))

        # Same text, single quotes instead of double -- the documented
        # limitation, not exempt. Proves the double-quote convention is
        # actually load-bearing rather than the fix being unconditional.
        meta_sq = write(
            'meta_sq.md',
            "## Boildown\n\nA reply asserting 'Don't archive this session' can "
            "no longer also contain a 'nothing blocking' phrase, and 'You can "
            "archive this session' can no longer co-occur with a 'still open' "
            "phrase.\n\nYou can archive this session -- the fix is pushed.\n")
        r6 = replycheck(meta_sq)
        cases.append(('negative control: the same citation in SINGLE quotes is '
                       'still blocked -- double quotes are the documented '
                       'convention, not an unconditional exemption',
                       r6.returncode == 2 and 'cannot both be true' in r6.stderr,
                       f'exit {r6.returncode}: {r6.stderr[:200]}'))

        # The third incident, same day: the flat match has no notion of
        # scope, so a per-item "nothing left to do" inside one Boildown
        # bullet -- about a single closed PR -- read identically to a
        # whole-session claim. (practice: the-boildown, cite-the-incident)
        scoped1 = write(
            'scoped1.md',
            '## The Boildown\n\n- PR #165 merged, confirmed -- nothing left '
            'to do there.\n- The source add/drop question is still waiting '
            "on you -- that's what's outstanding.\n\nDon't archive this "
            'session.\n')
        r7 = replycheck(scoped1)
        cases.append(('scope exemption: "nothing left to do THERE", scoped '
                       "to one closed item, does not block \"don't archive "
                       'this session\" driven by a different, real open item',
                       r7.returncode == 0, f'exit {r7.returncode}: {r7.stderr[:200]}'))

        # Negative control: same wording, scope qualifier removed -- proves
        # the exemption is on the trailing qualifier, not on bullet-list
        # phrasing or the presence of a second, genuine open item.
        scoped1_bare = write(
            'scoped1_bare.md',
            '## The Boildown\n\n- PR #165 merged, confirmed -- nothing left '
            'to do.\n- The source add/drop question is still waiting on '
            "you -- that's what's outstanding.\n\nDon't archive this "
            'session.\n')
        r8 = replycheck(scoped1_bare)
        cases.append(('negative control: the same reply with the "there" '
                       'dropped is still blocked -- the exemption is on the '
                       'scope qualifier, not on any other feature of the text',
                       r8.returncode == 2 and 'cannot both be true' in r8.stderr,
                       f'exit {r8.returncode}: {r8.stderr[:200]}'))

        # Same scope exemption, the reverse pairing ("You can archive this
        # session" / "still open" etc.) -- the fix touches both patterns in
        # the entry, so both get their own positive/negative pair.
        scoped2 = write(
            'scoped2.md',
            '## The Boildown\n\n- The deploy step is still open on this, '
            'a separate, already-tracked cleanup with its own owner.\n\n'
            'You can archive this session.\n')
        r9 = replycheck(scoped2)
        cases.append(('scope exemption: "still open ON THIS", scoped to a '
                       'separate tracked item, does not block "you can '
                       'archive this session"',
                       r9.returncode == 0, f'exit {r9.returncode}: {r9.stderr[:200]}'))

        scoped2_bare = write(
            'scoped2_bare.md',
            '## The Boildown\n\n- The deploy step is still open, a '
            'separate, already-tracked cleanup with its own owner.\n\n'
            'You can archive this session.\n')
        r10 = replycheck(scoped2_bare)
        cases.append(('negative control: the same reply with "on this" '
                       'dropped is still blocked',
                       r10.returncode == 2 and 'cannot both be true' in r10.stderr,
                       f'exit {r10.returncode}: {r10.stderr[:200]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'require_no_contradiction refuses a reply asserting both halves of '
          f'the archive contradiction ({len(cases)} stated cases, each with its control)',
          not bad_cases,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad_cases))


def check_reply_check_refuses_a_paste_block_that_lands_unauthorized():
    """A paste block that tells another session to land work on main
    carries the person's quoted approval, or the reply is refused.

    2026-10-01: two prompts a session wrote ended "Land it on staging per
    this repo's conventions", with no approval given; fence-block-for-paste
    passed both, since it checks where a block goes, not what it
    authorizes. Since 2026-10-02 the universal rule speaks of main, where
    work lands for a person off the ladder, and accepts any quoted approval;
    the tier branches and the quoted "Booked" are the ladder set's own copy
    of the rule (spec/LADDER_OPT_IN_PLAN.md D11). Driven against the rule
    as reply_check.json ships it (practice: prompt-please), both ways."""
    import precedent_reply_check as prc
    name = 'a paste block that lands on main needs a quoted approval'
    try:
        reqs = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
            encoding='utf-8')) if r.get('require_in_fence_paired_with')]
    except (OSError, ValueError):
        reqs = []
    if not reqs:
        check(name, False, 'reply_check.json declares no require_in_fence_paired_with')
        return

    def fires(body, prose='Paste into: a new session rooted in x.\n'):
        text = prose + '```\n' + body + '\n```\n'
        return [v for v in prc.violations(text, reqs) if v['kind'] == 'in_fence_paired']
    must_fire = {
        'merge into main': 'When the checks pass, merge it into `main`.',
        'land it on main': "Do the work.\nLand it on main per this repo's conventions.",
        'a pull request into main': 'Open a pull request into main and merge it.',
    }
    clean = {
        "the person's quoted approval": 'Morgan, 2026-10-01: "Approved".\nOpen a pull request into main and merge it.',
        'a feature-branch ending': 'Build it on your feature branch, push it there, and stop.',
        'a negated line': 'Open no pull request and merge nothing into main.',
        'a tier branch, which off the ladder is not a landing':
            'Push it to staging once it is green.',
        # 2026-10-10, a consumer's root-issues reply: a report of a past
        # merge, with no ending at Act, is not an order.
        'a report of a past merge, as the rule ships':
            'Situation: the update merged into main as PR #48. Read the diff.',
    }
    # 2026-10-08: a block that ends at the feature branch may NARRATE a past
    # landing -- what a session did, what a tool told it -- without that
    # report being read as an order; every instruction beside it is still
    # judged, and a claim of the person's word still has to quote it.
    stop = ('Build it on your feature branch, push it there, and stop; '
            'open none and land nothing.')
    told = ('A session had prepared a copy and a tool told it to open a '
            'pull request to main.')
    must_fire.update({
        'narration with no feature-branch ending': 'SITUATION\n' + told,
        'a feature-branch ending and an order to merge':
            'SITUATION\n' + told + '\nThen merge it into main.\n' + stop,
        'an order tacked onto narration':
            'The tool told it to open a PR to main, so merge it into main.\n' + stop,
        "the person's word claimed, not quoted":
            'Morgan said to merge it into main.\n' + stop,
        'narration addressed to the receiver':
            'You were told to merge it into main.\n' + stop,
        'an order with a past participle in it':
            'Push the merged branch to main.\n' + stop,
    })
    # 2026-10-10, a Prompt Please for a workflow fix: a present-tense
    # description of the event a workflow reacts to is no order. The verb
    # is what makes one, so the same nouns after "Open a" still fire.
    clean.update({
        'THE BUG: a workflow trigger described, across two sentences':
            'The step should run only on main itself, after a push, never a '
            'pull request. Today it also fires on a pull request into main.',
        'a condition: after every push to main':
            'The check runs after every push to main.',
    })
    # Later on 2026-10-10: a message a tool printed, quoted, is output, not
    # an order; a person's words quoted are still the rule's business.
    clean.update({
        'a tool message quoted as it printed it':
            'After the merge, the wait still prints "Merge the pull request into main". '
            'Say it passed instead.',
    })
    must_fire.update({
        'an order beside a quoted tool message':
            'The check prints "done". Then merge it into main.',
    })
    must_fire.update({
        'an order whose object follows "Open a"':
            'Open a PR into main once the checks pass.',
        'an order that names the event as its timing':
            'Merge it after a push to main.',
        'a described event beside an order, in one sentence':
            'It fires on a pull request into main, so merge it into main.',
    })
    clean.update({
        'narration in a block that ends at the feature branch':
            'SITUATION\n' + told + '\n' + stop,
        'a past merge, narrated':
            'The last session merged its PR into main yesterday.\n' + stop,
    })
    # Later on 2026-10-08: a negator exempts a clause only when it governs
    # the landing verb there, and a block that says land in other words is
    # read for what it asks (Morgan: "shouldn't it understand the intent
    # behind commands not just the literal words?"; practice:
    # read-for-intent). Until then a shell command stayed clean by design;
    # `git push origin main` is a landing, and now it reads as one.
    must_fire.update({
        'the bug: a negator that governs something else':
            'Merge it into main, no questions asked.',
        'a negator after the destination': 'Merge it into main without waiting.',
        'a negator that turns into a yes': "Don't hesitate to merge into main.",
        'an apostrophe is not a quote': "Don't wait; it's fine to merge into main.",
        'a negated object with an exception': 'Merge nothing but the fix into main.',
        'make it live': 'Make it live once the checks pass.',
        'ship to production': 'Deploy it to production when green.',
        'ship it': 'Ship it.',
        'fast-forward main': 'Fast-forward main to your branch.',
        'merge the PR': 'Open the pull request and merge the PR.',
        'gh pr merge': 'Run gh pr merge 12 --squash.',
        'a shell command': 'git push -u origin main',
        'a refspec': 'git push origin HEAD:main',
        'a PR opened with --base': 'gh pr create --base main',
    })
    clean.update({
        "don't merge": "Don't merge into main.",
        'never push': 'Never push to main.',
        'do not open a PR': 'Do not open a PR to main.',
        'without, governing the verb': 'Finish without merging into main.',
        'a negated command': 'Do not run gh pr merge, and do not make it live.',
        'fast-forwarding a local checkout to read it':
            'Fast-forward your checkout of main before you start.',
        'a push to the feature branch': 'git push -u origin 2026-10-08-fix-x1',
    })
    # 2026-10-20, found fixing the ladder set's copy of this rule
    # (todo/todo-2026-10-20-root-issues-from-ladder-landing-check.md, items
    # 1 and 2). Any quoted span holding push, merge or land counted as the
    # person's approval, so a refusal quoted further down ("push refused")
    # granted landing; and a landing noun with no verb addressed to the
    # reader ("A push to main runs ...") was read as an order.
    order = 'Open a pull request into main and merge it.'
    must_fire.update({
        'THE BUG: a quoted refusal is no approval':
            order + '\nThe tool said "push refused" earlier.',
        '...nor a quoted refusal on a blockquote line':
            order + '\n> push refused (403)',
        "...nor a tool's printed instruction, quoted":
            order + '\nThe check prints "Merge the pull request into main".',
        'an order written as an infinitive the reader is told to do':
            'Your job is to merge the PR into main.',
        'an order after a comma and "so"':
            'The checks pass, so merge it into main.',
        'the last item of a bracketed list is the order':
            'Finish the fix (run the tests, then merge the PR into main).',
    })
    clean.update({
        'THE BUG: a push to main described, no verb addressed to anyone':
            'A push to main runs the deep check.',
        'merge named as one example in a bracketed list':
            'Narrow it to orders to land (land it, merge the PR, or a stage word).',
        'a pull request into main named as a noun':
            'The pull request into main is still open; read its diff.',
    })
    clean.update({
        "the person's approval as a blockquote": '> Approved, merge it\n' + order,
        "the person's go-ahead quoted": 'Alex, 2026-10-20: "Go ahead and land it."\n' + order,
        "the person's order quoted": 'Morgan: "Merge it into main."\n' + order,
    })
    cases = [(f'fires: {k}', bool(fires(b)), '') for k, b in must_fire.items()]
    cases += [(f'clean: {k}', not fires(b), str(fires(b))[:200]) for k, b in clean.items()]
    cases.append(("clean: the reply's own prose saying where work lands",
                  not fires('push it there and stop',
                            prose='Approved work lands on main.\nPaste into: x\n'), ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} {d}' for n, d in bad))


def check_reply_check_wants_a_prompt_block_to_name_both_ends():
    """tools/precedent_reply_check.py -- a paste block written for another
    session opens with two lines: the session sending it (From) and the
    session it is for (For), or "a new session rooted in" a repository.

    Morgan, 2026-10-10: "Every prompt you give me should have BOTH at the
    top: the session sending it, and what session it is for ... and enforce
    it." THE INCIDENT, the discriminating case: a session answered a message
    opening "Sent automatically by the session ..." with a block that named
    itself and not its destination. The check before this one recognized a
    sender only as `From "..." (link)`, so it never fired. Judged against
    the shipped rule, so loosening either the engine or reply_check.json
    fails here.

    2026-10-11, a consuming repository: a block opening "From: <title>
    (<link>)" / "For: a new BestPractice session" matched none of the shapes
    that mark a block as a prompt, so it was never judged; and its From line
    never said a session wrote it. Both are cases below."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_reply_check as rc
    rule = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
        encoding='utf-8')) if r.get('id') == 'prompt-block-names-both-ends']
    cases = [('the shipped rule exists', len(rule) == 1)]
    sender = 'https://claude.ai/code/session_014zVauR9GhVyVVgSNEMLyGb'
    relayed = ('Sent automatically by the session "Zoom/Hangouts transcripts '
               'to GitHub" (session_014zVauR9GhVyVVgSNEMLyGb) -- '
               f'{sender}. Nobody typed this.\nSeed root: alex137/BestPractice.')
    me = 'https://claude.ai/code/session_01MEabcdef'
    origin = (f'Sent automatically by the session "BP: me" (session_01MEabcdef) '
              f'-- {me}. Nobody typed this.')
    old_shape = f'From "BP: me" (session_01MEabcdef) -- {me}'
    for_sender = f'For: the session "Zoom/Hangouts transcripts to GitHub" -- {sender}.'
    for_new = 'For: a new session rooted in alex137/BestPractice.'

    def reply(*lines, outside=f'Paste this into Zoom/Hangouts -- {sender}.'):
        return outside + '\n\n```\n' + '\n'.join(lines) + '\n```\n'

    def refused(text, p=relayed):
        return any(v['kind'] == 'prompt_header'
                   for v in rc.violations(text, rule, prompt=p))
    cases += [
        ("THE DISCRIMINATING CASE: the block that slipped through -- its own "
         "name first, no For line, answering a 'Sent automatically' message",
         refused(reply(old_shape, '', 'Done and on main.'))),
        ('a block with both lines, the For line naming the sender, passes',
         not refused(reply(origin, for_sender, 'Done and on main.'))),
        ("the old From shape, which never says a session wrote it, no longer "
         "counts as the first line (2026-10-11)",
         refused(reply(old_shape, for_sender, 'Done.'))),
        ('"From: the session ..." with its link counts as the first line',
         not refused(reply(f'From: the session "BP: me" -- {me}.', for_sender,
                           'Done.'))),
        ("THE 2026-10-11 CASE: 'From: <title> (<link>)' and 'For: a new "
         "BestPractice session' -- never recognized as a prompt, so never judged",
         refused(reply(f'From: Pesty: Update Vendors to BP 0840ae0 ({me})',
                       'For: a new BestPractice session', 'SITUATION ...',
                       outside='Here it is.'), p='Prompt Please')),
        ('...and with a full From line, that For line is still refused',
         refused(reply(origin, 'For: a new BestPractice session', 'Do it.',
                       outside='Here it is.'), p='Prompt Please')),
        ('a block with no header at all, under "Paste into: a new session '
         'rooted in ...", is judged and refused',
         refused(reply('SITUATION: the update failed.', 'Fix it.',
                       outside='**Paste into:** a new session rooted in '
                               'alex137/BestPractice.'), p='Prompt Please')),
        ('a command block under "Paste into: your terminal" is not judged',
         not refused(reply('git status', outside='Paste into: your terminal.'),
                     p='Prompt Please')),
        ('an email draft opening "From: alice@example.com" is not judged',
         not refused(reply('From: alice@example.com', 'To: bob@example.com',
                           'Hi Bob,', outside='Paste into: your mail app.'),
                     p='Prompt Please')),
        ('the For line must be the SECOND line, not further down',
         refused(reply(origin, 'Seed root: x/y.', for_sender))),
        ('the From line must be the FIRST line',
         refused(reply(for_sender, origin, 'Done.'))),
        ("a For line naming another session, in answer to the sender, is refused",
         refused(reply(origin, 'For: the session Other -- '
                       'https://claude.ai/code/session_01OTHERxyz.', 'Done.',
                       outside='Paste this into Other -- '
                               'https://claude.ai/code/session_01OTHERxyz.'))),
        ('a placeholder For line is refused',
         refused(reply(origin, 'For: unknown', 'Done.'), p='Prompt Please')),
        ('a new-session prompt passes with "For: a new session rooted in"',
         not refused(reply(origin, for_new, 'Seed root: alex137/BestPractice.',
                           outside='Open a new session rooted in alex137/BestPractice.'),
                     p='Prompt Please')),
        ('a new-session prompt with no For line is refused',
         refused(reply(origin, 'Seed root: alex137/BestPractice.', 'Do it.',
                       outside='Open a new session rooted in alex137/BestPractice.'),
                 p='Prompt Please')),
        ('answering a sender, the reply may send the block to a new session '
         'instead, and says so in both places',
         not refused(reply(origin, for_new, 'Do it.',
                           outside='Open a new session rooted in alex137/BestPractice.'))),
        ('a block for an existing session that the reply never names outside '
         'the block is refused',
         refused(reply(origin, for_sender, 'Done.', outside='Here it is.'))),
        ('a fenced block that is not a prompt is not judged',
         not refused(reply('git status', outside='Run this.'))),
    ]
    bad = [c[0] for c in cases if not c[1]]
    check(f'a prompt block names both the session sending it and the one it is '
          f'for ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_a_set_inherits_the_landing_triggers():
    """A set's landing pair that says "inherits" names its own branches
    (`landing_branches`) and its own extra orders (`adds_if_matches`), and
    keeps every trigger universal states, widened to those branches
    (precedent_reply_check._inherit_pair).

    2026-10-20: the ladder set's pair restated all of universal's triggers
    only to name staging beside main, and the copies drifted -- universal
    learned to read a verb only where it is addressed, the ladder copy did
    not (precedent-shared-ladder PR #126 fixed it by hand). Judged with the
    shipped universal rule and a set pair trimmed to what the ladder set
    actually adds; the old shape, a set restating everything, reads as it
    did."""
    import precedent_reply_check as rc
    name = 'a set keeps universal\'s landing triggers and names its own branches'
    uni = [dict(r, _source='universal/precedent') for r in json.loads(
        (ROOT / 'reply_check.json').read_text(encoding='utf-8'))
        if r.get('id') == 'prompt-please-landing-authority']
    if len(uni) != 1 or not hasattr(rc, '_inherit_pair'):
        check(name, False, 'the universal landing rule or _inherit_pair is missing')
        return
    stage = (r"(?:^|(?<=[.;:,!?]\s)|(?<=\bthen\s))(?-i:Booked|Debut|Promote)\b"
             r"(?!\s+(?:is|means|as\s+an?\s+instruction)\b)")
    trimmed = {'id': 'prompt-please-landing-authority', 'inherits': True,
               'practice': 'go-update', '_source': 'shared/fixture-ladder',
               'require_in_fence_paired_with': [{
                   'landing_branches': 'staging|main',
                   'adds_if_matches': [stage, r'--promote\b'],
                   'must_also_match': r'["\u201c]\s*(?:Booked|Approved)\b'}]}
    restated = {'id': 'prompt-please-landing-authority', 'inherits': True,
                '_source': 'shared/fixture-old',
                'require_in_fence_paired_with': [{
                    'if_matches': r'\bmerg\w*\b[^\n]{0,40}\binto\s+staging\b',
                    'must_also_match': r'"Booked"'}]}

    def refused(reqs, body):
        text = 'Paste into: a new session.\n\n```\n' + body + '\n```\n'
        return bool([v for v in rc.violations(text, rc._settle(list(reqs), str(ROOT)))
                     if v['kind'] == 'in_fence_paired'])
    ladder = uni + [trimmed]
    booked = 'Morgan, 2026-10-20: "Booked."\n'
    cases = []
    for body in ('Then merge the PR into main.', 'You can push it to staging.',
                 'Land it on staging.', 'git push origin staging',
                 'Then Debut it.', 'Run it with --promote.'):
        cases.append((f'an order fires: {body}', refused(ladder, body)))
        cases.append((f'...and the quoted Booked clears it: {body}',
                      not refused(ladder, booked + body)))
    for body in ('A push to staging runs the deep check.',
                 'A direct push to staging was refused.',
                 'Narrow it to orders to land (land it, merge the PR, or a stage word).',
                 'Then narrow it (Booked as an instruction).'):
        cases.append((f'a description does not: {body}', not refused(ladder, body)))
    cases.append(("universal alone still reads staging as no landing",
                  not refused(uni, 'Land it on staging.')))
    cases.append(('a set that restates its triggers reads as it did: its own fires',
                  refused(uni + [restated], 'Merge it into staging.')))
    cases.append(("...and universal's, which it replaced, do not",
                  not refused(uni + [restated], 'Land it on main.')))
    bad = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_reply_check_reads_a_landing_trigger_by_clause_and_by_list():
    """The engine keys behind read-for-intent's landing rule, driven with
    fixture rules so the mechanism is tested apart from any one set's data.

    `if_matches` may be a list and `also_if_matches` adds to it; a stage
    word given as the order fires only in a capitalized, imperative place
    (the ladder set lists its own the same way); `negation_exempt_if_clause_negates`
    forgives a clause only when the negator governs the landing verb in it,
    as one regex or as {before, object}; and an old-shape rule -- one
    string with its own line-level lookahead, neither key -- reads exactly
    as it did. (2026-10-08; practice: read-for-intent.)"""
    import precedent_reply_check as prc
    neg = r"\b(?:do not|never|not|no|nothing)\b"
    tier = r"\bmerg\w*\b[^\n]{0,80}?\binto\s+(?:staging|main)\b"
    stage = (r"(?:^|(?<=[.;:,!?]\s)|(?<=\bthen\s))(?-i:Debut|Booked)\b"
             r"(?!\s+(?:is|lands)\b)")

    def rule(**pair):
        pair.setdefault('must_also_match', r'"Booked"')
        return [{'practice': 'fixture', 'require_in_fence_paired_with': [pair]}]

    def fires(reqs, body):
        return bool([v for v in prc.violations('```\n' + body + '\n```\n', reqs)
                     if v['kind'] == 'in_fence_paired'])
    old = rule(if_matches=r"^(?![^\n]*\b(?:not|no)\b)[^\n]*" + tier)
    listed = rule(if_matches=[tier], also_if_matches=[stage],
                  negation_exempt_if_clause_negates=neg)
    split = rule(if_matches=tier, also_if_matches=[stage],
                 negation_exempt_if_clause_negates={
                     'before': neg, 'object': r"\bnothing\b"})
    cases = [
        ('old shape: a plain order fires', fires(old, 'Merge it into main.')),
        ('old shape: its own lookahead still skips a negated line',
         not fires(old, 'Do not merge into main.')),
        ('old shape: the line-level hole it had', not fires(
            old, 'Merge it into main, no questions asked.')),
        ('list: the bug case fires',
         fires(listed, 'Merge it into main, no questions asked.')),
        ('list: a negator before the verb exempts',
         not fires(listed, 'Never merge it into staging.')),
        ('list: a stage word as the order fires', fires(listed, 'Then Debut it.')),
        ('list: a stage word mentioned does not',
         not fires(listed, 'The person lands it with Booked.')),
        ('list: a lower-case stage word is a plain word',
         not fires(listed, 'Then debut the idea in the doc.')),
        ('list: a negated stage word is exempt', not fires(listed, 'Do not Debut it.')),
        ('list: a quoted Booked satisfies it',
         not fires(listed, 'Morgan: "Booked".\nThen Debut it.')),
        ('split: an object negator after the verb exempts',
         not fires(split, 'Merge nothing into main.')),
        ('split: the before-regex is not used as the object',
         fires(split, 'Merge not this into main.')),
        ('a trigger across a clause boundary is never forgiven',
         fires(listed, 'Do not wait, merge it into main.')),
    ]
    # 2026-10-10, a consumer's root-issues reply: "The update merged into
    # staging as PR #47" in a block's situation paragraph was refused as a
    # landing order. With narration_exempt a report of the past is never one,
    # whether or not the block stops at Act; an order beside it still fires.
    told = rule(if_matches=tier, narration_exempt=True)
    report = ('Situation: the consuming repo ran Update Vendors. The update '
              'merged into staging as PR #47.')
    cases += [
        ('narration_exempt: a block that only reports a past merge passes',
         not fires(told, report)),
        ('...and "PR #47 merged into staging" reads as a report too',
         not fires(told, 'PR #47 merged into staging an hour ago.')),
        ('...while an order in the same block still fires',
         fires(told, report + '\nNow merge it into main.')),
        ('...and a report to "you" is not forgiven',
         fires(told, 'The update you merged into staging stays.')),
        ('without the key, the same report is still judged (the stricter '
         'reading an older source gets)', fires(rule(if_matches=tier), report)),
        ('...but a report of what a tool TOLD a session still needs the stop: '
         'a reader may take it up',
         fires(told, 'A tool told it to merge it into main.')),
    ]
    bad = [n for n, ok in cases if not ok]
    return not bad, '; '.join(bad)


def check_reply_check_requires_a_destination_for_a_fence_block():
    """`require_paired_with` catches a reply that hands over a fenced block
    and never says where it goes.

    The incident: across 2026-09-20 and 21, Morgan asked roughly twenty
    times what session a block he had just been handed was for. Every one
    of those blocks was correctly fenced, because fence-block-for-paste
    already made the fence mandatory and said nothing about the address --
    the practice enforced the container and left out the destination.
    (practice: fence-block-for-paste, cite-the-incident)

    practice: control-asserts-which-failure -- the positive case asserts
    the guard's own message, and the two negatives prove BOTH escape routes
    work: naming a destination, and declaring the block to be output.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-paired-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        # The gate REFUSES to print anything for a gate with no practices
        # registered to it ("an empty gate is a step that loads nothing and
        # looks like it worked"), so the fixture needs one -- otherwise the
        # print case below would pass or fail for a reason unrelated to
        # what it is testing (practice: fixture-owns-its-state).
        (fx / 'practices' / 'fixture-paired.md').write_text(
            '---\n'
            'slug:        fixture-paired\n'
            'title:       A fixture practice wired to the reply gate\n'
            'tier:        on-demand\n'
            'severity:    default\n'
            'applies_to:  []\n'
            'occasion:    "a fixture needs one practice on the reply gate"\n'
            'gates:       ["reply"]\n'
            'index_clause: "a fixture rule"\n'
            'checked_by:  null\n'
            'status:      active\n'
            'in_force_at: null\n'
            'supersedes:  []\n'
            'overrides:   null\n'
            'added:       null\n'
            'approved_by: null\n'
            '---\n\n## Rule\nA fixture rule, present so the reply gate has '
            'something registered to it.\n', encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-paired',
            'require_paired_with': [
                {'if_matches': r'^\s*```',
                 'must_also_match': r'(?:\*\*)?Paste into:|\bnot for pasting\b',
                 'why': 'say where it goes'},
            ],
        }]), encoding='utf-8')

        def write(name, text):
            q = tmp / name
            q.write_text(text, encoding='utf-8')
            return q

        def replycheck(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(path)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        bad = write('bad.md', '## The Boildown\n\nHere it is.\n\n'
                              '```\nsome text\n```\n')
        r1 = replycheck(bad)
        cases.append(('a fence block with no destination is refused, naming '
                      'the requirement',
                      r1.returncode == 2 and 'nothing in it matches' in r1.stderr,
                      f'exit {r1.returncode}: {r1.stderr[:200]}'))

        good = write('good.md', '## The Boildown\n\n**Paste into:** the session '
                                'rooted in FooRepo.\n\n```\nsome text\n```\n')
        r2 = replycheck(good)
        cases.append(('negative control: a block WITH a named destination '
                      'passes',
                      r2.returncode == 0, f'exit {r2.returncode}: {r2.stderr[:160]}'))

        out = write('out.md', '## The Boildown\n\nMeasured, not for pasting:'
                              '\n\n```\noutput\n```\n')
        r3 = replycheck(out)
        cases.append(('negative control: a block declared output is not asked '
                      'for a destination',
                      r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:160]}'))

        none = write('none.md', '## The Boildown\n\nNo fenced block anywhere.\n')
        r4 = replycheck(none)
        cases.append(('negative control: a reply with no fence block is '
                      'unaffected',
                      r4.returncode == 0, f'exit {r4.returncode}: {r4.stderr[:160]}'))

        # The pre-reply print must NAME it. A blocking requirement that is
        # enforced and never announced costs the person the reply twice --
        # the exact failure precedent_gate.py's own docstring records.
        r5 = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_gate.py'),
             '--repo', str(fx), 'reply'],
            capture_output=True, text=True, cwd=str(tmp),
            env={**os.environ,
                 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})
        cases.append(('the reply gate PRINTS this requirement before the reply',
                      'must ALSO match' in r5.stdout, failure_detail(r5.stdout, 200)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_reply_check_keeps_practice_ideas_at_the_close():
    """A reply offering practice ideas is refused unless it is the one that
    says the session can be archived, and the refusal says to add nothing --
    never to add the archive line to make the pair match.

    Morgan, 2026-10-05 (strength: decided): practice ideas come at the
    natural end of a conversation, not after every message.

    practice: control-asserts-which-failure -- the positive case asserts the
    pair's own repair text; the controls prove the closing reply passes and
    that prose merely mentioning practice ideas is not read as offering them.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ideas-'))
    cases = []
    try:
        fx = tmp / 'repo'
        fx.mkdir()
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        decl = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
            encoding='utf-8')) if r.get('id') == 'practice-ideas-only-at-the-close']
        (fx / 'reply_check.json').write_text(json.dumps(decl), encoding='utf-8')

        def replycheck(name, text):
            q = tmp / name
            q.write_text(text, encoding='utf-8')
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(q)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        mid = ('Fixed.\n\n## Boildown\n- The work of this session is now on: '
               '`claude/x`.\n- Practice ideas:\n  - Run long checks in the '
               "background.\n- Don't archive this session.\n")
        r1 = replycheck('mid.md', mid)
        cases.append(('practice ideas mid-conversation are refused, and the '
                      'refusal asks for one withdrawing line, never the archive line',
                      r1.returncode == 2 and 'Output ONE line withdrawing them' in r1.stderr
                      and 'Output NOTHING' not in r1.stderr
                      and 'Do NOT add the archive line' in r1.stderr,
                      f'exit {r1.returncode}: {r1.stderr[:300]}'))

        for label in ('Content idea', 'Process idea'):
            r = replycheck(f'{label}.md', mid.replace('Practice ideas', label))
            cases.append((f'a "{label}:" mid-conversation is refused the same way',
                          r.returncode == 2 and 'Output ONE line withdrawing them'
                          in r.stderr, f'exit {r.returncode}: {r.stderr[:200]}'))

        close = mid.replace("- Don't archive this session.",
                            '- You can archive this session.')
        r2 = replycheck('close.md', close)
        cases.append(('negative control: the same ideas in the closing reply pass',
                      r2.returncode == 0, f'exit {r2.returncode}: {r2.stderr[:200]}'))

        prose = ('Practice ideas now come only at the close of a session.\n\n'
                 '## Boildown\n- The work of this session is now on: `x`.\n')
        r3 = replycheck('prose.md', prose)
        cases.append(('negative control: prose about practice ideas is not an offer',
                      r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:200]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_reply_check_refuses_a_repeated_boildown():
    """`require_section_not_repeated` refuses a Boildown whose every line says
    again what the previous reply's said, and nothing else.

    Morgan, 2026-10-05 (strength: decided): "a boildown with nothing should be
    one line", after three in a row repeated the same branch line and archive
    verdict around one new fact. The planted repeat is that day's own pair:
    the second rewords the first and adds nothing.

    practice: control-asserts-which-failure -- the positive case asserts the
    guard's own message and its say-nothing repair; the controls prove a new
    fact, a changed branch, the one-line form, a first reply and a missing
    transcript all pass.

    Negative control, measured 2026-10-29: with previous_section skipping
    only a last entry equal to the judged text, the woken-turn case fails.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-repeat-'))
    cases = []
    try:
        fx = tmp / 'repo'
        fx.mkdir()
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-repeat',
            'require_section_not_repeated': {
                'heading': 'boildown',
                'one_line': '- The work of this session is now on: <x>, '
                            'unchanged since the last update.',
                'same_when_both_say': ["Don't archive this session",
                                       'You can archive this session']},
        }]), encoding='utf-8')

        def transcript(name, replies):
            path = tmp / name
            path.write_text('\n'.join(json.dumps({
                'type': 'assistant', 'message': {
                    'usage': {'input_tokens': 2},
                    'content': [{'type': 'text', 'text': r}]}})
                for r in replies) + '\n', encoding='utf-8')
            return path

        def run(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx)],
                input=json.dumps({'transcript_path': str(path)}),
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        first = ('Harness passed.\n\n## Boildown\n'
                 '- The work of this session is now on: `claude/x-btnxe` '
                 '(BestPractice), pushed but not landed.\n'
                 '- **Your call:** say "Booked" to land it on `staging`. '
                 'My pick is yes.\n'
                 "- Don't archive this session. Archived now, the work never "
                 'lands.\n')
        again = ('That notice is the result I already reported.\n\n## Boildown\n'
                 '- The work of this session is now on: `claude/x-btnxe` '
                 '(BestPractice), pushed but not landed.\n'
                 '- Next is your "Booked" to land it on `staging`.\n'
                 "- Don't archive this session. The work would stay on its "
                 'feature branch.\n')
        r1 = run(transcript('repeat.jsonl', [first, again]))
        cases.append(('a reworded Boildown with nothing new is refused, '
                      'asking for the one-line form and nothing more -- never '
                      'for nothing, which the harness does not accept',
                      r1.returncode == 2 and 'previous reply' in r1.stderr
                      and 'unchanged since the last update' in r1.stderr
                      and 'Output ONLY the one-line form' in r1.stderr
                      and 'Output NOTHING' not in r1.stderr,
                      f'exit {r1.returncode}: {r1.stderr[:300]}'))

        news = again.replace('- Next is your "Booked" to land it on `staging`.',
                             '- The harness found a broken link, fixed in the '
                             'last commit.')
        r2 = run(transcript('news.jsonl', [first, news]))
        cases.append(('negative control: one new line makes it a real update',
                      r2.returncode == 0, f'exit {r2.returncode}: {r2.stderr[:200]}'))

        moved = again.replace('`claude/x-btnxe` (BestPractice), pushed but not '
                              'landed', '`staging` (BestPractice), landed')
        moved = moved.replace("- Don't archive this session. The work would stay "
                              'on its feature branch.',
                              "- Don't archive this session. Main still waits.")
        moved = moved.replace('- Next is your "Booked" to land it on `staging`.',
                              '- Landed on `staging`.')
        r3 = run(transcript('moved.jsonl', [first, moved]))
        cases.append(('negative control: a branch that changed is a change, '
                      'however alike the words',
                      r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:200]}'))

        short = ('Same as before.\n\n## Boildown\n- The work of this session '
                 'is now on: `claude/x-btnxe`, unchanged since the last update.\n')
        r4 = run(transcript('short.jsonl', [first, short]))
        cases.append(('negative control: the one-line form passes',
                      r4.returncode == 0, f'exit {r4.returncode}: {r4.stderr[:200]}'))

        r5 = run(transcript('only.jsonl', [first]))
        cases.append(('negative control: a first Boildown has nothing to repeat',
                      r5.returncode == 0, f'exit {r5.returncode}: {r5.stderr[:200]}'))

        r6 = run(tmp / 'no-such-transcript.jsonl')
        cases.append(('negative control: no transcript, no refusal',
                      r6.returncode == 0, f'exit {r6.returncode}: {r6.stderr[:200]}'))

        # 2026-10-28: a turn a background job woke, with short notes before
        # its final message. The wake path judges every text block of the
        # turn joined, which matched no timeline entry, so the reply was
        # compared with its own Boildown and refused.
        def woken(name, final, notes=('Checking the result.',)):
            note = '<task-notification><task-id>b1</task-id><status>completed</status></task-notification>'
            rows = [{'type': 'assistant', 'message': {
                        'usage': {'input_tokens': 2},
                        'content': [{'type': 'text', 'text': first}]}},
                    {'type': 'user', 'origin': {'kind': 'task-notification'},
                     'message': {'role': 'user', 'content': note}}]
            rows += [{'type': 'assistant', 'message': {
                        'usage': {'input_tokens': 2},
                        'content': [{'type': 'text', 'text': t}]}}
                     for t in [*notes, final]]
            path = tmp / name
            path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n',
                            encoding='utf-8')
            return path

        r7 = run(woken('woken-news.jsonl', news))
        cases.append(('a woken turn with notes before its final message is '
                      'compared with the previous turn, never with itself '
                      '(2026-10-28)',
                      r7.returncode == 0, f'exit {r7.returncode}: {r7.stderr[:200]}'))
        r8 = run(woken('woken-again.jsonl', again))
        cases.append(('...and a real repeat on such a turn is still refused',
                      r8.returncode == 2 and 'previous reply' in r8.stderr,
                      f'exit {r8.returncode}: {r8.stderr[:200]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_reply_check_keeps_quiet_while_a_batch_runs():
    """`require_quiet_while_background_runs` refuses any prose on a turn a
    background job woke while another background command is still running,
    or that a Monitor's progress event woke; the batch reports once.

    Morgan, 2026-10-05 (strength: decided), after four Debuts run in sequence
    reported themselves one at a time, each with its own Boildown: a reply to
    a job finishing gets no Boildown unless the job is done, and a batch
    reports once. The planted transcripts use that day's shapes: the
    harness's own "Command running in background with ID" result, a
    notification as the turn's prompt, and one that ended mid-turn as an
    `attachment` row.

    practice: control-asserts-which-failure -- the positive cases assert the
    guard's own say-nothing repair; the controls prove the batch's final
    report still needs (and passes with) its Boildown, a failure may speak,
    a silent turn is not judged by the last turn's words, and printed text
    that merely quotes the started line starts nothing.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-quiet-'))
    cases = []
    try:
        fx = tmp / 'repo'
        fx.mkdir()
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([
            {'practice': 'fixture-quiet', 'require_heading_matching': 'boildown'},
            {'practice': 'fixture-quiet',
             'require_quiet_while_background_runs': {'why': 'reports once'}},
        ]), encoding='utf-8')

        def human(t):
            return {'type': 'user', 'origin': {'kind': 'human'},
                    'message': {'role': 'user', 'content': t}}

        def started(task_id, extra='', output=None):
            # The output file exists, as it does for a job running here; a
            # job from a replaced container names one that does not.
            if output is None:
                output = tmp / f'{task_id}.output'
                output.write_text('', encoding='utf-8')
            return {'type': 'user', 'message': {'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': 't-' + task_id,
                 'content': extra + 'Command running in background with ID: '
                            f'{task_id}. Output is being written to: {output}. '
                            'You will be notified when it completes.'}]}}

        def helper(agent_id):
            return {'type': 'user', 'message': {'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': 'a-' + agent_id,
                 'content': [{'type': 'text', 'text':
                              'Async agent launched successfully. (internal)\n'
                              f'agentId: {agent_id} (internal ID)\nThe agent '
                              'is working in the background.'}]}]}}

        def notice(task_id, status=None, summary='', event=''):
            body = f'<task-id>{task_id}</task-id>'
            body += f'<status>{status}</status>' if status else ''
            body += f'<summary>{summary}</summary>' if summary else ''
            body += f'<event>{event}</event>' if event else ''
            return f'<task-notification>\n{body}\n</task-notification>'

        def wake(text):
            return {'type': 'user', 'origin': {'kind': 'task-notification'},
                    'message': {'role': 'user', 'content': text}}

        def said(t):
            return {'type': 'assistant', 'message': {
                'usage': {'input_tokens': 2},
                'content': [{'type': 'text', 'text': t}] if t else
                           [{'type': 'tool_use', 'id': 'u', 'name': 'Bash',
                             'input': {}}]}}

        def transcript(name, rows):
            path = tmp / name
            path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n',
                            encoding='utf-8')
            return path

        def run(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx)],
                input=json.dumps({'transcript_path': str(path)}),
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        report = ('Individual passed.\n\n## Boildown\n- The work of this '
                  'session is now on: `staging` (individual).\n')
        opening = [human('Debut all four'), said(''), started('aaa'),
                   started('bbb'), said('Both running.\n\n## Boildown\n- x\n')]
        done_ok = 'Background command "a" completed (exit code 0)'

        r1 = run(transcript('one-of-two.jsonl', opening + [
            wake(notice('aaa', 'completed', done_ok)), said(report)]))
        cases.append(('one job of two done: a report is refused, naming the '
                      'one still running and asking for one waiting line',
                      r1.returncode == 2 and 'bbb' in r1.stderr
                      and 'Output ONE line naming the wait' in r1.stderr
                      and 'Output NOTHING' not in r1.stderr,
                      f'exit {r1.returncode}: {r1.stderr[:300]}'))

        r2 = run(transcript('progress.jsonl', [
            human('watch it'), said('Watching.\n\n## Boildown\n- x\n'),
            wake(notice('mon', event='individual done: exit 0')),
            said('Individual passed.')]))
        cases.append(('a Monitor progress event, nothing else running: prose '
                      'is refused', r2.returncode == 2
                      and 'progress event' in r2.stderr,
                      f'exit {r2.returncode}: {r2.stderr[:300]}'))

        r3 = run(transcript('silent.jsonl', opening[:-1] + [
            said('Started, no closing section here.'),
            wake(notice('aaa', 'completed', done_ok)), said('')]))
        cases.append(('negative control: a silent wake passes, and is not '
                      'judged by the last turn\'s words',
                      r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:200]}'))

        # One waiting line is what a quiet wake owes (2026-10-06): an empty
        # turn makes the harness ask for visible output.
        r3b = run(transcript('wait-line.jsonl', opening[:-1] + [
            said('Started, no closing section here.'),
            wake(notice('aaa', 'completed', done_ok)),
            said('(Waiting on bbb.)')]))
        cases.append(('one waiting line in parentheses passes on a quiet wake',
                      r3b.returncode == 0, f'exit {r3b.returncode}: {r3b.stderr[:200]}'))
        r3c = run(transcript('two-lines.jsonl', opening[:-1] + [
            said('Started, no closing section here.'),
            wake(notice('aaa', 'completed', done_ok)),
            said('(Waiting on bbb.)\nAlso, aaa passed.')]))
        cases.append(('...but a second line makes it a report, refused',
                      r3c.returncode == 2, f'exit {r3c.returncode}: {r3c.stderr[:200]}'))

        ended_mid_turn = {'type': 'attachment', 'attachment': {
            'type': 'queued_command',
            'prompt': notice('bbb', 'completed', done_ok)}}
        last = opening + [ended_mid_turn, wake(notice('aaa', 'completed', done_ok))]
        r4 = run(transcript('last-done.jsonl', last + [said(report)]))
        cases.append(('negative control: the last job done, the one report with '
                      'its Boildown passes (the other ended mid-turn)',
                      r4.returncode == 0, f'exit {r4.returncode}: {r4.stderr[:200]}'))

        r5 = run(transcript('last-done-bare.jsonl', last + [
            said('All four passed.')]))
        cases.append(('the batch\'s one report still needs its Boildown',
                      r5.returncode == 2 and 'HEADING' in r5.stderr,
                      f'exit {r5.returncode}: {r5.stderr[:200]}'))

        r6 = run(transcript('failed.jsonl', opening + [
            wake(notice('aaa', 'completed',
                        'Background command "a" completed (exit code 1)')),
            said(report)]))
        cases.append(('negative control: a wake reporting a failure may speak '
                      'while the batch runs', r6.returncode == 0,
                      f'exit {r6.returncode}: {r6.stderr[:200]}'))

        quoted = [human('show me'), said(''),
                  started('aaa'),
                  {'type': 'user', 'message': {'role': 'user', 'content': [
                      {'type': 'tool_result', 'tool_use_id': 'cat',
                       'content': 'log says: Command running in background '
                                  'with ID: zzz.'}]}},
                  said('Running.\n\n## Boildown\n- x\n'),
                  wake(notice('aaa', 'completed', done_ok)), said(report)]
        r7 = run(transcript('quoted.jsonl', quoted))
        cases.append(('negative control: printed text quoting the started line '
                      'starts no job', r7.returncode == 0,
                      f'exit {r7.returncode}: {r7.stderr[:200]}'))

        r8 = run(transcript('human.jsonl', opening + [
            human('how is it going?'), said('Still running.')]))
        cases.append(('a person\'s question mid-batch is answered as ever: '
                      'the Boildown is still required',
                      r8.returncode == 2 and 'HEADING' in r8.stderr,
                      f'exit {r8.returncode}: {r8.stderr[:200]}'))

        # 2026-10-31: a job started in a container since replaced (its
        # output file is not on this machine) is not running; the gate held
        # one such job "still running" for eight hours.
        dead = [human('Debut all four'), said(''),
                started('old', output=tmp / 'gone-container' / 'old.output'),
                started('aaa'), said('Both running.\n\n## Boildown\n- x\n')]
        r9 = run(transcript('dead-job.jsonl', dead + [
            wake(notice('aaa', 'completed', done_ok)), said(report)]))
        cases.append(('a job whose output file is gone (an earlier container) '
                      'is not running: the last live job\'s report passes',
                      r9.returncode == 0, f'exit {r9.returncode}: {r9.stderr[:300]}'))
        helpers = [human('check it'), said(''), helper('agone'), helper('agtwo'),
                   said('Two helpers on it.\n\n## Boildown\n- x\n')]
        r10 = run(transcript('helpers.jsonl', helpers + [
            wake(notice('agone', 'completed', 'Agent "one" finished')),
            said('(Waiting on the second helper.)')]))
        cases.append(('one helper of two done: one waiting line passes',
                      r10.returncode == 0, f'exit {r10.returncode}: {r10.stderr[:300]}'))
        r11 = run(transcript('helpers-report.jsonl', helpers + [
            wake(notice('agone', 'completed', 'Agent "one" finished')),
            said(report)]))
        cases.append(('...and a full report while the other helper runs is '
                      'refused, naming it',
                      r11.returncode == 2 and 'agtwo' in r11.stderr,
                      f'exit {r11.returncode}: {r11.stderr[:300]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_reply_check_requires_the_boildown_first_line():
    """`require_first_item_under_heading` refuses a Boildown whose first
    bullet does not say where the work is.

    Morgan, 2026-09-29: the first bullet under The Boildown names the branch
    the session's work is on and the stage it finished, in every reply
    (practice: the-boildown).

    practice: control-asserts-which-failure -- the positive cases assert the
    guard's own message; the negatives prove the right line passes with or
    without bold, and that a reply with no heading is left to the heading
    check rather than reported twice.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-firstitem-'))
    cases = []
    try:
        fx = tmp / 'repo'
        fx.mkdir()
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-first-item',
            'require_first_item_under_heading': {
                'heading': 'boildown',
                'matching': r'^\s*the work of this session is now on\s*:'},
        }]), encoding='utf-8')

        def replycheck(name, text):
            q = tmp / name
            q.write_text(text, encoding='utf-8')
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(q)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        r1 = replycheck('bad.md', 'Done.\n\n## The Boildown\n\n'
                                  '- **Your next steps.** Nothing.\n')
        cases.append(('a Boildown opening on another bullet is refused, naming '
                      'the requirement',
                      r1.returncode == 2 and 'first bullet' in r1.stderr,
                      f'exit {r1.returncode}: {r1.stderr[:200]}'))

        r2 = replycheck('prose.md', '## The Boildown\n\nSome prose first.\n\n'
                                    '- The work of this session is now on: x\n')
        cases.append(('a Boildown opening on prose, not a bullet, is refused',
                      r2.returncode == 2, f'exit {r2.returncode}'))

        r3 = replycheck('good.md', '## The Boildown\n\n- **The work of this '
                                   'session is now on:** `staging` (you have '
                                   'finished step 3 of 5, Booked)\n- Next.\n')
        cases.append(('negative control: the bold first line passes',
                      r3.returncode == 0, f'exit {r3.returncode}: {r3.stderr[:160]}'))

        r4 = replycheck('plain.md', '## The Boildown\n\n- The work of this '
                                    'session is now on: no branch yet (you have '
                                    'finished step 1 of 5, Consider)\n')
        cases.append(('negative control: the plain first line passes',
                      r4.returncode == 0, f'exit {r4.returncode}: {r4.stderr[:160]}'))

        r5 = replycheck('none.md', 'No heading at all.\n')
        cases.append(('negative control: no heading is the heading check\'s '
                      'case, not this one',
                      r5.returncode == 0, f'exit {r5.returncode}: {r5.stderr[:160]}'))

        # The first line leads with what is not landed (Morgan, 2026-10-19,
        # decided): "now on: `staging` (BestPractice) ..., and four open pull
        # requests" was read as all of it on staging, and four missed a
        # Produce. In process, with this session's unlanded branches planted.
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_reply_check as _rc
        lead = [{'practice': 'fixture-first-line',
                 'require_first_item_leads_with_unlanded': {'heading': 'boildown'}}]
        saved = _rc._unlanded_names

        def kinds(line, unlanded):
            _rc._unlanded_names = lambda *a, **k: list(unlanded)
            return [v['kind'] for v in _rc.violations(
                'x\n\n## The Boildown\n- **The work of this session is now on:** '
                + line + '\n- Next.\n', lead)]
        try:
            pr = ['2026-10-19-someone-fix-abcde-fghij']
            cases.append(('the line that caused the incident is refused while a '
                          'branch is unlanded',
                          kinds('`staging` (BestPractice) for one change, and four '
                                'open pull requests into `staging`', pr)
                          == ['first_item_unlanded'], ''))
            cases.append(('negative control: counts and NOT first pass',
                          kinds('4 of 5 changes NOT on `staging` yet (open pull '
                                'requests); 1 is on `staging`', pr) == [], ''))
            cases.append(('negative control: with everything landed, `staging` '
                          'alone passes', kinds('`staging` (BestPractice)', []) == [], ''))
            cases.append(('a branch name holding the word main names no tier',
                          kinds('the open pull request from red-main-counts', pr)
                          == [], ''))
            cases.append(('a line silent about the unlanded work is refused',
                          kinds('BestPractice, five changes', pr)
                          == ['first_item_unlanded'], ''))
            # 2026-10-20: one refusal asked for the one-line repeat form and
            # for the not-landed lead, which that form had no room for. Both
            # conditions true: the form the repeat refusal now hands over,
            # from the real reply_check.json entry, passes the lead check;
            # the plain form it used to hand over does not.
            rep = next(e['require_section_not_repeated'] for e in json.loads(
                (ROOT / 'reply_check.json').read_text(encoding='utf-8'))
                if e.get('require_section_not_repeated'))

            def alone(line):
                _rc._unlanded_names = lambda *a, **k: list(pr)
                return [v['kind'] for v in _rc.violations(
                    'x\n\n## The Boildown\n' + line + '\n', lead)]
            filled = _rc.one_line_form(rep, pr).replace(
                '<where the rest is>', '`staging`')
            cases.append(('while a branch is unlanded, the one-line repeat form '
                          'handed over passes the not-landed lead check',
                          alone(filled) == [] and pr[0] in filled, filled))
            cases.append(('negative control: the plain one-line form is refused '
                          'then', alone(rep['one_line'].replace(
                              '<where it is>', '`staging`')) == ['first_item_unlanded'], ''))
            cases.append(('with nothing unlanded, the plain form is handed over',
                          _rc.one_line_form(rep, []) == rep['one_line'], ''))
        finally:
            _rc._unlanded_names = saved
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_reply_check_wants_an_ask_to_state_its_question():
    """`require_ask_states_its_question` refuses a "Your next steps" bullet
    that asks for an answer without carrying the question.

    Morgan, 2026-10-29 (strength: decided), after hours away: "you
    mentioned like 8 times I need to answer the [voice repo] question but
    I scrolled and scrolled and I can't find it ... how do we fix this?"
    The two refused bullets below are the ones that session actually wrote.

    practice: control-asserts-which-failure -- the refusals assert the
    guard's own kind; the controls prove a bullet that states the question,
    one that asks nothing, and a reply with no such bullet all pass.
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_reply_check as _rc
    reqs = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
        encoding='utf-8')) if r.get('id') == 'boildown-ask-states-its-question']
    if not reqs:
        return (False, '', 'reply_check.json no longer declares '
                           'boildown-ask-states-its-question')

    def kinds(steps):
        reply = ('Done.\n\n## The Boildown\n- The work of this session is now '
                 'on: staging (you have finished step 3 of 5, Booked)\n'
                 + steps + '- You can archive this session.\n')
        return [v['kind'] for v in _rc.violations(reply, reqs)]

    refused = 'ask_without_question'
    cases = [
        ('a bare yes-or-no with a pick but no stakes is refused',
         kinds("- **Your next steps:** yes or no on syncing the book's voice "
               "pack from the voice repo. My pick is yes. It stays in the open "
               "item if you don't answer.\n") == [refused]),
        ('a pointer to "the X question" is refused',
         kinds('- **Your next steps:** the voice pack question is the only '
               'one open, as before. It waits in [the open item](todo/x.md).\n')
         == [refused]),
        ('a sub-bullet saying "answer the question above" is refused on its own',
         kinds('- **Your next steps:**\n  - Paste the prompt below into a new '
               'session rooted in BestPractice.\n  - Answer the question '
               'above.\n') == [refused]),
        ('negative control: a bullet that states the question, what yes and no '
         'do, and the pick passes',
         kinds("- **Your next steps:** should the book's voice rules be "
               'refreshed from the newer copy in the voice repo? Yes means the '
               'next voice pass uses the new rules; no keeps the book on the '
               'copy it has now. My pick is yes. If you say nothing it waits '
               'in the open item.\n') == []),
        ('negative control: a step that asks nothing passes',
         kinds('- **Your next steps:** paste the prompt below into a new '
               'session rooted in BestPractice.\n') == []),
        ('negative control: "Nothing blocking" passes',
         kinds('- **Your next steps:** Nothing blocking for you to do now.\n')
         == []),
        ('negative control: an ask outside Your next steps is not read',
         kinds('- Process idea: should the gate also read item 2?\n') == []),
    ]
    # The repeat rule's one-line form must not swallow a question still
    # waiting: the first line plus the restated ask is that form now.
    both = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
        encoding='utf-8')) if r.get('id') in (
            'boildown-ask-states-its-question', 'boildown-not-repeated')]
    first = ('- The work of this session is now on: staging (you have '
             'finished step 3 of 5, Booked).\n')
    ask = ("- **Your next steps:** should the book's voice rules be refreshed "
           'from the voice repo? Yes means the next voice pass uses them; no '
           'keeps the old copy. My pick is yes.\n')
    arch = "- Don't archive this session.\n"
    tl = [(1000, 'Earlier.\n\n## Boildown\n' + first + ask + arch)]

    def rep(body):
        return [v['kind'] for v in _rc.violations(
            'Now.\n\n## Boildown\n' + body, both, timeline=tl)]
    cases += [
        ('the first line plus a restated ask is not refused as a repeat',
         rep(first + ask) == []),
        ('a repeat beyond the restated ask is still refused',
         rep(first + ask + arch) == ['repeat']),
    ]
    bad = [n for n, ok in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_reply_check_wants_a_finished_plan_to_ask_and_a_hold_to_say_why():
    """`require_finished_plan_asks_to_act` refuses a reply that finishes a
    plan without asking to act on it; `require_hold_names_what_runs`
    refuses "Don't archive this session" beside a Your next steps that gives
    the person nothing, unless What's blocking says what runs, where and
    when the session acts next.

    Morgan, 2026-10-30 (strength: decided): "You tell me not to archive this
    session, but you also tell me there's nothing for me to do. Are you
    doing anything? ... you made a plan ... nowhere did you suggest that we
    could act on this plan." The first hold case below is the shape that
    session wrote.

    practice: control-asserts-which-failure -- each refusal asserts its own
    kind; the controls prove a stated ask, a session already acting, a
    named hold, and a plain answer all pass, and that the two rules and
    boildown-ask-states-its-question agree on one reply.
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_reply_check as _rc
    ids = ('boildown-finished-plan-asks-to-act', 'boildown-hold-names-what-runs',
           'boildown-ask-states-its-question', 'the-boildown-no-contradiction')
    allreqs = json.loads((ROOT / 'reply_check.json').read_text(encoding='utf-8'))
    reqs = [r for r in allreqs if r.get('id') in ids[:3]
            or (r.get('practice') == 'the-boildown'
                and r.get('require_no_contradiction'))]
    if len([r for r in reqs if r.get('id') in ids[:2]]) != 2:
        return (False, '', 'reply_check.json no longer declares both '
                           'boildown-finished-plan-asks-to-act and '
                           'boildown-hold-names-what-runs')

    # The Consider trigger is the ladder set's, added over universal's rule
    # with "inherits": true (2026-10-31); universal alone does not carry it.
    # Built here rather than read from the set, so the fixture owns it.
    ladder_add = {'id': ids[0], 'inherits': True,
                  'require_finished_plan_asks_to_act': {
                      'stage_line': r'\bfinished step 1 of 5\b[^)]{0,10}\bConsider\b'}}
    universal = reqs
    reqs = [_rc.inherit_requirement(r, ladder_add) if r.get('id') == ids[0]
            else r for r in universal]

    def kinds(body, boildown, rules=None, **kw):
        return sorted(v['kind'] for v in _rc.violations(
            body + '\n\n## The Boildown\n' + boildown,
            reqs if rules is None else rules, **kw))
    consider = ('- The work of this session is now on: no branch yet (you '
                'have finished step 1 of 5, Consider)\n')
    booked = ('- The work of this session is now on: staging in BestPractice '
              '(you have finished step 3 of 5, Booked)\n')
    plan = 'Here is the plan: 1. add the check. 2. test it. 3. land it.'
    ask = ('- **Your next steps:** Do you want to act on this plan? Yes means '
           'I build the three steps and land them on staging, about 40 '
           'minutes; no leaves it here as a plan. My pick is yes.\n')
    nothing = '- **Your next steps:** Nothing for you to decide right now.\n'
    hold = "- Don't archive this session.\n"
    free = '- You can archive this session.\n'
    named = ("- **What's blocking:** step 3 is running in [the vendor session]"
             "(https://claude.ai/code/session_x); I start step 4 when it "
             'reports back, about 06:10 Buenos Aires time.\n')
    cases = [
        ('a Consider reply that makes a plan and never asks is refused, once '
         'the ladder adds its stage line',
         kinds(plan, consider + '- **Your next steps:** Nothing blocking for '
               'you to do now.\n' + free) == ['plan_without_ask']),
        ('universal alone carries no stage line, so the same reply is not '
         'read as a finished plan there',
         kinds(plan, consider + '- **Your next steps:** Nothing blocking for '
               'you to do now.\n' + free, rules=universal) == []),
        ('the added stage line is merged into universal\'s mapping, which '
         'keeps its ask and the rest',
         all(k in (r.get('require_finished_plan_asks_to_act') or {})
             for r in reqs if r.get('id') == ids[0]
             for k in ('stage_line', 'ask', 'heading', 'plan_words'))),
        ('a turn that wrote a plan file and never asks is refused',
         kinds('Written up.', booked + '- **Your next steps:** read it.\n' + free,
               written=['/r/spec/NEW_PLAN.md']) == ['plan_without_ask']),
        ('a new **Plan:** line with no ask or tell is refused',
         kinds('Started.', booked + nothing + '- **Plan:** [the plan](spec/X_PLAN.md), '
               'steps 2-4 left.\n' + named + hold, timeline=[(1, 'Earlier.')])
         == ['plan_without_ask']),
        ('"Don\'t archive" beside nothing for him, reason only implied, is refused',
         kinds('Waiting.', booked + nothing + '- Sessions this one spawned: '
               '[step 3](https://claude.ai/code/session_x).\n' + hold)
         == ['hold_without_reason']),
        ('a What\'s blocking line that says no where or when is refused',
         kinds('Waiting.', booked + nothing + "- **What's blocking:** the plan "
               'is still going.\n' + hold) == ['hold_without_reason']),
        ('negative control: the plan ask with its stakes and pick passes, and '
         'boildown-ask-states-its-question agrees',
         kinds(plan, consider + ask + free) == []),
        ('negative control: the bare ask, no stakes, is refused by the older '
         'rule, not this one',
         kinds(plan, consider + '- **Your next steps:** Do you want to act on '
               'this plan?\n' + free) == ['ask_without_question']),
        ('negative control: a session already acting says so and passes',
         kinds('Started.', booked + nothing + "- **What's blocking:** **Plan:** "
               "I'm acting on this plan: step 3 is running in [the vendor "
               'session](https://claude.ai/code/session_x); I start step 4 '
               'when it reports back, about 06:10 Buenos Aires time.\n' + hold)
         == []),
        ('negative control: a named hold passes, and the "nothing blocking" '
         'pair steps aside for it',
         kinds('Waiting.', booked + '- **Your next steps:** Nothing blocking '
               'for you to do now.\n' + named + hold) == []),
        ('negative control: "nothing blocking" plus "Don\'t archive" with no '
         'What\'s blocking line is still a contradiction',
         'contradiction' in kinds('Waiting.', booked + '- **Your next steps:** '
                                  'Nothing blocking for you to do now.\n' + hold)),
        ('negative control: a hold the person owes an action for is not read',
         kinds('Waiting.', booked + '- **Your next steps:** merge [the pull '
               'request](https://github.com/o/r/pull/1): the work cannot land '
               'without it.\n' + hold) == []),
        # 2026-10-31 (Morgan, strength: decided): a hold beside a go-ahead
        # any session can start later is refused -- it names no blocker.
        ('a hold beside a go-ahead that can wait is refused, naming the list',
         kinds('Done.', booked + '- **Your next steps:** to roll it out, say '
               '"Update All Vendors and merge them". My pick is yes; without '
               'it, the rollout waits.\n' + hold) == ['hold_without_blocker']),
        ('...and the same hold naming a real blocker passes',
         kinds('Done.', booked + '- **Your next steps:** to roll it out, say '
               '"Update All Vendors and merge them". My pick is yes.\n'
               "- What's blocking: two commits exist only in this container, "
               'not pushed yet.\n' + hold) == []),
        ('negative control: a plain answer on Consider with no plan passes',
         kinds('The gate reads the transcript.', consider
               + '- **Your next steps:** Nothing blocking for you to do now.\n'
               + free) == []),
        ('negative control: a **Plan:** line the last reply carried is not new',
         kinds('Still going.', booked + nothing + '- **Plan:** [the plan]'
               '(spec/X_PLAN.md), steps 3-4 left.\n' + named + hold,
               timeline=[(1, 'Earlier.\n\n## The Boildown\n' + booked
                          + '- **Plan:** [the plan](spec/X_PLAN.md), steps '
                          '2-4 left.\n' + hold)]) == []),
    ]
    bad = [n for n, ok in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


@_without_session_id
def check_archive_guard_refuses_work_left_on_a_feature_branch():
    """`require_landed_if_says` refuses the archive sentence while a feature
    branch holds work its repo has not landed, and accepts it once each such
    branch is named in a `**Branch disposition:** BRANCH -- drop` line
    (spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md, step 7).

    Two halves, because they fail differently. The FINDER is run on a
    fixture repo with a real feature branch ahead of its landing branch, so
    the parse of precedent_gate's NOT YET LANDED line is tested against the
    line that function really prints. The VERDICT is run with the finder
    pinned, so the escape and its negative controls do not depend on
    whatever this machine's own clones happen to hold. Owns its state.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_reply_check as rc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='archive-guard-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='f@example.com')

    def git(*a, cwd):
        return subprocess.run(['git', *a], cwd=str(cwd), env=env,
                              capture_output=True, text=True)
    cases = []
    real = rc._stranded_branches
    try:
        origin = tmp / 'origin.git'
        git('init', '-q', '--bare', '-b', 'main', str(origin), cwd=tmp)
        repo = tmp / 'repo'
        git('clone', '-q', str(origin), str(repo), cwd=tmp)
        (repo / 'precedent.json').write_text('{"base_branch": "main"}\n', encoding='utf-8')
        git('add', '-A', cwd=repo); git('commit', '-qm', 'base', cwd=repo)
        git('push', '-q', 'origin', 'HEAD:main', cwd=repo)
        git('fetch', '-q', 'origin', cwd=repo)
        git('checkout', '-q', '-b', 'claude/fixture-abc123', cwd=repo)
        (repo / 'work.md').write_text('finished work\n', encoding='utf-8')
        git('add', '-A', cwd=repo); git('commit', '-qm', 'work', cwd=repo)

        found = rc._stranded_branches(str(repo), siblings=False)
        cases.append(('the finder reports a feature branch ahead of its landing branch',
                      ('this checkout', 'claude/fixture-abc123') in found, f'{found}'))
        git('checkout', '-q', 'main', cwd=repo)
        clean = rc._stranded_branches(str(repo), siblings=False)
        cases.append(('negative control: on the landing branch itself, nothing is stranded',
                      clean == [], f'{clean}'))

        rc._stranded_branches = lambda *a, **k: [('this checkout', 'claude/fixture-abc123')]
        req = [{'practice': 'planted-ladder-rule', '_source': 'individual/fixture',
                'require_landed_if_says': ['You can archive this session']}]
        kinds = lambda text: [v['kind'] for v in rc.violations(text, req)]
        cases += [
            ('the archive sentence is refused while work sits on a feature branch',
             'landed' in kinds('Done.\n\nYou can archive this session.'), ''),
            ('a **Branch disposition:** line naming that branch lets it through',
             'landed' not in kinds('**Branch disposition:** claude/fixture-abc123 -- '
                                   'drop (superseded)\n\nYou can archive this session.'), ''),
            ('negative control: a disposition naming a DIFFERENT branch does not',
             'landed' in kinds('**Branch disposition:** claude/other -- drop (x)\n\n'
                               'You can archive this session.'), ''),
            ('negative control: "Don\'t archive this session" is never refused by it',
             'landed' not in kinds("Don't archive this session."), ''),
        ]
    finally:
        rc._stranded_branches = real
        shutil.rmtree(tmp, ignore_errors=True)
    ok = all(passed for _, passed, _ in cases)
    for name, passed, detail in cases:
        if not passed:
            print(f"  archive guard did NOT behave as stated: {name} [{detail}]")
    check(f'the archive guard refuses work left on a feature branch, and '
          f'accepts a named drop ({len(cases)} stated cases)', ok)


@_without_session_id
def check_archive_guard_waits_for_an_unfinished_plan():
    """`require_plan_done_if_says` refuses the archive sentence while the
    plan a `**Plan:**` line names still holds an unticked box, and accepts
    it once every box is ticked, the person's early end is quoted on a
    `**Plan ended early:**` line, or a `**Plan handed to:**` line links the
    session now carrying it (the-boildown blocker 5, Morgan,
    2026-10-19). The plan is a real file in a fixture directory, found both
    by a relative path and by a GitHub link to a clone beside it. Owns its
    state.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_reply_check as rc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='plan-guard-'))
    old = os.environ.get('CLAUDE_PROJECT_DIR')
    cases = []
    try:
        proj = tmp / 'Fixture'
        (proj / 'spec').mkdir(parents=True)
        plan = proj / 'spec' / 'FIXTURE_PLAN.md'
        plan.write_text('# Plan\n\n- [x] Step 1: write it\n- [ ] Step 2: ship it\n',
                        encoding='utf-8')
        (proj / 'spec' / 'NO_BOXES.md').write_text('# Notes\n\nStep 1, then 2.\n',
                                                   encoding='utf-8')
        os.environ['CLAUDE_PROJECT_DIR'] = str(proj)
        req = [{'practice': 'the-boildown', '_source': 'universal/fixture',
                'require_plan_done_if_says': ['You can archive this session']}]
        kinds = lambda text: [v['kind'] for v in rc.violations(text, req)]
        rel = '- **Plan:** [the plan](spec/FIXTURE_PLAN.md)\n\nYou can archive this session.'
        link = ('- **Plan:** https://github.com/someone/fixture/blob/staging/'
                'spec/FIXTURE_PLAN.md\n\nYou can archive this session.')
        cases += [
            ('refused while a step is unticked (relative path)', 'plan' in kinds(rel), ''),
            ('refused while a step is unticked (GitHub link, case-blind repo name)',
             'plan' in kinds(link), ''),
            ('a quoted early end lets it through',
             'plan' not in kinds(rel.replace('\n\n', '\n- **Plan ended early:** '
                                             '"stop after step 1"\n\n')), ''),
            ('negative control: an empty early-end line does not',
             'plan' in kinds(rel.replace('\n\n', '\n- **Plan ended early:**\n\n')), ''),
            ('a **Plan handed to:** line with a session link lets it through',
             'plan' not in kinds(rel.replace('\n\n', '\n- **Plan handed to:** '
                                             'https://claude.ai/code/session_01Abc\n\n')), ''),
            ('negative control: a **Plan handed to:** line with no session link does not',
             'plan' in kinds(rel.replace('\n\n', '\n- **Plan handed to:** another one\n\n')), ''),
            ('negative control: "Don\'t archive this session" is never refused by it',
             'plan' not in kinds(rel.replace('You can', "Don't")), ''),
            ('negative control: a plan with no checklist is not judged',
             'plan' not in kinds(rel.replace('FIXTURE_PLAN', 'NO_BOXES')), ''),
            ('negative control: a missing plan file is not judged',
             'plan' not in kinds(rel.replace('FIXTURE_PLAN', 'GONE')), ''),
        ]
        plan.write_text('# Plan\n\n- [x] Step 1\n- [x] Step 2\n', encoding='utf-8')
        cases.append(('accepted once every box is ticked', 'plan' not in kinds(rel), ''))
    finally:
        if old is None:
            os.environ.pop('CLAUDE_PROJECT_DIR', None)
        else:
            os.environ['CLAUDE_PROJECT_DIR'] = old
        shutil.rmtree(tmp, ignore_errors=True)
    ok = all(passed for _, passed, _ in cases)
    for name, passed, detail in cases:
        if not passed:
            print(f"  plan guard did NOT behave as stated: {name} [{detail}]")
    check(f'the archive guard waits for an unfinished plan, and accepts a '
          f'quoted early end ({len(cases)} stated cases)', ok)


def check_gate_drops_a_practice_another_source_replaced():
    """precedent_gate.py seeds its list from this repo's own practices/, then
    lays resolution over it. A universal practice that an individual set
    replaces through `overrides:` is still a file here, and resolution no
    longer carries it, so it was listed as "level unknown -- this source did
    not resolve" on every reply gate, beside the rule that replaced it
    (2026-09-30). Planted: a universal catalogue with one reply-gate
    practice, and an individual set whose practice overrides it.
    Discriminating cases: the replacing practice is listed at its level; the
    replaced one is not listed at all; and with no override, the universal
    one is listed as before (the control)."""
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='gate-override-'))
    cases = []
    try:
        repo, ind = tmp / 'repo', tmp / 'mine'
        shutil.copytree(ROOT / 'tools', repo / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        (repo / 'practices').mkdir()
        (ind / 'practices').mkdir(parents=True)
        base = (ROOT / 'practices' / 'session-title-names-the-difference.md'
                ).read_text(encoding='utf-8')
        (repo / 'practices' / 'fixture-replaced.md').write_text(
            base.replace('slug:        session-title-names-the-difference',
                         'slug:        fixture-replaced'), encoding='utf-8')
        mine = (base.replace('slug:        session-title-names-the-difference',
                             'slug:        fixture-replacing'))
        (ind / 'practices' / 'fixture-replacing.md').write_text(
            mine, encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        cfg = tmp / 'config.json'
        cfg.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'fixture-mine', 'path': str(ind)}}), encoding='utf-8')

        def gate():
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_gate.py'),
                 'reply'], capture_output=True, text=True, cwd=str(repo),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(cfg),
                     'HOME': str(tmp)})
            return r.stdout + r.stderr

        out = gate()
        cases.append(('with no override, both are listed (the control)',
                      '### fixture-replaced (' in out and
                      '### fixture-replacing (individual/fixture-mine)' in out,
                      failure_detail(out, 400)))
        (ind / 'practices' / 'fixture-replacing.md').write_text(
            mine.replace('overrides:   null', 'overrides:   fixture-replaced'),
            encoding='utf-8')
        out = gate()
        cases.append(('the replacing practice is listed at its own level',
                      '### fixture-replacing (individual/fixture-mine)' in out,
                      failure_detail(out, 400)))
        cases.append(('THE CASE THIS EXISTS FOR: the replaced practice is not '
                      'listed, and nothing claims a source did not resolve',
                      '### fixture-replaced' not in out and
                      'did not resolve' not in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the gate drops a practice another source replaced '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_archive_line_is_refused_when_the_container_holds_only_copy_work():
    """`require_container_safe_if_says` refuses a reply that tells the person
    they can archive while this container holds work that exists nowhere else.

    The incident (2026-09-22): a very deep check pushed its own eight commits,
    verified them on origin, and closed with the archive line. Six commits sat
    unpushed in ~/precedent-individual in the same container -- which archiving
    releases -- in a clone the session had never been working in. Morgan:
    *"if changes are done locally but not pushed to main or
    precedent-beta-v01 then never never recommend 'You can archive this
    session' (unless the work is intended to be lost!)"*.
    (practice: cite-the-incident)

    Two halves, both planted. The SCANNER is run against a container this test
    builds -- a repo with an untracked file, a repo whose commits are all on a
    remote -- so its verdict is not a reading of whatever the real disk happens
    to hold. The WIRING is run against a stub scanner placed beside a copy of
    precedent_reply_check.py, which is the only way to assert "a failing scan
    refuses the turn" and "a passing scan does not" without a real container in
    each state. The no-scanner case is planted too: an engine vendored before
    the scanner existed must block nothing.

    practice: control-asserts-which-failure -- every positive here has the
    negative that proves it is the scan doing the work.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-container-'))
    cases = []
    scanner = ROOT / 'tools' / 'precedent_container_safe.py'

    def git(repo, *args):
        return subprocess.run(['git', *args], cwd=str(repo),
                              capture_output=True, text=True)

    try:
        # --- half one: the scanner, against a planted container ------------
        dirty = tmp / 'dirty'
        dirty.mkdir()
        git(dirty, 'init', '-q', '-b', 'main')
        (dirty / 'keep.txt').write_text('work that is only here\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(scanner), '--only', str(dirty)],
                           capture_output=True, text=True)
        cases.append(('an untracked file in a checkout makes the container '
                      'unsafe, and the report names the checkout',
                      r.returncode == 1 and 'keep.txt' in r.stdout
                      and str(dirty) in r.stdout,
                      f'exit {r.returncode}: {r.stdout[:200]}'))

        # Committed but on no remote -- the case the 09-22 incident actually
        # was, and the one a `git status` in the right directory still misses.
        git(dirty, 'add', 'keep.txt')
        git(dirty, 'config', 'user.email', 'harness@example.com')
        git(dirty, 'config', 'user.name', 'Harness')
        git(dirty, 'commit', '-qm', 'planted')
        r2 = subprocess.run([sys.executable, str(scanner), '--only', str(dirty)],
                            capture_output=True, text=True)
        cases.append(('committing it is not enough -- a commit no remote can '
                      'reach still fails',
                      r2.returncode == 1 and 'commit(s) on no remote' in r2.stdout,
                      f'exit {r2.returncode}: {r2.stdout[:200]}'))

        # …and pushing it IS. The negative control that proves the check is
        # about reachability from a remote and not about the file existing.
        bare = tmp / 'origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(bare)],
                       capture_output=True, text=True)
        git(dirty, 'remote', 'add', 'origin', str(bare))
        git(dirty, 'push', '-q', 'origin', 'main')
        r3 = subprocess.run([sys.executable, str(scanner), '--only', str(dirty)],
                            capture_output=True, text=True)
        cases.append(('negative control: once it is pushed, the same checkout '
                      'is safe',
                      r3.returncode == 0 and 'container safe' in r3.stdout,
                      f'exit {r3.returncode}: {r3.stdout[:200]}'))

        # --- half two: the wiring, against a stub scanner -------------------
        def engine(stub_rc):
            """A whole tools/ dir with the scanner swapped for a stub of a
            known exit code, or removed entirely when stub_rc is None.

            THE WHOLE DIRECTORY, not just precedent_reply_check.py. Copying
            that one file leaves it without precedent_resolve.py beside it,
            so it resolves NO sources, reads NO reply_check.json and exits 0
            on every input -- which every negative control here is also
            expecting. Three of the four wiring cases passed on that, and
            the positive one failed, which is how the whole check was found
            to have never run at all (2026-09-22).
            """
            d = tmp / f'engine{stub_rc}'
            shutil.copytree(ROOT / 'tools', d / 'tools')
            planted = d / 'tools' / 'precedent_container_safe.py'
            if stub_rc is None:
                planted.unlink(missing_ok=True)
            else:
                planted.write_text(
                    'import sys\n'
                    'print("PLANTED: ~/somewhere holds 6 commit(s) on no remote")\n'
                    f'sys.exit({stub_rc})\n', encoding='utf-8')
            return d / 'tools' / 'precedent_reply_check.py'

        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (fx / 'practices' / 'fixture-container.md').write_text(
            '---\n'
            'slug:        fixture-container\n'
            'title:       A fixture practice wired to the reply gate\n'
            'tier:        on-demand\n'
            'severity:    default\n'
            'applies_to:  []\n'
            'occasion:    "a fixture needs one practice on the reply gate"\n'
            'gates:       ["reply"]\n'
            'index_clause: "a fixture rule"\n'
            'checked_by:  null\n'
            'status:      active\n'
            'in_force_at: null\n'
            'supersedes:  []\n'
            'overrides:   null\n'
            'added:       null\n'
            'approved_by: null\n'
            '---\n\n## Rule\nA fixture rule, present so the reply gate has '
            'something registered to it.\n', encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-container',
            'require_container_safe_if_says': ['You can archive this session'],
        }]), encoding='utf-8')

        says = tmp / 'says.md'
        says.write_text('## The Boildown\n\nAll done.\n\n'
                        'You can archive this session.\n', encoding='utf-8')
        holds = tmp / 'holds.md'
        holds.write_text("## The Boildown\n\nPush it first.\n\n"
                         "Don't archive this session.\n", encoding='utf-8')

        def replycheck(engine_path, reply):
            return subprocess.run(
                [sys.executable, str(engine_path), '--repo', str(fx),
                 '--text', str(reply)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        unsafe_engine = engine(1)
        r4 = replycheck(unsafe_engine, says)
        cases.append(('the archive line is REFUSED when the scan fails, and '
                      'the refusal carries the scan\'s own report',
                      r4.returncode == 2 and 'PLANTED:' in r4.stderr,
                      f'exit {r4.returncode}: {r4.stderr[:250]}'))

        r5 = replycheck(unsafe_engine, holds)
        cases.append(('negative control: the same unsafe container does not '
                      'refuse a reply that says the OTHER line',
                      r5.returncode == 0, f'exit {r5.returncode}: {r5.stderr[:160]}'))

        safe_engine = engine(0)
        r6 = replycheck(safe_engine, says)
        cases.append(('negative control: a clean scan lets the archive line '
                      'through',
                      r6.returncode == 0, f'exit {r6.returncode}: {r6.stderr[:160]}'))

        r7 = replycheck(engine(None), says)
        cases.append(('an engine with no scanner beside it blocks NOTHING -- '
                      'an old vendor is not a broken reply',
                      r7.returncode == 0, f'exit {r7.returncode}: {r7.stderr[:160]}'))

        # The pre-reply print must carry the VERDICT, not just the rule:
        # a refusal the session was never warned about costs the reply twice.
        #
        # RUN AGAINST THE STUBBED ENGINES, not ROOT's. This called
        # ROOT/tools/precedent_gate.py, whose _container_report() scans the
        # REAL disk -- and the gate is deliberately silent when that scan
        # comes back clean, which its own comment says is the ordinary case.
        # So the assertion below held only while the machine running the
        # suite happened to be carrying unpushed work, and went red the
        # moment a session pushed its own. Found 2026-09-22 by a suite that
        # passed twice and then failed on the same commit, with the push in
        # between; measured both ways before this was rewritten. A check
        # that reads live disk state is not asserting the code's contract,
        # it is reporting the weather (practice: checks-plant-their-state,
        # whose Story is this incident and whose Install explains why it
        # carries no check of its own).
        def gate(engine_path):
            return subprocess.run(
                [sys.executable, str(engine_path.parent / 'precedent_gate.py'),
                 '--repo', str(fx), 'reply'],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        r8 = gate(unsafe_engine)
        cases.append(('the reply gate names this requirement before the '
                      'reply, when the container is the unsafe one',
                      'You can archive this session' in r8.stdout,
                      failure_detail(r8.stdout, 250)))

        # An advisory block that EXITS must not end the gate (2026-10-17).
        # The session check imports the scanner on one path -- a clone ahead
        # of its base -- and this test's stub scanner exits as it loads, so
        # in a container in that state the gate died before the verdict
        # above, and the case failed only there. Planted directly: a session
        # check whose remind() exits.
        exiting = tmp / 'engine_exiting'
        shutil.copytree(unsafe_engine.parent.parent, exiting)
        (exiting / 'tools' / 'precedent_session_check.py').write_text(
            'import sys\n'
            'def remind(prefix=None):\n'
            '    sys.exit(1)\n', encoding='utf-8')
        r8b = gate(exiting / 'tools' / 'precedent_reply_check.py')
        cases.append(('an advisory block that exits does not end the gate: '
                      'the verdict is still printed',
                      'You can archive this session' in r8b.stdout,
                      failure_detail(r8b.stdout, 250)))

        # A clean container at turn start is a snapshot, not the answer at
        # the end of the turn (2026-10-16: a consumer's closing turn wrote
        # two scratch files after this ran clean and was refused with no
        # warning). So the clean case says to look again -- and never the
        # refusal itself.
        r9 = gate(safe_engine)
        cases.append(('negative control: a clean container gets no refusal '
                      'warning, only the one line saying what this turn '
                      'writes still counts and to scan again before the line',
                      'DO NOT SAY' not in r9.stdout
                      and 'clean as this turn starts' in r9.stdout
                      and 'precedent_container_safe.py` again' in r9.stdout,
                      failure_detail(r9.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_compaction_offer_fires_on_context_growth():
    """The size-aware half of the reply check: a long session is REFUSED a
    reply that never says whether this is a cheap point to compact.

    The incident is practices/session-spend-follows-the-task.md's own Story.
    The rule was registered on the reply gate on 2026-09-13 and still did not
    fire once in the eleven hours after -- because the reply gate PRINTS, and
    printing happens after the reply it was meant to shape. Morgan, 2026-09-14:
    *"you never once recommended I compact a session - despite our updated
    rules."*

    Every case below owns its own transcript (practice: fixture-owns-its-state)
    -- a real session's JSONL would make the assertions depend on how long this
    container had been running.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-compact-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-compaction',
            'require_one_of': ['This is a cheap point to compact',
                               'Not a cheap point to compact'],
            'require_when_context_grew_tokens': 100000,
        }]), encoding='utf-8')

        def transcript(name, turns):
            """turns: [(context_tokens, reply_text), ...], oldest first."""
            path = tmp / name
            lines = []
            for ctx, text in turns:
                lines.append(json.dumps({
                    'type': 'assistant',
                    'message': {
                        'usage': {'input_tokens': 2,
                                  'cache_creation_input_tokens': 0,
                                  'cache_read_input_tokens': max(ctx - 2, 0)},
                        'content': [{'type': 'text', 'text': text}],
                    }}))
            path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return path

        def run(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx)],
                input=json.dumps({'transcript_path': str(path)}),
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        # A short session says nothing about compacting and is left alone.
        # This is the case that keeps the rule from becoming a nag: most
        # sessions never reach the threshold and must never see this message.
        short = run(transcript('short.jsonl', [
            (96000, 'Opening.'), (120000, 'Done. Nothing about compacting here.')]))
        cases.append(('a session that has grown less than the declared amount '
                      'is NOT blocked', short.returncode == 0, short.stderr[:200]))

        # The same reply, on a session that has grown past it.
        grown = run(transcript('grown.jsonl', [
            (96000, 'Opening.'), (150000, 'Middle.'),
            (205000, 'Done. Nothing about compacting here.')]))
        cases.append(('a session that HAS grown past it is blocked',
                      grown.returncode == 2, f'exit {grown.returncode}'))
        # control-asserts-which-failure: the exit code alone would pass even if
        # the block came from some other requirement entirely.
        cases.append(('...and the message names the sentence that is missing',
                      'cheap point to compact' in grown.stderr, grown.stderr[:200]))
        cases.append(('...and says how big the conversation actually is, since '
                      'the person is deciding against a number they cannot see',
                      '109,000' in grown.stderr or '≈109' in grown.stderr,
                      grown.stderr[:300]))

        # Both answers satisfy it. The honest negative matters as much as the
        # offer: mid-investigation the rule's own answer is to keep working,
        # and a check that accepted only the offer would push a session into
        # making one it does not mean.
        for phrase in ('This is a cheap point to compact if you want to.',
                       'Not a cheap point to compact -- we are mid-investigation.'):
            r = run(transcript('ok.jsonl', [
                (96000, 'Opening.'), (205000, f'Done. {phrase}')]))
            cases.append((f'a reply saying "{phrase[:28]}..." is not blocked',
                          r.returncode == 0, r.stderr[:200]))

        # Having said it once, the session is not asked again until the
        # conversation has grown another full increment.
        again = run(transcript('again.jsonl', [
            (96000, 'Opening.'),
            (205000, 'This is a cheap point to compact if you want to.'),
            (250000, 'More work. Nothing about compacting here.')]))
        cases.append(('after the offer is made, it is not demanded again until '
                      'the conversation has grown another increment',
                      again.returncode == 0, again.stderr[:200]))
        overdue = run(transcript('overdue.jsonl', [
            (96000, 'Opening.'),
            (205000, 'This is a cheap point to compact if you want to.'),
            (320000, 'Much more work. Nothing about compacting here.')]))
        cases.append(('...and IS demanded once it has',
                      overdue.returncode == 2, f'exit {overdue.returncode}'))

        # THE COMPACTION ITSELF. After one, the context drops and the
        # historical maximum does not, so a check reading the high-water mark
        # goes on demanding the offer from the one session that owes nothing.
        # The first draft of this did exactly that.
        # The offer is deliberately ABSENT before the compaction here: with one
        # present, both the buggy and the fixed reading come out silent, and
        # the case discriminates nothing.
        compacted = run(transcript('compacted.jsonl', [
            (96000, 'Opening.'),
            (240000, 'A long stretch of work, no offer made.'),
            (40000, 'Fresh after the compaction. Nothing about compacting here.')]))
        cases.append(('a session that has just been COMPACTED is not asked '
                      'again -- the check reads the latest context, not the '
                      'high-water mark', compacted.returncode == 0,
                      compacted.stderr[:200]))

        # A size condition nobody can evaluate must not block a reply.
        missing = run(tmp / 'no-such-transcript.jsonl')
        cases.append(('an unreadable transcript blocks nothing',
                      missing.returncode == 0, missing.stderr[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the compaction offer is demanded once a session has grown, and only '
          f'then ({len(cases)} stated cases)',
          not bad_cases,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad_cases))


def check_compaction_offer_owed_printed_at_turn_start():
    """The turn-start reply gate says whether the compact offer is owed.

    2026-09-28: the Boildown's compact offer is advisory, and the stop hook
    drops an unmet advisory requirement without a word, while the turn-start
    print told sessions to leave the line out until the stop hook asked. A
    session ran from about 80,000 tokens to about 783,000 without one compact
    line. Morgan: "you have not told me ever to compact this session." The
    gate now reads the transcript reply-gate.sh passes it and prints the
    answer. Each case owns its transcript (practice: fixture-owns-its-state).
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-compact-owed-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-compaction',
            'require_one_of': ['Now is a good time to compact the session'],
            'require_when_context_grew_tokens': 100000,
            'advisory': True,
        }]), encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(fx)], capture_output=True)

        def transcript(name, turns):
            path = tmp / name
            path.write_text(''.join(json.dumps({
                'type': 'assistant',
                'message': {'usage': {'input_tokens': 2,
                                      'cache_creation_input_tokens': 0,
                                      'cache_read_input_tokens': max(c - 2, 0)},
                            'content': [{'type': 'text', 'text': t}]}}) + '\n'
                for c, t in turns), encoding='utf-8')
            return path

        # The tools are linked into the fixture once, before any run: the
        # four runs below go side by side (2026-10-31; each is a whole
        # reply-gate.sh, about 10 s, and they share nothing but this
        # read-only fixture), and linking inside each run raced on the links.
        (fx / 'tools').mkdir(exist_ok=True)
        for f in ROOT.joinpath('tools').glob('*.py'):
            dst = fx / 'tools' / f.name
            if not dst.exists():
                dst.symlink_to(f)

        def start(path):
            # Through the hook itself, so the payload-to-env hand-off is what
            # is tested, not only the gate's reading of the variable.
            hook = ROOT / 'tools' / 'reply-gate.sh'
            payload = json.dumps({'transcript_path': str(path)}) if path else ''
            proc = subprocess.Popen(
                ['bash', str(hook)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, cwd=str(fx),
                env={**os.environ, 'CLAUDE_PROJECT_DIR': str(fx),
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})
            # Handed over now, not at finish(): the hook's first act is to
            # read stdin to its end, so a payload held back would hold every
            # run back until the one before it was read.
            proc.stdin.write(payload)
            proc.stdin.close()
            proc.stdin = None
            return proc

        def finish(proc):
            out, err = proc.communicate()
            return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)

        _started = {
            'owed': start(transcript('owed.jsonl', [
                (96000, 'Opening.'), (150000, 'Middle.'), (205000, 'Done.')])),
            'short': start(transcript('short.jsonl', [(96000, 'Opening.'),
                                                      (120000, 'Done.')])),
            'said': start(transcript('said.jsonl', [
                (96000, 'Opening.'),
                (205000, 'Now is a good time to compact the session.'),
                (250000, 'More.')])),
            'blind': start(None),
        }
        owed = finish(_started['owed'])
        cases.append(('a grown session is told the offer is OWED, with the '
                      'sentence to say', 'OWED IN THIS REPLY' in owed.stdout
                      and 'Now is a good time to compact the session' in owed.stdout,
                      failure_detail(owed.stdout, 400)))
        short = finish(_started['short'])
        cases.append(('a short session hears nothing about compacting',
                      'good time to compact' not in short.stdout, failure_detail(short.stdout, 400)))
        said = finish(_started['said'])
        cases.append(('once said, it is not owed again until another increment',
                      'good time to compact' not in said.stdout, failure_detail(said.stdout, 400)))
        blind = finish(_started['blind'])
        cases.append(('no transcript: it says it could not tell, and never '
                      'defers to the stop hook', 'could not be worked out'
                      in blind.stdout and 'stop hook is the thing'
                      not in blind.stdout, failure_detail(blind.stdout, 400)))
        cases.append(('the hook exits 0 every time -- a non-zero '
                      'UserPromptSubmit exit eats the message',
                      all(r.returncode == 0 for r in (owed, short, said, blind)),
                      ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the turn-start gate says when the compact offer is owed '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} ({d})' for n, d in bad))


def check_trivial_checkin_exempts_the_boildown_gate():
    """practices/the-boildown.md names one fixed template for a turn where
    nothing happened that is visible, or non-trivial, to the person --
    "Unchanged since the last update: <X>." -- and says that turn does not
    owe a fresh Boildown. Widened 2026-09-20 to cover any turn that shape
    fits, not only a scheduled wakeup or background-task notification --
    including one the stop hook itself forces, which is what prompted it:
    a practice-candidate false positive rechecking its own prior output
    produced two closing headings in a row with nothing between them.
    `precedent_reply_check.is_trivial_checkin()` is the mechanical half;
    this proves it actually exempts a reply from a real declared
    requirement, and the negative control proves an ordinary short reply
    that merely mentions the phrase in passing still has to carry one.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-trivial-checkin-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps({
            'practice': 'fixture-trivial-checkin',
            'require_heading_matching': 'boildown',
            'require_one_of': ['You can archive this session',
                               "Don't archive this session"],
        }), encoding='utf-8')

        def replycheck(text_path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(text_path)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        trivial = tmp / 'trivial.md'
        trivial.write_text('Unchanged since the last update: still waiting '
                           'on your answer.\n', encoding='utf-8')
        r1 = replycheck(trivial)
        cases.append(('a reply opening with the fixed trivial-check-in '
                      'template is not blocked, though it carries neither '
                      'the declared heading nor the declared sentence',
                      r1.returncode == 0, r1.stderr[:200]))

        bold = tmp / 'bold.md'
        bold.write_text('**Unchanged since the last update:** still '
                        'waiting on your answer.\n', encoding='utf-8')
        r2 = replycheck(bold)
        cases.append(('...and the same holds when the lead phrase is bolded',
                      r2.returncode == 0, r2.stderr[:200]))

        # The negative control: a reply that merely mentions the phrase
        # partway through, rather than opening with it, is an ordinary reply
        # and still owes the real closing section. Without this, the case
        # above would prove nothing about the match being anchored.
        mid = tmp / 'mid.md'
        mid.write_text('Some work happened. Unchanged since the last '
                       'update: still waiting on your answer.\n', encoding='utf-8')
        r3 = replycheck(mid)
        cases.append(('the control: the same phrase appearing MID-REPLY, '
                      'not at the start, does not exempt anything -- this '
                      'is a literal template match, not a keyword scan',
                      r3.returncode == 2, f'exit {r3.returncode}'))
        cases.append(('...and the block names the missing heading, same as '
                      'any other ordinary reply',
                      'MARKDOWN HEADING' in r3.stderr, r3.stderr[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the fixed trivial-check-in template exempts a reply from the '
          f'Boildown gate, anchored to the start of the reply '
          f'({len(cases)} stated cases)',
          not bad_cases,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad_cases))


def check_boildown_contradiction_spares_work_waiting_upstream():
    """"Still waiting upstream" beside "You can archive this session" is not
    a contradiction: the work sits in another repository's queue, not this
    session's. Nor is a due reminder's own line asking for an answer
    (2026-10-17, from a consuming repo: the reminder lives in todo/, so
    archiving loses nothing, and the two universal practices' required
    texts collided). The shipped reply_check.json refused exactly that reply
    (2026-09-28). Read from the real file, so the test is of the pattern that
    ships; the control is "still waiting" about this session's own work,
    which must still be refused.
    """
    import tempfile
    name = 'the Boildown contradiction spares work waiting upstream'
    shipped = json.loads((ROOT / 'reply_check.json').read_text(encoding='utf-8'))
    entry = next((e for e in shipped if any(
        c.get('if_says') == 'You can archive this session'
        for c in e.get('require_no_contradiction', []))), None)
    if entry is None:
        not_applicable(name, 'reply_check.json carries no archive contradiction')
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-upstream-'))
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (fx / 'reply_check.json').write_text(json.dumps([{
            'practice': 'fixture-contradiction',
            'require_no_contradiction': entry['require_no_contradiction']}]),
            encoding='utf-8')

        def replycheck(text):
            p = tmp / 'reply.md'
            p.write_text(text, encoding='utf-8')
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_reply_check.py'),
                 '--repo', str(fx), '--text', str(p)],
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})
        up = replycheck('## The Boildown\n\n- The six updater fixes are still '
                        'waiting upstream.\n\nYou can archive this session.\n')
        other = replycheck('## The Boildown\n\n- Its fix is still open in '
                           'another repo.\n\nYou can archive this session.\n')
        own = replycheck('## The Boildown\n\n- The pull request is still '
                         'waiting.\n\nYou can archive this session.\n')
        # 2026-10-01: a report about ANOTHER session's block is its state.
        theirs = replycheck('## The Boildown\n\n- Your Planning window '
                            'says it\'s blocked on an upstream bug; nothing here '
                            'is.\n\nYou can archive this session.\n')
        mine = replycheck('## The Boildown\n\n- This session is blocked on '
                          'your answer.\n\nYou can archive this session.\n')
        # 2026-10-17: a due reminder's line (todo-reminder) asks the person
        # something, but the item lives in todo/: archiving loses nothing.
        due = replycheck('## The Boildown\n\n- A reminder you asked for, due '
                         'since 2026-10-15: [Renew the domain](todo/x.md). Is it '
                         'done, does it get a new date, or is it dropped? It '
                         'still needs your answer.\n\nYou can archive this '
                         'session.\n')
        ask = replycheck('## The Boildown\n\n- The merge still needs your '
                         'approval. It is waiting on you.\n\nYou can archive '
                         'this session.\n')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cases = [
        ('"still waiting upstream" beside the archive sentence passes',
         up.returncode == 0),
        ('"still open in another repo" beside it passes', other.returncode == 0),
        ('control: a bare "still waiting" beside it is still refused',
         own.returncode == 2 and 'cannot both be true' in own.stderr),
        ('"blocked on" in a sentence about another window passes',
         theirs.returncode == 0),
        ('control: "this session is blocked on" is still refused',
         mine.returncode == 2 and 'cannot both be true' in mine.stderr),
        ('a due reminder\'s line ("A reminder you asked for ... still needs '
         'your answer") beside the archive sentence passes', due.returncode == 0),
        ('control: "needs your approval" on any other line is still refused',
         ask.returncode == 2 and 'cannot both be true' in ask.stderr),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {up.stderr[:300]}'))


def check_empty_commits_are_never_counted():
    """A commit that changes no file -- a merge, an empty commit -- is never
    counted where a person reads a branch count, never blocks a stop, and
    never makes a Promote think work is waiting.

    Morgan, 2026-09-27 (strength: decided): "let's have the system stop
    describing and/or reporting and/or mentioning empty merges", and the
    branch lines count "the number of commits ahead/behind that made changes
    to the repo". Every Promote into main leaves merge commits staging
    lacks, so a count by lineage is never zero and never means anything."""
    import tempfile, shutil as _shutil
    name = 'commits that change no file are never counted or reported'
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_gate as _pg, precedent_branches as _pb
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                   GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                   GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'))

        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a],
                                  capture_output=True, text=True, env=env)

        def out(cwd, *a):
            r = git(cwd, *a)
            return r.stdout.strip() if r.returncode == 0 else ''

        bare = tmp / 'origin.git'
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
        work = tmp / 'work'
        git(tmp, 'init', '-q', '-b', 'main', str(work))
        (work / 'a.txt').write_text('a\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'init')
        git(work, 'remote', 'add', 'origin', f'file://{bare}')
        for b in ('main', 'staging'):
            git(work, 'push', '-q', 'origin', f'HEAD:refs/heads/{b}')

        # staging gains an empty commit and an empty merge.
        git(work, 'checkout', '-q', '-b', 'staging')
        git(work, 'commit', '-q', '--allow-empty', '-m', 'empty')
        git(work, 'checkout', '-q', '-b', 'side', 'HEAD~1')
        git(work, 'commit', '-q', '--allow-empty', '-m', 'side empty')
        git(work, 'checkout', '-q', 'staging')
        git(work, 'merge', '-q', '--no-ff', '-m', 'empty merge', 'side')
        git(work, 'push', '-q', 'origin', 'staging')
        git(work, 'fetch', '-q', 'origin')

        cases.append(('an empty commit and an empty merge on staging: the '
                      'Boildown line counts nothing waiting',
                      _pg._unpromoted(work, 'main', out) == 0))
        cases.append(('and Promote finds nothing waiting to move',
                      _pb._new_commits(work, 'origin/main',
                                       'origin/staging') == []))

        # A stop with only empty commits unpushed is not blocked.
        hook = ROOT / '.claude' / 'hooks' / 'stop-git-check.sh'
        git(work, 'checkout', '-q', '-b', 'feature', 'origin/staging')
        git(work, 'push', '-q', '-u', 'origin', 'feature')
        git(work, 'commit', '-q', '--allow-empty', '-m', 'nothing')

        def stop():
            return subprocess.run(['bash', str(hook)], cwd=str(work), input='{}',
                                  capture_output=True, text=True, env=env)
        r = stop()
        cases.append(('only an empty commit unpushed: the stop hook lets the '
                      'turn end', r.returncode == 0))

        # One real commit among the empty ones counts as exactly one.
        (work / 'b.txt').write_text('b\n', encoding='utf-8')
        git(work, 'add', 'b.txt')
        git(work, 'commit', '-q', '-m', 'real')
        git(work, 'commit', '-q', '--allow-empty', '-m', 'nothing again')
        r = stop()
        cases.append(('one real commit among empty ones: the stop hook blocks '
                      'and says 1, not 3', r.returncode == 2
                      and '1 unpushed commit(s)' in r.stderr))
        git(work, 'push', '-q', 'origin', 'feature:staging')
        git(work, 'fetch', '-q', 'origin')
        cases.append(('and the Boildown line counts that one real commit',
                      _pg._unpromoted(work, 'main', out) == 1))
        cases.append(('Promote sees exactly that one commit',
                      len(_pb._new_commits(work, 'origin/main',
                                           'origin/staging')) == 1))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_reply_check_refuses_an_unlinked_branch_or_file():
    """require_no_bare_pattern, with a planted copy of the link patterns a set
    declares, refuses a reply naming a
    dated session branch or a file in code font with no link, lets a name
    linked once be named bare again, and leaves alone what has no page: a
    command, an absolute path, a filename template, a file that exists in
    no repository the session holds.

    2026-10-19 (Morgan: "Don't we have practice rules so when you mention
    files you always give links?"): a Boildown named a branch and a file
    with no link and passed, because the requirement was advisory and
    main() drops an advisory finding unseen. Negative control: declared
    advisory again, the discriminating case is not in the blocking set."""
    import precedent_reply_check as prc
    # The real patterns are the writing set's (its reply_check.json, since
    # 2026-10-19); these are a planted copy, under a made-up practice name,
    # so this tests the engine's require_no_bare_pattern and not one set.
    planted = [
        {"pattern": "\\bPR #\\d+\\b", "why": "zz", "repair": "zz: link it"},
        {"pattern": "\\bsession_[A-Za-z0-9-]+\\b", "why": "zz", "repair": "zz: link it"},
        {"pattern": "\\bgithub\\.com/[\\w.-]+/[\\w.-]+/pull/\\d+\\b", "why": "zz", "repair": "zz: link it"},
        {"pattern": "`(?:\\d{4}-\\d{2}-\\d{2}-[a-z0-9][a-z0-9.-]*|claude/[\\w.-]+)`", "why": "zz", "repair": "zz: link it"},
        {"pattern": "`(?![/~])(?:[\\w.-]+/)*[\\w-][\\w.-]*\\.(?:md|py|json|sh|ya?ml|html|toml|txt|csv|docx)`", "why": "zz", "repair": "zz: link it"},
        {"pattern": "\\bgithub\\.com/[\\w.-]+/[\\w.-]+/tree/[\\w/-]+(?:\\.[\\w/-]+)*", "why": "zz", "repair": "zz: link it"},
    ]
    reqs = [{'practice': 'zz-links', 'require_no_bare_pattern': planted,
             '_source': 'shared/zz-set'}]
    branch = '2026-10-19-someone-a-plan-ab12c-xy9z0'

    def blocking(text, rs=None):
        return [v for v in prc.violations(text, rs if rs is not None else reqs)
                if v['kind'] == 'bare_pattern' and not v['advisory']]
    cases = []
    v = blocking(f'Work is on `{branch}` (repo).')
    cases.append(('THE DISCRIMINATING CASE: a bare dated branch in code font is '
                  'refused, with a repair', len(v) == 1 and branch in v[0]['message']
                  and v[0].get('repair'), v))
    v = blocking('See `spec/PRACTICE_FORMAT.md` and `claude/some-branch-x1`.')
    cases.append(('a bare file path and a bare claude/ branch are both named',
                  len(v) == 2, v))
    # 2026-10-30: a file that is in no repository this session holds has no
    # page and no path, so naming it is not an unlinked mention. Negative
    # control, measured: with _names_no_file_or_branch returning False this
    # case fails and the one above still passes.
    v = blocking('The consumer writes `NO_SUCH_FILE_ANYWHERE_ZZ.json` and '
                 '`spec/NO_SUCH_PLAN_ZZ.md`.')
    cases.append(('a file name that is no file in any repository here passes',
                  not v, v))
    v = blocking(f'On [`{branch}`](https://example.com/tree/{branch}); '
                 f'later `{branch}` again, and [A_PLAN.md](https://e/spec/A_PLAN.md) '
                 f'then `A_PLAN.md`.')
    cases.append(('a name linked once may be named bare again', not v, v))
    v = blocking('Run `python3 tools/x.py --apply`; the scratch file is '
                 '`/tmp/s/out.md`; items are `todo-<date>-<slug>.md`; `main` (BestPractice).')
    cases.append(('a command, an absolute path, a template and a plain branch '
                  'word pass', not v, v))
    v = blocking('Paste into: a new session rooted in alex137/BestPractice.\n\n'
                 '```\nFor: a new session.\nSee PR #1314 and session_01AbCdEfGh, '
                 f'on `{branch}`.\n```\n')
    cases.append(('2026-10-20: inside a fenced paste block, where a link cannot '
                  'render, a bare mention passes', not v, v))
    v = blocking('```\nquoted\n```\nThen PR #1314 in prose.')
    cases.append(('...and the same mention after the fence closes is still refused',
                  len(v) == 1, v))
    soft = [dict(r, advisory=True) for r in reqs]
    v = blocking(f'Work is on `{branch}`.', soft)
    cases.append(('negative control: declared advisory, nothing blocks', not v, v))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the reply check refuses an unlinked branch or file '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_turn_start_names_what_the_last_reply_left_out():
    """The turn-start reply gate names an advisory requirement the LAST
    reply left out, and refuses nothing; a reply that met it gets no line.

    2026-10-19 (Morgan: "make them visible"): the archive-line and compaction
    requirements are advisory on his word (2026-09-17, "an absent one must
    never refuse the turn"), and an unmet advisory requirement reached
    nobody. Negative control: with the requirement not advisory, the gate
    prints no such line, since the stop hook refuses that one itself."""
    import tempfile, io, contextlib
    import precedent_gate as pg
    import precedent_reply_check as prc
    req = {'practice': 'the-boildown', '_source': 'universal/precedent',
           'require_one_of': ['You can archive this session',
                              "Don't archive this session"], 'advisory': True}
    cases = []
    with tempfile.TemporaryDirectory() as td:
        def run(reply, reqs):
            path = pathlib.Path(td) / 't.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in [
                {'type': 'user', 'message': {'role': 'user', 'content': 'hi'}},
                {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
                    {'type': 'text', 'text': reply}]}}]) + '\n', encoding='utf-8')
            old = os.environ.get('PRECEDENT_TRANSCRIPT_PATH')
            os.environ['PRECEDENT_TRANSCRIPT_PATH'] = str(path)
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    pg._print_advisories_missed(reqs, prc)
            finally:
                if old is None:
                    os.environ.pop('PRECEDENT_TRANSCRIPT_PATH', None)
                else:
                    os.environ['PRECEDENT_TRANSCRIPT_PATH'] = old
            return buf.getvalue()
        out = run('Done.\n\n## The Boildown\n\n- one\n', [req])
        cases.append(('THE DISCRIMINATING CASE: a last reply without the archive '
                      'line is named at turn start', 'left these out' in out
                      and 'You can archive this session' in out, out))
        out = run("Done.\n\n## The Boildown\n\n- Don't archive this session.\n", [req])
        cases.append(('a last reply that met it gets no line', not out, out))
        out = run('Done.\n\n## The Boildown\n\n- one\n', [dict(req, advisory=False)])
        cases.append(('negative control: a blocking requirement is not listed here',
                      not out, out))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'turn start names what the last reply left out '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_reply_gate_trims_for_standing_sessions_and_one_line_forms():
    """tools/precedent_reply_check.py, the five trims of 2026-10-20 (S.
    Alexander Jacobson, strength: decided): a standing session is held only
    to the requirements that guard work; a one-line reply is never also
    asked for what only a full one carries; a branch given up by name stays
    given up; and one pattern of a requirement can be advice.

    Negative controls: an ordinary session keeps every requirement, and a
    reply with no closing section at all is still refused."""
    import tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    prc = importlib.import_module('precedent_reply_check')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True, timeout=30)
        (repo / 'precedent.json').write_text(json.dumps(
            {'maintainer': {'session': 'session_TRIMTEST'}}), encoding='utf-8')
        reqs = [{'require_heading_matching': 'boildown'},
                {'require_container_safe_if_says': ['You can archive this session']},
                {'require_section_not_repeated': {'heading': 'boildown'}}]
        old = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID')
        try:
            os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = 'cse_TRIMTEST'
            kept = prc.for_this_session(reqs, repo)
            cases.append(('THE DISCRIMINATING CASE: the named standing session keeps '
                          'only the requirement that guards work',
                          kept == [reqs[1]], kept))
            os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = 'cse_SOMEONEELSE'
            cases.append(('negative control: any other session keeps every requirement',
                          prc.for_this_session(reqs, repo) == reqs, None))
        finally:
            if old is None:
                os.environ.pop('CLAUDE_CODE_REMOTE_SESSION_ID', None)
            else:
                os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = old
        one = ('Done.\n\n## The Boildown\n\n- The work of this session is now on: '
               'main, unchanged since the last update.\n')
        fake = [{'kind': 'first_item_unlanded', 'advisory': False, 'message': 'x'},
                {'kind': 'paired', 'advisory': False, 'message': 'y'},
                {'kind': 'container', 'advisory': False, 'message': 'z'}]
        got = prc._one_line_wins(fake, one, reqs)
        cases.append(('the one-line form is not also asked to list branches or links; '
                      'a finding that guards work stands', [b['kind'] for b in got] == ['container'],
                      got))
        cases.append(('negative control: a full reply keeps every finding',
                      prc._one_line_wins(fake, 'Done.\n\n## The Boildown\n\n- a\n- b\n', reqs)
                      == fake, None))
        prc._record_given_up('**Branch disposition:** `2026-10-19-old-x` -- drop (superseded)',
                             root=str(repo))
        cases.append(('a branch given up by name stays given up after that reply',
                      prc.given_up_branches(str(repo)) == {'2026-10-19-old-x'},
                      prc.given_up_branches(str(repo))))
        bare = [{'require_no_bare_pattern': [
            {'pattern': r'`[\w.-]+\.md`', 'advisory': True},
            {'pattern': r'\bPR #\d+\b'}]}]
        v = prc.violations('See `README.md` and PR #4.', bare)
        cases.append(('one pattern can be advice while the other still blocks',
                      sorted(b['advisory'] for b in v) == [False, True], v))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the reply gate trims for standing sessions and one-line forms '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def check_archive_gate_keeps_inner_workings_from_non_owners():
    """When the container holds files found nowhere else, the reply gate
    tells a session working for a person who is not a code owner to settle
    them itself and say nothing about them; a code owner still gets the
    named files and the disposition line.

    WHY. Morgan, 2026-10-12 (strength: decided): "Anything on the inner
    works of how BP works including things like file management, dealing
    with temporary files, dealing with temporary repos etc -- should only be
    for codeowners" (practice: inner-workings-for-code-owners). Planted: the
    same unsafe container, read once as an owner and once as not; then the
    setup warning, a refusal, Update Vendors' report and the Files touched
    rule, each of which spoke to everyone."""
    import contextlib, inspect, io
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_gate as pg
    import precedent_reply_check as prc
    cases = []
    saved = (pg._container_report, pg._is_code_owner, pg._note_from_tool,
             prc._own_branches)
    report = ('CONTAINER NOT SAFE TO LOSE -- 1 of 2 checkout(s) hold work that '
              'is only here:\n  scratch:abc -- 1 file(s) in a scratch folder')

    def gate(owner):
        pg._container_report = lambda: report
        pg._is_code_owner = lambda _root: owner
        # Neither of these writes a word this test reads, and together they
        # were about 6 of each call's 6.5 s (2026-10-31): a set's own note
        # tool, run as a subprocess, and the scan of this session's real
        # branches on origin for the Boildown's one-line form. Stubbed, the
        # asserted text is the same and no longer depends on which branches
        # the session running the harness happens to have pushed.
        pg._note_from_tool = lambda _root, _spec: []
        prc._own_branches = lambda root=None, siblings=True: []
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pg._print_hard_requirements(ROOT)
        return buf.getvalue()
    try:
        out = gate(False)
        cases.append(('not a code owner: settle it and say nothing about it',
                      'SAY NOTHING ABOUT IT' in out
                      and 'never write a disposition line' in out, failure_detail(out, 1500)))
        cases.append(('...and the disposition line is never offered',
                      '**Checkout disposition:** <name>' not in out, failure_detail(out, 1500)))
        cases.append(('...and every turn opens with the plain-words instruction, '
                      'which names each technical kind of message',
                      "NOT one of this repository's code owners" in out
                      and all(k in out for k in ('Files touched', 'branch names',
                                                 'session-setup warnings',
                                                 'Paste into', 'Update Vendors',
                                                 'reason a reply was refused')),
                      out[:1500]))
        out = gate(True)
        cases.append(('CONTROL: a code owner still gets the files and the '
                      'disposition line', 'SAY NOTHING ABOUT IT' not in out
                      and '**Checkout disposition:** <name>' in out, failure_detail(out, 1500)))
        cases.append(('...and no plain-words instruction',
                      "NOT one of this repository's code owners" not in out, ''))
    finally:
        (pg._container_report, pg._is_code_owner, pg._note_from_tool,
         prc._own_branches) = saved
    # 2026-10-12, Morgan: "Nothing technical should ever be said to a non
    # technical person." The other places that speak through a session.
    import precedent_session_check as psc
    import precedent_update as pu
    saved_fg = psc.failing_guarantees
    try:
        psc.failing_guarantees = lambda **_k: [('a guarantee', 'its detail. More.')]
        line = psc.summary('precedent gate') if hasattr(psc, 'summary') else ''
    finally:
        psc.failing_guarantees = saved_fg
    src = inspect.getsource(psc)
    cases.append(('the setup warning says it is never relayed to a non-owner',
                  'hears nothing of it' in src, failure_detail(line, 300)))
    rc_src = (ROOT / 'tools' / 'precedent_reply_check.py').read_text(encoding='utf-8')
    cases.append(('a refusal says to correct without naming the check to a non-owner',
                  'without naming this check' in rc_src, ''))
    rep = pu.Report()
    rep.pin_repo = ROOT
    saved_owner = pu._person_is_code_owner
    try:
        pu._person_is_code_owner = lambda _r: False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                rep.close()
            except Exception:                                   # noqa: BLE001
                pass
        cases.append(('Update Vendors\' report, for a non-owner, opens by saying '
                      'none of it reaches them', 'FOR YOU, NOT THE PERSON'
                      in buf.getvalue(), buf.getvalue()[:600]))
        pu._person_is_code_owner = lambda _r: True
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                rep.close()
            except Exception:                                   # noqa: BLE001
                pass
        cases.append(('CONTROL: for a code owner it does not',
                      'FOR YOU, NOT THE PERSON' not in buf.getvalue(), ''))
    finally:
        pu._person_is_code_owner = saved_owner
    links = (ROOT / 'practices' / 'reply-links-files.md').read_text(encoding='utf-8')
    cases.append(('the Files touched rule is for code owners only',
                  "reply to a code owner that created" in links
                  and '**Never to anyone else.**' in links, ''))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the archive gate keeps the inner workings from a person who is not '
          f'a code owner ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_wait_loop_gate_refuses_pgrep_f():
    """wait-loop-gate.sh refuses a Bash command running `pgrep -f` or
    `pkill -f`, and nothing else (2026-10-01: a wait loop on `pgrep -f`
    matched its own shell and ran 20 minutes past the check it waited for;
    Morgan asked for a wall). Runs the real hook, both copies, on payloads."""
    cases = []
    refused = ['while pgrep -f "tools/x.py" >/dev/null; do sleep 5; done',
               'pkill -f tools/x', 'pgrep -fa x', 'echo hi; pgrep --full x',
               'sleep 1 && pkill -af y']
    allowed = ['grep -n "pgrep -f" file', 'pgrep python3', 'ls -la',
               "git commit -m 'stop using pkill -f'", 'ps -ef | grep x']
    for rel in ('.claude/hooks/wait-loop-gate.sh',
                'templates/harness/claude-code/hooks/wait-loop-gate.sh'):
        hook = ROOT / rel
        for cmd, want in [(c, True) for c in refused] + [(c, False) for c in allowed]:
            r = subprocess.run(['bash', str(hook)], input=json.dumps(
                {'tool_input': {'command': cmd}}), capture_output=True, text=True,
                timeout=30)
            denied = '"deny"' in r.stdout
            cases.append((f'{rel}: {cmd!r} {"refused" if want else "allowed"}',
                          r.returncode == 0 and denied == want, failure_detail(r.stdout, 200)))
    settings = json.loads((ROOT / 'templates' / 'harness' / 'claude-code'
                           / 'settings.json').read_text(encoding='utf-8'))
    wired = any('wait-loop-gate.sh' in h.get('command', '')
                for e in settings['hooks'].get('PreToolUse', [])
                if e.get('matcher') == 'Bash' for h in e.get('hooks', []))
    cases.append(('the template settings wire it on PreToolUse Bash', wired, ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'wait-loop-gate.sh refuses pgrep -f and pkill -f, and nothing else '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_a_replacing_rule_inherits_what_it_does_not_restate():
    """A reply rule that replaces an earlier one by id and says
    "inherits": true keeps every key it does not set, pair by pair.

    2026-10-10: the ladder set's landing rule restated universal's
    exemptions word for word, and adding one meant editing both copies. The
    set now states only its branches and the word it wants quoted; the
    exemptions come from universal's copy.
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_reply_check as prc
    finally:
        sys.path.pop(0)
    cases = []
    base = [r for r in json.loads((ROOT / 'reply_check.json').read_text(encoding='utf-8'))
            if r.get('id') == 'prompt-please-landing-authority']
    tier = {'id': 'prompt-please-landing-authority', 'inherits': True,
            'require_in_fence_paired_with': [{
                'if_matches': r"\b(?:(?:land|merg|promot|push)\w*|pull requests?|PRs?)\b"
                              r"[^\n]{0,80}?\b(?:into|onto|on|to|against)\s+[`\"']?"
                              r"(?:staging|main)\b",
                'must_also_match': r"[\"\u201c']\s*Booked\b"}]}
    settled = prc._settle(base + [tier], ROOT)
    rule = [r for r in settled if r.get('id') == 'prompt-please-landing-authority']
    pair = (rule[0].get('require_in_fence_paired_with') or [{}])[0] if rule else {}
    cases.append(('one rule results, with the tier branches and the word it wants',
                  len(rule) == 1 and '(?:staging|main)' in pair.get('if_matches', '')
                  and 'Booked' in pair.get('must_also_match', ''), str(pair)[:200]))
    cases.append(('THE DISCRIMINATING CASE: it inherits the exemptions it does not restate',
                  all(k in pair for k in ('description_exempt_if_clause_preceded_by',
                                          'quoted_output_exempt_if_preceded_by',
                                          'narration_exempt')), str(sorted(pair))))

    def fires(body):
        text = 'Paste into: x.\n```\n' + body + '\n```\n'
        return [v for v in prc.violations(text, rule) if v['kind'] == 'in_fence_paired']
    cases.append(('so a described event on staging passes under the tier rule',
                  not fires('The step fires on a pull request into staging.'), ''))
    cases.append(('and a tool message quoted as it printed it passes too',
                  not fires('After the merge, the wait still prints "Merge the pull '
                            'request into staging". Say it passed.'), ''))
    cases.append(('and an order to land on staging still needs the quoted word',
                  bool(fires('Land it on staging.')), ''))
    plain = dict(tier, inherits=False)
    alone = [r for r in prc._settle(base + [plain], ROOT)
             if r.get('id') == 'prompt-please-landing-authority']
    cases.append(('without "inherits", a replacing rule stands alone, as before',
                  'description_exempt_if_clause_preceded_by'
                  not in alone[0]['require_in_fence_paired_with'][0], ''))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a replacing rule inherits what it does not restate ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} ({d})' for n, d in bad))


def check_bestpractice_engine_hooks_are_stubs():
    """BestPractice's own .claude/hooks/reply-gate.sh, stop-git-check.sh and
    stop-reply-check.sh were hand copies of the engine scripts that had
    drifted from tools/<same>.sh -- two of them lacked the
    .precedent/python-bin PATH block -- while the dogfooded-hooks check
    called them repo-specific and left them out (2026-10-17 very deep
    check). Each is now the one engine stub, the check names it, and the
    stub still does the hook's job when Claude Code runs it: planted in a
    fixture repository with a dirty tree, the stop hook blocks the stop,
    and lets it go when Claude Code says a stop hook is already active."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    names = ('reply-gate.sh', 'stop-git-check.sh', 'stop-reply-check.sh')
    stub = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' /
            'doc-lint-gate.sh').read_bytes()
    cases = []
    for n in names:
        live = ROOT / '.claude' / 'hooks' / n
        cases.append((f'.claude/hooks/{n} is the engine stub',
                      live.is_file() and live.read_bytes() == stub, n))
        cases.append((f'the dogfooded-hooks check names {n}',
                      n in pc.DOGFOODED_HOOKS_MATCH_TEMPLATE, n))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='bp-hook-stub-'))
    try:
        repo = tmp / 'repo'
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        (repo / 'tools').mkdir()
        shutil.copy(ROOT / '.claude' / 'hooks' / 'stop-git-check.sh',
                    repo / '.claude' / 'hooks' / 'stop-git-check.sh')
        shutil.copy(ROOT / 'tools' / 'stop-git-check.sh',
                    repo / 'tools' / 'stop-git-check.sh')
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        g('add', '-A')
        g('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit',
          '-qm', 'base')
        g('remote', 'add', 'origin', str(tmp / 'none.git'))
        (repo / 'tools' / 'stop-git-check.sh').write_text(
            (repo / 'tools' / 'stop-git-check.sh').read_text() + '\n',
            encoding='utf-8')
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))

        def stop(payload):
            return subprocess.run(
                ['bash', str(repo / '.claude' / 'hooks' / 'stop-git-check.sh')],
                cwd=repo, input=payload, capture_output=True, text=True,
                env=env, timeout=60)
        r = stop('{"session_id": "h1", "stop_hook_active": false}')
        cases.append(('THE CASE: the stub runs the engine stop hook, which '
                      'blocks a stop over a dirty tree',
                      r.returncode == 2 and 'Uncommitted changes' in r.stderr,
                      f'rc={r.returncode} {r.stderr[:200]}'))
        r = stop('{"session_id": "h1", "stop_hook_active": true}')
        cases.append(('CONTROL: a stop hook already active is let through',
                      r.returncode == 0, f'rc={r.returncode} {r.stderr[:200]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + ' -- ' + str(c[2])[:300] for c in cases if not c[1]]
    check(f'BestPractice\'s reply and stop hooks are the engine stub, checked '
          f'as dogfooded, and still run ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_update_question_names_new_gates():
    """The hooks-and-settings question Update Vendors puts to the person
    names every hook the update newly wires into settings.json and what it
    refuses, and says "nothing changes about when anything is blocked" only
    when that is true.

    WHY. 2026-10-10, a consumer's Update Vendors: the last-time question
    (hooks becoming stubs) said nothing changed about blocking, while the
    same update wired artifact-publish-gate.sh, which refuses a hand-written
    page. The person's yes to that sentence is what lets the commit through.

    Negative control, measured 2026-10-10: on staging's code the gate case
    fails -- harness_ask ignored `cases` when `last` was set, and said the
    sentence anyway."""
    import inspect, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    env = _fixture_git_env()
    cases = []
    stub = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' /
            'push-check-gate.sh').read_text(encoding='utf-8')
    hook = lambda n: f'"$CLAUDE_PROJECT_DIR"/.claude/hooks/{n}'
    def settings(entries):
        d = {}
        for ev, m, c in entries:
            d.setdefault(ev, []).append(dict({'hooks': [{'type': 'command',
                                                         'command': c}]},
                                             **({'matcher': m} if m else {})))
        return json.dumps({'hooks': d}, indent=2) + '\n'
    base = [('PreToolUse', 'Bash', hook('push-check-gate.sh'))]
    dispatch = [(ev, None, hook('precedent-hooks.sh') + f' {ev}')
                for ev in ('PreToolUse', 'Stop')]
    gate = [('PreToolUse', 'Artifact', hook('artifact-publish-gate.sh'))]
    rewrite = [('PreToolUse', 'Bash', 'bash .claude/hooks/push-check-gate.sh')]

    def ask(after, migrate=True):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                          capture_output=True, text=True)
            g('init', '-q', '-b', 'main')
            (repo / '.claude' / 'hooks').mkdir(parents=True)
            (repo / '.claude' / 'hooks' / 'push-check-gate.sh').write_text(
                '#!/bin/bash\n# the real hook, before stubs\nexit 0\n', encoding='utf-8')
            (repo / '.claude' / 'settings.json').write_text(settings(base),
                                                            encoding='utf-8')
            g('add', '-A'); g('commit', '-qm', 'before')
            if migrate:
                (repo / '.claude' / 'hooks' / 'push-check-gate.sh').write_text(
                    stub, encoding='utf-8')
            (repo / 'tools').mkdir()
            for script in ('artifact-publish-gate.sh', 'wait-loop-gate.sh'):
                shutil.copy(ROOT / 'tools' / script, repo / 'tools' / script)
            (repo / '.claude' / 'settings.json').write_text(
                after if isinstance(after, str) else settings(after),
                encoding='utf-8')
            g('add', '-A')
            paths = pu.harness_changes(repo)
            # Older code had neither; read so, it fails a stated case below
            # rather than crashing (the negative control).
            gates = getattr(pu, 'harness_new_gates', lambda r, p: [])(repo, paths)
            more = ({'gates': gates} if 'gates' in
                    inspect.signature(pu.harness_ask).parameters else {})
            return gates, pu.harness_ask(
                paths, last=pu.migrates_to_stubs(repo, paths),
                cases=pu.harness_cases(repo, paths), **more)

    quiet = 'Nothing changes about when anything is blocked'
    gates, said = ask(base + dispatch)
    cases.append(('CONTROL: the move to stubs with only the per-event '
                  'entries says nothing new is blocked', gates == [] and quiet in said,
                  said))
    gates, said = ask(base + dispatch + gate)
    cases.append(('the move to stubs that also wires a gate names it and what '
                  'it refuses, and never says nothing new is blocked',
                  [n for n, _e, _w in gates] == ['artifact-publish-gate.sh']
                  and 'artifact-publish-gate.sh (PreToolUse)' in said
                  and 'REFUSES to publish' in said and quiet not in said, said))
    gates, said = ask(rewrite + dispatch)
    cases.append(("a hook's path rewritten is not a new gate", gates == [], gates))
    gates, said = ask(base + gate, migrate=False)
    cases.append(('an ordinary update that wires a gate names what it refuses '
                  'too', 'REFUSES to publish' in said and quiet not in said, said))
    # THE SHAPE OF 2026-10-10 (a consumer's Update Vendors at 78d970b): the
    # move to stubs, the per-event dispatch entries, and TWO gates wired for
    # the first time on different matchers -- wait-loop-gate.sh on Bash,
    # where a hook already ran, and artifact-publish-gate.sh on Artifact.
    wait = [('PreToolUse', 'Bash', hook('wait-loop-gate.sh'))]
    both = sorted(['artifact-publish-gate.sh', 'wait-loop-gate.sh'])
    gates, said = ask(base + dispatch + gate + wait)
    cases.append(('the move to stubs wiring two gates on different matchers '
                  'names both, never the dispatch entry, and never says nothing '
                  'new is blocked',
                  sorted(n for n, _e, _w in gates) == both
                  and 'wait-loop-gate.sh (PreToolUse)' in said
                  and 'artifact-publish-gate.sh (PreToolUse)' in said
                  and 'precedent-hooks.sh' not in said and quiet not in said
                  and 'one last time' in said, said))
    shared = json.loads(settings(base + dispatch + gate))
    for block in shared['hooks']['PreToolUse']:
        if block.get('matcher') == 'Bash':
            block['hooks'].append({'type': 'command',
                                   'command': hook('wait-loop-gate.sh')})
    gates, said = ask(json.dumps(shared, indent=2) + '\n')
    cases.append(("...and the same when the Bash gate joins the Bash block "
                  "already there", sorted(n for n, _e, _w in gates) == both
                  and quiet not in said, said))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the hooks question names each newly wired gate and what it '
          f'refuses ({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_publish_gate_passes_the_branch_cleanup_page():
    """The page tools/precedent_stale_branches.py --db-page writes is published
    past the Artifact publish gate; a hand-made page still is not.

    WHY. 2026-10-07, a consuming repository: the stop hook asked for the
    branch-cleanup page (the ladder set's stale-branch-cleanup), and
    tools/artifact_publish_gate.py refused it as "not a render of any
    registered document" -- two rules in force contradicting each other.
    Planted: the gate's own two-direction --self-check; the generator's
    --db-page run notes its page, which the gate then passes; the same page
    with one byte changed is refused."""
    import tempfile
    cases = []
    r = subprocess.run([sys.executable, 'tools/artifact_publish_gate.py', '--self-check'],
                       capture_output=True, text=True, cwd=str(ROOT))
    cases.append(('the gate\'s own self-check passes',
                  r.returncode == 0 and 'self-check OK' in r.stdout))
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_stale_branches as _sb
    import artifact_publish_gate as _apg
    saved = os.environ.get('PRECEDENT_GENERATED_PAGES')
    real_collect, real_person = _sb.collect, _sb._person
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        os.environ['PRECEDENT_GENERATED_PAGES'] = str(td / 'ledger.json')
        try:
            _sb.collect = lambda fetch=False, seen=None: (
                [('o', 'r', [('old-branch', '2026-10-01')])], [])
            # No saved page (practice: fixture-owns-its-state).
            _sb._person = lambda: {}
            page = td / 'branch-cleanup.html'
            with open(os.devnull, 'w') as quiet:
                saved_out, sys.stdout = sys.stdout, quiet
                try:
                    _sb.main(['--db-page', str(page)])
                finally:
                    sys.stdout = saved_out
            cases.append(('the generator\'s page passes the gate',
                          page.is_file() and not _apg.check([str(page)], [], td)))
            page.write_text(page.read_text(encoding='utf-8') + ' ', encoding='utf-8')
            cases.append(('the same page edited by hand is refused',
                          bool(_apg.check([str(page)], [], td))))
        finally:
            _sb.collect, _sb._person = real_collect, real_person
            if saved is None:
                os.environ.pop('PRECEDENT_GENERATED_PAGES', None)
            else:
                os.environ['PRECEDENT_GENERATED_PAGES'] = saved
    bad = [n for n, ok in cases if not ok]
    check(f'the publish gate passes the branch-cleanup page ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_landed_reduction_quiets_the_reduction_ask():
    """An over-target file whose reduction has already landed on the landing
    branch is reported as waiting on a Promote, not as needing another pass.

    Found 2026-10-01 in a reduction-pass session: the reply gate kept
    requiring a Reduction pass after the pass had landed on the tier below main,
    because the file it measures is built from main. The rule under test:
    AGENTS.md smaller on origin/staging than on origin/main marks the
    over-target line; the same size, or no landing branch, leaves it as
    the plain ask. Driven against a throwaway repository."""
    import tempfile
    import precedent_gate as pg
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = _stale_ref_fixture_env(tmp)
        bare, work = tmp / 'origin.git', tmp / 'work'

        def git(*a, cwd=None):
            return subprocess.run(['git', '-C', str(cwd or work), *a],
                                  capture_output=True, text=True, env=env)
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)],
                       capture_output=True, env=env)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(work)],
                       capture_output=True, env=env)
        (work / 'tools').mkdir()
        (work / 'tools' / 'session_load_budgets.json').write_text(json.dumps(
            {'surfaces': {'AGENTS.md': {'target': 50}}}), encoding='utf-8')
        (work / 'AGENTS.md').write_text('# A\n' + 'word ' * 400, encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'big')
        git('remote', 'add', 'origin', f'file://{bare}')
        git('push', '-q', 'origin', 'HEAD:main', 'HEAD:staging')
        git('fetch', '-q', 'origin')

        got = pg._over_target(work, siblings=False)
        cases.append(('over target, same size on staging: the plain ask',
                      len(got) == 1 and pg.LANDED_REDUCTION_MARK not in got[0],
                      repr(got)))
        git('checkout', '-q', '-b', 'staging', 'origin/staging')
        (work / 'AGENTS.md').write_text('# A\n' + 'word ' * 200, encoding='utf-8')
        git('commit', '-qam', 'reduction pass')
        git('push', '-q', 'origin', 'staging')
        git('fetch', '-q', 'origin')
        git('checkout', '-q', 'main')
        got = pg._over_target(work, siblings=False)
        cases.append(('a smaller AGENTS.md on staging marks the line as '
                      'waiting on a Promote, with both sizes',
                      len(got) == 1 and pg.LANDED_REDUCTION_MARK in got[0]
                      and 'on main' in got[0] and 'on staging' in got[0],
                      repr(got)))
        # Off the ladder: the same fact, with no tier and no ladder word
        # (found 2026-10-03, the line named the landing tier to such a person).
        saved = {k: os.environ.pop(k, None) for k in
                 ('PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG')}
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')
        try:
            got = pg._over_target(work, siblings=False)
        finally:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
            os.environ.update({k: v for k, v in saved.items() if v is not None})
        cases.append(('off the ladder, the same line says it plainly, with no '
                      'ladder word',
                      len(got) == 1 and pg.LANDED_REDUCTION_MARK_PLAIN in got[0]
                      and 'on main' in got[0]
                      and not _owned_word_hits(got[0]), repr(got)))
        git('push', '-q', 'origin', '--delete', 'staging')
        git('fetch', '-q', '--prune', 'origin')
        cases.append(('no landing branch on origin: no mark',
                      pg._landed_reduction(work) is None,
                      repr(pg._landed_reduction(work))))
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a reduction already on the landing branch is reported as waiting '
          f'on a Promote ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_stop_hook_says_each_state_once():
    """The Stop hook blocks once per dirty state, not at every turn end.

    Found 2026-10-01 in a reduction-pass session: while a background helper
    of the session was mid-edit on its branch, the same "uncommitted
    changes" finding blocked every stop, and each block was a turn with
    nothing to do. The rule under test: the first stop on a dirty state is
    blocked and says why; the same session stopping on the same state is
    not blocked again; a change to the state, or another session, is told
    afresh. Both copies are run, the template and this repo's own."""
    import tempfile
    name = 'the Stop hook says each dirty state once per session'
    hooks = [ROOT / 'tools' / 'stop-git-check.sh',
             ROOT / '.claude' / 'hooks' / 'stop-git-check.sh']
    hooks = [h for h in hooks if h.exists()]
    if not hooks:
        not_applicable(name, 'no stop-git-check.sh here')
        return
    cases = []
    for hook in hooks:
        label = hook.relative_to(ROOT).parts[0]
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            env = _stale_ref_fixture_env(tmp)

            def git(*a):
                return subprocess.run(['git', '-C', str(work), *a],
                                      capture_output=True, text=True, env=env)
            bare = tmp / 'origin.git'
            subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(bare)],
                           capture_output=True, env=env)
            work = tmp / 'work'
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(work)],
                           capture_output=True, env=env)
            (work / 'a.txt').write_text('a\n', encoding='utf-8')
            git('add', 'a.txt')
            git('commit', '-q', '-m', 'a')
            git('remote', 'add', 'origin', f'file://{bare}')
            git('push', '-q', '-u', 'origin', 'main')

            def stop(session):
                return subprocess.run(['bash', str(hook)], cwd=str(work),
                                      input=json.dumps({'session_id': session}),
                                      capture_output=True, text=True, env=env)

            (work / 'a.txt').write_text('a, edited\n', encoding='utf-8')
            r = stop('s1')
            cases.append((f'{label}: the first stop on a dirty tree is blocked, '
                          f'and says it will not repeat',
                          r.returncode == 2 and 'Uncommitted' in r.stderr
                          and 'will not repeat' in r.stderr))
            r = stop('s1')
            cases.append((f'{label}: the same session, same state: not blocked again',
                          r.returncode == 0))
            (work / 'b.txt').write_text('b\n', encoding='utf-8')
            r = stop('s1')
            cases.append((f'{label}: a new untracked file is a new state: blocked',
                          r.returncode == 2 and 'Untracked' in r.stderr))
            r = stop('s2')
            cases.append((f'{label}: another session is told afresh',
                          r.returncode == 2))
            git('add', '-A')
            git('commit', '-q', '-m', 'both')
            git('push', '-q')
            r = stop('s2')
            cases.append((f'{label}: clean and pushed: not blocked',
                          r.returncode == 0))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_stop_hook_ignores_commits_another_remote_ref_has():
    """The Stop hook's "unpushed" count asks whether a commit is on ANY
    remote ref, not whether it is ahead of origin/<current branch>.

    Two false blocks reported from a consumer repo, 2026-09-28, with
    nothing actually unpushed. (a) The branch's remote copy was deleted
    after its pull request merged; the stale remote-tracking ref stayed,
    and once the branch was moved onto origin/main the hook counted seven
    commits that were all on origin/main. (b) The branch was reset onto
    origin/staging, whose tip is the merge of that same branch's pull
    request; the hook counted one commit that was on origin/staging.
    Neither is the empty-merge case check_empty_commits_are_never_counted
    covers: both carry real file changes, just not unpushed ones.

    Both copies are run -- the template consumers install and this repo's
    own dogfooded one -- since the two carry different headers and a fix
    landed in only one of them before."""
    import tempfile
    name = ('the Stop hook counts only commits no remote ref has, so a stale '
            'or deleted branch ref never blocks a stop')
    hooks = [ROOT / 'tools' / 'stop-git-check.sh',
             ROOT / '.claude' / 'hooks' / 'stop-git-check.sh']
    hooks = [h for h in hooks if h.exists()]
    if not hooks:
        not_applicable(name, 'no stop-git-check.sh here')
        return
    cases = []
    for hook in hooks:
        label = hook.relative_to(ROOT).parts[0]
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            env = _stale_ref_fixture_env(tmp)

            def git(cwd, *a):
                return subprocess.run(['git', '-C', str(cwd), *a],
                                      capture_output=True, text=True, env=env)

            def write(repo, path, text):
                (repo / path).write_text(text, encoding='utf-8')
                git(repo, 'add', path)
                git(repo, 'commit', '-q', '-m', f'edit {path}')

            bare = tmp / 'origin.git'
            git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
            work = tmp / 'work'
            git(tmp, 'init', '-q', '-b', 'main', str(work))
            write(work, 'a.txt', 'a\n')
            git(work, 'remote', 'add', 'origin', f'file://{bare}')
            git(work, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
            git(work, 'push', '-q', 'origin', 'HEAD:refs/heads/staging')
            # A second clone stands in for GitHub: it merges pull requests
            # and deletes branches without this checkout hearing about it.
            other = tmp / 'other'
            git(tmp, 'clone', '-q', f'file://{bare}', str(other))

            def stop():
                return subprocess.run(['bash', str(hook)], cwd=str(work),
                                      input='{}', capture_output=True,
                                      text=True, env=env)

            # (a) feature is pushed, merged into main alongside other work,
            # and its remote copy deleted; origin/feature stays, stale.
            git(work, 'checkout', '-q', '-b', 'feature')
            write(work, 'f.txt', 'f\n')
            git(work, 'push', '-q', '-u', 'origin', 'feature')
            git(other, 'fetch', '-q', 'origin')
            git(other, 'checkout', '-q', 'main')
            write(other, 'x.txt', 'x\n')
            write(other, 'y.txt', 'y\n')
            git(other, 'merge', '-q', '--no-ff', '-m', 'merge feature',
                'origin/feature')
            git(other, 'push', '-q', 'origin', 'main')
            git(other, 'push', '-q', 'origin', '--delete', 'feature')
            git(work, 'fetch', '-q', 'origin')          # no --prune: stale ref
            git(work, 'reset', '-q', '--hard', 'origin/main')
            stale = bool(git(work, 'rev-parse', '-q', '--verify',
                             'refs/remotes/origin/feature').stdout.strip())
            r = stop()
            cases.append((f'{label}: (a) branch moved onto origin/main after '
                          f'its remote copy was deleted, stale ref kept: the '
                          f'stop is not blocked [{r.returncode}: '
                          f'{r.stderr.strip()[:160]}]',
                          stale and r.returncode == 0))

            # (b) feature2 is pushed and merged into staging; the local
            # branch is reset onto origin/staging, whose tip is that merge.
            git(work, 'checkout', '-q', '-B', 'feature2', 'origin/staging')
            write(work, 'g.txt', 'g\n')
            git(work, 'push', '-q', '-u', 'origin', 'feature2')
            git(other, 'fetch', '-q', 'origin')
            git(other, 'checkout', '-q', '-B', 'staging', 'origin/staging')
            write(other, 'z.txt', 'z\n')
            git(other, 'merge', '-q', '--no-ff', '-m', 'merge feature2',
                'origin/feature2')
            git(other, 'push', '-q', 'origin', 'staging')
            git(work, 'fetch', '-q', 'origin')
            git(work, 'reset', '-q', '--hard', 'origin/staging')
            r = stop()
            cases.append((f'{label}: (b) branch reset onto origin/staging, '
                          f'whose tip merges that branch: the stop is not '
                          f'blocked [{r.returncode}: {r.stderr.strip()[:160]}]',
                          r.returncode == 0))

            # Control: a real commit no remote has still blocks, counted once.
            write(work, 'h.txt', 'h\n')
            r = stop()
            cases.append((f'{label}: a real commit no remote has still blocks, '
                          f'and says 1 [{r.returncode}: '
                          f'{r.stderr.strip()[:160]}]', r.returncode == 2
                          and '1 unpushed commit(s)' in r.stderr))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


@_without_session_id
def check_reply_gate_refreshes_the_landing_branch():
    """The reply gate's NOT YET LANDED line reads origin/<landing branch>
    fresh, not as last fetched.

    Reported 2026-09-28: a session merged its pull request through the
    GitHub API -- how every cloud session merges -- so nothing in the
    checkout fetched, origin/<landing tier> stayed at the pre-merge tip,
    and for two turns the gate said the branch's commit was NOT on it and
    demanded the Boildown recommend merging a pull request already merged.
    Only a `git fetch` of that branch cleared it.

    A second clone stands in for GitHub here. Offline, the gate keeps its
    old answer from the ref it has, and never raises."""
    import tempfile
    import precedent_gate as pg
    name = ('the reply gate refreshes the landing branch before reporting '
            'work NOT on it')
    cases = []
    saved = {k: os.environ.get(k) for k in
             ('PRECEDENT_USER_CONFIG', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM')}
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = _stale_ref_fixture_env(tmp)
        # _unlanded_work runs in this process, so it sees this process's
        # environment: no personal landing branch, no machine git config.
        for k in saved:
            os.environ[k] = env[k]
        try:
            def git(cwd, *a):
                return subprocess.run(['git', '-C', str(cwd), *a],
                                      capture_output=True, text=True, env=env)

            def write(repo, path, text):
                (repo / path).write_text(text, encoding='utf-8')
                git(repo, 'add', path)
                git(repo, 'commit', '-q', '-m', f'edit {path}')

            bare = tmp / 'origin.git'
            git(tmp, 'init', '-q', '--bare', '-b', 'trunk', str(bare))
            repo = tmp / 'repo'
            git(tmp, 'init', '-q', '-b', 'trunk', str(repo))
            write(repo, 'precedent.json',
                  json.dumps({'base_branch': 'trunk', 'sources': []}))
            git(repo, 'remote', 'add', 'origin', f'file://{bare}')
            git(repo, 'push', '-q', '-u', 'origin', 'trunk')
            git(repo, 'checkout', '-q', '-b', 'feature')
            write(repo, 'b.txt', 'b\n')
            git(repo, 'push', '-q', '-u', 'origin', 'feature')
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(('before the merge, the commit is reported',
                          len(got) == 1, str(got)))

            other = tmp / 'other'
            git(tmp, 'clone', '-q', f'file://{bare}', str(other))
            git(other, 'merge', '-q', '--no-ff', '-m', 'merge feature',
                'origin/feature')
            git(other, 'push', '-q', 'origin', 'trunk')
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(('merged on the remote with nothing fetched here: '
                          'not reported', got == [], str(got)))

            write(repo, 'c.txt', 'c\n')
            git(repo, 'remote', 'set-url', 'origin', str(tmp / 'gone.git'))
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(('offline, a real unlanded commit is still reported '
                          'from the ref it has', len(got) == 1, str(got)))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    failed = [f'{n} [{d}]' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_reply_gate_counts_staging_as_a_landing_branch():
    """In a repo whose landing branch is staging, work merged into staging
    has landed: the reply gate prints no NOT YET LANDED line for it, and
    says instead that staging is ahead of main.

    THE INCIDENT (2026-10-10, a consumer). Its second Update Vendors set
    landing_branch to staging. A branch merged into
    staging still read "NOT YET LANDED ... NOT on 'main'", and the reply
    check, reading the same lines, refused "You can archive this session"
    for work already landed; the gentle "a Promote can move them" line was
    computed only for the tier it had used before. The DISCRIMINATING CASE is the second;
    the first is the control that the branch is still reported before its
    merge. The fixture owns its repositories and its session id."""
    import tempfile
    import precedent_gate as pg
    name = 'the reply gate counts staging as a landing branch'
    cases = []
    saved = {k: os.environ.get(k) for k in
             ('PRECEDENT_USER_CONFIG', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM')}
    saved_sid = pg._this_session_id
    import precedent_resolve as _pr
    saved_ladder = os.environ.get(_pr.ASSUME_LADDER_ENV)
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = _stale_ref_fixture_env(tmp)
        for k in saved:
            os.environ[k] = env[k]
        # On the ladder, as the person in the incident was: off it, work
        # lands on main by design and staging is not a landing branch.
        os.environ[_pr.ASSUME_LADDER_ENV] = '1'
        pg._this_session_id = lambda: ''       # every commit here is "ours"
        try:
            def git(cwd, *a):
                return subprocess.run(['git', '-C', str(cwd), *a],
                                      capture_output=True, text=True, env=env)

            def write(repo, path, text):
                (repo / path).write_text(text, encoding='utf-8')
                git(repo, 'add', path)
                git(repo, 'commit', '-q', '-m', f'edit {path}')

            bare = tmp / 'origin.git'
            git(tmp, 'init', '-q', '--bare', '-b', 'main', str(bare))
            repo = tmp / 'repo'
            git(tmp, 'init', '-q', '-b', 'main', str(repo))
            write(repo, 'precedent.json', json.dumps(
                {'base_branch': 'main', 'landing_branch': 'staging',
                 'staging_branch': 'staging', 'sources': []}))
            git(repo, 'remote', 'add', 'origin', f'file://{bare}')
            git(repo, 'push', '-q', '-u', 'origin', 'main')
            git(repo, 'push', '-q', 'origin', 'main:staging')
            git(repo, 'fetch', '-q', 'origin')
            git(repo, 'checkout', '-q', '-b', 'feature')
            write(repo, 'b.txt', 'b\n')
            git(repo, 'push', '-q', '-u', 'origin', 'feature')
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(("CONTROL: before the merge, the branch is reported as "
                          "not on staging",
                          any("'staging'" in l and 'feature' in l for l in got),
                          str(got)))

            other = tmp / 'other'
            git(tmp, 'clone', '-q', '-b', 'staging', f'file://{bare}', str(other))
            git(other, 'merge', '-q', '--no-ff', '-m', 'merge feature',
                'origin/feature')
            git(other, 'push', '-q', 'origin', 'staging')
            git(repo, 'fetch', '-q', 'origin')
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(('THE DISCRIMINATING CASE: merged into staging, the '
                          'branch is not reported as unlanded',
                          not any('feature' in l for l in got), str(got)))
            cases.append(("...and the gate says staging is ahead of 'main'",
                          any("staging is 1 commit(s) ahead of 'main'" in l
                              for l in got), str(got)))
            # Off the ladder there are no tiers: work lands on main, whatever
            # precedent.json's landing_branch says (Morgan, 2026-10-10:
            # "staging is the landing branch ONLY if people use the ladders
            # repo, for the normal repo, it should be main").
            os.environ.pop(_pr.ASSUME_LADDER_ENV, None)
            got = pg._unlanded_work(repo, siblings=False)
            cases.append(("OFF THE LADDER: merged into staging is still not "
                          "landed -- the branch is reported against 'main'",
                          any("'main'" in l and 'feature' in l for l in got)
                          and not any('ahead of' in l for l in got), str(got)))
        finally:
            pg._this_session_id = saved_sid
            if saved_ladder is None:
                os.environ.pop(_pr.ASSUME_LADDER_ENV, None)
            else:
                os.environ[_pr.ASSUME_LADDER_ENV] = saved_ladder
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    failed = [f'{n} [{d}]' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_parallels_table_holds_a_shipped_hook_this_repo_does_not_run():
    """templates/harness/PARALLELS.md must carry a row for every hook the
    claude-code adapter ships, run here or not -- and may: a row for one is
    never refused as naming a hook that does not exist.

    2026-10-17, very deep check: artifact-publish-gate.sh and
    precedent-universal-catalogue.sh ship to consumers and sets, BestPractice
    runs neither, so they had no row, and claude-only-surface-has-a-parallel
    refused adding one. Decision (the session's, under Morgan's delegation
    of 2026-10-17): the check reads templates/harness/claude-code/hooks/ as
    part of its list of mechanisms. Planted: a hook run here and a hook only
    shipped, with and without a row each; and this repository's own table."""
    import tempfile, types
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-parallels-'))
    cases = []
    try:
        (tmp / '.claude' / 'hooks').mkdir(parents=True)
        (tmp / '.claude' / 'hooks' / 'run-here.sh').write_text('#!/bin/bash\n')
        shipped = tmp / 'templates' / 'harness' / 'claude-code' / 'hooks'
        shipped.mkdir(parents=True)
        for n in ('run-here.sh', 'only-shipped.sh'):
            (shipped / n).write_text('#!/bin/bash\n')
        head = '| Mechanism | What it does | codex | gemini-cli | grok-build |\n|---|---|---|---|---|\n'
        row = lambda n: f'| `{n}` | does a thing | none, why | none, why | none, why |\n'
        table = tmp / 'templates' / 'harness' / 'PARALLELS.md'
        ctx = types.SimpleNamespace(root=tmp)

        def run(text):
            table.write_text('# Parallels\n\n' + text, encoding='utf-8')
            return [f.detail for f in pc._claude_only_surface_has_a_parallel(ctx)]
        got = run(head + row('run-here.sh') + row('only-shipped.sh'))
        cases.append(('a row for a hook only shipped is accepted', not got, str(got)))
        got = run(head + row('run-here.sh'))
        cases.append(('...and required', any('only-shipped.sh' in m for m in got), str(got)))
        got = run(head + row('run-here.sh') + row('only-shipped.sh') + row('long-gone.sh'))
        cases.append(('a row for a hook neither run nor shipped is still a finding',
                      any('long-gone.sh' in m for m in got), str(got)))
        real = ROOT / 'templates' / 'harness' / 'PARALLELS.md'
        text = real.read_text(encoding='utf-8')
        missing = [n for n in ('artifact-publish-gate.sh', 'precedent-universal-catalogue.sh')
                   if f'| `{n}` |' not in text]
        cases.append(('this repository\'s table carries both shipped-only hooks',
                      not missing, str(missing)))
        cases.append(('...and says only Claude Code\'s wiring is refreshed for you',
                      'Only Claude Code\'s wiring is written and kept current' in text, ''))
    except OSError as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the parallels table holds a hook BestPractice ships but does not run '
          f'({len(cases)} stated cases)', not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def _owned_word_hits(text, owners=None):
    """-> hits in printed `text` of the words every set on this machine
    declares as its own (tools/set_words.py), each run as that set's
    output patterns; [] where no such set is cloned here."""
    import set_words as sw
    owners = sw.sets_with_words(ROOT) if owners is None else owners
    return [h for _n, _p, words, _prov in owners
            for h in sw.output_hits(text, words)]


def check_ladder_off_engine_says_no_ladder_words():
    """spec/LADDER_OPT_IN_PLAN.md assertion B, on the engine's own output: a
    person with no practice set of their own -- the ladder not in force --
    runs the tools a session runs, in this repository, and none of them
    prints a word some set declares as its own (tools/set_words.py; the
    words are each set's, read from the sets cloned on this machine).
    Measured 2026-10-02 before the change: about 450 such words across
    these outputs.

    `PRECEDENT_ASSUME_LADDER` (the harness default) is cleared for every run
    here: this is the off-ladder world, as a person off the ladder meets it.
    One phrase is excused by name, the ordinary English "staging document"."""
    import set_words as sw
    import tempfile
    owners = sw.sets_with_words(ROOT)
    if not owners:
        not_applicable('off the ladder, the engine prints no set\'s own words',
                       'no set that declares words of its own is cloned on this '
                       'machine, so there is nothing to hold the output to')
        return
    env = {k: v for k, v in os.environ.items()
           if k not in ('PRECEDENT_ASSUME_LADDER', 'PRECEDENT_NO_LADDERS')}
    env['PRECEDENT_USER_CONFIG'] = str(pathlib.Path(tempfile.gettempdir())
                                       / 'no-such-precedent-config.json')
    runs = [
        ('the reply gate', ['tools/precedent_gate.py', 'reply']),
        ('the merge gate', ['tools/precedent_gate.py', 'merge']),
        ('the push gate', ['tools/precedent_gate.py', 'push']),
        ('the review gate', ['tools/precedent_gate.py', 'review']),
        ('the reply check\'s requirements', ['tools/precedent_reply_check.py', '--explain']),
        ('Vocabulary', ['tools/precedent_vocabulary.py']),
        ('the landing branch', ['tools/precedent_branches.py', '--landing']),
        ('the branch status', ['tools/precedent_branches.py']),
        ('the deep check\'s listing', ['tools/precedent_push_check.py', '--list']),
        ('the ladder helper', ['tools/precedent_ladder.py', '--status']),
    ]
    excused = sw.EXCUSED_IN_OUTPUT
    cases = []
    for what, argv in runs:
        r = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=600)
        text = r.stdout + r.stderr
        # A quoted commit ("  aeadfef4 <title>") is the repository's own
        # history, written by people, not the engine's wording: a person off
        # the ladder meets the same titles in `git log`. Found 2026-10-03:
        # inside a Debut the checked copy sits on the Debut's own merge
        # commit, titled as a Promote, and the reply
        # gate lists it as unlanded work. So is a command still running in
        # the session ("  pid N, running MM:SS: <command>",
        # precedent_container_safe): the person's own words, quoted. Found
        # 2026-10-04: a set's Debut, running beside this check, failed it.
        lines = [l for l in text.splitlines()
                 if not any(x in l for x in excused)
                 and not re.match(r'\s+[0-9a-f]{7,40} \S', l)
                 and not re.match(r'\s+pid \d+, running [\d:-]+: ', l)]
        found = _owned_word_hits('\n'.join(lines), owners)
        # The lines themselves, not only the words: a hit that appeared only
        # inside a Debut (2026-10-03) could not be found from the words.
        said = [lines[n - 1][:300] for n in sorted({h[0] for h in found})][:3]
        cases.append((f'{what} says no ladder word to a person off the ladder',
                      not found, f'{found[:6]!r} in {said!r}'))
    r = subprocess.run([sys.executable, 'tools/precedent_branches.py', '--landing'],
                       cwd=str(ROOT), env=env, capture_output=True, text=True)
    cases.append(('their work lands on main',
                  r.stdout.splitlines()[:1] == ['main'], r.stdout[:200]))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'off the ladder, the engine prints none of the ladder\'s words '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))

@_without_session_id
def check_reply_gate_reports_only_this_sessions_flow():
    """The reply gate's unlanded and Promote lines name only the branch or
    flow this session worked on -- commits carrying its session trailer --
    in this checkout and in a sibling clone alike (Morgan, 2026-09-29,
    strength: decided: "only tell me about that promotions that I need to
    do *ONLY* regarding the branch/flow that I edited/worked on in that
    session window"). With no session id to match, this checkout keeps its
    line and a sibling gets none."""
    name = 'reply gate reports only this session\'s own flow'
    import precedent_gate as pg
    import tempfile

    cases = []
    sid_env = 'cse_01FixtureOwnSession'
    trailer = 'Claude-Session: https://claude.ai/code/session_01FixtureOwnSession'
    saved = {k: os.environ.get(k) for k in ('HOME', 'PRECEDENT_USER_CONFIG')}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-own-flow-'))
    try:
        (tmp / 'home').mkdir()
        os.environ['HOME'] = str(tmp / 'home')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-config.json')

        def make(dirname):
            up = tmp / f'{dirname}.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(up)], check=True)
            repo = tmp / 'root' / dirname
            subprocess.run(['git', 'init', '-q', '-b', 'trunk', str(repo)], check=True)

            def g(*a):
                return subprocess.run(['git', '-C', str(repo), *a],
                                      capture_output=True, text=True)
            g('config', 'user.name', 'Harness Fixture')
            g('config', 'user.email', 'fixture' + chr(64) + 'example.invalid')
            g('config', 'commit.gpgsign', 'false')
            (repo / 'precedent.json').write_text(
                json.dumps({'base_branch': 'trunk', 'sources': []}), encoding='utf-8')
            g('add', '-A'); g('commit', '-qm', 'first')
            g('remote', 'add', 'origin', str(up))
            g('push', '-q', '-u', 'origin', 'trunk')
            g('switch', '-q', '-c', 'feature')
            return repo, g

        work, gw = make('work')
        sib, gs = make('precedent-sibling')
        (work / 'w.txt').write_text('w\n', encoding='utf-8')
        gw('add', '-A'); gw('commit', '-qm', 'another session\'s work')
        (sib / 's.txt').write_text('s\n', encoding='utf-8')
        gs('add', '-A'); gs('commit', '-qm', 'another session\'s work')

        def scan():
            return pg._unlanded_work(work, siblings=True)

        got = scan()
        cases.append(('no session id: this checkout keeps its line',
                      any(l.startswith('this checkout:') for l in got), str(got)))
        cases.append(('no session id: a sibling gets no line',
                      not any('precedent-sibling' in l for l in got), str(got)))

        os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = sid_env
        got = scan()
        cases.append(('commits this session did not make get no line, in '
                      'this checkout or a sibling', got == [], str(got)))

        (work / 'w.txt').write_text('w, mine\n', encoding='utf-8')
        gw('add', '-A'); gw('commit', '-qm', f'my work\n\n{trailer}')
        (sib / 's.txt').write_text('s, mine\n', encoding='utf-8')
        gs('add', '-A'); gs('commit', '-qm', f'my work\n\n{trailer}')
        got = scan()
        cases.append(('a commit carrying this session\'s trailer brings this '
                      'checkout\'s line back',
                      any(l.startswith('this checkout:') and "'feature'" in l
                          for l in got), str(got)))
        cases.append(('and a sibling\'s line, named by its directory',
                      any(l.startswith('precedent-sibling:') for l in got), str(got)))
    finally:
        os.environ.pop('CLAUDE_CODE_REMOTE_SESSION_ID', None)
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


