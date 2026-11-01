# The harness tests for the BestPractice-to-Precedent conversion
#
# tools/harness/vh_conversion.py -- part of the verification harness:
# the BestPractice-to-Precedent conversion: the catalogue split into practice files, and nothing lost or invented.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def _whole_body(sections, join=' '):
    """Every body section, in file order.

    Three checks used to spell this list out by hand, and they disagreed with
    each other: two omitted `story`, so invented content there went unchecked,
    and all three omitted `detail` the moment it was added -- caught by the
    no-lost-content check firing on 17 practices, which is the one place a
    dropped section shows up as words going missing rather than as silence.
    Derive it from SECTION_ORDER instead; a sixth section is then in every
    content check by construction."""
    return join.join(sections.get(name, '') for name in SECTION_ORDER)


def check_content_preserved_by_sentence(files, original_practices_by_number):
    """Every sentence of every practice, exactly as BestPractice wrote it,
    exactly as many times, distributed across Rule/Why/Story/Install however
    the editorial split decided. Nothing invented, nothing lost, nothing
    duplicated -- at sentence granularity rather than word granularity."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        if _amended_and_logged(fm.get('slug', stem)):
            continue  # deliberately rewritten post-conversion; see CHANGES_TO_TELL_ALEX.md
        orig = original_practices_by_number.get(fm.get('source_practice_number'))
        if orig is None:
            continue  # reported by check_no_invented_content
        src = collections.Counter(_source_sentences(orig))
        out = collections.Counter(
            s for _n, ss in _output_sentences_by_section(sections) for s in ss)
        lost, gained = src - out, out - src
        if lost or gained:
            ok = False
            print(f"  {f.name}:")
            for s in list(lost)[:3]:
                print(f"      LOST     {s[:100]!r}")
            for s in list(gained)[:3]:
                print(f"      INVENTED {s[:100]!r}")
    check('content preserved sentence-for-sentence '
          '(' + '+'.join(s.capitalize() for s in SECTION_ORDER) + ' == the '
          'source practice, both directions)', ok)


def _list_items(text):
    """Every markdown list item, as (indent, marker, first 60 chars). The
    sentence checks normalize whitespace away, so they cannot see a nested
    list flattened to one level or a continuation line that lost its indent
    while being moved. This can: markdown structure is content, and a
    two-level list rendered as one is a changed meaning even though every
    word survived."""
    out = []
    for line in (text or '').split('\n'):
        m = _LIST_ITEM_RE.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2), ' '.join(m.group(3).split())[:60]))
    return out


def check_list_structure_preserved(files, original_practices_by_number):
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        if _amended_and_logged(fm.get('slug', stem)):
            continue  # deliberately rewritten post-conversion; see CHANGES_TO_TELL_ALEX.md
        orig = original_practices_by_number.get(fm.get('source_practice_number'))
        if orig is None:
            continue
        src = collections.Counter(
            _list_items(orig['rule']) + _list_items(orig['why']) + _list_items(orig['install']))
        out = collections.Counter(
            i for name in SECTION_ORDER for i in _list_items(sections.get(name, '')))
        if src != out:
            ok = False
            for item in list((src - out))[:3]:
                print(f"  {f.name}: list item lost or re-indented -- indent={item[0]} "
                      f"marker={item[1]!r} {item[2]!r}")
            for item in list((out - src))[:3]:
                print(f"  {f.name}: list item appeared or re-indented -- indent={item[0]} "
                      f"marker={item[1]!r} {item[2]!r}")
    check('markdown list structure preserved (indent and nesting, which the '
          'sentence checks normalize away)', ok)
def _tokens(text):
    return collections.Counter(w.lower() for w in WORD_RE.findall(text))


def check_no_invented_content(files, original_practices_by_number):
    ok = True
    for stem, (fm, sections, f) in files.items():
        if 'source_practice_number' not in fm:
            continue  # a practice minted fresh, no BestPractice ancestor to compare against
        if _amended_and_logged(fm.get('slug', stem)):
            continue  # deliberately rewritten post-conversion; see CHANGES_TO_TELL_ALEX.md
        num = fm.get('source_practice_number')
        if num in POST_SNAPSHOT_PRACTICE_NUMBERS:
            continue  # added to `main` after PRACTICES.md's snapshot -- no ancestor here by construction
        orig = original_practices_by_number.get(num)
        if orig is None:
            ok = False
            print(f"  {f.name}: no source_practice_number {num!r} found in PRACTICES.md")
            continue
        orig_body = orig['rule'] + ' ' + orig['why'] + ' ' + orig['install']
        out_body = _whole_body(sections)
        out_tokens = _tokens(out_body)
        orig_tokens = _tokens(orig_body)
        # token-multiset subset: every word the split file uses, it uses no
        # more often than the original practice body did. A word appearing
        # MORE in the output than the input is the mechanical signature of
        # invented content; this catches it without requiring a full,
        # order-sensitive sentence re-derivation.
        excess = out_tokens - orig_tokens
        if excess:
            ok = False
            print(f"  {f.name}: tokens not found (or over-used) in source practice "
                  f"{num}: {dict(list(excess.items())[:10])}")
    check('no invented content (output word-multiset <= source word-multiset, per practice)', ok)
def check_no_lost_content(files, original_practices_by_number):
    """The mirror of check_no_invented_content, and the reason it has to
    exist: that check is a SUBSET test (output <= source), so a conversion
    that silently DELETES authored text passes it trivially. Both
    directions together make it a multiset EQUALITY, which -- combined with
    byte-identical regeneration, which pins order -- is a far stronger
    statement than either alone."""
    ok = True
    for stem, (fm, sections, f) in files.items():
        if _amended_and_logged(fm.get('slug', stem)):
            continue  # deliberately rewritten post-conversion; see CHANGES_TO_TELL_ALEX.md
        num = fm.get('source_practice_number')
        orig = original_practices_by_number.get(num)
        if orig is None:
            continue  # already reported by check_no_invented_content
        orig_body = orig['rule'] + ' ' + orig['why'] + ' ' + orig['install']
        out_body = _whole_body(sections)
        lost = _tokens(orig_body) - _tokens(out_body)
        if lost:
            ok = False
            print(f"  {f.name}: source words missing from the split file for practice "
                  f"{num}: {dict(list(lost.items())[:10])}")
    check('no lost content (source word-multiset <= output word-multiset, per practice)', ok)


def check_corruption_drop_is_a_duplicate(original_practices_by_number):
    """The one place the converter is licensed to delete source text is the
    practice-39 corruption (split_practices.FIXUP_39_MARKER). Every other
    check here takes that span's BOUNDARIES on faith: no-invented-content
    and no-lost-content both compare against a source already parsed through
    the same fixup, and byte-identical regeneration's approved exception was
    hand-written to match it -- so a wrong boundary makes all three agree
    with the bug instead of catching it. That is not hypothetical: the
    boundary WAS wrong, and deleted practice 39's entire Install paragraph
    with the harness fully green.

    So this check tests the boundary against a property that does not depend
    on where the boundary was drawn: whatever the converter drops must be a
    VERBATIM DUPLICATE of text appearing elsewhere in PRACTICES.md. That is
    the whole claim being made about it. Authored content -- practice 39's
    own Install paragraph, say -- is a duplicate of nothing, so an
    over-broad drop fails here immediately. It reads the span
    split_practices.py actually dropped rather than re-deriving one, since a
    check that recomputes the boundary cannot catch a converter that got the
    boundary wrong."""
    original = CATALOGUE.read_text(encoding='utf-8')
    drops = {num: p['dropped_corruption'] for num, p in original_practices_by_number.items()
             if p.get('dropped_corruption')}
    if not drops:
        check('corruption drop is a verbatim duplicate, not authored content', False,
              'split_practices.py dropped nothing at all -- the practice-39 corruption '
              'fixup is no longer firing. If PRACTICES.md was fixed upstream, retire the '
              'fixup and this check together; otherwise this is a regression')
        return
    ok = True
    for num, dropped in sorted(drops.items()):
        # A true duplicate occurs at least twice in the file.
        if original.count(dropped) < 2:
            ok = False
            print(f"  practice {num}: the {len(dropped)}-char span split_practices.py drops "
                  f"(starting {dropped[:70]!r}) does NOT occur verbatim anywhere else in "
                  f"PRACTICES.md -- it is not a duplicate, so dropping it is content loss")
    check('corruption drop is a verbatim duplicate, not authored content', ok)
def _body_lines(text):
    """Normalized non-blank lines of a practice body, for duplicate
    detection. Whitespace-collapsed so a re-wrap is not mistaken for a
    rewrite, and vice versa."""
    return [' '.join(l.split()) for l in text.split('\n') if l.strip()]


def _shared_runs(named_line_lists, min_run):
    """-> list of (name_a, name_b, run_length, first_line). Indexes every
    window of `min_run` consecutive lines by content, so a window appearing
    under two different names is a duplicated span. Hash-based rather than
    pairwise-DP: 52 practices is 1,326 pairs, and this stays linear."""
    windows = collections.defaultdict(list)
    for name, lines in named_line_lists:
        for i in range(len(lines) - min_run + 1):
            window = tuple(lines[i:i + min_run])
            # A run with no word in it -- closing braces and a code fence --
            # is how every JSON example ends, not copied text (2026-09-28:
            # two practices' examples both ended `}`, `}`, and a fence).
            if not any(re.search(r'[A-Za-z0-9]', l) for l in window):
                continue
            windows[window].append((name, i))
    seen_pairs = {}
    for window, places in windows.items():
        names = {n for n, _i in places}
        if len(names) < 2:
            continue
        for a_i in range(len(places)):
            for b_i in range(a_i + 1, len(places)):
                (na, ia), (nb, ib) = places[a_i], places[b_i]
                if na == nb:
                    continue
                key = tuple(sorted((na, nb)))
                # keep the longest run reported per pair
                prev = seen_pairs.get(key)
                if prev is None or prev[0] < min_run:
                    seen_pairs[key] = (min_run, window[0])
    return [(a, b, n, first) for (a, b), (n, first) in sorted(seen_pairs.items())]


def check_duplicate_runs_skip_wordless_lines():
    """_shared_runs reports shared prose, not shared punctuation: two JSON
    examples that both end with closing braces and a fence are not a
    duplicated span, and a real shared run is still found."""
    punct = ['}', '}', '```']
    prose = ['the same sentence here', 'and a second line', 'and a third']
    cases = [
        ('three wordless lines shared by two practices are not reported',
         _shared_runs([('a', ['x'] + punct), ('b', ['y'] + punct)], 3) == []),
        ('three shared lines of prose still are',
         len(_shared_runs([('a', prose), ('b', prose)], 3)) == 1),
        ('a run mixing a word line with braces still counts',
         len(_shared_runs([('a', ['"k": 1', '}', '}']),
                           ('b', ['"k": 1', '}', '}'])], 3)) == 1),
    ]
    failed = [n for n, ok in cases if not ok]
    return (not failed, f'{len(cases)} stated cases', '; '.join(failed))

def check_no_cross_practice_duplication(files, original_practices_by_number):
    """Catches the class of defect that produced this conversion's worst bug
    at source, rather than only cleaning up after it.

    BestPractice's PRACTICES.md carried, for two weeks, a 1,645-character
    verbatim duplicate of practice 34's tail pasted onto the end of practice
    39 -- introduced by a hand-renumbering of a collided practice range
    (upstream 5d28da6), starting mid-word at a line-wrap boundary, with no
    heading of its own. Nothing detected it; it was found only because a
    mechanical converter choked on it.

    A practice is a self-contained unit. Two practices sharing three or more
    consecutive identical lines is a paste artifact, a bad merge, or a
    practice that should have been retired in favour of the one it
    duplicates -- all three are defects, none is a thing to do on purpose.
    Runs over practices/, so it keeps working after PRACTICES.md retires,
    and over PRACTICES.md itself while it is still the upstream source."""
    ok = True

    named = [(stem, _body_lines(_whole_body(sections, join='\n')))
             for stem, (fm, sections, f) in sorted(files.items())]
    for a, b, n, first in _shared_runs(named, DUPLICATE_RUN_LINES):
        ok = False
        print(f"  practices/{a}.md and practices/{b}.md share {n}+ consecutive identical "
              f"lines, starting {first[:70]!r}")

    # And the same question asked of the upstream source file, so a re-sync
    # that imports a FRESH corruption is caught on arrival.
    #
    # The one duplication already known and handled -- practice 39's tail,
    # dropped by split_practices.FIXUP_39_MARKER and reported upstream on
    # 2026-08-31 -- is acknowledged rather than re-failed. The exception is
    # tied to the span the converter actually drops, not to a hardcoded
    # practice number, so it unwinds by itself: when Alex fixes PRACTICES.md
    # upstream, the fixup stops firing, check_corruption_drop_is_a_duplicate
    # fails and tells us to retire the fixup, and this exception evaporates
    # with it. Nothing has to remember to clean it up.
    known = '\n'.join(p.get('dropped_corruption', '')
                      for p in original_practices_by_number.values())
    known_lines = set(_body_lines(known))
    src = CATALOGUE.read_text(encoding='utf-8')
    src_named = []
    for chunk in re.split(r'\n(?=## \d+\. )', src):
        m = re.match(r'## (\d+)\. ', chunk)
        if m:
            src_named.append((f"practice {m.group(1)}",
                              _body_lines(chunk.split('\n', 1)[1])))
    for a, b, n, first in _shared_runs(src_named, DUPLICATE_RUN_LINES):
        if first in known_lines:
            print(f"  (known) PRACTICES.md: {a} and {b} share text that "
                  f"split_practices.py already drops as upstream corruption -- "
                  f"reported upstream 2026-08-31, not fixed here (read-only access).")
            continue
        ok = False
        print(f"  PRACTICES.md: {a} and {b} share {n}+ consecutive identical lines, "
              f"starting {first[:70]!r} -- a NEW upstream corruption. Report it "
              f"rather than only working around it.")
    check(f'no cross-practice duplication (no two practices share '
          f'{DUPLICATE_RUN_LINES}+ consecutive identical lines)', ok)


def check_practice_heading_parsing():
    """A DIRECT unit test of split_practices._parse_practice_text against
    synthetic malformed headings, since precedent_check.py's
    practice-file-shape only scans the real, currently-committed
    practices/*.md tree -- it can only
    catch a malformed heading that happens to exist right now, never prove
    the parser handles one correctly in general.

    Two stated cases, from the fix's own history: trailing whitespace on a
    heading (the original bug: "## Detail " silently merged the whole
    section into the one before it) must still parse correctly, and a
    heading with the wrong CASE ("## detail" for the one optional section)
    must fail LOUDLY rather than reproduce the identical silent merge one
    character over -- which practice-file-shape cannot catch for exactly
    this section, since its mandatory sections deliberately exclude
    'detail' as legitimately optional."""
    def body(detail_heading):
        return (
            "---\nslug: fixture\ntitle: fixture\ntier: on-demand\n"
            "severity: default\napplies_to: [\"**\"]\nchecked_by: null\n"
            "defines: []\nstatus: active\nsupersedes: []\noverrides: null\n"
            "added: null\napproved_by: fixture\n---\n"
            "## Rule\nThe rule text.\n\n"
            f"{detail_heading}\nDetail text that must not leak into Rule.\n\n"
            "## Why\nWhy text.\n\n## Story\nStory text.\n\n"
            "## Install\nInstall text.\n")

    cases = []

    # A tab, not just a trailing space, must still be tolerated.
    fm, sections = sp._parse_practice_text(body("## Detail\t"))
    cases.append(('a tab after the heading name still parses correctly',
                  sections.get('rule', '').strip() == 'The rule text.'
                  and sections.get('detail', '').strip()
                  == 'Detail text that must not leak into Rule.'))

    # The bug this check exists to close: a case typo on the one OPTIONAL
    # section must not silently merge into ## Rule -- it must be refused.
    try:
        sp._parse_practice_text(body("## detail"))
        cases.append(('a case typo on `## detail` is refused, not silently '
                       'merged into `## Rule`', False))
    except sp.PracticeFileError as e:
        cases.append(('a case typo on `## detail` is refused, not silently '
                       'merged into `## Rule`', 'detail' in str(e).lower()))

    # A real sub-heading at a DIFFERENT level (### inside a section body)
    # must not be mistaken for a malformed section marker.
    fm, sections = sp._parse_practice_text(body(
        "## Detail\n\n### A sub-heading some Detail sections use"))
    cases.append(('a `###` sub-heading inside a section body is left alone',
                  'sub-heading' in sections.get('detail', '')))

    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        if not passed:
            print(f"  practice heading parsing did NOT behave as stated: {name}")
    check(f'practice section heading parsing ({len(cases)} stated cases: '
          f'whitespace tolerated, a case typo refused loudly, a deeper '
          f'sub-heading left alone)', ok)
def check_catalogue_anchors():
    """tools/catalogue_stats.py's own ANCHORS list -- prose sentences
    elsewhere that restate a figure the script computes -- is checked by
    catalogue_stats.py's own `main()`, but nothing ever called it as part
    of this repo's actual gate suite. Found by a 2026-09-01 deep-check
    audit as the reason PRACTICE_ENGINE_PLAN.md could carry a stale "8"
    for months after spec/PRACTICE_FORMAT.md was corrected to 7, with an
    explicit note about the correction, the same day: the mechanism built
    specifically to catch this drift existed and worked, but was never
    wired to anything that runs automatically. This wires it in."""
    passes, fails = cs.check_anchors()
    for f in fails:
        print(f"  {f}")
    check(f'catalogue anchors ({len(passes) + len(fails)} stated figures: a '
          f'prose sentence citing a script-derived number must still agree '
          f'with what the script computes)', not fails)


def check_superseded_source_says_so():
    """A document that was the SOURCE for a generated replacement must say so.

    PRACTICES.md was the single-file catalogue phase 1 converted into
    practices/. The conversion landed 2026-08-31 and PRACTICES.md stopped
    being the catalogue that same day -- but nothing said so, and AGENTS.md's
    quick index went on pointing at it as "What each practice is and why".
    Twenty practices were minted over the next week; none appeared in it.
    Morgan found it while asking where a new index should live, 2026-09-07.

    NOTHING WAS BROKEN, WHICH IS THE POINT. check_source_coverage asks
    "does every practice in PRACTICES.md still have a file?" -- the MIGRATION
    direction, correct for the migration, and permanently green afterwards.
    The reverse question was never asked, and a practice minted after the
    conversion carries `source_practice_number: null` and is explicitly
    `continue`d, so it is invisible to the only check that reads both. A
    document can be a month out of date, still linked as authoritative, and
    every gate green.

    So the third state is what this refuses: **behind AND silent**. Either
    PRACTICES.md is current with the catalogue, or it declares itself
    superseded. It may not be neither. The banner is the cheap half -- a
    reader who opens the file learns in one line that it is frozen -- and
    this check is what stops a later session deleting the banner to tidy the
    file up, or "refreshing" the document without refreshing its content.

    Generalises past this one file: any repo doing a one-time conversion
    leaves its source behind, and the source is the thing everyone keeps
    linking.
    """
    cat = ROOT / 'PRACTICES.md'
    if not cat.is_file():
        not_applicable('a superseded conversion source says so',
                       'PRACTICES.md is not present here')
        return

    text = cat.read_text(encoding='utf-8')
    numbered = set(re.findall(r'^## (\d+)\.', text, re.M))

    minted_after = []
    for f in sorted((ROOT / 'practices').glob('*.md')):
        fm, _sections = sp._read_practice_file(f)
        num = fm.get('source_practice_number')
        if num is None or str(num).strip('"').strip("'") in ('', 'null'):
            minted_after.append(fm.get('slug', f.stem))

    behind = len(minted_after) > 0
    # "Declares itself superseded" means the machine-readable field, not a
    # sentence somebody hopes is read: kind/status frontmatter is the same
    # contract document-status-header applies under spec/ and record/.
    declared = bool(re.search(r'^status:\s*superseded\s*$', text, re.M))
    points_at_successor = bool(re.search(r'^superseded_by:\s*\S+', text, re.M))

    cases = [
        ('PRACTICES.md is either current with practices/ or declares '
         'status: superseded -- never behind and silent',
         (not behind) or declared),
        ('and when superseded, it names what replaced it',
         (not behind) or points_at_successor),
        ('the check can actually see the drift it is gating on -- a '
         'zero-drift reading would make this pass for the wrong reason',
         behind or len(numbered) >= len(list((ROOT / 'practices').glob('*.md')))),
    ]

    failed = [n for n, ok in cases if not ok]
    detail = '; '.join(failed)
    if failed and behind:
        detail += (f" [{len(minted_after)} practice(s) exist that PRACTICES.md "
                   f"has never carried, e.g. {', '.join(sorted(minted_after)[:3])}]")
    check(f'a superseded conversion source says so, rather than going stale '
          f'quietly ({len(cases)} stated cases)', not failed, detail)


def check_changed_files_compares_quoted_counts_when_a_practice_changes():
    """A practice change whose quoted count no longer matches what
    tools/catalogue_stats.py computes is refused at push time, not first
    found by main's GitHub test after a fast Produce.

    2026-10-11: repo-is-memory gained a Detail, which moved a count
    spec/PRACTICE_FORMAT.md quotes from 24 to 25; every quick check passed
    and main went red (issue #1088). A stub catalogue_stats.py stands in
    for the real one: failing, then passing, then a change that touches no
    practice, which never runs it."""
    import tempfile
    name = ('the changed-files check compares quoted counts when a practice '
            'changes')
    failing = ('import sys\nprint("  FAIL  [anchor] spec/PRACTICE_FORMAT.md: '
               'recites 24..24, this script derives 25..25")\nsys.exit(1)\n')
    passing = 'import sys\nsys.exit(0)\n'
    with tempfile.TemporaryDirectory() as td:
        commit, run = _changed_files_fixture(
            pathlib.Path(td) / 'red', {'tools/catalogue_stats.py': failing})
        commit({'practices/zz-rule.md': '## Rule\nA rule.\n'})
        rc, out = run()
        commit2, run2 = _changed_files_fixture(
            pathlib.Path(td) / 'green', {'tools/catalogue_stats.py': passing})
        commit2({'practices/zz-rule.md': '## Rule\nA rule.\n'})
        rc2, out2 = run2()
        commit3, run3 = _changed_files_fixture(
            pathlib.Path(td) / 'other', {'tools/catalogue_stats.py': failing})
        commit3({'notes/zz.md': 'not a practice\n'})
        rc3, out3 = run3()
    cases = [
        ('a changed practice whose quoted count is stale is refused', rc == 1),
        ('the refusal names the stale figure and what to update',
         'recites 24..24' in out and 'catalogue_stats.py' in out),
        ('control: the same change with the counts in step passes', rc2 == 0),
        ('a change that touches no practice and no quoting doc does not run '
         'the comparison', rc3 == 0),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed,
          '; '.join(failed) + ('' if not failed else
                               f' -- {failure_detail(out, 500)} / {failure_detail(out2, 300)} / {failure_detail(out3, 300)}'))


def check_session_start_refreshes_an_attached_team_clone():
    """A shared source that is already on disk is PULLED at session start, not
    waved through.

    THE INCIDENT (2026-09-11). sources_from_repo() returned
    `(name, True, 'already on disk')` the moment a clone had a practices/
    directory, so a team clone was pulled exactly once -- when it was created
    -- and every session afterwards read whatever it held that day. Measured
    on a real container: four attached sources 4, 4, 6 and 19 commits behind
    their own origin/main, with the session-start line reporting all four
    fine.

    The cost surfaced nowhere near the cause. This harness kept failing
    `every reachable copy of commit-identity.sh is byte-identical`, naming
    four repositories whose committed copies were in fact already canonical:
    the drift was in the stale clones on disk. A session reading it would go
    fix four repositories that had nothing wrong with them.

    Three cases, and the second and third are what keep the fix honest: a
    clone that cannot be fast-forwarded must stay IN FORCE (it is on disk and
    resolvable) while saying plainly that it was not refreshed, and it must
    not be clobbered -- somebody's uncommitted work in a source clone is
    still their work.
    """
    import json as _json, shutil, subprocess as sp, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_bootstrap as psb

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-team-refresh-'))
    env = dict(os.environ)
    env.update({'GIT_CONFIG_GLOBAL': str(tmp / 'gitconfig'),
                'PRECEDENT_ALLOW_ANY_AUTHOR': '1',
                'GIT_AUTHOR_NAME': 'Harness', 'GIT_COMMITTER_NAME': 'Harness',
                'GIT_AUTHOR_EMAIL': 'harness@example.com',
                'GIT_COMMITTER_EMAIL': 'harness@example.com'})
    (tmp / 'gitconfig').write_text('', encoding='utf-8')

    def git(d, *a, check=True):
        r = sp.run(['git', '-C', str(d), *a], capture_output=True, text=True,
                   env=env)
        if check and r.returncode != 0:
            raise RuntimeError(f'fixture setup: git {" ".join(a)}: '
                               f'{(r.stderr or r.stdout).strip()}')
        return r

    cases = []
    try:
        upstream = tmp / 'precedent-team-fixture'
        upstream.mkdir()
        sp.run(['git', 'init', '-q', '-b', 'main', str(upstream)], env=env,
               capture_output=True, text=True, check=True)
        (upstream / 'practices').mkdir()
        (upstream / 'practices' / 'x.md').write_text('v1\n', encoding='utf-8')
        git(upstream, 'add', '-A'); git(upstream, 'commit', '-qm', 'one')

        clone = tmp / 'clone-of-it'
        sp.run(['git', 'clone', '-q', f'file://{upstream}', str(clone)],
               env=env, capture_output=True, text=True, check=True)

        # Upstream moves after the clone was taken -- the ordinary state of
        # every attached source on a container that has been up for a day.
        (upstream / 'practices' / 'x.md').write_text('v2\n', encoding='utf-8')
        git(upstream, 'commit', '-qam', 'two')

        repo = tmp / 'consumer'
        repo.mkdir()
        (repo / 'precedent.json').write_text(_json.dumps(
            {'format_version': 1,
             'sources': [{'level': 'team', 'name': 'precedent-team-fixture',
                          'path': '../clone-of-it'}]}), encoding='utf-8')

        name, ok, msg = psb.sources_from_repo(repo)[0]
        cases.append(('a team clone that is behind its own origin is '
                      'fast-forwarded at session start',
                      ok and (clone / 'practices' / 'x.md').read_text().strip()
                      == 'v2', msg))
        cases.append(('and the line says it moved, rather than only that the '
                      'clone exists',
                      'fast-forwarded' in msg, msg))

        name, ok, msg = psb.sources_from_repo(repo)[0]
        cases.append(('a second run reports it current rather than claiming '
                      'to have moved it again',
                      ok and 'current' in msg and 'fast-forwarded' not in msg,
                      msg))

        # A source clone somebody is editing: not this tool's to clobber.
        (clone / 'practices' / 'x.md').write_text('v2\nlocal work\n',
                                                  encoding='utf-8')
        (upstream / 'practices' / 'x.md').write_text('v3\n', encoding='utf-8')
        git(upstream, 'commit', '-qam', 'three')
        name, ok, msg = psb.sources_from_repo(repo)[0]
        cases.append(('a clone with uncommitted work is left alone',
                      'local work' in (clone / 'practices' / 'x.md').read_text(),
                      msg))
        cases.append(('it stays IN FORCE -- present and resolvable is not the '
                      'same as current', ok, msg))
        cases.append(('and it says it could not be refreshed, naming git\'s '
                      'own reason rather than a bare pronoun',
                      'could NOT be brought up to date' in msg
                      and 'local changes' in msg, msg))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(n, d) for n, okc, d in cases if not okc]
    check(f'session start refreshes an attached team clone rather than '
          f'waving it through ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:200]}' for n, d in bad))


def check_null_frontmatter_is_absent():
    """A `null` frontmatter field parses as absent, not as the string 'null'.

    Every value the practice reader returns is raw field text, so a null
    field used to arrive as the literal `'null'` -- truthy, not None, not
    int-parseable. Every `if x is None` and `if 'x' not in fm` guard
    written against the four nullable fields was therefore dead code that
    had never once run, because every practice inherited from PRACTICES.md
    carries a real value in all four.

    This is worst in exactly the repos with no inherited practices at all.
    A brand-new team or individual set bootstrapped from
    templates/practice-set-*/ ships a starter practice with `checked_by:
    null`, `overrides: null` and `added: null`, so a new adopter's very
    first practice takes these paths, and a migrated repo whose practices
    are all locally authored takes them for every single one.

    Found 2026-09-06, when the first freshly-minted practice landed in
    practices/. `split_practices.py build` did not print the careful
    "no source_practice_number" message its author wrote for exactly this
    case -- it crashed on `int('null')` instead, and nine practices were
    already in that state.

    Null is dropped rather than stored as None deliberately: every caller
    that supplies its own default keeps behaving identically, including
    precedent_retire.py, whose `checked_by not in ('null', '')` would read
    None as a real value."""
    import tempfile
    fresh = ('---\nslug:        fx-null\ntitle:       "Fixture"\n'
             'tier:        on-demand\nseverity:    default\n'
             'applies_to:  ["**"]\noccasion:    "x"\ngates:       []\n'
             'index_clause: "x"\nchecked_by:  null\ndefines:     []\n'
             'status:      active\nsupersedes:  []\noverrides:   null\n'
             'added:       null\napproved_by: "A New Adopter"\n'
             'source_practice_number: null\n---\n## Rule\nx\n\n'
             '## Why\nx\n\n## Story\nx\n\n## Install\nx\n')
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / 'fx-null.md'
        f.write_text(fresh, encoding='utf-8')
        fm, _sections = sp._read_practice_file(f)

    nullable = ('checked_by', 'overrides', 'added', 'source_practice_number')
    present = [k for k in nullable if k in fm]
    check(f'a null frontmatter field is absent, so `k not in fm` and '
          f'`fm.get(k) is None` both work ({len(nullable)} nullable fields)',
          not present, f'still present: {present}')

    # The defaults every caller relies on must be untouched by that.
    check("a caller's own 'null' default still arrives as 'null', so "
          "precedent_retire.py's `not in ('null', '')` keeps working",
          fm.get('checked_by', 'null') == 'null'
          and fm.get('overrides', 'null') == 'null')

    # And a real value must still come through raw, quotes and all -- the
    # convention every reader in this codebase is written against.
    check('a non-null field is still returned as raw field text',
          fm.get('title') == '"Fixture"' and fm.get('status') == 'active',
          f'title={fm.get("title")!r} status={fm.get("status")!r}')

    # ONE reader for both formats. They had their own copies until
    # 2026-09-06 and had already drifted on exactly this: candidates
    # decoded null to None, practices kept the string. Pinned by behaviour
    # rather than by grepping for the import, so a re-forked copy that
    # happens to agree today still has to keep agreeing.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc_cand', ROOT / 'tools' / 'precedent_candidate.py')
    pcand = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcand)
    cand_fm, _body = pcand._parse_frontmatter(
        '---\nslug: x\nproposed_checked_by: null\n---\nbody\n')
    check('the candidate reader applies the same null policy as the '
          'practice reader -- absent, not None, not the string',
          'proposed_checked_by' not in cand_fm, str(cand_fm))
    check('and it still decodes its own format: a quoted scalar and a list '
          'come back as Python values',
          pcand._parse_frontmatter(
              '---\ntitle: "A, B"\nproposed_gates: ["merge", "push"]\n---\nx\n'
          )[0] == {'title': 'A, B', 'proposed_gates': ['merge', 'push']})

    # The end-to-end symptom, not just the parser: the command that broke.
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'split_practices.py'),
                        'build'], capture_output=True, text=True, cwd=str(ROOT))
    out = r.stdout + r.stderr
    check('split_practices.py build reports unnumbered practices by name '
          'instead of crashing on int(\'null\')',
          'Traceback' not in out and 'no source_practice_number' in out,
          failure_detail(out, 200))


