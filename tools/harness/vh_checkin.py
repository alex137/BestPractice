# The harness tests for check-in pull requests from dependent repositories
#
# tools/harness/vh_checkin.py -- part of the verification harness:
# check-in pull requests from dependent repositories.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_update_mirrors_from_a_depth_1_source_clone():
    """checkin.py update and record fetch the recorded commit a depth-1
    source clone lacks, bounded, instead of refusing.

    2026-10-29, a consumer's Update Vendors: the copied-in set's clone came
    from add_repo's `--depth 1`, so the commit its checkin recorded was not
    in it, and update refused with "recorded commit ... not found in the
    clone -- fetch it there, or pass --force". A bounded fetch by hand fixed
    it. Negative control, measured the same day: staging's checkin.py
    before this refuses the first case with exactly that message."""
    import tempfile as _tf
    cases = []
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    tmp = pathlib.Path(_tf.mkdtemp(prefix='precedent-shallow-source-'))
    try:
        def git(cwd, *a):
            return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                                  text=True, env=env)

        up, consumer = tmp / 'up', tmp / 'consumer'
        for d in (up, consumer):
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(d)], env=env)
        (up / 'practices').mkdir()
        (up / 'practices' / 'a.md').write_text('one\n', encoding='utf-8')
        git(up, 'add', '.'); git(up, 'commit', '-qm', 'c1')
        c1 = git(up, 'rev-parse', 'HEAD').stdout.strip()
        (up / 'practices' / 'a.md').write_text('one\ntwo\n', encoding='utf-8')
        git(up, 'commit', '-qam', 'c2')
        (up / 'practices' / 'b.md').write_text('three\n', encoding='utf-8')
        git(up, 'add', '.'); git(up, 'commit', '-qm', 'c3')
        tip = git(up, 'rev-parse', 'HEAD').stdout.strip()
        vendored = consumer / 'process' / 'upstream' / 'practices'
        vendored.mkdir(parents=True)
        (vendored / 'a.md').write_text('one\n', encoding='utf-8')
        (consumer / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': f'file://{up}', 'vendored_at': 'process/upstream',
                         'branch': 'main', 'commit': c1}, 'entries': []}) + '\n',
            encoding='utf-8')
        git(consumer, 'add', '.'); git(consumer, 'commit', '-qm', 'vendored at c1')

        def shallow_clone():
            clone = tmp / 'clone'
            shutil.rmtree(clone, ignore_errors=True)
            subprocess.run(['git', 'clone', '-q', '--depth', '1', f'file://{up}',
                            str(clone)], env=env)
            return clone

        def checkin(*a):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'checkin.py'), *a],
                               capture_output=True, text=True, env=env, cwd=consumer)
            return r.returncode, r.stdout + r.stderr

        clone = shallow_clone()
        cases.append(('the fixture clone is shallow and lacks the recorded commit',
                      git(clone, 'cat-file', '-e', f'{c1}^{{commit}}').returncode != 0, ''))
        rc, out = checkin('update', str(clone), '--repo', str(consumer))
        cases.append(('update mirrors from it',
                      rc == 0 and (vendored / 'b.md').is_file()
                      and (vendored / 'a.md').read_text(encoding='utf-8') == 'one\ntwo\n',
                      failure_detail(out, 600)))
        clone = shallow_clone()
        rc, out = checkin('record', str(clone), '--repo', str(consumer))
        m = json.loads((consumer / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        cases.append(('record\'s carry check runs against a fresh depth-1 clone too',
                      rc == 0 and m['upstream']['commit'] == tip, failure_detail(out, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f' ({c[2]})' if c[2] else '') for c in cases if not c[1]]
    check(f'Update Vendors mirrors from a depth-1 source clone without refusing '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_vendors_resolves_a_catalogue_edit():
    """The same resolution for process/upstream/, a pre-2026-09-14 install's
    mirrored catalogue: a committed, pushed local edit to a vendored
    practice, where upstream changed the same file elsewhere, is resolved
    (merged until 2026-10-08; upstream's version since, the rest shown), and
    `record` passes because its carry check skips exactly the file being
    resolved (checkin.py record --resolving).

    BASE is a commit object on top of origin/<source branch> whose copy of
    one practice lacks upstream's last line, so NEW (what checkin.py update
    mirrors) differs from BASE in exactly that file.

    Negative control, measured 2026-09-29: with c1dd37f5's
    precedent_update.py the update refuses ("the vendored tree has local
    changes"); with --resolving removed from the record call, record is held
    by the carry check ("lines to lose")."""
    import precedent_vendor_engine as _pve
    branch = _pve.SOURCE_BRANCH
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', '--quiet',
                           f'origin/{branch}'], capture_output=True, text=True).stdout.strip()
    if not head:
        not_applicable('Update Vendors resolves a local edit in process/upstream/',
                       f'this clone has no origin/{branch} for the catalogue to mirror')
        return
    fx = _LocalEditsFixture('precedent-local-edits-cat-')
    cases = []
    try:
        repo = fx.consumer('catalogue')
        seeded = fx.seeded_from(repo)
        # One commit for engine AND catalogue: precedent_update.py --from-ref
        # mirrors the catalogue at the ref too since 2026-10-03, so the
        # fixture is built on the commit the update will mirror.
        head = seeded
        practice = 'practices/verify-postcondition.md'
        upstream_text = subprocess.run(['git', '-C', str(ROOT), 'show',
                                        f'{head}:{practice}'], capture_output=True).stdout
        lines = upstream_text.decode().rstrip('\n').splitlines(True)
        base_text = ''.join(lines[:-1]).encode()
        base_commit = fx.upstream(head, {practice: base_text})
        (repo / 'process').mkdir()
        (repo / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream', 'branch': branch,
                         'commit': head}, 'entries': []}, indent=2) + '\n',
            encoding='utf-8')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--force', '--from-ref', head, cwd=repo)
        m = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        m['upstream']['commit'] = base_commit
        (repo / 'process' / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n',
                                                        encoding='utf-8')
        f = repo / 'process' / 'upstream' / practice
        local = _insert(base_text, 'A line this repo added to fix a local bug.\n', at=16)
        f.write_bytes(local)
        fx.commit(repo, 'a local fix to a vendored practice')
        fx.sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=repo)
        rc, out = fx.update(repo, seeded)
        got = f.read_bytes()
        rec = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        # Since 2026-10-08 (Morgan, decided): upstream's version, with the
        # rest of the edit shown for the session to judge.
        pref = _section(out, PREFERRED_GROUP)
        cases.append(('a committed local edit in process/upstream/ that upstream '
                      'changed elsewhere is resolved, not refused: upstream\'s '
                      'version taken, the rest shown',
                      'refused' not in out.split('catalogue', 1)[-1][:200]
                      and got == upstream_text
                      and f'process/upstream/{practice}' in pref
                      and '+A line this repo added' in pref,
                      failure_detail(pref or out, 2500)))
        cases.append(('...and record passes, its carry check skipping only that file',
                      'catalogue record' in out and 'held' not in out
                      and rec['upstream']['commit'] == head, failure_detail(out, 1500)))
    finally:
        fx.close()
    # Records its own verdict, so the not-applicable path above is said as
    # such and never counted as a pass.
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors resolves a committed local edit in process/upstream/ '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_vendors_declined_catalogue_copy_is_upstreams():
    """A declined catalogue file, changed upstream and re-decided once,
    passes the update and the consumer's audit on the next run: its vendored
    copy is always upstream's text at the recorded commit, the one basis
    both judge the decline by (practice_audit.decline_basis).

    2026-10-08, from a consuming repository, for two templates/local-
    practices/ templates: a run ended FAILED with the mirrored copy staged;
    the person ran --redecide, which changed process/manifest.json; the
    rerun put the staged files back to HEAD -- all but the manifest, now
    changed -- so the old copy read as a local edit against the new
    upstream.commit and was kept ("upstream has not changed this file"),
    while checkin.py judged the decline inside the swap, on upstream's text.
    Every recorded hash then failed one of the two. Here the FAILED end is
    the record a FAILED run writes (precedent_update.record_staged_output).

    Also: in a repo that vendors its engine, a declined tools/ file is
    judged by the engine manifest, never by a leftover copy under
    process/upstream/tools/ that the mirror no longer writes.

    Negative control, measured 2026-10-08 against
    2026-10-08-update-integrity-y1ktn at 353a946f: the rerun keeps the old
    copy as "still your local edit", the audit fails DECLINED, and a second
    --redecide makes the next run ask again; the leftover is the basis."""
    import hashlib
    import precedent_vendor_engine as _pve
    import precedent_update as _pu
    branch = _pve.SOURCE_BRANCH
    fx = _LocalEditsFixture('precedent-declined-copy-')
    cases = []
    sha = lambda b: hashlib.sha256(b).hexdigest()
    try:
        repo = fx.consumer('decline')
        seeded = fx.seeded_from(repo)
        rel = 'templates/local-practices/project-voice.md.template'
        old = subprocess.run(['git', '-C', str(ROOT), 'show', f'{seeded}:{rel}'],
                             capture_output=True).stdout
        (repo / 'process').mkdir()
        (repo / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream', 'branch': branch,
                         'commit': seeded, 'scrub_blocklist': None},
            'entries': [{'practice': 'project-voice', 'upstream_path': rel,
                         'local_path': None, 'status': 'declined',
                         'declined_upstream_sha256': sha(old),
                         'notes': 'no reader-facing prose here'}]},
            indent=2) + '\n', encoding='utf-8')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--force', '--from-ref', seeded, cwd=repo)
        fx.commit(repo, 'catalogue with a declined template')
        fx.sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=repo)
        aud = repo / '.audit' / 'tools'
        aud.mkdir(parents=True)
        for n in ('practice_audit.py', 'generated_blocks.py', 'checkin.py',
                  'precedent_time.py', 'declared_base_branch.py'):
            shutil.copy(ROOT / 'tools' / n, aud / n)
        with open(repo / '.git' / 'info' / 'exclude', 'a', encoding='utf-8') as f:
            f.write('.audit/\n')
        new = old + b'\nA sentence upstream added.\n'
        ref = fx.upstream(seeded, {rel: new})
        copy = repo / 'process' / 'upstream' / rel
        asked = lambda out: 'a decline to decide again' in out.split('LEFT FOR YOU', 1)[-1] \
            and 'LEFT FOR YOU' in out
        redecide = lambda: fx.sh(sys.executable, str(aud / 'practice_audit.py'),
                                 '--redecide', 'project-voice', cwd=repo)
        recorded = lambda: json.loads((repo / 'process' / 'manifest.json').read_text(
            encoding='utf-8'))['entries'][0]['declined_upstream_sha256']

        _rc, out1 = fx.update(repo, ref)
        cases.append(('the first run asks to decide the moved decline again',
                      asked(out1), failure_detail(out1, 1500)))
        staged = fx.git(repo, 'diff', '--cached', '--name-only').split()
        _pu.record_staged_output(repo, staged)        # run 1 ended FAILED
        redecide()
        cases.append(('--redecide records upstream\'s new text', recorded() == sha(new),
                      recorded()))
        _rc, out2 = fx.update(repo, ref)
        cases.append(('the rerun does not ask again', not asked(out2), failure_detail(out2, 1500)))
        cases.append(('...and leaves the copy as upstream\'s text, never the old one '
                      'as a local edit', copy.read_bytes() == new,
                      [l for l in out2.splitlines() if rel in l][:4]))
        _rc, audit = fx.sh(sys.executable, str(aud / 'practice_audit.py'), cwd=repo)
        cases.append(('the consumer\'s own audit agrees: no DECLINED failure',
                      'DECLINED:' not in audit and 'declined OK' in audit, failure_detail(audit, 1500)))
        redecide()
        _rc, out3 = fx.update(repo, ref)
        cases.append(('a second --redecide keeps the hash, and the next run does not '
                      'ask', recorded() == sha(new) and not asked(out3), failure_detail(out3, 1500)))

        # A leftover copy of a declined engine file is not its basis.
        tool = 'tools/precedent_show.py'
        leftover = repo / 'process' / 'upstream' / tool
        leftover.parent.mkdir(parents=True, exist_ok=True)
        leftover.write_bytes(b'# an old copy the mirror no longer writes\n')
        engine = json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json').read_text(
            encoding='utf-8'))['sha256']['precedent_show.py']
        r = subprocess.run([sys.executable, '-c',
                            'import sys, pathlib; sys.path.insert(0, sys.argv[1]); '
                            'import practice_audit as p; r = pathlib.Path(sys.argv[2]); '
                            'print(p.decline_basis(r, r / "process" / "upstream", '
                            'sys.argv[3])[0])', str(aud), str(repo), tool],
                           capture_output=True, text=True, cwd=str(repo))
        cases.append(('a declined tools/ file is judged by the engine manifest, not a '
                      'leftover under process/upstream/tools/',
                      r.stdout.strip() == engine, (r.stdout.strip(), engine, failure_detail(r.stderr, 300))))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))

def check_update_vendors_leaves_the_copy_its_record_names():
    """Update Vendors ends with the vendored catalogue copy holding exactly
    what the commit process/manifest.json records gives under the copy
    rules, apart from a local edit it resolved and kept, which it reports.

    2026-10-08, a consuming repository: after its update said DONE, both
    manifests recorded one commit while 440 of the 604 files under
    process/upstream/ were other upstream versions and process/upstream/
    tools/ held 99 files the copy no longer carries. The route: the copy was
    put back to an older commit than the (uncommitted) manifest named -- a
    reset of process/upstream/ after a refusal, or an earlier run's
    put-back with the manifest since changed -- and the local-edit rules
    then kept every older upstream text as "your edit", while the drop of
    files the copy no longer carries recognised upstream's text at two
    commits only. Four cases: a stale copy with a real local edit beside
    it; a rerun after the source moved, over an earlier run's uncommitted
    mirror ("changed here and not committed" before); a put-back followed
    by a rerun, with the manifest changed since; and the postcondition
    itself, called directly, for a file only the run-to-run record shows
    was an earlier run's deletion; and a run that fails before its staging
    step, which now records what it wrote and deleted for its rerun. Case 1
    also asserts the copy's fingerprint is recorded once the local-edit
    rules have run, so the repository's own check finds the kept edit
    unchanged and names a file put back to older text afterwards
    (check_copy_fingerprint_is_checked_without_a_clone has the check's own
    cases).

    Negative control, measured 2026-10-08 against
    2026-10-08-update-integrity-y1ktn at 353a946f: the stale files are
    listed as "Still your local edit" and kept, the stale tools/ file stays,
    and DONE is printed over them (case 1); the rerun is refused, "the
    vendored tree has an uncommitted change", over the earlier run's mirror
    (case 2); the put-back rerun keeps both the stale practice and the
    dropped tool (case 3); the run failing before staging records nothing,
    so its rerun puts nothing back (case 5); and neither the postcondition
    nor the record's realignment exists (case 4)."""
    import contextlib
    import filecmp
    import io
    import tempfile
    import precedent_vendor_engine as _pve
    branch = _pve.SOURCE_BRANCH
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as pu
        import precedent_local_edits as le
    finally:
        sys.path.pop(0)
    fx = _LocalEditsFixture('precedent-copy-record-')
    cases = []
    tool = 'tools/routing_reasons.py'      # not an engine file: the copy leaves it out
    edited, moved = 'practices/repo-is-memory.md', 'practices/verify-postcondition.md'
    show = lambda ref, rel: subprocess.run(['git', '-C', str(ROOT), 'show', f'{ref}:{rel}'],
                                           capture_output=True).stdout
    up = lambda repo, rel: repo / 'process' / 'upstream' / rel

    def pristine(repo):
        # Every case starts from the same consumer: its catalogue vendored
        # at the seeded commit and its first update run. Built once per
        # checkout state and copied for each case, repository and bare
        # origin (Morgan, 2026-10-09: "share the fake project"; the build
        # is about 25 seconds of real update runs), so nothing a case does
        # reaches another (_uv_cached_consumer).
        seeded = fx.seeded_from(repo)
        (repo / 'process').mkdir()
        (repo / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream', 'branch': branch,
                         'commit': seeded, 'scrub_blocklist': None},
            'entries': []}, indent=2) + '\n', encoding='utf-8')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--force', '--from-ref', seeded, cwd=repo)
        # Answer the bare fixture's first-run questions, so a later run
        # can end DONE.
        fx.update(repo, seeded)
        fx.commit(repo, 'catalogue at the seeded commit')

    def build(name):
        repo = _uv_cached_consumer(fx, name, 'catalogue-at-seeded', pristine)
        return repo, fx.seeded_from(repo)

    def mismatch(repo, ref):
        """-> the copy-relative paths where the copy is not `ref` under the
        copy rules (both directions)."""
        ck = le._checkin(repo)
        with tempfile.TemporaryDirectory() as td:
            ck._tree_at(ROOT, ref, td)
            theirs = ck._files(pathlib.Path(td))
            ours = {p.relative_to(ck.UPSTREAM) for p in ck.UPSTREAM.rglob('*')
                    if p.is_file()}
            return sorted(p.as_posix() for p in ours ^ theirs) + sorted(
                p.as_posix() for p in ours & theirs
                if not filecmp.cmp(ck.UPSTREAM / p, pathlib.Path(td) / p, shallow=False))

    try:
        # --- 1. a stale copy, with a real local edit beside it ------------
        repo, seeded = build('stale')
        # Back along the first parents until four files changed, never a
        # fixed 40 commits (2026-10-20: on a quiet stretch 40 commits changed
        # two or three, and the case failed with nothing wrong in the code).
        line = subprocess.run(['git', '-C', str(ROOT), 'rev-list', '--first-parent',
                               seeded], capture_output=True, text=True).stdout.split()
        for back in (40, 80, 160, 320, len(line) - 1):
            old = line[min(back, len(line) - 1)]
            stale = [r for r in subprocess.run(
                ['git', '-C', str(ROOT), 'diff', '--name-only', '--diff-filter=M', old,
                 seeded, '--', 'practices/', 'templates/'],
                capture_output=True, text=True).stdout.split()
                if r not in (edited, moved)][:4]
            if len(stale) == 4:
                break
        for rel in stale:
            up(repo, rel).write_bytes(show(old, rel))
        up(repo, tool).parent.mkdir(parents=True, exist_ok=True)
        up(repo, tool).write_bytes(show(old, tool) or show(seeded, tool))
        local = _insert(show(seeded, edited), 'A line this repo added on purpose.\n', at=8)
        up(repo, edited).write_bytes(local)
        fx.commit(repo, 'a copy older than its record, and one real local edit')
        fx.sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=repo)
        ref = fx.upstream(seeded, {moved: show(seeded, moved) + b'\nUpstream moved.\n'})
        rc, out = fx.update(repo, ref)
        left = mismatch(repo, ref)
        cases.append(('a stale copy ends as the commit its record names, the stale '
                      'tools/ file gone, and DONE is said',
                      len(stale) == 4 and left == [edited] and 'DONE' in out
                      and not up(repo, tool).exists(), (stale, left, failure_detail(out, 1500))))
        cases.append(('...while the real local edit is kept and reported, never '
                      'overwritten',
                      up(repo, edited).read_bytes() == local
                      and f'process/upstream/{edited}' in _section(out, 'Still your local edit')
                      and not any(f'process/upstream/{r}' in _section(out, 'Still your')
                                  for r in stale), _section(out, 'Still your')))
        # The fingerprint the consumer's own check compares with, recorded
        # after the local-edit rules ran: the kept edit is part of it.
        ck = le._checkin(repo)
        fp = (json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
              .get('upstream') or {}).get('copy_tree')
        drift = ck.copy_drift(repo)
        cases.append(('...and the copy\'s fingerprint is recorded, so the repository\'s '
                      'own check finds nothing drifted, the kept edit included',
                      bool(fp) and [d[2] for d in drift] == ['ok']
                      and 'catalogue fingerprint: recorded' in out, (fp, drift)))
        fx.commit(repo, 'the update')
        up(repo, moved).write_bytes(show(seeded, moved))
        drift = ck.copy_drift(repo)
        cases.append(('...and a file put back to older upstream text after the update '
                      'is named as drifted, with no upstream clone',
                      [(d[2], d[3]) for d in drift] == [('drifted', [(moved, 'changed')])],
                      drift))

        # --- 2. a rerun after the source moved, over an earlier run's mirror
        repo, seeded = build('moved')
        ref1 = fx.upstream(seeded, {moved: show(seeded, moved) + b'\nFirst move.\n'})
        # An earlier run's mirror with no record behind it: the manifest
        # still names the commit before it.
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--from-ref', ref1, cwd=repo)
        ref2 = fx.upstream(ref1, {edited: show(seeded, edited) + b'\nSecond move.\n'})
        rc, out = fx.update(repo, ref2)
        rec = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        cases.append(('a rerun after the source moved takes the earlier run\'s mirror '
                      'as its own: not refused, and the copy is the new commit',
                      'not committed' not in out and rec['upstream']['commit'] == ref2
                      and mismatch(repo, ref2) == [] and 'DONE' in out,
                      (mismatch(repo, ref2), failure_detail(out, 1500))))

        # --- 3. a put-back followed by a rerun ----------------------------
        repo, seeded = build('putback')
        up(repo, tool).parent.mkdir(parents=True, exist_ok=True)
        up(repo, tool).write_bytes(show(seeded, tool))
        fx.commit(repo, 'catalogue at the seeded commit, tools/ still in it')
        ref1 = fx.upstream(seeded, {moved: show(seeded, moved) + b'\nFirst move.\n',
                                    tool: show(seeded, tool) + b'\n# upstream changed it\n'})
        rc, out1 = fx.update(repo, ref1)
        staged = [l for l in fx.git(repo, 'diff', '--cached', '--name-only').splitlines() if l]
        dropped_first = not up(repo, tool).exists()
        # As a FAILED run leaves it: its output staged and recorded.
        pu.record_staged_output(repo, staged)
        # The person changes the manifest afterwards (practice_audit.py
        # --redecide writes a decline there), so the put-back leaves it,
        # naming ref1, while it puts the copy back to HEAD.
        m = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        m['_redecided'] = 'a change of the person\'s, after the failure'
        (repo / 'process' / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n',
                                                        encoding='utf-8')
        rc, out = fx.update(repo, ref1)
        m = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        cases.append(('after a put-back and a rerun, what the first run deleted stays '
                      'deleted and the copy is the recorded commit',
                      dropped_first and 'put back to HEAD' in out
                      and not up(repo, tool).exists() and mismatch(repo, ref1) == []
                      and 'Still your local edit' not in out,
                      (dropped_first, mismatch(repo, ref1), failure_detail(out, 1500))))
        cases.append(('...the manifest the person changed has its record of the copy '
                      'put back with the copy, and keeps the person\'s change',
                      'its record of the copy goes back to' in out
                      and m.get('_redecided') and m['upstream']['commit'] == ref1,
                      [l for l in out.splitlines() if 'earlier run' in l]))

        # --- 5. a run that fails before staging records what it wrote -----
        repo, seeded = build('early')
        up(repo, tool).parent.mkdir(parents=True, exist_ok=True)
        up(repo, tool).write_bytes(show(seeded, tool))
        fx.commit(repo, 'catalogue at the seeded commit, tools/ still in it')
        ref1 = fx.upstream(seeded, {moved: show(seeded, moved) + b'\nFirst move.\n'})
        rc, out1 = fx.sh(sys.executable, '-c', (
            'import sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_update as pu\n'
            'real = pu.run\n'
            'def run(argv, cwd):\n'
            '    if any(str(a).endswith("precedent_sync_views.py") for a in argv):\n'
            '        return 1, "stubbed: the view sync failed"\n'
            '    return real(argv, cwd)\n'
            'pu.run = run\n'
            f'sys.exit(pu.main(["--repo", {str(repo)!r}, "--from-ref", {ref1!r}, '
            '"--skip-check"]))\n'), cwd=repo)
        held = pu._read_record(repo).get('paths') or {}
        cases.append(('a run that fails before its staging step records what it wrote '
                      'and what it deleted',
                      rc == 2 and 'the view sync failed' in out1
                      and held.get(f'process/upstream/{moved}')
                      and f'process/upstream/{tool}' in held
                      and held[f'process/upstream/{tool}'] is None,
                      (rc, sorted(held)[:8], failure_detail(out1, 800))))
        ref2 = fx.upstream(ref1, {edited: show(seeded, edited) + b'\nSecond move.\n'})
        rc, out = fx.update(repo, ref2)
        cases.append(('...so the rerun, after the source moved, puts it back as its own '
                      'output, deletes the dropped file again, and ends on the new '
                      'commit',
                      'put back to HEAD' in out and 'not committed' not in out
                      and not up(repo, tool).exists() and mismatch(repo, ref2) == []
                      and 'DONE' in out, (mismatch(repo, ref2), failure_detail(out, 1500))))

        # --- 4. the postcondition, called directly ------------------------
        post = getattr(pu, 'catalogue_copy_postcondition', None)
        repo, seeded = build('direct')
        mine = 'gotchas/not-upstream-text.md'
        up(repo, mine).parent.mkdir(parents=True, exist_ok=True)
        up(repo, mine).write_text('Text upstream never shipped here.\n', encoding='utf-8')
        fx.commit(repo, 'catalogue, and a file of this repo\'s own in it')
        for put_back, name in (((), 'a file nothing resolved is left for the person, '
                                    'not overwritten'),
                               ((f'process/upstream/{mine}',),
                                'the same file, shown by the record as an earlier '
                                'run\'s deletion the put-back restored, is deleted '
                                'again')):
            rep = pu.Report()
            if post is None:
                cases.append((name, False, 'no catalogue_copy_postcondition'))
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                post(repo, rep, put_back)
            gone = not up(repo, mine).exists()
            named = any(w == f'process/upstream/{mine}' for w, _ in rep.left)
            cases.append((name, gone if put_back else (named and not gone),
                          (rep.left, rep.steps)))
        # The put-back's own consistency: the record of the copy goes back
        # with the copy, and only the keys checkin.py record writes.
        realign = getattr(pu, 'realign_catalogue_record', None)
        mf = repo / 'process' / 'manifest.json'
        rd = lambda: json.loads(mf.read_text(encoding='utf-8'))
        wr = lambda d: mf.write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8')
        at_head = rd()['upstream']['commit']
        m = rd()
        m['upstream'].update(commit='f' * 40, synced_from='f' * 40)
        m['_mine'] = 1
        wr(m)
        wrote = {'process/manifest.json': 'x', 'process/upstream/practices/a.md': 'y'}
        back = ['process/upstream/practices/a.md']
        got = realign(repo, wrote, back) if realign else None
        cases.append(('a manifest not put back has its record of the copy put back to '
                      'HEAD\'s, the person\'s change kept',
                      got == at_head and rd()['upstream']['commit'] == at_head
                      and rd()['upstream']['synced_from'] == at_head
                      and rd().get('_mine') == 1, (got, rd().get('upstream'))))
        m = rd()
        m['upstream'].update(commit='f' * 40, branch='another')
        wr(m)
        got = realign(repo, wrote, back) if realign else 'missing'
        cases.append(('...but not when the person changed another key of its upstream '
                      'record', got is None and rd()['upstream']['commit'] == 'f' * 40,
                      (got, rd().get('upstream'))))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_copy_fingerprint_is_checked_without_a_clone():
    """A consuming repository's own check (vendored-copy-matches-record)
    tells, with no BestPractice clone, that its vendored copy changed after
    process/manifest.json recorded it: the manifest keeps the copy's git tree
    id (checkin.COPY_TREE_KEY), and the repository's own history names the
    files that differ (2026-10-08; Morgan decided it the same day).

    Both directions: a changed, an added and a removed file are each named
    and fail the check; a file the manifest marks diverged, or precedent.json
    keeps under kept_template_divergences with a reason, does not (one kept
    with no reason does); a declined file's copy
    is still checked, since a decline is judged by upstream's text there; a
    manifest written before the fingerprint is COULD NOT VERIFY, never a
    pass or a fail; and recording the fingerprint leaves the repository's own
    index as it was.

    Negative control, measured 2026-10-08: with copy_drift's per-file
    comparison made to skip every file, and a missing fingerprint read as a
    match, the could-not-verify case and the named-files case fail; with the
    exemption by name removed, the exemption case fails, naming
    practices/mine.md. On the commit before this one nothing here exists, so
    the whole check fails."""
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import checkin as ck
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    cases = []
    env = _fixture_git_env()
    fn = getattr(getattr(pc, 'CHECKS', {}).get('vendored-copy-matches-record'), 'get',
                 lambda _k: None)('fn')
    if not hasattr(ck, 'copy_drift') or fn is None:
        return (False, '0 stated cases',
                'checkin.copy_drift or the vendored-copy-matches-record check is missing')
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        tree = repo / 'process' / 'upstream'
        for rel, text in (('practices/a.md', 'a\n'), ('practices/b.md', 'b\n'),
                          ('templates/t.md', 't\n'), ('templates/u.md', 'u\n'),
                          ('practices/declined.md', 'd\n'),
                          ('practices/mine.md', 'm\n')):
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            (tree / rel).write_text(text, encoding='utf-8')
        mf = repo / 'process' / 'manifest.json'
        manifest = {'upstream': {'repo': 'https://example.invalid/BestPractice',
                                 'vendored_at': 'process/upstream', 'commit': 'a' * 40},
                    'entries': []}
        mf.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'vendored copy, recorded before the fingerprint existed')

        def run_check():
            old = pc.ROOT
            pc.ROOT = repo
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    return fn(None)
            except pc.NotApplicable as e:
                return f'not applicable: {e}'
            finally:
                pc.ROOT = old

        got = run_check()
        cases.append(('a manifest with no fingerprint is COULD NOT VERIFY, not a pass '
                      'or a fail',
                      isinstance(got, list) and len(got) == 1
                      and isinstance(got[0], pc.Unverified)
                      and 'no fingerprint' in got[0].detail, got))

        (tree / 'practices' / 'untracked-scratch.md').write_text('x\n', encoding='utf-8')
        status_before = g('status', '--porcelain').stdout
        tid = ck.stamp_copy_tree(mf)
        status_after = g('status', '--porcelain').stdout
        cases.append(('recording the fingerprint leaves the repository\'s own index '
                      'as it was',
                      bool(tid) and status_before.replace(' M process/manifest.json\n', '')
                      == status_after.replace(' M process/manifest.json\n', '')
                      and '?? process/upstream/practices/untracked-scratch.md'
                      in status_after, (status_before, status_after)))
        (tree / 'practices' / 'untracked-scratch.md').unlink()
        ck.stamp_copy_tree(mf)
        g('add', '-A')
        g('commit', '-qm', 'the fingerprint recorded')
        cases.append(('a copy as recorded passes',
                      run_check() == [] and json.loads(mf.read_text())['upstream']
                      .get('copy_tree') == g('rev-parse', 'HEAD:process/upstream')
                      .stdout.strip(), run_check()))

        (tree / 'practices' / 'a.md').write_text('older upstream text\n', encoding='utf-8')
        (tree / 'practices' / 'b.md').unlink()
        (tree / 'practices' / 'stray.md').write_text('stray\n', encoding='utf-8')
        (tree / 'practices' / 'declined.md').write_text('edited\n', encoding='utf-8')
        (tree / 'practices' / 'mine.md').write_text('my change\n', encoding='utf-8')
        (tree / 'templates' / 't.md').write_text('kept on purpose\n', encoding='utf-8')
        (tree / 'templates' / 'u.md').write_text('kept, no reason\n', encoding='utf-8')
        data = json.loads(mf.read_text(encoding='utf-8'))
        data['entries'] = [
            {'practice': 'mine', 'upstream_path': 'practices/mine.md',
             'local_path': 'process/upstream/practices/mine.md', 'granularity': 'file',
             'status': 'diverged', 'notes': 'pending export'},
            {'practice': 'declined', 'upstream_path': 'practices/declined.md',
             'local_path': None, 'status': 'declined', 'notes': 'not taken'}]
        mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'kept_template_divergences': {
            'process/upstream/templates/t.md': {'reason': 'ours on purpose'},
            'process/upstream/templates/u.md': {'reason': ''}}}),
            encoding='utf-8')
        got = run_check()
        named = {f.where for f in got if isinstance(f, pc.Finding)
                 and not isinstance(f, pc.Unverified)} if isinstance(got, list) else set()
        want = {'process/upstream/practices/a.md', 'process/upstream/practices/b.md',
                'process/upstream/practices/stray.md',
                'process/upstream/practices/declined.md',
                'process/upstream/templates/u.md', 'process/manifest.json'}
        cases.append(('a changed, a removed, an added and a declined file, and one '
                      'kept with no reason, are each named and fail the check, '
                      'with the remedy',
                      want <= named and any('Update Vendors' in f.detail for f in got
                                            if f.where == 'process/manifest.json'),
                      sorted(named)))
        cases.append(('...while a diverged entry\'s file and a kept template '
                      'divergence are exempt by name',
                      'process/upstream/practices/mine.md' not in named
                      and 'process/upstream/templates/t.md' not in named, sorted(named)))

        data['upstream']['copy_tree'] = 'f' * 40
        mf.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        got = run_check()
        cases.append(('a copy that differs from a tree this clone lacks fails, saying '
                      'the files cannot be named here',
                      isinstance(got, list) and len(got) == 1
                      and not isinstance(got[0], pc.Unverified)
                      and 'cannot be named' in got[0].detail, got))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_with_source_stamps_that_sources_manifest():
    """`checkin.py update --source NAME` records which commit it mirrored in
    process/manifest_NAME.json, and leaves the universal manifest alone.
    Origin: the stamp was written to process/manifest.json whatever the
    source, so vendoring a shared set moved the universal set's
    synced_from to a commit of a different repository. Control: with no
    source selected the stamp lands in the universal manifest."""
    import importlib.util, tempfile
    bad, cases = [], []
    spec = importlib.util.spec_from_file_location('_vh_checkin', ROOT / 'tools' / 'checkin.py')
    ck = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ck)
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        (root / 'process').mkdir()
        uni = root / 'process' / 'manifest.json'
        shared = root / 'process' / 'manifest_team-x.json'
        for f in (uni, shared):
            f.write_text(json.dumps({'upstream': {'commit': 'old', 'synced_from': 'old'}}), encoding='utf-8')
        saved = (ck.ROOT, ck.MANIFEST, ck.UPSTREAM, ck.SOURCE)
        try:
            ck.ROOT = root
            ck.MANIFEST = uni
            ck._select_source('team-x')
            ck._stamp_synced_from('new')
            got_shared = json.loads(shared.read_text())['upstream']['synced_from']
            got_uni = json.loads(uni.read_text())['upstream']['synced_from']
            cases.append('a shared source stamps its own manifest')
            if got_shared != 'new' or got_uni != 'old':
                bad.append(f'with --source: shared={got_shared!r}, universal={got_uni!r}')
            ck.MANIFEST = uni
            ck._stamp_synced_from('newer')
            cases.append('control: no source stamps the universal manifest')
            if json.loads(uni.read_text())['upstream']['synced_from'] != 'newer':
                bad.append('with no source the universal manifest was not stamped')
        finally:
            ck.ROOT, ck.MANIFEST, ck.UPSTREAM, ck.SOURCE = saved
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_every_file_is_decided_by_a_vendoring_rule():
    """tools/checkin.py's VENDORING_RULES decide every file: a path in a new
    top-level place is UNDECIDED (no rule, left out of the copy), an
    exception inside a shipped folder wins over the folder, and this repo
    as it stands has no undecided file. Morgan, 2026-09-30: "make sure that
    *every new file* is evaluated to see if it should be vendored in or
    not"."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import checkin
    cases = []
    rule = checkin.vendoring_rule('newplace/notes.md')
    cases.append(('a file in a new top-level place has no rule',
                  rule is None, rule))
    cases.append(('an undecided file stays out of the copy',
                  not checkin._in_copy('newplace/notes.md', carries_tools=True),
                  ''))
    rule = checkin.vendoring_rule('tools/verify_harness.py')
    cases.append(('the test suite stays, though tools/ ships',
                  rule is not None and rule[1] is False, rule))
    rule = checkin.vendoring_rule('practices/any-rule.md')
    cases.append(('a practice ships', rule is not None and rule[1], rule))
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_check.py'),
                        '--only', 'vendoring-decided'],
                       capture_output=True, text=True, cwd=str(ROOT))
    cases.append(('this repo has no undecided file',
                  r.returncode == 0 and ' 0 violated' in r.stdout,
                  failure_detail(r.stdout, 300) + failure_detail(r.stderr, 300)))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('every file is decided by a vendoring rule: ships or stays, and a '
          'new place is undecided until someone writes the rule',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_shipped_copy_has_no_broken_links():
    """A consumer's copy of the catalogue, as it lands under
    process/upstream/, has no relative link that does not resolve inside it.

    WHY (2026-10-08). A consumer's light check counted 227 broken links,
    every one inside its process/upstream/: since 2026-09-30 the copy
    leaves tools/ at home, and shipped documents linked ../tools/... freely,
    because shipped-links-travel asked a different question than the copy
    does. This builds the copy the way the copy is defined
    (checkin.in_shipped_copy, every tracked file) under a scratch
    process/upstream/ and resolves each Markdown link in it there."""
    import tempfile, posixpath, shutil as _shutil
    name = "a consumer's catalogue copy has no broken relative link"
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import checkin, doc_lint
    except Exception as e:                                    # noqa: BLE001
        not_applicable(name, f'tools/checkin.py or doc_lint.py did not import: {e}')
        return
    finally:
        sys.path.pop(0)
    if not hasattr(checkin, 'in_shipped_copy'):
        not_applicable(name, 'this checkin.py has no in_shipped_copy')
        return
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files'],
                             capture_output=True, text=True).stdout.split('\n')
    shipped = [f for f in tracked if f and (ROOT / f).is_file()
               and checkin.in_shipped_copy(f, ROOT)]
    broken = []
    with tempfile.TemporaryDirectory() as td:
        up = pathlib.Path(td) / 'process' / 'upstream'
        for f in shipped:
            (up / f).parent.mkdir(parents=True, exist_ok=True)
            _shutil.copyfile(ROOT / f, up / f)
        for f in shipped:
            if not f.endswith('.md'):
                continue
            incode = False
            for i, line in enumerate((up / f).read_text(
                    encoding='utf-8', errors='ignore').splitlines(), 1):
                if line.lstrip().startswith(('```', '~~~')):
                    incode = not incode
                    continue
                if incode:
                    continue
                clean = doc_lint.CODE_SPAN_RE.sub(lambda m: ' ' * len(m.group(0)), line)
                for _label, target in doc_lint.LINK_RE.findall(clean):
                    if target.startswith(('http://', 'https://', 'mailto:', '#')):
                        continue
                    bare = target.partition('#')[0]
                    if not bare or bare.startswith('<'):
                        continue      # an install placeholder, not a path
                    tgt = posixpath.normpath(posixpath.join(posixpath.dirname(f), bare))
                    # Broken in this repo too is doc_lint's finding here, not
                    # the copy's.
                    if not (ROOT / tgt).exists():
                        continue
                    if not (up / tgt).exists():
                        broken.append(f'{f}:{i} -> {tgt}')
    check(f'{name} ({len(shipped)} files copied)', not broken,
          f'{len(broken)} broken: ' + '; '.join(broken[:8]))


def check_catalogue_copy_is_an_allowlist():
    """The catalogue copy (checkin.py, a consumer's process/upstream/) took
    everything outside a short exclusion list: 543 files, among them this
    repo's test suite, its gotchas, its repo-local practices, its own
    .claude/ and .github/, and a second copy of the engine the consumer
    already vendors into its own tools/ (Morgan, 2026-09-30: "Consumers
    just want to use it" ... "let's do. Act!"). Discriminating cases: what
    a consumer uses goes, what is this repo's own stays home, and tools/
    goes only while the consumer's own engine lacks checkin.py -- then it
    stays home, so the repo keeps one copy."""
    import contextlib, io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import checkin as ck
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='catalogue-copy-'))
    saved = ck.ROOT
    cases = []
    try:
        ck.ROOT = tmp
        goes = ['practices/a.md', 'templates/t.md', 'documentation/d.md',
                'README.md', 'INSTALL.md', 'precedent-source.json',
                'reply_check.json', 'close_detect.json', 'tools/x.py',
                # Traps a session using Precedent hits (Morgan, 2026-10-01).
                'gotchas/g.md']
        stays = ['local/practices/l.md', 'bridge/run.py',
                 '.claude/settings.json', '.github/workflows/w.yml', 'MAP.md',
                 'WHERE_THINGS_ARE.md', 'TODO.md', 'AGENTS.md', 'spec/s.md',
                 'todo/t.md', 'templates/harness/LEDGER.md',
                 'tools/verify_harness.py', 'something-new/n.md',
                 # This project's own open items and news log: a consumer
                 # gets the machinery (tools/, templates/) and writes its own
                 # (Morgan, 2026-09-30).
                 'WHATS_NEW.md', 'todo/INDEX.md']
        cases.append(('what a consumer uses is in the copy',
                      all(ck._in_copy(r) for r in goes),
                      [r for r in goes if not ck._in_copy(r)]))
        cases.append(('THE CASE THIS EXISTS FOR: this repo\'s own material, '
                      'and anything not named, stays home',
                      not any(ck._in_copy(r) for r in stays),
                      [r for r in stays if ck._in_copy(r)]))
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}', encoding='utf-8')
        cases.append(('a consumer whose engine lacks checkin.py still gets '
                      'the copy\'s tools/', ck._in_copy('tools/x.py'), ''))
        (tmp / 'tools' / 'checkin.py').write_text('', encoding='utf-8')
        cases.append(('once its own engine carries checkin.py, tools/ stays '
                      'home: one copy of the engine',
                      not ck._in_copy('tools/x.py')
                      and ck._in_copy('practices/a.md'), ''))
        # What the copy stopped carrying is removed from a consumer's tree,
        # unless the consumer edited it: _diff() reads both sides through
        # the allowlist, so without this the old files would stay forever.
        saved_up, saved_man = ck.UPSTREAM, ck.MANIFEST
        try:
            ck.UPSTREAM = tmp / 'process' / 'upstream'
            ck.MANIFEST = tmp / 'process' / 'no-manifest.json'
            src = tmp / 'src'
            for tree in (ck.UPSTREAM, src):
                for rel in ('gotchas/g.md', 'local/l.md', 'tools/y.py',
                            'practices/p.md', 'todo/todo-x.md', 'TODO.md',
                            'WHATS_NEW.md'):
                    (tree / rel).parent.mkdir(parents=True, exist_ok=True)
                    (tree / rel).write_text('upstream\n', encoding='utf-8')
            (ck.UPSTREAM / 'local' / 'l.md').write_text('ours\n', encoding='utf-8')
            # A manifest entry for a file the sweep removes goes with it:
            # practice_audit.py fails "local_path missing" on one left behind
            # (2026-10-01, from a consumer's Update Vendors: doc-lint ->
            # process/upstream/tools/doc_lint.py).
            planted = [{'name': 'upstream:doc-lint',
                        'local_path': 'process/upstream/tools/y.py'},
                       {'name': 'upstream:p', 'local_path': 'process/upstream/practices/p.md'},
                       {'name': 'upstream:l', 'local_path': 'process/upstream/local/l.md'}]
            (tmp / 'process' / 'manifest.json').write_text(
                json.dumps({'entries': planted}), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                dropped, kept = ck._drop_what_the_copy_no_longer_carries(tmp, src)
            left = [e['name'] for e in json.loads((tmp / 'process' / 'manifest.json')
                                                  .read_text(encoding='utf-8'))['entries']]
            cases.append(('a manifest entry for a removed file is dropped with it; '
                          'one for a file still there, or kept as edited, stays',
                          left == ['upstream:p', 'upstream:l'], str(left)))
            # A consumer an older update already left that way is healed on
            # the next run, when there is nothing left to remove.
            (tmp / 'process' / 'manifest.json').write_text(json.dumps({'entries': [
                {'name': 'upstream:gone', 'local_path': 'process/upstream/tools/gone.py'},
                {'name': 'own', 'local_path': 'docs/missing-but-ours.md'}]}),
                encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                ck._drop_what_the_copy_no_longer_carries(tmp, src)
            left = [e['name'] for e in json.loads((tmp / 'process' / 'manifest.json')
                                                  .read_text(encoding='utf-8'))['entries']]
            cases.append(('an entry an older update left inside the mirror is '
                          'cleared on the next run; one for the repo\'s own file '
                          'is the audit\'s to report', left == ['own'], str(left)))
            cases.append(('what the copy no longer carries is removed when it '
                          'is upstream\'s text, and kept when edited here',
                          sorted(map(str, dropped)) == ['TODO.md', 'WHATS_NEW.md',
                                                        'todo/todo-x.md', 'tools/y.py']
                          and list(map(str, kept)) == ['local/l.md']
                          and (ck.UPSTREAM / 'practices' / 'p.md').is_file()
                          and (ck.UPSTREAM / 'gotchas' / 'g.md').is_file(),
                          f'dropped={dropped} kept={kept}'))
        finally:
            ck.UPSTREAM, ck.MANIFEST = saved_up, saved_man
        import precedent_vendor_engine as pve
        cases.append(('...because the engine now vendors the tools that ran '
                      'from the copy',
                      {'checkin.py', 'practice_audit.py',
                       'precedent_local_edits.py'} <= set(pve.CONSUMER_ENGINE_FILES),
                      ''))
        cases.append(('...and the machinery for a consumer\'s own open items and '
                      'news log ships, though ours does not',
                      {'build_todo_index.py', 'todo_migrate.py',
                       'precedent_whats_new.py'} <= set(pve.CONSUMER_ENGINE_FILES)
                      and ck._in_copy('templates/TODO.md.template'), ''))
    finally:
        ck.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the catalogue copy carries what a consumer uses, and one copy '
          f'of the engine ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_update_refuses_while_a_branch_is_pinned():
    """`checkin.py update` enforces the hold its own document already states.

    spec/MIGRATING_EXISTING_INSTALLS.md's "The default-branch gotcha" has
    said since 2026-09-06, in as many words, *"Do the vendor as a one-off
    manual mirror ... not `checkin.py update`."* Nothing enforced it. The
    document mandated a procedure and the tool cheerfully did the forbidden
    thing -- the advisory-only state checkable-gets-checked exists to end,
    and the reason a session on 2026-09-07 reasoned its way to the manual
    mirror from a paragraph rather than being stopped.

    THE REFUSAL CONDITION IS THE HOLD'S OWN CONDITION, which is what makes
    it safe to add: it fires exactly while a non-default branch is pinned,
    so when precedent-beta-v01 merges and each consumer's manifest is
    repointed, it stops firing with no edit. A temporary guard that has to
    be remembered is a temporary guard that outlives its reason.

    THE FIXTURE MUST RUN THE CONSUMER'S OWN VENDORED COPY. checkin.py
    resolves ROOT from its own location's git toplevel, not the caller's
    cwd, so invoking the upstream script from a consumer directory resolves
    ROOT back to BestPractice and tests nothing. The first version of this
    fixture did exactly that: it saw a non-zero exit and scored a pass,
    while the real message was an unrelated "no upstream.commit recorded".
    A refusal is only evidence if you read WHY it refused.
    """
    import tempfile, json as _json, shutil as _shutil
    src = ROOT / 'tools' / 'checkin.py'
    if not src.exists():
        not_applicable('update refuses while a branch is pinned',
                       'tools/checkin.py is not present in this tree')
        return

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d)] + list(a),
                              capture_output=True, text=True)

    def _clone(base):
        origin, clone = base / 'origin', base / 'clone'
        (origin / 'tools').mkdir(parents=True)
        _git(origin, 'init', '-q', '-b', 'main')
        for c in (['config', 'user.email', 'harness@example.com'],
                  ['config', 'user.name', 'Harness']):
            _git(origin, *c)
        (origin / 'tools' / 'x.py').write_text('# main\n')
        _git(origin, 'add', '-A'); _git(origin, 'commit', '-qm', 'main')
        _git(origin, 'checkout', '-q', '-b', 'precedent-beta-v01')
        (origin / 'tools' / 'x.py').write_text('# beta\n')
        _git(origin, 'add', '-A'); _git(origin, 'commit', '-qm', 'beta')
        _git(origin, 'checkout', '-q', 'main')
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       capture_output=True)
        _git(clone, 'remote', 'set-head', 'origin', 'main')
        return clone

    def _consumer(base, branch):
        repo = base / 'consumer'
        (repo / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        up = {'repo': 'x/y', 'commit': 'deadbeef'}
        if branch:
            up['branch'] = branch
        (repo / 'process' / 'manifest.json').write_text(
            _json.dumps({'upstream': up, 'practices': []}), encoding='utf-8')
        _git(repo, 'init', '-q')
        _shutil.copy2(src, repo / 'process' / 'upstream' / 'tools' / 'checkin.py')
        # fixture-owns-its-state: checkin.py imports precedent_time at module
        # scope (practice: timestamps-carry-offset). Without the sibling the
        # fixture dies on the import, and every case here reads as "the tool
        # did not say what it should have" rather than "the tool never ran".
        _shutil.copy2(ROOT / 'tools' / 'precedent_time.py',
                      repo / 'process' / 'upstream' / 'tools' / 'precedent_time.py')
        _shutil.copy2(ROOT / 'tools' / 'declared_base_branch.py',
                      repo / 'process' / 'upstream' / 'tools' / 'declared_base_branch.py')
        return repo

    def _run(repo, clone, override=False, flag=False):
        env = dict(os.environ)
        env.pop('PRECEDENT_ALLOW_PINNED_UPDATE', None)
        if override:
            env['PRECEDENT_ALLOW_PINNED_UPDATE'] = '1'
        script = repo / 'process' / 'upstream' / 'tools' / 'checkin.py'
        args = [sys.executable, str(script), 'update', str(clone)]
        if flag:
            args.append('--allow-pinned')
        r = subprocess.run(args, capture_output=True, text=True, cwd=str(repo),
                           env=env, timeout=180)
        return r.returncode, r.stdout + r.stderr

    cases = []
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        clone = _clone(base / 'up')

        repo = _consumer(base / 'a', 'precedent-beta-v01')
        rc, out = _run(repo, clone)
        # Non-zero alone proves nothing -- see the docstring. Each of these
        # reads the message.
        cases.append(('a pinned install refuses `update`',
                      rc != 0 and 'is PINNED to' in out))
        cases.append(('and names the pinned branch',
                      'precedent-beta-v01' in out))
        cases.append(('and prescribes the manual mirror instead',
                      'manual mirror' in out))
        cases.append(('and says the hold lifts by itself once repointed',
                      'repointed' in out))
        cases.append(('and names its own override',
                      'PRECEDENT_ALLOW_PINNED_UPDATE=1' in out))
        # practice: control-asserts-which-failure -- the CLI flag exists
        # because at least one harness's own permission classifier refuses
        # the env-var form before checkin.py runs at all (its name reads as
        # a safety-bypass flag: ALLOW overriding a hold). The message must
        # name the flag too, not just the env var, or a session reading it
        # under such a harness has no non-refused override to reach for.
        cases.append(('and names the --allow-pinned flag',
                      '--allow-pinned' in out))

        _, out = _run(repo, clone, override=True)
        cases.append(('the env-var override gets past the hold',
                      'is PINNED to' not in out))
        _, out = _run(repo, clone, flag=True)
        cases.append(('the --allow-pinned flag also gets past the hold',
                      'is PINNED to' not in out))

        # The self-retiring cases: nothing to hold once the pin agrees with
        # the default, or when there is no pin at all.
        _, out = _run(_consumer(base / 'b', 'main'), clone)
        cases.append(('an install pinned to the DEFAULT branch is not held',
                      'is PINNED to' not in out))
        _, out = _run(_consumer(base / 'c', None), clone)
        cases.append(('an install with no pin recorded is not held',
                      'is PINNED to' not in out))

    failed = [n for n, ok in cases if not ok]
    check(f'checkin.py update refuses while a non-default branch is pinned '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_carry_check_never_counts_upstream_deletions():
    """`checkin.py record`'s carry check never reports a line upstream
    deleted itself as lost, and still reports a line upstream never had.

    Reproduced 2026-09-26 on a real consumer: 301 "LOST" lines, every one a
    line BestPractice had deleted between the two syncs. The consumer's base
    branch takes work by Promote, so it still held the PREVIOUS sync while
    the manifest named the new one; diffing that committed tree against the
    new commit alone made every upstream deletion in between look like
    dropped local work. The session could not confirm them one by one, so
    it wrote the commit by hand -- the fourth consumer update in a row to
    step around the guard, which is how a guard stops guarding.

    Four stated cases, each run through the consumer's own vendored copy
    (see check_update_refuses_while_a_branch_is_pinned for why), and each
    reading the message rather than the exit code alone:
      * the incident: committed tree one sync behind the manifest;
      * a stale committed stamp, so only upstream's own deletion history can
        explain the line -- the second of the two mechanisms;
      * a real local line upstream never wrote: still refused, still named;
      * a copy older than every stamp, never refreshed: the file's own
        upstream history says the line is upstream's.
    """
    import tempfile, json as _json, shutil as _shutil
    src = ROOT / 'tools' / 'checkin.py'
    if not src.exists():
        not_applicable('carry check never counts upstream deletions',
                       'tools/checkin.py is not present in this tree')
        return

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d)] + list(a),
                              capture_output=True, text=True)

    def _ident(d):
        _git(d, 'config', 'user.email', 'harness@example.com')
        _git(d, 'config', 'user.name', 'Harness')
        _git(d, 'config', 'commit.gpgsign', 'false')

    tools = {n: (ROOT / 'tools' / n).read_text(encoding='utf-8')
             for n in ('checkin.py', 'precedent_time.py',
                       'declared_base_branch.py')}
    # Upstream history: A, then B ADDS "gamma", then C DELETES "beta" and
    # "gamma" -- upstream's own deletions -- and adds "delta".
    history = [
        ('A', 'alpha line one\nbeta line two\n'),
        ('B', 'alpha line one\nbeta line two\ngamma line three\n'),
        ('C', 'alpha line one\ndelta line four\n'),
    ]

    def _upstream(base):
        up = base / 'upstream'
        (up / 'tools').mkdir(parents=True)
        _git(up, 'init', '-q', '-b', 'main'); _ident(up)
        shas = {}
        for name, text in history:
            (up / 'notes.md').write_text(text, encoding='utf-8')
            for n, t in tools.items():
                (up / 'tools' / n).write_text(t, encoding='utf-8')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', name)
            shas[name] = _git(up, 'rev-parse', 'HEAD').stdout.strip()
        clone = base / 'clone'
        subprocess.run(['git', 'clone', '-q', str(up), str(clone)],
                       capture_output=True)
        return clone, shas

    def _consumer(base, clone, committed_at, committed_stamp, working_commit,
                  extra_line=''):
        """A consumer whose origin/main holds the vendored tree mirrored
        from `committed_at` (plus `extra_line`, a local addition) with a
        committed manifest stamped `committed_stamp`, and whose working
        tree has since been updated to the clone's HEAD with the manifest
        naming `working_commit`."""
        origin, repo = base / 'origin.git', base / 'consumer'
        repo.mkdir(parents=True)
        _git(base, 'init', '-q', '--bare', '-b', 'main', str(origin))
        _git(repo, 'init', '-q', '-b', 'main'); _ident(repo)
        _git(repo, 'remote', 'add', 'origin', str(origin))
        vend = repo / 'process' / 'upstream'

        def _mirror(ref):
            if vend.exists():
                _shutil.rmtree(vend)
            (vend / 'tools').mkdir(parents=True)
            for rel in ('notes.md', 'tools/checkin.py', 'tools/precedent_time.py',
                        'tools/declared_base_branch.py'):
                (vend / rel).write_text(_git(clone, 'show', f'{ref}:{rel}').stdout,
                                        encoding='utf-8')

        def _manifest(commit):
            (repo / 'process' / 'manifest.json').write_text(_json.dumps(
                {'upstream': {'repo': 'x/y', 'branch': 'main', 'commit': commit,
                              'synced_from': commit}, 'practices': []}),
                encoding='utf-8')

        (repo / 'precedent.json').write_text('{"base_branch": "main"}\n',
                                             encoding='utf-8')
        _mirror(committed_at)
        if extra_line:
            with (vend / 'notes.md').open('a', encoding='utf-8') as fh:
                fh.write(extra_line + '\n')
        _manifest(committed_stamp)
        _git(repo, 'add', '-A'); _git(repo, 'commit', '-qm', 'vendored')
        _git(repo, 'push', '-q', 'origin', 'main')
        # The update, landed in the working tree but not on origin/main yet.
        _mirror('HEAD')
        _manifest(working_commit)
        return repo

    def _record(repo, clone):
        script = repo / 'process' / 'upstream' / 'tools' / 'checkin.py'
        r = subprocess.run([sys.executable, str(script), 'record', str(clone)],
                           capture_output=True, text=True, cwd=str(repo),
                           timeout=180)
        return r.returncode, r.stdout + r.stderr

    cases = []
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        clone, sha = _upstream(base / 'up')

        # 1. The incident: origin/main still holds the sync from B, the
        #    manifest already names C.
        rc, out = _record(_consumer(base / 'one', clone, sha['B'], sha['B'],
                                    sha['C']), clone)
        cases.append(('a committed tree one sync behind the manifest records '
                      'cleanly', rc == 0 and 'checkin record OK' in out))
        cases.append(('and names no upstream deletion as LOST',
                      'LOST' not in out and 'gamma' not in out))

        # 2. A committed tree mirrored from B but stamped A (a hand-written
        #    stamp gone stale). "gamma" is in no base's tree; only upstream's
        #    own deletion of it between A and C explains its absence.
        rc, out = _record(_consumer(base / 'two', clone, sha['B'], sha['A'],
                                    sha['A']), clone)
        cases.append(('a stale committed stamp still records cleanly',
                      rc == 0 and 'checkin record OK' in out))
        cases.append(('and says it set aside upstream\'s own deletions',
                      "upstream's own deletions" in out
                      or "upstream's own text, including its own deletions" in out))

        # 3. A real loss: a line nobody upstream ever wrote.
        rc, out = _record(_consumer(base / 'three', clone, sha['B'], sha['B'],
                                    sha['C'], extra_line='a local line upstream never had'),
                          clone)
        cases.append(('a line upstream never wrote is still refused',
                      rc != 0 and 'MISSING from the landed upstream' in out))
        cases.append(('and is the one line named LOST',
                      'a local line upstream never had' in out
                      and 'gamma line three' not in out
                      and 'beta line two' not in out))

        # 4. A copy never refreshed: the committed tree is upstream's A,
        #    but every stamp names C, so "beta" (deleted at B) is in no
        #    base and in no deletion after one. Only the file's own history
        #    says upstream wrote it (2026-09-30, a real consumer, 75 files).
        rc, out = _record(_consumer(base / 'four', clone, sha['A'], sha['C'],
                                    sha['C']), clone)
        cases.append(('a copy older than every stamp records cleanly',
                      rc == 0 and 'checkin record OK' in out and 'beta' not in out))
        cases.append(('and says the lines are an earlier upstream version',
                      'earlier upstream version' in out))

    failed = [n for n, ok in cases if not ok]
    check(f'checkin.py record never counts upstream\'s own deletions as lost '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_install_names_every_not_vendored_dir():
    """INSTALL.md §1 step 1 names everything checkin.py refuses to vendor --
    every NOT_VENDORED directory, and every NOT_VENDORED_ROOT_FILES file.

    These are two halves of one rule kept in two files, which is the shape
    that drifts. tools/checkin.py's NOT_VENDORED/NOT_VENDORED_ROOT_FILES are
    what the tooling acts on; INSTALL.md step 1 is what a person copying the
    tree by hand reads. An entry added to one and not the other means either
    a consumer hand-copies a tree the tooling then reports as drifted, or the
    prose promises an exclusion nothing performs.

    Found when philosophy/ was excluded on 2026-09-14 and nothing would have
    caught the doc being left behind (practice: checkable-gets-checked).
    Name-only: the paragraph's wording is nobody's business but its author's.
    A directory is matched as `name/` (so `spec` inside `specification` can't
    false-positive); a root file has no such delimiter available, so it is
    matched bare -- AGENTS.md/CLAUDE.md are distinctive enough that a bare
    substring match is not a meaningful false-positive risk in a 2000-char
    window, the same tradeoff `not_vendored_share()`'s own comment accepts.
    """
    install = ROOT / 'INSTALL.md'
    if not install.is_file():
        not_applicable('INSTALL.md names every not-vendored directory',
                       'INSTALL.md does not exist -- not a pass')
        return
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        import checkin as _checkin
        excluded_dirs = set(_checkin.NOT_VENDORED)
        excluded_files = set(_checkin.NOT_VENDORED_ROOT_FILES)
    except Exception as exc:                       # pragma: no cover
        not_applicable('INSTALL.md names every not-vendored directory',
                       f'could not read checkin.NOT_VENDORED: {exc}')
        return
    text = install.read_text(encoding='utf-8')
    # The step is the one that says "Skip"; scoping to it stops an incidental
    # mention elsewhere in a 1000-line document from passing this.
    i = text.find('**Skip ')
    step = text[i:i + 2000] if i != -1 else ''
    missing = sorted(d for d in excluded_dirs if f'{d}/' not in step) + \
        sorted(f for f in excluded_files if f not in step)
    total = len(excluded_dirs) + len(excluded_files)
    check(f'INSTALL.md §1 step 1 names every not-vendored directory/file '
          f'({total} excluded)',
          not missing,
          f'not named in the vendor step: {", ".join(missing)}' if missing
          else '')


def check_checkin_update_never_mutates_the_clone():
    """`checkin.py update <clone>` reads the clone; it never moves its HEAD.

    Its sibling precedent_vendor_engine.py makes that guarantee explicitly
    and is asserted on it here. checkin.py made no such promise and broke it:
    update() opened with `git checkout <default-branch>` and `git pull`
    INSIDE the caller's clone -- a repository passed only as a SOURCE.

    2026-09-06, found by being on the receiving end. A session running the
    command from a consumer repo had its BestPractice checkout silently
    moved off precedent-beta-v01 onto main, mid-session; it noticed only
    because a directory it expected had vanished from the working tree. The
    command had already FAILED its own guard by then, so the mutation was
    pure collateral -- and on a dirty tree the checkout would have failed
    and left the pull half-applied instead.

    Two properties, since the same call site carried two bugs: the clone is
    untouched, and the branch mirrored is the one the MANIFEST records, not
    the clone's configured default. Every consumer tracks
    precedent-beta-v01 today while main is still the default, so reading the
    default would have mirrored main over a tree vendored from the beta
    branch -- a wholesale revert dressed as an update.
    """
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='checkin-update-'))
    try:
        # A source clone with two branches, whose default is NOT the branch
        # the fixture consumer tracks -- the exact shape that made the second
        # bug invisible.
        src = tmp / 'source'
        src.mkdir()
        g = lambda *a: subprocess.run(['git', '-C', str(src), *a],
                                      capture_output=True, text=True)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 't@t'); g('config', 'user.name', 't')
        (src / 'marker.txt').write_text('from main\n')
        g('add', '-A'); g('commit', '-qm', 'main content')
        g('checkout', '-qb', 'precedent-beta-v01')
        (src / 'marker.txt').write_text('from beta\n')
        g('add', '-A'); g('commit', '-qm', 'beta content')
        # The clone rests on a THIRD branch, deliberately. Left on `main` it
        # cannot detect record()'s old `checkout <default-branch>`, because
        # checking out the branch you are already on is a no-op -- the first
        # version of this fixture sat on `main` and its negative control
        # passed against the bug. Left on `precedent-beta-v01` it would miss
        # update()'s checkout for the mirror image of the same reason. From
        # `scratch`, a checkout of either one moves HEAD and is caught.
        g('checkout', '-qb', 'scratch')
        (src / 'marker.txt').write_text('scratch, not a branch anything tracks\n')
        g('add', '-A'); g('commit', '-qm', 'scratch content')

        consumer = tmp / 'consumer'
        (consumer / 'process' / 'upstream').mkdir(parents=True)
        (consumer / 'process' / 'upstream' / 'marker.txt').write_text('from beta\n')
        beta = g('rev-parse', 'precedent-beta-v01').stdout.strip()
        (consumer / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': str(src), 'vendored_at': 'process/upstream',
                         'branch': 'precedent-beta-v01', 'commit': beta},
            'entries': []}) + '\n')
        # The real vendored layout: checkin.py derives ROOT from its own
        # location as HERE.parents[3], so it has to sit at
        # process/upstream/tools/ or it resolves the manifest somewhere else
        # entirely.
        (consumer / 'process' / 'upstream' / 'tools').mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'tools' / 'checkin.py',
                     consumer / 'process' / 'upstream' / 'tools' / 'checkin.py')
        # checkin.py imports it at module scope (practice:
        # timestamps-carry-offset). The real vendored tree carries it --
        # it is in precedent_vendor_engine.py's ENGINE_FILES -- so this
        # minimal mock of that tree has to as well, or it tests an install
        # shape that never ships.
        shutil.copy2(ROOT / 'tools' / 'precedent_time.py',
                     consumer / 'process' / 'upstream' / 'tools' / 'precedent_time.py')
        shutil.copy2(ROOT / 'tools' / 'declared_base_branch.py',
                     consumer / 'process' / 'upstream' / 'tools' / 'declared_base_branch.py')
        # push hands its work to send (2026-09-29); the real vendored tree
        # carries both, since the mirror brings the whole tools/ at once.
        shutil.copy2(ROOT / 'tools' / 'precedent_local_edits.py',
                     consumer / 'process' / 'upstream' / 'tools' / 'precedent_local_edits.py')

        def clone_state():
            return tuple(g(*a).stdout.strip() for a in (
                ('rev-parse', 'HEAD'), ('rev-parse', '--abbrev-ref', 'HEAD'),
                ('status', '--porcelain')))

        before = clone_state()
        r = subprocess.run(
            [sys.executable,
             str(consumer / 'process' / 'upstream' / 'tools' / 'checkin.py'),
             'update', str(src)],
            capture_output=True, text=True, cwd=str(consumer))
        after = clone_state()
        out = r.stdout + r.stderr

        check('checkin.py update leaves the source clone\'s HEAD, branch and '
              'working tree exactly as they were',
              before == after, f'before={before} after={after}\n{out}')
        check('checkin.py update mirrors the branch the MANIFEST records, '
              'not the clone\'s configured default',
              'precedent-beta-v01' in out and
              (consumer / 'process' / 'upstream' / 'marker.txt'
               ).read_text() == 'from beta\n',
              out)

        # record() and push() carried the SAME two bugs, and the first fix
        # reached only update() -- found on the next pass by grepping for the
        # other call sites rather than assuming one fix covered the family.
        # record() is the one that also checked the clone out.
        for sub in ('record', 'push'):
            before2 = clone_state()
            args = [sys.executable,
                    str(consumer / 'process' / 'upstream' / 'tools' / 'checkin.py'),
                    sub, str(src)]
            if sub == 'record':
                args += ['--note', 'harness fixture']
            r2 = subprocess.run(args, capture_output=True, text=True,
                                cwd=str(consumer))
            after2 = clone_state()
            check(f'checkin.py {sub} leaves the source clone\'s HEAD, branch '
                  f'and working tree exactly as they were',
                  before2 == after2,
                  f'before={before2} after={after2}\n{r2.stdout}{r2.stderr}')
            check(f'checkin.py {sub} resolves the branch the MANIFEST '
                  f'records, not the clone\'s configured default',
                  'main' not in (r2.stdout + r2.stderr).replace(
                      'precedent-beta-v01', ''),
                  r2.stdout + r2.stderr)

        # `fresh` is the most-run of the family -- tools/bootstrap.sh calls it
        # at every session start in every consumer -- and it reached the
        # remote a different way, `ls-remote <repo> HEAD`, which resolves the
        # remote's default branch. On a pinned consumer that compared the
        # pinned branch's recorded commit against an unrelated lineage and
        # printed "upstream has moved" every single session, forever.
        # `main` here is deliberately AHEAD of the recorded beta commit, so a
        # default-branch resolution cannot help but report movement.
        r3 = subprocess.run(
            [sys.executable,
             str(consumer / 'process' / 'upstream' / 'tools' / 'checkin.py'),
             'fresh'],
            capture_output=True, text=True, cwd=str(consumer))
        out3 = r3.stdout + r3.stderr
        check('checkin.py fresh compares against the branch the MANIFEST '
              'records, so a pinned install is not told "upstream has moved" '
              'every session by an unrelated lineage',
              'has moved' not in out3, out3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_checkin_ignores_files_git_does_not_track_in_the_clone():
    """`checkin.py` status/record compare against what is COMMITTED on the
    pinned branch, and push never deletes a file git does not track.

    2026-09-27, a real consumer's Update Vendors: `record` refused because
    the BestPractice clone held `.claude/settings.local.json` -- gitignored,
    written there by commit-identity.sh at session start to carry the
    person's TZ. record walked the clone's FOLDER, so a per-machine file read
    as "the clone has a file the vendored tree lacks". The session deleted
    it and re-recorded; the next session start wrote it straight back.
    `push` carried the same walk the other way and would have unlinked it,
    along with `.precedent/` and any uncommitted file a person had there.

    The clone also rests on a scratch branch whose commit is NOT what
    landed, because record wrote the clone's HEAD into the manifest: the
    upstream commit it stamps must be origin/<pinned branch>, whatever the
    clone happens to have checked out.

    Negative control (practice: control-asserts-which-failure): run against
    the checkin.py before this fix, status reports the three stray files as
    differing, record exits with "is not identical to the vendored tree",
    and push unlinks all three -- measured 2026-09-27 when this was written.
    """
    import tempfile, json as _json
    if not (ROOT / 'tools' / 'checkin.py').exists():
        not_applicable('checkin.py ignores files git does not track in the '
                       'clone', 'tools/checkin.py is not present in this tree')
        return

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d)] + list(a),
                              capture_output=True, text=True)

    def _ident(d):
        _git(d, 'config', 'user.email', 'harness@example.com')
        _git(d, 'config', 'user.name', 'Harness')
        _git(d, 'config', 'commit.gpgsign', 'false')

    # Under practices/: the catalogue copy is an allowlist since
    # 2026-09-30, and a top-level file of no known kind stays home.
    shipped = {
        'practices/marker.txt': 'upstream content\n',
        'practices/retired.txt': 'upstream stops vendoring this in the push case\n',
        '.gitignore': '.claude/settings.local.json\n.precedent/\n',
        'tools/checkin.py': (ROOT / 'tools' / 'checkin.py').read_text(encoding='utf-8'),
        'tools/precedent_time.py': (ROOT / 'tools' / 'precedent_time.py'
                                    ).read_text(encoding='utf-8'),
        'tools/declared_base_branch.py': (ROOT / 'tools' / 'declared_base_branch.py'
                                          ).read_text(encoding='utf-8'),
        # push hands the work to send (2026-09-29), from the same directory.
        'tools/precedent_local_edits.py': (ROOT / 'tools' / 'precedent_local_edits.py'
                                           ).read_text(encoding='utf-8'),
        # push() runs the vendored scrub first; this fixture is about the
        # mirror, so the scrub is a stub that passes.
        'tools/practice_audit.py': 'raise SystemExit(0)\n',
    }
    # What a SessionStart hook writes into every clone it runs in, plus a
    # person's own uncommitted file. None of it is upstream content.
    stray = {
        '.claude/settings.local.json': '{"env": {"TZ": "America/New_York"}}\n',
        '.precedent/SESSION_PRACTICES.md': 'practices in force this session\n',
        'notes-in-progress.txt': 'somebody\'s uncommitted work\n',
    }

    def _write(root, files):
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding='utf-8')

    cases = []
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        up = base / 'up'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main'); _ident(up)
        _write(up, shipped)
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'upstream')

        clone = base / 'clone'
        subprocess.run(['git', 'clone', '-q', str(up), str(clone)],
                       capture_output=True)
        _ident(clone)
        landed = _git(clone, 'rev-parse', 'origin/main').stdout.strip()
        _git(clone, 'checkout', '-qb', 'scratch')
        (clone / 'practices/marker.txt').write_text('scratch, not what landed\n',
                                          encoding='utf-8')
        _git(clone, 'commit', '-qam', 'scratch')
        _write(clone, stray)

        # The consumer is a repo of its own, so checkin.py resolves ROOT to
        # it and not to whatever repository the temp directory sits in
        # (practice: fixture-owns-its-state).
        consumer = base / 'consumer'
        vend = consumer / 'process' / 'upstream'
        vend.mkdir(parents=True)
        _git(consumer, 'init', '-q', '-b', 'main'); _ident(consumer)
        _write(vend, shipped)
        manifest = consumer / 'process' / 'manifest.json'
        manifest.write_text(_json.dumps({'upstream': {
            'repo': 'x/y', 'branch': 'main', 'commit': landed,
            'synced_from': landed}, 'entries': []}) + '\n', encoding='utf-8')

        def run(sub, *extra):
            r = subprocess.run([sys.executable, str(vend / 'tools' / 'checkin.py'),
                                sub, str(clone), *extra],
                               capture_output=True, text=True, cwd=str(consumer),
                               timeout=180)
            return r.returncode, r.stdout + r.stderr

        rc, out = run('status')
        cases.append(('status counts no gitignored or uncommitted clone file '
                      'as a difference', rc == 0 and ' 0 file(s) differ' in out,
                      out))

        rc, out = run('record', '--note', 'harness fixture')
        recorded = _json.loads(manifest.read_text(encoding='utf-8')
                               )['upstream']['commit']
        cases.append(('record passes with the stray files in the clone',
                      rc == 0 and 'checkin record OK' in out, out))
        cases.append(('record stamps origin/<pinned branch>, not the clone\'s '
                      'HEAD on another branch', recorded == landed,
                      f'recorded={recorded} landed={landed}'))

        # push: this repo drops retired.txt. Since 2026-09-29 push hands the
        # work to precedent_local_edits.py send, which builds a branch in a
        # worktree of its own -- so the clone's working tree, tracked files
        # and stray files alike, is never touched, whatever happens next.
        _git(clone, 'checkout', '-q', 'main')
        (vend / 'practices/retired.txt').unlink()
        rc, out = run('push')
        cases.append(('push hands the work to send, which asks what went wrong '
                      'before doing anything', rc == 2
                      and 'precedent_local_edits send REFUSED: --why is required' in out,
                      out))
        survived = [rel for rel, text in stray.items()
                    if (clone / rel).is_file()
                    and (clone / rel).read_text(encoding='utf-8') == text]
        cases.append(('push leaves the clone\'s working tree untouched: every '
                      'file git does not track, and the tracked file this repo '
                      'dropped', len(survived) == len(stray)
                      and (clone / 'practices/retired.txt').is_file(),
                      f'survived={survived}\n{out}'))

    failed = [f'{n}: {d[:400]}' for n, ok, d in cases if not ok]
    check(f'checkin.py ignores files git does not track in the source clone '
          f'({len(cases)} stated cases)', not failed, '\n'.join(failed))


def check_one_upstream_move_is_said_once_at_session_start():
    """Session start says one upstream move once.

    2026-10-10, a consumer's session start: one BestPractice move printed
    "NOTICE: BestPractice upstream has moved", "ENGINE BEHIND UPSTREAM" and
    "BEHIND UPSTREAM" for the same two commits. The freshness notice names
    the engine and the catalogue in one line when they are behind at the
    same commit (checked in check_freshness_covers_every_declared_source);
    the bootstrap template runs checkin.py fresh only where that notice
    cannot run. Alongside: the citations step of Update Vendors says how a
    dated record stops being listed (record_paths), the same day."""
    name = 'one upstream move is said once at session start'
    text = (ROOT / 'templates' / 'bootstrap.sh').read_text(encoding='utf-8')
    block = text[text.index('for _ck in tools/checkin.py'):]
    block = block[:block.index('done')]
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as _pu
    finally:
        sys.path.pop(0)
    hint = _pu.record_paths_hint(['process/PRECEDENT_MIGRATION.md:12 (`go-merge`, renamed)',
                                  'tools/x.py:3'])
    gate_src = (ROOT / 'tools' / 'precedent_gate.py').read_text(encoding='utf-8')
    cases = [
        # The note itself left the gate for the ladder set's own tool
        # (8d6a21c9, 2026-10-17), so the gate must carry no count at all.
        ('the reply gate gives no stale-branch count of its own: it reads '
         'without a fetch, the page after one (2026-10-10: 13 met 16)',
         'branch(es) "\n' not in gate_src and 'f"across {len(_groups)}' not in gate_src
         and 'precedent_stale_branches' not in gate_src),
        ('checkin.py fresh is skipped where the freshness notice runs',
         '! -f tools/precedent_engine_freshness.py' in block),
        ('the citations step names record_paths for a Markdown file it lists',
         'record_paths' in hint and 'process/PRECEDENT_MIGRATION.md' in hint
         and 'tools/x.py' not in hint),
        ('...and says nothing when there is no Markdown file to read',
         _pu.record_paths_hint(['tools/x.py:3']) == ''),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_engine_unpacks_tars_in_one_place():
    """Every tar the engine unpacks goes through checkin.extract_archive,
    which passes the 'data' filter; it unpacks a real git archive with
    Python's tar warnings made errors.

    WHY. A consuming repository's Update Vendors, 2026-10-12: three
    unfiltered extractall calls in checkin.py printed Python 3.12's
    DeprecationWarning, while precedent_update.py carried its own two
    copies of the guard. One helper means a new call site has nothing to
    remember. Planted: the scan finds an extractall written outside the
    helper; CONTROL: the tools as they stand have none."""
    import ast
    import tempfile
    import warnings
    sys.path.insert(0, str(ROOT / 'tools'))
    import checkin as _ck
    cases = []

    def outside_helper(src):
        tree = ast.parse(src)
        helper = [range(n.lineno, n.end_lineno + 1) for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == 'extract_archive']
        return [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == 'extractall'
                and not any(n.lineno in r for r in helper)]

    planted = 'import tarfile\ndef f(t, d):\n    tarfile.open(t).extractall(d)\n'
    cases.append(('the scan finds an extractall outside the helper',
                  outside_helper(planted) == [3], ''))
    stray = []
    for py in sorted((ROOT / 'tools').glob('*.py')):
        if py.name == 'verify_harness.py':
            continue
        try:
            src = py.read_text(encoding='utf-8')
            # Only a file naming extractall can call it: the rest are never
            # parsed, a handful left of 140.
            hits = outside_helper(src) if 'extractall' in src else []
        except SyntaxError:
            continue
        stray += [f'{py.name}:{n}' for n in hits]
    cases.append(('CONTROL: no tool unpacks a tar outside the helper',
                  not stray, ', '.join(stray)))
    tar = subprocess.run(['git', '-C', str(ROOT), 'archive', 'HEAD', 'README.md'],
                         capture_output=True).stdout
    with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        try:
            _ck.extract_archive(tar, td)
            ok, why = (pathlib.Path(td) / 'README.md').is_file(), ''
        except DeprecationWarning as e:
            ok, why = False, str(e)
    cases.append(('the helper unpacks a git archive without a warning', ok, why))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'the engine unpacks tars in one place, filtered ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_hosted_sessions_resolve_without_attaching_a_repo():
    """Two ways a hosted session resolves its sources with no human in the
    loop, added together on 2026-09-29 after a consumer's sessions were told
    at start to attach a private shared set by hand (the person saw an
    unexplained permission prompt and refused it) and printed an
    individual-set warning above every reply for a person who had declined
    one.

    1. With no sign of an individual set in the environment (no token,
       base URL, repo name or clone), unresolved_private_sources expects
       none; each sign on its own restores the expectation.
    2. checkin.py --source, with the consumer's `vendor_practices` opt-in,
       mirrors the set's practices/ and precedent-source.json beside its
       code; without the opt-in it still mirrors code only.
    3. _stamp_synced_from writes to the manifest of the source being
       checked in, never to the universal manifest."""
    import shutil, tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='hosted-no-attach-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'precedent.json').write_text('{"sources": []}', encoding='utf-8')
        home = tmp / 'home'
        home.mkdir()
        base = {'HOME': str(home), 'CLAUDE_CODE_REMOTE': 'true',
                'PRECEDENT_USER_CONFIG': str(home / 'absent.json')}
        none_seen = psc.unresolved_private_sources(repo, env=dict(base))
        cases.append(('with no user config and no sign of an individual set, '
                      'nothing is expected', none_seen == [], repr(none_seen)))
        for var in psc.INDIVIDUAL_SIGNAL_ENVS:
            seen = psc.unresolved_private_sources(repo, env={**base, var: 'x'})
            cases.append((f'{var} set is a sign of an individual set, so its '
                          f'absence is reported',
                          [u[0] for u in seen] == ['individual'], repr(seen)))
        clone = home / 'precedent-individual' / 'practices'
        clone.mkdir(parents=True)
        seen = psc.unresolved_private_sources(repo, env=dict(base))
        cases.append(('an individual clone on disk with no config is a sign '
                      'too, so the missing config is reported',
                      [u[0] for u in seen] == ['individual'], repr(seen)))

        import checkin
        for opted, want in ((False, {'filing'}),
                            (True, {'filing', 'practices',
                                    'precedent-source.json'})):
            importlib.reload(checkin)
            clone = tmp / f'set-{opted}'
            (clone / 'filing').mkdir(parents=True)
            (clone / 'practices').mkdir()
            (clone / 'filing' / 'engine.py').write_text('x = 1\n')
            (clone / 'practices' / 'rule.md').write_text('rule\n')
            (clone / 'precedent-source.json').write_text(json.dumps(
                {'name': 'fixture-set', 'level': 'shared', 'code': ['filing']}))
            host = tmp / f'host-{opted}'
            (host / 'process').mkdir(parents=True)
            checkin.ROOT = host
            checkin._select_source('fixture-set')
            checkin.MANIFEST.write_text(json.dumps(
                {'upstream': {'vendor_practices': True} if opted else {}}))
            checkin._bind_source(clone)
            got = {f.parts[0] for f in checkin._files(clone)}
            cases.append((f'vendor_practices={opted}: the mirror is '
                          f'{sorted(want)}', got == want, repr(sorted(got))))
            (host / 'process' / 'manifest.json').write_text('{}')
            checkin._stamp_synced_from('abc1234def')
            own = json.loads(checkin.MANIFEST.read_text())
            uni = json.loads((host / 'process' / 'manifest.json').read_text())
            cases.append((f'vendor_practices={opted}: synced_from lands in the '
                          f"set's own manifest, not the universal one",
                          own.get('upstream', {}).get('synced_from') == 'abc1234def'
                          and 'upstream' not in uni, f'{own} / {uni}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # _select_source/_bind_source rebind checkin's module state (ROOT,
        # CODE_DIRS); a later case in this process must get a fresh module.
        if 'checkin' in sys.modules:
            importlib.reload(sys.modules['checkin'])
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a hosted session resolves its sources without attaching a repo by '
          f'hand ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_copied_in_set_carries_its_reply_rules():
    """A whole copy of a shared set carries the set's reply_check.json (and
    close_detect.json), so the set's reply-gate requirements bind where the
    copy is the source; a copy taken for its exports alone does not, since
    none of its rules are in force there.

    THE INCIDENT (2026-11-01). A voice repository copies the ladder set in
    at process/precedent-shared-ladder/. The copy held practices/,
    precedent-source.json and the files its rules name, never
    reply_check.json, and the reply check reads each source's file from the
    source's path -- the copy. Measured in a copy of that repository with no
    individual set: universal's requirements only, none of the set's six,
    and no note saying so. The fixture owns its user config, so this
    machine's sets never resolve into it (practice: fixture-owns-its-state)."""
    import shutil, tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='copied-in-reply-'))
    cases = []
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t',
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
    (tmp / 'no-config.json').write_text('{}', encoding='utf-8')

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=env,
                              capture_output=True, text=True)

    try:
        origin = tmp / 'zz-reply.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=env, check=True)
        clone = tmp / 'zz-reply'
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       env=env, capture_output=True, check=True)
        (clone / 'practices').mkdir()
        (clone / 'practices' / 'zz-rule.md').write_text(
            '---\nslug: zz-rule\n---\n# zz\n\n## Rule\n\nx\n', encoding='utf-8')
        (clone / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-reply', 'level': 'shared', 'visibility': 'public',
             'exports': ['RULES.md']}), encoding='utf-8')
        (clone / 'RULES.md').write_text('rules\n', encoding='utf-8')
        (clone / 'reply_check.json').write_text(json.dumps(
            [{'id': 'zz-reply-says-zz', 'require_any': ['ZZ-MARKER'],
              'why': 'fixture'}]), encoding='utf-8')
        (clone / 'close_detect.json').write_text(json.dumps(
            [{'id': 'zz-close', 'why': 'fixture'}]), encoding='utf-8')
        git(clone, 'checkout', '-q', '-b', 'main')
        git(clone, 'add', '-A')
        git(clone, 'commit', '-qm', 'one')
        git(clone, 'push', '-q', 'origin', 'main')

        def host(hname, **entry):
            h = tmp / hname
            (h / 'process').mkdir(parents=True)
            (h / 'precedent.json').write_text(json.dumps({
                'format_version': 1, 'visibility': 'private', 'sources': [
                    {'name': 'zz-reply', 'level': 'shared',
                     'path': 'process/zz-reply', 'vendored': True, **entry}]}),
                encoding='utf-8')
            (h / 'process' / 'manifest_zz-reply.json').write_text(json.dumps(
                {'upstream': {'branch': 'main'}}), encoding='utf-8')
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(h)],
                           env=env, check=True)
            git(h, 'add', '-A')
            git(h, 'commit', '-qm', 'init')
            r = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'checkin.py'), '--source',
                 'zz-reply', '--repo', str(h), 'update', str(clone), '--force'],
                env=env, capture_output=True, text=True)
            return h, r

        whole, r1 = host('whole')
        copy = whole / 'process' / 'zz-reply'
        cases.append(('THE CASE: a whole copy carries the set\'s reply_check.json',
                      (copy / 'reply_check.json').is_file(),
                      failure_detail(r1.stdout + r1.stderr, 300)))
        cases.append(('...and its close_detect.json',
                      (copy / 'close_detect.json').is_file(), ''))
        real_env = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = env['PRECEDENT_USER_CONFIG']
        try:
            import precedent_reply_check as rc
            importlib.reload(rc)
            reqs, _notes = rc.declared_requirements(str(whole))
        finally:
            if real_env is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = real_env
        cases.append(('THE CASE: the reply check then holds the copy\'s '
                      'requirement, from shared/zz-reply',
                      any(r.get('id') == 'zz-reply-says-zz'
                          and r.get('_source') == 'shared/zz-reply'
                          for r in reqs),
                      repr([(r.get('_source'), r.get('id')) for r in reqs])))
        only, r2 = host('only', exports_only=True)
        ocopy = only / 'process' / 'zz-reply'
        cases.append(('CONTROL: a copy taken for its exports alone takes the '
                      'export and no reply_check.json -- none of its rules '
                      'are in force there',
                      (ocopy / 'RULES.md').is_file()
                      and not (ocopy / 'reply_check.json').exists(),
                      failure_detail(r2.stdout + r2.stderr, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a whole copy of a set carries its reply and close-detect rules '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_copied_in_shared_sets():
    """A shared set copied into a repository, the way the universal catalogue
    is at process/upstream/ (spec/VENDORED_SHARED_SETS.md, 2026-10-19). The
    plan: attached sets kept failing to arrive at session start; a copy has
    nothing to arrive.

    1. checkin.py --source mirrors a set declared `"vendored": true` --
       its practices and precedent-source.json, even with no `code` -- and
       record() writes vendored_at and repo, so the guard and the freshness
       line read process/<name>/ and the set's own origin.
    2. The hand-edit guard: the copy is clean after record, drifted once a
       rule in it is edited (the negative control).
    3. The resolver loads the copy with no sibling clone; a person who
       brings the same set gets the repository's copy, once.
    4. declared_source_paths() leaves the copy and the same-named brought
       set out (they are this checkout); vendored_source_paths() lists it.
    5. A private set is refused into a repository not declared private, and
       copied into one that is; the tree check says the same.
    6. The freshness line says BEHIND UPSTREAM once the set's origin moves.
    7. A missing copy is reported as Update Vendors' to make, never as a
       set to attach; session start does not fetch a set the repository
       copies in."""
    import shutil, tempfile, importlib
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='copied-in-sets-'))
    cases = []
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t',
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=env,
                              capture_output=True, text=True)

    def make_set(name, visibility):
        origin = tmp / f'{name}.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=env, check=True)
        clone = tmp / name
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       env=env, capture_output=True, check=True)
        (clone / 'practices').mkdir()
        (clone / 'practices' / 'zz-rule.md').write_text(
            '---\nslug: zz-rule\n---\n# zz\n\n## Rule\n\nx\n',
            encoding='utf-8')
        (clone / 'precedent-source.json').write_text(json.dumps(
            {'name': name, 'level': 'shared', 'visibility': visibility}),
            encoding='utf-8')
        git(clone, 'checkout', '-q', '-b', 'main')
        git(clone, 'add', '-A')
        git(clone, 'commit', '-qm', 'one')
        git(clone, 'push', '-q', 'origin', 'main')
        return clone

    def make_host(hname, name, visibility=None):
        host = tmp / hname
        (host / 'process').mkdir(parents=True)
        cfg = {'format_version': 1, 'sources': [
            {'name': name, 'level': 'shared', 'path': f'process/{name}',
             'vendored': True}]}
        if visibility:
            cfg['visibility'] = visibility
        (host / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        (host / 'process' / f'manifest_{name}.json').write_text(json.dumps(
            {'upstream': {'branch': 'main'}}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(host)],
                       env=env, check=True)
        git(host, 'add', '-A')
        git(host, 'commit', '-qm', 'init')
        return host

    def checkin_run(host, name, clone, verb, *flags):
        return subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'checkin.py'), '--source',
             name, '--repo', str(host), verb, str(clone), *flags],
            env=env, capture_output=True, text=True)

    try:
        import precedent_resolve as pr
        import checkin
        importlib.reload(checkin)
        pub = make_set('zz-set', 'public')
        host = make_host('host', 'zz-set')
        r1 = checkin_run(host, 'zz-set', pub, 'update', '--force')
        r2 = checkin_run(host, 'zz-set', pub, 'record')
        copy = host / 'process' / 'zz-set'
        got = sorted(f.relative_to(copy).as_posix() for f in copy.rglob('*')
                     if f.is_file())
        cases.append(('a set declared "vendored" with no code is copied: its '
                      'practices and precedent-source.json',
                      r1.returncode == 0 and r2.returncode == 0
                      and got == ['practices/zz-rule.md', 'precedent-source.json'],
                      f'{got} / {failure_detail(r1.stdout, 300)}{failure_detail(r1.stderr, 300)} / '
                      f'{failure_detail(r2.stdout, 300)}{failure_detail(r2.stderr, 300)}'))
        up = json.loads((host / 'process' / 'manifest_zz-set.json')
                        .read_text(encoding='utf-8')).get('upstream', {})
        cases.append(('record() writes where the copy lives and where it '
                      'came from', up.get('vendored_at') == 'process/zz-set'
                      and up.get('repo', '').endswith('zz-set.git'), repr(up)))

        if not (copy / 'practices' / 'zz-rule.md').is_file():
            raise RuntimeError('no copy was made, so nothing after it can be '
                               'tested')
        clean = checkin.copy_drift(host)
        rule = copy / 'practices' / 'zz-rule.md'
        kept = rule.read_text(encoding='utf-8')
        rule.write_text('edited in place\n', encoding='utf-8')
        edited = checkin.copy_drift(host)
        rule.write_text(kept, encoding='utf-8')
        cases.append(('the guard finds the copy clean after record',
                      [d[2] for d in clean] == ['ok']
                      and clean[0][1] == 'process/zz-set', repr(clean)))
        cases.append(('NEGATIVE CONTROL: the guard finds a rule edited in the '
                      'copy', [d[2] for d in edited] == ['drifted'], repr(edited)))

        srcs = pr.load_config(str(host), user_config=str(tmp / 'no-config.json'))
        mine = [s for s in srcs if s['name'] == 'zz-set']
        cases.append(('the copy resolves with no sibling clone',
                      len(mine) == 1 and mine[0].get('vendored') is True
                      and pathlib.Path(mine[0]['path']) == copy.resolve(),
                      repr(mine)))
        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [
                {'name': 'zz-set', 'repo_url': 'https://example.invalid/zz-set'}]}),
            encoding='utf-8')
        shutil.copytree(pub, ind.parent / 'zz-set')
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind',
                                                   'path': str(ind)}}),
                        encoding='utf-8')
        srcs = pr.load_config(str(host), user_config=str(ucfg))
        mine = [s for s in srcs if s['name'] == 'zz-set']
        cases.append(('a person who brings the same set gets the copy, once',
                      len(mine) == 1
                      and pathlib.Path(mine[0]['path']) == copy.resolve(),
                      repr(mine)))
        declared = pr.declared_source_paths(host, user_config=str(ucfg))
        listed = pr.vendored_source_paths(host)
        cases.append(('declared_source_paths leaves out the copy and the '
                      'same-named brought clone; vendored_source_paths lists it',
                      not [d for d in declared if d[2] == 'zz-set']
                      and [(n, note) for _p, _l, n, note in listed]
                      == [('zz-set', '')], f'{declared} / {listed}'))

        priv = make_set('zz-private', 'private')
        open_host = make_host('open-host', 'zz-private')
        r = checkin_run(open_host, 'zz-private', priv, 'update', '--force')
        cases.append(('a private set is refused into a repository not declared '
                      'private, and nothing is copied',
                      r.returncode != 0 and 'private' in (r.stdout + r.stderr)
                      and not (open_host / 'process' / 'zz-private').exists(),
                      failure_detail(r.stdout, 300) + failure_detail(r.stderr, 300)))
        closed = make_host('closed-host', 'zz-private', visibility='private')
        r = checkin_run(closed, 'zz-private', priv, 'update', '--force')
        cases.append(('the same set is copied into a private repository',
                      r.returncode == 0 and (closed / 'process' / 'zz-private'
                                             / 'practices').is_dir(),
                      failure_detail(r.stdout, 300) + failure_detail(r.stderr, 300)))
        import precedent_check as pc
        old_root = pc.ROOT
        try:
            for where, want in ((closed, 0), (open_host, 1)):
                if where is open_host:
                    shutil.copytree(closed / 'process' / 'zz-private',
                                    open_host / 'process' / 'zz-private')
                pc.ROOT = where
                found = pc._copied_in_set_fits_visibility(None)
                cases.append((f'the tree check finds {want} problem(s) in the '
                              f'{"private" if want == 0 else "unmarked"} '
                              f'repository', len(found) == want, repr(found)))
        finally:
            pc.ROOT = old_root

        (pub / 'practices' / 'zz-later.md').write_text(
            '---\nslug: zz-later\n---\n# later\n\n## Rule\n\ny\n',
            encoding='utf-8')
        git(pub, 'add', '-A')
        git(pub, 'commit', '-qm', 'two')
        git(pub, 'push', '-q', 'origin', 'main')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' /
                            'precedent_engine_freshness.py')], cwd=str(host),
                           env=env, capture_output=True, text=True)
        cases.append(('the freshness line says the copy is behind its origin',
                      'BEHIND UPSTREAM' in r.stdout and 'zz-set' in r.stdout,
                      failure_detail(r.stdout, 500)))

        # A set rooted in a folder of a repository that is something else
        # too: a voice pack beside that repository's own Precedent install,
        # whose practices/ is its own rules, not the set's.
        mixed = make_set('zz-mixed', 'public')
        (mixed / 'pack' / 'practices').mkdir(parents=True)
        (mixed / 'pack' / 'practices' / 'zz-pack-rule.md').write_text(
            '---\nslug: zz-pack-rule\n---\n# p\n\n## Rule\n\nx\n')
        (mixed / 'pack' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-mixed', 'level': 'shared', 'visibility': 'public'}))
        git(mixed, 'add', '-A')
        git(mixed, 'commit', '-qm', 'pack')
        git(mixed, 'push', '-q', 'origin', 'main')
        sub = make_host('sub-host', 'zz-mixed')
        cfg = json.loads((sub / 'precedent.json').read_text())
        cfg['sources'][0]['set_root'] = 'pack'
        (sub / 'precedent.json').write_text(json.dumps(cfg))
        r1 = checkin_run(sub, 'zz-mixed', mixed, 'update', '--force')
        r2 = checkin_run(sub, 'zz-mixed', mixed, 'record')
        got = sorted(f.relative_to(sub / 'process' / 'zz-mixed').as_posix()
                     for f in (sub / 'process' / 'zz-mixed').rglob('*')
                     if f.is_file())
        cases.append(('a set rooted in a folder of its repository is copied from '
                      'that folder alone',
                      r1.returncode == 0 and r2.returncode == 0
                      and got == ['practices/zz-pack-rule.md',
                                  'precedent-source.json'],
                      f'{got} / {failure_detail(r1.stdout, 200)}{failure_detail(r1.stderr, 200)} / '
                      f'{failure_detail(r2.stdout, 200)}{failure_detail(r2.stderr, 200)}'))
        # The carry check reads a set_root set at its folder too (2026-10-28,
        # a consumer's Update Vendors: a line the voice set deleted itself
        # was reported LOST, and the record asked for --accept-loss).
        carry = make_set('zz-carry', 'public')
        (carry / 'pack' / 'practices').mkdir(parents=True)
        carried = carry / 'pack' / 'practices' / 'zz-carry-rule.md'
        carried.write_text('---\nslug: zz-carry-rule\n---\n# c\n\n## Rule\n\n'
                           'a line upstream keeps\na line upstream drops\n')
        (carry / 'pack' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-carry', 'level': 'shared', 'visibility': 'public'}))
        git(carry, 'add', '-A')
        git(carry, 'commit', '-qm', 'pack')
        git(carry, 'push', '-q', 'origin', 'main')
        dep = make_host('carry-host', 'zz-carry')
        dcfg = json.loads((dep / 'precedent.json').read_text())
        dcfg['sources'][0]['set_root'] = 'pack'
        (dep / 'precedent.json').write_text(json.dumps(dcfg))
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(tmp / 'carry-host.git')], env=env, check=True)
        git(dep, 'remote', 'add', 'origin', str(tmp / 'carry-host.git'))
        checkin_run(dep, 'zz-carry', carry, 'update', '--force')
        r1 = checkin_run(dep, 'zz-carry', carry, 'record')
        git(dep, 'add', '-A')
        git(dep, 'commit', '-qm', 'copy the set')
        git(dep, 'push', '-q', 'origin', 'main')
        carried.write_text(carried.read_text().replace(
            'a line upstream drops\n', ''))
        git(carry, 'commit', '-qam', 'upstream drops a line')
        git(carry, 'push', '-q', 'origin', 'main')
        checkin_run(dep, 'zz-carry', carry, 'update', '--force')
        r2 = checkin_run(dep, 'zz-carry', carry, 'record')
        out = r2.stdout + r2.stderr
        cases.append(('a line a set_root set deleted itself is not reported '
                      'lost: the record passes with no --accept-loss',
                      r1.returncode == 0 and r2.returncode == 0
                      and 'LOST' not in out and 'upstream drops' not in out,
                      failure_detail(r1.stdout, 200) + failure_detail(r1.stderr, 200) + ' / ' + failure_detail(out, 600)))
        importlib.reload(checkin)
        checkin.SET_ROOT = 'pack'
        copied = dep / 'process' / 'zz-carry' / 'practices' / 'zz-carry-rule.md'
        cases.append(('upstream_text knows a set_root set\'s unchanged file as '
                      'upstream\'s own text',
                      checkin.upstream_text(carry, copied,
                                            'practices/zz-carry-rule.md', 'HEAD'),
                      str(copied)))
        checkin.SET_ROOT = ''

        cfg['sources'][0]['set_root'] = '../elsewhere'
        (sub / 'precedent.json').write_text(json.dumps(cfg))
        r = checkin_run(sub, 'zz-mixed', mixed, 'update')
        cases.append(('NEGATIVE CONTROL: a set_root that leaves the repository '
                      'is refused', r.returncode != 0
                      and 'set_root' in r.stdout + r.stderr,
                      failure_detail(r.stdout, 200) + failure_detail(r.stderr, 200)))

        # What a copied set's rules point at comes with it (2026-10-19, the
        # first real copy-in left the writing set's checks and the ladder
        # set's hook scripts behind), and the set's own engine copy does not.
        kit = tmp / 'kit-set'
        (kit / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        (kit / 'tools' / 'checks' / 'check_zz.py').write_text('x = 1\n')
        (kit / 'tools' / 'checks' / 'tests' / 'test_zz.sh').write_text('true\n')
        (kit / 'tools' / 'zz_shipped.py').write_text('x = 1\n')
        (kit / 'tools' / 'zzhooks').mkdir()
        (kit / 'tools' / 'zzhooks' / 'run.py').write_text('x = 1\n')
        (kit / 'tools' / 'zzhooks' / 'helper.py').write_text('x = 1\n')
        (kit / 'tools' / 'precedent_engine_file.py').write_text('x = 1\n')
        (kit / 'practices').mkdir()
        (kit / 'practices' / 'zz-kit.md').write_text(
            '---\nslug: zz-kit\nships: ["tools/zz_shipped.py"]\n'
            'hooks: [{"event": "Stop", "run": "tools/zzhooks/run.py"}]\n'
            'checked_by: "tools/checks/check_zz.py"\n---\n# k\n\n## Rule\n\nx\n')
        got = checkin._files_rules_name(kit)
        cases.append(('a copied set brings its checks, what its rules ship and '
                      'the hook scripts they run, folder and all',
                      got == ['tools/checks', 'tools/zz_shipped.py', 'tools/zzhooks'],
                      repr(got)))
        cases.append(('NEGATIVE CONTROL: and never the engine copy in its tools/',
                      'tools/precedent_engine_file.py' not in got
                      and 'tools' not in got, repr(got)))

        import precedent_source_credentials as psc
        gone = make_host('gone-host', 'zz-set', visibility='private')
        un = psc.unresolved_private_sources(gone, env={
            'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')})
        cases.append(('a missing copy is Update Vendors\' to make, not a set '
                      'to attach', any(n == 'zz-set' and 'Update Vendors' in why
                                       for _l, n, why in un), repr(un)))
        import precedent_source_bootstrap as psb
        old = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        try:
            res = psb.sources_from_brings(retries=0, skip_names={'zz-set'})
        finally:
            if old is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = old
        cases.append(('session start does not fetch a set the repository '
                      'copies in', res == [('zz-set', True, 'copied into this '
                                            'repository: not fetched')],
                      repr(res)))
    except RuntimeError as e:
        cases.append((str(e), False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if 'checkin' in sys.modules:
            importlib.reload(sys.modules['checkin'])
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a shared set copied into a repository resolves, is guarded and '
          f'reports its freshness ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_update_vendors_rehearsal_findings():
    """Ten defects a rehearsal of Update Vendors and a fresh install found on
    2026-09-28, run against a real consumer and a scratch one. Each group
    plants the state that exposed it and reads what the tool said or wrote.

    - A bare mention of a renamed practice (`go-merge`, now `go-update`) was
      dropped by citations(), which said "no live citation" while
      precedent_practice_refs.py --withdrawn listed one.
    - A root STYLEGUIDE.md or VOICE.md was left behind under a DONE.
    - .gitignore, installed once, never gained a line the template added.
    - An engine that landed off the fetched tip was not said.
    - A fresh install recorded none of its hooks in ENGINE_MANIFEST.json.
    - A vendored copy of the update fetched the consumer's own origin.
    - checkin.py read `origin/claude/x` as `x`, and held an install pinned
      to the branch every install follows.
    - One small edit to a template block read as the whole block missing.
    - The retired-name sweep missed precedent-team-* and MAP.md/GLOSSARY.md.
    - A run budget upstream gives a vendored tool went unmentioned (since
      2026-10-07 it is written in, upstream's figure and note)."""
    import contextlib, io, tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rehearsal-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)

    def verdict(name, cases):
        bad = [(n, d) for n, ok, d in cases if not ok]
        check(f'{name} ({len(cases)} stated cases)', not bad,
              '; '.join(f'{n}: {d}' for n, d in bad))

    saved_source, saved_run = pu.SOURCE, pu.run
    try:
        # -- citations: a bare mention of a withdrawn slug is listed --------
        cases = []
        fake = tmp / 'fake-source'
        (fake / 'tools').mkdir(parents=True)
        hits = [dict(source='this repository', kind='live', file='docs/X.md',
                     line=3, slug='go-merge', must_fix=False),
                dict(source='this repository', kind='live', file='docs/X.md',
                     line=5, slug='reworded-one', must_fix=False),
                dict(source='this repository', kind='live', file='docs/X.md',
                     line=7, slug='gone-hard', must_fix=True),
                dict(source='precedent', kind='live', file='practices/y.md',
                     line=1, slug='go-merge', must_fix=False)]
        argv_file = tmp / 'refs-argv.json'
        (fake / 'tools' / 'precedent_practice_refs.py').write_text(
            'import json, sys\nopen(' + repr(str(argv_file)) + ', "w").write('
            'json.dumps(sys.argv[1:]))\nprint(json.dumps(' + repr({
                'slugs': {'go-merge': 'deduplicated', 'reworded-one': 'Rule reworded',
                          'gone-hard': 'retired'},
                'successors': {'go-merge': 'go-update'}, 'hits': hits}) + '))\n',
            encoding='utf-8')
        pu.SOURCE = fake
        got = pu.citations(tmp)
        pu.SOURCE = saved_source
        fix, read = got if got else ([], [])
        cases.append(('a pointer to a withdrawn practice is still one to fix',
                      [w for w, _y in fix] == ['docs/X.md:7'], str(got)))
        cases.append(('a bare mention of a renamed practice is listed to read, '
                      'naming its successor',
                      any(r.startswith('docs/X.md:3') and 'go-update' in r
                          for r in read), str(read)))
        cases.append(('...beside a reworded one, and nothing from another source',
                      'docs/X.md:5' in read and len(read) == 2, str(read)))
        # Code too (2026-10-04, a consumer): a tool the update never touched
        # kept citing a slug a shared set had deduplicated, the update said
        # "no live citation of a withdrawn practice to fix", and only the
        # full check at Debut found it. The lookup read Markdown only.
        asked = json.loads(argv_file.read_text()) if argv_file.is_file() else []
        cases.append(('the lookup is asked to read code as well as Markdown',
                      '--code' in asked, str(asked)))
        verdict('Update Vendors lists a bare mention of a renamed practice', cases)

        # -- a vendored copy refuses before any fetch ------------------------
        cases = []
        cons = tmp / 'vendored-consumer'
        (cons / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        (cons / 'tools').mkdir()
        (cons / 'tools' / pve.MANIFEST_NAME).write_text('{}', encoding='utf-8')
        (cons / 'tools' / 'precedent_vendor_engine.py').write_text('', encoding='utf-8')
        git(tmp, 'init', '-q', str(cons))
        fetched = []

        def recording_run(argv, cwd):
            if 'fetch' in argv:
                fetched.append(argv)
                return 1, 'fatal: couldn\'t find remote ref main'
            return saved_run(argv, cwd)
        pu.SOURCE = cons / 'process' / 'upstream'
        pu.run = recording_run
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = pu.update(cons, skip_check=True)
        pu.SOURCE, pu.run = saved_source, saved_run
        text = out.getvalue()
        cases.append(('a copy inside a consumer\'s vendored tree FAILS, naming '
                      'the clone\'s own copy to run', rc == pu.FAILED
                      and '../BestPractice/tools/precedent_update.py --repo .' in text,
                      failure_detail(text, 600)))
        cases.append(('...before any fetch', not fetched, str(fetched)))
        cases.append(('a BestPractice clone is its own clone',
                      pu.source_is_its_own_clone() is None if hasattr(
                          pu, 'source_is_its_own_clone') else False, ''))
        verdict('Update Vendors refuses to run from a vendored copy', cases)

        # -- one update over a planted consumer: legacy docs, .gitignore,
        # -- a missing run budget; then an engine that landed elsewhere -----
        tip = git(ROOT, 'rev-parse', 'HEAD').stdout.strip()

        def planted(name, landed):
            repo = tmp / name
            (repo / 'tools').mkdir(parents=True)
            (repo / 'local' / 'practices').mkdir(parents=True)
            (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps({
                'source_commit': landed, 'kind': 'consumer',
                'files': ['precedent_branches.py', 'github_budget.py']}),
                encoding='utf-8')
            (repo / 'tools' / 'precedent_vendor_engine.py').write_text(
                'print("precedent_vendor_engine refresh OK: already current")\n',
                encoding='utf-8')
            (repo / 'tools' / 'github_api_budgets.json').write_text(json.dumps({
                'floors': {'core': 20}, 'run_budgets': {'github_budget.py': 1}}),
                encoding='utf-8')
            (repo / 'STYLEGUIDE.md').write_text('# Style\n', encoding='utf-8')
            (repo / 'VOICE.md').write_text('# Voice\n', encoding='utf-8')
            (repo / 'local' / 'practices' / 'project-voice.md').write_text(
                '# voice\n', encoding='utf-8')
            (repo / '.gitignore').write_text('__pycache__/\nbuild/\n', encoding='utf-8')
            git(tmp, 'init', '-q', str(repo))
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'installed')
            return repo

        def fetchless(argv, cwd):
            if argv[:1] == ['git'] and 'fetch' in argv:
                return 0, ''
            if argv[:1] == ['git'] and 'rev-parse' in argv \
                    and argv[-1] == f'origin/{pve.SOURCE_BRANCH}':
                return 0, tip + '\n'
            return saved_run(argv, cwd)

        def run_update(repo):
            pu.run = fetchless
            # GitHub stood in: the tip's test passed, so the tip is taken.
            saved_state = getattr(pu, 'main_test_state', None)
            pu.main_test_state = lambda sha, tests: ('passed', 'stand-in')
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    rc = pu.update(repo, skip_check=True)
            finally:
                pu.run = saved_run
                if saved_state is not None:
                    pu.main_test_state = saved_state
            return rc, out.getvalue()

        cases = []
        repo = planted('planted', tip)
        rc, text = run_update(repo)
        left = text.split('LEFT FOR YOU', 1)[-1] if 'LEFT FOR YOU' in text else ''
        cases.append(('a root STYLEGUIDE.md with no project-visual-identity.md is '
                      'left for you, naming the migration step',
                      rc == pu.LEFT and '- STYLEGUIDE.md:' in left
                      and 'project-visual-identity.md' in left and 'step 3b' in left,
                      failure_detail(text, 1500)))
        cases.append(('a root VOICE.md beside project-voice.md is left to delete',
                      '- VOICE.md:' in left and 'exists too' in left, failure_detail(left, 800)))
        gi = (repo / '.gitignore').read_text(encoding='utf-8')
        cases.append(('.gitignore gains the template lines it lacked, its own kept once',
                      '.claude/worktrees/' in gi.splitlines()
                      and '.precedent/' in gi.splitlines()
                      and gi.splitlines().count('__pycache__/') == 1
                      and 'build/' in gi.splitlines()
                      and '.gitignore:' in text, gi))
        # Since 2026-10-07 the update writes upstream's figure in, rather than
        # leaving a copy-it-yourself item (seed_engine_budgets says why).
        cases.append(('a run budget upstream gives a vendored tool, missing here, '
                      'is written in with upstream\'s figure, not left for you',
                      'tools/github_api_budgets.json: precedent_branches.py' not in left
                      and '"precedent_branches.py"' in (repo / 'tools' /
                                                        'github_api_budgets.json').read_text()
                      and 'API budgets' in text,
                      failure_detail(left, 800)))
        cases.append(('...and nothing for a tool this repo already budgets',
                      'github_api_budgets.json: github_budget.py' not in left, ''))
        # A consumer whose GLOSSARY.md build_views.py generates gets the full
        # build after the sync, which renders the loader block only: a
        # practice the update stopped materializing stayed linked from it,
        # and the lint failed on the dead link (2026-09-30). A hand-written
        # one is the repo's and is not rebuilt.
        for name, header in (('generated-views', '---\ngenerated_by: '
                              'tools/build_views.py\n---\n'),
                             ('hand-views', '')):
            repo = planted(name, tip)
            (repo / 'tools' / 'precedent_sync_views.py').write_text(
                'print("synced")\n', encoding='utf-8')
            (repo / 'tools' / 'build_views.py').write_text(
                'import pathlib\n'
                'p = pathlib.Path("GLOSSARY.md")\n'
                'p.write_text(p.read_text().replace("[Plan it](practices/planted-withdrawn.md)",'
                ' ""))\n', encoding='utf-8')
            (repo / 'GLOSSARY.md').write_text(
                header + '# Glossary\n\n[Plan it](practices/planted-withdrawn.md)\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'views')
            rc, text = run_update(repo)
            linked = 'practices/planted-withdrawn.md' in (repo / 'GLOSSARY.md').read_text()
            if header:
                cases.append(('a consumer\'s generated GLOSSARY.md is rebuilt by the '
                              'update, so a withdrawn practice is no longer linked',
                              not linked and 'GLOSSARY.md, which build_views.py '
                              'generates here' in text, failure_detail(text, 800)))
            else:
                cases.append(('...and a hand-written one is left as it is',
                              linked, failure_detail(text, 800)))
        elsewhere = planted('landed-elsewhere', '1' * 40)
        rc, text = run_update(elsewhere)
        cases.append(('an engine that landed off the fetched tip FAILS, saying '
                      'where it landed and where it should have',
                      rc == pu.FAILED and 'the engine landed at 111111111111' in text
                      and f'{pve.SOURCE_BRANCH} @ {tip[:12]}' in text, failure_detail(text, 800)))
        verdict('Update Vendors brings install-once files and migrations forward', cases)

        # -- a command the update repoints is staged with the rest ----------
        # Found 2026-10-03 rehearsing a consumer: the repoint ran after the
        # update staged its work, so `tools/bootstrap.sh` kept calling
        # process/upstream/tools/... `|| true` in the commit the report told
        # the person to make, and the session-start step silently did nothing.
        cases = []
        repo = planted('repointed', tip)
        (repo / 'tools' / 'checkin.py').write_text('', encoding='utf-8')
        (repo / 'tools' / 'bootstrap.sh').write_text(
            'python3 process/upstream/tools/checkin.py fresh || true\n', encoding='utf-8')
        (repo / 'NOTES.md').write_text('mine\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'startup script')
        (repo / 'NOTES.md').write_text('mine, unfinished\n', encoding='utf-8')
        rc, text = run_update(repo)
        staged = git(repo, 'diff', '--cached', '--name-only').stdout.split()
        unstaged = git(repo, 'diff', '--name-only').stdout.split()
        boot = git(repo, 'show', ':tools/bootstrap.sh').stdout
        cases.append(('the repointed startup script is staged, so the commit the '
                      'report asks for carries it',
                      'tools/bootstrap.sh' in staged and 'tools/bootstrap.sh' not in unstaged
                      and 'python3 tools/checkin.py fresh' in boot, failure_detail(text, 600)))
        cases.append(('...and a file already uncommitted before the update stays unstaged',
                      'NOTES.md' in unstaged and 'NOTES.md' not in staged,
                      f'staged={staged} unstaged={unstaged}'))
        verdict('Update Vendors stages the commands it repoints', cases)
    finally:
        pu.SOURCE, pu.run = saved_source, saved_run

    # -- checkin.py: a slash in the default branch, and the followed branch --
    cases = []
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import checkin
        finally:
            sys.path.pop(0)
        origin, clone = tmp / 'origin', tmp / 'clone'
        git(tmp, 'init', '-q', '-b', 'claude/x', str(origin))
        (origin / 'f').write_text('x\n', encoding='utf-8')
        git(origin, 'add', '-A')
        git(origin, 'commit', '-qm', 'x')
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)], env=env,
                       capture_output=True)
        git(clone, 'remote', 'set-head', 'origin', 'claude/x')
        cases.append(('origin/claude/x is the default branch claude/x, not x',
                      checkin._default_branch(clone) == 'claude/x',
                      checkin._default_branch(clone)))
        saved_manifest = checkin._manifest
        held = {}
        for pin in (pve.SOURCE_BRANCH, 'precedent-beta-v01'):
            checkin._manifest = lambda pin=pin: {'upstream': {'branch': pin}}
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    checkin._pinned_branch_hold(clone)
                held[pin] = False
            except SystemExit:
                held[pin] = True
        checkin._manifest = saved_manifest
        cases.append((f'an install pinned to {pve.SOURCE_BRANCH} is not held, '
                      f'whatever the clone\'s default', not held[pve.SOURCE_BRANCH],
                      str(held)))
        cases.append(('...and one pinned to any other non-default branch still is',
                      held['precedent-beta-v01'], str(held)))
    except (OSError, ImportError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    verdict('checkin.py reads a slashed default branch and never holds the '
            'followed branch', cases)

    # -- missing_template_blocks: a changed block is not a missing one ------
    cases = []
    tmpl = ('#!/bin/sh\n\n# Python dependencies\npip install --quiet cmarkgfm\n\n'
            'git fetch --quiet origin\ngit status --short\n\n'
            '# A block this copy does not have\necho "the freshness check"\n'
            'python3 tools/fresh.py --quiet\n')
    local = ('#!/bin/sh\n\n# Python dependencies\n'
             'pip install --quiet cmarkgfm pyyaml\n\n'
             'git fetch --quiet --prune origin\ngit status --short --branch\n\n'
             'echo "a block of this repo\'s own"\n')
    got = {title: how for _n, title, how in pve.missing_template_blocks(local, tmpl)}
    cases.append(('a block with its heading and one word added reads changed, '
                  'not missing', got.get('Python dependencies') == 'changed (1 of 1 lines)',
                  str(got)))
    cases.append(('a block with no heading, edited, reads changed by its words',
                  got.get('git fetch --quiet origin') == 'changed (2 of 2 lines)',
                  str(got)))
    cases.append(('a block nothing local resembles is still missing',
                  got.get('A block this copy does not have') == 'missing', str(got)))
    verdict('missing_template_blocks tells a changed block from a missing one', cases)

    # -- the retired-name sweep: precedent-team-*, MAP.md and GLOSSARY.md ---
    cases = []
    sweep = tmp / 'sweep'
    sweep.mkdir()
    (sweep / 'MAP.md').write_text('# Map\n\nRules come from precedent-team-writing.\n'
                                  '\n| old-rule | deduplicated | precedent-team-old |\n',
                                  encoding='utf-8')
    (sweep / 'GLOSSARY.md').write_text(
        '<!-- GENERATED by tools/build_views.py -->\nprecedent-team-writing\n',
        encoding='utf-8')
    (sweep / 'AGENTS.md').write_text(
        'Clone precedent-team-x.\n'
        'precedent-shared-x (named precedent-team-x until 2026-09-18).\n'
        'Branch precedent-beta-v01 here.\n'
        '\nThe engine was pinned to `precedent-beta-v01`, since\n'
        'renamed `staging`.\n', encoding='utf-8')
    hits = pve.retired_branch_mentions(sweep)
    cases.append(('a hand-kept MAP.md naming a precedent-team-* set is flagged',
                  ('MAP.md', 3, 'precedent-team-', 'precedent-shared-') in hits, str(hits)))
    cases.append(('...and AGENTS.md\'s, beside the retired branch name still found',
                  ('AGENTS.md', 1, 'precedent-team-', 'precedent-shared-') in hits
                  and ('AGENTS.md', 3, 'precedent-beta-v01', 'staging') in hits, str(hits)))
    cases.append(('a line recording the rename, and a file generated whole, are not',
                  not any(r == 'GLOSSARY.md' or (r, n) == ('AGENTS.md', 2)
                          for r, n, _o, _n in hits), str(hits)))
    # 2026-09-30: history that wraps was flagged, because only the line was
    # read; and a set's MAP.md lists withdrawn practices in status rows.
    cases.append(('a sentence recording the rename across a line break is '
                  'history, and so is a deduplicated row',
                  not any((r, n) in (('AGENTS.md', 5), ('MAP.md', 5))
                          for r, n, _o, _n in hits), str(hits)))
    saved_left = list(pve._LEFT_FOR_YOU)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            pve._report_retired_branch_names(sweep)
        said = out.getvalue()
        cases.append(('the report names the prefix rename without calling it a branch',
                      'RETIRED NAME: 2 line(s)' in said and 'precedent-shared-*' in said
                      and 'RETIRED BRANCH NAME: 1 line(s)' in said, failure_detail(said, 600)))
    except (KeyError, TypeError) as e:
        cases.append((f'the report ran ({type(e).__name__}: {e})', False, ''))
    finally:
        pve._LEFT_FOR_YOU[:] = saved_left
    verdict('the retired-name sweep covers precedent-team-* and the index files', cases)

    # -- a fresh install tracks its hooks ------------------------------------
    cases = []
    proj = tmp / 'proj'
    try:
        # The shared fresh install (_fresh_install_fixture), copied, not
        # rerun: no user config and no individual set, as on GitHub.
        rc, stdout, stderr = _fresh_install_fixture(proj)
        m = json.loads((proj / 'tools' / pve.MANIFEST_NAME).read_text(encoding='utf-8'))
        # The individual-set bootstrap hook is the person's, not the
        # engine's: written only where the person running the install has an
        # individual set (on a machine with its clone, that is this run),
        # rendered for them, and never in hook_files. Judged apart below.
        # Until 2026-10-08 this case counted it as an engine hook, so it
        # failed on any machine with an individual-set clone once install
        # began wiring that hook (a3a62285), and passed on GitHub.
        all_hooks = sorted(p.name for p in (proj / '.claude' / 'hooks').glob('*.sh'))
        hooks = [h for h in all_hooks if h != pve.INDIVIDUAL_HOOK]
        recorded = m.get('hooks_sha256') or {}
        if pve.INDIVIDUAL_HOOK in all_hooks:
            st = json.loads((proj / '.claude' / 'settings.json').read_text(encoding='utf-8'))
            first = [h.get('command', '') for g in st['hooks']['SessionStart']
                     for h in g.get('hooks', [])][:1]
            cases.append(('an install by a person with an individual set wires its '
                          'bootstrap hook first, and leaves it out of the engine record',
                          bool(first) and pve.INDIVIDUAL_HOOK in first[0]
                          and pve.INDIVIDUAL_HOOK not in (m.get('hook_files') or []),
                          f'first SessionStart command={first} '
                          f'hook_files={m.get("hook_files")}'))
        cases.append(('a fresh install records every hook it wrote, by hash',
                      rc == 0 and bool(hooks)
                      and sorted(m.get('hook_files') or []) == hooks
                      and all(recorded.get(h) == hashlib.sha256(
                          (proj / '.claude' / 'hooks' / h).read_bytes()).hexdigest()
                          for h in hooks),
                      f'rc={rc} on disk={hooks} recorded={sorted(recorded)} '
                      + failure_detail(stdout + stderr, 400)))
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    verdict('a fresh install tracks its hooks in ENGINE_MANIFEST.json', cases)


def check_carry_check_never_invents_lost_content():
    """A clone that does not contain the recorded base must refuse to answer,
    never report the whole vendored tree as lost.

    THE INCIDENT, 2026-09-08, on a real consumer repo. `checkin.py` reported
    69 "LOST" lines across a vendored tree from which nothing had been
    dropped. `git show <base>:<path>` exits 128 with EMPTY STDOUT for two
    unrelated situations -- the commit is not in this clone, or the path did
    not exist at that commit -- and the old code read stdout alone, so an
    unanswerable question was silently answered "every line here is new".
    Disproving it took extracting both trees and diffing them by hand, and
    the tempting shortcut was `--accept-loss`, which would have accepted a
    loss nobody measured: the guard against silent data loss becoming its
    cause.

    THE CASE THAT DISCRIMINATES IS 2, and it is built from a genuinely
    shallow clone rather than a fabricated one -- `git clone --depth 1` over
    a `file://` transport, because git IGNORES --depth on a plain path (this
    repository lost an hour to that once already, and a test that believed
    it had a shallow clone and did not would pass against the bug).

    Case 4 is the other half and the one a careless fix breaks: a file that
    really is new at base must still report its lines as pending, because
    that is the check doing its job.
    """
    import tempfile

    def git(cwd, *args, check_rc=True):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True, env=env)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # -- an "upstream" with two commits ---------------------------------
        up = tmp / 'upstream'
        up.mkdir()
        git(up.parent, 'init', '-q', str(up))
        git(up, 'config', 'user.email', 'harness@example.com')
        git(up, 'config', 'user.name', 'H')
        (up / 'shared.md').write_text('alpha\nbeta\ngamma\n', encoding='utf-8')
        git(up, 'add', '-A'); git(up, 'commit', '-qm', 'base')
        base_sha = git(up, 'rev-parse', 'HEAD')
        (up / 'shared.md').write_text('alpha\nbeta\ngamma\ndelta\n', encoding='utf-8')
        git(up, 'add', '-A'); git(up, 'commit', '-qm', 'second')

        # -- a genuinely shallow clone: file:// or --depth is IGNORED --------
        shallow = tmp / 'shallow'
        subprocess.run(['git', 'clone', '-q', '--depth', '1',
                        f'file://{up}', str(shallow)],
                       capture_output=True, text=True, check=True)
        # checkin.py fetches a recorded commit a shallow clone lacks
        # (fetch_recorded_commit, 2026-10-29), so the base must be one origin
        # cannot hand over either -- a rewritten or unreachable history.
        subprocess.run(['git', '-C', str(shallow), 'remote', 'set-url', 'origin',
                        f'file://{tmp}/no-such-upstream'],
                       capture_output=True, text=True, check=True)
        holds_base = subprocess.run(
            ['git', '-C', str(shallow), 'cat-file', '-e', f'{base_sha}^{{commit}}'],
            capture_output=True, text=True).returncode == 0
        cases.append(('the fixture clone is genuinely shallow -- it does NOT '
                      'hold the base commit (without this the case below '
                      'proves nothing)', not holds_base, f'holds_base={holds_base}'))

        # -- the two indistinguishable git failures, measured ---------------
        deep = tmp / 'deep'
        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(deep)],
                       capture_output=True, text=True, check=True)
        missing_commit = subprocess.run(
            ['git', '-C', str(shallow), 'show', f'{base_sha}:shared.md'],
            capture_output=True, text=True)
        missing_path = subprocess.run(
            ['git', '-C', str(deep), 'show', f'{base_sha}:never-existed.md'],
            capture_output=True, text=True)
        cases.append(('a missing COMMIT and a missing PATH are byte-identical '
                      'on stdout and exit code, so stdout alone cannot tell '
                      'them apart',
                      missing_commit.returncode == missing_path.returncode
                      and missing_commit.stdout == missing_path.stdout == '',
                      f'{missing_commit.returncode}/{missing_commit.stdout!r} vs '
                      f'{missing_path.returncode}/{missing_path.stdout!r}'))

        # -- the guard itself ----------------------------------------------
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'ck', ROOT / 'tools' / 'checkin.py')
        ck = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            spec.loader.exec_module(ck)
        finally:
            sys.path.pop(0)

        has_guard = hasattr(ck, '_base_is_present') and hasattr(ck, '_git_rc')
        cases.append(('checkin.py has the precondition helpers at all',
                      has_guard, str(sorted(n for n in dir(ck) if n.startswith('_git') or 'base_is' in n))))
        if has_guard:
            cases.append(('_base_is_present is FALSE for a base the shallow '
                          'clone lacks -- the case that used to read as "every '
                          'line is new"',
                          ck._base_is_present(shallow, base_sha) is False, ''))
            cases.append(('_base_is_present is TRUE for a base the full clone '
                          'holds, so the guard does not simply always refuse',
                          ck._base_is_present(deep, base_sha) is True, ''))
            rc_missing, out_missing = ck._git_rc(deep, 'show', f'{base_sha}:never-existed.md')
            rc_ok, out_ok = ck._git_rc(deep, 'show', f'{base_sha}:shared.md')
            cases.append(('_git_rc surfaces the exit code a new-at-base path '
                          'returns, which is what lets the caller treat it as '
                          'genuinely new rather than unanswerable',
                          rc_missing != 0 and out_missing == '' and rc_ok == 0
                          and 'alpha' in out_ok,
                          f'{rc_missing} {rc_ok} {out_ok!r}'))

            # -- END TO END, and this is the case that proves the guard
            # FIRES rather than merely exists. A non-zero exit is not
            # evidence (practice: control-asserts-which-failure), so it
            # asserts the message: "cannot run", never "LOST".
            consumer = tmp / 'consumer'
            (consumer / 'process' / 'upstream').mkdir(parents=True)
            git(consumer.parent, 'init', '-q', str(consumer))
            git(consumer, 'config', 'user.email', 'harness@example.com')
            git(consumer, 'config', 'user.name', 'H')
            (consumer / 'process' / 'upstream' / 'shared.md').write_text(
                'alpha\nbeta\ngamma\nlocal addition nobody upstream has\n',
                encoding='utf-8')
            (consumer / 'process' / 'manifest.json').write_text(json.dumps(
                {'upstream': {'commit': base_sha, 'branch': 'main'}}),
                encoding='utf-8')
            git(consumer, 'add', '-A'); git(consumer, 'commit', '-qm', 'vendored')
            git(consumer, 'branch', '-M', 'main')
            git(consumer, 'remote', 'add', 'origin', str(consumer))
            git(consumer, 'fetch', '-q', 'origin')

            saved = (ck.ROOT, ck.UPSTREAM, ck.MANIFEST)
            ck.ROOT = consumer
            ck.UPSTREAM = consumer / 'process' / 'upstream'
            ck.MANIFEST = consumer / 'process' / 'manifest.json'
            try:
                try:
                    ck._carry_check(shallow, accept_loss=False)
                    said = '<returned without exiting>'
                except SystemExit as exc:
                    said = str(exc.code)
                cases.append(('run end to end against the shallow clone, it '
                              'says it CANNOT RUN and names the base commit',
                              'cannot run' in said and base_sha[:12] in said,
                              said[:300]))
                cases.append(('and it does NOT report anything as LOST, which '
                              'is the false finding this whole check exists '
                              'for', 'LOST' not in said, said[:300]))
                cases.append(('and it refuses --accept-loss for this state by '
                              'name, so the tempting shortcut is closed',
                              'accept-loss does not apply' in said
                              or '--accept-loss does not apply' in said,
                              said[:300]))
            finally:
                ck.ROOT, ck.UPSTREAM, ck.MANIFEST = saved

    ok = all(c[1] for c in cases)
    check(f'the carry check refuses to answer rather than inventing lost '
          f'content ({len(cases)} stated cases, on a real shallow clone)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


