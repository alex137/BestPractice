# The harness tests for migrations and decommissioning
#
# tools/harness/vh_migrations.py -- part of the verification harness:
# migrations and decommissioning.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.


def check_citation_integrity(files):
    valid_numbers = {fm['source_practice_number'] for fm, _, _ in files.values()
                     if 'source_practice_number' in fm}
    ok = True
    for stem, (fm, sections, f) in files.items():
        text = f.read_text(encoding='utf-8')
        for m in CITATION_RE.finditer(text):
            if m.group(1) not in valid_numbers:
                ok = False
                print(f"  {f.name}: cites 'practice {m.group(1)}', which does not "
                      f"exist as any source_practice_number")
    check('citation integrity (every "practice N" reference resolves)', ok)


def check_doc_lint_fires():
    """doc_lint.py gates every push (AGENTS.md's "Two check levels") and had
    NEVER been given a direct unit test of its own internals -- this repo's
    own checkable-gets-checked convention, applied to the tool that
    enforces it on everyone else. Plants two regressions a 2026-09-01
    deep-check audit found and fixed, plus the clean-input and still-caught
    counterparts check_leak_gate_fires()'s family always pairs a fix with
    (a check that fires on everything is as useless as one that fires on
    nothing).

    1. Cross-line strikethrough: renders_del() used to test one PHYSICAL
       LINE at a time, but GFM strikethrough can open on one line and close
       on a later one within the same paragraph. GitHub renders the whole
       span as one <del>; the old per-line test never saw it, since neither
       half alone contains a matching pair of tildes.
    2. check_residue()'s "this is just a link to the record doc" allow-list
       only recognized `_record.md`/`_diligence.md`, not the four other
       record-doc suffixes is_record_doc() (and RECORD_NAME_RE) already
       treat as record docs -- so a line that was legitimately just a link
       to thing_decision.md (etc.) was falsely flagged as residue."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-doclint-'))
    cases = []
    real_root = dl.ROOT
    try:
        dl.ROOT = tmp

        (tmp / 'cross.md').write_text(
            "This is ~begin unwanted strike\nstrike end~ still here\n",
            encoding='utf-8')
        strikes, *_ = dl.check_file('cross.md', fix=False, known=None)
        cases.append(('a strikethrough span across two lines is caught',
                      bool(strikes)))

        (tmp / 'same.md').write_text("a rate of ~50~ items exactly\n",
                                     encoding='utf-8')
        strikes2, *_ = dl.check_file('same.md', fix=False, known=None)
        cases.append(('a same-line strikethrough is still caught (the '
                       'original, non-regressed case)', bool(strikes2)))

        (tmp / 'clean.md').write_text(
            "Nothing strange here.\n\nAnother clean paragraph.\n",
            encoding='utf-8')
        strikes3, *_ = dl.check_file('clean.md', fix=False, known=None)
        cases.append(('clean prose with no tildes is not flagged',
                      not strikes3))

        (tmp / 'linked.md').write_text(
            "See the [user decision](thing_decision.md) for why.\n",
            encoding='utf-8')
        residue = dl.check_residue('linked.md')
        cases.append(('a link to a *_decision.md record is not flagged as '
                       'residue', not residue))

        (tmp / 'flagged.md').write_text("[verify: headcount] later.\n",
                                        encoding='utf-8')
        residue2 = dl.check_residue('flagged.md')
        cases.append(('a genuine verify-later flag is still caught',
                      bool(residue2)))

        # 2026-10-01, a consumer's published pages: the same leaks written
        # as prose passed the bracketed patterns and reached readers. Each
        # line below has the shape of one that leaked (the words are made
        # up); each must fire, and the plain prose beside them must not.
        leaked = [
            "unit prices carried from memory, rough, until checked.",
            "The vendor figures stay rough until checked against sources.",
            "and the second warehouse, which the next revision opens with.",
            "every figure checked against search-engine snippets of the page.",
            "the export case is open. The record carries the rest.",
        ]
        for n, line in enumerate(leaked):
            (tmp / f'prose{n}.md').write_text(line + "\n", encoding='utf-8')
            cases.append((f'a prose verify-later or record note is caught: '
                          f'{line[:40]}...',
                          bool(dl.check_residue(f'prose{n}.md'))))
        (tmp / 'prose-clean.md').write_text(
            "The craft revisits the site on the next pass; the pilot recalled "
            "the checklist and the tail fin was checked.\n", encoding='utf-8')
        cases.append(('plain prose near those words is not residue',
                      not dl.check_residue('prose-clean.md')))

        # 2026-10-10: a repo that declares its reader-facing documents has
        # answered which files are deliverables. A rule that tells a writer
        # not to quote "from memory", in a working document it did not
        # declare, is the rule itself, not residue; the same words in a
        # declared document still fire. title_case caches its config per
        # root, so the cache is cleared on both sides of the declaration.
        import title_case as _tc
        _tc._PATHS_CONFIG.clear()
        (tmp / 'precedent.json').write_text(
            '{"output_paths": ["guide.md"]}', encoding='utf-8')
        rule = "Don't reconstruct a quote from memory; mark it to check.\n"
        (tmp / 'rulebook.md').write_text(rule, encoding='utf-8')
        (tmp / 'guide.md').write_text(rule, encoding='utf-8')
        cases.append(('residue words in a working doc are not flagged when '
                      'the repo declares its output_paths without it',
                      not dl.check_residue('rulebook.md')))
        cases.append(('the same words in a declared output path are still '
                      'flagged', bool(dl.check_residue('guide.md'))))
        (tmp / 'precedent.json').unlink()
        _tc._PATHS_CONFIG.clear()
        cases.append(('with no output_paths declared, a working doc is '
                      'judged as before', bool(dl.check_residue('rulebook.md'))))

        # REF_RE's `[^`]+` swallows a whole command line, so a backticked
        # invocation counted as an unlinked file reference -- 177 of 2,323
        # findings in this tree on 2026-09-21, none of them fixable by a
        # link. It mattered because --strict promotes this class to a
        # failure. Both halves here: the command must stop being a finding
        # AND the bare filename beside it must still be one.
        (tmp / 'command.md').write_text(
            "Run `python3 tools/doc_lint.py` before pushing.\n"
            "One file per trap, at `gotchas/gotcha-<date>-<slug>.md`, and "
            "the catalogue is `practices/*.md`.\n"
            "The rule lives in practices/very-deep-check.md, named "
            "`very-deep-check.md`.\n",
            encoding='utf-8')
        _s, cmd_unlinked, *_ = dl.check_file('command.md', fix=False, known=None)
        cases.append(('a backticked COMMAND, a glob and a <placeholder> are '
                      'not unlinked file references, while a bare filename '
                      'in the same document still is',
                      [r for _i, r in cmd_unlinked] == ['very-deep-check.md']))

        # A practice or template ships into other repositories, where
        # `AGENTS.md` means the reader's own file and no link from here can
        # reach it (164 of 437 warnings in practices/ and templates/ on
        # 2026-10-29). Skipped there only: the same name elsewhere is this
        # repository's file and still warns, and a real reference beside it
        # in a practice still warns.
        (tmp / 'practices').mkdir(exist_ok=True)
        (tmp / 'practices' / 'shipped.md').write_text(
            "Read `AGENTS.md` first, then `spec/PLAN.md`.\n", encoding='utf-8')
        (tmp / 'local.md').write_text("Read `AGENTS.md` first.\n", encoding='utf-8')
        _s, ship_unlinked, *_ = dl.check_file('practices/shipped.md', fix=False, known=None)
        _s, local_unlinked, *_ = dl.check_file('local.md', fix=False, known=None)
        cases.append(('in a shipped practice, the reader\'s own AGENTS.md is '
                      'not an unlinked reference while spec/PLAN.md beside it '
                      'is, and AGENTS.md outside practices/ still is',
                      [r for _i, r in ship_unlinked] == ['spec/PLAN.md']
                      and [r for _i, r in local_unlinked] == ['AGENTS.md']))

        # Deep-check regression case: seen_acr used to be recorded only on
        # the VIOLATION branch (inside the `if ... f'({tok})' not in clean`
        # block), so a term correctly glossed on first use never actually
        # marked the acronym as seen -- a second, later BARE mention of the
        # same term still got flagged, defeating "expand on first use"
        # entirely for any document that used a glossed acronym twice.
        (tmp / 'glossed-twice.md').write_text(
            "Uses the pull request (PR) flow. Later, another PR lands.\n",
            encoding='utf-8')
        _s, _u, glossed_twice, *_ = dl.check_file('glossed-twice.md', fix=False, known=set())
        cases.append(("an acronym glossed on first use is not re-flagged on "
                      "a later bare mention in the same document",
                      not glossed_twice))

        (tmp / 'never-glossed.md').write_text(
            "Uses the ZQX flow. Later, another ZQX lands.\n", encoding='utf-8')
        _s, _u, never_glossed, *_ = dl.check_file('never-glossed.md', fix=False, known=set())
        cases.append(('an acronym never glossed at all is still caught '
                      '(the baseline case, not regressed by the fix above)',
                      bool(never_glossed)))

        # 2026-09-02 deep-check finding: a hyphenated filename used as its own
        # link label (the doc-references-are-links convention: `[docs-team/
        # BUSINESS-MODEL-CONCEPTS.md](docs-team/BUSINESS-MODEL-CONCEPTS.md)`)
        # split into spurious ALL-CAPS fragments at each hyphen (MODEL), since
        # _decontent only ever stripped the `](target)` half and left the
        # repeated filename label scannable. AI and AGENTS -- generic,
        # non-project-specific terms this repo's own AGENTS.md and its
        # AI-assistant boilerplate use constantly -- were never in the
        # stoplist either, so any repo's README carrying that boilerplate
        # warned on every doc_lint run.
        (tmp / 'selflink.md').write_text(
            "See [docs-team/BUSINESS-MODEL-CONCEPTS.md]"
            "(docs-team/BUSINESS-MODEL-CONCEPTS.md) for the full analysis.\n",
            encoding='utf-8')
        _s, _u, selflink_flagged, *_ = dl.check_file('selflink.md', fix=False, known=set())
        cases.append(('a hyphenated filename fragment used as its own '
                      'self-referential link label is not flagged',
                      not selflink_flagged))

        (tmp / 'reallink.md').write_text(
            "See the [ZQX report](file.md) for details.\n", encoding='utf-8')
        _s, _u, reallink_flagged, *_ = dl.check_file('reallink.md', fix=False, known=set())
        cases.append(('a real acronym inside a descriptive (non-self-'
                      'referential) link label is still caught',
                      bool(reallink_flagged)))

        (tmp / 'stoplist.md').write_text(
            "This repo's AGENTS.md tells AI assistants what to do.\n",
            encoding='utf-8')
        _s, _u, stoplist_flagged, *_ = dl.check_file(
            'stoplist.md', fix=False, known=set(dl.ACRONYM_STOP))
        cases.append(('AI and AGENTS -- generic, non-project-specific terms '
                      '-- are in the acronym stoplist and not flagged',
                      not stoplist_flagged))

        # An ALL-CAPS filename stem is a file reference, not an acronym --
        # and neither is a document naming itself in its own title. Both
        # were standing, unfixable warnings (LEDGER.md, SETUP.md's own
        # heading); the second one could only be cleared by the one person
        # who cannot clear it, the person editing that file.
        # --- the corpus rule: an initialism has no ordinary lowercase form,
        # a shouted word does. Decided from the repo's own prose, not from a
        # hand-maintained English wordlist -- a first pass at the
        # 101-warning problem added about forty such words by hand, which is
        # a list that grows forever and is wrong the first time somebody
        # shouts a word nobody thought of.
        (tmp / 'corpus_a.md').write_text(
            "We only do this before the end. only, before, end, only, before.\n"
            "The zqx index is never written in lowercase anywhere.\n".replace('zqx', 'ZZZ'),
            encoding='utf-8')
        (tmp / 'corpus_b.md').write_text(
            "You must ONLY do this BEFORE the END, per the ZQX index.\n",
            encoding='utf-8')
        dl._corpus_cache = None
        dl.corpus_word_forms()
        cases.append(('the corpus classifies a shouted English word as a word '
                      '(it appears in lowercase in the same corpus)',
                      all(dl.looks_like_a_word(w) for w in ('ONLY', 'BEFORE', 'END'))))
        cases.append(('and classifies a real initialism as an acronym (no '
                      'lowercase form anywhere in the corpus)',
                      not dl.looks_like_a_word('ZQX')))
        _s, _u, corpus_flagged, *_ = dl.check_file('corpus_b.md', fix=False, known=set())
        flagged = {tok for _i, tok in corpus_flagged}
        cases.append(('so the scan flags the initialism and leaves the shouted '
                      'words alone, with no wordlist involved',
                      'ZQX' in flagged and not ({'ONLY', 'BEFORE', 'END'} & flagged)))
        dl._corpus_cache = None

        (tmp / 'stems.md').write_text(
            "The ledger is [templates/harness/LEDGER.md](../t/LEDGER.md).\n",
            encoding='utf-8')
        _s, _u, stem_flagged, *_ = dl.check_file('stems.md', fix=False, known=set())
        cases.append(('an ALL-CAPS filename stem (LEDGER.md) is not '
                      'reported as an unglossed acronym', not stem_flagged))

        (tmp / 'SETUP.md').write_text("# SETUP - guided install\n", encoding='utf-8')
        _s, _u, selfname_flagged, *_ = dl.check_file('SETUP.md', fix=False, known=set())
        cases.append(("a document naming itself in its own title is not "
                      "reported as an unglossed acronym", not selfname_flagged))

        # 2026-09-19: precedent-team-writing's create-word-doc.md tripped the
        # acronym scan the moment a consumer repo first vendored it -- "found
        # via Part II, verified on MS Word desktop macOS 16.78.3" read "II"
        # as a brand-new unglossed acronym, on a file the consumer neither
        # wrote nor can edit (same shape as the blockquote case above:
        # acronyms-glossary gates on what a change ADDS, so a brand-new
        # vendored file has every token in it read as new). "II" is a roman
        # numeral, not an acronym -- nothing to gloss. "MS" in the same line
        # is a different case, deliberately NOT engine-exempted: it is a
        # real, ambiguous acronym (Microsoft here, but also Multiple
        # Sclerosis, Mississippi...) that this document already has a
        # convention for glossing inline ("Office Open XML (OOXML)"
        # elsewhere in the same file) -- so the scan is still expected to
        # catch it, and the fix for that line is at the source, not here.
        (tmp / 'numeral.md').write_text(
            "Found via Part II, verified on MS Word desktop.\n", encoding='utf-8')
        _s, _u, numeral_flagged, *_ = dl.check_file(
            'numeral.md', fix=False, known=set(dl.ACRONYM_STOP))
        flagged = {tok for _i, tok in numeral_flagged}
        cases.append(('a roman numeral ("Part II") is not reported as an '
                      'unglossed acronym, while a real, unglossed acronym '
                      '("MS") right beside it still is',
                      'II' not in flagged and 'MS' in flagged))
        cases.append(('the roman-numeral check is a grammar, not a stoplist '
                      '-- ZQX (a real, never-glossed acronym) does not '
                      'read as one',
                      not dl.looks_like_roman_numeral('ZQX')
                      and dl.looks_like_roman_numeral('II')))

        # 2026-10-13: "Please do XYZ" and "don't touch department QRST" in a
        # consuming repo's proposal were reported as unglossed acronyms, and
        # the repo glossed them as "not an abbreviation" to get past it.
        (tmp / 'placeholder.md').write_text(
            "Please do XYZ, and leave department QRST alone; TBD.\n",
            encoding='utf-8')
        _s, _u, ph_flagged, *_ = dl.check_file(
            'placeholder.md', fix=False, known=set(dl.ACRONYM_STOP) - {'TBD'})
        ph = {tok for _i, tok in ph_flagged}
        cases.append(('placeholder letters in alphabet order (XYZ, QRST) are '
                      'not reported as unglossed acronyms, while a real one '
                      '(TBD) beside them still is',
                      'XYZ' not in ph and 'QRST' not in ph and 'TBD' in ph))
        cases.append(('the placeholder check is a grammar, not a stoplist -- '
                      'LMN reads as one, ZQX and TBD do not',
                      dl.looks_like_placeholder('LMN')
                      and not dl.looks_like_placeholder('ZQX')
                      and not dl.looks_like_placeholder('TBD')))

        # --- broken relative links (check 7) -------------------------------
        # 96 links in this repo resolved to nothing before this check
        # existed; the largest group was practices/*.md written with
        # root-relative targets from a file one directory down.
        (tmp / 'tools').mkdir(exist_ok=True)
        (tmp / 'tools' / 'real.py').write_text('x\n', encoding='utf-8')
        (tmp / 'practices').mkdir(exist_ok=True)
        (tmp / 'practices' / 'p.md').write_text(
            "# Top\n"
            "Root-relative from a subdirectory: [a](tools/real.py).\n"
            "Correct: [b](../tools/real.py).\n"
            "In a code span, a value not a reference: `[c](tools/gone.py)`.\n"
            "```\n[d](tools/gone.py)\n```\n"
            "External: [e](https://example.com/x) and anchor [f](#top).\n",
            encoding='utf-8')
        dl._anchor_cache.clear()
        broken = dl.check_broken_links('practices/p.md')
        cases.append(('a root-relative link from a subdirectory is caught '
                      'as broken',
                      broken == [(2, 'tools/real.py', 'no such file')]))
        cases.append(('a correct ../ link, a link inside a code span, a link '
                      'inside a fenced block, an external URL and a bare '
                      'anchor that resolves are all left alone',
                      [t for _i, t, _w in broken] == ['tools/real.py']))

        (tmp / 'templates').mkdir(exist_ok=True)
        (tmp / 'templates' / 'README.md').write_text(
            "The engine lands at [tools/](tools/) when instantiated.\n",
            encoding='utf-8')
        cases.append(('templates/ is exempt -- its links name files in the '
                      'repo the template is instantiated INTO',
                      dl.check_broken_links('templates/README.md') == []))

        # ...but only for the PATH half. A fragment on a target that
        # resolves to a real file HERE is checked even under templates/:
        # the 2026-09-11 dead anchor in templates/document-project/README.md
        # survived a heading rename because the whole file returned [].
        # The control asserts WHICH failure, not merely that one happened
        # (practice: control-asserts-which-failure).
        (tmp / 'guide.md').write_text("# Install Into a Dependent Repo\n",
                                      encoding='utf-8')
        (tmp / 'templates' / 'anchored.md').write_text(
            "Live: [a](../guide.md#install-into-a-dependent-repo).\n"
            "Dead: [b](../guide.md#installing-into-a-repo-that-already-has-one).\n"
            "Still exempt: [c](tools/lands-there-later.py).\n",
            encoding='utf-8')
        dl._anchor_cache.clear()
        anchored = dl.check_broken_links('templates/anchored.md')
        cases.append(("a dead #fragment under templates/ IS caught, while a "
                      "live one and a path naming the instantiated tree are "
                      "not",
                      anchored == [(2, '../guide.md#installing-into-a-repo-'
                                       'that-already-has-one',
                                    'no heading makes #installing-into-a-repo-'
                                    'that-already-has-one in guide.md')]))
    finally:
        dl.ROOT = real_root
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(passed for _, passed in cases)
    for name, passed in cases:
        if not passed:
            print(f"  doc_lint did NOT behave as stated: {name}")
    check(f'doc_lint fires ({len(cases)} stated cases: cross-line and '
          f'same-line strikethrough, clean prose stays clean, a '
          f'*_decision.md link is not residue, a real verify-later flag is '
          f'still caught, a glossed acronym stays clean on reuse while an '
          f'unglossed one is still caught, a filename stem and a document '
          f'naming itself are not acronyms, the corpus rule tells a shouted '
          f'English word from a real initialism with no wordlist, and a '
          f'broken relative link is '
          f'caught while a correct one, a code span, a fenced block, a URL, '
          f'an anchor and a templates/ PATH are not -- though a dead '
          f'#fragment under templates/ is, and a backticked command, glob '
          f'or placeholder is not an unlinked reference while a bare '
          f'filename still is)', ok)


def check_split_directories_pass_the_repos_own_checks():
    """The pieces of an index kept as a directory -- MAP.source/ and
    GLOSSARY.source/ from --split, X/ beside X.md from --split-file -- are
    fragments of one document, and three checks read them as documents of
    their own (a downstream repo's push check, 2026-10-12): filename-separator
    counted _head.md's underscore against the rows' hyphens, the light
    check's link scan read a row's links from the row's own folder instead
    of the view's, and doc_lint's render gate asked _head.md for a sortable
    render of its own."""
    import tempfile, types
    import precedent_check as pc
    import doc_lint as dl
    tool = ROOT / 'tools' / 'precedent_migrate_views.py'
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='split-checks-'))
    saved = pc.ROOT, dl.ROOT, dl.RENDER_REGISTRY
    try:
        subprocess.run(['git', 'init', '-q', str(tmp)], capture_output=True, check=True)
        (tmp / 'docs').mkdir()
        (tmp / 'docs' / 'a.md').write_text('# A\n', encoding='utf-8')
        sec = tmp / 'MAP.source' / '0020-layout'
        sec.mkdir(parents=True)
        (tmp / 'MAP.source' / '0010-intro.md').write_text(
            '# Map\n\nSee [a](docs/a.md).\n', encoding='utf-8')
        (sec / '_head.md').write_text('## Layout\n\n| Path | What | Who | When |\n'
                                      '|---|---|---|---|\n', encoding='utf-8')
        (sec / '0010-a-doc.md').write_text('| [a](docs/a.md) | x | y | z |\n',
                                           encoding='utf-8')
        (sec / '0020-b-doc.md').write_text('| b | x | y | z |\n', encoding='utf-8')
        (sec / '_tail.md').write_text('After, see [a](docs/a.md).\n', encoding='utf-8')
        (tmp / 'INDEX.md').write_text(
            '# Index\n\nIntro, see [a](docs/a.md).\n\n| Doc | What | Who | When |\n'
            '|---|---|---|---|\n| [a](docs/a.md) | x | y | z |\n| beta-doc | x | y | z |\n'
            '| gamma-doc | x | y | z |\n\nAfter, [a](docs/a.md).\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(tool), '--repo', str(tmp), '--split-file',
                            'INDEX.md'], capture_output=True, text=True)
        cases.append(('fixture: INDEX.md splits', r.returncode == 0, failure_detail(r.stdout, 300)))
        subprocess.run(['git', 'add', '-A'], cwd=str(tmp), capture_output=True, check=True)
        pc.ROOT = dl.ROOT = tmp
        got = [f.detail for f in pc._filename_separator(types.SimpleNamespace(root=tmp))]
        cases.append(('a split directory passes filename-separator', got == [], got))
        got = [f'{f.file()}: {f.detail}' for f in pc._light_check(types.SimpleNamespace(root=tmp))]
        cases.append(('a link in a --split row, head or tail resolves against the view '
                      '(light check)', not any('MAP.source/' in g for g in got), got))
        cases.append(('a link in a --split-file row, head or tail resolves against the '
                      'view (light check)', not any('INDEX/' in g for g in got), got))
        pieces = sorted(str(p.relative_to(tmp)) for d in ('MAP.source', 'INDEX')
                        for p in (tmp / d).rglob('*.md'))
        broken = [(p, x) for p in pieces for x in dl.check_broken_links(p)]
        cases.append(('...and doc_lint reads the same links the same way', broken == [],
                      broken))
        dl.RENDER_REGISTRY = lambda: []
        got = dl.check_unrendered(pieces)
        cases.append(('no piece of a split directory is asked for a sortable render '
                      'of its own', got == [], got))
        (tmp / 'wide.md').write_text('| a | b | c | d |\n|---|---|---|---|\n| 1 | 2 | 3 | 4 |\n',
                                     encoding='utf-8')
        got = dl.check_unrendered(['wide.md'])
        cases.append(('CONTROL: a document with the same table still is',
                      [g[0] for g in got] == ['wide.md'], got))
    except (OSError, subprocess.CalledProcessError) as e:
        cases.append((f'fixture could not be built ({e})', False, ''))
    finally:
        pc.ROOT, dl.ROOT, dl.RENDER_REGISTRY = saved
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'a split index directory passes the checks its view does '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {str(d)[:300]}' for n, d in bad))


def check_legacy_status_migration():
    """A practice written under the OLD status vocabulary can be classified,
    and cannot be classified by guessing.

    THE GAP THIS CLOSES. `status: retired` used to mean two different things
    -- a redundant copy of a rule still fully in force elsewhere, and a rule
    withdrawn everywhere -- and a legacy record does not say which. The
    records are in the private practice sets; BestPractice's own catalogue
    never had one, which is exactly why nothing here would otherwise
    exercise this. So the fixtures below reproduce both real cases:

      planted-sync-rule   the surviving copy has the SAME slug, in another
                          source -- mechanically determinable.
      header-caps         the surviving rule is `headline-capitalization`
                          at universal -- a RENAMED successor, which nothing
                          mechanical connects to it. Must come back
                          UNDETERMINED rather than guessed.

    The second is the one that matters. A migration willing to guess at a
    renamed successor would re-introduce precisely the resemblance-based
    reasoning the whole status rename removes."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_migrate_status as pms

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-legacy-'))
    cases = []
    try:
        src = (ROOT / 'practices' / 'verify-postcondition.md').read_text(encoding='utf-8')

        def make(root, slug, status='active', story=None, legacy=False):
            d = tmp / root / 'practices'
            d.mkdir(parents=True, exist_ok=True)
            x = re.sub(r'^slug:(\s+)\S+$', rf'slug:\g<1>{slug}', src, count=1, flags=re.M)
            x = re.sub(r'^status:(\s+)active$', rf'status:\g<1>{status}', x, count=1, flags=re.M)
            if legacy:                       # the field did not exist yet
                x = re.sub(r'^in_force_at: null\n', '', x, count=1, flags=re.M)
            if story is not None:
                x = re.sub(r'(?s)## Story\n.*?\n## Install',
                           f'## Story\n{story}\n\n## Install', x, count=1)
            (d / f'{slug}.md').write_text(x, encoding='utf-8')
            return d / f'{slug}.md'

        team_sync = make('team', 'planted-sync-rule', 'retired',
                         'Moved to the individual set.', legacy=True)
        team_caps = make('team', 'header-caps', 'retired',
                         'The universal catalogue carries this now.', legacy=True)
        make('individual', 'planted-sync-rule')
        make('universal', 'headline-capitalization')
        against = [str(tmp / 'individual'), str(tmp / 'universal')]

        recs = pms.legacy_records(tmp / 'team' / 'practices')
        cases.append(('a legacy record (non-active, no in_force_at) is found',
                      {fm.get('slug') for _f, fm, _s in recs}
                      == {'planted-sync-rule', 'header-caps'}))

        live = pms.active_slugs(against)
        cases.append(('only ACTIVE slugs count as a surviving copy',
                      'planted-sync-rule' in live and 'headline-capitalization' in live))

        # report-only must never write
        before = team_sync.read_text(encoding='utf-8')
        rc = pms.report(str(tmp / 'team'), against, {}, False)
        cases.append(('report-only leaves every file untouched',
                      team_sync.read_text(encoding='utf-8') == before))
        cases.append(('report-only exits non-zero while legacy records remain',
                      rc == 1))

        # the renamed successor must NOT be guessed
        rc = pms.report(str(tmp / 'team'), against, {}, True)
        caps_after = team_caps.read_text(encoding='utf-8')
        cases.append(('a RENAMED successor is left UNDETERMINED, not guessed -- '
                      'guessing here is the resemblance reasoning the rename removes',
                      'status:      retired' in caps_after
                      and 'in_force_at' not in caps_after))
        sync_after = team_sync.read_text(encoding='utf-8')
        cases.append(('...while the same-slug case IS migrated, to deduplicated',
                      'status:      deduplicated' in sync_after
                      and 'in_force_at: planted-sync-rule' in sync_after))

        # an explicitly named target that is not in force is refused
        pms.report(str(tmp / 'team'), against, {'header-caps': 'no-such-slug'}, True)
        cases.append(('an in_force_at: target that is not active anywhere is refused',
                      'no-such-slug' not in team_caps.read_text(encoding='utf-8')))

        # a real retirement needs a Story
        make('team2', 'storyless', 'retired', '', legacy=True)
        pms.report(str(tmp / 'team2'), against, {'storyless': 'none'}, True)
        cases.append(('--set ...=none is refused without a ## Story saying why',
                      'status:      retired' in
                      (tmp / 'team2' / 'practices' / 'storyless.md').read_text(encoding='utf-8')
                      and 'in_force_at' not in
                      (tmp / 'team2' / 'practices' / 'storyless.md').read_text(encoding='utf-8')))

        # the named target lands, and the result satisfies the contract
        pms.report(str(tmp / 'team'), against,
                   {'header-caps': 'headline-capitalization'}, True)
        fm, sections = sp._read_practice_file(team_caps)
        import build_views as _bv
        cases.append(('an explicitly named successor migrates cleanly',
                      _bv.practice_status(fm) == 'deduplicated'
                      and _bv._json_str(fm.get('in_force_at', '')) == 'headline-capitalization'))
        cases.append(('...and the migrated file satisfies the status contract',
                      _bv.status_contract_violation(
                          fm, sections, {'headline-capitalization'}.__contains__) is None))
        cases.append(('the migration is idempotent -- a second run finds nothing',
                      pms.report(str(tmp / 'team'), against, {}, False) == 0))

        # the rewriter must not touch a body line that merely starts "status:"
        body_trap = make('team3', 'body-trap', 'retired',
                         'status: active is a line of prose here.', legacy=True)
        pms.report(str(tmp / 'team3'), against, {'body-trap': 'engine'}, True)
        after = body_trap.read_text(encoding='utf-8')
        cases.append(('a body line beginning "status:" is not rewritten -- only '
                      'the frontmatter block is touched',
                      'status: active is a' in after
                      and 'status:      deduplicated' in after))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'a legacy status record can be migrated, and a renamed successor '
          f'is never guessed ({len(cases)} stated cases)', not bad, '; '.join(bad))


def check_update_hands_the_engine_refresh_the_followed_tip():
    """Update Vendors runs the engine refresh with the CONSUMER's own engine
    copy, and an older copy resolves the branch it was written to follow: a
    beta-era consumer's first update vendored from precedent-beta-v01 and
    reported `refreshed from precedent-beta-v01 @ ...` under `source: main`
    (very deep check, 2026-10-05, pass 1). The update now always hands the
    refresh the tip it read, and reports the leg that landed there. An
    engine recorded ahead of the tip is still left to the refresh's own
    no-rollback guard."""
    import contextlib
    import io
    import tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-update-tip-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)
    tip = git(ROOT, 'rev-parse', 'HEAD').stdout.strip()
    older = git(ROOT, 'rev-parse', 'HEAD~1').stdout.strip()
    saved_run = pu.run
    cases = []

    def planted(name, recorded, beta):
        # An engine copy that behaves like a beta-era one: given no
        # --from-ref it vendors `beta`, the integration branch's commit.
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps({
            'source_commit': recorded, 'kind': 'consumer', 'files': []}),
            encoding='utf-8')
        argv_file = tmp / f'{name}-argv.json'
        (repo / 'tools' / 'precedent_vendor_engine.py').write_text(
            'import json, pathlib, sys\n'
            f'open({str(argv_file)!r}, "w").write(json.dumps(sys.argv[1:]))\n'
            'a = sys.argv[1:]\n'
            'ref = a[a.index("--from-ref") + 1] if "--from-ref" in a else None\n'
            f'got = ref or {beta!r}\n'
            'm = pathlib.Path(__file__).with_name("ENGINE_MANIFEST.json")\n'
            'd = json.loads(m.read_text()); d["source_commit"] = got\n'
            'm.write_text(json.dumps(d))\n'
            'print("precedent_vendor_engine refresh OK (consumer): 3 file(s) "\n'
            '      "refreshed from " + (ref or "precedent-beta-v01") + " @ " + got[:12]\n'
            f'      + " (was {recorded[:12]})")\n',
            encoding='utf-8')
        git(tmp, 'init', '-q', '-b', 'main', str(repo))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'installed\n\nSession: none available (fixture)')
        return repo, argv_file

    def run_update(repo, followed_tip):
        def fetchless(argv, cwd):
            if argv[:1] == ['git'] and 'fetch' in argv:
                return 0, ''
            if argv[:1] == ['git'] and 'rev-parse' in argv \
                    and argv[-1] == f'origin/{pve.SOURCE_BRANCH}':
                return 0, followed_tip + '\n'
            return saved_run(argv, cwd)
        pu.run = fetchless
        # GitHub stood in: every commit's test passed, so the tip is taken.
        saved_state = getattr(pu, 'main_test_state', None)
        pu.main_test_state = lambda sha, tests: ('passed', 'stand-in')
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                pu.update(repo, skip_check=True)
        finally:
            pu.run = saved_run
            if saved_state is not None:
                pu.main_test_state = saved_state
        return out.getvalue()

    try:
        repo, argv_file = planted('beta-era', older, '0' * 40)
        text = run_update(repo, tip)
        argv = json.loads(argv_file.read_text()) if argv_file.is_file() else []
        cases.append(('a repo following main hands its own engine refresh the '
                      'tip of main', argv[-2:] == ['--from-ref', tip], str(argv)))
        landed = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                            .read_text(encoding='utf-8')).get('source_commit')
        cases.append(('...so the engine lands on main, not the integration branch',
                      landed == tip, str(landed)))
        cases.append(('...and the report names main, never the branch the old '
                      'copy would have read',
                      f'refreshed from {pve.SOURCE_BRANCH} @ {tip[:12]}' in text
                      and 'precedent-beta-v01' not in text, failure_detail(text, 1500)))
        two_legs = ('precedent_vendor_engine refresh OK (consumer): 3 file(s) '
                    f'refreshed from precedent-beta-v01 @ {"b" * 12} (was 1)\n'
                    'precedent_vendor_engine refresh OK (consumer): 3 file(s) '
                    f'refreshed from {tip} @ {tip[:12]} (was 1)\n')
        try:
            shown = pu.engine_summary('\n'.join(reversed(two_legs.splitlines())),
                                      None, follow='main', tip=tip)
        except TypeError as e:
            shown = f'engine_summary takes no tip: {e}'
        cases.append(('the report shows the leg that landed on the tip, whatever '
                      'order the passes print in',
                      shown.startswith(f'3 file(s) refreshed from main @ {tip[:12]}'),
                      shown))
        ahead, argv_file = planted('ahead', tip, '0' * 40)
        run_update(ahead, older)
        argv = json.loads(argv_file.read_text()) if argv_file.is_file() else []
        cases.append(('an engine recorded ahead of the tip is not told to roll '
                      'back: no --from-ref', bool(argv) and '--from-ref' not in argv,
                      str(argv)))
    finally:
        pu.run = saved_run
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    check(f'Update Vendors refreshes the engine from the tip it read '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {d}' for n, d in bad))


def check_refresh_never_says_nothing_to_do_after_removing_a_file():
    """A refresh whose recorded commit already matches still removes an
    engine file the kind no longer includes, and then said "engine already
    current ... nothing to do" right under the line reporting the deletion
    (very deep check, 2026-10-05, pass 1). The line now says what this pass
    did. The fixture is an installed consumer whose manifest records one
    more engine file than the kind includes, refreshed at its own commit."""
    import hashlib as _hl
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    top = pathlib.Path(_tf.mkdtemp(prefix='vh-orphan-msg-'))
    fx = top / 'consumer'
    fx.mkdir()
    (top / 'home').mkdir()
    # HOME and the user config are the fixture's own (practice:
    # fixture-owns-its-state), which also lets the seed cache key them.
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               PRECEDENT_ALLOW_ANY_AUTHOR='1', HOME=str(top / 'home'),
               PRECEDENT_USER_CONFIG=str(top / 'no-user-config.json'))

    def sh(*args):
        r = subprocess.run(list(args), cwd=str(fx), env=env,
                           capture_output=True, text=True)
        return r.stdout + r.stderr

    def commit(msg):
        sh('git', 'add', '-A')
        sh('git', 'commit', '-qm', f'{msg}\n\nSession: none available (fixture)')
    cases = []
    try:
        sh('git', 'init', '-q', '-b', 'main')
        # A seeded consumer engine, from the harness seed cache: the refresh
        # reads only the engine and its manifest, never what else an install
        # writes.
        (fx / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'visibility': 'private', 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': str(ROOT)}]}) + '\n', encoding='utf-8')
        (fx / 'AGENTS.md').write_text(
            f'# fixture\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')
        _seed_fixture_engine(fx, 'consumer', env, cwd=fx)
        commit('installed')
        recorded = json.loads((fx / 'tools' / _pve.MANIFEST_NAME)
                              .read_text(encoding='utf-8'))['source_commit']
        refresh = (sys.executable, 'tools/precedent_vendor_engine.py', 'refresh',
                   str(ROOT), '--from-ref', recorded)
        sh(*refresh)                      # converge whatever the install left
        commit('converged')
        m = fx / 'tools' / _pve.MANIFEST_NAME
        d = json.loads(m.read_text(encoding='utf-8'))
        old = fx / 'tools' / 'retired_tool.py'
        old.write_text('"""A tool upstream no longer ships."""\n', encoding='utf-8')
        d['files'].append('retired_tool.py')
        d.setdefault('sha256', {})['retired_tool.py'] = _hl.sha256(
            old.read_bytes()).hexdigest()
        m.write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8')
        commit('a file the kind no longer includes')
        out = sh(*refresh)
        cases.append(('the refresh removes the file', not old.exists()
                      and 'removed 1 vendored engine file' in out, failure_detail(out, 800)))
        current = [l for l in out.splitlines() if 'already current with' in l]
        cases.append(('...on the already-current path', bool(current), failure_detail(out, 800)))
        cases.append(('...and its closing line says so, never "nothing to do"',
                      bool(current) and 'nothing to do' not in current[-1]
                      and 'removed' in current[-1], str(current)))
    finally:
        _sh.rmtree(top, ignore_errors=True)
    bad = [(n, x) for n, ok, x in cases if not ok]
    check(f'a refresh that removed an engine file never says nothing was done '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {x}' for n, x in bad))


def check_fresh_install_links_its_file_names():
    """A fresh install failed its own link convention: INSTALL.md section 0
    step 8's lint of the instantiated files listed 18 file names written
    without a link -- in the loader AGENTS.md, MAP and local-practice
    templates -- while the installer said the light check passed, because
    the lint reports them as warnings and exits 0 (very deep check,
    2026-10-05, pass 1). The templates now link them, and the installer
    counts any such name outside a generated block as a failed light
    check. The generated block is the generator's text, not a template's."""
    import inspect
    import shutil as _sh
    import tempfile as _tf
    sys.path.insert(0, str(ROOT / 'tools'))
    import generated_blocks as _gb
    import precedent_install as _pi
    fx = pathlib.Path(_tf.mkdtemp(prefix='vh-install-links-'))
    cases = []
    try:
        proj = fx / 'proj'
        # The shared fresh install (_fresh_install_fixture), copied, not rerun.
        _rc, install_out, _err = _fresh_install_fixture(proj)
        step8 = ['AGENTS.md', 'MAP.md', 'TODO.md', 'GLOSSARY.md',
                 'GETTING_STARTED.md', 'local/practices/project-voice.md',
                 'local/practices/project-visual-identity.md', 'README.md',
                 'MAP.source.md', 'practices/project-voice.md',
                 'practices/project-visual-identity.md']
        lint = subprocess.run([sys.executable, 'tools/doc_lint.py', *step8],
                              cwd=str(proj), capture_output=True, text=True)
        outside = []
        for line in lint.stdout.splitlines():
            m = re.match(r'^\s+(\S+?):(\d+): `[^`]+` is not a link$', line)
            if not m:
                continue
            mask = _gb.mask((proj / m.group(1)).read_text(encoding='utf-8'))
            n = int(m.group(2))
            if not (n - 1 < len(mask) and mask[n - 1]):
                outside.append(line.strip())
        cases.append(('section 0 step 8\'s lint finds no unlinked file name the '
                      'templates wrote', lint.returncode == 0 and not outside,
                      '; '.join(outside) or failure_detail(lint.stdout, 600)))
        cases.append(('...and the installer\'s own light check passes',
                      'the light check on the written files: OK' in install_out,
                      failure_detail(install_out, 600)))
        # The installer's light check counts a template's unlinked name and
        # leaves the generated block's alone.
        probe = fx / 'probe'
        probe.mkdir()
        (probe / 'A.md').write_text(
            'See `B.md` here.\n'
            '<!-- BEGIN GENERATED: precedent-loader -->\n'
            'Generated `C.md` text.\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        fake = ('UNLINKED FILE REFERENCES — 2 (warning; link the ones you touched):\n'
                '  A.md:1: `B.md` is not a link\n'
                '  A.md:3: `C.md` is not a link\n')
        counter = getattr(_pi, '_unlinked_outside_generated', None)
        got = counter(probe, fake) if counter else None
        cases.append(('the installer counts an unlinked name a template wrote, '
                      'and not one in the generated block',
                      got == ['A.md:1: `B.md` is not a link'], str(got)))
        cases.append(('...and a counted one fails its light check',
                      counter is not None and 'not unlinked' in
                      inspect.getsource(_pi.install), ''))
    finally:
        _sh.rmtree(fx, ignore_errors=True)
    bad = [(n, x) for n, ok, x in cases if not ok]
    check(f'a fresh install links the file names its templates write '
          f'({len(cases)} stated cases)', not bad,
          '; '.join(f'{n}: {x}' for n, x in bad))


def check_update_vendors_takes_only_a_main_that_passed():
    """Update Vendors takes the newest main commit whose GitHub test passed,
    and says so in one line when that is not the newest: which commit, how
    many commits behind, and why. GitHub not answering takes the tip with a
    warning; --take-anyway takes a named commit on the person's word and
    records it for the commit message.

    2026-10-09, the main landing plan, piece A (Morgan, "Act on the
    ... plan"): a test that no longer fit sat on main for about an hour,
    and any repository updated in that hour would have taken it. Here the
    update runs in-process against a planted consumer whose engine copy is a
    stand-in recording the commit it was handed (as
    check_update_hands_the_engine_refresh_the_followed_tip does), main's
    tip is stubbed to this clone's HEAD, and GitHub is stood in through
    precedent_update.main_test_state, answering per commit of HEAD's
    first-parent line.

    Negative control, measured 2026-10-09 against origin/main at d14a6fd6:
    the red, running and unreachable cases take the tip with no line, and
    the override is an unknown argument. The green case takes the same
    commit there; it fails only on GitHub never having been asked."""
    import contextlib
    import io
    import tempfile
    pu, pve, _pr = _update_tools()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-update-green-'))
    env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
               GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
               GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1',
               PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def git(cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=env,
                              capture_output=True, text=True)
    line = git(ROOT, 'rev-list', '--first-parent', '--max-count=3', 'HEAD').stdout.split()
    if len(line) < 3:
        shutil.rmtree(tmp, ignore_errors=True)
        return (True, 'not applicable: fewer than three first-parent commits here', '')
    c0, c1, _c2 = line
    saved_run = pu.run
    saved_state = getattr(pu, 'main_test_state', None)
    saved_marks = getattr(pu, 'passed_trees', None)
    cases = []

    def planted(name):
        repo = tmp / name
        (repo / 'tools').mkdir(parents=True)
        (repo / 'tools' / pve.MANIFEST_NAME).write_text(json.dumps({
            'source_commit': _c2, 'kind': 'consumer', 'files': []}), encoding='utf-8')
        argv_file = tmp / f'{name}-argv.json'
        (repo / 'tools' / 'precedent_vendor_engine.py').write_text(
            'import json, pathlib, sys\n'
            f'open({str(argv_file)!r}, "w").write(json.dumps(sys.argv[1:]))\n'
            'a = sys.argv[1:]\n'
            'ref = a[a.index("--from-ref") + 1] if "--from-ref" in a else "none"\n'
            'm = pathlib.Path(__file__).with_name("ENGINE_MANIFEST.json")\n'
            'd = json.loads(m.read_text()); d["source_commit"] = ref\n'
            'm.write_text(json.dumps(d))\n'
            'print("precedent_vendor_engine refresh OK (consumer): 1 file(s) "\n'
            '      "refreshed from " + ref + " @ " + ref[:12])\n', encoding='utf-8')
        git(tmp, 'init', '-q', '-b', 'main', str(repo))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'installed\n\nSession: none available (fixture)')
        return repo, argv_file

    def tree(sha):
        return git(ROOT, 'rev-parse', f'{sha}^{{tree}}').stdout.strip()

    def run_update(name, states, take=None, marks=()):
        repo, argv_file = planted(name)

        def fetchless(argv, cwd):
            if argv[:1] == ['git'] and 'fetch' in argv:
                return 0, ''
            if argv[:1] == ['git'] and 'rev-parse' in argv \
                    and argv[-1] == f'origin/{pve.SOURCE_BRANCH}':
                return 0, c0 + '\n'
            return saved_run(argv, cwd)
        asked = []

        def state(sha, tests):
            asked.append(sha)
            return states.get(sha, ('failed', 'stand-in: not planted'))
        pu.run = fetchless
        pu.main_test_state = state
        # The passed markers are stood in too: the real ones are on origin,
        # and a run here must not read the network or main's real history.
        pu.passed_trees = lambda: set(marks)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                if take:
                    pu.update(repo, skip_check=True, take=take)
                else:
                    pu.update(repo, skip_check=True)
        except TypeError as e:
            out.write(f'\nupdate() takes no override: {e}')
        finally:
            pu.run = saved_run
            if saved_state is not None:
                pu.main_test_state = saved_state
            if saved_marks is not None:
                pu.passed_trees = saved_marks
        argv = json.loads(argv_file.read_text()) if argv_file.is_file() else []
        handed = argv[argv.index('--from-ref') + 1] if '--from-ref' in argv else None
        held = getattr(pu, 'held_pin', lambda _r: None)(repo) or {}
        return out.getvalue(), handed, held, asked

    def steps(text):
        return [l for l in text.splitlines() if l.startswith('precedent_update: GitHub test:')]

    try:
        text, handed, _held, asked = run_update('green', {c0: ('passed', 'ok')})
        cases.append(('(a) the newest main passed: it is taken, one question asked of '
                      'GitHub, and no line about it',
                      handed == c0 and asked == [c0] and not steps(text),
                      (handed, asked, steps(text))))

        text, handed, _held, _a = run_update('red', {c0: ('failed', 'url'),
                                                     c1: ('passed', 'ok')})
        want = (f"precedent_update: GitHub test: took main @ {c1[:12]}, 1 commit behind "
                f"the newest main, {c0[:12]}, because GitHub's test failed on "
                f"{c0[:12]}. This repo gets the newer ones once their test passes")
        cases.append(('(b) the newest main is red: the one before it is taken, said in '
                      'one line with the count and the reason',
                      handed == c1 and steps(text) == [want], (handed, steps(text))))

        text, handed, _held, _a = run_update('running', {c0: ('running', 'busy'),
                                                         c1: ('passed', 'ok')})
        cases.append(('(c) the newest main is still being tested: the one before it, '
                      '"still running"',
                      handed == c1 and len(steps(text)) == 1
                      and f"is still running on {c0[:12]}" in steps(text)[0]
                      and '1 commit behind' in steps(text)[0], (handed, steps(text))))

        text, handed, _held, asked = run_update('unreachable', {
            c0: ('unknown', 'curl exited 6'), c1: ('passed', 'ok')})
        cases.append(('(d) GitHub cannot be reached: the newest main, with a warning that '
                      'names why, never silently',
                      handed == c0 and asked == [c0] and len(steps(text)) == 1
                      and 'WARNING: could not ask GitHub' in steps(text)[0]
                      and 'curl exited 6' in steps(text)[0], (handed, steps(text))))

        text, handed, held, _a = run_update('override', {c1: ('failed', 'url')},
                                            take=c1[:10])
        cases.append(('(e) --take-anyway takes the named red commit, says it was the '
                      'person\'s word, and keeps that for the commit message',
                      handed == c1 and len(steps(text)) == 1
                      and "on the person's word (--take-anyway), although its GitHub "
                          "test had not passed" in steps(text)[0]
                      and (f"Took BestPractice main @ {c1[:12]} on the person's word "
                           f"(--take-anyway), although its GitHub test had not passed."
                           in (held.get('note') or '') + text.split('COMMIT MESSAGE: ', 1)[-1]
                           if 'COMMIT MESSAGE: ' in text or held.get('note') else False),
                      (handed, steps(text), held, failure_detail(text, 700))))

        # THE GIT MARKER (2026-10-10, Morgan: "yes, build it and take it
        # to main"): deep-check.yml pushes refs/precedent/passed/<tree> when
        # main's test passes, so a session that cannot ask GitHub's API
        # still takes only a main that passed.
        text, handed, _held, asked = run_update('marked', {}, marks=[tree(c0)])
        cases.append(('(f) the newest main carries a passed marker: it is taken, '
                      'GitHub is never asked, and no line about it',
                      handed == c0 and asked == [] and not steps(text),
                      (handed, asked, steps(text))))
        text, handed, _held, _a = run_update('marked-older', {
            c0: ('unknown', 'not enabled for this session')}, marks=[tree(c1)])
        cases.append(('(g) GitHub cannot be asked and only the commit before carries '
                      'a marker: that one is taken, said in one line, no warning',
                      handed == c1 and len(steps(text)) == 1
                      and 'left no passed marker, and GitHub could not be asked, on '
                          f'{c0[:12]}' in steps(text)[0]
                      and 'WARNING' not in steps(text)[0], (handed, steps(text))))
        cases.append(('(g2) ...and that line says it took the newest commit with a '
                      'recorded pass, with no advice to attach the source for push '
                      '(2026-10-17, a consumer: the advice pushed a read-only '
                      'session toward a push grant only to read a public check)',
                      len(steps(text)) == 1
                      and 'the newest with a recorded pass' in steps(text)[0]
                      and 'add_repo' not in steps(text)[0],
                      steps(text)))
        text, handed, _held, _a = run_update('marked-red', {
            c0: ('failed', 'url')}, marks=[tree(c1)])
        cases.append(('(h) a red tip with GitHub answering: the marked commit '
                      'before it, as for any older green one',
                      handed == c1 and len(steps(text)) == 1
                      and f"failed on {c0[:12]}" in steps(text)[0], (handed, steps(text))))
        text, handed, _held, _a = run_update('marks-out-of-reach', {
            sha: ('unknown', 'curl exited 6') for sha in line}, marks=['0' * 40])
        cases.append(('(i) markers exist but none in reach, and GitHub cannot be asked: '
                      'the newest main with a warning, as before markers',
                      handed == c0 and len(steps(text)) == 1
                      and 'WARNING' in steps(text)[0]
                      and 'carries a passed marker' in steps(text)[0], (handed, steps(text))))
        cases.append(('(i2) a network failure, not missing access: no attach advice',
                      'add_repo' not in steps(text)[0] if steps(text) else False,
                      steps(text)))

        text, handed, _held, _a = run_update('all-red', {})
        cases.append(('...and with nothing green in reach, nothing is taken and the '
                      'override is named',
                      handed is None and 'Nothing was taken' in text
                      and '--take-anyway <commit>' in text, (handed, failure_detail(text, 600))))
    finally:
        pu.run = saved_run
        if saved_state is not None:
            pu.main_test_state = saved_state
        if saved_marks is not None:
            pu.passed_trees = saved_marks
        shutil.rmtree(tmp, ignore_errors=True)
    # GitHub's refusal is a refusal, never "no runs" (2026-10-09: a session
    # with no GitHub access to BestPractice read "not enabled for this
    # session" as main's test never having run).
    import precedent_branches as _pb

    class _Refuses:
        def call(self, path, cache=True):
            return ({'message': 'GitHub access to this repository is not '
                     'enabled for this session. Use add_repo to request '
                     'access.'}, None)
    runs, err = _pb._runs_on(_Refuses(), 'o/r', 'abc')
    cases.append(('a refusal is read as GitHub not answering, with its own '
                  'words', runs is None and 'add_repo' in (err or ''), err))
    _pb._CURRENT_SLUG.pop('o/r', None)
    name, err = _pb._current_slug(_Refuses(), 'o/r')
    _pb._CURRENT_SLUG.pop('o/r', None)
    cases.append(('the name check says the same',
                  name is None and 'add_repo' in (err or ''), err))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_main_test_failure_opens_an_issue():
    """BestPractice's own deep-check.yml ends its one job with a step that
    files an issue labelled main-test-failed, or comments on the open one,
    when the test failed -- on main itself or on a pull request into main,
    never otherwise -- with issues: write the only permission added, and no
    new job. The next session here lists that issue first
    (check_session_start_lists_a_red_main_first).

    2026-10-09, the main landing plan, piece B, layer 2. The step's `if:`
    is evaluated here for each kind of run, not matched as text.

    Negative control, measured 2026-10-09 against origin/main at d14a6fd6:
    no such step, and the job carries no permissions of its own."""
    wf = ROOT / '.github' / 'workflows' / 'deep-check.yml'
    text = wf.read_text(encoding='utf-8') if wf.is_file() else ''
    cases = []
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import open_failures as of
    finally:
        sys.path.pop(0)
    label = getattr(of, 'MAIN_TEST_LABEL', 'main-test-failed')
    block = _workflow_step_block(text, "Open an issue when main's test fails")
    body = '\n'.join(block)
    cases.append(('the step exists', bool(block), wf.name))
    jobs = re.findall(r'^  ([\w-]+):\s*$', text.split('\njobs:', 1)[-1], re.M)
    cases.append(('no job was added for it: still already-tested and deep-check',
                  jobs == ['already-tested', 'deep-check'], jobs))
    deep = text.split('\n  deep-check:', 1)[-1]
    steps = re.findall(r'^      - name:\s*(.+)$', deep, re.M)
    cases.append(('it is the deep-check job\'s last step, after the harness',
                  bool(steps) and steps[-1] == "Open an issue when main's test fails"
                  and 'verification harness' in ' '.join(steps[:-1]), steps))
    m = re.search(r'^\s+if:\s*>-?\s*\n((?:\s{10,}.*\n)+)', body + '\n', re.M) \
        or re.search(r'^\s+if:\s*(.+)$', body, re.M)
    expr = ' '.join(m.group(1).split()) if m else ''
    runs = [
        ('push', 'refs/heads/main', '', True, True),
        ('workflow_dispatch', 'refs/heads/main', '', True, True),
        ('pull_request', 'refs/pull/9/merge', 'main', True, True),
        ('push', 'refs/heads/main', '', False, False),
        ('pull_request', 'refs/pull/9/merge', 'main', False, False),
        ('push', 'refs/heads/feature', '', True, False),
        ('workflow_dispatch', 'refs/heads/feature', '', True, False),
        ('pull_request', 'refs/pull/9/merge', 'release', True, False),
    ]
    for event, ref, base, failed, want in runs:
        try:
            got = _actions_if(expr, event, ref, base, failed) if expr else None
        except Exception as e:                                # noqa: BLE001
            got = f'unreadable: {e}'
        cases.append((f'{event} on {ref}{" into " + base if base else ""}, '
                      f'{"failed" if failed else "passed"}: '
                      f'{"files an issue" if want else "does nothing"}',
                      got is want, (expr, got)))
    perms = re.search(r'^    permissions:\s*\n((?:      .*\n)+)', deep, re.M)
    got = sorted(l.strip() for l in (perms.group(1) if perms else '').splitlines()
                 if l.strip() and not l.strip().startswith('#'))
    top = re.search(r'^permissions:\s*\n((?:  .*\n|\s*#.*\n)+)', text, re.M)
    top_got = sorted(l.strip() for l in (top.group(1) if top else '').splitlines()
                     if l.strip() and not l.strip().startswith('#'))
    # contents: write since 2026-10-10, for the passed marker
    # (check_main_test_pass_leaves_a_git_marker).
    want = sorted([l for l in top_got if l != 'contents: read']
                  + ['contents: write', 'issues: write'])
    cases.append(('the job adds issues: write and contents: write to the '
                  'workflow\'s read permissions, and nothing else',
                  got == want and 'issues: write' not in top_got, (got, top_got)))
    cases.append(('it files the issue under the label session start reads, or '
                  'comments on the open one, and links the run',
                  f'label={label}' in body and 'gh issue create' in body
                  and 'gh issue comment' in body and '--state open' in body
                  and 'RUN_URL' in body and 'continue-on-error: true' in body,
                  label))
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_main_test_pass_leaves_a_git_marker():
    """When main's test passes -- on main itself or on a pull request into
    main, never otherwise -- deep-check.yml pushes refs/precedent/passed/
    <tree> at the commit it tested, before the failure step and with no
    new job, and precedent_branches.passed_markers reads those trees back
    from origin with plain git.

    2026-10-10 (Morgan: "yes, build it and take it to main"): a session in
    a consuming repository could not ask GitHub's API about BestPractice, so
    its Update Vendors took main without knowing whether the test passed.

    Negative control, measured 2026-10-10 against origin/staging at
    06cbfce8: no such step, and no passed_markers."""
    import tempfile
    wf = ROOT / '.github' / 'workflows' / 'deep-check.yml'
    text = wf.read_text(encoding='utf-8') if wf.is_file() else ''
    cases = []
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_branches as pb
    finally:
        sys.path.pop(0)
    prefix = getattr(pb, 'PASSED_PREFIX', None)
    block = _workflow_step_block(text, 'Mark these files as passed')
    body = '\n'.join(block)
    cases.append(('the step exists', bool(block), wf.name))
    deep = text.split('\n  deep-check:', 1)[-1]
    steps = re.findall(r'^      - name:\s*(.+)$', deep, re.M)
    cases.append(('it comes after the harness and before the failure step, in the '
                  'same job', 'Mark these files as passed' in steps
                  and steps.index('Mark these files as passed')
                  == steps.index("Open an issue when main's test fails") - 1
                  and 'verification harness' in ' '.join(
                      steps[:steps.index('Mark these files as passed')]), steps))
    m = re.search(r'^\s+if:\s*>-?\s*\n((?:\s{10,}.*\n)+)', body + '\n', re.M)
    expr = ' '.join(m.group(1).split()) if m else ''
    runs = [
        ('push', 'refs/heads/main', '', False, True),
        ('workflow_dispatch', 'refs/heads/main', '', False, True),
        ('pull_request', 'refs/pull/9/merge', 'main', False, True),
        ('push', 'refs/heads/main', '', True, False),
        ('pull_request', 'refs/pull/9/merge', 'main', True, False),
        ('push', 'refs/heads/feature', '', False, False),
        ('pull_request', 'refs/pull/9/merge', 'release', False, False),
    ]
    for event, ref, base, failed, want in runs:
        try:
            got = _actions_if(expr, event, ref, base, failed) if expr else None
        except Exception as e:                                # noqa: BLE001
            got = f'unreadable: {e}'
        cases.append((f'{event} on {ref}{" into " + base if base else ""}, '
                      f'{"failed" if failed else "passed"}: '
                      f'{"marks" if want else "does nothing"}', got is want, (expr, got)))
    cases.append(('it pushes the tested tree under the prefix the engine reads, and a '
                  'failed push only warns',
                  prefix == 'refs/precedent/passed/' and "rev-parse 'HEAD^{tree}'" in body
                  and f'HEAD:{prefix}$tree' in body and 'continue-on-error: true' in body,
                  (prefix, body)))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vh-passed-marker-'))
    try:
        env = dict(os.environ, GIT_AUTHOR_NAME='F', GIT_AUTHOR_EMAIL='f@example.com',
                   GIT_COMMITTER_NAME='F', GIT_COMMITTER_EMAIL='f@example.com',
                   GIT_CONFIG_GLOBAL=empty_gitconfig(), GIT_CONFIG_NOSYSTEM='1')

        def git(*args):
            return subprocess.run(['git', *args], env=env, capture_output=True, text=True)
        git('init', '-q', '--bare', str(tmp / 'origin.git'))
        git('init', '-q', '-b', 'main', str(tmp / 'clone'))
        clone = tmp / 'clone'
        (clone / 'f').write_text('x', encoding='utf-8')
        git('-C', str(clone), 'add', 'f')
        git('-C', str(clone), 'commit', '-qm', 'one')
        git('-C', str(clone), 'remote', 'add', 'origin', str(tmp / 'origin.git'))
        tree = git('-C', str(clone), 'rev-parse', 'HEAD^{tree}').stdout.strip()
        reader = getattr(pb, 'passed_markers', None)
        before = reader(clone) if reader else 'no passed_markers'
        git('-C', str(clone), 'push', '-q', 'origin', f'HEAD:{prefix}{tree}',
            'HEAD:refs/heads/main')
        after = reader(clone) if reader else 'no passed_markers'
        cases.append(('passed_markers reads the trees back from origin, and nothing '
                      'else', before == set() and after == {tree}, (before, after)))
        git('-C', str(clone), 'remote', 'set-url', 'origin', str(tmp / 'nowhere.git'))
        gone = reader(clone) if reader else 'no passed_markers'
        cases.append(('an origin that cannot be read is None, not "nothing passed"',
                      gone is None, gone))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(n, d) for n, ok, d in cases if not ok]
    return (not bad, f'{len(cases)} stated cases', '; '.join(f'{n}: {d}' for n, d in bad))


def check_acronym_scan_skips_wrapped_code_spans():
    """doc_lint's acronym scan -- the one detector the acronyms-glossary gate
    shares -- skips a code span that wraps onto the next line, as it skips
    one on a single line (2026-09-28: `--changed-since HEAD --staged`,
    wrapped in vendor-update-runbook, failed a consuming repo's Update
    Vendors on HEAD). Both directions: prose around the span, a fenced
    block, and a paragraph break still end or bound it."""
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_lint as dl
    finally:
        sys.path.pop(0)
    name = ('the acronym scan skips code spans that wrap across lines, and '
            'a shouted phrase')
    toks = lambda t: [tok for _i, tok in dl.scan_unglossed(t, set(), 'x.md')
                      if tok in ('QZXA', 'QZXB', 'QZXC', 'QZXD')]
    cases = [
        ('a span wrapping onto the next line hides its second half',
         toks('Run `tool --flag\nQZXA --staged` now.\n') == []),
        ('prose after the wrapped span is still scanned',
         toks('Run `tool --flag\nx --staged` then QZXB.\n') == ['QZXB']),
        ('a paragraph break ends a span, so the next paragraph is scanned',
         toks('An open ` tick.\n\nQZXC and a close ` tick.\n') == ['QZXC']),
        ('a fenced block is not joined to prose around it',
         toks('Open `\n```\ncode\n```\nQZXD` here.\n') == ['QZXD']),
        ('a shouted phrase quoted inline is not an acronym (reach-or-ask, '
         '2026-10-17: "IT IS A HUGE TOKEN ORDEAL")',
         toks('He said "QZXA IS A HUGE TOKEN QZXB" twice.\n') == []),
        ('two capitalized words in a row are still scanned',
         toks('Use QZXC QZXD here.\n') == ['QZXC', 'QZXD']),
        ('inside a quotation, two capitalized words in a row are a shout '
         '(promote-only, 2026-10-19: "just PURE CONTENT")',
         toks('Me: *"since it is just QZXA QZXB, skip it"*.\n') == []),
        ('one capitalized word alone inside a quotation is still scanned',
         toks('He said "use QZXC here" once.\n') == ['QZXC']),
        ('a comma list of acronyms is still scanned',
         toks('Use QZXA, QZXB and QZXC.\n') == ['QZXA', 'QZXB', 'QZXC']),
        ('line numbers still point at the right line',
         [i for i, tok in dl.scan_unglossed('a `b\nc` d\nQZXA\n', set(), 'x.md')
          if tok == 'QZXA'] == [3]),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_lint_flags_a_table_with_no_render():
    """doc_lint check 7 (practice `tabular-shared-renderer`): a document
    whose widest table has RENDER_MIN_COLUMNS+ columns and is not in the
    host's render registry is reported, so a new one can fail the gate
    (origin: a dependent repo's product specification with eight
    multi-column tables landed as markdown only). Both directions: a
    registered document, a two-column table, a fenced table, a record
    document and the opt-out marker are all left alone, and with no
    registry configured the check stands aside."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_lint as dl
    finally:
        sys.path.pop(0)
    tmp = pathlib.Path(tempfile.mkdtemp())
    wide = '# T\n\n| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |\n'
    docs = {
        'wide.md': wide,
        'registered.md': wide,
        'narrow.md': '| a | b |\n|---|---|\n| 1 | 2 |\n',
        'fenced.md': '```\n| a | b | c |\n|---|---|---|\n```\n',
        'optout.md': wide + '\n<!--no-render-->\n',
        'thing_record.md': wide,
    }
    for n, t in docs.items():
        (tmp / n).write_text(t)
    saved = (dl.ROOT, dl.RENDER_REGISTRY)
    try:
        dl.ROOT = tmp
        dl.RENDER_REGISTRY = lambda: ['registered.md']
        got = {d for d, _c in dl.check_unrendered(list(docs))}
        dl.RENDER_REGISTRY = None
        off = dl.check_unrendered(list(docs))
    finally:
        dl.ROOT, dl.RENDER_REGISTRY = saved
        shutil.rmtree(tmp, ignore_errors=True)
    cases = [
        ('a three-column table with no render is flagged', 'wide.md' in got),
        ('a registered document is not', 'registered.md' not in got),
        ('a two-column table is not', 'narrow.md' not in got),
        ('a table inside a code fence is not', 'fenced.md' not in got),
        ('the opt-out marker is honoured', 'optout.md' not in got),
        ('a record document is exempt', 'thing_record.md' not in got),
        ('no registry configured: the check stands aside', off == []),
    ]
    failed = [n for n, ok in cases if not ok]
    check(f'doc_lint flags a multi-column table with no render ({len(cases)} '
          f'stated cases)', not failed, '; '.join(failed))


def check_branch_store_and_its_callers():
    """The shared branch store (tools/branch_store.py, spec/SHARED_ENGINES_PLAN.md)
    and the two tools built on it, on a scratch remote. The store's own
    self-check covers both modes; this adds the callers' behaviour that the
    move onto the store had to keep: the lease board refuses an overlapping
    take from another holder, a replacing take drops the holder's older lease
    in the same commit, and every change is a commit (history); the result
    cache keeps KEEP entries per family, publishes as one root commit, pulls
    an entry byte for byte into another clone, and two clones publishing in
    turn on a stale tip keep both entries."""
    bad, cases = [], []
    # The store and its callers commit with git's ambient identity; a runner
    # or a clean $HOME may have none (practice: fixture-owns-its-state).
    env = dict(os.environ, PRECEDENT_TZ='UTC',
               GIT_AUTHOR_NAME='x', GIT_AUTHOR_EMAIL='x@example.invalid',
               GIT_COMMITTER_NAME='x', GIT_COMMITTER_EMAIL='x@example.invalid')
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'branch_store.py'), '--self-check'],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        bad.append('branch_store self-check: ' + (r.stdout + r.stderr).strip()[-300:])
    cases.append('store self-check')
    import tempfile
    script = r"""
import importlib, json, os, pathlib, subprocess, sys
sys.path.insert(0, sys.argv[1]); t = pathlib.Path(sys.argv[2])
def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
git("init", "-q", "--bare", str(t / "r.git"))
for c in "ab":
    git("clone", "-q", str(t / "r.git"), str(t / c))
    git("-C", str(t / c), "-c", "user.email=x@example.invalid", "-c", "user.name=x",
        "commit", "-q", "--allow-empty", "-m", "i")
    git("-C", str(t / c), "checkout", "-q", "-b", "w" + c)
def load(c):
    for m in ("lease_board", "result_cache"): sys.modules.pop(m, None)
    lb = importlib.import_module("lease_board"); rc = importlib.import_module("result_cache")
    lb.REPO = rc.REPO = str(t / c); rc.KEEP = 2; rc.WAIT_S = 2; rc.POLL_S = 1
    return lb, rc
out = {}
lb, rc = load("a"); lb.take(["X"], "k", lease_id="L1")
lbB, _ = load("b")
try: lbB.take(["X"], "k", lease_id="L2"); out["refused"] = False
except lbB.LeaseConflict: out["refused"] = True
lb, _ = load("a"); lb.take(["Y"], "k", lease_id="L3", replace_kind=True)
out["board"] = sorted(lb.board())
out["coord_commits"] = int(git("-C", str(t / "r.git"), "rev-list", "--count", "coord"))
_, rc = load("a"); m = t / "a" / "m"; m.mkdir()
for i, k in enumerate(["aaaaaaaa1", "bbbbbbbb2", "cccccccc3"]):
    f = m / f"s_{k}.pkl"; f.write_bytes(bytes([i]) * 100); rc.publish(f)
_, rcB = load("b"); rcB._fetch()
_, rcA = load("a"); f = m / "o_dddddddd4.pkl"; f.write_bytes(b"A"); rcA.publish(f)
g = t / "b" / "m" / "p_eeeeeeee5.pkl"; g.parent.mkdir(); g.write_bytes(b"B"); rcB.publish(g)
out["index"] = sorted(json.loads(git("-C", str(t / "r.git"), "show", "result-cache:index.json")))
out["cache_commits"] = int(git("-C", str(t / "r.git"), "rev-list", "--count", "result-cache"))
_, rcB = load("b"); d = t / "b" / "m" / "s_cccccccc3.pkl"
out["pulled"] = rcB.ready(d, claim=False) and d.read_bytes() == bytes([2]) * 100
print(json.dumps(out))
"""
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run([sys.executable, '-c', script, str(ROOT / 'tools'), t],
                           capture_output=True, text=True, env=env)
        try:
            out = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return (False, '', 'callers script failed: ' + r.stderr.strip()[-400:])
    want = {'refused': True, 'board': ['L3'], 'coord_commits': 2,
            'index': ['o_dddddddd4.pkl', 'p_eeeeeeee5.pkl', 's_bbbbbbbb2.pkl', 's_cccccccc3.pkl'],
            'cache_commits': 1, 'pulled': True}
    for k, v in want.items():
        cases.append(k)
        if out.get(k) != v:
            bad.append(f'{k}: got {out.get(k)!r}, want {v!r}')
    return (not bad, f'{len(cases)} stated cases', '; '.join(bad))


def check_practice_ships_its_files():
    """practice: practice-carries-its-files -- a practice's `ships:` files
    reach every consumer, a publishing set is held to them at its own push,
    and a shipped test that reads a source-only tools/ file fails at home.

    THE INCIDENT (2026-09-26): create-word-doc's shipped test copies
    tools/create_word_doc.py, the materializer never delivered tools/
    scripts, and a consumer's deep check went red on a test nobody there
    could fix. Three mechanisms close it, and each has its own way to
    regress silently, so each is exercised in both directions here
    (practice: control-asserts-which-failure):

    * precedent_materialize.py delivers, records, drift-checks, honours a
      declared decline, and refuses the malformed and the colliding;
    * precedent_check.py's practice-carries-its-files fires in a source set
      on an undeclared dependency and on a declared file the set lacks, and
      is quiet once the declaration is right;
    * precedent_consumer_shape.py fails the test that reads a source-only
      file, passes it once the file is shipped, and leaves the source's own
      checkout untouched."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-ships-'))
    cases = []

    def practice(root, slug, ships=None, checked_by='null', body_link=''):
        p = root / 'practices' / f'{slug}.md'
        p.parent.mkdir(parents=True, exist_ok=True)
        ships_line = f'ships: {json.dumps(ships)}\n' if ships is not None else ''
        p.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x"\n'
            f'gates: []\nindex_clause: "x"\nchecked_by: {checked_by}\n'
            f'{ships_line}defines: []\nstatus: active\nsupersedes: []\n'
            f'overrides: null\nadded: 2026-09-26\n'
            f'approved_by: "harness, 2026-09-26"\n---\n## Rule\nx{body_link}\n\n'
            f'## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')

    try:
        # --- delivery ------------------------------------------------------
        uni, team, consumer = tmp / 'universal', tmp / 'team', tmp / 'consumer'
        practice(uni, 'uni-fixture')
        practice(team, 'team-fixture', ships=['tools/helper.py'],
                 body_link=' Run [the helper](../tools/helper.py).')
        (team / 'tools').mkdir(parents=True)
        helper = team / 'tools' / 'helper.py'
        helper.write_text('print("v1")\n', encoding='utf-8')
        os.chmod(helper, 0o755)
        consumer.mkdir()

        def config(extra=None):
            d = {'visibility': 'private',  # team source, run directly
                 'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                {'level': 'team', 'name': 'precedent-team-fixture',
                 'path': str(team)}]}
            d.update(extra or {})
            (consumer / 'precedent.json').write_text(json.dumps(d),
                                                     encoding='utf-8')
        config()
        fixture_home = tmp / 'home'
        fixture_home.mkdir()
        env = {k: v for k, v in os.environ.items()
               if k != 'CLAUDE_CODE_REMOTE' and not k.startswith('PRECEDENT_')}
        env['HOME'] = str(fixture_home)
        tool = str(ROOT / 'tools' / 'precedent_materialize.py')

        def run():
            r = subprocess.run([sys.executable, tool, '--out', str(consumer),
                                '--repo', str(consumer)],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def manifest():
            mf = consumer / 'MANIFEST.json'
            return json.loads(mf.read_text(encoding='utf-8')) if mf.is_file() else {}

        def drift():
            return _drift_at(consumer)

        def _drift_at(where):
            sys.path.insert(0, str(ROOT / 'tools'))
            import precedent_resolve as _pr, precedent_materialize as _pm
            # The fixture owns the whole environment the resolver reads, not
            # only HOME: a PRECEDENT_* variable left in this process would
            # hand it this container's real individual source.
            saved = {k: v for k, v in os.environ.items()
                     if k == 'HOME' or k.startswith('PRECEDENT_')}
            try:
                for k in saved:
                    del os.environ[k]
                os.environ['HOME'] = str(fixture_home)
                # Named explicitly: the resolver fixed its default user
                # config path from the real HOME when it was first imported.
                user_cfg = tmp / 'user-config.json'
                user_cfg.write_text('{}', encoding='utf-8')
                srcs = _pr.load_config(str(where), str(user_cfg))
                return _pm.drift(srcs, _pr.resolve(srcs), where)
            finally:
                os.environ.pop('HOME', None)
                os.environ.update(saved)

        delivered = consumer / 'tools' / 'helper.py'

        # Every read and write of the delivered file tolerates its absence:
        # a regression in delivery must show up as named failing cases, not
        # a traceback (practice: control-asserts-which-failure).
        def text_of(path):
            return path.read_text(encoding='utf-8') if path.is_file() else ''

        def put(path, text):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        rc, out = run()
        cases.append(('a declared `ships:` file is delivered to the same path '
                      'in the consumer', rc == 0 and delivered.is_file(), failure_detail(out, 300)))
        cases.append(('it keeps its executable bit',
                      delivered.is_file() and os.access(delivered, os.X_OK)))
        rows = [f for f in manifest().get('ships', [])
                if f.get('path') == 'tools/helper.py']
        cases.append(('it is recorded in MANIFEST.json with the practice and '
                      'source that ship it',
                      len(rows) == 1 and rows[0].get('practice') == 'team-fixture'
                      and rows[0].get('source') == 'precedent-team-fixture'))
        linked = consumer / 'practices' / 'team-fixture.md'
        cases.append(("the practice's relative link to the file it ships stays "
                      'relative -- the file is right there',
                      '](../tools/helper.py)' in text_of(linked)))
        cases.append(('a fresh sync reports no drift', drift() == []))

        helper.write_text('print("v2")\n', encoding='utf-8')
        rc, out = run()
        cases.append(("a change in the source reaches the consumer on the next "
                      'sync, quietly',
                      rc == 0 and 'v2' in text_of(delivered)
                      and 'REPLACED' not in out))

        # practice: repair-cannot-discard-work. This consumer is not a git
        # checkout, so a hand-edit here exists nowhere else: it is kept.
        put(delivered, 'print("hand edited")\n')
        cases.append(('a hand-edit no commit holds is drift, named as unsaved',
                      any('tools/helper.py holds changes no git commit has' in x
                          for x in drift())))
        rc, out = run()
        cases.append(('a sync leaves a hand-edit no commit holds untouched, and '
                      'says how to keep it or take the set\'s copy',
                      rc == 0 and 'hand edited' in text_of(delivered)
                      and 'LEFT UNTOUCHED' in out and 'REPLACED' not in out
                      and 'tools/helper.py' in out, failure_detail(out, 300)))
        delivered.unlink()
        rc, out = run()
        cases.append(('deleting it and syncing again takes the set\'s copy',
                      rc == 0 and 'v2' in text_of(delivered)))

        # --- git: the 2026-10-16 incident, the origin case, an adoption ----
        gconsumer = tmp / 'gconsumer'
        shutil.copytree(consumer, gconsumer)
        gdelivered = gconsumer / 'tools' / 'helper.py'

        def grun():
            r = subprocess.run([sys.executable, tool, '--out', str(gconsumer),
                                '--repo', str(gconsumer)],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def ggit(*a):
            return fixture_git(gconsumer, *a)
        ggit('init', '-q')
        ggit('config', 'user.email', 'fixture@example.com')
        ggit('config', 'user.name', 'fixture')
        ggit('add', '-A')
        ggit('commit', '-qm', 'synced')
        put(gdelivered, 'print("uncommitted")\n')
        rc, out = grun()
        cases.append(('an uncommitted edit to a delivered, committed file is '
                      'left untouched -- the incident: it used to be replaced '
                      'and `git diff` showed nothing',
                      rc == 0 and 'uncommitted' in text_of(gdelivered)
                      and 'LEFT UNTOUCHED' in out and 'no git commit has' in out,
                      failure_detail(out, 300)))
        ggit('commit', '-qam', 'our own newer helper')
        rc, out = grun()
        cases.append(('once committed, the repository\'s own version is kept, '
                      'and the sync asks for its answer',
                      rc == 0 and 'uncommitted' in text_of(gdelivered)
                      and 'upstream-bug-stops-here' in out
                      and 'owed-upstream' in out, failure_detail(out, 300)))
        # practice: upstream-bug-stops-here (2026-10-17): kept is not
        # answered. It is drift until precedent.json records its answer.
        cases.append(('...and it is drift until it has its answer',
                      any('tools/helper.py was committed here after the set'
                          in x for x in _drift_at(gconsumer))))
        gcfg = json.loads((gconsumer / 'precedent.json').read_text(encoding='utf-8'))
        gcfg['upstream_edits'] = {'tools/helper.py': {
            'answer': 'owed-upstream',
            'detail': 'https://example.com/set/pull/1 carries it to the set'}}
        (gconsumer / 'precedent.json').write_text(json.dumps(gcfg), encoding='utf-8')
        cases.append(('...and is not drift once "owed-upstream" records the '
                      'link that carries it up',
                      not any('tools/helper.py' in x for x in
                              _drift_at(gconsumer))))
        gcfg.pop('upstream_edits')
        (gconsumer / 'precedent.json').write_text(json.dumps(gcfg), encoding='utf-8')
        # The origin case before any delivery is recorded: this file's own
        # history holds the set's exact bytes, then moved on.
        mf = gconsumer / 'MANIFEST.json'
        m = json.loads(mf.read_text(encoding='utf-8'))
        m.pop('ships', None)
        mf.write_text(json.dumps(m), encoding='utf-8')
        put(gdelivered, 'print("v2")\n')
        ggit('commit', '-qam', 'the copy the set later took')
        put(gdelivered, 'print("origin, newer")\n')
        ggit('commit', '-qam', 'the origin moves on')
        rc, out = grun()
        cases.append(('a repository whose history holds the set\'s copy keeps '
                      'its newer one, with no delivery on record',
                      rc == 0 and 'origin, newer' in text_of(gdelivered)
                      and 'LEFT UNTOUCHED' in out
                      and 'committed its own version after' in out, failure_detail(out, 300)))
        # A committed hand-copy the set never came from is still adopted: git
        # keeps what goes.
        m = json.loads(mf.read_text(encoding='utf-8'))
        m.pop('ships', None)
        mf.write_text(json.dumps(m), encoding='utf-8')
        shutil.rmtree(gconsumer / '.git')
        put(gdelivered, 'print("hand copy")\n')
        ggit('init', '-q')
        ggit('config', 'user.email', 'fixture@example.com')
        ggit('config', 'user.name', 'fixture')
        ggit('add', '-A')
        ggit('commit', '-qm', 'a hand copy')
        rc, out = grun()
        cases.append(('a committed hand-copy whose history never held the '
                      'set\'s copy is replaced, and the way to keep one named',
                      rc == 0 and 'v2' in text_of(gdelivered)
                      and 'REPLACED' in out and 'declined_ships' in out,
                      failure_detail(out, 300)))

        # Delivered last time and unchanged since: the 2026-10-29 incident.
        # The manifest names a delivery whose hash disagrees with the file,
        # yet the file is byte for byte what the set shipped -- nothing of
        # this repository's is at stake, so the set's newer copy replaces it.
        def stale_manifest_row(m):
            m['ships'] = [dict(r, sha256_16='0' * 16) for r in m.get('ships', [])]
            m.setdefault('ships', []).append({'path': 'tools/helper.py',
                                              'sha256_16': '0' * 16})
            mf.write_text(json.dumps(m), encoding='utf-8')
        ggit('add', '-A')
        ggit('commit', '-qm', 'the set\'s v2, delivered')
        stale_manifest_row(json.loads(mf.read_text(encoding='utf-8')))
        helper.write_text('print("v3")\n', encoding='utf-8')
        rc, out = grun()
        cases.append(('a delivered file unchanged since, which the committed '
                      'manifest records, takes the set\'s newer copy and is '
                      'not kept as the repository\'s own',
                      rc == 0 and 'v3' in text_of(gdelivered)
                      and 'LEFT UNTOUCHED' not in out, failure_detail(out, 300)))
        # The same, with no committed manifest row: the set's own history
        # holds the bytes.
        helper.write_text('print("v2")\n', encoding='utf-8')
        fixture_git(team, 'init', '-q')
        fixture_git(team, 'config', 'user.email', 'fixture@example.com')
        fixture_git(team, 'config', 'user.name', 'fixture')
        fixture_git(team, 'add', '-A')
        fixture_git(team, 'commit', '-qm', 'set v2')
        put(gdelivered, 'print("v2")\n')
        m = json.loads(mf.read_text(encoding='utf-8'))
        m.pop('ships', None)
        mf.write_text(json.dumps(m), encoding='utf-8')
        ggit('add', '-A')
        ggit('commit', '-qm', 'v2 again, no delivery recorded')
        stale_manifest_row(m)
        helper.write_text('print("v3")\n', encoding='utf-8')
        fixture_git(team, 'commit', '-qam', 'set v3')
        rc, out = grun()
        cases.append(('...and so does one whose bytes only the set\'s own '
                      'history holds',
                      rc == 0 and 'v3' in text_of(gdelivered)
                      and 'LEFT UNTOUCHED' not in out, failure_detail(out, 300)))
        shutil.rmtree(team / '.git')
        helper.write_text('print("v2")\n', encoding='utf-8')

        # --- decline --------------------------------------------------------
        config({'declined_ships': {'tools/helper.py': 'we have our own'}})
        put(delivered, 'print("ours")\n')
        rc, out = run()
        declined = manifest().get('declined_ships', [])
        cases.append(('a declined file is left alone and the decline is '
                      'recorded with its reason',
                      rc == 0 and 'ours' in text_of(delivered)
                      and declined == [{'path': 'tools/helper.py',
                                        'slug': 'team-fixture',
                                        'reason': 'we have our own'}]))
        cases.append(('a declined file is not drift', drift() == []))
        config({'declined_ships': {'tools/helper.py': ''}})
        rc, out = run()
        cases.append(('a decline without a reason refuses',
                      rc == 1 and 'non-empty reason' in out))
        config({'declined_ships': {'tools/nothing.py': 'stale'}})
        rc, out = run()
        cases.append(('a decline naming nothing any practice ships warns as '
                      'stale', rc == 0 and 'the decline is stale' in out))
        config()
        run()

        # --- no longer shipped: removed while unchanged, else reported -------
        def cgit(*a):
            subprocess.run(['git', '-C', str(consumer), *a], capture_output=True)
        put(delivered, text_of(helper))   # the decline above left "ours" there
        cgit('init', '-q')
        cgit('config', 'user.email', 'fixture@example.com')
        cgit('config', 'user.name', 'fixture')
        cgit('add', '-A')
        cgit('commit', '-qm', 'the consumer')
        practice(team, 'team-fixture', ships=[])
        rc, out = run()
        cases.append(('a file no practice ships any more is removed in the same '
                      'sync while it is exactly what was shipped and nothing '
                      'names it', rc == 0 and not delivered.is_file()
                      and 'removed shipped file(s)' in out, failure_detail(out, 300)))
        cases.append(('a consumer that ships nothing carries no `ships` key '
                      'in its manifest (no churn for every other consumer)',
                      'ships' not in manifest()))
        practice(team, 'team-fixture', ships=['tools/helper.py'])
        run()
        cgit('add', '-A')
        cgit('commit', '-qm', 'shipped again')
        put(delivered, 'print("edited here")\n')
        practice(team, 'team-fixture', ships=[])
        rc, out = run()
        cases.append(('a file no practice ships any more that was edited here is '
                      'reported and left in place', rc == 0 and delivered.is_file()
                      and 'no practice in force here ships any more' in out
                      and 'edited here' in out, failure_detail(out, 300)))

        # --- refusals -------------------------------------------------------
        practice(team, 'team-fixture', ships=['tools/helper.py'])
        practice(uni, 'uni-fixture', ships=['tools/helper.py'])
        (uni / 'tools').mkdir(exist_ok=True)
        (uni / 'tools' / 'helper.py').write_text('x\n', encoding='utf-8')
        rc, out = run()
        cases.append(('two sources shipping one destination refuses',
                      rc == 1 and 'destination collision' in out))
        practice(uni, 'uni-fixture')
        for bad, words in ((['tools/precedent_check.py'], 'is an engine file'),
                           (['tools/*.py'], 'is a glob'),
                           (['../escape.py'], 'walks above the repository'),
                           (['tools/checks/check_x.py'], 'travel already'),
                           ('"tools/helper.py"', 'must be a JSON list')):
            if isinstance(bad, str):
                p = team / 'practices' / 'team-fixture.md'
                practice(team, 'team-fixture', ships=[])
                p.write_text(p.read_text(encoding='utf-8').replace(
                    'ships: []', f'ships: {bad}'), encoding='utf-8')
            else:
                practice(team, 'team-fixture', ships=bad)
            rc, out = run()
            cases.append((f'`ships: {bad}` refuses ({words})',
                          rc == 1 and words in out, failure_detail(out, 200)))
        practice(team, 'team-fixture', ships=['tools/absent.py'])
        rc, out = run()
        cases.append(('a declared file missing from its source warns and is '
                      'skipped', rc == 0 and 'NOT delivered' in out
                      and not (consumer / 'tools' / 'absent.py').exists()))
        cases.append(('the fixture owned its source set',
                      not any(fixture_home.iterdir())))

        # --- the source-side check -----------------------------------------
        src = tmp / 'set'
        src.mkdir()
        shutil.copytree(ROOT / 'tools', src / 'tools',
                        ignore=shutil.ignore_patterns('__pycache__', 'checks'))
        (src / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'source', 'files': []}), encoding='utf-8')
        (src / 'tools' / 'own_tool.py').write_text('print(1)\n', encoding='utf-8')
        checks_dir = src / 'tools' / 'checks'
        (checks_dir / 'tests').mkdir(parents=True)
        (checks_dir / 'check_x.py').write_text('import sys\nsys.exit(0)\n',
                                               encoding='utf-8')
        (checks_dir / 'tests' / 'test_x.sh').write_text(
            '#!/bin/bash\nset -e\ncd "$(dirname "$0")/../../.."\n'
            'SET_ROOT="$(pwd)"\n'
            'if [ -f "$SET_ROOT/tools/probed.py" ]; then echo p; fi\n'
            'cp "$SET_ROOT/tools/own_tool.py" "$(mktemp -d)/"\n'
            'git -C "$SET_ROOT" status --porcelain -- tools | '
            '(! grep -q .)\necho ok\n', encoding='utf-8')
        practice(src, 'x-practice', checked_by='"tools/checks/check_x.py"')
        genv = dict(env, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com',
                    GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.com',
                    GIT_CONFIG_GLOBAL=str(tmp / 'gitconfig'),
                    GIT_CONFIG_NOSYSTEM='1')
        (tmp / 'gitconfig').write_text('', encoding='utf-8')
        for args in (['init', '-q'], ['add', '-A'], ['commit', '-qm', 'base']):
            subprocess.run(['git', '-C', str(src), *args], env=genv,
                           capture_output=True)

        def pcheck():
            r = subprocess.run([sys.executable, str(src / 'tools' / 'precedent_check.py'),
                                '--only', 'practice-carries-its-files'],
                               capture_output=True, text=True, cwd=str(src), env=genv)
            return r.returncode, r.stdout + r.stderr

        rc, out = pcheck()
        cases.append(('the check fires in a source set on a shipped test that '
                      'reads an undeclared source-only tools/ file, naming it',
                      rc == 1 and 'test_x.sh:6' in out
                      and '`tools/own_tool.py`, which is in this repository'
                      ' and reaches no consumer' in out, failure_detail(out, 400)))
        cases.append(('a path the test probes first is not reported',
                      'tools/probed.py' not in out))
        practice(src, 'x-practice', checked_by='"tools/checks/check_x.py"',
                 ships=['tools/own_tool.py'])
        rc, out = pcheck()
        cases.append(('declaring it in `ships:` clears the check',
                      rc == 0 and '1 passed' in out, failure_detail(out, 300)))
        practice(src, 'x-practice', checked_by='"tools/checks/check_x.py"',
                 ships=['tools/own_tool.py', 'tools/left_behind.py'])
        rc, out = pcheck()
        cases.append(('a `ships:` file the set does not carry fires -- the '
                      'moved-without-its-script case',
                      rc == 1 and 'ships `tools/left_behind.py`, which is not '
                      'in this repository' in out, failure_detail(out, 300)))
        practice(src, 'x-practice', checked_by='"tools/checks/check_gone.py"',
                 ships=['tools/own_tool.py'])
        rc, out = pcheck()
        cases.append(('a checked_by script the set does not carry fires',
                      rc == 1 and 'checked_by names `tools/checks/check_gone.py`'
                      in out, failure_detail(out, 300)))
        practice(src, 'x-practice', checked_by='"tools/checks/check_x.py"',
                 ships=['tools/own_tool.py'])

        # --- the consumer-shaped run -----------------------------------------
        shape = str(ROOT / 'tools' / 'precedent_consumer_shape.py')

        def shape_run():
            r = subprocess.run([sys.executable, shape, '--repo', str(src)],
                               capture_output=True, text=True, env=genv)
            return r.returncode, r.stdout + r.stderr

        rc, out = shape_run()
        cases.append(('with the file shipped, the consumer-shaped run passes, '
                      'and a git status in the copy is as clean as at home',
                      rc == 0 and 'all 1 passed' in out, failure_detail(out, 400)))
        practice(src, 'x-practice', checked_by='"tools/checks/check_x.py"')
        rc, out = shape_run()
        cases.append(('undeclared, the consumer-shaped run fails the test and '
                      'lists the file the copy lacks',
                      rc == 1 and 'FAILED: test_x.sh' in out
                      and any('no consumer receives:' in l
                              and 'tools/own_tool.py' in l.split()
                              for l in out.splitlines()),
                      failure_detail(out, 400)))
        cases.append(("the source's own checkout is untouched by the run",
                      (src / 'tools' / 'own_tool.py').is_file()
                      and subprocess.run(['git', '-C', str(src), 'status',
                                          '--porcelain', '-uno', '--', 'tools'],
                                         capture_output=True, text=True,
                                         env=genv).stdout == ''))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a practice\'s `ships:` files travel, are held at the source, and '
          f'a home-only dependency fails at home ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_doc_lifecycle_fires_and_clears():
    """tools/doc_lifecycle.py -- the document status header, checked.

    checkable-gets-checked requires a firing test, not merely a check that
    passes: plant each violation, prove it fails, remove it, prove the
    unplanted tree passes. Every case runs against a THROWAWAY tree, never
    against spec/ -- a check whose test mutates the repo it audits cannot be
    run twice.

    The `Last updated:` case is the one worth reading. A first version of
    the detector was `'Last updated:' in text`, and it fired on
    spec/DOCUMENT_LIFECYCLE.md -- the document that SPECIFIES this rule and
    necessarily quotes the string it forbids, five times. A check that
    fails the file explaining it teaches the first reader that the checker
    is broken, so the two cases below pin the distinction: a real HTML
    comment fails, the same text inside a code span does not.
    """
    import tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import doc_lifecycle as dl

    GOOD = ('---\n'
            'title:         A Reference\n'
            'kind:          reference\n'
            'status:        current\n'
            'opened:        2026-09-07\n'
            'closed:        null\n'
            'superseded_by: null\n'
            'supersedes:    []\n'
            'audience:      session\n'
            'summary:       What the thing is.\n'
            '---\n\n# A Reference\n\nBody.\n')

    def _run(text, extra=None):
        """-> (findings, unstamped, stamped) for a one-file throwaway tree."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / 'spec').mkdir()
            (root / 'spec' / 'D.md').write_text(text, encoding='utf-8')
            for name, body in (extra or {}).items():
                (root / 'spec' / name).write_text(body, encoding='utf-8')
            return dl.scan(root=root)

    def _fires(name, text, needle, extra=None):
        f, _, _ = _run(text, extra)
        return (name, bool(f) and any(needle in x for x in f))

    cases = [
        # The unplanted control comes FIRST: a test suite where every case
        # is a planted failure cannot tell a working check from one that
        # returns a finding for everything.
        ('the unplanted document passes', not _run(GOOD)[0]),
        ('and it counts as stamped', _run(GOOD)[2] == 1),

        _fires('an illegal status for the kind',
               GOOD.replace('status:        current', 'status:        open'),
               'is not legal for kind'),
        _fires('an unknown kind',
               GOOD.replace('kind:          reference', 'kind:          memo'),
               'is not one of'),
        _fires('a title that disagrees with the first heading',
               GOOD.replace('# A Reference', '# Something Else'),
               '!= first heading'),
        _fires('a missing required field',
               GOOD.replace('supersedes:    []\n', ''),
               'missing required field'),
        _fires('an unknown audience',
               GOOD.replace('audience:      session', 'audience:      everyone'),
               'audience'),
        _fires('an opened date that is not YYYY-MM-DD',
               GOOD.replace('opened:        2026-09-07', 'opened:        Sept 7'),
               'is not YYYY-MM-DD'),
        _fires('status closed with no closed date',
               GOOD.replace('kind:          reference', 'kind:          brief')
                   .replace('status:        current', 'status:        closed'),
               'no `closed:` date'),
        _fires('a closed date on a document that is not closed',
               GOOD.replace('closed:        null', 'closed:        2026-09-07'),
               'but status is'),
        _fires('status superseded with no successor',
               GOOD.replace('status:        current', 'status:        superseded'),
               'no `superseded_by:`'),
        _fires('a superseded_by that does not resolve',
               GOOD.replace('status:        current', 'status:        superseded')
                   .replace('superseded_by: null', 'superseded_by: spec/GONE.md'),
               'does not exist'),
        _fires('a summary that does not end in a period',
               GOOD.replace('summary:       What the thing is.',
                            'summary:       What the thing is'),
               'does not end in a period'),
        _fires('a real `Last updated:` comment on a reference',
               GOOD.replace('\n# A Reference',
                            '\n<!-- Last updated: 2026-09-07 -->\n\n# A Reference'),
               'Last updated'),
    ]

    # The false-positive controls: the rule's own text must not trip it.
    quoted = GOOD.replace('Body.',
                          'A file may not carry `<!-- Last updated: x -->`.')
    cases.append(('the same string inside a code span does NOT fire',
                  not _run(quoted)[0]))
    fenced = GOOD.replace('Body.', '```\n<!-- Last updated: x -->\n```')
    cases.append(('nor inside a fenced block', not _run(fenced)[0]))
    brief = (GOOD.replace('kind:          reference', 'kind:          brief')
                 .replace('status:        current', 'status:        open')
                 .replace('\n# A Reference',
                          '\n<!-- Last updated: 2026-09-07 -->\n\n# A Reference'))
    cases.append(('and a `brief`, whose subject IS the date, may carry one',
                  not _run(brief)[0]))

    # An unstamped file is reported but is not a finding, while the backfill
    # is in progress. Both halves matter: reported, and not fatal.
    f, un, st = _run(GOOD, extra={'U.md': '# Unstamped\n\nNo frontmatter.\n'})
    cases.append(('an unstamped document is reported', un == ['spec/U.md']))
    cases.append(('and is not itself a finding, pre-phase-2', not f))

    failed = [n for n, ok in cases if not ok]
    check(f'the document lifecycle check fires on each planted violation and '
          f'clears the unplanted tree ({len(cases)} stated cases)',
          not failed, '; '.join(failed))


def check_decommission_exempt_record_still_blocks_a_link():
    """THE INCIDENT (2026-10-07, a consumer decommissioning a filing shim).
    Closed open items declared exempt as historical records passed the
    decommission audit, then failed the next landing: each held a markdown
    LINK to the deleted file, and the link check refuses a broken link
    whatever the registry says. Exempt lets a record keep naming a path;
    it cannot keep a link to it alive. Cases: an exempt record that names
    the path as text does not block; one that links to it blocks, with the
    fix in the message; with the link turned into text, the audit is
    CLEAR."""
    import tempfile, shutil as _shutil, json as _json
    tool = ROOT / 'tools' / 'precedent_decommission.py'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-decom-link-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        genv = dict(os.environ, GIT_AUTHOR_NAME='t',
                    GIT_AUTHOR_EMAIL='harness@example.com',
                    GIT_COMMITTER_NAME='t',
                    GIT_COMMITTER_EMAIL='harness@example.com')

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=genv)

        def w(rel, text):
            f = repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')

        repo.mkdir()
        git('init', '-q')
        w('tools/old_shim.py', '# retired\n')
        w('todo/named.md', 'Closed. The work was in tools/old_shim.py.\n')
        w('todo/linked.md', 'Closed. See [old_shim.py](../tools/old_shim.py).\n')
        w('process/decommissioned_paths.json', _json.dumps(
            {'decommissioned': [],
             'exempt_files': ['todo/named.md', 'todo/linked.md']}))
        git('add', '-A')
        git('commit', '-qm', 'fixture')

        def run():
            r = subprocess.run([sys.executable, str(tool), 'tools/old_shim.py'],
                               capture_output=True, text=True, cwd=str(repo),
                               timeout=120)
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('an exempt record naming the path as text does not block',
                      'todo/named.md:' not in out, failure_detail(out, 1500)))
        cases.append(('an exempt record LINKING to the path blocks, and says '
                      'to drop the link', rc == 1 and 'todo/linked.md:1' in out
                      and 'drop the link' in out, failure_detail(out, 1500)))
        w('todo/linked.md', 'Closed. See `tools/old_shim.py`.\n')
        git('add', '-A')
        git('commit', '-qm', 'unlink')
        rc2, out2 = run()
        cases.append(('with the link turned into text, the audit is CLEAR',
                      rc2 == 0 and 'CLEAR' in out2, failure_detail(out2, 1500)))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'decommission audit refuses a link in an exempt record '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:800]}' for n, d in bad))


def check_decommission_skips_generated_files_and_prose():
    """THE INCIDENT (2026-09-28, a classic-layout migration rehearsal in a
    real consumer). Decommissioning `process/personal` could never reach
    CLEAR: the basename pass searched the bare word `personal` and matched
    ordinary English in the loader-generated AGENTS.md, the vendored engine
    (whose own docstring names `process/personal`) and every materialized
    practice -- 141 blockers, none of them the repo's to repoint, and the
    tool has no flag to skip one by design.

    Two fixes, each with its negative control, because the audit is only
    worth running while it still refuses a real reference:
      * a directory's basename is searched as `base/`, so prose no longer
        matches but `personal/README.md` in a hand-written doc still blocks;
      * files tools/ENGINE_MANIFEST.json (files, hook_files) or the
        materializer's MANIFEST.json record are reported, not scanned, while
        a hand-authored practice the manifest does not list still blocks."""
    import tempfile, shutil as _shutil, json as _json
    tool = ROOT / 'tools' / 'precedent_decommission.py'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-decom-gen-'))
    cases = []
    try:
        repo = tmp / 'consumer'
        genv = dict(os.environ, GIT_AUTHOR_NAME='t',
                    GIT_AUTHOR_EMAIL='harness@example.com',
                    GIT_COMMITTER_NAME='t',
                    GIT_COMMITTER_EMAIL='harness@example.com')

        def git(*a):
            return subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True, env=genv)

        def w(rel, text):
            f = repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')

        repo.mkdir()
        git('init', '-q')
        w('process/personal/README.md', 'the retired personal pack\n')
        w('tools/engine_x.py',
          '"""Retires process/personal/README.md on refresh."""\n')
        w('.claude/hooks/h.sh', '# reads process/personal when present\n')
        w('tools/ENGINE_MANIFEST.json', _json.dumps(
            {'kind': 'consumer', 'files': ['engine_x.py'],
             'hook_files': ['h.sh']}))
        w('practices/p1.md', 'Older installs kept a process/personal tree.\n')
        w('MANIFEST.json', _json.dumps(
            {'generated_by': 'tools/precedent_materialize.py',
             'practices': [{'slug': 'p1'}], 'checks': [], 'adapters': []}))
        w('AGENTS.md', 'Give the GitHub steps for a personal repo, and a '
                       'personal welcome message. We archive nothing.\n')
        w('archive/old.md', 'a retired top-level directory\n')
        # The real references -- negative controls.
        w('docs/guide.md', 'See personal/README.md for the old layout.\n'
                           'And archive/old.md for the one before.\n')
        w('practices/own.md', 'We still read process/personal at start.\n')
        git('add', '-A')
        git('commit', '-qm', 'fixture')

        def run(target='process/personal'):
            r = subprocess.run([sys.executable, str(tool), target],
                               capture_output=True, text=True, cwd=str(repo),
                               timeout=120)
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('prose using the word in AGENTS.md does not block',
                      'AGENTS.md:' not in out, failure_detail(out, 1500)))
        cases.append(('the vendored engine file, hook and materialized '
                      'practice do not block',
                      not any(f'{x}:' in out for x in
                              ('tools/engine_x.py', '.claude/hooks/h.sh',
                               'practices/p1.md')), failure_detail(out, 1500)))
        cases.append(('and the report says they were skipped, and that 3 '
                      'of them mention it',
                      'not scanned' in out and '3 mention it' in out,
                      failure_detail(out, 1500)))
        cases.append(('a hand-written doc naming personal/README.md still '
                      'blocks (by basename)',
                      rc == 1 and 'docs/guide.md:1' in out, failure_detail(out, 1500)))
        cases.append(('a practice the materializer never wrote still blocks',
                      'practices/own.md:1' in out, failure_detail(out, 1500)))
        rc_a, out_a = run('archive')
        cases.append(('a TOP-LEVEL directory is searched as `archive/`: the '
                      'verb in AGENTS.md does not block, the path in a doc '
                      'does', rc_a == 1 and 'AGENTS.md:' not in out_a
                      and 'docs/guide.md:2' in out_a, failure_detail(out_a, 1500)))

        (repo / 'docs' / 'guide.md').unlink()
        (repo / 'practices' / 'own.md').unlink()
        git('add', '-A')
        git('commit', '-qm', 'repoint the real references')
        rc2, out2 = run()
        rc3, out3 = run('archive')
        cases.append(('with the real references gone, the audit is CLEAR',
                      rc2 == 0 and 'CLEAR' in out2
                      and rc3 == 0 and 'CLEAR' in out3,
                      failure_detail(out2, 1000) + failure_detail(out3, 1000)))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'decommission audit skips generated files and prose, and still '
          f'refuses a real reference ({len(cases)} stated cases)',
          not bad, '; '.join(f'{n} -- {d[:800]}' for n, d in bad))


def check_workflows_use_actions_that_run_on_node_24():
    """GitHub warned "Node.js 20 is deprecated" for actions/checkout@v4 and
    actions/setup-python@v5 (2026-10-14), in this repo's workflows and in
    the templates consumers receive. Each moved to the first release that
    runs on Node 24 (checkout v5, setup-python v6; Morgan, 2026-10-14:
    "Yes on fix 6"). No workflow or template here names an older one."""
    floor = {'actions/checkout': 5, 'actions/setup-python': 6}
    files = sorted((ROOT / '.github' / 'workflows').glob('*.yml')) + \
        sorted((ROOT / 'templates' / 'github-actions').glob('*.template'))
    old = []
    for f in files:
        for n, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            m = re.search(r'uses:\s*(actions/(?:checkout|setup-python))@v(\d+)', line)
            if m and int(m.group(2)) < floor[m.group(1)]:
                old.append(f'{f.relative_to(ROOT)}:{n} {m.group(1)}@v{m.group(2)}')
    check(f'workflows and templates use actions that run on Node 24 '
          f'({len(files)} files)', files and not old, '; '.join(old))

def check_vendor_engine_names_a_dependent_of_a_deleted_file():
    """THE INCIDENT (2026-09-21,
    todo-2026-09-21-refresh-deletes-a-workflow-another-file-depends-on.md).
    A refresh deleted .github/workflows/precedent-check.yml from four
    practice sets. In each of them a second workflow had been PAUSED hours
    earlier, its header saying its checks "now run as steps in
    .github/workflows/precedent-check.yml's single job". The destination
    was gone; two commit-scope checks ran nowhere; nothing said anything.

    The deletion mechanics were already tested -- by the two checks above,
    thoroughly. What nothing tested, because nothing did it, is the other
    half: a deletion travels to every installed repo, and the question
    "does anything here still depend on this" never travelled with it.
    precedent_decommission.py asks it, within one repo, when a person runs
    it deliberately.

    Both directions, because the warning half of a reporter is worth
    nothing without the quiet half: a reporter that fires on a clean case
    trains people to ignore it, which is the state this was meant to
    correct.

    Unit-level on purpose: the subject is what _remove_dropped_engine_files
    PRINTS, and driving a whole refresh to observe one stderr line would
    make the case slower and its failure harder to read, without testing
    anything the two end-to-end checks above do not already cover."""
    import contextlib, io, shutil, tempfile
    import precedent_vendor_engine as pve

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-deldeps-'))
    cases = []
    try:
        def _fixture(name, referrer_text):
            repo = tmp / name
            (repo / 'tools').mkdir(parents=True)
            dropped = 'zzz_retired_helper.py'
            body = '# a vendored engine file upstream no longer ships\n'
            (repo / 'tools' / dropped).write_text(body, encoding='utf-8')
            if referrer_text:
                (repo / 'README.md').write_text(referrer_text, encoding='utf-8')
            manifest = {'files': [dropped],
                        'sha256': {dropped: hashlib.sha256(
                            body.encode('utf-8')).hexdigest()}}
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(err):
                removed = pve._remove_dropped_engine_files(
                    repo / 'tools', manifest, 'consumer')
            return repo, removed, err.getvalue()

        repo_a, removed_a, err_a = _fixture(
            'with-dependent',
            'Nightly we run tools/zzz_retired_helper.py against the tree.\n')
        cases.append(('the dropped engine file is deleted',
                      removed_a == ['zzz_retired_helper.py'],
                      repr(removed_a)))
        cases.append(('the file that still names it is reported, with its '
                      'path and line',
                      'README.md:1' in err_a
                      and 'zzz_retired_helper.py' in err_a,
                      err_a[:800]))
        cases.append(('the report does not refuse the refresh -- it warns',
                      err_a.strip().startswith('WARN'), err_a[:200]))

        _repo_b, removed_b, err_b = _fixture('no-dependent', None)
        cases.append(('a deletion nothing depends on stays quiet',
                      removed_b == ['zzz_retired_helper.py']
                      and 'still names it' not in err_b,
                      err_b[:800]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a refresh that deletes a vendored file names whatever still '
          f'depends on it ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_doc_lint_leaves_a_received_practice_to_its_source():
    """doc_lint's unlinked-reference warning skips a practice a consuming
    repo received from another source, and still warns on its own.

    2026-10-10, a consumer's update: two individual-set practices' Story
    sections named files of another repository in backticks, and every
    repo that received them saw eight "is not a link" lines at every update
    -- in files the next sync overwrites, so nobody there could act on
    them. Planted: one received practice, one repo-local, the same line."""
    import tempfile
    name = 'doc_lint leaves a received practice\'s links to its source'
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import doc_lint as dl
    finally:
        sys.path.pop(0)
    saved_root, saved_cache = dl.ROOT, list(dl._RECEIVED)
    cases = []
    try:
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            (repo / 'practices').mkdir()
            line = 'The helper lives in `precedent_resolve.py` and `README.md`.\n'
            for slug in ('received', 'own'):
                (repo / 'practices' / f'{slug}.md').write_text(line, encoding='utf-8')
            (repo / 'README.md').write_text('x\n', encoding='utf-8')
            dl.ROOT = repo
            dl._RECEIVED.clear()
            before = dl.check_file('practices/received.md')[1]
            (repo / 'MANIFEST.json').write_text(json.dumps({'practices': [
                {'slug': 'received', 'level': 'individual', 'source': 'someone'},
                {'slug': 'own', 'level': 'repo-local', 'source': 'local'}]}),
                encoding='utf-8')
            dl._RECEIVED.clear()
            got = dl.check_file('practices/received.md')[1]
            own = dl.check_file('practices/own.md')[1]
            cases.append(('control: with no MANIFEST.json the line is flagged', bool(before)))
            cases.append(('a practice received from another source is not flagged', got == []))
            cases.append(('a repo-local practice still is', bool(own)))
    finally:
        dl.ROOT = saved_root
        dl._RECEIVED[:] = saved_cache
    failed = [n for n, ok in cases if not ok]
    check(f'{name} ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_link_anchors_resolve():
    """A link's #fragment is checked against the target's real headings.

    An anchor breaks more quietly than a path: edit a heading and every
    link into it silently lands at the top of the right document instead of
    at a 404, so no reader ever reports it. Nine were dead in this repo
    when the check was written (2026-09-06) -- six headings simply reworded
    since, two pointing at an `INSTALL.md` section number that no longer
    exists, one at a heading amended in place.

    The slug rule is GitHub's, and the case that catches a naive
    implementation is a dash set off by spaces: the dash is deleted and
    BOTH its spaces survive as hyphens, so `cost — the numbers` is
    `cost--the-numbers`. Getting that wrong invents a failure on a heading
    that is perfectly fine. The setext case is pinned in the other
    direction: a heading style this does not parse must read as "cannot
    tell", never as "the anchor is missing"."""
    import importlib.util, tempfile
    spec = importlib.util.spec_from_file_location(
        '_dl_anchor', ROOT / 'tools' / 'doc_lint.py')
    dl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dl)

    slugs = [
        ('a plain heading', 'The supporting moves', 'the-supporting-moves'),
        ('a spaced dash leaves both its spaces',
         'What it cost — the numbers', 'what-it-cost--the-numbers'),
        ('punctuation is dropped, not replaced',
         'Precedence, and the one case', 'precedence-and-the-one-case'),
        ('a parenthetical keeps its words',
         'Why this could not run (original reasoning, relaxed 2026-09-01)',
         'why-this-could-not-run-original-reasoning-relaxed-2026-09-01'),
        ('inline code and links contribute their text only',
         'Run `tools/x.py` per [the plan](PLAN.md)',
         'run-toolsxpy-per-the-plan'),
    ]
    bad = [n for n, h, want in slugs if dl.heading_slug(h) != want]
    for n in bad:
        h, want = next((h, w) for nm, h, w in slugs if nm == n)
        print(f"  anchor slug wrong for {n}: {dl.heading_slug(h)!r} != {want!r}")
    check(f'doc_lint computes GitHub\'s heading anchors ({len(slugs)} stated '
          f'cases, including the spaced dash that yields a double hyphen)',
          not bad)

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / 'target.md').write_text(
            '# Top\n\n## What it cost — the numbers\n\n## Dup\n\n## Dup\n')
        (d / 'src.md').write_text(
            '# Src\n\n'
            '[ok](target.md#what-it-cost--the-numbers)\n'
            '[ok2](target.md#dup-1)\n'
            '[ok-self](#src)\n'
            '[dead](target.md#what-it-cost-the-numbers)\n'
            '[dead-self](#no-such-thing)\n')
        (d / 'setext.md').write_text('Underlined Title\n================\n')
        (d / 'into-setext.md').write_text(
            '# S\n\n[unknowable](setext.md#underlined-title)\n')
        old_root = dl.ROOT
        try:
            dl.ROOT = d
            dl._anchor_cache.clear()
            found = {t for _i, t, _w in dl.check_broken_links('src.md')}
            unknowable = dl.check_broken_links('into-setext.md')
        finally:
            dl.ROOT = old_root
            dl._anchor_cache.clear()

    check('a live anchor, a de-duplicated one (`#dup-1`) and a same-file '
          'anchor all resolve; a reworded one and a missing same-file one '
          'are both caught',
          found == {'target.md#what-it-cost-the-numbers', '#no-such-thing'},
          f'flagged {sorted(found)}')
    check('an anchor into a setext-headed document reads as "cannot tell", '
          'not as a missing anchor', not unknowable,
          f'flagged {unknowable}')


def check_update_vendors_reports_live_pre_staging_mentions():
    """Once origin has no pre-staging, Update Vendors still reports each
    line of a repository's own Markdown that names it as more than history
    (tools/migration_retire_pre_staging.py, _live_markdown): until
    2026-10-18 every Markdown read sat behind "origin still has
    pre-staging", so precedent-shared-ladder kept push-directly's "Booked
    lands on pre-staging" unseen. What counts as history is shared with the
    reword: a retired practice, a finished document (DOCUMENT_DONE_STATUSES)
    and a sentence a date closes as well as one a date opens."""
    import tempfile, contextlib, io
    name = 'Update Vendors reports live pre-staging mentions with no pre-staging left'
    if not (ROOT / 'tools' / 'migration_retire_pre_staging.py').exists():
        not_applicable(name, 'tools/migration_retire_pre_staging.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as _pu
        import migration_retire_pre_staging as m
    finally:
        sys.path.pop(0)
    m.pu = _pu
    cases = []
    text = ('Sessions opened a PR into pre-staging, which\n'
            'ended on 2026-10-14.\n\n'
            '- Open a PR into pre-staging\n'
            '- 2026-10-01: a note.\n')
    new, changed, left = m.reword_pre_staging(text, None)
    cases.append(('a sentence a date closes is history on its earlier lines',
                  new.startswith('Sessions opened a PR into pre-staging, which')
                  and (1, 'dated sentence, history') in left, str(left)))
    cases.append(('a list item above a dated item is its own sentence, and '
                  'still reworded', '- Open a PR into staging' in new
                  and (4, 'instruction') in changed, str(changed)))
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        files = {
            'docs/a.md': 'Booked lands on pre-staging.\n',
            'practices/old.md': ('---\nstatus:      retired\n---\n'
                                 'Push it to pre-staging.\n'),
            'spec/DONE.md': ('---\nkind:          proposal\nstatus:        executed\n'
                             '---\nPush it to pre-staging.\n'),
            'spec/LIVE.md': ('---\nkind:          proposal\nstatus:        accepted\n'
                             '---\nPush it to pre-staging.\n'),
            # A shared set copied in (2026-10-19): a mirror, not this
            # repository's wording.
            'process/zz-copied/practices/zz.md': 'Push it to pre-staging.\n',
            'precedent.json': json.dumps({'sources': [
                {'level': 'shared', 'name': 'zz-copied',
                 'path': 'process/zz-copied', 'vendored': True}]}),
        }
        for rel, body in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(body, encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)

        def run(ladder):
            saved = m.pb.ladder_in_force
            m.pb.ladder_in_force = lambda _r: ladder
            try:
                rep = _pu.Report()
                rep.before = set()
                with contextlib.redirect_stdout(io.StringIO()):
                    m._live_markdown(repo, rep)
                return rep
            finally:
                m.pb.ladder_in_force = saved

        rep = run(True)
        said = rep.left[0][1] if len(rep.left) == 1 else ''
        cases.append(('on the ladder, a live line is reported as file:line',
                      rep.left[:1] and rep.left[0][0] == 'Markdown naming pre-staging'
                      and 'docs/a.md:1' in said and 'spec/LIVE.md:5' in said,
                      str(rep.left)))
        cases.append(('a retired practice and an executed spec are history, '
                      'not reported', 'practices/old.md' not in said
                      and 'spec/DONE.md' not in said, said))
        cases.append(('a shared set copied into the repository is a mirror, '
                      'not reported', 'process/zz-copied' not in said, said))
        cases.append(('nothing is rewritten',
                      all((repo / rel).read_text(encoding='utf-8') == body
                          for rel, body in files.items())))
        rep = run(False)
        cases.append(('off the ladder, nothing is said', not rep.left, str(rep.left)))
    import inspect
    src = inspect.getsource(m.migrate)
    cases.append(('migrate() runs it only when the retirement step did not read '
                  'the Markdown this run', 'if HEADER not in rep.migration_notes:'
                  in src and '_live_markdown(repo, rep)' in src, src))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))

def check_update_vendors_replaces_the_old_landing_comment():
    """precedent.json's `_landing_branch_comment` in the engine's former
    words, which describe pre-staging, is replaced by the current words
    whether or not this run switched `landing_branch` and whether or not
    origin still has pre-staging (tools/migration_retire_pre_staging.py,
    _landing_comment). On 2026-10-18 precedent-shared-writing, already on
    staging and with no pre-staging left, kept the old words after its
    Update Vendors: the only look at the comment sat behind both. A comment
    somebody wrote is never rewritten: one that reads as history is left
    quietly, any other that names pre-staging is reported on every run, and
    so is any comment anywhere in the repository's own JSON
    (_json_comments): the Markdown reword never read JSON."""
    import tempfile, json as _json
    name = 'Update Vendors replaces the engine\'s old landing comment'
    if not (ROOT / 'tools' / 'migration_retire_pre_staging.py').exists():
        not_applicable(name, 'tools/migration_retire_pre_staging.py is absent')
        return
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_update as _pu
        import migration_retire_pre_staging as m
        import precedent_branches as _pb
    finally:
        sys.path.pop(0)
    m.pu = _pu
    old, old_staging = m.FORMER_LANDING_COMMENTS
    cases = []
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td)
        pj = repo / 'precedent.json'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        pj.write_text('{}\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', 'precedent.json'], check=True)

        def write(landing, comment, extra='"sources": {"a": "b"}'):
            body = ('{\n  ' + extra + ',\n  "landing_branch": '
                    + _json.dumps(landing) + ',\n  "_landing_branch_comment": [\n'
                    + ',\n'.join('    ' + _json.dumps(l) for l in comment)
                    + '\n  ],\n  "after": 1\n}\n')
            pj.write_text(body, encoding='utf-8')
            return body

        def run(before=()):
            import contextlib, io
            rep = _pu.Report()
            rep.before = set(before)
            with contextlib.redirect_stdout(io.StringIO()):
                m._json_comments(repo, rep, m._landing_comment(repo, rep))
            return rep

        current = write('staging', _pb.REPO_LANDING_COMMENT)
        body = write('staging', old)
        rep = run()
        cases.append(('not switched, no pre-staging anywhere: the old engine '
                      'wording is replaced by the current one, every other '
                      'byte kept', pj.read_text(encoding='utf-8') == current,
                      pj.read_text(encoding='utf-8')))
        cases.append(('it says so in one line, and leaves nothing',
                      len(rep.steps) == 1 and rep.steps[0][0] == 'precedent.json'
                      and not rep.left, str(rep.steps + rep.left)))
        rep = run()
        cases.append(('a second run changes nothing and says nothing',
                      pj.read_text(encoding='utf-8') == current
                      and not rep.steps and not rep.left,
                      str(rep.steps + rep.left)))
        write('staging', old_staging)
        run()
        cases.append(('the old staging wording, which names retire_pre_staging, '
                      'is replaced too', pj.read_text(encoding='utf-8') == current))
        said = ' '.join(old).split()
        rewrapped = [' '.join(said[:10]), ' '.join(said[10:])]
        write('staging', rewrapped)
        run()
        cases.append(('rewrapped, it is still the engine\'s words, and replaced',
                      pj.read_text(encoding='utf-8') == current))
        for label, comment in (
                ('a comment that does not name pre-staging',
                 ['Work lands on staging here.']),
                ('a comment that names pre-staging as history',
                 ['Booked lands on staging (pre-staging, the tier below it,',
                  'was retired on 2026-10-14).'])):
            body = write('staging', comment)
            rep = run()
            cases.append((f'{label}: untouched, and nothing said',
                          pj.read_text(encoding='utf-8') == body
                          and not rep.steps and not rep.left,
                          str(rep.steps + rep.left)))
        for label, landing, comment, before, says in (
                ('a comment somebody wrote that still sends work to pre-staging',
                 'staging', ['Work lands on pre-staging here.'], (),
                 'precedent.json _landing_branch_comment'),
                ('the engine\'s old wording under a landing branch it does not '
                 'describe', 'main', old, (), 'is not staging'),
                ('the engine\'s old wording in a precedent.json with '
                 'uncommitted edits', 'staging', old, ('precedent.json',),
                 'uncommitted')):
            body = write(landing, comment)
            rep = run(before)
            cases.append((f'{label}: untouched, and reported',
                          pj.read_text(encoding='utf-8') == body
                          and not rep.steps and len(rep.left) == 1
                          and rep.left[0][0] in ('precedent.json _landing_branch_comment',
                                                 'JSON comments naming pre-staging')
                          and says in rep.left[0][1],
                          str(rep.steps + rep.left)))
        pj.write_text('{"landing_branch": "staging"}\n', encoding='utf-8')
        rep = run()
        cases.append(('no comment at all: nothing said',
                      not rep.steps and not rep.left))
        # Every comment in the repository's own JSON, at any depth.
        (repo / 'tools').mkdir()
        files = {
            'approvers.json': {'x': {'_comment': 'Push it to pre-staging.'},
                               'note': 'push it to pre-staging'},
            'other.json': {'_a_comment': ['Booked lands on staging (pre-staging',
                                          'was retired on 2026-10-14).']},
            'tools/engine.json': {'_comment': 'Push it to pre-staging.'},
            'tools/ENGINE_MANIFEST.json': {'files': ['engine.json']},
        }
        for rel, data in files.items():
            (repo / rel).write_text(_json.dumps(data), encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        before = {rel: (repo / rel).read_text(encoding='utf-8') for rel in files}
        rep = run()
        said = rep.left[0][1] if len(rep.left) == 1 else ''
        cases.append(('a nested comment in another of its JSON files that '
                      'sends work to pre-staging is reported as file and key, '
                      'and nothing is rewritten',
                      rep.left[:1] and rep.left[0][0] == 'JSON comments naming pre-staging'
                      and said.endswith(': approvers.json x._comment')
                      and all((repo / rel).read_text(encoding='utf-8') == t
                              for rel, t in before.items()), str(rep.left)))
        cases.append(('a field that is no comment, a comment that is history, '
                      'and the engine\'s own JSON are not reported',
                      'note' not in said and 'other.json' not in said
                      and 'tools/engine.json' not in said, said))
    # Run by migrate() itself, after the retirement step and outside its
    # "origin still has pre-staging" gate.
    import inspect
    src = inspect.getsource(m.migrate)
    cases.append(('migrate() runs it after _retire, ungated',
                  0 <= src.find('_retire(repo, rep)')
                  < src.find('_landing_comment(repo, rep)'), src))
    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'{name} ({len(cases)} stated cases)', not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_templates_point_at_gotchas_rather_than_inline_them():
    """The shipped AGENTS templates point at gotchas/ and carry no trap
    inline, and an install seeds the catalogue they point to (very deep
    check 2026-09-21 B1, fixed 2026-09-28): resident environment-gotchas
    rules the catalogue out of the instructions file, and the templates
    taught every new consumer to inline it. Discriminating case: the old
    templates' inline stale-checkout entry, which the gotcha check's own
    section parser reads as an entry."""
    import shutil, tempfile
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_install as pi
    import precedent_check as pc
    cases = []
    for rel in ('templates/AGENTS.md.loader.template',
                'templates/AGENTS.md.template',
                'templates/document-project/AGENTS.md'):
        text = (ROOT / rel).read_text(encoding='utf-8')
        m = pc.GOTCHA_HEADING_RE.search(text)
        body = text[m.end():] if m else ''
        body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
        body = body[:re.search(r'^#{1,4}\s', body, re.M).start()] \
            if re.search(r'^#{1,4}\s', body, re.M) else body
        cases.append((f'{rel} points at gotchas/ and inlines no trap',
                      m is not None and 'gotchas/' in body
                      and 'stale enough to look complete' not in body,
                      body[:200]))
    seeds = [k for k in pi.ROOT_FILES if k.startswith('gotchas/gotcha-')]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='gotcha-seed-'))
    try:
        for k in seeds:
            (tmp / k).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pi.TEMPLATES / pi.ROOT_FILES[k], tmp / k)
        got = pc._read_gotcha_files(tmp) or []
        ok = [g for g in got if g[1] == 'live' and g[2]
              and g[3] >= pc.STORY_MIN_WORDS and g[4] >= pc.STORY_MIN_SENTENCES]
        cases.append(('an install seeds a live gotcha with a symptom and a '
                      'story', bool(seeds) and len(ok) == len(seeds),
                      repr(got)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the shipped templates point at gotchas/ and an install seeds it '
          f'({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:300]}" for n, d in bad))


def check_public_tree_bakes_in_no_owner_account():
    """No EXECUTABLE tracked file in a `visibility: public` repo carries a
    private owner's account (practice: scrub-gate, source-naming).

    THE INCIDENT (2026-09-10). INSTALL.md section 8 states that no tracked
    file names the account owning the private practice sets -- that is the
    entire reason PRECEDENT_SOURCE_BASE_URL is an environment variable. It
    was true of the three shared sets and false of the individual one: this
    repo's tracked `.claude/hooks/precedent-individual-bootstrap.sh` carried
    a full `https://github.com/<account>/precedent-individual`, on a public
    branch, five lines below its own comment saying a public consumer should
    bake in no URL. The leak gate could not catch it -- the repo-reference
    allowlist that exists for exactly this is inert until an owner is
    declared private-by-default, and it prints that on every run and passes.

    SCOPED TO CODE, DELIBERATELY, and this is the whole judgment in the
    check. The same account appears ~99 more times in this repo's prose --
    TODO entries, spec documents, decision records -- and those are the
    project's own history, where naming which repository an incident
    happened in IS the value. Scrubbing them buys nothing (the account is
    already published, and a private repo answers 404 to a stranger
    regardless) and costs the record its legibility. What a check can
    usefully hold is the narrower line: a file that RUNS must not hard-code
    an account, because that is the copy every adopting repo instantiates
    and republishes as its own.
    """
    import json as _json

    PLACEHOLDER_ACCOUNTS = {'example', 'acct', 'owner', 'your-account',
                            'your-github-account', 'octocat', 'user'}

    try:
        cfg = _json.loads((ROOT / 'precedent.json').read_text(encoding='utf-8'))
    except Exception:
        cfg = {}
    if (cfg.get('visibility') or 'public').lower() != 'public':
        check('a public repo bakes no owner account into a file that runs',
              True, '', skipped='this repo does not declare visibility: public')
        return

    declared = set()
    for src in cfg.get('sources', []) or []:
        n = str(src.get('name') or '')
        if n:
            declared.add(n)
    declared.add('precedent-individual')

    # Any https://<host>/<account>/<a declared set name> in an executable
    # tracked file. Built from the DECLARED names rather than a literal
    # account, so the check itself names nobody and keeps working if the
    # account changes.
    pat = re.compile(r'https?://[^/\s"\']+/([A-Za-z0-9_.-]+)/(' +
                     '|'.join(re.escape(n) for n in sorted(declared)) + r')\b')
    offenders = []
    r = subprocess.run(['git', '-C', str(ROOT), 'ls-files'],
                       capture_output=True, text=True)
    for rel in r.stdout.splitlines():
        if not rel:
            continue
        if not (rel.endswith('.sh') or rel.endswith('.py')
                or rel.endswith('.sh.template') or rel.endswith('.yml')):
            continue
        f = ROOT / rel
        try:
            text = f.read_text(encoding='utf-8')
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            # A comment naming the shape is documentation, not a baked-in
            # value; what matters is a line that ASSIGNS or executes one.
            if stripped.startswith('#'):
                continue
            m = pat.search(line)
            # `example` and friends are the reserved placeholder accounts --
            # a fixture URL is the check's own first false positive, found
            # on its first run. Keep the list SHORT and literal: a broad
            # "looks like a placeholder" rule is how a real account that
            # happens to read like one walks straight through.
            if m and m.group(1).lower() in PLACEHOLDER_ACCOUNTS:
                continue
            if m and '{{' not in m.group(0):
                offenders.append(f'{rel}:{line_no}: names an account before '
                                 f'{m.group(2)}')

    check(f'a public repo bakes no owner account into a file that runs '
          f'({len(declared)} declared set name(s) checked across every '
          f'tracked .sh/.py/.yml)',
          not offenders,
          '; '.join(offenders[:5]) if offenders else '')


def check_update_leftovers_installs_and_stamps():
    """Four engine answers a consumer's landings depended on, 2026-10-15:

      * an update lists, as LEFT FOR YOU, every file still naming a check
        script the sync removed (removed_links_step) -- it only printed
        them, and the landing was refused for each;
      * the one install call retries pip's PEP 668 refusal
        (precedent_python.pip_install), which the push check's own copy
        did not;
      * a build code can hash a source without its header stamp
        (doc_lifecycle.without_header_stamp), so a commit-time restamp
        does not make every artifact built from it stale;
      * synced_copies names the single files a manifest keeps in step with
        upstream, which a commit-time fixer must not stamp;
      * build_views knows a consumer by its materialized MANIFEST.json, as
        the sync does, so a view the sync never writes is not drift.
    -> (ok, detail, failure)."""
    import json, shutil, subprocess as sp_, tempfile, types
    import precedent_update as pu
    import precedent_python as ppy
    import doc_lifecycle as dl
    import precedent_resolve as pr_
    cases = []

    rep = types.SimpleNamespace(left=[])
    rep.leave = lambda what, why: rep.left.append((what, why))
    pu.removed_links_step(rep, (
        'precedent_sync_views: local/practices/x.md:11 still names '
        'tools/checks/check_gone.py, which this sync removed -- repoint or '
        'remove it\n'))
    cases.append(('a mention of a removed check script is left for the person',
                  [w for w, _ in rep.left] == ['local/practices/x.md:11']
                  and 'check_gone.py' in rep.left[0][1], repr(rep.left)))

    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        if '--break-system-packages' in cmd:
            return sp_.CompletedProcess(cmd, 0, '', '')
        return sp_.CompletedProcess(cmd, 1, '', 'error: externally-managed-environment')
    real = ppy.subprocess.run
    ppy.subprocess.run = fake_run
    try:
        r = ppy.pip_install('python3', ['somepkg'])
    finally:
        ppy.subprocess.run = real
    cases.append(('a PEP 668 refusal is retried with --break-system-packages',
                  r.returncode == 0 and len(calls) == 2
                  and calls[1][-1] == '--break-system-packages', repr(calls)))

    a = ('<!-- Last updated: 2026-10-15 20:00:00 (Buenos Aires) by Morgan F, '
         'to version 3 -->\n# Title\nbody\n')
    b = a.replace('20:00:00', '21:30:00').replace('version 3', 'version 4')
    cases.append(('two stamps on the same text hash the same',
                  dl.without_header_stamp(a) == dl.without_header_stamp(b)
                  == '# Title\nbody\n', repr(dl.without_header_stamp(a))))
    quoted = '# Title\n<!-- Last updated: quoted further down -->\n'
    cases.append(('only a first-line stamp is taken out',
                  dl.without_header_stamp(quoted) == quoted, ''))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-synced-'))
    try:
        (tmp / 'process').mkdir()
        (tmp / 'process' / 'manifest.json').write_text(json.dumps({'entries': [
            {'local_path': 'GETTING_STARTED.md', 'status': 'synced'},
            {'local_path': 'AGENTS.md', 'granularity': 'section', 'status': 'synced'},
            {'local_path': 'NOTES.md', 'status': 'diverged'}]}), encoding='utf-8')
        (tmp / 'process' / 'manifest_pack.json').write_text(json.dumps({'entries': [
            {'local_path': 'pack/README.md', 'granularity': 'file'}]}), encoding='utf-8')
        got = pr_.synced_copies(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cases.append(('synced_copies names whole-file synced entries, in every manifest',
                  got == {'GETTING_STARTED.md', 'pack/README.md'}, repr(sorted(got))))

    import build_views as bv_
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-consumer-'))
    try:
        (tmp / 'MANIFEST.json').write_text(json.dumps(
            {'generated_by': 'tools/precedent_materialize.py'}), encoding='utf-8')
        materialized = bv_.repo_is_consumer(tmp)
        (tmp / 'tools').mkdir()
        (tmp / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            json.dumps({'kind': 'source'}), encoding='utf-8')
        declared_source = bv_.repo_is_consumer(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cases.append(('a repository with a materialized MANIFEST.json is a consumer, '
                  'unless its engine manifest says otherwise',
                  materialized and not declared_source,
                  f'{materialized} {declared_source}'))

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    return (not bad, f'{len(cases)} stated cases',
            '; '.join(f'{n} -- {d[:400]}' for n, d in bad))


