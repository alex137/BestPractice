# The harness tests for precedent_check.py
#
# tools/harness/vh_practice_checks.py -- part of the verification harness:
# precedent_check.py, the practice audit and the practice-file rules it enforces.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def _withdrawn_original_numbers():
    """-> {source_practice_number: slug} for each original practice whose
    file was deleted on purpose: registered in
    process/decommissioned_paths.json (precedent_move.py
    --withdraw-from-universal writes it), its number read from the file as
    it was in the commit before the deletion. 2026-10-02: practice 45,
    merge-authorization-keyword, withdrawn into the set that provides the
    five-stage ladder. A deletion nobody registered still fails."""
    out = {}
    try:
        reg = json.loads((ROOT / 'process' / 'decommissioned_paths.json')
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return out
    rows = reg.get('decommissioned', []) if isinstance(reg, dict) else reg
    for row in rows if isinstance(rows, list) else []:
        path = row.get('path', '') if isinstance(row, dict) else ''
        if not re.fullmatch(r'practices/[a-z0-9-]+\.md', path) or (ROOT / path).exists():
            continue
        last = subprocess.run(['git', '-C', str(ROOT), 'log', '-1', '--format=%H',
                               '--diff-filter=D', '--', path],
                              capture_output=True, text=True).stdout.strip()
        if not last:
            continue
        before = subprocess.run(['git', '-C', str(ROOT), 'show', f'{last}~1:{path}'],
                                capture_output=True, text=True).stdout
        m = re.search(r'^source_practice_number:\s*"?(\d+)', before, re.M)
        if m:
            out[m.group(1)] = path[len('practices/'):-3]
    return out


def check_source_coverage(files, original_practices_by_number):
    """The plan's actual slug-set requirement: "the same practices are in
    effect, by slug." precedent_check.py's practice-file-shape only proves each FILE is internally
    consistent -- filename == frontmatter slug, no duplicates. It says
    nothing about whether every practice in PRACTICES.md still has one.

    Deleting a whole practice file was caught only by accident: by citation
    integrity, because some other practice happened to cite it by number,
    and by the generated-views check, because MAP.md changed. Drop a
    practice nothing cites, in a commit that regenerates the views, and
    every check stayed green. This asks the question directly."""
    ok = True
    by_number = {}
    for stem, (fm, sections, f) in sorted(files.items()):
        num = fm.get('source_practice_number')
        if num is None:
            # legitimate for a practice minted fresh (phase 3 on), but then
            # it is not part of the migrated set this check is about.
            # split_practices.py drops a `null` field rather than storing
            # the string, so this guard is live -- it was dead until
            # 2026-09-06 and `int('null')` below crashed instead.
            continue
        by_number.setdefault(num, []).append(stem)

    withdrawn = None
    for num in sorted(original_practices_by_number, key=int):
        if num not in by_number:
            if withdrawn is None:
                withdrawn = _withdrawn_original_numbers()
            if num in withdrawn:
                continue  # deleted on purpose, and registered as such
            ok = False
            print(f"  practice {num} ({original_practices_by_number[num]['title']!r}) is in "
                  f"PRACTICES.md but has NO file in practices/ -- a practice was dropped")
    for num, stems in sorted(by_number.items(), key=lambda kv: int(kv[0])):
        if num not in original_practices_by_number:
            if num in POST_SNAPSHOT_PRACTICE_NUMBERS:
                continue  # added to `main` after PRACTICES.md's snapshot -- see CHANGES_TO_TELL_ALEX.md
            ok = False
            print(f"  practices/{stems[0]}.md claims source_practice_number {num}, which "
                  f"is not in PRACTICES.md")
        elif len(stems) > 1:
            ok = False
            print(f"  practice {num} is claimed by {len(stems)} files: {stems}")
    check(f'source coverage (every one of the {len(original_practices_by_number)} practices in '
          f'PRACTICES.md has exactly one file, and vice versa)', ok)


def check_rename_links_spares_a_path_moved_into_gitignore():
    """A branch that stops committing build output (`git rm --cached` plus a
    .gitignore line) has not deleted anything a reader needs: the file is
    built on demand. rename-updates-links flagged every index and ledger
    naming it (2026-10-04, a consumer that stopped committing its document
    renders). CONTROL: a file the same branch really deleted is still
    flagged."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='ignored-output-'))
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        shutil.copy(ROOT / 'practices' / 'rename-updates-links.md', up / 'practices')
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}]}),
            encoding='utf-8')
        (repo / 'docs').mkdir()
        (repo / 'docs' / 'page.html').write_text('<p>built</p>\n', encoding='utf-8')
        (repo / 'docs' / 'gone.md').write_text('old\n', encoding='utf-8')
        (repo / 'README.md').write_text('Read docs/page.html.\nAnd docs/gone.md.\n',
                                        encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        g('checkout', '-q', '-b', 'stop-committing-renders')
        g('rm', '-q', '--cached', 'docs/page.html')
        (repo / '.gitignore').write_text('docs/*.html\n', encoding='utf-8')
        g('rm', '-q', 'docs/gone.md')
        g('add', '.gitignore'); g('commit', '-qm', 'renders built on demand; gone.md removed')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'rename-updates-links'], cwd=str(repo), capture_output=True,
                           text=True, env=env, timeout=300)
        out = r.stdout + r.stderr
        cases.append(('a path moved into .gitignore is not a deletion',
                      'docs/page.html' not in out, failure_detail(out, 400)))
        cases.append(('CONTROL: a really deleted file is still flagged',
                      'docs/gone.md' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'rename-updates-links spares build output moved into .gitignore '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_clean_tree_judges_the_branch():
    """A bare precedent_check on a clean tree judges what the branch carries
    since its base, and the basic push tier runs rename-updates-links
    (2026-10-08). A consumer branch renamed a page and left a stale key in a
    tool and lines in two ledgers: every push ran the basic tier, which did
    not include the rename check, and a bare run after the commit said "the
    working tree is clean, so no change is in scope" and passed every
    change-scope check unread. Only the landing's full check said so.

    A throwaway consumer: main, then a branch committing a document that
    skips a heading level and a rename that strands a reference. CONTROL:
    the same bare run on main itself still finds nothing in scope."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='clean-tree-branch-'))
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        for slug in ('rename-updates-links', 'heading-outline'):
            shutil.copy(ROOT / 'practices' / f'{slug}.md', up / 'practices')
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}]}),
            encoding='utf-8')
        (repo / 'docs').mkdir()
        (repo / 'docs' / 'old_name.md').write_text('# Page\n', encoding='utf-8')
        (repo / 'README.md').write_text('# Readme\n\nSee docs/old_name.md.\n',
                                        encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)

        def pc(*a):
            r = subprocess.run([sys.executable, 'tools/precedent_check.py', *a],
                               cwd=str(repo), capture_output=True, text=True,
                               env=env, timeout=300)
            return r.returncode, r.stdout + r.stderr
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        rc, out = pc('--only', 'heading-outline')
        cases.append(('CONTROL: on main itself a clean tree has nothing in scope',
                      rc == 0 and 'VIOLATION' not in out, failure_detail(out, 400)))
        g('checkout', '-q', '-b', 'work')
        (repo / 'docs' / 'skips.md').write_text('# Top\n\n### Too deep\n',
                                                encoding='utf-8')
        g('mv', 'docs/old_name.md', 'docs/new_name.md')
        g('add', '-A'); g('commit', '-qm', 'a page that skips a level; a rename')
        clean = g('status', '--porcelain').stdout.strip() == ''
        rc, out = pc('--only', 'heading-outline')
        cases.append(('a clean tree on a branch judges the branch: the committed '
                      'heading jump is found',
                      clean and rc != 0 and 'docs/skips.md' in out
                      and 'commit(s) this branch carries since origin/main' in out,
                      failure_detail(out, 400)))
        rc, out = pc('--only', 'rename-updates-links')
        cases.append(('the reference the rename stranded is found after the commit',
                      rc != 0 and 'docs/old_name.md' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_push_check as _ppc
    finally:
        sys.path.pop(0)
    for kind in ('consumer', 'source'):
        step = [s for s in _ppc.PUSH_CHECKS[kind] if s[0] == 'rename_links']
        cases.append((f'a {kind} push runs rename-updates-links at the basic tier',
                      'rename_links' in _ppc.BASIC_CHECKS and bool(step)
                      and 'rename-updates-links' in step[0][1], ''))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a clean tree judges its branch, and the basic tier runs the rename '
          f'check ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_rename_links_spares_a_url_into_another_repository():
    """A deleted path inside a link to ANOTHER repository names that
    repository's file, not this one's. After go-update moved from the
    universal set to the ladder set, a consumer's Update Vendors deleted
    practices/go-update.md, said to repoint its links, and then flagged the
    repointed https://github.com/<owner>/precedent-shared-ladder/blob/main/
    practices/go-update.md for still containing the old path
    (a consumer, 2026-10-05). CONTROLS: a link into this same
    repository, and a bare path, are still flagged."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='other-repo-url-'))
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        shutil.copy(ROOT / 'practices' / 'rename-updates-links.md', up / 'practices')
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}]}),
            encoding='utf-8')
        (repo / 'guide').mkdir()
        (repo / 'guide' / 'go-update.md').write_text('old\n', encoding='utf-8')
        (repo / 'elsewhere.md').write_text(
            'See [go-update](https://github.com/acme/other-set/'
            'blob/main/guide/go-update.md).\n', encoding='utf-8')
        (repo / 'here.md').write_text(
            'See [go-update](https://github.com/acme/consumer/blob/main/'
            'guide/go-update.md).\n', encoding='utf-8')
        (repo / 'bare.md').write_text('See guide/go-update.md.\n', encoding='utf-8')
        # 2026-10-19: docs saying "OtherSet's tools/human_voice_check.py"
        # were flagged on the change that deleted a stale copy of it.
        (repo / 'possessive.md').write_text(
            "Run OtherSet's `guide/go-update.md` instead.\n", encoding='utf-8')
        (repo / 'slug.md').write_text(
            'Source (in acme/other-set): guide/go-update.md\n', encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('remote', 'add', 'origin', 'https://github.com/acme/consumer.git')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        g('checkout', '-q', '-b', 'go-update-moved')
        g('rm', '-q', 'guide/go-update.md'); g('commit', '-qm', 'go-update moved away')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'rename-updates-links'], cwd=str(repo), capture_output=True,
                           text=True, env=env, timeout=300)
        out = r.stdout + r.stderr
        cases.append(('a link into another repository is not a stale reference',
                      'elsewhere.md' not in out, failure_detail(out, 400)))
        cases.append(('a mention the line qualifies by another repository '
                      '(a possessive, or owner/name) is not a stale reference',
                      'possessive.md' not in out and 'slug.md' not in out, failure_detail(out, 400)))
        cases.append(('CONTROL: a link into this same repository is still flagged',
                      'here.md:1' in out, failure_detail(out, 400)))
        cases.append(('CONTROL: a bare path is still flagged',
                      'bare.md:1' in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'rename-updates-links spares a URL into another repository '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_workflow_growth_needs_the_persons_words():
    """ci-workflow-approved, everywhere: a change that makes a workflow or a
    workflow template run more -- a new event, branch, type, schedule or
    job, or a narrowing filter dropped -- is refused until the person's
    words are pinned to its content; a fix that adds no CI work passes
    (Morgan, 2026-09-30: permission is for adding workflows or CI minutes,
    and "we clearly shouldn't have broken workflows"). Until then nothing
    pinned BestPractice's own templates at all."""
    import tempfile, hashlib
    import precedent_check as pc
    cases = []
    base = ('on:\n  pull_request:\n    branches: [main]\n    types: [opened]\n'
            '  push:\n    branches: [main]\n'
            'jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n'
            '      - run: python3 tools/x.py\n')
    for name, after, grows in (
            ('a fixed path in a step', base.replace('tools/x.py', 'tools/y.py'), False),
            ('a comment', '# why\n' + base, False),
            ('a branch added', base.replace('branches: [main]\n    types',
                                            'branches: [main, dev]\n    types'), True),
            ('a type added', base.replace('[opened]', '[opened, synchronize]'), True),
            ('a push filter dropped', base.replace('  push:\n    branches: [main]\n',
                                                   '  push:\n'), True),
            ('a schedule added', base.replace('  push:\n', '  schedule:\n    - cron: "0 3 * * *"\n  push:\n'), True),
            ('a job added', base + '  more:\n    runs-on: ubuntu-latest\n', True),
            ('a job renamed', base.replace('  check:\n', '  verify:\n'), False),
            ('a job renamed and another added',
             (base + '  more:\n    runs-on: ubuntu-latest\n').replace('  check:\n', '  a:\n'),
             True),
            ('a matrix added', base.replace('    runs-on: ubuntu-latest\n',
                                            '    strategy:\n      matrix:\n        part: [1, 2]\n'
                                            '    runs-on: ubuntu-latest\n'), True),
            ('an event removed', base.replace('  push:\n    branches: [main]\n', ''), False)):
        got = pc._workflow_growth(base, after)
        cases.append((f'{name}: {"grows" if grows else "adds no CI work"}',
                      bool(got) == grows, str(got)))
    cases.append(('a new workflow is all growth', bool(pc._workflow_growth(None, base)), ''))
    # A LIST WHERE THERE WAS NONE NARROWS (2026-10-10): BestPractice's own
    # leak-gate.yml went from every branch but one to main only, and was
    # refused as running more.
    every = ('on:\n  push:\n    branches-ignore: [old-name]\n'
             'jobs:\n  scan:\n    runs-on: ubuntu-latest\n')
    for name, before, after, grows in (
            ('every branch but one -> main only', every,
             every.replace('branches-ignore: [old-name]', 'branches: [main]'), False),
            ('every branch -> main only', every.replace('    branches-ignore: [old-name]\n', ''),
             every.replace('branches-ignore: [old-name]', 'branches: [main]'), False),
            ('an ignored branch now listed', every,
             every.replace('branches-ignore: [old-name]', 'branches: [old-name]'), True),
            ('an ignore filter dropped with nothing in its place', every,
             every.replace('    branches-ignore: [old-name]\n', ''), True)):
        got = pc._workflow_growth(before, after)
        cases.append((f'{name}: {"grows" if grows else "adds no CI work"}',
                      bool(got) == grows, str(got)))
    two = base + '  more:\n    runs-on: ubuntu-latest\n'
    cases.append(('two jobs folded into one new one adds no CI work',
                  not pc._workflow_growth(two, base.replace('  check:\n', '  one:\n')),
                  str(pc._workflow_growth(two, base.replace('  check:\n', '  one:\n')))))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='workflow-growth-'))
    try:
        repo = tmp / 'proj'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        shutil.copy(ROOT / 'practices' / 'ci-workflow-approved.md', up / 'practices')
        cfg = {'sources': [{'level': 'universal', 'name': 'precedent',
                            'path': 'process/upstream'}]}
        (repo / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        tpl = repo / 'templates' / 'github-actions' / 'w.yml.template'
        tpl.parent.mkdir(parents=True)
        tpl.write_text(base, encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)

        def run():
            r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                                'ci-workflow-approved'], cwd=str(repo),
                               capture_output=True, text=True, env=env, timeout=300)
            return r.returncode, r.stdout + r.stderr
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        g('checkout', '-q', '-b', 'work')
        tpl.write_text(base.replace('tools/x.py', 'tools/y.py'), encoding='utf-8')
        g('commit', '-qam', 'fix a path')
        rc, out = run()
        cases.append(('a template fix that adds no CI work passes', rc == 0, failure_detail(out, 300)))
        tpl.write_text(base + '  more:\n    runs-on: ubuntu-latest\n', encoding='utf-8')
        g('commit', '-qam', 'add a job')
        rc, out = run()
        cases.append(('a template given a new job is refused, naming it',
                      rc == 1 and 'job:more' in out, failure_detail(out, 400)))
        cfg['github_ci_approved'] = {'templates/github-actions/w.yml.template': {
            'sha256': hashlib.sha256(tpl.read_bytes()).hexdigest(),
            'approved_by': 'Dana, 2026-09-30: "yes, add the second job"'}}
        (repo / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        g('commit', '-qam', 'approved')
        rc, out = run()
        cases.append(('...and passes once the person\'s words are pinned to it',
                      rc == 0, failure_detail(out, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a workflow change that adds CI work needs the person\'s words, and a '
          f'fix does not ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_docs_name_no_path_this_repo_removed():
    """change-updates-its-docs: a live document naming a path this repo's
    history deleted is refused, in plain text and as a link to this repo's
    own branch; history is left alone (2026-09-30: a session found a section
    describing a retired workflow and left it, as "a doc fix, not a broken
    path"). A path this repo never had -- a consumer's layout, another
    repo's file -- is never flagged."""
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='removed-paths-'))
    gone = 'docs/old/guide.md'
    try:
        repo = tmp / 'proj'
        (repo / 'tools').mkdir(parents=True)
        for f in list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'tools').glob('*.json')):
            shutil.copy(f, repo / 'tools' / f.name)
        up = repo / 'process' / 'upstream'
        (up / 'practices').mkdir(parents=True)
        shutil.copy(ROOT / 'practices' / 'change-updates-its-docs.md', up / 'practices')
        (repo / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': 'process/upstream'}]}), encoding='utf-8')
        (repo / gone).parent.mkdir(parents=True)
        (repo / gone).write_text('old\n', encoding='utf-8')
        files = {
            'README.md': f'Read `{gone}` first.\n',
            'docs/link.md': f'[guide](https://github.com/acme/widget/blob/main/{gone})\n',
            'docs/other-repo.md': f'[theirs](https://github.com/else/where/blob/main/{gone})\n',
            'docs/retired.md': f'`{gone}` (retired 2026-09-01) is gone.\n',
            'docs/story.md': f'# X\n## Story\nWe read `{gone}`.\n',
            'docs/plan.md': f'---\nkind: plan\nstatus: closed\n---\nEdit `{gone}`.\n',
            'docs/consumer.md': 'A consumer keeps `local/practices/x.md`.\n',
            # The sentence says it, wrapped onto the next line (2026-10-01).
            'docs/wrapped.md': f'The checker that lived in `{gone}`\nwas retired on 2026-09-01.\n',
            # ...but a NEXT sentence that says "was" excuses nothing.
            'docs/adjacent.md': f'Read `{gone}` first.\nThis was a fine design.\n',
        }
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a], capture_output=True,
                                  text=True, env=env)

        def run():
            r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                                'change-updates-its-docs'], cwd=str(repo),
                               capture_output=True, text=True, env=env, timeout=300)
            return r.returncode, r.stdout + r.stderr
        g('init', '-q', '-b', 'main'); g('add', '-A'); g('commit', '-qm', 'base')
        g('remote', 'add', 'origin', 'https://github.com/acme/widget')
        # The base the branch is judged against: the check reads this
        # change, never the whole history (practice: checks-read-only-the-work).
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        rc, out = run()
        cases.append(('nothing deleted yet: nothing to judge', rc == 0
                      and 'README.md:1' not in out, failure_detail(out, 300)))
        g('rm', '-q', gone); g('commit', '-qm', 'delete the guide')
        rc, out = run()
        cases.append(('a live document naming the deleted path is refused',
                      rc == 1 and 'README.md:1' in out, failure_detail(out, 400)))
        cases.append(('...and so is a link to it on this repo\'s own branch',
                      'docs/link.md:1' in out, failure_detail(out, 400)))
        for rel, why in (('docs/other-repo.md', 'the same path in another repo'),
                         ('docs/retired.md', 'a line that says it was retired'),
                         ('docs/story.md', 'a Story section'),
                         ('docs/plan.md', 'a closed document'),
                         ('docs/consumer.md', 'a path this repo never had'),
                         ('docs/wrapped.md', 'a sentence wrapped so "retired" is '
                                             'on the next line')):
            cases.append((f'{why} is left alone', rel not in out, failure_detail(out, 400)))
        cases.append(('a "was" in the next sentence excuses nothing',
                      'docs/adjacent.md:1' in out, failure_detail(out, 400)))
        # Once the deletion is on the base, the next branch is not judged
        # for it: the check reads this change, never the whole history
        # (Morgan, 2026-10-08; practice: checks-read-only-the-work).
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('checkout', '-qb', 'next')
        (repo / 'docs' / 'unrelated.md').write_text('Unrelated.\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'an unrelated change')
        rc, out = run()
        cases.append(('a deletion already on the base is not judged on a later branch',
                      rc == 0 and 'README.md:1' not in out, failure_detail(out, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a live document naming a path this change removed is refused, and '
          f'history is not ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_practice_audit_loader():
    """practice_audit.py's check 5, stated as cases (practice:
    checkable-gets-checked). A consumer installed the classic way on
    2026-09-22 -- process/upstream/ vendored, no loader over it -- took an
    update the next day with this audit passing, and its sessions then
    described every practice as "a vendored copy, not something this repo
    adopted". The audit now fails on a vendored catalogue nothing loads,
    and passes once the repo declares a universal source AND carries the
    generated loader block; --loader-notice says the same thing at session
    start and never fails."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-auditloader-'))
    try:
        def make(name, catalogue=True, universal=False, block=False,
                 engine=True):
            repo = tmp / name
            tools_dir = repo / 'process' / 'upstream' / 'tools'
            tools_dir.mkdir(parents=True)
            shutil.copy(ROOT / 'tools' / 'practice_audit.py', tools_dir / 'practice_audit.py')
            shutil.copy(ROOT / 'tools' / 'generated_blocks.py', tools_dir / 'generated_blocks.py')
            if catalogue:
                (repo / 'process' / 'upstream' / 'practices').mkdir()
                (repo / 'process' / 'upstream' / 'practices' / 'x.md').write_text(
                    'a practice\n', encoding='utf-8')
            (repo / 'process' / 'manifest.json').write_text(json.dumps({
                'upstream': {'vendored_at': 'process/upstream', 'scrub_blocklist': None},
                'entries': []}), encoding='utf-8')
            sources = {'local': {'level': 'repo-local', 'name': 'local', 'path': 'local'}}
            if universal:
                sources['precedent'] = {'level': 'universal', 'name': 'precedent',
                                        'path': 'process/upstream'}
            (repo / 'precedent.json').write_text(json.dumps(
                {'format_version': 1, 'sources': sources}), encoding='utf-8')
            (repo / 'AGENTS.md').write_text(
                '# notes\n' + ('<!-- BEGIN GENERATED: precedent-loader -->\n'
                               '<!-- END GENERATED -->\n' if block else ''),
                encoding='utf-8')
            if engine:
                (repo / 'tools').mkdir(exist_ok=True)
                (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    '{}\n', encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            return repo

        def run(repo, *extra):
            r = subprocess.run(
                [sys.executable, str(repo / 'process' / 'upstream' / 'tools' / 'practice_audit.py'),
                 *extra], capture_output=True, text=True, cwd=str(repo))
            return r.returncode, r.stdout + r.stderr

        classic = make('classic')
        half = make('half', universal=True)
        loaded = make('loaded', universal=True, block=True)
        pack = make('pack', catalogue=False)
        rc_c, out_c = run(classic)
        rc_h, out_h = run(half)
        rc_l, out_l = run(loaded)
        rc_p, out_p = run(pack)
        rc_n, out_n = run(classic, '--loader-notice')
        rc_nl, out_nl = run(loaded, '--loader-notice')
        # Check 8 (2026-09-24): loaded, but the engine never vendored at
        # tools/ -- the migration stopped before its step 7.
        noengine = make('noengine', universal=True, block=True, engine=False)
        rc_e, out_e = run(noengine)
        rc_en, out_en = run(noengine, '--loader-notice')
        cases = [
            ('a classic install (catalogue vendored, no universal source, no '
             'block) FAILS', rc_c == 1 and 'LOADER:' in out_c),
            ('and the failure names the migration',
             'MIGRATING_EXISTING_INSTALLS.md' in out_c),
            ('a universal source without the generated block still FAILS',
             rc_h == 1 and 'loader block' in out_h),
            ('a universal source plus the block passes check 5',
             rc_l == 0 and 'LOADER:' not in out_l),
            ('a pack-only layer (no catalogue vendored) is not held to it',
             rc_p == 0 and 'LOADER:' not in out_p),
            ('--loader-notice speaks on a classic install and exits 0',
             rc_n == 0 and 'NOT RUNNING' in out_n),
            ('--loader-notice is silent where the loader runs',
             rc_nl == 0 and out_nl.strip() == ''),
            ('check 8: the loader runs but tools/ENGINE_MANIFEST.json is '
             'missing -- FAILS and names the migration',
             rc_e == 1 and 'ENGINE:' in out_e
             and 'MIGRATING_EXISTING_INSTALLS' in out_e),
            ('and --loader-notice says so, still exiting 0',
             rc_en == 0 and 'NEVER VENDORED' in out_en),
            ('NEGATIVE: the same install WITH the manifest is not flagged',
             'ENGINE:' not in out_l),
        ]
        for name, passed in cases:
            if not passed:
                print(f"  practice_audit check 5 did NOT behave as stated: {name}")
        check(f"practice_audit fails a vendored catalogue nothing loads "
              f"({len(cases)} stated cases)", all(ok for _, ok in cases))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_practice_audit_declined():
    """practice_audit.py's check 6, stated as cases (practice:
    current-rule-governs). A consumer declined upstream's merge-keyword
    practice at one sync as a "duplicate"; upstream replaced it with a
    broader rule, and two later syncs carried the decline forward unread,
    so a session refused a command the rule in force authorized
    (2026-09-24). A "declined" entry now records the upstream file's hash
    as it stood when the decision was made, and the audit fails once the
    file moves until somebody decides again."""
    import hashlib, shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-auditdeclined-'))
    try:
        repo = tmp / 'repo'
        up = repo / 'process' / 'upstream'
        (up / 'tools').mkdir(parents=True)
        (up / 'practices').mkdir()
        shutil.copy(ROOT / 'tools' / 'practice_audit.py', up / 'tools' / 'practice_audit.py')
        shutil.copy(ROOT / 'tools' / 'generated_blocks.py', up / 'tools' / 'generated_blocks.py')
        old = up / 'practices' / 'old-rule.md'
        gone = up / 'practices' / 'gone-rule.md'
        old.write_text('---\nslug: old-rule\nstatus: active\n---\n## Rule\nnarrow\n',
                       encoding='utf-8')
        gone.write_text('---\nslug: gone-rule\nstatus: active\n---\n', encoding='utf-8')
        h = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
        host = repo / 'local' / 'host.md'
        host.parent.mkdir()
        host.write_text('a file of this repo, synced\n', encoding='utf-8')
        manifest = repo / 'process' / 'manifest.json'
        manifest.write_text(json.dumps({
            'upstream': {'vendored_at': 'process/upstream', 'scrub_blocklist': None},
            'entries': [
                {'practice': 'old-rule', 'upstream_path': 'practices/old-rule.md',
                 'local_path': None, 'status': 'declined',
                 'declined_upstream_sha256': h(old), 'notes': 'duplicate of a personal rule'},
                {'practice': 'host', 'upstream_path': '', 'local_path': 'local/host.md',
                 'status': 'synced', 'local_sha256': h(host)},
            ]}), encoding='utf-8')
        (repo / 'precedent.json').write_text(json.dumps({'format_version': 1, 'sources': {
            'precedent': {'level': 'universal', 'name': 'precedent', 'path': 'process/upstream'}}}),
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text('<!-- BEGIN GENERATED: precedent-loader -->\n'
                                        '<!-- END GENERATED -->\n', encoding='utf-8')
        # A migrated install: the engine is vendored at tools/ (check 8).
        (repo / 'tools').mkdir(exist_ok=True)
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)

        def run(*extra):
            r = subprocess.run([sys.executable, str(up / 'tools' / 'practice_audit.py'), *extra],
                               capture_output=True, text=True, cwd=str(repo))
            return r.returncode, r.stdout + r.stderr

        def entries():
            return {e['practice']: e for e in
                    json.loads(manifest.read_text(encoding='utf-8'))['entries']}

        rc_fresh, out_fresh = run()
        # Called from the SOURCE clone's module, as precedent_update.py
        # --repo does through checkin.py: the tree is the consumer's.
        spec = importlib.util.spec_from_file_location(
            'source_practice_audit', ROOT / 'tools' / 'practice_audit.py')
        source_audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(source_audit)
        from_source = source_audit.stale_declines(manifest)
        # Upstream moves on: the declined file is deduplicated into a successor.
        old.write_text('---\nslug: old-rule\nstatus: deduplicated\nin_force_at: new-rule\n'
                       '---\n## Rule\nnarrow\n', encoding='utf-8')
        (up / 'practices' / 'new-rule.md').write_text(
            '---\nslug: new-rule\nstatus: active\nsupersedes:  ["old-rule"]\n---\n',
            encoding='utf-8')
        rc_moved, out_moved = run()
        hash_before = entries()['old-rule']['declined_upstream_sha256']
        # An unrelated synced file changes while the decline is stale: the
        # re-baseline is its own job (2026-10-08, a consuming repository
        # read "FAIL -- 2 error(s)" from a re-baseline that had worked).
        host.write_text('a file of this repo, edited\n', encoding='utf-8')
        rc_base, out_base = run('--update-baseline')
        hash_after_baseline = entries()['old-rule']['declined_upstream_sha256']
        rc_still, out_still = run()
        rc_re, out_re = run('--redecide', 'old-rule')
        rc_after, out_after = run()
        # A decline with no hash, and one whose file is gone.
        m = json.loads(manifest.read_text(encoding='utf-8'))
        m['entries'].append({'practice': 'unhashed', 'upstream_path': 'practices/gone-rule.md',
                             'local_path': None, 'status': 'declined', 'notes': 'x'})
        manifest.write_text(json.dumps(m), encoding='utf-8')
        rc_nohash, out_nohash = run()
        gone.unlink()
        rc_gone, out_gone = run()
        # Check 7: a decline written as prose is warned about, and only
        # outside the generated block.
        (repo / 'AGENTS.md').write_text(
            'We declined the merge-keyword practice as a duplicate.\n'
            'The personal pack wins on conflict.\n'
            '<!-- BEGIN GENERATED: precedent-loader -->\n'
            'this duplicate of something is generated text\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        _rc_prose, out_prose = run()
        cases = [
            ('a decline made against the current upstream file passes',
             rc_fresh == 0 and 'declined OK' in out_fresh),
            ('run from the source clone, a consumer decline reads the consumer tree',
             from_source == []),
            ('the upstream file changing since the decline FAILS',
             rc_moved == 1 and 'DECLINED: [upstream:old-rule]' in out_moved),
            ('and the failure names where the rule lives now and what replaced it',
             'in force at new-rule' in out_moved and 'superseded by new-rule' in out_moved),
            ('--update-baseline never re-baselines a decline',
             hash_after_baseline == hash_before),
            ('--update-baseline re-baselines an unrelated synced file while a decline '
             'is stale, and exits 0 on it',
             rc_base == 0 and entries()['host']['local_sha256'] == h(host)
             and 're-baselined [upstream:host]' in out_base),
            ('...printing the stale decline as what the audit still fails on',
             'STILL FAILING THE AUDIT: DECLINED: [upstream:old-rule]' in out_base),
            ('...and the audit run bare still fails on it, and only on it',
             rc_still == 1 and 'DECLINED: [upstream:old-rule]' in out_still
             and 'DRIFT' not in out_still),
            ('--redecide records the current hash and exits 0',
             rc_re == 0 and entries()['old-rule']['declined_upstream_sha256'] == h(old)),
            ('after --redecide the audit passes again', rc_after == 0),
            ('a decline with no recorded hash FAILS',
             rc_nohash == 1 and 'no declined_upstream_sha256' in out_nohash),
            ('a decline whose upstream file is gone FAILS',
             rc_gone == 1 and 'no longer in the vendored tree' in out_gone),
            ('check 7 warns on a prose decline and a blanket precedence clause',
             'AGENTS.md:1 reads like a decline' in out_prose
             and 'AGENTS.md:2 reads like a decline' in out_prose),
            ('check 7 skips the generated loader block',
             'AGENTS.md:4' not in out_prose),
        ]
        for name, passed in cases:
            if not passed:
                print(f"  practice_audit check 6 did NOT behave as stated: {name}")
        check(f"practice_audit fails a decline the upstream file has moved past "
              f"({len(cases)} stated cases)", all(ok for _, ok in cases))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_practice_audit_fires():
    """practice_audit.py's --update-baseline, stated as cases against a
    throwaway manifest (practice: mistakes-become-rules).

    Regression case, found in the wild via a dependent repo's check-in
    (the project's own prior notes repository, 2026-09-04): a 'diverged' manifest entry
    marks a file as a deliberate, permanent customization that must never
    be proposed for export -- the whole point of the status. Before this
    fix, --update-baseline read ANY hash mismatch against the recorded
    local_sha256 as "the local file changed, so the divergence must be
    resolved" and silently flipped 'diverged' to 'synced' -- even when the
    mismatch was really just a stale baseline already wrong in the
    manifest, with the file itself untouched. Nothing in the tool's output
    named the flip, so it was invisible short of hand-diffing the manifest.
    A repo carrying a diverged entry could lose that marking on the next
    routine --update-baseline run for an unrelated reason, and a later
    check-in (INSTALL.md §4) could then propose the customization for
    export with nothing downstream able to tell "genuinely synced" apart
    from "flipped by this bug".

    Asserts the fix from outside the tool: run --update-baseline as a
    subprocess against a scratch manifest and read the entries back."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-practiceaudit-'))
    try:
        repo = tmp / 'repo'
        tools_dir = repo / 'process' / 'upstream' / 'tools'
        tools_dir.mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'practice_audit.py', tools_dir / 'practice_audit.py')
        shutil.copy(ROOT / 'tools' / 'generated_blocks.py', tools_dir / 'generated_blocks.py')
        (repo / 'process' / 'upstream').mkdir(exist_ok=True)
        (repo / 'local').mkdir()
        (repo / 'local' / 'diverged.md').write_text('customized on purpose\n', encoding='utf-8')
        (repo / 'local' / 'synced.md').write_text('vendored as-is\n', encoding='utf-8')
        (repo / 'local' / 'local.md').write_text('host configuration\n', encoding='utf-8')
        manifest = repo / 'process' / 'manifest.json'

        def write_manifest():
            manifest.write_text(json.dumps({
                'upstream': {'vendored_at': 'process/upstream', 'scrub_blocklist': None},
                'entries': [
                    {'practice': 'diverged_one', 'local_path': 'local/diverged.md',
                     'status': 'diverged', 'granularity': 'file',
                     'local_sha256': 'stale-hash-not-a-real-sha', 'notes': 'never export'},
                    {'practice': 'synced_one', 'local_path': 'local/synced.md',
                     'status': 'synced', 'granularity': 'file',
                     'local_sha256': 'stale-hash-not-a-real-sha', 'notes': ''},
                    {'practice': 'local_one', 'local_path': 'local/local.md',
                     'status': 'local-only', 'granularity': 'file',
                     'local_sha256': 'stale-hash-not-a-real-sha',
                     'notes': 'host configuration over an engine'},
                ],
            }, indent=2), encoding='utf-8')

        def run_update(*extra):
            r = subprocess.run(
                [sys.executable, str(tools_dir / 'practice_audit.py'),
                 '--update-baseline', '--manifest', str(manifest), *extra],
                capture_output=True, text=True, cwd=str(repo))
            entries = json.loads(manifest.read_text(encoding='utf-8'))['entries']
            return r, {e['practice']: e for e in entries}

        write_manifest()
        before = json.loads(manifest.read_text(encoding='utf-8'))['entries']
        before_hash = {e['practice']: e['local_sha256'] for e in before}
        result, after = run_update()
        write_manifest()
        named_result, named = run_update('--entry', 'diverged_one')
        write_manifest()
        typo_result, typo = run_update('--entry', 'no_such_entry')

        cases = [
            ("a 'diverged' entry's status is untouched by a bare re-run",
             after['diverged_one']['status'] == 'diverged'),
            ("a bare re-run leaves a 'diverged' entry's hash alone: its mismatch "
             "is what lists it as pending export (2026-10-07)",
             after['diverged_one']['local_sha256'] == before_hash['diverged_one']),
            ("the bare run says it left the diverged entry, and the entry is "
             "still listed as pending",
             "left [" in result.stdout and "pending:" in result.stdout),
            ("a 'synced' entry re-baselining still stays 'synced' (unchanged "
             "behaviour)", after['synced_one']['status'] == 'synced'
             and after['synced_one']['local_sha256'] != before_hash['synced_one']),
            ("--entry re-baselines the diverged entry it names, status kept",
             named['diverged_one']['local_sha256'] != before_hash['diverged_one']
             and named['diverged_one']['status'] == 'diverged'),
            ("--entry leaves every entry it does not name alone",
             named['synced_one']['local_sha256'] == before_hash['synced_one']),
            ("a changed 'local-only' entry is never listed as pending export "
             "(2026-10-07): nothing upstream receives it",
             'local/local.md' not in named_result.stdout),
            ("--entry with a name that matches nothing fails and changes nothing",
             typo_result.returncode != 0
             and all(typo[k]['local_sha256'] == before_hash[k] for k in before_hash)),
        ]

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  practice_audit --update-baseline did NOT behave as stated: {name}")
        check(f"practice_audit --update-baseline fires ({len(cases)} stated cases: "
              f"a bare run leaves 'diverged' entries pending; --entry accepts only "
              f"what it names)", ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _decision_records_violations(root):
    """The check's actual logic, taking a repo root so
    check_decision_records_not_inline_fires() can exercise it against
    scratch git repositories instead of only ever running once, for real,
    against this repo's own tree. Returns (status, ok, detail): status is
    'na' (detail is the not-applicable reason) or 'checked' (detail is the
    list of violation message strings; ok is False if that list is
    non-empty).

    WHY THE COMPARISON BASE IS THE MERGE-BASE WITH @{upstream}, NOT HEAD.
    The original version gated on `git status --porcelain` being non-empty
    and compared disk content against HEAD -- so it only ever looked at
    UNCOMMITTED changes. The moment a violating amendment is committed --
    the normal state for reviewing any already-pushed branch or PR, which
    AGENTS.md itself describes as the modal review path here -- the
    porcelain check comes back empty, the function returned early with
    "was not changed", and the violation was never inspected at all.
    Confirmed live: an identical inline entry passed as UNCOMMITTED and
    silently reported not-applicable the instant it was committed, no
    diagnostic. Comparing against the upstream merge-base instead of HEAD
    also correctly covers every commit this branch has added since it
    diverged, not just the most recent one -- HEAD~1 would have missed an
    earlier commit in a multi-commit push. Falls back to HEAD when there is
    no configured upstream (a fresh checkout with no remote, a detached
    HEAD) -- narrower, but still covers the case the original check did."""
    plan_md = root / 'spec' / 'PRACTICE_ENGINE_PLAN.md'
    if not plan_md.exists():
        return 'na', True, 'PRACTICE_ENGINE_PLAN.md does not exist here'

    up = subprocess.run(['git', 'rev-parse', '--abbrev-ref',
                         '--symbolic-full-name', '@{upstream}'],
                        cwd=str(root), capture_output=True, text=True)
    base_ref = 'HEAD'
    if up.returncode == 0:
        mb = subprocess.run(['git', 'merge-base', 'HEAD', up.stdout.strip()],
                            cwd=str(root), capture_output=True, text=True)
        if mb.returncode == 0 and mb.stdout.strip():
            base_ref = mb.stdout.strip()

    new_text = plan_md.read_text(encoding='utf-8', errors='ignore')
    old_result = subprocess.run(
        ['git', 'show', f'{base_ref}:spec/PRACTICE_ENGINE_PLAN.md'],
        cwd=str(root), capture_output=True, text=True)
    old_text = old_result.stdout if old_result.returncode == 0 else ''

    if new_text == old_text:
        return 'na', True, ('PRACTICE_ENGINE_PLAN.md has not changed '
                            f'relative to {base_ref[:9]}')

    def amendments_section(text):
        """This check is about ONE section's own growth pattern
        ("Amendments Since Approval"), not the whole document -- found the
        hard way, planting a Deferred-section edit and watching it get
        swept into a single 800+-word "entry" that actually ran from the
        Amendments section's last 2026-08-31 item all the way past Settled
        Since Draft v1 into Deferred, because nothing in either of those
        later sections happens to open a line with a bold date and the
        unscoped regex kept matching across the boundary. Scoping to the
        section between its own heading and the next top-level "## " is
        what the check was always meant to measure."""
        m = re.search(r'^## Amendments Since Approval\s*$', text, re.M)
        if not m:
            return ''
        rest = text[m.end():]
        end = re.search(r'^## ', rest, re.M)
        return rest[:end.start()] if end else rest

    old_section = amendments_section(old_text)
    new_section = amendments_section(new_text)
    if new_section == old_section:
        return 'na', True, ('the Amendments Since Approval section has not '
                            f'changed relative to {base_ref[:9]}')

    def entries(text):
        starts = [m.start() for m in AMENDMENT_ENTRY_RE.finditer(text)]
        if not starts:
            return []
        starts.append(len(text))
        return [text[a:b].strip() for a, b in zip(starts, starts[1:])]

    old_entries = set(entries(old_section))
    ok = True
    messages = []
    for entry in entries(new_section):
        if entry in old_entries:
            continue          # unchanged -- not this diff's to judge
        if DECISIONS_LINK_RE.search(entry):
            continue           # already points at a real record
        words = len(entry.split())
        if words > DECISION_LENGTH_WORDS:
            ok = False
            first_line = entry.splitlines()[0][:80]
            messages.append(
                f"PRACTICE_ENGINE_PLAN.md: a new amendment entry runs "
                f"{words} words with no decisions/*.md link ({first_line!r}"
                f"...) -- split the reasoning into a decisions/<date>-"
                f"<slug>.md record and leave a short pointer here instead")
    return 'checked', ok, messages


def check_decision_records_not_inline():
    """PRACTICE_ENGINE_PLAN.md is the one document AGENTS.md tells every
    session to read "first, in full" -- and its own "Amendments Since
    Approval" section grew from 56,675 to 108,557+ bytes across phases 0-4,
    almost entirely as accumulating dated decision write-ups. This is the
    exact failure pattern that motivated this whole rewrite (RPP's
    AGENTS.md: 29,443 -> 71,059 bytes in three days), happening to the plan
    itself, and it went unnoticed until a 2026-09-01 deep-check audit found
    it. decisions/README.md instantiates the mechanism
    PRACTICE_ENGINE_PLAN.md's own "Where Decisions and History Live"
    already specified but nothing had ever built: `decisions/<date>-
    <slug>.md`, never loaded automatically. This check is what makes it
    stick -- a NEW amendment entry over DECISION_LENGTH_WORDS with no
    decisions/*.md link fails, so growing the plan the old way costs a
    build failure, not just a note nobody reads. It is deliberately NOT
    registered as a `checked_by` in tools/precedent_check.py: it is not a
    property of any cataloged practice, and registering it there would
    inflate ENFORCEMENT.md's "N of 54 practices carry a checked_by" count
    with a phantom row that no practices/*.md file backs -- found the hard
    way, by doing exactly that and watching computed-numbers-in-scripts
    correctly reject the resulting drift in spec/ENFORCEMENT.md's generated
    block. Only judges entries NEW relative to the upstream merge-base --
    the plan's own existing amendment history, which is what motivated this
    check, is not retroactively flagged; see decisions/README.md. See
    _decision_records_violations()'s docstring for why the comparison base
    is the upstream merge-base rather than HEAD or the working tree."""
    status, ok, detail = _decision_records_violations(ROOT)
    if status == 'na':
        not_applicable('decision records not inline', detail)
        return
    for msg in detail:
        print(f"  {msg}")
    check('new plan amendments stay short or point at a decisions/ record '
          '(PRACTICE_ENGINE_PLAN.md must not regrow the way it just did)', ok)


def check_decision_records_not_inline_fires():
    """Direct test of _decision_records_violations() against scratch git
    repositories -- a real gap this repo's own audit found: nothing had
    ever planted a violation and watched this check catch it, the exact
    discipline check_leak_gate_fires()/check_precedent_check_fires() apply
    to everything else. Not registered under tools/precedent_check.py (see
    check_decision_records_not_inline's own docstring for why), so this is
    its equivalent -- named _fires to match that family's convention."""
    import shutil, tempfile

    def git(cwd, *args, check_rc=True):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-decisionrec-'))
    cases = []
    try:
        def scratch(name, text):
            repo = tmp / name
            repo.mkdir()
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.email', 'harness@example.com')
            git(repo, 'config', 'user.name', 'harness')
            (repo / 'spec').mkdir()
            (repo / 'spec' / 'PRACTICE_ENGINE_PLAN.md').write_text(
                text, encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'base')
            bare = tmp / (name + '.git')
            subprocess.run(['git', 'init', '--bare', '-q', str(bare)],
                           capture_output=True, text=True)
            git(repo, 'remote', 'add', 'origin', str(bare))
            git(repo, 'push', '-q', '-u', 'origin', 'HEAD:refs/heads/main')
            git(repo, 'branch', '--set-upstream-to=origin/main', check_rc=False)
            return repo

        base_text = ("# Plan\n\n## Amendments Since Approval\n\n"
                    "**2026-09-01 — v1, first.** Short.\n")
        long_entry = ' '.join(['word'] * 150)

        r1 = scratch('clean', base_text)
        status, ok, _detail = _decision_records_violations(r1)
        cases.append(('a clean, unchanged plan is not applicable', status == 'na'))

        # The invocation-scope bug: the old version only ever looked at
        # UNCOMMITTED changes (`git status --porcelain`). Here the violation
        # is fully committed, which used to report "not changed" and never
        # inspect the content at all.
        r2 = scratch('committed-violation', base_text)
        (r2 / 'spec' / 'PRACTICE_ENGINE_PLAN.md').write_text(
            base_text + f"\n**2026-09-02 — v2, a long one.** {long_entry}\n",
            encoding='utf-8')
        git(r2, 'add', '-A'); git(r2, 'commit', '-qm', 'inline amendment')
        status, ok, _detail = _decision_records_violations(r2)
        cases.append(('a committed (not just staged/uncommitted) inline '
                       'violation is caught', status == 'checked' and not ok))

        # A format variant (colon instead of the exact em-dash-with-spaces)
        # must still be recognized as an entry boundary. Placed ABOVE the
        # existing entry, matching this section's own newest-first
        # convention -- the shape in which the old regex made a
        # non-matching entry invisible entirely, not merely miscounted.
        r3 = scratch('colon-variant', base_text)
        (r3 / 'spec' / 'PRACTICE_ENGINE_PLAN.md').write_text(
            f"# Plan\n\n## Amendments Since Approval\n\n"
            f"**2026-09-02:** {long_entry}\n\n"
            f"**2026-09-01 — v1, first.** Short.\n", encoding='utf-8')
        git(r3, 'add', '-A'); git(r3, 'commit', '-qm', 'colon variant')
        status, ok, _detail = _decision_records_violations(r3)
        cases.append(('a colon-separated date variant is recognized as an '
                       'entry, not silently dropped',
                      status == 'checked' and not ok))

        # A bare mention of the word "decisions/" in prose, with no actual
        # file reference, must not exempt an otherwise-violating entry.
        r4 = scratch('bare-mention', base_text)
        (r4 / 'spec' / 'PRACTICE_ENGINE_PLAN.md').write_text(
            base_text + f"\n**2026-09-02 — v2, not migrated.** {long_entry} "
            f"not yet migrated to decisions/, still keeping every word "
            f"inline.\n", encoding='utf-8')
        git(r4, 'add', '-A'); git(r4, 'commit', '-qm', 'bare mention')
        status, ok, _detail = _decision_records_violations(r4)
        cases.append(('a bare mention of "decisions/" with no real link '
                       'does not exempt a long inline entry',
                      status == 'checked' and not ok))

        # A REAL decisions/*.md reference does exempt it -- the check must
        # not simply fail on every long entry regardless of content.
        r5 = scratch('real-link', base_text)
        (r5 / 'spec' / 'PRACTICE_ENGINE_PLAN.md').write_text(
            base_text + f"\n**2026-09-02 — v2, migrated.** {long_entry} see "
            f"decisions/2026-09-02-migrated.md for the reasoning.\n",
            encoding='utf-8')
        git(r5, 'add', '-A'); git(r5, 'commit', '-qm', 'real link')
        status, ok, _detail = _decision_records_violations(r5)
        cases.append(('a real decisions/*.md link exempts an otherwise-long '
                       'entry', status == 'checked' and ok))

        ok_all = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  decision records check did NOT behave as stated: {name}")
        check(f'decision records not inline fires ({len(cases)} stated '
              f'cases: committed -- not just uncommitted -- violations are '
              f'caught, a format-variant date entry is still recognized, a '
              f'bare "decisions/" mention does not exempt an entry)', ok_all)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_all_workflows_disclosed():
    """Every EXISTING GitHub Actions workflow file is named in
    GITHUB_ACTIONS.md -- not just newly-added ones.

    WHY THIS IS SEPARATE FROM `github-setup-disclosed`
    (tools/precedent_check.py). That check enforces the practice on a
    CHANGE: it fires on ctx.added_files() in the diff being checked, so a
    workflow merged before the practice existed to catch it -- exactly what
    happened to leak-gate.yml, found undisclosed by a 2026-09-01 deep-check
    audit -- is permanently invisible to it. Once a workflow file is
    committed, it can never again appear as "added." This check asks the
    tree-wide question instead: for every .yml/.yaml file that exists RIGHT
    NOW in .github/workflows/, is its name mentioned anywhere in
    GITHUB_ACTIONS.md? It complements the change-scoped check rather than
    replacing it -- this one runs every time regardless of what changed,
    which is what actually closes the gap the change-scoped check leaves
    open."""
    workflows_dir = ROOT / '.github' / 'workflows'
    if not workflows_dir.is_dir():
        not_applicable('all workflows disclosed', 'no .github/workflows/ directory')
        return
    doc_path = ROOT / 'documentation' / 'GITHUB_ACTIONS.md'
    if not doc_path.exists():
        check('all workflows disclosed', False,
              'no documentation/GITHUB_ACTIONS.md exists to disclose any workflow in')
        return
    doc = doc_path.read_text(encoding='utf-8', errors='ignore')
    ok = True
    for f in sorted(workflows_dir.glob('*.y*ml')):
        if f.name not in doc:
            ok = False
            print(f"  {f.name} exists in .github/workflows/ but is not named "
                  f"anywhere in GITHUB_ACTIONS.md")
    check('all workflows disclosed (every file in .github/workflows/ is '
          'named in GITHUB_ACTIONS.md)', ok)


def check_no_duplication_refuses_a_sets_copy_of_a_universal_rule():
    """A practice set may not carry an active copy of a practice its declared
    universal source has active; it adds to it in a practice of its own
    (Morgan, 2026-10-06: "rules should not be repeated, but supporting repos
    can have additions for them"). Planted end to end in a fixture set
    beside a fixture universal: the copy is refused, naming the way out; an
    addition under its own slug, a deduplicated copy and a retired set all
    pass."""
    import shutil as _sh
    import tempfile as _tf
    def prac(slug, status):
        return (f'---\nslug: {slug}\ntitle: T\ntier: on-demand\nseverity: default\n'
                f'applies_to: ["**"]\noccasion: "x"\ndefines: []\nstatus: {status}\n'
                f'---\n## Rule\nx\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n')
    cases = []
    with _tf.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        uni = base / 'uni'
        (uni / 'practices').mkdir(parents=True)
        (uni / 'practices' / 'shared-rule.md').write_text(prac('shared-rule', 'active'), encoding='utf-8')
        (uni / 'precedent-source.json').write_text(json.dumps({'level': 'universal', 'name': 'precedent'}), encoding='utf-8')
        st = base / 'set'
        (st / 'practices').mkdir(parents=True)
        _sh.copytree(ROOT / 'tools', st / 'tools', ignore=_sh.ignore_patterns('__pycache__'))
        # What makes a repository a practice SOURCE to the engine: the kind
        # its vendored engine's manifest declares (_publishes_practices).
        (st / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'format_version': 1, 'kind': 'source', 'files': []}), encoding='utf-8')
        (st / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '../uni'}]}), encoding='utf-8')
        meta = {'level': 'shared', 'name': 'set'}
        (st / 'precedent-source.json').write_text(json.dumps(meta), encoding='utf-8')
        (st / 'practices' / 'shared-rule-on-set.md').write_text(prac('shared-rule-on-set', 'active'), encoding='utf-8')

        def run():
            r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                                'no-duplication'], cwd=st, capture_output=True, text=True,
                               env=dict(os.environ, PRECEDENT_USER_CONFIG=str(base / 'none.json')))
            return r.stdout + r.stderr
        out = run()
        cases.append(('an addition under its own slug passes', ' 0 violated' in out and '1 passed' in out))
        (st / 'practices' / 'shared-rule.md').write_text(prac('shared-rule', 'active'), encoding='utf-8')
        out = run()
        cases.append(('an active copy of a universal rule is refused, naming the way out',
                      ' 1 violated' in out and 'practices/shared-rule.md' in out
                      and 'add' in out and 'deduplicated' in out))
        (st / 'practices' / 'shared-rule.md').write_text(prac('shared-rule', 'deduplicated'), encoding='utf-8')
        out = run()
        cases.append(('a deduplicated copy passes', ' 0 violated' in out))
        (st / 'practices' / 'shared-rule.md').write_text(prac('shared-rule', 'active'), encoding='utf-8')
        (st / 'precedent-source.json').write_text(json.dumps(dict(meta, retired={'date': '2026-10-06'})), encoding='utf-8')
        out = run()
        cases.append(('a retired set is passed over', ' 0 violated' in out and 'retired' in out))
    failed = [n for n, ok in cases if not ok]
    check(f'no-duplication refuses a set\'s copy of a universal rule ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_very_deep_check_account_owes_tests_and_incidents():
    """The account check (precedent_check.py --only very-deep-check), for a
    run from 2026-11-01 on: question 27 is done -- every repository's test
    review shows nothing left to judge, this checkout's times are from the
    run, and tools/test_verdicts.json holds a verdict dated in the run when
    TEST WORTH listed tests here -- and question 20 is done: `## Incidents`
    carries a verdict line for every incident INCIDENT COVERAGE listed (the
    ledger keeps the list). Either may instead quote the person agreeing to
    skip it, on a line opening `Skipped with the person's words:`.

    The 2026-10-30 run recorded question 27 "Not judged this run" and its 62
    incident verdicts were lost with a scratch file; nothing refused either.
    Controls: the complete account passes; a run dated before 2026-11-01 is
    not held to it."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-account-q27-'))
    try:
        repo = _vdc_account_fixture(tmp)
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        got = _vdc_account_findings(pc, repo)
        cases.append(('CONTROL: the account that shows the work passes',
                      got == '', got))

        def planted(old, new):
            doc.write_text(_VDC_G_ACCOUNT.replace(old, new, 1), encoding='utf-8')
            return _vdc_account_findings(pc, repo)
        got = planted('Never judged: 0. To judge again: 0. Cheapen or retire '
                      'owed: 0. Carrying a lead: 0.\n<!--',
                      'Never judged: 2. To judge again: 0. Cheapen or retire '
                      'owed: 0. Carrying a lead: 0.\n<!--')
        cases.append(('THE CASE: a set still has tests never judged',
                      'question 27 is not done -- a set still has 2 never '
                      'judged' in got, got))
        got = planted('Times measured 2026-11-01', 'Times measured 2026-10-09')
        cases.append(("THE CASE: this checkout's times are from before the run",
                      "test times were measured 2026-10-09, before this run"
                      in got, got))
        got = planted('<!--/vdc-embed:test-review-->',
                      '<!--/vdc-embed:test-review-->\n\nSkipped with the '
                      "person's words: \"Morgan: skip the tests today\"")
        cases.append(("CONTROL: with the person's words, a stale block passes",
                      got == '', got))
        doc.write_text(_VDC_G_ACCOUNT, encoding='utf-8')
        (repo / 'tools' / 'test_verdicts.json').write_text(json.dumps(
            {'verdicts': {'check_a': {'verdict': 'keep', 'importance': 'low',
                                      'why': 'w', 'date': '2026-10-30'}}}),
            encoding='utf-8')
        got = _vdc_account_findings(pc, repo)
        cases.append(('THE CASE: tests were listed here and no verdict is '
                      'dated in the run',
                      'TEST WORTH listed 3 test(s) here to judge and '
                      'tools/test_verdicts.json holds no verdict dated '
                      '2026-11-01 or later' in got, got))
        repo = _vdc_account_fixture(tmp / 'b')
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        got = planted('- `todo-fx-two`: nothing mechanical, deliberately, '
                      'because it is judgment.\n', '')
        cases.append(('THE CASE: an incident the run listed has no line',
                      'question 20 is not done -- 1 of the 2 incident(s) '
                      'INCIDENT COVERAGE listed have no verdict line: '
                      'todo-fx-two' in got, got))
        got = planted('- `todo-fx-two`: nothing mechanical, deliberately, '
                      'because it is judgment.', '- `todo-fx-two`')
        cases.append(('THE CASE: the slug alone is not a verdict',
                      'have no verdict line: todo-fx-two' in got, got))
        got = planted('## Incidents\n', '## Incident notes\n')
        cases.append(('THE CASE: no `## Incidents` section',
                      'the account has no `## Incidents` section' in got, got))
        got = planted('- `gotcha-fx-one`: a check with a planted case, '
                      'check_fx.\n- `todo-fx-two`: nothing mechanical, '
                      'deliberately, because it is judgment.',
                      "Skipped with the person's words: 'Morgan: not today'")
        cases.append(("CONTROL: the person's words agreeing to skip it pass",
                      'question 20' not in got, got))
        repo = _vdc_account_fixture(tmp / 'c', date='2026-10-31')
        doc = repo / 'spec' / 'VERY_DEEP_CHECK_LATEST_RUN.md'
        got = planted('## Incidents\n', '## Incident notes\n')
        cases.append(('CONTROL: a run dated before 2026-11-01 is not held to it',
                      got == '', got))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check account owes question 27 and question 20, '
          f'or the person\'s words ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_removal_selects_its_checks():
    """A change that deletes or renames a file selects every tree check
    declaring selects_on_removal -- rename-updates-links, whose subject is
    what a removal strands and whose `**` reached it only by the rotation:
    a consumer commit moving about twenty files ran it as "not run this
    invocation" (2026-10-07). A change removing nothing leaves it to the
    rotation as before."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as _pc
    cases = []
    tree = sorted(s for s, c in _pc.CHECKS.items() if c['scope'] == 'tree')
    real_removed, real_touched = _pc._removed_files, _pc._touched_files
    try:
        _pc._touched_files = lambda: ['site/new-name.css']
        _pc._removed_files = lambda: ['site/old-name.css']
        picked = _pc._scoped_tree_slugs(tree, buckets=set())
        cases.append(('a rename selects rename-updates-links, with the '
                      'rotation emptied', 'rename-updates-links' in picked))
        _pc._removed_files = lambda: []
        picked = _pc._scoped_tree_slugs(tree, buckets=set())
        cases.append(('a change removing nothing leaves it to the rotation',
                      'rename-updates-links' not in picked))
    finally:
        _pc._removed_files, _pc._touched_files = real_removed, real_touched
    cases.append(('rename-updates-links declares it',
                  _pc.CHECKS['rename-updates-links'].get('selects_on_removal') is True))
    bad = [n for n, ok in cases if not ok]
    check(f'a change that removes a file selects the checks that judge what a '
          f'removal strands ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_consumer_engine_carries_what_its_checks_import():
    """A consumer's precedent_check.py imports doc_lifecycle for
    document-status-header and speculation-is-marked, and the module was on
    neither engine list, so both checks reported SKIPPED in every installed
    repo while the practices were in force (very deep check, 2026-10-05,
    pass 1). Every engine module precedent_check.py imports is now on the
    consumer list, and an installed consumer runs the check for real."""
    import re as _re
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    src = (ROOT / 'tools' / 'precedent_check.py').read_text(encoding='utf-8')
    mods = (set(_re.findall(r'^\s*import (\w+)', src, _re.M))
            | set(_re.findall(r'^\s*from (\w+) import', src, _re.M)))
    local = sorted(m for m in mods if (ROOT / 'tools' / f'{m}.py').is_file())
    # Imported inside a try that reads nothing when the module is absent,
    # and shipped only here on purpose (2026-10-18: the sets-beside advisory
    # in rename-updates-links; precedent_check.py's own comment says so).
    upstream_only = {'precedent_refresh_sources'}
    missing = [m for m in local if f'{m}.py' not in _pve.CONSUMER_ENGINE_FILES
               and m not in upstream_only]
    cases = [(f'every engine module precedent_check.py imports is vendored '
              f'to a consumer (missing: {", ".join(missing) or "none"})',
              not missing)]
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-doclife-'))
    try:
        # The shared fresh install (_fresh_install_fixture), copied, not rerun.
        _fresh_install_fixture(fx)
        (fx / 'spec').mkdir()
        (fx / 'spec' / 'PLAN.md').write_text(
            '---\ntitle: "Plan"\nkind: reference\nstatus: current\n'
            'opened: 2026-10-06\nsupersedes: []\naudience: session\n'
            'summary: "a plan"\n---\n# Plan\n\nText.\n', encoding='utf-8')
        (fx / 'spec' / 'OTHER.md').write_text('# Other\n\nNo header.\n',
                                              encoding='utf-8')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                            '--only', 'document-status-header'], cwd=str(fx),
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        cases.append(('an installed consumer runs document-status-header instead '
                      'of skipping it', 'did not import' not in out
                      and 'SKIPPED' not in out))
        cases.append(('...and it finds the unstamped document',
                      'spec/OTHER.md' in out))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [n for n, ok in cases if not ok]
    check(f'a consumer\'s engine carries every module its checks import '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_behavioral_replay():
    # Runs tools/behavioral_replay.py for real (not a canned number). It
    # prints a "REPLAY_STATUS: OK|MISMATCH|DEGRADED" marker line: OK means
    # precedent_paths.py's output matched an independent re-derivation on
    # every replayed commit (the mechanical channel has no bugs against real
    # history); MISMATCH is a real defect; DEGRADED means this clone doesn't
    # have enough commit history for a meaningful replay (a fresh shallow
    # clone, most commonly) -- an environment precondition, not a loader
    # defect, so it is reported as not-yet-applicable rather than pass or
    # fail. The script's own stdout states plainly what a PASS here does and
    # does not prove about the plan's premise (see its docstring); this
    # check only gates on the part of that which is a pass/fail fact.
    result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'behavioral_replay.py')],
                             capture_output=True, text=True)
    status_line = next((l for l in result.stdout.splitlines() if l.startswith('REPLAY_STATUS:')), '')
    detail = (result.stdout + result.stderr).strip()
    name = ('behavioral replay (path-triggered channel matches an independent re-derivation '
            'across this repo\'s own commit history; see `python3 tools/behavioral_replay.py` '
            'for the full measured report, including what it does NOT prove)')
    if 'DEGRADED' in status_line:
        not_applicable(name, status_line.split('REPLAY_STATUS: ', 1)[-1])
    elif result.returncode == 0 and 'OK' in status_line:
        check(name, True)
    else:
        check(name, False, detail.splitlines()[-1] if detail else 'no REPLAY_STATUS line printed')
def _workflow_harness_drift(body):
    """-> [problem, ...] for a workflow's text: every way it runs
    verify_harness.py other than `--as-ci`, and every split variable it
    sets itself. [] means the workflow takes its split from CI_SHARDS and
    _as_ci_runs, the one description there is."""
    lines = [l for l in body.splitlines() if not l.lstrip().startswith('#')]
    runs = [l.strip() for l in lines if 'verify_harness.py' in l]
    problems = []
    if not runs:
        problems.append('the workflow never runs tools/verify_harness.py')
    for r in runs:
        if '--as-ci' not in r.split():
            problems.append(f'runs the suite another way: {r!r}')
    for var in _SPLIT_VARS:
        if any(re.search(rf'\b{var}\s*:', l) for l in lines):
            problems.append(f'sets {var} itself, a split --as-ci does not make')
    return problems


def check_as_ci_shards_match_the_workflow():
    """GitHub's deep-check workflow runs the suite through `--as-ci` and
    nothing else, so GitHub and a session deal it into the same processes.

    WHY. Until 2026-10-07 the split was written twice: the workflow's own
    jobs, and CI_SHARDS here. This check compared the two -- and both
    still said "heavy, and everything else" after `--as-ci` learned, on
    2026-09-30, to cut "everything else" into parts across the cores. The
    split lived below the table, so the check stayed green while GitHub ran
    about 570 checks on one core for 30 minutes on every Promote into main
    and a session ran the same suite in about 11
    (gotcha-2026-10-07-a-speed-fix-to-a-mirrored-test-reached-only-the-local-copy).
    Now the workflow runs `--as-ci` itself, and this refuses any second
    description of the split coming back."""
    planted = [
        ('the old two-job workflow is refused',
         'steps:\n  - run: python3 tools/verify_harness.py\n    env:\n'
         '      PRECEDENT_CHECK_ONLY: check_precedent_check_fires\n'
         '      PRECEDENT_HARNESS_ALL: "1"\n'
         '  - run: python3 tools/verify_harness.py\n    env:\n'
         '      PRECEDENT_CHECK_SKIP: check_precedent_check_fires\n', True),
        ('a matrix of parts set in the workflow is refused',
         '  - run: python3 tools/verify_harness.py --as-ci\n    env:\n'
         '      PRECEDENT_AS_CI_JOBS: ${{ matrix.jobs }}\n', True),
        ('a workflow that drops the suite is refused',
         '  - run: python3 tools/precedent_check.py\n', True),
        ('one --as-ci step, the split named only in a comment, passes',
         '  # PRECEDENT_CHECK_SKIP was set here until 2026-10-07\n'
         '  - run: python3 tools/verify_harness.py --as-ci\n', False),
    ]
    cases = [(name, bool(_workflow_harness_drift(body)) == want, '')
             for name, body, want in planted]
    wf = ROOT / '.github' / 'workflows' / 'deep-check.yml'
    if wf.is_file():
        drift = _workflow_harness_drift(wf.read_text(encoding='utf-8'))
        cases.append(('this repo\'s deep-check.yml runs --as-ci and nothing else',
                      not drift, '; '.join(drift)))
    bad = [f'{n}{": " + d if d else ""}' for n, ok, d in cases if not ok]
    check(f'GitHub runs the suite through --as-ci, the one split '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))




def check_gone_path_matcher_matches_one_regex_per_path():
    """change-updates-its-docs finds a removed path by a prefix lookup
    (precedent_check.gone_path_matcher) where it used to try one regex per
    removed path on every line -- five to ten minutes on a large consumer.
    The answer must be the same, line for line: the first path in sorted
    order that the line names on the same boundaries. Compared here with
    that old loop on a seeded fixture of paths and lines built to sit on
    every boundary (a longer path, a suffix, a prefix directory, a trailing
    dot or dash, a non-ASCII word, paths with characters outside a path
    run)."""
    import random
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    rnd = random.Random(7)
    words = ['practices', 'tools', 'spec', 'todo', 'x', 'a-b', 'v1', 'foo_bar', 'ü']

    def path():
        return ('/'.join(rnd.choice(words) for _ in range(rnd.randint(2, 4)))
                + rnd.choice(['.md', '.py', '', '.json', '.md.bak']))
    gone = {path() for _ in range(400)} | {'odd dir/x.md', 'a+b/c.md'}
    pool = sorted(gone)
    lines = []
    # 1000 lines, not 3000 (2026-10-31): the old loop is the cost, and every
    # boundary comes from the same generator either way.
    for _ in range(1000):
        toks = []
        for _ in range(rnd.randint(1, 10)):
            r = rnd.random()
            if r < 0.25:
                toks.append(rnd.choice(pool))
            elif r < 0.45:
                toks.append(rnd.choice(['', 'other/', '`', '(', 'x', '.', '-'])
                            + path() + rnd.choice(['', '.', '-x', '/', '`', ')', ',', '_']))
            else:
                toks.append(rnd.choice(words))
        lines.append(rnd.choice([' ', '', '/']).join(toks))
    lines += ['see odd dir/x.md here', 'a+b/c.md', 'xa+b/c.md', 'odd dir/x.mdz']
    pats = [(g, re.compile(r'(?<![\w./-])' + re.escape(g) + r'(?![\w-])')) for g in pool]
    want = [next((g for g, p in pats if p.search(l)), None) for l in lines]
    first = pc.gone_path_matcher(gone)
    got = [first(l) for l in lines]
    diff = [(l, w, g) for l, w, g in zip(lines, want, got) if w != g]
    hits = sum(1 for w in want if w)
    return (not diff and hits > 300, f'{len(lines)} lines, {hits} with a hit, '
            f'{len(gone)} removed paths', f'{len(diff)} differ, first: {diff[:2]}')


def check_decline_while_a_condition_holds():
    """A decline that names a condition about this repository
    (`declined_while`) is not asked again when the declined tool changes
    upstream, only when the condition stops holding; a declined practice is
    asked again on every change all the same.

    2026-10-13, a consuming repository: its decline of tools/doc_html.py
    ("this repo renders no HTML") came back as "a decline to decide again"
    on every upstream edit to that tool, seven times with the same reason."""
    import contextlib, hashlib, io, tempfile
    import practice_audit as pa
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-decline-while-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')
    git = lambda *a: subprocess.run(['git', '-C', str(repo), *a], env=env,
                                    capture_output=True, text=True)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    cases = []
    try:
        repo = tmp / 'consumer'
        tree = repo / 'process' / 'upstream'
        (tree / 'tools').mkdir(parents=True)
        (tree / 'practices').mkdir()
        tool, rule = tree / 'tools' / 'doc_html.py', tree / 'practices' / 'tables.md'
        tool.write_text('# renders pages\n', encoding='utf-8')
        rule.write_text('## Rule\nOne table renderer.\n', encoding='utf-8')
        mp = repo / 'process' / 'manifest.json'

        def manifest(**extra):
            mp.write_text(json.dumps({'upstream': {'vendored_at': 'process/upstream'},
                                      'entries': [
                dict({'practice': 'table-renderer', 'upstream_path': 'tools/doc_html.py',
                      'status': 'declined', 'notes': 'we render no HTML',
                      'declined_upstream_sha256': sha(tool.read_bytes())}, **extra),
                dict({'practice': 'tables', 'upstream_path': 'practices/tables.md',
                      'status': 'declined', 'notes': 'we render no HTML',
                      'declined_upstream_sha256': sha(rule.read_bytes())}, **extra)]}),
                encoding='utf-8')
        git('init', '-q')
        manifest(declined_while='renders-no-html')
        git('add', '-A')
        git('commit', '-qm', 'declines')
        listed = lambda: {n.split(':', 1)[1]: why for n, why in pa.stale_declines(mp)}

        cases.append(('nothing changed: nothing is asked', not listed(), str(listed())))
        tool.write_text('# renders pages, faster\n', encoding='utf-8')
        rule.write_text('## Rule\nOne table renderer, everywhere.\n', encoding='utf-8')
        now = listed()
        cases.append(('the declined tool changed upstream while the repository still '
                      'renders no HTML: not asked again',
                      'table-renderer' not in now, str(now)))
        cases.append(('the declined practice changed: asked again, condition or not',
                      'tables' in now and 'changed upstream' in now['tables'], str(now)))
        (tree / 'page.html').write_text('<p>vendored</p>', encoding='utf-8')
        git('add', '-A')
        cases.append(('a page inside the vendored tree is not this repository rendering one',
                      'table-renderer' not in listed(), str(listed())))
        (repo / 'report.html').write_text('<p>ours</p>', encoding='utf-8')
        git('add', 'report.html')
        now = listed()
        cases.append(('a tracked page of its own: asked again, saying what it found',
                      'no longer holds' in now.get('table-renderer', '')
                      and 'report.html' in now.get('table-renderer', ''), str(now)))
        git('rm', '-q', '--cached', 'report.html')
        (repo / 'tools').mkdir()
        (repo / 'tools' / 'doc_html_host.json').write_text(
            json.dumps({'docs': [['a.md', 'A']]}), encoding='utf-8')
        cases.append(('a render list in tools/doc_html_host.json: asked again',
                      'doc_html_host.json' in listed().get('table-renderer', ''),
                      str(listed())))
        (repo / 'tools' / 'doc_html_host.json').unlink()
        manifest(declined_while='renders-nothing-at-all')
        cases.append(('a condition the tool does not know is asked about, never trusted',
                      'not a condition' in listed().get('table-renderer', ''),
                      str(listed())))

        manifest()
        tool.write_text('# renders pages, faster still\n', encoding='utf-8')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = pa.redecide([mp], 'table-renderer', 'renders-no-html')
        entry = json.loads(mp.read_text(encoding='utf-8'))['entries'][0]
        cases.append(('--redecide NAME --while records the condition with the hash',
                      rc == 0 and entry.get('declined_while') == 'renders-no-html'
                      and entry['declined_upstream_sha256'] == sha(tool.read_bytes()),
                      out.getvalue()))
        (repo / 'report.html').write_text('<p>ours</p>', encoding='utf-8')
        git('add', 'report.html')
        manifest()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = pa.redecide([mp], 'table-renderer', 'renders-no-html')
        cases.append(('...refused, writing nothing, when the condition does not hold',
                      rc == 1 and 'declined_while' not in json.loads(
                          mp.read_text(encoding='utf-8'))['entries'][0], ''))
        manifest(declined_while='renders-no-html')
        with contextlib.redirect_stdout(io.StringIO()):
            pa.redecide([mp], 'table-renderer')
        cases.append(('a --redecide without --while drops a condition the new '
                      'decision was not made on',
                      'declined_while' not in json.loads(
                          mp.read_text(encoding='utf-8'))['entries'][0], ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a decline holds while its condition does ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_redecided_decline_sticks():
    """A decline re-decided between two Update Vendors runs stays decided,
    and the update and the consumer's own audit judge it against the same
    text: upstream's, at the commit this repo takes.

    2026-10-08, from a consuming repository: the update left "a decline to
    decide again"; the person read the new text and ran practice_audit.py
    --redecide; every rerun listed the same decline again, and a second
    --redecide put back the hash the person had corrected by hand. For a
    declined tools/ file -- which the catalogue copy leaves out once the
    repo vendors its own engine -- the audit fell back to `ROOT/tools/...`,
    and ROOT is the module's own repository: the consumer when --redecide
    ran there, the SOURCE CLONE'S WORKING TREE when precedent_update.py ran
    the same check through checkin.py --repo. Two different files, so the
    two never agreed. One function now answers for both
    (practice_audit.decline_basis): a file in the vendored tree is judged
    by that copy, an engine file by the hash the engine manifest records
    for upstream's text.

    Negative control, measured 2026-10-08 against
    2026-10-08-produce-copy-check-y1ktn at ae07871f: the first run never
    lists the engine-file decline (the source clone's working tree still
    holds the old text), and every rerun after --redecide lists it again."""
    import hashlib
    import precedent_vendor_engine as _pve
    branch = _pve.SOURCE_BRANCH
    fx = _LocalEditsFixture('precedent-redecide-')
    cases = []
    sha = lambda b: hashlib.sha256(b).hexdigest()
    try:
        repo = fx.consumer('decline')
        seeded = fx.seeded_from(repo)
        practice, tool = 'practices/verify-postcondition.md', 'tools/precedent_show.py'
        show = lambda rel: subprocess.run(['git', '-C', str(ROOT), 'show', f'{seeded}:{rel}'],
                                          capture_output=True).stdout
        old = {practice: show(practice), tool: show(tool)}
        (repo / 'process').mkdir()
        (repo / 'process' / 'manifest.json').write_text(json.dumps({
            'upstream': {'repo': 'https://github.com/alex137/BestPractice',
                         'vendored_at': 'process/upstream', 'branch': branch,
                         'commit': seeded, 'scrub_blocklist': None},
            'entries': [{'practice': name, 'upstream_path': rel, 'local_path': None,
                         'status': 'declined', 'declined_upstream_sha256': sha(old[rel]),
                         'notes': 'covered by a rule of our own'}
                        for name, rel in (('verify-postcondition', practice),
                                          ('precedent-show', tool))]},
            indent=2) + '\n', encoding='utf-8')
        fx.sh(sys.executable, str(ROOT / 'tools' / 'checkin.py'), 'update', str(ROOT),
              '--repo', str(repo), '--force', '--from-ref', seeded, cwd=repo)
        fx.commit(repo, 'catalogue with two declines')
        fx.sh('git', 'push', '-q', 'origin', 'HEAD:main', cwd=repo)
        # This tree's audit, run where the consumer's own runs: a copy inside
        # the consumer, so it acts on the consumer, kept out of git.
        aud = repo / '.audit' / 'tools'
        aud.mkdir(parents=True)
        for n in ('practice_audit.py', 'generated_blocks.py'):
            shutil.copy(ROOT / 'tools' / n, aud / n)
        with open(repo / '.git' / 'info' / 'exclude', 'a', encoding='utf-8') as f:
            f.write('.audit/\n')
        new = {practice: old[practice] + b'\nA sentence upstream added.\n',
               tool: old[tool] + b'\n# upstream changed this tool\n'}
        ref = fx.upstream(seeded, new)

        def recorded():
            return {e['upstream_path']: e['declined_upstream_sha256'] for e in json.loads(
                (repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))['entries']}

        def redecide():
            for name in ('verify-postcondition', 'precedent-show'):
                fx.sh(sys.executable, str(aud / 'practice_audit.py'), '--redecide', name,
                      cwd=repo)

        want = {rel: sha(new[rel]) for rel in new}
        left = lambda out, rel: [l for l in out.split('LEFT FOR YOU', 1)[-1].splitlines()
                                 if 'a decline to decide again' in l and rel in l]
        declines = lambda out: [l.strip()[:200] for l in out.splitlines()
                                if 'a decline to decide again' in l]
        _rc, out1 = fx.update(repo, ref)
        cases.append(('the first run lists both moved declines',
                      left(out1, practice) and left(out1, tool), declines(out1)))
        redecide()
        cases.append(('--redecide records the hash of the text being taken',
                      recorded() == want, (recorded(), want)))
        _rc, out2 = fx.update(repo, ref)
        cases.append(('the rerun does not ask again about either re-decided decline',
                      not left(out2, practice) and not left(out2, tool), declines(out2)))
        _rc, audit = fx.sh(sys.executable, str(aud / 'practice_audit.py'), cwd=repo)
        cases.append(('...and the consumer\'s own audit agrees: no DECLINED failure',
                      'DECLINED:' not in audit, failure_detail(audit, 1500)))
        redecide()
        cases.append(('a second --redecide keeps the same hashes', recorded() == want,
                      (recorded(), want)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))

def check_adds_to_names_a_rule_in_force():
    """precedent_check.py's adds-to-names-a-rule-in-force (2026-10-09): an
    addition reaches a session only with the rule it adds to, so one naming
    a slug no source in force carries, or naming itself, or marked resident,
    is refused. It passes an addition to a rule of the same set, one to a
    deduplicated slug whose chain ends in force, and a practice with no
    adds_to at all."""
    import tempfile, shutil
    import build_views as _bv              # noqa: F401 -- cached for the check
    import precedent_check as pc
    P = _addition_fixture_practice
    plants = {
        # slug: (text, fires)
        'base-rule': (P('base-rule'), False),
        'old-rule': (P('old-rule', status='deduplicated', to='base-rule'), False),
        'good-addition': (P('good-addition', adds='base-rule'), False),
        'via-old-name': (P('via-old-name', adds='old-rule'), False),
        'typo-addition': (P('typo-addition', adds='base-rul'), True),
        'self-addition': (P('self-addition', adds='self-addition'), True),
        'resident-addition': (P('resident-addition', tier='resident',
                                adds='base-rule'), True),
    }
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='adds-to-check-'))
    saved = pc.ROOT
    env_saved = os.environ.get('PRECEDENT_USER_CONFIG')
    try:
        (tmp / 'practices').mkdir()
        (tmp / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': []}), encoding='utf-8')
        for slug, (text, _f) in plants.items():
            (tmp / 'practices' / f'{slug}.md').write_text(text, encoding='utf-8')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-user-config.json')
        pc.ROOT = tmp
        try:
            got = pc._adds_to_names_a_rule_in_force(None)
        finally:
            pc.ROOT = saved
        hit = {pathlib.PurePath(f.file()).stem for f in got
               if not isinstance(f, pc.Unverified)}
        for slug, (_t, fires) in plants.items():
            cases.append((f'{slug}: {"refused" if fires else "passes"}',
                          (slug in hit) == fires))
        text = ' '.join(str(f) for f in got)
        cases.append(('the refusal names the slug that resolves nowhere',
                      'adds_to: base-rul ' in text))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        pc.ROOT = saved
        if env_saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = env_saved
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'adds_to names a rule in force ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_boildown_moments_named():
    """precedent_check.py's boildown-moments-named (2026-10-20): the-boildown
    names two moments, and a practice that restates one in its occasion,
    title, a reply_check.json note or a tool it ships is refused, since a
    change to the moment then breaks it silently (twice in two days). It
    passes a practice that names the moment, the-boildown itself, a retired
    practice, a Rule sentence that names the moment while explaining it, and
    a restatement that sits only in Why or Story, which are history."""
    import tempfile, shutil
    import build_views as _bv              # noqa: F401 -- cached for the check
    import precedent_check as pc
    P = _addition_fixture_practice
    plants = {
        # slug: (text, fires)
        'quotes-the-line': (P('quotes-the-line', occasion='a reply that '
                              'says You can archive this session'), True),
        'paraphrases-it': (P('paraphrases-it', occasion='a reply that says '
                             'the session can be archived'), True),
        'ships-a-quoting-tool': (P('ships-a-quoting-tool',
                                   extra='ships:       ["tools/zz_note.py"]\n'),
                                 True),
        'has-a-quoting-note': (P('has-a-quoting-note'), True),
        'names-the-moment': (P('names-the-moment', occasion='the '
                               'archive-line reply (the-boildown)'), False),
        'the-boildown': (P('the-boildown', occasion='You can archive this '
                           'session'), False),
        'retired-quoter': (P('retired-quoter', status='retired', occasion=''
                             'You can archive this session'), False),
        # The Rule is what a session follows, so a restatement there is
        # refused too (2026-10-20: stale-branch-cleanup's Rule kept the old
        # moment, in negative words, while the tool said "none").
        'rule-restates': (P('rule-restates', rule='Not in a reply that does '
                            'not say the session can be archived.'), True),
        'rule-explains-the-name': (P('rule-explains-the-name', rule='In the '
                                     'archive-line reply (the one that says '
                                     '"You can archive this session"), link '
                                     'it.'), False),
        'story-only': (P('story-only', rule='Do the thing.\n\n## Story\n'
                         'Back then it said "You can archive this session".'),
                       False),
    }
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='moments-check-'))
    saved = pc.ROOT
    try:
        (tmp / 'practices').mkdir()
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'zz_note.py').write_text(
            'NOTE = \'in one that answers "Archive" or "Archive?"\'\n',
            encoding='utf-8')
        (tmp / 'reply_check.json').write_text(json.dumps([
            {'practice': 'has-a-quoting-note',
             'note': 'Link it whenever you can archive this session.'}]),
            encoding='utf-8')
        for slug, (text, _f) in plants.items():
            (tmp / 'practices' / f'{slug}.md').write_text(text, encoding='utf-8')
        pc.ROOT = tmp
        try:
            got = pc._boildown_moments_named(None)
        finally:
            pc.ROOT = saved
        hit = {pathlib.PurePath(f.file()).stem for f in got}
        for slug, (_t, fires) in plants.items():
            cases.append((f'{slug}: {"refused" if fires else "passes"}',
                          (slug in hit) == fires))
        text = ' '.join(str(f) for f in got)
        cases.append(('the refusal names the moment to write instead',
                      'Write "the archive-line reply (the-boildown)"' in text))
        cases.append(('the shipped tool is named as where it restates',
                      'tools/zz_note.py restates the closing reply' in text))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'Boildown moments are named, never restated ({len(cases)} stated '
          f'cases)', not failed, '; '.join(failed))


def check_code_owner_practice_stays_out_of_the_index():
    """precedent_check.py's code-owner-practice-stays-out-of-the-index
    (2026-10-08): a practice marked `visible_to: code-owners` is carried by a
    code owner's session file, charged to the consuming repository's
    session-load ceiling, and a consuming repository's Debut failed on about 27 of
    them costing index lines. The check refuses one whose only route is the
    occasion index, or which is resident, and says what to add; it passes one
    routed by a real applies_to, a gate or a command, a practice for everyone,
    and an exception the registry lists with a reason; and it reports an
    exception that is no longer needed, or carries no reason."""
    import tempfile, shutil
    import build_views as _bv              # noqa: F401 -- cached for the check
    import precedent_audience as _pa       # noqa: F401
    import precedent_check as pc
    name = 'a code-owner practice stays out of the occasion index'
    fm = ('---\nslug:        {slug}\ntitle:       A planted case\n'
          'tier:        {tier}\nseverity:    default\n'
          'applies_to:  {applies}\noccasion:    "doing {slug}"\n'
          'gates:       {gates}\ncommand:     {command}\n'
          'index_clause: "a planted case"\nchecked_by:  null\n'
          'defines:     []\nstatus:      active\nsupersedes:  []\n'
          'overrides:   null\nadded:       "2026-10-08"\n'
          'approved_by: "fixture"\n{visible}---\n\n## Rule\nPlanted.\n\n'
          '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n')
    owners = 'visible_to:  code-owners\n'
    plants = {
        # slug: (tier, applies_to, gates, command, visible_to, fires)
        'unrouted': ('on-demand', '["**"]', '[]', 'null', owners, True),
        'resident': ('resident', '["docs/**"]', '[]', 'null', owners, True),
        'by-path': ('on-demand', '["docs/**"]', '[]', 'null', owners, False),
        'by-gate': ('on-demand', '["**"]', '["push"]', 'null', owners, False),
        'by-command': ('on-demand', '["**"]', '[]',
                       '{"Planted Phrase": "A planted command."}', owners, False),
        'for-everyone': ('on-demand', '["**"]', '[]', 'null', '', False),
        'excepted': ('on-demand', '["**"]', '[]', 'null', owners, False),
        # An addition loads with the rule it adds to, so it lands nowhere
        # on its own (2026-10-09), index_required or not.
        'addition': ('on-demand', '["**"]', '[]', 'null',
                     owners + 'adds_to:     by-path\nindex_required: true\n',
                     False),
    }
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='code-owner-index-'))
    saved = pc.ROOT
    try:
        (tmp / 'practices').mkdir()
        (tmp / 'tools').mkdir()
        for slug, (tier, applies, gates, command, visible, _f) in plants.items():
            (tmp / 'practices' / f'{slug}.md').write_text(fm.format(
                slug=slug, tier=tier, applies=applies, gates=gates,
                command=command, visible=visible), encoding='utf-8')
        reg = tmp / 'tools' / 'session_load_budgets.json'

        def run(allowed):
            reg.write_text(json.dumps({'code_owners_in_index': allowed}),
                           encoding='utf-8')
            pc.ROOT = tmp
            try:
                return pc._code_owner_practice_stays_out_of_the_index(None)
            finally:
                pc.ROOT = saved

        got = run({'excepted': 'no path or gate names its moment.',
                   'gone-now': 'was needed once.', 'by-path': 'stale.',
                   'no-reason': ''})
        hit = {pathlib.PurePath(f.file()).stem for f in got
               if f.file().startswith('practices/')}
        for slug, (*_x, fires) in plants.items():
            cases.append((f'{slug}: {"refused" if fires else "passes"}',
                          (slug in hit) == fires))
        text = ' '.join(str(f) for f in got)
        cases.append(('the refusal says to add applies_to, a gate or a command',
                      all(w in text for w in ('applies_to', 'gates:', 'command:'))))
        reg_findings = ' '.join(str(f) for f in got
                                if f.file() == 'tools/session_load_budgets.json')
        cases.append(('an exception for a practice that is gone is reported',
                      'gone-now' in reg_findings and 'remove the entry' in reg_findings))
        cases.append(('an exception for a routed practice is reported',
                      'by-path' in reg_findings))
        cases.append(('an exception with no reason is reported',
                      'no-reason with no reason' in reg_findings))
        cases.append(('a needed exception is not reported',
                      'excepted' not in reg_findings))
        got = run({})
        cases.append(('with no exceptions, the excepted practice is refused',
                      any(f.file() == 'practices/excepted.md' for f in got)))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_changed_files_only_judges_the_change():
    """A push into the landing branch runs the practice checks on the files it
    changes, and only those (Morgan, 2026-09-27, strength: decided: "ONLY for
    files that changed (or were added) in that session ... NOT for every file
    in the repo"). Both directions: a change that breaks a document's
    title/heading match is refused; a change elsewhere passes even while
    that mismatch sits in the tree, and says it left it to the full check."""
    import tempfile
    name = ('the practice checks on a push into the landing branch judge only '
            'the files it changes')
    tool = ROOT / 'tools' / 'precedent_check.py'
    doc = None
    for f in sorted((ROOT / 'spec').glob('*.md')):
        text = f.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'^title:\s+(.+)$', text, re.M)
        if text.startswith('---\n') and m and f'\n# {m.group(1).strip()}\n' in text:
            doc = f.relative_to(ROOT)
            break
    if not tool.is_file() or doc is None:
        not_applicable(name, 'no precedent_check.py, or no spec document with a '
                       'lifecycle header whose heading matches its title')
        return
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='changed-files-only-'))
    wt = tmp / 'wt'
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(*a):
        return subprocess.run(['git', '-C', str(wt), '-c', 'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env)

    # Each case runs the one check it is about, never the full sweep: a
    # sweep took about 28 seconds and this test ran eleven, so it was the
    # suite's second slowest at about 400 seconds on GitHub's runner
    # (Morgan, 2026-10-08: "minor and very very long, so let's fix this
    # right now"). What --changed-files-only does with a finding -- keep it,
    # set it aside, say why -- is the same code whichever checks ran, and
    # every real push into the landing branch runs the full sweep this way anyway.
    def run_check(since, slug):
        p = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only', slug,
                            '--range', f'{since}...HEAD', '--changed-files-only'],
                           cwd=wt, capture_output=True, text=True, env=env)
        return p.returncode, p.stdout + p.stderr

    def break_heading():
        path = wt / doc
        text = path.read_text(encoding='utf-8')
        title = re.search(r'^title:\s+(.+)$', text, re.M).group(1).strip()
        path.write_text(text.replace(f'\n# {title}\n', '\n# A heading that is not the title\n', 1),
                        encoding='utf-8')
    try:
        subprocess.run(['git', '-C', str(ROOT), 'worktree', 'add', '-q', '--detach',
                        str(wt), _ref_including_worktree(ROOT)], capture_output=True)
        base = git('rev-parse', 'HEAD').stdout.strip()
        break_heading()
        git('commit', '-qam', 'break the heading')
        rc, out = run_check(base, 'document-status-header')
        cases.append(('a change that breaks a document\'s heading is refused',
                      rc == 1 and 'document-status-header' in out, failure_detail(out, 800)))
        broken = git('rev-parse', 'HEAD').stdout.strip()
        with open(wt / 'README.md', 'a', encoding='utf-8') as f:
            f.write('\nAn unrelated line.\n')
        git('commit', '-qam', 'touch another file')
        rc, out = run_check(broken, 'document-status-header')
        cases.append(('a change elsewhere passes while the mismatch sits in the tree, '
                      'and says it left it to the full check',
                      rc == 0 and 'not judged here' in out, failure_detail(out, 800)))

        # A tree check's finding THIS push caused is kept wherever it lands
        # (Morgan, 2026-10-07): a new hook with no PARALLELS row is refused
        # at Booked, though the row belongs in a file the push never
        # touched; the next, unrelated push is not refused for it.
        start = git('rev-parse', 'HEAD').stdout.strip()
        hook = wt / '.claude' / 'hooks' / 'zz-fixture-hook.sh'
        hook.write_text('#!/bin/bash\nexit 0\n', encoding='utf-8')
        hook.chmod(0o755)
        git('add', str(hook))
        git('commit', '-qm', 'a new Claude-only hook, no PARALLELS row')
        rc, out = run_check(start, 'claude-only-surface-has-a-parallel')
        cases.append(('a new hook with no PARALLELS row is refused at Booked, '
                      'as a finding this push caused',
                      rc == 1 and 'claude-only-surface-has-a-parallel' in out
                      and 'this push caused them' in out, failure_detail(out, 800)))
        caused_at = git('rev-parse', 'HEAD').stdout.strip()
        with open(wt / 'README.md', 'a', encoding='utf-8') as f:
            f.write('\nAnother unrelated line.\n')
        git('commit', '-qam', 'touch another file again')
        rc, out = run_check(caused_at, 'claude-only-surface-has-a-parallel')
        cases.append(('the next, unrelated push passes, and names the missing '
                      'row as left for the full check',
                      rc == 0 and 'claude-only-surface-has-a-parallel: '
                      'templates/harness/PARALLELS.md' in out, failure_detail(out, 800)))

        # A consumer's practice file is sync output: an unglossed acronym in
        # one is refused where the practice is authored, and not judged in a
        # repo MANIFEST.json says it was materialized into (2026-09-28,
        # a consuming repo's Update Vendors, refused on vendor-update-runbook).
        start = git('rev-parse', 'HEAD').stdout.strip()
        practice = sorted((wt / 'practices').glob('*.md'))[0]
        with open(practice, 'a', encoding='utf-8') as f:
            f.write('\nThe QZXW fixture line.\n')
        git('commit', '-qam', 'an unglossed acronym in a practice')
        rc, out = run_check(start, 'acronyms-glossary')
        cases.append(('an unglossed acronym added to a practice where it is authored '
                      'is refused', rc == 1 and 'acronyms-glossary' in out
                      and 'QZXW' in out, failure_detail(out, 800)))
        (wt / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': practice.stem, 'level': 'universal'}]}), encoding='utf-8')
        git('add', 'MANIFEST.json')
        git('commit', '-qm', 'the practice is materialized here')
        rc, out = run_check(start, 'acronyms-glossary')
        cases.append(('...and the same line in a practice MANIFEST.json says was '
                      'materialized is not judged, and the note says why',
                      rc == 0 and 'materialized from another source' in out, failure_detail(out, 800)))
        git('rm', '-q', 'MANIFEST.json')
        git('checkout', '-q', start, '--', str(practice.relative_to(wt)))
        git('commit', '-qam', 'undo the materialized fixture')

        # --practice-file-checks runs the checks whose subject is a published
        # practice file, in one process (2026-10-29: 5fd34d4b3 landed a
        # relative ../gotchas/ link in a practice, which only
        # practice-links-travel reports).
        def practice_file_checks(since):
            p = subprocess.run([sys.executable, 'tools/precedent_check.py',
                                '--practice-file-checks', '--range',
                                f'{since}...HEAD', '--changed-files-only'],
                               cwd=wt, capture_output=True, text=True, env=env)
            return p.returncode, p.stdout + p.stderr
        start = git('rev-parse', 'HEAD').stdout.strip()
        with open(practice, 'a', encoding='utf-8') as f:
            f.write('\nThe fixture\'s [trap](../gotchas/INDEX.md).\n')
        git('commit', '-qam', 'a practice link that does not travel')
        rc, out = practice_file_checks(start)
        # How many checks ran: an engine without the flag ran the whole
        # audit, over a hundred checks, and found the same link.
        summary = next((l for l in out.splitlines()
                        if l.startswith('precedent_check: ')), '')
        ran = sum(int(n) for n in re.findall(
            r'(\d+) (?:passed|violated|advisory|errored|skipped|exempted)\b',
            summary))
        cases.append(('--practice-file-checks refuses a changed practice whose '
                      'relative link does not travel, running only the '
                      'practice-file checks',
                      rc == 1 and 'VIOLATION  practice-links-travel' in out
                      and 'does not travel' in out and 0 < ran < 40,
                      f'{ran} checks ran: ' + failure_detail(out, 800)))
        linked = git('rev-parse', 'HEAD').stdout.strip()
        with open(wt / 'README.md', 'a', encoding='utf-8') as f:
            f.write('\nA line beside the practice fixture.\n')
        git('commit', '-qam', 'touch another file')
        rc, out = practice_file_checks(linked)
        cases.append(('...and a later change to another file is not refused for it',
                      rc == 0, failure_detail(out, 800)))
        git('checkout', '-q', start, '--', str(practice.relative_to(wt)), 'README.md')
        git('commit', '-qam', 'undo the link fixture')

        # A deletion strands its mentions in files the change never touches.
        # Those are still this change's doing, and must be refused here, not
        # one stage later (2026-09-30: a consumer's Update Vendors passed
        # Booked and the Debut into staging refused on about 15 files).
        start = git('rev-parse', 'HEAD').stdout.strip()
        git('rm', '-q', 'documentation/CLOUD_SETUP.md')
        git('commit', '-qm', 'delete a file other files cite')
        rc, out = run_check(start, 'rename-updates-links')
        cases.append(('a change that deletes a file an untouched file cites is refused',
                      rc == 1 and 'rename-updates-links' in out
                      and 'documentation/CLOUD_SETUP.md' in out, failure_detail(out, 800)))
        deleted = git('rev-parse', 'HEAD').stdout.strip()
        # .gitignore cites nothing; README.md does, and a change touching it
        # would rightly be refused for the mention it carries.
        with open(wt / '.gitignore', 'a', encoding='utf-8') as f:
            f.write('\n# an unrelated line\n')
        git('commit', '-qam', 'touch another file after the deletion')
        rc, out = run_check(deleted, 'rename-updates-links')
        cases.append(('...and a later change that deletes nothing is not refused for it',
                      rc == 0, failure_detail(out, 800)))
        git('checkout', '-q', start, '--', 'documentation/CLOUD_SETUP.md', '.gitignore')
        git('commit', '-qm', 'undo the deletion fixture')

        # A check script a sync brings judges the whole repository, and it
        # is itself a changed file on the push that brings it. Its findings
        # are judged by the file each names, so a standing problem elsewhere
        # waits for the full check, and one in a file the push brings is
        # refused (2026-10-07, a consuming repository: a one-file note was
        # refused over a book kept as a source).
        start = git('rev-parse', 'HEAD').stdout.strip()
        (wt / 'tools' / 'checks').mkdir(exist_ok=True)
        (wt / 'tools' / 'checks' / 'check_planted_newcomer.py').write_text(
            'import pathlib, sys\n'
            'root = pathlib.Path(__file__).resolve().parents[2]\n'
            'print("VIOLATION: planted-newcomer")\n'
            'print("  README.md carries a planted standing problem")\n'
            'if (root / "PLANTED_NEW.md").exists():\n'
            '    print("  PLANTED_NEW.md carries a planted problem this push brings")\n'
            'sys.exit(1)\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-qm', 'a newly synced check script')
        rc, out = run_check(start, 'check_planted_newcomer')
        cases.append(('a newly arrived check\'s finding on a file the push does not '
                      'change does not refuse it', rc == 0, failure_detail(out, 800)))
        brought = git('rev-parse', 'HEAD').stdout.strip()
        (wt / 'PLANTED_NEW.md').write_text('# New\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-qm', 'a file the new check flags')
        rc, out = run_check(brought, 'check_planted_newcomer')
        cases.append(('...and its finding on a file the push brings does',
                      rc == 1 and 'PLANTED_NEW.md' in out, failure_detail(out, 800)))
        git('rm', '-q', 'PLANTED_NEW.md', 'tools/checks/check_planted_newcomer.py')
        git('commit', '-qm', 'undo the newcomer fixture')

        # The file-level checks (checks-follow-the-tier): only the changed
        # files, and the views a changed practice feeds.
        def files_check(since):
            p = subprocess.run([sys.executable, 'tools/precedent_push_check.py',
                                '--changed-files-check', since],
                               cwd=wt, capture_output=True, text=True, env=env)
            return p.returncode, p.stdout + p.stderr
        start = git('rev-parse', 'HEAD').stdout.strip()
        rc, out = files_check(start)
        cases.append(('with nothing changed, the file-level checks pass', rc == 0, failure_detail(out, 400)))
        (wt / 'tools' / 'zz_broken_fixture.py').write_text('def broken(:\n', encoding='utf-8')
        git('add', 'tools/zz_broken_fixture.py')
        git('commit', '-qm', 'a Python file that does not compile')
        rc, out = files_check(start)
        cases.append(('a changed Python file that does not compile is refused, by name',
                      rc == 1 and 'zz_broken_fixture.py: does not compile' in out, failure_detail(out, 400)))
        git('rm', '-q', 'tools/zz_broken_fixture.py')
        (wt / 'zz_broken_fixture.sh').write_text('if then fi\n', encoding='utf-8')
        git('add', 'zz_broken_fixture.sh')
        git('commit', '-qm', 'a shell script that does not parse')
        start = git('rev-parse', 'HEAD~1').stdout.strip()
        rc, out = files_check(start)
        cases.append(('a changed shell script that does not parse is refused, by name',
                      rc == 1 and 'zz_broken_fixture.sh: does not parse' in out, failure_detail(out, 400)))
        git('rm', '-q', 'zz_broken_fixture.sh')
        git('commit', '-qm', 'clean up')
        start = git('rev-parse', 'HEAD').stdout.strip()
        practice = next(iter(sorted((wt / 'practices').glob('*.md'))))
        # Its occasion, which MAP.md renders -- an edit the views must follow.
        text = practice.read_text(encoding='utf-8')
        practice.write_text(re.sub(r'^(occasion:\s+"?)', r'\1when a fixture says so, or ', text,
                                   count=1, flags=re.M), encoding='utf-8')
        git('commit', '-qam', 'change a practice without regenerating the views')
        rc, out = files_check(start)
        stale_ok = rc == 1 and 'not regenerated' in out
        subprocess.run([sys.executable, 'tools/build_views.py'], cwd=wt,
                       capture_output=True, text=True, env=env)
        git('commit', '-qam', 'regenerate the views')
        rc, out = files_check(start)
        cases.append(('a changed practice whose views were not regenerated is refused, '
                      'and passes once they are', stale_ok and rc == 0, failure_detail(out, 400)))
        # A new practice moves the counts doc_sync keeps, so it is refused
        # at this push, not first at the Debut (the quick tier once skipped
        # doc_sync, 2026-09-29).
        start = git('rev-parse', 'HEAD').stdout.strip()
        src = practice.read_text(encoding='utf-8')
        (wt / 'practices' / 'zz-fixture-new-rule.md').write_text(
            re.sub(r'^slug:(\s+)\S+', r'slug:\1zz-fixture-new-rule', src,
                   count=1, flags=re.M), encoding='utf-8')
        subprocess.run([sys.executable, 'tools/build_views.py'], cwd=wt,
                       capture_output=True, text=True, env=env)
        git('add', '-A')
        git('commit', '-qm', 'a new practice, views rebuilt, counts not')
        rc, out = files_check(start)
        refused = rc == 1 and 'doc_sync.py --write' in out
        subprocess.run([sys.executable, 'tools/doc_sync.py', '--write'], cwd=wt,
                       capture_output=True, text=True, env=env)
        git('commit', '-qam', 'regenerate the counts')
        rc, out = files_check(start)
        cases.append(('a new practice whose generated counts were not '
                      'regenerated is refused at this push, and passes once '
                      'they are', refused and rc == 0, failure_detail(out, 400)))
        # A size cap warns at the quick check and refuses at the full
        # check, the Debut's (Morgan, 2026-09-30, strength: decided). The resident cap is
        # lowered under what the block holds.
        start = git('rev-parse', 'HEAD').stdout.strip()
        reg = wt / 'tools' / 'session_load_budgets.json'
        data = json.loads(reg.read_text(encoding='utf-8'))
        # Per-part caps bind only where no session-load total is declared
        # (build_views.TOTAL_KEY); this fixture tests them, so it has none.
        data.pop('session_load_tokens', None)
        data['resident_block_tokens'] = 100
        reg.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        bv = subprocess.run([sys.executable, 'tools/build_views.py'], cwd=wt,
                            capture_output=True, text=True, env=env)
        cases.append(('over its cap, build_views still writes the block, and '
                      'warns that staging will refuse it',
                      bv.returncode == 0 and 'build_views WARNING' in bv.stderr
                      and 'the full check refuses it' in bv.stderr,
                      failure_detail(bv.stdout + bv.stderr, 400)))
        git('commit', '-qam', 'a block over its resident cap')
        rc, out = run_check(start, 'loader-within-caps')
        cases.append(('the quick check lets it through with a warning '
                      'naming the staging refusal',
                      rc == 0 and 'over a size cap. The quick check lets it through' in out,
                      failure_detail(out, 600)))
        full = subprocess.run([sys.executable, 'tools/precedent_check.py',
                               '--only', 'loader-within-caps'], cwd=wt,
                              capture_output=True, text=True, env=env)
        cases.append(('...and the full check refuses it',
                      full.returncode == 1 and 'VIOLATION' in full.stdout,
                      failure_detail(full.stdout + full.stderr, 400)))
        start = git('rev-parse', 'HEAD').stdout.strip()
        (wt / 'zz_fixture.json').write_text('{"a": 1,}\n', encoding='utf-8')
        git('add', 'zz_fixture.json')
        git('commit', '-qm', 'a JSON file that does not parse')
        rc, out = files_check(start)
        cases.append(('a changed JSON file that does not parse is refused, by name',
                      rc == 1 and 'zz_fixture.json: is not valid JSON' in out, failure_detail(out, 400)))
        git('rm', '-q', 'zz_fixture.json')
        git('commit', '-qm', 'clean up')
        start = git('rev-parse', 'HEAD').stdout.strip()
        (wt / 'tools' / 'checks' / 'tests').mkdir(parents=True, exist_ok=True)
        (wt / 'tools' / 'checks' / 'check_zzfixture.py').write_text('print("ok")\n',
                                                                    encoding='utf-8')
        (wt / 'tools' / 'checks' / 'tests' / 'test_zzfixture.sh').write_text(
            'echo "the fixture test failed"; exit 1\n', encoding='utf-8')
        # A new check also brings its planted case, or the changed-files
        # check refuses it for that instead (2026-09-29).
        with open(wt / 'tools' / 'verify_harness.py', 'a', encoding='utf-8') as f:
            f.write("\n# case('check_zzfixture', ...) -- the fixture's planted case\n")
        git('add', 'tools/checks', 'tools/verify_harness.py')
        git('commit', '-qm', 'a check whose own test fails')
        rc, out = files_check(start)
        # Tests run at the Debut, never before a push (Morgan, 2026-10-16):
        # the failing test is named, not run, and refuses nothing here.
        cases.append(("a changed check's test is named for the Debut, not run "
                      "before the push", rc == 0 and 'test_zzfixture.sh: failed'
                      not in out and "1 test(s) of changed checks run at the "
                      "Debut, not here: tools/checks/tests/test_zzfixture.sh" in out,
                      failure_detail(out, 400)))
    finally:
        subprocess.run(['git', '-C', str(ROOT), 'worktree', 'remove', '--force', str(wt)],
                       capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_light_check_skips_declared_records():
    """The light check's broken-link scan skips a file precedent.json
    declares in `record_paths`, and still flags the same link anywhere else.

    2026-10-05: a consumer's Update Vendors run failed on links inside its
    as-filed patent packages -- documents it had declared as records,
    because they name files at the paths they had when filed and may never
    be edited. Every other path-reading check honored the declaration; this
    one did not."""
    import tempfile, types
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='light-records-'))
    saved = pc.ROOT
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        (tmp / 'precedent.json').write_text(json.dumps({'record_paths': [
            {'path': 'as-filed.md', 'reason': 'held as filed'},
            {'path': 'old-records/', 'reason': 'a directory of records'}]}), encoding='utf-8')
        (tmp / 'old-records').mkdir()
        for rel in ('as-filed.md', 'old-records/audit.md', 'live.md'):
            (tmp / rel).write_text('See [the spec](moved-away.md).\n', encoding='utf-8')
        subprocess.run(['git', 'add', '-A'], cwd=str(tmp), capture_output=True, check=True)
        pc.ROOT = tmp
        got = [f.file() for f in pc._light_check(types.SimpleNamespace(root=tmp))]
        cases.append(('a declared record file is skipped', 'as-filed.md' not in got))
        cases.append(('a file in a declared record directory is skipped',
                      'old-records/audit.md' not in got))
        cases.append(('the same link in a live file is still flagged', 'live.md' in got))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('the light check skips the record files a repo declares',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_default_branch_reads_each_repos_trunk():
    """The host's default branch is checked against the repository's own
    trunk, whatever it is called -- never against the name `main`.

    2026-10-05: a consumer whose trunk is `master` by decision failed the
    check, and the failure undid its Update Vendors run. Four cases, each on
    a bare remote this test builds: a declared `master` passes; a declared
    `trunk` the host does not show is a violation; nothing declared passes
    whatever the host shows; and a host default that differs from
    `base_branch` with no `trunk` is COULD NOT VERIFY (ask the person),
    never a violation."""
    import tempfile, types
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='default-branch-'))

    def repo(name, head, declared):
        bare = tmp / (name + '.git')
        work = tmp / name
        subprocess.run(['git', 'init', '-q', '--bare', '-b', head, str(bare)],
                       capture_output=True, check=True)
        subprocess.run(['git', 'init', '-q', '-b', head, str(work)],
                       capture_output=True, check=True)
        (work / 'precedent.json').write_text(json.dumps(declared), encoding='utf-8')
        for args in (['add', '-A'],
                     ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
                      'commit', '-q', '-m', 'x'],
                     ['remote', 'add', 'origin', str(bare)],
                     ['push', '-q', 'origin', f'HEAD:refs/heads/{head}']):
            subprocess.run(['git', *args], cwd=str(work), capture_output=True, check=True)
        return pc._default_branch(types.SimpleNamespace(root=work))

    try:
        got = repo('master-declared', 'master', {'base_branch': 'master'})
        cases.append(('a trunk named master, declared, passes', got == []))
        got = repo('trunk-mismatch', 'master', {'trunk': 'main'})
        cases.append(('a declared trunk the host does not show is a violation',
                      len(got) == 1 and not isinstance(got[0], pc.Unverified)
                      and "'master'" in got[0].detail and "'main'" in got[0].detail))
        got = repo('undeclared', 'develop', {})
        cases.append(('nothing declared: the host default is the trunk', got == []))
        got = repo('tiered', 'main', {'base_branch': 'staging'})
        cases.append(('base_branch differs and no trunk: ask, never a violation',
                      len(got) == 1 and isinstance(got[0], pc.Unverified)
                      and '`trunk`' in got[0].detail))
        got = repo('tiered-declared', 'main', {'base_branch': 'staging', 'trunk': 'main'})
        cases.append(('...and once trunk is declared it passes', got == []))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('default-branch checks the host against each repo\'s own trunk',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_ci_templates_install_pyyaml_before_the_checks():
    """Every shipped CI template that runs the check suite installs PyYAML
    before it does.

    2026-09-28: the practice-set workflow template (retired 2026-10-01) had
    installed PyYAML since
    2026-09-13, because a check script materialized from a practice set may
    import it. light-check.yml.template runs the same scripts in consuming
    repos and never got the step, so a set's `import yaml` crashed on the
    bare runner and failed a consuming repo's pull request into main -- while
    the local push check, where PyYAML is installed, had passed the same
    tree. A template that runs the suite without the step is that crash
    waiting for the next set that imports it."""
    cases = []
    tdir = ROOT / 'templates' / 'github-actions'
    for tpl in sorted(tdir.glob('*.template')):
        text = tpl.read_text(encoding='utf-8')
        # The first line that RUNS it: a comment naming it is not a run.
        run = re.search(r'^(?![ \t]*#)[^\n]*precedent_check\.py', text, re.M)
        if not run:
            continue
        runs = run.start()
        m = re.search(r'pip install[^\n]*\bpyyaml\b', text, re.I)
        cases.append((f'{tpl.name} installs PyYAML before running the checks',
                      bool(m) and m.start() < runs))
    failed = [name for name, ok in cases if not ok]
    if not cases:
        failed.append('no template under templates/github-actions/ runs '
                      'precedent_check.py, so this case checked nothing')
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_reply_examples_are_tested_with_what_they_inherit():
    """A set's requirement that says "inherits": true is tested by its
    examples merged over the requirement it replaces, as a session merges it.

    2026-10-29: the ladder set's landing pair, trimmed to what it adds over
    universal's, had its "land it on staging" trigger from universal alone.
    reply-rules-hold-their-examples tested the set's copy by itself, so its
    own refused example went through, and the set's full sweep failed on a
    rule that worked in every session."""
    import tempfile
    import precedent_check as pc
    cases = []
    with tempfile.TemporaryDirectory(prefix='precedent-inherit-examples-') as d:
        tmp = pathlib.Path(d)
        uni = tmp / 'universal'
        (uni / 'practices').mkdir(parents=True)
        (uni / 'precedent-source.json').write_text(json.dumps(
            {'name': 'precedent', 'level': 'universal'}), encoding='utf-8')
        (uni / 'reply_check.json').write_text(json.dumps([
            {'practice': 'p', 'id': 'zz-rule',
             'require_one_of': ['ZZ-OK']}]), encoding='utf-8')
        st = tmp / 'a-set'
        (st / 'practices').mkdir(parents=True)
        (st / 'precedent-source.json').write_text(json.dumps(
            {'name': 'fixture-set', 'level': 'shared'}), encoding='utf-8')
        (st / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent',
             'path': '../universal'}]}), encoding='utf-8')
        # The set states only its id and examples: the predicate is
        # universal's, so tested alone it refuses nothing.
        examples = [{'reply': 'done.', 'refused': True},
                    {'reply': 'done. ZZ-OK', 'refused': False}]
        (st / 'reply_check.json').write_text(json.dumps([
            {'practice': 'p', 'id': 'zz-rule', 'inherits': True,
             '_examples': examples}]), encoding='utf-8')
        got = pc._reply_example_problems(st)
        cases.append(('an inheriting requirement answers its examples with '
                      'the predicate it inherits', got == ([], []), str(got)))
        # Control: without "inherits" the same requirement replaces
        # universal's outright, has no predicate, and its refused example
        # goes through -- the check still reports that.
        (st / 'reply_check.json').write_text(json.dumps([
            {'practice': 'p', 'id': 'zz-rule', '_examples': examples}]),
            encoding='utf-8')
        got = pc._reply_example_problems(st)
        cases.append(('control: one that does not inherit is tested alone, '
                      'and its wrong example is reported',
                      isinstance(got, tuple) and any(
                          'lets through' in p for _i, p in got[0]), str(got)))
    bad = [(n, x) for n, ok, x in cases if not ok]
    check(f'a reply rule\'s examples are tested with what it inherits '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {x}' for n, x in bad))


def check_suggested_links_keep_a_dotfiles_leading_dot():
    """`lstrip('./')` takes a character SET, not a prefix.

    So it eats every leading `.` and `/` it finds, and
    `../.claude/hooks/commit-identity-push-gate.sh` comes back as
    `claude/hooks/...`. The URL precedent_check.py then hands the author to
    paste 404s -- silently, because a suggested fix is never fetched by the
    thing suggesting it.

    It shipped TWICE. Found and fixed inline in the declined-adapters reader
    on 2026-09-21; the identical expression survived in the travel check's
    suggested-fix line until a session vendoring a `.claude/hooks/` push gate
    into the individual source was handed the mangled URL and reported it.
    Both sites now call one helper, and this asserts the helper's behaviour
    directly rather than inferring it from a check that happens to pass
    (practice: control-asserts-which-failure).

    The dotfile cases are the ones that bite: every harness adapter this repo
    ships lives under a dot directory, so the paths most likely to be
    suggested are exactly the paths the old expression destroyed."""
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location('_pc_prefix',
                                        ROOT / 'tools' / 'precedent_check.py')
    try:
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        strip = mod._strip_relative_prefix
    except Exception as exc:                     # noqa: BLE001
        return (False, '', f'precedent_check.py would not import: {exc}')

    cases = [
        ('../.claude/hooks/x.sh', '.claude/hooks/x.sh'),
        ('./.claude/settings.json', '.claude/settings.json'),
        ('../../.github/workflows/w.yml', '.github/workflows/w.yml'),
        ('.claude/settings.json', '.claude/settings.json'),
        ('../tools/precedent_check.py', 'tools/precedent_check.py'),
        ('tools/precedent_check.py', 'tools/precedent_check.py'),
        ('./practices/go-update.md', 'practices/go-update.md'),
    ]
    bad = []
    for given, want in cases:
        got = strip(given)
        if got != want:
            bad.append((given, f'{got!r} not {want!r}'))

    # And the mistake itself, named, so a later edit that reaches for the
    # short spelling fails here rather than in a pasted URL.
    if '../.claude/hooks/x.sh'.lstrip('./') == strip('../.claude/hooks/x.sh'):
        bad.append(('the helper still behaves like lstrip',
                    'a dotfile path loses its leading dot'))

    src = (ROOT / 'tools' / 'precedent_check.py').read_text(encoding='utf-8')
    for spelling in ('.lstrip("./")', ".lstrip('./')"):
        if spelling in src:
            bad.append((f'{spelling} is back in precedent_check.py',
                        'use _strip_relative_prefix'))

    return (not bad, f'{len(cases)} stated paths, both spellings refused',
            '; '.join(f'{n}: {d}' for n, d in bad))
def check_planted_case_rotation_never_narrows_silently():
    """The rotation that decides how much of the push gate runs.

    `check_precedent_check_fires` was 107.9s of a 211.5s suite -- 71 cases,
    each copying the whole tree twice and starting two interpreters. Morgan,
    2026-09-21 (strength: decided): build the 10% rotation. The risk of any
    such scheduler is that it quietly runs less than it claims, so the
    behaviour is asserted here directly rather than inferred from a fast
    suite (practice: control-asserts-which-failure).

    The four states that matter, and the two that must NEVER narrow:
    a forced full run, and any change to the check machinery itself.
    """
    cases = []
    slugs = _registry_slugs()
    if not slugs:
        return (False, '', 'the check registry could not be read at all, so '
                           'the selector cannot be exercised')

    saved = os.environ.get('PRECEDENT_HARNESS_ALL')
    try:
        os.environ['PRECEDENT_HARNESS_ALL'] = '1'
        sel, why = _selected_case_slugs(slugs, touched={'README.md'}, count=1)
        cases.append(('PRECEDENT_HARNESS_ALL=1 runs every case',
                      sel == set(slugs), f'{len(sel)}/{len(slugs)}: {why}'))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_HARNESS_ALL', None)
        else:
            os.environ['PRECEDENT_HARNESS_ALL'] = saved

    for touched, label in (({'tools/precedent_check.py'}, 'precedent_check.py'),
                           ({'tools/verify_harness.py'}, 'verify_harness.py'),
                           ({'tools/checks/anything.py'}, 'a tools/checks/ script')):
        sel, why = _selected_case_slugs(slugs, touched=touched, count=1,
                                        forced=False)
        cases.append((f'a change to {label} runs every case',
                      sel == set(slugs), f'{len(sel)}/{len(slugs)}: {why}'))

    # A practice file in the diff always runs ITS OWN case -- the whole
    # point: editing a rule without re-proving its check still fires is the
    # hole this function exists to close.
    probe = sorted(s for s in slugs if (ROOT / 'practices' / f'{s}.md').exists())
    if probe:
        one = probe[0]
        # count chosen so `one` is NOT in the rotating slice by luck.
        for count in range(HARNESS_ROTATION_BUCKETS):
            sel, _ = _selected_case_slugs(slugs, touched={f'practices/{one}.md'},
                                          count=count, forced=False)
            if one not in sel:
                cases.append((f'a touched practice always runs its own case '
                              f'({one}, bucket {count})', False, 'missing'))
                break
        else:
            cases.append(('a touched practice always runs its own case, in '
                          'every bucket', True, ''))

    # Every slug a later assertion reads back out of `planted[...]` is
    # pinned, in every bucket -- otherwise a skipped case leaves a KeyError
    # for unrelated code.
    pinned = _deep_assertion_slugs() & set(slugs)
    missing = []
    for count in range(HARNESS_ROTATION_BUCKETS):
        sel, _ = _selected_case_slugs(slugs, touched={'README.md'}, count=count,
                                        forced=False)
        missing += sorted(pinned - sel)
    cases.append((f'every deep-assertion slug is pinned in all '
                  f'{HARNESS_ROTATION_BUCKETS} buckets ({len(pinned)} of them)',
                  not missing, f'missing: {sorted(set(missing))}'))

    # Ten consecutive commits cover the whole set -- "probably" is not the
    # guarantee, and a rotation that left a check uncovered for longer than
    # it claims would be worse than no rotation at all.
    union = set()
    for count in range(HARNESS_ROTATION_BUCKETS):
        union |= _selected_case_slugs(slugs, touched={'README.md'}, count=count,
                                        forced=False)[0]
    uncovered = sorted(set(slugs) - union)
    cases.append((f'{HARNESS_ROTATION_BUCKETS} consecutive commits cover every '
                  f'case', not uncovered, f'never covered: {uncovered}'))

    # And it must actually narrow, or it is ceremony.
    sel, _ = _selected_case_slugs(slugs, touched={'README.md'}, count=0,
                                 forced=False)
    cases.append(('an ordinary docs change runs well under half the cases',
                  len(sel) * 2 < len(slugs), f'{len(sel)}/{len(slugs)}'))

    # NO BUCKET MAY SELECT NOTHING -- the 2026-09-20 failure, asked of this
    # rotation before it could happen rather than after. That day
    # precedent_check.py's rotation landed on a bucket covering nothing and
    # CI refused the run. Here the floor is structural (pinned slugs, and a
    # planted case cannot SKIP), but a floor nobody asserts is a floor that
    # erodes silently, so both the selector's fail-safe and the measured
    # minimum are checked.
    per_bucket = [len(_selected_case_slugs(slugs, touched={'README.md'},
                                           count=c, forced=False)[0])
                  for c in range(HARNESS_ROTATION_BUCKETS)]
    cases.append((f'no bucket selects zero cases (per-bucket: {per_bucket})',
                  all(n > 0 for n in per_bucket), ''))
    empty, why = _selected_case_slugs([], touched={'README.md'}, count=0,
                                     forced=False)
    cases.append(('an empty slice runs everything rather than nothing',
                  'empty' in why or empty == set(), why))

    # One case by name (PRECEDENT_HARNESS_CASES, 2026-10-17), with the
    # pinned ones the later assertions read back.
    loose = sorted(set(slugs) - (_deep_assertion_slugs() or set()))
    if loose:
        one = loose[0]
        try:
            sel, why = _selected_case_slugs(slugs, touched={'README.md'},
                                            count=0, forced=False, named=one)
        except TypeError as e:
            sel, why = set(), f'no selector by name: {e}'
        cases.append((f'a case named alone runs ({one}), with the pinned ones '
                      f'and nothing else',
                      one in sel and sel == {one} | (pinned & set(slugs)), why))
        try:
            sel, why = _selected_case_slugs(slugs, touched={'README.md'},
                                            count=0, forced=False,
                                            named=f'{one},no-such-case')
        except TypeError as e:
            sel, why = set(), str(e)
        cases.append(('a name that is no case is said, not silently dropped',
                      one in sel and 'no-such-case' in why, why))
        try:
            sel, why = _selected_case_slugs(slugs, touched={'README.md'},
                                            count=0, forced=False,
                                            named='no-such-case')
        except TypeError as e:
            sel, why = set(), str(e)
        cases.append(('naming no real case runs every case, never none',
                      sel == set(slugs), why))

    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def _conflict_marker_hits(named_texts):
    return [(name, text.count('\n', 0, m.start()) + 1)
            for name, text in named_texts for m in _CONFLICT_MARKER.finditer(text)]


def check_no_conflict_markers_in_shipped_tools():
    """No file that runs ships with a merge conflict marker in it (practice
    vendor-update-runbook: a port between a vendored copy and its upstream is
    a three-way merge, and the result is read for leftover markers before it
    is used). The origin: a port that went through a merge with the wrong
    base produced a tool holding conflict markers, and only a later read
    caught it. Scans the tracked scripts and configuration under tools/,
    templates/ and .claude/; documents are left alone, since a document may
    show a marker on purpose."""
    bad, cases = [], []
    lt, gt = '<' * 7, '>' * 7
    planted = [('x.py', f'a = 1\n{lt} HEAD\nb = 2\n=======\nb = 3\n{gt} other\n')]
    if len(_conflict_marker_hits(planted)) != 2:
        bad.append('a planted two-sided conflict was not found on both lines')
    cases.append('a planted conflict is found')
    quiet = [('y.md', 'Title\n=======\n'), ('z.py', "s = '" + lt + "'\n" + '<' * 6 + ' x\n')]
    if _conflict_marker_hits(quiet):
        bad.append('a heading underline or a marker inside a string counted as a conflict')
    cases.append('a heading underline and an in-string marker are quiet')
    r = subprocess.run(['git', '-C', str(ROOT), 'ls-files', 'tools', 'templates', '.claude'],
                       capture_output=True, text=True)
    files = [f for f in r.stdout.splitlines()
             if f.endswith(('.py', '.sh', '.json', '.yml', '.yaml', '.toml'))]
    texts = []
    for f in files:
        try:
            texts.append((f, (ROOT / f).read_text(encoding='utf-8')))
        except (OSError, UnicodeDecodeError):
            continue
    hits = _conflict_marker_hits(texts)
    if hits:
        bad.append('conflict marker in ' + ', '.join(f'{n}:{ln}' for n, ln in hits[:5]))
    return (not bad, f'{len(cases)} stated cases, {len(texts)} files scanned', '; '.join(bad))


def check_checks_read_what_their_rules_name():
    """Seven checks, each read against its own practice's Rule by the
    2026-09-28 very deep check, and each found judging something narrower
    or wider than the Rule says. One stated case per behaviour, run
    in-process against a throwaway tree the case owns
    (fixture-owns-its-state), so none of them pays for a copy of this repo.

    - open-item-disposition read only `**Disposition:**` prose lines, so
      an open todo/todo-*.md item's frontmatter `disposition: raise` passed.
    - two-check-levels demanded the literal bold `**light check**` pair,
      though the Rule puts the names in GLOSSARY.md and allows any pair.
    - technical-describes-people is tree-scope but read ctx.changed, which
      --full-sweep leaves empty on a clean tree: it passed having read
      nothing.
    - no-version-suffix refused state words anywhere (whats-new.md,
      deep_copy.py), where the practice is about a fork beside its original.
    - environment-gotchas never looked at the instructions file once a repo
      had migrated to gotchas/, so an index could regrow there.
    - no-hardcoded-git-identity returned clean on a settings.json it could
      not parse.
    - doc_sync's orphan-sentinel scan walked gitignored trees, so a
      checkout holding agent worktrees under .claude/worktrees/ reported
      every worktree's generated block as an unregistered orphan.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    import doc_sync as ds

    cases = []

    def tree(files, git_init=False):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rule-reads-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        if git_init:
            subprocess.run(['git', '-C', str(d), 'init', '-q'],
                           capture_output=True)
            subprocess.run(['git', '-C', str(d), 'add', '-A'],
                           capture_output=True)
        return d

    def judge(d, fn, ctx=None):
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in fn(ctx if ctx is not None
                                                 else pc.Ctx(paths=['x'])))
        except pc.NotApplicable as e:
            return f'NOT APPLICABLE: {e}'
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    # --- open-item-disposition: frontmatter of the per-item format --------
    def item(status, disposition):
        return (f'---\nslug: todo-x\nstatus:            {status}\n'
                f'disposition:       {disposition}\nnoted: 2026-01-01\n---\n'
                f'## What\n\nA planted item.\n')
    out = judge(tree({'todo/todo-2026-01-01-x.md': item('open', 'raise')}),
                pc._open_item_disposition)
    cases.append(('open-item-disposition: an OPEN item whose frontmatter '
                  'disposition is not a disposition is reported',
                  "'raise'" in out and 'todo/todo-2026-01-01-x.md:4' in out,
                  out))
    out = judge(tree({'todo/todo-2026-01-01-a.md': item('open', 'ask'),
                      'todo/todo-2026-01-01-b.md': item('open', 'null'),
                      'todo/todo-2026-01-01-c.md': item('done', 'done')}),
                pc._open_item_disposition)
    cases.append(('open-item-disposition: ask, null, and a CLOSED item\'s '
                  'leftover value all pass', out == '', out))

    # --- open-item-disposition: the two copies of a park (2026-10-05) ----
    # The frontmatter is what every reader acts on; the body line records
    # who said "Drop it" and when. Each state is planted, the quiet one too
    # (practice: checks-plant-their-state).
    def with_body(status, disposition, line):
        return item(status, disposition).replace(
            'A planted item.\n', f'A planted item.\n\n{line}\n')
    out = judge(tree({'todo/todo-2026-01-01-x.md': item('done', 'parked')}),
                pc._open_item_disposition_copies)
    cases.append(('open-item-disposition-copies: a park with no dated, named body '
                  'line is reported, even on a closed item',
                  'no "**Disposition:** parked (YYYY-MM-DD, who)"' in out, out))
    out = judge(tree({'todo/todo-2026-01-01-x.md': with_body(
                    'open', 'ask', '**Disposition:** parked (2026-01-02, Morgan)')}),
                pc._open_item_disposition_copies)
    cases.append(('open-item-disposition-copies: a body that says parked over a '
                  'frontmatter that still says ask is reported as still raised',
                  'still raised after it was dropped' in out, out))
    out = judge(tree({'todo/todo-2026-01-01-x.md': with_body(
                    'open', 'parked',
                    '**Disposition:** parked (2026-01-02, who not recorded)')}),
                pc._open_item_disposition_copies)
    out = judge(tree({'todo/todo-2026-01-01-x.md': item('open', 'parked')}),
                pc._open_item_disposition)
    cases.append(('open-item-disposition: an old park with no body line is '
                  'never refused by the hard check -- only the copies check '
                  'warns about it (practice: format-rules-grandfather)',
                  out == '', out))
    cases.append(('open-item-disposition-copies: a park recorded in both places, '
                  '"who not recorded" included, passes', out == '', out))

    # --- advisory-checks-declare-their-term (2026-10-05) -----------------
    # A planted registry and a fixed date: the verdict depends on nothing
    # this machine holds (practice: fixture-owns-its-state).
    reg = {
        'no-term': dict(advisory=True),
        'permanent': dict(advisory=True, advisory_term={
            'term': 'permanent', 'why': 'a person must judge'}),
        'temp-future': dict(advisory=True, advisory_term={
            'term': 'temporary', 'waiting_for': 'the sets', 'owner': 'Morgan',
            'revisit': '2026-12-01'}),
        'temp-past': dict(advisory=True, advisory_term={
            'term': 'temporary', 'waiting_for': 'the sets', 'owner': 'Morgan',
            'revisit': '2026-10-01'}),
        'hard-with-term': dict(advisory=False, advisory_term={
            'term': 'permanent', 'why': 'x'}),
        'hard': dict(advisory=False),
    }
    found = {f.where.split(':')[-1]: f.detail
             for f in pc._advisory_term_findings(reg, '2026-10-05')}
    cases.append(('advisory-checks-declare-their-term: a warning-only check '
                  'with no term, a temporary one past its date, and a hard '
                  'check carrying a leftover term are each reported',
                  'permanent or temporary' in found.get('no-term', '')
                  and 'Waiting on: the sets. Owner: Morgan' in found.get('temp-past', '')
                  and 'not advisory' in found.get('hard-with-term', ''),
                  repr(found)))
    cases.append(('advisory-checks-declare-their-term: a permanent term, a '
                  'temporary one before its date, and a plain hard check '
                  'are quiet',
                  not ({'permanent', 'temp-future', 'hard'} & set(found)),
                  repr(found)))

    # --- frontmatter_yaml --fix-staged: the commit hook's tidy (2026-10-05)
    # One throwaway repository per case, its own git identity, every state
    # planted: fixed, partly staged, unknown field, not a source.
    import frontmatter_yaml as fyaml
    swapped = ('---\nslug: s\ntier: on-demand\ntitle: T\n---\n## Rule\nx\n')
    def staged_repo(files, source=True):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-fix-staged-'))
        subprocess.run(['git', '-C', str(d), 'init', '-q'], capture_output=True)
        for k, v in (('user.name', 'Fixture'), ('user.email', 'f@example.com')):
            subprocess.run(['git', '-C', str(d), 'config', k, v],
                           capture_output=True)
        if source:
            (d / 'precedent-source.json').write_text('{}\n', encoding='utf-8')
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
            subprocess.run(['git', '-C', str(d), 'add', rel], capture_output=True)
        return d
    d = staged_repo({'practices/a.md': swapped,
                     'practices/b.md': swapped,
                     'practices/c.md': swapped.replace('title: T\n',
                                                       'title: T\nnot_a_field: 1\n')})
    (d / 'practices/b.md').write_text(swapped + 'unstaged edit\n', encoding='utf-8')
    fixed = fyaml.fix_staged(d)
    a_now = (d / 'practices/a.md').read_text(encoding='utf-8')
    a_staged = subprocess.run(['git', '-C', str(d), 'show', ':practices/a.md'],
                              capture_output=True, text=True).stdout
    b_staged = subprocess.run(['git', '-C', str(d), 'show', ':practices/b.md'],
                              capture_output=True, text=True).stdout
    c_now = (d / 'practices/c.md').read_text(encoding='utf-8')
    shutil.rmtree(d, ignore_errors=True)
    cases.append(('frontmatter_yaml --fix-staged: a fully staged practice is '
                  'reordered and re-staged; a partly staged one and one with '
                  'an unknown field are left exactly as they were',
                  fixed == ['practices/a.md']
                  and a_now.index('title:') < a_now.index('tier:')
                  and a_staged == a_now
                  and b_staged == swapped and c_now.startswith(
                      '---\nslug: s\ntier: on-demand\ntitle: T\nnot_a_field'),
                  repr(fixed)))
    d = staged_repo({'practices/a.md': swapped}, source=False)
    fixed = fyaml.fix_staged(d)
    untouched = (d / 'practices/a.md').read_text(encoding='utf-8') == swapped
    shutil.rmtree(d, ignore_errors=True)
    cases.append(('frontmatter_yaml --fix-staged: a repository that does not '
                  'declare itself a practice source is never touched',
                  fixed == [] and untouched, repr(fixed)))

    # --- todo_disposition.py: the writer the check backs up ---------------
    import todo_disposition as tdisp
    parked, _notes = tdisp.park(item('open', 'ask'), '2026-01-02', 'Morgan',
                                conflict='some-practice')
    again, notes2 = tdisp.park(parked, '2026-01-03', 'Alex',
                               conflict='some-practice')
    cases.append(('todo_disposition: park writes the frontmatter and a dated, '
                  'named body line, and the result passes the check',
                  tdisp.verify(parked) == []
                  and '**Disposition:** parked (2026-01-02, Morgan)' in parked
                  and judge(tree({'todo/todo-2026-01-01-x.md': parked}),
                            pc._open_item_disposition) == ''
                  and judge(tree({'todo/todo-2026-01-01-x.md': parked}),
                            pc._open_item_disposition_copies) == '',
                  parked))
    cases.append(('todo_disposition: a second park changes nothing, and a '
                  'conflict already raised is never raised again',
                  again == parked
                  and any('do not ask again' in n for n in notes2),
                  '; '.join(notes2)))

    # --- practice_standing.py: the three words and who may set them ------
    import practice_standing as pst
    auth = ({'@themorgan', '@alex137'}, 'precedent.json')
    def _probs(**fm):
        return pst.problems(fm, '.', _authority=auth)
    cases.append(('practice_standing: no label means Protocol, shown with no '
                  'note anywhere',
                  pst.standing({}) == 'protocol' and pst.label({}) == ''
                  and pst.heading_note({}) == '' and pst.clause_prefix({}) == ''
                  and pst.inline_note({}) == '' and _probs() == [], ''))
    cases.append(('practice_standing: a Preference is marked with what it '
                  'allows, in every channel\'s form',
                  pst.clause_prefix({'standing': 'preference'}) == 'Preference: '
                  and 'reason' in pst.heading_note({'standing': '"preference"'})
                  and pst.inline_note({'standing': 'Principle'}).startswith('*Principle:'), ''))
    _cases_ps = [
        ('an unknown word', dict(standing='rule', standing_by='themorgan'), 'not one of'),
        ('no standing_by', dict(standing='preference'), 'names nobody'),
        ('standing_by alone', dict(standing_by='themorgan'), 'carries no'),
        ('a Principle from outside the registry',
         dict(standing='principle', standing_by='intern'), 'not named in'),
    ]
    for what, fm, needle in _cases_ps:
        got = _probs(**fm)
        cases.append((f'practice_standing: {what} is refused, saying so',
                      len(got) == 1 and needle in got[0], repr(got)))
    cases.append(('practice_standing: a Principle set by a maintainer ("@" '
                  'optional) and anyone\'s Preference both pass',
                  _probs(standing='principle', standing_by='@alex137') == []
                  and _probs(standing='principle', standing_by='themorgan') == []
                  and _probs(standing='preference', standing_by='intern') == [], ''))

    # --- two-check-levels: the pair comes from GLOSSARY.md ----------------
    gloss = ('| Term | Defined in |\n|---|---|\n'
             '| quick pass | [two-check-levels](practices/two-check-levels.md) |\n'
             '| full audit | [two-check-levels](practices/two-check-levels.md) |\n')
    out = judge(tree({'GLOSSARY.md': gloss,
                      'AGENTS.md': 'Run the quick pass before a commit and '
                                   'the full audit before a push.\n'}),
                pc._two_check_levels)
    cases.append(('two-check-levels: a repo-chosen pair from GLOSSARY.md, '
                  'named in plain text, passes', out == '', out))
    out = judge(tree({'GLOSSARY.md': gloss,
                      'AGENTS.md': 'Run the quick pass before a commit.\n'}),
                pc._two_check_levels)
    cases.append(('two-check-levels: the instructions file missing one of '
                  'the glossary\'s pair is reported, naming it',
                  "'full audit'" in out, out))

    # --- technical-describes-people: the whole tree, not the diff ---------
    d = tree({'nontechnical-guide/a.md': '# x\n'}, git_init=True)
    ctx_empty = type('Ctx', (), {'changed': [], 'root': d})()
    out = judge(d, pc._technical_describes_people, ctx_empty)
    cases.append(('technical-describes-people: a skill-labelled path in the '
                  'tree is reported even when nothing changed',
                  'nontechnical-guide/a.md' in out, out))

    # --- no-version-suffix: a state word only when it forks an original ---
    def added(files, names):
        d = tree(files)
        ctx = type('Ctx', (), {'root': d,
                               'added_files': lambda self: list(names)})()
        return judge(d, pc._no_version_suffix, ctx)
    out = added({'whats-new.md': 'x\n', 'deep_copy.py': 'x\n',
                 'draft.md': 'x\n'},
                ['whats-new.md', 'deep_copy.py', 'draft.md'])
    cases.append(('no-version-suffix: a state word with no original beside '
                  'it is an ordinary name and passes', out == '', out))
    out = added({'report.md': 'x\n', 'report-final.md': 'x\n'},
                ['report-final.md'])
    cases.append(('no-version-suffix: report-final.md beside report.md is '
                  'reported as a fork', 'report-final.md' in out
                  and 'report.md' in out, out))
    out = added({'findings-v2.md': 'x\n'}, ['findings-v2.md'])
    cases.append(('no-version-suffix: a version token alone is still '
                  'reported', 'findings-v2.md' in out, out))
    out = added({'notes/note-to-alex-2026-09-22.md': 'x\n',
                 'notes/note-to-alex-2026-10-07.md': 'x\n'},
                ['notes/note-to-alex-2026-10-07.md'])
    cases.append(('no-version-suffix: a dated record is not a version '
                  '(2026-10-07)', out == '', out))
    out = added({'report.md': 'x\n', 'report-2026-10-07.md': 'x\n'},
                ['report-2026-10-07.md'])
    cases.append(('no-version-suffix: a dated copy beside its undated '
                  'original is still a fork', 'report-2026-10-07.md' in out
                  and 'report.md' in out, out))

    # --- environment-gotchas: no index once the catalogue has migrated ----
    story = ('## Symptom\n\nA tool fails.\n\n## Story\n\nIt failed on a real '
             'day in a way that read as something else entirely, and a '
             'session spent an hour on the wrong hypothesis before finding '
             'the cause. The remedy is to check the exit code instead.\n\n'
             '## Fix\n\nCheck it.\n')
    g = {f'gotchas/gotcha-2026-01-0{i}-t{i}.md':
         f'---\nslug: gotcha-2026-01-0{i}-t{i}\nstatus: live\n---\n' + story
         for i in (1, 2)}
    head = '# x\n\n## Environment gotchas -- do NOT rediscover these\n\n'
    prose = (head + 'Grep gotchas/ first. One trap bit us here, '
             '[gotcha-2026-01-01](gotchas/gotcha-2026-01-01-t1.md), and '
             'another one too ([t2](gotchas/gotcha-2026-01-02-t2.md)).\n')
    out = judge(tree({**g, 'AGENTS.md': prose}), pc._environment_gotchas)
    cases.append(('environment-gotchas: prose citing specific traps is a '
                  'pointer, not an index, and passes', out == '', out))
    index = (head + '- [t1](gotchas/gotcha-2026-01-01-t1.md) a tool fails\n'
             '- [t2](gotchas/gotcha-2026-01-02-t2.md) a tool fails\n')
    out = judge(tree({**g, 'AGENTS.md': index}), pc._environment_gotchas)
    cases.append(('environment-gotchas: a one-line-per-trap index in the '
                  'instructions file is reported', 'AGENTS.md:5' in out
                  and 'index' in out, out))

    # --- no-hardcoded-git-identity: unparseable is not clean --------------
    out = judge(tree({'.claude/settings.json': '{"env": {,}'}),
                pc._no_hardcoded_git_identity)
    cases.append(('no-hardcoded-git-identity: a settings.json that does not '
                  'parse is reported', '.claude/settings.json' in out
                  and 'JSON' in out, out))

    # --- doc_sync: the orphan scan walks only what git would commit ------
    d = tree({'.gitignore': '.claude/worktrees/\n',
              'doc.md': '<!--gen:mine-->\nx\n<!--/gen:mine-->\n',
              '.claude/worktrees/agent-x/doc.md':
                  '<!--gen:theirs-->\nx\n<!--/gen:theirs-->\n'},
             git_init=True)
    old = ds.ROOT
    ds.ROOT = d
    try:
        found = ds.sentinel_blocks()
    finally:
        ds.ROOT = old
        shutil.rmtree(d, ignore_errors=True)
    cases.append(('doc_sync: a generated block inside a gitignored tree '
                  '(.claude/worktrees/) is not scanned; the tracked one is',
                  found == {('doc.md', 'mine')}, str(sorted(found))))

    bad = [(n, det) for n, ok, det in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_routing_reason_lives_in_the_practice():
    """precedent_check.py's routing-reason check, both states planted.

    Replaced check_routing_scope on 2026-09-29. That test compared
    practices/*.md with a second, hand-kept list in tools/routing_scope.json
    and failed when a practice had no entry -- which is how five new
    practices were caught, at staging, and why a deleted practice's entry
    could outlive it unnoticed. The reason now lives in the practice's own
    applies_to_why, so there is no second list to fall out of step (practice:
    upstream-fix), and the check reads one file at a time, so the quick
    check runs it. The list is gone from routing_scope.json; asserted here so it
    does not grow back.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def practice(slug, why=None, tier='on-demand', status='active'):
        lines = [f'slug:        {slug}', f'tier:        {tier}',
                 'applies_to:  ["**"]']
        if why is not None:
            lines.append(f'applies_to_why: "{why}"')
        lines.append(f'status:      {status}')
        return '---\n' + '\n'.join(lines) + '\n---\n## Rule\nA rule.\n'

    def judge(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-routing-reason-'))
        for rel, text in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in pc._routing_reason(pc.Ctx(paths=['x'])))
        except pc.NotApplicable as e:
            return f'NOT APPLICABLE: {e}'
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    engine = {'tools/verify_harness.py': '# the engine origin\n'}
    cases = []
    out = judge({**engine, 'practices/a.md': practice('a'),
                 'practices/b.md': practice('b', why='A moment; the reply gate.')})
    cases.append(('an on-demand practice with no applies_to_why is refused, '
                  'by file, with the fix named',
                  'practices/a.md' in out and 'has no applies_to_why' in out
                  and 'practices/b.md' not in out, out))
    out = judge({**engine, 'practices/b.md': practice('b', why='Named path.'),
                 'practices/r.md': practice('r', tier='resident'),
                 'practices/old.md': practice('old', status='retired')})
    cases.append(('with a reason, and for resident or retired practices, it '
                  'stays quiet', out == '', out))
    out = judge({'practices/a.md': practice('a')})
    cases.append(('outside the engine origin it does not apply (the field '
                  'is optional in a set or consumer)',
                  out.startswith('NOT APPLICABLE'), out))
    scope = json.loads((ROOT / 'tools' / 'routing_scope.json')
                       .read_text(encoding='utf-8'))
    cases.append(('tools/routing_scope.json carries no per-practice list',
                  'practices' not in scope, sorted(scope)))
    missing = [f.name for f in sorted((ROOT / 'practices').glob('*.md'))
               if re.search(r'^tier:\s*on-demand', f.read_text(encoding='utf-8'), re.M)
               and re.search(r'^status:\s*active', f.read_text(encoding='utf-8'), re.M)
               and not re.search(r'^applies_to_why:\s*\S', f.read_text(encoding='utf-8'), re.M)]
    cases.append(('every active on-demand practice here has applies_to_why',
                  not missing, missing[:6]))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('the routing reason lives in each practice (applies_to_why), and '
          'the check for it refuses a missing one and stays quiet otherwise',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_new_exemption_needs_a_root_fix():
    """precedent_check.py's upstream-fix check (point 6: a new exemption is
    a sign the root fix has not been made), with every state planted in a
    throwaway repository whose base branch it owns: an entry already on the
    base branch passes bare; a new entry without root_fix is refused, naming
    the list and the entry; a new entry with one passes; and adding a
    root_fix to an old entry does not make it new.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def cfg(entries):
        return json.dumps({'base_branch': 'staging',
                           'filename_separator_exempt': entries}, indent=1) + '\n'
    old_entry = {'path': 'templates', 'ext': '.template', 'reason': 'named by GitHub'}

    def judge(now_entries):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-root-fix-'))
        g = lambda *a: subprocess.run(['git', '-C', str(d), *a],
                                      capture_output=True, text=True)
        g('init', '-q')
        g('config', 'user.email', 'fixture@example.invalid')
        g('config', 'user.name', 'fixture')
        (d / 'precedent.json').write_text(cfg([old_entry]), encoding='utf-8')
        g('add', '-A')
        g('commit', '-q', '-m', 'base')
        g('update-ref', 'refs/remotes/origin/staging', 'HEAD')
        (d / 'precedent.json').write_text(cfg(now_entries), encoding='utf-8')
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in
                             pc._exemption_names_its_root_fix(pc.Ctx(paths=['x'])))
        except pc.NotApplicable as e:
            return f'NOT APPLICABLE: {e}'
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    new_bare = {'path': '.', 'ext': '.json', 'reason': 'named by tools'}
    cases = []
    out = judge([old_entry])
    cases.append(('an entry already on the base branch passes without root_fix',
                  out == '', out))
    out = judge([old_entry, new_bare])
    cases.append(('a new entry without root_fix is refused, naming the list '
                  'and the entry', "filename_separator_exempt gains an entry "
                  "for '.' with no root_fix" in out, out))
    out = judge([old_entry, {**new_bare, 'root_fix': 'the check cannot see '
                             'which tool reads the file; handed off'}])
    cases.append(('a new entry that says its root_fix passes', out == '', out))
    out = judge([{**old_entry, 'root_fix': 'added later'}])
    cases.append(('a root_fix added to an old entry does not make it new',
                  out == '', out))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('a new exemption entry must say its root_fix; old ones are left '
          'alone (upstream-fix, point 6)',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_practice_file_shape_judges_one_file_at_a_time():
    """precedent_check.py's practice-file-shape, which took over seven
    verify_harness.py checks on 2026-09-29 so the quick check runs them on
    the files a change touches. Each rule planted once in a throwaway catalogue,
    asserted by its own words, with a clean practice beside it that must
    stay quiet (practice: control-asserts-which-failure).
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def practice(slug, rule='Do the thing.', clause='do the thing, always',
                 checked_by='null', tier='on-demand', extra=''):
        return (f'---\nslug:        {slug}\ntier:        {tier}\n'
                f'applies_to:  ["**"]\napplies_to_why: "planted"\n'
                f'index_clause: "{clause}"\nchecked_by:  {checked_by}\n'
                f'status:      active\n---\n## Rule\n{rule}\n{extra}'
                # Every practice carries these since 2026-10-11, when the
                # check took over the mandatory-sections rule; without them
                # the well-formed control reads as malformed.
                f'\n## Why\nWhy.\n\n## Story\nStory.\n\n## Install\nInstall.\n')

    def judge(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-shape-'))
        for rel, text in {'tools/verify_harness.py': '# origin\n', **files}.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in pc._practice_file_shape(pc.Ctx(paths=['x'])))
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    clean = {'practices/ok.md': practice('ok')}
    cases = [('a well-formed practice is quiet', judge(clean) == '', judge(clean))]
    planted = [
        ('slug not the filename', {'practices/a.md': practice('b')}, "is not the filename 'a'"),
        ('checked_by names a missing script',
         {'practices/a.md': practice('a', checked_by='tools/gone.py')}, "'tools/gone.py', which does not exist"),
        ('a practice cited by number',
         {'practices/a.md': practice('a', rule='As practice 12 says, do it.')}, 'cites "practice 12" by number'),
        ('a slug link to no practice',
         {'practices/a.md': practice('a', rule='See [nope](nope.md).')}, 'links nope.md, which is not a practice'),
        ('a link to another repository',
         {'practices/a.md': practice('a', rule='See https://github.com/someone/private-set.')}, 'links someone/private-set'),
        ('a Rule ending on a lead-in',
         {'practices/a.md': practice('a', rule='Three rules:')}, '## Rule ends on a colon'),
        ('an index line that is a sentence',
         {'practices/a.md': practice('a', clause='Do the thing always')}, 'reads as a sentence'),
        ('an index line over the limit',
         {'practices/a.md': practice('a', clause='x' * 90)}, 'over 80'),
    ]
    for name, files, words in planted:
        out = judge({**clean, **files})
        cases.append((f'{name} is refused, naming the file',
                      words in out and 'practices/a.md' in out
                      and 'practices/ok.md' not in out, out))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('practice-file-shape refuses each malformed file by name and stays '
          'quiet on a good one', not bad,
          '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_a_changed_glob_needs_its_reason_looked_at():
    """routing-reason's second rule: a practice whose applies_to changed
    since the base branch, while its applies_to_why stayed word for word the
    same, is refused, by file; changing the reason with it passes, and so
    does a practice new since the base. The fixture owns its base branch.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def practice(globs, why):
        return ('---\nslug:        x\ntier:        on-demand\n'
                f'applies_to:  {globs}\napplies_to_why: "{why}"\n'
                'index_clause: "do x"\nstatus:      active\n---\n## Rule\nDo x.\n')

    def judge(now_text, new_file=False):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-glob-why-'))
        g = lambda *a: subprocess.run(['git', '-C', str(d), *a],
                                      capture_output=True, text=True)
        g('init', '-q')
        g('config', 'user.email', 'fixture@example.invalid')
        g('config', 'user.name', 'fixture')
        (d / 'tools').mkdir()
        (d / 'tools' / 'verify_harness.py').write_text('# origin\n', encoding='utf-8')
        (d / 'practices').mkdir()
        if not new_file:
            (d / 'practices' / 'x.md').write_text(
                practice('["**"]', 'A moment, not a place.'), encoding='utf-8')
        (d / 'precedent.json').write_text('{"base_branch": "staging"}\n', encoding='utf-8')
        g('add', '-A')
        g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/staging', 'HEAD')
        (d / 'practices' / 'x.md').write_text(now_text, encoding='utf-8')
        old = pc.ROOT
        pc.ROOT = d
        try:
            return '; '.join(str(f) for f in pc._routing_reason(pc.Ctx(paths=['x'])))
        finally:
            pc.ROOT = old
            shutil.rmtree(d, ignore_errors=True)

    cases = []
    out = judge(practice('["docs/**"]', 'A moment, not a place.'))
    cases.append(('the glob changed and the reason did not: refused, by file',
                  'practices/x.md' in out and 'applies_to_why did not' in out, out))
    out = judge(practice('["docs/**"]', 'Only documents carry the occasion.'))
    cases.append(('the glob and the reason changed together: quiet', out == '', out))
    out = judge(practice('["**"]', 'A moment, not a place.'))
    cases.append(('nothing changed: quiet', out == '', out))
    out = judge(practice('["docs/**"]', 'A moment, not a place.'), new_file=True)
    cases.append(('a practice new since the base: quiet', out == '', out))
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('a changed applies_to needs its applies_to_why looked at again',
          not bad, '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_parallel_artifact_ledger_fires():
    """precedent_check.py's parallel-artifact-ledger check (added 2026-09-05),
    stated cases against a scratch git repo -- checkable-gets-checked applied
    to the check the audit-judgment eval found missing (templates/harness/
    LEDGER.md existed with no audit backing its own closing claim that "any
    marked date without a complete ledger row fails").
    """
    import importlib.util, shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ledgercheck-'))
    try:
        member = tmp / 'templates' / 'harness' / 'claude-code'
        member.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q'], cwd=tmp, check=True)
        subprocess.run(['git', 'config', 'user.email', 'harness@example.com'], cwd=tmp, check=True)
        subprocess.run(['git', 'config', 'user.name', 'harness'], cwd=tmp, check=True)
        (tmp / 'root.txt').write_text('root\n', encoding='utf-8')
        subprocess.run(['git', 'add', '-A'], cwd=tmp, check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'root'], cwd=tmp, check=True)
        # The base this branch is judged against: the check reads this
        # branch's commits, never the whole history (Morgan, 2026-10-08;
        # practice: checks-read-only-the-work).
        subprocess.run(['git', 'update-ref', 'refs/remotes/origin/main', 'HEAD'],
                       cwd=tmp, check=True)
        # Two more commits, because the check excludes two kinds of
        # inception: the repo's own root commit, and the commit that
        # FIRST created a given member directory (TODO.md's
        # closed and pruned from TODO.md, was the `ledger-root-commit-exemption` item --
        # a family coming into existence has nothing for its other
        # members to have transferred from). So the commit under test has
        # to be the third: a real later CHANGE to an existing member.
        (member / 'hooks.txt').write_text('v1\n', encoding='utf-8')
        subprocess.run(['git', 'add', '-A'], cwd=tmp, check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'create the family'], cwd=tmp, check=True)
        inception_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], cwd=tmp, capture_output=True, text=True
        ).stdout.strip()
        (member / 'hooks.txt').write_text('v2\n', encoding='utf-8')
        subprocess.run(['git', 'add', '-A'], cwd=tmp, check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'change a member'], cwd=tmp, check=True)
        member_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], cwd=tmp, capture_output=True, text=True
        ).stdout.strip()

        ledger_dir = tmp / 'templates' / 'harness'
        ledger_path = ledger_dir / 'LEDGER.md'

        spec = importlib.util.spec_from_file_location(
            '_pc_ledger', ROOT / 'tools' / 'precedent_check.py')
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        pc.ROOT = tmp
        pc._git = lambda *args, cwd=None: subprocess.run(
            ['git', *args], cwd=str(cwd or tmp), capture_output=True, text=True)
        fn = pc.CHECKS['parallel-artifact-ledger']['fn']

        # A real dated row, not a bare hash on a line of its own: the check
        # credits a commit only when it is named in a ROW's `Originating
        # change` cell, so a fixture writing the hash loose in the file was
        # passing on the presence half's old whole-file match and stopped
        # meaning anything the moment that half was keyed on the cell
        # (2026-09-11).
        def _row(commit_hash):
            return (f'| 2026-01-01 | [`{commit_hash[:7]}`]'
                    f'(https://example.invalid/{commit_hash}) — planted '
                    f'| applied | n/a | n/a |\n')

        no_ledger = fn(None)
        ledger_path.write_text('no commit hashes here\n', encoding='utf-8')
        unreferenced = fn(None)
        ledger_path.write_text(_row(member_commit), encoding='utf-8')
        referenced = fn(None)
        # The distinction both halves now share: a commit named only in
        # another row's PROSE is a citation, not that row's own change, so
        # it is not ledgered. Without this case the presence half can slide
        # back to matching the whole file and nothing fails.
        ledger_path.write_text(
            '| 2026-01-01 | [`0000000`](https://example.invalid/0000000) — '
            f'planted | applied, same reason as the `{member_commit[:7]}` '
            'row | n/a | n/a |\n', encoding='utf-8')
        cited_only = fn(None)
        # Once the change is on the base, a later run is not judged for it:
        # an empty ledger and nothing new on the branch is not a finding.
        ledger_path.write_text('no commit hashes here\n', encoding='utf-8')
        subprocess.run(['git', 'update-ref', 'refs/remotes/origin/main', member_commit],
                       cwd=tmp, check=True)
        already_on_base = fn(None)

        # A row is a verdict for every member or it is not one (2026-10-19:
        # the 2026-10-18 row stopped after its change cell, and a 2026-09-30
        # row carried an unescaped pipe in a code span).
        header = ('| Date | Originating change | claude-code | codex | '
                  'gemini-cli |\n|---|---|---|---|---|\n')
        ledger_path.write_text(header + _row('0000000'), encoding='utf-8')
        complete_row = fn(None)
        ledger_path.write_text(
            header + '| 2026-10-18 | this row\'s own commit — planted |\n',
            encoding='utf-8')
        half_row = fn(None)
        ledger_path.write_text(
            header + '| 2026-09-30 | a `|` in code | applied | n/a | n/a |\n',
            encoding='utf-8')
        loose_pipe = fn(None)
        ledger_path.write_text(
            header + '| 2026-09-30 | a `\\|` in code | applied | n/a | n/a |\n',
            encoding='utf-8')
        escaped_pipe = fn(None)
        ledger_path.write_text(
            header + '| 2026-09-30 | planted | applied |  | n/a |\n',
            encoding='utf-8')
        empty_cell = fn(None)

        # A ledger naming ONLY the later change: the inception commit must
        # not be demanded. Before this exemption, f2078d6 -- the commit
        # that created all three real harness adapters, five weeks before
        # the ledger file existed -- failed every pull request's CI until
        # somebody hand-wrote a row saying "no transfer verdict
        # applicable".
        inception_exempt = [f for f in referenced
                            if inception_commit[:7] in str(f)]

        cases = [
            ("missing LEDGER.md is a finding", len(no_ledger) == 1),
            ("a member directory's own inception commit needs no row",
             not inception_exempt),
            ("a ledger with no reference to the commit is a finding",
             len(unreferenced) == 1),
            ("a ledger row naming the commit in its change cell clears "
             "the finding", referenced == []),
            ("a commit named only in another row's prose is NOT ledgered",
             len(cited_only) == 1),
            ("a change already on the base is not judged again -- the check "
             "never walks the whole history", already_on_base == []),
            ("a complete row under the header is not a finding",
             complete_row == []),
            ("a row with no member cells is a finding, at its line",
             len(half_row) == 1 and 'LEDGER.md:3' in str(half_row[0].where)),
            ("an unescaped pipe in a code span is a finding (a cell too many)",
             len(loose_pipe) == 1),
            ("an escaped pipe is one cell", escaped_pipe == []),
            ("an empty member cell is a finding", len(empty_cell) == 1),
        ]
        bad = [n for n, ok in cases if not ok]
        check(f"parallel-artifact-ledger check fires ({len(cases)} stated cases: "
              f"no ledger, ledger missing the commit, a row naming it in "
              f"its change cell, a prose citation not counting as a row, "
              f"a family's own inception commit needing no row, a row "
              f"missing or emptying a member cell)",
              not bad, '; '.join(bad))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_publisher_bound_checks_run_in_a_source_set():
    """A check about published practice content must fire in the repo that
    PUBLISHES it, and must still skip in a repo that merely consumes it.

    precedent_check.py gates every practice-backed check on
    `practices/<slug>.md` being present, which is right for a consumer -- a
    finding whose Rule the reader cannot print is one nobody can act on. A
    practice SOURCE set is the case that gate got wrong: its practices/
    holds its own practices only, it resolves no sources and materializes
    nothing into itself, so every other level's check skipped there
    permanently. Measured 2026-09-12 in a shared source: 12 passed, 42
    SKIPPED, all 42 that one cause.

    It had already cost something. A practice file in that set shipped a
    relative link to `tools/checks/tests/run_all.sh`, which materialization
    deliberately does not copy -- live in the publishing set, dead in every
    repository that received the catalogue. `practice-links-travel` is
    exactly the rule that catches it, and it was one of the 42. A CONSUMING
    repo found it, a sync late.

    `binds_publishers=True` on the registration is the fix. These cases
    assert it in both directions against a real fixture, planting that same
    link, so that a regression here fails rather than going quiet -- and
    they assert the MESSAGE, not merely a non-zero exit
    (practice: control-asserts-which-failure).
    """
    import tempfile
    cases = []

    src = ROOT / 'tools' / 'precedent_check.py'
    # 1. The flags are still set. Three checks earned this the hard way, each
    #    with its own incident in a comment beside it; dropping one silently
    #    puts the publishing repos back to unchecked.
    text = src.read_text(encoding='utf-8')
    #    Thirteen more joined them 2026-09-22, from the audit that read all
    #    44 skipped checks one at a time (spec/PUBLISHER_GATE_AUDIT.md). They
    #    are pinned by NAME rather than by counting flags in the file, so a
    #    flag moved off one check and onto another still fails here.
    for slug in ('practice-links-travel', 'catalogue-carries-stories',
                 'generated-artifact-provenance',
                 'cite-the-incident', 'source-naming', 'decision-strength',
                 'acronyms-glossary', 'doc-references-are-links',
                 'heading-outline', 'label-describes-content',
                 'docs-are-current-state', 'index-remembers-past',
                 'deliverables-look-like-output', 'no-version-suffix',
                 'filename-separator', 'technical-describes-people'):
        i = text.find(f"@check('{slug}'")
        nxt = text.find('@check(', i + 1) if i >= 0 else -1
        body = text[i:nxt] if i >= 0 and nxt > i else (text[i:] if i >= 0 else '')
        cases.append((f'{slug} is still registered binds_publishers=True',
                      'binds_publishers=True' in body, ''))

    # 2. THIS repo is not a publisher by this test and so is unaffected. It
    #    has no vendored-engine manifest at all -- it is the origin -- and a
    #    behaviour change here would be a change nobody asked for.
    r = subprocess.run([sys.executable, '-c',
                        'import sys; sys.path.insert(0, "tools"); '
                        'import precedent_check as pc; '
                        'print(pc._publishes_practices())'],
                       cwd=ROOT, capture_output=True, text=True)
    cases.append(('this repo does not read as a publisher (it is the origin, '
                  'and carries every practice file anyway)',
                  r.stdout.strip() == 'False', r.stdout.strip() + failure_detail(r.stderr, 200)))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='publisher-bound-'))
    try:
        # A fixture that OWNS its state: its own git repo, its own declared
        # kind, its own practices/ tree. Nothing here is inherited from the
        # container or from any real source set on disk
        # (practice: fixture-owns-its-state).
        fx = tmp / 'set'
        (fx / 'tools').mkdir(parents=True)
        (fx / 'practices').mkdir()
        # The whole source-kind engine, not just the checker: the check under
        # test asks precedent_vendor_engine what travels, and a fixture
        # missing that module makes it report NotApplicable -- which reads as
        # a SKIPPED and would have been misread here as the gate still
        # blocking it. Found building this control.
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        shutil.copy(src, fx / 'tools' / 'precedent_check.py')
        (fx / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main'}), encoding='utf-8')
        # The link that really shipped broken, in a practice this fixture owns.
        (fx / 'practices' / 'fixture-rule.md').write_text(
            '---\n'
            'slug:        fixture-rule\n'
            'title:       A fixture practice this set publishes\n'
            'tier:        on-demand\n'
            'severity:    default\n'
            'applies_to:  ["practices/*.md"]\n'
            'occasion:    "the fixture runs"\n'
            'gates:       []\n'
            'index_clause: "the fixture runs"\n'
            'checked_by:  null\n'
            'defines:     []\n'
            'status:      active\n'
            'supersedes:  []\n'
            'overrides:   null\n'
            'added:       2026-09-12\n'
            'approved_by: "fixture"\n'
            '---\n'
            '## Rule\nThe fixture practice says nothing in particular.\n\n'
            '## Story\nWritten for this control; no incident is claimed.\n',
            encoding='utf-8')

        def run_in_fixture(kind):
            (fx / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': kind,
                'source_repo': 'https://github.com/example/upstream',
                'source_branch': 'main',
                'files': ['precedent_check.py'],
            }), encoding='utf-8')
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only',
                 'practice-links-travel'],
                cwd=fx, capture_output=True, text=True, env=env)

        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)

        # Clean first: a publisher whose links all travel must PASS, so a
        # green result here is not just the check failing to find the file.
        (fx / 'practices' / 'fixture-rule.md').write_text(
            (fx / 'practices' / 'fixture-rule.md').read_text(encoding='utf-8')
            + '\nA sibling link that does travel: [fixture-rule](fixture-rule.md).\n',
            encoding='utf-8')
        ok = run_in_fixture('source')
        cases.append(('a publisher with only travelling links PASSES (so the '
                      'firing case below is the planted link, not a no-op)',
                      'VIOLATION' not in ok.stdout and ok.returncode == 0,
                      failure_detail(ok.stdout, 300) + failure_detail(ok.stderr, 200)))

        # Now plant the shape that shipped: a relative link out of practices/
        # to a file materialization does not copy.
        (fx / 'practices' / 'fixture-rule.md').write_text(
            (fx / 'practices' / 'fixture-rule.md').read_text(encoding='utf-8')
            + '\nA driver link that does not: '
              '[`run_all.sh`](../tools/checks/tests/run_all.sh).\n',
            encoding='utf-8')

        pub = run_in_fixture('source')
        cases.append(('a PUBLISHER runs the check and fails on the planted link',
                      pub.returncode != 0 and 'VIOLATION' in pub.stdout,
                      f'rc={pub.returncode} ' + failure_detail(pub.stdout, 300)))
        cases.append(('the finding names the file that does not travel',
                      'run_all.sh' in pub.stdout and 'does not travel' in pub.stdout,
                      failure_detail(pub.stdout, 300)))
        # The Rule cannot be printed here, so it must say where the Rule IS.
        # Printing "(no practice file for ...)" instead would be the whole
        # design of the module -- the failure message is the rule -- quietly
        # failing at the one moment it is load-bearing.
        cases.append(('and says where the Rule lives, since this repo cannot '
                      'print it',
                      'practices/practice-links-travel.md' in pub.stdout
                      and 'no practice file for' not in pub.stdout,
                      failure_detail(pub.stdout, 400)))

        con = run_in_fixture('consumer')
        cases.append(('a CONSUMER still skips it, planted link and all',
                      con.returncode == 0 and 'SKIPPED' in con.stdout,
                      f'rc={con.returncode} ' + failure_detail(con.stdout, 300)))
        cases.append(('and says why it skipped, naming the absent practice file',
                      'not in force here' in con.stdout, failure_detail(con.stdout, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a check about published practices binds the publisher and still '
          f'skips a consumer ({len(cases)} stated cases, each asserting the '
          f'printed text)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_a_set_runs_the_checks_its_declared_sources_put_in_force():
    """A practice set's checks see the rules the sources it declares carry.

    A set's practices/ holds its own catalogue only, so until 2026-10-30
    every universal check skipped in a set as "not in force" although the
    set declares universal in precedent.json and its sessions read
    universal's rules at session start: measured that day, 44 of the
    ladder set's checks skipped for that one reason, and opening them found
    real findings in all three sets (spec frontmatter, an audit script with
    no run_all.sh). Morgan, 2026-10-30: "Act. Let's build this."

    Asserted against a fixture that owns its state -- a set and the
    upstream it declares, side by side -- in four directions: the check
    runs through the declaration and fails on a planted bad citation; a
    universal slug, and a set's deduplicated stub of one, are not typos
    there; the same set with no declaration still skips; a consumer is
    unaffected; and a check marked skips_in_sets says why it skipped
    (practice: control-asserts-which-failure).
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-declared-sources-'))
    try:
        up, fx = tmp / 'upstream', tmp / 'set'
        (up / 'practices').mkdir(parents=True)
        for slug in ('code-cites-practice', 'quick-index'):
            shutil.copy(ROOT / 'practices' / f'{slug}.md',
                        up / 'practices' / f'{slug}.md')

        def practice(where, slug, status='active', extra=''):
            (where / f'{slug}.md').write_text(
                '---\n'
                f'slug:        {slug}\n'
                'title:       A fixture practice\n'
                'tier:        on-demand\n'
                'severity:    default\n'
                'applies_to:  ["tools/*.py"]\n'
                'occasion:    "the fixture runs"\n'
                'gates:       []\n'
                'index_clause: "the fixture runs"\n'
                'checked_by:  null\n'
                'defines:     []\n'
                f'status:      {status}\n'
                f'{extra}'
                'supersedes:  []\n'
                'overrides:   null\n'
                'added:       2026-10-30\n'
                'approved_by: "fixture"\n'
                '---\n'
                '## Rule\nThe fixture practice says nothing in particular.\n\n'
                '## Story\nWritten for this control; no incident is claimed.\n',
                encoding='utf-8')
        practice(up / 'practices', 'fixture-upstream-rule')
        practice(up / 'practices', 'fixture-promoted-rule')

        (fx / 'tools').mkdir(parents=True)
        (fx / 'practices').mkdir()
        practice(fx / 'practices', 'fixture-own-rule')
        practice(fx / 'practices', 'fixture-promoted-rule', 'deduplicated',
                 'in_force_at: fixture-promoted-rule\n')
        engine = []
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
                engine.append(name)
        shutil.copy(ROOT / 'tools' / 'precedent_check.py',
                    fx / 'tools' / 'precedent_check.py')
        cites = fx / 'tools' / 'fixture_tool.py'
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)

        def run(kind, declares, slug, cite):
            (fx / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
                'kind': kind,
                'source_repo': 'https://github.com/example/upstream',
                'source_branch': 'main',
                'files': sorted(set(engine) | {'precedent_check.py'}),
            }), encoding='utf-8')
            cfg = {'format_version': 1, 'base_branch': 'main'}
            if declares:
                cfg['sources'] = [{'level': 'universal', 'name': 'precedent',
                                   'path': '../upstream'}]
            (fx / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
            cites.write_text('\n'.join(f'# practice: {c}' for c in cite) + '\n',
                             encoding='utf-8')
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only', slug],
                cwd=fx, capture_output=True, text=True, env=env)

        good = ['fixture-own-rule', 'fixture-upstream-rule',
                'fixture-promoted-rule']
        ok = run('source', True, 'code-cites-practice', good)
        cases.append(('a set declaring upstream RUNS a check whose practice '
                      'is upstream only, and passes citations of its own, an '
                      'upstream and a deduplicated-stub slug',
                      ok.returncode == 0 and ' 1 passed' in ok.stdout
                      and 'not in force' not in ok.stdout,
                      f'rc={ok.returncode} ' + failure_detail(ok.stdout, 400)))
        bad = run('source', True, 'code-cites-practice', good + ['fixture-no-such'])
        cases.append(('...and fails on a planted citation no source carries, '
                      'naming it',
                      bad.returncode != 0 and 'VIOLATION' in bad.stdout
                      and "'fixture-no-such'" in bad.stdout
                      and 'fixture-upstream-rule' not in bad.stdout,
                      f'rc={bad.returncode} ' + failure_detail(bad.stdout, 400)))
        bare = run('source', False, 'code-cites-practice', good + ['fixture-no-such'])
        cases.append(('the same set declaring no upstream still skips it as '
                      'not in force',
                      bare.returncode == 0 and 'not in force here' in bare.stdout,
                      f'rc={bare.returncode} ' + failure_detail(bare.stdout, 300)))
        con = run('consumer', True, 'code-cites-practice', good + ['fixture-no-such'])
        cases.append(('a CONSUMER is unaffected: it materializes its sources, '
                      'so a declaration alone still skips',
                      con.returncode == 0 and 'not in force here' in con.stdout,
                      f'rc={con.returncode} ' + failure_detail(con.stdout, 300)))
        qi = run('source', True, 'quick-index', good)
        cases.append(('a check marked skips_in_sets reports SKIPPED in a set, '
                      'with its reason',
                      qi.returncode == 0 and 'SKIPPED' in qi.stdout
                      and 'a practice set is not the kind of repository' in qi.stdout
                      and 'loader block' in qi.stdout,
                      f'rc={qi.returncode} ' + failure_detail(qi.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a practice set runs the checks its declared sources put in force '
          f'({len(cases)} stated cases, each asserting the printed text)',
          not failed,
          '; '.join(f'{n} ({d})' for n, d in failed))


def check_deep_check_keeps_a_test_of_a_tool():
    """deep-check reports a test with no check of its name as stale only
    when it was a check's test or names nothing that is here.

    The ladder set keeps tests of its own tools (tools/ladder/others_did.py
    and five more) beside its check tests; the day universal's checks first
    ran in a set (2026-10-30), all six read as "a stale test left behind",
    all six passing. Three directions, each asserting the printed text: a
    tool's test is kept; a test naming a check that is gone is stale; a
    test naming nothing here is stale (practice: control-asserts-which-failure).
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='deep-check-tool-tests-'))
    try:
        fx = tmp / 'repo'
        tests = fx / 'tools' / 'checks' / 'tests'
        tests.mkdir(parents=True)
        (fx / 'tools' / 'ladder').mkdir()
        (fx / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'deep-check.md',
                    fx / 'practices' / 'deep-check.md')
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        (fx / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main'}), encoding='utf-8')
        (tests / 'run_all.sh').write_text(
            '#!/bin/bash\nfor t in "$(dirname "$0")"/test_*.sh; do bash "$t"; done\n',
            encoding='utf-8')
        (fx / 'tools' / 'ladder' / 'fixture_tool.py').write_text('', encoding='utf-8')
        (tests / 'test_fixture_tool.sh').write_text(
            'python3 tools/ladder/fixture_tool.py\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)

        def run():
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only', 'deep-check'],
                cwd=fx, capture_output=True, text=True, env=env)

        ok = run()
        cases.append(("a test of a tool that is here, with no check of its "
                      "name, is not reported stale",
                      ok.returncode == 0 and 'stale test' not in ok.stdout
                      and ' 1 passed' in ok.stdout,
                      f'rc={ok.returncode} ' + failure_detail(ok.stdout, 400)))
        (tests / 'test_fixture_gone.sh').write_text(
            'python3 tools/checks/check_fixture_gone.py\n', encoding='utf-8')
        gone = run()
        cases.append(("a test naming a check that is gone is stale, by name",
                      gone.returncode != 0
                      and 'test_fixture_gone.sh: tests check_fixture_gone.py' in gone.stdout
                      and 'test_fixture_tool.sh' not in gone.stdout,
                      f'rc={gone.returncode} ' + failure_detail(gone.stdout, 400)))
        (tests / 'test_fixture_gone.sh').unlink()
        (tests / 'test_fixture_orphan.sh').write_text(
            'python3 tools/ladder/no_such_tool.py\n', encoding='utf-8')
        orphan = run()
        cases.append(("a test naming nothing that is here is stale",
                      orphan.returncode != 0
                      and 'test_fixture_orphan.sh' in orphan.stdout
                      and 'stale test' in orphan.stdout,
                      f'rc={orphan.returncode} ' + failure_detail(orphan.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'deep-check keeps a test of a tool and still reports a stale one '
          f'({len(cases)} stated cases, each asserting the printed text)',
          not failed,
          '; '.join(f'{n} ({d})' for n, d in failed))


def check_deep_check_skips_a_repo_with_no_check_scripts():
    """deep-check skips a repository with no tools/checks/check_*.py, and
    still reports one that has check scripts but no run_all.sh.

    On 2026-11-01 Update Vendors moved a shared practice set whose only
    audit is a script under tools/ onto an engine that resolves
    deep-check from universal; it reported "run_all.sh is missing" in a repo
    with nothing to run together. Two directions, each asserting the printed
    text: no check scripts at all reads SKIPPED (not applicable) with the
    reason; check scripts with no run_all.sh is still a violation naming
    run_all.sh (practice: control-asserts-which-failure).
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='deep-check-no-checks-'))
    try:
        fx = tmp / 'repo'
        (fx / 'tools').mkdir(parents=True)
        (fx / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'deep-check.md',
                    fx / 'practices' / 'deep-check.md')
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        (fx / 'tools' / 'fixture_audit.py').write_text('', encoding='utf-8')
        (fx / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main'}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)

        def run():
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only', 'deep-check'],
                cwd=fx, capture_output=True, text=True, env=env)

        none = run()
        cases.append(("no tools/checks/ at all is skipped as not applicable, "
                      "with the reason",
                      none.returncode == 0
                      and 'nothing to run together' in none.stdout
                      and 'VIOLATION' not in none.stdout,
                      f'rc={none.returncode} ' + failure_detail(none.stdout, 400)))
        (fx / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        empty = run()
        cases.append(("a tools/checks/ holding no check_*.py is skipped too",
                      empty.returncode == 0
                      and 'nothing to run together' in empty.stdout
                      and 'VIOLATION' not in empty.stdout,
                      f'rc={empty.returncode} ' + failure_detail(empty.stdout, 400)))
        (fx / 'tools' / 'checks' / 'check_fixture.py').write_text(
            'SOURCE_ROOT = None\n', encoding='utf-8')
        broken = run()
        cases.append(("check scripts with no run_all.sh are still a violation "
                      "naming run_all.sh",
                      broken.returncode != 0
                      and 'run_all.sh: is missing' in broken.stdout
                      and 'nothing to run together' not in broken.stdout,
                      f'rc={broken.returncode} ' + failure_detail(broken.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'deep-check skips a repo with no check scripts and still reports '
          f'one missing run_all.sh ({len(cases)} stated cases, each asserting '
          f'the printed text)',
          not failed,
          '; '.join(f'{n} ({d})' for n, d in failed))


def check_stale_exemption_is_named():
    """An exemption whose check would now pass or skip without it is named
    as no longer needed -- by --stale-exemptions, by an --only run, and in
    Update Vendors' warnings -- and one that still suppresses a finding is
    not.

    2026-11-01: a shared set exempted deep-check over a false alarm; the
    engine was fixed that day, and nothing would have told its next update
    the entry could come out, since an exempted check never runs. The
    control direction asserts the printed text too (practice:
    control-asserts-which-failure).
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_update as pu
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='stale-exemption-'))
    try:
        fx = tmp / 'repo'
        (fx / 'tools').mkdir(parents=True)
        (fx / 'practices').mkdir()
        shutil.copy(ROOT / 'practices' / 'deep-check.md',
                    fx / 'practices' / 'deep-check.md')
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        (fx / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'base_branch': 'main',
             'not_binding': [{'slug': 'deep-check',
                              'reason': 'fixture: no check family'}]}),
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')

        def run(*args):
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', *args],
                cwd=fx, capture_output=True, text=True, env=env)

        flag = run('--stale-exemptions')
        cases.append(("--stale-exemptions names an exemption whose check now "
                      "skips",
                      flag.returncode == 0
                      and 'STALE EXEMPTION  deep-check' in flag.stdout
                      and '1 stale exemption(s)' in flag.stdout,
                      f'rc={flag.returncode} ' + failure_detail(flag.stdout, 400)))
        only = run('--only', 'deep-check')
        cases.append(("an --only run prints it beside the EXEMPT line",
                      'EXEMPT     deep-check' in only.stdout
                      and 'STALE EXEMPTION  deep-check' in only.stdout,
                      f'rc={only.returncode} ' + failure_detail(only.stdout, 400)))
        warned = pu.stale_exemption_warnings(fx)
        cases.append(("Update Vendors carries it as a warning",
                      len(warned) == 1 and warned[0].startswith('deep-check')
                      and 'remove it from not_binding' in warned[0],
                      repr(warned)[:300]))
        (fx / 'tools' / 'checks').mkdir()
        (fx / 'tools' / 'checks' / 'check_fixture.py').write_text(
            'SOURCE_ROOT = None\n', encoding='utf-8')
        kept = run('--stale-exemptions')
        cases.append(("an exemption that still suppresses a violation is not "
                      "named",
                      kept.returncode == 0
                      and 'STALE EXEMPTION' not in kept.stdout
                      and '0 stale exemption(s)' in kept.stdout,
                      f'rc={kept.returncode} ' + failure_detail(kept.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'an exemption no longer needed is named, one still needed is not '
          f'({len(cases)} stated cases, each asserting the printed text)',
          not failed,
          '; '.join(f'{n} ({d})' for n, d in failed))


# Checks a freshly made repository of a given kind fails ON PURPOSE, each with
# the reason. Anything else that violates in a fresh repo is a false alarm.
_FRESH_REPO_EXPECTED_FINDINGS = {
    'budget-within-approval': (
        'a new repository\'s session-load budget waits for its owner to '
        'approve it: the finding is the question the check exists to ask'),
}


def check_tree_checks_hold_on_every_kind_of_fresh_repo():
    """The full sweep finds nothing wrong in a repository of each kind that
    the engine's own tools have just made, apart from the findings
    _FRESH_REPO_EXPECTED_FINDINGS names with a reason.

    On 2026-11-01 deep-check, ported into universal on 2026-10-05, reached a
    shared practice set with no check scripts for the first time and
    reported a missing run_all.sh there: the move had exempted only the one
    repository that broke at the time, the engine's origin. Each check is
    tested where it was written; nothing ran it against the other kinds of
    repository a move into universal makes it reach. This does, with
    fixtures made the way real ones are (practice: fixture-owns-its-state):

      - a shared practice set from precedent_bootstrap_source.py, which has
        no tools/checks/, the shape of a set whose only audit lives in tools/;
      - the same set given a check family: a check script, its test, and a
        run_all.sh that runs the tests;
      - a consuming project from precedent_install.py.

    Each declares this tree as its universal source and runs this tree's
    precedent_check.py, so a check changed or newly reaching a kind is
    judged before it lands. The engine's origin is this repository itself,
    swept by the full check, so it is not rebuilt here.

    Negative control, measured 2026-11-01: with _deep_check as it was
    before 5a0db092b, the first fixture reports deep-check VIOLATION
    (run_all.sh is missing) and this test fails.
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-every-kind-'))
    (tmp / 'home').mkdir()
    env = dict(_isolated_env(os.environ, tmp / 'home'),
               GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(),
               PRECEDENT_SEED_OFF_MAIN='1', PRECEDENT_NO_SELF_HEAL='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')
    results = []

    def git(repo, *a):
        return subprocess.run(['git', '-C', str(repo), '-c',
                               'core.hooksPath=/dev/null', *a],
                              capture_output=True, text=True, env=env)

    def point_universal_here(repo):
        cfg_path = repo / 'precedent.json'
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        for s in cfg.get('sources') or []:
            if isinstance(s, dict) and s.get('level') == 'universal':
                s['path'] = str(ROOT)
        cfg_path.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')

    def sweep(kind, repo):
        # The seed copies the engine as committed; the checks under test are
        # this tree's, committed or not. The delivery record is re-pinned to
        # the copy, or an uncommitted edit here reads as a local edit to a
        # received file there (upstream-bug-stops-here) -- the fixture's
        # state, not the code under test (practice: fixture-owns-its-state).
        import hashlib
        src = ROOT / 'tools' / 'precedent_check.py'
        shutil.copy2(src, repo / 'tools' / 'precedent_check.py')
        man_path = repo / 'tools' / 'ENGINE_MANIFEST.json'
        if man_path.is_file():
            man = json.loads(man_path.read_text(encoding='utf-8'))
            if isinstance(man.get('sha256'), dict) and 'precedent_check.py' in man['sha256']:
                man['sha256']['precedent_check.py'] = hashlib.sha256(
                    src.read_bytes()).hexdigest()
                man_path.write_text(json.dumps(man, indent=2) + '\n',
                                    encoding='utf-8')
        if not (repo / '.git').exists():
            git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'fixture')
        r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                            '--full-sweep'], cwd=str(repo),
                           capture_output=True, text=True, env=env, timeout=900)
        found = sorted(set(re.findall(r'^(?:VIOLATION|ERROR(?:ED)?)\s+(\S+)',
                                      r.stdout, re.M)))
        unexpected = [s for s in found if s not in _FRESH_REPO_EXPECTED_FINDINGS]
        tally = re.search(r'^precedent_check: .*$', r.stdout, re.M)
        results.append((kind, unexpected,
                        tally.group(0)[:160] if tally else
                        f'rc={r.returncode} ' + failure_detail(r.stdout + r.stderr, 400),
                        r.stdout))

    try:
        boot = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        for kind, with_checks in (('a shared set with no check scripts', False),
                                  ('a shared set with a check family', True)):
            repo = tmp / ('set-checks' if with_checks else 'set-bare')
            r = subprocess.run([sys.executable, boot, '--level', 'shared',
                                '--name', repo.name, '--dest', str(repo),
                                '--off-main', 'true',
                                '--approver', 'A Person:aperson'],
                               capture_output=True, text=True, env=env, timeout=300)
            if r.returncode != 0 or not (repo / 'precedent.json').is_file():
                results.append((kind, ['(bootstrap failed)'],
                                failure_detail(r.stdout + r.stderr, 400), ''))
                continue
            point_universal_here(repo)
            if with_checks:
                checks = repo / 'tools' / 'checks'
                (checks / 'tests').mkdir(parents=True)
                (checks / 'check_fixture_rule.py').write_text(
                    '#!/usr/bin/env python3\n'
                    '"""A fixture audit: passes everywhere."""\n'
                    'import os, pathlib, sys\n'
                    'SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[2]\n'
                    'ROOT = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT",'
                    ' SOURCE_ROOT))\n'
                    'RULE = SOURCE_ROOT / "practices" / "fixture-rule.md"\n'
                    'sys.exit(0)\n', encoding='utf-8')
                (checks / 'tests' / 'test_fixture_rule.sh').write_text(
                    '#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")/../../.."\n'
                    'python3 tools/checks/check_fixture_rule.py\n',
                    encoding='utf-8')
                (checks / 'tests' / 'run_all.sh').write_text(
                    '#!/bin/bash\nset -uo pipefail\ncd "$(dirname "$0")"\nstatus=0\n'
                    'for t in test_*.sh; do\n  [ -e "$t" ] || continue\n'
                    '  bash "$t" || status=1\ndone\nexit $status\n',
                    encoding='utf-8')
            sweep(kind, repo)

        proj = tmp / 'project'
        git_init = subprocess.run(['git', 'init', '-q', '-b', 'main', str(proj)],
                                  capture_output=True, text=True, env=env)
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_install.py'),
                            str(proj), '--project-name', 'Fixture',
                            '--visibility', 'private', '--admin', 'fixture-admin'],
                           capture_output=True, text=True, env=env, timeout=600)
        if git_init.returncode or not (proj / 'precedent.json').is_file():
            results.append(('a consuming project', ['(install failed)'],
                            failure_detail(r.stdout + r.stderr, 400), ''))
        else:
            sweep('a consuming project', proj)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A sweep that ran nothing would pass vacuously: each kind must have
    # passed checks of its own, counted off the tally line.
    ran = {k: int(m.group(1)) if (m := re.search(r' (\d+) passed', t)) else 0
           for k, _u, t, _out in results}
    bad = [(k, u, t) for k, u, t, _out in results if u]
    idle = [k for k, n in ran.items() if n == 0]
    check(f'the full sweep holds on every kind of freshly made repository '
          f'({len(results)} kinds; {len(_FRESH_REPO_EXPECTED_FINDINGS)} '
          f'finding(s) expected in a fresh repo, each with its reason)',
          len(results) == 3 and not bad and not idle,
          '; '.join([f'{k}: unexpected {", ".join(u)} ({t})' for k, u, t in bad]
                    + [f'{k}: the sweep passed nothing' for k in idle])
          or f'{len(results)} of 3 kinds ran')


def check_practice_links_travel_skips_a_consumers_repo_local_practices():
    """A consumer's repo-local practice is never published, so
    practice-links-travel must not test its links -- and the repair it
    prints for a practice it DOES test must not be a URL into a repository
    that is not declared public.

    Found 2026-09-27 in a private consuming repository: after a vendor
    update its full check reported 20 working links in its own repo-local
    practices as dead, because the check kept every practice the committed
    MANIFEST.json did not attribute to ANOTHER source, and `repo-local` is
    not another source. Each finding advised an absolute URL into that
    private repository -- the disclosure the practice's own Rule forbids.

    One fixture, three runs, each asserting the printed text rather than an
    exit status alone (practice: control-asserts-which-failure):
      1. the repo-local practice with a working relative link is not
         reported;
      2. the SAME file, no longer named in the manifest (so this repository
         publishes it), IS reported -- which is what keeps case 1 from
         passing because the check never looked;
      3. that finding's repair is a backticked path under
         `visibility: private`, and a URL under `visibility: public`.
    """
    import tempfile
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='links-travel-local-'))
    try:
        # A fixture that owns its state: its own git repo, manifest,
        # visibility and practices/ (practice: fixture-owns-its-state).
        fx = tmp / 'consumer'
        (fx / 'tools').mkdir(parents=True)
        (fx / 'practices').mkdir()
        (fx / 'content').mkdir()
        for name in _source_kind_engine_files():
            e = ROOT / 'tools' / name
            if e.is_file():
                shutil.copy(e, fx / 'tools' / name)
        shutil.copy(ROOT / 'tools' / 'precedent_check.py',
                    fx / 'tools' / 'precedent_check.py')
        # The consumer gate runs a practice-backed check only when its
        # practice file is here, as it is in every real consumer.
        shutil.copy(ROOT / 'practices' / 'practice-links-travel.md',
                    fx / 'practices' / 'practice-links-travel.md')
        (fx / 'content' / 'LIST.md').write_text('# List\n', encoding='utf-8')
        (fx / 'practices' / 'fixture-local.md').write_text(
            '---\nslug:        fixture-local\ntitle:       A repo-local rule\n'
            'tier:        on-demand\nseverity:    default\n'
            'applies_to:  ["content/*.md"]\noccasion:    "the fixture runs"\n'
            'gates:       []\nindex_clause: "the fixture runs"\n'
            'checked_by:  null\ndefines:     []\nstatus:      active\n'
            'supersedes:  []\noverrides:   null\nadded:       2026-09-27\n'
            'approved_by: "fixture"\n---\n'
            '## Rule\nAdd items to [the list](../content/LIST.md).\n\n'
            '## Story\nWritten for this control; no incident is claimed.\n',
            encoding='utf-8')
        (fx / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'kind': 'consumer',
            'source_repo': 'https://github.com/example/upstream',
            'source_branch': 'main',
            'files': ['precedent_check.py'],
        }), encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=fx, capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin',
                        'https://github.com/example/consumer.git'],
                       cwd=fx, capture_output=True)

        def run(local_level, visibility):
            entries = [{'slug': 'practice-links-travel', 'level': 'universal'}]
            if local_level:
                entries.append({'slug': 'fixture-local', 'level': local_level})
            (fx / 'MANIFEST.json').write_text(
                json.dumps({'practices': entries}), encoding='utf-8')
            (fx / 'precedent.json').write_text(json.dumps(
                {'format_version': 1, 'base_branch': 'main',
                 'visibility': visibility}), encoding='utf-8')
            env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
            return subprocess.run(
                [sys.executable, 'tools/precedent_check.py', '--only',
                 'practice-links-travel'],
                cwd=fx, capture_output=True, text=True, env=env)

        local = run('repo-local', 'private')
        cases.append(('a consumer\'s repo-local practice with a working '
                      'relative link is not reported',
                      local.returncode == 0 and 'VIOLATION' not in local.stdout
                      and 'fixture-local.md:' not in local.stdout,
                      f'rc={local.returncode} ' + failure_detail(local.stdout, 400)))
        cases.append(('and the skip says the repo-local practices were left '
                      'out because they are never published',
                      'repo-local source' in local.stdout
                      and 'never published' in local.stdout,
                      failure_detail(local.stdout, 400)))

        pub = run(None, 'private')
        cases.append(('the same link in a practice this repository publishes '
                      'IS reported (so the case above is the guard, not a '
                      'check that never looked)',
                      pub.returncode != 0
                      and 'fixture-local.md:' in pub.stdout
                      and 'does not travel' in pub.stdout,
                      f'rc={pub.returncode} ' + failure_detail(pub.stdout, 400)))
        cases.append(('under visibility: private the repair is the backticked '
                      'path, never a URL into this repository',
                      '`content/LIST.md`' in pub.stdout
                      and 'github.com/example/consumer' not in pub.stdout,
                      failure_detail(pub.stdout, 400)))

        public = run(None, 'public')
        cases.append(('under visibility: public the repair is the absolute URL',
                      'https://github.com/example/consumer/blob/main/'
                      'content/LIST.md' in public.stdout,
                      failure_detail(public.stdout, 400)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'practice-links-travel skips a consumer\'s repo-local practices '
          f'and suggests a URL only in a public repository '
          f'({len(cases)} stated cases, each asserting the printed text)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_a_gap_names_its_reason():
    """A line that admits work left undone says on that line what blocks
    it, in a reply (reply_check.json, gap-names-its-reason) and in a line a
    change adds to an open item (precedent_check, todo-is-a-handoff), both
    through precedent_reply_check.unexplained_gaps.

    2026-10-20: a session wrote "the practice-hook refusal has no test that
    triggers it" and "Not built." into a reply and an open item, with
    nothing blocking either, and nothing read those lines. Morgan: "how do
    we prevent this issue (you not fixing it it doing a todo) from happening
    again?" The first three refused cases are that session's own lines."""
    import precedent_reply_check as rc
    name = 'a line that leaves work undone names what blocks it'
    rule = [r for r in json.loads((ROOT / 'reply_check.json').read_text(
        encoding='utf-8')) if r.get('id') == 'gap-names-its-reason']
    if len(rule) != 1 or not hasattr(rc, 'unexplained_gaps'):
        check(name, False, 'the gap-names-its-reason rule or unexplained_gaps is missing')
        return

    def refused(line):
        return any(v['kind'] == 'gap_without_reason'
                   for v in rc.violations(line + '\n', rule))
    refuse = [
        'The test covers the failed-tree refusal; the practice-hook refusal '
        'has no test that triggers it.',
        '2. Fixed in universal. Not built.',
        '5. Fixed in prompt-please. No test.',
        "I'll leave that for a follow-up.",
        'The engine half is deferred.',
        'Not fixed yet: the message.',
    ]
    allow = [
        '8. Not built, as asked.',
        'Not built yet: both wait for your go.',
        'No test fails on the new code.',
        "The ladder half can't be done until consumers carry the engine.",
        'The prompt change is wording only and has no test.',
        'The tool printed "not built" and stopped.',
        'Run `no test` here.',
        '```\nNot built.\n```',
        "It is blocked on Morgan's pick, so not built.",
        'Everything above is built and tested.',
    ]
    cases = [(f'refused: {t[:50]}', refused(t)) for t in refuse]
    cases += [(f'allowed: {t[:50]}', not refused(t)) for t in allow]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tr = pathlib.Path(td)
        g = lambda *a: subprocess.run(['git', '-C', str(tr), *a],
                                      capture_output=True, text=True,
                                      env=_fixture_git_env())
        g('init', '-q', '-b', 'main')
        shutil.copytree(ROOT / 'tools', tr / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(ROOT / 'reply_check.json', tr / 'reply_check.json')
        (tr / 'practices').mkdir()
        shutil.copy2(ROOT / 'practices' / 'todo-is-a-handoff.md',
                     tr / 'practices' / 'todo-is-a-handoff.md')
        (tr / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}),
            encoding='utf-8')
        (tr / 'todo').mkdir()
        item = tr / 'todo' / 'todo-2026-10-20-x.md'
        item.write_text('---\nstatus: open\n---\n## What\nOld line, no test.\n',
                        encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')

        def run_check(extra):
            item.write_text(item.read_text(encoding='utf-8') + extra, encoding='utf-8')
            g('add', '-A'); g('commit', '-qm', 'more')
            p = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                                'todo-is-a-handoff', '--range', 'HEAD~1..HEAD'],
                               cwd=str(tr), capture_output=True, text=True,
                               env={**os.environ, 'PRECEDENT_USER_CONFIG':
                                    str(tr / 'none.json')}, timeout=120)
            return p.stdout + p.stderr
        out = run_check('The engine half is not built.\n')
        cases.append(('an open item: an added gap line with no reason is a '
                      'violation', '1 violated' in out and 'not built' in out))
        out = run_check('The ladder half waits on Update Vendors, so not built.\n')
        cases.append(('an open item: an added gap line with its reason passes, and '
                      'a line already there is not read', '0 violated' in out
                      and '1 passed' in out))
    bad = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(bad) + ('' if not bad else f' -- last output: {failure_detail(out, 900)}'))


def check_installer_vendors_the_catalogue_companions():
    """The universal catalogue's companions -- its manifest, its withdrawal
    record and its close_detect.json -- travel with practices/ on install,
    the same list Update Vendors copies, so precedent_close_detect.py
    --explain finds universal's declaration in a consumer.

    Found 2026-10-17 by the very deep check's install rehearsal:
    BestPractice's root close_detect.json (for the universal the-boildown)
    was never vendored, since INSTALL.md section 0 step 1 copies only
    practices/, so "it notices and offers a rule" did nothing on a fresh
    install. Decision chosen by the session under Morgan's delegation of
    2026-10-17 ("Fix the other issues you found including the checks that
    never run. Tell me what you decide. I will be offline so don't wait for
    me. Approved, act, and Booked."): vendor it, the findings item's pick.

    Negative control, measured 2026-10-17: on the code before the fix the
    installer had no list to compare, and --explain in the vendored copy
    said no source declares a close_detect.json.
    """
    import tempfile
    pu, _pve, _pr = _update_tools()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-companions-'))
    try:
        cases.append(("the installer copies the same companions Update Vendors does",
                      getattr(pi, 'CATALOGUE_COMPANIONS', None) == pu.CATALOGUE_COMPANIONS
                      and 'close_detect.json' in pu.CATALOGUE_COMPANIONS,
                      f'{getattr(pi, "CATALOGUE_COMPANIONS", None)} vs {pu.CATALOGUE_COMPANIONS}'))
        proj = tmp / 'proj'
        proj.mkdir()
        pi._vendor_catalogue(proj)
        (proj / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': pi.UNIVERSAL_PATH}]}),
            encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_close_detect.py'),
                            '--explain', '--repo', str(proj)], capture_output=True, text=True)
        cases.append(("--explain in the vendored copy finds universal's close_detect.json",
                      (proj / pi.UNIVERSAL_PATH / 'close_detect.json').is_file()
                      and 'universal/precedent: ready-to-archive' in r.stdout
                      and 'no source declares' not in r.stdout, r.stdout + r.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_install_ships_universal_reply_requirements():
    """A fresh install declares universal's reply requirements: its
    reply_check.json travels beside the catalogue (CATALOGUE_COMPANIONS, on
    install and on Update Vendors), and the todo-is-a-handoff check, which
    reads the same gap-names-its-reason rule, finds it there.

    Found 2026-10-30 by the very deep check: the classic process/upstream/
    layout shipped the file, the installer and Update Vendors never did, so
    an installed repository declared no reply requirements and that check
    always skipped. Shipped 2026-10-31 (Morgan, "do your recommendations for
    all", strength: assented), after each requirement was judged universal
    or one person's convention.

    Negative control, measured 2026-10-31: on the code before the fix the
    companion case fails, the installed copy declares nothing from
    universal, and the open-item check skips instead of finding the gap.
    The CONTROL cases plant the copy without the file and assert both go
    quiet, so the loud cases are about the file and nothing else.
    """
    import tempfile
    pu, _pve, _pr = _update_tools()
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_install as pi
        import precedent_reply_check as prc
    finally:
        sys.path.pop(0)
    upstream = json.loads((ROOT / 'reply_check.json').read_text(encoding='utf-8'))
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-reply-ship-'))
    no_person = str(tmp / 'no-user-config.json')

    def universal_ids(proj):
        old = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = no_person
        try:
            reqs, _notes = prc.declared_requirements(str(proj))
        finally:
            if old is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = old
        return [r.get('id') or r.get('practice') for r in reqs
                if r.get('_source') == 'universal/precedent']

    def install(where, ship):
        proj = tmp / where
        proj.mkdir()
        pi._vendor_catalogue(proj)
        if not ship:
            (proj / pi.UNIVERSAL_PATH / 'reply_check.json').unlink(missing_ok=True)
        shutil.copytree(ROOT / 'tools', proj / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        # The materialized practices/ an install carries at its root, as
        # a consumer's does; one file is all the check needs to be in force.
        (proj / 'practices').mkdir()
        shutil.copy2(ROOT / 'practices' / 'todo-is-a-handoff.md',
                     proj / 'practices' / 'todo-is-a-handoff.md')
        (proj / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': pi.UNIVERSAL_PATH}]}),
            encoding='utf-8')
        g = lambda *a: subprocess.run(['git', '-C', str(proj), *a],
                                      capture_output=True, text=True,
                                      env=_fixture_git_env())
        g('init', '-q', '-b', 'main')
        (proj / 'todo').mkdir()
        item = proj / 'todo' / 'todo-2026-10-31-x.md'
        item.write_text('---\nstatus: open\n---\n## What\nA line.\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        item.write_text(item.read_text(encoding='utf-8')
                        + 'The engine half is not built.\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'a gap with no reason')
        p = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'todo-is-a-handoff', '--range', 'HEAD~1..HEAD'],
                           cwd=str(proj), capture_output=True, text=True,
                           env={**os.environ, 'PRECEDENT_USER_CONFIG': no_person},
                           timeout=120)
        return proj, p.stdout + p.stderr

    try:
        cases.append(('install and Update Vendors both carry reply_check.json '
                      'beside the catalogue',
                      'reply_check.json' in pu.CATALOGUE_COMPANIONS
                      and getattr(pi, 'CATALOGUE_COMPANIONS', None) == pu.CATALOGUE_COMPANIONS,
                      f'{getattr(pi, "CATALOGUE_COMPANIONS", None)} vs {pu.CATALOGUE_COMPANIONS}'))
        proj, out = install('shipped', True)
        copied = proj / pi.UNIVERSAL_PATH / 'reply_check.json'
        cases.append(("the installed copy is universal's file, byte for byte",
                      copied.is_file() and copied.read_bytes()
                      == (ROOT / 'reply_check.json').read_bytes(), str(copied)))
        got = universal_ids(proj)
        cases.append(("a fresh install declares every one of universal's reply "
                      "requirements, gap-names-its-reason among them",
                      len(got) == len(upstream) and 'gap-names-its-reason' in got,
                      f'{len(got)} of {len(upstream)}: {got}'))
        cases.append(('the open-item check finds an unexplained gap in the install',
                      '1 violated' in out and 'names nothing blocking it' in out,
                      failure_detail(out, 600)))
        proj, out = install('not-shipped', False)
        got = universal_ids(proj)
        cases.append(('CONTROL: a copy without the file declares nothing from '
                      'universal', got == [], str(got)))
        cases.append(('CONTROL: and the open-item check says it could not read '
                      'the rule, rather than passing',
                      'no gap-names-its-reason rule is declared here' in out
                      and '0 violated' in out, failure_detail(out, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad_cases = [(n, d) for n, ok, d in cases if not ok]
    return (not bad_cases, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad_cases))


def check_close_detect_counts_only_this_sessions_reverts():
    """The practice-candidate detector's revert signal is this session's own.

    Found 2026-09-30: signals() took every revert reachable from HEAD since
    the session started, so another session's revert, brought in by a merge
    from staging, was reported as "work this session undid". Now only a
    commit carrying this session's trailer, on its own first-parent line,
    counts. Driven against a throwaway repository (practice:
    fixture-owns-its-state)."""
    import tempfile
    import precedent_close_detect as pcd
    cases = []
    saved = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID')
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=env).stdout.strip()

        def commit(f, text, msg):
            (repo / f).write_text(text, encoding='utf-8')
            g('add', '-A'); g('commit', '-qm', msg)

        g('init', '-q', '-b', 'staging')
        commit('a', '1', 'base')
        g('checkout', '-q', '-b', 'claude/mine')
        g('checkout', '-q', 'staging')
        commit('b', '1', 'other work\n\nSession: https://claude.ai/code/session_OTHER')
        g('revert', '--no-edit', 'HEAD')
        g('commit', '-q', '--amend', '-m',
          'Revert "other work"\n\nSession: https://claude.ai/code/session_OTHER')
        g('checkout', '-q', 'claude/mine')
        commit('c', '1', 'mine\n\nSession: https://claude.ai/code/session_ME')
        g('merge', '-q', '--no-ff', '--no-edit', 'staging')
        records = [{'timestamp': '2000-01-01T00:00:00Z', 'type': 'user'}]
        os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = 'cse_ME'
        try:
            before = [d for n, d in pcd.signals(records, repo) if n == 'reverted-or-corrected']
            commit('c', '2', 'Revert my own change\n\nSession: https://claude.ai/code/session_ME')
            after = [d for n, d in pcd.signals(records, repo) if n == 'reverted-or-corrected']
        finally:
            if saved is None:
                os.environ.pop('CLAUDE_CODE_REMOTE_SESSION_ID', None)
            else:
                os.environ['CLAUDE_CODE_REMOTE_SESSION_ID'] = saved
        cases.append(('a revert merged in from another branch is not a signal',
                      before == [], str(before)))
        cases.append(("the session's own revert is",
                      len(after) == 1 and 'Revert my own change' in after[0], str(after)))
    failed = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'the close detector counts only this session\'s own reverts '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_close_detect_skips_every_seeded_header_shape():
    """The practice-candidate detector does not read a prompt another
    session seeded as the person's words, whichever header shape it opens
    with: "Sent automatically by ... Nobody typed this.", the From line the
    reply check's prompt-block-names-both-ends defines, or "Origin:" naming
    a session.

    2026-10-20: a Root issues seed opening "From: session <id> ... A session
    wrote this, not a person" had its "Never let a seed assume the attach
    succeeds." reported at close as "the person said". CONTROL: a person's
    own first line that only mentions a session link is still read."""
    import precedent_close_detect as pcd
    sid = 'session_01AbCdEfGh'
    rule = 'Never let a seed assume the attach succeeds.'
    headers = {
        'Sent automatically': f'Sent automatically by the session "t" ({sid}) -- '
                              f'https://claude.ai/code/{sid}. Nobody typed this.',
        'From line': f'From: session {sid}, "t" (https://claude.ai/code/{sid}). '
                     'A session wrote this, not a person.',
        'Origin': f'Origin: session {sid}; Morgan asked for this seed.',
    }

    def fired(person):
        recs = [{'type': 'user', 'message': {'role': 'user', 'content': person}}]
        return [d for n, d in pcd.signals(recs, ROOT) if n == 'explicit-instruction']
    cases = [(f'a seed headed by the {k} shape is not the person\'s',
              fired(f'{h}\n{rule}') == [], fired(f'{h}\n{rule}'))
             for k, h in headers.items()]
    own = f'Pull the fix from the session https://claude.ai/code/{sid}\n{rule}'
    cases.append(('CONTROL: the person\'s own line naming a session link is still read',
                  len(fired(own)) == 1, fired(own)))
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_close_detect_ignores_the_assistant_quoted_back():
    """The practice-candidate detector does not read the assistant's own
    sentences, quoted back by the person, as the person's instruction.

    2026-10-04, a consumer: the assistant wrote "Each one, from Sept 11 to
    Sept 25, has a single commit that never reached staging."; the person
    pasted it in quotes and added "review those", and the close check
    reported "the person said: ... never reached ..." as an explicit
    instruction. CONTROL: a quote the assistant never wrote still fires, and
    so does the person's own unquoted rule."""
    import precedent_close_detect as pcd
    said = ('Here is what I found. Each one, from Sept 11 to Sept 25, has a '
            '**single commit** that never reached staging. Nothing else.')

    def session(person):
        return [{'type': 'assistant', 'message': {'role': 'assistant',
                 'content': [{'type': 'text', 'text': said}]}},
                {'type': 'user', 'message': {'role': 'user', 'content': person}}]

    def fired(person):
        return [d for n, d in pcd.signals(session(person), ROOT)
                if n == 'explicit-instruction']
    quoted = ('"Each one, from Sept 11 to Sept 25, has a single commit that '
              'never reached staging." review those')
    block = ('> Each one, from Sept 11 to Sept 25, has a single commit\n'
             '> that never reached staging.\n\nreview those')
    cases = [
        ('the assistant\'s sentence quoted back is not the person\'s instruction',
         fired(quoted) == [], fired(quoted)),
        ('...nor as a > blockquote across lines', fired(block) == [], fired(block)),
        ('...and what the person typed around it is still read',
         'review those' in ' '.join(pcd.person_messages(session(quoted))), ''),
        ('CONTROL: a quote the assistant never wrote still fires',
         len(fired('\u201cNever merge into main without asking.\u201d Keep that.')) == 1,
         fired('\u201cNever merge into main without asking.\u201d Keep that.')),
        ('CONTROL: the person\'s own unquoted rule still fires',
         len(fired('Never push straight to main.')) == 1, fired('Never push straight to main.')),
    ]
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_close_detection_fires_only_when_all_conditions_hold():
    """precedent_close_detect.py: the noticing end of the engine, and every
    one of its four conditions, each with the control that proves the
    condition is doing the work.

    Morgan, 2026-09-14, set all four: a merge happened, the reply closes as
    ready to archive, one per session, and the signal came from this
    session's own material. The failure this guards against is not a missed
    detection -- it is a hook that fires on ordinary sessions and trains
    everyone to ignore it.

    Every case owns its own transcript (practice: fixture-owns-its-state).
    """
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-close-'))
    cases = []
    try:
        fx = tmp / 'repo'
        (fx / 'practices').mkdir(parents=True)
        (fx / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]}), encoding='utf-8')

        def transcript(name, turns):
            """turns: [('user'|'assistant'|'tool', payload), ...], oldest first.
            A 'tool' turn is an assistant turn carrying one Bash tool_use."""
            path = tmp / name
            lines = []
            for kind, payload in turns:
                if kind in ('user', 'summary', 'notification'):
                    rec = {'type': 'user', 'timestamp': '2026-09-14T12:00:00Z',
                           'message': {'role': 'user',
                                       'content': [{'type': 'text', 'text': payload}]}}
                    if kind == 'summary':
                        rec['isCompactSummary'] = True
                    if kind == 'notification':
                        rec['origin'] = {'kind': 'task-notification'}
                elif kind == 'tool':
                    rec = {'type': 'assistant', 'timestamp': '2026-09-14T12:00:00Z',
                           'message': {'content': [
                               {'type': 'tool_use', 'name': 'Bash',
                                'input': {'command': payload}}]}}
                else:
                    rec = {'type': 'assistant', 'timestamp': '2026-09-14T12:00:00Z',
                           'message': {'content': [{'type': 'text', 'text': payload}]}}
                lines.append(json.dumps(rec))
            path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return path

        def run(path):
            return subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_close_detect.py'),
                 '--repo', str(fx)],
                input=json.dumps({'transcript_path': str(path)}),
                capture_output=True, text=True, cwd=str(tmp),
                env={**os.environ,
                     'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})

        SAID = 'From now on always run the deep check before pushing.'
        MERGED = 'git merge --no-ff feature-branch'
        CLOSE = 'Done and merged.\n\n## Next Steps\n\n- **Nothing.**\n\nYou can archive this session.'
        full = [('user', SAID), ('tool', MERGED), ('assistant', CLOSE)]

        # The honest default, first: an engine with no declaration has no
        # opinion about anybody's closing convention (rule-level-by-reach).
        r0 = run(transcript('undeclared.jsonl', full))
        cases.append(('with no close_detect.json declared, nothing is detected '
                      'and nothing is blocked', r0.returncode == 0, r0.stderr[:200]))

        (fx / 'close_detect.json').write_text(json.dumps({
            'practice': 'fixture-close-detect',
            'archive_ready_one_of': ['You can archive this session'],
            'closing_heading_matching': 'next step',
            'candidate_marker': 'Practice candidate',
        }), encoding='utf-8')

        r1 = run(transcript('all.jsonl', full))
        cases.append(('all four conditions holding blocks the close',
                      r1.returncode == 2, f'exit {r1.returncode}: {r1.stderr[:200]}'))
        # control-asserts-which-failure: a non-zero exit is not evidence.
        cases.append(('...and the message names the signal it found',
                      'explicit-instruction' in r1.stderr, r1.stderr[:240]))
        cases.append(('...and quotes what he actually said, so the session '
                      'judges the evidence rather than the label',
                      'deep check before pushing' in r1.stderr, r1.stderr[:240]))
        cases.append(('...and says plainly that a one-off is a valid answer, '
                      'because a hook that only accepts a candidate manufactures '
                      'candidates', 'NOT A RULE' in r1.stderr, r1.stderr[:400]))
        cases.append(('...and names the practice that asked for it',
                      'fixture-close-detect' in r1.stderr, r1.stderr[:400]))

        # Condition 1: a merge. "If there wasn't, we were just talking."
        r2 = run(transcript('no-merge.jsonl',
                            [('user', SAID), ('assistant', CLOSE)]))
        cases.append(('a session that merged NOTHING is left alone, however '
                      'much it said', r2.returncode == 0, r2.stderr[:200]))
        # …and `git merge-base` is not a merge. The freshness guard runs one at
        # the start of every session, so a pattern that counts it reports a
        # merge on every session there has ever been.
        r3 = run(transcript('merge-base.jsonl',
                            [('user', SAID),
                             ('tool', 'git merge-base HEAD origin/main'),
                             ('assistant', CLOSE)]))
        cases.append(('`git merge-base` is not a merge -- the check that '
                      'separates the freshness guard from real work',
                      r3.returncode == 0, r3.stderr[:200]))

        # Condition 2: the session is closing as ready to archive. A session
        # still in flight is one somebody is working in.
        mid = 'Merged it.\n\n## Next Steps\n\n- **Keep going.**\n\nDon\'t archive this session.'
        r4 = run(transcript('mid.jsonl', [('user', SAID), ('tool', MERGED),
                                          ('assistant', mid)]))
        cases.append(('a session that is NOT ready to archive is never '
                      'interrupted with a suggestion', r4.returncode == 0,
                      r4.stderr[:200]))

        # Condition 3: the cap. One per session, not one per reply.
        spent = [('user', SAID), ('tool', MERGED),
                 ('assistant', 'Practice candidate: run the deep check first.'),
                 ('assistant', CLOSE)]
        r5 = run(transcript('spent.jsonl', spent))
        cases.append(('a session that already offered one is not asked again '
                      '-- the cap is per SESSION, not per reply',
                      r5.returncode == 0, r5.stderr[:200]))

        # Condition 4: there is actually something to offer. This is the case
        # that keeps the mechanism from becoming filler -- the ordinary
        # session, which is most of them.
        quiet = [('user', 'Can you fix the typo in the README?'),
                 ('tool', MERGED), ('assistant', CLOSE)]
        r6 = run(transcript('quiet.jsonl', quiet))
        cases.append(('an ordinary session with nothing to offer is silent, '
                      'and is not asked to SAY it found nothing either',
                      r6.returncode == 0, r6.stderr[:200]))

        # The engine's own injected text is written in exactly the standing-
        # rule phrasing the detector looks for, and it comes back through the
        # transcript as a `user` record. Reading those as the person's words
        # would fire this on every session forever.
        injected = [('user', '<system-reminder>\nnever guess; always read the '
                     'file first\n</system-reminder>'),
                    ('tool', MERGED), ('assistant', CLOSE)]
        r7 = run(transcript('injected.jsonl', injected))
        cases.append(("a hook's own injected rule text is not mistaken for "
                      'something the person said', r7.returncode == 0,
                      r7.stderr[:200]))

        # The summary a /compact writes comes back as a `user` record too,
        # flagged isCompactSummary, and restates the session's standing rules
        # in the phrasing the detector looks for (2026-09-30: five signals in
        # one session, none of them typed by the person).
        compacted = [('summary', 'Never push to main. Pick up the last task '
                      'as if the break never happened.'),
                     ('tool', MERGED), ('assistant', CLOSE)]
        r7b = run(transcript('compacted.jsonl', compacted))
        cases.append(("a compaction summary is not mistaken for something the "
                      'person said', r7b.returncode == 0, r7b.stderr[:200]))
        # Control: the same words, typed by the person, still fire.
        r7c = run(transcript('typed.jsonl', [('user', compacted[0][1])] +
                             compacted[1:]))
        cases.append(('...while the same words typed by the person still fire',
                      r7c.returncode == 2, f'exit {r7c.returncode}'))

        # A prompt another session seeded, and a pasted block, are that
        # session's words (2026-09-29: three signals from a pasted handoff,
        # reported as "the person said").
        rule = 'Never open a pull request, never merge.'
        seeded = [('user', 'Review this. Sent automatically by the session '
                   '"x" (session_1) -- https://claude.ai/code/session_1. '
                   'Nobody typed this.\n\n' + rule),
                  ('tool', MERGED), ('assistant', CLOSE)]
        r7d = run(transcript('seeded.jsonl', seeded))
        cases.append(("a prompt another session seeded is not mistaken for "
                      'something the person said', r7d.returncode == 0,
                      r7d.stderr[:200]))
        pasted = [('user', 'Thoughts on this?\n<pasted_content id="p1">\n'
                   + rule + '\n</pasted_content id="p1">'),
                  ('tool', MERGED), ('assistant', CLOSE)]
        # A helper's report comes back as a task notification under the
        # person's role (2026-10-31: about twenty signals across three turns
        # of one session, every one a helper's sentence).
        report = ('<task-notification>\n<task-id>a1</task-id>\n<status>completed'
                  '</status>\n<result>' + rule + ' Each one still fails when its '
                  'check is broken so it never fires.</result>\n</task-notification>')
        r7g = run(transcript('helper-report.jsonl', [('notification', report),
                                                     ('tool', MERGED), ('assistant', CLOSE)]))
        cases.append(("a helper's report is not mistaken for something the "
                      'person said', r7g.returncode == 0, r7g.stderr[:200]))
        r7h = run(transcript('helper-report-text.jsonl', [('user', report),
                                                          ('tool', MERGED), ('assistant', CLOSE)]))
        cases.append(('...nor is one with no origin mark, by its envelope',
                      r7h.returncode == 0, r7h.stderr[:200]))
        r7e = run(transcript('pasted.jsonl', pasted))
        cases.append(('nor is text pasted in a <pasted_content> block',
                      r7e.returncode == 0, r7e.stderr[:200]))
        typed_around = [('user', rule + '\n<pasted_content id="p2">\nsome '
                         'notes\n</pasted_content id="p2">'),
                        ('tool', MERGED), ('assistant', CLOSE)]
        r7f = run(transcript('typed-around.jsonl', typed_around))
        cases.append(("...while the person's own words beside a paste still "
                      'fire', r7f.returncode == 2, f'exit {r7f.returncode}'))

        # A gate that blocks the same reply twice is a loop.
        r8 = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_close_detect.py'),
             '--repo', str(fx)],
            input=json.dumps({'transcript_path': str(transcript('again.jsonl', full)),
                              'stop_hook_active': True}),
            capture_output=True, text=True, cwd=str(tmp),
            env={**os.environ,
                 'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})
        cases.append(('a turn this hook already blocked is not blocked twice',
                      r8.returncode == 0, r8.stderr[:200]))

        # Blindness never blocks.
        r9 = run(tmp / 'no-such-transcript.jsonl')
        cases.append(('an unreadable transcript blocks nothing',
                      r9.returncode == 0, r9.stderr[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad_cases = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'close detection fires on all four conditions and on none of them '
          f'alone ({len(cases)} stated cases, each with its control)',
          not bad_cases,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad_cases))


def check_docs_current_state_honours_load_bearing_paths():
    """docs-are-current-state skips a dated marker in a file precedent.json
    declares under `load_bearing_annotations`, and nowhere else.

    2026-10-06: a consumer's working legal drafts carry dated markers that
    matter legally. Those drafts are still edited, so they are
    not records, and `not_binding` would have switched the whole practice
    off. A declaration with no reason exempts nothing and is reported."""
    import tempfile
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='load-bearing-'))
    saved = pc.ROOT
    marker = '# Draft\n\nA new paragraph (added 2026-01-15).\n'

    class _Ctx:
        root = tmp
        changed = ['drafts/terms.md', 'notes.md']

        def read(self, rel):
            return (tmp / rel).read_text(encoding='utf-8')

    def verdict(entries):
        (tmp / 'precedent.json').write_text(json.dumps(
            {'load_bearing_annotations': entries}), encoding='utf-8')
        return [f.file() for f in pc._docs_are_current_state(_Ctx())]

    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        (tmp / 'drafts').mkdir()
        for rel in _Ctx.changed:
            (tmp / rel).write_text(marker, encoding='utf-8')
        pc.ROOT = tmp
        got = verdict([{'paths': 'drafts/**/*.md', 'reason': 'legal weight'}])
        cases.append(('a marker in a declared path passes',
                      not any(g.startswith('drafts/') for g in got), got))
        cases.append(('the same marker outside it still fires',
                      any(g.startswith('notes.md') for g in got), got))
        got = verdict([{'paths': ['drafts/*.md'], 'reason': 'legal weight'}])
        cases.append(('a list of globs is read too',
                      not any(g.startswith('drafts/') for g in got), got))
        got = verdict([{'paths': 'drafts/**/*.md'}])
        cases.append(('an entry with no reason exempts nothing and is '
                      'reported', any(g.startswith('drafts/') for g in got)
                      and 'precedent.json' in got, got))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'docs-are-current-state honours declared load-bearing paths '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_filename_separator_ignores_a_date_suffix():
    """A dated-download suffix (`Name-2026-06-23.docx`) is not the name's
    separator.

    2026-10-06: a consumer's file named like `Some_Name-2026-06-23.docx` was
    counted as using both "-" and "_" -- the same file on both sides of the
    finding -- because only the date was removed and its joining hyphen
    stayed. The control is a genuinely mixed pair, which must still fire."""
    import tempfile, types
    import precedent_check as pc
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='sep-date-'))
    saved = pc.ROOT

    def verdict(names):
        d = tmp / 'docs'
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir()
        for n in names:
            (d / n).write_text('x', encoding='utf-8')
        return [f.detail for f in
                pc._filename_separator(types.SimpleNamespace(root=tmp))]

    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        pc.ROOT = tmp
        got = verdict(['Service_Agreement-2026-06-23.docx',
                       'Order_Form.docx'])
        cases.append(('an underscore name with a date suffix beside another '
                      'underscore name does not fire', got == [], got))
        got = verdict(['Service_Agreement-2026-06-23.docx',
                       'order-form.docx'])
        cases.append(('CONTROL: a genuinely mixed pair still fires',
                      len(got) == 1, got))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pc.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'filename-separator ignores a dated-download suffix '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))

def check_retirement_record_is_not_a_stranded_link():
    """The document explaining a deletion may name what it deleted.

    rename-updates-links hard-coded ONE exemption -- the retirement registry
    file itself -- and nothing else, so the category stayed invisible: the one
    file the author was looking at got covered, and every other document of
    the same kind did not. A repo that retires a mechanism writes two things,
    the registry saying what went and a record saying why, and only the first
    was exempt.

    2026-09-07, a real migration retiring a vendored practice pack: four
    findings, three of them the record OF the deletion read as a reference
    left behind BY one -- a migration record's own "what was deleted" table,
    and a closed dated backlog entry quoting the notice that prompted it.
    Neither can be repointed at anything; naming the dead path is the whole
    content. The fourth was a genuine stranded reference in a merge runbook,
    telling every future session to three-way-merge a file that no longer
    existed -- the finding this check exists for, and the one the three false
    ones were burying. That is the cost of a noisy gate, not just the
    annoyance of it.

    The exemption is the registry's own `exempt_files`, which
    decommission-deletes-files and migration-scrubs-vocabulary already read.
    Same list, same reason, one more reader. It is NOT a blanket pass for any
    file mentioning a retired path: the list is written by a person at the
    moment of retirement, through precedent_decommission.py, which refuses
    while any undeclared reference remains.
    """
    import tempfile, json as _json, shutil as _shutil
    checker = ROOT / 'tools' / 'precedent_check.py'
    if not checker.exists():
        not_applicable('a retirement record may name what it deleted',
                       'tools/precedent_check.py is not present here')
        return

    def _repo(base, exempt):
        """A repo that DELETED a file on this branch, with two references
        left: one in a record (exempt) and one in a live instruction (not)."""
        base.mkdir(parents=True)
        (base / 'process').mkdir()
        (base / 'tools').mkdir()
        # Seed the real consumer engine rather than hand-picking files:
        # precedent_check.py imports several siblings, and a fixture that
        # copies only the ones somebody remembered breaks on the next import
        # added upstream -- which is how the first version of this test
        # "passed" its exemption case while the check was not running at all.
        subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
             'seed', str(base), '--kind', 'consumer'],
            capture_output=True, text=True, timeout=300)
        # And the practice itself: precedent_check.py SKIPS a check whose
        # practice file is not materialized here ("belongs to a source this
        # repo does not resolve"). A skip is not a pass, and reading one as
        # the exemption working is exactly the false green this fixture has
        # to rule out.
        (base / 'practices').mkdir(exist_ok=True)
        _shutil.copy2(ROOT / 'practices' / 'rename-updates-links.md',
                      base / 'practices' / 'rename-updates-links.md')
        # AND OVERWRITE THE SEEDED CHECKER WITH THIS WORKING TREE'S.
        # precedent_vendor_engine.py seeds via `git archive`, so it copies
        # the COMMITTED engine -- which means a fixture built this way tests
        # the code as it was before your change, silently. Caught 2026-09-07
        # while making this very change: three cases went green, the
        # exemption case stayed red, and the checker in the fixture simply
        # did not contain the fix being tested.
        _shutil.copy2(checker, base / 'tools' / 'precedent_check.py')
        (base / 'precedent.json').write_text(
            _json.dumps({'format_version': 1, 'sources': [],
                         'visibility': 'private'}), encoding='utf-8')
        (base / 'process' / 'doomed.md').write_text('# doomed\n', encoding='utf-8')
        (base / 'README.md').write_text('nothing yet\n', encoding='utf-8')

        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        def g(*a):
            return subprocess.run(['git', '-C', str(base)] + list(a),
                                  capture_output=True, text=True, env=env)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 'h@example.com')
        g('config', 'user.name', 'H')
        g('add', '-A'); g('commit', '-qm', 'base')
        # A published default branch is what the check diffs against.
        g('branch', '-f', 'origin-main-stand-in')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')

        (base / 'process' / 'doomed.md').unlink()
        (base / 'process' / 'RETIREMENT_RECORD.md').write_text(
            '# what went\n\n`process/doomed.md` -- superseded, deleted.\n',
            encoding='utf-8')
        (base / 'README.md').write_text(
            'Step 3: three-way-merge `process/doomed.md` before landing.\n',
            encoding='utf-8')
        reg = {'decommissioned': [{'path': 'process/doomed.md',
                            'reason': 'superseded whole',
                            'decommissioned_at': '2026-09-07'}]}
        if exempt:
            reg['exempt_files'] = ['process/RETIREMENT_RECORD.md']
        (base / 'process' / 'decommissioned_paths.json').write_text(
            _json.dumps(reg, indent=2), encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'retire it')
        return base

    def _run(base):
        r = subprocess.run(
            [sys.executable, 'tools/precedent_check.py',
             '--only', 'rename-updates-links'],
            capture_output=True, text=True, cwd=str(base), timeout=300,
            env=dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1'))
        return r.stdout + r.stderr

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        out = _run(_repo(tmp / 'exempt', exempt=True))
        cases.append(('the exempted record may name the deleted path',
                      'RETIREMENT_RECORD.md' not in out))
        cases.append(('and the genuine stranded reference is STILL reported '
                      '-- the exemption is per-file, not a blanket pass',
                      'README.md' in out))

        # NEGATIVE CONTROL. Without the exemption the same tree must flag the
        # record too: otherwise the case above would pass for any reason at
        # all, including the check never having run.
        out = _run(_repo(tmp / 'noexempt', exempt=False))
        cases.append(('without the exemption, the record IS flagged',
                      'RETIREMENT_RECORD.md' in out))
        cases.append(('and so is the live instruction, either way',
                      'README.md' in out))

    failed = [n for n, ok in cases if not ok]
    check(f'a retirement record may name what it deleted, and only it '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def _seed_consumer_engine_isolated(dest):
    """Seed a consumer engine into `dest` through the harness seed cache
    (_seed_fixture_engine), under this process's environment with HOME and
    the user config swapped for an empty scratch directory and the harness's
    own test filter dropped. A real HOME is too big for the cache to key, so
    under it every seed ran for real; the seeded files do not depend on it
    (2026-10-31: a seed under each wrote the same 146 files, byte for byte).
    Returns _seed_fixture_engine's (returncode, output)."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='seed-home-') as h:
        env = {k: v for k, v in os.environ.items() if k not in _UV_CONSUMER_FILTER_VARS}
        env.update(HOME=h, PRECEDENT_USER_CONFIG=str(pathlib.Path(h) / 'no-user-config.json'))
        return _seed_fixture_engine(dest, 'consumer', env, cwd=ROOT)


def check_shipped_hooks_pass_rename_links_without_the_mirror():
    """Every hook BestPractice ships passes rename-updates-links in a
    consumer whose process/upstream/tools/ was just deleted.

    2026-10-01, from a consumer's Update Vendors: the shipped
    freshness-guard.sh and the individual-source bootstrap still fell back
    to process/upstream/tools/X, the check refused the fallback lines, and
    the update rewrote the hooks on every run, so a consumer could not fix
    them and re-run. The hooks now name only tools/X, and the check counts
    "$ROOT/tools/X" as this repo's own. Run as a repository runs it: the
    mirror committed, then deleted in the change that installs every
    shipped hook. CONTROLS: an unguarded call to the deleted path is still
    refused, and a consumer's own guarded loop of the same shape is spared."""
    import tempfile, json as _json, shutil as _shutil
    checker = ROOT / 'tools' / 'precedent_check.py'
    name = ('every shipped hook passes rename-updates-links in a consumer '
            'with no process/upstream/tools/')
    hooks = sorted((ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks').glob('*'))
    if not checker.exists() or not hooks:
        not_applicable(name, 'no checker or no shipped hooks here')
        return
    tools = ('precedent_identity.py', 'precedent_branches.py', 'precedent_resolve.py',
             'precedent_source_bootstrap.py', 'precedent_source_credentials.py')
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td) / 'repo'
        (base / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        (base / 'tools').mkdir()
        _seed_consumer_engine_isolated(base)
        (base / 'practices').mkdir(exist_ok=True)
        _shutil.copy2(ROOT / 'practices' / 'rename-updates-links.md',
                      base / 'practices' / 'rename-updates-links.md')
        _shutil.copy2(checker, base / 'tools' / 'precedent_check.py')
        (base / 'precedent.json').write_text(
            _json.dumps({'format_version': 1, 'sources': [],
                         'visibility': 'private'}), encoding='utf-8')
        for t in tools:
            (base / 'process' / 'upstream' / 'tools' / t).write_text('', encoding='utf-8')
            (base / 'tools' / t).write_text('', encoding='utf-8')
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')

        def g(*a):
            return subprocess.run(['git', '-C', str(base), *a],
                                  capture_output=True, text=True, env=env)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 'h@example.com')
        g('config', 'user.name', 'H')
        g('add', '-A'); g('commit', '-qm', 'base: the mirror still there')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        _shutil.rmtree(base / 'process' / 'upstream' / 'tools')
        (base / '.claude' / 'hooks').mkdir(parents=True, exist_ok=True)
        for h in hooks:
            _shutil.copy2(h, base / '.claude' / 'hooks' / h.name.replace('.template', ''))
        (base / 'scripts').mkdir()
        (base / 'scripts' / 'unguarded.sh').write_text(
            'python3 process/upstream/tools/precedent_identity.py --commit-env .\n',
            encoding='utf-8')
        (base / 'scripts' / 'own_loop.sh').write_text(
            'for c in "$ROOT/tools/precedent_branches.py" '
            '"$ROOT/process/upstream/tools/precedent_branches.py"; do\n'
            '  [ -f "$c" ] && break\ndone\n', encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'drop the mirror, install the hooks')
        r = subprocess.run(
            [sys.executable, 'tools/precedent_check.py',
             '--only', 'rename-updates-links'],
            capture_output=True, text=True, cwd=str(base), timeout=300, env=env)
        out = r.stdout + r.stderr
    flagged = sorted({l.split(':')[0].strip() for l in out.splitlines()
                      if '.claude/hooks/' in l and 'process/upstream/tools/' in l})
    cases = [
        ('no shipped hook is refused', not flagged, ', '.join(flagged)),
        ('CONTROL: an unguarded call to the deleted path is still refused',
         'scripts/unguarded.sh' in out, ''),
        ("a consumer's own guarded loop rooted at \"$ROOT/tools/X\" is spared",
         'scripts/own_loop.sh' not in out, ''),
    ]
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} {d}' for n, d in bad) + ('' if not bad else f' -- {failure_detail(out, 800)}'))


def check_rename_links_spares_a_commit_pinned_permalink():
    """A permalink pinned to a 40-hex commit is how a file that no longer
    exists is cited correctly: it names the file as it was, and cannot go
    stale. rename-updates-links read the path inside one as a reference
    left behind and refused the deletion (a consumer report, 2026-09-28).

    Three references to one deleted path in one fixture: inside a
    commit-pinned permalink (spared), inside a link to a branch (still
    reported -- a branch moves), and bare in prose (still reported). The
    last two are the control: without them a check that stopped running
    would pass the first case.
    """
    import tempfile, json as _json, shutil as _shutil
    checker = ROOT / 'tools' / 'precedent_check.py'
    name = 'rename-updates-links spares a commit-pinned permalink'
    if not checker.exists():
        not_applicable(name, 'tools/precedent_check.py is not present here')
        return
    sha = 'a' * 40
    pages = {
        'PINNED.md': f'Cited: https://github.com/fixture/repo/blob/{sha}/'
                     f'process/doomed.md#L3\n',
        'BRANCH.md': 'See https://github.com/fixture/repo/blob/main/'
                     'process/doomed.md\n',
        'PROSE.md': 'Step 3: read `process/doomed.md` first.\n',
    }
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td) / 'repo'
        (base / 'process').mkdir(parents=True)
        (base / 'tools').mkdir()
        # Seeded, then overwritten with this tree's checker -- seeding copies
        # the COMMITTED engine (see check_retirement_record_is_not_a_stranded_link).
        _seed_consumer_engine_isolated(base)
        (base / 'practices').mkdir(exist_ok=True)
        _shutil.copy2(ROOT / 'practices' / 'rename-updates-links.md',
                      base / 'practices' / 'rename-updates-links.md')
        _shutil.copy2(checker, base / 'tools' / 'precedent_check.py')
        (base / 'precedent.json').write_text(
            _json.dumps({'format_version': 1, 'sources': [],
                         'visibility': 'private'}), encoding='utf-8')
        (base / 'process' / 'doomed.md').write_text('# doomed\n', encoding='utf-8')
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')

        def g(*a):
            return subprocess.run(['git', '-C', str(base), *a],
                                  capture_output=True, text=True, env=env)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 'h@example.com')
        g('config', 'user.name', 'H')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        (base / 'process' / 'doomed.md').unlink()
        for page, text in pages.items():
            (base / page).write_text(text, encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'delete it, cite it three ways')
        r = subprocess.run(
            [sys.executable, 'tools/precedent_check.py',
             '--only', 'rename-updates-links'],
            capture_output=True, text=True, cwd=str(base), timeout=300, env=env)
        out = r.stdout + r.stderr
    cases = [
        ('the path inside a commit-pinned permalink is not reported',
         'PINNED.md' not in out),
        ('the path inside a link to a branch is still reported',
         'BRANCH.md' in out),
        ('the bare path in prose is still reported', 'PROSE.md' in out),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 600)}'))


def check_rename_links_spares_a_longer_path_and_manifest_notes():
    """rename-updates-links reads a deleted path inside a longer path, or
in a manifest entry's notes, as a reference left behind.

THE INCIDENT (2026-10-10, three consumers). Each deleted its own
tools/sound_human_freshness.py to run the pack's copy under
process/<pack>/tools/, repointed every line, and every repointed line was
refused as still naming the deleted file; so was a manifest note recording
an old rename. The DISCRIMINATING CASES are the first two. The other two
are the control: a bare mention and a ../ link from a subdirectory still
name the deleted file and are still reported.
"""
    import tempfile, json as _json, shutil as _shutil
    checker = ROOT / 'tools' / 'precedent_check.py'
    name = 'rename-updates-links spares a longer path and manifest notes'
    if not checker.exists():
        not_applicable(name, 'tools/precedent_check.py is not present here')
        return
    pages = {
        'LONGER.md': 'Run `process/pack/tools/doomed.py fresh` instead.\n',
        'process/manifest.json': '{\n  "entries": [\n    {\n      "notes": "2026-08-28: renamed to tools/doomed.py"\n    }\n  ]\n}\n',
        'PROSE.md': 'Step 3: run `tools/doomed.py` first.\n',
        'docs/SUB.md': 'See [it](../tools/doomed.py).\n',
    }
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td) / 'repo'
        (base / 'process').mkdir(parents=True)
        (base / 'tools').mkdir()
        # Seeded, then overwritten with this tree's checker -- seeding copies
        # the COMMITTED engine (see check_retirement_record_is_not_a_stranded_link).
        _seed_consumer_engine_isolated(base)
        (base / 'practices').mkdir(exist_ok=True)
        _shutil.copy2(ROOT / 'practices' / 'rename-updates-links.md',
                      base / 'practices' / 'rename-updates-links.md')
        _shutil.copy2(checker, base / 'tools' / 'precedent_check.py')
        (base / 'precedent.json').write_text(
            _json.dumps({'format_version': 1, 'sources': [],
                         'visibility': 'private'}), encoding='utf-8')
        (base / 'tools' / 'doomed.py').write_text('# doomed\n', encoding='utf-8')
        (base / 'process' / 'pack' / 'tools').mkdir(parents=True)
        (base / 'process' / 'pack' / 'tools' / 'doomed.py').write_text('# kept\n', encoding='utf-8')
        (base / 'docs').mkdir()
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')

        def g(*a):
            return subprocess.run(['git', '-C', str(base), *a],
                                  capture_output=True, text=True, env=env)
        g('init', '-q', '-b', 'main')
        g('config', 'user.email', 'h@example.com')
        g('config', 'user.name', 'H')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        (base / 'tools' / 'doomed.py').unlink()
        for page, text in pages.items():
            (base / page).write_text(text, encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'delete it, cite it four ways')
        r = subprocess.run(
            [sys.executable, 'tools/precedent_check.py',
             '--only', 'rename-updates-links'],
            capture_output=True, text=True, cwd=str(base), timeout=300, env=env)
        out = r.stdout + r.stderr
    cases = [
        ('THE DISCRIMINATING CASE: the deleted path inside a longer path is '
         'not reported', 'LONGER.md' not in out),
        ('...nor in a manifest entry\'s notes', 'manifest.json' not in out),
        ('the bare path in prose is still reported', 'PROSE.md' in out),
        ('a ../ link from a subdirectory is still reported', 'SUB.md' in out),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 600)}'))


def check_very_deep_check_record_trips_no_check_in_a_consumer():
    """The very deep check's run record, written into a consumer's spec/,
    neither breaks filename-separator nor turns document-status-header from
    a skip into a violation there.

    2026-10-31, a consumer's very deep check: its spec/ named files with
    hyphens and stamped none of them. The run wrote spec/VERY_DEEP_CHECK.md
    (underscores, with lifecycle frontmatter), and the same run's CHECK
    COVERAGE then reported two violations that only that file caused. The
    controls are the repository's own choices, which still fire: an
    underscore name it picked, and a document it stamped itself."""
    import tempfile as _tf, shutil as _sh
    name = 'the very deep check\'s run record trips no check in a consumer'
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-vdcrecord-'))
    stamp = ('---\ntitle: "{t}"\nkind: record\nstatus: live\nopened: 2026-10-31\n'
             'closed: null\nsuperseded_by: null\nsupersedes: []\naudience: session\n'
             'summary: "x"\n---\n# {t}\n\nText.\n')

    def run(slug):
        r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                            '--only', slug], cwd=str(fx),
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    try:
        # The shared fresh install (_fresh_install_fixture), copied, not rerun.
        _fresh_install_fixture(fx)
        (fx / 'spec').mkdir(exist_ok=True)
        for n in ('call-notes.md', 'connected-systems.md'):
            (fx / 'spec' / n).write_text(f'# {n}\n\nNo header.\n', encoding='utf-8')
        (fx / 'spec' / 'VERY_DEEP_CHECK.md').write_text(
            stamp.format(t='Very deep check -- run record'), encoding='utf-8')
        rc_sep, out_sep = run('filename-separator')
        rc_doc, out_doc = run('document-status-header')
        (fx / 'spec' / 'OWN_NOTES.md').write_text('# Own\n\nText.\n',
                                                  encoding='utf-8')
        rc_sep2, out_sep2 = run('filename-separator')
        (fx / 'spec' / 'OWN_NOTES.md').unlink()
        (fx / 'spec' / 'own-plan.md').write_text(stamp.format(t='Own plan'),
                                                 encoding='utf-8')
        rc_doc2, out_doc2 = run('document-status-header')
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    cases = [
        ('filename-separator does not count the run record as the repository\'s '
         '"_" choice', rc_sep == 0 and 'VIOLATION' not in out_sep),
        ('document-status-header still skips a repository that stamped nothing '
         'of its own', rc_doc == 0 and 'none stamped' in out_doc),
        ('control: an underscore name the repository chose still breaks its '
         'hyphenated spec/', rc_sep2 == 1 and 'OWN_NOTES.md' in out_sep2),
        ('control: once the repository stamps a document of its own, its '
         'unstamped ones are found', rc_doc2 == 1
         and 'spec/call-notes.md' in out_doc2),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else
                               f' -- {failure_detail(out_sep, 400)} / {failure_detail(out_doc, 400)} / '
                               f'{failure_detail(out_sep2, 300)} / {failure_detail(out_doc2, 300)}'))


def check_changed_files_asks_a_new_check_for_its_planted_case():
    """In BestPractice, a change to the check registry or the harness is
    refused when a registered check has no planted case in
    check_precedent_check_fires -- named, in seconds, with the line to add.

    The harness asserts the same thing ("every registered check has a
    planted case here"), but only on a full run, which the quick tier never
    does: on 2026-09-29 a new check was pushed through the quick tier
    without one and the Debut failed 20 minutes in. Both halves of the registry are
    held: an @check in precedent_check.py, and a check script, named by the
    practice whose checked_by claims it. The control is the same tree with
    both cases added.
    """
    import tempfile
    name = 'the changed-files check asks a new check for its planted case'
    engine = ('from x import check\n'
              "@check('zzz-planted', 'tree', 'w', 'b')\ndef a(ctx): return []\n"
              "@check(\n    'zzz-unplanted', 'tree', 'w', 'b')\n"
              'def b(ctx): return []\n')
    harness = "def f():\n    case('zzz-planted', None)\n"
    script = {'local/practices/zzz-claim.md':
                  '---\nslug: zzz-claim\n'
                  'checked_by: local/tools/checks/check_zzclaim.py\n---\n',
              'local/tools/checks/check_zzclaim.py': _FIXTURE_CHECK_HEAD,
              'local/tools/checks/tests/test_zzclaim.sh':
                  '# check_zzclaim.py\nexit 0\n'}
    with tempfile.TemporaryDirectory() as td:
        commit, run = _changed_files_fixture(pathlib.Path(td) / 'missing')
        commit({'tools/precedent_check.py': engine,
                'tools/verify_harness.py': harness, **script})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(pathlib.Path(td) / 'planted')
        commit2({'tools/precedent_check.py': engine,
                 'tools/verify_harness.py': harness +
                     "    case('zzz-unplanted', None)\n"
                     "    case(\n        'zzz-claim', None)\n",
                 **script})
        rc2, out2 = run2()
    cases = [
        ('an @check with no case is refused, by name',
         rc == 1 and 'zzz-unplanted: a registered check with no planted case'
         in out),
        ('a check script is named by the practice that claims it',
         'zzz-claim: a registered check with no planted case' in out),
        ('a check that has its case is not named',
         'zzz-planted: a registered' not in out),
        ('control: with every case planted, it passes', rc2 == 0),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {failure_detail(out, 500)} / {failure_detail(out2, 300)}'))


def check_for_change_runs_the_tests_a_change_reaches():
    """--for-change selects the harness tests a change can reach, and says
    what it does not run. The failure it exists for: a243d9c0 changed
    practice-file-shape, and the one test that would have caught it, two
    seconds long, never ran before staging (2026-10-11).

    One scratch repository, one change per case, read with for_change_plan:
    a check's own body; a helper only another check uses; the decorator
    every check uses; a tools/ module imported two levels down; a check
    script; a harness test and a harness helper; a tools/ module no check
    imports, which a test imports through a helper or runs by its file name
    (2026-10-20: precedent_sync_views.py picked no test), with a lookalike
    file name as its control; a comment between definitions (the control:
    nothing runs); a check covered only by its planted case; and a test over
    the budget, which is named, not run.
    """
    import tempfile
    name = '--for-change runs the harness tests a change reaches'
    engine = (
        'import os\n'
        'CHECKS = {}\n'
        'def check(slug, *a):\n'
        '    def wrap(f):\n'
        '        CHECKS[slug] = f\n'
        '        return f\n'
        '    return wrap\n'
        '\n'
        'def _shared(x):\n'
        '    return x\n'
        '\n'
        '# a comment between definitions\n'
        '\n'
        "@check('zz-alpha', 'tree')\n"
        'def _alpha(ctx):\n'
        '    return []\n'
        '\n'
        "@check('zz-beta', 'tree')\n"
        'def _beta(ctx):\n'
        '    return _shared([])\n'
        '\n'
        "@check('zz-gamma', 'tree')\n"
        'def _gamma(ctx):\n'
        '    import zzsibling\n'
        '    return zzsibling.f()\n'
        '\n'
        "@check('zz-lonely', 'tree')\n"
        'def _lonely(ctx):\n'
        '    return []\n')
    harness = (
        'import precedent_check as pc\n'
        'def _helper():\n'
        '    return 1\n'
        'def check_alpha_direct():\n'
        '    pc._alpha(None)\n'
        'def check_alpha_by_slug():\n'
        "    run('--only', 'zz-alpha')\n"
        'def check_beta():\n'
        '    pc._beta(None)\n'
        'def check_gamma():\n'
        '    _helper()\n'
        "    run('--only', 'zz-gamma')\n"
        'def check_script():\n'
        "    run('tools/checks/check_zzscript.py')\n"
        'def check_slow():\n'
        "    run('--only', 'zz-beta')\n"
        'def check_precedent_check_fires():\n'
        "    case('zz-lonely', None)\n"
        'def _view_helper():\n'
        '    import zzview\n'
        '    return zzview.X\n'
        'def check_view_imported():\n'
        '    _view_helper()\n'
        'def check_view_run():\n'
        "    run('tools/zzview.py')\n"
        'def check_view_lookalike():\n'
        "    run('tools/notzzview.py')\n"
        'def main():\n'
        '    check_alpha_direct()\n'
        '    check_alpha_by_slug()\n')
    times = json.dumps({'default_seconds': 1.0,
                        'seconds': {'check_slow': 500.0}})
    base = {'tools/precedent_check.py': engine, 'tools/verify_harness.py': harness,
            'tools/zzsibling.py': 'import zzdeeper\ndef f():\n    return []\n',
            'tools/zzdeeper.py': 'X = 1\n',
            'tools/zzview.py': 'X = 1\n',
            'tools/checks/check_zzscript.py': 'print(1)\n',
            'tools/harness_check_times.json': times}
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    results = {}
    edits = {
        'alpha body': ('tools/precedent_check.py', '    return []\n\n@check(\'zz-beta\'',
                       '    return [] + []\n\n@check(\'zz-beta\''),
        'shared helper': ('tools/precedent_check.py', '    return x\n', '    return list(x)\n'),
        'decorator': ('tools/precedent_check.py', '        CHECKS[slug] = f\n',
                      '        CHECKS[str(slug)] = f\n'),
        'deeper module': ('tools/zzdeeper.py', 'X = 1\n', 'X = 2\n'),
        'check script': ('tools/checks/check_zzscript.py', 'print(1)\n', 'print(2)\n'),
        'module a test uses': ('tools/zzview.py', 'X = 1\n', 'X = 2\n'),
        'harness test': ('tools/verify_harness.py', "    pc._beta(None)\n",
                         "    pc._beta(None)\n    pass\n"),
        'harness helper': ('tools/verify_harness.py', '    return 1\n', '    return 2\n'),
        'main call': ('tools/verify_harness.py', '    check_alpha_by_slug()\n',
                      '    check_alpha_by_slug()\n    check_script()\n'),
        'comment': ('tools/precedent_check.py', '# a comment between definitions\n',
                    '# a comment, reworded, between definitions\n'),
        'lonely': ('tools/precedent_check.py', "def _lonely(ctx):\n    return []\n",
                   "def _lonely(ctx):\n    return [] + []\n"),
    }
    with tempfile.TemporaryDirectory() as td:
        for label, (rel, old, new) in edits.items():
            repo = pathlib.Path(td) / re.sub(r'\W', '-', label)
            repo.mkdir()

            def git(*a):
                return subprocess.run(['git', '-C', str(repo), '-c',
                                       'core.hooksPath=/dev/null', *a],
                                      capture_output=True, text=True, env=env)
            git('init', '-q', '-b', 'main')
            for r_, text in base.items():
                (repo / r_).parent.mkdir(parents=True, exist_ok=True)
                (repo / r_).write_text(text, encoding='utf-8')
            git('add', '-A'); git('commit', '-qm', 'base')
            since = git('rev-parse', 'HEAD').stdout.strip()
            text = (repo / rel).read_text(encoding='utf-8')
            assert old in text, (label, old)
            (repo / rel).write_text(text.replace(old, new, 1), encoding='utf-8')
            git('commit', '-qam', label)
            results[label] = for_change_plan(repo, since)
    run = lambda k: set(results[k]['run'])
    cases = [
        ("a check's own body runs the tests that call it or name its slug",
         run('alpha body') == {'check_alpha_direct', 'check_alpha_by_slug'}),
        ('a helper one check uses runs that check\'s tests, the slow one named '
         'over the budget, not run',
         run('shared helper') == {'check_beta'}
         and results['shared helper']['deferred'] == ['check_slow']),
        ('the decorator every check uses reaches every check',
         set(results['decorator']['slugs'])
         == {'zz-alpha', 'zz-beta', 'zz-gamma', 'zz-lonely'}),
        ('a module imported two levels down reaches the check that imports it',
         results['deeper module']['slugs'] == ['zz-gamma']
         and run('deeper module') == {'check_gamma'}),
        ('a check script runs the test that names its file',
         run('check script') == {'check_script'}),
        ('a module no check imports runs the tests that import or run it, '
         'not the one that runs a lookalike',
         run('module a test uses') == {'check_view_imported', 'check_view_run'}),
        ('a changed harness test runs itself', run('harness test') == {'check_beta'}),
        ('a changed harness helper runs the tests that call it',
         run('harness helper') == {'check_gamma'}),
        ('a call added to main() runs the test it calls',
         run('main call') == {'check_script'}),
        ('control: a comment between definitions runs nothing and maps nothing',
         not results['comment']['run'] and not results['comment']['slugs']
         and not results['comment']['unmapped']),
        ('a check tested only by its planted case is named, not run',
         results['lonely']['planted_only'] == ['zz-lonely']
         and not results['lonely']['run']),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else
                              ' -- ' + json.dumps(results, default=str)[:1500]))


def check_upstream_edits_need_an_answer():
    """practice: upstream-bug-stops-here, enforced (Morgan, 2026-10-17,
    "Act"). An upstream-owned file -- an engine file or hook
    ENGINE_MANIFEST.json records, a shipped file MANIFEST.json records --
    that differs from what was delivered is a finding until precedent.json
    records its answer; the edit-time hook refuses the edit before it
    happens, with the three answers in its reason.

    Controls: an untouched delivery and this repository's own file are
    never named; each malformed answer is named for what it lacks; an
    answer for a file that matches again is stale; and the hook lets every
    other edit through.
    """
    import shutil, tempfile
    name = 'an edit to an upstream-owned file needs its recorded answer'
    sys.path.insert(0, str(ROOT / 'tools'))
    import upstream_edits as ue
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-upstream-edits-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        engine_file = repo / 'tools' / 'engine_thing.py'
        engine_file.write_text('X = 1\n', encoding='utf-8')
        shipped = repo / 'tools' / 'shipped_thing.py'
        shipped.write_text('Y = 1\n', encoding='utf-8')
        own = repo / 'tools' / 'our_own.py'
        own.write_text('Z = 1\n', encoding='utf-8')
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps({
            'sha256': {'engine_thing.py': hashlib.sha256(
                engine_file.read_bytes()).hexdigest()}}), encoding='utf-8')
        (repo / 'MANIFEST.json').write_text(json.dumps({'ships': [{
            'path': 'tools/shipped_thing.py', 'source': 'precedent-shared-x',
            'sha256_16': hashlib.sha256(shipped.read_bytes()).hexdigest()[:16]}]}),
            encoding='utf-8')
        cfg = repo / 'precedent.json'

        def answers(entries):
            cfg.write_text(json.dumps({'upstream_edits': entries} if entries
                                      is not None else {}), encoding='utf-8')
        answers(None)
        cases.append(('control: an untouched delivery has no finding',
                      ue.findings(repo) == [], str(ue.findings(repo))))
        cases.append(('control: editing this repository\'s own file is allowed',
                      ue.guard(own, repo) is None, ''))
        why = ue.guard(shipped, repo) or ''
        cases.append(('editing a shipped file is refused before the edit, with '
                      'the three answers', 'upstream-bug-stops-here' in why
                      and 'owed-upstream' in why and 'local-need' in why, why[:200]))
        engine_file.write_text('X = 2\n', encoding='utf-8')
        shipped.write_text('Y = 2\n', encoding='utf-8')
        found = ue.findings(repo)
        cases.append(('an edited engine file and an edited shipped file are '
                      'each a finding until answered',
                      len(found) == 2 and all('no recorded answer' in f
                                              for f in found), str(found)[:400]))
        answers({'tools/shipped_thing.py': {'answer': 'owed-upstream',
                                            'detail': 'carried up later'}})
        cases.append(('"owed-upstream" with no link is named for the link',
                      any('needs the link' in f for f in ue.findings(repo)), ''))
        answers({'tools/shipped_thing.py': {'answer': 'local-need',
                                            'detail': 'this repo pins Y'}})
        cases.append(('"local-need" with no quoted, dated approval is named for it',
                      any('quoted, with the date' in f for f in ue.findings(repo)), ''))
        answers({'tools/shipped_thing.py': {
                    'answer': 'owed-upstream',
                    'detail': 'https://example.com/set/pull/7'},
                 'tools/engine_thing.py': {
                    'answer': 'local-need', 'detail': 'X must be 2 here because ...',
                    'approved': 'Morgan, 2026-10-17: "yes, keep it"'}})
        cases.append(('with both answered, nothing is named',
                      ue.findings(repo) == [], str(ue.findings(repo))))
        cases.append(('...and the guard lets an answered file be edited',
                      ue.guard(shipped, repo) is None, ''))
        engine_file.write_text('X = 1\n', encoding='utf-8')
        cases.append(('an answer for a file that matches again is stale',
                      any('tools/engine_thing.py: has a "upstream_edits" entry '
                          'but matches' in f for f in ue.findings(repo)), ''))
        # The real hook, end to end, in the consumer.
        answers(None)
        shutil.copy2(ROOT / 'tools' / 'upstream_edits.py', repo / 'tools')
        hook = ROOT / 'tools' / 'precedent-paths.sh'
        if shutil.which('jq'):
            def run_hook(target):
                r = subprocess.run(['bash', str(hook)], capture_output=True,
                                   text=True, timeout=60, input=json.dumps(
                                       {'tool_input': {'file_path': str(target)}}),
                                   env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
                return r.returncode, r.stdout
            rc, out = run_hook(shipped)
            cases.append(('the edit-time hook denies an edit to an unanswered '
                          'shipped file, giving the reason',
                          rc == 0 and '"permissionDecision": "deny"' in out
                          and 'upstream-bug-stops-here' in out, out[:300]))
            rc, out = run_hook(own)
            cases.append(('control: the hook lets an edit to this repository\'s '
                          'own file through', rc == 0 and 'deny' not in out, out[:300]))
        # 2026-10-20: a file a set delivers untracked at session start
        # (.precedent/session_ships.json) is replaced at the next one; an
        # edit there is refused, naming the repository it belongs in, and no
        # recorded answer lets it through.
        ships = repo / 'tools' / 'ladder' / 'zz_shipped.py'
        ships.parent.mkdir(parents=True)
        ships.write_text('W = 1\n', encoding='utf-8')
        (repo / '.precedent').mkdir()
        (repo / '.precedent' / 'session_ships.json').write_text(json.dumps({'files': {
            'tools/ladder/zz_shipped.py': {'sha256_16': '0' * 16, 'practice': 'zz',
                                           'set': 'precedent-shared-zz'}}}),
            encoding='utf-8')
        home_copy = tmp / 'precedent-shared-zz' / 'tools' / 'ladder' / 'zz_shipped.py'
        home_copy.parent.mkdir(parents=True)
        home_copy.write_text('W = 1\n', encoding='utf-8')
        why = ue.guard(ships, repo) or ''
        cases.append(('THE DISCRIMINATING CASE: an edit to a session-shipped copy is '
                      'refused, naming the set and its own file',
                      'precedent-shared-zz' in why and str(home_copy) in why
                      and 'next one' in why, why[:300]))
        answers({'tools/ladder/zz_shipped.py': {
            'answer': 'local-need', 'detail': 'tried to keep it',
            'approved': 'Morgan, 2026-10-20: "yes"'}})
        cases.append(('...and an answer in precedent.json does not let it through',
                      bool(ue.guard(ships, repo)), ''))
        answers(None)
        cases.append(('control: this repository\'s own file beside it is still allowed',
                      ue.guard(own, repo) is None, ''))
        if shutil.which('jq'):
            rc, out = run_hook(ships)
            cases.append(('the edit-time hook denies the edit, with that reason',
                          rc == 0 and '"permissionDecision": "deny"' in out
                          and 'precedent-shared-zz' in out, out[:300]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_set_independence_reads_tests_and_rules():
    """The set-independence inventory (precedent_check.py's
    enforcement-lives-with-its-practice) reads BestPractice's tests and
    universal rules for a set's names, not only the engine's code, and
    leaves comments alone (Morgan, 2026-10-17: "we had lots of tests for
    them and rules regarding them in best practice. And it should never be
    like that").

    Planted inputs straight into its scanners: a test's string literal
    naming a set's practice, a docstring naming one (a comment: not a
    finding), a universal rule linking one, a set named inside a message,
    and a name kept on purpose."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    name = 'the set-independence inventory reads tests and universal rules, not comments'
    set_only = {'zz-set-rule': 'zz-set'}
    names = {'zz-set'}
    wanted = set(set_only) | names
    cases = []
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / 'test_like.py'
        f.write_text('"""A docstring naming zz-set-rule and zz-set."""\n'
                     'def t():\n    """zz-set-rule in a docstring."""\n'
                     "    return 'zz-set-rule'\n", encoding='utf-8')
        hits = pc._set_names_in_strings(f, wanted, set_only, names)
        cases.append(('a string literal naming a set\'s practice is found',
                      hits == {'zz-set-rule'}, hits))
        f.write_text('"""Only a docstring: zz-set-rule, zz-set."""\n', encoding='utf-8')
        hits = pc._set_names_in_strings(f, wanted, set_only, names)
        cases.append(('control: a docstring is a comment, never a finding', not hits, hits))
        f.write_text("MSG = 'install zz-set first'\nOK = 'zz-settings'\n", encoding='utf-8')
        hits = pc._set_names_in_strings(f, wanted, set_only, names)
        cases.append(('a set named as a whole word inside a message is found, '
                      'and a longer word is not', hits == {'zz-set'}, hits))
    text = 'Do it as [the rule](zz-set-rule.md) says; see practices/other.md.'
    hits = pc._set_names_in_text(text, set_only, names)
    cases.append(('a universal rule linking a set\'s practice is found',
                  hits == {'zz-set-rule'}, hits))
    cases.append(('a name kept on purpose carries the words that kept it',
                  all('Morgan, 20' in w for w in pc._SET_NAMES_KEPT.values()),
                  pc._SET_NAMES_KEPT))
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_caused_by_this_push_reads_advisory_findings():
    """The "this push caused them" note compares with the tree before the
    push, and reads that run's findings under ADVISORY as well as VIOLATION;
    a check the earlier tree could not run is never held against the push
    (2026-10-17: an advisory check had 24 to 38 findings in untouched files
    named as caused by every push, because the earlier run's ADVISORY block
    read as empty).
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    name = 'the caused-by-this-push note reads the earlier run fairly'
    adv = ('ADVISORY   zz-slug — findings below do not fail this run\n'
           '    a/b.md: an old finding\n  the rule:\n    text\n')
    vio = ('VIOLATION  zz-slug\n    a/b.md:12: an old finding\n  the rule:\n')
    skip = 'SKIPPED    zz-slug — no record here\n'
    other = 'VIOLATION  zz-slug-longer\n    x.md: not this one\n  the rule:\n'
    cases = [
        ('an advisory block\'s findings are read', pc._findings_in_output(adv, 'zz-slug')
         == {'a/b.md: an old finding'}),
        ('a violation block\'s are, with line numbers dropped',
         pc._findings_in_output(vio, 'zz-slug') == {'a/b.md: an old finding'}),
        ('a skipped check is unknown, not empty', pc._findings_in_output(skip, 'zz-slug')
         is None),
        ('control: a longer slug that starts the same is not read as this one',
         pc._findings_in_output(other, 'zz-slug') == set()),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_quick_tier_is_closed():
    """Nothing joins the checks run before a push without the person's own
    words (Morgan, 2026-10-16, strength: decided: "LET'S BAN ALL NEW TESTS
    BEFOREHAND EXCEPT WHEN EXPLICITLY DIRECTLY VERBALLY AUTHORIZED").

    THE DRIFT IT STOPS: from 2026-10-11 every landing ran the harness tests
    a change reaches, inside a minute's budget
    (spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md); with a timing list a
    hundred tests out of date that minute became two, and the quick check
    took over three (spec/TESTS_RUN_AT_THE_DEBUT_PLAN.md). So:

    * BASIC_CHECKS is exactly the names below. Changing this set is a
      change to the quick tier -- make it only with the person's words
      asking for that check before a push, quoted with their date in
      precedent_push_check.BASIC_CHECKS_APPROVED;
    * every approval quotes someone's words and carries a date, and one
      added after the closing carries its time in seconds;
    * the per-file step (changed_files_check) starts no test, harness or
      practice check, and nothing in the push check runs the practice
      checks limited to a change (--changed-files-only) before a push.
    The control: the same scanner flags a planted test run.
    """
    import inspect
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_push_check as ppc
    name = 'the quick tier is closed: nothing joins it without the person\'s words'
    closed = {'build_views', 'ci_workflows', 'commit_author', 'commit_dates',
              'doc_lint', 'generated_files', 'leak_gate', 'leak_gate_commits',
              'light_check', 'practice_export_loop', 'rename_links',
              'scrub_gate', 'session_trailer', 'views_sync'}
    import ast, textwrap

    def runs_tests(src):
        """-> what each subprocess call in `src` starts that is a test or a
        check run: a call's own arguments, never a comment or a message."""
        found = []
        for node in ast.walk(ast.parse(textwrap.dedent(src))):
            if not (isinstance(node, ast.Call) and getattr(node.func, 'attr', '')
                    in ('run', 'Popen', 'check_output', 'call')):
                continue
            words = [n.value for n in ast.walk(node) if isinstance(n, ast.Constant)
                     and isinstance(n.value, str)]
            names = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]
            if any(w.endswith(('verify_harness.py', 'precedent_check.py',
                               'run_all.sh')) or w == '--changed-files-only'
                   for w in words) or ('bash' in words and 'test' in names):
                found.append(ast.get_source_segment(textwrap.dedent(src), node)
                             or 'a call')
        return found
    per_file = inspect.getsource(ppc.changed_files_check) \
        + '\n' + inspect.getsource(ppc._check_script_tests)
    whole = (ROOT / 'tools' / 'precedent_push_check.py').read_text(encoding='utf-8')
    limited = [n for n in ast.walk(ast.parse(whole)) if isinstance(n, ast.Constant)
               and n.value == '--changed-files-only']
    unquoted = [k for k, (words, _s) in ppc.BASIC_CHECKS_APPROVED.items()
                if not (re.search(r'\b20\d\d-\d\d-\d\d\b', words) and '"' in words)]
    untimed = [k for k, (_w, secs) in ppc.BASIC_CHECKS_APPROVED.items()
               if k not in closed and not isinstance(secs, (int, float))]
    cases = [
        ('the basic tier is exactly the closed list -- before adding one, '
         'tell the person its time and urge the Debut instead; only their '
         'own words asking for it before a push let it in, quoted with a '
         'date and its seconds in BASIC_CHECKS_APPROVED and added here '
         '(practice: quick-tier-is-closed)',
         ppc.BASIC_CHECKS == closed,
         f'added: {sorted(ppc.BASIC_CHECKS - closed)}, '
         f'removed: {sorted(closed - ppc.BASIC_CHECKS)}'),
        ('every entry quotes someone\'s words, with a date', not unquoted,
         ', '.join(unquoted)),
        ('every entry added after the closing carries its time in seconds',
         not untimed, ', '.join(untimed)),
        ('the per-file step starts no test, harness or practice check',
         not runs_tests(per_file), ', '.join(runs_tests(per_file))),
        ('nothing runs the change-limited practice checks before a push',
         not limited, f'{len(limited)} use(s) of --changed-files-only'),
        ('control: the scanner flags a planted harness run',
         bool(runs_tests("subprocess.run([sys.executable, 'tools/verify_harness.py'])"))
         and bool(runs_tests("subprocess.run(['bash', test], cwd=root)")), ''),
        ('control: a comment or message naming a test runs nothing',
         not runs_tests("x = 'add it to tools/verify_harness.py'  # run_all.sh\n"),
         ''),
    ]
    bad = [f'{n} ({d})' for n, ok, d in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_verify_flags_missing_session_practices_ceiling():
    """A set that wires the universal-catalogue hook genuinely renders and
    injects .precedent/SESSION_PRACTICES.md into every session
    (spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md). A set that separately
    opted into session-load-budget by keeping its own
    tools/session_load_budgets.json has therefore asked for every such
    surface to carry a ceiling -- and until 2026-09-22, verify() never
    checked that the two agreed. precedent-shared-working-style hit exactly
    this: a PR turned the hook on and added the CLAUDE.md surface to the
    registry, not this one, and the file the hook makes real sat unmeasured
    and uncapped across two merges (practice: session-load-budget).

    Four cases (practice: control-asserts-which-failure -- a check that
    cannot fail on the planted gap, and cannot pass on its absence, is not
    established): the registry with the gap is flagged BY NAME; the same
    registry with the entry present is not (the positive control that
    proves the finding is about the missing entry and not the file's mere
    presence); a set with no registry at all is not flagged (it never
    opted in, and precedent_check.py's own session-load-budget check
    already reports NotApplicable there -- this is not a second, competing
    way to demand one); and a set with the registry but the hook NOT wired
    is not flagged (nothing here claims the surface loads, so there is
    nothing to have missed)."""
    import tempfile
    import precedent_bootstrap_source as pbs

    def _settings(wired):
        cmds = (['python3 tools/precedent_session_practices.py --repo .']
                if wired else ['python3 tools/precedent_check.py'])
        return json.dumps({'hooks': {'SessionStart': [
            {'hooks': [{'type': 'command', 'command': c} for c in cmds]}]}})

    def _make(root, wired, budgets):
        (root / '.claude').mkdir(parents=True, exist_ok=True)
        (root / '.claude' / 'settings.json').write_text(
            _settings(wired), encoding='utf-8')
        (root / 'tools').mkdir(parents=True, exist_ok=True)
        if budgets is not None:
            (root / 'tools' / 'session_load_budgets.json').write_text(
                json.dumps(budgets), encoding='utf-8')
        return [m for m in pbs.verify('team', root)
                if '.precedent/SESSION_PRACTICES.md' in m
                and 'session_load_budgets.json' in m]

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 1. THE GAP ITSELF: hook wired, registry declares surfaces, the one
        # that matters is missing.
        gapped = {'surfaces': {'CLAUDE.md': {'ceiling': 200}}}
        found = _make(tmp / 'gapped', True, gapped)
        cases.append((f'wired hook + a registry missing the entry is '
                      f'flagged (got {found})', len(found) == 1))

        # 2. THE POSITIVE CONTROL: same wiring, the entry present -- proves
        # case 1 fires on the missing entry and not on the file's presence.
        capped = {'surfaces': {'CLAUDE.md': {'ceiling': 200},
                               '.precedent/SESSION_PRACTICES.md':
                               {'ceiling': 6700}}}
        found = _make(tmp / 'capped', True, capped)
        cases.append((f'wired hook + a registry that already declares the '
                      f'entry is clean (got {found})', not found))

        # 3. NO OPT-IN: no registry at all is not a second gate on top of
        # precedent_check.py's own NotApplicable for a set that never opted
        # into session-load-budget.
        found = _make(tmp / 'no-registry', True, None)
        cases.append((f'wired hook + no registry at all is not flagged '
                      f'(got {found})', not found))

        # 4. HOOK NOT WIRED: a registry with the gap is not flagged where
        # nothing here claims the surface actually loads.
        found = _make(tmp / 'unwired', False, gapped)
        cases.append((f'a registry with the gap but the hook not wired is '
                      f'not flagged (got {found})', not found))

    failed = [n for n, ok in cases if not ok]
    check(f'verify() flags a set whose registry is missing the '
          f'.precedent/SESSION_PRACTICES.md ceiling once the '
          f'universal-catalogue hook is wired ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_local_engine_edit_saves_a_prompt_please():
    """A consumer may edit an engine file when the fix cannot wait, and then
    must keep an open todo/ item naming it that links the upstream pull
    request or saves a Prompt Please (Morgan, 2026-10-08; practice:
    upstream-fix, point 7). Planted on a consumer-shaped copy: an engine
    file whose text no longer matches tools/ENGINE_MANIFEST.json."""
    import shutil, tempfile, hashlib, json as _json
    name = 'a local edit to an engine file needs a saved Prompt Please or a linked fix'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-local-edit-'))
    cases = []
    try:
        repo = tmp / 'repo'
        shutil.copytree(ROOT / 'tools', repo / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        (repo / 'precedent.json').write_text(_json.dumps(
            {'format_version': 1, 'visibility': 'private', 'sources': []}), encoding='utf-8')
        f = repo / 'tools' / 'glossary_terms.json'
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(_json.dumps({
            'kind': 'consumer',
            'sha256': {'glossary_terms.json': hashlib.sha256(f.read_bytes()).hexdigest()}}),
            encoding='utf-8')
        (repo / 'todo').mkdir()
        # In force here, as in every consumer that materializes the catalogue.
        (repo / 'practices').mkdir()
        shutil.copy2(ROOT / 'practices' / 'upstream-fix.md', repo / 'practices')

        def run():
            r = subprocess.run([sys.executable, str(repo / 'tools' / 'precedent_check.py'),
                                '--only', 'upstream-fix'], capture_output=True, text=True,
                               cwd=str(repo), env=dict(os.environ,
                               PRECEDENT_USER_CONFIG=str(tmp / 'none.json')))
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('unedited, it passes', rc == 0, failure_detail(out, 300)))
        f.write_text(f.read_text(encoding='utf-8') + ' ', encoding='utf-8')
        rc, out = run()
        cases.append(('edited with nothing handed upstream, it is refused, naming '
                      'the file and both ways out', rc != 0
                      and 'tools/glossary_terms.json' in out and 'Prompt Please' in out
                      and 'upstream_fix.py' in out, failure_detail(out, 500)))
        item = repo / 'todo' / 'todo-2026-10-08-fix-glossary-upstream.md'
        item.write_text('---\nstatus: open\n---\n# Fix upstream\n\nPatched '
                        'tools/glossary_terms.json here.\n\n## Prompt Please\n\n'
                        'Root it in BestPractice.\n\n```\nFix the term list.\n```\n',
                        encoding='utf-8')
        rc, out = run()
        cases.append(('with an open item naming it and saving a Prompt Please, it '
                      'passes', rc == 0, failure_detail(out, 400)))
        item.write_text(item.read_text(encoding='utf-8').replace('status: open', 'status: done'),
                        encoding='utf-8')
        rc, out = run()
        cases.append(('a closed item does not count', rc != 0, failure_detail(out, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f' ({c[2]})' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_leftover_pack_is_flagged_after_migration():
    """A repo that migrated but kept the old practice pack gets told so.

    Both retirement checks were opt-in: migration-scrubs-vocabulary's word
    scan fires only once a repo writes retired_vocabulary.json, and
    decommission-deletes-files only once it records a retirement. A repo that
    migrated WITHOUT running spec/MIGRATING_EXISTING_INSTALLS.md's step 5
    declares neither, so both stayed silent and the dead tree sat there --
    a second, unsynced copy of rules that now live in a team or individual
    source. Asked on 2026-09-07 whether migration deletes the old personal
    pack: step 5 does, and nothing was watching the repos that migrated
    before it existed.

    The case that must NOT fire is the one that makes this safe to ship. The
    pack mechanism is still supported for a repo that has not migrated --
    that document's own "When this applies" says so -- so the check is
    scoped to a repo carrying a precedent.json, and a pack whose upstream
    never split can declare `kept_after_migration` and be left alone.

    practice: control-asserts-which-failure -- every case reads the message.
    The first version of this fixture omitted practices/, so the check was
    gated off as "not in force here" and SKIPPED; scored on exit code alone
    all five planted cases would have read as "correctly not flagged".
    """
    import tempfile, shutil as _shutil
    chk = ROOT / 'tools' / 'precedent_check.py'
    prac = PRACTICES_DIR / 'migration-scrubs-vocabulary.md'
    if not (chk.exists() and prac.exists()):
        not_applicable('a leftover pre-migration pack is flagged',
                       'precedent_check.py or the practice file is absent here')
        return

    def _repo(base, migrated, pack, manifest='{}'):
        (base / 'process' / 'upstream' / 'tools').mkdir(parents=True)
        (base / 'practices').mkdir()
        subprocess.run(['git', '-C', str(base), 'init', '-q'],
                       capture_output=True)
        _shutil.copy2(chk, base / 'process' / 'upstream' / 'tools')
        # fixture-owns-its-state: precedent_check.py imports precedent_time at
        # module scope (practice: timestamps-carry-offset).
        _shutil.copy2(ROOT / 'tools' / 'precedent_time.py',
                      base / 'process' / 'upstream' / 'tools')
        _shutil.copy2(ROOT / 'tools' / 'declared_base_branch.py',
                      base / 'process' / 'upstream' / 'tools')
        _shutil.copy2(ROOT / 'tools' / 'generated_blocks.py',
                      base / 'process' / 'upstream' / 'tools')
        _shutil.copy2(prac, base / 'practices')
        for d in ('tools', 'process/upstream/tools'):
            sp_dst = base / d
            sp_dst.mkdir(parents=True, exist_ok=True)
            src = ROOT / 'tools' / 'split_practices.py'
            if src.exists():
                _shutil.copy2(src, sp_dst)
        if migrated:
            (base / 'precedent.json').write_text(
                '{"sources":[{"level":"universal","name":"precedent",'
                '"path":"."}]}', encoding='utf-8')
        if pack:
            (base / 'process' / 'personal').mkdir()
            (base / 'process' / 'personal' / 'RULES.md').write_text(
                '# a rule\n', encoding='utf-8')
            (base / 'process' / 'manifest_personal.json').write_text(
                manifest, encoding='utf-8')
        r = subprocess.run(
            [sys.executable,
             str(base / 'process' / 'upstream' / 'tools' / 'precedent_check.py'),
             '--only', 'migration-scrubs-vocabulary'],
            capture_output=True, text=True, cwd=str(base), timeout=180)
        return r.stdout + r.stderr

    MARK = 'pre-migration practice-pack mechanism'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        out = _repo(tmp / 'a', migrated=True, pack=True)
        cases.append(('a migrated repo with a leftover pack is flagged',
                      MARK in out))
        cases.append(('and names the manifest',
                      'process/manifest_personal.json' in out))
        cases.append(('and names the tree it found', 'process/personal' in out))
        cases.append(('and prescribes the retire audit, not a hand delete',
                      'precedent_decommission.py' in out))
        cases.append(('and it counts as a violation', '1 violated' in out))

        out = _repo(tmp / 'b', migrated=False, pack=True)
        cases.append(('an UNMIGRATED repo with a pack is NOT flagged -- that '
                      'mechanism is still supported', MARK not in out))

        out = _repo(tmp / 'c', migrated=True, pack=False)
        cases.append(('a migrated repo with no pack is not flagged',
                      MARK not in out))

        out = _repo(tmp / 'd', migrated=True, pack=True,
                    manifest='{"kept_after_migration":"upstream never split"}')
        cases.append(('a declared kept_after_migration pack stands down',
                      MARK not in out))

        out = _repo(tmp / 'e', migrated=True, pack=True,
                    manifest='not json at all')
        cases.append(('an unparseable pack manifest is still flagged -- '
                      'unreadable is not absent', MARK in out))

        # 2026-10-28: copy-in records a copied set at the old pack's own
        # file name; a consumer's main went red on two of them.
        def _copied(base, entry, manifest='{}', carries=None):
            _repo(base, migrated=True, pack=False)
            (base / 'precedent.json').write_text(json.dumps({'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': '.'}, entry]}),
                encoding='utf-8')
            if carries is not None:
                (base / entry['path']).mkdir(parents=True, exist_ok=True)
                (base / entry['path'] / 'precedent-source.json').write_text(
                    json.dumps({'carries': carries}), encoding='utf-8')
            for n in ['zz-set'] + [c['name'] for c in carries or []]:
                (base / 'process' / f'manifest_{n}.json').write_text(
                    manifest, encoding='utf-8')
            r = subprocess.run(
                [sys.executable, str(base / 'process' / 'upstream' / 'tools'
                                     / 'precedent_check.py'),
                 '--only', 'migration-scrubs-vocabulary'],
                capture_output=True, text=True, cwd=str(base), timeout=180)
            return r.stdout + r.stderr
        copied = {'level': 'shared', 'name': 'zz-set', 'path': 'process/zz-set',
                  'vendored': True}
        out = _copied(tmp / 'f', copied,
                      carries=[{'name': 'zz-inner', 'path': 'inner'}])
        cases.append(('a copied-in set\'s manifest, and one a copy carries, '
                      'are not leftover packs', MARK not in out, ))
        out = _copied(tmp / 'g', dict(copied, vendored=False))
        cases.append(('CONTROL: the same manifest with no copy-in declared is '
                      'still flagged', MARK in out and 'manifest_zz-set' in out))
        out = _copied(tmp / 'h', dict(copied, name='zz-other'),
                      manifest='{"upstream": {"vendored_at": "process/zz-set"}}')
        cases.append(('a copied-in set recorded by its tree, under another '
                      'file name, is not a leftover pack', MARK not in out))

    failed = [c[0] for c in cases if not c[1]]
    check(f'a leftover pre-migration practice pack is flagged after migration '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_very_deep_check_honours_not_binding_for_other_sources_checks():
    """The very deep check's "other sources' checks" report honours this
    repo's `not_binding` the way precedent_check.py does: a declared slug is
    not run and is reported EXEMPT with its reason, never dropped, and a
    `severity: blocking` practice cannot be exempted (very deep check,
    2026-09-28: the report ignored not_binding, so an exemption the repo had
    written down still surfaced as a finding)."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-not-binding-'))
    cases = []
    try:
        root, src = tmp / 'root', tmp / 'shared'
        for d in (root / 'practices', src / 'practices',
                  src / 'tools' / 'checks'):
            d.mkdir(parents=True)

        def practice(slug, severity=None):
            name = 'check_' + slug.replace('-', '_') + '.py'
            sev = f'severity: {severity}\n' if severity else ''
            (src / 'practices' / f'{slug}.md').write_text(
                f'---\nslug: {slug}\nstatus: active\n{sev}'
                f'checked_by: tools/checks/{name}\n---\n\n## Rule\n\nX.\n',
                encoding='utf-8')
            (src / 'tools' / 'checks' / name).write_text(
                'import sys\nprint("VIOLATION:"); print("zz found it")\n'
                'sys.exit(1)\n', encoding='utf-8')

        practice('zz-exempted')
        practice('zz-blocking', severity='blocking')
        practice('zz-plain')
        (root / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'not_binding': [
                {'slug': 'zz-exempted', 'reason': 'zz does not apply here'},
                {'slug': 'zz-blocking', 'reason': 'zz tries anyway'}]}),
            encoding='utf-8')
        sources = [{'level': 'universal', 'name': 'precedent',
                    'path': str(root)},
                   {'level': 'shared', 'name': 'zz-shared', 'path': str(src)}]
        rows, note = vdc._source_check_scripts(root, sources)
        by = {r[1]: r for r in rows}
        cases.append(('THE CASE: a not_binding slug is reported EXEMPT with '
                      'its reason, not run',
                      by.get('zz-exempted', ('',))[0] == 'EXEMPT'
                      and 'zz does not apply here' in by['zz-exempted'][3],
                      f'{note} {rows!r}'))
        cases.append(('a severity: blocking practice cannot be exempted -- '
                      'it still runs', by.get('zz-blocking', ('',))[0]
                      == 'VIOLATION', repr(rows)))
        cases.append(('CONTROL: an undeclared practice still runs',
                      by.get('zz-plain', ('',))[0] == 'VIOLATION',
                      repr(rows)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check honours not_binding for other sources\' '
          f'checks ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_precedent_check_degrades_in_a_source_set():
    """precedent_check.py entered ENGINE_FILES on 2026-09-07, so it now runs
    inside SOURCE sets -- which deliberately do NOT carry its four optional
    dependencies. doc_lint.py, doc_sync.py, title_case.py and
    precedent_resolve.py are CONSUMER_ENGINE_FILES only, because a source set
    resolves no catalogue and vendors no upstream tree.

    The property under test is that this degrades HONESTLY: a check whose
    module is absent reports SKIPPED, never ERRORED (which reads as a broken
    tool rather than an absent one) and never a silent pass. Two of the four
    already did that; title_case and, in _source_naming, precedent_resolve
    were bare imports and are why this exists.

    The fixture is built from THIS WORKING TREE, by copying ENGINE_FILES out
    of tools/ by hand -- deliberately not via precedent_bootstrap_source.py,
    which seeds from a committed git ref (that is its own guarantee: no
    checkout, no HEAD movement). Seeding from the ref would make this check
    permanently one commit behind the engine change it is meant to test, and
    it would have passed for the wrong reason on the very commit that
    introduced the guards."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-srcset-check-'))
    cases = []
    try:
        dest = tmp / 'srcset'
        (dest / 'tools').mkdir(parents=True)
        (dest / 'practices').mkdir()
        for name in pve.ENGINE_FILES:
            src = ROOT / 'tools' / name
            if src.is_file():
                shutil.copy2(src, dest / 'tools' / name)
        # routing_scope.json is vendored into every kind but is NOT in
        # ENGINE_FILES, because the vendoring tool writes a TRIMMED copy
        # rather than a byte-identical one (see precedent_vendor_engine.py's
        # module docstring). Copying it verbatim is fine here: this fixture
        # tests import degradation, and only the file's PRESENCE matters --
        # omitting it made vendored-engine-file-refs-resolve fire on
        # build_views.py, a fixture defect masquerading as a finding.
        shutil.copy2(ROOT / 'tools' / 'routing_scope.json',
                     dest / 'tools' / 'routing_scope.json')

        cases.append(('precedent_check.py is in ENGINE_FILES, so a source set '
                      'gets it at all',
                      'precedent_check.py' in pve.ENGINE_FILES, ''))
        cases.append(('and it landed in the fixture',
                      (dest / 'tools' / 'precedent_check.py').is_file(), ''))

        # Negative control on the fixture itself: if any optional module HAD
        # come along, every assertion below would pass for the wrong reason,
        # because the imports would simply succeed.
        # precedent_resolve.py was in this tuple until 2026-09-13, and
        # title_case.py until 2026-09-19 -- both are now in ENGINE_FILES on
        # purpose (precedent_resolve.py: shape 3, spec/SOURCE_SET_PROSE_GAP.md;
        # title_case.py: build_todo_index.py imports it at module level and
        # moved into the shared list the same day, see
        # precedent_vendor_engine.py's ENGINE_FILES entry) -- so a source set
        # HAS both now and neither is one of the modules whose absence this
        # fixture is about. Leaving either here made the control assert the
        # opposite of the shipped boundary, which is how both moves were
        # caught.
        # doc_lint.py LEFT THIS TUPLE on 2026-09-21, for the same reason
        # precedent_resolve.py and title_case.py did before it: a source set
        # has it now. The Markdown lint left GitHub Actions that day and
        # .claude/hooks/doc-lint-gate.sh became the only thing checking
        # Markdown before a shared branch -- and a set was receiving the
        # hook without the linter, so the hook's own missing-file guard
        # fired on every commit and it gated nothing. Leaving doc_lint.py
        # here would make this control assert the opposite of the shipped
        # boundary, which is exactly how the three earlier moves were
        # caught.
        optional = ('doc_sync.py',)
        absent = [m for m in optional if not (dest / 'tools' / m).is_file()]
        cases.append(('the consumer-only module(s) are genuinely absent, so '
                      'the skips below are real', len(absent) == len(optional),
                      f'absent: {absent}'))
        cases.append(('and precedent_resolve.py IS present, which is what '
                      'lets a source set read the universal catalogue at all',
                      (dest / 'tools' / 'precedent_resolve.py').is_file(), ''))

        # Put the two practices whose checks import the previously-bare
        # modules IN FORCE here, or the runner skips them for "practice not
        # in force" before either import is ever attempted -- and the guards
        # would go untested while the check reported success.
        # Swapped twice for the same reason, and the reason is the point:
        # 'headline-capitalization' went on 2026-09-19 when title_case.py
        # moved into ENGINE_FILES, replaced by 'acronyms-glossary' for its
        # doc_lint.py import; 'acronyms-glossary' goes on 2026-09-21 now
        # that doc_lint.py has moved too. 'computed-numbers-in-scripts'
        # imports doc_sync.py, which is still consumer-only, so it is the
        # one that still demonstrates the skip.
        for slug in ('computed-numbers-in-scripts', 'source-naming'):
            src = ROOT / 'practices' / f'{slug}.md'
            if src.is_file():
                shutil.copy2(src, dest / 'practices' / f'{slug}.md')
        in_force = sorted(f.stem for f in (dest / 'practices').glob('*.md'))
        cases.append(('the import-dependent practices are in force in the '
                      'fixture, so their checks actually reach the import',
                      set(in_force) >= {'computed-numbers-in-scripts', 'source-naming'},
                      f'in force: {in_force}'))

        r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                            '--full-sweep'],
                           cwd=str(dest), capture_output=True, text=True)
        out = r.stdout + r.stderr
        cases.append(('it runs in a source set without a traceback',
                      'Traceback' not in out, failure_detail(out, 400)))
        cases.append(('nothing ERRORED -- an absent optional dependency is '
                      'not a broken tool', ' 0 errored' in out, failure_detail(out, 400)))
        cases.append(('no VIOLATION on a bare source set -- a check that '
                      'fires on a correct fresh install is one people learn '
                      'to ignore', 'VIOLATION' not in out,
                      failure_detail(out, 1400)))
        cases.append(('a skip names the module that was missing, rather than '
                      'going quiet', 'did not import' in out, failure_detail(out, 600)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for name, ok, detail in cases:
        check(f'precedent_check.py in a source set: {name}', ok,
              '' if ok else str(detail)[:500])


def check_rotation_gap_widens_to_find_coverage():
    """precedent_check.py's `_run_with_coverage_retry` (added 2026-09-20)
    against the incident it exists to close: on a sparse catalogue, the
    single rotation bucket a commit lands on -- unioned with every
    always-run non-tree check -- can be entirely inapplicable there even
    though the catalogue has real, passing coverage on OTHER buckets.
    Measured against two live PRs (see the function's own docstring for
    the commit counts and buckets): `0 passed`, correctly refused by CI's
    backstop, on commits where `--full-sweep` found 19 and 17 passing
    checks. The fix widens the rotation slice one bucket at a time until
    something is actually verified, or every bucket has been tried.

    Fixture, not the real catalogue (fixture-owns-its-state): ten fake
    `scope: 'tree'` slugs, `fake-tree-0..9`, only one of which
    (`fake-tree-7`) has a practices/ file on disk and a check function
    that reports PASS; the other nine are practice-backed with no file, so
    `run()` reports them SKIPPED exactly as a source set's own sparse
    catalogue does. Two fake non-tree slugs are wired the same way, to
    stand in for the always-run checks that were ALSO inapplicable in both
    measured PRs. `_touched_files` is stubbed to `[]` so nothing is
    directly or indirectly touched and the whole scoping question is
    rotation alone -- and the commit count is stubbed to land the base
    bucket on index 3, four buckets short of the one slug that can ever
    report anything (control-asserts-which-failure: the negative control
    below proves that gap is real before the fix's own retry is asked to
    close it)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc
    import tempfile, types

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-rotation-gap-'))
    saved_root, saved_checks, saved_git, saved_touched = (
        pc.ROOT, pc.CHECKS, pc._git, pc._touched_files)
    cases = []
    try:
        (tmp / 'practices').mkdir(parents=True)
        (tmp / 'practices' / 'fake-tree-7.md').write_text(
            '---\n'
            'slug:        fake-tree-7\n'
            'title:       Fixture practice for the rotation-gap test\n'
            'tier:        on-demand\n'
            'severity:    default\n'
            'applies_to:  []\n'
            'occasion:    "verify_harness.py fixture only"\n'
            'gates:       []\n'
            'checked_by:  "tools/precedent_check.py"\n'
            'status:      active\n'
            '---\n'
            '## Rule\nFixture only -- not a real practice.\n',
            encoding='utf-8')

        tree_slugs = [f'fake-tree-{i}' for i in range(10)]
        other_slugs = ['fake-other-0', 'fake-other-1']
        checks = {}
        for slug in tree_slugs:
            checks[slug] = {'scope': 'tree', 'practice_backed': True,
                             'fn': lambda ctx: [], 'what': 'fixture',
                             'blind_to': 'fixture'}
        for slug in other_slugs:
            checks[slug] = {'scope': 'change', 'practice_backed': True,
                             'fn': lambda ctx: [], 'what': 'fixture',
                             'blind_to': 'fixture'}

        pc.ROOT = tmp
        pc.CHECKS = checks
        pc._touched_files = lambda: []
        pc._git = (lambda *a: types.SimpleNamespace(stdout='3\n', returncode=0)
                   if a == ('rev-list', '--count', 'HEAD')
                   else saved_git(*a))
        ctx = pc.Ctx()
        scopes = {'tree', 'change'}

        # Negative control: the OLD behavior, one fixed bucket, no retry.
        # Base bucket for commit_count=3 is 3 -- 'fake-tree-3', which (like
        # every fake-tree slug but 7) has no practices/ file and can only
        # ever report SKIPPED. This is the bug: real coverage exists
        # (fake-tree-7) but the single-bucket selection never reaches it.
        old_scoped = pc._scoped_tree_slugs(tree_slugs, {3})
        old_slugs = sorted(set(other_slugs) | set(old_scoped))
        old_results = pc.run(old_slugs, ctx, scopes, exempt={})
        cases.append(('the negative control reproduces the gap -- a fixed '
                      'single bucket finds nothing to verify',
                      not any(r[1] in ('PASS', 'VIOLATION', 'ERROR')
                              for r in old_results),
                      [r[:2] for r in old_results]))

        # The fix: widen bucket by bucket until fake-tree-7 is in scope.
        slugs, results, scoped_tree, buckets_added = pc._run_with_coverage_retry(
            tree_slugs, other_slugs, ctx, scopes, exempt={})
        cases.append(('the widened run DOES find the real coverage',
                      any(r[1] == 'PASS' for r in results),
                      [r[:2] for r in results]))
        cases.append(('it found fake-tree-7 specifically, not some other slug '
                      'passing by accident',
                      any(r[0] == 'fake-tree-7' and r[1] == 'PASS'
                          for r in results),
                      [r[:2] for r in results]))
        cases.append(('it took exactly 4 extra buckets to reach index 7 from '
                      'base bucket 3 -- not fewer (lucky) and not a jump '
                      'straight to --full-sweep',
                      buckets_added == 4, buckets_added))
        cases.append(("scoped_tree names fake-tree-7 as run, not the other "
                      "eight buckets' worth of slugs it never needed",
                      scoped_tree.count('fake-tree-7') == 1
                      and len(scoped_tree) < len(tree_slugs),
                      scoped_tree))

        # Exhaustion: when NOTHING in the whole tree-scope catalogue can
        # ever report non-SKIPPED, the retry must still terminate -- by
        # trying every bucket exactly once, not looping forever -- and
        # come back with an honest all-SKIPPED result rather than
        # fabricating one (this is main()'s own `0 passed` refusal to
        # inherit, not something this function should paper over).
        checks_uncoverable = {s: {'scope': 'tree', 'practice_backed': True,
                                   'fn': lambda ctx: [], 'what': 'fixture',
                                   'blind_to': 'fixture'}
                              for s in tree_slugs}
        for slug in other_slugs:
            checks_uncoverable[slug] = {'scope': 'change',
                                         'practice_backed': True,
                                         'fn': lambda ctx: [],
                                         'what': 'fixture', 'blind_to': 'fixture'}
        pc.CHECKS = checks_uncoverable
        (tmp / 'practices' / 'fake-tree-7.md').unlink()
        _, results2, _, buckets_added2 = pc._run_with_coverage_retry(
            tree_slugs, other_slugs, ctx, scopes, exempt={})
        cases.append(('exhaustion terminates rather than looping -- every '
                      'bucket beyond the base one gets tried exactly once',
                      buckets_added2 == pc.ROTATION_BUCKETS - 1, buckets_added2))
        cases.append(('...and reports the honest result: nothing covered',
                      not any(r[1] in ('PASS', 'VIOLATION', 'ERROR')
                              for r in results2),
                      [r[:2] for r in results2]))
    finally:
        pc.ROOT, pc.CHECKS, pc._git, pc._touched_files = (
            saved_root, saved_checks, saved_git, saved_touched)
        shutil.rmtree(tmp, ignore_errors=True)

    for name, ok, detail in cases:
        check(f'precedent_check.py rotation-gap coverage retry: {name}', ok,
              '' if ok else str(detail)[:500])


def check_agents_templates_repeat_no_practice_text():
    """No block of an AGENTS.md template repeats a practice's own text.

    2026-10-01, from a consumer's Update Vendors: the update listed four
    `## Conventions` blocks the consumer's section lacked and said to copy
    each in by hand; once copied, session-load-budget refused the same text
    as already sitting in practices/<slug>.md, "paid for twice, every
    session". The template is where both instructions came from, so the
    template carries a one-line pointer to the practice instead, and this
    holds it there.

    The loader template only, since 2026-10-31: that day its sections moved
    into practices word for word, so the classic template -- for the
    process/upstream/ vendoring model, which loads no practice on occasion
    and runs no session-load-budget, so the double payment this guards
    against cannot happen there -- now shares their text by design."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
        import precedent_vendor_engine as pve
    finally:
        sys.path.pop(0)
    corpus = pc._practice_corpus(ROOT)
    bad = []
    for rel in ('templates/AGENTS.md.loader.template',):
        text = (ROOT / rel).read_text(encoding='utf-8')
        for offset, block in pve._md_blocks(text):
            for src, quote, words in pc.duplicated_resident_text(ROOT, block, corpus):
                bad.append(f'{rel}:{offset + 1} repeats {words} words of {src}: '
                           f'"{quote[:80]}..."')
    check('an AGENTS.md template repeats no practice text, so the update never '
          'asks for a copy session-load-budget then refuses', not bad, '; '.join(bad))


def check_retired_branch_name_does_not_ship():
    """precedent_check's retired-branch-name-ships: a practice whose shipped
    text names a retired branch is reported where it is authored, because
    every sync writes that text back into the consumers' generated blocks,
    which refresh's own retired-name report skips on purpose. Measured
    2026-09-26: a shared set's name-the-branch index_clause put
    precedent-beta-v01 back into a consumer's AGENTS.md on every sync.

    Both halves planted (practice: checks-plant-their-state): each shipped
    place it must catch, each place it must leave alone, and a control that
    empties the registry and watches the loud cases go quiet, so the
    finding is shown to come from RETIRED_BRANCH_NAMES and nothing else
    (practice: control-asserts-which-failure).
    """
    import tempfile
    import precedent_check as pc
    import precedent_vendor_engine as pve
    old, (new, _date) = next(iter(pve.RETIRED_BRANCH_NAMES.items()))
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='retired-name-ships-'))

    def practice(slug, tier='on-demand', status='active', clause='x',
                 rule='Do the thing.', detail='More.', story='It happened.'):
        return (f'---\nslug:        {slug}\ntitle:       T\ntier:        {tier}\n'
                f'severity:    default\napplies_to:  []\noccasion:    "doing x"\n'
                f'gates:       []\nindex_clause: "{clause}"\nchecked_by:  null\n'
                f'defines:     []\nstatus:      {status}\nsupersedes:  []\n'
                f'added:       "2026-09-26"\napproved_by: "fixture"\n---\n'
                f'## Rule\n{rule}\n\n## Detail\n{detail}\n\n## Why\nw\n\n'
                f'## Story\n{story}\n\n## Install\nNothing.\n')

    files = {
        'fx-clause': practice('fx-clause', clause=f'name it ({old}, main)'),
        'fx-resident': practice('fx-resident', tier='resident',
                                rule=f'Push to `{old}`.'),
        'fx-both-names': practice('fx-both-names',
                                  clause=f'`{new}` (named `{old}` until then)'),
        'fx-history': practice('fx-history', rule=f'Pushed to `{old}` once.',
                               detail=f'`{old}` was red.',
                               story=f'It landed on `{old}`.'),
        'fx-retired': practice('fx-retired', status='deduplicated',
                               clause=f'name it ({old})'),
        'fx-longer': practice('fx-longer', clause=f'name it ({old}-archive)'),
    }
    pdir = tmp / 'practices'
    pdir.mkdir(parents=True)
    for slug, text in files.items():
        (pdir / f'{slug}.md').write_text(text, encoding='utf-8')

    saved_root, saved_names = pc.ROOT, pve.RETIRED_BRANCH_NAMES
    try:
        pc.ROOT = tmp
        found = {f.where: str(f.detail) for f in pc._retired_branch_name_ships(None)}
        clause = found.get('practices/fx-clause.md', '')
        cases.append(('an index_clause naming a retired branch is reported, in '
                      'the check\'s own words and naming the new branch',
                      f'its index_clause names {old}, renamed {new}' in clause
                      and f'name {new} here instead' in clause, repr(found)))
        cases.append(('a RESIDENT practice\'s Rule naming it is reported -- '
                      'the resident block carries the whole Rule',
                      'its ## Rule names' in found.get('practices/fx-resident.md', ''),
                      repr(found)))
        cases.append(('QUIET: text that names the new branch beside the old one '
                      'is recording the rename, not using the old name',
                      'practices/fx-both-names.md' not in found, repr(found)))
        cases.append(('QUIET: an on-demand practice\'s Rule, Detail and Story '
                      'keep their dated history',
                      'practices/fx-history.md' not in found, repr(found)))
        cases.append(('QUIET: a practice no longer in force ships nothing',
                      'practices/fx-retired.md' not in found, repr(found)))
        cases.append(('QUIET: a longer branch name containing the old one is a '
                      'different branch',
                      'practices/fx-longer.md' not in found, repr(found)))
        pve.RETIRED_BRANCH_NAMES = {}
        try:
            pc._retired_branch_name_ships(None)
            emptied = 'ran'
        except pc.NotApplicable as e:
            emptied = str(e)
        cases.append(('CONTROL: with the registry empty the check says it cannot '
                      'apply, so the findings above came from it',
                      'predates RETIRED_BRANCH_NAMES' in emptied, emptied))
    finally:
        pc.ROOT, pve.RETIRED_BRANCH_NAMES = saved_root, saved_names
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a retired branch name is caught in the practice text a sync ships, '
          f'where it is authored ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_ledger_accepts_a_row_added_with_its_change():
    """practice: parallel-artifact-ledger, 2026-09-26. A commit cannot name
    its own ID, so the ledger check now also accepts a row added IN the
    commit that changed an adapter. Planted in a scratch history: a row
    arriving with its change passes; a change with no row, or with a row
    added only in a later commit, still fails; a row naming the change by
    ID still passes."""
    import shutil, tempfile
    import precedent_check as pc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ledger-same-commit-'))
    member = tmp / 'templates' / 'harness' / 'claude-code'
    ledger = tmp / 'templates' / 'harness' / 'LEDGER.md'
    head = ('| Date | Originating change | claude-code | codex | gemini-cli '
            '| grok-build |\n|---|---|---|---|---|---|\n')

    def g(*a):
        return subprocess.run(['git', *a], cwd=str(tmp), capture_output=True,
                              text=True, env=dict(os.environ,
                              GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@e.invalid',
                              GIT_COMMITTER_NAME='t',
                              GIT_COMMITTER_EMAIL='t@e.invalid'))

    def commit(msg, hook_text=None, row=None):
        if hook_text is not None:
            (member / 'hook.sh').write_text(hook_text)
        if row is not None:
            ledger.write_text(ledger.read_text() + row + '\n')
        g('add', '-A')
        g('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', msg)
        return g('rev-parse', 'HEAD').stdout.strip()

    old_root = pc.ROOT
    cases = []
    try:
        member.mkdir(parents=True)
        g('init', '-q')
        ledger.write_text(head)
        (tmp / 'README').write_text('x')
        commit('root')                                   # the base
        # The check reads this branch against its base, never the whole
        # history (Morgan, 2026-10-08; practice: checks-read-only-the-work).
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        commit('inception of claude-code', hook_text='v1')  # dir's first: exempt
        with_row = commit('change with its row', hook_text='v2',
                          row='| 2026-09-26 | the gate learns v2 | applied | none | none | none |')
        pc.ROOT = tmp
        f1 = [str(x) for x in pc._parallel_artifact_ledger(None)]
        cases.append(('CONTROL: a row added in the same commit as the change '
                      'passes, with no ID in it', f1 == []))
        bare = commit('change with no row', hook_text='v3')
        late = commit('row added later, without the ID',
                      row='| 2026-09-26 | the gate learns v3 | applied | none | none | none |')
        f2 = [str(x) for x in pc._parallel_artifact_ledger(None)]
        cases.append(('a change with no row of its own still fails, even '
                      'when a later commit adds an ID-less row',
                      any(bare[:7] in x and 'no row references' in x
                          for x in f2)))
        cases.append(('...and the ledger-only commit is not an adapter '
                      'change', not any(late[:7] in x for x in f2)))
        commit('pin', row=f'| 2026-09-26 | [`{bare[:7]}`](x) pinned | applied | none | none | none |')
        f3 = [str(x) for x in pc._parallel_artifact_ledger(None)]
        cases.append(('a row naming the change by ID still passes, as before',
                      f3 == []))
        cases.append(('the same-commit row was the one that passed',
                      pc._ledger_row_added_by(with_row) is True
                      and pc._ledger_row_added_by(bare) is False))
    finally:
        pc.ROOT = old_root
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] for c in cases if not c[1]]
    check(f'the ledger check accepts a row added with its change, and still '
          f'fails a change with no row ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_ci_workflow_approved_pins_approval_to_content():
    """THE INCIDENT (practice: ci-workflow-approved), 2026-09-25: a
    consumer's own light-check.yml billed a minute on every merge to main
    because a session had put back a push trigger another session removed
    six days earlier. An advisory check flagged the file on every run and
    nobody acted. This proves the blocking replacement: a workflow passes
    only as the engine's untouched copy or with an approval quoting the
    person, pinned by sha256 -- so an EDIT fails, not just an addition --
    and that the push gate runs it in the basic tier."""
    import hashlib, shutil, tempfile
    import precedent_install as _pi
    import precedent_push_check as _ppc
    import precedent_vendor_engine as _pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ci-approved-'))
    cases = []
    rel = '.github/workflows/light-check.yml'
    body = 'name: Light check\non:\n  pull_request:\n    branches: [main]\n'
    edited = body + '  push:\n    branches: [main]\n'
    quote = 'Morgan, 2026-09-25: "Please stop it running every time"'
    sha = hashlib.sha256(body.encode()).hexdigest()
    py = {n: (ROOT / 'tools' / n).read_bytes()
          for n in _pve.KINDS['consumer'] if n.endswith('.py')}
    try:
        def consumer(name, text=body, approved=None, tracked=None,
                     manifest=True, kind='consumer'):
            # No practices/ci-workflow-approved.md on purpose: the check
            # binds any repo keeping .github/workflows (binds_when), and a
            # fixture carrying the practice would hide that gate breaking.
            c = tmp / name
            (c / 'tools').mkdir(parents=True)
            (c / '.github' / 'workflows').mkdir(parents=True)
            for n, b in py.items():
                (c / 'tools' / n).write_bytes(b)
            if text is not None:
                (c / rel).write_text(text)
            if manifest:
                (c / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
                    {'kind': kind, 'source_commit': 'deadbeef',
                     'files': [], 'sha256': {},
                     'ci_workflow_files': sorted(tracked or {}),
                     'ci_workflows_sha256': tracked or {}}))
            cfg = {'sources': []}
            if approved is not None:
                cfg['github_ci_approved'] = approved
            (c / 'precedent.json').write_text(json.dumps(cfg))
            r = subprocess.run(
                [sys.executable, str(c / 'tools' / 'precedent_check.py'),
                 '--only', 'ci-workflow-approved'],
                capture_output=True, text=True, cwd=str(c))
            return r.returncode, r.stdout + r.stderr

        rc, out = consumer('unapproved')
        cases.append(('a workflow nobody approved is a VIOLATION, and says so',
                      rc != 0 and 'VIOLATION' in out
                      and 'has no approval' in out, failure_detail(out, 1500)))
        cases.append(('...and the finding names when it runs and the sha to '
                      'pin', 'pull_request' in out and sha in out, failure_detail(out, 1500)))
        good = {rel: {'sha256': sha, 'approved_by': quote}}
        rc, out = consumer('approved', approved=good)
        cases.append(('CONTROL: an approval quoting the person, pinned to '
                      'this content, passes', rc == 0 and '0 violated' in out,
                      failure_detail(out, 1500)))
        rc, out = consumer('edited', text=edited, approved=good)
        cases.append(('an EDIT after approval (a push trigger put back) fails',
                      rc != 0 and 'EDITED after it was approved' in out,
                      failure_detail(out, 1500)))
        rc, out = consumer('unquoted', approved={
            rel: {'sha256': sha, 'approved_by': 'Morgan, 2026-09-25'}})
        cases.append(('an approval quoting nobody is not an approval',
                      rc != 0 and 'quotes nobody' in out, failure_detail(out, 1500)))
        rc, out = consumer('undated', approved={
            rel: {'sha256': sha, 'approved_by': 'Morgan: "yes"'}})
        cases.append(('an undated approval is not an approval',
                      rc != 0 and 'carries no date' in out, failure_detail(out, 1500)))
        # A practice set is judged the same way (2026-10-01).
        rc, out = consumer('set-approved', approved=good, kind='source')
        cases.append(('in a practice set, an approved workflow passes',
                      rc == 0, failure_detail(out, 1500)))
        rc, out = consumer('set-unapproved', kind='source')
        cases.append(('...and an unapproved one is a VIOLATION',
                      rc != 0 and 'VIOLATION' in out, failure_detail(out, 1500)))
        rc, out = consumer('tracked', tracked={rel: sha})
        cases.append(('CONTROL: the engine\'s own untouched copy passes '
                      'with no approval', rc == 0, failure_detail(out, 1500)))
        rc, out = consumer('tracked-edited', text=edited, tracked={rel: sha})
        cases.append(('an edited engine copy with no approval fails',
                      rc != 0 and 'has no approval' in out, failure_detail(out, 1500)))
        rc, out = consumer('stale', text=None, approved=good)
        cases.append(('an approval whose file is gone is reported',
                      rc != 0 and 'no longer exists' in out, failure_detail(out, 1500)))
        rc, out = consumer('no-manifest', manifest=False)
        # Since 2026-09-30 a repo with no manifest is judged on growth only
        # (a change that makes a workflow run more), so it runs, never
        # crashes, and a repo whose change grows nothing passes.
        cases.append(('CONTROL: no manifest (BestPractice\'s shape) is judged '
                      'on growth only: no crash, and nothing grown passes',
                      rc == 0 and 'Traceback' not in out, failure_detail(out, 1500)))

        # Since 2026-09-27 the light check is an engine file like the leak
        # gate: shipped through CI_WORKFLOW_TEMPLATES, tracked in the
        # manifest the install writes, so it needs no approval entry.
        cases.append(('the light check ships to consumers as an engine-owned, '
                      'tracked workflow',
                      ('light-check.yml.template', rel)
                      in _pve.CI_WORKFLOW_TEMPLATES['consumer']
                      and not hasattr(_pve, 'CI_INSTALL_ONLY_TEMPLATES')
                      and not hasattr(_pi, '_approve_installed_workflow'), ''))
        inst = tmp / 'install'
        (inst / '.github' / 'workflows').mkdir(parents=True)
        (inst / 'tools').mkdir()
        shutil.copy(ROOT / 'templates' / 'github-actions' /
                    'light-check.yml.template', inst / rel)
        (inst / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'consumer'}))
        _pve.record_ci_workflow_files(inst, 'consumer')
        m = json.loads((inst / 'tools' / 'ENGINE_MANIFEST.json').read_text())
        cases.append(('...and the install records it in the manifest, pinned '
                      'to the template',
                      m.get('ci_workflows_sha256', {}).get(rel)
                      == hashlib.sha256((inst / rel).read_bytes()).hexdigest(),
                      str(m)))

        for kind in ('consumer', 'source'):
            names = [n for n, _a, _r in _ppc.PUSH_CHECKS[kind]]
            cases.append((f'the {kind} push check runs ci_workflows',
                          'ci_workflows' in names, str(names)))
        cases.append(('...in the BASIC tier, so a push to any branch runs it',
                      'ci_workflows' in _ppc.BASIC_CHECKS,
                      str(_ppc.BASIC_CHECKS)))
        cases.append(('a consumer\'s own light_check runs before a push, and '
                      'is optional where the repo has none',
                      'light_check' in [n for n, _a, _r
                                        in _ppc.PUSH_CHECKS['consumer']]
                      and 'light_check' in _ppc.OPTIONAL, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'ci-workflow-approved fails an unapproved or edited workflow, '
          f'passes a pinned approval or the engine\'s own copy, and runs '
          f'before every push ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:1500]}' for n, d in bad))


def check_workflow_file_outside_vendoring_detects_candidates():
    """THE INCIDENT this guards against (practice: workflow-file-outside-
    vendoring), 2026-09-20: a sweep list built by matching workflow
    filenames against a table of retired names flagged a real dependent
    repo's `light-check.yml` as a retired duplicate. It was a live,
    required, hand-authored check sharing a name with something Precedent
    once retired, for unrelated reasons. This tests that the mechanism
    built afterward compares by TRACKING (a repo's own ci_workflow_files),
    never by name, and never auto-classifies -- it only ever reports a
    candidate, with a declared-decline escape hatch for a legitimate one.

    Fixture shape mirrors check_vendor_engine_retires_ci_workflow_files
    immediately above: a fresh consumer directory per scenario, only the
    files each scenario actually needs."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-wf-outside-'))
    cases = []
    tracked_rel = '.github/workflows/bestpractice-docs.yml'
    untracked_rel = '.github/workflows/light-check.yml'
    exempt_rel = '.github/workflows/hand-authored-check.yml'
    try:
        # The full consumer-kind .py set, not just the two files this check
        # touches directly -- precedent_check.py imports several vendored
        # companions at module level (split_practices, precedent_time, and
        # others), and a fixture missing any one of them fails with an
        # import traceback that has nothing to do with what this test
        # actually checks (practice: fixture-owns-its-state).
        import precedent_vendor_engine as _pve_for_fixture
        _consumer_py = {n: (ROOT / 'tools' / n).read_bytes()
                        for n in _pve_for_fixture.KINDS['consumer']
                        if n.endswith('.py')}
        # This check is practice_backed=True (the default): run() refuses to
        # run it in a repo whose own practices/workflow-file-outside-
        # vendoring.md does not resolve, the same gate that keeps a check
        # from claiming coverage nobody actually distributed. A fixture
        # missing this file is not testing this check at all -- it is
        # testing the refusal, which every case here would silently do
        # instead of what its own name says it asserts.
        _practice_bytes = (ROOT / 'practices' /
                           'workflow-file-outside-vendoring.md').read_bytes()

        def make_consumer(name, ci_workflow_files, precedent_json=None,
                          write_workflows=True):
            consumer = tmp / name
            (consumer / 'tools').mkdir(parents=True)
            (consumer / '.github' / 'workflows').mkdir(parents=True)
            for _n, _b in _consumer_py.items():
                (consumer / 'tools' / _n).write_bytes(_b)
            (consumer / 'practices').mkdir()
            (consumer / 'practices' / 'workflow-file-outside-vendoring.md').write_bytes(
                _practice_bytes)
            if write_workflows:
                (consumer / tracked_rel).write_text('name: docs\n')
                (consumer / untracked_rel).write_text('name: light\n')
                (consumer / exempt_rel).write_text('name: hand-authored\n')
            manifest = {'kind': 'consumer', 'source_commit': 'deadbeef',
                       'files': [], 'sha256': {},
                       'ci_workflow_files': ci_workflow_files,
                       'ci_workflows_sha256': {}}
            (consumer / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                json.dumps(manifest), encoding='utf-8')
            if precedent_json is not None:
                (consumer / 'precedent.json').write_text(
                    json.dumps(precedent_json), encoding='utf-8')
            return consumer

        def run_check(consumer):
            r = subprocess.run(
                [sys.executable, str(consumer / 'tools' / 'precedent_check.py'),
                 '--only', 'workflow-file-outside-vendoring'],
                capture_output=True, text=True, cwd=str(consumer))
            return r.returncode, r.stdout + r.stderr

        # -- A: no exemption declared -- both untracked files are reported --
        a = make_consumer('bare', [tracked_rel])
        rc_a, out_a = run_check(a)
        cases.append(('the tracked file is never reported',
                      tracked_rel + ':' not in out_a, out_a[:1200]))
        cases.append(('an untracked workflow file IS reported, by path, as '
                      'a candidate -- never a verdict',
                      untracked_rel in out_a and 'CANDIDATE' not in out_a.split(untracked_rel)[0][-5:]
                      or untracked_rel in out_a,
                      out_a[:1200]))
        cases.append(('the report says "verify by content, never by name" -- '
                      'the exact framing the incident requires',
                      'verify by content, never by name' in out_a, out_a[:1200]))
        cases.append(('the hand-authored file is ALSO reported here -- no '
                      'exemption was declared for it',
                      exempt_rel in out_a, out_a[:1200]))
        cases.append(('the run reports ADVISORY, not VIOLATION -- this '
                      'check can never fail a build',
                      'ADVISORY' in out_a and 'VIOLATION' not in out_a, out_a[:1200]))

        # -- B: a declared exemption, with a reason, silences its own path
        # only -- the other untracked file is still reported --
        b = make_consumer('exempted', [tracked_rel], precedent_json={
            'ci_workflow_outside_vendoring_exempt': [
                {'path': exempt_rel, 'reason': 'a repo-specific hand-authored check'}]})
        rc_b, out_b = run_check(b)
        cases.append(('CONTROL: the exempted path is not reported once its '
                      'reason is declared',
                      exempt_rel not in out_b, out_b[:1200]))
        cases.append(('...but the OTHER untracked file is still reported -- '
                      'the exemption is scoped to its own path, not blanket',
                      untracked_rel in out_b, out_b[:1200]))

        # -- C: an exemption declared with no reason is not honoured at all
        # (checks-carry-a-declared-decline: the reason is mandatory) --
        c = make_consumer('reasonless', [tracked_rel], precedent_json={
            'ci_workflow_outside_vendoring_exempt': [{'path': exempt_rel}]})
        rc_c, out_c = run_check(c)
        cases.append(('an exemption with no reason is ignored -- still '
                      'reported',
                      exempt_rel in out_c, out_c[:1200]))

        # -- D: a STALE exemption -- declared, but this run does not find
        # the path untracked (it is now in ci_workflow_files) -- reported
        # as stale rather than silently honoured --
        d = make_consumer('stale', [tracked_rel, exempt_rel], precedent_json={
            'ci_workflow_outside_vendoring_exempt': [
                {'path': exempt_rel, 'reason': 'used to be hand-authored'}]})
        rc_d, out_d = run_check(d)
        cases.append(('a stale exemption (declared, but now tracked) is '
                      'reported rather than silently accepted',
                      exempt_rel in out_d
                      and 'does not find it untracked' in out_d,
                      out_d[:1200]))

        # -- E, CONTROL: no ENGINE_MANIFEST.json at all (BestPractice's own
        # shape) -- the check is NotApplicable, never a false pass or a
        # crash --
        e = tmp / 'no-manifest'
        (e / 'tools').mkdir(parents=True)
        (e / 'practices').mkdir()
        (e / 'practices' / 'workflow-file-outside-vendoring.md').write_bytes(
            _practice_bytes)
        for _n, _b in _consumer_py.items():
            (e / 'tools' / _n).write_bytes(_b)
        rc_e, out_e = run_check(e)
        cases.append(('CONTROL: no manifest at all reports SKIPPED, never '
                      'a crash or a silent pass claiming coverage it does '
                      'not have',
                      'SKIPPED' in out_e and 'workflow-file-outside-vendoring'
                      in out_e, out_e[:1200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'workflow-file-outside-vendoring reports an untracked workflow '
          f'file as a candidate, never a verdict, honours a declared '
          f'exemption scoped to its own path, and flags a stale one '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:1200]}" for n, d in bad))


def check_rule_rewrite_detection():
    """cite-the-incident asks "did somebody WRITE this rule", so it has to
    tell an authorship event from an edit.

    It used to compare the Rule text for equality, and that was wrong twice
    in one day (2026-09-06): a sweep repointing 67 broken relative links
    demanded a `## Story` from four inherited practices whose prose it had
    not touched a word of, and then a one-word product rename did the same.
    Both times the only ways to clear the demand were to invent an incident
    or to leave the defect unfixed. A demand nobody can honestly satisfy is
    worse than no demand: it teaches people to route around the check.

    Two thresholds, because neither alone works: on a short Rule one
    swapped word is a large FRACTION of the text, and on a long one a real
    paragraph rewrite can be a small fraction. Both directions are pinned
    here, because the lenient direction is where this could quietly become
    a check that never fires."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc_rewrite', ROOT / 'tools' / 'precedent_check.py')
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)

    long_rule = ("A practice layer's own install playbook records the mechanics "
                 "of every host-specific setup step, and the maintainers read "
                 "it, but the project's own people read the getting-started "
                 "page instead. " * 3)
    cases = [
        ('a single word swapped in a short Rule is an edit, not a rewrite',
         "Alpha's internal install playbook records the mechanics.",
         "Bravo's internal install playbook records the mechanics.", False),
        ('the same word swapped throughout a long Rule is still an edit',
         long_rule, long_rule.replace('playbook', 'runbook'), False),
        ('a repointed link is not a rewrite (the target is not prose)',
         'See [tools/x.py](tools/x.py) for the engine.',
         'See [tools/x.py](../tools/x.py) for the engine.', False),
        ('a typo fix is not a rewrite',
         'Order sections by how often the reader neds them.',
         'Order sections by how often the reader needs them.', False),
        ('replacing the Rule with different substance IS a rewrite',
         'Every generated file carries a build code.',
         'Sessions never edit a vendored file by hand; move the change into '
         'the source repository and re-vendor, so the next refresh does not '
         'silently discard it.', True),
        ('a Rule where there was none is authorship',
         '', 'A new rule, freshly authored, with real substance behind it.', True),
        ('replacing most of a Rule is a rewrite',
         'Order sections by how often the reader needs them; common first, '
         'rare last.',
         'Order sections alphabetically, and put every migration note in an '
         'appendix at the very end of the document.', True),
    ]
    results = [(name, pc._rule_was_rewritten({'rule': b}, {'rule': a}) == expect)
               for name, b, a, expect in cases]
    bad = [n for n, ok in results if not ok]
    for n in bad:
        print(f"  rule-rewrite detection did NOT behave as stated: {n}")
    check(f'cite-the-incident tells an authorship event from an edit '
          f'({len(cases)} stated cases: a rename, a repeated rename, a '
          f'repointed link and a typo are edits; new substance, a Rule added '
          f'from nothing, and most of a Rule replaced are rewrites)',
          not bad)


def check_title_case_leaves_code_and_first_word_alone():
    """Headline capitalization never reaches inside an inline code span, and
    the first WORD after an enumerator is capitalized.

    Both learned from real corruption, 2026-09-06. INSTALL.md's own section
    headings had been rewritten by `tools/title_case.py --write` to
    `Process/manifest.json` and `Tools/practice_audit.py` -- neither of which
    exists, in a heading whose whole job is to name the file the section is
    about. The tool's docstring already promised fenced code blocks were
    safe; inline spans were not, and a heading is exactly where a document
    names a path. The same run left `## 5. the Manifest Schema` lowercase,
    because "5." counted as token zero and headline style capitalizes the
    first word, not the first token.

    A tool that rewrites committed prose in place needs its blast radius
    asserted, not described: this is the check that would have caught both
    before they reached the tree.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_title_case', ROOT / 'tools' / 'title_case.py')
    try:
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:
        not_applicable('title_case leaves code spans and first words alone',
                       f'tools/title_case.py could not be imported ({e}) -- '
                       f'not a pass')
        return

    cases = [
        # (input, must appear in output, why)
        ("5. the Manifest Schema (`process/manifest.json`)",
         "`process/manifest.json`", 'a path in a code span is untouched'),
        ("6. the Audit (`tools/practice_audit.py`)",
         "`tools/practice_audit.py`", 'a second path, different depth'),
        ("5. the Manifest Schema (`process/manifest.json`)",
         "5. The Manifest", 'the first word after an enumerator is capitalized'),
        ("Working With `git rev-parse --verify` Safely",
         "`git rev-parse --verify`", 'a command with flags is untouched'),
        ("A Heading About `AGENTS.md` and `tools/doc_lint.py`",
         "`tools/doc_lint.py`", 'two spans in one heading'),
        # KEEP_PHRASES, both shapes. `The Why` is a noun phrase the SMALL
        # rule would lowercase; `See also` is the mirror image -- `also` is
        # not in SMALL, so headline style reaches for "See Also", which no
        # style guide asks for. The second was carried BY HAND in a dependent
        # repo for a day, re-applied after every engine refresh ate it, with
        # 16 live headings depending on it. It is asserted here because the
        # whole point of upstreaming it was that nobody should have to
        # notice again.
        ("see also", "See also", 'a lowercase cross-reference heading'),
        ("See Also", "See also", 'and one already miscapitalized'),
        ("Notes and see also", "See also", 'mid-heading, not only at the start'),
        ("the why", "The Why", 'the other keep-phrase still keeps its caps'),
    ]
    bad = []
    for text, must, why in cases:
        got = tc.title_case(text)
        if must not in got:
            bad.append(f'{why}: {text!r} -> {got!r} (wanted {must!r} in it)')
    check(f'title_case leaves inline code spans and enumerated first words '
          f'alone ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_title_case_never_corrupts_content():
    """Headline case is a STYLE change; it must never alter a word or a path.

    All three reproduced from a consuming repo that ran the rule against real
    output documents, 2026-09-07 -- the point at which a rule aimed at
    published prose first met labels, provenance headings and vendored
    subtrees. Every other rule in title_case is a capitalization choice a
    reader could argue with. These produced a DIFFERENT WORD or a path that
    does not resolve, which is a different kind of wrong and is why they get
    their own check.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_tc_corrupt', ROOT / 'tools' / 'title_case.py')
    try:
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:
        not_applicable('title_case never corrupts content',
                       f'tools/title_case.py could not be imported ({e}) -- '
                       f'not a pass')
        return

    cases = [
        # (input, must appear in output, why)
        ('Option A and Option B', 'Option A and',
         'a capital single-letter LABEL mid-heading is not the article "a"'),
        ('SAMPLE A — book introduction (excerpt)', 'SAMPLE A',
         'the same, with the label in caps'),
        ('Appendix A and the rest', 'Appendix A and',
         'and again -- these are where labels actually live'),
        ('Moved from content/BUSINESS-MODEL-CONCEPTS.md: the moat',
         'content/BUSINESS-MODEL-CONCEPTS.md',
         'a BARE path keeps its segments; capitalizing one breaks the path'),
        ('Running title_case.py on the tree', 'title_case.py',
         'a bare filename, no slash, is a path too'),
        # ... and the rules that must still work, so the fixes above are not
        # a licence to stop capitalizing.
        ('The rise of a nation', 'of a Nation',
         'a real lowercase article is still lowercased'),
        ('A study of moats', 'A Study of Moats',
         'a leading article is still capitalized as the first word'),
        ('Plan B', 'Plan B', 'a last-word label is untouched, as before'),
        ('Exhibit A: the numbers', 'Exhibit A: The',
         'a word after a colon still opens a new phrase'),
        ('Reading and/or writing', 'And/or',
         'prose containing a slash is NOT treated as a path'),
    ]
    bad = []
    for text, must, why in cases:
        got = tc.title_case(text)
        if must not in got:
            bad.append(f'{why}: {text!r} -> {got!r} (wanted {must!r} in it)')
    check(f'title_case never corrupts a word or a path '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_title_case_output_paths_inverts_the_default():
    """A repo may DECLARE what it publishes, instead of the tool inferring it.

    title_case's exclusion default reasons from BestPractice's own directory
    names, so in any other tree it names almost nothing and classifies the
    whole working tree as published -- which is how a consumer got 69
    "outward-facing" headings across 10 files, none of them outward-facing.
    `output_paths` inverts that for repos willing to answer, and is opt-in:
    absent, behaviour is exactly what it was, so no existing install moves.

    The case that matters most is the last one: a vendored subtree sitting
    INSIDE a declared output directory. It is mirrored from elsewhere by a
    sync tool, so headings "fixed" there are correct until the next sync and
    then silently revert. internal_paths must win over output_paths for that
    to be expressible at all.
    """
    import importlib.util, tempfile
    spec = importlib.util.spec_from_file_location(
        '_tc_output', ROOT / 'tools' / 'title_case.py')
    try:
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:
        not_applicable('title_case output_paths inverts the default',
                       f'tools/title_case.py could not be imported ({e}) -- '
                       f'not a pass')
        return

    bad = []
    with tempfile.TemporaryDirectory() as td:
        declared = pathlib.Path(td) / 'declared'; declared.mkdir()
        (declared / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'output_paths': ['business-modeling', 'book-joseph'],
            'internal_paths': ['book-joseph/voice-pack'],
        }), encoding='utf-8')
        absent = pathlib.Path(td) / 'absent'; absent.mkdir()
        (absent / 'precedent.json').write_text(
            json.dumps({'format_version': 1}), encoding='utf-8')
        empty = pathlib.Path(td) / 'empty'; empty.mkdir()
        (empty / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'output_paths': []}), encoding='utf-8')

        cases = [
            (declared, 'business-modeling/plan.md', True, 'a declared output path is output'),
            (declared, 'book-joseph/ch1.md', True, 'so is the second one'),
            (declared, 'notes/scratch.md', False, 'anything undeclared is internal'),
            (declared, 'README.md', False, 'including a root document'),
            (declared, 'practices/x.md', False, 'the engine exclusions still hold'),
            (declared, 'business-modeling/practices/y.md', False,
             'a vendored practices tree inside an output path is still excluded'),
            (declared, 'book-joseph/voice-pack/tone.md', False,
             'internal_paths WINS over output_paths -- the vendored-subtree case'),
            (absent, 'README.md', True, 'absent: unchanged, everything not excluded is output'),
            (absent, 'MAP.source.md', False,
             "a map's source is internal like the map it feeds (a consumer, 2026-10-03)"),
            (absent, 'GLOSSARY.source.md', False,
             "...and so is a glossary's"),
            (absent, 'notes/x.md', True, 'absent: unchanged for a working directory too'),
            (empty, 'README.md', False,
             'an EMPTY output_paths is a declaration ("we publish nothing"), not an absence'),
        ]
        for root, rel, want, why in cases:
            got = tc.is_outward(rel, root=root)
            if got != want:
                bad.append(f'{why}: is_outward({rel!r}) == {got}, wanted {want}')

    check(f'title_case output_paths inverts the default, opt-in, with '
          f'internal_paths still subtracting ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_title_case_honours_repo_declared_internal_paths():
    """A repo can exclude its own directories from headline capitalization
    through precedent.json, and cannot use that key to re-include what the
    engine excludes.

    tools/title_case.py is VENDORED into every consumer, so its
    INTERNAL_DIRS / INTERNAL_FILES lists are Precedent's names, not the
    adopter's, and an engine refresh overwrites anything edited into them.
    The exclusion default that fails safe upstream fails the other way in a
    consumer: every working directory nobody happened to name reads as
    published. 2026-09-07, a real consumer came back from an engine update
    with 69 "outward-facing" headings across 10 files, none of them
    outward-facing.

    Two properties, and the second matters more than the first: the key
    must ADD exclusions and must never subtract one. A consumer that could
    re-include `practices/` would have this tool rewriting headings inside
    a vendored upstream tree, undone by the next refresh -- the exact
    failure is_outward's own `practices` guard was added to stop.
    """
    import importlib.util, tempfile
    spec = importlib.util.spec_from_file_location(
        '_title_case_ip', ROOT / 'tools' / 'title_case.py')
    try:
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:
        not_applicable('title_case honours repo-declared internal_paths',
                       f'tools/title_case.py could not be imported ({e}) -- '
                       f'not a pass')
        return

    bad = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'internal_paths': ['notes', 'docs/drafts', 'ROADMAP.md',
                               '/escapes', '../escapes', 7, ''],
            # A consumer must not be able to re-include what the engine
            # excludes; this entry is here to prove it is ignored, since
            # the key only ever adds.
            'sources': [],
        }), encoding='utf-8')

        cases = [
            # (path, expected is_outward, why)
            ('README.md', True, 'an undeclared root document stays outward'),
            ('documentation/pitch.md', True, 'an undeclared directory stays outward'),
            ('notes/scratch.md', False, 'a declared directory is internal'),
            ('notes/deep/er.md', False, 'everything under it, at any depth'),
            ('docs/drafts/one.md', False, 'a nested declared path is internal'),
            ('docs/published.md', True, 'its sibling is not'),
            ('notesy/other.md', True, 'a prefix match is on path segments, not characters'),
            ('ROADMAP.md', False, 'a declared single file is internal'),
            ('practices/x.md', False, 'the engine exclusion still holds'),
        ]
        for rel, want, why in cases:
            got = tc.is_outward(rel, root=root)
            if got != want:
                bad.append(f'{why}: is_outward({rel!r}) == {got}, wanted {want}')

        # Malformed config fails OPEN -- the built-in boundary, never a crash.
        broken = pathlib.Path(td) / 'broken'
        broken.mkdir()
        (broken / 'precedent.json').write_text('{not json at all',
                                               encoding='utf-8')
        try:
            if tc.is_outward('README.md', root=broken) is not True:
                bad.append('a malformed precedent.json changed the boundary')
        except Exception as e:
            bad.append(f'a malformed precedent.json raised {e!r}')

        # No config at all: same.
        empty = pathlib.Path(td) / 'empty'
        empty.mkdir()
        try:
            if tc.is_outward('README.md', root=empty) is not True:
                bad.append('a missing precedent.json changed the boundary')
        except Exception as e:
            bad.append(f'a missing precedent.json raised {e!r}')

    check('title_case honours repo-declared internal_paths, additively only '
          '(11 stated cases)', not bad, '; '.join(bad))


def check_vocabulary_lets_a_local_practice_name_a_local_script():
    """vocabulary-reaches-the-consumer judges a repo-local command practice
    by whether its script is in the repo, not by the engine lists.

    2026-10-10, a consumer: its own practice declared a standing command and named
    its own tools/notes_file.py, and the check refused it as missing from
    ENGINE_FILES -- a failure that cannot happen to a practice that never
    leaves the repo. The session dropped the command to get past, and the
    word left that repo's Vocabulary. Planted: the same practice, local with
    its script, local without it, and received (the engine rule, unchanged)."""
    import tempfile, types
    name = 'a repo-local command practice may name the repo\'s own script'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'practices').mkdir()
        (repo / 'tools').mkdir()
        (repo / 'practices' / 'pull-notes.md').write_text(
            '---\nslug: pull-notes\nscope: any-adopter\n'
            'command: {"Pull notes": "Bring in every new note."}\n---\n\n'
            '## Rule\nRun `python3 tools/notes_file.py`.\n', encoding='utf-8')

        def run(level, script):
            if level:
                (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
                    {'slug': 'pull-notes', 'level': level, 'source': 'x'}]}),
                    encoding='utf-8')
            elif (repo / 'MANIFEST.json').exists():
                (repo / 'MANIFEST.json').unlink()
            f = repo / 'tools' / 'notes_file.py'
            if script:
                f.write_text('print(1)\n', encoding='utf-8')
            elif f.exists():
                f.unlink()
            return pc._vocabulary_reaches_the_consumer(types.SimpleNamespace(root=repo))

        cases.append(('THE DISCRIMINATING CASE: local, with its script here, passes',
                      run('repo-local', True) == []))
        cases.append(('local, with its script missing, still fails',
                      len(run('repo-local', False)) == 1))
        cases.append(('received from a set, the engine rule holds as before',
                      len(run('individual', True)) == 1))
        cases.append(('no MANIFEST.json: today\'s rule, no guessing',
                      len(run(None, True)) == 1))
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_writing_checks_leave_a_declared_record_as_filed():
    """The writing checks leave a file the repository declares in
    record_paths as it was filed; the same file anywhere else is still
    checked.

    2026-10-10, a consumer filing call transcripts: the first two could not
    be committed, because the acronym, figure and heading checks flagged
    what people SAID on the calls. record_paths already declared records for
    the link and citation checks, and the writing checks never asked it.
    Planted: one transcript with a skipped heading level and a lowercase
    heading, under a declared record directory and outside it."""
    import tempfile, types
    name = 'the writing checks leave a declared record as filed'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
        import doc_lint as dl
    finally:
        sys.path.pop(0)
    saved = (pc.ROOT, dl.ROOT)
    cases = []
    text = ('# Call with the team\n\n### what the client said about the CRM\n\n'
            'He put it at 40 percent, from memory.\n')
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            for d in ('calls', 'notes'):
                (repo / d).mkdir()
                (repo / d / '2026-10-01-call.md').write_text(text, encoding='utf-8')
            pc.ROOT = dl.ROOT = repo
            ctx = types.SimpleNamespace(root=repo, changed=[
                'calls/2026-10-01-call.md', 'notes/2026-10-01-call.md'])

            def run(fn):
                try:
                    return [f.file() if hasattr(f, 'file') else str(f) for f in fn(ctx)]
                except pc.NotApplicable:
                    return []

            def both():
                return (run(pc._heading_outline), run(pc._headline_capitalization),
                        pc._md_in_scope(ctx), dl.drop_frozen(list(ctx.changed)))
            (repo / 'precedent.json').write_text('{}', encoding='utf-8')
            before = both()
            (repo / 'precedent.json').write_text(json.dumps({'record_paths': [
                {'path': 'calls/', 'reason': 'call transcripts'}]}), encoding='utf-8')
            after = both()

            def hits(rows, where):
                return any(where in r for r in rows)
            cases.append(('control: undeclared, the transcript\'s skipped heading level is flagged',
                          hits(before[0], 'calls/')))
            cases.append(('control: undeclared, its lowercase heading is flagged',
                          hits(before[1], 'calls/')))
            cases.append(('declared, heading-outline leaves it alone',
                          not hits(after[0], 'calls/')))
            cases.append(('declared, headline capitalization leaves it alone',
                          not hits(after[1], 'calls/')))
            cases.append(('declared, the shared writing-check scope (acronyms, figures, '
                          'labels...) leaves it out',
                          'calls/2026-10-01-call.md' not in after[2]))
            cases.append(('declared, doc_lint\'s changed-file gate leaves it out',
                          'calls/2026-10-01-call.md' not in after[3]))
            cases.append(('the same file outside record_paths is still checked, every way',
                          hits(after[0], 'notes/') and hits(after[1], 'notes/')
                          and 'notes/2026-10-01-call.md' in after[2]
                          and 'notes/2026-10-01-call.md' in after[3]))
    finally:
        pc.ROOT, dl.ROOT = saved
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_very_deep_check_runs_other_sources_checks_here():
    """A declared source's own check script whose practice is IN FORCE in
    this repo, and which this repo's precedent_check.py never discovers, is
    run against this checkout by the very deep check's CHECK COVERAGE, with
    PRECEDENT_CHECK_ROOT pointing here -- a report, never a gate (practice:
    very-deep-check, pass 2 question 15; 2026-09-28: private-repo-scrub was
    in force in BestPractice and its check had never run here)."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import very_deep_check as vdc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-source-checks-'))
    cases = []
    try:
        root, src = tmp / 'root', tmp / 'shared'
        for d in (root / 'practices', root / 'tools' / 'checks',
                  src / 'practices', src / 'tools' / 'checks'):
            d.mkdir(parents=True)
        script = ('import os, pathlib, sys\n'
                  'root = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT") '
                  'or ".")\n'
                  'if not (root / "{f}").is_file():\n'
                  '    print("VIOLATION:"); print("{f} is missing here")\n'
                  '    sys.exit(1)\n'
                  'sys.exit(0)\n')

        def practice(slug, status='active'):
            name = 'check_' + slug.replace('-', '_') + '.py'
            (src / 'practices' / f'{slug}.md').write_text(
                f'---\nslug: {slug}\nstatus: {status}\n'
                f'checked_by: tools/checks/{name}\n---\n\n## Rule\n\nX.\n',
                encoding='utf-8')
            (src / 'tools' / 'checks' / name).write_text(
                script.format(f=f'{slug}.marker'), encoding='utf-8')
            return name

        practice('zz-fails-here')
        practice('zz-passes-here')
        (root / 'zz-passes-here.marker').write_text('x\n', encoding='utf-8')
        practice('zz-retired', status='retired')
        dup = practice('zz-already-run')
        (root / 'tools' / 'checks' / dup).write_text('x\n', encoding='utf-8')
        sources = [{'level': 'universal', 'name': 'precedent',
                    'path': str(root)},
                   {'level': 'shared', 'name': 'zz-shared', 'path': str(src)}]
        rows, note = vdc._source_check_scripts(root, sources)
        by = {r[1]: r for r in rows}
        cases.append(('THE CASE: an in-force source check runs against this '
                      'checkout and its violation is reported',
                      by.get('zz-fails-here', ('',))[0] == 'VIOLATION'
                      and 'missing here' in by['zz-fails-here'][3],
                      f'{note} {rows!r}'))
        cases.append(('it reads THIS checkout, not the source (control: the '
                      'marker is here)',
                      by.get('zz-passes-here', ('',))[0] == 'PASS',
                      repr(rows)))
        cases.append(('a retired practice\'s check does not run',
                      'zz-retired' not in by, repr(rows)))
        cases.append(('a check this repo already runs is not run twice',
                      'zz-already-run' not in by, repr(rows)))
    except AttributeError as exc:
        cases.append(('the very deep check can run other sources\' checks',
                      False, f'{type(exc).__name__}: {exc}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the very deep check runs other sources\' in-force checks against '
          f'this checkout ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_generated_blocks_both_styles():
    """generated_blocks.py: the one "is this line generated?" every scan that
    skips generated text uses (added 2026-09-29). Each tool used to match
    one marker style itself, and a shared set's no-stale-counts check,
    knowing only `<!--gen:NAME-->`, read the loader block's "1 of 20
    practices" as a stale hand-written count.

    Stated cases, one per shape (practice: checks-plant-their-state), with
    the unclosed-marker control: an opener with no closer hides nothing, so
    a marker quoted in a document cannot hide the rest of it (practice:
    control-asserts-which-failure). The callers are checked too, through the
    three whose skip used to know only one style, and so is
    checks-use-generated-blocks, which holds a repo's own checks to it."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import generated_blocks as gb
    L, E = gb.LOADER_BEGIN, gb.LOADER_END
    shapes = [
        ('the loader style is generated, both marker lines included',
         ['hand', L, 'gen 1 of 20 practices', E, 'hand'],
         [False, True, True, True, False]),
        ('the gen: style is generated, both marker lines included',
         ['hand', '<!--gen:t-->', 'gen', '<!--/gen:t-->', 'hand'],
         [False, True, True, True, False]),
        ('an indented marker still counts',
         ['  <!--gen:t-->', '  gen', '  <!--/gen:t-->'], [True] * 3),
        ('both styles in one document',
         ['<!--gen:a-->', 'x', '<!--/gen:a-->', 'hand', L, 'y', E],
         [True, True, True, False, True, True, True]),
        ('CONTROL: an unclosed loader opener hides nothing',
         ['hand', L, 'hand still', 'hand still'], [False] * 4),
        ('CONTROL: an unclosed gen: opener hides nothing',
         ['<!--gen:a-->', 'hand', 'hand'], [False] * 3),
        ('CONTROL: a gen: block closes only on its own name',
         ['<!--gen:a-->', 'x', '<!--/gen:b-->', 'hand'], [False] * 4),
        ('CONTROL: a marker quoted mid-line in prose is not a marker',
         [f'keep the `{L}` marker', 'hand', E, 'hand'],
         [False, False, False, False]),
    ]
    bad = []
    for label, lines, want in shapes:
        got = gb.mask(lines)
        if got != want:
            bad.append(f'{label}: got {got}')
    text = '\n'.join(['a', L, 'b', E, 'c'])
    if gb.blank(text).split('\n') != ['a', '', '', '', 'c']:
        bad.append('blank() does not keep line numbers')

    import importlib
    import tempfile
    dl = importlib.import_module('doc_lint')
    loader_doc = '\n'.join(['<!--numbers:gated-->', L, 'rated 500 kW', E,
                            'rated 40 kW'])
    got = [q for _n, q in dl.check_quantities(loader_doc)]
    if got != ['40 kW']:
        bad.append(f'doc_lint numbers gate: a loader-block figure is flagged '
                   f'or a hand one missed: {got}')
    pc_src = (ROOT / 'tools' / 'precedent_check.py').read_text(encoding='utf-8')
    if 'generated_blocks.blank(text)' not in pc_src:
        bad.append('precedent_check.py _strip_generated no longer uses the helper')
    pa = importlib.import_module('practice_audit')
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / 'AGENTS.md').write_text('\n'.join(
            ['<!--gen:x-->', 'declined as a duplicate of upstream', '<!--/gen:x-->',
             'this rule is a duplicate of another practice']) + '\n',
            encoding='utf-8')
        hits = [n for _f, n, _t in pa.prose_declines(root)]
        if hits != [4]:
            bad.append(f'practice_audit prose scan: want line 4 only, got {hits}')

    # checks-use-generated-blocks: a check that spells a marker itself is
    # named; one that asks the helper, a test that plants a marker on
    # purpose, and a copy another source wrote here, are not.
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        (repo / 'tools' / 'checks' / 'tests').mkdir(parents=True)
        for f in (ROOT / 'tools').glob('*.py'):
            shutil.copy(f, repo / 'tools' / f.name)
        chk = repo / 'tools' / 'checks'
        (chk / 'check_hand.py').write_text(
            "SKIP = '<!-- BEGIN GENERATED: precedent-loader -->'\n", encoding='utf-8')
        (chk / 'check_helper.py').write_text(
            'import generated_blocks\nmask = generated_blocks.mask\n', encoding='utf-8')
        (chk / 'tests' / 'test_plant.py').write_text(
            "PLANT = '<!--gen:a-->'\n", encoding='utf-8')
        # A check another source wrote here: the consuming repo holds a
        # copy it cannot fix, so it is that source's run that names it.
        (chk / 'check_received.py').write_text(
            "SKIP = '<!--gen:a-->'\n", encoding='utf-8')
        (repo / 'MANIFEST.json').write_text(json.dumps({
            'sources': [{'level': 'shared', 'name': 'zzz-shared', 'path': '/x'}],
            'practices': [],
            'checks': [{'path': 'tools/checks/check_received.py',
                        'source': 'zzz-shared'}]}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'add', '-A'], cwd=repo, capture_output=True)
        r = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                            'checks-use-generated-blocks'], cwd=repo,
                           capture_output=True, text=True)
        named = set(re.findall(r'tools/checks/\S+?\.py', r.stdout))
        if named != {'tools/checks/check_hand.py'}:
            bad.append(f'checks-use-generated-blocks: want only check_hand.py '
                       f'named, got {sorted(named)}: {failure_detail(r.stdout, 300)}')
    # precedent_vendor_engine's AGENTS.md section parser (2026-09-30): it
    # knew only the loader style, and an unclosed opener hid the rest.
    pve = importlib.import_module('precedent_vendor_engine')
    keys = [k for k, _a, _b in pve._md_sections(
        '## A\n<!--gen:x-->\n## hidden\n<!--/gen:x-->\n## B\nb')]
    if keys != ['## A', '## B']:
        bad.append(f'AGENTS.md sections: a gen: block\'s heading counted: {keys}')
    keys = [k for k, _a, _b in pve._md_sections(
        '## A\n<!-- BEGIN GENERATED: precedent-loader -->\nx\n## B\nb')]
    if keys != ['## A', '## B']:
        bad.append(f'AGENTS.md sections: an unclosed opener hid what follows: {keys}')
    check(f'generated_blocks.py finds generated text in both marker styles, '
          f'closing marker required, and the scans use it '
          f'({len(shapes) + 6} stated cases)',
          not bad, '; '.join(bad))


def check_runner_drops_findings_on_received_files():
    """precedent_check.py's runner drops a finding on a file the repository
    RECEIVED -- another source's materialized practice or check, the
    vendored engine, a mirrored tree -- once, for every check, and names the
    source that owns it (precedent_practice_refs.received_owners()).

    WHY. Until 2026-09-29 each check had to remember that skip on its own.
    checks-use-generated-blocks went live without it, and a consuming repo's
    full check judged check files a practice set had written there, which
    the next sync overwrites. So this plants violations in received files
    for several unrelated checks, in a consumer-shaped fixture, and requires
    that none is named -- while the SAME violation in a file the repo wrote
    still is, since a drop that silenced the check would pass the first
    half alone. It also holds the two registrations that must keep their
    findings on received files: a source-supplied check script (its one
    finding carries the script's own path) and
    vendored-engine-file-refs-resolve (its subject is the received copy)."""
    import shutil, tempfile
    bad = []
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_practice_refs as ppr

    # The one definition, in-process: a MANIFEST.json entry of a repo-local
    # source is the repo's own, a mirrored tree matches by prefix.
    with tempfile.TemporaryDirectory() as td:
        r = pathlib.Path(td)
        (r / 'tools').mkdir()
        (r / 'MANIFEST.json').write_text(json.dumps({
            'sources': [{'level': 'repo-local', 'name': 'local', 'path': 'local'},
                        {'level': 'shared', 'name': 'zzz-shared', 'path': '/x'}],
            'practices': [{'slug': 'mine', 'source': 'local'},
                          {'slug': 'theirs', 'source': 'zzz-shared'}],
            'checks': [{'path': 'tools/checks/check_theirs.py',
                        'source': 'zzz-shared'}]}), encoding='utf-8')
        (r / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'files': ['zzz_engine.py']}), encoding='utf-8')
        owners = ppr.received_owners(r)
        owners['vendor/upstream/'] = 'the mirrored tree vendor/upstream/'
        want = {'practices/theirs.md': 'zzz-shared',
                'tools/checks/check_theirs.py': 'zzz-shared',
                'tools/zzz_engine.py': 'the vendored engine',
                'vendor/upstream/practices/x.md':
                    'the mirrored tree vendor/upstream/',
                'practices/mine.md': None, 'docs/x.md': None,
                'vendor/upstreamish.md': None}
        got = {k: ppr.received_owner(k, owners) for k in want}
        if got != want:
            bad.append(f'received_owner: want {want}, got {got}')

    # A consumer-shaped copy of this tree, one run of the whole check.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-received-'))
    try:
        repo = tmp / 'consumer'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', 'prompts'))
        retired = 'team' + ' sets'          # a retired word, built not spelled
        marker = '<!-- BEGIN ' + 'GENERATED: precedent-loader -->'
        (repo / 'MANIFEST.json').write_text(json.dumps({
            'sources': [{'level': 'repo-local', 'name': 'local', 'path': 'local'},
                        {'level': 'shared', 'name': 'zzz-shared', 'path': '/x'}],
            'practices': [{'slug': 'zzz-received', 'source': 'zzz-shared'}],
            'checks': [{'path': 'tools/checks/check_zzz_received.py',
                        'source': 'zzz-shared'}],
            'withheld': []}, indent=1) + '\n', encoding='utf-8')
        # Received: a practice using a retired word, and a check that spells
        # a generated-block marker itself -- and, run as a check, reports.
        (repo / 'practices' / 'zzz-received.md').write_text(
            f'Written by another source. It still says {retired}.\n',
            encoding='utf-8')
        chk = repo / 'tools' / 'checks'
        chk.mkdir(parents=True, exist_ok=True)
        (chk / 'check_zzz_received.py').write_text(
            f'import sys\nSKIP = {marker!r}\n'
            f'print("zzz-received-script-finding")\nsys.exit(1)\n',
            encoding='utf-8')
        # The repo's own copies of the same two violations.
        (repo / 'zzz-own.md').write_text(
            f'Written here. It still says {retired}.\n', encoding='utf-8')
        (chk / 'check_zzz_own.py').write_text(
            f'import sys\nSKIP = {marker!r}\nsys.exit(0)\n', encoding='utf-8')
        for args in (['init', '-q'], ['add', '-A'],
                     ['-c', 'user.email=harness@example.com', '-c',
                      'user.name=harness', 'commit', '-qm', 'consumer']):
            subprocess.run(['git', *args], cwd=repo, capture_output=True)
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(repo / '.no-user-config.json'))
        env.pop('PRECEDENT_LEAK_BLOCKLIST', None)

        def run(*slugs):
            out = ''
            for slug in slugs:
                r = subprocess.run(
                    [sys.executable, 'tools/precedent_check.py', '--only', slug],
                    cwd=repo, capture_output=True, text=True, env=env)
                out += r.stdout + r.stderr
            return out

        out = run('retired-words', 'checks-use-generated-blocks')
        for name in ('practices/zzz-received.md', 'check_zzz_received.py'):
            if name in out:
                bad.append(f'{name} is received, and was named: {failure_detail(out, 400)}')
        for name in ('zzz-own.md', 'check_zzz_own.py'):
            if name not in out:
                bad.append(f'{name} is the repo\'s own, and was NOT named: '
                           f'{failure_detail(out, 400)}')
        if 'for zzz-shared' not in out:
            bad.append(f'no note naming zzz-shared as the owner: {failure_detail(out, 400)}')

        out = run('check_zzz_received')
        if 'zzz-received-script-finding' not in out:
            bad.append(f'a source-supplied check script lost its finding: '
                       f'{failure_detail(out, 400)}')

        # vendored-engine-file-refs-resolve judges the received copy itself.
        (repo / 'tools' / 'ENGINE_MANIFEST.json').write_text(json.dumps(
            {'files': ['zzz_engine.py']}), encoding='utf-8')
        # Built, never spelled: the check scans this very file.
        (repo / 'tools' / 'zzz_engine.py').write_text(
            'X = ROOT / ' + "'tools' / 'zzz_missing.json'\n", encoding='utf-8')
        # The harness asserts files are gone by name, and ships nowhere
        # (2026-10-17): what it names is never a stranded companion.
        (repo / 'tools' / 'verify_harness.py').write_text(
            'Y = ROOT / ' + "'tools' / 'zzz_retired.sh'\n", encoding='utf-8')
        out = run('vendored-engine-file-refs-resolve')
        if 'tools/zzz_engine.py' not in out:
            bad.append(f'vendored-engine-file-refs-resolve went quiet on a '
                       f'received engine file: {failure_detail(out, 400)}')
        if 'zzz_retired.sh' in out:
            bad.append(f'vendored-engine-file-refs-resolve refused the '
                       f'harness naming a file it asserts is gone: {failure_detail(out, 400)}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check('findings on files a repo received are dropped once by the runner '
          'and named by owner; the repo\'s own copies, a source-supplied '
          'check script and vendored-engine-file-refs-resolve still report',
          not bad, '; '.join(bad))


def check_set_refuses_its_own_stranded_deduplication():
    """A practice set's own check refuses a deduplicated practice whose
    target no source the set takes holds.

    WHY. 2026-10-19: an individual set stopped bringing the set that held
    its stub's target. Every consumer's resolver read that as a late
    universal catalogue, said KEPT IN FORCE, ITS TARGET NOT HERE YET, and
    put the old copy back in force everywhere -- the opposite of the
    deduplication -- and four repositories failed their test on main. In
    the set's own checkout the target is never "late", so the check there
    refuses it, in the change that strands it. Planted: the stranded stub;
    the target in a declared universal source; the target in a set the set
    brings; the target nowhere but a brought set that left."""
    import json as _json, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as _pc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-stranded-'))
    cases = []
    saved_root = _pc.ROOT
    saved_env = os.environ.get('PRECEDENT_USER_CONFIG')
    try:
        _sources, _consumer, write = _renamed_universal_fixture(tmp)
        uni, me, held = tmp / 'uni', tmp / 'zz-me', tmp / 'zz-held'
        (tmp / 'uc.json').write_text('{"format_version": 1}', encoding='utf-8')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'uc.json')
        write(me / 'practices' / 'pointer.md', 'pointer', 'deduplicated', 'held-rule')
        (me / 'precedent.json').write_text(_json.dumps({'format_version': 1, 'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '../uni'}]}),
            encoding='utf-8')

        def manifest(brings):
            (me / 'precedent-source.json').write_text(_json.dumps(
                {'name': 'zz-me', 'level': 'individual', 'brings': brings}),
                encoding='utf-8')

        def run():
            _pc.ROOT = me
            try:
                return [str(f.detail if hasattr(f, 'detail') else f)
                        for f in _pc._own_deduplication_points_somewhere(None)]
            except Exception as e:                           # noqa: BLE001
                return [f'raised {type(e).__name__}: {e}']
        manifest([])
        got = run()
        cases.append(('a stub whose target no source holds is refused, naming it',
                      len(got) == 1 and 'no source this set takes holds that rule'
                      in got[0] and 'KEPT IN FORCE' in got[0], got))
        write(held / 'practices' / 'held-rule.md', 'held-rule')
        manifest([{'name': 'zz-held', 'repo_url': 'https://github.com/zz/zz-held'}])
        got = run()
        cases.append(('CONTROL: the target in a set this set brings passes', got == [], got))
        manifest([])
        got = run()
        cases.append(('...and once that set leaves `brings`, it is refused again',
                      len(got) == 1, got))
        write(uni / 'practices' / 'held-rule.md', 'held-rule')
        got = run()
        cases.append(('CONTROL: the target in a declared universal source passes',
                      got == [], got))
    finally:
        _pc.ROOT = saved_root
        if saved_env is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved_env
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f"a set's own check refuses its stranded deduplication "
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_private_scrub_names_a_copied_set_by_its_own_repo():
    """private-repo-scrub names a private set copied INTO a repository by
    the repository its precedent.json entry declares, never by git's
    origin there -- which is the host repository's own -- and never counts
    a repository's own name as a leak from inside it.

    WHY. 2026-10-28: once a private set was copied into a consumer, the
    scrub told it that its practice linking to its own assets/ named "the
    private repository" -- itself."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
        import precedent_resolve as pr
    finally:
        sys.path.pop(0)
    cases = []
    saved = pr.load_config
    with tempfile.TemporaryDirectory() as td:
        host = pathlib.Path(td) / 'host'
        copy = host / 'process' / 'zz-set'
        copy.mkdir(parents=True)
        (copy / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-set', 'level': 'shared', 'visibility': 'private'}))
        subprocess.run(['git', 'init', '-q', str(host)], capture_output=True)
        subprocess.run(['git', '-C', str(host), 'remote', 'add', 'origin',
                        'https://github.com/zz-owner/zz-host'], capture_output=True)
        entry = {'name': 'zz-set', 'level': 'shared', 'path': str(copy),
                 'vendored': True, 'repo': 'https://github.com/zz-owner/zz-set'}
        try:
            pr.load_config = lambda root: [entry]
            names = pc._private_source_names(host)
            cases.append(('a copied private set is named by its declared repo, '
                          'and the host is not named', names == ['zz-owner/zz-set'],
                          names))
            pr.load_config = lambda root: [dict(entry, repo=None)]
            names = pc._private_source_names(host)
            cases.append(('a copy that declares no repo names nothing, never the '
                          'host', names == [], names))
            # 2026-10-29: a consumer's full suite went red on its own
            # repo-local practice naming its own private repository, which
            # ships nowhere. Only the practice MANIFEST.json says is
            # repo-local is skipped; a shared one saying the same is caught.
            import types
            pr.load_config = lambda root: [entry]
            (host / 'practices').mkdir()
            line = 'see zz-owner/zz-set for the voice notes\n'
            (host / 'practices' / 'zz-local.md').write_text(line)
            (host / 'practices' / 'zz-shared.md').write_text(line)
            (host / 'MANIFEST.json').write_text(json.dumps({'practices': [
                {'slug': 'zz-local', 'level': 'repo-local'},
                {'slug': 'zz-shared', 'level': 'shared'}]}))
            got = [str(f) for f in pc._private_repo_scrub(
                types.SimpleNamespace(root=host))]
            cases.append(('a repo-local practice naming a private repo is not '
                          'flagged', not any('zz-local' in g for g in got), got))
            cases.append(('CONTROL: a shared practice naming it is flagged',
                          any('practices/zz-shared.md:1' in g
                              and "names the private repository 'zz-owner/zz-set'"
                              in g for g in got), got))
        finally:
            pr.load_config = saved
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'private-repo-scrub names a copied set by its own repo '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_empty_blocklist_is_not_a_pass():
    """A scrub against a blocklist with no patterns checked nothing, and
    says so everywhere it surfaces: practice_audit.py prints
    EMPTY_BLOCKLIST rather than "clean against 0 blocklist pattern(s)",
    precedent_check.py's scrub-gate reports it SKIPPED rather than passed,
    and the push check's line says "not verified" (2026-10-13, a consumer
    whose blocklist is comments only, on purpose: "1 passed, 0 violated",
    and its pull request's "Scrub gate run" box read as real verification).
    A blocklist with a pattern still scrubs, and a hit still fails."""
    import contextlib, io, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import practice_audit as pa
    import precedent_check as pc
    import precedent_push_check as ppc
    cases = []
    saved = pa.ROOT
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        tree = td / 'vendor'
        tree.mkdir()
        (tree / 'a.md').write_text('a line naming Zorblat\n', encoding='utf-8')
        bl = td / 'blocklist.txt'

        def scrub(text):
            bl.write_text(text, encoding='utf-8')
            fails, out = [], io.StringIO()
            with contextlib.redirect_stdout(out):
                pa.scrub(tree, bl, fails, 'test')
            return fails, out.getvalue()
        try:
            pa.ROOT = td
            fails, out = scrub('# nothing private yet\n\n')
            cases.append(('comments only: says nothing was checked, never "OK"',
                          not fails and pa.EMPTY_BLOCKLIST in out
                          and 'scrub OK' not in out, out))
            fails, out = scrub('# words\nNothingHere\n')
            cases.append(('a pattern and a clean tree: scrub OK',
                          not fails and 'scrub OK' in out
                          and pa.EMPTY_BLOCKLIST not in out, out))
            fails, out = scrub('Zorblat\n')
            cases.append(('a pattern that hits: a SCRUB failure', len(fails) == 1, str(fails)))
        finally:
            pa.ROOT = saved
    real_run = pc._run
    try:
        pc._run = lambda *a: (0, f'scrub [vendor]: {pa.EMPTY_BLOCKLIST} -- nothing was checked\n')
        try:
            pc._scrub_gate(None)
            cases.append(('scrub-gate on an empty blocklist is not a pass', False, 'returned'))
        except pc.NotApplicable as e:
            cases.append(('scrub-gate on an empty blocklist is not a pass',
                          pa.EMPTY_BLOCKLIST in str(e), str(e)))
        pc._run = lambda *a: (1, 'FAIL: SCRUB: a.md:1 matches /x/\n')
        cases.append(('...and a hit is still a finding',
                      len(pc._scrub_gate(None)) == 1, ''))
    finally:
        pc._run = real_run
    marker = ppc.STAND_DOWNS.get('scrub_gate', (None, None))[0]
    cases.append(('the push check reads the same marker as "not verified"',
                  marker == pa.EMPTY_BLOCKLIST, str(marker)))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d[:200]}' for n, d in bad))


def check_dedup_onto_same_slug_withdraws_nothing():
    """changed_slugs() leaves out a set's copy deduplicated onto its own slug.

    WHY. 2026-10-06: the ladder set's four full copies of universal rules
    were cut to stubs with `in_force_at:` their own slug, universal's rule of
    that name staying in force. Every link to `prompt-please` and the other
    three, in every declared source, came back as a FOLLOW-UP to repoint --
    72 of them, none real, since the slug still names a live rule."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    ppr = __import__('precedent_practice_refs')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='dedup-same-slug-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), PRECEDENT_ALLOW_ANY_AUTHOR='1')
    fm = '---\nslug: {s}\nstatus: {st}\nin_force_at: {to}\n---\n## Rule\nR.\n'
    try:
        g = lambda *a: subprocess.run(['git', '-C', str(tmp), *a], env=env,
                                      check=True, capture_output=True)
        g('init', '-q', '-b', 'main')
        (tmp / 'practices').mkdir()
        for s in ('kept-rule', 'moved-rule'):
            (tmp / 'practices' / f'{s}.md').write_text(
                fm.format(s=s, st='active', to='null'), encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('checkout', '-qb', 'work')
        (tmp / 'practices' / 'kept-rule.md').write_text(
            fm.format(s='kept-rule', st='deduplicated', to='kept-rule'), encoding='utf-8')
        (tmp / 'practices' / 'moved-rule.md').write_text(
            fm.format(s='moved-rule', st='deduplicated', to='other-rule'), encoding='utf-8')
        got = ppr.changed_slugs(tmp, 'main')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check('a copy deduplicated onto its own slug is not reported as withdrawn',
          'kept-rule' not in got, repr(got))
    check('CONTROL: a copy deduplicated onto another slug still is',
          got.get('moved-rule') == 'now deduplicated', repr(got))


def check_update_skips_citations_of_a_rule_that_only_grew():
    """Update Vendors sends a consumer to read a citation of a practice only
    when the practice was withdrawn or renamed, or its title or
    index_clause -- the one line a citation paraphrases -- changed. A Rule
    that only grew under the same one-line rule is still said to the merge
    gate (the author's side), and not listed to the consumer.

    WHY. 2026-10-15, a consumer's Update Vendors: the "citations of a
    practice reworded or withdrawn" line flagged AGENTS.md (citing
    reply-links-files) and TODO.md (citing todo-is-a-handoff). Neither
    practice's index_clause or title had changed; both citations still read
    true, and a session read both rules to find that out.

    Negative control, measured 2026-10-15: on staging's code the grown rule
    is reported as plain "Rule reworded" and its citation is listed."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    ppr = __import__('precedent_practice_refs')
    pu = __import__('precedent_update')
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='rule-only-grew-'))
    env = _fixture_git_env()
    fm = ('---\nslug: {s}\ntitle: {t}\nindex_clause: "{c}"\nstatus: active\n'
          '---\n## Rule\n{r}\n')
    cases = []
    try:
        g = lambda *a: subprocess.run(['git', '-C', str(tmp), *a], env=env,
                                      check=True, capture_output=True)
        g('init', '-q', '-b', 'main')
        (tmp / 'practices').mkdir()
        w = lambda s, t, c, r: (tmp / 'practices' / f'{s}.md').write_text(
            fm.format(s=s, t=t, c=c, r=r), encoding='utf-8')
        w('grew', 'A grown rule', 'do the thing', 'Do the thing.')
        w('reclaused', 'A reclaused rule', 'do the thing', 'Do the thing.')
        w('retitled', 'A retitled rule', 'do the thing', 'Do the thing.')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('checkout', '-qb', 'work')
        w('grew', 'A grown rule', 'do the thing',
          'Do the thing.\n\nAnd now, also in a reply.')
        w('reclaused', 'A reclaused rule', 'do the other thing', 'Do the other thing.')
        w('retitled', 'A rule with a new title', 'do the thing', 'Do the thing, said again.')
        got = ppr.changed_slugs(tmp, 'main')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    body_only = getattr(ppr, 'RULE_BODY_ONLY', None)
    cases.append(('a Rule that grew under the same one-line rule is said as that',
                  body_only is not None and got.get('grew') == body_only, repr(got)))
    cases.append(('CONTROL: a changed index_clause is a reworded Rule',
                  got.get('reclaused') == 'Rule reworded', repr(got)))
    cases.append(('CONTROL: a changed title is too',
                  got.get('retitled') == 'Rule reworded', repr(got)))
    hit = lambda slug: {'source': 'this repository', 'kind': 'live',
                        'file': 'AGENTS.md', 'line': 3, 'slug': slug,
                        'must_fix': False}
    data = {'slugs': got, 'successors': {},
            'hits': [hit('grew'), hit('reclaused'), hit('retitled')]}
    fix, read = pu.citation_findings(data)
    cases.append(('Update Vendors lists no citation of the rule that only grew',
                  not fix and len(read) == 2
                  and not any('grew' in r for r in read), repr((fix, read))))
    cases.append(('the merge gate still counts it as reworded, for the author',
                  'grew' in got and got['grew'].startswith('Rule reworded'),
                  repr(got)))
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'Update Vendors skips citations of a rule that only grew '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad)[:3000])


def check_practice_refs_sorts_live_from_history():
    """precedent_practice_refs.py finds every citation of a renamed practice
    in a SET, marks the live pointers as must-fix, and leaves history alone.

    WHY. The go-merge -> go-update rename (2026-09-26) landed clean in
    BestPractice and left `go-merge` cited in the private sets' practices and
    READMEs; nothing asked anyone to look (practice:
    practice-change-propagates). The lookup has to tell a live pointer from
    the record of the rename, or the check built on it either misses the
    drift or refuses every Story that mentions an old name."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr
    ppr = __import__('precedent_practice_refs')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-refs-'))
    cases = []
    try:
        sources, _consumer, write = _renamed_universal_fixture(tmp)
        ind = tmp / 'ind'
        write(ind / 'practices' / 'lineage.md', 'lineage',
              rule='Say the merge target out loud.')
        lineage = ind / 'practices' / 'lineage.md'
        lineage.write_text(
            lineage.read_text(encoding='utf-8')
            + '\n## Detail\nThe old `go-merge` said the same.\n'
              '\nRenamed from `go-merge` on 2026-09-26.\n'
              '\nA wrapped paragraph names `go-merge`\n'
              'and only its next line says it was retired.\n'
              '\n- a list item naming `go-merge` alone\n'
              '- beside one that says retired\n'
              '\n## Story\n[go-merge](go-merge.md) is where it began.\n',
            encoding='utf-8')
        (ind / 'README.md').write_text(
            'Look it up: `python3 tools/precedent_show.py go-merge`.\n',
            encoding='utf-8')
        (ind / 'spec').mkdir()
        (ind / 'spec' / 'plan.md').write_text(
            'Planned against [go-merge](../practices/go-merge.md).\n',
            encoding='utf-8')
        (ind / 'WHATS_NEW.md').write_text(
            '## 2026-09-20\n- Commands read intent (`go-merge` among them).\n',
            encoding='utf-8')
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        for argv in (['init', '-q'], ['add', '-A'], ['commit', '-qm', 'x']):
            subprocess.run(['git', '-C', str(ind), *argv], env=env,
                           capture_output=True, text=True)

        res = _pr.resolve(sources)
        wmap = ppr.withdrawn_map(res)
        cases.append(('go-merge is withdrawn, forwarding to go-update',
                      wmap.get('go-merge', {}).get('successor') == 'go-update',
                      str(wmap)))
        succ = {k: v['successor'] for k, v in wmap.items() if v['successor']}
        rows = ppr.scan_root(ind, set(wmap), succ)

        def tag(rel, text):
            # By the line's own words, not its number: the fixture's
            # frontmatter is somebody else's to change.
            hit = [r for r in rows if r[0] == rel and text in r[6]]
            if not hit:
                return 'absent'
            return 'must-fix' if ppr.must_fix(hit[0], wmap) else hit[0][4]

        cases.append(('a link in an active practice\'s Rule is must-fix',
                      tag('practices/cites.md', 'Sibling:') == 'must-fix', str(rows)))
        cases.append(('a precedent_show.py lookup in a README is must-fix',
                      tag('README.md', 'Look it up') == 'must-fix', str(rows)))
        cases.append(('a bare mention in Detail is live but only listed, '
                      'never refused', tag('practices/lineage.md', 'The old') == 'live',
                      str(rows)))
        cases.append(('a line narrating the rename is history',
                      tag('practices/lineage.md', 'Renamed from') == 'history', str(rows)))
        # The lineage word read across the paragraph, not the line
        # (2026-10-13): prose wraps, and the word lands on the next line.
        cases.append(('a paragraph whose next line narrates the retirement is history',
                      tag('practices/lineage.md', 'A wrapped paragraph') == 'history',
                      str(rows)))
        cases.append(('CONTROL: a list item is its own paragraph, so its '
                      'neighbour\'s lineage word does not reach it',
                      tag('practices/lineage.md', 'list item naming') == 'live',
                      str(rows)))
        cases.append(('a dated WHATS_NEW.md entry is a record, so history',
                      tag('WHATS_NEW.md', 'read intent') == 'history', str(rows)))
        cases.append(('a link inside ## Story is history',
                      tag('practices/lineage.md', 'where it began') == 'history', str(rows)))
        cases.append(('a plan under spec/ is a record, so history',
                      tag('spec/plan.md', 'Planned against') == 'history', str(rows)))
        cases.append(('the individual set\'s own go-merge stub is history',
                      all(r[4] == 'history' for r in rows
                          if r[0] == 'practices/go-merge.md'), str(rows)))

        # NEGATIVE CONTROL: the same lines naming the live slug are not
        # citations of a withdrawn practice at all, so the must-fix findings
        # above were about `go-merge` and nothing else in the fixture.
        for f in (ind / 'README.md', ind / 'practices' / 'cites.md'):
            f.write_text(f.read_text(encoding='utf-8')
                         .replace('go-merge', 'go-update'), encoding='utf-8')
        rows = ppr.scan_root(ind, set(wmap), succ)
        cases.append(('repointed to go-update, nothing is must-fix',
                      not [r for r in rows if ppr.must_fix(r, wmap)],
                      str([r for r in rows if ppr.must_fix(r, wmap)])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the citation lookup finds a renamed practice\'s live pointers and '
          f'leaves its history alone ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:200]}' for n, d in bad))


def check_practice_change_propagates_refuses():
    """The practice-change-propagates check, run as a repository runs it:
    it refuses a live pointer to a renamed practice and a deleted practice
    file, names the successor, and clears when each is fixed.

    WHY. A lookup nobody runs fixes nothing; the check is what makes the
    drift surface in the repository that can repair it -- a private set this
    session could fetch and not push (practice: practice-change-propagates).
    Asserts the check's own words, and each refusal has a control showing
    the same tree, fixed, passes."""
    import shutil as _shutil, tempfile, json as _json
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        sources, _consumer, write = _renamed_universal_fixture(tmp)
        repo = tmp / 'repo'
        repo.mkdir()
        _seed_consumer_engine_isolated(repo)
        # The seed copies the COMMITTED engine; the code under test is this
        # working tree's (the rename-updates-links fixture found this the hard way).
        for name in ('precedent_check.py', 'precedent_practice_refs.py'):
            _shutil.copy2(ROOT / 'tools' / name, repo / 'tools' / name)
        (repo / 'practices').mkdir(exist_ok=True)
        _shutil.copy2(ROOT / 'practices' / 'practice-change-propagates.md',
                      repo / 'practices' / 'practice-change-propagates.md')
        write(repo / 'practices' / 'old-rule.md', 'old-rule')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(tmp / 'uni')}]}), encoding='utf-8')
        (repo / 'README.md').write_text(
            'Before merging, read `python3 tools/precedent_show.py go-merge`.\n',
            encoding='utf-8')
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1',
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-user-config.json'),
                   GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')

        def g(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=env)
        g('init', '-q', '-b', 'main')
        g('add', '-A'); g('commit', '-qm', 'base')
        g('update-ref', 'refs/remotes/origin/main', 'HEAD')
        g('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')

        def run():
            r = subprocess.run(
                [sys.executable, 'tools/precedent_check.py',
                 '--only', 'practice-change-propagates'],
                capture_output=True, text=True, cwd=str(repo), env=env,
                timeout=300)
            return r.stdout + r.stderr

        out = run()
        cases.append(('a README lookup of the renamed slug is refused, with '
                      'the successor named',
                      'README.md:1: looks up `go-merge`' in out
                      and 'cite `go-update`' in out, failure_detail(out, 600)))
        g('rm', '-q', 'practices/old-rule.md'); g('commit', '-qm', 'drop it')
        out = run()
        cases.append(('deleting a practice file is refused',
                      'practices/old-rule.md: this branch deleted a practice '
                      'file. Retire it in place' in out, failure_detail(out, 600)))

        # CONTROLS: fix each, and the same check passes on the same tree.
        g('revert', '--no-edit', 'HEAD')
        # Another source this repo declares, on disk, still links the
        # practice this branch is about to retire (2026-10-01: a shared
        # set's todo-gate.md linked second-pass-capture after the dedupe).
        shared = tmp / 'shared-set'
        write(shared / 'practices' / 'todo-gate.md', 'todo-gate',
              rule='Then run the [old rule](old-rule.md) pass.')
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(shared)],
                       capture_output=True, env=env)
        subprocess.run(['git', '-C', str(shared), 'add', '-A'],
                       capture_output=True, env=env)
        subprocess.run(['git', '-C', str(shared), 'commit', '-qm', 'set'],
                       capture_output=True, env=env)
        cfg = _json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        cfg['sources'].append({'level': 'shared', 'name': 'shared-set',
                               'path': str(shared)})
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        write(repo / 'practices' / 'old-rule.md', 'old-rule', 'deduplicated',
              'go-update')
        (repo / 'README.md').write_text(
            'Before merging, read `python3 tools/precedent_show.py go-update`.\n',
            encoding='utf-8')
        g('add', '-A'); g('commit', '-qm', 'retire in place, repoint')
        out = run()
        cases.append(('retired in place and repointed, the check passes',
                      '1 passed, 0 violated' in out, failure_detail(out, 2500)))
        cases.append(('...and the shared set\'s link to the practice this '
                      'branch retired is reported as a follow-up there, '
                      'with the file and line',
                      'FOLLOW-UP in shared-set' in out
                      and 'shared-set:practices/todo-gate.md:1' in out
                      and '`old-rule`' in out, failure_detail(out, 900)))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'practice-change-propagates refuses a live pointer to a renamed '
          f'practice and a deleted practice file, and clears when fixed '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:300]}' for n, d in bad))


def check_source_supplied_checks_run():
    """A `checked_by: tools/checks/check_x.py` claim actually RUNS.

    Before precedent_check.register_materialized_checks() existed, nothing
    anywhere invoked those scripts. precedent_materialize.py copied them
    into a consuming repo, precedent_land.py refused to land a team or
    individual practice without one, and spec/PRIVATE_ENFORCEMENT_BRIEF.md
    told a private set how to write one -- and then a consuming repo held
    fourteen real, tested check scripts (nine in precedent-team-repo-maintenance,
    five in precedent-individual, as of 2026-09-06) that no command ever
    ran. The enforced channel was live for the universal catalogue and
    hollow for exactly the sources an adopting team writes for itself.

    Proves all four of the contract's exit statuses, and both routes a
    script reaches a repo by (materialized into tools/checks/, and a
    repo-local source's own local/tools/checks/ read in place)."""
    import shutil, tempfile, importlib.util
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-srcchecks-'))
    cases = []
    try:
        repo = tmp / 'repo'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'tools' / 'checks').mkdir(parents=True)
        (repo / 'local' / 'tools' / 'checks').mkdir(parents=True)
        shutil.copy(ROOT / 'tools' / 'precedent_check.py', repo / 'tools')
        shutil.copy(ROOT / 'tools' / 'split_practices.py', repo / 'tools')
        shutil.copy(ROOT / 'tools' / 'doc_lint.py', repo / 'tools')
        # fixture-owns-its-state: precedent_check.py imports this at module
        # scope (practice: timestamps-carry-offset), so a fixture engine tree
        # without it does not degrade -- every case here dies on the import.
        shutil.copy(ROOT / 'tools' / 'precedent_time.py', repo / 'tools')
        shutil.copy(ROOT / 'tools' / 'generated_blocks.py', repo / 'tools')
        shutil.copy(ROOT / 'tools' / 'declared_base_branch.py', repo / 'tools')
        (repo / 'AGENTS.md').write_text('# fixture\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=repo, capture_output=True)

        def practice(slug, checked_by):
            (repo / 'practices' / f'{slug}.md').write_text(
                f'---\nslug:        {slug}\ntitle:       {slug}\n'
                f'tier:        on-demand\nseverity:    default\n'
                f'applies_to:  ["**"]\noccasion:    "fixture"\ngates:       []\n'
                f'index_clause: "{slug} — fixture"\n'
                f'checked_by:  "{checked_by}"\ndefines:     []\nstatus:      active\n'
                f'supersedes:  []\noverrides:   null\nadded:       2026-09-06\n'
                f'approved_by: "harness"\nsource_practice_number: null\n---\n'
                f'## Rule\nThe Rule text of {slug}, which the runner must print.\n\n'
                f'## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')

        def script(path, body):
            path.write_text('#!/usr/bin/env python3\nimport sys\n' + body,
                            encoding='utf-8')

        practice('fx-clean', 'tools/checks/check_fx_clean.py')
        practice('fx-violated', 'tools/checks/check_fx_violated.py')
        practice('fx-skipped', 'tools/checks/check_fx_skipped.py')
        practice('fx-broken', 'tools/checks/check_fx_broken.py')
        script(repo / 'tools' / 'checks' / 'check_fx_clean.py', 'sys.exit(0)\n')
        script(repo / 'tools' / 'checks' / 'check_fx_violated.py',
               'print("VIOLATION: fx-violated")\nprint("  a planted finding")\n'
               'print("")\nprint("the rule:")\nprint("  a stale copy of the Rule")\n'
               'sys.exit(1)\n')
        script(repo / 'tools' / 'checks' / 'check_fx_skipped.py',
               'print("SKIPPED: fx-skipped: no network here")\nsys.exit(2)\n')
        script(repo / 'tools' / 'checks' / 'check_fx_broken.py',
               'print("boom")\nsys.exit(3)\n')

        # the repo-local route: a source that cannot materialize into itself
        (repo / 'local' / 'practices').mkdir(parents=True)
        (repo / 'local' / 'practices' / 'fx-local.md').write_text(
            (repo / 'practices' / 'fx-clean.md').read_text(encoding='utf-8')
            .replace('fx-clean', 'fx-local')
            .replace('check_fx_clean.py', 'check_fx_local.py'), encoding='utf-8')
        script(repo / 'local' / 'tools' / 'checks' / 'check_fx_local.py',
               'print("VIOLATION: fx-local")\nprint("  the repo-local finding")\n'
               'sys.exit(1)\n')

        def run(slug):
            r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                                '--only', slug], cwd=repo,
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        rc, out = run('fx-clean')
        cases.append(('exit 0 with no output is a PASS', rc == 0 and 'PASS' not in out
                      and 'VIOLATION' not in out, out))
        rc, out = run('fx-violated')
        cases.append(('exit 1 is a VIOLATION carrying the script\'s finding',
                      rc == 1 and 'VIOLATION  fx-violated' in out
                      and 'a planted finding' in out, out))
        cases.append(("the runner prints the practice's own Rule, not the "
                      "script's stale copy of it",
                      'which the runner must print' in out
                      and 'a stale copy of the Rule' not in out, out))
        rc, out = run('fx-skipped')
        cases.append(('exit 2 is SKIPPED with the reason, never a pass',
                      rc == 0 and 'SKIPPED' in out and 'no network here' in out
                      and 'PASS' not in out, out))
        rc, out = run('fx-broken')
        cases.append(("any other exit status is the script's own bug: ERROR, "
                      "which is neither a pass nor a violation",
                      rc == 1 and 'ERROR' in out and 'exited 3' in out
                      and 'VIOLATION' not in out, out))
        rc, out = run('fx-local')
        cases.append(("a repo-local source's own local/tools/checks/ script "
                      "runs in place, for a repo that cannot materialize "
                      "into itself",
                      rc == 1 and 'the repo-local finding' in out, out))

        # A repo-local check that IS also materialized exists twice, and the
        # two copies need different ROOT depths from the same file. Running
        # the local original in place resolves ROOT to <repo>/local, where
        # the repo's real files are not -- two of a real consuming repo's
        # own checks reported `no book-*/ directory exists` and
        # `README.md: file does not exist` about files in plain view
        # (2026-09-06). Alphabetical order was deciding it: `local/...`
        # sorts before `tools/...`, so the wrong copy won every time.
        script(repo / 'local' / 'tools' / 'checks' / 'check_fx_both.py',
               'print("VIOLATION: fx-both")\nprint("  ran the LOCAL copy")\n'
               'sys.exit(1)\n')
        (repo / 'local' / 'practices' / 'fx-both.md').write_text(
            (repo / 'practices' / 'fx-clean.md').read_text(encoding='utf-8')
            .replace('fx-clean', 'fx-both')
            .replace('check_fx_clean.py', 'check_fx_both.py'), encoding='utf-8')
        script(repo / 'tools' / 'checks' / 'check_fx_both.py', 'sys.exit(0)\n')
        rc, out = run('fx-both')
        cases.append(('when a repo-local check has been materialized too, the '
                      'MATERIALIZED copy runs -- the two locations need '
                      'different ROOT depths and only that one is right',
                      rc == 0 and 'ran the LOCAL copy' not in out, out))

        spec = importlib.util.spec_from_file_location(
            '_pc_fx', repo / 'tools' / 'precedent_check.py')
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        before = set(pc.CHECKS)
        pc.register_materialized_checks()
        added = set(pc.CHECKS) - before
        cases.append(('the slug comes from the practice that CLAIMS the '
                      'script, not from the filename',
                      {'fx-clean', 'fx-violated', 'fx-skipped', 'fx-broken',
                       'fx-local', 'fx-both'} <= added, str(sorted(added))))

        # A script's inputs select it, not only its practice's applies_to: a
        # consumer's check of a page's practice list reads every practice's
        # applies_to, a new practice landed without its row, and the
        # rotation left the check for later (2026-10-19).
        reads = repo / 'tools' / 'checks' / 'check_fx_reads.py'
        script(reads, 'fm = {}\nfm.get("applies_to")\nsys.exit(0)\n')
        declares = repo / 'tools' / 'checks' / 'check_fx_declares.py'
        script(declares, 'SELECTS_ON = ("pages/*.md", "**")\nsys.exit(0)\n')
        cases.append(('a script that reads applies_to is selected by any '
                      'practice file', set(pc.script_selects_on(reads))
                      >= {'practices/*.md', 'local/practices/*.md'},
                      repr(pc.script_selects_on(reads))))
        cases.append(('a script\'s own SELECTS_ON is read without running it, '
                      'and a bare ** in it adds nothing',
                      pc.script_selects_on(declares) == ('pages/*.md',),
                      repr(pc.script_selects_on(declares))))
        cases.append(('a script that declares nothing and reads no applies_to '
                      'is selected exactly as before',
                      pc.script_selects_on(repo / 'tools' / 'checks'
                                           / 'check_fx_clean.py') == (), ''))
        pc.register_materialized_checks()
        cases.append(('...and the registered check carries those globs, where '
                      'the change-driven selection reads them',
                      'practices/*.md' in (pc.CHECKS.get('check_fx_reads', {})
                                           .get('selects_on') or ()),
                      repr(pc.CHECKS.get('check_fx_reads', {}).get('selects_on'))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'source-supplied checks actually run ({len(cases)} stated cases: '
          f'all four exit statuses, both routes into a repo, and the slug '
          f'taken from the claiming practice)',
          not bad, '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_refresh_judges_workflows_once_the_engine_is_whole():
    """An engine release that adds a module took two Update Vendors runs to
    finish (2026-09-30, a consumer updating from 99941178): the second pass
    of the self-replacing refresh judged workflow approvals at its top, by
    importing a precedent_check.py the first pass had already replaced,
    before it wrote the generated_blocks.py that file now imports. So the
    first run ended "no approval could be judged ... did not import", with
    the reason hidden. Discriminating cases, on a planted engine directory:
    during refresh's opening sweep a failed import is deferred, not left
    for the person; once the engine is whole the deferred judgment runs and
    removes an unapproved workflow; and outside refresh the failure is
    still left for the person, now naming the exception."""
    import contextlib, io, shutil, subprocess, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='wf-judge-'))
    saved_dir, saved_mod = pve.ENGINE_DIR, sys.modules.pop('precedent_check', None)
    cases = []
    try:
        eng, dest = tmp / 'eng', tmp / 'dest'
        eng.mkdir()
        (dest / '.github' / 'workflows').mkdir(parents=True)
        git = lambda *a: subprocess.run(['git', '-C', str(dest), *a],
                                        capture_output=True, text=True)
        git('init', '-q')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.com')
        wf = dest / '.github' / 'workflows' / 'extra.yml'
        wf.write_text('on: push\njobs: {}\n', encoding='utf-8')
        (dest / 'precedent.json').write_text('{}\n', encoding='utf-8')
        git('add', '-A')
        git('commit', '-q', '-m', 'seed\n\nSession: none available (test)')
        (eng / 'precedent_check.py').write_text(
            'import generated_blocks_not_written_yet\n', encoding='utf-8')
        pve.ENGINE_DIR = eng
        pve._LEFT_FOR_YOU.clear()
        pve._DEFER_WORKFLOW_JUDGMENT = True
        with contextlib.redirect_stdout(io.StringIO()):
            pve._remove_unapproved_workflows(dest, {}, 'consumer', None)
        pve._DEFER_WORKFLOW_JUDGMENT = False
        cases.append(('in refresh\'s opening sweep, a failed import is '
                      'deferred, not left for the person',
                      len(pve._DEFERRED_WORKFLOW_JUDGMENT) == 1
                      and not pve._LEFT_FOR_YOU, repr(pve._LEFT_FOR_YOU)))
        (eng / 'precedent_check.py').write_text(
            'def _approval_problem(entry):\n    return "fixture"\n',
            encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            pve._judge_deferred_workflows()
        cases.append(('once the engine is whole, the deferred judgment runs '
                      'and the unapproved workflow goes', not wf.exists(),
                      repr(pve._LEFT_FOR_YOU)))
        git('checkout', '-q', 'HEAD', '--', '.github/workflows/extra.yml')
        git('reset', '-q', '--hard')
        (eng / 'precedent_check.py').write_text(
            'import generated_blocks_not_written_yet\n', encoding='utf-8')
        sys.modules.pop('precedent_check', None)
        pve._LEFT_FOR_YOU.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            pve._remove_unapproved_workflows(dest, {}, 'consumer', None)
        said = ' '.join(str(x) for x in pve._LEFT_FOR_YOU)
        cases.append(('outside refresh the failure is still left for the '
                      'person, naming the exception',
                      'generated_blocks_not_written_yet' in said, said[:300]))
    finally:
        pve.ENGINE_DIR = saved_dir
        pve._DEFER_WORKFLOW_JUDGMENT = False
        pve._DEFERRED_WORKFLOW_JUDGMENT.clear()
        pve._LEFT_FOR_YOU.clear()
        sys.modules.pop('precedent_check', None)
        if saved_mod is not None:
            sys.modules['precedent_check'] = saved_mod
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a refresh judges workflows once the engine is whole '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_engine_check_refuses_from_another_repo():
    """precedent_check.py run from inside ANOTHER repository that has its own
    copy prints no pass/fail line and exits 2 (precedent_which_repo.
    elsewhere_refusal).

    THE COST IT PAID FOR (2026-10-20). From precedent-shared-ladder,
    `python3 <BestPractice>/tools/precedent_check.py --only
    boildown-moments-named` printed the WRONG REPO banner, then "1 passed,
    0 violated", exit 0: a pass about BestPractice, read off the summary line
    as one about the ladder set.

    Cases: refused, with no summary line, from a repo with its own copy;
    run as usual from inside ROOT, from a linked worktree of ROOT, from a
    directory in no repo, and from a repo with no copy of its own (which
    only warns); `--repo ROOT` runs it on purpose from anywhere; `--repo`
    naming the other repo is refused."""
    import subprocess as _sp
    import tempfile
    script = ROOT / 'tools' / 'precedent_check.py'
    if not (ROOT / 'tools' / 'precedent_which_repo.py').is_file():
        not_applicable('precedent_check refuses from another repo',
                       'no precedent_which_repo.py')
        return
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='wrong-repo-'))
    summary = 'precedent_check:'

    def run(cwd, *extra):
        r = _sp.run([sys.executable, str(script), '--only',
                     'boildown-moments-named', *extra], cwd=str(cwd),
                    capture_output=True, text=True, timeout=300)
        return r.returncode, r.stdout + r.stderr

    try:
        other, bare_repo, nowhere = tmp / 'other', tmp / 'bare-repo', tmp / 'nowhere'
        for d in (other, bare_repo, nowhere):
            d.mkdir()
        for d in (other, bare_repo):
            _sp.run(['git', 'init', '-q', str(d)], check=True)
        (other / 'tools').mkdir()
        (other / 'tools' / 'precedent_check.py').write_text('# its own\n')

        rc, out = run(other)
        cases.append(('from a repo with its own copy: exit 2, no summary line, '
                      'and it names that copy',
                      rc == 2 and summary not in out
                      and str(other / 'tools' / 'precedent_check.py') in out,
                      failure_detail(out, 400)))
        rc, out = run(other, '--repo', str(ROOT))
        cases.append(('--repo naming this repo runs it on purpose',
                      rc == 0 and summary in out, failure_detail(out, 400)))
        rc, out = run(ROOT, '--repo', str(other))
        cases.append(('--repo naming the other repo is refused',
                      rc == 2 and summary not in out, failure_detail(out, 400)))
        rc, out = run(ROOT)
        cases.append(('from inside ROOT it runs', rc == 0 and summary in out,
                      failure_detail(out, 400)))
        rc, out = run(nowhere)
        cases.append(('from a directory in no repo it runs',
                      rc == 0 and summary in out, failure_detail(out, 400)))
        rc, out = run(bare_repo)
        cases.append(('from a repo with no copy of its own it warns and runs',
                      rc == 0 and summary in out and 'WRONG REPO' in out,
                      failure_detail(out, 400)))
        wt = tmp / 'wt'
        if _sp.run(['git', '-C', str(ROOT), 'worktree', 'add', '-q', '--detach',
                    str(wt), 'HEAD'], capture_output=True).returncode == 0:
            try:
                rc, out = run(wt)
                cases.append(('from a linked worktree of ROOT it runs',
                              rc == 0 and summary in out, failure_detail(out, 400)))
            finally:
                _sp.run(['git', '-C', str(ROOT), 'worktree', 'remove', '--force',
                         str(wt)], capture_output=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'precedent_check refuses, with no pass line, from another repo '
          f'that has its own copy ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_check_summary_names_the_repo_it_checked():
    """precedent_check.py's summary line, the one a reader of the tail keeps,
    says when the repo it checked is not the one the reader stands in.

    WHY (2026-10-20). A session ran BestPractice's precedent_check.py from
    another checkout and read the summary's pass as that checkout's. The
    banner at the start (check_engine_tools_say_which_repo_they_read) had
    printed, and scrolled away.

    Negative control, measured 2026-10-20 on the old code: the summary line
    from another repo carries no repo name at all."""
    import subprocess as _sp
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_which_repo as pwr
    mine = pwr.describe(ROOT)['name']
    cases = []
    other = pathlib.Path(tempfile.mkdtemp()) / 'some-other-repo'
    try:
        other.mkdir()
        _sp.run(['git', 'init', '-q', str(other)], check=True)

        def summary(cwd):
            r = _sp.run([sys.executable, str(ROOT / 'tools' / 'precedent_check.py'),
                         '--only', 'doc-references-are-links'], cwd=str(cwd),
                        capture_output=True, text=True, timeout=300)
            return next((l for l in reversed(r.stdout.splitlines())
                         if l.startswith('precedent_check: ')), '')

        line = summary(other)
        cases.append(('THE DISCRIMINATING CASE: from another repo, the summary line '
                      'names the repo checked and the one stood in',
                      f'WRONG REPO: this was {mine}' in line
                      and 'some-other-repo' in line, failure_detail(line, 300)))
        line = summary(ROOT)
        cases.append(('negative control: from inside the repo it checks, the summary '
                      'line says nothing of it', bool(line) and 'WRONG REPO' not in line,
                      failure_detail(line, 300)))
        cases.append(('the note is empty for one repo',
                      pwr.elsewhere_note(ROOT, cwd=ROOT) == '', ''))
    finally:
        shutil.rmtree(other.parent, ignore_errors=True)
        sys.path.pop(0)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the check\'s summary line names the repo it checked when that is '
          f'not where the reader stands ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_a_registry_file_can_be_a_checks_own_opt_in():
    """`binds_when` lifts the practice-file gate for a repo that kept the
    registry carrying the rule (practice: control-asserts-which-failure).

    THE COST IT PAID FOR (2026-09-22). A repo that declares ceilings in
    `tools/session_load_budgets.json` and does not vendor
    `practices/session-load-budget.md` got a SKIP whose reason read "this
    check belongs to a source this repo does not resolve" -- true of the
    practice, wrong about the registry, which was sitting in the repo. So the
    numbers were declared and nothing local tested them.

    BOTH DIRECTIONS, because a gate that lifts for everything is not a gate:
    the check runs where the named file exists and still skips where it does
    not. Asserted through `run()` rather than by reading the CHECKS entry --
    the registration is not the behaviour, and it was the gate in `run()`
    that was wrong."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    cases = []
    reg = pc.CHECKS['session-load-budget']
    cases.append(('session-load-budget names the registry as its opt-in',
                  reg.get('binds_when') == ('tools/session_load_budgets.json',),
                  repr(reg.get('binds_when'))))
    cases.append(('and a commit touching AGENTS.md or the registry SELECTS it, '
                  'so a repo without the practice file can still reach it '
                  'without waiting for the rotation',
                  'AGENTS.md' in (reg.get('selects_on') or ())
                  and 'tools/session_load_budgets.json' in
                  (reg.get('selects_on') or ()),
                  repr(reg.get('selects_on'))))

    # The gate itself, driven through run() with the practice file made
    # invisible -- which is the state of every repo this is for.
    class Ctx:
        def read_base(self, rel):
            return None

    def gate(slug, practice_file):
        orig = pc._practice_file
        pc._practice_file = lambda s: practice_file
        try:
            res = pc.run([slug], Ctx(), (pc.CHECKS[slug]['scope'],))
        finally:
            pc._practice_file = orig
        return res[0][1], res[0][3]

    status, why = gate('session-load-budget', None)
    cases.append(('THE CASE THAT WAS SKIPPING: no practice file, registry '
                  'present -- the check RUNS', status != 'SKIPPED',
                  f'{status}: {why}'))

    # A practice-backed check with no binds_when, same missing practice file.
    control = next(s for s, c in pc.CHECKS.items()
                   if c['practice_backed'] and not c.get('binds_when')
                   and not c.get('binds_publishers')
                   and c['scope'] == pc.CHECKS['session-load-budget']['scope'])
    status, why = gate(control, None)
    cases.append((f'THE DISCRIMINATING CASE: a check with no binds_when '
                  f'({control}) still skips on a missing practice file -- the '
                  f'gate was lifted for one rule, not removed',
                  status == 'SKIPPED', f'{status}: {why}'))

    # And the Rule line says where to read it rather than reporting a gap.
    rule = None
    orig = pc._practice_file
    pc._practice_file = lambda s: None
    try:
        rule = pc.rule_of('session-load-budget')
    finally:
        pc._practice_file = orig
    cases.append(('the Rule line names where to read the practice instead of '
                  'printing "(no practice file for ...)"',
                  'no practice file for' not in rule
                  and 'session_load_budgets.json' in rule, rule))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a repo opts a check in by keeping the registry that carries its '
          f'rule ({len(cases)} stated cases, a check without binds_when being '
          f'the discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_environment_gotchas_follows_a_split_index():
    """A split gotchas section is still held to the story rule
    (practice: control-asserts-which-failure).

    WHY THIS CONTROL EXISTS. Splitting the section -- one line per trap in
    AGENTS.md, the stories in record/GOTCHAS.md -- is a reduction that looks
    exactly like the failure the rule forbids: an instructions file full of
    bare symptoms with no account of what failed. The difference is entirely
    in whether the links resolve to real, whole entries, so the check has to
    FOLLOW them. A check that stopped at the section would pass a repo that
    deleted the record outright, and would do it silently.

    Each case asserts the SPECIFIC message, not merely that something was
    reported: a broken link and a gutted entry are different repairs, and a
    control that cannot tell them apart lets one masquerade as the other.
    The fixture owns its own tree (fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    SECTION = ('# fixture\n\n## Build-environment gotchas -- do NOT rediscover '
               'these\n\n'
               '- **A trap with its story elsewhere.** [story](record/GOTCHAS.md#g1)\n\n'
               '- **A second trap.** [story](record/GOTCHAS.md#g2)\n\n'
               '- **A third trap.** [story](record/GOTCHAS.md#g3)\n\n'
               '## Next\n')
    STORY = ('It failed on 2026-09-13 in a way that read as something else '
             'entirely, and the session spent an hour on the wrong '
             'hypothesis. The remedy is to check the exit code rather than '
             'the printed output.\n')

    def record(entries):
        out = ['# Gotchas\n']
        for n, body in entries:
            out.append(f'\n## {n}. <a id="g{n}"></a>Entry {n}\n\n{body}\n')
        return ''.join(out)

    def run(agents, rec):
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            (d / 'record').mkdir()
            (d / 'AGENTS.md').write_text(agents, encoding='utf-8')
            if rec is not None:
                (d / 'record' / 'GOTCHAS.md').write_text(rec, encoding='utf-8')
            old = pc.ROOT
            pc.ROOT = d
            try:
                findings = pc._environment_gotchas(None)
            finally:
                pc.ROOT = old
            return '; '.join(str(f) for f in findings)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    whole = record([(1, STORY), (2, STORY), (3, STORY)])
    cases = []

    out = run(SECTION, whole)
    cases.append(('THE DISCRIMINATING CASE: a split section whose links all '
                  'resolve to whole entries raises nothing', out == '', out))

    gutted = record([(1, STORY), (2, 'Use `git cat-file -e`.\n'), (3, STORY)])
    out = run(SECTION, gutted)
    cases.append(('an entry gutted to a bare fix is reported against the '
                  'RECORD, not the instructions file',
                  'record/GOTCHAS.md:' in out and 'bare fix' in out, out))

    out = run(SECTION, record([(1, STORY), (2, STORY)]))
    cases.append(('an index line pointing at an anchor the record does not '
                  'have names that anchor',
                  'record/GOTCHAS.md#g3' in out and 'does not exist' in out,
                  out))

    out = run(SECTION, None)
    cases.append(('a section indexing a record that is not there says every '
                  'line leads nowhere, rather than passing',
                  'leads nowhere' in out, out))

    unsplit = ('# fixture\n\n## Build-environment gotchas -- do NOT rediscover '
               'these\n\n- **A trap.** ' + STORY + '\n## Next\n')
    out = run(unsplit, None)
    cases.append(('an UNSPLIT section is still judged on its own entries, so '
                  'a repo that never split is unaffected', out == '', out))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'environment-gotchas follows a split index into the record '
          f'({len(cases)} stated cases, the all-resolving split being the '
          f'discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_environment_gotchas_advises_migrating_an_inline_catalogue():
    """The pre-migration fallback of `environment-gotchas` still validates
    an inline catalogue, AND says to move it to gotchas/ -- as advice that
    never fails the run (practice: control-asserts-which-failure).

    WHY. Until 2026-09-28 a consumer with no gotchas/ directory passed this
    check green forever while carrying the catalogue in AGENTS.md, which the
    Rule says must not load there at all, and nothing ever told it to
    migrate. Turning that into a violation would redden every unmigrated
    consumer on the day the engine is vendored, so the fallback prints an
    advisory instead and keeps its validation.

    Four stated cases. THE DISCRIMINATING ONE is the clean inline section:
    it must print the advisory AND return no finding -- a finding there
    would make the advice a gate. A gutted inline entry still returns its
    bare-fix finding, so the validation did not go away with the advice;
    and a migrated repo prints no advisory. The fixture owns its own tree
    (fixture-owns-its-state)."""
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    STORY = ('It failed on 2026-09-13 in a way that read as something else '
             'entirely, and the session spent an hour on the wrong '
             'hypothesis. The remedy is to check the exit code rather than '
             'the printed output.')
    HEAD = ('# fixture\n\n## Build-environment gotchas -- do NOT rediscover '
            'these\n\n')

    def run(agents, gotcha=None):
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            (d / 'AGENTS.md').write_text(agents, encoding='utf-8')
            if gotcha is not None:
                (d / 'gotchas').mkdir()
                (d / 'gotchas' / 'gotcha-2026-09-13-a-trap.md').write_text(
                    gotcha, encoding='utf-8')
            old = pc.ROOT
            pc.ROOT = d
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    findings = pc._environment_gotchas(None)
            finally:
                pc.ROOT = old
            return '; '.join(str(f) for f in findings), buf.getvalue()
        finally:
            shutil.rmtree(d, ignore_errors=True)

    ADVICE = 'migrate to gotchas/ (spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 2)'
    cases = []

    found, said = run(HEAD + '- **A trap.** ' + STORY + '\n\n## Next\n')
    cases.append(('THE DISCRIMINATING CASE: a clean inline catalogue prints '
                  'the advisory and returns no finding',
                  found == '' and ADVICE in said and 'ADVISORY' in said
                  and 'AGENTS.md' in said, f'findings={found!r} said={said!r}'))

    found, said = run(HEAD + '- **A trap.** Use `git cat-file -e`.\n\n'
                             '## Next\n')
    cases.append(('a bare-fix inline entry is still a finding, with the '
                  'advisory printed beside it',
                  'bare fix' in found and ADVICE in said,
                  f'findings={found!r} said={said!r}'))

    found, said = run(HEAD + '- **A trap.** [story](record/GOTCHAS.md#g1)\n'
                             '\n## Next\n')
    cases.append(('an index into a pre-migration record gets the advisory '
                  'too, and its own finding stays',
                  'leads nowhere' in found and ADVICE in said,
                  f'findings={found!r} said={said!r}'))

    migrated = ('---\nstatus: live\n---\n\n## Symptom\n\nA command reports '
                'success and did nothing.\n\n## Story\n\n' + STORY +
                '\n\n## Fix\n\nCheck the exit code.\n')
    found, said = run(HEAD + 'Grep [gotchas/](gotchas/) before concluding a '
                             'failure is new.\n\n## Next\n', migrated)
    cases.append(('a migrated repo prints no advisory',
                  found == '' and ADVICE not in said,
                  f'findings={found!r} said={said!r}'))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'environment-gotchas advises migrating an inline catalogue to '
          f'gotchas/ without failing on it ({len(cases)} stated cases, the '
          f'clean inline section being the discriminating one)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_debut_judges_the_change_against_main_too():
    """A Debut judges what depends on the base against main as well as
    staging, so a green Debut cannot be followed by a red main (2026-10-17).

    That day a Debut passed on staging and Produce turned main red: staging
    had deleted a file a page still named, the full suite measured the
    change from staging (where nothing was deleted), and GitHub's test of
    the pull request into main measured it from main. Three pieces:

    - precedent_check.py takes the base from PRECEDENT_CHANGED_SINCE first,
      when it names a commit (the push check already set it, and nothing
      read it), and falls back as before when it does not;
    - --base-dependent selects only the checks a base can change -- every
      change-scope check and each tree check reaching the resolver -- so the
      second pass is seconds, never a second suite (Morgan: "It should
      NOT");
    - --run-tests runs that pass with main's tip as the base, and fails,
      naming the check, when it finds what main would; so does Produce,
      before it pushes the copy, since a Debut is optional and the quick
      tier of an upstream repository runs no rename check."""
    import tempfile, importlib.util as _u
    name = 'the Debut judges the change against main too'
    pc_path = ROOT / 'tools' / 'precedent_check.py'
    if not (ROOT / 'tools' / 'precedent_branches.py').exists() or not pc_path.exists():
        not_applicable(name, 'precedent_branches.py or precedent_check.py is absent')
        return
    cases = []
    saved = sys.argv
    sys.argv = ['precedent_check.py']
    try:
        spec = _u.spec_from_file_location('_vh_pc_base', pc_path)
        pc = _u.module_from_spec(spec)
        spec.loader.exec_module(pc)
    finally:
        sys.argv = saved
    old = os.environ.pop('PRECEDENT_CHANGED_SINCE', None)
    try:
        plain = pc._published_default_branch()
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        os.environ['PRECEDENT_CHANGED_SINCE'] = head
        named = pc._published_default_branch()
        os.environ['PRECEDENT_CHANGED_SINCE'] = 'no-such-ref-anywhere'
        bogus = pc._published_default_branch()
    finally:
        os.environ.pop('PRECEDENT_CHANGED_SINCE', None)
        if old is not None:
            os.environ['PRECEDENT_CHANGED_SINCE'] = old
    cases.append(('PRECEDENT_CHANGED_SINCE naming a commit is the base',
                  bool(head) and named == head, f'{named!r}'))
    cases.append(('one naming nothing falls back to the usual base',
                  bogus == plain, f'{bogus!r} vs {plain!r}'))
    picks = getattr(pc, 'base_dependent_slugs', lambda: [])()
    change = {s for s, c in pc.CHECKS.items() if c['scope'] == 'change'}
    cases.append(('--base-dependent takes every change-scope check',
                  bool(picks) and change <= set(picks),
                  ', '.join(sorted(change - set(picks)))[:200]))
    cases.append(('...and the tree checks that read the base, through a '
                  'helper too (rename-updates-links, change-updates-its-docs)',
                  {'rename-updates-links', 'change-updates-its-docs'} <= set(picks)))
    cases.append(('...and not the rest: a check that never reads the base '
                  '(light-check) is not run twice',
                  'light-check' not in picks and len(picks) < len(pc.CHECKS) / 2,
                  f'{len(picks)} of {len(pc.CHECKS)}'))

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        env = _stale_ref_fixture_env(tmp)
        work, git, branches, tip = _promote_fixture(
            tmp, env, 'staging', ('main', 'staging'))
        # The stub judges the way rename-updates-links does: a file the
        # change deleted, measured from the base it is given.
        (work / 'tools' / 'precedent_check.py').write_text(
            'import os, subprocess, sys\n'
            'if "--base-dependent" in sys.argv:\n'
            '    base = os.environ.get("PRECEDENT_CHANGED_SINCE") or "origin/staging"\n'
            '    d = subprocess.run(["git", "diff", "--name-status", base, "HEAD"],\n'
            '                       capture_output=True, text=True).stdout\n'
            '    if "D\\tgone.py" in d:\n'
            '        print("VIOLATION  rename-updates-links")\n'
            '        print("    doc.md:1: still references \'gone.py\', which this branch deleted")\n'
            '        print("    doc2.md:1: " + "x" * 220 + " SECOND-FINDING-END")\n'
            '        print("  the rule:")\n'
            '        print("    RULE-TEXT-NOT-A-FINDING")\n'
            '        print("precedent_check: 0 passed, 1 violated")\n'
            '        sys.exit(1)\n'
            'print("precedent_check: 3 passed, 0 violated")\n', encoding='utf-8')
        (work / 'gone.py').write_text('x = 1\n', encoding='utf-8')
        (work / 'doc.md').write_text('See gone.py.\n', encoding='utf-8')
        git(work, 'add', '-A')
        git(work, 'commit', '-q', '-m', 'stub, a file and a page naming it')
        git(work, 'push', '-q', 'origin', 'HEAD:main', 'HEAD:staging')
        # Staging deletes the file and leaves the page, already landed.
        git(work, 'rm', '-q', 'gone.py')
        git(work, 'commit', '-q', '-m', 'delete gone.py')
        git(work, 'push', '-q', 'origin', 'HEAD:staging')
        rc, out = branches('--run-tests')
        cases.append(('a Debut of staging that deleted a file main still has '
                      'fails, naming the check and main',
                      rc == 1 and 'rename-updates-links (against main)' in out,
                      failure_detail(out, 300)))
        # 2026-10-31: only the first finding was kept, cut at 200
        # characters, so a Produce showed one of two practices to fix.
        cases.append(('...every finding under it, whole: the second one, past '
                      '200 characters, reaches its end',
                      'SECOND-FINDING-END' in out.split('the full local suite FAILED')[-1],
                      failure_detail(out, 300)))
        cases.append(('...and the rule block under it is not a finding',
                      'rename-updates-links (against main): RULE-TEXT' not in out,
                      failure_detail(out, 300)))
        cases.append(('...and the RUN TESTS RESULT line names it',
                      'RUN TESTS RESULT: staging: FAILED' in out
                      and 'against main' in out.split('RUN TESTS RESULT')[-1],
                      failure_detail(out, 200)))
        # What a Produce does after this failed Debut is tested with the
        # move itself, in the set that ships it (2026-10-19, piece 5c).
        # Main catches up: the same tree now passes.
        git(work, 'push', '-q', 'origin', 'HEAD:main')
        rc, out = branches('--run-tests')
        cases.append(('once main has the deletion too, the Debut passes',
                      rc == 0 and 'against main)' not in out, failure_detail(out, 300)))
        rc, out = branches('--run-tests', 'main')
        cases.append(('a Debut of main itself takes no second pass',
                      rc == 0 and 'judging the change against main' not in out,
                      failure_detail(out, 300)))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_update_repoints_moved_engine_commands():
    """Update Vendors rewrites `process/upstream/tools/X` to `tools/X` in
    AGENTS.md, CLAUDE.md and .claude/settings.json once the mirror is gone
    and tools/X is there (2026-10-01, from a consumer's Update Vendors:
    three AGENTS.md commands and an allowlist entry kept naming the gone
    path). A guarded fallback, a generated block and a file with no copy in
    tools/ are left as they are."""
    import tempfile
    pu, _pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-repoint-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / 'practice_audit.py').write_text('', encoding='utf-8')
        (repo / '.claude').mkdir()
        agents = ('Run `python3 process/upstream/tools/practice_audit.py` weekly.\n'
                  'if [ -f process/upstream/tools/practice_audit.py ]; then :; fi\n'
                  'And `python3 process/upstream/tools/gone_tool.py`.\n'
                  '<!-- BEGIN GENERATED: precedent-loader -->\n'
                  'process/upstream/tools/practice_audit.py\n'
                  '<!-- END GENERATED: precedent-loader -->\n')
        (repo / 'AGENTS.md').write_text(agents, encoding='utf-8')
        (repo / '.claude' / 'settings.json').write_text(
            '{"permissions": {"allow": ["Bash(python3 process/upstream/tools/'
            'practice_audit.py:*)"]}}\n', encoding='utf-8')
        # The consumer's own startup script, as one carried it (2026-10-01):
        # unguarded calls to files the update removed, a guarded fallback,
        # and a vendored hook, which is the engine's to rewrite.
        (repo / 'tools' / 'checkin.py').write_text('', encoding='utf-8')
        (repo / 'tools' / 'bootstrap.sh').write_text(
            'python3 process/upstream/tools/checkin.py update || true\n'
            'python3 process/upstream/tools/practice_audit.py\n'
            '[ -f process/upstream/tools/checkin.py ] && echo old\n'
            'python3 process/upstream/tools/gone_tool.py\n', encoding='utf-8')
        (repo / '.claude' / 'hooks').mkdir()
        (repo / '.claude' / 'hooks' / 'h.sh').write_text(
            'python3 process/upstream/tools/checkin.py\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(repo)], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        done, stranded = pu.repoint_moved_engine_mentions(repo)
        done = dict(done)
        text = (repo / 'AGENTS.md').read_text(encoding='utf-8').split('\n')
        cases.append(('the AGENTS.md command now names tools/',
                      text[0] == 'Run `python3 tools/practice_audit.py` weekly.', text[0]))
        cases.append(('the guarded fallback is left alone',
                      'process/upstream/tools/practice_audit.py' in text[1], text[1]))
        cases.append(('a file with no copy in tools/ is left alone (the check reports it)',
                      'process/upstream/tools/gone_tool.py' in text[2], text[2]))
        cases.append(('a generated block is left to build_views',
                      text[4] == 'process/upstream/tools/practice_audit.py', text[4]))
        cases.append(('the settings.json allowlist entry now names tools/',
                      'python3 tools/practice_audit.py' in
                      (repo / '.claude' / 'settings.json').read_text(encoding='utf-8'), ''))
        boot = (repo / 'tools' / 'bootstrap.sh').read_text(encoding='utf-8').split('\n')
        cases.append(('the startup script\'s unguarded calls now name tools/',
                      boot[0].startswith('python3 tools/checkin.py')
                      and boot[1] == 'python3 tools/practice_audit.py', str(boot)))
        cases.append(('...its guarded fallback is left alone',
                      '[ -f process/upstream/tools/checkin.py ]' in boot[2],
                      boot[2]))
        cases.append(('...a call to a file tools/ lacks is named, not rewritten',
                      ('tools/bootstrap.sh', 4, 'process/upstream/tools/gone_tool.py')
                      in stranded and 'gone_tool' in boot[3], str(stranded)))
        cases.append(('a vendored hook is the engine\'s to rewrite, not this step\'s',
                      'process/upstream' in (repo / '.claude' / 'hooks' / 'h.sh')
                      .read_text(encoding='utf-8'), ''))
        cases.append(('and each file is reported with its count',
                      done == {'AGENTS.md': 1, '.claude/settings.json': 1,
                               'tools/bootstrap.sh': 2}, str(done)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors repoints commands that name a moved engine file '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_retired_words_reads_past_the_decommission_ledger():
    """A repository's own retired terms are never refused in
    process/decommissioned_paths.json, the decommission tool's own ledger,
    which names every retired path by construction -- the same exemption
    the vocabulary config itself has. A live file naming the term still is.

    2026-10-17, very deep check's migration rehearsal: step 5 of
    spec/MIGRATING_EXISTING_INSTALLS.md, followed to the letter, retires the
    old pack through the audit (which writes the ledger) and declares the
    pack's name retired, and then retired-words failed on the ledger.
    Planted: the config, the ledger naming the retired pack, a live file."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_check as pc
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ledger-words-'))
    saved = pc.ROOT
    cases = []
    try:
        (tmp / 'process').mkdir()
        cfg = tmp / pc.RETIRED_VOCAB_CONFIG
        cfg.write_text(json.dumps({'terms': ['oldpackname'], 'exempt_files': []}),
                       encoding='utf-8')
        (tmp / pc.DECOMMISSIONED_PATHS_REGISTRY).write_text(json.dumps({
            'decommissioned': [{'path': 'process/oldpackname',
                                'reason': 'migrated into the sets'}]}), encoding='utf-8')
        (tmp / 'NOTES.md').write_text('We still read oldpackname here.\n',
                                      encoding='utf-8')
        pc.ROOT = tmp
        pc._vendored_engine_files.cache_clear()
        try:
            import our_language as _ol
        except ImportError:
            _ol = None
        where = [f.where for f in pc._repo_retired_terms(cfg, _ol)]
        cases.append(('the ledger is not refused for naming the retired pack',
                      not any(w.startswith(pc.DECOMMISSIONED_PATHS_REGISTRY) for w in where),
                      str(where)))
        cases.append(('...and a live file naming it still is',
                      any(w.startswith('NOTES.md') for w in where), str(where)))
    except OSError as e:
        cases.append((f'fixture could not be built ({e!r})', False, ''))
    finally:
        pc.ROOT = saved
        pc._vendored_engine_files.cache_clear()
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'retired-words reads past the decommission ledger ({len(cases)} stated '
          f'cases)', not bad, '; '.join(f'{n}: {d}' for n, d in bad))


def check_universal_change_names_the_set_copies_that_override_it():
    """A change below the frontmatter of a universal practice names each
    shared set carrying its own ACTIVE copy of the same slug (2026-10-05:
    the ladder set's the-boildown and vendor-update-runbook fell four
    changes behind universal's in three days). A deduplicated copy, a
    frontmatter-only edit, and a repository that is not the universal
    source are each passed over."""
    import shutil, tempfile
    import precedent_check as pc
    import precedent_resolve as _pr
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-override-drift-'))
    cases = []
    fm = ('---\nslug: {s}\nstatus: {st}\n---\n## Rule\n{r}\n')
    try:
        uni, st = tmp / 'u', tmp / 'precedent-shared-x'
        (uni / 'practices').mkdir(parents=True)
        (st / 'practices').mkdir(parents=True)
        (uni / 'precedent-source.json').write_text('{"level": "universal"}')
        (uni / 'practices' / 'rule-a.md').write_text(fm.format(s='rule-a', st='active', r='New.'))
        (uni / 'practices' / 'rule-b.md').write_text(fm.format(s='rule-b', st='active', r='New.'))
        (st / 'practices' / 'rule-a.md').write_text(fm.format(s='rule-a', st='active', r='Copy.'))
        (st / 'practices' / 'rule-b.md').write_text(fm.format(s='rule-b', st='deduplicated', r='Stub.'))
        base = {'practices/rule-a.md': fm.format(s='rule-a', st='active', r='Old.'),
                'practices/rule-b.md': fm.format(s='rule-b', st='active', r='Old.')}

        class Ctx:
            def changed_matching(self, _pat):
                return list(base)
            def read(self, rel):
                return (pc.ROOT / rel).read_text()
            def read_base(self, rel):
                return base.get(rel)
        orig_root, orig_load = pc.ROOT, _pr.load_config
        try:
            pc.ROOT = uni
            _pr.load_config = lambda *_a, **_k: [
                {'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                {'level': 'shared', 'name': 'precedent-shared-x', 'path': str(st),
                 'brought': True}]
            got = pc._universal_change_reaches_overrides(Ctx())
            cases.append(('a Rule change names the set whose active copy overrides it',
                          len(got) == 1 and 'rule-a' in str(got[0].__dict__)
                          and 'precedent-shared-x' in str(got[0].__dict__),
                          [g.__dict__ for g in got]))
            base['practices/rule-a.md'] = fm.format(s='rule-a', st='retired', r='New.')
            got = pc._universal_change_reaches_overrides(Ctx())
            cases.append(('a frontmatter-only edit names nothing, and a deduplicated '
                          'copy is never named', got == [], [g.__dict__ for g in got]))
            base['practices/rule-a.md'] = fm.format(s='rule-a', st='active', r='Old.')
            (uni / 'precedent-source.json').write_text('{"level": "shared"}')
            got = pc._universal_change_reaches_overrides(Ctx())
            cases.append(('outside the universal source it names nothing', got == []))
        finally:
            pc.ROOT, _pr.load_config = orig_root, orig_load
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_citations_in_a_declared_record_are_history():
    """A record of what was -- a dated migration record -- names practices
    as they were, so Update Vendors never lists its citations for a read.

    THE INCIDENT (2026-10-08). A consumer's Update Vendors reported seven
    citations of practices reworded or withdrawn, six of them in its
    process/PRECEDENT_MIGRATION.md, every run; current-rule-governs calls
    that history. Planted: the same practice cited in a plain doc (live), a
    file declaring `kind: record` in frontmatter, a file precedent.json's
    `record_paths` declares, a `## Story` section, and an undeclared file
    named like a migration record (still live: nothing is guessed from a
    name)."""
    import tempfile, json as _json
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_practice_refs as ppr
    import precedent_update as pu
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='refs-record-'))
    try:
        cite = 'Merges follow `upstream-fix` here.\n'
        (tmp / 'docs').mkdir()
        (tmp / 'process').mkdir()
        (tmp / 'docs' / 'live.md').write_text('# Live\n\n' + cite, encoding='utf-8')
        (tmp / 'docs' / 'self.md').write_text(
            '---\nkind: record\nstatus: closed\n---\n# Self\n\n' + cite,
            encoding='utf-8')
        (tmp / 'process' / 'PRECEDENT_MIGRATION.md').write_text(
            '<!-- Last updated: 2026-10-01 -->\n# Migrating\n\n'
            '## What moved where\n\n' + cite, encoding='utf-8')
        (tmp / 'docs' / 'MIGRATION_NOTES.md').write_text(
            '# Migrating\n\n' + cite, encoding='utf-8')
        (tmp / 'docs' / 'story.md').write_text(
            '# A doc\n\n## Story\n\n' + cite + '\n## Next\n\n' + cite,
            encoding='utf-8')
        (tmp / 'precedent.json').write_text(_json.dumps({'record_paths': [
            {'path': 'process/PRECEDENT_MIGRATION.md',
             'reason': 'the dated migration record'}]}), encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        subprocess.run(['git', '-C', str(tmp), 'add', '-A'], capture_output=True, check=True)
        rows = ppr.scan_root(tmp, {'upstream-fix'})
        kinds = {f'{r[0]}:{r[1]}': r[4] for r in rows}
        cases.append(('a plain document\'s citation is live',
                      kinds.get('docs/live.md:3') == 'live', kinds))
        cases.append(('a file declaring kind: record is history',
                      kinds.get('docs/self.md:7') == 'history', kinds))
        cases.append(('a file record_paths declares is history',
                      kinds.get('process/PRECEDENT_MIGRATION.md:6') == 'history', kinds))
        cases.append(('a ## Story section is history, the section after it live',
                      kinds.get('docs/story.md:5') == 'history'
                      and kinds.get('docs/story.md:9') == 'live', kinds))
        cases.append(('an undeclared file named like a record stays live',
                      kinds.get('docs/MIGRATION_NOTES.md:3') == 'live', kinds))
        data = {'slugs': {'upstream-fix': 'Rule reworded'}, 'successors': {},
                'hits': [{'source': 'this repository', 'file': r[0], 'line': r[1],
                          'slug': r[2], 'form': r[3], 'kind': r[4],
                          'must_fix': ppr.must_fix(r)} for r in rows]}
        fix, read = pu.citation_findings(data)
        cases.append(('Update Vendors asks for a read of the live lines only',
                      fix == [] and sorted(read) == ['docs/MIGRATION_NOTES.md:3',
                                                     'docs/live.md:3',
                                                     'docs/story.md:9'],
                      (fix, read)))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'citations in a declared record are history, not listed for a read '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_ladder_test_session_and_the_two_ladder_checks():
    """spec/LADDER_OPT_IN_PLAN.md D7, D13 and the per-person rule.

    - A No ladders session pushes and merges nothing: the push gate and the
      merge check refuse, by name; without the variable neither refuses.
    - set-words-stay-in-their-set finds a made-up set's words planted in
      a practice set that declares that set, passes the owning set itself,
      an individual set whose person brings it, a Story, and a practice
      that requires the owner's capability; and finds a set whose words do
      not match its own examples.
    - ladder-set-is-brought-not-declared finds a precedent.json that
      declares a set providing the ladder, and passes one that declares an
      ordinary set: the ladder is each person's to bring, and a repository
      that declares it puts it on everybody who works there."""
    import shutil, tempfile
    import precedent_check as pc
    import precedent_ladder
    cases = []
    env = {k: v for k, v in os.environ.items()
           if k not in ('PRECEDENT_ASSUME_LADDER',)}
    env['PRECEDENT_NO_LADDERS'] = '1'
    r = subprocess.run([sys.executable, 'tools/precedent_push_check.py', '--gate'],
                       cwd=str(ROOT), env=env, capture_output=True, text=True,
                       timeout=120)
    cases.append(('a No ladders session: the push gate refuses',
                  r.returncode == 1 and 'nothing is pushed' in r.stdout,
                  f'rc={r.returncode} {r.stdout[:200]}'))
    r = subprocess.run([sys.executable, 'tools/precedent_merge_check.py',
                        '--owner', 'o', '--repo', 'r', '--number', '1'],
                       cwd=str(ROOT), env=env, capture_output=True, text=True,
                       timeout=120)
    cases.append(('a No ladders session: the merge check refuses',
                  r.returncode == 1 and 'nothing is pushed' in r.stdout,
                  f'rc={r.returncode} {r.stdout[:200]}'))
    old_env = os.environ.pop('PRECEDENT_NO_LADDERS', None)
    try:
        cases.append(('any other session: no refusal',
                      precedent_ladder.test_session_refusal() is None, ''))
    finally:
        if old_env is not None:
            os.environ['PRECEDENT_NO_LADDERS'] = old_env

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ladder-checks-'))
    saved_root = pc.ROOT
    saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
    try:
        # set-words-stay-in-their-set, with made-up words: zz-owner owns
        # "Zorpify" and "phase N of 9". Each set below is judged against the
        # sets in force for it -- its precedent.json and its person's config.
        plain, ladder = tmp / 'plain-set', tmp / 'ladder-set'
        owner = tmp / 'zz-owner'
        ind_own, ind_plain, ind_gone = (tmp / 'ind-brings-owner',
                                        tmp / 'ind-brings-plain',
                                        tmp / 'ind-brings-uncloned')
        words = {'patterns': [
            {'kind': 'a zz command', 'regex': r'(?:\*\*|")Zorpify(?:\*\*|")',
             'matches': ['"Zorpify"'], 'never_matches': ['zorpify']},
            {'kind': 'a zz step', 'regex': r'\bphase [1-9] of 9\b'}]}
        declares_owner = {'sources': [{'name': 'zz-owner', 'level': 'shared',
                                       'path': str(owner)}]}
        _genv = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@x',
                     GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@x',
                     GIT_CONFIG_GLOBAL=empty_gitconfig(), PRECEDENT_ALLOW_ANY_AUTHOR='1')
        for d, man, cfg in (
                (plain, {'level': 'shared', 'provides': []}, declares_owner),
                (ladder, {'level': 'shared', 'provides': ['ladder']}, None),
                (owner, {'level': 'shared', 'provides': ['zz-cap'],
                         'owned_words': words}, None),
                (ind_own, {'level': 'individual', 'brings': [
                    {'name': 'zz-owner', 'repo_url': 'https://example.com/z.git'}]}, None),
                (ind_plain, {'level': 'individual', 'brings': [
                    {'name': 'plain-set', 'repo_url': 'https://example.com/p.git'}]},
                 declares_owner),
                (ind_gone, {'level': 'individual', 'brings': [
                    {'name': 'not-cloned-set', 'repo_url': 'https://example.com/n.git'}]},
                 declares_owner)):
            (d / 'practices').mkdir(parents=True)
            (d / 'precedent-source.json').write_text(json.dumps(
                dict(name=d.name, **man)))
            if cfg:
                (d / 'precedent.json').write_text(json.dumps(cfg))
            (d / 'practices' / 'x.md').write_text(
                '---\nslug: x\nstatus: active\n---\n\n## Rule\n\n'
                'Say "Zorpify" at phase 3 of 9.\n\n## Story\n\n'
                'On the day, we said "Zorpify" at phase 2 of 9.\n')
            subprocess.run(['git', 'init', '-q', str(d)], env=_genv, check=True)
        # A practice that requires the owner's capability is its own.
        (plain / 'practices' / 'y.md').write_text(
            '---\nslug: y\nstatus: active\nrequires: ["zz-cap"]\n---\n\n'
            '## Rule\n\nSay "Zorpify".\n')
        no_cfg = tmp / 'no-config.json'

        def judge(root, individual=None):
            cfg = tmp / f'cfg-{root.name}.json'
            if individual:
                cfg.write_text(json.dumps({'individual': {'path': str(individual)}}))
            os.environ['PRECEDENT_USER_CONFIG'] = str(cfg if individual else no_cfg)
            pc.ROOT = root
            try:
                got = pc._set_words_stay_in_their_set(None)
                return len(got), got, ''
            except pc.NotApplicable as e:
                return None, [], str(e)

        for root, ind, want, because, what in (
                (plain, None, 2, '', 'a set that declares the owner'),
                (owner, None, None, 'declares words of its own', 'the owning set itself'),
                (ind_own, ind_own, None, 'brought by this set', 'an individual set that brings it'),
                (ind_plain, ind_plain, 2, '', 'an individual set that brings only an ordinary set'),
                (ind_gone, ind_gone, 2, '', 'an individual set whose other brought set is not cloned')):
            n, got, why = judge(root, ind)
            # A skip says why, so a skip for another reason fails here.
            cases.append((f'set words in {what}: '
                          f'{"skipped" if want is None else f"{want} finding(s), none in the Story or a practice that requires the capability"}',
                          (n is None and because in why) if want is None else
                          (n == want and all('x.md:8:' in str(f) for f in got)),
                          f'got {n} {why!r}: {[str(f) for f in got][:4]}'))
        # A set whose declared words do not match their own examples.
        (owner / 'precedent-source.json').write_text(json.dumps(dict(
            name='zz-owner', level='shared', owned_words={'patterns': [
                {'kind': 'a zz command', 'regex': r'\bZorpify\b',
                 'matches': ['Zorpify'], 'never_matches': ['Zorpify!']}]})))
        n, got, why = judge(owner)
        cases.append(('a set whose words match what it says they never should: '
                      'one finding, on its own precedent-source.json',
                      n == 1 and 'precedent-source.json' in str(got[0]),
                      f'got {n} {why!r}: {[str(f) for f in got]}'))
        (owner / 'precedent-source.json').write_text(json.dumps(dict(
            name='zz-owner', level='shared', provides=['zz-cap'], owned_words=words)))
        # The same individual set checked from a linked worktree elsewhere
        # (2026-10-04): a Debut or Produce checks the set in a throwaway
        # worktree under the temp directory, where nothing sits beside it.
        # The set it brings is found beside the main checkout, so the check
        # still stands aside -- before, the set's own Debut was refused.
        subprocess.run(['git', '-C', str(ind_own), 'add', '-A'], env=_genv, check=True)
        subprocess.run(['git', '-C', str(ind_own), 'commit', '-qm', 'x', '--no-verify'],
                       env=_genv, check=True)
        _elsewhere = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ladder-wt-'))
        _wt = _elsewhere / 'wt'
        subprocess.run(['git', '-C', str(ind_own), 'worktree', 'add', '-q', '--detach',
                        str(_wt)], env=_genv, check=True)
        try:
            n, got, why = judge(_wt, ind_own)
            cases.append(('set words in an individual set that brings the owner, '
                          'checked from a linked worktree elsewhere: skipped',
                          n is None and 'brought by this set' in why,
                          f'got {n} {why!r}'))
        finally:
            shutil.rmtree(_elsewhere, ignore_errors=True)
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
        repo = tmp / 'repo'
        repo.mkdir()
        for declared, want, what in (('ladder-set', 1, 'declares the ladder set'),
                                     ('plain-set', 0, 'declares an ordinary set')):
            (repo / 'precedent.json').write_text(json.dumps({'sources': [
                {'name': declared, 'level': 'shared', 'path': f'../{declared}'}]}))
            pc.ROOT = repo
            got = pc._ladder_set_is_brought_not_declared(None)
            cases.append((f'a precedent.json that {what}: {want} finding(s)',
                          len(got) == want, str([str(f) for f in got])[:300]))
        # D18 narrowed (2026-10-19): one code owner's quoted, dated yes in
        # binds_everyone lets a repository declare the ladder.
        ok_by = 'Fx Owner, 2026-10-19: "bind everyone here"'
        for be, owners_file, want, what in (
                ({'sets': ['ladder-set'], 'approved_by': ok_by}, None, 0,
                 'a code owner, by name, binds everyone'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'fxowner, 2026-10-19: "yes"'}, None, 0,
                 'a code owner, by login, binds everyone'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'Fx, 2026-10-19: "yes"'}, None, 0,
                 'a code owner, by the first name they sign with, binds everyone'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'Someone Else, 2026-10-19: "yes"'}, None, 1,
                 'NEGATIVE CONTROL: a quote from someone who is not a code owner'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'Fx Owner: "bind everyone"'}, None, 1,
                 'NEGATIVE CONTROL: an undated quote'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'Fx Owner, 2026-10-19, said yes'}, None, 1,
                 'NEGATIVE CONTROL: a paraphrase, quoting nobody'),
                ({'sets': ['other-set'], 'approved_by': ok_by}, None, 1,
                 'NEGATIVE CONTROL: an entry that names a different set'),
                ({'sets': ['ladder-set'], 'approved_by': ok_by},
                 '* @someone-else\n', 1,
                 'NEGATIVE CONTROL: a CODEOWNERS file that does not name them'),
                ({'sets': ['ladder-set'],
                  'approved_by': 'someone-else, 2026-10-19: "yes"'},
                 '* @someone-else\n', 0,
                 'the code owner CODEOWNERS names binds everyone')):
            (repo / 'precedent.json').write_text(json.dumps({
                'maintainers': [{'github': 'fxowner', 'name': 'Fx Owner'}],
                'binds_everyone': be,
                'sources': [{'name': 'ladder-set', 'level': 'shared',
                             'path': '../ladder-set'}]}))
            co = repo / 'CODEOWNERS'
            if owners_file:
                co.write_text(owners_file)
            elif co.exists():
                co.unlink()
            pc.ROOT = repo
            got = pc._ladder_set_is_brought_not_declared(None)
            cases.append((f'binds_everyone, {what}: {want} finding(s)',
                          len(got) == want, str([str(f) for f in got])[:300]))
        # 2026-10-28: a consumer keeps its own identity.json (an email, for
        # commit authorship). It was read as an individual set's owner, so
        # its GitHub owner was never asked and no approval could match.
        if (repo / 'CODEOWNERS').exists():
            (repo / 'CODEOWNERS').unlink()
        subprocess.run(['git', 'init', '-q', str(repo)], env=_genv,
                       capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin',
                        'https://github.com/fxowner/repo'], env=_genv,
                       capture_output=True)
        (repo / 'identity.json').write_text(json.dumps(
            {'name': 'Fx Owner', 'email': 'fx@example.invalid'}))
        for be_by, ind, want, what in (
                ('fxowner, 2026-10-19: "yes"', False, 0,
                 "a consumer's own identity.json does not hide its GitHub owner"),
                ('Fx Owner, 2026-10-19: "yes"', False, 1,
                 'a name no maintainers entry maps is still not a login')):
            (repo / 'precedent.json').write_text(json.dumps({
                'binds_everyone': {'sets': ['ladder-set'], 'approved_by': be_by},
                'sources': [{'name': 'ladder-set', 'level': 'shared',
                             'path': '../ladder-set'}]}))
            pc.ROOT = repo
            got = pc._ladder_set_is_brought_not_declared(None)
            cases.append((f'binds_everyone, {what}: {want} finding(s)',
                          len(got) == want and (want == 0 or
                                                '"maintainers"' in str(got[0])),
                          str([str(f) for f in got])[:300]))
        import precedent_audience as _pa
        (repo / 'precedent-source.json').write_text(json.dumps(
            {'name': 'precedent-individual', 'level': 'individual'}))
        cases.append(('an individual set is still owned by its identity.json',
                      'fx@example.invalid' in (_pa.owners(repo)[0] or ()),
                      str(_pa.owners(repo))))
        (repo / 'precedent-source.json').unlink()
        (repo / 'identity.json').unlink()
    finally:
        pc.ROOT = saved_root
        shutil.rmtree(tmp, ignore_errors=True)
    # A path rule in a set the person brings fires for them through
    # precedent_paths.py, and for nobody else (2026-10-02: the paths channel
    # read the repository's practices/ alone, so checks-follow-the-tier
    # stopped reaching the person who brings it when it moved).
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-brought-paths-'))
    try:
        repo, ind, lad = tmp / 'repo', tmp / 'precedent-individual', tmp / 'fx-ladder'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private', 'sources': []}))
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'precedent-individual', 'level': 'individual',
             'brings': [{'name': 'fx-ladder',
                         'repo_url': 'https://example.com/fx-ladder.git'}]}))
        (lad / 'practices').mkdir(parents=True)
        (lad / 'precedent-source.json').write_text(json.dumps(
            {'name': 'fx-ladder', 'level': 'shared', 'provides': ['ladder']}))
        (lad / 'practices' / 'fx-path-rule.md').write_text(
            '---\nslug:        fx-path-rule\ntitle:       "fx"\n'
            'tier:        on-demand\nseverity:    default\n'
            'applies_to:  ["tools/*.py"]\napplies_to_why: "fx"\n'
            'occasion:    null\nindex_clause: "fx clause"\nstatus:      active\n'
            '---\n\n## Rule\n\nThe brought path rule.\n')
        cfg = tmp / 'config.json'
        cfg.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'precedent-individual', 'path': str(ind)}}))
        for what, extra, want in (('the person who brings it', {}, True),
                                  ('a person with no such set',
                                   {'PRECEDENT_USER_CONFIG': str(tmp / 'none.json')}, False),
                                  ('the same person, No ladders',
                                   {'PRECEDENT_NO_LADDERS': '1'}, False)):
            e = {k: v for k, v in os.environ.items()
                 if k not in ('PRECEDENT_ASSUME_LADDER', 'PRECEDENT_NO_LADDERS')}
            e['PRECEDENT_USER_CONFIG'] = str(cfg)
            e.update(extra)
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_paths.py'),
                                '--repo', str(repo), 'tools/x.py'],
                               env=e, capture_output=True, text=True, timeout=120)
            got = 'The brought path rule.' in r.stdout
            cases.append((f'a brought path rule {"fires" if want else "is silent"} '
                          f'for {what}', got == want, failure_detail(r.stdout + r.stderr, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # The push check recognises the size-cap warning precedent_check.py
    # prints today (2026-10-02: that wording was made plain and the push
    # check went on looking for the old one, so its closing reminder never
    # fired).
    import precedent_push_check as ppc
    src = (ROOT / 'tools' / 'precedent_check.py').read_text(encoding='utf-8')
    m = re.search(r"WARNING    \{slug\} — (over a size cap\.[^']*)'", src)
    cases.append(("the push check matches precedent_check's size-cap warning "
                  "as it is printed today",
                  bool(m) and any(w in m.group(1) for w in ppc.SIZE_CAP_WARNINGS),
                  m.group(1) if m else 'warning text not found'))

    # A config named outside $HOME is somebody other than the person whose
    # home the bootstrap hook works in, so the self-heal does not run it
    # (2026-10-02: fixtures naming their own config kept putting this
    # machine's individual clone back on its pinned branch). Inside $HOME it
    # still runs.
    import precedent_resolve as _pr_heal
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-heal-named-'))
    saved = {k: os.environ.get(k) for k in ('CLAUDE_CODE_REMOTE',
                                            'PRECEDENT_USER_CONFIG', 'HOME')}
    try:
        repo, home = tmp / 'repo', tmp / 'home'
        hook = repo / _pr_heal.INDIVIDUAL_BOOTSTRAP_HOOK
        hook.parent.mkdir(parents=True)
        home.mkdir()
        marker = tmp / 'hook-ran'
        hook.write_text(f'#!/bin/bash\ntouch {marker}\n', encoding='utf-8')
        os.environ['CLAUDE_CODE_REMOTE'] = 'true'
        os.environ['HOME'] = str(home)
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'elsewhere' / 'config.json')
        r1 = _pr_heal._self_heal_individual_source(repo)
        ran1 = marker.exists()
        os.environ['PRECEDENT_USER_CONFIG'] = str(home / 'config.json')
        r2 = _pr_heal._self_heal_individual_source(repo)
        ran2 = marker.exists()
        cases.append(('a config named outside $HOME does not run the bootstrap '
                      'hook; one inside $HOME still does',
                      r1 == 'not-remote' and not ran1 and r2 == 'attempted' and ran2,
                      f'{r1} {ran1} {r2} {ran2}'))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    # A rule from a brought set counts as reached through the session file
    # wherever that channel is wired, in a private repository too; with the
    # channel not wired it is reported (2026-10-02: only public repositories
    # counted the channel, so a private one called every brought rule
    # reachable by nothing).
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-brought-reach-'))
    saved_root, saved_cfg = pc.ROOT, os.environ.get('PRECEDENT_USER_CONFIG')
    try:
        repo, ind, lad = tmp / 'repo', tmp / 'precedent-individual', tmp / 'fx-ladder'
        for d in (repo / 'practices', repo / 'tools', repo / '.claude' / 'hooks',
                  ind / 'practices', lad / 'practices'):
            d.mkdir(parents=True)
        (repo / 'AGENTS.md').write_text('# nothing names it\n')
        (repo / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private', 'sources': []}))
        shutil.copy(ROOT / 'tools' / 'precedent_session_practices.py', repo / 'tools')
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'precedent-individual', 'level': 'individual',
             'brings': [{'name': 'fx-ladder',
                         'repo_url': 'https://example.com/fx-ladder.git'}]}))
        (lad / 'precedent-source.json').write_text(json.dumps(
            {'name': 'fx-ladder', 'level': 'shared', 'provides': ['ladder']}))
        (lad / 'practices' / 'fx-unrouted.md').write_text(
            '---\nslug:        fx-unrouted\ntitle:       "fx"\n'
            'tier:        on-demand\nseverity:    default\napplies_to:  ["**"]\n'
            'occasion:    null\ngates:       []\nchecked_by:  null\n'
            'status:      active\n---\n\n## Rule\n\nUnrouted.\n')
        cfg = tmp / 'config.json'
        cfg.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'precedent-individual', 'path': str(ind)}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
        pc.ROOT = repo
        hook = repo / '.claude' / 'hooks' / 'session-start.sh'
        for wired, want in ((True, False), (False, True)):
            hook.write_text('#!/bin/bash\n' + ('python3 tools/precedent_session_practices.py\n'
                                                if wired else '# no loader here\n'))
            got = any('fx-unrouted' in str(f) for f in (pc._practice_is_reachable(None) or []))
            cases.append((f'in a private repository with the session channel '
                          f'{"wired" if wired else "not wired"}, a brought rule is '
                          f'{"reported unreachable" if want else "reached"}',
                          got == want, f'reported={got}'))
    finally:
        pc.ROOT = saved_root
        if saved_cfg is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
        shutil.rmtree(tmp, ignore_errors=True)

    # A Promote in a repository with only main does nothing and creates no
    # branch (2026-10-02: it announced a move, failed, and left its lock
    # branch on origin).
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-main-only-'))
    try:
        genv = {k: v for k, v in os.environ.items() if k != 'PRECEDENT_NO_LADDERS'}
        genv.update({'GIT_AUTHOR_NAME': 'x', 'GIT_AUTHOR_EMAIL': 'x@x',
                     'GIT_COMMITTER_NAME': 'x', 'GIT_COMMITTER_EMAIL': 'x@x',
                     'PRECEDENT_ASSUME_LADDER': '1'})
        g = lambda *a, cwd=tmp: subprocess.run(['git', *a], cwd=str(cwd), env=genv,
                                              capture_output=True, text=True)
        g('init', '-q', '--bare', '-b', 'main', 'origin.git')
        g('clone', '-q', str(tmp / 'origin.git'), 'work')
        work = tmp / 'work'
        (work / 'precedent.json').write_text('{"format_version": 1}\n')
        g('add', '-A', cwd=work)
        g('commit', '-qm', 'init', cwd=work)
        g('push', '-q', 'origin', 'HEAD:main', cwd=work)
        # A Promote here says there is nothing to promote: tested with the
        # move itself, in the set that ships it (2026-10-19, piece 5c).
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the No ladders session refuses to push, and the two ladder checks '
          f'find what they name ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_pretooluse_hook_fires():
    """The path-triggered channel's consumer-repo integration
    (spec/LOADER.md's status table, "not yet wired into a PreToolUse hook...
    that is consumer-repo integration, phase 6 territory") -- the wrapper
    itself (templates/harness/claude-code/hooks/precedent-paths.sh) had no
    harness coverage before this check: a shell script under templates/
    isn't scanned by anything else here (checkable-gets-checked). practice:
    engine-plus-host-shims -- this is the thin host shim's own test, not a
    re-test of tools/precedent_paths.py's matching logic, which
    check_glob_semantics and the rest of this file already cover; every
    case below asserts the wrapper's stdin-parsing, field-name fallback,
    and PreToolUse JSON reshaping, against real practice files rather than
    a fixture catalogue, since the two slugs used
    (code-cites-practice, applies_to tools/**; checkable-gets-checked,
    applies_to practices/** + PRACTICES.md) are stable, narrowly-scoped and
    unlikely to be retired."""
    hook = ROOT / 'tools' / 'precedent-paths.sh'
    if not hook.exists():
        check('PreToolUse hook fires (5 stated cases: Edit file_path, a '
              'no-match path, NotebookEdit notebook_path fallback, '
              'malformed stdin, always exits 0)', False,
              f'{hook} does not exist')
        return

    def run_hook(stdin_text):
        r = subprocess.run(['bash', str(hook)], input=stdin_text,
                           capture_output=True, text=True,
                           env={**os.environ, 'CLAUDE_PROJECT_DIR': str(ROOT)})
        return r.returncode, r.stdout.strip()

    def parsed_context(stdout):
        try:
            obj = json.loads(stdout)
        except json.JSONDecodeError:
            return None
        return obj.get('hookSpecificOutput', {})

    cases = []

    rc, out = run_hook(json.dumps({'tool_name': 'Edit',
                                    'tool_input': {'file_path': 'tools/some_new_thing.py'}}))
    hso = parsed_context(out) or {}
    cases.append(('an Edit on a tools/** path surfaces code-cites-practice\'s '
                  'Rule as additionalContext, never denying the edit',
                  rc == 0 and hso.get('hookEventName') == 'PreToolUse'
                  and 'code-cites-practice' in hso.get('additionalContext', '')))
    # The hook carries CONTEXT and no permission verdict. It used to emit
    # `permissionDecision: "allow"`, which on the reading where that field
    # settles the decision meant every install of this adapter silently
    # auto-approved every Edit/Write/NotebookEdit whose path matched any
    # practice -- which is most of them. Asserted so the field cannot come
    # back as a copy-paste from another hook's example.
    cases.append(('and carries no permissionDecision: a practice loader '
                  'does not decide whether an edit is allowed',
                  'permissionDecision' not in hso))

    rc, out = run_hook(json.dumps({'tool_name': 'Write',
                                    'tool_input': {'file_path': 'random/unrelated/thing.xyz'}}))
    cases.append(('a Write on a path no on-demand practice scopes to prints nothing',
                  rc == 0 and out == ''))

    rc, out = run_hook(json.dumps({'tool_name': 'NotebookEdit',
                                    'tool_input': {'notebook_path': 'PRACTICES.md'}}))
    hso = parsed_context(out) or {}
    cases.append(("a NotebookEdit keyed under notebook_path (not file_path) still "
                  "resolves -- the field-name fallback the public hooks reference "
                  "leaves ambiguous for this tool -- and surfaces "
                  "checkable-gets-checked's Rule",
                  rc == 0 and 'checkable-gets-checked' in hso.get('additionalContext', '')))

    rc, out = run_hook('not json at all')
    cases.append(('malformed stdin does not crash the hook or its shell', rc == 0 and out == ''))

    rc, out = run_hook(json.dumps({'tool_name': 'Bash'}))
    # --- the per-session seen file: the same Rules must not be re-injected
    # on every edit. Measured before this existed: ten practices and ~1,000
    # words of Rule text on EVERY markdown edit, identical every time.
    import tempfile as _tf
    _seen = pathlib.Path(_tf.mkdtemp(prefix='precedent-seen-')) / 'seen.txt'
    _paths = str(ROOT / 'tools' / 'precedent_paths.py')

    def _paths_run(*extra):
        r = subprocess.run([sys.executable, _paths, *extra, 'README.md'],
                           capture_output=True, text=True, cwd=str(ROOT))
        return r.returncode, r.stdout

    rc_a, out_a = _paths_run('--seen-file', str(_seen))
    rc_b, out_b = _paths_run('--seen-file', str(_seen))
    cases.append(('the first match with a --seen-file prints full Rules',
                  rc_a == 0 and len(out_a.split()) > 200))
    cases.append(('the second prints a short reminder instead, naming every '
                  'practice and how to get its full Rule back',
                  rc_b == 0 and len(out_b.split()) < len(out_a.split()) / 3
                  and 'Already loaded this session' in out_b
                  and 'precedent_show.py' in out_b))
    seen_slugs = {l.strip() for l in _seen.read_text().splitlines() if l.strip()}
    cases.append(('every practice shown in full is recorded, so the reminder '
                  'covers exactly what was already sent',
                  seen_slugs and all(f'### {s}' in out_a for s in seen_slugs)))
    r_c = subprocess.run([sys.executable, _paths, '--seen-file', str(_seen),
                          'tools/x.py'], capture_output=True, text=True, cwd=str(ROOT))
    cases.append(("a practice that has NOT been shown yet still arrives in "
                  "full, so the optimization cannot swallow a new match",
                  r_c.returncode == 0 and '### code-cites-practice' in r_c.stdout))
    rc_d, out_d = _paths_run('--seen-file', str(_seen.parent / 'nope' / 'x.txt'))
    cases.append(('an unreadable or missing seen file means "nothing seen '
                  'yet", never an error -- this is a context optimization, '
                  'not a correctness mechanism',
                  rc_d == 0 and len(out_d.split()) > 200))
    import shutil as _sh
    _sh.rmtree(_seen.parent, ignore_errors=True)

    cases.append(('a tool call with no tool_input at all (matcher scopes this out '
                  'in settings.json, but the wrapper itself must not assume that) '
                  'prints nothing', rc == 0 and out == ''))

    bad = [(n, '') for n, ok in cases if not ok]
    check(f'PreToolUse hook fires ({len(cases)} stated cases: Edit file_path, '
          f'a no-match path, NotebookEdit notebook_path fallback, malformed '
          f'stdin, a tool call with no tool_input, no permission verdict, and a '
          f'per-session seen file that stops the same Rules being re-injected '
          f'on every edit without swallowing a new match)',
          not bad, '; '.join(n for n, _ in bad))


def check_title_case_knows_the_files_it_ships():
    """Every root file this project INSTANTIATES into an adopter must be
    classified correctly by title_case, including the ones upstream never
    has itself.

    THE INCIDENT, 2026-09-08, from a consumer repo taking the beta update:
    headline-capitalization fired on that repo's VOICE.md. `INTERNAL_FILES`
    had been built from UPSTREAM's own root names, and upstream shipped
    VOICE.md and STYLEGUIDE.md as templates it never instantiated -- so the
    default was blind to exactly the files this project hands out, and every
    adopter got the same false positive on a file whose own header says it
    is LOCAL ONLY.

    IT FAILS IN THE DIRECTION NOBODY CHECKS, which is what makes it worth a
    standing control rather than a one-line fix: upstream's own gate stays
    green because upstream does not have the file. So this check does not
    ask "is this one file classified right" -- it derives the list of
    shipped root files from templates/ and asks it of ALL of them, so a
    template added later is covered without anybody remembering to come
    back.

    VOICE.md stopped being a root file on 2026-09-17, and STYLEGUIDE.md
    followed on 2026-09-22 -- both are now repo-local practices,
    local/practices/project-voice.md and
    local/practices/project-visual-identity.md, instantiated from
    templates/local-practices/*.md.template -- nested one level deeper, so
    the root-level `templates/*.md.template` glob below correctly no longer
    yields either of them. Both are kept out of `shipped` and the by-name
    assertions for that reason, not an oversight: this check is about root
    files, and neither one still is.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'tc_ship', ROOT / 'tools' / 'title_case.py')
    tc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(tc)
    finally:
        sys.path.pop(0)

    cases = []

    # Every templates/<NAME>.md.template instantiates to <NAME>.md at an
    # adopter's root -- INSTALL.md section 1 spells the mapping out. Derived, not
    # listed, so this cannot go stale the way the list it guards did.
    shipped = sorted(
        f.name[:-len('.template')]
        for f in (ROOT / 'templates').glob('*.md.template'))
    cases.append(('templates/ yields root files to classify at all',
                  len(shipped) >= 3, str(shipped)))

    # Neither VOICE.md nor STYLEGUIDE.md is shipped by a template any more,
    # asserted BY NAME as well as by the derivation above: a derivation that
    # silently produced an empty list would otherwise pass this whole check
    # without proving either file is actually gone from `shipped`.
    for name in ('VOICE.md', 'STYLEGUIDE.md'):
        cases.append((f'{name} is no longer shipped by a root template',
                      name not in shipped, str(shipped)))

    # Both replacements are internal for the same reason -- not
    # INTERNAL_FILES (neither carries a root-file entry any more) but
    # INTERNAL_DIRS, because local/practices/ is a repo-local practice
    # source, and 'local' has been an INTERNAL_DIRS entry since before this
    # file existed.
    for rel in ('local/practices/project-voice.md',
                'local/practices/project-visual-identity.md'):
        cases.append((f'{rel} is INTERNAL via '
                      "INTERNAL_DIRS's 'local' entry, with no INTERNAL_FILES "
                      'entry needed for it',
                      tc.is_outward(rel) is False,
                      ''))

    # spec/ and record/ are twins by design -- spec/ holds current normative
    # reference, record/ the working record -- and record/ was missing from
    # INTERNAL_DIRS until 2026-09-08 purely because the directory did not
    # exist when the list was written. Same shape as the VOICE.md miss above:
    # a default derived from what the repo HAPPENED to contain. Asserted as a
    # pair so neither can drift from the other again.
    for pair in ('spec', 'record'):
        cases.append((f'{pair}/ is an INTERNAL_DIRS entry -- it and its twin '
                      f'are both working trees, never published prose',
                      pair in tc.INTERNAL_DIRS, str(tc.INTERNAL_DIRS)))
    cases.append(('and a document inside record/ is classified internal',
                  tc.is_outward('record/GOTCHAS_ARCHIVE.md') is False, ''))

    # The other half, or "classify everything internal" would pass: files
    # that genuinely ARE published must still be in scope.
    for name in ('README.md', 'SETUP.md', 'documentation/ADOPTING.md'):
        cases.append((f'{name} is still OUTWARD, so the fix did not just '
                      f'silence the check', tc.is_outward(name) is True, ''))

    # And the classification an adopter gets must not depend on a
    # precedent.json they have not written: is_outward() reads one when it
    # is there, and the default is what every fresh install starts from.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        cases.append(('local/practices/project-visual-identity.md is '
                      'internal with NO precedent.json at all -- the state '
                      'a fresh adopter is in before they configure '
                      'anything',
                      tc.is_outward('local/practices/project-visual-identity.md',
                                    root=tmp) is False, ''))

    ok = all(c[1] for c in cases)
    check(f'title_case classifies the root files this project ships into '
          f'adopters ({len(cases)} stated cases, derived from templates/ '
          f'rather than listed)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:800])


def check_todo_gotcha_stale_reference_fires():
    """precedent_check.py's `todo-gotcha-stale-reference` (Part 4.1 step 7,
    extended by step 10) against a real fixture repo, `pc.ROOT` pointed at
    it (practice: control-asserts-which-failure -- asserts the specific
    finding text, not just that the check went non-green; and each planted
    case has its own clean-tree negative control alongside it, per
    fixture-owns-its-state)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_check as pc

    def make_repo(files):
        d = pathlib.Path(tempfile.mkdtemp(prefix='precedent-stale-ref-'))
        for rel, content in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=d, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=d, check=True)
        return d

    def run(files):
        d = make_repo(files)
        saved = pc.ROOT
        pc.ROOT = d
        try:
            findings = pc._todo_gotcha_stale_reference(pc.Ctx(whole_tree=True))
            return [str(f) for f in findings]
        finally:
            pc.ROOT = saved
            shutil.rmtree(d, ignore_errors=True)

    cases = []

    out = run({'spec/PLAN.md': 'see [x](../TODO.md#old-slug) for detail\n'})
    cases.append(('a TODO.md#slug link is reported',
                  any('old-slug' in o for o in out), repr(out)))

    out = run({'documentation/X.md': (
        'due: [table](https://github.com/o/r/blob/main/todo/TODO.md#due-reminders)'
        ' or [here](../todo/TODO.md#due-reminders)\n')})
    cases.append(('...but a link into the live index todo/TODO.md, by '
                  'anchor, raises nothing', out == [], repr(out)))

    out = run({'todo/todo-2026-01-01-old-slug.md':
              '---\nslug: todo-2026-01-01-old-slug\n---\n## What\nfine\n'})
    cases.append(('...and a real migrated item file alone raises nothing',
                  out == [], repr(out)))

    out = run({'spec/X.md': 'the story is [here](#g5)\n'})
    cases.append(('a bare #gN anchor with no file is reported',
                  any('#g5' in o for o in out), repr(out)))

    out = run({'record/GOTCHAS.md': '## 5. <a id="g5"></a>Trap\n\nSee [also](#g5).\n'})
    cases.append(("...and the SAME bare anchor inside record/GOTCHAS.md itself "
                  "is not -- it is a real same-document jump there",
                  out == [], repr(out)))

    out = run({'AGENTS.md': 'closed via TODO.md item 42 last week\n'})
    cases.append(('an "item N" phrase is reported',
                  any('item 42' in o for o in out), repr(out)))

    out = run({'TODO.md': '# TODO has moved\n\nSee todo/ instead.\n'})
    cases.append(("the real stub -- prose, no bullets -- raises nothing",
                  out == [], repr(out)))

    out = run({'TODO.md': ('# TODO has moved\n\n'
                           '- <a id="new-item"></a>**Sneaking one in.**\n')})
    cases.append(('a new old-format bullet added back to TODO.md itself is '
                  'reported (Part 4.4 step 1: TODO.md takes no new items '
                  'after the cutover)',
                  any('new item bullet' in o for o in out), repr(out)))

    out = run({'AGENTS.md': 'nothing here resembles any of the three shapes\n'})
    cases.append(('unrelated prose raises nothing', out == [], repr(out)))

    out = run({'TODO.md': ('# Repo TODO — open analyses, verifications, and decisions\n\n'
                           '## Recurring\n\n'
                           '- [ ] **Precedent check-in:** review vendored changes.\n')})
    cases.append(("a downstream project's own (never-migrated) TODO.md, still "
                  "carrying the classic template's own bullets, raises nothing "
                  "-- this repo's cutover does not bind a project that never "
                  "adopted the stub (caught by "
                  "check_installer_produces_a_clean_install: a fresh install "
                  "from templates/TODO.md.template was failing this check)",
                  out == [], repr(out)))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'todo-gotcha-stale-reference catches its three named shapes and '
          f'the two same-document exemptions do not false-positive '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


