# The harness tests for practice sources
#
# tools/harness/vh_sources.py -- part of the verification harness:
# practice sources: resolving, loading and showing them.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_section_source_order(files, original_practices_by_number):
    """Text may be re-homed between sections; it may not be scrambled.
    Within each section, sentences must appear in the same relative order
    they had in PRACTICES.md. This is what byte-identical regeneration used
    to guarantee, kept alive after that check could no longer run."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        if _amended_and_logged(fm.get('slug', stem)):
            continue  # deliberately rewritten post-conversion; see CHANGES_TO_TELL_ALEX.md
        orig = original_practices_by_number.get(fm.get('source_practice_number'))
        if orig is None:
            continue
        src = _source_sentences(orig)
        # position lists, so a sentence repeated in the source is matched
        # greedily in order rather than ambiguously
        positions = collections.defaultdict(collections.deque)
        for i, s in enumerate(src):
            positions[s].append(i)
        for name, out in _output_sentences_by_section(sections):
            last, last_text = -1, None
            for s in out:
                if not positions[s]:
                    continue  # already reported by the sentence check
                i = positions[s].popleft()
                if i < last:
                    ok = False
                    print(f"  {f.name} [{name}]: out of source order -- "
                          f"{s[:70]!r} precedes {last_text[:70]!r} here but follows "
                          f"it in PRACTICES.md")
                last, last_text = i, s
    check('section content keeps its source order (text may be re-homed, not scrambled)', ok)
def check_source_precedence():
    """Four sources resolved by a consumer repo, and the precedence rules
    asserted as stated cases (PRACTICE_ENGINE_PLAN.md, phase-3 done-when: "a
    consumer repo resolves all three and precedence is tested" -- extended
    2026-09-03 to a fourth source, repo-local, and to the reordered
    precedence team > repo-local > individual > universal; see
    spec/SOURCES.md for why the order changed).

    WHY THE FIXTURE IS BUILT IN A TEMPORARY DIRECTORY AND NOT COMMITTED.
    Levels are repositories, not directories. A committed fixture holding a
    team- or individual-shaped tree inside Precedent is exactly the shortcut
    the plan forbids and the leak gate refuses by path -- and a check whose
    setup requires switching off another check is a check that ends up
    switching it off. The fixture practices below are invented, and exist
    only for the length of this function.

    EACH CASE IS A RULE FROM THE PLAN, NOT A RESTATEMENT OF THE RESOLVER.
    They are written from "Precedence, and the One Case Where the Individual
    Does Not Win" and from "One Individual Set per Person": what SHOULD
    happen, so the check disagrees with the resolver when the resolver is
    wrong rather than agreeing with it by construction."""
    import shutil, tempfile

    def practice(d, slug, *, level_note, severity='default', overrides='null',
                 status='active'):
        (d / 'practices').mkdir(parents=True, exist_ok=True)
        (d / 'practices' / f'{slug}.md').write_text(
            f"---\nslug:        {slug}\ntitle:       {slug}\n"
            f"tier:        on-demand\nseverity:    {severity}\n"
            f'applies_to:  ["**"]\noccasion:    "a fixture occasion"\n'
            f'index_clause: "a fixture clause"\nchecked_by:  null\n'
            f"defines:     []\nstatus:      {status}\nsupersedes:  []\n"
            f"overrides:   {overrides}\nadded:       null\n"
            f'approved_by: "fixture"\n---\n'
            f"## Rule\n{level_note}\n\n## Detail\n\n## Why\n\n"
            f"## Story\n\n## Install\n", encoding='utf-8')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-resolve-'))
    try:
        consumer = tmp / 'a-project'
        universal, team, individual = tmp / 'u', tmp / 't', tmp / 'i'
        (consumer).mkdir()

        # repo-local practices live at the FIXED subdirectory `local`
        # (precedent_resolve.py now requires exactly `path: "local"` for
        # any repo-local source -- see load_config's own docstring) --
        # `practice(consumer / 'local', ...)` writes to
        # consumer/local/practices/, which is exactly what a repo-local
        # source declared at `path: "local"` resolves against.
        consumer_local = consumer / 'local'
        practice(universal, 'shared-slug', level_note='universal wins nothing')
        practice(universal, 'shared-slug-2', level_note='universal wins nothing here either')
        practice(universal, 'universal-only', level_note='only here')
        practice(universal, 'house-style', level_note='what we ship',
                 severity='blocking')
        practice(universal, 'retired-one', level_note='gone', status='retired')
        practice(team, 'shared-slug', level_note='team beats everything, '
                 'even repo-local')
        practice(team, 'team-only', level_note='only here')
        practice(consumer_local, 'shared-slug', level_note='repo-local beats '
                 'individual and universal, but not team')
        practice(consumer_local, 'shared-slug-2', level_note='repo-local beats '
                 'individual and universal here too, and team is not in '
                 'play for this slug at all')
        practice(consumer_local, 'repo-local-only', level_note='only here')
        practice(consumer_local, 'house-style', level_note='a repo-local attempt '
                 'at the same slug the blocking universal practice holds')
        practice(individual, 'shared-slug', level_note='individual beats '
                 'universal, loses to repo-local and team')
        practice(individual, 'shared-slug-2', level_note='individual beats '
                 'universal, loses to repo-local')
        practice(individual, 'individual-only', level_note='only here')
        practice(individual, 'client-tone', level_note='an individual '
                 'practice that must survive a team override attempt',
                 severity='blocking')
        practice(team, 'team-formal-tone', level_note='team tries to '
                 'override the individual\'s blocking client-tone',
                 overrides='client-tone')
        practice(universal, 'old-universal-name', level_note='the universal '
                 'practice an individual practice renames')
        practice(individual, 'my-own-name', level_note='replaces '
                 'old-universal-name', overrides='old-universal-name')
        # A practice whose OWN slug is blocked, that ALSO names an unrelated
        # slug in `overrides:`. Regression fixture for a real bug: the
        # resolver used to process a practice's own-slug collision and its
        # `overrides:` target as independent loop iterations, so a refused
        # own-slug collision did not stop the SAME practice's `overrides:`
        # from still deleting its target -- a practice that was never
        # activated still "shadowed" something, and the report claimed a
        # practice was doing the shadowing that was, in fact, never in force.
        practice(universal, 'client-tone-2', level_note='blocking, unrelated '
                 'to the override target below', severity='blocking')
        practice(universal, 'legacy-note-format', level_note='an unrelated '
                 'universal practice the blocked shared practice tries to '
                 'retire')
        practice(team, 'client-tone-2', level_note='refused: collides with '
                 'a blocking universal practice under its OWN slug',
                 overrides='legacy-note-format')

        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(universal)},
                        {'level': 'team', 'name': 'precedent-team-fixture',
                         'path': str(team)},
                        {'level': 'repo-local', 'name': 'local',
                         'path': 'local'}]}), encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({
            'format_version': 1,
            'individual': {'name': 'precedent-individual',
                           'path': str(individual)}}), encoding='utf-8')

        def run(*extra):
            r = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                 '--repo', str(consumer), '--user-config', str(user_cfg),
                 '--json', *extra],
                capture_output=True, text=True)
            return r.returncode, r.stdout, r.stderr

        rc, out, _err = run()
        if rc != 0:
            check('source precedence (four sources resolved by a consumer repo)',
                  False, f'precedent_resolve.py exited {rc}')
            return
        data = json.loads(out)
        by_slug = {p['slug']: p for p in data['practices']}
        cases = []

        # all four sources are actually in play
        cases.append(('all four sources resolve',
                      {s['level'] for s in data['sources']}
                      == {'universal', 'shared', 'individual', 'repo-local'}))
        # precedence: team > repo-local > individual > universal, on a slug
        # defined at all four
        cases.append(('team beats repo-local beats individual beats '
                      'universal on a slug defined at all four',
                      by_slug.get('shared-slug', {}).get('level') == 'shared'))
        # isolate repo-local's own rank: a slug defined at repo-local,
        # individual and universal, but NOT team, must resolve to repo-local
        cases.append(('repo-local beats individual and universal when team '
                      'is not in play for that slug',
                      by_slug.get('shared-slug-2', {}).get('level') == 'repo-local'))
        # everything unique to a level survives
        for slug, level in (('universal-only', 'universal'),
                            ('individual-only', 'individual'),
                            ('team-only', 'shared'),
                            ('repo-local-only', 'repo-local')):
            cases.append((f'{slug} survives from {level}',
                          by_slug.get(slug, {}).get('level') == level))
        # blocking protects a LOWER-ranked practice from a HIGHER one, not
        # just "team or universal" -- a blocking universal practice survives
        # against team, individual and repo-local all reusing its slug
        cases.append(('a blocking universal practice is not overridden by '
                      'anything above it', by_slug.get('house-style', {}).get('level')
                      == 'universal'))
        # and a blocking INDIVIDUAL practice survives against team, which
        # ranks above individual and would otherwise win by plain precedence
        cases.append(('a blocking individual practice is not overridden by '
                      'a higher-ranked team `overrides:` attempt',
                      by_slug.get('client-tone', {}).get('level') == 'individual'))
        cases.append(('the refusal is reported, not silent',
                      {b['slug'] for b in data['blocked']}
                      == {'house-style', 'client-tone', 'client-tone-2'}))
        # `overrides:` naming a differently-named lower slug: the named
        # practice leaves the set, and the one naming it enters. Without a
        # non-blocking case here, deleting the whole `overrides:` branch still
        # passed -- the two blocking cases pass either way, because a refused
        # override and an ignored one look identical from outside.
        cases.append(('an `overrides:` removes the lower practice it names',
                      'old-universal-name' not in by_slug))
        cases.append(('and the practice doing the overriding enters the set',
                      by_slug.get('my-own-name', {}).get('level') == 'individual'))
        cases.append(('the override is reported',
                      any(s['slug'] == 'old-universal-name' for s in data['overridden'])))
        cases.append(('an overriding practice still enters the set itself '
                      'even when its override attempt is refused by blocking',
                      'team-formal-tone' in by_slug))
        # lifecycle: a retired practice is resolvable but not in force
        cases.append(('a retired practice is not in force',
                      'retired-one' not in by_slug))

        # a practice refused on its OWN slug must not act on `overrides:` --
        # the target of its override must survive untouched, and the report
        # must not credit a never-activated practice with shadowing anything
        cases.append(('a practice blocked on its own slug does not enter '
                      'the resolved set',
                      by_slug.get('client-tone-2', {}).get('level') == 'universal'))
        cases.append(("that same practice's `overrides:` target is left "
                      "alone, since the practice naming it was never "
                      "activated",
                      by_slug.get('legacy-note-format', {}).get('level')
                      == 'universal'))
        cases.append(('and the target is not reported as overridden by a '
                      'practice that was refused',
                      not any(s['slug'] == 'legacy-note-format'
                              for s in data['overridden'])))

        # two same-level practices claiming the same `overrides:` target must
        # fail loudly, not silently drop the second collision. Regression for
        # a real bug: the first same-level practice to process deletes its
        # target from `resolved`, so a second same-level practice naming the
        # same target found `resolved.get(ov)` already None and its override
        # intent vanished with no error and no trace in either practice's
        # `--explain` output. PRACTICE_ENGINE_PLAN.md is explicit this must
        # fail loudly: "the resolver fails loudly if two same-level practices
        # claim one slug."
        collision = tmp / 'collision-project'
        collision.mkdir()
        coll_universal, coll_team = tmp / 'cu', tmp / 'ct'
        practice(coll_universal, 'shared-target',
                 level_note='the contested universal practice')
        practice(coll_team, 'claim-one', level_note='first shared practice',
                 overrides='shared-target')
        practice(coll_team, 'claim-two', level_note='second shared practice',
                 overrides='shared-target')
        (collision / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(coll_universal)},
                        {'level': 'team', 'name': 'precedent-team-fixture',
                         'path': str(coll_team)}]}), encoding='utf-8')
        r_coll = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(collision)],
            capture_output=True, text=True)
        cases.append(("two same-level practices naming one `overrides:` "
                       "target fail loudly instead of silently dropping the "
                       "second",
                       r_coll.returncode == 1 and 'cannot both claim' in
                       (r_coll.stdout + r_coll.stderr)))

        # a shared repo may not name someone's individual set
        leaky = tmp / 'leaky-project'
        leaky.mkdir()
        (leaky / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'individual', 'name': 'precedent-individual',
                         'path': str(individual)}]}), encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(leaky), '--user-config', str(user_cfg)],
            capture_output=True, text=True)
        cases.append(('a shared repo declaring an individual source is refused',
                      r.returncode == 1 and 'individual source' in
                      (r.stdout + r.stderr)))

        # a repo-local source whose path is NOT exactly "local" is refused --
        # the level only means anything if a repo cannot point it at
        # someone else's tree, or at any name of its own choosing, and call
        # that "local"
        elsewhere = tmp / 'elsewhere-project'
        elsewhere.mkdir()
        (elsewhere / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'repo-local', 'name': 'not-actually-local',
                         'path': str(team)}]}), encoding='utf-8')
        r_el = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(elsewhere)],
            capture_output=True, text=True)
        cases.append(('a repo-local source whose path is someone else\'s '
                      'tree entirely is refused',
                      r_el.returncode == 1 and 'repo-local source' in
                      (r_el.stdout + r_el.stderr)))

        # a repo-local source at the bare repo root ("." -- the path that
        # silently lost its own hand-authored content to
        # precedent_materialize.py before this was a hard rule) is refused
        bare_root = tmp / 'bare-root-project'
        bare_root.mkdir()
        (bare_root / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'repo-local', 'name': 'bare-root-local',
                         'path': '.'}]}), encoding='utf-8')
        r_br = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(bare_root)],
            capture_output=True, text=True)
        cases.append(('a repo-local source at the bare repo root (".") is '
                      'refused', r_br.returncode == 1 and 'must resolve to '
                      'exactly "local"' in (r_br.stdout + r_br.stderr)))

        # a repo-local source at some OTHER in-repo subdirectory name (not
        # "local") is refused too -- an in-repo path is necessary but not
        # sufficient; the whole point is that the name is the SAME across
        # every Precedent repo, not merely "somewhere safe"
        other_name = tmp / 'other-name-project'
        other_name.mkdir()
        (other_name / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'repo-local', 'name': 'oddly-named',
                         'path': 'repo-local-stuff'}]}), encoding='utf-8')
        r_on = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(other_name)],
            capture_output=True, text=True)
        cases.append(('a repo-local source at an in-repo but non-"local" '
                      'subdirectory name is refused too',
                      r_on.returncode == 1 and 'must resolve to exactly '
                      '"local"' in (r_on.stdout + r_on.stderr)))

        # but a path that's merely a DIFFERENT SPELLING of "local" -- a
        # trailing slash, or a "./" prefix -- is accepted, not refused: the
        # rule is about the resolved directory, not the literal string. A
        # real bug found testing the strict-string-equality version of this
        # check, fixed by normalizing with posixpath.normpath before
        # comparing.
        for slug_variant in ('local/', './local'):
            spelling = tmp / f'spelling-{slug_variant.replace("/", "-").replace(".", "")}'
            spelling.mkdir()
            (spelling / 'local' / 'practices').mkdir(parents=True)
            (spelling / 'precedent.json').write_text(json.dumps({
                'format_version': 1,
                'sources': [{'level': 'repo-local', 'name': 'local',
                             'path': slug_variant}]}), encoding='utf-8')
            r_sp = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                 '--repo', str(spelling)],
                capture_output=True, text=True)
            cases.append((f'a repo-local path spelled {slug_variant!r} -- the '
                          'same directory as "local", just written '
                          'differently -- is accepted, not refused',
                          r_sp.returncode == 0))

        # degrade gracefully: the individual set is gone (a fresh cloud session)
        shutil.rmtree(individual)
        rc2, out2, err2 = run()
        data2 = json.loads(out2) if rc2 == 0 else {}
        cases.append(('a missing individual set degrades instead of failing',
                      rc2 == 0))
        cases.append(('and says so rather than pretending it was applied',
                      'individual' in err2 and 'not in force' in err2))
        cases.append(('and the team, universal and repo-local practices '
                      'still resolve',
                      {p['slug'] for p in data2.get('practices', [])}
                      >= {'team-only', 'universal-only', 'repo-local-only'}))
        cases.append(('--strict makes a missing source fatal',
                      run('--strict')[0] == 1))

        # --- two sources at the SAME level claiming one slug -------------
        # Nothing orders them, so the winner would be whichever the config
        # lists second. Until 2026-09-06 that is exactly what happened, and
        # it was reported as an ordinary `overridden:` notice on stderr --
        # indistinguishable from a legitimate higher-level override. The
        # plan's own rule is that the resolver fails loudly here.
        two_teams = tmp / 'two-teams'
        (two_teams).mkdir()
        t_a, t_b = tmp / 'precedent-team-a', tmp / 'precedent-team-b'
        practice(t_a, 'shared', level_note='Team A version.')
        practice(t_b, 'shared', level_note='Team B version.')
        practice(t_b, 'b-only', level_note='Only in B.')
        (two_teams / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'team', 'name': 'precedent-team-a', 'path': str(t_a)},
                        {'level': 'team', 'name': 'precedent-team-b', 'path': str(t_b)}]}),
            encoding='utf-8')
        r_two = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(two_teams)], capture_output=True, text=True)
        out_two = r_two.stdout + r_two.stderr
        cases.append(('two shared-level sources defining one slug is a loud '
                      'failure, not a silent last-one-wins',
                      r_two.returncode == 1 and 'shared' in out_two
                      and 'same level' in out_two))

        # ...and two shared sources that DON'T collide still resolve fine --
        # the rule must not have turned "more than one shared source" into an
        # error by itself.
        (t_a / 'practices' / 'shared.md').unlink()
        practice(t_a, 'a-only', level_note='Only in A.')
        r_ok = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(two_teams), '--json'], capture_output=True, text=True)
        slugs_ok = ({p['slug'] for p in json.loads(r_ok.stdout).get('practices', [])}
                    if r_ok.returncode == 0 else set())
        cases.append(('two non-colliding shared sources still resolve together',
                      r_ok.returncode == 0 and {'a-only', 'b-only', 'shared'} <= slugs_ok))

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  precedence did NOT behave as stated: {name}")
        check(f'source precedence ({len(cases)} stated cases: a consumer repo '
              f'resolves universal + team + individual + repo-local, blocking '
              f'wins over precedence, a missing set degrades)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_cross_source_resident_budget():
    """The resident-block cap has to hold across ALL resolved sources, not
    just this repo's own practices/ directory (spec/PRIVATE_SETS_BRIEF.md,
    "One open gap to report back, not to solve there": build_views.py's
    RESIDENT_BUDGET_TOKENS only ever saw this repo's practices/, and
    precedent_resolve.py had no resident/budget logic at all -- a shared set
    marking several practices resident, on top of an individual set doing
    the same, could push a real session's resident block well past the cap
    with nothing objecting).

    THREE DIRECTIONS, ALL SYNTHETIC -- and that is the fix, not a detail.
    Until 2026-09-11 direction 1 ran `precedent_resolve.py --repo <this
    repo>`, which resolves whatever private sources the CONTAINER has
    attached. So the check's result depended on the machine: green where the
    sets were missing, red where they were attached and their own combined
    resident block went over the cap. It failed that way for most of a day,
    and the failure it printed -- "this repo's own resolved set was wrongly
    flagged over budget" -- was wrong twice over: the flag was correct, and
    the set being measured was not this repo's. The same
    [fixture-owns-its-state] shape as the three instances in AGENTS.md's
    gotchas, one level out.

    What replaced it measures the MECHANISM, which is all a harness can own:
    this repo as a single declared source stays clean; a single source over
    the cap is still flagged (so direction 1 is not vacuous); and a
    multi-source combination over the cap is refused. A real combination
    going over is not this check's business -- it is content in somebody's
    private set, reported by `precedent_resolve.py` exiting 1 and enforced by
    `build_views.py` refusing to write an over-budget block, which is a
    harder stop than a harness line. session-load-budget's own Rule says the
    reduction is the owner's to choose, never a session's."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-budget-'))
    try:
        def _consumer(name, sources):
            d = tmp / name
            d.mkdir(parents=True, exist_ok=True)
            (d / 'precedent.json').write_text(json.dumps(
                {'format_version': 1, 'sources': sources}), encoding='utf-8')
            return d

        def _resolve(repo):
            rc, out, err = _run([sys.executable, str(ROOT / 'tools' /
                                 'precedent_resolve.py'), '--repo', str(repo),
                                 '--json'])
            return rc, (json.loads(out) if out else {}), err

        def _resident_source(dirname, slug, words):
            d = tmp / dirname / 'practices'
            d.mkdir(parents=True, exist_ok=True)
            (d.parent / 'practices' / f'{slug}.md').write_text(
                f"---\nslug:        {slug}\ntitle:       Fixture\n"
                "tier:        resident\nseverity:    default\n"
                'applies_to:  ["**"]\noccasion:    null\ngates:       []\n'
                'index_clause: "n/a"\nchecked_by:  null\ndefines:     []\n'
                "status:      active\nsupersedes:  []\noverrides:   null\n"
                'added:       null\napproved_by: "fixture"\n---\n'
                f"## Rule\n{' '.join(['word'] * words)}\n\n## Why\n\n"
                "## Story\n\n## Install\n", encoding='utf-8')
            return (tmp / dirname)

        # direction 1: THIS REPO as the only declared source -- named
        # explicitly, so the container's own attached sources cannot change
        # the answer.
        rc, data, _err = _resolve(_consumer('alone', [
            {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]))
        clean_ok = rc == 0 and not data.get('resident', {}).get('over_budget', True)

        # direction 1's control: a SINGLE source over the cap is flagged, so
        # the pass above means "under budget", not "this code never flags".
        rc1b, data1b, _e1b = _resolve(_consumer('single-over', [
            {'level': 'universal', 'name': 'precedent',
             'path': str(_resident_source('huge-universal', 'huge-alone', 1800))}]))
        single_over_ok = (rc1b == 1
                          and data1b.get('resident', {}).get('over_budget') is True)

        # direction 2: a synthetic shared source with an oversized resident
        # Rule, stacked on top of this repo's own resident practices, must
        # push the combined figure over budget and be refused
        consumer = tmp / 'consumer'
        team = tmp / 'team'
        (consumer).mkdir()
        (team / 'practices').mkdir(parents=True)
        big_rule = ' '.join(['word'] * 1500)  # ~1950 approx-tokens alone
        (team / 'practices' / 'huge-resident.md').write_text(
            "---\nslug:        huge-resident\ntitle:       Huge\n"
            "tier:        resident\nseverity:    default\n"
            'applies_to:  ["**"]\noccasion:    null\ngates:       []\n'
            'index_clause: "n/a"\nchecked_by:  null\ndefines:     []\n'
            "status:      active\nsupersedes:  []\noverrides:   null\n"
            'added:       null\napproved_by: "fixture"\n---\n'
            f"## Rule\n{big_rule}\n\n## Why\n\n## Story\n\n## Install\n",
            encoding='utf-8')
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(ROOT)},
                        {'level': 'team', 'name': 'precedent-team-fixture',
                         'path': str(team)}]}), encoding='utf-8')
        rc2, out2, err2 = _run([sys.executable, str(ROOT / 'tools' /
                                'precedent_resolve.py'), '--repo', str(consumer),
                                '--json'])
        over_data = json.loads(out2) if out2 else {}
        over_ok = (rc2 == 1
                   and over_data.get('resident', {}).get('over_budget') is True
                   and 'huge-resident' in {p['slug'] for p in
                                           over_data.get('resident', {}).get('practices', [])}
                   and 'cross-source cap' in err2)

        ok = clean_ok and single_over_ok and over_ok
        if not clean_ok:
            print("  this repo declared as the ONLY source was flagged over "
                  "budget -- this repo's own resident block, nothing else")
        if not single_over_ok:
            print("  a single source over the cap was NOT flagged, so "
                  "direction 1 proves nothing")
        if not over_ok:
            print("  a synthetic multi-source set built to exceed the budget "
                  "was NOT refused")
        check('cross-source resident budget (this repo as the only declared '
              'source stays clean; a single source over the cap is flagged; a '
              'synthetic team+universal combination over the 2,000-token cap '
              'is refused -- all three synthetic, so the container\'s own '
              'attached sources cannot change the result)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_example_set():
    """The shipped example set is real, parseable, and resolvable.

    The plan ships an example set so an adopter can see what a personal set
    looks like without being shown a real one. An example that has quietly
    stopped matching the format is worse than none: it is the first thing
    someone copies. So it is held to the same parser the catalogue uses, and
    it is actually resolved -- if `overrides:` or the section list changes
    underneath it, this fails rather than the example silently teaching the
    old shape."""
    if not EXAMPLE_SET.is_dir():
        not_applicable('example practice set',
                       f'{EXAMPLE_SET.relative_to(ROOT)} does not exist')
        return
    ok = True
    files = sorted((EXAMPLE_SET / 'practices').glob('*.md'))
    if not files:
        check('example practice set', False, 'the example set holds no practices')
        return
    for f in files:
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            ok = False
            print(f"  {e}")
            continue
        if fm.get('slug') != f.stem:
            ok = False
            print(f"  {f.name}: frontmatter slug {fm.get('slug')!r} does not match "
                  f"the filename")
        missing = [s for s in SECTION_ORDER if s not in sections]
        if missing:
            ok = False
            print(f"  {f.name}: missing section(s) {', '.join(missing)} -- an "
                  f"example that has drifted from the format teaches the wrong "
                  f"shape to whoever copies it")
        if not (sections.get('rule') or '').strip():
            ok = False
            print(f"  {f.name}: empty ## Rule")

    # And it must actually resolve, as somebody's individual set, against
    # this repo's universal catalogue.
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-example-'))
    try:
        cfg = tmp / 'user.json'
        cfg.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'precedent-individual', 'path': str(EXAMPLE_SET)}}),
            encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--user-config', str(cfg), '--json'], capture_output=True, text=True)
        if r.returncode != 0:
            ok = False
            print(f"  the example set does not resolve: "
                  f"{(r.stdout + r.stderr).strip().splitlines()[-1:]}")
        else:
            data = json.loads(r.stdout)
            levels = {p['slug']: p['level'] for p in data['practices']}
            if not any(l == 'individual' for l in levels.values()):
                ok = False
                print("  the example set resolved but contributed no practices")
            # its one `overrides:` must still land on a universal practice that
            # exists -- an override naming a slug nobody has is a no-op that
            # looks like a working example.
            if not data['overridden']:
                ok = False
                print("  the example set's `overrides:` did not override anything "
                      "-- it names a universal slug that no longer exists")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check(f'example practice set ({len(files)} practices parse, match the '
          f'format, and resolve as an individual source)', ok)


def check_source_names_detects_a_rename():
    """precedent_source_names.py -- a declared source repository that has been
    RENAMED is reported, and a name it could not check is never reported as
    current.

    THE INCIDENT (2026-09-11). A shared source was renamed on GitHub. A
    consuming repo went on declaring, cloning, attaching and materializing
    under the old name with every check green, for an unknown number of
    sessions, because GitHub redirects a renamed repository indefinitely:
    clone succeeds, ls-remote succeeds, the sibling clone resolves, the
    practices materialize correctly. It surfaced because a person recognised
    a name he had retired.

    THE REDIRECT PATH, ADDED 2026-09-14. The incident above was reported by
    a person, not by the tool: run against the real renamed repository the
    tool answered UNVERIFIED, because GitHub's 301 points at the numeric-ID
    form (`/repositories/1352494938`) and the session proxy refuses it, so
    the tool caught the error and said it could not check. A redirect is
    conclusive on its own -- a repository still called that does not
    redirect -- so it is now RENAMED whether or not the new name can be
    read, and `--check` fails on it.

    THE API CALL IS STUBBED HERE AND MEASURED ELSEWHERE. A harness case may
    not depend on the network, and no renamed repository is reachable from a
    hosted session anyway -- api.github.com answers 403 for every repo the
    session has not attached. What the stub cannot prove was measured live
    on 2026-09-11 against `alex137/bestpractice`: the API's response BODY
    carries the canonical `full_name` (`alex137/BestPractice`) whatever
    spelling was asked for, which is why this reads the body and never the
    status code or the final URL. The tool reported SPELLING on that run.

    The UNVERIFIED case is the one that matters most (practice:
    fail-gracefully): "could not check" and "checked, the name is current"
    must never render the same, so each case asserts the printed verdict,
    not merely that something was printed (practice:
    control-asserts-which-failure)."""
    import io, shutil, tempfile, urllib.error, urllib.request
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_names as psn

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-names-'))
    cases = []
    real_api = psn.api_full_name
    try:
        consumer = tmp / 'consumer'
        consumer.mkdir()
        clone = tmp / 'precedent-team-fixture'
        clone.mkdir()
        subprocess.run(['git', 'init', '-q', str(clone)], capture_output=True)
        subprocess.run(['git', '-C', str(clone), 'remote', 'add', 'origin',
                        'https://github.com/example/precedent-team-fixture'],
                       capture_output=True)
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'team', 'name': 'precedent-team-fixture',
                         'path': '../precedent-team-fixture'}]}),
            encoding='utf-8')

        # The fixture OWNS its user config. Without this it inherits the
        # machine's real individual source and grades that too, which is
        # how the first run of this case reported two rows where it
        # asserted one (practice: fixture-owns-its-state).
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({}), encoding='utf-8')

        def run_with(stub):
            psn.api_full_name = stub
            rows = psn.assess(str(consumer), user_config=str(user_cfg))
            buf = io.StringIO()
            psn.report(rows, out=buf)
            return rows, buf.getvalue()

        rows, out = run_with(lambda o, n, env=None:
                             ('example/precedent-team-repo-maintenance', None, False))
        cases.append(('a renamed source is reported as RENAMED, naming both '
                      'the name this repo fetches and the one GitHub uses now',
                      [r['verdict'] for r in rows] == ['RENAMED']
                      and 'example/precedent-team-fixture' in out
                      and 'example/precedent-team-repo-maintenance' in out,
                      out))

        rows, out = run_with(lambda o, n, env=None:
                             ('example/precedent-team-fixture', None, False))
        cases.append(('an unrenamed source is OK, and the summary counts zero '
                      'renamed and zero unchecked',
                      [r['verdict'] for r in rows] == ['OK']
                      and '0 renamed, 0 NOT checked' in out, out))

        rows, out = run_with(lambda o, n, env=None:
                             (None, 'GitHub answered HTTP 403: not enabled', False))
        cases.append(('a source whose name could NOT be checked is UNVERIFIED '
                      'with the reason, never OK, and the summary says an '
                      'unchecked source is not a passing one',
                      [r['verdict'] for r in rows] == ['UNVERIFIED']
                      and 'HTTP 403' in out
                      and '1 NOT checked' in out
                      and 'an unchecked source is not a passing one' in out,
                      out))

        # A NAME THE SESSION READ FROM list_repos (2026-10-01, from a
        # consumer's Update Vendors): the auto-mode classifier refused the
        # push attach that lets the API answer, and list_repos had already
        # given each repository's current full_name. Supplied with
        # --canonical, it settles the name where the API could not.
        psn.api_full_name = (lambda o, n, env=None:
                             (None, 'GitHub answered HTTP 403: not enabled', False))

        def verdicts(canonical):
            return [r['verdict'] for r in psn.assess(
                str(consumer), user_config=str(user_cfg), canonical=canonical)]
        cases.append(('an unreachable API with the name listed exactly by '
                      '--canonical is OK',
                      verdicts(['example/precedent-team-fixture']) == ['OK'], ''))
        cases.append(('...listed in another case, SPELLING',
                      verdicts(['Example/Precedent-Team-Fixture']) == ['SPELLING'], ''))
        cases.append(('...not listed at all, still UNVERIFIED -- the list cannot '
                      'tell a rename from a repository out of reach',
                      verdicts(['example/precedent-team-other']) == ['UNVERIFIED'], ''))
        psn.api_full_name = (lambda o, n, env=None:
                             ('example/precedent-team-repo-maintenance', None, False))
        cases.append(('where the API answers, its answer wins over --canonical',
                      verdicts(['example/precedent-team-fixture']) == ['RENAMED'], ''))
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_source_names.py'),
                            '--repo', str(consumer), '--user-config', str(user_cfg),
                            '--canonical', 'example/precedent-team-fixture'],
                           capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, https_proxy='http://127.0.0.1:9',
                                    HTTPS_PROXY='http://127.0.0.1:9',
                                    GITHUB_TOKEN='', GH_TOKEN=''))
        cases.append(('the command line takes --canonical OWNER/NAME',
                      r.returncode == 0 and 'OK' in r.stdout
                      and 'precedent-team-fixture' in r.stdout,
                      failure_detail(r.stdout + r.stderr, 300)))

        # THE REDIRECT, which is the case this tool exists for and the one
        # it got wrong until 2026-09-14. GitHub answers 301 for a renamed
        # repository, `urlopen` followed it by default, the Location is the
        # numeric-ID form, and a session proxy refuses that form -- so the
        # tool caught an HTTPError and said "could not check" about the one
        # input that is conclusive on its own. Both halves are stated: the
        # verdict must be RENAMED even when the new name cannot be read, and
        # the detail must not pretend to know a name it never got.
        class _FakeOpener:
            def __init__(self, second=None):
                self.calls = 0
                self.second = second

            def open(self, req, timeout=None):
                self.calls += 1
                if self.calls == 1 or self.second is None:
                    raise urllib.error.HTTPError(
                        'https://api.github.com/repos/example/old-name', 301,
                        'Moved Permanently',
                        {'Location': 'https://api.github.com/repositories/1352494938'},
                        io.BytesIO(b'{}'))
                return io.BytesIO(json.dumps(self.second).encode('utf-8'))

        # The two cases below exercise the REAL api_full_name, so the stub
        # the run_with cases above installed has to come off first -- leaving
        # it on measures the stub (practice: fixture-owns-its-state).
        psn.api_full_name = real_api
        real_build = urllib.request.build_opener
        try:
            fake = _FakeOpener()
            urllib.request.build_opener = lambda *a, **k: fake
            full, why, renamed = psn.api_full_name('example', 'old-name')
            cases.append(('a 301 whose Location cannot be read is still a '
                          'rename: renamed is True, no name is invented, and '
                          'the detail says how to read the current one',
                          (full, renamed) == (None, True)
                          and 'is NOT what this repository is called' in (why or '')
                          and '1352494938' in (why or '')
                          and 'github.com/example/old-name' in (why or ''),
                          why or ''))

            fake2 = _FakeOpener(second={'full_name': 'example/new-name'})
            urllib.request.build_opener = lambda *a, **k: fake2
            full, why, renamed = psn.api_full_name('example', 'old-name')
            cases.append(('a 301 whose Location CAN be read reports the new '
                          'name, and still as a rename',
                          (full, why, renamed) == ('example/new-name', None, True),
                          str((full, why, renamed))))
        finally:
            urllib.request.build_opener = real_build

        # And the verdict the redirect produces has to survive into the
        # report: a row with no `current` name used to render UNVERIFIED
        # unconditionally, which is exactly the bug.
        rows, out = run_with(lambda o, n, env=None:
                             (None, 'that name is a redirect', True))
        cases.append(('a source whose rename was proven by a redirect is '
                      'RENAMED in the report and counts against --check, not '
                      'UNVERIFIED',
                      [r['verdict'] for r in rows] == ['RENAMED']
                      and '1 renamed' in out, out))

        # A case difference is not a rename: git does not care, and reporting
        # it as one would cry wolf on every clone URL a tool lowercased.
        rows, out = run_with(lambda o, n, env=None:
                             ('example/Precedent-Team-Fixture', None, False))
        cases.append(('a name differing only in case is SPELLING, not RENAMED',
                      [r['verdict'] for r in rows] == ['SPELLING'], out))

        # THE OFFLINE HALF, which costs no network and nothing else prints.
        subprocess.run(['git', '-C', str(clone), 'remote', 'set-url', 'origin',
                        'https://github.com/example/something-else'],
                       capture_output=True)
        rows, out = run_with(lambda o, n, env=None:
                             ('example/something-else', None, False))
        cases.append(('the declared name disagreeing with the clone\'s own '
                      'remote is reported as DRIFT even when the API says the '
                      'repository is current',
                      'DRIFT' in out and rows[0]['verdict'] == 'OK', out))

        # A remote this tool has no API for is UNVERIFIED, not OK -- guessing
        # an API for an unknown host answers from the wrong server.
        subprocess.run(['git', '-C', str(clone), 'remote', 'set-url', 'origin',
                        'https://git.example.com/example/precedent-team-fixture'],
                       capture_output=True)
        rows, out = run_with(lambda o, n, env=None:
                             (None, 'should not be called', False))
        cases.append(('a source on a non-github host is UNVERIFIED, not OK',
                      [r['verdict'] for r in rows] == ['UNVERIFIED']
                      and 'github.com' in out, out))

        # THE SECRET. A tokenised remote URL is parsed rather than skipped,
        # and the token is not what comes back out.
        # Assembled rather than written out: the leak gate reads
        # `<anything>@github.com` as an email address, correctly, and a
        # fixture is not worth a false hit on every run.
        tokenised = ('https://x-access-token:ghp_NOTAREALTOKEN' + '@'
                     + 'github.com/example/a-repo.git')
        owner, name = psn.parse_remote(tokenised)
        cases.append(('a remote carrying a credential is parsed, and the '
                      'credential is not in what comes back',
                      (owner, name) == ('example', 'a-repo')))
    finally:
        psn.api_full_name = real_api
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_source_names.py reports a renamed source and never '
          f'reports an unchecked one as current ({len(cases)} stated cases: '
          f'renamed, unrenamed, unverified, a 301 whose new name cannot be '
          f'read, a 301 whose new name can, that redirect surviving into the '
          f'report, case-only, declared-vs-remote drift, a non-github host, '
          f'and a tokenised remote URL)',
          not bad, '; '.join(f"{n}: {d}" for n, d in bad))


def check_source_survey_gives_every_repository_a_verdict():
    """precedent_source_survey.py -- vendor-update-runbook step 9, should a
    source be added or dropped, gives every repository the account reaches a
    verdict, and a repository it could not read is never a pass.

    THE INCIDENT (2026-11-01). Step 9 was prose. A session running Update
    Vendors in a practice set listed the account's repositories, found one
    it had no clone of, and reported "not on disk, so I didn't check whether
    it's a practice set" -- half the step, and nothing said so until the
    person asked. Each case asserts the verdict printed for one repository
    (practice: control-asserts-which-failure), and the fixture owns its
    user config, so the machine's real individual set is never surveyed
    (practice: fixture-owns-its-state)."""
    import io, shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_survey as pss

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-survey-'))
    cases = []

    def clone(name, origin, source=None):
        d = tmp / name
        d.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
        subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin',
                        f'https://github.com/{origin}'], capture_output=True)
        if source is not None:
            (d / 'precedent-source.json').write_text(json.dumps(source),
                                                     encoding='utf-8')
        return d

    try:
        consumer = clone('consumer', 'example/consumer')
        clone('precedent-shared-fixture', 'example/precedent-shared-fixture',
              {'name': 'precedent-shared-fixture', 'level': 'shared',
               'subject': 'the fixture subject'})
        clone('precedent-shared-old', 'example/precedent-shared-old',
              {'name': 'precedent-shared-old', 'level': 'shared',
               'retired': {'date': '2026-10-01',
                           'folded_into': ['precedent-shared-fixture']}})
        clone('a-project', 'example/a-project')
        clone('precedent-shared-other', 'example/precedent-shared-other',
              {'name': 'precedent-shared-other', 'level': 'shared',
               'subject': 'how to keep the other books'})
        # A folder called for a candidate, holding a clone of something else.
        clone('precedent-shared-impostor', 'example/somebody-else')
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [
                {'level': 'shared', 'name': 'precedent-shared-fixture',
                 'path': '../precedent-shared-fixture'},
                {'level': 'shared', 'name': 'precedent-shared-old',
                 'path': '../precedent-shared-old'},
                {'level': 'shared', 'name': 'precedent-shared-gone',
                 'path': '../precedent-shared-gone'}]}), encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({}), encoding='utf-8')

        candidates = ['example/consumer', 'example/precedent-shared-fixture',
                      'example/precedent-shared-old', 'example/a-project',
                      'Example/Precedent-Shared-Other',
                      'example/precedent-shared-impostor',
                      'example/precedent-shared-unseen']
        rows = pss.survey(str(consumer), candidates, user_config=str(user_cfg))
        by = {r['repo']: r for r in rows}
        verdict = {k: v['verdict'] for k, v in by.items()}
        buf = io.StringIO()
        pss.report(rows, out=buf)
        out = buf.getvalue()

        cases.append(('the repository being surveyed is THIS REPO',
                      verdict.get('example/consumer') == 'THIS REPO', out))
        cases.append(('a set precedent.json declares is DECLARED',
                      verdict.get('example/precedent-shared-fixture')
                      == 'DECLARED', out))
        cases.append(('a declared set that says it is retired is SHOULD DROP?, '
                      'naming the set it folded into',
                      verdict.get('example/precedent-shared-old') == 'SHOULD DROP?'
                      and 'precedent-shared-fixture' in
                      by.get('example/precedent-shared-old', {}).get('detail', ''),
                      out))
        cases.append(('a clone with no precedent-source.json is NOT A SET',
                      verdict.get('example/a-project') == 'NOT A SET', out))
        cases.append(('a set not in force is SHOULD ADD?, with its subject, '
                      'found though the candidate is spelled in another case',
                      verdict.get('Example/Precedent-Shared-Other') == 'SHOULD ADD?'
                      and 'how to keep the other books' in out, out))
        cases.append(('a folder named for a candidate but cloned from another '
                      'repository is not taken for it: NOT ON DISK, saying '
                      'what the folder holds instead',
                      verdict.get('example/precedent-shared-impostor')
                      == 'NOT ON DISK' and 'example/somebody-else' in
                      by.get('example/precedent-shared-impostor', {}).get(
                          'detail', ''), out))
        cases.append(('a candidate with no clone at all is NOT ON DISK, and the '
                      'line says to attach, clone and run it again',
                      verdict.get('example/precedent-shared-unseen') == 'NOT ON DISK'
                      and 'run this again' in
                      by.get('example/precedent-shared-unseen', {}).get('detail', ''),
                      out))
        gone = [r for r in rows if 'precedent-shared-gone' in r['repo']]
        cases.append(('a declared set with no clone that the account no longer '
                      'reaches is SHOULD DROP?',
                      [r['verdict'] for r in gone] == ['SHOULD DROP?'], out))
        cases.append(('the summary counts what was not checked and says an '
                      'unchecked repository is not a passing one',
                      '2 NOT checked' in out
                      and 'an unchecked repository is not a passing one' in out,
                      out))

        def exit_of(argv):
            real = sys.stdout
            sys.stdout = io.StringIO()
            try:
                return pss.main(argv)
            finally:
                sys.stdout = real
        base = ['--repo', str(consumer), '--user-config', str(user_cfg)]
        cases.append(('it exits 1 while any repository is NOT ON DISK',
                      exit_of(base + sum((['--candidate', c] for c in
                                          candidates), [])) == 1, ''))
        cases.append(('...and 0 once every candidate was read',
                      exit_of(base + ['--candidate', 'example/a-project',
                                      '--candidate',
                                      'example/precedent-shared-fixture']) == 0,
                      ''))
        cases.append(('with no --candidate at all it exits 1: step 9 is not '
                      'done on the sources in force alone',
                      exit_of(base) == 1, ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_source_survey.py gives every repository a verdict and '
          f'never passes one it could not read ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n}: {d}" for n, d in bad))


def check_steps_8_and_9_tools_ship_to_every_kind_of_repo():
    """Update Vendors steps 8 and 9 apply wherever a repo declares sources,
    practice sets included, so their tools are in the shared ENGINE_FILES.

    THE INCIDENT (2026-11-01). precedent_source_names.py was
    CONSUMER_ENGINE_FILES-only, on the reasoning that a practice set has no
    multi-source config. A set that declares two sources ran Update Vendors,
    found step 8's tool missing, and ran it from the BestPractice clone."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as pve
    import precedent_update as pu
    tools = ('precedent_source_credentials.py', 'precedent_source_names.py',
             'precedent_source_survey.py')
    missing = [t for t in tools if t not in pve.ENGINE_FILES]
    twice = [t for t in tools if pve.CONSUMER_ENGINE_FILES.count(t) != 1]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-steps-'))
    try:
        (tmp / 'precedent.json').write_text(json.dumps(
            {'sources': [{'level': 'shared', 'name': 'x', 'path': '../x'}]}),
            encoding='utf-8')
        lines = '\n'.join(pu.source_steps_lines(tmp))
        (tmp / 'precedent.json').write_text(json.dumps({}), encoding='utf-8')
        none = '\n'.join(pu.source_steps_lines(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    done_ok = ('precedent_source_names.py' in lines
               and 'precedent_source_survey.py' in lines
               and '--candidate' in lines
               and 'not applicable: this repo declares no sources' in none
               and 'precedent_source_survey.py' in none)
    check('steps 7, 8 and 9\'s tools are in the shared ENGINE_FILES, so a '
          'practice set vendors them, and DONE names each step\'s command '
          '(step 8 not applicable only where no source is declared)',
          not missing and not twice and done_ok,
          f'not in ENGINE_FILES: {missing}; not once in CONSUMER_ENGINE_FILES: '
          f'{twice}; DONE lines: {lines!r} / {none!r}')


def _raw_level_comparisons(text):
    """-> [line numbers] of raw level comparisons in Python `text`."""
    import ast

    def raw(n):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == 'get' and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == 'level'):
            return True
        return (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                and n.slice.value == 'level')

    def names(n):
        if isinstance(n, ast.Constant):
            return n.value in _LEVEL_NAMES
        if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
            return any(isinstance(e, ast.Constant) and e.value in _LEVEL_NAMES
                       for e in n.elts)
        if isinstance(n, ast.Name):
            return n.id.upper().endswith('LEVELS')
        return isinstance(n, ast.Attribute) and n.attr.upper().endswith('LEVELS')

    def own(scope):
        # The scope's own nodes: a nested function is a scope of its own, so
        # a name bound raw in one function never taints another's `level`.
        todo = list(ast.iter_child_nodes(scope))
        while todo:
            n = todo.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                todo.extend(ast.iter_child_nodes(n))

    out = set()
    tree = ast.parse(text)
    for scope in ast.walk(tree):
        if not isinstance(scope, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound = set()
        for a in own(scope):
            if not isinstance(a, ast.Assign):
                continue
            for t in a.targets:
                if isinstance(t, ast.Name) and raw(a.value):
                    bound.add(t.id)
                if isinstance(t, ast.Tuple) and isinstance(a.value, ast.Tuple):
                    bound |= {te.id for te, ve in zip(t.elts, a.value.elts)
                              if isinstance(te, ast.Name) and raw(ve)}
        for c in own(scope):
            if not isinstance(c, ast.Compare):
                continue
            sides = [c.left] + list(c.comparators)
            if any(names(s) for s in sides) and any(
                    raw(s) or (isinstance(s, ast.Name) and s.id in bound) for s in sides):
                out.add(c.lineno)
    return sorted(out)


def check_source_level_reads_go_through_the_normalizer():
    """No tool compares a source's raw `level` against a level name.

    2026-10-09: a consumer declared two deleted sets at the older `team`
    level and Update Vendors removed neither, because the drop compared the
    raw field against "shared" while the resolver read `team` as shared. The
    same raw comparison sat in a dozen other tools, several kept right only
    by a hand-written ('shared', 'team') pair. Every one now reads the level
    through precedent_resolve.declared_level (or normalize_level); this
    refuses a new raw one anywhere in tools/, and shows the scan catching
    the shapes it is meant to catch. The fallback alias tables kept for a
    copy with no resolver beside it must equal the resolver's own."""
    cases = []
    skip = {'verify_harness.py', 'precedent_resolve.py'}
    hits = []
    # The scanner flags only a comparison with a raw read, and a raw read is
    # a 'level' string constant, so a file whose text quotes no `level` is
    # never parsed: about a quarter of tools/ is, at half the time.
    quoted = re.compile(r"""['"]level['"]""")
    for f in sorted((ROOT / 'tools').glob('*.py')):
        if f.name in skip:
            continue
        try:
            text = f.read_text(encoding='utf-8')
            if not quoted.search(text):
                continue
            hits += [f'{f.name}:{n}' for n in _raw_level_comparisons(text)]
        except (OSError, SyntaxError) as e:
            hits.append(f'{f.name}: unreadable ({e})')
    cases.append(('no tool compares a raw source level', not hits, ', '.join(hits[:20])))
    injected = {
        "def f(s):\n    return s.get('level') == 'shared'\n": True,
        "def f(s):\n    return s['level'] in ('shared', 'team')\n": True,
        "def f(s):\n    lvl, p = s.get('level'), s.get('path')\n    return lvl not in X_LEVELS\n": True,
        "def f(s):\n    return s.get('level') in bv.PRIVATE_LEVELS\n": True,
        "def f(s):\n    return pr.declared_level(s) == 'shared'\n": False,
        "def f(s):\n    return pr.normalize_level(s.get('level')) in ('shared',)\n": False,
        "def f(s):\n    return s.get('level') == 'repo-local'\n": False,
        "def f(s):\n    level = s.get('level')\n\ndef g(s):\n    level = pr.declared_level(s)\n    return level == 'shared'\n": False,
        "def f(s):\n    level = s.get('level')\n    return level == 'shared'\n": True,
    }
    for code, want in injected.items():
        got = bool(_raw_level_comparisons(code))
        cases.append((('catches ' if want else 'passes ') + code.split('\n')[-2].strip(),
                      got == want))
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_resolve as _pr
        import leak_gate as _lg
        import precedent_source_bootstrap as _psb
        import precedent_engine_freshness as _pef
    finally:
        sys.path.pop(0)
    for mod, attr in ((_lg, '_FALLBACK_LEVEL_ALIASES'), (_psb, 'LEVEL_ALIASES'),
                      (_pef, '_FALLBACK_LEVEL_ALIASES')):
        cases.append((f'{mod.__name__}.{attr} equals the resolver\'s alias table',
                      getattr(mod, attr, None) == _pr.LEVEL_ALIASES))
    dl = getattr(_pr, 'declared_level', None)
    ds = getattr(_pr, 'declared_sources', None)
    cases.append(('declared_level reads team as shared, and leaves shared alone',
                  dl is not None and dl({'level': 'team'}) == 'shared'
                  and dl({'level': 'shared'}) == 'shared' and dl('x') is None))
    got = ds({'sources': [{'level': 'team', 'name': 'a'}, 'junk',
                          {'level': 'universal', 'name': 'u'}]}) if ds else []
    cases.append(('declared_sources normalizes every entry and drops non-objects',
                  [(s['name'], s['level']) for s in got] == [('a', 'shared'), ('u', 'universal')]))
    bad = [c[0] + (f' ({c[2]})' if len(c) > 2 and c[2] else '') for c in cases if not c[1]]
    check(f'every source-level comparison goes through the one reader '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_engine_capability_holds_a_practice_back():
    """A practice that names an engine capability in `requires:` is in force
    on an engine that has it, and held back -- check and all -- on one that
    does not; the sync says which (2026-10-07: a set's hooks-declaring
    practice reached a consumer whose engine could not wire hooks, and its
    check refused an unrelated merge)."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr
    import precedent_sync_views as _sv
    cases = []
    base = (ROOT / 'practices' / 'no-version-suffix.md').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp) / 'set'
        (d / 'practices').mkdir(parents=True)
        (d / 'precedent-source.json').write_text(json.dumps(
            {'name': 'fx-set', 'level': 'shared', 'visibility': 'public'}),
            encoding='utf-8')
        for slug, need in (('needs-hooks', 'engine:practice-hooks'),
                           ('needs-future', 'engine:not-built-yet')):
            text = base.replace('slug:        no-version-suffix', f'slug:        {slug}', 1)
            text = text.replace('\nstatus:', f'\nrequires:    ["{need}"]\nstatus:', 1)
            (d / 'practices' / f'{slug}.md').write_text(text, encoding='utf-8')
        src = [{'level': 'shared', 'name': 'fx-set', 'path': str(d)}]
        got = _pr.resolve([dict(s) for s in src])['practices']
        cases.append(('a practice needing a capability this engine has is in force',
                      'needs-hooks' in got))
        cases.append(('one needing a capability no engine has yet is held back',
                      'needs-future' not in got))
        notes = _sv.held_for_a_newer_engine([dict(s) for s in src])
        cases.append(('the sync names the held-back practice and says Update Vendors',
                      len(notes) == 1 and 'needs-future' in notes[0]
                      and 'Update Vendors' in notes[0]))
        real = _pr.ENGINE_CAPABILITIES
        try:
            _pr.ENGINE_CAPABILITIES = frozenset()
            got = _pr.resolve([dict(s) for s in src])['practices']
            cases.append(('on an engine without hook wiring, the hooks practice '
                          'is held back, so no check it cannot pass is installed',
                          'needs-hooks' not in got))
        finally:
            _pr.ENGINE_CAPABILITIES = real
    bad = [n for n, ok in cases if not ok]
    check(f'an engine capability in requires: holds a practice back on an engine '
          f'without it ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_session_practices_load_without_publishing():
    """The team and individual practices reach a session here, and cannot
    reach a commit.

    THE PROBLEM (spec/PRELAUNCH_AUDIT.md, 2026-09-06). precedent.json
    declares more sources than the committed AGENTS.md carries, and 43 of
    the 114 practices in force reached no loading channel at all -- a
    session was never shown the team's or the person's own rules while the
    config said they bind the work.

    WHY THE OBVIOUS FIX IS WRONG HERE. Rendering the resolved multi-source
    set into AGENTS.md would publish private practice text, in a PUBLIC
    repo, on the commit that added the feature. The constraint is on
    COMMITTING that text, not on LOADING it -- so it is generated at session
    start into .precedent/, which is gitignored.

    The two properties that make that safe are asserted together here,
    because either alone is worthless: the file must actually carry the
    other sources' practices, AND it must be impossible to commit."""
    import tempfile, shutil, json as _json
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_practices as psp

    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-session-'))
    try:
        # A repo declaring universal (itself) + a shared source.
        repo = tmp / 'repo'
        (repo / 'practices').mkdir(parents=True)
        team = tmp / 'team' / 'practices'
        team.mkdir(parents=True)
        src = (ROOT / 'practices' / 'verify-postcondition.md').read_text(encoding='utf-8')

        def mk(dest, slug, occasion):
            x = re.sub(r'^slug:(\s+)\S+$', rf'slug:\g<1>{slug}', src, count=1, flags=re.M)
            x = re.sub(r'^occasion:.*$', f'occasion:    {_json.dumps(occasion)}',
                       x, count=1, flags=re.M)
            (dest / f'{slug}.md').write_text(x, encoding='utf-8')

        mk(repo / 'practices', 'universal-one', 'doing universal work')
        mk(team, 'team-only-rule', 'committing work in this repo')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'public',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                        {'level': 'team', 'name': 'precedent-team-repo-maintenance',
                         'path': str(tmp / 'team')}]}), encoding='utf-8')

        extra, levels, notes = psp.collect(str(repo))
        slugs = {fm['slug'] for fm, _s, _f in extra}
        cases.append(("a shared source's practice IS collected for the session",
                      'team-only-rule' in slugs))
        cases.append(('...and the universal one is NOT duplicated -- it is already '
                      'in the committed AGENTS.md, and repeating it would double '
                      'every session\'s resident block',
                      'universal-one' not in slugs))
        cases.append(('the level is carried, so the block can say where a rule came from',
                      levels.get('team-only-rule') == 'shared'))

        text = psp.render(extra, levels, notes)
        cases.append(('the rendered block names the shared practice',
                      'team-only-rule' in text))
        cases.append(('...and warns, in the file itself, never to commit it',
                      'Never commit it' in text))

        # An unreachable source is NAMED, not silently dropped.
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'public',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                        {'level': 'team', 'name': 'precedent-team-repo-maintenance',
                         'path': str(tmp / 'no-such-dir')}]}), encoding='utf-8')
        _extra, _levels, notes2 = psp.collect(str(repo))
        # notes are (kind, text) since 2026-09-13 -- the tag is what keeps a
        # DEFERRED source out of the "did not resolve" heading, so assert the
        # tag as well as the name. `in n` on a bare tuple tests membership of
        # an element, not substring, so the old form silently stopped
        # asserting anything the moment the tag landed.
        cases.append(('an unresolved source is NAMED in the output -- "unreachable" '
                      'and "that source has no rules" must not look the same',
                      any('precedent-team-repo-maintenance' in txt
                          for _k, txt in notes2)))
        cases.append(('...and it is TAGGED unresolved, so it renders under the '
                      'failure heading rather than the deferral one',
                      any(k == 'unresolved'
                          and 'precedent-team-repo-maintenance' in txt
                          for k, txt in notes2)))
        _rendered = psp.render(_extra, _levels, notes2)
        cases.append(('...and the file still renders rather than failing',
                      'did not resolve' in _rendered))
        _deferred_only = psp.render(_extra, _levels,
                                    [('deferred', 'precedent deferred to it')])
        cases.append(('a DEFERRED source is not filed under "did not resolve" '
                      '-- both kinds shared one heading until 2026-09-13, so a '
                      'set was told its working sources had failed',
                      'did not resolve' not in _deferred_only
                      and ('resolved' in _deferred_only
                           or 'precedent deferred to it' in _deferred_only)))
        # 2026-10-13, from a consuming repository: a bare "every source ...
        # resolved" beside an ACCESS list showing some as HANDOFF read as
        # a contradiction. The line says resolved means readable, and
        # names the list that answers whether a push will land.
        # Where no source adds anything here (an isolated copy, whose
        # fixture set does not resolve beside it), render() takes its
        # "Nothing to add" path and claims nothing resolved: then there is
        # no line to judge, only no bare claim.
        _claims = 'declares resolved' in _deferred_only
        cases.append(('the resolved line says it means resolved for reading, '
                      'and points at the ACCESS list for pushing; no bare '
                      '"resolved" claim is ever printed',
                      ('resolved for reading' in _deferred_only
                       and 'ACCESS list' in _deferred_only
                       and 'HANDOFF' in _deferred_only)
                      if (_extra or _claims) else
                      'Nothing to add' in _deferred_only))

        # WHAT THE FILE SAYS ABOUT THE REPO IT IS IN HAS TO BE TRUE. The
        # header explains why the file is untracked, and until 2026-09-14
        # every CONSUMER got "this repository is public" -- measured in a
        # private repo whose precedent.json declares `visibility: private`,
        # where a session opening the file read a false claim about the
        # repository it was working in. A practice set was already carved
        # out for exactly this reason; a private consumer had not been.
        pub = psp.render(_extra, _levels, [], repo=str(repo))
        cases.append(('a PUBLIC consumer still says so -- the reason is true '
                      'there and is what makes the instruction land',
                      'this repository is public' in pub))
        priv = tmp / 'private-repo'
        priv.mkdir()
        (priv / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        privtxt = psp.render(_extra, _levels, [], repo=str(priv))
        cases.append(('a PRIVATE consumer is never told its repository is '
                      'public, and still gets a reason and the same '
                      '"never commit it" instruction',
                      'this repository is public' not in privtxt
                      and 'goes stale' in privtxt
                      and 'Never commit it' in privtxt))
        # An ABSENT visibility keeps reading as public, matching
        # build_views.visibility_is_declared -- this file must not
        # contradict the tree it is generated beside.
        nov = tmp / 'undeclared-repo'
        nov.mkdir()
        (nov / 'precedent.json').write_text(_json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        cases.append(('an UNDECLARED visibility still reads as public here, '
                      'as it does everywhere else in the engine',
                      'this repository is public'
                      in psp.render(_extra, _levels, [], repo=str(nov))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A SET THAT IS NOT STALE STILL GETS REPAIRED, and all three repairs
    # happen together. Both halves were wrong for one afternoon: the wiring
    # and ignore repairs sat inside apply_to(), which runs over the STALE sets
    # only, so a set already current got neither -- and _repairable() did not
    # look for either, so such a set appeared on no list at all. Separately,
    # hook-INSTALL and WIRING were reached by different paths, so one --apply
    # wired a hook into SessionStart and left the file absent: a
    # declared-but-missing hook, which the harness reports as nothing.
    # Reported by the set it happened in.
    rtmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-repair-'))
    try:
        import json as _j
        import precedent_refresh_sources as _rs
        import precedent_bootstrap_source as _bs3
        st = rtmp / 'set'
        (st / '.claude' / 'hooks').mkdir(parents=True)
        (st / '.claude' / 'settings.json').write_text(_j.dumps({'hooks': {
            'SessionStart': [{'hooks': [{'type': 'command', 'command':
                '$CLAUDE_PROJECT_DIR/.claude/hooks/'
                + _bs3.INDIVIDUAL_SOURCE_HOOK}]}]}}, indent=2), encoding='utf-8')
        entry = {'repo': str(st), 'hooks': {'missing': []}, 'stale': False}
        found = _rs._repairable(entry)
        cases.append(('a set that is NOT stale but is missing the wiring reads '
                      'as repairable -- apply_to() only walks the stale ones, '
                      'so this list is the only way such a set is reached',
                      any(_bs3.UNIVERSAL_CATALOGUE_HOOK in m for m in found)))
        cases.append(('...and a missing `.precedent/` ignore line does too',
                      any('.precedent/' in m for m in found)))
        ok, _msg = _rs.repair_hooks(st)
        wired = _bs3.UNIVERSAL_CATALOGUE_HOOK in ' '.join(_bs3._wired_commands(st))
        present = (st / '.claude' / 'hooks'
                   / _bs3.UNIVERSAL_CATALOGUE_HOOK).is_file()
        cases.append(('one repair pass installs the hook FILE and wires it and '
                      'writes the ignore line -- a hook wired but absent is one '
                      'the harness reports as nothing at all',
                      ok and wired and present
                      and '.precedent/' in (st / '.gitignore').read_text()))
    finally:
        shutil.rmtree(rtmp, ignore_errors=True)

    # THE WIRING IS REPAIRABLE BY A TOOL, which is the whole reason nobody
    # has to edit .claude/settings.json by hand. The harness refuses a SESSION
    # hand-editing that file; it does not refuse a vendored tool writing a
    # hook the engine ships, and a person was sent to a GitHub web form for
    # three turns before anybody tested the difference.
    wtmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-wire-'))
    try:
        import json as _json
        import precedent_bootstrap_source as _bs2
        ws = wtmp / 'set' / '.claude'
        ws.mkdir(parents=True)
        (ws / 'settings.json').write_text(_json.dumps({'hooks': {'SessionStart': [
            {'hooks': [{'type': 'command',
                        'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/'
                                   + _bs2.INDIVIDUAL_SOURCE_HOOK},
                       {'type': 'command',
                        'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/'
                                   'freshness-guard.sh session-start main'}]}]}},
            indent=2), encoding='utf-8')
        _p, changed = _bs2.ensure_hook_wired(wtmp / 'set',
                                             _bs2.UNIVERSAL_CATALOGUE_HOOK)
        cmds = [e['command'] for g in _json.loads(_p.read_text())['hooks']['SessionStart']
                for e in g['hooks']]
        cases.append(('an unwired set gets the catalogue hook written into its '
                      'settings.json by a TOOL -- no person, no hand edit',
                      changed and any(_bs2.UNIVERSAL_CATALOGUE_HOOK in c
                                      for c in cmds)))
        cases.append(('...placed AFTER the individual-source hook, because the '
                      'first writes the config the second resolves against',
                      cmds.index(next(c for c in cmds
                                      if _bs2.UNIVERSAL_CATALOGUE_HOOK in c))
                      == cmds.index(next(c for c in cmds
                                         if _bs2.INDIVIDUAL_SOURCE_HOOK in c)) + 1))
        before = _p.read_text()
        _p2, again = _bs2.ensure_hook_wired(wtmp / 'set',
                                            _bs2.UNIVERSAL_CATALOGUE_HOOK)
        cases.append(('...and re-running leaves the file byte-identical -- a '
                      'repair that runs every session start must not append '
                      'a duplicate each time',
                      not again and _p2.read_text() == before))
        bad = wtmp / 'broken' / '.claude'
        bad.mkdir(parents=True)
        (bad / 'settings.json').write_text('{not json', encoding='utf-8')
        _p3, ch3 = _bs2.ensure_hook_wired(wtmp / 'broken',
                                          _bs2.UNIVERSAL_CATALOGUE_HOOK)
        cases.append(('a settings.json that does not parse is LEFT ALONE -- '
                      'rewriting one somebody hand-edited and broke would '
                      'destroy their work',
                      not ch3 and _p3.read_text() == '{not json'))
    finally:
        shutil.rmtree(wtmp, ignore_errors=True)

    # A SET'S OWN PRACTICES ARE NEVER DEFERRED INTO ITS OWN SESSION FILE,
    # however the source that names them was resolved. Two clones of one
    # repository is the real case -- an individual source resolves through an
    # absolute path in ~/.config/precedent/config.json, which routinely names
    # a SECOND clone -- and until 2026-09-13 the own-tree test compared paths,
    # so a set saw its own practices as somebody else's tree and rendered them
    # twice: once from the tracked block, once from the session file. Reported
    # by the set it happened in.
    dup = pathlib.Path(tempfile.mkdtemp(prefix='precedent-samerepo-'))
    try:
        a, b = dup / 'a', dup / 'b'
        for d in (a, b):
            d.mkdir()
            subprocess.run(['git', 'init', '-q', str(d)], check=False)
        for d, url in ((a, 'https://github.com/acct/precedent-individual.git'),
                       (b, 'HTTPS://github.com/acct/precedent-individual/')):
            subprocess.run(['git', '-C', str(d), 'remote', 'add', 'origin', url],
                           check=False)
        cases.append(('two clones of one repository read as the SAME repository '
                      '-- a .git suffix, a trailing slash and case are not '
                      'differences',
                      bv._same_repository(a, b)))
        c = dup / 'c'
        c.mkdir()
        subprocess.run(['git', 'init', '-q', str(c)], check=False)
        subprocess.run(['git', '-C', str(c), 'remote', 'add', 'origin',
                        'https://github.com/acct/something-else.git'], check=False)
        cases.append(('...and two clones of DIFFERENT repositories do not -- the '
                      'test must still separate a real other tree',
                      not bv._same_repository(a, c)))
        d_no_remote = dup / 'd'
        d_no_remote.mkdir()
        cases.append(('a directory with no remote falls back to the path test '
                      'rather than matching everything',
                      bv._same_repository(d_no_remote, d_no_remote)
                      and not bv._same_repository(d_no_remote, a)))
        # A git-tracked SUBDIRECTORY with no .git of its own -- what
        # process/upstream/ is in a consumer that vendors this catalogue as
        # plain files rather than a submodule (practice-export-loop). `git -C
        # <subdir> remote get-url origin` does not stop at the subdirectory;
        # it walks up to the ENCLOSING repo and answers with ITS origin, so
        # before the repo-root check the subdir wrongly read as its
        # enclosing repo's own top-level checkout. Reported against a real
        # vendored tree, 2026-09-15.
        e = dup / 'e'
        e.mkdir()
        subprocess.run(['git', 'init', '-q', str(e)], check=False)
        subprocess.run(['git', '-C', str(e), 'remote', 'add', 'origin',
                        'https://github.com/acct/consumer-repo.git'], check=False)
        e_vendored = e / 'process' / 'upstream'
        e_vendored.mkdir(parents=True)
        cases.append(("a git-tracked subdirectory with no .git of its own is "
                      "never mistaken for its enclosing repository's own "
                      "top-level checkout, even though its `origin` resolves "
                      "to the enclosing repo's",
                      not bv._same_repository(e_vendored, e)))
    finally:
        shutil.rmtree(dup, ignore_errors=True)

    # THE SAFETY PROPERTY. Asserted against this repo's real .gitignore and
    # real git, not against a fixture: the whole design rests on this file
    # being uncommittable, and a fixture could pass while the real repo leaks.
    r = subprocess.run(['git', '-C', str(ROOT), 'check-ignore',
                        '.precedent/SESSION_PRACTICES.md'],
                       capture_output=True, text=True)
    cases.append(('.precedent/ is gitignored in THIS repo -- the private text '
                  'cannot reach a commit, which is the only reason loading it '
                  'here is safe at all', r.returncode == 0))
    r = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--error-unmatch',
                        '.precedent/SESSION_PRACTICES.md'],
                       capture_output=True, text=True)
    cases.append(('...and no such file is tracked right now', r.returncode != 0))

    # The pointer a session actually follows must be in the committed block.
    agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    cases.append(('AGENTS.md tells a session the file exists -- a generated file '
                  'nothing points at is one nobody reads',
                  '.precedent/SESSION_PRACTICES.md' in agents))

    # Never fatal: it runs from a session-start hook under `set -e`.
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_session_practices.py'),
                        '--repo', str(tmp / 'gone')], capture_output=True, text=True)
    cases.append(('it exits 0 even pointed at a directory that does not exist -- a '
                  'session that fails to START because an optional practice file '
                  'could not be written is far worse than one missing it',
                  r.returncode == 0))

    # THE INTEGRATION PROPERTY, and the one this nearly got wrong. The
    # tracked loader block now renders every declared source EXCEPT the
    # private levels in a public repo. So this file must carry exactly that
    # complement -- no more (duplicating what the block already has) and no
    # less (the gap reopening in silence). Both sides read
    # build_views.PRIVATE_LEVELS and build_views.repo_is_public, and the
    # pointer in the standing instruction is keyed off the same test: an
    # earlier version keyed it off "was this rendered single-source", which
    # stopped being true the moment a public repo rendered multi-source, and
    # the pointer silently vanished from AGENTS.md.
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as _bv
    cases.append(('this repo declares visibility: public, so its tracked block '
                  'omits the private levels and something else must carry them',
                  _bv.repo_is_public(ROOT)))
    cases.append(('the levels this file carries are exactly the ones the block '
                  'omits -- one definition, so the two cannot disagree about '
                  'which practices a session is otherwise never shown',
                  psp.__dict__.get('bv').PRIVATE_LEVELS is _bv.PRIVATE_LEVELS))
    block_text = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    cases.append(('no private level appears in the committed block',
                  '(team)' not in block_text.split('END GENERATED')[0]
                  and '(individual)' not in block_text.split('END GENERATED')[0]))

    # AND THE REACHABILITY CHECK MUST KNOW IT. Loading them is half the job:
    # if `layered-practice-packs` still reports them unreachable, the gap
    # reads as open, and the next session weighs publishing private text or
    # leaving the rules unloaded against a channel that already exists.
    # Found 2026-09-06 exactly that way -- by testing the claim, not
    # assuming it.
    import tempfile as _tf, shutil as _sh, json as _js
    import precedent_check as _pc
    fx = pathlib.Path(_tf.mkdtemp(prefix='precedent-fifth-'))
    try:
        repo = fx / 'repo'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'tools').mkdir(parents=True)
        (repo / '.claude' / 'hooks').mkdir(parents=True)
        tsrc = fx / 'team' / 'practices'
        tsrc.mkdir(parents=True)
        base = (ROOT / 'practices' / 'verify-postcondition.md').read_text(encoding='utf-8')
        x = re.sub(r'^slug:(\s+)\S+$', r'slug:\g<1>team-unreachable', base, count=1, flags=re.M)
        x = re.sub(r'^gates:.*$', 'gates:       []', x, count=1, flags=re.M)
        x = re.sub(r'^checked_by:.*$', 'checked_by:  null', x, count=1, flags=re.M)
        (tsrc / 'team-unreachable.md').write_text(x, encoding='utf-8')
        (repo / 'AGENTS.md').write_text('# nothing names it\n', encoding='utf-8')
        (repo / 'precedent.json').write_text(_js.dumps({
            'format_version': 1, 'visibility': 'public',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                        {'level': 'team', 'name': 'precedent-team-repo-maintenance',
                         'path': str(fx / 'team')}]}), encoding='utf-8')
        _sh.copy(ROOT / 'tools' / 'precedent_session_practices.py', repo / 'tools')
        hook = repo / '.claude' / 'hooks' / 'session-start.sh'

        def findings():
            # The fixture owns who is working here: nobody. The real person's
            # individual set, and every set it brings, would otherwise add
            # their own findings to the count (2026-10-02).
            saved, saved_cfg = _pc.ROOT, os.environ.get('PRECEDENT_USER_CONFIG')
            _pc.ROOT = repo
            os.environ['PRECEDENT_USER_CONFIG'] = str(fx / 'no-user-config.json')
            try:
                return len(_pc._practice_is_reachable(None) or [])
            finally:
                _pc.ROOT = saved
                if saved_cfg is None:
                    os.environ.pop('PRECEDENT_USER_CONFIG', None)
                else:
                    os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg

        hook.write_text('#!/bin/bash\n# no loader here\n', encoding='utf-8')
        cases.append(('with the session channel NOT wired, a private-level '
                      'practice is still reported unreachable -- the channel is '
                      'never assumed', findings() == 1))
        hook.write_text('#!/bin/bash\npython3 tools/precedent_session_practices.py\n',
                        encoding='utf-8')
        cases.append(('...and once the hook invokes it, the same practice counts '
                      'as reachable, so the gap stops reading as open',
                      findings() == 0))
        hook.write_text('#!/bin/bash\nbash tools/bootstrap.sh\n', encoding='utf-8')
        (repo / 'tools' / 'bootstrap.sh').write_text(
            '#!/bin/bash\n# no loader here either\n', encoding='utf-8')
        cases.append(('a hook that runs tools/bootstrap.sh is not wired when '
                      'bootstrap.sh does not run the tool', findings() == 1))
        (repo / 'tools' / 'bootstrap.sh').write_text(
            '#!/bin/bash\npython3 tools/precedent_session_practices.py\n',
            encoding='utf-8')
        cases.append(('...and is wired once bootstrap.sh runs it -- the shipped '
                      'consumer hook does exactly this, and every fresh install '
                      'read as unwired until 2026-10-05', findings() == 0))
        (repo / 'tools' / 'precedent_session_practices.py').unlink()
        cases.append(('...and removing the tool reopens it, even with the hook '
                      'still calling it -- both halves are required',
                      findings() == 1))
    finally:
        _sh.rmtree(fx, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'the team and individual practices reach a session without reaching a '
          f'commit ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_not_binding_cannot_be_abused():
    """A repo can say "in force at its source, does not bind here" -- and
    cannot use that to quietly switch a rule off.

    THE GAP THIS CLOSES (TODO's `unreachable-practices`, opened by
    spec/PRELAUNCH_AUDIT.md). 43 of 114 practices in force in this repo were
    reachable by no loading channel. Running the source-supplied checks
    against the tree showed the answer is not "turn them all on": some pass,
    some report real findings, and some report things this repo cannot act
    on because the practice is about a DIFFERENT KIND OF REPOSITORY. The
    system had no vocabulary for that, so silence was doing the job, and a
    forgotten rule and a deliberately-inapplicable one looked identical.

    THE RISK, WHICH IS THE WHOLE REASON THIS CHECK EXISTS. An exemption list
    is a mechanism for opting out of rules. Left unguarded it is strictly
    worse than the silence it replaces, because it launders "I did not want
    to" into a recorded decision. So the guards are the feature, and each is
    asserted here with a negative control:

      a reason is mandatory     an exemption nobody argued for is the same
                                silence, with a config entry on top
      blocking cannot be exempt the same rule the resolver already applies
                                to precedence: a blocking practice is
                                exactly the one no downstream repo may
                                switch off
      stale exemptions surface  one naming a slug nothing puts in force is
                                a typo (and the rule it meant to exempt is
                                still unexplained) or outlived its practice
      malformed fails loudly    a list that silently ignores its own bad
                                entries is a way to opt out by typo
    """
    import tempfile, shutil, json as _json
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as pr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-notbinding-'))
    cases = []
    try:
        def cfg(obj):
            (tmp / 'precedent.json').write_text(_json.dumps(obj), encoding='utf-8')

        base = {"format_version": 1,
                "sources": [{"level": "universal", "name": "u", "path": "."}]}

        cfg(base)
        cases.append(('a repo with no `not_binding` key reads as no exemptions',
                      pr.load_not_binding(tmp) == {}))

        cfg({**base, "not_binding": [
            {"slug": "planted-author-rule", "reason": "about a repo one person authors alone"}]})
        cases.append(('a well-formed exemption is read, reason and all',
                      pr.load_not_binding(tmp) ==
                      {"planted-author-rule": "about a repo one person authors alone"}))

        def refuses(obj):
            cfg(obj)
            try:
                pr.load_not_binding(tmp)
                return False
            except pr.NotBindingError:
                return True
            except Exception:
                return False

        cases.append(('an exemption with NO reason is refused -- the guard is '
                      'that opting out is argued, never merely declared',
                      refuses({**base, "not_binding": [{"slug": "x"}]})))
        cases.append(('...and an empty/whitespace reason counts as none',
                      refuses({**base, "not_binding": [{"slug": "x", "reason": "   "}]})))
        cases.append(('an exemption with no slug is refused',
                      refuses({**base, "not_binding": [{"reason": "because"}]})))
        cases.append(('a `not_binding` that is not a list is refused',
                      refuses({**base, "not_binding": {"x": "y"}})))
        cases.append(('a non-object entry is refused',
                      refuses({**base, "not_binding": ["planted-author-rule"]})))

        # Through the REAL check function, with its ROOT pointed at a
        # fixture repo. Driven in-process rather than by subprocess because
        # precedent_check.ROOT comes from `git rev-parse --show-toplevel`,
        # not from an environment variable -- PRECEDENT_CHECK_ROOT steers the
        # source-supplied check SCRIPTS, not this module.
        import precedent_check as pc
        reachable = pc._practice_is_reachable

        def run_check(not_binding, severity='default', slug='fx-unreachable'):
            repo = tmp / 'repo'
            shutil.rmtree(repo, ignore_errors=True)
            (repo / 'practices').mkdir(parents=True)
            src = (ROOT / 'practices' / 'verify-postcondition.md').read_text(encoding='utf-8')
            x = re.sub(r'^slug:(\s+)\S+$', rf'slug:\g<1>{slug}', src, count=1, flags=re.M)
            x = re.sub(r'^severity:(\s+)\S+$', rf'severity:\g<1>{severity}', x, count=1, flags=re.M)
            x = re.sub(r'^occasion:.*$', 'occasion:    null', x, count=1, flags=re.M)
            x = re.sub(r'^gates:.*$', 'gates:       []', x, count=1, flags=re.M)
            x = re.sub(r'^checked_by:.*$', 'checked_by:  null', x, count=1, flags=re.M)
            (repo / 'practices' / f'{slug}.md').write_text(x, encoding='utf-8')
            (repo / 'AGENTS.md').write_text('# nothing names it\n', encoding='utf-8')
            # `name` is fixed by level (spec/SOURCE_NAMING.md) -- the resolver
            # refuses anything else, which this fixture found the hard way.
            (repo / 'precedent.json').write_text(_json.dumps(
                {"format_version": 1,
                 "sources": [{"level": "universal", "name": "precedent", "path": "."}],
                 **({"not_binding": not_binding} if not_binding is not None else {})}),
                encoding='utf-8')
            saved = pc.ROOT
            pc.ROOT = repo
            try:
                return ' | '.join(str(getattr(f, 'detail', f)) for f in (reachable(None) or []))
            finally:
                pc.ROOT = saved

        out = run_check(None)
        cases.append(('an unreachable practice IS reported when nothing exempts it',
                      'fx-unreachable' in out))

        out = run_check([{"slug": "fx-unreachable", "reason": "different kind of repo"}])
        cases.append(('...and stops being reported once exempted, with a reason',
                      'fx-unreachable' not in out))

        out = run_check([{"slug": "fx-unreachable", "reason": "inconvenient"}],
                        severity='blocking')
        cases.append(('a `severity: blocking` practice CANNOT be exempted -- the '
                      'one rule a downstream repo may never switch off',
                      'blocking' in out and 'fx-unreachable' in out))

        out = run_check([{"slug": "no-such-practice-anywhere", "reason": "x"},
                         {"slug": "fx-unreachable", "reason": "different kind of repo"}])
        cases.append(('a STALE exemption naming a slug nothing puts in force is '
                      'reported -- a typo must not silently exempt nothing',
                      'no-such-practice-anywhere' in out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'`not_binding` states what a repo is not bound by, and cannot be '
          f'used to switch a rule off quietly ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_update_vendors_resolves_local_edits():
    """Update Vendors resolves a committed local edit to a vendored engine
    file instead of refusing over it (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md,
    2026-09-29), by comparing BASE (vendored from), LOCAL (committed here)
    and NEW (upstream now). One consumer holds one edited file per rule, so
    one update run shows every rule; separate runs cover a merge whose check
    fails, an uncommitted edit, a refresh that fails after the swap, and a
    journal a killed run left behind.

    Negative control (practice: control-asserts-which-failure), measured
    2026-09-29 against precedent_update.py and checkin.py as they were at
    c1dd37f5: every rule case fails -- the refresh refuses
    ("hand-edited since the last seed/refresh") and no LOCAL EDITS section
    is printed; the refresh-fails case passes there only because nothing was
    ever swapped, and the journal case fails because nothing replays one.

    Rule 2 changed 2026-10-08 (Morgan, strength: decided: "a definite
    preference towards using the upstream wording"): an edit upstream
    changed elsewhere in the file takes upstream's version, shows the rest
    as a diff, and `keep` puts it back with a reason. Negative control,
    measured that day against the code before it: the merged file is kept,
    and the rule 2 cases fail on "its version is taken"."""
    import hashlib
    fx = _LocalEditsFixture('precedent-local-edits-')
    cases = []
    sha = lambda b: hashlib.sha256(b).hexdigest()
    try:
        # --- one run, every rule ---------------------------------------------
        repo = fx.consumer('rules')
        seeded = fx.seeded_from(repo)
        t = repo / 'tools'
        base = {n: (t / n).read_bytes() for n in (
            'precedent_paths.py', 'precedent_show.py', 'precedent_gate.py',
            'build_views.py', 'precedent_resolve.py', 'precedent_branches.py')}
        local = {
            'precedent_paths.py': _insert(base['precedent_paths.py'], '# rule 1: a local fix\n'),
            'precedent_show.py': _insert(base['precedent_show.py'], '# rule 2: a local fix\n'),
            'precedent_gate.py': _replace_line(base['precedent_gate.py'], '# rule 3: the local line\n'),
            'build_views.py': _insert(base['build_views.py'], '# the same fix on both sides\n'),
            'precedent_resolve.py': _insert(base['precedent_resolve.py'], '# kept on purpose\n'),
            'precedent_branches.py': _insert(base['precedent_branches.py'], '# kept, pin now stale\n'),
        }
        new = {
            'precedent_show.py': base['precedent_show.py'] + b'\n# upstream: rule 2\n',
            'precedent_gate.py': _replace_line(base['precedent_gate.py'], '# rule 3: the upstream line\n'),
            'build_views.py': local['build_views.py'],
            'precedent_resolve.py': base['precedent_resolve.py'] + b'\n# upstream: kept\n',
            'precedent_branches.py': base['precedent_branches.py'] + b'\n# upstream: stale\n',
        }
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
        cfg['kept_template_divergences'] = {
            'tools/precedent_resolve.py': {
                'reason': 'this repo resolves sources its own way',
                'template_sha256': sha(new['precedent_resolve.py'])},
            'tools/precedent_branches.py': {
                'reason': 'this repo names its branches its own way',
                'template_sha256': sha(base['precedent_branches.py'])}}
        (repo / 'precedent.json').write_text(json.dumps(cfg) + '\n', encoding='utf-8')
        for n, data in local.items():
            (t / n).write_bytes(data)
        c_local = fx.commit(repo, 'local fixes to received engine files')
        ref = fx.upstream(seeded, {f'tools/{n}': d for n, d in new.items()})
        rc, out = fx.update(repo, ref)
        got = {n: (t / n).read_bytes() for n in local}
        cases.append(('the update resolves every committed edit and does not fail '
                      'on one', rc != 2 and 'hand-edited since the last seed' not in out
                      and 'LOCAL EDITS' in out, failure_detail(out, 2500)))
        cases.append(('rule 1: upstream did not change it -- the local edit stays, '
                      'reported with the send command',
                      got['precedent_paths.py'] == local['precedent_paths.py']
                      and 'tools/precedent_paths.py' in _section(out, 'Still your local edit')
                      and 'precedent_local_edits.py send' in _section(out, 'Still your local edit'),
                      _section(out, 'Still your local edit') or failure_detail(out, 1500)))
        # Rule 2 since 2026-10-08 (Morgan, decided): upstream changed the
        # file, so upstream's version is taken, and what is left of the local
        # edit goes to the session as a judgment -- shown, saved, one command
        # from coming back, never kept or dropped silently.
        pref = _section(out, PREFERRED_GROUP)
        cases.append(('rule 2: upstream changed the file, so its version is '
                      'taken over the rest of the local edit',
                      got['precedent_show.py'] == new['precedent_show.py']
                      and 'tools/precedent_show.py' in pref
                      and 'tools/precedent_show.py' not in _section(out, 'Merged'),
                      pref or failure_detail(out, 1500)))
        cases.append(('...and what it dropped is shown as a diff, with the commit '
                      'holding it and the keep command',
                      '+# rule 2: a local fix' in pref and c_local in pref
                      and 'precedent_local_edits.py keep --repo . --path '
                          'tools/precedent_show.py --object' in pref
                      and 'different and important' in pref, pref or failure_detail(out, 1500)))
        cases.append(('...and the closing report asks for the judgment beside '
                      'the outcome', 'JUDGE:' in out and 'tools/precedent_show.py'
                      in out.split('JUDGE:', 1)[-1].split('\n', 1)[0], failure_detail(out, 1500)))
        oid = re.search(r'--object ([0-9a-f]+)', pref)
        if oid:
            rc_k, out_k = fx.sh(sys.executable, str(ROOT / 'tools' / 'precedent_local_edits.py'),
                                'keep', '--repo', '.', '--path', 'tools/precedent_show.py',
                                '--object', oid.group(1), cwd=repo)
            cases.append(('keep with no reason is refused, and writes nothing',
                          rc_k == 1 and '--why' in out_k
                          and (t / 'precedent_show.py').read_bytes() == new['precedent_show.py'],
                          out_k))
            rc_k, out_k = fx.sh(sys.executable, str(ROOT / 'tools' / 'precedent_local_edits.py'),
                                'keep', '--repo', '.', '--path', 'tools/precedent_show.py',
                                '--object', oid.group(1), '--why', 'a fix upstream lacks',
                                cwd=repo)
            kept = (t / 'precedent_show.py').read_bytes()
            entry = (json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
                     .get('kept_template_divergences') or {}).get('tools/precedent_show.py') or {}
            cases.append(('keep puts the local edit back on top of upstream\'s change, '
                          'and records why, pinned to upstream\'s text',
                          rc_k == 0 and b'# rule 2: a local fix' in kept
                          and b'# upstream: rule 2' in kept
                          and entry.get('reason') == 'a fix upstream lacks'
                          and entry.get('template_sha256') == sha(new['precedent_show.py']),
                          (out_k, entry)))
        else:
            cases.append(('the report names the saved object to keep', False, pref))
        cases.append(('rule 3: a conflict takes upstream\'s version and names the '
                      'commit holding the local one',
                      got['precedent_gate.py'] == new['precedent_gate.py']
                      and 'tools/precedent_gate.py' in _section(out, "Upstream's version taken")
                      and c_local in _section(out, "Upstream's version taken")
                      and 'same lines' in _section(out, "Upstream's version taken"),
                      _section(out, "Upstream's version taken") or failure_detail(out, 1500)))
        cases.append(('upstream already carrying the change: the file matches '
                      'upstream, reported as nothing lost',
                      got['build_views.py'] == new['build_views.py']
                      and 'tools/build_views.py' in _section(out, 'Upstream now carries'),
                      _section(out, 'Upstream now carries') or failure_detail(out, 1500)))
        cases.append(('rule 4: a file kept on purpose is never replaced, and its '
                      'reason is said',
                      got['precedent_resolve.py'] == local['precedent_resolve.py']
                      and 'resolves sources its own way' in _section(out, 'Kept on purpose'),
                      _section(out, 'Kept on purpose') or failure_detail(out, 1500)))
        left = out.split('LEFT FOR YOU', 1)[-1] if 'LEFT FOR YOU' in out else ''
        cases.append(('rule 4 with a stale pin: still never replaced, and left for '
                      'the person with the hash to record',
                      got['precedent_branches.py'] == local['precedent_branches.py']
                      and 'tools/precedent_branches.py' in left
                      and sha(new['precedent_branches.py']) in left, failure_detail(left, 1500)))

        # --- rule 2 whose check fails: every merged file back to NEW ---------
        repo = fx.consumer('failing-check')
        seeded = fx.seeded_from(repo)
        f = repo / 'tools' / 'precedent_show.py'
        b = f.read_bytes()
        f.write_bytes(_insert(b, '# rule 2: a local fix\n'))
        tests = repo / 'tools' / 'checks' / 'tests' / 'run_all.sh'
        tests.parent.mkdir(parents=True, exist_ok=True)
        failing = ('#!/usr/bin/env bash\n'
                   'if grep -q "local fix" tools/precedent_show.py && '
                   'grep -q "upstream: rule 2" tools/precedent_show.py; then\n'
                   '  echo "the merged file breaks a fixture test"; exit 1\nfi\n')
        tests.write_text(failing, encoding='utf-8')
        fx.commit(repo, 'a local fix, and a test the merge will fail')
        up = b + b'\n# upstream: rule 2\n'
        rc, out = fx.update(repo, fx.upstream(seeded, {'tools/precedent_show.py': up}))
        pref = _section(out, PREFERRED_GROUP)
        # The update vendors its own run_all.sh over the fixture's, so the
        # failing test is planted again for the keep that follows.
        tests.write_text(failing, encoding='utf-8')
        oid = re.search(r'--object ([0-9a-f]+)', pref)
        before = (repo / 'precedent.json').read_bytes()
        rc_k, out_k = (fx.sh(sys.executable, str(ROOT / 'tools' / 'precedent_local_edits.py'),
                             'keep', '--repo', '.', '--path', 'tools/precedent_show.py',
                             '--object', oid.group(1), '--why', 'mine', cwd=repo)
                       if oid else (None, pref or out[-1500:]))
        cases.append(('keep whose check fails puts upstream\'s version back, records '
                      'nothing, and names the failed check', f.read_bytes() == up
                      and rc_k == 1 and 'run_all.sh' in out_k and 'not kept' in out_k
                      and (repo / 'precedent.json').read_bytes() == before, out_k))

        # --- an uncommitted edit: nothing written -----------------------------
        repo = fx.consumer('uncommitted')
        seeded = fx.seeded_from(repo)
        f = repo / 'tools' / 'precedent_paths.py'
        edited = _insert(f.read_bytes(), '# not committed\n')
        f.write_bytes(edited)
        manifest = (repo / 'tools' / 'ENGINE_MANIFEST.json').read_bytes()
        rc, out = fx.update(repo, fx.upstream(seeded, {
            'tools/precedent_paths.py': f.read_bytes() + b'\n# upstream\n'}))
        cases.append(('an uncommitted edit stops the update with nothing written',
                      rc == 1 and 'not committed' in out
                      and 'tools/precedent_paths.py' in out.split('LEFT FOR YOU', 1)[-1]
                      and f.read_bytes() == edited
                      and (repo / 'tools' / 'ENGINE_MANIFEST.json').read_bytes() == manifest,
                      failure_detail(out, 1500)))

        # --- the refresh fails after the swap: LOCAL back, byte for byte ------
        repo = fx.consumer('refresh-fails',
                           {'engine_paths': {'README.md': 'tools/precedent_gate.py'}})
        seeded = fx.seeded_from(repo)
        f = repo / 'tools' / 'precedent_show.py'
        edited = _insert(f.read_bytes(), '# a local fix\n')
        f.write_bytes(edited)
        fx.commit(repo, 'a local fix')
        rc, out = fx.update(repo, fx.upstream(seeded, {
            'tools/precedent_show.py': f.read_bytes() + b'\n# upstream\n'}))
        journal = pathlib.Path(fx.git(repo, 'rev-parse', '--absolute-git-dir')) / \
            'precedent-local-edits'
        cases.append(('a refresh that fails after the swap puts the local edit back '
                      'byte for byte, and leaves no journal',
                      rc == 2 and 'this engine already vendors this path' in out
                      and f.read_bytes() == edited and not journal.exists(),
                      failure_detail(out, 1500)))

        # --- a journal a killed run left: replayed first ---------------------
        repo = fx.consumer('killed')
        seeded = fx.seeded_from(repo)
        f = repo / 'tools' / 'precedent_show.py'
        edited = _insert(f.read_bytes(), '# a local fix\n')
        f.write_bytes(edited)
        fx.commit(repo, 'a local fix')
        rc, out = fx.sh(sys.executable, '-c', (
            'import os, pathlib, sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_local_edits as le\n'
            f'repo = pathlib.Path({str(repo)!r})\n'
            'edits, _ = le.engine_edits(repo)\n'
            'le.Swap(repo, edits).__enter__()\n'
            'os._exit(9)\n'), cwd=repo)
        journal = pathlib.Path(fx.git(repo, 'rev-parse', '--absolute-git-dir')) / \
            'precedent-local-edits'
        swapped = f.read_bytes() != edited and journal.is_dir()
        rc, out = fx.update(repo, seeded)
        cases.append(('a journal left by a killed run is replayed first: the local '
                      'edit is back, and said', swapped
                      and 'put back your local tools/precedent_show.py' in out
                      and f.read_bytes() == edited and not journal.exists(),
                      failure_detail(out, 1500)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_rerun_after_failed_takes_its_own_output():
    """A rerun of Update Vendors after a FAILED one recognises what the
    failed run staged as its own output, puts it back and writes it again,
    instead of refusing it as "a vendored file edited here and not
    committed" (2026-10-02: a consumer's run failed its deep check with an
    engine file it had merged with the repo's committed local edit still
    staged, and the rerun the FAILED message asked for stopped on that very
    file). A staged file the person changed after the failure is still
    theirs, and still refused.

    Negative control, measured 2026-10-02 against staging at 1c2403f: the
    rerun stops with "not committed" naming tools/precedent_show.py, so the
    second case fails."""
    fx = _LocalEditsFixture('precedent-update-rerun-')
    cases = []

    def red_update(repo, ref):
        # The real update, with its closing check stubbed red, so the run
        # ends FAILED with its output staged exactly as a red check leaves it.
        return fx.sh(sys.executable, '-c', (
            'import sys\n'
            f'sys.path.insert(0, {str(ROOT / "tools")!r})\n'
            'import precedent_update as pu\n'
            'pu.judged_as_committed = lambda _r, _a: (1, "stubbed red check")\n'
            f'sys.exit(pu.main(["--repo", {str(repo)!r}, "--from-ref", {ref!r}]))\n'),
            cwd=repo)
    def local_fix(repo):
        # Answer the bare fixture's first-run questions, so the run below
        # reaches its check rather than stopping short of it.
        fx.update(repo, fx.seeded_from(repo))
        fx.commit(repo, 'first update')
        f = repo / 'tools' / 'precedent_show.py'
        f.write_bytes(_insert(f.read_bytes(), '# a local fix\n'))
        fx.commit(repo, 'a local fix to a received engine file')
    try:
        for name, touch in (('untouched', False), ('touched', True)):
            # Both cases start from the same consumer, built once and copied
            # (_uv_cached_consumer).
            repo = _uv_cached_consumer(fx, name, 'first-update-local-fix', local_fix)
            seeded = fx.seeded_from(repo)
            f = repo / 'tools' / 'precedent_show.py'
            b = subprocess.run(['git', '-C', str(repo), 'show',
                                'HEAD~1:tools/precedent_show.py'],
                               capture_output=True, env=fx.env).stdout
            if f.read_bytes() != _insert(b, '# a local fix\n'):
                cases.append((f'{name}: the fixture holds the local fix on top of the '
                              'first update', False, ''))
                continue
            ref = fx.upstream(seeded, {'tools/precedent_show.py': b + b'\n# upstream\n'})
            rc, out = red_update(repo, ref)
            # Upstream's version, since 2026-10-08 (rule 2 takes it): still
            # this run's output, and not what HEAD holds.
            merged = f.read_bytes()
            if not touch:
                cases.append(('the first run ends FAILED on its check, with its '
                              'own version of the engine file staged', rc == 2
                              and 'FAILED' in out
                              and merged == b + b'\n# upstream\n'
                              and 'tools/precedent_show.py' in fx.git(
                                  repo, 'diff', '--cached', '--name-only'), failure_detail(out, 1500)))
                rc, out = fx.update(repo, ref)
                cases.append(('the rerun takes that file as its own output and does not '
                              'refuse it', 'not committed' not in out and rc != 2
                              and 'earlier run' in out and f.read_bytes() == merged,
                              failure_detail(out, 1500)))
            else:
                f.write_bytes(merged + b'# the person fixed something here\n')
                rc, out = fx.update(repo, ref)
                cases.append(('a staged file changed after the failure is the person\'s: '
                              'refused, and left as they wrote it',
                              rc == 1 and 'not committed' in out
                              and 'tools/precedent_show.py' in out.split('LEFT FOR YOU', 1)[-1]
                              and f.read_bytes().endswith(b'fixed something here\n'),
                              failure_detail(out, 1500)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_rerun_counts_its_own_staged_output_apart():
    """A rerun of Update Vendors before the commit counts what an earlier
    run staged apart from what was uncommitted before any run.

    THE INCIDENT (2026-10-08, a consuming repository). The second run said
    "116 already uncommitted before it ran, left as they were"; all 116 were
    the first run's own staged output, and git status showed nothing
    unstaged. Planted: a person's own uncommitted note before run 1, then a
    run that stages an engine change and is not committed, then a rerun --
    which must name the earlier run's output as its own and still count the
    note as the person's. A staged file the person then edits is theirs."""
    fx = _LocalEditsFixture('precedent-update-recount-')
    cases = []

    def staged(out):
        return next((l for l in out.splitlines()
                     if l.startswith('precedent_update: staged:')), '')
    try:
        repo = fx.consumer('recount')
        seeded = fx.seeded_from(repo)
        fx.update(repo, seeded)
        fx.commit(repo, 'first update')
        f = repo / 'tools' / 'precedent_show.py'
        ref = fx.upstream(seeded, {'tools/precedent_show.py':
                                   f.read_bytes() + b'\n# upstream\n'})
        (repo / 'notes.md').write_text('# My notes\n', encoding='utf-8')
        rc, out = fx.update(repo, ref)
        first = staged(out)
        cases.append(('run 1 stages the engine change and leaves the note',
                      'tools/precedent_show.py' in fx.git(repo, 'diff', '--cached',
                                                          '--name-only')
                      and '1 already uncommitted' in first, first or failure_detail(out, 1200)))
        rc, out = fx.update(repo, ref)
        second = staged(out)
        cases.append(('the rerun counts run 1\'s staged output as an earlier run\'s, '
                      'and only the note as uncommitted before it ran',
                      'staged by an earlier run of this update' in second
                      and '1 already uncommitted before it ran' in second,
                      second or failure_detail(out, 1200)))
        f.write_bytes(f.read_bytes() + b'# the person changed this\n')
        subprocess.run(['git', '-C', str(repo), 'add', '--', 'tools/precedent_show.py'],
                       capture_output=True)
        import precedent_update as pu
        before = pu.dirty_paths(repo)
        mine = pu.earlier_runs_output(repo, before)
        cases.append(('a staged file the person changed since is not counted as the '
                      'update\'s', 'tools/precedent_show.py' not in mine
                      and 'notes.md' not in mine, sorted(mine)))
    except (OSError, subprocess.CalledProcessError, ImportError, AttributeError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_send_carries_a_local_edit_upstream():
    """tools/precedent_local_edits.py send turns a consumer's committed edit
    to a received engine file into a branch in the owner's clone, merged
    three ways onto the owner's landing branch, scrubbed on both sides, and
    pushed -- never a pull request, never a merge
    (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md, part one, 2026-09-29).

    The owner is a full local clone of this repo whose origin is a bare
    repository in the fixture, so the push leaves nothing on the machine's
    real remotes. Its commits are authored as whoever this checkout's own
    identity resolves to, as a real clone's would be, so its basic tier
    judges the branch as it judges any other push.

    Negative control, measured 2026-09-29: with send's three-way merge
    replaced by a plain copy of the local file, the "not reverted" case
    fails; with consumer_scrub() returning nothing, the private-word case
    pushes the branch and fails (the owner's gate has never heard of the
    word -- which is the whole point of scrubbing on the consumer's side);
    the file did not exist before, so every case fails without it."""
    fx = _LocalEditsFixture('precedent-send-')
    cases = []
    tool = [sys.executable, str(ROOT / 'tools' / 'precedent_local_edits.py')]
    try:
        import precedent_identity
        who = precedent_identity.declared_identity(ROOT) or {}
    except Exception:                           # noqa: BLE001
        who = {}
    ident = {k: v for k, v in (
        ('GIT_AUTHOR_NAME', who.get('name')), ('GIT_AUTHOR_EMAIL', who.get('email')),
        ('GIT_COMMITTER_NAME', who.get('name')), ('GIT_COMMITTER_EMAIL', who.get('email'))) if v}
    try:
        repo = fx.consumer('secret-client-repo')
        seeded = fx.seeded_from(repo)
        f = repo / 'tools' / 'precedent_show.py'
        base = f.read_bytes()

        # The owner: its landing branch has moved on since the consumer
        # vendored, with a change to the same file.
        fx.env.update(ident)
        owner, bare = fx.tmp / 'owner', fx.tmp / 'owner.git'
        # A plain local clone: its objects are hardlinks, never written to in
        # place, so nothing the owner does reaches this checkout; --no-local
        # copied every object of this repository, about 12 seconds of 23.
        fx.sh('git', 'clone', '-q', str(ROOT), str(owner), cwd=fx.tmp)
        landing = fx.sh(sys.executable, 'tools/precedent_branches.py', '--landing',
                        cwd=owner)[1].split()[0]
        fx.sh('git', 'checkout', '-q', '-B', landing, seeded, cwd=owner)
        (owner / 'tools' / 'precedent_show.py').write_bytes(
            base + b'\n# upstream moved on since vendoring\n')
        fx.sh('git', 'commit', '-qam', 'upstream moved on', cwd=owner)
        fx.sh('git', 'clone', '-q', '--bare', str(owner), str(bare), cwd=fx.tmp)
        fx.sh('git', 'remote', 'set-url', 'origin', str(bare), cwd=owner)
        heads_before = fx.sh('git', 'ls-remote', '--heads', str(bare), cwd=fx.tmp)[1]
        # The owner is cloned from this checkout, so it starts on whatever
        # branch this checkout is on -- a local-edit/ branch itself when the
        # check runs on the branch send made (2026-10-04: the deep check of
        # such a branch failed here, counting its own branch as left behind).
        # Only a branch send leaves is a leftover.
        local_before = set(fx.git(owner, 'branch', '--list', 'local-edit/*').split())

        def send(consumer, why):
            return fx.sh(*tool, 'send', '--repo', str(consumer), '--owner-clone',
                         str(owner), '--why', why, cwd=consumer)

        def new_branches():
            now = fx.sh('git', 'ls-remote', '--heads', str(bare), cwd=fx.tmp)[1]
            # Only send's own branches: the owner's basic tier also shares its
            # check receipts on a branch of their own, which is not this.
            return [b for b in (l.split('\t')[1][len('refs/heads/'):]
                                for l in now.splitlines()
                                if l not in heads_before.splitlines())
                    if b.startswith('local-edit/')]

        # No edits: nothing happens, and it says so.
        rc, out = send(repo, 'nothing')
        cases.append(('a consumer with no edits does nothing and says so',
                      rc == 0 and 'nothing to send' in out and not new_branches(),
                      failure_detail(out, 800)))

        # A leak-gate word in the edit: refused before anything is pushed.
        # base64, as this file's other probes are: the harness is itself
        # scanned by the gate, so the word cannot appear in it literally.
        import base64
        word = base64.b64decode('c2hpdA==').decode()
        f.write_bytes(_insert(base, f'# this {word} is a local fix\n'))
        fx.commit(repo, 'a local fix with a word the gate refuses')
        rc, out = send(repo, 'it crashed')
        leftover = set(fx.git(owner, 'branch', '--list', 'local-edit/*').split()) - local_before - {'*'}
        cases.append(('an edit carrying a leak-gate word is refused before '
                      'anything is pushed, and no branch is left behind',
                      rc == 2 and 'REFUSED before anything left this machine' in out
                      and not new_branches() and not leftover, failure_detail(out, 1500)))

        # A word only THIS repo's own scrub list knows -- the owner's gate
        # has never heard of it, so only the consumer's side can stop it.
        (repo / 'process').mkdir(exist_ok=True)
        (repo / 'process' / 'scrub_blocklist.txt').write_text(
            'zanzibar-codename\n', encoding='utf-8')
        f.write_bytes(_insert(base, '# works around the zanzibar-codename import\n'))
        fx.commit(repo, 'a local fix naming a private word')
        rc, out = send(repo, 'it crashed')
        cases.append(('a word only this repo\'s scrub list knows is refused by '
                      'this repo\'s side, before anything is pushed',
                      rc == 2 and 'the scrub on this repo\'s side found' in out
                      and 'zanzibar-codename' in out and not new_branches(),
                      failure_detail(out, 1500)))

        # The real case.
        f.write_bytes(_insert(base, '# a local fix for an empty slug\n'))
        fx.commit(repo, 'fix the show tool on an empty slug')
        rc, out = send(repo, 'precedent_show.py crashed on an empty slug')
        made = new_branches()
        branch = made[0] if len(made) == 1 else ''
        sent = fx.sh('git', '--git-dir', str(bare), 'show',
                     f'{branch}:tools/precedent_show.py', cwd=fx.tmp)[1] if branch else ''
        cases.append(('the branch appears upstream carrying the local change',
                      rc == 0 and branch.startswith('local-edit/')
                      and '# a local fix for an empty slug' in sent,
                      failure_detail(out + '\n' + '\n'.join(made), 2000)))
        cases.append(('...merged onto the landing branch, so upstream\'s change '
                      'since vendoring is kept, not reverted',
                      '# upstream moved on since vendoring' in sent, failure_detail(sent, 400)))
        cases.append(('...on a branch whose name does not carry the consumer\'s '
                      'name', bool(branch) and 'secret' not in branch
                      and 'client' not in branch, branch))
        cases.append(('...with a paste-ready prompt that asks for a test that '
                      'fails without the fix, and no merge or pull request',
                      'Paste into:' in out and 'a test that fails without the fix' in out
                      and 'No pull request' in out, failure_detail(out, 2000)))
        cases.append(('...and the consumer\'s edit left in place, said so',
                      b'# a local fix for an empty slug' in f.read_bytes()
                      and 'Your local edit stays in place' in out, failure_detail(out, 800)))
    finally:
        fx.close()
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_update_vendors_repoints_renamed_shared_sets():
    """Update Vendors repoints a precedent-team-* source to its
    precedent-shared-* name, path and level itself, and says so.

    2026-09-28, a consumer: the refresh listed the renamed sets under Left
    for you, then the view sync refused on the resolver's name check ("calls
    itself precedent-shared-repo-maintenance ... declares it as
    precedent-team-repo-maintenance") and the run stopped. Plants a
    hand-kept precedent.json, a clone at the new path, a clone left only at
    the old path, and the resolver's own refusal text, which a mismatch the
    rename does not cover is still reported by."""
    import tempfile
    pu, pve, pr = _update_tools()
    step = getattr(pu, 'renamed_sources_step', None)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-renamed-sets-'))
    try:
        repo = tmp / 'consumer'
        repo.mkdir()
        (tmp / 'precedent-shared-rm').mkdir()
        (tmp / 'precedent-shared-rm' / 'precedent-source.json').write_text(
            json.dumps({'name': 'precedent-shared-rm', 'level': 'shared'}))
        (tmp / 'precedent-team-ws').mkdir()        # cloned only at the old path
        (tmp / 'precedent-team-own').mkdir()       # still named so by its author
        (tmp / 'precedent-team-own' / 'precedent-source.json').write_text(
            json.dumps({'name': 'precedent-team-own', 'level': 'shared'}))
        text = ('{\n  "_comment": ["kept as written"],\n  "sources": [\n'
                '    {"level": "universal", "name": "precedent", "path": "../BestPractice"},\n'
                '    {"level": "team", "name": "precedent-team-rm",\n'
                '     "path": "../precedent-team-rm"},\n'
                '    {"level": "team", "name": "precedent-team-own", "path": "../precedent-team-own"},\n'
                '    {"level": "team", "name": "precedent-team-ws", "path": "../precedent-team-ws"}\n'
                '  ]\n}\n')
        (repo / 'precedent.json').write_text(text)
        rep = pu.Report()
        rep.leave("precedent.json source 'precedent-team-rm' at ../precedent-team-rm",
                  'names a precedent-team-* set, renamed precedent-shared-*')
        if step is None:
            cases.append(('precedent_update has renamed_sources_step()', False))
        else:
            import io, contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                step(repo, rep, '')
            after = (repo / 'precedent.json').read_text()
            srcs = {s['name']: s for s in json.loads(after)['sources']}
            rm = srcs.get('precedent-shared-rm', {})
            cases.append(('the renamed set gets its new name, path and level',
                          rm.get('path') == '../precedent-shared-rm'
                          and rm.get('level') == 'shared'))
            ws = srcs.get('precedent-shared-ws', {})
            cases.append(('a set cloned only at the old path is renamed, its path kept',
                          ws.get('path') == '../precedent-team-ws'
                          and ws.get('level') == 'shared'))
            cases.append(('NEGATIVE: a set whose own manifest keeps the old name is left alone',
                          srcs.get('precedent-team-own', {}).get('level') == 'team'))
            cases.append(('...and the kept path is left for the person, with where to clone',
                          any('precedent-shared-ws' in w and '../precedent-shared-ws' in y
                              for w, y in rep.left)))
            cases.append(('the stale Left-for-you line about the old name is dropped',
                          not any("'precedent-team-rm'" in w for w, _y in rep.left)))
            cases.append(('the report says what was repointed',
                          any('precedent-team-rm -> precedent-shared-rm' in o
                              for _n, o in rep.steps)))
            cases.append(('a hand-kept file keeps its own layout',
                          '"_comment": ["kept as written"]' in after
                          and '     "path": "../precedent-shared-rm"},' in after))
            cases.append(('the resolver accepts the repointed declaration',
                          pr.check_source_manifest({'path': str(tmp / 'precedent-shared-rm'),
                                                    'name': 'precedent-shared-rm',
                                                    'level': rm.get('level')}) is not None))
        try:
            pr.check_source_manifest({'path': str(tmp / 'precedent-shared-rm'),
                                      'name': 'something-else', 'level': 'shared'})
            said = ''
        except pr.ResolveError as e:
            said = f'precedent_sync_views FAIL: {e}'
        pat = getattr(pu, 'SOURCE_NAME_MISMATCH', None)
        m = pat.search(said) if pat is not None else None
        cases.append(('any other name mismatch is recognised from the sync\'s own words',
                      bool(m) and m.group('declared') == 'something-else'
                      and m.group('own') == 'precedent-shared-rm'))
    except (OSError, ValueError, KeyError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, ok in cases if not ok]
    check('Update Vendors repoints renamed precedent-team-* sources itself',
          not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_source_names_explains_a_proxy_refusal():
    """A hosted session's proxy answers 403 for any repository the session has
    not attached, public ones included. precedent_source_names reports that as
    UNVERIFIED with the reason and the remedy -- attach it, with push access
    for a public repo -- rather than a bare status code a reader takes for
    GitHub's own answer (2026-09-28: all three public shared sets). The API
    call is replaced with the proxy's real refusal; no network is used."""
    import io, urllib.error
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_source_names as psn
    finally:
        sys.path.pop(0)
    body = (b'{"message":"GitHub access to this repository is not enabled for this '
            b'session. Use add_repo to request access."}')
    import urllib.request

    def opener_answering(payload):
        class _Opener:
            def open(self, req, timeout=None):
                raise urllib.error.HTTPError(req.full_url, 403, 'Forbidden', {},
                                             io.BytesIO(payload))
        return lambda *a, **k: _Opener()
    real = urllib.request.build_opener
    try:
        urllib.request.build_opener = opener_answering(body)
        full, why, renamed = psn.api_full_name('o', 'public-set', {})
        urllib.request.build_opener = opener_answering(b'{"message":"rate limited"}')
        _f2, why2, _r2 = psn.api_full_name('o', 'public-set', {})
    finally:
        urllib.request.build_opener = real
    cases = [
        ("the proxy's refusal is explained, not relayed as GitHub's answer",
         full is None and not renamed and 'proxy' in (why or '')),
        ('...and names the remedy: attach it, with push access for a public repo',
         'add_repo' in (why or '') and '"push"' in (why or '')),
        ('any other 403 is still reported in GitHub\'s own words',
         'rate limited' in (why2 or '') and 'proxy' not in (why2 or '')),
    ]
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_show_loads_a_practice_from_a_declared_source():
    """precedent_show.py finds a practice that lives in a shared or an
    individual source the repo declares, labels its level as the gates do,
    and still fails loudly on a slug no source has (2026-09-30: the merge
    gate listed shared and individual practices by name, and this tool
    answered "unknown slug" for each). Fixture sources only, built here;
    never the real private sets."""
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-show-sources-'))
    cases = []
    try:
        def practice(d, slug, rule):
            (d / 'practices').mkdir(parents=True, exist_ok=True)
            (d / 'practices' / f'{slug}.md').write_text(
                f'---\nslug:        {slug}\ntitle:       {slug}\n'
                f'tier:        on-demand\nstatus:      active\n---\n'
                f'## Rule\n{rule}\n', encoding='utf-8')
        repo, shared, ind = tmp / 'repo', tmp / 'zzz-shared', tmp / 'zzz-individual'
        practice(repo, 'zzz-own-rule', 'The repo\'s own rule.')
        practice(shared, 'zzz-shared-rule', 'The shared set says this.')
        practice(ind, 'zzz-individual-rule', 'The individual set says this.')
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': '.'},
                {'level': 'shared', 'name': 'zzz-shared',
                 'path': '../zzz-shared'}]}), encoding='utf-8')
        cfg = tmp / 'user.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'zzz-individual', 'path': str(ind)}}), encoding='utf-8')
        env = dict(os.environ, PRECEDENT_USER_CONFIG=str(cfg))

        def show(*slugs):
            r = subprocess.run([sys.executable,
                                str(ROOT / 'tools' / 'precedent_show.py'),
                                '--repo', str(repo), *slugs],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr
        rc, out = show('zzz-shared-rule', 'zzz-individual-rule')
        cases.append(('a shared and an individual practice both load, each '
                      'labelled with its level',
                      rc == 0 and '### zzz-shared-rule (shared)' in out
                      and 'The shared set says this.' in out
                      and '### zzz-individual-rule (individual)' in out
                      and 'The individual set says this.' in out, failure_detail(out, 500)))
        rc, out = show('zzz-own-rule')
        cases.append(("the repo's own practice still loads unlabelled",
                      rc == 0 and '### zzz-own-rule\n' in out, failure_detail(out, 300)))
        rc, out = show('zzz-no-such-rule')
        cases.append(('a slug no source has still fails, by name',
                      rc != 0 and 'zzz-no-such-rule' in out, failure_detail(out, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, det) for n, ok, det in cases if not ok]
    check('precedent_show.py loads a practice from a declared shared or '
          'individual source', not bad,
          '; '.join(f'{n}: {det!r}' for n, det in bad))


def check_vocabulary_prefers_the_file_you_are_standing_on():
    """A practice defined both in this repo and in a resolved source is read
    from THIS repo's file, and the collision is named either way.

    THE HOUR IT COST, 2026-09-21. A session in a practice source removed a
    `command:` field, ran precedent_vocabulary.py to confirm the row was
    gone, and got the old row back. `cat` showed the edit. `git diff` showed
    the edit. The commit landed. Only the tool disagreed, and the natural
    reading of that is that you edited the wrong field or the frontmatter
    parse is fussy -- neither of which leaves a trace when you test it.

    `collect()` built one dict keyed by slug: local `practices/*.md` first,
    then everything the resolver returned, assigned with a bare
    `found[slug] = ...`. In a CONSUMING repo that precedence is right and
    the slugs never collide. In a repo that IS one of those sources, both
    halves are the same practice from two different checkouts and the local
    edit lost in silence.

    Planted rather than reproduced against the real disk, deliberately: the
    condition is a resolved source whose path is not the repo you are
    standing in, and whether any given container is in that state changes
    with its config. A check that only fires on a machine that happens to be
    misconfigured is a check that reports the weather.

    Four cases, and the two negative controls are the load-bearing ones: a
    slug that exists ONLY in the resolved source still comes from there
    (this is not "ignore the resolver"), and --resolved-view still reaches
    the old behaviour for a caller that wants it.
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vocabulary as pv

    def practice(slug, phrase, title):
        return (f'---\nslug:        {slug}\n'
                f'title:       {title}\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  []\n'
                f'occasion:    "a fixture practice for {slug}"\n'
                'gates:       []\n'
                f'command:     {{"{phrase}": "a fixture command"}}\n'
                f'index_clause: "{phrase} -- a fixture"\n'
                'checked_by:  null\nstatus:      active\nin_force_at: null\n'
                'supersedes:  []\noverrides:   null\nadded:       null\n'
                'approved_by: null\n---\n\n## Rule\nA fixture rule.\n')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vocab-shadow-'))
    try:
        # `other` stands in for the checkout the resolver reaches: same
        # slug, older text. `here` is the repo the tool runs in.
        other = tmp / 'other'
        (other / 'practices').mkdir(parents=True)
        (other / 'practices' / 'fixture-shadowed.md').write_text(
            practice('fixture-shadowed', 'Stale Phrase', 'A shadowed fixture'),
            encoding='utf-8')
        (other / 'practices' / 'fixture-resolved-only.md').write_text(
            practice('fixture-resolved-only', 'Resolved Only Phrase',
                      'Only in the resolved source'), encoding='utf-8')
        (other / 'precedent.json').write_text('{"sources": []}', encoding='utf-8')

        here = tmp / 'here'
        (here / 'practices').mkdir(parents=True)
        # The edit in front of you: same slug, different phrase.
        (here / 'practices' / 'fixture-shadowed.md').write_text(
            practice('fixture-shadowed', 'Live Phrase', 'A shadowed fixture'),
            encoding='utf-8')
        (here / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '../other'}]}),
            encoding='utf-8')

        env_cfg = str(tmp / 'no-such-user-config.json')
        saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = env_cfg
        try:
            entries, notes = pv.collect(here)
            entries_rv, notes_rv = pv.collect(here, resolved_view=True)
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved

        phrases = {e[0] for e in entries}
        phrases_rv = {e[0] for e in entries_rv}
        levels = {e[0]: (e[3], e[4]) for e in entries}

        cases = [
            ('the file you are standing on wins over a resolved copy of the '
             'same slug',
             'Live Phrase' in phrases and 'Stale Phrase' not in phrases,
             f'{sorted(phrases)}'),
            ('and the collision is NAMED, with both paths and the winner -- '
             'the silence was the whole defect',
             any('fixture-shadowed' in n and str(here) in n
                 and str(other) in n for n in notes), f'{notes}'),
            ('the local file keeps the RESOLVED label, since a local read '
             'cannot know which level it is standing in',
             levels.get('Live Phrase') == ('universal', 'precedent'),
             f'{levels.get("Live Phrase")}'),
            ('negative control: a slug only the resolver has still comes '
             'from there -- this is not "ignore the resolver"',
             'Resolved Only Phrase' in phrases, f'{sorted(phrases)}'),
            ('negative control: --resolved-view still reaches the old '
             'precedence for a caller that wants it',
             'Stale Phrase' in phrases_rv and 'Live Phrase' not in phrases_rv,
             f'{sorted(phrases_rv)}'),
            ('...and names the collision there too, pointing the other way',
             any('fixture-shadowed' in n for n in notes_rv), f'{notes_rv}'),
        ]
        ok = all(passed for _, passed, _ in cases)
        for name, passed, detail in cases:
            if not passed:
                print(f"  vocabulary precedence did NOT behave as stated: "
                      f"{name} [{detail}]")
        check(f'precedent_vocabulary reads the file you are standing on, and '
              f'names the collision ({len(cases)} stated cases)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_vocabulary_moves_a_word_to_our_language():
    """A `command:` phrase that is also a word in tools/our_language.json
    prints under "Our language", not among the commands, and the word list
    is read from that one registry (spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md
    step 2).

    "Primary branch" and "Tier branch" name things, not actions -- Morgan,
    2026-09-27 and 2026-09-28, asked for both to sit with the words. The
    negative control is the load-bearing case: an ordinary command in the
    same fixture must still be listed, or the filter is just dropping rows.
    """
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vocabulary as pv
    import our_language as ol

    def practice(slug, phrase):
        return (f'---\nslug:        {slug}\n'
                f'title:       A fixture for {slug}\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  []\n'
                f'occasion:    "a fixture practice for {slug}"\n'
                'gates:       []\n'
                f'command:     {{"{phrase}": "a fixture gloss"}}\n'
                f'index_clause: "{phrase} -- a fixture"\n'
                'checked_by:  null\nstatus:      active\nin_force_at: null\n'
                'supersedes:  []\noverrides:   null\nadded:       null\n'
                'approved_by: null\n---\n\n## Rule\nA fixture rule.\n')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vocab-words-'))
    try:
        (tmp / 'practices').mkdir(parents=True)
        (tmp / 'practices' / 'fixture-word.md').write_text(
            practice('fixture-word', 'Primary branch'), encoding='utf-8')
        (tmp / 'practices' / 'fixture-command.md').write_text(
            practice('fixture-command', 'Fixture Command'), encoding='utf-8')
        (tmp / 'precedent.json').write_text('{"sources": []}', encoding='utf-8')
        saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-such-config.json')
        try:
            entries, _notes = pv.collect(tmp)
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved
        phrases = {e[0] for e in entries}
        word_list, word_note = pv.words()
        names = {w.lower() for w, _ in word_list}

        dup = tmp / 'dup.json'
        dup.write_text(json.dumps({'words': [
            {'word': 'x', 'meaning': 'one'}, {'word': 'X', 'meaning': 'two'}]}),
            encoding='utf-8')
        try:
            ol.load(dup)
            dup_refused = False
        except SystemExit:
            dup_refused = True

        cases = [
            ('a command phrase that is a word leaves the command list',
             'Primary branch' not in phrases, f'{sorted(phrases)}'),
            ('negative control: an ordinary command in the same fixture is '
             'still listed', 'Fixture Command' in phrases, f'{sorted(phrases)}'),
            ('the word list reads from the registry, with no error note',
             'primary branch' in names and word_note is None,
             f'{sorted(names)} {word_note}'),
            ('a word listed twice is refused rather than rendered twice',
             dup_refused, ''),
        ]
        ok = all(passed for _, passed, _ in cases)
        for name, passed, detail in cases:
            if not passed:
                print(f"  vocabulary word list did NOT behave as stated: "
                      f"{name} [{detail}]")
        check(f'precedent_vocabulary prints words under Our language, not as '
              f'commands ({len(cases)} stated cases)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_loader_tools_are_repo_relocatable():
    """precedent_show.py, precedent_paths.py, precedent_gate.py and
    build_views.py used to compute their working root as `pathlib.Path(
    __file__).resolve().parents[1]` -- "whatever is two folders up from my
    own file" -- which is only correct when the script sits at exactly
    <repo>/tools/whatever.py. precedent_sync_views.py's own docstring
    already named this trap for anyone tempted to run these from inside a
    vendored process/upstream/tools/ mirror instead. Fixed to take --repo,
    keeping two notions of "root" apart that the old code conflated:
    where to find THIS SCRIPT's own sibling modules to import (tied to the
    script's own file location, never to --repo) versus which repo's
    content (practices/, AGENTS.md, ...) to actually operate on (--repo,
    defaulting to today's behavior when omitted). Each half gets its own
    case below, for every one of the four tools, rather than trusting that
    fixing one half didn't quietly break the other: running the real,
    in-place script from a cwd that is neither the repo root nor the
    script's own directory (sibling imports must still resolve), and
    running it with --repo pointed at a small fixture repo whose content
    exists nowhere else (the named repo's content must actually be what
    comes back, not a silent fallback to this repo's own)."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-relocation-'))
    elsewhere = pathlib.Path(tempfile.mkdtemp(prefix='precedent-elsewhere-cwd-'))
    cases = []
    try:
        fixture = tmp / 'fixture'
        (fixture / 'practices').mkdir(parents=True)
        (fixture / 'practices' / 'fixture-only-slug.md').write_text(
            '---\nslug: fixture-only-slug\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["fixture-only/**"]\n'
            'occasion: "testing --repo relocation"\ngates: ["merge"]\n'
            # This fixture asserts the slug lands in the rendered block, so it
            # must declare its index line rather than inherit one: it carries a
            # real glob AND a gate, which is exactly the shape build_views now
            # omits from the occasion index (practice: fixture-owns-its-state).
            'index_required: true\n'
            'index_clause: "x"\nchecked_by: null\ndefines: []\nstatus: active\n'
            'supersedes: []\noverrides: null\nadded: 2026-09-05\n'
            'approved_by: "harness, 2026-09-05"\nsource_practice_number: null\n'
            '---\n## Rule\nA fixture-only rule text, present in no other repo.\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')
        (fixture / 'tools').mkdir(parents=True)
        (fixture / 'tools' / 'routing_scope.json').write_text(
            json.dumps({'_note': [], 'practices': {}, 'gates': {'merge': 'merging a branch'}}),
            encoding='utf-8')
        (fixture / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        fixture_slug = 'fixture-only-slug'
        real_slug = sorted(PRACTICES_DIR.glob('*.md'))[0].stem
        original_agents_text = AGENTS_MD.read_text(encoding='utf-8')

        def run(tool, *args, cwd=None):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / tool), *args],
                               capture_output=True, text=True,
                               cwd=str(cwd) if cwd else None)
            return r.returncode, r.stdout + r.stderr

        # --- a different cwd, no --repo: sibling imports must still resolve,
        # and the unchanged default must still be THIS repo's own content --
        rc, out = run('precedent_show.py', real_slug, cwd=elsewhere)
        cases.append(("precedent_show.py from a different cwd, no --repo, resolves its "
                      "sibling import and shows THIS repo's own practice",
                      rc == 0 and f'### {real_slug}' in out, out[:200] if rc else ''))

        rc, out = run('precedent_paths.py', '--matches-only', 'AGENTS.md', cwd=elsewhere)
        cases.append(('precedent_paths.py from a different cwd, no --repo, resolves',
                      rc == 0, out[:200] if rc else ''))

        rc, out = run('precedent_gate.py', '--list', cwd=elsewhere)
        cases.append(('precedent_gate.py from a different cwd, no --repo, resolves',
                      rc == 0 and bool(out.strip()), out[:200] if rc else ''))

        rc, out = run('build_views.py', '--check', '--agents-only', cwd=elsewhere)
        cases.append(('build_views.py from a different cwd, no --repo, still checks '
                      'THIS repo unchanged', rc == 0, out[:200] if rc else ''))

        # --- --repo pointed at the fixture: each tool must read the NAMED
        # repo's content, not silently fall back to this repo's own --------
        rc, out = run('precedent_show.py', fixture_slug, '--repo', str(fixture))
        cases.append(("precedent_show.py --repo reads the named repo's own practice",
                      rc == 0 and 'fixture-only rule text' in out, out[:200]))

        rc, out = run('precedent_show.py', real_slug, '--repo', str(fixture))
        cases.append(("precedent_show.py --repo does NOT fall back to this repo's own practice",
                      rc != 0, '' if rc != 0 else out[:200]))

        rc, out = run('precedent_paths.py', '--repo', str(fixture), '--matches-only',
                      'fixture-only/thing.txt')
        cases.append(("precedent_paths.py --repo matches the named repo's own applies_to glob",
                      rc == 0 and fixture_slug in out, out[:200]))

        rc, out = run('precedent_gate.py', '--repo', str(fixture), 'merge')
        cases.append(("precedent_gate.py --repo loads the named repo's own gate-registered practice",
                      rc == 0 and fixture_slug in out, out[:200]))

        rc, out = run('build_views.py', '--repo', str(fixture), '--agents-only')
        fixture_agents_text = (fixture / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(("build_views.py --repo regenerates the named repo's own AGENTS.md",
                      rc == 0 and fixture_slug in fixture_agents_text, out[:200]))
        cases.append(("build_views.py --repo left THIS repo's own AGENTS.md untouched",
                      AGENTS_MD.read_text(encoding='utf-8') == original_agents_text))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(elsewhere, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'the four file-location-dependent loader tools take --repo '
          f'(precedent_show.py, precedent_paths.py, precedent_gate.py, build_views.py; '
          f'{len(cases)} stated cases: sibling imports resolve from a different cwd with '
          f"no --repo, and --repo relocates content without touching this repo's own)",
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_brought_set_ships_reach_the_session_untracked():
    """practice: practice-carries-its-files -- a set the person brings ships
    its files and its hook too, without touching the tracked tree.

    THE INCIDENT (2026-10-13): a consuming repository got the writing set
    only through the person's individual set (`brings`). The sync delivers a
    declared set's `ships:` and `hooks:`; a brought set is deferred to the
    untracked session file, so create-word-doc told every session to run a
    tools/create_word_doc.py that was not there, and dated-download-names'
    hook had no tools/dated_name.py to run.

    Planted end to end, both worlds (practice: checks-plant-their-state):
    a git consumer that declares only a universal set, a person whose
    individual set brings a set that ships tools/helper.py with a
    PreToolUse hook, and precedent_session_practices.py run as a session
    start runs it. Each case states which outcome it asserts (practice:
    control-asserts-which-failure)."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_materialize as pm
        import precedent_hooks as ph
        import precedent_check as pc
        import build_views as bv
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-brought-ships-'))
    cases = []

    def practice(root, slug, ships=None, hooks=None):
        p = root / 'practices' / f'{slug}.md'
        p.parent.mkdir(parents=True, exist_ok=True)
        extra = (f'ships: {json.dumps(ships)}\n' if ships is not None else '')
        extra += (f'hooks: {json.dumps(hooks)}\n' if hooks is not None else '')
        p.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
            f'gates: []\nindex_clause: "x"\nchecked_by: null\n'
            f'{extra}defines: []\nstatus: active\nsupersedes: []\n'
            f'overrides: null\nadded: 2026-10-13\n'
            f'approved_by: "harness, 2026-10-13"\n---\n## Rule\nx\n\n'
            f'## Why\nx\n', encoding='utf-8')

    genv = {k: v for k, v in os.environ.items()
            if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
    genv.update(HOME=str(tmp / 'home'), GIT_AUTHOR_NAME='T',
                GIT_AUTHOR_EMAIL='t@example.com', GIT_COMMITTER_NAME='T',
                GIT_COMMITTER_EMAIL='t@example.com',
                GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1',
                PRECEDENT_USER_CONFIG=str(tmp / 'user-config.json'))

    def git(*args):
        return subprocess.run(['git', '-C', str(consumer), *args],
                              capture_output=True, text=True, env=genv)

    def session_start():
        r = subprocess.run([sys.executable,
                            str(ROOT / 'tools' / 'precedent_session_practices.py'),
                            '--repo', str(consumer), '--quiet'],
                           capture_output=True, text=True, env=genv)
        return r.returncode, r.stdout + r.stderr

    def status():
        return git('status', '--porcelain', '--untracked-files=all').stdout

    def hooks_for(tool):
        return [label for label, _a, _t in
                ph.entries_for('PreToolUse', tool, root=consumer, engine={})]

    hook = [{'event': 'PreToolUse', 'matcher': 'SendUserFile',
             'run': 'tools/helper.py', 'args': ['--hook']}]
    command = 'python3 $CLAUDE_PROJECT_DIR/tools/helper.py --hook'
    try:
        (tmp / 'home').mkdir()
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        uni, ind, brought = tmp / 'universal', tmp / 'mine', tmp / 'brought-set'
        consumer = tmp / 'consumer'
        practice(uni, 'uni-fixture')
        practice(ind, 'mine-fixture')
        (ind / 'precedent-source.json').write_text(json.dumps({
            'name': 'mine', 'level': 'individual', 'brings': [
                {'name': 'brought-set',
                 'repo_url': 'https://github.com/example/brought-set'}]}),
            encoding='utf-8')
        practice(brought, 'helper-fixture', ships=['tools/helper.py'], hooks=hook)
        (brought / 'precedent-source.json').write_text(json.dumps(
            {'name': 'brought-set', 'level': 'shared'}), encoding='utf-8')
        (brought / 'tools').mkdir()
        src = brought / 'tools' / 'helper.py'
        src.write_text('print("v1")\n', encoding='utf-8')
        os.chmod(src, 0o755)
        (tmp / 'user-config.json').write_text(json.dumps({
            'format_version': 1,
            'individual': {'name': 'mine', 'path': str(ind)}}), encoding='utf-8')
        (consumer / '.claude').mkdir(parents=True)
        (consumer / '.claude' / 'settings.json').write_text(
            '{"hooks": {}}\n', encoding='utf-8')
        (consumer / '.gitignore').write_text('.precedent/\n', encoding='utf-8')
        (consumer / 'AGENTS.md').write_text(
            '# Fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        def config(extra=None):
            d = {'visibility': 'private', 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(uni)}]}
            d.update(extra or {})
            (consumer / 'precedent.json').write_text(json.dumps(d),
                                                     encoding='utf-8')
        config()
        git('init', '-q')
        git('add', '-A')
        git('commit', '-qm', 'base')
        delivered = consumer / 'tools' / 'helper.py'

        # Control: before the change, the brought set's file never arrived.
        cases.append(('control: nothing is delivered before a session starts',
                      not delivered.exists()))
        rc, out = session_start()
        cases.append(('1. a session start delivers the brought set\'s file to '
                      'the path its practice names, executable',
                      rc == 0 and delivered.is_file()
                      and os.access(delivered, os.X_OK), failure_detail(out, 400)))
        cases.append(('2. ...and the tracked tree does not change: git sees '
                      'nothing new', status() == '', status()))
        excl = pathlib.Path(git('rev-parse', '--git-path', 'info/exclude')
                            .stdout.strip())
        excl = excl if excl.is_absolute() else consumer / excl
        cases.append(('2. ...because this clone\'s own info/exclude lists it, '
                      'not the tracked .gitignore',
                      excl.is_file() and '/tools/helper.py'
                      in excl.read_text(encoding='utf-8')
                      and 'helper' not in (consumer / '.gitignore')
                      .read_text(encoding='utf-8')))
        (consumer / 'tools' / 'own.py').write_text('print(0)\n', encoding='utf-8')
        cases.append(('2. ...and what describes or judges the repository\'s '
                      'tools/ (MAP.md, the code checks) leaves it out, and '
                      'keeps the repository\'s own script',
                      [p.name for p in pc._tools_py(consumer / 'tools')]
                      == ['own.py']
                      and bv.session_shipped(consumer) == {'tools/helper.py'}))
        (consumer / 'tools' / 'own.py').unlink()
        cases.append(('3. its hook is listed untracked and the hook runner '
                      'runs it for the tool it names',
                      command in hooks_for('SendUserFile'),
                      repr(hooks_for('SendUserFile'))))
        cases.append(('3. ...and stays quiet for any other tool',
                      command not in hooks_for('Bash')))
        delivered.unlink()
        r = subprocess.run([sys.executable,
                            str(ROOT / 'tools' / 'precedent_sync_views.py'),
                            '--repo', str(consumer)],
                           capture_output=True, text=True, env=genv)
        cases.append(('3. a sync delivers it too, as a session start would',
                      r.returncode == 0 and delivered.is_file(),
                      failure_detail(r.stdout + r.stderr, 400)))
        git('add', '-A')
        git('commit', '-qm', 'synced')
        rc, out = session_start()
        cases.append(('4. a second session start is quiet: nothing to deliver',
                      rc == 0 and 'delivered' not in out, failure_detail(out, 300)))
        src.write_text('print("v2")\n', encoding='utf-8')
        session_start()
        cases.append(('5. a change in the set reaches the next session',
                      'v2' in delivered.read_text(encoding='utf-8')))
        delivered.write_text('print("mine")\n', encoding='utf-8')
        rc, out = session_start()
        cases.append(('6. a copy edited since is left as it is, and named',
                      'mine' in delivered.read_text(encoding='utf-8')
                      and 'left as they are' in out and 'tools/helper.py' in out,
                      failure_detail(out, 300)))
        delivered.unlink()
        session_start()
        config({'declined_ships': {'tools/helper.py': 'we never use it'}})
        rc, out = session_start()
        cases.append(('7. a file the repository declines is not delivered, and '
                      'the unchanged copy goes with its hook',
                      not delivered.exists()
                      and command not in hooks_for('SendUserFile'), failure_detail(out, 300)))
        config()
        session_start()
        practice(brought, 'helper-fixture', ships=[])
        rc, out = session_start()
        cases.append(('8. a file no practice ships any more is removed while '
                      'unchanged, and leaves info/exclude',
                      not delivered.exists() and 'removed tools/helper.py' in out
                      and '/tools/helper.py' not in excl.read_text(encoding='utf-8'),
                      failure_detail(out, 300)))
        practice(brought, 'helper-fixture', ships=['tools/helper.py'], hooks=hook)
        session_start()
        pm.release_session_ships(consumer, ['tools/helper.py'])
        cases.append(('9. once the tracked sync ships the same file it is '
                      'released: git sees it, to commit with the sync',
                      '?? tools/helper.py' in status(), status()))
        git('add', '-A')
        git('commit', '-qm', 'the repository keeps its own helper')
        delivered.write_text('print("tracked")\n', encoding='utf-8')
        git('commit', '-qam', 'its own version')
        rc, out = session_start()
        cases.append(('10. a file git tracks is never overwritten or removed',
                      'tracked' in delivered.read_text(encoding='utf-8')
                      and status() == '', status()))
    except (OSError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a brought set\'s `ships:` files and hooks reach the session, '
          f'untracked ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_show_flags_unreachable_materialized_source():
    """practices/verify-postcondition.md, applied to the READ side of the
    gap practices/session-bootstrap.md's Story records on the write side.
    A materialized practices/<slug>.md (tools/precedent_materialize.py's
    output, in a consumer repo resolving universal/team/individual/
    repo-local together) is whatever was on disk at the last successful
    materialize() run -- precedent_show.py reading it back proves nothing
    about whether the source that produced it is reachable THIS session.
    Before this, a session could get a clean, confident-looking Rule
    printout from a source that had silently dropped off, with nothing to
    tell that apart from a source genuinely still live -- exactly the
    false-confidence case the self-heal fix (tools/precedent_resolve.py)
    makes MORE likely to occur unnoticed, not less: a source can now fail
    to resolve in one particular session while a materialized tree from an
    earlier, working session still reads back clean.

    Six stated cases: a real individual source materialized and read while
    reachable (silent, no note); the same slug read again after that
    source's directory is removed (the note fires, naming the level and
    the materialize timestamp); a universal-sourced slug in the SAME
    materialized tree, whose source never leaves (stays silent throughout
    -- the check is source-specific, not a blanket flag on every slug once
    anything is missing); restoring the source and re-reading (silent
    again -- not sticky, re-checked every call); a plain SOURCE repo (this
    one) with no MANIFEST.json at all (never adds a note, regardless of
    slug); and multiple slugs in one call sourced differently (each gets
    its own independent verdict, matching precedent_show.py's own
    per-slug concatenation).

    EXTENDED 2026-09-06 (closed and pruned from TODO.md; was the `gate-and-paths-unreachable-source` item) to cover
    precedent_gate.py and precedent_paths.py too -- both read
    practices/*.md directly, the same way precedent_show.py itself used
    to, so the note above never reached a practice loaded through the
    gate-triggered or path-triggered channel. Closed by having both
    modules `import precedent_show as ps` and call its two helpers
    directly, NOT by a subprocess call to precedent_show.py (would mean
    re-parsing its own "### slug\\n<body>" stdout format back into
    structured data purely to recover a note this file can already print
    itself) and NOT by a second, copy-pasted implementation
    (engine-plus-host-shims: one mechanism, shared by import, the same
    discipline all three files already use for split_practices.py). Two
    more stated cases below reuse the same indiv/uni fixture with one
    added practice (gated + a narrow applies_to, so both channels can
    actually reach it), checked reachable and unreachable exactly like
    the show() cases above."""
    import shutil, subprocess, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-show-reachability-'))
    cases = []
    try:
        def write_practice(path, slug, rule, applies_to='["**"]', gates='[]'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
                f'severity: default\napplies_to: {applies_to}\noccasion: "testing"\n'
                f'gates: {gates}\nindex_clause: "a harness fixture"\nchecked_by: null\n'
                f'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
                f'added: null\napproved_by: "harness"\n---\n\n## Rule\n{rule}\n\n'
                f'## Detail\n\n## Why\n\n## Story\n\n## Install\n', encoding='utf-8')

        indiv = tmp / 'indiv-source'
        write_practice(indiv / 'practices' / 'show-fixture-individual.md',
                       'show-fixture-individual', 'The individual fixture Rule.')
        # Gated + narrow applies_to, so the SAME materialized fixture also
        # exercises precedent_gate.py and precedent_paths.py below -- both
        # read practices/*.md directly, same as precedent_show.py, and
        # the `gate-and-paths-unreachable-source` item (closed, pruned from TODO.md) named them as needing the identical reachability note.
        write_practice(indiv / 'practices' / 'show-fixture-individual-routed.md',
                       'show-fixture-individual-routed', 'The routed individual fixture Rule.',
                       applies_to='["fixture-only/*.md"]', gates='["push"]')
        # Whose set it is (2026-10-19): a saved copy loads for its owner
        # only, so every read below runs as the owner's session.
        (indiv / 'identity.json').write_text(json.dumps(
            {'name': 'Fx Owner', 'email': 'fx@example.com', 'github': 'fx-owner'}),
            encoding='utf-8')
        owner_env = {**os.environ, 'PRECEDENT_GITHUB_USER': 'fx-owner'}
        uni = tmp / 'uni-source'
        write_practice(uni / 'practices' / 'show-fixture-universal.md',
                       'show-fixture-universal', 'The universal fixture Rule.')

        consumer = tmp / 'consumer'
        (consumer).mkdir()
        # Private: run directly, materialize refuses individual text in a
        # public (or undeclared) repo since 2026-10-17.
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)}]
        }), encoding='utf-8')
        user_config = tmp / 'user-config.json'
        user_config.write_text(json.dumps({
            'individual': {'name': 'precedent-individual', 'path': str(indiv)},
        }), encoding='utf-8')

        materialize_tool = str(ROOT / 'tools' / 'precedent_materialize.py')
        show_tool = str(ROOT / 'tools' / 'precedent_show.py')
        gate_tool = str(ROOT / 'tools' / 'precedent_gate.py')
        paths_tool = str(ROOT / 'tools' / 'precedent_paths.py')

        def materialize():
            r = subprocess.run([sys.executable, materialize_tool, '--out', str(consumer),
                               '--repo', str(consumer), '--user-config', str(user_config)],
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        def show(*slugs):
            r = subprocess.run([sys.executable, show_tool, *slugs, '--repo', str(consumer)],
                               capture_output=True, text=True, env=owner_env)
            return r.returncode, r.stdout + r.stderr

        def gate(name):
            r = subprocess.run([sys.executable, gate_tool, name, '--repo', str(consumer)],
                               capture_output=True, text=True, env=owner_env)
            return r.returncode, r.stdout + r.stderr

        def paths(*p):
            r = subprocess.run([sys.executable, paths_tool, *p, '--repo', str(consumer)],
                               capture_output=True, text=True, env=owner_env)
            return r.returncode, r.stdout + r.stderr

        rc, out = materialize()
        cases.append(('the two-source fixture materializes cleanly', rc == 0, out))

        rc, out = show('show-fixture-individual')
        cases.append(('reachable: an individual-sourced slug shows no note',
                      rc == 0 and 'NOT reachable' not in out
                      and 'The individual fixture Rule.' in out, out))

        rc, out = show('show-fixture-universal')
        cases.append(('a universal-sourced slug in the same materialized tree '
                      'shows no note either', rc == 0 and 'NOT reachable' not in out, out))

        rc, out = gate('push')
        cases.append(('reachable: precedent_gate.py shows no note for the '
                      'gated individual-sourced slug either',
                      rc == 0 and 'NOT reachable' not in out
                      and 'show-fixture-individual-routed' in out, out))

        rc, out = paths('fixture-only/x.md')
        cases.append(('reachable: precedent_paths.py shows no note for the '
                      'same slug matched by path',
                      rc == 0 and 'NOT reachable' not in out
                      and 'show-fixture-individual-routed' in out, out))

        shutil.move(str(indiv), str(tmp / 'indiv-source-hidden'))
        rc, out = show('show-fixture-individual')
        cases.append(('unreachable: the same individual-sourced slug now carries '
                      'a note naming its level',
                      rc == 0 and 'NOT reachable this session' in out
                      and '(source: individual,' in out, out))

        rc, out = show('show-fixture-universal')
        cases.append(('the universal-sourced slug is unaffected by the '
                      'individual source going missing -- the check is per-slug, '
                      'not a blanket flag', rc == 0 and 'NOT reachable' not in out, out))

        rc, out = gate('push')
        cases.append(('unreachable: precedent_gate.py now carries the note for '
                      'the gated individual-sourced slug (the `gate-and-paths-unreachable-source` item, closed and pruned from TODO.md)',
                      rc == 0 and 'NOT reachable this session' in out
                      and '(source: individual,' in out, out))

        rc, out = paths('fixture-only/x.md')
        cases.append(('unreachable: precedent_paths.py now carries the note for '
                      'the same slug matched by path (the `gate-and-paths-unreachable-source` item, closed and pruned from TODO.md)',
                      rc == 0 and 'NOT reachable this session' in out
                      and '(source: individual,' in out, out))

        rc, out = show('show-fixture-individual', 'show-fixture-universal')
        cases.append(('mixed in one call: each slug gets its own independent '
                      'verdict', rc == 0 and out.count('NOT reachable') == 1
                      and '### show-fixture-individual' in out
                      and '### show-fixture-universal' in out, out))

        shutil.move(str(tmp / 'indiv-source-hidden'), str(indiv))
        rc, out = show('show-fixture-individual')
        cases.append(('restored: the note is re-checked every call, not sticky',
                      rc == 0 and 'NOT reachable' not in out, out))

        # A plain SOURCE repo (no MANIFEST.json at all) never adds a note,
        # for any slug -- this repo's own tree is exactly that fixture.
        r = subprocess.run([sys.executable, show_tool, 'environment-gotchas'],
                           capture_output=True, text=True, cwd=str(ROOT))
        cases.append(('a plain source repo with no MANIFEST.json never adds a note',
                      r.returncode == 0 and 'NOT reachable' not in r.stdout, r.stdout + r.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'precedent_show.py/precedent_gate.py/precedent_paths.py all flag a '
          f'materialized slug whose declared source is not reachable this session '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_commit_backstop_points_shipped_links_at_github():
    """The commit backstop repoints a shipped Markdown file's link to a file
    the catalogue copy leaves out at GitHub, as the file is committed, so the
    file shipped is the file here, byte for byte (Morgan, 2026-10-19: "go,
    build it and book it").

    Two gotchas in one day linked ../tools/ files no consumer has and turned
    main red; rewriting in the copy instead would have made every copied
    file differ from upstream's text, and Update Vendors would call each a
    consumer's edit. Cases: the tool link moves and keeps its anchor while a
    practice link stays relative, and the result is staged; a file the copy
    does not carry is left alone; a file with unstaged changes is left
    alone and said; and a repository that does not ship the copy is never
    touched."""
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_regenerate as pr
    name = 'the commit backstop points a shipped link at GitHub'
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    for k in pr.HOOK_GIT_ENV:
        env.pop(k, None)
    link = ('See [the tool](../tools/zz_tool.py#L3) and '
            '[a practice](../practices/zz-rule.md).\n')
    with tempfile.TemporaryDirectory() as td:
        def repo_with(tag, engine_manifest=False):
            r = pathlib.Path(td) / tag
            for rel, text in {'tools/verify_harness.py': '', 'tools/zz_tool.py': '',
                              'practices/zz-rule.md': '## Rule\nA rule.\n',
                              'precedent.json': '{"base_branch": "staging"}\n',
                              'gotchas/gotcha-zz.md': 'x\n',
                              'spec/ZZ.md': 'x\n'}.items():
                (r / rel).parent.mkdir(parents=True, exist_ok=True)
                (r / rel).write_text(text, encoding='utf-8')
            if engine_manifest:
                (r / 'tools' / 'ENGINE_MANIFEST.json').write_text('{}', encoding='utf-8')
            g = lambda *a: subprocess.run(['git', '-C', str(r), '-c',
                                           'core.hooksPath=/dev/null', *a],
                                          capture_output=True, text=True, env=env)
            g('init', '-q'); g('add', '-A'); g('commit', '-qm', 'base')
            return r, g

        said = []
        r, g = repo_with('ship')
        (r / 'gotchas' / 'gotcha-zz.md').write_text(link, encoding='utf-8')
        (r / 'spec' / 'ZZ.md').write_text('[t](../tools/zz_tool.py)\n', encoding='utf-8')
        g('add', '-A')
        fixed = pr.fix_shipped_links(r, ['gotchas/gotcha-zz.md', 'spec/ZZ.md'],
                                     say=said.append)
        staged = g('show', ':gotchas/gotcha-zz.md').stdout
        spec_now = (r / 'spec' / 'ZZ.md').read_text(encoding='utf-8')

        r2, g2 = repo_with('unstaged')
        (r2 / 'gotchas' / 'gotcha-zz.md').write_text(link, encoding='utf-8')
        g2('add', '-A')
        (r2 / 'gotchas' / 'gotcha-zz.md').write_text(link + 'mine\n', encoding='utf-8')
        said2 = []
        fixed2 = pr.fix_shipped_links(r2, ['gotchas/gotcha-zz.md'], say=said2.append)
        kept2 = (r2 / 'gotchas' / 'gotcha-zz.md').read_text(encoding='utf-8')

        r3, g3 = repo_with('consumer', engine_manifest=True)
        (r3 / 'gotchas' / 'gotcha-zz.md').write_text(link, encoding='utf-8')
        g3('add', '-A')
        fixed3 = pr.fix_shipped_links(r3, ['gotchas/gotcha-zz.md'], say=said.append)
    url = 'https://github.com/alex137/BestPractice/blob/staging/tools/zz_tool.py#L3'
    cases = [
        ('a link to a file the copy leaves out points at GitHub, anchor kept, '
         'and the result is staged',
         fixed == ['gotchas/gotcha-zz.md'] and f'[the tool]({url})' in staged),
        ('a link to a file the copy carries stays relative',
         '[a practice](../practices/zz-rule.md)' in staged),
        ('a file the copy does not carry is left alone',
         spec_now == '[t](../tools/zz_tool.py)\n'),
        ('a file with unstaged changes is left as it is, and said',
         fixed2 == [] and kept2 == link + 'mine\n'
         and any('not staged' in m for m in said2)),
        ('a repository that does not ship the copy is never touched',
         fixed3 == []),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else f' -- {staged!r} {said} {said2}'))


def check_source_pin_counts_an_uncommitted_new_practice():
    """A set with a new practice file nobody committed is dirty to a sync.

    2026-10-17, very deep check (the practice-move rehearsal): after
    `precedent_move.py` put a practice into a shared set and before anyone
    committed it there, a consumer's sync materialized the new file,
    pinned the set at a commit that does not contain it, and its own
    `--check` printed OK -- is_dirty asked git with --untracked-files=no.
    The control halves matter as much: an untracked file outside what a
    sync reads, an ignored one, and an engine file refreshed in place must
    all still read clean, or no set clone in a session is ever pinned."""
    import tempfile
    import precedent_source_pins as psp

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        s = pathlib.Path(td) / 'set'
        (s / 'practices').mkdir(parents=True)
        (s / 'tools').mkdir()
        (s / 'practices' / 'old.md').write_text('old\n', encoding='utf-8')
        (s / 'tools' / 'engine.py').write_text('x = 1\n', encoding='utf-8')
        (s / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            '{"files": ["engine.py"]}\n', encoding='utf-8')
        (s / '.gitignore').write_text('scratch/\n', encoding='utf-8')
        git(s, 'init', '-q', '-b', 'main')
        git(s, 'add', '-A')
        git(s, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        cases.append(('a clean set reads clean', not psp.is_dirty(s)))
        (s / 'notes.txt').write_text('mine\n', encoding='utf-8')
        (s / 'scratch').mkdir()
        (s / 'scratch' / 'practices.md').write_text('x\n', encoding='utf-8')
        cases.append(('an untracked file a sync never reads, and an ignored '
                      'one, leave it clean', not psp.is_dirty(s)))
        (s / 'tools' / 'engine.py').write_text('x = 2\n', encoding='utf-8')
        cases.append(('an engine file refreshed in place leaves it clean',
                      not psp.is_dirty(s)))
        (s / 'practices' / 'moved-in.md').write_text('new\n', encoding='utf-8')
        cases.append(('an uncommitted NEW practice file makes it dirty',
                      psp.is_dirty(s)))
    failed = [n for n, ok in cases if not ok]
    check(f'source pin counts an uncommitted new practice ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_one_tree_per_source_whichever_way_links_run():
    """One practice source, one tree, whichever folder got there first.

    Seen 2026-10-18 on one cloud container: /home/user/precedent-individual
    and /home/user/precedent-shared-ladder were links into /root, while
    /root/precedent-shared-writing was a link into /home/user. One tree each,
    but which folder held it depended on which repository resolved the set
    first, and the clone lock is keyed by path, so two runs cloning the same
    set into the two folders at once never waited on each other. A report
    from 2026-10-17 of a shared set "cloned twice at session start" could
    not be reproduced afterwards, which is what that race leaves behind.

    Morgan, 2026-10-19 (strength: decided): each harness declares a home
    folder (tools/source_homes.json); the tree is cloned there and every
    other path is a link into it; every tool that lists checkouts treats a
    link and its target as one, through precedent_source_home.

    Three parts, each against a fixture it owns (practice:
    fixture-owns-its-state): (a) each harness's home folder, and the
    bootstrap cloning into it, (b) the listers on a container laid out the
    2026-10-18 way, links running both directions, (c) the two runs that
    used to leave two trees. NEGATIVE CONTROLS: (a) and (c) run again with
    the home rule off, the code before this change, and must leave two
    trees; (b)'s session-hooks lister must have run a repository's hooks
    twice before."""
    import tempfile, contextlib, io
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_source_home as psh
        import precedent_source_bootstrap as psb
        import precedent_run_session_hooks as rsh
        import precedent_stale_branches as psbr
    finally:
        sys.path.pop(0)
    cases = []

    # (a) the registry: one home folder per harness, the four adapters and a
    # default, and every adapter that runs the bootstrap names its entry.
    reg = psh.registry()
    adapters = sorted(d.name for d in (ROOT / 'templates' / 'harness').iterdir()
                      if d.is_dir())
    cases.append(('the registry has every adapter under templates/harness/ '
                  'and a default',
                  set(adapters) | {'default'} <= set(reg), f'{adapters} {sorted(reg)}'))
    for adapter, rel in (('codex', 'codex/hooks.json'),
                         ('gemini-cli', 'gemini-cli/settings.json'),
                         ('grok-build', 'grok-build/README.md')):
        text = (ROOT / 'templates' / 'harness' / rel).read_text(encoding='utf-8')
        cases.append((f'the {adapter} adapter declares PRECEDENT_HARNESS={adapter}',
                      f'PRECEDENT_HARNESS={adapter}' in text, rel))
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        home, ws = t / 'home', t / 'ws'
        proj = ws / 'proj'
        proj.mkdir(parents=True)
        home.mkdir()
        subprocess.run(['git', 'init', '-q', str(proj)], capture_output=True)
        base = {'HOME': str(home), 'PRECEDENT_PROJECT_DIR': str(proj)}
        want = {
            'claude-code on the web': ({**base, 'CLAUDECODE': '1',
                                        'CLAUDE_CODE_REMOTE': 'true'}, ws),
            'claude-code on a computer': ({**base, 'CLAUDECODE': '1'}, home),
            'codex': ({**base, 'PRECEDENT_HARNESS': 'codex'}, home),
            'gemini-cli': ({**base, 'PRECEDENT_HARNESS': 'gemini-cli'}, home),
            'grok-build': ({**base, 'PRECEDENT_HARNESS': 'grok-build'}, home),
            'any other harness': (dict(base), home),
            'PRECEDENT_SOURCE_HOME set': ({**base, 'CLAUDECODE': '1',
                                           'CLAUDE_CODE_REMOTE': 'true',
                                           'PRECEDENT_SOURCE_HOME': str(t / 'mine')},
                                          t / 'mine'),
        }
        for label, (env, folder) in want.items():
            got = psh.home(env)
            cases.append((f'home folder, {label}', got == folder, f'{got} != {folder}'))

    # (a) and (c): the bootstrap clones a shared set into the home folder and
    # links the declared path, so two runs that resolve the set into the
    # two folders leave one tree. With the rule off -- the old code -- the
    # same two runs leave two.
    def two_runs(rule, harness_env):
        with tempfile.TemporaryDirectory() as td:
            t = pathlib.Path(td)
            srv, home, ws = t / 'srv', t / 'home', t / 'ws'
            proj = ws / 'proj'
            source = srv / 'acct' / 'precedent-shared-x'
            for d in (source, home, proj):
                d.mkdir(parents=True)
            rewrite = {'GIT_CONFIG_COUNT': '1',
                       'GIT_CONFIG_KEY_0': f'url.file://{srv}/.insteadOf',
                       'GIT_CONFIG_VALUE_0': 'https://example.invalid/'}
            git_env = {**os.environ, **rewrite, 'GIT_AUTHOR_NAME': 't',
                       'GIT_AUTHOR_EMAIL': 't@example.com',
                       'GIT_COMMITTER_NAME': 't',
                       'GIT_COMMITTER_EMAIL': 't@example.com'}
            for args in (['init', '-q', '-b', 'main'], ['add', '-A'],
                         ['commit', '-qm', 'seed']):
                if args[0] == 'add':
                    (source / 'practices').mkdir()
                    (source / 'practices' / 'x.md').write_text('x\n')
                subprocess.run(['git', *args], cwd=str(source), env=git_env,
                               capture_output=True)
            subprocess.run(['git', 'init', '-q', str(proj)], capture_output=True)
            keys = ['HOME', 'PRECEDENT_PROJECT_DIR', 'CLAUDE_PROJECT_DIR',
                    'CLAUDECODE', 'CLAUDE_CODE_REMOTE', 'PRECEDENT_HARNESS',
                    'PRECEDENT_SOURCE_HOME', *rewrite]
            saved = {k: os.environ.get(k) for k in keys}
            saved_rule = getattr(psb, '_home_rule', False)
            try:
                for k in keys:
                    os.environ.pop(k, None)
                os.environ.update(rewrite)
                os.environ.update(HOME=str(home), PRECEDENT_PROJECT_DIR=str(proj),
                                  **harness_env)
                psb._home_rule = rule
                url = 'https://example.invalid/acct/precedent-shared-x'
                for declared in (home / 'precedent-shared-x',
                                 ws / 'precedent-shared-x'):
                    with contextlib.redirect_stderr(io.StringIO()):
                        psb.ensure_source('shared', 'precedent-shared-x', url,
                                          declared, None, retries=1,
                                          retry_delay=0)
            finally:
                psb._home_rule = saved_rule
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            paths = [home / 'precedent-shared-x', ws / 'precedent-shared-x']
            real = [p for p in paths if (p / '.git').exists()
                    and not p.is_symlink()]
            linked = [p for p in paths if p.is_symlink()
                      and real and psh.same_tree(p, real[0])]
            return real, linked, paths

    for label, harness_env, tree_in in (
            ('claude-code on the web', {'CLAUDECODE': '1',
                                        'CLAUDE_CODE_REMOTE': 'true'}, 1),
            ('codex', {'PRECEDENT_HARNESS': 'codex'}, 0)):
        real, linked, paths = two_runs(True, harness_env)
        cases.append((f'{label}: two runs from the two folders leave one tree, '
                      f'in the home folder, and a link into it',
                      [p.name for p in real] == ['precedent-shared-x']
                      and real[0].parent == paths[tree_in].parent
                      and len(linked) == 1,
                      f'trees {real}, links {linked}'))
        real_old, _, _ = two_runs(False, harness_env)
        cases.append((f'{label}: CONTROL, with the rule off the same two runs '
                      f'leave two trees',
                      len(real_old) == 2, f'trees {real_old}'))

    # (a) the individual set the same way, through the hook's own path
    # ($HOME/<name>): cloned into the home folder with $HOME linked to it,
    # and a tree in the home folder that is some other repository is never
    # adopted -- the run clones where the hook said instead.
    def individual_run(foreign):
        with tempfile.TemporaryDirectory() as td:
            t = pathlib.Path(td)
            srv, home, ws = t / 'srv', t / 'home', t / 'ws'
            proj = ws / 'proj'
            source = srv / 'acct' / 'precedent-individual'
            for d in (source, home, proj):
                d.mkdir(parents=True)
            rewrite = {'GIT_CONFIG_COUNT': '1',
                       'GIT_CONFIG_KEY_0': f'url.file://{srv}/.insteadOf',
                       'GIT_CONFIG_VALUE_0': 'https://example.invalid/'}
            git_env = {**os.environ, **rewrite, 'GIT_AUTHOR_NAME': 't',
                       'GIT_AUTHOR_EMAIL': 't@example.com',
                       'GIT_COMMITTER_NAME': 't',
                       'GIT_COMMITTER_EMAIL': 't@example.com'}
            (source / 'practices').mkdir()
            (source / 'practices' / 'x.md').write_text('x\n')
            for args in (['init', '-q', '-b', 'main'], ['add', '-A'],
                         ['commit', '-qm', 'seed']):
                subprocess.run(['git', *args], cwd=str(source), env=git_env,
                               capture_output=True)
            subprocess.run(['git', 'init', '-q', str(proj)], capture_output=True)
            if foreign:
                other = ws / 'precedent-individual'
                subprocess.run(['git', 'init', '-q', str(other)], capture_output=True)
                subprocess.run(['git', '-C', str(other), 'remote', 'add', 'origin',
                                'https://example.invalid/owner/precedent-individual'],
                               capture_output=True)
            keys = ['HOME', 'PRECEDENT_PROJECT_DIR', 'CLAUDE_PROJECT_DIR',
                    'CLAUDECODE', 'CLAUDE_CODE_REMOTE', 'PRECEDENT_HARNESS',
                    'PRECEDENT_SOURCE_HOME', *rewrite]
            saved = {k: os.environ.get(k) for k in keys}
            saved_rule = getattr(psb, '_home_rule', False)
            try:
                for k in keys:
                    os.environ.pop(k, None)
                os.environ.update(rewrite)
                os.environ.update(HOME=str(home), PRECEDENT_PROJECT_DIR=str(proj),
                                  CLAUDECODE='1', CLAUDE_CODE_REMOTE='true')
                psb._home_rule = True
                with contextlib.redirect_stderr(io.StringIO()):
                    ok, _ = psb.ensure_source(
                        'individual', 'precedent-individual',
                        'https://example.invalid/acct/precedent-individual',
                        home / 'precedent-individual', t / 'config.json',
                        retries=1, retry_delay=0, workspace=ws)
                cfg = json.loads((t / 'config.json').read_text())
            finally:
                psb._home_rule = saved_rule
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            in_ws, in_home = ws / 'precedent-individual', home / 'precedent-individual'
            return (ok, cfg['individual']['path'], str(in_ws), str(in_home),
                    in_home.is_symlink() and psh.same_tree(in_home, in_ws),
                    (in_ws / 'practices').is_dir(), (in_home / 'practices').is_dir()
                    and not in_home.is_symlink())

    ok, cfg_path, in_ws, in_home, home_linked, ws_has, home_real = individual_run(False)
    cases.append(('the individual set is cloned into the home folder (the attach '
                  'folder on the web), and $HOME/<name> is a link into it',
                  ok and cfg_path == in_ws and home_linked and ws_has,
                  f'ok={ok} config={cfg_path} home_linked={home_linked}'))
    ok, cfg_path, in_ws, in_home, home_linked, ws_has, home_real = individual_run(True)
    cases.append(('a tree in the home folder that is another repository is never '
                  'adopted: the run clones where the hook said',
                  ok and cfg_path == in_home and home_real and not ws_has,
                  f'ok={ok} config={cfg_path} home_real={home_real}'))

    # (b) a container laid out the 2026-10-18 way: links both directions.
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        root_home, user = t / 'root', t / 'home-user'
        root_home.mkdir()
        user.mkdir()
        trees = {'precedent-individual': root_home,
                 'precedent-shared-zz': root_home,
                 'precedent-shared-yy': user,
                 'BestPractice': user}
        for name, where in trees.items():
            d = where / name
            (d / '.claude').mkdir(parents=True)
            (d / '.claude' / 'settings.json').write_text('{}')
            subprocess.run(['git', 'init', '-q', str(d)], capture_output=True)
            other = user if where == root_home else root_home
            if name != 'BestPractice':
                (other / name).symlink_to(d, target_is_directory=True)
        # the attach tool's lowercase spelling of a repository already there
        (user / 'bestpractice').symlink_to(user / 'BestPractice',
                                           target_is_directory=True)
        every = sorted(root_home.iterdir()) + sorted(user.iterdir())
        one = psh.one_per_tree(every)
        cases.append(('one_per_tree lists each of four trees once, links running '
                      'both ways and a second spelling',
                      len(one) == 4, f'{[str(p) for p in one]}'))
        listed = [p.name for p in rsh.repos_under(user)]
        cases.append(('the session-hooks runner runs a repository\'s hooks once '
                      'when two names under the root reach it',
                      sorted(n.lower() for n in listed)
                      == ['bestpractice', 'precedent-individual',
                          'precedent-shared-yy', 'precedent-shared-zz'],
                      str(listed)))
        cases.append(('the branch page\'s place test agrees with it',
                      psbr._same_place(user / 'bestpractice')
                      == psbr._same_place(user / 'BestPractice')
                      and psbr._same_place(root_home / 'precedent-shared-yy')
                      == psbr._same_place(user / 'precedent-shared-yy'), ''))
        # The individual bootstrap's own "cloned twice" report: a link in
        # either direction is one tree, never reported.
        url = 'https://example.invalid/acct/precedent-individual'
        saved_home = os.environ.get('HOME')
        try:
            os.environ['HOME'] = str(root_home)
            for clone in (user / 'precedent-individual',
                          root_home / 'precedent-individual'):
                _p, _links, report = psb._one_individual_tree(
                    'precedent-individual', url, clone, user)
                cases.append((f'the bootstrap does not call {clone.parent.name}/'
                              f'precedent-individual a second clone',
                              report is None, str(report)))
        finally:
            if saved_home is None:
                os.environ.pop('HOME', None)
            else:
                os.environ['HOME'] = saved_home
    # The runner case above is not empty: by name, that root holds five
    # repositories for four trees, which the runner before this change ran
    # the hooks of five times.
    cases.append(('the layout really has five names for four trees under one root',
                  len([p for p in every if p.parent == user]) == 5, ''))

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n}: {d}' for n, d in bad))


def check_bootstrap_source_produces_resolvable_set():
    """spec/BOOTSTRAP_NEW_SOURCES.md's own claim, tested rather than trusted:
    tools/precedent_bootstrap_source.py's output is not just files copied
    into place, it is a working individual set AND shared set that
    tools/precedent_resolve.py actually resolves cleanly the moment they're
    wired in -- the property that matters, since a skeleton nobody can
    resolve is no better than no skeleton at all.

    Fixture: bootstrap one individual set and one shared set into a scratch
    dir, point a synthetic consumer repo's precedent.json (team) and
    PRECEDENT_USER_CONFIG (individual) at them, and resolve. A fixture
    practice with ONE slug is then planted into both sets, which exercises
    the precedence resolver for real (team must win over individual, per
    tools/precedent_resolve.py's documented order) rather than only proving
    the sources load. Until 2026-09-14 the two skeletons' own placeholder
    files shared the slug `example-starter` and this case leaned on that --
    and a real migration that bootstrapped both sets then had its first
    sync REFUSED: the team placeholder overrode the individual one, so the
    individual set "contributed no practices at all". The skeletons carry
    distinct slugs now; the collision this case needs is planted here."""
    import shutil, tempfile

    def pyrun(*args, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        r = subprocess.run([sys.executable, *args], capture_output=True,
                           text=True, env=env)
        return r.returncode, r.stdout + r.stderr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bootstrap-'))
    cases = []
    try:
        bootstrap_tool = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        indiv_dest = tmp / 'indiv-set'
        team_dest = tmp / 'shared-set'

        rc, out = pyrun(bootstrap_tool, '--level', 'individual',
                        '--name', 'precedent-individual', '--dest', str(indiv_dest))
        cases.append(('bootstrapping an individual set succeeds and writes its files',
                      rc == 0 and (indiv_dest / 'practices' / 'example-starter-individual.md').is_file()
                      and (indiv_dest / 'config.json.sample').is_file(), out))
        # Its own list of generated files (spec/GENERATED_FILES_PLAN.md step
        # 4): what its commit rebuilds and its check reads, current from
        # the first commit.
        _gf = indiv_dest / 'tools' / 'generated_files.json'
        _entries = (json.loads(_gf.read_text(encoding='utf-8')).get('files', [])
                    if _gf.is_file() else [])
        _reg = subprocess.run([sys.executable, 'tools/precedent_check.py', '--only',
                               'generated-files-registered'], cwd=str(indiv_dest),
                              capture_output=True, text=True)
        cases.append(('a new set lists the three views it generates, and its own '
                      'check of that list passes',
                      {(e.get('path'), e.get('part')) for e in _entries} == {
                          ('MAP.md', None), ('GLOSSARY.md', None),
                          ('AGENTS.md', '<!-- BEGIN GENERATED: precedent-loader -->')}
                      and all(e.get('inputs') and e.get('check') for e in _entries)
                      and _reg.returncode == 0 and '1 passed' in _reg.stdout,
                      failure_detail(_reg.stdout, 400) + failure_detail(_reg.stderr, 200)))
        # 2026-10-28: sets made here had no permissions block, so a session
        # rooted in one stopped at the add_repo prompt for the sets it brings.
        _st = indiv_dest / '.claude' / 'settings.json'
        _allow = ((json.loads(_st.read_text(encoding='utf-8')).get('permissions') or {})
                  .get('allow') or []) if _st.is_file() else []
        cases.append(('a new set\'s settings.json allows attaching without a prompt',
                      'mcp__claude-code-remote__add_repo' in _allow
                      and 'mcp__claude-code-remote__register_repo_root' in _allow,
                      _allow))
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import precedent_push_check as _ppc
        finally:
            sys.path.pop(0)
        cases.append(('a set\'s views are checked at the quick tier, so a stale or '
                      'hand-edited one fails the push to staging, not only the Debut',
                      'build_views' in _ppc.BASIC_CHECKS
                      and any(st[0] == 'build_views' for st in _ppc.PUSH_CHECKS['source']),
                      f'BASIC_CHECKS = {sorted(_ppc.BASIC_CHECKS)}'))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'precedent-team-harness-fixture', '--dest', str(team_dest))
        cases.append(('bootstrapping a shared set without --approver is refused',
                      rc == 1 and 'approver' in out, out))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'precedent-team-harness-fixture', '--dest', str(team_dest),
                        '--approver', 'Harness Approver:harness-approver-gh')
        approvers_json = team_dest / 'approvers.json'
        cases.append(('bootstrapping a shared set succeeds and seeds approvers.json',
                      rc == 0 and approvers_json.is_file()
                      and json.loads(approvers_json.read_text()).get('approvers')
                      == [{'name': 'Harness Approver', 'github': 'harness-approver-gh'}], out))

        non_empty = tmp / 'occupied'
        (non_empty / 'something.txt').parent.mkdir(parents=True)
        (non_empty / 'something.txt').write_text('pre-existing', encoding='utf-8')
        rc, out = pyrun(bootstrap_tool, '--level', 'individual',
                        '--name', 'precedent-individual', '--dest', str(non_empty))
        cases.append(('bootstrapping into a non-empty destination is refused without --force',
                      rc == 1 and 'not empty' in out, out))

        consumer = tmp / 'consumer'
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                {'level': 'team', 'name': 'precedent-team-harness-fixture', 'path': str(team_dest)},
            ],
        }), encoding='utf-8')
        user_config = tmp / 'user-config.json'
        user_config.write_text(json.dumps({
            'individual': {'name': 'precedent-individual', 'path': str(indiv_dest)},
        }), encoding='utf-8')

        # The deliberate collision: one slug in both sets.
        for dest, level in ((indiv_dest, 'individual'), (team_dest, 'team')):
            (dest / 'practices' / 'zz-shared-slug.md').write_text(
                '---\nslug:        zz-shared-slug\n'
                f'title:       A {level} practice sharing a slug\n'
                'tier:        on-demand\nseverity:    default\n'
                'applies_to:  ["**"]\noccasion:    "fixture"\n'
                'index_clause: "fixture"\nchecked_by:  null\n'
                'defines:     []\nstatus:      active\nin_force_at: null\n'
                'supersedes:  []\noverrides:   null\nadded:       null\n'
                'approved_by: "fixture"\n---\n\n## Rule\nPlanted.\n\n'
                '## Why\nPlanted.\n\n## Story\nPlanted for the harness.\n',
                encoding='utf-8')
        rc, out = pyrun(str(ROOT / 'tools' / 'precedent_resolve.py'),
                        '--repo', str(consumer), '--json',
                        env_extra={'PRECEDENT_USER_CONFIG': str(user_config)})
        resolved = {}
        try:
            resolved = json.loads(out)
        except json.JSONDecodeError:
            pass
        slugs = {p['slug']: p for p in resolved.get('practices', [])}
        cases.append(('the resulting consumer repo resolves cleanly -- no missing, '
                      'no blocked sources',
                      rc == 0 and not resolved.get('missing') and not resolved.get('blocked'), out))
        cases.append(('the planted shared slug resolves, won by the shared set over '
                      'the individual set (real precedence, not just presence)',
                      slugs.get('zz-shared-slug', {}).get('level') == 'shared', out))
        cases.append(('and the two skeletons\' own placeholders no longer collide: '
                      'both resolve, each from its own level',
                      slugs.get('example-starter-shared', {}).get('level') == 'shared'
                      and slugs.get('example-starter-individual', {}).get('level')
                      == 'individual', out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'bootstrap_source produces a resolvable individual and shared set '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_loader_block_covers_every_declared_source():
    """The loader block renders every PUBLISHABLE source `precedent.json`
    declares -- and never a private one in a public repo.

    Measured here 2026-09-06, before the fix: 65 of 65 universal practices
    reached this repo's block, 0 of 41 team, 0 of 11 individual. The config
    declared all three, the resolver agreed, and the one artifact a session
    actually reads listed only the first. A rule nothing can load is not in
    force; it is filed. That is what the first half asserts, and it is the
    whole rule in a private consumer repo -- which is every repo that
    vendors this engine.

    The second half is the privacy boundary, and it is the reason this is a
    check rather than a setting somebody remembers.
    `precedent_resolve.py` already refuses to let a shared repo DECLARE an
    individual source, because naming it leaks its existence and location.
    Rendering a private source's practices into a tracked, published file is
    the same disclosure arriving by another route -- so a repo marked
    `"visibility": "public"` must never carry team- or individual-level
    content in its block, and a regression there publishes a private set
    silently and permanently. This repo is that public case; see
    decisions/2026-09-06-precedent-binds-itself.md section 2, which rejected
    multi-source generated views here on exactly this ground.
    """
    import json as _json
    config = ROOT / 'precedent.json'
    if not config.is_file():
        not_applicable('the loader block covers every declared source',
                       'this repo declares no precedent.json')
        return
    try:
        import precedent_resolve as pr
        declared = pr.load_config(ROOT)
        cfg = _json.loads(config.read_text(encoding='utf-8'))
    except Exception as e:
        not_applicable('the loader block covers every declared source',
                       f'sources did not resolve here ({e}) -- not a pass')
        return

    agents = ROOT / 'AGENTS.md'
    if not agents.is_file():
        not_applicable('the loader block covers every declared source',
                       'this repo has no AGENTS.md')
        return
    name = 'AGENTS.md'
    instructions = agents.read_text(encoding='utf-8')
    a, b = '<!-- BEGIN GENERATED', '<!-- END GENERATED'
    if a not in instructions or b not in instructions:
        not_applicable('the loader block covers every declared source',
                       'AGENTS.md carries no generated loader block')
        return
    # Only the GENERATED block counts. A slug mentioned in hand-written prose
    # is not the loader pointing a session at it.
    block = instructions[instructions.index(a):instructions.index(b)]
    # Slugs the loader ACTUALLY indexes, read from the two shapes the
    # generated block uses -- an occasion-index line ("  slug — clause") and
    # a resident entry ("**slug.** ..."). Matching bare words in prose
    # instead was wrong both ways: it required a hyphen, so a single-word
    # slug like `install` could never be found and was reported unreachable
    # forever; and loosening the pattern to allow single words would have
    # matched the ordinary English word "install" anywhere in the file and
    # called the practice reachable when nothing indexed it.
    named = set(re.findall(r'^\s+([a-z0-9][a-z0-9-]*) \u2014 ', block, re.M))
    named |= set(re.findall(r'^\*\*([a-z0-9][a-z0-9-]*)\.\*\*', block, re.M))

    public = cfg.get('visibility') == 'public'

    # Slugs a PUBLISHABLE source (universal, or repo-local, which lives in
    # this repo's own tree) has active. A slug in both a publishable source
    # and a private one is NOT evidence of a leak: build_views.py excludes
    # private-level sources from a public repo's block, so the entry the
    # block carries is the publishable source's own text, and only the SLUG
    # is shared. Without this the guard fired on the first same-slug
    # override to exist (catalogue-carries-stories, 2026-09-07 -- landed at
    # universal, and the shared source that had authored it first kept a copy
    # to put the rule in force on itself, since a source repo consumes no
    # catalogue). Verified by reading the rendered line: it was universal's
    # index_clause, not the team's. A finding nobody can act on without
    # deleting a legitimate practice is one people learn to ignore.
    publishable = set()
    for s in declared:
        if s['level'] in ('shared', 'team', 'individual'):
            continue
        d = pathlib.Path(s['path']) / 'practices'
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sec = sp._read_practice_file(f)
            except Exception:
                continue
            if (fm.get('status') or 'active').strip('" ') == 'active':
                publishable.add(fm.get('slug', f.stem))

    import build_views as _bv
    missing, leaked = [], []
    for s in declared:
        d = pathlib.Path(s['path']) / 'practices'
        if not d.is_dir():
            continue                       # unreachable here; not evidence
        active, expected_in_block = [], []
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sec = sp._read_practice_file(f)
            except Exception:
                continue
            if (fm.get('status') or 'active').strip('" ') == 'active':
                active.append(fm.get('slug', f.stem))
                # A practice routed by a real applies_to glob or a gate is
                # deliberately NOT named in the block -- build_views omits it
                # from the occasion index because those channels already reach
                # it. A source whose practices are ALL routed therefore
                # contributes nothing to the rendered text while having
                # resolved perfectly, so requiring its name here would be a
                # false failure. Only a source with at least one practice that
                # should appear is evidence of anything either way.
                if not _bv.index_is_redundant(fm):
                    expected_in_block.append(fm.get('slug', f.stem))
        if not active:
            continue
        present = [a for a in active if a in named]
        if public and s['level'] in ('shared', 'team', 'individual'):
            leaked += [a for a in present if a not in publishable]
        elif not present and expected_in_block:
            missing.append(f"{s['level']}/{s['name']} ({len(expected_in_block)} of "
                           f"{len(active)} active practices should be named in "
                           f"{name}, none is)")

    check('the loader block renders every publishable source '
          'precedent.json declares', not missing, '; '.join(missing))
    if public:
        check('no private-source practice reaches a public repo\'s tracked '
              'loader block',
              not leaked,
              f'{len(leaked)} leaked: {", ".join(sorted(leaked)[:6])}')


def check_deduplicated_copy_stays_in_force_until_its_target_arrives():
    """A practice a set handed on to another source stays in force from the
    handed-on copy while the copy it names has not reached this repository,
    said so on every sync, and stands down by itself once it has.

    WHY. 2026-10-16, a consuming repository: a plain sync printed "IN FORCE NOWHERE --
    curly-quotes (precedent-shared-writing)" and removed the rule and its
    check, still reporting OK. precedent-shared-writing had handed
    curly-quotes to universal, and the repository's vendored universal
    catalogue predated that. Planted: the handed-on copy alone; the same
    with the target present (the control); and the bytes the materializer
    writes for a kept copy. And the control the other way: a universal copy
    pointing at a set the repo does not declare is not kept -- that is the
    person's call (not_in_force_here), asked by Update Vendors."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr
    import precedent_materialize as _pm
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-kept-'))
    cases = []
    try:
        sources, _consumer, write = _renamed_universal_fixture(tmp)
        write(tmp / 'ind' / 'practices' / 'handed-on.md', 'handed-on',
              'deduplicated', 'handed-on', rule='The whole rule, still here.')
        res = _pr.resolve(sources)
        kept = res['practices'].get('handed-on') or {}
        entry = next((d for d in res['dangling'] if d['slug'] == 'handed-on'), {})
        cases.append(('the handed-on copy binds while its target is missing',
                      bool(kept.get('kept_in_force')), sorted(res['practices'])))
        cases.append(('and every report says it was kept, and why',
                      entry.get('kept_in_force') is True
                      and 'kept in force here' in entry.get('why', ''), entry))
        data = _pm._as_written(kept) if kept else b''
        cases.append(('it is written out active, with no forwarding address',
                      b'status: active' in data and b'in_force_at: null' in data
                      and b'The whole rule, still here.' in data, data[:300]))
        write(tmp / 'uni' / 'practices' / 'to-a-set.md', 'to-a-set',
              'deduplicated', 'to-a-set')
        res = _pr.resolve(sources)
        cases.append(('CONTROL: a universal copy pointing at an undeclared set is not kept',
                      'to-a-set' not in res['practices']
                      and any(d['slug'] == 'to-a-set' and not d.get('kept_in_force')
                              for d in res['dangling']), sorted(res['practices'])))
        write(tmp / 'uni' / 'practices' / 'handed-on.md', 'handed-on')
        res = _pr.resolve(sources)
        cases.append(('CONTROL: once the target arrives, it is the rule in force and '
                      'the handed-on copy stands down',
                      res['practices'].get('handed-on', {}).get('source') == 'precedent'
                      and not res['practices']['handed-on'].get('kept_in_force')
                      and not any(d['slug'] == 'handed-on' for d in res['dangling']),
                      str(res['practices'].get('handed-on', {}).get('source'))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [f'{n}: {d}' for n, ok, d in cases if not ok]
    check(f'a deduplicated copy stays in force until its target arrives '
          f'({len(cases)} stated cases)', not bad, '; '.join(map(str, bad)))


def check_in_force_at_chain_is_followed():
    """A deduplication naming a slug that is itself a deduplicated stub is in
    force wherever that stub forwards to, not IN FORCE NOWHERE.

    WHY. Renaming go-merge to go-update on 2026-09-26 left a universal
    `go-merge` stub forwarding to `go-update`. An individual set's own
    `go-merge`, deduplicated against the universal one by the old name,
    was checked with a bare membership test against what resolved in force,
    so every consumer read it IN FORCE NOWHERE while the rule was live one
    hop on. The walk has to stop on a cycle as well: a set's copy names the
    very slug it carries, which is a two-node loop the moment the other end
    is missing."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-chain-'))
    cases = []
    try:
        sources, _consumer, write = _renamed_universal_fixture(tmp)
        res = _pr.resolve(sources)
        cases.append(('an individual deduplication naming a renamed universal '
                      'stub resolves through it -- nothing dangling',
                      not res['dangling'], str(res['dangling'])))
        # getattr, so an engine without the helpers reports named failing
        # cases rather than a traceback that hides which behaviour broke.
        follow = getattr(_pr, 'follow_in_force_at', None)
        fmap = getattr(_pr, 'forwarding_map', None)
        cases.append(('the chain ends on the live slug',
                      follow is not None and follow(
                          'go-merge', res['practices'], res['retired']) == 'go-update',
                      'follow_in_force_at missing' if follow is None else ''))
        forwards = fmap(res) if fmap else None
        cases.append(('forwarding_map names the rename',
                      forwards == {'go-merge': 'go-update'}, str(forwards)))

        # The control: take the live end away, and the same chain is
        # dangling again -- following it must not make everything pass.
        (tmp / 'uni' / 'practices' / 'go-update.md').unlink()
        res = _pr.resolve(sources)
        cases.append(('with the live end gone the chain is dangling, not '
                      'quietly accepted',
                      any(d['slug'] == 'go-merge' for d in res['dangling']),
                      str(res['dangling'])))

        # A cycle ends in None rather than a hang.
        write(tmp / 'uni' / 'practices' / 'loop-a.md', 'loop-a', 'deduplicated', 'loop-b')
        write(tmp / 'uni' / 'practices' / 'loop-b.md', 'loop-b', 'deduplicated', 'loop-a')
        res = _pr.resolve(sources)
        cases.append(('a cycle of deduplications is reported dangling and '
                      'the walk terminates',
                      {'loop-a', 'loop-b'} <= {d['slug'] for d in res['dangling']},
                      str(res['dangling'])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a deduplication\'s in_force_at: chain is followed to the rule in '
          f'force, with a cycle guard ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:160]}' for n, d in bad))


def check_links_to_renamed_practice_forward():
    """A materialized link to a renamed or deduplicated practice points at the
    live practice this run writes, not at a stub the consumer never gets.

    WHY. A consumer materializes only what is in force. After the go-merge
    -> go-update rename (2026-09-26), every `go-merge.md` citation in the
    private sets was left as written by _rewrite_links -- and, from an
    individual source, it may not become a URL either -- so the link was
    dead in every consumer."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr, precedent_materialize as _pm

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-fwdlinks-'))
    cases = []
    try:
        sources, consumer, _write = _renamed_universal_fixture(tmp)
        res = _pr.resolve(sources)
        _pm.materialize(sources, res, consumer)
        placed = consumer / 'practices'
        text = ((placed / 'cites.md').read_text(encoding='utf-8')
                if (placed / 'cites.md').is_file() else '')
        cases.append(('the stub itself is not materialized -- the reason the '
                      'old link was dead',
                      not (placed / 'go-merge.md').exists()
                      and (placed / 'go-update.md').is_file(), ''))
        cases.append(('a sibling link to the renamed slug now names the live '
                      'one, anchor kept',
                      '](go-update.md#rule)' in text, failure_detail(text, 300)))
        cases.append(('a path into the source clone naming the stub file is '
                      'sent to the live sibling too',
                      '](go-update.md)' in text
                      and 'uni/practices/go-merge.md' not in text, failure_detail(text, 300)))
        cases.append(('an individual source still names no repository',
                      'github.com' not in text, failure_detail(text, 300)))

        # With the live end not in this run there is nothing to forward to,
        # so the link is left as written rather than invented.
        (tmp / 'uni' / 'practices' / 'go-update.md').unlink()
        res = _pr.resolve(sources)
        _pm.materialize(sources, res, consumer)
        text = (placed / 'cites.md').read_text(encoding='utf-8')
        cases.append(('with no live slug in the run, the link is left alone',
                      '](go-merge.md#rule)' in text, failure_detail(text, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a materialized link to a renamed practice forwards to the live '
          f'practice ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:160]}' for n, d in bad))


def check_session_share_keeps_a_moved_rule_with_its_brought_set():
    """A rule an individual set moved into a set it brings is charged to the
    brought set's share, never back to the individual set's own.

    WHY (2026-10-28). The shares are measured by rendering the session file
    without the brought sets. Rendered that way, the individual set's
    deduplicated stubs found no target and were kept in force, so eleven
    rules moved into the ladder set on purpose were counted as the
    individual set's own and charged to the repository's ceiling as well,
    while the brought set's share came out too small.

    1. measured without the brought set, the moved rule is not there;
    2. the individual set's own rule still is;
    3. CONTROL: the full render still carries the moved rule, from the set
       it moved to."""
    import tempfile, contextlib, io
    import json as _json
    import precedent_session_practices as psp
    import precedent_resolve as pr

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
                _move_fixture_practice('plain-rule'), encoding='utf-8')
            lad = tmp / 'p' / 'fx-ladder'
            (lad / 'practices').mkdir(parents=True)
            (lad / 'precedent-source.json').write_text(_json.dumps({
                'name': 'fx-ladder', 'level': 'shared'}), encoding='utf-8')
            (lad / 'practices' / 'moved-rule.md').write_text(
                _move_fixture_practice('moved-rule'), encoding='utf-8')
            ind = tmp / 'p' / 'precedent-individual'
            (ind / 'practices').mkdir(parents=True)
            (ind / 'precedent-source.json').write_text(_json.dumps({
                'name': 'precedent-individual', 'level': 'individual',
                'brings': [{'name': 'fx-ladder',
                            'repo_url': 'https://example.com/fx.git'}]}),
                encoding='utf-8')
            (ind / 'practices' / 'own-rule.md').write_text(
                _move_fixture_practice('own-rule'), encoding='utf-8')
            (ind / 'practices' / 'moved-rule.md').write_text(
                _move_fixture_practice('moved-rule')
                .replace('status:      active', 'status:      deduplicated')
                .replace('in_force_at: null', 'in_force_at: moved-rule'),
                encoding='utf-8')
            cfg = tmp / 'cfg.json'
            cfg.write_text(_json.dumps({'format_version': 1, 'individual': {
                'name': 'precedent-individual', 'path': str(ind)}}),
                encoding='utf-8')
            os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
            repo = tmp / 'consumer'
            repo.mkdir()
            (repo / 'precedent.json').write_text(_json.dumps({
                'format_version': 1, 'base_branch': 'main',
                'visibility': 'private',
                'sources': [{'level': 'universal', 'name': 'precedent',
                             'path': str(uni)}]}), encoding='utf-8')

            def slugs(**kw):
                with contextlib.redirect_stderr(io.StringIO()):
                    extra = psp.collect(str(repo), **kw)[0]
                return {fm.get('slug') for fm, _s, _f in extra}

            full, bare = slugs(), slugs(skip_brought=True)
            results.append(('1: measured without the brought set, the moved '
                            'rule is not kept in force from its old stub',
                            'moved-rule' not in bare,
                            sorted(bare)))
            results.append(("2: the individual set's own rule is still there",
                            'own-rule' in bare,
                            sorted(bare)))
            results.append(('3: CONTROL: the full render carries the moved '
                            'rule, from the set it moved to',
                            'moved-rule' in full,
                            sorted(full)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    failed = [(n, d) for n, ok, d in results if not ok]
    check(f'a rule moved into a brought set is charged to that set, not back '
          f'to the individual set ({len(results)} stated cases)',
          not failed, '; '.join(f'{n} -- {d}' for n, d in failed))


def check_session_file_over_ceiling_names_the_individual_share():
    """The session check's over-ceiling row for .precedent/SESSION_PRACTICES.md
    says how much of the charge is the person's own individual set, which the
    repository cannot shorten, and how much is the repository's own.

    WHY. 2026-10-20, a consuming repository: ceiling 400, seeded when its own
    part measured 312; the session check failed every session start at
    ~1,510 and told the repository to do a reduction pass. ~1,176 of it was
    the person's individual set; the repository's own part, ~334, was within
    its ceiling."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_session_check as psc
    import precedent_session_practices as psp
    import precedent_resolve as pr
    cases = []
    saved_share, saved_load = getattr(psp, 'individual_share', None), pr.load_config
    saved_brought = psp.brought_budget
    try:
        psp.individual_share = lambda repo: 1176
        # This machine's own individual set may declare a budget of its own,
        # which makes _individual_part stand aside; the fixture owns that.
        psp.brought_budget = lambda repo=None, key=None: (None, None)
        part = getattr(psc, '_individual_part', lambda n, cap: '')(1510, 400)
        cases.append(('THE DISCRIMINATING CASE: the row names the individual '
                      "set's share and the repository's own",
                      '~1,176' in part and '~334' in part
                      and 'individual set' in part, repr(part)))
        cases.append(('...and says the repository part is within its ceiling',
                      'within its ceiling' in part, repr(part)))
        psp.individual_share = lambda repo: 0
        cases.append(('no individual share: nothing added',
                      getattr(psc, '_individual_part', lambda n, cap: '')(1510, 400) == '',
                      ''))
        seen = []
        pr.load_config = lambda repo: [
            {'level': 'universal', 'name': 'u', 'path': '.'},
            {'level': 'individual', 'name': 'me', 'path': '/nowhere'}]
        _resolve = pr.resolve
        pr.resolve = lambda sources, **_kw: (seen.append([s['level'] for s in sources])
                                      or {'missing': [], 'practices': {}})
        try:
            try:
                psp.collect(str(ROOT), skip_brought=True, skip_individual=True)
            except Exception:                                # noqa: BLE001
                pass
        finally:
            pr.resolve = _resolve
        cases.append(('collect(skip_individual=True) resolves without the '
                      'individual set', seen[:1] == [['universal']], str(seen)))
    finally:
        if saved_share is not None:
            psp.individual_share = saved_share
        psp.brought_budget = saved_brought
        pr.load_config = saved_load
        sys.path.pop(0)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'the session file over its ceiling names the individual share '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_declared_set_found_beside_the_individual_set():
    """A repository cloned away from its siblings resolves a set it
    declares (`../<name>`) at the clone beside the person's individual set,
    where session start puts every set; a real sibling still wins, and a
    folder that is not a practice set is never taken.

    WHY. 2026-10-28, a Produce from a clone made outside the session's
    project folder: its pre-push refused for a set that was on disk all
    along ("a practice source in force here did not load"), and the
    session symlinked the set in by hand."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='declared-beside-'))
    cases = []
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    try:
        people = tmp / 'people'

        def a_set(where, practices=True):
            (where / '.git').mkdir(parents=True)
            if practices:
                (where / 'practices').mkdir()
            return where

        a_set(people / 'zz-ind')
        known = a_set(people / 'zz-set')
        a_set(people / 'zz-bare', practices=False)
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {
            'name': 'zz-ind', 'path': str(people / 'zz-ind')}}))
        os.environ['PRECEDENT_USER_CONFIG'] = str(ucfg)
        import precedent_resolve as pr
        far = tmp / 'scratch' / 'repo'
        far.mkdir(parents=True)
        (far / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'zz-set', 'path': '../zz-set'}]}))
        got = pr._declared_path(far.resolve(), '../zz-set')
        cases.append(('away from its siblings: the clone beside the '
                      'individual set', got == known.resolve(), str(got)))
        rows = {n: (p, note) for p, _l, n, note in pr.declared_source_paths(far)}
        cases.append(('...which the push hook reads as loaded',
                      rows.get('zz-set') == (str(known.resolve()), ''),
                      repr(rows.get('zz-set'))))
        bare = pr._declared_path(far.resolve(), '../zz-bare')
        cases.append(('a folder with no practices is not taken',
                      bare == (far / '../zz-bare').resolve(), str(bare)))
        sib = a_set(tmp / 'scratch' / 'zz-set')
        got2 = pr._declared_path(far.resolve(), '../zz-set')
        cases.append(('NEGATIVE CONTROL: a real sibling still wins',
                      got2 == sib.resolve(), str(got2)))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c[0] + (f': {c[2]}' if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a declared set is found beside the individual set '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_budget_approvals_see_computed_raises():
    """The budgets in force stay within the person's approvals, however a
    number got bigger, and the session-start file's hard ceiling is enforced
    as a sum of its sources' declared numbers (practice: session-load-budget;
    control-asserts-which-failure).

    THE INCIDENT (2026-09-29): a session made precedent-individual's
    session-file ceiling a computed sum and the number in force went from
    5,200 to 6,200 with the `ceiling` field unchanged; Morgan had not been
    asked. The first fix compared registry FIELDS with a base commit, and
    could see neither a computed raise nor anything on a direct push or a
    Promote, where the base is HEAD. Each case below asserts the check's own
    words, so a case that fails for another reason reads as a failure.

    The fixture owns its tree (fixture-owns-its-state): a copy of this repo
    with no .git, no sibling sources and no user config."""
    import tempfile
    import importlib
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / 'fixture'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', 'prompts'))
        reg_p = repo / 'tools' / 'session_load_budgets.json'
        # Per-part caps bind only where no session-load total is declared
        # (build_views.TOTAL_KEY); this fixture tests them, so it has none.
        _drop_session_load_total(reg_p)
        bv_p = repo / 'tools' / 'build_views.py'
        src_p = repo / 'precedent-source.json'
        pristine = {p: p.read_text(encoding='utf-8') for p in (reg_p, bv_p, src_p)}

        def reset():
            for p, t in pristine.items():
                p.write_text(t, encoding='utf-8')

        def edit_reg(fn):
            d = json.loads(reg_p.read_text(encoding='utf-8'))
            fn(d)
            reg_p.write_text(json.dumps(d, indent=2), encoding='utf-8')

        def run():
            env = dict(os.environ,
                       PRECEDENT_USER_CONFIG=str(repo / '.no-user-config.json'))
            r = subprocess.run([sys.executable, str(repo / 'tools' / 'precedent_check.py'),
                                '--only', 'budget-within-approval'],
                               capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('this tree, as committed, is within its approvals',
                      rc == 0 and '1 passed' in out, failure_detail(out, 400)))

        edit_reg(lambda d: d['surfaces']['AGENTS.md'].update(ceiling=9000))
        rc, out = run()
        cases.append(('a raised ceiling field is refused, naming the number '
                      'and the approval it exceeds',
                      rc != 0 and 'surfaces/AGENTS.md is 9,000 in force, above '
                      'the 6,950' in out, failure_detail(out, 600)))
        reset()

        bv_p.write_text(pristine[bv_p].replace(
            "    v = row.get('ceiling')\n    return v if isinstance(v, int) else default",
            "    v = row.get('ceiling')\n    return v + 1000 if isinstance(v, int) else default", 1),
            encoding='utf-8')
        rc, out = run()
        cases.append(('a COMPUTED raise with every field unchanged is refused '
                      '(the 2026-09-29 incident)',
                      rc != 0 and 'surfaces/.precedent/SESSION_PRACTICES.md is '
                      '5,000 in force, above the 4,000' in out, failure_detail(out, 600)))
        reset()

        src_p.write_text(json.dumps({k: v for k, v in json.loads(
            pristine[src_p]).items() if k != 'occasion_share_tokens'}),
            encoding='utf-8')
        rc, out = run()
        cases.append(('a removed allowance reads as uncapped and is refused',
                      rc != 0 and 'occasion_share_tokens is uncapped in force'
                      in out, failure_detail(out, 600)))
        reset()

        edit_reg(lambda d: d['surfaces']['AGENTS.md'].update(target=5000))
        rc, out = run()
        cases.append(('a new target nobody approved is refused',
                      rc != 0 and 'surfaces/AGENTS.md/target is 5000 in force '
                      'and has no entry in approved_budgets' in out, failure_detail(out, 600)))
        reset()

        def raise_with(words, strength):
            def fn(d):
                d['surfaces']['AGENTS.md']['ceiling'] = 9000
                d['approved_budgets']['surfaces/AGENTS.md'] = {
                    'max': 9000, 'strength': strength,
                    'approved_by': f'Fixture Person, 2026-09-30: {words}'}
            return fn

        edit_reg(raise_with('"yes, raise it to 9,000"', 'decided'))
        rc, out = run()
        cases.append(('a raise carrying the person\'s quoted words passes',
                      rc == 0 and '1 passed' in out, failure_detail(out, 600)))
        reset()

        edit_reg(raise_with('said yes', 'decided'))
        rc, out = run()
        cases.append(('a "decided" approval with no quoted words is refused',
                      rc != 0 and "approved_by quotes nobody's words" in out,
                      failure_detail(out, 600)))
        reset()

        # 2026-10-08: brought_sets_tokens was a budget no check could see,
        # and a session raised it from 700 to 1,200 unasked.
        src_p.write_text(json.dumps(dict(json.loads(pristine[src_p]),
                                         brought_sets_tokens=1200)), encoding='utf-8')
        rc, out = run()
        cases.append(("a person's brought_sets_tokens is a budget the check "
                      'sees: unapproved, it is refused',
                      rc != 0 and 'brought_sets_tokens is 1200 in force and has '
                      'no entry in approved_budgets' in out, failure_detail(out, 600)))
        reset()

        def offset(freed):
            def fn(d):
                d['surfaces']['AGENTS.md']['ceiling'] = 7250
                d['approved_budgets']['surfaces/AGENTS.md'] = {
                    'max': 7250, 'strength': 'offset', 'previous_max': 6950,
                    'freed': freed, 'offset_from': 'a removed shared set',
                    'approved_by': 'offset, 2026-10-08'}
            return fn

        edit_reg(offset(400))
        rc, out = run()
        cases.append(('a raise paid for by tokens a removal freed passes without '
                      "the person's words", rc == 0 and '1 passed' in out, failure_detail(out, 600)))
        reset()
        edit_reg(offset(100))
        rc, out = run()
        cases.append(('...and one larger than what was freed is refused',
                      rc != 0 and 'more than the 100 tokens its offset freed' in out,
                      failure_detail(out, 600)))
        reset()

        edit_reg(lambda d: d.pop('approved_budgets'))
        rc, out = run()
        cases.append(('with no approvals list and no main to compare, the '
                      'check says it is not checking, never passes',
                      'SKIPPED' in out and 'a raise here is not checked' in out,
                      failure_detail(out, 600)))
        reset()

        # --- the hard ceiling as a sum, in a consumer's shape ------------
        sys.path.insert(0, str(ROOT / 'tools'))
        pc = importlib.import_module('precedent_check')
        bv = importlib.import_module('build_views')
        pr = importlib.import_module('precedent_resolve')
        consumer = pathlib.Path(tmp) / 'consumer'
        (consumer / 'tools').mkdir(parents=True)

        def source(name, share, resident):
            d = pathlib.Path(tmp) / name
            (d / 'tools').mkdir(parents=True, exist_ok=True)
            (d / 'precedent-source.json').write_text(json.dumps(
                {'name': name, 'occasion_share_tokens': share}), encoding='utf-8')
            rb = {} if resident is None else {'resident_block_tokens': resident}
            (d / 'tools' / 'session_load_budgets.json').write_text(
                json.dumps(rb), encoding='utf-8')
            return {'name': name, 'path': str(d), 'level': 'shared'}

        def fit(entry, srcs):
            (consumer / 'tools' / 'session_load_budgets.json').write_text(
                json.dumps({'surfaces': {'.precedent/SESSION_PRACTICES.md': entry}}),
                encoding='utf-8')
            saved = (pc.ROOT, bv.sources_for_tracked_block, pr.load_config)
            pc.ROOT = consumer
            bv.sources_for_tracked_block = lambda root, cfg: ([], srcs, [])
            pr.load_config = lambda root, *a, **k: []
            try:
                return pc._session_file_allowances_fit(None)
            except pc.NotApplicable as e:
                return f'N/A {e}'
            finally:
                pc.ROOT, bv.sources_for_tracked_block, pr.load_config = saved

        small = [source('u', 1800, 900), source('w', 150, 200)]
        got = fit({'hard_ceiling': 4400, 'fixed_allowance': 300}, small)
        cases.append(('sources whose numbers add up under the hard ceiling pass',
                      got == [], repr(got)))
        big = [source('u2', 2800, 2000), source('w2', 550, 425)]
        got = fit({'hard_ceiling': 4400, 'fixed_allowance': 300}, big)
        cases.append(('sources whose numbers add up over it are refused, with '
                      'the parts listed',
                      len(got) == 1 and "allowances add up to 6,075" in got[0].detail
                      and 'u2 2,800+2,000' in got[0].detail, repr(got)))
        got = fit({'hard_ceiling': 4400, 'fixed_allowance': 300},
                  small + [source('r', 450, None)])
        cases.append(('a source with no resident cap means the sum cannot be '
                      'shown, and does not pass',
                      len(got) == 1 and 'r (no resident_block_tokens)' in got[0].detail,
                      repr(got)))
        got = fit({'target': 4000}, big)
        cases.append(('with no hard_ceiling declared, it is not switched on',
                      isinstance(got, str) and 'declares no hard_ceiling' in got,
                      repr(got)))

        # --- D: the once-per-session warning ------------------------------
        psp = importlib.import_module('precedent_session_practices')
        (consumer / 'tools' / 'session_load_budgets.json').write_text(json.dumps(
            {'surfaces': {'.precedent/SESSION_PRACTICES.md': {'target': 50}}}),
            encoding='utf-8')
        text = '<!-- x -->\n\n# Practices\n\n' + 'word ' * 100
        warned = psp._with_target_warning(consumer, text)
        cases.append(('the session-start file opens with the warning under its '
                      'title when over target',
                      'SESSION LOAD OVER TARGET' in warned
                      and warned.index('# Practices') < warned.index('OVER TARGET'),
                      warned[:200]))
        short = '<!-- x -->\n\n# Practices\n\nshort\n'
        cases.append(('and carries none when under it',
                      psp._with_target_warning(consumer, short) == short,
                      psp._with_target_warning(consumer, short)))

        # --- F: the trend tool names the repository it measured ----------
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'session_load_trend.py'),
                            '--root', str(repo)], capture_output=True, text=True,
                           cwd=str(repo))
        cases.append(('session_load_trend.py --root measures that repository '
                      'and names it',
                      r.returncode == 0 and 'SESSION LOAD -- fixture' in r.stdout
                      and f'at {repo.resolve()}' in r.stdout
                      and 'WRONG REPO' not in r.stderr,
                      r.stdout[:300] + failure_detail(r.stderr, 300)))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'budgets in force stay within the person\'s approvals, and the '
          f'session file\'s hard ceiling is a sum that must fit '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d_}" for n, d_ in bad))


def check_a_set_exports_only_its_own_rules():
    """A practice set hands on only the rules it writes
    (spec/A_SET_EXPORTS_ONLY_ITS_OWN_RULES.md, 2026-10-19). A repository that
    had Precedent installed like a project kept 209 copies of other sources'
    practices in the practices/ folder a set's consumers read as its own.

    1. The resolver leaves out a copy an install recorded in the set's
       MANIFEST.json -- byte-identical or stale -- and keeps the set's own.
    2. It leaves out a byte-identical copy with no MANIFEST.json (a hand
       copy); the weaker source's rule stays in force.
    3. NEGATIVE CONTROL: a set's real override, different text under the
       same slug, still replaces the weaker rule.
    4. The install step refuses to write into a set, before touching it.
    5. Update Vendors' copy-in refuses a set that holds an install's
       copies.
    6. The set-shape check (precedent_bootstrap_source.py --verify) reports
       them, and passes a set that holds none."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='set-own-rules-'))
    cases = []

    def rule(slug, body):
        return f'---\nslug: {slug}\n---\n# {slug}\n\n## Rule\n\n{body}\n'

    def make_source(name, level, files, manifest=None):
        d = tmp / name
        (d / 'practices').mkdir(parents=True)
        (d / 'precedent-source.json').write_text(json.dumps(
            {'name': name, 'level': level, 'visibility': 'public'}),
            encoding='utf-8')
        for slug, text in files.items():
            (d / 'practices' / f'{slug}.md').write_text(text, encoding='utf-8')
        if manifest is not None:
            (d / 'MANIFEST.json').write_text(json.dumps(
                {'generated_by': 'tools/precedent_materialize.py',
                 'practices': manifest}), encoding='utf-8')
        return d

    def host(hname, set_name):
        h = tmp / hname
        h.mkdir()
        (h / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'visibility': 'private', 'sources': [
                {'level': 'universal', 'name': 'precedent',
                 'path': str(tmp / 'precedent')},
                {'level': 'shared', 'name': set_name,
                 'path': str(tmp / set_name)}]}), encoding='utf-8')
        return h

    try:
        import precedent_resolve as pr
        import precedent_materialize as pm
        import checkin
        aa, bb = rule('aa', 'live aa'), rule('bb', 'live bb')
        make_source('precedent', 'universal', {'aa': aa, 'bb': bb})
        polluted = make_source(
            'zz-set', 'shared',
            {'zz-own': rule('zz-own', 'mine'), 'aa': aa,
             'bb': rule('bb', 'stale bb')},
            manifest=[{'slug': 'aa', 'source': 'precedent'},
                      {'slug': 'bb', 'source': 'precedent'},
                      {'slug': 'zz-own', 'source': 'zz-set'}])
        make_source('zz-hand', 'shared',
                    {'aa': aa, 'bb': rule('bb', 'a real override')})
        cfg = str(tmp / 'no-config.json')

        def resolve(h):
            srcs = [s for s in pr.load_config(str(h), user_config=cfg)
                    if s['name'] in ('precedent', 'zz-set', 'zz-hand')]
            return srcs, pr.resolve(srcs)

        srcs, res = resolve(host('h1', 'zz-set'))
        got = {s: p['source'] for s, p in res['practices'].items()}
        cases.append(('copies an install recorded in the set are left out, '
                      'stale or not; the set keeps its own rule',
                      got == {'aa': 'precedent', 'bb': 'precedent',
                              'zz-own': 'zz-set'}
                      and sorted(c['slug'] for c in res['copies']) == ['aa', 'bb']
                      and 'left out 2' in pr.copies_note(res['copies']),
                      f'{got} / {res.get("copies")}'))
        _s2, res2 = resolve(host('h2', 'zz-hand'))
        got2 = {s: p['source'] for s, p in res2['practices'].items()}
        cases.append(('a byte-identical hand copy is left out; the original '
                      'stays in force',
                      got2.get('aa') == 'precedent'
                      and [c['slug'] for c in res2['copies']] == ['aa'],
                      f'{got2} / {res2.get("copies")}'))
        cases.append(('NEGATIVE CONTROL: a real override under the same slug '
                      'still replaces the weaker rule',
                      got2.get('bb') == 'zz-hand', repr(got2)))

        before = sorted(f.name for f in (polluted / 'practices').iterdir())
        uni = [s for s in srcs if s['name'] == 'precedent']
        try:
            pm._materialize(uni, pr.resolve(uni), polluted)
            refused, why = False, 'materialized into a set'
        except pm.MaterializeError as e:
            refused, why = 'precedent-source.json' in str(e), str(e)
        after = sorted(f.name for f in (polluted / 'practices').iterdir())
        cases.append(('the install step refuses to write into a practice '
                      'set, and leaves it as it was',
                      refused and before == after, why[:300]))

        old = (checkin.SOURCE, checkin.SET_ROOT)
        checkin.SOURCE, checkin.SET_ROOT = 'zz-set', ''
        try:
            checkin._refuse_set_holding_copies(polluted)
            exited = 'not refused'
        except SystemExit as e:
            exited = str(e)
        try:
            checkin._refuse_set_holding_copies(tmp / 'zz-hand')
            clean_ok = True
        except SystemExit:
            clean_ok = False
        finally:
            checkin.SOURCE, checkin.SET_ROOT = old
        cases.append(("Update Vendors' copy-in refuses a set holding an "
                      "install's copies, and takes one that holds none",
                      'holds 2 practice(s)' in exited and clean_ok, exited[:300]))
        import precedent_bootstrap_source as pbs
        bad = [m for m in pbs._malformed('shared', polluted)
               if 'an install copied in' in m]
        good = [m for m in pbs._malformed('shared', tmp / 'zz-hand')
                if 'an install copied in' in m]
        cases.append(('the set-shape check reports a set holding copies, and '
                      'not one that holds none',
                      len(bad) == 1 and 'holds 2 practice(s)' in bad[0]
                      and not good, repr(bad + good)))
    except Exception as e:                                   # noqa: BLE001
        cases.append(('the test ran', False, f'{type(e).__name__}: {e}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in cases:
        check(f'a set exports only its own rules: {name}', ok,
              '' if ok else str(detail)[:500])


def check_copied_set_carries_another():
    """A copied set may carry a second set inside it -- a voice pack and the
    writing rules it is built on (spec/VENDORED_SHARED_SETS.md, 2026-10-19).

    1. Update Vendors' copy brings the carried set along with its carrier.
    2. The resolver puts the carried set in force, once, at its place in
       the copy; a person who brings the same set gets the carried one.
    3. A repository that declares the same set itself keeps its own: one
       copy in force, the repository's (and the freshness line says the
       carried one is not in force).
    4. NEGATIVE CONTROL: a `carries` path that leaves the set is ignored.
    5. A private set carried by a public one is refused into a repository
       not declared private."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='carried-sets-'))
    cases = []
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@t',
           'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@t',
           'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}

    def git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a], env=env,
                              capture_output=True, text=True)

    def rule(d, slug):
        (d / 'practices').mkdir(parents=True, exist_ok=True)
        (d / 'practices' / f'{slug}.md').write_text(
            f'---\nslug: {slug}\n---\n# {slug}\n\n## Rule\n\nx\n',
            encoding='utf-8')

    def make_pack(name, inner_vis, carries):
        origin = tmp / f'{name}.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main',
                        str(origin)], env=env, check=True)
        clone = tmp / name
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)],
                       env=env, capture_output=True, check=True)
        rule(clone, 'zz-pack-rule')
        rule(clone / 'inner', 'zz-inner-rule')
        (clone / 'inner' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-inner', 'level': 'shared', 'visibility': inner_vis}),
            encoding='utf-8')
        (clone / 'precedent-source.json').write_text(json.dumps(
            {'name': name, 'level': 'shared', 'visibility': 'public',
             'carries': carries}), encoding='utf-8')
        git(clone, 'add', '-A')
        git(clone, 'commit', '-qm', 'one')
        git(clone, 'push', '-q', 'origin', 'main')
        return clone

    def make_host(hname, name, extra=(), visibility=None):
        host = tmp / hname
        (host / 'process').mkdir(parents=True)
        cfg = {'format_version': 1, 'sources': [
            {'name': name, 'level': 'shared', 'path': f'process/{name}',
             'vendored': True}, *extra]}
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

    def take(host, name, clone):
        out = ''
        for verb, flags in (('update', ['--force']), ('record', [])):
            r = subprocess.run(
                [sys.executable, str(ROOT / 'tools' / 'checkin.py'), '--source',
                 name, '--repo', str(host), verb, str(clone), *flags],
                env=env, capture_output=True, text=True)
            out += r.stdout[-300:] + r.stderr[-300:]
            if r.returncode != 0:
                return False, out
        return True, out

    try:
        import precedent_resolve as pr
        carries = [{'name': 'zz-inner', 'path': 'inner'}]
        pack = make_pack('zz-pack', 'public', carries)
        host = make_host('host', 'zz-pack')
        ok, out = take(host, 'zz-pack', pack)
        inner = host / 'process' / 'zz-pack' / 'inner'
        cases.append(('the copy brings the carried set along',
                      ok and (inner / 'practices' / 'zz-inner-rule.md').is_file()
                      and (inner / 'precedent-source.json').is_file(), out))
        srcs = pr.load_config(str(host), user_config=str(tmp / 'no-config.json'))
        mine = [s for s in srcs if s['name'] == 'zz-inner']
        cases.append(('the carried set is in force, once, at its place in the copy',
                      len(mine) == 1 and pathlib.Path(mine[0]['path'])
                      == inner.resolve() and mine[0].get('carried_by') == 'zz-pack',
                      repr(mine)))

        # A pack with no rules of its own (a voice pack: all its rules are
        # the set it carries) is not an empty source to the sync
        # (2026-10-19, the first voice pack copied into a repository).
        own = host / 'process' / 'zz-pack' / 'practices' / 'zz-pack-rule.md'
        own.unlink()
        senv = {**env, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-config.json')}
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                            '--repo', str(host), '--check'],
                           env=senv, capture_output=True, text=True)
        cases.append(('a pack whose only rules are the set it carries is not '
                      'refused as empty',
                      'contributed no practices' not in r.stdout + r.stderr,
                      failure_detail(r.stdout + r.stderr, 500)))
        # NEGATIVE CONTROL: with the carried set's rules gone too, it is.
        (inner / 'practices' / 'zz-inner-rule.md').unlink()
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                            '--repo', str(host), '--check'],
                           env=senv, capture_output=True, text=True)
        cases.append(('NEGATIVE CONTROL: a pack that carries an empty set is '
                      'still refused as empty',
                      'contributed no practices' in r.stdout + r.stderr,
                      failure_detail(r.stdout + r.stderr, 500)))
        rule(host / 'process' / 'zz-pack', 'zz-pack-rule')
        rule(inner, 'zz-inner-rule')

        ind = tmp / 'people' / 'zz-ind'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [
                {'name': 'zz-inner',
                 'repo_url': 'https://example.invalid/zz-inner'}]}),
            encoding='utf-8')
        rule(ind.parent / 'zz-inner', 'zz-inner-rule')
        ucfg = tmp / 'person.json'
        ucfg.write_text(json.dumps({'individual': {'name': 'zz-ind',
                                                   'path': str(ind)}}))
        srcs = pr.load_config(str(host), user_config=str(ucfg))
        mine = [s for s in srcs if s['name'] == 'zz-inner']
        cases.append(('a person who brings the carried set gets the carried copy',
                      len(mine) == 1 and pathlib.Path(mine[0]['path'])
                      == inner.resolve(), repr(mine)))

        own = tmp / 'own-inner'
        rule(own, 'zz-inner-rule')
        cfg = json.loads((host / 'precedent.json').read_text())
        cfg['sources'].append({'name': 'zz-inner', 'level': 'shared',
                               'path': str(own)})
        (host / 'precedent.json').write_text(json.dumps(cfg))
        srcs = pr.load_config(str(host), user_config=str(tmp / 'no-config.json'))
        mine = [s for s in srcs if s['name'] == 'zz-inner']
        cases.append(('a repository that declares the carried set keeps its own',
                      len(mine) == 1 and pathlib.Path(mine[0]['path'])
                      == own.resolve(), repr(mine)))
        r = subprocess.run([sys.executable, str(ROOT / 'tools' /
                            'precedent_engine_freshness.py')], cwd=str(host),
                           env=env, capture_output=True, text=True)
        cases.append(('the freshness line says the carried copy is not in force',
                      'carried at' in r.stdout and 'not in force here' in r.stdout,
                      failure_detail(r.stdout, 600)))

        esc = tmp / 'escape-pack'
        rule(esc, 'zz-pack-rule')
        rule(tmp / 'outside', 'zz-out-rule')
        (esc / 'precedent-source.json').write_text(json.dumps(
            {'name': 'escape-pack', 'level': 'shared', 'visibility': 'public',
             'carries': [{'name': 'zz-out', 'path': '../outside'}]}))
        got = pr.carried_sources(esc, 'escape-pack')
        cases.append(('NEGATIVE CONTROL: a carries path that leaves the set is '
                      'ignored', got == [], repr(got)))

        priv = make_pack('zz-priv-pack', 'private', carries)
        open_host = make_host('open-host', 'zz-priv-pack')
        ok, out = take(open_host, 'zz-priv-pack', priv)
        cases.append(('a private set carried by a public one is refused into a '
                      'repository not declared private',
                      not ok and 'private' in out
                      and not (open_host / 'process' / 'zz-priv-pack').exists(),
                      out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if 'checkin' in sys.modules:
            import importlib
            importlib.reload(sys.modules['checkin'])
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a copied set carries another inside it, and the repository\'s own '
          f'declaration wins ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_exports_only_copy_resolves():
    """A source copied in for its exports alone ("vendored": true,
    "exports_only": true) has no practices/ folder by design, and is
    resolved when its exported files are there (Morgan, 2026-10-30: every
    session start in a voice repository reported its two present, current
    copies as missing, with "run Update Vendors").

    1. An exports-only copy holding its exports and no practices/ is not
       reported unresolved.
    2. The same declaration with its folder gone IS reported, with the
       Update Vendors wording. NEGATIVE CONTROL for case 1: the test reads
       the guard's own words, so a reader that skipped exports-only copies
       outright would fail here.
    3. A full copy with no practices/ is still reported, so the change did
       not loosen the test for a practice source."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='exports-only-resolves-'))
    cases = []
    try:
        host = tmp / 'host'
        voice = host / 'process' / 'zz-voicey'
        (voice / 'essentials').mkdir(parents=True)
        (voice / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-voicey', 'level': 'shared',
             'exports': ['PROMPT.md', 'essentials']}))
        (voice / 'PROMPT.md').write_text('the compiled prompt\n')
        rules = host / 'process' / 'zz-rulesy'
        rules.mkdir(parents=True)
        (rules / 'RULES.md').write_text('rule one\n')

        def declare(sources):
            (host / 'precedent.json').write_text(json.dumps(
                {'format_version': 1, 'sources': sources}, indent=2))

        def entry(name, **kw):
            return {'level': 'shared', 'name': name,
                    'path': f'process/{name}', 'vendored': True, **kw}

        env = {'CLAUDE_CODE_REMOTE': 'true',
               'PRECEDENT_USER_CONFIG': str(tmp / 'no-person.json')}

        def shared(srcs):
            declare(srcs)
            return [(n, why) for lvl, n, why
                    in psc.unresolved_private_sources(host, env)
                    if lvl == 'shared']

        got = shared([entry('zz-voicey', exports_only=True),
                      entry('zz-rulesy', exports_only=True,
                            exports=['RULES.md'])])
        cases.append(('an exports-only copy with its exports and no practices/ '
                      'resolves', got == [], repr(got)))
        shutil.rmtree(voice)
        got = shared([entry('zz-voicey', exports_only=True)])
        cases.append(('the same copy with its folder gone is reported, with the '
                      'Update Vendors wording',
                      len(got) == 1 and got[0][0] == 'zz-voicey'
                      and 'run Update Vendors to make the copy' in got[0][1],
                      repr(got)))
        got = shared([entry('zz-rulesy')])
        cases.append(('a full copy with no practices/ is still reported',
                      [n for n, _ in got] == ['zz-rulesy']
                      and 'run Update Vendors to make the copy' in got[0][1],
                      repr(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # clone_elsewhere finds a clone whose folder spells the name differently.
    import precedent_resolve as pr
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='clone-elsewhere-case-'))
    try:
        (tmp / 'MixedCaseZ' / '.git').mkdir(parents=True)
        got = pr.clone_elsewhere('mixedcasez', str(tmp / 'mixedcasez'),
                                 any_clone=True)
        cases.append(('clone_elsewhere finds ../MixedCaseZ for a source named '
                      '"mixedcasez"', got == tmp / 'MixedCaseZ', repr(got)))
        got = pr.clone_elsewhere('nosuchz', str(tmp / 'nosuchz'),
                                 any_clone=True)
        cases.append(('NEGATIVE CONTROL: no folder of any spelling is None',
                      got is None, repr(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check('an exports-only copied-in source resolves without practices/',
          not bad, f'{len(cases)} stated cases',
          '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


def check_worktree_resolves_sources_beside_its_main_checkout():
    """precedent_resolve.load_config() from a LINKED worktree under the temp
    directory resolves a relative source path beside the main checkout when
    it does not resolve beside the worktree (2026-09-29). The merge check,
    Promote's batch and the push check's base all check a commit in such a
    worktree; from there `../<set>` named nothing, a set's practice in force
    in the repository read as not in force, and a consuming repo's merge
    check refused a pull request its checkout passed. Stated cases, with the
    control that a plain copy (not a worktree) gets no such fallback, and the
    network self-heal switched off so the answer is the resolver's alone."""
    import tempfile
    base = pathlib.Path(tempfile.mkdtemp(prefix='wt-sources-'))
    cases = []
    try:
        main, src = base / 'consumer', base / 'zzz-src'
        (src / 'practices').mkdir(parents=True)
        (src / 'practices' / 'zzz-rule.md').write_text(
            '---\nslug: zzz-rule\nstatus: active\n---\n## Rule\nx\n', encoding='utf-8')
        (src / 'precedent-source.json').write_text(
            json.dumps({'name': 'zzz-src', 'level': 'shared'}), encoding='utf-8')
        main.mkdir()
        (main / 'precedent.json').write_text(json.dumps(
            {'format_version': 1, 'sources': [
                {'level': 'shared', 'name': 'zzz-src', 'path': '../zzz-src'}]}),
            encoding='utf-8')
        g = ['git', '-c', 'user.name=h', '-c', 'user.email=h@example.com']
        subprocess.run([*g, 'init', '-q', str(main)], capture_output=True)
        subprocess.run([*g, '-C', str(main), 'add', '-A'], capture_output=True)
        subprocess.run([*g, '-C', str(main), 'commit', '-qm', 'x'], capture_output=True)
        far = pathlib.Path(tempfile.mkdtemp(prefix='wt-far-'))
        wt = far / 'tree'
        subprocess.run(['git', '-C', str(main), 'worktree', 'add', '-q', '--detach',
                        str(wt), 'HEAD'], capture_output=True)
        copy = far / 'copy'
        shutil.copytree(main, copy)
        env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_CODE_REMOTE'}
        env['PRECEDENT_USER_CONFIG'] = str(base / 'no-user-config.json')
        probe = ('import sys, json; sys.path.insert(0, sys.argv[1]); '
                 'import precedent_resolve as pr; '
                 'print(json.dumps([s["path"] for s in pr.load_config(sys.argv[2])]))')

        def paths(root):
            r = subprocess.run([sys.executable, '-c', probe, str(ROOT / 'tools'),
                                str(root)], capture_output=True, text=True, env=env)
            try:
                return json.loads(r.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                return r.stdout + r.stderr
        want = str(src.resolve())
        got = paths(wt)
        cases.append(('a worktree under the temp directory resolves ../zzz-src '
                      'beside its main checkout', isinstance(got, list)
                      and want in got, got))
        got = paths(main)
        cases.append(('the main checkout resolves it as before',
                      isinstance(got, list) and want in got, got))
        got = paths(copy)
        cases.append(('CONTROL: a plain copy is not a worktree and gets no '
                      'fallback', isinstance(got, list) and want not in got, got))
        subprocess.run(['git', '-C', str(main), 'worktree', 'remove', '--force',
                        str(wt)], capture_output=True)
        shutil.rmtree(far, ignore_errors=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a worktree resolves relative sources beside its main checkout '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_individual_source_bootstrap_self_heals():
    """practices/session-bootstrap.md's Detail, tested rather than trusted
    -- and corrected 2026-09-06 after this check's own first version
    proved a false claim clean.

    tools/precedent_resolve.py's own load_config() treats a still-missing
    individual config, on a remote session, as "try the hook once more"
    rather than "no individual set" -- this is the ENTIRE fix for the
    incident practices/session-bootstrap.md's Story records (two
    independent adopters' SessionStart hook running to completion before
    the agent's own turn, and therefore its add_repo call, could start).
    A first version of this check also asserted that
    tools/precedent_source_bootstrap.py retrying "instead of trying once"
    was a second, contributing half. That was tested here only by calling
    the tool directly against synthetic fixtures -- never inside a real
    SessionStart hook on a genuinely fresh Claude Code Web session, which
    is the one environment where the claim was actually false: a
    SessionStart hook's execution window and the agent's own first turn
    never overlap in time, so no retry count or delay inside the hook can
    ever observe add_repo access appearing. A follow-up testing session
    ran that real test and disproved it directly. This check's own
    passing runs never caught that, and could not have: it proves the
    tool's CODE does what the code says (retries N times, degrades
    gracefully), which was never in question -- it cannot prove the
    premise about the outside world (whether a retry, in that specific
    execution context, has anything to retry into) the retry was written
    against. Case 6 below locks in the correction: the tool now defaults
    to a single attempt, precisely because a default of more than one
    bought nothing for the case it was sized for.

    Fixture: a real local git repo served over file:// -- not a bare path;
    this repo's own environment-gotchas.md already names why (`git clone
    --depth 1 /some/path` is ignored; only a real transport gets real
    clone semantics, and `file://` is what forces that locally). Six
    stated cases, all fast: --retry-delay 0 proves an explicitly-requested
    retry count without a real wall-clock wait."""
    import shutil, tempfile
    import precedent_source_credentials as psc
    import precedent_source_bootstrap as psb

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-source-bootstrap-'))
    cases = []
    try:
        bootstrap_tool = ROOT / 'tools' / 'precedent_source_bootstrap.py'
        resolve_tool = ROOT / 'tools' / 'precedent_resolve.py'

        def _no_credentials():
            env = dict(os.environ)
            env.pop(psc.TOKEN_ENV, None)
            env.pop(psb.BASE_URL_ENV, None)
            return env

        def run(*args, env_extra=None):
            # Same scrub as check_source_credentials's run(), for the same
            # reason: cases here assert what a bootstrap does with no
            # credential and no base url, and this harness runs in a
            # container that normally carries both
            # (practice: fixture-owns-its-state).
            env = dict(os.environ)
            env.pop(psc.TOKEN_ENV, None)
            env.pop(psb.BASE_URL_ENV, None)
            if env_extra is not None:
                env.update(env_extra)
            r = subprocess.run([sys.executable, *args], capture_output=True,
                               text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def git(cwd, *args):
            subprocess.run(['git', '-C', str(cwd), *args], check=True,
                           capture_output=True, text=True)

        # --- a real source repo, with one fixture practice -------------------
        source = tmp / 'source-repo'
        source.mkdir()
        git(source, 'init', '-q')
        git(source, 'config', 'user.email', 'harness@example.com')
        git(source, 'config', 'user.name', 'harness')
        (source / 'practices').mkdir()
        (source / 'practices' / 'example.md').write_text(
            '---\nslug: harness-fixture\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "testing"\n'
            'index_clause: "a harness fixture"\nchecked_by: null\n'
            'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
            'added: null\napproved_by: "harness"\n---\n\n## Rule\nFixture.\n\n'
            '## Detail\n\n## Why\n\n## Story\n\n## Install\n', encoding='utf-8')
        git(source, 'add', '-A')
        git(source, 'commit', '-qm', 'seed')
        source_url = f'file://{source}'

        # --- case 1+2: reachable, cloned then pulled (idempotent) -----------
        # `--remote-only false` makes this hermetic: main()'s own default
        # (--remote-only true) no-ops the whole tool unless the AMBIENT
        # CLAUDE_CODE_REMOTE env var happens to already be 'true' -- true in
        # the Claude Code Remote session this was authored and verified in,
        # never true on a plain GitHub Actions runner, so this fixture
        # deterministically passed nothing and asserted on files that were
        # never written the first time this ran in CI. Case 4 below already
        # sets CLAUDE_CODE_REMOTE explicitly for the same reason, applied
        # here to the tool's own direct invocations instead.
        clone, config = tmp / 'clone', tmp / 'config.json'
        rc, out = run(str(bootstrap_tool), '--level', 'individual',
                     '--name', 'precedent-individual', '--repo-url', source_url,
                     '--clone', str(clone), '--config', str(config),
                     '--retries', '3', '--retry-delay', '0',
                     '--remote-only', 'false')
        cases.append(('a reachable source is cloned and the config written on '
                      'the first attempt',
                      rc == 0 and (clone / 'practices' / 'example.md').is_file()
                      and json.loads(config.read_text()).get('individual', {}).get('name')
                      == 'precedent-individual', out))

        rc2, out2 = run(str(bootstrap_tool), '--level', 'individual',
                        '--name', 'precedent-individual', '--repo-url', source_url,
                        '--clone', str(clone), '--config', str(config),
                        '--retries', '3', '--retry-delay', '0',
                        '--remote-only', 'false')
        cases.append(('running it again against an already-cloned source pulls '
                      'rather than re-cloning (idempotent)', rc2 == 0, out2))

        # --- case 3: unreachable -- retries the stated number, then degrades,
        # never fails, never writes a config -------------------------------
        rc3, out3 = run(str(bootstrap_tool), '--level', 'individual',
                        '--name', 'precedent-individual',
                        '--repo-url', f'file://{tmp / "does-not-exist"}',
                        '--clone', str(tmp / 'clone-unreachable'),
                        '--config', str(tmp / 'config-unreachable.json'),
                        '--retries', '3', '--retry-delay', '0',
                        '--remote-only', 'false')
        cases.append(('an unreachable source retries the stated number of '
                      'times, then exits 0 and writes no config',
                      rc3 == 0 and not (tmp / 'config-unreachable.json').exists()
                      and 'after 3 attempt' in out3, out3))

        # --- case 6 (2026-09-06 correction): the DEFAULT is a single
        # attempt, with no --retries/--retry-delay given at all -- locks in
        # the corrected understanding that a multi-attempt default bought
        # nothing for the SessionStart-hook case it was originally sized
        # for (see this function's own docstring). A regression back to a
        # default > 1 would silently reintroduce the exact wasted latency
        # this correction removed, on every cold session, for zero benefit.
        rc6, out6 = run(str(bootstrap_tool), '--level', 'individual',
                        '--name', 'precedent-individual',
                        '--repo-url', f'file://{tmp / "does-not-exist"}',
                        '--clone', str(tmp / 'clone-unreachable-default'),
                        '--config', str(tmp / 'config-unreachable-default.json'),
                        '--remote-only', 'false')
        cases.append(('with no --retries given, the tool defaults to exactly '
                      'one attempt', rc6 == 0 and 'after 1 attempt' in out6, out6))

        # --- case 4: the resolver's own lazy self-heal, on a remote session -
        consumer = tmp / 'consumer'
        (consumer / '.claude' / 'hooks').mkdir(parents=True)
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}],
        }), encoding='utf-8')
        hook = consumer / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        hook.write_text(
            '#!/bin/bash\nset -uo pipefail\n'
            'if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then exit 0; fi\n'
            f'python3 "{bootstrap_tool}" --level individual '
            f'--name precedent-individual --repo-url "{source_url}" '
            '--clone "$HOME/precedent-individual" '
            '--config "$HOME/.config/precedent/config.json" '
            '--retries 3 --retry-delay 0\n', encoding='utf-8')
        hook.chmod(0o755)

        home_remote = tmp / 'home-remote'
        home_remote.mkdir()
        rc4, out4 = run(str(resolve_tool), '--repo', str(consumer), '--json',
                        env_extra={'HOME': str(home_remote),
                                   'CLAUDE_CODE_REMOTE': 'true',
                                   'PRECEDENT_USER_CONFIG':
                                       str(home_remote / '.config' / 'precedent' / 'config.json')})
        resolved4 = {}
        try:
            resolved4 = json.loads(out4)
        except json.JSONDecodeError:
            pass
        cases.append(('on a remote session with the config absent, resolve '
                      'self-heals via the hook and finds the individual '
                      'source afterward',
                      rc4 == 0 and any(p['slug'] == 'harness-fixture'
                                       for p in resolved4.get('practices', [])), out4))

        # --- case 5: the same absence, off a remote session, self-heals NOT -
        home_local = tmp / 'home-local'
        home_local.mkdir()
        env_local = dict(os.environ)
        env_local.pop('CLAUDE_CODE_REMOTE', None)
        env_local['HOME'] = str(home_local)
        env_local['PRECEDENT_USER_CONFIG'] = str(home_local / '.config' / 'precedent' / 'config.json')
        r5 = subprocess.run([sys.executable, str(resolve_tool), '--repo', str(consumer), '--json'],
                            capture_output=True, text=True, env=env_local)
        resolved5 = {}
        try:
            resolved5 = json.loads(r5.stdout)
        except json.JSONDecodeError:
            pass
        cases.append(('without CLAUDE_CODE_REMOTE, resolve does NOT invoke the '
                      'hook -- a local machine with genuinely no individual '
                      'set stays silent, not self-healed',
                      r5.returncode == 0
                      and not any(p['slug'] == 'harness-fixture'
                                  for p in resolved5.get('practices', []))
                      and not (home_local / '.config').exists(),
                      r5.stdout + r5.stderr))

        # --- cases 6-8: "no individual set" vs "could not find out" --------
        # The silence these close: before 2026-09-06 an undeclared individual
        # source was appended to nothing, so it reached neither `sources` nor
        # `missing`, and a hosted session that had no way to look printed the
        # same confident summary as a laptop that genuinely has none.
        # run() returns stdout + stderr concatenated, and the whole point of
        # this fix is that these runs now PRINT a notice on stderr -- so the
        # JSON is a prefix of the captured text, not the whole of it.
        def _json_prefix(text):
            try:
                return json.JSONDecoder().raw_decode(text.lstrip())[0]
            except (json.JSONDecodeError, ValueError):
                return {}

        cases.append(('a resolved individual source reports no '
                      'individual_status finding -- its fate belongs in '
                      '`missing` like any other declared source',
                      (_json_prefix(out4) or {}).get('individual_status') is None,
                      out4))

        nohook = tmp / 'consumer-nohook'
        nohook.mkdir()
        (nohook / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}],
        }), encoding='utf-8')
        home6 = tmp / 'home-nohook'
        home6.mkdir()
        rc6b, out6b = run(str(resolve_tool), '--repo', str(nohook), '--json',
                          env_extra={'HOME': str(home6), 'PRECEDENT_INDIVIDUAL_REPO': 'file:///fixture/precedent-individual',
                                     'CLAUDE_CODE_REMOTE': 'true',
                                     'PRECEDENT_USER_CONFIG':
                                         str(home6 / 'config.json')})
        st6 = (_json_prefix(out6b) or {}).get('individual_status') or {}
        cases.append(('on a remote session whose project ships no bootstrap '
                      'hook, resolve reports that it could NOT determine '
                      'whether an individual set exists, rather than implying '
                      'there is none',
                      st6.get('certain') is False
                      and st6.get('code') == 'no-bootstrap-hook', out6b))

        r7 = subprocess.run([sys.executable, str(resolve_tool), '--repo',
                             str(nohook), '--json'],
                            capture_output=True, text=True, env=env_local)
        st7 = (_json_prefix(r7.stdout) or {}).get('individual_status') or {}
        cases.append(('off a remote session, an absent user config IS a '
                      'definite "no individual practices" -- $HOME is the '
                      "person's own machine, so there is nothing to find out",
                      st7.get('certain') is True
                      and st7.get('code') == 'no-config-file',
                      r7.stdout + r7.stderr))

        declares_none = home6 / 'declares-none.json'
        declares_none.write_text('{"individual": null}', encoding='utf-8')
        rc8, out8 = run(str(resolve_tool), '--repo', str(nohook), '--json',
                        env_extra={'HOME': str(home6),
                                   'CLAUDE_CODE_REMOTE': 'true',
                                   'PRECEDENT_USER_CONFIG': str(declares_none)})
        st8 = (_json_prefix(out8) or {}).get('individual_status') or {}
        cases.append(('a user config that exists and declares no individual '
                      'source is a definite answer, even on a remote session',
                      st8.get('certain') is True
                      and st8.get('code') == 'config-declares-none', out8))

        # No sign anywhere of an individual set -- no token, base URL, repo
        # name or clone -- is a definite "none" even on a remote session with
        # no hook and no user config: nothing could have fetched one.
        rc8b, out8b = run(str(resolve_tool), '--repo', str(nohook), '--json',
                          env_extra={'HOME': str(home6),
                                     'CLAUDE_CODE_REMOTE': 'true',
                                     'PRECEDENT_USER_CONFIG':
                                         str(home6 / 'absent.json')})
        st8b = (_json_prefix(out8b) or {}).get('individual_status') or {}
        cases.append(('with no sign of an individual set, a remote session '
                      'with no user config reports a definite "none"',
                      st8b.get('certain') is True
                      and st8b.get('code') == 'no-individual-signal'
                      and 'could not find out' not in out8b, out8b))

        # --- cases 9-11: BestPractice as a CONSUMER of its own instructions -
        # The root cause of the hook being absent here for as long as it was:
        # this repo is treated as the publisher, so every case above builds a
        # fixture consumer and asserts things about IT. Nothing asserted the
        # publisher follows the install steps it publishes. These do.
        own_hook = ROOT / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        cases.append(('this repo carries the individual-source bootstrap hook '
                      'it tells every adopter to install, and it is executable',
                      own_hook.is_file() and os.access(own_hook, os.X_OK),
                      f'{own_hook} is_file={own_hook.is_file()}'))

        # The property that makes committing it safe, and the reason it was
        # left out as "must not be committed blind": a SessionStart hook must
        # never block a session, so it has to exit 0 even when its whole job
        # is impossible. Run here with a HOME that has nothing and no git
        # credentials -- exactly a session without access to the private set.
        home_hook = tmp / 'home-own-hook'
        home_hook.mkdir()
        rh = subprocess.run(['bash', str(own_hook)], capture_output=True,
                            text=True, timeout=180,
                            env={**_no_credentials(), 'HOME': str(home_hook),
                                 'CLAUDE_PROJECT_DIR': str(ROOT),
                                 'CLAUDE_CODE_REMOTE': 'true'})
        cases.append(("this repo's own bootstrap hook exits 0 when it cannot "
                      'reach the individual set -- a session-start hook that '
                      'fails must never block the session',
                      rh.returncode == 0, rh.stdout + rh.stderr))

        # And the CLI route that writes it. Until 2026-09-06 --write-session-hook
        # was reachable only after bootstrap() created a whole individual set,
        # so the documented "run it again against an already-bootstrapped set"
        # could not be run -- which is why this repo went without the hook.
        hook_only_proj = tmp / 'hook-only-project'
        hook_only_proj.mkdir()
        rc9, out9 = run(str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                        '--level', 'individual', '--name', 'precedent-individual',
                        '--write-session-hook', str(hook_only_proj),
                        '--repo-url', 'https://example.invalid/precedent-individual')
        written_hook = hook_only_proj / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        cases.append(('--write-session-hook writes the hook with no --dest and '
                      'creates no individual set -- the documented '
                      '"run it again against an already-bootstrapped set"',
                      rc9 == 0 and written_hook.is_file()
                      and not (hook_only_proj / 'practices').exists(),
                      out9))

        # --- cases 12-14: THE INSTANTIATED HOOK ACTUALLY RUNS ---------------
        # Case 9 above asserted the file exists, which is the whole reason
        # the defect below survived to a real install. It did not assert the
        # file WORKS, and it did not: the template guarded "still a raw
        # template?" by testing $REPO_URL against the source-repo-url
        # placeholder, and the substituter rewrote that occurrence along
        # with every other, so an instantiated hook compared the real URL
        # against itself and took the "no repository URL" exit on every
        # session while holding the correct URL. Silent, and inert at every
        # layer -- precedent_resolve.py's self-heal re-invokes this same
        # hook, so it short-circuited too. Found 2026-09-10 installing
        # precedent-beta-v01 into a real project, not by anything here.
        #
        # These three assert the property that was missing: instantiated
        # with a real URL the hook REACHES ITS EXEC and does the clone;
        # instantiated with none it still degrades quietly; and the raw
        # template, run as-is, must not mistake its own placeholder for a
        # URL and try to clone it.
        live_proj = tmp / 'live-hook-project'
        live_proj.mkdir()
        rc12, out12 = run(str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                          '--level', 'individual', '--name', 'precedent-individual',
                          '--write-session-hook', str(live_proj),
                          '--repo-url', source_url)
        live_hook = live_proj / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        live_home = tmp / 'home-live-hook'
        live_home.mkdir()
        r12 = subprocess.run(['bash', str(live_hook)], capture_output=True,
                             text=True, timeout=180,
                             env={**_no_credentials(), 'HOME': str(live_home),
                                  'CLAUDE_PROJECT_DIR': str(ROOT),
                                  'CLAUDE_CODE_REMOTE': 'true'})
        live_cfg = live_home / '.config' / 'precedent' / 'config.json'
        cases.append(('a hook instantiated with a REAL --repo-url reaches its '
                      'exec and clones -- it does not mistake the substituted '
                      'URL for an unsubstituted placeholder',
                      rc12 == 0 and r12.returncode == 0
                      and 'no repository URL' not in (r12.stdout + r12.stderr)
                      and (live_home / 'precedent-individual' / 'practices'
                           / 'example.md').is_file()
                      and live_cfg.is_file(),
                      out12 + r12.stdout + r12.stderr))

        nourl_proj = tmp / 'no-url-hook-project'
        nourl_proj.mkdir()
        rc13, out13 = run(str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                          '--level', 'individual', '--name', 'precedent-individual',
                          '--write-session-hook', str(nourl_proj))
        nourl_hook = nourl_proj / '.claude' / 'hooks' / 'precedent-individual-bootstrap.sh'
        nourl_home = tmp / 'home-no-url-hook'
        nourl_home.mkdir()
        # The hook DERIVES its URL from the base url when no URL was baked
        # in, so a fixture asserting "it degrades quietly when nothing else
        # supplies one" has to be the thing that establishes "nothing else
        # supplies one". Inheriting the container's own base url made this
        # case assert the opposite of what it ran (2026-09-11).
        r13 = subprocess.run(['bash', str(nourl_hook)], capture_output=True,
                             text=True, timeout=180,
                             env={**_no_credentials(), 'HOME': str(nourl_home),
                                  'CLAUDE_PROJECT_DIR': str(ROOT),
                                  'CLAUDE_CODE_REMOTE': 'true'})
        cases.append(('--write-session-hook with NO --repo-url still writes a '
                      'fully instantiated hook -- the shape a PUBLIC consumer '
                      'needs, since the baked-in URL is tracked -- and that '
                      'hook degrades quietly when nothing else supplies one',
                      rc13 == 0 and nourl_hook.is_file()
                      and r13.returncode == 0
                      and 'no repository URL' in (r13.stdout + r13.stderr),
                      out13 + r13.stdout + r13.stderr))

        raw_template = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
                        / 'individual-source-bootstrap.sh.template')
        raw_home = tmp / 'home-raw-template'
        raw_home.mkdir()
        stray = pathlib.Path('/home/user/{{SOURCE_NAME}}')
        stray_before = os.path.lexists(stray)
        r14 = subprocess.run(['bash', str(raw_template)], capture_output=True,
                             text=True, timeout=180,
                             env={**_no_credentials(), 'HOME': str(raw_home),
                                  'CLAUDE_PROJECT_DIR': str(ROOT),
                                  'CLAUDE_CODE_REMOTE': 'true'})
        cases.append(('the RAW template, run without being instantiated, still '
                      'recognises itself as uninstantiated and exits 0 without '
                      'trying to clone its own placeholder',
                      r14.returncode == 0
                      and 'no repository URL' in (r14.stdout + r14.stderr),
                      r14.stdout + r14.stderr))
        # ...and sets nothing up: a run that derived a URL from the
        # environment once cloned and linked a path named after the
        # placeholder, outside the fixture (2026-10-01).
        cases.append(('...and creates nothing named after its placeholder, in '
                      'the fixture or outside it',
                      not any('{{' in q.name for q in raw_home.rglob('*'))
                      and (stray_before or not os.path.lexists(stray)),
                      r14.stdout + r14.stderr))

        # NO COMMENT IN THE TEMPLATE MAY SPELL A PLACEHOLDER OUT. The same
        # bug one layer out, and the one that made the first fix's own
        # explanation unreadable: the substituter rewrites comments too, so
        # prose naming a placeholder comes out of instantiation as prose
        # naming the value -- "<the real URL> is substituted at install time
        # with a real URL". Assert the rule directly on the template rather
        # than on any one instantiation of it: every literal {{...}} sits on
        # a line that is actually substituted, never in a comment.
        raw_text = raw_template.read_text(encoding='utf-8')
        commented_placeholders = [
            ln for ln in raw_text.splitlines()
            if '{{' in ln and ln.lstrip().startswith('#')]
        cases.append(('no comment in the hook template spells a placeholder '
                      'out -- substitution rewrites comments too, so such a '
                      'line instantiates into nonsense',
                      not commented_placeholders,
                      '; '.join(commented_placeholders)))

        # And the publisher's own copy is a real instantiation, not a
        # fixture: nothing unsubstituted may survive in it.
        own_hook_text = own_hook.read_text(encoding='utf-8')
        cases.append(("this repo's own instantiated hook carries no leftover "
                      'placeholder', '{{' not in own_hook_text,
                      own_hook_text[:400]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the resolver self-heals (the actual fix); the bootstrap tool '
          f'defaults to one attempt and still honors an explicit retry count '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_a_set_in_a_linked_worktree_does_not_load_itself_twice():
    """A set the individual set brings is left out when it IS the repository
    being resolved -- in a linked worktree of it too (2026-10-17 very deep
    check: precedent_resolve compared paths only, so the ladder set in a
    worktree loaded itself a second time from its main checkout, 3,801
    words of session load against 3,399 in the clone; --land and the merge
    gate check in throwaway worktrees).

    Stated cases: in the clone the brought copy is left out (control); in a
    linked worktree of the same set it is left out too; a different set
    beside it is still brought."""
    import shutil, tempfile
    import precedent_resolve as pr
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-wt-self-'))
    cases = []

    def git(repo, *a):
        return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C',
                               str(repo), *a], capture_output=True, text=True)

    def practice(d, slug):
        (d / 'practices').mkdir(parents=True, exist_ok=True)
        (d / 'practices' / f'{slug}.md').write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
            f'index_clause: "x"\nstatus: active\n---\n## Rule\nx\n\n## Story\nx\n',
            encoding='utf-8')

    try:
        ind, ladder, other = tmp / 'zz-ind', tmp / 'zz-ladder', tmp / 'zz-other'
        practice(ind, 'zz-ind-rule')
        (ind / 'precedent-source.json').write_text(json.dumps({
            'name': 'zz-ind', 'level': 'individual', 'brings': [
                {'name': 'zz-ladder', 'repo_url': 'https://example.com/zz-ladder'},
                {'name': 'zz-other', 'repo_url': 'https://example.com/zz-other'}]}),
            encoding='utf-8')
        for s in (ladder, other):
            practice(s, f'{s.name}-rule')
            (s / 'precedent-source.json').write_text(json.dumps(
                {'name': s.name, 'level': 'shared'}), encoding='utf-8')
            (s / 'precedent.json').write_text(json.dumps({
                'format_version': 1, 'base_branch': 'main', 'sources': [
                    {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)}]}),
                encoding='utf-8')
            git(s, 'init', '-q', '-b', 'main')
            git(s, 'add', '-A')
            git(s, '-c', 'user.email=h@example.com', '-c', 'user.name=h',
                'commit', '-qm', 'fixture')
        wt = tmp / 'elsewhere' / 'zz-ladder-wt'
        wt.parent.mkdir()
        git(ladder, 'worktree', 'add', '-q', '-b', 'wt', str(wt))
        user = tmp / 'user.json'
        user.write_text(json.dumps({'format_version': 1, 'individual': {
            'name': 'zz-ind', 'path': str(ind)}}), encoding='utf-8')

        def brought(repo):
            os.environ[pr.SELF_HEAL_RENDER_ENV] = '1'   # no render from a fixture
            try:
                srcs = pr.load_config(str(repo), str(user))
            finally:
                os.environ.pop(pr.SELF_HEAL_RENDER_ENV, None)
            return sorted(s['name'] for s in srcs if s.get('brought'))

        got_clone, got_wt = brought(ladder), brought(wt)
        cases.append(('control: in the clone, the set does not bring itself',
                      got_clone == ['zz-other'], repr(got_clone)))
        cases.append(('in a linked worktree of the set, it does not bring itself '
                      'from its main checkout either', got_wt == ['zz-other'],
                      repr(got_wt)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a set resolved in a linked worktree of itself does not load itself '
          f'twice ({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_stale_render_heal_never_overwrites_with_less():
    """A read-only check must not replace a complete session file with an
    emptier one (2026-10-17 very deep check: in an isolated clone with no
    sibling checkouts, build_views.py --check's load_config() ran
    precedent_resolve._self_heal_stale_render, which re-rendered a 3-day-old
    complete .precedent/SESSION_PRACTICES.md into one listing its sources as
    "did NOT resolve").

    Stated cases: the heal asks the renderer to keep an incomplete render
    out (--keep-if-incomplete); with that flag and a declared source
    missing, the renderer keeps the old file, marks it STALE on the line
    after its GENERATED comment, names the missing source, and leaves its
    modification time, so it still reads as stale; a second kept run does
    not add a second mark; with every source resolving, the same flag
    renders normally; and without the flag (session start) the renderer
    still writes what it can resolve."""
    import shutil, tempfile
    import precedent_resolve as pr
    tool = str(ROOT / 'tools' / 'precedent_session_practices.py')
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-keep-render-'))
    env = dict(os.environ, PRECEDENT_USER_CONFIG=str(tmp / 'no-user.json'),
               HOME=str(tmp / 'home'))
    try:
        # 1. The heal passes the flag (a stub renderer records its argv).
        stub_repo = tmp / 'stub'
        (stub_repo / 'tools').mkdir(parents=True)
        (stub_repo / 'tools' / 'precedent_session_practices.py').write_text(
            'import pathlib, sys\n'
            'repo = sys.argv[sys.argv.index("--repo") + 1]\n'
            'o = pathlib.Path(repo) / ".precedent"; o.mkdir(exist_ok=True)\n'
            '(o / "SESSION_PRACTICES.md").write_text(" ".join(sys.argv[1:]))\n',
            encoding='utf-8')
        saved = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = env['PRECEDENT_USER_CONFIG']
        try:
            pr._self_heal_stale_render(stub_repo)
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved
        argv = (stub_repo / '.precedent' / 'SESSION_PRACTICES.md').read_text(
            encoding='utf-8') if (stub_repo / '.precedent' /
                                  'SESSION_PRACTICES.md').is_file() else ''
        cases.append(('the self-heal asks the renderer to keep a complete '
                      'render (--keep-if-incomplete)',
                      '--keep-if-incomplete' in argv, argv))

        # 2. The real renderer against a repo whose shared source is gone.
        shared = tmp / 'shared-set'
        (shared / 'practices').mkdir(parents=True)
        (shared / 'practices' / 'shared-rule.md').write_text(
            '---\nslug: shared-rule\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "x happens"\n'
            'index_clause: "do the shared thing"\nstatus: active\n---\n'
            '## Rule\nSHARED-RULE-TEXT.\n\n## Story\nx\n', encoding='utf-8')
        repo = tmp / 'consumer'
        repo.mkdir()
        # Public, so the shared set is the session file's to carry.
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'base_branch': 'main', 'visibility': 'public',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(ROOT)},
                        {'level': 'shared', 'name': 'precedent-shared-fixture',
                         'path': str(shared)}]}), encoding='utf-8')
        target = repo / '.precedent' / 'SESSION_PRACTICES.md'

        def render(*extra):
            r = subprocess.run([sys.executable, tool, '--repo', str(repo),
                                '--quiet', *extra], capture_output=True,
                               text=True, env=env, cwd=str(repo))
            return r.stdout + r.stderr

        out = render('--keep-if-incomplete')
        full = target.read_text(encoding='utf-8') if target.is_file() else ''
        cases.append(('control: with every source resolving the flag renders '
                      'normally', 'shared-rule' in full and 'STALE' not in full,
                      out))
        old = time.time() - 3 * 86400
        os.utime(target, (old, old))
        shutil.move(str(shared), str(tmp / 'shared-hidden'))

        out = render('--keep-if-incomplete')
        kept = target.read_text(encoding='utf-8')
        lines = kept.splitlines()
        cases.append(('with a source missing, the complete render is kept',
                      'shared-rule' in kept, out + kept[:400]))
        cases.append(('and marked STALE on the line after its GENERATED comment, '
                      'naming the missing source',
                      len(lines) > 1 and lines[0].startswith('<!--')
                      and lines[1].startswith('> **STALE:**')
                      and 'precedent-shared-fixture' in lines[1], kept[:400]))
        cases.append(('and keeps its old modification time, so the next heal '
                      'still re-renders it', abs(target.stat().st_mtime - old) < 2,
                      str(target.stat().st_mtime - old)))
        render('--keep-if-incomplete')
        cases.append(('a second kept run does not add a second mark',
                      target.read_text(encoding='utf-8').count('**STALE:**') == 1,
                      target.read_text(encoding='utf-8')[:400]))

        render()
        now = target.read_text(encoding='utf-8')
        cases.append(('without the flag (session start) the renderer writes '
                      'what resolves and says what did not',
                      'did NOT resolve' in now and 'STALE' not in now, now[:400]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a read-only check keeps a complete session file rather than '
          f'rewrite it from sources that did not resolve ({len(cases)} stated '
          f'cases)', not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


def check_stale_render_self_heals():
    """spec/SESSION_PRACTICES_RENDER_SELF_HEAL.md's Shape C, tested rather
    than trusted -- precedent_resolve._self_heal_stale_render() is the fix
    for the half of the render gap check_individual_source_bootstrap_self_heals
    above does not cover: that self-heal (and
    _self_heal_universal_source() beside it) only ever fires on a MISSING
    clone. The 2026-09-18 incident this follows from had the clone present
    the whole session -- .precedent/SESSION_PRACTICES.md was simply a day
    stale -- so an existence-only guard would have stayed silent the whole
    extra day, which is exactly what Shape A (rejected in the brief) does
    and Shape C does not.

    Fixture: a stub tools/precedent_session_practices.py that writes a
    marker rather than performing a real multi-source render -- the
    function under test only decides WHETHER to call the render tool,
    never what the tool itself produces, so a stub keeps every case here
    hermetic and fast (practice: fixture-owns-its-state). Each case gets
    its own tmp repo, so no case's precedent.json or file mtime leaks into
    the next."""
    import shutil, tempfile
    import precedent_resolve as pr

    stub = ('#!/usr/bin/env python3\n'
            'import pathlib, sys\n'
            'repo = sys.argv[sys.argv.index("--repo") + 1]\n'
            'out = pathlib.Path(repo) / ".precedent"\n'
            'out.mkdir(parents=True, exist_ok=True)\n'
            '(out / "SESSION_PRACTICES.md").write_text("rendered", encoding="utf-8")\n')

    def _repo(tmp, *, with_tool=True, stale_hours=None):
        repo = tmp / next(tempfile._get_candidate_names())
        (repo / 'tools').mkdir(parents=True)
        if with_tool:
            tool = repo / 'tools' / 'precedent_session_practices.py'
            tool.write_text(stub, encoding='utf-8')
            tool.chmod(0o755)
        if stale_hours is not None:
            (repo / 'precedent.json').write_text(
                json.dumps({'stale_render_hours': stale_hours}), encoding='utf-8')
        return repo

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-stale-render-'))
    cases = []
    # The fixture owns who is working here: nobody. The real person's sets
    # are sources too, and since 2026-10-02 a source checkout that moved
    # after the render makes it stale, so their clones' mtimes decided
    # these cases (practice: fixture-owns-its-state).
    _saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
    os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-user-config.json')
    try:
        # --- case 1: absent render -> the stub is invoked, file appears --
        repo1 = _repo(tmp)
        result1 = pr._self_heal_stale_render(repo1)
        rendered1 = (repo1 / '.precedent' / 'SESSION_PRACTICES.md')
        cases.append(('an absent render is written by the self-heal',
                      result1 == 'attempted' and rendered1.is_file()
                      and rendered1.read_text(encoding='utf-8') == 'rendered',
                      f'result={result1!r} exists={rendered1.is_file()}'))

        # --- case 2: a fresh render (just written) is left alone ---------
        result2 = pr._self_heal_stale_render(repo1)
        cases.append(("a render younger than the threshold is reported "
                      "'fresh' and left untouched, not re-rendered on "
                      "every call",
                      result2 == 'fresh', f'result={result2!r}'))

        # --- case 3: a render older than the declared threshold re-fires -
        repo3 = _repo(tmp, stale_hours=1)
        out3 = repo3 / '.precedent'
        out3.mkdir(parents=True)
        marker = out3 / 'SESSION_PRACTICES.md'
        marker.write_text('stale copy', encoding='utf-8')
        old = time.time() - 2 * 3600  # 2h old, past this repo's 1h threshold
        os.utime(marker, (old, old))
        result3 = pr._self_heal_stale_render(repo3)
        cases.append(('a render older than the declared stale_render_hours '
                      'is re-rendered, not just an absent one',
                      result3 == 'attempted'
                      and marker.read_text(encoding='utf-8') == 'rendered',
                      f'result={result3!r} content={marker.read_text(encoding="utf-8")!r}'))

        # --- case 4: same age, but a generous threshold leaves it fresh --
        repo4 = _repo(tmp, stale_hours=48)
        out4 = repo4 / '.precedent'
        out4.mkdir(parents=True)
        marker4 = out4 / 'SESSION_PRACTICES.md'
        marker4.write_text('still current', encoding='utf-8')
        os.utime(marker4, (old, old))
        result4 = pr._self_heal_stale_render(repo4)
        cases.append(("the SAME 2h-old file is 'fresh' under a 48h "
                      "threshold -- the threshold is read from THIS repo's "
                      "own precedent.json, not hardcoded",
                      result4 == 'fresh'
                      and marker4.read_text(encoding='utf-8') == 'still current',
                      f'result={result4!r}'))

        # --- case 5: the declared-default (1h) is honored when
        # precedent.json is absent, not silently zero ---------------------
        repo5 = _repo(tmp)  # no precedent.json written at all
        cases.append(('the declared-default (1h) is used when this repo '
                      'has no precedent.json at all',
                      pr._stale_render_hours(repo5) == 1,
                      f'got {pr._stale_render_hours(repo5)!r}'))

        # --- case 6: a source set whose engine predates this addition (no
        # precedent_session_practices.py) degrades, never raises ----------
        repo6 = _repo(tmp, with_tool=False)
        result6 = pr._self_heal_stale_render(repo6)
        cases.append(('a repo with no precedent_session_practices.py '
                      'degrades to no-tool rather than raising',
                      result6 == 'no-tool', f'result={result6!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if _saved_cfg is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = _saved_cfg

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the stale-render self-heal fires on absent-or-stale, not just '
          f'absent, and reads its threshold from this repo\'s own '
          f'precedent.json ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:400]}" for n, d in bad))


def check_self_heal_skips_a_scratch_copy():
    """precedent_resolve.py's source repairs cloned every declared source
    beside ANY repository that resolved, including a test's `git clone
    <path>` scratch copy in /tmp: precedent-shared-repo-maintenance's
    trailer test then resolved the working-style set it set out to exclude,
    and failed on an untouched landing tier (2026-09-30). Planted, with a stand-
    in bootstrap tool that leaves a marker when it runs. Discriminating
    cases: from a copy whose origin is another checkout on this disk, the
    repair does not run; from a checkout whose origin is a remote, it still
    does (the control); a file:// origin counts as a copy too."""
    import shutil, subprocess, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as _pr
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='self-heal-scratch-'))
    saved = os.environ.get('CLAUDE_CODE_REMOTE')
    cases = []
    try:
        orig = tmp / 'orig'
        (orig / 'tools').mkdir(parents=True)
        (orig / 'tools' / 'precedent_source_bootstrap.py').write_text(
            'import pathlib, sys\n'
            'pathlib.Path(sys.argv[sys.argv.index("--sources-from") + 1]'
            ').joinpath("HEALED").write_text("x")\n', encoding='utf-8')
        git = lambda *a: subprocess.run(['git', *a], capture_output=True, text=True)
        git('init', '-q', str(orig))
        git('-C', str(orig), '-c', 'user.name=T', '-c', 'user.email=t@t',
            'add', '-A')
        git('-C', str(orig), '-c', 'user.name=T', '-c', 'user.email=t@t',
            'commit', '-qm', 'x')
        os.environ['CLAUDE_CODE_REMOTE'] = 'true'

        copy = tmp / 'copy'
        git('clone', '-q', str(orig), str(copy))
        got = _pr._self_heal_universal_source(copy)
        cases.append(('THE CASE THIS EXISTS FOR: from a copy of a checkout on '
                      'this disk, the repair does not run',
                      got == 'scratch-copy' and not (copy / 'HEALED').exists(),
                      got))
        fcopy = tmp / 'fcopy'
        git('clone', '-q', f'file://{orig}', str(fcopy))
        got = _pr._self_heal_universal_source(fcopy)
        cases.append(('...and a file:// origin is a copy too',
                      got == 'scratch-copy' and not (fcopy / 'HEALED').exists(),
                      got))
        cases.append(('...and the individual repair stands aside there too',
                      _pr._self_heal_individual_source(copy) == 'scratch-copy',
                      ''))
        git('-C', str(copy), 'remote', 'set-url', 'origin',
            'https://example.invalid/someone/some-set')
        got = _pr._self_heal_universal_source(copy)
        cases.append(('CONTROL: a checkout whose origin is a remote is still '
                      'repaired', got == 'attempted' and (copy / 'HEALED').exists(),
                      got))
    finally:
        if saved is None:
            os.environ.pop('CLAUDE_CODE_REMOTE', None)
        else:
            os.environ['CLAUDE_CODE_REMOTE'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the source repairs skip a scratch copy of a checkout '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d}" for n, d in bad))


def check_not_binding_actually_exempts_a_check():
    """A `not_binding` entry has to change the RUN, not just the
    reachability report.

    precedent_resolve.load_not_binding()'s docstring describes the
    mechanism as a property of the pair -- "commit-author binds a repo one
    person authors alone and not one with many contributors" -- and names
    that slug as its motivating example. But precedent_check.py read the
    list in one place only, _unreachable_practices, where it suppressed a
    reachability finding and nothing else; main() built its slug list from
    sorted(CHECKS) and never consulted it. So a consuming repo could write
    a reasoned exemption and have it change nothing: the check still ran,
    still violated, still failed the run. A real install ended on two
    permanent violations it had written exemptions for, and the 17 entries
    in templates/document-project/precedent.json were, for
    check purposes, decorative (found 2026-09-10).

    Four cases, on one fixture consuming repo, because the fix has four
    separable ways to be wrong: the exemption must SUPPRESS the violation;
    it must not do so SILENTLY (an exemption that leaves no trace is how a
    rule gets switched off and forgotten, which is worse than the bug);
    the run must then be CLEAN, which is the whole point; and a
    `severity: blocking` practice must still be REFUSED an exemption."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-not-binding-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        (repo / 'tools').mkdir(parents=True)
        (repo / 'practices').mkdir()
        # DERIVED, not hand-listed. This was a fixed tuple of seven names
        # until 2026-09-10, and the day a new engine module arrived
        # (precedent_identity.py, carved out of precedent_resolve.py) the
        # fixture silently stopped matching a real consumer: it copied a
        # precedent_resolve.py that imports a companion the fixture had
        # never heard of. Reading the vendoring tool's own list is what
        # keeps this fixture a consumer rather than a curated subset of one
        # (practice: fixture-owns-its-state -- the state it owns includes
        # which files a consumer actually gets).
        _seed_consumer_engine(repo / 'tools', extra=('routing_scope.json',))

        # A practice that is in force, exemptible, and whose check FIRES
        # here -- otherwise a "clean run" would prove nothing. Written
        # rather than copied so the fixture does not drift with the
        # catalogue: this one demands a file the fixture does not have.
        (repo / 'practices' / 'harness-exempt-fixture.md').write_text(
            '---\nslug: harness-exempt-fixture\ntitle: Fixture\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "testing"\nindex_clause: "a harness fixture"\n'
            'checked_by: null\ndefines: []\nstatus: active\n'
            'supersedes: []\noverrides: null\nadded: null\n'
            'approved_by: "harness"\n---\n\n## Rule\nFixture.\n\n'
            '## Detail\n\n## Why\n\n## Story\n\n## Install\n',
            encoding='utf-8')

        def write_config(not_binding):
            (repo / 'precedent.json').write_text(json.dumps({
                'format_version': 1,
                'visibility': 'private',
                'sources': [{'level': 'universal', 'name': 'precedent',
                             'path': '.'}],
                'not_binding': not_binding,
            }, indent=2) + '\n', encoding='utf-8')

        def run_check():
            r = subprocess.run([sys.executable, 'tools/precedent_check.py',
                                '--full-sweep'],
                               cwd=str(repo), capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        # PLANT the violation rather than hoping for one. This used to
        # discover whatever slug happened to be violated, on the reasoning
        # that naming one would go stale -- and on 2026-09-10 the fixture
        # went CLEAN instead (a fuller vendored engine removed the
        # incidental finding it had been relying on), so there was suddenly
        # nothing to exempt and the whole check rested on an accident. A
        # planted violation is the only kind a negative control can trust
        # (practice: control-asserts-which-failure).
        #
        # two-check-levels is the plant: it asks the instructions file to
        # name a fast check and a full check, and this fixture's AGENTS.md
        # deliberately names neither. Cheap, deterministic, and unrelated to
        # the exemption machinery under test.
        for slug in ('two-check-levels',):
            src = ROOT / 'practices' / f'{slug}.md'
            if src.is_file():
                shutil.copy2(src, repo / 'practices' / f'{slug}.md')
        (repo / 'AGENTS.md').write_text(
            '# Fixture\n\nNames no check levels, on purpose -- that is the '
            'planted violation.\n', encoding='utf-8')

        # BASELINE: with nothing exempted the fixture must produce that
        # VIOLATION and no exemptions. Without this the cases below would
        # pass on a fixture that never had anything to exempt -- which is
        # the shape of the bug itself, so it has to be ruled out.
        write_config([])
        rc0, out0 = run_check()
        violated_slugs = [ln.split()[1] for ln in out0.splitlines()
                          if ln.startswith('VIOLATION')]
        cases.append(('baseline: the PLANTED violation actually fires, so '
                      'there is something for an exemption to act on',
                      'two-check-levels' in violated_slugs,
                      f'violated: {violated_slugs}\n' + failure_detail(out0, 900)))
        cases.append(('the baseline summary counts no exemptions',
                      ' 0 exempted' in out0, failure_detail(out0, 300)))
        cases.append(('a violation fails the run, so a suppressed one is a '
                      'visible difference', rc0 == 1, f'rc={rc0}'))

        if 'two-check-levels' in violated_slugs:
            target = 'two-check-levels'
            write_config([{'slug': target,
                           'reason': 'harness fixture: exempted on purpose'}])
            rc2, out2 = run_check()
            cases.append((f'exempting {target!r} removes its VIOLATION from '
                          f'the run -- the declaration reaches main(), not '
                          f'just the reachability report',
                          f'VIOLATION  {target}' not in out2, failure_detail(out2, 900)))
            cases.append((f'and says so out loud: {target!r} is named EXEMPT '
                          f'with its recorded reason, never silently dropped',
                          f'EXEMPT     {target}' in out2
                          and 'exempted on purpose' in out2, failure_detail(out2, 900)))
            cases.append(('the summary line carries `exempted` as its own '
                          'category', ' 1 exempted' in out2, failure_detail(out2, 300)))

        # THE REFUSAL, which must survive the fix: `severity: blocking` is
        # exactly the rule a downstream repo may not switch off.
        (repo / 'practices' / 'harness-blocking-fixture.md').write_text(
            '---\nslug: harness-blocking-fixture\ntitle: Fixture\n'
            'tier: on-demand\nseverity: blocking\napplies_to: ["**"]\n'
            'occasion: "testing"\nindex_clause: "a blocking fixture"\n'
            'checked_by: null\ndefines: []\nstatus: active\n'
            'supersedes: []\noverrides: null\nadded: null\n'
            'approved_by: "harness"\n---\n\n## Rule\nFixture.\n\n'
            '## Detail\n\n## Why\n\n## Story\n\n## Install\n',
            encoding='utf-8')
        write_config([{'slug': 'harness-blocking-fixture',
                       'reason': 'harness fixture: must be refused'}])
        rc3, out3 = run_check()
        cases.append(('a `severity: blocking` practice cannot be exempted: it '
                      'is not counted as EXEMPT and the refusal is stated',
                      'EXEMPT     harness-blocking-fixture' not in out3
                      and 'severity: blocking' in out3
                      and ' 0 exempted' in out3, failure_detail(out3, 900)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'`not_binding` actually exempts a check, visibly, and still '
          f'refuses a blocking practice ({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {str(d)[:600]}' for n, d in bad))


def check_mirrored_prefixes_answers_both_install_models():
    """precedent_resolve.mirrored_prefixes() has to work in the install
    model that has no `process/manifest.json`, because that is the one it
    was written for.

    Every check that scans prose and must not report findings inside a
    vendored copy of somebody else's catalogue derived this privately from
    `process/manifest.json`'s `upstream.vendored_at`. That file is §1's
    bookkeeping and INSTALL.md §0 step 5 says to SKIP it, so in a §0
    install the exclusion silently evaporated and the vendored catalogue
    came back into scope: a real install's run reported dozens of
    unactionable findings inside Precedent's own historical prose, and the
    workaround downstream was to write a manifest carrying nothing but an
    `upstream` block purely to feed the signal (2026-09-10).

    Five fixtures, because "returns something" is not the property -- what
    matters is that it excludes a MIRROR and never a repo's own
    hand-authored practices. A source set declares `path: "."`; treating
    that as a mirror would blind every check inside a practice set to that
    set's own content, which is a worse failure than the one being
    fixed."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as pr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-mirrored-'))
    cases = []
    try:
        def write(rel, payload):
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

        # §0: vendored catalogue, a live sibling shared source, a repo-local
        # source, and NO process/manifest.json.
        (tmp / 's0' / 'precedent' / 'universal' / 'practices').mkdir(parents=True)
        (tmp / 's0' / 'local' / 'practices').mkdir(parents=True)
        write('s0/precedent.json', {
            'format_version': 1, 'visibility': 'private', 'sources': [
                {'level': 'universal', 'name': 'precedent',
                 'path': 'precedent/universal'},
                {'level': 'team', 'name': 'precedent-team-writing',
                 'path': '../precedent-team-writing'},
                {'level': 'repo-local', 'name': 'local', 'path': 'local'}]})
        s0 = pr.mirrored_prefixes(tmp / 's0')
        cases.append(('a §0 install excludes its vendored catalogue with no '
                      'process/manifest.json anywhere -- the whole point',
                      'precedent/universal/' in s0, str(s0)))
        cases.append(('and does NOT exclude its own repo-local source, which '
                      'is hand-authored', 'local/' not in s0, str(s0)))
        cases.append(('and does NOT exclude a shared source resolved from a '
                      'sibling clone outside this repo',
                      not any('precedent-team-writing' in x for x in s0),
                      str(s0)))

        # §1: the classic layout, which must keep working unchanged.
        (tmp / 's1' / 'process' / 'upstream' / 'practices').mkdir(parents=True)
        write('s1/process/manifest.json',
              {'upstream': {'vendored_at': 'process/upstream'}})
        s1 = pr.mirrored_prefixes(tmp / 's1')
        cases.append(('a §1 install still excludes process/upstream/',
                      'process/upstream/' in s1, str(s1)))

        # §1 with the manifest missing: the tree alone is enough.
        (tmp / 's1b' / 'process' / 'upstream' / 'practices').mkdir(parents=True)
        s1b = pr.mirrored_prefixes(tmp / 's1b')
        cases.append(('a process/upstream/ tree with no manifest is still a '
                      'mirror -- that is a half-finished install, not a repo '
                      'that owns the tree', 'process/upstream/' in s1b, str(s1b)))

        # A domain pack vendored beside the catalogue (2026-10-10): a
        # mirror where its manifest names the repo it comes from, and the
        # source's own tree where it records none.
        (tmp / 'pk' / 'process' / 'voicepack').mkdir(parents=True)
        write('pk/process/manifest_voicepack.json', {'upstream': {
            'repo': 'https://example.invalid/pack', 'vendored_at': 'process/voicepack'}})
        pk = pr.mirrored_prefixes(tmp / 'pk')
        cases.append(('a pack whose manifest names its upstream repo is a mirror',
                      'process/voicepack/' in pk, str(pk)))
        (tmp / 'pks' / 'process' / 'voicepack').mkdir(parents=True)
        write('pks/process/manifest_voicepack.json', {'upstream': {
            'repo': None, 'vendored_at': 'process/voicepack'}})
        pks = pr.mirrored_prefixes(tmp / 'pks')
        cases.append(("...and the pack's own source, recording no upstream "
                      "repo, owns that tree", 'process/voicepack/' not in pks, str(pks)))

        # A SOURCE SET: `path: "."`. Its practices/ is its own.
        (tmp / 'set' / 'practices').mkdir(parents=True)
        write('set/precedent.json', {'format_version': 1, 'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': '.'}]})
        st = pr.mirrored_prefixes(tmp / 'set')
        cases.append(('a source set declaring `path: "."` mirrors NOTHING -- '
                      'excluding its own root would blind every check inside '
                      'a practice set to that set\'s content', st == (), str(st)))

        # Degradation: a caller is a check, and a check must not crash.
        cases.append(('a directory that is not a Precedent repo at all '
                      'returns an empty tuple rather than raising',
                      pr.mirrored_prefixes(tmp / 'does-not-exist') == (), ''))
        (tmp / 'broken').mkdir()
        (tmp / 'broken' / 'precedent.json').write_text('{not json',
                                                       encoding='utf-8')
        cases.append(('a malformed precedent.json returns an empty tuple '
                      'rather than raising -- a check that cannot read this '
                      'must degrade to excluding nothing, not die',
                      pr.mirrored_prefixes(tmp / 'broken') == (), ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'mirrored_prefixes() answers in a §0 install, where '
          f'process/manifest.json does not exist ({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_no_engine_tool_hardcodes_a_mirror_path():
    """No engine tool decides what it mirrors by matching a literal path.

    practice: convention-to-audit -- this convention was broken six times
    before anybody wrote it down, which is exactly the threshold that
    practice names.

    THE BUG THIS CATCHES, in its own words. `process/upstream/` is
    INSTALL.md §1's layout, and for a long time it was the only one, so
    every check that had to skip a mirrored tree simply matched that
    string. INSTALL.md §0 mirrors somewhere else entirely -- the vendored
    catalogue sits at whatever path precedent.json's `universal` source
    names -- so in a §0 install each of those exclusions silently stopped
    excluding anything, and the checks went looking inside a tree the
    consumer may not edit and cannot fix. Measured in a real §0 install
    (2026-09-10): doc_lint went red on 109 broken relative links, every one
    of them inside a mirror; technical-describes-people flagged Precedent's
    own practice file; rename-updates-links reported two findings in
    Precedent's prose for a file the consumer had deleted from its own
    tree. All unactionable, all caused by the constant meant to prevent
    exactly that.

    precedent_resolve.mirrored_prefixes() is the one authority, and it
    never raises, so there is no reason left to match a literal.

    WHAT IS DELIBERATELY STILL ALLOWED, and why the check reads calls
    rather than the whole file: the string appears legitimately in prose,
    in comments explaining this very history, and in the two documented
    import-failure fallbacks (doc_lint.py and precedent_check.py both ship
    into trees carrying no precedent_resolve.py). Only a path-matching CALL
    is a violation -- that is where the decision actually gets made."""
    import re as _re
    # A `.startswith(...)` / `.endswith(...)` call whose argument text
    # mentions the §1 mirror path: the decision site, not the prose.
    call = _re.compile(r'\.(?:startswith|endswith)\(([^)]*)\)')
    scanned = sorted((ROOT / 'tools').glob('*.py'))
    bad = []
    for f in scanned:
        rel = f.relative_to(ROOT).as_posix()
        for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            for m in call.finditer(line):
                if 'process/upstream/' in m.group(1):
                    bad.append(f'{rel}:{i}: {line.strip()[:90]}')
    check(f'no engine tool decides what it mirrors by matching a literal '
          f'path -- mirrored_prefixes() is the one authority '
          f'({len(scanned)} tools scanned)',
          not bad,
          '; '.join(bad))


def check_ladder_opt_in_loader():
    """spec/LADDER_OPT_IN_PLAN.md steps 2-4, tested in a fixture world (never a
    real profile: a real one would carry private set text into the harness).

    A person's individual set BRINGS a shared set that provides the ladder.
    Cases, each naming the behaviour it guards:
      1. the brought set loads, at the shared level, beside the individual set;
      2. a person who brings nothing does not get it -- the same repository,
         another person;
      3. a malformed `brings` entry is skipped with one line, never fatal;
      4. build_views never writes a brought set into a committed view, in a
         private repository, a public one, or a practice set;
      5. precedent_ladder: in force for the person who brings it, not for one
         who does not, not under PRECEDENT_NO_LADDERS, and the --in-force
         exit code agrees;
      6. PRECEDENT_NO_LADDERS drops the set from load_config, and a brought
         set that provides nothing is NOT dropped by it;
      7. session start clones a brought set from its repo_url, beside the
         individual set, and pulls it on the next run;
      8. --withdraw-from-universal deletes the universal copy, records the
         withdrawal once, and a consumer of universal alone sees no IN FORCE
         NOWHERE for it; refused without --approved-by."""
    import contextlib, io, shutil, tempfile
    import precedent_resolve as pr
    import precedent_ladder as pl
    import precedent_source_bootstrap as psb
    import build_views as bv

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    def commit_all(repo, msg='x'):
        git(repo, 'add', '-A')
        git(repo, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', msg)

    def make_set(path, name, provides=None, level='shared'):
        (path / 'practices').mkdir(parents=True, exist_ok=True)
        man = {'name': name, 'level': level, 'visibility': 'public',
               'subject': 'a fixture', 'code': []}
        if provides is not None:
            man['provides'] = provides
        (path / 'precedent-source.json').write_text(json.dumps(man),
                                                    encoding='utf-8')
        (path / 'practices' / f'{name}-rule.md').write_text(
            _move_fixture_practice(f'{name}-rule'), encoding='utf-8')
        return path

    saved = {k: os.environ.get(k) for k in (
        'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG', pr.NO_LADDERS_ENV, 'CLAUDE_PROJECT_DIR',
        'PRECEDENT_PROJECT_DIR', pr.SELF_HEAL_RENDER_ENV)}
    for k in saved:                       # practice: fixture-owns-its-state
        os.environ.pop(k, None)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='ladder-opt-in-'))
    cases = []
    try:
        home = tmp / 'home'
        # The ladder set's origin, a real repository so session start can
        # clone it from a URL.
        origin = make_set(tmp / 'origin-ladder', 'fixture-ladder', ['ladder'])
        git(origin, 'init', '-q', '-b', 'main')
        commit_all(origin)
        url = f'file://{origin}'
        ind = home / 'precedent-individual'
        (ind / 'practices').mkdir(parents=True)
        git(ind, 'init', '-q', '-b', 'main')
        (ind / 'precedent-source.json').write_text(json.dumps({
            'name': 'precedent-individual', 'level': 'individual',
            'brings': [{'name': 'fixture-ladder', 'repo_url': url},
                       {'name': 'Not A Slug', 'repo_url': url},
                       'not-a-dict',
                       # git would read this as an option, not a repository
                       {'name': 'evil', 'repo_url': '--upload-pack=touch /tmp/x'},
                       # the set itself, which would load it twice
                       {'name': 'precedent-individual', 'repo_url': url}]}),
            encoding='utf-8')
        brings_cfg = tmp / 'brings.json'
        brings_cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(ind)}}), encoding='utf-8')
        plain_ind = tmp / 'other' / 'precedent-individual'
        (plain_ind / 'practices').mkdir(parents=True)
        git(plain_ind, 'init', '-q')
        plain_cfg = tmp / 'plain.json'
        plain_cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(plain_ind)}}),
            encoding='utf-8')
        repo = tmp / 'work' / 'consumer'
        repo.mkdir(parents=True)
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'sources': []}),
            encoding='utf-8')

        # 7 first: session start puts the brought set on disk.
        os.environ['PRECEDENT_USER_CONFIG'] = str(brings_cfg)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            res = psb.sources_from_brings()
        clone = home / 'fixture-ladder'
        cases.append(('session start clones a brought set from its repo_url, '
                      'beside the individual set',
                      any(n == 'fixture-ladder' and ok for n, ok, _m in res)
                      and (clone / 'practices').is_dir(), repr(res)))
        (origin / 'practices' / 'later.md').write_text(
            _move_fixture_practice('later'), encoding='utf-8')
        commit_all(origin, 'later')
        with contextlib.redirect_stderr(io.StringIO()):
            psb.sources_from_brings()
        cases.append(('and pulls it on the next run',
                      (clone / 'practices' / 'later.md').is_file(), ''))

        # 1 and 3
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            srcs = pr.load_config(repo)
        got = [s for s in srcs if s['name'] == 'fixture-ladder']
        cases.append(('the brought set loads at the shared level, beside the '
                      'individual set, marked as brought',
                      len(got) == 1 and got[0]['level'] == 'shared'
                      and got[0].get('brought') is True
                      and pathlib.Path(got[0]['path']).resolve() == clone.resolve(),
                      repr(srcs)))
        cases.append(('each malformed brings entry -- a bad name, not a dict, a URL '
                      'git would read as an option, the set itself -- is skipped '
                      'with one line',
                      err.getvalue().count('`brings` entry') == 4
                      and not [s for s in srcs if s['name'] in
                               ('Not A Slug', 'evil')]
                      and len([s for s in srcs
                               if s['name'] == 'precedent-individual']) == 1,
                      err.getvalue()))
        dsp = [n for _p, _l, n, _note in pr.declared_source_paths(repo)]
        cases.append(('declared_source_paths names it, so the freshness guard '
                      'and the refresh check it', 'fixture-ladder' in dsp, repr(dsp)))

        # 4
        for vis in ('private', 'public'):
            (repo / 'precedent.json').write_text(json.dumps({
                'format_version': 1, 'visibility': vis, 'sources': []}),
                encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()):
                srcs = pr.load_config(repo)
            tracked, deferred, _n = bv.sources_for_tracked_block(repo, srcs)
            cases.append((f'a {vis} repository\'s committed view never carries '
                          f'the brought set',
                          not [s for s in tracked if s.get('brought')]
                          and [s for s in deferred if s.get('brought')],
                          repr(tracked)))
        with contextlib.redirect_stderr(io.StringIO()):
            srcs = pr.load_config(ind)
        tracked, deferred, _n = bv.sources_for_tracked_block(ind, srcs)
        cases.append(('nor does a practice set\'s',
                      not [s for s in tracked if s.get('brought')], repr(tracked)))

        # 5
        cases.append(('the ladder is in force for the person who brings it',
                      pl.ladder_in_force(repo), pl.status_sentence(repo)))
        cli = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_ladder.py'),
                              '--in-force', '--repo', str(repo)],
                             capture_output=True, text=True,
                             env=dict(os.environ))
        cases.append(('--in-force exits 0 for them', cli.returncode == 0,
                      cli.stdout + cli.stderr))
        os.environ['PRECEDENT_USER_CONFIG'] = str(plain_cfg)
        cases.append(('and not for a person who brings nothing, in the same '
                      'repository', not pl.ladder_in_force(repo),
                      pl.status_sentence(repo)))
        cli = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_ladder.py'),
                              '--in-force', '--repo', str(repo)],
                             capture_output=True, text=True, env=dict(os.environ))
        cases.append(('--in-force exits 1 for them', cli.returncode == 1,
                      cli.stdout + cli.stderr))
        with contextlib.redirect_stderr(io.StringIO()):
            srcs = pr.load_config(repo)
        cases.append(('and load_config gives them no such set',
                      not [s for s in srcs if s['name'] == 'fixture-ladder'],
                      repr(srcs)))

        # 6
        os.environ['PRECEDENT_USER_CONFIG'] = str(brings_cfg)
        os.environ[pr.NO_LADDERS_ENV] = '1'
        with contextlib.redirect_stderr(io.StringIO()):
            srcs = pr.load_config(repo)
        cases.append(('PRECEDENT_NO_LADDERS drops the ladder set from the session',
                      not [s for s in srcs if s['name'] == 'fixture-ladder']
                      and not pl.ladder_in_force(repo)
                      and 'switched off' in pl.status_sentence(repo), repr(srcs)))
        man = json.loads((clone / 'precedent-source.json').read_text(encoding='utf-8'))
        man.pop('provides')
        (clone / 'precedent-source.json').write_text(json.dumps(man), encoding='utf-8')
        with contextlib.redirect_stderr(io.StringIO()):
            srcs = pr.load_config(repo)
        cases.append(('but keeps a brought set that provides nothing',
                      [s for s in srcs if s['name'] == 'fixture-ladder'], repr(srcs)))
        os.environ.pop(pr.NO_LADDERS_ENV, None)

        # 8
        env = _move_fixture_env(tmp)
        team = tmp / 'precedent-team-fixture'
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_bootstrap_source.py'),
                        '--level', 'team', '--name', 'precedent-team-fixture', '--dest', str(team),
                        '--approver', 'Fixture Approver:fixture-gh'],
                       capture_output=True, text=True, env=env)
        uclone = tmp / 'precedent'
        (uclone / 'practices').mkdir(parents=True)
        (uclone / 'tools').mkdir()
        (uclone / 'practices' / 'zz-gone.md').write_text(
            _move_fixture_practice('zz-gone', install='Nothing.'), encoding='utf-8')
        (uclone / 'practices' / 'zz-stays.md').write_text(
            _move_fixture_practice('zz-stays'), encoding='utf-8')

        def move(*args):
            return subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_move.py'),
                                   *args], cwd=str(ROOT), capture_output=True,
                                  text=True, env=env)
        move('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
             '--to', 'team', '--to-path', str(team), '--approved-by', 'Fixture Approver')
        r = move('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--withdraw-from-universal')
        cases.append(('--withdraw-from-universal is refused without --approved-by, '
                      'and writes nothing',
                      r.returncode == 1 and '--approved-by' in r.stderr
                      and (uclone / 'practices' / 'zz-gone.md').is_file(), failure_detail(r.stderr, 300)))
        r = move('--slug', 'zz-gone', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--withdraw-from-universal',
                 '--approved-by', 'Fixture Approver')
        record = uclone / 'record' / 'WITHDRAWN_FROM_UNIVERSAL.md'
        cases.append(('it deletes the universal copy and records the withdrawal once',
                      r.returncode == 0
                      and not (uclone / 'practices' / 'zz-gone.md').exists()
                      and record.is_file()
                      and record.read_text(encoding='utf-8').count('`zz-gone` withdrawn') == 1,
                      failure_detail(r.stdout + r.stderr, 500)))
        # The set's copy no longer says a universal copy stays active, and
        # still carries the approval the rule had in universal (2026-10-02:
        # fourteen ladder rules lost theirs).
        kept = sp._read_practice_file(team / 'practices' / 'zz-gone.md')[0]
        ab = str(kept.get('approved_by') or '')
        cases.append(("the set's copy says universal keeps no copy, and keeps "
                      "the rule's own approval",
                      'keeps no copy' in ab and 'stays active' not in ab
                      and '(there: Fixture, 2026-09-14)' in ab, ab[:300]))
        consumer = tmp / 'consumer-u'
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uclone)}]}),
            encoding='utf-8')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
                            '--repo', str(consumer), '--json'],
                           capture_output=True, text=True, env=env)
        try:
            dangling = json.loads(r.stdout).get('dangling') or []
        except json.JSONDecodeError:
            dangling = None
        cases.append(('a consumer of universal alone sees no IN FORCE NOWHERE for it',
                      dangling == [], failure_detail(r.stdout + r.stderr, 400)))
        # 8b. A retired name leaves with the rule it forwards to, and the
        # tool writes its record line, in the shape the record's reader
        # knows. 2026-10-02: four such names were withdrawn by hand, because
        # the tool refused them, in a shape the reader did not know; the
        # first consumer to update past them was refused (2026-10-04).
        stub_fm = lambda: (_move_fixture_practice('zz-old-name')
                           .replace('status:      active\nin_force_at: null',
                                    'status:      deduplicated\nin_force_at: zz-gone'))
        (uclone / 'practices' / 'zz-old-name.md').write_text(stub_fm(), encoding='utf-8')
        (team / 'practices' / 'zz-old-name.md').write_text(
            _move_fixture_practice('zz-old-name'), encoding='utf-8')
        r = move('--slug', 'zz-old-name', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--withdraw-from-universal',
                 '--approved-by', 'Fixture Approver')
        cases.append(("CONTROL: a retired name whose set copy is ACTIVE is refused, "
                      "by that reason, and nothing is deleted",
                      r.returncode == 1 and 'not the same retired name kept as history' in r.stderr
                      and (uclone / 'practices' / 'zz-old-name.md').is_file(),
                      failure_detail(r.stdout + r.stderr, 400)))
        (team / 'practices' / 'zz-old-name.md').write_text(
            stub_fm(), encoding='utf-8')
        r = move('--slug', 'zz-old-name', '--from', 'universal', '--from-path', str(uclone),
                 '--to', 'team', '--to-path', str(team), '--withdraw-from-universal',
                 '--approved-by', 'Fixture Approver')
        hist = pr.withdrawn_history(uclone)
        rec = pr.withdrawn_record(uclone)
        cases.append(('a retired name is withdrawn by the tool, and its record line '
                      'reads back as history beside the rule it forwards to',
                      r.returncode == 0
                      and not (uclone / 'practices' / 'zz-old-name.md').exists()
                      and 'zz-old-name' in hist and 'zz-gone' not in hist
                      and set(rec) >= {'zz-gone', 'zz-old-name'},
                      failure_detail(r.stdout + r.stderr, 500) + repr(rec)))
        text = record.read_text(encoding='utf-8')
        cases.append(('every line the tool wrote to the record reads back',
                      len(pr.withdrawn_record_entries(text))
                      == sum(1 for l in text.splitlines() if l.startswith('- ')),
                      failure_detail(text, 600)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a set a person brings loads for that person only, never reaches a '
          f'committed view, answers precedent_ladder, and a universal rule can be '
          f'withdrawn to it cleanly ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {str(d)[:400]}" for n, d in bad))


def check_withdrawal_record_lines_all_read_back():
    """Every line of this repository's record/WITHDRAWN_FROM_UNIVERSAL.md is
    one precedent_resolve.withdrawn_record reads. The record ships to every
    consumer, whose sync reads it to tell a withdrawal from a loss; a line it
    cannot read is a rule that sync refuses as lost. 2026-10-04: four lines
    written by hand in a second shape were unreadable, and the first
    consumer to update past them was refused on two of them."""
    import precedent_resolve as pr
    path = ROOT / pr.WITHDRAWN_RECORD
    if not path.is_file():
        return True, 'no withdrawal record in this repository', ''
    text = path.read_text(encoding='utf-8')
    lines = [l for l in text.splitlines() if l.startswith('- ')]
    read = {e[1] for e in pr.withdrawn_record_entries(text)}
    unread = [l[:120] for l in lines
              if not any(f'`{slug}`' in l.split(' withdrawn from ')[0] for slug in read)]
    return (not unread and len(pr.withdrawn_record_entries(text)) == len(lines),
            f'{len(lines)} line(s), every one read back',
            'unreadable line(s): ' + ' | '.join(unread))


def check_vocabulary_reads_a_materialized_practice_as_one():
    """Vocabulary does not call a practice "defined twice" because the view
    sync wrote it into a consumer's practices/: MANIFEST.json records that
    file as the sync's own output. 2026-10-04, a consumer: a note for nearly
    every practice it has, about 57 KB, in which a real shadow could not be
    seen. CONTROL: a local file the manifest does not record, under a
    universal practice's name, is still noted."""
    import shutil, tempfile
    import precedent_vocabulary as pv
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-vocab-twice-'))
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-user-config.json')
    cases = []
    try:
        uni = tmp / 'universal'
        (uni / 'practices').mkdir(parents=True)
        for slug in ('zz-synced', 'zz-shadowed'):
            (uni / 'practices' / f'{slug}.md').write_text(
                _move_fixture_practice(slug), encoding='utf-8')
        repo = tmp / 'consumer'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)}]}),
            encoding='utf-8')
        shutil.copy(uni / 'practices' / 'zz-synced.md', repo / 'practices' / 'zz-synced.md')
        (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
            {'slug': 'zz-synced', 'source': 'precedent'}]}), encoding='utf-8')
        _e, notes = pv.collect(repo)
        cases.append(('a practice the sync wrote, recorded in MANIFEST.json, is not '
                      '"defined twice"', not any('zz-synced is defined twice' in n
                                                 for n in notes), notes))
        shutil.copy(uni / 'practices' / 'zz-shadowed.md', repo / 'practices' / 'zz-shadowed.md')
        _e, notes = pv.collect(repo)
        cases.append(('CONTROL: a local file the manifest does not record is noted',
                      any('zz-shadowed is defined twice' in n for n in notes), notes))
    finally:
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_vocabulary_scan_skips_code_owner_commands():
    """The very deep check's list of spoken commands leaves out a command
    marked for code owners only, as the vocabulary page itself does.

    WHY. precedent_vocabulary.py keeps code-owner commands out of every
    committed page (Morgan, 2026-10-05), and DAILY_HABITS.md is generated
    from it. The scan that checks the page used its own list and reported
    "Deep check", "Very deep check", "Full practice audit" and "Update
    Vendors" missing on every run, and a session told to fix that would have
    broken the generated page (2026-10-11)."""
    import tempfile
    import very_deep_check as vdc
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / 'practices'
        d.mkdir()
        for slug, extra in (('everyone', ''),
                            ('owners-only', 'visible_to: code-owners\n')):
            (d / f'{slug}.md').write_text(
                f'---\nslug: {slug}\nstatus: active\n{extra}'
                f'command: ["Say {slug}"]\n---\n## Rule\n\nx\n',
                encoding='utf-8')
        got = vdc._spoken_commands(td)
    phrases = [p for p, _s in got]
    cases = [('a command for everyone is listed', 'Say everyone' in phrases),
             ('a code-owner command is not', 'Say owners-only' not in phrases)]
    failed = [n for n, ok in cases if not ok]
    check(f'the vocabulary scan skips code-owner commands ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed) + f' -- {got}')


def check_spoken_commands_lead_the_session_start():
    """With five sets attached, a session opened above them got every repo's
    start-up output joined and cut, and the ladder's stage words came after
    the cut (2026-10-04, the review of the first fix).

    1. precedent_session_practices.py prints the spoken-commands block
       first, one line per practice defining a command.
    2. precedent_run_session_hooks.py lifts every repo's block to the front,
       merged, before the cut -- even a block from the LAST repo, under a cap
       the first repo alone overflows.
    3. The two files agree on how the block begins."""
    import io, contextlib, tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_session_practices as psp
        import precedent_run_session_hooks as rsh
    finally:
        sys.path.pop(0)
    cases = []
    head = getattr(psp, 'SPOKEN_HEAD', None)
    prefix = getattr(rsh, 'SPOKEN_PREFIX', None)
    cases.append(('3. the writer and the runner agree on the block\'s first line',
                  bool(head and prefix and head.startswith(prefix))))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-spoken-first-'))
    saved_cap = getattr(rsh, 'CONTEXT_CAP', None)
    try:
        for name, out in (('a-first', 'x' * 400),
                          ('z-last', f'{head}\n- "Debut" -> debut: stage 4'
                                     f'\nnoise after the block')):
            repo = tmp / name
            (repo / '.git').mkdir(parents=True)
            (repo / '.claude').mkdir()
            (repo / 'out.txt').write_text(out + '\n', encoding='utf-8')
            (repo / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {
                'SessionStart': [{'hooks': [{'type': 'command',
                                             'command': 'cat out.txt'}]}]}}))
        rsh.CONTEXT_CAP = 100
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            rsh.run(tmp, log=tmp / 'hooks.log')
        ctx = json.loads(buf.getvalue())['hookSpecificOutput']['additionalContext']
        cases.append(("2. the last repo's spoken commands lead, ahead of a first repo "
                      "that overflows the cap",
                      ctx.startswith(f'{head}\n- "Debut" -> debut: stage 4')))
        cases.append(('2. ...and the block ends where its `- ` lines do',
                      'noise after the block' not in ctx.split('\n\n')[0]))
        practices = tmp / 'set' / 'practices'
        practices.mkdir(parents=True)
        (practices / 'debut.md').write_text(
            '---\nslug: debut\ntitle: Debut\ntier: on-demand\nstatus: active\n'
            'occasion: "a person says \\"Debut\\""\n'
            'index_clause: "stage 4: staging into main, full checks"\n'
            'command: {"Debut": "Stage 4."}\n---\n\n## Rule\n\nMove it.\n', encoding='utf-8')
        import build_views as bv
        block = psp.spoken_block(bv.load_practices(practices)) \
            if hasattr(psp, 'spoken_block') else ''
        cases.append(('1. a practice with a command is one line of the block',
                      block == f'{head}\n- "Debut" -> debut: stage 4: staging '
                               f'into main, full checks\n'))
    except (OSError, ValueError, KeyError, TypeError) as e:
        cases.append((f'fixture could not be built ({type(e).__name__}: {e})', False))
    finally:
        if saved_cap is not None:
            rsh.CONTEXT_CAP = saved_cap
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_a_brought_sets_spoken_trigger_reaches_the_session_at_start():
    """A consumer's session searched the clones for "Debut" (2026-10-04).

    The ladder's stage words live in a set the person brings, which is
    deferred to the untracked .precedent/SESSION_PRACTICES.md. A practice
    set's own hook hands that file back as context; a consumer's session-start
    hook only ran precedent_session_practices.py, which wrote the file and
    printed nothing, and the consumer's generated Standing instruction never
    pointed at it, because a brought set is left out of defers_sources.

    1. The write prints the file on stdout -- a SessionStart hook's output
       is what reaches the session -- with a spoken trigger's line in it.
       Since 2026-10-08 that line is in the spoken-commands list the file
       opens with, not in its occasion index.
    2. --quiet writes the same file and prints nothing, and the set's own
       hook, which emits the file itself, passes it. A consumer declines that
       hook, so its start-up script (templates/bootstrap.sh) runs the write.
    3. A loader block whose sources are all tracked still carries the
       read-it-too sentence."""
    import io, contextlib, tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_session_practices as psp
        import build_views as bv
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-spoken-trigger-'))
    saved_collect = psp.collect
    try:
        practices = tmp / 'set' / 'practices'
        practices.mkdir(parents=True)
        (practices / 'planted-stage.md').write_text(
            '---\n'
            'slug: planted-stage\n'
            'title: Debut\n'
            'tier: on-demand\n'
            'status: active\n'
            'occasion: "a person says \\"Debut\\""\n'
            'index_clause: "stage 4: staging into main, full checks"\n'
            'command: {"Debut": "Stage 4."}\n'
            '---\n\n## Rule\n\nMove staging into main.\n\n'
            '## Why\n\nSo staging is tested.\n', encoding='utf-8')
        extra = bv.load_practices(practices)
        repo = tmp / 'consumer'
        repo.mkdir()
        psp.collect = lambda r, skip_brought=False: (
            extra, {'planted-stage': 'shared'},
            [('deferred', 'a brought set, deferred to this file')])

        def run(*flags):
            out, saved_argv = io.StringIO(), sys.argv
            sys.argv = ['precedent_session_practices.py', '--repo', str(repo), *flags]
            # The person's own sets stay out of the fixture: main() also
            # notes a real source clone that is off its base branch, and on
            # 2026-10-31 that printed three lines into a --quiet run while
            # the clones sat on staging (practice: fixture-owns-its-state).
            saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
            os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-such-config.json')
            try:
                with contextlib.redirect_stdout(out), \
                        contextlib.redirect_stderr(io.StringIO()):
                    psp.main()
            finally:
                sys.argv = saved_argv
                if saved_cfg is None:
                    os.environ.pop('PRECEDENT_USER_CONFIG', None)
                else:
                    os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
            written = repo / '.precedent' / 'SESSION_PRACTICES.md'
            return out.getvalue(), (written.read_text(encoding='utf-8')
                                    if written.is_file() else '')
        said, written = run()
        line = '"Debut" -> planted-stage: stage 4'
        cases.append(('1. the session-start write prints the file, spoken trigger and all',
                      line in said and line in written))
        (repo / '.precedent' / 'SESSION_PRACTICES.md').unlink()
        said, written = run('--quiet')
        cases.append(('2. --quiet writes the same file and prints nothing',
                      said.strip() == '' and line in written))
        hook = (ROOT / 'tools' / 'precedent-universal-catalogue.sh').read_text(encoding='utf-8')
        cases.append(("2. ...and the set's hook, which emits the file whole, passes --quiet",
                      'precedent_session_practices.py" --repo "$P" --quiet' in hook))
        boot = (ROOT / 'templates' / 'bootstrap.sh').read_text(encoding='utf-8')
        cases.append(("2. ...and a consumer's start-up script runs the write at all",
                      'python3 tools/precedent_session_practices.py' in boot))
        block, _t, _n = bv.build_loader_block(extra, defers_sources=False)
        cases.append(('3. a block that defers nothing still points at the file',
                      '.precedent/SESSION_PRACTICES.md exists, read it too' in block))
    except (OSError, TypeError, ValueError) as e:
        cases.append((f'fixture could not be built ({e})', False))
    finally:
        psp.collect = saved_collect
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))


def check_session_file_says_each_command_once():
    """A consuming repository's session file went over its ceiling on
    2026-10-08, and part of what it paid for was every spoken command twice:
    precedent_session_practices.py printed a spoken-commands block ahead of
    the file, and the file's occasion index listed the same practices again.

    1. The file's first section, under its title, is the spoken-commands
       block, and it lists every practice that defines a command.
    2. The file's occasion index has no line for any of them, and still has
       the line of a practice that defines none.
    3. The tracked AGENTS.md block, rendered by the same function without the
       option, still lists the command practices in its index.
    4. main() prints that block once: the file, which opens with it, and
       nothing ahead of it.
    5. A brought set's command is charged to the person's brought budget:
       what the repository pays is the file rendered without the brought
       set, though that set's command line is in the full file.

    Negative control, run by hand when this landed: with render() passing
    omit_commands=False, case 2 fails and the rest pass."""
    import io, contextlib, tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_session_practices as psp
        import build_views as bv
    finally:
        sys.path.pop(0)
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-commands-once-'))
    saved = (psp.collect, psp.brought_budget, psp.pr.load_config)
    try:
        def practice(d, slug, occasion, clause, command=None):
            d.mkdir(parents=True, exist_ok=True)
            (d / f'{slug}.md').write_text(
                '---\n'
                f'slug: {slug}\n'
                f'title: {slug}\n'
                'tier: on-demand\n'
                'status: active\n'
                f'occasion: "{occasion}"\n'
                f'index_clause: "{clause}"\n'
                + (f'command: {json.dumps(command)}\n' if command else '')
                + '---\n\n## Rule\n\nDo it.\n', encoding='utf-8')
        own, brought = tmp / 'own', tmp / 'ladder'
        practice(own, 'deep-check', 'asked for a \\"deep check\\"',
                 'every audit, plus a full read', {'Deep check': 'Check it all.'})
        practice(own, 'install', 'installing Precedent into a repo',
                 'precedent_install.py, declare the set')
        practice(brought, 'planted-stage', 'a person says \\"Debut\\"',
                 'stage 4: staging into main', {'Debut': 'Stage 4.'})
        bare = bv.load_practices(own)
        full = bare + bv.load_practices(brought)
        levels = {'deep-check': 'universal', 'install': 'universal',
                  'planted-stage': 'shared'}
        repo = tmp / 'consumer'
        repo.mkdir()
        text = psp.render(full, levels, [], repo=str(repo))
        head = psp.SPOKEN_HEAD
        lines = text.split('\n')
        title = next(i for i, l in enumerate(lines) if l.startswith('# '))
        first = next(l for l in lines[title + 1:] if l.strip())
        cases.append(('1. the file opens, under its title, with the spoken commands',
                      first == head))
        cases.append(('1. ...and they list every practice that defines one',
                      '- "Deep check" -> deep-check: every audit' in text
                      and '- "Debut" -> planted-stage: stage 4' in text))
        index = text.split('## Occasion index', 1)[-1]
        cases.append(('2. the file\'s occasion index has no line for a command practice',
                      '## Occasion index' in text
                      and 'deep-check —' not in index and 'planted-stage —' not in index))
        cases.append(('2. ...and keeps the line of a practice that defines none',
                      'install — precedent_install.py' in index))
        tracked, _t, _n = bv.build_loader_block(full)
        cases.append(('3. the tracked AGENTS.md block still lists the command '
                      'practices in its index',
                      'deep-check — every audit' in tracked
                      and 'planted-stage — stage 4' in tracked and head not in tracked))

        notes = [('deferred', 'a brought set, deferred to this file')]
        bare_levels = {k: v for k, v in levels.items() if v != 'shared'}
        psp.collect = lambda r, skip_brought=False: (
            (bare, bare_levels, notes) if skip_brought else (full, levels, notes))
        out = io.StringIO()
        # Not the person's own sets (2026-10-31: their clones on staging put
        # an off-base notice ahead of the file; fixture-owns-its-state).
        saved_cfg = os.environ.get('PRECEDENT_USER_CONFIG')
        os.environ['PRECEDENT_USER_CONFIG'] = str(tmp / 'no-such-config.json')
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                psp.main(['--repo', str(repo)])
        finally:
            if saved_cfg is None:
                os.environ.pop('PRECEDENT_USER_CONFIG', None)
            else:
                os.environ['PRECEDENT_USER_CONFIG'] = saved_cfg
        said = out.getvalue()
        cases.append(('4. main() prints the commands once, at the top of the file',
                      said.count(head) == 1 and said.count('"Debut" -> planted-stage') == 1
                      and said.lstrip().startswith('<!-- GENERATED')))

        psp.pr.load_config = lambda r: [
            {'level': 'shared', 'name': 'ladder', 'path': str(brought),
             'brought': True}]
        psp.brought_budget = lambda repo=None: (1000, None)
        n = bv._approx_tokens(psp.render(full, levels, notes, repo=str(repo)))
        charged, share, names, budget = psp.charged_to_repo(str(repo), n)
        bare_text = psp.render(bare, bare_levels, notes, repo=str(repo))
        cases.append(('5. the repository pays for the file without the brought set',
                      share > 0 and charged == bv._approx_tokens(bare_text),
                      f'charged {charged}, bare {bv._approx_tokens(bare_text)}, '
                      f'share {share}'))
        cases.append(("5. ...though the brought set's command is in the full file "
                      "and not in that one",
                      '"Debut" -> planted-stage' in text and '"Debut"' not in bare_text))
        # 2026-10-09: the file on disk was written by an older engine at
        # session start and measured 190 tokens more than this engine's
        # render, and n less the share charged all 190 to the repository.
        stale, _s, _n, _b = psp.charged_to_repo(str(repo), n + 190)
        cases.append(('6. a file on disk that an older engine wrote does not move '
                      'the charge: it is the bare render, whatever n says',
                      stale == charged == bv._approx_tokens(bare_text),
                      f'charged {stale} for n+190, {charged} for n'))
    except (OSError, TypeError, ValueError, StopIteration, AttributeError) as e:
        cases.append((f'fixture could not be built ({type(e).__name__}: {e})', False))
    finally:
        psp.collect, psp.brought_budget, psp.pr.load_config = saved
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [name for name, ok, *_ in cases if not ok]
    detail = '; '.join(f'{c[0]} ({c[2]})' if len(c) > 2 and not c[1] else c[0]
                       for c in cases if not c[1])
    return (not failed, f'{len(cases)} stated cases', detail)


def check_show_follows_a_deduplicated_slug_across_sources():
    """precedent_show.py SLUG follows a deduplicated slug to the rule in
    force, across declared sources and through a set's copy that names its
    own slug (in force under that name elsewhere). 2026-10-04: file-mention-
    links, merged into rule-links by way of the writing set, answered
    "unknown slug", while current-rule-governs tells every session this tool
    follows a deduplicated copy to the live one. CONTROL: a slug nothing
    declares is still unknown."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-show-chain-'))
    cases = []

    def practice(slug, status='active', to='null', rule='Do the thing.'):
        return (_move_fixture_practice(slug)
                .replace('status:      active\nin_force_at: null',
                         f'status:      {status}\nin_force_at: {to}')
                .replace('## Rule\nDo the thing.', '## Rule\n' + rule))
    try:
        a, b = tmp / 'set-a', tmp / 'set-b'
        for d, name in ((a, 'fx-set-a'), (b, 'fx-set-b')):
            (d / 'practices').mkdir(parents=True)
            (d / 'precedent-source.json').write_text(json.dumps({'name': name, 'level': 'shared'}),
                                                     encoding='utf-8')
        (a / 'practices' / 'zz-old.md').write_text(practice('zz-old', 'deduplicated', 'zz-old'),
                                                   encoding='utf-8')
        (b / 'practices' / 'zz-old.md').write_text(practice('zz-old', 'deduplicated', 'zz-new'),
                                                   encoding='utf-8')
        (b / 'practices' / 'zz-new.md').write_text(practice('zz-new', rule='The live rule.'),
                                                   encoding='utf-8')
        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'precedent.json').write_text(json.dumps({'format_version': 1, 'sources': [
            {'level': 'shared', 'name': 'fx-set-a', 'path': str(a)},
            {'level': 'shared', 'name': 'fx-set-b', 'path': str(b)}]}), encoding='utf-8')
        env = {**os.environ, 'PRECEDENT_USER_CONFIG': str(tmp / 'no-user-config.json')}

        def show(slug):
            r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_show.py'),
                                '--repo', str(repo), slug], capture_output=True, text=True,
                               env=env, timeout=120)
            return r.returncode, r.stdout + r.stderr
        rc, out = show('zz-old')
        cases.append(('a slug deduplicated through a set\'s own-name copy shows the rule '
                      'it was merged into, and says so',
                      rc == 0 and 'zz-old -> zz-new' in out and 'The live rule.' in out
                      and 'was merged into `zz-new`' in out, failure_detail(out, 500)))
        rc, out = show('zz-nothing')
        cases.append(('CONTROL: a slug nothing declares is still unknown',
                      rc != 0 and 'unknown slug' in out, failure_detail(out, 300)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {str(d)[:400]}' for n, d in bad))


def check_bound_set_tools_and_reply_examples_are_held_in_any_set():
    """Two general holds, run in any repository, never keyed to a set
    (2026-10-20). (1) precedent_resolve.undeclared_bound_calls names every
    engine name a bound set tool reads through what its bind() set, beyond
    the tuple the engine declares for its key -- found through
    BOUND_SET_TOOLS, so a new bound tool needs no new test. (2) The
    reply-rules-hold-their-examples check runs a requirement's own example
    replies through the real reply check. Each with its control. Also every
    set cloned on this machine: its bound tools call only declared names."""
    import tempfile
    import precedent_resolve as pr
    import precedent_check as pc
    cases = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / 'set'
        (root / 'tools').mkdir(parents=True)
        (root / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-set', 'branch_moves': 'tools/zz_moves.py'}))
        tool = root / 'tools' / 'zz_moves.py'
        tool.write_text('core = None\n\ndef bind(engine):\n    global core\n'
                        '    core = engine\n\ndef main():\n'
                        '    return core.MAIN, core.zz_not_declared()\n')
        got = [(k, n) for k, _r, n, _l in pr.undeclared_bound_calls(root)]
        cases.append(('THE DISCRIMINATING CASE: an undeclared engine name is named',
                      got == [('branch_moves', 'zz_not_declared')], got))
        tool.write_text(tool.read_text().replace('core.zz_not_declared()', 'core.STAGING'))
        got = pr.undeclared_bound_calls(root)
        cases.append(('CONTROL: only declared names, nothing named', got == [], got))
        tool.write_text('import precedent_branches as core\n\ndef main():\n'
                        '    return core.zz_not_declared()\n')
        got = pr.undeclared_bound_calls(root)
        cases.append(('CONTROL: a module with no bind() is not a bound tool', got == [], got))

        (root / 'reply_check.json').write_text(json.dumps([
            {'practice': 'zz', 'require_one_of': ['ZZ-OK'],
             '_examples': [{'reply': 'done. ZZ-OK', 'refused': False},
                          {'reply': 'done.', 'refused': True}]},
            {'practice': 'zz2', 'require_one_of': ['ZZ2']}]))
        got = pc._reply_example_problems(root)
        cases.append(('examples the requirement answers as declared: no problem, and '
                      'the requirement without examples is named',
                      got == ([], [1]), got))
        (root / 'reply_check.json').write_text(json.dumps([
            {'practice': 'zz', 'require_one_of': ['ZZ-OK'], 'advisory': True,
             '_examples': [{'reply': 'done.', 'refused': False}]}]))
        wrong, _bare = pc._reply_example_problems(root)
        cases.append(('THE DISCRIMINATING CASE: an example the requirement answers '
                      'otherwise is named, advisory or not', len(wrong) == 1
                      and 'refuses' in wrong[0][1], wrong))
        (root / 'reply_check.json').write_text(json.dumps([
            {'practice': 'zz', 'require_quiet_while_background_runs': {'why': 'zz'},
             '_examples': [{'reply': 'One passed, two run.', 'refused': True,
                            'wake': {'quiet_owed': True, 'running': ['b1']}},
                           {'reply': 'One passed, two run.', 'refused': False}]},
            {'practice': 'zz2', 'require_plan_done_if_says': ['ZZ-ARCHIVE']}]))
        got = pc._reply_example_problems(root)
        cases.append(('2026-10-29: an example carries the wake it is judged under, '
                      'and a rule that reads the machine is not asked for examples',
                      got == ([], []), got))
    for path in sorted(p for p in ROOT.parent.iterdir()
                       if p != ROOT and (p / 'precedent-source.json').is_file()):
        got = pr.undeclared_bound_calls(path)
        cases.append((f'{path.name}, cloned here: its bound tools call only '
                      f'declared names', got == [], got))
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'bound set tools and reply-rule examples are held in any set '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n} -- {str(d)[:200]}' for n, d in bad))


def _with_user_config(path):
    """-> a restore() for PRECEDENT_USER_CONFIG, after pointing it at `path`."""
    saved = os.environ.get('PRECEDENT_USER_CONFIG')
    os.environ['PRECEDENT_USER_CONFIG'] = str(path)

    def restore():
        if saved is None:
            os.environ.pop('PRECEDENT_USER_CONFIG', None)
        else:
            os.environ['PRECEDENT_USER_CONFIG'] = saved
    return restore


def check_resolver_leaves_out_the_set_itself_by_name():
    """precedent_resolve.declared_source_paths leaves the repository itself
    out by name, not only by path, for a declared set and for one the
    individual set brings (is_repository_itself). Until 2026-10-18 it
    compared paths, so a checkout of a set elsewhere -- the --run-tests
    worktree, a CI clone -- listed the set's own clone as a second source;
    #1198 fixed that in set_words.py alone. A different set still lists
    (the control)."""
    import precedent_resolve as pr
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        for d, name in (('clone', 'zz-set'), ('other', 'zz-other'),
                        ('wt', 'zz-set'), ('ind', 'zz-ind'), ('zz-brought', 'zz-brought')):
            (tmp / d / '.git').mkdir(parents=True)
            (tmp / d / 'precedent-source.json').write_text(json.dumps(
                {'name': name, 'level': 'shared'}))
        (tmp / 'ind' / 'precedent-source.json').write_text(json.dumps(
            {'name': 'zz-ind', 'level': 'individual', 'brings': [
                {'name': 'zz-set', 'repo_url': 'https://github.com/o/zz-set'},
                {'name': 'zz-brought', 'repo_url': 'https://github.com/o/zz-brought'}]}))
        (tmp / 'zz-set' / '.git').mkdir(parents=True)
        (tmp / 'wt' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'zz-set', 'path': '../clone'},
            {'level': 'shared', 'name': 'zz-other', 'path': '../other'}]}))
        cfg = tmp / 'config.json'
        cfg.write_text(json.dumps({'individual': {'name': 'zz-ind',
                                                  'path': str(tmp / 'ind')}}))
        restore = _with_user_config(cfg)
        try:
            got = sorted(n for _p, _l, n, _note in pr.declared_source_paths(tmp / 'wt'))
        finally:
            restore()
    check('a set checked out in a second place is not its own source, '
          'declared or brought', got == ['zz-brought', 'zz-ind', 'zz-other'],
          f'declared_source_paths gave {got}')


def check_a_missing_clone_says_not_cloned():
    """A source whose declared path holds nothing reads "not cloned at
    <path>", naming a clone of the same set found elsewhere; "has no
    practices/ directory" is kept for a directory that is there
    (precedent_resolve.missing_source_reason). 2026-10-18: the session check
    said a set "has no practices/ directory" at a path where nothing
    existed, while the set sat cloned under another home."""
    import precedent_resolve as pr
    import tempfile
    saved = os.environ.get('HOME')
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / 'home' / 'zz-set' / 'practices').mkdir(parents=True)
        (tmp / 'empty').mkdir()
        os.environ['HOME'] = str(tmp / 'home')
        try:
            gone = pr.missing_source_reason(str(tmp / 'decl' / 'zz-set'), 'zz-set')
            none = pr.missing_source_reason(str(tmp / 'decl' / 'zz-none'), 'zz-none')
            there = pr.missing_source_reason(str(tmp / 'empty'), 'empty')
        finally:
            if saved is None:
                os.environ.pop('HOME', None)
            else:
                os.environ['HOME'] = saved
    check('a missing clone reads as not cloned, naming the clone elsewhere',
          gone.startswith('not cloned at') and str(tmp / 'home' / 'zz-set') in gone
          and none.startswith('not cloned at') and 'a clone of it' not in none
          and there.endswith('has no practices/ directory'),
          f'{gone!r} / {none!r} / {there!r}')


def check_off_base_sources_are_named():
    """A declared set whose clone is on a feature branch, or detached, is
    named at session start (precedent_resolve.off_base_sources), because the
    loader reads it from whatever is checked out. 2026-10-18: a session
    working on a set's feature branch had every repository bringing that set
    read its rules from there. On its base branch it is not named (the
    control)."""
    import precedent_resolve as pr
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        s = tmp / 'zz-set'
        g = ['git', '-C', str(s), '-c', 'user.name=t', '-c', 'user.email=t@e']
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(s)], check=True)
        subprocess.run(g + ['commit', '-q', '--allow-empty', '-m', 'x'], check=True)
        (tmp / 'repo').mkdir()
        (tmp / 'repo' / 'precedent.json').write_text(json.dumps({'sources': [
            {'level': 'shared', 'name': 'zz-set', 'path': '../zz-set'}]}))
        restore = _with_user_config(tmp / 'no-config.json')
        try:
            on_main = pr.off_base_sources(tmp / 'repo')
            subprocess.run(g + ['switch', '-q', '-c', 'feature'], check=True)
            on_feature = pr.off_base_sources(tmp / 'repo')
            subprocess.run(g + ['switch', '-q', '--detach'], check=True)
            detached = pr.off_base_sources(tmp / 'repo')
        finally:
            restore()
    check('a set read from a feature branch or a detached HEAD is named',
          on_main == [] and [w for _n, _p, w, _b in on_feature] == ['branch feature']
          and len(detached) == 1 and detached[0][2].startswith('a detached HEAD'),
          f'main {on_main}; feature {on_feature}; detached {detached}')


def check_declared_identity_has_a_passing_state_in_a_shared_repo():
    """`planted-author-rule` and `planted-dates-rule` have to be able to PASS in
    a repo many people commit to.

    Both computed the expected author from an `identity.json` at the
    consuming repo's root and reported a VIOLATION when it was absent --
    while check_commit_author.py's own comment says a shared consuming repo
    must NOT have one, because an identity.json at a repo's root means
    "this repository is somebody's individual practice source" and putting
    one there pins one person onto everyone committing. So in any shared
    repo those two checks were permanently red with the fix forbidden by
    the same file that demanded it (found 2026-09-10 installing
    precedent-beta-v01 into a real project).

    precedent_resolve.declared_identity() is the engine's answer: look
    where commit-identity.sh already looks, in its order, and raise
    NoDeclaredIdentity -- a check's cue to `raise NotApplicable` -- rather
    than return an absence a caller will read as a violation. These cases
    assert the order and, above all, that "shared repo" is a DISTINCT
    outcome from "wrong author"."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_resolve as pr
    import precedent_identity as pi
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-identity-'))
    cases = []

    # WHERE THE RESOLUTION LIVES, which is the half that was wrong first
    # (2026-09-10, the same day it landed). It was born in
    # precedent_resolve.py, which is CONSUMER_ENGINE_FILES-only because a
    # practice SET resolves no catalogue -- so the two checks this whole
    # change exists to fix went from enforcing to SKIPPED inside
    # `precedent-individual` itself, the one repository that most certainly
    # HAS an identity (a root identity.json is what declares one). Identity
    # is about a person; the resolver is about a catalogue, and only the
    # second reason keeps a file out of a set. These cases pin that down so
    # it cannot drift back.
    cases.append(('the resolution lives in precedent_identity.py, which is '
                  'in ENGINE_FILES -- so a practice SET vendors it and its '
                  'own identity checks can enforce rather than skip',
                  'precedent_identity.py' in pve.ENGINE_FILES,
                  str(pve.ENGINE_FILES)))
    cases.append(('and therefore reaches consumers too',
                  'precedent_identity.py' in pve.CONSUMER_ENGINE_FILES,
                  str(pve.CONSUMER_ENGINE_FILES)))
    cases.append(('precedent_resolve.py re-exports both names rather than '
                  'keeping a second implementation, so a consumer that '
                  'already imports them from there keeps working',
                  pr.declared_identity is pi.declared_identity
                  and pr.NoDeclaredIdentity is pi.NoDeclaredIdentity, ''))
    # The one duplication the move required: precedent_identity.py cannot
    # import these FROM the resolver without reintroducing the dependency it
    # exists to break, so it restates them. Assert they stay identical
    # rather than trusting that nobody edits one of the two.
    cases.append(('the user-config constants the two modules each declare '
                  'are identical -- the duplication the move required is '
                  'checked, not trusted',
                  pr.USER_CONFIG_ENV == pi.USER_CONFIG_ENV
                  and pr.DEFAULT_USER_CONFIG == pi.DEFAULT_USER_CONFIG,
                  f'{pr.USER_CONFIG_ENV!r}/{pi.USER_CONFIG_ENV!r} '
                  f'{pr.DEFAULT_USER_CONFIG}/{pi.DEFAULT_USER_CONFIG}'))

    # And the property that actually matters, exercised the way the failure
    # arrived rather than grepped for: stand the module up ALONE, with no
    # precedent_resolve.py anywhere on the path, which is exactly the state
    # a practice set is in. A stray module-scope import would fail here and
    # nowhere else in this file.
    alone = tmp / 'engine-alone'
    alone.mkdir(parents=True)
    shutil.copy2(ROOT / 'tools' / 'precedent_identity.py',
                 alone / 'precedent_identity.py')
    solo = subprocess.run(
        [sys.executable, '-c',
         'import sys, json; sys.path.insert(0, sys.argv[1]); '
         'import precedent_identity as m; '
         'ok = False\n'
         'try:\n'
         '    m.declared_identity(sys.argv[2])\n'
         'except m.NoDeclaredIdentity:\n'
         '    ok = True\n'
         'print(json.dumps({"ok": ok, "resolver_loaded": '
         '"precedent_resolve" in sys.modules}))',
         str(alone), str(tmp)],
        capture_output=True, text=True, timeout=120,
        # OWN every input that can change the answer. An inherited
        # PRECEDENT_COMMIT_EMAIL is step 1 of the resolution order, so a
        # session that exports one -- the individual set's own
        # settings.json does -- would hand this fixture an identity and
        # the case would pass for the wrong reason, proving nothing about
        # where the module lives. Same for the user config and PYTHONPATH.
        env={**{k: v for k, v in os.environ.items()
                if not k.startswith('PRECEDENT_')},
             'PYTHONPATH': '',
             'PRECEDENT_USER_CONFIG': str(tmp / 'no-such-config.json')})
    solo_out = {}
    try:
        solo_out = json.loads(solo.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        pass
    cases.append(('precedent_identity stands up with NO precedent_resolve.py '
                  'on the path at all -- the exact state a practice set is '
                  'in, and the state the old placement failed in',
                  solo.returncode == 0 and solo_out.get('ok') is True
                  and solo_out.get('resolver_loaded') is False,
                  solo.stdout + solo.stderr))

    # A seeded practice set really receives the file. ENGINE_FILES membership
    # is the declaration; this is the delivery.
    seeded = tmp / 'seeded-set' / 'tools'
    seeded.mkdir(parents=True)
    for name in pve.ENGINE_FILES:
        src = ROOT / 'tools' / name
        if src.is_file():
            shutil.copy2(src, seeded / name)
    cases.append(('a practice set seeded from ENGINE_FILES receives '
                  'precedent_identity.py, so its own planted-author-rule and '
                  'planted-dates-rule checks can import it',
                  (seeded / 'precedent_identity.py').is_file(),
                  str(sorted(f.name for f in seeded.iterdir()))))
    # This asserted `not (seeded / 'precedent_resolve.py').is_file()` until
    # 2026-09-13, when the resolver deliberately moved INTO ENGINE_FILES so a
    # practice set can read the universal catalogue (shape 3,
    # spec/SOURCE_SET_PROSE_GAP.md). The invariant that mattered is NOT
    # membership -- it is that precedent_identity.py stands alone, which the
    # solo case above proves directly by running it with no resolver on the
    # path at all. What is left of the consumer-only boundary is the
    # materializing pair, so that is what this case now asserts: a set
    # materializes nothing and must not be handed the tools that do.
    # precedent_materialize.py joined ENGINE_FILES on 2026-10-17: a set's
    # session file delivers ships and registers hooks with it. Its writer is
    # refused in a set (check_materialize_run_directly_refuses_what_the_sync_
    # withholds), so the boundary that matters is the sync, still a
    # consumer's alone.
    cases.append(('a seeded practice set does NOT receive '
                  'precedent_sync_views.py -- the consumer-only boundary that '
                  'survives the resolver moving into ENGINE_FILES -- and does '
                  'receive precedent_materialize.py for its session file',
                  (seeded / 'precedent_materialize.py').is_file()
                  and not (seeded / 'precedent_sync_views.py').is_file(),
                  str(sorted(f.name for f in seeded.iterdir()))))
    cases.append(('and DOES receive precedent_resolve.py and '
                  'precedent_session_practices.py, the pair that puts '
                  "universal's rules in front of a session rooted in a set",
                  (seeded / 'precedent_resolve.py').is_file()
                  and (seeded / 'precedent_session_practices.py').is_file(),
                  str(sorted(f.name for f in seeded.iterdir()))))
    # PRECEDENT_COMMIT_* is step 1 of the order, and this harness's own
    # process may carry it (verify_harness sets identity for its fixtures).
    # Pop it for the cases that are about the other steps, or step 1 answers
    # every one of them and the check passes for the wrong reason.
    saved = {k: os.environ.pop(k) for k in
             ('PRECEDENT_COMMIT_EMAIL', 'PRECEDENT_COMMIT_NAME',
              'PRECEDENT_COMMIT_TZ') if k in os.environ}
    try:
        shared = tmp / 'shared-consumer'
        shared.mkdir()
        empty_cfg = tmp / 'no-individual.json'
        empty_cfg.write_text('{"individual": null}', encoding='utf-8')
        raised = None
        try:
            pr.declared_identity(shared, user_config=empty_cfg)
        except pr.NoDeclaredIdentity as e:
            raised = e
        cases.append(('a SHARED repo with no root identity.json and no '
                      'individual source raises NoDeclaredIdentity -- its own '
                      'outcome, so a check can skip rather than report a '
                      'violation nobody can clear', raised is not None,
                      'returned an identity instead of raising'))
        cases.append(('and the message says why that is the expected state '
                      'rather than a defect',
                      raised is not None and 'not a defect' in str(raised),
                      str(raised)))

        # A repo that IS an individual source: step 2.
        own = tmp / 'individual-source'
        own.mkdir()
        (own / 'identity.json').write_text(json.dumps({
            'name': 'Fixture Person', 'email': 'fixture@example.com',
            'timezone': 'America/Argentina/Buenos_Aires'}), encoding='utf-8')
        got_own = pr.declared_identity(own, user_config=empty_cfg)
        cases.append(('a repo whose own root carries identity.json resolves '
                      'from it -- that is what such a file MEANS',
                      got_own['email'] == 'fixture@example.com'
                      and got_own['timezone'].endswith('Buenos_Aires'),
                      str(got_own)))

        # The override names the person without a zone: the repo's own
        # identity.json supplies it (2026-09-25 -- an environment that kept
        # PRECEDENT_COMMIT_NAME/EMAIL and dropped PRECEDENT_COMMIT_TZ left
        # the individual source reporting "declares no timezone").
        _saved = {k: os.environ.get(k) for k in
                  ('PRECEDENT_COMMIT_EMAIL', 'PRECEDENT_COMMIT_NAME',
                   'PRECEDENT_COMMIT_TZ')}
        try:
            os.environ['PRECEDENT_COMMIT_EMAIL'] = 'fixture@example.com'
            os.environ['PRECEDENT_COMMIT_NAME'] = 'Fixture Person'
            os.environ.pop('PRECEDENT_COMMIT_TZ', None)
            got_env = pr.declared_identity(own, user_config=empty_cfg)
            got_env_shared = pr.declared_identity(shared, user_config=empty_cfg)
        finally:
            for k, v in _saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        cases.append(('an environment override with no zone takes the zone '
                      "from the repo's own identity.json",
                      got_env['timezone'].endswith('Buenos_Aires'), str(got_env)))
        cases.append(('...and in a shared repo, with no identity.json, it has '
                      'none', got_env_shared['timezone'] == '',
                      str(got_env_shared)))

        # A shared repo whose PERSON has an individual source: step 3. This
        # is the case the two checks needed and never had.
        cfg = tmp / 'user-config.json'
        cfg.write_text(json.dumps({'individual': {
            'name': 'precedent-individual', 'path': str(own)}}),
            encoding='utf-8')
        got_shared = pr.declared_identity(shared, user_config=cfg)
        cases.append(('a SHARED repo resolves the identity from the '
                      "INDIVIDUAL SOURCE's root, which is where the practice "
                      'text says it lives and where commit-identity.sh '
                      'already reads it',
                      got_shared['email'] == 'fixture@example.com',
                      str(got_shared)))
        cases.append(('and says where it came from, so a finding can name it',
                      'individual practice source' in got_shared['source'],
                      str(got_shared)))

        # An identity.json that exists but declares no email is not an
        # identity: falling through beats returning a nameless one.
        blank = tmp / 'blank-identity'
        blank.mkdir()
        (blank / 'identity.json').write_text('{"timezone": "UTC"}',
                                             encoding='utf-8')
        blank_raised = False
        try:
            pr.declared_identity(blank, user_config=empty_cfg)
        except pr.NoDeclaredIdentity:
            blank_raised = True
        cases.append(('an identity.json with no email is not an identity',
                      blank_raised, 'it returned one anyway'))
    finally:
        os.environ.update(saved)
        shutil.rmtree(tmp, ignore_errors=True)

    # Step 1 last, with the variable deliberately set, so the pops above are
    # not quietly hiding a broken override path.
    os.environ['PRECEDENT_COMMIT_EMAIL'] = 'override@example.com'
    try:
        override = pr.declared_identity(ROOT)
        cases.append(('an explicit PRECEDENT_COMMIT_EMAIL wins outright',
                      override['email'] == 'override@example.com',
                      str(override)))
    finally:
        os.environ.pop('PRECEDENT_COMMIT_EMAIL', None)
        os.environ.update(saved)

    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'declared_identity() gives a shared repo a passing state instead '
          f'of a permanent violation ({len(cases)} stated cases)',
          not bad,
          '; '.join(f'{n} -- {d}' for n, d in bad))


def check_brought_sets_have_their_own_session_budget():
    """The sets a person brings are charged to `brought_sets_tokens` in that
    person's individual set, never to the repository's ceiling for
    .precedent/SESSION_PRACTICES.md (Morgan, 2026-10-03, strength:
    assented). A consumer rehearsal found the ladder put two repositories'
    session files over their ceilings, refusing every push there.

    1. bringing a set with a resident rule has a measured share > 0;
    2. no budget declared: the share stays charged to the repository,
       as before the budget existed;
    3. a budget at least the share: no finding, and the repo is charged the
       file less the share;
    4. CONTROL: a budget under the share is a finding;
    5. CONTROL: a person who brings nothing has a share of 0;
    6-8. the ceiling Update Vendors seeds and the over-target line take the
       same split, with a CONTROL that the repo's own part still counts."""
    import tempfile, contextlib, io
    import json as _json
    import precedent_session_practices as psp
    import precedent_check as pc
    import precedent_resolve as pr

    saved = {k: os.environ.get(k) for k in (
        'PRECEDENT_ASSUME_LADDER', 'PRECEDENT_USER_CONFIG', pr.NO_LADDERS_ENV)}
    for k in saved:                       # practice: fixture-owns-its-state
        os.environ.pop(k, None)
    saved_root = pc.ROOT
    results = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            uni = tmp / 'universal'
            (uni / 'practices').mkdir(parents=True)
            (uni / 'practices' / 'plain-rule.md').write_text(
                _move_fixture_practice('plain-rule'), encoding='utf-8')
            home = tmp / 'home'
            lad = home / 'fx-ladder'
            (lad / 'practices').mkdir(parents=True)
            (lad / 'precedent-source.json').write_text(_json.dumps({
                'name': 'fx-ladder', 'level': 'shared', 'provides': ['ladder']}),
                encoding='utf-8')
            (lad / 'practices' / 'fx-stage.md').write_text(
                _move_fixture_practice('fx-stage').replace(
                    'tier:        on-demand', 'tier:        resident')
                .replace('Do the thing.', 'Do the thing. ' * 60),
                encoding='utf-8')
            ind = home / 'precedent-individual'
            (ind / 'practices').mkdir(parents=True)
            repo = tmp / 'consumer'
            repo.mkdir()
            (repo / 'precedent.json').write_text(_json.dumps({
                'format_version': 1, 'visibility': 'private',
                'sources': [{'level': 'universal', 'name': 'precedent',
                             'path': str(uni)}]}), encoding='utf-8')
            cfg = tmp / 'user.json'
            cfg.write_text(_json.dumps({'format_version': 1, 'individual': {
                'name': 'precedent-individual', 'path': str(ind)}}),
                encoding='utf-8')
            os.environ['PRECEDENT_USER_CONFIG'] = str(cfg)
            pc.ROOT = repo

            def manifest(brings, budget=None):
                man = {'name': 'precedent-individual', 'level': 'individual',
                       'brings': brings}
                if budget is not None:
                    man[psp.BROUGHT_BUDGET_KEY] = budget
                (ind / 'precedent-source.json').write_text(_json.dumps(man),
                                                           encoding='utf-8')

            fx = [{'name': 'fx-ladder', 'repo_url': 'https://example.com/fx.git'}]
            manifest(fx)
            with contextlib.redirect_stderr(io.StringIO()):
                share, names = psp.brought_share(repo)
                results.append(('1: a brought resident rule has a share > 0',
                                share > 0 and names == ['fx-ladder'],
                                f'{share} {names}'))
                n, f = pc._charge_brought_share(1000 + share)
                results.append(('2: no budget declared: charged to the '
                                'repository, as before, with no finding',
                                f is None and n == 1000 + share, f'{n} {f}'))
                manifest(fx, budget=share + 10)
                n, f = pc._charge_brought_share(1000 + share)
                # Since 2026-10-09 the charge is the file as this engine
                # renders it now without the brought sets, never the figure
                # read off disk less the share (the two could come from
                # different engines).
                bare = psp._brought_renders(str(repo))[1]
                results.append(('3: within budget, no finding, and the repo is '
                                'charged the file rendered without the share',
                                f is None and bare is not None and n == bare,
                                f'{n} {f} bare={bare}'))
                manifest(fx, budget=max(0, share - 10))
                n, f = pc._charge_brought_share(1000 + share)
                results.append(('4: CONTROL: over budget is a finding',
                                f is not None and 'over the' in str(f), str(f)))
                # The seed and the target line read the same split as the
                # check (charged_to_repo): a ceiling written by Update
                # Vendors, and the over-target line, never count the brought
                # sets (2026-10-08, a consuming repository: seeded at 150,
                # re-measured by hand once the ladder arrived).
                manifest(fx, budget=share + 10)
                import precedent_bootstrap_source as pbs
                import session_load_trend as slt
                import build_views as bv
                full = psp.render(*psp.collect(str(repo)), repo=str(repo))
                (repo / '.precedent').mkdir(exist_ok=True)
                (repo / '.precedent' / 'SESSION_PRACTICES.md').write_text(
                    full, encoding='utf-8')
                pbs._write_session_load_budget(repo, occasion='test')
                reg_f = repo / 'tools' / 'session_load_budgets.json'
                reg = _json.loads(reg_f.read_text(encoding='utf-8'))
                ent = reg['surfaces']['.precedent/SESSION_PRACTICES.md']
                seeded_n = int(ent['_note'].split()[0])
                want = bv._approx_tokens(full) - share
                results.append(('6: the seeded ceiling measures the file less '
                                'the brought share', seeded_n == want,
                                f'seeded {seeded_n}, file {bv._approx_tokens(full)}, '
                                f'share {share}'))
                ent['target'] = want + 1
                reg_f.write_text(_json.dumps(reg), encoding='utf-8')
                results.append(('7: the over-target line charges the repo its '
                                'part only', slt.over_target(repo) == [],
                                str(slt.over_target(repo))))
                ent['target'] = want - 1
                reg_f.write_text(_json.dumps(reg), encoding='utf-8')
                results.append(('8: CONTROL: over its own part, it is reported',
                                len(slt.over_target(repo)) == 1, ''))
                manifest([])
                results.append(('5: CONTROL: bringing nothing has no share',
                                psp.brought_share(repo)[0] == 0, ''))
    finally:
        pc.ROOT = saved_root
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    failed = [(n, d) for n, ok, d in results if not ok]
    check(f'the sets a person brings are charged to their own session budget, '
          f'not the repository\'s ceiling ({len(results)} stated cases)',
          not failed, '; '.join(f'{n} -- {d}' for n, d in failed))


