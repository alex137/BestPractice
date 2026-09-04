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
import collections, json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
AGENTS_MD = ROOT / 'AGENTS.md'
CATALOGUE = ROOT / 'PRACTICES.md'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import precedent_paths as pp
import precedent_candidate as pcand
import doc_lint as dl
# build_views is imported for its pure helpers only (_json_str,
# INDEX_CLAUSE_MAX). check_generated_views_regenerate still shells out to it
# as a SUBPROCESS on purpose: build_loader_block() calls sys.exit() when the
# resident block is over budget, and an in-process call would turn that into
# an uncaught SystemExit taking the whole harness down instead of a FAIL
# line. Keep it that way -- import helpers, run the build out-of-process.
import build_views as bv
import catalogue_stats as cs

FAILED = []
PASSED = []
NA = []

# --------------------------------------------------------------------------
# Post-conversion provenance exceptions -- both narrow and self-checking.
# --------------------------------------------------------------------------

# Practices that existed on Alex's live `main` but not in this repo's own
# PRACTICES.md at the time they were converted here (spec/PRACTICE_FORMAT.md).
# Converted independently against `main`, not against PRACTICES.md, so the
# fidelity checks below had no ancestor to compare against and had to not
# read that absence as invention. Frontmatter values come back as strings
# (see split_practices.py's own int(num) casts before comparison), so these
# are strings too.
#
# EMPTIED 2026-09-02: practice 53 (`todo-is-a-handoff`) stopped qualifying
# the moment a phase-5 pre-flight `git merge origin/main` brought main's own
# "## 53." entry into this branch's PRACTICES.md -- an ancestor now exists,
# so the fidelity checks run for real instead of skipping via this set, and
# correctly found the same unregistered citation-link edit the 2026-09-01
# sweep already exempted for the other 52 (see AMENDED_POST_CONVERSION and
# CHANGES_TO_TELL_ALEX.md's "Slug-link citation sweep" entry, updated to
# match). Left as an empty set, not deleted, because the mechanism is
# real and will be needed again the next time `main` outruns this branch.
POST_SNAPSHOT_PRACTICE_NUMBERS = set()

# Practices deliberately rewritten after phase-1 conversion -- a real edit,
# not a conversion bug -- keyed by slug.
AMENDED_POST_CONVERSION = {
    'layered-practice-packs',
    # Pre-phase-5 citation sweep, 2026-09-01 (see CHANGES_TO_TELL_ALEX.md):
    # every in-body "practice N" cross-reference converted to a [slug](slug.md)
    # link, since numbers stop meaning one fixed thing once practices can be
    # reordered, split, and retired. Listed here because a slug link is new
    # text relative to BestPractice's frozen original, so it fails the
    # word-multiset and sentence-preservation checks below on the citation
    # words alone -- the exemption covers a real, disclosed edit, not a
    # conversion bug.
    'acronyms-glossary', 'affordance-is-shared', 'build-buy-decompose',
    'capture-gate', 'check-source-architecture', 'computed-numbers-in-scripts',
    'convention-to-audit', 'deliverables-look-like-output', 'docs-track-models',
    'engine-plus-host-shims', 'environment-gotchas', 'frame-from-audience-question',
    'generated-artifact-provenance', 'index-remembers-past',
    'merge-authorization-keyword', 'merge-runbook', 'mistakes-become-rules',
    'no-rewrite-for-warnings', 'one-formatter-per-quantity',
    'outward-summary-discipline', 'parallel-artifact-ledger',
    'permutation-frontier-column', 'practice-export-loop', 'readers-vocabulary',
    'registry-source-of-truth', 'repo-is-memory', 'scripts-assert-properties',
    'scrub-gate', 'search-by-purpose', 'second-pass-capture', 'session-bootstrap',
    'tabular-shared-renderer', 'two-check-levels', 'variant-re-derives',
    'verify-decomposition', 'verify-postcondition', 'volatile-rules-carry-dates',
    # Added 2026-09-02, when a phase-5 pre-flight merge of `main` gave
    # practice 53 a real ancestor in PRACTICES.md for the first time on this
    # branch (see the POST_SNAPSHOT_PRACTICE_NUMBERS comment above) and the
    # fidelity checks found the same category of edit the rest of this set
    # already covers: three "practice N" citations converted to slug links.
    'todo-is-a-handoff',
}

CHANGES_DOC = ROOT / 'CHANGES_TO_TELL_ALEX.md'


def _amended_and_logged(slug):
    """True only if `slug` is BOTH in AMENDED_POST_CONVERSION AND actually
    named in CHANGES_TO_TELL_ALEX.md. The registry alone is not enough --
    tying the exemption to a checked property rather than a trusted list is
    the same discipline check_corruption_drop_is_a_duplicate already uses,
    so an amendment that forgets to log itself fails here instead of
    silently exempting itself from the fidelity checks below."""
    if slug not in AMENDED_POST_CONVERSION:
        return False
    if not CHANGES_DOC.exists():
        return False
    return slug in CHANGES_DOC.read_text(encoding='utf-8')


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
    the audit." Testing that the check has a test is phase 4; testing that
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


SECTION_ORDER = ('rule', 'detail', 'why', 'story', 'install')


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


def _output_sentences_by_section(sections):
    return [(name, _sentences(sections.get(name, ''))) for name in SECTION_ORDER]


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


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")


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


CROSS_PRACTICE_LINK_RE = re.compile(r'\]\(([a-z0-9]+(?:-[a-z0-9]+)*)\.md\)')
AGENTS_PRACTICE_LINK_RE = re.compile(r'\]\(practices/([a-z0-9]+(?:-[a-z0-9]+)*)\.md\)')


def check_no_bare_numeric_citations(files):
    """The pre-phase-5 citation sweep (2026-09-01, CHANGES_TO_TELL_ALEX.md)
    replaced every "practice N" cross-reference in practices/ body text with
    a [slug](slug.md) link -- numbers stop meaning one fixed thing once
    practices can be reordered, split, and retired, which this catalogue is
    now built to do. check_citation_integrity above still checks that a
    numeric citation, if one exists, resolves; this is the regression guard
    that the numeric form does not come back in body prose at all. (The
    `source_practice_number` frontmatter field is exempt by construction --
    CITATION_RE requires "practice" immediately followed by whitespace,
    which never matches the `source_practice_number:` key.)"""
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        body = _whole_body(sections)
        for m in CITATION_RE.finditer(body):
            ok = False
            print(f"  {f.name}: body text cites 'practice {m.group(1)}' by number; "
                  f"convert to a [{{slug}}]({{slug}}.md) link instead")
    # AGENTS.md is the one file every session reads at startup, and its own
    # hand-written prose (below the generated loader block) used to cite
    # practices the pre-sweep way -- "practice 12", "practice 34" -- outside
    # this check's reach, because it only ever scanned practices/*.md. Found
    # by a 2026-09-01 deep-check audit; the four citations happened to still
    # resolve correctly, which is not something to rely on going forward.
    if AGENTS_MD.exists():
        agents_text = AGENTS_MD.read_text(encoding='utf-8', errors='ignore')
        for m in CITATION_RE.finditer(agents_text):
            ok = False
            print(f"  AGENTS.md: cites 'practice {m.group(1)}' by number; "
                  f"convert to a [{{slug}}](practices/{{slug}}.md) link instead")
    check('no bare numeric citations in body text (slugs are the official reference form)', ok)


def check_slug_link_integrity(files):
    """The slug-link counterpart of check_citation_integrity: every
    [slug](slug.md)-shaped cross-reference in a practice's body text must
    resolve to a real slug in this catalogue."""
    ok = True
    valid_slugs = set(files.keys())
    for stem, (fm, sections, f) in sorted(files.items()):
        body = _whole_body(sections)
        for m in CROSS_PRACTICE_LINK_RE.finditer(body):
            if m.group(1) not in valid_slugs:
                ok = False
                print(f"  {f.name}: links to '{m.group(1)}.md', which is not a "
                      f"known practice slug")
    # AGENTS.md links to a practice as [slug](practices/slug.md) -- a
    # different href shape than practices/*.md's own sibling-relative
    # [slug](slug.md) -- so it needs its own regex, not a reuse of
    # CROSS_PRACTICE_LINK_RE above.
    if AGENTS_MD.exists():
        agents_text = AGENTS_MD.read_text(encoding='utf-8', errors='ignore')
        for m in AGENTS_PRACTICE_LINK_RE.finditer(agents_text):
            if m.group(1) not in valid_slugs:
                ok = False
                print(f"  AGENTS.md: links to 'practices/{m.group(1)}.md', "
                      f"which is not a known practice slug")
    check('slug-link citation integrity (every [slug](slug.md) cross-reference resolves)', ok)


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
                       f'tools/leak_gate.py --explain and '
                       f'templates/leak-blocklist.txt.template. This is the permanent '
                       f'state in CI, which has no access to a private list; on a '
                       f'person\'s own machine it means the layer is not switched on '
                       f'yet. Reported rather than passed over, because a clean '
                       f'structural scan is not evidence that no private word is '
                       f'present. `leak gate fires` below tests the layer either way')
    else:
        check('leak gate (structural and vocabulary layers)', True)


def check_leak_gate_fires():
    """The gate's own behaviour, as stated cases against a throwaway repo.

    WHY THIS EXISTS, AND WHY IT IS NOT A SECOND COPY OF THE GATE'S LOGIC.
    check_leak_gate() above runs the gate on this tree and reports what it
    says. That is a check on the TREE, not on the GATE -- it passes just as
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
        blocklist = tmp / 'blocklist.txt'          # OUTSIDE the repo, as required
        blocklist.write_text('zorbulon\n\\bproject[- ]nightjar\\b\n', encoding='utf-8')

        git(repo, 'init', '-q')
        git(repo, 'config', 'user.email', 'harness@example.com')
        git(repo, 'config', 'user.name', 'harness')
        (repo / 'ok.md').write_text('nothing sensitive here\n', encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'base')
        base = git(repo, 'rev-parse', 'HEAD')

        def gate(*args, blocklist_set=True):
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
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
        # case: the four FORBIDDEN_PATHS regexes had no re.I, so a
        # directory named the way a person actually types it --
        # "Team-Nightjar/", "Individual/", "Candidates/" -- passed the gate
        # silently while its lowercase spelling correctly failed.
        (repo / 'Team-Nightjar').mkdir()
        (repo / 'Team-Nightjar' / 'notes.md').write_text('clean\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'mixed-case team dir')
        cases.append(('a mixed-case forbidden path (Team-Nightjar/) fails the '
                      'same as its lowercase spelling',
                      gate('--range', f'{base}..HEAD') == 1))
        git(repo, 'reset', '-q', '--hard', base)
        shutil.rmtree(repo / 'Team-Nightjar', ignore_errors=True)

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

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  leak gate did NOT behave as stated: {name}")
        check(f'leak gate fires ({len(cases)} stated cases: blobs not the working '
              f'tree, every commit in a push, commit messages, fail-closed)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_practice_audit_fires():
    """practice_audit.py's --update-baseline, stated as cases against a
    throwaway manifest (practice: mistakes-become-rules).

    Regression case, found in the wild via a dependent repo's check-in
    (themorgan/WorkingWithAI, 2026-09-04): a 'diverged' manifest entry
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
        (repo / 'process' / 'upstream').mkdir(exist_ok=True)
        (repo / 'local').mkdir()
        (repo / 'local' / 'diverged.md').write_text('customized on purpose\n', encoding='utf-8')
        (repo / 'local' / 'synced.md').write_text('vendored as-is\n', encoding='utf-8')
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
                ],
            }, indent=2), encoding='utf-8')

        def run_update():
            r = subprocess.run(
                [sys.executable, str(tools_dir / 'practice_audit.py'),
                 '--update-baseline', '--manifest', str(manifest)],
                capture_output=True, text=True, cwd=str(repo))
            entries = json.loads(manifest.read_text(encoding='utf-8'))['entries']
            return r, {e['practice']: e for e in entries}

        write_manifest()
        before = json.loads(manifest.read_text(encoding='utf-8'))['entries']
        before_hash = {e['practice']: e['local_sha256'] for e in before}
        result, after = run_update()

        cases = [
            ("a 'diverged' entry's status is untouched by a stale-baseline "
             "re-run", after['diverged_one']['status'] == 'diverged'),
            ("a 'diverged' entry's hash IS re-baselined (the fix narrows the bug, "
             "it doesn't stop the hash update)",
             after['diverged_one']['local_sha256'] != before_hash['diverged_one']),
            ("a 'synced' entry re-baselining still stays 'synced' (unchanged "
             "behaviour)", after['synced_one']['status'] == 'synced'),
            ("the diverged re-baseline is named in the output, not silent",
             "was 'diverged'" in result.stdout),
        ]

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  practice_audit --update-baseline did NOT behave as stated: {name}")
        check(f"practice_audit --update-baseline fires ({len(cases)} stated cases: "
              f"'diverged' status survives a hash-only re-baseline)", ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
                 'universal practice the blocked team practice tries to '
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
                        {'level': 'repo-local', 'name': 'a-project-local',
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
                      == {'universal', 'team', 'individual', 'repo-local'}))
        # precedence: team > repo-local > individual > universal, on a slug
        # defined at all four
        cases.append(('team beats repo-local beats individual beats '
                      'universal on a slug defined at all four',
                      by_slug.get('shared-slug', {}).get('level') == 'team'))
        # isolate repo-local's own rank: a slug defined at repo-local,
        # individual and universal, but NOT team, must resolve to repo-local
        cases.append(('repo-local beats individual and universal when team '
                      'is not in play for that slug',
                      by_slug.get('shared-slug-2', {}).get('level') == 'repo-local'))
        # everything unique to a level survives
        for slug, level in (('universal-only', 'universal'),
                            ('individual-only', 'individual'),
                            ('team-only', 'team'),
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
        practice(coll_team, 'claim-one', level_note='first team practice',
                 overrides='shared-target')
        practice(coll_team, 'claim-two', level_note='second team practice',
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
                'sources': [{'level': 'repo-local', 'name': 'spelled-differently',
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
    precedent_resolve.py had no resident/budget logic at all -- a team set
    marking several practices resident, on top of an individual set doing
    the same, could push a real session's resident block well past the cap
    with nothing objecting). Two directions: this repo's own resolved set
    (single source, well under budget) must NOT be flagged, and a
    synthetic multi-source set built to exceed the budget MUST be."""
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-budget-'))
    try:
        # direction 1: this repo's own set, unmodified, must resolve clean
        rc, out, _err = _run([sys.executable, str(ROOT / 'tools' /
                              'precedent_resolve.py'), '--repo', str(ROOT), '--json'])
        clean_ok = False
        if rc == 0:
            data = json.loads(out)
            clean_ok = not data.get('resident', {}).get('over_budget', True)

        # direction 2: a synthetic team source with an oversized resident
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
                        {'level': 'team', 'name': 'fixture-team',
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

        ok = clean_ok and over_ok
        if not clean_ok:
            print("  this repo's own resolved set was wrongly flagged over budget")
        if not over_ok:
            print("  a synthetic multi-source set built to exceed the budget "
                  "was NOT refused")
        check('cross-source resident budget (this repo alone stays clean; '
              'a synthetic team+universal combination built to exceed the '
              '2,000-token cap is refused, not silently carried)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


EXAMPLE_SET = ROOT / 'examples' / 'practice-set'


MANDATORY_SECTIONS = ('rule', 'why', 'story', 'install')  # 'detail' is optional


def check_practice_sections_present():
    """Every REAL practice file carries all four mandatory sections
    (## Detail is legitimately optional -- only some practices carry one).

    WHY THIS EXISTS SEPARATELY FROM check_example_set's identical-looking
    check. That check only ever ran against examples/practice-set/. For the
    52 phase-1-converted practices, a missing section usually gets caught
    anyway by the word-multiset content-preservation checks, because the
    corrupted text is not what PRACTICES.md's frozen original said. But
    those checks have nothing to compare against for a practice with no
    `source_practice_number` -- exactly the plan's own stated path forward
    (a new practice minted post-conversion, e.g. checkable-gets-checked).
    A single accidental trailing space on a heading
    (split_practices.py's section regex) used to silently merge that whole
    section into the one before it, with no error anywhere in the harness,
    for any practice minted this way. This closes that for the real
    catalogue, not just the shipped example."""
    ok = True
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue  # a parse failure is check_all_practices_parse's job
        missing = [s for s in MANDATORY_SECTIONS if s not in sections]
        if missing:
            ok = False
            print(f"  {f.name}: missing section(s) {', '.join(missing)} -- a "
                  f"heading with trailing whitespace, or one silently merged "
                  f"into the section before it, produces exactly this")
    check('every practice file carries all mandatory sections (## Rule, '
          '## Why, ## Story, ## Install -- ## Detail is optional)', ok)


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
          f'unglossed one is still caught)', ok)


def check_practice_heading_parsing():
    """A DIRECT unit test of split_practices._parse_practice_text against
    synthetic malformed headings, since check_practice_sections_present only
    scans the real, currently-committed practices/*.md tree -- it can only
    catch a malformed heading that happens to exist right now, never prove
    the parser handles one correctly in general.

    Two stated cases, from the fix's own history: trailing whitespace on a
    heading (the original bug: "## Detail " silently merged the whole
    section into the one before it) must still parse correctly, and a
    heading with the wrong CASE ("## detail" for the one optional section)
    must fail LOUDLY rather than reproduce the identical silent merge one
    character over -- which check_practice_sections_present cannot catch for
    exactly this section, since MANDATORY_SECTIONS deliberately excludes
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


# Widened from the original `^\*\*(\d{4}-\d{2}-\d{2}) — ` (bold date, then
# exactly an em dash with a space each side, nothing else) after a
# 2026-09-01 audit constructed plausible near-future variants -- a colon
# instead of the em-dash, an en-dash, a double-hyphen, an unbolded date, a
# leading list marker or checkbox -- and found every one silently invisible
# to `entries()` below: a non-matching entry is not merely miscounted, it
# is DROPPED from the text entirely if it sits above the first recognized
# match, which is exactly where a new entry lands under this section's own
# newest-first convention. This still cannot recognize a violation with NO
# date-like structure at all (unfixable by any regex); it substantially
# narrows the gap for the plausible near-term reformattings a human or an
# agent might actually type.
AMENDMENT_ENTRY_RE = re.compile(
    r'^\s*(?:[-*]\s+)?(?:\[[ xX]\]\s+)?\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}'
    r'\s*(?:[:—–]|--)\s*', re.M)
# A bare substring test ('decisions/' anywhere in the entry) exempted any
# entry that merely MENTIONED the word, including "not yet migrated to
# decisions/, still keeping every word inline" -- prose about NOT having a
# record, exempted as if it were one. Requires an actual file reference.
DECISIONS_LINK_RE = re.compile(r'decisions/[\w.-]+\.md')
DECISION_LENGTH_WORDS = 120
PLAN_MD = ROOT / 'PRACTICE_ENGINE_PLAN.md'


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
    plan_md = root / 'PRACTICE_ENGINE_PLAN.md'
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
        ['git', 'show', f'{base_ref}:PRACTICE_ENGINE_PLAN.md'],
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
            (repo / 'PRACTICE_ENGINE_PLAN.md').write_text(text, encoding='utf-8')
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
        (r2 / 'PRACTICE_ENGINE_PLAN.md').write_text(
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
        (r3 / 'PRACTICE_ENGINE_PLAN.md').write_text(
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
        (r4 / 'PRACTICE_ENGINE_PLAN.md').write_text(
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
        (r5 / 'PRACTICE_ENGINE_PLAN.md').write_text(
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
    doc_path = ROOT / 'GITHUB_ACTIONS.md'
    if not doc_path.exists():
        check('all workflows disclosed', False,
              'no GITHUB_ACTIONS.md exists to disclose any workflow in')
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
            'name': 'an-example-personal-set', 'path': str(EXAMPLE_SET)}}),
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


def check_rule_is_self_contained(files):
    """A `## Rule` may not end on a lead-in whose payload is somewhere else.

    The plan's binding constraint on the Rule/Detail split is that `## Rule`
    stays loadable ON ITS OWN: a session reading only the Rule must know what
    to DO, not merely that something applies. That is a judgment about
    meaning, and most of it cannot be checked -- a review pass over the split
    practices caught three defects that every check here passed, and only one
    of the three had a mechanical signature.

    This is that one. A Rule ending on "Three rules:" or "Two things fix it:"
    has had its payload moved to Detail and now announces a list it does not
    contain. It is the cheapest and least ambiguous form of the failure, so
    it is the form that gets a check; the other two -- a Rule whose scope gate
    moved to Detail, and a Rule using a term Detail defines -- are recorded in
    spec/PRACTICE_FORMAT.md as needing a reader, because they do.
    """
    ok = True
    for stem, (fm, sections, f) in sorted(files.items()):
        rule = (sections.get('rule') or '').strip()
        if not rule:
            ok = False
            print(f"  {f.name}: empty ## Rule -- a practice with nothing to do "
                  f"is not loadable on its own")
            continue
        if rule.endswith(':'):
            ok = False
            print(f"  {f.name}: ## Rule ends on a colon -- {rule.splitlines()[-1][:60]!r} "
                  f"-- the list or clause it introduces is not in the Rule, so a "
                  f"session that loads only the Rule is told something applies "
                  f"and not what to do about it")
    check('every ## Rule is self-contained (non-empty, and never ends on a '
          'lead-in whose payload moved to ## Detail)', ok)


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


def check_precedent_check_fires():
    """The enforced channel's own behaviour, as stated cases against throwaway
    repositories -- one planted violation per enforced practice.

    WHY THIS EXISTS. Until phase 4 the only thing verifying a `checked_by:`
    was check_checked_by_targets_exist() above, which asserts the named FILE
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
    import shutil, tempfile

    def git(cwd, *args, check_rc=True):
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-enforce-'))
    cases = []
    try:
        pristine = tmp / 'pristine'
        shutil.copytree(ROOT, pristine,
                        ignore=shutil.ignore_patterns('.git', '__pycache__',
                                                      '*.pyc', 'prompts'))
        git(pristine, 'init', '-q')
        git(pristine, 'config', 'user.email', 'harness@example.com')
        git(pristine, 'config', 'user.name', 'harness')
        git(pristine, 'add', '-A')
        git(pristine, 'commit', '-qm', 'baseline')

        def fresh(name):
            repo = tmp / name
            shutil.copytree(pristine, repo, symlinks=True)
            return repo

        def run(repo, slug, *extra):
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_check.py'),
                 '--only', slug, *extra],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        def rewrite(repo, rel, fn):
            p = repo / rel
            p.write_text(fn(p.read_text(encoding='utf-8')), encoding='utf-8')

        # --- the baseline must be clean, or every case below is meaningless
        base = fresh('baseline')
        rc, out = subprocess.run(
            [sys.executable, str(base / 'tools' / 'precedent_check.py')],
            capture_output=True, text=True, cwd=str(base)).returncode, ''
        cases.append(('an unplanted copy of this tree passes every check', rc == 0))

        # --- one planted violation per enforced practice --------------------
        planted = {}

        def case(slug, plant, extra=(), setup=None):
            repo = fresh(slug)
            if setup:
                setup(repo)
            if plant:
                plant(repo)
            rc, out = run(repo, slug, *extra)
            planted[slug] = (rc, out)
            cases.append((f'{slug}: a planted violation fails the check',
                          rc == 1 and 'VIOLATION' in out))
            clean = fresh(slug + '-clean')
            if setup:
                setup(clean)
            rc2, out2 = run(clean, slug, *extra)
            cases.append((f'{slug}: the same tree unplanted does not',
                          rc2 == 0 and 'VIOLATION' not in out2))

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

        # no-version-suffix
        case('no-version-suffix',
             lambda repo: (repo / 'findings-v2.md').write_text('x\n', encoding='utf-8'))

        # generated-artifact-provenance -- a hand-edited generated view
        case('generated-artifact-provenance',
             lambda repo: rewrite(repo, 'MAP.md', lambda t: t + '\nhand-added\n'))

        # orientation-map
        case('orientation-map', lambda repo: (repo / 'MAP.md').unlink())

        # quick-index -- the table removed from the instructions
        def _plant_qi(repo):
            rewrite(repo, 'AGENTS.md', lambda t: re.sub(
                r'\n\| Looking for.*?\n\n', '\n\n', t, flags=re.S))
        case('quick-index', _plant_qi)

        # two-check-levels -- the light/deep check pair removed from AGENTS.md
        def _plant_tcl(repo):
            rewrite(repo, 'AGENTS.md', lambda t: t.replace(
                '**light check**', 'light check', 1).replace(
                '**deep check**', 'deep check', 1))
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

        # merge-target-is-beta-branch -- origin/main advanced to include
        # origin/precedent-beta-v01 as an ancestor (the PR #89 incident,
        # replayed against the throwaway repo's own two remote-tracking
        # refs rather than the real ones). The pristine copy has exactly one
        # commit, so a second is made here to give the two refs a real
        # ancestor relationship to plant.
        def _plant_mtib(repo):
            c1 = git(repo, 'rev-parse', 'HEAD')
            (repo / 'PLANT_MARKER.txt').write_text('planted\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'second commit for the plant')
            c2 = git(repo, 'rev-parse', 'HEAD')
            git(repo, 'update-ref', 'refs/remotes/origin/precedent-beta-v01', c1)
            git(repo, 'update-ref', 'refs/remotes/origin/main', c2)
        case('merge-target-is-beta-branch', _plant_mtib)

        # environment-gotchas -- an entry that is a bare fix
        def _plant_eg(repo):
            rewrite(repo, 'AGENTS.md', lambda t: t.replace(
                '- **`pip install cmarkgfm`',
                '- `pip install cmarkgfm`.\n\n- **`pip install cmarkgfm`', 1))
        case('environment-gotchas', _plant_eg)

        # session-bootstrap -- setup named in prose, no hook to run it
        case('session-bootstrap',
             lambda repo: shutil.rmtree(repo / '.claude' / 'hooks'))

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

        # github-setup-disclosed -- a new workflow file, undisclosed
        case('github-setup-disclosed',
             lambda repo: (repo / '.github' / 'workflows' / 'zzz-planted.yml')
                 .write_text('name: planted\non: push\njobs: {}\n', encoding='utf-8'))

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

        # deliverables-look-like-output -- process residue in a deliverable
        case('deliverables-look-like-output',
             lambda repo: (repo / 'report.md').write_text(
                 '# Report\n\nThe number is 4. [verify later]\n', encoding='utf-8'))

        # search-by-purpose -- a document carrying generated numbers, indexed
        # from nothing a reader consults
        def _plant_sbp(repo):
            rewrite(repo, 'AGENTS.md', lambda t: t.replace('spec/LOADER.md', 'spec/x.md'))
            rewrite(repo, 'MAP.md', lambda t: t.replace('spec/LOADER.md', 'spec/x.md'))
            rewrite(repo, 'CLAUDE.md', lambda t: t.replace('spec/LOADER.md', 'spec/x.md'))
            rewrite(repo, 'spec/LOADER.md', lambda t: t + '\n')
        case('search-by-purpose', _plant_sbp)

        # computed-numbers-in-scripts -- a generated block edited by hand
        def _plant_cnis(repo):
            n = len(list((repo / 'practices').glob('*.md')))
            rewrite(repo, 'spec/LOADER.md', lambda t: t.replace(
                f'| Practices in the catalogue | {n} |',
                f'| Practices in the catalogue | {n + 9} |'))
        case('computed-numbers-in-scripts', _plant_cnis)

        # docs-track-models -- an owned figure restated in the prose
        def _plant_dtm(repo):
            n = len(list((repo / 'practices').glob('*.md')))
            rewrite(repo, 'spec/LOADER.md', lambda t: t.replace(
                '## The resident set, and why these six',
                f'The resident block is 6 of {n} practices.\n\n'
                '## The resident set, and why these six'))
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
        case('migration-scrubs-vocabulary',
             lambda repo: (repo / 'STALE.md').write_text(
                 'Still mentions OldPackName here.\n', encoding='utf-8'),
             setup=_setup_retired_vocab)

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
        rc_malf, out_malf = run(malformed_repo, 'migration-scrubs-vocabulary')
        cases.append(('migration-scrubs-vocabulary: a malformed config (a '
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
        # dependent-repo migration hit this with a team source's own
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
        rc_dir, out_dir = run(dir_exempt_repo, 'migration-scrubs-vocabulary')
        cases.append(("migration-scrubs-vocabulary: a `/`-suffixed "
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
             '--only', 'migration-scrubs-vocabulary'],
            capture_output=True, text=True, cwd=str(vendored_repo))
        out_vend = r_vend.stdout + r_vend.stderr
        cases.append(('migration-scrubs-vocabulary: ROOT resolves to the '
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
            [sys.executable, str(boom_repo / 'tools' / 'precedent_check.py')],
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
        # invariant no longer holds
        case('scripts-assert-properties',
             lambda repo: rewrite(repo, 'tools/build_views.py', lambda t: t.replace(
                 'RESIDENT_BUDGET_TOKENS = 2000', 'RESIDENT_BUDGET_TOKENS = 10')))

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

        # --- and the registry must not contain an untested claim ------------
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            '_pc', ROOT / 'tools' / 'precedent_check.py')
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        untested = sorted(set(pc.CHECKS) - set(planted))
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
        check(f"enforced channel fires ({len(cases)} stated cases: one planted "
              f"violation per enforced practice, plus the unplanted baseline)",
              not bad, detail)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_routing_scope(files):
    """Every on-demand practice's applies_to agrees with tools/routing_scope.json,
    and every entry carries a reason.

    The point is not that a second file holds the same globs -- that would be a
    restatement with nothing gating it, which is the failure `docs-track-models`
    describes. The point is that the REASON is recorded per practice, including
    for the 24 that deliberately stay at `**`. A practice left unrouted by
    omission and one left unrouted on purpose look identical in the practice
    file; they do not here.
    """
    scope_path = ROOT / 'tools' / 'routing_scope.json'
    if not scope_path.exists():
        not_applicable('routing scope is recorded with a reason per practice',
                       'tools/routing_scope.json does not exist')
        return
    scope = json.loads(scope_path.read_text(encoding='utf-8'))['practices']
    problems = []
    for slug, (fm, _s, _f) in sorted(files.items()):
        row = scope.get(slug)
        if fm.get('tier') != 'on-demand':
            continue
        if row is None:
            problems.append(f"{slug}: no entry in routing_scope.json -- a practice "
                            f"whose routing nobody decided")
            continue
        want, got = row.get('globs'), json.loads(fm.get('applies_to', '[]'))
        if want != got:
            problems.append(f"{slug}: applies_to is {got} but routing_scope.json "
                            f"says {want}")
        if not (row.get('why') or '').strip():
            problems.append(f"{slug}: no reason recorded for its scope")
    check('routing scope agrees with the practice files, with a reason for every '
          'one (including every practice deliberately left at `**`)',
          not problems, '; '.join(problems[:6]))


def check_routing_audit_coverage():
    """routing_audit.py's coverage() -- the mechanical half of the routing
    audit (practices/routing-audit.md) -- against real practices already in
    the catalogue, not a synthetic fixture: PRACTICES_DIR is hardcoded in
    routing_audit.py (it reads the real tree, deliberately, the same way
    this file's own PRACTICES_DIR is), so the planted case is choosing real
    judgment-only practices with known narrow globs and asserting on their
    known, checkable behavior -- the checkable-gets-checked discipline
    applied to the routing audit's own tool, per spec/UNBUILT_PLAN_ITEMS.md
    ("Part 2"), which found this half had never actually been exercised.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_ra', ROOT / 'tools' / 'routing_audit.py')
    ra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ra)

    practices = {slug: globs for slug, globs, _rule, _f in ra.judgment_only_practices()}
    problems = []

    def want(slug):
        if slug not in practices:
            problems.append(f"fixture practice {slug!r} is no longer judgment-only "
                            f"or no longer active -- pick a replacement fixture")
            return False
        return True

    # A narrow glob that should match: lead-with-what-it-is names README.md
    # explicitly (not '**').
    if want('lead-with-what-it-is'):
        hits = {slug for slug, _path in ra.coverage(['README.md'])}
        if 'lead-with-what-it-is' not in hits:
            problems.append("coverage(['README.md']) missed lead-with-what-it-is, "
                            "whose applies_to names README.md directly")

    # A file none of the narrow-glob fixtures should match -- catches a glob
    # implementation that over-matches (e.g. '**' leaking through, or a bad
    # path-matching call) as well as one that under-matches.
    unrelated_hits = {slug for slug, _path in ra.coverage(['tools/verify_harness.py'])}
    for slug in ('lead-with-what-it-is', 'pr-template-honest-gates', 'parallel-artifact-ledger'):
        if slug in practices and slug in unrelated_hits:
            problems.append(f"coverage(['tools/verify_harness.py']) false-positived "
                            f"on {slug}, whose applies_to does not match this path")

    # The practice's own stated design: applies_to: ['**'] carries no routing
    # signal (routing_audit.coverage() drops it deliberately -- "narrow = [g
    # for g in globs if g != '**']; if not narrow: continue") and must never
    # surface as a coverage hit for any file, even one everything matches.
    if want('registry-source-of-truth'):
        wildcard_hits = {slug for slug, _path in ra.coverage(['README.md', 'AGENTS.md'])}
        if 'registry-source-of-truth' in wildcard_hits:
            problems.append("coverage() surfaced registry-source-of-truth (applies_to: "
                            "['**']) as a hit -- '**' is not a routing signal and must "
                            "be excluded, per the tool's own docstring")

    # A glob scoped to a directory that does not include the probe file.
    if want('pr-template-honest-gates'):
        hits = {slug for slug, _path in ra.coverage(['.github/pull_request_template.md'])}
        if 'pr-template-honest-gates' not in hits:
            problems.append("coverage(['.github/pull_request_template.md']) missed "
                            "pr-template-honest-gates")

    check('routing audit coverage() matches narrow applies_to globs correctly, '
          'in both directions, and drops \'**\' as a non-signal (5 stated cases '
          'against real catalogue fixtures)',
          not problems, '; '.join(problems))


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
    for g in sorted(vocab):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_gate.py'), g],
                           capture_output=True, text=True, cwd=str(ROOT))
        ok = r.returncode == 0 and all(s in r.stdout for s in by_gate[g])
        cases.append((f'`precedent_gate.py {g}` returns every practice registered to it', ok,
                      (r.stdout + r.stderr).strip()[:120] if not ok else ''))

    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_gate.py'), 'no-such-gate'],
                       capture_output=True, text=True, cwd=str(ROOT))
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
    for stop_hook in (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'stop-git-check.sh',
                      ROOT / '.claude' / 'hooks' / 'stop-git-check.sh'):
        cases.append((f'the reply gate is wired into {stop_hook.relative_to(ROOT)}',
                      stop_hook.exists() and 'precedent_gate' in stop_hook.read_text(errors='ignore')))

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'gate-triggered channel ({len(cases)} stated cases: closed vocabulary, '
          f'no empty gate, every gate resolves, unknown gates fail loudly, '
          f'push and reply actually wired)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_materialize_bridges_loader():
    """tools/precedent_materialize.py — the deep-check session's own answer
    to spec/PHASE5_BRIEF.md's named gap: precedent_resolve.py is the only
    multi-source-aware tool; build_views.py/precedent_paths.py/
    precedent_gate.py/precedent_check.py all read a single local practices/
    directory. Proven for real (not just unit-tested here) against the two
    real private sets by that session; this harness case is the planted,
    repeatable version: two throwaway sources (one universal-shaped, one
    team-shaped) with a deliberate tools/checks/ filename collision AND a
    resident-budget overage, confirming both refuse, then a clean pair
    materializes and an unmodified build_views.py run against the output
    actually produces a resident block naming a practice from EACH source
    (not just proving files got copied)."""
    import shutil, subprocess, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-materialize-'))

    def write_practice(path, slug, rule, tier='on-demand', occasion='x'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "{occasion}"\n'
            f'gates: []\nindex_clause: "x"\nchecked_by: null\ndefines: []\n'
            f'status: active\nsupersedes: []\noverrides: null\n'
            f'added: 2026-09-02\napproved_by: "harness, 2026-09-02"\n'
            f'source_practice_number: null\n---\n## Rule\n{rule}\n\n'
            f'## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')

    def write_check(path, body='VIOLATION: fixture\n'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'#!/usr/bin/env python3\nprint({body!r})\n', encoding='utf-8')

    cases = []
    try:
        uni, team = tmp / 'universal', tmp / 'team'
        write_practice(uni / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture Rule.', tier='resident')
        write_practice(team / 'practices' / 'team-fixture.md', 'team-fixture',
                        'A team fixture Rule.', tier='resident')
        write_check(uni / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(team / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(uni / 'tools' / 'checks' / 'tests' / 'test_uni_fixture.sh',
                    body='fixture\n')

        consumer = tmp / 'consumer'
        (consumer).mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'uni', 'path': str(uni)},
                        {'level': 'team', 'name': 'team', 'path': str(team)}]
        }), encoding='utf-8')

        materialize_tool = str(ROOT / 'tools' / 'precedent_materialize.py')

        def run(*extra):
            r = subprocess.run([sys.executable, materialize_tool, '--out', str(consumer),
                                 '--repo', str(consumer), *extra],
                                capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        # --- a tools/checks/ filename collision across sources refuses -----
        rc, out = run()
        cases.append(('a checks/ filename collision across two sources refuses',
                      rc == 1 and 'collision' in out))

        # --- an over-budget combined resident set refuses -------------------
        (team / 'tools' / 'checks' / 'check_shared_name.py').unlink()
        huge_rule = ' '.join(['word'] * 2000)
        write_practice(team / 'practices' / 'huge-fixture.md', 'huge-fixture',
                        huge_rule, tier='resident')
        rc, out = run()
        cases.append(('an over-budget combined resident set refuses to materialize',
                      rc == 1 and 'over' in out and 'budget' in out))

        # --- a clean pair materializes, and an UNMODIFIED build_views.py run
        # against the output actually shows both sources' resident practices --
        (team / 'practices' / 'huge-fixture.md').unlink()
        rc, out = run()
        materialized_ok = (rc == 0 and (consumer / 'MANIFEST.json').exists()
                            and (consumer / 'practices' / 'uni-fixture.md').exists()
                            and (consumer / 'practices' / 'team-fixture.md').exists())

        # --- every MANIFEST.json path (practices AND checks) actually
        # resolves to a file on disk -- regression case for a doubled
        # tools/checks/checks/ segment in checks[].path entries -------------
        manifest_paths_ok = False
        manifest_paths_detail = ''
        if materialized_ok:
            manifest = json.loads((consumer / 'MANIFEST.json').read_text(encoding='utf-8'))
            entries = ([('practices', e['slug'], f"practices/{e['slug']}.md")
                        for e in manifest.get('practices', [])]
                       + [('checks', e['path'], e['path'])
                          for e in manifest.get('checks', [])])
            missing = [label for _, label, rel in entries if not (consumer / rel).exists()]
            manifest_paths_ok = not missing
            manifest_paths_detail = f"missing on disk: {missing}" if missing else ''
        cases.append(('every MANIFEST.json practices[]/checks[] path resolves to a '
                      'real file on disk', manifest_paths_ok, manifest_paths_detail))

        for f in ('build_views.py', 'split_practices.py'):
            shutil.copyfile(ROOT / 'tools' / f, consumer / 'tools' / f)
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'build_views.py')],
                            capture_output=True, text=True, cwd=str(consumer))
        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8') \
            if (consumer / 'AGENTS.md').exists() else ''
        cases.append(('a clean materialize + unmodified build_views.py run produces '
                      "a resident block naming BOTH sources' practices, not just one",
                      materialized_ok and r.returncode == 0
                      and 'uni-fixture' in agents_text and 'team-fixture' in agents_text))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_materialize.py bridges the loader ({len(cases)} stated cases: '
          f'a checks/ collision refuses, an over-budget combined set refuses, a clean '
          f"materialize feeds an unmodified build_views.py both sources' content)",
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_sync_views_cross_source():
    """tools/precedent_sync_views.py -- the one-command glue over
    precedent_materialize.py + build_views.py --agents-only that a
    CONSUMING repo (all four sources at once) actually runs, as opposed to
    the two tools it wraps, each already covered by their own harness
    case. Built and this case added 2026-09-03 alongside the precedence
    reorder and the repo-local level -- the fixture below is what caught
    two real bugs before either shipped: precedent_materialize.py deleting
    a repo-local source's own file before reading it (a self-referential
    `path: "."` source), and this tool's resident-count-by-level header
    counting every resolved practice instead of only the resident ones."""
    import shutil, tempfile

    def write_practice(path, slug, rule, tier='on-demand', occasion='x'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\nseverity: default\n'
            f'applies_to: ["**"]\noccasion: "{occasion}"\ngates: []\n'
            f'index_clause: "x"\nchecked_by: null\ndefines: []\nstatus: active\n'
            f'supersedes: []\noverrides: null\nadded: null\napproved_by: "x"\n'
            f'source_practice_number: null\n---\n## Rule\n{rule}\n\n## Why\nx\n\n'
            f'## Story\nx\n\n## Install\nx\n', encoding='utf-8')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-sync-views-'))
    cases = []
    try:
        consumer = tmp / 'consumer'
        universal, team, individual = tmp / 'u', tmp / 't', tmp / 'i'

        write_practice(universal / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture rule.', tier='resident')
        write_practice(team / 'practices' / 'team-fixture.md', 'team-fixture',
                        'A team fixture rule.', tier='resident')
        write_practice(individual / 'practices' / 'ind-fixture.md', 'ind-fixture',
                        'An individual fixture rule.', occasion='doing individual things')
        # repo-local at a SUBDIRECTORY, per the recommended convention --
        # this is what keeps its hand-authored source apart from the
        # materialized output, both of which land under `consumer/`.
        write_practice(consumer / 'local' / 'practices' / 'local-fixture.md',
                        'local-fixture', 'A repo-local fixture rule.',
                        occasion='doing local things')

        (consumer / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'uni', 'path': str(universal)},
                        {'level': 'team', 'name': 'team', 'path': str(team)},
                        {'level': 'repo-local', 'name': 'self', 'path': 'local'}]
        }), encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({
            'individual': {'name': 'ind', 'path': str(individual)}}), encoding='utf-8')
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        sync_tool = str(ROOT / 'tools' / 'precedent_sync_views.py')

        def run(*extra):
            r = subprocess.run([sys.executable, sync_tool, '--repo', str(consumer),
                                 '--user-config', str(user_cfg), *extra],
                                capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        rc, out = run()
        cases.append(('a clean sync across all four sources exits 0', rc == 0, out))

        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('the resident block names BOTH resident sources, not just one',
                      'uni-fixture' in agents_text and 'team-fixture' in agents_text))
        cases.append(('the resident-count-by-level header counts only the '
                      'RESIDENT practices, not all four resolved ones',
                      '2 of 4 practices (1 team, 1 universal)' in agents_text))
        cases.append(('the occasion index reaches the on-demand individual '
                      'and repo-local practices too',
                      'ind-fixture' in agents_text and 'local-fixture' in agents_text))
        cases.append(('the repo-local source file at its OWN subdirectory '
                      'survives the sync untouched',
                      (consumer / 'local' / 'practices' / 'local-fixture.md').exists()))

        rc2, out2 = run('--check')
        cases.append(('--check on a just-synced, unmodified AGENTS.md exits 0',
                      rc2 == 0, out2))

        (consumer / 'AGENTS.md').write_text(
            agents_text.replace('uni-fixture', 'HAND-EDITED'), encoding='utf-8')
        rc3, out3 = run('--check')
        cases.append(('--check on a hand-edited AGENTS.md exits 1, not silently 0',
                      rc3 == 1, out3))

        # the exact bug this fixture was built to catch (2026-09-03): a
        # repo-local source declared at the bare repo root (`path: "."`)
        # used to crash precedent_materialize.py, or worse, silently
        # destroy its own hand-authored file the moment another source won
        # a shared slug. A later deep-check audit the same day found the
        # crash fix didn't close the silent-overwrite case, or a second,
        # worse case (materialize()'s own output read back as if this
        # source had authored it on the NEXT run) -- materialize() now
        # refuses this combination outright, unconditionally, rather than
        # attempting to make source == destination safe.
        #
        # repo-local itself can no longer even REACH this fixture:
        # precedent_resolve.py's load_config now requires a repo-local
        # source's `path` to be exactly "local" (see check_source_precedence's
        # own bare-root and other-subdirectory-name cases), so `path: "."`
        # for `level: "repo-local"` is refused before materialize() runs at
        # all. This fixture uses `level: "universal"` instead -- still a
        # perfectly legal `path: "."` (this repo's own precedent.json does
        # exactly that, self-hosting) -- to keep materialize()'s
        # level-agnostic `_self_referential_sources` guard itself under
        # test, on a configuration that is still allowed to reach it.
        selfref = tmp / 'selfref'
        write_practice(selfref / 'practices' / 'local-only.md', 'local-only',
                        'A self-referential universal rule.')
        (selfref / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'self', 'path': '.'}]
        }), encoding='utf-8')
        (selfref / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        original_selfref = (selfref / 'practices' / 'local-only.md').read_bytes()
        r_self = subprocess.run([sys.executable, sync_tool, '--repo', str(selfref)],
                                 capture_output=True, text=True)
        cases.append(("a repo-local source declared at the bare repo root "
                      "(`path: \".\"`) is refused outright, loudly, naming "
                      "the subdirectory convention, rather than crashing or "
                      "silently materializing over its own source",
                      r_self.returncode == 1
                      and 'declares its `path` as this run' in (r_self.stdout + r_self.stderr)
                      and 'subdirectory' in (r_self.stdout + r_self.stderr)
                      and (selfref / 'practices' / 'local-only.md').read_bytes()
                          == original_selfref,
                      r_self.stdout + r_self.stderr))

        # the shadow-and-second-run case: a self-referential source at path
        # "." shares a slug with a HIGHER-precedence source -- this must
        # also refuse before any file is touched, not just the
        # single-source case above. `level: "universal"` again, for the
        # same reason as selfref above -- repo-local at "." can no longer
        # reach materialize() at all, so this exercises the same
        # lowest-precedence-loses-and-must-not-be-destroyed shape with
        # universal (still below team) standing in for it.
        selfref2 = tmp / 'selfref2'
        other = tmp / 'other-team'
        write_practice(selfref2 / 'practices' / 'shared.md', 'shared',
                        'HAND-AUTHORED -- MUST SURVIVE.')
        write_practice(other / 'practices' / 'shared.md', 'shared',
                        'TEAM VERSION.')
        (selfref2 / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'team', 'name': 'other-team', 'path': str(other)},
                        {'level': 'universal', 'name': 'self', 'path': '.'}]
        }), encoding='utf-8')
        (selfref2 / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r_self2 = subprocess.run([sys.executable, sync_tool, '--repo', str(selfref2)],
                                  capture_output=True, text=True)
        cases.append(('a self-referential source shadowed by a '
                      'higher-precedence source is refused before its own '
                      'file is touched, not silently overwritten',
                      r_self2.returncode == 1
                      and 'MUST SURVIVE' in
                          (selfref2 / 'practices' / 'shared.md').read_text(encoding='utf-8'),
                      r_self2.stdout + r_self2.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_sync_views.py syncs a consuming repo across all four '
          f'sources ({len(cases)} stated cases: clean sync, both resident '
          f'sources shown, correct level-of-resident counting, occasion '
          f'index reaches on-demand practices, --check both directions, a '
          f'self-referential source is refused rather than crashed or '
          f'silently overwritten, alone or shadowed)',
          not bad, '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_detect_restated_fires():
    """`precedent_detect.py restated` (Stage 1's cross-source duplicate-Rule
    scan) had zero harness coverage before this deep-check pass -- a real
    run against all three real sources together (this repo, and both
    private sets, once populated) found nothing, which is consistent with
    there being no actual restatement today, but is indistinguishable from
    the detector being silently broken without a planted case that proves
    it still fires. Two throwaway sources, one practice each: a near-exact
    reword (should fire) and a genuinely unrelated Rule (should not)."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-detect-restated-'))

    def write_practice(path, slug, rule):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "x"\ngates: []\n'
            f'index_clause: "x"\nchecked_by: null\ndefines: []\nstatus: active\n'
            f'supersedes: []\noverrides: null\nadded: 2026-09-02\n'
            f'approved_by: "harness, 2026-09-02"\nsource_practice_number: null\n'
            f'---\n## Rule\n{rule}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')

    try:
        src_a, src_b = tmp / 'source-a', tmp / 'source-b'
        write_practice(src_a / 'practices' / 'reworded-one.md', 'reworded-one',
                        'After any state-changing operation, check the state you '
                        'wanted, not that the command reported success.')
        write_practice(src_b / 'practices' / 'reworded-two.md', 'reworded-two',
                        'After any state changing operation check the state you '
                        'actually wanted, never just that the command reported success.')
        write_practice(src_b / 'practices' / 'unrelated.md', 'unrelated',
                        'Slide decks are built by the deck engine and delivered '
                        'as a viewable file attached to the same reply.')
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_detect.py'),
                             'restated', '--against', f'{src_a},{src_b}'],
                            capture_output=True, text=True)
        out = r.stdout + r.stderr
        fires_on_reword = (r.returncode == 0 and "'reworded-one'" in out
                            and "'reworded-two'" in out and '1 pair' in out)
        silent_on_unrelated = "'unrelated'" not in out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    check('precedent_detect.py restated fires (2 stated cases: a genuine '
          'reword across sources is caught, an unrelated Rule in the same '
          'run is not)',
          fires_on_reword and silent_on_unrelated,
          f'fires_on_reword={fires_on_reword} silent_on_unrelated={silent_on_unrelated}')


def check_creation_pipeline_fires():
    """Phase 5's own done-when, tested directly rather than trusted from a
    manual smoke test: "a candidate can be raised, promoted and landed end
    to end; a candidate failing any of the four criteria is refused with a
    reason" (PRACTICE_ENGINE_PLAN.md, Sequence). Not registered as a
    `checked_by` in tools/precedent_check.py -- same reasoning
    check_decision_records_not_inline already states for itself: no single
    practices/*.md file backs "the creation pipeline works," so registering
    it there would inflate ENFORCEMENT.md's coverage count with a phantom
    row.

    Fixture is a throwaway individual-shaped repo (practices/ + candidates/)
    against THIS repo's real universal catalogue for the non-duplication and
    checked_by-registration cases, since those need a real, populated
    CHECKS registry and a real existing slug to collide with -- a fixture
    catalogue of one or two invented practices would not exercise either."""
    import shutil, tempfile

    def pyrun(*args, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        r = subprocess.run([sys.executable, *args], capture_output=True,
                           text=True, env=env)
        return r.returncode, r.stdout + r.stderr

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-pipeline-'))
    cases = []
    try:
        repo = tmp / 'fixture-individual'
        (repo / 'practices').mkdir(parents=True)
        (repo / 'candidates').mkdir(parents=True)

        cand_tool = str(ROOT / 'tools' / 'precedent_candidate.py')
        promote_tool = str(ROOT / 'tools' / 'precedent_promote.py')
        land_tool = str(ROOT / 'tools' / 'precedent_land.py')

        def make_candidate(slug, **extra):
            args = [cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                    '--slug', slug, '--title', slug, '--signal', 'explicit-instruction',
                    '--raised-by', 'harness', '--observed', 'a fixture incident',
                    '--proposed-rule', extra.pop('rule', f'Always do the {slug} thing.')]
            for k, v in extra.items():
                args += [f'--{k}', str(v)]
            rc, out = pyrun(*args)
            if rc != 0:
                raise RuntimeError(f"fixture candidate creation failed: {out}")
            found = sorted((repo / 'candidates').glob(f'{slug}-*.md'))
            return found[-1]

        # --- criterion 1: recurrence or real cost ---------------------------
        f1 = make_candidate('pipeline-fixture-c1', recurrence=1)
        rc, out = pyrun(promote_tool, '--file', str(f1), '--level', 'individual')
        cases.append(('criterion 1 (recurrence/cost) refuses a lone, costless candidate',
                      rc == 1 and 'criterion 1' in out and 'recurrence or real cost' in out))
        f1b = make_candidate('pipeline-fixture-c1b', recurrence=1, occasion='a fixture occasion',
                            **{'cost-if-once': 'a stated one-time cost'})
        rc, out = pyrun(promote_tool, '--file', str(f1b), '--level', 'individual')
        cases.append(('criterion 1 passes on a stated one-time cost '
                      '(reachability also satisfied, so only criterion 1 is isolated)',
                      rc == 0 and 'PROMOTED' in out))

        # --- criterion 2: reachability ---------------------------------------
        f2 = make_candidate('pipeline-fixture-c2', recurrence=2)
        rc, out = pyrun(promote_tool, '--file', str(f2), '--level', 'individual')
        cases.append(('criterion 2 (reachability) refuses a wide-open, occasion-less candidate',
                      rc == 1 and 'criterion 2' in out and 'reachability' in out))

        # --- criterion 3: non-duplication (against THIS repo's real catalogue) ---
        real_slug = 'verify-postcondition'
        f3 = make_candidate(real_slug, recurrence=2, occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f3), '--level', 'individual',
                        '--against', str(ROOT))
        cases.append(('criterion 3 (non-duplication) refuses an exact-slug collision '
                      'with a real existing practice',
                      rc == 1 and 'criterion 3' in out and 'non-duplication' in out))

        # --- non-duplication defaults to checking the candidate's OWN repo too --
        # Deep-check regression case: --against used to default to ROOT alone
        # regardless of the candidate's level, so promoting an individual/team
        # candidate with no explicit --against silently never checked it
        # against that repo's own catalogue.
        (repo / 'practices' / 'pipeline-fixture-owncatalogue.md').write_text(
            '---\nslug: pipeline-fixture-owncatalogue\ntitle: Fixture\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "x"\ngates: []\nindex_clause: "x"\nchecked_by: null\n'
            'defines: []\nstatus: active\nsupersedes: []\noverrides: null\n'
            'added: 2026-09-02\napproved_by: "harness, 2026-09-02"\n'
            'source_practice_number: null\n---\n## Rule\nAlways do the fixture thing.\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
            encoding='utf-8')
        f3b = make_candidate('pipeline-fixture-owncatalogue', recurrence=2,
                              occasion='a fixture occasion',
                              rule='Always do the fixture thing.')
        rc, out = pyrun(promote_tool, '--file', str(f3b), '--level', 'individual')
        cases.append(("non-duplication's default --against catches a collision with "
                      "the candidate's OWN repo, not just this repo (universal)",
                      rc == 1 and 'criterion 3' in out and 'non-duplication' in out))

        # --- criterion 4: budget ----------------------------------------------
        huge_rule = ' '.join(['word'] * 3000)  # ~3900 tokens at 1.3/word, alone over the 2000 cap
        f4 = make_candidate('pipeline-fixture-c4', recurrence=2, tier='resident', rule=huge_rule)
        rc, out = pyrun(promote_tool, '--file', str(f4), '--level', 'individual')
        cases.append(('criterion 4 (budget) refuses a resident request that blows the cap',
                      rc == 1 and 'criterion 4' in out and 'budget' in out))

        # --- full pass: create, promote, land, and the file really parses -----
        f5 = make_candidate('pipeline-fixture-pass', recurrence=2, occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f5), '--level', 'individual')
        promoted = rc == 0 and 'PROMOTED' in out
        rc, out = pyrun(land_tool, '--file', str(f5), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        landed_file = repo / 'practices' / 'pipeline-fixture-pass.md'
        parses = False
        if landed_file.exists():
            try:
                sp._read_practice_file(landed_file)
                parses = True
            except sp.PracticeFileError:
                parses = False
        cases.append(('a fully-valid candidate promotes, lands, and the landed '
                      'file parses as a real practice',
                      promoted and rc == 0 and landed_file.exists() and parses))

        # --- landing hard-refuses an unregistered checked_by claim -------------
        f6 = make_candidate('pipeline-fixture-checkedby', recurrence=2,
                            **{'checked-by': 'tools/doc_lint.py'})
        rc, out = pyrun(land_tool, '--file', str(f6), '--level', 'universal',
                        '--against', str(ROOT))
        cases.append(("landing refuses a checked_by naming a real file that is not "
                      "registered in precedent_check.py's CHECKS",
                      rc == 1 and 'not a key in' in out
                      and not (ROOT / 'practices' / 'pipeline-fixture-checkedby.md').exists()))

        # --- landing marks the source candidate promoted, not left open ---------
        # Deep-check regression case: `status: promoted` was a declared valid
        # value nothing ever set -- a landed candidate stayed `status: open`
        # forever, so `list --status open` kept surfacing it as if it still
        # needed a decision.
        f5b = make_candidate('pipeline-fixture-marks-promoted', recurrence=2,
                              occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f5b), '--level', 'individual')
        rc, out = pyrun(land_tool, '--file', str(f5b), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        landed_fm, _ = pcand._parse_frontmatter(f5b.read_text(encoding='utf-8'))
        cases.append(('landing rewrites the source candidate to status: promoted',
                      rc == 0 and landed_fm.get('status') == 'promoted'))

        # --- landing hard-refuses an unlisted team approver ---------------------
        f7 = make_candidate('pipeline-fixture-approver', recurrence=2, occasion='x')
        rc, out = pyrun(land_tool, '--file', str(f7), '--level', 'team',
                        '--path', str(ROOT), '--approved-by', 'Someone Not An Approver')
        # ROOT has no approvers.json at all -- refused for that reason, which is
        # itself the right failure mode (never landed without one to check against).
        cases.append(('landing refuses a team candidate when there is no '
                      'approvers.json to check the named approver against',
                      rc == 1 and not (ROOT / 'practices' / 'pipeline-fixture-approver.md').exists()))

        # --- disclose-landing: landing states plainly what happened and where --
        # Added 2026-09-03 after Morgan asked directly whether this was
        # already happening -- it wasn't guaranteed, only implied by the
        # tools' own file paths. The tools now print an unconditional
        # DISCLOSE TO THE HUMAN line naming the level, the location, and
        # whether it's already in force; this is that line's own test, not
        # a proxy for it, so a future edit that quietly drops the line fails
        # here rather than only in a live conversation.
        f9 = make_candidate('pipeline-fixture-disclose-individual', recurrence=2,
                             occasion='a fixture occasion')
        rc, out = pyrun(promote_tool, '--file', str(f9), '--level', 'individual')
        rc, out = pyrun(land_tool, '--file', str(f9), '--level', 'individual',
                        '--path', str(repo), '--approved-by', 'harness')
        cases.append(('landing an individual practice discloses it as the '
                      "person's own set, already in force",
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'YOUR OWN individual practice set' in out
                      and str(repo) in out))

        # A dynamic execution test for the universal disclosure line would
        # need to actually land into ROOT/practices/ (precedent_land.py
        # hardcodes universal's dest_dir to this repo's own tree) -- the
        # checked_by-refusal case above deliberately avoids ever doing that
        # for real, and this test follows the same caution rather than risk
        # a stray file in this repo's real, public catalogue on a crash
        # mid-test. A static source check is the honest, zero-risk substitute.
        land_src = (ROOT / 'tools' / 'precedent_land.py').read_text(encoding='utf-8')
        cases.append(('precedent_land.py source still carries the universal '
                      'DISCLOSE line (static check -- see comment above for why '
                      'this is not an execution test)',
                      'DISCLOSE TO THE HUMAN' in land_src
                      and 'DRAFT ONLY' in land_src))

        # --- a same-day, same-slug raise registers as recurrence, never fails --
        # Deep-check regression case: cmd_create used to hard-refuse a second
        # same-day raise of the same slug ("already exists"), silently dropping
        # exactly the recurrence signal Stage 1 exists to capture.
        rc_a, out_a = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                             '--slug', 'pipeline-fixture-sameday', '--title', 't',
                             '--signal', 'explicit-instruction', '--raised-by', 'harness',
                             '--observed', 'first raise', '--proposed-rule', 'r',
                             '--occasion', 'a fixture occasion')
        rc_b, out_b = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                             '--slug', 'pipeline-fixture-sameday', '--title', 't',
                             '--signal', 'explicit-instruction', '--raised-by', 'harness',
                             '--observed', 'second raise, same day', '--proposed-rule', 'r',
                             '--occasion', 'a fixture occasion')
        sameday_files = sorted((repo / 'candidates').glob('pipeline-fixture-sameday-*.md'))
        rc, out = pyrun(promote_tool, '--file', str(sameday_files[0]), '--level', 'individual')
        cases.append(('a second same-day raise of the same slug does not fail, and '
                      'registers as recurrence rather than needing recurrence hand-bumped',
                      rc_a == 0 and rc_b == 0 and len(sameday_files) == 2
                      and rc == 0 and 'PROMOTED' in out))

        # --- recurrence counting matches on the parsed slug, not a filename prefix --
        # Deep-check regression case: counting file_count via glob(f'{slug}-*.md')
        # let a candidate named e.g. 'foo-bar' inflate 'foo''s recurrence count,
        # since 'foo-bar-<date>.md' also matches the glob 'foo-*.md'.
        make_candidate('pipeline-fixture-prefix', recurrence=1)
        make_candidate('pipeline-fixture-prefix-longer', recurrence=1,
                        **{'cost-if-once': 'unrelated candidate, shares a slug prefix'})
        f_prefix = sorted((repo / 'candidates').glob('pipeline-fixture-prefix-2*.md'))[0]
        rc, out = pyrun(promote_tool, '--file', str(f_prefix), '--level', 'individual')
        cases.append(("a differently-slugged candidate sharing a name prefix "
                      "('foo-bar' alongside 'foo') never inflates the shorter "
                      "slug's recurrence count",
                      rc == 1 and 'criterion 1' in out and 'actual file count 1' in out))

        # --- Observed text quoting the Proposed Rule heading does not corrupt the split --
        # Deep-check regression case: a naive first-match split on '## Proposed
        # Rule' truncates Observed and folds the rest of it into the Rule the
        # moment Observed narrates something that itself contains that literal
        # heading line -- a real risk for a candidate ABOUT a heading collision.
        f8 = make_candidate(
            'pipeline-fixture-heading', recurrence=2, occasion='x',
            observed='the output contained a line reading\n## Proposed Rule\nwhich confused a naive parser',
            rule='The real proposed rule text.')
        rc, out = pyrun(promote_tool, '--file', str(f8), '--level', 'individual')
        cases.append(("an Observed section that quotes the literal '## Proposed "
                      "Rule' heading does not corrupt the extracted Rule text",
                      rc == 0 and 'The real proposed rule text.' in out
                      and 'confused a naive parser' not in out))

        # --- team --as-issue: authority, not access, decides the path ---------
        # Added 2026-09-02 after a real dependent-repo session worked through
        # exactly when a team candidate needs to become a GitHub Issue rather
        # than a quiet candidates/ file: only when whoever's raising it is NOT
        # a listed approver. A listed approver's own say-so already lands a
        # team practice directly (precedent_land.py), so --as-issue and the
        # nudge below are both about authority, never about git access.
        team_repo = tmp / 'fixture-team'
        (team_repo / 'candidates').mkdir(parents=True)
        (team_repo / 'approvers.json').write_text(
            json.dumps({'approvers': [{'name': 'Approved Person', 'github': 'approved-gh'}]}),
            encoding='utf-8')
        subprocess.run(['git', 'init', '-q'], cwd=team_repo, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin',
                        'https://github.com/fixture-owner/fixture-team.git'],
                       cwd=team_repo, check=True)

        f10 = make_candidate('pipeline-fixture-disclose-team', recurrence=2, occasion='x')
        rc, out = pyrun(promote_tool, '--file', str(f10), '--level', 'team')
        rc, out = pyrun(land_tool, '--file', str(f10), '--level', 'team',
                        '--path', str(team_repo), '--approved-by', 'Approved Person')
        cases.append(('landing a team practice by a real approver discloses the '
                      'named team set, already in force for everyone on it',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'TEAM practice set' in out and str(team_repo) in out
                      and "'Approved Person'" in out))

        def make_issue_draft(raised_by, **extra):
            gh_repo = extra.pop('github_repo', None)
            args = [cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                    '--as-issue', 'true',
                    '--slug', extra.pop('slug', 'pipeline-fixture-issue'),
                    '--title', 't', '--signal', 'explicit-instruction',
                    '--raised-by', raised_by, '--observed', 'a fixture incident',
                    '--proposed-rule', 'Always do the fixture thing.',
                    '--occasion', 'a fixture occasion', '--recurrence', '2']
            if gh_repo:
                args += ['--github-repo', gh_repo]
            return pyrun(*args)

        rc, out = make_issue_draft('Someone Not An Approver', slug='pipeline-fixture-issue-a')
        no_file_written = not any(team_repo.glob('candidates/pipeline-fixture-issue-a-*.md'))
        cases.append(('team --as-issue drafts a GitHub Issue body and URL, and '
                      'writes nothing to candidates/, for a non-approver',
                      rc == 0
                      and 'github.com/fixture-owner/fixture-team/issues/new' in out
                      and 'labels=precedent-candidate' in out
                      and no_file_written))

        rc, out = make_issue_draft('Approved Person', slug='pipeline-fixture-issue-b')
        cases.append(('team --as-issue nudges toward landing directly when '
                      "--raised-by is already a listed approver, by name",
                      rc == 0 and 'already a listed approver' in out))

        rc, out = make_issue_draft('approved-gh', slug='pipeline-fixture-issue-c')
        cases.append(('the same nudge fires matching on the github handle, '
                      'not just the display name',
                      rc == 0 and 'already a listed approver' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                        '--slug', 'pipeline-fixture-disclose-cand-i', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'harness',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('raising an individual candidate discloses it as a '
                      "proposal in the person's own set, not yet a practice",
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'YOUR OWN individual set' in out and str(repo) in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                        '--slug', 'pipeline-fixture-disclose-cand-t', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'Approved Person',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('an approver filing a team candidate (rather than landing '
                      'directly) discloses which team set it sits in and that it '
                      'still needs a yes',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'TEAM set at' in out and str(team_repo) in out
                      and 'already an approver' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(team_repo),
                        '--slug', 'pipeline-fixture-disclose-cand-n', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'Someone Not An Approver',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('a non-approver filing a plain team candidate (forgetting '
                      '--as-issue) gets an explicit warning that nothing is '
                      'watching for it, not just a quiet file',
                      rc == 0 and 'DISCLOSE TO THE HUMAN, PLAINLY' in out
                      and 'NOT a listed approver' in out and '--as-issue' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'individual', '--path', str(repo),
                        '--as-issue', 'true', '--slug', 'pipeline-fixture-issue-d',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--as-issue is refused for --level individual '
                      '(no one else to notify)',
                      rc == 1 and 'only applies to --level team' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'universal',
                        '--slug', 'pipeline-fixture-disclose-cand-u', '--title', 't',
                        '--signal', 'explicit-instruction', '--raised-by', 'harness',
                        '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('raising a universal candidate discloses it as a proposal '
                      'for everyone, not yet a practice for anyone',
                      rc == 0 and 'DISCLOSE TO THE HUMAN' in out
                      and 'proposal for EVERYONE using Precedent' in out))

        no_remote_repo = tmp / 'fixture-team-no-remote'
        (no_remote_repo / 'candidates').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q'], cwd=no_remote_repo, check=True)
        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(no_remote_repo),
                        '--as-issue', 'true', '--slug', 'pipeline-fixture-issue-e',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--as-issue refuses cleanly, without guessing, when the '
                      'repo has no detectable GitHub remote and --github-repo '
                      'was not given',
                      rc == 1 and 'could not detect a GitHub owner/repo' in out
                      and '--github-repo' in out))

        rc, out = pyrun(cand_tool, 'create', '--level', 'team', '--path', str(no_remote_repo),
                        '--as-issue', 'true', '--github-repo', 'override-owner/override-repo',
                        '--slug', 'pipeline-fixture-issue-f',
                        '--title', 't', '--signal', 'explicit-instruction',
                        '--raised-by', 'harness', '--observed', 'x', '--proposed-rule', 'x')
        cases.append(('--github-repo overrides remote detection entirely, for '
                      'a repo git could not identify on its own',
                      rc == 0 and 'github.com/override-owner/override-repo/issues/new' in out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'creation pipeline fires ({len(cases)} stated cases: all four '
          f'promotion criteria refuse individually and pass together, '
          f'landing enforces registered-check and named-approver invariants)',
          not bad,
          '; '.join(f"{n}{' (' + d + ')' if d else ''}" for n, d in bad))


def check_bootstrap_source_produces_resolvable_set():
    """spec/BOOTSTRAP_NEW_SOURCES.md's own claim, tested rather than trusted:
    tools/precedent_bootstrap_source.py's output is not just files copied
    into place, it is a working individual set AND team set that
    tools/precedent_resolve.py actually resolves cleanly the moment they're
    wired in -- the property that matters, since a skeleton nobody can
    resolve is no better than no skeleton at all.

    Fixture: bootstrap one individual set and one team set into a scratch
    dir, point a synthetic consumer repo's precedent.json (team) and
    PRECEDENT_USER_CONFIG (individual) at them, and resolve. Both skeletons'
    example-starter.md intentionally share a slug -- that also exercises the
    precedence resolver for real (team must win over individual, per
    tools/precedent_resolve.py's documented order) rather than only proving
    the sources load."""
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
        team_dest = tmp / 'team-set'

        rc, out = pyrun(bootstrap_tool, '--level', 'individual',
                        '--name', 'harness-fixture-individual', '--dest', str(indiv_dest))
        cases.append(('bootstrapping an individual set succeeds and writes its files',
                      rc == 0 and (indiv_dest / 'practices' / 'example-starter.md').is_file()
                      and (indiv_dest / 'config.json.sample').is_file(), out))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'harness-fixture-team', '--dest', str(team_dest))
        cases.append(('bootstrapping a team set without --approver is refused',
                      rc == 1 and 'approver' in out, out))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'harness-fixture-team', '--dest', str(team_dest),
                        '--approver', 'Harness Approver:harness-approver-gh')
        approvers_json = team_dest / 'approvers.json'
        cases.append(('bootstrapping a team set succeeds and seeds approvers.json',
                      rc == 0 and approvers_json.is_file()
                      and json.loads(approvers_json.read_text()).get('approvers')
                      == [{'name': 'Harness Approver', 'github': 'harness-approver-gh'}], out))

        non_empty = tmp / 'occupied'
        (non_empty / 'something.txt').parent.mkdir(parents=True)
        (non_empty / 'something.txt').write_text('pre-existing', encoding='utf-8')
        rc, out = pyrun(bootstrap_tool, '--level', 'individual',
                        '--name', 'harness-fixture-refused', '--dest', str(non_empty))
        cases.append(('bootstrapping into a non-empty destination is refused without --force',
                      rc == 1 and 'not empty' in out, out))

        consumer = tmp / 'consumer'
        consumer.mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                {'level': 'team', 'name': 'harness-fixture-team', 'path': str(team_dest)},
            ],
        }), encoding='utf-8')
        user_config = tmp / 'user-config.json'
        user_config.write_text(json.dumps({
            'individual': {'name': 'harness-fixture-individual', 'path': str(indiv_dest)},
        }), encoding='utf-8')

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
        cases.append(('example-starter resolves, won by the team set over the '
                      'individual set (real precedence, not just presence)',
                      slugs.get('example-starter', {}).get('level') == 'team', out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'bootstrap_source produces a resolvable individual and team set '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:200]}" for n, d in bad))


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
    hook = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'precedent-paths.sh'
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
                  and hso.get('permissionDecision') == 'allow'
                  and 'code-cites-practice' in hso.get('additionalContext', '')))

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
    cases.append(('a tool call with no tool_input at all (matcher scopes this out '
                  'in settings.json, but the wrapper itself must not assume that) '
                  'prints nothing', rc == 0 and out == ''))

    bad = [(n, '') for n, ok in cases if not ok]
    check(f'PreToolUse hook fires ({len(cases)} stated cases: Edit file_path, '
          f'a no-match path, NotebookEdit notebook_path fallback, malformed '
          f'stdin, a tool call with no tool_input)',
          not bad, '; '.join(n for n, _ in bad))


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
    check_no_bare_numeric_citations(files)
    check_slug_link_integrity(files)
    check_leak_gate()
    check_leak_gate_fires()
    check_practice_audit_fires()
    check_source_precedence()
    check_cross_source_resident_budget()
    check_doc_lint_fires()
    check_practice_sections_present()
    check_practice_heading_parsing()
    check_decision_records_not_inline()
    check_decision_records_not_inline_fires()
    check_catalogue_anchors()
    check_all_workflows_disclosed()
    check_example_set()
    check_index_clauses(files)
    check_rule_is_self_contained(files)
    check_glob_semantics()
    check_symlinked_root_path_matching()
    check_generated_views_regenerate()
    check_resident_subset(files)
    check_behavioral_replay()
    check_precedent_check_fires()
    check_routing_scope(files)
    check_routing_audit_coverage()
    check_gate_channel()
    check_materialize_bridges_loader()
    check_sync_views_cross_source()
    check_detect_restated_fires()
    check_creation_pipeline_fires()
    check_bootstrap_source_produces_resolvable_set()
    check_pretooluse_hook_fires()

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    return 1 if FAILED else 0


if __name__ == '__main__':
    sys.exit(main())
