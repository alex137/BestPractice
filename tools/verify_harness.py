#!/usr/bin/env python3
"""verify_harness.py — phase-1 verification harness for the practice-engine
conversion (PRACTICE_ENGINE_PLAN.md, "The Verification Harness" and Sequence
row 1: "Practices are files; the catalogue regenerates byte-identically;
harness passes.").

Only the checks that are meaningful with no loader and no resident-tier
curation yet (both phase 2) actually run. The two the plan lists that
depend on those — resident subset, behavioral replay — are reported as
NOT YET APPLICABLE rather than skipped silently, so their absence stays
visible instead of reading as a pass.

Run:  python3 tools/verify_harness.py
Exit: 0 if every applicable check passes, 1 otherwise.
"""
import collections, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
CATALOGUE = ROOT / 'PRACTICES.md'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import precedent_paths as pp
# build_views is imported for its pure helpers only (_json_str,
# INDEX_CLAUSE_MAX). check_generated_views_regenerate still shells out to it
# as a SUBPROCESS on purpose: build_loader_block() calls sys.exit() when the
# resident block is over budget, and an in-process call would turn that into
# an uncaught SystemExit taking the whole harness down instead of a FAIL
# line. Keep it that way -- import helpers, run the build out-of-process.
import build_views as bv

FAILED = []
PASSED = []
NA = []


def check(name, ok, detail=''):
    (PASSED if ok else FAILED).append((name, detail))
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" -- {detail}" if detail and not ok else ""))


def not_applicable(name, reason):
    NA.append((name, reason))
    print(f"N/A:  {name} -- {reason}")


def load_practice_files():
    out = {}
    broken = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            broken.append(str(e))
            continue
        out[f.stem] = (fm, sections, f)
    if broken:
        # A malformed practice file used to abort the whole harness with a
        # bare AssertionError traceback that did not name the file. Report
        # it as a failed check, like everything else here, and keep going so
        # the rest of the run still tells you what else is wrong.
        for msg in broken:
            print(f"  {msg}")
        check('every practices/*.md file parses', False,
              f"{len(broken)} unparseable practice file(s)")
    else:
        check('every practices/*.md file parses', True)
    return out


def check_slug_set(files):
    ok = True
    for stem, (fm, sections, f) in files.items():
        slug = fm.get('slug', '')
        if slug != stem:
            ok = False
            print(f"  slug mismatch: {f.name} frontmatter slug={slug!r} != filename")
    slugs = [fm['slug'] for fm, _, _ in files.values()]
    dupes = [s for s, n in collections.Counter(slugs).items() if n > 1]
    if dupes:
        ok = False
        print(f"  duplicate slugs: {dupes}")
    check('slug-set equality (filename == frontmatter slug, all unique)', ok)


def check_source_coverage(files, original_practices_by_number):
    """The plan's actual slug-set requirement: "the same practices are in
    effect, by slug." check_slug_set only proves each FILE is internally
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
            # it is not part of the migrated set this check is about
            continue
        by_number.setdefault(num, []).append(stem)

    for num in sorted(original_practices_by_number, key=int):
        if num not in by_number:
            ok = False
            print(f"  practice {num} ({original_practices_by_number[num]['title']!r}) is in "
                  f"PRACTICES.md but has NO file in practices/ -- a practice was dropped")
    for num, stems in sorted(by_number.items(), key=lambda kv: int(kv[0])):
        if num not in original_practices_by_number:
            ok = False
            print(f"  practices/{stems[0]}.md claims source_practice_number {num}, which "
                  f"is not in PRACTICES.md")
        elif len(stems) > 1:
            ok = False
            print(f"  practice {num} is claimed by {len(stems)} files: {stems}")
    check(f'source coverage (every one of the {len(original_practices_by_number)} practices in '
          f'PRACTICES.md has exactly one file, and vice versa)', ok)


def check_titles_match_source(files, original_practices_by_number):
    """A practice's title is what MAP.md shows and what a person reads to
    decide whether to open it -- and it was entirely unchecked. Every title
    in the catalogue could have been rewritten with the harness green."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        orig = original_practices_by_number.get(fm.get('source_practice_number'))
        if orig is None:
            continue
        if fm.get('title', '').strip() != orig['title'].strip():
            ok = False
            print(f"  {f.name}: title differs from PRACTICES.md\n"
                  f"      file:   {fm.get('title','')!r}\n"
                  f"      source: {orig['title']!r}")
    check('titles match the source catalogue exactly', ok)


def check_checked_by_targets_exist(files):
    """The plan: "a `checked_by` naming a script with no test for it fails
    the audit." Testing that the check has a test is phase 5; testing that
    the script EXISTS is free, and a checked_by pointing at a deleted or
    renamed script is a practice that silently claims enforcement it does
    not have."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        raw = fm.get('checked_by', 'null').strip()
        if raw in ('null', ''):
            continue
        target = raw.strip('"')
        if not (ROOT / target).exists():
            ok = False
            print(f"  {f.name}: checked_by names {target!r}, which does not exist -- "
                  f"the practice claims enforcement it does not have")
    check('every checked_by names a script that exists', ok)


def check_reachability(files):
    ok = True
    for stem, (fm, sections, f) in files.items():
        if fm.get('tier') != 'on-demand':
            continue
        checked_by = fm.get('checked_by', 'null')
        applies_to = fm.get('applies_to', '[]')
        occasion = fm.get('occasion', '""')
        has_checked_by = checked_by not in ('null', '')
        has_narrow_applies = applies_to not in ('[]', '["**"]', '')
        has_occasion = occasion not in ('""', "''", '')
        if not (has_checked_by or has_narrow_applies or has_occasion):
            ok = False
            print(f"  UNREACHABLE: {f.name} (slug={stem}) has no checked_by, "
                  f"no narrower-than-** applies_to, and no occasion")
    check('reachability (every on-demand practice has checked_by / narrow applies_to / occasion)', ok)


# ---------------------------------------------------------------------------
# RETIRED: byte-identical regeneration.
#
# Phase 1's converter was mechanical -- it routed each paragraph by the bold
# label that opened it -- so the catalogue could be rebuilt from practices/
# and diffed against PRACTICES.md byte for byte. That was the right proof for
# a mechanical conversion, and it held: 52 practices, no unexplained
# difference, modulo three documented source quirks.
#
# It cannot survive the phase-1.5 editorial re-split, and not because the
# re-split is unfaithful. Re-homing a paragraph from Rule to Why moves where
# cmd_build re-emits the "**Why.**" label, so the rebuilt catalogue differs
# from the source however faithful the move was. A check that fails on
# correct work is worse than no check: it gets suppressed, and then it is not
# there when something is actually wrong.
#
# Its two claims are both still checked, by name, and one of them more
# strongly than before:
#
#   CONTENT  -> check_content_preserved_by_sentence. Byte-identical compared
#               a reassembly; this compares every sentence of every practice
#               against PRACTICES.md directly, in both directions. It is
#               strictly stronger: a single word reworded inside a Rule
#               passes both word-multiset checks (the reworded word can
#               lowercase to the same token) and fails this one.
#   ORDERING -> check_section_source_order. Text may be re-homed between
#               sections; within a section it must still appear in its
#               original source order.
#
# Plus check_no_lost_content, check_list_structure_preserved and
# check_corruption_drop_is_a_duplicate, none of which existed when
# byte-identical was the whole story.
#
# tools/split_practices.py build still renders a catalogue view and
# `build --diff` still runs -- but its diff is now expected output showing
# the editorial re-split, not a defect report.

# ---------------------------------------------------------------------------
# Content preservation across an EDITORIAL re-split.
#
# Phase 1's converter was mechanical, so "byte-identical regeneration" could
# prove it lost nothing: rebuild PRACTICES.md from practices/ and diff. That
# check cannot survive the phase-1.5 editorial pass, by construction -- the
# whole point of that pass is that text MOVES between sections, so the
# rebuilt catalogue's **Why.** label lands somewhere else and the diff is
# non-empty no matter how faithful the move was.
#
# It is replaced by something stronger on the dimension that actually
# matters, and weaker only on one that does not. The plan's own rule for the
# converter is a SENTENCE rule -- "no sentence may appear in the output that
# does not appear in the input" (Migration, The Converter) -- so that is what
# is checked, in both directions, against PRACTICES.md itself. PRACTICES.md
# is the immutable upstream source and stays in the repo, so this is a
# permanent, non-circular guarantee that survives any future re-split:
# whatever the sections end up being, their combined content is exactly
# BestPractice's content, sentence for sentence.
#
# What is lost is the ORDERING claim byte-identical regeneration also made,
# and check_section_source_order restores it: within each section, sentences
# must still appear in their original relative source order. Any pure
# re-homing preserves that; scrambling does not.
_PARA_SPLIT = re.compile(r'\n\s*\n')
_SENT_SPLIT = re.compile(r'(?<=[.!?])[ \t]+(?=[A-Z0-9*\[(“"`—-])')


def _sentences(text):
    """Sentence-ish chunks, whitespace-normalized. Deliberately the SAME
    tokenizer on both sides of every comparison, so an imperfect split (a
    trailing "e.g." swallowing the next sentence, say) is symmetric and
    harmless: it just makes the compared chunk bigger. The only way it
    misfires is if an edit splits text *inside* a chunk the tokenizer
    merged -- which fails the check rather than passing it, i.e. it fails
    closed, which is the direction to be wrong in."""
    out = []
    for para in _PARA_SPLIT.split(text or ''):
        para = ' '.join(para.split())
        if not para:
            continue
        out.extend(s for s in (x.strip() for x in _SENT_SPLIT.split(para)) if s)
    return out


def _source_sentences(orig):
    return _sentences(orig['rule']) + _sentences(orig['why']) + _sentences(orig['install'])


SECTION_ORDER = ('rule', 'why', 'story', 'install')


def _output_sentences_by_section(sections):
    return [(name, _sentences(sections.get(name, ''))) for name in SECTION_ORDER]


def check_content_preserved_by_sentence(files, original_practices_by_number):
    """Every sentence of every practice, exactly as BestPractice wrote it,
    exactly as many times, distributed across Rule/Why/Story/Install however
    the editorial split decided. Nothing invented, nothing lost, nothing
    duplicated -- at sentence granularity rather than word granularity."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
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
    check('content preserved sentence-for-sentence (Rule+Why+Story+Install == the '
          'source practice, both directions)', ok)


def check_section_source_order(files, original_practices_by_number):
    """Text may be re-homed between sections; it may not be scrambled.
    Within each section, sentences must appear in the same relative order
    they had in PRACTICES.md. This is what byte-identical regeneration used
    to guarantee, kept alive after that check could no longer run."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
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


_LIST_ITEM_RE = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.*)$')


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


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")


def _tokens(text):
    return collections.Counter(w.lower() for w in WORD_RE.findall(text))


def check_no_invented_content(files, original_practices_by_number):
    ok = True
    for stem, (fm, sections, f) in files.items():
        num = fm.get('source_practice_number')
        orig = original_practices_by_number.get(num)
        if orig is None:
            ok = False
            print(f"  {f.name}: no source_practice_number {num!r} found in PRACTICES.md")
            continue
        orig_body = orig['rule'] + ' ' + orig['why'] + ' ' + orig['install']
        out_body = (sections.get('rule', '') + ' ' + sections.get('why', '') + ' '
                    + sections.get('install', ''))
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


CITATION_RE = re.compile(r'\bpractice\s+(\d+)\b', re.IGNORECASE)


def check_no_lost_content(files, original_practices_by_number):
    """The mirror of check_no_invented_content, and the reason it has to
    exist: that check is a SUBSET test (output <= source), so a conversion
    that silently DELETES authored text passes it trivially. Both
    directions together make it a multiset EQUALITY, which -- combined with
    byte-identical regeneration, which pins order -- is a far stronger
    statement than either alone."""
    ok = True
    for stem, (fm, sections, f) in files.items():
        num = fm.get('source_practice_number')
        orig = original_practices_by_number.get(num)
        if orig is None:
            continue  # already reported by check_no_invented_content
        orig_body = orig['rule'] + ' ' + orig['why'] + ' ' + orig['install']
        out_body = (sections.get('rule', '') + ' ' + sections.get('why', '') + ' '
                    + sections.get('story', '') + ' ' + sections.get('install', ''))
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


# How many consecutive identical non-blank lines, shared between two
# different practices, count as duplication rather than coincidence. Three
# is comfortably clear of any real overlap in this catalogue: across all 52
# practices the ONLY pair that trips it is the one real corruption, and the
# runner-up shares nothing at all. Practices legitimately quote each other's
# names and cite each other by number; they do not share paragraphs.
DUPLICATE_RUN_LINES = 3


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
            windows[tuple(lines[i:i + min_run])].append((name, i))
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

    named = [(stem, _body_lines(
        sections.get('rule', '') + '\n' + sections.get('why', '') + '\n'
        + sections.get('story', '') + '\n' + sections.get('install', '')))
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


def check_citation_integrity(files):
    valid_numbers = {fm['source_practice_number'] for fm, _, _ in files.values()}
    ok = True
    for stem, (fm, sections, f) in files.items():
        text = f.read_text(encoding='utf-8')
        for m in CITATION_RE.finditer(text):
            if m.group(1) not in valid_numbers:
                ok = False
                print(f"  {f.name}: cites 'practice {m.group(1)}', which does not "
                      f"exist as any source_practice_number")
    check('citation integrity (every "practice N" reference resolves)', ok)


def check_leak_gate():
    """The real gate is tools/leak_gate.py, run as a subprocess. It replaces a
    stand-in that hardcoded a list of private terms -- including a personal
    email address -- INSIDE this public repo, which is the anti-pattern the
    gate exists to prevent: a blocklist of secret words, committed to a public
    repo, publishes the words it guards. Found by pointing the new gate at the
    tree and reading what it said. Fixed forward, not by rewriting published
    history (practice 31, no-rewrite-for-warnings).

    The vocabulary layer is reported as not-yet-applicable when no private
    blocklist is configured -- which is the honest state before phase 3 -- and
    the structural layer is a real pass or fail either way."""
    result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'leak_gate.py')],
                            capture_output=True, text=True)
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        check('leak gate (tools/leak_gate.py)', False,
              out.splitlines()[0] if out else 'leak_gate.py failed with no output')
        for line in out.splitlines():
            if line.startswith('LEAK:'):
                print(f"  {line}")
    elif 'leak gate PARTIAL' in out:
        check('leak gate, structural layer (no private-source paths, emails, home '
              'directories, or non-universal practice sources)', True)
        not_applicable('leak gate, vocabulary layer',
                       f'no private-term blocklist is configured ({"PRECEDENT_LEAK_BLOCKLIST"} '
                       f'is unset), and none can live in this public repo -- see '
                       f'tools/leak_gate.py --explain. Expected until phase 3 creates the '
                       f'private sets; reported rather than passed over, because a clean '
                       f'structural scan is not evidence that no private word is present')
    else:
        check('leak gate (structural and vocabulary layers)', True)


def check_index_clauses(files):
    """The occasion index is the ONLY route to 34 of the 46 on-demand
    practices, and a session decides whether to open a practice on the
    strength of one line. So that line is authored, and required.

    It used to be derived -- the Rule's first sentence, cut at 90 characters
    -- and 86% of the entries came out truncated mid-thought, one of them
    ending on a dangling colon. A routing table whose rows do not finish
    their sentence is a routing table nobody can route from, and nothing
    was checking it."""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        if fm.get('tier') != 'on-demand':
            continue
        clause = bv._json_str(fm.get('index_clause', ''))
        if not clause:
            ok = False
            print(f"  {f.name}: no index_clause -- an on-demand practice is reached "
                  f"through the occasion index, so it needs the line that gets it opened")
            continue
        if len(clause) > bv.INDEX_CLAUSE_MAX:
            ok = False
            print(f"  {f.name}: index_clause is {len(clause)} chars, over "
                  f"{bv.INDEX_CLAUSE_MAX} -- it renders on one line of a table")
        if clause.rstrip().endswith(('...', '…', ':')):
            ok = False
            print(f"  {f.name}: index_clause does not finish its thought: {clause!r}")
        if clause[:1].isupper() and not clause.startswith(('A ', 'I ')):
            ok = False
            print(f"  {f.name}: index_clause reads as a sentence, not a table cell: "
                  f"{clause!r}")
    check(f'occasion-index clauses are written, complete and under '
          f'{bv.INDEX_CLAUSE_MAX} chars', ok)


# (path, glob, expected) -- the semantics `applies_to` is written against.
# This table exists because the path-triggered channel shipped with a bare
# fnmatch.fnmatch(path, glob), under which "**/*.md" silently never matched
# a top-level file, and NOTHING in the harness noticed: the behavioral
# replay's "independent" cross-check re-derived matches with the same
# fnmatch call, so it agreed with the bug on every commit and reported 0
# misses. A cross-check against a second copy of the same rule is not a
# check. Stating the intended semantics as literal cases is.
GLOB_CASES = [
    # a root-level file is at depth zero -- "**/" must match zero segments
    ('AGENTS.md',                          '**/*.md',                          True),
    ('README.md',                          '**/*.md',                          True),
    ('docs/guide.md',                      '**/*.md',                          True),
    ('a/b/c/deep.md',                      '**/*.md',                          True),
    ('notes.txt',                          '**/*.md',                          False),
    ('docs/notes.txt',                     '**/*.md',                          False),
    # the same file, spelled three ways, must give one answer
    ('./AGENTS.md',                        '**/*.md',                          True),
    (str(ROOT / 'AGENTS.md'),              '**/*.md',                          True),
    # a single * does not cross a directory separator
    ('docs/guide.md',                      '*.md',                             False),
    ('guide.md',                           '*.md',                             True),
    ('a/b.md',                             'a/*.md',                           True),
    ('a/b/c.md',                           'a/*.md',                           False),
    ('a/b/c.md',                           'a/**/*.md',                        True),
    ('a/c.md',                             'a/**/*.md',                        True),
    # "dir/**" is everything INSIDE dir, not dir itself
    ('process/upstream/tools/x.py',        'process/upstream/**',              True),
    ('process/upstream/x.py',              'process/upstream/**',              True),
    ('process/upstream',                   'process/upstream/**',              False),
    ('process/upstreamish/x.py',           'process/upstream/**',              False),
    # a literal path is a literal path
    ('.github/pull_request_template.md',   '.github/pull_request_template.md', True),
    ('docs/.github/pull_request_template.md',
                                           '.github/pull_request_template.md', False),
    ('README.md',                          'README.md',                        True),
    ('docs/README.md',                     'README.md',                        False),
    # "**" alone matches anything (filtered out of the path channel, but the
    # matcher still has to be right about it)
    ('anything/at/all.py',                 '**',                               True),
    ('top.py',                             '**',                               True),
]


def check_glob_semantics():
    ok = True
    for path, glob, expected in GLOB_CASES:
        got = pp.path_matches(path, glob)
        if got != expected:
            ok = False
            print(f"  {path!r} vs {glob!r}: expected {expected}, got {got}")
    check(f'path-glob semantics ({len(GLOB_CASES)} stated cases: `**` crosses "/", '
          f'`*` does not, paths normalize to repo-root-relative)', ok)


def check_generated_views_regenerate():
    # "hand-editing a generated view fails a check" (Sequence row 2, done-when).
    # Runs build_views.py --check as a real subprocess, not an in-process
    # import-and-call: bv.build_loader_block() can sys.exit() (over the
    # resident token budget, or missing BEGIN/END markers), which is a clean
    # process exit but would be an uncaught SystemExit escaping straight
    # through this function if called in-process, taking the whole harness
    # down with a raw traceback instead of a reported FAIL line.
    result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'), '--check'],
                             capture_output=True, text=True)
    ok = result.returncode == 0
    detail = (result.stdout + result.stderr).strip() if not ok else ''
    check('generated views regenerate byte-identically (AGENTS.md loader block, MAP.md, GLOSSARY.md)',
          ok, detail)


def check_resident_subset(files):
    # Phase 1's always-loaded set was every practice, unconditionally (no
    # tier existed yet). The post-migration resident set must be a STRICT
    # subset of that -- i.e. fewer than all of them, and within the token
    # budget build_views.py enforces at build time (a build over budget
    # already exits nonzero there; this check additionally confirms the
    # curation actually happened rather than defaulting everything resident).
    resident = [stem for stem, (fm, _s, _f) in files.items() if fm.get('tier') == 'resident']
    ok = 0 < len(resident) < len(files)
    check('resident subset (curated resident tier is a strict, non-empty subset of all practices)',
          ok, f"{len(resident)} of {len(files)} practices are resident")


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


def main():
    if not PRACTICES_DIR.exists():
        sys.exit("verify_harness FAIL: practices/ does not exist -- run "
                 "tools/split_practices.py split first")
    files = load_practice_files()
    check_slug_set(files)
    original_text = CATALOGUE.read_text(encoding='utf-8')
    original_practices = {p['number']: p for p in sp.parse_catalogue(original_text)}
    check_source_coverage(files, original_practices)
    check_titles_match_source(files, original_practices)
    check_checked_by_targets_exist(files)
    check_reachability(files)
    check_no_invented_content(files, original_practices)
    check_no_lost_content(files, original_practices)
    check_content_preserved_by_sentence(files, original_practices)
    check_section_source_order(files, original_practices)
    check_list_structure_preserved(files, original_practices)
    check_corruption_drop_is_a_duplicate(original_practices)
    check_no_cross_practice_duplication(files, original_practices)
    check_citation_integrity(files)
    check_leak_gate()
    check_index_clauses(files)
    check_glob_semantics()
    check_generated_views_regenerate()
    check_resident_subset(files)
    check_behavioral_replay()

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    return 1 if FAILED else 0


if __name__ == '__main__':
    sys.exit(main())
