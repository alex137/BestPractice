# The harness tests for the planted cases
#
# tools/harness/vh_planted_cases.py -- part of the verification harness:
# the planted cases: one per enforced practice check, each with its clean control (check_precedent_check_fires).
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def _reverse_marked_dated_list(text):
    """-> `text` with the first `<!--dated-list-->` block reversed.

    Restores the disorder the practice was written for: entries prepended at
    the top, so the list reads newest first.
    """
    head, rest = text.split('<!--dated-list-->', 1)
    lines = rest.splitlines()
    rows = [i for i, l in enumerate(lines) if l.startswith('- ')]
    picked = [lines[i] for i in rows]
    for i, row in zip(rows, reversed(picked)):
        lines[i] = row
    return head + '<!--dated-list-->' + '\n'.join(lines)


def _failing_findings(out, cap=40):
    """-> the VIOLATION/ERROR blocks of a precedent_check.py run -- each
    finding line and the indented lines under it -- capped at `cap` lines,
    or the run's last lines when it printed none."""
    keep, inside = [], False
    for line in out.splitlines():
        if re.match(r'\s*(VIOLATION|ERROR|FAIL)\b', line):
            inside = True
            keep.append(line.strip())
        elif inside and line.strip() == 'the rule:':
            inside = False                  # the rule's text is not a finding
        elif inside and line.startswith((' ', '\t')) and line.strip():
            keep.append('  ' + line.strip())
        else:
            inside = False
    if not keep:
        keep = [l for l in out.splitlines() if l.strip()][-8:]
    if len(keep) > cap:
        keep = keep[:cap] + [f'... and {len(keep) - cap} more line(s)']
    return '\n' + '\n'.join(keep)


def check_precedent_check_fires():
    """The enforced channel's own behaviour, as stated cases against throwaway
    repositories -- one planted violation per enforced practice.

    WHY THIS EXISTS. Until phase 4 the only thing verifying a `checked_by:`
    was check_checked_by_targets_exist() (now precedent_check.py's practice-file-shape), which asserts the named FILE
    is present. Tested one by one, the eight inherited claims came apart:
    `readers-vocabulary` named a linter with no vocabulary check in it,
    `acronyms-glossary` named a check that only ever warns, and four named
    gates that were RED on this repository for reasons unrelated to either
    practice. A claim nobody has watched fire reads as coverage and is not.

    So this asserts what each check is supposed to DO, from outside it: copy
    the tree into a scratch repository, PLANT the violation the practice
    exists to prevent, run tools/precedent_check.py --only SLUG as a
    subprocess, and require a non-zero exit. Each case also requires the
    UNPLANTED baseline to come back clean, because a check that fires on
    everything is as useless as one that fires on nothing -- that direction is
    what caught the first version of the quick-index check, which counted rows
    from the middle of the header line and reported zero on a table with
    twenty-six.
    """
    import shutil, tempfile, multiprocessing

    # A FIXTURE'S OWN GIT RUNS NO GLOBAL HOOKS. A session's core.hooksPath
    # reaches every throwaway repository here (the 2026-09-13 gotcha), and
    # measured 2026-10-11 it was about 100 of this function's 487 seconds:
    # each push to a fixture's bare remote ran the leak gate over the whole
    # tree (about 13.6 s), each commit about 1 s. No case plants anything a
    # hook judges -- every case is judged by precedent_check.py, which this
    # does not touch -- and GitHub's runners have no global hooks at all.
    def git(cwd, *args, check_rc=True, env=None):
        r = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                            '-C', str(cwd), *args],
                           capture_output=True, text=True, env=env)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-enforce-'))
    cases = []
    try:
        pristine = tmp / 'pristine'
        # Files a set this repository does not track ships here
        # (precedent_materialize.deliver_session_ships lists them in
        # .git/info/exclude) are this session's, never the tree's: a copy
        # that takes them judges a set's own code as this repository's.
        _shipped = set()
        try:
            _excl = (ROOT / '.git' / 'info' / 'exclude').read_text(encoding='utf-8')
            if '# BEGIN precedent session ships' in _excl:
                _block = _excl.split('# BEGIN precedent session ships', 1)[1]
                _block = _block.split('# END precedent session ships', 1)[0]
                _shipped = {ln.strip().lstrip('/') for ln in _block.splitlines()[1:]
                            if ln.strip() and not ln.startswith('#')}
        except OSError:
            pass
        _base_ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'prompts')

        def _ignore(d, names):
            rel = pathlib.PurePath(os.path.relpath(d, ROOT)).as_posix()
            return set(_base_ignore(d, names)) | {
                n for n in names
                if (f'{rel}/{n}' if rel != '.' else n) in _shipped}
        shutil.copytree(ROOT, pristine, ignore=_ignore)
        git(pristine, 'init', '-q')
        git(pristine, 'config', 'user.email', 'harness@example.com')
        git(pristine, 'config', 'user.name', 'harness')
        git(pristine, 'add', '-A')
        # A fixture commit has no session behind it, and says so: the
        # engine's own session-trailer check (2026-10-06) judges every commit
        # no origin has, and a silent one is exactly what it exists to catch.
        git(pristine, 'commit', '-qm',
            'baseline\n\nSession: none available (verify_harness fixture)')
        # Packed once, so every copy below is 1,638 files instead of 3,198
        # (half were loose objects): 0.34 s to copy instead of 0.50, and
        # 0.03 s to delete instead of 0.07 (measured 2026-10-11).
        git(pristine, 'repack', '-adq')
        git(pristine, 'prune')

        def fresh(name):
            repo = tmp / name
            shutil.copytree(pristine, repo, symlinks=True)
            # NO sibling sources are copied beside the fixture, deliberately.
            # build_views.py went multi-source on 2026-09-06 and the first
            # version of this fixture DID copy them, so that the regeneration
            # case exercised the real path instead of a degraded one. That
            # became wrong the same day, when the privacy guard widened: this
            # repo declares `visibility: public`, so private-level sources are
            # dropped from the block BEFORE resolution and their absence
            # cannot make it unverifiable. Copying them back in only gave
            # layered-practice-packs' baseline the real repo's 34 unreachable
            # shared practices to report -- an open architectural question (see
            # todo/todo-2026-09-06-unreachable-practices.md), not a defect a fixture planted,
            # and it made every planted case below prove nothing. A fixture
            # for a PRIVATE consumer's multi-source block would need them; the
            # coverage for that lives in
            # check_loader_block_covers_every_declared_source(), which runs
            # against the real tree with its real sources.
            return repo

        def run(repo, slug, *extra, env_extra=None):
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
            # practice: fixture-owns-its-state -- a case that judges commits
            # against a DECLARED IDENTITY (check_commit_author,
            # check_buenos_aires_dates) must not inherit whichever person's
            # PRECEDENT_COMMIT_* this session's own environment happens to
            # carry: that would make the case pass or fail depending on WHO
            # is running the harness, never on the code. Cleared here, for
            # every case, so only a case that explicitly asks for an
            # identity (env_extra) gets one.
            for _k in ('PRECEDENT_COMMIT_NAME', 'PRECEDENT_COMMIT_EMAIL',
                      'PRECEDENT_COMMIT_TZ'):
                env.pop(_k, None)
            # The fixture must not resolve whoever's individual set happens
            # to be configured on this machine. It is found by ABSOLUTE path
            # from a user-level config, so unlike the shared source (a relative
            # sibling that a temp-dir fixture cannot reach) it follows the
            # fixture anywhere -- and layered-practice-packs' baseline then
            # reports that developer's private practices, making the planted
            # case prove nothing. Pointed at a file that does not exist, so
            # the resolver takes its documented "this person has no
            # individual set" path rather than a half-configured one.
            env['PRECEDENT_USER_CONFIG'] = str(repo / '.no-user-config.json')
            # A case's own env_extra is applied after that default, so a case
            # that brings an individual set of its own keeps it (2026-10-05:
            # private-repo-scrub's planted set was silently replaced).
            if env_extra:
                env.update(env_extra)
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_check.py'),
                 '--only', slug, *extra],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        def rewrite(repo, rel, fn):
            p = repo / rel
            p.write_text(fn(p.read_text(encoding='utf-8')), encoding='utf-8')

        # ROTATION (Morgan, 2026-09-21, strength: decided -- "build the 10%
        # rotation"). This function was 107.9s of a 211.5s suite: 71 cases,
        # each copying the whole tree twice and starting two interpreters.
        # Running all 71 before every push is the cost; running none of them
        # is not an option, so this is the same three-tier shape Morgan
        # already directed for precedent_check.py on 2026-09-18
        # (_scoped_tree_slugs there), applied to the planted cases.
        #
        # WHAT ALWAYS RUNS, and each of these is load-bearing:
        #   - a check whose own practices/<slug>.md this change touched.
        #     Editing a rule without re-proving its check still fires is
        #     the exact hole this whole function exists to close.
        #   - ANY case whose recorded output a later assertion in this file
        #     reads back out of `planted[...]`. Those are derived from this
        #     file's own source below rather than kept as a hand-list,
        #     because a hand-list drifts the first time somebody adds a
        #     deeper assertion, and the failure would be a KeyError in an
        #     unrelated case months later.
        #   - EVERYTHING, when the change touches the check machinery
        #     itself (tools/precedent_check.py, this file, or a
        #     tools/checks/ script). A change there can alter any check's
        #     behaviour, so no rotation slice is a safe sample of it.
        #
        # The rest rotate deterministically by commit count, so ten
        # consecutive commits cover the whole set exactly once each -- not
        # "probably", the same guarantee _scoped_tree_slugs gives.
        #
        # --all, or PRECEDENT_HARNESS_ALL=1, forces the full set. CI sets
        # it: a gate that runs a tenth of itself is right for a push a
        # person is standing at, and wrong for the run nobody is watching.
        _all_case_slugs = _registry_slugs()
        if _all_case_slugs:
            _selected, _selection_reason = _selected_case_slugs(_all_case_slugs)
        else:
            _selected, _selection_reason = None, 'all (the registry could not be read)'

        # ONE CLEAN RUN SERVES EVERY PLAIN CASE (2026-10-31). Each case used
        # to check its own unplanted copy as well -- a second tree copy and
        # a second interpreter per case, about 130 of each, on a tree the
        # baseline below checks anyway. When every case runs, the baseline
        # is a --full-sweep (bare, it runs only a rotation slice of the tree
        # checks), and a case with no setup=, extra= or env_extra= -- whose
        # clean run would be `--only SLUG` on that same tree -- reads its
        # slug's verdict out of it (_clean_from_baseline). A slug the sweep
        # does not show clean, or any output the sweep cannot attribute to
        # one slug, is checked again on its own copy exactly as before, so a
        # failure reads the same as it always did. A rotated run keeps the
        # bare baseline and the per-case clean runs: a whole sweep there
        # would cost more than the few clean runs it saves.
        _shared_clean = (_selected is None
                         or set(_all_case_slugs) <= set(_selected))

        # --- the baseline must be clean, or every case below is meaningless
        base = fresh('baseline')
        # The same isolation run() applies (fixture-owns-its-state): no
        # PRECEDENT_COMMIT_*, and no user-level config to reach the person's
        # own individual set. With either, the commit-author check failed
        # this baseline on the fixture's own `harness` commit (2026-10-10,
        # once a change touching the check machinery made every check run
        # here).
        _env = {k: v for k, v in os.environ.items()
                if k not in ('PRECEDENT_COMMIT_NAME', 'PRECEDENT_COMMIT_EMAIL',
                             'PRECEDENT_COMMIT_TZ', 'PRECEDENT_LEAK_BLOCKLIST')}
        _env['PRECEDENT_USER_CONFIG'] = str(base / '.no-user-config.json')
        # Started here and read just before the closing assertions (or by
        # the first plain case's clean verdict): a bare run takes about 30 s,
        # a full sweep about a minute, and nothing between reads its result.
        _baseline = subprocess.Popen(
            [sys.executable, str(base / 'tools' / 'precedent_check.py'),
             *(['--full-sweep'] if _shared_clean else [])],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            cwd=str(base), env=_env)
        _baseline_read = []

        def _baseline_result():
            if not _baseline_read:
                out, _ = _baseline.communicate()
                _baseline_read.append((_baseline.returncode, out))
            return _baseline_read[0]

        # --- one planted violation per enforced practice --------------------
        # SEVERAL CASES IN FLIGHT (2026-10-11). case() starts its two
        # processes and returns; the result is collected the first time
        # anything reads planted[slug] (or `in`, .get, .items), and every
        # case still pending is collected before the closing assertions.
        # So a later assertion that reads a case back blocks until that
        # case is done, without anyone listing which cases are read --
        # sketch (a) of spec/VERIFY_HARNESS_PERFORMANCE.md's 2026-09-19
        # follow-ups. Two at a time used about one core of four; the width
        # stays bounded, because a fan-out with no bound ran a container out
        # of memory once (gotcha-2026-09-18).
        _pending = {}
        _width = max(1, ((os.cpu_count() or 2) + 2) // 2)
        # The bound is on processes, not cases: a plain case starts one, a
        # case with its own clean run two, and twice _width processes was
        # always the most in flight.
        _weight = {}
        _deferred = {}            # slug -> index in cases of its clean case

        def _drain(slug):
            _weight.pop(slug, None)
            _pending.pop(slug)()

        class _Planted(dict):
            def _settle(self, key):
                slug = key[:-len('-clean')] if key.endswith('-clean') else key
                for k in (key, slug):
                    if k in _pending:
                        _drain(k)
                if key.endswith('-clean') and slug in _deferred:
                    # Read back before the sweep is done (one assertion
                    # reads generated-edit-goes-upstream's clean output
                    # early): its own copy now, rather than every case
                    # after it waiting about a minute for the sweep.
                    _clean_from_baseline(slug, wait=False)

            def settle_all(self):
                while _pending:
                    _drain(next(iter(_pending)))
                for slug in list(_deferred):
                    _clean_from_baseline(slug)

            def __getitem__(self, key):
                self._settle(key)
                return dict.__getitem__(self, key)

            def __contains__(self, key):
                self._settle(key)
                return dict.__contains__(self, key)

            def get(self, key, default=None):
                self._settle(key)
                return dict.get(self, key, default)

            def items(self):
                self.settle_all()
                return dict.items(self)

        planted = _Planted()
        declared = set()          # every slug case() was ASKED for
        ran, skipped = [], []     # and which of those actually executed


        # case()'s two sub-runs -- the planted fixture and the clean fixture
        # -- are provably independent: different directories, no shared
        # state, and nothing outside case() reads either one until both
        # are done. That makes them safe to run as two real OS processes
        # instead of one after another. Threads were tried for this exact
        # spot before (2026-09-16, see spec/VERIFY_HARNESS_PERFORMANCE.md)
        # and again today, and both times measured no reliable win or an
        # active loss -- this container's `shutil.copytree` does not
        # parallelize across Python threads. Real processes are different:
        # benchmarked directly today, 8 independent (copytree + subprocess)
        # pipelines launched as separate `multiprocessing.Process` workers
        # finished in ~1/3 the time of running them one at a time, with
        # identical results. `ProcessPoolExecutor`/`multiprocessing.Pool`
        # don't fit here -- their workers receive tasks by pickling them
        # through a queue, and `plant`/`setup` are local closures, which
        # can't be pickled. `multiprocessing.Process` forks directly from
        # the point in the code where the closure already exists in memory,
        # so no pickling of the closure itself is needed -- only the
        # (rc, out) result has to come back, and that's a plain int and str.
        def _case_worker(fn, q):
            # A plant()/setup() that raises today fails the whole check
            # loudly, which is correct -- a case that can't even build its
            # fixture is itself a bug. In a child process an uncaught
            # exception would otherwise just kill that process silently;
            # the parent's queue.get() would hang forever waiting for a
            # result that is never coming. Catch it here and forward it
            # instead, so the parent can re-raise and keep that behavior.
            try:
                q.put(('ok', fn()))
            except BaseException as e:
                q.put(('error', e))

        def case(slug, plant, extra=(), setup=None, advisory=False,
                 env_extra=None):
            # DECLARED is recorded before the rotation decision, and is what
            # the untested-claim assertion at the end of this function reads.
            # A case that this invocation did not RUN is still a case this
            # file HAS -- conflating the two would turn the rotation into a
            # report that the registry is missing coverage it actually has.
            declared.add(slug)
            if _selected is not None and slug not in _selected:
                skipped.append(slug)
                return
            ran.append(slug)

            def _planted_pipeline():
                repo = fresh(slug)
                if setup:
                    setup(repo)
                if plant:
                    plant(repo)
                result = run(repo, slug, *extra, env_extra=env_extra)
                # Deleted here, while it is one tree among a few: left for
                # the closing rmtree, about 270 trees took 108 s to delete
                # at once on one core (measured 2026-10-11).
                shutil.rmtree(repo, ignore_errors=True)
                return result

            def _clean_pipeline():
                clean = fresh(slug + '-clean')
                if setup:
                    setup(clean)
                result = run(clean, slug, *extra, env_extra=env_extra)
                shutil.rmtree(clean, ignore_errors=True)
                return result

            plain = _shared_clean and setup is None and not extra and not env_extra
            q1, q2 = multiprocessing.Queue(), multiprocessing.Queue()
            p1 = multiprocessing.Process(target=_case_worker, args=(_planted_pipeline, q1))
            p2 = None if plain else multiprocessing.Process(
                target=_case_worker, args=(_clean_pipeline, q2))
            w = 1 if plain else 2
            while _pending and sum(_weight.values()) + w > 2 * _width:
                _drain(next(iter(_pending)))
            p1.start()
            if p2:
                p2.start()
            _weight[slug] = w
            _pending[slug] = lambda: _collect(slug, advisory, q1, q2, p1, p2)

        def _collect(slug, advisory, q1, q2, p1, p2):
            status1, value1 = q1.get()
            status2, value2 = q2.get() if p2 else ('ok', None)
            p1.join()
            if p2:
                p2.join()
            if status1 == 'error':
                raise value1
            if status2 == 'error':
                raise value2
            rc, out = value1

            planted[slug] = (rc, out)
            if advisory:
                # advisory=True means a planted violation still reports its
                # findings, labeled ADVISORY, but does not fail the run (rc
                # stays 0). precedent_check.check() still offers the parameter;
                # as of 2026-09-06 no check uses it (parallel-artifact-ledger,
                # the only one that ever did, is enforcing again), so this
                # branch is dormant rather than dead -- kept so downgrading a
                # check stays a one-word change with test support already
                # there, not a silent loss of coverage. (Live again since
                # 2026-09-06: layered-practice-packs' reachability check is
                # advisory, because closing its findings is an architectural
                # decision a check cannot make -- see its own registration.)
                cases.append((f'{slug}: a planted violation reports ADVISORY '
                              f'but does not fail the check',
                              rc == 0 and 'ADVISORY' in out and 'VIOLATION' not in out))
            else:
                cases.append((f'{slug}: a planted violation fails the check',
                              rc == 1 and 'VIOLATION' in out))
            if p2 is None:
                # Its place in `cases` is kept; the shared baseline fills it.
                _deferred[slug] = len(cases)
                cases.append((f'{slug}: the same tree unplanted does not', False,
                              'not yet read from the shared baseline'))
                return
            _clean_case(slug, *value2)

        def _clean_case(slug, rc2, out2, at=None):
            planted[slug + '-clean'] = (rc2, out2)
            stated = (f'{slug}: the same tree unplanted does not',
                      rc2 == 0 and 'VIOLATION' not in out2 and 'ADVISORY' not in out2)
            if at is None:
                cases.append(stated)
            else:
                cases[at] = stated

        _HEADER = re.compile(r'^(VIOLATION|ADVISORY|ERROR|SKIPPED|COULD NOT VERIFY'
                             r'|EXEMPT)\s+(\S+)')
        _by_slug = []

        def _baseline_by_slug():
            """-> ({slug: its lines of the shared sweep}, whether anything
            in the sweep could not be put down to one slug). A section is a
            header naming the slug and the indented lines under it; what is
            left over may say VIOLATION or ADVISORY only if no slug's own
            run would have, and a sweep that never reached its summary line
            is all left over."""
            if not _by_slug:
                _rc, out = _baseline_result()
                sections, rest, cur = {}, [], None
                for line in out.splitlines():
                    m = _HEADER.match(line)
                    if m:
                        cur = sections.setdefault(m.group(2), [])
                        cur.append(line)
                    elif cur is not None and line.startswith((' ', '\t')):
                        cur.append(line)
                    else:
                        cur = None
                        rest.append(line)
                rest = '\n'.join(rest)
                unattributed = ('VIOLATION' in rest or 'ADVISORY' in rest
                                or not re.search(r'^precedent_check: \d+ passed', rest, re.M))
                _by_slug.append(({k: '\n'.join(v) for k, v in sections.items()},
                                 unattributed))
            return _by_slug[0]

        def _clean_from_baseline(slug, wait=True):
            """The clean case of a plain slug, from the shared sweep: what
            `--only SLUG` on the same tree would have said. Run on its own
            copy instead when the sweep shows it anything but clean, or
            holds something it cannot attribute -- the old path, so its
            failure detail is the old one."""
            at = _deferred.pop(slug)
            if not wait and not _baseline_read and _baseline.poll() is None:
                sections, unattributed = {}, True
            else:
                sections, unattributed = _baseline_by_slug()
            mine = sections.get(slug, '')
            failing = re.search(r'^(VIOLATION|ADVISORY|ERROR)\s', mine, re.M)
            if unattributed or failing or 'VIOLATION' in mine or 'ADVISORY' in mine:
                clean = fresh(slug + '-clean')
                rc2, out2 = run(clean, slug)
                shutil.rmtree(clean, ignore_errors=True)
            else:
                rc2, out2 = 0, mine
            _clean_case(slug, rc2, out2, at=at)

        # cite-the-incident -- a new practice with no ## Story
        def _plant_cite(repo):
            (repo / 'practices' / 'zzz-new-rule.md').write_text(
                '---\nslug:        zzz-new-rule\ntitle:       A new rule\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "testing"\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nsupersedes:  []\n'
                'overrides:   null\nadded:       null\n'
                'approved_by: "harness"\nsource_practice_number: 999\n---\n\n'
                '## Rule\nDo the thing.\n\n## Detail\n\n## Why\nBecause.\n\n'
                '## Story\n\n## Install\nNone.\n', encoding='utf-8')
        case('cite-the-incident', _plant_cite)

        # catalogue-carries-stories -- an EXISTING active practice whose
        # Story is emptied. Deliberately not a new file: cite-the-incident
        # above already covers the new-practice case, and the whole reason
        # this check exists is the case that one cannot see -- a gap sitting
        # in the tree that no commit touches again.
        def _plant_catalogue_stories(repo):
            f = repo / 'practices' / 'orientation-map.md'
            body = f.read_text(encoding='utf-8')
            start = body.index('## Story')
            end = body.index('## Install', start)
            f.write_text(body[:start] + '## Story\n\n' + body[end:],
                         encoding='utf-8')
        case('catalogue-carries-stories', _plant_catalogue_stories)

        def _plant_retired_branch_name(repo):
            f = repo / 'practices' / 'name-both-sides-of-ledger.md'
            body = f.read_text(encoding='utf-8')
            f.write_text(re.sub(r'^index_clause: "', 'index_clause: "on precedent-beta-v01, ',
                                body, count=1, flags=re.M), encoding='utf-8')
        case('retired-branch-name-ships', _plant_retired_branch_name)

        # default-branch: `origin` is a local bare repository whose HEAD is
        # `trunk`. The clean copy has no remote at all, which the check
        # reports as skipped -- never a violation.
        def _plant_default_branch(repo):
            bare = repo.parent / (repo.name + '-remote.git')
            subprocess.run(['git', 'init', '-q', '--bare', '-b', 'trunk', str(bare)],
                           capture_output=True, check=True)
            git(repo, 'push', '-q', str(bare), 'HEAD:refs/heads/trunk')
            git(repo, 'remote', 'add', 'origin', str(bare))
        case('default-branch', _plant_default_branch)

        # pending-approval-outlives-its-merge: origin's `staging`, the base
        # this repo declares, holds the baseline. A practice already there
        # says approved_by "pending PR review" -- its pull request merged,
        # the placeholder stayed -- and a practice the change ADDS says it
        # too, which is right while its own pull request is open. The clean
        # copy has no remote, which the check reports as skipped.
        def _plant_pending_approval(repo):
            bare = repo.parent / (repo.name + '-remote.git')
            subprocess.run(['git', 'init', '-q', '--bare', str(bare)],
                           capture_output=True, check=True)
            git(repo, 'push', '-q', str(bare), 'HEAD:refs/heads/staging')
            git(repo, 'remote', 'add', 'origin', str(bare))
            git(repo, 'fetch', '-q', 'origin')
            pending = ('approved_by: "pending PR review -- drafted 2026-10-05 '
                       'by Pat, moved from the shared set zz-set"')
            rewrite(repo, 'practices/repo-is-memory.md',
                    lambda t: re.sub(r'^approved_by: .*$', pending, t,
                                     count=1, flags=re.M))
            (repo / 'practices' / 'zzz-moved-in.md').write_text(
                '---\nslug:        zzz-moved-in\napproved_by: "(pending PR '
                'review)"\n---\n\n## Rule\nMoved in by this change.\n',
                encoding='utf-8')
        case('pending-approval-outlives-its-merge', _plant_pending_approval)
        if 'pending-approval-outlives-its-merge' in planted:
            _pa = planted['pending-approval-outlives-its-merge'][1]
            cases.append(('pending-approval-outlives-its-merge: the finding '
                          'names the practice already on the base branch, '
                          'never the one the change adds',
                          'practices/repo-is-memory.md' in _pa
                          and 'zzz-moved-in' not in _pa))

        # universal-dedup-lands-in-universal: a universal stub hand-pointed
        # at a slug only a set carries (2026-10-17 very deep check), and a
        # second one carrying the move tool's --accept-reach-loss line,
        # which must stay clean.
        def _plant_universal_dedup_nowhere(repo):
            rewrite(repo, 'practices/brief-it.md',
                    lambda t: re.sub(r'^in_force_at:.*$',
                                     'in_force_at:       zz-set-only-rule', t,
                                     count=1, flags=re.M))
            rewrite(repo, 'practices/session-text.md',
                    lambda t: re.sub(r'^in_force_at:.*$',
                                     'in_force_at:       zz-other-set-rule', t,
                                     count=1, flags=re.M).replace(
                        '\n## Install', '\nWithdrawn from universal on '
                        '2026-10-17, deliberately, with --accept-reach-loss '
                        '(approved by Pat): deduplicated here; the rule is in '
                        'force only from the shared set `zz-set` now. A '
                        'consumer resolving only universal no longer gets '
                        'it.\n\n## Install', 1))
        case('universal-dedup-lands-in-universal', _plant_universal_dedup_nowhere)
        if 'universal-dedup-lands-in-universal' in planted:
            _ud = planted['universal-dedup-lands-in-universal'][1]
            cases.append(('universal-dedup-lands-in-universal: the hand stub is '
                          'refused, the one carrying the --accept-reach-loss '
                          'line is not', 'practices/brief-it.md' in _ud
                          and 'practices/session-text.md' not in _ud))

        # session-trailer: the baseline commit carries an explicit "none
        # available" trailer; the plant adds one commit with no trailer at
        # all. The check ships with the engine since 2026-10-06.
        def _plant_session_trailer(repo):
            (repo / 'zz-no-trailer.txt').write_text('x\n', encoding='utf-8')
            git(repo, 'add', 'zz-no-trailer.txt')
            git(repo, 'commit', '-qm', 'a commit with no session trailer')
        case('session-trailer', _plant_session_trailer)

        # derived-file-marker: a tracked file claims `DERIVED from ... @ sha`
        # on its first line and carries none of the other three lines.
        def _plant_derived_file_marker(repo):
            f = repo / 'zz-derived.txt'
            f.write_text('# DERIVED from practices/ @ 0123abc\n\nbody\n',
                         encoding='utf-8')
            git(repo, 'add', 'zz-derived.txt')
        case('derived-file-marker', _plant_derived_file_marker)

        # deep-check: a run_all.sh that globs test_*.sh, beside a check
        # script with no test. The clean copy has no run_all.sh and
        # declares itself a source, which the check skips.
        def _plant_deep_check(repo):
            tests = repo / 'tools' / 'checks' / 'tests'
            tests.mkdir(parents=True, exist_ok=True)
            (tests / 'run_all.sh').write_text(
                '#!/bin/bash\nfor t in "$(dirname "$0")"/test_*.sh; do bash "$t"; done\n',
                encoding='utf-8')
            (repo / 'tools' / 'checks' / 'check_zz_untested.py').write_text(
                'import os, pathlib\n'
                'SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent\n'
                'ROOT = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT") or SOURCE_ROOT)\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
        case('deep-check', _plant_deep_check)

        # light-check: one of each thing the audit exists to catch. The
        # marker and the token are assembled here, never spelled out, or
        # this file would be the finding on the real tree.
        def _plant_light_check(repo):
            (repo / 'zz-conflict.txt').write_text(
                'a\n' + '<' * 7 + ' HEAD\nb\n', encoding='utf-8')
            (repo / 'zz-token.txt').write_text(
                'token = ' + 'gh' + 'p_' + 'A' * 36 + '\n', encoding='utf-8')
            (repo / 'zz-broken.json').write_text('{"a": 1,}\n', encoding='utf-8')
            (repo / 'zz-links.md').write_text(
                'See [nothing](zz-no-such-file.md).\n\n'
                '`[an example](not-a-link.md)` is code, not a link.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
        case('light-check', _plant_light_check)

        # private-repo-scrub: a private individual set, brought through the
        # person's own config, whose origin is zz-owner/zz-private. The
        # clean copy has it in force and does not name it -- a real pass,
        # not a skip; the planted copy names it in a practice file.
        _priv = tmp / 'zz-private-set'
        (_priv / 'practices').mkdir(parents=True)
        (_priv / 'precedent-source.json').write_text(json.dumps(
            {'name': 'precedent-individual', 'level': 'individual',
             'visibility': 'private'}), encoding='utf-8')
        git(_priv, 'init', '-q')
        git(_priv, 'remote', 'add', 'origin', 'https://github.com/zz-owner/zz-private.git')
        _priv_cfg = tmp / 'zz-user-config.json'
        _priv_cfg.write_text(json.dumps(
            {'format_version': 1, 'individual': {'name': 'precedent-individual',
                                                 'path': str(_priv)}}),
            encoding='utf-8')

        def _plant_private_repo_scrub(repo):
            f = repo / 'practices' / 'repo-is-memory.md'
            f.write_text(f.read_text(encoding='utf-8').replace(
                '## Story\n', '## Story\nFirst seen in zz-owner/zz-private.\n', 1),
                encoding='utf-8')
        case('private-repo-scrub', _plant_private_repo_scrub,
             env_extra={'PRECEDENT_USER_CONFIG': str(_priv_cfg)})
        cases.append(('private-repo-scrub: the finding names the private repository',
                      "'zz-owner/zz-private'" in planted['private-repo-scrub'][1]))
        _lc = planted['light-check'][1]
        for _what, _needle in (('conflict marker', 'zz-conflict.txt:2: unresolved conflict marker'),
                               ('token', 'zz-token.txt: looks like a GitHub personal access token'),
                               ('JSON', 'zz-broken.json: not valid JSON'),
                               ('broken link', "zz-links.md:1: broken relative link to 'zz-no-such-file.md'")):
            cases.append((f'light-check: a planted {_what} is reported', _needle in _lc))
        cases.append(('light-check: a link inside a code span is not read as a link',
                      'not-a-link.md' not in _lc))

        # set-words-stay-in-their-set: a made-up set declared beside the copy
        # owns the words "Zorpify" and "phase N of 9"; one is planted in a
        # universal practice's Rule. No person's config is read, so only the
        # made-up set's words are judged.
        def _owner_set(repo):
            owner = repo.parent / (repo.name + '-zz-owner-set')
            (owner / 'practices').mkdir(parents=True, exist_ok=True)
            (owner / 'precedent-source.json').write_text(json.dumps({
                'name': 'zz-owner-set', 'level': 'shared', 'provides': ['zz-cap'],
                'owned_words': {'patterns': [
                    {'kind': 'a zz command', 'regex': r'\bZorpify\b',
                     'matches': ['Zorpify'], 'never_matches': ['zorpify']},
                    {'kind': 'a zz step', 'regex': r'\bphase [1-9] of 9\b'}]}}),
                encoding='utf-8')
            git(owner, 'init', '-q')
            cfg_path = repo / 'precedent.json'
            cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
            cfg.setdefault('sources', []).append(
                {'name': 'zz-owner-set', 'level': 'shared', 'path': str(owner)})
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding='utf-8')

        def _plant_set_words(repo):
            f = repo / 'practices' / 'park-it.md'
            body = f.read_text(encoding='utf-8')
            f.write_text(body.replace('## Rule\n', '## Rule\n\nSay '
                                      '"Zorpify" at phase 3 of 9.\n', 1),
                         encoding='utf-8')
        case('set-words-stay-in-their-set', _plant_set_words, setup=_owner_set,
             env_extra={'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        # ladder-set-is-brought-not-declared: precedent.json declares a
        # sibling set whose precedent-source.json provides the ladder.
        def _plant_declared_ladder(repo):
            prov = repo.parent / f'{repo.name}-ladder-provider'
            (prov / 'practices').mkdir(parents=True, exist_ok=True)
            (prov / 'precedent-source.json').write_text(json.dumps(
                {'name': prov.name, 'level': 'shared', 'provides': ['ladder']}),
                encoding='utf-8')
            cfg_f = repo / 'precedent.json'
            cfg = json.loads(cfg_f.read_text(encoding='utf-8'))
            cfg.setdefault('sources', []).append(
                {'name': prov.name, 'level': 'shared', 'path': f'../{prov.name}'})
            cfg_f.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
        case('ladder-set-is-brought-not-declared', _plant_declared_ladder)

        # copied-in-set-fits-visibility: a private set copied into a
        # repository whose precedent.json does not say it is private.
        def _plant_private_copy(repo):
            copy = repo / 'process' / 'zz-private-set'
            (copy / 'practices').mkdir(parents=True, exist_ok=True)
            (copy / 'precedent-source.json').write_text(json.dumps(
                {'name': 'zz-private-set', 'level': 'shared',
                 'visibility': 'private'}), encoding='utf-8')
            cfg_f = repo / 'precedent.json'
            cfg = json.loads(cfg_f.read_text(encoding='utf-8'))
            cfg.pop('visibility', None)
            cfg.setdefault('sources', []).append(
                {'name': 'zz-private-set', 'level': 'shared',
                 'path': 'process/zz-private-set', 'vendored': True})
            cfg_f.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
        case('copied-in-set-fits-visibility', _plant_private_copy)

        # copied-in-folder-is-declared -- a folder a sync script copied in
        # (its .source-commit marker) that precedent.json does not declare
        # (Morgan, 2026-10-30).
        def _plant_undeclared_copy(repo):
            (repo / 'external' / 'zz-synced').mkdir(parents=True, exist_ok=True)
            (repo / 'external' / 'zz-synced' / '.source-commit').write_text(
                'abc\n', encoding='utf-8')
        case('copied-in-folder-is-declared', _plant_undeclared_copy)

        # universal-change-reaches-overrides -- a permanent warning: universal's
        # orientation-map changes below its frontmatter while a declared set
        # carries its own active copy of that slug (2026-10-05, the ladder
        # set's copies falling behind).
        def _plant_override_drift(repo):
            st = repo.parent / f'{repo.name}-override-set'
            (st / 'practices').mkdir(parents=True, exist_ok=True)
            (st / 'precedent-source.json').write_text(json.dumps(
                {'name': st.name, 'level': 'shared'}), encoding='utf-8')
            mine = repo / 'practices' / 'orientation-map.md'
            (st / 'practices' / 'orientation-map.md').write_text(
                mine.read_text(encoding='utf-8'), encoding='utf-8')
            cfg_f = repo / 'precedent.json'
            cfg = json.loads(cfg_f.read_text(encoding='utf-8'))
            cfg.setdefault('sources', []).append(
                {'name': st.name, 'level': 'shared', 'path': f'../{st.name}'})
            cfg_f.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
            mine.write_text(mine.read_text(encoding='utf-8')
                            + '\nA planted change to universal\'s copy.\n',
                            encoding='utf-8')
        case('universal-change-reaches-overrides', _plant_override_drift,
             advisory=True)

        # bound-set-tool-calls-only-declared-names -- a set's bound tool
        # reads an engine name the engine does not declare for its key.
        def _bound_tool_setup(repo):
            src_f = repo / 'precedent-source.json'
            src = json.loads(src_f.read_text(encoding='utf-8'))
            src['branch_moves'] = 'tools/zz_moves.py'
            src_f.write_text(json.dumps(src, indent=2), encoding='utf-8')
            (repo / 'tools' / 'zz_moves.py').write_text(
                'core = None\n\ndef bind(engine):\n    global core\n'
                '    core = engine\n\ndef main():\n    return core.MAIN\n',
                encoding='utf-8')

        def _plant_undeclared_engine_call(repo):
            f = repo / 'tools' / 'zz_moves.py'
            f.write_text(f.read_text(encoding='utf-8').replace(
                'core.MAIN', 'core.zz_never_declared()'), encoding='utf-8')
        case('bound-set-tool-calls-only-declared-names', _plant_undeclared_engine_call,
             setup=_bound_tool_setup)

        # reply-rules-hold-their-examples / reply-rules-carry-examples -- a
        # requirement whose example the reply check answers otherwise, and
        # one with no examples at all.
        def _reply_examples_setup(repo):
            (repo / 'reply_check.json').write_text(json.dumps([
                {'practice': 'zz', 'require_one_of': ['ZZ-OK'],
                 '_examples': [{'reply': 'done. ZZ-OK', 'refused': False},
                               {'reply': 'done.', 'refused': True}]}]),
                encoding='utf-8')

        def _plant_wrong_example(repo):
            f = repo / 'reply_check.json'
            f.write_text(f.read_text(encoding='utf-8').replace(
                '"refused": true', '"refused": false'), encoding='utf-8')
        case('reply-rules-hold-their-examples', _plant_wrong_example,
             setup=_reply_examples_setup)

        def _plant_no_examples(repo):
            f = repo / 'reply_check.json'
            reqs = json.loads(f.read_text(encoding='utf-8'))
            reqs.append({'practice': 'zz2', 'require_one_of': ['ZZ2']})
            f.write_text(json.dumps(reqs), encoding='utf-8')
        case('reply-rules-carry-examples', _plant_no_examples,
             setup=_reply_examples_setup, advisory=True)

        # todo-is-a-handoff -- a line added to an open item that leaves work
        # undone names nothing blocking it (2026-10-20: "Not built." in an
        # item's notes, with nothing blocking it).
        def _plant_gap_without_reason(repo):
            (repo / 'todo' / 'todo-2026-10-20-planted-gap.md').write_text(
                '---\nstatus: open\n---\n## What\nThe second half: not built.\n',
                encoding='utf-8')
        case('todo-is-a-handoff', _plant_gap_without_reason)

        # no-duplication -- in a practice SET, an active practice whose slug
        # its declared universal source also has active is refused (Morgan,
        # 2026-10-06: "rules should not be repeated, but supporting repos can
        # have additions for them"). The fixture is universal's own tree, so
        # the setup makes it a set beside a small universal that shares
        # nothing with it; the plant gives that universal one of its slugs.
        def _setup_set_beside_universal(repo):
            uni = repo.parent / f'{repo.name}-dup-universal'
            (uni / 'practices').mkdir(parents=True, exist_ok=True)
            (uni / 'precedent-source.json').write_text(json.dumps(
                {'name': 'precedent', 'level': 'universal'}), encoding='utf-8')
            (uni / 'practices' / 'zz-only-in-universal.md').write_text(
                '---\nslug: zz-only-in-universal\nstatus: active\n---\n', encoding='utf-8')
            src = json.loads((repo / 'precedent-source.json').read_text(encoding='utf-8'))
            src['level'] = 'shared'
            (repo / 'precedent-source.json').write_text(json.dumps(src), encoding='utf-8')
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
                {'format_version': 1, 'kind': 'source', 'files': []}), encoding='utf-8')
            cfg_f = repo / 'precedent.json'
            cfg = json.loads(cfg_f.read_text(encoding='utf-8'))
            cfg['sources'] = [{'name': 'precedent', 'level': 'universal',
                               'path': f'../{uni.name}'}]
            cfg_f.write_text(json.dumps(cfg, indent=2), encoding='utf-8')

        def _plant_set_copy(repo):
            uni = repo.parent / f'{repo.name}-dup-universal'
            (uni / 'practices' / 'orientation-map.md').write_text(
                (repo / 'practices' / 'orientation-map.md').read_text(encoding='utf-8'),
                encoding='utf-8')
        case('no-duplication', _plant_set_copy, setup=_setup_set_beside_universal)

        # frontmatter-field-order -- a permanent warning (practice:
        # format-rules-grandfather): a planted misorder is reported, and
        # never fails the run.
        def _plant_field_order(repo):
            f = repo / 'practices' / 'name-both-sides-of-ledger.md'
            body = f.read_text(encoding='utf-8')
            line = re.search(r'^index_clause:.*\n', body, re.M).group(0)
            body = body.replace(line, '', 1)
            f.write_text(body.replace('---\n', '---\n' + line, 1), encoding='utf-8')
        case('frontmatter-field-order', _plant_field_order, advisory=True)

        # generated-edit-goes-upstream -- four shapes in one fixture, told
        # apart by the messages below rather than by the exit status
        # (practice: control-asserts-which-failure). MAP.md loses its
        # `Source:` clause entirely, which is the header every generated view
        # here carried until 2026-09-11 and the one that produces the hand
        # edit; GLOSSARY.md keeps a clause and points it at a directory that
        # does not exist, which is the worse case -- it reads as an answer.
        #
        # The other two headers are CORRECT, and the check reported both as
        # violations until 2026-09-11 -- one per fault in the terminator
        # `_SOURCE_CLAUSE_RE` used to carry, found from a consuming repo by a
        # session trying to COMPLY with the rule. They are cases rather than
        # a comment because both faults produced a message pointing at the
        # wrong problem, so a regression looks like a pass to anybody reading
        # the exit status: the hyphen fault reported a clause sitting in the
        # header as missing, and the extension fault reported a path that
        # exists as gone.
        _SOURCE_OK = (
            # A hyphenated path. `[^-]+?` could not cross the hyphen, so the
            # clause did not match AT ALL and the file was reported as
            # carrying no `Source:` clause -- and most real paths in these
            # repos are hyphenated, so this was the common case.
            ('fixture-hyphenated-source.md',
             'Source: practices/generated-edit-goes-upstream.md -- the '
             'practice this header exists to satisfy.'),
            # A hyphen-free path, so this case isolates the second fault: `\.`
            # in the terminator truncated at the extension, and the clause was
            # reported as naming `spec/LOADER`, which does not exist.
            ('fixture-dotted-source.md',
             'Source: spec/LOADER.md -- the loader spec.'),
        )

        # A MIRRORED artifact: built in another repo, copied in here, so its
        # source is a path this repo does not have and never will. Three
        # wordings were tried from a consuming repo on 2026-09-12 and all
        # three were refused -- no clause, the source's own in-repo paths
        # (reported as a Source that had MOVED), and a URL (reported as
        # naming no path). This is the fourth.
        #
        # Its own category, NOT a member of _SOURCE_OK above, and the
        # distinction is the whole design: those two are correct AND fully
        # resolvable here, so the check says nothing about them at all. This
        # one is correct and NOT resolvable here, so the check has to say so
        # -- reported, and not as a violation. Filing it with the silent ones
        # asserted exactly the silence this change exists to prevent.
        _SOURCE_MIRRORED = (
            ('fixture-qualified-source.md',
             'Source (in the Voice pack): voice/, examples/ and prompt/ -- '
             'built there and mirrored here.'),
        )

        # The shapes a qualified Source must NOT let through. Each is a way
        # of saying "somewhere else" that leaves the reader with nothing to
        # open, which is the failure the whole clause exists to prevent --
        # and the escape hatch the parenthetical would otherwise be.
        _SOURCE_BAD = (
            ('fixture-bare-url-source.md',
             'Source: https://example.invalid/acct/Pack -- built there.'),
            ('fixture-empty-place-source.md',
             'Source (): voice/ -- mirrored here.'),
            ('fixture-placeless-source.md',
             'Source (in the Voice pack): the pack itself -- mirrored here.'),
        )

        # The `evals/` exclusion, which is a PATH SEGMENT test rather than an
        # `evals/` PREFIX test because this engine is VENDORED: in a consuming
        # repo this whole tree, evals/ included, sits under a mirror prefix,
        # so a prefix test matches nothing there. On 2026-09-12 a consumer's
        # run reported 26 of these recorded eval prompts as violations at
        # `<mirror>/evals/...` -- every one a false positive, and none of them
        # fixable there, since a vendored tree has to stay byte-identical to
        # the commit it mirrors.
        #
        # One file per shape, and each one fails a DIFFERENT wrong test.
        # Measured against this tree, 2026-09-12:
        #   * the mirror path is the regression witness -- restore the
        #     `startswith('evals/')` test and it alone goes red, which is the
        #     consumer's 26 false positives reproduced in one file;
        #   * the root path guards the other direction, that the fix did not
        #     stop excluding what the prefix test correctly excluded;
        #   * `my-evals/` fails a naive `'evals/' in rel` (that substring sits
        #     inside `my-evals/`), and `evals-notes/` fails a naive
        #     `'evals' in rel`.
        # The two that must be REPORTED are also what keeps the two that must
        # be SILENT honest: if these fixture files never reached the check at
        # all, the silent pair would pass vacuously while the reported pair
        # went red.
        _EVALS_EXCLUDED = (
            'evals/fixture-eval-at-root.md',
            'process/upstream/evals/fixture-eval-under-mirror.md',
        )
        _EVALS_REPORTED = (
            'evals-notes/fixture-eval-suffix-dir.md',
            'my-evals/fixture-eval-prefix-dir.md',
        )

        def _plant_generated_source(repo):
            # MAP.md and GLOSSARY.md open with a generated_by label since
            # 2026-09-29 rather than a comment, so the header with no clause
            # and the one naming a moved directory are planted in files of
            # their own (assembled, for the reason given in the loop below).
            _m = 'do not ' + 'hand-edit'
            (repo / 'planted-no-source.md').write_text(
                f'<!-- GENERATED by the harness -- {_m}. -->\n',
                encoding='utf-8')
            (repo / 'planted-moved-source.md').write_text(
                f'<!-- GENERATED by the harness -- {_m}. '
                f'Source: catalogue/entries/ -- the entries. -->\n',
                encoding='utf-8')
            for rel, clause in _SOURCE_BAD + _SOURCE_OK + _SOURCE_MIRRORED:
                # Assembled rather than written literally, for the reason the
                # leak-gate fixture above is: spelled out, the marker makes
                # THIS file match `_DONT_EDIT_RE`, and since the header here
                # is a template with no `Source:` in it, the check then
                # reports verify_harness.py as a generated view that does not
                # say where its content comes from. Caught by this fixture's
                # own unplanted baseline on 2026-09-11, which is what that
                # baseline is for.
                marker = 'do not ' + 'hand-edit'
                (repo / rel).write_text(
                    f'<!-- GENERATED by the harness -- {marker}. '
                    f'Regenerate with: nothing, this file is a fixture. '
                    f'{clause} -->\n', encoding='utf-8')
            # All four evals-scope files carry a header with NO `Source:`
            # clause, so an excluded path and a reported one are told apart
            # below BY NAME rather than by the exit status
            # (practice: control-asserts-which-failure) -- the exit status is
            # non-zero either way, since two of the four are meant to be
            # violations. Directories are created here because none of the
            # four exists in this tree.
            for rel in _EVALS_EXCLUDED + _EVALS_REPORTED:
                marker = 'do not ' + 'hand-edit'
                dest = repo / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(f'<!-- GENERATED by the harness -- {marker}. '
                                f'Regenerate with: nothing, this file is a '
                                f'fixture. -->\n', encoding='utf-8')
            # Tracked, or `git ls-files` never hands them to the check and
            # the cases below pass by never being looked at
            # (practice: fixture-owns-its-state).
            git(repo, 'add', '-A')
        case('generated-edit-goes-upstream', _plant_generated_source)
        _ges = planted['generated-edit-goes-upstream'][1]
        cases.append(('generated-edit-goes-upstream: the header with no clause '
                      'is reported as having none, not merely counted',
                      'no `Source:` clause' in _ges))
        cases.append(('generated-edit-goes-upstream: the clause pointing at a '
                      'directory that has moved names that directory',
                      'names `catalogue/entries/` as its Source and that path '
                      'does not exist' in _ges))
        for _rel, _clause in _SOURCE_OK:
            cases.append((f'generated-edit-goes-upstream: {_rel}, whose header '
                          f'is correct, is not reported at all',
                          _rel not in _ges))
        for _rel in _EVALS_EXCLUDED:
            cases.append((f'generated-edit-goes-upstream: {_rel} is excluded '
                          f'by its `evals` path SEGMENT -- at the root and '
                          f'under a vendoring mirror alike',
                          _rel not in _ges))
        for _rel in _EVALS_REPORTED:
            cases.append((f'generated-edit-goes-upstream: {_rel} is NOT '
                          f'excluded -- a directory that merely begins or '
                          f'ends with the word is an ordinary directory',
                          _rel in _ges))

        # The sharper half of the extension fault: its old message named a
        # path nobody wrote. A regression that truncated the clause again
        # would still be a finding about a header that is right.
        cases.append(('generated-edit-goes-upstream: a Source path is not '
                      'truncated at its file extension',
                      '`spec/LOADER`' not in _ges))

        # The mirrored case, both halves. It must not be a violation -- the
        # header is right and nobody holding the mirror can act on a finding
        # about it -- and it must not be silent either, which is the state a
        # plain exemption for mirrored files would have produced.
        cases.append(('generated-edit-goes-upstream: a Source qualified by '
                      'the place it lives in is not reported as a violation',
                      'fixture-qualified-source.md' not in
                      _ges.split('COULD NOT VERIFY')[0]))
        cases.append(('generated-edit-goes-upstream: ...and is reported as '
                      'COULD NOT VERIFY rather than passing silently',
                      'COULD NOT VERIFY' in _ges and
                      'fixture-qualified-source.md' in
                      _ges.split('COULD NOT VERIFY', 1)[1]))
        # Every token, not just the ones that fail to resolve. `examples/` is
        # a real directory in this repo and in plenty of others, so resolving
        # the tokens that happen to exist locally let a coincidence render
        # identically to a verification (practice: fail-gracefully, clause 1).
        cases.append(('generated-edit-goes-upstream: a qualified Source does '
                      'not silently verify a token against a same-named '
                      'local directory',
                      '`examples/` under `Source (in the Voice pack):`'
                      in _ges))
        # A could-not-verify is not a violation, so it must not turn the run
        # red on its own -- and `--strict` is where a caller says otherwise.
        _rc_uv, _out_uv = planted['generated-edit-goes-upstream-clean']
        cases.append(('generated-edit-goes-upstream: the unplanted tree has '
                      'nothing it could not verify, so the case above is '
                      'about the planted header and not about this repo',
                      _rc_uv == 0 and 'COULD NOT VERIFY' not in _out_uv))

        # The three ways of saying "somewhere else" that still leave a reader
        # with nothing to open. Named one at a time: the parenthetical is free
        # text, and a check that accepted any of these would have turned it
        # into a way of switching the rule off.
        cases.append(('generated-edit-goes-upstream: an unqualified `Source:` '
                      'naming a URL is told which form it wanted, not that it '
                      'named no path',
                      'naming a URL' in _ges and
                      'Source (in <place>): <path>' in _ges))
        cases.append(('generated-edit-goes-upstream: an empty parenthetical '
                      'names no place and is refused',
                      'has a `Source ():` clause with nothing in the '
                      'parentheses' in _ges))
        cases.append(('generated-edit-goes-upstream: a place with no address '
                      'inside it is refused',
                      'and then no address within it' in _ges))

        # And the terminator itself, per fault, so a regression is reported as
        # the regex being wrong rather than as a fixture file the check could
        # not read.
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_check as _pcsrc
        for _shape, _clause, _want in (
                ('a hyphenated path',
                 'Source: business-modeling/doc-recipes/OUT.recipe.md -- x',
                 'business-modeling/doc-recipes/OUT.recipe.md'),
                ('a path carrying an extension',
                 'Source: docs/plain.md -- fine', 'docs/plain.md')):
            _m = _pcsrc._SOURCE_CLAUSE_RE.search(_clause)
            cases.append((f'generated-edit-goes-upstream: {_shape} survives '
                          f'the Source-clause terminator whole',
                          _m is not None and _m.group('clause') == _want))
        # ...and the terminator still has to STOP. Widening it is what makes
        # the clause swallow the comment's prose, and every path-shaped word
        # in that prose is then checked as if the header had named it.
        _m = _pcsrc._SOURCE_CLAUSE_RE.search(
            'Source: practices/ -- edit tools/build_views.py instead -->')
        cases.append(('generated-edit-goes-upstream: the Source clause still '
                      'stops at the prose dash instead of swallowing the rest '
                      'of the comment',
                      _m is not None and _m.group('clause') == 'practices/'))
        # The parenthetical is optional, and adding it must not have changed
        # what an UNQUALIFIED clause means -- a regression here reads as every
        # correct header in every repo suddenly naming a place.
        _m = _pcsrc._SOURCE_CLAUSE_RE.search('Source: practices/ -- x')
        cases.append(('generated-edit-goes-upstream: an unqualified Source '
                      'still parses as having no place',
                      _m is not None and _m.group('place') is None))
        # A URL's own slashes are path-shaped. Read without stripping it
        # first, one URL becomes several imaginary directories, and the
        # message names paths nobody wrote -- the 2026-09-11 failure mode
        # exactly, one layer along.
        _c = 'Source (in the pack): https://example.invalid/a/b -- x'
        _m = _pcsrc._SOURCE_CLAUSE_RE.search(_c)
        _cl = _m.group('clause') if _m else ''
        cases.append(('generated-edit-goes-upstream: a URL in the clause is '
                      'read as one address, not as several paths',
                      _pcsrc._SOURCE_URL_RE.findall(_cl) == [
                          'https://example.invalid/a/b'] and
                      _pcsrc._SOURCE_PATH_RE.findall(
                          _pcsrc._SOURCE_URL_RE.sub(' ', _cl)) == []))

        # practice-links-travel -- all three shapes at once, in one existing
        # practice file: a relative link into a directory that does not
        # travel, an upstream URL on a branch this repo is not publishing
        # from, and an upstream URL naming a path that does not exist. One
        # planted file rather than three cases because `case()` keys its
        # fixture directory by slug; the three are told apart below by the
        # messages the check prints, not by the exit status
        # (practice: control-asserts-which-failure).
        def _plant_practice_links(repo):
            # A sibling practice that is NOT in force. It is WRITTEN here
            # rather than borrowed from the tree: pointing the link at
            # whichever real practice happens to carry a withdrawn status
            # today would make this control lapse silently the day somebody
            # changes that file's status, and a control that has stopped
            # testing reads exactly like one that is passing
            # (practice: fixture-owns-its-state).
            (repo / 'practices' / 'zzz-withdrawn.md').write_text(
                '---\nslug:        zzz-withdrawn\ntitle:       Withdrawn\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "testing"\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      deduplicated\n'
                'in_force_at: repo-is-memory\nsupersedes:  []\n'
                'overrides:   null\nadded:       null\n'
                'approved_by: "harness"\n---\n\n'
                '## Rule\nSee [s](zzz-withdrawn-two.md).\n\n'
                # A link that DOES fail the travel half -- the identical
                # shape planted into the active practice above, where it is
                # reported. Without it the "not reported" case below would
                # be asserting an absence nothing could have produced, which
                # passes forever and tests nothing
                # (practice: control-asserts-which-failure).
                '## Detail\nSee [x](../spec/LOADER.md).\n\n## Why\nBecause.'
                '\n\n## Story\nPlanted.\n\n## Install\nNone.\n',
                encoding='utf-8')
            (repo / 'practices' / 'zzz-withdrawn-two.md').write_text(
                '---\nslug:        zzz-withdrawn-two\ntitle:       Withdrawn\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "testing"\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      retired\n'
                'in_force_at: none\nsupersedes:  []\n'
                'overrides:   null\nadded:       null\n'
                'approved_by: "harness"\n---\n\n'
                '## Rule\nDo the thing.\n\n## Detail\n\n## Why\nBecause.'
                '\n\n## Story\nPlanted.\n\n## Install\nNone.\n',
                encoding='utf-8')
            # A DEDUPLICATED sibling whose in_force_at names its OWN slug:
            # the redundant-copy case, where another source carries the same
            # slug and materialization writes it at this very filename. The
            # link travels, and reporting it was a false positive that blocked
            # a real vendor update on 2026-09-14 (see the practice's Story).
            (repo / 'practices' / 'zzz-dedup-self.md').write_text(
                '---\nslug:        zzz-dedup-self\ntitle:       Dedup\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "testing"\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      deduplicated\n'
                'in_force_at: zzz-dedup-self\nsupersedes:  []\n'
                'overrides:   null\nadded:       null\n'
                'approved_by: "harness"\n---\n\n'
                '## Rule\nDo the thing.\n\n## Detail\n\n## Why\nBecause.'
                '\n\n## Story\nPlanted.\n\n## Install\nNone.\n',
                encoding='utf-8')
            f = repo / 'practices' / 'repo-is-memory.md'
            f.write_text(f.read_text(encoding='utf-8') +
                         '\nPlanted: [f](zzz-dedup-self.md), '
                         '\nPlanted: [a](../spec/LOADER.md), '
                         '[b](https://github.com/alex137/BestPractice/blob/'
                         'main/TODO.md), '
                         '[c](https://github.com/alex137/BestPractice/blob/'
                         'staging/no-such-planted-path.md), '
                         '[d](../tools/checks/check_not_here.py), '
                         '[e](zzz-withdrawn.md), '
                         '[g](zzz-in-another-set.md), '
                         '[h](https://github.com/example/other-set/blob/'
                         'main/practices/zzz-by-url.md), '
                         '[i](https://github.com/example/other-set/blob/'
                         'main/README.md).\n',
                         encoding='utf-8')
        # The fixture is a `git init` copy with no remote, and the
        # upstream-URL half of the check asks origin which repository this
        # is -- without this the two URL cases below would be skipped and
        # read as passing. (practice: fixture-owns-its-state)
        def _setup_origin(repo):
            git(repo, 'remote', 'add', 'origin',
                'https://github.com/alex137/BestPractice.git')
            # And a link to a source's own check script AND to the test that
            # proves it, in BOTH the planted and the clean tree. This is the
            # FALSE-POSITIVE direction, which is the one that matters most
            # here: the check shipped on 2026-09-11 without the check-script
            # clause at all, and then with one that matched `check_*.py` only
            # -- so a practice citing its own test still read as a violation.
            # Both shapes are what precedent_materialize.py actually copies.
            # The two files are CREATED, not just linked, because the check
            # requires the target to exist in the tree it is scanning; a
            # fixture that linked them without writing them would be asserting
            # the opposite of what it claims (practice: fixture-owns-its-state).
            d = repo / 'tools' / 'checks' / 'tests'
            d.mkdir(parents=True, exist_ok=True)
            (d.parent / 'check_x.py').write_text('# planted\n', encoding='utf-8')
            (d / 'test_x.sh').write_text('# planted\n', encoding='utf-8')
            f = repo / 'practices' / 'repo-is-memory.md'
            f.write_text(f.read_text(encoding='utf-8') +
                         '\nIts check: [check_x.py](../tools/checks/check_x.py), '
                         'proved by [test_x.sh](../tools/checks/tests/test_x.sh).\n',
                         encoding='utf-8')
        case('practice-links-travel', _plant_practice_links,
             setup=_setup_origin)

        # practice: practice-carries-its-files -- a practice promising
        # consumers a file this repository does not carry.
        def _plant_ship_missing(repo):
            f = repo / 'practices' / 'repo-is-memory.md'
            f.write_text(f.read_text(encoding='utf-8').replace(
                '\ndefines:', '\nships:       ["tools/not_shipped_here.py"]'
                '\ndefines:', 1), encoding='utf-8')
        case('practice-carries-its-files', _plant_ship_missing)
        if 'practice-carries-its-files' in planted:
            cases.append(('practice-carries-its-files: the finding names the '
                          'shipped file the repository does not carry',
                          'ships `tools/not_shipped_here.py`, which is not in '
                          'this repository'
                          in planted['practice-carries-its-files'][1]))
        _plt = planted['practice-links-travel'][1]
        cases.append(("practice-links-travel: a source's own check script is "
                      'not reported as failing to travel',
                      'check_x.py' not in planted['practice-links-travel'][1]))
        cases.append(("practice-links-travel: a source's own check-script TEST "
                      'is not reported as failing to travel',
                      'test_x.sh' not in planted['practice-links-travel'][1]))
        # ...and the other direction, which is what keeps the clause above
        # from being a blanket exemption for anything spelled like a check
        # script: a tools/checks/ link whose target is not in the tree is
        # still a dead link, and is still reported.
        cases.append(('practice-links-travel: a tools/checks/ link with no '
                      'such file in the tree is still reported',
                      'check_not_here.py' in planted['practice-links-travel'][1]))
        # A sibling link to a practice that lives in ANOTHER set is told to
        # become a backticked slug, never a URL: the URL advice is what put a
        # private set's name into a public one on 2026-09-23.
        _g = [l for l in _plt.splitlines() if 'zzz-in-another-set.md' in l]
        cases.append(('practice-links-travel: a link to a practice in another '
                      'set is told to use the backticked slug, not a URL',
                      bool(_g) and all('`zzz-in-another-set` in backticks' in l
                                       and 'https://' not in l for l in _g)))
        # ...and the same practice linked by URL straight into that other
        # set, which never passes through the dead-link case: reported, with
        # the same advice. A URL to any OTHER file in that repository is not
        # this rule's business and stays unreported.
        cases.append(('practice-links-travel: a URL to a practice in another '
                      'set is reported and told to use the backticked slug',
                      '`zzz-by-url` in backticks' in _plt))
        cases.append(('practice-links-travel: a URL to a non-practice file in '
                      'another repository is not reported',
                      _plt.count('by URL into example/other-set') == 1))
        for _frag, _what in (
                ('does not travel with this file', 'the relative link'),
                ('precedent.json declares', 'the wrong-branch URL'),
                ('no such path exists here', 'the dead-path URL'),
                ('`status: deduplicated`', 'the withdrawn sibling')):
            cases.append((f'practice-links-travel: {_what} is named in the '
                          f'finding, not merely counted', _frag in _plt))
        # The withdrawn-sibling half is the shape no check in this system
        # could see before 2026-09-14: the target file IS in practices/, so
        # every local check passes, and the link breaks only in the consumer,
        # which never receives the withdrawn file. The successor has to be
        # NAMED -- a finding that only says "this does not travel" sends the
        # reader back to the same dead file to work out what replaced it.
        cases.append(('practice-links-travel: a link to a withdrawn sibling '
                      'names the successor, not just the breakage',
                      'link `repo-is-memory.md` instead' in _plt))
        # ...and the opposite direction, which keeps the clause above from
        # reporting links nobody receives: neither a withdrawn practice nor
        # its target is materialized, so a link between two of them is sound.
        # ...and the opposite direction for the WITHDRAWN-SIBLING half
        # specifically: zzz-withdrawn.md links zzz-withdrawn-two.md, the
        # identical shape that IS reported from the active file above. Neither
        # file is materialized, so nothing a consumer receives is broken by
        # it. Asserting both halves in one case is what keeps it from passing
        # vacuously the day the planted link stops being planted.
        cases.append(('practice-links-travel: a withdrawn-sibling link FROM a '
                      'withdrawn practice is not reported, though the '
                      'identical shape in an active practice is',
                      'links `zzz-withdrawn-two.md`' not in _plt
                      and 'links `zzz-withdrawn.md`' in _plt))
        # The BOUNDARY of that silence, pinned deliberately: only the
        # withdrawn-sibling finding is suppressed. The travel half still
        # reports a non-travelling link in a withdrawn practice, exactly as it
        # did before 2026-09-14 -- this change narrows nothing that was
        # already enforced, and a future session widening the guard to the
        # whole check should have to change this line to do it.
        cases.append(('practice-links-travel: the travel half still reports a '
                      'non-travelling link in a WITHDRAWN practice',
                      'practices/zzz-withdrawn.md:' in _plt))
        # The deduplication case, and the reason this clause exists at all: a
        # sibling whose in_force_at names its OWN slug is redundant HERE and
        # in force elsewhere under that same slug, so the resolver writes the
        # surviving copy at the same practices/<slug>.md the link points at.
        # Asserting both halves keeps it from passing vacuously: the
        # different-slug case above must still be reported.
        cases.append(('practice-links-travel: a deduplicated sibling whose '
                      'in_force_at names its own slug is NOT reported, though '
                      'one naming a different slug is',
                      'links `zzz-dedup-self.md`' not in _plt
                      and 'links `zzz-withdrawn.md`' in _plt))

        # technical-describes-people -- a DIRECTORY named for a person's
        # skill level. The person-noun form (`nontechnical-contributor-*`)
        # is deliberately NOT planted here: it must stay silent, and the
        # unplanted baseline in this same table is what proves it does.
        def _plant_skill_label(repo):
            d = repo / 'templates' / 'nontechnical-thing'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'a.md').write_text('# planted\n', encoding='utf-8')
        case('technical-describes-people', _plant_skill_label)

        # no-version-suffix
        case('no-version-suffix',
             lambda repo: (repo / 'findings-v2.md').write_text('x\n', encoding='utf-8'))

        # filename-separator -- a directory that already holds `.md` files
        # using one separator gains one using the other. `decisions/` is
        # kebab throughout (dated slugs), so a snake sibling is the exact
        # shape the practice was raised about: two conventions, same kind of
        # file, same folder, nothing distinguishing them.
        case('filename-separator',
             lambda repo: (repo / 'decisions' / 'PLANTED_MIXED_NAME.md')
             .write_text('# planted\n', encoding='utf-8'))

        # practice-file-shape -- a practice whose Rule ends on a lead-in.
        def _plant_bad_shape(repo):
            f = repo / 'practices' / 'mistakes-become-rules.md'
            text = f.read_text(encoding='utf-8')
            f.write_text(text.replace('## Detail', 'Three steps:\n\n## Detail', 1),
                         encoding='utf-8')
        case('practice-file-shape', _plant_bad_shape)

        # routing-reason -- an on-demand practice loses its applies_to_why,
        # the state a second hand-kept routing list used to let through.
        def _plant_no_routing_reason(repo):
            f = repo / 'practices' / 'mistakes-become-rules.md'
            f.write_text('\n'.join(l for l in f.read_text(encoding='utf-8')
                                   .split('\n')
                                   if not l.startswith('applies_to_why:')),
                         encoding='utf-8')
        case('routing-reason', _plant_no_routing_reason)

        # retired-words -- live prose using a word our_language.json retired.
        case('retired-words',
             lambda repo: (repo / 'documentation' / 'PLANTED_RETIRED.md')
             .write_text('# Planted\n\nDeclare the team source here.\n',
                         encoding='utf-8'))

        # upstream-fix -- a NEW exemption entry with no root_fix. The base
        # branch the check compares against is the fixture's own baseline
        # commit, so the old entries read as old and only the planted one
        # as new (practice: fixture-owns-its-state).
        def _setup_base(repo):
            git(repo, 'update-ref', 'refs/remotes/origin/staging', 'HEAD')

        def _plant_new_exemption(repo):
            f = repo / 'precedent.json'
            cfg = json.loads(f.read_text(encoding='utf-8'))
            cfg.setdefault('filename_separator_exempt', []).append(
                {'path': 'planted', 'ext': '.md', 'reason': 'planted'})
            f.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
        case('upstream-fix', _plant_new_exemption, setup=_setup_base)

        # advisory-checks-declare-their-term -- a warning-only check whose
        # term is neither permanent nor temporary. Planted in the fixture's
        # own copy of precedent_check.py, the file the check reads its
        # registry from.
        def _plant_bad_advisory_term(repo):
            f = repo / 'tools' / 'precedent_check.py'
            text = f.read_text(encoding='utf-8')
            needle = "advisory_term={'term': 'permanent',\n                      'why': 'closing a gap"
            assert needle in text, 'planted anchor moved'
            f.write_text(text.replace(needle, needle.replace('permanent', 'someday'), 1),
                         encoding='utf-8')
        case('advisory-checks-declare-their-term', _plant_bad_advisory_term)

        # expires-is-honoured -- a DATE expiry that has passed while the
        # practice is still `active`. The date is far in the past on purpose:
        # a fixture dated near today passes for a while and then starts
        # failing on a calendar boundary nobody is watching.
        case('expires-is-honoured',
             lambda repo: (repo / 'practices' / 'zzz-expired-rule.md')
             .write_text(
                 '---\nslug:        zzz-expired-rule\n'
                 'title:       An expired rule\n'
                 'tier:        on-demand\nseverity:    default\n'
                 'applies_to:  ["**"]\noccasion:    "testing"\n'
                 'index_clause: "a planted case"\nchecked_by:  null\n'
                 'defines:     []\nstatus:      active\nsupersedes:  []\n'
                 'expires:     "2020-01-01"\n'
                 'overrides:   null\nadded:       null\n'
                 'approved_by: "harness"\nsource_practice_number: 998\n---\n\n'
                 '## Rule\nDo the thing.\n\n## Detail\n\n## Why\nBecause.\n\n'
                 '## Story\nPlanted by the harness.\n\n## Install\nNone.\n',
                 encoding='utf-8'))

        # vendored-engine-file-refs-resolve -- delete a file precedent_gate.py
        # hardcodes a reference to (_ENGINE_DIR / 'routing_scope.json'),
        # reproducing the the project's own prior notes repository incident this check exists for
        case('vendored-engine-file-refs-resolve',
             lambda repo: (repo / 'tools' / 'routing_scope.json').unlink())

        # vendored-import-refs-resolve -- a vendored file (precedent_paths.py,
        # in both ENGINE_FILES and CONSUMER_ENGINE_FILES) module-level
        # imports a tool vendored in NEITHER -- reproducing the 2026-09-19
        # incident this check exists for (precedent_check.py did exactly
        # this to itself and broke check_installer_produces_a_clean_install).
        #
        # THE PLANTED IMPORT WAS parse_check UNTIL 2026-09-21, and vendoring
        # very_deep_check.py that day brought parse_check.py into both lists
        # with it -- so the planted "violation" resolved cleanly and this
        # case silently stopped testing anything. The harness caught it in
        # the same run: "a planted violation fails the check". That is the
        # planted-case mechanism doing precisely its job, and it is the
        # reason a check without one is refused.
        #
        # precedent_simulate.py is the replacement because it is unvendored
        # BY DESIGN rather than by omission: an authoring aid for writing
        # practices here, which no consumer runs (UPSTREAM_ONLY in
        # precedent_check.py says so). It took over from
        # the upstream-carry notice's tool when that was retired on
        # 2026-09-27. A future list change is unlikely to absorb it the way
        # parse_check.py was absorbed -- but if one ever does, this case will
        # fail exactly like this one did, which is the point.
        case('vendored-import-refs-resolve',
             lambda repo: rewrite(repo, 'tools/precedent_paths.py',
                                  lambda t: 'import precedent_simulate\n' + t))

        # generated-artifact-provenance -- a hand-edited generated view
        case('generated-artifact-provenance',
             lambda repo: rewrite(repo, 'MAP.md', lambda t: t + '\nhand-added\n'))

        # orientation-map
        case('orientation-map', lambda repo: (repo / 'MAP.md').unlink())

        # open-item-disposition -- a misspelt disposition. Deliberately not a
        # MISSING one: absence is a defined state (`wait`, the quiet
        # default), so planting one would assert the opposite of the rule.
        # The dangerous case is the line that reads as parked to a person
        # skimming and as nothing at all to a session grepping for the word.
        case('open-item-disposition',
             lambda repo: rewrite(repo, 'TODO.md',
                                  lambda x: x + '\n**Disposition:** parkd (2026-09-08, Morgan)\n'))

        # open-item-disposition-copies -- a park in the frontmatter with no
        # dated, named body line: warned about, never refused (practice:
        # format-rules-grandfather).
        case('open-item-disposition-copies',
             lambda repo: (repo / 'todo' / 'todo-2099-01-01-planted-park.md')
             .write_text('---\nslug: todo-2099-01-01-planted-park\n'
                         'status:            open\n'
                         'disposition:       parked\nnoted: 2099-01-01\n---\n'
                         '## What\n\nA planted item.\n', encoding='utf-8'),
             advisory=True)

        # The other half of that grammar, asserted directly rather than
        # through case(): a `parked` line nobody signed. case() proves only
        # that SOMETHING failed, and this practice has two distinct
        # violations whose messages must not be interchangeable
        # (control-asserts-which-failure).
        _unsigned = fresh('open-item-disposition-unsigned')
        rewrite(_unsigned, 'TODO.md',
                lambda x: x + '\n**Disposition:** parked\n')
        _rc, _out = run(_unsigned, 'open-item-disposition')
        cases.append(('open-item-disposition: a `parked` line with no date '
                      'and no name fails, saying so',
                      _rc == 1 and 'carries no' in _out and 'YYYY-MM-DD' in _out))
        _wait = fresh('open-item-disposition-wait')
        rewrite(_wait, 'TODO.md', lambda x: x + '\n**Disposition:** wait\n')
        _rcw, _outw = run(_wait, 'open-item-disposition')
        cases.append(('open-item-disposition: a bare `wait` line -- the quiet '
                      'default, written out -- does not fail',
                      _rcw == 0 and 'VIOLATION' not in _outw))

        # decision-strength -- an INVENTED strength value. Deliberately not
        # a missing one: absence is a defined state (unknown, and nothing is
        # backfilled), so planting one would assert the opposite of the
        # rule. The dangerous case is `strength: strong`, which reads as an
        # endorsement to a person skimming and matches neither defined word
        # for a session looking for one.
        # practice-standing -- a Principle set by someone the universal
        # set's registry (precedent.json maintainers) does not name. The
        # check's other refusals are asserted in-process, by message.
        case('practice-standing',
             lambda repo: rewrite(repo, 'practices/weak-yes.md',
                                  lambda t: t.replace(
                                      'severity:    default\n',
                                      'severity:    default\nstanding:    principle\n'
                                      'standing_by: not-an-approver\n', 1)))

        case('decision-strength',
             lambda repo: rewrite(repo, 'practices/decision-strength.md',
                                  lambda t: t.replace('strength:    decided',
                                                      'strength:    strong')))

        # The other two halves of that grammar, asserted directly rather than
        # through case(): case() proves only that SOMETHING failed, and this
        # practice's failures must not be interchangeable
        # (control-asserts-which-failure).
        _unowned = fresh('decision-strength-unowned')
        rewrite(_unowned, 'practices/decision-strength.md',
                lambda t: t.replace('approved_by: "Morgan, 2026-09-09"',
                                    'approved_by: null'))
        _rcu, _outu = run(_unowned, 'decision-strength')
        cases.append(('decision-strength: a `decided` naming nobody in '
                      'approved_by fails, saying so',
                      _rcu == 1 and 'names nobody' in _outu))
        _unmarked = fresh('decision-strength-unmarked')
        rewrite(_unmarked, 'practices/decision-strength.md',
                lambda t: t.replace('strength:    decided\n', ''))
        _rcm, _outm = run(_unmarked, 'decision-strength')
        cases.append(('decision-strength: a practice with no strength at all '
                      '-- the unknown state, which is legal forever -- does '
                      'not fail',
                      _rcm == 0 and 'VIOLATION' not in _outm))

        # dated-list-runs-forward -- a marked list put back into the order
        # it actually had before 2026-09-23: newest first. That is the plant
        # rather than a single swapped row because it is how the disorder
        # really arises -- somebody adds an entry at the top, where the
        # cursor is, and nothing objects.
        case('dated-list-runs-forward',
             lambda repo: rewrite(repo, 'practices/very-deep-check.md',
                                  _reverse_marked_dated_list))

        # The other half of the grammar, asserted directly rather than
        # through case(): case() proves only that SOMETHING failed, and an
        # undated entry must not be interchangeable with an out-of-order one
        # (control-asserts-which-failure). This is the exact shape the
        # practice was written for -- a relative date creeping back in.
        _undated = fresh('dated-list-runs-forward-undated')
        rewrite(_undated, 'practices/very-deep-check.md',
                lambda x: x.replace(
                    '\n## Install',
                    '\n- **Extended same day, Morgan** \u2014 a relative date '
                    'creeps back in\n\n## Install', 1))
        _rcd, _outd = run(_undated, 'dated-list-runs-forward')
        cases.append(('dated-list-runs-forward: an entry dated "same day" '
                      'rather than with a date of its own fails, saying so',
                      _rcd == 1 and 'no date of its own' in _outd))
        # And the clean direction, which is the one that decides whether this
        # check is safe to leave switched on: the mark shown as an EXAMPLE,
        # indented or fenced inside the practice that documents it, must not
        # register as a real list. The first run of this check flagged
        # exactly that (practice: checkable-gets-checked).
        _example = fresh('dated-list-runs-forward-example')
        _rce, _oute = run(_example, 'dated-list-runs-forward')
        cases.append(('dated-list-runs-forward: the mark shown as an example '
                      'in its own practice file is not read as a list',
                      _rce == 0 and 'VIOLATION' not in _oute))

        # speculation-is-marked -- the four markers drifting apart. The plant
        # is `status: accepted` on the repo's own speculative document:
        # somebody deciding to do the thing is the realistic way a marker
        # goes stale, and it is the one drift that reads as HARMLESS while
        # leaving the other three markers saying the opposite.
        case('speculation-is-marked',
             lambda repo: rewrite(repo, 'spec/SPECULATIVE_WHATSAPP_BRIDGE.md',
                                  lambda t: t.replace('status:        drafted',
                                                      'status:        accepted')))

        # The other two directions, asserted by MESSAGE rather than through
        # case(): this check has four distinct failures and case() proves only
        # that one of them fired (control-asserts-which-failure).
        _nowarn = fresh('speculation-is-marked-nowarn')
        rewrite(_nowarn, 'spec/SPECULATIVE_WHATSAPP_BRIDGE.md',
                lambda t: t.replace('> **This is a brainstorm, not a plan of record.**',
                                    'It is a brainstorm.'))
        _rcn, _outn = run(_nowarn, 'speculation-is-marked')
        cases.append(('speculation-is-marked: a speculative document with no '
                      'warning block under its heading fails, saying so',
                      _rcn == 1 and 'no warning block' in _outn))
        # The reverse direction: the markers are all inside the file and the
        # FILENAME is the one that lost them, which no content rewrite can
        # reach -- a file listing is the reader this marker exists for.
        _noprefix = fresh('speculation-is-marked-noprefix')
        (_noprefix / 'spec' / 'SPECULATIVE_WHATSAPP_BRIDGE.md').rename(
            _noprefix / 'spec' / 'WHATSAPP_BRIDGE.md')
        _rcp, _outp = run(_noprefix, 'speculation-is-marked')
        cases.append(('speculation-is-marked: a document that calls itself '
                      'speculative but is not named that way fails, saying so',
                      _rcp == 1 and 'calls itself speculative' in _outp))
        # A plan that only SAYS WHERE IT CAME FROM is not speculative: the
        # opening paragraph of an executed plan read "after a brainstorm" and
        # was flagged (2026-10-30). The check reads "brainstorm" there only
        # where the document calls itself one.
        _origin = fresh('speculation-is-marked-origin')
        (_origin / 'spec' / 'ORIGIN_NAMED_PLAN.md').write_text(
            '---\ntitle:         A plan that names its origin\n'
            'kind:          plan\nstatus:        done\nopened:        2026-10-01\n'
            'closed:        2026-10-02\nsuperseded_by: null\nsupersedes:    []\n'
            'audience:      contributor\nsummary:       Executed.\n---\n\n'
            '# A plan that names its origin\n\n'
            'Written after a brainstorm, and carried out the next day.\n',
            encoding='utf-8')
        _rco, _outo = run(_origin, 'speculation-is-marked')
        cases.append(('speculation-is-marked: an executed plan whose opening '
                      'says it began after a brainstorm passes',
                      _rco == 0 and 'calls itself speculative' not in _outo))

        # reply-checker-keeps-set-examples -- a reply-checker change that
        # breaks a set's examples (2026-10-30, 20dabf57e and the writing
        # set). Setup puts a set beside the fixture whose one example the
        # real checker answers as declared; the plant makes the fixture's
        # checker refuse nothing, as a regression would.
        def _set_beside(repo):
            d = repo.parent / 'precedent-zz-planted-set'
            (d / 'practices').mkdir(parents=True, exist_ok=True)
            (d / 'reply_check.json').write_text(json.dumps([
                {'practice': 'p', 'id': 'zz-rule', 'require_one_of': ['ZZ-OK'],
                 '_examples': [{'reply': 'Done.', 'refused': True},
                               {'reply': 'Done. ZZ-OK', 'refused': False}]}]),
                encoding='utf-8')

        def _checker_refuses_nothing(repo):
            rewrite(repo, 'tools/precedent_reply_check.py',
                    lambda t: re.sub(r'(\ndef violations\([^)]*\):\n)',
                                     r'\1    return []\n', t, count=1))
        case('reply-checker-keeps-set-examples', _checker_refuses_nothing,
             setup=_set_beside)

        # very-deep-check -- the run's full account left out. The plant is
        # the exact shape of 2026-10-11: all four passes recorded and the
        # account still the previous run's (opened 2026-10-05).
        _VDC_UP = 'spec/VERY_DEEP_CHECK_LATEST_RUN.md'

        def _vdc_stale_account(t):
            return re.sub(r'^opened:(\s*)\S+', r'opened:\g<1>2026-10-05',
                          t, count=1, flags=re.M)
        # The fixture owns the ledger state it asserts on: the last completed
        # run gets all four passes and a date past the rule's. Inheriting the
        # real ledger made this case fail during every real run -- between
        # the tool's first run and the session's --record-pass the last
        # completed run has no passes, so nothing was owed and nothing fired
        # (2026-10-17; practice: fixture-owns-its-state).
        def _vdc_four_passes(t):
            d = json.loads(t)
            done = [r for r in d['runs'] if r.get('completed', True)]
            done[-1]['passes'] = [{'pass': str(n), 'status': 'done'}
                                  for n in (1, 2, 3, 4)]
            if str(done[-1].get('date') or '') < '2026-10-11':
                done[-1]['date'] = '2026-10-11'
            return json.dumps(d, indent=2) + '\n'

        def _vdc_plant(repo):
            rewrite(repo, 'record/very-deep-check-ledger.json', _vdc_four_passes)
            rewrite(repo, _VDC_UP, _vdc_stale_account)
        case('very-deep-check', _vdc_plant)

        # The other two states, by message and by silence
        # (control-asserts-which-failure, checks-plant-their-state): no
        # account at all is its own finding, and a run whose fourth pass is
        # not recorded yet is still in progress, so a stale account is not
        # owed and must not fail.
        _vdc_gone = fresh('very-deep-check-no-account')
        rewrite(_vdc_gone, 'record/very-deep-check-ledger.json', _vdc_four_passes)
        (_vdc_gone / _VDC_UP).unlink()
        _rcg, _outg = run(_vdc_gone, 'very-deep-check')
        cases.append(('very-deep-check: four passes recorded and no account '
                      'file fails, saying no account was written',
                      _rcg == 1 and 'no account was written' in _outg))

        def _vdc_three_passes(t):
            d = json.loads(t)
            done = [r for r in d['runs'] if r.get('completed', True)]
            done[-1]['passes'] = [p for p in done[-1].get('passes') or []
                                  if str(p.get('pass')) != '4']
            return json.dumps(d, indent=2) + '\n'
        _vdc_mid = fresh('very-deep-check-mid-run')
        rewrite(_vdc_mid, 'record/very-deep-check-ledger.json', _vdc_four_passes)
        rewrite(_vdc_mid, 'record/very-deep-check-ledger.json', _vdc_three_passes)
        rewrite(_vdc_mid, _VDC_UP, _vdc_stale_account)
        _rcm, _outm = run(_vdc_mid, 'very-deep-check')
        cases.append(('very-deep-check: a run with pass 4 not yet recorded '
                      'does not owe its account yet',
                      _rcm == 0 and 'VIOLATION' not in _outm))

        # A run from 2026-10-18 on owes its test review too (Pass 2's
        # question 27). The plant: a current account with every other
        # section and no `## Test review`. The quiet half is the real tree,
        # whose 2026-10-17 run predates the rule and passes above.
        def _vdc_from_the_18th(t):
            d = json.loads(_vdc_four_passes(t))
            [r for r in d['runs'] if r.get('completed', True)][-1]['date'] = '2026-10-18'
            return json.dumps(d, indent=2) + '\n'

        def _vdc_no_test_review(t):
            t = re.sub(r'^opened:(\s*)\S+', r'opened:\g<1>2026-10-18', t,
                       count=1, flags=re.M)
            t = re.sub(r'^## Test review\s*$', '## Tests', t, flags=re.M)
            return t if re.search(r'^## Checks by stage\s*$', t, re.M) \
                else t + '\n## Checks by stage\n\nPlanted.\n'
        _vdc_tr = fresh('very-deep-check-no-test-review')
        rewrite(_vdc_tr, 'record/very-deep-check-ledger.json', _vdc_from_the_18th)
        rewrite(_vdc_tr, _VDC_UP, _vdc_no_test_review)
        _rct, _outt = run(_vdc_tr, 'very-deep-check')
        cases.append(('very-deep-check: a run from 2026-10-18 whose account '
                      'has no test review fails, saying so',
                      _rct == 1 and 'no `## Test review` section' in _outt))

        # heading-outline -- a heading demoted two levels at once, so it has
        # no parent. documentation/INSTALL.md is the plant because it is a
        # short file whose only heading is its H1, so appending an h3 makes
        # the skip unambiguous and cannot collide with other planted cases.
        def _plant_outline(repo):
            rewrite(repo, 'documentation/INSTALL.md',
                    lambda t: t + '\n### An orphaned heading, two levels down\n')
        case('heading-outline', _plant_outline)

        # headline-capitalization -- an outward-facing heading knocked back
        # into sentence case. "Learn More" is the plant because it is the one
        # heading every documentation/ file ends with, so this stays valid
        # however the pages themselves are reorganized.
        def _plant_headline(repo):
            rewrite(repo, 'documentation/WHY_PRECEDENT.md',
                    lambda t: t.replace('## Learn More', '## Learn more', 1))
        case('headline-capitalization', _plant_headline)

        # whats-new -- an entry's bullet with its bold opening taken off, the
        # exact slip the check was added for on 2026-10-01 (the bold sat
        # mid-sentence and went unseen). The log's first bullet is the plant
        # because the newest entry always has one.
        def _plant_whats_new(repo):
            def strip_first_bold(t):
                head, sep, rest = t.partition('\n- **')
                return head + sep.replace('**', '') + rest.replace('**', '', 1) if sep else t
            rewrite(repo, 'WHATS_NEW.md', strip_first_bold)
        case('whats-new', _plant_whats_new)

        # source-naming -- a source named freehand instead of by its level.
        # `bestpractice-local` is the real name this repo's own repo-local
        # source carried before the convention was fixed, so the planted case
        # is the exact drift the practice exists to stop, not an invented one.
        case('source-naming',
             lambda repo: rewrite(repo, 'precedent.json', lambda t: t.replace(
                 '"name": "local"', '"name": "bestpractice-local"')))

        # layered-practice-packs -- a practice left in force with nothing
        # able to load it. Planted by deleting one judgment-only practice's
        # line from the instructions' occasion index while leaving the
        # practice itself active: it is still in force, and now no channel
        # reaches it. That is the real shape (a source declared in
        # precedent.json whose practices never reach the generated views),
        # reproduced with only the universal source, which is the one a
        # fixture can resolve.
        # A second shape in the same fixture (2026-10-05): a practice whose
        # only file route names its own tool files is NOT reachable -- the
        # routing audit's own route until that day. Reported by name below.
        def _plant_unreachable(repo):
            rewrite(repo, 'AGENTS.md', lambda t: re.sub(
                r'\n  quote-discipline [^\n]*', '', t))
            rewrite(repo, 'practices/routing-audit.md', lambda t: t.replace(
                '["practices/*.md", "tools/routing_audit.py"',
                '["tools/routing_audit.py"', 1))
        case('layered-practice-packs', _plant_unreachable, advisory=True)
        # practice: shared-index-is-a-directory -- a change adding a row to a
        # 25-row table typed by hand is told the file can be a directory. The
        # setup commits the table to both trees, so only the planted one
        # carries a change; advisory, so it reports and never fails.
        def _setup_long_index(repo):
            (repo / 'docs').mkdir(exist_ok=True)
            (repo / 'docs' / 'zz-index.md').write_text(
                '# Index\n\n| Name | Where |\n|---|---|\n'
                + ''.join(f'| row {i} | here |\n' for i in range(25)),
                encoding='utf-8')
            git(repo, 'add', '-f', 'docs/zz-index.md')
            git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.com',
                'commit', '-qm', 'a long hand-typed index')

        def _plant_long_index(repo):
            rewrite(repo, 'docs/zz-index.md', lambda t: t + '| row new | there |\n')
        case('shared-index-is-a-directory', _plant_long_index,
             setup=_setup_long_index, advisory=True)
        if 'shared-index-is-a-directory' in planted:
            cases.append(('shared-index-is-a-directory: the finding gives the '
                          'command that splits the file',
                          '--split-file docs/zz-index.md'
                          in planted['shared-index-is-a-directory'][1]))
        if 'layered-practice-packs' in planted:
            _lpp = planted['layered-practice-packs'][1]
            cases.append(('layered-practice-packs: a practice routed only by '
                          'its own tool files, with an existence-only check, '
                          'is reported unreachable',
                          'routing-audit' in _lpp and 'quote-discipline' in _lpp))

        # quick-index -- the table removed from the instructions
        def _plant_qi(repo):
            rewrite(repo, 'AGENTS.md', lambda t: re.sub(
                r'\n\| Looking for.*?\n\n', '\n\n', t, flags=re.S))
        case('quick-index', _plant_qi)

        # decommission-deletes-files -- a path declared retired that is
        # tracked again. The CLEAN half deliberately still declares a
        # retirement (of a path that really is absent), so the negative
        # control proves the check PASSES rather than merely skipping: with
        # no registry at all it reports NotApplicable, which looks identical
        # to a pass from outside and would have proved nothing.
        def _retire_registry(repo, entries):
            (repo / 'process').mkdir(exist_ok=True)
            (repo / 'process' / 'decommissioned_paths.json').write_text(
                json.dumps({'decommissioned': entries, 'exempt_files': []},
                           indent=2) + '\n', encoding='utf-8')
            git(repo, 'add', 'process/decommissioned_paths.json')
            git(repo, 'commit', '-qm', 'declare a retirement')

        def _setup_retire(repo):
            _retire_registry(repo, [
                {'path': 'process/never-existed-here',
                 'reason': 'the harness fixture has no such tree',
                 'decommissioned_at': '2026-09-07'}])

        def _plant_retire(repo):
            _retire_registry(repo, [
                {'path': 'process/never-existed-here',
                 'reason': 'the harness fixture has no such tree',
                 'decommissioned_at': '2026-09-07'},
                {'path': 'spec/LOADER.md',
                 'reason': 'planted -- this file is very much still here',
                 'decommissioned_at': '2026-09-07'}])
        case('decommission-deletes-files', _plant_retire, setup=_setup_retire)

        # rename-updates-links -- a file moved, its references left behind.
        # Needs a published default branch to diff against, which the
        # pristine fixture has no remote for, so the setup gives it one
        # pointing at the baseline commit and branches off it. spec/LOADER.md
        # is chosen because AGENTS.md and other documents link it, so the
        # rename really does strand references the way the practice describes.
        def _setup_rename(repo):
            git(repo, 'branch', '-M', 'main')
            git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
            git(repo, 'symbolic-ref', 'refs/remotes/origin/HEAD',
                'refs/remotes/origin/main')
            git(repo, 'checkout', '-qb', 'feature')

        def _plant_rename(repo):
            git(repo, 'mv', 'spec/LOADER.md', 'spec/LOADER_MOVED.md')
            git(repo, 'commit', '-qm', 'rename, leaving every reference behind')
        case('rename-updates-links', _plant_rename, setup=_setup_rename)

        # change-updates-its-docs -- a file this branch deleted, every
        # document that names it left as it was. The unplanted fixture's
        # branch deletes nothing, so it has nothing to judge; the check reads
        # the branch against its base, never the whole history.
        def _plant_removed_path(repo):
            git(repo, 'rm', '-q', 'spec/LOADER.md')
            git(repo, 'commit', '-qm', 'delete a file other documents name')
        case('change-updates-its-docs', _plant_removed_path, setup=_setup_rename)

        # shipped-links-travel -- a shipped document linking relatively to
        # a file the catalogue copy leaves out (2026-10-01: links to
        # templates/harness/LEDGER.md were broken in every consumer).
        # 2026-10-08: and to an engine file, which a consumer keeps in its
        # own tools/ while its copy leaves tools/ out -- 320 such links
        # passed this check while the copy dropped every target.
        case('shipped-links-travel',
             lambda repo: rewrite(repo, 'README.md', lambda t: t +
                                  '\nSee [the loader](spec/LOADER.md) and '
                                  '[the check](tools/precedent_check.py).\n'))
        if 'shipped-links-travel' in planted:
            out = planted['shipped-links-travel'][1]
            cases.append(('shipped-links-travel: a link into tools/ is a finding '
                          'too, since the copy leaves tools/ at home',
                          'links to tools/precedent_check.py' in out))

        # checks-use-generated-blocks -- a repo's own check that finds
        # generated text by spelling a marker itself, the shape a shared
        # set's no-stale-counts check had, instead of asking
        # tools/generated_blocks.py.
        def _plant_hand_marker(repo):
            (repo / 'tools' / 'checks').mkdir(parents=True, exist_ok=True)
            (repo / 'tools' / 'checks' / 'check_zzz_hand.py').write_text(
                "SKIP_FROM = '<!-- BEGIN GENERATED: precedent-loader -->'\n",
                encoding='utf-8')
            git(repo, 'add', '-A')
        case('checks-use-generated-blocks', _plant_hand_marker)

        # practice-change-propagates -- a live lookup of a practice this tree
        # renamed away. `brief-it` is a deduplicated stub forwarding to
        # `my-options` here, so a README telling the reader to look it up
        # sends them to the stub: the shape of the go-merge rename this case
        # was first written for (go-merge, a stub forwarding to go-update),
        # planted in the repository that made the rename.
        case('practice-change-propagates',
             lambda repo: rewrite(repo, 'README.md', lambda t: t +
                                  '\nBefore merging, read '
                                  '`python3 tools/precedent_show.py brief-it`.\n'))

        # rename-updates-links, the other direction: a stranded reference the
        # consuming repo CANNOT repoint must leave the check silent, and the
        # identical reference in a file it CAN edit must still fail. Both
        # halves in one fixture, because a skip that quietly disabled the
        # check would pass the first half on its own.
        #
        # This repo has no MANIFEST.json (it is the upstream, not a consumer),
        # so the fixture writes one: that file is where
        # precedent_materialize.py records which source produced each
        # materialized practice and check, and attribution is by that record
        # rather than by live resolution -- a bare CI checkout can reach
        # universal and repo-local but never team or individual.
        # The planted path is built, never spelled: this file is inside every
        # fixture, so a literal copy of it here is itself a stale reference.
        # The old stale-reference scan hid it by accident -- any line quoting
        # the loader marker opened a "generated block" in this file -- and
        # tools/generated_blocks.py, which needs the marker alone on its line,
        # no longer does (2026-09-29).
        zzz_old = 'notes/' + 'ZZZ_OLD.md'

        def _setup_received(repo):
            _setup_rename(repo)
            (repo / 'MANIFEST.json').write_text(json.dumps({
                'sources': [
                    {'level': 'repo-local', 'name': 'local', 'path': 'local'},
                    {'level': 'individual', 'name': 'zzz-individual',
                     'path': '/nowhere'},
                ],
                'practices': [{'slug': 'zzz-received', 'source': 'zzz-individual'}],
                'checks': [{'path': 'tools/checks/check_zzz_received.py',
                            'source': 'zzz-individual'}],
                'withheld': [],
            }, indent=1) + '\n', encoding='utf-8')
            (repo / 'notes').mkdir(exist_ok=True)
            (repo / 'notes' / 'ZZZ_OLD.md').write_text('placeholder\n',
                                                       encoding='utf-8')
            (repo / 'practices' / 'zzz-received.md').write_text(
                f'Materialized from another source; it names `{zzz_old}`\n'
                'as this convention\'s canonical example.\n', encoding='utf-8')
            (repo / 'tools' / 'checks').mkdir(parents=True, exist_ok=True)
            (repo / 'tools' / 'checks' / 'check_zzz_received.py').write_text(
                f'# materialized check; its docstring names {zzz_old}\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'materialized output from another source')
            git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')

        def _plant_received_only(repo):
            git(repo, 'mv', zzz_old, 'notes/ZZZ_NEW.md')
            git(repo, 'commit', '-qm', 'rename; only received files still name it')

        repo = fresh('rename-updates-links-received')
        _setup_received(repo)
        _plant_received_only(repo)
        rc, out = run(repo, 'rename-updates-links')
        cases.append(('rename-updates-links: a stranded reference inside a '
                      'materialized practice or check is not reported '
                      '(the consuming repo cannot repoint it -- the next '
                      'sync overwrites any edit)',
                      rc == 0 and 'VIOLATION' not in out))

        repo = fresh('rename-updates-links-editable')
        _setup_received(repo)
        (repo / 'docs-page.md').write_text(
            f'See `{zzz_old}` for the details.\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'a page this repo owns names the same path')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        _plant_received_only(repo)
        rc, out = run(repo, 'rename-updates-links')
        cases.append(('rename-updates-links: the identical reference in a file '
                      'the repo DOES own still fails (the skip above is a '
                      'scope, not the check going quiet)',
                      rc == 1 and 'VIOLATION' in out and 'docs-page.md' in out))

        # ...and the generated loader block is skipped as a REGION, so a
        # reference in the hand-written half of the same document is still
        # reported. One fixture, both halves, same reason as above.
        repo = fresh('rename-updates-links-generated')
        _setup_rename(repo)
        (repo / 'notes').mkdir(exist_ok=True)
        (repo / 'notes' / 'ZZZ_OLD.md').write_text('placeholder\n',
                                                   encoding='utf-8')
        rewrite(repo, 'AGENTS.md', lambda x: x.replace(
            '<!-- BEGIN GENERATED: precedent-loader -->',
            '<!-- BEGIN GENERATED: precedent-loader -->\n'
            f'A regenerated line naming {zzz_old}.', 1))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'loader block names the path')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        _plant_received_only(repo)
        rc, out = run(repo, 'rename-updates-links')
        cases.append(('rename-updates-links: a reference inside the generated '
                      'loader block is not reported (build_views.py rewrites '
                      'it wholesale from the sources)',
                      rc == 0 and 'VIOLATION' not in out))

        repo = fresh('rename-updates-links-outside-block')
        _setup_rename(repo)
        (repo / 'notes').mkdir(exist_ok=True)
        (repo / 'notes' / 'ZZZ_OLD.md').write_text('placeholder\n',
                                                   encoding='utf-8')
        rewrite(repo, 'AGENTS.md', lambda x:
                f'A hand-written line naming {zzz_old}.\n' + x)
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'hand-written half names the path')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        _plant_received_only(repo)
        rc, out = run(repo, 'rename-updates-links')
        cases.append(('rename-updates-links: the same reference OUTSIDE the '
                      'generated block is still reported (skipped as a '
                      'region, not as a file)',
                      rc == 1 and 'VIOLATION' in out and 'AGENTS.md' in out))

        # two-check-levels -- one of the pair GLOSSARY.md defines is no
        # longer named anywhere in AGENTS.md. Until 2026-09-28 this plant
        # only un-bolded the pair, because the check demanded the literal
        # bold markup; the Rule asks for the names, so the plant removes a
        # name.
        def _plant_tcl(repo):
            rewrite(repo, 'AGENTS.md', lambda t: re.sub(
                r'light check', 'quick pass', t, flags=re.I))
        case('two-check-levels', _plant_tcl)

        # routing-audit -- a stale rotation entry for a practice that no
        # longer exists (the exact bookkeeping-drift case the check exists
        # to catch: a retired or renamed practice left behind in the state
        # file)
        def _plant_ra(repo):
            (repo / 'tools' / 'routing_audit_state.json').write_text(
                '{"not-a-real-practice-zzz": {"last_reviewed": '
                '"2020-01-01", "commit": "deadbeef"}}\n', encoding='utf-8')
        case('routing-audit', _plant_ra)

        # declared-sources-are-cloned -- this repo declares three shared sets
        # beside itself, and both .claude/hooks/session-start.sh and the
        # tools/bootstrap.sh it runs clone them. Planted by deleting that
        # line from both: the finding must name the missing clone step.
        def _plant_dsac(repo):
            # tools/session-start.sh since 2026-10-07: the .claude/hooks/ copy is
            # the pointer stub, and the check follows it there.
            for rel in ('tools/bootstrap.sh', '.claude/hooks/session-start.sh',
                        'tools/session-start.sh'):
                rewrite(repo, rel, lambda t: re.sub(
                    r'\n[^\n]*precedent_source_bootstrap\.py --teams-from[^\n]*',
                    '', t))
        case('declared-sources-are-cloned', _plant_dsac)
        cases.append(('declared-sources-are-cloned: the planted finding names '
                      'the missing session-start clone step',
                      'no session-start step clones them' in
                      planted.get('declared-sources-are-cloned', (0, ''))[1]
                      or 'declared-sources-are-cloned' not in ran))

        # philosophy-is-not-repo-policy -- a practice whose ## Rule leans on
        # an essay for its authority, which is exactly the drift the
        # philosophy/ copy created the risk of. Planted in the EXPORTED
        # catalogue, since that is the costlier of the two directions.
        def _plant_pinrp(repo):
            rewrite(repo, 'practices/quick-index.md', lambda s: s.replace(
                '## Rule\n',
                '## Rule\nFollow philosophy/OUR_PHILOSOPHY.md when you write.\n',
                1))
        case('philosophy-is-not-repo-policy', _plant_pinrp)

        # philosophy-declares-its-source -- a document dropped into
        # philosophy/ with no provenance line, so nothing records where its
        # text was argued out. The essays have no upstream to fall behind:
        # the notebook they came from was retired, which is exactly why the
        # line is the only surviving trace of that history.
        def _plant_pdis(repo):
            (repo / 'philosophy' / 'ORPHAN.md').write_text(
                '# An Orphan\n\nWith no provenance line.\n', encoding='utf-8')
        case('philosophy-declares-its-source', _plant_pdis)

        # park-it -- the standing phrase stripped out of AGENTS.md, leaving
        # the practice file in force and nothing a session reads that says
        # what the phrase means. That is not a hypothetical: it is the state
        # `go-merge` was in when a session met the phrase cold and went and
        # asked Morgan what it meant, which is the interruption the phrase
        # exists to stop. Only the phrase is removed, not the word `parked`,
        # so the planted case also proves the check names the missing half
        # rather than reporting a generic failure.
        def _plant_park_it(repo):
            rewrite(repo, 'AGENTS.md',
                    lambda s: s.replace('Drop it', 'the phrase'))
        case('park-it', _plant_park_it)

        # install-declares-its-scope -- SETUP.md put back the way it read
        # before 2026-09-14: the paragraph naming project-voice.md and
        # project-visual-identity.md together, stripped of every deferral
        # marker, so it reads as an instruction to fill them in during the
        # install. That is the exact regression the check exists for, and
        # it is the state the guided install was actually in. (Read
        # 'VOICE.md' here before 2026-09-17, and 'STYLEGUIDE.md' before
        # 2026-09-22, when these were still plain root documents rather
        # than local/practices/project-voice.md and
        # local/practices/project-visual-identity.md.)
        #
        # The counterpart matters as much as the case: the check's own test
        # (local/tools/checks/tests/) proves that prose saying "do NOT walk
        # them through" does NOT fire. A first draft of the check could not
        # tell an instruction from its negation and flagged three correct
        # passages in INSTALL.md.
        def _plant_idis(repo):
            rewrite(repo, 'SETUP.md', lambda s: s + (
                "\n## Fill In the Identity Files\n\n"
                "Walk the administrator through `project-voice.md` section "
                "by section, and\nask whether a brand guideline exists to "
                "fill `project-visual-identity.md` from.\n"))
        case('install-declares-its-scope', _plant_idis)

        # environment-gotchas -- a live gotcha file that is a bare fix.
        #
        # Revised 2026-09-16: the catalogue moved out of AGENTS.md into one
        # file per trap under gotchas/ (spec/OPEN_ITEM_AND_GOTCHA_PLAN.md
        # Part 2), and precedent_check.py's environment-gotchas now reads
        # gotchas/*.md directly whenever that directory exists, ignoring
        # AGENTS.md's structure entirely once it does. The old plant edited
        # AGENTS.md's own bulleted index, which no longer exists on this
        # repository's real tree -- planting there would silently prove
        # nothing (the check would take the new branch and never look at
        # AGENTS.md's content). This plant instead ADDS a new gotchas/*.md
        # file, which is robust the same way the old one tried to be
        # (anchored on structure, not on any existing entry's wording) and
        # additive, so it cannot collide with or depend on the 44 real
        # entries already there (practice: fixture-owns-its-state).
        def _plant_eg(repo):
            gd = repo / 'gotchas'
            if not gd.is_dir():
                raise AssertionError(
                    'environment-gotchas plant: no gotchas/ directory in the '
                    'fixture tree, so nothing was planted and the case below '
                    'would assert nothing')
            (gd / 'gotcha-2026-01-01-planted-bare-fix.md').write_text(
                '---\nslug: gotcha-2026-01-01-planted-bare-fix\n'
                'status: live\nnoted: 2026-01-01\nseverity: null\n'
                'retired: null\nretires_when: null\n---\n'
                '## Symptom\n\nPlanted bare fix.\n\n'
                '## Story\n\nUse `git cat-file -e`.\n\n'
                '## Fix\n\n(see story)\n',
                encoding='utf-8')
        case('environment-gotchas', _plant_eg)

        # session-bootstrap -- setup named in prose, no hook to run it. Both
        # halves are planted (practice: fixture-owns-its-state): until
        # 2026-10-31 the case leaned on AGENTS.md happening to say
        # `pip install cmarkgfm`, and a rewording that dropped the phrase
        # left the check skipping the plant instead of failing it.
        def _plant_sb(repo):
            shutil.rmtree(repo / '.claude' / 'hooks')
            agents = repo / 'AGENTS.md'
            agents.write_text(agents.read_text(encoding='utf-8')
                              + '\nBefore working, run `pip install '
                                'planted-package` in this repository.\n',
                              encoding='utf-8')
        case('session-bootstrap', _plant_sb)

        # session-load-budget -- the instructions file over its declared
        # ceiling. Planted by moving the CEILING rather than by growing the
        # file: a fixture that pasted 20,000 tokens into AGENTS.md would trip
        # half the other checks in this repo on its way past this one, and
        # then a pass here would prove nothing about which check fired.
        def _plant_load_budget(repo):
            # Parsed, not string-replaced: a plant keyed on the spelling of a
            # number is a plant that rots the first time somebody reviews the
            # ceiling, and the case then reports the CHECK as broken. That is
            # this same fixture's scripts-assert-properties history, and it
            # happened to this case too, within the hour.
            def _lower(t):
                d = json.loads(t)
                # The per-surface ceilings bind only with no session-load
                # total declared (build_views.TOTAL_KEY); this plants them.
                d.pop('session_load_tokens', None)
                for e in d['surfaces'].values():
                    e['ceiling'] = 10
                return json.dumps(d, indent=2) + '\n'
            rewrite(repo, 'tools/session_load_budgets.json', _lower)
        # github-api-budget -- a new tool starts calling the API directly,
        # which is the shape that made "what is spending our allowance"
        # unanswerable in the first place: one uncounted caller, and the
        # figures every other tool reports are no longer the whole bill.
        # control-asserts-which-failure: the exit code alone would pass if
        # the check fired for any other reason, so the message is asserted.
        def _plant_api_caller(repo):
            (repo / 'tools' / 'gh_thing.py').write_text(
                "import subprocess\n"
                "subprocess.run(['curl', 'https://api.github.com/user'])\n",
                encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', 'tools/gh_thing.py'],
                           capture_output=True, text=True)

        case('github-api-budget', _plant_api_caller)
        cases.append(('github-api-budget: the planted violation names the '
                      'uncounted caller and the way out of it',
                      'tools/gh_thing.py' in planted['github-api-budget'][1]
                      and 'unrouted_callers' in planted['github-api-budget'][1]))

        case('session-load-budget', _plant_load_budget)
        cases.append(('session-load-budget: the planted violation names the '
                      'ceiling it is over, not just that something is big',
                      'over its declared ceiling of 10'
                      in planted['session-load-budget'][1]))

        # declared-hooks-exist -- settings.json still declares a hook file
        # that is no longer there. This is the 2026-09-08 incident with the
        # variables swapped: there every hook path was right and the session
        # root was wrong, here the root is right and the file is gone. Both
        # render identically, as nothing at all, which is why a machine has
        # to be the one asking.
        def _plant_declared_hook(repo):
            (repo / '.claude' / 'hooks' / 'commit-identity.sh').unlink()
        # access-probe-is-wired -- the tool is vendored and nothing runs it.
        # Same family as the two hook cases around it, and the same reason a
        # machine has to ask: a wiring line that was deleted and a wiring line
        # that was never added look identical, and both leave a session
        # unable to discover it cannot push somewhere until after the work is
        # done. The plant swaps the invocation for a different script, which
        # is the realistic shape -- the `[ -f ... ]` guard around it still
        # names the file, so a check testing for a MENTION rather than an
        # INVOCATION passes this plant. That false pass was measured on the
        # first version of the check, which is why the plant is written this
        # way rather than by deleting the whole block.
        def _plant_unwired_probe(repo):
            for rel in (pathlib.Path('.claude') / 'hooks' / 'session-start.sh',
                        pathlib.Path('tools') / 'bootstrap.sh',
                        pathlib.Path('templates') / 'bootstrap.sh'):
                f = repo / rel
                if not f.exists():
                    continue
                f.write_text(
                    f.read_text(encoding='utf-8').replace(
                        'python3 tools/precedent_access_check.py',
                        'python3 tools/some_other_tool.py'),
                    encoding='utf-8')

        case('access-probe-is-wired', _plant_unwired_probe)
        cases.append(('access-probe-is-wired: the planted violation names the '
                      'wiring files it looked in and the line to add',
                      'no session-start wiring invokes it'
                      in planted['access-probe-is-wired'][1]
                      and 'python3 tools/precedent_access_check.py .'
                      in planted['access-probe-is-wired'][1]))

        # fresh-before-write -- the guard's pre-write half no longer meets
        # Bash, the realistic edit (a matcher trimmed to the file tools),
        # which leaves a session editing through cat or sed unguarded.
        def _plant_fresh_guard_matcher(repo):
            f = repo / '.claude' / 'settings.json'
            d = json.loads(f.read_text(encoding='utf-8'))
            for entry in d.get('hooks', {}).get('PreToolUse', []):
                if any('freshness-guard.sh' in h.get('command', '')
                       for h in entry.get('hooks', [])):
                    entry['matcher'] = 'Edit|Write|NotebookEdit'
            f.write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8')

        case('fresh-before-write', _plant_fresh_guard_matcher)
        cases.append(('fresh-before-write: the planted violation says the '
                      'pre-write matcher leaves out Bash',
                      'leaves out Bash' in planted['fresh-before-write'][1]))

        case('declared-hooks-exist', _plant_declared_hook)
        cases.append(('declared-hooks-exist: the planted violation names the '
                      'hook that went missing, not just that something did',
                      'commit-identity.sh does not exist'
                      in planted['declared-hooks-exist'][1]))

        # dogfooded-hooks-match-template -- this repo's own installed copy
        # of a hook drifts from the template it was installed from. The
        # realistic shape is a fix landing in the live copy alone (exactly
        # what happened to freshness-guard.sh on 2026-09-15), so the plant
        # edits the INSTALLED side, not the template.
        def _plant_dogfooded_drift(repo):
            f = repo / '.claude' / 'hooks' / 'precedent-paths.sh'
            f.write_text(f.read_text(encoding='utf-8') + '\n# drift\n',
                        encoding='utf-8')
        case('dogfooded-hooks-match-template', _plant_dogfooded_drift)
        cases.append(('dogfooded-hooks-match-template: the planted violation '
                      'names the drifted hook, not just that something differs',
                      'precedent-paths.sh' in
                      planted['dogfooded-hooks-match-template'][1]))

        # new-hook-joins-the-registry -- a hook script dropped into the
        # shipped hooks directory and put on no kind's list. That is the
        # 2026-09-21 bug with one extra step in it: a hook no list names is
        # never wired into an installed repo by a refresh, so it reaches
        # fresh installs at best and existing repos never.
        def _plant_unlisted_hook(repo):
            (repo / 'templates' / 'harness' / 'claude-code' / 'hooks'
             / 'zzz-unlisted.sh').write_text('#!/bin/sh\necho unlisted\n',
                                             encoding='utf-8')
        case('new-hook-joins-the-registry', _plant_unlisted_hook)
        cases.append(('new-hook-joins-the-registry: the planted violation '
                      'names the unlisted hook and where to list it',
                      'zzz-unlisted.sh' in
                      planted['new-hook-joins-the-registry'][1]
                      and 'HOOK_WIRING' in
                      planted['new-hook-joins-the-registry'][1]))

        # hooks-on-disk-are-reachable -- the other end of the same failure.
        # declared-hooks-exist above plants a settings entry whose file is
        # gone; this plants a file no settings entry, no other hook and no
        # engine tool names. Both are a hook that does not run, and neither
        # is visible from inside a session: an orphaned hook and a working
        # one look identical, which is what cost a consuming repo its reply
        # gate on 2026-09-14.
        def _plant_orphan_hook(repo):
            (repo / '.claude' / 'hooks' / 'zzz-orphan.sh').write_text(
                '#!/bin/sh\necho orphan\n', encoding='utf-8')
        case('hooks-on-disk-are-reachable', _plant_orphan_hook)
        cases.append(('hooks-on-disk-are-reachable: the planted violation '
                      'names the orphaned hook and says nothing that could '
                      'run it names it',
                      'zzz-orphan.sh' in planted['hooks-on-disk-are-reachable'][1]
                      and 'nothing that could run it names it'
                      in planted['hooks-on-disk-are-reachable'][1]))

        # no-hardcoded-git-identity -- settings.json hardcodes a person's
        # git identity in its tracked env block, which is exactly what
        # commit-identity.sh exists to resolve per session instead. Merged
        # into the fixture's existing env block rather than replacing it
        # (practice: fixture-owns-its-state) -- this repo's own
        # .claude/settings.json already carries TZ, and a plant that
        # clobbered it would prove the check fires on a tree that no
        # longer resembles a real one. No identity.json is planted beside
        # it: this fixture is not an individual practice source, so the
        # check's one exemption must not apply here, or the case would
        # pass for the wrong reason.
        def _plant_hardcoded_identity(repo):
            def _add_identity(t):
                d = json.loads(t)
                env = d.setdefault('env', {})
                env['GIT_AUTHOR_NAME'] = 'Planted Person'
                env['GIT_AUTHOR_EMAIL'] = 'planted@example.com'
                return json.dumps(d, indent=2) + '\n'
            rewrite(repo, '.claude/settings.json', _add_identity)
        case('no-hardcoded-git-identity', _plant_hardcoded_identity)

        # repo-name-compare-via-helper -- a tool comparing a clone's origin
        # with a declared URL letter for letter, the freshness check's own
        # shape before 2026-10-31.
        def _plant_raw_repo_compare(repo):
            (repo / 'tools' / 'planted_repo_compare.py').write_text(
                'def same(origin, repo_url):\n'
                '    return origin == repo_url\n', encoding='utf-8')
        case('repo-name-compare-via-helper', _plant_raw_repo_compare)
        cases.append(('repo-name-compare-via-helper: the planted violation '
                      'names the file, line and comparison',
                      'tools/planted_repo_compare.py:2' in
                      planted['repo-name-compare-via-helper'][1]
                      and 'origin == repo_url' in
                      planted['repo-name-compare-via-helper'][1]))

        # declared-repo-spelling -- a copy manifest recording a declared
        # source's repository in lowercase, as checkin.py record did from a
        # lowercase add_repo clone. Merged into precedent.json's sources
        # (practice: fixture-owns-its-state).
        def _plant_repo_spelling(repo):
            def _add_source(t):
                d = json.loads(t)
                d.setdefault('sources', []).append(
                    {'level': 'shared', 'name': 'plantedset',
                     'path': 'process/plantedset', 'vendored': True,
                     'repo': 'https://github.com/owner/PlantedSet'})
                return json.dumps(d, indent=2) + '\n'
            rewrite(repo, 'precedent.json', _add_source)
            (repo / 'process').mkdir(exist_ok=True)
            (repo / 'process' / 'manifest_plantedset.json').write_text(
                json.dumps({'upstream': {
                    'repo': 'https://github.com/owner/plantedset'}}),
                encoding='utf-8')
        case('declared-repo-spelling', _plant_repo_spelling)
        cases.append(('declared-repo-spelling: the planted violation names '
                      'both spellings',
                      'https://github.com/owner/plantedset' in
                      planted['declared-repo-spelling'][1]
                      and 'https://github.com/owner/PlantedSet' in
                      planted['declared-repo-spelling'][1]))
        cases.append(('no-hardcoded-git-identity: the planted violation '
                      'names the hardcoded fields it found',
                      'GIT_AUTHOR_NAME' in planted['no-hardcoded-git-identity'][1]
                      and 'GIT_AUTHOR_EMAIL'
                      in planted['no-hardcoded-git-identity'][1]))

        # workflow-yaml-github-can-parse -- a workflow file using a YAML
        # merge key, which PyYAML resolves and GitHub's workflow parser
        # refuses. The plant also carries a plain anchor and alias (legal on
        # GitHub since 2025-09-18) and a heredoc `cat <<EOF` in a run step,
        # ON PURPOSE: the check must name the merge-key line and neither of
        # the others. Line 11 is the merge key.
        def _plant_workflow_anchor(repo):
            wf = repo / '.github' / 'workflows'
            wf.mkdir(parents=True, exist_ok=True)
            (wf / 'anchor-probe.yml').write_text(
                'name: probe\n'
                'on:\n'
                '  push:\n'
                "    paths: &probe_paths\n"
                "      - '**/*.md'\n"
                '  pull_request:\n'
                '    paths: *probe_paths\n'
                'env: &base_env\n'
                '  A: 1\n'
                'defaults:\n'
                '  <<: *base_env\n'
                'jobs:\n'
                '  a:\n'
                '    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - run: cat <<EOF && echo "a && b" 2>&1; ls *.md || true\n',
                encoding='utf-8')
        case('workflow-yaml-github-can-parse', _plant_workflow_anchor)

        # generated-files-registered (2026-09-29): the incident was a
        # generated index gone stale with nothing checking it, so the plant
        # is a hand edit to todo/TODO.md, plus an unlisted file that says it
        # is generated -- the list's reverse half.
        def _plant_generated_drift(repo):
            with (repo / 'todo' / 'TODO.md').open('a', encoding='utf-8') as fh:
                fh.write('\nA hand edit the next regeneration would discard.\n')
            (repo / 'unlisted-view.md').write_text(
                '---\ngenerated_by: tools/some_builder.py\n---\n\n# x\n',
                encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', 'unlisted-view.md'],
                           capture_output=True)
        case('generated-files-registered', _plant_generated_drift)

        def _plant_undecided_file(repo):
            (repo / 'zzz-newplace').mkdir()
            (repo / 'zzz-newplace' / 'notes.md').write_text('x\n',
                                                          encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', 'zzz-newplace'],
                           capture_output=True)
        case('vendoring-decided', _plant_undecided_file)

        def _plant_small_resident_cap(repo):
            reg = repo / 'tools' / 'session_load_budgets.json'
            data = json.loads(reg.read_text(encoding='utf-8'))
            # Caps bind only with no session-load total declared.
            data.pop('session_load_tokens', None)
            data['resident_block_tokens'] = 100
            reg.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        case('loader-within-caps', _plant_small_resident_cap)
        _gf = planted['generated-files-registered'][1]
        cases.append(('generated-files-registered: the planted violation names '
                      'the stale index and the unlisted generated file, and '
                      'not the other index the same command writes',
                      'todo/TODO.md' in _gf and 'unlisted-view.md' in _gf
                      and 'todo/CLOSED.md' not in _gf))
        _wy = planted['workflow-yaml-github-can-parse'][1]
        cases.append(('workflow-yaml-github-can-parse: the planted violation '
                      'names the file and the merge key at its line only, '
                      'not the plain anchor, the alias or the heredoc',
                      'anchor-probe.yml' in _wy and 'merge key' in _wy
                      and 'line 11 ' in _wy))

        # ...and the same failure in the OTHER hook layout. A practice set
        # created by precedent_bootstrap_source.py wires its hooks out of a
        # tracked `bootstrap/` and has no .claude/hooks/ at all, so sweeping
        # only the conventional directory declined as NotApplicable there
        # while five real hooks sat unchecked -- measured 2026-09-14 against
        # a real individual set. Two plants, because the sweep is driven by
        # what settings*.json actually wires: the directory is in scope only
        # when a hook is declared out of it.
        # The planted names are spelled `<dir>/<name>` NOWHERE in this
        # file, and that is load-bearing rather than fussy. The check reads
        # tools/*.py for callers, this source sits in tools/, and a path
        # reference written here would make the planted orphan reachable --
        # the same unfalsifiability that made the first version of this
        # check pass its own plant, caught then by matching a bare filename
        # and reintroduced here by an assertion string. So the directory is
        # joined at runtime and only the bare basename is ever a literal.
        _BS_ORPHAN = 'zzz-bootstrap-orphan.sh'
        _BS_LIVE = 'zzz-bootstrap-live.sh'
        _bs_ref = lambda n: 'bootstrap' + '/' + n

        def _plant_bootstrap(repo, wire):
            (repo / 'bootstrap').mkdir(exist_ok=True)
            for n in (_BS_LIVE, _BS_ORPHAN):
                (repo / 'bootstrap' / n).write_text('#!/bin/sh\necho x\n',
                                                    encoding='utf-8')
            if wire:
                sp = repo / '.claude' / 'settings.json'
                d = json.loads(sp.read_text(encoding='utf-8'))
                d.setdefault('hooks', {}).setdefault('SessionStart', []).append(
                    {'hooks': [{'type': 'command',
                                'command': '$CLAUDE_PROJECT_DIR/'
                                           + _bs_ref(_BS_LIVE)}]})
                sp.write_text(json.dumps(d, indent=2), encoding='utf-8')

        _bs = fresh('hooks-reachable-bootstrap')
        _plant_bootstrap(_bs, wire=True)
        _bs_rc, _bs_out = run(_bs, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: an orphan in a '
                      'bootstrap/ a settings entry wires hooks out of is '
                      'found, so a source set is not silently unswept',
                      _bs_rc == 1 and _bs_ref(_BS_ORPHAN) in _bs_out))
        cases.append(('hooks-on-disk-are-reachable: THE DISCRIMINATING CASE '
                      '-- the hook that settings entry DECLARES is not '
                      'reported alongside it',
                      _bs_ref(_BS_LIVE) not in _bs_out))

        _bs2 = fresh('hooks-reachable-bootstrap-unwired')
        _plant_bootstrap(_bs2, wire=False)
        _bs2_rc, _bs2_out = run(_bs2, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: THE DISCRIMINATING CASE '
                      '-- a bootstrap/ no settings entry wires hooks out of '
                      'is not swept, so the sweep follows declarations and '
                      'does not just walk every directory',
                      _bs2_rc == 0 and _BS_ORPHAN not in _bs2_out))

        # ...and the DECLINE, since 2026-09-14. A source declares its
        # harness adapters and the consuming repo's sync writes them into
        # .claude/hooks/ without touching settings.json, on purpose -- so a
        # repo that does not want one cannot end up wired, and before this
        # the check reported that correct decision as an orphan forever.
        # Four states, because a decline is only worth having if the three
        # ways it can be wrong are reported too: no reason, no such file,
        # and a decline sitting beside a hook that actually runs.
        # Same spelling discipline as the block above -- the declined path
        # is joined at runtime, never written here as a path literal, or
        # this source (which the check reads as a possible caller) would
        # make its own planted orphan reachable.
        _DECLINED = 'zzz-declined.sh'
        _hook_ref = lambda n: '.claude/' + 'hooks' + '/' + n

        def _plant_decline(repo, reason=None, path=None, also_wire=False):
            (repo / '.claude' / 'hooks' / _DECLINED).write_text(
                '#!/bin/sh\necho declined\n', encoding='utf-8')
            if also_wire:
                sp = repo / '.claude' / 'settings.json'
                d = json.loads(sp.read_text(encoding='utf-8'))
                d.setdefault('hooks', {}).setdefault('SessionStart', []).append(
                    {'hooks': [{'type': 'command',
                                'command': '$CLAUDE_PROJECT_DIR/'
                                           + _hook_ref(_DECLINED)}]})
                sp.write_text(json.dumps(d, indent=2), encoding='utf-8')
            cp = repo / 'precedent.json'
            cfg = json.loads(cp.read_text(encoding='utf-8'))
            entry = {'path': path if path is not None
                     else _hook_ref(_DECLINED)}
            if reason is not None:
                entry['reason'] = reason
            cfg['declined_adapters'] = [entry]
            cp.write_text(json.dumps(cfg, indent=2), encoding='utf-8')

        _d1 = fresh('hooks-decline-declared')
        _plant_decline(_d1, reason='our own bootstrap already does this')
        _d1_rc, _d1_out = run(_d1, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: a hook declined WITH a '
                      'reason is satisfied by the reason, not by wiring it',
                      _d1_rc == 0 and _DECLINED not in _d1_out))

        _d2 = fresh('hooks-decline-reasonless')
        _plant_decline(_d2, reason=None)
        _d2_rc, _d2_out = run(_d2, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: a decline with NO reason '
                      'is a silenced check and is reported as one',
                      _d2_rc == 1 and 'with no reason' in _d2_out
                      and _DECLINED in _d2_out))

        _d3 = fresh('hooks-decline-stale-path')
        _plant_decline(_d3, reason='we do not want it',
                       path=_hook_ref('zzz-not-here.sh'))
        _d3_rc, _d3_out = run(_d3, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: a decline naming a file '
                      'that is not there is reported, so an exemption cannot '
                      'outlive what it exempted',
                      _d3_rc == 1 and 'no such file is here' in _d3_out))
        # The plant above ALSO leaves a real orphan on disk, undeclined.
        # Asserting only the stale-path message would pass on the orphan
        # finding alone (practice: control-asserts-which-failure).
        cases.append(('hooks-on-disk-are-reachable: ...and that case reports '
                      'the stale declaration separately from the orphan it '
                      'failed to cover',
                      'zzz-not-here.sh' in _d3_out and _DECLINED in _d3_out))

        _d4 = fresh('hooks-decline-contradicted')
        _plant_decline(_d4, reason='we decided against it', also_wire=True)
        _d4_rc, _d4_out = run(_d4, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: a decline for a hook '
                      'something DOES call is reported, because the note is '
                      'what the next reader trusts',
                      _d4_rc == 1 and 'something does call it' in _d4_out))

        # A comment or docstring naming the declined hook is prose, not a
        # call. Before 2026-09-25 the engine's own commentary about
        # freshness-guard.sh made a consuming repo's decline read as stale.
        # The string-literal line is the control: the same path as code
        # still counts, so the fix did not just stop reading tools/.
        def _plant_mentions(repo, as_code):
            ref = _hook_ref(_DECLINED)
            body = (f'"""Explains {ref}."""\n'
                    f'# {ref} is declined here\n')
            if as_code:
                body += f'HOOK = {ref!r}\n'
            (repo / 'tools' / 'zzz_mentions.py').write_text(
                body, encoding='utf-8')

        _d5 = fresh('hooks-decline-mentioned-in-prose')
        _plant_decline(_d5, reason='we decided against it')
        _plant_mentions(_d5, as_code=False)
        _d5_rc, _d5_out = run(_d5, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: an engine comment or '
                      'docstring naming a declined hook does not make the '
                      'decline stale',
                      _d5_rc == 0 and 'something does call it' not in _d5_out))

        _d6 = fresh('hooks-decline-called-from-code')
        _plant_decline(_d6, reason='we decided against it')
        _plant_mentions(_d6, as_code=True)
        _d6_rc, _d6_out = run(_d6, 'hooks-on-disk-are-reachable')
        cases.append(('hooks-on-disk-are-reachable: ...while the same path as '
                      'a string literal in engine code still counts as a call',
                      _d6_rc == 1 and 'something does call it' in _d6_out))

        # engine-plus-host-shims -- a host-tree fork of a vendored module
        def _setup_vendored(repo):
            up = repo / 'process' / 'upstream' / 'tools'
            up.mkdir(parents=True)
            body = '\n'.join(f'    value_{i} = compute_something({i}, base)'
                             for i in range(12))
            (up / 'engine.py').write_text(
                'def engine(base):\n' + body + '\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'vendor')
        def _plant_fork(repo):
            shutil.copy(repo / 'process' / 'upstream' / 'tools' / 'engine.py',
                        repo / 'tools' / 'engine_fork.py')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'fork')
        case('engine-plus-host-shims', _plant_fork, setup=_setup_vendored)
        # ...and must NOT fire on a host tools/bootstrap.sh that matches the
        # upstream's own tools/bootstrap.sh: both are instantiations of
        # templates/bootstrap.sh, so the match proves the install, not a fork
        # (2026-09-23, the first precedent_check run in a migrated consumer).
        _sb = fresh('shims-bootstrap-instantiation')
        (_sb / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        shutil.copy(_sb / 'tools' / 'bootstrap.sh',
                    _sb / 'process' / 'upstream' / 'tools' / 'bootstrap.sh')
        git(_sb, 'add', '-A')
        git(_sb, 'commit', '-qm', 'vendor')
        _sb_rc, _sb_out = run(_sb, 'engine-plus-host-shims')
        cases.append(('engine-plus-host-shims: a host tools/bootstrap.sh that '
                      'matches the upstream\'s own instantiation of the '
                      'bootstrap template is not reported as a fork',
                      _sb_rc == 0 and 'duplicates' not in _sb_out))

        # doc-references-are-links -- a line that renders <del> on GitHub
        case('doc-references-are-links',
             lambda repo: rewrite(repo, 'TODO.md',
                                  lambda t: t + '\nabout ~5 items~ remain.\n'))

        # label-describes-content -- a "(one line)" label over a multi-line block
        case('label-describes-content',
             lambda repo: (repo / 'planted-label.md').write_text(
                 '# Doc\n\n## Summary (one line)\n\nThis section actually\n'
                 'runs to two separate lines of text.\n', encoding='utf-8'))

        # acronyms-glossary -- a changed doc introduces a new unglossed acronym
        case('acronyms-glossary',
             lambda repo: rewrite(repo, 'TODO.md',
                                  lambda t: t + '\nSee the new ZQX report.\n'))

        # ...and the same acronym, already unglossed in a COMMITTED file,
        # copied into a brand-new path must NOT fail. read_base(f) only ever
        # checks this file's own path in the base tree, so a migration that
        # moves content to a new path (TODO.md -> todo/*.md is the real
        # incident this reproduces) left it blind: identical prose read as
        # newly introduced at its new path and clean at its old one.
        _mig = fresh('acronyms-glossary-migrated-path')
        rewrite(_mig, 'TODO.md', lambda t: t + '\nSee the new ZQX report.\n')
        git(_mig, 'add', '-A')
        git(_mig, 'commit', '-qm', 'plant ZQX in TODO.md')
        (_mig / 'planted-migrated.md').write_text(
            'See the new ZQX report.\n', encoding='utf-8')
        _rc_mig, _out_mig = run(_mig, 'acronyms-glossary')
        cases.append(('acronyms-glossary: an unglossed acronym copied to a '
                      'brand-new path, already unglossed elsewhere in the '
                      'base tree, does NOT fail -- a migration moved it, '
                      'the change did not introduce it',
                      _rc_mig == 0 and 'VIOLATION' not in _out_mig))

        # ...and the same new acronym in a file the repository declares as
        # the person's own material (precedent.json `content_paths`,
        # 2026-10-13) is theirs to leave: the gate skips it. The case
        # above that plants it with no declaration is the control.
        _cnt = fresh('acronyms-glossary-content-path')
        _cfg_path = _cnt / 'precedent.json'
        _cfg = json.loads(_cfg_path.read_text(encoding='utf-8'))
        _cfg.setdefault('content_paths', []).append('TODO.md')
        _cfg_path.write_text(json.dumps(_cfg, indent=2) + '\n', encoding='utf-8')
        git(_cnt, 'add', '-A')
        git(_cnt, 'commit', '-qm', 'declare TODO.md as content')
        rewrite(_cnt, 'TODO.md', lambda t: t + '\nSee the new ZQX report.\n')
        _rc_cnt, _out_cnt = run(_cnt, 'acronyms-glossary')
        cases.append(('acronyms-glossary: a new unglossed acronym in a file '
                      'under content_paths does NOT fail -- the person\'s own '
                      'material, not session work',
                      _rc_cnt == 0 and 'ZQX' not in _out_cnt))

        # ci-commits-carry-identity -- a workflow that commits as the bot.
        # The fixture is the real shape: the two `git config` lines and the
        # `git commit` that a scheduled refresh workflow actually runs.
        def _plant_ci_identity(repo):
            wf = repo / '.github' / 'workflows'
            wf.mkdir(parents=True, exist_ok=True)
            (wf / 'zzz-refresh.yml').write_text(
                'name: refresh\non: {schedule: [{cron: "0 6 * * 1"}]}\n'
                'jobs:\n  r:\n    runs-on: ubuntu-latest\n    steps:\n'
                '      - run: |\n'
                '          git config user.name  "github-actions[bot]"\n'
                '          git add -A\n'
                '          git commit -m "refresh"\n', encoding='utf-8')
        case('ci-commits-carry-identity', _plant_ci_identity)

        # ...and the FIXED workflow, still carrying the incident note its own
        # fix is about, must PASS. This is the case that did not exist when
        # the check landed, and its absence shipped a false positive within
        # the hour: CI_BOT_RE read the raw file while CI_COMMIT_RE read the
        # comment-stripped body, so a workflow explaining why it does NOT
        # use the bot was reported as one that does. The only ways out were
        # deleting the explanation or wording around it -- the check
        # punished a repo for citing the incident. Found independently by
        # two sessions, each against a real workflow, neither of which had
        # done anything wrong.
        fixed = fresh('ci-commits-carry-identity-documented')
        wf_dir = fixed / '.github' / 'workflows'
        wf_dir.mkdir(parents=True, exist_ok=True)
        (wf_dir / 'zzz-refresh.yml').write_text(
            'name: refresh\non: {schedule: [{cron: "0 6 * * 1"}]}\n'
            'jobs:\n  r:\n    runs-on: ubuntu-latest\n    steps:\n'
            '      - run: |\n'
            '          # THE AUTHOR COMES FROM identity.json, NEVER the\n'
            '          # runner. This step hardcoded `github-actions[bot]`\n'
            '          # and committed on the runner UTC clock.\n'
            '          NAME=$(python3 -c \'import json;'
            'print(json.load(open("identity.json"))["name"])\')\n'
            '          [ -z "$NAME" ] && exit 1\n'
            '          git config user.name "$NAME"\n'
            '          TZ="$DECLARED_TZ" git commit -m "refresh"\n',
            encoding='utf-8')
        rc_fixed, out_fixed = run(fixed, 'ci-commits-carry-identity')
        cases.append(('ci-commits-carry-identity: a FIXED workflow that '
                      'documents the bot-authorship incident in a comment '
                      'passes -- the check reads code, not prose, so citing '
                      'the incident is never what fires it',
                      rc_fixed == 0 and 'VIOLATION' not in out_fixed))

        # github-setup-disclosed -- a new workflow file, undisclosed
        case('github-setup-disclosed',
             lambda repo: (repo / '.github' / 'workflows' / 'zzz-planted.yml')
                 .write_text('name: planted\non: push\njobs: {}\n', encoding='utf-8'))

        # ...and the same workflow DISCLOSED in GETTING_STARTED.md must pass.
        # The negative case above passed all along; this is the half that did
        # not exist, and its absence let a three-way contradiction stand:
        # the practice's Rule names GETTING_STARTED.md's administrator
        # section, the check read only a root GITHUB_ACTIONS.md, and
        # INSTALL.md §1 step 6's root-hygiene list forbids GITHUB_ACTIONS.md
        # at a dependent repo's root. A repo that FOLLOWED the practice
        # failed the check (2026-09-10). Nothing here would have noticed,
        # because nothing here ever satisfied the practice.
        def _disclosed_in_getting_started(repo):
            (repo / '.github' / 'workflows' / 'zzz-planted.yml').write_text(
                'name: planted\non: push\njobs: {}\n', encoding='utf-8')
            (repo / 'GETTING_STARTED.md').write_text(
                '# Getting Started\n\n## For the Administrator\n\n'
                '### Automatic Checks Installed for This Project\n\n'
                '- A Markdown check runs on every pull request '
                '(`zzz-planted.yml`). It needs no maintenance.\n',
                encoding='utf-8')
        disclosed = fresh('github-setup-disclosed-getting-started')
        _disclosed_in_getting_started(disclosed)
        rc_disc, out_disc = run(disclosed, 'github-setup-disclosed')
        cases.append(('github-setup-disclosed: a workflow named in '
                      "GETTING_STARTED.md's administrator section satisfies "
                      'the check -- the document the Rule actually names, and '
                      'the one root hygiene lets a dependent repo have',
                      rc_disc == 0 and 'VIOLATION' not in out_disc))

        # ...and disclosure in documentation/GITHUB_ACTIONS.md must pass too
        # -- BestPractice's own self-disclosure path since its copy moved
        # off the root on 2026-09-20 (DISCLOSURE_DOCS in precedent_check.py).
        # Never exercised before this: the only other positive case tests
        # GETTING_STARTED.md, so a typo in the third DISCLOSURE_DOCS entry
        # would have shipped silently.
        def _disclosed_in_doc_github_actions(repo):
            (repo / '.github' / 'workflows' / 'zzz-planted.yml').write_text(
                'name: planted\non: push\njobs: {}\n', encoding='utf-8')
            (repo / 'documentation').mkdir(parents=True, exist_ok=True)
            (repo / 'documentation' / 'GITHUB_ACTIONS.md').write_text(
                '# GitHub Actions\n\nRuns `zzz-planted.yml` on every push.\n',
                encoding='utf-8')
        disclosed_doc_ga = fresh('github-setup-disclosed-documentation-github-actions')
        _disclosed_in_doc_github_actions(disclosed_doc_ga)
        rc_doc_ga, out_doc_ga = run(disclosed_doc_ga, 'github-setup-disclosed')
        cases.append(('github-setup-disclosed: a workflow named in '
                      'documentation/GITHUB_ACTIONS.md satisfies the check -- '
                      "BestPractice's own self-disclosure path now that its "
                      'copy is not at the root',
                      rc_doc_ga == 0 and 'VIOLATION' not in out_doc_ga))

        # docs-are-current-state -- an in-document revision annotation
        case('docs-are-current-state',
             lambda repo: (repo / 'planted-revision.md').write_text(
                 '# Doc\n\nThe timeout is 30s (updated 2026-01-15).\n',
                 encoding='utf-8'))

        # index-remembers-past -- inline lineage language in a document
        case('index-remembers-past',
             lambda repo: (repo / 'planted-lineage.md').write_text(
                 '# New Doc\n\nThis document is the successor to the old one.\n',
                 encoding='utf-8'))

        # ...and the exemption added 2026-09-07 is not a blanket one. The
        # case above plants the phrase in a plain document and must still
        # fail; this plants the SAME phrase in a document carrying the
        # <!--record-doc--> marker and must pass. Both halves are needed:
        # an exemption tested only by the thing it exempts proves nothing
        # about what it still catches, and the failure mode of a widened
        # skip rule is silence, which no single case can see.
        # (practice: control-asserts-which-failure)
        _rd = fresh('index-remembers-past-record-doc')
        (_rd / 'planted-lineage-record.md').write_text(
            '<!--record-doc--> A dated log, kept for one future '
            'conversation.\n\n# Log\n\nThe 2026-01-01 entry is '
            'superseded by the one above.\n', encoding='utf-8')
        _rc_rd, _out_rd = run(_rd, 'index-remembers-past')
        cases.append(('index-remembers-past: the same phrase in a '
                      '<!--record-doc--> document does NOT fail -- a '
                      'historical record is where lineage belongs',
                      _rc_rd == 0 and 'VIOLATION' not in _out_rd))

        # ...and the same lineage phrase, already committed somewhere in the
        # base tree, copied to a brand-new path must NOT fail either -- same
        # fix, same reason as acronyms-glossary's migrated-path case above.
        _migl = fresh('index-remembers-past-migrated-path')
        (_migl / 'source-lineage.md').write_text(
            '# Doc\n\nThis document is the successor to the old one.\n',
            encoding='utf-8')
        git(_migl, 'add', '-A')
        git(_migl, 'commit', '-qm', 'plant lineage phrase')
        (_migl / 'planted-migrated-lineage.md').write_text(
            '# New Doc\n\nThis document is the successor to the old one.\n',
            encoding='utf-8')
        _rc_migl, _out_migl = run(_migl, 'index-remembers-past')
        cases.append(('index-remembers-past: the same lineage phrase copied '
                      'to a brand-new path, already present in the base '
                      "tree, does NOT fail -- a migration moved it, the "
                      "change didn't introduce it",
                      _rc_migl == 0 and 'VIOLATION' not in _out_migl))

        # deliverables-look-like-output -- process residue in a deliverable
        case('deliverables-look-like-output',
             lambda repo: (repo / 'report.md').write_text(
                 '# Report\n\nThe number is 4. [verify later]\n', encoding='utf-8'))

        # search-by-purpose -- a document carrying generated numbers, indexed
        # from nothing a reader consults
        def _plant_sbp(repo):
            # Scrub the reference from EVERY index file the check reads, taken
            # from doc_lint's own list rather than named here. The three were
            # hardcoded until 2026-09-14, when the quick index was split and
            # WHERE_THINGS_ARE.md became a fourth: the plant then left the
            # reference standing in a file the check consults, so the planted
            # violation stopped firing and this control silently passed while
            # proving nothing (practice: fixture-owns-its-state -- whatever a
            # fixture asserts on, it must own).
            import doc_lint as _dl
            for _idx in _dl.INDEX_FILES:
                if (repo / _idx).exists():
                    rewrite(repo, _idx,
                            lambda t: t.replace('spec/LOADER.md', 'spec/x.md'))
            rewrite(repo, 'spec/LOADER.md', lambda t: t + '\n')
        case('search-by-purpose', _plant_sbp)

        # computed-numbers-in-scripts -- a generated block edited by hand
        def _plant_cnis(repo):
            n = len(list((repo / 'practices').glob('*.md')))
            rewrite(repo, 'spec/LOADER.md', lambda t: t.replace(
                f'| Practices in the catalogue | {n} |',
                f'| Practices in the catalogue | {n + 9} |'))
        case('computed-numbers-in-scripts', _plant_cnis)

        # timestamps-carry-offset -- a bare date.today() in a tracked .py
        #
        # Planted as CODE, not as a comment mentioning the call: the check
        # parses rather than greps precisely because its first draft matched
        # its own explanatory comments in the twelve files it had migrated.
        def _plant_tco(repo):
            (repo / 'tools' / 'zz_naive_stamp.py').write_text(
                '#!/usr/bin/env python3\nimport datetime\n\n\n'
                'def when():\n    return datetime.date.today().isoformat()\n',
                encoding='utf-8')
        case('timestamps-carry-offset', _plant_tco)

        # one-python -- a tool that starts python3 by name
        def _plant_onepy(repo):
            (repo / 'tools' / 'zz_starts_python3.py').write_text(
                '#!/usr/bin/env python3\nimport subprocess\n\n\n'
                "def go():\n    subprocess.run(['python3', 'tools/x.py'])\n",
                encoding='utf-8')
        case('one-python', _plant_onepy)

        # tracked-practice-files -- a practice file left out of the index
        def _plant_tpf(repo):
            src = next((repo / 'practices').glob('*.md'))
            (repo / 'practices' / 'zz-forgotten-add.md').write_text(
                src.read_text(encoding='utf-8').replace(
                    'slug:        ' + src.stem,
                    'slug:        zz-forgotten-add'),
                encoding='utf-8')
            # deliberately NOT `git add`ed -- that is the whole violation
        case('tracked-practice-files', _plant_tpf)

        # index-required-is-declared -- a practice whose occasion reads as a
        # SPOKEN trigger ("when a person says ...") while a glob and a gate
        # route it, and which declares no index_required either way. That is
        # the exact shape whose index line build_views would drop, silently
        # un-routing a phrase no glob or gate can ever fire on.
        def _plant_ird(repo):
            (repo / 'practices' / 'zzz-spoken-trigger.md').write_text(
                '---\nslug:        zzz-spoken-trigger\n'
                'title:       A spoken trigger\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["docs/**"]\n'
                'occasion:    "a person says \\"Wind It Back\\""\n'
                'gates:       ["reply"]\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nsupersedes:  []\n'
                'overrides:   null\nadded:       "2026-09-14"\n'
                'approved_by: "fixture"\n---\n\n## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        case('index-required-is-declared', _plant_ird)

        # code-owner-practice-stays-out-of-the-index -- a practice for code
        # owners whose only route is the occasion index, so every code
        # owner's session file pays a line for it (2026-10-08).
        def _plant_copsooti(repo):
            (repo / 'practices' / 'zzz-owner-only.md').write_text(
                '---\nslug:        zzz-owner-only\n'
                'title:       An owner-only rule\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\n'
                'occasion:    "running the repository a planted way"\n'
                'gates:       []\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nsupersedes:  []\n'
                'overrides:   null\nadded:       "2026-10-08"\n'
                'approved_by: "fixture"\nvisible_to:  code-owners\n---\n\n'
                '## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        case('code-owner-practice-stays-out-of-the-index', _plant_copsooti)

        # adds-to-names-a-rule-in-force -- an addition that names itself, so
        # no rule carries it and no session is shown it (2026-10-09). Itself
        # rather than an unknown slug: the fixture's other sources do not
        # resolve, and a base that might live in one is could-not-verify.
        def _plant_atnarif(repo):
            (repo / 'practices' / 'zzz-own-addition.md').write_text(
                '---\nslug:        zzz-own-addition\n'
                'title:       An addition to itself\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\n'
                'occasion:    "doing a planted thing"\n'
                'gates:       []\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nsupersedes:  []\n'
                'overrides:   null\nadds_to:     zzz-own-addition\n'
                'added:       "2026-10-09"\n'
                'approved_by: "fixture"\n---\n\n'
                '## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        case('adds-to-names-a-rule-in-force', _plant_atnarif)

        # own-deduplication-points-somewhere -- a set's own stub whose target
        # no source it takes holds (2026-10-20). The fixture is made a shared
        # set that declares only its repo-local source, so nothing it takes fails to resolve
        # and the stranded stub is a violation, not a could-not-verify.
        def _setup_odps(repo):
            import json as _j
            src = _j.loads((repo / 'precedent-source.json').read_text(encoding='utf-8'))
            (repo / 'precedent-source.json').write_text(_j.dumps(
                dict(src, level='shared', brings=[])), encoding='utf-8')
            cfg = _j.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
            cfg['sources'] = [s for s in cfg.get('sources') or []
                              if s.get('path') == 'local']
            (repo / 'precedent.json').write_text(_j.dumps(cfg), encoding='utf-8')

        def _plant_odps(repo):
            (repo / 'practices' / 'zzz-stranded.md').write_text(
                '---\nslug:        zzz-stranded\n'
                'title:       A pointer to a rule no source holds\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  []\n'
                'occasion:    "doing a planted thing"\n'
                'gates:       []\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      deduplicated\n'
                'in_force_at: zzz-held-nowhere\nsupersedes:  []\n'
                'overrides:   null\nadded:       "2026-10-20"\n'
                'approved_by: "fixture"\n---\n\n'
                '## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        case('own-deduplication-points-somewhere', _plant_odps, setup=_setup_odps)

        # boildown-moments-named -- a practice whose occasion quotes the
        # archive sentence instead of naming the moment (2026-10-20).
        def _plant_bmn(repo):
            (repo / 'practices' / 'zzz-quotes-the-line.md').write_text(
                '---\nslug:        zzz-quotes-the-line\n'
                'title:       A practice that copies a moment\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\n'
                'occasion:    "a reply that says You can archive this session"\n'
                'gates:       ["reply"]\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nsupersedes:  []\n'
                'overrides:   null\nadded:       "2026-10-20"\n'
                'approved_by: "fixture"\n---\n\n'
                '## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        case('boildown-moments-named', _plant_bmn)


        # docs-track-models -- an owned figure restated in the prose
        #
        # THE FIGURE IS DERIVED, not typed. This plant used to hardcode
        # "6 of {n} practices" -- the resident-set count on the day it was
        # written. `docs-track-models` fires on a restatement of a string a
        # script DECLARES it owns, so the moment the resident set grew to 7
        # (2026-09-07, promoting bold-key-phrases to universal) the planted
        # sentence said "6 of 68" while the owned string was "7 of 68": the
        # plant landed, matched nothing, and the harness reported the CHECK
        # as broken. It was the fixture. Asking doc_sync for the owned
        # string means the plant is whatever the check is currently looking
        # for, and neither can drift from the other.
        def _plant_dtm(repo):
            import doc_sync as _ds
            owned = [f for _d, _n, s in _ds.PAIRS for f in _ds.owned_figures(s)]
            phrase = next((v[0] for name, v in owned
                           if name == 'resident set' and v), None)
            if phrase is None:                      # nothing owned to restate
                return

            # Anchor on doc_sync's own closing sentinel, NOT on a heading.
            # 2026-09-08: this plant anchored on the literal heading
            # '## The resident set, and why these six'; renaming that heading
            # (it said "six" while there were ten -- no-stale-counts) made the
            # plant match nothing, so the check correctly found no violation
            # and the negative control read as "the CHECK is broken" -- the
            # identical failure the comment above records, one layer out. A
            # sentinel is owned by doc_sync and cannot drift when prose is
            # reworded. (practice: control-asserts-which-failure)
            anchor = '<!--/gen:catalogue-->'

            def _insert(text):
                if anchor not in text:
                    raise AssertionError(
                        f'docs-track-models plant: anchor {anchor!r} is gone '
                        'from spec/LOADER.md -- the FIXTURE is broken, not '
                        'the check. Re-anchor the plant.')
                return text.replace(
                    anchor, f'{anchor}\n\nThe resident block is {phrase}.', 1)

            rewrite(repo, 'spec/LOADER.md', _insert)
        case('docs-track-models', _plant_dtm)

        # scrub-gate -- a blocked term in a tree destined for another repo
        def _root_doc_entries(repo):
            names = ['INSTALL.md', 'PRACTICES.md', 'SETUP.md',
                     'GITHUB_ACTIONS.md', 'MOBILE.md', 'METHOD.md', 'GIT.md']
            return [{'practice': n, 'local_path': n, 'status': 'local-only',
                     'granularity': 'file',
                     'notes': 'this fixture is the upstream repo itself'}
                    for n in names if (repo / n).exists()]

        def _setup_pack(repo):
            (repo / 'process' / 'upstream').mkdir(parents=True)
            (repo / 'process' / 'upstream' / 'note.md').write_text(
                'generic guidance\n', encoding='utf-8')
            (repo / 'process' / 'scrub_blocklist.txt').write_text(
                'zorbulon\n', encoding='utf-8')
            # The root-hygiene check (practice_audit's check 4) is right to
            # object that this fixture's root holds INSTALL.md, PRACTICES.md
            # and friends: it makes the upstream repo LOOK like a dependent
            # one. Claim them, which is the escape hatch that check names.
            (repo / 'process' / 'manifest.json').write_text(json.dumps({
                'upstream': {'vendored_at': 'process/upstream'},
                'entries': _root_doc_entries(repo),
            }, indent=2), encoding='utf-8')
        def _plant_scrub(repo):
            (repo / 'process' / 'upstream' / 'note.md').write_text(
                'guidance for zorbulon\n', encoding='utf-8')
        case('scrub-gate', _plant_scrub, setup=_setup_pack)

        # migration-scrubs-vocabulary -- a declared retired term still
        # appears outside the declared exempt files
        def _setup_retired_vocab(repo):
            (repo / 'process').mkdir(parents=True, exist_ok=True)
            (repo / 'process' / 'retired_vocabulary.json').write_text(
                json.dumps({'terms': ['OldPackName'],
                            'exempt_files': ['MIGRATION.md']}),
                encoding='utf-8')
            (repo / 'MIGRATION.md').write_text(
                'OldPackName is discussed here, on purpose.\n', encoding='utf-8')
            # A CURRENT name that merely contains the retired one. A plain
            # substring match reported a live `voice_pack_sync.py` three
            # times for carrying the retired `pack_sync` (2026-09-06), with
            # no way to satisfy it but renaming a real file. This file must
            # stay clean, or the planted case below is passing for the
            # wrong reason.
            (repo / 'CURRENT.md').write_text(
                'See tools/voice_OldPackName_helper.py and '
                'my_OldPackName-thing, both current.\n', encoding='utf-8')
        # A repository's own retired terms are retired-words' to scan since
        # 2026-09-29 (migration-scrubs-vocabulary kept only the leftover-pack
        # half), so this pair runs that check: planted and clean.
        voc_repo = fresh('retired-words-repo-terms')
        _setup_retired_vocab(voc_repo)
        rc_voc_clean, out_voc_clean = run(voc_repo, 'retired-words')
        (voc_repo / 'STALE.md').write_text('Still mentions OldPackName here.\n',
                                           encoding='utf-8')
        rc_voc, out_voc = run(voc_repo, 'retired-words')
        cases.append(("retired-words: a repository's own retired term in a "
                      "live file is refused; the exempt file and a current "
                      "name that merely contains the term are not",
                      rc_voc == 1 and 'STALE.md' in out_voc
                      and 'MIGRATION.md' not in out_voc
                      and 'CURRENT.md' not in out_voc
                      and rc_voc_clean == 0, out_voc + out_voc_clean))

        # migration-scrubs-vocabulary -- what it still does: a leftover
        # pre-migration pack in a repo that has already migrated.
        def _plant_old_pack(repo):
            (repo / 'process' / 'oldpack').mkdir(parents=True, exist_ok=True)
            (repo / 'process' / 'oldpack' / 'RULES.md').write_text(
                '# old rules\n', encoding='utf-8')
            (repo / 'process' / 'manifest_oldpack.json').write_text(
                json.dumps({'upstream': {'path': 'process/oldpack'}}),
                encoding='utf-8')
        case('migration-scrubs-vocabulary', _plant_old_pack)

        # migration-scrubs-vocabulary -- a malformed config (valid JSON,
        # wrong shape: a bare array where `{"terms": [...]}` belongs) used
        # to reach `cfg.get('terms')` and raise an uncaught AttributeError
        # -- a 2026-09-03 deep-check audit found this took down the WHOLE
        # precedent_check.py run, not just this one check: zero of the
        # other ~40 checks got to report anything. Now a clean VIOLATION
        # naming the exact problem, same as any other malformed input this
        # check already handles (bad JSON syntax, above).
        malformed_repo = fresh('migration-scrubs-vocabulary-malformed')
        (malformed_repo / 'process').mkdir(parents=True, exist_ok=True)
        (malformed_repo / 'process' / 'retired_vocabulary.json').write_text(
            json.dumps(['OldPackName']), encoding='utf-8')
        rc_malf, out_malf = run(malformed_repo, 'retired-words')
        cases.append(('retired-words: a malformed config (a '
                      'JSON array where an object belongs) is a clean '
                      'VIOLATION naming the problem, not an uncaught crash',
                      rc_malf == 1 and 'VIOLATION' in out_malf
                      and 'Traceback' not in out_malf
                      and 'must be a JSON object' in out_malf,
                      out_malf))

        # migration-scrubs-vocabulary -- a `/`-suffixed exempt_files entry
        # exempts a whole DIRECTORY, not just one file (2026-09-03 fix: a
        # materialized directory like practices/, filled in by
        # precedent_materialize.py on every precedent_sync_views.py run,
        # can hold another source's own legitimate content that happens to
        # share a literal substring with a retired term -- a real
        # dependent-repo migration hit this with a shared source's own
        # `approved_by` provenance note). Both directions in one fixture:
        # the term INSIDE the exempted directory is clean; the SAME term
        # OUTSIDE it still fails -- proving this isn't a blanket disable.
        dir_exempt_repo = fresh('migration-scrubs-vocabulary-dir-exempt')
        (dir_exempt_repo / 'process').mkdir(parents=True, exist_ok=True)
        (dir_exempt_repo / 'process' / 'retired_vocabulary.json').write_text(
            json.dumps({'terms': ['OldPackName'],
                        'exempt_files': ['materialized/']}),
            encoding='utf-8')
        (dir_exempt_repo / 'materialized').mkdir(parents=True, exist_ok=True)
        (dir_exempt_repo / 'materialized' / 'other_source.md').write_text(
            'OldPackName, mentioned by a different source, on purpose.\n',
            encoding='utf-8')
        (dir_exempt_repo / 'STALE.md').write_text(
            'Still mentions OldPackName here.\n', encoding='utf-8')
        rc_dir, out_dir = run(dir_exempt_repo, 'retired-words')
        cases.append(("retired-words: a `/`-suffixed "
                      "exempt_files entry exempts everything under that "
                      "directory, but not files outside it",
                      rc_dir == 1 and 'VIOLATION' in out_dir
                      and 'materialized/other_source.md' not in out_dir
                      and 'STALE.md' in out_dir,
                      out_dir))

        # migration-scrubs-vocabulary / ROOT resolution -- when
        # precedent_check.py is VENDORED into a dependent repo at
        # process/upstream/tools/ (the documented convention --
        # spec/MIGRATING_EXISTING_INSTALLS.md step 7 also vendors
        # split_practices.py at the dependent repo's own top-level tools/,
        # which precedent_check.py needs importable), ROOT must resolve to
        # the DEPENDENT repo's own root, not process/upstream/ itself
        # (2026-09-03 fix -- Path(__file__).resolve().parents[1] got this
        # wrong in exactly that layout: a real dependent-repo migration's
        # migration-scrubs-vocabulary run silently scanned process/upstream/'s
        # own tree instead and reported a false-clean SKIPPED, no matter
        # how the check was invoked, exactly as spec/MIGRATING_EXISTING_INSTALLS.md
        # step 5 documents). Before this fix this fixture reproduced that
        # exact false-clean SKIPPED; it now correctly reports the violation
        # sitting at the dependent repo's own root.
        vendored_repo = tmp / 'migration-scrubs-vocabulary-vendored'
        (vendored_repo / 'process' / 'upstream').mkdir(parents=True)
        shutil.copytree(pristine / 'tools',
                        vendored_repo / 'process' / 'upstream' / 'tools')
        shutil.copytree(pristine / 'practices',
                        vendored_repo / 'process' / 'upstream' / 'practices')
        (vendored_repo / 'tools').mkdir(parents=True, exist_ok=True)
        shutil.copy(pristine / 'tools' / 'split_practices.py',
                   vendored_repo / 'tools' / 'split_practices.py')
        git(vendored_repo, 'init', '-q')
        git(vendored_repo, 'config', 'user.email', 'harness@example.com')
        git(vendored_repo, 'config', 'user.name', 'harness')
        (vendored_repo / 'process' / 'retired_vocabulary.json').write_text(
            json.dumps({'terms': ['OldPackName'], 'exempt_files': []}),
            encoding='utf-8')
        (vendored_repo / 'STALE.md').write_text(
            "Still mentions OldPackName here, at the dependent repo's own "
            "root.\n", encoding='utf-8')
        git(vendored_repo, 'add', '-A')
        git(vendored_repo, 'commit', '-qm', 'baseline')
        r_vend = subprocess.run(
            [sys.executable,
             str(vendored_repo / 'process' / 'upstream' / 'tools' / 'precedent_check.py'),
             '--only', 'retired-words'],
            capture_output=True, text=True, cwd=str(vendored_repo))
        out_vend = r_vend.stdout + r_vend.stderr
        cases.append(('retired-words: ROOT resolves to the '
                      'DEPENDENT repo when precedent_check.py runs vendored '
                      'at process/upstream/tools/, not to process/upstream/ '
                      'itself',
                      r_vend.returncode == 1 and 'VIOLATION' in out_vend
                      and 'STALE.md' in out_vend
                      and 'SKIPPED' not in out_vend,
                      out_vend))

        # precedent_check.py's runner -- ANY check's own uncaught bug
        # (not just this one) must fail that check alone, not abort every
        # OTHER check in the same run. Proven directly by making an
        # arbitrary, otherwise-unrelated check (`code-cites-practice`)
        # raise a bare RuntimeError, then confirming the FULL suite (no
        # --only) still completes: that one check reports ERROR, nothing
        # tracebacks to the console, and other checks still produce real
        # PASS/VIOLATION verdicts around it.
        boom_repo = fresh('precedent-check-error-isolation')
        rewrite(boom_repo, 'tools/precedent_check.py', lambda t: t.replace(
            'def _code_cites_practice(ctx):\n',
            'def _code_cites_practice(ctx):\n'
            '    raise RuntimeError("planted: an unrelated check\'s own bug")\n'))
        r_boom = subprocess.run(
            [sys.executable, str(boom_repo / 'tools' / 'precedent_check.py'),
             '--full-sweep'],
            capture_output=True, text=True, cwd=str(boom_repo))
        boom_out = r_boom.stdout + r_boom.stderr
        m_passed = re.search(r'precedent_check: (\d+) passed,', boom_out)
        cases.append(("precedent_check.py's runner: one check's uncaught "
                      "exception is isolated as its own ERROR result, "
                      "never a crash that aborts every other check",
                      'ERROR      code-cites-practice' in boom_out
                      and 'planted: an unrelated check' in boom_out
                      and 'Traceback' not in boom_out
                      and bool(m_passed) and int(m_passed.group(1)) > 10,
                      boom_out))

        # practice-export-loop -- a vendored file improved locally and never
        # exported: the entry still says "synced" and its baseline no longer
        # matches
        def _setup_manifest(repo):
            _setup_pack(repo)
            local = repo / 'tools' / 'shim.py'
            local.write_text('print("shim")\n', encoding='utf-8')
            import hashlib
            digest = hashlib.sha256(local.read_bytes()).hexdigest()
            (repo / 'process' / 'manifest.json').write_text(json.dumps({
                'upstream': {'vendored_at': 'process/upstream'},
                'entries': _root_doc_entries(repo) +
                [{'practice': 'shim', 'local_path': 'tools/shim.py',
                  'upstream_path': 'note.md', 'status': 'synced',
                  'granularity': 'file', 'local_sha256': digest}],
            }, indent=2), encoding='utf-8')
        case('practice-export-loop',
             lambda repo: (repo / 'tools' / 'shim.py').write_text(
                 'print("shim, improved")\n', encoding='utf-8'),
             setup=_setup_manifest)

        # code-cites-practice -- a code comment citing a slug that does not
        # exist (a typo, or a practice file deleted instead of retired)
        case('code-cites-practice',
             lambda repo: (repo / 'tools' / 'cite_fixture.py').write_text(
                 '# practice: this-slug-does-not-exist\nprint("x")\n',
                 encoding='utf-8'))

        # code-cites-practice -- the SAME planted citation, in a repo that
        # carries tools/ENGINE_MANIFEST.json naming that file, must NOT
        # fire: in a consuming repo the citation is upstream's, in vendored
        # code, naming a practice the consumer's own catalogue has not
        # caught up to yet. Both directions are stated, because an exemption
        # nobody has watched NOT fire is indistinguishable from one that
        # silently swallows the real case it was carved out of.
        skew_repo = fresh('code-cites-practice-skew')
        (skew_repo / 'tools' / 'cite_fixture.py').write_text(
            '# practice: this-slug-does-not-exist\nprint("x")\n',
            encoding='utf-8')
        (skew_repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'format_version': 1, 'kind': 'consumer',
                        'files': ['cite_fixture.py']}), encoding='utf-8')
        rc_skew, out_skew = run(skew_repo, 'code-cites-practice')
        cases.append(('code-cites-practice: a stale citation inside a VENDORED '
                      'engine file (named in ENGINE_MANIFEST.json) does not '
                      'fire -- it is upstream\'s citation, unfixable here',
                      rc_skew == 0 and 'VIOLATION' not in out_skew))

        skew_off = fresh('code-cites-practice-skew-off')
        (skew_off / 'tools' / 'cite_fixture.py').write_text(
            '# practice: this-slug-does-not-exist\nprint("x")\n',
            encoding='utf-8')
        (skew_off / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'format_version': 1, 'kind': 'consumer',
                        'files': ['some_other_file.py']}), encoding='utf-8')
        rc_off, out_off = run(skew_off, 'code-cites-practice')
        cases.append(('code-cites-practice: the exemption is per-FILE -- a '
                      'manifest that does not name this file leaves the '
                      'citation checked',
                      rc_off == 1 and 'VIOLATION' in out_off))

        # code-cites-practice -- a real slug, but retired: the code should
        # have been updated or removed along with the practice, not left
        # citing a rule that no longer applies
        def _plant_retired_cite(repo):
            (repo / 'practices' / 'zzz-retired-fixture.md').write_text(
                '---\nslug:        zzz-retired-fixture\ntitle:       A retired fixture\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "testing"\n'
                'index_clause: "a planted case"\nchecked_by:  null\n'
                'defines:     []\nstatus:      retired\nsupersedes:  []\n'
                'overrides:   null\nadded:       null\n'
                'approved_by: "harness"\n---\n\n'
                '## Rule\nDo the thing.\n\n## Detail\n\n## Why\nBecause.\n\n'
                '## Story\n\n## Install\nNone.\n', encoding='utf-8')
            (repo / 'tools' / 'cite_retired_fixture.py').write_text(
                '# practice: zzz-retired-fixture\nprint("x")\n', encoding='utf-8')
        retired_repo = fresh('code-cites-practice-retired')
        _plant_retired_cite(retired_repo)
        rc_retired, out_retired = run(retired_repo, 'code-cites-practice')
        cases.append(('code-cites-practice: a citation naming a real but '
                      'retired practice fails the check',
                      rc_retired == 1 and 'VIOLATION' in out_retired
                      and "status: 'retired'" in out_retired))

        # code-cites-practice -- a 2026-09-03 deep-check audit found the
        # citation scan missed real shapes already live in this codebase:
        # more than one slug inside one parenthetical, a trailing clause
        # before the close-paren, and a parenthetical wrapped across two
        # physical lines by its own paragraph wrap (a single `re.search()`
        # per line, requiring the slug to butt right up against `)`, could
        # not see any of the three). Each is planted here citing a slug
        # that does not exist, so a regression back to "only the first,
        # immediately-closed match on one line" shows up as a missed
        # violation, not a check that quietly stopped looking.
        def _plant_citation_shape_gaps(repo):
            (repo / 'tools' / 'cite_shapes_fixture.py').write_text(
                '"""Fixture exercising three real citation shapes.\n\n'
                '(practice: this-slug-does-not-exist; practice: also-fake) '
                '-- two\nslugs, one parenthetical.\n\n'
                '(practice: this-slug-does-not-exist: "a trailing clause '
                'before\nthe close paren").\n\n'
                '(practice: this-slug-does-not-exist -- wrapped across a\n'
                'paragraph, closed on the next physical line).\n"""\n'
                'print("x")\n', encoding='utf-8')
        shapes_repo = fresh('code-cites-practice-shapes')
        _plant_citation_shape_gaps(shapes_repo)
        rc_shapes, out_shapes = run(shapes_repo, 'code-cites-practice')
        cases.append(('code-cites-practice: a multi-slug parenthetical, a '
                      'trailing clause before the close-paren, and a '
                      'parenthetical wrapped across two lines are all '
                      'still caught, not silently invisible',
                      rc_shapes == 1
                      and out_shapes.count('this-slug-does-not-exist') == 3
                      and 'also-fake' in out_shapes,
                      out_shapes))

        # scripts-assert-properties -- an instrumented script whose own
        # invariant no longer holds. The plant moves the resident cap, which
        # lives in tools/session_load_budgets.json since 2026-09-11
        # (session-load-budget) -- it used to rewrite the literal
        # `RESIDENT_BUDGET_TOKENS = 2000` in build_views.py, and the moment
        # that literal became a registry lookup the rewrite silently matched
        # nothing and the case reported the check as broken. A plant keyed on
        # a spelling is a plant that rots.
        case('scripts-assert-properties',
             lambda repo: rewrite(repo, 'tools/session_load_budgets.json',
                                  lambda t: t.replace(
                                      '"resident_block_tokens": 1750',
                                      '"resident_block_tokens": 10')))

        # Regression: an INSTRUMENTED script with neither self_check() nor
        # check_anchors() is reported by model_audit.py as a WARN, not a
        # FAIL -- warnings never affect model_audit.py's own exit code, by
        # design, since it runs standalone. Filtering the enforced check for
        # `FAIL:` lines only let exactly this violation -- the one the
        # practice's own Install section names ("keep the instrumented list
        # explicit so the audit can warn when a listed script has no
        # assertions") -- pass silently.
        def _plant_unasserted_instrumented_script(repo):
            (repo / 'tools' / 'unasserted_fixture.py').write_text(
                '"""A fixture script with no self_check() or '
                'check_anchors()."""\n', encoding='utf-8')
            rewrite(repo, 'tools/model_audit.py', lambda t: t.replace(
                'INSTRUMENTED = [\n',
                'INSTRUMENTED = [\n    "tools/unasserted_fixture.py",\n'))
        unasserted_repo = fresh('scripts-assert-properties-unasserted')
        _plant_unasserted_instrumented_script(unasserted_repo)
        rc_ua, out_ua = run(unasserted_repo, 'scripts-assert-properties')
        cases.append(('scripts-assert-properties: an INSTRUMENTED script '
                       'with no self_check() or ANCHORS fails the check, '
                       'not just silently warns',
                       rc_ua == 1 and 'VIOLATION' in out_ua))

        # --- turn-end scope: these need a remote to have a postcondition ----
        def _publish(repo):
            bare = tmp / (repo.name + '.git')
            git(repo, 'init', '--bare', '-q', str(bare), check_rc=False)
            subprocess.run(['git', 'init', '--bare', '-q', str(bare)],
                           capture_output=True, text=True)
            git(repo, 'remote', 'add', 'origin', str(bare))
            git(repo, 'push', '-q', '-u', 'origin', 'HEAD:refs/heads/main')
            git(repo, 'branch', '--set-upstream-to=origin/main', check_rc=False)

        def _plant_unpushed(repo):
            (repo / 'later.md').write_text('later\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'unpushed')
        case('verify-postcondition', _plant_unpushed, extra=('--turn-end',),
             setup=_publish)

        # Regression: the check used to compare only the CURRENTLY CHECKED
        # OUT branch against its own @{upstream}, missing the practice's own
        # origin incident -- work committed on a branch that is then left
        # un-checked-out and unpublished. Here the checked-out branch stays
        # clean and fully pushed; the violation is entirely on a second,
        # not-checked-out local branch.
        stray_repo = fresh('verify-postcondition-stray-branch')
        _publish(stray_repo)
        git(stray_repo, 'checkout', '-qb', 'stray')
        (stray_repo / 'stray.md').write_text('stray\n', encoding='utf-8')
        git(stray_repo, 'add', '-A')
        git(stray_repo, 'commit', '-qm', 'stray unpushed')
        git(stray_repo, 'checkout', '-q', '-')
        rc_stray, out_stray = run(stray_repo, 'verify-postcondition', '--turn-end')
        cases.append(('verify-postcondition: an unpushed commit on a '
                       'different, not-checked-out local branch still fails '
                       'the check',
                       rc_stray == 1 and 'VIOLATION' in out_stray))

        def _plant_rewrite(repo):
            git(repo, 'reset', '--hard', '-q', 'HEAD~1')
            (repo / 'rewritten.md').write_text('rewritten\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'rewritten history')
        def _publish_two(repo):
            (repo / 'published.md').write_text('published\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'second')
            _publish(repo)
        case('no-rewrite-for-warnings', _plant_rewrite, extra=('--turn-end',),
             setup=_publish_two)

        # parallel-artifact-ledger -- the check reads this branch's commits
        # against its base, never the whole history (Morgan, 2026-10-08;
        # practice: checks-read-only-the-work). fresh() squashes each
        # scratch copy into one "baseline" commit, which becomes the base.
        def _ledger_setup(repo):
            git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')

        def _ledger_change(repo, name):
            (repo / 'templates' / 'harness' / 'claude-code' / name
             ).write_text('new\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', f'harness change {name}')
            return git(repo, 'rev-parse', 'HEAD')

        def _plant_unledgered_harness_change(repo):
            (repo / 'templates' / 'harness' / 'claude-code' / 'fixture.txt'
             ).write_text('new\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'unledgered harness change')

        # advisory=True was dropped 2026-09-06: the CI substitution that made
        # this check look like a false positive is root-caused and fixed, so a
        # planted violation must fail the check again like every other one.
        case('parallel-artifact-ledger', _plant_unledgered_harness_change,
             setup=_ledger_setup)

        # The DUPLICATE-ROW half of this check had no planted case at all,
        # and that is exactly how a false positive shipped: it counted any
        # row CONTAINING a commit hash, so three correct rows citing an
        # earlier one in their prose read as three duplicates of one change,
        # and precedent-beta-v01 sat red against a tree nobody had edited
        # (found 2026-09-11). Both directions below; the second is the one
        # that would have caught it.
        # One cell per member the real ledger's header names: a row short of
        # them is incomplete, and the check refuses it on its own
        # (2026-10-19, when grok-build made the family four).
        def _ledger_row(repo, cell_hash, prose_hash=None):
            header = next(l for l in (repo / 'templates' / 'harness'
                                      / 'LEDGER.md').read_text(
                              encoding='utf-8').splitlines()
                          if l.startswith('| Date |'))
            others = header.count('|') - 4
            h = f'[`{cell_hash[:7]}`](https://example.invalid/{cell_hash})'
            tail = (f' — same reason as the [`{prose_hash[:7]}`]'
                    f'(https://example.invalid/{prose_hash}) row'
                    if prose_hash else '')
            return (f'| 2026-01-01 | {h} — planted | applied{tail} |'
                    + ' n/a |' * others)

        dup = fresh('parallel-artifact-ledger-dup')
        _ledger_setup(dup)
        _dh = _ledger_change(dup, 'dup.txt')
        rewrite(dup, 'templates/harness/LEDGER.md',
                lambda s: s + '\n' + _ledger_row(dup, _dh)
                             + '\n' + _ledger_row(dup, _dh) + '\n')
        _rc, _out = run(dup, 'parallel-artifact-ledger')
        cases.append(('parallel-artifact-ledger: two rows whose commit cell '
                      'names one change fail the check',
                      _rc == 1 and 'rows reference' in _out))

        xref = fresh('parallel-artifact-ledger-xref')
        _ledger_setup(xref)
        _xh = _ledger_change(xref, 'xref.txt')
        rewrite(xref, 'templates/harness/LEDGER.md',
                lambda s: s + '\n' + _ledger_row(xref, _xh)
                             + '\n' + _ledger_row(xref, _xh[::-1][:40],
                                                   prose_hash=_xh) + '\n')
        _rc2, _out2 = run(xref, 'parallel-artifact-ledger')
        cases.append(('parallel-artifact-ledger: a later row CITING that '
                      'change in its prose is not a duplicate of it',
                      _rc2 == 0 and 'rows reference' not in _out2))

        # declared-base-branch -- plant the exact regression the check
        # exists for: a resolver that infers the branch from origin/HEAD
        # with no declared value read first. Removing the CALL while
        # leaving the helper's body in place is deliberate; that is the
        # shape that passed two earlier versions of this check, so it is
        # the shape worth planting.
        def _plant_unguarded_branch_inference(repo):
            rewrite(repo, 'tools/doc_lint.py',
                   lambda s: s.replace(
                       "    declared = _declared_base_branch(ROOT)\n"
                       "    if declared:\n"
                       "        return declared\n", '', 1))
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'unguarded base-branch inference')

        case('declared-base-branch', _plant_unguarded_branch_inference)

        # document-status-header -- a stamped document whose declared
        # status is illegal for its declared kind. The fixture must stamp a
        # SECOND file legally as well: the check raises NotApplicable when
        # nothing at all is stamped (a tree that has not adopted the header
        # is not a tree doing it wrong), so a single bad file would test the
        # skip path and read as a passing plant.
        def _plant_bad_lifecycle_status(repo):
            spec_dir = repo / 'spec'
            spec_dir.mkdir(exist_ok=True)
            def stamp(name, status, heading):
                (spec_dir / name).write_text(
                    f'---\ntitle:         {heading}\nkind:          reference\n'
                    f'status:        {status}\nopened:        2026-09-07\n'
                    f'closed:        null\nsuperseded_by: null\n'
                    f'supersedes:    []\naudience:      session\n'
                    f'summary:       A planted case.\n---\n\n# {heading}\n',
                    encoding='utf-8')
            stamp('PLANTED_GOOD.md', 'current', 'Planted Good')
            stamp('PLANTED_BAD.md', 'open', 'Planted Bad')  # `open` is a brief status
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted lifecycle status')

        # The unplanted control needs the legal file too, or the clean run
        # skips instead of passing -- and a skip is not a pass.
        def _setup_lifecycle(repo):
            spec_dir = repo / 'spec'
            spec_dir.mkdir(exist_ok=True)
            (spec_dir / 'PLANTED_GOOD.md').write_text(
                '---\ntitle:         Planted Good\nkind:          reference\n'
                'status:        current\nopened:        2026-09-07\n'
                'closed:        null\nsuperseded_by: null\n'
                'supersedes:    []\naudience:      session\n'
                'summary:       A planted case.\n---\n\n# Planted Good\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'lifecycle baseline')

        case('document-status-header', _plant_bad_lifecycle_status,
             setup=_setup_lifecycle)

        # todo-gotcha-stale-reference -- a stray old-format citation added
        # to a tracked file after the 2026-09-16 migration. The dedicated,
        # multi-case fixture for this check's three shapes and its two
        # same-document exemptions is
        # check_todo_gotcha_stale_reference_fires(); this is only the one
        # planted case `enforced channel fires` itself wants, to keep the
        # "every registered check has a planted case here" claim honest.
        def _plant_stale_todo_reference(repo):
            (repo / 'WHERE_THINGS_ARE.md').write_text(
                (repo / 'WHERE_THINGS_ARE.md').read_text(encoding='utf-8')
                + '\n\nSee [x](TODO.md#a-slug-nothing-has) for detail.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted stale TODO.md reference')

        case('todo-gotcha-stale-reference', _plant_stale_todo_reference)

        # open-items-outside-todo -- an item a migration wrote under
        # docs/todo/, where nothing indexes or closes it (2026-10-01).
        def _plant_item_outside_todo(repo):
            d = repo / 'docs' / 'todo'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'todo-2026-01-01-planted.md').write_text(
                '---\nslug: planted\nstatus: open\n---\n# Planted\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted item outside todo/')

        case('open-items-outside-todo', _plant_item_outside_todo)

        # exported-files-received -- a sync that left a source's test behind
        # because no practice in force claims it (2026-10-31).
        def _plant_not_received(repo):
            (repo / 'MANIFEST.json').write_text(json.dumps({
                'practices': [], 'not_received': [
                    'tools/checks/tests/test_planted.sh (a-set)']}), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a test the sync left behind')

        case('exported-files-received', _plant_not_received)

        # manifest-entries-resolve -- an entry left naming a file a sweep
        # deleted (2026-10-01).
        def _plant_dead_manifest_entry(repo):
            m = repo / 'process' / 'manifest.json'
            m.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(m.read_text(encoding='utf-8')) if m.is_file() else {}
            data.setdefault('entries', []).append(
                {'name': 'planted', 'local_path': 'process/upstream/tools/gone.py'})
            m.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted dead manifest entry')

        case('manifest-entries-resolve', _plant_dead_manifest_entry)

        # vendored-copy-matches-record -- a vendored copy changed after its
        # record, seen with no upstream clone (2026-10-08). setup() records a
        # copy and its fingerprint, so the unplanted control passes rather
        # than reporting COULD NOT VERIFY; the plant puts older text in.
        def _setup_recorded_copy(repo):
            f = repo / 'process' / 'upstream' / 'practices' / 'planted.md'
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('Upstream text at the recorded commit.\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'a vendored copy')
            m = repo / 'process' / 'manifest.json'
            m.write_text(json.dumps({'upstream': {
                'vendored_at': 'process/upstream', 'commit': 'a' * 40,
                'copy_tree': git(repo, 'rev-parse', 'HEAD:process/upstream')},
                'entries': []}, indent=2) + '\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'its record')

        def _plant_drifted_copy(repo):
            (repo / 'process' / 'upstream' / 'practices' / 'planted.md').write_text(
                'Older upstream text, put back after the record.\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted drift in the vendored copy')

        case('vendored-copy-matches-record', _plant_drifted_copy,
             setup=_setup_recorded_copy)

        # upstream-bug-stops-here -- a file the sync's MANIFEST.json records
        # as shipped here, edited after delivery with no recorded answer.
        # The setup records it as delivered, so the clean tree matches.
        def _setup_received_file(repo):
            f = repo / 'planted_received.txt'
            f.write_text('As the set shipped it.\n', encoding='utf-8')
            (repo / 'MANIFEST.json').write_text(json.dumps({'ships': [{
                'path': 'planted_received.txt', 'source': 'precedent-shared-x',
                'sha256_16': hashlib.sha256(f.read_bytes()).hexdigest()[:16]}]}),
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'a received file and its record')

        def _plant_edited_received_file(repo):
            (repo / 'planted_received.txt').write_text(
                'Fixed here instead of upstream.\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted local edit of a shipped file')

        case('upstream-bug-stops-here', _plant_edited_received_file,
             setup=_setup_received_file)

        # todo-migrate-available-but-unused -- a repo that has the migration
        # tool vendored (an ENGINE_MANIFEST.json declaring a kind, same as a
        # real vendored repo would carry) but whose TODO.md was never
        # actually migrated: no todo/ directory, and no stub heading. This
        # repo's own tree is already migrated (it IS the tool's origin), so
        # the setup alone -- just adding the manifest -- keeps the clean
        # pipeline clean; the plant undoes the migration to create the
        # violation.
        def _setup_todo_migrate_manifest(repo):
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps({'kind': 'consumer'}), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted vendored-consumer manifest')

        def _plant_todo_migrate_unused(repo):
            shutil.rmtree(repo / 'todo')
            (repo / 'TODO.md').write_text(
                '# Repo TODO -- open items\n\n## Recurring\n'
                '- [ ] **An old-format item, never migrated.**\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted unmigrated TODO.md')

        case('todo-migrate-available-but-unused', _plant_todo_migrate_unused,
             setup=_setup_todo_migrate_manifest)

        # workflow-file-outside-vendoring -- advisory. setup() gives the
        # check something to compare against at all (this repo's own tree
        # has no tools/ENGINE_MANIFEST.json -- BestPractice vendors nothing
        # into itself), naming ONLY bestpractice-docs.yml as tracked; the
        # plant adds a second, untracked workflow file. Both run in the
        # clean pipeline too (setup applies to both -- see case()'s own
        # _clean_pipeline), so the clean control still has a manifest and
        # still reports nothing, proving the check does not fire on a
        # manifest's mere presence.
        def _setup_workflow_outside_vendoring(repo):
            # The fixture OWNS .github/workflows/ rather than inheriting it
            # (practice: fixture-owns-its-state). fresh() copies this repo's
            # real tree, which carries its own three hand-authored workflow
            # files -- every one of them untracked by the manifest written
            # below, so leaving them in place made the CLEAN control report
            # findings and proved nothing. Measured: the unplanted case
            # failed on exactly those three before this line existed.
            wf = repo / '.github' / 'workflows'
            if wf.is_dir():
                shutil.rmtree(wf)
            wf.mkdir(parents=True)
            (repo / '.github/workflows/bestpractice-docs.yml').write_text(
                'name: docs\n', encoding='utf-8')
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': 'consumer',
                'ci_workflow_files': ['.github/workflows/bestpractice-docs.yml'],
                'ci_workflows_sha256': {},
            }), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted vendored-consumer manifest + tracked workflow')

        def _plant_workflow_outside_vendoring(repo):
            (repo / '.github/workflows/hand-authored.yml').write_text(
                'name: hand-authored\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted untracked workflow file')

        case('workflow-file-outside-vendoring', _plant_workflow_outside_vendoring,
             setup=_setup_workflow_outside_vendoring, advisory=True)

        # ci-workflow-approved (2026-09-25). Setup gives the fixture a
        # vendored consumer's shape: a manifest tracking one workflow at its
        # real hash, so the unplanted tree is the engine's own untouched
        # copy and passes. The plant adds a workflow nobody approved -- the
        # incident's shape, a repo-owned check with a push trigger on main.
        def _setup_ci_workflow_approved(repo):
            import hashlib
            wf = repo / '.github' / 'workflows'
            if wf.is_dir():
                shutil.rmtree(wf)
            wf.mkdir(parents=True)
            # The workflows went, so the repo's own approvals of them go too:
            # an approval naming a removed file is a finding of its own, and
            # the clean tree must have none (2026-10-09: BestPractice
            # recorded one for deep-check.yml and this case went red).
            pj = repo / 'precedent.json'
            if pj.is_file():
                d = json.loads(pj.read_text(encoding='utf-8'))
                if d.pop('github_ci_approved', None) is not None:
                    d.pop('_github_ci_approved_comment', None)
                    pj.write_text(json.dumps(d, indent=2) + '\n',
                                  encoding='utf-8')
            body = 'name: Leak gate\n'
            (wf / 'leak-gate.yml').write_text(body, encoding='utf-8')
            (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': 'consumer',
                'ci_workflow_files': ['.github/workflows/leak-gate.yml'],
                'ci_workflows_sha256': {
                    '.github/workflows/leak-gate.yml':
                        hashlib.sha256(body.encode()).hexdigest()},
            }), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted consumer manifest, engine workflow')

        def _plant_ci_workflow_unapproved(repo):
            (repo / '.github/workflows/light-check.yml').write_text(
                'name: Light check\non:\n  push:\n    branches: [main]\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted unapproved workflow file')

        case('ci-workflow-approved', _plant_ci_workflow_unapproved,
             setup=_setup_ci_workflow_approved)

        # budget-within-approval (2026-09-30). The plant replays the
        # 2026-09-29 incident's SHAPE: the registry field is untouched and
        # the engine computes a bigger number. A check that read the field
        # (the first attempt at this) passes this plant; this one must not.
        # The plant raises a surface ceiling, a per-part budget, which this
        # check asks about only where no session-load total is declared
        # (build_views.TOTAL_KEY): the fixture drops the total first.
        def _plant_ceiling_over_approval(repo):
            _drop_session_load_total(repo / 'tools' / 'session_load_budgets.json')
            rewrite(repo, 'tools/build_views.py', lambda t: t.replace(
                "    v = row.get('ceiling')\n    return v if isinstance(v, int) else default",
                "    v = row.get('ceiling')\n    return v + 1000 if isinstance(v, int) else default", 1))

        case('budget-within-approval', _plant_ceiling_over_approval)

        # session-file-allowances-fit (2026-09-30). Switched on by a
        # hard_ceiling; the plant declares one the file's own fixed
        # allowance already exceeds, so the sum cannot fit whatever sources
        # resolve in the fixture.
        # Allowances are held only where no session-load total is declared
        # (build_views.TOTAL_KEY), so the plant drops the total first.
        def _plant_allowances_over(repo):
            _drop_session_load_total(repo / 'tools' / 'session_load_budgets.json')
            rewrite(repo, 'tools/session_load_budgets.json', lambda t: t.replace(
                '"approved_budgets": {',
                '"approved_budgets": {\n    "surfaces/.precedent/SESSION_PRACTICES.md/hard_ceiling": '
                '{"max": 10, "strength": "baseline", "approved_by": "fixture 2026-09-30"},', 1)
                .replace('".precedent/SESSION_PRACTICES.md": {',
                         '".precedent/SESSION_PRACTICES.md": {\n      "hard_ceiling": 10, "fixed_allowance": 50,', 1))

        case('session-file-allowances-fit', _plant_allowances_over)

        # shipped-template-carries-its-script (2026-09-21). The check reads
        # THIS repo's templates/github-actions/ against the REAL
        # CI_WORKFLOW_TEMPLATES/KINDS imported from tools/ -- so the fixture
        # supplies only the template, and the registries it is judged
        # against are the live ones. Setup writes a template running a
        # script that IS vendored (clean); the plant rewrites it to run one
        # that is not, reproducing the leak_gate.py incident exactly.
        def _setup_shipped_template_script(repo):
            d = repo / 'templates' / 'github-actions'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'leak-gate.yml.template').write_text(
                'name: Leak gate\n'
                'on:\n'
                '  push:\n'
                'jobs:\n'
                '  leak-gate:\n'
                '    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - uses: actions/checkout@v4\n'
                '      - name: Run it\n'
                '        run: python3 tools/leak_gate.py --structural-only\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm',
                'planted CI template running a vendored script')

        def _plant_shipped_template_script(repo):
            d = repo / 'templates' / 'github-actions'
            (d / 'leak-gate.yml.template').write_text(
                'name: Leak gate\n'
                'on:\n'
                '  push:\n'
                'jobs:\n'
                '  leak-gate:\n'
                '    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - uses: actions/checkout@v4\n'
                '      # tools/mentioned_only.py here is a COMMENT and must\n'
                '      # not be flagged -- the false-positive direction.\n'
                '      - name: Advise\n'
                "        run: echo \"run 'python3 tools/advised_only.py' yourself\"\n"
                '      - name: Run it\n'
                '        run: python3 tools/never_vendored_anywhere.py\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm',
                'planted CI template running an unvendored script')

        case('shipped-template-carries-its-script',
             _plant_shipped_template_script,
             setup=_setup_shipped_template_script)

        # vocabulary-reaches-the-consumer (2026-09-21). The check reads THIS
        # repo's practices/ against the REAL engine file lists imported from
        # tools/, so the fixture supplies only practice files and is judged
        # against the live registries. Setup plants a command practice that
        # is properly reachable; the plant makes it unreachable in BOTH ways
        # the check catches -- a scope that withholds it from a consumer's
        # tree, and a named tool that ships to nobody.
        def _setup_vocabulary_reaches(repo):
            d = repo / 'practices'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'planted-command.md').write_text(
                '---\n'
                'slug:        planted-command\n'
                'title:       Planted\n'
                'tier:        on-demand\n'
                'severity:    advisory\n'
                'scope:       null\n'
                'applies_to:  ["**"]\n'
                'occasion:    "a person says the planted word"\n'
                'gates:       []\n'
                'index_clause: "planted"\n'
                'checked_by:  null\n'
                'defines:     []\n'
                'command:     {"Planted word": "Do the planted thing."}\n'
                'status:      active\n'
                'supersedes:  []\n'
                'overrides:   null\n'
                'added:       null\n'
                'approved_by: "h"\n'
                '---\n\n'
                '## Rule\nRun `python3 tools/precedent_show.py SLUG`.\n\n'
                '## Story\nIt is vendored, so the word works downstream.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a reachable command practice')

        def _plant_vocabulary_reaches(repo):
            d = repo / 'practices'
            (d / 'planted-command.md').write_text(
                '---\n'
                'slug:        planted-command\n'
                'title:       Planted\n'
                'tier:        on-demand\n'
                'severity:    advisory\n'
                'scope:       engine-dev\n'
                'applies_to:  ["**"]\n'
                'occasion:    "a person says the planted word"\n'
                'gates:       []\n'
                'index_clause: "planted"\n'
                'checked_by:  null\n'
                'defines:     []\n'
                'command:     {"Planted word": "Do the planted thing."}\n'
                'status:      active\n'
                'supersedes:  []\n'
                'overrides:   null\n'
                'added:       null\n'
                'approved_by: "h"\n'
                '---\n\n'
                '## Rule\nRun `python3 tools/never_vendored_anywhere.py`.\n\n'
                '## Story\nBOTH failures at once: scope: engine-dev withholds\n'
                'this from a consuming tree, and the tool it names ships to\n'
                'nobody. A person can say the word and nothing can happen.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted an unreachable command practice')

        case('vocabulary-reaches-the-consumer',
             _plant_vocabulary_reaches,
             setup=_setup_vocabulary_reaches)

        # enforcement-lives-with-its-practice (2026-10-16). An individual set
        # of the fixture's own, found through a user config it brings
        # (relative, so the planted and clean trees each read their own).
        # Setup: the set's practice is checked by its own tools/checks/
        # script. Plant: by an engine file instead. Advisory until the moves
        # in spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md land.
        # The set's name is made at run time, never written here: this file
        # is one the check reads, and a planted name spelled out in it is
        # itself "an engine test naming the set" in the clean tree.
        import secrets as _zz_secrets
        _zz_set = 'zzz-planted-' + _zz_secrets.token_hex(3)

        def _set_practice(checked_by):
            return (f'---\nslug:        {_zz_set}-rule\ntitle:       Planted\n'
                    'tier:        on-demand\nseverity:    default\n'
                    'applies_to:  ["**"]\noccasion:    "testing"\n'
                    'index_clause: "planted"\n'
                    f'checked_by:  {checked_by}\n'
                    'defines:     []\nstatus:      active\nsupersedes:  []\n'
                    'overrides:   null\nadded:       null\napproved_by: "h"\n'
                    '---\n\n## Rule\nDo it.\n\n## Story\nPlanted.\n')

        def _setup_enforcement_lives(repo):
            ind = repo / '_planted_individual'
            (ind / 'practices').mkdir(parents=True, exist_ok=True)
            (ind / 'tools' / 'checks').mkdir(parents=True, exist_ok=True)
            (ind / 'tools' / 'checks' / 'check_zzz.py').write_text('', encoding='utf-8')
            # A set's check is tested in the set (2026-10-17).
            (ind / 'tools' / 'checks' / 'tests').mkdir(exist_ok=True)
            (ind / 'tools' / 'checks' / 'tests' / 'test_zzz.sh').write_text(
                '#!/bin/bash\nexit 0\n', encoding='utf-8')
            (ind / 'practices' / f'{_zz_set}-rule.md').write_text(
                _set_practice('tools/checks/check_zzz.py'), encoding='utf-8')
            (repo / '.planted-user-config.json').write_text(_pj_e.dumps({
                'format_version': 1, 'individual': {
                    'name': _zz_set, 'path': '_planted_individual'}}),
                encoding='utf-8')

        def _plant_enforcement_lives(repo):
            (repo / '_planted_individual' / 'practices' / f'{_zz_set}-rule.md'
             ).write_text(_set_practice('tools/leak_gate.py'), encoding='utf-8')

        import json as _pj_e
        case('enforcement-lives-with-its-practice',
             _plant_enforcement_lives, setup=_setup_enforcement_lives,
             advisory=True,
             env_extra={'PRECEDENT_USER_CONFIG': '.planted-user-config.json'})

        # wired-hooks-can-reach-a-consumer (2026-09-21). The check reads a
        # repo's own .claude/settings.json against the REAL HOOK_SOURCE_DIR
        # imported from precedent_vendor_engine, so the fixture supplies
        # both sides and is judged against the live constant. Setup wires a
        # hook that IS in the mirrored directory; the plant wires one that
        # is not, reproducing the doc-lint-gate.sh incident exactly -- a
        # hook this repo ran and no consumer could ever receive.
        import json as _pj

        def _settings_wiring(script):
            return _pj.dumps({'hooks': {'PreToolUse': [{
                'matcher': 'Bash',
                'hooks': [{'type': 'command',
                           'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/' + script}],
            }]}}, indent=2) + '\n'

        def _setup_wired_hooks_reach(repo):
            d = repo / 'templates' / 'harness' / 'claude-code' / 'hooks'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'planted-hook.sh').write_text('#!/bin/bash\nexit 0\n',
                                               encoding='utf-8')
            s = repo / '.claude'
            s.mkdir(parents=True, exist_ok=True)
            (s / 'settings.json').write_text(
                _settings_wiring('planted-hook.sh'), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a hook that can reach a consumer')

        def _plant_wired_hooks_reach(repo):
            s = repo / '.claude'
            (s / 'settings.json').write_text(
                _settings_wiring('never-shipped-anywhere.sh'), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a hook no consumer can receive')

        case('wired-hooks-can-reach-a-consumer',
             _plant_wired_hooks_reach,
             setup=_setup_wired_hooks_reach)

        # shipped-hook-carries-its-script (2026-09-21). The check reads a
        # repo's HOOK_SOURCE_DIR against the REAL engine file lists, so the
        # fixture supplies only the hook and is judged against the live
        # registries. Setup ships a hook running a script that IS vendored
        # to both kinds; the plant rewrites it to run one that is vendored
        # to neither, reproducing the doc_lint.py incident exactly -- a hook
        # that lands without the tool it runs and then fails open forever.
        def _setup_hook_carries_script(repo):
            d = repo / 'templates' / 'harness' / 'claude-code' / 'hooks'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'planted-gate.sh').write_text(
                '#!/bin/bash\n'
                '# tools/mentioned_only.py in a COMMENT must not be flagged.\n'
                'script="$project_dir/tools/doc_lint.py"\n'
                'exec python3 "$script" "$@"\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a hook whose script is vendored')

        def _plant_hook_carries_script(repo):
            d = repo / 'templates' / 'harness' / 'claude-code' / 'hooks'
            (d / 'planted-gate.sh').write_text(
                '#!/bin/bash\n'
                '# tools/mentioned_only.py in a COMMENT must not be flagged.\n'
                'script="$project_dir/tools/never_vendored_anywhere.py"\n'
                'exec python3 "$script" "$@"\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a hook whose script ships nowhere')

        case('shipped-hook-carries-its-script',
             _plant_hook_carries_script,
             setup=_setup_hook_carries_script)

        # claude-only-surface-has-a-parallel (2026-09-21). The check reads
        # the fixture's OWN .claude/ and templates/harness/PARALLELS.md, so
        # the fixture supplies both. Setup gives one Claude-only hook and a
        # table row covering it for all three adapters; the plant deletes
        # the row, reproducing the shape the check exists for -- a
        # mechanism that lives in .claude/ and nowhere else, with nothing
        # recording what the other three harnesses get instead.
        _PAR_HEAD = ('| Mechanism | What it does | codex | gemini-cli | '
                     'grok-build |\n|---|---|---|---|---|\n')

        def _par_rows_for(repo):
            """A covering row for every mechanism the FIXTURE's own .claude/
            holds. The fixture is a copy of this tree, so it inherits the
            real hooks; a table naming only the planted one leaves those
            uncovered and the clean case fails for a reason that has
            nothing to do with what is being tested."""
            import json as _vj
            names = {q.name for q in (repo / '.claude' / 'hooks').glob('*.sh')}
            # ...and the hooks this repo ships, which the check also reads
            # as mechanisms since 2026-10-17.
            names |= {q.name for q in (repo / 'templates' / 'harness' /
                                       'claude-code' / 'hooks').glob('*.sh')}
            for sp in sorted((repo / '.claude').glob('settings*.json')):
                try:
                    doc = _vj.loads(sp.read_text(encoding='utf-8'))
                except Exception:                             # noqa: BLE001
                    continue
                for _e, blocks in (doc.get('hooks') or {}).items():
                    for b in blocks or ():
                        for h in b.get('hooks') or ():
                            c = (h.get('command') or '').strip()
                            if c and c.split()[0].endswith('.sh'):
                                names.add(c.split()[0].rsplit('/', 1)[-1])
            return ''.join(
                f'| `{n}` | fixture row | none, no hook mechanism | '
                f'none, same | none, same |\n' for n in sorted(names))

        def _setup_surface_parallel(repo):
            h = repo / '.claude' / 'hooks'
            h.mkdir(parents=True, exist_ok=True)
            (h / 'planted-hook.sh').write_text('#!/bin/bash\nexit 0\n',
                                               encoding='utf-8')
            d = repo / 'templates' / 'harness'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'PARALLELS.md').write_text(
                '# Planted\n\n' + _PAR_HEAD + _par_rows_for(repo),
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted a covered Claude-only hook')

        def _plant_surface_parallel(repo):
            # Drop exactly one row -- the planted hook's -- and leave every
            # other row standing. A table emptied wholesale would fail for
            # a dozen reasons at once; this fails for the one under test.
            keep = [l for l in (repo / 'templates' / 'harness' /
                                'PARALLELS.md').read_text(encoding='utf-8')
                    .splitlines(True)
                    if not l.startswith('| `planted-hook.sh`')]
            (repo / 'templates' / 'harness' / 'PARALLELS.md').write_text(
                ''.join(keep), encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'planted an uncovered Claude-only hook')

        case('claude-only-surface-has-a-parallel',
             _plant_surface_parallel,
             setup=_setup_surface_parallel)

        # check_commit_author.py / check_buenos_aires_dates.py -- the two
        # source-supplied identity checks BestPractice permanently carries
        # since 2026-09-22 (commit 9d16b6ae, "Port commit-identity push
        # gate to BestPractice"). Neither has a practices/*.md file here
        # (their practice text is precedent-individual's, private), so
        # register_materialized_checks() falls back to their filenames as
        # slugs -- which is exactly why they read as UNTESTED rather than
        # by a clean hyphenated slug: nobody wrote a case for the fallback
        # name. Found 2026-09-22 running --as-ci for an unrelated change.
        #
        # Both checks stand down (exit 2, SKIPPED) unless a declared
        # identity resolves, so env_extra supplies one via the first rung
        # precedent_identity.declared_identity() reads -- PRECEDENT_COMMIT_*
        # -- rather than writing a repo-root identity.json, which would
        # itself change what env_findings() inside check_commit_author.py
        # asserts (identity.json present means "this repo IS an individual
        # source", a different case entirely).
        #
        # The chosen identity is name=harness/email=harness@example.com --
        # the SAME author `pristine`'s own "baseline" commit already uses
        # (set at the top of this function), so the unplanted clean
        # fixture needs no re-authoring for check_commit_author to pass.
        _ID_NAME, _ID_EMAIL, _ID_TZ = (
            'harness', 'harness@example.com', 'America/Argentina/Buenos_Aires')
        _ID_ENV = {'PRECEDENT_COMMIT_NAME': _ID_NAME,
                  'PRECEDENT_COMMIT_EMAIL': _ID_EMAIL,
                  'PRECEDENT_COMMIT_TZ': _ID_TZ}

        def _plant_commit_author(repo):
            (repo / 'zzz-wrong-author.txt').write_text('x\n', encoding='utf-8')
            git(repo, 'add', '-A')
            # Non-anthropic.com, non-empty, and this process's own ambient
            # TZ decides the offset -- none of which the GLOBAL commit
            # backstop (installed session-wide at
            # ~/.config/precedent/git-hooks/pre-commit, practice:
            # commit-author's own mechanism) objects to, so no override is
            # needed to make the commit itself land.
            git(repo, '-c', 'user.name=Someone Else',
                '-c', 'user.email=someone@example.com',
                'commit', '-qm', 'wrong author')

        # buenos-aires-dates needs the CLEAN fixture's pre-existing
        # "baseline" commit itself to carry the -0300 offset, or a harness
        # run under a different ambient TZ (a CI runner defaults to UTC)
        # would show that commit as a violation with no plant at all --
        # practice: fixture-owns-its-state. Re-dated under an explicit TZ
        # rather than assumed from whatever machine happens to run this.
        #
        # And since 2026-09-25 the fixture must BE an individual source: the
        # check audits history only in a repo carrying its own identity.json,
        # and stands down everywhere else -- a shared repo's history holds
        # other people's commits.
        def _setup_buenos_aires_dates(repo):
            (repo / 'identity.json').write_text(json.dumps(
                {'name': _ID_NAME, 'email': _ID_EMAIL, 'timezone': _ID_TZ}),
                encoding='utf-8')
            git(repo, 'add', 'identity.json')
            git(repo, '-c', f'user.name={_ID_NAME}', '-c',
                f'user.email={_ID_EMAIL}', 'commit', '--amend',
                '--reset-author', '--no-edit',
                env={**os.environ, 'TZ': _ID_TZ,
                     'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})

        def _plant_buenos_aires_dates(repo):
            (repo / 'zzz-wrong-offset.txt').write_text('x\n', encoding='utf-8')
            git(repo, 'add', '-A')
            # Deliberately the one commit in this whole function that NEEDS
            # the global backstop's override: the point of this commit is
            # to have the WRONG offset, which is precisely what that hook
            # refuses by default.
            git(repo, '-c', f'user.name={_ID_NAME}', '-c',
                f'user.email={_ID_EMAIL}', 'commit', '-qm', 'wrong offset',
                env={**os.environ, 'TZ': 'UTC',
                     'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})

        case('check_commit_author', _plant_commit_author, env_extra=_ID_ENV)
        case('check_commit_dates', _plant_buenos_aires_dates,
             setup=_setup_buenos_aires_dates, env_extra=_ID_ENV)

        planted.settle_all()
        rc, _out = _baseline_result()
        # On a failure, the failing checks' own findings go into the detail:
        # a bare rc said only the slug of this case, and under --as-ci
        # --isolated (UTC) finding that todo/TODO.md had drifted took a
        # manual rebuild of the fixture (2026-09-30).
        cases.insert(0, ('an unplanted copy of this tree passes every check',
                         rc == 0, '' if rc == 0 else _failing_findings(_out)))

        # --- and the registry must not contain an untested claim ------------
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            '_pc', ROOT / 'tools' / 'precedent_check.py')
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        # The registry is only complete after the source-supplied check
        # scripts register themselves -- precedent_check.main() does this
        # before it reads CHECKS, and so must anything auditing CHECKS.
        # Without it a practice whose checked_by names a tools/checks/
        # script would look unregistered here (and its check would look
        # untested), which is the opposite of the truth.
        pc.register_materialized_checks()
        # `declared`, not `planted`: with the rotation on, `planted` holds
        # only the cases this invocation ran, and every skipped one would
        # read as an untested claim. What this assertion is actually about
        # is whether the FILE has a case for every registered check, which
        # is a property of the source, not of one run's rotation slice.
        untested = sorted(set(pc.CHECKS) - declared)
        cases.append(('every registered check has a planted case here',
                      not untested, f'untested: {untested}' if untested else ''))
        claimed = sorted(
            fm['slug'] for fm, _s, _f in load_practice_files().values()
            if (fm.get('checked_by') or 'null').strip('"') != 'null')
        unregistered = sorted(set(claimed) - set(pc.CHECKS))
        cases.append(('every practice claiming a checked_by is registered',
                      not unregistered,
                      f'claimed but not registered: {unregistered}'
                      if unregistered else ''))

        bad = [(n, d) for n, ok, *rest in
               [(c[0], c[1], (c[2] if len(c) > 2 else '')) for c in cases]
               if not ok for d in [rest[0] if rest else '']]
        detail = ''
        if bad:
            detail = '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad)
            for slug, (rc, out) in planted.items():
                if any(slug in n for n, _ in bad):
                    detail += f"\n    --- {slug} planted run (rc={rc}):\n" + \
                        '\n'.join('    ' + l for l in out.splitlines()[:12])
        # THE SELECTION IS PART OF THE RESULT LINE, never a silent
        # narrowing. A rotated run and a full run must not read the same:
        # "a skip is not a pass" is this repo's own rule about its check
        # suite, and a scheduler that hid what it declined to run would
        # break it in the one place it is hardest to notice.
        _sel = (f"{len(ran)} of {len(declared)} planted cases ran -- "
                f"{_selection_reason}"
                + (f"; {len(skipped)} NOT exercised this run, covered within "
                   f"{HARNESS_ROTATION_BUCKETS} commits (--all forces every "
                   f"one)" if skipped else ""))
        check(f"enforced channel fires ({len(cases)} stated cases; {_sel})",
              not bad, detail)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
